#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/senator_bruise_incentive_dialogue_kindness_misunderstanding_bedtime.py
======================================================================================================

A small bedtime-style story world about a child, a senator toy, a bruise, and a
kind misunderstanding that is repaired with gentle dialogue.

Premise
-------
A child gets a bruise during an ordinary bedtime moment, then mistakes an adult's
careful incentive for a scolding. The misunderstanding is cleared up by talking
kindly, and the ending shows comfort and safety returning.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in the simulated world
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
SLEEPY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return {"mother": "mom", "father": "dad", "senator": "senator"}.get(self.type, self.type)
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
    bedtime_image: str
    cozy_detail: str
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
class CharacterCfg:
    id: str
    type: str
    label: str
    bedside_role: str
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
class Incident:
    id: str
    bruise_kind: str
    cause: str
    bruise_line: str
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
class Incentive:
    id: str
    label: str
    promise: str
    kind: str
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
    healing: int
    text: str
    fail: str
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


def _r_bruise_spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["bruise"] < THRESHOLD:
            continue
        sig = ("bruise_spook", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in list(world.entities.values()):
            if other.kind == "character" and other.id != ent.id:
                other.memes["worry"] += 1
        out.append("__spook__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["warmth"] += 1
        out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("bruise_spook", "social", _r_bruise_spook), Rule("kindness", "social", _r_kindness)]


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


def bedside_literally_safe(setting: Setting) -> bool:
    return "bed" in setting.place or "bedtime" in setting.tags


def reasonable_combo(setting: Setting, incident: Incident, incentive: Incentive, response: Response) -> bool:
    return bedside_literally_safe(setting) and incident.bruise_kind in {"knee", "elbow", "hand"} and response.sense >= SLEEPY_MIN and incentive.kind in {"rest", "bandage", "story"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for iid, inc in INCIDENTS.items():
            for x, incent in INCENTIVES.items():
                for rid, resp in RESPONSES.items():
                    if reasonable_combo(s, inc, incent, resp):
                        combos.append((sid, iid, x, rid))
    return combos


def explain_rejection(setting: Setting, incident: Incident, incentive: Incentive, response: Response) -> str:
    return "(No story: this bedtime scene needs a gentle bruise, a kind incentive, and a calm response that actually fits the moment.)"


def predict_misunderstanding(world: World, child_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.memes["worry"] += 1
    child.memes["misunderstanding"] += 1
    return {"worry": child.memes["worry"], "misunderstanding": child.memes["misunderstanding"]}


def setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["sleepiness"] += 1
    world.say(f"It was bedtime, and {child.id} was tucked into {setting.place}. {setting.bedtime_image} {setting.cozy_detail}")


def incident(world: World, child: Entity, inc: Incident) -> None:
    child.meters["bruise"] += 1
    child.memes["surprise"] += 1
    world.say(f"Somehow, {child.id} got {inc.bruise_line}.")


def incentive_scene(world: World, adult: Entity, child: Entity, incent: Incentive) -> None:
    adult.memes["kindness"] += 1
    world.say(f"{adult.id} smiled softly. \"{incent.promise}\" {adult.pronoun()} said.")


def misunderstanding(world: World, child: Entity, adult: Entity, incent: Incentive) -> None:
    pred = predict_misunderstanding(world, child.id)
    child.memes["misunderstanding"] += 1
    if pred["misunderstanding"] >= THRESHOLD:
        world.say(f"{child.id} blinked and looked worried, thinking {adult.id}'s words meant something stricter than they did.")
    world.say(f"\"Are you mad?\" {child.id} whispered.")
    world.say(f"\"No,\" {adult.id} said. \"{incent.promise}\"")


def answer(world: World, adult: Entity, child: Entity, response: Response) -> None:
    child.memes["worry"] = 0
    child.memes["comfort"] += 1
    child.memes["trust"] += 1
    adult.memes["warmth"] += 1
    world.say(f"{adult.id} took a careful look and {response.text}.")
    propagate(world, narrate=False)


def ending(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(f"After that, {child.id} relaxed against the blankets while {adult.id} sat beside {child.pronoun('object')}.")
    world.say(f"The bruise was still there, but the worry was gone, and the room felt as quiet as a lullaby.")


def tell(setting: Setting, incident_cfg: Incident, incentive_cfg: Incentive, response: Response,
         child_name: str = "Nina", child_gender: str = "girl",
         adult_name: str = "Aunt May", adult_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.add(Entity(id="room", type="room", label=setting.place))
    setup(world, child, adult, setting)
    world.para()
    incident(world, child, incident_cfg)
    incentive_scene(world, adult, child, incentive_cfg)
    world.para()
    misunderstanding(world, child, adult, incentive_cfg)
    answer(world, adult, child, response)
    world.para()
    ending(world, child, adult, setting)
    world.facts.update(
        child=child, adult=adult, setting=setting, incident=incident_cfg, incentive=incentive_cfg,
        response=response, bruised=child.meters["bruise"] >= THRESHOLD,
        misunderstood=child.memes["misunderstanding"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(id="bedroom", place="the little bedroom", bedtime_image="The lamp glowed like a sleepy moon.", cozy_detail="A stuffed rabbit watched over the pillows.", tags={"bedtime"}),
    "nursery": Setting(id="nursery", place="the nursery", bedtime_image="The curtain made a soft shadow over the crib.", cozy_detail="A rocking chair waited in the corner.", tags={"bedtime"}),
    "atticbed": Setting(id="atticbed", place="the attic bedroom", bedtime_image="The skylight showed one tiny star.", cozy_detail="A wool blanket lay folded at the foot of the bed.", tags={"bedtime"}),
}

INCIDENTS = {
    "knee": Incident(id="knee", bruise_kind="knee", cause="bumped a corner", bruise_line="a little bruise on a knee", tags={"bruise"}),
    "elbow": Incident(id="elbow", bruise_kind="elbow", cause="bumped a dresser", bruise_line="a bruise on an elbow", tags={"bruise"}),
    "hand": Incident(id="hand", bruise_kind="hand", cause="caught a hand on the bedframe", bruise_line="a small bruise on a hand", tags={"bruise"}),
}

INCENTIVES = {
    "story": Incentive(id="story", label="story", promise="If you rest now, I'll tell you a gentle story.", kind="story", tags={"kindness"}),
    "bandage": Incentive(id="bandage", label="bandage", promise="This bandage will help, and then we can cuddle the bruise better.", kind="bandage", tags={"kindness"}),
    "rest": Incentive(id="rest", label="rest", promise="You can rest here and feel better before morning.", kind="rest", tags={"kindness"}),
}

RESPONSES = {
    "ice": Response(id="ice", sense=3, healing=3, text="found a cool cloth and held it on the bruise until the ache calmed down", fail="tried a cool cloth, but the bruise was still too sore", qa_text="held a cool cloth on the bruise until the ache calmed down", tags={"help"}),
    "hug": Response(id="hug", sense=3, healing=2, text="gave a soft hug and tucked the blanket in just right", fail="gave a soft hug, but the worry still stayed put", qa_text="gave a soft hug and tucked the blanket in", tags={"comfort"}),
    "rest": Response(id="rest", sense=2, healing=2, text="turned off the lamp and let the child rest with a sleepy sigh", fail="turned off the lamp, but the child still felt upset", qa_text="turned off the lamp and let the child rest", tags={"rest"}),
}

CURATED = [
    StoryParams()  # placeholder replaced below
]

CURATED = [
    StoryParams(),
]
