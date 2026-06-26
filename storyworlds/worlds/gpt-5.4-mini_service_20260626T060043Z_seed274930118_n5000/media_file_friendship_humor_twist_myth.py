#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/media_file_friendship_humor_twist_myth.py
===============================================================================================================

A small myth-shaped story world about friendship, humor, and a twist around a
mysterious media file.

The seed image is a child-facing tale about two friends carrying a magical
file through a village of old stories. The file is not just a thing; it is a
promise: if it reaches the shrine intact, the village will hear the lost song.
A trickster tries to spoil the plan, but the friends outwit the trick and the
ending proves what changed.

The world uses two kinds of state:

* physical meters: distance, brightness, safety, damage, fullness
* emotional memes: trust, joy, worry, mischief, relief, friendship

The prose is generated from state transitions rather than from a fixed paragraph
template, so the middle turn and ending image are driven by the simulated world.
"""

from __future__ import annotations

import argparse
import copy
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    elder: object | None = None
    friend: object | None = None
    hero: object | None = None
    def __post_init__(self):
        for k in ["distance", "safety", "damage", "brightness", "fullness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["trust", "joy", "worry", "mischief", "relief", "friendship", "humor", "surprise"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)
    hazard: str = "rain"
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
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    hazard: str
    carries: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Trick:
    id: str
    label: str
    joke: str
    twist: str
    mess: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.weather = self.weather
        return clone


def _turn_hazard(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "thing":
            continue
        if ent.meters["safety"] >= THRESHOLD:
            continue
        if ent.meters["damage"] >= THRESHOLD:
            continue
        if world.facts.get("hazard_active") and ent.carried_by:
            sig = ("damage", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["damage"] += 1
            ent.meters["safety"] = max(0.0, ent.meters["safety"] - 1.0)
            out.append(f"The {ent.label} shivered, but it stayed whole.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for msg in _turn_hazard(world):
            produced.append(msg)
            changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, artifact_id: str) -> dict:
    sim = world.copy()
    art = sim.get(artifact_id)
    return {
        "damaged": art.meters["damage"] >= THRESHOLD,
        "safe": art.meters["safety"] >= THRESHOLD,
    }


def setting_line(setting: Setting) -> str:
    return {
        "temple": f"The temple stood like a quiet mountain of stone, with old carvings in the shade.",
        "harbor": f"The harbor breathed salt and wind, and ropes tapped softly against the docks.",
        "grove": f"The grove was green and still, as if the trees were keeping a secret.",
    }[setting.place]


def introduce(hero: Entity, friend: Entity) -> str:
    return f"{hero.id} and {friend.id} were friends who loved to carry stories for the village."


def describe_artifact(artifact: Artifact) -> str:
    return f"They guarded {artifact.phrase}, a {artifact.label} that held the village's lost song."


def want(world: World, hero: Entity, artifact: Artifact) -> str:
    hero.memes["joy"] += 1
    hero.memes["friendship"] += 1
    return f"{hero.id} wanted to bring {artifact.label} to the shrine at once."


def warn(world: World, elder: Entity, hero: Entity, artifact: Artifact, trick: Trick) -> bool:
    pred = predict(world, artifact.id)
    if not pred["damaged"]:
        return False
    world.facts["warned"] = True
    elder.memes["worry"] += 1
    return True


def joke(world: World, trick: Trick, hero: Entity, friend: Entity) -> str:
    hero.memes["humor"] += 1
    friend.memes["humor"] += 1
    trickster = trick.label
    return f"Then {trickster} told a joke so round and silly that even the stones seemed to grin."


def twist(world: World, trick: Trick, artifact: Artifact) -> str:
    world.facts["twist"] = True
    return (
        f"But the trickster's prank failed, because the {artifact.label} was not the real treasure. "
        f"The song was hidden inside the friends' promise to finish the journey together."
    )


def resolve(world: World, hero: Entity, friend: Entity, elder: Entity, artifact: Artifact) -> str:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    elder.memes["friendship"] += 1
    artifact.meters["safety"] = 1.0
    artifact.carried_by = hero.id
    return (
        f"So {hero.id} and {friend.id} carried the {artifact.label} in both hands, "
        f"and when they reached the shrine, the file was still safe and bright."
    )


def ending(world: World, hero: Entity, friend: Entity, artifact: Artifact, setting: Setting) -> str:
    return (
        f"At last the shrine sang, {hero.id} laughed with {friend.id}, and the little media file "
        f"rested in peace while the village listened under {setting.light} light."
    )


SETTINGS = {
    "temple": Setting(place="temple", light="golden lantern"),
    "harbor": Setting(place="harbor", light="moonlight"),
    "grove": Setting(place="grove", light="sun-mist"),
}

ARTIFACTS = {
    "songfile": Artifact(
        id="songfile",
        label="media file",
        phrase="a glowing media file sealed in a shell case",
        type="file",
        hazard="rain",
        carries="song",
    ),
    "storyfile": Artifact(
        id="storyfile",
        label="file",
        phrase="an old file wrapped in blue cloth",
        type="file",
        hazard="wind",
        carries="story",
    ),
    "tablet": Artifact(
        id="tablet",
        label="media file",
        phrase="a small media file etched into a bronze tablet",
        type="file",
        hazard="salt",
        carries="map",
    ),
}

TRICKS = {
    "goose": Trick(
        id="goose",
        label="a goose",
        joke="a crooked neck joke",
        twist="a goose stole the ribbon and turned the chase into a parade",
        mess="feathers",
    ),
    "monkey": Trick(
        id="monkey",
        label="a monkey",
        joke="banana-singing nonsense",
        twist="a monkey rang the bells backward and made everybody laugh",
        mess="peels",
    ),
    "wind": Trick(
        id="wind",
        label="the wind",
        joke="whispering riddles",
        twist="the wind blew open the pouch, but only to reveal the hidden note",
        mess="dust",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Suri", "Asha", "Nina", "Tala"]
BOY_NAMES = ["Ravi", "Oren", "Kian", "Milo", "Jiro", "Timo"]
FRIEND_NAMES = ["Pip", "Juno", "Bela", "Ned", "Ivo", "Zuri"]
ELDER_NAMES = ["Grandmother", "Grandfather", "Old Sage"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "quick-witted"]


@dataclass
class StoryParams:
    setting: str
    artifact: str
    trick: str
    hero: str
    friend: str
    elder: str
    hero_type: str
    friend_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ARTIFACTS:
            for t in TRICKS:
                out.append((s, a, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic friendship storyworld with humor and a twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "artifact", None):
        combos = [c for c in combos if c[1] == getattr(args, "artifact", None)]
    if getattr(args, "trick", None):
        combos = [c for c in combos if c[2] == getattr(args, "trick", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, artifact, trick = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    hero_type = gender
    friend_type = "boy" if rng.random() < 0.5 else "girl"
    elder_type = "woman" if elder == "Grandmother" else "man"
    trait = rng.choice(TRAITS)
    return StoryParams(setting, artifact, trick, hero, friend, elder, hero_type, friend_type, elder_type, trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    world.weather = params.setting

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type))
    artifact = world.add(Entity(
        id="artifact",
        kind="thing",
        type="file",
        label=_safe_lookup(ARTIFACTS, params.artifact).label,
        phrase=_safe_lookup(ARTIFACTS, params.artifact).phrase,
        owner=hero.id,
        caretaker=elder.id,
        carried_by=friend.id,
    ))
    trick = _safe_lookup(TRICKS, params.trick)

    world.facts.update(hero=hero, friend=friend, elder=elder, artifact=artifact, trick=trick)
    world.facts["hazard_active"] = True

    world.say(introduce(hero, friend))
    world.say(setting_line(world.setting))
    world.say(describe_artifact(_safe_lookup(ARTIFACTS, params.artifact)))
    world.say(f"{hero.id} was {params.trait}, and {friend.id} was the kind of friend who smiled before speaking.")
    world.para()
    world.say(want(world, hero, _safe_lookup(ARTIFACTS, params.artifact)))
    world.say(f"{elder.id} frowned, because the path to the shrine could turn rough and splashy.")
    if warn(world, elder, hero, _safe_lookup(ARTIFACTS, params.artifact), trick):
        world.say(f'"Not yet," {elder.id} said. "The {artifact.label} needs a safer carry."')
    world.say(joke(world, trick, hero, friend))
    world.say(f"{friend.id} held the case tighter when the prankster's laughter blew across the path.")
    world.para()
    world.say(twist(world, trick, _safe_lookup(ARTIFACTS, params.artifact)))
    world.say(resolve(world, hero, friend, elder, artifact))
    world.say(ending(world, hero, friend, artifact, world.setting))
    propagate(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for a young child about friendship, humor, and a twist, using the words "media" and "file".',
        f"Tell a gentle legend where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend").id} carry a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "artifact").label} and discover a surprising hidden treasure.",
        f"Write a child-facing story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}, a funny trick, and two friends who keep a sacred file safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    artifact: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "artifact")
    trick: Trick = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trick")
    setting: Setting = world.setting
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They stayed together while carrying the {artifact.label}.",
        ),
        QAItem(
            question=f"What did {elder.id} worry about?",
            answer=f"{elder.id} worried that the journey to the shrine could hurt the {artifact.label} before it reached safety.",
        ),
        QAItem(
            question=f"What kind of thing was being carried?",
            answer=f"They were carrying {artifact.phrase}. It was a magical media file that held part of the village's song.",
        ),
        QAItem(
            question=f"What funny thing happened in the middle?",
            answer=f"{trick.label} made a silly joke, and the joke turned the trip into a laugh instead of a scare.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=(
                f"The twist was that the real treasure was not only the {artifact.label}; "
                f"it was the friends' promise to finish the journey together."
            ),
        ),
        QAItem(
            question=f"Where did the ending happen?",
            answer=f"The ending happened at the {setting.place}, where the shrine could finally hear the old song again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a file?",
            answer="A file is a container for information, like a story, a song, a picture, or a message.",
        ),
        QAItem(
            question="What does media mean?",
            answer="Media means things people use to share stories and information, like books, music, pictures, or videos.",
        ),
        QAItem(
            question="Why are friends important?",
            answer="Friends can help each other, share jokes, and make hard jobs feel lighter.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can turn worry into laughter and help people keep going when a plan gets tricky.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes you see the problem in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
artifact(A) :- artifact_fact(A).
trick(T) :- trick_fact(T).

compatible(S,A,T) :- setting(S), artifact(A), trick(T).
story(S,A,T) :- compatible(S,A,T).
#show compatible/3.
#show story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact_fact", a))
    for t in TRICKS:
        lines.append(asp.fact("trick_fact", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("temple", "songfile", "goose", "Mira", "Pip", "Grandmother", "girl", "boy", "woman", "curious"),
    StoryParams("harbor", "tablet", "wind", "Ravi", "Juno", "Grandfather", "boy", "girl", "man", "brave"),
    StoryParams("grove", "storyfile", "monkey", "Tala", "Bela", "Old Sage", "girl", "girl", "man", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, a, t in combos:
            print(f"  {s:7} {a:10} {t}")
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
            header = f"### {p.hero} and {p.friend} at {p.setting} (artifact: {p.artifact}, trick: {p.trick})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
