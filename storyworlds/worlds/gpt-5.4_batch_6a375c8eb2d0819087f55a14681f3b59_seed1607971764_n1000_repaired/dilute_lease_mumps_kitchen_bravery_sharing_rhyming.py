#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py
================================================================================

A standalone story world for a tiny, child-facing kitchen tale told in a gently
rhyming style.

Premise:
A hungry child in the kitchen wants the last bit of a comforting food, while a
sibling with mumps has sore cheeks and needs something gentle to sip. The brave,
sharing choice is to dilute the food the right way so there is enough for both.
A paper lease on the fridge appears in the scene so the seed word belongs to the
world rather than floating in as a random token.

Run it
------
    python storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py
    python storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py --base syrup --liquid water
    python storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py --base cookie
    python storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py --all --qa
    python storyworlds/worlds/gpt-5.4/dilute_lease_mumps_kitchen_bravery_sharing_rhyming.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class BaseFood:
    id: str
    label: str
    phrase: str
    texture: str
    needs: set[str] = field(default_factory=set)
    yields_two_when_diluted: bool = True
    dilutable: bool = True
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
class Liquid:
    id: str
    label: str
    phrase: str
    warmth: str
    fits: set[str] = field(default_factory=set)
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
class CupPair:
    id: str
    first: str
    second: str
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
class LeaseNote:
    id: str
    text: str
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


def _r_strong_for_sore(world: World) -> list[str]:
    drink = world.get("drink")
    sick = world.get("sick")
    if drink.meters["mixed"] < THRESHOLD or drink.meters["diluted"] >= THRESHOLD:
        return []
    if sick.meters["sore_cheeks"] < THRESHOLD:
        return []
    sig = ("strong_for_sore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    drink.meters["too_strong"] += 1
    sick.memes["worry"] += 1
    return []


def _r_dilute_gentle(world: World) -> list[str]:
    drink = world.get("drink")
    if drink.meters["diluted"] < THRESHOLD:
        return []
    sig = ("dilute_gentle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    drink.meters["gentle"] += 1
    drink.meters["portions"] = 2
    sick.memes["hope"] += 1
    return []


def _r_shared_comfort(world: World) -> list[str]:
    drink = world.get("drink")
    hero = world.get("hero")
    sick = world.get("sick")
    if drink.meters["gentle"] < THRESHOLD or drink.meters["shared"] < THRESHOLD:
        return []
    sig = ("shared_comfort",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["sharing"] += 1
    hero.memes["bravery"] += 1
    hero.memes["relief"] += 1
    sick.memes["comfort"] += 1
    sick.memes["relief"] += 1
    hero.meters["fed"] += 1
    sick.meters["fed"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="strong_for_sore", tag="physical", apply=_r_strong_for_sore),
    Rule(name="dilute_gentle", tag="physical", apply=_r_dilute_gentle),
    Rule(name="shared_comfort", tag="social", apply=_r_shared_comfort),
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
                produced.extend(sents)
            elif rule.name in {sig[0] for sig in world.fired}:
                changed = True if False else changed
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


BASES = {
    "syrup": BaseFood(
        id="syrup",
        label="berry syrup",
        phrase="the last spoonful of berry syrup",
        texture="thick and sweet",
        needs={"water"},
        yields_two_when_diluted=True,
        dilutable=True,
        tags={"syrup", "dilute"},
    ),
    "broth_paste": BaseFood(
        id="broth_paste",
        label="golden broth paste",
        phrase="the last dab of golden broth paste",
        texture="salty and strong",
        needs={"warm_water"},
        yields_two_when_diluted=True,
        dilutable=True,
        tags={"broth", "dilute"},
    ),
    "cocoa_mix": BaseFood(
        id="cocoa_mix",
        label="cocoa mix",
        phrase="the last scoop of cocoa mix",
        texture="dark and rich",
        needs={"warm_milk"},
        yields_two_when_diluted=True,
        dilutable=True,
        tags={"cocoa", "dilute"},
    ),
    "cookie": BaseFood(
        id="cookie",
        label="honey cookie",
        phrase="the last honey cookie",
        texture="crumbly and crisp",
        needs=set(),
        yields_two_when_diluted=False,
        dilutable=False,
        tags={"cookie"},
    ),
}

LIQUIDS = {
    "water": Liquid(
        id="water",
        label="water",
        phrase="cool water",
        warmth="cool",
        fits={"syrup"},
        tags={"water"},
    ),
    "warm_water": Liquid(
        id="warm_water",
        label="warm water",
        phrase="warm water",
        warmth="warm",
        fits={"broth_paste"},
        tags={"water", "warm"},
    ),
    "warm_milk": Liquid(
        id="warm_milk",
        label="warm milk",
        phrase="warm milk",
        warmth="warm",
        fits={"cocoa_mix"},
        tags={"milk", "warm"},
    ),
}

CUPS = {
    "stars": CupPair(
        id="stars",
        first="a blue star cup",
        second="a yellow moon cup",
        image="one cup shone blue and one cup gleamed gold",
        tags={"cups"},
    ),
    "garden": CupPair(
        id="garden",
        first="a daisy cup",
        second="a leaf cup",
        image="one cup wore flowers and one wore leaves",
        tags={"cups"},
    ),
    "animals": CupPair(
        id="animals",
        first="a rabbit mug",
        second="a duck mug",
        image="one mug showed a rabbit and one showed a duck",
        tags={"cups"},
    ),
}

LEASE_NOTES = {
    "yellow_flat": LeaseNote(
        id="yellow_flat",
        text="Above the table, the paper lease for their little yellow flat fluttered on the fridge."
    ),
    "oak_street": LeaseNote(
        id="oak_street",
        text="By the magnets hung the lease for Oak Street, with a curled corner that wiggled in the draft."
    ),
    "new_room": LeaseNote(
        id="new_room",
        text="Near the clock, the kitchen fridge held the family lease, tucked under a red magnet."
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Tess"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["kind", "eager", "gentle", "thoughtful", "sunny", "steady"]


def compatible(base_id: str, liquid_id: str) -> bool:
    if base_id not in BASES or liquid_id not in LIQUIDS:
        return False
    base = BASES[base_id]
    liquid = LIQUIDS[liquid_id]
    return base.dilutable and liquid_id in base.needs and base_id in liquid.fits


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for base_id, base in BASES.items():
        if not base.dilutable:
            continue
        for liquid_id in LIQUIDS:
            if compatible(base_id, liquid_id):
                combos.append((base_id, liquid_id))
    return combos


@dataclass
class StoryParams:
    base: str
    liquid: str
    cups: str
    lease_note: str
    hero: str
    hero_gender: str
    sick: str
    sick_gender: str
    parent: str
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


def explain_rejection(base_id: str, liquid_id: Optional[str]) -> str:
    if base_id not in BASES:
        return "(No story: that base food is not known in this kitchen.)"
    base = BASES[base_id]
    if not base.dilutable:
        return (
            f"(No story: {base.label} cannot sensibly dilute into a gentle drink. "
            f"A brave sharing fix needs something that can be thinned for two cups.)"
        )
    if liquid_id is None:
        return "(No story: the kitchen needs a liquid for the mixture.)"
    if liquid_id not in LIQUIDS:
        return "(No story: that liquid is not known in this kitchen.)"
    liquid = LIQUIDS[liquid_id]
    return (
        f"(No story: {liquid.label} does not fit {base.label}. "
        f"Pick a liquid that can dilute it into a gentle, shareable drink.)"
    )


def predict_gentle_share(world: World, diluted: bool) -> dict:
    sim = world.copy()
    drink = sim.get("drink")
    if diluted:
        drink.meters["diluted"] += 1
    propagate(sim, narrate=False)
    return {
        "gentle": drink.meters["gentle"] >= THRESHOLD,
        "portions": int(drink.meters["portions"]),
    }


def setup_scene(world: World, hero: Entity, sick: Entity, parent: Entity, lease_note: LeaseNote) -> None:
    hero.meters["hunger"] = 1
    sick.meters["hunger"] = 1
    sick.meters["sore_cheeks"] = 1
    hero.memes["love"] = 1
    sick.memes["love"] = 1
    world.say(
        f"In the kitchen, morning light lay thin and bright, a silver, gentle stripe."
    )
    world.say(lease_note.text)
    world.say(
        f"{hero.id} stood near the counter, small and {hero.attrs['trait']}, ready for a bite."
    )
    world.say(
        f"On a stool sat {sick.id}, quiet with the mumps, holding {sick.pronoun('possessive')} cheeks just right."
    )
    world.say(
        f"{parent.label_word.capitalize()} moved between the kettle and the sink, making the room feel warm, not white."
    )


def reveal_last_bit(world: World, hero: Entity, base: BaseFood) -> None:
    world.say(
        f"There on the tray was {base.phrase}, {base.texture} in the morning gleam."
    )
    world.say(
        f"{hero.id} licked {hero.pronoun('possessive')} lips and thought, \"That little treat was in my dream.\""
    )


def warn_need(world: World, sick: Entity, parent: Entity, base: BaseFood) -> None:
    world.say(
        f'But {parent.label_word} glanced at {sick.id} and said, "Poor dear, those cheeks still ache, it seems."'
    )
    world.say(
        f'"Something too strong will sting today. {base.label.capitalize()} alone may scratch, not soothe, those seams."'
    )


def hero_hesitates(world: World, hero: Entity, sick: Entity) -> None:
    hero.memes["torn"] += 1
    world.say(
        f"{hero.id} felt hungry as a drum, yet saw {sick.id} sit small and slow."
    )
    world.say(
        f"The wish to keep it all tugged hard; another wish said, \"Share and help it go.\""
    )


def choose_bravery(world: World, hero: Entity, sick: Entity) -> None:
    hero.memes["decision"] += 1
    world.say(
        f"Then {hero.id} took a braver breath and let the kinder answer grow."
    )
    world.say(
        f'"If we can make enough for two," {hero.pronoun()} said, "then {sick.id} gets the first warm glow."'
    )


def mix_without_diluting(world: World, base: BaseFood) -> None:
    drink = world.get("drink")
    drink.meters["mixed"] += 1
    propagate(world, narrate=False)
    if drink.meters["too_strong"] >= THRESHOLD:
        world.say(
            f"For one small blink, the spoon just stirred {base.label} by itself, too thick to flow."
        )
        world.say(
            f"The scent was nice, but everyone could tell it would be sharp for cheeks still sore and low."
        )


def dilute_and_stir(world: World, hero: Entity, parent: Entity, base: BaseFood, liquid: Liquid) -> None:
    drink = world.get("drink")
    drink.meters["mixed"] += 1
    drink.meters["diluted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} and {parent.label_word} poured in {liquid.phrase} to dilute the little store."
    )
    world.say(
        f"The spoon went round with soft clink-clink, and soon the mixture looked like more."
    )
    world.say(
        f"What had been strong grew calm and smooth, a gentle sip instead of a roar."
    )


def pour_and_share(world: World, hero: Entity, sick: Entity, cups: CupPair) -> None:
    drink = world.get("drink")
    drink.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They poured it out in {cups.first} and {cups.second}; {cups.image}."
    )
    world.say(
        f"{hero.id} slid the first cup toward {sick.id} with careful hands and a steady eye."
    )
    world.say(
        f'Then {hero.pronoun()} smiled and whispered, "Sharing makes a small thing stretch, and that is why."'
    )


def ending(world: World, hero: Entity, sick: Entity, parent: Entity) -> None:
    world.say(
        f"{sick.id} took a sip. The tight face eased. {hero.id} took one too and gave a happy sigh."
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed the tops of both their heads and said, "Brave hearts can multiply."'
    )
    world.say(
        "And in the kitchen, warm with steam, two cups sat empty, side by side."
    )


def tell(
    base: BaseFood,
    liquid: Liquid,
    cups: CupPair,
    lease_note: LeaseNote,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    sick_name: str = "Tom",
    sick_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "kind",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        attrs={"trait": trait},
    ))
    sick = world.add(Entity(
        id=sick_name,
        kind="character",
        type=sick_gender,
        role="sick",
        attrs={"illness": "mumps"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    drink = world.add(Entity(
        id="drink",
        kind="thing",
        type="drink",
        label=base.label,
        attrs={"base": base.id, "liquid": liquid.id},
    ))

    world.facts.update(
        hero=hero,
        sick=sick,
        parent=parent,
        base_cfg=base,
        liquid_cfg=liquid,
        cups_cfg=cups,
        lease_cfg=lease_note,
        illness="mumps",
    )

    setup_scene(world, hero, sick, parent, lease_note)
    reveal_last_bit(world, hero, base)

    world.para()
    warn_need(world, sick, parent, base)
    hero_hesitates(world, hero, sick)
    choose_bravery(world, hero, sick)

    world.para()
    mix_without_diluting(world, base)
    pred = predict_gentle_share(world, diluted=True)
    world.facts["predicted_gentle"] = pred["gentle"]
    world.facts["predicted_portions"] = pred["portions"]
    dilute_and_stir(world, hero, parent, base, liquid)
    pour_and_share(world, hero, sick, cups)

    world.para()
    ending(world, hero, sick, parent)

    world.facts.update(
        shared=hero.memes["sharing"] >= THRESHOLD,
        brave=hero.memes["bravery"] >= THRESHOLD,
        gentle=drink.meters["gentle"] >= THRESHOLD,
        portions=int(drink.meters["portions"]),
        fed_both=hero.meters["fed"] >= THRESHOLD and sick.meters["fed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "mumps": [
        (
            "What are mumps?",
            "Mumps is an illness that can make the cheeks and jaw swell and feel sore. A child with mumps may want gentle food and lots of rest."
        )
    ],
    "dilute": [
        (
            "What does dilute mean?",
            "To dilute something means to add more liquid so it becomes thinner and less strong. That can make a drink gentler to sip."
        )
    ],
    "sharing": [
        (
            "What is sharing?",
            "Sharing means letting someone else have part of something you also want. It can turn one small thing into a kind moment for two people."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is making a kind or careful choice even when it feels hard. A brave child may give up the easiest choice to help someone else."
        )
    ],
    "water": [
        (
            "Why can water help dilute a drink?",
            "Water makes a strong drink thinner. That can help it feel less sharp in the mouth."
        )
    ],
    "milk": [
        (
            "Why can warm milk make cocoa gentle?",
            "Warm milk turns cocoa mix into a soft drink instead of a dry, strong powder. The warmth can also feel cozy."
        )
    ],
    "broth": [
        (
            "What is broth?",
            "Broth is a light soup liquid with flavor from food cooked in water. When it is made gently, it can be easy to sip."
        )
    ],
    "cups": [
        (
            "Why do people pour food into two cups when sharing?",
            "Two cups make it easy to divide a drink fairly. Then each person has a clear place for their own sip."
        )
    ],
    "lease": [
        (
            "What is a lease?",
            "A lease is a paper that says a family may live in a home for a certain time. Grown-ups keep it safe because it is important."
        )
    ],
}
KNOWLEDGE_ORDER = ["mumps", "dilute", "sharing", "bravery", "water", "milk", "broth", "cups", "lease"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sick = f["sick"]
    base = f["base_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old set in a kitchen, using the words "dilute", "lease", and "mumps".',
        f"Tell a kitchen story where {hero.id} is hungry, {sick.id} has mumps, and the brave solution is to share {base.label} after making it gentle enough for two.",
        "Write a gentle story in a lightly rhyming voice about bravery and sharing, ending with two children sipping together in the kitchen.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sick = f["sick"]
    parent = f["parent"]
    base = f["base_cfg"]
    liquid = f["liquid_cfg"]
    cups = f["cups_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {sick.id}, and their {parent.label_word} in the kitchen. {hero.id} is hungry, and {sick.id} has mumps and sore cheeks."
        ),
        (
            f"Why was {hero.id} torn at first?",
            f"{hero.id} wanted the last bit of {base.label} very much. But {hero.pronoun().capitalize()} could see that {sick.id} needed something gentle to sip, so hunger and kindness pulled in different directions."
        ),
        (
            f"Why could they not serve {base.label} by itself?",
            f"By itself, the {base.label} would have been too strong for cheeks sore from mumps. The story shows that they needed to dilute it first so it would feel gentler."
        ),
        (
            "How did bravery appear in the story?",
            f"Bravery appeared when {hero.id} chose the kinder plan even though keeping the whole treat would have been easier. {hero.pronoun().capitalize()} offered the first cup to {sick.id}, which proves the brave choice lasted all the way to the end."
        ),
        (
            "How did sharing solve the problem?",
            f"They added {liquid.label} to dilute the last bit and make enough for two cups. That changed one small portion into something both children could sip together."
        ),
        (
            "What changed at the end?",
            f"At the end, the worried kitchen became calm, and both children were fed. The two cups side by side show that kindness turned scarcity into comfort."
        ),
        (
            "What was the lease doing in the kitchen scene?",
            "The lease was hanging on the fridge as part of the family kitchen scene. It helped place the story in a real home instead of feeling like a floating word."
        ),
        (
            f"What cups did they use?",
            f"They used {cups.first} and {cups.second}. The matching pair makes the sharing visible, because each child gets a cup of their own."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mumps", "dilute", "sharing", "bravery", "cups", "lease"}
    base = world.facts["base_cfg"]
    liquid = world.facts["liquid_cfg"]
    if "broth" in base.tags:
        tags.add("broth")
    if "milk" in liquid.tags:
        tags.add("milk")
    if "water" in liquid.tags:
        tags.add("water")
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
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(B,L) :- base(B), dilutable(B), liquid(L), needs(B,L), fits(L,B).

#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for base_id, base in BASES.items():
        lines.append(asp.fact("base", base_id))
        if base.dilutable:
            lines.append(asp.fact("dilutable", base_id))
        for liquid_id in sorted(base.needs):
            lines.append(asp.fact("needs", base_id, liquid_id))
    for liquid_id, liquid in LIQUIDS.items():
        lines.append(asp.fact("liquid", liquid_id))
        for base_id in sorted(liquid.fits):
            lines.append(asp.fact("fits", liquid_id, base_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        base="syrup",
        liquid="water",
        cups="stars",
        lease_note="yellow_flat",
        hero="Lily",
        hero_gender="girl",
        sick="Tom",
        sick_gender="boy",
        parent="mother",
        trait="kind",
        seed=101,
    ),
    StoryParams(
        base="broth_paste",
        liquid="warm_water",
        cups="garden",
        lease_note="oak_street",
        hero="Ben",
        hero_gender="boy",
        sick="Mia",
        sick_gender="girl",
        parent="father",
        trait="steady",
        seed=102,
    ),
    StoryParams(
        base="cocoa_mix",
        liquid="warm_milk",
        cups="animals",
        lease_note="new_room",
        hero="Ava",
        hero_gender="girl",
        sick="Leo",
        sick_gender="boy",
        parent="mother",
        trait="thoughtful",
        seed=103,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Kitchen rhyming storyworld: a brave child dilutes the last comfort food and shares it."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--cups", choices=CUPS)
    ap.add_argument("--lease-note", choices=LEASE_NOTES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--sick")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid (base, liquid) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and args.base not in BASES:
        raise StoryError("(No story: unknown base food.)")
    if args.liquid and args.liquid not in LIQUIDS:
        raise StoryError("(No story: unknown liquid.)")
    if args.base and not BASES[args.base].dilutable:
        raise StoryError(explain_rejection(args.base, args.liquid))
    if args.base and args.liquid and not compatible(args.base, args.liquid):
        raise StoryError(explain_rejection(args.base, args.liquid))

    combos = [
        combo for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.liquid is None or combo[1] == args.liquid)
    ]
    if not combos:
        if args.base:
            raise StoryError(explain_rejection(args.base, args.liquid))
        raise StoryError("(No valid combination matches the given options.)")

    base_id, liquid_id = rng.choice(sorted(combos))
    cups_id = args.cups or rng.choice(sorted(CUPS))
    lease_id = getattr(args, "lease_note") or rng.choice(sorted(LEASE_NOTES))
    hero_name, hero_gender = _pick_name(rng)
    sick_name, sick_gender = _pick_name(rng, avoid=hero_name)
    if args.hero:
        hero_name = args.hero
    if args.sick:
        sick_name = args.sick
        if sick_name == hero_name:
            raise StoryError("(No story: the hungry child and the sick child must be different people.)")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        base=base_id,
        liquid=liquid_id,
        cups=cups_id,
        lease_note=lease_id,
        hero=hero_name,
        hero_gender=hero_gender,
        sick=sick_name,
        sick_gender=sick_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.base not in BASES:
        raise StoryError("(No story: unknown base food.)")
    if params.liquid not in LIQUIDS:
        raise StoryError("(No story: unknown liquid.)")
    if params.cups not in CUPS:
        raise StoryError("(No story: unknown cup pair.)")
    if params.lease_note not in LEASE_NOTES:
        raise StoryError("(No story: unknown lease note.)")
    if not compatible(params.base, params.liquid):
        raise StoryError(explain_rejection(params.base, params.liquid))
    world = tell(
        base=BASES[params.base],
        liquid=LIQUIDS[params.liquid],
        cups=CUPS[params.cups],
        lease_note=LEASE_NOTES[params.lease_note],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sick_name=params.sick,
        sick_gender=params.sick_gender,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(777))
        params.seed = 777
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty random story")
        print("OK: default random generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (base, liquid) combos:\n")
        for base_id, liquid_id in combos:
            print(f"  {base_id:12} {liquid_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.sick}: {p.base} + {p.liquid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
