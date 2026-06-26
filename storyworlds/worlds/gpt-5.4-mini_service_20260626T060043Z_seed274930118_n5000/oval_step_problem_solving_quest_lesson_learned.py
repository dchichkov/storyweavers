#!/usr/bin/env python3
"""
Storyworld: an oval step quest with problem solving and a lesson learned.

A small child-friend finds an oval pebble on a step, then goes on a tiny quest
to solve a problem: the pebble keeps rolling away. The child learns to choose a
better place for it, and the ending image proves the change.

The prose aims for a rhyming-story feel: simple, concrete, and gently musical.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Content registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    affordance: str


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    consequence: str
    quest_word: str
    meter: str


@dataclass
class Solution:
    id: str
    label: str
    method: str
    effect: str
    fits: set[str]


SETTINGS = {
    "garden": Setting(place="the garden", affordance="small paths"),
    "yard": Setting(place="the yard", affordance="sunny corners"),
    "porch": Setting(place="the porch", affordance="front steps"),
    "path": Setting(place="the stone path", affordance="little ledges"),
}

PROBLEMS = {
    "roll": Problem(
        id="roll",
        noun="oval pebble",
        verb="rolled",
        consequence="kept slipping away",
        quest_word="find a safe spot",
        meter="wobble",
    ),
    "chip": Problem(
        id="chip",
        noun="oval clay cup",
        verb="chipped",
        consequence="had a little crack",
        quest_word="fix the crack",
        meter="crack",
    ),
    "drop": Problem(
        id="drop",
        noun="oval egg",
        verb="dropped",
        consequence="almost broke",
        quest_word="carry it carefully",
        meter="care",
    ),
}

SOLUTIONS = {
    "nest": Solution(
        id="nest",
        label="a soft nest of moss",
        method="make a soft nest of moss",
        effect="stayed still and snug",
        fits={"roll"},
    ),
    "shelf": Solution(
        id="shelf",
        label="a low shelf under the bench",
        method="place it on a low shelf",
        effect="rested high and safe",
        fits={"chip", "drop"},
    ),
    "box": Solution(
        id="box",
        label="a little box with a lid",
        method="put it in a little box",
        effect="sat tight and tidy",
        fits={"drop", "roll"},
    ),
}


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    gender: str
    lesson: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mina", "Lila", "Nora", "Pia", "Zoe", "Ivy"]
NAMES_BOY = ["Owen", "Finn", "Milo", "Theo", "Noah", "Ezra"]
LESSONS = [
    "small things need a smart place",
    "a careful choice can stop a wobble",
    "a gentle plan can solve a tricky thing",
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
class StoryState:
    def __init__(self, world: World, hero: Entity, object_: Entity, problem: Problem, solution: Solution):
        self.world = world
        self.hero = hero
        self.object = object_
        self.problem = problem
        self.solution = solution
        self.resolved = False
        self.quest_done = False

    def set_problem(self) -> None:
        self.object.meters[self.problem.meter] = 1
        self.hero.memes["worry"] = 1
        self.world.facts["problem_started"] = True

    def quest(self) -> None:
        self.hero.memes["quest"] = 1
        self.world.facts["quest"] = self.problem.quest_word

    def solve(self) -> None:
        self.resolved = True
        self.quest_done = True
        self.object.meters[self.problem.meter] = 0
        self.object.meters["safe"] = 1
        self.hero.memes["joy"] = 1
        self.hero.memes["lesson"] = 1
        self.world.facts["resolved"] = True


def speak_intro(world: World, hero: Entity, obj: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} found an {obj.label} by the step, "
        f"and it was a sweet little sight."
    )
    world.say(
        f"But the {obj.label} {problem.consequence}, so the day turned from bright to a bit untidy."
    )


def speak_quest(world: World, hero: Entity, obj: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} took a small quest to {problem.quest_word}, "
        f"with tiny feet on the step."
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked left and looked right, then searched the light, "
        f"for a way to keep the {obj.label} neat."
    )


def speak_solution(world: World, hero: Entity, obj: Entity, solution: Solution) -> None:
    world.say(
        f"Then {hero.pronoun().capitalize()} had a thought that was quick and sweet: "
        f"{solution.method}."
    )
    world.say(
        f"Soon the {obj.label} {solution.effect}, and the little plan was a cheerful feat."
    )


def speak_lesson(world: World, hero: Entity, obj: Entity, lesson: str) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} smiled and learned a lesson, neat and clear: {lesson}."
    )
    world.say(
        f"At the end, the {obj.label} sat safe on the step-side scene, "
        f"and the day felt calm and clean."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem exists when an object is at risk in the setting.
at_risk(P) :- problem(P), setting(S), placed_on(P,S).

% A solution is reasonable when it fits the problem.
fits_solution(Sol, Prob) :- solution(Sol), problem(Prob), matches(Sol, Prob).

% A complete story is valid only if the chosen solution fits the problem.
valid_story(Place, Prob, Sol) :- setting(Place), problem(Prob), solution(Sol), fits_solution(Sol, Prob).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_noun", pid, p.noun))
        lines.append(asp.fact("placed_on", pid, "step"))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for fit in sorted(s.fits):
            lines.append(asp.fact("matches", sid, fit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / validation
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for prob_id, prob in PROBLEMS.items():
            for sol_id, sol in SOLUTIONS.items():
                if prob_id in sol.fits:
                    out.append((place, prob_id, sol_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: an oval step quest with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--lesson", choices=range(len(LESSONS)), type=int)
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
    combos = valid_stories()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    prob = PROBLEMS[problem]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    lesson = LESSONS[args.lesson] if args.lesson is not None else rng.choice(LESSONS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, gender=gender, lesson=lesson)


def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTINGS[params.place].place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    prob = PROBLEMS[params.problem]
    sol = SOLUTIONS[params.solution]
    obj = world.add(Entity(id="object", type=prob.noun, label=prob.noun, owner=hero.id))
    state = StoryState(world, hero, obj, prob, sol)

    world.say(f"On a bright day, {hero.id} found an {obj.label} by the step.")
    state.set_problem()
    world.para()
    speak_intro(world, hero, obj, prob)
    state.quest()
    speak_quest(world, hero, obj, prob)
    world.para()
    speak_solution(world, hero, obj, sol)
    state.solve()
    speak_lesson(world, hero, obj, params.lesson)

    world.facts.update(
        hero=hero,
        problem=prob,
        solution=sol,
        place=params.place,
        lesson=params.lesson,
        resolved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    return [
        f'Write a rhyming story for young children that includes the words "oval" and "step".',
        f"Tell a tiny quest story where {hero.id} tries to solve a problem with an {prob.noun}.",
        f"Write a gentle lesson-learned story with a small problem, a clever fix, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prob: Problem = f["problem"]
    sol: Solution = f["solution"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} find by the step?",
            answer=f"{hero.id} found an {prob.noun} by the step.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The {prob.noun} {prob.consequence}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} chose to {sol.method}, and that made the {prob.noun} safe.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at {place}?",
            answer=f"{hero.id} learned that {world.facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does oval mean?",
            answer="Oval means shaped like an egg or a stretched circle.",
        ),
        QAItem(
            question="What is a step?",
            answer="A step is a flat place you put your foot on when you go up or down.",
        ),
        QAItem(
            question="Why do people make little nests or boxes for small things?",
            answer="People make little nests or boxes so small things can stay in one safe place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, prob_id, sol_id in valid_stories():
            params = StoryParams(
                place=place,
                problem=prob_id,
                solution=sol_id,
                name="Mina",
                gender="girl",
                lesson=LESSONS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
