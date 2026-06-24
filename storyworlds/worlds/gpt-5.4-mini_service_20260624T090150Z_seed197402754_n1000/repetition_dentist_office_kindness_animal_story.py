#!/usr/bin/env python3
"""
A small Storyweavers storyworld: animal kindness in a dentist office, with a
gentle repetition-based turn and a warm resolution.

The seed idea:
A shy animal keeps repeating a brave kindness phrase while waiting at the
dentist office. The repeated kindness helps the animal settle, cooperate, and
leave with a bright smile.
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
class Animal:
    name: str
    species: str
    kind: str = "animal"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the dentist office"
    waiting_room: str = "the waiting room"
    chair: str = "the tall chair"


@dataclass
class Action:
    id: str
    verb: str
    repeated_phrase: str
    nervous_word: str
    calming_word: str
    result_word: str


@dataclass
class StoryParams:
    animal: str
    name: str
    helper: str
    action: str
    seed: Optional[int] = None


ANIMALS = {
    "rabbit": "rabbit",
    "mouse": "mouse",
    "fox": "fox",
    "bear": "bear",
    "cat": "cat",
    "dog": "dog",
    "panda": "panda",
    "koala": "koala",
}

NAMES = {
    "rabbit": ["Ruby", "Riley", "Rosie"],
    "mouse": ["Milo", "Mina", "Mochi"],
    "fox": ["Fiona", "Finn", "Fern"],
    "bear": ["Benny", "Bela", "Bruno"],
    "cat": ["Coco", "Mimi", "Luna"],
    "dog": ["Daisy", "Buddy", "Barkley"],
    "panda": ["Poppy", "Pip", "Panda"],
    "koala": ["Kiki", "Koda", "Kona"],
}

HELPERS = ["the dentist", "the nurse", "a kind helper"]
SETTING = Setting()

ACTIONS = {
    "brush": Action(
        id="brush",
        verb="brush their teeth",
        repeated_phrase="I can be kind and brave",
        nervous_word="nervous",
        calming_word="gentle",
        result_word="clean",
    ),
    "sit": Action(
        id="sit",
        verb="sit in the chair",
        repeated_phrase="I can sit still and be kind",
        nervous_word="wobbly",
        calming_word="steady",
        result_word="safe",
    ),
    "open": Action(
        id="open",
        verb="open their mouth wide",
        repeated_phrase="I can open wide and be kind",
        nervous_word="shy",
        calming_word="calm",
        result_word="ready",
    ),
}


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Animal] = {}
        self.setting = SETTING
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, animal: Animal) -> Animal:
        self.entities[animal.name] = animal
        return animal

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _buildup(world: World, hero: Animal, action: Action) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0) + 1
    world.say(
        f"{hero.name} was a little {hero.species} who had never liked the dentist office very much."
    )
    world.say(
        f"{hero.pronoun().capitalize()} felt {action.nervous_word} when {world.setting.place} smelled like mint and soap."
    )
    world.say(
        f"Still, {hero.name} kept whispering, \"{action.repeated_phrase}.\""
    )


def _repetition(world: World, hero: Animal, helper: str, action: Action) -> None:
    hero.memes["repetition"] = hero.memes.get("repetition", 0) + 1
    world.say(
        f"At {world.setting.waiting_room}, {hero.name} said it again: \"{action.repeated_phrase}.\""
    )
    world.say(
        f"{helper.capitalize()} smiled and said, \"That is a kind way to talk to yourself.\""
    )
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1


def _turn(world: World, hero: Animal, action: Action) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    hero.meters["cooperation"] = hero.meters.get("cooperation", 0) + 1
    world.say(
        f"Then {hero.name} took a slow breath and did the {action.verb} part by part."
    )
    world.say(
        f"Each time {hero.name} repeated, \"{action.repeated_phrase},\" {hero.pronoun()} felt a little {action.calming_word}."
    )


def _resolution(world: World, hero: Animal, helper: str, action: Action) -> None:
    hero.meters["smile"] = hero.meters.get("smile", 0) + 1
    hero.meters["clean"] = hero.meters.get("clean", 0) + 1
    world.say(
        f"Before long, {hero.name} was done. {hero.pronoun().capitalize()} had a {action.result_word} smile and a softer, happier face."
    )
    world.say(
        f"{helper.capitalize()} gave {hero.name} a little wave, and {hero.name} waved back kindly."
    )
    world.say(
        f"{hero.name} left the dentist office repeating, \"{action.repeated_phrase}.\""
    )


def tell(params: StoryParams) -> World:
    action = ACTIONS[params.action]
    world = World()
    hero = world.add(Animal(name=params.name, species=params.animal))
    helper = params.helper

    world.facts.update(hero=hero, helper=helper, action=action, setting=world.setting)

    _buildup(world, hero, action)
    world.para()
    _repetition(world, hero, helper, action)
    world.para()
    _turn(world, hero, action)
    _resolution(world, hero, helper, action)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]
    action: Action = world.facts["action"]
    return [
        f"Write a short animal story set in a dentist office where {hero.name} keeps repeating a kind phrase to stay brave.",
        f"Tell a gentle story about a {hero.species} who learns kindness by repeating \"{action.repeated_phrase}\" at the dentist office.",
        "Write a child-friendly animal story with repetition, a nervous moment, and a smiling ending in a dentist office.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    action: Action = world.facts["action"]
    helper: str = world.facts["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.name}, a little {hero.species} who goes to the dentist office.",
        ),
        QAItem(
            question=f"What did {hero.name} keep repeating?",
            answer=f"{hero.name} kept repeating, \"{action.repeated_phrase}.\"",
        ),
        QAItem(
            question=f"Who helped {hero.name} feel calmer?",
            answer=f"{helper.capitalize()} helped by smiling and praising {hero.name}'s kindness.",
        ),
        QAItem(
            question=f"How did {hero.name} feel at the end?",
            answer=f"{hero.name} felt brave, kind, and happy, with a clean smile after the visit.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dentist office?",
            answer="A dentist office is a place where teeth are checked and cleaned.",
        ),
        QAItem(
            question="Why can repetition help a nervous child?",
            answer="Repeating a calm phrase can help a nervous child feel steadier and more confident.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:8} ({ent.species:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="rabbit", name="Ruby", helper="the dentist", action="brush"),
    StoryParams(animal="mouse", name="Milo", helper="the nurse", action="sit"),
    StoryParams(animal="fox", name="Fiona", helper="a kind helper", action="open"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal kindness storyworld set in a dentist office.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--action", choices=sorted(ACTIONS))
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    name = args.name or rng.choice(NAMES[animal])
    helper = args.helper or rng.choice(HELPERS)
    action = args.action or rng.choice(sorted(ACTIONS))
    return StoryParams(animal=animal, name=name, helper=helper, action=action)


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
valid_action(brush).
valid_action(sit).
valid_action(open).

good_story(A) :- valid_action(A).
#show good_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("setting", "dentist_office") for _ in [0])


def asp_program(show: str) -> str:
    return f"{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show good_story/1."))
    if asp.atoms(model, "good_story"):
        print("OK: ASP program is live.")
        return 0
    print("Mismatch or empty ASP result.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
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
