#!/usr/bin/env python3
"""
gastroenteritis_lesson_learned_sharing_magic_detective_story.py
===============================================================

A tiny storyworld in the style of a detective story.

Premise:
- A child detective investigates why a friend got stomach-sick with gastroenteritis.
- The trail leads to shared magic candy and a sticky spoon.
- The detective learns a careful lesson about sharing, cleanliness, and when not to
  share food.

This world is intentionally small and constraint-checked. It produces a complete
child-facing story with a beginning, a clue trail, a turn, and a lesson learned.
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
# Model
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    role: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little neighborhood"
    location: str = "the bakery lane"


@dataclass
class Clue:
    name: str
    phrase: str
    reveals: str


@dataclass
class Case:
    illness: str
    cause: str
    clue1: Clue
    clue2: Clue
    lesson: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, c: Character) -> Character:
        self.entities[c.name] = c
        return c

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
    "lane": Setting(place="the little neighborhood", location="the bakery lane"),
    "library": Setting(place="the sunny library street", location="the corner café"),
    "garden": Setting(place="the quiet garden row", location="the garden gate"),
}

CASES = {
    "candy": Case(
        illness="gastroenteritis",
        cause="shared magic candy that had been touched by unwashed hands",
        clue1=Clue(
            name="sparkles",
            phrase="a trail of glittery sugar crumbs",
            reveals="someone had shared the magic candy",
        ),
        clue2=Clue(
            name="tummy",
            phrase="a worried hand pressed to a tummy",
            reveals="the friend had tummy pain and nausea",
        ),
        lesson="not every sweet magic thing should be shared, especially not food that might be dirty",
    ),
    "juice": Case(
        illness="gastroenteritis",
        cause="shared magic juice from a cup that had been left open in the sun",
        clue1=Clue(
            name="cup",
            phrase="a warm cup with a ring of sticky juice on the rim",
            reveals="the drink had been shared carelessly",
        ),
        clue2=Clue(
            name="sink",
            phrase="a sink full of cups waiting to be washed",
            reveals="the detective noticed the kitchen had not been cleaned well",
        ),
        lesson="sharing is kind, but food and drinks should be clean and safe first",
    ),
}

HEROES = [
    ("Mira", "girl", "junior detective"),
    ("Noah", "boy", "junior detective"),
    ("Ivy", "girl", "curious detective"),
    ("Theo", "boy", "small detective"),
]

FRIENDS = [
    ("Benny", "boy"),
    ("Luna", "girl"),
    ("Sami", "boy"),
    ("Nina", "girl"),
]

ADULTS = [
    ("Mum", "mother"),
    ("Dad", "father"),
    ("Aunt June", "woman"),
    ("Uncle Ray", "man"),
]


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    hero_type: str
    hero_role: str
    friend_name: str
    friend_type: str
    adult_name: str
    adult_type: str
    seed: Optional[int] = None


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Character(
        name=params.hero_name,
        role=params.hero_role,
        type=params.hero_type,
        meters={"curiosity": 1.0, "attention": 1.0},
        memes={"bravery": 1.0, "care": 1.0},
    ))
    friend = world.add(Character(
        name=params.friend_name,
        role="friend",
        type=params.friend_type,
        meters={"sick": 1.0, "tummyache": 1.0},
        memes={"mood": -1.0},
    ))
    adult = world.add(Character(
        name=params.adult_name,
        role="adult",
        type=params.adult_type,
        meters={"worry": 1.0},
        memes={"patience": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, adult=adult, case=CASES[params.case])
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    adult: Character = f["adult"]
    case: Case = f["case"]

    world.say(
        f"{hero.name} was { _article(hero.role) } {hero.role} who loved clues, quiet steps, "
        f"and any mystery that needed a sharp eye."
    )
    world.say(
        f"One morning in {world.setting.place}, {friend.name} did not look happy at all. "
        f"{friend.pronoun().capitalize()} had a tummy ache, and {adult.name} said it was {case.illness}."
    )
    world.para()
    world.say(
        f"{hero.name} put on a small detective face and followed the signs through {world.setting.location}."
    )
    world.say(
        f"The first clue was {case.clue1.phrase}. That clue revealed that {case.clue1.reveals}."
    )
    world.say(
        f"The second clue was {case.clue2.phrase}. That clue revealed that {case.clue2.reveals}."
    )
    world.para()
    world.say(
        f"Then the pieces fit together: the trouble came from {case.cause}."
    )
    world.say(
        f"{hero.name} told {friend.name} and {adult.name} the answer: magic can be fun, "
        f"but when food or drinks are shared, they should stay clean and safe."
    )
    world.say(
        f"{adult.name} nodded, washed the cups, and made plain crackers and fresh water instead."
    )
    world.say(
        f"{friend.name} smiled a little more, and {hero.name} learned a lesson learned the careful way: "
        f"{case.lesson}."
    )

    world.facts["solved"] = True
    world.facts["lesson"] = case.lesson
    world.facts["illness"] = case.illness
    world.facts["clue1"] = case.clue1
    world.facts["clue2"] = case.clue2


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    case: Case = f["case"]
    return [
        f'Write a short detective story for a child where {hero.name} investigates why {friend.name} got {case.illness}.',
        f"Tell a gentle mystery involving magic sharing, a tummy ache, and a lesson learned.",
        f'Write a child-friendly detective tale that includes "{case.illness}" and ends with a careful sharing lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    adult: Character = f["adult"]
    case: Case = f["case"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.name} and {friend.name}?",
            answer=f"It is a detective story about {hero.name} solving a small mystery about why {friend.name} got {case.illness}.",
        ),
        QAItem(
            question=f"What was the first clue {hero.name} found?",
            answer=f"The first clue was {case.clue1.phrase}, and it showed that {case.clue1.reveals}.",
        ),
        QAItem(
            question=f"What did {hero.name} learn at the end?",
            answer=f"{hero.name} learned that {case.lesson}.",
        ),
        QAItem(
            question=f"What did {adult.name} do after the mystery was solved?",
            answer=f"{adult.name} nodded, washed the cups, and offered safe food and drink instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gastroenteritis?",
            answer="Gastroenteritis is an illness that makes the stomach and intestines hurt, so a person may feel sick, have a tummy ache, or throw up.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving someone else some of what you have or letting them use it too.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special pretend power in stories that can make unusual things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A case is valid when the illness, clue trail, and lesson are present.
case(C) :- illness(C, _), lesson(C, _).

% The detective story is reasonable when a clue trail points to a shared item
% and the illness is gastroenteritis.
detective_story(C) :- illness(C, gastroenteritis), shared_item(C), clue(C, clue1), clue(C, clue2).

% The lesson learned should be about safe sharing.
safe_lesson(C) :- lesson(C, L), contains_safe(L).

#show detective_story/1.
#show safe_lesson/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, case in CASES.items():
        lines.append(asp.fact("illness", sid, case.illness))
        lines.append(asp.fact("lesson", sid, case.lesson))
        lines.append(asp.fact("shared_item", sid))
        lines.append(asp.fact("clue", sid, "clue1"))
        lines.append(asp.fact("clue", sid, "clue2"))
        if "safe" in case.lesson or "clean" in case.lesson:
            lines.append(asp.fact("contains_safe", case.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show detective_story/1.\n#show safe_lesson/1."))
    return sorted(set(asp.atoms(model, "detective_story")))


def asp_verify() -> int:
    python_set = {"candy", "juice"}
    asp_set = {t[0] for t in asp_valid_cases()}
    if python_set == asp_set:
        print(f"OK: clingo gate matches Python registry ({len(asp_set)} cases).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("python:", sorted(python_set))
    print("asp:", sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld about gastroenteritis, sharing, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "woman", "man"])
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
    case = args.case or rng.choice(list(CASES))
    hero_name, hero_type, hero_role = rng.choice(HEROES)
    friend_name, friend_type = rng.choice(FRIENDS)
    adult_name, adult_type = rng.choice(ADULTS)

    if args.hero_type:
        hero_type = args.hero_type
    if args.friend_type:
        friend_type = args.friend_type
    if args.adult_type:
        adult_type = args.adult_type

    if args.hero_name:
        hero_name = args.hero_name
    if args.friend_name:
        friend_name = args.friend_name
    if args.adult_name:
        adult_name = args.adult_name

    return StoryParams(
        setting=setting,
        case=case,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_role=hero_role,
        friend_name=friend_name,
        friend_type=friend_type,
        adult_name=adult_name,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.entities.values():
        lines.append(f"{c.name} ({c.role}/{c.type}) meters={c.meters} memes={c.memes}")
    lines.append(f"setting={world.setting.place} / {world.setting.location}")
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
        print(asp_program("#show detective_story/1.\n#show safe_lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show detective_story/1.\n#show safe_lesson/1."))
        print(sorted(set(asp.atoms(model, "detective_story"))))
        print(sorted(set(asp.atoms(model, "safe_lesson"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("lane", "candy", "Mira", "girl", "junior detective", "Benny", "boy", "Mum"),
            StoryParams("library", "juice", "Noah", "boy", "junior detective", "Luna", "girl", "Dad"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
