#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py
================================================================================

A standalone storyworld for a nursery-rhyme-style forest-trail tale with a
repetitive hidden sound, a teasing mistake, a lesson learned, and
reconciliation.

Premise
-------
Two children walk along a forest trail. A small hidden creature makes a
repetitive sound -- sometimes "boog, boog" -- from a nook beside the path.
One child is tempted to answer the sound as a joke. The other child warns that
mystery sounds should be met with gentle listening, not teasing. Depending on
their relationship and the cautioner's authority, the teasing is either averted
or it happens and must be repaired with a sincere, effective act of making up.

The world model tracks physical state (steps off the trail, startle, hiding,
returning) and emotional state (fear, guilt, trust, warmth). The prose is
driven by those changes rather than by slot-swapping a frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py --spot stump_nook --creature bog_toad
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py --tool tapping_stick
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py --repair shrug
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py --all
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/repetitive_boog_forest_trail_lesson_learned_sound.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "gentle", "steady", "kind"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Spot:
    id: str
    label: str
    phrase: str
    path_line: str
    echoey: bool = False
    shelters: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    label: str
    little: str
    sound: str
    call: str
    sign: str
    emerge: str
    spook: int = 1
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    sounds: set[str] = field(default_factory=set)
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
class Repair:
    id: str
    sense: int
    power: int
    label: str
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_tease_startle(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teased") and not world.facts.get("startle_applied"):
        world.facts["startle_applied"] = True
        creature = world.get("creature")
        cautioner = world.get("cautioner")
        spot = world.get("spot")
        creature.meters["startled"] += 1
        cautioner.memes["fear"] += 1
        cautioner.memes["hurt"] += 1
        cautioner.memes["trust"] -= 1
        if spot.attrs.get("echoey"):
            cautioner.memes["fear"] += 1
        out.append("__startle__")
    return out


def _r_fear_step(world: World) -> list[str]:
    out: list[str] = []
    cautioner = world.get("cautioner")
    if cautioner.memes["fear"] >= THRESHOLD:
        sig = ("fear_step", cautioner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            cautioner.meters["off_trail"] += 1
            world.facts["cautioner_stepped_aside"] = True
            out.append("__step__")
    return out


def _r_gentle_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("repair_done") and not world.facts.get("repair_applied"):
        world.facts["repair_applied"] = True
        instigator = world.get("instigator")
        cautioner = world.get("cautioner")
        creature = world.get("creature")
        cautioner.memes["fear"] = max(0.0, cautioner.memes["fear"] - 2.0)
        cautioner.memes["hurt"] = max(0.0, cautioner.memes["hurt"] - 1.0)
        cautioner.memes["trust"] += 2.0
        cautioner.memes["warmth"] += 1.0
        instigator.memes["guilt"] = max(0.0, instigator.memes["guilt"] - 1.0)
        instigator.memes["warmth"] += 1.0
        creature.meters["startled"] = 0.0
        if cautioner.meters["off_trail"] >= THRESHOLD:
            cautioner.meters["off_trail"] = 0.0
            cautioner.meters["on_trail"] += 1.0
        out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule(name="tease_startle", tag="social", apply=_r_tease_startle),
    Rule(name="fear_step", tag="physical", apply=_r_fear_step),
    Rule(name="gentle_repair", tag="social", apply=_r_gentle_repair),
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


def habitat_match(spot: Spot, creature: Creature) -> bool:
    return creature.id in spot.shelters


def tool_matches(tool: Tool, creature: Creature) -> bool:
    return creature.sound in tool.sounds


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def severity(spot: Spot, creature: Creature) -> int:
    return creature.spook + (1 if spot.echoey else 0)


def repair_works(repair: Repair, spot: Spot, creature: Creature) -> bool:
    return repair.power >= severity(spot, creature)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_tease(world: World) -> dict:
    sim = world.copy()
    sim.facts["teased"] = True
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("cautioner").memes["fear"],
        "off_trail": sim.get("cautioner").meters["off_trail"],
        "startled": sim.get("creature").meters["startled"],
    }


def opening(world: World, a: Entity, b: Entity, spot: Spot) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"Down the forest trail went {a.id} and {b.id}, tip-tap, twig-snap, "
        f"past fern and feather and {spot.path_line}."
    )
    world.say(
        f"They walked in a little repetitive marching rhyme -- "
        f'"step and peep, step and peep" -- because the morning felt small and sweet.'
    )


def hear_sound(world: World, b: Entity, spot: Spot, creature: Creature) -> None:
    creature.meters["calling"] += 1
    world.say(
        f"Then from {spot.phrase} came a sound: "
        f'"{creature.call}! {creature.call}!" Soft first, then round and deep.'
    )
    world.say(
        f'{b.id} stopped under the leaves. "{creature.sound}," {b.pronoun()} whispered. '
        f'"Who could be hiding there?"'
    )


def tempt(world: World, a: Entity, tool: Tool) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} lifted {tool.phrase}. "{tool.action}," {a.pronoun()} said. '
        f'"I can answer it back."'
    )


def warn(world: World, b: Entity, a: Entity, creature: Creature, spot: Spot) -> None:
    pred = predict_tease(world)
    b.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_off_trail"] = pred["off_trail"]
    extra = " The trees would only make the teasing louder." if spot.echoey else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"Let the hidden thing be, {a.id}. A strange little voice may be shy.{extra}"'
    )


def back_down(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    b.memes["warmth"] += 1
    world.say(
        f"{a.id} lowered {tool.phrase} and gave a small nod. "
        f'"You are right," {a.pronoun()} said. "No teasing on the trail."'
    )


def tease(world: World, a: Entity, tool: Tool, creature: Creature) -> None:
    a.memes["defiance"] += 1
    world.facts["teased"] = True
    propagate(world, narrate=False)
    world.say(
        f"But {a.id} could not resist. {a.pronoun().capitalize()} {tool.action.lower()}, "
        f'and sang back, "{creature.call}! {creature.call}!"'
    )


def startle_beat(world: World, b: Entity, creature: Creature) -> None:
    a = world.get("instigator")
    if world.facts.get("cautioner_stepped_aside"):
        world.say(
            f"{b.id} jumped back from the edge of the trail with a rustle-rush of leaves. "
            f'The joke did not feel funny now. "{a.id}," {b.id} said, "that scared me."'
        )
    else:
        world.say(
            f"{b.id} flinched, and the hidden creature tucked itself in even tighter. "
            f'The joke did not feel funny now.'
        )
    a.memes["guilt"] += 2.0


def discover(world: World, a: Entity, b: Entity, creature: Creature, spot: Spot) -> None:
    creature.meters["seen"] += 1
    world.say(
        f"They waited. Rustle... blink... out from {spot.phrase} peeped {creature.little}, "
        f"with {creature.sign}."
    )
    world.say(
        f"It was only {creature.label}, not a monster at all, just small and alive and "
        f"busy with its own forest morning."
    )


def repair_scene(world: World, a: Entity, b: Entity, repair: Repair) -> None:
    world.facts["repair_done"] = True
    world.facts["repair_id"] = repair.id
    propagate(world, narrate=False)
    world.say(
        f"{a.id}'s cheeks grew warm. {a.pronoun().capitalize()} {repair.text}"
    )
    world.say(
        f"{b.id} listened, then stepped close again until both children stood "
        f"together on the trail."
    )


def lesson_close(world: World, a: Entity, b: Entity, creature: Creature, spot: Spot, av: bool) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"So they learned a trail-song lesson: when a hidden voice says "
        f'"{creature.call}," you do not mock it, you listen softly first.'
    )
    if av:
        world.say(
            f'{a.id} and {b.id} smiled at each other and went on with gentle feet -- '
            f'"step and peep, step and peep" -- while {creature.little} stayed calm in {spot.label}.'
        )
    else:
        world.say(
            f'{a.id} and {b.id} made up beside the moss and walked on hand in hand -- '
            f'"step and peep, step and peep" -- while behind them came one last quiet "{creature.sound}".'
        )


def tell(
    spot: Spot,
    creature: Creature,
    tool: Tool,
    repair: Repair,
    *,
    instigator: str = "Pip",
    instigator_gender: str = "boy",
    cautioner: str = "Moss",
    cautioner_gender: str = "girl",
    trait: str = "gentle",
    relation: str = "friends",
    instigator_age: int = 5,
    cautioner_age: int = 5,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"display": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"display": cautioner, "relation": relation},
    ))
    c = world.add(Entity(
        id="creature",
        kind="thing",
        type="creature",
        label=creature.label,
        attrs={"sound": creature.sound},
    ))
    s = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        attrs={"echoey": spot.echoey},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = 1.0
    b.memes["caution"] = initial_caution(trait)
    c.meters["calling"] = 0.0
    c.meters["startled"] = 0.0
    c.meters["seen"] = 0.0
    b.meters["off_trail"] = 0.0
    b.meters["on_trail"] = 0.0
    world.facts.update(
        teased=False,
        startle_applied=False,
        repair_done=False,
        repair_applied=False,
        cautioner_stepped_aside=False,
    )

    opening(world, a, b, spot)
    hear_sound(world, b, spot, creature)

    world.para()
    tempt(world, a, tool)
    warn(world, b, a, creature, spot)

    av = would_avert(relation, instigator_age, cautioner_age, trait)
    if av:
        back_down(world, a, b, tool)
        world.para()
        discover(world, a, b, creature, spot)
        world.say(
            f'{a.label} bent low and whispered, "Hush and kind, hush and kind." '
            f'{b.label} smiled because the forest felt friendly again.'
        )
    else:
        world.say(f'"Only once," {a.label} said, and answered anyway.')
        world.para()
        tease(world, a, tool, creature)
        startle_beat(world, b, creature)
        discover(world, a, b, creature, spot)
        world.para()
        repair_scene(world, a, b, repair)

    world.para()
    lesson_close(world, a, b, creature, spot, av)

    world.facts.update(
        instigator=a,
        cautioner=b,
        creature_cfg=creature,
        creature=c,
        spot_cfg=spot,
        spot=s,
        tool=tool,
        repair=repair,
        relation=relation,
        outcome="averted" if av else "mended",
        teased=not av,
        seen_creature=c.meters["seen"] >= THRESHOLD,
        learned=True,
    )
    return world


SPOTS = {
    "stump_nook": Spot(
        id="stump_nook",
        label="the stump nook",
        phrase="a hollow stump by the trail",
        path_line="a bend with a hollow stump",
        echoey=True,
        shelters={"bog_toad", "beetle_drummer"},
        tags={"trail", "stump"},
    ),
    "mossy_log": Spot(
        id="mossy_log",
        label="the mossy log",
        phrase="a mossy log beside the path",
        path_line="a green log soft with moss",
        echoey=False,
        shelters={"bog_toad", "beetle_drummer"},
        tags={"trail", "log"},
    ),
    "branch_bend": Spot(
        id="branch_bend",
        label="the branch bend",
        phrase="a bent branch over the path",
        path_line="a bend where branches arched overhead",
        echoey=False,
        shelters={"owl"},
        tags={"trail", "branch"},
    ),
    "bridge_rail": Spot(
        id="bridge_rail",
        label="the bridge rail",
        phrase="the old rail of a little wooden bridge",
        path_line="a wooden bridge over a shallow runnel",
        echoey=True,
        shelters={"owl", "beetle_drummer"},
        tags={"trail", "bridge"},
    ),
    "pebble_turn": Spot(
        id="pebble_turn",
        label="the pebble turn",
        phrase="a bare pebble turn in the trail",
        path_line="a bright curve of pebbles",
        echoey=False,
        shelters=set(),
        tags={"trail", "pebbles"},
    ),
}

CREATURES = {
    "bog_toad": Creature(
        id="bog_toad",
        label="a little bog toad",
        little="a little bog toad",
        sound="boog",
        call="boog, boog",
        sign="two shiny bead-eyes and a round brown back",
        emerge="hopped out in one soft plop",
        spook=2,
        tags={"toad", "boog", "trail_listen"},
    ),
    "owl": Creature(
        id="owl",
        label="a young owl",
        little="a young owl",
        sound="hoo",
        call="hoo, hoo",
        sign="wide gold eyes and tiny tucked claws",
        emerge="blinked from under a branch",
        spook=1,
        tags={"owl", "night_sounds", "trail_listen"},
    ),
    "beetle_drummer": Creature(
        id="beetle_drummer",
        label="a beetle tapping wood",
        little="a shiny beetle drummer",
        sound="tok",
        call="tok, tok",
        sign="a bright shell and clever little legs",
        emerge="crept out and tapped once more",
        spook=1,
        tags={"beetle", "forest_sounds", "trail_listen"},
    ),
}

TOOLS = {
    "cupped_hands": Tool(
        id="cupped_hands",
        label="cupped hands",
        phrase="her hands by her mouth" if False else "cupped hands",
        action="made a tiny tunnel with the hands",
        sounds={"boog", "hoo"},
        tags={"echo", "voice"},
    ),
    "bark_horn": Tool(
        id="bark_horn",
        label="a bark horn",
        phrase="a bark horn",
        action="put the bark horn to the lips",
        sounds={"boog", "hoo"},
        tags={"echo", "bark"},
    ),
    "tapping_stick": Tool(
        id="tapping_stick",
        label="a tapping stick",
        phrase="a tapping stick",
        action="tapped the stick on the rail",
        sounds={"tok"},
        tags={"tap", "stick"},
    ),
    "leaf_whistle": Tool(
        id="leaf_whistle",
        label="a leaf whistle",
        phrase="a leaf whistle",
        action="blew the leaf whistle",
        sounds={"chee"},
        tags={"whistle"},
    ),
}

REPAIRS = {
    "held_hand": Repair(
        id="held_hand",
        sense=3,
        power=3,
        label="held hands",
        text='said, "I am sorry for my teasing," and held out a hand, palm open and still.',
        qa_text="apologized and held out a hand",
        tags={"apology", "hands"},
    ),
    "sorry_song": Repair(
        id="sorry_song",
        sense=3,
        power=4,
        label="sorry song",
        text='sang a soft sorry-song: "kind and slow, kind and slow," so the trail felt gentle again.',
        qa_text="sang a soft sorry-song and apologized",
        tags={"apology", "song"},
    ),
    "berry_share": Repair(
        id="berry_share",
        sense=2,
        power=2,
        label="berry share",
        text='offered the last berry from the pocket and said, "I was wrong to make that joke."',
        qa_text="shared a berry and admitted the joke was wrong",
        tags={"apology", "sharing"},
    ),
    "shrug": Repair(
        id="shrug",
        sense=1,
        power=0,
        label="shrug",
        text='only shrugged and muttered, "It was just a sound."',
        qa_text="shrugged instead of truly apologizing",
        tags={"poor_repair"},
    ),
}

GIRL_NAMES = ["Pip", "Mira", "Tansy", "Wren", "Nell", "Ivy", "Lark", "Mabel"]
BOY_NAMES = ["Pip", "Bram", "Milo", "Ash", "Rowan", "Finn", "Ned", "Toby"]
TRAITS = ["careful", "gentle", "steady", "kind", "curious", "bright"]


@dataclass
class StoryParams:
    spot: str
    creature: str
    tool: str
    repair: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    trait: str
    relation: str = "friends"
    instigator_age: int = 5
    cautioner_age: int = 5
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
    "trail": [
        (
            "What should you do when you hear a strange sound on a forest trail?",
            "Stop and listen first. Strange sounds often come from small animals, so kind, quiet looking is better than teasing or stomping."
        )
    ],
    "toad": [
        (
            "What is a toad?",
            "A toad is a small animal with dry, bumpy skin. It often stays low to the ground and can hide in damp places."
        )
    ],
    "owl": [
        (
            "Why do owls make sounds?",
            "Owls call to talk to other owls and to tell where they are. Their calls can sound big in the trees, even when the owl is small."
        )
    ],
    "beetle": [
        (
            "Can tiny creatures make big sounds in the woods?",
            "Yes. A small creature tapping wood or rustling leaves can sound much bigger when the forest echoes around it."
        )
    ],
    "boog": [
        (
            'What does the sound word "boog" mean in this story?',
            '"Boog" is a playful sound word. It helps the story sound like a rhyme and lets the hidden call feel round and funny instead of plain.'
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what was wrong and tries to make things gentler. It helps the hurt person feel seen and safe again."
        )
    ],
    "song": [
        (
            "Why can a soft song calm someone down?",
            "A soft song slows the moment and makes voices gentle. That can help a scared friend feel less shaky."
        )
    ],
    "sharing": [
        (
            "How can sharing help after a mistake?",
            "Sharing by itself does not fix everything, but it can show kindness when it comes with honest words. The important part is admitting the mistake too."
        )
    ],
}
KNOWLEDGE_ORDER = ["trail", "toad", "owl", "beetle", "boog", "apology", "song", "sharing"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for creature_id, creature in CREATURES.items():
            if not habitat_match(spot, creature):
                continue
            for tool_id, tool in TOOLS.items():
                if not tool_matches(tool, creature):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair.sense < SENSE_MIN:
                        continue
                    if not repair_works(repair, spot, creature):
                        continue
                    combos.append((spot_id, creature_id, tool_id, repair_id))
    return combos


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    creature = f["creature_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a nursery-rhyme-style story set on a forest trail where two children hear a repetitive '
        f'"{creature.call}" from {spot.label}. Include the word "boog" if it fits the sound-play.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle forest-trail story where {a.label} wants to answer the hidden sound as a joke, "
            f"but {b.label} stops the teasing before it begins and the children learn to listen kindly.",
            "Write a short rhyming story with sound effects, a lesson learned, and a peaceful ending where the children stay gentle with a hidden woodland creature.",
        ]
    return [
        base,
        f"Tell a nursery-rhyme story where {a.label} teases a hidden trail sound, {b.label} gets scared, and the children reconcile with a sincere apology.",
        "Write a child-facing rhyme with sound effects, a small mistake, a lesson learned, and reconciliation at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    creature = f["creature_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool"]
    repair = f["repair"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, walking together on a forest trail. They hear a hidden sound and must decide whether to tease it or treat it gently."
        ),
        (
            "What sound did the children hear?",
            f"They heard {creature.call} coming from {spot.phrase}. The repetitive sound made the forest feel mysterious and drew both children closer."
        ),
        (
            f"Why did {b.label} warn {a.label} not to answer back?",
            f"{b.label} thought the hidden creature might be shy and that teasing would make the moment worse. The warning was about kindness as much as caution."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.label} do after the warning?",
                f"{a.label} lowered {tool.label} and decided not to tease the sound. That choice kept the trail calm, so the children could discover the small creature gently."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that when a strange voice says {creature.call}, it is better to listen softly first. The ending shows the lesson because the trail stays peaceful and the creature stays calm."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.label} answered the sound back?",
                f"{b.label} got scared, and the hidden creature was startled too. The teasing made the mystery feel sharper instead of kinder, so the trail moment turned tense."
            )
        )
        qa.append(
            (
                f"How did {a.label} make things right with {b.label}?",
                f"{a.label} {repair.qa_text}. That helped {b.label} step close again because the apology was gentle enough to mend the hurt."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with reconciliation: the children made up and walked on together. The final image proves what changed because they moved forward side by side instead of startled apart."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"trail", "apology"}
    creature = f["creature_cfg"]
    repair = f["repair"]
    if "boog" in creature.tags:
        tags.add("boog")
    if creature.id == "bog_toad":
        tags.add("toad")
    if creature.id == "owl":
        tags.add("owl")
    if creature.id == "beetle_drummer":
        tags.add("beetle")
    if repair.id == "sorry_song":
        tags.add("song")
    if repair.id == "berry_share":
        tags.add("sharing")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spot="stump_nook",
        creature="bog_toad",
        tool="bark_horn",
        repair="held_hand",
        instigator="Pip",
        instigator_gender="boy",
        cautioner="Mabel",
        cautioner_gender="girl",
        trait="gentle",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        spot="branch_bend",
        creature="owl",
        tool="cupped_hands",
        repair="sorry_song",
        instigator="Ivy",
        instigator_gender="girl",
        cautioner="Ash",
        cautioner_gender="boy",
        trait="careful",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
    ),
    StoryParams(
        spot="mossy_log",
        creature="beetle_drummer",
        tool="tapping_stick",
        repair="berry_share",
        instigator="Rowan",
        instigator_gender="boy",
        cautioner="Nell",
        cautioner_gender="girl",
        trait="steady",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        spot="bridge_rail",
        creature="owl",
        tool="bark_horn",
        repair="sorry_song",
        instigator="Wren",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        trait="kind",
        relation="siblings",
        instigator_age=5,
        cautioner_age=8,
    ),
]


def explain_rejection(spot: Spot, creature: Creature, tool: Tool, repair: Repair) -> str:
    if not habitat_match(spot, creature):
        return (
            f"(No story: {creature.label} does not plausibly hide at {spot.label}. "
            f"Pick a spot that could shelter that creature.)"
        )
    if not tool_matches(tool, creature):
        return (
            f"(No story: {tool.label} does not fit the sound '{creature.sound}'. "
            f"Pick a tool that can answer that kind of call.)"
        )
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it is too weak on common sense for a reconciliation story. "
            f"Use a sincere repair such as held_hand, sorry_song, or berry_share.)"
        )
    if not repair_works(repair, spot, creature):
        return (
            f"(No story: {repair.label} is too weak for how startling this trail echo would feel. "
            f"Choose a stronger repair so the ending can truly reconcile.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
habitat(S, C) :- spot(S), creature(C), shelters(S, C).
mimics(T, C)  :- tool(T), creature(C), creature_sound(C, Sd), tool_sound(T, Sd).
sensible(R)   :- repair(R), sense(R, S), sense_min(M), S >= M.
sev(S, C, V)  :- creature_spook(C, Sp), echoey(S), V = Sp + 1.
sev(S, C, V)  :- creature_spook(C, Sp), not echoey(S), V = Sp.
repair_works(S, C, R) :- sev(S, C, V), repair_power(R, P), P >= V.

valid(S, C, T, R) :- habitat(S, C), mimics(T, C), sensible(R), repair_works(S, C, R).

cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(mended)  :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.echoey:
            lines.append(asp.fact("echoey", sid))
        for cid in sorted(spot.shelters):
            lines.append(asp.fact("shelters", sid, cid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("creature_sound", cid, creature.sound))
        lines.append(asp.fact("creature_spook", cid, creature.spook))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for snd in sorted(tool.sounds):
            lines.append(asp.fact("tool_sound", tid, snd))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("repair_power", rid, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(
        params.relation, params.instigator_age, params.cautioner_age, params.trait
    ) else "mended"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_repairs()}
    if clingo_sens == python_sens:
        print(f"OK: sensible repairs match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed on seed {s}")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False)
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme forest-trail storyworld with a repetitive hidden sound, a lesson learned, and reconciliation."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.creature and args.tool and args.repair:
        spot = SPOTS[args.spot]
        creature = CREATURES[args.creature]
        tool = TOOLS[args.tool]
        repair = REPAIRS[args.repair]
        if (args.spot, args.creature, args.tool, args.repair) not in set(valid_combos()):
            raise StoryError(explain_rejection(spot, creature, tool, repair))
    elif args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_rejection(
            SPOTS[next(iter(SPOTS))],
            CREATURES[next(iter(CREATURES))],
            TOOLS[next(iter(TOOLS))],
            REPAIRS[args.repair],
        ))

    combos = [
        c for c in valid_combos()
        if (args.spot is None or c[0] == args.spot)
        and (args.creature is None or c[1] == args.creature)
        and (args.tool is None or c[2] == args.tool)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        spot = SPOTS[args.spot] if args.spot else SPOTS[next(iter(SPOTS))]
        creature = CREATURES[args.creature] if args.creature else CREATURES[next(iter(CREATURES))]
        tool = TOOLS[args.tool] if args.tool else TOOLS[next(iter(TOOLS))]
        repair = REPAIRS[args.repair] if args.repair else REPAIRS[next(iter(REPAIRS))]
        raise StoryError(explain_rejection(spot, creature, tool, repair))

    spot_id, creature_id, tool_id, repair_id = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        spot=spot_id,
        creature=creature_id,
        tool=tool_id,
        repair=repair_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"Unknown spot '{params.spot}'.")
    if params.creature not in CREATURES:
        raise StoryError(f"Unknown creature '{params.creature}'.")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool '{params.tool}'.")
    if params.repair not in REPAIRS:
        raise StoryError(f"Unknown repair '{params.repair}'.")

    if (params.spot, params.creature, params.tool, params.repair) not in set(valid_combos()):
        raise StoryError(explain_rejection(
            SPOTS[params.spot], CREATURES[params.creature], TOOLS[params.tool], REPAIRS[params.repair]
        ))

    world = tell(
        SPOTS[params.spot],
        CREATURES[params.creature],
        TOOLS[params.tool],
        REPAIRS[params.repair],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, creature, tool, repair) combos:\n")
        for spot, creature, tool, repair in combos:
            print(f"  {spot:12} {creature:15} {tool:13} {repair}")
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
                f"### {p.instigator} & {p.cautioner}: {p.creature} at {p.spot} "
                f"with {p.tool} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
