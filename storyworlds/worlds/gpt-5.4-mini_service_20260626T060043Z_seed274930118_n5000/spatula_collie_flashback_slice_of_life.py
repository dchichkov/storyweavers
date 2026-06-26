#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spatula_collie_flashback_slice_of_life.py
===============================================================================================================

A small slice-of-life story world about a child, a collie, and a spatula,
with a gentle flashback that explains why the collie cares so much about the
kitchen job.

Premise:
- A child is making breakfast at home.
- A collie wants to help and keeps a spatula nearby.
- A small problem appears: the child is moving too fast, and the spatula gets
  set down in the wrong place.

Turn:
- A brief flashback shows that the collie learned the spatula matters during
  a previous weekend pancake session.
- In the present, the child remembers that lesson and asks the collie for a
  safe, simple kind of help.

Resolution:
- The collie helps in a calm way.
- The breakfast gets finished.
- The spatula ends up back in the right hand, and the little home scene feels
  warm and settled.

The prose is intentionally grounded in physical state:
- location, holding, and cleanliness are tracked in meters;
- eagerness, worry, and relief are tracked in memes.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    extra: str = "the sunny table by the window"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", extra="the sunny table by the window"),
    "yard": Setting(place="the backyard", extra="the little patio table"),
    "diner": Setting(place="the cozy diner corner", extra="the red booth by the counter"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Jack"]


@dataclass
class DogProfile:
    name: str = "Moss"
    type: str = "collie"
    fluff: str = "soft brown-and-white"
    helper_trait: str = "careful"


COLLIE = DogProfile()


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_place(place: str) -> bool:
    return place in SETTINGS


def valid_story(place: str) -> bool:
    return place in SETTINGS


def explain_invalid(place: str) -> str:
    return f"(No story: {place!r} is not a supported slice-of-life setting.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        location=world.setting.place,
        meters={"clean": 1.0},
        memes={"hope": 1.0, "curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        location=world.setting.place,
        meters={"clean": 1.0},
        memes={"calm": 1.0},
    ))
    collie = world.add(Entity(
        id="Moss",
        kind="character",
        type="collie",
        label="Moss",
        location=world.setting.place,
        meters={"clean": 1.0, "energy": 1.0},
        memes={"loyalty": 1.0, "eagerness": 1.0},
    ))
    spatula = world.add(Entity(
        id="spatula",
        kind="thing",
        type="spatula",
        label="spatula",
        phrase="a wooden spatula",
        owner=params.name,
        caretaker="Parent",
        held_by=params.name,
        location=world.setting.place,
        meters={"clean": 1.0},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        collie=collie,
        spatula=spatula,
        flashback_seen=False,
        breakfast_done=False,
    )
    return world


def open_scene(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    collie: Entity = world.facts["collie"]
    spatula: Entity = world.facts["spatula"]

    world.say(
        f"{child.id} was in {world.setting.place} making breakfast with {spatula.label} in hand."
    )
    world.say(
        f"{collie.id}, the {COLLIE.type}, padded close by and watched every little move with bright eyes."
    )
    world.say(
        f"{child.id} liked the quiet morning, and {collie.id} liked being near the warm pan and the smell of food."
    )
    world.say(
        f"{parent.label.capitalize()} smiled from across the room and said it was a nice, ordinary morning."
    )


def problem(world: World) -> None:
    child: Entity = world.facts["child"]
    collie: Entity = world.facts["collie"]
    spatula: Entity = world.facts["spatula"]

    child.memes["rushed"] = child.memes.get("rushed", 0.0) + 1.0
    collie.memes["concern"] = collie.memes.get("concern", 0.0) + 1.0
    spatula.location = "the counter edge"
    spatula.held_by = None

    world.say(
        f"Then {child.id} turned quickly to reach for the bowl, and the {spatula.label} got set down on the counter edge."
    )
    world.say(
        f"{collie.id} looked up at once, because the collie had a strong feeling that the {spatula.label} should stay where cooking hands could find it."
    )


def flashback(world: World) -> None:
    child: Entity = world.facts["child"]
    collie: Entity = world.facts["collie"]
    spatula: Entity = world.facts["spatula"]

    world.para()
    world.say(
        f"For a moment, {child.id} remembered last weekend."
    )
    world.say(
        f"Back then, {collie.id} had sat beside the table while pancakes sizzled, and the {spatula.label} had been passed back and forth with care."
    )
    world.say(
        f"When the batter nearly slipped off the pan, {collie.id} had nudged the handle just enough for {child.id} to catch it."
    )
    world.say(
        f"That tiny rescue made {child.id} trust {collie.id} as a true kitchen helper."
    )
    world.facts["flashback_seen"] = True
    collie.memes["confidence"] = collie.memes.get("confidence", 0.0) + 1.0
    child.memes["memory_warmth"] = child.memes.get("memory_warmth", 0.0) + 1.0


def repair(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    collie: Entity = world.facts["collie"]
    spatula: Entity = world.facts["spatula"]

    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    collie.memes["joy"] = collie.memes.get("joy", 0.0) + 1.0

    world.say(
        f"{child.id} remembered that and laughed softly."
    )
    world.say(
        f'"Could you help by waiting with {mealsafe(collie)} while I flip this?" {child.id} asked.'
    )
    world.say(
        f"{collie.id} sat down right away, tail swishing in the air, and waited beside the stove instead of crowding the pan."
    )
    world.say(
        f"{parent.label.capitalize()} handed over a small plate, and together they finished breakfast without any fuss."
    )
    spatula.held_by = child.id
    spatula.location = world.setting.place
    world.facts["breakfast_done"] = True

    world.para()
    world.say(
        f"In the end, {child.id} held the {spatula.label} again, {collie.id} kept watch in a calm little loaf on the floor, and the kitchen felt settled and kind."
    )


def mealsafe(collie: Entity) -> str:
    return "a careful spot"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_place(kitchen).
valid_place(yard).
valid_place(diner).

story(P) :- valid_place(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("valid_place", place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    python_set = {(p,) for p in SETTINGS}
    asp_set = set(asp_valid_places())
    if asp_set == python_set:
        print(f"OK: clingo gate matches SETTINGS ({len(asp_set)} places).")
        return 0
    print("MISMATCH between clingo and SETTINGS:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    collie: Entity = world.facts["collie"]
    return [
        f"Write a gentle slice-of-life story about {child.id} and a collie named {collie.id} in the kitchen, with a flashback to an earlier cooking moment.",
        f"Tell a short story where a child uses a spatula, remembers a helpful moment, and lets a collie help in a calm way.",
        f"Write a cozy story with the words 'spatula' and 'collie' that includes a brief flashback and ends with breakfast being finished.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    collie: Entity = world.facts["collie"]
    spatula: Entity = world.facts["spatula"]

    return [
        QAItem(
            question=f"Who was making breakfast with the spatula?",
            answer=f"{child.id} was making breakfast with the {spatula.label}.",
        ),
        QAItem(
            question=f"What kind of dog was {collie.id}?",
            answer=f"{collie.id} was a collie who stayed close to the kitchen action.",
        ),
        QAItem(
            question=f"Why did {child.id} remember last weekend?",
            answer=f"{child.id} remembered last weekend because it showed that {collie.id} could be a careful helper with the {spatula.label}.",
        ),
        QAItem(
            question=f"What changed after the flashback?",
            answer=f"After the flashback, {child.id} asked for calm help, {collie.id} sat and waited, and breakfast got finished neatly.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened in {world.setting.place}, a cozy place for an ordinary morning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spatula used for?",
            answer="A spatula is a kitchen tool used for flipping, lifting, or mixing food while you cook.",
        ),
        QAItem(
            question="What is a collie like?",
            answer="A collie is a herding dog that is usually smart, alert, and good at paying attention to people.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that looks back at something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.held_by:
            bits.append(f"held_by={ent.held_by}")
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str]]:
    return [(p,) for p in SETTINGS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and not valid_place(args.place):
        raise StoryError(explain_invalid(args.place))

    places = [args.place] if args.place else list(SETTINGS.keys())
    if not places:
        raise StoryError("(No valid combination matches the given options.)")

    place = rng.choice(sorted(places))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    open_scene(world)
    problem(world)
    flashback(world)
    repair(world)
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world with a spatula, a collie, and a flashback."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def asp_verify_storyworld() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify_storyworld())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_place/1."))
        places = sorted(set(asp.atoms(model, "valid_place")))
        print(f"{len(places)} supported places:\n")
        for (place,) in places:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Mia", gender="girl", parent="mother", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
