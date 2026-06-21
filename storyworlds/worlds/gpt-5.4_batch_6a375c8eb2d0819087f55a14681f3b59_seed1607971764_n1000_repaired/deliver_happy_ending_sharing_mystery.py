#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py
==================================================================

A standalone story world for a gentle mystery: a package is delivered with no
name, two children find it, and the mystery is solved by sharing the clue with
other people instead of keeping the surprise to themselves.

The world model is small and concrete:

- a place supports certain kinds of delivered gifts
- each gift comes with a clue that points to a likely giver
- a helper at that place can recognize some clues
- the children choose a sharing move that opens the mystery to the room

If the combination is reasonable, the helper can identify who meant the gift for
everyone, and the ending image shows the children sharing it. Unreasonable
combinations are refused with a readable StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py --gift muffins --place hall
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py --gift seedlings --place reading_room
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py --all
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/deliver_happy_ending_sharing_mystery.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    parcel_spot: str
    crowd: str
    allows_gifts: set[str] = field(default_factory=set)
    allows_share: set[str] = field(default_factory=set)
    helper_ids: set[str] = field(default_factory=set)
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
class Gift:
    id: str
    label: str
    phrase: str
    container: str
    ending: str
    giver_kind: str
    place_ids: set[str] = field(default_factory=set)
    clue_ids: set[str] = field(default_factory=set)
    shareable: bool = True
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
class Clue:
    id: str
    label: str
    sight: str
    giver_kind: str
    gift_ids: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    title: str
    type: str
    place_ids: set[str] = field(default_factory=set)
    knows: set[str] = field(default_factory=set)
    giver_kinds: set[str] = field(default_factory=set)
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
class ShareMode:
    id: str
    line: str
    result: str
    place_ids: set[str] = field(default_factory=set)
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"finder", "friend"}]

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


def _r_found_curiosity(world: World) -> list[str]:
    parcel = world.get("parcel")
    if parcel.meters["found"] < THRESHOLD:
        return []
    sig = ("found_curiosity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out: list[str] = []
    for kid in world.kids():
        kid.memes["curiosity"] += 1
        kid.memes["wonder"] += 1
    parcel.meters["mystery"] += 1
    out.append("__mystery__")
    return out


def _r_share_attention(world: World) -> list[str]:
    parcel = world.get("parcel")
    if parcel.meters["shared"] < THRESHOLD:
        return []
    sig = ("share_attention",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["generosity"] += 1
    world.get("room").meters["attention"] += 1
    return ["__attention__"]


def _r_solve(world: World) -> list[str]:
    parcel = world.get("parcel")
    helper = world.get("helper")
    clue = world.get("clue")
    room = world.get("room")
    if parcel.meters["shared"] < THRESHOLD:
        return []
    if clue.meters["seen"] < THRESHOLD:
        return []
    if room.meters["attention"] < THRESHOLD:
        return []
    if helper.attrs.get("can_decode") != 1:
        return []
    sig = ("solve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["solved"] += 1
    parcel.meters["delivered_for_all"] += 1
    gift = world.get("gift")
    gift.meters["claimed_for_all"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="found_curiosity", tag="emotional", apply=_r_found_curiosity),
    Rule(name="share_attention", tag="social", apply=_r_share_attention),
    Rule(name="solve", tag="social", apply=_r_solve),
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
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if not bit.startswith("__"):
                world.say(bit)
    return produced


def gift_fits_place(place: Place, gift: Gift) -> bool:
    return gift.id in place.allows_gifts and place.id in gift.place_ids


def clue_matches_gift(gift: Gift, clue: Clue) -> bool:
    return clue.id in gift.clue_ids and gift.id in clue.gift_ids and clue.giver_kind == gift.giver_kind


def helper_fits(place: Place, helper: Helper, clue: Clue, gift: Gift) -> bool:
    return (
        helper.id in place.helper_ids
        and place.id in helper.place_ids
        and clue.id in helper.knows
        and clue.giver_kind in helper.giver_kinds
        and gift.giver_kind in helper.giver_kinds
    )


def share_allowed(place: Place, share: ShareMode) -> bool:
    return share.id in place.allows_share and place.id in share.place_ids


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for gift_id, gift in GIFTS.items():
            for clue_id, clue in CLUES.items():
                for helper_id, helper in HELPERS.items():
                    for share_id, share in SHARE_MODES.items():
                        if not gift.shareable:
                            continue
                        if gift_fits_place(place, gift) and clue_matches_gift(gift, clue) and helper_fits(place, helper, clue, gift) and share_allowed(place, share):
                            combos.append((place_id, gift_id, clue_id, helper_id, share_id))
    return combos


def explain_rejection(place: Place, gift: Gift, clue: Clue, helper: Helper, share: ShareMode) -> str:
    if not gift.shareable:
        return (
            f"(No story: {gift.label} is not something the children can share, "
            "so it does not fit a sharing ending.)"
        )
    if not gift_fits_place(place, gift):
        return (
            f"(No story: {gift.label} does not fit {place.label}. A delivered gift "
            "needs to belong naturally in that place.)"
        )
    if not clue_matches_gift(gift, clue):
        return (
            f"(No story: the clue '{clue.label}' does not honestly point to "
            f"{gift.label}. The mystery must have a real answer.)"
        )
    if not helper_fits(place, helper, clue, gift):
        return (
            f"(No story: {helper.title} would not reasonably recognize that clue "
            f"in {place.label}. The mystery needs a believable solver.)"
        )
    if not share_allowed(place, share):
        return (
            f"(No story: the sharing move '{share.id}' does not fit {place.label}. "
            "The children need a sensible way to open the mystery to others.)"
        )
    return "(No story: the requested combination is not reasonable.)"


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("parcel").meters["shared"] += 1
    sim.get("clue").meters["seen"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim.get("parcel").meters["solved"] >= THRESHOLD,
        "attention": sim.get("room").meters["attention"],
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"{place.opening} {hero.id} and {friend.id} were in {place.label}, where even small sounds seemed to matter."
    )
    world.say(
        f"They liked pretending they were detectives, so when something odd appeared, both of them noticed at once."
    )


def discover(world: World, hero: Entity, friend: Entity, gift: Gift, clue: Clue, place: Place) -> None:
    parcel = world.get("parcel")
    gift_ent = world.get("gift")
    clue_ent = world.get("clue")
    parcel.meters["found"] += 1
    gift_ent.attrs["container"] = gift.container
    clue_ent.attrs["clue_label"] = clue.label
    propagate(world, narrate=False)
    world.say(
        f"On {place.parcel_spot} sat {gift.container}. Someone had come early to deliver it, but no name was written on the outside."
    )
    world.say(
        f'"Who left that there?" {hero.id} whispered. {friend.id} stepped closer, eyes wide, and saw {clue.sight}.'
    )


def wonder(world: World, hero: Entity, friend: Entity, clue: Clue, helper: Entity) -> None:
    pred = predict_solution(world)
    world.facts["predicted_attention"] = pred["attention"]
    if pred["solved"]:
        extra = f" If they showed the clue around, maybe {helper.label} would know what it meant."
    else:
        extra = ""
    world.say(
        f"The clue looked important, but neither child could read the whole secret from it.{extra}"
    )
    world.say(
        f'{friend.id} breathed, "It feels like the beginning of a real mystery."'
    )


def temptation(world: World, hero: Entity, gift: Gift) -> None:
    hero.memes["want_keep"] += 1
    world.say(
        f"For one little moment, {hero.id} wondered whether the surprise might be just for the two of them."
    )
    world.say(
        f"But {gift.container} looked too carefully placed for a sneaky private treat."
    )


def choose_share(world: World, hero: Entity, friend: Entity, share: ShareMode) -> None:
    parcel = world.get("parcel")
    clue_ent = world.get("clue")
    parcel.meters["shared"] += 1
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(share.line.format(hero=hero.id, friend=friend.id))
    world.say(share.result)


def solve_mystery(world: World, helper: Entity, gift: Gift, clue: Clue) -> None:
    parcel = world.get("parcel")
    if parcel.meters["solved"] < THRESHOLD:
        raise StoryError("(Internal story error: a shared mystery did not resolve.)")
    world.say(
        f"That was enough for {helper.label}. {helper.pronoun('subject').capitalize()} looked at {clue.sight}, smiled slowly, and said, "
        f'"I know this sign. It came from the {gift.giver_kind}."'
    )
    world.say(
        f"{helper.label} explained that the {gift.giver_kind} had asked someone to deliver {gift.phrase} for everyone to enjoy together."
    )


def reveal_giver(world: World, helper: Entity, gift: Gift) -> None:
    giver_name = gift.giver_kind
    world.say(
        f"At once the mystery changed shape. The package had never been a secret prize to hide; it was a kind surprise meant to be shared."
    )
    world.say(
        f"{helper.label} set the {gift.container} where everyone could see it, and the room gave a happy little murmur."
    )
    world.facts["giver_kind"] = giver_name


def shared_ending(world: World, hero: Entity, friend: Entity, gift: Gift, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["generosity"] += 1
    friend.memes["generosity"] += 1
    world.say(gift.ending.format(hero=hero.id, friend=friend.id, place=place.label))
    world.say(
        f"{hero.id} grinned at {friend.id}. The best part of the mystery, both of them decided, was not finding something to keep. It was helping everyone share it."
    )


def tell(
    place: Place,
    gift: Gift,
    clue: Clue,
    helper_cfg: Helper,
    share: ShareMode,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    friend_name: str = "Theo",
    friend_gender: str = "boy",
) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, role="finder"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, label=friend_name, role="friend"))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"can_decode": 1},
        tags=set(helper_cfg.tags),
    ))
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(id="parcel", type="parcel", label="the parcel"))
    world.add(Entity(id="gift", type="gift", label=gift.label, tags=set(gift.tags)))
    world.add(Entity(id="clue", type="clue", label=clue.label, tags=set(clue.tags), attrs={"giver_kind": clue.giver_kind}))

    world.facts["predicted_attention"] = 0
    world.facts["giver_kind"] = ""
    world.facts["place"] = place
    world.facts["gift_cfg"] = gift
    world.facts["clue_cfg"] = clue
    world.facts["helper_cfg"] = helper_cfg
    world.facts["share_cfg"] = share

    introduce(world, hero, friend, place)

    world.para()
    discover(world, hero, friend, gift, clue, place)
    wonder(world, hero, friend, clue, helper)
    temptation(world, hero, gift)

    world.para()
    choose_share(world, hero, friend, share)
    solve_mystery(world, helper, gift, clue)
    reveal_giver(world, helper, gift)

    world.para()
    shared_ending(world, hero, friend, gift, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        solved=world.get("parcel").meters["solved"] >= THRESHOLD,
        delivered_for_all=world.get("parcel").meters["delivered_for_all"] >= THRESHOLD,
        gift_shared=world.get("gift").meters["claimed_for_all"] >= THRESHOLD,
        outcome="shared_happy",
    )
    return world


PLACES = {
    "hall": Place(
        id="hall",
        label="the little town hall",
        opening="On a bright morning",
        parcel_spot="the long bench by the door",
        crowd="neighbors",
        allows_gifts={"muffins", "puzzle"},
        allows_share={"circle", "table"},
        helper_ids={"baker", "caretaker"},
        tags={"hall"},
    ),
    "garden": Place(
        id="garden",
        label="the community garden",
        opening="In the soft gold of morning",
        parcel_spot="the wooden table beside the gate",
        crowd="garden friends",
        allows_gifts={"seedlings"},
        allows_share={"circle", "row"},
        helper_ids={"gardener"},
        tags={"garden"},
    ),
    "reading_room": Place(
        id="reading_room",
        label="the reading room",
        opening="In the quiet after breakfast",
        parcel_spot="the round table under the window",
        crowd="readers",
        allows_gifts={"books", "puzzle"},
        allows_share={"circle", "table"},
        helper_ids={"librarian"},
        tags={"library"},
    ),
}

GIFTS = {
    "muffins": Gift(
        id="muffins",
        label="blueberry muffins",
        phrase="a tin of warm blueberry muffins",
        container="a round tin tied with string",
        ending="{hero} and {friend} helped pass the muffins around until the whole hall smelled sweet, and every plate had one.",
        giver_kind="baker",
        place_ids={"hall"},
        clue_ids={"flour_star"},
        shareable=True,
        tags={"muffins", "sharing"},
    ),
    "seedlings": Gift(
        id="seedlings",
        label="tiny sunflower seedlings",
        phrase="a tray of tiny sunflower seedlings",
        container="a shallow tray wrapped in paper",
        ending="{hero}, {friend}, and the other children knelt in the warm dirt and planted the seedlings in a bright row, sharing the watering can as they went.",
        giver_kind="gardener",
        place_ids={"garden"},
        clue_ids={"leaf_note"},
        shareable=True,
        tags={"plants", "sharing"},
    ),
    "books": Gift(
        id="books",
        label="picture books",
        phrase="a stack of new picture books",
        container="a paper parcel tied with blue ribbon",
        ending="Soon a soft reading circle filled {place}, and {hero} and {friend} took turns handing out the books so nobody was left waiting.",
        giver_kind="librarian",
        place_ids={"reading_room"},
        clue_ids={"silver_stamp"},
        shareable=True,
        tags={"books", "sharing"},
    ),
    "puzzle": Gift(
        id="puzzle",
        label="a giant floor puzzle",
        phrase="a giant floor puzzle in a flat box",
        container="a flat box wrapped in brown paper",
        ending="{hero} and {friend} slid puzzle pieces across the floor to anyone who needed one, and the finished picture seemed even better because so many hands had helped.",
        giver_kind="caretaker",
        place_ids={"hall", "reading_room"},
        clue_ids={"brass_key"},
        shareable=True,
        tags={"puzzle", "sharing"},
    ),
}

CLUES = {
    "flour_star": Clue(
        id="flour_star",
        label="a floury paper star",
        sight="a floury paper star tucked under the string",
        giver_kind="baker",
        gift_ids={"muffins"},
        tags={"baking"},
    ),
    "leaf_note": Clue(
        id="leaf_note",
        label="a leaf-shaped note",
        sight="a leaf-shaped note with damp soil on one corner",
        giver_kind="gardener",
        gift_ids={"seedlings"},
        tags={"garden"},
    ),
    "silver_stamp": Clue(
        id="silver_stamp",
        label="a tiny silver library stamp",
        sight="a tiny silver library stamp pressed into the ribbon",
        giver_kind="librarian",
        gift_ids={"books"},
        tags={"library"},
    ),
    "brass_key": Clue(
        id="brass_key",
        label="a brass key charm",
        sight="a brass key charm hanging from the paper string",
        giver_kind="caretaker",
        gift_ids={"puzzle"},
        tags={"building"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="Mrs. Della the baker",
        title="the baker",
        type="woman",
        place_ids={"hall"},
        knows={"flour_star"},
        giver_kinds={"baker"},
        tags={"baking"},
    ),
    "gardener": Helper(
        id="gardener",
        label="Mr. Ivo the gardener",
        title="the gardener",
        type="man",
        place_ids={"garden"},
        knows={"leaf_note"},
        giver_kinds={"gardener"},
        tags={"garden"},
    ),
    "librarian": Helper(
        id="librarian",
        label="Ms. June the librarian",
        title="the librarian",
        type="woman",
        place_ids={"reading_room"},
        knows={"silver_stamp"},
        giver_kinds={"librarian"},
        tags={"library"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="Mr. Bell the caretaker",
        title="the caretaker",
        type="man",
        place_ids={"hall", "reading_room"},
        knows={"brass_key"},
        giver_kinds={"caretaker"},
        tags={"building"},
    ),
}

SHARE_MODES = {
    "circle": ShareMode(
        id="circle",
        line='"Let\'s not hide it," {friend} said. "{hero}, let\'s call everyone into a little circle and show them the clue."',
        result="So the children invited nearby people closer, and the tiny mystery grew bright instead of secret.",
        place_ids={"hall", "garden", "reading_room"},
        tags={"sharing"},
    ),
    "table": ShareMode(
        id="table",
        line='"If we set it in the middle, everyone can look," {hero} said. Together the children carried the package to the common table and opened the room to the mystery.',
        result="Hands stayed gentle, eyes stayed sharp, and suddenly the clue belonged to everyone who cared to notice.",
        place_ids={"hall", "reading_room"},
        tags={"sharing"},
    ),
    "row": ShareMode(
        id="row",
        line='"Put it here by the path," {friend} said. "{hero}, if everyone walking in sees the clue, someone will know it."',
        result="They set the parcel where all the garden friends could pass it, and the mystery stopped being lonely at once.",
        place_ids={"garden"},
        tags={"sharing"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Ella", "Zoe", "Tess"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Arlo", "Finn", "Noah", "Eli", "Sam"]


@dataclass
class StoryParams:
    place: str
    gift: str
    clue: str
    helper: str
    share: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


KNOWLEDGE = {
    "muffins": [
        (
            "What is a muffin?",
            "A muffin is a small baked bread-cake you can hold in your hand. People often share muffins because they come as a batch, not just one piece.",
        )
    ],
    "plants": [
        (
            "What is a seedling?",
            "A seedling is a very young plant that has just started to grow. It needs careful soil, water, and light so it can grow bigger.",
        )
    ],
    "books": [
        (
            "Why is a library a good place to share books?",
            "A library is made for sharing books. Many readers can enjoy the same books one after another instead of one person keeping them all.",
        )
    ],
    "puzzle": [
        (
            "Why is a big puzzle good for sharing?",
            "A big puzzle works well for sharing because many people can look for pieces at the same time. Working together helps the picture appear faster.",
        )
    ],
    "baking": [
        (
            "What clue might make you think of a baker?",
            "A clue like flour, a paper pastry bag, or a baking mark can point to a baker. Those are things bakers use every day.",
        )
    ],
    "garden": [
        (
            "What clue might make you think of a gardener?",
            "A leaf mark or a little bit of soil can point to a gardener. Gardeners spend time with plants, dirt, and growing things.",
        )
    ],
    "library": [
        (
            "What clue might make you think of a librarian?",
            "A library stamp can point to a librarian because librarians use stamps and labels to care for books. A small mark can tell a big story.",
        )
    ],
    "building": [
        (
            "Why might a caretaker use keys?",
            "A caretaker often carries keys because they open rooms, cupboards, and gates that need looking after. A key charm can be a strong clue.",
        )
    ],
    "sharing": [
        (
            "Why can sharing help solve a mystery?",
            "Sharing lets more eyes look at the same clue. Someone else may notice the one detail you missed.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "muffins", "plants", "books", "puzzle", "baking", "garden", "library", "building"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gift = f["gift_cfg"]
    place = f["place"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old where something is delivered to {place.label} and two children solve the mystery by sharing instead of hiding.',
        f"Tell a gentle mystery about {hero.id} and {friend.id}, who find {gift.phrase} with no name on it and invite others to help read the clue.",
        'Write a child-friendly mystery with a happy ending where a secret package turns out to be for everyone, and include the word "deliver".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    place = f["place"]
    gift = f["gift_cfg"]
    clue = f["clue_cfg"]
    share = f["share_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children who found a mystery package in {place.label}. {helper.label} helps them understand the clue.",
        ),
        (
            "What made the package feel mysterious?",
            f"It had been left there with no name on the outside, even though someone had come to deliver it. The children could see {clue.sight}, but they did not yet know what it meant.",
        ),
        (
            f"Why did {hero.id} and {friend.id} choose to share the mystery?",
            f"They realized the clue was too important to keep to themselves, so they opened it to the room instead of hiding it. That sharing move gave more people a chance to notice what they could not read alone.",
        ),
        (
            f"How was the mystery solved?",
            f"They used the sharing plan called {share.id}, and that let {helper.label} see the clue clearly. {helper.pronoun('subject').capitalize()} recognized it and explained who had meant the gift for everyone.",
        ),
        (
            "What was the happy ending?",
            f"The package turned out to be {gift.phrase}, and it had been delivered for everyone to share. The ending feels happy because the children solved the mystery and then helped the whole place enjoy the surprise together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sharing"}
    tags |= set(world.facts["gift_cfg"].tags)
    tags |= set(world.facts["clue_cfg"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hall",
        gift="muffins",
        clue="flour_star",
        helper="baker",
        share="circle",
        hero="Mina",
        hero_gender="girl",
        friend="Theo",
        friend_gender="boy",
    ),
    StoryParams(
        place="garden",
        gift="seedlings",
        clue="leaf_note",
        helper="gardener",
        share="row",
        hero="Ruby",
        hero_gender="girl",
        friend="Milo",
        friend_gender="boy",
    ),
    StoryParams(
        place="reading_room",
        gift="books",
        clue="silver_stamp",
        helper="librarian",
        share="table",
        hero="Ella",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
    ),
    StoryParams(
        place="hall",
        gift="puzzle",
        clue="brass_key",
        helper="caretaker",
        share="table",
        hero="Ben",
        hero_gender="boy",
        friend="Lila",
        friend_gender="girl",
    ),
    StoryParams(
        place="reading_room",
        gift="puzzle",
        clue="brass_key",
        helper="caretaker",
        share="circle",
        hero="Nora",
        hero_gender="girl",
        friend="Sam",
        friend_gender="boy",
    ),
]


ASP_RULES = r"""
shareable_gift(G) :- gift(G), shareable(G).
fits_place(P,G) :- place(P), gift(G), allows_gift(P,G), gift_place(G,P).
matches_clue(G,C) :- gift(G), clue(C), gift_clue(G,C), clue_giver(C,K), gift_giver(G,K).
helper_fits(P,H,C,G) :- helper(H), helper_place(H,P), helper_knows(H,C),
                        clue_giver(C,K), helper_giver(H,K), gift_giver(G,K).
share_ok(P,S) :- share(S), share_place(S,P).

valid(P,G,C,H,S) :- fits_place(P,G), matches_clue(G,C), helper_fits(P,H,C,G),
                    share_ok(P,S), shareable_gift(G).

solved(P,G,C,H,S) :- valid(P,G,C,H,S).
#show valid/5.
#show solved/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for gift_id in sorted(place.allows_gifts):
            lines.append(asp.fact("allows_gift", place_id, gift_id))
        for share_id in sorted(place.allows_share):
            lines.append(asp.fact("share_place", share_id, place_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if gift.shareable:
            lines.append(asp.fact("shareable", gift_id))
        lines.append(asp.fact("gift_giver", gift_id, gift.giver_kind))
        for place_id in sorted(gift.place_ids):
            lines.append(asp.fact("gift_place", gift_id, place_id))
        for clue_id in sorted(gift.clue_ids):
            lines.append(asp.fact("gift_clue", gift_id, clue_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_giver", clue_id, clue.giver_kind))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for place_id in sorted(helper.place_ids):
            lines.append(asp.fact("helper_place", helper_id, place_id))
        for clue_id in sorted(helper.knows):
            lines.append(asp.fact("helper_knows", helper_id, clue_id))
        for giver_kind in sorted(helper.giver_kinds):
            lines.append(asp.fact("helper_giver", helper_id, giver_kind))
    for share_id in SHARE_MODES:
        lines.append(asp.fact("share", share_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.place, params.gift, params.clue, params.helper, params.share),
            "picked_solved :- chosen(P,G,C,H,S), solved(P,G,C,H,S).",
            "#show picked_solved/0.",
        ]
    )
    model = asp.one_model(asp_program(extra))
    return ("picked_solved",) in asp.atoms(model, "picked_solved")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a delivered mystery package is solved by sharing the clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--share", choices=SHARE_MODES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or None
    gift_id = args.gift or None
    clue_id = args.clue or None
    helper_id = args.helper or None
    share_id = args.share or None

    if all(v is not None for v in [place_id, gift_id, clue_id, helper_id, share_id]):
        place = PLACES[place_id]
        gift = GIFTS[gift_id]
        clue = CLUES[clue_id]
        helper = HELPERS[helper_id]
        share = SHARE_MODES[share_id]
        if not (gift_fits_place(place, gift) and clue_matches_gift(gift, clue) and helper_fits(place, helper, clue, gift) and share_allowed(place, share) and gift.shareable):
            raise StoryError(explain_rejection(place, gift, clue, helper, share))

    combos = [
        c
        for c in valid_combos()
        if (place_id is None or c[0] == place_id)
        and (gift_id is None or c[1] == gift_id)
        and (clue_id is None or c[2] == clue_id)
        and (helper_id is None or c[3] == helper_id)
        and (share_id is None or c[4] == share_id)
    ]
    if not combos:
        if place_id and gift_id and clue_id and helper_id and share_id:
            raise StoryError(
                explain_rejection(
                    PLACES[place_id],
                    GIFTS[gift_id],
                    CLUES[clue_id],
                    HELPERS[helper_id],
                    SHARE_MODES[share_id],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, gift_id, clue_id, helper_id, share_id = rng.choice(sorted(combos))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid=hero_name)

    return StoryParams(
        place=place_id,
        gift=gift_id,
        clue=clue_id,
        helper=helper_id,
        share=share_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        (params.place, PLACES, "place"),
        (params.gift, GIFTS, "gift"),
        (params.clue, CLUES, "clue"),
        (params.helper, HELPERS, "helper"),
        (params.share, SHARE_MODES, "share"),
    ]
    for key, table, label in missing:
        if key not in table:
            raise StoryError(f"(No story: unknown {label} '{key}'.)")

    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    clue = CLUES[params.clue]
    helper = HELPERS[params.helper]
    share = SHARE_MODES[params.share]
    if not (gift_fits_place(place, gift) and clue_matches_gift(gift, clue) and helper_fits(place, helper, clue, gift) and share_allowed(place, share) and gift.shareable):
        raise StoryError(explain_rejection(place, gift, clue, helper, share))

    world = tell(
        place=place,
        gift=gift,
        clue=clue,
        helper_cfg=helper,
        share=share,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        solved_py = params.place in PLACES and params.gift in GIFTS and params.clue in CLUES and params.helper in HELPERS and params.share in SHARE_MODES
        if solved_py:
            place = PLACES[params.place]
            gift = GIFTS[params.gift]
            clue = CLUES[params.clue]
            helper = HELPERS[params.helper]
            share = SHARE_MODES[params.share]
            solved_py = gift_fits_place(place, gift) and clue_matches_gift(gift, clue) and helper_fits(place, helper, clue, gift) and share_allowed(place, share) and gift.shareable
        if asp_solved(params) != solved_py:
            bad += 1
    if bad == 0:
        print(f"OK: solved parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solved checks differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, gift, clue, helper, share) combos:\n")
        for place, gift, clue, helper, share in combos:
            print(f"  {place:12} {gift:10} {clue:12} {helper:10} {share}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.hero} & {p.friend}: {p.gift} at {p.place} ({p.share})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
