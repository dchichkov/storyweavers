#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py
===============================================================================

A standalone story world about two friends, a missing object, and a small
mystery in and around a lift. The world models a child-facing mystery with
dialogue, clues, helpers, and a calm resolution.

Premise
-------
Two friends are on their way somewhere in a building when one of their things
goes missing near the lift. They notice a clue, talk it through together, ask
for help, and solve the mystery without anyone being mean on purpose. The ending
proves that friendship grew stronger because they listened, searched, and solved
the puzzle side by side.

Run it
------
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py --building apartment --item scarf --cause kitten_nest --clue pawprints --helper neighbor
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py --item lunch_tin --cause kitten_nest
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py --all
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lift_friendship_mystery_to_solve_dialogue_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Building:
    id: str
    place: str
    destination: str
    opening_image: str
    clue_spot: str
    locations: dict[str, str] = field(default_factory=dict)
    supports: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    carry: str
    texture: str
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
class Cause:
    id: str
    title: str
    place_key: str
    reason: str
    discovery: str
    needs: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    text: str
    inference: str
    fits: set[str] = field(default_factory=set)
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
    arrival: str
    speech: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
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
    def __init__(self, building: Building) -> None:
        self.building = building
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
        clone = World(self.building)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    friend = world.get("friend")
    owner.memes["worry"] += 1
    friend.memes["care"] += 1
    world.facts["mystery_started"] = True
    return []


def _r_clue_lead(world: World) -> list[str]:
    clue = world.get("clue")
    item = world.get("item")
    if clue.meters["seen"] < THRESHOLD or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("clue_lead", world.facts.get("clue_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    friend = world.get("friend")
    owner.memes["hope"] += 1
    friend.memes["focus"] += 1
    world.facts["has_lead"] = True
    return []


def _r_helper_guides(world: World) -> list[str]:
    helper = world.get("helper")
    if helper.meters["spoken"] < THRESHOLD or not world.facts.get("has_lead"):
        return []
    sig = ("helper_guides", world.facts.get("helper_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    friend = world.get("friend")
    owner.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.facts["guided_search"] = True
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    friend = world.get("friend")
    owner.memes["worry"] = 0.0
    owner.memes["relief"] += 1
    friend.memes["relief"] += 1
    owner.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.facts["solved"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_lead", tag="epistemic", apply=_r_clue_lead),
    Rule(name="helper_guides", tag="social", apply=_r_helper_guides),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def cause_works_for_item(cause: Cause, item: MissingItem) -> bool:
    return cause.needs.issubset(item.tags)


def clue_matches_cause(clue: Clue, cause: Cause) -> bool:
    return cause.id in clue.fits


def helper_matches_cause(helper: Helper, cause: Cause) -> bool:
    return cause.id in helper.helps


def building_supports_cause(building: Building, cause: Cause) -> bool:
    return cause.id in building.supports and cause.place_key in building.locations


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for building_id, building in BUILDINGS.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                if not building_supports_cause(building, cause):
                    continue
                if not cause_works_for_item(cause, item):
                    continue
                for clue_id, clue in CLUES.items():
                    if not clue_matches_cause(clue, cause):
                        continue
                    for helper_id, helper in HELPERS.items():
                        if helper_matches_cause(helper, cause):
                            combos.append((building_id, item_id, cause_id, clue_id, helper_id))
    return combos


def explain_rejection(building: Optional[Building], item: Optional[MissingItem],
                      cause: Optional[Cause], clue: Optional[Clue],
                      helper: Optional[Helper]) -> str:
    if building and cause and not building_supports_cause(building, cause):
        return (f"(No story: {building.place} has no believable {cause.title.lower()} "
                f"at its lift, so this mystery would feel fake.)")
    if item and cause and not cause_works_for_item(cause, item):
        return (f"(No story: {item.phrase} does not fit the mystery '{cause.title}'. "
                f"The world only allows causes that make sense for the missing item.)")
    if clue and cause and not clue_matches_cause(clue, cause):
        return (f"(No story: the clue '{clue.label}' does not honestly point to "
                f"'{cause.title.lower()}'. A mystery clue must match the real cause.)")
    if helper and cause and not helper_matches_cause(helper, cause):
        return (f"(No story: {helper.label} would not know enough to help with "
                f"'{cause.title.lower()}'. Pick a helper who fits that mystery.)")
    return "(No story: the requested options do not make a reasonable mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_search(world: World) -> dict:
    sim = world.copy()
    sim.get("item").meters["missing"] += 1
    propagate(sim, narrate=False)
    sim.get("clue").meters["seen"] += 1
    propagate(sim, narrate=False)
    sim.get("helper").meters["spoken"] += 1
    propagate(sim, narrate=False)
    return {
        "lead": bool(sim.facts.get("has_lead")),
        "guided_search": bool(sim.facts.get("guided_search")),
        "owner_hope": sim.get("owner").memes["hope"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, owner: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    owner.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.say(
        f"{owner.id} and {friend.id} were best friends who liked making even an ordinary ride in the lift feel like the start of an adventure."
    )
    world.say(
        f"In {world.building.place}, they were on the way to {world.building.destination}, and {owner.id} was carrying {item_cfg.phrase}."
    )
    world.say(world.building.opening_image)


def ride_lift(world: World, owner: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f'The lift doors slid shut with a soft whisper. "{item_cfg.carry}," {friend.id} said, and {owner.id} nodded and hugged the {item_cfg.label} close.'
    )
    world.say(
        f'When the lift opened again, {friend.id} stepped out first. Then {owner.id} blinked and looked down. "{item_cfg.label.capitalize()}?" {owner.pronoun().capitalize()} whispered.'
    )


def discover_missing(world: World, owner: Entity, friend: Entity) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {item.label} was gone. {owner.id}'s face fell at once."
    )
    if owner.memes["worry"] >= THRESHOLD:
        world.say(
            f'"It was right here in the lift," {owner.id} said. "{friend.id}, what if I lost it?"'
        )
    if friend.memes["care"] >= THRESHOLD:
        world.say(
            f'"Then we will find it together," {friend.id} said. "{friends_word(owner, friend)} do not leave each other alone with a mystery."'
        )


def notice_clue(world: World, owner: Entity, friend: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {world.building.clue_spot}, they noticed {clue_cfg.text}."
    )
    world.say(
        f'"That is strange," {friend.id} said. "{clue_cfg.inference}"'
    )
    if world.facts.get("has_lead"):
        world.say(
            f'"So the lift did not just swallow it," {owner.id} said. "The clue is trying to tell us something."'
        )


def friends_think(world: World, owner: Entity, friend: Entity, cause_cfg: Cause) -> None:
    world.say(
        f'"Let us think slowly," {friend.id} said. "{cause_cfg.reason}"'
    )
    world.say(
        f'"I was scared for a second," {owner.id} admitted, "but it feels better when we solve it together."'
    )


def helper_arrives(world: World, owner: Entity, friend: Entity, helper_cfg: Helper) -> None:
    helper = world.get("helper")
    pred = predict_search(world)
    helper.meters["spoken"] += 1
    propagate(world, narrate=False)
    world.say(helper_cfg.arrival)
    if pred["lead"]:
        world.say(
            f'"I heard you two talking by the lift," {helper_cfg.label} said. "{helper_cfg.speech}"'
        )
    else:
        world.say(
            f'"What happened?" {helper_cfg.label} asked.'
        )
    if world.facts.get("guided_search"):
        world.say(
            f'"Then our clue matters," {friend.id} said. "{owner.id}, come on."'
        )


def find_item(world: World, owner: Entity, friend: Entity, item_cfg: MissingItem,
              cause_cfg: Cause) -> None:
    item = world.get("item")
    place = world.building.locations[cause_cfg.place_key]
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    item.attrs["found_place"] = place
    propagate(world, narrate=False)
    world.say(
        f"They hurried to {place}. There was {cause_cfg.discovery}"
    )
    world.say(
        f'"My {item_cfg.label}!" {owner.id} cried.'
    )
    world.say(
        f"{owner.id} picked it up, and {friend.id} laughed the relieved kind of laugh that comes after a puzzle finally clicks."
    )


def explain_kindness(world: World, owner: Entity, friend: Entity, cause_cfg: Cause,
                     helper_cfg: Helper) -> None:
    world.say(
        f'"So that was the mystery," {helper_cfg.label} said. "{cause_cfg.reason}"'
    )
    world.say(
        f'"Nobody was being sneaky at all," {friend.id} said. "{owner.id}, your {world.get('item').label} was only on a little journey."'
    )
    world.say(
        f'{owner.id} smiled. "A very puzzly little journey."'
    )


def ending(world: World, owner: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    owner.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f'On the next lift ride, {owner.id} tucked {item_cfg.phrase} safely under {owner.pronoun("possessive")} arm.'
    )
    world.say(
        f'"If another mystery comes, we will solve it side by side," {friend.id} said.'
    )
    world.say(
        f'The lift hummed upward, and the two friends rode with lighter hearts than before, because the missing thing had been found and their friendship felt even steadier.'
    )


def friends_word(owner: Entity, friend: Entity) -> str:
    if owner.type == "girl" and friend.type == "girl":
        return "friends"
    if owner.type == "boy" and friend.type == "boy":
        return "friends"
    return "friends"


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(building: Building, item_cfg: MissingItem, cause_cfg: Cause,
         clue_cfg: Clue, helper_cfg: Helper, owner_name: str = "Mina",
         owner_gender: str = "girl", friend_name: str = "Owen",
         friend_gender: str = "boy") -> World:
    world = World(building)

    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["careful"],
        attrs={"friend": friend_name},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["patient"],
        attrs={"friend": owner_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="woman" if helper_cfg.id in {"neighbor", "caretaker"} else "man",
        role="helper",
        label=helper_cfg.label,
        attrs={},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        attrs={"soft": "soft" in item_cfg.tags},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        attrs={},
    ))

    world.facts.update(
        building=building,
        building_id=building.id,
        item_cfg=item_cfg,
        item_id=item_cfg.id,
        cause=cause_cfg,
        cause_id=cause_cfg.id,
        clue_cfg=clue_cfg,
        clue_id=clue_cfg.id,
        helper_cfg=helper_cfg,
        helper_id=helper_cfg.id,
        owner=owner,
        friend=friend,
        solved=False,
        has_lead=False,
        guided_search=False,
        mystery_started=False,
    )

    introduce(world, owner, friend, item_cfg)
    world.para()
    ride_lift(world, owner, friend, item_cfg)
    discover_missing(world, owner, friend)
    notice_clue(world, owner, friend, clue_cfg)
    friends_think(world, owner, friend, cause_cfg)
    world.para()
    helper_arrives(world, owner, friend, helper_cfg)
    find_item(world, owner, friend, item_cfg, cause_cfg)
    explain_kindness(world, owner, friend, cause_cfg, helper_cfg)
    world.para()
    ending(world, owner, friend, item_cfg)

    world.facts.update(
        found_place=world.get("item").attrs.get("found_place", ""),
        owner_relieved=owner.memes["relief"] >= THRESHOLD,
        friendship_grew=owner.memes["friendship"] > 1.0 and friend.memes["friendship"] > 1.0,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
BUILDINGS = {
    "apartment": Building(
        id="apartment",
        place="the old brick apartment house",
        destination="the rooftop garden",
        opening_image="The hallway lamp made a gold puddle on the floor outside the lift, and every sound seemed to wait there for a secret.",
        clue_spot="the shiny brass lift button",
        locations={
            "laundry_nook": "the laundry nook beside the lift",
            "umbrella_corner": "the umbrella corner by the front hall",
            "mail_shelf": "the mail shelf near the lobby bench",
        },
        supports={"kitten_nest", "rolling_tin", "safe_pickup"},
        tags={"building", "home"},
    ),
    "community": Building(
        id="community",
        place="the busy community center",
        destination="the craft room upstairs",
        opening_image="Posters fluttered softly on the wall by the lift, and the echo in the hall made every little sound feel important.",
        clue_spot="the silver lift door track",
        locations={
            "supply_closet": "the supply closet near the lift",
            "umbrella_corner": "the umbrella basket by the front desk",
            "mail_shelf": "the welcome shelf by the office door",
        },
        supports={"cleaning_cart", "rolling_tin", "safe_pickup"},
        tags={"building", "center"},
    ),
    "hotel": Building(
        id="hotel",
        place="the little seaside hotel",
        destination="the reading room on the top floor",
        opening_image="A striped rug lay in front of the lift, and the whole hall smelled like soap and salt air and whispers.",
        clue_spot="the polished lift mirror",
        locations={
            "supply_closet": "the linen closet by the service lift",
            "mail_shelf": "the front desk shelf",
            "umbrella_corner": "the umbrella stand under the stairs",
        },
        supports={"cleaning_cart", "safe_pickup", "rolling_tin"},
        tags={"building", "hotel"},
    ),
}

ITEMS = {
    "scarf": MissingItem(
        id="scarf",
        label="scarf",
        phrase="a red scarf with tiny silver stars",
        carry="Do not drop the scarf",
        texture="soft",
        tags={"soft", "light"},
    ),
    "lunch_tin": MissingItem(
        id="lunch_tin",
        label="lunch tin",
        phrase="a round lunch tin with a blue lid",
        carry="Hold the lunch tin tight",
        texture="round and smooth",
        tags={"round", "metal"},
    ),
    "sticker_folder": MissingItem(
        id="sticker_folder",
        label="sticker folder",
        phrase="a sticker folder full of shiny animal stickers",
        carry="Keep the folder flat",
        texture="flat and papery",
        tags={"paper", "flat"},
    ),
    "bell_bracelet": MissingItem(
        id="bell_bracelet",
        label="bell bracelet",
        phrase="a bell bracelet that gave a tiny jingle when it moved",
        carry="Listen to the bracelet jingle",
        texture="little and jangly",
        tags={"sound", "small"},
    ),
}

CAUSES = {
    "kitten_nest": Cause(
        id="kitten_nest",
        title="Kitten Nest",
        place_key="laundry_nook",
        reason="Something soft or jangly must have caught the neighbor kitten's eye, and the little rascal may have dragged it away from the lift.",
        discovery="the missing thing tucked beside a sleepy gray kitten in a warm basket.",
        needs={"soft"},
        tags={"pet", "kind"},
    ),
    "cleaning_cart": Cause(
        id="cleaning_cart",
        title="Cleaning Cart Mix-up",
        place_key="supply_closet",
        reason="A flat paper thing near the lift could easily have slid onto a cleaner's cart while the hallway was being tidied.",
        discovery="the missing thing resting on top of a folded stack of cloths, safe but very misplaced.",
        needs={"paper"},
        tags={"cleaning", "mixup"},
    ),
    "rolling_tin": Cause(
        id="rolling_tin",
        title="Rolling Tin",
        place_key="umbrella_corner",
        reason="A round thing can roll farther than anyone expects when the lift floor gives a tiny bump.",
        discovery="the missing thing hiding behind two tall umbrellas where it had quietly rolled.",
        needs={"round"},
        tags={"roll", "accident"},
    ),
    "safe_pickup": Cause(
        id="safe_pickup",
        title="Safe Pickup",
        place_key="mail_shelf",
        reason="Someone kind must have noticed the lost thing by the lift and put it somewhere safe where it could be seen.",
        discovery="the missing thing lying neatly on a shelf with nothing wrong except the surprise it had caused.",
        needs={"small"},
        tags={"kind", "care"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        text="a line of dusty pawprints leading away from the lift",
        inference="Those do not look like shoe marks. Something small with paws went this way.",
        fits={"kitten_nest"},
        tags={"pet", "tracks"},
    ),
    "lemon_smell": Clue(
        id="lemon_smell",
        label="lemon smell",
        text="a clean lemon smell and one tiny paper corner peeking from the floor edge",
        inference="That smells like fresh cleaning, and paper likes to slide where brooms and cloths go.",
        fits={"cleaning_cart"},
        tags={"cleaning", "paper"},
    ),
    "metal_clink": Clue(
        id="metal_clink",
        label="metal clink",
        text="a faint clink from somewhere near a stand of umbrellas beside the lift",
        inference="That sound is too round and tinny to be a shoe or a door.",
        fits={"rolling_tin"},
        tags={"sound", "metal"},
    ),
    "careful_note": Clue(
        id="careful_note",
        label="careful note",
        text='a neat little note by the lift mirror that said, "Found by the lift. Kept safe nearby."',
        inference="Someone helpful found it first and wanted the owner to follow the message.",
        fits={"safe_pickup"},
        tags={"note", "kind"},
    ),
    "tiny_jingle": Clue(
        id="tiny_jingle",
        label="tiny jingle",
        text="the faintest jingle from behind the laundry baskets",
        inference="That sounds like something small and shiny moved by curious paws.",
        fits={"kitten_nest"},
        tags={"sound", "pet"},
    ),
}

HELPERS = {
    "neighbor": Helper(
        id="neighbor",
        label="Mrs. Vale from downstairs",
        arrival="Just then, Mrs. Vale from downstairs stepped out of the stairwell with a basket of socks.",
        speech="I saw whiskers and a flicking tail near the lift a moment ago. If your clue points to paws, I know where to look.",
        helps={"kitten_nest", "safe_pickup"},
        tags={"neighbor", "kind"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="the caretaker",
        arrival="The caretaker came around the corner with a ring of keys and stopped when he saw their worried faces.",
        speech="When the hall gets busy by the lift, things sometimes slide onto the cleaning cart or roll into corners. Let us check the sensible places first.",
        helps={"cleaning_cart", "rolling_tin"},
        tags={"building", "help"},
    ),
    "desk_clerk": Helper(
        id="desk_clerk",
        label="the desk clerk",
        arrival="The desk clerk leaned out from the office and lowered her voice as if the hall were part of the mystery too.",
        speech="People often leave found things where everyone can see them. If someone was being careful, the shelf by the office is worth a look.",
        helps={"safe_pickup", "cleaning_cart"},
        tags={"desk", "help"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ruby", "Nora", "Ivy", "Sara", "Tia", "Maya"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Noah", "Sam", "Theo", "Max", "Ben"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    building: str
    item: str
    cause: str
    clue: str
    helper: str
    owner: str
    owner_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "lift": [("What is a lift?",
              "A lift is a small room that moves people up and down between floors in a building. Some people call it an elevator.")],
    "pet": [("Why might a kitten carry something away?",
             "Kittens are curious and playful, so they bat at soft or jangly things and sometimes drag them to a cozy spot. They are playing, not trying to be rude.")],
    "cleaning": [("Why do cleaners move things when they tidy up?",
                  "When a hallway is being cleaned, loose things can get picked up by mistake or set somewhere safe for a moment. That is why it helps to check calm, sensible places.")],
    "roll": [("Why can a round tin roll away?",
              "Round things can keep moving after a little bump, especially on a smooth floor. They may end up in a corner where nobody first expects them.")],
    "note": [("Why would someone leave a note for a lost item?",
              "A note helps the owner know that a found thing is safe. It is a kind way to turn confusion into a clue.")],
    "friendship": [("How can friends solve a mystery well together?",
                    "Friends can talk calmly, share ideas, and help each other feel brave. Working together often makes the answer easier to find.")],
}
KNOWLEDGE_ORDER = ["lift", "friendship", "pet", "cleaning", "roll", "note"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    building = f["building"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the word "lift", friendship, and dialogue.',
        f"Tell a gentle mystery where {owner.id} and {friend.id} lose {item_cfg.phrase} near a lift in {building.place} and solve it together.",
        f"Write a child-friendly story with clues, talking friends, and a kind ending where a missing {item_cfg.label} is found after a small lift mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    cause_cfg = f["cause"]
    helper_cfg = f["helper_cfg"]
    place = f.get("found_place", "a nearby spot")
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about two friends, {owner.id} and {friend.id}. They were riding in a lift when {owner.id}'s {item_cfg.label} went missing."),
        (f"What was the mystery?",
         f"The mystery was what happened to {owner.id}'s {item_cfg.label} near the lift. At first it seemed to vanish, so the children had to look for a real clue."),
        (f"What clue did they notice?",
         f"They noticed {clue_cfg.text}. That clue mattered because it pointed them toward the true answer instead of making them guess wildly."),
        (f"How did {friend.id} help {owner.id}?",
         f"{friend.id} stayed calm and said they would solve the mystery together. That helped {owner.id} feel less scared and more ready to think."),
        (f"How was the mystery solved?",
         f"{helper_cfg.label} listened to what the friends saw and shared a sensible idea. Then the children followed the clue to {place}, where they found the {item_cfg.label}."),
        (f"Why was the ending kind instead of scary?",
         f"No one had stolen the {item_cfg.label} to be mean. {cause_cfg.reason} That turns the mystery into a problem that can be understood and fixed."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lift", "friendship"}
    tags |= set(world.facts["cause"].tags)
    tags |= set(world.facts["clue_cfg"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: solved={world.facts.get('solved')} has_lead={world.facts.get('has_lead')} guided_search={world.facts.get('guided_search')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        building="apartment",
        item="scarf",
        cause="kitten_nest",
        clue="pawprints",
        helper="neighbor",
        owner="Mina",
        owner_gender="girl",
        friend="Owen",
        friend_gender="boy",
    ),
    StoryParams(
        building="community",
        item="sticker_folder",
        cause="cleaning_cart",
        clue="lemon_smell",
        helper="caretaker",
        owner="Ruby",
        owner_gender="girl",
        friend="Finn",
        friend_gender="boy",
    ),
    StoryParams(
        building="hotel",
        item="lunch_tin",
        cause="rolling_tin",
        clue="metal_clink",
        helper="caretaker",
        owner="Theo",
        owner_gender="boy",
        friend="Lena",
        friend_gender="girl",
    ),
    StoryParams(
        building="apartment",
        item="bell_bracelet",
        cause="safe_pickup",
        clue="careful_note",
        helper="neighbor",
        owner="Ivy",
        owner_gender="girl",
        friend="Ben",
        friend_gender="boy",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
item_works(I, C) :- item(I), cause(C), need(C, T), has_tag(I, T), not missing_need(I, C).
missing_need(I, C) :- need(C, T), not has_tag(I, T).

valid(B, I, C, Cl, H) :- building(B), item(I), cause(C), clue(Cl), helper(H),
                         supports(B, C), item_works(I, C),
                         clue_fits(Cl, C), helper_fits(H, C).

solved(B, I, C, Cl, H) :- valid(B, I, C, Cl, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bid, building in BUILDINGS.items():
        lines.append(asp.fact("building", bid))
        for cause_id in sorted(building.supports):
            lines.append(asp.fact("supports", bid, cause_id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("has_tag", iid, tag))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for tag in sorted(cause.needs):
            lines.append(asp.fact("need", cid, tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cause_id in sorted(clue.fits):
            lines.append(asp.fact("clue_fits", clue_id, cause_id))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for cause_id in sorted(helper.helps):
            lines.append(asp.fact("helper_fits", hid, cause_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_case(params: StoryParams) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_building", params.building),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_helper", params.helper),
        "chosen_valid :- valid(B,I,C,Cl,H), chosen_building(B), chosen_item(I), chosen_cause(C), chosen_clue(Cl), chosen_helper(H).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_valid/0."))
    return bool(model)


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        if not asp_verify_case(params):
            rc = 1
            print("MISMATCH: curated params not valid in ASP:", params)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True)
        if not buf.getvalue().strip():
            raise StoryError("emit produced no output")
        rng = random.Random(13)
        args = build_parser().parse_args([])
        params = resolve_params(args, rng)
        sample2 = generate(params)
        if not sample2.story.strip():
            raise StoryError("randomly generated story was empty")
        print("OK: smoke-tested normal generate/emit.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two friends solve a gentle mystery around a lift."
    )
    ap.add_argument("--building", choices=BUILDINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    building = BUILDINGS.get(args.building) if args.building else None
    item = ITEMS.get(args.item) if args.item else None
    cause = CAUSES.get(args.cause) if args.cause else None
    clue = CLUES.get(args.clue) if args.clue else None
    helper = HELPERS.get(args.helper) if args.helper else None

    if args.building and args.cause and not building_supports_cause(building, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if args.item and args.cause and not cause_works_for_item(cause, item):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if args.clue and args.cause and not clue_matches_cause(clue, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if args.helper and args.cause and not helper_matches_cause(helper, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.building is None or combo[0] == args.building)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.clue is None or combo[3] == args.clue)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    building_id, item_id, cause_id, clue_id, helper_id = rng.choice(sorted(combos))
    owner_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if owner_gender == "girl" else "girl" if rng.random() < 0.6 else owner_gender
    owner_name = _pick_name(rng, owner_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=owner_name)
    return StoryParams(
        building=building_id,
        item=item_id,
        cause=cause_id,
        clue=clue_id,
        helper=helper_id,
        owner=owner_name,
        owner_gender=owner_gender,
        friend=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.building not in BUILDINGS:
        raise StoryError(f"(Unknown building: {params.building})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    building = BUILDINGS[params.building]
    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    helper = HELPERS[params.helper]

    if not building_supports_cause(building, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if not cause_works_for_item(cause, item):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if not clue_matches_cause(clue, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))
    if not helper_matches_cause(helper, cause):
        raise StoryError(explain_rejection(building, item, cause, clue, helper))

    world = tell(
        building=building,
        item_cfg=item,
        cause_cfg=cause,
        clue_cfg=clue,
        helper_cfg=helper,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (building, item, cause, clue, helper) combos:\n")
        for building, item, cause, clue, helper in combos:
            print(f"  {building:10} {item:14} {cause:14} {clue:12} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.owner} & {p.friend}: {p.item} at {p.building} ({p.cause}, {p.clue}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
