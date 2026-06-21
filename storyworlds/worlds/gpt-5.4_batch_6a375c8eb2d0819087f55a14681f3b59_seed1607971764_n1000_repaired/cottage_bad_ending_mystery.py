#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py
========================================================

A standalone story world for a small cottage mystery with a possible bad ending.

Premise
-------
On a stormy night in a cottage, two children hear a strange sound from somewhere
inside the house. One wants to solve the mystery at once. The other warns that
the place is dark and dangerous. If they wake the caretaker and use a proper
light, the mystery is solved safely. If the bold child sneaks off alone, the
night ends badly: the child is trapped and frightened until morning.

This world models:
- a clue from a place in the cottage,
- a hidden cause that must plausibly fit that clue,
- a caution beat grounded in the danger of the location,
- a decision (wait or sneak),
- and either a safe reveal or a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py --location attic --clue tapping
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py --light candle
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/cottage_bad_ending_mystery.py --verify
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
SENSE_MIN = 2
COTTAGE_NAME = "the old cottage"
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}
BRAVERY_INIT = 6.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
class Location:
    id: str
    label: str
    phrase: str
    entry: str
    hazard: int
    danger_text: str
    trap_text: str
    dawn_text: str
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
class Clue:
    id: str
    sound: str
    line: str
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
class Source:
    id: str
    label: str
    location: str
    clues: set[str]
    reveal: str
    fix: str
    unresolved: str
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
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    power: int
    sense: int
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
class Method:
    id: str
    label: str
    support: int
    sense: int
    with_caretaker: bool
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


# ---------------------------------------------------------------------------
# Rules
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


def _r_bad_investigation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("instigator")
    source = world.get("source")
    place = world.get("place")
    if hero.meters["investigating"] < THRESHOLD:
        return out
    if world.facts["support"] >= world.facts["hazard"]:
        return out
    sig = ("bad", hero.id, place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["trapped"] += 1
    hero.memes["fear"] += 2
    hero.memes["regret"] += 1
    place.meters["danger"] += 1
    source.meters["unresolved"] += 1
    out.append("__bad__")
    return out


def _r_safe_investigation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("instigator")
    source = world.get("source")
    if hero.meters["investigating"] < THRESHOLD:
        return out
    if world.facts["support"] < world.facts["hazard"]:
        return out
    sig = ("safe", hero.id, source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["found"] += 1
    hero.memes["relief"] += 1
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    out.append("__safe__")
    return out


def _r_pipe_spreads_water(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    cottage = world.get("cottage")
    if source.attrs.get("kind") != "pipe":
        return out
    if source.meters["unresolved"] < THRESHOLD:
        return out
    sig = ("water", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cottage.meters["water"] += 1
    out.append("__water__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bad_investigation", tag="physical", apply=_r_bad_investigation),
    Rule(name="safe_investigation", tag="physical", apply=_r_safe_investigation),
    Rule(name="pipe_spreads_water", tag="physical", apply=_r_pipe_spreads_water),
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


# ---------------------------------------------------------------------------
# Reasonableness / outcome helpers
# ---------------------------------------------------------------------------
def clue_matches(location: str, source: Source, clue: str) -> bool:
    return source.location == location and clue in source.clues


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc_id in LOCATIONS:
        for clue_id in CLUES:
            for src_id, src in SOURCES.items():
                if clue_matches(loc_id, src, clue_id):
                    combos.append((loc_id, clue_id, src_id))
    return combos


def sensible_lights() -> list[Light]:
    return [light for light in LIGHTS.values() if light.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "solved"
    support = METHODS[params.method].support + LIGHTS[params.light].power
    hazard = LOCATIONS[params.location].hazard
    return "solved" if support >= hazard else "trapped"


def explain_combo_rejection(location: str, clue: str, source: str) -> str:
    return (
        f"(No story: {CLUES[clue].sound} from the {LOCATIONS[location].label} does not fit "
        f"{SOURCES[source].label}. Pick a cause that could honestly make that sound there.)"
    )


def explain_light_rejection(light_id: str) -> str:
    light = LIGHTS[light_id]
    better = ", ".join(sorted(l.id for l in sensible_lights()))
    return (
        f"(Refusing light '{light_id}': it scores too low on common sense "
        f"(sense={light.sense} < {SENSE_MIN}). A dark mystery in a cottage needs a steadier, "
        f"safer light. Try: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_danger(world: World) -> dict:
    sim = world.copy()
    sim.get("instigator").meters["investigating"] += 1
    propagate(sim, narrate=False)
    return {
        "trapped": sim.get("instigator").meters["trapped"] >= THRESHOLD,
        "water": sim.get("cottage").meters["water"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, a: Entity, b: Entity, cottage: Entity) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"Rain pressed against the windows of {cottage.label}, and the rooms seemed to listen back. "
        f"{a.id} and {b.id} sat wrapped in blankets while the wind moved through the eaves."
    )


def sound_arrives(world: World, clue: Clue, place: Location) -> None:
    world.say(
        f"Then they heard it: {clue.line} from {place.phrase}. "
        f"The sound came, stopped, and came again, as if the house were trying to whisper."
    )


def tempt(world: World, a: Entity, clue: Clue, place: Location) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"Did you hear that?" {a.id} whispered. "If we go to the {place.label} now, we can solve the mystery before anybody else does."'
    )


def warn(world: World, b: Entity, a: Entity, caretaker: Entity, place: Location) -> None:
    pred = predict_danger(world)
    b.memes["caution"] += 1
    world.facts["predicted_trapped"] = pred["trapped"]
    world.facts["predicted_water"] = pred["water"]
    extra = ""
    if pred["trapped"]:
        extra = " If someone went alone, the night could turn from exciting to frightening in one breath."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{place.danger_text}. '
        f'We should wake {caretaker.label_word} first."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, caretaker: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} listened to {b.id} for a long moment, then let out the breath "
        f"{a.pronoun()} had been holding. Together they padded to {caretaker.label_word}'s room instead of chasing the noise alone."
    )


def defy(world: World, a: Entity, b: Entity, method: Method, light: Light) -> None:
    a.memes["defiance"] += 1
    if method.with_caretaker:
        world.say(
            f'"Maybe you are right," {a.id} said at last. {a.pronoun().capitalize()} took {light.phrase} and hurried to wake a grown-up.'
        )
    else:
        world.say(
            f'"It will only take one peek," {a.id} whispered. Before {b.id} could stop {a.pronoun("object")}, '
            f'{a.pronoun()} snatched up {light.phrase} and slipped away alone.'
        )


def investigate(world: World, a: Entity, caretaker: Entity, method: Method, light: Light, place: Location) -> None:
    a.meters["investigating"] += 1
    world.facts["used_light"] = light.id
    if method.with_caretaker:
        world.say(
            f"{caretaker.label_word.capitalize()} opened the door at once, saw their pale faces, "
            f"and came with them holding {light.phrase} that {light.glow}. "
            f"Together they moved toward the {place.label}, listening for the sound."
        )
    else:
        world.say(
            f"The small beam from {light.phrase} shook over the walls as {a.id} crept toward the {place.label}. "
            f"Every board in {COTTAGE_NAME} seemed louder than the mystery itself."
        )
    propagate(world, narrate=False)


def reveal_safe(world: World, caretaker: Entity, source_cfg: Source, place: Location) -> None:
    source = world.get("source")
    source.meters["found"] += 0  # keep the state explicit for trace readability
    world.say(
        f"At the {place.label}, the mystery opened all at once: it was {source_cfg.reveal}. "
        f"{caretaker.label_word.capitalize()} {source_cfg.fix}, and the frightening sound stopped."
    )


def quiet_ending(world: World, a: Entity, b: Entity, caretaker: Entity, place: Location) -> None:
    for kid in (a, b):
        kid.memes["safe"] += 1
    world.say(
        f"Back in bed, {a.id} and {b.id} listened to the new quiet. {a.id} smiled in the dark, "
        f"because the cottage no longer felt full of secrets; it felt like a house that had finally told the truth."
    )


def bad_turn(world: World, a: Entity, place: Location) -> None:
    a.meters["trapped"] += 0
    world.say(place.trap_text)
    world.say(
        f'{a.id} called out once, then again, but the storm swallowed the sound. '
        f'Soon the mystery was not the noise anymore. It was how long the dark could feel.'
    )


def dawn_rescue(world: World, a: Entity, b: Entity, caretaker: Entity, source_cfg: Source, place: Location) -> None:
    cottage = world.get("cottage")
    water_note = ""
    if cottage.meters["water"] >= THRESHOLD:
        water_note = " A shallow sheet of water had spread over the stones during the night."
    world.say(
        f"Gray morning finally reached the windows of {COTTAGE_NAME}. {caretaker.label_word.capitalize()} found {a.id}, pale and shivering, "
        f"and pulled {a.pronoun('object')} out at once.{water_note}"
    )
    world.say(
        f"Only then did the mystery give up its name: it had been {source_cfg.reveal}. "
        f"But the answer felt small after such a long night."
    )
    world.say(place.dawn_text)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    instigator: Instigator,
    instigator_gender: str,
    cautioner: Cautioner,
    cautioner_gender: str,
    trait: str,
    parent_type: ParentType,
    relation: Relation,
    instigator_age: InstigatorAge,
    cautioner_age: CautionerAge,
) -> World:
    world = World()
    cottage = world.add(Entity(id="cottage", type="cottage", label=COTTAGE_NAME))
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            age=instigator_age,
            attrs={"name": instigator, "relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"name": cautioner, "relation": relation},
        )
    )
    caretaker = world.add(
        Entity(
            id="caretaker",
            kind="character",
            type=parent_type,
            label="the caretaker",
            role="caretaker",
        )
    )
    place = world.add(
        Entity(
            id="place",
            type="place",
            label=location_cfg.label,
            attrs={"entry": location_cfg.entry, "hazard": location_cfg.hazard},
        )
    )
    source = world.add(
        Entity(
            id="source",
            type="source",
            label=source_cfg.label,
            attrs={"kind": source_cfg.id},
        )
    )
    lamp = world.add(
        Entity(
            id="light",
            type="light",
            label=light_cfg.label,
            attrs={"sense": light_cfg.sense, "power": light_cfg.power},
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    world.facts.update(
        location_cfg=location_cfg,
        clue_cfg=clue_cfg,
        source_cfg=source_cfg,
        light_cfg=light_cfg,
        method_cfg=method_cfg,
        hazard=location_cfg.hazard,
        support=method_cfg.support + light_cfg.power,
        relation=relation,
    )

    introduce(world, a, b, cottage)
    sound_arrives(world, clue_cfg, location_cfg)

    world.para()
    tempt(world, a, clue_cfg, location_cfg)
    warn(world, b, a, caretaker, location_cfg)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, caretaker)
        world.para()
        investigate(world, a, caretaker, METHODS["wake_caretaker"], light_cfg, location_cfg)
        reveal_safe(world, caretaker, source_cfg, location_cfg)
        quiet_ending(world, a, b, caretaker, location_cfg)
        outcome = "solved"
    else:
        defy(world, a, b, method_cfg, light_cfg)
        world.para()
        investigate(world, a, caretaker, method_cfg, light_cfg, location_cfg)
        if outcome_of(
            StoryParams(
                location=location_cfg.id,
                clue=clue_cfg.id,
                source=source_cfg.id,
                light=light_cfg.id,
                method=method_cfg.id,
                instigator=instigator,
                instigator_gender=instigator_gender,
                cautioner=cautioner,
                cautioner_gender=cautioner_gender,
                parent=parent_type,
                trait=trait,
                relation=relation,
                instigator_age=instigator_age,
                cautioner_age=cautioner_age,
                seed=None,
            )
        ) == "solved":
            reveal_safe(world, caretaker, source_cfg, location_cfg)
            quiet_ending(world, a, b, caretaker, location_cfg)
            outcome = "solved"
        else:
            bad_turn(world, a, location_cfg)
            world.para()
            dawn_rescue(world, a, b, caretaker, source_cfg, location_cfg)
            outcome = "trapped"

    world.facts.update(
        instigator=a,
        cautioner=b,
        caretaker=caretaker,
        place=place,
        source=source,
        light=lamp,
        outcome=outcome,
        solved=source.meters["found"] >= THRESHOLD,
        trapped=a.meters["trapped"] >= THRESHOLD,
        averted=averted,
    )
    return world


# ---------------------------------------------------------------------------
# Content
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


LOCATIONS = {
    "attic": Location(
        id="attic",
        label="attic",
        phrase="above the narrow attic door",
        entry="ladder",
        hazard=3,
        danger_text="The attic ladder wobbles, and the roof is low and dark",
        trap_text=(
            "Halfway up, a rung groaned and gave way. The light skipped wildly, boxes slid, "
            "and the child ended up stranded in a pocket of dust and darkness near the top"
        ),
        dawn_text=(
            "After that, nobody in the cottage called the night thrilling. The attic kept its dust, "
            "but it lost its magic"
        ),
        tags={"attic", "night"},
    ),
    "cellar": Location(
        id="cellar",
        label="cellar",
        phrase="below the kitchen floor",
        entry="steps",
        hazard=3,
        danger_text="The cellar steps are slick with damp, and the old latch likes to stick",
        trap_text=(
            "At the bottom, the door swung hard behind the child and the latch caught. The air turned cold, "
            "the stones smelled of wet earth, and the narrow room became a trap"
        ),
        dawn_text=(
            "After that, the cellar was only a cellar again. No one pretended it held adventures worth a night of fear"
        ),
        tags={"cellar", "night"},
    ),
}

CLUES = {
    "tapping": Clue(
        id="tapping",
        sound="a tapping noise",
        line="a light tapping, quick and patient",
        tags={"sound", "tapping"},
    ),
    "scratching": Clue(
        id="scratching",
        sound="a scratching noise",
        line="a dry scratching, like tiny nails on wood",
        tags={"sound", "scratching"},
    ),
    "dripping": Clue(
        id="dripping",
        sound="a dripping noise",
        line="slow dripping into metal, plink after plink",
        tags={"sound", "dripping"},
    ),
    "clinking": Clue(
        id="clinking",
        sound="a clinking noise",
        line="a careful clinking, glass touching glass",
        tags={"sound", "clinking"},
    ),
}

SOURCES = {
    "shutter": Source(
        id="shutter",
        label="a loose shutter",
        location="attic",
        clues={"tapping"},
        reveal="a loose shutter knocking the roof window whenever the wind pushed it",
        fix="pulled the shutter tight and fastened it with a strip of cord",
        unresolved="the shutter kept knocking in the dark",
        tags={"shutter", "wind"},
    ),
    "squirrel": Source(
        id="squirrel",
        label="a squirrel",
        location="attic",
        clues={"scratching"},
        reveal="a small squirrel nosing through a basket of pinecones near the rafters",
        fix="opened the tiny side window and shooed the squirrel back into the rain-wet trees",
        unresolved="the squirrel kept scratching among the rafters",
        tags={"animal", "attic"},
    ),
    "pipe": Source(
        id="pipe",
        label="a cracked pipe",
        location="cellar",
        clues={"dripping"},
        reveal="a cracked pipe dripping into an old tin pail in the corner",
        fix="turned the little wheel to slow the leak and set a bigger bucket underneath",
        unresolved="the pipe kept dripping and the puddle kept widening",
        tags={"pipe", "water"},
    ),
    "jars": Source(
        id="jars",
        label="a shelf of jars",
        location="cellar",
        clues={"clinking"},
        reveal="wind from a loose vent making a shelf of old jars knock softly together",
        fix="closed the vent and steadied the jars with a folded cloth",
        unresolved="the jars kept clinking each time the wind slipped in",
        tags={"jars", "wind"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="the old lantern",
        glow="cast a warm, steady circle",
        power=1,
        sense=3,
        tags={"lantern", "light"},
    ),
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="cut a clean white path through the dark",
        power=1,
        sense=3,
        tags={"flashlight", "light"},
    ),
    "candle": Light(
        id="candle",
        label="candle",
        phrase="a little candle",
        glow="flickered weakly in every draft",
        power=0,
        sense=1,
        tags={"candle", "light"},
    ),
}

METHODS = {
    "wake_caretaker": Method(
        id="wake_caretaker",
        label="wake the caretaker",
        support=2,
        sense=3,
        with_caretaker=True,
        tags={"adult_help", "safe_choice"},
    ),
    "sneak_alone": Method(
        id="sneak_alone",
        label="sneak off alone",
        support=1,
        sense=2,
        with_caretaker=False,
        tags={"alone", "bad_choice"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Zoe", "Ava", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Max", "Theo", "Leo", "Finn", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "quiet"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space up under the roof of a house. It is often dusty and dark, so people should be careful there.",
        )
    ],
    "cellar": [
        (
            "What is a cellar?",
            "A cellar is a room under a house, often cool and damp. Old cellars can be slippery, so children should not explore them alone.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with a protected light inside. It can make the dark easier to see, but children still need a grown-up in risky places.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small electric light you can carry in your hand. It helps you see in the dark, but it does not make unsafe places safe by itself.",
        )
    ],
    "candle": [
        (
            "Why is a candle a poor choice for exploring?",
            "A candle gives only a small, shaky light, and it can go out or drip wax. In an old house, a steadier and safer light is better.",
        )
    ],
    "adult_help": [
        (
            "Why should children wake a grown-up if they hear a scary noise at night?",
            "A grown-up can bring better light, know the house, and help if something goes wrong. Asking for help is wiser than chasing a mystery alone.",
        )
    ],
    "pipe": [
        (
            "Why does a cracked pipe make a dripping sound?",
            "Water slips out one drop at a time and falls onto the floor or into a bucket. That makes a repeated plink or drip sound.",
        )
    ],
    "shutter": [
        (
            "Why can a loose shutter tap in the wind?",
            "Wind can push it against the wall or window again and again. That makes a tapping sound that can seem mysterious at night.",
        )
    ],
    "animal": [
        (
            "Why do animals make scratching sounds in walls or attics?",
            "Small animals have claws and quick feet, so they scrape wood when they move. In a quiet house at night, those little sounds can seem very loud.",
        )
    ],
    "night": [
        (
            "Why do ordinary sounds seem scarier at night?",
            "Night is quieter, and you cannot see as much, so your mind has to guess what made the noise. That can make a normal sound feel much bigger and stranger.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "attic",
    "cellar",
    "lantern",
    "flashlight",
    "candle",
    "adult_help",
    "pipe",
    "shutter",
    "animal",
    "night",
]


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
    place = f["location_cfg"]
    clue = f["clue_cfg"]
    outcome = f["outcome"]
    if outcome == "trapped":
        return [
            f'Write a short mystery story for a 3-to-5-year-old set in a cottage, where children hear {clue.sound} from the {place.label} and the ending is bad.',
            f"Tell a gentle-but-scary mystery where {a.label} wants to solve a noise in the {place.label}, ignores {b.label}'s warning, and the night ends badly.",
            f'Write a cottage mystery that teaches children not to chase strange sounds alone at night, and end with a sad morning-after image.',
        ]
    return [
        f'Write a short mystery story for a 3-to-5-year-old set in a cottage, where children hear {clue.sound} from the {place.label} and a grown-up helps solve it.',
        f"Tell a cozy mystery where {a.label} and {b.label} hear a strange sound in the cottage and learn what it really was.",
        f'Write a simple mystery with the word "cottage" that begins with a frightening noise and ends with the house feeling safe again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    caretaker = f["caretaker"]
    place = f["location_cfg"]
    clue = f["clue_cfg"]
    source_cfg = f["source_cfg"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, spending a stormy night in a cottage. A caretaker is there too, but the mystery begins with the children hearing the sound first.",
        ),
        (
            "What mystery did the children notice?",
            f"They heard {clue.sound} coming from the {place.label}. Because the storm and the dark made the cottage feel secretive, the sound seemed much stranger than it really was.",
        ),
        (
            f"Why did {b.label} want to wake a grown-up first?",
            f"{b.label} knew that {place.danger_text.lower()}. {b.pronoun().capitalize()} was not only scared of the noise; {b.pronoun()} was scared that chasing it alone could turn dangerous.",
        ),
    ]
    if f["outcome"] == "solved":
        qa.append(
            (
                "What was the mystery really?",
                f"It was {source_cfg.reveal}. Once the caretaker came with proper light, the sound stopped feeling magical and became an ordinary problem with an ordinary cause.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the noise explained and the cottage quiet again. The ending proves that the house changed from a frightening mystery back into a home.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.label} went after the sound alone?",
                f"{a.label} got trapped in the {place.label} and had to stay there until morning. The bad ending came because curiosity was stronger than caution, and the dark place became more dangerous than mysterious.",
            )
        )
        qa.append(
            (
                "Did the children solve the mystery in a happy way?",
                f"No. By morning they learned the cause was {source_cfg.reveal}, but that answer did not feel exciting anymore. The night had already ended badly, so the truth came with relief instead of triumph.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["location_cfg"].tags) | set(f["source_cfg"].tags) | set(f["light_cfg"].tags)
    tags |= set(f["method_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, 0)}
            if shown:
                bits.append(f"attrs={shown}")
        label = e.label or e.id
        lines.append(f"  {label:18} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    clue: str
    source: str
    light: str
    method: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        location="attic",
        clue="tapping",
        source="shutter",
        light="lantern",
        method="sneak_alone",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        location="cellar",
        clue="dripping",
        source="pipe",
        light="flashlight",
        method="sneak_alone",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        location="attic",
        clue="scratching",
        source="squirrel",
        light="lantern",
        method="wake_caretaker",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        location="cellar",
        clue="clinking",
        source="jars",
        light="flashlight",
        method="wake_caretaker",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Rose",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(L, C, S) :- location(L), clue(C), source(S), source_at(S, L), clue_of(S, C).
sensible_light(Li) :- light(Li), light_sense(Li, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

support(MS + LP) :- chosen_method(M), method_support(M, MS),
                    chosen_light(Li), light_power(Li, LP).
hazard(H) :- chosen_location(L), risk(L, H).

outcome(solved)  :- averted.
outcome(solved)  :- not averted, support(S), hazard(H), S >= H.
outcome(trapped) :- not averted, support(S), hazard(H), S < H.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        lines.append(asp.fact("risk", lid, loc.hazard))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("source_at", sid, src.location))
        for clue_id in sorted(src.clues):
            lines.append(asp.fact("clue_of", sid, clue_id))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("light_sense", lid, light.sense))
        lines.append(asp.fact("light_power", lid, light.power))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_support", mid, method.support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_lights() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_light/1."))
    return sorted(l for (l,) in asp.atoms(model, "sensible_light"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_location", params.location),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_method", params.method),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: compatibility gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_lights = set(asp_sensible_lights())
    p_lights = {light.id for light in sensible_lights()}
    if c_lights == p_lights:
        print(f"OK: sensible lights match ({sorted(c_lights)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible lights: clingo={sorted(c_lights)} python={sorted(p_lights)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a cottage mystery with a possible bad ending. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.light and LIGHTS[args.light].sense < SENSE_MIN:
        raise StoryError(explain_light_rejection(args.light))
    if args.location and args.clue and args.source:
        if not clue_matches(args.location, SOURCES[args.source], args.clue):
            raise StoryError(explain_combo_rejection(args.location, args.clue, args.source))

    combos = [
        c
        for c in valid_combos()
        if (args.location is None or c[0] == args.location)
        and (args.clue is None or c[1] == args.clue)
        and (args.source is None or c[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    location, clue, source = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(l.id for l in sensible_lights()))
    method = args.method or rng.choice(sorted(METHODS))
    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        location=location,
        clue=clue,
        source=source,
        light=light,
        method=method,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("location", LOCATIONS),
        ("clue", CLUES),
        ("source", SOURCES),
        ("light", LIGHTS),
        ("method", METHODS),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value})")
    if not clue_matches(params.location, SOURCES[params.source], params.clue):
        raise StoryError(explain_combo_rejection(params.location, params.clue, params.source))
    if LIGHTS[params.light].sense < SENSE_MIN:
        raise StoryError(explain_light_rejection(params.light))

    world = tell(
        LOCATIONS[params.location],
        CLUES[params.clue],
        SOURCES[params.source],
        LIGHTS[params.light],
        METHODS[params.method],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
    )
    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
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
        print(asp_program("", "#show valid/3.\n#show sensible_light/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible lights: {', '.join(asp_sensible_lights())}\n")
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (location, clue, source) mystery triples:\n")
        for location, clue, source in triples:
            print(f"  {location:8} {clue:10} {source}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.instigator} & {p.cautioner}: {p.clue} in the {p.location} "
                f"({p.source}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
