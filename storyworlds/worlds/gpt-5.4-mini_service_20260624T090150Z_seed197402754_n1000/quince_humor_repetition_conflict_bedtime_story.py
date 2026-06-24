#!/usr/bin/env python3
"""
Standalone storyworld for a bedtime-style tale centered on a quince, with
humor, repetition, and a small conflict that resolves gently.

The domain is intentionally small:
- a child wants to use a quince at bedtime,
- the quince is a little too tart or too strange for the moment,
- a repeated bedtime refrain adds humor,
- a tiny conflict about "now or later" turns into a calming, cozy ending.

The script follows the Storyweavers contract:
- stdlib-only prose engine,
- lazy ASP helper import,
- StoryParams, registries, build_parser, resolve_params, generate, emit, main,
- QA outputs and trace support,
- a reasonableness gate with inline ASP rules.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Tiny world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    edible: bool = False
    sweet: bool = False
    tart: bool = False
    prepared: bool = False
    whole: bool = True
    cut: bool = False
    warmed: bool = False
    has_spice: bool = False
    on_plate: bool = False
    in_bowl: bool = False
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {"warmth": 0.0}
        if self.memes is None:
            self.memes = {"joy": 0.0, "conflict": 0.0, "amusement": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little kitchen"
    bedtime: bool = True
    cozy: bool = True
    affords: set[str] = None

    def __post_init__(self) -> None:
        if self.affords is None:
            self.affords = {"eat_quince", "tell_story", "serve_tea", "slice_quince"}


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_role: str
    trait: str
    place: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", bedtime=True, cozy=True, affords={"eat_quince", "tell_story", "serve_tea", "slice_quince"}),
    "bedroom": Setting(place="the bedtime bedroom", bedtime=True, cozy=True, affords={"eat_quince", "tell_story"}),
    "porch": Setting(place="the quiet porch", bedtime=False, cozy=True, affords={"eat_quince", "tell_story", "slice_quince"}),
}

CHILD_NAMES_GIRL = ["Mina", "Lily", "Nora", "Ava", "June", "Ella"]
CHILD_NAMES_BOY = ["Theo", "Ben", "Finn", "Leo", "Milo", "Owen"]
TRAITS = ["curious", "cheerful", "sleepy", "silly", "patient"]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity]
    paragraphs: list[list[str]]
    facts: dict
    fired: set

    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities = {}
        self.paragraphs = [[]]
        self.facts = {}
        self.fired = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
QUINCES = {
    "fresh_quince": {
        "label": "quince",
        "phrase": "a ripe golden quince",
        "taste": "tart",
        "size": "small and lumpy",
        "humor": "it looked like a pear that had forgotten how to be a pear",
    }
}

PREPARATIONS = {
    "plain": {
        "label": "plain slices",
        "prep_line": "let the quince rest in calm slices",
        "result_line": "the slices were still tart, but they were easy to eat",
        "asp": "plain",
    },
    "spooned": {
        "label": "soft spoonfuls",
        "prep_line": "turn the quince into soft spoonfuls with a little warmth",
        "result_line": "the spoonfuls were gentle and sweet enough for bedtime",
        "asp": "spooned",
    },
    "honeyed": {
        "label": "honeyed bites",
        "prep_line": "drizzle a tiny bit of honey over the quince",
        "result_line": "the honey made the tartness less bossy",
        "asp": "honeyed",
    },
}

TEAS = {
    "chamomile": {
        "label": "chamomile tea",
        "comfort": "sleepy",
        "asp": "chamomile",
    },
    "mint": {
        "label": "mint tea",
        "comfort": "fresh",
        "asp": "mint",
    },
}

BEDTIME_RHYMES = [
    "one bite, two bites, then the moon says goodnight",
    "slice by slice, the stars shine nice",
    "little tart fruit, soft and cute, time to scoot toward sleep",
]

# ---------------------------------------------------------------------------
# World + narrative helpers
# ---------------------------------------------------------------------------
def _child_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def _parent_label(role: str) -> str:
    return {"mother": "mom", "father": "dad"}.get(role, role)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_role,
        label=_parent_label(params.parent_role),
    ))
    quince = world.add(Entity(
        id="Quince",
        kind="thing",
        type="quince",
        label="quince",
        phrase=QUINCES["fresh_quince"]["phrase"],
        edible=True,
        tart=True,
        whole=True,
    ))
    world.facts.update(child=child, parent=parent, quince=quince)
    return world


def _intro(world: World) -> None:
    child = world.facts["child"]
    quince = world.facts["quince"]
    world.say(
        f"{child.id} was a {next((t for t in ['curious', 'cheerful', 'sleepy', 'silly', 'patient'] if t in child.id.lower()), 'small')} child who liked quiet bedtime things."
    )
    world.say(
        f"One evening there was a quince on the table, and it was {QUINCES['fresh_quince']['size']}."
    )
    world.say(
        f"It even had a funny look to it, because {QUINCES['fresh_quince']['humor']}."
    )


def _love_and_routine(world: World) -> None:
    child = world.facts["child"]
    world.say(
        f"{child.id} pointed at the quince and said, 'Quince for bedtime, quince for bedtime.'"
    )
    world.say(
        f"{child.id} said it again, because repeating things made the room feel extra cozy."
    )


def _conflict(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    quince = world.facts["quince"]
    child.memes["conflict"] += 1
    world.say(
        f"{parent.label.capitalize()} smiled and said the quince was too tart to rush."
    )
    world.say(
        f"{child.id} wanted it right now anyway, but {parent.label} wanted bedtime to stay calm."
    )
    world.say(
        f"So {child.id} frowned, then whispered, 'Quince now. Quince now.'"
    )
    quince.memes["amusement"] += 1


def _turn(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    quince = world.facts["quince"]
    prep = random.choice(list(PREPARATIONS.values()))
    tea = random.choice(list(TEAS.values()))
    quince.prepared = True
    quince.warmed = True
    quince.cut = True
    quince.on_plate = True
    quince.in_bowl = True
    quince.meters["warmth"] += 1
    child.memes["joy"] += 1
    child.memes["amusement"] += 1
    child.memes["conflict"] = 0
    world.say(
        f"{parent.label.capitalize()} said, 'Let's not fight the tartness. Let's {prep['prep_line']}.'"
    )
    world.say(
        f"Then {parent.label} poured {tea['label']} into a tiny cup and put the little bowl beside it."
    )
    world.say(
        f"{child.id} sniffed the steam and laughed, because the quince looked less bossy when it was warm."
    )
    world.facts.update(prep=prep, tea=tea)


def _resolution(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    prep = world.facts["prep"]
    tea = world.facts["tea"]
    world.say(
        f"{child.id} ate a few {prep['label']} and took a sip of {tea['label']}."
    )
    world.say(
        f"Then {child.id} smiled the smallest bedtime smile and said, 'Quince later, quarrel never.'"
    )
    world.say(
        f"{parent.label.capitalize()} laughed softly, and the room grew quiet and warm again."
    )
    world.say(
        f"At the end, the quince was in a bowl, the tea was nearly gone, and {child.id} was ready for sleep."
    )


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _intro(world)
    world.para()
    _love_and_routine(world)
    world.para()
    _conflict(world)
    world.para()
    _turn(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen).
setting(bedroom).
setting(porch).

affords(kitchen,eat_quince).
affords(kitchen,tell_story).
affords(kitchen,serve_tea).
affords(kitchen,slice_quince).

affords(bedroom,eat_quince).
affords(bedroom,tell_story).

affords(porch,eat_quince).
affords(porch,tell_story).
affords(porch,slice_quince).

quince(fresh_quince).
taste(fresh_quince,tart).
prepared_option(plain).
prepared_option(spooned).
prepared_option(honeyed).

compatible(kitchen, plain) :- setting(kitchen), affords(kitchen, slice_quince).
compatible(kitchen, spooned) :- setting(kitchen), affords(kitchen, eat_quince).
compatible(kitchen, honeyed) :- setting(kitchen), affords(kitchen, serve_tea).

compatible(bedroom, spooned) :- setting(bedroom), affords(bedroom, eat_quince).
compatible(bedroom, honeyed) :- setting(bedroom), affords(bedroom, tell_story).
compatible(porch, plain) :- setting(porch), affords(porch, slice_quince).
compatible(porch, honeyed) :- setting(porch), affords(porch, tell_story).

valid_story(Place, Prep) :- compatible(Place, Prep).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for qid in QUINCES:
        lines.append(asp.fact("quince", qid))
        lines.append(asp.fact("taste", qid, QUINCES[qid]["taste"]))
    for pid in PREPARATIONS:
        lines.append(asp.fact("prepared_option", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prep in PREPARATIONS:
            if place == "kitchen" and prep in {"plain", "spooned", "honeyed"}:
                out.append((place, prep))
            elif place == "bedroom" and prep in {"spooned", "honeyed"}:
                out.append((place, prep))
            elif place == "porch" and prep in {"plain", "honeyed"}:
                out.append((place, prep))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(python_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python_valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python_valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        f"Write a cozy bedtime story about a child named {child.id} and a quince that starts out funny and a little tart.",
        f"Tell a short bedtime tale where {child.id} wants quince right now, but {parent.label} suggests a calmer way.",
        "Write a gentle story with repetition, humor, and a small conflict about a quince at bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    prep = world.facts["prep"]
    tea = world.facts["tea"]
    q = world.facts["quince"]
    return [
        QAItem(
            question=f"What did {child.id} keep asking for in the story?",
            answer=f"{child.id} kept asking for the quince, because {child.id} wanted the tart little fruit right away.",
        ),
        QAItem(
            question=f"Why did {parent.label} say the quince should not be rushed?",
            answer=f"{parent.label.capitalize()} said the quince was too tart to rush, so it would be better to prepare it gently for bedtime.",
        ),
        QAItem(
            question=f"How did the story turn from a little conflict into a cozy ending?",
            answer=f"{parent.label.capitalize()} prepared the quince as {prep['label']} and added {tea['label']}, which helped {child.id} calm down and smile again.",
        ),
        QAItem(
            question=f"What was funny about the quince?",
            answer=f"It was funny because it looked like {QUINCES['fresh_quince']['humor']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quince?",
            answer="A quince is a fruit that can smell sweet but taste tart, and people often cook it before eating it.",
        ),
        QAItem(
            question="Why do some bedtime stories repeat the same words?",
            answer="Repeating words can make a story feel soothing, musical, and easy for a sleepy child to remember.",
        ),
        QAItem(
            question="Why can a little conflict be part of a gentle story?",
            answer="A small conflict gives the story a problem to solve, and then the ending feels warm when everyone agrees again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.prepared:
            bits.append("prepared=True")
        if e.cut:
            bits.append("cut=True")
        if e.warmed:
            bits.append("warmed=True")
        if e.on_plate:
            bits.append("on_plate=True")
        if e.meters.get("warmth"):
            bits.append(f"meters={{warmth:{e.meters['warmth']}}}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a quince, with humor, repetition, and conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(child_name=name, child_gender=gender, parent_role=parent, trait=trait, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, prep) combos:\n")
        for place, prep in combos:
            print(f"  {place:8} {prep}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(child_name="Mina", child_gender="girl", parent_role="mother", trait="curious", place="kitchen"),
            StoryParams(child_name="Theo", child_gender="boy", parent_role="father", trait="silly", place="bedroom"),
            StoryParams(child_name="Nora", child_gender="girl", parent_role="mother", trait="sleepy", place="porch"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
