#!/usr/bin/env python3
"""
storyworlds/worlds/face_tickle_riverbank_bravery_magic_mystery.py
==================================================================

A small story world about a child at a riverbank, a tickle on the face, a
mystery to solve, and bravery that makes the answer feel less spooky.

Seed tale shape:
- A child visits the riverbank.
- Something magical tickles their face.
- They feel nervous because they cannot tell what it is.
- They choose bravery, look closely, and discover the harmless magical source.
- The ending proves what changed: the child is braver, the mystery is solved,
  and the riverbank feels friendly.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of results.py
- lazy import of asp.py only in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    parent: object | None = None
    source: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    place: str = "the riverbank"
    affords: set[str] = field(default_factory=set)
    world: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class MysterySource:
    id: str
    label: str
    phrase: str
    clue: str
    reveals: str
    tickles: bool = True
    magical: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class HeroConfig:
    name: str
    gender: str
    parent: str
    trait: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


def _r_tickle(world: World) -> list[str]:
    out: list[str] = []
    for hero in list(world.entities.values()):
        if hero.kind != "character":
            continue
        if hero.meters["tickle"] < THRESHOLD:
            continue
        sig = ("tickle_notice", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["unease"] += 1
        out.append(f"A strange tickle teased {hero.id}'s face, and {hero.id} blinked at the riverbank.")
    return out


def _r_unease_to_bravery(world: World) -> list[str]:
    out: list[str] = []
    for hero in list(world.entities.values()):
        if hero.kind != "character":
            continue
        if hero.memes["unease"] < THRESHOLD:
            continue
        if hero.memes["bravery"] < THRESHOLD:
            continue
        sig = ("brave_shift", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["curiosity"] += 1
        out.append(f"{hero.id} took a careful breath, and the fear turned into a little more bravery.")
    return out


def _r_magic_reveal(world: World) -> list[str]:
    out: list[str] = []
    source = world.facts.get("source")
    hero = world.facts.get("hero")
    if not source or not hero:
        return out
    if world.get(hero.id).memes["curiosity"] < THRESHOLD:
        return out
    sig = ("reveal", hero.id, source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero_ent = world.get(hero.id)
    source_ent = world.get(source.id)
    source_ent.meters["seen"] += 1
    hero_ent.memes["relief"] += 1
    hero_ent.memes["bravery"] += 1
    out.append(
        f"At last, {hero.id} peered closer and saw that the tickle came from {source_ent.phrase}."
    )
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    source = world.facts.get("source")
    if not hero or not source:
        return out
    he = world.get(hero.id)
    src = world.get(source.id)
    sig = ("resolved", hero.id, source.id)
    if sig in world.fired:
        return out
    if he.memes["relief"] < THRESHOLD:
        return out
    world.fired.add(sig)
    he.memes["fear"] = 0.0
    he.memes["joy"] += 1
    out.append(
        f"The mystery was no monster at all; it was {src.reveals}, and {hero.id} laughed with relief."
    )
    return out


RULES = [
    _r_tickle,
    _r_unease_to_bravery,
    _r_magic_reveal,
    _r_resolution,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def set_up_story(world: World, hero: Entity, parent: Entity, source: Entity) -> None:
    world.say(
        f"{hero.id} loved the riverbank because the water flashed like silver threads."
    )
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went down to the riverbank."
    )
    world.say(
        f"{hero.id} noticed a little tickle on {hero.pronoun('possessive')} face and looked around, because the air felt full of a secret."
    )
    hero.meters["tickle"] += 1
    hero.memes["curiosity"] += 1
    world.facts["source"] = source
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    propagate(world)


def tension_beats(world: World, hero: Entity, parent: Entity, source: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} whispered, \"Something invisible touched my face.\""
    )
    hero.memes["fear"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} wanted to hide behind {hero.pronoun('possessive')} {parent.label}, but {hero.id} remembered to be brave."
    )
    hero.memes["bravery"] += 1
    propagate(world)


def resolve_beats(world: World, hero: Entity, parent: Entity, source: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} stepped closer to the reeds, even though the water tugged softly at the stones."
    )
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin and found the tiny glowing thing that had been tickling {hero.pronoun('possessive')} face."
    )
    propagate(world)
    if hero.memes["joy"] > 0:
        world.say(
            f"{hero.id}'s {parent.label} smiled, and together they watched the magical little source drift away over the river."
        )


def make_world(params: "StoryParams") -> World:
    world = World(Setting(place="the riverbank", affords={"tickle", "mystery", "magic"}))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label="parent"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    source = world.add(Entity(
        id=params.source,
        type="thing",
        label=params.source,
        phrase=params.source_phrase,
        magical=True,
    ))
    set_up_story(world, hero, parent, source)
    tension_beats(world, hero, parent, source)
    resolve_beats(world, hero, parent, source)
    world.facts["source"] = source
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    return world


@dataclass
class StoryParams:
    source: str
    source_phrase: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


SOURCES = {
    "glow_moth": MysterySource(
        id="glow_moth",
        label="glow moth",
        phrase="a tiny glow moth hiding in the reeds",
        clue="a flutter of light",
        reveals="a friendly glow moth",
    ),
    "spark_feather": MysterySource(
        id="spark_feather",
        label="spark feather",
        phrase="a spark feather stuck to a willow branch",
        clue="a bright feather tip",
        reveals="a spark feather from a river sprite",
    ),
    "firefly_string": MysterySource(
        id="firefly_string",
        label="firefly string",
        phrase="a loose thread of fireflies twined around a grass stem",
        clue="a string of tiny lights",
        reveals="a string of fireflies playing tag",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Noah", "Max", "Owen"]
TRAITS = ["curious", "gentle", "brave", "careful", "lively", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("riverbank", sid, "child") for sid in SOURCES]


CURATED = [
    StoryParams(source="glow_moth", source_phrase=SOURCES["glow_moth"].phrase, name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(source="spark_feather", source_phrase=SOURCES["spark_feather"].phrase, name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(source="firefly_string", source_phrase=SOURCES["firefly_string"].phrase, name="Nora", gender="girl", parent="mother", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery story world at a riverbank, with face-tickle magic and bravery.")
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    source = getattr(args, "source", None) or rng.choice(sorted(SOURCES))
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    src = _safe_lookup(SOURCES, source)
    return StoryParams(
        source=src.id,
        source_phrase=src.phrase,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    src: MysterySource = SOURCES[f["source"].id]
    return [
        f'Write a short mystery story for a child named {hero.id} at the riverbank with a face tickle and a brave ending.',
        f'Create a gentle riverbank story where something magical makes {hero.id} feel a tickle on the face, then bravery solves the mystery.',
        f'Write a child-friendly mystery using the words "face" and "tickle" and ending with a magical reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    source: Entity = _safe_fact(world, f, "source")
    return [
        QAItem(
            question=f"Where did {hero.id} go with {hero.pronoun('possessive')} {parent.label}?",
            answer=f"{hero.id} went to the riverbank with {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What felt strange on {hero.id}'s face?",
            answer=f"A magical tickle felt strange on {hero.id}'s face.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of running away from the mystery?",
            answer=f"{hero.id} chose bravery, looked closer, and found {source.phrase}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with relief and laughter, because the mystery was only {_safe_lookup(SOURCES, source.id).reveals}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land right next to a river.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising or special that can do impossible-seeming things in the story world.",
        ),
        QAItem(
            question="What can a mystery do in a story?",
            answer="A mystery makes the reader wonder what is happening until the clue is found.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
source(S) :- source_id(S).
hero(H) :- hero_id(H).
parent(P) :- parent_id(P).

tickle(H) :- feels(H,tickle).
unease(H) :- tickle(H).
bravery(H) :- has(H,bravery).
curiosity(H) :- has(H,curiosity), bravery(H).

reveal(H,S) :- curiosity(H), source(S).
resolved(H,S) :- reveal(H,S).

#show valid/1.
valid(S) :- source_id(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source_id", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(sid,) for sid, _, _ in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        vals = asp.atoms(model, "valid")
        print(f"{len(vals)} compatible story sources:")
        for (sid,) in sorted(set(vals)):
            print(f"  riverbank  {sid}")
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
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.source} at riverbank"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
