#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py
============================================================================

A standalone story world for a child-scale mystery: a strange "ouch-dim" sound
comes from a dark hiding place, two children wonder what it could be, one is
tempted to solve it the unsafe way, and a calm grown-up helps them investigate
properly. The mystery turns out to have an ordinary cause, everyone is safe, and
the ending proves the lesson: dark surprises should be checked with light and
help, not with blind reaching or risky climbing.

Run it
------
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py --setting attic --place high_shelf --source robot
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py --place under_bench --response stool
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ouch_dim_lesson_learned_happy_ending_mystery.py --verify
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
BOLD_INIT = 6.0
CAREFUL_TRAITS = {"careful", "cautious", "patient", "thoughtful"}


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
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Setting:
    id: str
    place: str
    lead_in: str
    mood: str
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
class HidingPlace:
    id: str
    label: str
    the: str
    scene: str
    need: str
    risk: str
    sounds: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    phrase: str
    kind: str
    sound: str
    reveal: str
    truth: str
    allowed_places: set[str]
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
    handles: set[str]
    text: str
    qa_text: str
    lesson: str
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
        return [e for e in self.entities.values() if e.role in {"solver", "buddy"}]

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


def _r_dark_noise(world: World) -> list[str]:
    place = world.get("place")
    source = world.get("source")
    if place.meters["dark"] < THRESHOLD or source.meters["hidden"] < THRESHOLD or source.meters["making_noise"] < THRESHOLD:
        return []
    sig = ("dark_noise", place.id, source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["unease"] += 1
        kid.memes["curiosity"] += 1
    return ["__mystery__"]


def _r_climb_wobble(world: World) -> list[str]:
    solver = world.get("solver")
    place = world.get("place")
    if solver.meters["climbing"] < THRESHOLD or place.attrs.get("need") != "stool":
        return []
    sig = ("climb_wobble", solver.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    solver.meters["wobble"] += 1
    solver.meters["minor_ouch"] += 1
    solver.memes["alarm"] += 1
    world.get("buddy").memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    return ["__wobble__"]


def _r_blind_bump(world: World) -> list[str]:
    solver = world.get("solver")
    place = world.get("place")
    if solver.meters["blind_reaching"] < THRESHOLD or place.attrs.get("need") not in {"hook", "open"}:
        return []
    sig = ("blind_bump", solver.id, place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    solver.meters["minor_ouch"] += 1
    solver.memes["alarm"] += 1
    world.get("buddy").memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    return ["__bump__"]


CAUSAL_RULES = [
    Rule(name="dark_noise", tag="mystery", apply=_r_dark_noise),
    Rule(name="climb_wobble", tag="risk", apply=_r_climb_wobble),
    Rule(name="blind_bump", tag="risk", apply=_r_blind_bump),
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


def source_fits(place: HidingPlace, source: Source) -> bool:
    return place.id in source.allowed_places


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(place: HidingPlace, response: Response) -> bool:
    return place.need in response.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for place_id, place in HIDING_PLACES.items():
            for source_id, source in SOURCES.items():
                if not source_fits(place, source):
                    continue
                combos.append((setting_id, place_id, source_id))
    return combos


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_wait(relation: str, solver_age: int, buddy_age: int, trait: str) -> bool:
    buddy_older = relation == "siblings" and buddy_age > solver_age
    authority = initial_care(trait) + 1.0 + (3.0 if buddy_older else 0.0)
    return buddy_older and authority > BOLD_INIT


def predict_ouch(world: World, place_need: str) -> dict:
    sim = world.copy()
    solver = sim.get("solver")
    if place_need == "stool":
        solver.meters["climbing"] += 1
    else:
        solver.meters["blind_reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "minor_ouch": solver.meters["minor_ouch"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def open_mystery(world: World, solver: Entity, buddy: Entity, setting: Setting, place: HidingPlace) -> None:
    for kid in (solver, buddy):
        kid.memes["joy"] += 1
    world.say(
        f"{setting.lead_in}, {solver.id} and {buddy.id} were pretending to be tiny detectives. "
        f"{setting.mood} by {place.scene}."
    )
    world.say(
        f"Then they both heard it from {place.the}: a strange little sound that seemed to say, "
        f'"ouch-dim... ouch-dim."'
    )
    world.get("place").meters["dark"] = 1.0
    world.get("source").meters["hidden"] = 1.0
    world.get("source").meters["making_noise"] = 1.0
    propagate(world, narrate=False)


def wonder(world: World, solver: Entity, buddy: Entity, place: HidingPlace) -> None:
    world.say(
        f'{buddy.id} squeezed closer. "What do you think is in {place.the}?"'
    )
    world.say(
        f'{solver.id} looked hard into the shadows. "I do not know," {solver.pronoun()} whispered, '
        f'"but it sounds like a mystery."'
    )


def tempt(world: World, solver: Entity, place: HidingPlace) -> None:
    solver.memes["boldness"] += 1
    if place.need == "stool":
        plan = "climb up and grab it"
    elif place.need == "hook":
        plan = "reach in without looking"
    else:
        plan = "flip it open fast"
    world.say(
        f'The sound came again, soft and odd. "{place.sounds}," said {solver.id}. '
        f'"I can {plan} all by myself."'
    )


def warn(world: World, solver: Entity, buddy: Entity, place: HidingPlace, adult: Entity) -> None:
    pred = predict_ouch(world, place.need)
    world.facts["predicted_danger"] = pred["danger"]
    buddy.memes["care"] += 1
    extra = " and get a little hurt" if pred["minor_ouch"] else ""
    world.say(
        f'{buddy.id} shook {buddy.pronoun("possessive")} head. "Please do not. '
        f'{place.risk.capitalize()}{extra}. Let us tell {adult.label_word} and bring a light first."'
    )


def back_down(world: World, solver: Entity, buddy: Entity, adult: Entity) -> None:
    solver.memes["relief"] += 1
    buddy.memes["relief"] += 1
    world.say(
        f'{solver.id} took one step forward, then stopped. The mystery still tugged at {solver.pronoun("object")}, '
        f'but {buddy.id} sounded so certain that {solver.pronoun()} nodded.'
    )
    world.say(
        f'Together they hurried to find {adult.label_word}, carrying the mystery with them like a small secret in their pockets.'
    )


def unsafe_try(world: World, solver: Entity, buddy: Entity, place: HidingPlace) -> None:
    solver.memes["defiance"] += 1
    world.say(
        f'"Just one quick peek," {solver.id} said.'
    )
    if place.need == "stool":
        solver.meters["climbing"] += 1
        propagate(world, narrate=False)
        if solver.meters["wobble"] >= THRESHOLD:
            world.say(
                f'{solver.id} put one foot on a low crate and reached up. The crate gave a tiny skid, and {solver.pronoun()} hopped back with a startled gasp.'
            )
    else:
        solver.meters["blind_reaching"] += 1
        propagate(world, narrate=False)
        if solver.meters["minor_ouch"] >= THRESHOLD:
            world.say(
                f'{solver.id} pushed a hand toward the dark without seeing clearly. At once {solver.pronoun()} bumped {solver.pronoun("possessive")} fingers and snatched them back.'
            )
    world.say(
        f'{buddy.id} grabbed {solver.id}\'s sleeve. "That is enough. We really need help."'
    )


def call_adult(world: World, adult: Entity) -> None:
    world.say(f'"{adult.label_word.capitalize()}!" the children called together.')


def adult_arrives(world: World, adult: Entity, light: Light) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came over at once and listened to the odd sound. "
        f"{adult.pronoun().capitalize()} brought {light.phrase} that {light.glow}."
    )


def investigate(world: World, adult: Entity, response: Response, source: Source, place: HidingPlace, light: Light) -> None:
    world.get("source").meters["found"] = 1.0
    world.get("source").meters["hidden"] = 0.0
    world.get("source").meters["making_noise"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    world.get("room").meters["danger"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"In the beam of the {light.label}, the shadows stopped being spooky and turned back into ordinary corners."
    )
    world.say(
        f"{adult.label_word.capitalize()} {response.text.format(place=place.label)}. "
        f"Inside was {source.phrase}."
    )
    world.say(source.reveal)


def explain_truth(world: World, adult: Entity, source: Source) -> None:
    world.say(
        f'"So that was the mystery," said {adult.label_word}. "{source.truth}"'
    )


def lesson(world: World, adult: Entity, solver: Entity, buddy: Entity, response: Response) -> None:
    for kid in (solver, buddy):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{adult.label_word.capitalize()} knelt beside them and smiled. "
        f'"Dark sounds can feel bigger than they really are," {adult.pronoun()} said, '
        f'"but {response.lesson}"'
    )
    world.say(
        f'"We learned it," {buddy.id} said. "{solver.id} and I will use light and ask for help."'
    )


def bright_ending(world: World, solver: Entity, buddy: Entity, source: Source, light: Light) -> None:
    for kid in (solver, buddy):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if source.kind == "pet":
        ending = f"{source.label} curled against them as if nothing mysterious had happened at all."
    else:
        ending = f"{source.label} sat between them, sounding much less spooky in the light."
    world.say(
        f"A little later, the mystery did not feel scary anymore. {solver.id} and {buddy.id} sat together under the warm glow of the {light.label}, and {ending}"
    )
    world.say(
        "What had been a dark puzzle was now a solved one, and the room felt cozy again."
    )


def tell(
    setting: Setting,
    place_cfg: HidingPlace,
    source_cfg: Source,
    response_cfg: Response,
    light_cfg: Light,
    solver_name: str = "Nora",
    solver_gender: str = "girl",
    buddy_name: str = "Leo",
    buddy_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    solver_age: int = 5,
    buddy_age: int = 7,
) -> World:
    world = World()
    solver = world.add(Entity(
        id=solver_name,
        kind="character",
        type=solver_gender,
        role="solver",
        traits=["curious"],
        age=solver_age,
        attrs={"relation": relation},
    ))
    buddy = world.add(Entity(
        id=buddy_name,
        kind="character",
        type=buddy_gender,
        role="buddy",
        traits=[trait],
        age=buddy_age,
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=parent_type,
        role="adult",
        label="the grown-up",
    ))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    place = world.add(Entity(
        id="place",
        type="place",
        label=place_cfg.label,
        attrs={"need": place_cfg.need},
        tags=set(place_cfg.tags),
    ))
    source = world.add(Entity(
        id="source",
        type=source_cfg.kind,
        label=source_cfg.label,
        tags=set(source_cfg.tags),
    ))
    light = world.add(Entity(
        id="light",
        type="light",
        label=light_cfg.label,
        tags=set(light_cfg.tags),
    ))

    for ent in (solver, buddy, adult, room, place, source, light):
        ent.meters["dummy_init"] += 0.0
        ent.memes["dummy_init"] += 0.0
    solver.memes["boldness"] = BOLD_INIT
    buddy.memes["care"] = initial_care(trait)
    room.meters["mystery"] = 0.0
    room.meters["danger"] = 0.0
    place.meters["dark"] = 0.0
    source.meters["hidden"] = 0.0
    source.meters["making_noise"] = 0.0
    source.meters["found"] = 0.0
    solver.meters["climbing"] = 0.0
    solver.meters["blind_reaching"] = 0.0
    solver.meters["wobble"] = 0.0
    solver.meters["minor_ouch"] = 0.0
    buddy.memes["fear"] = 0.0

    open_mystery(world, solver, buddy, setting, place_cfg)
    wonder(world, solver, buddy, place_cfg)

    world.para()
    tempt(world, solver, place_cfg)
    warn(world, solver, buddy, place_cfg, adult)

    waited = would_wait(relation, solver_age, buddy_age, trait)
    if waited:
        back_down(world, solver, buddy, adult)
    else:
        unsafe_try(world, solver, buddy, place_cfg)

    world.para()
    call_adult(world, adult)
    adult_arrives(world, adult, light_cfg)
    investigate(world, adult, response_cfg, source_cfg, place_cfg, light_cfg)
    explain_truth(world, adult, source_cfg)

    world.para()
    lesson(world, adult, solver, buddy, response_cfg)
    bright_ending(world, solver, buddy, source_cfg, light_cfg)

    world.facts.update(
        setting=setting,
        place_cfg=place_cfg,
        source_cfg=source_cfg,
        response=response_cfg,
        light_cfg=light_cfg,
        solver=solver,
        buddy=buddy,
        adult=adult,
        place=place,
        source=source,
        light=light,
        relation=relation,
        waited=waited,
        had_ouch=solver.meters["minor_ouch"] >= THRESHOLD,
        learned=solver.memes["lesson"] >= THRESHOLD,
        solved=source.meters["found"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic landing",
        lead_in="On a drizzly afternoon",
        mood="The boards gave tiny creaks, and the air smelled like old paper",
        tags={"mystery", "dark"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the long hallway",
        lead_in="One quiet evening",
        mood="The house was hushed, and the corners looked extra deep after sunset",
        tags={"mystery", "dark"},
    ),
    "shed": Setting(
        id="shed",
        place="the garden shed doorway",
        lead_in="After supper",
        mood="The little shed held rakes, flower pots, and pockets of shadow",
        tags={"mystery", "garden"},
    ),
}

HIDING_PLACES = {
    "under_bench": HidingPlace(
        id="under_bench",
        label="bench",
        the="the old bench",
        scene="the old bench by the wall",
        need="hook",
        risk="reaching into dark spaces can pinch your fingers",
        sounds="Maybe it is stuck under there",
        tags={"under", "dark_space"},
    ),
    "high_shelf": HidingPlace(
        id="high_shelf",
        label="high shelf",
        the="the highest shelf",
        scene="the tallest shelf near the rafters",
        need="stool",
        risk="climbing on wobbly things can make you slip",
        sounds="Maybe something is perched up high",
        tags={"high", "dark_space"},
    ),
    "trunk": HidingPlace(
        id="trunk",
        label="trunk",
        the="the old trunk",
        scene="the old trunk with brass corners",
        need="open",
        risk="snapping lids and hidden corners can bump little hands",
        sounds="Maybe it is shut inside there",
        tags={"container", "dark_space"},
    ),
}

SOURCES = {
    "robot": Source(
        id="robot",
        label="the little robot",
        phrase="a small silver toy robot with fading batteries",
        kind="toy",
        sound='"Ouch-dim! Ouch-dim!" it chirped in a flat tinny voice',
        reveal='The toy robot blinked once and said, "Ouch-dim!" again, but now it sounded silly instead of spooky.',
        truth="Its sleepy batteries made its old detective phrase come out all wrong.",
        allowed_places={"under_bench", "high_shelf"},
        tags={"toy", "batteries"},
    ),
    "parrot": Source(
        id="parrot",
        label="the talking parrot toy",
        phrase="a bright plush parrot with a squeeze box inside",
        kind="toy",
        sound='When the box inside was squashed, it croaked something like "ouch-dim"',
        reveal="The plush parrot flopped into view, and when the grown-up squeezed its middle, the same funny sound popped out.",
        truth="The sound was only the toy's squeaker talking through cloth and dust.",
        allowed_places={"trunk", "high_shelf"},
        tags={"toy", "sound"},
    ),
    "kitten": Source(
        id="kitten",
        label="the kitten",
        phrase="a small gray kitten with dusty whiskers",
        kind="pet",
        sound='Its mew had been bouncing off wood and tin until it came out sounding almost like "ouch-dim"',
        reveal="A tiny gray kitten peeped out, blinked at the light, and gave one offended little mew.",
        truth="Echoes in the dark had twisted a kitten's mew into a very odd sound.",
        allowed_places={"under_bench", "trunk"},
        tags={"pet", "animal"},
    ),
}

RESPONSES = {
    "grabber": Response(
        id="grabber",
        sense=3,
        handles={"hook"},
        text="used a long grabber and gently reached under the {place}",
        qa_text="used a long grabber to reach safely into the dark space",
        lesson="we do not solve dark mysteries by grabbing blindly",
        tags={"tool", "reacher"},
    ),
    "stool": Response(
        id="stool",
        sense=3,
        handles={"stool"},
        text="held a steady step stool and reached up carefully",
        qa_text="used a steady step stool and reached carefully with the light on",
        lesson="we do not climb on wobbly things just because we are curious",
        tags={"stool", "tool"},
    ),
    "open_carefully": Response(
        id="open_carefully",
        sense=3,
        handles={"open"},
        text="set one hand on the lid and opened the {place} slowly",
        qa_text="opened the container slowly with good light and careful hands",
        lesson="we open dark containers slowly and carefully",
        tags={"container", "careful"},
    ),
    "jump": Response(
        id="jump",
        sense=1,
        handles={"stool"},
        text="jumped for the thing in the dark",
        qa_text="jumped for it",
        lesson="jumping first is not a safe plan",
        tags={"unsafe"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on with a clear white beam",
        tags={"flashlight", "light"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little camping lantern",
        glow="made a warm round pool of light",
        tags={"lantern", "light"},
    ),
    "headlamp": Light(
        id="headlamp",
        label="head-lamp",
        phrase="a head-lamp",
        glow="lit the shelves and corners without using any hands",
        tags={"headlamp", "light"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Leo", "Max", "Ben", "Sam", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["careful", "cautious", "patient", "thoughtful", "brave", "curious"]


@dataclass
class StoryParams:
    setting: str
    place: str
    source: str
    response: str
    light: str
    solver: str
    solver_gender: str
    buddy: str
    buddy_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    solver_age: int = 5
    buddy_age: int = 7
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
    "dark": [
        ("Why can a sound seem scarier in the dark?",
         "In the dark, you cannot see what is making the sound, so your mind guesses before your eyes can check. That can make a small ordinary noise feel mysterious.")
    ],
    "flashlight": [
        ("Why is a flashlight good for checking a dark place?",
         "A flashlight lets you see before you touch anything. Good light helps you notice what is really there and keeps your hands safer.")
    ],
    "lantern": [
        ("What does a lantern help you do?",
         "A lantern spreads light around a whole little space. That makes it easier to inspect dark corners calmly.")
    ],
    "headlamp": [
        ("Why can a head-lamp be useful?",
         "A head-lamp shines where you look while keeping your hands free. That is handy when a grown-up needs both hands for a careful job.")
    ],
    "reacher": [
        ("What is a long grabber for?",
         "A long grabber helps someone reach under furniture or into a narrow space without putting fingers in first. It can make a small rescue safer.")
    ],
    "stool": [
        ("How should a step stool be used safely?",
         "A step stool should be steady and used with care, usually with a grown-up helping. It is not the same as climbing on boxes or crates.")
    ],
    "container": [
        ("Why should you open an old box or trunk slowly?",
         "Opening it slowly helps you see inside and keeps your fingers away from sharp corners or a quick lid. Careful hands make surprises easier to handle.")
    ],
    "batteries": [
        ("Why can a battery toy sound funny when the batteries are low?",
         "Low batteries can make a toy's voice weak, stretched, or garbled. That can turn a normal message into a silly mystery sound.")
    ],
    "animal": [
        ("Why might a kitten sound different in a small space?",
         "Sound can bounce off wood, metal, or walls and come back changed. In a small space, a kitten's mew can seem stranger than it really is.")
    ],
}
KNOWLEDGE_ORDER = ["dark", "flashlight", "lantern", "headlamp", "reacher", "stool", "container", "batteries", "animal"]


CURATED = [
    StoryParams(
        setting="attic",
        place="high_shelf",
        source="robot",
        response="stool",
        light="headlamp",
        solver="Nora",
        solver_gender="girl",
        buddy="Leo",
        buddy_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        solver_age=5,
        buddy_age=7,
    ),
    StoryParams(
        setting="hallway",
        place="under_bench",
        source="kitten",
        response="grabber",
        light="flashlight",
        solver="Max",
        solver_gender="boy",
        buddy="Ruby",
        buddy_gender="girl",
        parent="father",
        trait="thoughtful",
        relation="friends",
        solver_age=6,
        buddy_age=6,
    ),
    StoryParams(
        setting="shed",
        place="trunk",
        source="parrot",
        response="open_carefully",
        light="lantern",
        solver="Ava",
        solver_gender="girl",
        buddy="Finn",
        buddy_gender="boy",
        parent="mother",
        trait="patient",
        relation="siblings",
        solver_age=6,
        buddy_age=8,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_wait(params.relation, params.solver_age, params.buddy_age, params.trait) else "attempted"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    solver = f["solver"]
    buddy = f["buddy"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    light = f["light_cfg"]
    if f["waited"]:
        return [
            'Write a gentle mystery story for a 3-to-5-year-old that includes the word "ouch-dim" and ends happily.',
            f"Tell a child-friendly mystery where {solver.id} and {buddy.id} hear a strange sound from {place.the}, but they stop and get a grown-up with {light.phrase} before touching anything.",
            f"Write a short story with a lesson learned: a dark clue seems spooky, yet the children solve it safely and discover {source.label}.",
        ]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the word "ouch-dim" and ends happily.',
        f"Tell a mystery where {solver.id} hears 'ouch-dim' from {place.the}, tries one unsafe moment first, then learns to ask a grown-up for help and light.",
        f"Write a short lesson-learned story in which a spooky sound turns out to have an ordinary cause, and the ending feels cozy instead of scary.",
    ]


def pair_noun(solver: Entity, buddy: Entity, relation: str) -> str:
    if relation == "siblings":
        if solver.type == "boy" and buddy.type == "boy":
            return "two brothers"
        if solver.type == "girl" and buddy.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    solver = f["solver"]
    buddy = f["buddy"]
    adult = f["adult"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    response = f["response"]
    light = f["light_cfg"]
    relation = f["relation"]
    pair = pair_noun(solver, buddy, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {solver.id} and {buddy.id}, and the {adult.label_word} who helped them solve a dark little mystery."
        ),
        (
            'What was the mystery sound?',
            f"They heard a strange noise that seemed to say 'ouch-dim' from {place.the}. Because they could not see into the shadows, the sound felt bigger and spookier than it really was."
        ),
        (
            "Why did the children think they needed help?",
            f"They knew the sound was coming from a dark hiding place. {buddy.id} also understood that touching or climbing in the dark could lead to a little ouch, so getting light and a grown-up was safer."
        ),
    ]
    if f["waited"]:
        qa.append(
            (
                f"What did {solver.id} do after {buddy.id} warned {solver.pronoun('object')}?",
                f"{solver.id} stopped before trying anything risky and went to get the {adult.label_word}. That choice changed the mystery from a scary guess into a calm search."
            )
        )
    else:
        qa.append(
            (
                f"Did {solver.id} get hurt?",
                f"{solver.id} had a tiny scare and a little ouch, but nothing serious happened. The close call helped {solver.pronoun('object')} understand why dark places should be checked carefully."
            )
        )
    qa.append(
        (
            "How did the grown-up solve the mystery?",
            f"The {adult.label_word} brought {light.phrase} and {response.qa_text}. Once the light was on, they could finally see clearly enough to find {source.label}."
        )
    )
    qa.append(
        (
            "What was really making the sound?",
            f"It was {source.label}. {source.truth} That is why the spooky clue turned out to have an ordinary answer."
        )
    )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned that mysteries in the dark should be solved with light, patience, and help. Curiosity is good, but hands and feet need safe choices too."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily, with the mystery solved and the room feeling cozy again. The children were no longer frightened because they knew what had changed and why."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dark"}
    tags |= set(world.facts["light_cfg"].tags)
    if world.facts["response"].id == "grabber":
        tags.add("reacher")
    if world.facts["response"].id == "stool":
        tags.add("stool")
    if world.facts["response"].id == "open_carefully":
        tags.add("container")
    if world.facts["source_cfg"].id == "robot":
        tags.add("batteries")
    if world.facts["source_cfg"].id == "kitten":
        tags.add("animal")
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
            shown = {k: v for k, v in e.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_place_source(place: HidingPlace, source: Source) -> str:
    return (
        f"(No story: {source.label} is not a reasonable thing to discover in {place.the}. "
        f"Pick a source that could plausibly be hidden there.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these safer responses: {better}.)"
    )


def explain_place_response(place: HidingPlace, response: Response) -> str:
    return (
        f"(No story: {response.id} does not match {place.the}. "
        f"This mystery needs a method that handles '{place.need}'.)"
    )


ASP_RULES = r"""
fits_source(P, S) :- allowed(S, P).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
fits_response(P, R) :- place_need(P, Need), handles(R, Need).
valid(Setting, P, S) :- setting(Setting), place(P), source(S), fits_source(P, S).

care_now(T) :- trait(T), careful_trait(T).
init_care(5) :- care_now(T), trait(T).
init_care(3) :- trait(T), not care_now(T).
buddy_older :- relation(siblings), solver_age(SA), buddy_age(BA), BA > SA.
bonus(3) :- buddy_older.
bonus(0) :- not buddy_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
waited :- buddy_older, authority(A), bold_init(BI), A > BI.
outcome(waited) :- waited.
outcome(attempted) :- not waited.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_need", pid, place.need))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for pid in sorted(source.allowed_places):
            lines.append(asp.fact("allowed", sid, pid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for need in sorted(response.handles):
            lines.append(asp.fact("handles", rid, need))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
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
    scenario = "\n".join([
        asp.fact("trait", params.trait),
        asp.fact("relation", params.relation),
        asp.fact("solver_age", params.solver_age),
        asp.fact("buddy_age", params.buddy_age),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small mystery, a safe investigation, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--place", choices=HIDING_PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        place = HIDING_PLACES[args.place]
        source = SOURCES[args.source]
        if not source_fits(place, source):
            raise StoryError(explain_place_source(place, source))
    if args.response:
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))
        if args.place and not response_fits(HIDING_PLACES[args.place], RESPONSES[args.response]):
            raise StoryError(explain_place_response(HIDING_PLACES[args.place], RESPONSES[args.response]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.place is None or combo[1] == args.place)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, place_id, source_id = rng.choice(sorted(combos))
    place = HIDING_PLACES[place_id]

    response_candidates = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN
        and response_fits(place, response)
        and (args.response is None or rid == args.response)
    ]
    if not response_candidates:
        raise StoryError("(No safe response matches the given options.)")
    response_id = rng.choice(sorted(response_candidates))

    light_id = args.light or rng.choice(sorted(LIGHTS))
    solver, solver_gender = _pick_child(rng)
    buddy, buddy_gender = _pick_child(rng, avoid=solver)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    solver_age, buddy_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        setting=setting_id,
        place=place_id,
        source=source_id,
        response=response_id,
        light=light_id,
        solver=solver,
        solver_gender=solver_gender,
        buddy=buddy,
        buddy_gender=buddy_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        solver_age=solver_age,
        buddy_age=buddy_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.place not in HIDING_PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source '{params.source}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light '{params.light}'.)")

    place = HIDING_PLACES[params.place]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    if not source_fits(place, source):
        raise StoryError(explain_place_source(place, source))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_fits(place, response):
        raise StoryError(explain_place_response(place, response))

    world = tell(
        setting=SETTINGS[params.setting],
        place_cfg=place,
        source_cfg=source,
        response_cfg=response,
        light_cfg=LIGHTS[params.light],
        solver_name=params.solver,
        solver_gender=params.solver_gender,
        buddy_name=params.buddy,
        buddy_gender=params.buddy_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        solver_age=params.solver_age,
        buddy_age=params.buddy_age,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        sample = generate(default_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, place, source) combos:\n")
        for setting_id, place_id, source_id in combos:
            print(f"  {setting_id:8} {place_id:12} {source_id}")
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
            header = f"### {p.solver} & {p.buddy}: {p.source} in {p.place} ({p.setting}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
