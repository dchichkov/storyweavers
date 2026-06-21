#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trauma_topple_atlantic_conflict_pirate_tale.py
===========================================================================

A standalone story world for a pirate-flavored conflict tale on the Atlantic
shore: two children are playing pirates, a bit of treasure slips somewhere hard
to reach, one child wants to climb something wobbly, the other warns that it
could topple, and a grown-up helps them choose the safer way.

This world keeps the storytelling close to a tiny pirate adventure while making
the conflict genuinely state-driven:
- a setting affords certain shore zones,
- a treasure lands in one zone,
- an unsafe perch in that same zone might reach it but can topple,
- a safer response tool can succeed or fail depending on how risky the situation
  has become.

The word "trauma" is used carefully, as a grown-up's gentle explanation for a
big scary feeling after a fall.

Run it
------
    python storyworlds/worlds/gpt-5.4/trauma_topple_atlantic_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/trauma_topple_atlantic_conflict_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/trauma_topple_atlantic_conflict_pirate_tale.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trauma_topple_atlantic_conflict_pirate_tale.py --verify
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
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "wise"}


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
    unstable: bool = False
    recover_tool: bool = False
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
class Setting:
    id: str
    place: str
    shore: str
    rig: str
    zones: set[str] = field(default_factory=set)
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
class Perch:
    id: str
    label: str
    phrase: str
    zone: str
    climb: str
    wobble: str
    fall: str
    severity: int
    unstable: bool = True
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
class Treasure:
    id: str
    label: str
    phrase: str
    zone: str
    drift: str
    ending: str
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
    zone: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_topple(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    child = world.get("instigator")
    if perch.meters["climbed"] >= THRESHOLD and perch.unstable:
        sig = ("topple", perch.id)
        if sig not in world.fired:
            world.fired.add(sig)
            perch.meters["fallen"] += 1
            child.meters["wet"] += 1
            child.meters["bruised"] += 1
            child.memes["fear"] += 2
            world.get("cautioner").memes["fear"] += 1
            world.get("shore").meters["danger"] += 1
            out.append("__topple__")
    return out


def _r_shaken(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    if child.meters["bruised"] >= THRESHOLD and child.memes["fear"] >= THRESHOLD:
        sig = ("shaken", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["shaken"] += 1
            out.append("__shaken__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="topple", tag="physical", apply=_r_topple),
    Rule(name="shaken", tag="emotional", apply=_r_shaken),
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


def treasure_at_risk(setting: Setting, perch: Perch, treasure: Treasure) -> bool:
    return perch.unstable and perch.zone == treasure.zone and treasure.zone in setting.zones


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def tool_matches(perch: Perch, response: Response) -> bool:
    return perch.zone == response.zone


def best_response() -> Response:
    return max(sensible_responses(), key=lambda r: (r.sense, r.power))


def incident_severity(perch: Perch, delay: int) -> int:
    return perch.severity + delay


def is_recovered(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= incident_severity(perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_topple(world: World) -> dict:
    sim = world.copy()
    perch = sim.get("perch")
    perch.meters["climbed"] += 1
    propagate(sim, narrate=False)
    return {
        "topples": perch.meters["fallen"] >= THRESHOLD,
        "danger": sim.get("shore").meters["danger"],
        "shaken": sim.get("instigator").memes["shaken"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon by the Atlantic, {a.id} and {b.id} turned {setting.place} into a pirate harbor. "
        f"{setting.rig}"
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} cried. "Today we sail for treasure!"'
    )


def treasure_problem(world: World, b: Entity, treasure: Treasure, perch: Perch) -> None:
    world.say(
        f"A gust snatched their {treasure.label} and sent it {treasure.drift}, close beside {perch.phrase}."
    )
    world.say(
        f'{b.id} leaned forward. "Oh no," {b.pronoun()} said. "Our treasure is stuck where we cannot quite reach it."'
    )


def tempt(world: World, a: Entity, perch: Perch) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {perch.phrase}. "I can get it," {a.pronoun()} said. "I will {perch.climb}."'
    )


def warn(world: World, b: Entity, a: Entity, perch: Perch, parent: Entity) -> None:
    pred = predict_topple(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_shaken"] = pred["shaken"]
    extra = ""
    if pred["shaken"]:
        extra = " It could leave a big, shaky feeling afterward, even if the splash was small."
    world.say(
        f'{b.id} grabbed {a.pronoun("possessive")} sleeve. "No, {a.id}," {b.pronoun()} said. '
        f'"{perch.wobble}. We should call {parent.label_word} instead."{extra}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Pirates do not wait," {a.id} said, and because {a.pronoun()} was {b.id}\'s older sibling, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"Pirates do not wait," {a.id} said, and darted forward before {b.id} could pull {a.pronoun("object")} back.'
        )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sib = ""
    if b.age > a.age and a.attrs.get("relation") == "siblings":
        sib = " big"
    world.say(
        f'{a.id} looked at {b.id}\'s{sib} steady face, swallowed hard, and stepped back from the edge. "All right," {a.pronoun()} said. "We call {parent.label_word}."'
    )


def climb_and_topple(world: World, a: Entity, perch: Entity, perch_cfg: Perch) -> None:
    perch.meters["climbed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} scrambled up, but {perch_cfg.fall}. The whole thing began to topple with a clack and a scrape."
    )
    world.say(
        f"{a.id} splashed down in the cold shallows with a yelp, clutching nothing but a dripping sleeve."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} shouted. "Help! The perch toppled!"')


def rescue(world: World, parent: Entity, response: Response, treasure: Treasure, a: Entity) -> None:
    a.meters["wet"] = 0.0
    world.get("shore").meters["danger"] = 0.0
    world.get("treasure").meters["recovered"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came running and {response.text.format(treasure=treasure.label)}."
    )
    world.say(
        f'Soon the {treasure.label} was back in safe hands, and {a.id} was wrapped in a dry towel, shivering more from surprise than from cold.'
    )


def comfort(world: World, parent: Entity, a: Entity, b: Entity, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    a.memes["fear"] = 0.0
    b.memes["fear"] = 0.0
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "That was a real scare," {parent.pronoun()} said softly. '
        f'"Sometimes a shock leaves a little trauma in your tummy or your chest, even after you are safe. That is why we ask for help before we climb wobbly things."'
    )
    world.say(
        f'{a.id} nodded and leaned against {parent.pronoun("object")}, while {b.id} held the {treasure.label} tight and stayed close.'
    )


def safe_end(world: World, a: Entity, b: Entity, parent: Entity, treasure: Treasure, response: Response) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f'After the scare, {parent.label_word} showed them how to use {response.label} from solid ground. This time they reached the treasure without one slippery step.'
    )
    world.say(
        f'Soon Captain {a.id} and Mate {b.id} were back to their game, and the Atlantic wind only rattled their paper flag, not their hearts.'
    )


def rescue_fail(world: World, parent: Entity, response: Response, treasure: Treasure, a: Entity) -> None:
    world.get("treasure").meters["lost"] += 1
    world.get("shore").meters["danger"] = 0.0
    a.meters["wet"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.fail.format(treasure=treasure.label)}."
    )
    world.say(
        f'But a wash of Atlantic water tugged the {treasure.label} away, and it bobbed out beyond everyone\'s reach.'
    )


def sad_lesson(world: World, parent: Entity, a: Entity, b: Entity, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} held them close. "The treasure is gone, but you are here," {parent.pronoun()} said. "That matters more than any pirate prize."'
    )
    world.say(
        f'The children watched the empty water for a moment. They never forgot how fast one proud choice could turn a game into a frightening conflict.'
    )


def tell(
    setting: Setting,
    perch: Perch,
    treasure: Treasure,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation, "name": instigator},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "name": cautioner},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(id="shore", type="shore", label=setting.shore))
    world.add(Entity(id="perch", type="perch", label=perch.label, unstable=perch.unstable))
    world.add(Entity(id="treasure", type="treasure", label=treasure.label))
    world.add(Entity(id="tool", type="tool", label=response.label, recover_tool=True))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    world.facts["relation"] = relation
    world.facts["delay"] = delay

    play_setup(world, Entity(id=instigator, type=instigator_gender), Entity(id=cautioner, type=cautioner_gender), setting)
    treasure_problem(world, Entity(id=cautioner, type=cautioner_gender), treasure, perch)

    world.para()
    tempt(world, Entity(id=instigator, type=instigator_gender), perch)
    warn(world, Entity(id=cautioner, type=cautioner_gender), Entity(id=instigator, type=instigator_gender), perch, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, Entity(id=instigator, type=instigator_gender), Entity(id=cautioner, type=cautioner_gender, age=cautioner_age), parent)
        world.para()
        rescue(world, parent, response, treasure, a)
        comfort(world, parent, a, b, treasure)
        world.para()
        safe_end(world, Entity(id=instigator, type=instigator_gender), Entity(id=cautioner, type=cautioner_gender), parent, treasure, response)
        severity = 0
        recovered = True
        outcome = "averted"
    else:
        defy(world, a=Entity(id=instigator, type=instigator_gender, age=instigator_age, attrs={"relation": relation}),
             b=Entity(id=cautioner, type=cautioner_gender, age=cautioner_age))
        world.para()
        climb_and_topple(world, a, world.get("perch"), perch)
        alarm(world, Entity(id=cautioner, type=cautioner_gender), parent)
        severity = incident_severity(perch, delay)
        world.get("perch").meters["severity"] = float(severity)
        recovered = is_recovered(response, perch, delay)
        world.para()
        if recovered:
            rescue(world, parent, response, treasure, a)
            comfort(world, parent, a, b, treasure)
            world.para()
            safe_end(world, Entity(id=instigator, type=instigator_gender), Entity(id=cautioner, type=cautioner_gender), parent, treasure, response)
            outcome = "recovered"
        else:
            rescue_fail(world, parent, response, treasure, a)
            sad_lesson(world, parent, a, b, treasure)
            outcome = "lost"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        setting=setting,
        perch_cfg=perch,
        perch=world.get("perch"),
        treasure_cfg=treasure,
        treasure=world.get("treasure"),
        response=response,
        outcome=outcome,
        severity=severity,
        recovered=recovered,
        toppled=world.get("perch").meters["fallen"] >= THRESHOLD,
        shaken=a.memes["shaken"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "atlantic_cove": Setting(
        id="atlantic_cove",
        place="the little Atlantic cove",
        shore="the cove shore",
        rig="A driftwood bench became their ship, a striped towel became a sail, and a biscuit tin held their sea-glass treasure.",
        zones={"rocks", "pier"},
        tags={"atlantic", "shore"},
    ),
    "atlantic_dock": Setting(
        id="atlantic_dock",
        place="the old Atlantic dock",
        shore="the dock edge",
        rig="A coil of rope became an anchor line, a blue bucket became their barrel, and a chalk arrow pointed toward hidden gold.",
        zones={"pier", "crates"},
        tags={"atlantic", "dock"},
    ),
    "atlantic_beach": Setting(
        id="atlantic_beach",
        place="the windy Atlantic beach",
        shore="the beach edge",
        rig="A blanket became their deck, two sticks became masts, and a lunch box clicked shut like a captain's chest.",
        zones={"rocks", "dunes"},
        tags={"atlantic", "beach"},
    ),
}

PERCHES = {
    "slippery_rocks": Perch(
        id="slippery_rocks",
        label="rocks",
        phrase="the slippery rocks",
        zone="rocks",
        climb="hop onto the rocks and stretch from there",
        wobble="Those rocks are slick, and one wrong step could send you sideways",
        fall="the green-slick stones slid under his shoes",
        severity=2,
        unstable=True,
        tags={"rocks", "topple"},
    ),
    "stacked_crates": Perch(
        id="stacked_crates",
        label="crates",
        phrase="the stacked crates",
        zone="crates",
        climb="climb the crates and lean over the side",
        wobble="Those crates are stacked too high, and they could topple if you climb them",
        fall="the top crate lurched under his foot",
        severity=3,
        unstable=True,
        tags={"crates", "topple"},
    ),
    "dune_fence": Perch(
        id="dune_fence",
        label="fence",
        phrase="the wobbly dune fence",
        zone="dunes",
        climb="stand on the fence rail and reach across",
        wobble="That fence is loose, and it could topple you right into the wet sand",
        fall="the thin rail tipped and rattled loose",
        severity=1,
        unstable=True,
        tags={"fence", "topple"},
    ),
    "pier_rail": Perch(
        id="pier_rail",
        label="rail",
        phrase="the old pier rail",
        zone="pier",
        climb="balance on the rail and snatch it quickly",
        wobble="That rail is slick with spray, and you could topple off before you knew it",
        fall="the old rail rolled the spray right under his feet",
        severity=2,
        unstable=True,
        tags={"pier", "topple"},
    ),
}

TREASURES = {
    "map": Treasure(
        id="map",
        label="map",
        phrase="a crayon treasure map",
        zone="pier",
        drift="under the pier boards",
        ending="their map stayed dry enough for one more voyage",
        tags={"map", "tide"},
    ),
    "chest": Treasure(
        id="chest",
        label="chest",
        phrase="a little tin treasure chest",
        zone="crates",
        drift="behind the crate stack",
        ending="their chest clinked again with shells inside",
        tags={"chest", "dock"},
    ),
    "shell_pouch": Treasure(
        id="shell_pouch",
        label="shell pouch",
        phrase="a striped shell pouch",
        zone="rocks",
        drift="into a crack beside the rocks",
        ending="their shell pouch was sandy but safe",
        tags={"shells", "rocks"},
    ),
    "flag": Treasure(
        id="flag",
        label="flag",
        phrase="a paper pirate flag",
        zone="dunes",
        drift="against the dune grass",
        ending="their flag snapped proudly in the wind again",
        tags={"flag", "dunes"},
    ),
}

RESPONSES = {
    "boat_hook": Response(
        id="boat_hook",
        sense=3,
        power=3,
        zone="pier",
        label="a long boat hook",
        text="caught {treasure} with a long boat hook and guided it back while pulling the child away from the edge",
        fail="reached with a long boat hook, but the current carried {treasure} past the tip",
        qa_text="used a long boat hook to guide the treasure back and keep the child away from the edge",
        tags={"boat_hook", "rescue"},
    ),
    "cargo_net": Response(
        id="cargo_net",
        sense=3,
        power=3,
        zone="crates",
        label="a cargo net",
        text="flung down a cargo net, steadied the child, and scooped {treasure} free from behind the crates",
        fail="lowered a cargo net, but {treasure} had already slid too deep to catch",
        qa_text="used a cargo net to steady the child and scoop the treasure free",
        tags={"net", "rescue"},
    ),
    "drift_pole": Response(
        id="drift_pole",
        sense=2,
        power=2,
        zone="rocks",
        label="a smooth driftwood pole",
        text="stretched out a driftwood pole, helped the child stand, and nudged {treasure} back from the rocks",
        fail="reached with a driftwood pole, but a wave knocked {treasure} farther into the rocks",
        qa_text="used a driftwood pole to help the child stand and nudge the treasure back",
        tags={"pole", "rescue"},
    ),
    "sand_rake": Response(
        id="sand_rake",
        sense=2,
        power=1,
        zone="dunes",
        label="a long sand rake",
        text="used a long sand rake to pull {treasure} out of the grass while keeping everyone on firm sand",
        fail="raked for {treasure}, but the wind flipped it deeper into the dune grass",
        qa_text="used a long sand rake to pull the treasure out while everyone stayed on firm sand",
        tags={"rake", "rescue"},
    ),
    "bare_hands": Response(
        id="bare_hands",
        sense=1,
        power=1,
        zone="rocks",
        label="bare hands",
        text="scrambled in with bare hands and snatched {treasure} up at the last moment",
        fail="reached in with bare hands, but the slippery place was too awkward and {treasure} slipped away",
        qa_text="grabbed for the treasure with bare hands",
        tags={"unsafe_response"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "steady", "thoughtful", "wise", "curious", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, perch in PERCHES.items():
            for tid, treasure in TREASURES.items():
                if treasure_at_risk(setting, perch, treasure):
                    combos.append((sid, pid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    perch: str
    treasure: str
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
    "atlantic": [
        ("What is the Atlantic?",
         "The Atlantic is a very big ocean. Ocean water moves with wind and tides, so the shore can change quickly.")
    ],
    "topple": [
        ("What does topple mean?",
         "Topple means to tip over and fall down. Wobbly things can topple if someone climbs or pushes them.")
    ],
    "trauma": [
        ("What does trauma mean?",
         "Trauma is a very big hurt or shock feeling after something scary happens. Kind grown-ups help children feel safe again after a scare.")
    ],
    "tide": [
        ("What is a tide?",
         "A tide is the ocean water moving higher and lower along the shore. That moving water can carry light things away.")
    ],
    "rocks": [
        ("Why are shore rocks slippery?",
         "Shore rocks can be slippery because water and green seaweed make their tops slick. Feet can slide on them very fast.")
    ],
    "dock": [
        ("What is a dock?",
         "A dock is a place by the water where boats can stop. It often has boards, ropes, and edges that children should be careful around.")
    ],
    "boat_hook": [
        ("What is a boat hook?",
         "A boat hook is a long pole with a hook on the end. Grown-ups use it to pull things closer without leaning too far over the water.")
    ],
    "net": [
        ("What is a cargo net?",
         "A cargo net is a strong net used to hold or lift things. Its wide shape can help catch or steady something safely.")
    ],
    "pole": [
        ("Why can a long pole be safer than climbing?",
         "A long pole lets you reach from solid ground. That means you do not have to stand on a wobbly place.")
    ],
    "rake": [
        ("What does a rake do?",
         "A rake has a long handle and a head that pulls things closer. On sand, it can help move light things without stepping into a risky spot.")
    ],
}
KNOWLEDGE_ORDER = ["atlantic", "topple", "trauma", "tide", "rocks", "dock", "boat_hook", "net", "pole", "rake"]


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
    perch = f["perch_cfg"]
    treasure = f["treasure_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a short pirate tale for a 3-to-5-year-old set by the Atlantic, where two children argue over how to get back a lost {treasure.label}. '
        f'Include the words "trauma", "topple", and "atlantic".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle conflict story where {a.attrs['name']} wants to climb {perch.phrase}, but {b.attrs['name']} stops the risky plan and a grown-up helps from solid ground.",
            f"Write a pirate-play story with no bad fall, where a warning about something that might topple leads to a safer ending and a calm lesson about big scary feelings.",
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a cautionary pirate story where {a.attrs['name']} ignores a warning, something topples, and the children are safe but the {treasure.label} is lost to the Atlantic water.",
            f"Write a story about conflict, pride, and a scary mistake by the shore, ending with the lesson that people matter more than treasure.",
        ]
    return [
        base,
        f"Tell a pirate adventure where {a.attrs['name']} ignores {b.attrs['name']}'s warning, a perch topples, and a grown-up uses a safe tool to help.",
        f"Write a child-facing conflict story with a scary middle and a soft ending, where the children learn to ask for help instead of climbing something wobbly.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    setting = f["setting"]
    perch = f["perch_cfg"]
    treasure = f["treasure_cfg"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.attrs['name']} and {b.attrs['name']}, playing pirates by the Atlantic with their {pw} nearby."
        ),
        (
            "What problem started the conflict?",
            f"Their {treasure.label} blew into a hard-to-reach place near {perch.phrase}. {a.attrs['name']} wanted to climb after it, but {b.attrs['name']} wanted to call a grown-up instead."
        ),
        (
            f"Why did {b.attrs['name']} say no?",
            f"{b.attrs['name']} thought {perch.phrase} could topple and make the game turn scary. The warning came from seeing how wobbly and slippery that place was."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How was the problem solved without a fall?",
            f"{a.attrs['name']} listened and stepped back, so nobody climbed the risky place at all. Then {pw} used {response.label} from solid ground to bring the {treasure.label} back."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the treasure back and the pirate game going on in a calmer way. The ending proves the children changed because they chose help instead of pride."
        ))
    elif f["outcome"] == "recovered":
        qa.append((
            f"What happened when {a.attrs['name']} tried to climb?",
            f"{perch.phrase.capitalize()} toppled, and {a.attrs['name']} splashed down and got frightened. The fall turned a pretend pirate conflict into a real problem."
        ))
        qa.append((
            f"How did the grown-up help?",
            f"{pw.capitalize()} {response.qa_text.format(treasure=treasure.label)}. That quick, safer method fixed the problem without more climbing."
        ))
        qa.append((
            "Why did the grown-up use the word trauma?",
            f"{pw.capitalize()} used that big word to explain that a scary shock can stay in the body for a while, even after danger ends. It helped the children understand their shaky feelings and feel cared for."
        ))
    else:
        qa.append((
            f"Did they get the {treasure.label} back?",
            f"No. {pw.capitalize()} tried to help, but the Atlantic water carried it away. The children were safe, but they lost the pirate prize."
        ))
        qa.append((
            "What was the lesson at the end?",
            f"They learned that one proud choice can make a playful conflict much bigger. They also learned that people matter more than treasure, so safety comes first."
        ))
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"atlantic", "topple", "trauma"}
    tags |= set(f["setting"].tags)
    tags |= set(f["perch_cfg"].tags)
    tags |= set(f["treasure_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.unstable:
            bits.append("unstable=True")
        if e.recover_tool:
            bits.append("recover_tool=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="atlantic_cove",
        perch="slippery_rocks",
        treasure="shell_pouch",
        response="drift_pole",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="atlantic_dock",
        perch="stacked_crates",
        treasure="chest",
        response="cargo_net",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        setting="atlantic_cove",
        perch="pier_rail",
        treasure="map",
        response="boat_hook",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        setting="atlantic_beach",
        perch="dune_fence",
        treasure="flag",
        response="sand_rake",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="wise",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(setting: Setting, perch: Perch, treasure: Treasure) -> str:
    if treasure.zone not in setting.zones:
        return (
            f"(No story: {setting.place} does not have the right kind of spot for a {treasure.label} stuck in the {treasure.zone} area.)"
        )
    if perch.zone != treasure.zone:
        return (
            f"(No story: {perch.phrase} would not honestly help reach the {treasure.label}, because they are in different shore spots.)"
        )
    if not perch.unstable:
        return (
            f"(No story: {perch.phrase} is not risky enough to create the topple conflict.)"
        )
    return "(No story: this combination does not make a reasonable shore hazard.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense for this storyworld (sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "recovered" if is_recovered(RESPONSES[params.response], PERCHES[params.perch], params.delay) else "lost"


ASP_RULES = r"""
hazard(S, P, T) :- setting(S), perch(P), treasure(T), unstable(P),
                   zone_of(P, Z), zone_of(T, Z), affords(S, Z).

sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.
tool_match(P, R) :- perch(P), response(R), zone_of(P, Z), tool_zone(R, Z).
valid(S, P, T) :- hazard(S, P, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Sv + D) :- chosen_perch(P), perch_severity(P, Sv), delay(D).
contained :- chosen_response(R), chosen_perch(P), tool_match(P, R),
             power(R, Pw), severity(Se), Pw >= Se.

outcome(averted) :- averted.
outcome(recovered) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for zone in sorted(setting.zones):
            lines.append(asp.fact("affords", sid, zone))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("zone_of", pid, perch.zone))
        lines.append(asp.fact("perch_severity", pid, perch.severity))
        if perch.unstable:
            lines.append(asp.fact("unstable", pid))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("zone_of", tid, treasure.zone))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        lines.append(asp.fact("tool_zone", rid, response.zone))
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
    scenario = "\n".join([
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-tale storyworld: Atlantic shore conflict, a topple risk, and a safer way."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before the grown-up acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.perch and args.treasure:
        setting = SETTINGS[args.setting]
        perch = PERCHES[args.perch]
        treasure = TREASURES[args.treasure]
        if not treasure_at_risk(setting, perch, treasure):
            raise StoryError(explain_rejection(setting, perch, treasure))

    if args.response:
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.perch is None or combo[1] == args.perch)
        and (args.treasure is None or combo[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, perch_id, treasure_id = rng.choice(sorted(combos))
    perch = PERCHES[perch_id]

    response_choices = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and tool_matches(perch, response)
        and (args.response is None or rid == args.response)
    ]
    if not response_choices:
        raise StoryError("(No sensible response matches the chosen perch.)")
    response_id = rng.choice(sorted(response_choices))

    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        setting=setting_id,
        perch=perch_id,
        treasure=treasure_id,
        response=response_id,
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
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    perch = PERCHES[params.perch]
    treasure = TREASURES[params.treasure]
    response = RESPONSES[params.response]

    if not treasure_at_risk(setting, perch, treasure):
        raise StoryError(explain_rejection(setting, perch, treasure))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not tool_matches(perch, response):
        raise StoryError(
            f"(No story: {response.label} does not fit the {perch.zone} problem. Pick a tool for that shore spot.)"
        )

    world = tell(
        setting=setting,
        perch=perch,
        treasure=treasure,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
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
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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
        print(f"{len(combos)} compatible (setting, perch, treasure) combos:\n")
        for setting, perch, treasure in combos:
            print(f"  {setting:14} {perch:15} {treasure}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.treasure} at {p.setting} ({p.perch}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
