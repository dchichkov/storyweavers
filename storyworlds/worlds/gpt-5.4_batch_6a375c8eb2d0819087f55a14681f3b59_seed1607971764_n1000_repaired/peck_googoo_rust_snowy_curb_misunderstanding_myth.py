#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py
================================================================================

A standalone storyworld for a tiny winter myth: on a snowy curb, a young bird
misunderstands a friend's dreamy saying about a rust-red mark, mistakes it for
food, and learns to ask before it pecks.

The world is classical and state-driven:
- typed entities carry physical meters and emotional memes
- a small forward-chaining rule set turns actions into soreness, relief, and joy
- a Python reasonableness gate constrains which misunderstandings make sense
- an inline ASP twin mirrors the validity and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py --bird robin --lure rust_smear
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py --lure rusty_bolt
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/peck_googoo_rust_snowy_curb_misunderstanding_myth.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible_kind: str = ""
    hard: bool = False
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "man", "king"}
        female = {"girl", "mother", "woman", "queen"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class BirdKind:
    id: str
    label: str
    winter_food: str
    step: str
    color: str
    voice: str
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


@dataclass
class Lure:
    id: str
    label: str
    place: str
    look: str
    appeal: str
    myth_word: str
    lesson_name: str
    risk: int = 1
    misleading: bool = True
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
class FoodSource:
    id: str
    label: str
    place: str
    food_kind: str
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
class Guide:
    id: str
    label: str
    type: str
    knows: set[str]
    speed: int
    proverb: str
    arrival: str
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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
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


def _r_bad_peck(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    lure = world.get("lure")
    if hero.meters["pecked"] < THRESHOLD:
        return out
    if lure.edible_kind:
        return out
    sig = ("bad_peck", hero.id, lure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["beak_sore"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["fear"] += 1
    out.append("__sore_beak__")
    return out


def _r_eat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    food = world.get("food")
    if hero.meters["eating"] < THRESHOLD or not food.edible_kind:
        return out
    sig = ("eat", hero.id, food.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["hunger"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    out.append("__fed__")
    return out


def _r_understand(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["understanding"] < THRESHOLD:
        return out
    sig = ("understood", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["wisdom"] += 1
    hero.memes["fear"] = 0.0
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule(name="bad_peck", tag="physical", apply=_r_bad_peck),
    Rule(name="eat", tag="physical", apply=_r_eat),
    Rule(name="understand", tag="social", apply=_r_understand),
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


def misunderstanding_possible(bird: BirdKind, lure: Lure) -> bool:
    return lure.misleading and bird.winter_food == lure.appeal


def guiding_fix_exists(bird: BirdKind, food: FoodSource, guide: Guide) -> bool:
    return food.food_kind == bird.winter_food and bird.winter_food in guide.knows


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for bird_id, bird in BIRDS.items():
        for lure_id, lure in LURES.items():
            for food_id, food in FOODS.items():
                for guide_id, guide in GUIDES.items():
                    if misunderstanding_possible(bird, lure) and guiding_fix_exists(bird, food, guide):
                        combos.append((bird_id, lure_id, food_id, guide_id))
    return combos


def can_avert(guide: Guide, watch: str, lure: Lure) -> bool:
    return watch == "near" and guide.speed >= lure.risk


def predict_bad_peck(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["pecked"] += 1
    propagate(sim, narrate=False)
    return hero.meters["beak_sore"] >= THRESHOLD


def scene_open(world: World, hero: Entity, bird: BirdKind) -> None:
    hero.meters["hunger"] = 1.0
    hero.meters["cold"] = 1.0
    hero.memes["wonder"] = 1.0
    world.say(
        f"In the old winter days, when snow laid a white hem along the curb and the street "
        f"looked as still as a sleeping river, there lived a little {bird.label} named {hero.id}."
    )
    world.say(
        f"{hero.id} came {bird.step} over the snowy curb, {bird.color} feathers puffed against the cold, "
        f"looking for {bird.winter_food} beneath the morning glitter."
    )


def friend_arrives(world: World, friend: Entity, hero: Entity, lure: Lure) -> None:
    friend.memes["dreaminess"] = 1.0
    world.say(
        f"With {hero.id} came a round young pigeon called {friend.id}, who liked to murmur "
        f'"googoo, googoo," as if talking to the snow itself.'
    )
    world.say(
        f"{friend.id} tilted {friend.pronoun('possessive')} head at {lure.label} and whispered, "
        f'"The Winter Curb keeps little gifts in red places. Maybe that bright bit is one."'
    )


def spot_lure(world: World, hero: Entity, lure: Lure) -> None:
    hero.memes["hunger"] += 1
    world.say(
        f"There on {lure.place} lay {lure.label}, {lure.look}. In the white morning it truly did "
        f"look a little like {lure.myth_word}."
    )
    world.say(
        f"{hero.id} stared so hard that the misunderstanding grew warm inside {hero.pronoun('object')}: "
        f"perhaps the red mark was breakfast, not merely rust."
    )


def warning(world: World, guide_ent: Entity, guide: Guide, hero: Entity, lure: Lure) -> None:
    world.facts["predicted_bad_peck"] = predict_bad_peck(world)
    world.say(
        f"But {guide.arrival} came {guide.label}. {guide_ent.id} had watched many winters and knew the curb's tricks."
    )
    if world.facts["predicted_bad_peck"]:
        world.say(
            f'"Little one," {guide_ent.id} called, "{lure.lesson_name} is not for eating. '
            f'{guide.proverb}"'
        )


def peck_wrong(world: World, hero: Entity, lure_ent: Entity, lure: Lure) -> None:
    hero.meters["pecked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But hunger ran quicker than wisdom. {hero.id} darted forward and gave {lure.label} a peck."
    )
    if hero.meters["beak_sore"] >= THRESHOLD:
        world.say(
            f"The sound was tiny and hard. {hero.pronoun('possessive').capitalize()} beak stung at once, "
            f"for the red shine was only rust sleeping on old iron."
        )


def stop_in_time(world: World, guide_ent: Entity, hero: Entity, lure: Lure) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"{guide_ent.id} spread {guide_ent.pronoun('possessive')} wings across the mark just in time, "
        f"and {hero.id} stopped with {hero.pronoun('possessive')} beak a feather-width away."
    )
    world.say(
        f'"See?" said {guide_ent.id}. "Red can call to hungry eyes, but not every red thing is food."'
    )


def explain(world: World, guide_ent: Entity, guide: Guide, hero: Entity, friend: Entity, lure: Lure) -> None:
    hero.memes["understanding"] += 1
    propagate(world, narrate=False)
    if hero.meters["beak_sore"] >= THRESHOLD:
        world.say(
            f"{friend.id} shuffled close, ashamed. \"I only meant it looked lucky,\" {friend.pronoun()} said softly."
        )
    else:
        world.say(
            f"{friend.id} bobbed in the snow. \"So that is what the curb was hiding,\" {friend.pronoun()} said. "
            f"\"Not food, but a lesson.\""
        )
    world.say(
        f'{guide_ent.id} nodded. "Rust is old iron wearing a red winter coat," {guide_ent.pronoun()} said. '
        f'"It may glitter, but it does not feed a hungry heart."'
    )


def lead_to_food(world: World, guide_ent: Entity, hero: Entity, food_ent: Entity, food: FoodSource) -> None:
    hero.meters["eating"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {guide_ent.id} led them to {food.place}, where {food.label} waited {food.image}."
    )
    world.say(
        f"{hero.id} ate there at last, and the cold curb no longer felt like a cruel place."
    )


def ending(world: World, hero: Entity, friend: Entity, lure: Lure, food: FoodSource) -> None:
    world.say(
        f"Since that morning, when red shone from a snowy curb, {hero.id} did not peck first and wonder later."
    )
    world.say(
        f"{hero.pronoun().capitalize()} asked, {friend.id} listened more carefully, and together they searched for "
        f"true {food.food_kind} instead of {lure.lesson_name}."
    )
    final = "The snow kept its silence, but the little birds had learned how to hear it rightly."
    if hero.meters["beak_sore"] >= THRESHOLD:
        final = (
            f"Even when {hero.pronoun('possessive')} beak remembered that first sting, {hero.id} smiled, "
            f"for the snowy curb had given a painful lesson and a kinder ending."
        )
    world.say(final)


def tell(
    bird: BirdKind,
    lure: Lure,
    food: FoodSource,
    guide: Guide,
    watch: str,
    hero_name: str,
    friend_name: str = "Googoo",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="bird", label=bird.label, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="bird", label="young pigeon", role="friend"))
    guide_ent = world.add(Entity(id=guide.label.title(), kind="character", type=guide.type, label=guide.label, role="guide"))
    lure_ent = world.add(Entity(id="lure", kind="thing", type="iron", label=lure.label, role="lure", hard=True))
    food_ent = world.add(
        Entity(id="food", kind="thing", type="food", label=food.label, role="food", edible_kind=food.food_kind)
    )

    world.facts["watch"] = watch
    world.facts["outcome"] = "averted" if can_avert(guide, watch, lure) else "sore_then_feast"

    scene_open(world, hero, bird)
    friend_arrives(world, friend, hero, lure)
    world.para()
    spot_lure(world, hero, lure)
    warning(world, guide_ent, guide, hero, lure)

    world.para()
    if can_avert(guide, watch, lure):
        stop_in_time(world, guide_ent, hero, lure)
    else:
        peck_wrong(world, hero, lure_ent, lure)
    explain(world, guide_ent, guide, hero, friend, lure)

    world.para()
    lead_to_food(world, guide_ent, hero, food_ent, food)
    ending(world, hero, friend, lure, food)

    world.facts.update(
        hero=hero,
        friend=friend,
        guide_ent=guide_ent,
        bird_cfg=bird,
        lure_cfg=lure,
        food_cfg=food,
        guide_cfg=guide,
        sore=hero.meters["beak_sore"] >= THRESHOLD,
        fed=hero.meters["hunger"] < THRESHOLD,
    )
    return world


BIRDS = {
    "sparrow": BirdKind(
        id="sparrow",
        label="sparrow",
        winter_food="grain",
        step="in quick hops",
        color="brown",
        voice="chip",
        title="seed-finder",
        tags={"bird", "grain"},
    ),
    "robin": BirdKind(
        id="robin",
        label="robin",
        winter_food="berry",
        step="in bright little steps",
        color="red-breasted",
        voice="tik",
        title="hedge-singer",
        tags={"bird", "berry"},
    ),
    "pigeon": BirdKind(
        id="pigeon",
        label="pigeon",
        winter_food="grain",
        step="in round proud steps",
        color="silver-necked",
        voice="coo",
        title="curb-walker",
        tags={"bird", "grain"},
    ),
}

LURES = {
    "rust_flakes": Lure(
        id="rust_flakes",
        label="rust flakes on a bent signpost",
        place="the bent post by the curb",
        look="little red crumbs caught in a seam of snow",
        appeal="grain",
        myth_word="scattered seed",
        lesson_name="rust flakes",
        risk=1,
        misleading=True,
        tags={"rust", "metal"},
    ),
    "rust_ring": Lure(
        id="rust_ring",
        label="a rust ring around a drain grate",
        place="the iron grate at the curb",
        look="a neat circle of red-brown dust around black bars",
        appeal="grain",
        myth_word="a dropped breakfast wreath",
        lesson_name="the rust ring",
        risk=1,
        misleading=True,
        tags={"rust", "drain"},
    ),
    "rust_smear": Lure(
        id="rust_smear",
        label="a rust smear on an old rail",
        place="the low rail beside the snowy curb",
        look="a red streak bright as berry juice on gray iron",
        appeal="berry",
        myth_word="berry jam",
        lesson_name="the rust smear",
        risk=2,
        misleading=True,
        tags={"rust", "rail"},
    ),
    "rusty_bolt": Lure(
        id="rusty_bolt",
        label="a rusty bolt head",
        place="the frozen edge of the curb",
        look="one hard round knob with no soft promise in it",
        appeal="none",
        myth_word="nothing a bird would trust for supper",
        lesson_name="the rusty bolt",
        risk=2,
        misleading=False,
        tags={"rust", "bolt"},
    ),
}

FOODS = {
    "bakery_crumbs": FoodSource(
        id="bakery_crumbs",
        label="warm bakery crumbs",
        place="the step behind the corner bakery",
        food_kind="grain",
        image="under a window breathing out bread-sweet air",
        tags={"grain", "bread"},
    ),
    "window_seed": FoodSource(
        id="window_seed",
        label="birdseed",
        place="the blue house with the feeder",
        food_kind="grain",
        image="in a little drift beneath a shaking feeder",
        tags={"grain", "seed"},
    ),
    "winter_berries": FoodSource(
        id="winter_berries",
        label="winter berries",
        place="the vine over the brick wall",
        food_kind="berry",
        image="like red lamps above the snow",
        tags={"berry", "vine"},
    ),
}

GUIDES = {
    "crow_mother": Guide(
        id="crow_mother",
        label="crow mother",
        type="bird",
        knows={"grain", "berry"},
        speed=2,
        proverb="Ask twice, peck once.",
        arrival="down from a lamp post",
        tags={"crow", "wisdom"},
    ),
    "lamp_gull": Guide(
        id="lamp_gull",
        label="lamp gull",
        type="bird",
        knows={"grain"},
        speed=1,
        proverb="Street-glitter is not supper.",
        arrival="off the high streetlamp",
        tags={"gull", "wisdom"},
    ),
    "hedge_wren": Guide(
        id="hedge_wren",
        label="hedge wren",
        type="bird",
        knows={"berry"},
        speed=2,
        proverb="A bright stain is not the same as a sweet fruit.",
        arrival="out of the bare hedge",
        tags={"wren", "wisdom"},
    ),
}

HERO_NAMES = {
    "sparrow": ["Pip", "Mote", "Nip", "Dab"],
    "robin": ["Bram", "Rill", "Tansy", "Glow"],
    "pigeon": ["Tumble", "Pearl", "Roundy", "Skiff"],
}


@dataclass
class StoryParams:
    bird: str
    lure: str
    food: str
    guide: str
    watch: str
    hero_name: str
    friend_name: str = "Googoo"
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
    "rust": [
        (
            "What is rust?",
            "Rust is what can happen to iron when water and air stay on it for a long time. It makes the metal turn reddish-brown and flaky."
        )
    ],
    "curb": [
        (
            "What is a curb?",
            "A curb is the raised edge between a street and a sidewalk. Snow often piles there in winter."
        )
    ],
    "grain": [
        (
            "What do little city birds eat in winter?",
            "Many birds eat seeds and grain in winter when bugs are hard to find. They look for safe food near feeders, crumbs, and dry plants."
        )
    ],
    "berry": [
        (
            "Why do some birds look for berries in winter?",
            "Winter berries stay on vines and bushes after many other foods are gone. They give birds a bright, sweet thing to eat in cold weather."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or sees something the wrong way. Then they act on the wrong idea until someone clears it up."
        )
    ],
    "ask_first": [
        (
            "Why is it smart to look carefully before you peck or taste something?",
            "Not every bright thing is food. Looking carefully or asking for help can keep you safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["curb", "rust", "misunderstanding", "grain", "berry", "ask_first"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bird = f["bird_cfg"]
    lure = f["lure_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short myth for a young child about a {bird.label} on a snowy curb who hears "googoo" and nearly pecks {lure.lesson_name}, but is stopped in time.',
            f"Tell a winter myth where a misunderstanding about rust almost tricks a hungry bird, and a wise guide teaches the rule: ask twice, peck once.",
            f'Write a child-facing myth set by a snowy curb with the words "peck", "googoo", and "rust", ending in a calm lesson instead of an injury.',
        ]
    return [
        f'Write a short myth for a young child about a {bird.label} on a snowy curb who misunderstands a red mark and gives it a peck.',
        f'Tell a winter myth with the words "peck", "googoo", and "rust" where a mistaken idea hurts a little at first, then becomes wisdom.',
        f"Write a child-facing myth about misunderstanding appearances in winter: a hungry bird thinks rust is food, learns the truth, and finds real supper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bird = f["bird_cfg"]
    lure = f["lure_cfg"]
    guide_ent = f["guide_ent"]
    food = f["food_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {bird.label}, and {friend.id}, the young pigeon who spoke dreamily beside the snowy curb. A wiser bird, {guide_ent.id}, comes to straighten out the mistake."
        ),
        (
            "What was the misunderstanding?",
            f"{friend.id}'s whisper made {hero.id} think the red mark on the iron might be food. The misunderstanding grew because the rust looked bright and hungry eyes wanted the world to be kind."
        ),
        (
            f"Why did the red mark fool {hero.id}?",
            f"It looked like {lure.myth_word} against the snow, so it seemed possible that the curb had hidden breakfast there. In the white cold, the rust stood out so clearly that it invited a mistake."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Did {hero.id} actually peck the rust?",
                f"No. {guide_ent.id} reached {hero.pronoun('object')} in time and stopped the peck before it landed. That quick warning turned the misunderstanding into a lesson without the sting."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} gave the red mark a peck?",
                f"{hero.pronoun('possessive').capitalize()} beak hurt, because the bright red thing was only rust on old iron. The pain showed at once that the misunderstanding had been about appearance, not real food."
            )
        )
    qa.append(
        (
            f"How was the problem solved?",
            f"{guide_ent.id} explained what rust was and then led the birds to {food.label} at {food.place}. After that, {hero.id} could eat safely and understand the truth at the same time."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a new habit: {hero.id} learned not to peck first and wonder later. The final image proves the change, because the birds now ask and look carefully before choosing what to eat."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"curb", "rust", "misunderstanding", "ask_first", f["bird_cfg"].winter_food}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.edible_kind:
            bits.append(f"edible_kind={e.edible_kind}")
        if e.hard:
            bits.append("hard=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bird="sparrow",
        lure="rust_flakes",
        food="window_seed",
        guide="crow_mother",
        watch="near",
        hero_name="Pip",
        friend_name="Googoo",
    ),
    StoryParams(
        bird="pigeon",
        lure="rust_ring",
        food="bakery_crumbs",
        guide="lamp_gull",
        watch="far",
        hero_name="Tumble",
        friend_name="Googoo",
    ),
    StoryParams(
        bird="robin",
        lure="rust_smear",
        food="winter_berries",
        guide="hedge_wren",
        watch="near",
        hero_name="Glow",
        friend_name="Googoo",
    ),
    StoryParams(
        bird="robin",
        lure="rust_smear",
        food="winter_berries",
        guide="crow_mother",
        watch="far",
        hero_name="Rill",
        friend_name="Googoo",
    ),
]


def explain_rejection(bird: BirdKind, lure: Lure, food: Optional[FoodSource] = None, guide: Optional[Guide] = None) -> str:
    if not lure.misleading:
        return (
            f"(No story: {lure.label} does not honestly look like food, so there is no grounded misunderstanding to drive the myth.)"
        )
    if bird.winter_food != lure.appeal:
        return (
            f"(No story: a {bird.label} in this world looks for {bird.winter_food}, but {lure.label} resembles {lure.appeal}. "
            f"The misunderstanding would not feel natural.)"
        )
    if food is not None and food.food_kind != bird.winter_food:
        return (
            f"(No story: {food.label} is the wrong kind of food for this {bird.label}. The ending must solve hunger with a fitting meal.)"
        )
    if guide is not None and bird.winter_food not in guide.knows:
        return (
            f"(No story: {guide.label} does not know where this kind of winter food is found, so the misunderstanding has no reliable guide to resolve it.)"
        )
    return "(No story: this combination does not form a reasonable misunderstanding with a credible fix.)"


ASP_RULES = r"""
% validity
misunderstanding(B,L) :- bird(B), lure(L), misleading(L), winter_food(B,K), appeal(L,K).
fixable(B,F,G) :- bird(B), food(F), guide(G), winter_food(B,K), food_kind(F,K), knows(G,K).
valid(B,L,F,G) :- misunderstanding(B,L), fixable(B,F,G).

% outcome
quick_guide :- watch(near), chosen_guide(G), chosen_lure(L), speed(G,S), risk(L,R), S >= R.
outcome(averted) :- quick_guide.
outcome(sore_then_feast) :- not quick_guide.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bird_id, bird in BIRDS.items():
        lines.append(asp.fact("bird", bird_id))
        lines.append(asp.fact("winter_food", bird_id, bird.winter_food))
    for lure_id, lure in LURES.items():
        lines.append(asp.fact("lure", lure_id))
        lines.append(asp.fact("appeal", lure_id, lure.appeal))
        lines.append(asp.fact("risk", lure_id, lure.risk))
        if lure.misleading:
            lines.append(asp.fact("misleading", lure_id))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("food_kind", food_id, food.food_kind))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        lines.append(asp.fact("speed", guide_id, guide.speed))
        for kind in sorted(guide.knows):
            lines.append(asp.fact("knows", guide_id, kind))
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
            asp.fact("chosen_guide", params.guide),
            asp.fact("chosen_lure", params.lure),
            asp.fact("watch", params.watch),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    guide = GUIDES[params.guide]
    lure = LURES[params.lure]
    return "averted" if can_avert(guide, params.watch, lure) else "sore_then_feast"


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
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        sample_json = smoke.to_json()
        if '"story"' not in sample_json:
            raise StoryError("smoke test JSON serialization failed")
        print("OK: smoke test generate()/to_json() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a winter myth of misunderstanding on a snowy curb."
    )
    ap.add_argument("--bird", choices=sorted(BIRDS))
    ap.add_argument("--lure", choices=sorted(LURES))
    ap.add_argument("--food", choices=sorted(FOODS))
    ap.add_argument("--guide", choices=sorted(GUIDES))
    ap.add_argument("--watch", choices=["near", "far"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name", default="Googoo")
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
    if args.bird and args.lure:
        bird = BIRDS[args.bird]
        lure = LURES[args.lure]
        if not misunderstanding_possible(bird, lure):
            raise StoryError(explain_rejection(bird, lure))
    if args.bird and args.food:
        bird = BIRDS[args.bird]
        food = FOODS[args.food]
        if food.food_kind != bird.winter_food:
            lure = LURES[args.lure] if args.lure else next(iter(LURES.values()))
            raise StoryError(explain_rejection(bird, lure, food=food))
    if args.bird and args.guide:
        bird = BIRDS[args.bird]
        guide = GUIDES[args.guide]
        lure = LURES[args.lure] if args.lure else next(iter(LURES.values()))
        if bird.winter_food not in guide.knows:
            raise StoryError(explain_rejection(bird, lure, guide=guide))

    combos = [
        c
        for c in valid_combos()
        if (args.bird is None or c[0] == args.bird)
        and (args.lure is None or c[1] == args.lure)
        and (args.food is None or c[2] == args.food)
        and (args.guide is None or c[3] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bird_id, lure_id, food_id, guide_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES[bird_id])
    friend_name = args.friend_name or "Googoo"
    watch = args.watch or rng.choice(["near", "far"])

    return StoryParams(
        bird=bird_id,
        lure=lure_id,
        food=food_id,
        guide=guide_id,
        watch=watch,
        hero_name=hero_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [name for name, table in [("bird", BIRDS), ("lure", LURES), ("food", FOODS), ("guide", GUIDES)] if getattr(params, name) not in table]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")

    bird = BIRDS[params.bird]
    lure = LURES[params.lure]
    food = FOODS[params.food]
    guide = GUIDES[params.guide]

    if not misunderstanding_possible(bird, lure):
        raise StoryError(explain_rejection(bird, lure))
    if not guiding_fix_exists(bird, food, guide):
        raise StoryError(explain_rejection(bird, lure, food=food, guide=guide))
    if params.watch not in {"near", "far"}:
        raise StoryError("(Invalid params: watch must be 'near' or 'far'.)")

    world = tell(
        bird=bird,
        lure=lure,
        food=food,
        guide=guide,
        watch=params.watch,
        hero_name=params.hero_name,
        friend_name=params.friend_name,
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
        print(f"{len(combos)} compatible (bird, lure, food, guide) combos:\n")
        for bird, lure, food, guide in combos:
            print(f"  {bird:8} {lure:12} {food:14} {guide}")
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
            header = f"### {p.hero_name}: {p.bird}, {p.lure}, {p.watch} guide"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
