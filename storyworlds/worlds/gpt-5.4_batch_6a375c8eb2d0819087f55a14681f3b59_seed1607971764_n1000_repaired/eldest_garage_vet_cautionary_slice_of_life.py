#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py
========================================================================

A standalone story world for a gentle, cautionary slice-of-life tale about an
eldest child, a family pet, a messy garage, and a quick trip to the vet when a
garage danger is not taken seriously fast enough.

The world rebuilds one small domestic pattern:

- ordinary family chore in the garage
- younger child notices something tempting for the pet
- the eldest child predicts the danger and warns
- either the warning averts the mistake, or the pet swallows something unsafe
- the family calls the vet, and the ending image shows safer habits afterward

Run it
------
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py --pet puppy --hazard raisins
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py --hazard crayons
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py --response wait
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/eldest_garage_vet_cautionary_slice_of_life.py --verify
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
SENSE_MIN = 2
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "gentle"}


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
    toxic: bool = False
    attractive_to_pet: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"puppy", "dog", "kitten", "cat"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Chore:
    id: str
    setup: str
    clutter: str
    ending: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    found_where: str
    temptation: str
    bad_for: set[str]
    toxic: bool
    attractive_to_pet: bool
    toxicity: int
    lesson: str
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
class PetType:
    id: str
    label: str
    sound: str
    gait: str
    treats_like: str
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
class Response:
    id: str
    sense: int
    speed: int
    text: str
    qa_text: str
    fail_text: str
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
    def __init__(self, chore: Chore) -> None:
        self.chore = chore
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"eldest", "younger"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.chore)
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


def _r_pet_poison(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("pet")
    hazard = world.get("hazard")
    if pet.meters["ate_hazard"] < THRESHOLD or not hazard.toxic:
        return out
    sig = ("poison", pet.id, hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pet.meters["risk"] += hazard.meters["toxicity"]
    pet.meters["sick"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("parent").meters["urgency"] += 1
    out.append("__danger__")
    return out


def _r_vet_needed(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("pet")
    if pet.meters["risk"] < THRESHOLD:
        return out
    sig = ("vet_needed", pet.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pet.meters["needs_vet"] += 1
    out.append("__vet__")
    return out


CAUSAL_RULES = [
    Rule(name="pet_poison", tag="physical", apply=_r_pet_poison),
    Rule(name="vet_needed", tag="social", apply=_r_vet_needed),
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


def hazard_at_risk(pet: PetType, hazard: Hazard) -> bool:
    return hazard.toxic and hazard.attractive_to_pet and pet.id in hazard.bad_for


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def would_avert(eldest_age: int, younger_age: int, trust: int, trait: str) -> bool:
    age_gap = eldest_age - younger_age
    careful = trait in CAUTIOUS_TRAITS
    return careful and age_gap >= 2 and trust >= 5


def severity_of(hazard: Hazard, delay: int) -> int:
    return hazard.toxicity + delay


def is_treated_at_home(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.speed >= severity_of(hazard, delay)


def predict_danger(world: World) -> dict:
    sim = world.copy()
    pet = sim.get("pet")
    pet.meters["ate_hazard"] += 1
    propagate(sim, narrate=False)
    return {
        "needs_vet": sim.get("pet").meters["needs_vet"] >= THRESHOLD,
        "risk": sim.get("pet").meters["risk"],
    }


def introduce(world: World, eldest: Entity, younger: Entity, parent: Entity,
              pet: Entity, chore: Chore) -> None:
    world.say(
        f"On a slow Saturday morning, {parent.label_word} asked {eldest.id}, the eldest, "
        f"and {younger.id} to help in the garage. {chore.setup}"
    )
    world.say(
        f"{pet.id}, the family {pet.label}, padded after them with a soft {pet.attrs['sound']} "
        f"and kept sniffing at the corners."
    )


def daily_detail(world: World, chore: Chore) -> None:
    world.say(chore.clutter)


def find_hazard(world: World, younger: Entity, pet: Entity, hazard: Hazard) -> None:
    younger.memes["curiosity"] += 1
    world.say(
        f"While they worked, {younger.id} spotted {hazard.phrase} {hazard.found_where}. "
        f'"Look," {younger.pronoun()} said. "Maybe {pet.id} wants {hazard.temptation}."'
    )


def eldest_warn(world: World, eldest: Entity, younger: Entity, pet: Entity,
                hazard: Hazard, parent: Entity) -> None:
    pred = predict_danger(world)
    world.facts["predicted_risk"] = pred["risk"]
    eldest.memes["care"] += 1
    world.say(
        f"{eldest.id} shook {eldest.pronoun('possessive')} head at once. "
        f'"No, {pet.id} can\'t have {hazard.label}," {eldest.pronoun()} said. '
        f'"That could make {pet.pronoun("object")} sick, and then we would need the vet."'
    )
    if pred["needs_vet"]:
        world.say(
            f"{eldest.pronoun().capitalize()} had seen enough to know this was not a little tummy mistake."
        )
    world.say(
        f"{parent.label_word.capitalize()} looked over from the shelf and listened more carefully."
    )


def back_down(world: World, eldest: Entity, younger: Entity, pet: Entity,
              hazard: Hazard, parent: Entity, chore: Chore) -> None:
    eldest.memes["relief"] += 1
    younger.memes["relief"] += 1
    younger.memes["trust"] += 1
    world.say(
        f"{younger.id} looked at {eldest.id}, then at {pet.id}'s hopeful nose, and pulled "
        f"{hazard.phrase} back."
    )
    world.say(
        f'"Okay," {younger.pronoun()} said. "{pet.id} can have a real treat later." '
        f"{parent.label_word.capitalize()} took {hazard.phrase} and set it on a high shelf."
    )
    world.say(
        f"Soon the hard moment passed, and the family went back to {chore.ending}."
    )


def defy(world: World, younger: Entity, pet: Entity, hazard: Hazard) -> None:
    younger.memes["defiance"] += 1
    world.say(
        f"But the warning felt far away for one careless second. {younger.id} bent down anyway, "
        f"and {pet.id} darted closer."
    )


def ingest(world: World, pet: Entity, hazard_ent: Entity, hazard: Hazard) -> None:
    pet.meters["ate_hazard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone could stop it, {pet.id} {pet.attrs['eats']} {hazard.label}."
    )
    if pet.meters["needs_vet"] >= THRESHOLD:
        world.say(
            f"{pet.pronoun().capitalize()} swallowed fast, licked {pet.pronoun('possessive')} lips, "
            f"and then looked small and confused."
        )


def alarm(world: World, eldest: Entity, parent: Entity, pet: Entity) -> None:
    world.say(
        f'"{parent.label_word.capitalize()}, {pet.id} ate it!" {eldest.id} cried.'
    )
    world.say(
        f"{parent.label_word.capitalize()} was moving before the last word had even finished."
    )


def vet_help(world: World, parent: Entity, response: Response, pet: Entity) -> None:
    pet.meters["risk"] = 0.0
    pet.meters["sick"] = 0.0
    pet.meters["needs_vet"] = 0.0
    pet.meters["treated"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.text}."
    )
    world.say(
        f"At the vet clinic, the bright room smelled clean and strange, but the grown-ups worked quickly."
    )


def overnight_care(world: World, parent: Entity, pet: Entity, response: Response) -> None:
    pet.meters["overnight"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail_text}."
    )
    world.say(
        f"The vet said {pet.id} would need to stay for the night so everyone could watch {pet.pronoun('object')} carefully."
    )


def comfort_and_lesson(world: World, eldest: Entity, younger: Entity, parent: Entity,
                       pet: Entity, hazard: Hazard) -> None:
    for kid in (eldest, younger):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
    world.say(
        f"When they were finally home again, {parent.label_word} sat with both children on the bottom step by the garage door."
    )
    world.say(
        f'"You did the right thing by telling me fast," {parent.pronoun()} said. '
        f'"But remember this too: {hazard.lesson}"'
    )


def safer_after(world: World, eldest: Entity, younger: Entity, parent: Entity,
                pet: Entity, chore: Chore, hazard: Hazard) -> None:
    eldest.memes["safety"] += 1
    younger.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word} brought a lidded bin for the garage and a hook high on the wall for snack bags and little boxes."
    )
    if world.get("pet").meters["overnight"] >= THRESHOLD:
        world.say(
            f"{pet.id} came home sleepy from the vet, with a wag that was smaller than usual but still there."
        )
    else:
        world.say(
            f"{pet.id} came home from the vet tired but steady, and soon {pet.pronoun()} was asking for water and a blanket."
        )
    world.say(
        f"{eldest.id} checked the low shelves, {younger.id} shut the bin lid tight, and the garage felt different after that: still busy, still ordinary, but much safer for {pet.id}."
    )
    world.say(chore.ending)


def tell(chore: Chore, hazard: Hazard, pet_cfg: PetType, response: Response,
         eldest_name: str = "Nora", eldest_gender: str = "girl",
         younger_name: str = "Ben", younger_gender: str = "boy",
         parent_type: str = "mother", eldest_age: int = 8, younger_age: int = 5,
         trust: int = 7, trait: str = "careful") -> World:
    world = World(chore=chore)
    eldest = world.add(Entity(
        id=eldest_name,
        kind="character",
        type=eldest_gender,
        label=eldest_name,
        role="eldest",
        traits=[trait],
        age=eldest_age,
        attrs={"relation": "siblings"},
    ))
    younger = world.add(Entity(
        id=younger_name,
        kind="character",
        type=younger_gender,
        label=younger_name,
        role="younger",
        traits=["curious"],
        age=younger_age,
        attrs={"relation": "siblings"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    pet = world.add(Entity(
        id=pet_cfg.label.capitalize(),
        kind="character",
        type=pet_cfg.id,
        label=pet_cfg.label,
        role="pet",
        attrs={"sound": pet_cfg.sound, "gait": pet_cfg.gait, "eats": pet_cfg.treats_like},
    ))
    hazard_ent = world.add(Entity(
        id="hazard",
        kind="thing",
        type="hazard",
        label=hazard.label,
        role="hazard",
        attrs={},
        toxic=hazard.toxic,
        attractive_to_pet=hazard.attractive_to_pet,
    ))
    hazard_ent.meters["toxicity"] = float(hazard.toxicity)
    eldest.memes["trust"] = float(trust)
    younger.memes["trust"] = float(trust)
    world.facts.update(
        chore=chore,
        hazard_cfg=hazard,
        pet_cfg=pet_cfg,
        response=response,
        trust=trust,
        trait=trait,
        delay=0,
    )

    introduce(world, eldest, younger, parent, pet, chore)
    daily_detail(world, chore)

    world.para()
    find_hazard(world, younger, pet, hazard)
    eldest_warn(world, eldest, younger, pet, hazard, parent)

    averted = would_avert(eldest_age=eldest_age, younger_age=younger_age, trust=trust, trait=trait)

    if averted:
        back_down(world, eldest, younger, pet, hazard, parent, chore)
        outcome = "averted"
    else:
        defy(world, younger, pet, hazard)
        world.para()
        ingest(world, pet, hazard_ent, hazard)
        alarm(world, eldest, parent, pet)

        severity = severity_of(hazard, world.facts["delay"])
        hazard_ent.meters["severity"] = float(severity)
        treated = is_treated_at_home(response=response, hazard=hazard, delay=world.facts["delay"])

        world.para()
        if treated:
            vet_help(world, parent, response, pet)
            comfort_and_lesson(world, eldest, younger, parent, pet, hazard)
            world.para()
            safer_after(world, eldest, younger, parent, pet, chore, hazard)
            outcome = "treated"
        else:
            overnight_care(world, parent, pet, response)
            comfort_and_lesson(world, eldest, younger, parent, pet, hazard)
            world.para()
            safer_after(world, eldest, younger, parent, pet, chore, hazard)
            outcome = "overnight"

    world.facts.update(
        eldest=eldest,
        younger=younger,
        parent=parent,
        pet=pet,
        hazard=hazard_ent,
        averted=averted,
        outcome=outcome,
        treated_home=(outcome == "treated"),
        ingested=pet.meters["ate_hazard"] >= THRESHOLD,
        severity=int(hazard_ent.meters["severity"]),
        promised=eldest.memes["lesson"] >= THRESHOLD or outcome == "averted",
    )
    return world


CHORES = {
    "donations": Chore(
        id="donations",
        setup="Old coats lay in one pile, cardboard boxes in another, and a wobbling lamp waited to be tested before the garage sale.",
        clutter="Dust floated in the sunstripe under the open door, and every shelf seemed to be holding one more forgotten thing.",
        ending="By lunchtime the boxes were labeled, the floor was swept, and the family had learned not every little find in the garage was harmless.",
        tags={"garage", "cleanup"},
    ),
    "bikes": Chore(
        id="bikes",
        setup="One bicycle was upside down for a loose chain, and a crate of rags sat beside the workbench.",
        clutter="The garage smelled like rubber, old cardboard, and the cool concrete that never quite lost the morning chill.",
        ending="At the end, the bike tires were full, the rags were folded away, and everyone looked twice before leaving anything low to the ground.",
        tags={"garage", "bike"},
    ),
    "plant_shelf": Chore(
        id="plant_shelf",
        setup="Seed trays, empty pots, and a bag of soil were waiting by the side wall where the garden things lived.",
        clutter="Bits of dry leaves had gathered along the edges, and the shelves looked busier than anyone remembered.",
        ending="Soon the pots were stacked, the soil bag was clipped shut, and safer habits had become part of the job.",
        tags={"garage", "garden"},
    ),
}

HAZARDS = {
    "raisins": Hazard(
        id="raisins",
        label="raisins",
        phrase="a small paper cup of raisins",
        found_where="on the low workbench",
        temptation="one as a treat",
        bad_for={"puppy", "dog"},
        toxic=True,
        attractive_to_pet=True,
        toxicity=2,
        lesson="food for people is not always safe for pets, especially in the garage where things get forgotten.",
        tags={"raisins", "pet_safety", "garage"},
    ),
    "gum": Hazard(
        id="gum",
        label="sweet gum",
        phrase="a crinkly pack of sweet gum",
        found_where="in the pocket of an old coat",
        temptation="a chewy little piece",
        bad_for={"puppy", "dog"},
        toxic=True,
        attractive_to_pet=True,
        toxicity=3,
        lesson="pets should never eat gum or mystery sweets, because even a small piece can mean a fast call to the vet.",
        tags={"gum", "pet_safety", "vet"},
    ),
    "antifreeze": Hazard(
        id="antifreeze",
        label="a bright drip of antifreeze",
        phrase="a bright drip of antifreeze",
        found_where="near the back tire",
        temptation="a quick lick",
        bad_for={"puppy", "dog", "kitten", "cat"},
        toxic=True,
        attractive_to_pet=True,
        toxicity=4,
        lesson="garage liquids are never for pets, even if they smell sweet or look like water.",
        tags={"antifreeze", "garage", "vet", "pet_safety"},
    ),
    "crayons": Hazard(
        id="crayons",
        label="broken crayons",
        phrase="a box of broken crayons",
        found_where="under a folding chair",
        temptation="something bright to nibble",
        bad_for=set(),
        toxic=False,
        attractive_to_pet=False,
        toxicity=0,
        lesson="small things should still be picked up and put away.",
        tags={"cleanup"},
    ),
}

PETS = {
    "puppy": PetType(
        id="puppy",
        label="puppy",
        sound="snuffle",
        gait="bounce",
        treats_like="snatched up the",
        tags={"puppy", "pet"},
    ),
    "dog": PetType(
        id="dog",
        label="dog",
        sound="huff",
        gait="trot",
        treats_like="gulped down the",
        tags={"dog", "pet"},
    ),
    "kitten": PetType(
        id="kitten",
        label="kitten",
        sound="mew",
        gait="tiptoe",
        treats_like="licked at the",
        tags={"kitten", "pet"},
    ),
}

RESPONSES = {
    "call_vet": Response(
        id="call_vet",
        sense=3,
        speed=3,
        text="grabbed the phone, called the vet right from the garage, and followed the clinic's advice without wasting a minute",
        qa_text="called the vet right away and followed the clinic's advice",
        fail_text="called the vet fast and drove straight over, but the vet still wanted to keep the pet for extra care",
        tags={"vet", "call_help"},
    ),
    "rinse_call": Response(
        id="rinse_call",
        sense=3,
        speed=2,
        text="wiped out the pet's mouth, called the vet, and drove over with the windows cracked and one worried hand on the carrier",
        qa_text="cleaned the pet's mouth and called the vet right away",
        fail_text="cleaned the pet's mouth and rushed to the vet, but the danger was too serious for a quick trip home afterward",
        tags={"vet", "call_help"},
    ),
    "wait": Response(
        id="wait",
        sense=1,
        speed=0,
        text="said they should wait and see",
        qa_text="waited to see what would happen",
        fail_text="waited instead of getting help quickly",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Rose", "Ella", "Maya", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "steady", "gentle", "thoughtful", "calm", "curious"]


@dataclass
class StoryParams:
    chore: str
    hazard: str
    pet: str
    response: str
    eldest_name: str
    eldest_gender: str
    younger_name: str
    younger_gender: str
    parent: str
    trait: str
    eldest_age: int = 8
    younger_age: int = 5
    trust: int = 7
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for chore_id in CHORES:
        for hazard_id, hazard in HAZARDS.items():
            for pet_id, pet in PETS.items():
                if hazard_at_risk(pet=pet, hazard=hazard):
                    combos.append((chore_id, hazard_id, pet_id))
    return combos


KNOWLEDGE = {
    "garage": [(
        "Why should families keep garage shelves tidy when pets are nearby?",
        "Garages often hold food scraps, little objects, and liquids that are safe for tools but not for animals. Putting things high up and closing bins helps pets stay away from trouble."
    )],
    "vet": [(
        "What does a vet do?",
        "A vet is a doctor for animals. Vets help pets when they are sick, hurt, or have eaten something unsafe."
    )],
    "pet_safety": [(
        "Why should you ask a grown-up before giving a pet a snack?",
        "Some foods that are fine for people can make a pet very sick. A grown-up can make sure the snack is safe and the right size."
    )],
    "raisins": [(
        "Why can raisins be dangerous for dogs?",
        "Raisins can make some dogs very sick, even in a small amount. If a dog eats them, a grown-up should call the vet right away."
    )],
    "gum": [(
        "Why is sweet gum unsafe for many dogs?",
        "Some sweet gum has ingredients that can hurt a dog's body very quickly. That is why gum should stay in pockets, bags, or bins that pets cannot reach."
    )],
    "antifreeze": [(
        "Why are garage puddles or drips dangerous for pets?",
        "A pet does not know which liquids are safe. Even a small lick of the wrong garage liquid can be an emergency."
    )],
    "call_help": [(
        "What should you do if a pet eats something dangerous?",
        "Tell a grown-up right away and call the vet. Getting help quickly gives the pet the best chance to feel better soon."
    )],
    "puppy": [(
        "Why do puppies need close watching around floors and shelves?",
        "Puppies explore with their noses and mouths. They can gulp down things before people notice if the room is cluttered."
    )],
    "dog": [(
        "Why do dogs sniff and eat things off the ground?",
        "Dogs learn about the world with their noses, and some will swallow food very fast. That is why safe storage matters so much."
    )],
    "kitten": [(
        "Why do kittens need careful watching around little objects and drips?",
        "Kittens are curious and quick, so they may lick or bat at things that are not meant for them. Calm, clean spaces help keep them safe."
    )],
}
KNOWLEDGE_ORDER = [
    "garage",
    "vet",
    "pet_safety",
    "raisins",
    "gum",
    "antifreeze",
    "call_help",
    "puppy",
    "dog",
    "kitten",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    eldest = f["eldest"]
    younger = f["younger"]
    pet = f["pet"]
    hazard = f["hazard_cfg"]
    chore = f["chore"]
    if f["outcome"] == "averted":
        return [
            f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "eldest", "garage", and "vet", where an eldest child stops a pet mistake before it happens.',
            f"Tell a gentle family story where {eldest.id}, the eldest, warns that {hazard.label} in the garage could send {pet.id} to the vet, and the younger child listens in time.",
            f"Write a quiet home story about siblings doing {chore.id} in the garage, noticing a danger for the family {pet.label}, and choosing the safe thing before anyone gets hurt.",
        ]
    return [
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "eldest", "garage", and "vet", where a family pet eats something unsafe and the grown-up acts fast.',
        f"Tell a gentle but serious story where {eldest.id}, the eldest, gives a warning in the garage, the warning is not followed quickly enough, and the family has to call the vet for {pet.id}.",
        f"Write a domestic story about ordinary cleanup, one unsafe little mistake, and a safer garage by the end.",
    ]


def pair_noun(eldest: Entity, younger: Entity) -> str:
    if eldest.type == "boy" and younger.type == "boy":
        return "two brothers"
    if eldest.type == "girl" and younger.type == "girl":
        return "two sisters"
    return "a brother and a sister"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eldest = f["eldest"]
    younger = f["younger"]
    parent = f["parent"]
    pet = f["pet"]
    hazard_cfg = f["hazard_cfg"]
    response = f["response"]
    chore = f["chore"]
    pair = pair_noun(eldest, younger)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {eldest.id} and {younger.id}, their {parent.label_word}, and their {pet.label} {pet.id}. The family is together in the garage doing an ordinary chore when the trouble starts."
        ),
        (
            "What were they doing in the garage?",
            f"They were helping with {chore.id} in the garage. The everyday job is what put them near shelves, boxes, and the forgotten unsafe thing."
        ),
        (
            f"Why did {eldest.id} warn {younger.id}?",
            f"{eldest.id} warned {younger.id} because {hazard_cfg.label} could make {pet.id} very sick. {eldest.pronoun().capitalize()} understood that if {pet.id} swallowed it, they might need the vet right away."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {eldest.id} spoke up?",
            f"{younger.id} listened and pulled the unsafe thing back before {pet.id} could eat it. Then their {parent.label_word} put it high up, so the danger passed without a vet visit."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and safely, with the family finishing the garage chore in a more careful way. The ending shows that listening early can stop a scary problem before it begins."
        ))
    elif f["outcome"] == "treated":
        qa.append((
            f"What did the family do when {pet.id} ate {hazard_cfg.label}?",
            f"They got help fast: their {parent.label_word} {response.qa_text}. Moving quickly mattered because the danger had already become real."
        ))
        qa.append((
            f"Why did they go to the vet?",
            f"They went to the vet because {pet.id} had swallowed something unsafe in the garage. The vet was needed to make sure one small mistake did not turn into a bigger sickness."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a safer garage and a tired but recovering pet back home. The new bin and high hook show what changed after the scare."
        ))
    else:
        qa.append((
            f"Did {pet.id} get better right away?",
            f"No. The family got to the vet fast, but the danger was serious enough that {pet.id} had to stay overnight for care. That happened because the unsafe thing was especially harmful once it had been swallowed."
        ))
        qa.append((
            "How did the family change after the scary night?",
            f"They made the garage safer by storing small foods and mystery items high up and closing a bin tightly. The ending image proves they learned from the trip to the vet instead of only feeling afraid."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["chore"].tags) | set(f["hazard_cfg"].tags) | set(f["pet_cfg"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.toxic:
            bits.append("toxic=True")
        if ent.attractive_to_pet:
            bits.append("attractive_to_pet=True")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(pet: PetType, hazard: Hazard) -> str:
    if not hazard.toxic:
        return (
            f"(No story: {hazard.label} is not a true poisoning risk here, so the family would have no honest reason to mention the vet. Pick a hazard like raisins, gum, or antifreeze.)"
        )
    if not hazard.attractive_to_pet:
        return (
            f"(No story: {hazard.label} is not tempting in the right way for a family pet, so the cautionary turn does not hold.)"
        )
    return (
        f"(No story: {hazard.label} is not the right kind of garage danger for a {pet.label} in this world. Pick a hazard that is toxic to that pet.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is below the common-sense floor for a pet poisoning story "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(
        eldest_age=params.eldest_age,
        younger_age=params.younger_age,
        trust=params.trust,
        trait=params.trait,
    ):
        return "averted"
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "treated" if is_treated_at_home(response=response, hazard=hazard, delay=params.delay) else "overnight"


ASP_RULES = r"""
hazard_for(Pet, Hazard) :- pet(Pet), hazard(Hazard), toxic(Hazard), attractive(Hazard), bad_for(Hazard, Pet).
valid(Chore, Hazard, Pet) :- chore(Chore), hazard_for(Pet, Hazard).

cautious_trait(T) :- trait(T), is_cautious(T).
age_gap(EA - YA) :- eldest_age(EA), younger_age(YA).
averted :- cautious_trait(T), age_gap(G), G >= 2, trust(Tr), Tr >= 5.

severity(Tox + D) :- chosen_hazard(H), toxicity(H, Tox), delay(D).
treated :- chosen_response(R), speed(R, S), severity(V), S >= V.

outcome(averted) :- averted.
outcome(treated) :- not averted, treated.
outcome(overnight) :- not averted, not treated.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for chore_id in CHORES:
        lines.append(asp.fact("chore", chore_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        if hazard.toxic:
            lines.append(asp.fact("toxic", hazard_id))
        if hazard.attractive_to_pet:
            lines.append(asp.fact("attractive", hazard_id))
        lines.append(asp.fact("toxicity", hazard_id, hazard.toxicity))
        for pet_id in sorted(hazard.bad_for):
            lines.append(asp.fact("bad_for", hazard_id, pet_id))
    for pet_id in PETS:
        lines.append(asp.fact("pet", pet_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("speed", response_id, response.speed))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("eldest_age", params.eldest_age),
        asp.fact("younger_age", params.younger_age),
        asp.fact("trust", params.trust),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: the eldest, the garage, and a quick call to the vet."
    )
    ap.add_argument("--chore", choices=CHORES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time lost before the trip to the vet")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (chore, hazard, pet) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.pet:
        hazard = HAZARDS[args.hazard]
        pet = PETS[args.pet]
        if not hazard_at_risk(pet=pet, hazard=hazard):
            raise StoryError(explain_rejection(pet=pet, hazard=hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.chore is None or combo[0] == args.chore)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.pet is None or combo[2] == args.pet)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chore_id, hazard_id, pet_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    eldest_gender = rng.choice(["girl", "boy"])
    younger_gender = rng.choice(["girl", "boy"])
    eldest_name = _pick_name(rng=rng, gender=eldest_gender)
    younger_name = _pick_name(rng=rng, gender=younger_gender, avoid=eldest_name)
    parent = args.parent or rng.choice(["mother", "father"])
    eldest_age = rng.choice([7, 8, 9])
    younger_age = rng.choice([4, 5, 6])
    if younger_age >= eldest_age:
        younger_age = max(4, eldest_age - 2)
    trust = rng.randint(2, 9)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        chore=chore_id,
        hazard=hazard_id,
        pet=pet_id,
        response=response_id,
        eldest_name=eldest_name,
        eldest_gender=eldest_gender,
        younger_name=younger_name,
        younger_gender=younger_gender,
        parent=parent,
        trait=trait,
        eldest_age=eldest_age,
        younger_age=younger_age,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.chore not in CHORES:
        raise StoryError(f"(Unknown chore: {params.chore})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    hazard = HAZARDS[params.hazard]
    pet_cfg = PETS[params.pet]
    response = RESPONSES[params.response]
    if not hazard_at_risk(pet=pet_cfg, hazard=hazard):
        raise StoryError(explain_rejection(pet=pet_cfg, hazard=hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    world = tell(
        chore=CHORES[params.chore],
        hazard=hazard,
        pet_cfg=pet_cfg,
        response=response,
        eldest_name=params.eldest_name,
        eldest_gender=params.eldest_gender,
        younger_name=params.younger_name,
        younger_gender=params.younger_gender,
        parent_type=params.parent,
        eldest_age=params.eldest_age,
        younger_age=params.younger_age,
        trust=params.trust,
        trait=params.trait,
    )
    world.facts["delay"] = params.delay
    world.facts["response"] = response
    # Recompute outcome facts for this exact param set so QA/trace match the requested delay.
    exact_outcome = outcome_of(params)
    if exact_outcome != world.facts["outcome"] and world.facts["outcome"] != "averted":
        world.facts["outcome"] = exact_outcome
        world.facts["treated_home"] = exact_outcome == "treated"
        if exact_outcome == "overnight":
            world.get("pet").meters["overnight"] = 1.0
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
        chore="donations",
        hazard="raisins",
        pet="puppy",
        response="call_vet",
        eldest_name="Nora",
        eldest_gender="girl",
        younger_name="Ben",
        younger_gender="boy",
        parent="mother",
        trait="careful",
        eldest_age=9,
        younger_age=5,
        trust=8,
        delay=0,
    ),
    StoryParams(
        chore="bikes",
        hazard="gum",
        pet="dog",
        response="call_vet",
        eldest_name="Theo",
        eldest_gender="boy",
        younger_name="Mia",
        younger_gender="girl",
        parent="father",
        trait="steady",
        eldest_age=8,
        younger_age=6,
        trust=6,
        delay=0,
    ),
    StoryParams(
        chore="plant_shelf",
        hazard="antifreeze",
        pet="kitten",
        response="call_vet",
        eldest_name="Lily",
        eldest_gender="girl",
        younger_name="Sam",
        younger_gender="boy",
        parent="mother",
        trait="calm",
        eldest_age=8,
        younger_age=6,
        trust=4,
        delay=1,
    ),
    StoryParams(
        chore="donations",
        hazard="gum",
        pet="puppy",
        response="rinse_call",
        eldest_name="Max",
        eldest_gender="boy",
        younger_name="Ava",
        younger_gender="girl",
        parent="father",
        trait="thoughtful",
        eldest_age=9,
        younger_age=4,
        trust=7,
        delay=0,
    ),
    StoryParams(
        chore="bikes",
        hazard="antifreeze",
        pet="dog",
        response="call_vet",
        eldest_name="Rose",
        eldest_gender="girl",
        younger_name="Finn",
        younger_gender="boy",
        parent="mother",
        trait="gentle",
        eldest_age=7,
        younger_age=6,
        trust=3,
        delay=1,
    ),
]


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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "garage" not in sample.story.lower():
            raise StoryError("smoke test story missing expected garage prose")
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=False, qa=False)
        sample2 = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not sample2.story or "vet" not in sample2.story.lower():
            raise StoryError("smoke test story missing expected vet prose")
        print("OK: smoke-tested generate() and emit().")
    except Exception as err:
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
        print(f"{len(combos)} compatible (chore, hazard, pet) combos:\n")
        for chore_id, hazard_id, pet_id in combos:
            print(f"  {chore_id:12} {hazard_id:10} {pet_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.eldest_name} and {p.younger_name}: {p.hazard} in the garage "
                f"with a {p.pet} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
