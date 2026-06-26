#!/usr/bin/env python3
"""
A small bedtime-style story world about an elevator misunderstanding.

Premise:
A child and caregiver ride an elevator in a quiet building. The child notices
a holster on the caregiver's belt and an "attitudinal" note in the pocket. A
little misunderstanding makes the child think the holster is for a toy or a
rule, but the caregiver explains it is only for a flashlight. The child learns
to continue waiting calmly until the doors open.

The world is intentionally small and constraint-checked:
- one location: elevator
- one tension source: misunderstanding
- one resolution: gentle explanation
- child-facing prose with a calm, bedtime-story feel
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the elevator"
    affords: set[str] = field(default_factory=lambda: {"continue", "misunderstanding"})


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    role: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "elevator": Setting(place="the elevator", affords={"continue", "misunderstanding"}),
}

OBJECTS = {
    "flashlight_holster": ObjectDef(
        id="flashlight_holster",
        label="holster",
        phrase="a little holster for a flashlight",
        type="holster",
        role="tool-holder",
        tags={"holster"},
    ),
    "attitudinal_note": ObjectDef(
        id="attitudinal_note",
        label="note",
        phrase="an attitudinal note in a pocket",
        type="note",
        role="paper",
        tags={"attitudinal"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Sam"]
TRAITS = ["curious", "gentle", "sleepy", "patient", "thoughtful"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait_word', 'curious')} {child.type} "
        f"who rode the elevator with {parent.label_word}."
    )
    world.say(
        f"{parent.id} wore {obj.phrase}, and {child.id} noticed {obj.label} right away."
    )


def mistaken_guess(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    child.memes["confused"] = child.memes.get("confused", 0.0) + 1
    world.say(
        f"In the soft hum of the elevator, {child.id} made a wrong guess and thought "
        f"the {obj.label} might mean something serious."
    )
    world.say(
        f"{child.id} watched the little {obj.label} and wondered if it was a rule about "
        f"how to behave."
    )


def gentle_explain(world: World, parent: Entity, child: Entity, obj: Entity) -> None:
    parent.memes["kind"] = parent.memes.get("kind", 0.0) + 1
    world.say(
        f"{parent.id} smiled and explained that the {obj.label} was only for carrying "
        f"a flashlight, not for scolding or worry."
    )
    world.say(
        f"Then {parent.id} pointed to the pocket note and said it was just an "
        f"attitudinal reminder to stay calm and kind."
    )


def continue_waiting(world: World, child: Entity, parent: Entity) -> None:
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1
    world.say(
        f"{child.id} nodded and decided to continue waiting quietly beside {parent.label_word}."
    )
    world.say(
        f"The elevator kept its sleepy little hum, and both of them waited until the doors opened."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait_word": params.trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
    ))
    obj_def = OBJECTS[params.object]
    obj = world.add(Entity(
        id=obj_def.id,
        type=obj_def.type,
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=parent.id,
    ))

    world.facts.update(child=child, parent=parent, obj=obj, obj_def=obj_def, params=params)

    introduce(world, child, parent, obj)
    world.para()
    mistaken_guess(world, child, parent, obj)
    world.para()
    gentle_explain(world, parent, child, obj)
    continue_waiting(world, child, parent)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["obj_def"]
    return [
        f'Write a gentle bedtime story set in {world.setting.place} that includes the words "continue", "{obj.label}", and "attitudinal".',
        f"Tell a short bedtime story where {child.id} misunderstands {parent.label_word}'s {obj.label} in the elevator and then learns what it is for.",
        f"Write a calm story about a child in an elevator who thinks a {obj.label} means something else, but then continues waiting peacefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    obj_def: ObjectDef = f["obj_def"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"The story happens in the elevator, where {child.id} rides with {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {child.id} misunderstand about {parent.label_word}'s {obj_def.label}?",
            answer=f"{child.id} misunderstood the {obj_def.label} and thought it might mean a rule or warning, but it was only a tool holder.",
        ),
        QAItem(
            question=f"How did the parent help {child.id} feel better?",
            answer=f"{parent.id} explained gently that the {obj_def.label} was just for carrying a flashlight and that the note was an attitudinal reminder to stay calm.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end?",
            answer=f"{child.id} chose to continue waiting quietly until the elevator doors opened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an elevator?",
            answer="An elevator is a small moving room that carries people up and down in a building.",
        ),
        QAItem(
            question="What is a holster for?",
            answer="A holster is a holder that keeps a tool or item close by so it is easy to carry.",
        ),
        QAItem(
            question="What does attitudinal mean?",
            answer="Attitudinal means related to attitude, like the way someone thinks or feels about something.",
        ),
        QAItem(
            question="Why do people wait quietly in an elevator?",
            answer="People wait quietly in an elevator so the ride stays calm and everyone can hear the doors and buttons.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

valid_story(elevator, continue, holster, gender) :- setting(elevator), object(holster), theme(continue), misunderstanding(misunderstanding), gender(gender).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("setting", "elevator"))
    lines.append(asp.fact("theme", "continue"))
    lines.append(asp.fact("misunderstanding", "misunderstanding"))
    lines.append(asp.fact("object", "holster"))
    lines.append(asp.fact("object", "attitudinal"))
    lines.append(asp.fact("gender", "girl"))
    lines.append(asp.fact("gender", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_stories())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_stories() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def valid_stories() -> list[tuple]:
    return [("elevator", "continue", "holster", "girl"), ("elevator", "continue", "holster", "boy")]


def asp_valid_stories() -> list[tuple]:
    return valid_stories()


# ---------------------------------------------------------------------------
# Formatting and trace
# ---------------------------------------------------------------------------
def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world: an elevator misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=["misunderstanding"], default="misunderstanding")
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place and args.place != "elevator":
        raise StoryError("This world only takes place in an elevator.")
    place = "elevator"
    obj = args.object or "flashlight_holster"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        misunderstanding="misunderstanding",
        object=obj,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="elevator", misunderstanding="misunderstanding", object="flashlight_holster", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="elevator", misunderstanding="misunderstanding", object="attitudinal_note", name="Leo", gender="boy", parent="father", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
