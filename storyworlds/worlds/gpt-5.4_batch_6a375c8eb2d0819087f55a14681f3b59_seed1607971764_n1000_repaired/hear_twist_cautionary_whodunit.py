#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py
============================================================

A standalone story world for a tiny whodunit-shaped cautionary tale: two
children hear a strange sound in a dark storage place, imagine a thief, and
must decide whether to investigate safely or sneak into the dark alone.

The twist is that the "culprit" is never a villain at all. It is something
ordinary -- a cat, a mouse, or the wind -- but the danger becomes real when a
child treats the mystery like a game and moves through clutter without light.
The lesson is simple and child-facing: if you hear a strange noise, call a
grown-up and turn on a light instead of creeping into the dark.

Run it
------
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --location pantry --culprit mouse
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --response candle
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/hear_twist_cautionary_whodunit.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


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
    movable: bool = False
    makes_noise: bool = False
    gives_light: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Location:
    id: str
    label: str
    opening: str
    detail: str
    dark_phrase: str
    obstacle: str
    obstacle_phrase: str
    spill: str
    risk: int
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
class Culprit:
    id: str
    label: str
    article: str
    sound: str
    clue: str
    reveal: str
    innocent: str
    locations: set[str] = field(default_factory=set)
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
    label: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_stumble(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("entered_dark"):
        return out
    investigator = world.get("investigator")
    place = world.get("place")
    obstacle = world.get("obstacle")
    if place.meters["dark"] < THRESHOLD or obstacle.meters["trip_risk"] < THRESHOLD:
        return out
    if investigator.meters["has_light"] >= THRESHOLD:
        return out
    sig = ("stumble", investigator.id, place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    investigator.meters["stumbled"] += 1
    investigator.meters["bumped"] += 1
    place.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.facts["stumble_happened"] = True
    out.append("__stumble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    investigator = world.get("investigator")
    spill = world.get("spill")
    if investigator.meters["stumbled"] < THRESHOLD:
        return out
    sig = ("spill", spill.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spill.meters["spilled"] += 1
    world.get("place").meters["mess"] += 1
    world.facts["big_noise"] = True
    out.append("__spill__")
    return out


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("big_noise"):
        return out
    parent = world.get("Parent")
    sig = ("alert", parent.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.meters["alerted"] += 1
    world.facts["parent_alerted"] = True
    out.append("__alert__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stumble", tag="physical", apply=_r_stumble),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="alert", tag="social", apply=_r_alert),
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


def culprit_fits(location: Location, culprit: Culprit) -> bool:
    return location.id in culprit.locations


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def mystery_severity(location: Location, delay: int) -> int:
    return location.risk + delay


def is_contained(response: Response, location: Location, delay: int) -> bool:
    return response.power >= mystery_severity(location, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_dark_trouble(world: World) -> dict:
    sim = world.copy()
    sim.facts["entered_dark"] = True
    propagate(sim, narrate=False)
    return {
        "stumble": sim.get("investigator").meters["stumbled"] >= THRESHOLD,
        "mess": sim.get("place").meters["mess"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, place: Location) -> None:
    for kid in (a, b):
        kid.memes["cozy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} were supposed to be getting ready for bed, "
        f"but the house still felt full of soft little sounds."
    )
    world.say(
        f"They passed {place.opening}, and the dark doorway looked almost like the start "
        f"of a tiny mystery."
    )
    world.say(place.detail)


def hear_noise(world: World, a: Entity, b: Entity, culprit: Culprit, place: Location) -> None:
    world.say(
        f'Then {a.id} stopped. "Wait -- I hear something," {a.pronoun()} whispered.'
    )
    world.say(
        f"From inside {place.dark_phrase} came {culprit.sound}. {b.id} listened too, "
        f"and both children stared at the shadows."
    )
    world.say(
        f"It sounded just strange enough to make them wonder who could be hiding in there."
    )


def suspect_game(world: World, a: Entity, b: Entity, culprit: Culprit, place: Location) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"Maybe it is a thief," {a.id} said, lowering {a.pronoun("possessive")} voice. '
        f'"Or maybe a snack robber. We can solve it before anyone else even knows."'
    )
    world.say(
        f"{b.id} glanced toward {place.label} and noticed {culprit.clue}. The clue only made "
        f"the mystery feel deeper."
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, place: Location) -> None:
    pred = predict_dark_trouble(world)
    world.facts["predicted_stumble"] = pred["stumble"]
    b.memes["caution"] += 1
    extra = ""
    if pred["stumble"]:
        extra = f" There was {place.obstacle_phrase} in the dark, and that was exactly the sort of thing a rushing foot could miss."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, let\'s not sneak in by ourselves. '
        f'We should get {parent.label_word} and turn on a light first."{extra}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    instigator_older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Real detectives do not wait," {a.id} said. Because {a.id} was {b.pronoun("possessive")} '
            f'{rel}, {b.id} hesitated for one worried second before following to the doorway.'
        )
    else:
        world.say(
            f'"Real detectives do not wait," {a.id} said, and tiptoed toward the darkness anyway.'
        )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} took one step, then stopped. {b.id} sounded so sure that the mystery no longer felt '
        f'fun. Instead of sneaking in, they hurried to find {parent.label_word}.'
    )


def enter_dark(world: World, a: Entity, place: Location) -> None:
    world.facts["entered_dark"] = True
    world.say(
        f"{a.id} slipped into {place.dark_phrase}, holding {a.pronoun('possessive')} breath as if that "
        f"might help {a.pronoun('object')} hear better."
    )
    propagate(world, narrate=False)
    if world.facts.get("stumble_happened"):
        world.say(
            f"But the floor was darker than it looked. {a.id}'s foot found {place.obstacle_phrase}, and "
            f"{a.pronoun()} stumbled with a frightened gasp."
        )
    if world.get("spill").meters["spilled"] >= THRESHOLD:
        world.say(
            f"{place.spill.capitalize()} tumbled over with a loud clatter. The tiny mystery suddenly became "
            f"a real problem."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} cried. "We need help!"')


def rescue(world: World, parent: Entity, response: Response, place: Location) -> None:
    investigator = world.get("investigator")
    investigator.meters["has_light"] += 1
    world.get("place").meters["dark"] = 0.0
    world.get("place").meters["danger"] = 0.0
    body = response.text.format(place=place.label)
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {body}."
    )
    world.say(
        f"The dark corner did not feel spooky anymore once the light reached all the way in."
    )


def rescue_fail(world: World, parent: Entity, response: Response, place: Location) -> None:
    body = response.fail.format(place=place.label)
    investigator = world.get("investigator")
    investigator.meters["bumped"] += 1
    world.get("place").meters["mess"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"By then, the spill had spread farther across the floor, and {world.get('investigator').id} was rubbing a sore knee."
    )


def reveal(world: World, culprit: Culprit, place: Location) -> None:
    culprit_ent = world.get("culprit")
    culprit_ent.meters["found"] += 1
    world.facts["solved"] = True
    world.say(
        f"Then the truth popped into view: {culprit.reveal}"
    )
    world.say(
        f"The great nighttime suspect was only {culprit.innocent}, not a villain at all."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, place: Location) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "If you hear a strange noise, you do not have '
        f'to solve it alone," {parent.pronoun()} said softly. "Dark places hide ordinary things -- and they '
        f'also hide {place.obstacle}. Call a grown-up and get light first."'
    )


def tidy_ending(world: World, a: Entity, b: Entity, place: Location, response: Response) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Together they set {place.label} right again, and this time the mystery felt small enough to smile at."
    )
    world.say(
        f"After that, whenever a house sound made them wonder, {a.id} and {b.id} looked for a light before they looked for clues."
    )
    world.say(
        f"In the bright doorway, the case was closed -- safely, sensibly, and with everyone able to laugh."
    )


def sore_ending(world: World, a: Entity, b: Entity, place: Location) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"They cleaned up slowly while {a.id} sat on a chair with a cold cloth on {a.pronoun('possessive')} knee."
    )
    world.say(
        f"The mystery had been harmless, but sneaking into {place.label} in the dark had not been. After that night, both children remembered to ask for help first."
    )


def tell(
    location: Location,
    culprit: Culprit,
    response: Response,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    cautioner: str = "Ben",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    place = world.add(Entity(
        id="place",
        type="place",
        label=location.label,
    ))
    place.meters["dark"] = 1.0
    obstacle = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=location.obstacle,
        movable=True,
    ))
    obstacle.meters["trip_risk"] = 1.0
    spill = world.add(Entity(
        id="spill",
        type="spill",
        label=location.spill,
        movable=True,
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        type="culprit",
        label=culprit.label,
        makes_noise=True,
    ))
    investigator = world.add(Entity(
        id="investigator",
        type=instigator_gender,
        label=instigator,
    ))
    investigator.meters["has_light"] = 0.0
    investigator.meters["stumbled"] = 0.0
    investigator.meters["bumped"] = 0.0
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.facts.update(
        entered_dark=False,
        stumble_happened=False,
        big_noise=False,
        parent_alerted=False,
        solved=False,
    )

    play_setup(world, a, b, location)
    hear_noise(world, a, b, culprit, location)

    world.para()
    suspect_game(world, a, b, culprit, location)
    warn(world, b, a, parent, location)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        rescue(world, parent, response, location)
        reveal(world, culprit, location)
        lesson(world, parent, a, b, location)
        world.para()
        tidy_ending(world, a, b, location, response)
        contained = True
    else:
        defy(world, a, b)
        world.para()
        enter_dark(world, a, location)
        alarm(world, b, parent)
        contained = is_contained(response, location, delay)
        world.para()
        if contained:
            rescue(world, parent, response, location)
            reveal(world, culprit, location)
            lesson(world, parent, a, b, location)
            world.para()
            tidy_ending(world, a, b, location, response)
        else:
            rescue_fail(world, parent, response, location)
            reveal(world, culprit, location)
            lesson(world, parent, a, b, location)
            world.para()
            sore_ending(world, a, b, location)

    outcome = "averted" if averted else ("contained" if contained else "bumped")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        location_cfg=location,
        culprit_cfg=culprit,
        response=response,
        investigator=investigator,
        obstacle=obstacle,
        spill=spill,
        outcome=outcome,
        delay=delay,
        severity=mystery_severity(location, delay) if not averted else 0,
        mystery_sound=culprit.sound,
        relation=relation,
        revealed=world.get("culprit").meters["found"] >= THRESHOLD,
        stumbled=investigator.meters["stumbled"] >= THRESHOLD,
        bumped=investigator.meters["bumped"] >= THRESHOLD,
    )
    return world


LOCATIONS = {
    "pantry": Location(
        id="pantry",
        label="the pantry",
        opening="the pantry door",
        detail="A thin line of warm hall light stopped at the cracked door, but inside the shelves were only shapes.",
        dark_phrase="the pantry",
        obstacle="a low wooden step stool",
        obstacle_phrase="the low wooden step stool",
        spill="a tin of cookie cutters",
        risk=1,
        tags={"pantry", "dark", "kitchen"},
    ),
    "attic": Location(
        id="attic",
        label="the attic stairs",
        opening="the attic stairs",
        detail="The little stairs to the attic curled up into a dusty dark patch near the ceiling.",
        dark_phrase="the attic stairs",
        obstacle="a loose toy train left on a step",
        obstacle_phrase="the loose toy train on a step",
        spill="a box of old buttons",
        risk=2,
        tags={"attic", "dark"},
    ),
    "shed": Location(
        id="shed",
        label="the garden shed",
        opening="the garden shed",
        detail="Outside the back door, the shed stood quiet and black under the moon, with tools asleep inside.",
        dark_phrase="the garden shed",
        obstacle="a rake lying where it should not have been",
        obstacle_phrase="the rake lying on the floor",
        spill="a stack of empty flower pots",
        risk=2,
        tags={"shed", "dark", "garden"},
    ),
}

CULPRITS = {
    "cat": Culprit(
        id="cat",
        label="cat",
        article="the cat",
        sound="a light clink and a scratch",
        clue="one tiny paw print near the doorway",
        reveal="the family cat batting at something shiny with one delighted paw",
        innocent="the cat chasing a glimmer",
        locations={"pantry", "shed"},
        tags={"cat", "pet", "hear"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        article="a mouse",
        sound="a rustle, then a soft tap",
        clue="a nibbled paper corner by a box",
        reveal="a mouse peeping out from behind a box and freezing in the light",
        innocent="a little mouse looking for crumbs",
        locations={"pantry", "attic", "shed"},
        tags={"mouse", "hear"},
    ),
    "wind": Culprit(
        id="wind",
        label="wind",
        article="the wind",
        sound="a tap-tap rattle",
        clue="the curtain or door edge moving just a little",
        reveal="the wind nudging a loose latch so it tapped again and again",
        innocent="the wind playing with a loose latch",
        locations={"attic", "shed"},
        tags={"wind", "weather", "hear"},
    ),
}

RESPONSES = {
    "flashlight": Response(
        id="flashlight",
        sense=3,
        power=3,
        label="flashlight",
        text="clicked on a flashlight and swept the beam across {place} before taking another step",
        fail="found a flashlight, but by the time the beam reached {place}, the mess had already spread",
        qa_text="turned on a flashlight and checked the dark place carefully",
        tags={"flashlight", "light"},
    ),
    "hall_light": Response(
        id="hall_light",
        sense=3,
        power=2,
        label="hall light",
        text="snapped on the nearest bright light and called for everyone to stay still",
        fail="snapped on the nearest bright light, but it did not reach far enough into {place} to prevent a bigger spill",
        qa_text="turned on the nearby light and made everyone stay still",
        tags={"light", "switch"},
    ),
    "lantern": Response(
        id="lantern",
        sense=3,
        power=4,
        label="lantern",
        text="lifted a camping lantern from the shelf and carried its steady glow straight to {place}",
        fail="lifted a lantern and hurried over, but the clatter had already knocked more things loose in {place}",
        qa_text="brought a bright lantern and checked the dark place slowly",
        tags={"lantern", "light"},
    ),
    "candle": Response(
        id="candle",
        sense=1,
        power=1,
        label="candle",
        text="lit a candle and held it up carefully",
        fail="lit a candle, but the little flame was a poor way to search a cluttered dark place",
        qa_text="lit a candle",
        tags={"candle", "light"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Ella", "Lucy", "Anna", "Maya", "Zoe", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Tom"]
TRAITS = ["careful", "cautious", "sensible", "thoughtful", "curious", "clever"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for lid, location in LOCATIONS.items():
        for cid, culprit in CULPRITS.items():
            if culprit_fits(location, culprit):
                combos.append((lid, cid))
    return combos


@dataclass
class StoryParams:
    location: str
    culprit: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "hear": [
        (
            "What does it mean to hear something?",
            "To hear something means sound reaches your ears, like a tap, a rustle, or a voice. Hearing tells you something is happening, but not always exactly what caused it."
        )
    ],
    "light": [
        (
            "Why should you turn on a light in a dark place?",
            "A light helps you see where to step and what is really there. In the dark, harmless things can look spooky, and clutter can be easy to trip over."
        )
    ],
    "cat": [
        (
            "Why might a cat make strange sounds at night?",
            "Cats like to chase, tap, and explore, especially when a house is quiet. A cat can make little mystery noises without meaning to scare anyone."
        )
    ],
    "mouse": [
        (
            "Why does a mouse make rustling sounds?",
            "A mouse is small and quick, so it often makes light rustling sounds when it moves through paper, boxes, or crumbs. You may hear it before you see it."
        )
    ],
    "wind": [
        (
            "How can the wind sound like a mystery?",
            "Wind can tap a loose latch, shake a branch, or rattle a door. That can sound mysterious until you see what it is doing."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight makes a bright beam so you can see clearly in dark places. It is a safe way to check a shadowy corner."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives a steady light all around it, so people can see where they are walking. It helps make a dark place feel less confusing."
        )
    ],
    "switch": [
        (
            "Why is staying still helpful when a grown-up turns on a light?",
            "Staying still keeps you from stepping on something you cannot see yet. Once the light is on, it is easier to move safely."
        )
    ],
    "caution": [
        (
            "What should you do if you hear a strange noise in the dark?",
            "Tell a grown-up and get light before you investigate. Solving the mystery safely is more important than solving it quickly."
        )
    ],
}
KNOWLEDGE_ORDER = ["hear", "caution", "light", "cat", "mouse", "wind", "flashlight", "lantern", "switch"]


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
    location = f["location_cfg"]
    culprit = f["culprit_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short whodunit-style story for a 3-to-5-year-old where two children hear a strange noise in '
        f'{location.label} and wonder who made it. Include the word "hear".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle mystery where {a.id} wants to sneak into {location.label}, but {b.id} insists on getting a grown-up and that turns out to be the wise choice.",
            f'Write a cautionary twist story where the children expect a thief, but the real culprit is {culprit.innocent}, and the mystery is solved safely with a light.',
        ]
    if outcome == "bumped":
        return [
            base,
            f"Tell a cautionary whodunit where {a.id} investigates alone in the dark, bumps into clutter, and learns that a harmless sound can still lead to a real accident.",
            f'Write a mystery with a twist: the culprit is {culprit.innocent}, but the bigger problem comes from sneaking into the dark without help.',
        ]
    return [
        base,
        f"Tell a child-friendly mystery where {a.id} thinks there may be a thief in {location.label}, a grown-up arrives with light, and the truth is surprising but ordinary.",
        f'Write a cautionary twist story where the culprit is {culprit.innocent}, and the ending teaches the children to get light and help before they investigate.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    location = f["location_cfg"]
    culprit = f["culprit_cfg"]
    response = f["response"]
    pair = pair_noun(a, b, f.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who heard a strange sound, and their {parent.label_word} who helped solve the mystery."
        ),
        (
            "What mystery did the children notice?",
            f"They heard {culprit.sound} coming from {location.label}, so they started wondering who was hiding there. The strange sound made an ordinary place feel spooky for a moment."
        ),
        (
            f"Why did {b.id} want help before they investigated?",
            f"{b.id} knew the place was dark and that dark floors can hide {location.obstacle}. {b.pronoun().capitalize()} wanted a grown-up and a light first so the mystery would not turn into an accident."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} stopped before sneaking in and went to get {parent.label_word} instead. That choice kept the mystery exciting without letting anyone trip in the dark."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} went into the dark place?",
                f"{a.id} stumbled because the floor hid {location.obstacle_phrase}. The quick call for help stopped the small scare from turning into a bigger mess."
            )
        )
        qa.append(
            (
                f"How did the grown-up solve the problem?",
                f"{parent.label_word.capitalize()} {response.qa_text}. Once the light reached inside, the scary guess disappeared and the real cause was easy to see."
            )
        )
    else:
        qa.append(
            (
                f"What went wrong before the mystery was solved?",
                f"{a.id} stumbled in the dark and knocked over {location.spill}. The real culprit was harmless, but the unsafe sneaking caused the sore knee and extra mess."
            )
        )
        qa.append(
            (
                f"What lesson did the children learn?",
                f"They learned that hearing a mystery sound does not mean they should rush toward it alone. Asking for help and turning on a light would have made the whole case much safer."
            )
        )
    qa.append(
        (
            "What was the twist at the end?",
            f"The children thought the noise might be a thief, but it was really {culprit.innocent}. The twist shows that the frightening guess was wrong even though the dark place was still risky."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hear", "caution", "light"}
    culprit = world.facts["culprit_cfg"]
    response = world.facts["response"]
    tags |= set(culprit.tags)
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k in {'entered_dark', 'stumble_happened', 'big_noise', 'parent_alerted', 'solved', 'outcome', 'severity', 'delay'})}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        location="pantry",
        culprit="mouse",
        response="flashlight",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        location="shed",
        culprit="cat",
        response="lantern",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        location="attic",
        culprit="wind",
        response="hall_light",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Anna",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        location="pantry",
        culprit="cat",
        response="lantern",
        instigator="Lucy",
        instigator_gender="girl",
        cautioner="Rose",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=6,
    ),
]


def explain_rejection(location: Location, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.article} is not a reasonable culprit in {location.label} here. "
        f"Pick a culprit that could actually make sounds there.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A dark mystery should be solved with a safer source of light. "
        f"Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], LOCATIONS[params.location], params.delay)
    return "contained" if contained else "bumped"


ASP_RULES = r"""
culprit_fits(L, C) :- location(L), culprit(C), allowed(C, L).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(L, C) :- location(L), culprit(C), culprit_fits(L, C).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(R + D) :- chosen_location(L), risk(L, R), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bumped) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lid, location in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        lines.append(asp.fact("risk", lid, location.risk))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for lid in sorted(culprit.locations):
            lines.append(asp.fact("allowed", cid, lid))
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

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_location", params.location),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(150):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny cautionary whodunit about hearing a strange sound in the dark."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much extra time the confusion gets before the grown-up's light fully helps")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.culprit:
        location = LOCATIONS[args.location]
        culprit = CULPRITS[args.culprit]
        if not culprit_fits(location, culprit):
            raise StoryError(explain_rejection(location, culprit))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.location is None or c[0] == args.location)
        and (args.culprit is None or c[1] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    location, culprit = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        location=location,
        culprit=culprit,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    location = LOCATIONS[params.location]
    culprit = CULPRITS[params.culprit]
    response = RESPONSES[params.response]

    if not culprit_fits(location, culprit):
        raise StoryError(explain_rejection(location, culprit))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        location=location,
        culprit=culprit,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (location, culprit) combos:\n")
        for location, culprit in combos:
            print(f"  {location:8} {culprit}")
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
                f"### {p.instigator} & {p.cautioner}: {p.culprit} in {p.location} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
