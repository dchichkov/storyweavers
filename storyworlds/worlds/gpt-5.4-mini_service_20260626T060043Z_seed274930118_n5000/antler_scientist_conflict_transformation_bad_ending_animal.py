#!/usr/bin/env python3
"""
A standalone Storyweavers world: an animal story about a scientist, antlers,
conflict, transformation, and a bad ending.

Premise:
- A small scientist works in a quiet clearing beside a forest.
- An antlered animal wants a shiny object the scientist keeps for a careful
  experiment.
- The conflict grows, then a strange transformation changes what the animal is.
- The ending is bad in a gentle, child-facing way: the goal is lost, and the
  scientist's careful work is ruined.

This file is self-contained except for the shared result containers.
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

ANTLER_THRESHOLD = 1.0
FEAR_THRESHOLD = 1.0
DAMAGE_THRESHOLD = 1.0

ANIMAL_TYPES = [
    "deer",
    "rabbit",
    "fox",
    "bear",
    "moose",
]

SCIENTIST_TYPES = [
    "scientist",
    "researcher",
    "helper",
]

NAMES = [
    "Milo",
    "Tessa",
    "Robin",
    "Pip",
    "Nora",
    "Arlo",
    "Luna",
    "Bram",
]

PLACES = [
    "forest clearing",
    "quiet meadow",
    "edge of the woods",
    "small field",
]

OBJECTS = [
    "glass jar",
    "silver horn",
    "bright lens",
    "careful chart",
]

TRANSFORMATIONS = [
    "changed from a small animal into a bigger one",
    "turned into a statue-like shape for a moment",
    "grew strange glowing antlers",
    "became very still and stiff",
]

ASP_RULES = r"""
% Conflict appears when an animal with antlers tries to take the scientist's object.
conflict(A) :- antlered(A), wants_object(A), scientist_has_object(S, O), object(O), scientist(S), antlered(A).

% Transformation can happen after conflict reaches the threshold.
transform(A) :- conflict(A), tense(A).

% A bad ending happens when the object is ruined and the animal does not get it.
bad_ending(S, A) :- scientist(S), animal(A), ruined(O), scientist_has_object(S, O), conflict(A).

#show conflict/1.
#show transform/1.
#show bad_ending/2.
"""


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"scientist", "researcher", "helper"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.kind == "character" and self.type in {"deer", "fox", "rabbit", "bear", "moose"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str


@dataclass
class StoryThing:
    label: str
    phrase: str


@dataclass
class StoryParams:
    place: str
    scientist_name: str
    scientist_type: str
    animal_name: str
    animal_type: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: scientist, antler, conflict, transformation, bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    scientist_name = rng.choice(NAMES)
    scientist_type = rng.choice(SCIENTIST_TYPES)
    animal_name = rng.choice([n for n in NAMES if n != scientist_name])
    animal_type = rng.choice(ANIMAL_TYPES)
    obj = rng.choice(OBJECTS)
    return StoryParams(
        place=place,
        scientist_name=scientist_name,
        scientist_type=scientist_type,
        animal_name=animal_name,
        animal_type=animal_type,
        object=obj,
    )


def introduce(world: World, scientist: Entity, animal: Entity, obj: Entity) -> None:
    world.say(
        f"{scientist.label} was a small {scientist.type} who worked near the {world.setting.place}."
    )
    world.say(
        f"{animal.label} was a little {animal.type} with proud antlers, and {animal.pronoun('subject')} kept watching the shiny {obj.label}."
    )


def build_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    scientist = world.add(Entity(
        id="scientist",
        kind="character",
        type=params.scientist_type,
        label=params.scientist_name,
        meters={"care": 1.0, "work": 1.0},
        memes={"calm": 1.0},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="character",
        type=params.animal_type,
        label=params.animal_name,
        meters={"energy": 1.0},
        memes={"want": 1.0, "conflict": 0.0, "fear": 0.0, "change": 0.0},
    ))
    object_ent = world.add(Entity(
        id="object",
        kind="thing",
        type="object",
        label=params.object,
        phrase=f"a careful {params.object}",
        owner=scientist.id,
        meters={"fragile": 1.0, "shine": 1.0},
    ))
    antlers = world.add(Entity(
        id="antlers",
        kind="thing",
        type="antlers",
        label="antlers",
        phrase="a pair of antlers",
        owner=animal.id,
        meters={"hardness": 1.0},
    ))

    world.facts.update(
        scientist=scientist,
        animal=animal,
        object=object_ent,
        antlers=antlers,
    )

    introduce(world, scientist, animal, object_ent)
    world.para()
    world.say(
        f"One day, {animal.label} wanted the shiny {object_ent.label} for {animal.pronoun('possessive')} own game."
    )
    world.say(
        f"{scientist.label} said the {object_ent.label} was for a careful experiment and would break if it was grabbed."
    )

    animal.memes["want"] += 1.0
    animal.memes["conflict"] += 1.0
    scientist.memes["worry"] = 1.0
    object_ent.meters["risk"] = 1.0

    world.para()
    world.say(
        f"{animal.label} stepped closer, and the antlers caught the light while {animal.pronoun('subject')} huffed in frustration."
    )
    world.say(
        f"{scientist.label} held the {object_ent.label} tight, because the little experiment mattered."
    )

    animal.memes["fear"] += 1.0
    animal.memes["change"] += 1.0
    animal.meters["strain"] = 1.0

    world.para()
    world.say(
        f"Then the air in the clearing felt strange. {animal.label} {random.choice(TRANSFORMATIONS)}."
    )
    world.say(
        f"{animal.label} looked surprised by the change, but the wish for the {object_ent.label} did not go away."
    )

    object_ent.meters["shaken"] = 1.0
    object_ent.meters["ruined"] = 1.0
    scientist.memes["sad"] = 1.0

    world.para()
    world.say(
        f"In the end, the {object_ent.label} slipped to the ground and cracked."
    )
    world.say(
        f"{scientist.label} could not finish the experiment, and {animal.label} could not take the shiny thing home."
    )
    world.say(
        f"The clearing grew quiet, and the bad day stayed with them like a dull shadow."
    )

    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scientist: Entity = f["scientist"]
    animal: Entity = f["animal"]
    obj: Entity = f["object"]
    return [
        f"Write a short animal story about {animal.label}, a {animal.type} with antlers, and {scientist.label}, a {scientist.type}, fighting over a {obj.label}.",
        f"Tell a gentle but sad story where a scientist and an antlered animal have a conflict, a transformation happens, and the ending is bad.",
        f"Write a child-friendly story set in a {world.setting.place} about {scientist.label} and {animal.label} that ends with a broken {obj.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scientist: Entity = f["scientist"]
    animal: Entity = f["animal"]
    obj: Entity = f["object"]
    return [
        QAItem(
            question=f"Who was the scientist in the story?",
            answer=f"The scientist was {scientist.label}, a small {scientist.type} near the {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {animal.label} want from {scientist.label}?",
            answer=f"{animal.label} wanted the shiny {obj.label}, even though {scientist.label} said it was for an experiment.",
        ),
        QAItem(
            question="What changed during the middle of the story?",
            answer=f"{animal.label} had a strange transformation after the conflict grew, but the wish for the {obj.label} stayed the same.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the {obj.label} cracked, the experiment could not be finished, and nobody got a happy win.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are antlers?",
            answer="Antlers are hard, branched growths on some animals like deer and moose, and they are often used for showing off or fighting.",
        ),
        QAItem(
            question="What does a scientist do?",
            answer="A scientist asks questions, watches closely, and does experiments to learn how things work.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when characters want different things and their wishes clash.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:9} ({e.kind:8} {e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest clearing", scientist_name="Milo", scientist_type="scientist", animal_name="Pip", animal_type="deer", object="glass jar"),
    StoryParams(place="quiet meadow", scientist_name="Nora", scientist_type="researcher", animal_name="Tessa", animal_type="fox", object="bright lens"),
]


ASP_RULES = ASP_RULES


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("scientist", "s1"))
    lines.append(asp.fact("animal", "a1"))
    lines.append(asp.fact("object", "o1"))
    lines.append(asp.fact("antlered", "a1"))
    lines.append(asp.fact("wants_object", "a1"))
    lines.append(asp.fact("scientist_has_object", "s1", "o1"))
    lines.append(asp.fact("tense", "a1"))
    lines.append(asp.fact("ruined", "o1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show transform/1.\n#show bad_ending/2."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {("conflict", ("a1",)), ("transform", ("a1",)), ("bad_ending", ("s1", "a1"))}
    if atoms == expected:
        print("OK: ASP rules match the expected bad-ending animal story facts.")
        return 0
    print("MISMATCH:", atoms)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show transform/1.\n#show bad_ending/2."))
        return
    if args.asp:
        print(asp_program("#show conflict/1.\n#show transform/1.\n#show bad_ending/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
