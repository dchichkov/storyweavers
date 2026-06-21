#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py
=======================================================================

A standalone storyworld for a gentle ghost-story domain at a pier.

Premise
-------
At dusk on a pier, a child sees what looks like a ghost near an old incinerator.
The world model decides whether the shape is plausibly ghost-like, what eerie
sound the incinerator adds, how fear rises, how a calm grown-up investigates,
and how the scare is resolved by a concrete fix: fastening the loose object with
a velcro strap. Some piers also carry a tiny final whisper of mystery -- a last
friendly sign that feels just a little bit like a real ghost story.

Run it
------
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --apparition sailcloth
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --response rock_throw
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/velcro_incinerator_pier_twist_ghost_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    pale: bool = False
    loose: bool = False
    warm: bool = False
    lit: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "keeper": "keeper",
            "aunt": "aunt",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
class Pier:
    id: str
    label: str
    opening: str
    detail: str
    spirit: bool = False
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
class Apparition:
    id: str
    label: str
    phrase: str
    mount: str
    flutter: str
    reveal: str
    material: str
    pale: bool = True
    loose: bool = True
    ghostly: int = 2
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
class Incinerator:
    id: str
    label: str
    phrase: str
    sound: str
    draft: int
    glow: str
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
class Helper:
    id: str
    type: str
    label: str
    entrance: str
    comfort: str
    history: str
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
    beam: str
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
class Response:
    id: str
    sense: int
    approach: str
    fix: str
    qa_fix: str
    kind: bool = True
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
    pier: str
    apparition: str
    incinerator: str
    helper: str
    light: str
    response: str
    child_name: str
    child_gender: str
    child_trait: str
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
    def __init__(self, pier_cfg: Pier) -> None:
        self.pier_cfg = pier_cfg
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
        clone = World(self.pier_cfg)
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


def _r_spooky_shape(world: World) -> list[str]:
    out: list[str] = []
    shape = world.get("shape")
    burner = world.get("incinerator")
    if not (shape.loose and shape.pale):
        return out
    if burner.meters["draft"] < THRESHOLD:
        return out
    sig = ("spooky_shape", shape.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shape.meters["spooky"] += 1
    world.get("pier").meters["eerie"] += 1
    out.append("__shape__")
    return out


def _r_child_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shape = world.get("shape")
    if shape.meters["spooky"] < THRESHOLD or child.attrs.get("saw_shape") != 1:
        return out
    sig = ("fear", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["imagination"] += 1
    out.append("__fear__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    light = world.get("light")
    shape = world.get("shape")
    if child.attrs.get("approached") != 1 or helper.attrs.get("present") != 1:
        return out
    if not light.lit:
        return out
    sig = ("reveal", shape.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shape.meters["revealed"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["courage"] += 1
    out.append("__reveal__")
    return out


def _r_fastened(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shape = world.get("shape")
    if child.attrs.get("fastened") != 1:
        return out
    sig = ("fastened", shape.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shape.loose = False
    shape.meters["spooky"] = 0.0
    world.get("pier").meters["eerie"] = 0.0
    child.memes["pride"] += 1
    out.append("__fixed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spooky_shape", tag="physical", apply=_r_spooky_shape),
    Rule(name="child_fear", tag="emotional", apply=_r_child_fear),
    Rule(name="reveal", tag="social", apply=_r_reveal),
    Rule(name="fastened", tag="physical", apply=_r_fastened),
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


PIERS = {
    "lantern_pier": Pier(
        id="lantern_pier",
        label="the lantern pier",
        opening="At the end of the lantern pier, the boards were silver with mist.",
        detail="Old pilings knocked softly below, and the rope rails smelled of salt.",
        spirit=True,
        tags={"pier", "fog", "ghost"},
    ),
    "crab_pier": Pier(
        id="crab_pier",
        label="the crab pier",
        opening="Along the crab pier, gulls had gone quiet and the evening tide was turning black-blue.",
        detail="Lobster pots sat in neat stacks, and water tapped the posts under the planks.",
        spirit=False,
        tags={"pier", "fog"},
    ),
    "ferry_pier": Pier(
        id="ferry_pier",
        label="the ferry pier",
        opening="On the old ferry pier, the fog came in thin white ribbons.",
        detail="A bell rope swayed by the shed, and the water beyond it looked deep and sleepy.",
        spirit=True,
        tags={"pier", "fog", "ghost"},
    ),
}

APPARITIONS = {
    "rain_cape": Apparition(
        id="rain_cape",
        label="rain cape",
        phrase="a white rain cape",
        mount="a fish cart",
        flutter="lifted and folded in the wind like shoulders and arms",
        reveal="it was only a white rain cape left on a fish cart",
        material="slick cloth",
        pale=True,
        loose=True,
        ghostly=3,
        tags={"cloth", "ghost"},
    ),
    "sailcloth": Apparition(
        id="sailcloth",
        label="sailcloth",
        phrase="a torn square of sailcloth",
        mount="a piling hook",
        flutter="twisted and bowed as if a tall person were turning to look",
        reveal="it was only a torn square of sailcloth snagged on a piling hook",
        material="canvas",
        pale=True,
        loose=True,
        ghostly=3,
        tags={"cloth", "ghost"},
    ),
    "gull_net": Apparition(
        id="gull_net",
        label="gull net",
        phrase="a pale gull net",
        mount="a bait crate",
        flutter="billowed and shrank like a breathing chest",
        reveal="it was only a pale gull net caught on a bait crate",
        material="netting",
        pale=True,
        loose=True,
        ghostly=2,
        tags={"net", "ghost"},
    ),
    "red_flag": Apparition(
        id="red_flag",
        label="red warning flag",
        phrase="a red warning flag",
        mount="a mooring post",
        flutter="snapped sharply in the wind",
        reveal="it was only a red warning flag on a mooring post",
        material="canvas",
        pale=False,
        loose=True,
        ghostly=0,
        tags={"flag"},
    ),
}

INCINERATORS = {
    "ash_drum": Incinerator(
        id="ash_drum",
        label="ash drum incinerator",
        phrase="an old ash-drum incinerator by the bait shed",
        sound="its little iron door clicked and sighed",
        draft=1,
        glow="a sleepy red blink shone through the vent holes",
        tags={"incinerator", "fire"},
    ),
    "brick_box": Incinerator(
        id="brick_box",
        label="brick incinerator",
        phrase="the squat brick incinerator by the rail",
        sound="its chimney gave a hollow moan each time the wind crossed it",
        draft=2,
        glow="orange heat breathed behind the grate",
        tags={"incinerator", "fire"},
    ),
    "cold_bin": Incinerator(
        id="cold_bin",
        label="cold scrap incinerator",
        phrase="a cold scrap incinerator with a bent lid",
        sound="its loose lid rattled now and then",
        draft=0,
        glow="no glow showed from it at all",
        tags={"incinerator"},
    ),
}

HELPERS = {
    "keeper": Helper(
        id="keeper",
        type="keeper",
        label="the pier keeper",
        entrance="The keeper came out of the shed with steady steps.",
        comfort='"Ghosts do not need old fish carts," he said in a calm voice.',
        history="He had watched that pier through many foggy evenings and knew all its ordinary sounds.",
        tags={"adult", "pier"},
    ),
    "grandpa": Helper(
        id="grandpa",
        type="grandfather",
        label="grandpa",
        entrance="Grandpa looked up from the crab buckets and came over at once.",
        comfort='"Let us look slowly before we leap to a fright," he said softly.',
        history="He had worked on the pier for years and trusted lantern light more than spooky guesses.",
        tags={"adult", "pier"},
    ),
    "aunt": Helper(
        id="aunt",
        type="aunt",
        label="aunt Bea",
        entrance="Aunt Bea pushed the shed door open and hurried over.",
        comfort='"A mystery gets smaller when we walk toward it together," she said.',
        history="She knew the pier's ropes, hooks, and shadows so well that almost nothing fooled her for long.",
        tags={"adult", "pier"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a glass lantern",
        beam="made a round pool of gold on the boards",
        tags={"light", "lantern"},
    ),
    "torch": Light(
        id="torch",
        label="torch",
        phrase="a pocket torch",
        beam="cut a thin white path through the fog",
        tags={"light", "flashlight"},
    ),
    "headlamp": Light(
        id="headlamp",
        label="head-lamp",
        phrase="a head-lamp",
        beam="sent a small bright beam wherever they looked",
        tags={"light", "flashlight"},
    ),
}

RESPONSES = {
    "walk_and_check": Response(
        id="walk_and_check",
        sense=3,
        approach="took the child's hand and walked closer with the light held low",
        fix="used the velcro strap from the child's tackle satchel to bind the loose cloth tight",
        qa_fix="used the velcro strap from the tackle satchel to fasten the loose cloth so it could not flap anymore",
        kind=True,
        tags={"velcro", "light"},
    ),
    "speak_then_check": Response(
        id="speak_then_check",
        sense=2,
        approach="stood still for one breath, listened, and then stepped closer with the light",
        fix="wrapped the velcro strap around the loose cloth and its hook until the shape stayed still",
        qa_fix="wrapped the velcro strap around the loose cloth and its hook until it stayed still",
        kind=True,
        tags={"velcro", "light"},
    ),
    "rock_throw": Response(
        id="rock_throw",
        sense=1,
        approach="grabbed a pebble and threw it at the shape from far away",
        fix="did nothing sensible at all",
        qa_fix="threw a pebble from far away",
        kind=False,
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nell", "Ivy", "Tess", "Willa", "June", "Cora"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Eli", "Ned", "Sam", "Finn"]
TRAITS = ["brave", "curious", "quiet", "careful", "dreamy", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pier_id in PIERS:
        for app_id, app in APPARITIONS.items():
            for inc_id, inc in INCINERATORS.items():
                if app.pale and app.loose and inc.draft >= 1 and app.ghostly >= 2:
                    combos.append((pier_id, app_id, inc_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def explain_apparition_rejection(apparition: Apparition, incinerator: Incinerator) -> str:
    if not apparition.pale:
        return (
            f"(No story: {apparition.phrase} is not pale enough to read as a ghost in fog, "
            f"so the child has no honest spooky mistake to make.)"
        )
    if not apparition.loose:
        return (
            f"(No story: {apparition.phrase} is fixed in place, so it cannot flap into a ghostly shape.)"
        )
    if apparition.ghostly < 2:
        return (
            f"(No story: {apparition.phrase} does not make a strong enough ghostly silhouette for this domain.)"
        )
    if incinerator.draft < 1:
        return (
            f"(No story: {incinerator.phrase} gives no warm draft, so nothing near it billows into a ghost-shape.)"
        )
    return "(No story: that apparition and incinerator do not make a plausible scare.)"


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is not a calm, child-sensible way to handle a spooky shape "
        f"(sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def gentle_outcome(params: StoryParams) -> str:
    pier = PIERS[params.pier]
    response = RESPONSES[params.response]
    return "wink" if pier.spirit and response.kind else "revealed"


def predict_spook(world: World) -> dict:
    sim = world.copy()
    sim.get("child").attrs["saw_shape"] = 1
    propagate(sim, narrate=False)
    shape = sim.get("shape")
    child = sim.get("child")
    return {
        "spooky": shape.meters["spooky"] >= THRESHOLD,
        "fear": child.memes["fear"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, pier_cfg: Pier) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} walked beside {helper.label_word} on {pier_cfg.label} as evening pulled the light thin. "
        f"{pier_cfg.opening}"
    )
    world.say(pier_cfg.detail)
    world.say(
        f"{child.pronoun('possessive').capitalize()} little tackle satchel bumped against {child.pronoun('possessive')} side, "
        f"its velcro flap making tiny ripping sounds each time it brushed {child.pronoun('possessive')} coat."
    )


def seed_spook(world: World, child: Entity, app: Apparition, inc: Incinerator) -> None:
    world.get("incinerator").warm = True
    world.get("incinerator").meters["draft"] = float(inc.draft)
    child.attrs["saw_shape"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Near {inc.phrase}, {app.phrase} on {app.mount} {app.flutter}. "
        f"At the same time, {inc.sound}, and {inc.glow}."
    )
    pred = predict_spook(world)
    world.facts["predicted_spooky"] = pred["spooky"]
    world.facts["predicted_fear"] = pred["fear"]
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped so fast that the boards squeaked. "
            f'"There," {child.pronoun()} whispered. "A ghost on the pier."'
        )


def comfort(world: World, helper: Entity) -> None:
    world.say(HELPERS[helper.attrs["cfg_id"]].entrance)
    world.say(HELPERS[helper.attrs["cfg_id"]].comfort)
    world.say(HELPERS[helper.attrs["cfg_id"]].history)
    helper.attrs["present"] = 1


def investigate(world: World, child: Entity, helper: Entity, light_ent: Entity,
                light_cfg: Light, response: Response) -> None:
    light_ent.lit = True
    child.attrs["approached"] = 1
    world.say(
        f"{helper.label_word.capitalize()} {response.approach}. "
        f"The {light_cfg.label} {light_cfg.beam}."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, app: Apparition) -> None:
    shape = world.get("shape")
    if shape.meters["revealed"] >= THRESHOLD:
        world.say(
            f"Then the scary person-shape broke apart in the light. {app.reveal}, "
            f"all wet edges and ordinary {app.material}."
        )
        world.say(
            f"{child.id} let out the breath {child.pronoun()} had been keeping trapped in {child.pronoun('possessive')} chest."
        )


def fasten(world: World, child: Entity, response: Response, app: Apparition) -> None:
    child.attrs["fastened"] = 1
    world.say(
        f'"It was only lonely cloth," {child.id} said. Then {child.pronoun()} {response.fix}.'
    )
    propagate(world, narrate=False)
    world.say(
        f"At once, the {app.label} stopped jumping and sagged back into being just a thing on the pier."
    )


def ending_revealed(world: World, child: Entity, helper: Entity, pier_cfg: Pier, light_cfg: Light) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"They walked back along the boards more slowly, listening again. Now the pier only sounded like water, rope, "
        f"and the soft clink of the old {world.get('incinerator').label}."
    )
    world.say(
        f"{child.id} opened and closed the satchel flap once -- rrip, rrip -- and smiled. "
        f"The next time fog came to {pier_cfg.label}, {child.pronoun()} still remembered the scare, "
        f"but {child.pronoun()} also remembered what the {light_cfg.label} had shown."
    )


def ending_wink(world: World, child: Entity, helper: Entity, pier_cfg: Pier) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"They turned to go, and the pier grew quiet enough for little sounds again: water under planks, a far bell, "
        f"and the hush of fog slipping past the rails."
    )
    world.say(
        f"Then, just once, a small lantern far down the empty pier gave one bright wink and went dark, though no one stood there at all."
    )
    world.say(
        f"{child.id} looked up at {helper.label_word}. {helper.pronoun().capitalize()} only smiled. "
        f'"Maybe this pier likes being tidied," {helper.pronoun()} said. {child.id} held the satchel with its velcro strap close and smiled back.'
    )


def tell(pier_cfg: Pier, app: Apparition, inc: Incinerator, helper_cfg: Helper,
         light_cfg: Light, response: Response, child_name: str, child_gender: str,
         child_trait: str) -> World:
    world = World(pier_cfg)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        traits=[child_trait],
        role="child",
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"cfg_id": helper_cfg.id, "present": 0},
    ))
    light_ent = world.add(Entity(
        id="light",
        kind="thing",
        type="light",
        label=light_cfg.label,
        attrs={},
    ))
    world.add(Entity(
        id="pier",
        kind="thing",
        type="pier",
        label=pier_cfg.label,
        attrs={},
    ))
    world.add(Entity(
        id="incinerator",
        kind="thing",
        type="incinerator",
        label=inc.label,
        warm=False,
        attrs={},
    ))
    world.add(Entity(
        id="shape",
        kind="thing",
        type="cloth",
        label=app.label,
        pale=app.pale,
        loose=app.loose,
        attrs={},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        pier_cfg=pier_cfg,
        apparition=app,
        incinerator=inc,
        light_cfg=light_cfg,
        response=response,
        child_name=child_name,
    )

    opening(world, child, helper, pier_cfg)
    world.para()
    seed_spook(world, child, app, inc)
    comfort(world, helper)
    world.para()
    investigate(world, child, helper, light_ent, light_cfg, response)
    reveal(world, child, app)
    fasten(world, child, response, app)
    world.para()

    outcome = "wink" if pier_cfg.spirit and response.kind else "revealed"
    if outcome == "wink":
        ending_wink(world, child, helper, pier_cfg)
    else:
        ending_revealed(world, child, helper, pier_cfg, light_cfg)

    world.facts.update(
        outcome=outcome,
        fear_happened=child.memes["relief"] >= THRESHOLD,
        fixed=child.attrs.get("fastened") == 1,
        revealed=world.get("shape").meters["revealed"] >= THRESHOLD,
        spooky_before=world.facts.get("predicted_spooky", False),
        spirit=pier_cfg.spirit,
    )
    return world


KNOWLEDGE = {
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. Boats can tie up beside it, and people can walk along it.",
        )
    ],
    "fog": [
        (
            "Why does fog make things look spooky?",
            "Fog hides parts of things and blurs their edges. Your eyes can mistake an ordinary object for something strange when you cannot see it clearly.",
        )
    ],
    "incinerator": [
        (
            "What is an incinerator?",
            "An incinerator is a metal or brick burner used to burn trash or scraps. When it is warm, air can move through it and make sounds.",
        )
    ],
    "velcro": [
        (
            "What is velcro?",
            "Velcro is a fastener with two sides that grip each other when you press them together. It is handy because you can pull it open and press it shut again quickly.",
        )
    ],
    "light": [
        (
            "Why does a lantern or torch help with a spooky mistake?",
            "A steady light shows shape, size, and color more clearly. When you can really see an object, your mind has less room to turn it into a monster or a ghost.",
        )
    ],
    "ghost": [
        (
            "Are all ghost stories about dangerous ghosts?",
            "No. Some ghost stories are really about mystery, surprise, and brave looking. A spooky feeling can end in a safe explanation, or in a tiny gentle mystery.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pier", "fog", "incinerator", "velcro", "light", "ghost"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    app = f["apparition"]
    inc = f["incinerator"]
    pier_cfg = f["pier_cfg"]
    outcome = f["outcome"]
    if outcome == "wink":
        return [
            f'Write a gentle ghost story for a young child set on a pier, using the words "velcro" and "incinerator".',
            f"Tell a story where {child.label} sees {app.phrase} near {inc.phrase}, mistakes it for a ghost, and solves the scare with a velcro strap -- but end with one tiny friendly supernatural wink.",
            f"Write a foggy pier story with a twist: the ghost is first explained, and then the ending leaves just a little room for wonder.",
        ]
    return [
        f'Write a gentle ghost story for a young child set on a pier, using the words "velcro" and "incinerator".',
        f"Tell a story where {child.label} sees {app.phrase} by {inc.phrase}, feels afraid, and learns to walk closer with light before deciding what is there.",
        f"Write a spooky-but-safe story with a twist where a ghost on the pier turns out to be an ordinary object and the child helps fix it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    app = f["apparition"]
    inc = f["incinerator"]
    light_cfg = f["light_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child on a foggy pier, and {helper.label_word} who helps with the scare. The story follows how they turn a spooky mistake into something understandable.",
        ),
        (
            "Why did the shape look like a ghost at first?",
            f"{app.phrase.capitalize()} was loose, pale, and moving in the warm draft near the incinerator, so it looked like a person in the fog. The eerie sound from the incinerator made the mistake feel even more real.",
        ),
        (
            f"What did {helper.label_word} do when {child.label} got scared?",
            f"{helper.label_word.capitalize()} did not laugh and did not run away. {helper.pronoun().capitalize()} brought {light_cfg.phrase} and walked closer calmly, because clear light can show what a fear is really made of.",
        ),
        (
            "How did they stop the scare from happening again?",
            f"They {response.qa_fix}. That mattered because once the cloth stopped flapping, it could not pretend to be a ghost anymore.",
        ),
    ]
    if outcome == "wink":
        qa.append(
            (
                "What was the twist at the end?",
                f"First, the ghost turned out to be only {app.label}. Then a tiny lantern wink appeared on the empty pier, which left one gentle mystery behind. The story becomes safe and spooky at the same time.",
            )
        )
    else:
        qa.append(
            (
                "What changed by the end of the story?",
                f"{child.label} was no longer trapped by the first scary guess. After seeing the shape clearly and fixing it, {child.pronoun()} could hear the pier as a normal place again instead of a haunted one.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pier", "fog", "incinerator", "velcro", "light", "ghost"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("pale", ent.pale),
            ("loose", ent.loose),
            ("warm", ent.warm),
            ("lit", ent.lit),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        pier="lantern_pier",
        apparition="rain_cape",
        incinerator="brick_box",
        helper="keeper",
        light="lantern",
        response="walk_and_check",
        child_name="Lina",
        child_gender="girl",
        child_trait="curious",
    ),
    StoryParams(
        pier="crab_pier",
        apparition="gull_net",
        incinerator="ash_drum",
        helper="grandpa",
        light="torch",
        response="speak_then_check",
        child_name="Milo",
        child_gender="boy",
        child_trait="thoughtful",
    ),
    StoryParams(
        pier="ferry_pier",
        apparition="sailcloth",
        incinerator="brick_box",
        helper="aunt",
        light="headlamp",
        response="walk_and_check",
        child_name="June",
        child_gender="girl",
        child_trait="dreamy",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
ghostly(A, I) :- apparition(A), incinerator(I), pale(A), loose(A), draft(I, D), D >= 1, ghost_score(A, G), G >= 2.
sensible(R)   :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, A, I) :- pier(P), ghostly(A, I).

% --- outcome model ---------------------------------------------------------
outcome(wink) :- chosen_pier(P), spirit(P), chosen_response(R), kind(R).
outcome(revealed) :- not outcome(wink).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pier_id, pier in PIERS.items():
        lines.append(asp.fact("pier", pier_id))
        if pier.spirit:
            lines.append(asp.fact("spirit", pier_id))
    for app_id, app in APPARITIONS.items():
        lines.append(asp.fact("apparition", app_id))
        if app.pale:
            lines.append(asp.fact("pale", app_id))
        if app.loose:
            lines.append(asp.fact("loose", app_id))
        lines.append(asp.fact("ghost_score", app_id, app.ghostly))
    for inc_id, inc in INCINERATORS.items():
        lines.append(asp.fact("incinerator", inc_id))
        lines.append(asp.fact("draft", inc_id, inc.draft))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.kind:
            lines.append(asp.fact("kind", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_pier", params.pier),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a child, a pier, a false ghost, and a twist."
    )
    ap.add_argument("--pier", choices=PIERS)
    ap.add_argument("--apparition", choices=APPARITIONS)
    ap.add_argument("--incinerator", choices=INCINERATORS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))
    if args.apparition and args.incinerator:
        apparition = APPARITIONS[args.apparition]
        incinerator = INCINERATORS[args.incinerator]
        if (args.pier, args.apparition, args.incinerator) not in valid_combos() and not (
            apparition.pale and apparition.loose and apparition.ghostly >= 2 and incinerator.draft >= 1
        ):
            raise StoryError(explain_apparition_rejection(apparition, incinerator))
        if not (apparition.pale and apparition.loose and apparition.ghostly >= 2 and incinerator.draft >= 1):
            raise StoryError(explain_apparition_rejection(apparition, incinerator))
    if args.apparition and args.incinerator is None:
        apparition = APPARITIONS[args.apparition]
        if not (apparition.pale and apparition.loose and apparition.ghostly >= 2):
            chosen_inc = next(iter(INCINERATORS.values()))
            raise StoryError(explain_apparition_rejection(apparition, chosen_inc))
    if args.incinerator and args.apparition is None:
        incinerator = INCINERATORS[args.incinerator]
        if incinerator.draft < 1:
            chosen_app = next(iter(APPARITIONS.values()))
            raise StoryError(explain_apparition_rejection(chosen_app, incinerator))

    combos = [
        combo for combo in valid_combos()
        if (args.pier is None or combo[0] == args.pier)
        and (args.apparition is None or combo[1] == args.apparition)
        and (args.incinerator is None or combo[2] == args.incinerator)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pier_id, apparition_id, incinerator_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS.keys()))
    light_id = args.light or rng.choice(sorted(LIGHTS.keys()))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        pier=pier_id,
        apparition=apparition_id,
        incinerator=incinerator_id,
        helper=helper_id,
        light=light_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pier not in PIERS:
        raise StoryError(f"(Unknown pier: {params.pier})")
    if params.apparition not in APPARITIONS:
        raise StoryError(f"(Unknown apparition: {params.apparition})")
    if params.incinerator not in INCINERATORS:
        raise StoryError(f"(Unknown incinerator: {params.incinerator})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    apparition = APPARITIONS[params.apparition]
    incinerator = INCINERATORS[params.incinerator]
    response = RESPONSES[params.response]
    if not (apparition.pale and apparition.loose and apparition.ghostly >= 2 and incinerator.draft >= 1):
        raise StoryError(explain_apparition_rejection(apparition, incinerator))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        pier_cfg=PIERS[params.pier],
        app=apparition,
        inc=incinerator,
        helper_cfg=HELPERS[params.helper],
        light_cfg=LIGHTS[params.light],
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    text = sample.story.replace(" child ", f" {sample.params.child_name} ")
    if header:
        print(header)
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if py_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(clingo_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != gentle_outcome(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(777))
        smoke_params.seed = 777
        sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pier, apparition, incinerator) combos:\n")
        for pier_id, apparition_id, incinerator_id in combos:
            print(f"  {pier_id:13} {apparition_id:12} {incinerator_id}")
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
            header = f"### {p.child_name}: {p.apparition} by {p.incinerator} at {p.pier} ({gentle_outcome(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
