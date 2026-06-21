#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py
==============================================================

A small standalone storyworld for gentle animal stories with a happy ending.

Premise
-------
A little animal wants to carry a present along a path to an older loved one.
A friend notices that the path itself makes the gift risky: a gust can blow a
light present away, a drizzly lane can soak a dry treat, or bumpy stepping
stones can spill something round. The friend suggests the right carrier. Some
heroes listen at once; others try first and need help in the middle. Either
way, the story ends warmly, with the gift safely shared.

The required word "ruffle" appears naturally in the weather beat:
the wind or damp air can ruffle feathers or fur.

Run it
------
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py --place hill_path --gift wreath
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py --fix ribbon_box --gift berries
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py --all
python storyworlds/worlds/gpt-5.4/ruffle_happy_ending_animal_story.py --verify
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
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Animal:
    id: str
    species: str
    coat: str
    home: str
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
class Place:
    id: str
    label: str
    path_phrase: str
    obstacle: str
    obstacle_text: str
    ruffle_text: str
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
class Gift:
    id: str
    label: str
    phrase: str
    category: str
    vulnerable_to: set[str]
    making_text: str
    ending_text: str
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
class Fix:
    id: str
    label: str
    phrase: str
    guards: set[str]
    fits: set[str]
    offer_text: str
    rescue_text: str
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
class StoryParams:
    place: str
    gift: str
    fix: str
    hero_name: str
    hero_animal: str
    helper_name: str
    helper_animal: str
    elder_name: str
    elder_animal: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    place = world.place
    gift = world.get("gift")
    if gift.attrs.get("open_carried") != 1:
        return out
    if gift.meters["at_risk"] < THRESHOLD:
        return out
    obstacle = place.obstacle
    if obstacle not in gift.attrs.get("vulnerable_to", set()):
        return out
    sig = ("damage", obstacle, gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if obstacle == "gust":
        gift.meters["lost_pieces"] += 1
        gift.meters["trouble"] += 1
        out.append("__gust_trouble__")
    elif obstacle == "drizzle":
        gift.meters["wet"] += 1
        gift.meters["trouble"] += 1
        out.append("__drizzle_trouble__")
    elif obstacle == "bump":
        gift.meters["spilled"] += 1
        gift.meters["trouble"] += 1
        out.append("__bump_trouble__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    hero = world.get("hero")
    helper = world.get("helper")
    if gift.meters["trouble"] < THRESHOLD:
        return out
    sig = ("worry", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    helper.memes["care"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="worry", tag="emotional", apply=_r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ANIMALS = {
    "duckling": Animal(
        id="duckling",
        species="duckling",
        coat="feathers",
        home="nest by the reeds",
        tags={"duck", "feathers"},
    ),
    "rabbit": Animal(
        id="rabbit",
        species="rabbit",
        coat="fur",
        home="burrow under the clover hill",
        tags={"rabbit", "fur"},
    ),
    "squirrel": Animal(
        id="squirrel",
        species="squirrel",
        coat="fur",
        home="oak-tree hollow",
        tags={"squirrel", "fur"},
    ),
    "mouse": Animal(
        id="mouse",
        species="mouse",
        coat="fur",
        home="little nook under a log",
        tags={"mouse", "fur"},
    ),
}

PLACES = {
    "hill_path": Place(
        id="hill_path",
        label="the hill path",
        path_phrase="up the windy hill path",
        obstacle="gust",
        obstacle_text="little gusts came skipping over the grass",
        ruffle_text="The breeze began to ruffle {hero}'s {coat}.",
        tags={"wind", "path"},
    ),
    "fern_lane": Place(
        id="fern_lane",
        label="the fern lane",
        path_phrase="through the fern lane after the rain",
        obstacle="drizzle",
        obstacle_text="tiny drops kept falling from the tall fern tips",
        ruffle_text="The cool damp air seemed to ruffle {hero}'s {coat}.",
        tags={"rain", "path"},
    ),
    "creek_stones": Place(
        id="creek_stones",
        label="the creek stones",
        path_phrase="across the creek stones",
        obstacle="bump",
        obstacle_text="the round stones wobbled under small feet",
        ruffle_text="Each careful hop made {hero}'s {coat} ruffle and bounce.",
        tags={"creek", "stones"},
    ),
}

GIFTS = {
    "wreath": Gift(
        id="wreath",
        label="dandelion wreath",
        phrase="a soft dandelion wreath",
        category="light",
        vulnerable_to={"gust"},
        making_text="wove a ring of bright dandelion heads with the longest stems",
        ending_text="resting like a little sunshine crown on the teapot",
        tags={"flowers", "light"},
    ),
    "cakes": Gift(
        id="cakes",
        label="seed cakes",
        phrase="three crumbly seed cakes",
        category="dry",
        vulnerable_to={"drizzle"},
        making_text="pressed seeds and honey into three tiny cakes on a flat leaf",
        ending_text="set out on a mossy plate beside warm acorn tea",
        tags={"cake", "seeds"},
    ),
    "berries": Gift(
        id="berries",
        label="berries",
        phrase="a heap of shiny red berries",
        category="round",
        vulnerable_to={"bump"},
        making_text="picked the ripest red berries and piled them in a shallow leaf tray",
        ending_text="tucked into a jam bowl that shone ruby in the firelight",
        tags={"berries", "fruit"},
    ),
    "painting": Gift(
        id="painting",
        label="pinecone painting",
        phrase="a pinecone painting",
        category="paper",
        vulnerable_to={"gust", "drizzle"},
        making_text="dabbed berry juice and pine-needle green across a smooth scrap of bark paper",
        ending_text="leaning proudly against the elder's favorite mug",
        tags={"painting", "paper"},
    ),
}

FIXES = {
    "ribbon_box": Fix(
        id="ribbon_box",
        label="ribbon-tied box",
        phrase="a small ribbon-tied box",
        guards={"gust"},
        fits={"light", "paper"},
        offer_text="put it in my ribbon-tied box so the wind cannot tease it away",
        rescue_text="opened a ribbon-tied box and sheltered the gift inside",
        tags={"box", "wind"},
    ),
    "wax_wrap": Fix(
        id="wax_wrap",
        label="wax-leaf wrap",
        phrase="a waxy leaf wrap",
        guards={"drizzle"},
        fits={"dry", "paper"},
        offer_text="wrap it in this waxy leaf so the drops cannot soak it",
        rescue_text="spread a waxy leaf around the gift and tucked every edge snug",
        tags={"wrap", "rain"},
    ),
    "deep_basket": Fix(
        id="deep_basket",
        label="deep berry basket",
        phrase="a deep berry basket",
        guards={"bump"},
        fits={"round"},
        offer_text="carry it in my deep berry basket so the stones cannot jolt it out",
        rescue_text="held out a deep berry basket and helped gather everything back in",
        tags={"basket", "berries"},
    ),
    "lidded_tin": Fix(
        id="lidded_tin",
        label="lidded tin",
        phrase="a shiny little lidded tin",
        guards={"gust", "drizzle"},
        fits={"dry", "light"},
        offer_text="keep it in this lidded tin and the path will not bother it",
        rescue_text="clicked open a little lidded tin and slipped the gift safely inside",
        tags={"tin", "lid"},
    ),
}

NAMES = [
    "Pip",
    "Mimi",
    "Tumble",
    "Nettle",
    "Dot",
    "Hazel",
    "Moss",
    "Peep",
    "Bramble",
    "Poppy",
]
TRAITS = ["careful", "patient", "thoughtful", "gentle", "bouncy", "hasty", "eager"]


def gift_at_risk(place: Place, gift: Gift) -> bool:
    return place.obstacle in gift.vulnerable_to


def compatible_fix(place: Place, gift: Gift, fix: Fix) -> bool:
    return gift_at_risk(place, gift) and place.obstacle in fix.guards and gift.category in fix.fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for gift_id, gift in GIFTS.items():
            for fix_id, fix in FIXES.items():
                if compatible_fix(place, gift, fix):
                    combos.append((place_id, gift_id, fix_id))
    return sorted(combos)


def would_prepare(trait: str) -> bool:
    return trait in CAREFUL_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "prepared" if would_prepare(params.trait) else "rescued"


def explain_rejection(place: Place, gift: Gift, fix: Optional[Fix] = None) -> str:
    if not gift_at_risk(place, gift):
        return (
            f"(No story: {gift.phrase} is not the kind of present that would be troubled on "
            f"{place.label}. The path needs to create a real problem before a fix can matter.)"
        )
    if fix is not None and place.obstacle not in fix.guards:
        return (
            f"(No story: {fix.label} does not protect a gift from the trouble on {place.label}. "
            f"Choose a carrier that guards against {place.obstacle}.)"
        )
    if fix is not None and gift.category not in fix.fits:
        return (
            f"(No story: {fix.label} is not a sensible carrier for {gift.label}. "
            f"The fix must fit the gift as well as the path.)"
        )
    return "(No story: this combination is unreasonable in this world.)"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    gift = sim.get("gift")
    gift.attrs["open_carried"] = 1
    gift.meters["at_risk"] = 1
    propagate(sim, narrate=False)
    return {
        "trouble": gift.meters["trouble"] >= THRESHOLD,
        "lost_pieces": gift.meters["lost_pieces"],
        "wet": gift.meters["wet"],
        "spilled": gift.meters["spilled"],
    }


def introduce(world: World, hero: Entity, gift_cfg: Gift, elder: Entity) -> None:
    world.say(
        f"In {hero.attrs['home']}, {hero.id} the little {hero.type} {gift_cfg.making_text} "
        f"for {elder.id}. {hero.pronoun('possessive').capitalize()} heart felt big and warm at the thought of sharing it."
    )


def set_out(world: World, hero: Entity, helper: Entity, place: Place, gift_cfg: Gift) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"That afternoon, {hero.id} started {place.path_phrase} with {gift_cfg.phrase}. "
        f"{helper.id} the {helper.type} trotted along beside {hero.pronoun('object')}."
    )
    world.say(place.obstacle_text)
    world.say(place.ruffle_text.format(hero=hero.id, coat=hero.attrs["coat"]))


def warn(world: World, hero: Entity, helper: Entity, place: Place, gift: Entity, gift_cfg: Gift) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_trouble"] = pred
    hero.memes["uncertain"] += 1
    if not pred["trouble"]:
        return
    if place.obstacle == "gust":
        because = f"the wind could snatch at the {gift_cfg.label}"
    elif place.obstacle == "drizzle":
        because = f"the drops could soak the {gift_cfg.label}"
    else:
        because = f"the stones could jolt the {gift_cfg.label} right out"
    world.say(
        f'"Wait a moment," {helper.id} said. "If you carry it that way, {because}."'
    )


def accept_fix(world: World, hero: Entity, helper: Entity, fix_cfg: Fix) -> None:
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'{hero.id} stopped and listened. "{fix_cfg.offer_text.capitalize()}," '
        f"{helper.id} said."
    )
    world.say(
        f"{hero.id} nodded, because the idea sounded kind and sensible."
    )


def pack_gift(world: World, gift: Entity, fix_cfg: Fix) -> None:
    gift.attrs["open_carried"] = 0
    gift.attrs["carrier"] = fix_cfg.id
    gift.meters["safe"] += 1


def try_open_path(world: World, hero: Entity, helper: Entity, place: Place, gift: Entity, gift_cfg: Gift) -> None:
    gift.attrs["open_carried"] = 1
    gift.meters["at_risk"] = 1
    world.say(
        f"But {hero.id} took three small steps anyway, still carrying {gift_cfg.phrase} the old easy way."
    )
    propagate(world, narrate=False)
    if gift.meters["lost_pieces"] >= THRESHOLD:
        world.say(
            f"A frisking gust tugged at the {gift_cfg.label}, and a bit of it fluttered loose."
        )
    elif gift.meters["wet"] >= THRESHOLD:
        world.say(
            f"A cold drop tapped the {gift_cfg.label}, then another, until the edges began to look damp."
        )
    elif gift.meters["spilled"] >= THRESHOLD:
        world.say(
            f"One wobble on the stones tipped the shallow tray, and the berries rolled with tiny red bumps."
        )
    world.say(
        f"{hero.id}'s ears drooped. {helper.id} hurried closer at once."
    )


def rescue(world: World, hero: Entity, helper: Entity, gift: Entity, fix_cfg: Fix, gift_cfg: Gift) -> None:
    pack_gift(world, gift, fix_cfg)
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["care"] += 1
    gift.meters["saved"] += 1
    world.say(
        f'"It is not ruined," {helper.id} said gently. {helper.id} {fix_cfg.rescue_text}.'
    )
    if gift.meters["lost_pieces"] >= THRESHOLD:
        world.say(
            f"Together they tucked the wandering wreath back into shape."
        )
    elif gift.meters["wet"] >= THRESHOLD:
        world.say(
            f"Together they patted the damp corners dry under a broad leaf."
        )
    elif gift.meters["spilled"] >= THRESHOLD:
        world.say(
            f"Together they picked up every shiny berry that had not burst."
        )
    world.say(
        f"Soon the present was safe again, and {hero.id} could breathe easily."
    )


def arrive(world: World, hero: Entity, helper: Entity, elder: Entity, gift_cfg: Gift) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    elder.memes["love"] += 1
    world.say(
        f"When they reached {elder.id}'s {elder.attrs['home']}, the door was already open with welcome."
    )
    world.say(
        f"{elder.id} smiled wide at the sight of {hero.id} carrying {gift_cfg.phrase} so carefully."
    )


def share_end(world: World, hero: Entity, helper: Entity, elder: Entity, gift_cfg: Gift) -> None:
    hero.memes["gratitude"] += 1
    helper.memes["gratitude"] += 1
    world.say(
        f'''"For me?" {elder.id} asked. {hero.id} nodded and gave the gift over with both paws."'''
        if hero.type in {"rabbit", "squirrel", "mouse"}
        else f'"For me?" {elder.id} asked. {hero.id} nodded and gave the gift over with both wings.'
    )
    world.say(
        f"Soon it was {gift_cfg.ending_text}, and the little home smelled of tea, toast, and happy voices."
    )
    world.say(
        f"{hero.id} leaned against {helper.id} and felt glad for the warning, the help, and the warm ending to the walk."
    )


def tell(
    place: Place,
    gift_cfg: Gift,
    fix_cfg: Fix,
    hero_name: str,
    hero_animal: Animal,
    helper_name: str,
    helper_animal: Animal,
    elder_name: str,
    elder_animal: Animal,
    trait: str,
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_animal.species,
            role="hero",
            attrs={"coat": hero_animal.coat, "home": hero_animal.home, "trait": trait},
            tags=set(hero_animal.tags),
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_animal.species,
            role="helper",
            attrs={"coat": helper_animal.coat, "home": helper_animal.home},
            tags=set(helper_animal.tags),
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_animal.species,
            role="elder",
            attrs={"coat": elder_animal.coat, "home": elder_animal.home},
            tags=set(elder_animal.tags),
        )
    )
    gift = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift_cfg.label,
            attrs={
                "category": gift_cfg.category,
                "vulnerable_to": set(gift_cfg.vulnerable_to),
                "open_carried": 0,
                "carrier": "",
            },
            tags=set(gift_cfg.tags),
        )
    )
    gift.meters["at_risk"] = 0
    gift.meters["trouble"] = 0
    gift.meters["lost_pieces"] = 0
    gift.meters["wet"] = 0
    gift.meters["spilled"] = 0
    hero.memes["worry"] = 0
    helper.memes["care"] = 0
    world.facts["predicted_trouble"] = {"trouble": False, "lost_pieces": 0, "wet": 0, "spilled": 0}

    introduce(world, hero, gift_cfg, elder)
    world.para()
    set_out(world, hero, helper, place, gift_cfg)
    warn(world, hero, helper, place, gift, gift_cfg)

    prepared = would_prepare(trait)
    if prepared:
        accept_fix(world, hero, helper, fix_cfg)
        pack_gift(world, gift, fix_cfg)
        world.para()
        arrive(world, hero, helper, elder, gift_cfg)
        share_end(world, hero, helper, elder, gift_cfg)
        outcome = "prepared"
    else:
        world.say(
            f'{hero.id} wanted to be quick and brave. "Maybe it will be all right," {hero.pronoun()} said.'
        )
        world.para()
        try_open_path(world, hero, helper, place, gift, gift_cfg)
        rescue(world, hero, helper, gift, fix_cfg, gift_cfg)
        world.para()
        arrive(world, hero, helper, elder, gift_cfg)
        share_end(world, hero, helper, elder, gift_cfg)
        outcome = "rescued"

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        place=place,
        gift_cfg=gift_cfg,
        fix_cfg=fix_cfg,
        gift=gift,
        outcome=outcome,
        prepared=prepared,
        rescued=(outcome == "rescued"),
    )
    return world


KNOWLEDGE = {
    "wind": [
        (
            "What can a strong breeze do to light things?",
            "A strong breeze can push, lift, and scatter light things. That is why a light present may need a box or lid on a windy path."
        )
    ],
    "rain": [
        (
            "Why do dry treats need to stay out of drizzle?",
            "Dry treats can turn soggy when little drops soak into them. Covering them keeps them tasty and easy to carry."
        )
    ],
    "berries": [
        (
            "Why do berries spill so easily?",
            "Berries are round and smooth, so they can roll when a tray tips. A deeper basket helps keep them together."
        )
    ],
    "flowers": [
        (
            "Why might a flower wreath need a box in the wind?",
            "A flower wreath is light and soft, so the wind can tug it out of shape. A box keeps it from fluttering away."
        )
    ],
    "painting": [
        (
            "Why should a painting stay dry?",
            "A painting can smear or wrinkle when it gets wet. Keeping it wrapped helps the colors stay neat."
        )
    ],
    "box": [
        (
            "What does a box do for something delicate?",
            "A box gives a gift firm sides and a safer shape. That helps protect it while someone walks with it."
        )
    ],
    "wrap": [
        (
            "What does a wrap do for a present?",
            "A wrap covers the outside of a present. That can help keep out drips and little splashes."
        )
    ],
    "basket": [
        (
            "Why is a deep basket good for carrying round fruit?",
            "A deep basket has higher sides, so round fruit is less likely to roll out. It makes bumpy walking safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "rain", "berries", "flowers", "painting", "box", "wrap", "basket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    gift_cfg = f["gift_cfg"]
    if f["outcome"] == "prepared":
        return [
            f'Write a gentle animal story for a 3-to-5-year-old that includes the word "ruffle" and ends happily.',
            f"Tell a story where {hero.id} carries {gift_cfg.phrase} along {place.label}, listens to {helper.id}'s good advice, and reaches an older loved one safely.",
            f"Write a warm woodland story where a little animal pauses, chooses the right way to carry a gift, and learns that careful help can keep a day sweet.",
        ]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the word "ruffle" and ends happily.',
        f"Tell a story where {hero.id} tries to carry {gift_cfg.phrase} the easy way, runs into trouble on {place.label}, and is helped by {helper.id}.",
        f"Write a warm animal story with a small middle mishap, a kind rescue, and a cozy ending where the present still reaches the elder.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    place = f["place"]
    gift_cfg = f["gift_cfg"]
    fix_cfg = f["fix_cfg"]
    pred = f["predicted_trouble"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, and {helper.id}, the friend who walked beside {hero.pronoun('object')}. They were taking a present to {elder.id}."
        ),
        (
            f"What was {hero.id} carrying?",
            f"{hero.id} was carrying {gift_cfg.phrase} for {elder.id}. The gift mattered because it was made with love, not just picked up on the way."
        ),
        (
            f"Why did {helper.id} warn {hero.id} on {place.label}?",
            (
                f"{helper.id} warned {hero.id} because the path itself could trouble the gift. "
                + (
                    "The wind could pull at it and spoil its shape."
                    if pred["lost_pieces"] >= THRESHOLD
                    else "The drizzle could soak it."
                    if pred["wet"] >= THRESHOLD
                    else "The bumpy stones could jolt it out and make it spill."
                )
            ),
        ),
    ]
    if f["outcome"] == "prepared":
        qa.append(
            (
                f"How did the problem get solved before anything went wrong?",
                f"{hero.id} listened and used {fix_cfg.phrase}. That kept the gift safe before the tricky part of the walk could harm it."
            )
        )
    else:
        if world.get("gift").meters["lost_pieces"] >= THRESHOLD:
            trouble = "a gust tugged at the wreath and made part of it flutter loose"
        elif world.get("gift").meters["wet"] >= THRESHOLD:
            trouble = "drips began to dampen the gift"
        else:
            trouble = "the berries rolled when the tray tipped on the stones"
        qa.append(
            (
                f"What went wrong in the middle of the story?",
                f"When {hero.id} tried the easy way first, {trouble}. That frightened {hero.pronoun('object')} for a moment because the present might not reach {elder.id} nicely."
            )
        )
        qa.append(
            (
                f"How did {helper.id} help?",
                f"{helper.id} used {fix_cfg.phrase} and helped make the present safe again. Because {helper.pronoun()} stayed calm, the walk could still end happily."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the gift safely reaching {elder.id} and everyone sharing a warm, happy moment together. The ending proves that kindness and the right help changed the hard part of the walk."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.place.tags) | set(world.facts["gift_cfg"].tags) | set(world.facts["fix_cfg"].tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", 0, None, set())}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
gift_at_risk(P,G) :- place(P), gift(G), obstacle(P,O), vulnerable(G,O).
compatible_fix(P,G,F) :- gift_at_risk(P,G), fix(F), obstacle(P,O), guards(F,O), category(G,C), fits(F,C).
valid(P,G,F) :- compatible_fix(P,G,F).

careful_now(T) :- trait(T), careful_trait(T).
outcome(prepared) :- careful_now(T), trait(T).
outcome(rescued) :- trait(T), not careful_now(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("obstacle", place_id, place.obstacle))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("category", gift_id, gift.category))
        for vuln in sorted(gift.vulnerable_to):
            lines.append(asp.fact("vulnerable", gift_id, vuln))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for guard in sorted(fix.guards):
            lines.append(asp.fact("guards", fix_id, guard))
        for fit in sorted(fix.fits):
            lines.append(asp.fact("fits", fix_id, fit))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle animal storyworld: a present, a risky path, and the right help."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-animal", choices=ANIMALS)
    ap.add_argument("--helper-animal", choices=ANIMALS)
    ap.add_argument("--elder-animal", choices=ANIMALS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> str:
    choices = [n for n in NAMES if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.gift:
        place = PLACES[args.place]
        gift = GIFTS[args.gift]
        if not gift_at_risk(place, gift):
            raise StoryError(explain_rejection(place, gift))
    if args.place and args.gift and args.fix:
        place = PLACES[args.place]
        gift = GIFTS[args.gift]
        fix = FIXES[args.fix]
        if not compatible_fix(place, gift, fix):
            raise StoryError(explain_rejection(place, gift, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.gift is None or combo[1] == args.gift)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, gift_id, fix_id = rng.choice(combos)
    used: set[str] = set()
    hero_name = args.hero_name or _pick_name(rng, used)
    used.add(hero_name)
    helper_name = args.helper_name or _pick_name(rng, used)
    used.add(helper_name)
    elder_name = args.elder_name or _pick_name(rng, used)
    hero_animal = args.hero_animal or rng.choice(sorted(ANIMALS))
    helper_animal = args.helper_animal or rng.choice(sorted(ANIMALS))
    elder_animal = args.elder_animal or rng.choice(sorted(ANIMALS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        gift=gift_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_animal=hero_animal,
        helper_name=helper_name,
        helper_animal=helper_animal,
        elder_name=elder_name,
        elder_animal=elder_animal,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.hero_animal not in ANIMALS or params.helper_animal not in ANIMALS or params.elder_animal not in ANIMALS:
        raise StoryError("(Unknown animal choice.)")

    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    fix = FIXES[params.fix]
    if not compatible_fix(place, gift, fix):
        raise StoryError(explain_rejection(place, gift, fix))

    world = tell(
        place=place,
        gift_cfg=gift,
        fix_cfg=fix,
        hero_name=params.hero_name,
        hero_animal=ANIMALS[params.hero_animal],
        helper_name=params.helper_name,
        helper_animal=ANIMALS[params.helper_animal],
        elder_name=params.elder_name,
        elder_animal=ANIMALS[params.elder_animal],
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


CURATED = [
    StoryParams(
        place="hill_path",
        gift="wreath",
        fix="ribbon_box",
        hero_name="Pip",
        hero_animal="duckling",
        helper_name="Hazel",
        helper_animal="rabbit",
        elder_name="Moss",
        elder_animal="mouse",
        trait="careful",
    ),
    StoryParams(
        place="fern_lane",
        gift="cakes",
        fix="wax_wrap",
        hero_name="Dot",
        hero_animal="mouse",
        helper_name="Bramble",
        helper_animal="squirrel",
        elder_name="Poppy",
        elder_animal="rabbit",
        trait="hasty",
    ),
    StoryParams(
        place="creek_stones",
        gift="berries",
        fix="deep_basket",
        hero_name="Mimi",
        hero_animal="rabbit",
        helper_name="Peep",
        helper_animal="duckling",
        elder_name="Nettle",
        elder_animal="squirrel",
        trait="eager",
    ),
    StoryParams(
        place="hill_path",
        gift="painting",
        fix="ribbon_box",
        hero_name="Tumble",
        hero_animal="squirrel",
        helper_name="Hazel",
        helper_animal="mouse",
        elder_name="Pip",
        elder_animal="rabbit",
        trait="thoughtful",
    ),
    StoryParams(
        place="fern_lane",
        gift="painting",
        fix="wax_wrap",
        hero_name="Poppy",
        hero_animal="duckling",
        helper_name="Dot",
        helper_animal="rabbit",
        elder_name="Moss",
        elder_animal="duckling",
        trait="patient",
    ),
]


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, gift, fix) combos:\n")
        for place, gift, fix in combos:
            print(f"  {place:12} {gift:10} {fix}")
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
            header = f"### {p.hero_name}: {p.gift} on {p.place} ({p.fix}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
