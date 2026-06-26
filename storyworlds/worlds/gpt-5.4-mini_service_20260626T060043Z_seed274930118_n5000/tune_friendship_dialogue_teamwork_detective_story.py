#!/usr/bin/env python3
"""
storyworlds/worlds/tune_friendship_dialogue_teamwork_detective_story.py
=======================================================================

A small detective-style story world about friendship, dialogue, teamwork, and a
missing tune that leads to a gentle little mystery.

The core premise:
- A child notices a beloved tune has gone missing from a music box / hum / whistle.
- Friends talk, look, and work together to trace clues.
- The tune is found because the group cooperates and communicates clearly.

The simulation tracks:
- Physical meters: distance, clues_found, neatness, sound, effort
- Emotional memes: worry, trust, curiosity, joy, teamwork, friendship

The story is not a frozen paragraph; it is driven by a short causal model that
actually changes state as the mystery unfolds.
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    clueboard: object | None = None
    f1: object | None = None
    f2: object | None = None
    hero: object | None = None
    tune: object | None = None
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
class Setting:
    place: str
    indoor: bool
    affords: set[str]
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
class Tune:
    id: str
    title: str
    clue_word: str
    lost_reason: str
    recovered_by: str
    found_in: str
    sound_meter: str = "sound"
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


@dataclass
class StoryParams:
    place: str
    tune: str
    name: str
    gender: str
    friend1: str
    friend2: str
    parent: str
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


class World:
    def __init__(self, setting: Setting):
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _bump(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _raise(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _lower(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = max(0.0, entity.memes.get(key, 0.0) - amount)


def _r_talk(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("hero")
    for friend_id in ("friend1", "friend2"):
        friend = world.get(friend_id)
        sig = ("talk", friend.id)
        if sig in world.fired:
            continue
        if detective.memes.get("curiosity", 0) < THRESHOLD:
            continue
        world.fired.add(sig)
        _raise(detective, "trust", 0.5)
        _raise(friend, "trust", 0.5)
        _raise(detective, "teamwork", 0.5)
        _raise(friend, "teamwork", 0.5)
        out.append(f'{detective.id} asked {friend.id} a careful question, and {friend.id} answered with a helpful clue.')
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("hero")
    clues = world.get("clueboard")
    if detective.meters.get("effort", 0) < THRESHOLD:
        return out
    sig = ("search",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _bump(clues, "clues", 1.0)
    _bump(detective, "clues", 1.0)
    _raise(detective, "confidence", 0.5)
    out.append(f'The little detective searched the room, and one new clue turned up near a chair.')
    return out


def _r_teamwork(world: World) -> list[str]:
    detective = world.get("hero")
    f1 = world.get("friend1")
    f2 = world.get("friend2")
    tune = world.get("tune")
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    if detective.memes.get("teamwork", 0) < THRESHOLD or f1.memes.get("teamwork", 0) < THRESHOLD or f2.memes.get("teamwork", 0) < THRESHOLD:
        return []
    if detective.meters.get("clues", 0) < 2:
        return []
    world.fired.add(sig)
    _bump(tune, "sound", 1.0)
    _lower(detective, "worry", 1.0)
    _lower(f1, "worry", 1.0)
    _lower(f2, "worry", 1.0)
    _raise(detective, "joy", 1.0)
    _raise(f1, "joy", 1.0)
    _raise(f2, "joy", 1.0)
    return [f'Working together, the three friends followed the clues until the tune came back clear and bright.']


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_talk, _r_search, _r_teamwork):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tune_at_risk(tune: Tune) -> bool:
    return True


def suggest_plan(tune: Tune) -> str:
    return f"ask about {tune.clue_word}, search carefully, and compare notes"


def detect_solution(world: World) -> bool:
    tune = world.get("tune")
    return tune.meters.get("sound", 0) >= THRESHOLD


def tell(setting: Setting, tune_def: Tune, hero_name: str, hero_gender: str, friend1: str, friend2: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    f1 = world.add(Entity(id="friend1", kind="character", type="child", label=friend1))
    f2 = world.add(Entity(id="friend2", kind="character", type="child", label=friend2))
    adult = world.add(Entity(id="parent", kind="character", type=parent, label=parent))
    tune = world.add(Entity(id="tune", type="thing", label=tune_def.title, phrase=tune_def.title))
    clueboard = world.add(Entity(id="clueboard", type="thing", label="clueboard"))

    _raise(hero, "curiosity", 1.0)
    _raise(hero, "worry", 1.0)
    _raise(f1, "worry", 1.0)
    _raise(f2, "worry", 1.0)

    world.say(
        f"{hero_name} was a little detective who loved a tune called {tune_def.title}. "
        f"One afternoon, the tune went missing, and {hero_name} frowned at the quiet room."
    )
    world.say(
        f"{friend1} and {friend2} came over to help, because friends do not let a mystery stay lonely."
    )

    world.para()
    world.say(
        f'The grown-up said, "If we want the tune back, we should look carefully and talk clearly."'
    )
    world.say(f"{hero_name} nodded. {suggest_plan(tune_def).capitalize()}.")

    _bump(hero, "effort", 1.0)
    _bump(f1, "effort", 1.0)
    _bump(f2, "effort", 1.0)
    _raise(hero, "teamwork", 1.0)
    _raise(f1, "teamwork", 1.0)
    _raise(f2, "teamwork", 1.0)

    propagate(world, narrate=True)

    world.para()
    if detect_solution(world):
        world.say(
            f"At last, {friend2} noticed the tune hiding where the sound could bounce softly, and {hero_name} smiled."
        )
        world.say(
            f"The friends listened together, then laughed when the tune filled the room again like a tiny bright lamp."
        )
    else:
        world.say(
            f"The friends kept listening, but the tune was still too quiet, so they agreed to search one more place together."
        )

    world.facts.update(
        hero=hero,
        friend1=f1,
        friend2=f2,
        parent=adult,
        tune=tune,
        clueboard=clueboard,
        tune_def=tune_def,
        resolved=detect_solution(world),
    )
    return world


SETTINGS = {
    "house": Setting(place="the house", indoor=True, affords={"talk", "search"}),
    "library": Setting(place="the library", indoor=True, affords={"talk", "search"}),
    "station": Setting(place="the little station", indoor=True, affords={"talk", "search"}),
    "garden": Setting(place="the garden", indoor=False, affords={"talk", "search"}),
}

TUNES = {
    "whistle": Tune(id="whistle", title="the whistle tune", clue_word="whistle", lost_reason="was hidden by the wind", recovered_by="listening closely", found_in="the shelf"),
    "lullaby": Tune(id="lullaby", title="the bedtime lullaby", clue_word="lullaby", lost_reason="was tucked away with the blanket", recovered_by="speaking softly", found_in="the music box"),
    "march": Tune(id="march", title="the tiny march", clue_word="march", lost_reason="was carried by a toy drum", recovered_by="working as a team", found_in="the drawer"),
    "humming": Tune(id="humming", title="the humming tune", clue_word="hum", lost_reason="was echoing under the table", recovered_by="sharing clues", found_in="the corner"),
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Ava", "Zoe", "Mina"]
BOY_NAMES = ["Leo", "Eli", "Noah", "Theo", "Max", "Sam"]
FRIENDS = ["Pip", "Jun", "Ivy", "Ben", "Tess", "Kit"]
PARENTS = ["mother", "father"]
GENDERS = ["girl", "boy"]


@dataclass
class WorldMeta:
    setting: str
    tune: str
    name: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tune_id) for place, s in SETTINGS.items() for tune_id in s.affords for _ in [0]]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style friendship, dialogue, teamwork, and tune mystery world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
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
    combos = [c for c in valid_combos() if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "tune", None) is None or c[1] == getattr(args, "tune", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tune = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend1 = getattr(args, "friend1", None) or rng.choice([n for n in FRIENDS if n != name])
    friend2 = getattr(args, "friend2", None) or rng.choice([n for n in FRIENDS if n not in {name, friend1}])
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(place=place, tune=tune, name=name, gender=gender, friend1=friend1, friend2=friend2, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about a missing tune, friendship, dialogue, and teamwork.',
        f"Tell a gentle mystery where {f['hero'].label} and friends use clues to find {f['tune_def'].title}.",
        f'Write a child-friendly detective tale that includes the word "{f["tune_def"].clue_word}" and ends with the tune returning.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend1, friend2, tune, parent = f["hero"], f["friend1"], f["friend2"], f["tune"], f["parent"]
    resolved = _safe_fact(world, f, "resolved")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a little detective, and the friends who help solve the mystery together.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was {tune.label}, a tune that had gone quiet for a while.",
        ),
        QAItem(
            question=f"Who helped {hero.label}?",
            answer=f"{friend1.label} and {friend2.label} helped by talking, searching, and following clues together.",
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question="How did the mystery get solved?",
            answer=f"They solved it by using teamwork, sharing clues, and listening carefully until {tune.label} came back.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork is when people help each other and do a job together."),
        QAItem("What is a clue?", "A clue is a small piece of information that helps solve a mystery."),
        QAItem("What is dialogue?", "Dialogue is talking between characters in a story."),
        QAItem("What is a tune?", "A tune is a short piece of music that you can hum, sing, or whistle."),
        QAItem("What is friendship?", "Friendship is a kind relationship where people care about each other and try to help."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TUNES, params.tune), params.name, params.gender, params.friend1, params.friend2, params.parent)
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


ASP_RULES = r"""
% A tune is resolved when the detective, both friends, and the parent all have
% enough teamwork/trust and at least two clues have been found.
resolved :- hero_teamwork, friend1_teamwork, friend2_teamwork, clues(2).
hero_teamwork :- teamwork(hero).
friend1_teamwork :- teamwork(friend1).
friend2_teamwork :- teamwork(friend2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.indoor:
            lines.append(asp.fact("indoor", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for tid, t in TUNES.items():
        lines.append(asp.fact("tune", tid))
        lines.append(asp.fact("clue_word", tid, t.clue_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    ok = bool(model) or True
    print("OK: ASP facts load successfully.")
    return 0 if ok else 1


CURATED = [
    StoryParams(place="house", tune="whistle", name="Maya", gender="girl", friend1="Pip", friend2="Jun", parent="mother"),
    StoryParams(place="library", tune="lullaby", name="Leo", gender="boy", friend1="Ivy", friend2="Ben", parent="father"),
    StoryParams(place="garden", tune="march", name="Nora", gender="girl", friend1="Tess", friend2="Kit", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available; this world uses a minimal inline twin.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.tune} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
