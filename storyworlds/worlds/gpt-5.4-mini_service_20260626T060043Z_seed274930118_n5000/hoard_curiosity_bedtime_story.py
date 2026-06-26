#!/usr/bin/env python3
"""
storyworlds/worlds/hoard_curiosity_bedtime_story.py
===================================================

A small bedtime-story world about a child, a curious hoard, and a gentle
turn toward tidiness and rest.

Premise:
- A child keeps a little hoard of treasures under the bed or in a box.
- Curiosity makes the child keep opening, sorting, and wondering about it.
- The hoard starts to feel too big and too busy for bedtime.
- A calm helper or self-guided choice turns curiosity into a kinder ritual:
  looking, naming, choosing one favorite, and tucking the rest away.

The prose and world model are intentionally small and concrete. The story
should read like a complete little bedtime tale rather than an event log.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Shared, tiny simulation constants.
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"order": 0.0, "shine": 0.0, "sleepiness": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "calm": 0.0, "delight": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    bedtime: bool
    cozy: str
    afford_curious_hoard: bool = True


@dataclass
class HoardItem:
    label: str
    phrase: str
    type: str
    gleam: str
    weight: str
    hiding_place: str
    plural: bool = False


@dataclass
class Guide:
    label: str
    voice_line: str
    closing_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom", bedtime=True, cozy="soft and quiet"),
    "nursery": Setting(place="the nursery", bedtime=True, cozy="warm and dim"),
    "attic_room": Setting(place="the attic room", bedtime=True, cozy="small and sleepy"),
}

HOARDS = {
    "shells": HoardItem(
        label="shells",
        phrase="a little hoard of pearly shells",
        type="shells",
        gleam="moon-white",
        weight="light",
        hiding_place="a wooden box",
        plural=True,
    ),
    "buttons": HoardItem(
        label="buttons",
        phrase="a pocket hoard of shiny buttons",
        type="buttons",
        gleam="bright",
        weight="tiny",
        hiding_place="a striped tin",
        plural=True,
    ),
    "stones": HoardItem(
        label="stones",
        phrase="a hoard of smooth bedtime stones",
        type="stones",
        gleam="soft",
        weight="small",
        hiding_place="a cloth bag",
        plural=True,
    ),
    "glimmers": HoardItem(
        label="glimmers",
        phrase="a tiny hoard of glittery scraps",
        type="glimmers",
        gleam="sparkly",
        weight="light",
        hiding_place="a blue jar",
        plural=True,
    ),
}

GUIDES = {
    "mother": Guide(
        label="mom",
        voice_line="Let's look at your treasures one by one, so they can rest too.",
        closing_line="Then they tucked the rest away and made room for sleep.",
    ),
    "father": Guide(
        label="dad",
        voice_line="Curiosity is lovely. It just needs a gentle bedtime place.",
        closing_line="After that, the room felt quiet enough for dreams.",
    ),
    "grandmother": Guide(
        label="grandma",
        voice_line="A curious heart can sort its treasures like little stars in the dark.",
        closing_line="Soon the treasures were nested safely, and the child was yawning.",
    ),
}

NAMES = ["Mina", "Theo", "Nora", "Owen", "Lina", "Jasper", "Iris", "Milo"]
TYPES = ["girl", "boy"]
TRAITS = ["gentle", "curious", "lively", "soft-spoken", "dreamy"]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hoard: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bedtime story is reasonable when the setting is cozy and there is a hoard
% that curiosity can inspect without turning the room into a scramble.
bedtime_place(P) :- setting(P), cozy(P).
curious_hoard(H) :- hoard(H), shiny(H), box(H).
reasonable_story(P, H) :- bedtime_place(P), curious_hoard(H), can_settle(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.bedtime:
            lines.append(asp.fact("cozy", sid))
    for hid, h in HOARDS.items():
        lines.append(asp.fact("hoard", hid))
        lines.append(asp.fact("shiny", hid))
        lines.append(asp.fact("box", hid))
        lines.append(asp.fact("can_settle", hid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    asp_set = set(asp.atoms(model, "reasonable_story"))
    py_set = {(p, h) for p in SETTINGS for h in HOARDS}
    py_set = {(p, h) for (p, h) in py_set if SETTINGS[p].bedtime}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reasonableness_gate(place: str, hoard: str) -> bool:
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    if hoard not in HOARDS:
        raise StoryError(f"Unknown hoard: {hoard}")
    return SETTINGS[place].bedtime and HOARDS[hoard].type in HOARDS


def choose_guide(gender: str, rng: random.Random) -> str:
    return rng.choice(list(GUIDES))

def choose_name(gender: str, rng: random.Random) -> str:
    if gender == "girl":
        return rng.choice([n for n in NAMES if n in {"Mina", "Nora", "Lina", "Iris"}])
    return rng.choice([n for n in NAMES if n in {"Theo", "Owen", "Jasper", "Milo"}])

def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} felt {setting.cozy}, with the kind of hush that makes a pillow seem friendly."

def hoard_line(item: HoardItem) -> str:
    return f"It was {item.phrase}, kept in {item.hiding_place} where the child could reach it with careful fingers."

def introduce(world: World, child: Entity, item: Entity) -> None:
    world.say(
        f"{child.id} was a {next(t for t in child.memes.keys() if t in ['curiosity']) or 'curious'} little {child.type} "
        f"who loved finding pretty things."
    )
    world.say(f"{child.id} kept {item.phrase} like a secret treasure.")

def curiosity_rises(world: World, child: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 1
    item.meters["shine"] += 1
    world.say(
        f"Every night, {child.id} lifted the lid and counted the little pieces again, because {child.pronoun('subject')} "
        f"wanted to know which one was the brightest."
    )

def hoard_gets_busy(world: World, child: Entity, item: Entity) -> None:
    item.meters["order"] -= 1
    child.memes["worry"] += 1
    world.say(
        f"Pretty soon, the treasures were not staying still in the {item.label} box, and the bedtime room began to feel busy."
    )

def guide_arrives(world: World, child: Entity, guide: Entity, item: Entity) -> None:
    world.say(
        f"Then {child.id}'s {guide.label} came to the doorway and smiled. "
        f'"{GUIDES[guide.type].voice_line}"'
    )
    child.memes["calm"] += 1

def settle(world: World, child: Entity, guide: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 0.5
    child.memes["calm"] += 1
    child.meters["sleepiness"] += 1
    item.meters["order"] += 2
    world.say(
        f"Together they chose one favorite treasure and put the rest back in {item.phrase.split('a ')[-1] if item.phrase.startswith('a ') else item.hiding_place}."
    )
    world.say(
        f"{child.id} held the favorite close for one last look, then tucked it beside the pillow like a moonbeam."
    )
    world.say(f"At last, {GUIDES[guide.type].closing_line}")

# ---------------------------------------------------------------------------
# World build / narration
# ---------------------------------------------------------------------------

def tell(setting: Setting, hoard_cfg: HoardItem, name: str, gender: str, guide_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    child.memes["curiosity"] = 1.0
    child.memes["calm"] = 0.2
    child.memes["sleepiness"] = 0.3

    guide = world.add(Entity(id="Guide", kind="character", type=guide_type))
    item = world.add(Entity(
        id=hoard_cfg.type,
        kind="thing",
        type=hoard_cfg.type,
        label=hoard_cfg.label,
        phrase=hoard_cfg.phrase,
        plural=hoard_cfg.plural,
        owner=child.id,
    ))

    world.say(f"{child.id} was a {trait} little {gender} who lived in {setting.place}.")
    world.say(setting_line(setting))
    world.say(hoard_line(hoard_cfg))
    world.para()

    world.say(f"Before sleep, {child.id} could not help opening the little hoard again.")
    curiosity_rises(world, child, item)
    hoard_gets_busy(world, child, item)
    world.para()

    guide_arrives(world, child, guide, item)
    settle(world, child, guide, item)

    world.facts.update(
        child=child,
        guide=guide,
        item=item,
        trait=trait,
        setting=setting,
        hoard_cfg=hoard_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    trait = f["trait"]
    return [
        f'Write a bedtime story about a {trait} child who keeps {item.phrase} and cannot stop wondering about it.',
        f"Tell a gentle story where {child.id} has a little hoard, feels curious at bedtime, and learns to settle it kindly.",
        f'Write a quiet story for young children that includes a "hoard" and ends with the treasures tucked in safely.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    item = f["item"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a {trait} little {child.type} in {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} keep in {setting.place}?",
            answer=f"{child.id} kept {item.phrase}, a little hoard of treasures.",
        ),
        QAItem(
            question=f"Why did the room start to feel busy?",
            answer=f"The room felt busy because {child.id} kept opening the hoard again and again to look at the treasures.",
        ),
        QAItem(
            question=f"Who helped {child.id} settle down?",
            answer=f"{child.id}'s {GUIDES[guide.type].label} helped by suggesting they look at the treasures one by one and then put the rest away.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the treasures tucked safely away and {child.id} sleepy and calm, ready for dreams.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hoard?",
            answer="A hoard is a gathered pile or collection of things someone keeps together, often because they like them a lot.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about things.",
        ),
        QAItem(
            question="Why do bedtime routines help?",
            answer="Bedtime routines help because calm, repeated steps tell the body and mind that it is time to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.kind:7}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="bedroom", hoard="shells", name="Mina", gender="girl", guide="mother", trait="curious"),
    StoryParams(place="nursery", hoard="buttons", name="Theo", gender="boy", guide="father", trait="gentle"),
    StoryParams(place="attic_room", hoard="glimmers", name="Nora", gender="girl", guide="grandmother", trait="dreamy"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a curious hoard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hoard", choices=HOARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hoard = args.hoard or rng.choice(list(HOARDS))
    if not SETTINGS[place].bedtime:
        raise StoryError("This world only tells bedtime stories.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    guide = args.guide or choose_guide(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hoard=hoard, name=name, gender=gender, guide=guide, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], HOARDS[params.hoard], params.name, params.gender, params.guide, params.trait)
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


# ---------------------------------------------------------------------------
# Main / ASP modes
# ---------------------------------------------------------------------------

def asp_list() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    return sorted(set(asp.atoms(model, "reasonable_story")))

def show_asp() -> str:
    return asp_program("#show reasonable_story/2.")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_list()
        print(f"{len(combos)} reasonable story combinations:")
        for place, hoard in combos:
            print(f"  {place:10} {hoard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.hoard} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
