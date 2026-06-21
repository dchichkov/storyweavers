#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py
===============================================================

A standalone story world for a tall-tale-flavored sharing story built around one
huge pan of food. The world models a child in an exaggerated frontier setting
who thinks about keeping a giant treat, discovers that a feast this big is too
heavy and hot to manage alone, and learns that sharing brings help and joy.

The core reasonableness constraint is simple:

    a giant pan + a dish + a serving aid + a place with a crowd

must fit together honestly. Soup needs bowls, biscuits need baskets, and a town
square can host a crowd better than a windy hill. The world rejects mismatches.
Within valid combinations, the hero's trait determines the turn:

    generous hero -> shares early
    boastful hero -> tries to manage alone first, the pan wobbles, then shares

The story is driven by simulated state: heat, weight, wobble, servings, hunger,
and emotional shifts such as pride, worry, relief, and belonging.

Run it
------
    python storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py --dish biscuits
    python storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py --aid bowls
    python storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py --verify
    python storyworlds/worlds/gpt-5.4/pan_moral_value_sharing_tall_tale.py --all --qa
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
LOAD_LIMIT = 5
HELP_STRENGTH_MIN = 2

GENEROUS_TRAITS = {"generous", "kind", "neighborly"}
BOASTFUL_TRAITS = {"boastful", "stubborn", "showy"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Setting:
    id: str
    place: str
    image: str
    crowd_word: str
    supports: set[str] = field(default_factory=set)
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
class Dish:
    id: str
    label: str
    phrase: str
    scoop_word: str
    serving_kind: str
    weight: int
    heat: int
    brag: str
    shared_end: str
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
    serves: set[str] = field(default_factory=set)
    carry_bonus: int = 0
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
class HelperKind:
    id: str
    label: str
    phrase: str
    count_word: str
    strength: int
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pan = world.get("pan")
    if hero.meters["load"] <= LOAD_LIMIT:
        return out
    if pan.meters["wobble"] >= THRESHOLD:
        return out
    sig = ("wobble", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pan.meters["wobble"] += 1
    hero.memes["worry"] += 1
    world.get("crowd").memes["gasp"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    if pan.meters["wobble"] < THRESHOLD:
        return out
    if pan.meters["carried"] < THRESHOLD:
        return out
    if pan.meters["saved"] >= THRESHOLD:
        return out
    sig = ("spill_risk", "pan")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pan.meters["spill_risk"] += 1
    world.get("crowd").meters["hungry"] += 1
    out.append("__spill__")
    return out


def _r_share_feeds(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    crowd = world.get("crowd")
    if pan.meters["portioned"] < THRESHOLD:
        return out
    sig = ("fed", "crowd")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crowd.meters["hungry"] = 0.0
    crowd.memes["joy"] += 1
    crowd.memes["gratitude"] += 1
    hero = world.get("hero")
    hero.memes["belonging"] += 1
    out.append("__fed__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill_risk", tag="physical", apply=_r_spill),
    Rule(name="share_feeds", tag="social", apply=_r_share_feeds),
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


def place_can_host(setting: Setting, dish: Dish) -> bool:
    return dish.serving_kind in setting.supports


def aid_fits(aid: Aid, dish: Dish) -> bool:
    return dish.serving_kind in aid.serves


def can_share_here(setting: Setting, dish: Dish, aid: Aid, helpers: HelperKind) -> bool:
    return (
        place_can_host(setting, dish)
        and aid_fits(aid, dish)
        and helpers.strength >= HELP_STRENGTH_MIN
    )


def effective_load(dish: Dish, aid: Aid, helpers: HelperKind) -> int:
    return max(0, dish.weight - aid.carry_bonus - helpers.strength)


def outcome_of(params: "StoryParams") -> str:
    if params.trait in GENEROUS_TRAITS:
        return "shared_early"
    return "shared_after_wobble"


def predict_alone(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    pan = sim.get("pan")
    pan.meters["carried"] += 1
    hero.meters["load"] += pan.meters["weight"]
    propagate(sim, narrate=False)
    return {
        "wobble": pan.meters["wobble"] >= THRESHOLD,
        "spill_risk": pan.meters["spill_risk"] >= THRESHOLD,
        "load": hero.meters["load"],
    }


def introduce(world: World, hero: Entity, setting: Setting, dish: Dish) -> None:
    world.say(
        f"In {setting.place}, where {setting.image}, {hero.id} was known as the child who could smell "
        f"{dish.label} before a wood stove even thought about warming up."
    )
    world.say(
        f"Folks said {hero.pronoun()} could hear a pan hum from half a county away, and in a tall-tale place like that, "
        f"nobody argued much with folks."
    )


def giant_cook(world: World, hero: Entity, dish: Dish) -> None:
    hero.memes["pride"] += 1
    pan = world.get("pan")
    world.say(
        f"That morning, {hero.id} cooked {dish.phrase} in a pan so wide it looked fit to shine the moon. "
        f"The pan held enough {dish.label} to feed a parade and still leave crumbs for the crows."
    )
    if pan.meters["heat"] >= 3:
        world.say(
            f"It came off the fire puffing and sizzling, and the handles were hot enough to make a potholder think twice."
        )


def spot_crowd(world: World, hero: Entity, setting: Setting) -> None:
    crowd = world.get("crowd")
    crowd.meters["hungry"] = 1.0
    world.say(
        f"Just then, {hero.id} saw {setting.crowd_word} gathering nearby. Their bellies were rumbling like wagon wheels on a bridge."
    )
    world.say(
        f"{hero.id} looked at the mountain inside the pan and knew there was far more than one child could ever finish."
    )


def boast(world: World, hero: Entity, dish: Dish) -> None:
    hero.memes["pride"] += 1
    hero.memes["stingy"] += 1
    world.say(
        f'"This {dish.brag}," {hero.id} said, hugging the pan close. For one proud minute, keeping it all sounded grander than sunrise.'
    )


def generous_thought(world: World, hero: Entity, dish: Dish) -> None:
    hero.memes["generosity"] += 1
    world.say(
        f"{hero.id} sniffed the fine smell curling up from the pan and thought how lonely a feast would be if nobody else got a taste."
    )


def warn_need_help(world: World, hero: Entity, helper: HelperKind, aid: Aid) -> None:
    pred = predict_alone(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill_risk"]
    if pred["spill_risk"]:
        world.say(
            f"Even before taking a full step, {hero.id} could tell the load would wobble. A pan that big needed helping hands and {aid.phrase}, or supper might slosh into the dust."
        )
    else:
        world.say(
            f"{hero.id} judged the load with a squint and knew the smart thing was plain: {helper.count_word} and {aid.label} would make the feast safer to share."
        )


def try_alone(world: World, hero: Entity) -> None:
    pan = world.get("pan")
    pan.meters["carried"] += 1
    hero.meters["load"] += pan.meters["weight"]
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} heaved up the pan alone and took one mighty step."
    )
    if pan.meters["wobble"] >= THRESHOLD:
        world.say(
            f"The pan tipped left, then right, and the whole shiny supper swayed like a pond in a windstorm."
        )


def gasp(world: World, hero: Entity) -> None:
    crowd = world.get("crowd")
    if crowd.memes["gasp"] >= THRESHOLD:
        world.say(
            f"The waiting crowd let out one long gasp, and {hero.id}'s heart sank faster than a biscuit in gravy."
        )


def ask_to_share(world: World, hero: Entity, helper: HelperKind, aid: Aid) -> None:
    hero.memes["generosity"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["stingy"] = 0.0
    world.say(
        f'"Friends," {hero.id} called, "come help me carry this pan and pass the {aid.label}. A feast this big belongs to more than one pair of hands."'
    )
    helpers = world.get("helpers")
    helpers.memes["eagerness"] += 1
    world.say(
        f"{helper.phrase.capitalize()} came hurrying over at once, grinning as if they had been hoping to hear exactly that."
    )


def save_and_portion(world: World, dish: Dish, aid: Aid, helpers: HelperKind) -> None:
    hero = world.get("hero")
    pan = world.get("pan")
    crowd = world.get("crowd")
    hero.meters["load"] = float(effective_load(dish, aid, helpers))
    pan.meters["saved"] += 1
    pan.meters["portioned"] += 1
    pan.meters["servings"] = float(max(6, dish.weight + helpers.strength + aid.carry_bonus + 3))
    propagate(world, narrate=False)
    if pan.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Three quick pairs of hands steadied the wobbling pan before even one crumb could escape."
        )
    world.say(
        f"Soon the {aid.label} were moving, the pan was steady, and warm {dish.label} began landing in happy hands all around."
    )
    if crowd.meters["hungry"] <= 0:
        world.say(
            f"The grumbles in the crowd faded away, replaced by chewing, laughing, and the kind of thank-yous that make a chilly day feel warmer."
        )


def lesson(world: World, hero: Entity, dish: Dish) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} learned something bigger than the pan that day: food tastes finer when it is shared."
    )
    world.say(
        f"When {hero.pronoun()} watched other faces brighten over {dish.label}, the feast somehow seemed to grow instead of shrink."
    )


def ending_image(world: World, setting: Setting, dish: Dish) -> None:
    world.say(
        f"By sunset, {setting.place} smelled of warm {dish.label}, and the great pan sat nearly empty and shining, as proud as a silver moon after doing a kind deed."
    )
    world.say(
        dish.shared_end
    )
def tell(
    dish: Dish,
    aid: Aid,
    helpers_cfg: Helpers,
    hero_name: str,
    hero_gender: str,
    parent_type: ParentType,
    trait: Trait,
    setting=None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait], attrs={"name": hero_name}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    crowd = world.add(Entity(id="crowd", kind="character", type="folk", label=setting.crowd_word, role="crowd"))
    helpers = world.add(Entity(id="helpers", kind="character", type="folk", label=helpers_cfg.label, role="helpers"))
    pan = world.add(Entity(id="pan", kind="thing", type="pan", label="pan", role="pan"))
    aid_ent = world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label, role="aid"))

    hero.meters["load"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["stingy"] = 0.0
    hero.memes["generosity"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["belonging"] = 0.0
    crowd.meters["hungry"] = 0.0
    crowd.memes["joy"] = 0.0
    crowd.memes["gratitude"] = 0.0
    crowd.memes["gasp"] = 0.0
    helpers.memes["eagerness"] = 0.0
    pan.meters["weight"] = float(dish.weight)
    pan.meters["heat"] = float(dish.heat)
    pan.meters["wobble"] = 0.0
    pan.meters["spill_risk"] = 0.0
    pan.meters["carried"] = 0.0
    pan.meters["saved"] = 0.0
    pan.meters["portioned"] = 0.0
    pan.meters["servings"] = 0.0
    aid_ent.meters["ready"] = 1.0

    world.facts.update(
        setting=setting,
        dish=dish,
        aid=aid,
        helpers_cfg=helpers_cfg,
        hero_name=hero_name,
        hero=hero,
        parent=parent,
        crowd=crowd,
        helpers=helpers,
        pan=pan,
        trait=trait,
    )

    introduce(world, hero, setting, dish)
    giant_cook(world, hero, dish)
    spot_crowd(world, hero, setting)

    world.para()
    if trait in GENEROUS_TRAITS:
        generous_thought(world, hero, dish)
        warn_need_help(world, hero, helpers_cfg, aid)
        ask_to_share(world, hero, helpers_cfg, aid)
    else:
        boast(world, hero, dish)
        try_alone(world, hero)
        gasp(world, hero)
        warn_need_help(world, hero, helpers_cfg, aid)
        ask_to_share(world, hero, helpers_cfg, aid)

    world.para()
    save_and_portion(world, dish, aid, helpers_cfg)
    lesson(world, hero, dish)
    ending_image(world, setting, dish)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            dish=dish.id,
            aid=aid.id,
            helpers=helpers_cfg.id,
            hero=hero_name,
            gender=hero_gender,
            parent=parent_type,
            trait=trait,
            seed=None,
        )),
        shared=True,
        wobble=pan.meters["wobble"] >= THRESHOLD,
        spill_risk=pan.meters["spill_risk"] >= THRESHOLD,
        servings=int(pan.meters["servings"]),
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


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the windy prairie edge",
        image="grain bent like it was bowing to every passing cloud",
        crowd_word="a line of hungry neighbors",
        supports={"basket", "plate"},
        tags={"sharing", "neighbors"},
    ),
    "square": Setting(
        id="square",
        place="the little town square",
        image="wagon spokes glittered and every porch seemed to be listening",
        crowd_word="half the town",
        supports={"bowl", "basket", "plate"},
        tags={"sharing", "town"},
    ),
    "barn": Setting(
        id="barn",
        place="the red barn dance yard",
        image="fiddles squeaked in the loft and boots thumped like rain on a roof",
        crowd_word="a ring of dancers and cousins",
        supports={"basket", "plate"},
        tags={"sharing", "family"},
    ),
}

DISHES = {
    "biscuits": Dish(
        id="biscuits",
        label="biscuits",
        phrase="a mountain of honey biscuits",
        scoop_word="biscuit",
        serving_kind="basket",
        weight=7,
        heat=2,
        brag="could keep me chewing till next spring",
        shared_end="And folks remembered that the biggest thing in the story was not the pan at all, but the open heart beside it.",
        tags={"bread", "sharing"},
    ),
    "corncakes": Dish(
        id="corncakes",
        label="corncakes",
        phrase="a tall stack of skillet corncakes",
        scoop_word="corncake",
        serving_kind="plate",
        weight=6,
        heat=2,
        brag="is enough to make me the strongest eater in three counties",
        shared_end="From then on, whenever someone bragged too hard, somebody would grin and say, 'Better fetch another plate and share like Tess.'",
        tags={"bread", "sharing"},
    ),
    "stew": Dish(
        id="stew",
        label="stew",
        phrase="a deep, savory stew thick with beans and carrots",
        scoop_word="ladle",
        serving_kind="bowl",
        weight=8,
        heat=3,
        brag="could keep every spoon in town busy and still leave me the best of it",
        shared_end="Long after the last bowl was scraped clean, the story kept simmering: kindness can make even a giant supper feel light.",
        tags={"stew", "sharing"},
    ),
}

AIDS = {
    "baskets": Aid(
        id="baskets",
        label="baskets",
        phrase="three willow baskets",
        serves={"basket"},
        carry_bonus=1,
        tags={"basket", "sharing"},
    ),
    "plates": Aid(
        id="plates",
        label="plates",
        phrase="a stack of tin plates",
        serves={"plate"},
        carry_bonus=1,
        tags={"plate", "sharing"},
    ),
    "bowls": Aid(
        id="bowls",
        label="bowls",
        phrase="a row of soup bowls",
        serves={"bowl"},
        carry_bonus=1,
        tags={"bowl", "sharing"},
    ),
}

HELPERS = {
    "cousins": HelperKind(
        id="cousins",
        label="cousins",
        phrase="three lanky cousins",
        count_word="three cousins",
        strength=2,
        tags={"family", "sharing"},
    ),
    "ranchers": HelperKind(
        id="ranchers",
        label="ranchers",
        phrase="two broad-shouldered ranchers",
        count_word="two ranchers",
        strength=3,
        tags={"neighbors", "sharing"},
    ),
    "bakers": HelperKind(
        id="bakers",
        label="bakers",
        phrase="two flour-dusted bakers",
        count_word="two bakers",
        strength=2,
        tags={"town", "sharing"},
    ),
}

GIRL_NAMES = ["Tess", "Mabel", "June", "Cora", "Nell", "Della"]
BOY_NAMES = ["Bo", "Cal", "Jeb", "Wade", "Rory", "Finn"]
TRAITS = ["generous", "kind", "neighborly", "boastful", "stubborn", "showy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for did, dish in DISHES.items():
            for aid_id, aid in AIDS.items():
                for hid, helper in HELPERS.items():
                    if can_share_here(setting, dish, aid, helper):
                        combos.append((sid, did, aid_id, hid))
    return combos


KNOWLEDGE = {
    "pan": [
        (
            "What is a pan?",
            "A pan is a wide cooking dish with a flat bottom. People use it to cook food over heat."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing lets other people enjoy something good too. It can also turn one person's work into something joyful for a whole group."
        )
    ],
    "basket": [
        (
            "What is a basket for?",
            "A basket can carry food from one place to another. It helps keep many pieces together so they are easier to pass around."
        )
    ],
    "plate": [
        (
            "What is a plate for?",
            "A plate gives food a clean, steady place to rest. That makes it easier to hand food to someone without dropping it."
        )
    ],
    "bowl": [
        (
            "Why does stew go in a bowl?",
            "Stew is soft and runny, so it needs high sides. A bowl holds the liquid so it does not spill."
        )
    ],
    "town": [
        (
            "What is a town square?",
            "A town square is an open place where many people can gather. It is often used for markets, meetings, and celebrations."
        )
    ],
    "neighbors": [
        (
            "Who are neighbors?",
            "Neighbors are people who live near you. Good neighbors often help each other when there is work to do."
        )
    ],
    "family": [
        (
            "How can family help with a big job?",
            "Family members can each do a small part, and together that makes a hard job easier. Helping together can also make the work feel cheerful."
        )
    ],
}
KNOWLEDGE_ORDER = ["pan", "sharing", "basket", "plate", "bowl", "town", "neighbors", "family"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    dish = f["dish"]
    setting = f["setting"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "pan" and teaches sharing.',
        f"Tell a warm frontier-style tall tale where {hero.attrs['name']} cooks {dish.label} in a giant pan in {setting.place} and learns that a feast is better when it is shared.",
        f'Write a simple exaggerated story with a big pan, hungry neighbors, and a happy ending that shows kindness can grow when food is shared.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    dish = f["dish"]
    setting = f["setting"]
    aid = f["aid"]
    helpers = f["helpers_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']}, a child with a giant pan of {dish.label}. The story also includes {setting.crowd_word} and the helpers who came to share the work."
        ),
        (
            "What made the pan hard to manage?",
            f"The pan was huge, heavy, and still hot from cooking. That meant one child could not carry it safely and serve everyone alone."
        ),
        (
            f"Why did {hero.attrs['name']} decide to share the food?",
            f"{hero.attrs['name']} saw that there was more food than one person needed. Sharing also brought extra hands, which kept the pan steady and let the hungry crowd eat."
        ),
        (
            "How did the helpers make things better?",
            f"The helpers came with {aid.label} and steady hands. Because they shared the work, the food could be passed out safely instead of wobbling or spilling."
        ),
    ]
    if outcome == "shared_after_wobble":
        qa.append(
            (
                f"What happened before {hero.attrs['name']} began sharing?",
                f"{hero.attrs['name']} tried to carry the pan alone first, and it wobbled badly. That scary moment showed that pride was not as useful as asking for help."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.attrs['name']} wait for trouble before sharing?",
                f"No. {hero.attrs['name']} thought ahead and chose to share before the pan could cause a problem. That kind choice made the whole feast easier from the start."
            )
        )
    qa.append(
        (
            "What is the lesson of the story?",
            f"The lesson is that sharing is wise as well as kind. When {hero.attrs['name']} opened the feast to others, the food fed more people and the day ended happier for everyone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pan", "sharing"} | set(f["setting"].tags) | set(f["dish"].tags) | set(f["aid"].tags) | set(f["helpers_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    dish: str
    aid: str
    helpers: str
    hero: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="square",
        dish="stew",
        aid="bowls",
        helpers="ranchers",
        hero="Tess",
        gender="girl",
        parent="father",
        trait="boastful",
        seed=None,
    ),
    StoryParams(
        setting="prairie",
        dish="biscuits",
        aid="baskets",
        helpers="cousins",
        hero="Bo",
        gender="boy",
        parent="mother",
        trait="generous",
        seed=None,
    ),
    StoryParams(
        setting="barn",
        dish="corncakes",
        aid="plates",
        helpers="bakers",
        hero="June",
        gender="girl",
        parent="father",
        trait="neighborly",
        seed=None,
    ),
    StoryParams(
        setting="square",
        dish="corncakes",
        aid="plates",
        helpers="ranchers",
        hero="Cal",
        gender="boy",
        parent="mother",
        trait="showy",
        seed=None,
    ),
]


def explain_rejection(setting: Setting, dish: Dish, aid: Aid, helpers: HelperKind) -> str:
    if not place_can_host(setting, dish):
        return (
            f"(No story: {setting.place} is not a good fit for serving {dish.label} this way. "
            f"Pick a place that can honestly host {dish.serving_kind}s.)"
        )
    if not aid_fits(aid, dish):
        return (
            f"(No story: {dish.label} should be served with {dish.serving_kind}s, not {aid.label}. "
            f"The serving aid must fit the food.)"
        )
    if helpers.strength < HELP_STRENGTH_MIN:
        return (
            f"(No story: {helpers.label} are not strong enough to steady a pan this large. "
            f"Pick helpers who can honestly help carry and serve it.)"
        )
    return "(No story: this combination does not make practical sense.)"


ASP_RULES = r"""
fit_place(S, D) :- setting(S), dish(D), supports(S, K), serving_kind(D, K).
fit_aid(A, D)   :- aid(A), dish(D), serves(A, K), serving_kind(D, K).
strong_enough(H) :- helper(H), strength(H, N), help_strength_min(M), N >= M.

valid(S, D, A, H) :- fit_place(S, D), fit_aid(A, D), strong_enough(H).

shared_early :- trait(T), generous_trait(T).
shared_after_wobble :- trait(T), boastful_trait(T).
outcome(shared_early) :- shared_early.
outcome(shared_after_wobble) :- shared_after_wobble.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for kind in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, kind))
    for did, dish in DISHES.items():
        lines.append(asp.fact("dish", did))
        lines.append(asp.fact("serving_kind", did, dish.serving_kind))
        lines.append(asp.fact("weight", did, dish.weight))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for kind in sorted(aid.serves):
            lines.append(asp.fact("serves", aid_id, kind))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("strength", hid, helper.strength))
    for t in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", t))
    for t in sorted(BOASTFUL_TRAITS):
        lines.append(asp.fact("boastful_trait", t))
    lines.append(asp.fact("help_strength_min", HELP_STRENGTH_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
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
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale sharing world: one huge pan, a hungry crowd, and a lesson about sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--helpers", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.dish and args.aid and args.helpers:
        setting = SETTINGS[args.setting]
        dish = DISHES[args.dish]
        aid = AIDS[args.aid]
        helpers = HELPERS[args.helpers]
        if not can_share_here(setting, dish, aid, helpers):
            raise StoryError(explain_rejection(setting, dish, aid, helpers))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.dish is None or combo[1] == args.dish)
        and (args.aid is None or combo[2] == args.aid)
        and (args.helpers is None or combo[3] == args.helpers)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, dish_id, aid_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        dish=dish_id,
        aid=aid_id,
        helpers=helper_id,
        hero=hero,
        gender=gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish: {params.dish})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.helpers not in HELPERS:
        raise StoryError(f"(Unknown helpers: {params.helpers})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    setting = SETTINGS[params.setting]
    dish = DISHES[params.dish]
    aid = AIDS[params.aid]
    helpers = HELPERS[params.helpers]
    if not can_share_here(setting, dish, aid, helpers):
        raise StoryError(explain_rejection(setting, dish, aid, helpers))

    world = tell(
        setting=setting,
        dish=dish,
        aid=aid,
        helpers_cfg=helpers,
        hero_name=params.hero,
        hero_gender=params.gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, dish, aid, helpers) combos:\n")
        for setting, dish, aid, helpers in combos:
            print(f"  {setting:8} {dish:10} {aid:8} {helpers}")
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
            header = (
                f"### {p.hero}: {p.dish} in {p.setting} "
                f"({p.aid}, {p.helpers}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
