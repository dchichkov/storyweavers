#!/usr/bin/env python3
"""
storyworlds/worlds/bandit_problem_solving_dialogue_mystery_to_solve.py
======================================================================

A small pirate-tale storyworld about a bandit mystery that gets solved by
careful thinking, dialogue, and a final clue.

Seed tale shape:
- A brave young pirate notices something strange.
- A bandit causes trouble or leaves behind a mystery.
- The crew talks it through, follows clues, and solves the problem.
- The ending proves what changed in the world: the clue is found, the worry
  is gone, and the ship can sail on.

This script keeps the simulation tiny and classical:
- typed entities with physical meters and emotional memes
- causal state drives prose
- a reasonableness gate ensures only solvable mysteries are generated
- an inline ASP twin mirrors the Python validity logic
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    breeze: str = ""


@dataclass
class Problem:
    id: str
    title: str
    mystery: str
    clue: str
    fix: str
    clue_kind: str


@dataclass
class StoryParams:
    problem: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    bandit_name: str
    bandit_type: str
    seed: Optional[int] = None


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


PROBLEMS = {
    "missing_map": Problem(
        id="missing_map",
        title="the missing map",
        mystery="a map page was gone from the cabin",
        clue="a wet scrap of map tucked under a barrel",
        fix="the crew can follow the scrap and put the map back together",
        clue_kind="map",
    ),
    "stolen_keys": Problem(
        id="stolen_keys",
        title="the stolen keys",
        mystery="the little brass keys were not in their hook",
        clue="a key print in the sand by the pier",
        fix="the crew can trace the print to the hiding spot",
        clue_kind="keys",
    ),
    "bent_compass": Problem(
        id="bent_compass",
        title="the bent compass",
        mystery="the ship's compass needle kept wobbling",
        clue="a tiny magnet hidden in a bandit's pouch",
        fix="the crew can remove the magnet and make the compass steady",
        clue_kind="compass",
    ),
}


SETTINGS = {
    "harbor": Setting(place="the harbor", breeze="salty"),
    "dock": Setting(place="the dock", breeze="salt-bright"),
    "cove": Setting(place="the cove", breeze="warm"),
    "ship": Setting(place="the little ship", breeze="windy"),
}


GENDERS = {
    "girl": ("girl", ["girl", "woman", "mother"]),
    "boy": ("boy", ["boy", "man", "father"]),
}


GIRL_NAMES = ["Mina", "Ruby", "Elsa", "Nina", "Ivy", "Lila", "Nora"]
BOY_NAMES = ["Finn", "Rowan", "Toby", "Jude", "Perry", "Eli", "Otis"]


class Reasoner:
    @staticmethod
    def valid(problem: Problem) -> bool:
        return bool(problem.clue and problem.fix and problem.mystery)

    @staticmethod
    def solve_possible(problem: Problem) -> bool:
        return problem.id in PROBLEMS and Reasoner.valid(problem)


def _say_title(world: World, hero: Entity, helper: Entity, bandit: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a little pirate who loved the sea, {helper.id} was a sharp-eyed helper, "
        f"and the bandit {bandit.id} had a way of making trouble near the water."
    )
    world.say(
        f"One day, {problem.mystery} at {world.setting.place}, and everyone felt the puzzle in their bones."
    )


def _raise_mystery(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} frowned and said, \"This is strange. {problem.title} should not be like this.\""
    )
    world.say("The crew looked around carefully, because good pirates know that clues can hide in plain sight.")


def _dialogue(world: World, hero: Entity, helper: Entity, bandit: Entity, problem: Problem) -> None:
    world.say(
        f'"Did you see anything?" {hero.id} asked. "Only a flutter and a splash," said {helper.id}.'
    )
    world.say(
        f'"I was near the barrels," muttered the bandit {bandit.id}, "but I did not take what was lost."'
    )
    helper.memes["thoughtful"] = helper.memes.get("thoughtful", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{helper.id} said, \"Then let us follow the clue and see where it leads.\""
    )


def _solve(world: World, hero: Entity, helper: Entity, bandit: Entity, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    bandit.memes["caught"] = 1.0
    world.say(
        f"They found {problem.clue}, and {hero.id} pointed and said, \"There! That tells us what happened.\""
    )
    world.say(
        f"Together they followed it until the truth came clear: {problem.fix}."
    )
    world.say(
        f"The bandit {bandit.id} could not hide the answer anymore, and the ship felt safe again."
    )


def tell(problem: Problem, hero_name: str, hero_type: str, helper_name: str, helper_type: str,
         bandit_name: str, bandit_type: str) -> World:
    world = World(random.choice(list(SETTINGS.values())))
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    bandit = world.add(Entity(id=bandit_name, kind="character", type=bandit_type))
    world.facts.update(hero=hero, helper=helper, bandit=bandit, problem=problem)

    _say_title(world, hero, helper, bandit, problem)
    world.para()
    _raise_mystery(world, hero, problem)
    _dialogue(world, hero, helper, bandit, problem)
    world.para()
    _solve(world, hero, helper, bandit, problem)
    world.facts["resolved"] = True
    return world


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = f["problem"]
    hero = f["hero"]
    helper = f["helper"]
    bandit = f["bandit"]
    return [
        f'Write a short pirate tale for a young child about "{problem.title}" and a bandit mystery.',
        f"Tell a story where {hero.id} and {helper.id} use dialogue to solve a mystery caused by bandit {bandit.id}.",
        f"Write a simple pirate story that begins with a strange problem, follows clues, and ends with the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bandit = f["bandit"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who noticed that {problem.mystery}?",
            answer=f"{hero.id} noticed the mystery first and spoke up right away.",
        ),
        QAItem(
            question=f"Who talked with {hero.id} about the clue?",
            answer=f"{helper.id} talked with {hero.id} and helped think it through.",
        ),
        QAItem(
            question=f"What did the bandit have to do with the problem?",
            answer=f"The bandit {bandit.id} was part of the trouble and helped make the mystery harder to understand.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"They followed {problem.clue} and used it to figure out that {problem.fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bandit?",
            answer="A bandit is a sneaky person who may steal things or cause trouble.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery.",
        ),
        QAItem(
            question="Why do people ask questions when solving a mystery?",
            answer="People ask questions to gather clues and understand what happened.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pirate tale about a bandit mystery to solve."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--bandit")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--bandit-gender", choices=["girl", "boy"])
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
    problem_id = args.problem or rng.choice(list(PROBLEMS))
    problem = PROBLEMS[problem_id]
    if not Reasoner.solve_possible(problem):
        raise StoryError("No story: this mystery has no honest clue and cannot be solved.")
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    bandit_gender = args.bandit_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    bandit_name = args.bandit or rng.choice(GIRL_NAMES if bandit_gender == "girl" else BOY_NAMES)
    hero_type = "girl" if gender == "girl" else "boy"
    helper_type = "girl" if helper_gender == "girl" else "boy"
    bandit_type = "girl" if bandit_gender == "girl" else "boy"
    return StoryParams(problem=problem_id, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type,
                       bandit_name=bandit_name, bandit_type=bandit_type)


def generate(params: StoryParams) -> StorySample:
    problem = PROBLEMS[params.problem]
    world = tell(problem, params.hero_name, params.hero_type,
                 params.helper_name, params.helper_type,
                 params.bandit_name, params.bandit_type)
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


ASP_RULES = r"""
problem(P) :- problem_id(P).
solvable(P) :- problem(P), clue(P), fix(P).
valid_story(P) :- solvable(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
        lines.append(asp.fact("clue", pid))
        lines.append(asp.fact("fix", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("missing_map",), ("stolen_keys",), ("bent_compass",)}
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} problems).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(problem="missing_map", hero_name="Mina", hero_type="girl",
                helper_name="Finn", helper_type="boy",
                bandit_name="Rook", bandit_type="boy"),
    StoryParams(problem="stolen_keys", hero_name="Jude", hero_type="boy",
                helper_name="Ruby", helper_type="girl",
                bandit_name="Mara", bandit_type="girl"),
    StoryParams(problem="bent_compass", hero_name="Nora", hero_type="girl",
                helper_name="Otis", helper_type="boy",
                bandit_name="Pike", bandit_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = asp.atoms(model, "valid_story")
        print(f"{len(vals)} solvable problems:")
        for (pid,) in vals:
            print(f"  {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
