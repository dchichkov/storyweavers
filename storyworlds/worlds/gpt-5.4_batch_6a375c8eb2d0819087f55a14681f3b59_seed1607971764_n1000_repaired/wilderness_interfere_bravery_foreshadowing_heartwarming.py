#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py
======================================================================================

A standalone story world about a child in the wilderness who notices a trapped
wild animal, acts with bravery, and helps a grown-up make a careful rescue.

The heart of the world is a simple rule:

    We do not interfere with wild animals just to touch or keep them,
    but we should help and call a grown-up when human-made trash is hurting one.

The story varies over:
- a wilderness place,
- a young wild animal,
- a human-made hazard,
- a sensible rescue tool,
- a weather sign that foreshadows urgency.

Run it
------
python storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py
python storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py --place creek_trail --animal fawn --hazard fishing_line
python storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py --tool bare_hands
python storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py --all --qa
python storyworlds/worlds/gpt-5.4/wilderness_interfere_bravery_foreshadowing_heartwarming.py --verify
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
    attrs: dict = field(default_factory=dict)
    wild: bool = False
    young: bool = False
    # physical and emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_woman", "aunt"}
        male = {"boy", "father", "man", "ranger_man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)
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
    image: str
    hazard_ids: set[str] = field(default_factory=set)
    animal_ids: set[str] = field(default_factory=set)
    risky_water: bool = False
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
class AnimalCfg:
    id: str
    label: str
    cry: str
    move: str
    family: str
    habitat: set[str] = field(default_factory=set)
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
class HazardCfg:
    id: str
    label: str
    material: str
    where: str
    verb: str
    danger: str
    difficulty: int
    human_made: bool = True
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    cuts: set[str] = field(default_factory=set)
    sense: int = 0
    reach: bool = False
    careful: bool = False
    rescue_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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
class WeatherCfg:
    id: str
    hint: str
    foreshadow: str
    sky: str
    urgency: int
    ending_light: str
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


def _r_trapped_worry(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    helper = world.get("helper")
    out: list[str] = []
    if animal.meters["trapped"] >= THRESHOLD:
        sig = ("trapped_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            helper.memes["concern"] += 1
            out.append("__trap__")
    return out


def _r_weather_urgency(world: World) -> list[str]:
    place = world.get("place")
    animal = world.get("animal")
    if animal.meters["trapped"] < THRESHOLD:
        return []
    if place.meters["storm_near"] < THRESHOLD:
        return []
    sig = ("weather_urgency",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["danger"] += 1
    world.get("child").mêmes = getattr(world.get("child"), "mêmes", None)
    world.get("child").memes["fear"] += 1
    return ["__urgency__"]


def _r_rescue_relief(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["trapped"] >= THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    animal.memes["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="trapped_worry", tag="emotional", apply=_r_trapped_worry),
    Rule(name="weather_urgency", tag="physical", apply=_r_weather_urgency),
    Rule(name="rescue_relief", tag="emotional", apply=_r_rescue_relief),
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


def tool_can_free(tool: ToolCfg, hazard: HazardCfg, weather: WeatherCfg, place: Place) -> bool:
    if tool.sense < SENSE_MIN:
        return False
    if hazard.material not in tool.cuts:
        return False
    need_reach = place.risky_water or weather.urgency >= 2
    if need_reach and not tool.reach:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id, animal in ANIMALS.items():
            if animal_id not in place.animal_ids:
                continue
            for hazard_id, hazard in HAZARDS.items():
                if hazard_id not in place.hazard_ids:
                    continue
                if not hazard.human_made:
                    continue
                for weather_id, weather in WEATHER.items():
                    for tool_id, tool in TOOLS.items():
                        if tool_can_free(tool, hazard, weather, place):
                            combos.append((place_id, animal_id, hazard_id, tool_id, weather_id))
    return combos


def explain_rejection(place: Place, animal: AnimalCfg, hazard: HazardCfg, tool: ToolCfg,
                      weather: WeatherCfg) -> str:
    if animal.id not in place.animal_ids:
        return (
            f"(No story: a {animal.label} does not fit naturally at {place.label}. "
            f"Pick an animal that belongs in that part of the wilderness.)"
        )
    if hazard.id not in place.hazard_ids:
        return (
            f"(No story: {hazard.label} is not a sensible hazard for {place.label}. "
            f"Choose a place where that kind of litter could really appear.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). The rescue should use a calmer, safer tool.)"
        )
    if hazard.material not in tool.cuts:
        return (
            f"(No story: {tool.label} cannot deal with {hazard.label}. "
            f"The rescue tool must actually work on the material that is trapping the animal.)"
        )
    if (place.risky_water or weather.urgency >= 2) and not tool.reach:
        return (
            f"(No story: at {place.label} with {weather.hint}, the rescue needs a tool "
            f"that lets the grown-up keep a safer distance. Try rescue snips or a ranger pole cutter.)"
        )
    return "(No valid combination matches the given options.)"


def predict_danger(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "animal_trapped": sim.get("animal").meters["trapped"] >= THRESHOLD,
        "storm_near": sim.get("place").meters["storm_near"] >= THRESHOLD,
        "danger": sim.get("animal").meters["danger"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place, weather: WeatherCfg) -> None:
    world.say(
        f"{child.id} walked through the wilderness with {child.pronoun('possessive')} "
        f"{helper.label_word} along {place.label}. {place.image}"
    )
    world.say(
        f"{weather.sky} {weather.foreshadow}"
    )


def teach_rule(world: World, helper: Entity) -> None:
    world.say(
        f'"Remember," said {helper.label_word}, "we do not interfere with wild animals '
        f'just because we want to touch them. But if people\'s trash is hurting one, '
        f'we help carefully and call for a grown-up right away."'
    )


def notice(world: World, child: Entity, animal: Entity, animal_cfg: AnimalCfg, hazard: HazardCfg) -> None:
    animal.meters["trapped"] += 1
    animal.meters["danger"] += 1
    world.say(
        f"A thin {animal_cfg.cry} drifted from the brush. {child.id} pushed aside a fern "
        f"and found a {animal_cfg.label} with {hazard.label} {hazard.verb} {hazard.where}."
    )
    propagate(world, narrate=False)
    world.say(
        f"The little animal tried to {animal_cfg.move}, but {hazard.danger}."
    )


def brave_speak(world: World, child: Entity, helper: Entity, weather: WeatherCfg) -> None:
    child.memes["bravery"] += 1
    pred = predict_danger(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{child.id} felt a shaky thump in {child.pronoun("possessive")} chest, yet '
        f'{child.pronoun()} stood very still. "Please come quick," {child.pronoun()} said. '
        f'"The sky looks like {weather.hint}, and it may get harder for the little one."'
    )


def assess(world: World, helper: Entity, tool: ToolCfg, hazard: HazardCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} knelt beside {world.get('child').id} and looked without reaching in at once. "
        f'"Good noticing," {helper.pronoun()} said softly. "It is {hazard.label}. '
        f'We will use {tool.phrase} and keep our hands calm."'
    )


def rescue(world: World, child: Entity, helper: Entity, animal: Entity,
           animal_cfg: AnimalCfg, hazard: HazardCfg, tool: ToolCfg, weather: WeatherCfg) -> None:
    child.memes["bravery"] += 1
    helper.memes["skill"] += 1
    animal.meters["trapped"] = 0.0
    animal.meters["danger"] = 0.0
    animal.meters["free"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} held the fern stems aside and did not wiggle or grab. "
        f"{helper.label_word.capitalize()} {tool.rescue_text.format(hazard=hazard.label)}."
    )
    world.say(
        f"For one breath nothing moved. Then the {animal_cfg.label} gave a tiny shake, "
        f"lifted {animal_cfg.family}, and was free."
    )
    world.say(
        f"The clouds came no closer than a warning after all, but that earlier hush in the air "
        f"made the brave moment feel even bigger."
    )


def aftercare(world: World, child: Entity, helper: Entity, animal_cfg: AnimalCfg,
              place: Place, weather: WeatherCfg) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'Together they stepped back and let the {animal_cfg.label} choose its own path. '
        f'"That is the kind way," said {helper.label_word}. "Help, then give wild things room."'
    )
    world.say(
        f"They tucked the cut trash into a trail bag so it could not hurt anything else in the wilderness."
    )
    world.say(
        f"Soon the {animal_cfg.label} slipped into the leaves, and {weather.ending_light} lay over "
        f"{place.label} like a warm thank-you."
    )


def tell(place: Place, animal_cfg: AnimalCfg, hazard: HazardCfg, tool: ToolCfg,
         weather: WeatherCfg, child_name: str = "Mira", child_type: str = "girl",
         helper_type: str = "aunt") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    animal = world.add(Entity(id="animal", kind="thing", type=animal_cfg.id, label=animal_cfg.label, role="animal",
                              wild=True, young=True))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, role="place"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, role="tool"))
    hazard_ent = world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label, role="hazard"))

    place_ent.meters["storm_near"] = float(weather.urgency)
    animal.meters["trapped"] = 0.0
    animal.meters["danger"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["bravery"] = 0.0
    helper.memes["concern"] = 0.0

    world.facts.update(
        place_cfg=place,
        animal_cfg=animal_cfg,
        hazard_cfg=hazard,
        tool_cfg=tool,
        weather_cfg=weather,
        child=child,
        helper=helper,
        animal=animal,
        tool=tool_ent,
        hazard=hazard_ent,
    )

    introduce(world, child, helper, place, weather)
    teach_rule(world, helper)

    world.para()
    notice(world, child, animal, animal_cfg, hazard)
    brave_speak(world, child, helper, weather)
    assess(world, helper, tool, hazard)

    world.para()
    rescue(world, child, helper, animal, animal_cfg, hazard, tool, weather)
    aftercare(world, child, helper, animal_cfg, place, weather)

    world.facts.update(
        rescued=animal.meters["free"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD,
        storm_near=place_ent.meters["storm_near"] >= THRESHOLD,
        place=place_ent,
    )
    return world


PLACES = {
    "creek_trail": Place(
        id="creek_trail",
        label="the creek trail",
        image="Fir trees leaned over the path, and the creek flashed silver below the stones.",
        hazard_ids={"fishing_line", "plastic_ring"},
        animal_ids={"fawn", "duckling"},
        risky_water=True,
        tags={"wilderness", "creek"},
    ),
    "pine_meadow": Place(
        id="pine_meadow",
        label="the pine meadow",
        image="Tall grass moved in soft waves, and a row of pines kept the edge of the path cool and green.",
        hazard_ids={"plastic_ring", "snare_wire"},
        animal_ids={"fawn", "fox_cub"},
        risky_water=False,
        tags={"wilderness", "meadow"},
    ),
    "rocky_overlook": Place(
        id="rocky_overlook",
        label="the rocky overlook",
        image="Gray stones warmed in the sun, and little juniper bushes clung to the hillside.",
        hazard_ids={"fishing_line", "snare_wire"},
        animal_ids={"fox_cub", "duckling"},
        risky_water=True,
        tags={"wilderness", "rocks"},
    ),
}

ANIMALS = {
    "fawn": AnimalCfg(
        id="fawn",
        label="fawn",
        cry="bleat",
        move="pull away",
        family="its knees",
        habitat={"creek_trail", "pine_meadow"},
        tags={"deer", "wildlife"},
    ),
    "fox_cub": AnimalCfg(
        id="fox_cub",
        label="fox cub",
        cry="yip",
        move="twist free",
        family="its paws",
        habitat={"pine_meadow", "rocky_overlook"},
        tags={"fox", "wildlife"},
    ),
    "duckling": AnimalCfg(
        id="duckling",
        label="duckling",
        cry="peep",
        move="flutter and kick",
        family="its wet feet",
        habitat={"creek_trail", "rocky_overlook"},
        tags={"duck", "wildlife"},
    ),
}

HAZARDS = {
    "fishing_line": HazardCfg(
        id="fishing_line",
        label="fishing line",
        material="line",
        where="around one leg",
        verb="looped tightly",
        danger="the more it fought, the more the clear strand bit in",
        difficulty=2,
        human_made=True,
        tags={"trash", "line"},
    ),
    "plastic_ring": HazardCfg(
        id="plastic_ring",
        label="a plastic ring",
        material="plastic",
        where="around its middle",
        verb="caught snugly",
        danger="each frightened breath pressed the ring harder",
        difficulty=1,
        human_made=True,
        tags={"trash", "plastic"},
    ),
    "snare_wire": HazardCfg(
        id="snare_wire",
        label="snare wire",
        material="wire",
        where="through the grass by one paw",
        verb="twisted cruelly",
        danger="every little jerk pulled the wire tighter",
        difficulty=2,
        human_made=True,
        tags={"wire", "trash"},
    ),
}

TOOLS = {
    "rescue_snips": ToolCfg(
        id="rescue_snips",
        label="rescue snips",
        phrase="the rescue snips from the pack",
        cuts={"line", "plastic", "wire"},
        sense=3,
        reach=True,
        careful=True,
        rescue_text="slid the rescue snips under the {hazard} and clipped once, clean and quick",
        fail_text="tried to reach the trap, but the tool was wrong for the job",
        qa_text="used rescue snips to cut the trap safely",
        tags={"rescue_tool", "snips"},
    ),
    "pole_cutter": ToolCfg(
        id="pole_cutter",
        label="a ranger pole cutter",
        phrase="the ranger pole cutter",
        cuts={"line", "plastic", "wire"},
        sense=3,
        reach=True,
        careful=True,
        rescue_text="reached with the pole cutter and opened the {hazard} without crowding the frightened animal",
        fail_text="reached in, but the trap sat in the wrong place for the pole cutter",
        qa_text="used a pole cutter to free the animal from a safer distance",
        tags={"rescue_tool", "pole"},
    ),
    "camp_scissors": ToolCfg(
        id="camp_scissors",
        label="camp scissors",
        phrase="the little camp scissors",
        cuts={"line", "plastic"},
        sense=2,
        reach=False,
        careful=True,
        rescue_text="worked the camp scissors in gently and cut through the {hazard}",
        fail_text="snipped and snipped, but the tool could not reach well enough",
        qa_text="used camp scissors to cut the trap",
        tags={"rescue_tool", "scissors"},
    ),
    "bare_hands": ToolCfg(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        cuts=set(),
        sense=1,
        reach=False,
        careful=False,
        rescue_text="pulled at the trap with bare hands",
        fail_text="tried to pull the trap loose by hand",
        qa_text="pulled at the trap by hand",
        tags={"unsafe"},
    ),
}

WEATHER = {
    "golden_evening": WeatherCfg(
        id="golden_evening",
        hint="a quiet evening light",
        foreshadow="Even so, the wind had gone oddly still, as if the day were waiting for something.",
        sky="Late sunlight spilled between the branches.",
        urgency=1,
        ending_light="golden light",
        tags={"light"},
    ),
    "rain_smell": WeatherCfg(
        id="rain_smell",
        hint="rain in the air",
        foreshadow="A wet smell drifted up from the earth, and clouds were quietly gathering behind the hills.",
        sky="The sky was pale, but the edges of the clouds were turning darker.",
        urgency=2,
        ending_light="a silver patch of sky",
        tags={"rain"},
    ),
    "distant_thunder": WeatherCfg(
        id="distant_thunder",
        hint="distant thunder",
        foreshadow="Far away, thunder rolled once, so softly that it felt more like a warning than a sound.",
        sky="The air looked bright, but a dark band rested low beyond the trees.",
        urgency=2,
        ending_light="one calm stripe of sun",
        tags={"storm"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Theo", "Milo", "Sam", "Noah", "Eli"]


@dataclass
class StoryParams:
    place: str
    animal: str
    hazard: str
    tool: str
    weather: str
    child_name: str
    child_type: str
    helper_type: str
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
        place="creek_trail",
        animal="duckling",
        hazard="fishing_line",
        tool="rescue_snips",
        weather="rain_smell",
        child_name="Mira",
        child_type="girl",
        helper_type="aunt",
    ),
    StoryParams(
        place="pine_meadow",
        animal="fawn",
        hazard="plastic_ring",
        tool="camp_scissors",
        weather="golden_evening",
        child_name="Owen",
        child_type="boy",
        helper_type="father",
    ),
    StoryParams(
        place="rocky_overlook",
        animal="fox_cub",
        hazard="snare_wire",
        tool="pole_cutter",
        weather="distant_thunder",
        child_name="Lina",
        child_type="girl",
        helper_type="ranger_woman",
    ),
]


KNOWLEDGE = {
    "wilderness": [
        (
            "What does wilderness mean?",
            "Wilderness means a wild natural place with trees, rocks, water, and animals living there. People visit it, but it mostly belongs to nature."
        )
    ],
    "interfere": [
        (
            "What does interfere mean in this kind of story?",
            "To interfere means to step in and change what is happening. With wild animals, people should not interfere for fun, but they should help when something dangerous made by people is hurting an animal."
        )
    ],
    "trash": [
        (
            "Why is litter dangerous for wild animals?",
            "Litter can wrap around bodies, legs, or mouths and make it hard for animals to move or breathe. Something small to us can become a big trap to them."
        )
    ],
    "line": [
        (
            "Why is fishing line dangerous?",
            "Fishing line is thin and hard to see, but it can tangle around an animal and tighten when the animal struggles. That can hurt skin and stop safe movement."
        )
    ],
    "wire": [
        (
            "Why is wire dangerous to animals?",
            "Wire can twist tightly and dig into fur or skin. It is strong, so an animal may not be able to pull free alone."
        )
    ],
    "plastic": [
        (
            "Why can a plastic ring hurt an animal?",
            "A plastic ring can get stuck around part of an animal's body as it grows or squirms. Then the ring rubs and squeezes instead of coming off."
        )
    ],
    "rescue_tool": [
        (
            "Why is a rescue tool better than using bare hands?",
            "A rescue tool lets a grown-up work carefully and from a safer distance. That helps the animal and keeps people from startling it or getting hurt."
        )
    ],
    "storm": [
        (
            "Why can bad weather make a rescue more urgent?",
            "Rain or thunder can make the ground slippery and scare an already trapped animal. That means a problem can get worse if nobody helps soon."
        )
    ],
}
KNOWLEDGE_ORDER = ["wilderness", "interfere", "trash", "line", "wire", "plastic", "rescue_tool", "storm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    hazard = f["hazard_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that uses the words "wilderness" and "interfere".',
        f"Tell a gentle wilderness rescue story where {child.id} notices a {animal.label} trapped by {hazard.label} at {place.label} and shows bravery by calling a grown-up.",
        f"Write a story with foreshadowing in the sky, a careful rescue by {child.id}'s {helper.label_word}, and an ending where the wild animal is free again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    hazard = f["hazard_cfg"]
    tool = f["tool_cfg"]
    weather = f["weather_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {helper.label_word} in the wilderness. They find a young {animal.label} that needs careful help."
        ),
        (
            f"What first told {child.id} that something was wrong?",
            f"{child.id} heard a small {animal.cry} from the brush and then saw the trapped {animal.label}. The sound came before the sight, which made the discovery feel urgent and important."
        ),
        (
            "What did the foreshadowing in the story do?",
            f"The still air and {weather.hint} hinted that time mattered before the rescue even began. When the trapped animal was found, that earlier warning made the danger feel more real."
        ),
        (
            f"Why did they help instead of walking away and not interfere?",
            f"They had learned not to interfere with wild animals for fun, but this was different because human-made trash was hurting the little one. Helping was the kind and responsible thing to do."
        ),
        (
            f"How did {child.id} show bravery?",
            f"{child.id} felt scared, but spoke up right away and stayed calm beside the grown-up. That bravery mattered because quick noticing and steady hands helped the rescue happen safely."
        ),
        (
            f"How did {helper.label_word} free the {animal.label}?",
            f"{helper.label_word.capitalize()} {tool.qa_text}. The right tool matched the trap, so the rescue could be careful instead of rough."
        ),
        (
            "How did the story end?",
            f"The {animal.label} was freed, they packed the dangerous trash away, and the path felt peaceful again. The ending shows that brave help can be gentle and leave the wilderness safer than before."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"wilderness", "interfere", "trash", "rescue_tool"}
    hazard = world.facts["hazard_cfg"]
    weather = world.facts["weather_cfg"]
    if hazard.material == "line":
        tags.add("line")
    if hazard.material == "wire":
        tags.add("wire")
    if hazard.material == "plastic":
        tags.add("plastic")
    if weather.urgency >= 2:
        tags.add("storm")
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
habitat_ok(P,A) :- place(P), animal(A), lives_in(A,P).
hazard_ok(P,H)  :- place(P), hazard(H), found_at(P,H).

sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
cuts_ok(T,H)     :- tool(T), hazard(H), material(H,M), cuts(T,M).

need_reach(P,W)  :- risky_water(P).
need_reach(P,W)  :- weather(W), urgency(W,U), U >= 2.
reach_ok(T,P,W)  :- not need_reach(P,W).
reach_ok(T,P,W)  :- need_reach(P,W), reach(T).

valid(P,A,H,T,W) :- habitat_ok(P,A), hazard_ok(P,H),
                    sensible_tool(T), cuts_ok(T,H), reach_ok(T,P,W).

#show valid/5.
#show sensible_tool/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.risky_water:
            lines.append(asp.fact("risky_water", place_id))
        for hazard_id in sorted(place.hazard_ids):
            lines.append(asp.fact("found_at", place_id, hazard_id))
        for animal_id in sorted(place.animal_ids):
            lines.append(asp.fact("lives_in", animal_id, place_id))
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("material", hazard_id, hazard.material))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.reach:
            lines.append(asp.fact("reach", tool_id))
        for material in sorted(tool.cuts):
            lines.append(asp.fact("cuts", tool_id, material))
    for weather_id, weather in WEATHER.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("urgency", weather_id, weather.urgency))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave child notices a trapped wild animal and helps with a careful rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle", "ranger_woman", "ranger_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.animal and args.hazard and args.tool and args.weather:
        place = PLACES[args.place]
        animal = ANIMALS[args.animal]
        hazard = HAZARDS[args.hazard]
        tool = TOOLS[args.tool]
        weather = WEATHER[args.weather]
        if not tool_can_free(tool, hazard, weather, place) or args.animal not in place.animal_ids or args.hazard not in place.hazard_ids:
            raise StoryError(explain_rejection(place, animal, hazard, tool, weather))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.tool is None or combo[3] == args.tool)
        and (args.weather is None or combo[4] == args.weather)
    ]
    if not combos:
        if args.place and args.animal and args.hazard and args.tool and args.weather:
            raise StoryError(
                explain_rejection(
                    PLACES[args.place],
                    ANIMALS[args.animal],
                    HAZARDS[args.hazard],
                    TOOLS[args.tool],
                    WEATHER[args.weather],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, animal_id, hazard_id, tool_id, weather_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle", "ranger_woman", "ranger_man"])
    return StoryParams(
        place=place_id,
        animal=animal_id,
        hazard=hazard_id,
        tool=tool_id,
        weather=weather_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        animal = ANIMALS[params.animal]
        hazard = HAZARDS[params.hazard]
        tool = TOOLS[params.tool]
        weather = WEATHER[params.weather]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from None

    if params.animal not in place.animal_ids or params.hazard not in place.hazard_ids or not tool_can_free(tool, hazard, weather, place):
        raise StoryError(explain_rejection(place, animal, hazard, tool, weather))

    world = tell(
        place=place,
        animal_cfg=animal,
        hazard=hazard,
        tool=tool,
        weather=weather,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: valid story set matches ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid story set:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens = set(asp_sensible_tools())
    psens = {tool_id for tool_id, tool in TOOLS.items() if tool.sense >= SENSE_MIN}
    if csens == psens:
        print(f"OK: sensible tools match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(csens)} python={sorted(psens)}")

    smoke_cases = list(CURATED)
    for seed in range(6):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE-SETUP FAILED for seed {seed}")
    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "wilderness" not in sample.story or "interfere" not in sample.story:
                raise StoryError("required seed words missing from story")
        except Exception as exc:
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {exc}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
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
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        print(f"{len(combos)} valid (place, animal, hazard, tool, weather) combos:\n")
        for place, animal, hazard, tool, weather in combos:
            print(f"  {place:14} {animal:9} {hazard:13} {tool:13} {weather}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.animal} at {p.place} ({p.hazard}, {p.tool}, {p.weather})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
