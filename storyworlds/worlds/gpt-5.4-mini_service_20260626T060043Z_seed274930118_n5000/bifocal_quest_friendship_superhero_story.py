#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero quest about friendship and a
bifocal rescue.

The world is intentionally small and constraint-driven:
- a young hero wants to finish a quest,
- a friend notices a problem with reading the clues,
- bifocal glasses solve the clue-reading problem,
- the ending proves the quest changed the world state.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class City:
    id: str
    name: str
    place_phrase: str
    mood: str
    clue_source: str


@dataclass(frozen=True)
class Quest:
    id: str
    goal: str
    clue: str
    hazard: str
    reward: str
    requires_reading: bool = True


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    phrase: str
    use: str
    fixes_reading: bool = False


@dataclass(frozen=True)
class HeroSpec:
    id: str
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str


CITIES = {
    "rooftops": City("rooftops", "the rooftop district", "the rooftops", "bright and windy", "a blinking sign"),
    "museum": City("museum", "the museum avenue", "the museum steps", "quiet and echoing", "a glass case label"),
    "harbor": City("harbor", "the harbor walk", "the harbor wall", "salt-bright and busy", "a foggy map"),
}

QUESTS = {
    "save_map": Quest(
        "save_map",
        "find the hidden map piece",
        "the tiny letters on the map note",
        "a locked tower door",
        "a secret path to the lost garden",
        True,
    ),
    "return_emblem": Quest(
        "return_emblem",
        "return the shining emblem",
        "the clue under the bench plaque",
        "a gust of wind over the river",
        "the city parade ribbon",
        True,
    ),
    "find_lantern": Quest(
        "find_lantern",
        "locate the lost lantern",
        "the directions on the old poster",
        "a dark stairwell",
        "the festival lights",
        True,
    ),
}

GEAR = {
    "bifocal": Gear(
        "bifocal",
        "bifocal glasses",
        "a pair of bifocal glasses",
        "read tiny clues close up and far away",
        True,
    ),
    "mask": Gear(
        "mask",
        "a superhero mask",
        "a bright superhero mask",
        "look brave",
        False,
    ),
    "boots": Gear(
        "boots",
        "swift boots",
        "swift boots",
        "run faster",
        False,
    ),
}

HEROES = {
    "nova": HeroSpec("nova", "Nova", "hero", "she", "her", "her"),
    "spark": HeroSpec("spark", "Spark", "hero", "he", "him", "his"),
    "mira": HeroSpec("mira", "Mira", "hero", "she", "her", "her"),
}

FRIENDS = {
    "pip": HeroSpec("pip", "Pip", "friend", "they", "them", "their"),
    "jules": HeroSpec("jules", "Jules", "friend", "they", "them", "their"),
    "tess": HeroSpec("tess", "Tess", "friend", "she", "her", "her"),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    name: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn: set[str] = field(default_factory=set)
    owner: Optional[str] = None


@dataclass
class World:
    city: City
    quest: Quest
    hero: Entity
    friend: Entity
    gear: Optional[Entity] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _ent(eid: str, kind: str, name: str, role: str = "") -> Entity:
    return Entity(eid, kind, name, role=role, meters={"focus": 0.0, "risk": 0.0, "joy": 0.0},
                  memes={"hope": 0.0, "friendship": 0.0, "frustration": 0.0, "relief": 0.0})


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def tell(city: City, quest: Quest, hero: HeroSpec, friend: HeroSpec, seed: Optional[int] = None) -> World:
    world = World(
        city=city,
        quest=quest,
        hero=_ent(hero.id, "hero", hero.name, hero.role),
        friend=_ent(friend.id, "friend", friend.name, friend.role),
    )
    world.entities[hero.id] = world.hero
    world.entities[friend.id] = world.friend

    world.say(f"{hero.name} was a little superhero who loved helping people in {city.place_phrase}.")
    world.say(f"{hero.name} had a brave heart, and {friend.name} had a kind grin that always made hard days feel lighter.")
    world.say(f"One morning, {hero.name} heard about a quest to {quest.goal}.")

    world.para()
    world.say(f"At {city.place_phrase}, a clue waited on {city.clue_source}.")
    world.say(f"{hero.name} hurried closer, but the clue had {quest.clue}, and the tiny words blurred together.")
    world.hero.meters["focus"] += 1
    world.hero.meters["risk"] += 1
    world.hero.memes["frustration"] += 1
    world.hero.memes["hope"] += 0.5
    world.say(f"{hero.name} frowned. {hero.name} wanted to finish the quest, but the little words would not stay still.")

    world.para()
    world.say(f"{friend.name} stepped beside {hero.name} and said, \"We can do this together.\"")
    world.friend.memes["friendship"] += 1
    world.hero.memes["friendship"] += 1
    world.hero.memes["hope"] += 1
    world.say(f"{friend.name} reached for a special pair of glasses: {GEAR['bifocal'].phrase}.")
    world.gear = _ent("bifocal", "gear", "bifocal glasses")
    world.gear.owner = hero.id
    world.gear.worn.add(hero.id)

    world.say(f"They were {GEAR['bifocal'].use}, so {hero.name} could read the clue close up and far away.")
    world.say(f"With the {GEAR['bifocal'].label}, the tiny words finally made sense.")

    world.para()
    world.say(f"{hero.name} read the clue aloud and led the way through {city.mood} streets.")
    world.say(f"They solved the puzzle, slipped past the {quest.hazard}, and reached the place that held the prize.")
    world.hero.meters["focus"] += 2
    world.hero.meters["joy"] += 1
    world.hero.memes["relief"] += 1
    world.friend.meters["joy"] += 1
    world.friend.memes["friendship"] += 1

    world.say(f"In the end, {hero.name} found the {quest.reward}, and {friend.name} smiled beside {hero.name}.")
    world.say(f"The quest was done, and the pair of bifocal glasses had turned a blurry problem into a shared victory.")
    return world


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    quest: str
    hero: str
    friend: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(city="rooftops", quest="save_map", hero="nova", friend="pip"),
    StoryParams(city="museum", quest="return_emblem", hero="spark", friend="jules"),
    StoryParams(city="harbor", quest="find_lantern", hero="mira", friend="tess"),
]


def valid_pairs() -> list[tuple[str, str, str, str]]:
    return [(c, q, h, f) for c in CITIES for q in QUESTS for h in HEROES for f in FRIENDS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld about a quest, friendship, and bifocal glasses.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    city = args.city or rng.choice(list(CITIES))
    quest = args.quest or rng.choice(list(QUESTS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(city=city, quest=quest, hero=hero, friend=friend, seed=None)


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short superhero story for a young child about a quest, friendship, and the word "bifocal".',
        f"Tell a gentle superhero tale where {world.hero.name} and {world.friend.name} solve a quest using bifocal glasses.",
        f"Write a child-friendly story in which a tiny clue is hard to read until a friend brings bifocal glasses.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What was {world.hero.name} trying to do in the story?",
            answer=f"{world.hero.name} was trying to finish a quest and solve a clue that was hard to read.",
        ),
        QAItem(
            question=f"Who helped {world.hero.name} when the clue looked blurry?",
            answer=f"{world.friend.name} helped by bringing bifocal glasses and standing beside {world.hero.name}.",
        ),
        QAItem(
            question="What made the ending possible?",
            answer="The bifocal glasses let the hero read the clue close up and far away, so the quest could continue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are bifocal glasses for?",
            answer="Bifocal glasses help a person see clearly at two different distances, like reading something close and looking farther away.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or adventure to find something, fix something, or help someone.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind together.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(CITIES[params.city], QUESTS[params.quest], HEROES[params.hero], FRIENDS[params.friend], seed=params.seed)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"city={world.city.id} quest={world.quest.id}")
    lines.append(f"hero={world.hero.name} meters={world.hero.meters} memes={world.hero.memes}")
    lines.append(f"friend={world.friend.name} meters={world.friend.meters} memes={world.friend.memes}")
    if world.gear:
        lines.append(f"gear={world.gear.name} owner={world.gear.owner} worn={sorted(world.gear.worn)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
city(C) :- city_fact(C).
quest(Q) :- quest_fact(Q).
hero(H) :- hero_fact(H).
friend(F) :- friend_fact(F).

compatible(C,Q,H,F) :- city(C), quest(Q), hero(H), friend(F), H != F.
#show compatible/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for cid in CITIES:
        lines.append(asp.fact("city_fact", cid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_fact", qid))
    for hid in HEROES:
        lines.append(asp.fact("hero_fact", hid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend_fact", fid))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/4."))
    clingo_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_pairs())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python registry ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python registry:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/4."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
        print(format_json(samples))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} + {p.friend} in {p.city} on quest {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
