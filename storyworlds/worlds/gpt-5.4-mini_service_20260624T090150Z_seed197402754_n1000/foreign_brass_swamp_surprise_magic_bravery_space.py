#!/usr/bin/env python3
"""
A small story world: a child on a space adventure finds a foreign swamp surprise,
uses a little magic, and learns bravery.
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
class Place:
    name: str
    kind: str
    detail: str
    is_foreign: bool = False
    muddy: bool = False
    has_echo: bool = False


@dataclass
class ObjectThing:
    name: str
    kind: str
    material: str = ""
    shiny: bool = False
    important: bool = False


@dataclass
class Character:
    name: str
    type: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"surprise": 0.0, "magic": 0.0, "bravery": 0.0, "worry": 0.0})


@dataclass
class World:
    place: Place
    hero: Character
    companion: Character
    treasure: ObjectThing
    clue: ObjectThing
    history: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_swamp": Place(
        name="the moon swamp",
        kind="swamp",
        detail="a quiet basin under pale stars, where silver reeds waved in low gravity",
        is_foreign=True,
        muddy=True,
        has_echo=True,
    ),
    "asteroid_garden": Place(
        name="the asteroid garden",
        kind="garden",
        detail="a tiny garden inside a glass dome, floating far from home",
        is_foreign=True,
        muddy=False,
        has_echo=False,
    ),
    "space_station_dock": Place(
        name="the space station dock",
        kind="dock",
        detail="a bright docking bay with humming lights and open airlocks",
        is_foreign=False,
        muddy=False,
        has_echo=True,
    ),
}

HERO_NAMES = ["Mina", "Tobi", "Luna", "Ari", "Juno", "Sami"]
COMPANION_NAMES = ["Captain Sol", "Pip the Pilot", "Nia", "Rook"]
TRAITS = ["curious", "kind", "careful", "small", "brave"]


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = SETTINGS[params.place]
    hero = Character(name=params.hero_name, type="child", role="explorer", traits=["curious", "small", "brave"])
    companion = Character(name=params.companion_name, type="alien", role="guide", traits=["gentle", "wise"])
    treasure = ObjectThing(name="brass lantern", kind="treasure", material="brass", shiny=True, important=True)
    clue = ObjectThing(name="silver map chip", kind="clue", material="metal", shiny=False, important=True)
    world = World(place=place, hero=hero, companion=companion, treasure=treasure, clue=clue)
    return world


def run_story(world: World) -> None:
    place = world.place
    hero = world.hero
    companion = world.companion
    treasure = world.treasure
    clue = world.clue

    world.say(f"{hero.name} flew with {companion.name} to {place.name}, {place.detail}.")
    if place.is_foreign:
        hero.memes["surprise"] += 1
        world.say(f"It felt foreign and strange, and {hero.name} blinked at the new sky.")
    world.say(f"Near a soft patch of moss, {hero.name} found a {treasure.material} {treasure.name}.")
    world.say(f"Beside it lay a {clue.name} that flashed like a tiny star.")
    hero.meters["distance"] += 1

    hero.memes["worry"] += 1
    world.say(f"{hero.name} wanted to pick them up, but the swamp mud wobbled under every step.")

    hero.memes["surprise"] += 1
    hero.memes["magic"] += 1
    world.say(f"{companion.name} smiled and whispered a little magic word, and a glowing bridge appeared over the swamp.")

    hero.meters["distance"] += 1
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0
    world.say(f"With bravery, {hero.name} walked across the glowing bridge and lifted the brass lantern safely.")

    world.say(f"The lantern lit up the swamp, and the silver map chip showed a safe path home.")
    world.say(f"{hero.name} laughed, because the strange swamp had turned into a bright adventure instead of a scary one.")

    world.facts.update(
        place=place,
        hero=hero,
        companion=companion,
        treasure=treasure,
        clue=clue,
        foreign=place.is_foreign,
        swamp=place.kind == "swamp",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short space adventure story about a child who finds a brass treasure in a swamp.",
        f"Tell a gentle story where {world.hero.name} feels surprise in a foreign place and finds courage.",
        "Write a child-friendly adventure with magic, bravery, and a shiny brass object on a strange planet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    companion = world.companion
    treasure = world.treasure
    place = world.place
    return [
        QAItem(
            question=f"Where did {hero.name} go with {companion.name}?",
            answer=f"{hero.name} went to {place.name}, a strange place full of space-adventure wonder.",
        ),
        QAItem(
            question=f"What shiny treasure did {hero.name} find?",
            answer=f"{hero.name} found a brass lantern.",
        ),
        QAItem(
            question=f"How did {hero.name} get across the swamp?",
            answer=f"{companion.name} used a little magic to make a glowing bridge, and {hero.name} crossed it bravely.",
        ),
        QAItem(
            question=f"How did {hero.name} feel by the end of the story?",
            answer=f"{hero.name} felt brave and happy, because the scary swamp became a safe adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is brass?",
            answer="Brass is a shiny yellow metal often used for bells, keys, and lanterns.",
        ),
        QAItem(
            question="What is a swamp?",
            answer="A swamp is a wet, muddy place with shallow water and plants growing in it.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="Surprise is the feeling you get when something happens that you did not expect.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little afraid.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is when something impossible seems to happen in a wonderful story way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return (
        f"place={world.place.name}\n"
        f"hero={world.hero.name} meters={world.hero.meters} memes={world.hero.memes}\n"
        f"companion={world.companion.name} meters={world.companion.meters} memes={world.companion.memes}\n"
        f"treasure={world.treasure.name} material={world.treasure.material}\n"
        f"clue={world.clue.name} material={world.clue.material}"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with brass, swamp, surprise, magic, and bravery.")
    ap.add_argument("--place", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice(COMPANION_NAMES)
    return StoryParams(place=place, hero_name=hero_name, companion_name=companion_name, seed=args.seed)


ASP_RULES = r"""
place(moon_swamp).
place(asteroid_garden).
place(space_station_dock).

foreign(moon_swamp).
foreign(asteroid_garden).

swamp(moon_swamp).
brass(treasure).
surprise_event(find_treasure).
magic_event(open_bridge).
bravery_event(cross_bridge).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.is_foreign:
            lines.append(asp.fact("foreign", pid))
        if p.kind == "swamp":
            lines.append(asp.fact("swamp", pid))
    lines.append(asp.fact("brass", "treasure"))
    lines.append(asp.fact("surprise", "story"))
    lines.append(asp.fact("magic", "story"))
    lines.append(asp.fact("bravery", "story"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show foreign/1. #show swamp/1."))
    asp_set = set(asp.atoms(model, "foreign")) | set(asp.atoms(model, "swamp"))
    py_set = set()
    for pid, p in SETTINGS.items():
        if p.is_foreign:
            py_set.add((pid,))
        if p.kind == "swamp":
            py_set.add((pid,))
    if asp_set == py_set:
        print("OK: ASP parity verified.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    run_story(world)
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
        print(asp_program("#show foreign/1. #show swamp/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name=HERO_NAMES[0],
                companion_name=COMPANION_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
