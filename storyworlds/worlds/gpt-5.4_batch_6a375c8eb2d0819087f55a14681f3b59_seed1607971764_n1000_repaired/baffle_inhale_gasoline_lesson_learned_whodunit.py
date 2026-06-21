#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py
==============================================================================

A standalone story world for a tiny child-facing whodunit:
two junior detectives are baffled by a sharp smell, one child is tempted to get
too close and inhale for a clue, and a calm grown-up helps solve the mystery and
teach the lesson that gasoline fumes are not for sniffing.

Run it
------
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py --place garage --source gas_can --cause tipped_can
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py --cause cracked_hose --source gas_can
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py --response sniff_again
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/baffle_inhale_gasoline_lesson_learned_whodunit.py --verify
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
CURIOSITY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "patient", "sensible"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Place:
    id: str
    label: str
    scene: str
    door_text: str
    fits: set[str] = field(default_factory=set)
    enclosed: int = 1
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
    phrase: str
    vessel: str
    clue_spot: str
    volatility: int
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
class Cause:
    id: str
    label: str
    reveal: str
    clue: str
    source_types: set[str] = field(default_factory=set)
    spill: int = 1
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
    power: int
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"place": place}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"sniffer", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_fumes(world: World) -> list[str]:
    source = world.get("source")
    room = world.get("room")
    if source.meters["leaking"] < THRESHOLD:
        return []
    sig = ("fumes", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["odor"] += 1
    room.meters["danger"] += source.meters["severity"]
    for kid in world.kids():
        kid.memes["unease"] += 1
    return ["__fumes__"]


def _r_inhale(world: World) -> list[str]:
    sniffer = world.get("sniffer")
    room = world.get("room")
    if sniffer.meters["inhaled"] < THRESHOLD or room.meters["odor"] < THRESHOLD:
        return []
    sig = ("dizzy", sniffer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sniffer.meters["dizzy"] += 1
    sniffer.meters["cough"] += 1
    sniffer.memes["fear"] += 1
    world.get("partner").memes["fear"] += 1
    return ["__inhale__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="fumes", tag="physical", apply=_r_fumes),
    Rule(name="inhale", tag="physical", apply=_r_inhale),
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


def cause_fits(source: Source, cause: Cause) -> bool:
    return source.id in cause.source_types


def place_fits(place: Place, source: Source) -> bool:
    return source.id in place.fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not place_fits(place, source):
                continue
            for cause_id, cause in CAUSES.items():
                if cause_fits(source, cause):
                    combos.append((place_id, source_id, cause_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(place: Place, source: Source, cause: Cause) -> int:
    return place.enclosed + source.volatility + cause.spill


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, sniffer_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > sniffer_age
    authority = initial_caution(trait) + 1.0 + (4.0 if partner_older else 0.0)
    return partner_older and authority > CURIOSITY_INIT


def predict_inhale(world: World) -> dict:
    sim = world.copy()
    sim.get("sniffer").meters["inhaled"] += 1
    propagate(sim, narrate=False)
    return {
        "dizzy": sim.get("sniffer").meters["dizzy"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def open_case(world: World, sniffer: Entity, partner: Entity, place: Place) -> None:
    for kid in (sniffer, partner):
        kid.memes["joy"] += 1
    world.say(
        f"On a still afternoon, {sniffer.id} and {partner.id} padded toward {place.label} "
        f"as if it were a secret detective office. {place.scene}"
    )
    world.say(
        f'{sniffer.id} tapped an imaginary badge and whispered, "Detective work starts now."'
    )


def discover_smell(world: World, sniffer: Entity, partner: Entity, place: Place) -> None:
    room = world.get("room")
    source = world.get("source")
    source.meters["leaking"] = 1.0
    source.meters["severity"] = float(world.facts["severity"])
    propagate(world, narrate=False)
    room.memes["mystery"] = 1.0
    world.say(
        f"Then both children stopped. A sharp smell drifted out through {place.door_text}, "
        f"and it was enough to baffle the two junior detectives."
    )
    world.say(
        f'"Something in there smells like gasoline," {partner.id} said, wrinkling '
        f'{partner.pronoun("possessive")} nose.'
    )


def gather_clues(world: World, cause: Cause, source: Source) -> None:
    world.say(
        f"They peered from the doorway and spotted a clue: {cause.clue} near {source.clue_spot}."
    )
    world.say("The mystery no longer felt pretend. It felt real, and that made the room seem smaller.")


def tempt_sniff(world: World, sniffer: Entity) -> None:
    sniffer.memes["curiosity"] += 1
    world.say(
        f'"Maybe I should get closer and inhale just a tiny sniff," {sniffer.id} said. '
        f'{sniffer.pronoun().capitalize()} wanted to solve the case first.'
    )


def warn(world: World, partner: Entity, sniffer: Entity, adult: Entity) -> None:
    pred = predict_inhale(world)
    partner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_dizzy"] = pred["dizzy"]
    extra = ""
    if partner.memes["caution"] >= 6:
        extra = f" {partner.pronoun().capitalize()} stood very still, already sure the clue was dangerous."
    world.say(
        f'"No," {partner.id} said. "We should not inhale that smell. {adult.label_word.capitalize()} '
        f'once told us that gasoline fumes can make people feel sick."{extra}'
    )


def back_down(world: World, sniffer: Entity, partner: Entity, adult: Entity) -> None:
    sniffer.memes["relief"] += 1
    partner.memes["relief"] += 1
    sniffer.memes["curiosity"] = 0.0
    world.say(
        f'{sniffer.id} looked at the dark doorway, then at {partner.id}, and stepped back. '
        f'"You\'re right," {sniffer.pronoun()} said. "This is a grown-up mystery."'
    )
    world.say(
        f"Together they hurried to find {adult.label_word} instead of chasing the smell."
    )


def lean_close(world: World, sniffer: Entity, partner: Entity) -> None:
    sniffer.meters["inhaled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the mystery tugged harder than good sense. {sniffer.id} crept one step closer and "
        f"did inhale a breath before {partner.id} could stop {sniffer.pronoun('object')}."
    )
    world.say(
        f"At once, {sniffer.pronoun()} coughed and blinked hard. The clue had turned into a mistake."
    )


def alarm(world: World, partner: Entity, adult: Entity, sniffer: Entity) -> None:
    if sniffer.meters["dizzy"] >= THRESHOLD:
        world.say(
            f'"{adult.label_word.upper()}!" {partner.id} shouted. "{sniffer.id} feels funny, and something smells like gasoline!"'
        )
    else:
        world.say(
            f'"{adult.label_word.upper()}!" {partner.id} shouted. "Please come help us with the smell!"'
        )


def solve_case(world: World, adult: Entity, source: Source, cause: Cause, response: Response) -> None:
    room = world.get("room")
    source_ent = world.get("source")
    room.meters["danger"] = 0.0
    room.meters["odor"] = 0.0
    source_ent.meters["leaking"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came quickly, kept the children back, and {response.text}."
    )
    world.say(
        f"Then {adult.pronoun()} studied the clue and solved the case: {cause.reveal} on {source.phrase}."
    )


def comfort(world: World, adult: Entity, sniffer: Entity, partner: Entity) -> None:
    sniffer.memes["relief"] += 1
    partner.memes["relief"] += 1
    sniffer.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    if sniffer.meters["dizzy"] >= THRESHOLD:
        world.say(
            f"{adult.label_word.capitalize()} sat {sniffer.id} on the porch steps until the fresh air helped. "
            f"{sniffer.id} felt better after a little while, but the scare stayed with both children."
        )
    else:
        world.say(
            f"Fresh air blew through the doorway, and the sharp smell slowly faded. Both children let out the breath they had been holding."
        )
    world.say(
        f'"A real detective does not sniff dangerous clues," {adult.label_word} said gently. '
        f'"If you smell gasoline, step back and tell a grown-up right away."'
    )


def safer_ending(world: World, sniffer: Entity, partner: Entity, adult: Entity) -> None:
    for kid in (sniffer, partner):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {adult.label_word} brought them a little notebook and a stubby pencil for future cases."
    )
    world.say(
        f'"What do detectives use now?" {adult.pronoun()} asked with a smile.'
    )
    world.say(
        f'"Eyes, ears, and asking for help," {partner.id} answered.'
    )
    world.say(
        f'{sniffer.id} nodded and wrote their first rule in big letters: "Never sniff gasoline." '
        f"The mystery was solved, and the lesson stayed solved too."
    )


def tell(
    place: Place,
    source: Source,
    cause: Cause,
    response: Response,
    *,
    sniffer_name: str = "Milo",
    sniffer_gender: str = "boy",
    partner_name: str = "Nora",
    partner_gender: str = "girl",
    partner_trait: str = "careful",
    adult_type: str = "mother",
    relation: str = "siblings",
    sniffer_age: int = 5,
    partner_age: int = 7,
) -> World:
    world = World(place)
    sniffer = world.add(Entity(
        id=sniffer_name,
        kind="character",
        type=sniffer_gender,
        role="sniffer",
        age=sniffer_age,
        traits=["curious"],
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        traits=[partner_trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(id="source", type="source", label=source.label))
    sniffer.memes["curiosity"] = CURIOSITY_INIT
    partner.memes["caution"] = initial_caution(partner_trait)
    world.facts.update(
        sniffer=sniffer,
        partner=partner,
        adult=adult,
        source_cfg=source,
        cause=cause,
        response=response,
        relation=relation,
        severity=severity_of(place, source, cause),
    )

    open_case(world, sniffer, partner, place)
    discover_smell(world, sniffer, partner, place)
    gather_clues(world, cause, source)

    world.para()
    tempt_sniff(world, sniffer)
    warn(world, partner, sniffer, adult)

    averted = would_avert(relation, sniffer_age, partner_age, partner_trait)
    if averted:
        back_down(world, sniffer, partner, adult)
    else:
        lean_close(world, sniffer, partner)
    alarm(world, partner, adult, sniffer)

    world.para()
    solve_case(world, adult, source, cause, response)
    comfort(world, adult, sniffer, partner)

    world.para()
    safer_ending(world, sniffer, partner, adult)

    world.facts.update(
        averted=averted,
        outcome="averted" if averted else "inhaled",
        inhaled=sniffer.meters["inhaled"] >= THRESHOLD,
        dizzy=sniffer.meters["dizzy"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garage": Place(
        id="garage",
        label="the garage",
        scene="The window was dusty, the shelves were full of flowerpots and boxes, and every corner looked ready to hide a clue.",
        door_text="the half-open garage door",
        fits={"gas_can", "mower_tank"},
        enclosed=2,
        tags={"garage"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        scene="Rakes leaned in one corner, seed packets slept in a tin, and the narrow doorway made the whole place feel like a puzzle box.",
        door_text="the crooked shed door",
        fits={"gas_can", "mower_tank"},
        enclosed=2,
        tags={"shed"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the boathouse",
        scene="Ropes hung from hooks, life jackets bumped the wall, and the boards gave little creaks under careful feet.",
        door_text="the open boathouse door",
        fits={"gas_can", "boat_tank"},
        enclosed=1,
        tags={"boathouse"},
    ),
}

SOURCES = {
    "gas_can": Source(
        id="gas_can",
        label="gas can",
        phrase="the red gas can",
        vessel="can",
        clue_spot="the base of the shelf",
        volatility=2,
        tags={"gasoline", "container"},
    ),
    "mower_tank": Source(
        id="mower_tank",
        label="lawn mower tank",
        phrase="the lawn mower",
        vessel="tank",
        clue_spot="the wheel of the mower",
        volatility=2,
        tags={"gasoline", "mower"},
    ),
    "boat_tank": Source(
        id="boat_tank",
        label="small boat tank",
        phrase="the little boat motor",
        vessel="tank",
        clue_spot="the wooden floorboards",
        volatility=2,
        tags={"gasoline", "boat"},
    ),
}

CAUSES = {
    "loose_cap": Cause(
        id="loose_cap",
        label="loose cap",
        reveal="someone had left the cap twisted only halfway on",
        clue="a shiny wet ring and a cap sitting crooked",
        source_types={"gas_can", "boat_tank"},
        spill=1,
        tags={"cap", "spill"},
    ),
    "tipped_can": Cause(
        id="tipped_can",
        label="tipped can",
        reveal="the can had been knocked onto its side behind a box",
        clue="a thin trail of liquid leading under a box",
        source_types={"gas_can"},
        spill=2,
        tags={"spill"},
    ),
    "cracked_hose": Cause(
        id="cracked_hose",
        label="cracked hose",
        reveal="a tiny crack in the hose had been dripping fuel",
        clue="small drops shining along a rubber line",
        source_types={"mower_tank", "boat_tank"},
        spill=1,
        tags={"hose", "leak"},
    ),
}

RESPONSES = {
    "ventilate_and_help": Response(
        id="ventilate_and_help",
        sense=3,
        power=3,
        text="opened the wide door, moved everyone outside, and checked the spill from a safe distance",
        qa_text="opened the doors, moved the children back, and handled the spill safely",
        tags={"ventilate", "adult_help"},
    ),
    "close_area_and_call": Response(
        id="close_area_and_call",
        sense=3,
        power=3,
        text="kept everyone outside, blocked the doorway, and called for proper help before touching anything",
        qa_text="kept the area closed off and called for help from a safe place",
        tags={"call_help", "adult_help"},
    ),
    "sniff_again": Response(
        id="sniff_again",
        sense=1,
        power=0,
        text="leaned in for another smell",
        qa_text="leaned in for another smell",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Zoe", "Ava", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Jack"]
TRAITS = ["careful", "cautious", "patient", "sensible", "curious", "bold"]


@dataclass
class StoryParams:
    place: str
    source: str
    cause: str
    response: str
    sniffer: str
    sniffer_gender: str
    partner: str
    partner_gender: str
    partner_trait: str
    adult: str
    relation: str = "siblings"
    sniffer_age: int = 5
    partner_age: int = 7
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


def pair_noun(sniffer: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if sniffer.type == "boy" and partner.type == "boy":
            return "two brothers"
        if sniffer.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sniffer = f["sniffer"]
    partner = f["partner"]
    place = f["place"]
    source = f["source_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short whodunit for a 3-to-5-year-old where two children are baffled by a smell of gasoline in {place.label}, and one child wisely stops the other before anyone tries to inhale it.',
            f"Tell a gentle detective story where {sniffer.id} and {partner.id} notice a dangerous clue, call a grown-up, and learn a safety lesson.",
            'Write a "Lesson Learned" mystery with child detectives, a real clue, a calm grown-up reveal, and the exact words "baffle", "inhale", and "gasoline".',
        ]
    return [
        f'Write a child-friendly whodunit where two junior detectives are baffled by a smell of gasoline in {place.label}, and one child makes the mistake of trying to inhale the clue.',
        f"Tell a small mystery where {sniffer.id} wants to solve the case alone, but learns that dangerous smells are for grown-ups to handle.",
        f'Write a "Lesson Learned" story in whodunit style using the words "baffle", "inhale", and "gasoline", ending with a safe rule for next time.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sniffer = f["sniffer"]
    partner = f["partner"]
    adult = f["adult"]
    place = f["place"]
    source = f["source_cfg"]
    cause = f["cause"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(sniffer, partner, relation)
    pw = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {sniffer.id} and {partner.id}, who were pretending to be detectives. The grown-up who helped was their {pw}.",
        ),
        (
            "What mystery did they find?",
            f"They found a sharp gasoline smell coming from {place.label}. A clue near {source.phrase} made the pretend case turn into a real safety problem.",
        ),
        (
            "Why were the children baffled at first?",
            f"They did not expect a dangerous smell in the middle of their detective game. That surprise is what made the mystery baffle them before they understood the clue.",
        ),
        (
            "What clue helped solve the mystery?",
            f"They noticed {cause.clue}. Later, the grown-up used that clue to figure out that {cause.reveal}.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {partner.id} stop {sniffer.id} from getting closer?",
                f"{partner.id} remembered that gasoline fumes can make people feel sick, so {partner.pronoun()} warned {sniffer.id} not to inhale the smell. That warning changed the case from a risky mistake into a safe call for help.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {sniffer.id} tried to inhale the clue?",
                f"{sniffer.id} coughed and felt dizzy right away. The smell stopped being a mystery and became proof that the fumes were dangerous.",
            )
        )
    qa.append(
        (
            f"How did the {pw} solve the problem?",
            f"The {pw} {response.qa_text}. Then {adult.pronoun()} studied the clue and explained that {cause.reveal} on {source.phrase}.",
        )
    )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned that real detectives do not sniff dangerous clues. If they ever smell gasoline again, they should step back and tell a grown-up right away.",
        )
    )
    return qa


KNOWLEDGE = {
    "gasoline": [
        (
            "What is gasoline?",
            "Gasoline is a fuel that helps some engines run. It has a strong smell, and children should stay away from it.",
        )
    ],
    "fumes": [
        (
            "Why is it unsafe to inhale gasoline fumes?",
            "Gasoline fumes can make your head hurt, make you cough, or make you feel sick and dizzy. That is why you should move away and tell a grown-up.",
        )
    ],
    "ventilate": [
        (
            "Why do grown-ups open doors or windows when a strong fuel smell is around?",
            "Fresh air helps push the fumes out and makes the area safer. A grown-up also keeps people back while fixing the real problem.",
        )
    ],
    "call_help": [
        (
            "When should you call a grown-up for help?",
            "You should call a grown-up when something smells dangerous, spills, breaks, or feels unsafe. Asking for help quickly is the smart thing to do.",
        )
    ],
    "mower": [
        (
            "What is a lawn mower?",
            "A lawn mower is a machine that cuts grass. Some lawn mowers use gasoline, so only grown-ups should handle their fuel parts.",
        )
    ],
    "boat": [
        (
            "What is a boat motor?",
            "A boat motor helps push a boat through the water. Some small motors use fuel, and that fuel should be handled carefully by grown-ups.",
        )
    ],
    "cap": [
        (
            "Why does a fuel cap need to stay on tight?",
            "A tight cap helps keep fuel from spilling and keeps fumes from drifting out. If the cap is loose, the smell can spread quickly.",
        )
    ],
    "hose": [
        (
            "Why is a cracked fuel hose a problem?",
            "A cracked hose can let fuel drip out little by little. Even a small leak can make a strong smell and create danger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gasoline", "fumes", "ventilate", "call_help", "mower", "boat", "cap", "hose"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gasoline", "fumes"}
    tags |= set(f["response"].tags)
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["cause"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garage",
        source="gas_can",
        cause="tipped_can",
        response="ventilate_and_help",
        sniffer="Milo",
        sniffer_gender="boy",
        partner="Nora",
        partner_gender="girl",
        partner_trait="careful",
        adult="mother",
        relation="siblings",
        sniffer_age=5,
        partner_age=7,
    ),
    StoryParams(
        place="shed",
        source="mower_tank",
        cause="cracked_hose",
        response="close_area_and_call",
        sniffer="Lucy",
        sniffer_gender="girl",
        partner="Ben",
        partner_gender="boy",
        partner_trait="cautious",
        adult="father",
        relation="friends",
        sniffer_age=6,
        partner_age=6,
    ),
    StoryParams(
        place="boathouse",
        source="boat_tank",
        cause="loose_cap",
        response="ventilate_and_help",
        sniffer="Sam",
        sniffer_gender="boy",
        partner="Maya",
        partner_gender="girl",
        partner_trait="patient",
        adult="uncle",
        relation="siblings",
        sniffer_age=4,
        partner_age=8,
    ),
    StoryParams(
        place="garage",
        source="mower_tank",
        cause="cracked_hose",
        response="close_area_and_call",
        sniffer="Ava",
        sniffer_gender="girl",
        partner="Ella",
        partner_gender="girl",
        partner_trait="sensible",
        adult="mother",
        relation="siblings",
        sniffer_age=5,
        partner_age=7,
    ),
]


def explain_rejection(place: Place, source: Source, cause: Cause) -> str:
    if not place_fits(place, source):
        return (
            f"(No story: {source.label} does not belong naturally in {place.label}, "
            f"so the mystery would feel forced. Pick a source that fits the place.)"
        )
    if not cause_fits(source, cause):
        return (
            f"(No story: {cause.label} does not match {source.label}. The clue and the cause must fit the actual fuel source.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of these safer responses: {better}.)"
    )


ASP_RULES = r"""
fits(Place, Source) :- place(Place), source(Source), kept_in(Place, Source).
matches(Source, Cause) :- source(Source), cause(Cause), allowed(Source, Cause).
valid(Place, Source, Cause) :- fits(Place, Source), matches(Source, Cause).

sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.

cautious_now(Trait) :- trait(Trait), is_cautious(Trait).
init_caution(5) :- trait(Trait), cautious_now(Trait).
init_caution(3) :- trait(Trait), not cautious_now(Trait).

partner_older :- relation(siblings), sniffer_age(SA), partner_age(PA), PA > SA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), curiosity_init(CI), A > CI.

outcome(averted) :- averted.
outcome(inhaled) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.fits):
            lines.append(asp.fact("kept_in", place_id, source_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for source_id in sorted(cause.source_types):
            lines.append(asp.fact("allowed", source_id, cause_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
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


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.sniffer_age, params.partner_age, params.partner_trait) else "inhaled"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("sniffer_age", params.sniffer_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.partner_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small whodunit about a dangerous smell, a detective mistake, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.place and args.source and args.cause:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        cause = CAUSES[args.cause]
        if not (place_fits(place, source) and cause_fits(source, cause)):
            raise StoryError(explain_rejection(place, source, cause))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.source is None or c[1] == args.source)
        and (args.cause is None or c[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, cause_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    sniffer, sniffer_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=sniffer)
    partner_trait = rng.choice(TRAITS)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    relation = rng.choice(["siblings", "friends"])
    sniffer_age, partner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        place=place_id,
        source=source_id,
        cause=cause_id,
        response=response_id,
        sniffer=sniffer,
        sniffer_gender=sniffer_gender,
        partner=partner,
        partner_gender=partner_gender,
        partner_trait=partner_trait,
        adult=adult,
        relation=relation,
        sniffer_age=sniffer_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    place = PLACES[params.place]
    source = SOURCES[params.source]
    cause = CAUSES[params.cause]
    if not (place_fits(place, source) and cause_fits(source, cause)):
        raise StoryError(explain_rejection(place, source, cause))

    world = tell(
        place=place,
        source=source,
        cause=cause,
        response=RESPONSES[params.response],
        sniffer_name=params.sniffer,
        sniffer_gender=params.sniffer_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        partner_trait=params.partner_trait,
        adult_type=params.adult,
        relation=params.relation,
        sniffer_age=params.sniffer_age,
        partner_age=params.partner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, cause) combos:\n")
        for place, source, cause in combos:
            print(f"  {place:10} {source:11} {cause}")
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
            header = f"### {p.sniffer} & {p.partner}: {p.place}, {p.source}, {p.cause} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
