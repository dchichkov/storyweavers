#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py
==================================================================================

A standalone story world for a tiny child-facing detective tale: a curious child
goes on a small quest to recover a missing object, follows concrete clues,
speaks badly for one worried moment, corrects course, and solves the case with
help.

The required seed words appear in authored prose:
- assure
- twerp
- flatter

Domain summary
--------------
A young detective notices that an important object has gone missing in a place
full of clues. The child wants to finish a tiny quest, so curiosity pulls the
search forward. A helper knows the place well. Sometimes the detective starts to
blurt out the rude word "twerp," then stops and apologizes; sometimes the
detective stays calm from the start. The helper gives a clue, assures the child
that the mystery has a simple answer, and the object is found in a plausible
spot.

Reasonableness constraints
--------------------------
Not every item belongs in every place, and not every hiding spot works for every
place. Flattery is only treated as a reasonable social move with a helper who
actually enjoys praise; otherwise the world refuses it and asks for a more
honest approach.

Run it
------
    python storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py
    python storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py --place bakery --item ribbon
    python storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py --place library --method flatter
    python storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/assure_twerp_flatter_quest_curiosity_detective_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "librarian_f", "baker_f", "gardener_f", "mother"}
        male = {"boy", "man", "librarian_m", "baker_m", "gardener_m", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "librarian_f": "librarian",
            "librarian_m": "librarian",
            "baker_f": "baker",
            "baker_m": "baker",
            "gardener_f": "gardener",
            "gardener_m": "gardener",
            "mother": "mom",
            "father": "dad",
        }
        return mapping.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    room_text: str
    helper_name: str
    helper_type: str
    helper_label: str
    helper_trait: str
    likes_praise: bool = False
    spots: set[str] = field(default_factory=set)
    items: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    quest_text: str
    owner_line: str
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
class Spot:
    id: str
    label: str
    clue_text: str
    clue_tag: str
    find_text: str
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
class Method:
    id: str
    sense: int
    text: str
    helper_effect: str
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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["clue_seen"] >= THRESHOLD:
        sig = ("curiosity",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["curiosity"] += 1
            out.append("__curiosity__")
    return out


def _r_hurt_pride(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    if detective.memes["rude"] >= THRESHOLD:
        sig = ("hurt",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hurt"] += 1
            out.append("__hurt__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    item = world.get("item")
    if helper.memes["hurt"] >= THRESHOLD and detective.memes["apology"] >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["trust"] += 1
            out.append("__repair__")
    if helper.memes["trust"] >= THRESHOLD and detective.meters["at_spot"] >= THRESHOLD:
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["found"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="curiosity", tag="emotional", apply=_r_curiosity),
    Rule(name="hurt_pride", tag="social", apply=_r_hurt_pride),
    Rule(name="repair", tag="social", apply=_r_repair),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="the little library",
        room_text="Tall shelves made quiet corners, and a yellow lamp shone over the reading table.",
        helper_name="Ms. Vale",
        helper_type="librarian_f",
        helper_label="the librarian",
        helper_trait="calm",
        likes_praise=False,
        spots={"returns_cart", "atlas_shelf", "window_nook"},
        items={"stamp_card", "magnifier"},
        tags={"library"},
    ),
    "bakery": Place(
        id="bakery",
        label="the warm bakery",
        room_text="The windows were foggy with sweet steam, and the counter smelled like cinnamon rolls.",
        helper_name="Mr. Crisp",
        helper_type="baker_m",
        helper_label="the baker",
        helper_trait="jolly",
        likes_praise=True,
        spots={"cookie_jar", "flour_tin", "receipt_hook"},
        items={"ribbon", "recipe_card"},
        tags={"bakery"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        room_text="Sunlight slid over the glass roof, and the benches were bright with leaves and little clay pots.",
        helper_name="Aunt Bea",
        helper_type="gardener_f",
        helper_label="the gardener",
        helper_trait="patient",
        likes_praise=False,
        spots={"seed_tray", "watering_bench", "boot_rack"},
        items={"brass_key", "magnifier"},
        tags={"garden"},
    ),
}

ITEMS = {
    "stamp_card": LostItem(
        id="stamp_card",
        label="stamp card",
        phrase="a small stamp card with five empty stars",
        quest_text="Without it, the reading quest could not be finished.",
        owner_line="The card was needed to earn the last bright star.",
        tags={"quest", "paper"},
    ),
    "magnifier": LostItem(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass with a blue handle",
        quest_text="Without it, the detective quest felt unfinished.",
        owner_line="The magnifying glass was the detective's favorite tool.",
        tags={"quest", "detective"},
    ),
    "ribbon": LostItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon for the pretend champion",
        quest_text="Without it, the winner's quest parade could not begin.",
        owner_line="The ribbon was meant for the end of the day's little quest.",
        tags={"quest", "ribbon"},
    ),
    "recipe_card": LostItem(
        id="recipe_card",
        label="recipe card",
        phrase="a flour-dusted recipe card with a smiling pie on it",
        quest_text="Without it, the baking quest could not reach its last step.",
        owner_line="The card held the final step for the morning's treat.",
        tags={"quest", "baking"},
    ),
    "brass_key": LostItem(
        id="brass_key",
        label="brass key",
        phrase="a brass key tied with green string",
        quest_text="Without it, the garden chest at the end of the quest would stay shut.",
        owner_line="The key opened the tiny chest where the prize waited.",
        tags={"quest", "key"},
    ),
}

SPOTS = {
    "returns_cart": Spot(
        id="returns_cart",
        label="the returns cart",
        clue_text="A paper edge peeked out beside a stack of returned books.",
        clue_tag="paper",
        find_text="There, tucked beside the returned books, lay the missing thing.",
        tags={"paper", "cart"},
    ),
    "atlas_shelf": Spot(
        id="atlas_shelf",
        label="the atlas shelf",
        clue_text="A fat atlas leaned crooked, as if something had slipped behind it.",
        clue_tag="book",
        find_text="Behind the atlas, safe in the dust-free gap, lay the missing thing.",
        tags={"book"},
    ),
    "window_nook": Spot(
        id="window_nook",
        label="the window nook",
        clue_text="A square patch of sun lit a little seat where small things liked to slide.",
        clue_tag="sun",
        find_text="In the window nook, under the cushion seam, lay the missing thing.",
        tags={"sun"},
    ),
    "cookie_jar": Spot(
        id="cookie_jar",
        label="the cookie jar shelf",
        clue_text="A blue thread rested near the cookie jar, bright against the wood.",
        clue_tag="thread",
        find_text="Curled behind the cookie jar shelf, the missing thing waited.",
        tags={"thread", "cookie"},
    ),
    "flour_tin": Spot(
        id="flour_tin",
        label="the flour tin",
        clue_text="A puff of white dust marked a tiny trail across the counter.",
        clue_tag="flour",
        find_text="Leaning against the flour tin, the missing thing was dusted white but safe.",
        tags={"flour"},
    ),
    "receipt_hook": Spot(
        id="receipt_hook",
        label="the receipt hook",
        clue_text="A corner of paper fluttered under a hook by the register.",
        clue_tag="paper",
        find_text="Pinned lightly behind the receipt hook, the missing thing hung in plain sight.",
        tags={"paper"},
    ),
    "seed_tray": Spot(
        id="seed_tray",
        label="the seed tray",
        clue_text="A line of crumbly soil led to the tray of tiny seedlings.",
        clue_tag="soil",
        find_text="Beside the seed tray, half hidden by leaves, lay the missing thing.",
        tags={"soil", "leaf"},
    ),
    "watering_bench": Spot(
        id="watering_bench",
        label="the watering bench",
        clue_text="A wet ring on the bench showed where something had been set down in a hurry.",
        clue_tag="water",
        find_text="Under the watering can on the bench, the missing thing glinted.",
        tags={"water"},
    ),
    "boot_rack": Spot(
        id="boot_rack",
        label="the boot rack",
        clue_text="A green string peeked from behind the smallest boot.",
        clue_tag="string",
        find_text="Behind the boot rack, right where muddy shoes ended, lay the missing thing.",
        tags={"string"},
    ),
}

METHODS = {
    "ask": Method(
        id="ask",
        sense=3,
        text="asked a clear, honest question",
        helper_effect="The question made it easy for the helper to think back carefully.",
        tags={"ask"},
    ),
    "flatter": Method(
        id="flatter",
        sense=2,
        text='tried to flatter the helper by saying, "You notice everything here."',
        helper_effect="The warm praise opened the helper's memory instead of making the moment feel pushy.",
        tags={"flatter"},
    ),
    "grumble": Method(
        id="grumble",
        sense=1,
        text="muttered and grumbled instead of asking properly",
        helper_effect="The grumbling only made the room feel tighter.",
        tags={"rude"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Ruby", "June"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Eli", "Finn", "Jack", "Noah"]
TRAITS = ["curious", "careful", "bright", "eager", "patient", "thoughtful"]
MOODS = ["steady", "snappy"]


def item_fits_place(item_id: str, place_id: str) -> bool:
    return item_id in PLACES[place_id].items


def spot_fits_place(spot_id: str, place_id: str) -> bool:
    return spot_id in PLACES[place_id].spots


def method_fits_place(method_id: str, place_id: str) -> bool:
    if method_id == "ask":
        return True
    if method_id == "flatter":
        return PLACES[place_id].likes_praise
    if method_id == "grumble":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            if not item_fits_place(item_id, place_id):
                continue
            for spot_id in sorted(SPOTS):
                if not spot_fits_place(spot_id, place_id):
                    continue
                for method_id, method in METHODS.items():
                    if method.sense < SENSE_MIN:
                        continue
                    if method_fits_place(method_id, place_id):
                        combos.append((place_id, item_id, spot_id, method_id))
    return combos


def explain_item_place(item_id: str, place_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    return (
        f"(No story: {item.phrase} does not belong in {place.label}. "
        f"Choose an item that fits that place's tiny mystery.)"
    )


def explain_spot_place(spot_id: str, place_id: str) -> str:
    place = PLACES[place_id]
    spot = SPOTS[spot_id]
    return (
        f"(No story: {spot.label} is not a plausible hiding place in {place.label}. "
        f"Pick a spot that actually belongs there.)"
    )


def explain_method(method_id: str, place_id: str) -> str:
    method = METHODS[method_id]
    place = PLACES[place_id]
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try asking clearly instead.)"
        )
    if method_id == "flatter" and not place.likes_praise:
        return (
            f"(No story: in {place.label}, trying to flatter {place.helper_label} "
            f"is not a natural or necessary way to get help. Try --method ask.)"
        )
    return "(No story: that social method does not fit this mystery.)"


def outcome_of(params: "StoryParams") -> str:
    return "repair" if params.mood == "snappy" else "smooth"


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("detective").meters["at_spot"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("item").meters["found"] >= THRESHOLD,
        "trust": sim.get("helper").memes["trust"],
    }


def introduce(world: World, detective: Entity, place: Place) -> None:
    world.say(
        f"{detective.id} padded into {place.label} with a notebook in one hand and "
        f"a look of bright curiosity on {detective.pronoun('possessive')} face. "
        f"{place.room_text}"
    )


def set_quest(world: World, detective: Entity, item: LostItem) -> None:
    detective.memes["quest"] += 1
    world.say(
        f"Today was no ordinary errand. It was a small quest. {detective.id} was "
        f"looking for {item.phrase}. {item.quest_text}"
    )
    world.say(item.owner_line)


def discover_missing(world: World, detective: Entity, item_ent: Entity) -> None:
    detective.memes["worry"] += 1
    item_ent.meters["missing"] += 1
    world.say(
        f"But when {detective.pronoun()} reached for the {item_ent.label}, it was gone. "
        f"The empty space where it should have been felt like the start of a real case."
    )


def notice_clue(world: World, detective: Entity, spot: Spot) -> None:
    detective.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} knelt down and looked slowly instead of rushing. "
        f"{spot.clue_text}"
    )
    if detective.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"That small clue tugged hard at {detective.pronoun('possessive')} curiosity. "
            f"A good detective followed what the room was quietly saying."
        )


def blurt_and_catch(world: World, detective: Entity) -> None:
    detective.memes["rude"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did some twerp hide it?" {detective.id} blurted, and the word sounded '
        f"too sharp the moment it landed."
    )


def self_correct(world: World, detective: Entity) -> None:
    detective.memes["restraint"] += 1
    world.say(
        f"{detective.id} took a breath. Calling someone a twerp would not solve the case, "
        f"and trying to flatter everyone without thinking would not solve it either."
    )


def ask_helper(world: World, detective: Entity, helper: Entity, method: Method, place: Place) -> None:
    if method.id == "ask":
        world.say(
            f"So {detective.id} walked to {place.helper_name} and asked a careful question "
            f"about where the {world.get('item').label} had last been seen."
        )
    elif method.id == "flatter":
        world.say(
            f"So {detective.id} went to {place.helper_name} and {method.text}. "
            f'{place.helper_name} smiled a little at that.'
        )
    else:
        world.say(
            f"So {detective.id} {method.text}."
        )
    world.say(method.helper_effect)
    helper.memes["trust"] += 1


def apologize(world: World, detective: Entity, helper: Entity, place: Place) -> None:
    detective.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry," {detective.id} said. "I should not have said twerp. '
        f'I want to solve the mystery kindly."'
    )
    if helper.memes["trust"] >= THRESHOLD:
        world.say(
            f"{place.helper_name} nodded. The room felt easier at once."
        )


def helper_assures(world: World, helper: Entity, place: Place, spot: Spot) -> None:
    world.say(
        f'"I can assure you nobody was being mean," {place.helper_name} said. '
        f'"I remember seeing a clue near {spot.label}."'
    )


def follow_clue(world: World, detective: Entity, spot: Spot) -> None:
    detective.meters["at_spot"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Off went {detective.id}, following the clue to {spot.label} as if the whole "
        f"place had become a map made just for this case."
    )


def find_item(world: World, detective: Entity, item_ent: Entity, spot: Spot) -> None:
    if item_ent.meters["found"] < THRESHOLD:
        item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    detective.memes["relief"] += 1
    detective.memes["joy"] += 1
    world.say(spot.find_text.replace("the missing thing", f"the missing {item_ent.label}"))
    world.say(
        f"{detective.id} lifted it high and laughed softly, because the mystery had "
        f"turned back into a quest again."
    )


def close_case(world: World, detective: Entity, helper: Entity, item: LostItem, place: Place, outcome: str) -> None:
    if outcome == "repair":
        world.say(
            f"{place.helper_name} tapped the notebook with one finger. "
            f'"That was real detective work," {helper.pronoun()} said. '
            f'{detective.id} nodded, a little pink in the cheeks, and used a kinder voice after that.'
        )
    else:
        world.say(
            f"{place.helper_name} smiled and said the case had been solved with clear eyes and a calm heart."
        )
    world.say(
        f"With the {item.label} safe again, {detective.id} hurried on toward the end of the quest, "
        f"more curious than ever and much more careful with words."
    )
def tell(
    item: Item,
    spot: Spot,
    method: Method,
    name: str,
    gender: str,
    trait: Trait,
    mood: Mood,
    place=None,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="detective",
            traits=[trait],
            attrs={"mood": mood},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=place.helper_type,
            role="helper",
            label=place.helper_label,
            attrs={"name": place.helper_name, "likes_praise": place.likes_praise},
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item.label,
            attrs={"spot": spot.id},
        )
    )

    world.facts.update(
        place=place,
        item_cfg=item,
        spot=spot,
        method=method,
        mood=mood,
        detective_name=name,
        detective_gender=gender,
        trait=trait,
        helper_name=place.helper_name,
        predicted_found=False,
    )

    detective.memes["trust_help"] = 0.0
    helper.memes["trust"] = 0.0
    helper.memes["hurt"] = 0.0
    detective.meters["clue_seen"] = 0.0
    detective.meters["at_spot"] = 0.0
    item_ent.meters["found"] = 0.0
    item_ent.meters["missing"] = 0.0

    introduce(world, detective, place)
    set_quest(world, detective, item)
    discover_missing(world, detective, item_ent)

    world.para()
    notice_clue(world, detective, spot)
    if mood == "snappy":
        blurt_and_catch(world, detective)
    self_correct(world, detective)
    ask_helper(world, detective, helper, method, place)
    if mood == "snappy":
        apologize(world, detective, helper, place)
    helper_assures(world, helper, place, spot)

    predicted = predict_solution(world)
    world.facts["predicted_found"] = predicted["found"]
    world.facts["predicted_trust"] = predicted["trust"]

    world.para()
    follow_clue(world, detective, spot)
    find_item(world, detective, item_ent, spot)
    close_case(world, detective, helper, item, place, outcome_of(StoryParams(
        place=place.id,
        item=item.id,
        spot=spot.id,
        method=method.id,
        name=name,
        gender=gender,
        trait=trait,
        mood=mood,
    )))

    world.facts.update(
        detective=detective,
        helper=helper,
        item=item_ent,
        found=item_ent.meters["found"] >= THRESHOLD,
        outcome="repair" if mood == "snappy" else "smooth",
    )
    return world
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


KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a job or journey with a goal at the end. In a story, a quest gives the character something important to keep trying for.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery. Good detectives notice small details instead of guessing wildly.",
        )
    ],
    "library": [
        (
            "What does a librarian do?",
            "A librarian helps people find books and keeps them in the right places. Librarians also notice where things were last seen.",
        )
    ],
    "bakery": [
        (
            "What does a baker do?",
            "A baker makes bread, cakes, and other treats. Bakers often notice flour, trays, and other clues around their work tables.",
        )
    ],
    "garden": [
        (
            "What does a gardener do?",
            "A gardener cares for plants, seeds, and soil. Gardeners notice leaves, strings, and watering tools that other people might miss.",
        )
    ],
    "flatter": [
        (
            "What does flatter mean?",
            "To flatter someone is to praise them in a way that tries to make them feel extra pleased. Honest kindness is better than praise that is only used to get something.",
        )
    ],
    "kind_words": [
        (
            "Why should we avoid rude words when we need help?",
            "Rude words can hurt feelings and make people pull back. Calm, kind words make it easier for everyone to think and solve the problem together.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that points toward an answer. A clue might be a mark, a trail, or something in an odd place.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "detective", "library", "bakery", "garden", "clue", "flatter", "kind_words"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    item = world.facts["item_cfg"]
    mood = world.facts["mood"]
    method = world.facts["method"]
    name = world.facts["detective_name"]
    tone = "briefly says a rude word and then apologizes" if mood == "snappy" else "stays calm and observant"
    return [
        f'Write a short detective story for a 3-to-5-year-old about a child on a quest to find a missing {item.label} in {place.label}. Include the words "assure", "twerp", and "flatter".',
        f"Tell a gentle mystery where {name} {tone}, follows a clue, and gets help from {place.helper_label}.",
        f"Write a child-facing detective tale where curiosity leads the search and {method.id} is the way the child asks for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    item = world.facts["item_cfg"]
    spot = world.facts["spot"]
    method = world.facts["method"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a young detective on a small quest, and {place.helper_name}, who knows {place.label} well.",
        ),
        (
            f"What was {detective.id} trying to find?",
            f"{detective.id} was trying to find the missing {item.label}. It mattered because {item.quest_text.lower()}",
        ),
        (
            "What clue started the search?",
            f"The first clue was that {spot.clue_text[0].lower()}{spot.clue_text[1:]} That clue gave {detective.id} a real place to investigate instead of just guessing.",
        ),
        (
            f"How did {detective.id} ask for help?",
            f"{detective.id} {method.text}. {method.helper_effect}",
        ),
    ]
    if outcome == "repair":
        qa.append(
            (
                f"Why did {detective.id} apologize?",
                f"{detective.id} blurted out the rude word 'twerp' when the mystery felt frustrating. Then {detective.pronoun()} realized that unkind words would not solve the case, so {detective.pronoun()} apologized and made it easier for the helper to trust {detective.pronoun('object')}.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the search go smoothly?",
                f"The search went smoothly because {detective.id} slowed down, noticed a real clue, and used a calm voice with the helper. That kept the mystery from turning into an argument.",
            )
        )
    qa.append(
        (
            f"How was the mystery solved?",
            f"{place.helper_name} said, 'I can assure you nobody was being mean,' and pointed {detective.id} toward {spot.label}. When {detective.pronoun()} followed that clue, the missing {item.label} was right there.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the {item.label} found and the quest back on track. The ending shows that curiosity and kind words helped more than sharp guesses.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    tags = {"quest", "detective", "clue", "kind_words", "flatter"} | set(place.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    item: str
    spot: str
    method: str
    name: str
    gender: str
    trait: str
    mood: str = "steady"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="library",
        item="stamp_card",
        spot="returns_cart",
        method="ask",
        name="Nora",
        gender="girl",
        trait="curious",
        mood="steady",
    ),
    StoryParams(
        place="bakery",
        item="ribbon",
        spot="cookie_jar",
        method="flatter",
        name="Theo",
        gender="boy",
        trait="bright",
        mood="snappy",
    ),
    StoryParams(
        place="greenhouse",
        item="brass_key",
        spot="seed_tray",
        method="ask",
        name="Mia",
        gender="girl",
        trait="careful",
        mood="steady",
    ),
    StoryParams(
        place="bakery",
        item="recipe_card",
        spot="flour_tin",
        method="ask",
        name="Ben",
        gender="boy",
        trait="eager",
        mood="snappy",
    ),
    StoryParams(
        place="library",
        item="magnifier",
        spot="atlas_shelf",
        method="ask",
        name="Ruby",
        gender="girl",
        trait="thoughtful",
        mood="steady",
    ),
]


ASP_RULES = r"""
valid(P, I, S, M) :- place(P), item(I), spot(S), method(M),
                     item_in_place(P, I), spot_in_place(P, S),
                     sensible(M), method_ok(P, M).

sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.
method_ok(P, ask) :- place(P).
method_ok(P, flatter) :- place(P), likes_praise(P).
method_ok(P, grumble) :- place(P).

outcome(repair) :- mood(snappy).
outcome(smooth) :- mood(steady).

#show valid/4.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.likes_praise:
            lines.append(asp.fact("likes_praise", pid))
        for item_id in sorted(place.items):
            lines.append(asp.fact("item_in_place", pid, item_id))
        for spot_id in sorted(place.spots):
            lines.append(asp.fact("spot_in_place", pid, spot_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("mood", params.mood)))
    bits = asp.atoms(model, "outcome")
    return bits[0][0] if bits else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid_combos parity holds ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos parity:")
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))

    py_sensible = {mid for mid, method in METHODS.items() if method.sense >= SENSE_MIN}
    cl_sensible = set(asp_sensible_methods())
    if py_sensible == cl_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sensible)} clingo={sorted(cl_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny detective story world: a missing object, a clue, and a kind solution."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and not item_fits_place(args.item, args.place):
        raise StoryError(explain_item_place(args.item, args.place))
    if args.place and args.spot and not spot_fits_place(args.spot, args.place):
        raise StoryError(explain_spot_place(args.spot, args.place))
    if args.method and args.place and not method_fits_place(args.method, args.place):
        raise StoryError(explain_method(args.method, args.place))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method, args.place or "library"))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spot is None or combo[2] == args.spot)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, spot_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    trait = args.trait or rng.choice(TRAITS)
    mood = args.mood or rng.choice(MOODS)

    return StoryParams(
        place=place_id,
        item=item_id,
        spot=spot_id,
        method=method_id,
        name=name,
        gender=gender,
        trait=trait,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.spot not in SPOTS:
        raise StoryError(f"Unknown spot: {params.spot}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")

    if not item_fits_place(params.item, params.place):
        raise StoryError(explain_item_place(params.item, params.place))
    if not spot_fits_place(params.spot, params.place):
        raise StoryError(explain_spot_place(params.spot, params.place))
    if METHODS[params.method].sense < SENSE_MIN or not method_fits_place(params.method, params.place):
        raise StoryError(explain_method(params.method, params.place))

    world = tell(
        place=PLACES[params.place],
        item=ITEMS[params.item],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        name=params.name,
        gender=params.gender,
        trait=params.trait,
        mood=params.mood,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        print(f"{len(combos)} compatible (place, item, spot, method) combos:\n")
        for place_id, item_id, spot_id, method_id in combos:
            print(f"  {place_id:10} {item_id:12} {spot_id:14} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.name}: {p.item} in {p.place} ({p.spot}, {p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
