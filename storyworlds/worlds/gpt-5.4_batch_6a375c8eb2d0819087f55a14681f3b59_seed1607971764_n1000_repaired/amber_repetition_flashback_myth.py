#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py
=============================================================

A small myth-flavored storyworld about a child who must carry an amber light to a
hill or shore shrine before dawn. The world is simulated: weather presses on the
ember, the path itself makes the child afraid, and a matching aid helps the hero
through the middle turn. Every story includes a repeated refrain and an explicit
flashback from an elder who remembers an earlier dim dawn.

Run it
------
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py --all
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py --trace --seed 11
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py --json
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py --asp
python storyworlds/worlds/gpt-5.4/amber_repetition_flashback_myth.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "priestess"}
        male = {"boy", "man", "grandfather", "keeper"}
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


@dataclass
class Shrine:
    id: str
    label: str
    place: str
    path_phrase: str
    risk: str
    peril: int
    dawn_image: str
    flashback_loss: str
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
    sky: str
    force: int
    press_text: str
    air_text: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    shield: int
    carry_text: str
    keep_text: str
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
class Aid:
    id: str
    label: str
    phrase: str
    protects: str
    power: int
    use_text: str
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


def _r_weather_press(world: World) -> list[str]:
    hero = world.get("hero")
    ember = world.get("ember")
    if hero.meters["traveling"] < THRESHOLD:
        return []
    sig = ("weather_press", int(hero.meters["steps"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    force = int(world.facts["weather_force"])
    shield = int(world.facts["vessel_shield"])
    if force >= shield:
        ember.meters["flicker"] += 1
        hero.memes["fear"] += 1
        return ["__weather_narrow__"]
    hero.memes["courage"] += 1
    return []


def _r_path_turn(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["traveling"] < THRESHOLD:
        return []
    sig = ("path_turn", int(hero.meters["steps"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    peril = int(world.facts["shrine_peril"])
    risk = world.facts["shrine_risk"]
    aid_risk = world.facts["aid_risk"]
    aid_power = int(world.facts["aid_power"])
    if aid_risk == risk and aid_power >= peril:
        hero.memes["courage"] += 1
        hero.attrs["aid_used"] = True
        return ["__aid__"]
    hero.memes["fear"] += 1
    return []


def _r_light_shrine(world: World) -> list[str]:
    hero = world.get("hero")
    ember = world.get("ember")
    shrine = world.get("shrine")
    village = world.get("village")
    if hero.meters["at_shrine"] < THRESHOLD or ember.meters["glow"] < THRESHOLD:
        return []
    sig = ("light_shrine",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["lit"] += 1
    village.meters["darkness"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__lit__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="weather_press", tag="physical", apply=_r_weather_press),
    Rule(name="path_turn", tag="physical", apply=_r_path_turn),
    Rule(name="light_shrine", tag="resolution", apply=_r_light_shrine),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for line in out:
            if not line.startswith("__"):
                world.say(line)
    return out


def refrain() -> str:
    return "Carry the amber light, carry it high."


def valid_combo(shrine: Shrine, weather: Weather, vessel: Vessel, aid: Aid) -> bool:
    return vessel.shield >= weather.force and aid.protects == shrine.risk and aid.power >= shrine.peril


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for shrine_id, shrine in SHRINES.items():
        for weather_id, weather in WEATHERS.items():
            for vessel_id, vessel in VESSELS.items():
                for aid_id, aid in AIDS.items():
                    if valid_combo(shrine, weather, vessel, aid):
                        combos.append((shrine_id, weather_id, vessel_id, aid_id))
    return combos


def challenge_of(params: "StoryParams") -> str:
    shrine = SHRINES[params.shrine]
    weather = WEATHERS[params.weather]
    vessel = VESSELS[params.vessel]
    aid = AIDS[params.aid]
    if not valid_combo(shrine, weather, vessel, aid):
        return "invalid"
    if vessel.shield == weather.force or aid.power == shrine.peril:
        return "narrow"
    return "steady"


def predict_passage(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["traveling"] = 1
    hero.meters["steps"] = 1
    propagate(sim, narrate=False)
    ember = sim.get("ember")
    return {
        "flicker": ember.meters["flicker"] >= THRESHOLD,
        "aid_used": bool(hero.attrs.get("aid_used")),
    }


def opening(world: World, hero: Entity, elder: Entity, shrine: Shrine, weather: Weather) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In the old days, when people still believed dawn had to be invited, "
        f"{hero.id} lived in a village below {shrine.place}. Each morning the people "
        f"watched that lonely shrine, because if its lamp slept, the fields stayed gray."
    )
    world.say(weather.air_text)
    world.say(
        f"Before the first bird called, {elder.id} put a hand over the small amber flame "
        f'''on the hearth and whispered, \"{refrain()}\"'''
    )


def flashback(world: World, hero: Entity, elder: Entity, shrine: Shrine) -> None:
    elder.memes["memory"] += 1
    world.say(
        f"Then {elder.id} looked past the doorway and remembered another year. "
        f"Long ago, {elder.pronoun()} had seen {shrine.flashback_loss}, and the children "
        f"of the village had eaten breakfast in a half-night that would not lift."
    )
    world.say(
        f"Because of that memory, {elder.id} never treated the dawn lamp like a game."
    )


def charge(world: World, hero: Entity, elder: Entity, vessel: Vessel, aid: Aid) -> None:
    world.say(
        f"{elder.id} set the ember into {vessel.phrase} and gave {hero.id} {aid.phrase}. "
        f"\"{refrain()}\" {elder.pronoun()} said again. \"Do not hurry, and do not hide it. "
        f'''The sky remembers brave hands.\"'''
    )


def depart(world: World, hero: Entity, shrine: Shrine, vessel: Vessel) -> None:
    ember = world.get("ember")
    hero.meters["traveling"] = 1
    hero.meters["steps"] = 1
    ember.meters["glow"] = 1
    world.say(
        f"So {hero.id} climbed onto {shrine.path_phrase}, carrying {vessel.carry_text}. "
        f"The ember shone like a drop of amber honey in the dark."
    )


def middle_turn(world: World, hero: Entity, shrine: Shrine, weather: Weather, vessel: Vessel, aid: Aid) -> None:
    pred = predict_passage(world)
    world.facts["predicted_flicker"] = pred["flicker"]
    world.facts["predicted_aid"] = pred["aid_used"]
    produced = propagate(world, narrate=False)
    if "__weather_narrow__" in produced:
        world.say(
            f"{weather.press_text} For a breath the little fire bent low inside the {vessel.label}, "
            f"and {hero.id}'s heart knocked hard."
        )
    else:
        world.say(
            f"{weather.press_text} The flame trembled, yet {vessel.keep_text}, and {hero.id} kept walking."
        )
    if hero.attrs.get("aid_used"):
        hero.memes["trust"] += 1
        world.say(
            f"At the hardest part, where {shrine.path_phrase} tested every step, {hero.id} used {aid.label}. "
            f'''{aid.use_text} Then {hero.id} said the old words aloud: \"{refrain()}\"'''
        )
    else:
        world.say(
            f"The path tried to make {hero.id} small, but {hero.pronoun()} did not turn back."
        )


def arrival(world: World, hero: Entity, shrine: Shrine) -> None:
    hero.meters["traveling"] = 0
    hero.meters["at_shrine"] = 1
    world.say(
        f"At last {hero.id} reached {shrine.label}. The bowl of the dawn lamp was cold, "
        f"and the world still waited."
    )
    propagate(world, narrate=False)


def resolution(world: World, hero: Entity, shrine: Shrine) -> None:
    shrine_ent = world.get("shrine")
    if shrine_ent.meters["lit"] < THRESHOLD:
        raise StoryError("The shrine was not lit; this story configuration is unreasonable.")
    world.say(
        f"{hero.id} tipped the ember into the waiting lamp, and the wick caught at once. "
        f"\"{refrain()}\" {hero.pronoun().capitalize()} said for the third time."
    )
    world.say(
        f"Then {shrine.dawn_image} Even the roofs below seemed to wake and breathe."
    )


def return_image(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["belonging"] += 1
    world.say(
        f"When {hero.id} came home, {elder.id} saw the new light on {hero.pronoun('possessive')} face "
        f"before a word was spoken. The village kept the story, and after that {hero.id} was trusted "
        f"whenever morning needed a steady hand."
    )

def tell(
    weather: Weather,
    vessel: Vessel,
    aid: Aid,
    hero_name: str,
    hero_gender: str,
    elder_name: str,
    elder_type: ElderType,
    shrine=None,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder"))
    ember = world.add(Entity(id="ember", type="ember", label="amber ember", tags={"amber"}))
    shrine_ent = world.add(Entity(id="shrine", type="shrine", label=shrine.label, tags=set(shrine.tags)))
    village = world.add(Entity(id="village", type="village", label="the village"))

    village.meters["darkness"] = 1.0
    ember.meters["glow"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["duty"] = 0.0
    hero.memes["relief"] = 0.0
    hero.meters["traveling"] = 0.0
    hero.meters["steps"] = 0.0
    hero.meters["at_shrine"] = 0.0
    hero.attrs["aid_used"] = False

    world.facts["shrine_peril"] = shrine.peril
    world.facts["shrine_risk"] = shrine.risk
    world.facts["weather_force"] = weather.force
    world.facts["vessel_shield"] = vessel.shield
    world.facts["aid_risk"] = aid.protects
    world.facts["aid_power"] = aid.power
    world.facts["refrain"] = refrain()

    opening(world, hero, elder, shrine, weather)
    world.para()
    flashback(world, hero, elder, shrine)
    charge(world, hero, elder, vessel, aid)
    world.para()
    depart(world, hero, shrine, vessel)
    middle_turn(world, hero, shrine, weather, vessel, aid)
    world.para()
    arrival(world, hero, shrine)
    resolution(world, hero, shrine)
    return_image(world, hero, elder)

    world.facts.update(
        hero=hero,
        elder=elder,
        ember=ember,
        shrine_cfg=shrine,
        weather_cfg=weather,
        vessel_cfg=vessel,
        aid_cfg=aid,
        challenge=challenge_of(
            StoryParams(
                shrine=shrine.id,
                weather=weather.id,
                vessel=vessel.id,
                aid=aid.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                elder_name=elder_name,
                elder_type=elder_type,
                seed=None,
            )
        ),
        lit=shrine_ent.meters["lit"] >= THRESHOLD,
    )
    return world
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


SHRINES = {
    "cliff_lamp": Shrine(
        id="cliff_lamp",
        label="the cliff lamp",
        place="the black sea cliff",
        path_phrase="the salt path above the waves",
        risk="wind",
        peril=2,
        dawn_image="the sea turned from iron to gold, and a bright road ran across the water.",
        flashback_loss="the cliff lamp burn low while the sea wind bit it thin",
        tags={"shrine", "sea", "wind"},
    ),
    "reed_tower": Shrine(
        id="reed_tower",
        label="the reed tower",
        place="the marsh of whispering reeds",
        path_phrase="the narrow boards over the marsh water",
        risk="water",
        peril=2,
        dawn_image="the reeds flashed silver, and the marsh birds rose like thrown leaves.",
        flashback_loss="the marsh stay dim when cold water splashed the lamp before sunrise",
        tags={"shrine", "marsh", "water"},
    ),
    "stone_crown": Shrine(
        id="stone_crown",
        label="the stone crown",
        place="the red hill of standing stones",
        path_phrase="the steep goat steps under the stones",
        risk="stones",
        peril=3,
        dawn_image="the high stones blushed pink, and the first sun touched every doorstep below.",
        flashback_loss="the hill keep its shadows after loose stones scattered a keeper's footing",
        tags={"shrine", "hill", "stones"},
    ),
}

WEATHERS = {
    "sea_wind": Weather(
        id="sea_wind",
        sky="a dark sea sky",
        force=2,
        press_text="The sea wind rushed sideways across the path and clawed at sleeves and hair.",
        air_text="That morning the air smelled of salt, and the stars looked sharp as fish bones.",
        tags={"wind", "weather"},
    ),
    "cold_mist": Weather(
        id="cold_mist",
        sky="a low misty sky",
        force=1,
        press_text="Cold mist gathered on lashes and wrists and made every plank shine.",
        air_text="That morning mist lay on the ground like folded wool.",
        tags={"mist", "weather"},
    ),
    "mountain_gust": Weather(
        id="mountain_gust",
        sky="a hard mountain sky",
        force=3,
        press_text="A mountain gust came down the slope in sudden fists and tried to turn the flame backward.",
        air_text="That morning the hill air was thin and cold, and even the grass bowed one way.",
        tags={"wind", "weather"},
    ),
}

VESSELS = {
    "horn_lantern": Vessel(
        id="horn_lantern",
        label="horn lantern",
        phrase="a horn lantern with a narrow mouth",
        shield=2,
        carry_text="the ember in a horn lantern with both hands",
        keep_text="the horn walls held the worst of the weather away",
        tags={"lantern", "light"},
    ),
    "clay_lamp": Vessel(
        id="clay_lamp",
        label="lidded clay lamp",
        phrase="a lidded clay lamp wrapped in cloth",
        shield=3,
        carry_text="the ember in a warm clay lamp against the chest",
        keep_text="the clay kept the fire close and breathing",
        tags={"lamp", "light"},
    ),
    "shell_cup": Vessel(
        id="shell_cup",
        label="shell cup",
        phrase="a shell cup lined with ash",
        shield=1,
        carry_text="the ember in a shell cup held very still",
        keep_text="the ash steadied the small coal",
        tags={"lamp", "light"},
    ),
}

AIDS = {
    "wind_cord": Aid(
        id="wind_cord",
        label="the wind cord",
        phrase="a braided wind cord",
        protects="wind",
        power=2,
        use_text="It let the child lash lantern to wrist and body, so the gusts could tug but not steal it.",
        tags={"wind", "cord"},
    ),
    "reed_staff": Aid(
        id="reed_staff",
        label="the reed staff",
        phrase="a reed staff polished smooth",
        protects="water",
        power=2,
        use_text="It found the hidden boards and kept the child above the dark water between the reeds.",
        tags={"staff", "water"},
    ),
    "goat_sandals": Aid(
        id="goat_sandals",
        label="the goat sandals",
        phrase="goat-hide sandals with rough soles",
        protects="stones",
        power=3,
        use_text="Their rough soles bit the loose stones, and each step held where a bare foot would have slipped.",
        tags={"sandals", "stones"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Mira", "Daphne", "Eleni", "Rhea"]
BOY_NAMES = ["Timon", "Leander", "Nikos", "Pelas", "Oren", "Theo"]
ELDER_NAMES = ["Neris", "Syla", "Old Phaon", "Maera", "Doros", "Lysa"]


KNOWLEDGE = {
    "amber": [
        (
            "What is amber?",
            "Amber is old tree resin that has turned hard over a very long time. It often shines warm yellow or orange, so people compare it to honey or firelight.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern holds a light so the flame is safer from wind and fingers. It helps people carry light from one place to another.",
        )
    ],
    "lamp": [
        (
            "Why would people keep a lamp at a shrine?",
            "A shrine lamp can be a sign of welcome, memory, or prayer. In a myth, it can also stand for hope or the coming of dawn.",
        )
    ],
    "wind": [
        (
            "Why is wind hard for a small flame?",
            "Wind pushes air against a flame and can bend it or blow it out. A stronger cover helps the flame keep burning.",
        )
    ],
    "water": [
        (
            "Why is a narrow path over water tricky?",
            "Wet boards or stones can be slippery, and the water below can frighten you into hurrying. A staff helps you keep your balance one careful step at a time.",
        )
    ],
    "stones": [
        (
            "Why are loose stones dangerous on a hill?",
            "Loose stones roll under your feet, so you can slip or stumble. Good shoes or sandals help your feet grip the ground.",
        )
    ],
    "shrine": [
        (
            "What is a shrine?",
            "A shrine is a special place set aside for memory, thanks, or worship. People often keep it neat and quiet because it matters to the whole community.",
        )
    ],
}
KNOWLEDGE_ORDER = ["amber", "lantern", "lamp", "wind", "water", "stones", "shrine"]
@dataclass
class StoryParams:
    shrine: str
    weather: str
    vessel: str
    aid: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        shrine="cliff_lamp",
        weather="sea_wind",
        vessel="horn_lantern",
        aid="wind_cord",
        hero_name="Ione",
        hero_gender="girl",
        elder_name="Neris",
        elder_type="grandmother",
        seed=None,
    ),
    StoryParams(
        shrine="reed_tower",
        weather="cold_mist",
        vessel="shell_cup",
        aid="reed_staff",
        hero_name="Timon",
        hero_gender="boy",
        elder_name="Maera",
        elder_type="priestess",
        seed=None,
    ),
    StoryParams(
        shrine="stone_crown",
        weather="mountain_gust",
        vessel="clay_lamp",
        aid="goat_sandals",
        hero_name="Rhea",
        hero_gender="girl",
        elder_name="Old Phaon",
        elder_type="keeper",
        seed=None,
    ),
    StoryParams(
        shrine="reed_tower",
        weather="sea_wind",
        vessel="clay_lamp",
        aid="reed_staff",
        hero_name="Theo",
        hero_gender="boy",
        elder_name="Lysa",
        elder_type="grandmother",
        seed=None,
    ),
    StoryParams(
        shrine="cliff_lamp",
        weather="cold_mist",
        vessel="shell_cup",
        aid="wind_cord",
        hero_name="Daphne",
        hero_gender="girl",
        elder_name="Doros",
        elder_type="keeper",
        seed=None,
    ),
]


def explain_rejection(shrine: Shrine, weather: Weather, vessel: Vessel, aid: Aid) -> str:
    reasons: list[str] = []
    if vessel.shield < weather.force:
        reasons.append(
            f"{vessel.label} shields a flame only up to {vessel.shield}, but {weather.id} presses at {weather.force}"
        )
    if aid.protects != shrine.risk:
        reasons.append(
            f"{aid.label} helps with {aid.protects}, but {shrine.label} is dangerous because of {shrine.risk}"
        )
    elif aid.power < shrine.peril:
        reasons.append(
            f"{aid.label} is too weak for the {shrine.risk} hazard at {shrine.label}"
        )
    if not reasons:
        reasons.append("this combination does not fit the world's reasonableness rules")
    return "(No story: " + "; ".join(reasons) + ".)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    shrine = f["shrine_cfg"]
    weather = f["weather_cfg"]
    return [
        'Write a short myth for a 3-to-5-year-old that includes the word "amber" and uses repetition.',
        f"Tell a mythic story where a child named {hero.label} carries an amber flame to {shrine.label} before dawn while {weather.id.replace('_', ' ')} tests the journey.",
        "Write a gentle myth with a repeated line, an elder's flashback about an earlier mistake, and an ending image that shows morning has truly arrived.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    shrine = f["shrine_cfg"]
    weather = f["weather_cfg"]
    vessel = f["vessel_cfg"]
    aid = f["aid_cfg"]
    challenge = f["challenge"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child trusted with carrying the dawn fire, and {elder.label}, the elder who sends {hero.pronoun('object')} out. Their village is waiting for the shrine lamp to wake the morning.",
        ),
        (
            "What did the elder remember in the flashback?",
            f"{elder.label} remembered an older dawn when {shrine.flashback_loss}. That memory is why {elder.pronoun()} treats the little light so carefully now.",
        ),
        (
            "Why did the child have to carry the amber light?",
            f"{hero.label} had to bring the ember to {shrine.label} so the dawn lamp would be lit before morning. In this myth, the village believes the day comes properly only after that light is returned.",
        ),
        (
            f"How did {hero.label} get through the dangerous part of the path?",
            f"{hero.label} carried the ember in {vessel.phrase} and used {aid.label} on the path. That mattered because the danger there was {shrine.risk}, and the matching aid helped {hero.pronoun('object')} keep going without losing the light.",
        ),
    ]
    if challenge == "narrow":
        qa.append(
            (
                "Was the journey easy or close to failing?",
                f"It came close to failing for a moment. The weather pressed the ember hard or the path was just as difficult as the help could manage, so the child had to be steady instead of quick.",
            )
        )
    else:
        qa.append(
            (
                "Why did the journey work?",
                f"It worked because the chosen lantern and aid truly matched the danger. The vessel protected the flame from the weather, and the path-help fit the hardest part of the shrine road.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the shrine lamp catching and morning showing itself across the land. The final image proves the change: what had been dark and waiting became bright and awake.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"amber", "shrine"}
    tags |= set(f["weather_cfg"].tags)
    tags |= set(f["vessel_cfg"].tags)
    if f["shrine_cfg"].risk in {"water", "stones"}:
        tags.add(f["shrine_cfg"].risk)
    if f["shrine_cfg"].risk == "wind":
        tags.add("wind")
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  challenge={world.facts.get('challenge')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,W,V,A) :- shrine(S), weather(W), vessel(V), aid(A),
                  shield(V,Sh), force(W,F), Sh >= F,
                  risk(S,R), protects(A,R), power(A,P), peril(S,Need), P >= Need.

narrow_case(S,W,V,A) :- valid(S,W,V,A), shield(V,Sh), force(W,F), Sh = F.
narrow_case(S,W,V,A) :- valid(S,W,V,A), power(A,P), peril(S,Need), P = Need.

challenge(S,W,V,A,narrow) :- narrow_case(S,W,V,A).
challenge(S,W,V,A,steady) :- valid(S,W,V,A), not narrow_case(S,W,V,A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shrine_id, shrine in SHRINES.items():
        lines.append(asp.fact("shrine", shrine_id))
        lines.append(asp.fact("risk", shrine_id, shrine.risk))
        lines.append(asp.fact("peril", shrine_id, shrine.peril))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("force", weather_id, weather.force))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("shield", vessel_id, vessel.shield))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("protects", aid_id, aid.protects))
        lines.append(asp.fact("power", aid_id, aid.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_challenge(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.shrine, params.weather, params.vessel, params.aid),
            "picked_challenge(C) :- chosen(S,W,V,A), challenge(S,W,V,A,C).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_challenge/1."))
    atoms = asp.atoms(model, "picked_challenge")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for params in cases:
        py = challenge_of(params)
        asp_val = asp_challenge(params)
        if py != asp_val:
            bad += 1
    if bad == 0:
        print(f"OK: challenge model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} challenge classifications differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic child carries an amber dawn flame."
    )
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandmother", "keeper", "priestess"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shrine and args.weather and args.vessel and args.aid:
        shrine = SHRINES[args.shrine]
        weather = WEATHERS[args.weather]
        vessel = VESSELS[args.vessel]
        aid = AIDS[args.aid]
        if not valid_combo(shrine, weather, vessel, aid):
            raise StoryError(explain_rejection(shrine, weather, vessel, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.shrine is None or combo[0] == args.shrine)
        and (args.weather is None or combo[1] == args.weather)
        and (args.vessel is None or combo[2] == args.vessel)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shrine_id, weather_id, vessel_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, gender)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "keeper", "priestess"])
    return StoryParams(
        shrine=shrine_id,
        weather=weather_id,
        vessel=vessel_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_gender=gender,
        elder_name=elder_name,
        elder_type=elder_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES:
        raise StoryError(f"Unknown shrine: {params.shrine}")
    if params.weather not in WEATHERS:
        raise StoryError(f"Unknown weather: {params.weather}")
    if params.vessel not in VESSELS:
        raise StoryError(f"Unknown vessel: {params.vessel}")
    if params.aid not in AIDS:
        raise StoryError(f"Unknown aid: {params.aid}")

    shrine = SHRINES[params.shrine]
    weather = WEATHERS[params.weather]
    vessel = VESSELS[params.vessel]
    aid = AIDS[params.aid]
    if not valid_combo(shrine, weather, vessel, aid):
        raise StoryError(explain_rejection(shrine, weather, vessel, aid))

    world = tell(
        shrine=shrine,
        weather=weather,
        vessel=vessel,
        aid=aid,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show challenge/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shrine, weather, vessel, aid) combos:\n")
        for shrine, weather, vessel, aid in combos:
            ch = asp_challenge(
                StoryParams(
                    shrine=shrine,
                    weather=weather,
                    vessel=vessel,
                    aid=aid,
                    hero_name="Ione",
                    hero_gender="girl",
                    elder_name="Neris",
                    elder_type="grandmother",
                    seed=None,
                )
            )
            print(f"  {shrine:12} {weather:13} {vessel:12} {aid:12} [{ch}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.hero_name}: {p.shrine} with {p.weather} "
                f"({p.vessel}, {p.aid}, {challenge_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
