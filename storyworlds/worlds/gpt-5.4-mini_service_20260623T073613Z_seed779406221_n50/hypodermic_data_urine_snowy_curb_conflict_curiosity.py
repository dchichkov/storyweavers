#!/usr/bin/env python3
"""
storyworlds/worlds/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
==========================================================================

A standalone storyworld for a tiny, rhyming, child-facing tale set on a snowy
curb. A curious child spots a little clinic tote with a hypodermic, some data
cards, and a urine cup. Curiosity pulls one way; the caregiver's conflict and
care pull the other. The story turns when the child chooses to ask first, not
poke first, and the ending image proves what changed.

This world keeps the classical storyworld shape:
- typed entities with meters and memes,
- a small forward-chaining simulation,
- a reasonableness gate,
- inline ASP twin rules,
- grounded QA from the generated world state.

The prose is lightly rhymed and child-facing, but still driven by state.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    snow_depth: str
    curb_detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class KitItem:
    id: str
    label: str
    phrase: str
    kind: str
    purpose: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    protects: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for child in world.children():
        if child.memes["curiosity"] < THRESHOLD or child.memes["stopped"] >= THRESHOLD:
            continue
        if child.memes["warned"] < THRESHOLD:
            continue
        sig = ("conflict", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for child in world.children():
        if child.memes["asked"] < THRESHOLD or child.memes["conflict"] < THRESHOLD:
            continue
        sig = ("calm", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["conflict"] = 0.0
        child.memes["joy"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [
    _r_conflict,
    _r_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def child_at_risk(item: KitItem, setting: Setting) -> bool:
    return item.risk == "needle" and "curb" in setting.place


def compatible_cover(item: KitItem, cover: Cover) -> bool:
    return item.risk in cover.protects


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for cover_id, cover in COVERS.items():
                if child_at_risk(item, setting) and compatible_cover(item, cover):
                    combos.append((setting_id, item_id, cover_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    cover: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: snowy curb, curiosity, and a calm turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "careful", "bright"])
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
    if args.item and args.cover and not compatible_cover(ITEMS[args.item], COVERS[args.cover]):
        raise StoryError("That cover does not truly fit the item's risk.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.cover is None or c[2] == args.cover)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, cover = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["curious", "careful", "bright"])
    return StoryParams(setting=setting, item=item, cover=cover, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, item: KitItem, cover: Cover, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    grown = world.add(Entity(id="Parent", kind="character", type=parent, label="the parent"))
    kit = world.add(Entity(id=item.id, type=item.kind, label=item.label, caretaker=grown.id))
    kit.attrs["phrase"] = item.phrase
    kit.attrs["purpose"] = item.purpose
    cover_ent = world.add(Entity(id=cover.id, type="thing", label=cover.label, caretaker=grown.id))
    cover_ent.attrs["phrase"] = cover.phrase
    child.memes["curiosity"] += 1
    child.memes["warned"] = 0
    child.memes["asked"] = 0
    child.memes["stopped"] = 0

    world.say(f"{name} stood by the snowy curb, where white drifts curled like sugar on a pie.")
    world.say(f"The curb was cold and still, and the little snow made the whole street sigh.")
    world.say(f"{name} was a {trait} {gender} who liked to look, to peek, to see, to spy.")
    world.say(f"By the curb sat {item.phrase}, with {cover.phrase} tucked close nearby.")

    world.para()
    if item.id == "hypodermic":
        world.say("A hypodermic glinted thin and slick, a shiny little needle-tick.")
    if item.id == "data":
        world.say("A stack of data cards lay near, with numbers neat and lines severe.")
    if item.id == "urine":
        world.say("A small urine cup sat snug in place, like a tiny boat in a frosty space.")
    world.say(f"{name} leaned in close, with curious eyes, and whispered, 'What is this prize?'")
    world.say(f'But {grown.label} frowned. "{item.purpose.capitalize()}, dear one, and not for play; it can help a person in a careful way."')
    child.memes["warned"] += 1
    child.memes["conflict"] += 1
    propagate(world, narrate=False)
    world.say(f"{name} felt a tug-of-war inside: a curious pull and a caution tide.")
    world.say(f'The child said, "I want to touch it, see?" but the parent said, "First ask me."')

    world.para()
    child.memes["asked"] += 1
    child.memes["conflict"] = 0
    child.memes["joy"] += 1
    world.say(f"So {name} asked, and waited, and did not poke; the snowy curb stayed safe and woke.")
    world.say(f"{grown.label_word if hasattr(grown, 'label_word') else 'The parent'} smiled and showed {name} the cards and cup, then kept the needle safely up.")
    world.say(f"{name} learned that questions can be kind, and that care is lovely too, you find.")
    world.say(f"At the end, the curb was still, and the child was bright, and the chill felt mild.")

    world.facts.update(
        child=child,
        parent=grown,
        item=item,
        cover=cover,
        setting=setting,
        trait=trait,
        asked=True,
        conflict_before=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child on a snowy curb about {f["child"].id} noticing a {f["item"].label} and choosing to ask first.',
        f"Tell a gentle rhyme where a {f['trait']} child feels curiosity by the snowy curb, but a parent keeps {f['item'].label} safe.",
        f'Create a rhyming story that includes the words "hypodermic", "data", and "urine", and ends with a calm question instead of a poke.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item, cover = f["child"], f["parent"], f["item"], f["cover"]
    return [
        QAItem(
            question=f"Where was {child.id} standing when the story began?",
            answer=f"{child.id} was standing by the snowy curb, where the cold snow made the street look soft and white.",
        ),
        QAItem(
            question=f"What did {child.id} notice near the curb?",
            answer=f"{child.id} noticed {item.phrase}, and also {cover.phrase}, and got very curious about them.",
        ),
        QAItem(
            question=f"Why did {parent.label} not want {child.id} to touch the {item.label}?",
            answer=f"{parent.label.capitalize()} said it was for helping a person in a careful way, not for play. The parent wanted the item kept safe.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end instead of poking?",
            answer=f"{child.id} asked first and waited. That choice calmed the conflict and kept the snowy curb safe.",
        ),
    ]


KNOWLEDGE = {
    "hypodermic": [("What is a hypodermic?", "A hypodermic is a needle used by trained grown-ups to give medicine or take a sample in a careful way.")],
    "data": [("What is data?", "Data is information that people collect, like numbers, notes, or facts.")],
    "urine": [("What is urine?", "Urine is liquid that comes from the body and goes into a toilet or a sample cup when a doctor needs it.")],
    "curb": [("What is a curb?", "A curb is the raised edge at the side of a road or sidewalk.")],
    "snow": [("Why is snow cold?", "Snow is cold because it is frozen water, so it feels chilly to touch.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    items = [world.facts["item"].id, "data", "urine"]
    out: list[QAItem] = []
    for key, qas in KNOWLEDGE.items():
        if key in items or key == "curb":
            out.extend(QAItem(question=q, answer=a) for q, a in qas)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "snowy_curb": Setting(
        place="snowy curb",
        snow_depth="ankle-high",
        curb_detail="a white ridge of snow along the street edge",
        afford={"look", "ask"},
    )
}

ITEMS = {
    "hypodermic": KitItem(
        id="hypodermic",
        label="hypodermic",
        phrase="a hypodermic",
        kind="tool",
        purpose="It helps a doctor work with care",
        risk="needle",
        tags={"hypodermic"},
    ),
    "data": KitItem(
        id="data",
        label="data",
        phrase="some data cards",
        kind="papers",
        purpose="It helps a grown-up keep facts in order",
        risk="paper",
        tags={"data"},
    ),
    "urine": KitItem(
        id="urine",
        label="urine cup",
        phrase="a urine cup",
        kind="cup",
        purpose="It helps a doctor collect a sample with care",
        risk="cup",
        tags={"urine"},
    ),
}

COVERS = {
    "case": Cover(
        id="case",
        label="a padded case",
        phrase="a padded case",
        protects={"needle"},
        tags={"case"},
    ),
    "folder": Cover(
        id="folder",
        label="a blue folder",
        phrase="a blue folder",
        protects={"paper"},
        tags={"folder"},
    ),
    "lid": Cover(
        id="lid",
        label="a snap lid",
        phrase="a snap lid",
        protects={"cup"},
        tags={"lid"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Max", "Eli", "Noah"]
TRAITS = ["curious", "careful", "bright"]


def explain_rejection(item: KitItem, cover: Cover) -> str:
    return f"(No story: {cover.label} does not fit the risk of {item.label}.)"


def valid_for_asp() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
risk(item_hypodermic, needle).
risk(item_data, paper).
risk(item_urine, cup).

covers(case, needle).
covers(folder, paper).
covers(lid, cup).

valid(setting_snowy_curb, Item, Cover) :- risk(Item, R), covers(Cover, R).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "setting_snowy_curb"),
        asp.fact("item", "item_hypodermic"),
        asp.fact("item", "item_data"),
        asp.fact("item", "item_urine"),
        asp.fact("cover", "case"),
        asp.fact("cover", "folder"),
        asp.fact("cover", "lid"),
        asp.fact("needle", "needle"),
        asp.fact("paper", "paper"),
        asp.fact("cup", "cup"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_for_asp())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts_from_params(params: StoryParams) -> list[str]:
    return [
        f'Write a short rhyming story for a child on a snowy curb about {params.name} and a {params.item} going from curiosity to calm.',
        f'Create a rhyme where a {params.trait} child asks before touching a {params.item} and keeps the scene safe.',
        'Tell a gentle, rhyming story that includes the words hypodermic, data, and urine.',
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], COVERS[params.cover],
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts_from_params(params),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, cover) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("snowy_curb", "hypodermic", "case", "Mia", "girl", "mother", "curious"),
            StoryParams("snowy_curb", "data", "folder", "Leo", "boy", "father", "bright"),
            StoryParams("snowy_curb", "urine", "lid", "Nora", "girl", "mother", "careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
