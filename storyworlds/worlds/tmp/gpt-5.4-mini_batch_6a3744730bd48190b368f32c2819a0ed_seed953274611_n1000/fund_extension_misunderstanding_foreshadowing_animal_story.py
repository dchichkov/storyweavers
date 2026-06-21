#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fund_extension_misunderstanding_foreshadowing_animal_story.py
=============================================================================================

A standalone storyworld for a small animal-story domain built from the seed
words "fund" and "extension" with misunderstanding and foreshadowing.

Premise:
- Animals live in a cozy shelter.
- They are raising a fund for an extension: a bigger, warmer room.
- A misunderstanding makes one animal think the extension is a kind of
  exercise or trick, not a building addition.
- Foreshadowing plants clues: stacks of boards, a map, and a measuring tape.
- The misunderstanding is cleared up, and the ending shows the new space.

The world is intentionally small and classical: typed entities, physical meters,
emotional memes, a forward-chained rule engine, and state-driven prose.

Run:
    python storyworlds/worlds/gpt-5.4-mini/fund_extension_misunderstanding_foreshadowing_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/fund_extension_misunderstanding_foreshadowing_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/fund_extension_misunderstanding_foreshadowing_animal_story.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Animal:
    id: str
    sound: str
    kind: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    shelter_name: str
    cozy_spot: str
    future_spot: str
    feels: str


@dataclass
class Project:
    id: str
    noun: str
    phrase: str
    meaning: str
    clue: str


@dataclass
class Misunderstanding:
    id: str
    mistaken_meaning: str
    correction: str


@dataclass
class Foreshadow:
    id: str
    clue: str
    later_payoff: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_nervous(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.memes["worry"] >= THRESHOLD and ("nervous" not in world.fired):
            world.fired.add(("nervous",))
            world.get("leader").memes["patience"] += 1
            out.append("__narrate__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def predict_misunderstanding(world: World, animal: Animal, project: Project) -> dict:
    sim = world.copy()
    sim.get("leader").memes["worry"] += 1
    animal.memes["curiosity"] += 1
    return {
        "confused": True if project.id == "extension" else False,
        "needs_clarify": True,
    }


SETTINGS = {
    "shelter": Setting(
        id="shelter",
        place="the little animal shelter",
        shelter_name="the little animal shelter",
        cozy_spot="the warm corner by the hay",
        future_spot="the empty side room",
        feels="soft and busy",
    ),
    "farm": Setting(
        id="farm",
        place="the old farmyard",
        shelter_name="the old farmyard shelter",
        cozy_spot="the barn corner",
        future_spot="the open shed",
        feels="bright and windy",
    ),
}

PROJECTS = {
    "extension": Project(
        id="extension",
        noun="extension",
        phrase="an extension to the shelter",
        meaning="a new room added onto the shelter",
        clue="boards, a map, and a measuring tape",
    ),
}

MISUNDERSTANDINGS = {
    "extension": Misunderstanding(
        id="extension",
        mistaken_meaning="a long stretching exercise",
        correction="a bigger room added to the shelter",
    ),
}

FORESHADOWS = {
    "boards": Foreshadow(
        id="boards",
        clue="a neat stack of boards leaned by the door",
        later_payoff="the boards became the new wall",
    ),
    "map": Foreshadow(
        id="map",
        clue="a paper map showed an extra square behind the shelter",
        later_payoff="that square became the new room",
    ),
}

ANIMALS = {
    "Milo": Animal("Milo", "baa", "goat", "the shelter", ["curious", "lively"]),
    "Pip": Animal("Pip", "peep", "chick", "the shelter", ["careful", "small"]),
    "Dot": Animal("Dot", "woof", "puppy", "the shelter", ["kind", "eager"]),
}


@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    project: str
    misunderstanding: str
    foreshadow: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="shelter", animal1="Milo", animal2="Pip", project="extension", misunderstanding="extension", foreshadow="boards", seed=1),
    StoryParams(setting="farm", animal1="Dot", animal2="Milo", project="extension", misunderstanding="extension", foreshadow="map", seed=2),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("shelter", a1, a2) for a1 in ANIMALS for a2 in ANIMALS if a1 != a2]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: fund, extension, misunderstanding, foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    a1 = args.animal1 or rng.choice(list(ANIMALS))
    a2 = args.animal2 or rng.choice([a for a in ANIMALS if a != a1])
    if a1 == a2:
        raise StoryError("The two animals must be different so the misunderstanding can play out clearly.")
    return StoryParams(
        setting=setting,
        animal1=a1,
        animal2=a2,
        project=args.project or "extension",
        misunderstanding=args.misunderstanding or "extension",
        foreshadow=args.foreshadow or rng.choice(list(FORESHADOWS)),
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    if not setting:
        raise StoryError("Unknown setting.")
    project = PROJECTS.get(params.project)
    if not project:
        raise StoryError("Unknown project.")
    misunderstanding = MISUNDERSTANDINGS.get(params.misunderstanding)
    if not misunderstanding:
        raise StoryError("Unknown misunderstanding.")
    foreshadow = FORESHADOWS.get(params.foreshadow)
    if not foreshadow:
        raise StoryError("Unknown foreshadow.")
    a = ANIMALS[params.animal1]
    b = ANIMALS[params.animal2]

    world = World(setting)
    leader = world.add(Entity(id="leader", kind="character", type="hen", label="the old hen"))
    a_ent = world.add(Entity(id=a.id, kind="character", type=a.kind, label=a.id))
    b_ent = world.add(Entity(id=b.id, kind="character", type=b.kind, label=b.id))
    world.facts.update(setting=setting, project=project, misunderstanding=misunderstanding, foreshadow=foreshadow, a=a_ent, b=b_ent, leader=leader)

    leader.memes["hope"] += 1
    world.say(
        f"In {setting.shelter_name}, {a.id} and {b.id} heard that the family was raising a fund for {project.phrase}."
    )
    world.say(
        f'{a.id} peered at the notice and said, "Maybe {project.noun} means something to stretch and exercise?" '
        f'{b.id} blinked. "I thought it meant a bigger room."'
    )
    world.say(
        f"The shelter felt {setting.feels}, but {foreshadow.clue} near the wall."
    )

    world.para()
    a_ent.memes["curiosity"] += 1
    b_ent.memes["care"] += 1
    world.say(
        f"The old hen shook out a clean paper with a pencil sketch. It showed {project.meaning}."
    )
    world.say(
        f'"No, no," she clucked gently. "{project.noun} is not a stretch. It is {project.meaning}."'
    )
    world.say(
        f'{a.id} looked embarrassed, and {b.id} gave a small nod. The misunderstanding floated away like a feather.'
    )

    world.para()
    leader.meters["progress"] += 1
    world.say(
        f"After that, everyone helped with the fund. {a.id} carried nails, {b.id} carried a tin cup, and the old hen counted the coins."
    )
    world.say(
        f"When the builders came, {foreshadow.later_payoff}. Soon {setting.future_spot} became bright, dry, and ready for smaller paws."
    )
    world.say(
        f"That night, {a.id} and {b.id} curled up together and watched the new extension glow under the lamp, a little bigger than before and much kinder."
    )
    world.facts["outcome"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an animal story that uses the words "fund" and "extension" and includes a clear misunderstanding.',
        f"Tell a gentle story where {world.facts['a'].id} and {world.facts['b'].id} help with a fund for {world.facts['project'].noun}, but one animal first thinks it means something else.",
        "Write a foreshadowed animal story with a cozy shelter, a correction, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b = world.facts["a"], world.facts["b"]
    project = world.facts["project"]
    misunderstanding = world.facts["misunderstanding"]
    foreshadow = world.facts["foreshadow"]
    return [
        QAItem(
            question=f"What was the fund for?",
            answer=f"It was for {project.phrase}. That would give the shelter more space and make it warmer for the animals.",
        ),
        QAItem(
            question=f"What misunderstanding did {a.id} have?",
            answer=f"{a.id} thought {project.noun} meant {misunderstanding.mistaken_meaning}. The old hen corrected that and explained it was {project.meaning}.",
        ),
        QAItem(
            question="How did the foreshadowing help the story?",
            answer=f"The story showed {foreshadow.clue} before the building work began. That clue hinted that the new room was already planned and would matter later.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fund?",
            answer="A fund is money collected for a shared goal, like building something or helping others.",
        ),
        QAItem(
            question="What is an extension?",
            answer="An extension is an extra part added onto something, like a new room added to a shelter.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at something important before it happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
chosen_setting(shelter).
chosen_project(extension).
misunderstanding(extension).
foreshadow(boards).

valid(setting, project, misunderstanding) :- chosen_setting(setting), chosen_project(project), misunderstanding(project).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROJECTS:
        lines.append(asp.fact("project", p))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for f in FORESHADOWS:
        lines.append(asp.fact("foreshadow", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP/Python combo gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as e:
        raise StoryError(f"Invalid parameter: {e.args[0]}") from None
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
