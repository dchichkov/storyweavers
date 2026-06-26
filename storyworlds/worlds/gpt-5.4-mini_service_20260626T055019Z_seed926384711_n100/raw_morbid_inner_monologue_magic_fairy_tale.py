#!/usr/bin/env python3
"""
storyworlds/worlds/raw_morbid_inner_monologue_magic_fairy_tale.py
==================================================================

A small fairy-tale story world with a magical, slightly morbid mood and a
strong inner-monologue beat. The world stays child-facing: the "morbid" part
means moonlit bones, old tombstones, and spooky shadows, not grim content.

Seed tale:
---
In a village at the edge of a dark wood, a small child found a raw, unfinished
wand beside an old gate. The wand whispered a spell that made the night feel
morbid and chilly, and the child worried that the whole garden might stay gloomy
forever.

The child listened to an inner voice, remembered a kind old fairy's lesson, and
used the wand to warm a little lantern, wake the sleeping flowers, and soften
the shadows. By morning, the garden looked enchanted instead of frightening.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
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
            keys = [upper, upper + "S", upper + "ES"]
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    token: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fairy", "queen"}
        male = {"boy", "father", "man", "wizard", "king"}
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
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
class Artifact:
    id: str
    label: str
    phrase: str
    magic: str
    effect: str
    risk: str
    vulnerable: str
    needs: str
    at_home: bool = False
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
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    comforts: set[str]
    use: str
    finish: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "moonlit"

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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _story_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _story_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _moonlit_detail(place: Place) -> str:
    if place.id == "grave_garden":
        return "Silver moonlight lay across the little stones, and the sleepy roses nodded beside the gate."
    if place.id == "old_tower":
        return "The tower windows blinked like stars, and ivy curled over the worn bricks."
    return "The wood was hush-quiet, with pale flowers and a path that glimmered under the moon."


def _fear_line(hero: Entity, artifact: Artifact) -> str:
    return (
        f"{hero.id} held the raw wand very still. Inside {hero.pronoun('possessive')} "
        f"head, {hero.pronoun('subject')} whispered, 'This feels too morbid and too cold. "
        f"What if the spell makes everything sad forever?'"
    )


def _wonder_line(hero: Entity) -> str:
    return (
        f"Then another little thought came along, soft as a firefly: 'A spell can be scary, "
        f"but I can still choose what it means.'"
    )


def _act_use_magic(world: World, hero: Entity, artifact: Artifact, charm: Charm) -> list[str]:
    out: list[str] = []
    sig = ("use", hero.id, artifact.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _story_meter(hero, "magic", 1.0)
    _story_meter(hero, "unease", 1.0)
    _story_meme(hero, "curiosity", 1.0)
    world.say(
        f"{hero.id} lifted the {artifact.label} and spoke the old words. "
        f"The spell felt {artifact.magic}, and at once the air grew {artifact.effect}."
    )
    if world.place.affords and artifact.risk in world.place.affords:
        out.append(f"The place seemed to answer with a hush.")
    return out


def _act_inner_monologue(world: World, hero: Entity, artifact: Artifact, charm: Charm) -> list[str]:
    sig = ("think", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _story_meme(hero, "resolve", 1.0)
    _story_meter(hero, "brave", 1.0)
    world.say(_fear_line(hero, artifact))
    world.say(_wonder_line(hero))
    return []


def _act_use_charm(world: World, hero: Entity, artifact: Artifact, charm: Charm) -> list[str]:
    sig = ("charm", hero.id, charm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _story_meter(hero, "warmth", 1.0)
    _story_meme(hero, "hope", 1.0)
    _story_meme(hero, "fear", -1.0)
    world.say(
        f"With a careful breath, {hero.id} used the {charm.label}. {charm.use} "
        f"Then the {artifact.label} no longer felt so raw, and the gloom started to loosen."
    )
    return []


def _act_resolution(world: World, hero: Entity, artifact: Artifact, charm: Charm) -> list[str]:
    sig = ("resolve", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _story_meter(hero, "joy", 1.0)
    _story_meme(hero, "fear", -1.0)
    world.say(
        f"The wand's last spark turned sweet and gold. {artifact.finish} "
        f"{hero.id} smiled, because the garden looked enchanted now, not eerie."
    )
    world.say(
        f"By morning, the flowers had opened, the shadows were soft, and {hero.id} "
        f"felt proud of {hero.pronoun('possessive')} own brave thought."
    )
    return []


@dataclass
class StoryParams:
    place: str
    artifact: str
    charm: str
    name: str
    gender: str
    role: str
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


PLACES = {
    "grave_garden": Place("grave_garden", "the moon garden", affords={"wand", "lantern"}),
    "old_tower": Place("old_tower", "the old tower", affords={"wand", "mirror"}),
    "forest_edge": Place("forest_edge", "the edge of the dark wood", affords={"wand", "lantern"}),
}

ARTIFACTS = {
    "wand": Artifact(
        "wand",
        "wand",
        "a raw little wand with a branchy handle",
        "raw and prickly",
        "chilly and morbid",
        "gloom",
        "gloomy",
        "warm the night",
        at_home=False,
    ),
    "mirror": Artifact(
        "mirror",
        "mirror",
        "a plain silver mirror with a cloudy face",
        "strange and cold",
        "full of ghostly shapes",
        "shadows",
        "spooky",
        "show kind things",
        at_home=False,
    ),
}

CHARMS = {
    "lantern": Charm(
        "lantern",
        "lantern",
        "a tiny moon lantern",
        guards={"gloom", "shadows"},
        comforts={"fear", "unease"},
        use="Its light made a cozy circle on the ground.",
        finish="The lantern gave one last twinkle, as if it were pleased.",
    ),
    "song": Charm(
        "song",
        "song",
        "a humming charm-song",
        guards={"gloom"},
        comforts={"fear"},
        use="Its tune made the dark feel sleepy instead of sharp.",
        finish="The note faded gently, like a bird settling in a nest.",
    ),
}

NAMES = {
    "girl": ["Mira", "Lina", "Ivy", "Nora", "Elsa"],
    "boy": ["Oren", "Pip", "Felix", "Rowan", "Theo"],
}

ROLES = ["little", "brave", "curious", "gentle"]


def reasonableness_gate(place: Place, artifact: Artifact, charm: Charm) -> bool:
    return artifact.magic in {"raw and prickly", "strange and cold"} and (
        artifact.risk in charm.guards or artifact.vulnerable in charm.guards
    )


def tell(place: Place, artifact: Artifact, charm: Charm, name: str, gender: str, role: str) -> World:
    if not reasonableness_gate(place, artifact, charm):
        pass
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper = world.add(Entity(id="FairyGuide", kind="character", type="fairy", label="the fairy guide"))
    item = world.add(Entity(id=artifact.id, type="thing", label=artifact.label, phrase=artifact.phrase, owner=hero.id, caretaker=helper.id))
    token = world.add(Entity(id=charm.id, type="thing", label=charm.label, phrase=charm.phrase, owner=hero.id))
    world.facts.update(hero=hero, helper=helper, artifact=item, charm=token, role=role, place=place)

    world.say(f"Once, at {place.label}, there was a {role} {gender} named {name}.")
    world.say(f"{name} found {artifact.phrase} near an old gate, where {_moonlit_detail(place)}")
    world.say(
        f"{name} loved magic, yet the wand felt too {artifact.magic}. "
        f"It seemed to breathe {artifact.effect}, and the child gave a tiny shiver."
    )

    world.para()
    _act_use_magic(world, hero, artifact, charm)
    _act_inner_monologue(world, hero, artifact, charm)
    world.say(
        f"Nearby, {helper.label} remembered a kinder spell and placed {charm.phrase} into {name}'s hand."
    )
    _act_use_charm(world, hero, artifact, charm)

    world.para()
    _act_resolution(world, hero, artifact, charm)
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for a in ARTIFACTS.values():
            for c in CHARMS.values():
                if reasonableness_gate(p, a, c):
                    out.append((p.id, a.id, c.id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    artifact = _safe_fact(world, f, "artifact")
    return [
        f'Write a short fairy tale for a child named {hero.id} that includes a {artifact.label} and a gentle inner monologue.',
        f"Tell a moonlit story where {hero.id} finds {artifact.phrase} and learns how a small charm can soften a morbid feeling.",
        f"Write a magical story about courage, where a raw spell is made kind by a thoughtful child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    artifact = _safe_fact(world, f, "artifact")
    charm = _safe_fact(world, f, "charm")
    place = _safe_fact(world, f, "place").label
    return [
        QAItem(
            question=f"What did {hero.id} find at {place}?",
            answer=f"{hero.id} found {artifact.phrase} near the old gate.",
        ),
        QAItem(
            question=f"Why did the child feel worried about the magic?",
            answer=f"The wand felt {artifact.magic}, and its spell made the night seem {artifact.effect}.",
        ),
        QAItem(
            question=f"What helped the story turn from gloomy to gentle?",
            answer=f"The tiny {charm.label} helped soften the spell so the garden could feel safe again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and brave, because {hero.pronoun('subject')} had changed the scary feeling into an enchanted one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives light so you can see in the dark and feel less afraid.",
        ),
        QAItem(
            question="What does it mean when something is raw?",
            answer="If something is raw, it is unfinished, rough, or not fully made yet.",
        ),
        QAItem(
            question="Why can moonlight make a place look magical?",
            answer="Moonlight is soft and silver, so it can make old trees, stones, and flowers look mysterious and beautiful.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_fact(P).
artifact(A) :- artifact_fact(A).
charm(C) :- charm_fact(C).

compatible(P,A,C) :- place(P), artifact(A), charm(C),
                     artifact_risk(A,R), guarded_by(C,R),
                     place_affords(P,AType), artifact_type(A,AType).

valid_story(P,A,C) :- compatible(P,A,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place_fact", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_affords", p.id, a))
    for a in ARTIFACTS.values():
        lines.append(asp.fact("artifact_fact", a.id))
        lines.append(asp.fact("artifact_type", a.id, a.id))
        lines.append(asp.fact("artifact_risk", a.id, a.risk))
    for c in CHARMS.values():
        lines.append(asp.fact("charm_fact", c.id))
        for g in sorted(c.guards):
            lines.append(asp.fact("guarded_by", c.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python reasonableness gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world of raw magic, inner monologue, and a gentle ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "artifact", None) is None or c[1] == getattr(args, "artifact", None))
        and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, artifact, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, artifact=artifact, charm=charm, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ARTIFACTS, params.artifact), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.role)
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


CURATED = [
    StoryParams(place="grave_garden", artifact="wand", charm="lantern", name="Mira", gender="girl", role="curious"),
    StoryParams(place="forest_edge", artifact="mirror", charm="song", name="Oren", gender="boy", role="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, artifact, charm) combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.artifact} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
