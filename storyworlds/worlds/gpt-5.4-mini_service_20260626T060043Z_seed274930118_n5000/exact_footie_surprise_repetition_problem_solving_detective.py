#!/usr/bin/env python3
"""
A small detective-story world: repeated clues, a surprise turn, and a careful
problem-solving ending built around footie on the green.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    time: str
    supports_footie: bool = True


@dataclass
class Clue:
    label: str
    exactness: str
    repeated: bool = False
    hidden: bool = False


@dataclass
class Problem:
    id: str
    mystery: str
    surprise: str
    solution_method: str
    solved_image: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    detective_name: str
    sidekick_name: str
    seed: Optional[int] = None


SETTINGS = {
    "park": Setting(place="the park", time="late afternoon", supports_footie=True),
    "schoolyard": Setting(place="the schoolyard", time="after lunch", supports_footie=True),
    "back_lot": Setting(place="the back lot", time="just before dusk", supports_footie=True),
}

PROBLEMS = {
    "lost_ball": Problem(
        id="lost_ball",
        mystery="the exact footie ball had vanished from the goal box",
        surprise="the missing ball was not stolen at all",
        solution_method="follow the tiny scuffs, check the net, and listen for the faint thump in the grass",
        solved_image="the ball rolled out from under the bench, right where the scuffs had pointed",
    ),
    "mixed_boots": Problem(
        id="mixed_boots",
        mystery="the exact pair of footie boots kept turning up in the wrong place",
        surprise="someone had been borrowing them for a surprise practice",
        solution_method="match the muddy prints, ask the coach, and trace the locker notes carefully",
        solved_image="the boots sat beside the chalk line, waiting for the next practice",
    ),
    "repeated_whistle": Problem(
        id="repeated_whistle",
        mystery="a whistle sounded again and again from the empty pitch",
        surprise="the whistle was caught in the fence and blew in the wind",
        solution_method="walk the fence line, test the breeze, and look for the snag",
        solved_image="the whistle came free with a little pop, and the field went quiet",
    ),
}

DETECTIVE_NAMES = ["Mina", "Theo", "Jun", "Ivy", "Pip", "Ada", "Noah", "Rose"]
SIDEKICK_NAMES = ["Max", "Lena", "Bo", "Milo", "Nia", "Sami", "Jules", "Tess"]


class World:
    def __init__(self, setting: Setting, problem: Problem) -> None:
        self.setting = setting
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting, self.problem)
        clone.entities = {k: Entity(e.id, e.kind, e.label, dict(e.meters), dict(e.memes)) for k, e in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def explain_scene(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was busy and bright, with a patch of grass that looked ready for footie."


def introduce(world: World, detective: Entity, sidekick: Entity) -> None:
    world.say(
        f"{detective.label} was a little detective who loved exact clues and careful thinking."
    )
    world.say(
        f"{sidekick.label} stayed close because {detective.label} liked solving puzzles out loud."
    )


def case_setup(world: World) -> None:
    world.say(
        f"One {world.setting.time}, the two friends went to {world.setting.place} for a game of footie."
    )
    world.say(explain_scene(world.setting))
    world.say(
        f"But then a surprise stopped the game: {world.problem.mystery}."
    )


def repeat_clue(world: World) -> None:
    world.say(
        "At first, the same clue kept showing up again and again."
    )
    world.say(
        "A tiny muddy mark, then another tiny muddy mark, and then the same shape near the sideline."
    )
    world.facts["repetition"] = True


def investigate(world: World) -> None:
    world.say(
        f"{world.facts['detective_name']} knelt down and checked each mark exactly."
    )
    world.say(
        f"That careful look turned the surprise into a problem they could solve."
    )
    world.say(
        f"They decided to {world.problem.solution_method}."
    )
    world.facts["problem_solving"] = True


def solve_case(world: World) -> None:
    world.say(
        f"In the end, {world.problem.solved_image}."
    )
    world.say(
        "The repeated clues finally made sense, and the little detective smiled."
    )
    world.say(
        f"The footie game could begin at last, and the field felt calm again."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, problem: Problem, detective_name: str, sidekick_name: str) -> World:
    world = World(setting, problem)
    detective = world.add(Entity(id="detective", kind="character", label=detective_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", label=sidekick_name))

    world.facts["detective_name"] = detective_name
    world.facts["sidekick_name"] = sidekick_name

    introduce(world, detective, sidekick)
    world.para()
    case_setup(world)
    world.para()
    repeat_clue(world)
    investigate(world)
    world.para()
    solve_case(world)
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.supports_footie:
            lines.append(asp.fact("supports_footie", sid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mystery", pid, problem.mystery))
        lines.append(asp.fact("surprise", pid, problem.surprise))
        lines.append(asp.fact("solution", pid, problem.solution_method))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,P) :- setting(S), problem(P), supports_footie(S).
#show valid_story/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(sid, pid) for sid in SETTINGS for pid in PROBLEMS if SETTINGS[sid].supports_footie}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with exact footie clues, surprise, repetition, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    problem = args.problem or rng.choice(list(PROBLEMS))
    return StoryParams(
        setting=setting,
        problem=problem,
        detective_name=args.name or rng.choice(DETECTIVE_NAMES),
        sidekick_name=args.sidekick or rng.choice(SIDEKICK_NAMES),
        seed=args.seed,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short detective story for a young child that includes exact footie clues and a surprise.',
        f"Tell a simple mystery at {world.setting.place} where {world.facts['detective_name']} uses repetition to solve a footie problem.",
        "Make the ending cheerful, with problem solving that explains the repeated clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What kind of story is this one?",
            answer="It is a detective story about a little mystery, a repeated clue, and a clever solution.",
        ),
        QAItem(
            question=f"What kept happening before the problem was solved?",
            answer="The same clue kept showing up again and again, which helped the detective notice a pattern.",
        ),
        QAItem(
            question=f"What was the surprise in the mystery?",
            answer=world.problem.surprise.capitalize() + ".",
        ),
        QAItem(
            question=f"How did the detective solve the footie problem?",
            answer=f"They used {world.problem.solution_method} and followed the exact clues carefully.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer="The mystery made sense, the repeated clues were explained, and the footie game could begin again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens again and again.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking step by step to find a way to fix a problem.",
        ),
        QAItem(
            question="What is footie?",
            answer="Footie is a game played with a ball, where players try to move and kick it carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting.place}")
    lines.append(f"problem={world.problem.id}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], params.detective_name, params.sidekick_name)
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
    StoryParams(setting="park", problem="lost_ball", detective_name="Mina", sidekick_name="Max"),
    StoryParams(setting="schoolyard", problem="mixed_boots", detective_name="Theo", sidekick_name="Lena"),
    StoryParams(setting="back_lot", problem="repeated_whistle", detective_name="Ivy", sidekick_name="Bo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid_story'))} valid story combos")
        for sid, pid in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {sid} / {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
