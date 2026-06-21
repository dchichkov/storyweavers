#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py
========================================================================

A standalone storyworld for a small myth-shaped domain: a child carries a holy
ember beneath a hood to relight a hill beacon for the village below.

This world is built for stories that explicitly include:
- the word "hood"
- sound effects
- dialogue
- flashback
- a myth-like tone

The simulation models whether a chosen hood is reasonable for the chosen
weather and holy place. Unreasonable combinations are rejected. Valid stories
all tell a complete little myth: a village need, a dangerous climb, a remembered
teaching, and an ending image that proves the light has returned.

Run it
------
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py --setting sea_cliff --weather rain --hood waxed
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py --setting marsh_tower --weather snow
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py --all
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/hood_sound_effects_dialogue_flashback_myth.py --verify
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
    kind: str = "thing"           # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elder_woman"}
        male = {"boy", "man", "father", "grandfather", "elder_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "elder_woman": "elder",
            "elder_man": "elder",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
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
class Setting:
    id: str
    place: str
    beacon: str
    people: str
    creatures: str
    path: str
    afford_weathers: set[str] = field(default_factory=set)
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
    sound: str
    severity: int
    threat: str               # "wind" | "rain" | "cold"
    sky: str
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
class HoodCfg:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    shield: int = 0
    comfort: int = 0
    material: str = ""
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
    def __init__(self, setting: Setting, weather: Weather, hood_cfg: HoodCfg) -> None:
        self.setting = setting
        self.weather = weather
        self.hood_cfg = hood_cfg
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "flashback_used": False,
            "sound_used": False,
            "dialogue_used": False,
            "weather_threat": weather.threat,
            "weather_severity": weather.severity,
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
        clone = World(self.setting, self.weather, self.hood_cfg)
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


def hood_suits(hood_cfg: HoodCfg, weather: Weather) -> bool:
    return weather.threat in hood_cfg.guards and hood_cfg.shield >= weather.severity


def _r_weather_bites(world: World) -> list[str]:
    child = world.get("child")
    ember = world.get("ember")
    hood = world.get("hood")
    threat = world.weather.threat
    sig = ("weather_bites", threat)
    if sig in world.fired:
        return []
    if child.meters["on_path"] < THRESHOLD:
        return []
    world.fired.add(sig)
    if threat not in hood.attrs.get("guards", set()) or hood.attrs.get("shield", 0) < world.weather.severity:
        if threat == "wind":
            ember.meters["heat"] -= 1
            child.memes["fear"] += 1
            child.meters["stumble"] += 1
        elif threat == "rain":
            ember.meters["heat"] -= 1
            child.meters["wet"] += 1
            child.memes["fear"] += 1
        elif threat == "cold":
            child.meters["cold"] += 1
            child.meters["slow"] += 1
            child.memes["fear"] += 1
    else:
        child.memes["steady"] += 1
        if threat == "cold":
            child.meters["cold"] = max(0.0, child.meters["cold"] - 1)
    return []


def _r_flashback_stirs(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    ember = world.get("ember")
    sig = ("flashback", child.id)
    if sig in world.fired:
        return []
    if ember.meters["heat"] > 1 and child.memes["fear"] < THRESHOLD:
        return []
    world.fired.add(sig)
    child.memes["memory"] += 1
    child.memes["courage"] += 1
    world.facts["flashback_used"] = True
    return [
        f"For one breath, {child.id} remembered another night long before this one: "
        f"{elder.id} by the hearth, laying {elder.pronoun('possessive')} hand on the "
        f"{hood_desc(world.hood_cfg)} and saying, \"A true light does not shout. It hides, "
        f"waits, and then shines when the world most needs it.\""
    ]


def _r_arrival_relights(world: World) -> list[str]:
    child = world.get("child")
    ember = world.get("ember")
    beacon = world.get("beacon")
    sig = ("relight", beacon.id)
    if sig in world.fired:
        return []
    if child.meters["at_beacon"] < THRESHOLD:
        return []
    world.fired.add(sig)
    if ember.meters["heat"] >= THRESHOLD:
        beacon.meters["lit"] += 1
        child.memes["relief"] += 1
        child.memes["awe"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="weather_bites", tag="physical", apply=_r_weather_bites),
    Rule(name="flashback_stirs", tag="memory", apply=_r_flashback_stirs),
    Rule(name="arrival_relights", tag="physical", apply=_r_arrival_relights),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hood_desc(hood_cfg: HoodCfg) -> str:
    return hood_cfg.label if hood_cfg.label.startswith("the ") else f"the {hood_cfg.label}"


def weather_step_effect(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["on_path"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    ember = sim.get("ember")
    return {
        "heat": ember.meters["heat"],
        "fear": child.memes["fear"],
        "cold": child.meters["cold"],
        "wet": child.meters["wet"],
        "steady": child.memes["steady"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for wid in sorted(setting.afford_weathers):
            weather = WEATHERS[wid]
            for hid, hood_cfg in HOODS.items():
                if hood_suits(hood_cfg, weather):
                    combos.append((sid, wid, hid))
    return combos


def explain_rejection(setting: Setting, weather: Weather, hood_cfg: HoodCfg) -> str:
    if weather.id not in setting.afford_weathers:
        return (
            f"(No story: {weather.label} is not a fitting sky for {setting.place}. "
            f"Choose weather the place truly affords.)"
        )
    if weather.threat not in hood_cfg.guards:
        return (
            f"(No story: {hood_desc(hood_cfg)} does not protect against {weather.label}. "
            f"The child would have no honest chance to keep the ember alive.)"
        )
    if hood_cfg.shield < weather.severity:
        return (
            f"(No story: {hood_desc(hood_cfg)} is too weak for {weather.label}. "
            f"The weather would beat the ember before the child reached the beacon.)"
        )
    return "(No story: this combination is unreasonable in this world.)"


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def omen_setup(world: World, child: Entity, elder: Entity) -> None:
    beacon = world.get("beacon")
    world.say(
        f"In the elder days, people said the gods tied one small light to every faithful village. "
        f"So when the flame on {beacon.label} went dark above {world.setting.place}, "
        f"the people below fell silent."
    )
    world.say(
        f"The fishers, shepherds, and bakers of {world.setting.people} lifted their faces to the hill, "
        f"for that beacon was believed to guide {world.setting.creatures} home."
    )
    world.say(
        f'{elder.id} placed a clay ember-bowl in {child.id}\'s hands and whispered, '
        f'"Take this up the {world.setting.path}. Keep it breathing, and the hill will remember us."'
    )
    world.facts["dialogue_used"] = True


def gift_hood(world: World, child: Entity, elder: Entity, hood: Entity) -> None:
    world.say(
        f"Then {elder.id} drew {hood_desc(world.hood_cfg)} over {child.id}'s hair. "
        f'\"This hood was made from {world.hood_cfg.material},\" {elder.pronoun()} said. '
        f'"Do not wear it for pride. Wear it for mercy."'
    )
    world.facts["dialogue_used"] = True
    child.memes["duty"] += 1
    child.memes["courage"] += 1


def begin_climb(world: World, child: Entity) -> None:
    world.say(
        f"{world.weather.sky.capitalize()} leaned over the path as {child.id} began the climb. "
        f"{world.weather.sound} went the night around the stones."
    )
    world.facts["sound_used"] = True
    child.meters["on_path"] += 1
    propagate(world, narrate=False)


def danger_beat(world: World, child: Entity, ember: Entity) -> None:
    pred = weather_step_effect(world)
    if world.weather.threat == "wind":
        world.say(
            f"The path narrowed between black pines. {world.weather.sound} -- and the ember shivered red in its bowl."
        )
    elif world.weather.threat == "rain":
        world.say(
            f"The steps turned slick. {world.weather.sound} -- and silver drops came slanting through the dark."
        )
    else:
        world.say(
            f"The stones were white with frost. {world.weather.sound} -- and {child.id}'s breath came out like pale smoke."
        )
    if pred["heat"] < ember.meters["heat"]:
        world.say(
            f"{child.id} bent low and tucked the ember closer under the hood, for the little light had begun to shrink."
        )
        ember.meters["heat"] = float(pred["heat"])
    if pred["cold"] >= THRESHOLD:
        child.meters["cold"] = float(pred["cold"])
    if pred["wet"] >= THRESHOLD:
        child.meters["wet"] = float(pred["wet"])
    if pred["fear"] >= THRESHOLD:
        child.memes["fear"] = float(pred["fear"])
    if pred["steady"] >= THRESHOLD:
        child.memes["steady"] = float(pred["steady"])
    propagate(world, narrate=True)


def child_dialogue(world: World, child: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'"Stay, little flame," {child.id} said. "If you stay, I will stay too."'
        )
    else:
        world.say(
            f'"I hear you, hill," {child.id} said softly. "I am coming."'
        )
    world.facts["dialogue_used"] = True


def shield_with_hood(world: World, child: Entity, hood: Entity, ember: Entity) -> None:
    world.say(
        f"{child.id} gathered the hood around the bowl with both hands. "
        f"The {hood.label} turned the weather aside just long enough for the ember to glow full again."
    )
    ember.meters["heat"] = max(1.0, ember.meters["heat"])
    child.memes["steady"] += 1


def reach_beacon(world: World, child: Entity) -> None:
    world.say(
        f"At last {child.id} came to the empty iron basket atop the height. It waited like a starless crown."
    )
    child.meters["at_beacon"] += 1
    propagate(world, narrate=False)


def relight(world: World, child: Entity, beacon: Entity, ember: Entity) -> None:
    propagate(world, narrate=False)
    if beacon.meters["lit"] >= THRESHOLD:
        world.say(
            f"{child.id} tipped the ember-bowl. Pffft -- then fwoom: gold climbed the old wood, "
            f"and the beacon rose bright against the dark."
        )
        world.facts["sound_used"] = True
    else:
        raise StoryError("(Story failed internally: the beacon did not relight in a supposedly valid story.)")


def ending(world: World, child: Entity, elder: Entity) -> None:
    beacon = world.get("beacon")
    world.say(
        f"Far below, the windows of {world.setting.people} answered one by one. "
        f"The cranes, boats, or wandering feet of the night would not be lost now."
    )
    world.say(
        f"When {child.id} came down at dawn, {elder.id} touched the warm edge of the hood and smiled. "
        f'"Now you know," {elder.pronoun()} said, "why the old stories dress mercy in humble cloth."'
    )
    world.say(
        f"And for many years after, whenever children looked up at {beacon.label} burning over {world.setting.place}, "
        f"they remembered the small figure beneath a hood who had carried one living spark through the dark."
    )
    world.facts["dialogue_used"] = True


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    weather: Weather,
    hood_cfg: HoodCfg,
    child_name: str = "Mira",
    child_type: str = "girl",
    elder_name: str = "Nala",
    elder_type: str = "grandmother",
    child_trait: str = "patient",
) -> World:
    world = World(setting, weather, hood_cfg)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=["young", child_trait],
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        role="elder",
        traits=["wise"],
    ))
    hood = world.add(Entity(
        id="hood",
        kind="thing",
        type="hood",
        label=hood_cfg.label,
        attrs={
            "guards": set(hood_cfg.guards),
            "shield": hood_cfg.shield,
            "comfort": hood_cfg.comfort,
            "material": hood_cfg.material,
        },
    ))
    ember = world.add(Entity(
        id="ember",
        kind="thing",
        type="ember",
        label="the holy ember",
    ))
    beacon = world.add(Entity(
        id="beacon",
        kind="thing",
        type="beacon",
        label=setting.beacon,
    ))

    child.meters["on_path"] = 0.0
    child.meters["at_beacon"] = 0.0
    child.meters["cold"] = 0.0
    child.meters["wet"] = 0.0
    child.meters["stumble"] = 0.0
    child.meters["slow"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["courage"] = 2.0
    child.memes["duty"] = 1.0
    child.memes["steady"] = 0.0
    child.memes["memory"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["awe"] = 0.0

    elder.memes["trust"] = 1.0
    ember.meters["heat"] = 2.0
    beacon.meters["lit"] = 0.0

    world.facts.update(
        child=child,
        elder=elder,
        hood=hood,
        hood_cfg=hood_cfg,
        ember=ember,
        beacon=beacon,
        setting=setting,
        weather=weather,
        child_trait=child_trait,
    )

    omen_setup(world, child, elder)
    gift_hood(world, child, elder, hood)

    world.para()
    begin_climb(world, child)
    danger_beat(world, child, ember)
    child_dialogue(world, child)
    shield_with_hood(world, child, hood, ember)

    world.para()
    reach_beacon(world, child)
    relight(world, child, beacon, ember)
    ending(world, child, elder)

    world.facts.update(
        success=beacon.meters["lit"] >= THRESHOLD,
        ember_alive=ember.meters["heat"] >= THRESHOLD,
        child_afraid=child.memes["fear"] >= THRESHOLD,
        child_wet=child.meters["wet"] >= THRESHOLD,
        child_cold=child.meters["cold"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "sea_cliff": Setting(
        id="sea_cliff",
        place="the Sea-Cliff of Lamps",
        beacon="the Cliff Beacon",
        people="the harbor village of Thessa",
        creatures="boats and white sea birds",
        path="salt stair",
        afford_weathers={"wind", "rain"},
        tags={"beacon", "sea"},
    ),
    "cedar_pass": Setting(
        id="cedar_pass",
        place="the Cedar Pass",
        beacon="the Pass Fire",
        people="the valley village of Orun",
        creatures="late walkers and mountain goats",
        path="cedar path",
        afford_weathers={"wind", "snow"},
        tags={"beacon", "mountain"},
    ),
    "marsh_tower": Setting(
        id="marsh_tower",
        place="the Reed Marsh Tower",
        beacon="the Marsh Lantern",
        people="the reed village of Seli",
        creatures="cranes and the ferry folk",
        path="plank walk",
        afford_weathers={"rain", "wind"},
        tags={"beacon", "marsh"},
    ),
}

WEATHERS = {
    "wind": Weather(
        id="wind",
        label="hard wind",
        sound="Whooo! Hushhh!",
        severity=2,
        threat="wind",
        sky="a black sky full of racing clouds",
        tags={"wind"},
    ),
    "rain": Weather(
        id="rain",
        label="cold rain",
        sound="Drip-drip. Ssshhh.",
        severity=2,
        threat="rain",
        sky="a low sky stitched with rain",
        tags={"rain"},
    ),
    "snow": Weather(
        id="snow",
        label="deep snow",
        sound="Hrrr... soft hush.",
        severity=3,
        threat="cold",
        sky="a white sky heavy with snow",
        tags={"snow", "cold"},
    ),
}

HOODS = {
    "wool": HoodCfg(
        id="wool",
        label="wool hood",
        phrase="a thick wool hood",
        guards={"wind", "cold"},
        shield=2,
        comfort=2,
        material="lamb's wool and cedar thread",
        tags={"hood", "wool"},
    ),
    "waxed": HoodCfg(
        id="waxed",
        label="waxed hood",
        phrase="a dark waxed hood",
        guards={"rain", "wind"},
        shield=2,
        comfort=1,
        material="waxed linen and river-reed cord",
        tags={"hood", "rain"},
    ),
    "fur": HoodCfg(
        id="fur",
        label="fur-lined hood",
        phrase="a fur-lined hood",
        guards={"cold", "wind"},
        shield=3,
        comfort=3,
        material="goat wool and soft winter fur",
        tags={"hood", "cold"},
    ),
    "linen": HoodCfg(
        id="linen",
        label="linen hood",
        phrase="a plain linen hood",
        guards={"sun"},
        shield=1,
        comfort=0,
        material="plain linen",
        tags={"hood"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Iris", "Nera", "Soma", "Lina"]
BOY_NAMES = ["Aren", "Tarin", "Milo", "Soren", "Davi", "Kelan"]
ELDER_WOMEN = ["Nala", "Sira", "Oma", "Tavi"]
ELDER_MEN = ["Beren", "Orin", "Toman", "Savel"]
TRAITS = ["patient", "brave", "quiet", "steadfast", "watchful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    weather: str
    hood: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
    child_trait: str
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
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a bright light set up high so people can find their way. In old stories, a beacon often protects travelers by helping them see where home is."
        )
    ],
    "hood": [
        (
            "What does a hood do?",
            "A hood covers your head and helps protect you from weather like wind, rain, or cold. In stories, it can also shelter something small and precious."
        )
    ],
    "wind": [
        (
            "Why is wind hard on a small flame?",
            "Wind pushes air against a flame and makes it shake and bend. If the gust is strong enough, it can blow the flame out."
        )
    ],
    "rain": [
        (
            "Why can rain put a flame out?",
            "Rain cools a flame and soaks the things feeding it. When too much water falls on a little fire, the fire cannot keep burning."
        )
    ],
    "snow": [
        (
            "Why does deep snow make a journey hard?",
            "Deep snow slows your feet and steals warmth from your body. That makes climbing and carrying things much harder."
        )
    ],
    "ember": [
        (
            "What is an ember?",
            "An ember is a small glowing piece of fire that still has heat inside it. If you protect it, it can help start a bigger flame again."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short memory scene from earlier in time. It helps explain why a character understands something or chooses to act a certain way."
        )
    ],
}
KNOWLEDGE_ORDER = ["beacon", "hood", "ember", "wind", "rain", "snow", "flashback"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    weather = f["weather"]
    hood_cfg = f["hood_cfg"]
    return [
        f'Write a short myth for a young child that includes the word "hood", a flashback, dialogue, and sound effects. The story should be about a child carrying a sacred ember through {weather.label} to relight a beacon.',
        f"Tell a myth-like story where {child.id} climbs to {setting.beacon} in {weather.label}, wearing a {hood_cfg.label}, and remembers a lesson from {elder.id} at the hardest moment.",
        f'Write a gentle myth with lines of dialogue and sounds like "{weather.sound}" where a child shelters a holy ember under a hood and brings light back to a village.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    weather = f["weather"]
    hood_cfg = f["hood_cfg"]
    beacon = f["beacon"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a young child from {setting.people}, and {elder.id}, the elder who trusted {child.pronoun('object')} with the holy ember."
        ),
        (
            f"Why did {child.id} climb to {beacon.label}?",
            f"{child.id} climbed because the beacon had gone dark above {setting.place}, and the village believed that light guided {setting.creatures} home. Bringing the fire back was a way of protecting everyone below."
        ),
        (
            f"How did the hood help {child.id}?",
            f"The {hood_cfg.label} shielded the ember from {weather.label}, so the little flame could keep breathing on the climb. It also helped {child.id} stay steady when the path felt frightening."
        ),
    ]
    if f.get("flashback_used"):
        qa.append(
            (
                f"What did {child.id} remember in the flashback?",
                f"{child.id} remembered {elder.id} teaching that a true light hides and waits until the world most needs it. That memory mattered because it helped {child.pronoun('object')} protect the ember instead of panicking."
            )
        )
    if f.get("success"):
        qa.append(
            (
                f"What changed at the end of the story?",
                f"At the end, {beacon.label} was burning again, and the people of {setting.people} could see that the village had not been forgotten. The ending image proves the climb worked because the lost light returned to the hill."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beacon", "hood", "ember", "flashback"} | set(world.weather.tags)
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
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in e.attrs.items() if v or v == 0}
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supports(S, W) :- setting(S), weather(W), affords(S, W).
hood_suits(H, W) :- hood(H), weather(W), threat(W, T), guards(H, T), shield(H, P), severity(W, S), P >= S.
valid(S, W, H) :- supports(S, W), hood_suits(H, W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for wid in sorted(setting.afford_weathers):
            lines.append(asp.fact("affords", sid, wid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("severity", wid, weather.severity))
        lines.append(asp.fact("threat", wid, weather.threat))
    for hid, hood_cfg in HOODS.items():
        lines.append(asp.fact("hood", hid))
        lines.append(asp.fact("shield", hid, hood_cfg.shield))
        for guard in sorted(hood_cfg.guards):
            lines.append(asp.fact("guards", hid, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="sea_cliff",
        weather="rain",
        hood="waxed",
        child_name="Mira",
        child_type="girl",
        elder_name="Nala",
        elder_type="grandmother",
        child_trait="steadfast",
        seed=None,
    ),
    StoryParams(
        setting="cedar_pass",
        weather="wind",
        hood="wool",
        child_name="Aren",
        child_type="boy",
        elder_name="Orin",
        elder_type="grandfather",
        child_trait="watchful",
        seed=None,
    ),
    StoryParams(
        setting="cedar_pass",
        weather="snow",
        hood="fur",
        child_name="Tala",
        child_type="girl",
        elder_name="Sira",
        elder_type="grandmother",
        child_trait="patient",
        seed=None,
    ),
    StoryParams(
        setting="marsh_tower",
        weather="wind",
        hood="waxed",
        child_name="Kelan",
        child_type="boy",
        elder_name="Tavi",
        elder_type="grandmother",
        child_trait="quiet",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-shaped storyworld: a child beneath a hood carries a holy ember to relight a beacon."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--hood", choices=HOODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate matches Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_names(rng: random.Random, child_type: str, elder_type: str) -> tuple[str, str]:
    child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_name = rng.choice(ELDER_WOMEN if elder_type == "grandmother" else ELDER_MEN)
    if elder_name == child_name:
        elder_name = (elder_name + " the Elder")
    return child_name, elder_name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.weather and args.hood:
        setting = SETTINGS[args.setting]
        weather = WEATHERS[args.weather]
        hood_cfg = HOODS[args.hood]
        if not (args.weather in setting.afford_weathers and hood_suits(hood_cfg, weather)):
            raise StoryError(explain_rejection(setting, weather, hood_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.weather is None or combo[1] == args.weather)
        and (args.hood is None or combo[2] == args.hood)
    ]
    if not combos:
        if args.setting and args.weather and args.hood:
            raise StoryError(explain_rejection(SETTINGS[args.setting], WEATHERS[args.weather], HOODS[args.hood]))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, weather_id, hood_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    child_name, elder_name = _pick_names(rng, child_type, elder_type)

    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        hood=hood_id,
        child_name=args.child_name or child_name,
        child_type=child_type,
        elder_name=args.elder_name or elder_name,
        elder_type=elder_type,
        child_trait=rng.choice(TRAITS),
        seed=None,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.weather not in WEATHERS:
        raise StoryError(f"(No story: unknown weather '{params.weather}'.)")
    if params.hood not in HOODS:
        raise StoryError(f"(No story: unknown hood '{params.hood}'.)")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown child type '{params.child_type}'.)")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError(f"(No story: unknown elder type '{params.elder_type}'.)")
    setting = SETTINGS[params.setting]
    weather = WEATHERS[params.weather]
    hood_cfg = HOODS[params.hood]
    if not (params.weather in setting.afford_weathers and hood_suits(hood_cfg, weather)):
        raise StoryError(explain_rejection(setting, weather, hood_cfg))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        weather=WEATHERS[params.weather],
        hood_cfg=HOODS[params.hood],
        child_name=params.child_name,
        child_type=params.child_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
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

    try:
        sample = generate(CURATED[0])
        if "hood" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story did not include 'hood'.)")
        if sample.world is None or not sample.world.facts.get("flashback_used"):
            raise StoryError("(Smoke test failed: generated story did not exercise flashback state.)")
        print("OK: smoke generation succeeded on a curated sample.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: default-resolved story was empty.)")
        print("OK: default resolve_params() + generate() smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, weather, hood) combos:\n")
        for setting, weather, hood in combos:
            print(f"  {setting:11} {weather:6} {hood}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.setting}, {p.weather}, {p.hood}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
