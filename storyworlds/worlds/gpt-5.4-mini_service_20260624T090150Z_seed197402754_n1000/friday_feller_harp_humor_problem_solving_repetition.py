#!/usr/bin/env python3
"""
A heartwarming storyworld about a Friday feller, a harp, a small problem, and
the gentle repair that turns worry into music.

Seed tale:
---
On Friday, a little feller named Rory found an old harp in the attic. He wanted
to play a happy tune, but one string was too loose and made a funny twang. Rory
laughed, tried again, and again, and again. Each try helped him notice a better
way to tighten the string. At last the harp sang a bright song, and Rory played
for his family while they smiled.

World idea:
- The story is driven by a small physical problem: one harp string is loose.
- The hero uses problem solving and repetition to fix it.
- Humor appears as a funny twang and a silly first attempt.
- The emotional arc moves from curiosity to frustration to relief and pride.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man", "feller"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_twang(world: World) -> list[str]:
    out: list[str] = []
    harp = world.entities["harp"]
    hero = world.entities["hero"]
    if harp.meters.get("loose_string", 0.0) >= THRESHOLD and ("twang", "loose") not in world.fired:
        world.fired.add(("twang", "loose"))
        harp.memes["funny"] = harp.memes.get("funny", 0.0) + 1
        hero.memes["amused"] = hero.memes.get("amused", 0.0) + 1
        out.append("The harp gave a funny twang.")
    return out


def _r_frustration(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    harp = world.entities["harp"]
    if harp.meters.get("loose_string", 0.0) >= THRESHOLD and hero.memes.get("tries", 0.0) >= 1 and ("frustrated",) not in world.fired:
        world.fired.add(("frustrated",))
        hero.memes["frustrated"] = hero.memes.get("frustrated", 0.0) + 1
        out.append("That made the feller pause and scratch his head.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    harp = world.entities["harp"]
    hero = world.entities["hero"]
    if harp.meters.get("tightened", 0.0) >= THRESHOLD and harp.meters.get("loose_string", 0.0) < THRESHOLD and ("fix",) not in world.fired:
        world.fired.add(("fix",))
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        out.append("The harp rang clear at last.")
    return out


CAUSAL_RULES = [Rule("twang", _r_twang), Rule("frustration", _r_frustration), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Setting:
    place: str = "the attic"
    day: str = "Friday"


SETTING = Setting()


def introduce(world: World, hero: Entity) -> None:
    world.say(f"On Friday, a little {hero.type} named {hero.id} found an old harp in the attic.")


def problem(world: World, hero: Entity, harp: Entity) -> None:
    world.say("He wanted to play a happy tune, but one string was loose and made a funny twang.")
    world.facts["problem"] = "loose string"
    harp.meters["loose_string"] = 1.0
    hero.memes["curious"] = 1.0
    propagate(world)


def attempts(world: World, hero: Entity, harp: Entity) -> None:
    world.para()
    world.say("The feller laughed, then tried again.")
    hero.memes["tries"] = hero.memes.get("tries", 0.0) + 1
    world.say("He gently twisted the peg, listened, and tried once more.")
    hero.memes["tries"] += 1
    world.say("He did it again and again, because each careful try taught him a little more.")
    hero.memes["tries"] += 1
    harp.meters["tightened"] = 1.0
    harp.meters["loose_string"] = 0.0
    propagate(world)


def resolution(world: World, hero: Entity, harp: Entity) -> None:
    world.para()
    world.say("At last the harp sang bright and clear.")
    world.say(f"{hero.id} smiled, played a sweet song, and the family came close to listen.")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.facts["resolved"] = True


def tell(name: str = "Rory", gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    harp = world.add(Entity(id="harp", kind="thing", type="harp", label="harp"))
    hero.id = name
    world.entities.pop("hero")
    world.entities[name] = hero
    world.facts.update(hero=hero, harp=harp, setting=SETTING)

    introduce(world, hero)
    world.para()
    problem(world, hero, harp)
    attempts(world, hero, harp)
    resolution(world, hero, harp)
    return world


WORLD_NAMES = ["boy", "girl"]
NAMES = {
    "boy": ["Rory", "Theo", "Finn", "Ned", "Milo"],
    "girl": ["Mira", "June", "Lena", "Mabel", "Tess"],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        "Write a warm story about a Friday feller and a harp, with a small problem and a happy fix.",
        f"Tell a heartwarming tale where {hero.label} finds a harp, laughs at a funny sound, and solves the problem by trying again.",
        "Write a child-friendly story that uses repetition, problem solving, and a gentle joke while a harp gets tuned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    harp: Entity = world.facts["harp"]
    return [
        QAItem(
            question="What did the feller find on Friday?",
            answer=f"He found an old harp in the attic.",
        ),
        QAItem(
            question="What was wrong with the harp?",
            answer="One string was loose, so the harp made a funny twang instead of a clear note.",
        ),
        QAItem(
            question="How did he fix the problem?",
            answer="He tried again and again, listened closely, and gently tightened the string until the harp sounded bright and clear.",
        ),
        QAItem(
            question="How did he feel at the end?",
            answer=f"He felt happy and proud when {hero.label} played a sweet song and the family came to listen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harp?",
            answer="A harp is a musical instrument with strings that you pluck to make music.",
        ),
        QAItem(
            question="Why can trying again help solve a problem?",
            answer="Trying again lets you notice what is not working and make a better choice the next time.",
        ),
        QAItem(
            question="Why do people sometimes laugh at a funny mistake?",
            answer="Sometimes a mistake is harmless and silly, so laughing can help people stay calm and keep going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The feller can have a harp problem when a string is loose.
problem(harp) :- loose_string(harp).

% Repetition helps when the feller tries more than once.
repetition(hero) :- tries(hero,N), N >= 2.

% Humor appears when the harp makes a funny twang.
humor(harp) :- funny_twang(harp).

% Problem solving is present when the problem is fixed.
solved(harp) :- problem(harp), fixed(harp).

good_story(hero, harp) :- humor(harp), repetition(hero), solved(harp).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("feller", "hero"),
        asp.fact("instrument", "harp"),
        asp.fact("day", "friday"),
        asp.fact("theme", "humor"),
        asp.fact("theme", "problem_solving"),
        asp.fact("theme", "repetition"),
        asp.fact("loose_string", "harp"),
        asp.fact("funny_twang", "harp"),
        asp.fact("fixed", "harp"),
        asp.fact("tries", "hero", 3),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_story() -> bool:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return bool(asp.atoms(model, "good_story"))


def asp_verify() -> int:
    if asp_good_story():
        print("OK: ASP twin recognizes the heartwarming harp story.")
        return 0
    print("MISMATCH: ASP twin failed to recognize the story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming Friday feller harp storyworld.")
    ap.add_argument("--name", choices=sum([NAMES[k] for k in NAMES], []))
    ap.add_argument("--gender", choices=WORLD_NAMES)
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
    gender = args.gender or rng.choice(WORLD_NAMES)
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender)
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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: humor + repetition + problem solving")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for gender in WORLD_NAMES:
            for name in NAMES[gender]:
                samples.append(generate(StoryParams(name=name, gender=gender)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
