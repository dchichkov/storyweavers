#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/susceptible_moor_shoe_pl_dim_inner_monologue.py
===========================================================================

A standalone storyworld for a small animal tale on a moor.

Seed constraints:
- include the words "susceptible", "moor", and "shoe-pl-dim"
- include inner monologue
- use a bad ending
- keep the style close to a simple animal story

World premise
-------------
A young animal is sent across the moor with a small parcel and told to stay on
the stone path. The child is susceptible to a tempting sight beside the path.
When the ground is soft enough and the chosen shoes are poor enough, stepping
off the path leads to mud, fear, and a bad ending: the parcel is ruined or
lost, and the child comes home sad.

The world enforces a reasonableness gate:
- the lure must be off the path, or there is no honest reason to leave safety
- the weather must make the moor soft enough to be dangerous
- the shoes must be poor enough for the bog to win

Run it
------
python storyworlds/worlds/gpt-5.4/susceptible_moor_shoe_pl_dim_inner_monologue.py
python storyworlds/worlds/gpt-5.4/susceptible_moor_shoe_pl_dim_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/susceptible_moor_shoe_pl_dim_inner_monologue.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/susceptible_moor_shoe_pl_dim_inner_monologue.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe", "ewe"}
        male = {"boy", "father", "buck", "ram"}
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
class AnimalKind:
    id: str
    child_word: str
    adult_word: str
    home: str
    likes: str
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
    ground: str
    softness: int
    scene: str
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
    sight: str
    desire: str
    thought: str
    off_path: bool
    pull: int
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
class Shoes:
    id: str
    label: str
    phrase: str
    grip: int
    soak: int
    plural: bool = True
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
class Parcel:
    id: str
    label: str
    phrase: str
    recipient: str
    comfort: str
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
    animal: str
    weather: str
    lure: str
    shoes: str
    parcel: str
    name: str
    gender: str
    elder_gender: str
    trait: str
    seed: Optional[int] = None
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


def _r_sink(world: World) -> list[str]:
    hero = world.get("hero")
    shoes = world.get("shoes")
    bog = world.get("bog")
    if hero.meters["off_path"] < THRESHOLD:
        return []
    if bog.meters["softness"] <= shoes.meters["grip"]:
        return []
    sig = ("sink",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["stuck"] += 1
    shoes.meters["muddy"] += 1
    if shoes.meters["soak"] > 0:
        hero.meters["cold"] += 1
    hero.memes["fear"] += 1
    return ["__sink__"]


def _r_parcel_ruin(world: World) -> list[str]:
    hero = world.get("hero")
    parcel = world.get("parcel")
    bog = world.get("bog")
    if hero.meters["stuck"] < THRESHOLD:
        return []
    sig = ("parcel_ruin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["wet"] += 1
    hero.memes["shame"] += 1
    if bog.meters["softness"] >= 3:
        parcel.meters["lost"] += 1
    return ["__parcel__"]


def _r_shoe_loss(world: World) -> list[str]:
    hero = world.get("hero")
    shoes = world.get("shoes")
    bog = world.get("bog")
    if hero.meters["stuck"] < THRESHOLD:
        return []
    if bog.meters["softness"] - shoes.meters["grip"] < 2:
        return []
    sig = ("shoe_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shoes.meters["lost"] += 1
    hero.memes["grief"] += 1
    return ["__shoe_loss__"]


CAUSAL_RULES = [
    Rule(name="sink", tag="physical", apply=_r_sink),
    Rule(name="parcel_ruin", tag="physical", apply=_r_parcel_ruin),
    Rule(name="shoe_loss", tag="physical", apply=_r_shoe_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for bit in produced:
            world.say(bit)
    return produced


ANIMALS = {
    "hare": AnimalKind(
        id="hare",
        child_word="hare",
        adult_word="mother hare",
        home="a heather burrow",
        likes="running where the wind made the grass bow",
        tags={"hare", "moor"},
    ),
    "lamb": AnimalKind(
        id="lamb",
        child_word="lamb",
        adult_word="mother ewe",
        home="a stone fold",
        likes="trotting beside the low walls",
        tags={"lamb", "moor"},
    ),
    "fox": AnimalKind(
        id="fox",
        child_word="fox cub",
        adult_word="mother fox",
        home="a warm den under roots",
        likes="sniffing out every secret smell",
        tags={"fox", "moor"},
    ),
}

WEATHERS = {
    "mist": Weather(
        id="mist",
        sky="a low pearl-gray mist",
        ground="spongy",
        softness=2,
        scene="beads of mist sat on every stem of heather",
        tags={"mist", "bog"},
    ),
    "drizzle": Weather(
        id="drizzle",
        sky="thin drizzle and a silver sky",
        ground="soft",
        softness=2,
        scene="small drops kept knitting the dark soil together",
        tags={"rain", "bog"},
    ),
    "rain": Weather(
        id="rain",
        sky="steady rain and a bent, dark sky",
        ground="sucking",
        softness=3,
        scene="water shivered in the hollows of the moor",
        tags={"rain", "bog"},
    ),
    "breeze": Weather(
        id="breeze",
        sky="a clear sky with a cool breeze",
        ground="firm",
        softness=0,
        scene="the heather nodded, but the ground held fast",
        tags={"wind"},
    ),
}

LURES = {
    "feather": Lure(
        id="feather",
        label="a silver feather",
        sight="a silver feather rocked in the heather beside the path",
        desire="It looked as if it had fallen from the moon.",
        thought="If I only hop there and back, nobody will even know.",
        off_path=True,
        pull=1,
        tags={"feather", "temptation"},
    ),
    "berries": Lure(
        id="berries",
        label="a clump of dark berries",
        sight="a clump of dark berries shone where the stones ended",
        desire="They looked plump enough to stain the tongue purple.",
        thought="I can pick just one handful and still be quick.",
        off_path=True,
        pull=2,
        tags={"berries", "temptation"},
    ),
    "bell": Lure(
        id="bell",
        label="a lost brass bell",
        sight="a lost brass bell winked in a patch of moss",
        desire="It gave a tiny bright gleam whenever the light touched it.",
        thought="If I bring it home too, Mother will see I was helpful.",
        off_path=True,
        pull=1,
        tags={"bell", "temptation"},
    ),
    "path_shell": Lure(
        id="path_shell",
        label="a striped shell",
        sight="a striped shell sat right on the stone path",
        desire="It was pretty, but it was already in the safe place.",
        thought="I do not even need to step away for that.",
        off_path=False,
        pull=0,
        tags={"shell"},
    ),
}

SHOES = {
    "shoe-pl-dim": Shoes(
        id="shoe-pl-dim",
        label="shoe-pl-dim shoes",
        phrase="soft shoe-pl-dim shoes with thin soles",
        grip=0,
        soak=2,
        plural=True,
        tags={"shoes", "bog"},
    ),
    "button_shoes": Shoes(
        id="button_shoes",
        label="button shoes",
        phrase="brown button shoes polished that morning",
        grip=1,
        soak=1,
        plural=True,
        tags={"shoes"},
    ),
    "reed_slippers": Shoes(
        id="reed_slippers",
        label="reed slippers",
        phrase="light reed slippers that were lovely indoors",
        grip=0,
        soak=2,
        plural=True,
        tags={"slippers", "bog"},
    ),
    "marsh_boots": Shoes(
        id="marsh_boots",
        label="marsh boots",
        phrase="snug marsh boots laced up to the ankles",
        grip=3,
        soak=0,
        plural=True,
        tags={"boots", "bog"},
    ),
}

PARCELS = {
    "cake": Parcel(
        id="cake",
        label="honey cake",
        phrase="a wrapped honey cake",
        recipient="Grand-Aunt Bracken",
        comfort="for tea by the lamp",
        tags={"cake", "gift"},
    ),
    "soup": Parcel(
        id="soup",
        label="a jar of nettle soup",
        phrase="a jar of nettle soup",
        recipient="Old Mossy",
        comfort="for supper before dark",
        tags={"soup", "gift"},
    ),
    "thread": Parcel(
        id="thread",
        label="blue sewing thread",
        phrase="a spool of blue sewing thread",
        recipient="Aunt Fern",
        comfort="for mending before evening",
        tags={"thread", "gift"},
    ),
}

GIRL_NAMES = ["Mira", "Poppy", "Tansy", "Bria", "Nell", "Juniper"]
BOY_NAMES = ["Bram", "Pip", "Rowan", "Tobin", "Moss", "Ash"]
TRAITS = ["dreamy", "eager", "curious", "restless", "gentle", "quick-hearted"]


def bog_risk(weather: Weather, shoes: Shoes, lure: Lure) -> bool:
    return lure.off_path and weather.softness > shoes.grip


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for animal_id in ANIMALS:
        for weather_id, weather in WEATHERS.items():
            for lure_id, lure in LURES.items():
                for shoes_id, shoes in SHOES.items():
                    if bog_risk(weather, shoes, lure):
                        combos.append((animal_id, weather_id, lure_id, shoes_id))
    return combos


def loss_level(weather: Weather, shoes: Shoes) -> str:
    gap = weather.softness - shoes.grip
    return "lost" if gap >= 2 else "ruined"


def explain_rejection(weather: Weather, lure: Lure, shoes: Shoes) -> str:
    if not lure.off_path:
        return (
            f"(No story: {lure.label} is already on the safe stones, so the child has "
            f"no honest reason to step off the path.)"
        )
    if weather.softness <= 0:
        return (
            f"(No story: in {weather.id}, the moor is firm, so stepping off the stones "
            f"would not make a believable bog accident.)"
        )
    if weather.softness <= shoes.grip:
        return (
            f"(No story: {shoes.label} are sturdy enough for this weather, so the bog "
            f"would not win. Pick softer shoes or wetter weather.)"
        )
    return "(No story: this combination has no believable bog danger.)"


def predict_bog(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["off_path"] += 1
    propagate(sim, narrate=False)
    return {
        "stuck": sim.get("hero").meters["stuck"] >= THRESHOLD,
        "parcel_lost": sim.get("parcel").meters["lost"] >= THRESHOLD,
        "shoe_lost": sim.get("shoes").meters["lost"] >= THRESHOLD,
        "parcel_wet": sim.get("parcel").meters["wet"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, animal: AnimalKind, shoes: Shoes, parcel: Parcel) -> None:
    hero.memes["susceptible"] = 1.0
    hero.memes["love_home"] = 1.0
    world.say(
        f"{hero.id} was a little {animal.child_word} who lived in {animal.home}. "
        f"{hero.pronoun().capitalize()} loved {animal.likes}."
    )
    world.say(
        f"That afternoon, {elder.label} tied up {parcel.phrase} and asked "
        f"{hero.pronoun('object')} to carry it across the moor to {parcel.recipient}, "
        f"{parcel.comfort}."
    )
    world.say(
        f"{hero.id} set out in {shoes.phrase}. The old stones made a pale line through "
        f"the heather."
    )


def warning(world: World, hero: Entity, elder: Entity, weather: Weather) -> None:
    world.say(
        f'The sky wore {weather.sky}, and {weather.scene}. "{hero.id}," said {elder.label}, '
        f'"keep to the stones. The moor is {weather.ground} today, and soft places do not let go quickly."'
    )


def journey(world: World, hero: Entity, lure: Lure) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"{hero.id} walked carefully at first, balancing the parcel between careful paws. "
        f"Then {lure.sight} {lure.desire}"
    )


def inner_monologue(world: World, hero: Entity, lure: Lure) -> None:
    hero.memes["tempted"] += 1
    susceptible = hero.memes["susceptible"] >= THRESHOLD
    if susceptible:
        world.say(
            f'{hero.id} slowed. "{lure.thought}" {hero.pronoun()} thought. '
            f'{hero.pronoun().capitalize()} was susceptible to bright little chances, '
            f'and the thought felt warm and clever for one breath.'
        )
    else:
        world.say(
            f'"{lure.thought}" {hero.pronoun()} thought.'
        )


def step_off(world: World, hero: Entity, weather: Weather) -> None:
    hero.meters["off_path"] += 1
    world.say(
        f"So {hero.id} stepped off the last white stone. Beside the path, the ground looked "
        f"shoe-pl-dim and harmless, as if even mud could pretend to be mild."
    )
    propagate(world, narrate=False)


def sink_scene(world: World, hero: Entity, shoes: Entity, parcel: Entity) -> None:
    if hero.meters["stuck"] < THRESHOLD:
        return
    hero.memes["regret"] += 1
    world.say(
        f"At once the heather crust broke. One small foot went down, then the other, and the mud "
        f"held on to {shoes.label} with a hungry slurp."
    )
    if shoes.meters["lost"] >= THRESHOLD:
        world.say(
            f"{hero.id} kicked and pulled, but one shoe stayed behind in the black water. "
            f"The other came up streaked and heavy."
        )
    else:
        world.say(
            f"{hero.id} tugged hard and got free at last, but the shoes came up thick with mud and cold water."
        )
    if parcel.meters["lost"] >= THRESHOLD:
        world.say(
            f"The parcel slipped from {hero.pronoun('possessive')} paws and vanished into the bog with hardly a ripple."
        )
    elif parcel.meters["wet"] >= THRESHOLD:
        world.say(
            f"The parcel banged against the mud and drank in the wet. Whatever was inside was spoiled before "
            f"{hero.pronoun()} could grab it back."
        )


def trudge_home(world: World, hero: Entity, elder: Entity, parcel_cfg: Parcel) -> None:
    world.say(
        f"There was nothing brave in the walk home. {hero.id} limped back over the stones, cold to the knees and "
        f"too ashamed to call out."
    )
    if world.get("parcel").meters["lost"] >= THRESHOLD:
        world.say(
            f"{elder.label.capitalize()} saw the empty paws first. {parcel_cfg.recipient} would have no {parcel_cfg.label} at all that night."
        )
    else:
        world.say(
            f"{elder.label.capitalize()} opened the parcel and found only a soaked, ruined mess. {parcel_cfg.recipient} would have no use for it."
        )


def bad_ending(world: World, hero: Entity, elder: Entity, shoes: Entity, parcel_cfg: Parcel) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f'{elder.label.capitalize()} wrapped a blanket around {hero.id}, but did not say, "Never mind," because it did matter. '
        f'The errand was lost, and so was the easy trust of the afternoon.'
    )
    if shoes.meters["lost"] >= THRESHOLD:
        world.say(
            f"That evening, one place by the hearth stayed empty where the missing shoe should have stood. "
            f"{hero.id} stared at the dark doorway and did not ask to run on the moor again."
        )
    else:
        world.say(
            f"That evening, the muddy shoes steamed sadly by the hearth while the ruined parcel sat in a basin. "
            f"{hero.id} watched them and learned how one foolish step can make a whole room quiet."
        )


def tell(
    animal: AnimalKind,
    weather: Weather,
    lure: Lure,
    shoes_cfg: Shoes,
    parcel_cfg: Parcel,
    name: str = "Mira",
    gender: str = "girl",
    elder_gender: str = "mother",
    trait: str = "dreamy",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="hero",
            traits=[trait],
            attrs={"animal": animal.id},
        )
    )
    elder_label = animal.adult_word if elder_gender == "mother" else f"old {animal.id} father"
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_gender,
            label=elder_label,
            role="elder",
            attrs={"animal": animal.id},
        )
    )
    bog = world.add(
        Entity(
            id="bog",
            kind="thing",
            type="bog",
            label="the bog",
            role="hazard",
        )
    )
    bog.meters["softness"] = float(weather.softness)
    shoes = world.add(
        Entity(
            id="shoes",
            kind="thing",
            type="shoes",
            label=shoes_cfg.label,
            role="gear",
        )
    )
    shoes.meters["grip"] = float(shoes_cfg.grip)
    shoes.meters["soak"] = float(shoes_cfg.soak)
    parcel = world.add(
        Entity(
            id="parcel",
            kind="thing",
            type="parcel",
            label=parcel_cfg.label,
            role="parcel",
        )
    )
    hero.meters["off_path"] = 0.0
    hero.meters["stuck"] = 0.0
    hero.meters["cold"] = 0.0
    shoes.meters["muddy"] = 0.0
    shoes.meters["lost"] = 0.0
    parcel.meters["wet"] = 0.0
    parcel.meters["lost"] = 0.0

    introduce(world, hero, elder, animal, shoes_cfg, parcel_cfg)
    warning(world, hero, elder, weather)

    world.para()
    journey(world, hero, lure)
    inner_monologue(world, hero, lure)
    pred = predict_bog(world)
    world.facts["predicted_stuck"] = pred["stuck"]
    world.facts["predicted_parcel_lost"] = pred["parcel_lost"]
    world.facts["predicted_shoe_lost"] = pred["shoe_lost"]
    step_off(world, hero, weather)

    world.para()
    sink_scene(world, hero, shoes, parcel)
    trudge_home(world, hero, elder, parcel_cfg)

    world.para()
    bad_ending(world, hero, elder, shoes, parcel_cfg)

    outcome = "lost" if parcel.meters["lost"] >= THRESHOLD or shoes.meters["lost"] >= THRESHOLD else "ruined"
    world.facts.update(
        animal=animal,
        weather=weather,
        lure=lure,
        shoes_cfg=shoes_cfg,
        parcel_cfg=parcel_cfg,
        hero=hero,
        elder=elder,
        shoes=shoes,
        parcel=parcel,
        outcome=outcome,
        reached_recipient=False,
        bad_ending=True,
    )
    return world


KNOWLEDGE = {
    "moor": [
        (
            "What is a moor?",
            "A moor is a wide open place with rough grass, heather, and soft ground in some spots. Some parts can be boggy and tricky to cross."
        )
    ],
    "bog": [
        (
            "Why is a bog dangerous?",
            "A bog can look flat on top, but the ground underneath is wet and grabby. Small feet can sink into it before they know what is happening."
        )
    ],
    "temptation": [
        (
            "Why can a bright little thing be a problem on a path?",
            "A tempting thing can make you stop thinking about the safe plan. Then you may step where you should not."
        )
    ],
    "shoes": [
        (
            "Why do good shoes matter on wet ground?",
            "Good shoes help your feet grip the ground and stay drier. Thin shoes can slip and soak through very fast."
        )
    ],
    "boots": [
        (
            "What do marsh boots do?",
            "Marsh boots help keep mud and water away from your feet. They also grip better on soft ground."
        )
    ],
    "gift": [
        (
            "Why should you carry a parcel carefully?",
            "A parcel can be dropped, soaked, or broken if you take a foolish shortcut. Carrying it carefully shows you are thinking about the person waiting for it."
        )
    ],
    "mist": [
        (
            "Why can mist make walking harder?",
            "Mist makes everything look softer and farther away. It can also hide which ground is safe and which ground is wet."
        )
    ],
    "rain": [
        (
            "Why does rain make mud worse?",
            "Rain puts more water into the ground. Then the soil loosens and clings more strongly to shoes and paws."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    lure = f["lure"]
    parcel = f["parcel_cfg"]
    shoes = f["shoes_cfg"]
    animal = f["animal"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the words "susceptible", "moor", and "shoe-pl-dim", and ends sadly.',
        f"Tell a gentle but cautionary story about a little {animal.child_word} named {hero.id} who carries {parcel.phrase} across a moor, feels tempted by {lure.label}, and makes one bad choice.",
        f"Write a story with inner monologue where a child in {shoes.label} thinks a tiny shortcut will be safe, but the bad ending proves it was not.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    weather = f["weather"]
    lure = f["lure"]
    parcel_cfg = f["parcel_cfg"]
    shoes_cfg = f["shoes_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {f['animal'].child_word}, and {elder.label} who trusted {hero.pronoun('object')} with an errand. The story follows what happens when {hero.id} leaves the safe stones on the moor."
        ),
        (
            f"What was {hero.id} supposed to do?",
            f"{hero.pronoun().capitalize()} was supposed to carry {parcel_cfg.phrase} across the moor to {parcel_cfg.recipient}. It was meant to bring comfort before evening, so the errand mattered."
        ),
        (
            f"Why did {elder.label} warn {hero.id} to stay on the stones?",
            f"{elder.label.capitalize()} knew the moor was {weather.ground} in that weather. Soft ground can grab little feet before they can pull free."
        ),
        (
            f"What was {hero.id} thinking before stepping off the path?",
            f"{hero.pronoun().capitalize()} told {hero.pronoun('object')} that one tiny step would do no harm. That inner thought matters because it shows how temptation made the bad choice feel small."
        ),
    ]

    if outcome == "lost":
        qa.append(
            (
                f"What went wrong when {hero.id} stepped toward {lure.label}?",
                f"The bog caught at {hero.pronoun('possessive')} feet, and the struggle turned worse than {hero.pronoun()} expected. A shoe or the parcel was lost because the ground was wetter and stronger than {hero.pronoun('possessive')} shoes could handle."
            )
        )
    else:
        qa.append(
            (
                f"What happened to the parcel?",
                f"It fell into the wet and was spoiled. Even though {hero.id} got free, the errand was still ruined because the parcel was no longer fit to give."
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended badly: {hero.id} came home cold, ashamed, and without a proper parcel for {parcel_cfg.recipient}. The quiet hearth and the ruined errand show what changed after one foolish step."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"moor", "bog", "gift", "temptation"}
    tags |= set(world.facts["weather"].tags)
    tags |= set(world.facts["shoes_cfg"].tags)
    out: list[tuple[str, str]] = []
    order = ["moor", "bog", "temptation", "shoes", "boots", "gift", "mist", "rain"]
    for tag in order:
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
        animal="hare",
        weather="mist",
        lure="feather",
        shoes="shoe-pl-dim",
        parcel="cake",
        name="Mira",
        gender="girl",
        elder_gender="mother",
        trait="dreamy",
    ),
    StoryParams(
        animal="lamb",
        weather="drizzle",
        lure="berries",
        shoes="button_shoes",
        parcel="soup",
        name="Pip",
        gender="boy",
        elder_gender="mother",
        trait="eager",
    ),
    StoryParams(
        animal="fox",
        weather="rain",
        lure="bell",
        shoes="reed_slippers",
        parcel="thread",
        name="Juniper",
        gender="girl",
        elder_gender="mother",
        trait="curious",
    ),
    StoryParams(
        animal="hare",
        weather="rain",
        lure="berries",
        shoes="button_shoes",
        parcel="cake",
        name="Rowan",
        gender="boy",
        elder_gender="father",
        trait="restless",
    ),
]


ASP_RULES = r"""
risky(W, L, S) :- weather(W), lure(L), shoes(S), off_path(L), softness(W, SW), grip(S, SG), SW > SG.
valid(A, W, L, S) :- animal(A), risky(W, L, S).

gap(W, S, G) :- softness(W, SW), grip(S, SG), G = SW - SG.
outcome(lost) :- chosen_weather(W), chosen_shoes(S), gap(W, S, G), G >= 2.
outcome(ruined) :- chosen_weather(W), chosen_shoes(S), gap(W, S, G), G = 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("softness", wid, weather.softness))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        if lure.off_path:
            lines.append(asp.fact("off_path", lid))
    for sid, shoes in SHOES.items():
        lines.append(asp.fact("shoes", sid))
        lines.append(asp.fact("grip", sid, shoes.grip))
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
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_shoes", params.shoes),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        w = WEATHERS[params.weather]
        s = SHOES[params.shoes]
        if asp_outcome(params) != loss_level(w, s):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches loss_level() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a little errand across the moor, a tempting step off the path, and a bad ending."
    )
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--weather", choices=sorted(WEATHERS))
    ap.add_argument("--lure", choices=sorted(LURES))
    ap.add_argument("--shoes", choices=sorted(SHOES))
    ap.add_argument("--parcel", choices=sorted(PARCELS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.weather and args.lure and args.shoes:
        weather = WEATHERS[args.weather]
        lure = LURES[args.lure]
        shoes = SHOES[args.shoes]
        if not bog_risk(weather, shoes, lure):
            raise StoryError(explain_rejection(weather, lure, shoes))

    combos = [
        c
        for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.weather is None or c[1] == args.weather)
        and (args.lure is None or c[2] == args.lure)
        and (args.shoes is None or c[3] == args.shoes)
    ]
    if not combos:
        if args.weather and args.lure and args.shoes:
            raise StoryError(explain_rejection(WEATHERS[args.weather], LURES[args.lure], SHOES[args.shoes]))
        raise StoryError("(No valid combination matches the given options.)")

    animal, weather, lure, shoes = rng.choice(sorted(combos))
    parcel = args.parcel or rng.choice(sorted(PARCELS))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        animal=animal,
        weather=weather,
        lure=lure,
        shoes=shoes,
        parcel=parcel,
        name=name,
        gender=gender,
        elder_gender=elder_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.shoes not in SHOES:
        raise StoryError(f"(Unknown shoes: {params.shoes})")
    if params.parcel not in PARCELS:
        raise StoryError(f"(Unknown parcel: {params.parcel})")

    animal = ANIMALS[params.animal]
    weather = WEATHERS[params.weather]
    lure = LURES[params.lure]
    shoes = SHOES[params.shoes]
    parcel = PARCELS[params.parcel]
    if not bog_risk(weather, shoes, lure):
        raise StoryError(explain_rejection(weather, lure, shoes))

    world = tell(
        animal=animal,
        weather=weather,
        lure=lure,
        shoes_cfg=shoes,
        parcel_cfg=parcel,
        name=params.name,
        gender=params.gender,
        elder_gender=params.elder_gender,
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
        print(f"{len(combos)} compatible (animal, weather, lure, shoes) combos:\n")
        for animal, weather, lure, shoes in combos:
            print(f"  {animal:6} {weather:7} {lure:10} {shoes}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} on the moor ({p.weather}, {p.lure}, {p.shoes})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
