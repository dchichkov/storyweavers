#!/usr/bin/env python3
"""
A standalone storyworld script for a tall-tale archaeology quest with kindness
and a lesson learned.

The world:
- A young quester searches for an old river hill dig site.
- A proud falcon helps by circling overhead and finding clues.
- A stubborn choice risks a dig find.
- Kindness toward a tired helper changes the outcome.
- The lesson learned is that gentleness can uncover more than hurry.

This script follows the Storyweavers world contract.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, subject: str = "they") -> str:
        return subject


@dataclass
class Falcon:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    perched: bool = False


@dataclass
class Relic:
    name: str
    condition: str = "hidden"
    found: bool = False
    cared_for: bool = False


@dataclass
class Site:
    place: str
    landmark: str
    weather: str
    clue: str
    depth: int


@dataclass
class StoryParams:
    place: str
    site: str
    hero_name: str
    falcon_name: str
    seed: Optional[int] = None


@dataclass
class World:
    site: Site
    hero: Person
    falcon: Falcon
    relic: Relic
    meters: dict[str, float] = field(default_factory=lambda: {"dust": 0.0, "hope": 0.0, "care": 0.0, "rush": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "pride": 0.0, "lesson": 0.0, "wonder": 0.0})
    history: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, line: str) -> None:
        if line:
            self.history.append(line)

    def paragraph(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(chunk for chunk in self.history if chunk)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "riverbank": Site(
        place="the riverbank",
        landmark="a leaning willow",
        weather="windy",
        clue="a shiny blue pebble",
        depth=3,
    ),
    "mesa": Site(
        place="the red mesa",
        landmark="a broken stone arch",
        weather="hot",
        clue="a feather-shaped shard",
        depth=5,
    ),
    "cliffside": Site(
        place="the cliffside dig",
        landmark="a striped lookout pole",
        weather="breezy",
        clue="a circle of carved shells",
        depth=4,
    ),
}

QUEST_WORDS = [
    "quest",
    "treasure hunt",
    "search",
    "journey",
]

HERO_NAMES = [
    "Nora",
    "Milo",
    "June",
    "Theo",
    "Ivy",
    "Ada",
]

FALCON_NAMES = [
    "Sky",
    "Brass",
    "Swift",
    "Comet",
    "Gale",
]

KNOWLEDGE = {
    "falcon": (
        "What is a falcon?",
        "A falcon is a fast bird of prey that can soar high and spot tiny things from far away."
    ),
    "archeology": (
        "What does an archeologist do?",
        "An archeologist looks for old things people made long ago and learns stories from the ground."
    ),
    "kindness": (
        "What is kindness?",
        "Kindness means being gentle, helpful, and caring to someone or something."
    ),
    "lesson": (
        "What is a lesson learned?",
        "A lesson learned is something wise a person understands after trying, making mistakes, or changing their mind."
    ),
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    site = PLACES[params.place]
    hero = Person(name=params.hero_name, role="young archeologist")
    falcon = Falcon(name=params.falcon_name)
    relic = Relic(name="the old river charm")
    world = World(site=site, hero=hero, falcon=falcon, relic=relic)
    world.facts.update(
        quest_word="quest",
        place=site.place,
        landmark=site.landmark,
        clue=site.clue,
        hero_name=hero.name,
        falcon_name=falcon.name,
        relic=relic.name,
    )
    return world


def _introduce(world: World) -> None:
    world.meters["hope"] += 1
    world.memes["wonder"] += 1
    world.say(
        f"Long ago, on {world.site.place}, there lived a young archeologist named {world.hero.name}."
    )
    world.say(
        f"Near {world.site.landmark}, {world.hero.name} dreamed of a big quest and of uncovering {world.relic.name}."
    )


def _falcon_arrives(world: World) -> None:
    world.falcon.perched = True
    world.falcon.meters["altitude"] = 8
    world.falcon.memes["alert"] = 1
    world.say(
        f"One bright morning, {world.falcon.name} the falcon swept down like a ribbon in the wind and landed on a post."
    )
    world.say(
        f"{world.falcon.name} tilted its sharp head, as if it already knew where the best clue was hiding."
    )


def _begin_search(world: World) -> None:
    world.meters["dust"] += 1
    world.hero.meters["digging"] = world.hero.meters.get("digging", 0.0) + 1
    world.say(
        f"{world.hero.name} began the archeology quest with a little brush, a little trowel, and a lot of eager feet."
    )
    world.say(
        f"Together, {world.hero.name} and {world.falcon.name} followed {world.site.clue} and the shadow of {world.site.landmark}."
    )


def _tension(world: World) -> None:
    world.meters["rush"] += 1
    world.hero.memes["pride"] = world.hero.memes.get("pride", 0.0) + 1
    world.say(
        f"Before long, {world.hero.name} got so proud of the fast digging that {world.hero.name} started scooping too hard."
    )
    world.say(
        f"A tiny stone clinked and skittered down the dirt, and {world.falcon.name} gave a loud cry, as if to warn, \"Careful!\""
    )


def _lesson_turn(world: World) -> None:
    world.memes["kindness"] += 1
    world.hero.memes["kindness"] = world.hero.memes.get("kindness", 0.0) + 1
    world.hero.memes["lesson"] = world.hero.memes.get("lesson", 0.0) + 1
    world.relic.condition = "safe"
    world.relic.found = True
    world.relic.cared_for = True
    world.say(
        f"{world.hero.name} stopped, knelt down, and brushed the dirt away with a kinder hand."
    )
    world.say(
        f"{world.hero.name} whispered an apology to the ground itself, then used the soft brush the right way."
    )
    world.say(
        f"That gentle choice let {world.falcon.name} circle low and point to a hidden shape that had been waiting all along."
    )
    world.say(
        f"Out came {world.relic.name}, old and dusty, but safe and shining in the afternoon light."
    )


def _ending(world: World) -> None:
    world.say(
        f"{world.hero.name} smiled at {world.falcon.name} and said the biggest lesson of the quest: "
        f"\"Kindness helps the truth come up clean.\""
    )
    world.say(
        f"And from that day on, {world.hero.name} dug slower, listened better, and treated every little clue like a treasure."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _introduce(world)
    world.history.append("")
    _falcon_arrives(world)
    _begin_search(world)
    _tension(world)
    _lesson_turn(world)
    _ending(world)
    world.facts.update(
        found=world.relic.found,
        kind=world.hero.memes.get("kindness", 0.0) > 0,
        lesson=world.hero.memes.get("lesson", 0.0) > 0,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_place(place: str) -> bool:
    return place in PLACES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError(f"(No story: unknown place {args.place!r}.)")
    place = args.place or rng.choice(sorted(PLACES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    falcon_name = args.falcon or rng.choice(FALCON_NAMES)
    return StoryParams(
        place=place,
        site=PLACES[place].place,
        hero_name=hero_name,
        falcon_name=falcon_name,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a tall tale for a young child about a falcon and an archeology quest at {world.site.place}.',
        f"Tell a story where {world.hero.name} learns kindness while searching for {world.relic.name} with {world.falcon.name}.",
        f"Create a gentle adventure about {world.site.landmark}, a falcon, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who went on the quest at {world.site.place}?",
            answer=f"{world.hero.name}, a young archeologist, went on the quest at {world.site.place} with {world.falcon.name} the falcon.",
        ),
        QAItem(
            question=f"What did {world.falcon.name} help find?",
            answer=f"{world.falcon.name} helped find {world.relic.name}.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer="The hero learned that kindness and gentle hands help uncover old treasures safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_valid(P) :- place(P).
quest_story(P) :- place_valid(P), falcon(F), archeology(hero), kindness(hero), lesson(hero).
#show place_valid/1.
#show quest_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in PLACES:
        lines.append(asp.fact("place", key))
    lines.append(asp.fact("falcon", "falcon"))
    lines.append(asp.fact("archeology", "hero"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("lesson", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show place_valid/1.")
    model = asp.one_model(prog)
    clingo_places = sorted(set(asp.atoms(model, "place_valid")))
    python_places = sorted((p,) for p in PLACES)
    if clingo_places == python_places:
        print(f"OK: clingo gate matches python registry ({len(clingo_places)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", clingo_places)
    print("  python:", python_places)
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale archaeology quest world with falcon, kindness, and a lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--falcon")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"site: {world.site.place}, landmark: {world.site.landmark}, clue: {world.site.clue}")
    lines.append(f"hero: {world.hero.name}, memes={world.hero.memes}")
    lines.append(f"falcon: {world.falcon.name}, perched={world.falcon.perched}, memes={world.falcon.memes}")
    lines.append(f"relic: {world.relic.name}, found={world.relic.found}, condition={world.relic.condition}")
    lines.append(f"meters: {world.meters}")
    lines.append(f"memes: {world.memes}")
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
        print(asp_program("#show quest_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_story/1."))
        print(sorted(set(asp.atoms(model, "quest_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            params = StoryParams(place=place, site=PLACES[place].place, hero_name="Nora", falcon_name="Swift")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
