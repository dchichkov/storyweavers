#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py
======================================================================================

A standalone story world about two young friends on a sunny village avenue who
try to help a thirsty growing thing with water, a pitcher, and a colander.

The tiny domain is built around one practical lesson:
    *a pitcher carries water well; a colander lets water fall through.*
Some plants need a deep drink at the roots, while delicate blooms like a gentle
sprinkle. The happiest endings come when the friends listen, work together, and
use each tool for what it does best.

The fairy-tale flavor comes from a village avenue, a speaking-style rhyme from a
wise neighbor, and an ending image that proves the lesson was learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py --plant roses --plan nested
    python storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py --plan colander_only
    python storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/avenue_pitcher_colander_friendship_rhyme_lesson_learned.py --qa --json
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    leakiness: int = 0
    capacity: int = 0
    sprinkling: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Avenue:
    id: str
    label: str
    scene: str
    shimmer: str
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
class Plant:
    id: str
    label: str
    the: str
    need: str
    gratitude: str
    deep_need: int
    delicate: bool
    blossom: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Source:
    id: str
    label: str
    phrase: str
    sound: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    capacity: int
    leakiness: int
    sprinkling: bool = False
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
class Plan:
    id: str
    sense: int
    carry: str
    finish: str
    title: str
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


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("carry_tool")
    if tool.meters["filled"] < THRESHOLD or tool.leakiness <= 0:
        return out
    sig = ("leak", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lost = float(tool.leakiness)
    tool.meters["water"] = max(0.0, tool.meters["water"] - lost)
    world.get("path").meters["spilled"] += lost
    for kid_id in ("friend_a", "friend_b"):
        world.get(kid_id).memes["worry"] += 1
    out.append("__leak__")
    return out


def _r_helpful_sprinkle(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    finish = world.facts.get("finish_tool")
    if finish is None:
        return out
    if finish.sprinkling and plant.fragile and world.facts.get("delivered_water", 0) >= THRESHOLD:
        sig = ("sprinkle", plant.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        plant.meters["comforted"] += 1
        for kid_id in ("friend_a", "friend_b"):
            world.get(kid_id).memes["care"] += 1
        out.append("__sprinkle__")
    return out


CAUSAL_RULES = [
    Rule(name="leak", tag="physical", apply=_r_leak),
    Rule(name="sprinkle", tag="physical", apply=_r_helpful_sprinkle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


AVENUES = {
    "sunflower_lane": Avenue(
        id="sunflower_lane",
        label="Sunflower Lane",
        scene="a bright avenue where yellow shutters winked over tidy cottages",
        shimmer="warm light lay over the avenue like a folded golden ribbon",
        tags={"avenue"},
    ),
    "willow_avenue": Avenue(
        id="willow_avenue",
        label="Willow Avenue",
        scene="a quiet avenue where soft willow shadows trembled on the stones",
        shimmer="the avenue held a green hush, as if it were listening",
        tags={"avenue"},
    ),
    "berry_avenue": Avenue(
        id="berry_avenue",
        label="Berry Avenue",
        scene="a merry avenue where window boxes leaned out with red flowers",
        shimmer="the avenue smelled of warm bread and summer leaves",
        tags={"avenue"},
    ),
}

PLANTS = {
    "roses": Plant(
        id="roses",
        label="rose bush",
        the="the rose bush",
        need="its blossoms were drooping in the heat",
        gratitude="lifted its heads and let out a soft rosy smell",
        deep_need=1,
        delicate=True,
        blossom="petals",
        tags={"flowers", "fragile"},
    ),
    "sapling": Plant(
        id="sapling",
        label="linden sapling",
        the="the linden sapling",
        need="its small leaves hung tired as ribbons",
        gratitude="stood a little straighter, and its leaves stopped curling",
        deep_need=2,
        delicate=False,
        blossom="leaves",
        tags={"tree"},
    ),
    "violets": Plant(
        id="violets",
        label="violet box",
        the="the violet box",
        need="the tiny violet faces looked dry and sleepy",
        deep_need=1,
        delicate=True,
        gratitude="seemed to wake all at once, fresh and purple again",
        blossom="violet faces",
        tags={"flowers", "fragile"},
    ),
}

SOURCES = {
    "fountain": Source(
        id="fountain",
        label="fountain",
        phrase="the little fountain in the square",
        sound="where water sang over stone",
        tags={"water"},
    ),
    "well": Source(
        id="well",
        label="well",
        phrase="the old well behind the bakery",
        sound="where the bucket rope creaked softly",
        tags={"water"},
    ),
    "pump": Source(
        id="pump",
        label="pump",
        phrase="the green hand pump by the avenue gate",
        sound="where clear water knocked into the trough",
        tags={"water"},
    ),
}

TOOLS = {
    "pitcher": ToolCfg(
        id="pitcher",
        label="pitcher",
        phrase="a blue clay pitcher",
        capacity=3,
        leakiness=0,
        sprinkling=False,
        tags={"pitcher"},
    ),
    "colander": ToolCfg(
        id="colander",
        label="colander",
        phrase="a shiny tin colander",
        capacity=3,
        leakiness=2,
        sprinkling=True,
        tags={"colander"},
    ),
}

PLANS = {
    "pitcher_only": Plan(
        id="pitcher_only",
        sense=3,
        carry="pitcher",
        finish="pitcher",
        title="carry and pour with the pitcher",
        tags={"pitcher"},
    ),
    "nested": Plan(
        id="nested",
        sense=3,
        carry="pitcher",
        finish="colander",
        title="carry with the pitcher and sprinkle through the colander",
        tags={"pitcher", "colander"},
    ),
    "colander_only": Plan(
        id="colander_only",
        sense=1,
        carry="colander",
        finish="colander",
        title="carry everything in the colander",
        tags={"colander"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nella", "Ivy", "Pippa", "Rosa", "Wren"]
BOY_NAMES = ["Rowan", "Milo", "Theo", "Finn", "Jory", "Nico", "Bram", "Leo"]
TRAITS = ["kind", "patient", "cheerful", "careful", "brisk", "thoughtful"]


def plan_valid_for_plant(plan: Plan, plant: Plant) -> bool:
    if plan.sense < SENSE_MIN:
        return False
    carry = TOOLS[plan.carry]
    if carry.capacity - carry.leakiness < plant.deep_need:
        return False
    if plan.finish == "colander" and not plant.delicate:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for avenue in AVENUES:
        for source in SOURCES:
            for plant_id, plant in PLANTS.items():
                for plan_id, plan in PLANS.items():
                    if plan_valid_for_plant(plan, plant):
                        combos.append((avenue, source, plant_id, plan_id))
    return combos


def explain_plan_rejection(plan: Plan, plant: Plant) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(Refusing plan '{plan.id}': carrying water in a colander is poor common sense. "
            f"A colander has holes, so the water slips away before it reaches {plant.the}. "
            f"Try --plan pitcher_only or --plan nested.)"
        )
    carry = TOOLS[plan.carry]
    if carry.capacity - carry.leakiness < plant.deep_need:
        return (
            f"(No story: {plant.the} needs a deeper drink than a {carry.label} can deliver in this plan. "
            f"The water would not reach the roots in time.)"
        )
    if plan.finish == "colander" and not plant.delicate:
        return (
            f"(No story: {plant.the} needs a deep drink at the roots, not a light sprinkle. "
            f"The colander ending would waste the chance to help it properly.)"
        )
    return "(No story: this plan does not fit the plant's need.)"


def best_plan_for(plant: Plant) -> str:
    candidates = [pid for pid, plan in PLANS.items() if plan_valid_for_plant(plan, plant)]
    return sorted(candidates)[0]


def outcome_of(params: "StoryParams") -> str:
    plant = PLANTS[params.plant]
    plan = PLANS[params.plan]
    if not plan_valid_for_plant(plan, plant):
        return "wilted"
    return "sprinkled" if plan.finish == "colander" and plant.delicate else "watered"


@dataclass
class StoryParams:
    avenue: str
    source: str
    plant: str
    plan: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    guardian: str
    trait_a: str
    trait_b: str
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


def make_tool_entity(eid: str, cfg: ToolCfg) -> Entity:
    return Entity(
        id=eid,
        type="tool",
        label=cfg.label,
        attrs={"cfg_id": cfg.id},
        leakiness=cfg.leakiness,
        capacity=cfg.capacity,
        sprinkling=cfg.sprinkling,
    )


def predict_plan(plant: Plant, plan: Plan) -> dict:
    carry = TOOLS[plan.carry]
    delivered = max(0, carry.capacity - carry.leakiness)
    return {
        "delivered": delivered,
        "enough": delivered >= plant.deep_need,
        "gentle": plan.finish == "colander" and plant.delicate,
    }


def opening(world: World, avenue: Avenue, a: Entity, b: Entity, plant: Plant) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"Once, in a little village on {avenue.label}, there lived two friends, "
        f"{a.id} and {b.id}. {avenue.scene}, and {avenue.shimmer}."
    )
    world.say(
        f"Each morning they skipped together past {plant.the}, and on this morning "
        f"they stopped at once, for {plant.need}."
    )


def pity(world: World, a: Entity, b: Entity, plant: Plant) -> None:
    plant_ent = world.get("plant")
    plant_ent.meters["thirst"] = float(plant.deep_need)
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f'"Oh dear," said {a.id}, touching one small {plant.blossom[:-1] if plant.blossom.endswith("s") else plant.blossom} with a careful finger. '
        f'"{plant.The} looks thirsty."'
    )
    world.say(
        f'{b.id} nodded. "Then we must help it together."'
    )


def choose_badly(world: World, chooser: Entity, other: Entity, source: Source) -> None:
    chooser.memes["pride"] += 1
    other.memes["worry"] += 1
    world.say(
        f"By the garden gate sat a blue clay pitcher, and beside it shone a silver-bright colander. "
        f'"The colander sparkles like a crown," said {chooser.id}. "Let us take that to {source.phrase}."'
    )
    world.say(
        f'{other.id} hesitated, but friendship made {other.pronoun("object")} follow.'
    )


def choose_well(world: World, chooser: Entity, other: Entity, source: Source, plan: Plan) -> None:
    chooser.memes["good_sense"] += 1
    other.memes["trust"] += 1
    if plan.id == "nested":
        world.say(
            f"By the garden gate sat a blue clay pitcher and a silver-bright colander. "
            f'"Let us carry the water in the pitcher," said {chooser.id}, '
            f'"and use the colander only at the end, if the blossoms need a gentle rain."'
        )
    else:
        world.say(
            f"By the garden gate sat a blue clay pitcher and a silver-bright colander. "
            f'"The pitcher keeps what it carries," said {chooser.id}. '
            f'"Let us bring a true drink from {source.phrase}."'
        )
    world.say(
        f'{other.id} smiled and took the handle with {chooser.pronoun("object")}.'
    )


def fill(world: World, a: Entity, b: Entity, source: Source, carry_tool: Entity) -> None:
    carry_tool.meters["filled"] = 1.0
    carry_tool.meters["water"] = float(carry_tool.capacity)
    world.say(
        f"So off they went along the avenue to {source.phrase}, {source.sound}. "
        f"Together they filled the {carry_tool.label} to the brim."
    )


def carry_and_leak(world: World, carry_tool: Entity, plant: Plant) -> None:
    propagate(world, narrate=False)
    lost = int(world.get("path").meters["spilled"])
    if lost > 0:
        world.say(
            f"But as they hurried back, silver drops slipped through the holes of the colander "
            f"and darkened the dust of the avenue. By the time they reached {plant.the}, "
            f"far too little water remained."
        )


def meet_guardian(world: World, guardian: Entity, a: Entity, b: Entity, plant: Plant, plan: Plan) -> None:
    pred = predict_plan(plant, plan)
    world.facts["predicted_delivered"] = pred["delivered"]
    world.facts["predicted_enough"] = pred["enough"]
    world.say(
        f"At the bend of the avenue they met {guardian.label}, who carried a basket of mint. "
        f"{guardian.pronoun().capitalize()} listened to their tale and looked from the thirsty plant to the wet stones."
    )
    rhyme = (
        '"Pitcher for keeping, colander for rain; '
        'choose each thing well, and green will smile again."'
    )
    world.facts["rhyme"] = rhyme.strip('"')
    world.say(f"Then {guardian.pronoun()} sang a little rhyme: {rhyme}")
    if pred["enough"]:
        world.say(
            f'"You have brought enough," {guardian.pronoun()} said, '
            f'"but remember what each tool is made to do."'
        )
    else:
        world.say(
            f'"A kind heart is not always enough by itself," {guardian.pronoun()} said gently. '
            f'"You must match the tool to the need."'
        )
    a.memes["reflection"] += 1
    b.memes["reflection"] += 1


def retry_with_lesson(world: World, a: Entity, b: Entity, source: Source, plant: Plant, plan: Plan) -> None:
    carry_cfg = TOOLS["pitcher"]
    finish_cfg = TOOLS[plan.finish]
    carry_tool = make_tool_entity("carry_tool_retry", carry_cfg)
    finish_tool = make_tool_entity("finish_tool_retry", finish_cfg)
    world.entities["carry_tool"] = carry_tool
    world.facts["finish_tool"] = finish_tool
    carry_tool.meters["filled"] = 1.0
    carry_tool.meters["water"] = float(carry_tool.capacity)
    delivered = float(carry_tool.capacity)
    world.facts["delivered_water"] = delivered
    world.say(
        f"So the two friends ran back to {source.phrase}. This time they filled the pitcher, "
        f"held it steady between them, and brought every shining drop home."
    )
    if plan.finish == "colander":
        world.say(
            f"At {plant.the}, {a.id} poured the water softly through the colander, "
            f"and it fell in a fine cool rain over the roots and petals."
        )
    else:
        world.say(
            f"At {plant.the}, {a.id} and {b.id} tipped the pitcher together and gave the roots a long, deep drink."
        )
    propagate(world, narrate=False)
    plant_ent = world.get("plant")
    if delivered >= plant.deep_need:
        plant_ent.meters["thirst"] = 0.0
        plant_ent.meters["watered"] += 1
        plant_ent.meters["revived"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["lesson"] += 1
        b.memes["lesson"] += 1


def direct_success(world: World, a: Entity, b: Entity, plant: Plant, plan: Plan) -> None:
    carry_tool = world.get("carry_tool")
    finish_tool = world.facts["finish_tool"]
    delivered = float(carry_tool.meters["water"])
    world.facts["delivered_water"] = delivered
    if plan.finish == "colander":
        world.say(
            f"When they came to {plant.the}, {b.id} held the colander low while {a.id} poured from the pitcher, "
            f"making a gentle shower that did not bruise the blossoms."
        )
    else:
        world.say(
            f"When they came to {plant.the}, they knelt side by side and poured from the pitcher right at the roots."
        )
    propagate(world, narrate=False)
    plant_ent = world.get("plant")
    if delivered >= plant.deep_need:
        plant_ent.meters["thirst"] = 0.0
        plant_ent.meters["watered"] += 1
        plant_ent.meters["revived"] += 1
        a.memes["lesson"] += 1
        b.memes["lesson"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1


def ending(world: World, a: Entity, b: Entity, plant: Plant, avenue: Avenue) -> None:
    plant_ent = world.get("plant")
    if plant_ent.meters["revived"] >= THRESHOLD:
        world.say(
            f"Soon {plant.the} {plant.gratitude}. {a.id} laughed, and {b.id} clapped softly, "
            f"for the avenue no longer looked thirsty and tired."
        )
        world.say(
            f'From that day on, the friends remembered the rhyme whenever work had to be done: '
            f'"{world.facts["rhyme"]}"'
        )
        world.say(
            f"And so on {avenue.label}, friendship grew wiser as well as dearer, and every useful thing was loved for its true use."
        )
    else:
        world.say(
            f"But {plant.the} still drooped in the sun, and the avenue looked sadder for it. "
            f"{a.id} and {b.id} stood very still, understanding at last that wishing to help is not the same as helping well."
        )
        world.say(
            f"Before the shadows grew long, they promised to return with the right tool and kinder sense."
        )


def tell(
    avenue: Avenue,
    source: Source,
    plant: Plant,
    plan: Plan,
    friend_a: str = "Lina",
    friend_a_gender: str = "girl",
    friend_b: str = "Milo",
    friend_b_gender: str = "boy",
    guardian_type: str = "mother",
    trait_a: str = "kind",
    trait_b: str = "careful",
) -> World:
    world = World()
    a = world.add(Entity(
        id="friend_a",
        kind="character",
        type=friend_a_gender,
        label=friend_a,
        role="friend_a",
        traits=[trait_a],
        attrs={"display": friend_a},
    ))
    b = world.add(Entity(
        id="friend_b",
        kind="character",
        type=friend_b_gender,
        label=friend_b,
        role="friend_b",
        traits=[trait_b],
        attrs={"display": friend_b},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label=f"the old {guardian_type}",
        role="guardian",
    ))
    plant_ent = world.add(Entity(
        id="plant",
        type="plant",
        label=plant.label,
        fragile=plant.delicate,
        attrs={"cfg_id": plant.id},
    ))
    world.add(Entity(id="path", type="path", label="avenue stones"))
    carry_tool = world.add(make_tool_entity("carry_tool", TOOLS[plan.carry]))
    finish_tool = make_tool_entity("finish_tool", TOOLS[plan.finish])
    world.facts["finish_tool"] = finish_tool
    world.facts["friend_a_name"] = friend_a
    world.facts["friend_b_name"] = friend_b
    world.facts["guardian_type"] = guardian_type
    world.facts["avenue"] = avenue
    world.facts["source"] = source
    world.facts["plant_cfg"] = plant
    world.facts["plan"] = plan

    opening(world, avenue, a, b, plant)
    pity(world, a, b, plant)

    world.para()
    if plan.id == "colander_only":
        choose_badly(world, a, b, source)
    else:
        choose_well(world, a, b, source, plan)
    fill(world, a, b, source, carry_tool)

    if plan.id == "colander_only":
        carry_and_leak(world, carry_tool, plant)
        world.para()
        meet_guardian(world, guardian, a, b, plant, plan)
        corrected_plan_id = best_plan_for(plant)
        corrected_plan = PLANS[corrected_plan_id]
        world.facts["corrected_plan"] = corrected_plan
        world.para()
        retry_with_lesson(world, a, b, source, plant, corrected_plan)
    else:
        world.para()
        meet_guardian(world, guardian, a, b, plant, plan)
        world.para()
        direct_success(world, a, b, plant, plan)

    world.para()
    ending(world, a, b, plant, avenue)

    outcome = "revived" if plant_ent.meters["revived"] >= THRESHOLD else "wilted"
    world.facts.update(
        friend_a=a,
        friend_b=b,
        guardian=guardian,
        carry_tool=carry_tool,
        plant=plant_ent,
        source_cfg=source,
        avenue_cfg=avenue,
        outcome=outcome,
        corrected_plan=world.facts.get("corrected_plan"),
        delivered_water=world.facts.get("delivered_water", 0.0),
    )
    return world


KNOWLEDGE = {
    "pitcher": [
        (
            "What is a pitcher?",
            "A pitcher is a container with a handle and a spout for holding and pouring water. It keeps the water inside until you are ready to use it."
        )
    ],
    "colander": [
        (
            "What is a colander?",
            "A colander is a bowl with many holes. It is good for letting water run through, but not for carrying water far."
        )
    ],
    "avenue": [
        (
            "What is an avenue?",
            "An avenue is a broad street or road, often with houses or trees along it. People walk or ride along an avenue to go from place to place."
        )
    ],
    "flowers": [
        (
            "Why do flowers need water?",
            "Flowers need water so their roots and stems can stay healthy. Without enough water, they droop and dry out."
        )
    ],
    "tree": [
        (
            "Why does a young tree need a deep drink?",
            "A young tree has roots that need water to soak into the soil. A quick sprinkle on top may not be enough to help it."
        )
    ],
    "fragile": [
        (
            "Why can gentle watering help delicate blossoms?",
            "Delicate blossoms can bend or bruise if water falls too hard on them. A soft sprinkle can be kinder while still reaching the soil."
        )
    ],
    "friendship": [
        (
            "How can friendship help solve a problem?",
            "Friends can share work, listen to each other, and fix mistakes together. A good friend helps you choose better, not just faster."
        )
    ],
    "rhyme": [
        (
            "Why do people remember lessons in a rhyme?",
            "A rhyme is easier to remember because the words fit together in a pattern. That makes the lesson come back to mind later."
        )
    ],
}
KNOWLEDGE_ORDER = ["avenue", "pitcher", "colander", "flowers", "tree", "fragile", "friendship", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    plant = f["plant_cfg"]
    avenue = f["avenue_cfg"]
    plan = f["plan"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that uses the words "avenue," "pitcher," and "colander" and ends with a lesson learned.',
        f"Tell a gentle fairy-tale about two friends, {a.label} and {b.label}, on {avenue.label} trying to help {plant.the} and learning that each tool has its proper use.",
        f"Write a child-facing story with friendship and a memorable rhyme where the plan is {plan.title} and the ending shows what changed."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    plant_cfg = f["plant_cfg"]
    source = f["source_cfg"]
    plan = f["plan"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.label} and {b.label}, who wanted to help {plant_cfg.the}. They worked together along the avenue and learned from what happened."
        ),
        (
            f"Why did {a.label} and {b.label} go to {source.phrase}?",
            f"They went there to fetch water for {plant_cfg.the}, because it looked dry and tired. The whole problem began when they saw that the plant needed help."
        ),
        (
            "What rhyme did the old neighbor sing?",
            f'The rhyme was: "{f["rhyme"]}" It taught them to choose a tool for what it truly does.'
        ),
    ]
    if plan.id == "colander_only":
        qa.append(
            (
                "Why did carrying water in the colander fail at first?",
                f"It failed because the colander had holes, so the water dripped away along the avenue before the friends reached {plant_cfg.the}. Their hearts were kind, but the wrong tool could not do the job."
            )
        )
        corrected = f.get("corrected_plan")
        if corrected is not None:
            if corrected.finish == "colander" and plant_cfg.delicate:
                fix_text = "They carried the water in the pitcher and used the colander only for a gentle sprinkle at the end."
            else:
                fix_text = "They carried and poured the water with the pitcher so the roots got a full drink."
            qa.append(
                (
                    "How did the friends fix the problem?",
                    f"{fix_text} That worked because the pitcher kept the water in until they were ready to use it."
                )
            )
    else:
        if outcome == "revived":
            if plan.finish == "colander":
                why = f"They used the pitcher to carry the water safely, then let it fall through the colander in a soft shower over {plant_cfg.the}. That gave the flowers water without treating the blossoms roughly."
            else:
                why = f"They carried the water in the pitcher and poured it right at the roots of {plant_cfg.the}. That gave it the deep drink it needed."
            qa.append(
                (
                    "How did their plan help the plant?",
                    why
                )
            )
    qa.append(
        (
            "What lesson did the friends learn?",
            "They learned that being helpful also means being thoughtful. A good heart works best when it chooses the right tool for the need."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    plant_cfg = f["plant_cfg"]
    tags = {"avenue", "friendship", "rhyme", "pitcher"}
    plan = f["plan"]
    tags.add(plan.carry)
    tags.add(plan.finish)
    if plant_cfg.delicate:
        tags.add("fragile")
        tags.add("flowers")
    else:
        tags.add("tree")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.capacity:
            bits.append(f"capacity={e.capacity}")
        if e.leakiness:
            bits.append(f"leakiness={e.leakiness}")
        if e.sprinkling:
            bits.append("sprinkling=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_plan(P) :- plan(P), sense(P,S), sense_min(M), S >= M.

deliverable(P,Pl) :- carry(P,T), capacity(T,C), leakiness(T,L), need(Pl,N), C-L >= N.
gentle_fit(P,Pl)  :- finish(P,colander), delicate(Pl).
gentle_fit(P,Pl)  :- finish(P,pitcher).
valid_plan_for(P,Pl) :- sensible_plan(P), deliverable(P,Pl), finish(P,pitcher).
valid_plan_for(P,Pl) :- sensible_plan(P), deliverable(P,Pl), finish(P,colander), delicate(Pl).

valid(A,S,Pl,P) :- avenue(A), source(S), plant(Pl), plan(P), valid_plan_for(P,Pl).

outcome(Pl,P,watered) :- valid_plan_for(P,Pl), finish(P,pitcher).
outcome(Pl,P,sprinkled) :- valid_plan_for(P,Pl), finish(P,colander), delicate(Pl).
outcome(Pl,P,wilted) :- plan(P), plant(Pl), not valid_plan_for(P,Pl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in AVENUES:
        lines.append(asp.fact("avenue", aid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    for pid, plant in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("need", pid, plant.deep_need))
        if plant.delicate:
            lines.append(asp.fact("delicate", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("capacity", tid, tool.capacity))
        lines.append(asp.fact("leakiness", tid, tool.leakiness))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        lines.append(asp.fact("carry", pid, plan.carry))
        lines.append(asp.fact("finish", pid, plan.finish))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(plant: str, plan: str) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_plant", plant),
        asp.fact("chosen_plan", plan),
        "picked_outcome(O) :- chosen_plant(Pl), chosen_plan(P), outcome(Pl,P,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        avenue="sunflower_lane",
        source="fountain",
        plant="violets",
        plan="nested",
        friend_a="Lina",
        friend_a_gender="girl",
        friend_b="Milo",
        friend_b_gender="boy",
        guardian="mother",
        trait_a="kind",
        trait_b="careful",
    ),
    StoryParams(
        avenue="willow_avenue",
        source="well",
        plant="sapling",
        plan="pitcher_only",
        friend_a="Theo",
        friend_a_gender="boy",
        friend_b="Rosa",
        friend_b_gender="girl",
        guardian="father",
        trait_a="thoughtful",
        trait_b="patient",
    ),
    StoryParams(
        avenue="berry_avenue",
        source="pump",
        plant="roses",
        plan="colander_only",
        friend_a="Mira",
        friend_a_gender="girl",
        friend_b="Finn",
        friend_b_gender="boy",
        guardian="mother",
        trait_a="cheerful",
        trait_b="kind",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: two friends on an avenue learn how to use a pitcher and a colander wisely."
    )
    ap.add_argument("--avenue", choices=AVENUES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.plan:
        plant = PLANTS[args.plant]
        plan = PLANS[args.plan]
        if not plan_valid_for_plant(plan, plant):
            raise StoryError(explain_plan_rejection(plan, plant))

    combos = [
        c for c in valid_combos()
        if (args.avenue is None or c[0] == args.avenue)
        and (args.source is None or c[1] == args.source)
        and (args.plant is None or c[2] == args.plant)
        and (args.plan is None or c[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    avenue, source, plant, plan = rng.choice(sorted(combos))
    friend_a, friend_a_gender = _pick_child(rng)
    friend_b, friend_b_gender = _pick_child(rng, avoid=friend_a)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice([t for t in TRAITS if t != trait_a] or TRAITS)
    return StoryParams(
        avenue=avenue,
        source=source,
        plant=plant,
        plan=plan,
        friend_a=friend_a,
        friend_a_gender=friend_a_gender,
        friend_b=friend_b,
        friend_b_gender=friend_b_gender,
        guardian=guardian,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def _require_key(table: dict, key: str, field_name: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    avenue = _require_key(AVENUES, params.avenue, "avenue")
    source = _require_key(SOURCES, params.source, "source")
    plant = _require_key(PLANTS, params.plant, "plant")
    plan = _require_key(PLANS, params.plan, "plan")
    if not plan_valid_for_plant(plan, plant):
        raise StoryError(explain_plan_rejection(plan, plant))
    world = tell(
        avenue=avenue,
        source=source,
        plant=plant,
        plan=plan,
        friend_a=params.friend_a,
        friend_a_gender=params.friend_a_gender,
        friend_b=params.friend_b,
        friend_b_gender=params.friend_b_gender,
        guardian_type=params.guardian,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
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
        print(f"OK: valid_combos() matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[tuple[str, str]] = []
    for plant in PLANTS:
        for plan in PLANS:
            cases.append((plant, plan))
    bad = 0
    for plant, plan in cases:
        py = "wilted"
        if plan_valid_for_plant(PLANS[plan], PLANTS[plant]):
            py = "sprinkled" if PLANS[plan].finish == "colander" and PLANTS[plant].delicate else "watered"
        cl = asp_outcome(plant, plan)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} plant/plan cases.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (avenue, source, plant, plan) combos:\n")
        for avenue, source, plant, plan in combos:
            print(f"  {avenue:15} {source:9} {plant:8} {plan}")
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
            header = f"### {p.friend_a} & {p.friend_b}: {p.plant} on {p.avenue} ({p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
