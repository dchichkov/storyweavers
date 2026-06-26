#!/usr/bin/env python3
"""
storyworlds/worlds/crucial_mystery_to_solve_happy_ending_slice.py
=================================================================

A small slice-of-life storyworld about a crucial missing thing, a calm mystery,
and a happy ending.

Premise:
A child notices that one important, everyday object is missing right before a
simple plan for the day. The family searches in ordinary places, follows small
clues, and finds the object where it belongs.

The world is intentionally small:
- one home setting
- one important object
- one helpful clue chain
- one satisfying resolution

The prose should feel like a gentle TinyStories slice-of-life mystery: concrete,
grounded, and resolved with a warm ending image.
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
# Small world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    locations: tuple[str, ...]
    weather: str = ""


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    location: str
    clue: str
    why_crucial: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object_id: str
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
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", locations=("table", "chair", "sink", "counter", "fridge")),
    "bedroom": Setting(place="the bedroom", locations=("bed", "pillow", "desk", "drawer", "toy box")),
    "living_room": Setting(place="the living room", locations=("sofa", "rug", "basket", "shelf", "blanket")),
}

MYSTERY_OBJECTS = {
    "key": MysteryObject(
        id="key",
        label="key",
        phrase="a small brass key",
        location="a bowl by the door",
        clue="the bowl by the door was open and empty",
        why_crucial="it opened the little box with the saved letter inside",
    ),
    "glasses": MysteryObject(
        id="glasses",
        label="glasses",
        phrase="a pair of round glasses",
        location="the bedside table under a book",
        clue="the book had been moved aside, leaving a glasses-shaped mark",
        why_crucial="they helped the grown-up read the recipe card for supper",
        plural=True,
    ),
    "scarf": MysteryObject(
        id="scarf",
        label="scarf",
        phrase="a soft red scarf",
        location="the back of a chair",
        clue="one chair still had a warm little fold where the scarf had rested",
        why_crucial="it kept the child warm on the walk to the market",
    ),
    "notebook": MysteryObject(
        id="notebook",
        label="notebook",
        phrase="a blue notebook",
        location="under a cushion on the sofa",
        clue="a corner of blue paper peeked out from under the cushion",
        why_crucial="it held the drawing plan for the child's happy surprise",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Theo", "Noah", "Sam"]

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def object_can_be_found(setting: Setting, obj: MysteryObject) -> bool:
    return obj.location in setting.locations or "door" in obj.location or "table" in obj.location or "sofa" in obj.location


def object_is_crucial(obj: MysteryObject) -> bool:
    return bool(obj.why_crucial)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for oid, obj in MYSTERY_OBJECTS.items():
            if object_can_be_found(setting, obj) and object_is_crucial(obj):
                out.append((place, oid))
    return out


def explain_rejection(place: str, object_id: str) -> str:
    return f"(No story: the object '{object_id}' does not fit a small findable slice-of-life mystery in {place}.)"


# ---------------------------------------------------------------------------
# World story
# ---------------------------------------------------------------------------

def build_world(setting: Setting, obj_cfg: MysteryObject, name: str, gender: str, parent: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type="thing",
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=grownup.id,
        location=obj_cfg.location,
        hidden=True,
        plural=obj_cfg.plural,
    ))

    # Setup
    world.say(f"{child.label} was a little {gender} who liked quiet mornings in {setting.place}.")
    world.say(f"That day, {child.label} and {grownup.label} needed {obj.phrase}, because {obj_cfg.why_crucial}.")
    world.para()

    # Mystery: it's missing
    world.say(f"At first, {child.label} looked in the usual spots, but {obj.label} was nowhere to be seen.")
    world.say(f"{obj_cfg.clue.capitalize()}.")
    world.say(f"{child.label} and {grownup.label} began to search carefully, one room at a time.")
    world.para()

    # Turn: clue leads to discovery
    world.say(f"They checked the nearby places with small, patient steps.")
    world.say(f"Then {child.label} noticed {obj.phrase} hiding exactly where it had been left.")
    obj.hidden = False
    world.say(f"{grownup.label.capitalize()} smiled and said that sometimes even a crucial thing simply waits for the right person to notice it.")
    world.para()

    # Ending
    world.say(f"Soon {child.label} held {obj.it()} close, and the morning felt easy again.")
    world.say(f"The little worry was gone, the important thing was back, and the day could go on with a happy heart.")

    world.facts.update(
        child=child,
        grownup=grownup,
        obj=obj,
        obj_cfg=obj_cfg,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj_cfg"]
    return [
        f'Write a short slice-of-life mystery for a young child where {child.label} loses {obj.phrase} and finds it again.',
        f"Tell a gentle story about a crucial missing {obj.label} in {world.setting.place} with a happy ending.",
        f"Write a calm mystery story that ends with {child.label} solving the little search and feeling relieved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    obj = f["obj"]
    obj_cfg = f["obj_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What important thing were {child.label} and {grownup.label} looking for in {setting.place}?",
            answer=f"They were looking for {obj.phrase}, because {obj_cfg.why_crucial}.",
        ),
        QAItem(
            question=f"How did {child.label} help solve the mystery?",
            answer=f"{child.label} looked carefully in the usual places, noticed the clue, and found {obj.it()} where it had been left.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The happy ending came when {child.label} got {obj.it()} back and the little worry disappeared.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or something unexplained that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What does crucial mean?",
            answer="Crucial means very important. If something is crucial, it really matters to what happens next.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that can help someone solve a puzzle or find something missing.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An object is eligible for the world when it can be found in the setting and is crucial.
eligible(P, O) :- place(P), object(O), can_find(P, O), crucial(O).

% A story is valid when it has one eligible object in one place.
valid_story(P, O) :- eligible(P, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for loc in setting.locations:
            lines.append(asp.fact("location", place, loc))
    for oid, obj in MYSTERY_OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("can_find", "kitchen", oid) if "kitchen" in obj.location else "")
        lines.append(asp.fact("can_find", "bedroom", oid) if "bedroom" in obj.location else "")
        lines.append(asp.fact("can_find", "living_room", oid) if "living_room" in obj.location else "")
        lines.append(asp.fact("crucial", oid))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in asp:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery about finding something crucial.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=MYSTERY_OBJECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place is not None:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_id is not None:
        combos = [c for c in combos if c[1] == args.object_id]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, object_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, object_id=object_id, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    obj = MYSTERY_OBJECTS[params.object_id]
    world = build_world(setting, obj, params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", object_id="key", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="bedroom", object_id="glasses", name="Leo", gender="boy", parent="father"),
    StoryParams(place="living_room", object_id="notebook", name="Nora", gender="girl", parent="mother"),
    StoryParams(place="living_room", object_id="scarf", name="Ben", gender="boy", parent="father"),
]


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
        print(f"{len(combos)} compatible (place, object) combos:\n")
        for place, oid in combos:
            print(f"  {place:12} {oid}")
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object_id} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
