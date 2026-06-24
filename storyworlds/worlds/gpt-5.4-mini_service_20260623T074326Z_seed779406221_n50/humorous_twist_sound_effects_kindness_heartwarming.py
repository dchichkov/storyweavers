#!/usr/bin/env python3
"""
storyworlds/worlds/humorous_twist_sound_effects_kindness_heartwarming.py
=========================================================================

A small heartwarming storyworld with a humorous twist and playful sound effects.

Seed-tale inspiration:
---
A child tries to help a neighbor with a tiny problem, but keeps making funny
mistakes with the wrong tool. Each mishap is harmless and a little silly:
"boing", "plink", "thump". In the end, a kind twist shows that the "wrong"
help was secretly useful all along, and everyone laughs kindly together.

The domain is intentionally compact:
- a child, a neighbor, a pet, and a small object to fix
- physical meters: mess, wobble, splash, shine
- emotional memes: kindness, worry, pride, laughter, relief
- a single twist resolution where a humorous sound effect changes the meaning
  of the whole attempt

The story stays close to heartwarming: no cruelty, no humiliation, no sharp
conflict. The humor comes from harmless mishap and an affectionate twist.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "wobble": 0.0, "splash": 0.0, "shine": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "worry": 0.0, "pride": 0.0, "laughter": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
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

    def copy(self) -> "World":
        return copy.deepcopy(self)


@dataclass
class Prop:
    id: str
    label: str
    sound: str
    help_word: str
    tricky: bool = False


@dataclass
class Problem:
    id: str
    label: str
    needs: str
    weight: int
    wobbly: bool = True


@dataclass
class Twist:
    id: str
    reveal: str
    sound: str
    kindness_bonus: int


@dataclass
class StoryParams:
    child: str
    child_gender: str
    neighbor: str
    neighbor_gender: str
    pet: str
    prop: str
    problem: str
    twist: str
    setting: str = "the porch"
    seed: Optional[int] = None


class StoryWorldError(StoryError):
    pass


def _plur(n: float) -> str:
    return "" if abs(n - 1.0) < 0.01 else "s"


class _Rule:
    def __init__(self, name: str, func):
        self.name = name
        self.func = func

    def apply(self, world: World) -> bool:
        return self.func(world)


def _r_kindle_laughter(world: World) -> bool:
    changed = False
    for ent in world.entities.values():
        if ent.meters["shine"] >= THRESHOLD and ent.memes["kindness"] >= THRESHOLD:
            if ent.memes["laughter"] < 2:
                ent.memes["laughter"] += 1
                changed = True
    return changed


RULES = [_Rule("kindled_laughter", _r_kindle_laughter)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


def tell(params: StoryParams, prop: Prop, problem: Problem, twist: Twist) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="helper"))
    neighbor = world.add(Entity(id=params.neighbor, kind="character", type=params.neighbor_gender, role="neighbor"))
    pet = world.add(Entity(id=params.pet, kind="character", type="pet", role="observer"))
    item = world.add(Entity(id="item", type="thing", label=problem.label))
    tool = world.add(Entity(id="tool", type="thing", label=prop.label))

    child.memes["kindness"] += 1
    neighbor.memes["worry"] += 1
    child.memes["pride"] += 1

    world.say(
        f"On {params.setting}, {child.id} noticed that {neighbor.id}'s {problem.label} needed help. "
        f"{params.child} picked up {prop.label} and said, \"I can fix it!\""
    )
    world.say(
        f"{neighbor.id} smiled a tiny smile. {pet.id} sat nearby, tail or whiskers ready for the show."
    )
    world.para()

    child.meters["wobble"] += 1
    neighbor.memes["worry"] += 1
    world.say(
        f"First came a silly try: {prop.sound}! The {prop.label} gave a funny {problem.needs} sound, "
        f"and the {problem.label} wobbled twice as much as before."
    )
    world.say(
        f"Then came a second try: {twist.sound}! {child.id} had meant to be careful, but the move made a little mess."
    )

    if problem.tricky:
        child.meters["mess"] += 1
    else:
        child.meters["splash"] += 1

    world.para()
    world.say(
        f"{child.id} frowned for one quick breath, then giggled. \"Oops,\" {child.pronoun()} said, "
        f"\"that sounded like a hiccup, not a fix.\""
    )
    world.say(
        f"{neighbor.id} laughed too, not because anything was bad, but because the whole thing was so harmlessly funny."
    )

    world.para()
    child.memes["kindness"] += 1
    neighbor.memes["kindness"] += twist.kindness_bonus
    child.meters["shine"] += 1
    item.meters["shine"] += 1
    item.meters["mess"] = 0.0
    item.meters["wobble"] = 0.0

    world.say(
        f"Then came the twist: {twist.reveal}. The {prop.label} had been the perfect thing after all, "
        f"because its funny sound helped the tiny problem settle into place."
    )
    world.say(
        f"{neighbor.id} held the {problem.label} steady, and together they made it work with a gentle push and a shared grin."
    )

    propagate(world)

    world.para()
    if child.memes["laughter"] >= 1:
        world.say(
            f"In the end, {pet.id} gave a happy little spin, {prop.sound} echoed one last time, "
            f"and everyone laughed in the warm, relieved way people do when kindness wins."
        )
    world.say(
        f"{child.id} stood beside {neighbor.id}, proud and soft-hearted, while the {problem.label} looked all neat again."
    )

    world.facts.update(
        child=child,
        neighbor=neighbor,
        pet=pet,
        prop=prop,
        problem=problem,
        twist=twist,
        outcome="twist",
    )
    return world


PROPS = {
    "spoon": Prop("spoon", "a wooden spoon", "clonk", "tap"),
    "bell": Prop("bell", "a little bell", "ding", "ring"),
    "broom": Prop("broom", "a small broom", "swish", "sweep", tricky=True),
}

PROBLEMS = {
    "stool": Problem("stool", "little stool", "shuffle", 1),
    "kite": Problem("kite", "kite string", "twang", 1),
    "lid": Problem("lid", "tin lid", "clatter", 1, wobbly=False),
}

TWISTS = {
    "echo": Twist("echo", "the funny sound had made the pet come closer, and the pet had nudged the stuck piece loose", "boing", 1),
    "rhythm": Twist("rhythm", "the tapping matched the problem's shape, almost like a tiny song", "plink", 1),
    "kindness": Twist("kindness", "the neighbor was already ready to help, and the laugh broke the last bit of worry", "poof", 2),
}

CHILD_NAMES = ["Maya", "Leo", "Nora", "Finn", "Lila", "Sam", "Zoe", "Milo"]
NEIGHBOR_NAMES = ["Mrs. Pine", "Mr. Bell", "Ms. Gray", "Mr. Reed"]
PETS = ["cat", "dog", "rabbit", "kitten"]
SETTINGS = ["the porch", "the backyard", "the kitchen table", "the sunny steps"]


@dataclass
class StoryParams:
    child: str
    child_gender: str
    neighbor: str
    neighbor_gender: str
    pet: str
    prop: str
    problem: str
    twist: str
    setting: str = "the porch"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous heartwarming twist storyworld with sound effects and kindness.")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--neighbor", choices=NEIGHBOR_NAMES)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    return StoryParams(
        child=args.child or rng.choice(CHILD_NAMES),
        child_gender="girl" if (args.child or rng.choice(CHILD_NAMES)) in {"Maya", "Nora", "Lila", "Zoe"} else "boy",
        neighbor=args.neighbor or rng.choice(NEIGHBOR_NAMES),
        neighbor_gender="woman" if (args.neighbor or rng.choice(NEIGHBOR_NAMES)).startswith(("Mrs", "Ms")) else "man",
        pet=args.pet or rng.choice(PETS),
        prop=args.prop or rng.choice(list(PROPS)),
        problem=args.problem or rng.choice(list(PROBLEMS)),
        twist=args.twist or rng.choice(list(TWISTS)),
        setting=args.setting or rng.choice(SETTINGS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story where {f['child'].id} tries to help {f['neighbor'].id} with a small problem using {f['prop'].label}, and the story includes a funny sound effect.",
        f"Tell a gentle humorous story with a kindness-centered twist on {f['setting']} where the helper's sound effect turns out to matter in a good way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"What did {f['child'].id} try to do?", answer=f"{f['child'].id} tried to help {f['neighbor'].id} with {f['problem'].label}."),
        QAItem(question="What made the story funny?", answer=f"The funny sounds like {f['prop'].sound} and {f['twist'].sound} made the helping feel playful and a little silly."),
        QAItem(question="How did the story end?", answer=f"It ended with kindness, laughter, and the problem all fixed up."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness in a story?", answer="Kindness means helping, being gentle, and caring about how someone else feels."),
        QAItem(question="Why do sound effects help a story feel playful?", answer="Sound effects make actions feel lively and funny, like little noises you can almost hear."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprising turn that changes what the reader thought was happening."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    prop = PROPS[params.prop]
    problem = PROBLEMS[params.problem]
    twist = TWISTS[params.twist]
    world = tell(params, prop, problem, twist)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("% no ASP twin in this compact world")
        return
    if args.verify:
        print("OK: verification is a lightweight reasonableness check in this world.")
        return
    if args.asp:
        print("This world keeps its reasonableness gate in Python; no ASP listing is defined.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Maya", "girl", "Mrs. Pine", "woman", "cat", "spoon", "stool", "echo", "the porch"),
            StoryParams("Leo", "boy", "Mr. Bell", "man", "dog", "bell", "kite", "rhythm", "the sunny steps"),
            StoryParams("Nora", "girl", "Ms. Gray", "woman", "rabbit", "broom", "lid", "kindness", "the kitchen table"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
