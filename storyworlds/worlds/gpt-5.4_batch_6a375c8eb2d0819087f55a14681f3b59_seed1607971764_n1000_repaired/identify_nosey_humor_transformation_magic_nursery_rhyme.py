#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/identify_nosey_humor_transformation_magic_nursery_rhyme.py
======================================================================================

A standalone story world for a playful nursery-rhyme tale about trying to
identify a nosey little visitor, using magic the wrong way, and ending wiser
and kinder.

The domain:
- A child notices a nosey creature peeking into a window-box or pie sill.
- The child wants to identify the visitor.
- One method is patient and polite; the other is a peeping spell that backfires.
- In the backfire branch, the child is temporarily transformed in a funny way.
- A grown-up helper uses the right reversal charm, and the ending proves the
  child learned to ask before peeking.

This script follows the Storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- Python reasonableness gate plus inline ASP twin
- three QA sets grounded in world state
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "gran", "woman"}
        male = {"boy", "father", "uncle", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "gran": "gran",
            "aunt": "aunt",
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
    place: str
    nook: str
    sill_thing: str
    closing_image: str
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
    track: str
    peep_text: str
    desire: str
    feature: str
    apology: str
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
class Method:
    id: str
    label: str
    safe: bool
    opening: str
    action: str
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
class Transformation:
    id: str
    label: str
    verse: str
    movement: str
    joke: str
    caused_by: str
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
class Remedy:
    id: str
    label: str
    action: str
    fixed: str
    repairs: str
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


def _r_noticed_peeking(world: World) -> list[str]:
    culprit = world.get("culprit")
    hero = world.get("hero")
    if culprit.meters["peeking"] < THRESHOLD:
        return []
    sig = ("noticed_peeking", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    return []


def _r_backfire(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["miscast"] < THRESHOLD:
        return []
    sig = ("backfire", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["transformed"] += 1
    hero.memes["surprise"] += 1
    hero.memes["embarrassment"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["restored"] < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["kindness"] += 1
    hero.memes["embarrassment"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="noticed_peeking", tag="social", apply=_r_noticed_peeking),
    Rule(name="backfire", tag="magic", apply=_r_backfire),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a tidy cottage yard",
        nook="the blue window-box",
        sill_thing="a tray of cooling tarts",
        closing_image="the moon shone on the cottage, and nobody peeped without asking",
        tags={"yard", "home"},
    ),
    "garden": Setting(
        id="garden",
        place="a singing garden path",
        nook="the striped bean arbor",
        sill_thing="a bowl of sugared plums",
        closing_image="the stars winked over the garden, and every nose stayed in its own row",
        tags={"garden"},
    ),
    "bakery": Setting(
        id="bakery",
        place="a little bakery lane",
        nook="the warm back window",
        sill_thing="a plate of jam buns",
        closing_image="the lamps glowed by the bakery, and the buns were safe from poking noses",
        tags={"bakery", "food"},
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        article="a",
        track="a silver-black feather by the sill",
        peep_text="cocked one bright eye at the shiny things",
        desire="anything that glittered",
        feature="beak",
        apology='“I only meant to peep at the sparkle,” chirped the magpie.',
        tags={"bird", "feather", "shiny"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        article="a",
        track="a line of floury pawprints by the crust",
        peep_text="twitched at the smell of crumbs",
        desire="pie crumbs and buttery edges",
        feature="whiskers",
        apology='“I only meant to sniff the crumbs,” squeaked the mouse.',
        tags={"mouse", "crumbs"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        article="a",
        track="a nibbled ribbon near the gate",
        peep_text="stretched its neck over the latch",
        desire="ribbons, leaves, and anything left hanging",
        feature="horns",
        apology='“I only meant to nibble one bit,” bleated the goat.',
        tags={"goat", "gate"},
    ),
}

METHODS = {
    "ask_rhyme": Method(
        id="ask_rhyme",
        label="asking rhyme",
        safe=True,
        opening="a soft asking rhyme",
        action="sang a neat little rhyme instead of poking about",
        tags={"polite", "ask"},
    ),
    "peep_spell": Method(
        id="peep_spell",
        label="peep spell",
        safe=False,
        opening="a prickly peep spell",
        action="whispered a nosey peep spell and leaned much too close",
        tags={"magic", "sneak"},
    ),
}

TRANSFORMATIONS = {
    "beak": Transformation(
        id="beak",
        label="beak",
        verse="Out popped a beak, both bright and sleek.",
        movement="It made every word peck out in tiny clicks",
        joke="and even pudding tasted like it ought to be swallowed with a squawk",
        caused_by="magpie",
        tags={"beak", "bird"},
    ),
    "whiskers": Transformation(
        id="whiskers",
        label="whiskers",
        verse="Out sprang whiskers, quick and spry.",
        movement="They wiggled whenever a pie went by",
        joke="and they tickled so much that giggles burst from the child's nose",
        caused_by="mouse",
        tags={"whiskers", "mouse"},
    ),
    "horns": Transformation(
        id="horns",
        label="horns",
        verse="Up curled horns, two little moons.",
        movement="They bobbed whenever the child tried to bow",
        joke="and one of them caught on the washing line with a very silly twang",
        caused_by="goat",
        tags={"horns", "goat"},
    ),
}

REMEDIES = {
    "feather_flute": Remedy(
        id="feather_flute",
        label="feather flute",
        action="played the feather flute in three soft toots",
        fixed="The beak melted back into an ordinary nose",
        repairs="beak",
        tags={"music", "beak"},
    ),
    "cream_comb": Remedy(
        id="cream_comb",
        label="cream comb",
        action="brushed the air with the cream comb in a gentle curl",
        fixed="The whiskers folded away like moonlit threads",
        repairs="whiskers",
        tags={"comb", "whiskers"},
    ),
    "butter_bell": Remedy(
        id="butter_bell",
        label="butter bell",
        action="rang the butter bell with one buttery ding",
        fixed="The little horns shrank down with a polite pop",
        repairs="horns",
        tags={"bell", "horns"},
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Nell", "Daisy", "Poppy", "Minnie"]
BOY_NAMES = ["Pip", "Toby", "Ned", "Alfie", "Bram", "Milo"]
HELPERS = [
    ("Gran", "gran"),
    ("Aunt May", "aunt"),
    ("Mom", "mother"),
    ("Dad", "father"),
]


def valid_combo(culprit_id: str, transform_id: str, remedy_id: str) -> bool:
    if culprit_id not in CULPRITS or transform_id not in TRANSFORMATIONS or remedy_id not in REMEDIES:
        return False
    return (
        TRANSFORMATIONS[transform_id].caused_by == culprit_id
        and REMEDIES[remedy_id].repairs == transform_id
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for culprit_id in CULPRITS:
        for transform_id in TRANSFORMATIONS:
            for remedy_id in REMEDIES:
                if valid_combo(culprit_id, transform_id, remedy_id):
                    combos.append((culprit_id, transform_id, remedy_id))
    return combos


def predict_outcome(method_id: str) -> str:
    if method_id not in METHODS:
        return "?"
    return "identified" if METHODS[method_id].safe else "transformed"


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {setting.place} lived {hero.id}, who liked to count ladybirds and listen for kettle-song."
    )
    world.say(
        f"By day there was {setting.nook}, and by day there was {setting.sill_thing}, all sweet and neat and bright."
    )


def first_peep(world: World, hero: Entity, culprit: Entity, culprit_cfg: Culprit) -> None:
    culprit.meters["peeking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something nosey made the leaves go tip-tap-tip. {hero.id} saw that {culprit_cfg.article} {culprit_cfg.label} had {culprit_cfg.peep_text}."
    )
    world.say(
        f"{hero.id} longed to identify the peeper at once, for there beside the nook lay {culprit_cfg.track}."
    )


def scheme(world: World, hero: Entity, method: Method) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'“I shall identify this nosey visitor,” said {hero.id}, and chose {method.opening}.'
    )
    world.say(f"{hero.id} {method.action}.")


def polite_reveal(world: World, hero: Entity, culprit: Entity, culprit_cfg: Culprit) -> None:
    hero.memes["kindness"] += 1
    culprit.memes["shame"] += 1
    world.say(
        f"Out from the leaves stepped the {culprit_cfg.label}, plain as jam on toast. {culprit_cfg.apology}"
    )
    world.say(
        f"{hero.id} did not stamp or scold. Instead, {hero.pronoun()} pointed to the sill and said a person should ask before peeping at {culprit_cfg.desire}."
    )


def backfire(world: World, hero: Entity, transform: Transformation) -> None:
    hero.meters["miscast"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But magic dislikes a meddling nose. The rhyme bounced back with a blink and a fizz. {transform.verse}"
    )
    world.say(f"{transform.movement}, {transform.joke}.")


def helper_arrives(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} came along with calm shoes and a knowing smile. {helper.pronoun().capitalize()} took one look and did not laugh until {helper.pronoun()} had first made sure the child was all right."
    )


def helper_explains(world: World, helper: Entity, hero: Entity, culprit_cfg: Culprit) -> None:
    world.say(
        f'“Little one,” said {helper.id}, “you may identify a nosey creature, but you must not peep more nosey than it does. Asking is kinder than prying.”'
    )
    world.say(
        f"As {helper.pronoun()} spoke, the real culprit rustled nearby again, still after {culprit_cfg.desire}."
    )


def fix_magic(world: World, helper: Entity, hero: Entity, remedy: Remedy, culprit_cfg: Culprit) -> None:
    hero.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} {remedy.action}. {remedy.fixed}."
    )
    world.say(
        f"Only then did the {culprit_cfg.label} peep out properly, and everyone could identify it without another muddle."
    )


def ending_safe(world: World, hero: Entity, helper: Entity, culprit_cfg: Culprit, setting: Setting) -> None:
    world.say(
        f"The {culprit_cfg.label} gave a sheepish nod, was offered a proper crumb away from the sill, and promised not to be so nosey tomorrow."
    )
    world.say(
        f"{hero.id} promised to ask first and poke later never. Soon {setting.closing_image}."
    )


def tell(
    setting: Setting,
    culprit_cfg: Culprit,
    method: Method,
    transform_cfg: Transformation,
    remedy_cfg: Remedy,
    hero_name: str = "Mabel",
    hero_type: str = "girl",
    helper_name: str = "Gran",
    helper_type: str = "gran",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.label, role="culprit", label=culprit_cfg.label))
    world.facts["predicted_outcome"] = predict_outcome(method.id)

    introduce(world, hero, setting)
    world.para()
    first_peep(world, hero, culprit, culprit_cfg)
    scheme(world, hero, method)

    world.para()
    if method.safe:
        polite_reveal(world, hero, culprit, culprit_cfg)
        outcome = "identified"
    else:
        backfire(world, hero, transform_cfg)
        helper_arrives(world, helper)
        helper_explains(world, helper, hero, culprit_cfg)
        fix_magic(world, helper, hero, remedy_cfg, culprit_cfg)
        outcome = "transformed"

    world.para()
    ending_safe(world, hero, helper, culprit_cfg, setting)

    world.facts.update(
        hero=hero,
        helper=helper,
        culprit=culprit,
        setting=setting,
        culprit_cfg=culprit_cfg,
        method=method,
        transform_cfg=transform_cfg,
        remedy_cfg=remedy_cfg,
        outcome=outcome,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        restored=hero.meters["restored"] >= THRESHOLD,
        identified=True,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    culprit: str
    method: str
    transformation: str
    remedy: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
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
    "magpie": [
        (
            "Why do magpies like shiny things?",
            "Many magpies notice bright, glittery objects very quickly. They are curious birds, so sparkle catches their eye."
        )
    ],
    "mouse": [
        (
            "Why would a mouse sniff near a pie?",
            "A mouse has a sharp nose and follows food smells. Crumbs and buttery crust can tempt it close."
        )
    ],
    "goat": [
        (
            "Why do goats nibble odd things?",
            "Goats explore with their mouths and will try leaves, paper, or ribbons. That does not mean they should."
        )
    ],
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic is something unusual that makes impossible things happen, like a quick transformation. In stories, it often follows special words or music."
        )
    ],
    "identify": [
        (
            "What does identify mean?",
            "To identify something means to figure out what it is. You notice clues, then name the right thing."
        )
    ],
    "nosey": [
        (
            "What does nosey mean?",
            "Nosey means too curious about something that is not yours. A nosey creature peeps where it should ask first."
        )
    ],
    "beak": [
        (
            "What is a beak?",
            "A beak is the hard mouth part on a bird. Birds use beaks to pick, peck, and carry food."
        )
    ],
    "whiskers": [
        (
            "What are whiskers for?",
            "Whiskers help some animals feel what is near them. They can brush against things before the nose does."
        )
    ],
    "horns": [
        (
            "What are horns?",
            "Horns are hard points that grow on the heads of some animals. They can be curved or straight."
        )
    ],
    "kindness": [
        (
            "Why is asking kinder than peeping?",
            "Asking gives the other person a choice. Peeping pokes into their space without permission."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "identify",
    "nosey",
    "magic",
    "magpie",
    "mouse",
    "goat",
    "beak",
    "whiskers",
    "horns",
    "kindness",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    culprit_cfg = f["culprit_cfg"]
    method = f["method"]
    if method.safe:
        return [
            f'Write a short nursery-rhyme story that uses the words "identify" and "nosey" and features gentle magic.',
            f"Tell a humorous rhyme about {hero.id} trying to identify a nosey {culprit_cfg.label} without being unkind.",
            f"Write a child-facing magical verse where a careful asking rhyme reveals the culprit and ends with better manners.",
        ]
    return [
        f'Write a short nursery-rhyme story that uses the words "identify" and "nosey" and includes humor, magic, and a funny transformation.',
        f"Tell a playful rhyme about {hero.id} trying to identify a nosey {culprit_cfg.label} with a peeping spell that backfires.",
        f"Write a magical nursery-style story where a child pries too hard, changes in a silly way, and learns to ask kindly instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    culprit_cfg = f["culprit_cfg"]
    method = f["method"]
    transform_cfg = f["transform_cfg"]
    remedy_cfg = f["remedy_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who wanted to identify a nosey {culprit_cfg.label}. The story also includes {helper.id}, who helps set things right."
        ),
        (
            "What clue showed that someone had been peeping?",
            f"The clue was {culprit_cfg.track}. That little sign helped {hero.id} know that a visitor had been nosing around the sill."
        ),
        (
            f"Why did {hero.id} want to identify the visitor?",
            f"{hero.id} saw that something had been peeping at {world.setting.sill_thing}. The strange clue made {hero.pronoun()} curious and eager to know exactly who it was."
        ),
    ]
    if outcome == "identified":
        qa.append(
            (
                f"How did {hero.id} solve the mystery?",
                f"{hero.id} used {method.opening} and asked instead of prying. Because the method was gentle, the {culprit_cfg.label} stepped out and could be identified safely."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"The culprit stopped peeping and {hero.id} learned to ask kindly. The ending shows that the sill is peaceful and everyone knows better manners now."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} used the magic the wrong way?",
                f"The peep spell bounced back and gave {hero.pronoun('object')} {transform_cfg.label}. It happened because {hero.pronoun()} tried to pry with nosey magic instead of asking first."
            )
        )
        qa.append(
            (
                f"How did {helper.id} fix the problem?",
                f"{helper.id} used the {remedy_cfg.label} and reversed the transformation. After that, the real {culprit_cfg.label} could be identified properly without any more muddle."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{hero.id} learned that it is fine to identify a mystery, but not fine to be nosey in return. Asking kindly worked better than poking magic into somebody else's business."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"identify", "nosey", "magic", "kindness"}
    culprit_id = f["culprit_cfg"].id
    tags.add(culprit_id)
    if f["outcome"] == "transformed":
        tags.add(f["transform_cfg"].id)

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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        culprit="mouse",
        method="peep_spell",
        transformation="whiskers",
        remedy="cream_comb",
        hero_name="Mabel",
        hero_gender="girl",
        helper_name="Gran",
        helper_type="gran",
        seed=1,
    ),
    StoryParams(
        setting="garden",
        culprit="magpie",
        method="ask_rhyme",
        transformation="beak",
        remedy="feather_flute",
        hero_name="Pip",
        hero_gender="boy",
        helper_name="Aunt May",
        helper_type="aunt",
        seed=2,
    ),
    StoryParams(
        setting="bakery",
        culprit="goat",
        method="peep_spell",
        transformation="horns",
        remedy="butter_bell",
        hero_name="Tilly",
        hero_gender="girl",
        helper_name="Dad",
        helper_type="father",
        seed=3,
    ),
    StoryParams(
        setting="garden",
        culprit="mouse",
        method="ask_rhyme",
        transformation="whiskers",
        remedy="cream_comb",
        hero_name="Ned",
        hero_gender="boy",
        helper_name="Mom",
        helper_type="mother",
        seed=4,
    ),
]


def explain_invalid_combo(culprit_id: str, transformation_id: str, remedy_id: str) -> str:
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    if transformation_id not in TRANSFORMATIONS:
        return f"(No story: unknown transformation '{transformation_id}'.)"
    if remedy_id not in REMEDIES:
        return f"(No story: unknown remedy '{remedy_id}'.)"
    culprit_need = CULPRITS[culprit_id].feature
    if TRANSFORMATIONS[transformation_id].caused_by != culprit_id:
        return (
            f"(No story: a {CULPRITS[culprit_id].label} in this world causes a {culprit_need} mishap, "
            f"not {TRANSFORMATIONS[transformation_id].label}. Pick the matching transformation.)"
        )
    if REMEDIES[remedy_id].repairs != transformation_id:
        return (
            f"(No story: the {REMEDIES[remedy_id].label} fixes {REMEDIES[remedy_id].repairs}, "
            f"not {TRANSFORMATIONS[transformation_id].label}. Pick the matching remedy.)"
        )
    return "(No story: the chosen magic pieces do not fit together.)"


ASP_RULES = r"""
% consistent magic chain
valid_combo(C,T,R) :- culprit(C), transformation(T), remedy(R),
                      causes(C,T), repairs(R,T).

% method outcome
safe_outcome(identified) :- chosen_method(M), safe_method(M).
safe_outcome(transformed) :- chosen_method(M), risky_method(M).

% transformation only matters in risky branch, but the combo itself must fit.
story_ok :- chosen_culprit(C), chosen_transformation(T), chosen_remedy(R), valid_combo(C,T,R).

outcome(identified) :- story_ok, safe_outcome(identified).
outcome(transformed) :- story_ok, safe_outcome(transformed).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("causes", cid, culprit.feature))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        if method.safe:
            lines.append(asp.fact("safe_method", mid))
        else:
            lines.append(asp.fact("risky_method", mid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("repairs", rid, remedy.repairs))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_transformation", params.transformation),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return predict_outcome(params.method)


def smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to identify a nosey visitor in a magical nursery-rhyme tale."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-type", choices=["gran", "aunt", "mother", "father"])
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible culprit/transformation/remedy chains from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _choose_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def _choose_helper(rng: random.Random, helper_type: Optional[str], helper_name: Optional[str]) -> tuple[str, str]:
    if helper_type and helper_name:
        return helper_name, helper_type
    if helper_type and not helper_name:
        for name, htype in HELPERS:
            if htype == helper_type:
                return name, htype
        raise StoryError(f"(No story: unknown helper type '{helper_type}'.)")
    name, htype = rng.choice(HELPERS)
    if helper_name:
        return helper_name, htype
    return name, htype


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    culprit_choice = args.culprit
    transformation_choice = args.transformation
    remedy_choice = args.remedy

    if culprit_choice and transformation_choice and remedy_choice:
        if not valid_combo(culprit_choice, transformation_choice, remedy_choice):
            raise StoryError(explain_invalid_combo(culprit_choice, transformation_choice, remedy_choice))

    combos = [
        combo for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.transformation is None or combo[1] == args.transformation)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    culprit_id, transformation_id, remedy_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    method_id = args.method or rng.choice(sorted(METHODS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _choose_name(rng, hero_gender)
    helper_name, helper_type = _choose_helper(rng, args.helper_type, args.helper_name)

    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        method=method_id,
        transformation=transformation_id,
        remedy=remedy_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        culprit_cfg = CULPRITS[params.culprit]
        method = METHODS[params.method]
        transformation = TRANSFORMATIONS[params.transformation]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter value {err.args[0]!r}.)") from None

    if not valid_combo(params.culprit, params.transformation, params.remedy):
        raise StoryError(explain_invalid_combo(params.culprit, params.transformation, params.remedy))

    world = tell(
        setting=setting,
        culprit_cfg=culprit_cfg,
        method=method,
        transform_cfg=transformation,
        remedy_cfg=remedy,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid_combo/3.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (culprit, transformation, remedy) combos:\n")
        for culprit_id, transformation_id, remedy_id in combos:
            print(f"  {culprit_id:8} {transformation_id:10} {remedy_id}")
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
            header = f"### {p.hero_name}: {p.culprit} with {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
