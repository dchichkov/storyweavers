#!/usr/bin/env python3
"""
Standalone storyworld: Sillybilly at the mill.

A small adventure domain built from the seed words:
- sillybilly
- mill
- suppose

Narrative instruments:
- Foreshadowing
- Repetition
- Happy Ending

The story model is state-driven: the hero travels, notices clues, faces a
problem at the mill, uses the repeated clue to solve it, and ends with a happy
image that proves the world changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    clue: str
    problem: str
    fix: str
    risk: str


@dataclass
class StoryParams:
    place: str
    goal: str
    name: str = "Sillybilly"
    seed: Optional[int] = None


PLACES = {
    "mill": Place(id="mill", label="the old mill", features={"waterwheel", "loft", "sacks"}),
    "riverbank": Place(id="riverbank", label="the riverbank", features={"path", "stones", "rushes"}),
    "barn": Place(id="barn", label="the red barn", features={"loft", "hay", "rope"}),
}

GOALS = {
    "repair": Goal(
        id="repair",
        label="fix the mill wheel",
        clue="the wheel groaned twice in the wind",
        problem="the wheel jammed under a tangled reed",
        fix="use a long hook to pull the reed free",
        risk="the mill would stop grinding grain",
    ),
    "findkey": Goal(
        id="findkey",
        label="find the lost key",
        clue="a bright key-shaped gleam flashed under the stairs",
        problem="the key had slipped behind a sack of flour",
        fix="move the sack and lift the key out carefully",
        risk="the door would stay locked",
    ),
    "savebird": Goal(
        id="savebird",
        label="help the trapped bird",
        clue="a tiny chirp came from the loft again and again",
        problem="a small bird was caught behind loose twine",
        fix="cut the twine and guide the bird to the open air",
        risk="the bird would stay scared and stuck",
    ),
}

NARRATIVE_TAGS = ["Foreshadowing", "Repetition", "Happy Ending", "Adventure"]


@dataclass
class World:
    place: Place
    goal: Goal
    hero: Entity
    helper: Entity
    clue_seen: int = 0
    problem_seen: bool = False
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: sillybilly, mill, suppose.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--goal", choices=GOALS.keys())
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


def _reasonableness_gate(place: Place, goal: Goal) -> bool:
    if place.id == "mill" and goal.id in GOALS:
        return True
    return False


def explain_rejection(place: str, goal: str) -> str:
    return f"(No story: the goal {goal!r} does not fit the adventure at {place!r}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or "mill"
    goal_id = args.goal or rng.choice(list(GOALS.keys()))
    if not _reasonableness_gate(PLACES[place_id], GOALS[goal_id]):
        raise StoryError(explain_rejection(place_id, goal_id))
    name = args.name or "Sillybilly"
    return StoryParams(place=place_id, goal=goal_id, name=name)


def _hero_name(params: StoryParams) -> str:
    return params.name if params.name else "Sillybilly"


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    hero = Entity(id=_hero_name(params), kind="character", label="hero", type="child")
    helper = Entity(id="Mara", kind="character", label="helper", type="friend")
    world = World(place=place, goal=goal, hero=hero, helper=helper)

    # Act 1: setup and foreshadowing
    world.say(f"{hero.id} set out for {place.label} with a light step and a brave grin.")
    world.say(
        f"Before long, {hero.id} noticed {goal.clue}. {hero.id} smiled and said, "
        f'"I suppose that means something important is waiting for me."'
    )
    world.say(
        f"The same small clue came back again as {hero.id} crossed the yard: "
        f"{goal.clue}."
    )

    # Act 2: problem appears, repeated clue matters
    world.para()
    world.say(
        f"Inside {place.label}, the work began, but then {goal.problem}."
    )
    world.problem_seen = True
    world.clue_seen += 2
    world.say(
        f"{hero.id} remembered the clue. {hero.id} remembered it well: "
        f"{goal.clue}."
    )
    world.say(
        f"'If that clue was true,' {hero.id} said, 'then I can still {goal.fix}.'"
    )

    # Act 3: fix and happy ending
    world.para()
    world.say(f"{helper.id} rushed over to help, and together they did just that.")
    world.say(f"They worked carefully until the {goal.id} problem was gone.")
    world.solved = True
    world.say(
        f"In the end, {hero.id} had done it: {goal.risk} was no longer a worry, "
        f"and {place.label} felt bright and safe again."
    )
    world.say(
        f"{hero.id} laughed, {helper.id} waved, and the mill hummed along like a happy song."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        goal=goal,
        clue_seen=world.clue_seen,
        problem_seen=world.problem_seen,
        solved=world.solved,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short Adventure story for children featuring {world.hero.id}, {world.place.label}, and the word 'suppose'.",
        f"Tell a story with foreshadowing and repetition where {world.hero.id} visits {world.place.label} and solves a problem.",
        f"Write a gentle mill adventure that ends happily after a repeated clue helps the hero succeed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    g = world.goal
    p = world.place.label
    h = world.hero.id
    return [
        QAItem(
            question=f"Where did {h} go in the story?",
            answer=f"{h} went to {p} for a small adventure.",
        ),
        QAItem(
            question=f"What repeated clue did {h} notice?",
            answer=f"{h} noticed this clue more than once: {g.clue}",
        ),
        QAItem(
            question=f"What problem had to be solved at {p}?",
            answer=f"The problem was that {g.problem}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily because {h} solved the problem and the mill was safe again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mill?",
            answer="A mill is a place where people or machines grind grain, often by using moving water or wind.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early on that hints at something important later.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a story repeats a word, sound, or clue to help it stand out and feel memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.id} label={world.place.label} features={sorted(world.place.features)}")
    lines.append(f"goal={world.goal.id} clue_seen={world.clue_seen} problem_seen={world.problem_seen} solved={world.solved}")
    lines.append(f"hero={world.hero.id}")
    lines.append(f"helper={world.helper.id}")
    return "\n".join(lines)


ASP_RULES = r"""
place(mill).
goal(repair;findkey;savebird).

compatible(P,G) :- place(P), goal(G), P = mill.

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "mill")]
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {("mill", gid) for gid in GOALS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="mill", goal="repair", name="Sillybilly"),
    StoryParams(place="mill", goal="findkey", name="Sillybilly"),
    StoryParams(place="mill", goal="savebird", name="Sillybilly"),
]


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:")
        for p, g in combos:
            print(f"  {p} {g}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
            header = f"### {p.name}: {p.goal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
