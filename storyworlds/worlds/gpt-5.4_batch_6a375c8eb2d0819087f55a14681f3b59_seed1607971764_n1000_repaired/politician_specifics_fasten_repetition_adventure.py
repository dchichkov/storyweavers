#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py
==============================================================================

A standalone storyworld for a tiny adventure domain: two children carry the
important specifics for a town celebration to a kind politician at the hill
office. The central tension is whether the message carrier gets fastened before
a windy dash through town.

The story uses repetition as part of the world state: the helper keeps repeating
a short fastening chant, and that chant can either prevent the trouble or return
during the recovery.

Run it
------
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py --route bridge --carrier satchel --fastener buckle
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py --carrier folder --message scroll
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py --all
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/politician_specifics_fasten_repetition_adventure.py --verify
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
COURAGE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    supports_pages: bool = False
    supports_scroll: bool = False
    can_fasten: bool = False
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mayor"}
        male = {"boy", "man", "father"}
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
class Route:
    id: str
    path: str
    image: str
    risk: int
    landmark: str
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
class Message:
    id: str
    label: str
    shape: str
    specifics: str
    phrase: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    holds: set[str]
    hold_power: int
    can_fasten: bool
    closure_word: str
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
class Fastener:
    id: str
    label: str
    grip: int
    action: str
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
class Wind:
    id: str
    line: str
    risk: int
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
class PoliticianCfg:
    id: str
    name: str
    title: str
    office: str
    help_text: str
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
class StoryParams:
    route: str
    message: str
    carrier: str
    fastener: str
    wind: str
    politician: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    relation: str = "friends"
    hero_age: int = 6
    helper_age: int = 5
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
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_loose_scatter(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    note = world.get("message")
    if carrier.meters["fastened"] >= THRESHOLD:
        return out
    risk = world.facts["travel_risk"]
    if risk <= carrier.meters["hold_power"]:
        return out
    sig = ("scatter", risk, int(carrier.meters["hold_power"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    note.meters["scattered"] += 1
    note.meters["delayed"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__scatter__")
    return out


def _r_recovered_secure(world: World) -> list[str]:
    out: list[str] = []
    note = world.get("message")
    carrier = world.get("carrier")
    if note.meters["gathered"] < THRESHOLD or carrier.meters["fastened"] < THRESHOLD:
        return out
    sig = ("secure_after_gather",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    note.meters["safe"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    out.append("__secure__")
    return out


CAUSAL_RULES = [
    Rule(name="loose_scatter", tag="physical", apply=_r_loose_scatter),
    Rule(name="recovered_secure", tag="physical", apply=_r_recovered_secure),
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
        for sent in produced:
            world.say(sent)
    return produced


ROUTES = {
    "bridge": Route(
        id="bridge",
        path="the little bridge over the stream",
        image="where the boards hummed over the water",
        risk=3,
        landmark="the stream bridge",
        tags={"bridge", "windy_walk"},
    ),
    "market": Route(
        id="market",
        path="the market lane between striped stalls",
        image="where bright awnings snapped above baskets of oranges",
        risk=2,
        landmark="the market lane",
        tags={"market", "windy_walk"},
    ),
    "tower": Route(
        id="tower",
        path="the clock-tower steps",
        image="where the bells made the air jump",
        risk=4,
        landmark="the clock tower",
        tags={"steps", "windy_walk"},
    ),
}

MESSAGES = {
    "pages": Message(
        id="pages",
        label="pages",
        shape="pages",
        specifics="the lantern parade specifics: where the drummers should stand, when the paper boats would float, and which lane the children would march through",
        phrase="three bright pages of parade specifics",
        tags={"specifics", "paper"},
    ),
    "scroll": Message(
        id="scroll",
        label="scroll",
        shape="scroll",
        specifics="the adventure-map specifics for the town treasure walk: the red gate, the fern tunnel, and the final bell rope",
        phrase="a rolled scroll of treasure-walk specifics",
        tags={"specifics", "map"},
    ),
    "cards": Message(
        id="cards",
        label="cards",
        shape="cards",
        specifics="the picnic race specifics: team colors, clue stops, and the last shady table near the hill",
        phrase="a ring of little planning cards full of specifics",
        tags={"specifics", "cards"},
    ),
}

CARRIERS = {
    "satchel": Carrier(
        id="satchel",
        label="satchel",
        phrase="a small explorer satchel",
        holds={"pages", "cards"},
        hold_power=2,
        can_fasten=True,
        closure_word="flap",
        tags={"satchel"},
    ),
    "tube": Carrier(
        id="tube",
        label="map tube",
        phrase="a red map tube",
        holds={"scroll"},
        hold_power=3,
        can_fasten=True,
        closure_word="cap",
        tags={"tube"},
    ),
    "folder": Carrier(
        id="folder",
        label="folder",
        phrase="a cardboard folder",
        holds={"pages", "cards"},
        hold_power=1,
        can_fasten=True,
        closure_word="band",
        tags={"folder"},
    ),
}

FASTENERS = {
    "buckle": Fastener(
        id="buckle",
        label="buckle",
        grip=3,
        action="clicked the buckle shut",
        tags={"buckle", "fasten"},
    ),
    "cord": Fastener(
        id="cord",
        label="red cord",
        grip=2,
        action="wrapped the red cord twice and tied it tight",
        tags={"cord", "fasten"},
    ),
    "clip": Fastener(
        id="clip",
        label="silver clip",
        grip=1,
        action="pinched the silver clip over the edge",
        tags={"clip", "fasten"},
    ),
}

WINDS = {
    "breezy": Wind(
        id="breezy",
        line="A playful breeze skipped ahead of them and flipped the bunting in the square.",
        risk=1,
        tags={"wind", "breezy"},
    ),
    "gusty": Wind(
        id="gusty",
        line="Sharp gusts chased each other through town and tugged at every loose corner.",
        risk=2,
        tags={"wind", "gusty"},
    ),
    "blustery": Wind(
        id="blustery",
        line="The whole hill was blustery, and the air kept reaching for hats, ribbons, and papers.",
        risk=3,
        tags={"wind", "blustery"},
    ),
}

POLITICIANS = {
    "mayor": PoliticianCfg(
        id="mayor",
        name="Mayor Alma",
        title="mayor",
        office="the little hill office",
        help_text="knelt right on the cobbles and helped scoop the papers before they could slide away",
        tags={"politician", "mayor"},
    ),
    "councilor": PoliticianCfg(
        id="councilor",
        name="Councilor Ivo",
        title="councilor",
        office="the green-door council room",
        help_text="held the office door wide, then helped gather every page with quick, careful hands",
        tags={"politician", "councilor"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Ava", "Nora", "Zoe", "Tess", "Ivy", "Mina"]
BOY_NAMES = ["Finn", "Leo", "Max", "Ben", "Theo", "Eli", "Sam", "Noah"]
TRAITS = ["careful", "steady", "thoughtful", "brave", "curious", "quick"]


def fits(carrier: Carrier, message: Message) -> bool:
    return message.shape in carrier.holds and carrier.can_fasten


def travel_risk(route: Route, wind: Wind) -> int:
    return route.risk + wind.risk


def careful_level(trait: str) -> int:
    return 5 if trait in CAREFUL_TRAITS else 3


def would_heed(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    older_helper = relation == "siblings" and helper_age > hero_age
    return older_helper and careful_level(trait) + 1 > int(COURAGE_INIT)


def secure_power(carrier: Carrier, fastener: Fastener) -> int:
    return carrier.hold_power + fastener.grip


def will_scatter(carrier: Carrier, route: Route, wind: Wind) -> bool:
    return travel_risk(route, wind) > carrier.hold_power


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for route_id in ROUTES:
        for message_id, message in MESSAGES.items():
            for carrier_id, carrier in CARRIERS.items():
                if not fits(carrier, message):
                    continue
                for fastener_id in FASTENERS:
                    for wind_id in WINDS:
                        for politician_id in POLITICIANS:
                            combos.append(
                                (route_id, message_id, carrier_id, fastener_id, wind_id, politician_id)
                            )
    return combos


def explain_rejection(carrier: Carrier, message: Message) -> str:
    return (
        f"(No story: {carrier.phrase} does not sensibly carry {message.phrase}. "
        f"This adventure needs a carrier that really fits the message and can fasten it closed.)"
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def introduction(world: World, hero: Entity, helper: Entity, route: Route, message: Message,
                 politician: PoliticianCfg) -> None:
    for kid in (hero, helper):
        kid.memes["excitement"] += 1
    world.say(
        f"On festival morning, {hero.id} and {helper.id} were chosen for a real adventure. "
        f"They had to carry {message.phrase} to {politician.name}, the kind {politician.title} "
        f"and busiest politician in town."
    )
    world.say(
        f"The path ran by {route.path}, {route.image}, and to the door of {politician.office}."
    )
    world.say(
        f"Inside the message were {message.specifics}."
    )


def setup_gear(world: World, hero: Entity, helper: Entity, carrier: Carrier, fastener: Fastener) -> None:
    world.say(
        f"{hero.id} tucked the message into {carrier.phrase}. "
        f"{helper.id} held up the {fastener.label} and said, "
        f'"Fasten it first, fasten it first, fasten it first."'
    )
    helper.memes["caution"] += 1
    world.facts["chant"] = "Fasten it first, fasten it first, fasten it first."


def wind_warning(world: World, helper: Entity, route: Route, wind: Wind) -> None:
    world.say(wind.line)
    world.say(
        f'{helper.id} pointed along {route.path}. "That way gets windy. '
        f'If the {world.get("carrier").label} stays loose, the specifics may fly."'
    )


def fasten_now(world: World, hero: Entity, carrier: Entity, fastener: Fastener) -> None:
    carrier.meters["fastened"] += 1
    carrier.meters["hold_power"] = float(carrier.attrs["base_hold"] + fastener.grip)
    hero.memes["prudence"] += 1
    world.say(
        f"So {hero.id} slowed down, {fastener.action}, and pressed the {carrier.attrs['closure_word']} once more "
        f"to make sure it held."
    )


def dash_anyway(world: World, hero: Entity, route: Route) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"We can make it!" {hero.id} said, and dashed toward {route.landmark} with the carrier still loose.'
    )


def cross_town(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    for kid in (hero, helper):
        kid.memes["courage"] += 1
    world.say(
        f"They hurried along {route.path} like explorers on a secret mission, boots tapping fast."
    )


def scatter_scene(world: World, message: Message) -> None:
    world.say(
        f"Halfway there, a gust caught the open carrier. The {message.label} leapt into the air "
        f"like startled birds, and the precious specifics whirled over the stones."
    )


def lucky_scene(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"A hard gust tugged at the loose carrier, but the message stayed wedged inside. "
        f"{hero.id} and {helper.id} froze for one breath, suddenly understanding how close they had come."
    )


def gather_with_politician(world: World, politician_ent: Entity, helper: Entity, fastener: Fastener) -> None:
    note = world.get("message")
    carrier = world.get("carrier")
    note.meters["gathered"] += 1
    carrier.meters["fastened"] += 1
    carrier.meters["hold_power"] = float(carrier.attrs["base_hold"] + fastener.grip)
    helper.memes["caution"] += 1
    world.say(
        f"{politician_ent.id}, who had just stepped outside, {politician_ent.attrs['help_text']}."
    )
    world.say(
        f'{helper.id} repeated, "{world.facts["chant"]}" This time even the wind seemed to hear it.'
    )
    world.say(
        f"Together they stacked every piece in order, and {politician_ent.id} showed {hero.id} how to {fastener.label} the carrier so nothing could slip free again."
    )
    note.meters["delivered"] += 1


def arrival(world: World, hero: Entity, helper: Entity, politician_ent: Entity, message: Message,
            early_fastened: bool) -> None:
    if early_fastened:
        world.say(
            f"When they reached {politician_ent.attrs['office']}, the message was still neat and dry. "
            f"{politician_ent.id} smiled at the tidy bundle of specifics."
        )
    else:
        world.say(
            f"At last they reached {politician_ent.attrs['office']} with the message safe again. "
            f"The politician took the pages with both hands, glad not a single important detail was missing."
        )
    politician_ent.memes["gratitude"] += 1
    for kid in (hero, helper):
        kid.memes["pride"] += 1
        kid.memes["relief"] += 1
    world.get("message").meters["delivered"] += 1


def lesson_end(world: World, hero: Entity, helper: Entity, politician_ent: Entity, fastener: Fastener,
               route: Route) -> None:
    world.say(
        f'"You were brave couriers," {politician_ent.id} said, "and brave couriers remember the little things too. '
        f'Specifics matter, and so does the moment you fasten a bag before the wind gets a vote."'
    )
    world.say(
        f"On the walk home, {hero.id} tapped the {fastener.label}, and {helper.id} sang the chant once more: "
        f'"{world.facts["chant"]}"'
    )
    world.say(
        f"From then on, whenever an errand led past {route.landmark}, they checked every strap and flap before they ran, "
        f"and the adventure felt steadier because of it."
    )


def tell(route: Route, message: Message, carrier_cfg: Carrier, fastener: Fastener,
         wind: Wind, politician: PoliticianCfg, hero_name: str = "Lina", hero_gender: str = "girl",
         helper_name: str = "Finn", helper_gender: str = "boy", trait: str = "careful",
         relation: str = "friends", hero_age: int = 6, helper_age: int = 5) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    politician_ent = world.add(Entity(
        id=politician.name,
        kind="character",
        type="mayor" if politician.id == "mayor" else "woman",
        role="politician",
        attrs={"office": politician.office, "help_text": politician.help_text},
    ))
    carrier = world.add(Entity(
        id="carrier",
        type="carrier",
        label=carrier_cfg.label,
        supports_pages="pages" in carrier_cfg.holds,
        supports_scroll="scroll" in carrier_cfg.holds,
        can_fasten=carrier_cfg.can_fasten,
        attrs={"base_hold": carrier_cfg.hold_power, "closure_word": carrier_cfg.closure_word},
    ))
    message_ent = world.add(Entity(
        id="message",
        type="message",
        label=message.label,
        attrs={"shape": message.shape},
    ))

    carrier.meters["hold_power"] = float(carrier_cfg.hold_power)
    world.facts["travel_risk"] = travel_risk(route, wind)
    world.facts["route"] = route
    world.facts["message_cfg"] = message
    world.facts["carrier_cfg"] = carrier_cfg
    world.facts["fastener"] = fastener
    world.facts["wind"] = wind
    world.facts["politician_cfg"] = politician
    world.facts["relation"] = relation
    world.facts["scatter"] = False
    world.facts["chant"] = ""

    introduction(world, hero, helper, route, message, politician)
    setup_gear(world, hero, helper, carrier_cfg, fastener)
    world.para()
    wind_warning(world, helper, route, wind)

    early_fastened = would_heed(relation, hero_age, helper_age, trait)
    world.facts["early_fastened"] = early_fastened
    scatter = False
    lucky = False

    if early_fastened:
        fasten_now(world, hero, carrier, fastener)
        world.para()
        cross_town(world, hero, helper, route)
        arrival(world, hero, helper, politician_ent, message, early_fastened=True)
    else:
        dash_anyway(world, hero, route)
        world.para()
        cross_town(world, hero, helper, route)
        propagate(world, narrate=False)
        if message_ent.meters["scattered"] >= THRESHOLD:
            scatter = True
            world.facts["scatter"] = True
            scatter_scene(world, message)
            world.para()
            gather_with_politician(world, politician_ent, helper, fastener)
        else:
            lucky = True
            fasten_now(world, hero, carrier, fastener)
            world.get("message").meters["safe"] += 1
            lucky_scene(world, hero, helper)
            world.para()
            arrival(world, hero, helper, politician_ent, message, early_fastened=False)

    if scatter:
        world.para()
        lesson_end(world, hero, helper, politician_ent, fastener, route)
        outcome = "recovered"
    elif early_fastened:
        world.para()
        lesson_end(world, hero, helper, politician_ent, fastener, route)
        outcome = "fastened_early"
    else:
        world.para()
        lesson_end(world, hero, helper, politician_ent, fastener, route)
        outcome = "lucky"

    world.facts.update(
        hero=hero,
        helper=helper,
        politician=politician_ent,
        outcome=outcome,
        lucky=lucky,
        message=message_ent,
        carrier=carrier,
    )
    return world


KNOWLEDGE = {
    "politician": [
        (
            "What is a politician?",
            "A politician is a person who helps make plans and decisions for a town, city, or country. Some politicians, like mayors, listen to people and help organize public things."
        )
    ],
    "specifics": [
        (
            "What are specifics?",
            "Specifics are the small important details about something. They tell exactly what should happen, where it should happen, or when it should happen."
        )
    ],
    "fasten": [
        (
            "What does fasten mean?",
            "To fasten something means to close it or secure it so it stays in place. You can fasten a buckle, a cord, or a clip."
        )
    ],
    "wind": [
        (
            "Why can wind be a problem for papers?",
            "Wind can lift light papers and push them away very quickly. That is why loose pages should be tucked in and fastened before you carry them outside."
        )
    ],
    "bridge": [
        (
            "Why might a bridge feel windier than a quiet room?",
            "A bridge is open on the sides, so the air can move across it more easily. That can make gusts feel stronger there."
        )
    ],
    "market": [
        (
            "Why do cloth awnings flap in the wind?",
            "Awnings are made of cloth, and moving air pushes against cloth easily. When the wind tugs them, they flap and snap."
        )
    ],
    "steps": [
        (
            "Why can carrying things on steps be tricky?",
            "Steps make you lift your feet and balance carefully. If something is loose while you climb, it is easier to fumble it."
        )
    ],
    "satchel": [
        (
            "What is a satchel?",
            "A satchel is a small bag you carry with a strap. It is useful for errands because it can hold papers or tools."
        )
    ],
    "tube": [
        (
            "What is a map tube for?",
            "A map tube is a long round case for rolled paper. It helps keep a scroll from bending or flying away."
        )
    ],
    "folder": [
        (
            "What is a folder used for?",
            "A folder holds flat papers together. It works best when it is closed tightly so the papers do not slide out."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "politician",
    "specifics",
    "fasten",
    "wind",
    "bridge",
    "market",
    "steps",
    "satchel",
    "tube",
    "folder",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    route = f["route"]
    message = f["message_cfg"]
    politician = f["politician_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old where two children carry {message.phrase} '
        f'to a politician named {politician.name}. Include the words "politician", "specifics", and "fasten".'
    )
    if outcome == "fastened_early":
        return [
            base,
            f"Tell a windy errand adventure where {helper.id} repeats a fastening chant, and {hero.id} listens before the trouble starts.",
            f"Write a gentle adventure in which a child learns that little specifics matter and chooses to fasten the bag before running across {route.landmark}.",
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell an adventure where {hero.id} runs with a loose carrier, the specifics scatter in the wind, and a kind politician helps the children gather them again.",
            f"Write a story with repetition in which a helper keeps saying 'Fasten it first' until the lesson finally sticks.",
        ]
    return [
        base,
        f"Tell an adventure where the children almost lose the message in the wind, then stop and fasten it in time.",
        f"Write a story that uses repetition and a near-miss to teach why fastening a carrier matters on an errand.",
    ]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    politician = f["politician"]
    route = f["route"]
    message_cfg = f["message_cfg"]
    carrier_cfg = f["carrier_cfg"]
    fastener = f["fastener"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper, relation)}, {hero.id} and {helper.id}, carrying important specifics to {politician.id}, a town politician. Their errand feels like an adventure because the whole town path matters."
        ),
        (
            "What were they carrying?",
            f"They were carrying {message_cfg.phrase}. The message held the specifics for a town event, so every little detail mattered."
        ),
        (
            f"Why did {helper.id} keep repeating the chant?",
            f"{helper.id} could see that the wind and the route might shake a loose carrier open. The repetition was a warning meant to help {hero.id} remember to fasten it before the specifics could fly away."
        ),
    ]
    if f["outcome"] == "fastened_early":
        qa.append(
            (
                f"What changed the adventure before anything went wrong?",
                f"{hero.id} listened to {helper.id} and fastened the {carrier_cfg.label} before running on. That small choice kept the message neat all the way to the politician's door."
            )
        )
    elif f["outcome"] == "recovered":
        qa.append(
            (
                "What happened in the middle of the story?",
                f"A gust caught the loose {carrier_cfg.label}, and the message scattered. Then {politician.id} helped gather it, and the children fastened the carrier properly so the specifics stayed safe."
            )
        )
        qa.append(
            (
                f"How did the politician help?",
                f"{politician.id} stopped to help scoop up the message instead of scolding the children. That gave them time to put the details back in order and fasten the carrier the right way."
            )
        )
    else:
        qa.append(
            (
                "Did they lose the message?",
                f"No, but they came very close. The near-miss frightened them into stopping, and then {hero.id} fastened the {carrier_cfg.label} before the wind could steal the specifics."
            )
        )
    qa.append(
        (
            "What did they learn at the end?",
            f"They learned that brave adventures still need careful little steps. Fastening a carrier before running can protect important specifics just as much as courage does."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"politician", "specifics", "fasten", "wind"}
    tags |= set(f["route"].tags)
    tags |= set(f["carrier_cfg"].tags)
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


ASP_RULES = r"""
% A carrier is compatible when it can hold the message shape.
fits(C, M) :- holds(C, S), shape(M, S), can_fasten(C).

valid(R, M, C, F, W, P) :-
    route(R), message(M), carrier(C), fastener(F), wind(W), politician(P),
    fits(C, M).

travel_risk(V) :- chosen_route(R), route_risk(R, A), chosen_wind(W), wind_risk(W, B), V = A + B.
secure_power(V) :- chosen_carrier(C), hold_power(C, A), chosen_fastener(F), grip(F, B), V = A + B.

older_helper :- relation(siblings), helper_age(H), hero_age(G), H > G.
careful_bonus(5) :- chosen_trait(T), careful_trait(T).
careful_bonus(3) :- chosen_trait(T), not careful_trait(T).
heed :- older_helper, careful_bonus(B), bravery_init(C), B + 1 > C.

scatter :- not heed, chosen_carrier(C), travel_risk(R), hold_power(C, H), R > H.
lucky :- not heed, chosen_carrier(C), travel_risk(R), hold_power(C, H), R <= H.

outcome(fastened_early) :- heed.
outcome(recovered) :- scatter.
outcome(lucky) :- lucky.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_risk", route_id, route.risk))
    for message_id, message in MESSAGES.items():
        lines.append(asp.fact("message", message_id))
        lines.append(asp.fact("shape", message_id, message.shape))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        lines.append(asp.fact("hold_power", carrier_id, carrier.hold_power))
        if carrier.can_fasten:
            lines.append(asp.fact("can_fasten", carrier_id))
        for shape in sorted(carrier.holds):
            lines.append(asp.fact("holds", carrier_id, shape))
    for fastener_id, fastener in FASTENERS.items():
        lines.append(asp.fact("fastener", fastener_id))
        lines.append(asp.fact("grip", fastener_id, fastener.grip))
    for wind_id, wind in WINDS.items():
        lines.append(asp.fact("wind", wind_id))
        lines.append(asp.fact("wind_risk", wind_id, wind.risk))
    for politician_id in POLITICIANS:
        lines.append(asp.fact("politician", politician_id))
    lines.append(asp.fact("bravery_init", int(COURAGE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_message", params.message),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_fastener", params.fastener),
            asp.fact("chosen_wind", params.wind),
            asp.fact("chosen_politician", params.politician),
            asp.fact("chosen_trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.relation, params.hero_age, params.helper_age, params.trait):
        return "fastened_early"
    if will_scatter(CARRIERS[params.carrier], ROUTES[params.route], WINDS[params.wind]):
        return "recovered"
    return "lucky"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a windy town errand, a politician, and the small adventure of fastening a carrier in time."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--fastener", choices=FASTENERS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--politician", choices=POLITICIANS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.message and args.carrier:
        message = MESSAGES[args.message]
        carrier = CARRIERS[args.carrier]
        if not fits(carrier, message):
            raise StoryError(explain_rejection(carrier, message))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.message is None or combo[1] == args.message)
        and (args.carrier is None or combo[2] == args.carrier)
        and (args.fastener is None or combo[3] == args.fastener)
        and (args.wind is None or combo[4] == args.wind)
        and (args.politician is None or combo[5] == args.politician)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route, message, carrier, fastener, wind, politician = rng.choice(sorted(combos))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        route=route,
        message=message,
        carrier=carrier,
        fastener=fastener,
        wind=wind,
        politician=politician,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.message not in MESSAGES:
        raise StoryError(f"(Unknown message: {params.message})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.fastener not in FASTENERS:
        raise StoryError(f"(Unknown fastener: {params.fastener})")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind: {params.wind})")
    if params.politician not in POLITICIANS:
        raise StoryError(f"(Unknown politician: {params.politician})")

    carrier = CARRIERS[params.carrier]
    message = MESSAGES[params.message]
    if not fits(carrier, message):
        raise StoryError(explain_rejection(carrier, message))

    world = tell(
        route=ROUTES[params.route],
        message=message,
        carrier_cfg=carrier,
        fastener=FASTENERS[params.fastener],
        wind=WINDS[params.wind],
        politician=POLITICIANS[params.politician],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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


CURATED = [
    StoryParams(
        route="bridge",
        message="pages",
        carrier="satchel",
        fastener="buckle",
        wind="gusty",
        politician="mayor",
        hero="Lina",
        hero_gender="girl",
        helper="Finn",
        helper_gender="boy",
        trait="careful",
        relation="siblings",
        hero_age=5,
        helper_age=7,
    ),
    StoryParams(
        route="tower",
        message="pages",
        carrier="folder",
        fastener="clip",
        wind="blustery",
        politician="councilor",
        hero="Max",
        hero_gender="boy",
        helper="Mira",
        helper_gender="girl",
        trait="quick",
        relation="friends",
        hero_age=6,
        helper_age=6,
    ),
    StoryParams(
        route="market",
        message="scroll",
        carrier="tube",
        fastener="cord",
        wind="breezy",
        politician="mayor",
        hero="Nora",
        hero_gender="girl",
        helper="Eli",
        helper_gender="boy",
        trait="curious",
        relation="friends",
        hero_age=6,
        helper_age=5,
    ),
    StoryParams(
        route="market",
        message="cards",
        carrier="satchel",
        fastener="clip",
        wind="breezy",
        politician="councilor",
        hero="Theo",
        hero_gender="boy",
        helper="Ivy",
        helper_gender="girl",
        trait="thoughtful",
        relation="siblings",
        hero_age=4,
        helper_age=7,
    ),
]


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed on seed {s}")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=False, header="### smoke")
        if "politician" not in smoke.story or "specifics" not in smoke.story or "fasten" not in smoke.story:
            raise StoryError("required seed words missing from smoke story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, message, carrier, fastener, wind, politician) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
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
            header = (
                f"### {p.hero} & {p.helper}: {p.message} by {p.route} "
                f"({p.carrier}, {p.fastener}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
