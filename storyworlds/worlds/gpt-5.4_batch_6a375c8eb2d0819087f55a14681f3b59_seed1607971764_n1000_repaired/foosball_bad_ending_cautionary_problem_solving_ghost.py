#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py
==================================================================================

A standalone storyworld about children playing foosball in an old game room when
a ghostly sound starts in the walls. The world models a spooky misunderstanding:
the "ghost" is really a storm problem -- loose boards, dripping water, and old
electric gear. The children can solve the mystery safely by getting a grown-up,
or make it worse by trying a reckless fix themselves.

Run it
------
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py --source hatch_chain
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py --hazard lantern
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py --response keep_playing
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py --all
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/foosball_bad_ending_cautionary_problem_solving_ghost.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    wettable: bool = False
    electric: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "caretaker": "caretaker",
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
class Venue:
    id: str
    place: str
    room_phrase: str
    storm_line: str
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
    sound: str
    cause: str
    drip_from: str
    reveal: str
    severity: int
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
class Hazard:
    id: str
    label: str
    the: str
    wet_phrase: str
    spark_line: str
    damage_word: str
    electric: bool = True
    wettable: bool = True
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
    risky: bool = False
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


def _r_shock_risk(world: World) -> list[str]:
    out: list[str] = []
    if "hazard" not in world.entities:
        return out
    hazard = world.get("hazard")
    if hazard.meters["wet"] < THRESHOLD or not hazard.electric:
        return out
    sig = ("shock_risk", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    if "hazard" not in world.entities:
        return out
    hazard = world.get("hazard")
    if hazard.meters["tugged"] < THRESHOLD and hazard.meters["ignored"] < THRESHOLD:
        return out
    if hazard.meters["wet"] < THRESHOLD:
        return out
    sig = ("spark", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hazard.meters["sparking"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__spark__")
    return out


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    if "hazard" not in world.entities:
        return out
    hazard = world.get("hazard")
    if hazard.meters["sparking"] < THRESHOLD:
        return out
    sig = ("smoke", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["smoke"] += 1
    out.append("__smoke__")
    return out


CAUSAL_RULES = [
    Rule(name="shock_risk", tag="physical", apply=_r_shock_risk),
    Rule(name="spark", tag="physical", apply=_r_spark),
    Rule(name="smoke", tag="physical", apply=_r_smoke),
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


def spooky_combo(source: Source, hazard: Hazard) -> bool:
    return source.severity > 0 and hazard.electric and hazard.wettable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def danger_score(source: Source, delay: int) -> int:
    return source.severity + delay


def is_contained(response: Response, source: Source, delay: int) -> bool:
    return response.power >= danger_score(source, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _make_wet(world: World) -> None:
    hazard = world.get("hazard")
    hazard.meters["wet"] += 1
    propagate(world, narrate=False)


def _unsafe_touch(world: World) -> None:
    hazard = world.get("hazard")
    hazard.meters["tugged"] += 1
    propagate(world, narrate=False)


def _ignore_problem(world: World) -> None:
    hazard = world.get("hazard")
    hazard.meters["ignored"] += 1
    propagate(world, narrate=False)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _make_wet(sim)
    _unsafe_touch(sim)
    return {
        "danger": sim.get("room").meters["danger"],
        "spark": sim.get("hazard").meters["sparking"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"Late in the afternoon, {a.id} and {b.id} slipped into {venue.place}. "
        f"{venue.room_phrase}"
    )
    world.say(
        f"They loved the old foosball table there. The tiny players clicked and spun, "
        f"and the little silver ball rattled like a quick secret running under the rods."
    )


def stir_storm(world: World, venue: Venue, source: Source) -> None:
    world.say(venue.storm_line)
    world.say(
        f"Then the sound came -- {source.sound}. It seemed to creep from above the room, "
        f"the kind of noise that could make two children stop in the middle of a foosball game and stare."
    )


def tempt(world: World, a: Entity, source: Source) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"Did you hear that?" {a.id} whispered. Then {a.pronoun()} tried to smile. '
        f'"Maybe it is a ghost in the walls. I can fix it myself if I find where {source.label} is coming from."'
    )


def warn(world: World, b: Entity, a: Entity, caretaker: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["spark"]:
        extra = f" {b.pronoun().capitalize()} could almost picture a bad spark jumping from {hazard.the}."
    world.say(
        f'{b.id} stepped closer to {a.id} and shook {b.pronoun("possessive")} head. '
        f'"No. We should get the {caretaker.label_word}. Water and electricity do not belong together."'
        f"{extra}"
    )


def back_down(world: World, a: Entity, b: Entity, caretaker: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} listened at last. The room still felt spooky, but {a.pronoun()} did not touch a thing. '
        f'Together they went to fetch the {caretaker.label_word}.'
    )


def defy(world: World, a: Entity, b: Entity, response: Response) -> None:
    a.memes["defiance"] += 1
    if response.id == "keep_playing":
        world.say(
            f'"It is probably nothing," {a.id} said, though {a.pronoun("possessive")} voice had turned small. '
            f'"Let\'s just keep playing foosball."'
        )
    else:
        world.say(
            f'"I can handle it," {a.id} said, and before {b.id} could stop {a.pronoun("object")}, '
            f'{a.pronoun()} hurried toward the dark corner of the room.'
        )


def investigate(world: World, a: Entity, source: Source, hazard: Hazard, response: Response) -> None:
    _make_wet(world)
    if response.id == "poke_with_broom":
        _unsafe_touch(world)
        world.say(
            f"{a.id} grabbed an old broom and poked toward the ceiling where {source.label} seemed loudest. "
            f"A cold drip ran down the handle. Below, {hazard.the} was already {hazard.wet_phrase}."
        )
    elif response.id == "pull_cord":
        _unsafe_touch(world)
        world.say(
            f"{a.id} reached for a dangling cord and gave it a hard pull, trying to stop the ghostly sound. "
            f"But the cord led straight to {hazard.the}, which was {hazard.wet_phrase}."
        )
    elif response.id == "keep_playing":
        _ignore_problem(world)
        world.say(
            f"They turned back to the foosball table, pretending not to hear the sound. "
            f"Above them the storm kept working, and {hazard.the} grew {hazard.wet_phrase}."
        )
    else:
        world.say(
            f"{a.id} edged nearer the noise, and the room felt colder with every step."
        )


def spark_beat(world: World, hazard: Hazard) -> None:
    if world.get("hazard").meters["sparking"] >= THRESHOLD:
        world.say(
            f"Then it happened. {hazard.spark_line} and a sharp blue spark snapped in the dark."
        )
    if world.get("room").meters["smoke"] >= THRESHOLD:
        world.say("A bitter smell rose at once, and thin gray smoke began to spread across the ceiling.")


def rescue(world: World, caretaker: Entity, response: Response, source: Source, hazard: Hazard) -> None:
    world.get("hazard").meters["sparking"] = 0.0
    world.get("room").meters["smoke"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"The {caretaker.label_word} came fast, carrying a flashlight and a dry towel. "
        f"{caretaker.pronoun().capitalize()} {response.text.replace('{hazard}', hazard.label).replace('{source}', source.label)}."
    )
    world.say(
        f"In the bright beam, the ghost shrank into an ordinary problem: {source.reveal}. "
        f"The room still smelled stormy, but it was safe again."
    )


def lesson(world: World, caretaker: Entity, a: Entity, b: Entity, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f'The {caretaker.label_word} knelt beside them. "Old rooms can make strange sounds," '
        f'{caretaker.pronoun()} said softly. "But when water creeps near {hazard.label}, children must get a grown-up, not experiment."'
    )
    world.say(
        f"{a.id} and {b.id} nodded. The mystery had felt like a ghost, but the real trouble had been a storm and an unsafe machine."
    )


def safe_end(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Before they left, the {world.facts['caretaker'].label_word} set a lantern on a shelf and opened the door wide to the clean evening air."
    )
    world.say(
        f"The foosball table stood quiet under the steady light. {a.id} rolled the ball once across the field, "
        f"and this time the clicking rods sounded cheerful instead of haunted."
    )


def rescue_fail(world: World, caretaker: Entity, response: Response, source: Source, hazard: Hazard) -> None:
    world.get("room").meters["smoke"] += 1
    world.get("room").meters["closed"] += 1
    world.say(
        f"The {caretaker.label_word} came running, but {response.fail.replace('{hazard}', hazard.label).replace('{source}', source.label)}."
    )
    world.say(
        f"Smoke curled thicker around the foosball table, and the old room had to be emptied at once."
    )


def escape_and_loss(world: World, caretaker: Entity, a: Entity, b: Entity, venue: Venue) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"The {caretaker.label_word} rushed {a.id} and {b.id} outside into the wet dusk. "
        f"Behind them, {venue.place} glowed with flashlight beams and shouting grown-ups."
    )
    world.say(
        "No one was badly hurt, but the game room had to be closed for a long time. "
        "The foosball table sat behind a locked door, dark and silent."
    )


def grim_lesson(world: World, caretaker: Entity, a: Entity, b: Entity, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'The {caretaker.label_word} wrapped a blanket around their shoulders and said, '
        f'"A spooky noise is never a reason to touch {hazard.label} or ignore a leak. The safe way is to tell a grown-up first."'
    )
    world.say(
        f"{a.id} looked back at the shut door and knew the worst part was not the ghostly sound at all. "
        f"It was the choice to solve a dangerous problem the wrong way."
    )


def tell(
    venue: Venue,
    source: Source,
    hazard: Hazard,
    response: Response,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    cautioner: str = "Eli",
    cautioner_gender: str = "boy",
    caretaker_type: str = "caretaker",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        role="caretaker",
        label="the caretaker",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="hazard", type="machine", label=hazard.label, electric=hazard.electric, wettable=hazard.wettable))
    world.add(Entity(id="table", type="game", label="foosball table"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = 5.0
    b.memes["caution"] = initial_caution(trait)
    room.meters["danger"] = 0.0
    room.meters["smoke"] = 0.0
    room.meters["closed"] = 0.0
    world.get("hazard").meters["wet"] = 0.0
    world.get("hazard").meters["tugged"] = 0.0
    world.get("hazard").meters["ignored"] = 0.0
    world.get("hazard").meters["sparking"] = 0.0

    play_setup(world, a, b, venue)
    stir_storm(world, venue, source)

    world.para()
    tempt(world, a, source)
    warn(world, b, a, caretaker, hazard)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, caretaker)
        world.para()
        _make_wet(world)
        rescue(world, caretaker, RESPONSES["get_caretaker"], source, hazard)
        lesson(world, caretaker, a, b, hazard)
        world.para()
        safe_end(world, a, b, venue)
        contained = True
        severity = 0
    else:
        defy(world, a, b, response)
        world.para()
        investigate(world, a, source, hazard, response)
        spark_beat(world, hazard)
        severity = danger_score(source, delay)
        world.get("hazard").meters["severity"] = float(severity)
        contained = is_contained(response, source, delay)
        world.para()
        if contained:
            rescue(world, caretaker, response, source, hazard)
            lesson(world, caretaker, a, b, hazard)
            world.para()
            safe_end(world, a, b, venue)
        else:
            rescue_fail(world, caretaker, response, source, hazard)
            escape_and_loss(world, caretaker, a, b, venue)
            grim_lesson(world, caretaker, a, b, hazard)

    outcome = "averted" if averted else ("contained" if contained else "closed")
    world.facts.update(
        venue=venue,
        source=source,
        hazard_cfg=hazard,
        hazard=world.get("hazard"),
        response=response,
        instigator=a,
        cautioner=b,
        caretaker=caretaker,
        outcome=outcome,
        severity=severity,
        delay=delay,
        spark=world.get("hazard").meters["sparking"] >= THRESHOLD,
        room_closed=world.get("room").meters["closed"] >= THRESHOLD or outcome == "closed",
    )
    return world


VENUES = {
    "boathouse": Venue(
        id="boathouse",
        place="the old boathouse club",
        room_phrase="Down the hall was a game room with peeling green paint, a tall window, and a foosball table that everyone said had been there forever.",
        storm_line="Outside, wind dragged across the lake and pushed cold rain against the boards.",
        tags={"storm", "club"},
    ),
    "parish_hall": Venue(
        id="parish_hall",
        place="the old parish hall",
        room_phrase="At the back stood a narrow game room with dusty trophies, long curtains, and a foosball table under a buzzing light.",
        storm_line="Outside, the evening storm drummed on the roof and made the gutters groan.",
        tags={"storm", "hall"},
    ),
    "camp_lodge": Venue(
        id="camp_lodge",
        place="the camp lodge",
        room_phrase="Beside the main stairs was a little rec room with knotty walls, a rack of board games, and a scarred foosball table by the window.",
        storm_line="Outside, pine trees hissed in the wind and rain tapped sharply on the glass.",
        tags={"storm", "camp"},
    ),
}

SOURCES = {
    "hatch_chain": Source(
        id="hatch_chain",
        label="the attic hatch chain",
        sound="a slow clink-clink, then a scrape above their heads",
        cause="wind shaking a chain on the attic hatch",
        drip_from="the hatch seam",
        reveal="wind had been shaking the attic hatch chain while rain leaked through the seam",
        severity=2,
        tags={"ghost", "wind"},
    ),
    "loose_sign": Source(
        id="loose_sign",
        label="the loose roof sign",
        sound="a hollow thump and a long moan inside the rafters",
        cause="a loose sign board bumping in the storm",
        drip_from="a crack near the rafters",
        reveal="a loose sign board had been thumping outside while rain slipped through a crack above the wall",
        severity=3,
        tags={"ghost", "roof"},
    ),
    "vent_flap": Source(
        id="vent_flap",
        label="the old vent flap",
        sound="a papery flap-flap, followed by a whistle like someone breathing",
        cause="an old vent flap snapping in the wind",
        drip_from="the vent edge",
        reveal="an old vent flap had been snapping in the storm, and water had crept in along the vent edge",
        severity=2,
        tags={"ghost", "vent"},
    ),
}

HAZARDS = {
    "power_strip": Hazard(
        id="power_strip",
        label="power strip",
        the="the power strip",
        wet_phrase="beaded with rainwater",
        spark_line="The power strip spat orange light",
        damage_word="smoke",
        electric=True,
        wettable=True,
        tags={"electricity", "water"},
    ),
    "scoreboard": Hazard(
        id="scoreboard",
        label="scoreboard box",
        the="the scoreboard box",
        wet_phrase="dark with dripping water",
        spark_line="The scoreboard box snapped and flashed",
        damage_word="smoke",
        electric=True,
        wettable=True,
        tags={"electricity", "water"},
    ),
    "lantern": Hazard(
        id="lantern",
        label="wall lantern",
        the="the wall lantern",
        wet_phrase="spotted with cold drips",
        spark_line="The wall lantern crackled hard",
        damage_word="smoke",
        electric=True,
        wettable=True,
        tags={"electricity", "water", "light"},
    ),
}

RESPONSES = {
    "get_caretaker": Response(
        id="get_caretaker",
        sense=3,
        power=4,
        text="switched off the room's power, moved the dripping {hazard} away from the leak, and checked the noisy place with a flashlight",
        fail="switched off the power, but the storm damage was already spreading through the wall",
        qa_text="switched off the power and checked the leak with a flashlight",
        risky=False,
        tags={"adult_help", "electricity"},
    ),
    "unplug_then_tell": Response(
        id="unplug_then_tell",
        sense=2,
        power=3,
        text="pulled the main plug with a dry cloth, then had them step back while the leak was traced",
        fail="tried to pull the main plug with a dry cloth, but the trouble had already spread too far",
        qa_text="used a dry cloth to pull the main plug and then checked the leak",
        risky=False,
        tags={"adult_help", "electricity"},
    ),
    "poke_with_broom": Response(
        id="poke_with_broom",
        sense=1,
        power=1,
        text="poked at the ceiling with a broom while calling for help",
        fail="found the children had already poked at the leak and the spark had spread smoke through the room",
        qa_text="poked at the ceiling with a broom",
        risky=True,
        tags={"bad_fix", "electricity"},
    ),
    "pull_cord": Response(
        id="pull_cord",
        sense=1,
        power=1,
        text="yanked on the wet cord",
        fail="found that the wet cord had already been yanked and the room was filling with smoke",
        qa_text="pulled the wet cord",
        risky=True,
        tags={"bad_fix", "electricity"},
    ),
    "keep_playing": Response(
        id="keep_playing",
        sense=0,
        power=0,
        text="kept playing anyway",
        fail="found that the leak had been ignored while the danger quietly grew",
        qa_text="ignored the leak and kept playing",
        risky=True,
        tags={"ignore_problem", "electricity"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna", "Lucy", "June"]
BOY_NAMES = ["Eli", "Ben", "Sam", "Theo", "Max", "Noah", "Finn", "Jack"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "braveish"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for venue_id in VENUES:
        for source_id, source in SOURCES.items():
            for hazard_id, hazard in HAZARDS.items():
                if spooky_combo(source, hazard):
                    combos.append((venue_id, source_id, hazard_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    source: str
    hazard: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    caretaker: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
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
    "ghost": [
        (
            "Can a spooky sound have an ordinary cause?",
            "Yes. Wind, loose boards, pipes, and dripping water can make eerie sounds, even when no ghost is there.",
        )
    ],
    "electricity": [
        (
            "Why are water and electricity dangerous together?",
            "Water can help electricity travel where it should not go. That can cause shocks, sparks, or fire, so children should get a grown-up right away.",
        )
    ],
    "adult_help": [
        (
            "What should a child do if a machine is wet or sparking?",
            "Step back and tell a grown-up immediately. A grown-up can turn off the power and fix the problem safely.",
        )
    ],
    "light": [
        (
            "Why is a flashlight useful in a dark room?",
            "A flashlight lets you see clearly without touching dangerous things. Good light helps people solve a problem more safely.",
        )
    ],
    "storm": [
        (
            "How can a storm make a house sound spooky?",
            "Wind can bang, whistle, flap, and rattle around boards and vents. In the dark, those noises can sound much stranger than they really are.",
        )
    ],
    "bad_fix": [
        (
            "Why is poking or pulling a wet electric thing a bad idea?",
            "Because it can make the danger worse right away. Wet electric things can spark, shock, or start smoking when someone disturbs them.",
        )
    ],
    "ignore_problem": [
        (
            "Is ignoring a dangerous problem a safe choice?",
            "No. A problem that is leaking, sparking, or getting stranger usually grows worse if nobody tells a grown-up.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "storm", "electricity", "adult_help", "light", "bad_fix", "ignore_problem"]


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
    a, b = f["instigator"], f["cautioner"]
    venue, source, hazard = f["venue"], f["source"], f["hazard_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a ghost-story-style cautionary tale for a 3-to-5-year-old about two children playing foosball in {venue.place} '
        f'when they hear a spooky noise from {source.label}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {a.id} wants to solve the ghostly sound alone, but {b.id} insists on getting the caretaker because {hazard.label} might be wet.",
            'Write a spooky-but-safe story where the mystery is solved by careful thinking and getting adult help instead of touching dangerous equipment.',
        ]
    if outcome == "closed":
        return [
            base,
            f"Tell a cautionary story where {a.id} ignores a warning and tries to solve the spooky problem near {hazard.the}, and the game room ends up closed.",
            'Write a ghostly bad-ending story that teaches children to tell a grown-up when water and electricity meet.',
        ]
    return [
        base,
        f"Tell a spooky problem-solving story where a grown-up discovers the ghostly noise is really storm damage near {hazard.the}.",
        'Write a child-facing mystery where the scary sound has a real cause and the safe solution is to get adult help fast.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, caretaker = f["instigator"], f["cautioner"], f["caretaker"]
    venue, source, hazard, response = f["venue"], f["source"], f["hazard_cfg"], f["response"]
    pair = pair_noun(a, b, a.attrs.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and the caretaker at {venue.place}. They were playing foosball when the mystery began.",
        ),
        (
            "What made the room feel haunted?",
            f"The children heard {source.sound}, so the room suddenly felt like a ghost story. The sound came right in the middle of their foosball game, which made it even more startling.",
        ),
        (
            f"Why did {b.id} want to get the caretaker?",
            f"{b.id} knew the problem might be dangerous because water was creeping near {hazard.the}. {b.pronoun().capitalize()} understood that electricity and rainwater do not belong together.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} stopped trying to solve the mystery alone and went to fetch the caretaker instead. That choice kept the spooky problem from turning into a real accident.",
            )
        )
        qa.append(
            (
                "What was the ghost really?",
                f"It was not a ghost at all. {source.reveal}.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "How was the problem solved?",
                f"The caretaker {response.qa_text.replace('{hazard}', hazard.label).replace('{source}', source.label)}. That worked because the real problem was storm damage, not a ghost.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                "The room became safe again, and the children understood what had changed. The same foosball table that had seemed haunted now looked ordinary under steady light.",
            )
        )
    else:
        qa.append(
            (
                "Why did the ending turn bad?",
                f"The children tried to handle the spooky problem the wrong way near {hazard.the}, and the danger grew into smoke and a shutdown. The bad ending came from treating a risky machine like part of the game instead of telling a grown-up.",
            )
        )
        qa.append(
            (
                "What happened to the game room?",
                "It had to be closed after the smoke and damage. No one was badly hurt, but the children lost the room where they had been playing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["source"].tags) | set(f["hazard_cfg"].tags)
    tags |= set(f["response"].tags)
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
        flags = [n for n, on in (("wettable", e.wettable), ("electric", e.electric)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="boathouse",
        source="hatch_chain",
        hazard="power_strip",
        response="get_caretaker",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Eli",
        cautioner_gender="boy",
        caretaker="caretaker",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        venue="camp_lodge",
        source="vent_flap",
        hazard="lantern",
        response="unplug_then_tell",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Lucy",
        cautioner_gender="girl",
        caretaker="caretaker",
        trait="steady",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        venue="parish_hall",
        source="loose_sign",
        hazard="scoreboard",
        response="poke_with_broom",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Max",
        cautioner_gender="boy",
        caretaker="caretaker",
        trait="cautious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        venue="boathouse",
        source="loose_sign",
        hazard="power_strip",
        response="get_caretaker",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        caretaker="caretaker",
        trait="sensible",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
    ),
]


def explain_rejection(source: Source, hazard: Hazard) -> str:
    if not hazard.electric:
        return f"(No story: {hazard.the} is not electric, so the spooky leak would not create the cautionary danger this world needs.)"
    if not hazard.wettable:
        return f"(No story: water could not realistically threaten {hazard.the}, so there is no grounded problem to solve.)"
    return f"(No story: {source.label} and {hazard.label} do not form a reasonable spooky hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], SOURCES[params.source], params.delay)
    return "contained" if contained else "closed"


ASP_RULES = r"""
hazardous(S, H) :- source(S), hazard(H), severity(S, V), V > 0, electric(H), wettable(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Vn, S, H) :- venue(Vn), source(S), hazard(H), hazardous(S, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

danger(V + D) :- chosen_source(S), severity(S, V), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), danger(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(closed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("severity", source_id, source.severity))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        if hazard.electric:
            lines.append(asp.fact("electric", hazard_id))
        if hazard.wettable:
            lines.append(asp.fact("wettable", hazard_id))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
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


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="SMOKE TEST")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a ghostly foosball mystery with a safe solution or a cautionary bad ending."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--caretaker", choices=["caretaker", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.hazard:
        source, hazard = SOURCES[args.source], HAZARDS[args.hazard]
        if not spooky_combo(source, hazard):
            raise StoryError(explain_rejection(source, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.source is None or combo[1] == args.source)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue, source, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    caretaker = args.caretaker or "caretaker"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        venue=venue,
        source=source,
        hazard=hazard,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        caretaker=caretaker,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.caretaker not in {"caretaker", "mother", "father"}:
        raise StoryError(f"(Unknown caretaker: {params.caretaker})")

    source = SOURCES[params.source]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    if not spooky_combo(source, hazard):
        raise StoryError(explain_rejection(source, hazard))
    world = tell(
        venue=VENUES[params.venue],
        source=source,
        hazard=hazard,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        caretaker_type=params.caretaker,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, source, hazard) combos:\n")
        for venue, source, hazard in combos:
            print(f"  {venue:12} {source:12} {hazard}")
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
                f"### {p.instigator} & {p.cautioner}: {p.source} near {p.hazard} "
                f"({p.venue}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
