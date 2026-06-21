#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py
======================================================================================

A small story world about a child who finds a mysterious collar with the letters
"OPA" on it, misunderstands the clue, and follows a gentle mystery to its true
origin. The ending is always happy, but the misunderstanding changes the middle:
sometimes the child fears a hidden dog, sometimes imagines a secret code, and
sometimes worries the collar belongs to a lost pet.

Run it
------
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --place attic --origin memory_box
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --place porch --origin repair_return
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --json
    python storyworlds/worlds/gpt-5.4/collar_opa_origin_misunderstanding_happy_ending_mystery.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "grandfather"}
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
            "grandfather": "opa",
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
    mood: str
    find_spot: str
    sound: str
    supports: set[str] = field(default_factory=set)
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


@dataclass
class Misunderstanding:
    id: str
    guess: str
    fear_text: str
    search_text: str
    needs_mark: bool = True
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
class Origin:
    id: str
    clue: str
    reveal: str
    ending: str
    helper: str
    places: set[str] = field(default_factory=set)
    living_pet: bool = False
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


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    collar = world.get("collar")
    child = world.get("child")
    if collar.meters["found"] >= THRESHOLD and collar.attrs.get("mark") and child.memes["wonder"] < THRESHOLD:
        sig = ("mystery", collar.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wonder"] += 1
            world.get("room").memes["mystery"] += 1
            out.append("__mystery__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.attrs.get("misunderstood") and child.memes["worry"] < THRESHOLD:
        sig = ("worry", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            child.memes["caution"] += 1
            out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if world.facts.get("origin_known") and child.memes["relief"] < THRESHOLD:
        sig = ("relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["joy"] += 1
            child.memes["worry"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mystery", tag="emotion", apply=_r_mystery),
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="The slanted ceiling made soft triangles of shadow.",
        find_spot="under a folded quilt beside a cedar box",
        sound="The house was so quiet that each floorboard creak sounded important.",
        supports={"memory_box"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        mood="The screen door clicked softly in the breeze.",
        find_spot="inside a rain boot by the wall",
        sound="Outside, leaves whispered against the steps.",
        supports={"repair_return", "puppy_surprise"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden shed",
        mood="The little shed smelled of wood, twine, and cool earth.",
        find_spot="hanging from a nail above the seed jars",
        sound="Somewhere outside, a watering can gave one last silver drip.",
        supports={"repair_return"},
    ),
}

MISUNDERSTANDINGS = {
    "secret_code": Misunderstanding(
        id="secret_code",
        guess="a secret code",
        fear_text="The letters OPA looked like they belonged to a hidden message.",
        search_text="If OPA was a code, then perhaps the collar had been left as the first clue.",
        tags={"code", "mystery"},
    ),
    "hidden_dog": Misunderstanding(
        id="hidden_dog",
        guess="the name of a dog hiding nearby",
        fear_text="The letters OPA made the child picture a silent dog padding around just out of sight.",
        search_text="The child listened for paws and noses and tiny jingles in the dark corners.",
        tags={"dog", "mystery"},
    ),
    "lost_pet": Misunderstanding(
        id="lost_pet",
        guess="proof that some pet had been lost",
        fear_text="The collar felt lonely, as if it had slipped away from someone who missed it.",
        search_text="The child searched for signs of who might be waiting for it.",
        tags={"lost_pet", "kindness"},
    ),
}

ORIGINS = {
    "memory_box": Origin(
        id="memory_box",
        clue="A faded photograph in the cedar box showed Opa as a little boy beside a shaggy dog.",
        reveal='Opa smiled and explained that the collar had belonged to Brindle, the dog he loved when he was small. The brass tag said "OPA" because his own grandfather had stamped it there as a joke, long before anyone in the house was born.',
        ending="Together they tucked the collar beside the photograph, and the mystery turned into a warm family story instead of a worry.",
        helper="opa",
        places={"attic"},
        living_pet=False,
        tags={"memory", "family"},
    ),
    "repair_return": Origin(
        id="repair_return",
        clue="A tiny card nearby had a paw print and the words 'Thank you, Opa, for fixing my buckle.'",
        reveal='Opa chuckled and said the collar was not a warning at all. He had repaired it for the neighbor\'s small dog, Pip, and he had set it down for a moment while he fetched a stronger strap.',
        ending="Just then Pip trotted up the path, and the child got to help fasten the collar on before Pip gave everyone happy, wiggly kisses.",
        helper="opa",
        places={"porch", "garden"},
        living_pet=True,
        tags={"repair", "dog", "neighbor"},
    ),
    "puppy_surprise": Origin(
        id="puppy_surprise",
        clue="Behind the boot sat a folded note that read, 'Wait for Opa before opening the gate.'",
        reveal='Opa opened the gate with a grin and said the collar was brand new. He had brought it for a fluffy puppy he was giving the family, and he had hidden it early so the surprise would not be spoiled.',
        ending="A round little puppy bounced in after him, and the child laughed so hard that the whole porch stopped feeling mysterious and started feeling bright.",
        helper="opa",
        places={"porch"},
        living_pet=True,
        tags={"puppy", "gift", "dog"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Ava", "Nora", "Sami", "Ella", "Maya", "Lucy"]
BOY_NAMES = ["Leo", "Milo", "Ben", "Noah", "Eli", "Theo", "Finn", "Max"]
TRAITS = ["careful", "curious", "gentle", "thoughtful", "bright-eyed", "patient"]


def misunderstanding_fits(place_id: str, misunderstanding_id: str) -> bool:
    if misunderstanding_id == "hidden_dog":
        return place_id in {"attic", "garden", "porch"}
    if misunderstanding_id == "secret_code":
        return place_id in {"attic", "porch", "garden"}
    if misunderstanding_id == "lost_pet":
        return place_id in {"porch", "garden", "attic"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for origin_id, origin in ORIGINS.items():
            if origin_id not in setting.supports or place_id not in origin.places:
                continue
            for misunderstanding_id in MISUNDERSTANDINGS:
                if misunderstanding_fits(place_id, misunderstanding_id):
                    combos.append((place_id, misunderstanding_id, origin_id))
    return sorted(combos)


def predict_resolution(world: World, origin: Origin) -> dict:
    sim = world.copy()
    sim.facts["origin_known"] = True
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "relief": child.memes["relief"],
        "joy": child.memes["joy"],
    }


def introduce(world: World, child: Entity, grownup: Entity) -> None:
    trait = child.traits[0] if child.traits else "curious"
    world.say(
        f"One quiet afternoon, {child.id} followed {child.pronoun('possessive')} "
        f"{grownup.label_word} up to {world.setting.place}. {world.setting.mood}"
    )
    world.say(
        f"{world.setting.sound} {child.id} was a {trait} {child.type} who noticed "
        f"small things, and that day a small thing started everything."
    )


def find_collar(world: World, child: Entity) -> None:
    collar = world.get("collar")
    collar.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} reached {world.setting.find_spot} and pulled out a dusty collar "
        f"with a round brass tag. On the tag, three letters caught the light: OPA."
    )
    world.say(
        f"{child.pronoun().capitalize()} turned the collar over and whispered, "
        f'"OPA? What could that mean? Where was the origin of this collar?"'
    )


def misunderstand(world: World, child: Entity, misunderstanding: Misunderstanding) -> None:
    child.attrs["misunderstood"] = True
    propagate(world, narrate=False)
    world.say(misunderstanding.fear_text)
    world.say(
        f"Soon {child.id} decided that OPA must be {misunderstanding.guess}. "
        f"{misunderstanding.search_text}"
    )


def share_with_grownup(world: World, child: Entity, grownup: Entity, misunderstanding: Misunderstanding) -> None:
    world.say(
        f'{child.id} hurried to {grownup.label_word} with the collar in both hands. '
        f'"I found this, and I think OPA means {misunderstanding.guess}," '
        f'{child.pronoun()} said.'
    )
    world.say(
        f"{grownup.label_word.capitalize()} took the collar gently, looked at the tag, "
        f"and did not laugh. Instead, {grownup.pronoun()} knelt down and said, "
        f'"That is a clever thought. Let\'s look for one more clue before we decide."'
    )


def clue_search(world: World, child: Entity, grownup: Entity, origin: Origin) -> None:
    child.memes["focus"] += 1
    world.say(
        f"Together they searched {world.setting.place} more carefully. "
        f"{origin.clue}"
    )
    pred = predict_resolution(world, origin)
    world.facts["predicted_relief"] = pred["relief"]
    world.facts["predicted_joy"] = pred["joy"]


def reveal_origin(world: World, child: Entity, opa: Entity, origin: Origin) -> None:
    world.facts["origin_known"] = True
    propagate(world, narrate=False)
    world.say(
        f"At that moment, {opa.label_word.capitalize()} came in and saw the collar. "
        f"{origin.reveal}"
    )
    world.say(
        f"{child.id} blinked, then smiled at once. The misunderstanding melted away "
        f"because the true origin was kinder than the guess."
    )


def ending(world: World, child: Entity, grownup: Entity, origin: Origin) -> None:
    world.say(origin.ending)
    if origin.living_pet:
        child.memes["joy"] += 1
        world.say(
            f"{child.id} stroked the soft neck under the collar and decided that some "
            f"mysteries end in the nicest possible way."
        )
    else:
        world.say(
            f"{child.id} leaned close to the old photograph and felt proud to know a "
            f"piece of family history."
        )
    world.say(
        f"By evening, the collar was no longer a puzzling object. It had become part "
        f"of a story {child.id} would remember whenever {child.pronoun()} heard the word Opa."
    )


def tell(
    setting: Setting,
    misunderstanding: Misunderstanding,
    origin: Origin,
    child_name: str = "Lina",
    child_type: str = "girl",
    trait: str = "curious",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"misunderstood": False},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=parent_type,
        label="the parent",
        role="grownup",
    ))
    opa = world.add(Entity(
        id="opa",
        kind="character",
        type="grandfather",
        label="Opa",
        role="helper",
    ))
    collar = world.add(Entity(
        id="collar",
        kind="thing",
        type="collar",
        label="collar",
        attrs={"mark": "OPA"},
    ))
    world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=setting.place,
    ))

    world.facts.update(
        child=child,
        child_name=child_name,
        grownup=grownup,
        opa=opa,
        collar=collar,
        setting=setting,
        misunderstanding=misunderstanding,
        origin_cfg=origin,
        origin_known=False,
        happy_ending=True,
    )

    introduce(world, child, grownup)
    find_collar(world, child)

    world.para()
    misunderstand(world, child, misunderstanding)
    share_with_grownup(world, child, grownup, misunderstanding)

    world.para()
    clue_search(world, child, grownup, origin)
    reveal_origin(world, child, opa, origin)

    world.para()
    ending(world, child, grownup, origin)

    world.facts.update(
        misunderstanding_guess=misunderstanding.guess,
        living_pet=origin.living_pet,
        resolved=world.facts["origin_known"],
    )
    return world


KNOWLEDGE = {
    "collar": [
        (
            "What is a collar?",
            "A collar is a band that fits around an animal's neck. People often attach a tag so others know who the pet belongs to.",
        )
    ],
    "opa": [
        (
            "What does Opa mean?",
            "Opa is a family word many children use for their grandfather. Different families use different loving names for grandparents.",
        )
    ],
    "origin": [
        (
            "What does origin mean?",
            "Origin means where something came from or how it first began. If you ask the origin of an object, you are asking about its beginning.",
        )
    ],
    "code": [
        (
            "What is a secret code?",
            "A secret code is a message written in a way not everyone understands right away. You have to figure out what the signs or letters really mean.",
        )
    ],
    "dog": [
        (
            "Why do dogs wear collars?",
            "Dogs wear collars so a leash or tag can be attached. A tag can help people return the dog if it gets lost.",
        )
    ],
    "lost_pet": [
        (
            "What should you do if you find something that might belong to a pet?",
            "Take it to a grown-up and look for clues together. A calm grown-up can help find the pet's family safely.",
        )
    ],
    "memory": [
        (
            "Why do families keep old objects in boxes?",
            "Sometimes an old object helps a family remember someone they loved or a special time long ago. The object becomes part of the family's memory.",
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix it so it works again. A buckle, strap, or toy can often be repaired instead of thrown away.",
        )
    ],
    "puppy": [
        (
            "Why do puppies need collars?",
            "Puppies need light, comfortable collars so people can guide them and attach an identification tag. The collar should fit gently and safely.",
        )
    ],
    "gift": [
        (
            "What is a surprise gift?",
            "A surprise gift is a present someone keeps secret until the happy moment of giving it. The surprise makes the moment feel extra special.",
        )
    ],
    "family": [
        (
            "Why can a misunderstanding happen in a mystery?",
            "A misunderstanding happens when someone guesses before they know all the facts. In a mystery, one clue can look different before the truth is explained.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "collar",
    "opa",
    "origin",
    "code",
    "dog",
    "lost_pet",
    "memory",
    "repair",
    "puppy",
    "gift",
    "family",
]


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    origin: str
    name: str
    gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    misunderstanding = f["misunderstanding"]
    origin = f["origin_cfg"]
    setting = f["setting"]
    return [
        'Write a gentle mystery for a 3-to-5-year-old that includes the words "collar", "opa", and "origin".',
        f"Tell a story about a {child.type} who finds a collar in {setting.place} and mistakenly thinks the letters OPA mean {misunderstanding.guess}, before learning the true origin.",
        f"Write a happy-ending mystery where one small clue seems spooky or puzzling at first, but Opa explains it kindly and the story ends with {origin.ending.lower()}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    opa = f["opa"]
    misunderstanding = f["misunderstanding"]
    origin = f["origin_cfg"]
    setting = f["setting"]
    child_name = f["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, {child.pronoun('possessive')} {grownup.label_word}, and {opa.label_word}. The mystery begins when {child_name} finds a collar and tries to explain it.",
        ),
        (
            "What did the child find?",
            f"{child_name} found a dusty collar with a brass tag that said OPA. The strange letters made the child wonder about the collar's origin right away.",
        ),
        (
            "What was the misunderstanding?",
            f"{child_name} thought OPA meant {misunderstanding.guess}. That guess felt believable at first because the collar was hidden in {setting.place} and there was not enough information yet.",
        ),
        (
            "How did the grown-up help with the mystery?",
            f"{grownup.label_word.capitalize()} did not laugh at the guess. {grownup.pronoun().capitalize()} asked {child_name} to look for one more clue, which helped them slow down and search carefully.",
        ),
        (
            "What was the true origin of the collar?",
            f"{origin.reveal} That answer solved the mystery because it explained why the collar was there and what OPA really meant in that moment.",
        ),
        (
            "How did the story end?",
            f"{origin.ending} The ending is happy because the child moves from worry to relief once the truth is known.",
        ),
    ]
    if origin.living_pet:
        qa.append(
            (
                "Why did the child feel better so quickly at the end?",
                f"{child_name} could see the collar being used in a kind, real way, not a scary one. Seeing the dog and helping with the collar turned the misunderstanding into joy.",
            )
        )
    else:
        qa.append(
            (
                "Why did the collar stop feeling mysterious?",
                f"Once Opa explained the family story behind it, the collar had a clear origin. The child was no longer guessing, so the object felt warm and meaningful instead of puzzling.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"collar", "opa", "origin", "family"}
    tags |= set(f["misunderstanding"].tags)
    tags |= set(f["origin_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        misunderstanding="secret_code",
        origin="memory_box",
        name="Lina",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="porch",
        misunderstanding="hidden_dog",
        origin="puppy_surprise",
        name="Leo",
        gender="boy",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        place="garden",
        misunderstanding="lost_pet",
        origin="repair_return",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        place="porch",
        misunderstanding="secret_code",
        origin="repair_return",
        name="Max",
        gender="boy",
        parent="father",
        trait="careful",
    ),
]


def explain_rejection(place_id: str, misunderstanding_id: str, origin_id: str) -> str:
    parts = []
    if place_id not in SETTINGS:
        parts.append(f"unknown place '{place_id}'")
    if misunderstanding_id not in MISUNDERSTANDINGS:
        parts.append(f"unknown misunderstanding '{misunderstanding_id}'")
    if origin_id not in ORIGINS:
        parts.append(f"unknown origin '{origin_id}'")
    if parts:
        return "(No story: " + "; ".join(parts) + ".)"
    setting = SETTINGS[place_id]
    origin = ORIGINS[origin_id]
    if origin_id not in setting.supports or place_id not in origin.places:
        return (
            f"(No story: {setting.place} does not fit that collar origin. "
            f"This world only tells mysteries where the hiding place plausibly matches where the collar came from.)"
        )
    if not misunderstanding_fits(place_id, misunderstanding_id):
        return (
            f"(No story: that misunderstanding does not fit the mood of {setting.place}. "
            f"Choose a misunderstanding that a child might reasonably imagine from this clue.)"
        )
    return "(No story: that combination is not supported.)"


ASP_RULES = r"""
supports_origin(P, O) :- place(P), origin(O), place_supports(P, O), origin_place(O, P).
fits(P, M) :- place(P), misunderstanding(M), fits_place(P, M).

valid(P, M, O) :- place(P), misunderstanding(M), origin(O), supports_origin(P, O), fits(P, M).

resolved(P, M, O) :- valid(P, M, O), helper(O, opa).
happy(P, M, O) :- resolved(P, M, O).

#show valid/3.
#show resolved/3.
#show happy/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for origin_id in sorted(setting.supports):
            lines.append(asp.fact("place_supports", place_id, origin_id))
    for misunderstanding_id in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", misunderstanding_id))
    for origin_id, origin in ORIGINS.items():
        lines.append(asp.fact("origin", origin_id))
        lines.append(asp.fact("helper", origin_id, origin.helper))
        for place_id in sorted(origin.places):
            lines.append(asp.fact("origin_place", origin_id, place_id))
    for place_id in SETTINGS:
        for misunderstanding_id in MISUNDERSTANDINGS:
            if misunderstanding_fits(place_id, misunderstanding_id):
                lines.append(asp.fact("fits_place", place_id, misunderstanding_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        if "collar" not in sample.story.lower():
            raise StoryError("smoke test story missed required word 'collar'")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved story is empty")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mysterious collar, a misunderstanding, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--origin", choices=ORIGINS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.misunderstanding and args.origin:
        if (args.place, args.misunderstanding, args.origin) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.misunderstanding, args.origin))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.misunderstanding is None or combo[1] == args.misunderstanding)
        and (args.origin is None or combo[2] == args.origin)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, misunderstanding_id, origin_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        misunderstanding=misunderstanding_id,
        origin=origin_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(No story: unknown misunderstanding '{params.misunderstanding}'.)")
    if params.origin not in ORIGINS:
        raise StoryError(f"(No story: unknown origin '{params.origin}'.)")
    if (params.place, params.misunderstanding, params.origin) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.misunderstanding, params.origin))

    world = tell(
        setting=SETTINGS[params.place],
        misunderstanding=MISUNDERSTANDINGS[params.misunderstanding],
        origin=ORIGINS[params.origin],
        child_name=params.name,
        child_type=params.gender,
        trait=params.trait,
        parent_type=params.parent,
    )

    story_text = world.render().replace("child", params.name)
    story_text = story_text.replace("grownup", world.get("grownup").label_word)
    story_text = story_text.replace("opa", "Opa")

    story_text = story_text.replace("child's", f"{params.name}'s")
    story_text = story_text.replace("child ", f"{params.name} ")
    story_text = story_text.replace("child.", f"{params.name}.")
    story_text = story_text.replace("child,", f"{params.name},")
    story_text = story_text.replace(" child", f" {params.name}")

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, misunderstanding, origin) combos:\n")
        for place_id, misunderstanding_id, origin_id in combos:
            print(f"  {place_id:8} {misunderstanding_id:14} {origin_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.name}: {sample.params.place}, "
                f"{sample.params.misunderstanding}, {sample.params.origin}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
