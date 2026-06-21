#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smiley_cautionary_friendship_conflict_pirate_tale.py
====================================================================================

A standalone storyworld for a small pirate-tale domain with cautionary
friendship/conflict beats. Two young deckhands are playing pirates on a windy
pier. One wants to use a forbidden flame to light a dark hideout; a friend warns
that the sailcloth and tar are close by; the conflict is resolved by calling the
captain and using safe lanterns instead.

This world keeps the story child-facing, state-driven, and compact. The word
"smiley" appears as a named treasure marker and in the ending image.
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
BRAVERY_INIT = 5.5
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_flame: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    age: object | None = None
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
        return {"mother": "mom", "father": "dad", "captain": "captain"}.get(self.type, self.type)
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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    dark_spot: str
    cave_word: str
    role_solo: str
    role_plural: str
    send_off: str
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


@dataclass
class Forbidden:
    id: str
    cry: str
    label: str
    phrase: str
    where: str
    unit: str
    strike: str
    not_toy: str
    plural: bool = True
    makes_flame: bool = True
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
class Hazard:
    id: str
    label: str
    the: str
    near: str
    drape: str
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[:1].upper() + self.the[1:]
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
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
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
    theme: str
    forbidden: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 5
    relation: str = "friends"
    trust: int = 5
    smiley: str = "smiley chest"
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_spread(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "deck" in world.entities:
            world.get("deck").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def hazard_at_risk(forbidden: Forbidden, target: Hazard) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Hazard, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Hazard, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "friends" and cautioner_age > instigator_age
    authority = (5.0 if trait in CAUTIOUS_TRAITS else 3.0) + 1.0 + (2.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {"ignites": sim.get(target_id).meters["burning"] >= THRESHOLD, "danger": sim.get("deck").meters["danger"]}


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, smiley: str) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"On a windy afternoon, {a.id} and {b.id} turned the pier into {theme.scene}. {theme.rig}")
    world.say(f'On a crate sat a little {smiley}, grinning like a lucky coin in the sun.')
    world.say(f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. "Let\'s find {theme.goal}!"')


def need_light(world: World, b: Entity, theme: Theme, target: Hazard) -> None:
    world.say(f"But the {theme.cave_word} -- {theme.dark_spot}, {target.drape} -- swallowed the light from the waves.")
    world.say(f'{b.id} peered inside. "We need a light," {b.pronoun()} said.')


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    world.say(f'{a.id}\'s eyes lit up. "I know! {forbidden.cry} I saw {forbidden.phrase} {forbidden.where}."')
    world.say("For one breath, the idea felt bold and clever.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, target: Hazard, parent: Entity) -> None:
    pred = predict_fire(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = " That could go bad very fast." if pred["danger"] >= 1 else ""
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, we\'re not allowed to touch '
        f'{forbidden.label}. {parent.label_word.capitalize()} said. It can make a real flame, '
        f"and {target.the} can catch."{extra}"
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    them = "them" if forbidden.plural else "it"
    world.say(f'"Don\'t be such a scaredy-cat," {a.id} said, and ran to get {them}.')


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    them = "them" if forbidden.plural else "it"
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said. But {b.id} stood firm, so {a.id} '
        f"looked at {b.pronoun('object')}, thought better of it, and gave up the idea."
    )
    world.say(f"They left {them} right where they were and went to tell {parent.label_word.capitalize()} about the dark {theme.cave_word}.")


def ignite(world: World, target_ent: Entity, forbidden: Forbidden, target: Hazard) -> None:
    _do_forbidden(world, target_ent)
    world.say(
        f"{forbidden.strike} {forbidden.unit[0].upper()}{forbidden.unit[1:]} flared to life. "
        f"For one second it was wonderful, like a tiny lantern. Then the flame leaned, kissed {target.near}, "
        f"and a little line of orange began to climb."
    )


def alarm(world: World, b: Entity, a: Entity, target: Hazard, parent: Entity) -> None:
    world.say(f'"{a.id}! Fire! {target.The}!" {b.id} screamed.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Hazard, theme: Theme) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("deck").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} {body}.")
    world.say(f"The flame hissed and died, leaving only a smoky smell and two very frightened {theme.role_plural}.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden, smiley: str) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I\'m not angry that you are scared," {parent.pronoun()} said softly. '
        f'"I am glad you called me. But you must always remember: {forbidden.not_toy}. '
        f"Fire can grow faster than you can run. Promise me -- never, ever again."'
    )
    world.say(f'"We promise," whispered {b.id} and {a.id} together.')
    world.say(f"The little {smiley} still grinned on the crate, but now it seemed like a safe sign for a safer game.")


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} had a surprise. "
        f"{parent.pronoun().capitalize()} handed them {l1.phrase} that {l1.glow}, and {l2.phrase} that {l2.glow}."
    )
    world.say(f'"Now," {parent.pronoun()} smiled, "what does {theme.role_solo} need to explore a dark {theme.cave_word}?"')
    world.say(f'{a.id} held up the {l2.label}. {b.id} clicked on the {l1.label}.')
    world.say('"Safe light!" they cheered.')
    world.say(f"This time, the {theme.role_plural} {theme.send_off} -- bright, brave, and safe.")


def rescue_fail(world: World, parent: Entity, response: Response, target_ent: Entity, target: Hazard) -> None:
    if "deck" in world.entities:
        world.get("deck").meters["burning"] += 1
    target_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say(f"The flames leapt from {target.the} to the sails and raced along the ropes.")


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"There was no time to be heroes. {parent.label_word.capitalize()} grabbed {a.id} and {b.id} by the hand and rushed them out to the shore."
    )
    world.say("From the dock they watched the mast glow orange, and by the time help came, the little fort was full of smoke.")
    world.say("Their whole game -- the ropes, the flag, every bit of it -- was gone.")


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt in the sand and held them tight. '
        f'"You\'re safe. That\'s all that matters," {parent.pronoun()} whispered.'
    )
    world.say(
        f"But {a.id} and {b.id} never forgot what they learned that day: {forbidden.not_toy}, '
        f'and fire can grow faster than anyone can run."
    )
    world.say("After that, when a game grew too dark, they called a grown-up instead.")


THEMES = {
    "pirate": Theme(
        id="pirate",
        scene="a brave little pirate camp",
        rig="The crate was their ship, a broom became a mast, a coil of rope was treasure, and a torn map showed the way to the cave.",
        captain="Captain",
        mate="Scout",
        goal="the hidden cave",
        dark_spot="the cave mouth",
        cave_word="cave",
        role_solo="a pirate",
        role_plural="pirates",
        send_off="sailed off to hunt the treasure",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a toy harbor full of waves",
        rig="The bench was their deck, a bucket was a cannon, a coil of rope was treasure, and a paper map pointed to the rocks.",
        captain="Captain",
        mate="Mate",
        goal="the rock cave",
        dark_spot="the rock tunnel",
        cave_word="tunnel",
        role_solo="a deckhand",
        role_plural="deckhands",
        send_off="set off to search the bay",
    ),
}

FORBIDDEN = {
    "matches": Forbidden(
        id="matches",
        cry="Matches!",
        label="matches",
        phrase="a box of matches",
        where="under the stool",
        unit="the first match",
        strike="Scritch!",
        not_toy="matches are not toys",
        plural=True,
        makes_flame=True,
        tags={"fire", "call_adult"},
    ),
    "sparkler": Forbidden(
        id="sparkler",
        cry="A sparkler!",
        label="the sparkler",
        phrase="a sparkler stick",
        where="in the lantern crate",
        unit="the spark",
        strike="Fizz!",
        not_toy="sparklers are not toys",
        plural=False,
        makes_flame=True,
        tags={"fire", "call_adult"},
    ),
}

TARGETS = {
    "sail": Hazard(
        id="sail",
        label="sail",
        the="the sailcloth",
        near="the edge of the sail",
        drape="hung with salt-stiff sails",
        spread=3,
        flammable=True,
        tags={"sail", "flammable"},
    ),
    "rope": Hazard(
        id="rope",
        label="rope",
        the="the rope pile",
        near="the dry rope",
        drape="stacked with dry rope",
        spread=2,
        flammable=True,
        tags={"rope", "flammable"},
    ),
    "tarcloth": Hazard(
        id="tarcloth",
        label="tarcloth",
        the="the tarcloth",
        near="the tar cloth",
        drape="covered by a tarcloth",
        spread=2,
        flammable=True,
        tags={"cloth", "flammable"},
    ),
}

SAFE_LIGHTS = {
    "lantern": SafeLight(id="lantern", label="lantern", phrase="a little lantern", glow="glowed warm and safe", tags={"lantern"}),
    "flashlight": SafeLight(id="flashlight", label="flashlight", phrase="a flashlight", glow="shone bright as a star", tags={"flashlight"}),
    "glowstick": SafeLight(id="glowstick", label="glow stick", phrase="a glow stick", glow="shimmered green and gentle", tags={"glowstick"}),
}

RESPONSES = {
    "extinguisher": Response(
        id="extinguisher", sense=3, power=4,
        text="grabbed the fire bucket and smothered the flames until every spark was gone",
        fail="tried to douse the fire with one tiny splash, but the flames were already too big to stop",
        qa_text="grabbed the fire bucket and smothered the flames",
        tags={"bucket", "fire"},
    ),
    "smother": Response(
        id="smother", sense=3, power=3,
        text="pulled the {target} down to the deck, balled it up, and pressed the flames out under a heavy cloak",
        fail="tried to pull the {target} down, but the fire was climbing too fast to smother",
        qa_text="pulled the {target} down and smothered the flames under a heavy cloak",
        tags={"cloth", "fire"},
    ),
    "stomp": Response(
        id="stomp", sense=2, power=2,
        text="pulled the {target} down and stamped on the flames, hard and fast, until they were out",
        fail="stamped at the flames, but they only leapt higher",
        qa_text="pulled the {target} down and stamped the flames out",
        tags={"smother", "fire"},
    ),
    "water_bucket": Response(
        id="water_bucket", sense=1, power=1,
        text="filled a bucket at the pump and threw the water over the {target}",
        fail="threw a bucket of water over the {target}, but it was far too little",
        qa_text="threw a bucket of water over the {target}",
        tags={"water", "fire"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli"]
TRAITS = ["careful", "curious", "steady", "wise", "bold"]

KNOWLEDGE = {
    "matches": [("What are matches?", "Matches are small sticks that make a flame when you scratch them. They are for grown-ups, not for play.")],
    "sparkler": [("What is a sparkler?", "A sparkler is a stick that throws out bright sparks. It can burn skin and start a fire, so children should not use one.")],
    "fire": [("Why is fire dangerous?", "Fire is very hot and can spread faster than you can run. It can burn people and ruin things very quickly.")],
    "sail": [("Why can a sail catch fire easily?", "A sail is made of cloth. Cloth burns, so a flame near a sail can make a big fire fast.")],
    "rope": [("Why is rope dangerous near fire?", "Dry rope can catch fire and help the flames spread to other things.")],
    "call_adult": [("What should you do if something catches fire?", "Get away and call a grown-up right away. Calling for help fast is the safest choice.")],
    "lantern": [("What is a lantern?", "A lantern is a light that glows without an open flame when it uses batteries. It is safe to carry in the dark.")],
    "flashlight": [("What is a flashlight?", "A flashlight is a battery light you switch on with a button. It helps you see without fire.")],
    "glowstick": [("What is a glow stick?", "A glow stick is a bendy stick that shines with a soft light. It is cool and safe to hold.")],
}
KNOWLEDGE_ORDER = ["matches", "sparkler", "fire", "sail", "rope", "call_adult", "lantern", "flashlight", "glowstick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for fb in FORBIDDEN:
            for tg in TARGETS:
                if hazard_at_risk(FORBIDDEN[fb], TARGETS[tg]):
                    combos.append((theme, fb, tg))
    return combos


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == b.type == "boy":
        return "two boy pirates"
    if a.type == b.type == "girl":
        return "two girl pirates"
    return "two pirate friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, fb, th, tg = f["instigator"], f["cautioner"], f["forbidden"], f["theme"], f["target_cfg"]
    l1, l2 = f["lights"]
    outcome = f.get("outcome")
    if outcome == "averted":
        return [
            f'Write a pirate tale for a young child where {a.id} wants to use {fb.label} near {tg.the}, but {b.id} stops the idea before any fire starts. Include the word "smiley".',
            f"Tell a friendly pirate story where two deckhands argue, then choose safe lanterns instead of {fb.label}. Keep it cautious and kind.",
            f'Write a short cautionary friendship story on a pirate ship where a warning helps the friends avoid trouble and the ending shows safe light.',
        ]
    if outcome == "contained":
        return [
            f'Write a pirate tale that includes the word "smiley" and shows {a.id} making a bad choice with {fb.label}, then a grown-up putting the fire out.',
            f"Tell a cautionary friendship story where {b.id} warns about {fb.label}, the fire starts anyway, and the captain fixes it fast.",
            f'Write a child-friendly pirate story with conflict, a scare, and a safe ending where the children learn "{fb.not_toy}".',
        ]
    return [
        f'Write a pirate cautionary story with the word "smiley" where {fb.label} near {tg.the} causes a fire that gets too big to stop.',
        f"Tell a sad but safe pirate story where the ship game burns down after a child ignores a friend and a grown-up's response is too weak.",
        f'Write a story that teaches "{fb.not_toy}" and ends with everyone safe but the little pirate fort gone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    fb, th, tg, resp = f["forbidden"], f["theme"], f["target_cfg"], f["response"]
    l1, l2 = f["lights"]
    pw = parent.label_word
    qa = [
        ("Who is the story about?", f"It is about {pair_noun(a, b)} named {a.id} and {b.id}, plus {pw} who keeps them safe."),
        ("What were the children pretending to do?", f"They turned the deck into {th.scene} and hunted for {th.goal}. The smiley treasure marker made the game feel brave and playful."),
        ("What did {0} want to use for light?".format(a.id), f"{a.id} wanted to use {fb.label}, but {b.id} warned that it was not allowed and could make a real flame."),
        ("Why did {0} warn {1}?".format(b.id, a.id), f"{b.id} knew {fb.label} near {tg.the} could start a fire. {b.id} wanted to protect {a.id}, the ship game, and everyone on the pier."),
    ]
    if f.get("outcome") == "averted":
        qa.append((
            f"What happened after {b.id} warned {a.id}?",
            f"{a.id} listened, gave up the idea, and the friends asked {pw} for safe light instead. No fire ever started, so the game stayed cheerful and calm."
        ))
        qa.append((
            f"What did {pw} give them next?",
            f"{pw.capitalize()} gave them {l1.phrase} and {l2.phrase}. Those lights were bright enough for a dark cave and safe enough for children."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the pirate friends using safe light and smiling beside the little smiley treasure marker. Their friendship stayed strong because they chose caution."
        ))
    elif f.get("outcome") == "contained":
        body = resp.qa_text.replace("{target}", tg.label)
        qa.append((
            f"What happened when {a.id} used {fb.label}?",
            f"{tg.The} caught fire, and the flame climbed fast. The danger came from the flame being near cloth and dry rope."
        ))
        qa.append((
            f"How did {pw} fix the fire?",
            f"{pw.capitalize()} came running and {body}. That stopped the fire before it could eat through the whole deck."
        ))
        qa.append((
            f"How did the children feel at the end?",
            f"They were frightened at first, then relieved when {pw} hugged them and gave the lesson. The ending shows the friends still together, but now much wiser."
        ))
    else:
        fail = resp.fail.replace("{target}", tg.label)
        qa.append((
            f"Could {pw} put the fire out?",
            f"No. {pw.capitalize()} {fail}, and the fire raced through the ship game. It was already too late for that small response."
        ))
        qa.append((
            "How did the story end?",
            f"Everyone got away safely, but the pirate fort burned down. The smiley marker still mattered because it reminded them they had lost a game, not each other."
        ))
        qa.append((
            f"What did {a.id} and {b.id} learn?",
            f"{fb.not_toy.capitalize()}, and fire can grow faster than anyone can run. They learned to call a grown-up when a game turns risky."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forbidden"].tags) | set(f["target_cfg"].tags)
    outcome = f.get("outcome")
    if outcome == "averted":
        tags |= set(f["lights"][0].tags) | set(f["lights"][1].tags)
    elif outcome == "contained":
        tags |= set(f["response"].tags) | set(f["lights"][0].tags) | set(f["lights"][1].tags)
    else:
        tags |= set(f["response"].tags)
    out = []
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
        if e.attrs:
            bits.append(f"attrs={{{', '.join(f'{k}: {v!r}' for k, v in e.attrs.items() if v)}}}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(theme: Theme, forbidden: Forbidden, target: Hazard, lights: tuple[SafeLight, SafeLight], response: Response,
         instigator: str = "Mia", instigator_gender: str = "girl",
         cautioner: str = "Tom", cautioner_gender: str = "boy",
         trait: str = "careful", parent_type: str = "captain",
         delay: int = 0, instigator_age: int = 6, cautioner_age: int = 5,
         relation: str = "friends", trust: int = 5, smiley: str = "smiley chest") -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator", traits=["bold"], age=instigator_age, attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender, role="cautioner", traits=[trait], age=cautioner_age, attrs={"relation": relation}))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, role="parent", label="the captain"))
    world.add(Entity(id="deck", type="room", label="the deck"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0

    tgt = world.add(Entity(id="target", type="target", label=target.label, flammable=target.flammable))
    l1, l2 = lights

    play_setup(world, a, b, theme, smiley)
    need_light(world, b, theme, target)
    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target, parent)

    averted = would_avert(relation, a.age, b.age, trait)
    if averted:
        back_down(world, a, b, forbidden, parent, theme)
        world.para()
        safe_gift(world, parent, a, b, theme, l1, l2)
        severity, contained = 0, True
    else:
        defy(world, a, b, forbidden)
        world.para()
        ignite(world, tgt, forbidden, target)
        alarm(world, b, a, target, parent)
        severity = fire_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, parent, response, tgt, target, theme)
            lesson(world, parent, a, b, forbidden, smiley)
            world.para()
            safe_gift(world, parent, a, b, theme, l1, l2)
        else:
            rescue_fail(world, parent, response, tgt, target)
            escape_and_loss(world, parent, a, b, theme)
            grim_lesson(world, parent, a, b, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        instigator=a, cautioner=b, parent=parent, theme=theme, forbidden=forbidden,
        target_cfg=target, target=tgt, lights=(l1, l2), response=response, outcome=outcome,
        severity=severity, delay=delay, relation=relation, promised=True, smiley=smiley
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate cautionary friendship story world.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["captain", "mother", "father"])
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
    if args.forbidden and args.target:
        if not hazard_at_risk(FORBIDDEN[args.forbidden], TARGETS[args.target]):
            raise StoryError("That flame wouldn't meaningfully threaten that target.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak and too odd for this world.")

    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["friends", "friends", "siblings"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme, forbidden=forbidden, target=target,
        light1=light1, light2=light2, response=response,
        instigator=instigator, instigator_gender=ig,
        cautioner=cautioner, cautioner_gender=cg, parent=parent,
        trait=trait, delay=delay, instigator_age=instigator_age,
        cautioner_age=cautioner_age, relation=relation, trust=trust,
        smiley="smiley chest",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(
            THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
            (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]),
            RESPONSES[params.response],
            params.instigator, params.instigator_gender,
            params.cautioner, params.cautioner_gender,
            params.trait, params.parent, params.delay,
            params.instigator_age, params.cautioner_age, params.relation,
            params.trust, params.smiley,
        )
    except KeyError as err:
        raise StoryError(f"Invalid parameter value: {err}") from err
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
hazard(F, T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T, F, Tg) :- theme(T), forbidden(F), target(Tg), hazard(F, Tg).

averted :- relation(friends), cautioner_older, authority(A), bravery_init(B), A > B.
cautioner_older :- instigator_age(IA), cautioner_age(CA), CA > IA.
authority(A) :- trait(T), cautious(T), A = 6.
authority(A) :- trait(T), not cautious(T), A = 4.

severity(V) :- chosen_target(Tg), spread(Tg, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if f.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", tr))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
        asp.fact("chosen_target", params.target),
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested ordinary generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    cases = [resolve_params(build_parser().parse_args([]), random.Random(s)) for s in range(10)]
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: ASP/Python outcomes match on smoke cases.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome cases differ.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


CURATED = [
    StoryParams(theme="pirate", forbidden="matches", target="sail", light1="lantern", light2="flashlight", response="extinguisher",
                instigator="Lily", instigator_gender="girl", cautioner="Tom", cautioner_gender="boy", parent="captain", trait="careful",
                delay=0, instigator_age=5, cautioner_age=6, relation="friends", trust=7, smiley="smiley chest"),
    StoryParams(theme="harbor", forbidden="sparkler", target="rope", light1="glowstick", light2="lantern", response="smother",
                instigator="Mia", instigator_gender="girl", cautioner="Ben", cautioner_gender="boy", parent="captain", trait="steady",
                delay=1, instigator_age=6, cautioner_age=7, relation="friends", trust=4, smiley="smiley flag"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate cautionary friendship story world.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["captain", "mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.forbidden and args.target and not hazard_at_risk(FORBIDDEN[args.forbidden], TARGETS[args.target]):
        raise StoryError("That forbidden thing would not really threaten that target.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    return StoryParams(
        theme=theme, forbidden=forbidden, target=target, light1=light1, light2=light2,
        response=response, instigator=instigator, instigator_gender=ig,
        cautioner=cautioner, cautioner_gender=cg, parent=args.parent or "captain",
        trait=rng.choice(TRAITS), delay=args.delay if args.delay is not None else rng.randint(0, 2),
        instigator_age=rng.choice([4, 5, 6, 7]), cautioner_age=rng.choice([5, 6, 7]),
        relation=rng.choice(["friends", "friends", "siblings"]), trust=rng.randint(0, 10),
        smiley="smiley chest",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
        (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]), RESPONSES[params.response],
        params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender,
        params.trait, params.parent, params.delay, params.instigator_age, params.cautioner_age,
        params.relation, params.trust, params.smiley,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        for t, f, tg in asp_valid_combos():
            print(f"{t:8} {f:10} {tg}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
