#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py
====================================================================================

A standalone storyworld for a small rhyming domain built from the seed words
"supreme", "tassel", and "snorkel".

Premise
-------
A child is dressed for a silly sea parade on dry land: a proud paper crown, a
swinging tassel, and an unnecessary snorkel. The outfit is funny, but one part
is not: the tassel can flop over the child's eyes right when it is time to walk
past a real hazard such as steps or a shiny puddle. A friend predicts the risk,
a grown-up helps choose a fix, and the ending proves whether the child can march
safely or takes a comic tumble.

The world model drives the prose:
- physical meters: swing, block, wobble, danger, tumble
- emotional memes: pride, worry, trust, relief, laughter, lesson

The domain prefers sensible fixes. A weak fix is known to the world but refused
by the common-sense gate unless explicitly curated for a cautionary ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py --venue gym_stage --tassel long
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py --tassel tiny
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py --fix tape_flag
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py --all --qa
    python storyworlds/worlds/gpt-5.4/supreme_tassel_snorkel_suspense_dialogue_humor_rhyming.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Configuration registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    label: str
    place_line: str
    hazard_line: str
    hazard_type: str
    hazard_level: int
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
class Costume:
    id: str
    title: str
    theme_line: str
    ending_line: str
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
class TasselCfg:
    id: str
    label: str
    phrase: str
    swing_line: str
    length_level: int
    blocks_eyes: bool
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
class SnorkelCfg:
    id: str
    label: str
    phrase: str
    joke_line: str
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_blocked_vision(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    crown = world.get("crown")
    venue = world.get("venue")
    if crown.meters["swing"] >= THRESHOLD and crown.attrs.get("blocks_eyes", False):
        sig = ("blocked", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["vision_blocked"] += 1
            hero.memes["worry"] += 1
            out.append("__blocked__")
    if hero.meters["vision_blocked"] >= THRESHOLD and venue.meters["hazard"] >= THRESHOLD:
        sig = ("wobble", venue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["wobble"] += 1
            hero.memes["worry"] += 1
            out.append("__wobble__")
    return out


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["wobble"] >= THRESHOLD and world.facts.get("marching_without_fix", False):
        sig = ("tumble", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["tumble"] += 1
            hero.memes["embarrassed"] += 1
            out.append("__tumble__")
    return out


RULES = [
    Rule(name="blocked_vision", tag="physical", apply=_r_blocked_vision),
    Rule(name="tumble", tag="physical", apply=_r_tumble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def hazard_at_risk(venue: Venue, tassel: TasselCfg, excitement: int) -> bool:
    severity = venue.hazard_level + excitement
    return tassel.blocks_eyes and severity >= 2


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def severity_of(venue: Venue, tassel: TasselCfg, excitement: int) -> int:
    return venue.hazard_level + excitement + max(0, tassel.length_level - 1)


def fix_holds(fix: Fix, venue: Venue, tassel: TasselCfg, excitement: int) -> bool:
    return fix.power >= severity_of(venue, tassel, excitement)


def explain_rejection(venue: Venue, tassel: TasselCfg, excitement: int) -> str:
    if not tassel.blocks_eyes:
        return (
            f"(No story: {tassel.phrase} is too short to flop into the child's eyes, "
            f"so there is no honest suspense at {venue.label}. Pick a longer tassel.)"
        )
    if venue.hazard_level + excitement < 2:
        return (
            f"(No story: the route at {venue.label} is too easy for the tassel to make "
            f"a real problem. Pick a riskier venue or more excitement.)"
        )
    return "(No story: this combination has no meaningful tassel hazard.)"


def explain_fix(fid: str) -> str:
    fx = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, int]]:
    combos = []
    for venue_id, venue in VENUES.items():
        for tassel_id, tassel in TASSELS.items():
            for excitement in EXCITEMENTS:
                if hazard_at_risk(venue, tassel, excitement) and sensible_fixes():
                    combos.append((venue_id, tassel_id, excitement))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_route(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    crown = sim.get("crown")
    sim.facts["marching_without_fix"] = True
    crown.meters["swing"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": hero.meters["vision_blocked"] >= THRESHOLD,
        "wobble": hero.meters["wobble"] >= THRESHOLD,
        "tumble": hero.meters["tumble"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_scene(world: World, hero: Entity, helper: Entity, adult: Entity,
                costume: Costume, tassel: TasselCfg, snorkel: SnorkelCfg, venue: Venue) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"In {venue.place_line}, {hero.id} dressed for the parade with delight, "
        f"a {costume.title} crown tucked on just right."
    )
    world.say(
        f"The crown wore {tassel.phrase}, the child wore {snorkel.phrase}, "
        f"and {helper.id} giggled, \"That snorkel looks brave on dry land in this place!\""
    )
    world.say(
        f'"I am the {costume.title}!" {hero.id} cried. '
        f'"If a fish needs a ruler, I\'m ready!" {hero.pronoun()} sighed with pride.'
    )


def announce_route(world: World, adult: Entity, venue: Venue) -> None:
    world.say(
        f'{adult.label_word.capitalize()} pointed ahead. "{venue.hazard_line}"'
    )


def hurry_beat(world: World, hero: Entity, tassel: TasselCfg, snorkel: SnorkelCfg, excitement: int) -> None:
    hero.memes["eager"] += 1
    world.get("crown").meters["swing"] = float(excitement + 1)
    world.say(
        f"{hero.id} took one eager step, then another with zest; "
        f"{tassel.swing_line} and the snorkel stuck out from {hero.pronoun('possessive')} chest."
    )
    if excitement >= 2:
        world.say(
            f'The snorkel gave a silly bonk. "{snorkel.joke_line}" said {hero.id}, '
            f"though the laugh came out thin."
        )


def warn(world: World, helper: Entity, hero: Entity, venue: Venue) -> None:
    pred = predict_route(world)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_tumble"] = pred["tumble"]
    helper.memes["worry"] += 1
    if pred["tumble"]:
        world.say(
            f'"Wait!" said {helper.id}. "Your tassel may cover your eyes, '
            f'and then you might wobble by the {venue.hazard_type}. '
            f'Funny is fine, but a bump is no prize."'
        )
    else:
        world.say(
            f'"Wait!" said {helper.id}. "Your tassel may cover your eyes, '
            f'and that could make the walk wiggly and wise to revise."'
        )


def choose_fix(world: World, adult: Entity, fix: Fix) -> None:
    world.say(
        f'{adult.label_word.capitalize()} knelt down and said, '
        f'"Let\'s not rush in a muddle. We can keep the joke and still settle the trouble."'
    )
    world.say(
        f'{adult.pronoun().capitalize()} reached for {fix.label} and {fix.text}.'
    )


def succeed(world: World, hero: Entity, helper: Entity, adult: Entity,
            costume: Costume, venue: Venue, fix: Fix) -> None:
    crown = world.get("crown")
    crown.meters["swing"] = 0.0
    hero.meters["vision_blocked"] = 0.0
    hero.meters["wobble"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1
    helper.memes["laughter"] += 1
    adult.memes["pride"] += 1
    world.say(
        f'The tassel stayed high, so the path stayed plain; '
        f'{hero.id} marched on without a wobble or strain.'
    )
    world.say(
        f'"Behold!" cried {hero.id}. "My snorkel is silly, but my steps are supreme!" '
        f'Even {helper.id} bowed to the grand parade theme.'
    )
    world.say(
        f"At the end of the route in {venue.label}, the crowd gave a cheer, "
        f"and {costume.ending_line} shone bright and clear."
    )


def fail_fix(world: World, adult: Entity, fix: Fix) -> None:
    world.say(
        f"{adult.label_word.capitalize()} tried to help, but {fix.fail}."
    )


def tumble(world: World, hero: Entity, helper: Entity, adult: Entity, venue: Venue) -> None:
    world.facts["marching_without_fix"] = True
    propagate(world, narrate=False)
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    adult.memes["calm"] += 1
    if hero.meters["tumble"] >= THRESHOLD:
        world.say(
            f"The tassel flopped low with a swish and a sweep; "
            f"{hero.id} missed the safe mark and took one comic peep."
        )
        world.say(
            f"Then came a soft tumble by the {venue.hazard_type} -- not hard, not mean. "
            f'The snorkel booped the floor and made the silliest sound ever seen.'
        )
        world.say(
            f'"Are you hurt?" asked {helper.id}. "{adult.label_word.capitalize()}?" asked {hero.id} in a squeak. '
            f'"Only startled," said {adult.label_word}. "We fix first, then parade next week."'
        )


def lesson_and_retry(world: World, hero: Entity, helper: Entity, adult: Entity,
                     costume: Costume, fix: Fix) -> None:
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f'{adult.label_word.capitalize()} straightened the crown and said, '
        f'"A joke can stay jolly when safety comes first."'
    )
    world.say(
        f'{hero.id} nodded. "A supreme parade needs eyes that can see." '
        f'So they used {fix.label}, and the next slow march went splendidly.'
    )
    world.say(
        f"By sunset the child could grin, wave, and rhyme with ease; "
        f"{costume.ending_line}, with the tassel behaving in the breeze."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(venue: Venue, costume: Costume, tassel: TasselCfg, snorkel: SnorkelCfg,
         fix: Fix, hero_name: str = "Milo", hero_gender: str = "boy",
         helper_name: str = "Nora", helper_gender: str = "girl",
         adult_type: str = "teacher", excitement: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_type, role="adult"))
    crown = world.add(Entity(
        id="crown",
        kind="thing",
        type="crown",
        label="crown",
        phrase=f"a paper crown with {tassel.label}",
        attrs={"blocks_eyes": tassel.blocks_eyes, "length_level": tassel.length_level},
    ))
    snorkel_ent = world.add(Entity(
        id="snorkel",
        kind="thing",
        type="snorkel",
        label=snorkel.label,
        phrase=snorkel.phrase,
    ))
    venue_ent = world.add(Entity(
        id="venue",
        kind="thing",
        type="venue",
        label=venue.label,
        attrs={"hazard_type": venue.hazard_type},
    ))
    venue_ent.meters["hazard"] = float(venue.hazard_level)
    world.facts["marching_without_fix"] = False

    setup_scene(world, hero, helper, adult, costume, tassel, snorkel, venue)
    announce_route(world, adult, venue)

    world.para()
    hurry_beat(world, hero, tassel, snorkel, excitement)
    warn(world, helper, hero, venue)

    world.para()
    choose_fix(world, adult, fix)
    safe = fix_holds(fix, venue, tassel, excitement)
    if safe:
        succeed(world, hero, helper, adult, costume, venue, fix)
        outcome = "safe"
    else:
        fail_fix(world, adult, fix)
        tumble(world, hero, helper, adult, venue)
        world.para()
        lesson_and_retry(world, hero, helper, adult, costume, FIXES["comb_clip"])
        outcome = "tumble"

    world.facts.update(
        hero=hero,
        helper=helper,
        adult=adult,
        venue_cfg=venue,
        costume=costume,
        tassel_cfg=tassel,
        snorkel_cfg=snorkel,
        fix=fix,
        outcome=outcome,
        excitement=excitement,
        severity=severity_of(venue, tassel, excitement),
        safe=(outcome == "safe"),
        tumbled=(outcome == "tumble"),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "gym_stage": Venue(
        id="gym_stage",
        label="the school gym stage",
        place_line="the bright school gym before the class parade",
        hazard_line="Mind the low steps by the stage",
        hazard_type="stage steps",
        hazard_level=2,
        tags={"stage", "steps"},
    ),
    "library_aisle": Venue(
        id="library_aisle",
        label="the library aisle",
        place_line="the library during the silly sea march",
        hazard_line="Mind the rolling cart near the narrow aisle",
        hazard_type="book cart",
        hazard_level=1,
        tags={"library", "cart"},
    ),
    "hall_puddle": Venue(
        id="hall_puddle",
        label="the hall by the rain mat",
        place_line="the hall where umbrellas dripped by the door",
        hazard_line="Mind the shiny puddle by the rain mat",
        hazard_type="puddle",
        hazard_level=2,
        tags={"hall", "puddle"},
    ),
}

COSTUMES = {
    "shell_supreme": Costume(
        id="shell_supreme",
        title="Supreme Shell Ruler",
        theme_line="shells and songs",
        ending_line="the cardboard crown looked small no more",
        tags={"crown", "parade"},
    ),
    "bubble_boss": Costume(
        id="bubble_boss",
        title="Bubble Boss Supreme",
        theme_line="bubbles and blubs",
        ending_line="the bubble banner bobbed by the door",
        tags={"crown", "parade"},
    ),
    "reef_royal": Costume(
        id="reef_royal",
        title="Supreme Reef Royal",
        theme_line="reefs and giggles",
        ending_line="the whole room clapped for the reefy roar",
        tags={"crown", "parade"},
    ),
}

TASSELS = {
    "long": TasselCfg(
        id="long",
        label="a long gold tassel",
        phrase="a long gold tassel that tickled one eyebrow",
        swing_line="the tassel swayed left, then right, then low",
        length_level=2,
        blocks_eyes=True,
        tags={"tassel", "vision"},
    ),
    "super_long": TasselCfg(
        id="super_long",
        label="a very long purple tassel",
        phrase="a very long purple tassel that brushed the child's nose",
        swing_line="the tassel swung wide like a jumpy rope show",
        length_level=3,
        blocks_eyes=True,
        tags={"tassel", "vision"},
    ),
    "tiny": TasselCfg(
        id="tiny",
        label="a tiny silver tassel",
        phrase="a tiny silver tassel no bigger than a thumb",
        swing_line="the tassel gave one little wiggle and stayed",
        length_level=0,
        blocks_eyes=False,
        tags={"tassel"},
    ),
}

SNORKELS = {
    "striped": SnorkelCfg(
        id="striped",
        label="striped snorkel",
        phrase="a striped snorkel that made no sense indoors",
        joke_line="If a whale appears in the hallway, I shall be ready",
        tags={"snorkel", "humor"},
    ),
    "sparkly": SnorkelCfg(
        id="sparkly",
        label="sparkly snorkel",
        phrase="a sparkly snorkel much too fancy for the floor",
        joke_line="This is for surprise puddle oceans",
        tags={"snorkel", "humor"},
    ),
    "giant": SnorkelCfg(
        id="giant",
        label="giant snorkel",
        phrase="a giant snorkel taller than the child's shoulder",
        joke_line="If the gym turns to sea, I shall simply breathe",
        tags={"snorkel", "humor"},
    ),
}

FIXES = {
    "comb_clip": Fix(
        id="comb_clip",
        label="a bright shell comb clip",
        sense=3,
        power=4,
        text="clipped the tassel high against the crown band",
        fail="even the clip slipped loose at the first brisk bounce",
        qa_text="used a shell comb clip to hold the tassel up",
        tags={"clip", "safety"},
    ),
    "ribbon_tie": Fix(
        id="ribbon_tie",
        label="a blue ribbon tie",
        sense=3,
        power=3,
        text="looped the tassel back with a neat blue ribbon tie",
        fail="the ribbon knot loosened and the tassel slid down again",
        qa_text="tied the tassel back with a blue ribbon",
        tags={"ribbon", "safety"},
    ),
    "sticker_star": Fix(
        id="sticker_star",
        label="a sticky paper star",
        sense=2,
        power=2,
        text="pressed the tassel aside with a sticky paper star",
        fail="the paper star peeled up and stopped holding the tassel",
        qa_text="used a sticky paper star to pin the tassel aside",
        tags={"sticker", "safety"},
    ),
    "tape_flag": Fix(
        id="tape_flag",
        label="a floppy bit of tape",
        sense=1,
        power=1,
        text="stuck the tassel down with a floppy bit of tape",
        fail="the tape curled at once and the tassel popped free",
        qa_text="tried to hold the tassel down with tape",
        tags={"tape"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ruby", "Ivy", "Zoe", "Pia", "Ava"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Jude", "Eli", "Max", "Leo"]
EXCITEMENTS = [0, 1, 2]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    venue: str
    costume: str
    tassel: str
    snorkel: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    excitement: int = 1
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "tassel": [
        (
            "What is a tassel?",
            "A tassel is a bunch of strings tied together at one end. People put tassels on hats, clothes, or decorations so they can sway and look fancy.",
        )
    ],
    "snorkel": [
        (
            "What is a snorkel for?",
            "A snorkel is a tube people use to breathe while floating face-down in water. It is silly to wear one in a dry hallway, which is why it felt funny in the story.",
        )
    ],
    "steps": [
        (
            "Why do steps need careful walking?",
            "Steps change height, so you need to see where your feet are going. If something blocks your eyes, you can wobble or trip.",
        )
    ],
    "puddle": [
        (
            "Why can a puddle be slippery?",
            "A puddle can make the floor smooth and slick. Shoes may slide if you hurry without looking.",
        )
    ],
    "clip": [
        (
            "What does a clip do?",
            "A clip holds something in place so it does not flop around. In a costume, that can help keep hair, ribbons, or a tassel out of your eyes.",
        )
    ],
    "ribbon": [
        (
            "Why tie something back with a ribbon?",
            "A ribbon can gather loose things and hold them neatly. That helps keep them from swinging where they should not.",
        )
    ],
    "sticker": [
        (
            "Can a sticker hold something safely?",
            "Sometimes a sticker can hold a very light thing for a little while. But it is weaker than a clip or tie, so it may peel away.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tassel", "snorkel", "steps", "puddle", "clip", "ribbon", "sticker"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    venue = f["venue_cfg"]
    tassel = f["tassel_cfg"]
    snorkel = f["snorkel_cfg"]
    outcome = f["outcome"]
    if outcome == "safe":
        return [
            f'Write a rhyming story for a 3-to-5-year-old that includes the words "supreme", "tassel", and "snorkel". Make it funny, suspenseful, and kind.',
            f"Tell a humorous rhyming story where {hero.label} wears a silly {snorkel.label}, but {helper.label} notices a dangerous {tassel.label} before the walk through {venue.label}.",
            f"Write a playful parade story in rhyme where a child looks supreme, nearly gets in trouble because of a tassel, and then marches safely after a clever fix.",
        ]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "supreme", "tassel", and "snorkel". Use suspense, dialogue, and gentle humor.',
        f"Tell a rhyming cautionary story where {hero.label} hurries in a silly snorkel, a tassel drops over {hero.pronoun('possessive')} eyes, and there is one comic tumble before the grown-up fixes it.",
        f"Write a funny parade story in rhyme where a costume stays silly but the child learns not to rush when a tassel blocks the way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    venue = f["venue_cfg"]
    tassel = f["tassel_cfg"]
    snorkel = f["snorkel_cfg"]
    costume = f["costume"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child in a {costume.title} costume, {helper.label} who noticed the problem, and {adult.label_word} who helped fix it.",
        ),
        (
            f"Why was the {snorkel.label} funny?",
            f"The snorkel was funny because everyone was on dry land, not in the sea. That silly detail made the parade playful even while the real problem came from the tassel.",
        ),
        (
            f"Why did {helper.label} tell {hero.label} to wait?",
            f"{helper.label} saw that the tassel could flop over {hero.label}'s eyes near the {venue.hazard_type}. That mattered because if {hero.label} could not see clearly, {hero.pronoun('subject')} might wobble or tumble.",
        ),
    ]
    if f["outcome"] == "safe":
        qa.extend(
            [
                (
                    f"How did {adult.label_word} solve the problem?",
                    f"{adult.label_word.capitalize()} {fix.qa_text}. That kept the tassel out of {hero.label}'s eyes, so the child could march safely and still look funny and grand.",
                ),
                (
                    f"How did the story end?",
                    f"It ended with {hero.label} walking safely through {venue.label} and hearing cheers. The ending image proves what changed: the child still wore the silly snorkel, but the tassel no longer caused trouble.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What happened when the fix did not hold?",
                    f"The weak fix failed, so the tassel dropped low and {hero.label} took a soft comic tumble by the {venue.hazard_type}. Nobody was badly hurt, but the scare showed why seeing the path mattered.",
                ),
                (
                    f"What did {hero.label} learn after the tumble?",
                    f"{hero.label} learned that even a supreme costume has to be safe enough to see through. After that, the child used a stronger fix and marched more slowly.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tassel_cfg"].tags) | set(world.facts["snorkel_cfg"].tags)
    venue = world.facts["venue_cfg"]
    fix = world.facts["fix"]
    if "steps" in venue.tags:
        tags.add("steps")
    if "puddle" in venue.tags:
        tags.add("puddle")
    tags |= set(fix.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
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
        shown_attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated stories
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        venue="gym_stage",
        costume="shell_supreme",
        tassel="long",
        snorkel="striped",
        fix="ribbon_tie",
        hero_name="Milo",
        hero_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        adult="teacher",
        excitement=1,
    ),
    StoryParams(
        venue="hall_puddle",
        costume="reef_royal",
        tassel="super_long",
        snorkel="giant",
        fix="comb_clip",
        hero_name="Ava",
        hero_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        adult="mother",
        excitement=1,
    ),
    StoryParams(
        venue="library_aisle",
        costume="bubble_boss",
        tassel="long",
        snorkel="sparkly",
        fix="sticker_star",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        adult="teacher",
        excitement=0,
    ),
    StoryParams(
        venue="gym_stage",
        costume="bubble_boss",
        tassel="super_long",
        snorkel="giant",
        fix="sticker_star",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        adult="father",
        excitement=2,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hazard(V, T, E) :- venue(V), tassel(T), excitement(E), blocks_eyes(T), hazard_level(V,H), H + E >= 2.
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(V, T, E) :- venue(V), tassel(T), excitement(E), hazard(V, T, E).

severity(V, T, E, H + E + L - 1) :-
    hazard_level(V,H), chosen_tassel(T), length_level(T,L), chosen_excite(E).

holds :- chosen_fix(F), power(F,P), chosen_venue(V), chosen_tassel(T), chosen_excite(E), severity(V,T,E,S), P >= S.
outcome(safe) :- holds.
outcome(tumble) :- not holds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("hazard_level", venue_id, venue.hazard_level))
    for tassel_id, tassel in TASSELS.items():
        lines.append(asp.fact("tassel", tassel_id))
        if tassel.blocks_eyes:
            lines.append(asp.fact("blocks_eyes", tassel_id))
        lines.append(asp.fact("length_level", tassel_id, tassel.length_level))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    for excitement in EXCITEMENTS:
        lines.append(asp.fact("excitement", excitement))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_tassel", params.tassel),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_excite", params.excitement),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not all(
        [
            params.venue in VENUES,
            params.tassel in TASSELS,
            params.fix in FIXES,
        ]
    ):
        return "?"
    return "safe" if fix_holds(FIXES[params.fix], VENUES[params.venue], TASSELS[params.tassel], params.excitement) else "tumble"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sensible = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: python={sorted(py_sensible)} asp={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for p in mismatches[:5]:
            print(" ", p)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test story rendered empty.")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a supreme costume, a swinging tassel, and a silly snorkel."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--tassel", choices=TASSELS)
    ap.add_argument("--snorkel", choices=SNORKELS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father", "teacher"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--excitement", type=int, choices=EXCITEMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="show Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tassel and args.excitement is not None and args.venue:
        if not hazard_at_risk(VENUES[args.venue], TASSELS[args.tassel], args.excitement):
            raise StoryError(explain_rejection(VENUES[args.venue], TASSELS[args.tassel], args.excitement))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.tassel is None or combo[1] == args.tassel)
        and (args.excitement is None or combo[2] == args.excitement)
    ]
    if not combos:
        if args.venue and args.tassel and args.excitement is not None:
            raise StoryError(explain_rejection(VENUES[args.venue], TASSELS[args.tassel], args.excitement))
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, tassel_id, excitement = rng.choice(sorted(combos))
    costume_id = args.costume or rng.choice(sorted(COSTUMES))
    snorkel_id = args.snorkel or rng.choice(sorted(SNORKELS))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    adult = args.adult or rng.choice(["mother", "father", "teacher"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)

    return StoryParams(
        venue=venue_id,
        costume=costume_id,
        tassel=tassel_id,
        snorkel=snorkel_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        excitement=excitement,
    )


def _validate_params(params: StoryParams) -> None:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.costume not in COSTUMES:
        raise StoryError(f"(Unknown costume: {params.costume})")
    if params.tassel not in TASSELS:
        raise StoryError(f"(Unknown tassel: {params.tassel})")
    if params.snorkel not in SNORKELS:
        raise StoryError(f"(Unknown snorkel: {params.snorkel})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.adult not in {"mother", "father", "teacher"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")
    if params.excitement not in EXCITEMENTS:
        raise StoryError(f"(Bad excitement: {params.excitement})")
    venue = VENUES[params.venue]
    tassel = TASSELS[params.tassel]
    if not hazard_at_risk(venue, tassel, params.excitement):
        raise StoryError(explain_rejection(venue, tassel, params.excitement))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        venue=VENUES[params.venue],
        costume=COSTUMES[params.costume],
        tassel=TASSELS[params.tassel],
        snorkel=SNORKELS[params.snorkel],
        fix=FIXES[params.fix],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        excitement=params.excitement,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("helper", params.helper_name),
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
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, tassel, excitement) combos:\n")
        for venue, tassel, excitement in combos:
            print(f"  {venue:12} {tassel:10} excitement={excitement}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.venue} ({p.tassel}, {p.fix}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
