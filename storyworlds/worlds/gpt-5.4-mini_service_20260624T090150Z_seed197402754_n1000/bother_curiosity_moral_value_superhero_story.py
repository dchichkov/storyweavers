#!/usr/bin/env python3
"""
A small Storyweavers world: a curious kid learns a moral superhero lesson
when a tiny bother turns into a chance to help.

Premise:
- A child hero wants to explore something interesting.
- A small bother blocks the easy path.
- Curiosity leads to a choice.
- Moral value determines whether the hero uses the chance to help or to
  ignore someone else.

This world is intentionally small and self-contained.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% The moral turn is only reasonable when curiosity creates a real bother.
bothering(X) :- curious(X), sees_problem(X).

% A hero acts with moral value when they help someone instead of simply chasing
% the interesting thing.
moral_choice(X) :- hero(X), bothering(X), helps(X).

% The story is valid when the curious hero has a bother, helps, and learns.
valid_story(Name, Bother, Lesson) :- hero_name(Name), bother_kind(Bother), lesson_kind(Lesson),
                                    curious(hero), moral(hero), solved(hero).
"""


@dataclass
class StoryParams:
    name: str
    sidekick: str
    bother: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    chunks.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            chunks.append(" ".join(current))
        return "\n\n".join(chunks)


NAMES = ["Nova", "Sky", "Ruby", "Milo", "Zane", "Ivy", "Piper", "Jett"]
SIDEKICKS = ["pigeon", "robot pup", "kitten", "little drone", "mouse helper"]
BOTHERS = {
    "stuck-door": "a stuck door",
    "lost-cap": "a lost cape",
    "trapped-ball": "a trapped ball",
    "broken-sign": "a broken park sign",
}
LESSONS = {
    "kindness": "kindness matters more than showing off",
    "helping": "a true hero helps first",
    "care": "it feels good to care about others",
}


@dataclass
class StoryWorldState:
    hero: Entity
    sidekick: Entity
    bother_name: str
    bother_label: str
    lesson_key: str
    curiosity: float = 0.0
    moral_value: float = 0.0
    tension: float = 0.0
    solved: bool = False
    helped: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with curiosity, bother, and moral value.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--bother", choices=BOTHERS)
    ap.add_argument("--lesson", choices=LESSONS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for n in NAMES:
        lines.append(asp.fact("hero_name", n))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick_kind", s))
    for b in BOTHERS:
        lines.append(asp.fact("bother_kind", b))
    for l in LESSONS:
        lines.append(asp.fact("lesson_kind", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(n, b, l) for n in NAMES for b in BOTHERS for l in LESSONS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    bother = args.bother or rng.choice(list(BOTHERS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    return StoryParams(name=name, sidekick=sidekick, bother=bother, lesson=lesson)


def build_world(params: StoryParams) -> StoryWorldState:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="character", label=params.sidekick))
    bother_label = BOTHERS[params.bother]
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        bother_name=params.bother,
        bother_label=bother_label,
        lesson_key=params.lesson,
    )
    return StoryWorldState(
        hero=hero,
        sidekick=sidekick,
        bother_name=params.bother,
        bother_label=bother_label,
        lesson_key=params.lesson,
    )


def tell(params: StoryParams) -> StorySample:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="character", label=params.sidekick))
    bother_label = BOTHERS[params.bother]
    lesson_text = LESSONS[params.lesson]

    state = StoryWorldState(
        hero=hero,
        sidekick=sidekick,
        bother_name=params.bother,
        bother_label=bother_label,
        lesson_key=params.lesson,
    )
    world.facts.update(state=state, hero=hero, sidekick=sidekick, bother=params.bother, lesson=params.lesson)

    # Act 1: curiosity wakes up.
    hero.inc_meme("curiosity", 1)
    world.say(
        f"{params.name} wore a bright cape and loved peeking at every odd thing in the city."
    )
    world.say(
        f"One afternoon, {params.name} and the {params.sidekick} spotted {bother_label} near the park gate."
    )
    world.say(
        f"{params.name} felt a strong tug of curiosity and wanted to see what was causing the bother."
    )

    # Act 2: tension rises and the hero chooses a moral path.
    world.para()
    hero.inc_meter("tension", 1)
    hero.inc_meme("curiosity", 1)
    world.say(
        f"When {params.name} got closer, the little trouble turned out to be bigger than it looked."
    )
    world.say(
        f"A child on the other side of the gate was trying hard to fix the problem, but could not do it alone."
    )
    world.say(
        f"{params.name} could chase the mystery, or {lesson_text} by helping first."
    )

    # Moral choice.
    hero.inc_meme("moral_value", 1)
    state.helped = True
    world.say(
        f"{params.name} chose the good hero path, held the gate, and used careful hands to help."
    )

    # Act 3: resolution.
    world.para()
    hero.inc_meter("tension", -1)
    state.solved = True
    state.curiosity = hero.memes.get("curiosity", 0.0)
    state.moral_value = hero.memes.get("moral_value", 0.0)
    world.say(
        f"With the help, the bother was fixed at last, and the park gate opened with a happy creak."
    )
    world.say(
        f"The child smiled, the {params.sidekick} chirped, and {params.name} stood tall as a superhero who used curiosity for good."
    )
    world.say(
        f"That night, {params.name} remembered that {lesson_text}."
    )

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(params),
        world_qa=world_qa(params),
        world=world,
    )
    return sample


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f'Write a short superhero story for a young child that includes "{params.bother}" and shows curiosity leading to a moral choice.',
        f"Tell a gentle superhero tale where {params.name} notices {BOTHERS[params.bother]} and chooses to help.",
        f"Create a child-friendly story about a hero, a bother, and the lesson that {LESSONS[params.lesson]}.",
    ]


def story_qa(params: StoryParams) -> list[QAItem]:
    return [
        QAItem(
            question=f"What made {params.name} curious at the start of the story?",
            answer=f"{params.name} became curious when they noticed {BOTHERS[params.bother]} near the park gate.",
        ),
        QAItem(
            question=f"What did {params.name} choose to do when the trouble got bigger?",
            answer=f"{params.name} chose to help first instead of chasing the mystery.",
        ),
        QAItem(
            question=f"What lesson did {params.name} remember at the end?",
            answer=f"{params.name} remembered that {LESSONS[params.lesson]}.",
        ),
    ]


def world_qa(params: StoryParams) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something interesting.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means caring about what is right and choosing to help, be fair, and do good for others.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a person in stories who uses courage and special effort to help others and solve problems.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
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
    StoryParams(name="Nova", sidekick="robot pup", bother="broken-sign", lesson="helping"),
    StoryParams(name="Ivy", sidekick="pigeon", bother="lost-cap", lesson="kindness"),
    StoryParams(name="Jett", sidekick="little drone", bother="trapped-ball", lesson="care"),
]


def asp_verify_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_verify_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} valid stories")
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [tell(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = tell(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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


def valid_story_count() -> int:
    return len(valid_combos())


if __name__ == "__main__":
    main()
