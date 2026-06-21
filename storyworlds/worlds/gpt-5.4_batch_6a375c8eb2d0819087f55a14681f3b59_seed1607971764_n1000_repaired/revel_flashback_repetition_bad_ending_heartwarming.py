#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py
================================================================================

A standalone story world for a tiny heartwarming lantern-revel tale with a
flashback, a repeated line, and sometimes a bad ending. A child carries a
homemade lantern toward an evening revel. The lantern holds memory as well as
light. Weather threatens it, a grown-up tries to protect it, and the ending
depends on whether that protection is enough.

This world models:
- typed entities with physical meters and emotional memes
- a short forward-chaining causal engine
- a reasonableness gate over weather, lantern, and cover choices
- an inline ASP twin for the same gate and the outcome model
- three Q&A sets grounded in the simulated world state

Run it
------
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py --weather gusts
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py --cover scarf_wrap
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/revel_flashback_repetition_bad_ending_heartwarming.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
class Setting:
    id: str
    place: str
    path: str
    ending_place: str
    revel_name: str
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
    hazard: str
    severity: int
    sky_text: str
    threat_text: str
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
class Lantern:
    id: str
    label: str
    phrase: str
    material: str
    weak_to: set[str]
    fragility: int
    glow_text: str
    maker_role: str
    maker_line: str
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
class Cover:
    id: str
    label: str
    protects: set[str]
    sense: int
    power: int
    use_text: str
    fail_text: str
    qa_text: str
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
class Warmth:
    id: str
    drink: str
    window_light: str
    closing_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_hazard_hits(world: World) -> list[str]:
    child = world.get("child")
    lantern = world.get("lantern")
    weather = world.facts["weather_cfg"]
    if lantern.meters["lit"] < THRESHOLD:
        return []
    if weather.hazard not in world.facts["lantern_cfg"].weak_to:
        return []
    if child.meters["shield"] >= THRESHOLD:
        return []
    sig = ("hazard_hits", weather.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lantern.meters["strain"] += 1
    child.memes["worry"] += 1
    return ["__hazard__"]


def _r_lantern_lost(world: World) -> list[str]:
    lantern = world.get("lantern")
    child = world.get("child")
    if lantern.meters["strain"] < THRESHOLD:
        return []
    sig = ("lantern_lost",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lantern.meters["lit"] = 0.0
    lantern.meters["lost"] += 1
    child.memes["grief"] += 1
    world.get("path").meters["missed_revel"] += 1
    return ["__lost__"]


def _r_comfort(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["held"] < THRESHOLD:
        return []
    sig = ("comfort",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["comfort"] += 1
    child.memes["grief"] = max(0.0, child.memes["grief"] - 1.0)
    helper.memes["care"] += 1
    return ["__comfort__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hazard_hits", tag="physical", apply=_r_hazard_hits),
    Rule(name="lantern_lost", tag="physical", apply=_r_lantern_lost),
    Rule(name="comfort", tag="social", apply=_r_comfort),
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


def lantern_at_risk(weather: Weather, lantern: Lantern) -> bool:
    return weather.hazard in lantern.weak_to


def sensible_covers() -> list[Cover]:
    return [c for c in COVERS.values() if c.sense >= SENSE_MIN]


def total_risk(weather: Weather, lantern: Lantern) -> int:
    return weather.severity + lantern.fragility


def is_saved(weather: Weather, lantern: Lantern, cover: Cover) -> bool:
    if weather.hazard not in cover.protects:
        return False
    return cover.power >= total_risk(weather, lantern)


def predict_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["shield"] = 0.0
    propagate(sim, narrate=False)
    return {
        "lost": sim.get("lantern").meters["lost"] >= THRESHOLD,
        "missed_revel": sim.get("path").meters["missed_revel"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, lantern_cfg: Lantern) -> None:
    child.memes["hope"] += 1
    lantern = world.get("lantern")
    lantern.meters["lit"] = 1.0
    world.say(
        f"{child.id} held {lantern_cfg.phrase} with both hands as dusk gathered over "
        f"{world.setting.place}. Tonight the whole street would walk to {world.setting.revel_name}, "
        f"and little lights would bob like stars."
    )
    world.say(
        f"The lantern glowed softly; {lantern_cfg.glow_text}. {child.id} whispered, "
        f'"{lantern_cfg.maker_line}"'
    )


def flashback(world: World, child: Entity, helper: Entity, lantern_cfg: Lantern) -> None:
    world.say(
        f"That whisper brought a flashback. Earlier that afternoon, {child.id} had sat at the table with "
        f"{helper.label_word}, folding {lantern_cfg.material} into careful corners while "
        f"{helper.pronoun()} smiled and said, \"{lantern_cfg.maker_line}\""
    )
    child.memes["memory"] += 1


def set_out(world: World, child: Entity, weather: Weather) -> None:
    world.say(
        f"They stepped onto {world.setting.path}. {weather.sky_text}. "
        f"{weather.threat_text}"
    )


def warning(world: World, child: Entity, helper: Entity, weather: Weather, lantern_cfg: Lantern) -> None:
    pred = predict_loss(world)
    world.facts["predicted_loss"] = pred["lost"]
    child.memes["worry"] += 1
    if pred["lost"]:
        world.say(
            f'"Keep close," {helper.label_word} said. "Your {lantern_cfg.label} is lovely, '
            f'but {weather.label} can spoil a tender light."'
        )


def try_cover(world: World, child: Entity, helper: Entity, cover: Cover, lantern_cfg: Lantern) -> None:
    child.meters["shield"] = 1.0
    child.memes["trust"] += 1
    world.say(
        f'{helper.label_word.capitalize()} {cover.use_text}. "{lantern_cfg.maker_line}," '
        f"{child.id} said again, smaller this time."
    )


def lose_cover(world: World) -> None:
    world.get("child").meters["shield"] = 0.0


def bad_turn(world: World, child: Entity, helper: Entity, weather: Weather, lantern_cfg: Lantern, cover: Cover) -> None:
    lose_cover(world)
    propagate(world, narrate=False)
    world.say(
        f"But {weather.label} pressed harder. {cover.fail_text}, and the little lantern gave a sad shiver."
    )
    if world.get("lantern").meters["lost"] >= THRESHOLD:
        if weather.hazard == "wind":
            world.say(
                f"The flame went out, and one thin side of the {lantern_cfg.label} crumpled in on itself."
            )
        else:
            world.say(
                f"Moisture dotted the {lantern_cfg.material}, and the warm glow sank into darkness."
            )
    world.say(
        f'The music from {world.setting.revel_name} kept floating ahead, but {child.id} stopped walking. '
        f'"{lantern_cfg.maker_line}," {child.pronoun()} whispered once more, and now it sounded like a wish.'
    )


def good_turn(world: World, child: Entity, helper: Entity, cover: Cover) -> None:
    child.memes["relief"] += 1
    helper.memes["care"] += 1
    world.say(
        f"The cover held. The light stayed steady inside it, and the two of them walked on together."
    )


def join_revel(world: World, child: Entity, helper: Entity, lantern_cfg: Lantern) -> None:
    child.memes["belonging"] += 1
    world.say(
        f"When they reached {world.setting.revel_name}, rows of neighbors smiled at the small glow in "
        f"{child.id}'s hands. The repeated words had carried {child.pronoun('object')} all the way there."
    )
    world.say(
        f"Soon {child.id} was laughing among the lights, and {helper.label_word} watched with shining eyes as "
        f"the lantern swayed gently and safe."
    )


def comfort_bad_ending(
    world: World,
    child: Entity,
    helper: Entity,
    warmth: Warmth,
    lantern_cfg: Lantern,
) -> None:
    child.memes["held"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id} and wrapped an arm around '
        f"{child.pronoun('object')}. \"We can miss the revel and still keep its warm part,\" "
        f"{helper.pronoun()} said softly."
    )
    world.say(
        f"They turned back toward {world.setting.ending_place}, carrying the dark lantern very gently."
    )
    world.say(
        f"At home, {helper.label_word} poured {warmth.drink}, set {warmth.window_light} in the window, "
        f"and together they looked out at the far-off line of tiny lights."
    )
    world.say(
        f"{warmth.closing_text} The lantern had gone dark, but the memory inside it had not."
    )
    child.memes["belonging"] += 1


def tell(
    setting: Setting,
    weather: Weather,
    lantern_cfg: Lantern,
    cover: Cover,
    warmth: Warmth,
    child_name: str = "Mira",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, role="child", label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, role="helper", label="the helper"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", role="prize", label=lantern_cfg.label))
    path = world.add(Entity(id="path", kind="thing", type="path", role="path", label=setting.path))

    child.attrs["name"] = child_name
    helper.attrs["name"] = helper.label_word
    world.facts["weather_cfg"] = weather
    world.facts["lantern_cfg"] = lantern_cfg
    world.facts["cover_cfg"] = cover
    world.facts["warmth_cfg"] = warmth

    child.meters["shield"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["grief"] = 0.0
    child.memes["comfort"] = 0.0
    child.memes["held"] = 0.0
    helper.memes["care"] = 0.0
    lantern.meters["lit"] = 0.0
    lantern.meters["strain"] = 0.0
    lantern.meters["lost"] = 0.0
    path.meters["missed_revel"] = 0.0

    opening(world, child, helper, lantern_cfg)
    flashback(world, child, helper, lantern_cfg)

    world.para()
    set_out(world, child, weather)
    warning(world, child, helper, weather, lantern_cfg)
    try_cover(world, child, helper, cover, lantern_cfg)

    saved = is_saved(weather, lantern_cfg, cover)
    world.facts["saved"] = saved
    world.facts["outcome"] = "kept" if saved else "missed"
    world.facts["repeated_line"] = lantern_cfg.maker_line

    world.para()
    if saved:
        good_turn(world, child, helper, cover)
        join_revel(world, child, helper, lantern_cfg)
    else:
        bad_turn(world, child, helper, weather, lantern_cfg, cover)
        world.para()
        comfort_bad_ending(world, child, helper, warmth, lantern_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        lantern=lantern,
        path=path,
        setting=setting,
        weather=weather,
        lantern_cfg=lantern_cfg,
        cover=cover,
        warmth=warmth,
        missed=path.meters["missed_revel"] >= THRESHOLD,
        lost=lantern.meters["lost"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lane": Setting(
        id="lane",
        place="the little lane by the churchyard",
        path="the cobbled lane",
        ending_place="their front porch",
        revel_name="the winter revel",
        tags={"revel"},
    ),
    "green": Setting(
        id="green",
        place="the village green",
        path="the narrow footpath",
        ending_place="their kitchen window",
        revel_name="the lantern revel",
        tags={"revel"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor road",
        path="the salt-smelling path",
        ending_place="their window seat",
        revel_name="the harbor revel",
        tags={"revel"},
    ),
}

WEATHERS = {
    "mist": Weather(
        id="mist",
        label="a silvery mist",
        hazard="damp",
        severity=1,
        sky_text="A pale mist sat over the hedges like breath on a mirror",
        threat_text="The damp touched cheeks and sleeves, soft at first",
        tags={"weather", "damp"},
    ),
    "drizzle": Weather(
        id="drizzle",
        label="a thin drizzle",
        hazard="damp",
        severity=2,
        sky_text="A thin drizzle stitched the air with tiny silver threads",
        threat_text="Each drop was small, but they kept coming",
        tags={"weather", "rain"},
    ),
    "gusts": Weather(
        id="gusts",
        label="restless gusts",
        hazard="wind",
        severity=2,
        sky_text="Clouds hurried overhead while restless gusts fussed at coats and scarves",
        threat_text="The wind kept reaching for every loose edge",
        tags={"weather", "wind"},
    ),
    "hard_wind": Weather(
        id="hard_wind",
        label="a hard river wind",
        hazard="wind",
        severity=3,
        sky_text="The river wind came in strong breaths that bent the reeds and rattled signs",
        threat_text="It snatched at anything light enough to lift",
        tags={"weather", "wind"},
    ),
}

LANTERNS = {
    "star": Lantern(
        id="star",
        label="star lantern",
        phrase="a small star lantern",
        material="gold tissue paper",
        weak_to={"wind", "damp"},
        fragility=1,
        glow_text="it turned the paper stars on its sides amber and honey-soft",
        maker_role="grandmother",
        maker_line="Steady hands, warm light",
        tags={"lantern", "memory"},
    ),
    "leaf": Lantern(
        id="leaf",
        label="leaf lantern",
        phrase="a leaf lantern stitched from pressed leaves and thin paper",
        material="pressed leaves and thin paper",
        weak_to={"wind"},
        fragility=1,
        glow_text="veins in the leaves shone like tiny golden roads",
        maker_role="grandfather",
        maker_line="Steady hands, warm light",
        tags={"lantern", "memory"},
    ),
    "waxed": Lantern(
        id="waxed",
        label="wax-paper lantern",
        phrase="a wax-paper lantern with a blue handle",
        material="wax paper",
        weak_to={"wind"},
        fragility=0,
        glow_text="the blue handle looked bright against the warm little flame",
        maker_role="mother",
        maker_line="Steady hands, warm light",
        tags={"lantern", "memory"},
    ),
}

COVERS = {
    "umbrella": Cover(
        id="umbrella",
        label="umbrella",
        protects={"damp"},
        sense=3,
        power=3,
        use_text="opened the umbrella over the lantern and tucked the handle close under one arm",
        fail_text="a sideways gust slipped under the umbrella's edge",
        qa_text="held an umbrella over the lantern",
        tags={"umbrella", "cover"},
    ),
    "glass_jar": Cover(
        id="glass_jar",
        label="glass jar shield",
        protects={"wind", "damp"},
        sense=3,
        power=4,
        use_text="slid the lantern into a clear glass jar and left the top open just enough for air",
        fail_text="the weather worried at the jar until even that careful shelter trembled",
        qa_text="slid the lantern into a clear glass jar to shield it",
        tags={"jar", "cover"},
    ),
    "cloak_fold": Cover(
        id="cloak_fold",
        label="cloak fold",
        protects={"wind"},
        sense=2,
        power=2,
        use_text="cupped a fold of the old cloak around the lantern and walked shoulder to shoulder with the child",
        fail_text="the cloth fluttered back for one unlucky moment",
        qa_text="used a fold of the cloak to block the wind",
        tags={"cloak", "cover"},
    ),
    "scarf_wrap": Cover(
        id="scarf_wrap",
        label="scarf wrap",
        protects={"wind"},
        sense=1,
        power=1,
        use_text="tried to wrap a scarf around the handle and around little fingers too",
        fail_text="the scarf slipped and pulled the lantern off balance",
        qa_text="tried to wrap the lantern with a scarf",
        tags={"scarf", "cover"},
    ),
}

WARMTHS = {
    "cocoa": Warmth(
        id="cocoa",
        drink="hot cocoa into two round mugs",
        window_light="a safe lamp",
        closing_text="They listened to the faraway singing and let the room feel like its own small revel",
        tags={"cocoa", "comfort"},
    ),
    "tea": Warmth(
        id="tea",
        drink="warm tea and honey into two cups",
        window_light="a candle-safe lantern",
        closing_text="They watched the moving lights together and talked about the careful hands that had made the lantern",
        tags={"tea", "comfort"},
    ),
    "milk": Warmth(
        id="milk",
        drink="warm milk with cinnamon into two mugs",
        window_light="their porch lamp",
        closing_text="They sat close and smiled at each other whenever another glow drifted past outside",
        tags={"milk", "comfort"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Ava", "Ruby", "Wren", "Elsie", "Clara"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Finn", "Leo", "Sam", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for weather_id, weather in WEATHERS.items():
            for lantern_id, lantern in LANTERNS.items():
                if not lantern_at_risk(weather, lantern):
                    continue
                combos.append((setting_id, weather_id, lantern_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    weather: str
    lantern: str
    cover: str
    warmth: str
    child_name: str
    child_gender: str
    helper: str
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
    "revel": [(
        "What is a revel?",
        "A revel is a happy gathering with music, lights, or celebrating together. It is a time when people enjoy being together."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light inside a case or holder, so you can carry it safely. It helps people see in the dark."
    )],
    "wind": [(
        "Why can wind bother a lantern?",
        "Wind can push at a flame and make it flicker or go out. It can also bend or tear light paper."
    )],
    "rain": [(
        "Why is drizzle bad for paper?",
        "Paper soaks up water and turns soft. When that happens, it can droop, tear, or stop holding its shape."
    )],
    "umbrella": [(
        "What does an umbrella protect?",
        "An umbrella helps keep rain and drizzle off your head and what you carry under it. It does not always stop strong wind."
    )],
    "jar": [(
        "Why would a glass jar help protect a lantern?",
        "A glass jar blocks wind and keeps some wet weather off the lantern. The clear sides still let the light shine through."
    )],
    "memory": [(
        "What is a flashback in a story?",
        "A flashback is when the story remembers something that happened earlier. It helps you understand why a moment matters now."
    )],
    "comfort": [(
        "How can a grown-up comfort a sad child?",
        "A grown-up can stay close, speak gently, and help the child feel safe. Warm drinks, hugs, and kind words can help too."
    )],
}
KNOWLEDGE_ORDER = ["revel", "lantern", "wind", "rain", "umbrella", "jar", "memory", "comfort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    weather = f["weather"]
    lantern_cfg = f["lantern_cfg"]
    outcome = f["outcome"]
    if outcome == "missed":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old that includes the word "revel", a flashback, and a repeated line. A child carries a handmade lantern toward {setting.revel_name}, but {weather.label} leads to a sad ending with loving comfort at home.',
            f"Tell a gentle story where {child.attrs['name']} keeps repeating \"{lantern_cfg.maker_line}\" while trying to protect a lantern on the way to a revel, but the child misses the celebration and is comforted afterward.",
            f'Write a story with a bad ending that still feels warm: the lantern is lost before the revel, yet the family keeps the memory glowing inside the house.',
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "revel", a flashback, and a repeated line. A child carries a handmade lantern safely to {setting.revel_name}.',
        f"Tell a gentle lantern story where {child.attrs['name']} repeats \"{lantern_cfg.maker_line}\" and remembers making the lantern earlier that day.",
        f'Write a simple story about reaching a revel with a small light, using a flashback to show why the light matters.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    weather = f["weather"]
    lantern_cfg = f["lantern_cfg"]
    cover = f["cover"]
    warmth = f["warmth"]
    name = child.attrs["name"]
    hpw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name} and {hpw}, walking with a handmade {lantern_cfg.label} toward {setting.revel_name}. The lantern matters because they made it together earlier."
        ),
        (
            "What line gets repeated in the story?",
            f'The repeated line is "{lantern_cfg.maker_line}." {name} says it at the start and again during the hard part, so it feels like a little thread tying the story together.'
        ),
        (
            "What is the flashback about?",
            f"The flashback remembers the afternoon when {name} and {hpw} made the lantern together. It matters because the lantern is not just a thing to carry; it holds their shared work and love."
        ),
        (
            f"Why was the lantern in danger?",
            f"The lantern was in danger because {weather.label} could hurt a lantern made from {lantern_cfg.material}. The weather matched the lantern's weakness, so the walk to the revel became risky."
        ),
    ]
    if f["outcome"] == "kept":
        qa.append((
            f"How did {hpw} help keep the lantern safe?",
            f"{hpw.capitalize()} {cover.qa_text}. That protection fit the weather well enough, so the lantern stayed lit all the way to the revel."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily at {setting.revel_name}, with {name} among the other lights. The ending image shows that the careful words from the flashback helped carry the child forward."
        ))
    else:
        qa.append((
            f"Why did they miss the revel?",
            f"They missed the revel because {weather.label} was too strong for the way they tried to protect the lantern. Once the lantern went dark, they turned back instead of hurrying on with a broken light."
        ))
        qa.append((
            "Was the ending only sad?",
            f"No. It is a bad ending because they missed the revel and the lantern was lost, but it is still warm. At home they shared {warmth.drink}, set {warmth.window_light} by the window, and kept the memory glowing together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"revel", "lantern", "memory", "comfort"}
    weather = world.facts["weather"]
    cover = world.facts["cover"]
    if weather.hazard == "wind":
        tags.add("wind")
    if weather.hazard == "damp":
        tags.add("rain")
    if "umbrella" in cover.id:
        tags.add("umbrella")
    if "jar" in cover.id:
        tags.add("jar")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="lane",
        weather="gusts",
        lantern="leaf",
        cover="cloak_fold",
        warmth="tea",
        child_name="Mira",
        child_gender="girl",
        helper="grandmother",
        seed=101,
    ),
    StoryParams(
        setting="green",
        weather="drizzle",
        lantern="star",
        cover="umbrella",
        warmth="cocoa",
        child_name="Eli",
        child_gender="boy",
        helper="grandfather",
        seed=102,
    ),
    StoryParams(
        setting="harbor",
        weather="hard_wind",
        lantern="waxed",
        cover="glass_jar",
        warmth="milk",
        child_name="Nora",
        child_gender="girl",
        helper="mother",
        seed=103,
    ),
    StoryParams(
        setting="green",
        weather="hard_wind",
        lantern="star",
        cover="cloak_fold",
        warmth="cocoa",
        child_name="Leo",
        child_gender="boy",
        helper="grandmother",
        seed=104,
    ),
    StoryParams(
        setting="lane",
        weather="mist",
        lantern="star",
        cover="glass_jar",
        warmth="tea",
        child_name="Ruby",
        child_gender="girl",
        helper="father",
        seed=105,
    ),
]


def explain_rejection(weather: Weather, lantern: Lantern) -> str:
    return (
        f"(No story: {weather.label} does not meaningfully threaten a {lantern.label} in this world. "
        f"Pick a weather condition that matches the lantern's weakness so the walk to the revel has real tension.)"
    )


def explain_cover(cover_id: str) -> str:
    cover = COVERS[cover_id]
    better = ", ".join(sorted(c.id for c in sensible_covers()))
    return (
        f"(Refusing cover '{cover_id}': it scores too low on common sense "
        f"(sense={cover.sense} < {SENSE_MIN}). Try one of these safer choices: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    weather = WEATHERS[params.weather]
    lantern = LANTERNS[params.lantern]
    cover = COVERS[params.cover]
    return "kept" if is_saved(weather, lantern, cover) else "missed"


ASP_RULES = r"""
hazard(W, L) :- weather(W), lantern(L), weak_to(L, H), hazard_kind(W, H).
sensible(C) :- cover(C), sense(C, S), sense_min(M), S >= M.
valid(S, W, L) :- setting(S), weather(W), lantern(L), hazard(W, L).

risk(V) :- chosen_weather(W), chosen_lantern(L), severity(W, SW), fragility(L, FL), V = SW + FL.
saved :- chosen_weather(W), chosen_lantern(L), chosen_cover(C),
         hazard_kind(W, H), protects(C, H),
         risk(V), power(C, P), P >= V.
outcome(kept) :- saved.
outcome(missed) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("hazard_kind", weather_id, weather.hazard))
        lines.append(asp.fact("severity", weather_id, weather.severity))
    for lantern_id, lantern in LANTERNS.items():
        lines.append(asp.fact("lantern", lantern_id))
        lines.append(asp.fact("fragility", lantern_id, lantern.fragility))
        for hazard in sorted(lantern.weak_to):
            lines.append(asp.fact("weak_to", lantern_id, hazard))
    for cover_id, cover in COVERS.items():
        lines.append(asp.fact("cover", cover_id))
        lines.append(asp.fact("sense", cover_id, cover.sense))
        lines.append(asp.fact("power", cover_id, cover.power))
        for hazard in sorted(cover.protects):
            lines.append(asp.fact("protects", cover_id, hazard))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_lantern", params.lantern),
        asp.fact("chosen_cover", params.cover),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {c.id for c in sensible_covers()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible covers match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible covers: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child carries a memory lantern toward a revel. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--warmth", choices=WARMTHS)
    ap.add_argument("--helper", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.cover and COVERS[args.cover].sense < SENSE_MIN:
        raise StoryError(explain_cover(args.cover))

    if args.weather and args.lantern:
        weather = WEATHERS[args.weather]
        lantern = LANTERNS[args.lantern]
        if not lantern_at_risk(weather, lantern):
            raise StoryError(explain_rejection(weather, lantern))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.weather is None or combo[1] == args.weather)
        and (args.lantern is None or combo[2] == args.lantern)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, weather_id, lantern_id = rng.choice(sorted(combos))
    weather = WEATHERS[weather_id]
    cover_choices = [
        cover_id for cover_id, cover in COVERS.items()
        if cover.sense >= SENSE_MIN and weather.hazard in cover.protects
    ]
    if args.cover:
        cover_id = args.cover
        if weather.hazard not in COVERS[cover_id].protects:
            raise StoryError(
                f"(No story: {COVERS[cover_id].label} does not protect against {weather.hazard}, "
                f"so it is not a sensible choice for this weather.)"
            )
    else:
        cover_id = rng.choice(sorted(cover_choices))
    warmth_id = args.warmth or rng.choice(sorted(WARMTHS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "grandfather", "mother", "father"])

    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        lantern=lantern_id,
        cover=cover_id,
        warmth=warmth_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.lantern not in LANTERNS:
        raise StoryError(f"(Unknown lantern: {params.lantern})")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover: {params.cover})")
    if params.warmth not in WARMTHS:
        raise StoryError(f"(Unknown warmth choice: {params.warmth})")
    if params.helper not in {"grandmother", "grandfather", "mother", "father"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")

    weather = WEATHERS[params.weather]
    lantern_cfg = LANTERNS[params.lantern]
    cover = COVERS[params.cover]

    if cover.sense < SENSE_MIN:
        raise StoryError(explain_cover(params.cover))
    if not lantern_at_risk(weather, lantern_cfg):
        raise StoryError(explain_rejection(weather, lantern_cfg))
    if weather.hazard not in cover.protects:
        raise StoryError(
            f"(No story: {cover.label} does not protect against {weather.hazard}, "
            f"so the grown-up would not honestly choose it.)"
        )

    world = tell(
        setting=SETTINGS[params.setting],
        weather=weather,
        lantern_cfg=lantern_cfg,
        cover=cover,
        warmth=WARMTHS[params.warmth],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible covers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, weather, lantern) combos:\n")
        for setting_id, weather_id, lantern_id in combos:
            print(f"  {setting_id:8} {weather_id:10} {lantern_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
                f"### {p.child_name}: {p.lantern} in {p.weather} "
                f"({p.setting}, {p.cover}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
