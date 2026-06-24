#!/usr/bin/env python3
"""
storyworlds/worlds/script_constipate_rejoice_transformation_humor_mystery.py
=============================================================================

A small standalone storyworld for a mystery-tinged, humorous transformation tale.

Seed sketch:
- A child finds a strange script backstage.
- The script seems to cause a transformation.
- A silly clue with the word "constipate" turns out to be a misunderstanding.
- The ending lands in relief and rejoice.

The world is built from stateful entities with physical meters and emotional memes,
a tiny causal engine, a reasonableness gate, an inline ASP twin, and a story-driven
renderer that keeps the tone child-facing and mysterious.
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



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    hero: object | None = None
    page: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    indoor: bool = True
    clue_spot: str = "backstage"
    affords: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class ScriptProp:
    id: str
    phrase: str
    clue_word: str
    transformation: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Transformation:
    id: str
    label: str
    before: str
    after: str
    trigger: str
    visible: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class HumorBeat:
    id: str
    setup: str
    punch: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def _r_confess(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue", "")
    if clue and not world.facts.get("confessed"):
        detective = world.get("hero")
        if detective.memes["curiosity"] >= THRESHOLD:
            sig = ("confess",)
            if sig not in world.fired:
                world.fired.add(sig)
                world.facts["confessed"] = True
                detective.memes["relief"] += 1
                out.append("The clue finally made sense.")
    return out


CAUSAL_RULES = [Rule("confess", "social", _r_confess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def script_at_risk(prop: ScriptProp, transformation: Transformation) -> bool:
    return prop.transformation == transformation.id


def select_transformation(prop: ScriptProp) -> Optional[Transformation]:
    for t in TRANSFORMATIONS:
        if t.id == prop.transformation:
            return t
    return None


def clue_is_reasonable(clue_word: str) -> bool:
    return clue_word in {"script", "constipate", "rejoice"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            if script_at_risk(prop, TRANSFORMATIONS_BY_ID[prop.transformation]):
                combos.append((sid, pid))
    return combos


def whisper(world: World, hero: Entity, prop: ScriptProp) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} found a thin script tucked behind a curtain in {world.setting.place}. "
        f"The pages smelled like dust and fresh glue."
    )
    world.say(
        f"One line kept repeating the word “{prop.clue_word},” which sounded odd and a little funny."
    )


def inspect(world: World, hero: Entity, prop: ScriptProp, tf: Transformation) -> None:
    world.say(
        f"{hero.id} held the script closer. It mentioned {tf.before}, but the margin sketch showed {tf.after}."
    )
    world.say(
        f"That was the mystery: the script looked like a clue, but it also looked like a promise."
    )


def transform(world: World, hero: Entity, tf: Transformation) -> None:
    hero.meters["changed"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"Then the stage lights blinked once, and {hero.id} felt {tf.visible}."
    )
    world.say(
        f"In a blink, {hero.pronoun()} was {tf.after}, not {tf.before}."
    )


def joke(world: World, hero: Entity, prop: ScriptProp, humor: HumorBeat) -> None:
    world.say(humor.setup.format(name=hero.id, clue=prop.clue_word))
    world.say(humor.punch)


def rejoice(world: World, hero: Entity, prop: ScriptProp, tf: Transformation) -> None:
    hero.memes["joy"] += 2
    world.say(
        f"{hero.id} laughed in relief. The strange word was only part of the script, not a problem."
    )
    world.say(
        f"{hero.id} and the others could rejoice, because the transformation had turned the scene from confusing to wonderful."
    )
    world.say(
        f"At the end, the script still lay open on the table, and {tf.after} smiled at the neat little mystery it had solved."
    )


def tell(setting: Setting, prop: ScriptProp, tf: Transformation, humor: HumorBeat,
         hero_name: str = "Mina", hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    page = world.add(Entity(id="script", type="thing", label="the script"))
    world.facts["clue"] = prop.clue_word
    world.facts["prop"] = prop
    world.facts["transformation"] = tf
    world.facts["humor"] = humor
    world.facts["hero"] = hero
    world.facts["page"] = page

    whisper(world, hero, prop)
    inspect(world, hero, prop, tf)
    world.para()
    joke(world, hero, prop, humor)
    transform(world, hero, tf)
    propagate(world, narrate=True)
    world.para()
    rejoice(world, hero, prop, tf)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "theater": Setting(place="the little theater", indoor=True, clue_spot="backstage", affords={"script"}),
    "library": Setting(place="the quiet library stage corner", indoor=True, clue_spot="between shelves", affords={"script"}),
    "attic": Setting(place="the dusty attic rehearsal room", indoor=True, clue_spot="under a trunk", affords={"script"}),
}

PROPS = {
    "script": ScriptProp(
        id="script",
        phrase="a folded script with blue ink",
        clue_word="script",
        transformation="costume",
        effect="a change in outfit",
        tags={"script", "mystery"},
    ),
    "constipate": ScriptProp(
        id="constipate",
        phrase="a silly script page with the odd word",
        clue_word="constipate",
        transformation="badge",
        effect="a comic change in appearance",
        tags={"constipate", "humor"},
    ),
    "rejoice": ScriptProp(
        id="rejoice",
        phrase="a bright script page with a happy chorus",
        clue_word="rejoice",
        transformation="crown",
        effect="a cheerful change in appearance",
        tags={"rejoice", "humor"},
    ),
}

TRANSFORMATIONS = [
    Transformation(
        id="costume",
        label="costume",
        before="plain and ordinary",
        after="wearing a detective cape and a paper star badge",
        trigger="the stage lights blinked",
        visible="a little more like a clue-solver",
        tags={"transformation", "mystery"},
    ),
    Transformation(
        id="badge",
        label="badge",
        before="all serious",
        after="wearing a funny badge with tiny bells",
        trigger="a page rustled",
        visible="suddenly extra cheerful",
        tags={"transformation", "humor"},
    ),
    Transformation(
        id="crown",
        label="crown",
        before="quiet and careful",
        after="wearing a paper crown with a silver moon",
        trigger="the script flipped itself open",
        visible="ready to smile",
        tags={"transformation", "rejoice"},
    ),
]

TRANSFORMATIONS_BY_ID = {t.id: t for t in TRANSFORMATIONS}

HUMOR = {
    "constipate": HumorBeat(
        id="constipate",
        setup="{name} frowned at the strange word “{clue}.” It sounded so serious that it became funny.",
        punch="Then a turtle-shaped prop fell over with a soft thump, as if it had been listening too.",
        tags={"humor", "constipate"},
    ),
    "rejoice": HumorBeat(
        id="rejoice",
        setup="A tiny squeak came from the curtain, as if the room itself were trying not to laugh.",
        punch="Even the dusty lamp seemed to grin.",
        tags={"humor", "rejoice"},
    ),
    "script": HumorBeat(
        id="script",
        setup="{name} tapped the script and said, “Maybe it is trying to tell us a joke.”",
        punch="The paper stayed silent, which somehow made it funnier.",
        tags={"humor", "script"},
    ),
}

NAMES = ["Mina", "Ivy", "Jules", "Owen", "Nora", "Theo", "Lena", "Beau"]
TRAITS = ["curious", "careful", "bright", "quiet", "cheerful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    prop: ScriptProp = f["prop"]
    tf: Transformation = f["transformation"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the word "{prop.clue_word}" and ends with a happy change.',
        f"Tell a gentle story where {hero.id} finds a strange script in {world.setting.place} and it leads to {tf.label} transformation.",
        f'Write a funny, child-friendly mystery with a script, a clue, and a moment of rejoice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prop: ScriptProp = f["prop"]
    tf: Transformation = f["transformation"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found a script tucked away backstage, and it looked like it wanted to solve a mystery.",
        ),
        QAItem(
            question=f"What odd word did the script keep repeating?",
            answer=f"It kept repeating the word “{prop.clue_word},” which sounded strange and a little funny.",
        ),
        QAItem(
            question=f"What did the script seem to cause?",
            answer=f"It seemed to cause a {tf.label} transformation, turning {hero.id} into {tf.after}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["prop"].tags) | set(world.facts["transformation"].tags) | set(world.facts["humor"].tags)
    bank = {
        "script": QAItem(
            question="What is a script?",
            answer="A script is a page of words that tells actors what to say and do in a play.",
        ),
        "constipate": QAItem(
            question="Why can a silly word make a story funny?",
            answer="A silly word can surprise people, and surprise often makes a story feel funny.",
        ),
        "rejoice": QAItem(
            question="What does it mean to rejoice?",
            answer="To rejoice means to feel very glad and happy.",
        ),
        "transformation": QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or look into another.",
        ),
        "humor": QAItem(
            question="What is humor?",
            answer="Humor is what makes people smile or laugh because something is playful, odd, or surprising.",
        ),
        "mystery": QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is unknown at first and then gets understood.",
        ),
    }
    order = ["script", "constipate", "rejoice", "transformation", "humor", "mystery"]
    return [bank[k] for k in order if k in tags]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    theme: str
    prop: str
    transform: str
    hero: str
    gender: str
    trait: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


CURATED = [
    StoryParams(theme="theater", prop="script", transform="costume", hero="Mina", gender="girl", trait="curious"),
    StoryParams(theme="library", prop="constipate", transform="badge", hero="Owen", gender="boy", trait="careful"),
    StoryParams(theme="attic", prop="rejoice", transform="crown", hero="Lena", gender="girl", trait="cheerful"),
]


ASP_RULES = r"""
at_risk(P,T) :- prop(P), transformation(T), trans_id(P,T).
valid(T,P) :- theme(T), prop(P), at_risk(P, costume).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("theme", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("trans_id", pid, p.transformation))
    for tid, t in TRANSFORMATIONS_BY_ID.items():
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a script, a transformation, and a funny clue.")
    ap.add_argument("--theme", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--transform", choices=TRANSFORMATIONS_BY_ID)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "theme", None) is None or c[0] == getattr(args, "theme", None))
              and (getattr(args, "prop", None) is None or c[1] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    theme, prop = rng.choice(list(combos))
    transform = _safe_lookup(PROPS, prop).transformation
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice([n for n in NAMES if n != ""])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(theme=theme, prop=prop, transform=transform, hero=hero, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.theme), _safe_lookup(PROPS, params.prop), TRANSFORMATIONS_BY_ID[params.transform], HUMOR[params.prop], params.hero, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
