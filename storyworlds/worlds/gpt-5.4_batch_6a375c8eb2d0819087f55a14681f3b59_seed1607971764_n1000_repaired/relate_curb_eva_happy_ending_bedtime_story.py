#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py
========================================================================

A small bedtime-story world about Eva finding a frightened little animal near a
curb and helping it reach a safe sleeping place. The world enforces a simple
common-sense constraint: the comfort or guiding method must actually suit the
animal, or there is no honest story to tell.

Run it
------
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py --animal kitten --helper ribbon
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py --animal hedgehog --helper ribbon
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/relate_curb_eva_happy_ending_bedtime_story.py --json
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
from contextlib import redirect_stdout
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Lane:
    id: str
    label: str
    night_sound: str
    glow: str
    ending_image: str
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
    move: str
    fear_image: str
    sleep_name: str
    home_phrase: str
    likes: set[str] = field(default_factory=set)
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
class HelperCfg:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    calming: int
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
class HomeCfg:
    id: str
    label: str
    phrase: str
    belongs_to: str
    warmth: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_curb_danger(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    street = world.get("street")
    if animal.attrs.get("place") == "curb" and street.meters["passing_noise"] >= THRESHOLD:
        sig = ("curb_danger", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.memes["fear"] += 1
            animal.meters["risk"] += 1
            out.append("__danger__")
    return out


def _r_empathy(world: World) -> list[str]:
    out: list[str] = []
    eva = world.get("Eva")
    animal = world.get("animal")
    if eva.memes["relating"] >= THRESHOLD and animal.memes["fear"] >= THRESHOLD:
        sig = ("empathy", eva.id, animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            eva.memes["care"] += 1
            out.append("__empathy__")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    eva = world.get("Eva")
    animal = world.get("animal")
    helper = world.get("helper")
    if eva.attrs.get("moving_slowly") and helper.attrs.get("fits_animal") and eva.memes["care"] >= THRESHOLD:
        sig = ("trust", helper.id, animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.memes["trust"] += float(helper.attrs.get("calming", 1))
            out.append("__trust__")
    return out


def _r_follow_home(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    home = world.get("home")
    if animal.memes["trust"] >= THRESHOLD and home.attrs.get("fits_animal"):
        sig = ("follow_home", animal.id, home.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.attrs["place"] = "home"
            animal.meters["risk"] = 0.0
            animal.memes["fear"] = 0.0
            animal.memes["relief"] += 1
            out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule(name="curb_danger", tag="physical", apply=_r_curb_danger),
    Rule(name="empathy", tag="social", apply=_r_empathy),
    Rule(name="trust", tag="social", apply=_r_trust),
    Rule(name="follow_home", tag="physical", apply=_r_follow_home),
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


def helper_fits(animal: AnimalCfg, helper: HelperCfg) -> bool:
    return helper.id in animal.likes


def home_fits(animal: AnimalCfg, home: HomeCfg) -> bool:
    return animal.id == home.belongs_to


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lane_id in LANES:
        for animal_id, animal in ANIMALS.items():
            for helper_id, helper in HELPERS.items():
                for home_id, home in HOMES.items():
                    if helper_fits(animal, helper) and home_fits(animal, home):
                        combos.append((lane_id, animal_id, helper_id, home_id))
    return combos


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    eva = sim.get("Eva")
    eva.attrs["moving_slowly"] = True
    eva.memes["relating"] += 1
    propagate(sim, narrate=False)
    return {
        "safe": sim.get("animal").attrs.get("place") == "home",
        "fear": sim.get("animal").memes["fear"],
        "trust": sim.get("animal").memes["trust"],
    }


def scene_open(world: World, lane: Lane, eva: Entity, parent: Entity) -> None:
    eva.memes["sleepy"] += 1
    world.say(
        f"It was almost bedtime when Eva walked home with her {parent.label_word} along {lane.label}. "
        f"{lane.glow}, and the houses were beginning to yawn into quiet."
    )


def hear_small_sound(world: World, lane: Lane, animal_cfg: AnimalCfg) -> None:
    world.say(
        f"Then Eva heard a tiny sound near the curb. There, in the dim light, was {animal_cfg.fear_image}."
    )
    world.say(
        f"A wheel hummed somewhere down the lane, and that made the little {animal_cfg.label} seem even smaller."
    )


def relate_beat(world: World, eva: Entity, animal_cfg: AnimalCfg) -> None:
    eva.memes["relating"] += 1
    world.say(
        f'Eva stopped at once. "I can relate," she whispered. "Sometimes loud evening sounds make me want to tuck myself in too."'
    )


def quick_reach_mistake(world: World, eva: Entity, animal: Entity, parent: Entity) -> None:
    eva.memes["hurry"] += 1
    animal.memes["fear"] += 1
    animal.meters["risk"] += 1
    world.say(
        f"At first Eva took one quick step forward, but the little {animal.label} {animal.attrs['flinch_verb']} and edged closer to the curb."
    )
    world.say(
        f'"Slow hands," said her {parent.label_word} softly. "Scared little ones listen better when the world grows gentle."'
    )


def choose_gentle_way(world: World, eva: Entity, helper_cfg: HelperCfg, animal_cfg: AnimalCfg, home_cfg: HomeCfg) -> None:
    helper = world.get("helper")
    home = world.get("home")
    helper.attrs["fits_animal"] = helper_fits(animal_cfg, helper_cfg)
    helper.attrs["calming"] = helper_cfg.calming
    home.attrs["fits_animal"] = home_fits(animal_cfg, home_cfg)
    eva.attrs["moving_slowly"] = True
    world.say(
        f"So Eva bent her knees, made herself small, and used {helper_cfg.phrase}. She {helper_cfg.action}."
    )


def safe_arrival(world: World, lane: Lane, animal_cfg: AnimalCfg, helper_cfg: HelperCfg, home_cfg: HomeCfg) -> None:
    world.say(
        f"Soon the little {animal_cfg.label} {animal_cfg.move} away from the curb and toward {home_cfg.phrase}. {helper_cfg.result}"
    )
    world.say(
        f"It slipped into {animal_cfg.sleep_name}, where {home_cfg.warmth}."
    )
    world.say(
        f"Eva and her parent stood still for one happy breath, and then they walked on under the moon. {lane.ending_image}."
    )


def bedtime_close(world: World, eva: Entity, parent: Entity, animal_cfg: AnimalCfg) -> None:
    eva.memes["relief"] += 1
    eva.memes["joy"] += 1
    eva.memes["care"] += 1
    world.say(
        f'That night, tucked under her blanket, Eva smiled and thought about the little {animal_cfg.label} sleeping safely. '
        f'"I am glad we were gentle," she murmured.'
    )
    world.say(
        f'Her {parent.label_word} kissed her forehead. "Gentle hearts help the world rest too," {parent.pronoun()} said.'
    )


def tell(
    lane: Lane,
    animal_cfg: AnimalCfg,
    helper_cfg: HelperCfg,
    home_cfg: HomeCfg,
    parent_type: str = "mother",
) -> World:
    world = World()
    eva = world.add(Entity(id="Eva", kind="character", type="girl", role="helper", label="Eva"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    street = world.add(Entity(id="street", kind="thing", type="street", label="the lane"))
    animal = world.add(
        Entity(
            id="animal",
            kind="thing",
            type=animal_cfg.id,
            label=animal_cfg.label,
            role="lost_one",
            attrs={"place": "curb", "flinch_verb": animal_cfg.move},
            tags=set(animal_cfg.tags),
        )
    )
    helper = world.add(Entity(id="helper", kind="thing", type="helper", label=helper_cfg.label))
    home = world.add(Entity(id="home", kind="thing", type="home", label=home_cfg.label))

    street.meters["passing_noise"] = 1.0
    eva.attrs["moving_slowly"] = False
    helper.attrs["fits_animal"] = False
    helper.attrs["calming"] = 0
    home.attrs["fits_animal"] = False
    animal.meters["risk"] = 0.0
    animal.memes["fear"] = 0.0
    animal.memes["trust"] = 0.0
    animal.memes["relief"] = 0.0
    eva.memes["relating"] = 0.0
    eva.memes["care"] = 0.0

    scene_open(world, lane, eva, parent)
    hear_small_sound(world, lane, animal_cfg)
    propagate(world, narrate=False)

    world.para()
    relate_beat(world, eva, animal_cfg)
    propagate(world, narrate=False)
    quick_reach_mistake(world, eva, animal, parent)

    world.para()
    choose_gentle_way(world, eva, helper_cfg, animal_cfg, home_cfg)
    propagate(world, narrate=False)

    if animal.attrs.get("place") != "home":
        raise StoryError(
            f"(No story: {helper_cfg.label} would not honestly calm a {animal_cfg.label} into {home_cfg.label}.)"
        )

    safe_arrival(world, lane, animal_cfg, helper_cfg, home_cfg)
    world.para()
    bedtime_close(world, eva, parent, animal_cfg)

    world.facts.update(
        lane=lane,
        animal_cfg=animal_cfg,
        helper_cfg=helper_cfg,
        home_cfg=home_cfg,
        eva=eva,
        parent=parent,
        animal=animal,
        helper=helper,
        home=home,
        outcome="safe_home",
        related=eva.memes["relating"] >= THRESHOLD,
        animal_safe=animal.attrs.get("place") == "home",
        risk_start=1,
        fear_start=1,
    )
    return world


LANES = {
    "lantern_lane": Lane(
        id="lantern_lane",
        label="Lantern Lane",
        night_sound="a bicycle bell far away",
        glow="Porch lamps made little golden puddles on the path",
        ending_image="By the last gate, the moon looked round and sleepy above the chimneys",
        tags={"street", "bedtime"},
    ),
    "garden_walk": Lane(
        id="garden_walk",
        label="the garden walk",
        night_sound="soft leaves brushing the fence",
        glow="The moon laid silver stripes across the stones",
        ending_image="At the corner, the hedges looked like soft dark pillows",
        tags={"night", "garden"},
    ),
    "willow_row": Lane(
        id="willow_row",
        label="Willow Row",
        night_sound="a late cart rolling home",
        glow="Window-light shone in warm squares on the ground",
        ending_image="The stars peeped out one by one as if the sky were settling into bed",
        tags={"night", "street"},
    ),
}

ANIMALS = {
    "kitten": AnimalCfg(
        id="kitten",
        label="kitten",
        move="padded",
        fear_image="a gray kitten with its tail tucked tight around its paws",
        sleep_name="the porch basket",
        home_phrase="the baker's porch basket",
        likes={"ribbon", "soft_call"},
        tags={"kitten", "pet"},
    ),
    "hedgehog": AnimalCfg(
        id="hedgehog",
        label="hedgehog",
        move="snuffled",
        fear_image="a round hedgehog curled like a prickly pinecone",
        sleep_name="the hedge nook",
        home_phrase="the hedge nook under the rosebush",
        likes={"leaf_trail", "soft_hum"},
        tags={"hedgehog", "garden"},
    ),
    "duckling": AnimalCfg(
        id="duckling",
        label="duckling",
        move="waddled",
        fear_image="a duckling with one damp foot lifted off the stone",
        sleep_name="the reed nest",
        home_phrase="the reed nest beside the pond gate",
        likes={"soft_hum", "crumb_path"},
        tags={"duckling", "pond"},
    ),
}

HELPERS = {
    "ribbon": HelperCfg(
        id="ribbon",
        label="a ribbon wand",
        phrase="a ribbon from her coat pocket",
        action="let the ribbon sway in a small sleepy loop",
        result="The tiny swish gave it something safe to follow",
        calming=1,
        tags={"ribbon", "gentle"},
    ),
    "soft_call": HelperCfg(
        id="soft_call",
        label="a soft call",
        phrase="the quietest little call she could make",
        action='said, "here, little one," as if she were singing to a pillow',
        result="The sound made the dark feel less lonely",
        calming=1,
        tags={"voice", "gentle"},
    ),
    "leaf_trail": HelperCfg(
        id="leaf_trail",
        label="a leaf trail",
        phrase="a tiny trail of dry leaves",
        action="set the leaves down one by one toward the garden wall",
        result="The rustly path felt friendly instead of frightening",
        calming=1,
        tags={"leaves", "gentle"},
    ),
    "soft_hum": HelperCfg(
        id="soft_hum",
        label="a soft hum",
        phrase="a low evening hum",
        action="hummed so quietly that it almost sounded like the night itself",
        result="The steady sound gave the little creature courage",
        calming=1,
        tags={"hum", "bedtime"},
    ),
    "crumb_path": HelperCfg(
        id="crumb_path",
        label="a crumb path",
        phrase="a few bread crumbs from her pocket",
        action="laid the crumbs in a careful line away from the stone edge",
        result="The crumbs made a safe path to follow",
        calming=1,
        tags={"crumbs", "food"},
    ),
}

HOMES = {
    "porch_basket": HomeCfg(
        id="porch_basket",
        label="porch basket",
        phrase="the baker's porch basket",
        belongs_to="kitten",
        warmth="the old blanket there looked warm as toast",
        tags={"basket", "home"},
    ),
    "hedge_nook": HomeCfg(
        id="hedge_nook",
        label="hedge nook",
        phrase="the hedge nook under the rosebush",
        belongs_to="hedgehog",
        warmth="the leaves made a snug brown roof",
        tags={"hedge", "home"},
    ),
    "reed_nest": HomeCfg(
        id="reed_nest",
        label="reed nest",
        phrase="the reed nest beside the pond gate",
        belongs_to="duckling",
        warmth="the reeds rocked in a hush-hush whisper",
        tags={"pond", "home"},
    ),
}

PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    lane: str
    animal: str
    helper: str
    home: str
    parent: str
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
    "curb": [
        (
            "What is a curb?",
            "A curb is the raised edge between a sidewalk and the street. It helps show where walking should stop and the road begins.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten be scared near a street?",
            "A kitten is small, and street sounds can feel very loud and confusing. If it gets frightened, it may not know where to run safely.",
        )
    ],
    "hedgehog": [
        (
            "Where do hedgehogs like to hide?",
            "Hedgehogs like snug, quiet places such as leaf piles, hedges, and little garden corners. Those places help them feel safe while they rest.",
        )
    ],
    "duckling": [
        (
            "Why does a duckling need a calm path home?",
            "A duckling is small and can be startled by noise and movement. A calm path helps it keep going toward safety instead of freezing in fear.",
        )
    ],
    "gentle": [
        (
            "Why can being gentle help a frightened animal?",
            "Gentle movements and soft sounds make the world feel less scary. When fear goes down, trust can begin to grow.",
        )
    ],
    "bedtime": [
        (
            "Why do bedtime stories often end quietly?",
            "A quiet ending helps your mind slow down and feel safe. It leaves one warm picture to carry into sleep.",
        )
    ],
}
KNOWLEDGE_ORDER = ["curb", "kitten", "hedgehog", "duckling", "gentle", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lane = f["lane"]
    animal = f["animal_cfg"]
    helper = f["helper_cfg"]
    home = f["home_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "relate", "curb", and "Eva", and ends happily.',
        f"Tell a gentle night story where Eva finds a frightened {animal.label} near a curb on {lane.label} and helps it back to {home.label}.",
        f"Write a soothing story in which Eva can relate to a scared little animal, uses {helper.label}, and ends with everyone safe and sleepy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal_cfg"]
    helper = f["helper_cfg"]
    home = f["home_cfg"]
    lane = f["lane"]
    parent = f["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Eva, her {parent.label_word}, and a frightened little {animal.label}. The story follows how Eva notices danger and chooses to help gently.",
        ),
        (
            "Where did Eva find the little animal?",
            f"Eva found the {animal.label} near the curb on {lane.label}. That was worrying because the edge of the street felt noisy and unsafe.",
        ),
        (
            "Why did Eva say she could relate?",
            f"Eva said she could relate because loud evening sounds sometimes made her want to tuck herself in too. That feeling helped her understand why the little {animal.label} was scared.",
        ),
        (
            "What mistake did Eva make first?",
            f"At first Eva stepped forward too quickly, and the little {animal.label} moved even closer to the curb. That showed her that hurry made the fear bigger instead of smaller.",
        ),
        (
            "How did Eva help in the end?",
            f"Eva slowed down and used {helper.label} to guide the little {animal.label}. Because she became gentle and patient, the frightened animal trusted her enough to move toward {home.phrase}.",
        ),
        (
            "How did the story end?",
            f"The little {animal.label} reached {home.phrase} and settled into its sleeping place. Later Eva went to bed smiling, which shows that both the child and the little creature ended the night safe and calm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal_cfg"]
    tags = {"curb", "gentle", "bedtime"}
    if animal.id in {"kitten", "hedgehog", "duckling"}:
        tags.add(animal.id)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lane="lantern_lane",
        animal="kitten",
        helper="ribbon",
        home="porch_basket",
        parent="mother",
    ),
    StoryParams(
        lane="garden_walk",
        animal="hedgehog",
        helper="leaf_trail",
        home="hedge_nook",
        parent="father",
    ),
    StoryParams(
        lane="willow_row",
        animal="duckling",
        helper="soft_hum",
        home="reed_nest",
        parent="mother",
    ),
    StoryParams(
        lane="lantern_lane",
        animal="kitten",
        helper="soft_call",
        home="porch_basket",
        parent="father",
    ),
    StoryParams(
        lane="garden_walk",
        animal="duckling",
        helper="crumb_path",
        home="reed_nest",
        parent="mother",
    ),
]


def explain_rejection(animal: AnimalCfg, helper: HelperCfg, home: HomeCfg) -> str:
    if not helper_fits(animal, helper):
        likes = ", ".join(sorted(animal.likes))
        return (
            f"(No story: {helper.label} is not a sensible way to calm a {animal.label} here. "
            f"Try one of the fitting helpers: {likes}.)"
        )
    if not home_fits(animal, home):
        return (
            f"(No story: {home.label} is not the right safe sleeping place for a {animal.label}. "
            f"The ending should guide it to its own kind of home.)"
        )
    return "(No story: this combination does not make a reasonable rescue.)"


ASP_RULES = r"""
fits_helper(A,H) :- likes(A,H).
fits_home(A,Ho)  :- belongs_to(Ho,A).
valid(L,A,H,Ho)  :- lane(L), animal(A), helper(H), home(Ho), fits_helper(A,H), fits_home(A,Ho).

safe(A,H,Ho)     :- fits_helper(A,H), fits_home(A,Ho).
outcome(safe_home) :- chosen_animal(A), chosen_helper(H), chosen_home(Ho), safe(A,H,Ho).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lane_id in LANES:
        lines.append(asp.fact("lane", lane_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for helper_id in sorted(animal.likes):
            lines.append(asp.fact("likes", animal_id, helper_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        lines.append(asp.fact("belongs_to", home_id, home.belongs_to))
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
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_home", params.home),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {seed}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != "safe_home")
    if bad == 0:
        print(f"OK: ASP outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: Eva helps a frightened little animal away from a curb and into a safe sleeping place."
    )
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.helper and args.home:
        animal = ANIMALS[args.animal]
        helper = HELPERS[args.helper]
        home = HOMES[args.home]
        if not (helper_fits(animal, helper) and home_fits(animal, home)):
            raise StoryError(explain_rejection(animal, helper, home))

    combos = [
        combo
        for combo in valid_combos()
        if (args.lane is None or combo[0] == args.lane)
        and (args.animal is None or combo[1] == args.animal)
        and (args.helper is None or combo[2] == args.helper)
        and (args.home is None or combo[3] == args.home)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lane_id, animal_id, helper_id, home_id = rng.choice(sorted(combos))
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(
        lane=lane_id,
        animal=animal_id,
        helper=helper_id,
        home=home_id,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lane not in LANES:
        raise StoryError(f"(Unknown lane: {params.lane})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.home not in HOMES:
        raise StoryError(f"(Unknown home: {params.home})")
    if params.parent not in PARENT_TYPES:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    lane = LANES[params.lane]
    animal = ANIMALS[params.animal]
    helper = HELPERS[params.helper]
    home = HOMES[params.home]
    if not (helper_fits(animal, helper) and home_fits(animal, home)):
        raise StoryError(explain_rejection(animal, helper, home))

    world = tell(
        lane=lane,
        animal_cfg=animal,
        helper_cfg=helper,
        home_cfg=home,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (lane, animal, helper, home) combos:\n")
        for lane, animal, helper, home in combos:
            print(f"  {lane:13} {animal:9} {helper:10} {home}")
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
            header = f"### Eva helps a {p.animal} with {p.helper} on {p.lane}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
