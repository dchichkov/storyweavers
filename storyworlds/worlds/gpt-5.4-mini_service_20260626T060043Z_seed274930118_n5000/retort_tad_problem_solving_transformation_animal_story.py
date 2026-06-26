#!/usr/bin/env python3
"""
A small Animal Story world about a tadpole named Tad, a problem that needs
solving, a sharp retort, and a transformation that changes the ending image.

This world keeps a compact simulated model:
- physical meters: reach, wetness, helpfulness, growth, distance
- emotional memes: worry, courage, pride, friendship, grumpiness

The central premise is simple and child-facing:
Tad wants to reach a sunny lily patch, but the path is blocked by a fallen reed
mat. The other pond animals worry. Tad gives a retort, the animals solve the
problem together, and Tad transforms by growing into a frog.
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
    can_move: bool = False
    can_speak: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"frog", "tadpole", "toad", "duck", "goose", "fish", "bear", "fox", "mouse", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pond"
    sunny: bool = True
    has_lily_patch: bool = True


@dataclass
class Problem:
    id: str
    obstacle: str
    blocked_by: str
    fix: str
    clue: str


@dataclass
class Transformation:
    id: str
    from_form: str
    to_form: str
    trigger: str
    image: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pond": Setting(place="the pond", sunny=True, has_lily_patch=True),
    "reedbed": Setting(place="the reedbed", sunny=False, has_lily_patch=False),
    "marsh": Setting(place="the marsh", sunny=True, has_lily_patch=True),
}

PROBLEMS = {
    "reedblock": Problem(
        id="reedblock",
        obstacle="a fallen mat of reeds",
        blocked_by="the narrow stepping stones",
        fix="they used a flat lily leaf as a bridge and pushed the reeds aside",
        clue="the leaf was wide enough to hold Tad's tiny feet",
    ),
    "muddybank": Problem(
        id="muddybank",
        obstacle="a steep muddy bank",
        blocked_by="the path to the water",
        fix="they packed mud with sticks and made a little ramp",
        clue="the sticks stopped the mud from sliding away",
    ),
    "snailtrail": Problem(
        id="snailtrail",
        obstacle="a slow trail of snails",
        blocked_by="the trail to the sunny patch",
        fix="they gently moved the snails onto a cool stone",
        clue="the stone kept the snails safe and out of the way",
    ),
}

TRANSFORMS = {
    "growlegs": Transformation(
        id="growlegs",
        from_form="tadpole",
        to_form="frog",
        trigger="after the hard work and a long warm day",
        image="tiny green legs wiggling out behind him",
    ),
    "brighten": Transformation(
        id="brighten",
        from_form="gray tadpole",
        to_form="golden frog",
        trigger="after he felt brave and seen by his friends",
        image="a bright green back shining in the sun",
    ),
}

ANIMALS = {
    "Tad": {"type": "tadpole", "kind": "character", "label": "Tad", "phrase": "a tiny tadpole named Tad"},
    "Moss": {"type": "frog", "kind": "character", "label": "Moss", "phrase": "a patient old frog named Moss"},
    "Pip": {"type": "duckling", "kind": "character", "label": "Pip", "phrase": "a lively duckling named Pip"},
    "Bram": {"type": "turtle", "kind": "character", "label": "Bram", "phrase": "a slow turtle named Bram"},
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    transform: str
    hero: str = "Tad"
    friend: str = "Moss"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(tad).
friend(moss).

setting(pond).
setting(reedbed).
setting(marsh).

problem(reedblock).
problem(muddybank).
problem(snailtrail).

transform(growlegs).
transform(brighten).

can_story(S,P,T) :- setting(S), problem(P), transform(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    lines.append(asp.fact("hero", "tad"))
    lines.append(asp.fact("friend", "moss"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, t) for s in SETTINGS for p in PROBLEMS for t in TRANSFORMS]


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: Tad solves a problem and changes form.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--hero", default="Tad")
    ap.add_argument("--friend", default="Moss")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.transform:
        combos = [c for c in combos if c[2] == args.transform]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    s, p, t = rng.choice(sorted(combos))
    return StoryParams(setting=s, problem=p, transform=t, hero=args.hero, friend=args.friend)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    transform = TRANSFORMS[params.transform]
    world = World(setting)

    hero_spec = ANIMALS.get(params.hero, ANIMALS["Tad"])
    friend_spec = ANIMALS.get(params.friend, ANIMALS["Moss"])

    hero = world.add(Entity(
        id=params.hero, kind=hero_spec["kind"], type=hero_spec["type"],
        label=hero_spec["label"], phrase=hero_spec["phrase"], can_move=True, can_speak=True,
        meters={"reach": 1.0, "growth": 0.2, "distance": 0.0},
        memes={"worry": 0.1, "courage": 0.2, "pride": 0.1, "friendship": 0.2},
    ))
    friend = world.add(Entity(
        id=params.friend, kind=friend_spec["kind"], type=friend_spec["type"],
        label=friend_spec["label"], phrase=friend_spec["phrase"], can_move=True, can_speak=True,
        meters={"helpfulness": 1.0},
        memes={"patience": 0.8, "friendship": 0.5},
    ))

    world.say(f"Under the warm sky at {setting.place}, {hero.phrase} wanted to reach the sunny lily patch.")
    world.say(f"But {problem.obstacle} was blocking {problem.blocked_by}, and the little path would not open.")
    world.say(f"{friend.phrase} said they should be careful, because the water was shallow but the bank was slippery.")
    world.para()

    hero.memes["worry"] += 0.6
    hero.memes["courage"] += 0.4
    world.say(f"Tad frowned, then gave a small retort: \"I may be tiny, but I can still think of a way!\"")
    world.say(f"That made Moss blink, then smile, because Tad's brave retort turned worry into action.")
    world.para()

    world.say(f"Together they looked closely. {problem.clue.capitalize()}.")
    world.say(f"So they solved the problem by working side by side: {problem.fix}.")
    hero.meters["distance"] += 1.0
    friend.meters["helpfulness"] += 0.5
    hero.memes["pride"] += 0.7
    hero.memes["friendship"] += 0.5
    world.para()

    hero.meters["growth"] += 1.0
    hero.meters["reach"] += 1.0
    world.say(f"{transform.trigger}, Tad changed at last.")
    world.say(f"He transformed from a {transform.from_form} into a {transform.to_form}, with {transform.image}.")
    world.say(f"By the end, Tad could sit on the leaf edge and grin at the pond, no longer stuck below it.")

    world.facts = {
        "params": params,
        "setting": setting,
        "problem": problem,
        "transform": transform,
        "hero": hero,
        "friend": friend,
    }

    prompts = [
        f"Write a short animal story about Tad the tadpole, a problem to solve, a retort, and a transformation.",
        f"Tell a gentle story set at {setting.place} where Tad and a friend solve a problem and Tad becomes a frog.",
        f"Write a child-friendly animal story with a small obstacle, a brave retort, teamwork, and a change in form.",
    ]

    story_qa = [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Tad, a tiny tadpole who wants to reach the sunny lily patch.",
        ),
        QAItem(
            question="What problem blocked the way?",
            answer=f"{problem.obstacle.capitalize()} blocked the path, so Tad and Moss had to solve the problem together.",
        ),
        QAItem(
            question="What did Tad say that was a retort?",
            answer='Tad said, "I may be tiny, but I can still think of a way!"',
        ),
        QAItem(
            question="How did the animals fix the trouble?",
            answer=f"They fixed it by using a careful plan: {problem.fix}.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="Tad transformed from a tadpole into a frog, and he could rest on the leaf at the sunny patch.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog that swims with a tail and later grows into a frog.",
        ),
        QAItem(
            question="What helps animals solve problems?",
            answer="Thinking carefully, asking for help, and trying more than one safe idea can help animals solve problems.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another, like a tadpole growing into a frog.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        lines.append(f"  {e.id:8} ({e.type:10}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="pond", problem="reedblock", transform="growlegs", hero="Tad", friend="Moss"),
    StoryParams(setting="marsh", problem="muddybank", transform="brighten", hero="Tad", friend="Pip"),
    StoryParams(setting="reedbed", problem="snailtrail", transform="growlegs", hero="Tad", friend="Bram"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def generation_qa_json(sample: StorySample) -> str:
    return sample.to_json()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:")
        for s, p, t in combos:
            print(f"  {s:8} {p:10} {t:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.problem} at {p.setting} (transform: {p.transform})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    lines.append(asp.fact("hero", "tad"))
    lines.append(asp.fact("friend", "moss"))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
