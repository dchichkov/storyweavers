#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py
========================================================================

A small standalone storyworld for a child-facing whodunit: a missing parade item,
a wrong suspect, a phone-based clue, and a teamwork ending that prevents a hurt
feeling and solves the case fairly.

The seed asked for the words "phone", "prevent", and "exasperate", plus
Teamwork and a Whodunit style. Every generated story keeps those ingredients:
a child detective team works together, the mystery begins to exasperate the
room, and a phone helps prevent a hasty accusation before the real explanation
is found.

Run it
------
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py --item ribbon --mover kitten
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py --mover gust --place costume_trunk
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/phone_prevent_exasperate_teamwork_whodunit.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "woman", "coach_woman"}
        male = {"boy", "father", "man", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    event: str
    lightness: str
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
class PlaceCfg:
    id: str
    label: str
    phrase: str
    dark: bool = False
    high: bool = False
    wheeled: bool = False
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
class MoverCfg:
    id: str
    label: str
    phrase: str
    clue: str
    move_text: str
    reveal_text: str
    item_ids: set[str] = field(default_factory=set)
    place_ids: set[str] = field(default_factory=set)
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
class SuspectCfg:
    id: str
    name: str
    role_label: str
    seen_near: str
    innocent_task: str
    alibi_kind: str
    alibi_text: str
    mood: str
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
class PhoneUseCfg:
    id: str
    verb: str
    text: str
    proves: str
    clue_help_dark: bool = False
    alibi_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


def _r_exasperate(world: World) -> list[str]:
    item = world.get("item")
    suspect = world.get("suspect")
    if item.meters["missing"] < THRESHOLD or item.meters["found"] >= THRESHOLD:
        return []
    if suspect.meters["blamed"] < THRESHOLD:
        return []
    sig = ("exasperate",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.facts["kids"]:
        kid.memes["exasperation"] += 1
    world.get("coach").memes["worry"] += 1
    return ["__exasperate__"]


def _r_clear(world: World) -> list[str]:
    suspect = world.get("suspect")
    if suspect.meters["blamed"] < THRESHOLD or suspect.meters["alibi"] < THRESHOLD:
        return []
    sig = ("clear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.meters["blamed"] = 0.0
    suspect.memes["relief"] += 1
    for kid in world.facts["kids"]:
        kid.memes["fairness"] += 1
    return ["__cleared__"]


def _r_find(world: World) -> list[str]:
    item = world.get("item")
    place = world.get("place")
    if item.meters["hidden"] < THRESHOLD or place.meters["searched"] < THRESHOLD:
        return []
    if world.facts["true_place"] != place.id:
        return []
    sig = ("find", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    for kid in world.facts["kids"]:
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.get("coach").memes["relief"] += 1
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="exasperate", tag="social", apply=_r_exasperate),
    Rule(name="clear", tag="social", apply=_r_clear),
    Rule(name="find", tag="physical", apply=_r_find),
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
            if s == "__exasperate__":
                world.say("The ticking clock and the sideways glances began to exasperate everyone in the clubhouse.")
            elif s == "__cleared__":
                world.say("At once, the team realized they could prevent a hurtful mistake. The wrong suspect was innocent after all.")
            elif s == "__found__":
                world.say("There it was at last, exactly where the clues had pointed.")
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def mover_can_take(item_id: str, mover_id: str) -> bool:
    return item_id in MOVERS[mover_id].item_ids


def mover_can_hide(mover_id: str, place_id: str) -> bool:
    return place_id in MOVERS[mover_id].place_ids


def phone_matches_suspect(phone_id: str, suspect_id: str) -> bool:
    return SUSPECTS[suspect_id].alibi_kind in PHONE_USES[phone_id].alibi_kinds


def valid_combo(item_id: str, mover_id: str, place_id: str, suspect_id: str, phone_id: str) -> bool:
    return (
        item_id in ITEMS
        and mover_id in MOVERS
        and place_id in PLACES
        and suspect_id in SUSPECTS
        and phone_id in PHONE_USES
        and mover_can_take(item_id, mover_id)
        and mover_can_hide(mover_id, place_id)
        and phone_matches_suspect(phone_id, suspect_id)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for item_id in ITEMS:
        for mover_id in MOVERS:
            for place_id in PLACES:
                for suspect_id in SUSPECTS:
                    for phone_id in PHONE_USES:
                        if valid_combo(item_id, mover_id, place_id, suspect_id, phone_id):
                            out.append((item_id, mover_id, place_id, suspect_id, phone_id))
    return out


def explain_invalid(item_id: str, mover_id: str, place_id: str, suspect_id: str, phone_id: str) -> str:
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if mover_id not in MOVERS:
        return f"(No story: unknown mover '{mover_id}'.)"
    if place_id not in PLACES:
        return f"(No story: unknown hiding place '{place_id}'.)"
    if suspect_id not in SUSPECTS:
        return f"(No story: unknown suspect '{suspect_id}'.)"
    if phone_id not in PHONE_USES:
        return f"(No story: unknown phone use '{phone_id}'.)"
    if not mover_can_take(item_id, mover_id):
        return (
            f"(No story: {MOVERS[mover_id].label} would not reasonably move "
            f"{ITEMS[item_id].phrase}. Pick a lighter or looser item for that mover.)"
        )
    if not mover_can_hide(mover_id, place_id):
        return (
            f"(No story: {MOVERS[mover_id].label} would not reasonably leave the item "
            f"{PLACES[place_id].phrase}. Pick a hiding place that fits the mover's path.)"
        )
    if not phone_matches_suspect(phone_id, suspect_id):
        return (
            f"(No story: using the phone as '{phone_id}' would not honestly prove "
            f"{SUSPECTS[suspect_id].name}'s alibi. Pick a phone move that matches the suspect.)"
        )
    return "(No story: this combination is not supported.)"


# ---------------------------------------------------------------------------
# Screenplay actions
# ---------------------------------------------------------------------------
def introduce(world: World, lead: Entity, scout: Entity, thinker: Entity, coach: Entity, item: ItemCfg) -> None:
    for kid in (lead, scout, thinker):
        kid.memes["team_spirit"] = 1.0
    world.say(
        f"After school, {lead.id}, {scout.id}, and {thinker.id} met in the clubhouse to get ready for the parade. "
        f"They called themselves the Lantern Detectives, even on ordinary days."
    )
    world.say(
        f"Tonight's most important job was simple: keep {item.phrase} ready for {item.event}. "
        f"Coach {coach.id} had set it out carefully, right where everyone could admire it."
    )


def discovery(world: World, lead: Entity, coach: Entity, item: ItemCfg) -> None:
    thing = world.get("item")
    thing.meters["missing"] = 1.0
    world.say(
        f"But when {lead.id} reached for it, the spot was empty. "
        f'"The {item.label} is gone!" {lead.id} gasped.'
    )
    world.say(
        f"Coach {coach.id} looked from the empty table to the parade clock and took a slow breath."
    )


def suspicion(world: World, suspect_cfg: SuspectCfg) -> None:
    suspect = world.get("suspect")
    suspect.meters["blamed"] = 1.0
    world.say(
        f"Someone whispered that maybe {suspect_cfg.name}, {suspect_cfg.role_label}, had taken it, because {suspect_cfg.seen_near}."
    )
    propagate(world, narrate=True)


def teamwork_plan(world: World, lead: Entity, scout: Entity, thinker: Entity, phone_cfg: PhoneUseCfg) -> None:
    world.para()
    world.say(
        f'"No guessing," said {thinker.id}. "A real whodunit needs clues."'
    )
    world.say(
        f"So the three friends made a teamwork plan. {lead.id} would watch the room, "
        f"{scout.id} would follow odd little signs, and {thinker.id} would use a phone to {phone_cfg.verb}."
    )


def phone_alibi(world: World, thinker: Entity, suspect_cfg: SuspectCfg, phone_cfg: PhoneUseCfg) -> None:
    suspect = world.get("suspect")
    suspect.meters["alibi"] = 1.0
    thinker.meters["phone_used"] = 1.0
    world.say(
        f"{thinker.id} {phone_cfg.text}."
    )
    world.say(
        f"It showed that {suspect_cfg.name} had really been {suspect_cfg.innocent_task}. {phone_cfg.proves}"
    )
    propagate(world, narrate=True)


def clue_and_search(world: World, scout: Entity, mover_cfg: MoverCfg, place_cfg: PlaceCfg, phone_cfg: PhoneUseCfg) -> None:
    place = world.get("place")
    place.meters["searched"] = 1.0
    scout.meters["clue_found"] = 1.0
    if place_cfg.dark and phone_cfg.clue_help_dark:
        world.say(
            f"{scout.id} spotted {mover_cfg.clue} leading toward {place_cfg.phrase}, and the phone light helped everyone look into the dim place properly."
        )
    else:
        world.say(
            f"{scout.id} spotted {mover_cfg.clue} leading toward {place_cfg.phrase}."
        )
    world.say(
        f"The three detectives knelt, peered, and checked together instead of shoving past one another."
    )
    propagate(world, narrate=True)


def reveal(world: World, item_cfg: ItemCfg, mover_cfg: MoverCfg, place_cfg: PlaceCfg) -> None:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        raise StoryError("(Internal story error: the item was not found after the search.)")
    world.say(
        f"{mover_cfg.reveal_text} It had ended up {place_cfg.phrase}, not in any thief's pocket."
    )
    world.say(
        f"Coach {world.get('coach').id} laughed softly with relief and brushed the dust from the {item_cfg.label}."
    )


def ending(world: World, lead: Entity, scout: Entity, thinker: Entity, item_cfg: ItemCfg, suspect_cfg: SuspectCfg) -> None:
    world.para()
    world.say(
        f"{suspect_cfg.name} was invited back with a smile, and nobody looked cross anymore."
    )
    world.say(
        f'"Case closed," said {lead.id}. "{item_cfg.label.capitalize()} found, feelings saved."'
    )
    world.say(
        f"The three friends pinned the {item_cfg.label} in place together, and when the parade music began, "
        f"the Lantern Detectives stood shoulder to shoulder, proud that teamwork had solved the mystery fairly."
    )


def tell(
    item_cfg: ItemCfg,
    mover_cfg: MoverCfg,
    place_cfg: PlaceCfg,
    suspect_cfg: SuspectCfg,
    phone_cfg: PhoneUseCfg,
    lead_name: str,
    scout_name: str,
    thinker_name: str,
    coach_name: str,
    coach_type: str,
) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type="girl", role="lead"))
    scout = world.add(Entity(id=scout_name, kind="character", type="boy", role="scout"))
    thinker = world.add(Entity(id=thinker_name, kind="character", type="girl", role="thinker"))
    coach = world.add(Entity(id=coach_name, kind="character", type=coach_type, role="coach", label="coach"))
    suspect = world.add(Entity(id="suspect", kind="character", type="girl" if suspect_cfg.name.endswith(("a", "ie")) else "boy", role="suspect", label=suspect_cfg.name))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label))
    place = world.add(Entity(id="place", type="place", label=place_cfg.label))
    mover = world.add(Entity(id="mover", type="thing", label=mover_cfg.label))

    item.meters["missing"] = 0.0
    item.meters["hidden"] = 1.0
    item.meters["found"] = 0.0
    suspect.meters["blamed"] = 0.0
    suspect.meters["alibi"] = 0.0
    place.meters["searched"] = 0.0
    lead.meters["phone_used"] = 0.0
    scout.meters["clue_found"] = 0.0
    thinker.meters["phone_used"] = 0.0
    coach.memes["worry"] = 0.0
    coach.memes["relief"] = 0.0
    for kid in (lead, scout, thinker):
        kid.memes["exasperation"] = 0.0
        kid.memes["fairness"] = 0.0
        kid.memes["relief"] = 0.0
        kid.memes["joy"] = 0.0
        kid.memes["team_spirit"] = 0.0

    world.facts["true_place"] = "place"
    world.facts["kids"] = [lead, scout, thinker]
    world.facts["item_cfg"] = item_cfg
    world.facts["mover_cfg"] = mover_cfg
    world.facts["place_cfg"] = place_cfg
    world.facts["suspect_cfg"] = suspect_cfg
    world.facts["phone_cfg"] = phone_cfg
    world.facts["coach"] = coach

    introduce(world, lead, scout, thinker, coach, item_cfg)
    discovery(world, lead, coach, item_cfg)

    world.para()
    suspicion(world, suspect_cfg)
    teamwork_plan(world, lead, scout, thinker, phone_cfg)
    phone_alibi(world, thinker, suspect_cfg, phone_cfg)
    clue_and_search(world, scout, mover_cfg, place_cfg, phone_cfg)
    reveal(world, item_cfg, mover_cfg, place_cfg)
    ending(world, lead, scout, thinker, item_cfg, suspect_cfg)

    world.facts.update(
        lead=lead,
        scout=scout,
        thinker=thinker,
        suspect=world.get("suspect"),
        coach=coach,
        item=world.get("item"),
        place=world.get("place"),
        mover=world.get("mover"),
        prevented_hurt=all(k.memes["fairness"] >= THRESHOLD for k in (lead, scout, thinker)),
        found=world.get("item").meters["found"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
ITEMS = {
    "ribbon": ItemCfg(
        id="ribbon",
        label="blue ribbon",
        phrase="the blue ribbon for the lantern banner",
        event="the opening march",
        lightness="light",
        tags={"ribbon", "parade"},
    ),
    "badge": ItemCfg(
        id="badge",
        label="star badge",
        phrase="the brass star badge for the detective cape",
        event="the clubhouse salute",
        lightness="light",
        tags={"badge", "costume"},
    ),
    "whistle": ItemCfg(
        id="whistle",
        label="silver whistle",
        phrase="the silver whistle for the first drumbeat",
        event="the first drumbeat",
        lightness="small",
        tags={"whistle", "music"},
    ),
}

PLACES = {
    "under_curtain": PlaceCfg(
        id="under_curtain",
        label="stage curtain",
        phrase="under the velvet curtain",
        dark=True,
        tags={"curtain", "dark"},
    ),
    "costume_trunk": PlaceCfg(
        id="costume_trunk",
        label="costume trunk",
        phrase="inside the half-open costume trunk",
        dark=True,
        tags={"trunk", "dark"},
    ),
    "trophy_shelf": PlaceCfg(
        id="trophy_shelf",
        label="trophy shelf",
        phrase="behind the tall trophy shelf",
        high=True,
        tags={"shelf"},
    ),
    "under_bench": PlaceCfg(
        id="under_bench",
        label="bench",
        phrase="under the long hallway bench",
        tags={"bench"},
    ),
    "supply_box": PlaceCfg(
        id="supply_box",
        label="supply box",
        phrase="inside a paper supply box",
        dark=True,
        tags={"box", "dark"},
    ),
    "rolling_cart": PlaceCfg(
        id="rolling_cart",
        label="rolling cart",
        phrase="on the lower tray of the rolling cart",
        wheeled=True,
        tags={"cart"},
    ),
}

MOVERS = {
    "kitten": MoverCfg(
        id="kitten",
        label="the clubhouse kitten",
        phrase="the clubhouse kitten",
        clue="tiny paw prints and one bent thread",
        move_text="batted it away in play",
        reveal_text="A little mew came from the side of the room, and everyone understood: the clubhouse kitten had batted it away while chasing the dangling end",
        item_ids={"ribbon", "badge"},
        place_ids={"under_curtain", "costume_trunk", "under_bench"},
        tags={"kitten", "paw_prints"},
    ),
    "gust": MoverCfg(
        id="gust",
        label="a gust from the open window",
        phrase="a gust from the open window",
        clue="a fluttering paper star and the cold draft from the window",
        move_text="blew it off the table",
        reveal_text="No sneaky thief had been there at all. A gust from the open window had whisked it away",
        item_ids={"ribbon", "badge"},
        place_ids={"trophy_shelf", "under_bench"},
        tags={"wind", "window"},
    ),
    "cleanup_cart": MoverCfg(
        id="cleanup_cart",
        label="the cleanup cart",
        phrase="the cleanup cart",
        clue="a squeaky wheel track and a stripe of chalk dust",
        move_text="nudged it along while the room was being tidied",
        reveal_text="The clue fit perfectly: the cleanup cart had nudged it along while someone was sweeping, carrying it by accident",
        item_ids={"badge", "whistle"},
        place_ids={"supply_box", "rolling_cart"},
        tags={"cart", "dust"},
    ),
}

SUSPECTS = {
    "mara": SuspectCfg(
        id="mara",
        name="Mara",
        role_label="the paint captain",
        seen_near="her apron had been seen near the table",
        innocent_task="mixing blue paint in the art room",
        alibi_kind="photo",
        alibi_text="a phone photo with a clean timestamp",
        mood="patient",
        tags={"photo", "art"},
    ),
    "owen": SuspectCfg(
        id="owen",
        name="Owen",
        role_label="the drum helper",
        seen_near="his drumsticks had been left on a chair nearby",
        innocent_task="counting beats with the band teacher",
        alibi_kind="call",
        alibi_text="a quick phone call to the band teacher",
        mood="nervous",
        tags={"call", "music"},
    ),
    "tia": SuspectCfg(
        id="tia",
        name="Tia",
        role_label="the garden monitor",
        seen_near="her watering can had been resting by the door",
        innocent_task="tying up bean vines in the courtyard",
        alibi_kind="message",
        alibi_text="a phone message with a fresh picture from the courtyard",
        mood="quiet",
        tags={"message", "garden"},
    ),
}

PHONE_USES = {
    "photo": PhoneUseCfg(
        id="photo",
        verb="check a saved photo",
        text="opened a phone photo from a few minutes earlier and zoomed in",
        proves="The timestamp made the room go quiet, because it proved she could not have taken the missing thing then.",
        clue_help_dark=False,
        alibi_kinds={"photo"},
        tags={"phone", "photo"},
    ),
    "call": PhoneUseCfg(
        id="call",
        verb="make a quick phone call",
        text="borrowed Coach's phone and made a quick call",
        proves="The answer came back at once, calm and clear, and it proved he had been somewhere else when the item vanished.",
        clue_help_dark=False,
        alibi_kinds={"call"},
        tags={"phone", "call"},
    ),
    "message": PhoneUseCfg(
        id="message",
        verb="check a phone message",
        text="checked a phone message that had just arrived",
        proves="The fresh picture in the message proved she had been outside, busy with a different job at the very same time.",
        clue_help_dark=True,
        alibi_kinds={"message"},
        tags={"phone", "message"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Nora", "Ava", "Zoe", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Max", "Eli", "Finn", "Noah"]
COACH_NAMES = ["Mrs. Bell", "Mr. Reed", "Coach June", "Coach Sam"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    item: str
    mover: str
    place: str
    suspect: str
    phone_use: str
    lead_name: str
    scout_name: str
    thinker_name: str
    coach_name: str
    coach_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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
    "phone": [
        (
            "How can a phone help in a mystery?",
            "A phone can help people check a photo, make a call, or read a message to learn what really happened. It is useful when it helps people look for the truth instead of making wild guesses."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful when something is missing?",
            "Teamwork lets different people do different jobs at the same time, like checking clues and asking careful questions. That makes it easier to solve the problem fairly and quickly."
        )
    ],
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where people try to figure out who caused a problem. Good whodunits use clues instead of blaming someone too fast."
        )
    ],
    "kitten": [
        (
            "Why might a kitten move something shiny or dangly?",
            "Kittens like to bat at little moving things because they feel like toys. A ribbon or badge can slide away if a kitten pats it."
        )
    ],
    "wind": [
        (
            "How can wind move a light object indoors?",
            "If a window is open, a strong gust can push or flutter light things off a table. That is why papers and ribbons sometimes blow away."
        )
    ],
    "cart": [
        (
            "How can a rolling cart move something by accident?",
            "A rolling cart can bump, drag, or sweep a small object along if the object is near its wheels or trays. The person using the cart may not even notice."
        )
    ],
    "fairness": [
        (
            "Why should we prevent a wrong accusation?",
            "A wrong accusation can hurt someone's feelings and make the real problem harder to solve. It is fairer to look for proof first."
        )
    ],
}
KNOWLEDGE_ORDER = ["phone", "teamwork", "whodunit", "fairness", "kitten", "wind", "cart"]


def generation_prompts(world: World) -> list[str]:
    item_cfg = world.facts["item_cfg"]
    suspect_cfg = world.facts["suspect_cfg"]
    phone_cfg = world.facts["phone_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "phone", "prevent", and "exasperate", and make teamwork solve the case.',
        f"Tell a child-friendly mystery where a parade {item_cfg.label} goes missing, everyone nearly blames {suspect_cfg.name}, and a phone is used to {phone_cfg.verb}.",
        f"Write a short teamwork mystery in which children prevent a wrong accusation by checking clues before deciding who did it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    lead = world.facts["lead"]
    scout = world.facts["scout"]
    thinker = world.facts["thinker"]
    coach = world.facts["coach"]
    suspect_cfg = world.facts["suspect_cfg"]
    item_cfg = world.facts["item_cfg"]
    mover_cfg = world.facts["mover_cfg"]
    place_cfg = world.facts["place_cfg"]
    phone_cfg = world.facts["phone_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three child detectives, {lead.id}, {scout.id}, and {thinker.id}, with Coach {coach.id} at the clubhouse. They are trying to find the missing {item_cfg.label} before the parade begins."
        ),
        (
            f"Why did the missing {item_cfg.label} matter?",
            f"It mattered because the {item_cfg.label} was needed for {item_cfg.event}. The clock was ticking, so the mystery felt big right away."
        ),
        (
            f"Why did everyone start to suspect {suspect_cfg.name}?",
            f"People looked at {suspect_cfg.name} because {suspect_cfg.seen_near}. That made the room tense, and the worry began to exasperate everyone."
        ),
        (
            f"How did the phone help prevent a mistake?",
            f"{thinker.id} used the phone to {phone_cfg.verb}, and that gave the team real proof about {suspect_cfg.name}. Because of that proof, they could prevent a wrong accusation instead of blaming someone innocent."
        ),
        (
            "How did teamwork solve the mystery?",
            f"The children split the jobs: one watched, one followed clues, and one checked the phone. Working together let them clear the suspect and search the right place without wasting time."
        ),
        (
            f"Where was the {item_cfg.label}, and what had really happened?",
            f"They found it {place_cfg.phrase}. {mover_cfg.reveal_text}, so the mystery was an accident, not stealing."
        ),
    ]
    if world.facts.get("prevented_hurt"):
        qa.append(
            (
                f"How did {suspect_cfg.name} feel after the truth came out?",
                f"{suspect_cfg.name} could relax because the team learned the truth in time. Finding proof first protected {suspect_cfg.pronoun if hasattr(suspect_cfg, 'pronoun') else suspect_cfg.name}'s feelings and made the ending kinder."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mover_cfg = world.facts["mover_cfg"]
    tags = {"phone", "teamwork", "whodunit", "fairness"}
    if mover_cfg.id == "kitten":
        tags.add("kitten")
    elif mover_cfg.id == "gust":
        tags.add("wind")
    else:
        tags.add("cart")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        item="ribbon",
        mover="kitten",
        place="under_curtain",
        suspect="owen",
        phone_use="call",
        lead_name="Lina",
        scout_name="Ben",
        thinker_name="Mia",
        coach_name="Mrs. Bell",
        coach_type="coach_woman",
    ),
    StoryParams(
        item="badge",
        mover="gust",
        place="trophy_shelf",
        suspect="mara",
        phone_use="photo",
        lead_name="Ruby",
        scout_name="Theo",
        thinker_name="Ava",
        coach_name="Mr. Reed",
        coach_type="coach_man",
    ),
    StoryParams(
        item="whistle",
        mover="cleanup_cart",
        place="supply_box",
        suspect="tia",
        phone_use="message",
        lead_name="Nora",
        scout_name="Finn",
        thinker_name="Zoe",
        coach_name="Coach Sam",
        coach_type="coach_man",
    ),
    StoryParams(
        item="badge",
        mover="kitten",
        place="costume_trunk",
        suspect="mara",
        phone_use="photo",
        lead_name="Ava",
        scout_name="Max",
        thinker_name="Ruby",
        coach_name="Coach June",
        coach_type="coach_woman",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_move(M, I) :- mover(M), item(I), mover_item(M, I).
can_hide(M, P) :- mover(M), place(P), mover_place(M, P).
phone_matches(S, Ph) :- suspect(S), phone_use(Ph), alibi_kind(S, K), phone_alibi(Ph, K).

valid(I, M, P, S, Ph) :- item(I), mover(M), place(P), suspect(S), phone_use(Ph),
                         can_move(M, I), can_hide(M, P), phone_matches(S, Ph).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for mover_id, mover in MOVERS.items():
        lines.append(asp.fact("mover", mover_id))
        for item_id in sorted(mover.item_ids):
            lines.append(asp.fact("mover_item", mover_id, item_id))
        for place_id in sorted(mover.place_ids):
            lines.append(asp.fact("mover_place", mover_id, place_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("alibi_kind", suspect_id, suspect.alibi_kind))
    for phone_id, phone in PHONE_USES.items():
        lines.append(asp.fact("phone_use", phone_id))
        for kind in sorted(phone.alibi_kinds):
            lines.append(asp.fact("phone_alibi", phone_id, kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "phone" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missing the required phone beat.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Default generation did not produce a full sample.)")
        print("OK: default resolve/generate path succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child-facing whodunit storyworld: a missing parade item, a phone clue, and teamwork."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--phone-use", dest="phone_use", choices=PHONE_USES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include generated Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(
        getattr(args, name) is not None
        for name in ("item", "mover", "place", "suspect", "phone_use")
    ):
        if not valid_combo(args.item, args.mover, args.place, args.suspect, args.phone_use):
            raise StoryError(explain_invalid(args.item, args.mover, args.place, args.suspect, args.phone_use))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.mover is None or combo[1] == args.mover)
        and (args.place is None or combo[2] == args.place)
        and (args.suspect is None or combo[3] == args.suspect)
        and (args.phone_use is None or combo[4] == args.phone_use)
    ]
    if not combos:
        item_id = args.item or next(iter(ITEMS))
        mover_id = args.mover or next(iter(MOVERS))
        place_id = args.place or next(iter(PLACES))
        suspect_id = args.suspect or next(iter(SUSPECTS))
        phone_id = args.phone_use or next(iter(PHONE_USES))
        raise StoryError(explain_invalid(item_id, mover_id, place_id, suspect_id, phone_id))

    item_id, mover_id, place_id, suspect_id, phone_id = rng.choice(sorted(combos))

    girl_pool = GIRL_NAMES[:]
    boy_pool = BOY_NAMES[:]
    lead_name = rng.choice(girl_pool)
    thinker_name = rng.choice([n for n in girl_pool if n != lead_name])
    scout_name = rng.choice(boy_pool)
    coach_name = rng.choice(COACH_NAMES)
    coach_type = "coach_woman" if any(token in coach_name for token in ("Mrs.", "June")) else "coach_man"

    return StoryParams(
        item=item_id,
        mover=mover_id,
        place=place_id,
        suspect=suspect_id,
        phone_use=phone_id,
        lead_name=lead_name,
        scout_name=scout_name,
        thinker_name=thinker_name,
        coach_name=coach_name,
        coach_type=coach_type,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.item, params.mover, params.place, params.suspect, params.phone_use):
        raise StoryError(explain_invalid(params.item, params.mover, params.place, params.suspect, params.phone_use))

    world = tell(
        item_cfg=ITEMS[params.item],
        mover_cfg=MOVERS[params.mover],
        place_cfg=PLACES[params.place],
        suspect_cfg=SUSPECTS[params.suspect],
        phone_cfg=PHONE_USES[params.phone_use],
        lead_name=params.lead_name,
        scout_name=params.scout_name,
        thinker_name=params.thinker_name,
        coach_name=params.coach_name,
        coach_type=params.coach_type,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, mover, place, suspect, phone_use) combos:\n")
        for item_id, mover_id, place_id, suspect_id, phone_id in combos:
            print(f"  {item_id:8} {mover_id:12} {place_id:14} {suspect_id:6} {phone_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.item} / {p.mover} / {p.place} / {p.suspect} / {p.phone_use}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
