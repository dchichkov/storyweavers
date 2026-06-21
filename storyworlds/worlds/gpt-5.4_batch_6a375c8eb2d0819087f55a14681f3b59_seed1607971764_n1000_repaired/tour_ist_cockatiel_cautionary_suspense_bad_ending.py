#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py
================================================================================

A standalone story world about a visiting child, a cherished cockatiel, and the
difference between a lovely idea and a safe one.

The seed asked for:
- the words "tour-ist" and "cockatiel"
- a cautionary story
- suspense
- a bad ending
- a style that stays warm and child-facing

This world models a small holiday guesthouse domain. A child tour-ist befriends
the house cockatiel and wants to take the bird to a pretty place. A gentle
grown-up explains that small birds can startle in noisy, windy places, so they
must go in a secure way. If the child chooses an unsafe method, the bird may
flutter away. A quick, sensible search can sometimes bring the bird back, but
not always.

Run it
------
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py --destination pier --method shoulder
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py --destination breakfast_room --method shoulder
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py --qa --seed 777
    python storyworlds/worlds/gpt-5.4/tour_ist_cockatiel_cautionary_suspense_bad_ending.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    can_fly: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "innkeeper", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "bird":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "innkeeper": "innkeeper",
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
class Setting:
    id: str
    lodging: str
    opening: str
    host_name: str
    host_type: str
    host_phrase: str
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
class Destination:
    id: str
    label: str
    phrase: str
    detail: str
    sound: str
    open_sky: bool
    startle: int
    affords: set[str] = field(default_factory=lambda: {"visit"})
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
    phrase: str
    secure: int
    closed: bool
    worn: bool = False
    plural: bool = False
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


@dataclass
class StoryParams:
    setting: str
    destination: str
    method: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    bird_name: str
    weather: str
    host_type: str
    trait: str
    delay: int = 0
    child_age: int = 6
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.weather = self.weather
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


def _r_escape(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("bird")
    dest = world.facts.get("destination_cfg")
    method = world.facts.get("method_cfg")
    if not bird or not dest or not method:
        return out
    if bird.meters["outdoors"] < THRESHOLD:
        return out
    if method.closed:
        return out
    if method.secure >= world.facts.get("severity", 0):
        return out
    sig = ("escape", dest.id, method.id, world.weather)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.meters["escaped"] += 1
    bird.meters["distance"] += float(dest.startle)
    for kid_role in ("child", "helper"):
        if kid_role in world.entities:
            world.get(kid_role).memes["fear"] += 1
    if "host" in world.entities:
        world.get("host").memes["worry"] += 1
    out.append("__escape__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("bird")
    if not bird or bird.meters["escaped"] < THRESHOLD:
        return out
    if bird.meters["recovered"] >= THRESHOLD:
        return out
    if world.facts.get("search_failed") is not True:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.meters["lost"] += 1
    world.get("child").memes["guilt"] += 1
    world.get("helper").memes["sadness"] += 1
    world.get("host").memes["sadness"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="escape", tag="physical", apply=_r_escape),
    Rule(name="loss", tag="emotional", apply=_r_loss),
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


def weather_wind(weather: str) -> int:
    return {"still": 0, "breezy": 1, "gusty": 2}[weather]


def outing_reasonable(destination: Destination, method: Method) -> bool:
    if destination.id not in destination.affords and destination.affords:
        return False
    if destination.open_sky:
        return True
    return method.secure >= 2


def suspenseful_risk(destination: Destination, method: Method, weather: str) -> bool:
    return destination.open_sky and not method.closed and method.secure < (destination.startle + weather_wind(weather))


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(destination: Destination, weather: str) -> int:
    return destination.startle + weather_wind(weather)


def escape_happens(destination: Destination, method: Method, weather: str) -> bool:
    return destination.open_sky and not method.closed and method.secure < severity_of(destination, weather)


def recovered_by(response: Response, destination: Destination, weather: str, delay: int) -> bool:
    return response.power >= severity_of(destination, weather) + delay


def outcome_of(params: StoryParams) -> str:
    destination = DESTINATIONS[params.destination]
    method = METHODS[params.method]
    response = RESPONSES[params.response]
    if not escape_happens(destination, method, params.weather):
        return "safe"
    return "recovered" if recovered_by(response, destination, params.weather, params.delay) else "lost"


def explain_combo(destination: Destination, method: Method) -> str:
    if not destination.open_sky and method.secure < 2:
        return (
            f"(No story: {destination.label} is too sheltered for a suspenseful escape story, "
            f"and carrying the bird by {method.label} there would not create a strong cautionary turn. "
            f"Pick an open place like the pier or choose a secure method.)"
        )
    return "(No story: this outing does not fit the world model.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_escape(world: World, destination_id: str, method_id: str, weather: str) -> dict:
    sim = world.copy()
    sim.facts["destination_cfg"] = DESTINATIONS[destination_id]
    sim.facts["method_cfg"] = METHODS[method_id]
    sim.facts["severity"] = severity_of(DESTINATIONS[destination_id], weather)
    sim.weather = weather
    sim.get("bird").meters["outdoors"] += 1
    propagate(sim, narrate=False)
    bird = sim.get("bird")
    return {
        "escape": bird.meters["escaped"] >= THRESHOLD,
        "distance": bird.meters["distance"],
    }


def introduce(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity) -> None:
    relation = "with " + helper.id if world.facts["relation"] == "friends" else "with " + helper.id
    world.say(
        f"{child.id} was a little {world.facts['trait']} tour-ist staying {world.setting.lodging} {relation}. "
        f"{world.setting.opening}"
    )
    world.say(
        f"{host.id}, the {host.label_word}, smiled and introduced them to {bird.id}, "
        f"a bright yellow cockatiel with orange cheek spots and a soft gray tail."
    )
    world.say(
        f"Soon {bird.id} was stepping from perch to perch and tipping his head as if he already knew their names."
    )


def bond(world: World, child: Entity, helper: Entity, bird: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    bird.memes["trust"] += 1
    world.say(
        f"{child.id} laughed when {bird.id} whistled back to the kettle in the kitchen, "
        f"and {helper.id} fed him one tiny seed at a time."
    )
    world.say(
        f"By afternoon, it felt as if the holiday had grown a small feathered heart."
    )


def warning(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity,
            destination: Destination, method: Method) -> None:
    pred = predict_escape(world, destination.id, method.id, world.weather)
    world.facts["predicted_escape"] = pred["escape"]
    world.facts["predicted_distance"] = pred["distance"]
    world.say(
        f'Before anyone went out, {host.id} touched the latch on {bird.id}\'s stand and said, '
        f'"{bird.id} startles quickly when a place is loud or windy. '
        f'If you take him to {destination.phrase}, he must go {method.phrase} if it is truly safe."'
    )
    if pred["escape"]:
        world.say(
            f"{helper.id} glanced toward {destination.label} and imagined {bird.id} bursting upward at {destination.sound}. "
            f"The thought made the air feel tighter."
        )


def temptation(world: World, child: Entity, helper: Entity, bird: Entity,
               destination: Destination) -> None:
    child.memes["desire"] += 1
    world.say(
        f"But {destination.phrase} looked beautiful that day. {destination.detail}"
    )
    world.say(
        f'{child.id} hugged the idea close. "Just one picture of {bird.id} there," {child.pronoun()} said. '
        f'"He would look like a little king of the holiday."'
    )


def helper_warns(world: World, helper: Entity, child: Entity, bird: Entity,
                 destination: Destination, method: Method) -> None:
    extra = ""
    if world.facts.get("predicted_escape"):
        extra = (
            f" {helper.id} could almost hear a sharp noise, see {bird.id}'s wings flash, "
            f"and lose him against the sky."
        )
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "Please don\'t be casual with a cockatiel," '
        f'{helper.pronoun()} said. "Small birds get scared fast, and {destination.label} is full of surprises."{extra}'
    )


def obey(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity,
         destination: Destination, method: Method) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    bird.memes["calm"] += 1
    bird.meters["outdoors"] += 1
    world.say(
        f"{child.id} looked at {bird.id}, then at the sky beyond the doorway, and decided not to be stubborn."
    )
    world.say(
        f"They took him to {destination.phrase} {method.phrase}, and when {destination.sound} came and went, "
        f"{bird.id} only blinked and tucked one foot up safely."
    )
    world.say(
        f"After one cheerful picture, they brought him back in, and the whole guesthouse felt peaceful again."
    )


def defy(world: World, child: Entity, helper: Entity, bird: Entity, method: Method) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} nodded as if listening, but the pretty idea still glowed in {child.pronoun("possessive")} mind.'
    )
    if method.id == "shoulder":
        world.say(
            f"When {host_name(world)} turned to fold napkins, {child.id} lifted {bird.id} onto {child.pronoun('possessive')} shoulder and hurried toward the door."
        )
    elif method.id == "finger":
        world.say(
            f"When nobody was looking for one little breath, {child.id} let {bird.id} step onto {child.pronoun('possessive')} finger and slipped outside."
        )
    else:
        world.say(
            f"In the bustle of getting ready, {child.id} carried {bird.id} out anyway."
        )
    world.say(
        f"{helper.id} followed with a worried face and a fast little heartbeat."
    )


def take_out(world: World, bird: Entity, destination: Destination, method: Method) -> None:
    world.facts["destination_cfg"] = destination
    world.facts["method_cfg"] = method
    world.facts["severity"] = severity_of(destination, world.weather)
    bird.meters["outdoors"] += 1
    propagate(world, narrate=False)
    if bird.meters["escaped"] < THRESHOLD:
        world.say(
            f"For a moment, it seemed as if the risk had been imagined. {bird.id} turned his head, "
            f"crest lifting in the light, while {destination.sound} rolled around them."
        )


def escape_scene(world: World, child: Entity, helper: Entity, bird: Entity,
                 destination: Destination) -> None:
    world.say(
        f"Then it happened. {destination.sound.capitalize()} crashed together all at once."
    )
    world.say(
        f"{bird.id}'s crest sprang up. He gave one frightened cry, beat his wings, and flew from {child.id} so quickly "
        f"that the motion felt like a torn ribbon in the air."
    )
    world.say(
        f"{child.id} reached up too late. {bird.id} skimmed past the rail, rose into the bright open sky, "
        f"and became smaller than a hand."
    )


def search(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity,
           response: Response, destination: Destination, delay: int) -> None:
    world.say(
        f"{helper.id} shouted for {host.id}, and all three of them ran after the small moving speck."
    )
    body = response.text.replace("{bird}", bird.id).replace("{destination}", destination.label)
    world.say(body)
    ok = recovered_by(response, destination, world.weather, delay)
    world.facts["search_failed"] = not ok
    if ok:
        bird.meters["recovered"] += 1
        bird.meters["escaped"] = 0.0
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        host.memes["relief"] += 1
        world.say(
            f"At last {bird.id} fluttered down, trembling but safe, and {host.id} wrapped both hands around the carrier door before anyone spoke again."
        )
    else:
        propagate(world, narrate=False)
        fail = response.fail.replace("{bird}", bird.id).replace("{destination}", destination.label)
        world.say(fail)
        world.say(
            f"The light thinned. Roof after roof went pale. Still, {bird.id} did not come back."
        )


def safe_lesson(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity) -> None:
    world.say(
        f"Back inside, {host.id} knelt beside them and stroked {bird.id}'s crest through the bars of the carrier."
    )
    world.say(
        f'"I know you wanted to share something lovely," {host.pronoun()} said softly. '
        f'"But love has to keep small creatures safe, even when a picture would be pretty."'
    )
    world.say(
        f"{child.id} nodded and promised never to carry {bird.id} out carelessly again."
    )


def sad_ending(world: World, child: Entity, helper: Entity, host: Entity, bird: Entity) -> None:
    child.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"They came back to the guesthouse with the carrier empty. No one hurried anymore."
    )
    world.say(
        f'{host.id} sat beside {child.id} on the porch step and said, '
        f'"I know you meant kindness. But frightened birds can vanish in one second, and sometimes one second is too much."'
    )
    world.say(
        f"{child.id} cried quietly into {child.pronoun('possessive')} sleeves while {helper.id} held {child.pronoun('possessive')} hand."
    )
    world.say(
        f"That night the perch by the window stayed bare, and the whole warm little house listened to the sea without {bird.id}'s whistle."
    )


def host_name(world: World) -> str:
    return world.get("host").id


def tell(setting: Setting, destination: Destination, method: Method, response: Response,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Theo", helper_gender: str = "boy",
         bird_name: str = "Sunny", weather: str = "breezy",
         host_type: str = "innkeeper", trait: str = "kind",
         delay: int = 0, child_age: int = 6, helper_age: int = 7,
         relation: str = "siblings") -> World:
    world = World(setting)
    world.weather = weather
    world.facts.update(
        relation=relation,
        trait=trait,
        delay=delay,
        weather=weather,
        search_failed=False,
    )

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"age": child_age, "relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["careful"],
        attrs={"age": helper_age, "relation": relation},
    ))
    host = world.add(Entity(
        id=setting.host_name,
        kind="character",
        type=host_type,
        role="host",
        label=setting.host_phrase,
        attrs={"setting": setting.id},
    ))
    bird = world.add(Entity(
        id=bird_name,
        kind="thing",
        type="bird",
        role="bird",
        label="cockatiel",
        can_fly=True,
        attrs={"home": setting.id},
    ))

    child.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0
    bird.memes["trust"] = 0.0
    bird.meters["escaped"] = 0.0
    bird.meters["recovered"] = 0.0
    bird.meters["lost"] = 0.0
    bird.meters["outdoors"] = 0.0

    introduce(world, child, helper, host, bird)
    bond(world, child, helper, bird)

    world.para()
    warning(world, child, helper, host, bird, destination, method)
    temptation(world, child, helper, bird, destination)
    helper_warns(world, helper, child, bird, destination, method)

    world.para()
    if method.secure >= severity_of(destination, weather):
        obey(world, child, helper, host, bird, destination, method)
        outcome = "safe"
    else:
        defy(world, child, helper, bird, method)
        take_out(world, bird, destination, method)
        if bird.meters["escaped"] >= THRESHOLD:
            world.para()
            escape_scene(world, child, helper, bird, destination)
            world.para()
            search(world, child, helper, host, bird, response, destination, delay)
            if bird.meters["recovered"] >= THRESHOLD:
                world.para()
                safe_lesson(world, child, helper, host, bird)
                outcome = "recovered"
            else:
                world.para()
                sad_ending(world, child, helper, host, bird)
                outcome = "lost"
        else:
            world.say(
                f"They were lucky this time, and luck was the only thing holding the moment together."
            )
            world.para()
            safe_lesson(world, child, helper, host, bird)
            outcome = "recovered"

    world.facts.update(
        child=child,
        helper=helper,
        host=host,
        bird=bird,
        setting_cfg=setting,
        destination_cfg=destination,
        method_cfg=method,
        response=response,
        outcome=outcome,
        escaped=bird.meters["escaped"] >= THRESHOLD or bird.meters["lost"] >= THRESHOLD or bird.meters["recovered"] >= THRESHOLD,
        recovered=bird.meters["recovered"] >= THRESHOLD,
        lost=bird.meters["lost"] >= THRESHOLD,
        severity=severity_of(destination, weather),
    )
    return world


SETTINGS = {
    "seaside_inn": Setting(
        id="seaside_inn",
        lodging="at a blue-painted seaside inn",
        opening="The windows smelled of salt and warm bread, and a string of shells clicked softly by the door.",
        host_name="Maris",
        host_type="innkeeper",
        host_phrase="the innkeeper",
        tags={"holiday", "inn"},
    ),
    "canal_hotel": Setting(
        id="canal_hotel",
        lodging="above a little canal hotel",
        opening="Below the balcony, boats bumped the posts with sleepy wooden knocks.",
        host_name="Elena",
        host_type="innkeeper",
        host_phrase="the innkeeper",
        tags={"holiday", "canal"},
    ),
    "hill_guesthouse": Setting(
        id="hill_guesthouse",
        lodging="in a white hill guesthouse",
        opening="From the porch, the town roofs looked like folded paper under the sun.",
        host_name="Aunt Rosa",
        host_type="aunt",
        host_phrase="their aunt",
        tags={"holiday", "family"},
    ),
}

DESTINATIONS = {
    "pier": Destination(
        id="pier",
        label="the pier",
        phrase="the pier",
        detail="The planks shone gold, and the water flashed in broken pieces below.",
        sound="gulls cried and ropes slapped the masts",
        open_sky=True,
        startle=3,
        tags={"pier", "bird", "sea"},
    ),
    "market_square": Destination(
        id="market_square",
        label="the market square",
        phrase="the market square",
        detail="Baskets of oranges glowed there, and striped awnings rippled over the stone.",
        sound="wheels rattled and vendors called",
        open_sky=True,
        startle=2,
        tags={"market", "bird"},
    ),
    "garden_patio": Destination(
        id="garden_patio",
        label="the garden patio",
        phrase="the garden patio",
        detail="Geraniums leaned over the wall, and sunlight rested on the tiles.",
        sound="chairs scraped and sparrows hopped in the ivy",
        open_sky=True,
        startle=1,
        tags={"garden", "bird"},
    ),
    "breakfast_room": Destination(
        id="breakfast_room",
        label="the breakfast room",
        phrase="the breakfast room",
        detail="The room smelled of jam and toast, and lace curtains breathed at the windows.",
        sound="cups clinked and spoons chimed",
        open_sky=False,
        startle=1,
        tags={"room", "bird"},
    ),
}

METHODS = {
    "carrier": Method(
        id="carrier",
        label="a closed travel carrier",
        phrase="inside a closed travel carrier",
        secure=4,
        closed=True,
        tags={"carrier", "safe"},
    ),
    "harness": Method(
        id="harness",
        label="a tiny bird harness",
        phrase="in a tiny bird harness",
        secure=3,
        closed=False,
        worn=True,
        tags={"harness", "safe"},
    ),
    "finger": Method(
        id="finger",
        label="one finger",
        phrase="on a finger",
        secure=1,
        closed=False,
        tags={"unsafe"},
    ),
    "shoulder": Method(
        id="shoulder",
        label="a shoulder",
        phrase="on a shoulder",
        secure=0,
        closed=False,
        tags={"unsafe"},
    ),
}

RESPONSES = {
    "whistle_and_carrier": Response(
        id="whistle_and_carrier",
        sense=3,
        power=3,
        text="Maris grabbed the carrier, called {bird}'s favorite whistle, and followed the sound of wings through {destination}.",
        fail="Maris called and called, carrying the open carrier from corner to corner, but {bird} had already gone beyond the nearest roofs.",
        qa_text="called the bird's favorite whistle while bringing the carrier",
        tags={"search", "carrier"},
    ),
    "millet_lure": Response(
        id="millet_lure",
        sense=3,
        power=2,
        text="The grown-up shook a little millet spray and spoke in the same calm kitchen voice {bird} knew at breakfast.",
        fail="They held out millet and waited in every likely place, but the city noises carried farther than the soft rattle of seeds.",
        qa_text="used millet and a calm voice to lure the bird back",
        tags={"search", "millet"},
    ),
    "call_and_wait": Response(
        id="call_and_wait",
        sense=2,
        power=1,
        text="They stood still, called {bird}'s name gently, and watched every railing and signpost for a yellow flutter.",
        fail="They called {bird}'s name until their voices turned thin, but no yellow flutter came back to them.",
        qa_text="called the bird's name and watched nearby perches",
        tags={"search"},
    ),
    "run_randomly": Response(
        id="run_randomly",
        sense=1,
        power=0,
        text="Everyone ran in different directions at once, shouting over one another.",
        fail="Everyone ran in different directions, and the frightened bird only vanished faster into the wide noise.",
        qa_text="ran around shouting",
        tags={"search"},
    ),
}

GIRL_NAMES = ["Mila", "Lina", "Ava", "Nora", "Sophie", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Theo", "Max", "Leo", "Eli", "Finn", "Noah", "Sam", "Jack"]
BIRD_NAMES = ["Sunny", "Pip", "Saffron", "Peep", "Goldie", "Mango"]
TRAITS = ["kind", "curious", "eager", "gentle", "bright"]
WEATHERS = ["still", "breezy", "gusty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for destination_id, destination in DESTINATIONS.items():
            for method_id, method in METHODS.items():
                if outing_reasonable(destination, method):
                    combos.append((setting_id, destination_id, method_id))
    return combos


KNOWLEDGE = {
    "cockatiel": [
        (
            "What is a cockatiel?",
            "A cockatiel is a small parrot with a crest on its head. It can whistle, climb, and flutter very quickly when it feels scared.",
        )
    ],
    "carrier": [
        (
            "Why do birds ride in a carrier?",
            "A carrier keeps a pet bird enclosed and protected when people travel. It helps the bird stay safe if something loud or surprising happens nearby.",
        )
    ],
    "harness": [
        (
            "What does a bird harness do?",
            "A bird harness is a gentle strap made to keep a pet bird attached to its person. It is safer than carrying a bird loose in an open place.",
        )
    ],
    "search": [
        (
            "What should you do if a pet bird gets loose?",
            "Tell a grown-up right away and search calmly with the bird's carrier or favorite food. A frightened bird needs familiar sounds and safe places, not more shouting.",
        )
    ],
    "sea": [
        (
            "Why can a pier be scary for a small bird?",
            "A pier can be full of wind, gull cries, and sudden boat noises. Those surprises can make a small bird flap away before someone can catch it.",
        )
    ],
    "market": [
        (
            "Why can a market square startle an animal?",
            "A market square has many footsteps, wheels, voices, and flapping cloth. All that movement can frighten a small animal.",
        )
    ],
    "bird": [
        (
            "Why should you be gentle with pet birds?",
            "Pet birds have light bodies and quick feelings. They can trust people deeply, but they can also startle in one fast moment.",
        )
    ],
    "millet": [
        (
            "Why might millet help call a bird back?",
            "Millet is a favorite seed treat for many little birds. A familiar food can help a nervous bird feel safe enough to come closer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cockatiel", "bird", "carrier", "harness", "search", "sea", "market", "millet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    bird = f["bird"]
    destination = f["destination_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a heartwarming but cautionary story for a 3-to-5-year-old that includes the words "tour-ist" and "cockatiel".',
            f"Tell a suspenseful holiday story where {child.id}, a young tour-ist, takes a cockatiel named {bird.id} to {destination.phrase} {method.phrase}, and the bird is lost.",
            f"Write a gentle sad-ending story where love is real but carelessness has a consequence, and the final image shows what the family misses.",
        ]
    if outcome == "recovered":
        return [
            f'Write a short, suspenseful story for a 3-to-5-year-old that includes the words "tour-ist" and "cockatiel".',
            f"Tell a story where a visiting child makes one unsafe choice with a cockatiel, the grown-up searches quickly, and the ending teaches careful love.",
            f"Write a cautionary but warm story set on holiday, where the danger is real and the rescue depends on sensible help.",
        ]
    return [
        f'Write a warm story for a 3-to-5-year-old that includes the words "tour-ist" and "cockatiel".',
        f"Tell a holiday story where a child wants to show a cockatiel a beautiful place, listens to a safety warning, and brings the bird back safely.",
        f"Write a gentle cautionary story where the best ending comes from choosing a secure way instead of a pretty but risky one.",
    ]


def pair_noun(child: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "girl" and helper.type == "girl":
            return "two sisters"
        if child.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    host = f["host"]
    bird = f["bird"]
    destination = f["destination_cfg"]
    method = f["method_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(child, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {helper.id}, the host {host.id}, and a cockatiel named {bird.id}. They meet while staying away from home on holiday.",
        ),
        (
            f"Why did {child.id} want to take {bird.id} to {destination.label}?",
            f"{child.id} thought {destination.label} looked beautiful and wanted one pretty picture there. The lovely idea made the risk feel smaller than it really was.",
        ),
        (
            f"What warning did {host.id} give about {bird.id}?",
            f"{host.id} said that {bird.id} startles in loud or windy places and must be taken out only in a truly safe way. That warning mattered because {destination.sound} could frighten a small bird very quickly.",
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(
            (
                f"How did they keep {bird.id} safe?",
                f"They took him to {destination.label} {method.phrase}, so the noise and movement could not carry him away. The safe method let them enjoy the outing without turning beauty into danger.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully. They brought {bird.id} back in safely, and the guesthouse still felt warm and happy.",
            )
        )
    elif f["outcome"] == "recovered":
        qa.append(
            (
                f"What happened when {bird.id} got scared?",
                f"{bird.id} suddenly flew away when {destination.sound} startled him. The suspense came from how fast one frightened flutter turned into a chase.",
            )
        )
        qa.append(
            (
                f"How did the grown-up try to get {bird.id} back?",
                f"{host.id} {response.qa_text}. That worked because a scared pet bird is more likely to come toward familiar sounds and familiar things than toward panic.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that loving an animal is not the same as wanting a pretty moment. Love has to protect a small creature before it tries to show that creature off.",
            )
        )
    else:
        qa.append(
            (
                f"What made the dangerous moment so sudden?",
                f"{destination.sound.capitalize()} startled {bird.id}, and he flew before {child.id} could react. Small birds move fast, so a careless choice can go wrong in one heartbeat.",
            )
        )
        qa.append(
            (
                f"Why couldn't they find {bird.id} before dark?",
                f"They searched, but {bird.id} had already gone beyond the nearest roofs and the noises of the place were bigger than their soft calling. By the time the light faded, he still had not come back.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly. The carrier came home empty, and the quiet perch by the window showed what had been lost.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"cockatiel", "bird"}
    destination = f["destination_cfg"]
    method = f["method_cfg"]
    response = f["response"]
    tags |= set(destination.tags)
    tags |= set(method.tags)
    tags |= set(response.tags)
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
    lines.append(f"  weather={world.weather}")
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
        if ent.can_fly:
            bits.append("can_fly=True")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- gate ------------------------------------------------------------------
risky(D, M, W) :- destination(D), method(M), weather(W),
                  open_sky(D), secure(M, S), severity(D, W, V), S < V, not closed(M).

reasonable(D, M) :- destination(D), method(M), open_sky(D).
reasonable(D, M) :- destination(D), method(M), not open_sky(D), secure(M, S), S >= 2.

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, D, M) :- setting(S), reasonable(D, M).

% --- outcome ---------------------------------------------------------------
safe_outing :- chosen_destination(D), chosen_method(M), chosen_weather(W),
               secure(M, S), severity(D, W, V), S >= V.
safe_outing :- chosen_destination(D), chosen_method(M), closed(M).

escape :- chosen_destination(D), chosen_method(M), chosen_weather(W),
          open_sky(D), not closed(M), secure(M, S), severity(D, W, V), S < V.

recovered :- escape, chosen_response(R), chosen_destination(D), chosen_weather(W),
             chosen_delay(Delay), power(R, P), severity(D, W, V), P >= V + Delay.

outcome(safe) :- safe_outing, not escape.
outcome(recovered) :- recovered.
outcome(lost) :- escape, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", did))
        if destination.open_sky:
            lines.append(asp.fact("open_sky", did))
        else:
            lines.append(asp.fact("indoor", did))
        for weather in WEATHERS:
            lines.append(asp.fact("severity", did, weather, severity_of(destination, weather)))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("secure", mid, method.secure))
        if method.closed:
            lines.append(asp.fact("closed", mid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for weather in WEATHERS:
        lines.append(asp.fact("weather", weather))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_destination", params.destination),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        setting="seaside_inn",
        destination="pier",
        method="shoulder",
        response="millet_lure",
        child_name="Mila",
        child_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        bird_name="Sunny",
        weather="gusty",
        host_type="innkeeper",
        trait="eager",
        delay=1,
        child_age=6,
        helper_age=8,
        relation="siblings",
    ),
    StoryParams(
        setting="hill_guesthouse",
        destination="market_square",
        method="finger",
        response="whistle_and_carrier",
        child_name="Noah",
        child_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        bird_name="Pip",
        weather="breezy",
        host_type="aunt",
        trait="curious",
        delay=0,
        child_age=6,
        helper_age=7,
        relation="friends",
    ),
    StoryParams(
        setting="canal_hotel",
        destination="garden_patio",
        method="harness",
        response="millet_lure",
        child_name="Ella",
        child_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        bird_name="Mango",
        weather="still",
        host_type="innkeeper",
        trait="gentle",
        delay=0,
        child_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        setting="seaside_inn",
        destination="breakfast_room",
        method="carrier",
        response="call_and_wait",
        child_name="Jack",
        child_gender="boy",
        helper_name="Ivy",
        helper_gender="girl",
        bird_name="Saffron",
        weather="still",
        host_type="innkeeper",
        trait="bright",
        delay=0,
        child_age=5,
        helper_age=6,
        relation="friends",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a visiting child, a cockatiel, and a holiday choice that must be safe."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--host-type", choices=["innkeeper", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.method:
        destination = DESTINATIONS[args.destination]
        method = METHODS[args.method]
        if not outing_reasonable(destination, method):
            raise StoryError(explain_combo(destination, method))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.destination is None or combo[1] == args.destination)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, destination_id, method_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    weather = args.weather or rng.choice(WEATHERS)
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    bird_name = rng.choice(BIRD_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    host_type = args.host_type or SETTINGS[setting_id].host_type
    relation = rng.choice(["siblings", "friends"])
    child_age, helper_age = rng.sample([5, 6, 7, 8], 2)
    return StoryParams(
        setting=setting_id,
        destination=destination_id,
        method=method_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        bird_name=bird_name,
        weather=weather,
        host_type=host_type,
        trait=trait,
        delay=delay,
        child_age=child_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    destination = DESTINATIONS[params.destination]
    method = METHODS[params.method]
    if not outing_reasonable(destination, method):
        raise StoryError(explain_combo(destination, method))

    setting = SETTINGS[params.setting]
    host_type = params.host_type or setting.host_type
    if host_type not in {"innkeeper", "aunt", "uncle"}:
        raise StoryError(f"(Unknown host type: {host_type})")

    custom_setting = Setting(
        id=setting.id,
        lodging=setting.lodging,
        opening=setting.opening,
        host_name=setting.host_name,
        host_type=host_type,
        host_phrase=setting.host_phrase if host_type == setting.host_type else ("their aunt" if host_type == "aunt" else "their uncle" if host_type == "uncle" else "the innkeeper"),
        tags=set(setting.tags),
    )

    world = tell(
        setting=custom_setting,
        destination=destination,
        method=method,
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        bird_name=params.bird_name,
        weather=params.weather,
        host_type=host_type,
        trait=params.trait,
        delay=params.delay,
        child_age=params.child_age,
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

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, destination, method) combos:\n")
        for setting_id, destination_id, method_id in combos:
            print(f"  {setting_id:15} {destination_id:15} {method_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name} & {p.helper_name}: {p.destination} with {p.method} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
