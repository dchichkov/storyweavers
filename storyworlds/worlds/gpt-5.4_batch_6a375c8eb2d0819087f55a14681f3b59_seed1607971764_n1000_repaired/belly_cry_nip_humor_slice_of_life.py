#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/belly_cry_nip_humor_slice_of_life.py
===============================================================

A small storyworld about a hungry toddler waiting for a hot meal in an ordinary
kitchen. A growling belly turns into a cry, a pet gives a tiny nip to something
dangling, and the family finds a funny, gentle way through the wait.

The domain aims for slice-of-life warmth with a comic turn:
- a meal smells good but is not ready yet
- the toddler's hunger rises into a cry
- a quick bridge snack helps
- a kitten or puppy gives a playful nip to a dangling cloth
- the funny little flutter helps the tears turn into a laugh
- the meal arrives and the ending image proves what changed

Run it
------
python storyworlds/worlds/gpt-5.4/belly_cry_nip_humor_slice_of_life.py
python storyworlds/worlds/gpt-5.4/belly_cry_nip_humor_slice_of_life.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/belly_cry_nip_humor_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/belly_cry_nip_humor_slice_of_life.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Meal:
    id: str
    label: str
    smell: str
    bowl: str
    wait: int
    spoonable: bool = True
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
class Soother:
    id: str
    label: str
    phrase: str
    power: int
    safe_for_toddler: bool = True
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
class NipTarget:
    id: str
    label: str
    phrase: str
    dangling: bool
    flutter_text: str
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
class PetCfg:
    id: str
    label: str
    sound: str
    type: str
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
        self.facts: dict = {
            "meal_wait": 0,
            "soother_power": 0,
            "outcome": "",
            "nip_happened": False,
            "cry_started": False,
            "laugh_started": False,
        }

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


def _r_hunger_to_cry(world: World) -> list[str]:
    out: list[str] = []
    toddler = world.get("toddler")
    if toddler.meters["hunger"] >= 2 and toddler.meters["crying"] < THRESHOLD:
        sig = ("cry",)
        if sig not in world.fired:
            world.fired.add(sig)
            toddler.meters["crying"] += 1
            toddler.memes["distress"] += 1
            world.facts["cry_started"] = True
            out.append("__cry__")
    return out


def _r_snack_settles(world: World) -> list[str]:
    toddler = world.get("toddler")
    if toddler.meters["snack"] < THRESHOLD:
        return []
    sig = ("settle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toddler.meters["hunger"] = max(0.0, toddler.meters["hunger"] - float(world.facts["soother_power"]))
    if toddler.meters["hunger"] < 2:
        toddler.meters["crying"] = 0.0
        toddler.memes["relief"] += 1
    return []


def _r_nip_to_laugh(world: World) -> list[str]:
    pet = world.get("pet")
    target = world.get("target")
    toddler = world.get("toddler")
    if pet.meters["nipped"] < THRESHOLD or not target.attrs.get("dangling"):
        return []
    sig = ("laugh",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["flutter"] += 1
    toddler.memes["surprise"] += 1
    if toddler.meters["crying"] < THRESHOLD or toddler.meters["hunger"] < 2:
        toddler.memes["amusement"] += 1
        world.facts["laugh_started"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hunger_to_cry", tag="physical", apply=_r_hunger_to_cry),
    Rule(name="snack_settles", tag="physical", apply=_r_snack_settles),
    Rule(name="nip_to_laugh", tag="social", apply=_r_nip_to_laugh),
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


MEALS = {
    "porridge": Meal(
        id="porridge",
        label="warm porridge",
        smell="sweet cinnamon steam",
        bowl="a blue bowl of porridge",
        wait=1,
        tags={"porridge", "kitchen"},
    ),
    "noodles": Meal(
        id="noodles",
        label="soft noodles",
        smell="garlic and soup",
        bowl="a little bowl of noodles",
        wait=2,
        tags={"noodles", "kitchen"},
    ),
    "dumplings": Meal(
        id="dumplings",
        label="steamy dumplings",
        smell="ginger and broth",
        bowl="a plate of dumplings cut into small bites",
        wait=3,
        tags={"dumplings", "kitchen"},
    ),
    "pancakes": Meal(
        id="pancakes",
        label="small pancakes",
        smell="butter and vanilla",
        bowl="a warm plate of little pancakes",
        wait=1,
        tags={"pancakes", "kitchen"},
    ),
}

SOOTHERS = {
    "banana": Soother(
        id="banana",
        label="banana slice",
        phrase="a soft banana slice",
        power=2,
        safe_for_toddler=True,
        tags={"banana", "snack"},
    ),
    "cracker": Soother(
        id="cracker",
        label="plain cracker",
        phrase="a plain little cracker",
        power=1,
        safe_for_toddler=True,
        tags={"cracker", "snack"},
    ),
    "yogurt": Soother(
        id="yogurt",
        label="yogurt spoonful",
        phrase="a spoonful of yogurt",
        power=3,
        safe_for_toddler=True,
        tags={"yogurt", "snack"},
    ),
    "nuts": Soother(
        id="nuts",
        label="whole nuts",
        phrase="a handful of whole nuts",
        power=2,
        safe_for_toddler=False,
        tags={"nuts"},
    ),
}

TARGETS = {
    "apron_string": NipTarget(
        id="apron_string",
        label="apron string",
        phrase="the loose apron string",
        dangling=True,
        flutter_text="The apron string flicked like a tiny flag",
        tags={"apron", "cloth"},
    ),
    "tea_towel": NipTarget(
        id="tea_towel",
        label="tea towel corner",
        phrase="the corner of the tea towel",
        dangling=True,
        flutter_text="The tea towel flapped and brushed the air",
        tags={"towel", "cloth"},
    ),
    "shoelace": NipTarget(
        id="shoelace",
        label="shoelace",
        phrase="the dangling shoelace",
        dangling=True,
        flutter_text="The shoelace bounced in a silly little loop",
        tags={"shoelace"},
    ),
    "chair_leg": NipTarget(
        id="chair_leg",
        label="chair leg",
        phrase="the chair leg",
        dangling=False,
        flutter_text="Nothing funny happened",
        tags={"chair"},
    ),
}

PETS = {
    "kitten": PetCfg(
        id="kitten",
        label="kitten",
        sound="mrrp",
        type="cat",
        tags={"cat", "pet"},
    ),
    "puppy": PetCfg(
        id="puppy",
        label="puppy",
        sound="ruff",
        type="dog",
        tags={"dog", "pet"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Noah", "Finn", "Eli"]
TODDLER_NAMES = ["Pip", "Tess", "Milo", "June", "Nell", "Ollie"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for meal_id, meal in MEALS.items():
        for soother_id, soother in SOOTHERS.items():
            for target_id, target in TARGETS.items():
                if soother.safe_for_toddler and target.dangling and meal.spoonable:
                    combos.append((meal_id, soother_id, target_id))
    return combos


def explain_target(target: NipTarget) -> str:
    return (
        f"(No story: {target.phrase} does not dangle, so a playful nip would not make "
        f"a funny flutter. Pick a dangling target like an apron string or tea towel.)"
    )


def explain_soother(soother: Soother) -> str:
    return (
        f"(No story: {soother.phrase} is not a good toddler bridge snack here. "
        f"Pick something soft and simple, like yogurt, banana, or a plain cracker.)"
    )


def outcome_of(params: "StoryParams") -> str:
    meal = MEALS[params.meal]
    soother = SOOTHERS[params.soother]
    comfort = soother.power + 1
    return "giggle" if comfort >= meal.wait else "sniffly"


@dataclass
class StoryParams:
    meal: str
    soother: str
    target: str
    pet: str
    helper_name: str
    helper_gender: str
    toddler_name: str
    toddler_gender: str
    caregiver: str
    helper_trait: str
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_hunger(world: World, snack: Soother) -> dict:
    sim = world.copy()
    toddler = sim.get("toddler")
    toddler.meters["snack"] += 1
    sim.facts["soother_power"] = snack.power
    propagate(sim, narrate=False)
    return {
        "crying": toddler.meters["crying"] >= THRESHOLD,
        "hunger": toddler.meters["hunger"],
    }


def scene_setup(world: World, helper: Entity, toddler: Entity, caregiver: Entity, meal: Meal, pet: PetCfg) -> None:
    world.say(
        f"After a busy afternoon, {helper.id} stood on a stool beside {caregiver.label_word} "
        f"and watched dinner in the kitchen. {meal.label.capitalize()} filled the room with "
        f"{meal.smell}, and {toddler.id} sat in a booster seat kicking small feet under the table."
    )
    world.say(
        f"Down by the floor, the family {pet.label} prowled in hopeful little circles as if "
        f"the smell belonged to {pet.label_word(pet) if False else pet.label} too."
    )


def belly_rumble(world: World, toddler: Entity, meal: Meal) -> None:
    toddler.meters["hunger"] += float(meal.wait)
    toddler.memes["want_food"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{toddler.id}'s belly made a round, surprised sound. {toddler.pronoun().capitalize()} "
        f"leaned toward the stove and whispered, \"Mine?\""
    )


def cry_beat(world: World, toddler: Entity, helper: Entity) -> None:
    if toddler.meters["crying"] >= THRESHOLD:
        world.say(
            f"But the food still needed another minute. {toddler.id}'s mouth tipped down, "
            f"and soon a real cry came out."
        )
        helper.memes["concern"] += 1
    else:
        world.say(
            f"The wait was short, but {toddler.id} still wriggled in the chair and looked very serious."
        )


def helper_notice(world: World, helper: Entity, toddler: Entity, caregiver: Entity, soother: Soother) -> None:
    pred = predict_hunger(world, soother)
    world.facts["predicted_hunger_after_snack"] = pred["hunger"]
    world.say(
        f"{helper.id} looked from the pot to {toddler.id}. \"{caregiver.label_word.capitalize()}, "
        f"{toddler.id}'s belly sounds worried,\" {helper.pronoun()} said."
    )


def offer_bridge(world: World, caregiver: Entity, toddler: Entity, soother: Soother) -> None:
    toddler.meters["snack"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{caregiver.label_word.capitalize()} nodded and offered {soother.phrase}. '
        f'"This is just a little bridge bite while dinner finishes," {caregiver.pronoun()} said.'
    )


def pet_nip(world: World, pet_ent: Entity, target_ent: Entity, pet: PetCfg, target: NipTarget) -> None:
    pet_ent.meters["nipped"] += 1
    world.facts["nip_happened"] = True
    propagate(world, narrate=False)
    world.say(
        f"Just then, the {pet.label} made a tiny nip at {target.phrase}. "
        f"{target.flutter_text}, and the {pet.label} froze with its ears up as if it had "
        f"invented the whole joke on purpose."
    )


def laugh_or_sniffle(world: World, toddler: Entity, helper: Entity, caregiver: Entity, pet: PetCfg) -> None:
    if world.facts["laugh_started"]:
        toddler.meters["crying"] = 0.0
        toddler.memes["joy"] += 1
        helper.memes["joy"] += 1
        caregiver.memes["relief"] += 1
        world.say(
            f"For one blink, {toddler.id} forgot to cry. Then {toddler.pronoun()} made a wet little "
            f"snort and laughed instead. Even {helper.id} had to press a hand over {helper.pronoun('possessive')} "
            f"mouth because the surprised {pet.label} looked too proud."
        )
    else:
        toddler.memes["relief"] += 1
        caregiver.memes["patience"] += 1
        world.say(
            f"The cry softened into sniffles. {toddler.id} kept one hand on the snack and one hand on "
            f"{caregiver.label_word}'s sleeve while the room calmed down."
        )


def meal_arrives(world: World, helper: Entity, toddler: Entity, caregiver: Entity, meal: Meal) -> None:
    toddler.meters["fullness"] += 2
    toddler.meters["hunger"] = 0.0
    toddler.meters["crying"] = 0.0
    toddler.memes["comfort"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"A moment later, dinner really was ready. {caregiver.label_word.capitalize()} set down "
        f"{meal.bowl}, and the room changed all at once."
    )
    world.say(
        f"{toddler.id} took the first bite, blinked, and relaxed from shoulders to toes. Soon "
        f"{toddler.pronoun('possessive')} belly was full, {helper.id} was grinning over the table, "
        f"and the little family kept laughing whenever the {world.facts['pet_cfg'].label} glanced at "
        f"the dangling {world.facts['target_cfg'].label} again."
    )


def tell(
    meal: Meal,
    soother: Soother,
    target: NipTarget,
    pet: PetCfg,
    helper_name: str = "Mia",
    helper_gender: str = "girl",
    toddler_name: str = "Pip",
    toddler_gender: str = "boy",
    caregiver_type: str = "mother",
    helper_trait: str = "gentle",
) -> World:
    world = World()
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=[helper_trait],
            age=6,
            attrs={},
        )
    )
    toddler = world.add(
        Entity(
            id=toddler_name,
            kind="character",
            type=toddler_gender,
            role="toddler",
            traits=["hungry", "small"],
            age=2,
            attrs={},
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the grown-up",
            attrs={},
        )
    )
    pet_ent = world.add(
        Entity(
            id="pet",
            kind="character",
            type="animal",
            role="pet",
            label=pet.label,
            attrs={},
        )
    )
    target_ent = world.add(
        Entity(
            id="target",
            kind="thing",
            type="cloth" if target.dangling else "hard_thing",
            label=target.label,
            attrs={"dangling": target.dangling},
        )
    )
    world.add(Entity(id="room", kind="thing", type="kitchen", label="kitchen", attrs={}))

    world.facts.update(
        helper=helper,
        toddler=toddler,
        caregiver=caregiver,
        meal_cfg=meal,
        soother_cfg=soother,
        pet_cfg=pet,
        target_cfg=target,
        meal_wait=meal.wait,
        soother_power=soother.power,
    )

    scene_setup(world, helper, toddler, caregiver, meal, pet)
    belly_rumble(world, toddler, meal)

    world.para()
    cry_beat(world, toddler, helper)
    helper_notice(world, helper, toddler, caregiver, soother)
    offer_bridge(world, caregiver, toddler, soother)

    world.para()
    pet_nip(world, pet_ent, target_ent, pet, target)
    laugh_or_sniffle(world, toddler, helper, caregiver, pet)
    meal_arrives(world, helper, toddler, caregiver, meal)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            meal=meal.id,
            soother=soother.id,
            target=target.id,
            pet=pet.id,
            helper_name=helper_name,
            helper_gender=helper_gender,
            toddler_name=toddler_name,
            toddler_gender=toddler_gender,
            caregiver=caregiver_type,
            helper_trait=helper_trait,
            seed=None,
        )
    )
    return world


def generation_prompts(world: World) -> list[str]:
    helper = world.facts["helper"]
    toddler = world.facts["toddler"]
    meal = world.facts["meal_cfg"]
    pet = world.facts["pet_cfg"]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "belly", "cry", and "nip".',
        f"Tell a warm kitchen story where {toddler.id} gets hungry waiting for {meal.label}, starts to cry, and a {pet.label}'s silly nip helps turn the mood around.",
        f"Write a funny family story where {helper.id} notices a toddler's upset belly and the ending image shows dinner, relief, and laughter around the table.",
    ]


KNOWLEDGE = {
    "snack": [(
        "Why can a small snack help while dinner is still cooking?",
        "A little snack can calm a hungry tummy for a short time. It helps someone wait without feeling quite so upset."
    )],
    "cat": [(
        "Why do kittens sometimes nip or bat at strings?",
        "Kittens like things that wiggle because moving strings feel like a game to them. A gentle playful nip is different from being mean."
    )],
    "dog": [(
        "Why do puppies chase dangling things?",
        "Puppies are playful and curious, so a swinging lace or towel can look very exciting. They need gentle teaching so play stays safe."
    )],
    "kitchen": [(
        "Why do good smells make you feel hungry?",
        "Smells tell your brain that food is nearby. That can make your stomach notice its hunger even more."
    )],
    "porridge": [(
        "What is porridge?",
        "Porridge is a soft warm food, often made from oats or another grain. People eat it from a bowl with a spoon."
    )],
    "noodles": [(
        "What are noodles?",
        "Noodles are soft strips of dough cooked until tender. Many children like them because they are warm and easy to eat."
    )],
    "dumplings": [(
        "What are dumplings?",
        "Dumplings are little pockets or soft pieces of dough with filling or broth nearby. Grown-ups often cut them into small bites for toddlers."
    )],
    "pancakes": [(
        "What are pancakes?",
        "Pancakes are soft round cakes cooked on a pan. They smell warm and buttery when they are fresh."
    )],
}

KNOWLEDGE_ORDER = ["kitchen", "snack", "cat", "dog", "porridge", "noodles", "dumplings", "pancakes"]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper"]
    toddler = world.facts["toddler"]
    caregiver = world.facts["caregiver"]
    meal = world.facts["meal_cfg"]
    soother = world.facts["soother_cfg"]
    pet = world.facts["pet_cfg"]
    target = world.facts["target_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id}, {toddler.id}, their {caregiver.label_word}, and a playful {pet.label} in the kitchen."
        ),
        (
            f"Why did {toddler.id} start to cry?",
            f"{toddler.id} could smell {meal.label}, but dinner was not ready yet, and that made {toddler.pronoun('possessive')} belly feel very empty. The hungry wait built up until it turned into a cry."
        ),
        (
            f"What did the grown-up give {toddler.id} before dinner?",
            f"{caregiver.label_word.capitalize()} gave {toddler.id} {soother.phrase} as a small bridge bite. It helped take the sharpest edge off the hunger while the hot meal finished."
        ),
        (
            f"What did the {pet.label} nip, and why was it funny?",
            f"The {pet.label} made a tiny nip at {target.phrase}. That made it flutter in a silly way, and the pet looked so startled by its own joke that everyone noticed."
        ),
    ]
    if outcome == "giggle":
        qa.append(
            (
                f"How did the cry change before dinner was served?",
                f"The cry stopped and turned into a laugh. The snack eased the hunger, and the funny little nip gave {toddler.id} something surprising to laugh at instead."
            )
        )
    else:
        qa.append(
            (
                f"Did {toddler.id} stop crying right away?",
                f"Not all the way. The cry softened into sniffles first because the snack helped, and then the real calm came when dinner finally reached the table."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with dinner on the table, a full belly, and everyone calmer than before. The last image shows an ordinary family moment made funny and warm by a tiny pet mistake."
        )
    )
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    meal = world.facts["meal_cfg"]
    pet = world.facts["pet_cfg"]
    tags = {"kitchen", "snack"} | meal.tags | pet.tags
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} cry_started={world.facts.get('cry_started')} laugh_started={world.facts.get('laugh_started')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, S, T) :- meal(M), soother(S), target(T), toddler_safe(S), dangling(T).

comfort(S, 1 + P) :- soother(S), soother_power(S, P).
giggle(M, S) :- meal_wait(M, W), comfort(S, C), C >= W.
sniffly(M, S) :- meal_wait(M, W), comfort(S, C), C < W.

outcome(giggle) :- chosen_meal(M), chosen_soother(S), giggle(M, S).
outcome(sniffly) :- chosen_meal(M), chosen_soother(S), sniffly(M, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for meal_id, meal in MEALS.items():
        lines.append(asp.fact("meal", meal_id))
        lines.append(asp.fact("meal_wait", meal_id, meal.wait))
    for soother_id, soother in SOOTHERS.items():
        lines.append(asp.fact("soother", soother_id))
        lines.append(asp.fact("soother_power", soother_id, soother.power))
        if soother.safe_for_toddler:
            lines.append(asp.fact("toddler_safe", soother_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.dangling:
            lines.append(asp.fact("dangling", target_id))
    for pet_id in PETS:
        lines.append(asp.fact("pet", pet_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_meal", params.meal),
        asp.fact("chosen_soother", params.soother),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        meal="noodles",
        soother="banana",
        target="apron_string",
        pet="kitten",
        helper_name="Mia",
        helper_gender="girl",
        toddler_name="Pip",
        toddler_gender="boy",
        caregiver="mother",
        helper_trait="gentle",
        seed=None,
    ),
    StoryParams(
        meal="dumplings",
        soother="cracker",
        target="tea_towel",
        pet="puppy",
        helper_name="Ben",
        helper_gender="boy",
        toddler_name="June",
        toddler_gender="girl",
        caregiver="father",
        helper_trait="careful",
        seed=None,
    ),
    StoryParams(
        meal="porridge",
        soother="yogurt",
        target="shoelace",
        pet="kitten",
        helper_name="Nora",
        helper_gender="girl",
        toddler_name="Ollie",
        toddler_gender="boy",
        caregiver="grandmother",
        helper_trait="helpful",
        seed=None,
    ),
    StoryParams(
        meal="pancakes",
        soother="cracker",
        target="apron_string",
        pet="puppy",
        helper_name="Sam",
        helper_gender="boy",
        toddler_name="Tess",
        toddler_gender="girl",
        caregiver="grandfather",
        helper_trait="bright",
        seed=None,
    ),
]


HELPER_TRAITS = ["gentle", "careful", "helpful", "bright", "patient", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a hungry toddler, a bridge snack, and a funny little nip in the kitchen."
    )
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--soother", choices=SOOTHERS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--toddler-name")
    ap.add_argument("--toddler-gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target:
        target = TARGETS[args.target]
        if not target.dangling:
            raise StoryError(explain_target(target))
    if args.soother:
        soother = SOOTHERS[args.soother]
        if not soother.safe_for_toddler:
            raise StoryError(explain_soother(soother))

    combos = [
        combo for combo in valid_combos()
        if (args.meal is None or combo[0] == args.meal)
        and (args.soother is None or combo[1] == args.soother)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    meal_id, soother_id, target_id = rng.choice(sorted(combos))
    pet_id = args.pet or rng.choice(sorted(PETS.keys()))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    toddler_gender = args.toddler_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender)
    toddler_name = args.toddler_name or rng.choice([n for n in TODDLER_NAMES if n != helper_name])
    caregiver = args.caregiver or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        meal=meal_id,
        soother=soother_id,
        target=target_id,
        pet=pet_id,
        helper_name=helper_name,
        helper_gender=helper_gender,
        toddler_name=toddler_name,
        toddler_gender=toddler_gender,
        caregiver=caregiver,
        helper_trait=helper_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal: {params.meal})")
    if params.soother not in SOOTHERS:
        raise StoryError(f"(Unknown soother: {params.soother})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")

    soother = SOOTHERS[params.soother]
    target = TARGETS[params.target]
    if not soother.safe_for_toddler:
        raise StoryError(explain_soother(soother))
    if not target.dangling:
        raise StoryError(explain_target(target))
    if (params.meal, params.soother, params.target) not in set(valid_combos()):
        raise StoryError("(These options do not make a reasonable story together.)")

    world = tell(
        meal=MEALS[params.meal],
        soother=soother,
        target=target,
        pet=PETS[params.pet],
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        toddler_name=params.toddler_name,
        toddler_gender=params.toddler_gender,
        caregiver_type=params.caregiver,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} compatible (meal, soother, target) combos:\n")
        for meal_id, soother_id, target_id in combos:
            print(f"  {meal_id:10} {soother_id:8} {target_id}")
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
            header = f"### {p.helper_name} & {p.toddler_name}: {p.meal}, {p.soother}, {p.pet}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
