#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py
================================================================================================

A standalone story world for a tiny mythic domain:

A child in a mountain valley notices an omen. Kaka the raven cries overhead,
and a giant arrives with a gift meant to help. The villagers misunderstand the
signs and think the giant means harm. One kind child steps forward, learns the
truth, and helps the village use the giant's gift before the danger arrives.

The seed constraints for this world are built directly into the simulation:
- required words: "bout", "kaka", "ridiculous"
- required features: Kindness, Foreshadowing, Misunderstanding
- style: Myth

Run it
------
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py --omen flood_birds --gift hill_rope
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py --gift sun_veil
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/bout_kaka_ridiculous_kindness_foreshadowing_misunderstanding_myth.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "mother": "mother", "father": "father"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Domain registries
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
class Omen:
    id: str
    danger: str
    sign: str
    detail: str
    kaka_line: str
    warning_image: str
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
    use_line: str
    ending_image: str
    protects: set[str] = field(default_factory=set)
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
class Misreading:
    id: str
    sign: str
    fear_line: str
    mistake_line: str
    truth_line: str
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


OMENS = {
    "flood_birds": Omen(
        id="flood_birds",
        danger="flood",
        sign="river birds flew uphill in a hurry",
        detail="Even the fish-silver river looked tight and restless between its banks",
        kaka_line='Kaka the raven wheeled over the reeds and cried, "Kaka! Kaka!" as if the sky itself had learned a warning word.',
        warning_image="the low fields would drown under brown water by nightfall",
        tags={"flood", "raven", "river"},
    ),
    "frost_moon": Omen(
        id="frost_moon",
        danger="frost",
        sign="a pale ring formed around the afternoon sun",
        detail="The bean leaves had already curled their edges as if listening for cold",
        kaka_line='Kaka the raven sat on the garden wall and called, "Kaka! Kaka!" into the bright air, which sounded strange on such a warm day.',
        warning_image="a hard white frost would bite the valley before dawn",
        tags={"frost", "raven", "garden"},
    ),
    "wind_pines": Omen(
        id="wind_pines",
        danger="wind",
        sign="the highest pines hissed though the valley floor was still",
        detail="Dust made tiny circles in the square and would not lie flat again",
        kaka_line='Kaka the raven beat against the calm with urgent wings and shouted, "Kaka! Kaka!" from roof to roof.',
        warning_image="a mountain wind would come roaring down after sunset",
        tags={"wind", "raven", "roofs"},
    ),
}

GIFTS = {
    "hill_rope": Gift(
        id="hill_rope",
        label="hill rope",
        phrase="a braided hill rope thick as a child's waist",
        use_line="stretched the rope from the square to the stone steps above the river path",
        ending_image="families climbed hand over hand to high ground while the water rushed below",
        protects={"flood"},
        tags={"rope", "flood"},
    ),
    "ember_bowl": Gift(
        id="ember_bowl",
        label="ember bowl",
        phrase="a bronze ember bowl full of coals that never sulked into ash",
        use_line="set the ember bowl in the middle of the seedlings and shared its warm breath from shed to shed",
        ending_image="the beans stood green at sunrise, with bright drops instead of ice on their leaves",
        protects={"frost"},
        tags={"fire", "warmth", "frost"},
    ),
    "roof_pegs": Gift(
        id="roof_pegs",
        label="roof pegs",
        phrase="a sack of cedar roof pegs as long as flute sticks",
        use_line="hammered the pegs through thatch ropes and tied every roof down tight",
        ending_image="the roofs bowed but stayed, and not one sleeping mat flew into the dark",
        protects={"wind"},
        tags={"wind", "roofs", "wood"},
    ),
    "sun_veil": Gift(
        id="sun_veil",
        label="sun veil",
        phrase="a shimmering sun veil woven from gold grass",
        use_line="hung the shining cloth between two poles and admired it",
        ending_image="the cloth glowed beautifully, but it did not answer the danger at all",
        protects=set(),
        tags={"cloth"},
    ),
}

MISREADINGS = {
    "shadow": Misreading(
        id="shadow",
        sign="the giant's shadow rolled over the square before the giant himself appeared",
        fear_line='A few grown-ups whispered that only trouble arrives before its own feet.',
        mistake_line='When the giant lifted both hands, the villagers thought he meant to cover their homes and steal the sun.',
        truth_line='Later they learned he had only been trying to show how high the water or wind or cold might reach.',
        tags={"shadow", "fear"},
    ),
    "thunder_voice": Misreading(
        id="thunder_voice",
        sign="the giant called from the ridge in a voice so deep that shutters trembled",
        fear_line='Some people clutched one another and said a shout that large could only be a threat.',
        mistake_line='They thought the giant was demanding tribute, when he was only trying to make himself heard from far away.',
        truth_line='Later they understood that a huge voice is not the same as an angry heart.',
        tags={"voice", "fear"},
    ),
    "muddy_steps": Misreading(
        id="muddy_steps",
        sign="great muddy footprints appeared on the path before dawn",
        fear_line='The baker said the prints looked like marching, and marching always made people imagine the worst.',
        mistake_line='When the giant came carrying his burden, the villagers decided he had already begun an attack.',
        truth_line='Later they saw the mud had splashed from the riverbank where he had hurried to prepare a warning.',
        tags={"footprints", "fear"},
    ),
}

GIRL_NAMES = ["Nara", "Tali", "Ila", "Mira", "Suri", "Luma"]
BOY_NAMES = ["Tarin", "Elo", "Beni", "Kio", "Maro", "Sami"]
TRAITS = ["gentle", "patient", "watchful", "brave", "soft-spoken", "thoughtful"]


# ---------------------------------------------------------------------------
# World
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


def _r_omen_fear(world: World) -> list[str]:
    village = world.get("Village")
    if village.meters["danger"] < THRESHOLD:
        return []
    sig = ("omen_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.memes["fear"] += 1
    hero = world.get("Hero")
    hero.memes["worry"] += 1
    return []


def _r_misreading_conflict(world: World) -> list[str]:
    village = world.get("Village")
    giant = world.get("Giant")
    if village.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("misreading_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    giant.memes["sadness"] += 1
    village.memes["fear"] += 1
    return []


def _r_kindness_bridge(world: World) -> list[str]:
    hero = world.get("Hero")
    giant = world.get("Giant")
    village = world.get("Village")
    if hero.memes["kindness"] < THRESHOLD or village.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("kindness_bridge",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    giant.memes["trust"] += 1
    return []


def _r_gift_saves(world: World) -> list[str]:
    village = world.get("Village")
    gift = world.get("Gift")
    if village.meters["danger"] < THRESHOLD or gift.meters["deployed"] < THRESHOLD:
        return []
    sig = ("gift_saves",)
    if sig in world.fired:
        return []
    danger = world.facts["danger"]
    if danger not in gift.protects:
        return []
    world.fired.add(sig)
    village.meters["safe"] += 1
    village.meters["danger"] = 0.0
    village.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="omen_fear", tag="emotion", apply=_r_omen_fear),
    Rule(name="misreading_conflict", tag="emotion", apply=_r_misreading_conflict),
    Rule(name="kindness_bridge", tag="social", apply=_r_kindness_bridge),
    Rule(name="gift_saves", tag="physical", apply=_r_gift_saves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current_fired_count = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > current_fired_count:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def gift_fits_omen(omen: Omen, gift: Gift) -> bool:
    return omen.danger in gift.protects


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for omen_id, omen in OMENS.items():
        for gift_id, gift in GIFTS.items():
            if not gift_fits_omen(omen, gift):
                continue
            for mis_id in MISREADINGS:
                combos.append((omen_id, gift_id, mis_id))
    return combos


def explain_rejection(omen: Omen, gift: Gift) -> str:
    return (
        f"(No story: {gift.phrase} does not truly protect a village from {omen.danger}. "
        f"In this world, the giant's gift must honestly solve the danger it warns about.)"
    )


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def foretell(world: World, omen: Omen) -> None:
    world.get("Village").meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the age when hills were said to listen, the valley of Reed Hollow woke to a sign: {omen.sign}. "
        f"{omen.detail}."
    )
    world.say(omen.kaka_line)
    world.say(
        f"The old people did not yet know the whole trouble, but each of them felt that {omen.warning_image}."
    )


def introduce_hero(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"There lived a child named {hero.id}, a {next((t for t in hero.traits if t), 'kind')} {hero.type} "
        f"who carried bread first to others and only after to {hero.pronoun('object')}self."
    )
    world.say(
        f"{hero.id}'s {elder.label_word} used to say, "
        f'"When fear runs ahead of truth, let kindness walk after it and see what fear forgot."'
    )


def arrival(world: World, misreading: Misreading, gift: Gift) -> None:
    world.say(
        f"Before noon, {misreading.sign}. Soon Boru the mountain giant came down the path with {gift.phrase} over one shoulder."
    )
    world.say(misreading.fear_line)


def misunderstanding(world: World, misreading: Misreading) -> None:
    village = world.get("Village")
    village.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(misreading.mistake_line)
    world.say(
        'One potter cried, "He means to frighten us!" and another answered, '
        '"Or worse." Even Kaka\'s harsh call sounded like mockery then, and someone muttered that the whole scene was ridiculous.'
    )


def choose_kindness(world: World, hero: Entity, giant: Entity) -> None:
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id} remembered the elder saying and stepped forward with a bowl of water held in both hands."
    )
    world.say(
        f'"Boru," {hero.pronoun()} said, "if you bring harm, I will know soon enough. '
        f'If you bring help, you should not stand thirsty while we guess at your heart."'
    )
    world.say(
        f"The giant blinked, small tears shining in the corners of his enormous eyes, and bent low to drink without spilling a drop."
    )


def reveal_truth(world: World, misreading: Misreading, omen: Omen, gift: Gift) -> None:
    giant = world.get("Giant")
    giant.memes["relief"] += 1
    world.say(
        f'In his deep voice Boru said, "Little one, Kaka woke me at dawn. The signs mean {omen.warning_image}. '
        f'I brought this {gift.label} so your people could live through it."'
    )
    world.say(misreading.truth_line)


def deploy_gift(world: World, gift: Gift) -> None:
    world.get("Gift").meters["deployed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the village moved all at once. Boru and the people {gift.use_line}."
    )


def resolution(world: World, hero: Entity, elder: Entity, gift: Gift) -> None:
    village = world.get("Village")
    if village.meters["safe"] < THRESHOLD:
        raise StoryError("The deployed gift did not protect the village; the story has no honest resolution.")
    world.say(
        f"By evening the danger came exactly as foretold, but the gift held true: {gift.ending_image}."
    )
    world.say(
        f"The next morning the villagers brought honey cakes to Boru and tied a bright thread around Kaka's leg so they would remember the raven's warning."
    )
    world.say(
        f"From then on, when fright leapt up after only a short bout of seeing, the people of Reed Hollow would say, "
        f'"Do not answer shadows before you answer kindness." And {elder.label_word} would smile at {hero.id}, for the child had taught the grown-ups a lesson old as myth and fresh as dawn.'
    )


def tell(
    omen: Omen,
    gift: Gift,
    misreading: Misreading,
    *,
    hero_name: str = "Nara",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "gentle",
) -> World:
    if not gift_fits_omen(omen, gift):
        raise StoryError(explain_rejection(omen, gift))

    world = World()
    hero = world.add(
        Entity(
            id="Hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"name": hero_name},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            attrs={},
        )
    )
    giant = world.add(
        Entity(
            id="Giant",
            kind="character",
            type="giant",
            label="Boru",
            role="helper",
            attrs={},
        )
    )
    village = world.add(
        Entity(
            id="Village",
            kind="thing",
            type="village",
            label="Reed Hollow",
            role="place",
            attrs={},
        )
    )
    gift_ent = world.add(
        Entity(
            id="Gift",
            kind="thing",
            type="gift",
            label=gift.label,
            role="gift",
            protects=set(gift.protects),
            attrs={},
        )
    )
    raven = world.add(
        Entity(
            id="Raven",
            kind="character",
            type="bird",
            label="Kaka",
            role="messenger",
            attrs={},
        )
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        giant=giant,
        village=village,
        gift_cfg=gift,
        omen=omen,
        misreading=misreading,
        danger=omen.danger,
        raven=raven,
        protected=False,
    )

    foretell(world, omen)
    introduce_hero(world, hero, elder)
    world.para()
    arrival(world, misreading, gift)
    misunderstanding(world, misreading)
    world.para()
    choose_kindness(world, hero, giant)
    reveal_truth(world, misreading, omen, gift)
    deploy_gift(world, gift)
    world.facts["protected"] = world.get("Village").meters["safe"] >= THRESHOLD
    world.para()
    resolution(world, hero, elder, gift)

    world.facts.update(
        misunderstanding_happened=world.get("Village").memes["misunderstanding"] >= THRESHOLD,
        kindness_happened=world.get("Hero").memes["kindness"] >= THRESHOLD,
        gratitude=world.get("Village").memes["gratitude"] >= THRESHOLD,
        giant_trusted=world.get("Giant").memes["trust"] >= THRESHOLD,
        gift_deployed=world.get("Gift").meters["deployed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    omen: str
    gift: str
    misreading: str
    hero_name: str
    hero_gender: str
    elder_type: str
    trait: str
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
    "raven": [
        (
            "Why do myths often use birds as messengers?",
            "Birds can see far and travel quickly, so stories often imagine them carrying signs between places. In myths, that makes them feel like a bridge between the ordinary world and the warning world."
        )
    ],
    "flood": [
        (
            "Why do people go to high ground in a flood?",
            "Water runs downhill and fills low places first. High ground is safer because the flood cannot reach it as easily."
        )
    ],
    "frost": [
        (
            "What can frost do to young plants?",
            "Frost freezes the water inside tender leaves and stems. That can make young plants go limp, dark, and dead."
        )
    ],
    "wind": [
        (
            "Why can strong wind damage roofs?",
            "Strong wind pushes and tugs at loose edges. If a roof is not tied down well, the wind can peel it away."
        )
    ],
    "rope": [
        (
            "What is a rope useful for in an emergency?",
            "A rope gives people something strong to hold while they climb or cross. It helps them move safely when the ground is dangerous."
        )
    ],
    "warmth": [
        (
            "Why does warmth help on a freezing night?",
            "Warmth keeps water from turning to ice so quickly. It also helps living things, like people and plants, stay safe from cold."
        )
    ],
    "roofs": [
        (
            "Why do pegs and ties help keep roofs on?",
            "Pegs and ties hold the roof materials in place. When the wind pulls, the roof has something firm to pull against."
        )
    ],
    "kindness": [
        (
            "How can kindness help when people misunderstand each other?",
            "Kindness slows everyone down long enough to listen. Once people feel less threatened, they can notice what is really true."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone believes the wrong thing about what another person meant. It can cause fear or anger even when no harm was intended."
        )
    ],
}

KNOWLEDGE_ORDER = ["raven", "flood", "frost", "wind", "rope", "warmth", "roofs", "kindness", "misunderstanding"]


def generation_prompts(world: World) -> list[str]:
    omen = world.facts["omen"]
    gift = world.facts["gift_cfg"]
    misreading = world.facts["misreading"]
    hero = world.facts["hero"]
    return [
        f'Write a short myth for a young child that includes the words "bout", "kaka", and "ridiculous".',
        f"Tell a mythic story where a child named {hero.attrs['name']} shows kindness after a village misunderstands a giant carrying {gift.phrase}.",
        f"Write a story with foreshadowing from {omen.sign}, a misunderstanding caused by {misreading.sign}, and a gentle ending where kindness reveals the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    omen = world.facts["omen"]
    gift = world.facts["gift_cfg"]
    misreading = world.facts["misreading"]
    giant = world.facts["giant"]
    hero_name = hero.attrs["name"]

    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, the giant Boru, Kaka the raven, and the people of Reed Hollow. The story follows how one kind child changes what the whole village believes."
        ),
        (
            "What showed that trouble was coming?",
            f"The omen was that {omen.sign}. Kaka's urgent crying and the strange look of the valley foreshadowed that {omen.warning_image}."
        ),
        (
            "What did the villagers misunderstand?",
            f"They misunderstood Boru's arrival and thought his signs meant harm. Because of {misreading.sign}, they guessed at his heart before they listened to his warning."
        ),
        (
            f"How did {hero_name} show kindness?",
            f"{hero_name} stepped forward with water for Boru instead of shouting at him. That kind act gave Boru a safe moment to explain why he had come."
        ),
        (
            "Why was the giant really there?",
            f"Boru came to help the village survive the coming {omen.danger}. He brought {gift.phrase}, which was the right tool for that danger."
        ),
    ]
    if world.facts.get("protected"):
        out.append(
            (
                "How did the story end?",
                f"The villagers used the {gift.label} in time, and the danger arrived just as Boru had warned. After they were safe, they thanked Boru and remembered that kindness had cleared up the misunderstanding."
            )
        )
    if world.facts.get("giant_trusted"):
        out.append(
            (
                f"Why did Boru answer {hero_name} honestly?",
                f"He answered because {hero_name}'s kindness showed that not everyone wished him away. Once Boru felt trusted for even a moment, he could speak instead of standing there in sadness."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["omen"].tags) | set(world.facts["gift_cfg"].tags) | {"kindness", "misunderstanding"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.protects:
            bits.append(f"protects={sorted(ent.protects)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        omen="flood_birds",
        gift="hill_rope",
        misreading="muddy_steps",
        hero_name="Nara",
        hero_gender="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        omen="frost_moon",
        gift="ember_bowl",
        misreading="shadow",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="grandmother",
        trait="watchful",
    ),
    StoryParams(
        omen="wind_pines",
        gift="roof_pegs",
        misreading="thunder_voice",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
        trait="patient",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(O, G) :- omen(O), gift(G), danger_of(O, D), protects(G, D).
valid(O, G, M) :- omen(O), gift(G), misreading(M), fits(O, G).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("danger_of", omen_id, omen.danger))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for danger in sorted(gift.protects):
            lines.append(asp.fact("protects", gift_id, danger))
    for mis_id in MISREADINGS:
        lines.append(asp.fact("misreading", mis_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: omen, misunderstanding, giant gift, and kindness."
    )
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--gift", choices=sorted(GIFTS))
    ap.add_argument("--misreading", choices=sorted(MISREADINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "mother", "father"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.omen and args.gift:
        omen = OMENS[args.omen]
        gift = GIFTS[args.gift]
        if not gift_fits_omen(omen, gift):
            raise StoryError(explain_rejection(omen, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.omen is None or combo[0] == args.omen)
        and (args.gift is None or combo[1] == args.gift)
        and (args.misreading is None or combo[2] == args.misreading)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    omen_id, gift_id, mis_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        omen=omen_id,
        gift=gift_id,
        misreading=mis_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.omen not in OMENS:
        raise StoryError(f"Unknown omen: {params.omen}")
    if params.gift not in GIFTS:
        raise StoryError(f"Unknown gift: {params.gift}")
    if params.misreading not in MISREADINGS:
        raise StoryError(f"Unknown misreading: {params.misreading}")
    world = tell(
        OMENS[params.omen],
        GIFTS[params.gift],
        MISREADINGS[params.misreading],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        trait=params.trait,
    )

    hero = world.get("Hero")
    story_text = world.render().replace("Hero", hero.attrs["name"])

    return StorySample(
        params=params,
        story=story_text.replace("Hero", hero.attrs["name"]),
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
        print(f"{len(combos)} valid (omen, gift, misreading) combos:\n")
        for omen, gift, misreading in combos:
            print(f"  {omen:12} {gift:11} {misreading}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.omen} + {p.gift} ({p.misreading})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
