#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py
=================================================================

A small storyworld for gentle child-facing mysteries told with inner monologue.
A child notices that a cherished little object is missing, studies one concrete
clue, and solves the mystery in a sensible way. A calm helper is nearby, and an
apparently indifferent animal or little witness adds a mystery-story feeling
without becoming a villain.

The reasonableness gate is simple and strict:

* a place must actually allow the chosen cause
* an item must be the sort of thing that cause could move or take
* the chosen method must fit the cause

That keeps the world narrow enough to produce complete stories instead of loose,
generic detective scenes.

Run it
------
    python storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py
    python storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py --all
    python storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/indifferent_inner_monologue_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    afford_causes: set[str] = field(default_factory=set)
    witness: str = ""
    witness_phrase: str = ""
    witness_trait: str = "still"


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    cherished: str
    tags: set[str] = field(default_factory=set)
    hide_spot: dict[str, str] = field(default_factory=dict)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    clue_detail: str
    find_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    thought: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_missing_makes_mystery(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    room = world.get("room")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    return []


def _r_clue_draws_focus(world: World) -> list[str]:
    hero = world.get("hero")
    room = world.get("room")
    if room.meters["clue"] < THRESHOLD:
        return []
    sig = ("focus", "clue")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["focus"] += 1
    return []


def _r_right_method_finds_item(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    room = world.get("room")
    needed = world.facts.get("cause_id")
    chosen = world.facts.get("method_for")
    if item.meters["missing"] < THRESHOLD:
        return []
    if room.meters["clue"] < THRESHOLD or hero.meters["searching"] < THRESHOLD:
        return []
    if chosen != needed:
        return []
    sig = ("found", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    room.meters["mystery"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    return []


RULES = [
    Rule(name="missing_makes_mystery", apply=_r_missing_makes_mystery),
    Rule(name="clue_draws_focus", apply=_r_clue_draws_focus),
    Rule(name="right_method_finds_item", apply=_r_right_method_finds_item),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = (dict(world.get("room").meters), dict(world.get("hero").memes), dict(world.get("item").meters))
            rule.apply(world)
            after = (dict(world.get("room").meters), dict(world.get("hero").memes), dict(world.get("item").meters))
            if after != before:
                changed = True


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        scene="The kitchen was bright except for the shady strip under the table.",
        afford_causes={"wind", "puppy", "sibling"},
        witness="cat",
        witness_phrase="On the windowsill, the cat blinked once and looked indifferent.",
        witness_trait="indifferent",
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        scene="The back porch smelled like rain and old flowerpots.",
        afford_causes={"wind", "puppy"},
        witness="sparrow",
        witness_phrase="A sparrow on the railing hopped once, then seemed almost indifferent to the whole fuss.",
        witness_trait="indifferent",
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        scene="The playroom had soft rugs, a low shelf, and a lamp that made round pools of light.",
        afford_causes={"puppy", "sibling"},
        witness="turtle",
        witness_phrase="In the corner, the little turtle looked completely indifferent inside its glass tank.",
        witness_trait="indifferent",
    ),
}

ITEMS = {
    "recipe_card": MissingItem(
        id="recipe_card",
        label="recipe card",
        phrase="a recipe card with a jam stain in one corner",
        cherished="it held the cookie directions that always made the house smell sweet",
        tags={"light", "flat", "paper", "colorful"},
        hide_spot={
            "wind": "behind the bread box",
            "puppy": "under the cushion by the basket",
            "sibling": "tucked into a doll blanket beside the toy stove",
        },
    ),
    "seed_packet": MissingItem(
        id="seed_packet",
        label="seed packet",
        phrase="a sunflower seed packet with a bright yellow face on the front",
        cherished="it was the packet for the tallest flowers in the garden",
        tags={"light", "flat", "paper", "colorful"},
        hide_spot={
            "wind": "behind the watering can",
            "puppy": "under the porch bench",
            "sibling": "inside a toy wagon with three crayons",
        },
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon with a silver star stitched on the end",
        cherished="it was the ribbon the hero liked to tie around special boxes",
        tags={"light", "soft", "chewable", "colorful"},
        hide_spot={
            "wind": "behind a stack of bowls",
            "puppy": "inside the puppy's blanket nest",
            "sibling": "wrapped around a stuffed bear in the reading corner",
        },
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="a sneaky breeze",
        clue="flutter",
        clue_detail="A corner of the curtain kept lifting, and a dry paper whisper came from somewhere behind a heavier thing.",
        find_text="The clue pointed to a draft, not a thief.",
        tags={"wind", "air", "look_behind"},
    ),
    "puppy": Cause(
        id="puppy",
        label="the puppy",
        clue="pawprints",
        clue_detail="Tiny muddy pawprints crossed the floor and ended beside a snug hiding place.",
        find_text="The clue pointed to playful paws, not a bad plan.",
        tags={"puppy", "pawprints", "follow_tracks"},
    ),
    "sibling": Cause(
        id="sibling",
        label="the little sibling",
        clue="crayon",
        clue_detail="A waxy crayon loop ran along the floor, and a soft humming came from the place where toys gathered.",
        find_text="The clue pointed to make-believe, not meanness.",
        tags={"sibling", "crayon", "ask_kindly"},
    ),
}

METHODS = {
    "check_breezy_corners": Method(
        id="check_breezy_corners",
        label="check breezy corners",
        action="followed the moving curtain and looked behind the heavier things the breeze could not push",
        thought='I should look where a breeze could slide something, the hero thought.',
        tags={"wind"},
    ),
    "follow_pawprints": Method(
        id="follow_pawprints",
        label="follow pawprints",
        action="knelt down and followed the little pawprints all the way to their ending place",
        thought='Paws leave a path, the hero thought. Paths can answer questions.',
        tags={"puppy"},
    ),
    "ask_small_artist": Method(
        id="ask_small_artist",
        label="ask the small artist kindly",
        action="sat beside the toys and asked gentle questions instead of scolding",
        thought='If this was part of a game, I need kind words, not a loud voice, the hero thought.',
        tags={"sibling"},
    ),
}


def item_allows_cause(item: MissingItem, cause_id: str) -> bool:
    if cause_id == "wind":
        return "light" in item.tags
    if cause_id == "puppy":
        return "soft" in item.tags or "chewable" in item.tags or "paper" in item.tags
    if cause_id == "sibling":
        return "colorful" in item.tags
    return False


def method_fits_cause(method: Method, cause_id: str) -> bool:
    return cause_id in method.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for cause_id in place.afford_causes:
                if not item_allows_cause(item, cause_id):
                    continue
                for method_id, method in METHODS.items():
                    if method_fits_cause(method, cause_id):
                        combos.append((place_id, item_id, cause_id, method_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    item: str
    cause: str
    method: str
    name: str
    gender: str
    helper: str
    helper_type: str
    mood: str
    seed: Optional[int] = None


NAME_POOLS = {
    "girl": ["Lina", "Maya", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Ivy"],
    "boy": ["Owen", "Leo", "Ben", "Max", "Finn", "Theo", "Eli", "Sam"],
}
HELPERS = [
    {"name": "Mom", "type": "mother"},
    {"name": "Dad", "type": "father"},
    {"name": "Aunt June", "type": "aunt"},
    {"name": "Uncle Ray", "type": "uncle"},
]
MOODS = ["quiet", "careful", "curious", "steady", "thoughtful"]


def explain_rejection(place_id: str, item_id: str, cause_id: str, method_id: str) -> str:
    parts: list[str] = []
    place = PLACES[place_id]
    item = ITEMS[item_id]
    method = METHODS[method_id]
    if cause_id not in place.afford_causes:
        parts.append(f"{place.label.capitalize()} does not support the cause '{cause_id}'")
    if not item_allows_cause(item, cause_id):
        parts.append(f"{item.label} is not a sensible match for the cause '{cause_id}'")
    if not method_fits_cause(method, cause_id):
        parts.append(f"the method '{method.label}' does not fit the cause '{cause_id}'")
    if not parts:
        parts.append("that combination is outside this story world's mystery logic")
    return "(No story: " + "; ".join(parts) + ".)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle mystery storyworld with inner monologue. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_helper(raw: Optional[str], rng: random.Random) -> tuple[str, str]:
    if raw is None:
        choice = rng.choice(HELPERS)
        return choice["name"], choice["type"]
    for entry in HELPERS:
        if raw == entry["name"]:
            return entry["name"], entry["type"]
    raise StoryError(f"(No story: unknown helper '{raw}'.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.cause and args.method:
        if (args.place, args.item, args.cause, args.method) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.place, args.item, args.cause, args.method))

    possible = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.method is None or combo[3] == args.method)
    ]
    if not possible:
        if args.place and args.item and args.cause and args.method:
            raise StoryError(explain_rejection(args.place, args.item, args.cause, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, cause_id, method_id = rng.choice(sorted(possible))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAME_POOLS[gender])
    helper_name, helper_type = resolve_helper(args.helper, rng)
    mood = rng.choice(MOODS)
    return StoryParams(
        place=place_id,
        item=item_id,
        cause=cause_id,
        method=method_id,
        name=name,
        gender=gender,
        helper=helper_name,
        helper_type=helper_type,
        mood=mood,
    )


def inner(world: World, text: str) -> None:
    hero = world.get("hero")
    hero.memes["thinking"] += 1
    world.say(f'"{text}" {hero.pronoun()} thought.')


def introduce(world: World, hero: Entity, helper: Entity, item: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"{hero.id} was a {hero.attrs['mood']} little {hero.type} who liked to notice small things."
    )
    world.say(
        f"That afternoon, {hero.id} was with {helper.id} in {world.place.label}. {world.place.scene}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} had brought {item_cfg.phrase}, and {item_cfg.cherished}."
    )


def vanish(world: World, hero: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world)
    world.say(
        f"But when {hero.id} reached for the {item.label} again, it was gone."
    )
    inner(world, "That was strange. Things do not simply walk away by themselves")
    world.say(world.place.witness_phrase)


def clue_appears(world: World, cause: Cause) -> None:
    room = world.get("room")
    room.meters["clue"] += 1
    propagate(world)
    world.say(cause.clue_detail)
    inner(world, "A mystery always starts to shrink when a clue stops being just a clue and starts being a direction")


def helper_response(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["supported"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} did not laugh or hurry {hero.pronoun("object")}. "{hero.id}," {helper.id} said softly, '
        f'"look carefully first. The room is telling a story."'
    )


def search(world: World, hero: Entity, method: Method, cause_id: str) -> None:
    hero.meters["searching"] += 1
    world.facts["method_for"] = cause_id if method_fits_cause(method, cause_id) else ""
    world.say(method.thought)
    world.say(
        f"So {hero.id} {method.action}."
    )
    propagate(world)


def find_item(world: World, item_cfg: MissingItem, cause: Cause) -> None:
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["found"] < THRESHOLD:
        raise StoryError("(Story failed: the search did not find the missing item.)")
    spot = item_cfg.hide_spot[cause.id]
    world.say(cause.find_text)
    world.say(
        f"There, {hero.id} found the {item.label} {spot}."
    )
    inner(world, "So that was it. The mystery was not mean at all. It was only waiting to be understood")


def ending(world: World, helper: Entity, hero: Entity, item: Entity, cause: Cause) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} held the {item.label} against {hero.pronoun('possessive')} chest and smiled."
    )
    if cause.id == "wind":
        world.say(
            f'{helper.id} closed the window a little. "Even a small breeze can play tricks," {helper.pronoun()} said.'
        )
    elif cause.id == "puppy":
        world.say(
            f'{helper.id} scratched the puppy behind the ears. "Playful does not mean naughty," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.id} smiled toward the toy corner. "Sometimes little games borrow big things," {helper.pronoun()} said.'
        )
    world.say(
        f"The room no longer felt full of mystery. It felt warm, ordinary, and solved."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.item not in ITEMS or params.cause not in CAUSES or params.method not in METHODS:
        raise StoryError("(No story: one or more parameter values are not in this world's registries.)")

    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]

    if (params.place, params.item, params.cause, params.method) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.item, params.cause, params.method))

    world = World(place=place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        role="hero",
        attrs={"mood": params.mood},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        label=params.helper,
        role="helper",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        tags=set(item_cfg.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=place.label,
    ))
    witness = world.add(Entity(
        id="witness",
        kind="thing",
        type=place.witness,
        label=place.witness,
        role="witness",
        attrs={"trait": place.witness_trait},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        room=room,
        witness=witness,
        place=place,
        item_cfg=item_cfg,
        cause=cause,
        cause_id=cause.id,
        method=method,
        solved=False,
    )

    introduce(world, hero, helper, item, item_cfg)
    world.para()
    vanish(world, hero, item)
    clue_appears(world, cause)
    helper_response(world, helper, hero)
    world.para()
    search(world, hero, method, cause.id)
    find_item(world, item_cfg, cause)
    world.para()
    ending(world, helper, hero, item, cause)

    world.facts["solved"] = item.meters["found"] >= THRESHOLD
    world.facts["hide_spot"] = item_cfg.hide_spot[cause.id]
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    item_cfg = world.facts["item_cfg"]
    place = world.facts["place"]
    cause = world.facts["cause"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the word "indifferent" and uses inner monologue.',
        f"Tell a gentle mystery about a {hero.type} named {hero.id} in {place.label} who notices that {item_cfg.phrase} is missing and solves it by following a real clue.",
        f"Write a child-facing mystery where the true cause is {cause.label}, not a villain, and the ending shows the room feeling safe again after the answer is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    place = world.facts["place"]
    cause = world.facts["cause"]
    method = world.facts["method"]
    hide_spot = world.facts["hide_spot"]
    witness = world.facts["witness"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who noticed that a special {item.label} was missing in {place.label}. {helper.id} stayed calm nearby and helped {hero.pronoun('object')} think carefully.",
        ),
        (
            f"What made the story feel like a mystery?",
            f"The {item.label} vanished, and then a real clue appeared in the room. {hero.id} also kept thinking quietly to {hero.pronoun('object')}self, which made the mystery feel close and careful.",
        ),
        (
            f"Who seemed indifferent?",
            f"The {witness.label} seemed indifferent while {hero.id} was worried about the missing {item.label}. That made the room feel even stranger, because one creature was calm while {hero.id} was full of questions.",
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} noticed the clue and then chose to {method.label}. That worked because the clue matched the real cause, which was {cause.label}.",
        ),
        (
            f"Where was the missing {item.label}?",
            f"The missing {item.label} was {hide_spot}. It turned up there because the true cause was {cause.label}, not a thief or a mean trick.",
        ),
        (
            "How did the story end?",
            f"It ended with the {item.label} back in {hero.id}'s hands and the room feeling solved instead of strange. The answer changed {hero.pronoun('possessive')} worry into relief.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "wind": [
        (
            "How can wind move light things indoors?",
            "A breeze can slide under paper or ribbon and push it along little by little. Light things may end up behind heavier objects without anyone noticing right away.",
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies explore with their mouths and paws, so they often carry soft or interesting things during play. That does not mean they are being mean; it usually means they are curious.",
        )
    ],
    "sibling": [
        (
            "Why might a little sibling take an object into a game?",
            "Small children often pull nearby things into pretend play because they look bright or special. They may not realize someone else is searching for that object at the same time.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a question that does not have an answer yet. You solve it by noticing clues and thinking carefully about what those clues mean.",
        )
    ],
    "inner": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet voice of a person's thoughts. In a story, it lets you hear what a character is wondering without anyone speaking out loud.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that points toward an answer. Good clues help you look in the right place or understand what really happened.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "inner", "clue", "wind", "puppy", "sibling"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause"]
    tags = {"mystery", "inner", "clue", cause.id}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        item="recipe_card",
        cause="wind",
        method="check_breezy_corners",
        name="Maya",
        gender="girl",
        helper="Mom",
        helper_type="mother",
        mood="thoughtful",
    ),
    StoryParams(
        place="porch",
        item="seed_packet",
        cause="puppy",
        method="follow_pawprints",
        name="Leo",
        gender="boy",
        helper="Dad",
        helper_type="father",
        mood="careful",
    ),
    StoryParams(
        place="playroom",
        item="ribbon",
        cause="sibling",
        method="ask_small_artist",
        name="Ivy",
        gender="girl",
        helper="Aunt June",
        helper_type="aunt",
        mood="quiet",
    ),
]


ASP_RULES = r"""
item_allows(I, wind)    :- item(I), tagged(I, light).
item_allows(I, puppy)   :- item(I), tagged(I, soft).
item_allows(I, puppy)   :- item(I), tagged(I, chewable).
item_allows(I, puppy)   :- item(I), tagged(I, paper).
item_allows(I, sibling) :- item(I), tagged(I, colorful).

method_fits(M, C) :- method(M), method_tag(M, C).

valid(P, I, C, M) :- place(P), item(I), cause(C), method(M),
                     allows(P, C), item_allows(I, C), method_fits(M, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.afford_causes):
            lines.append(asp.fact("allows", place_id, cause_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("tagged", item_id, tag))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for tag in sorted(method.tags):
            lines.append(asp.fact("method_tag", method_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed on seed {seed}: {err}")
            break

    for idx, params in enumerate(smoke_cases):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "{" in sample.story or "}" in sample.story:
                raise StoryError("unresolved template braces in story")
            if "indifferent" not in sample.story:
                raise StoryError('required seed word "indifferent" missing from story')
            _ = sample.to_dict()
        except Exception as err:
            rc = 1
            print(f"SMOKE generate failed on case {idx}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, cause, method) combos:\n")
        for place_id, item_id, cause_id, method_id in combos:
            print(f"  {place_id:9} {item_id:12} {cause_id:8} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} in {p.place} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
