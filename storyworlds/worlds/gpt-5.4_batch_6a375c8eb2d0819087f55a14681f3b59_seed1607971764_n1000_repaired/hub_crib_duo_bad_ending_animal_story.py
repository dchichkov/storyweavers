#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py
==================================================================

A standalone story world for a small animal-story domain built from the seed
words "hub", "crib", and "duo" with a cautionary bad-ending branch.

Premise
-------
A playful animal duo turns a woodland hub into a pretend delivery station.
They want to send a soft present to a sleepy baby near a crib. One child wants
to race a wheeled cart down a ramp to get there faster. The other warns that
speed near the nursery can end in a crash. Sometimes the warning works. If it
doesn't, an adult may still catch the cart in time; if not, something fragile
breaks and the ending turns sad.

Run it
------
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py --target crib
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py --response shout_only
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py --all
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/hub_crib_duo_bad_ending_animal_story.py --verify
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
DARING_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "watchful", "sensible", "gentle"}


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
    fragile: bool = False
    rolling: bool = False
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "sister"}
        male = {"boy", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Hub:
    id: str
    label: str
    scene: str
    props: str
    nursery: str
    floor: str
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
class Racer:
    id: str
    label: str
    phrase: str
    speed: int
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
class Ramp:
    id: str
    label: str
    phrase: str
    steep: int
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
class Target:
    id: str
    label: str
    the: str
    near: str
    fragility: int
    fragile: bool = True
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
class Response:
    id: str
    sense: int
    power: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"driver", "watcher"}]

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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if cart is None or cart.meters["rolling"] < THRESHOLD:
        return out
    sig = ("rattle", "cart")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nursery = world.get("nursery")
    nursery.meters["danger"] += 1
    baby = world.get("baby")
    baby.memes["startle"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__rattle__")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    cart = world.entities.get("cart")
    if target is None or cart is None:
        return out
    if cart.meters["crashed"] < THRESHOLD or target.meters["broken"] >= THRESHOLD:
        return out
    sig = ("break", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["broken"] += 1
    nursery = world.get("nursery")
    nursery.meters["mess"] += 1
    baby = world.get("baby")
    baby.memes["cry"] += 1
    out.append("__break__")
    return out


CAUSAL_RULES = [
    Rule(name="rattle", tag="physical", apply=_r_rattle),
    Rule(name="break", tag="physical", apply=_r_break),
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


def hazard_at_risk(racer: Racer, ramp: Ramp, target: Target) -> bool:
    return racer.speed > 0 and ramp.steep > 0 and target.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def crash_severity(racer: Racer, ramp: Ramp, target: Target, delay: int) -> int:
    return racer.speed + ramp.steep + target.fragility + delay


def is_stopped(response: Response, racer: Racer, ramp: Ramp, target: Target, delay: int) -> bool:
    return response.power >= crash_severity(racer, ramp, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, driver_age: int, watcher_age: int, trait: str) -> bool:
    watcher_older = relation == "siblings" and watcher_age > driver_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if watcher_older else 0.0)
    return watcher_older and authority > DARING_INIT


def predict_crash(world: World, severity: int) -> dict:
    sim = world.copy()
    cart = sim.get("cart")
    target = sim.get("target")
    cart.meters["rolling"] += 1
    cart.meters["speed"] = float(severity)
    cart.meters["crashed"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("nursery").meters["danger"],
        "broken": target.meters["broken"] >= THRESHOLD,
    }


def play_setup(world: World, driver: Entity, watcher: Entity, hub: Hub, baby_name: str) -> None:
    for kid in (driver, watcher):
        kid.memes["joy"] += 1
    world.say(
        f"In {hub.label}, {driver.id} and {watcher.id} made a busy delivery station. "
        f"{hub.scene} {hub.props}"
    )
    world.say(
        f"The duo whispered extra softly because little {baby_name} was asleep in a crib by {hub.nursery}."
    )
    world.say(
        f'"Fast paws and careful paws!" {driver.id} cheered. "We can carry one soft present anywhere in the hub."'
    )


def need_delivery(world: World, target: Target) -> None:
    world.say(
        f"On a stool near {target.near} sat a tiny bundle of lavender moss tied with blue thread."
    )
    world.say(
        f"The present was meant for the nursery, but the path past {target.the} was narrow and close."
    )


def tempt(world: World, driver: Entity, racer: Racer, ramp: Ramp) -> None:
    driver.memes["daring"] += 1
    world.say(
        f'{driver.id} spotted {ramp.phrase} and grinned. "Let\'s use {racer.phrase} and zoom down {ramp.label}!"'
    )
    world.say("For one bright second, going fast sounded cleverer than going carefully.")


def warn(world: World, watcher: Entity, driver: Entity, racer: Racer, ramp: Ramp,
         target: Target, adult: Entity) -> None:
    severity = crash_severity(
        racer=racer,
        ramp=ramp,
        target=target,
        delay=world.facts["delay"],
    )
    pred = predict_crash(world, severity)
    watcher.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_break"] = pred["broken"]
    extra = ""
    if watcher.memes["caution"] >= 6:
        extra = f" {watcher.pronoun().capitalize()} tucked {watcher.pronoun('possessive')} paws close and would not smile at all."
    world.say(
        f'{watcher.id} shook {watcher.pronoun("possessive")} head. "{driver.id}, no. '
        f'{racer.label.capitalize()} on {ramp.label} could slam into {target.the}, and then {adult.label_word} would have a real mess to fix."{extra}'
    )


def defy(world: World, driver: Entity, watcher: Entity) -> None:
    driver.memes["defiance"] += 1
    older_driver = driver.attrs.get("relation") == "siblings" and driver.age > watcher.age
    if older_driver:
        world.say(
            f'"You worry too much," {driver.id} said. Because {driver.id} was the older sibling, {watcher.id} could not quite stop {driver.pronoun("object")}.'
        )
    else:
        world.say(
            f'"You worry too much," {driver.id} said, and reached for the cart anyway.'
        )


def back_down(world: World, driver: Entity, watcher: Entity, adult: Entity, safe_task: str) -> None:
    driver.memes["daring"] = 0.0
    driver.memes["relief"] += 1
    watcher.memes["relief"] += 1
    world.say(
        f'{driver.id} looked at the sleeping crib, then at {watcher.id}, and let out a small sigh. "All right," {driver.pronoun()} said. "We will do it the slow way."'
    )
    world.say(
        f"They asked {adult.label_word} for help and {safe_task}, one careful paw-step at a time."
    )


def launch(world: World, driver: Entity, racer: Racer, ramp: Ramp, target: Target, severity: int) -> None:
    cart = world.get("cart")
    cart.meters["rolling"] += 1
    cart.meters["speed"] = float(severity)
    world.say(
        f"{driver.id} set the moss bundle into {racer.the if hasattr(racer, 'the') else racer.phrase}."
    )
    world.say(
        f"Down {ramp.label} it went -- bump, rattle, skitter -- straight toward {target.the}."
    )
    propagate(world, narrate=False)


def alarm(world: World, watcher: Entity, target: Target, adult: Entity) -> None:
    world.say(f'"Look out! {target.The}!" {watcher.id} cried.')
    world.say(f'"{adult.label_word.capitalize()}!"')


def rescue(world: World, adult: Entity, response: Response, target: Target) -> None:
    cart = world.get("cart")
    cart.meters["rolling"] = 0.0
    cart.meters["crashed"] = 0.0
    world.get("nursery").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(f"{adult.label_word.capitalize()} rushed in and {body}.")
    world.say(
        f"The cart bumped once, then stopped. {target.The} stayed safe, and the sleeping room grew quiet again."
    )


def lesson(world: World, adult: Entity, driver: Entity, watcher: Entity, racer: Racer) -> None:
    for kid in (driver, watcher):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{adult.label_word.capitalize()} knelt beside them. "A nursery is not a race track," {adult.pronoun()} said softly. '
        f'"{racer.label.capitalize()} is for slow pulling here, not for zooming."'
    )
    world.say(f'{driver.id} and {watcher.id} nodded and held the moss bundle between them.')


def safe_finish(world: World, driver: Entity, watcher: Entity, target: Target, baby_name: str) -> None:
    driver.memes["joy"] += 1
    watcher.memes["joy"] += 1
    world.say(
        f"Together they padded past {target.the} and laid the present beside {baby_name}'s blanket."
    )
    world.say(
        "The hub felt gentle now, and the duo moved as carefully as moonlight on moss."
    )


def crash(world: World, target: Target) -> None:
    cart = world.get("cart")
    cart.meters["crashed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The cart smacked into {target.the} with a wooden crack."
    )


def rescue_fail(world: World, adult: Entity, response: Response, target: Target) -> None:
    body = response.fail.replace("{target}", target.label)
    world.say(f"{adult.label_word.capitalize()} hurried after it and {body}.")
    world.say(
        f"But the room had already heard the crash, and {target.the} could not stay whole."
    )


def sad_aftermath(world: World, driver: Entity, watcher: Entity, adult: Entity,
                  target: Target, baby_name: str) -> None:
    for kid in (driver, watcher):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    baby = world.get("baby")
    baby.memes["cry"] += 1
    if target.id == "crib":
        world.say(
            f"{baby_name} woke and wailed while {adult.label_word} lifted {baby.pronoun('object')} away from the broken crib and wrapped {baby.pronoun('object')} in a warm shawl."
        )
        world.say(
            "That night the baby had to sleep in a laundry basket lined with blankets, because the crib was splintered and useless."
        )
    else:
        world.say(
            f"{baby_name} woke and cried at the noise while pieces from {target.the} scattered over the nursery floor."
        )
        world.say(
            f"{adult.label_word.capitalize()} had to sweep and mend instead of sitting quietly beside the crib."
        )
    world.say(
        f"{driver.id} and {watcher.id} did not play messenger anymore that evening. They gathered the moss bundle in their paws and wished they had chosen slow steps first."
    )


def final_bad_image(world: World, hub: Hub, target: Target) -> None:
    if target.id == "crib":
        world.say(
            f"By bedtime, {hub.label} was hushed. Where the crib had stood, only a neat stack of broken slats leaned against the wall."
        )
    else:
        world.say(
            f"By bedtime, {hub.label} was hushed. Even from the nursery door, the pair could still see the damage near {target.the}."
        )


def tell(hub: Hub, racer: Racer, ramp: Ramp, target: Target, response: Response,
         driver_name: str = "Pip", driver_type: str = "boy",
         watcher_name: str = "Mira", watcher_type: str = "girl",
         adult_type: str = "mother", baby_name: str = "Nib",
         trait: str = "careful", delay: int = 0, driver_age: int = 6,
         watcher_age: int = 4, relation: str = "siblings") -> World:
    world = World()
    driver = world.add(Entity(
        id=driver_name,
        kind="character",
        type=driver_type,
        role="driver",
        age=driver_age,
        traits=["playful"],
        attrs={"relation": relation},
    ))
    watcher = world.add(Entity(
        id=watcher_name,
        kind="character",
        type=watcher_type,
        role="watcher",
        age=watcher_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type="kit",
        role="baby",
        label=baby_name,
    ))
    nursery = world.add(Entity(
        id="nursery",
        type="room",
        label="the nursery",
    ))
    world.add(Entity(
        id="cart",
        type="cart",
        label=racer.label,
        rolling=True,
    ))
    world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        fragile=target.fragile,
    ))

    driver.memes["daring"] = DARING_INIT
    watcher.memes["caution"] = initial_caution(trait)
    baby.memes["startle"] = 0.0
    baby.memes["cry"] = 0.0
    nursery.meters["danger"] = 0.0
    nursery.meters["mess"] = 0.0
    world.facts["delay"] = delay

    play_setup(world, driver, watcher, hub, baby_name)
    need_delivery(world, target)

    world.para()
    tempt(world, driver, racer, ramp)
    warn(world, watcher, driver, racer, ramp, target, adult)

    averted = would_avert(relation, driver_age, watcher_age, trait)

    if averted:
        back_down(
            world=world,
            driver=driver,
            watcher=watcher,
            adult=adult,
            safe_task="carried the little bundle to the crib together",
        )
        world.para()
        lesson(world, adult, driver, watcher, racer)
        safe_finish(world, driver, watcher, target, baby_name)
        severity = 0
        contained = True
    else:
        defy(world, driver, watcher)
        severity = crash_severity(racer, ramp, target, delay)
        world.para()
        launch(world, driver, racer, ramp, target, severity)
        alarm(world, watcher, target, adult)
        contained = is_stopped(response, racer, ramp, target, delay)
        world.para()
        if contained:
            rescue(world, adult, response, target)
            lesson(world, adult, driver, watcher, racer)
            world.para()
            safe_finish(world, driver, watcher, target, baby_name)
        else:
            crash(world, target)
            rescue_fail(world, adult, response, target)
            sad_aftermath(world, driver, watcher, adult, target, baby_name)
            final_bad_image(world, hub, target)

    outcome = "averted" if averted else ("contained" if contained else "broken")
    world.facts.update(
        hub=hub,
        racer=racer,
        ramp=ramp,
        target_cfg=target,
        response=response,
        driver=driver,
        watcher=watcher,
        adult=adult,
        baby_name=baby_name,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        broke=world.get("target").meters["broken"] >= THRESHOLD,
    )
    return world


HUBS = {
    "moss_hub": Hub(
        id="moss_hub",
        label="the moss hub",
        scene="It was a round room under an oak root, bright with fern-green light.",
        props="Acorn cups stood in tidy rows, a spool of blue thread served as a post marker, and smooth pebbles made little lanes on the floor.",
        nursery="the nursery arch",
        floor="moss",
        tags={"hub", "nursery"},
    ),
    "hay_hub": Hub(
        id="hay_hub",
        label="the hay hub",
        scene="It was the warm corner of a barn loft, striped with sun.",
        props="Twine reels, feather pillows, and polished chestnuts turned the floor into a fine little station.",
        nursery="the lamb room",
        floor="hay",
        tags={"hub", "nursery"},
    ),
    "hollow_hub": Hub(
        id="hollow_hub",
        label="the hollow hub",
        scene="It was a tree-room tucked inside a maple trunk, smelling of bark and apples.",
        props="Button signs hung from string, a thimble bell marked departures, and folded leaves waited like parcels.",
        nursery="the little hollow room",
        floor="wood",
        tags={"hub", "nursery"},
    ),
}

RACERS = {
    "seed_cart": Racer(
        id="seed_cart",
        label="seed cart",
        phrase="the seed cart",
        speed=2,
        tags={"cart", "wheels"},
    ),
    "apple_wagon": Racer(
        id="apple_wagon",
        label="apple wagon",
        phrase="the apple wagon",
        speed=3,
        tags={"wagon", "wheels"},
    ),
    "button_barrow": Racer(
        id="button_barrow",
        label="button barrow",
        phrase="the button barrow",
        speed=2,
        tags={"cart", "wheels"},
    ),
}

RAMPS = {
    "root_ramp": Ramp(
        id="root_ramp",
        label="the root ramp",
        phrase="the curved root ramp by the wall",
        steep=1,
        tags={"ramp"},
    ),
    "hay_slope": Ramp(
        id="hay_slope",
        label="the hay slope",
        phrase="the slippery hay slope",
        steep=2,
        tags={"ramp"},
    ),
    "board_ramp": Ramp(
        id="board_ramp",
        label="the board ramp",
        phrase="the polished board ramp",
        steep=2,
        tags={"ramp"},
    ),
}

TARGETS = {
    "crib": Target(
        id="crib",
        label="crib",
        the="the crib",
        near="the nursery door",
        fragility=2,
        fragile=True,
        tags={"crib", "sleep"},
    ),
    "milk_shelf": Target(
        id="milk_shelf",
        label="milk shelf",
        the="the milk shelf",
        near="the nursery door",
        fragility=1,
        fragile=True,
        tags={"shelf", "milk"},
    ),
    "lampstand": Target(
        id="lampstand",
        label="lampstand",
        the="the lampstand",
        near="the nursery curtain",
        fragility=2,
        fragile=True,
        tags={"lamp", "light"},
    ),
    "stone_step": Target(
        id="stone_step",
        label="stone step",
        the="the stone step",
        near="the nursery arch",
        fragility=0,
        fragile=False,
        tags={"stone"},
    ),
}

RESPONSES = {
    "catch_handle": Response(
        id="catch_handle",
        sense=3,
        power=7,
        text="snatched the cart handle and dragged it sideways before it could hit the {target}",
        fail="grabbed for the cart handle, but the wheels were already too wild to turn",
        qa_text="snatched the cart handle and pulled the cart aside",
        tags={"stop_fast", "cart"},
    ),
    "throw_cushion": Response(
        id="throw_cushion",
        sense=3,
        power=6,
        text="flung a thick cushion in front of the wheels, and the cart thumped into the padding instead of the {target}",
        fail="threw a cushion, but the cart bounced over it and kept going",
        qa_text="threw a thick cushion in front of the wheels to stop the cart",
        tags={"cushion", "cart"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=2,
        text="shouted for the duo to stop",
        fail="shouted a warning, but a warning alone could not stop rolling wheels",
        qa_text="only shouted a warning",
        tags={"warning"},
    ),
}

ANIMAL_NAMES = {
    "girl": ["Mira", "Poppy", "Tansy", "Lulu", "Hazel"],
    "boy": ["Pip", "Toby", "Nico", "Bram", "Otis"],
}

BABY_NAMES = ["Nib", "Dew", "Peep", "Fern"]
TRAITS = ["careful", "watchful", "sensible", "gentle", "curious", "brisk"]


@dataclass
class StoryParams:
    hub: str
    racer: str
    ramp: str
    target: str
    response: str
    driver: str
    driver_gender: str
    watcher: str
    watcher_gender: str
    adult: str
    baby_name: str
    trait: str
    delay: int = 0
    driver_age: int = 6
    watcher_age: int = 4
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
    "crib": [
        (
            "What is a crib?",
            "A crib is a small bed with sides for a baby. The sides help keep the baby safe while sleeping.",
        )
    ],
    "hub": [
        (
            "What is a hub?",
            "A hub is a busy center where things come together. In a story, it can be the little place where everyone gathers and works.",
        )
    ],
    "cart": [
        (
            "Why can a cart be dangerous indoors if it rolls too fast?",
            "A cart with wheels keeps moving once it gets going. Indoors it can bump into furniture or a sleeping place before small paws can stop it.",
        )
    ],
    "ramp": [
        (
            "Why does a ramp make wheels go faster?",
            "A ramp slopes downward, so rolling things speed up as they go. The steeper the ramp is, the harder it can be to stop.",
        )
    ],
    "sleep": [
        (
            "Why should animals be quiet near a sleeping baby?",
            "Sleeping babies need calm, gentle sounds. Loud crashes can frighten them awake and make them cry.",
        )
    ],
    "cushion": [
        (
            "How can a cushion help stop something rolling?",
            "A thick cushion can soften a bump and slow the wheels down. It works by making the rolling thing hit something soft instead of something hard.",
        )
    ],
    "stop_fast": [
        (
            "What is a good way for a grown-up to stop a runaway cart?",
            "A grown-up can grab the handle or block the wheels quickly. Acting fast matters because rolling things do not stop on their own right away.",
        )
    ],
    "warning": [
        (
            "Why is shouting sometimes not enough to stop an accident?",
            "Words can warn someone, but words cannot hold wheels still. When something is already moving fast, it may need hands or a barrier to stop it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hub", "crib", "sleep", "cart", "ramp", "cushion", "stop_fast", "warning"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hub_id in HUBS:
        for racer_id, racer in RACERS.items():
            for ramp_id, ramp in RAMPS.items():
                for target_id, target in TARGETS.items():
                    if hazard_at_risk(racer, ramp, target):
                        combos.append((hub_id, racer_id, ramp_id, target_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    driver = f["driver"]
    watcher = f["watcher"]
    target = f["target_cfg"]
    hub = f["hub"]
    outcome = f["outcome"]
    if outcome == "broken":
        return [
            'Write an animal story for a 3-to-5-year-old that uses the words "hub", "crib", and "duo" and ends sadly.',
            f"Tell a cautionary animal story where a playful duo races a cart inside {hub.label} near {target.the}, and something important gets broken.",
            f"Write a woodland nursery story where {driver.id} ignores {watcher.id}'s warning, and the ending shows why fast games do not belong near a crib.",
        ]
    if outcome == "averted":
        return [
            'Write an animal story for a 3-to-5-year-old that uses the words "hub", "crib", and "duo" and ends safely.',
            f"Tell a gentle story where {watcher.id} warns {driver.id} not to race a cart near a crib, and the duo chooses slow careful steps instead.",
            f"Write a simple nursery tale about a busy hub, a present, and a pair of young animals who stop an accident before it happens.",
        ]
    return [
        'Write an animal story for a 3-to-5-year-old that uses the words "hub", "crib", and "duo".',
        f"Tell a story where a duo of young animals nearly crashes a cart into {target.the}, but a grown-up stops it in time.",
        f"Write a child-facing animal story about racing indoors, a quiet crib, and learning that careful paws are better than fast paws.",
    ]


def pair_noun(driver: Entity, watcher: Entity, relation: str) -> str:
    if relation == "siblings":
        if driver.type == "boy" and watcher.type == "boy":
            return "two brothers"
        if driver.type == "girl" and watcher.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    driver = f["driver"]
    watcher = f["watcher"]
    adult = f["adult"]
    hub = f["hub"]
    racer = f["racer"]
    ramp = f["ramp"]
    target = f["target_cfg"]
    baby_name = f["baby_name"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(driver, watcher, relation)}, {driver.id} and {watcher.id}, in {hub.label}. They were trying to carry a present while {baby_name} slept nearby.",
        ),
        (
            "Why did the duo have to be quiet?",
            f"They had to be quiet because {baby_name} was asleep in a crib near the nursery. That is why racing indoors was risky from the start.",
        ),
        (
            f"What did {driver.id} want to do?",
            f"{driver.id} wanted to use the {racer.label} on {ramp.label} so the present would reach the nursery faster. The idea sounded exciting because speed felt like a shortcut.",
        ),
        (
            f"Why did {watcher.id} warn {driver.id}?",
            f"{watcher.id} warned {driver.id} that the cart could slam into {target.the}. {watcher.pronoun().capitalize()} understood that rolling wheels and a narrow nursery path could end in a crash.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed {driver.id}'s mind?",
                f"{driver.id} looked at the sleeping crib and listened to {watcher.id}'s warning. That helped {driver.pronoun('object')} choose the slow safe plan instead of the fast one.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. The duo carried the present with careful paws, and the hub felt calm again.",
            )
        )
    elif outcome == "contained":
        resp = f["response"].qa_text.replace("{target}", target.label)
        qa.append(
            (
                f"How did the grown-up stop the accident?",
                f"The grown-up {resp}. That quick action stopped the rolling cart before it could smash into {target.the}.",
            )
        )
        qa.append(
            (
                "What lesson did the duo learn?",
                f"They learned that the nursery was not a race track. The near miss showed them that fast games can turn dangerous in just one moment.",
            )
        )
    else:
        qa.append(
            (
                f"What broke in the story?",
                f"{target.The} broke when the cart crashed into it. The crash happened because the wheels were already moving too fast to stop safely.",
            )
        )
        if target.id == "crib":
            qa.append(
                (
                    "Why is the ending sad?",
                    f"The ending is sad because the baby's crib was broken and could not be used at bedtime. Even though the baby was carried to safety, the duo had to see the nursery changed by their choice.",
                )
            )
        else:
            qa.append(
                (
                    "Why is the ending sad?",
                    f"The ending is sad because the nursery was left noisy, broken, and full of extra work for the grown-up. The duo could not keep playing after they saw what their fast game had damaged.",
                )
            )
        qa.append(
            (
                "What did the duo learn at the end?",
                "They learned that being careful matters more than being quick near a sleeping baby. The broken room showed them the warning had been true.",
            )
        )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["hub"].tags) | set(f["target_cfg"].tags) | set(f["racer"].tags) | set(f["ramp"].tags)
    outcome = f["outcome"]
    if outcome == "contained":
        tags |= set(f["response"].tags)
    elif outcome == "broken":
        tags |= {"warning"}
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("fragile", ent.fragile), ("rolling", ent.rolling)) if on]
        if flags:
            parts.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hub="moss_hub",
        racer="apple_wagon",
        ramp="board_ramp",
        target="crib",
        response="catch_handle",
        driver="Pip",
        driver_gender="boy",
        watcher="Mira",
        watcher_gender="girl",
        adult="mother",
        baby_name="Nib",
        trait="careful",
        delay=0,
        driver_age=6,
        watcher_age=4,
        relation="siblings",
    ),
    StoryParams(
        hub="hay_hub",
        racer="seed_cart",
        ramp="hay_slope",
        target="milk_shelf",
        response="throw_cushion",
        driver="Lulu",
        driver_gender="girl",
        watcher="Otis",
        watcher_gender="boy",
        adult="father",
        baby_name="Fern",
        trait="watchful",
        delay=1,
        driver_age=5,
        watcher_age=5,
        relation="friends",
    ),
    StoryParams(
        hub="hollow_hub",
        racer="apple_wagon",
        ramp="board_ramp",
        target="crib",
        response="catch_handle",
        driver="Nico",
        driver_gender="boy",
        watcher="Hazel",
        watcher_gender="girl",
        adult="aunt",
        baby_name="Dew",
        trait="gentle",
        delay=2,
        driver_age=7,
        watcher_age=5,
        relation="siblings",
    ),
    StoryParams(
        hub="moss_hub",
        racer="seed_cart",
        ramp="root_ramp",
        target="lampstand",
        response="throw_cushion",
        driver="Poppy",
        driver_gender="girl",
        watcher="Toby",
        watcher_gender="boy",
        adult="uncle",
        baby_name="Peep",
        trait="careful",
        delay=0,
        driver_age=4,
        watcher_age=7,
        relation="siblings",
    ),
]


def explain_rejection(racer: Racer, ramp: Ramp, target: Target) -> str:
    if not target.fragile:
        return (
            f"(No story: {target.the} is too sturdy to make a believable crash problem here. "
            f"Pick something fragile like a crib, milk shelf, or lampstand.)"
        )
    if racer.speed <= 0 or ramp.steep <= 0:
        return "(No story: this setup would not make the cart roll dangerously.)"
    return "(No story: this combination does not create a believable nursery hazard.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the stronger responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.driver_age, params.watcher_age, params.trait):
        return "averted"
    contained = is_stopped(
        response=RESPONSES[params.response],
        racer=RACERS[params.racer],
        ramp=RAMPS[params.ramp],
        target=TARGETS[params.target],
        delay=params.delay,
    )
    return "contained" if contained else "broken"


ASP_RULES = r"""
hazard(R, Rp, T) :- racer(R), ramp(Rp), target(T), speed(R, S), S > 0, steep(Rp, St), St > 0, fragile(T).
sensible(Resp) :- response(Resp), sense(Resp, S), sense_min(M), S >= M.
valid(H, R, Rp, T) :- hub(H), hazard(R, Rp, T), target(T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
watcher_older :- relation(siblings), driver_age(DA), watcher_age(WA), WA > DA.
bonus(4) :- watcher_older.
bonus(0) :- not watcher_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- watcher_older, authority(A), daring_init(D), A > D.

severity(Sr + Sp + Fr + D) :- chosen_racer(R), speed(R, Sr),
                              chosen_ramp(Rp), steep(Rp, Sp),
                              chosen_target(T), fragility(T, Fr),
                              delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hub_id in HUBS:
        lines.append(asp.fact("hub", hub_id))
    for racer_id, racer in RACERS.items():
        lines.append(asp.fact("racer", racer_id))
        lines.append(asp.fact("speed", racer_id, racer.speed))
    for ramp_id, ramp in RAMPS.items():
        lines.append(asp.fact("ramp", ramp_id))
        lines.append(asp.fact("steep", ramp_id, ramp.steep))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("fragility", target_id, target.fragility))
        if target.fragile:
            lines.append(asp.fact("fragile", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("daring_init", int(DARING_INIT)))
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
            asp.fact("chosen_racer", params.racer),
            asp.fact("chosen_ramp", params.ramp),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("driver_age", params.driver_age),
            asp.fact("watcher_age", params.watcher_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sens = {r.id for r in sensible_responses()}
    clingo_sens = set(asp_sensible())
    if python_sens == clingo_sens:
        print(f"OK: sensible responses match ({sorted(python_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=False, header="### smoke")
        if "hub" not in smoke.story or "crib" not in smoke.story or "duo" not in smoke.story:
            raise StoryError("Smoke story did not include required seed words.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a playful duo, a quiet crib, and a risky race in a busy hub."
    )
    ap.add_argument("--hub", choices=HUBS)
    ap.add_argument("--racer", choices=RACERS)
    ap.add_argument("--ramp", choices=RAMPS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start before the grown-up can act")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in ANIMAL_NAMES[gender] if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None:
        target = TARGETS[args.target]
        racer = RACERS[args.racer] if args.racer else next(iter(RACERS.values()))
        ramp = RAMPS[args.ramp] if args.ramp else next(iter(RAMPS.values()))
        if not hazard_at_risk(racer, ramp, target):
            raise StoryError(explain_rejection(racer, ramp, target))
    if args.racer is not None and args.ramp is not None and args.target is not None:
        racer = RACERS[args.racer]
        ramp = RAMPS[args.ramp]
        target = TARGETS[args.target]
        if not hazard_at_risk(racer, ramp, target):
            raise StoryError(explain_rejection(racer, ramp, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hub is None or combo[0] == args.hub)
        and (args.racer is None or combo[1] == args.racer)
        and (args.ramp is None or combo[2] == args.ramp)
        and (args.target is None or combo[3] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hub_id, racer_id, ramp_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    driver_name, driver_gender = _pick_name(rng)
    watcher_name, watcher_gender = _pick_name(rng, avoid=driver_name)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    baby_name = rng.choice(BABY_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    driver_age, watcher_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        hub=hub_id,
        racer=racer_id,
        ramp=ramp_id,
        target=target_id,
        response=response_id,
        driver=driver_name,
        driver_gender=driver_gender,
        watcher=watcher_name,
        watcher_gender=watcher_gender,
        adult=adult,
        baby_name=baby_name,
        trait=trait,
        delay=delay,
        driver_age=driver_age,
        watcher_age=watcher_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hub not in HUBS:
        raise StoryError(f"(Unknown hub: {params.hub})")
    if params.racer not in RACERS:
        raise StoryError(f"(Unknown racer: {params.racer})")
    if params.ramp not in RAMPS:
        raise StoryError(f"(Unknown ramp: {params.ramp})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    hub = HUBS[params.hub]
    racer = RACERS[params.racer]
    ramp = RAMPS[params.ramp]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]

    if not hazard_at_risk(racer, ramp, target):
        raise StoryError(explain_rejection(racer, ramp, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        hub=hub,
        racer=racer,
        ramp=ramp,
        target=target,
        response=response,
        driver_name=params.driver,
        driver_type=params.driver_gender,
        watcher_name=params.watcher,
        watcher_type=params.watcher_gender,
        adult_type=params.adult,
        baby_name=params.baby_name,
        trait=params.trait,
        delay=params.delay,
        driver_age=params.driver_age,
        watcher_age=params.watcher_age,
        relation=params.relation,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hub, racer, ramp, target) combos:\n")
        for hub_id, racer_id, ramp_id, target_id in combos:
            print(f"  {hub_id:10} {racer_id:13} {ramp_id:10} {target_id}")
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
            header = (
                f"### {p.driver} & {p.watcher}: {p.racer} on {p.ramp} toward {p.target} "
                f"({p.hub}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
