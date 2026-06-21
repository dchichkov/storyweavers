#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py
===================================================================================

A standalone story world for a tall-tale domain about building an enormous stag
that must gain real permanence before wild weather knocks it apart.

Premise
-------
A child in an outsized frontier town builds a festival stag so huge its antlers
can tickle a cloud. The trouble is that grand things made in a hurry do not last.
A wise helper predicts that the weather will undo the bragging-size sculpture
unless it is transformed into something more lasting. The solution is not to
abandon the stag, but to change what it *becomes*: a hay stag can turn into a
living green landmark, a snow stag can turn glass-bright and firm, a mud stag
can bake into brick, and so on.

World logic
-----------
This world models:
- physical meters: stability, weathered, cracked, sealed, enduring
- emotional memes: pride, worry, relief, joy
- a reasonableness gate: only certain material/transform/weather combinations
  make sense, and only combinations with enough durability become stories
- an ASP twin that mirrors the Python gate and outcome model

Every valid story ends happily, but not all happy endings are the same:
- "lasting"  -> the transformed stag stands for years
- "grand"    -> it becomes the town's famous forever landmark

Run it
------
python storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py
python storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py --asp
python storyworlds/worlds/gpt-5.4/stag_permanence_happy_ending_transformation_tall_tale.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
PERMANENCE_MIN = 2


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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Ridge:
    id: str
    label: str
    detail: str
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
class Material:
    id: str
    label: str
    phrase: str
    texture: str
    base: int
    build_line: str
    weakness_line: str
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
class Transform:
    id: str
    label: str
    boost: int
    compatible: set[str]
    helper_title: str
    method_line: str
    result_form: str
    result_line: str
    permanence_line: str
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
    stress: int
    arrival_line: str
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
    def __init__(self, ridge: Ridge) -> None:
        self.ridge = ridge
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
        clone = World(self.ridge)
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


def _r_weather_damage(world: World) -> list[str]:
    out: list[str] = []
    stag = world.get("stag")
    town = world.get("town")
    hero = world.get("hero")
    if stag.meters["weathered"] < THRESHOLD or stag.meters["sealed"] >= THRESHOLD:
        return out
    sig = ("weather_damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stag.meters["cracked"] += 1
    stag.meters["stability"] -= 1
    hero.memes["worry"] += 1
    town.memes["worry"] += 1
    out.append("__damage__")
    return out


def _r_endure(world: World) -> list[str]:
    out: list[str] = []
    stag = world.get("stag")
    hero = world.get("hero")
    town = world.get("town")
    if stag.meters["sealed"] < THRESHOLD:
        return out
    sig = ("endure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stag.meters["enduring"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    town.memes["joy"] += 1
    out.append("__endure__")
    return out


CAUSAL_RULES = [
    Rule(name="weather_damage", tag="physical", apply=_r_weather_damage),
    Rule(name="endure", tag="physical", apply=_r_endure),
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


RIDGES = {
    "thundermesa": Ridge(
        id="thundermesa",
        label="Thunder Mesa",
        detail="The ridge was so broad that wagon wheels rolled three echoes before the sound came back.",
        tags={"hill", "wind"},
    ),
    "longwhistle": Ridge(
        id="longwhistle",
        label="Longwhistle Ridge",
        detail="Folks said a tune could start at one end of the ridge and still be whistling when supper was served.",
        tags={"hill", "song"},
    ),
    "redmile": Ridge(
        id="redmile",
        label="Redmile Bluff",
        detail="Its red dirt ran for a mile and a little extra, because tall-tale miles always stretch when nobody is measuring.",
        tags={"hill", "red_dirt"},
    ),
}

MATERIALS = {
    "hay": Material(
        id="hay",
        label="hay",
        phrase="a hay stag",
        texture="golden hay tied in wagon-thick bundles",
        base=1,
        build_line="By noon, the hay was stacked so high that sparrows mistook the antlers for a new forest.",
        weakness_line="Everybody could see the trouble too: hay is proud to stand up, but it is not famous for permanence.",
        tags={"hay", "soft"},
    ),
    "snow": Material(
        id="snow",
        label="snow",
        phrase="a snow stag",
        texture="snow packed as hard as bakery sugar",
        base=1,
        build_line="The snow stag rose white and shining, with a back smooth enough for moonlight to skate on.",
        weakness_line="Still, snow and permanence rarely shake hands unless help comes along.",
        tags={"snow", "cold"},
    ),
    "mud": Material(
        id="mud",
        label="mud",
        phrase="a mud stag",
        texture="red mud kneaded with river clay",
        base=2,
        build_line="The mud was slapped and smoothed until the stag looked as if the hill itself had stood up to stretch.",
        weakness_line="Mud can hold a shape longer than hay or snow, yet a rough day can still worry it into cracks.",
        tags={"mud", "clay"},
    ),
    "driftwood": Material(
        id="driftwood",
        label="driftwood",
        phrase="a driftwood stag",
        texture="silver driftwood pegged together with fence-nail pegs",
        base=2,
        build_line="The driftwood ribs curved so neatly that even the wind slowed down to admire them.",
        weakness_line="But old wood on an open ridge still needs help if it is going to last beyond one bragging season.",
        tags={"wood", "ridge"},
    ),
}

TRANSFORMS = {
    "rootsong": Transform(
        id="rootsong",
        label="rootsong",
        boost=2,
        compatible={"hay", "driftwood"},
        helper_title="gardener",
        method_line="The helper wound green vines through every rib and sang a rootsong so low the hill hummed back.",
        result_form="living green stag",
        result_line="Leaves broke from the antlers, the legs thickened like young trunks, and the whole creature turned into a living green stag.",
        permanence_line="Its roots gripped the ridge so firmly that children said the hill finally had hooves.",
        tags={"plants", "transformation"},
    ),
    "glassfrost": Transform(
        id="glassfrost",
        label="glassfrost",
        boost=3,
        compatible={"snow"},
        helper_title="glassblower",
        method_line="The helper breathed a silver chill over the snow and polished it with moon-bright powder until it rang like a bell.",
        result_form="clear ice-glass stag",
        result_line="The snow hardened clear as window glass, and the stag became an ice-glass marvel with stars caught in its sides.",
        permanence_line="It no longer slumped at noon, because the glaze held every curve in shining place.",
        tags={"ice", "transformation"},
    ),
    "kilnflame": Transform(
        id="kilnflame",
        label="kilnflame",
        boost=2,
        compatible={"mud"},
        helper_title="brickmaker",
        method_line="The helper banked a ring of slow coals around the stag and fed them with cedar smoke until the whole shape baked true.",
        result_form="brick-red stag",
        result_line="The mud deepened from brown to brick-red, and the stag stood there like a fired guardian from an old story.",
        permanence_line="Rain could drum on it all day and find nothing loose enough to steal.",
        tags={"brick", "transformation"},
    ),
    "pitchshine": Transform(
        id="pitchshine",
        label="pitchshine",
        boost=2,
        compatible={"driftwood", "hay"},
        helper_title="varnisher",
        method_line="The helper brushed on pine pitch so glossy that the sunset slid over it without leaving a scratch.",
        result_form="amber-bright stag",
        result_line="The loose stalks and boards drew tight together under the amber shine, and the stag became a smooth bright landmark.",
        permanence_line="From then on, weather skidded off its sides like peas off a drum.",
        tags={"wood", "amber", "transformation"},
    ),
}

WEATHERS = {
    "highwind": Weather(
        id="highwind",
        label="high wind",
        stress=2,
        arrival_line="By afternoon, a high wind came shouldering over the ridge, pushing hats sideways and making fence posts sing.",
        tags={"wind"},
    ),
    "springrain": Weather(
        id="springrain",
        label="spring rain",
        stress=2,
        arrival_line="Then spring rain rolled in thick and sudden, laying silver ropes across the sky.",
        tags={"rain"},
    ),
    "hotsun": Weather(
        id="hotsun",
        label="hot sun",
        stress=1,
        arrival_line="Toward midday, the hot sun leaned down so close it seemed to be reading the ridgeline for itself.",
        tags={"sun"},
    ),
}

GIRL_NAMES = ["Mira", "June", "Cora", "Elsie", "Mae", "Nell", "Tilda", "Rosa"]
BOY_NAMES = ["Eli", "Boone", "Cal", "Jesse", "Toby", "Hank", "Levi", "Milo"]
TRAITS = ["bold", "cheerful", "steady", "quick-handed", "hopeful", "stubborn"]


def compatible_transform(material_id: str, transform_id: str) -> bool:
    return material_id in TRANSFORMS[transform_id].compatible


def permanence_score(material_id: str, transform_id: str, weather_id: str) -> int:
    material = MATERIALS[material_id]
    transform = TRANSFORMS[transform_id]
    weather = WEATHERS[weather_id]
    return material.base + transform.boost - weather.stress


def valid_combo(material_id: str, transform_id: str, weather_id: str) -> bool:
    if not compatible_transform(material_id, transform_id):
        return False
    return permanence_score(material_id, transform_id, weather_id) >= PERMANENCE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for material_id in MATERIALS:
        for transform_id in TRANSFORMS:
            for weather_id in WEATHERS:
                if valid_combo(material_id, transform_id, weather_id):
                    out.append((material_id, transform_id, weather_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    score = permanence_score(params.material, params.transform, params.weather)
    return "grand" if score >= 3 else "lasting"


@dataclass
class StoryParams:
    ridge: str
    material: str
    transform: str
    weather: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    town_name: str
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


def predict_weather_damage(world: World) -> dict:
    sim = world.copy()
    stag = sim.get("stag")
    stag.meters["weathered"] += 1
    propagate(sim, narrate=False)
    return {
        "cracked": stag.meters["cracked"] >= THRESHOLD,
        "stability": stag.meters["stability"],
        "hero_worry": sim.get("hero").memes["worry"],
    }


def predict_after_transform(world: World, transform: Transform) -> dict:
    sim = world.copy()
    stag = sim.get("stag")
    stag.meters["sealed"] += 1
    stag.attrs["form"] = transform.result_form
    stag.meters["stability"] += transform.boost
    stag.meters["weathered"] += 1
    propagate(sim, narrate=False)
    return {
        "enduring": stag.meters["enduring"] >= THRESHOLD,
        "cracked": stag.meters["cracked"] >= THRESHOLD,
        "stability": stag.meters["stability"],
    }


def introduce(world: World, hero: Entity, town: Entity) -> None:
    world.say(
        f"In {world.facts['town_name']}, folks measured ambition by the wagonload, and {hero.id} had more of it than the rest put together."
    )
    world.say(
        f"{hero.id} was a {next((t for t in hero.traits if t), 'bold')} {hero.type} who could stack a plan so high it needed its own ladder."
    )
    world.say(world.ridge.detail)
    world.say(
        f"That year the town wanted a fair marker on {world.ridge.label}, something shaped like a stag and full of permanence, so travelers would know they had reached the right hill."
    )
    town.memes["hope"] += 1
    hero.memes["pride"] += 1


def build(world: World, hero: Entity, material: Material) -> None:
    stag = world.get("stag")
    stag.meters["stability"] = float(material.base)
    stag.attrs["form"] = material.phrase
    world.say(
        f"So {hero.id} hauled up {material.texture} and built {material.phrase} big enough to cast shade on both sides of the ridge at once."
    )
    world.say(material.build_line)
    world.say(material.weakness_line)


def weather_turn(world: World, hero: Entity, weather: Weather) -> None:
    pred = predict_weather_damage(world)
    world.facts["predicted_crack"] = pred["cracked"]
    world.facts["predicted_stability"] = pred["stability"]
    hero.memes["worry"] += 1
    world.say(weather.arrival_line)
    world.say(
        f"{hero.id} squinted up at the sky and felt a small, honest worry. Even a tall tale can tell when trouble is coming."
    )


def warning(world: World, helper: Entity, material: Material, weather: Weather) -> None:
    pred = predict_weather_damage(world)
    if pred["cracked"]:
        world.say(
            f'"That fine {material.label} work will not keep its antlers by supper in {weather.label}," said {helper.id}.'
        )
    else:
        world.say(
            f'"It may stand a while yet," said {helper.id}, "but a hilltop needs more than bragging if it wants permanence."'
        )


def offer_transform(world: World, helper: Entity, transform: Transform) -> None:
    after = predict_after_transform(world, transform)
    world.facts["predicted_enduring"] = after["enduring"]
    helper.memes["confidence"] += 1
    world.say(
        f"{helper.id}, the town's {transform.helper_title}, tipped {helper.pronoun('possessive')} hat and said there was a way to change the whole matter instead of merely patching it."
    )
    world.say(
        f'"Let me give this stag a new body," {helper.pronoun()} said. "If we transform it right, the hill may keep it for years."'
    )


def apply_transform(world: World, hero: Entity, helper: Entity, transform: Transform) -> None:
    stag = world.get("stag")
    hero.memes["hope"] += 1
    world.say(transform.method_line)
    stag.meters["sealed"] += 1
    stag.meters["stability"] += float(transform.boost)
    stag.attrs["form"] = transform.result_form
    world.say(transform.result_line)
    propagate(world, narrate=False)
    if stag.meters["enduring"] >= THRESHOLD:
        world.say(transform.permanence_line)


def weather_test(world: World, weather: Weather) -> None:
    stag = world.get("stag")
    stag.meters["weathered"] += 1
    propagate(world, narrate=False)
    if stag.meters["cracked"] >= THRESHOLD:
        world.say(
            f"The {weather.label} hit it hard, and the whole shape gave a nervous shiver."
        )
    else:
        world.say(
            f"The {weather.label} came on strong, but the transformed stag held its ground as if the ridge had finally learned to stand on four legs."
        )


def celebration(world: World, hero: Entity, helper: Entity, town: Entity, outcome: str) -> None:
    stag = world.get("stag")
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    town.memes["joy"] += 1
    world.say(
        f"Then the people of {world.facts['town_name']} climbed the ridge with pies, fiddles, and enough cheering to wake rocks from afternoon naps."
    )
    if outcome == "grand":
        world.say(
            f"They said no traveler would ever miss the way again, because that {stag.attrs['form']} could be seen from three counties and one very optimistic fourth."
        )
    else:
        world.say(
            f"They knew the hill had gained a keeper at last, one that would greet each season instead of falling apart before bedtime."
        )
    world.say(
        f"{hero.id} grinned at {helper.id}, and the two of them looked up at the stag shining over the town, proof that a brave idea can last when it learns what to become."
    )


def tell(
    ridge: Ridge,
    material: Material,
    transform: Transform,
    weather: Weather,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
    town_name: str,
) -> World:
    world = World(ridge)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, traits=[trait], role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    town = world.add(Entity(id="town", kind="thing", type="town", label=town_name))
    stag = world.add(Entity(id="stag", kind="thing", type="stag", label="the stag", attrs={"form": material.phrase}))
    hero.memes["pride"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["relief"] = 0.0
    helper.memes["confidence"] = 0.0
    town.memes["worry"] = 0.0
    town.memes["joy"] = 0.0
    town.memes["hope"] = 0.0
    stag.meters["stability"] = float(material.base)
    stag.meters["weathered"] = 0.0
    stag.meters["cracked"] = 0.0
    stag.meters["sealed"] = 0.0
    stag.meters["enduring"] = 0.0
    world.facts["town_name"] = town_name

    introduce(world, hero, town)
    build(world, hero, material)

    world.para()
    weather_turn(world, hero, weather)
    warning(world, helper, material, weather)
    offer_transform(world, helper, transform)

    world.para()
    apply_transform(world, hero, helper, transform)
    weather_test(world, weather)

    world.para()
    outcome = "grand" if stag.meters["stability"] >= 3 else "lasting"
    celebration(world, hero, helper, town, outcome)

    world.facts.update(
        hero=hero,
        helper=helper,
        town=town,
        ridge=ridge,
        material=material,
        transform=transform,
        weather=weather,
        stag=stag,
        outcome=outcome,
        transformed_form=stag.attrs["form"],
        enduring=stag.meters["enduring"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    material = f["material"]
    transform = f["transform"]
    weather = f["weather"]
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the words "stag" and "permanence".',
        f"Tell a happy tall tale where {hero.label} builds a giant {material.label} stag on a ridge, bad {weather.label} threatens it, and a transformation makes it last.",
        f"Write a playful frontier story about a fair marker that changes into a {transform.result_form} so the town can keep it for years.",
    ]


KNOWLEDGE = {
    "hay": [(
        "What is hay?",
        "Hay is dry cut grass that farmers bundle up. It is light and useful, but by itself it does not stay firm in bad weather."
    )],
    "snow": [(
        "What happens to snow in warm weather?",
        "Snow can soften and melt when it gets warm. That is why snow shapes usually need cold weather or extra help to last."
    )],
    "mud": [(
        "How can mud become strong?",
        "Mud mixed with clay can dry or bake until it gets hard. When it is treated the right way, it can hold its shape much better."
    )],
    "wood": [(
        "Why does wood need protection outside?",
        "Wind and rain can wear wood down over time. A good coating or careful building helps it last longer."
    )],
    "plants": [(
        "How can roots help a plant stay in place?",
        "Roots grip the soil and hold a plant steady. They help the plant stay put when wind or rain pushes on it."
    )],
    "brick": [(
        "What is a brick made from?",
        "A brick is made from clay or mud that is shaped and baked until it gets hard. That makes it stronger than soft wet mud."
    )],
    "ice": [(
        "What is ice?",
        "Ice is water that has frozen hard. It can look shiny and clear when light passes through it."
    )],
    "wind": [(
        "What can strong wind do to things on a hill?",
        "Strong wind can shove, shake, and loosen things on an open hill. Light or weak things can break or blow away."
    )],
    "rain": [(
        "Why can rain damage something soft?",
        "Rain soaks into soft things and can make them sag or crumble. That is why builders choose materials that can handle water."
    )],
    "sun": [(
        "Why can hot sun change a sculpture?",
        "Hot sun can dry, soften, or melt some materials depending on what they are made of. Heat is a kind of weather that changes things."
    )],
    "transformation": [(
        "What is a transformation?",
        "A transformation is when something changes into a different form. It may still be the same thing underneath, but it works in a new way."
    )],
}
KNOWLEDGE_ORDER = ["hay", "snow", "mud", "wood", "plants", "brick", "ice", "wind", "rain", "sun", "transformation"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    material = f["material"]
    transform = f["transform"]
    weather = f["weather"]
    ridge = f["ridge"]
    stag = f["stag"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who built a giant stag on {ridge.label}, and {helper.label}, who knew how to change it so it could last. Together they helped the whole town."
        ),
        (
            "Why did the town want the stag?",
            f"The town wanted a fair marker on the ridge so travelers would know they had reached the right place. They wanted something with permanence, not just a pretty shape for one afternoon."
        ),
        (
            f"What was the stag made from at first?",
            f"At first it was made from {material.label}. That made it impressive, but also left it open to trouble from the weather."
        ),
        (
            f"Why did {hero.label} start to worry?",
            f"{hero.label} saw that {weather.label} was coming toward the ridge. That mattered because the first stag body was not strong enough to promise real permanence by itself."
        ),
        (
            f"How did {helper.label} solve the problem?",
            f"{helper.label} used {transform.label} to transform the stag into a {stag.attrs['form']}. The change gave it a stronger body, so the weather could not undo it the way it would have undone the first version."
        ),
    ]
    if f["outcome"] == "grand":
        qa.append((
            "How did the story end?",
            f"It ended with a grand happy ending: the transformed stag stood so proudly over the ridge that people said travelers could spot it from counties away. The ending proves the change worked because the stag became a true landmark."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended happily with the stag still standing after the weather test. The town finally had a keeper on the hill, which shows the transformation gave the sculpture the permanence it needed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["material"].tags) | set(f["transform"].tags) | set(f["weather"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ridge="thundermesa",
        material="hay",
        transform="rootsong",
        weather="highwind",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Aunt Willow",
        helper_gender="aunt",
        trait="bold",
        town_name="Cattail Crossing",
    ),
    StoryParams(
        ridge="redmile",
        material="snow",
        transform="glassfrost",
        weather="hotsun",
        hero_name="Eli",
        hero_gender="boy",
        helper_name="Mr. Gleam",
        helper_gender="man",
        trait="steady",
        town_name="Tinbucket Flats",
    ),
    StoryParams(
        ridge="longwhistle",
        material="mud",
        transform="kilnflame",
        weather="springrain",
        hero_name="June",
        hero_gender="girl",
        helper_name="Old Brick Tom",
        helper_gender="man",
        trait="quick-handed",
        town_name="Sagebrush Ferry",
    ),
    StoryParams(
        ridge="thundermesa",
        material="driftwood",
        transform="pitchshine",
        weather="highwind",
        hero_name="Boone",
        hero_gender="boy",
        helper_name="Miss Amber",
        helper_gender="woman",
        trait="hopeful",
        town_name="Cedar Loop",
    ),
    StoryParams(
        ridge="redmile",
        material="driftwood",
        transform="rootsong",
        weather="springrain",
        hero_name="Rosa",
        hero_gender="girl",
        helper_name="Uncle Fern",
        helper_gender="uncle",
        trait="cheerful",
        town_name="Larkspur Bend",
    ),
]


def explain_rejection(material_id: str, transform_id: str, weather_id: str) -> str:
    material = MATERIALS[material_id]
    transform = TRANSFORMS[transform_id]
    weather = WEATHERS[weather_id]
    if material_id not in transform.compatible:
        return (
            f"(No story: {transform.label} does not sensibly work on a {material.label} stag. "
            f"That transformation fits only {', '.join(sorted(transform.compatible))}.)"
        )
    score = permanence_score(material_id, transform_id, weather_id)
    return (
        f"(No story: a {material.label} stag with {transform.label} would still not have enough permanence in {weather.label} "
        f"(score={score} < {PERMANENCE_MIN}). Pick a sturdier material, a stronger transformation, or gentler weather.)"
    )


ASP_RULES = r"""
compatible(M, T) :- transform(T), material(M), works_on(T, M).
score(M, T, W, S) :- base(M, B), boost(T, G), stress(W, R), S = B + G - R.
valid(M, T, W) :- compatible(M, T), score(M, T, W, S), permanence_min(P), S >= P.

outcome(M, T, W, grand) :- valid(M, T, W), score(M, T, W, S), S >= 3.
outcome(M, T, W, lasting) :- valid(M, T, W), score(M, T, W, S), S < 3.

#show valid/3.
#show outcome/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("base", material_id, material.base))
    for transform_id, transform in TRANSFORMS.items():
        lines.append(asp.fact("transform", transform_id))
        lines.append(asp.fact("boost", transform_id, transform.boost))
        for material_id in sorted(transform.compatible):
            lines.append(asp.fact("works_on", transform_id, material_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("stress", weather_id, weather.stress))
    lines.append(asp.fact("permanence_min", PERMANENCE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(material_id: str, transform_id: str, weather_id: str) -> str:
    import asp

    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "outcome")
    for m_id, t_id, w_id, out in atoms:
        if (m_id, t_id, w_id) == (material_id, transform_id, weather_id):
            return out
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant stag gains permanence through transformation."
    )
    ap.add_argument("--ridge", choices=RIDGES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (material, transform, weather) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pick_helper(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    choices = [
        ("Aunt Willow", "aunt"),
        ("Uncle Fern", "uncle"),
        ("Miss Amber", "woman"),
        ("Mr. Gleam", "man"),
        ("Old Brick Tom", "man"),
        ("Willow Reed", "woman"),
    ]
    pool = [item for item in choices if item[0] != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.transform and args.weather:
        if not valid_combo(args.material, args.transform, args.weather):
            raise StoryError(explain_rejection(args.material, args.transform, args.weather))

    combos = [
        combo for combo in valid_combos()
        if (args.material is None or combo[0] == args.material)
        and (args.transform is None or combo[1] == args.transform)
        and (args.weather is None or combo[2] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    material_id, transform_id, weather_id = rng.choice(sorted(combos))
    ridge_id = args.ridge or rng.choice(sorted(RIDGES))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, gender)
    helper_name, helper_gender = _pick_helper(rng, avoid=hero_name)
    trait = rng.choice(TRAITS)
    town_name = rng.choice([
        "Cattail Crossing",
        "Tinbucket Flats",
        "Sagebrush Ferry",
        "Cedar Loop",
        "Larkspur Bend",
        "Whistle Junction",
    ])
    return StoryParams(
        ridge=ridge_id,
        material=material_id,
        transform=transform_id,
        weather=weather_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        town_name=town_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ridge not in RIDGES:
        raise StoryError(f"(Unknown ridge: {params.ridge})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.transform not in TRANSFORMS:
        raise StoryError(f"(Unknown transform: {params.transform})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if not valid_combo(params.material, params.transform, params.weather):
        raise StoryError(explain_rejection(params.material, params.transform, params.weather))

    world = tell(
        ridge=RIDGES[params.ridge],
        material=MATERIALS[params.material],
        transform=TRANSFORMS[params.transform],
        weather=WEATHERS[params.weather],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        trait=params.trait,
        town_name=params.town_name,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params.material, params.transform, params.weather) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False)
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
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
        print(f"{len(combos)} valid (material, transform, weather) combos:\n")
        for material_id, transform_id, weather_id in combos:
            print(f"  {material_id:10} {transform_id:10} {weather_id:10} -> {asp_outcome(material_id, transform_id, weather_id)}")
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
                f"### {p.hero_name}: {p.material} -> {p.transform} in {p.weather} "
                f"at {p.ridge} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
