#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py
=================================================

A standalone story world for a tiny dialogue-heavy comedy about a child who
turns a window sill into a "bird café." The child wants to set a snack and a
tiny cup on the sill for a feathered guest. A helper warns that the family pet
may leap for the food and knock everything down. Sometimes the warning works
and the silly plan is changed before any mess begins; sometimes the pet pounces,
something spills, and a grown-up helps the children turn the mistake into a
better idea.

The domain is intentionally small and constraint-checked:

* A room must really have a usable window sill.
* The offered bird snack must be something a small bird might honestly like.
* The cleanup method must pass a basic common-sense gate.
* The story's ending comes from world state: either the plan is averted in time,
  or the spill happens and is cleaned up.

Run it
------
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py --room kitchen --snack cupcake
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py --json
    python storyworlds/worlds/gpt-5.4/sill_dialogue_comedy.py --verify
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
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "practical", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    bird_safe: bool = False
    spillable: bool = False
    has_sill: bool = False
    tempting: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "cat":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "dog":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Room:
    id: str
    label: str
    has_sill: bool
    window_view: str
    prop: str
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
class Snack:
    id: str
    label: str
    phrase: str
    bird_safe: bool
    tempting: bool
    qa_reason: str
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
class Drink:
    id: str
    label: str
    phrase: str
    splash: str
    severity: int
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    safe_plan: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"host", "helper"}]

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


def _r_cat_interest(world: World) -> list[str]:
    cat = world.entities.get("pet")
    sill = world.entities.get("sill")
    snack = world.entities.get("snack")
    if not cat or not sill or not snack:
        return []
    if sill.meters["occupied"] < THRESHOLD or snack.tempting is False:
        return []
    sig = ("cat_interest",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cat.memes["curious"] += 1
    cat.meters["jump_risk"] += 1
    return ["__cat_interest__"]


def _r_jump_spill(world: World) -> list[str]:
    cat = world.entities.get("pet")
    sill = world.entities.get("sill")
    cup = world.entities.get("cup")
    room = world.entities.get("room")
    if not cat or not sill or not cup or not room:
        return []
    if cat.meters["jump"] < THRESHOLD or sill.meters["occupied"] < THRESHOLD:
        return []
    sig = ("jump_spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cup.meters["fallen"] += 1
    cup.meters["spilled"] += 1
    room.meters["mess"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    return ["__spill__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="cat_interest", tag="physical", apply=_r_cat_interest),
    Rule(name="jump_spill", tag="physical", apply=_r_jump_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def snack_works(snack: Snack) -> bool:
    return snack.bird_safe and snack.tempting


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def plan_valid(room: Room, snack: Snack) -> bool:
    return room.has_sill and snack_works(snack)


def spill_severity(drink: Drink, delay: int) -> int:
    return drink.severity + delay


def cleanup_succeeds(fix: Fix, drink: Drink, delay: int) -> bool:
    return fix.power >= spill_severity(drink, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, host_age: int, helper_age: int, trait: str) -> bool:
    older_helper = relation == "siblings" and helper_age > host_age
    authority = initial_care(trait) + 1.0 + (2.0 if older_helper else 0.0)
    return older_helper and authority > BOLDNESS_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sill = sim.get("sill")
    cup = sim.get("cup")
    cat = sim.get("pet")
    sill.meters["occupied"] += 1
    propagate(sim, narrate=False)
    cat.meters["jump"] += 1
    propagate(sim, narrate=False)
    return {
        "cat_interested": cat.meters["jump_risk"] >= THRESHOLD,
        "spill": cup.meters["spilled"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def introduce(world: World, host: Entity, helper: Entity, room: Room) -> None:
    host.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {host.id} and {helper.id} stood by the {room.label} window. "
        f"The sill was wide enough for adventures, and {room.window_view} made it feel as if a guest might arrive at any moment."
    )
    world.say(
        f'"Let\'s open the Bird Café on the sill," {host.id} announced. '
        f'"Only very fancy birds may come in."'
    )
    world.say(
        f'"Do fancy birds pay with worms or with singing?" {helper.id} asked.'
    )


def choose_menu(world: World, host: Entity, snack: Snack, drink: Drink, room: Room) -> None:
    world.say(
        f"{host.id} set out {drink.phrase} and whispered that the first customer should also receive {snack.phrase}. "
        f"{room.prop.capitalize()} stood nearby like part of the stage set."
    )
    world.say(
        f'"If a sparrow taps the glass, I will say, "Welcome, sir, your table is on the sill," '
        f'{host.id} said.'
    )


def warn(world: World, helper: Entity, host: Entity, snack: Snack, parent: Entity, pet: Entity) -> None:
    pred = predict_trouble(world)
    helper.memes["care"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{helper.id} looked at {pet.id}, whose whiskers were already twitching. '
        f'"Wait," {helper.pronoun()} said. "{pet.id} thinks every snack is a drum solo for his feet."'
    )
    if pred["spill"]:
        world.say(
            f'"If we put food and a cup on the sill, {pet.id} will jump, and then something will splash on the floor," '
            f'{helper.id} told {host.id}. "{parent.label_word.capitalize()} will hear the plop before the bird hears the invitation."'
        )
    else:
        world.say(
            f'"I have a funny feeling this plan will not stay polite for long," {helper.id} said.'
        )


def defy(world: World, host: Entity, helper: Entity) -> None:
    host.memes["defiance"] += 1
    host.say_line = ""
    world.say(
        f'"Nonsense," {host.id} said. "A café on the sill is classy."'
    )
    world.say(
        f'"It is classy right up until the cat becomes a waiter," {helper.id} replied.'
    )


def back_down(world: World, host: Entity, helper: Entity, parent: Entity, fix: Fix) -> None:
    host.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{host.id} looked from the cup to the cat and then sighed. '
        f'"You are ruining my business with facts," {host.pronoun()} said.'
    )
    world.say(
        f'"That is one of my best skills," {helper.id} said.'
    )
    world.say(
        f"They laughed, left the sill empty, and called for {parent.label_word}. "
        f'Soon the plan changed to {fix.safe_plan}.'
    )


def place_on_sill(world: World, host: Entity) -> None:
    sill = world.get("sill")
    sill.meters["occupied"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{host.id} balanced the little cup and the snack on the sill as carefully as a circus plate-spinner."
    )
    world.say(
        f'"Perfect," {host.id} whispered. "Now we wait for a tiny customer with excellent manners."'
    )


def cat_pounces(world: World, pet: Entity, drink: Drink) -> None:
    pet.meters["jump"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {pet.id} did not wait politely. {pet.pronoun().capitalize()} crouched, wriggled, and sprang toward the sill."
    )
    world.say(
        f'There was a quick tap, a wobble, and then {drink.splash}.'
    )


def cleanup(world: World, parent: Entity, fix: Fix, host: Entity, helper: Entity) -> None:
    room = world.get("room")
    cup = world.get("cup")
    room.meters["mess"] = 0.0
    cup.meters["spilled"] = 0.0
    host.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came in at once and {fix.text}.'
    )
    world.say(
        f'"Nobody is in trouble," {parent.pronoun()} said. "But the sill is not a good restaurant table for cats, cups, or birds."'
    )


def better_plan(world: World, parent: Entity, host: Entity, helper: Entity, snack: Snack, fix: Fix, pet: Entity) -> None:
    host.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'"Birds would rather have {snack.label} in a quiet safe spot anyway," {parent.label_word} said. '
        f'"Let\'s try {fix.safe_plan}."'
    )
    world.say(
        f'{helper.id} grinned. "So the café moves, but the sill retires with honor."'
    )
    world.say(
        f'{host.id} nodded. "And {pet.id} is banned from waiting tables."'
    )
    world.say(
        f"Soon the new snack spot was ready, the cup stayed far from the sill, and even {pet.id} only sat below the window with an offended little tail flick."
    )


def tell(
    room_cfg: Room,
    snack_cfg: Snack,
    drink_cfg: Drink,
    fix_cfg: Fix,
    host_name: str = "Lily",
    host_gender: str = "girl",
    helper_name: str = "Max",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    pet_name: str = "Pudding",
    pet_type: str = "cat",
    trait: str = "careful",
    delay: int = 0,
    host_age: int = 5,
    helper_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    host = world.add(
        Entity(
            id=host_name,
            kind="character",
            type=host_gender,
            role="host",
            age=host_age,
            traits=["dramatic"],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    pet = world.add(
        Entity(
            id=pet_name,
            kind="character",
            type=pet_type,
            role="pet",
            label=pet_name,
            tempting=True,
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=room_cfg.label,
            has_sill=room_cfg.has_sill,
            attrs={"view": room_cfg.window_view, "prop": room_cfg.prop},
        )
    )
    sill = world.add(
        Entity(
            id="sill",
            type="sill",
            label="the sill",
            has_sill=room_cfg.has_sill,
        )
    )
    snack = world.add(
        Entity(
            id="snack",
            type="snack",
            label=snack_cfg.label,
            bird_safe=snack_cfg.bird_safe,
            tempting=snack_cfg.tempting,
        )
    )
    cup = world.add(
        Entity(
            id="cup",
            type="cup",
            label=drink_cfg.label,
            spillable=True,
        )
    )

    host.memes["boldness"] = BOLDNESS_INIT
    helper.memes["care"] = initial_care(trait)
    room.meters["mess"] = 0.0
    sill.meters["occupied"] = 0.0
    pet.meters["jump"] = 0.0
    pet.meters["jump_risk"] = 0.0
    cup.meters["spilled"] = 0.0
    cup.meters["fallen"] = 0.0

    introduce(world, host, helper, room_cfg)
    choose_menu(world, host, snack_cfg, drink_cfg, room_cfg)

    world.para()
    warn(world, helper, host, snack_cfg, parent, pet)
    averted = would_avert(relation, host_age, helper_age, trait)

    if averted:
        back_down(world, host, helper, parent, fix_cfg)
    else:
        defy(world, host, helper)
        world.para()
        place_on_sill(world, host)
        cat_pounces(world, pet, drink_cfg)
        world.para()
        if cleanup_succeeds(fix_cfg, drink_cfg, delay):
            cleanup(world, parent, fix_cfg, host, helper)
            better_plan(world, parent, host, helper, snack_cfg, fix_cfg, pet)
        else:
            raise StoryError("The chosen cleanup method is too weak for this spill.")

    outcome = "averted" if averted else "cleaned"
    world.facts.update(
        room_cfg=room_cfg,
        snack_cfg=snack_cfg,
        drink_cfg=drink_cfg,
        fix_cfg=fix_cfg,
        host=host,
        helper=helper,
        parent=parent,
        pet=pet,
        outcome=outcome,
        relation=relation,
        host_age=host_age,
        helper_age=helper_age,
        trait=trait,
        delay=delay,
        spill_happened=cup.meters["fallen"] >= THRESHOLD,
        improved_plan=True,
    )
    return world


ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="kitchen",
        has_sill=True,
        window_view="Outside, a pear tree bobbed in the breeze",
        prop="a blue bread box",
        tags={"window", "kitchen"},
    ),
    "bedroom": Room(
        id="bedroom",
        label="bedroom",
        has_sill=True,
        window_view="Outside, the garden fence looked like a stage for sparrows",
        prop="a lopsided stack of picture books",
        tags={"window", "bedroom"},
    ),
    "sunroom": Room(
        id="sunroom",
        label="sunroom",
        has_sill=True,
        window_view="Outside, the yard glittered and every leaf looked ready for applause",
        prop="a sleepy fern",
        tags={"window", "sunroom"},
    ),
    "hall": Room(
        id="hall",
        label="hall",
        has_sill=False,
        window_view="There was hardly any place to set even a pebble",
        prop="a shoe basket",
        tags={"hall"},
    ),
}

SNACKS = {
    "seeds": Snack(
        id="seeds",
        label="sunflower seeds",
        phrase="a neat pinch of sunflower seeds",
        bird_safe=True,
        tempting=True,
        qa_reason="Little birds really do peck seeds, so the idea at least sounds possible.",
        tags={"bird", "seeds"},
    ),
    "apple": Snack(
        id="apple",
        label="apple bits",
        phrase="a few tiny apple bits",
        bird_safe=True,
        tempting=True,
        qa_reason="Small fruit pieces can interest birds, especially when set out quietly.",
        tags={"bird", "fruit"},
    ),
    "crumbs": Snack(
        id="crumbs",
        label="crumbs",
        phrase="a few plain crumbs",
        bird_safe=True,
        tempting=True,
        qa_reason="Crumbs are the sort of thing a child would think a bird might nibble.",
        tags={"bird", "crumbs"},
    ),
    "cupcake": Snack(
        id="cupcake",
        label="cupcake",
        phrase="half a cupcake with pink icing",
        bird_safe=False,
        tempting=True,
        qa_reason="A cupcake is a silly café treat for children, not a sensible snack to offer a bird.",
        tags={"cake"},
    ),
}

DRINKS = {
    "lemonade": Drink(
        id="lemonade",
        label="lemonade",
        phrase="a tiny cup of lemonade",
        splash="the lemonade leapt out in a bright yellow splash",
        severity=2,
        tags={"drink", "spill"},
    ),
    "cocoa": Drink(
        id="cocoa",
        label="cocoa",
        phrase="a tiny cup of cocoa",
        splash="the cocoa made a soft brown loop through the air",
        severity=2,
        tags={"drink", "spill"},
    ),
    "water": Drink(
        id="water",
        label="water",
        phrase="a little cup of water",
        splash="the water tipped over in a clear slap on the floorboards",
        severity=1,
        tags={"drink", "spill"},
    ),
}

FIXES = {
    "towel": Fix(
        id="towel",
        sense=2,
        power=2,
        text="snatched up a towel, wiped the puddle fast, and set the cup safely on the counter",
        qa_text="wiped the spill quickly with a towel and moved the cup away from the sill",
        safe_plan="putting the bird snack in a little dish outside the window and keeping drinks on the table",
        tags={"towel", "cleanup"},
    ),
    "tray": Fix(
        id="tray",
        sense=3,
        power=3,
        text="slid a tray under the mess, mopped the drops, and rescued the cup before it rolled farther",
        qa_text="used a tray and cloth to catch the mess and rescue the cup",
        safe_plan="using a tray on the table by the window and setting the bird snack in a safer dish",
        tags={"tray", "cleanup"},
    ),
    "sock": Fix(
        id="sock",
        sense=1,
        power=1,
        text="dabbed at the floor with a lonely sock",
        qa_text="dabbed at the spill with a sock",
        safe_plan="using a safer tray instead",
        tags={"sock"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "steady", "practical", "thoughtful", "curious", "bouncy"]
PET_NAMES = ["Pudding", "Muffin", "Pickles", "Biscuit"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for room_id, room in ROOMS.items():
        for snack_id, snack in SNACKS.items():
            if plan_valid(room, snack):
                combos.append((room_id, snack_id))
    return combos


@dataclass
class StoryParams:
    room: str
    snack: str
    drink: str
    fix: str
    host: str
    host_gender: str
    helper: str
    helper_gender: str
    parent: str
    pet: str
    trait: str
    delay: int = 0
    host_age: int = 5
    helper_age: int = 7
    relation: str = "siblings"
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
    "bird": [
        (
            "What do small birds like to eat?",
            "Many small birds like seeds or tiny bits of fruit. Sweet human treats are not the best choice for them."
        )
    ],
    "seeds": [
        (
            "Why are seeds a more sensible bird snack than cake?",
            "Seeds are something birds really peck for food. Cake is made for people and is mostly a silly pretend-café idea."
        )
    ],
    "fruit": [
        (
            "Can birds eat little fruit pieces?",
            "Some birds do peck at small fruit pieces. They still need the food put somewhere safe and quiet."
        )
    ],
    "crumbs": [
        (
            "Why might a child offer crumbs to a bird?",
            "A child may notice that birds peck little bits from the ground. So crumbs can seem like a reasonable bird snack in a pretend game."
        )
    ],
    "spill": [
        (
            "Why can a cup on a window sill make a mess?",
            "A cup on a sill can wobble if it gets bumped. If it tips over, the drink splashes down and makes the floor messy."
        )
    ],
    "towel": [
        (
            "What is a towel good for in a spill?",
            "A towel soaks up liquid quickly. That makes it useful when a small spill happens on the floor."
        )
    ],
    "tray": [
        (
            "Why is a tray helpful near food and drinks?",
            "A tray gives cups and dishes a flatter place to sit. It also helps catch drips before they spread."
        )
    ],
    "window": [
        (
            "What is a window sill?",
            "A window sill is the flat ledge at the bottom of a window. It can hold little things, but it is not always a safe table."
        )
    ],
}
KNOWLEDGE_ORDER = ["window", "bird", "seeds", "fruit", "crumbs", "spill", "towel", "tray"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    helper = f["helper"]
    snack = f["snack_cfg"]
    room = f["room_cfg"]
    if f["outcome"] == "averted":
        return [
            f'Write a funny dialogue story for a 3-to-5-year-old about two children opening a pretend bird café on a window sill in a {room.label}. Include the word "sill".',
            f"Tell a comedy where {host.id} has a silly plan for a bird guest, but {helper.id} talks {host.pronoun('object')} out of balancing everything on the sill.",
            f'Write a gentle story with lots of dialogue where a child says something grand and silly, then changes the plan before any mess happens.',
        ]
    return [
        f'Write a funny dialogue story for a 3-to-5-year-old about a child making a pretend bird café on a window sill in a {room.label}. Include the word "sill".',
        f"Tell a comedy where {host.id} puts a drink and {snack.label} on the sill, a pet makes trouble, and a grown-up helps turn the mess into a better plan.",
        f'Write a dialogue-heavy story where a silly indoor café idea becomes a safer outdoor bird snack at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    helper = f["helper"]
    parent = f["parent"]
    pet = f["pet"]
    snack = f["snack_cfg"]
    drink = f["drink_cfg"]
    fix = f["fix_cfg"]
    room = f["room_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {host.id} and {helper.id}, who tried to make a Bird Café by the window, plus {parent.label_word} and {pet.id}. The joke begins because the children treat the sill as if it were a grand restaurant table."
        ),
        (
            "What did the children want to do?",
            f"They wanted to serve a tiny bird guest from the window sill with {snack.label} and {drink.label}. The plan was funny because they gave the bird a much fancier café than any bird had asked for."
        ),
        (
            f"Why did {helper.id} warn {host.id}?",
            f"{helper.id} noticed that {pet.id} was already interested in the snack and guessed the sill plan would turn messy. In the world model, food on the sill made the pet a jump risk, and that could knock the cup down."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                "Did anything spill?",
                f"No. {host.id} listened before setting the café on the sill, so the cup stayed safe and the floor stayed clean. The warning changed the plan before the pet could leap."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children laughing and making a safer bird-snack plan with {parent.label_word}. The sill was left empty, which proves they learned it was not a good café table."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {pet.id} jumped?",
                f"{pet.id} sprang toward the sill, the cup wobbled, and the {drink.label} spilled. The mess happened because the snack tempted the pet and the sill setup put the cup in the way."
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} {fix.qa_text}. Then {parent.pronoun()} helped the children move to {fix.safe_plan}, so the story turned from a spill into a better idea."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"At first the children treated the sill like a bird café table. At the end, the drink was kept away from the sill and the bird snack was moved to a safer place, so the ending image shows a wiser plan."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["room_cfg"].tags) | set(f["snack_cfg"].tags) | set(f["drink_cfg"].tags)
    tags |= set(f["fix_cfg"].tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if e.bird_safe:
            flags.append("bird_safe")
        if e.spillable:
            flags.append("spillable")
        if e.has_sill:
            flags.append("has_sill")
        if e.tempting:
            flags.append("tempting")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="kitchen",
        snack="seeds",
        drink="lemonade",
        fix="tray",
        host="Lily",
        host_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        pet="Pudding",
        trait="careful",
        delay=0,
        host_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        room="bedroom",
        snack="apple",
        drink="cocoa",
        fix="towel",
        host="Ben",
        host_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        pet="Muffin",
        trait="steady",
        delay=0,
        host_age=4,
        helper_age=6,
        relation="siblings",
    ),
    StoryParams(
        room="sunroom",
        snack="crumbs",
        drink="water",
        fix="tray",
        host="Ava",
        host_gender="girl",
        helper="Noah",
        helper_gender="boy",
        parent="mother",
        pet="Pickles",
        trait="curious",
        delay=0,
        host_age=6,
        helper_age=5,
        relation="friends",
    ),
]


def explain_rejection(room: Room, snack: Snack) -> str:
    if not room.has_sill:
        return (
            f"(No story: the {room.label} does not really offer a usable sill, so the whole sill-café plan has nowhere honest to happen.)"
        )
    if not snack.bird_safe:
        return (
            f"(No story: {snack.label} is a funny treat for children, but not a sensible snack to offer a bird. Pick seeds, crumbs, or apple bits instead.)"
        )
    return "(No story: this plan is not reasonable in this world.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing cleanup '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.host_age, params.helper_age, params.trait):
        return "averted"
    return "cleaned"


ASP_RULES = r"""
usable_plan(Room, Snack) :- room(Room), has_sill(Room), snack(Snack), bird_safe(Snack), tempting(Snack).
sensible(Fix) :- fix(Fix), sense(Fix,S), sense_min(M), S >= M.
valid(Room, Snack) :- usable_plan(Room, Snack).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).
older_helper :- relation(siblings), host_age(H), helper_age(He), He > H.
bonus(2) :- older_helper.
bonus(0) :- not older_helper.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- older_helper, authority(A), boldness_init(B), A > B.

spill_severity(V + D) :- chosen_drink(DR), drink_severity(DR,V), delay(D).
cleanup_ok :- chosen_fix(Fix), fix_power(Fix,P), spill_severity(S), P >= S.

outcome(averted) :- averted.
outcome(cleaned) :- not averted, cleanup_ok.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.has_sill:
            lines.append(asp.fact("has_sill", rid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.bird_safe:
            lines.append(asp.fact("bird_safe", sid))
        if snack.tempting:
            lines.append(asp.fact("tempting", sid))
    for did, drink in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("drink_severity", did, drink.severity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("fix_power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_drink", params.drink),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("host_age", params.host_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Dialogue-heavy comedy storyworld about a bird café on a window sill."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra mess head-start for cleanup")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (room, snack) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.snack:
        room = ROOMS[args.room]
        snack = SNACKS[args.snack]
        if not plan_valid(room, snack):
            raise StoryError(explain_rejection(room, snack))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.snack is None or combo[1] == args.snack)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, snack_id = rng.choice(sorted(combos))
    drink_id = args.drink or rng.choice(sorted(DRINKS))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    host, host_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=host)
    parent = args.parent or rng.choice(["mother", "father"])
    pet = rng.choice(PET_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    host_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        room=room_id,
        snack=snack_id,
        drink=drink_id,
        fix=fix_id,
        host=host,
        host_gender=host_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        pet=pet,
        trait=trait,
        delay=delay,
        host_age=host_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"Unknown room: {params.room}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.drink not in DRINKS:
        raise StoryError(f"Unknown drink: {params.drink}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")

    room_cfg = ROOMS[params.room]
    snack_cfg = SNACKS[params.snack]
    drink_cfg = DRINKS[params.drink]
    fix_cfg = FIXES[params.fix]

    if not plan_valid(room_cfg, snack_cfg):
        raise StoryError(explain_rejection(room_cfg, snack_cfg))
    if fix_cfg.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not cleanup_succeeds(fix_cfg, drink_cfg, params.delay):
        raise StoryError("This cleanup method cannot honestly handle that spill.")

    world = tell(
        room_cfg=room_cfg,
        snack_cfg=snack_cfg,
        drink_cfg=drink_cfg,
        fix_cfg=fix_cfg,
        host_name=params.host,
        host_gender=params.host_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        pet_name=params.pet,
        pet_type="cat",
        trait=params.trait,
        delay=params.delay,
        host_age=params.host_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (room, snack) combos:\n")
        for room, snack in combos:
            print(f"  {room:8} {snack}")
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
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.host} & {p.helper}: {p.snack} on the sill in the {p.room} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
