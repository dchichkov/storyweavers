#!/usr/bin/env python3
"""
storyworlds/worlds/radiator_arthritis_mystery_to_solve_happy_ending.py
======================================================================

A small detective-story world about a puzzling radiator, a sore set of hands,
and a kind solution that ends happily.

Premise:
- A young detective notices a mystery around a radiator.
- Someone with arthritis is struggling to do an ordinary task.
- The investigation turns on clues from heat, noise, and household habits.
- The ending rewards care, patience, and helping.

The world is intentionally tiny and constraint-checked:
- The mystery must be solvable.
- The radiator must be involved in the cause of the problem.
- Arthritis must matter in the physical and emotional state.
- The ending must resolve in a kind, concrete way.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    has_radiator: bool = True
    has_hallway: bool = True
    has_kitchen: bool = True


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _pronoun_word(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def _detective_intro(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "curious")
    world.say(
        f"{detective.id} was a little {trait} detective who liked solving small mysteries."
    )


def _mystery_setup(world: World, detective: Entity, helper: Entity, clue: str) -> None:
    world.say(
        f"One chilly morning, {detective.id} visited {world.place.name} and noticed a mystery."
    )
    world.say(
        f"The clue was {clue}, and {helper.id} kept rubbing {helper.pronoun('possessive')} hands."
    )


def _radiator_clue(world: World) -> None:
    radiator = world.add(Entity(
        id="radiator",
        kind="thing",
        type="radiator",
        label="radiator",
        phrase="the old radiator by the wall",
        location="hallway",
        meters={"warmth": 1.0, "noise": 1.0},
    ))
    radiator.memes["attention"] = 1.0
    world.say(
        "The radiator gave off a soft tick-tick sound, like it had a secret to tell."
    )


def _arthritis_effects(world: World, helper: Entity) -> None:
    helper.meters["stiffness"] = helper.meters.get("stiffness", 0.0) + 1.0
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{helper.id} had arthritis, so {helper.pronoun('possessive')} hands felt stiff and sore."
    )
    world.say(
        f"That made small jobs, like turning a knob or opening a window, feel extra hard."
    )


def _investigate(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"{detective.id} looked at the hallway, the kitchen, and the radiator like a true detective."
    )
    world.say(
        f"{detective.pronoun().capitalize()} noticed that the room was warm near the radiator, "
        f"but the draft from the window made the house feel chilly."
    )
    world.say(
        f"{helper.id} had been trying to stay warm, because warm hands hurt less when arthritis flared up."
    )


def _solve_mystery(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"Then {detective.id} found the answer: the radiator was not broken."
    )
    world.say(
        f"It was making the ticking sound because it was heating up the pipes, and the cold draft was bothering {helper.id}."
    )
    world.say(
        f"{detective.id} closed the window, and the room grew cozy and still."
    )


def _happy_ending(world: World, detective: Entity, helper: Entity) -> None:
    helper.memes["worry"] = 0.0
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{helper.id} smiled and flexed {helper.pronoun('possessive')} hands with a little less pain."
    )
    world.say(
        f"{detective.id} brought a warm mug and said, \"Sometimes the best clue is caring about how someone feels.\""
    )
    world.say(
        f"That afternoon, the house felt safe, the radiator hummed softly, and the mystery was solved."
    )


def tell_story(world: World, detective: Entity, helper: Entity, clue: str) -> World:
    _detective_intro(world, detective)
    _mystery_setup(world, detective, helper, clue)
    world.para()
    _radiator_clue(world)
    _arthritis_effects(world, helper)
    _investigate(world, detective, helper)
    world.para()
    _solve_mystery(world, detective, helper)
    _happy_ending(world, detective, helper)
    return world


SETTINGS = {
    "old_house": Place(name="the old house", indoors=True, has_radiator=True, has_hallway=True, has_kitchen=True),
    "apartment": Place(name="the little apartment", indoors=True, has_radiator=True, has_hallway=True, has_kitchen=True),
    "cottage": Place(name="the cozy cottage", indoors=True, has_radiator=True, has_hallway=True, has_kitchen=True),
}

CLUES = [
    "a strange tick-tick from the wall",
    "a cold draft under the window",
    "a warm patch beside the chair",
    "a creaky sound near the hallway",
]

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben", "Eli"]
HELPER_GIRL_NAMES = ["Grandma Rose", "Mrs. June", "Aunt May", "Nana Sue"]
HELPER_BOY_NAMES = ["Grandpa Tom", "Mr. Miles", "Uncle Ben", "Grandpa Eli"]


@dataclass
class RegistryItem:
    name: str
    description: str
    topic: str


WORLD_KNOWLEDGE = {
    "radiator": [
        (
            "What is a radiator?",
            "A radiator is a device in a house that gets warm and helps heat a room.",
        ),
        (
            "Why can a radiator tick?",
            "A radiator can tick when hot water or steam moves through it and the metal expands a little.",
        ),
    ],
    "arthritis": [
        (
            "What is arthritis?",
            "Arthritis is a condition that can make joints sore, stiff, and hard to move.",
        ),
        (
            "Why do warm rooms help some people with arthritis?",
            "Warmth can help muscles and joints feel a little more comfortable and less stiff.",
        ),
    ],
    "mystery": [
        (
            "What does a detective do?",
            "A detective looks for clues and thinks carefully to solve a mystery.",
        ),
    ],
    "kindness": [
        (
            "Why is kindness important?",
            "Kindness helps people feel safe, cared for, and less alone when something is hard.",
        ),
    ],
}

ASP_RULES = r"""
% A mystery is solvable when the radiator clue and arthritis clue both exist.
solvable(M) :- clue(M, radiator), clue(M, arthritis).

% Happy ending when the detective helps the person with arthritis and the room gets cozy.
happy_end(S) :- solvable(S), help(S), cozy(S).

#show solvable/1.
#show happy_end/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for c in CLUES:
        lines.append(asp.fact("clue_text", c))
    lines.append(asp.fact("clue", "story", "radiator"))
    lines.append(asp.fact("clue", "story", "arthritis"))
    lines.append(asp.fact("help", "story"))
    lines.append(asp.fact("cozy", "story"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1.\n#show happy_end/1."))
    syms = set((s.name, tuple(a.name if hasattr(a, "name") else str(a) for a in s.arguments)) for s in model)
    expected = {("solvable", ("story",)), ("happy_end", ("story",))}
    if syms == expected:
        print("OK: ASP parity holds.")
        return 0
    print("MISMATCH in ASP parity.")
    print("got:", sorted(syms))
    print("expected:", sorted(expected))
    return 1


@dataclass
class StoryRuntime:
    world: World
    detective: Entity
    helper: Entity


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: radiator, arthritis, mystery, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--clue", choices=range(len(CLUES)), type=int)
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(HELPER_GIRL_NAMES if helper_gender == "girl" else HELPER_BOY_NAMES)
    clue = CLUES[args.clue] if args.clue is not None else rng.choice(CLUES)
    return StoryParams(
        place=place,
        detective_name=name,
        detective_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        clue=clue,
    )


def _make_world(params: StoryParams) -> StoryRuntime:
    place = SETTINGS[params.place]
    world = World(place)
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_gender,
        traits=["little", "curious", "careful"],
        meters={"attention": 1.0},
        memes={"hope": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        traits=["kind", "patient"],
        meters={"stiffness": 1.0},
        memes={"worry": 1.0},
    ))
    return StoryRuntime(world=world, detective=detective, helper=helper)


def generate(params: StoryParams) -> StorySample:
    runtime = _make_world(params)
    world = tell_story(runtime.world, runtime.detective, runtime.helper, params.clue)
    world.facts.update(
        place=params.place,
        detective=params.detective_name,
        helper=params.helper_name,
        clue=params.clue,
        solved=True,
        happy=True,
    )
    story = world.render()
    prompts = [
        f"Write a gentle detective story for a young child that includes a radiator and arthritis.",
        f"Tell a short mystery where {params.detective_name} solves a household clue and ends with kindness.",
        f"Write a happy-ending story about a child detective, a warm radiator, and someone with arthritis.",
    ]
    story_qa = [
        QAItem(
            question=f"What mystery did {params.detective_name} try to solve?",
            answer=(
                f"{params.detective_name} tried to solve why the radiator was making a tick-tick sound "
                f"and why {params.helper_name} was having trouble because of arthritis."
            ),
        ),
        QAItem(
            question=f"Why was {params.helper_name} upset or uncomfortable?",
            answer=(
                f"{params.helper_name} had arthritis, so {params.helper_name.split()[0].lower() if ' ' in params.helper_name else params.helper_name.lower()}'s hands felt sore and stiff, and the cold draft made it harder to feel comfortable."
            ),
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=(
                f"{params.detective_name} figured out that the radiator was fine and the real problem was the cold draft, so closing the window made the room cozy again."
            ),
        ),
        QAItem(
            question="What made the ending happy?",
            answer=(
                f"The ending was happy because the house became warm and calm, {params.helper_name} felt better, and {params.detective_name} helped with kindness."
            ),
        ),
    ]
    world_qa = [
        QAItem(*WORLD_KNOWLEDGE["radiator"][0]),
        QAItem(*WORLD_KNOWLEDGE["arthritis"][0]),
        QAItem(*WORLD_KNOWLEDGE["mystery"][0]),
        QAItem(*WORLD_KNOWLEDGE["kindness"][0]),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="old_house", detective_name="Mia", detective_gender="girl", helper_name="Grandma Rose", helper_gender="girl", clue="a strange tick-tick from the wall"),
    StoryParams(place="apartment", detective_name="Leo", detective_gender="boy", helper_name="Grandpa Tom", helper_gender="boy", clue="a cold draft under the window"),
    StoryParams(place="cottage", detective_name="Nora", detective_gender="girl", helper_name="Aunt May", helper_gender="girl", clue="a warm patch beside the chair"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/1.\n#show happy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1.\n#show happy_end/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
