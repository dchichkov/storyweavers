#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py
===================================================================

A standalone storyworld for a gentle cautionary ghost-story domain: a child sees
something spooky, decides ordinary rules do not apply because bravery should make
them exempt, and then learns that brave choices still need care.

The world model tracks a small physical danger hidden behind the "ghost" feeling:
rotted stairs, an open well, or loose floorboards. The child-facing prose grows
from state: a spooky sign, a bold decision, a warning, either an averted near-miss
or a grown-up rescue, and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py --place attic --omen curtain_shape --hazard loose_floorboard
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py --hazard open_well
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exempt_bravery_cautionary_ghost_story.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}
SENSE_MIN = 2


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
    # physical / emotional axes
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
class Place:
    id: str
    label: str
    intro: str
    ghost_nook: str
    danger_nook: str
    hazards: set[str] = field(default_factory=set)
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
class Omen:
    id: str
    label: str
    seen_as: str
    cause_text: str
    sound_text: str
    works_in: set[str] = field(default_factory=set)
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
    risk_text: str
    rescue_text: str
    prevent_text: str
    severity: int
    places: set[str] = field(default_factory=set)
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
class SafetyAid:
    id: str
    label: str
    phrase: str
    use_text: str
    covers: set[str] = field(default_factory=set)
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_near_hazard(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    danger = world.entities.get("danger")
    if hero is None or danger is None:
        return out
    if hero.meters["approach"] < THRESHOLD:
        return out
    sig = ("near_hazard", world.facts.get("hazard_id"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    danger.meters["risk"] += 1
    hero.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_slip_or_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    danger = world.entities.get("danger")
    if hero is None or danger is None:
        return out
    if danger.meters["risk"] < THRESHOLD:
        return out
    if world.facts.get("averted"):
        return out
    sig = ("mishap", world.facts.get("hazard_id"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["shaken"] += 1
    hero.memes["fear"] += 1
    hero.memes["relief"] += 1
    out.append("__mishap__")
    return out


CAUSAL_RULES = [
    Rule(name="near_hazard", tag="physical", apply=_r_near_hazard),
    Rule(name="mishap", tag="physical", apply=_r_slip_or_drop),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def omen_fits(place: Place, omen: Omen) -> bool:
    return place.id in omen.works_in


def hazard_in_place(place: Place, hazard: Hazard) -> bool:
    return hazard.id in place.hazards and place.id in hazard.places


def aid_covers_hazard(aid: SafetyAid, hazard: Hazard) -> bool:
    return hazard.id in aid.covers


def sensible_aids() -> list[SafetyAid]:
    return [aid for aid in AIDS.values() if len(aid.covers) >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["approach"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("danger").meters["risk"],
        "shaken": sim.get("hero").meters["shaken"],
    }


def introduce(world: World, hero: Entity, cautioner: Entity, place: Place) -> None:
    hero.memes["wonder"] += 1
    cautioner.memes["wonder"] += 1
    world.say(
        f"On a windy evening, {hero.id} and {cautioner.id} stood near {place.label}. "
        f"{place.intro}"
    )
    world.say(
        f"The shadows around {place.ghost_nook} looked as if they were trying to whisper."
    )


def spot_omen(world: World, hero: Entity, cautioner: Entity, omen: Omen) -> None:
    hero.memes["bravado"] += 1
    cautioner.memes["unease"] += 1
    world.say(
        f"Then they saw {omen.seen_as}. {omen.sound_text}"
    )
    world.say(
        f'"It looks like a ghost," {cautioner.id} whispered.'
    )
    world.say(
        f'{hero.id} lifted {hero.pronoun("possessive")} chin. "Maybe," '
        f'{hero.pronoun()} said, "but I am not going to run."'
    )


def tempt_bravery(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} wanted to prove that being brave meant stepping closer to {place.danger_nook}."
    )
    world.say(
        f'"I am exempt from babyish shivers," {hero.id} said, trying to sound bigger than the night.'
    )


def warn(world: World, hero: Entity, cautioner: Entity, hazard: Hazard, parent: Entity) -> None:
    pred = predict_risk(world)
    cautioner.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{cautioner.id} caught {hero.id}\'s sleeve. "{parent.label_word.capitalize()} said '
        f'we should not creep around in the dark alone," {cautioner.pronoun()} said. '
        f'"There could be {hazard.label} there."'
    )


def back_down(world: World, hero: Entity, cautioner: Entity, parent: Entity, aid: SafetyAid, omen: Omen) -> None:
    hero.memes["bravery"] = 0.0
    hero.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f"{hero.id} listened at last and let the brave pose slip away."
    )
    world.say(
        f'Together they went to fetch {hero.pronoun("possessive")} {parent.label_word}, who brought {aid.phrase}. '
        f'In the steady light, the "ghost" turned out to be {omen.cause_text}.'
    )


def defy(world: World, hero: Entity, cautioner: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I just need one quick look," {hero.id} said, and before {cautioner.id} could stop '
        f'{hero.pronoun("object")}, {hero.pronoun()} crept forward.'
    )


def approach(world: World, hero: Entity, place: Place, hazard: Hazard) -> None:
    hero.meters["approach"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The boards and weeds near {place.danger_nook} seemed to breathe with the dark."
    )
    world.say(
        f"Then {hazard.risk_text}"
    )


def rescue(world: World, parent: Entity, hero: Entity, cautioner: Entity, hazard: Hazard, aid: SafetyAid, omen: Omen) -> None:
    world.get("danger").meters["risk"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f'{cautioner.id} shouted for {parent.label_word}, and {parent.label_word} came at once with {aid.phrase}. '
        f'{hazard.rescue_text}'
    )
    world.say(
        f'In the safer light, the ghostly shape was only {omen.cause_text}.'
    )


def lesson(world: World, parent: Entity, hero: Entity, cautioner: Entity, hazard: Hazard) -> None:
    for kid in (hero, cautioner):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "Brave does not mean careless," '
        f'{parent.pronoun()} said softly. "{hazard.prevent_text}"'
    )
    world.say(
        f'{hero.id} nodded first. "{hero.pronoun("subject").capitalize()} thought being brave meant going alone," '
        f'{hero.pronoun()} said, "but brave can mean calling for help."'
    )


def safe_return(world: World, hero: Entity, cautioner: Entity, parent: Entity, aid: SafetyAid, place: Place) -> None:
    hero.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"The next evening, {parent.label_word} let them visit {place.label} again, but this time only together and with {aid.phrase}."
    )
    world.say(
        f"{aid.use_text} The corners of the dark stayed only corners."
    )
    world.say(
        f"{hero.id} squeezed {cautioner.id}'s hand, and the place that had seemed haunted looked old and ordinary at last."
    )


def tell(
    place: Place,
    omen: Omen,
    hazard: Hazard,
    aid: SafetyAid,
    *,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    cautioner: str = "Ben",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    watcher = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="danger", type="hazard", label=hazard.label))
    world.facts["hazard_id"] = hazard.id
    hero.memes["bravery"] = BRAVERY_INIT
    watcher.memes["caution"] = initial_caution(trait)
    watcher.memes["trust"] = float(trust)
    world.facts["averted"] = False

    introduce(world, hero, watcher, place)
    spot_omen(world, hero, watcher, omen)

    world.para()
    tempt_bravery(world, hero, place)
    warn(world, hero, watcher, hazard, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    world.facts["averted"] = averted

    if averted:
        back_down(world, hero, watcher, parent, aid, omen)
        world.para()
        lesson(world, parent, hero, watcher, hazard)
        world.para()
        safe_return(world, hero, watcher, parent, aid, place)
        outcome = "averted"
    else:
        defy(world, hero, watcher)
        world.para()
        approach(world, hero, place, hazard)
        rescue(world, parent, hero, watcher, hazard, aid, omen)
        world.para()
        lesson(world, parent, hero, watcher, hazard)
        world.para()
        safe_return(world, hero, watcher, parent, aid, place)
        outcome = "rescued"

    world.facts.update(
        place=place,
        omen=omen,
        hazard=hazard,
        aid=aid,
        instigator=hero,
        cautioner=watcher,
        parent=parent,
        outcome=outcome,
        relation=relation,
        predicted_risk=world.facts.get("predicted_risk", 0.0),
        mishap=hero.meters["shaken"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic stairs",
        intro="The house roof ticked above them, and moonlight lay in pale strips across the steps.",
        ghost_nook="the landing under the rafters",
        danger_nook="the top step by the dusty trunk",
        hazards={"loose_floorboard", "rotted_stairs"},
        tags={"attic", "dark"},
    ),
    "shed": Place(
        id="shed",
        label="the old garden shed",
        intro="The boards smelled of rain, and the latch clicked each time the wind pushed it.",
        ghost_nook="the crooked window",
        danger_nook="the patch of nettles beside the door",
        hazards={"open_well", "thorn_patch"},
        tags={"shed", "yard"},
    ),
    "hall": Place(
        id="hall",
        label="the long upstairs hall",
        intro="The family portraits looked silver in the dimness, and every floorboard answered with a creak.",
        ghost_nook="the end near the curtain",
        danger_nook="the loose runner by the tall mirror",
        hazards={"loose_floorboard", "rotted_stairs"},
        tags={"hall", "dark"},
    ),
}

OMENS = {
    "curtain_shape": Omen(
        id="curtain_shape",
        label="curtain shape",
        seen_as="a tall white shape swaying at the window",
        cause_text="a bedsheet hung over a chair beside the curtain",
        sound_text="Each gust made it bow and rise again, almost like someone breathing.",
        works_in={"attic", "hall"},
        tags={"ghost", "sheet"},
    ),
    "rattling_latch": Omen(
        id="rattling_latch",
        label="rattling latch",
        seen_as="a shadow jumping across the shed wall",
        cause_text="the loose latch knocking while ivy scraped the boards",
        sound_text="Rattle, tap, rattle went the sound, quick enough to make small hearts stumble.",
        works_in={"shed"},
        tags={"ghost", "sound"},
    ),
    "owl_cry": Omen(
        id="owl_cry",
        label="owl cry",
        seen_as="a round glow and two bright eyes above the dark",
        cause_text="an owl on the beam with moonlight on its feathers",
        sound_text="A long, hollow cry floated down the passage and made the night feel taller.",
        works_in={"attic", "shed", "hall"},
        tags={"ghost", "owl"},
    ),
}

HAZARDS = {
    "loose_floorboard": Hazard(
        id="loose_floorboard",
        label="a loose floorboard",
        risk_text="a board tipped under one foot, and the floor gave a scary clack.",
        rescue_text="Parent pulled the child back before the foot could sink into the gap between the boards.",
        prevent_text="Old boards can hurt you when you cannot see where you are stepping.",
        severity=2,
        places={"attic", "hall"},
        tags={"floor", "dark"},
    ),
    "rotted_stairs": Hazard(
        id="rotted_stairs",
        label="rotted stairs",
        risk_text="the step sagged with a groan, and one leg slipped through to the knee.",
        rescue_text="Parent steadied the child and lifted the trapped leg free before the wood could break farther.",
        prevent_text="Rotten steps can break all at once, especially in the dark.",
        severity=3,
        places={"attic", "hall"},
        tags={"stairs", "dark"},
    ),
    "open_well": Hazard(
        id="open_well",
        label="an open well hidden by weeds",
        risk_text="the weeds bent aside and showed a round black opening in the ground.",
        rescue_text="Parent caught the child by the shoulders and drew them back from the old well mouth.",
        prevent_text="Hidden holes are never a place for brave guessing.",
        severity=3,
        places={"shed"},
        tags={"well", "yard"},
    ),
    "thorn_patch": Hazard(
        id="thorn_patch",
        label="a thorn patch",
        risk_text="thorns grabbed at a sleeve and scratched the child's hand.",
        rescue_text="Parent eased the child free and brushed the prickly branches away from the path.",
        prevent_text="Dark corners can hide sharp things that do not care how brave you feel.",
        severity=2,
        places={"shed"},
        tags={"thorns", "yard"},
    ),
}

AIDS = {
    "lantern_and_parent": SafetyAid(
        id="lantern_and_parent",
        label="lantern and parent",
        phrase="a bright lantern",
        use_text="The lantern showed every board and every weed clearly.",
        covers={"loose_floorboard", "rotted_stairs", "open_well", "thorn_patch"},
        tags={"lantern", "adult"},
    ),
    "flashlight_and_parent": SafetyAid(
        id="flashlight_and_parent",
        label="flashlight and parent",
        phrase="a strong flashlight",
        use_text="The flashlight beam slid over the floor and found every edge before small feet reached it.",
        covers={"loose_floorboard", "thorn_patch"},
        tags={"flashlight", "adult"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ella", "Anna", "Lucy", "Ivy"]
BOY_NAMES = ["Ben", "Tom", "Max", "Eli", "Finn", "Noah", "Sam", "Leo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "quiet"]


def best_aid_for(hazard_id: str) -> SafetyAid:
    options = [aid for aid in AIDS.values() if hazard_id in aid.covers]
    if not options:
        raise StoryError(f"(No safe aid covers hazard {hazard_id}.)")
    return sorted(options, key=lambda a: (-len(a.covers), a.id))[0]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for omen_id, omen in OMENS.items():
            if not omen_fits(place, omen):
                continue
            for hazard_id, hazard in HAZARDS.items():
                if not hazard_in_place(place, hazard):
                    continue
                for aid_id, aid in AIDS.items():
                    if aid_covers_hazard(aid, hazard):
                        combos.append((place_id, omen_id, hazard_id, aid_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str = "attic"
    omen: str = "curtain_shape"
    hazard: str = "loose_floorboard"
    aid: str = "lantern_and_parent"
    instigator: str = "Nora"
    instigator_gender: str = "girl"
    cautioner: str = "Ben"
    cautioner_gender: str = "boy"
    parent: str = "mother"
    trait: str = "careful"
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
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
    "ghost": [(
        "Why can something ordinary look like a ghost at night?",
        "In the dark, your eyes get less detail, so a sheet, bird, or branch can look strange and spooky. Sounds also seem bigger when you cannot see what made them."
    )],
    "lantern": [(
        "What does a lantern help you do?",
        "A lantern makes a steady light so you can see the ground and the corners around you. Seeing clearly helps people stay safe."
    )],
    "flashlight": [(
        "What is a flashlight for?",
        "A flashlight sends a beam of light where you point it. It helps you notice steps, holes, and sharp things before you get too close."
    )],
    "dark": [(
        "Why is walking in the dark risky?",
        "In the dark, it is harder to see edges, gaps, and obstacles. That means your feet can go somewhere unsafe before your brain notices."
    )],
    "stairs": [(
        "Why are broken stairs dangerous?",
        "Broken stairs can crack or sag under your weight. A foot can slip through and make you fall."
    )],
    "well": [(
        "Why is an old well dangerous?",
        "An old well is a deep hole, and weeds can hide it from sight. If someone steps too close, they could fall in."
    )],
    "thorns": [(
        "Why should you be careful around thorn bushes?",
        "Thorns are sharp and can scratch skin or catch clothes. They are harder to notice in dim light."
    )],
    "adult": [(
        "Why should children call a grown-up when something feels scary or unsafe?",
        "A grown-up can bring light, look carefully, and help with dangers a child might miss. Asking for help is a brave safety choice."
    )],
}
KNOWLEDGE_ORDER = ["ghost", "dark", "lantern", "flashlight", "stairs", "well", "thorns", "adult"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["instigator"]
    cautioner = f["cautioner"]
    place = f["place"]
    omen = f["omen"]
    hazard = f["hazard"]
    if f["outcome"] == "averted":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "exempt" and takes place near {place.label}.',
            f"Tell a cautionary story where {hero.id} thinks bravery makes {hero.pronoun('object')} exempt from ordinary fear, but {cautioner.id} stops {hero.pronoun('object')} before {hazard.label} can cause trouble.",
            f"Write a spooky-but-safe story where a ghostly sign turns out to be {omen.cause_text}, and the children learn that asking a grown-up for light is part of being brave.",
        ]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "exempt" and takes place near {place.label}.',
        f"Tell a cautionary story where {hero.id} tries to prove {hero.pronoun('object')} is exempt from fear, creeps toward a ghostly sign, and is saved from {hazard.label}.",
        f"Write a spooky story with a safe ending where a grown-up brings light, explains the ordinary cause, and teaches that bravery is not the same as carelessness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["instigator"]
    cautioner = f["cautioner"]
    parent = f["parent"]
    place = f["place"]
    omen = f["omen"]
    hazard = f["hazard"]
    aid = f["aid"]
    relation = f["relation"]
    pair = pair_noun(hero, cautioner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {cautioner.id}, near {place.label}. Their {parent.label_word} helps them understand what the scary thing really was."
        ),
        (
            "What looked like a ghost?",
            f"They saw {omen.seen_as}. It looked spooky at first because the dark hid the ordinary cause."
        ),
        (
            f'Why did {hero.id} say {hero.pronoun("subject")} was "exempt from babyish shivers"?',
            f"{hero.id} wanted to sound brave and prove the ghostly place did not scare {hero.pronoun('object')}. But the story shows that brave feelings do not make anyone exempt from real danger."
        ),
        (
            f"Why did {cautioner.id} warn {hero.id} not to go closer?",
            f"{cautioner.id} remembered that the dark place could hide {hazard.label}. The warning mattered because the risk was physical, not imaginary."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {hero.id} listened?",
            f"{hero.id} backed away and got a grown-up with {aid.phrase}. In the safer light, the ghostly thing turned out to be {omen.cause_text}."
        ))
    else:
        qa.append((
            f"What happened when {hero.id} crept closer?",
            f"{hazard.risk_text[0].upper()}{hazard.risk_text[1:]} That scared everyone because the danger had been real all along."
        ))
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} came with {aid.phrase} and helped right away. The light and the grown-up's quick action kept the scare from becoming worse."
        ))
    qa.append((
        "What did the children learn at the end?",
        f"They learned that being brave does not mean going alone into the dark. The ending proves the change because they return only together and with {aid.phrase}."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "dark", "adult"} | set(f["aid"].tags) | set(f["hazard"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        omen="curtain_shape",
        hazard="loose_floorboard",
        aid="lantern_and_parent",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        place="shed",
        omen="rattling_latch",
        hazard="open_well",
        aid="lantern_and_parent",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        place="hall",
        omen="owl_cry",
        hazard="rotted_stairs",
        aid="lantern_and_parent",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        place="shed",
        omen="owl_cry",
        hazard="thorn_patch",
        aid="flashlight_and_parent",
        instigator="Anna",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="father",
        trait="sensible",
        instigator_age=6,
        cautioner_age=8,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(place: Optional[Place], omen: Optional[Omen], hazard: Optional[Hazard], aid: Optional[SafetyAid]) -> str:
    if place is not None and omen is not None and not omen_fits(place, omen):
        return f"(No story: {omen.label} does not make sense at {place.label}. Pick an omen that fits that place.)"
    if place is not None and hazard is not None and not hazard_in_place(place, hazard):
        return f"(No story: {hazard.label} is not a reasonable danger at {place.label}.)"
    if hazard is not None and aid is not None and not aid_covers_hazard(aid, hazard):
        return f"(No story: {aid.label} is not enough for {hazard.label}. Choose a safer aid.)"
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "rescued"


ASP_RULES = r"""
omen_fits(P,O) :- place(P), omen(O), omen_place(O,P).
hazard_here(P,H) :- place(P), hazard(H), place_hazard(P,H), hazard_place(H,P).
aid_ok(H,A) :- hazard(H), aid(A), covers(A,H).
valid(P,O,H,A) :- omen_fits(P,O), hazard_here(P,H), aid_ok(H,A).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(rescued) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.hazards):
            lines.append(asp.fact("place_hazard", place_id, hazard_id))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        for place_id in sorted(omen.works_in):
            lines.append(asp.fact("omen_place", omen_id, place_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        for place_id in sorted(hazard.places):
            lines.append(asp.fact("hazard_place", hazard_id, place_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for hazard_id in sorted(aid.covers):
            lines.append(asp.fact("covers", aid_id, hazard_id))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only in clingo:", sorted(set(asp_valid_combos()) - set(valid_combos())))
        print("  only in python:", sorted(set(valid_combos()) - set(asp_valid_combos())))

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story cautionary world: bravery, darkness, and safe help."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    omen = OMENS.get(args.omen) if args.omen else None
    hazard = HAZARDS.get(args.hazard) if args.hazard else None
    aid = AIDS.get(args.aid) if args.aid else None

    if place and omen and not omen_fits(place, omen):
        raise StoryError(explain_rejection(place, omen, None, None))
    if place and hazard and not hazard_in_place(place, hazard):
        raise StoryError(explain_rejection(place, None, hazard, None))
    if hazard and aid and not aid_covers_hazard(aid, hazard):
        raise StoryError(explain_rejection(None, None, hazard, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.omen is None or combo[1] == args.omen)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, omen_id, hazard_id, aid_id = rng.choice(combos)
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    trait = rng.choice(TRAITS)
    trust = rng.randint(0, 10)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        omen=omen_id,
        hazard=hazard_id,
        aid=aid_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    place = PLACES[params.place]
    omen = OMENS[params.omen]
    hazard = HAZARDS[params.hazard]
    aid = AIDS[params.aid]
    if not omen_fits(place, omen):
        raise StoryError(explain_rejection(place, omen, None, None))
    if not hazard_in_place(place, hazard):
        raise StoryError(explain_rejection(place, None, hazard, None))
    if not aid_covers_hazard(aid, hazard):
        raise StoryError(explain_rejection(None, None, hazard, aid))

    world = tell(
        place=place,
        omen=omen,
        hazard=hazard,
        aid=aid,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, omen, hazard, aid) combos:\n")
        for place_id, omen_id, hazard_id, aid_id in combos:
            print(f"  {place_id:6} {omen_id:14} {hazard_id:16} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.omen} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
