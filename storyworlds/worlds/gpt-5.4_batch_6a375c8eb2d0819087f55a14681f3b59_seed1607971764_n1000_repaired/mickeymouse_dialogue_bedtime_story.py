#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py
================================================================

A standalone storyworld for a gentle bedtime tale with dialogue: a child cannot
find a beloved comfort item, worries that sleep will not come, and a calm
grown-up helps search in a sensible way until the room feels cozy again.

The seed asked for the word "mickeymouse", dialogue, and a bedtime-story feel.
This world centers those elements while still being a small classical simulation:
typed entities carry physical meters and emotional memes, the story is driven by
state changes, and a reasonableness gate only allows search plans that fit both
the hidden place and the kind of lost object.

Examples
--------
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py --item mickeymouse_plush
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py --place bookshelf
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py --method flashlight_peek
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/mickeymouse_dialogue_bedtime_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    type: str
    bedtime_use: str
    sleepy_image: str
    kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    clue: str
    reach: str
    properties: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    sense: int = 2
    action: str = ""
    found_line: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "bedtime": True,
            "search_started": False,
            "found": False,
            "predicted_soothe": False,
        }

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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_missing_worry(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    room = world.get("room")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["lonely"] += 1
    room.memes["hush"] += 1
    return ["__missing__"]


def _r_search_hope(world: World) -> list[str]:
    if not world.facts.get("search_started"):
        return []
    child = world.get("child")
    sig = ("search_hope", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    room = world.get("room")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    child.memes["sleepy"] += 1
    room.meters["cozy"] += 1
    world.facts["found"] = True
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="search_hope", tag="emotional", apply=_r_search_hope),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


COMFORT_ITEMS = {
    "mickeymouse_plush": ComfortItem(
        id="mickeymouse_plush",
        label="mickeymouse plush",
        phrase="a soft mickeymouse plush with round black ears",
        type="plush",
        bedtime_use="to tuck the plush under one arm",
        sleepy_image="the little plush rested under the child's chin",
        kinds={"plush"},
        tags={"plush", "bedtime"},
    ),
    "moon_blanket": ComfortItem(
        id="moon_blanket",
        label="moon blanket",
        phrase="a moon blanket with tiny silver stars",
        type="blanket",
        bedtime_use="to pull the blanket up to the child's shoulders",
        sleepy_image="the blanket made a warm hill of stars over the bed",
        kinds={"blanket"},
        tags={"blanket", "bedtime"},
    ),
    "bunny_book": ComfortItem(
        id="bunny_book",
        label="bunny book",
        phrase="a small bunny book with thick sleepy pages",
        type="book",
        bedtime_use="to keep the book beside the pillow for one last look at the pictures",
        sleepy_image="the closed book waited beside the pillow like a quiet friend",
        kinds={"book"},
        tags={"book", "bedtime"},
    ),
}

PLACES = {
    "under_bed": Place(
        id="under_bed",
        label="under the bed",
        phrase="under the bed where the shadows gathered",
        clue="a dark space just beyond the bedskirt",
        reach="low",
        properties={"dark", "low"},
        allows={"plush", "book", "blanket"},
        tags={"under_bed", "dark"},
    ),
    "laundry_basket": Place(
        id="laundry_basket",
        label="the laundry basket",
        phrase="the laundry basket full of warm little shirts",
        clue="a soft pile of clothes by the dresser",
        reach="middle",
        properties={"pile", "soft"},
        allows={"plush", "blanket", "shirt"},
        tags={"laundry", "clothes"},
    ),
    "bookshelf": Place(
        id="bookshelf",
        label="the bookshelf",
        phrase="the top shelf of the little bookshelf",
        clue="a high place where books liked to lean together",
        reach="high",
        properties={"high", "neat"},
        allows={"book", "plush"},
        tags={"bookshelf", "high"},
    ),
    "pillow_nest": Place(
        id="pillow_nest",
        label="the pillow nest",
        phrase="between the pillows at the head of the bed",
        clue="a puffy place where blankets and dreams got mixed together",
        reach="bed",
        properties={"bed", "soft"},
        allows={"plush", "blanket", "book"},
        tags={"pillows", "bed"},
    ),
    "toy_box": Place(
        id="toy_box",
        label="the toy box",
        phrase="the toy box where blocks and cars bumped shoulders",
        clue="a crowded box near the rug",
        reach="low",
        properties={"crowded", "low"},
        allows={"plush", "book"},
        tags={"toy_box", "toys"},
    ),
}

METHODS = {
    "flashlight_peek": Method(
        id="flashlight_peek",
        label="flashlight peek",
        phrase="a small flashlight peek",
        handles={"dark", "low"},
        sense=3,
        action="clicked on a tiny flashlight and knelt to look carefully",
        found_line="The beam slid across the floorboards until it found the missing thing.",
        qa_text="used a flashlight and looked carefully near the floor",
        tags={"flashlight", "search"},
    ),
    "sort_laundry": Method(
        id="sort_laundry",
        label="laundry sort",
        phrase="a slow laundry sort",
        handles={"pile", "soft"},
        sense=3,
        action="lifted the little clothes one by one and made neat stacks",
        found_line="At the bottom of the warm pile, the missing thing was waiting.",
        qa_text="sorted through the laundry basket one piece at a time",
        tags={"laundry", "search"},
    ),
    "parent_reach": Method(
        id="parent_reach",
        label="parent reach",
        phrase="a careful grown-up reach",
        handles={"high"},
        sense=3,
        action="stretched up with a steady grown-up arm and checked the high shelf",
        found_line="Behind a leaning row of books, the missing thing was tucked safely back.",
        qa_text="reached the high shelf with a steady grown-up arm",
        tags={"high", "search"},
    ),
    "straighten_bed": Method(
        id="straighten_bed",
        label="bed straighten",
        phrase="a gentle bed straighten",
        handles={"bed", "soft"},
        sense=3,
        action="fluffed the pillows and smoothed the blanket very slowly",
        found_line="Between the pillows, the missing thing peeked out as if it had been napping there.",
        qa_text="smoothed the pillows and blanket until the lost item appeared",
        tags={"bed", "search"},
    ),
    "tidy_box": Method(
        id="tidy_box",
        label="toy-box tidy",
        phrase="a toy-box tidy",
        handles={"crowded", "low"},
        sense=2,
        action="set the toys aside one by one instead of digging in a hurry",
        found_line="Under the wooden blocks, the missing thing appeared at last.",
        qa_text="tidied the toy box instead of rummaging wildly",
        tags={"toy_box", "search"},
    ),
    "wild_rummage": Method(
        id="wild_rummage",
        label="wild rummage",
        phrase="a wild rummage",
        handles={"crowded"},
        sense=1,
        action="dug everywhere at once and made the room messier",
        found_line="Nothing helpful came from the wild rummage.",
        qa_text="rummaged too fast and made a bigger mess",
        tags={"messy_search"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn", "Noah", "Eli", "Jack", "Owen"]
TRAITS = ["sleepy", "gentle", "careful", "quiet", "curious", "snuggly"]


def item_fits_place(item: ComfortItem, place: Place) -> bool:
    return item.type in place.allows or bool(item.kinds & place.allows)


def method_fits_place(method: Method, place: Place) -> bool:
    return place.properties.issubset(method.handles) or bool(place.properties & method.handles)


def reasonable_combo(item: ComfortItem, place: Place, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if not item_fits_place(item, place):
        return False
    return method_fits_place(method, place)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in COMFORT_ITEMS.items():
        for place_id, place in PLACES.items():
            for method_id, method in METHODS.items():
                if reasonable_combo(item, place, method):
                    combos.append((item_id, place_id, method_id))
    return combos


def explain_item_place(item: ComfortItem, place: Place) -> str:
    return (
        f"(No story: {item.label} does not plausibly belong in {place.label} here. "
        f"This world only hides each bedtime object in places where a child or grown-up "
        f"might reasonably have left it.)"
    )


def explain_method(place: Place, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Bedtime stories here prefer calm, "
            f"careful searching over frantic mess-making.)"
        )
    return (
        f"(No story: {method.label} does not fit {place.label}. The search method "
        f"must match where the item is hidden.)"
    )


def predict_success(world: World, place_id: str, method_id: str) -> bool:
    sim = world.copy()
    place = PLACES[place_id]
    method = METHODS[method_id]
    return place.properties.issubset(method.handles) or bool(place.properties & method.handles)


def introduce(world: World, child: Entity, parent: Entity, item_cfg: ComfortItem) -> None:
    world.say(
        f"In a quiet room with a moonlit window, {child.id} was getting ready for bed. "
        f"Every night, {child.pronoun()} liked {item_cfg.bedtime_use}."
    )
    world.say(
        f"That evening, {child.id}'s {parent.label_word} had already dimmed the lamp, "
        f"and the blanket on the bed looked soft as a cloud."
    )


def notice_missing(world: World, child: Entity, item_cfg: ComfortItem) -> None:
    item = world.get("item")
    item.meters["hidden"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} reached for {item_cfg.phrase}, it was not there."
    )
    world.say(
        f'"Oh no," {child.id} whispered. "I cannot sleep without my {item_cfg.label}."'
    )


def parent_asks(world: World, child: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed. '
        f'"Let us think slowly," {parent.pronoun()} said. '
        f'"Where did you last have it?"'
    )
    world.say(
        f'{child.id} blinked at the room and pointed toward {place.phrase}. '
        f'"Maybe near {place.label}," {child.pronoun()} said.'
    )


def search_start(world: World, child: Entity, parent: Entity, method: Method) -> None:
    world.facts["search_started"] = True
    propagate(world, narrate=False)
    world.say(
        f'"Then we will use {method.phrase}," {parent.label_word} said. '
        f'"Slow hands. Quiet eyes."'
    )
    world.say(
        f"Together they {method.action}."
    )


def find_item(world: World, child: Entity, item_cfg: ComfortItem, place: Place, method: Method) -> None:
    item = world.get("item")
    item.meters["hidden"] = 0.0
    item.meters["found"] = 1.0
    propagate(world, narrate=False)
    world.say(method.found_line)
    world.say(
        f'"There you are!" {child.id} said, hugging the {item_cfg.label}.'
    )
    world.say(
        f"The room no longer felt quite so large and whispery."
    )


def settle(world: World, child: Entity, parent: Entity, item_cfg: ComfortItem) -> None:
    world.say(
        f'{parent.label_word.capitalize()} kissed the top of {child.id}\'s head. '
        f'"See?" {parent.pronoun()} murmured. "When something is lost, we look slowly, '
        f'and the room grows gentle again."'
    )
    world.say(
        f'Snuggled into bed, {child.id} held the {item_cfg.label} close. Soon '
        f'{item_cfg.sleepy_image}, and {child.id}\'s eyes drifted shut.'
    )


def tell(
    item_cfg: ComfortItem,
    place_cfg: Place,
    method_cfg: Method,
    *,
    child_name: str = "Lily",
    child_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "sleepy",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        attrs={"trait": trait},
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        tags={"parent"},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="bedroom",
        tags={"room", "bedtime"},
    ))
    item = world.add(Entity(
        id="item",
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="comfort",
        attrs={"place": place_cfg.id},
        tags=set(item_cfg.tags),
    ))

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        item=item,
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        method_cfg=method_cfg,
        resolved=False,
        bedtime=True,
    )

    introduce(world, child, parent, item_cfg)
    world.para()
    notice_missing(world, child, item_cfg)
    parent_asks(world, child, parent, place_cfg)
    world.para()
    search_start(world, child, parent, method_cfg)
    find_item(world, child, item_cfg, place_cfg, method_cfg)
    world.para()
    settle(world, child, parent, item_cfg)

    world.facts["resolved"] = world.facts.get("found", False)
    world.facts["predicted_soothe"] = predict_success(world, place_cfg.id, method_cfg.id)
    return world


KNOWLEDGE = {
    "bedtime": [
        (
            "Why do bedtime routines help children sleep?",
            "Bedtime routines help because the same calm steps happen in the same order each night. That makes the body and mind feel safe and ready to rest.",
        )
    ],
    "plush": [
        (
            "Why can a plush toy feel comforting at bedtime?",
            "A plush toy feels soft and familiar, so holding it can help a child feel less alone. Familiar things often make bedtime feel safer.",
        )
    ],
    "blanket": [
        (
            "Why does a blanket feel cozy at night?",
            "A blanket helps keep your body warm. Warmth and softness can make it easier to relax and fall asleep.",
        )
    ],
    "book": [
        (
            "Why do some children like a book near the bed?",
            "A favorite book feels familiar, and quiet pictures or words can help the mind slow down. That is why bedtime books are often calm and gentle.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for at night?",
            "A flashlight helps you see in a dark place without turning the whole room bright again. It lets people look carefully and safely.",
        )
    ],
    "laundry": [
        (
            "Why is it easier to find something when you sort slowly?",
            "Sorting slowly keeps things from getting mixed up even more. Careful hands help your eyes notice what was hidden.",
        )
    ],
    "high": [
        (
            "Why should a grown-up reach for something high up?",
            "A grown-up is taller and steadier, so high shelves are safer for them to check. Children should ask for help instead of climbing alone.",
        )
    ],
    "toy_box": [
        (
            "Why is a toy box hard to search when it is crowded?",
            "A crowded toy box has many things touching and covering one another. Moving them one at a time is the best way to find something hidden.",
        )
    ],
    "under_bed": [
        (
            "Why can under the bed look spooky at night?",
            "Under the bed is dark, so shapes are harder to see clearly. When a light shines there, it often looks ordinary again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bedtime", "plush", "blanket", "book", "flashlight", "laundry", "high", "toy_box", "under_bed"]


@dataclass
class StoryParams:
    item: str
    place: str
    method: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item_cfg = world.facts["item_cfg"]
    place_cfg = world.facts["place_cfg"]
    return [
        (
            f'Write a gentle bedtime story with dialogue where a child cannot find a '
            f'beloved {item_cfg.label} and feels worried for a moment.'
        ),
        (
            f'Tell a cozy story about {child.id} looking for {item_cfg.phrase} near '
            f'{place_cfg.label}, with a calm grown-up helping and everyone speaking softly.'
        ),
        (
            'Write a bedtime story that includes the exact word "mickeymouse" when possible, '
            'uses dialogue, and ends with the child feeling safe enough to sleep.'
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    item_cfg = world.facts["item_cfg"]
    place_cfg = world.facts["place_cfg"]
    method_cfg = world.facts["method_cfg"]
    found = world.facts.get("found", False)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was getting ready for bed, and {child.pronoun('possessive')} {parent.label_word}, who helped. The story follows their quiet search together.",
        ),
        (
            f"Why was {child.id} upset at bedtime?",
            f"{child.id} was upset because the {item_cfg.label} was missing when bedtime was starting. Without that familiar comfort item, the room felt bigger and less cozy.",
        ),
        (
            f"Where did they look for the missing {item_cfg.label}?",
            f"They looked near {place_cfg.label}. {child.id} remembered that place and pointed to it when {parent.label_word} asked where to search.",
        ),
        (
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} helped by choosing {method_cfg.phrase} and moving carefully instead of rushing. That gentle method matched the place they were searching, so it helped them find the lost item.",
        ),
    ]
    if found:
        qa.append(
            (
                f"What happened when they searched carefully?",
                f"They found the {item_cfg.label} and {child.id} hugged it right away. Once the comfort item was back, the room felt gentle again and bedtime could go on.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {child.id} tucked safely in bed, holding the {item_cfg.label} close. The ending image shows that worry changed into relief and sleepiness.",
            )
        )
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bedtime"} | set(world.facts["item_cfg"].tags) | set(world.facts["method_cfg"].tags) | set(world.facts["place_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="mickeymouse_plush",
        place="under_bed",
        method="flashlight_peek",
        child_name="Lily",
        child_type="girl",
        parent_type="mother",
        trait="sleepy",
    ),
    StoryParams(
        item="moon_blanket",
        place="pillow_nest",
        method="straighten_bed",
        child_name="Theo",
        child_type="boy",
        parent_type="father",
        trait="gentle",
    ),
    StoryParams(
        item="bunny_book",
        place="bookshelf",
        method="parent_reach",
        child_name="Mia",
        child_type="girl",
        parent_type="mother",
        trait="quiet",
    ),
    StoryParams(
        item="mickeymouse_plush",
        place="toy_box",
        method="tidy_box",
        child_name="Ben",
        child_type="boy",
        parent_type="father",
        trait="curious",
    ),
    StoryParams(
        item="moon_blanket",
        place="laundry_basket",
        method="sort_laundry",
        child_name="Nora",
        child_type="girl",
        parent_type="mother",
        trait="snuggly",
    ),
]


ASP_RULES = r"""
fits_place(I,P) :- item_kind(I,K), allows(P,K).
works(M,P)      :- place_prop(P,R), handles(M,R).
good_method(M)  :- method(M), sense(M,S), sense_min(Min), S >= Min.
valid(I,P,M)    :- item(I), place(P), method(M), fits_place(I,P), works(M,P), good_method(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in COMFORT_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_kind", item_id, item.type))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for kind in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, kind))
        for prop in sorted(place.properties):
            lines.append(asp.fact("place_prop", place_id, prop))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for prop in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, prop))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params() raised StoryError on defaults: {err}")

    for idx, params in enumerate(smoke_cases):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False)
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE FAIL on case {idx + 1}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} normal story generations.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle bedtime search for a lost comfort item."
    )
    ap.add_argument("--item", choices=COMFORT_ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.item not in COMFORT_ITEMS:
        raise StoryError(f"(No story: unknown item '{args.item}'.)")
    if args.place and args.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{args.place}'.)")
    if args.method and args.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{args.method}'.)")

    if args.item and args.place:
        item = COMFORT_ITEMS[args.item]
        place = PLACES[args.place]
        if not item_fits_place(item, place):
            raise StoryError(explain_item_place(item, place))
    if args.place and args.method:
        place = PLACES[args.place]
        method = METHODS[args.method]
        if not reasonable_combo(COMFORT_ITEMS[args.item] if args.item else next(iter(COMFORT_ITEMS.values())), place, method):
            if method.sense < SENSE_MIN or not method_fits_place(method, place):
                raise StoryError(explain_method(place, method))
    if args.item and args.place and args.method:
        item = COMFORT_ITEMS[args.item]
        place = PLACES[args.place]
        method = METHODS[args.method]
        if not reasonable_combo(item, place, method):
            if not item_fits_place(item, place):
                raise StoryError(explain_item_place(item, place))
            raise StoryError(explain_method(place, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.place is None or combo[1] == args.place)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, place_id, method_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        item=item_id,
        place=place_id,
        method=method_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in COMFORT_ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")

    item_cfg = COMFORT_ITEMS[params.item]
    place_cfg = PLACES[params.place]
    method_cfg = METHODS[params.method]

    if not item_fits_place(item_cfg, place_cfg):
        raise StoryError(explain_item_place(item_cfg, place_cfg))
    if not reasonable_combo(item_cfg, place_cfg, method_cfg):
        raise StoryError(explain_method(place_cfg, method_cfg))

    world = tell(
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        method_cfg=method_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, place, method) combos:\n")
        for item_id, place_id, method_id in combos:
            print(f"  {item_id:18} {place_id:16} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} in {p.place} via {p.method}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
