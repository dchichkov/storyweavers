#!/usr/bin/env python3
"""
storyworlds/worlds/zebra_parking_lot_teamwork_quest_pirate_tale.py
===================================================================

A small Storyweavers world about a zebra, a parking lot, teamwork, and a quest.
The tale keeps a pirate-story flavor: a little crew, a map, a missing treasure,
and a shared plan that gets everyone home by the end.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"zebra", "captain", "mate"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the parking lot"
    has_trucks: bool = True
    has_lines: bool = True


@dataclass
class Quest:
    goal: str
    clue: str
    risk: str
    turn: str
    ending: str
    keyword: str = "quest"


@dataclass
class Crew:
    helper: str
    helper_type: str
    helper_label: str
    tool_label: str
    tool_phrase: str
    tool_kind: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
PLACEs = {
    "parking_lot": Place(name="the parking lot", has_trucks=True, has_lines=True),
}

QUESTS = {
    "lost_map": Quest(
        goal="find the missing map",
        clue="a glittery feather stuck under a red wagon",
        risk="the map might blow away under the cars",
        turn="the zebra could not search alone, because the map was tucked beneath two parked vans and a rolling cart",
        ending="the map was safe in the captain's satchel",
        keyword="quest",
    ),
    "shell_key": Quest(
        goal="find the shell key",
        clue="a small shell wedged beside a scooter wheel",
        risk="the key might slide into a storm drain",
        turn="the zebra needed a helper to lift the scooter and look under it",
        ending="the shell key was found before it could vanish",
        keyword="quest",
    ),
}

CREWS = {
    "parrot": Crew(
        helper="Pip",
        helper_type="parrot",
        helper_label="parrot",
        tool_label="hook",
        tool_phrase="a shiny hook for lifting things",
        tool_kind="hook",
    ),
    "mouse": Crew(
        helper="Mina",
        helper_type="mouse",
        helper_label="mouse",
        tool_label="lantern",
        tool_phrase="a tiny lantern that shone under the cars",
        tool_kind="lantern",
    ),
}

ZEBRA_NAMES = ["Zuri", "Nala", "Milo", "Tavi", "Juno"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Salt", "Captain Blue"]
TRAITS = ["brave", "curious", "cheerful", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "parking_lot"
    quest: str = "lost_map"
    crew: str = "parrot"
    name: str = "Zuri"
    trait: str = "brave"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def say_intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little zebra with a pirate heart, and {hero.pronoun('possessive')} "
        f"striped tail swished like a flag in the wind."
    )
    world.say(
        f"{hero.id} loved a good {quest.keyword}, especially when it promised {quest.goal}."
    )


def say_setup(world: World, hero: Entity, quest: Quest, crew: Crew) -> None:
    world.say(
        f"One bright day in {world.place.name}, {hero.id} spotted {quest.clue} near the painted parking lines."
    )
    world.say(
        f"{hero.id} knew the clue mattered, because {quest.risk}."
    )
    world.say(
        f"Then {crew.helper} the {crew.helper_label} landed close by and showed {hero.pronoun('object')} "
        f"{crew.tool_phrase}."
    )


def say_conflict(world: World, hero: Entity, quest: Quest, crew: Crew) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} wanted to rush off by {hero.pronoun('possessive')}self, but the parking lot was busy with carts and car doors."
    )
    world.say(
        f"{quest.turn.capitalize()}, so {hero.id} and {crew.helper} shared a careful plan instead."
    )


def say_teamwork(world: World, hero: Entity, quest: Quest, crew: Crew) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"The zebra held the clue high while {crew.helper} shone the lantern under the nearest truck."
        if crew.tool_kind == "lantern"
        else f"The zebra held the clue high while {crew.helper} used the hook to lift a loose tarp."
    )
    world.say(
        f"Together they checked every row, whispering like tiny pirates on a secret {quest.keyword}."
    )


def say_resolution(world: World, hero: Entity, quest: Quest, crew: Crew) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"At last, they found what they wanted, and {quest.ending}."
    )
    world.say(
        f"{hero.id} grinned at {crew.helper} and said the best treasure of all was working together."
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACEs:
        raise StoryError(f"Unknown place: {params.place}")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    if params.crew not in CREWS:
        raise StoryError(f"Unknown crew helper: {params.crew}")

    world = World(PLACEs[params.place])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="zebra",
        label="zebra",
        traits=[params.trait, "little"],
    ))
    crew = CREWS[params.crew]
    helper = world.add(Entity(
        id=crew.helper,
        kind="character",
        type=crew.helper_type,
        label=crew.helper_label,
        traits=["helpful"],
    ))
    quest = QUESTS[params.quest]
    world.facts.update(hero=hero, helper=helper, quest=quest, crew=crew, params=params)

    say_intro(world, hero, quest)
    world.para()
    say_setup(world, hero, quest, crew)
    world.para()
    say_conflict(world, hero, quest, crew)
    say_teamwork(world, hero, quest, crew)
    world.para()
    say_resolution(world, hero, quest, crew)
    return world


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    crew: Crew = f["crew"]  # type: ignore[assignment]
    return [
        f'Write a short pirate-style story for a child about a zebra named {hero.id} in a parking lot.',
        f"Tell a gentle quest story where {hero.id} needs teamwork to {quest.goal}.",
        f'Write a little tale that includes the word "zebra" and ends with friends solving a parking-lot problem together.',
        f"Make it feel like a pirate adventure, but set it in {world.place.name} and keep it friendly for children.",
        f"Show how {crew.helper} helps {hero.id} finish a {quest.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    crew: Crew = f["crew"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little zebra who likes pirate-style adventures and teamwork.",
        ),
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {world.place.name}, where the zebra looks for clues between the parked cars.",
        ),
        QAItem(
            question=f"What was {hero.id}'s big {quest.keyword}?",
            answer=f"{hero.id}'s big {quest.keyword} was to {quest.goal}.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} the {crew.helper_label} helped by bringing {crew.tool_phrase}.",
        ),
        QAItem(
            question=f"How did teamwork help in the end?",
            answer=f"Teamwork helped because {hero.id} and {helper.id} searched together and found {quest.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zebra?",
            answer="A zebra is an animal with black-and-white stripes, like a horse with a striped coat.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or adventure to find something important.",
        ),
        QAItem(
            question="What is a parking lot?",
            answer="A parking lot is a place where cars and trucks are parked.",
        ),
        QAItem(
            question="Why do pirates like treasure maps?",
            answer="Pirates like treasure maps because they show the way to something hidden and exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(zebra).
place(parking_lot).
quest(lost_map).
quest(shell_key).
helper(parrot).
helper(mouse).

valid(Place, Quest, Helper) :- place(Place), quest(Quest), helper(Helper).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACEs:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for c in CREWS:
        lines.append(asp.fact("helper", c))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, q, c) for p in PLACEs for q in QUESTS for c in CREWS}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style zebra quest in a parking lot.")
    ap.add_argument("--place", choices=PLACEs.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--crew", choices=CREWS.keys())
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACEs))
    quest = args.quest or rng.choice(list(QUESTS))
    crew = args.crew or rng.choice(list(CREWS))
    trait = args.trait or rng.choice(TRAITS)

    if args.name:
        name = args.name
    else:
        name = rng.choice(ZEBRA_NAMES)

    return StoryParams(place=place, quest=quest, crew=crew, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="parking_lot", quest="lost_map", crew="parrot", name="Zuri", trait="brave"),
    StoryParams(place="parking_lot", quest="shell_key", crew="mouse", name="Nala", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 50:
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
