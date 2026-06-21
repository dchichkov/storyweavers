#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py
====================================================================================================

A standalone storyworld for a tiny child-facing detective tale: one child thinks
a friend may have taken a missing thing, investigates a few grounded clues,
discovers a simple misunderstanding, and ends the day with friendship repaired.

Seed constraints rebuilt as world state
---------------------------------------
Words: investigate, leather
Features: Happy Ending, Misunderstanding, Friendship
Style: Detective Story

The world model tracks:
- typed entities with physical ``meters`` and emotional ``memes``
- a small causal chain: missing item -> worry -> suspicion -> clue-following ->
  find object -> apology -> repaired friendship
- a reasonableness gate: only objects that can plausibly be misplaced in a place,
  and only clue routes that can plausibly lead to a find, are allowed
- an inline ASP twin for the valid-combo gate and the simple outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py
    python storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py --all
    python storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py --qa
    python storyworlds/worlds/gpt-5.4/investigate_leather_happy_ending_misunderstanding_friendship_detective.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    # physical
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional / social
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    object_types: set[str] = field(default_factory=set)
    clue_spots: set[str] = field(default_factory=set)
    mood: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    type: str
    material: str = ""
    clue_mark: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueSpot:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    found_at: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    role_word: str
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if hero is None or item is None:
        return out
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing_worry", hero.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_friend_suspicion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.meters["saw_friend_near"] < THRESHOLD or hero.memes["worry"] < THRESHOLD:
        return out
    sig = ("friend_suspicion", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    friend.memes["hurt"] += 1
    out.append("__suspicion__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    item = world.entities.get("item")
    if hero is None or friend is None or item is None:
        return out
    if item.meters["found"] < THRESHOLD:
        return out
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["suspicion"] = 0.0
    friend.memes["hope"] += 1
    out.append("__found__")
    return out


def _r_apology_repairs(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiven"] < THRESHOLD:
        return out
    sig = ("repair", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="friend_suspicion", tag="emotion", apply=_r_friend_suspicion),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="library",
        phrase="the little library corner by the classroom windows",
        object_types={"notebook", "pouch"},
        clue_spots={"reading_rug", "book_cart"},
        mood="The room was so quiet that every tiny scrape sounded important.",
        tags={"library", "quiet"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="clubhouse",
        phrase="the backyard clubhouse with a wobbling table and a secret map on the wall",
        object_types={"notebook", "case", "magnifier"},
        clue_spots={"crate", "coat_hook"},
        mood="The clubhouse smelled of wood, crayons, and old adventures.",
        tags={"clubhouse", "hideout"},
    ),
    "art_room": Place(
        id="art_room",
        label="art room",
        phrase="the sunny art room with long tables and jars of colored pencils",
        object_types={"pouch", "case"},
        clue_spots={"paint_shelf", "window_sill"},
        mood="Sunlight lay across the tables like bright detective lamps.",
        tags={"art", "school"},
    ),
}

ITEMS = {
    "notebook": MissingItem(
        id="notebook",
        label="notebook",
        phrase="a little leather notebook with a snap",
        type="notebook",
        material="leather",
        clue_mark="a bent paper corner",
        tags={"leather", "notebook"},
    ),
    "pouch": MissingItem(
        id="pouch",
        label="pencil pouch",
        phrase="a brown leather pencil pouch with a brass zipper",
        type="pouch",
        material="leather",
        clue_mark="a blue chalk smudge",
        tags={"leather", "pouch"},
    ),
    "case": MissingItem(
        id="case",
        label="magnifying-glass case",
        phrase="a tiny leather case for a play magnifying glass",
        type="case",
        material="leather",
        clue_mark="a loose strap",
        tags={"leather", "detective"},
    ),
    "magnifier": MissingItem(
        id="magnifier",
        label="magnifying glass",
        phrase="a play magnifying glass in a leather loop",
        type="magnifier",
        material="leather",
        clue_mark="a dusty ring on the table",
        tags={"leather", "detective"},
    ),
}

CLUE_SPOTS = {
    "reading_rug": ClueSpot(
        id="reading_rug",
        label="reading rug",
        phrase="the reading rug by the window",
        reveals={"notebook", "pouch"},
        found_at="window_sill",
        tags={"rug", "library"},
    ),
    "book_cart": ClueSpot(
        id="book_cart",
        label="book cart",
        phrase="the squeaky book cart",
        reveals={"notebook", "pouch"},
        found_at="book_cart",
        tags={"books", "wheels"},
    ),
    "crate": ClueSpot(
        id="crate",
        label="supply crate",
        phrase="the old supply crate under the clubhouse table",
        reveals={"notebook", "case", "magnifier"},
        found_at="crate",
        tags={"crate", "clubhouse"},
    ),
    "coat_hook": ClueSpot(
        id="coat_hook",
        label="coat hook",
        phrase="the coat hook beside the door",
        reveals={"case", "magnifier"},
        found_at="coat_hook",
        tags={"hook", "door"},
    ),
    "paint_shelf": ClueSpot(
        id="paint_shelf",
        label="paint shelf",
        phrase="the paint shelf where the paper cups dried",
        reveals={"pouch", "case"},
        found_at="paint_shelf",
        tags={"paint", "shelf"},
    ),
    "window_sill": ClueSpot(
        id="window_sill",
        label="window sill",
        phrase="the wide window sill above the radiators",
        reveals={"pouch", "case"},
        found_at="window_sill",
        tags={"window", "light"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        label="teacher",
        type="mother",
        role_word="teacher",
        method="remembered seeing something carefully moved out of the way during cleanup",
        tags={"adult", "school"},
    ),
    "librarian": Helper(
        id="librarian",
        label="librarian",
        type="father",
        role_word="librarian",
        method="noticed a clue where books had been stacked in a hurry",
        tags={"adult", "books"},
    ),
    "big_sister": Helper(
        id="big_sister",
        label="big sister",
        type="girl",
        role_word="big sister",
        method="knelt down and checked the room from the height of dropped things",
        tags={"family", "helper"},
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    clue_spot: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "bright", "patient", "thoughtful", "quick-eyed"]

CURATED = [
    StoryParams(
        place="clubhouse",
        item="notebook",
        clue_spot="crate",
        helper="big_sister",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="library",
        item="pouch",
        clue_spot="reading_rug",
        helper="librarian",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        trait="patient",
    ),
    StoryParams(
        place="art_room",
        item="case",
        clue_spot="paint_shelf",
        helper="teacher",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        trait="bright",
    ),
    StoryParams(
        place="clubhouse",
        item="magnifier",
        clue_spot="coat_hook",
        helper="big_sister",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        trait="quick-eyed",
    ),
]


def valid_combo(place_id: str, item_id: str, clue_spot_id: str) -> bool:
    if place_id not in PLACES or item_id not in ITEMS or clue_spot_id not in CLUE_SPOTS:
        return False
    place = PLACES[place_id]
    item = ITEMS[item_id]
    clue = CLUE_SPOTS[clue_spot_id]
    return item.type in place.object_types and clue_spot_id in place.clue_spots and item.type in clue.reveals


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for clue_id in sorted(CLUE_SPOTS):
                if valid_combo(place_id, item_id, clue_id):
                    out.append((place_id, item_id, clue_id))
    return out


def explain_rejection(place_id: str, item_id: str, clue_spot_id: str) -> str:
    place = PLACES.get(place_id)
    item = ITEMS.get(item_id)
    clue = CLUE_SPOTS.get(clue_spot_id)
    if place is None or item is None or clue is None:
        return "(No story: one of the requested options is unknown.)"
    if item.type not in place.object_types:
        return (
            f"(No story: {item.phrase} does not fit naturally in {place.phrase}, "
            f"so the missing-object problem would feel forced there.)"
        )
    if clue_spot_id not in place.clue_spots:
        return (
            f"(No story: {clue.phrase} is not a clue place in {place.phrase}, "
            f"so the investigation would not have a grounded path.)"
        )
    return (
        f"(No story: {clue.phrase} would not reasonably lead to {item.phrase}. "
        f"Pick a clue spot that matches the item and place.)"
    )


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.place, params.item, params.clue_spot):
        return "invalid"
    return "repaired_friendship"


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def introduce(world: World, hero: Entity, friend: Entity, place: Place, item: MissingItem) -> None:
    world.say(
        f"{hero.id} loved detective stories, so when {hero.pronoun()} and {friend.id} "
        f"met in {place.phrase}, {hero.pronoun()} liked to call the morning their newest case."
    )
    world.say(place.mood)
    world.say(
        f"In {hero.pronoun('possessive')} pocket, {hero.pronoun()} carried {item.phrase}. "
        f"{hero.pronoun().capitalize()} used it to write clues and circle suspects, though only in pretend games."
    )


def lose_item(world: World, hero: Entity, item_ent: Entity, place: Place) -> None:
    item_ent.meters["missing"] += 1
    hero.meters["saw_friend_near"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the game began, {hero.id} reached for the {item_ent.label} and felt only an empty pocket."
    )
    world.say(
        f'"Case of the Missing {item_ent.label.title()}," {hero.pronoun()} whispered. '
        f'Then {hero.pronoun()} remembered that {friend_name_for(world)} had been standing nearby a moment before.'
    )


def friend_name_for(world: World) -> str:
    friend = world.entities.get("friend")
    return friend.id if friend is not None else "the friend"


def suspect_friend(world: World, hero: Entity, friend: Entity, item: MissingItem) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{hero.id}'s detective heart beat fast, but not in a happy way. "
        f"Because {hero.pronoun()} was worried, a wrong idea slipped in: maybe {friend.id} had picked the {item.label} up and forgotten to say so."
    )
    world.say(
        f'"Did you take my {item.label}?" {hero.id} asked. '
        f'{friend.id} blinked and shook {friend.pronoun("possessive")} head at once.'
    )


def hurt_response(world: World, friend: Entity) -> None:
    world.say(
        f'"No," {friend.id} said softly. "I would help you look for it." '
        f'The answer was gentle, but {friend.pronoun("possessive")} face still looked hurt.'
    )


def choose_to_investigate(world: World, hero: Entity, clue: ClueSpot) -> None:
    hero.memes["care"] += 1
    world.say(
        f"That made {hero.id} stop. A good detective should investigate before deciding anything."
    )
    world.say(
        f"So {hero.pronoun()} crouched low, searched around {clue.phrase}, and looked for the smallest sign."
    )


def find_clue(world: World, hero: Entity, item: MissingItem, clue: ClueSpot) -> None:
    hero.meters["clue_found"] += 1
    world.say(
        f"There it was: {item.clue_mark} near {clue.phrase}. It did not look like stealing at all. It looked like the {item.label} had slipped, bumped, and been set aside."
    )


def helper_joins(world: World, helper_ent: Entity, helper: Helper) -> None:
    helper_ent.memes["helpfulness"] += 1
    world.say(
        f"Just then, the {helper.role_word} came by and {helper.method}."
    )


def locate_item(world: World, hero: Entity, friend: Entity, item_ent: Entity, clue: ClueSpot) -> None:
    item_ent.meters["found"] += 1
    item_ent.attrs["found_at"] = clue.found_at
    propagate(world, narrate=False)
    found_phrase = clue.phrase if clue.id == clue.found_at else CLUE_SPOTS[clue.found_at].phrase
    world.say(
        f'Together they followed the clue, and there, waiting in {found_phrase}, was the missing {item_ent.label}.'
    )
    world.say(
        f"Someone had moved it to keep it safe after it fell. The whole mystery had been a misunderstanding."
    )


def apologize(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1
    friend.memes["forgiven"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} picked it up and looked at {friend.id}. "I am sorry," {hero.pronoun()} said. '
        f'"I guessed before I knew. You were trying to help."'
    )
    world.say(
        f'{friend.id} smiled a little. "It is okay," {friend.pronoun()} said. '
        f'"Next time we can solve the case together."'
    )


def repaired_end(world: World, hero: Entity, friend: Entity, item: MissingItem) -> None:
    world.say(
        f"That answer warmed the room faster than sunshine. Soon the two friends were side by side again, using the {item.label} to sketch a fresh list of clues for a brand-new pretend case."
    )
    world.say(
        f"This time, when {hero.id} said they should investigate, {friend.id} grinned. "
        f"Their friendship felt stronger because they had told the truth, listened, and mended the mistake together."
    )


def tell(
    place: Place,
    item: MissingItem,
    clue: ClueSpot,
    helper: Helper,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        traits=[trait],
        role="hero",
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        traits=["kind"],
        role="friend",
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type,
        label=helper.label,
        role="helper",
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type=item.type,
        label=item.label,
        phrase=item.phrase,
        role="missing_item",
        portable=True,
        tags=set(item.tags),
    ))

    introduce(world, hero, friend, place, item)
    world.para()
    lose_item(world, hero, item_ent, place)
    suspect_friend(world, hero, friend, item)
    hurt_response(world, friend)
    world.para()
    choose_to_investigate(world, hero, clue)
    find_clue(world, hero, item, clue)
    helper_joins(world, helper_ent, helper)
    locate_item(world, hero, friend, item_ent, clue)
    world.para()
    apologize(world, hero, friend)
    repaired_end(world, hero, friend, item)

    world.facts.update(
        place=place,
        item_cfg=item,
        clue=clue,
        helper_cfg=helper,
        hero=hero,
        friend=friend,
        helper=helper_ent,
        item=item_ent,
        misunderstood=friend.memes["hurt"] >= THRESHOLD,
        found=item_ent.meters["found"] >= THRESHOLD,
        friendship_repaired=hero.memes["friendship"] >= THRESHOLD and friend.memes["friendship"] >= THRESHOLD,
        found_at=item_ent.attrs.get("found_at", clue.found_at),
        outcome="repaired_friendship",
    )
    return world


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues and tries to understand what really happened. A good detective does not guess too fast."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone believes the wrong thing about what happened. Talking and checking the facts can fix it."
    )],
    "friendship": [(
        "How can friends fix a mistake?",
        "Friends can tell the truth, listen, and say sorry when they were unfair. That helps trust grow again."
    )],
    "leather": [(
        "What is leather?",
        "Leather is a strong material made from animal skin. It can feel smooth and sturdy, so people use it for things like bags, belts, and covers."
    )],
    "library": [(
        "Why is a library a good place to look for clues?",
        "A library is full of shelves, carts, and quiet corners where things can be set down carefully. That means a missing object may be nearby, not gone forever."
    )],
    "clubhouse": [(
        "Why do children like pretending a clubhouse is a detective office?",
        "A clubhouse can feel secret and special, which makes pretend cases exciting. Small corners and boxes also make good hiding places for lost things."
    )],
    "art": [(
        "Why do objects get moved in an art room?",
        "In an art room, people tidy tables and save materials from spills. A grown-up may move something to a safer spot during cleanup."
    )],
    "apology": [(
        "Why is saying sorry important after a wrong guess?",
        "Saying sorry shows that you know your guess hurt someone. It helps repair trust after a misunderstanding."
    )],
}
KNOWLEDGE_ORDER = ["detective", "misunderstanding", "friendship", "leather", "library", "clubhouse", "art", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    place = f["place"]
    return [
        f'Write a child-friendly detective story that includes the words "investigate" and "{item.material}".',
        f"Tell a gentle mystery where {hero.id} thinks {friend.id} took {item.phrase}, but the real answer is a misunderstanding in {place.phrase}.",
        "Write a short story about friendship where a child follows clues, learns not to blame too quickly, and ends with a happy solved case.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    clue = f["clue"]
    helper = f["helper_cfg"]
    found_at = f["found_at"]
    found_phrase = clue.phrase if clue.id == found_at else CLUE_SPOTS[found_at].phrase
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two friends playing at being detectives. The mystery begins when {hero.id} cannot find {item.phrase}."
        ),
        (
            f"Why did {hero.id} think {friend.id} had taken the {item.label}?",
            f"{hero.id} noticed the {item.label} was missing and remembered {friend.id} standing nearby. Because {hero.pronoun()} was worried, {hero.pronoun()} guessed too fast and turned worry into suspicion."
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {item.clue_mark} near {clue.phrase}. That sign suggested the {item.label} had slipped or been moved, not stolen."
        ),
        (
            f"How did the {helper.role_word} help?",
            f"The {helper.role_word} helped by joining the search and noticing the room carefully. That calm help pushed the children toward the real answer instead of the wrong guess."
        ),
        (
            f"Where was the missing {item.label}?",
            f"It was in {found_phrase}. Someone had set it there to keep it safe after it fell."
        ),
        (
            "Why was it a misunderstanding?",
            f"It was a misunderstanding because {friend.id} had not taken anything. {hero.id} only thought that because the {item.label} was gone and worry made the wrong idea seem true."
        ),
        (
            "How did the story end?",
            f"{hero.id} said sorry, and {friend.id} forgave {hero.pronoun('object')}. Then they used the found {item.label} together, which showed their friendship was repaired."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "misunderstanding", "friendship", "leather", "apology"}
    place = world.facts["place"]
    if place.id == "library":
        tags.add("library")
    elif place.id == "clubhouse":
        tags.add("clubhouse")
    elif place.id == "art_room":
        tags.add("art")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
item_fits(P, I) :- place_item(P, T), item_type(I, T).
clue_works(P, C) :- place_clue(P, C).
clue_matches(I, C) :- item_type(I, T), clue_reveals(C, T).
valid(P, I, C) :- item_fits(P, I), clue_works(P, C), clue_matches(I, C).

outcome(repaired_friendship) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for item_type in sorted(place.object_types):
            lines.append(asp.fact("place_item", place_id, item_type))
        for clue_id in sorted(place.clue_spots):
            lines.append(asp.fact("place_clue", place_id, clue_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_type", item_id, item.type))
    for clue_id, clue in CLUE_SPOTS.items():
        lines.append(asp.fact("clue", clue_id))
        for item_type in sorted(clue.reveals):
            lines.append(asp.fact("clue_reveals", clue_id, item_type))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_clue", params.clue_spot),
        "valid(_, _, _) :- valid(chosen_place, chosen_item, chosen_clue).",
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_val}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a missing leather object, a detective-style misunderstanding, and a repaired friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue-spot", choices=CLUE_SPOTS, dest="clue_spot")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"], dest="hero_gender")
    ap.add_argument("--friend-gender", choices=["girl", "boy"], dest="friend_gender")
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--friend-name", dest="friend_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.clue_spot and not valid_combo(args.place, args.item, args.clue_spot):
        raise StoryError(explain_rejection(args.place, args.item, args.clue_spot))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.clue_spot is None or combo[2] == args.clue_spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, clue_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        item=item_id,
        clue_spot=clue_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue_spot not in CLUE_SPOTS:
        raise StoryError(f"(Unknown clue spot: {params.clue_spot})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(params.place, params.item, params.clue_spot):
        raise StoryError(explain_rejection(params.place, params.item, params.clue_spot))

    world = tell(
        place=PLACES[params.place],
        item=ITEMS[params.item],
        clue=CLUE_SPOTS[params.clue_spot],
        helper=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, clue_spot) combos:\n")
        for place_id, item_id, clue_id in combos:
            print(f"  {place_id:10} {item_id:10} {clue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} investigates a missing {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
