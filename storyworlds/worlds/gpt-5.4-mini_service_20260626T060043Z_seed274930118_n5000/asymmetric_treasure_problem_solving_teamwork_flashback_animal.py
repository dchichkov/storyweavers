#!/usr/bin/env python3
"""
A small animal-story world about an asymmetric treasure problem that only a
team can solve, with a brief flashback that explains why the treasure matters.
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
class Species:
    id: str
    kind: str
    name: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    small: bool = False


@dataclass
class Treasure:
    id: str
    name: str
    place: str
    weight: int
    asymmetric: bool = False
    split_into: str = ""


@dataclass
class Problem:
    id: str
    description: str
    obstacle: str
    clue: str
    solution: str


@dataclass
class Setting:
    id: str
    place: str
    adjective: str


@dataclass
class World:
    setting: Setting
    team: list[Species] = field(default_factory=list)
    treasure: Optional[Treasure] = None
    problem: Optional[Problem] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "meadow": Setting("meadow", "the sunny meadow", "sunny"),
    "riverbank": Setting("riverbank", "the riverbank", "muddy"),
    "woods": Setting("woods", "the quiet woods", "shady"),
    "hill": Setting("hill", "the soft hill", "windy"),
}

SPECIES = {
    "rabbit": Species("rabbit", "rabbit", "Milo", "he", "him", "his", small=True),
    "fox": Species("fox", "fox", "Fern", "she", "her", "her"),
    "badger": Species("badger", "badger", "Bram", "he", "him", "his"),
    "mouse": Species("mouse", "mouse", "Pip", "they", "them", "their", small=True),
    "otter": Species("otter", "otter", "Ollie", "he", "him", "his"),
    "bird": Species("bird", "bird", "Tula", "she", "her", "her", small=True),
}

TREASURES = {
    "shell": Treasure("shell", "a striped shell", "riverbank", 1, asymmetric=True, split_into="two bright halves"),
    "seedpod": Treasure("seedpod", "a golden seedpod", "woods", 1, asymmetric=False),
    "crown": Treasure("crown", "a tiny leaf crown", "meadow", 1, asymmetric=False),
    "stone": Treasure("stone", "a smooth blue stone", "hill", 3, asymmetric=True, split_into="a small chip and a larger piece"),
}

PROBLEMS = {
    "bridge": Problem(
        "bridge",
        "the path had a crooked bridge with one plank missing",
        "one side was too high for the smallest animal to cross alone",
        "a vine could make a handhold",
        "the team could tie the vine and make a safe crossing",
    ),
    "jar": Problem(
        "jar",
        "the treasure was stuck inside a lidded jar under roots",
        "the lid would not turn without one animal holding the jar steady",
        "one friend could brace the jar while another twisted",
        "they could use teamwork to hold and turn at the same time",
    ),
    "split": Problem(
        "split",
        "the treasure was asymmetric and needed careful balance",
        "the heavy side kept tipping the little cart",
        "two ropes could spread the weight evenly",
        "the team could balance it together",
    ),
}

CURATED = [
    ("meadow", "split", "crown", ("rabbit", "fox")),
    ("riverbank", "bridge", "shell", ("otter", "mouse")),
    ("woods", "jar", "seedpod", ("badger", "bird")),
    ("hill", "split", "stone", ("fox", "rabbit")),
]


@dataclass
class StoryParams:
    setting: str
    problem: str
    treasure: str
    team: tuple[str, str]
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: asymmetric treasure, problem solving, teamwork, flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--team-a", choices=SPECIES)
    ap.add_argument("--team-b", choices=SPECIES)
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
    if args.team_a and args.team_b and args.team_a == args.team_b:
        raise StoryError("The team needs two different animals.")
    settings = list(SETTINGS)
    problems = list(PROBLEMS)
    treasures = list(TREASURES)
    if args.setting and args.problem and args.treasure:
        if args.problem == "split" and not TREASURES[args.treasure].asymmetric:
            raise StoryError("The split problem needs an asymmetric treasure.")
    pick_setting = args.setting or rng.choice(settings)
    pick_problem = args.problem or rng.choice(problems)
    if pick_problem == "split":
        pick_treasure = args.treasure or rng.choice([t for t in treasures if TREASURES[t].asymmetric])
    else:
        pick_treasure = args.treasure or rng.choice(treasures)
    team_ids = [args.team_a, args.team_b]
    if not all(team_ids):
        team_ids = rng.sample(list(SPECIES), 2)
    if len(set(team_ids)) != 2:
        raise StoryError("The team needs two different animals.")
    return StoryParams(setting=pick_setting, problem=pick_problem, treasure=pick_treasure, team=(team_ids[0], team_ids[1]))


def story_line(world: World, text: str) -> None:
    world.say(text)


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    treasure = TREASURES[params.treasure]
    a = SPECIES[params.team[0]]
    b = SPECIES[params.team[1]]
    world = World(setting=setting, team=[a, b], treasure=treasure, problem=problem)
    world.facts.update(setting=setting, problem=problem, treasure=treasure, team=(a, b))

    story_line(world, f"In {setting.place}, {a.name} and {b.name} were small animals with a big idea.")
    story_line(world, f"They wanted to find {treasure.name} and bring it home.")
    story_line(world, f"The treasure felt special because it was a little asymmetric, which made it hard to carry alone.")
    world.para()

    flashback = (
        f"Before this day, {a.name} had once watched a friend drop a lopsided fruit basket, "
        f"and the memory came back like a quick flashback. "
        f"So {a.pronoun_subject} told {b.name} that a careful plan would matter."
    )
    story_line(world, flashback)
    story_line(world, f"Then they found the problem: {problem.description}.")
    story_line(world, f"{a.name} noticed {problem.clue}, and {b.name} saw a way to use it.")
    world.para()

    if params.problem == "split":
        story_line(world, f"The treasure kept tipping because one side was heavier than the other.")
        story_line(world, f"{a.name} held the lighter side while {b.name} tied two ropes around the heavier side.")
        story_line(world, f"Together they made the load steady, and the little cart rolled straight.")
    elif params.problem == "bridge":
        story_line(world, f"The bridge was too tricky for one small animal, but two friends could solve it.")
        story_line(world, f"{a.name} held a vine low while {b.name} climbed first and pulled the line tight.")
        story_line(world, f"With teamwork, they made a safe path across.")
    else:
        story_line(world, f"{a.name} braced the jar while {b.name} twisted the lid with tiny careful turns.")
        story_line(world, f"When that was not enough, they tried again with both paws and a steady rhythm.")
        story_line(world, f"At last the lid opened, and the treasure came free.")
    world.para()

    story_line(world, f"In the end, they carried {treasure.name} home together.")
    story_line(world, f"Their teamwork solved the problem, and the asymmetric treasure no longer felt impossible.")
    story_line(world, f"{a.name} and {b.name} smiled at the shiny prize, proud that they had helped each other.")
    return world


def generation_prompts(world: World) -> list[str]:
    t = world.facts["treasure"]
    p = world.facts["problem"]
    a, b = world.facts["team"]
    return [
        f"Write an animal story about {a.name} and {b.name} solving a problem to carry {t.name}.",
        f"Tell a short teamwork story with a flashback, where two animals help move an asymmetric treasure.",
        f"Make a child-friendly story about {p.description} and how friends work together to fix it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b = world.facts["team"]
    t = world.facts["treasure"]
    p = world.facts["problem"]
    return [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{a.name} and {b.name} worked together as a team.",
        ),
        QAItem(
            question=f"What treasure did they want to carry?",
            answer=f"They wanted to carry {t.name}.",
        ),
        QAItem(
            question="What made the treasure hard to move?",
            answer="It was asymmetric, so it did not balance well by itself.",
        ),
        QAItem(
            question="Why did the flashback matter?",
            answer="It reminded one animal to plan carefully before trying to lift the treasure.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used teamwork to handle {p.description.lower()} and get the treasure home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means two or more helpers work together to reach the same goal.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick part that shows something from before the main moment of the story.",
        ),
        QAItem(
            question="What does asymmetric mean?",
            answer="Asymmetric means one side is different from the other side, so it may not balance evenly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    a, b = world.team
    return "\n".join(
        [
            "--- world trace ---",
            f"setting: {world.setting.place}",
            f"team: {a.name}, {b.name}",
            f"treasure: {world.treasure.name}",
            f"problem: {world.problem.description}",
        ]
    )


ASP_RULES = r"""
setting(m meadow).
setting(r riverbank).
setting(w woods).
setting(h hill).

problem(split).
problem(bridge).
problem(jar).

treasure(crown, nonasym).
treasure(shell, asym).
treasure(seedpod, nonasym).
treasure(stone, asym).

team_ok(P, T) :- problem(P), treasure(T, asym).
valid(S, P, T) :- setting(S), problem(P), treasure(T), (P != split; treasure(T, asym)).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.asymmetric:
            lines.append(asp.fact("asymmetric", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for t in TREASURES:
                if p == "split" and not TREASURES[t].asymmetric:
                    continue
                out.append((s, p, t))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    import storyworlds.asp as sasp  # lazy import required by contract
    model = sasp.one_model(asp_program("#show valid/3."))
    return sorted(set(sasp.atoms(model, "valid")))


def build_story(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(setting=s, problem=p, treasure=t, team=team))
            for s, p, t, team in CURATED
        ]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
