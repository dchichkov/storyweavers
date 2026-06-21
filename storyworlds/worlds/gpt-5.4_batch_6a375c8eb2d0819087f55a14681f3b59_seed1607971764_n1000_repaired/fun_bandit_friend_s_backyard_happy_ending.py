#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py
=======================================================================

A standalone story world for a tiny "space adventure in a friend's backyard"
domain: two children turn a backyard into a moon base, something important goes
missing, a sneaky "bandit" seems to be in the dark, and the children solve the
mystery safely with help, clues, and a bright ending.

The stories are deliberately small and constraint-checked:

* The setting is always a friend's backyard.
* The play frame is always space-adventure flavored.
* The word "fun" appears naturally in the prose.
* The word "bandit" appears naturally in the prose.
* The middle includes suspense: rustling leaves, a vanished item, and a careful search.
* The ending is happy and state-driven: the item is recovered, the children learn
  to search safely, and the last image proves what changed.

Reasonableness constraint
-------------------------
Not every critter, missing item, and hiding place make sense together. This
world models a small gate:

* a raccoon can take a snack tin or a foil map and can hide under the deck or by the shed
* a crow can snatch a shiny badge or foil map and can hide in a tree fork
* a squirrel can drag only a snack tin and can stash it by the shed

The search tool must also fit the hiding place:

* flashlight works for dark places
* step stool works for high places
* wagon ramp works for low places without crawling

This gives a clear problem/fix pair instead of weak free mixing.

Run it
------
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py --bandit crow --item badge
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py --bandit squirrel --item badge
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py --qa
    python storyworlds/worlds/gpt-5.4/fun_bandit_friend_s_backyard_happy_ending.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    can_carry: set[str] = field(default_factory=set)
    likes: set[str] = field(default_factory=set)
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    yard_phrase: str
    launch_line: str
    goal: str
    sendoff: str
    rhyme_open: str
    rhyme_close: str
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


@dataclass
class BanditSpec:
    id: str
    label: str
    phrase: str
    rustle: str
    steps: str
    likes: set[str] = field(default_factory=set)
    can_carry: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    article: str
    attract: set[str] = field(default_factory=set)
    needed_for: str = ""
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    quality: str
    dark: bool = False
    high: bool = False
    low: bool = False
    fits: set[str] = field(default_factory=set)
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
class SearchTool:
    id: str
    label: str
    phrase: str
    reaches: set[str] = field(default_factory=set)
    success: str = ""
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
class Reward:
    id: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return [e for e in self.entities.values() if e.role in {"host", "guest"}]

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


# ---------------------------------------------------------------------------
# Causal rules
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


def _r_missing_brings_suspense(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing_suspense", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["suspense"] += 1
    out.append("__suspense__")
    return out


def _r_clue_builds_hope(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["clue_found"] < THRESHOLD:
        return out
    sig = ("clue_hope", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["hope"] += 1
        kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1.0)
    out.append("__hope__")
    return out


def _r_found_resolves(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return out
    sig = ("found_resolves", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["suspense"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_brings_suspense", tag="emotion", apply=_r_missing_brings_suspense),
    Rule(name="clue_builds_hope", tag="emotion", apply=_r_clue_builds_hope),
    Rule(name="found_resolves", tag="emotion", apply=_r_found_resolves),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def hazard_at_risk(bandit: BanditSpec, item: LostItem, place: HidingPlace, tool: SearchTool) -> bool:
    return (
        item.id in bandit.can_carry
        and item.id in bandit.likes
        and bandit.id in place.fits
        and place.quality in tool.reaches
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for bandit_id, bandit in BANDITS.items():
        for item_id, item in ITEMS.items():
            for place_id, place in PLACES.items():
                for tool_id, tool in TOOLS.items():
                    if hazard_at_risk(bandit, item, place, tool):
                        combos.append((bandit_id, item_id, place_id, tool_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_search(world: World, place_id: str, tool_id: str) -> dict:
    sim = world.copy()
    place = PLACES[place_id]
    tool = TOOLS[tool_id]
    sim.facts["chosen_place"] = place.id
    sim.facts["chosen_tool"] = tool.id
    item = sim.get("item")
    if place.quality in tool.reaches:
        item.meters["clue_found"] += 1
        item.meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "hope": sum(k.memes["hope"] for k in sim.kids()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_play(world: World, host: Entity, guest: Entity, mission: Mission, reward: Reward) -> None:
    for kid in (host, guest):
        kid.memes["joy"] += 1
        kid.memes["fun"] += 1
    world.say(
        f"At {host.id}'s friend's backyard, {host.id} and {guest.id} made a cardboard rocket beside "
        f"{mission.yard_phrase}. They were not just playing outside. They were space explorers with "
        f"{reward.phrase} waiting for whoever finished the mission."
    )
    world.say(
        f'{host.id} tapped the side of the rocket and grinned. "{mission.launch_line}"'
    )
    world.say(
        f'{guest.id} laughed. "This is fun. We will zoom by moonlight soon!"'
    )


def show_item(world: World, guest: Entity, item: Entity, item_cfg: LostItem, mission: Mission) -> None:
    item.meters["safe"] = 1.0
    world.say(
        f"{guest.id} set {item_cfg.article} {item_cfg.label} on an upside-down crate and said it was "
        f"needed for {mission.goal}. Without it, the launch could not feel complete."
    )


def rustle_and_loss(world: World, bandit: Entity, item: Entity, bandit_cfg: BanditSpec, item_cfg: LostItem) -> None:
    item.meters["missing"] += 1
    item.meters["safe"] = 0.0
    item.attrs["carrier"] = bandit.id
    propagate(world, narrate=False)
    world.say(
        f"Then the leaves gave {bandit_cfg.rustle}, and something moved where the fence cast a wiggly shadow. "
        f"For one quiet second, neither child breathed."
    )
    world.say(
        f"When they looked back, {item_cfg.article} {item_cfg.label} was gone. {guest_name(world)} whispered, "
        f'"A bandit!"'
    )


def guest_name(world: World) -> str:
    return world.facts["guest"].id


def host_name(world: World) -> str:
    return world.facts["host"].id


def worry(world: World, host: Entity, guest: Entity, parent: Entity, item_cfg: LostItem, bandit_cfg: BanditSpec) -> None:
    host.memes["fear"] += 1
    guest.memes["fear"] += 1
    world.say(
        f'{host.id} held still and listened to {bandit_cfg.steps}. "{item_cfg.label.capitalize()} means our mission," '
        f'{host.pronoun()} said. "{parent.label_word.capitalize()} said we must stay where feet are safe and eyes can see."'
    )


def rhyme_plan(world: World, host: Entity, guest: Entity, tool_cfg: SearchTool, place_cfg: HidingPlace, mission: Mission) -> None:
    pred = predict_search(world, place_cfg.id, tool_cfg.id)
    world.facts["predicted_found"] = pred["found"]
    host.memes["care"] += 1
    guest.memes["care"] += 1
    world.say(
        f'{guest.id} took a brave breath and sang a little rhyme: "{mission.rhyme_open}"'
    )
    world.say(
        f'{host.id} pointed to {tool_cfg.phrase}. "We can search the safe way. We will use {tool_cfg.phrase} and look by '
        f'{place_cfg.phrase}, not with hands in the dark."'
    )


def call_for_help(world: World, parent: Entity, place_cfg: HidingPlace) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came to the porch light and listened. Instead of scolding, "
        f"{parent.pronoun()} nodded and stayed nearby while they checked {place_cfg.phrase}."
    )


def search(world: World, host: Entity, guest: Entity, item: Entity, bandit: Entity,
           item_cfg: LostItem, bandit_cfg: BanditSpec, place_cfg: HidingPlace, tool_cfg: SearchTool) -> None:
    item.meters["clue_found"] += 1
    bandit.meters["noticed"] += 1
    propagate(world, narrate=False)
    clue = ""
    if bandit_cfg.id == "raccoon":
        clue = "tiny muddy handprints"
    elif bandit_cfg.id == "crow":
        clue = "one black feather and a bright scrape on the bark"
    else:
        clue = "little chewed leaves and a fast flicking tail"
    world.say(
        f"Near {place_cfg.phrase}, they spotted {clue}. The children leaned close, but they kept their shoes on the path and "
        f"used {tool_cfg.phrase} just as planned."
    )
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    item.attrs["carrier"] = ""
    item.attrs["location"] = place_cfg.id
    bandit.meters["retreated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {tool_cfg.success}, and there it was: {item_cfg.article} {item_cfg.label}, tucked by {place_cfg.phrase} while "
        f"the little {bandit_cfg.label} blinked at them from a safe distance."
    )


def gentle_turn(world: World, host: Entity, guest: Entity, bandit_cfg: BanditSpec, item_cfg: LostItem) -> None:
    for kid in (host, guest):
        kid.memes["kindness"] += 1
    if bandit_cfg.id == "raccoon":
        reason = "the foil had flashed like treasure"
    elif bandit_cfg.id == "crow":
        reason = "the shine had looked like a bit of sky"
    else:
        reason = "the tin had smelled like a snack"
    world.say(
        f'"So that was our bandit," {guest.id} said. They could see now that the animal had not been mean at all; '
        f"{reason}. The mystery felt smaller once they understood it."
    )


def happy_ending(world: World, host: Entity, guest: Entity, parent: Entity, mission: Mission,
                 reward: Reward, item_cfg: LostItem) -> None:
    for kid in (host, guest):
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. "You were careful, you asked for help, and you solved it together."'
    )
    world.say(
        f'{host.id} set the {item_cfg.label} back on the crate. {guest.id} clapped and finished the rhyme: "{mission.rhyme_close}"'
    )
    world.say(
        f"They counted down from ten, whooshed around the rocket, and shared {reward.phrase}. {reward.ending} "
        f"The backyard still felt like space, but now it felt bright and safe too."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(mission: Mission, bandit_cfg: BanditSpec, item_cfg: LostItem, place_cfg: HidingPlace,
         tool_cfg: SearchTool, reward_cfg: Reward, host_name_value: str = "Mia",
         host_gender: str = "girl", guest_name_value: str = "Leo", guest_gender: str = "boy",
         parent_type: str = "mother", twilight: str = "dusk") -> World:
    world = World()
    host = world.add(Entity(id=host_name_value, kind="character", type=host_gender, role="host", label=host_name_value))
    guest = world.add(Entity(id=guest_name_value, kind="character", type=guest_gender, role="guest", label=guest_name_value))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bandit = world.add(Entity(
        id="bandit",
        kind="animal",
        type="animal",
        role="bandit",
        label=bandit_cfg.label,
        can_carry=set(bandit_cfg.can_carry),
        likes=set(bandit_cfg.likes),
        tags=set(bandit_cfg.tags),
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="mission_item",
        role="item",
        label=item_cfg.label,
        attrs={"carrier": "", "location": "crate"},
        tags=set(item_cfg.tags),
    ))
    world.add(Entity(id="yard", kind="thing", type="place", role="place", label="friend's backyard"))
    world.facts.update(
        host=host,
        guest=guest,
        parent=parent,
        bandit_cfg=bandit_cfg,
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        tool_cfg=tool_cfg,
        reward_cfg=reward_cfg,
        mission=mission,
        twilight=twilight,
    )

    setup_play(world, host, guest, mission, reward_cfg)
    show_item(world, guest, item, item_cfg, mission)

    world.para()
    rustle_and_loss(world, bandit, item, bandit_cfg, item_cfg)
    worry(world, host, guest, parent, item_cfg, bandit_cfg)
    rhyme_plan(world, host, guest, tool_cfg, place_cfg, mission)
    call_for_help(world, parent, place_cfg)

    world.para()
    search(world, host, guest, item, bandit, item_cfg, bandit_cfg, place_cfg, tool_cfg)
    gentle_turn(world, host, guest, bandit_cfg, item_cfg)
    happy_ending(world, host, guest, parent, mission, reward_cfg, item_cfg)

    world.facts.update(
        found=item.meters["found"] >= THRESHOLD,
        suspense=max(host.memes["suspense"], guest.memes["suspense"]) >= 0.0,
        asked_for_help=True,
        safe_search=True,
        recovered_item=item.label,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
MISSIONS = {
    "moon_rescue": Mission(
        id="moon_rescue",
        yard_phrase="the bean patch and the little plum tree",
        launch_line="Captain Comet to Star Scout: ready for moon rescue!",
        goal="the moon rescue launch",
        sendoff="blasted off around the flower beds",
        rhyme_open="Moon so bright, guide our sight.",
        rhyme_close="Moon so bright, all is right.",
    ),
}

BANDITS = {
    "raccoon": BanditSpec(
        id="raccoon",
        label="raccoon",
        phrase="a masked raccoon",
        rustle="a crinkle-crinkle sound",
        steps="soft scratchy steps by the deck",
        likes={"map", "tin"},
        can_carry={"map", "tin"},
        tags={"raccoon", "night_animal"},
    ),
    "crow": BanditSpec(
        id="crow",
        label="crow",
        phrase="a glossy crow",
        rustle="a flap-flap in the branches",
        steps="a quick hop and wing-shiver overhead",
        likes={"badge", "map"},
        can_carry={"badge", "map"},
        tags={"crow", "bird"},
    ),
    "squirrel": BanditSpec(
        id="squirrel",
        label="squirrel",
        phrase="a stripy squirrel",
        rustle="a skitter-skitter in the ivy",
        steps="tiny pattering feet by the shed",
        likes={"tin"},
        can_carry={"tin"},
        tags={"squirrel"},
    ),
}

ITEMS = {
    "badge": LostItem(
        id="badge",
        label="star badge",
        phrase="a silver star badge",
        article="the",
        attract={"shiny"},
        needed_for="the captain's suit",
        tags={"badge", "shiny"},
    ),
    "map": LostItem(
        id="map",
        label="foil moon map",
        phrase="a foil moon map",
        article="the",
        attract={"shiny", "crinkly"},
        needed_for="the launch path",
        tags={"map", "foil"},
    ),
    "tin": LostItem(
        id="tin",
        label="comet-cookie tin",
        phrase="a comet-cookie tin",
        article="the",
        attract={"snack", "shiny"},
        needed_for="the victory snack",
        tags={"cookies", "tin"},
    ),
}

PLACES = {
    "deck": HidingPlace(
        id="deck",
        label="under the deck",
        phrase="the dark space under the deck",
        quality="dark",
        dark=True,
        fits={"raccoon"},
        tags={"deck", "dark_place"},
    ),
    "tree": HidingPlace(
        id="tree",
        label="the plum-tree fork",
        phrase="the fork of the little plum tree",
        quality="high",
        high=True,
        fits={"crow"},
        tags={"tree", "high_place"},
    ),
    "shed": HidingPlace(
        id="shed",
        label="by the shed step",
        phrase="the gap beside the shed step",
        quality="low",
        low=True,
        fits={"raccoon", "squirrel"},
        tags={"shed", "low_place"},
    ),
}

TOOLS = {
    "flashlight": SearchTool(
        id="flashlight",
        label="flashlight",
        phrase="the flashlight",
        reaches={"dark"},
        success="the flashlight beam slid between the boards",
        tags={"flashlight", "safe_search"},
    ),
    "stool": SearchTool(
        id="stool",
        label="step stool",
        phrase="the little step stool",
        reaches={"high"},
        success="from the little step stool they could peek into the fork",
        tags={"stool", "safe_search"},
    ),
    "ramp": SearchTool(
        id="ramp",
        label="wagon ramp",
        phrase="the wagon ramp",
        reaches={"low"},
        success="the wagon ramp let them nudge the leaves aside without crawling in",
        tags={"ramp", "safe_search"},
    ),
}

REWARDS = {
    "sticks": Reward(
        id="sticks",
        phrase="cold star-shaped fruit sticks",
        ending="Their giggles rang past the fence like tiny rocket bells.",
        tags={"snack"},
    ),
    "juice": Reward(
        id="juice",
        phrase="grape juice in paper cups",
        ending="Even the porch light seemed to wink at their landing.",
        tags={"drink"},
    ),
    "cookies": Reward(
        id="cookies",
        phrase="moon cookies with sugar dust",
        ending="They nibbled and laughed until the shadows no longer felt mysterious.",
        tags={"cookies"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Zoe", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Finn", "Noah", "Eli", "Theo", "Sam", "Jack"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str = "moon_rescue"
    bandit: str = "raccoon"
    item: str = "map"
    place: str = "deck"
    tool: str = "flashlight"
    reward: str = "cookies"
    host_name: str = "Mia"
    host_gender: str = "girl"
    guest_name: str = "Leo"
    guest_gender: str = "boy"
    parent: str = "mother"
    twilight: str = "dusk"
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
    "raccoon": [(
        "Why do people sometimes call a raccoon a bandit?",
        "People sometimes call a raccoon a bandit because the dark fur around its eyes looks like a mask. Raccoons are curious animals and they often pick up interesting things."
    )],
    "crow": [(
        "Why might a crow take something shiny?",
        "Crows notice bright, shiny things very quickly. A shiny object can catch a crow's eye the same way a sparkle catches yours."
    )],
    "squirrel": [(
        "Why would a squirrel drag off a snack tin?",
        "A squirrel looks for food and follows good smells. If a tin smells like treats, it may try to pull it somewhere safe."
    )],
    "flashlight": [(
        "Why is a flashlight helpful in the dark?",
        "A flashlight helps you see into dark places without putting your hands where you cannot see. Seeing first is a safe way to search."
    )],
    "stool": [(
        "Why use a step stool instead of climbing something wobbly?",
        "A step stool gives you a steady place to stand. That makes it safer than climbing a loose crate or a branch."
    )],
    "ramp": [(
        "Why is using a tool safer than reaching into a tight gap?",
        "A tool lets you check a tight space from farther away. That keeps fingers out of dark little hiding spots."
    )],
    "space": [(
        "What is a pretend space mission?",
        "A pretend space mission is a game where children imagine they are astronauts or explorers. Pretend play can feel exciting because ordinary places become new worlds."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme uses words with matching sounds, like bright and night. Rhymes can help a line feel playful and easy to remember."
    )],
}
KNOWLEDGE_ORDER = ["space", "rhyme", "raccoon", "crow", "squirrel", "flashlight", "stool", "ramp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    item = f["item_cfg"]
    bandit = f["bandit_cfg"]
    place = f["place_cfg"]
    return [
        f'Write a short story for a 3-to-5-year-old in a friend\'s backyard that includes the words "fun" and "bandit". Make it feel like a space adventure with a happy ending.',
        f"Tell a suspenseful but gentle backyard space story where {host.id} and {guest.id} lose a {item.label}, think a {bandit.label} bandit took it, and search safely near {place.phrase}.",
        f"Write a child-friendly story with a little rhyme, a missing mission item, and a bright ending where the children solve the mystery together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    parent = f["parent"]
    item = f["item_cfg"]
    bandit = f["bandit_cfg"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    reward = f["reward_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {host.id} and {guest.id}, two children playing a space mission in a friend's backyard. {parent.label_word.capitalize()} stays nearby and helps them search safely."
        ),
        (
            f"What went missing?",
            f"The {item.label} went missing during their pretend launch. It mattered because they needed it for {item.needed_for}."
        ),
        (
            f"Why did the children think there was a bandit?",
            f"They heard {bandit.rustle} and then saw that the {item.label} was gone. That sudden change made the mystery feel spooky and suspenseful for a moment."
        ),
        (
            "How did they search safely?",
            f"They called to {parent.label_word} and stayed where they could see clearly. Then they used {tool.phrase} near {place.phrase} instead of grabbing into the dark."
        ),
        (
            f"Where did they find the {item.label}?",
            f"They found it by {place.phrase}. The clue there matched the little animal they had heard moving."
        ),
        (
            f"Why wasn't the animal really a bad bandit?",
            f"It had not tried to ruin the game. It only took the {item.label} because it looked interesting or smelled tempting, so the children understood the mistake and felt calmer."
        ),
        (
            "How did the story end?",
            f"It ended happily: the children got the {item.label} back, finished their space mission, and shared {reward.phrase}. The last part feels bright because the backyard is still fun, but now it feels safe too."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"space", "rhyme", world.facts["bandit_cfg"].id, world.facts["tool_cfg"].id}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.can_carry:
            bits.append(f"can_carry={sorted(e.can_carry)}")
        if e.likes:
            bits.append(f"likes={sorted(e.likes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon_rescue",
        bandit="raccoon",
        item="map",
        place="deck",
        tool="flashlight",
        reward="cookies",
        host_name="Mia",
        host_gender="girl",
        guest_name="Leo",
        guest_gender="boy",
        parent="mother",
        twilight="dusk",
    ),
    StoryParams(
        mission="moon_rescue",
        bandit="crow",
        item="badge",
        place="tree",
        tool="stool",
        reward="juice",
        host_name="Noah",
        host_gender="boy",
        guest_name="Luna",
        guest_gender="girl",
        parent="father",
        twilight="dusk",
    ),
    StoryParams(
        mission="moon_rescue",
        bandit="squirrel",
        item="tin",
        place="shed",
        tool="ramp",
        reward="sticks",
        host_name="Ivy",
        host_gender="girl",
        guest_name="Finn",
        guest_gender="boy",
        parent="mother",
        twilight="dusk",
    ),
]


def explain_rejection(bandit: BanditSpec, item: LostItem, place: HidingPlace, tool: SearchTool) -> str:
    if item.id not in bandit.can_carry or item.id not in bandit.likes:
        return (
            f"(No story: a {bandit.label} would not sensibly run off with the {item.label} here. "
            f"Pick an item that this little backyard bandit would actually notice or carry.)"
        )
    if bandit.id not in place.fits:
        return (
            f"(No story: {place.phrase} is not a sensible hiding place for a {bandit.label} in this world.)"
        )
    if place.quality not in tool.reaches:
        return (
            f"(No story: {tool.label} is the wrong search tool for {place.phrase}. "
            f"The safe fix should match the kind of place being checked.)"
        )
    return "(No story: this combination does not form a grounded mystery.)"


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
takes(B, I) :- bandit(B), item(I), likes(B, I), carries(B, I).
safe_tool(P, T) :- place(P), tool(T), quality(P, Q), reaches(T, Q).
valid(B, I, P, T) :- bandit(B), item(I), place(P), tool(T),
                     takes(B, I), fits(P, B), safe_tool(P, T).
resolved(B, I, P, T) :- valid(B, I, P, T).
#show valid/4.
#show resolved/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for bandit_id, bandit in BANDITS.items():
        lines.append(asp.fact("bandit", bandit_id))
        for item_id in sorted(bandit.likes):
            lines.append(asp.fact("likes", bandit_id, item_id))
        for item_id in sorted(bandit.can_carry):
            lines.append(asp.fact("carries", bandit_id, item_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("quality", place_id, place.quality))
        for bandit_id in sorted(place.fits):
            lines.append(asp.fact("fits", place_id, bandit_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for quality in sorted(tool.reaches):
            lines.append(asp.fact("reaches", tool_id, quality))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "bandit" not in sample.story.lower() or "fun" not in sample.story.lower():
            raise StoryError("smoke test story missing required words or empty output")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            _ = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"GENERATE FAILED for seed {seed}: {err}")
            break
    else:
        print("OK: seeded generation smoke tests passed.")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a space game in a friend's backyard, a missing item, and a gentle backyard bandit."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--bandit", choices=BANDITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--host-name")
    ap.add_argument("--guest-name")
    ap.add_argument("--host-gender", choices=["girl", "boy"])
    ap.add_argument("--guest-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bandit and args.item and args.place and args.tool:
        if not hazard_at_risk(BANDITS[args.bandit], ITEMS[args.item], PLACES[args.place], TOOLS[args.tool]):
            raise StoryError(explain_rejection(BANDITS[args.bandit], ITEMS[args.item], PLACES[args.place], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.bandit is None or combo[0] == args.bandit)
        and (args.item is None or combo[1] == args.item)
        and (args.place is None or combo[2] == args.place)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        if args.bandit and args.item and args.place and args.tool:
            raise StoryError(explain_rejection(BANDITS[args.bandit], ITEMS[args.item], PLACES[args.place], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    bandit_id, item_id, place_id, tool_id = rng.choice(sorted(combos))
    host_gender = args.host_gender or rng.choice(["girl", "boy"])
    guest_gender = args.guest_gender or rng.choice(["girl", "boy"])
    host_name = args.host_name or pick_name(rng, host_gender)
    guest_name = args.guest_name or pick_name(rng, guest_gender, avoid=host_name)
    return StoryParams(
        mission=args.mission or "moon_rescue",
        bandit=bandit_id,
        item=item_id,
        place=place_id,
        tool=tool_id,
        reward=args.reward or rng.choice(sorted(REWARDS)),
        host_name=host_name,
        host_gender=host_gender,
        guest_name=guest_name,
        guest_gender=guest_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        twilight="dusk",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        bandit = BANDITS[params.bandit]
        item = ITEMS[params.item]
        place = PLACES[params.place]
        tool = TOOLS[params.tool]
        reward = REWARDS[params.reward]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not hazard_at_risk(bandit, item, place, tool):
        raise StoryError(explain_rejection(bandit, item, place, tool))

    world = tell(
        mission=mission,
        bandit_cfg=bandit,
        item_cfg=item,
        place_cfg=place,
        tool_cfg=tool,
        reward_cfg=reward,
        host_name_value=params.host_name,
        host_gender=params.host_gender,
        guest_name_value=params.guest_name,
        guest_gender=params.guest_gender,
        parent_type=params.parent,
        twilight=params.twilight,
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
        print(f"{len(combos)} compatible (bandit, item, place, tool) combos:\n")
        for bandit, item, place, tool in combos:
            print(f"  {bandit:8} {item:5} {place:5} {tool}")
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
            header = f"### {p.host_name} & {p.guest_name}: {p.bandit} / {p.item} / {p.place} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
