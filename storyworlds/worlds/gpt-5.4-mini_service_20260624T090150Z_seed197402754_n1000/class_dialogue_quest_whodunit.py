#!/usr/bin/env python3
"""
storyworlds/worlds/class_dialogue_quest_whodunit.py
===================================================

A small whodunit storyworld set in a classroom, where a class of children
follows a clue trail through dialogue and a simple quest to solve a gentle
mystery.

Premise:
- A class notices something important is missing.
- Everyone talks about what they saw.
- The search becomes a quest of clues, careful questions, and one smart reveal.

The world model tracks:
- physical state: where things are, who holds what, what is hidden
- emotional state: surprise, worry, suspicion, relief
- clue progression and resolution

The stories are intended to feel like small detective tales for children:
clear setup, a few clues, a turn, and a satisfying ending image.
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
class Character:
    id: str
    kind: str = "character"
    role: str = "student"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    holds: Optional[str] = None
    knows: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Clue:
    id: str
    label: str
    place: str
    hint: str


@dataclass
class Setting:
    place: str = "the classroom"
    subplaces: list[str] = field(default_factory=lambda: ["the desk", "the bookshelf", "the coat hooks", "the art corner"])


@dataclass
class StoryParams:
    place: str
    missing: str
    hero: str
    sidekick: str
    culprit: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Character] = {}
        self.clues: dict[str, Clue] = {}
        self.hidden: dict[str, str] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_character(self, c: Character) -> Character:
        self.entities[c.id] = c
        return c

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A classroom whodunit with dialogue and a small quest.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--missing", choices=MISSING_ITEMS.keys())
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--sidekick", choices=NAMES)
    ap.add_argument("--culprit", choices=NAMES)
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


SETTINGS = {
    "classroom": Setting("the classroom"),
}

MISSING_ITEMS = {
    "glasses": ("the reading glasses", "desk", "needed to read the clue card"),
    "key": ("the classroom key", "coat hooks", "opened the clue box"),
    "ribbon": ("the blue ribbon", "bookshelf", "was tied around the note"),
}

NAMES = ["Mina", "Noah", "Iris", "Leo", "Maya", "Finn", "Zoe", "Arun", "Lina", "Eli"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "gentle", "quick-thinking"]


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add_character(Character(id=params.hero, label=params.hero, traits=[random.choice(TRAITS)]))
    sidekick = world.add_character(Character(id=params.sidekick, label=params.sidekick, traits=[random.choice(TRAITS)]))
    culprit = world.add_character(Character(id=params.culprit, label=params.culprit, traits=["nervous"]))
    item_phrase, hiding_place, clue_reason = MISSING_ITEMS[params.missing]
    clue = world.add_clue(Clue(id="first_clue", label=f"a clue about {params.missing}", place=hiding_place, hint=clue_reason))
    world.hidden[params.missing] = hiding_place
    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "culprit": culprit,
        "missing": params.missing,
        "item_phrase": item_phrase,
        "hiding_place": hiding_place,
        "clue_reason": clue_reason,
        "clue": clue,
        "setting": world.setting,
    }
    return world


def intro(world: World) -> None:
    f = world.facts
    hero, sidekick = f["hero"], f["sidekick"]
    item_phrase = f["item_phrase"]
    world.say(f"In {world.setting.place}, {hero.name_word()} noticed that {item_phrase} was gone.")
    world.say(f"“This is odd,” {hero.name_word()} said. “It was here before class.”")
    world.say(f"“Then we should ask questions,” said {sidekick.name_word()}. “A mystery is just a clue that has not spoken yet.”")


def clue_scene(world: World) -> None:
    f = world.facts
    culprit, sidekick = f["culprit"], f["sidekick"]
    clue = f["clue"]
    world.para()
    world.say(f"The class began a quiet quest around {world.setting.place}.")
    world.say(f"At {clue.place}, {sidekick.name_word()} found {clue.label}.")
    world.say(f"“That hint says someone was near the {clue.place},” said {sidekick.name_word()}.")
    world.say(f"{culprit.name_word()} looked away and said, “I only went there to tidy up.”")
    culprit.memes["worry"] = culprit.memes.get("worry", 0) + 1
    culprit.memes["suspicion"] = culprit.memes.get("suspicion", 0) + 1
    world.facts["clue_found"] = True


def dialogue_turn(world: World) -> None:
    f = world.facts
    hero, sidekick, culprit = f["hero"], f["sidekick"], f["culprit"]
    missing = f["missing"]
    world.say(f'“Did you see the {missing}?” asked {hero.name_word()}.')
    world.say(f'“No,” said {culprit.name_word()}, “but I saw a little note near the desk.”')
    world.say(f'“Then let us follow the note,” said {sidekick.name_word()}. “A good mystery is solved by listening carefully.”')
    culprit.knows.add("questioned")
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1


def reveal(world: World) -> None:
    f = world.facts
    hero, sidekick, culprit = f["hero"], f["sidekick"], f["culprit"]
    missing = f["missing"]
    hiding_place = f["hiding_place"]
    item_phrase = f["item_phrase"]
    culprit.holds = missing
    world.para()
    world.say(f"At last, the class reached {hiding_place}.")
    world.say(f"There, tucked safely away, was {item_phrase}.")
    world.say(f"{culprit.name_word()} sighed. “I moved it while cleaning and forgot to put it back.”")
    world.say(f'“So that is the whole mystery,” said {hero.name_word()}. “A small mistake, not a mean trick.”')
    world.say(f'“And now the clue has finished talking,” said {sidekick.name_word()}, smiling.')
    culprit.memes["worry"] = 0
    culprit.memes["relief"] = culprit.memes.get("relief", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    sidekick.memes["relief"] = sidekick.memes.get("relief", 0) + 1
    world.facts["resolved"] = True


def ending(world: World) -> None:
    f = world.facts
    hero, sidekick = f["hero"], f["sidekick"]
    item_phrase = f["item_phrase"]
    world.say(f"Before the bell rang, the class put everything back in order.")
    world.say(f"{hero.name_word()} carried {item_phrase} back to its place, and {sidekick.name_word()} locked the lesson in a happy grin.")
    world.say("The classroom felt calm again, as if the whole day had straightened its tie.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    intro(world)
    clue_scene(world)
    dialogue_turn(world)
    reveal(world)
    ending(world)
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "classroom"
    missing = args.missing or rng.choice(list(MISSING_ITEMS.keys()))
    hero = args.hero or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != hero])
    culprit = args.culprit or rng.choice([n for n in NAMES if n not in {hero, sidekick}])
    if len({hero, sidekick, culprit}) < 3:
        raise StoryError("The hero, sidekick, and culprit must be three different children.")
    return StoryParams(place=place, missing=missing, hero=hero, sidekick=sidekick, culprit=culprit)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short classroom whodunit about a missing {f["missing"]} and a clue-led quest.',
        f'Create a gentle mystery where {f["hero"].name_word()} and {f["sidekick"].name_word()} ask questions until they find the {f["item_phrase"]}.',
        f'Write a child-friendly dialogue story in which a class solves a small mystery in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, culprit = f["hero"], f["sidekick"], f["culprit"]
    missing, item_phrase, hiding_place = f["missing"], f["item_phrase"], f["hiding_place"]
    return [
        QAItem(
            question=f"What mystery started the story in {world.setting.place}?",
            answer=f"The mystery started when {hero.name_word()} noticed that {item_phrase} was missing from the classroom.",
        ),
        QAItem(
            question=f"Who helped {hero.name_word()} follow the clues?",
            answer=f"{sidekick.name_word()} helped by asking careful questions and following the clue trail.",
        ),
        QAItem(
            question=f"Where was the missing {missing} found?",
            answer=f"It was found at {hiding_place}, tucked safely away after the class followed the clues.",
        ),
        QAItem(
            question=f"Why did {culprit.name_word()} move the item?",
            answer=f"{culprit.name_word()} said they moved it while cleaning and then forgot to put it back.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"The mystery ended with the missing item returned, the confusion cleared up, and everyone feeling relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps people figure out what happened.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important or solve a problem.",
        ),
        QAItem(
            question="Why do people ask questions in a mystery?",
            answer="People ask questions to learn what each person saw and to help solve the puzzle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for c in world.entities.values():
        bits = []
        if c.holds:
            bits.append(f"holds={c.holds}")
        if c.knows:
            bits.append(f"knows={sorted(c.knows)}")
        if c.memes:
            bits.append(f"memes={dict(c.memes)}")
        lines.append(f"{c.id}: {' '.join(bits)}")
    lines.append(f"hidden: {world.hidden}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
place(classroom).
mystery(missing_item).
quest(follow_clues).

solved :- found_clue, found_item, explanation_given.
found_clue :- question_asked, clue_nearby.
found_item :- clue_found, searched(hiding_place).
explanation_given :- culprit_confesses.

#show solved/0.
#show found_clue/0.
#show found_item/0.
#show explanation_given/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "classroom"),
        asp.fact("mystery", "missing_item"),
        asp.fact("quest", "follow_clues"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_reasoner():
    import asp
    return asp


def asp_verify() -> int:
    asp = build_reasoner()
    model = asp.one_model(asp_program("#show mystery/1."))
    ok = bool(model)
    if ok:
        print("OK: ASP program loads and produces a model.")
        return 0
    print("ASP verification failed.")
    return 1


CURATED = [
    StoryParams(place="classroom", missing="glasses", hero="Mina", sidekick="Noah", culprit="Iris"),
    StoryParams(place="classroom", missing="key", hero="Leo", sidekick="Maya", culprit="Finn"),
    StoryParams(place="classroom", missing="ribbon", hero="Zoe", sidekick="Arun", culprit="Lina"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for missing in MISSING_ITEMS:
            for hero in NAMES:
                for sidekick in NAMES:
                    for culprit in NAMES:
                        if len({hero, sidekick, culprit}) == 3:
                            combos.append((place, missing, hero))
    return combos


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: missing {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
