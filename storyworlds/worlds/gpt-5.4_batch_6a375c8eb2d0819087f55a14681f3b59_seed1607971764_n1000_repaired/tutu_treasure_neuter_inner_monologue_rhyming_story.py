#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tutu_treasure_neuter_inner_monologue_rhyming_story.py
=================================================================================

A standalone story world about a child in a tutu who goes treasure hunting,
finds a frightened stray pet instead, thinks carefully in an inner monologue,
and helps the animal reach safety. The ending proves what changed: the child
learns that the truest treasure is caring well, and the pet's next steps include
a vet visit and a neuter plan when appropriate.

This world models:
- typed entities with physical meters and emotional memes
- a small causal engine
- a reasonableness gate over lure/animal compatibility and hiding places
- state-driven rhyming-story prose with bits of inner monologue
- grounded QA plus child-facing world knowledge QA
- an inline ASP twin for the same compatibility logic and outcome checks
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    bright_detail: str
    cache: str
    afford_spots: set[str] = field(default_factory=set)
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
    kind: str
    sound: str
    paw: str
    likes: set[str] = field(default_factory=set)
    future_home: str = ""
    neuter_line: str = ""
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
class Spot:
    id: str
    label: str
    phrase: str
    reachable: bool = True
    fear_boost: int = 1
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
class Lure:
    id: str
    label: str
    phrase: str
    gentle: bool = True
    smell: str = ""
    works_for: set[str] = field(default_factory=set)
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
class CarrierCfg:
    id: str
    label: str
    phrase: str
    safe_for: set[str] = field(default_factory=set)
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
class EndingCfg:
    id: str
    keeper: str
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


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the community garden",
        bright_detail="Tomato stakes stood like little masts, and marigolds bobbed in rows.",
        cache="a corner where children sometimes hid shiny stones and bottle-cap treasure",
        afford_spots={"bush", "crate"},
        tags={"garden", "treasure"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        bright_detail="Brick walls held warm sun, and scooter bells rang like tiny chimes.",
        cache="the pebble bed beside the fountain where lost coins sometimes winked",
        afford_spots={"bench", "crate"},
        tags={"courtyard", "treasure"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch and walkway",
        bright_detail="Flowerpots lined the steps, and the railing made neat silver stripes.",
        cache="the step-box where chalk bits and shell buttons sometimes gathered",
        afford_spots={"bench", "bush"},
        tags={"porch", "treasure"},
    ),
}

ANIMALS = {
    "kitten": AnimalCfg(
        id="kitten",
        label="kitten",
        kind="cat",
        sound="mew",
        paw="paw",
        likes={"tuna", "treats"},
        future_home="a soft basket by the window",
        neuter_line="The vet smiled and said that when the little cat was big enough, a neuter visit would help him stay healthy and keep future kittens from crowding the world.",
        tags={"kitten", "pet", "neuter"},
    ),
    "puppy": AnimalCfg(
        id="puppy",
        label="puppy",
        kind="dog",
        sound="yip",
        paw="paw",
        likes={"treats", "crackers"},
        future_home="a blanket bed near the kitchen",
        neuter_line="The vet smiled and said that when the little dog was old enough, a neuter visit would help him stay healthy and stop more puppies from arriving by surprise.",
        tags={"puppy", "pet", "neuter"},
    ),
    "rabbit": AnimalCfg(
        id="rabbit",
        label="rabbit",
        kind="rabbit",
        sound="sniff",
        paw="paw",
        likes={"carrot"},
        future_home="a roomy pen with hay and a water bowl",
        neuter_line="The vet smiled and said that when the rabbit was ready, a neuter visit would help him stay calm and healthy and make home life easier.",
        tags={"rabbit", "pet", "neuter"},
    ),
}

SPOTS = {
    "bush": Spot(
        id="bush",
        label="bush",
        phrase="under a prickly bush",
        reachable=True,
        fear_boost=1,
        tags={"bush"},
    ),
    "bench": Spot(
        id="bench",
        label="bench",
        phrase="under the slatted bench",
        reachable=True,
        fear_boost=1,
        tags={"bench"},
    ),
    "crate": Spot(
        id="crate",
        label="crate",
        phrase="inside a tipped wooden crate",
        reachable=True,
        fear_boost=2,
        tags={"crate"},
    ),
    "storm_drain": Spot(
        id="storm_drain",
        label="storm drain",
        phrase="down in the storm drain",
        reachable=False,
        fear_boost=3,
        tags={"drain"},
    ),
}

LURES = {
    "tuna": Lure(
        id="tuna",
        label="tuna",
        phrase="a little dish of tuna",
        gentle=True,
        smell="salty and strong",
        works_for={"kitten"},
        tags={"tuna"},
    ),
    "treats": Lure(
        id="treats",
        label="treats",
        phrase="a few crunchy pet treats",
        gentle=True,
        smell="toasty and meaty",
        works_for={"kitten", "puppy"},
        tags={"treats"},
    ),
    "crackers": Lure(
        id="crackers",
        label="crackers",
        phrase="a crumbly cracker",
        gentle=True,
        smell="warm and buttery",
        works_for={"puppy"},
        tags={"crackers"},
    ),
    "carrot": Lure(
        id="carrot",
        label="carrot",
        phrase="a sweet carrot coin",
        gentle=True,
        smell="earthy and fresh",
        works_for={"rabbit"},
        tags={"carrot"},
    ),
}

CARRIERS = {
    "laundry_basket": CarrierCfg(
        id="laundry_basket",
        label="laundry basket",
        phrase="a laundry basket lined with a towel",
        safe_for={"kitten", "puppy", "rabbit"},
        tags={"carrier"},
    ),
    "pet_carrier": CarrierCfg(
        id="pet_carrier",
        label="pet carrier",
        phrase="a real pet carrier with a click-shut door",
        safe_for={"kitten", "puppy", "rabbit"},
        tags={"carrier"},
    ),
    "cardboard_box": CarrierCfg(
        id="cardboard_box",
        label="cardboard box",
        phrase="a cardboard box with air holes and a soft cloth",
        safe_for={"kitten", "rabbit"},
        tags={"carrier"},
    ),
}

ENDINGS = {
    "foster": EndingCfg(
        id="foster",
        keeper="foster",
        image="At home, the little pet curled up small and still, then sighed and slept.",
        tags={"foster"},
    ),
    "adopt": EndingCfg(
        id="adopt",
        keeper="adopt",
        image="By evening, the little pet had a name, a bowl, and a sleepy place to rest.",
        tags={"adopt"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Zoe", "Ava", "Nora", "Tessa", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Theo", "Sam", "Noah", "Jack"]
TRAITS = ["gentle", "hopeful", "careful", "bright", "patient"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_hunger_to_trust(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    if animal.meters["hungry"] < THRESHOLD:
        return out
    if animal.attrs.get("lure_ok") and world.facts.get("used_lure"):
        sig = ("trust_from_lure", animal.id, world.facts["used_lure"])
        if sig not in world.fired:
            world.fired.add(sig)
            animal.meters["trust"] += 1
            animal.meters["fear"] = max(0.0, animal.meters["fear"] - 1)
            out.append("__trust__")
    return out


def _r_trust_to_approach(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    if animal.meters["trust"] < THRESHOLD or animal.meters["fear"] > 1.5:
        return out
    sig = ("approach", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["near_child"] += 1
    out.append("__approach__")
    return out


def _r_near_to_rescued(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    carrier = world.get("carrier")
    if animal.meters["near_child"] < THRESHOLD:
        return out
    if not animal.attrs.get("carrier_ok"):
        return out
    sig = ("rescued", animal.id, carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["safe"] += 1
    animal.meters["rescued"] += 1
    animal.meters["fear"] = 0.0
    out.append("__rescued__")
    return out


CAUSAL_RULES = [
    Rule(name="hunger_to_trust", tag="physical", apply=_r_hunger_to_trust),
    Rule(name="trust_to_approach", tag="social", apply=_r_trust_to_approach),
    Rule(name="near_to_rescued", tag="physical", apply=_r_near_to_rescued),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints / prediction
# ---------------------------------------------------------------------------
def spot_allowed(setting: Setting, spot: Spot) -> bool:
    return spot.id in setting.afford_spots


def lure_matches(animal: AnimalCfg, lure: Lure) -> bool:
    return animal.id in lure.works_for


def carrier_matches(animal: AnimalCfg, carrier: CarrierCfg) -> bool:
    return animal.id in carrier.safe_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for animal_id, animal in ANIMALS.items():
            for spot_id, spot in SPOTS.items():
                if not (spot_allowed(setting, spot) and spot.reachable):
                    continue
                for lure_id, lure in LURES.items():
                    if lure_matches(animal, lure):
                        combos.append((setting_id, animal_id, spot_id, lure_id))
    return combos


def explain_rejection(setting: Setting, animal: AnimalCfg, spot: Spot, lure: Lure) -> str:
    if not spot_allowed(setting, spot):
        return (
            f"(No story: {spot.phrase} does not fit {setting.place}. "
            f"Pick a hiding place that belongs in that setting.)"
        )
    if not spot.reachable:
        return (
            f"(No story: if the {animal.label} is {spot.phrase}, a child cannot safely "
            f"rescue it with gentle waiting and a basket. This world only tells small, reachable rescues.)"
        )
    if not lure_matches(animal, lure):
        return (
            f"(No story: {lure.label} is not a sensible lure for a {animal.label}. "
            f"Choose a treat the animal would actually follow.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def predict_rescue(world: World, lure_id: str, carrier_id: str) -> dict:
    sim = world.copy()
    sim.facts["used_lure"] = lure_id
    sim.get("animal").attrs["carrier_ok"] = sim.get("animal").attrs.get("carrier_ok", False) and (
        carrier_id == sim.facts["carrier_id"]
    )
    propagate(sim, narrate=False)
    animal = sim.get("animal")
    return {
        "approaches": animal.meters["near_child"] >= THRESHOLD,
        "rescued": animal.meters["rescued"] >= THRESHOLD,
        "fear": animal.meters["fear"],
    }


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"One bright day in {setting.place}, {child.id} skipped with a swish and a twirl, "
        f"a {child.attrs['color']} tutu puffing round this treasure-loving {child.type}. "
        f"{setting.bright_detail}"
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} eyes were sharp for sparkle and clue. "
        f"{setting.cache} looked like a map come true."
    )


def treasure_goal(world: World, child: Entity) -> None:
    world.say(
        f'"I will find some treasure today," thought {child.id}. '
        f'"A bead, a shell, a button blue—something small with a secret hue."'
    )


def hear_sound(world: World, child: Entity, animal_cfg: AnimalCfg, spot: Spot) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"But under the hunt-song, thin and light, came a {animal_cfg.sound} in a worried fright, "
        f"from {spot.phrase} half tucked from sight."
    )


def discover(world: World, child: Entity, animal: Entity, animal_cfg: AnimalCfg, spot: Spot) -> None:
    world.say(
        f"{child.id} knelt down low and peeped with care. There was a little {animal_cfg.label} shivering there, "
        f"with dusty fur and wide round stare."
    )
    if spot.fear_boost >= 2:
        world.say(
            f"The cramped dark place made the small one freeze; even the breeze seemed hard to please."
        )


def inner_monologue(world: World, child: Entity, animal_cfg: AnimalCfg, lure: Lure) -> None:
    child.memes["care"] += 1
    child.memes["thinking"] += 1
    world.say(
        f'"Do not rush and do not grab," thought {child.id}. '
        f'"Fast hands may make a frightened heart jab. If I stay soft, if I stay true, '
        f'maybe it will trust me too."'
    )
    world.say(
        f'"What does this little one need from me? Not treasure first, but safety," thought {child.id}. '
        f'"A gentle smell, a patient knee, and room to choose what feels fear-free."'
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} remembered the {lure.label} in the bag and held it still instead of bold. "
        f"The air soon filled with {lure.smell} gold."
    )


def call_parent(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," called {child.id}, "please come near. '
        f'There is a small one hiding here."'
    )


def parent_guides(world: World, parent: Entity, child: Entity, carrier: CarrierCfg) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came with quiet feet, carrying {carrier.phrase}. "
        f'"You had a kind and careful plan," {parent.pronoun()} said. '
        f'"We will wait and let calm win, not hurry hands and tumble in."'
    )


def use_lure(world: World, child: Entity, lure: Lure) -> None:
    world.facts["used_lure"] = lure.id
    world.say(
        f"{child.id} set down {lure.phrase}, then scooted back a little space. "
        f"The smell drifted slow in the sunny air, a tiny promise: care is here."
    )
    propagate(world, narrate=False)


def approach(world: World, animal_cfg: AnimalCfg) -> None:
    animal = world.get("animal")
    if animal.meters["near_child"] >= THRESHOLD:
        world.say(
            f"First came a nose, then whiskers through, then one small {animal_cfg.paw} with a cautious view. "
            f"The little {animal_cfg.label} crept near the dish and took one bite, then two."
        )


def rescue(world: World, child: Entity, parent: Entity, carrier: CarrierCfg, ending: EndingCfg) -> None:
    animal = world.get("animal")
    if animal.meters["rescued"] >= THRESHOLD:
        child.memes["relief"] += 1
        parent.memes["relief"] += 1
        world.say(
            f"When the small one had eaten and stopped to rest, {parent.label_word} tipped {carrier.phrase} close to its chest. "
            f"The little pet stepped inside all by itself, and the door clicked shut with the gentlest help."
        )
        world.say(
            f'"We found no coin and no pirate chest," thought {child.id}, '
            f'"but safe small breathing is treasure best."'
        )
        world.say(ending.image)


def vet_ending(world: World, child: Entity, animal_cfg: AnimalCfg, ending: EndingCfg) -> None:
    world.say(
        f"At the clinic they checked for a family first, then gave fresh water for the poor thing's thirst."
    )
    world.say(animal_cfg.neuter_line)
    if ending.keeper == "adopt":
        world.say(
            f"Soon {child.id} helped choose a name, and every evening felt changed by the same sweet aim: "
            f"fill the bowl, speak low, be kind, and keep that living treasure in mind."
        )
    else:
        world.say(
            f"Until the right home could be found, {child.id} promised gentle steps and a soothing sound."
        )


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    animal_cfg: AnimalCfg,
    spot: Spot,
    lure: Lure,
    carrier_cfg: CarrierCfg,
    ending_cfg: EndingCfg,
    *,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "gentle",
    tutu_color: str = "pink",
) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"color": tutu_color},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type=animal_cfg.kind,
        role="animal",
        label=animal_cfg.label,
        attrs={
            "lure_ok": lure_matches(animal_cfg, lure),
            "carrier_ok": carrier_matches(animal_cfg, carrier_cfg),
        },
    ))
    world.add(Entity(
        id="carrier",
        kind="thing",
        type="carrier",
        label=carrier_cfg.label,
    ))

    animal.meters["hungry"] = 1.0
    animal.meters["fear"] = float(spot.fear_boost)
    animal.meters["trust"] = 0.0
    animal.meters["near_child"] = 0.0
    animal.meters["rescued"] = 0.0
    animal.meters["safe"] = 0.0

    world.facts.update(
        setting=setting,
        animal_cfg=animal_cfg,
        spot=spot,
        lure=lure,
        carrier_cfg=carrier_cfg,
        carrier_id=carrier_cfg.id,
        ending=ending_cfg,
        child=child,
        parent=parent,
        found_treasure=False,
        used_lure="",
    )

    introduce(world, child, setting)
    treasure_goal(world, child)
    world.para()

    hear_sound(world, child, animal_cfg, spot)
    discover(world, child, animal, animal_cfg, spot)
    inner_monologue(world, child, animal_cfg, lure)
    call_parent(world, parent, child)
    parent_guides(world, parent, child, carrier_cfg)
    world.para()

    use_lure(world, child, lure)
    approach(world, animal_cfg)
    propagate(world, narrate=False)
    rescue(world, child, parent, carrier_cfg, ending_cfg)
    world.para()

    vet_ending(world, child, animal_cfg, ending_cfg)

    world.facts.update(
        approached=animal.meters["near_child"] >= THRESHOLD,
        rescued=animal.meters["rescued"] >= THRESHOLD,
        safe=animal.meters["safe"] >= THRESHOLD,
        keeper=ending_cfg.keeper,
    )
    return world


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    animal: str
    spot: str
    lure: str
    carrier: str
    ending: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    tutu_color: str = "pink"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "treasure": [(
        "What can treasure mean in a story?",
        "Treasure can mean gold or shiny things, but it can also mean something precious you should care for. Sometimes the best treasure is a living thing being safe."
    )],
    "kitten": [(
        "What does a kitten need if it is lost?",
        "A lost kitten needs calm help, food, water, and a safe place. A grown-up or shelter should check for its family and make sure it is healthy."
    )],
    "puppy": [(
        "What does a lost puppy need?",
        "A lost puppy needs calm voices, water, and a safe place to rest. A grown-up should help check for a tag, a chip, or the puppy's family."
    )],
    "rabbit": [(
        "How should you help a lost rabbit?",
        "Move slowly and stay gentle, because rabbits scare easily. A grown-up should help bring the rabbit to a safe place with food and water."
    )],
    "carrier": [(
        "Why is a pet carrier or basket useful in a rescue?",
        "It keeps a small animal from running back into danger. It also gives the animal a dark, snug place that can feel safer."
    )],
    "neuter": [(
        "What does neuter mean for a pet?",
        "Neuter is an operation a veterinarian does so a male pet cannot make babies. It can help with health and keep there from being more unwanted litters."
    )],
    "gentle": [(
        "Why should you move gently around a frightened animal?",
        "A scared animal may run or hide if hands come too fast. Slow movements and soft voices help it feel safer."
    )],
}
KNOWLEDGE_ORDER = ["treasure", "kitten", "puppy", "rabbit", "carrier", "neuter", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal_cfg = f["animal_cfg"]
    setting = f["setting"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "tutu," "treasure," and "neuter." Use inner monologue as {child.id} finds a lost {animal_cfg.label} in {setting.place}.',
        f"Tell a gentle rhyming story where a child in a {child.attrs['color']} tutu goes looking for treasure but discovers a frightened {animal_cfg.label} instead, and thinks carefully before helping.",
        f'Write a child-facing rescue story in rhyme with inner thoughts, where "treasure" changes from a shiny object into caring for a small animal, and the ending mentions a vet and a neuter plan.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal_cfg = f["animal_cfg"]
    setting = f["setting"]
    spot = f["spot"]
    lure = f["lure"]
    carrier_cfg = f["carrier_cfg"]
    ending = f["ending"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in a {child.attrs['color']} tutu, and a frightened {animal_cfg.label} in {setting.place}. {parent.label_word.capitalize()} also helps with the rescue."
        ),
        (
            "What treasure was the child looking for at first?",
            f"{child.id} first hoped to find a small shiny treasure like a bead, shell, or button. That wish is what brought {child.pronoun('object')} to the spot where the little animal was hiding."
        ),
        (
            f"Where was the {animal_cfg.label} hiding?",
            f"The little {animal_cfg.label} was hiding {spot.phrase}. That cramped place made it feel scared and hard to reach, so the rescue had to be calm."
        ),
        (
            f"How did {child.id}'s inner thoughts help the rescue?",
            f"{child.id} told {child.pronoun('object')}self not to rush or grab because fast hands could scare the animal more. That quiet thinking led to a gentle plan instead of a frightening one."
        ),
        (
            f"How did they help the {animal_cfg.label} come closer?",
            f"They used {lure.phrase} and gave the little animal space to choose. The smell was inviting, and the waiting made the frightened pet brave enough to creep near."
        ),
    ]
    if f.get("rescued"):
        qa.append((
            f"How did the rescue end?",
            f"The {animal_cfg.label} stepped into {carrier_cfg.phrase} and was carried to safety. In the end, {child.id} understood that a living creature can be a truer treasure than anything shiny."
        ))
    qa.append((
        "Why does the story mention neuter at the end?",
        f"It shows that caring for a pet means more than one kind rescue in one bright moment. The vet's neuter plan is part of keeping the little animal healthy and cared for over time."
    ))
    if ending.keeper == "adopt":
        qa.append((
            f"What changed for {child.id} by the end of the story?",
            f"At first {child.id} was hunting for treasure outside. By the end, {child.pronoun('subject')} was helping care for a real pet at home, so the meaning of treasure had changed completely."
        ))
    else:
        qa.append((
            f"What changed for {child.id} by the end of the story?",
            f"At first {child.id} was hunting for treasure outside. By the end, {child.pronoun('subject')} had learned that being gentle and helping a scared animal mattered more than finding shiny things."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"treasure", "carrier", "gentle", "neuter"} | set(f["animal_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(Setting, Animal, Spot, Lure) :-
    setting(Setting), animal(Animal), spot(Spot), lure(Lure),
    affords(Setting, Spot), reachable(Spot), likes(Animal, Lure).

% --- simple outcome model --------------------------------------------------
rescued :-
    chosen_animal(A), chosen_lure(L), likes(A, L),
    chosen_spot(S), reachable(S),
    chosen_carrier(C), safe_carrier(C, A).

outcome(rescued) :- rescued.
outcome(stuck) :- not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for spot_id in sorted(setting.afford_spots):
            lines.append(asp.fact("affords", setting_id, spot_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for lure_id in sorted(animal.likes):
            lines.append(asp.fact("likes", animal_id, lure_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.reachable:
            lines.append(asp.fact("reachable", spot_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        for animal_id in sorted(carrier.safe_for):
            lines.append(asp.fact("safe_carrier", carrier_id, animal_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_lure", params.lure),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_carrier", params.carrier),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# Helpers / curated set
# ---------------------------------------------------------------------------
def outcome_of(params: StoryParams) -> str:
    if not (
        params.setting in SETTINGS
        and params.animal in ANIMALS
        and params.spot in SPOTS
        and params.lure in LURES
        and params.carrier in CARRIERS
    ):
        return "?"
    if not spot_allowed(SETTINGS[params.setting], SPOTS[params.spot]):
        return "stuck"
    if not SPOTS[params.spot].reachable:
        return "stuck"
    if not lure_matches(ANIMALS[params.animal], LURES[params.lure]):
        return "stuck"
    if not carrier_matches(ANIMALS[params.animal], CARRIERS[params.carrier]):
        return "stuck"
    return "rescued"


CURATED = [
    StoryParams(
        setting="garden",
        animal="kitten",
        spot="bush",
        lure="tuna",
        carrier="pet_carrier",
        ending="adopt",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        tutu_color="pink",
    ),
    StoryParams(
        setting="courtyard",
        animal="puppy",
        spot="bench",
        lure="crackers",
        carrier="laundry_basket",
        ending="foster",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="careful",
        tutu_color="blue",
    ),
    StoryParams(
        setting="porch",
        animal="rabbit",
        spot="bush",
        lure="carrot",
        carrier="cardboard_box",
        ending="foster",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        trait="patient",
        tutu_color="gold",
    ),
    StoryParams(
        setting="garden",
        animal="puppy",
        spot="crate",
        lure="treats",
        carrier="pet_carrier",
        ending="adopt",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        trait="bright",
        tutu_color="green",
    ),
]


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming inner-monologue story world: a child in a tutu goes treasure hunting and helps a lost pet."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--tutu-color", choices=["pink", "blue", "gold", "green", "violet"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def explain_gender(gender: str, name: str) -> str:
    return f'(No story: the supplied name "{name}" does not fit the requested gender "{gender}" in this world.)'


def name_pool(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.animal and args.spot and args.lure:
        s = SETTINGS[args.setting]
        a = ANIMALS[args.animal]
        sp = SPOTS[args.spot]
        l = LURES[args.lure]
        if not (spot_allowed(s, sp) and sp.reachable and lure_matches(a, l)):
            raise StoryError(explain_rejection(s, a, sp, l))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.animal is None or c[1] == args.animal)
        and (args.spot is None or c[2] == args.spot)
        and (args.lure is None or c[3] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, spot_id, lure_id = rng.choice(sorted(combos))
    carrier_choices = sorted(
        cid for cid, cfg in CARRIERS.items()
        if carrier_matches(ANIMALS[animal_id], cfg)
        and (args.carrier is None or cid == args.carrier)
    )
    if not carrier_choices:
        raise StoryError("(No valid carrier matches the given options.)")
    carrier_id = rng.choice(carrier_choices)

    gender = args.gender or rng.choice(["girl", "boy"])
    pool = name_pool(gender)
    if args.name and args.name not in GIRL_NAMES + BOY_NAMES:
        raise StoryError(explain_gender(gender, args.name))
    if args.name and args.name not in pool:
        raise StoryError(explain_gender(gender, args.name))
    child_name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    ending = args.ending or rng.choice(sorted(ENDINGS))
    trait = rng.choice(TRAITS)
    tutu_color = args.tutu_color or rng.choice(["pink", "blue", "gold", "green", "violet"])
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        spot=spot_id,
        lure=lure_id,
        carrier=carrier_id,
        ending=ending,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        tutu_color=tutu_color,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "setting": SETTINGS,
        "animal": ANIMALS,
        "spot": SPOTS,
        "lure": LURES,
        "carrier": CARRIERS,
        "ending": ENDINGS,
    }
    for field_name, registry in required.items():
        key = getattr(params, field_name)
        if key not in registry:
            raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    setting = SETTINGS[params.setting]
    animal = ANIMALS[params.animal]
    spot = SPOTS[params.spot]
    lure = LURES[params.lure]
    carrier = CARRIERS[params.carrier]
    if not (spot_allowed(setting, spot) and spot.reachable and lure_matches(animal, lure)):
        raise StoryError(explain_rejection(setting, animal, spot, lure))
    if not carrier_matches(animal, carrier):
        raise StoryError("(No story: that carrier is not safe for this animal.)")

    world = tell(
        setting=setting,
        animal_cfg=animal,
        spot=spot,
        lure=lure,
        carrier_cfg=carrier,
        ending_cfg=ENDINGS[params.ending],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        tutu_color=params.tutu_color,
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
    for s in range(20):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Failed to resolve random params for seed {s}.")
            continue

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # smoke test ordinary generation / emit
    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generate()/emit() passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, animal, spot, lure) combos:\n")
        for setting_id, animal_id, spot_id, lure_id in combos:
            print(f"  {setting_id:10} {animal_id:8} {spot_id:10} {lure_id}")
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
                f"### {p.child_name}: {p.animal} at {p.setting} "
                f"({p.spot}, {p.lure}, {p.ending})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
