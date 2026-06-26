#!/usr/bin/env python3
"""
A tiny fable-style story world about a cord, a dish, repetition, and surprise.

A seed tale:
---
A little mouse named Milo found a shiny cord and a blue dish. He liked to
tap the dish with the cord to make a tiny song. Every morning, Milo tapped,
tapped, tapped. One day, the cord slipped, the dish wobbled, and a hidden
berry rolled out from under it. Milo was surprised. He laughed, shared the
berry with his friend, and learned that small, repeated habits can hide a
kind surprise.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rat", "cat", "fox", "bird"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Prop:
    label: str
    phrase: str
    type: str
    surprise_source: bool = False


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False),
    "kitchen": Setting(place="the kitchen", indoor=True),
    "barn": Setting(place="the barn", indoor=True),
}

HERO_TYPES = ["mouse", "rabbit", "sparrow", "fox"]
FRIEND_TYPES = ["mouse", "rabbit", "sparrow", "turtle", "duck"]
TRAITS = ["careful", "curious", "patient", "cheerful", "quiet"]

CORDS = {
    "string": Prop(label="cord", phrase="a soft red cord", type="cord"),
    "rope": Prop(label="cord", phrase="a little blue cord", type="cord"),
    "twine": Prop(label="cord", phrase="a thin gold cord", type="cord"),
}

DISHES = {
    "dish": Prop(label="dish", phrase="a blue dish", type="dish", surprise_source=True),
    "bowl": Prop(label="dish", phrase="a green dish", type="dish", surprise_source=True),
    "cup": Prop(label="dish", phrase="a small dish", type="dish", surprise_source=True),
}

CURATED = [
    StoryParams(setting="garden", hero_name="Milo", hero_type="mouse",
                friend_name="Nina", friend_type="rabbit", trait="curious"),
    StoryParams(setting="kitchen", hero_name="Tia", hero_type="sparrow",
                friend_name="Gus", friend_type="mouse", trait="patient"),
    StoryParams(setting="barn", hero_name="Pip", hero_type="rabbit",
                friend_name="Dot", friend_type="duck", trait="careful"),
]


@dataclass
class StoryState:
    repeated_taps: int = 0
    dish_wobbled: bool = False
    surprise_found: bool = False
    surprise_kind: str = "berry"
    shared: bool = False
    lesson: str = ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about cord, dish, surprise, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    hero_name = args.hero_name or rng.choice(["Milo", "Tia", "Pip", "Penny", "Luna", "Toby"])
    friend_name = args.friend_name or rng.choice(["Nina", "Gus", "Dot", "Bea", "Ollie", "Ada"])
    if hero_name == friend_name:
        raise StoryError("The hero and the friend must have different names.")
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=hero_type,
                       friend_name=friend_name, friend_type=friend_type,
                       trait=trait)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, StoryState]:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name))
    cord = world.add(Entity(id="cord", type="cord", label="cord", phrase="a cord"))
    dish = world.add(Entity(id="dish", type="dish", label="dish", phrase="a dish", caretaker=friend.id))
    state = StoryState()
    world.facts.update(hero=hero, friend=friend, cord=cord, dish=dish, state=state, params=params)
    return world, hero, friend, cord, dish, state


def _intro(world: World, hero: Entity, friend: Entity, cord: Entity, dish: Entity, params: StoryParams) -> None:
    world.say(f"In {world.setting.place}, {hero.label} was a {params.trait} little {hero.type} who liked small things that made a difference.")
    world.say(f"{hero.label} found {cord.phrase} and {dish.phrase}, and that pair became {hero.pronoun('possessive')} favorite toy and treasure.")
    world.say(f"{hero.label} loved to use the cord near the dish, because the tiny tapping sound made the day feel like a song.")


def _repetition(world: World, hero: Entity, state: StoryState) -> None:
    state.repeated_taps = 3
    world.say(f"Each morning, {hero.label} tapped the dish with the cord: tap, tap, tap.")
    world.say(f"Then {hero.label} did it again the next morning, and again after that, because repetition felt safe and sweet.")


def _surprise(world: World, hero: Entity, friend: Entity, dish: Entity, state: StoryState) -> None:
    state.dish_wobbled = True
    state.surprise_found = True
    state.surprise_kind = "berry"
    world.say(f"One day, the cord slipped sideways, and the dish wobbled with a little clink.")
    world.say(f"From beneath the dish rolled a hidden berry, round and bright as a bead.")
    world.say(f"{hero.label} blinked in surprise. {hero.pronoun().capitalize()} had not known the dish was hiding a treat.")


def _resolution(world: World, hero: Entity, friend: Entity, state: StoryState) -> None:
    state.shared = True
    state.lesson = "little habits can lead to gentle surprises"
    world.say(f"{hero.label} laughed and called {friend.label} over to look.")
    world.say(f"They shared the berry together, and {hero.label} learned that little habits can lead to gentle surprises.")


def tell(params: StoryParams) -> World:
    world, hero, friend, cord, dish, state = _setup_world(params)
    _intro(world, hero, friend, cord, dish, params)
    world.para()
    _repetition(world, hero, state)
    world.para()
    _surprise(world, hero, friend, dish, state)
    world.para()
    _resolution(world, hero, friend, state)
    world.facts.update(
        setting=world.setting.place,
        repeated_taps=state.repeated_taps,
        surprise_kind=state.surprise_kind,
        shared=state.shared,
        lesson=state.lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short fable for a child about "{f["cord"].label}" and "{f["dish"].label}" with a surprise hidden by repetition.',
        f"Tell a gentle story where {hero.label} repeats a small action every day, then finds a surprise near a dish.",
        f'Create a simple moral tale in which a cord, a dish, and a repeated habit lead to a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"The story is about {hero.label}, a {params.trait} little {hero.type}, and {friend.label}, who helps at the end.",
        ),
        QAItem(
            question=f"What did {hero.label} do again and again?",
            answer=f"{hero.label} tapped the dish with the cord every morning, and the tapping was repeated like a little song.",
        ),
        QAItem(
            question=f"What surprise did {hero.label} find under the dish?",
            answer=f"{hero.label} found a hidden berry under the dish, and that surprise changed the ending of the story.",
        ),
        QAItem(
            question=f"What did {hero.label} and {friend.label} do with the surprise?",
            answer=f"They shared the berry together, so the surprise became a kind moment instead of a secret one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cord?",
            answer="A cord is a long, thin piece of string or rope that can be tied, pulled, or used to hold things together.",
        ),
        QAItem(
            question="What is a dish?",
            answer="A dish is a shallow container used to hold food or small objects.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same action again and again.",
        ),
        QAItem(
            question="What is surprise?",
            answer="A surprise is something unexpected that makes someone stop and notice.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    f = world.facts
    state: StoryState = f["state"]
    lines = ["--- world model state ---"]
    lines.append(f"setting={world.setting.place}")
    lines.append(f"hero={f['hero'].label}:{f['hero'].type}")
    lines.append(f"friend={f['friend'].label}:{f['friend'].type}")
    lines.append(f"cord={f['cord'].phrase}")
    lines.append(f"dish={f['dish'].phrase}")
    lines.append(f"repeated_taps={state.repeated_taps}")
    lines.append(f"dish_wobbled={state.dish_wobbled}")
    lines.append(f"surprise_found={state.surprise_found}")
    lines.append(f"shared={state.shared}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a repeated action leads to a surprise and a shared ending.
repeated(hero, 3) :- hero(hero).
surprise_after_repeat(hero) :- repeated(hero, 3), dish(dish), cord(cord).
shared_ending(hero) :- surprise_after_repeat(hero), share(hero).
valid_story(S) :- setting(S), surprise_after_repeat(hero), shared_ending(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("dish", "dish"))
    lines.append(asp.fact("cord", "cord"))
    lines.append(asp.fact("share", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(SETTINGS.keys())
    cl = {x[0] for x in asp_valid_stories()}
    if cl == py:
        print(f"OK: ASP gate matches settings ({len(cl)} story settings).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


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


def resolve_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story settings:")
        for item in stories:
            print(f"  {item[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_story_choice(args, random.Random(seed))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: cord, dish, surprise, repetition ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
