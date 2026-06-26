#!/usr/bin/env python3
"""
storyworlds/worlds/amuse_tinker_important_bad_ending_mystery.py
===============================================================

A small mystery story world about an important object, a curious tinker, and an
ending that stays bad in a child-safe, concrete way.

The core premise is simple:
- a child tries to amuse themselves by tinkering with an important thing,
- their tinkering causes a strange mystery,
- clues point in a few directions,
- but the final outcome is a bad ending: the important thing remains broken or
  lost, and the mystery is not fully solved.

The world is intentionally narrow so the generated stories stay coherent.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False
    broken: bool = False

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    mood: str
    clue_place: str
    secret_place: str


@dataclass
class Case:
    name: str
    important_item: str
    cause: str
    clue: str
    bad_result: str
    tinker_tool: str
    amusement: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty", clue_place="under the boxes", secret_place="behind the old trunk"),
    "shed": Setting(place="the shed", mood="creaky", clue_place="inside the toolbox", secret_place="under the loose plank"),
    "library": Setting(place="the library corner", mood="quiet", clue_place="between the books", secret_place="behind the atlas"),
}

CASES = {
    "music_box": Case(
        name="music box",
        important_item="music box",
        cause="a missing spring",
        clue="a tiny brass spring",
        bad_result="the box only clicked and would not play",
        tinker_tool="a small screwdriver",
        amusement="a funny tick-tick sound",
    ),
    "lantern": Case(
        name="lantern",
        important_item="lantern",
        cause="a loose wick",
        clue="a singed thread",
        bad_result="the lantern stayed dark",
        tinker_tool="a bent spoon",
        amusement="a wobbly glow that flickered",
    ),
    "clock": Case(
        name="clock",
        important_item="clock",
        cause="a jammed gear",
        clue="a rusty gear tooth",
        bad_result="the clock lost its song and stopped",
        tinker_tool="a pocket magnet",
        amusement="a loud tick that made the child grin",
    ),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ivy", "June"],
    "boy": ["Theo", "Ben", "Owen", "Eli", "Max"],
}

HELPERS = ["mother", "father", "grandmother", "grandfather"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    case = args.case or rng.choice(list(CASES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, case=case, name=name, gender=gender, helper=helper)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.case not in CASES:
        raise StoryError("Unknown mystery case.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if not params.name.strip():
        raise StoryError("The child needs a name.")


def _setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    world = World(setting)
    child = world.add(Character(
        id=params.name,
        type=params.gender,
        traits=["curious", "bouncy"],
        meters={"amuse": 0.0, "tinker": 0.0},
        memes={"wonder": 1.0, "worry": 0.0},
    ))
    helper = world.add(Character(
        id=params.helper.title(),
        type=params.helper,
        label=f"the {params.helper}",
        traits=["important", "watchful"],
    ))
    item = world.add(Item(
        id=case.name.replace(" ", "_"),
        type=case.important_item,
        label=case.important_item,
        phrase=f"the important {case.important_item}",
        owner=params.name,
        location=setting.place,
        meters={"whole": 1.0},
        memes={"important": 1.0},
    ))
    clue = world.add(Item(
        id="clue",
        type="clue",
        label="clue",
        phrase=case.clue,
        location=setting.clue_place,
        hidden=True,
    ))
    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        clue=clue,
        case=case,
        setting=setting,
    )
    return world


def _narrate_setup(world: World) -> None:
    f = world.facts
    child: Character = f["child"]
    helper: Character = f["helper"]
    item: Item = f["item"]
    case: Case = f["case"]
    setting: Setting = f["setting"]

    world.say(
        f"{child.id} was a curious child who liked to amuse {child.pronoun('object')}self by tinkering with little things."
    )
    world.say(
        f"One important day, {child.id} noticed the {item.label} in {setting.place}."
    )
    world.say(
        f"{child.id} thought {case.amusement} would be funny, and {child.pronoun()} picked up {case.tinker_tool}."
    )
    world.say(
        f"{helper.label.capitalize()} said the {item.label} was important and should be left alone, but the room was so quiet that {child.id} kept peeking at {item.it()} anyway."
    )


def _narrate_mystery(world: World) -> None:
    f = world.facts
    child: Character = f["child"]
    helper: Character = f["helper"]
    item: Item = f["item"]
    case: Case = f["case"]
    setting: Setting = f["setting"]

    child.meters["amuse"] += 1.0
    child.meters["tinker"] += 1.0
    child.memes["worry"] += 1.0

    world.para()
    world.say(
        f"At {setting.place}, {child.id} turned a tiny screw, and {case.amusement} made {child.pronoun('object')} smile."
    )
    world.say(
        f"Then something strange happened: a small piece slipped away, and the {item.label} stopped acting right."
    )
    world.say(
        f"{child.id} checked {setting.clue_place}, and there was {case.clue}."
    )
    world.say(
        f"{helper.label.capitalize()} looked at the clue and frowned, because now the mystery was getting bigger instead of smaller."
    )
    world.say(
        f"{child.id} wanted to fix it fast, but every careful turn made the {item.label} quieter and more stubborn."
    )


def _narrate_bad_ending(world: World) -> None:
    f = world.facts
    child: Character = f["child"]
    helper: Character = f["helper"]
    item: Item = f["item"]
    case: Case = f["case"]
    setting: Setting = f["setting"]

    item.broken = True
    item.meters["whole"] = 0.0
    helper.memes["worry"] = 1.0
    child.memes["worry"] = 1.0

    world.para()
    world.say(
        f"{child.id} and {helper.label} searched {setting.secret_place}, but the missing piece was not there."
    )
    world.say(
        f"The clue fit the problem, yet it did not lead to a real fix."
    )
    world.say(
        f"In the end, the {item.label} stayed broken, and {case.bad_result}."
    )
    world.say(
        f"{child.id} felt sad, because the important thing could not be put right before night came."
    )
    world.say(
        f"The last light in {setting.place} was small and dim, and the mystery stayed unsolved."
    )


def generate_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = _setup_world(params)
    _narrate_setup(world)
    _narrate_mystery(world)
    _narrate_bad_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Character = f["child"]
    item: Item = f["item"]
    case: Case = f["case"]
    return [
        f'Write a child-friendly mystery story about {child.id} who likes to amuse {child.pronoun("object")}self by tinkering with an important {item.label}.',
        f"Tell a short mystery where a curious child makes a small mistake, finds a clue, and cannot fully fix the important {item.label}.",
        f"Write a simple story with the words amuse, tinker, and important, and end with a bad ending for the {item.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Character = f["child"]
    helper: Character = f["helper"]
    item: Item = f["item"]
    case: Case = f["case"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"What did {child.id} try to do with the important {item.label}?",
            answer=f"{child.id} tried to tinker with the important {item.label} to amuse {child.pronoun('object')}self."
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"The mystery happened in {setting.place}, where the important {item.label} was sitting."
        ),
        QAItem(
            question=f"What clue did {child.id} find?",
            answer=f"{child.id} found {case.clue} while looking around {setting.clue_place}."
        ),
        QAItem(
            question=f"Why was {helper.label} worried?",
            answer=f"{helper.label.capitalize()} was worried because the {item.label} was important, and tinkering with it made it stop working right."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the {item.label} stayed broken, the mystery was not fully solved, and everyone felt sad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to tinker with something?",
            answer="To tinker with something means to handle it, adjust it, or try to fix it with small careful changes."
        ),
        QAItem(
            question="What does it mean when something is important?",
            answer="When something is important, it matters a lot and people should take care of it."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange or puzzling that people try to understand."
        ),
    ]


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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        if isinstance(ent, Character):
            lines.append(f"{ent.id}: character meters={ent.meters} memes={ent.memes}")
        else:
            lines.append(
                f"{ent.id}: thing type={ent.type} label={ent.label} location={ent.location} broken={ent.broken} hidden={ent.hidden} meters={ent.meters}"
            )
    return "\n".join(lines)


ASP_RULES = r"""
% A child's tinkering can create an obvious clue, but a bad ending leaves the
% important object broken and the mystery unsolved.

amuses(C) :- child(C), meter(C, amuse, V), V >= 1.
tinkers(C) :- child(C), meter(C, tinker, V), V >= 1.
important(I) :- thing(I), meter(I, important, V), V >= 1.

bad_ending(I) :- important(I), meter(I, whole, V), V < 1.
unsolved(I) :- bad_ending(I), clue_present(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("important_name", case.important_item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [
    StoryParams(place="attic", case="music_box", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="shed", case="lantern", name="Theo", gender="boy", helper="father"),
    StoryParams(place="library", case="clock", name="Nora", gender="girl", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1.\n#show unsolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.case} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
