#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py
=======================================================================

A small superhero-flavored story world about a child who wants to help a gentle
mule finish an important delivery. The child begins with a flashy "superhero"
idea, but the world only allows calm, sensible fixes that actually match the
mule's problem. Every valid story ends happily, with the changed ending image
showing that real heroes help with care, not just speed.

Run it
------
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py --place farm_gate --problem puddle_edge --fix straw_path
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py --problem tilted_load --fix remove_noise
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mule_sneaker_happy_ending_superhero_story.py --verify
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    intro: str
    clue: str
    risk: str
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
class Fix:
    id: str
    label: str
    sense: int
    handles: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    gift_line: str = ""
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
class Delivery:
    id: str
    cargo: str
    destination: str
    celebration: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    mule = world.get("mule")
    cart = world.get("cart")
    if (
        cart.meters["noise"] >= THRESHOLD
        or cart.meters["tilted"] >= THRESHOLD
        or world.get("path").meters["wobbly"] >= THRESHOLD
    ):
        sig = ("stuck",)
        if sig not in world.fired:
            world.fired.add(sig)
            mule.meters["stopped"] += 1
            mule.memes["worry"] += 1
            out.append("__stopped__")
    return out


def _r_hero_urge(world: World) -> list[str]:
    mule = world.get("mule")
    hero = world.get("hero")
    if mule.meters["stopped"] >= THRESHOLD:
        sig = ("urge",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["urgency"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    mule = world.get("mule")
    hero = world.get("hero")
    helper = world.get("helper")
    owner = world.get("owner")
    cart = world.get("cart")
    path = world.get("path")
    if (
        mule.meters["stopped"] < THRESHOLD
        and cart.meters["moving"] >= THRESHOLD
        and cart.meters["noise"] < THRESHOLD
        and cart.meters["tilted"] < THRESHOLD
        and path.meters["wobbly"] < THRESHOLD
    ):
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            mule.memes["calm"] += 1
            hero.memes["pride"] += 1
            helper.memes["relief"] += 1
            owner.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="hero_urge", tag="emotional", apply=_r_hero_urge),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def fix_matches(problem: Problem, fix: Fix) -> bool:
    return bool(problem.tags & fix.handles)


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id in sorted(place.affords):
            problem = PROBLEMS[problem_id]
            for fix in sensible_fixes():
                if fix_matches(problem, fix):
                    combos.append((place_id, problem_id, fix.id))
    return sorted(combos)


def predict_worse_if_rushed(world: World) -> dict:
    sim = world.copy()
    mule = sim.get("mule")
    hero = sim.get("hero")
    mule.memes["worry"] += 1
    hero.meters["slip_risk"] += 1
    return {
        "mule_worry": mule.memes["worry"],
        "slip_risk": hero.meters["slip_risk"],
    }


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it is too showy and not sensible enough "
            f"for this world. Real help here needs a calm plan, not force.)"
        )
    return (
        f"(No story: {fix.label} does not honestly solve the problem "
        f'"{problem.label}". Pick a fix that matches what is actually wrong with the mule or cart.)'
    )


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    cape = hero.attrs["cape"]
    sneaker = hero.attrs["sneaker"]
    world.say(
        f"On a bright morning in {place.label}, {hero.id} tied on {cape} and decided "
        f"to be a superhero for the day. {hero.pronoun().capitalize()} stamped one "
        f"{sneaker} on the ground, lifted {hero.pronoun('possessive')} chin, and "
        f"struck the bravest pose {helper.id} had ever seen."
    )
    world.say(
        f'{helper.id} laughed and gave a little salute. "Super {hero.id}, ready for any mission," '
        f'{helper.pronoun()} said.'
    )


def mission_arrives(world: World, owner: Entity, mule: Entity, cart: Entity, delivery: Delivery, problem: Problem) -> None:
    world.say(
        f"Just then, {owner.id} came along with {mule.label}, a gentle mule pulling a small cart of "
        f"{delivery.cargo}. The cart was headed to {delivery.destination}, where everyone was waiting for "
        f"{delivery.celebration}."
    )
    world.say(problem.intro)
    propagate(world, narrate=False)
    world.say(problem.clue)


def hero_impulse(world: World, hero: Entity, helper: Entity, owner: Entity) -> None:
    pred = predict_worse_if_rushed(world)
    world.facts["predicted_mule_worry"] = pred["mule_worry"]
    world.facts["predicted_slip_risk"] = pred["slip_risk"]
    hero.memes["showoff"] += 1
    world.say(
        f'"I can save the day!" {hero.id} cried. {hero.pronoun().capitalize()} took one fast step as if '
        f'{hero.pronoun()} might pull the whole cart by sheer superhero power.'
    )
    world.say(
        f'{helper.id} caught {hero.pronoun("possessive")} sleeve. "Wait," {helper.pronoun()} said. '
        f'"If we rush, {mule.label} will worry more, and your loose {hero.attrs["sneaker"]} might slip."'
    )
    owner.memes["trust"] += 1


def owner_explains(world: World, owner: Entity, problem: Problem) -> None:
    world.say(
        f'{owner.id} nodded. "{problem.risk}," {owner.pronoun()} said. '
        f'"A real helper looks first and then helps."'
    )


def plan_fix(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    hero.memes["focus"] += 1
    helper.memes["focus"] += 1
    world.say(
        f"{hero.id} took a deep breath, tightened {hero.pronoun('possessive')} cape, and looked carefully instead of charging ahead. "
        f'This time {hero.pronoun()} used superhero eyes, superhero patience, and a superhero plan.'
    )
    world.say(
        f"Together, {hero.id} and {helper.id} chose {fix.label}."
    )


def apply_fix(world: World, hero: Entity, helper: Entity, owner: Entity, mule: Entity, cart: Entity, path: Entity,
              problem: Problem, fix: Fix) -> None:
    hero.meters["slip_risk"] = 0.0
    if problem.id == "loose_pan" and fix.id == "remove_noise":
        cart.meters["noise"] = 0.0
        world.say(
            f"{owner.id} unhooked the shiny pan that had been knocking against the cart, and {hero.id} held it still with both hands. "
            f"When the clang-clang stopped, {mule.label}'s ears softened."
        )
    elif problem.id == "tilted_load" and fix.id == "retie_load":
        cart.meters["tilted"] = 0.0
        world.say(
            f"{helper.id} steadied the cart while {owner.id} pulled the rope snug again. "
            f"{hero.id} passed up the loose ends like a caped assistant on a very important roof."
        )
    elif problem.id == "puddle_edge" and fix.id == "straw_path":
        path.meters["wobbly"] = 0.0
        world.say(
            f"{owner.id} spread a dry trail of straw over the slick edge by the puddle, and {hero.id} patted it flat with careful feet. "
            f"{helper.id} stood nearby, quiet as a guard at a castle gate."
        )
    else:
        raise StoryError(explain_rejection(problem, fix))
    mule.meters["stopped"] = 0.0
    cart.meters["moving"] = 1.0
    propagate(world, narrate=False)
    owner.memes["gratitude"] += 1
    world.say(
        f"Then {owner.id} spoke softly to {mule.label} and gave {mule.pronoun('object')} a kind stroke on the neck. "
        f"{mule.label.capitalize()} stepped forward, and the cart rolled again."
    )


def success(world: World, hero: Entity, helper: Entity, owner: Entity, mule: Entity, delivery: Delivery, fix: Fix) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    mule.memes["calm"] += 1
    world.say(
        f"They reached {delivery.destination} just in time. The waiting crowd cheered when the cart arrived, and the whole place filled with "
        f"the happy smell of {delivery.cargo} and the sound of clapping hands."
    )
    world.say(
        f'{owner.id} smiled at {hero.id}. "You did not use the loudest hero trick," {owner.pronoun()} said. '
        f'"You used the right one. That is what made you helpful."'
    )
    world.say(
        f"{hero.id} looked at {hero.pronoun('possessive')} dusty {hero.attrs['sneaker']}, then at {mule.label} walking calmly beside the cart, and grinned. "
        f"In the sunshine, {hero.pronoun('possessive')} cape fluttered behind {hero.pronoun('object')} like a little flag of real courage."
    )
    if fix.gift_line:
        world.say(fix.gift_line)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, problem: Problem, fix: Fix, delivery: Delivery,
         hero_name: str = "Nora", hero_type: str = "girl",
         helper_name: str = "Ben", helper_type: str = "boy",
         owner_type: str = "father") -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["brave", "kind"],
        attrs={"cape": "a red towel-cape", "sneaker": "blue sneaker"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        traits=["steady", "thoughtful"],
        attrs={},
    ))
    owner = world.add(Entity(
        id="Farmer Jo",
        kind="character",
        type=owner_type,
        role="owner",
        label="the farmer",
        attrs={},
    ))
    mule = world.add(Entity(
        id="mule",
        kind="thing",
        type="animal",
        role="mule",
        label="Maple the mule",
        attrs={},
    ))
    cart = world.add(Entity(
        id="cart",
        kind="thing",
        type="cart",
        label="the cart",
        attrs={},
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label="the path",
        attrs={},
    ))

    cart.meters["moving"] = 0.0
    cart.meters["noise"] = 1.0 if problem.id == "loose_pan" else 0.0
    cart.meters["tilted"] = 1.0 if problem.id == "tilted_load" else 0.0
    path.meters["wobbly"] = 1.0 if problem.id == "puddle_edge" else 0.0
    mule.meters["stopped"] = 0.0
    mule.memes["worry"] = 0.0
    mule.memes["calm"] = 0.0
    hero.meters["slip_risk"] = 0.0
    hero.memes["urgency"] = 0.0
    hero.memes["showoff"] = 0.0
    hero.memes["focus"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["focus"] = 0.0
    helper.memes["relief"] = 0.0
    helper.memes["joy"] = 0.0
    owner.memes["trust"] = 0.0
    owner.memes["gratitude"] = 0.0

    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["delivery"] = delivery
    world.facts["place"] = place

    introduce(world, hero, helper, place)
    world.para()
    mission_arrives(world, owner, mule, cart, delivery, problem)
    hero_impulse(world, hero, helper, owner)
    owner_explains(world, owner, problem)
    world.para()
    plan_fix(world, hero, helper, fix)
    apply_fix(world, hero, helper, owner, mule, cart, path, problem, fix)
    world.para()
    success(world, hero, helper, owner, mule, delivery, fix)

    world.facts.update(
        hero=hero,
        helper=helper,
        owner=owner,
        mule=mule,
        cart=cart,
        path=path,
        solved=cart.meters["moving"] >= THRESHOLD and mule.meters["stopped"] < THRESHOLD,
        predicted_rush_bad=world.facts.get("predicted_mule_worry", 0) >= 1,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "market_lane": Place(
        id="market_lane",
        label="Market Lane",
        scene="bright stalls and striped awnings",
        affords={"loose_pan", "tilted_load"},
    ),
    "orchard_path": Place(
        id="orchard_path",
        label="Orchard Path",
        scene="apple trees and drowsy bees",
        affords={"loose_pan", "puddle_edge"},
    ),
    "farm_gate": Place(
        id="farm_gate",
        label="the farm gate",
        scene="a wide gate, hay smell, and muddy wheel tracks",
        affords={"tilted_load", "puddle_edge"},
    ),
}

PROBLEMS = {
    "loose_pan": Problem(
        id="loose_pan",
        label="a clanging pan",
        intro="But halfway down the road, a shiny pan hanging from the cart began to bang against the wood.",
        clue="Maple the mule stopped with all four hooves planted hard and flicked her ears at the noisy clatter.",
        risk="The sharp noise is frightening her",
        tags={"noise"},
    ),
    "tilted_load": Problem(
        id="tilted_load",
        label="a tilted load",
        intro="But one side of the cart had sunk low, and the boxes on top had slipped into a crooked wobble.",
        clue="Maple the mule leaned forward, then stopped again because the load was pulling unevenly on the harness.",
        risk="If the load stays crooked, it will tug and pinch while she pulls",
        tags={"load"},
    ),
    "puddle_edge": Problem(
        id="puddle_edge",
        label="a slick puddle edge",
        intro="But near the gate, yesterday's rain had left a wide puddle with a slick, wobbling edge.",
        clue="Maple the mule stretched out one hoof, then drew it back and snorted at the slippery ground.",
        risk="She does not feel safe stepping there yet",
        tags={"crossing"},
    ),
}

FIXES = {
    "remove_noise": Fix(
        id="remove_noise",
        label="removing the noisy pan",
        sense=3,
        handles={"noise"},
        action="stop the clanging and let the mule hear a calm voice again",
        qa_text="They stopped the clanging by removing the pan that was banging against the cart.",
        gift_line="Farmer Jo tucked a tiny paper star into the hero's hand and said it was for quiet courage.",
        tags={"noise", "calm"},
    ),
    "retie_load": Fix(
        id="retie_load",
        label="retightening the rope and balancing the boxes",
        sense=3,
        handles={"load"},
        action="make the load sit straight so the mule can pull evenly",
        qa_text="They straightened the boxes and tightened the rope so the load stopped pulling sideways.",
        gift_line="Farmer Jo let the children walk beside the cart like an official rescue team all the way to the party.",
        tags={"rope", "load"},
    ),
    "straw_path": Fix(
        id="straw_path",
        label="making a dry straw path",
        sense=3,
        handles={"crossing"},
        action="give the mule a steadier place to step",
        qa_text="They spread dry straw over the slick edge so the mule had safe footing.",
        gift_line="At the party, someone pinned a straw-yellow ribbon to the cape and called it a hero medal.",
        tags={"straw", "crossing"},
    ),
    "shout_and_tug": Fix(
        id="shout_and_tug",
        label="shouting and tugging on the harness",
        sense=1,
        handles=set(),
        action="pull harder and hope the mule moves",
        qa_text="They shouted and tugged, which would only make the mule more worried.",
        gift_line="",
        tags={"bad_idea"},
    ),
}

DELIVERIES = {
    "pies": Delivery(
        id="pies",
        cargo="warm berry pies",
        destination="the village picnic table",
        celebration="the noon picnic",
        tags={"food", "party"},
    ),
    "flowers": Delivery(
        id="flowers",
        cargo="sunflower bunches",
        destination="the square fountain",
        celebration="the afternoon welcome party",
        tags={"flowers", "party"},
    ),
    "bread": Delivery(
        id="bread",
        cargo="soft round loaves",
        destination="the long supper table",
        celebration="the sunset supper",
        tags={"bread", "party"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Theo"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    delivery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    owner_type: str
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
    "mule": [
        (
            "What is a mule?",
            "A mule is an animal with long ears and strong legs. People often trust a mule to carry or pull things because it is steady and hardworking.",
        )
    ],
    "sneaker": [
        (
            "What is a sneaker?",
            "A sneaker is a soft shoe made for walking, running, and playing. Good sneakers help your feet grip the ground better.",
        )
    ],
    "superhero": [
        (
            "Do superheroes always help by using force?",
            "No. A good superhero first notices what the real problem is. Then the hero chooses the safest, kindest way to help.",
        )
    ],
    "noise": [
        (
            "Why can a loud clanging sound scare an animal?",
            "A sudden hard noise can make an animal jump because it feels sharp and surprising. When the noise stops, the animal often feels calmer.",
        )
    ],
    "rope": [
        (
            "Why do people tie a cart load carefully?",
            "A careful rope keeps boxes from sliding around. That makes the cart easier and safer for an animal to pull.",
        )
    ],
    "crossing": [
        (
            "Why might an animal stop at slippery ground?",
            "Animals need to feel steady under their feet. If the ground looks slick or wobbly, they may stop because they do not want to slip.",
        )
    ],
    "straw": [
        (
            "Why can straw help on muddy ground?",
            "Straw can make a wet spot less slippery by giving hooves or shoes something dry to press on. It helps make the path feel steadier.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mule", "sneaker", "superhero", "noise", "rope", "crossing", "straw"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    delivery = world.facts["delivery"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "mule" and "sneaker" and ends happily.',
        f"Tell a gentle rescue story where {hero.id} wants to act like a superhero, but slows down to help a mule with {problem.label} so a delivery of {delivery.cargo} can reach the party.",
        "Write a child-facing story that shows real heroism as calm, careful helping instead of rushing or showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    owner = world.facts["owner"]
    mule = world.facts["mule"]
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    delivery = world.facts["delivery"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was pretending to be a superhero, {helper.id}, and {mule.label}. They all became part of one rescue mission when the cart stopped on the way to {delivery.destination}.",
        ),
        (
            "What problem stopped the mule?",
            f"The problem was {problem.label}. {problem.risk}, so {mule.label} did not feel ready to keep pulling.",
        ),
        (
            f"Why did {helper.id} tell {hero.id} to slow down?",
            f"{helper.id} could see that rushing would not fix the real problem. If {hero.id} had charged ahead, {mule.label} would have worried more and {hero.pronoun('possessive')} {hero.attrs['sneaker']} might have slipped.",
        ),
        (
            "How did they help the mule?",
            f"{fix.qa_text} That changed the world around {mule.label}, so the mule felt safe enough to step forward again.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the cart reached {delivery.destination} in time for {delivery.celebration}. {hero.id} learned that being heroic meant helping in the right way, and {mule.label} walked on calmly beside the cart.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mule", "sneaker", "superhero"} | set(world.facts["fix"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="market_lane",
        problem="loose_pan",
        fix="remove_noise",
        delivery="pies",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Ben",
        helper_type="boy",
        owner_type="father",
        seed=None,
    ),
    StoryParams(
        place="farm_gate",
        problem="tilted_load",
        fix="retie_load",
        delivery="flowers",
        hero_name="Max",
        hero_type="boy",
        helper_name="Lily",
        helper_type="girl",
        owner_type="mother",
        seed=None,
    ),
    StoryParams(
        place="orchard_path",
        problem="puddle_edge",
        fix="straw_path",
        delivery="bread",
        hero_name="Ava",
        hero_type="girl",
        helper_name="Theo",
        helper_type="boy",
        owner_type="father",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
sensible(Fx) :- fix(Fx), sense(Fx, S), sense_min(M), S >= M.
matches(P, Fx) :- problem(P), fix(Fx), problem_tag(P, T), handles(Fx, T).
valid(Place, P, Fx) :- place(Place), affords(Place, P), sensible(Fx), matches(P, Fx).
#show valid/3.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for problem_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        for tag in sorted(problem.tags):
            lines.append(asp.fact("problem_tag", problem_id, tag))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for tag in sorted(fix.handles):
            lines.append(asp.fact("handles", fix_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(fx for (fx,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {fix.id for fix in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero child helps a mule with a calm, sensible fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delivery", choices=DELIVERIES)
    ap.add_argument("--owner", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, problem, fix) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not fix_matches(problem, fix) or fix.sense < SENSE_MIN:
            raise StoryError(explain_rejection(problem, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, fix = rng.choice(combos)
    delivery = args.delivery or rng.choice(sorted(DELIVERIES.keys()))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if hero_type == "girl" else "girl"
    hero_name = _pick_name(rng, hero_type)
    helper_name = _pick_name(rng, helper_type, avoid=hero_name)
    owner_type = args.owner or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        delivery=delivery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        owner_type=owner_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.delivery not in DELIVERIES:
        raise StoryError(f"(Unknown delivery: {params.delivery})")

    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    delivery = DELIVERIES[params.delivery]

    if params.problem not in place.affords:
        raise StoryError(
            f"(No story: {problem.label} does not fit {place.label}. Pick a place that can honestly cause that problem.)"
        )
    if not fix_matches(problem, fix) or fix.sense < SENSE_MIN:
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        place=place,
        problem=problem,
        fix=fix,
        delivery=delivery,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        owner_type=params.owner_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, problem, fix) combos:\n")
        for place, problem, fix in combos:
            print(f"  {place:12} {problem:12} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} at {p.place} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
