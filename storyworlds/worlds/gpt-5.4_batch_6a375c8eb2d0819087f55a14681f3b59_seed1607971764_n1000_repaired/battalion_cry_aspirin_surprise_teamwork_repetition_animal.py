#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py
=======================================================================================

A standalone storyworld about small animals who hear a cry, form a battalion,
and work together to move a fallen aspirin tin away from a burrow door.

The domain is intentionally small and state-driven:
- a named animal battalion is practicing together,
- a trapped youngster cries for help,
- the group chooses a method that may or may not need a surprise helper,
- repeated chants coordinate the teamwork,
- the ending image proves that fear turned into brave belonging.

Run it
------
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py --all
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py --qa
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py --asp
python storyworlds/worlds/gpt-5.4/battalion_cry_aspirin_surprise_teamwork_repetition_animal.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck"}
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
class Place:
    id: str
    label: str
    scene: str
    terrain: str
    need: int
    sight: str
    surprise: str
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
class Battalion:
    id: str
    label: str
    captain: str
    species: str
    members: str
    strength: int
    practice: str
    chant: str
    closing: str
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
class Method:
    id: str
    label: str
    usable: set[str]
    power: int
    prep: str
    action: str
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
class Helper:
    id: str
    label: str
    bonus: int
    arrive: str
    action: str
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
class Victim:
    id: str
    name: str
    species: str
    home: str
    cry_text: str
    thanks: str
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


def _r_hope(world: World) -> list[str]:
    victim = world.get("victim")
    team = world.get("team")
    if victim.meters["trapped"] < THRESHOLD:
        return []
    if team.memes["comforting"] < THRESHOLD:
        return []
    sig = ("hope", victim.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    victim.memes["hope"] += 1
    victim.memes["fear"] = max(0.0, victim.memes["fear"] - 1.0)
    return []


def _r_free(world: World) -> list[str]:
    victim = world.get("victim")
    tin = world.get("tin")
    if victim.meters["trapped"] < THRESHOLD:
        return []
    if tin.meters["effort"] < tin.meters["need"]:
        return []
    sig = ("free", victim.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    victim.meters["trapped"] = 0.0
    tin.meters["blocking"] = 0.0
    victim.memes["relief"] += 1
    victim.memes["fear"] = 0.0
    world.get("team").memes["pride"] += 1
    world.get("captain").memes["relief"] += 1
    return []


def _r_join(world: World) -> list[str]:
    victim = world.get("victim")
    if victim.meters["trapped"] >= THRESHOLD:
        return []
    if victim.memes["belonging"] >= THRESHOLD:
        return []
    sig = ("join", victim.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    victim.memes["belonging"] += 1
    world.get("team").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hope", tag="emotional", apply=_r_hope),
    Rule(name="free", tag="physical", apply=_r_free),
    Rule(name="join", tag="social", apply=_r_join),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current = len(world.fired)
        if current > len(set(world.fired)):
            changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def works(place: Place, method: Method, battalion: Battalion, helper: Helper) -> bool:
    return place.terrain in method.usable and battalion.strength + method.power + helper.bonus >= place.need


def direct_enough(place: Place, method: Method, battalion: Battalion) -> bool:
    return place.terrain in method.usable and battalion.strength + method.power >= place.need


def rescue_outcome(place: Place, method: Method, battalion: Battalion, helper: Helper) -> str:
    if not works(place, method, battalion, helper):
        return "invalid"
    if direct_enough(place, method, battalion):
        return "direct"
    if helper.id != "none":
        return "assisted"
    return "invalid"


def predict_release(world: World, place: Place, method: Method, battalion: Battalion, helper: Helper) -> dict:
    sim = world.copy()
    tin = sim.get("tin")
    tin.meters["effort"] += battalion.strength + method.power + helper.bonus
    propagate(sim, narrate=False)
    return {
        "free": sim.get("victim").meters["trapped"] < THRESHOLD,
        "remaining": max(0, int(sim.get("tin").meters["need"] - sim.get("tin").meters["effort"])),
    }


def introduce(world: World, place: Place, battalion: Battalion, victim: Victim) -> None:
    captain = world.get("captain")
    team = world.get("team")
    team.memes["order"] += 1
    team.memes["joy"] += 1
    world.say(
        f"In {place.scene}, {battalion.label} marched behind {battalion.captain} the "
        f"{battalion.species}. They were practicing {battalion.practice}."
    )
    world.say(
        f'Again and again they called, "{battalion.chant}" The little line sounded so neat '
        f"that even the grasses seemed to stand straighter."
    )
    captain.memes["care"] += 1
    world.facts["first_chant"] = battalion.chant
    world.facts["victim_name"] = victim.name


def hear_cry(world: World, place: Place, victim: Victim) -> None:
    team = world.get("team")
    victim_ent = world.get("victim")
    victim_ent.meters["trapped"] = 1.0
    victim_ent.memes["fear"] = 2.0
    team.memes["worry"] += 1
    world.say(
        f"Then a small cry floated from {place.label}. "
        f'"Help, help!" it said. "{victim.cry_text}"'
    )
    world.say(
        f"The sound led them to an old aspirin tin that had rolled from a camper's blanket "
        f"and come to rest against {victim.home}."
    )


def inspect(world: World, place: Place, battalion: Battalion, method: Method, helper: Helper) -> None:
    captain = world.get("captain")
    team = world.get("team")
    team.memes["comforting"] = 1.0
    propagate(world, narrate=False)
    pred = predict_release(world, place, method, battalion, helper)
    world.facts["predicted_free"] = pred["free"]
    world.facts["predicted_remaining"] = pred["remaining"]
    helper_clause = ""
    if helper.id != "none" and not direct_enough(place, method, battalion):
        helper_clause = f" If someone else joined in, the plan might just work."
    world.say(
        f"{battalion.captain} put one ear to the cool tin and looked at {place.sight}. "
        f'"Do not be afraid," {captain.pronoun()} called. "We hear you, and we will work together."'
        f"{helper_clause}"
    )
    world.say(
        f"At once the battalion stopped fidgeting and listened for the next tiny sound."
    )


def prepare(world: World, battalion: Battalion, method: Method) -> None:
    world.say(
        f"First they {method.prep}. Then {battalion.captain} tapped the ground and called, "
        f'"{battalion.chant}"'
    )
    world.facts["second_chant"] = battalion.chant


def attempt_direct(world: World, place: Place, battalion: Battalion, method: Method) -> None:
    tin = world.get("tin")
    team = world.get("team")
    team.memes["teamwork"] += 1
    tin.meters["effort"] += battalion.strength + method.power
    propagate(world, narrate=False)
    world.say(
        f"They {method.action}. The aspirin tin gave a rusty scrape, tipped once, "
        f"and slid away from the door."
    )
    world.say(
        f'Out came {world.get("victim").label}, blinking hard. To everyone\'s surprise, '
        f'{world.get("victim").pronoun()} was the first one to laugh.'
    )


def attempt_assisted(world: World, place: Place, battalion: Battalion, method: Method, helper: Helper) -> None:
    tin = world.get("tin")
    team = world.get("team")
    team.memes["teamwork"] += 1
    direct_power = battalion.strength + method.power
    tin.meters["effort"] += direct_power
    world.say(
        f"They {method.action}, but the aspirin tin only shivered in the dirt. "
        f"It was heavier than it had looked."
    )
    world.say(
        f'Once more {battalion.captain} cried, "{battalion.chant}"'
    )
    world.say(helper.arrive)
    tin.meters["effort"] += helper.bonus
    world.get("helper").memes["helpful"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With {helper.action}, the tin hopped over a pebble and rolled clear of the door."
    )
    world.say(
        f'Out came {world.get("victim").label}, and to everyone\'s surprise, '
        f'{world.get("victim").pronoun()} joined the chant before anyone asked.'
    )


def celebrate(world: World, place: Place, battalion: Battalion, victim: Victim) -> None:
    victim_ent = world.get("victim")
    team = world.get("team")
    victim_ent.memes["gratitude"] += 1
    team.memes["joy"] += 1
    world.say(
        f'{victim.name} took a shaky breath and said, "{victim.thanks}"'
    )
    world.say(
        f"{place.surprise} The old aspirin tin was not scary anymore; it made a cheerful plink "
        f"when the breeze touched it."
    )
    world.say(
        f"Soon {victim.name} was marching beside the others, and the whole battalion sang, "
        f'"{battalion.closing}"'
    )


PLACES = {
    "fern_hollow": Place(
        id="fern_hollow",
        label="the mouth of a fern hollow",
        scene="the shady edge of the campsite",
        terrain="hollow",
        need=5,
        sight="the bent ferns and a narrow lip of earth",
        surprise="A ladybug landed on the tin like a red button and bobbed up and down.",
        tags={"camp", "hollow"},
    ),
    "pebble_path": Place(
        id="pebble_path",
        label="a pebble path by the picnic stump",
        scene="a sun-dappled clearing",
        terrain="flat",
        need=4,
        sight="the smooth pebbles and the place where the tin could roll",
        surprise="A hidden stripe of blue flowers behind the door seemed to wake up all at once.",
        tags={"camp", "path"},
    ),
    "muddy_bank": Place(
        id="muddy_bank",
        label="the muddy bank beside a rain puddle",
        scene="the soft, damp edge of the campsite",
        terrain="muddy",
        need=5,
        sight="the slick mud and the tiny ridges where paws had slipped",
        surprise="A water drop fell from a reed into the tin and rang like a bell.",
        tags={"camp", "mud"},
    ),
}

BATTALIONS = {
    "ant_battalion": Battalion(
        id="ant_battalion",
        label="the ant battalion",
        captain="Captain Pip",
        species="ant",
        members="ants",
        strength=2,
        practice="seed-carrying in a tidy line",
        chant="Shoulder, shuffle, shove!",
        closing="Shoulder, shuffle, smile!",
        tags={"ants", "teamwork"},
    ),
    "mouse_battalion": Battalion(
        id="mouse_battalion",
        label="the mouse battalion",
        captain="Captain Mallow",
        species="mouse",
        members="mice",
        strength=3,
        practice="acorn-rolling in pairs",
        chant="Push together, puff together, pop it free!",
        closing="Push together, puff together, friends are free!",
        tags={"mice", "teamwork"},
    ),
    "beetle_battalion": Battalion(
        id="beetle_battalion",
        label="the beetle battalion",
        captain="Captain Gloss",
        species="beetle",
        members="beetles",
        strength=2,
        practice="crumb-pushing in a shining row",
        chant="Lift low, lean slow, let it go!",
        closing="Lift low, laugh low, off we go!",
        tags={"beetles", "teamwork"},
    ),
}

METHODS = {
    "lever_stick": Method(
        id="lever_stick",
        label="a twig lever",
        usable={"flat", "hollow"},
        power=2,
        prep="nudged a strong twig under the rim",
        action="pressed the twig down together",
        qa_text="used a twig as a lever under the rim",
        tags={"lever"},
    ),
    "pebble_roll": Method(
        id="pebble_roll",
        label="pebble rollers",
        usable={"flat", "muddy"},
        power=2,
        prep="poked little pebbles beneath the edge",
        action="pushed and rolled the tin over the pebbles",
        qa_text="rolled the tin over little pebbles",
        tags={"rollers"},
    ),
    "shoulder_push": Method(
        id="shoulder_push",
        label="a shoulder push",
        usable={"flat"},
        power=1,
        prep="lined shoulder to shoulder along the rusty side",
        action="heaved with all their shoulders at once",
        qa_text="pushed with all their shoulders at once",
        tags={"push"},
    ),
}

HELPERS = {
    "none": Helper(
        id="none",
        label="no extra helper",
        bonus=0,
        arrive="",
        action="one more hard shove",
        qa_text="no extra helper was needed",
        tags=set(),
    ),
    "turtle": Helper(
        id="turtle",
        label="Tumble the turtle",
        bonus=2,
        arrive="Just then Tumble the turtle came plodding by, blinked at the trouble, and tucked his sturdy shell under the edge.",
        action="Tumble bracing from below while the battalion kept the chant steady",
        qa_text="Tumble the turtle braced the tin with his strong shell",
        tags={"turtle"},
    ),
    "frog": Helper(
        id="frog",
        label="Ploop the frog",
        bonus=1,
        arrive="Just then Ploop the frog sprang from the puddle, saw the struggle, and planted both springy feet against the rim.",
        action="Ploop kicking in time while the battalion shoved",
        qa_text="Ploop the frog kicked against the rim while the others shoved",
        tags={"frog"},
    ),
}

VICTIMS = {
    "vole": Victim(
        id="vole",
        name="Tizzy",
        species="vole",
        home="a tiny vole burrow",
        cry_text="the door is stuck, and I cannot squeeze out!",
        thanks="I thought I would have to sit in the dark all afternoon.",
        tags={"vole"},
    ),
    "mole": Victim(
        id="mole",
        name="Nub",
        species="mole",
        home="a snug mole tunnel",
        cry_text="the round thing rolled over my doorway!",
        thanks="My whiskers were shaking, but your marching feet sounded brave.",
        tags={"mole"},
    ),
    "shrew": Victim(
        id="shrew",
        name="Pipkin",
        species="shrew",
        home="a mossy shrew nook",
        cry_text="I gave one cry, and then another, but the tin would not listen!",
        thanks="When you answered my cry, the whole world felt bigger and kinder.",
        tags={"shrew"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for battalion_id, battalion in BATTALIONS.items():
            for method_id, method in METHODS.items():
                for helper_id, helper in HELPERS.items():
                    if works(place=place, method=method, battalion=battalion, helper=helper):
                        combos.append((place_id, battalion_id, method_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    battalion: str
    method: str
    helper: str
    victim: str
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


def tell(place: Place, battalion: Battalion, method: Method, helper: Helper, victim: Victim) -> World:
    outcome = rescue_outcome(place=place, method=method, battalion=battalion, helper=helper)
    if outcome == "invalid":
        raise StoryError(
            f"(No story: {battalion.label} using {method.label} at {place.label} "
            f"cannot move the aspirin tin. Choose a stronger plan or a helper.)"
        )

    world = World()
    captain = world.add(Entity(id="captain", kind="character", type=battalion.species, label=battalion.captain, role="captain"))
    team = world.add(Entity(id="team", kind="character", type=battalion.species, label=battalion.label, role="team"))
    victim_ent = world.add(Entity(id="victim", kind="character", type=victim.species, label=victim.name, role="victim"))
    tin = world.add(Entity(id="tin", kind="thing", type="tin", label="the aspirin tin", role="obstacle"))
    helper_ent = world.add(Entity(id="helper", kind="character", type="helper", label=helper.label, role="helper"))

    tin.meters["need"] = float(place.need)
    tin.meters["blocking"] = 1.0
    tin.meters["effort"] = 0.0
    victim_ent.meters["trapped"] = 0.0
    victim_ent.memes["fear"] = 0.0
    victim_ent.memes["hope"] = 0.0
    victim_ent.memes["relief"] = 0.0
    victim_ent.memes["belonging"] = 0.0
    team.memes["comforting"] = 0.0
    team.memes["teamwork"] = 0.0
    team.memes["joy"] = 0.0
    helper_ent.memes["helpful"] = 0.0

    introduce(world=world, place=place, battalion=battalion, victim=victim)
    hear_cry(world=world, place=place, victim=victim)

    world.para()
    inspect(world=world, place=place, battalion=battalion, method=method, helper=helper)
    prepare(world=world, battalion=battalion, method=method)

    world.para()
    if outcome == "direct":
        attempt_direct(world=world, place=place, battalion=battalion, method=method)
    else:
        attempt_assisted(world=world, place=place, battalion=battalion, method=method, helper=helper)

    world.para()
    celebrate(world=world, place=place, battalion=battalion, victim=victim)

    world.facts.update(
        place=place,
        battalion=battalion,
        method=method,
        helper=helper,
        victim_cfg=victim,
        captain=captain,
        team=team,
        victim=victim_ent,
        obstacle=tin,
        outcome=outcome,
        direct=(outcome == "direct"),
        assisted=(outcome == "assisted"),
        freed=victim_ent.meters["trapped"] < THRESHOLD,
        chant=battalion.chant,
    )
    return world


KNOWLEDGE = {
    "aspirin": [
        (
            "What is aspirin?",
            "Aspirin is a medicine people use for pain or fever. Children and animals should never take medicine on their own, because a safe grown-up must decide what is for whom."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means doing one job together instead of all alone. When everyone pushes, pulls, or plans together, the job can become much easier."
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a stiff stick or bar you press on to lift something heavy. It helps a small push do a bigger job."
        )
    ],
    "rollers": [
        (
            "Why do little pebbles help something roll?",
            "Round pebbles let a heavy thing move over them instead of dragging hard on the ground. That means less rubbing and less effort."
        )
    ],
    "push": [
        (
            "Why is pushing together better than pushing one by one?",
            "When many bodies push at the same time, their strength adds up. A heavy object can move because all the little shoves become one big shove."
        )
    ],
    "turtle": [
        (
            "Why can a turtle help with a heavy job?",
            "A turtle has a low, sturdy body and can brace strongly against the ground. That makes the turtle good at holding or nudging something heavy."
        )
    ],
    "frog": [
        (
            "Why might a frog help near mud or puddles?",
            "Frogs are good at springing and pushing with strong back legs, especially on wet ground. A quick kick at the right moment can help start something moving."
        )
    ],
}
KNOWLEDGE_ORDER = ["aspirin", "teamwork", "lever", "rollers", "push", "turtle", "frog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    battalion = f["battalion"]
    victim = f["victim_cfg"]
    place = f["place"]
    helper = f["helper"]
    prompts = [
        'Write a short animal story for a 3-to-5-year-old that includes the words "battalion", "cry", and "aspirin".',
        f"Tell a gentle story where {battalion.label} hears a cry near {place.label} and works together to rescue {victim.name}.",
        f'Write a repetitive teamwork story with a marching chant and a happy ending in which an old aspirin tin stops being scary.',
    ]
    if helper.id != "none":
        prompts.append(
            f"Include a surprise helper who arrives in the middle of the rescue and changes what the little team can do."
        )
    else:
        prompts.append(
            "Include a surprise moment after the rescue when the frightened little animal becomes brave enough to join the song."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    battalion = f["battalion"]
    place = f["place"]
    method = f["method"]
    helper = f["helper"]
    victim_cfg = f["victim_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {battalion.label}, a trapped little {victim_cfg.species} named {victim_cfg.name}, and the old aspirin tin that blocked the door. The story follows how the group answered a cry instead of hurrying past it."
        ),
        (
            "What problem did the animals find?",
            f"They heard a cry from {place.label} and discovered that an old aspirin tin had rolled against {victim_cfg.home}. That trapped {victim_cfg.name} inside and made the little one feel frightened."
        ),
        (
            "Why did the battalion chant the same words again and again?",
            f"They used the chant to keep everyone moving at the same time. The repetition turned many small bodies into one steady team."
        ),
        (
            f"How did they move the aspirin tin?",
            f"They {method.qa_text}. That method fit the ground at {place.label}, so the work made sense instead of being a wild guess."
        ),
    ]
    if outcome == "assisted":
        qa.append(
            (
                "What was the surprise in the middle of the rescue?",
                f"The first try was not enough, and then {helper.label} arrived unexpectedly to help. With that extra help, the battalion's plan finally had enough strength to move the tin."
            )
        )
    else:
        qa.append(
            (
                "What was the surprise after the rescue?",
                f"To everyone's surprise, {victim_cfg.name} was the first one to laugh and join the chant. The little animal changed from scared and hidden to brave and included."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {victim_cfg.name} marching beside the others instead of crying alone in the dark. The closing song shows that the battalion did more than move a tin: it made room for one more friend."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"aspirin", "teamwork"} | set(f["method"].tags) | set(f["helper"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pebble_path",
        battalion="mouse_battalion",
        method="lever_stick",
        helper="none",
        victim="vole",
    ),
    StoryParams(
        place="muddy_bank",
        battalion="mouse_battalion",
        method="pebble_roll",
        helper="frog",
        victim="shrew",
    ),
    StoryParams(
        place="fern_hollow",
        battalion="beetle_battalion",
        method="lever_stick",
        helper="turtle",
        victim="mole",
    ),
    StoryParams(
        place="pebble_path",
        battalion="ant_battalion",
        method="pebble_roll",
        helper="turtle",
        victim="vole",
    ),
    StoryParams(
        place="pebble_path",
        battalion="beetle_battalion",
        method="lever_stick",
        helper="none",
        victim="shrew",
    ),
]


def explain_rejection(place: Place, battalion: Battalion, method: Method, helper: Helper) -> str:
    if place.terrain not in method.usable:
        supported = ", ".join(sorted(method.usable))
        return (
            f"(No story: {method.label} does not suit the {place.terrain} ground at {place.label}. "
            f"It only makes sense on: {supported}.)"
        )
    total = battalion.strength + method.power + helper.bonus
    return (
        f"(No story: {battalion.label} using {method.label}"
        f"{'' if helper.id == 'none' else f' with {helper.label}'} reaches strength {total}, "
        f"but the aspirin tin at {place.label} needs {place.need}.)"
    )


ASP_RULES = r"""
valid(Place, Battalion, Method, Helper) :-
    place(Place), battalion(Battalion), method(Method), helper(Helper),
    terrain(Place, T), usable(Method, T),
    need(Place, N), b_strength(Battalion, B), m_power(Method, M), h_bonus(Helper, H),
    B + M + H >= N.

direct(Place, Battalion, Method) :-
    place(Place), battalion(Battalion), method(Method),
    terrain(Place, T), usable(Method, T),
    need(Place, N), b_strength(Battalion, B), m_power(Method, M),
    B + M >= N.

outcome(direct) :-
    chosen_place(P), chosen_battalion(B), chosen_method(M), chosen_helper(H),
    valid(P, B, M, H), direct(P, B, M).

outcome(assisted) :-
    chosen_place(P), chosen_battalion(B), chosen_method(M), chosen_helper(H),
    valid(P, B, M, H), not direct(P, B, M), H != none.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("terrain", place_id, place.terrain))
        lines.append(asp.fact("need", place_id, place.need))
    for battalion_id, battalion in BATTALIONS.items():
        lines.append(asp.fact("battalion", battalion_id))
        lines.append(asp.fact("b_strength", battalion_id, battalion.strength))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("m_power", method_id, method.power))
        for terrain in sorted(method.usable):
            lines.append(asp.fact("usable", method_id, terrain))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("h_bonus", helper_id, helper.bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_battalion", params.battalion),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


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
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = rescue_outcome(
            place=PLACES[params.place],
            method=METHODS[params.method],
            battalion=BATTALIONS[params.battalion],
            helper=HELPERS[params.helper],
        )
        asp_res = asp_outcome(params)
        if py != asp_res:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a battalion hears a cry and works together to move an aspirin tin."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--battalion", choices=sorted(BATTALIONS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--victim", choices=sorted(VICTIMS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.battalion and args.method and args.helper:
        place = PLACES[args.place]
        battalion = BATTALIONS[args.battalion]
        method = METHODS[args.method]
        helper = HELPERS[args.helper]
        if not works(place=place, method=method, battalion=battalion, helper=helper):
            raise StoryError(explain_rejection(place=place, battalion=battalion, method=method, helper=helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.battalion is None or combo[1] == args.battalion)
        and (args.method is None or combo[2] == args.method)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, battalion_id, method_id, helper_id = rng.choice(sorted(combos))
    victim_id = args.victim or rng.choice(sorted(VICTIMS))
    return StoryParams(
        place=place_id,
        battalion=battalion_id,
        method=method_id,
        helper=helper_id,
        victim=victim_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.battalion not in BATTALIONS:
        raise StoryError(f"(Unknown battalion: {params.battalion})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.victim not in VICTIMS:
        raise StoryError(f"(Unknown victim: {params.victim})")

    place = PLACES[params.place]
    battalion = BATTALIONS[params.battalion]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    victim = VICTIMS[params.victim]
    if not works(place=place, method=method, battalion=battalion, helper=helper):
        raise StoryError(explain_rejection(place=place, battalion=battalion, method=method, helper=helper))

    world = tell(place=place, battalion=battalion, method=method, helper=helper, victim=victim)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, battalion, method, helper) combos:\n")
        for place, battalion, method, helper in combos:
            out = rescue_outcome(
                place=PLACES[place],
                method=METHODS[method],
                battalion=BATTALIONS[battalion],
                helper=HELPERS[helper],
            )
            print(f"  {place:12} {battalion:16} {method:14} {helper:7} -> {out}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.battalion} at {p.place} "
                f"({p.method}, {p.helper}, {rescue_outcome(place=PLACES[p.place], method=METHODS[p.method], battalion=BATTALIONS[p.battalion], helper=HELPERS[p.helper])})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
