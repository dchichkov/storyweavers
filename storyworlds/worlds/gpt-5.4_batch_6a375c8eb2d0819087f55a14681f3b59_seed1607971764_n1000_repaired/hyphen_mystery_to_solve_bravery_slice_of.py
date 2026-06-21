#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py
======================================================================

A standalone storyworld for a small slice-of-life mystery: a child notices a clue
on a handwritten "lost-and-found" card, follows it with bravery, and finds a
missing everyday item.

The mystery is always gentle and domestic. The key clue is a tiny mark on the
hyphen in "lost-and-found". That mark points toward the place where the item was
set down. Some places feel a little dim or echoey, so the child either takes a
deep breath and checks bravely, or bravely asks a nearby helper to come along.

Run it
------
    python storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py
    python storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py --item scarf --clue lint_on_hyphen
    python storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/hyphen_mystery_to_solve_bravery_slice_of.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ItemConfig:
    id: str
    label: str
    phrase: str
    type: str
    likely_places: set[str] = field(default_factory=set)
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
class ClueConfig:
    id: str
    place: str
    mark_text: str
    notice_text: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class PlaceConfig:
    id: str
    label: str
    phrase: str
    scare: int
    atmosphere: str
    find_text: str
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
class HelperConfig:
    id: str
    label: str
    type: str
    opening: str
    tags: set[str] = field(default_factory=set)
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


def _r_find_item(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    place = world.get("place")
    if child.meters["searched"] < THRESHOLD:
        return out
    if item.attrs.get("hidden_at") != place.id:
        return out
    sig = ("find", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.facts["found"] = True
    out.append("__found__")
    return out


def _r_settle_worry(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("settle", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="find_item", tag="physical", apply=_r_find_item),
    Rule(name="settle_worry", tag="emotional", apply=_r_settle_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def valid_combo(item_id: str, clue_id: str) -> bool:
    if item_id not in ITEMS or clue_id not in CLUES:
        return False
    return CLUES[clue_id].place in ITEMS[item_id].likely_places


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for clue_id, clue in CLUES.items():
            if clue.place in item.likely_places:
                combos.append((item_id, clue_id))
    return combos


def bravery_score(trait: str) -> int:
    return TRAIT_BRAVERY[trait]


def solve_mode(place_id: str, trait: str) -> str:
    place = PLACES[place_id]
    return "self" if bravery_score(trait) >= place.scare else "with_help"


def predict_solution(item_id: str, clue_id: str, trait: str) -> dict:
    place_id = CLUES[clue_id].place
    return {
        "valid": valid_combo(item_id, clue_id),
        "place": place_id,
        "mode": solve_mode(place_id, trait),
    }


def introduce(world: World, child: Entity, parent: Entity, item_cfg: ItemConfig) -> None:
    world.say(
        f"After school, {child.id} came in with {child.pronoun('possessive')} "
        f"{parent.label_word} and set down {item_cfg.phrase} by the apartment door."
    )
    world.say(
        f"It was the kind of ordinary evening with soft hallway sounds, a warm kitchen, "
        f"and shoes lined up by the wall."
    )


def cherish(world: World, child: Entity, item: Entity) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} liked that {item.label} very much and reached for it again a few minutes later."
    )


def missing(world: World, child: Entity, item: Entity) -> None:
    item.meters["missing"] = 1.0
    child.memes["worry"] += 1
    world.say(
        f"But the {item.label} was gone. {child.id} looked under the bench, on the chair, "
        f"and even behind the umbrella stand, and could not find it."
    )


def note_clue(world: World, child: Entity, clue: ClueConfig) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} noticed a little card on the hall table that said "
        f'"lost-and-found." {clue.mark_text}'
    )
    world.say(clue.notice_text)


def parent_support(world: World, child: Entity, parent: Entity, place: PlaceConfig) -> None:
    child.memes["supported"] += 1
    world.say(
        f'{parent.label_word.capitalize()} saw {child.id} thinking hard and said, '
        f'"We can solve one small mystery at a time. If the clue points to {place.phrase}, '
        f'we can start there."'
    )


def brave_decision(world: World, child: Entity, place: PlaceConfig, mode: str, helper: Entity) -> None:
    child.memes["fear"] += float(place.scare)
    child.memes["courage"] += float(bravery_score(child.attrs["trait"]))
    if mode == "self":
        world.say(
            f"{child.id} looked toward {place.phrase}. {place.atmosphere} "
            f"{child.pronoun().capitalize()} took a slow breath, held the card a little tighter, "
            f"and decided to check anyway."
        )
        world.facts["solution_mode"] = "self"
    else:
        child.memes["asking_help"] += 1
        world.say(
            f"{child.id} looked toward {place.phrase}. {place.atmosphere} "
            f"For a moment, {child.pronoun()} did not want to go alone."
        )
        world.say(
            f'{child.pronoun().capitalize()} walked over to {helper.label} and said, '
            f'"Will you come with me to {place.phrase}? I think the clue points there."'
        )
        world.say(
            f"{helper.opening} Together, they started down the hall."
        )
        world.facts["solution_mode"] = "with_help"


def search(world: World, child: Entity, place: Entity) -> None:
    child.meters["searched"] = 1.0
    place.meters["visited"] += 1
    propagate(world, narrate=False)


def found_scene(world: World, child: Entity, item: Entity, place_cfg: PlaceConfig) -> None:
    world.say(
        f"In {place_cfg.phrase}, {place_cfg.find_text} There was the {item.label}, "
        f"waiting exactly where the clue had promised."
    )


def ending(world: World, child: Entity, parent: Entity, item: Entity, clue: ClueConfig) -> None:
    mode = world.facts["solution_mode"]
    if mode == "self":
        brave_line = (
            f"{child.id} smiled in that quiet, surprised way that comes after doing "
            f"something brave alone."
        )
    else:
        brave_line = (
            f"{child.id} smiled because asking for help had been its own kind of bravery."
        )
    world.say(
        f"{child.id} carried the {item.label} back upstairs. {parent.label_word.capitalize()} "
        f"touched the little card and said the tiny hyphen had turned into a very good clue."
    )
    world.say(
        f"{brave_line} At home, the {item.label} went back to its proper place, and the evening "
        f"felt easy again."
    )
    world.say(
        f"Before dinner, {child.id} carefully drew a darker line through the hyphen on the "
        f'"lost-and-found" card so the next mystery would be easier to solve.'
    )


def tell(
    item_cfg: ItemConfig,
    clue_cfg: ClueConfig,
    helper_cfg: HelperConfig,
    child_name: str = "Nora",
    child_gender: str = "girl",
    trait: str = "steady",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.type,
        label=item_cfg.label,
        role="item",
        attrs={"hidden_at": clue_cfg.place},
    ))
    place_cfg = PLACES[clue_cfg.place]
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place_cfg.label,
        role="place",
        attrs={"scare": place_cfg.scare},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        item=item,
        item_cfg=item_cfg,
        clue=clue_cfg,
        place_cfg=place_cfg,
        found=False,
        solution_mode="",
    )

    introduce(world, child, parent, item_cfg)
    cherish(world, child, item)
    missing(world, child, item)

    world.para()
    note_clue(world, child, clue_cfg)
    parent_support(world, child, parent, place_cfg)

    mode = solve_mode(place_cfg.id, trait)
    brave_decision(world, child, place_cfg, mode, helper)

    world.para()
    search(world, child, place)
    if item.meters["found"] >= THRESHOLD:
        found_scene(world, child, item, place_cfg)
        ending(world, child, parent, item, clue_cfg)

    return world


KNOWLEDGE = {
    "hyphen": [
        (
            "What is a hyphen?",
            "A hyphen is a short little line used to join parts of some words. It can help a reader see that two words belong together."
        )
    ],
    "lost_found": [
        (
            "What is a lost-and-found?",
            "A lost-and-found is a place where people put things that have been misplaced. It helps the owner find them later."
        )
    ],
    "laundry_room": [
        (
            "Why can a laundry room feel damp or warm?",
            "A laundry room often has washing machines and dryers, so it can feel warm and steamy. That moisture can make paper curl or smudge."
        )
    ],
    "coat_closet": [
        (
            "Why does a coat closet collect lint and threads?",
            "Coats, scarves, and sweaters rub against one another in a closet. Tiny bits of fuzz or thread can come loose and stick to things nearby."
        )
    ],
    "basement_shelf": [
        (
            "Why can a basement shelf feel a little spooky even when it is safe?",
            "Basements are often dimmer and quieter than the rooms upstairs. New sounds and shadows can feel strange, even when nothing is wrong."
        )
    ],
    "ask_help": [
        (
            "Is asking for help a brave thing to do?",
            "Yes. Asking for help is brave because it means you notice what you need and say it out loud."
        )
    ],
    "library_book": [
        (
            "Why should people take care of library books?",
            "Library books belong to many readers, not just one person. Taking care of them helps the next child enjoy the same story."
        )
    ],
    "scarf": [
        (
            "What does a scarf do?",
            "A scarf helps keep your neck warm on a chilly day. Soft scarves can also easily slip off a hook or chair if nobody notices."
        )
    ],
    "notebook": [
        (
            "Why do people keep a notebook?",
            "A notebook is handy for lists, drawings, and small ideas. Because it is light and flat, it can be set down and forgotten more easily than a big bag."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item_cfg = world.facts["item_cfg"]
    place_cfg = world.facts["place_cfg"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old where a child solves a small mystery about a missing {item_cfg.label}. Include the word "hyphen".',
        f"Tell a homey story where {child.label} notices a clue on a lost-and-found card and bravely checks {place_cfg.phrase}.",
        f"Write a short mystery-to-solve story with everyday family life, a careful clue, and a brave ending where the missing {item_cfg.label} is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    item_cfg = world.facts["item_cfg"]
    clue = world.facts["clue"]
    place_cfg = world.facts["place_cfg"]
    mode = world.facts["solution_mode"]

    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {child.label}'s {item.label} had gone missing. {child.label} had to figure out where it had been set down."
        ),
        (
            "What clue did the child find?",
            f"{child.label} found a little card that said \"lost-and-found,\" and the mark near the hyphen gave a clue. {clue.mark_text} That helped point toward {place_cfg.phrase}."
        ),
        (
            f"Why did {child.label} feel nervous?",
            f"{child.label} felt nervous because {place_cfg.phrase} seemed a little daunting. {place_cfg.atmosphere} That made the search feel brave, not easy."
        ),
    ]
    if mode == "self":
        qa.append(
            (
                f"How did {child.label} show bravery?",
                f"{child.label} took a slow breath and checked {place_cfg.phrase} even though it felt a little scary. The bravery came from going on after the worry instead of running away from it."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.label} solve the mystery?",
                f"{child.label} bravely asked {helper.label} to come along to {place_cfg.phrase}. Asking for help was important because it let {child.pronoun('object')} keep going even while still feeling unsure."
            )
        )
    qa.append(
        (
            f"Where was the {item.label}?",
            f"The {item.label} was in {place_cfg.phrase}. It was there because the clue on the lost-and-found card pointed to that place."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The {item.label} went back to its proper place, and the evening felt easy again. {parent.label_word.capitalize()} even said the tiny hyphen had turned into a useful clue."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    place_cfg = world.facts["place_cfg"]
    mode = world.facts["solution_mode"]
    tags = {"hyphen", "lost_found"} | set(item_cfg.tags) | set(place_cfg.tags)
    if mode == "with_help":
        tags.add("ask_help")
    out: list[tuple[str, str]] = []
    order = [
        "hyphen",
        "lost_found",
        "laundry_room",
        "coat_closet",
        "basement_shelf",
        "ask_help",
        "library_book",
        "scarf",
        "notebook",
    ]
    for tag in order:
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


ITEMS = {
    "library_book": ItemConfig(
        id="library_book",
        label="library book",
        phrase="a thin library book with a clear plastic cover",
        type="book",
        likely_places={"laundry_room", "basement_shelf"},
        tags={"library_book"},
    ),
    "scarf": ItemConfig(
        id="scarf",
        label="scarf",
        phrase="a striped scarf still soft from winter",
        type="scarf",
        likely_places={"coat_closet", "laundry_room"},
        tags={"scarf"},
    ),
    "notebook": ItemConfig(
        id="notebook",
        label="notebook",
        phrase="a small notebook full of tidy drawings and lists",
        type="notebook",
        likely_places={"basement_shelf", "laundry_room"},
        tags={"notebook"},
    ),
}

PLACES = {
    "laundry_room": PlaceConfig(
        id="laundry_room",
        label="laundry room",
        phrase="the laundry room downstairs",
        scare=2,
        atmosphere="The hall was warm, and the machines made a low rumbling sound.",
        find_text="a folded towel sat on top of one machine, and beside it",
        tags={"laundry_room"},
    ),
    "coat_closet": PlaceConfig(
        id="coat_closet",
        label="coat closet",
        phrase="the coat closet near the lobby",
        scare=1,
        atmosphere="The door stood half-open, and the hanging coats made soft rustling sounds.",
        find_text="one sleeve had slipped sideways on a hook, and just below it",
        tags={"coat_closet"},
    ),
    "basement_shelf": PlaceConfig(
        id="basement_shelf",
        label="basement shelf",
        phrase="the basement shelf by the old bulbs",
        scare=3,
        atmosphere="The stairs were dim, and every footstep came back with a little echo.",
        find_text="a stack of flowerpots leaned against the wall, and right beside them",
        tags={"basement_shelf"},
    ),
}

CLUES = {
    "steam_smudge": ClueConfig(
        id="steam_smudge",
        place="laundry_room",
        mark_text="The little line of the hyphen looked blurred, as if warm damp air had touched it.",
        notice_text="That made the card seem as if it had spent time somewhere steamy.",
        tags={"hyphen", "lost_found"},
    ),
    "lint_on_hyphen": ClueConfig(
        id="lint_on_hyphen",
        place="coat_closet",
        mark_text="A tiny thread clung to the hyphen, blue and fuzzy as sweater lint.",
        notice_text="It looked exactly like the kind of fluff that gathered where coats and scarves brushed together.",
        tags={"hyphen", "lost_found"},
    ),
    "dust_by_hyphen": ClueConfig(
        id="dust_by_hyphen",
        place="basement_shelf",
        mark_text="A soft gray speck rested beside the hyphen, like shelf dust from a place people hardly used.",
        notice_text="It was not kitchen dust or hallway dirt. It looked like the still, powdery kind from downstairs.",
        tags={"hyphen", "lost_found"},
    ),
}

HELPERS = {
    "super": HelperConfig(
        id="super",
        label="the building super",
        type="man",
        opening="He smiled, took the stairs slowly, and said they would look together.",
        tags={"ask_help"},
    ),
    "neighbor": HelperConfig(
        id="neighbor",
        label="Mrs. Vega from 2B",
        type="woman",
        opening="She nodded at once and said that good clues were worth following.",
        tags={"ask_help"},
    ),
}

GIRL_NAMES = ["Nora", "Lina", "Mia", "Ava", "Rose", "Ella", "June", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Eli", "Leo", "Noah", "Sam", "Theo"]

TRAIT_BRAVERY = {
    "timid": 1,
    "careful": 2,
    "steady": 3,
    "bold": 4,
}
TRAITS = sorted(TRAIT_BRAVERY)


@dataclass
class StoryParams:
    item: str
    clue: str
    helper: str
    child_name: str
    child_gender: str
    trait: str
    parent: str
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


CURATED = [
    StoryParams(
        item="library_book",
        clue="steam_smudge",
        helper="neighbor",
        child_name="Nora",
        child_gender="girl",
        trait="careful",
        parent="mother",
    ),
    StoryParams(
        item="scarf",
        clue="lint_on_hyphen",
        helper="super",
        child_name="Milo",
        child_gender="boy",
        trait="steady",
        parent="father",
    ),
    StoryParams(
        item="notebook",
        clue="dust_by_hyphen",
        helper="neighbor",
        child_name="Ava",
        child_gender="girl",
        trait="timid",
        parent="mother",
    ),
    StoryParams(
        item="notebook",
        clue="steam_smudge",
        helper="super",
        child_name="Leo",
        child_gender="boy",
        trait="bold",
        parent="father",
    ),
]


def explain_rejection(item_id: str, clue_id: str) -> str:
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if clue_id not in CLUES:
        return f"(No story: unknown clue '{clue_id}'.)"
    item = ITEMS[item_id]
    clue = CLUES[clue_id]
    place = PLACES[clue.place]
    return (
        f"(No story: the clue points to {place.phrase}, but a {item.label} would not plausibly end up there in this world. "
        f"Choose a clue that points to one of these places instead: {', '.join(sorted(item.likely_places))}.)"
    )


ASP_RULES = r"""
valid(I,C) :- item(I), clue(C), clue_place(C,P), likely_place(I,P).

solve_mode(C,self) :- clue_place(C,P), scare(P,S), trait(T), bravery(T,B), B >= S.
solve_mode(C,with_help) :- clue_place(C,P), scare(P,S), trait(T), bravery(T,B), B < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for place_id in sorted(item.likely_places):
            lines.append(asp.fact("likely_place", item_id, place_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_place", clue_id, clue.place))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("scare", place_id, place.scare))
    for trait, score in TRAIT_BRAVERY.items():
        lines.append(asp.fact("bravery", trait, score))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solve_mode(clue_id: str, trait: str) -> str:
    import asp

    scenario = "\n".join([asp.fact("trait", trait), asp.fact("chosen", clue_id)])
    program = f"{asp_facts()}\n{ASP_RULES}\n{asp.fact('trait', trait)}\n#show solve_mode/2.\n"
    model = asp.one_model(program)
    modes = [mode for cid, mode in asp.atoms(model, "solve_mode") if cid == clue_id]
    return modes[0] if modes else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    cases = [
        ("steam_smudge", "timid"),
        ("steam_smudge", "bold"),
        ("lint_on_hyphen", "careful"),
        ("dust_by_hyphen", "steady"),
        ("dust_by_hyphen", "bold"),
    ]
    bad = 0
    for clue_id, trait in cases:
        if asp_solve_mode(clue_id, trait) != solve_mode(CLUES[clue_id].place, trait):
            bad += 1
    if bad == 0:
        print(f"OK: solve mode matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solve modes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny home mystery, a clue on a hyphen, and everyday bravery."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (item, clue) set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.clue and not valid_combo(args.item, args.clue):
        raise StoryError(explain_rejection(args.item, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.clue is None or combo[1] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, clue_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        item=item_id,
        clue=clue_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.trait not in TRAIT_BRAVERY:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if not valid_combo(params.item, params.clue):
        raise StoryError(explain_rejection(params.item, params.clue))

    world = tell(
        item_cfg=ITEMS[params.item],
        clue_cfg=CLUES[params.clue],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/2.\n#show solve_mode/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, clue) combos:\n")
        for item_id, clue_id in combos:
            place_id = CLUES[clue_id].place
            print(f"  {item_id:12} {clue_id:16} -> {place_id}")
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
            header = f"### {p.child_name}: {p.item} with {p.clue} ({solve_mode(CLUES[p.clue].place, p.trait)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
