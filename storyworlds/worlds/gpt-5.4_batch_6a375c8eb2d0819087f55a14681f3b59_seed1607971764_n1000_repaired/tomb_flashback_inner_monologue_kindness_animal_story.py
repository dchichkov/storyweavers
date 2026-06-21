#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py
==================================================================================

A standalone story world for gentle animal stories about a visit to a tomb,
a hungry stranger, a remembered lesson, and a kind choice.

This tiny domain rebuilds a simple shape:
- a small animal brings a gift to an old tomb,
- another small animal is in need nearby,
- tension rises around the gift or the need,
- a flashback and an inner monologue turn the hero toward kindness,
- the ending image proves the tomb has become a place of sharing instead of fear.

Run it
------
    python storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py
    python storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/tomb_flashback_inner_monologue_kindness_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    place: str
    tomb_desc: str
    tomb_name: str
    patch_foods: set[str] = field(default_factory=set)
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
class AnimalRole:
    id: str
    species: str
    label: str
    gait: str
    voice: str
    favorite_foods: set[str] = field(default_factory=set)
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
class Offering:
    id: str
    label: str
    phrase: str
    edible_for: set[str] = field(default_factory=set)
    memorial_text: str = ""
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
class Kindness:
    id: str
    label: str
    need: str
    qa_text: str
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
class StoryParams:
    setting: str
    hero: str
    needy: str
    offering: str
    kindness: str
    hero_name: str
    needy_name: str
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


def _r_reach(world: World) -> list[str]:
    hero = world.get("hero")
    needy = world.get("needy")
    offering = world.get("offering")
    if needy.meters["hunger"] < THRESHOLD:
        return []
    if world.facts.get("offering_edible", False) and offering.attrs.get("present", False):
        sig = ("reach",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        needy.meters["reaching"] += 1
        needy.memes["shame"] += 1
        hero.memes["alarm"] += 1
    return []


def _r_memory(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["alarm"] < THRESHOLD:
        return []
    if hero.memes["grief"] < THRESHOLD:
        return []
    if not world.facts.get("at_tomb", False):
        return []
    sig = ("memory",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["memory"] += 1
    hero.memes["softness"] += 1
    return []


def _r_kindness_ready(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["memory"] < THRESHOLD:
        return []
    sig = ("kindness_ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="reach", tag="physical", apply=_r_reach),
    Rule(name="memory", tag="emotional", apply=_r_memory),
    Rule(name="kindness_ready", tag="emotional", apply=_r_kindness_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the old garden behind the hill",
        tomb_desc="a little stone tomb with moss in the cracks",
        tomb_name="Old Tortoise's tomb",
        patch_foods={"clover", "berries", "seeds"},
        tags={"garden", "plants"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the quiet orchard at the edge of the wood",
        tomb_desc="a round marble tomb under a leaning pear tree",
        tomb_name="Old Tortoise's tomb",
        patch_foods={"berries", "seeds"},
        tags={"orchard", "fruit"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the sunny meadow near the brook",
        tomb_desc="a weathered tomb ringed with daisies",
        tomb_name="Old Tortoise's tomb",
        patch_foods={"clover", "seeds", "beetles"},
        tags={"meadow", "flowers"},
    ),
}

ANIMALS = {
    "rabbit": AnimalRole(
        id="rabbit",
        species="rabbit",
        label="rabbit",
        gait="hopped",
        voice="soft",
        favorite_foods={"clover", "berries"},
        tags={"rabbit", "herbivore"},
    ),
    "squirrel": AnimalRole(
        id="squirrel",
        species="squirrel",
        label="squirrel",
        gait="skipped",
        voice="bright",
        favorite_foods={"seeds", "berries"},
        tags={"squirrel", "tree"},
    ),
    "mouse": AnimalRole(
        id="mouse",
        species="mouse",
        label="mouse",
        gait="scurried",
        voice="tiny",
        favorite_foods={"seeds", "berries"},
        tags={"mouse", "small"},
    ),
    "hedgehog": AnimalRole(
        id="hedgehog",
        species="hedgehog",
        label="hedgehog",
        gait="padded",
        voice="hushed",
        favorite_foods={"beetles", "berries"},
        tags={"hedgehog", "spines"},
    ),
    "sparrow": AnimalRole(
        id="sparrow",
        species="sparrow",
        label="sparrow",
        gait="fluttered",
        voice="quick",
        favorite_foods={"seeds", "berries"},
        tags={"sparrow", "bird"},
    ),
}

OFFERINGS = {
    "clover_bundle": Offering(
        id="clover_bundle",
        label="clover bundle",
        phrase="a fresh bundle of clover",
        edible_for={"rabbit"},
        memorial_text="because Old Tortoise used to smile whenever the meadow smelled green",
        tags={"clover", "gift"},
    ),
    "berry_basket": Offering(
        id="berry_basket",
        label="berry basket",
        phrase="a small basket of red berries",
        edible_for={"rabbit", "squirrel", "mouse", "hedgehog", "sparrow"},
        memorial_text="because Old Tortoise said sweet berries tasted best when shared",
        tags={"berries", "gift"},
    ),
    "seed_cake": Offering(
        id="seed_cake",
        label="seed cake",
        phrase="a crumbly little seed cake",
        edible_for={"squirrel", "mouse", "sparrow"},
        memorial_text="because Old Tortoise loved to feed the tiny birds in winter",
        tags={"seeds", "gift"},
    ),
    "daisy_ring": Offering(
        id="daisy_ring",
        label="daisy ring",
        phrase="a ring of white daisies",
        edible_for=set(),
        memorial_text="because Old Tortoise liked quiet beauty more than big fusses",
        tags={"flowers", "gift"},
    ),
}

KINDNESSES = {
    "share": Kindness(
        id="share",
        label="share the offering",
        need="food",
        qa_text="shared the food they had brought",
        tags={"sharing", "food"},
    ),
    "guide": Kindness(
        id="guide",
        label="lead the hungry animal to food nearby",
        need="food",
        qa_text="led the hungry animal to a nearby patch of food",
        tags={"help", "food"},
    ),
}

NAME_POOL = ["Pip", "Moss", "Hazel", "Nettle", "Pebble", "Fern", "Juniper", "Thimble"]


def offering_feeds(offering: Offering, needy: AnimalRole) -> bool:
    return needy.id in offering.edible_for


def patch_feeds(setting: Setting, needy: AnimalRole) -> bool:
    return bool(setting.patch_foods & needy.favorite_foods)


def kindness_works(setting: Setting, needy: AnimalRole, offering: Offering, kindness: Kindness) -> bool:
    if kindness.id == "share":
        return offering_feeds(offering, needy)
    if kindness.id == "guide":
        return patch_feeds(setting, needy)
    return False


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hero_id in ANIMALS:
            for needy_id, needy in ANIMALS.items():
                if hero_id == needy_id:
                    continue
                for offering_id, offering in OFFERINGS.items():
                    for kindness_id, kindness in KINDNESSES.items():
                        if kindness_works(setting, needy, offering, kindness):
                            combos.append((setting_id, hero_id, needy_id, offering_id, kindness_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "shared" if params.kindness == "share" else "guided"


def explain_rejection(setting: Setting, needy: AnimalRole, offering: Offering, kindness: Kindness) -> str:
    if kindness.id == "share" and not offering_feeds(offering, needy):
        return (
            f"(No story: {offering.phrase} would not feed a {needy.label}, so sharing it "
            f"would not honestly solve the hunger problem. Try an edible offering or "
            f"choose --kindness guide.)"
        )
    if kindness.id == "guide" and not patch_feeds(setting, needy):
        return (
            f"(No story: {setting.place} has no nearby food patch that would help a "
            f"{needy.label}, so guiding would not fix the problem. Try another setting "
            f"or choose --kindness share.)"
        )
    return "(No story: this combination does not create a reasonable act of kindness.)"


def predict_need(setting: Setting, needy_cfg: AnimalRole, offering_cfg: Offering) -> dict:
    return {
        "offering_edible": offering_feeds(offering_cfg, needy_cfg),
        "patch_available": patch_feeds(setting, needy_cfg),
    }


def introduce(world: World, setting: Setting, hero: Entity, offering_cfg: Offering) -> None:
    world.say(
        f"One soft morning, {hero.id} the {hero.type} {hero.attrs['gait']} to "
        f"{setting.place}. In {hero.pronoun('possessive')} paws was {offering_cfg.phrase} "
        f"for {setting.tomb_name}."
    )
    world.say(
        f"At the center of the grass stood {setting.tomb_desc}. {hero.id} always slowed down "
        f"there, because the place felt quiet and full of listening."
    )


def remember_loss(world: World, hero: Entity, offering_cfg: Offering) -> None:
    hero.memes["grief"] += 1
    world.say(
        f"{hero.id} set the gift beside the tomb {offering_cfg.memorial_text}. "
        f"The thought of Old Tortoise still made {hero.pronoun('object')} chest feel small and sore."
    )


def reveal_needy(world: World, needy: Entity, setting: Setting) -> None:
    needy.meters["hunger"] += 1
    needy.meters["tremble"] += 1
    needy.memes["shame"] += 1
    world.say(
        f"Then a rustle came from the ferny side of the tomb. {needy.id} the {needy.type} "
        f"peeked out, looking thin and hungry."
    )


def tension(world: World, hero: Entity, needy: Entity, offering_cfg: Offering) -> None:
    if world.facts["offering_edible"]:
        world.say(
            f"{needy.id}'s nose twitched toward the gift, and one paw lifted as if to reach. "
            f"{hero.id} stiffened at once."
        )
    else:
        world.say(
            f"{needy.id} did not reach for the gift, but the little animal's knees wobbled with hunger. "
            f"{hero.id} still felt a jump of worry, because the tomb was such a tender place."
        )
    world.say(
        f'Inside, {hero.id} thought, "This is for Old Tortoise. What am I supposed to do now?"'
    )
    propagate(world, narrate=False)


def flashback(world: World, hero: Entity, needy: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["softness"] += 1
    world.say(
        f"Then memory opened like a little door. {hero.id} saw, in a flashback, a rainy afternoon "
        f"when Old Tortoise had once shared lunch with a soaked stranger under a dock leaf."
    )
    world.say(
        f'Old Tortoise had said, "A full heart should open its paws." '
        f"Remembering that, {hero.id}'s fear loosened."
    )
    world.say(
        f'Inside, {hero.id} thought, "If Old Tortoise were here, {hero.pronoun()} would choose kindness first."'
    )
    hero.memes["resolve"] += 1
    needy.memes["hope"] += 1


def share_kindness(world: World, hero: Entity, needy: Entity, offering_cfg: Offering) -> None:
    needy.meters["hunger"] = 0.0
    needy.meters["tremble"] = 0.0
    hero.memes["grief"] = max(0.0, hero.memes["grief"] - 0.5)
    hero.memes["warmth"] += 1
    needy.memes["relief"] += 1
    world.say(
        f'{hero.id} nudged the gift closer instead of pulling it away. '
        f'"You may have some," {hero.pronoun()} said. "We can remember Old Tortoise by sharing."'
    )
    world.say(
        f"{needy.id} blinked in surprise, then ate slowly and carefully. Color came back into "
        f"{needy.pronoun('possessive')} face with every bite."
    )


def guide_kindness(world: World, hero: Entity, needy: Entity, setting: Setting) -> None:
    foods = sorted(setting.patch_foods & ANIMALS[needy.type].favorite_foods)
    food_word = foods[0] if foods else "food"
    needy.meters["hunger"] = 0.0
    needy.meters["tremble"] = 0.0
    hero.memes["grief"] = max(0.0, hero.memes["grief"] - 0.5)
    hero.memes["warmth"] += 1
    needy.memes["relief"] += 1
    world.say(
        f'{hero.id} looked from the tomb to the path beyond the grass. '
        f'"Come with me," {hero.pronoun()} said. "I know where there is {food_word} nearby."'
    )
    world.say(
        f"{hero.id} led {needy.id} past the tomb to a small patch where breakfast still waited. "
        f"Soon the hungry little animal was nibbling happily."
    )


def closing(world: World, hero: Entity, needy: Entity, setting: Setting, offering_cfg: Offering, kindness: Kindness) -> None:
    hero.memes["peace"] += 1
    needy.memes["belonging"] += 1
    if kindness.id == "share":
        world.say(
            f"Afterward, {hero.id} and {needy.id} tucked a few petals beside the tomb and sat quietly together. "
            f"The place no longer felt lonely."
        )
    else:
        world.say(
            f"When they came back, {hero.id} set the gift straight again beside the tomb, and "
            f"{needy.id} added a tiny feather as thanks."
        )
    world.say(
        f"In the mild light around {setting.tomb_name}, grief felt softer than before. "
        f"{hero.id} walked home thinking that kindness was the truest song the old tomb could keep."
    )


def tell(
    setting: Setting,
    hero_cfg: AnimalRole,
    needy_cfg: AnimalRole,
    offering_cfg: Offering,
    kindness: Kindness,
    hero_name: str,
    needy_name: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_cfg.id,
            label=hero_cfg.label,
            role="hero",
            attrs={"gait": hero_cfg.gait, "voice": hero_cfg.voice},
        )
    )
    needy = world.add(
        Entity(
            id=needy_name,
            kind="character",
            type=needy_cfg.id,
            label=needy_cfg.label,
            role="needy",
            attrs={"gait": needy_cfg.gait, "voice": needy_cfg.voice},
        )
    )
    world.add(
        Entity(
            id="offering",
            kind="thing",
            type="offering",
            label=offering_cfg.label,
            attrs={"present": True},
        )
    )
    world.add(
        Entity(
            id="tomb",
            kind="thing",
            type="tomb",
            label="tomb",
            attrs={"name": setting.tomb_name},
        )
    )

    world.facts["at_tomb"] = True
    world.facts["offering_edible"] = offering_feeds(offering_cfg, needy_cfg)
    world.facts["patch_available"] = patch_feeds(setting, needy_cfg)
    world.facts["setting"] = setting
    world.facts["hero_cfg"] = hero_cfg
    world.facts["needy_cfg"] = needy_cfg
    world.facts["offering_cfg"] = offering_cfg
    world.facts["kindness_cfg"] = kindness
    world.facts["hero_name"] = hero_name
    world.facts["needy_name"] = needy_name

    introduce(world, setting, hero, offering_cfg)
    remember_loss(world, hero, offering_cfg)

    world.para()
    reveal_needy(world, needy, setting)
    tension(world, hero, needy, offering_cfg)

    world.para()
    flashback(world, hero, needy)
    if kindness.id == "share":
        share_kindness(world, hero, needy, offering_cfg)
    else:
        guide_kindness(world, hero, needy, setting)

    world.para()
    closing(world, hero, needy, setting, offering_cfg, kindness)

    world.facts.update(
        hero=hero,
        needy=needy,
        outcome="shared" if kindness.id == "share" else "guided",
        shared=kindness.id == "share",
        guided=kindness.id == "guide",
        offering_edible=offering_feeds(offering_cfg, needy_cfg),
        patch_available=patch_feeds(setting, needy_cfg),
    )
    return world


KNOWLEDGE = {
    "tomb": [
        (
            "What is a tomb?",
            "A tomb is a place where someone who has died is remembered or laid to rest. People and animals in stories may visit a tomb quietly to think, remember, or leave a small gift."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps readers understand why a character feels or chooses something now."
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means choosing to help, comfort, or share with someone else. A kind act can make another creature feel safer and less alone."
        )
    ],
    "sharing": [
        (
            "Why can sharing food be kind?",
            "Sharing food can help someone who is hungry right away. It also shows that you care about what they need."
        )
    ],
    "memory": [
        (
            "How can a memory change what someone does?",
            "A memory can remind someone of an important lesson. That reminder can help them make a gentler choice."
        )
    ],
    "rabbit": [
        (
            "What do rabbits like to eat?",
            "Rabbits often nibble soft plants like clover and greens. They use their noses and whiskers to search for food."
        )
    ],
    "squirrel": [
        (
            "What do squirrels often eat?",
            "Squirrels often eat seeds, nuts, and some fruits or berries. They are good at finding little snacks in trees and on the ground."
        )
    ],
    "mouse": [
        (
            "What do mice often eat?",
            "Mice often nibble seeds and small bits of plant food. In stories, they are often shown sniffing carefully for safe things to eat."
        )
    ],
    "hedgehog": [
        (
            "What does a hedgehog eat?",
            "A hedgehog often eats small crawling creatures and some fruit. Its prickles help protect it while it searches for food."
        )
    ],
    "sparrow": [
        (
            "What do sparrows eat?",
            "Sparrows often peck at seeds and tiny bits of food. They use their small beaks to pick up crumbs and grains."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "tomb",
    "flashback",
    "kindness",
    "sharing",
    "memory",
    "rabbit",
    "squirrel",
    "mouse",
    "hedgehog",
    "sparrow",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_cfg = f["hero_cfg"]
    needy_cfg = f["needy_cfg"]
    kindness = f["kindness_cfg"]
    offering = f["offering_cfg"]
    if kindness.id == "share":
        return [
            'Write a gentle animal story for a 3-to-5-year-old that includes the word "tomb", uses a flashback, and ends with kindness.',
            f"Tell a story where a {hero_cfg.label} brings {offering.phrase} to a tomb, meets a hungry {needy_cfg.label}, remembers an old lesson, and chooses to share.",
            "Write a simple animal tale with an inner monologue where grief turns into kindness after a remembered moment from the past.",
        ]
    return [
        'Write a gentle animal story for a 3-to-5-year-old that includes the word "tomb", uses a flashback, and ends with kindness.',
        f"Tell a story where a {hero_cfg.label} visits a tomb with a gift, meets a hungry {needy_cfg.label}, and remembers to help by leading the smaller animal to food.",
        "Write a simple animal tale with an inner monologue where a remembered lesson helps a sad character choose kindness first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    needy = f["needy"]
    setting = f["setting"]
    offering = f["offering_cfg"]
    kindness = f["kindness_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {needy.id} the {needy.type} at {setting.tomb_name}. The story follows how a sad visit changes into a kind meeting."
        ),
        (
            f"Why did {hero.id} go to the tomb?",
            f"{hero.id} went there to leave {offering.phrase} and remember Old Tortoise. The visit began as a quiet, grieving moment."
        ),
        (
            f"Why did {hero.id} feel worried when {needy.id} appeared?",
            f"{hero.id} saw a hungry stranger near a tender place and felt protective of the gift by the tomb. That is why {hero.pronoun()} first wondered what to do."
        ),
        (
            "What was the flashback about?",
            f"The flashback showed Old Tortoise sharing lunch with a soaked stranger long ago. That memory reminded {hero.id} that kindness mattered more than guarding things tightly."
        ),
        (
            f"What was {hero.id}'s inner thought?",
            f"{hero.id} first wondered what to do with the gift at the tomb. Then {hero.pronoun()} thought that Old Tortoise would choose kindness first."
        ),
    ]
    if kindness.id == "share":
        qa.append(
            (
                f"How did {hero.id} help {needy.id}?",
                f"{hero.id} shared the food from the offering instead of pulling it away. That helped because the gift was something a hungry {needy.type} could really eat."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} help {needy.id}?",
                f"{hero.id} led {needy.id} to nearby food instead of leaving the little animal to stay hungry. That worked because there was a safe patch of food close to the tomb."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the tomb feeling gentler instead of lonely. The kind choice changed grief into warmth, and both animals left with a softer heart."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tomb", "flashback", "kindness", "memory"}
    tags |= set(world.facts["hero_cfg"].tags)
    tags |= set(world.facts["needy_cfg"].tags)
    tags |= set(world.facts["kindness_cfg"].tags)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        hero="rabbit",
        needy="mouse",
        offering="berry_basket",
        kindness="share",
        hero_name="Hazel",
        needy_name="Pip",
    ),
    StoryParams(
        setting="orchard",
        hero="squirrel",
        needy="hedgehog",
        offering="daisy_ring",
        kindness="guide",
        hero_name="Moss",
        needy_name="Pebble",
    ),
    StoryParams(
        setting="meadow",
        hero="sparrow",
        needy="rabbit",
        offering="clover_bundle",
        kindness="share",
        hero_name="Fern",
        needy_name="Juniper",
    ),
    StoryParams(
        setting="meadow",
        hero="hedgehog",
        needy="sparrow",
        offering="daisy_ring",
        kindness="guide",
        hero_name="Thimble",
        needy_name="Nettle",
    ),
]


ASP_RULES = r"""
works(share,S,N,O) :- offering_feeds(O,N).
works(guide,S,N,O) :- patch_feeds(S,N).
valid(S,H,N,O,K) :- setting(S), hero(H), needy(N), offering(O), kindness(K),
                    H != N, works(K,S,N,O).

outcome(shared) :- chosen_kindness(share).
outcome(guided) :- chosen_kindness(guide).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("hero", aid))
        lines.append(asp.fact("needy", aid))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        for animal_id in sorted(offering.edible_for):
            lines.append(asp.fact("offering_feeds", oid, animal_id))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    for sid, setting in SETTINGS.items():
        for food in sorted(setting.patch_foods):
            lines.append(asp.fact("patch_food", sid, food))
    for aid, animal in ANIMALS.items():
        for food in sorted(animal.favorite_foods):
            lines.append(asp.fact("likes_food", aid, food))
    lines.append("patch_feeds(S,N) :- patch_food(S,F), likes_food(N,F).")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_kindness", params.kindness)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    text = buf.getvalue()
    if "tomb" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include 'tomb'.")
    if "### smoke" not in text:
        raise StoryError("Smoke test failed: emit() did not print the header.")


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
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an animal visits a tomb, remembers kindness, and helps someone in need."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--needy", choices=ANIMALS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--needy-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.needy and args.hero == args.needy:
        raise StoryError("(No story: the helper and the needy animal should be different animals here.)")

    if args.setting and args.needy and args.offering and args.kindness:
        setting = SETTINGS[args.setting]
        needy = ANIMALS[args.needy]
        offering = OFFERINGS[args.offering]
        kindness = KINDNESSES[args.kindness]
        if not kindness_works(setting, needy, offering, kindness):
            raise StoryError(explain_rejection(setting, needy, offering, kindness))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hero is None or combo[1] == args.hero)
        and (args.needy is None or combo[2] == args.needy)
        and (args.offering is None or combo[3] == args.offering)
        and (args.kindness is None or combo[4] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hero_id, needy_id, offering_id, kindness_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(NAME_POOL)
    avoid = {hero_name}
    needy_name_choices = [name for name in NAME_POOL if name not in avoid]
    needy_name = args.needy_name or rng.choice(needy_name_choices)

    return StoryParams(
        setting=setting_id,
        hero=hero_id,
        needy=needy_id,
        offering=offering_id,
        kindness=kindness_id,
        hero_name=hero_name,
        needy_name=needy_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.hero not in ANIMALS:
        raise StoryError(f"(Invalid hero: {params.hero})")
    if params.needy not in ANIMALS:
        raise StoryError(f"(Invalid needy animal: {params.needy})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Invalid offering: {params.offering})")
    if params.kindness not in KINDNESSES:
        raise StoryError(f"(Invalid kindness choice: {params.kindness})")
    if params.hero == params.needy:
        raise StoryError("(No story: the helper and the needy animal should be different animals here.)")

    setting = SETTINGS[params.setting]
    hero_cfg = ANIMALS[params.hero]
    needy_cfg = ANIMALS[params.needy]
    offering = OFFERINGS[params.offering]
    kindness = KINDNESSES[params.kindness]

    if not kindness_works(setting, needy_cfg, offering, kindness):
        raise StoryError(explain_rejection(setting, needy_cfg, offering, kindness))

    world = tell(
        setting=setting,
        hero_cfg=hero_cfg,
        needy_cfg=needy_cfg,
        offering_cfg=offering,
        kindness=kindness,
        hero_name=params.hero_name,
        needy_name=params.needy_name,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hero, needy, offering, kindness) combos:\n")
        for setting_id, hero_id, needy_id, offering_id, kindness_id in combos:
            print(f"  {setting_id:8} {hero_id:9} {needy_id:9} {offering_id:13} {kindness_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            p = sample.params
            header = (
                f"### {p.hero_name} the {p.hero}: {p.kindness} at {p.setting} "
                f"(offering: {p.offering}, outcome: {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
