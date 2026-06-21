#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py
==============================================================================

A standalone story world for a small adventure domain: a young messenger is sent
on a quest to deliver a needed boon after an elder gives a careful speech. Some
choices lead to a proud, successful delivery; others lead to a cautionary bad
ending when the warning is ignored and the boon is lost before it can be
delivered.

Run it
------
    python storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py
    python storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py --route shortcut --weather wind
    python storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/speech_boon_deliver_quest_cautionary_bad_ending.py --verify
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
DANGER_FAIL = 3


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
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Destination:
    id: str
    label: str
    place: str
    need: str
    keeper: str
    image: str
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
class Boon:
    id: str
    label: str
    phrase: str
    need: str
    fragile: bool
    vessel: str
    spoil_verb: str
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
class Route:
    id: str
    label: str
    style: str
    caution: str
    travel: str
    bad_step: str
    risk: int
    safe: bool
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
class Weather:
    id: str
    label: str
    sky: str
    risk_bonus: int
    trouble: str
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


def _r_fragile_loss(world: World) -> list[str]:
    out: list[str] = []
    boon = world.get("boon")
    if boon.attrs.get("fragile") and boon.meters["danger"] >= DANGER_FAIL and boon.meters["lost"] < THRESHOLD:
        sig = ("fragile_loss",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        boon.meters["lost"] += 1
        boon.meters["delivered"] = 0.0
        hero = world.get("hero")
        hero.memes["fear"] += 1
        hero.memes["guilt"] += 1
        out.append("__boon_lost__")
    return out


def _r_delivery(world: World) -> list[str]:
    out: list[str] = []
    boon = world.get("boon")
    hero = world.get("hero")
    if hero.meters["arrived"] >= THRESHOLD and boon.meters["lost"] < THRESHOLD and boon.meters["delivered"] < THRESHOLD:
        sig = ("delivered",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        boon.meters["delivered"] += 1
        hero.memes["pride"] += 1
        out.append("__delivered__")
    return out


CAUSAL_RULES = [
    Rule(name="fragile_loss", tag="physical", apply=_r_fragile_loss),
    Rule(name="delivery", tag="quest", apply=_r_delivery),
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


DESTINATIONS = {
    "lighthouse": Destination(
        id="lighthouse",
        label="the lighthouse",
        place="on the black cliff above the sea",
        need="lamp_oil",
        keeper="the lighthouse keeper",
        image="the tall lamp could burn through the night",
        tags={"lighthouse", "light", "keeper"},
    ),
    "orchard": Destination(
        id="orchard",
        label="the frost orchard",
        place="beyond the stone fields",
        need="sunseed",
        keeper="the orchard warden",
        image="the bare trees might wake with green again",
        tags={"orchard", "seed", "warden"},
    ),
    "cave": Destination(
        id="cave",
        label="the snow cave",
        place="under the white mountain",
        need="healing_soup",
        keeper="the cave watch",
        image="the tired travelers could grow warm again",
        tags={"cave", "travelers", "warmth"},
    ),
}

BOONS = {
    "oil_flask": Boon(
        id="oil_flask",
        label="lamp oil",
        phrase="a blue flask of lamp oil",
        need="lamp_oil",
        fragile=True,
        vessel="flask",
        spoil_verb="shattered on the rocks",
        tags={"oil", "fragile", "light"},
    ),
    "sunseed_pouch": Boon(
        id="sunseed_pouch",
        label="sunseeds",
        phrase="a golden pouch of sunseeds",
        need="sunseed",
        fragile=False,
        vessel="pouch",
        spoil_verb="spilled into the dust",
        tags={"seed", "pouch"},
    ),
    "soup_pot": Boon(
        id="soup_pot",
        label="healing soup",
        phrase="a small sealed pot of healing soup",
        need="healing_soup",
        fragile=True,
        vessel="pot",
        spoil_verb="split open and ran into the snow",
        tags={"soup", "fragile", "food"},
    ),
}

ROUTES = {
    "road": Route(
        id="road",
        label="the king's road",
        style="the long road",
        caution="Stay on the king's road, even if it feels slow.",
        travel="followed the old road between mile stones and bramble hedges",
        bad_step="there was no bad step at all, only patient walking",
        risk=0,
        safe=True,
        tags={"road", "safe_route"},
    ),
    "wood": Route(
        id="wood",
        label="the whispering wood path",
        style="the wood path",
        caution="If you cross the whispering wood, keep to the marked stones and do not run.",
        travel="slipped under the green wood path where roots braided across the ground",
        bad_step="a hidden root caught a careless foot",
        risk=1,
        safe=False,
        tags={"wood", "forest"},
    ),
    "shortcut": Route(
        id="shortcut",
        label="the cliff shortcut",
        style="the cliff shortcut",
        caution="Do not take the cliff shortcut with a burden in your arms.",
        travel="climbed toward the cliff shortcut where the path narrowed over the sea",
        bad_step="loose stones skittered under one quick step",
        risk=2,
        safe=False,
        tags={"cliff", "shortcut"},
    ),
}

WEATHERS = {
    "clear": Weather(
        id="clear",
        label="clear weather",
        sky="The sky was bright and high.",
        risk_bonus=0,
        trouble="nothing tugged at the path but time",
        tags={"clear"},
    ),
    "wind": Weather(
        id="wind",
        label="hard wind",
        sky="A hard wind hurried through the day.",
        risk_bonus=1,
        trouble="the wind shoved at cloaks and baskets",
        tags={"wind"},
    ),
    "rain": Weather(
        id="rain",
        label="cold rain",
        sky="Cold rain stitched silver lines through the air.",
        risk_bonus=1,
        trouble="the wet stones turned slick",
        tags={"rain", "wet"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Asha", "Nora", "Tala", "Ivy", "Pia", "Sela"]
BOY_NAMES = ["Tobin", "Eli", "Finn", "Arlo", "Nico", "Bram", "Jules", "Rowan"]
TRAITS = ["brave", "eager", "quick", "hopeful", "restless", "determined"]


def boon_fits(destination: Destination, boon: Boon) -> bool:
    return destination.need == boon.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for dest_id, dest in DESTINATIONS.items():
        for boon_id, boon in BOONS.items():
            if not boon_fits(dest, boon):
                continue
            for route_id in ROUTES:
                for weather_id in WEATHERS:
                    combos.append((dest_id, boon_id, route_id, weather_id))
    return combos


def danger_score(route: Route, weather: Weather, boon: Boon) -> int:
    score = route.risk + weather.risk_bonus
    if boon.fragile and not route.safe:
        score += 1
    return score


def outcome_of(params: "StoryParams") -> str:
    dest = DESTINATIONS[params.destination]
    boon = BOONS[params.boon]
    route = ROUTES[params.route]
    weather = WEATHERS[params.weather]
    if not boon_fits(dest, boon):
        return "invalid"
    return "failed" if danger_score(route, weather, boon) >= DANGER_FAIL else "delivered"


@dataclass
class StoryParams:
    destination: str
    boon: str
    route: str
    weather: str
    hero: str
    gender: str
    elder: str
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


def predict_journey(world: World, route: Route, weather: Weather) -> dict:
    sim = world.copy()
    boon = sim.get("boon")
    boon.meters["danger"] += danger_score(route, weather, BOONS[boon.attrs["cfg_id"]])
    if route.id == "shortcut":
        boon.meters["danger"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": boon.meters["danger"],
        "lost": boon.meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, boon_cfg: Boon, dest_cfg: Destination) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In the small gate-town below the hills, {hero.id} loved stories of maps, towers, and brave errands."
    )
    world.say(
        f"One morning {elder.id}, the village {elder.label_word}, set {boon_cfg.phrase} into {hero.id}'s hands."
    )
    world.say(
        f'"This is a boon for {dest_cfg.keeper} at {dest_cfg.label}," {elder.pronoun()} said. '
        f'"It must be delivered before night, because then {dest_cfg.image}."'
    )


def elder_speech(world: World, hero: Entity, elder: Entity, route_cfg: Route, weather_cfg: Weather) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"{weather_cfg.sky} Before {hero.id} left, {elder.id} gave a careful speech beside the town gate."
    )
    world.say(
        f'"{route_cfg.caution} Walk with both hands on the parcel. Today {weather_cfg.trouble}, and a quest is finished by care, not by hurry."'
    )


def accept_quest(world: World, hero: Entity, dest_cfg: Destination) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'{hero.id} nodded hard. "{hero.id if hero.id.endswith("s") else hero.id} can do it," {hero.pronoun()} whispered, and set off for {dest_cfg.place}.'
    )


def choose_route(world: World, hero: Entity, route_cfg: Route, weather_cfg: Weather) -> None:
    boon = world.get("boon")
    if route_cfg.safe:
        hero.memes["care"] += 1
        world.say(
            f"{hero.id} {route_cfg.travel}. It was slower than a dash, but it gave room to breathe and think."
        )
    else:
        hero.memes["haste"] += 1
        world.say(
            f"After a while, the long way began to feel heavy in {hero.id}'s mind. {hero.pronoun().capitalize()} turned aside and {route_cfg.travel}."
        )
        world.say(
            f"The path looked like a shortcut fit for a storybook hero, and that made it easy to forget the warning."
        )
    boon.meters["danger"] += float(danger_score(route_cfg, weather_cfg, BOONS[boon.attrs["cfg_id"]]))
    if route_cfg.id == "shortcut":
        boon.meters["danger"] += 1.0


def stumble(world: World, hero: Entity, boon_cfg: Boon, route_cfg: Route, weather_cfg: Weather) -> None:
    boon = world.get("boon")
    if boon.meters["danger"] < DANGER_FAIL:
        hero.memes["strain"] += 1
        world.say(
            f"{hero.id} kept going while {weather_cfg.trouble}, and the parcel felt more precious with every step."
        )
        return
    world.say(
        f"Then {route_cfg.bad_step}, and {weather_cfg.trouble}. {hero.id} tried to save the bundle, but the jolt was too hard."
    )
    propagate(world, narrate=False)
    if boon.meters["lost"] >= THRESHOLD:
        world.say(
            f"The {boon_cfg.vessel} slipped free and {boon_cfg.spoil_verb}. At once the quest changed from hopeful to hopeless."
        )


def arrive(world: World, hero: Entity, dest_cfg: Destination, boon_cfg: Boon) -> None:
    boon = world.get("boon")
    hero.meters["arrived"] += 1
    propagate(world, narrate=False)
    if boon.meters["delivered"] >= THRESHOLD:
        world.say(
            f"At last {hero.id} reached {dest_cfg.label}. {dest_cfg.keeper.capitalize()} opened the door, saw the boon, and smiled with deep relief."
        )
        world.say(
            f"{hero.id} had managed to deliver it in time, and the whole place seemed to breathe easier."
        )
    else:
        world.say(
            f"When {hero.id} finally reached {dest_cfg.label}, {dest_cfg.keeper} saw the empty hands and understood before a word was said."
        )


def good_ending(world: World, hero: Entity, elder: Entity, dest_cfg: Destination) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"That night, back in town, {elder.id} listened to the tale and put a proud hand on {hero.id}'s shoulder."
    )
    world.say(
        f"The quest had ended well because {hero.id} remembered that brave feet are best guided by careful choices."
    )
    world.say(
        f"Far away, {dest_cfg.image[0].upper() + dest_cfg.image[1:]}, and {hero.id} went to sleep feeling a little taller."
    )


def bad_ending(world: World, hero: Entity, elder: Entity, dest_cfg: Destination, boon_cfg: Boon) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f'"I wanted to deliver it fast," {hero.id} said at last, and the words felt small after such a long road.'
    )
    world.say(
        f"{dest_cfg.keeper.capitalize()} thanked {hero.pronoun('object')} for trying, but the needed boon was gone, and that night no help came from it."
    )
    world.say(
        f"When {hero.id} returned to town, {elder.id} did not shout. {elder.pronoun().capitalize()} only said that a warning is part of a gift, and dropping it can break more than a {boon_cfg.vessel}."
    )
    world.say(
        f"So the adventure ended badly: the boon was never delivered, the need remained, and {hero.id} learned too late that rushing can ruin a quest."
    )


def tell(
    destination: Destination,
    boon_cfg: Boon,
    route_cfg: Route,
    weather_cfg: Weather,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "woman",
    trait: str = "brave",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="elder", role="elder"))
    boon = world.add(Entity(id="boon", kind="thing", type="boon", label=boon_cfg.label, role="boon", attrs={"fragile": boon_cfg.fragile, "cfg_id": boon_cfg.id}))
    world.add(Entity(id="destination", kind="thing", type="place", label=destination.label, role="destination"))

    hero.meters["arrived"] = 0.0
    boon.meters["danger"] = 0.0
    boon.meters["lost"] = 0.0
    boon.meters["delivered"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["guilt"] = 0.0

    world.facts["destination_cfg"] = destination
    world.facts["boon_cfg"] = boon_cfg
    world.facts["route_cfg"] = route_cfg
    world.facts["weather_cfg"] = weather_cfg
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["boon"] = boon

    introduce(world, hero, elder, boon_cfg, destination)
    elder_speech(world, hero, elder, route_cfg, weather_cfg)
    world.para()
    accept_quest(world, hero, destination)
    choose_route(world, hero, route_cfg, weather_cfg)
    stumble(world, hero, boon_cfg, route_cfg, weather_cfg)
    world.para()
    arrive(world, hero, destination, boon_cfg)

    outcome = "failed" if boon.meters["lost"] >= THRESHOLD else "delivered"
    world.facts["predicted"] = predict_journey(world, route_cfg, weather_cfg)
    world.facts["outcome"] = outcome

    if outcome == "delivered":
        world.para()
        good_ending(world, hero, elder, destination)
    else:
        world.para()
        bad_ending(world, hero, elder, destination, boon_cfg)
    return world


KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is an important trip with a goal. Someone sets out to do something that matters and must keep going until the job is done."
        )
    ],
    "speech": [
        (
            "What is a speech?",
            "A speech is when someone speaks carefully to tell others something important. It can give rules, advice, or courage before a hard job."
        )
    ],
    "boon": [
        (
            "What is a boon?",
            "A boon is a helpful gift or blessing. It is something given because it can bring comfort, help, or hope."
        )
    ],
    "deliver": [
        (
            "What does deliver mean?",
            "To deliver something means to carry it to the right person or place. You do not just hold it; you make sure it truly arrives."
        )
    ],
    "lighthouse": [
        (
            "Why does a lighthouse need oil or light?",
            "A lighthouse shines to guide people in the dark. If its lamp goes out, travelers and sailors can lose their way."
        )
    ],
    "seed": [
        (
            "Why are seeds important?",
            "Seeds can grow into plants when they are planted and cared for. A small pouch of seeds can become food or trees later."
        )
    ],
    "soup": [
        (
            "Why can warm soup help tired travelers?",
            "Warm soup gives heat and food at the same time. When people are cold and worn out, that can help them feel stronger."
        )
    ],
    "shortcut": [
        (
            "Why can a shortcut be a bad choice?",
            "A shortcut is not always safer just because it is faster. If it is narrow, steep, or slippery, hurrying there can cause a bigger problem."
        )
    ],
    "wind": [
        (
            "Why is strong wind risky on a narrow path?",
            "Strong wind can push at your body and what you are carrying. On a narrow path, even a little shove can make you stumble."
        )
    ],
    "rain": [
        (
            "Why is rain dangerous on stone paths?",
            "Rain makes stone slick. Feet can slide more easily, especially if someone is rushing."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "speech", "boon", "deliver", "lighthouse", "seed", "soup", "shortcut", "wind", "rain"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    dest = f["destination_cfg"]
    boon_cfg = f["boon_cfg"]
    route = f["route_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a young child that includes the words "speech", "boon", and "deliver". '
        f"The story should be about {hero.id} carrying {boon_cfg.phrase} to {dest.label}."
    )
    if outcome == "failed":
        return [
            base,
            f"Tell a cautionary quest where an elder gives a warning speech, but {hero.id} ignores it, takes {route.style}, and fails to deliver the boon.",
            f"Write a small adventure with a bad ending: the hero rushes, the boon is lost, and the lesson is that care matters more than speed.",
        ]
    return [
        base,
        f"Tell a quest story where an elder's speech helps {hero.id} make careful choices and deliver a needed boon to {dest.label}.",
        f"Write a gentle adventure that ends with the boon delivered and the hero learning that patience can be brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    dest = f["destination_cfg"]
    boon_cfg = f["boon_cfg"]
    route = f["route_cfg"]
    weather = f["weather_cfg"]
    outcome = f["outcome"]
    predicted = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young messenger on a quest, and the elder who trusted {hero.pronoun('object')} with an important errand."
        ),
        (
            "What was the boon, and where did it need to go?",
            f"The boon was {boon_cfg.phrase}, and it needed to go to {dest.label}. It mattered there because {dest.image}."
        ),
        (
            "What did the elder say in the speech?",
            f"The elder warned {hero.id} to travel carefully and not let hurry lead the way. The speech mattered because {weather.trouble}, so the road itself could turn a small mistake into a big one."
        ),
    ]
    if outcome == "failed":
        qa.append(
            (
                f"Why did {hero.id} fail to deliver the boon?",
                f"{hero.id} failed because {hero.pronoun()} ignored the warning and chose {route.style} when the journey was too risky. The danger grew until the {boon_cfg.vessel} was lost, so there was nothing left to deliver."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly: the boon never reached {dest.label}, and the people there had to go without its help that night. The ending proves the lesson because the quest was ruined by rushing instead of listening."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} manage to deliver the boon?",
                f"{hero.id} kept going carefully and arrived with the boon still safe. That worked because the danger never grew high enough to ruin the parcel."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the boon delivered and relief at {dest.label}. The final image shows that care, not hurry, brought the quest safely home."
            )
        )
    qa.append(
        (
            "Was the warning important?",
            f"Yes. The elder's speech pointed straight at the real danger of the trip, and the world of the story proved it. When the predicted danger rose to {int(predicted['danger'])}, the journey could turn from hopeful to harmful."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dest = f["destination_cfg"]
    boon_cfg = f["boon_cfg"]
    route = f["route_cfg"]
    weather = f["weather_cfg"]
    tags = {"quest", "speech", "boon", "deliver"} | set(dest.tags) | set(boon_cfg.tags) | set(route.tags) | set(weather.tags)
    tag_map = {
        "lighthouse": "lighthouse",
        "seed": "seed",
        "soup": "soup",
        "shortcut": "shortcut",
        "wind": "wind",
        "rain": "rain",
    }
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags or tag_map.get(key) in tags:
            out.extend(KNOWLEDGE[key])
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
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:11} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="lighthouse",
        boon="oil_flask",
        route="shortcut",
        weather="wind",
        hero="Mira",
        gender="girl",
        elder="woman",
        trait="eager",
    ),
    StoryParams(
        destination="cave",
        boon="soup_pot",
        route="wood",
        weather="rain",
        hero="Tobin",
        gender="boy",
        elder="man",
        trait="quick",
    ),
    StoryParams(
        destination="orchard",
        boon="sunseed_pouch",
        route="road",
        weather="clear",
        hero="Asha",
        gender="girl",
        elder="woman",
        trait="hopeful",
    ),
    StoryParams(
        destination="lighthouse",
        boon="oil_flask",
        route="road",
        weather="clear",
        hero="Finn",
        gender="boy",
        elder="man",
        trait="determined",
    ),
    StoryParams(
        destination="orchard",
        boon="sunseed_pouch",
        route="shortcut",
        weather="wind",
        hero="Lina",
        gender="girl",
        elder="woman",
        trait="restless",
    ),
]


def explain_rejection(destination: Destination, boon: Boon) -> str:
    return (
        f"(No story: {boon.phrase} does not match what {destination.label} needs. "
        f"This quest works only when the boon honestly helps the place it is meant for.)"
    )


ASP_RULES = r"""
fits(D,B) :- destination(D), boon(B), needs(D,N), serves(B,N).
valid(D,B,R,W) :- fits(D,B), route(R), weather(W).

danger(Risk + Bonus + Frag) :-
    chosen_route(R), route_risk(R,Risk),
    chosen_weather(W), weather_bonus(W,Bonus),
    chosen_boon(B), fragile(B), not route_safe(R),
    Frag = 1.
danger(Risk + Bonus) :-
    chosen_route(R), route_risk(R,Risk),
    chosen_weather(W), weather_bonus(W,Bonus),
    chosen_boon(B), not fragile(B).
danger(Risk + Bonus) :-
    chosen_route(R), route_risk(R,Risk),
    chosen_weather(W), weather_bonus(W,Bonus),
    chosen_boon(B), fragile(B), route_safe(R).
danger2(D + 1) :- chosen_route(shortcut), danger(D).
danger2(D) :- chosen_route(R), R != shortcut, danger(D).

outcome(failed) :- danger2(D), fail_at(F), D >= F.
outcome(delivered) :- danger2(D), fail_at(F), D < F.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dest_id, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("needs", dest_id, dest.need))
    for boon_id, boon in BOONS.items():
        lines.append(asp.fact("boon", boon_id))
        lines.append(asp.fact("serves", boon_id, boon.need))
        if boon.fragile:
            lines.append(asp.fact("fragile", boon_id))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_risk", route_id, route.risk))
        if route.safe:
            lines.append(asp.fact("route_safe", route_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("weather_bonus", weather_id, weather.risk_bonus))
    lines.append(asp.fact("fail_at", DANGER_FAIL))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_destination", params.destination),
            asp.fact("chosen_boon", params.boon),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_weather", params.weather),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure quest to deliver a needed boon after an elder's speech."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--boon", choices=BOONS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.boon:
        destination = DESTINATIONS[args.destination]
        boon = BOONS[args.boon]
        if not boon_fits(destination, boon):
            raise StoryError(explain_rejection(destination, boon))

    combos = [
        combo
        for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.boon is None or combo[1] == args.boon)
        and (args.route is None or combo[2] == args.route)
        and (args.weather is None or combo[3] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination_id, boon_id, route_id, weather_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["woman", "man"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        destination=destination_id,
        boon=boon_id,
        route=route_id,
        weather=weather_id,
        hero=hero,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.boon not in BOONS:
        raise StoryError(f"(Unknown boon: {params.boon})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")

    destination = DESTINATIONS[params.destination]
    boon = BOONS[params.boon]
    route = ROUTES[params.route]
    weather = WEATHERS[params.weather]

    if not boon_fits(destination, boon):
        raise StoryError(explain_rejection(destination, boon))

    world = tell(
        destination=destination,
        boon_cfg=boon,
        route_cfg=route,
        weather_cfg=weather,
        hero_name=params.hero,
        hero_gender=params.gender,
        elder_type=params.elder,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, boon, route, weather) combos:\n")
        for dest, boon, route, weather in combos:
            print(f"  {dest:10} {boon:14} {route:10} {weather}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.boon} to {p.destination} "
                f"via {p.route} in {p.weather} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
