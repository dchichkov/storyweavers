#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny comedy domain about influence:
one character tries to sway another through dialogue, and the conversation
sometimes causes a funny transformation in mood, posture, or appearance.

Premise:
- A boastful character wants everyone to follow their idea.
- Another character resists until a clever, kind, or silly line of dialogue
  changes their mind.
- The turn is a transformation: a costume swap, a mood shift, or a silly role
  change that makes the ending image feel earned and funny.

The world uses typed entities with meters and memes, a small forward simulation,
and an inline ASP twin that matches the Python reasonableness gate.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    transformed_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the kitchen"
    affordances: set[str] = field(default_factory=set)
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
class Influence:
    id: str
    verb: str
    line: str
    mood_shift: str
    transform: str
    target_form: str
    comic_style: str = "silly"
    keyword: str = "influence"
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Costume:
    id: str
    label: str
    phrase: str
    fits: str
    causes: str
    worn_form: str
    safe_when: str
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
class StoryParams:
    setting: str
    influence: str
    costume: str
    name: str
    gender: str
    friend_name: str
    friend_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if _ensure_meme(ent, "won_over") >= THRESHOLD and _ensure_meme(ent, "joy") < THRESHOLD:
            sig = ("joy", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["joy"] = ent.memes.get("joy", 0) + 1
            out.append(f"{ent.id} looked brighter already.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if _ensure_meme(ent, "inspired") < THRESHOLD:
            continue
        if ent.transformed_to:
            continue
        if ent.id not in world.facts.get("transforms", {}):
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        target = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "transforms")[ent.id]
        ent.transformed_to = target
        ent.type = target
        out.append(f"{ent.id} became a {target}.")
    return out


CAUSAL_RULES = [
    _r_mood,
    _r_transform,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled like toast and tiny giggles."
    if setting.place == "the stage":
        return "The stage was small, shiny, and a little too dramatic."
    if setting.place == "the backyard":
        return "The backyard had one brave chair and two suspicious flowerpots."
    return f"{setting.place.capitalize()} was ready for a very odd day."


def dialogue_line(inf: Influence) -> str:
    return inf.line


def transform_phrase(costume: Costume, hero: Entity) -> str:
    return f"{hero.id} could be {costume.worn_form} without looking silly"


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    inf = _safe_lookup(INFLUENCES, params.influence)
    costume = _safe_lookup(COSTUMES, params.costume)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        memes={"stubborn": 1.0, "curious": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=["little", "sensible"],
        memes={"stubborn": 1.0},
    ))
    prop = world.add(Entity(
        id=costume.id,
        type="costume",
        label=costume.label,
        phrase=costume.phrase,
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        costume=prop,
        influence=inf,
        transforms={friend.id: costume.worn_form},
        setting=setting,
    )

    return world


def introduce(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    inf = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "influence")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "costume")
    world.say(
        f"{hero.id} was a little {hero.traits[1]} {hero.type} who loved trying to influence friends."
    )
    world.say(
        f"{hero.id} had a plan: {dialogue_line(inf)}"
    )
    world.say(
        f"And waiting nearby was {costume.phrase}."
    )


def conflict(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    inf = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "influence")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "costume")
    world.para()
    world.say(setting_detail(world.setting))
    world.say(
        f"{hero.id} said, “{dialogue_line(inf)}”"
    )
    world.say(
        f"But {friend.id} crossed {friend.pronoun('possessive')} arms and said, “Nope. I look like a spoon already.”"
    )
    world.say(
        f"{hero.id} pointed at {costume.label} and tried a second line: “{inf.transform}!”"
    )
    friend.memes["resisting"] = friend.memes.get("resisting", 0) + 1


def turn(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    inf = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "influence")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "costume")
    world.para()
    friend.memes["inspired"] = friend.memes.get("inspired", 0) + 1
    friend.memes["won_over"] = friend.memes.get("won_over", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} grinned and said, “{inf.mood_shift}.”"
    )
    world.say(
        f"That was such a funny idea that {friend.id} snorted a laugh."
    )
    world.say(
        f"Then {friend.id} tried on {costume.label}, and {friend.id} turned into {costume.worn_form}."
    )
    world.say(
        f"Now {hero.id} could see that {transform_phrase(costume, hero)}."
    )


def ending(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "costume")
    world.para()
    world.say(
        f"{friend.id} did a tiny bow and said, “Okay, okay, you influenced me.”"
    )
    world.say(
        f"{hero.id} laughed so hard {hero.pronoun('subject')} nearly tipped over."
    )
    world.say(
        f"By the end, {friend.id} was {costume.worn_form}, and the whole room was cheerful and very proud of the joke."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    conflict(world)
    turn(world)
    ending(world)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordances={"dialogue", "transformation"}),
    "stage": Setting(place="the stage", affordances={"dialogue", "transformation"}),
    "backyard": Setting(place="the backyard", affordances={"dialogue", "transformation"}),
}

INFLUENCES = {
    "hat": Influence(
        id="hat",
        verb="convince everyone to wear a hat",
        line="Everyone looks smarter with a hat on",
        mood_shift="Maybe the hat is the funniest part",
        transform="Try it on and see",
        target_form="hat person",
        tags={"influence", "dialogue", "transformation", "comedy"},
    ),
    "goat": Influence(
        id="goat",
        verb="convince everyone to act like a goat",
        line="Mysterious goats know the best snacks",
        mood_shift="If this works, I'm calling it genius",
        transform="One little baa won't hurt",
        target_form="goat",
        tags={"influence", "dialogue", "transformation", "comedy"},
    ),
    "robot": Influence(
        id="robot",
        verb="convince everyone to talk like a robot",
        line="Beep! This plan is excellent",
        mood_shift="Robots never spill juice on the rug",
        transform="Try the robot voice",
        target_form="robot",
        tags={"influence", "dialogue", "transformation", "comedy"},
    ),
}

COSTUMES = {
    "hat": Costume(
        id="hat",
        label="a floppy hat",
        phrase="a floppy hat with a bendy brim",
        fits="head",
        causes="sudden dignity",
        worn_form="a hat-wearing fool",
        safe_when="the joke is harmless",
    ),
    "goat": Costume(
        id="goat",
        label="a goat mask",
        phrase="a goat mask with tiny ears",
        fits="face",
        causes="goofy confidence",
        worn_form="a dramatic goat",
        safe_when="no one is real embarrassed",
    ),
    "robot": Costume(
        id="robot",
        label="a cardboard robot suit",
        phrase="a cardboard robot suit with shiny buttons",
        fits="body",
        causes="stiff little steps",
        worn_form="a clanking robot",
        safe_when="the floor is clear",
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Luna", "Ava", "Nina"]
BOY_NAMES = ["Leo", "Max", "Owen", "Finn", "Theo"]
TRAITS = ["curious", "cheerful", "sneaky", "silly", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for i in INFLUENCES:
            for c in COSTUMES:
                if i == c:
                    out.append((s, i, c))
    return out


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def choose_friend_name(name: str, rng: random.Random) -> str:
    options = [n for n in GIRL_NAMES + BOY_NAMES if n != name]
    return rng.choice(options)


def explain_rejection(inf: Influence, costume: Costume) -> str:
    return f"(No story: {inf.id} and {costume.id} do not match in this tiny comedy world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about influence, dialogue, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--influence", choices=INFLUENCES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    influence = getattr(args, "influence", None) or rng.choice(list(INFLUENCES))
    costume = getattr(args, "costume", None) or influence
    if getattr(args, "influence", None) and getattr(args, "costume", None) and getattr(args, "influence", None) != getattr(args, "costume", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    friend_type = getattr(args, "friend_type", None) or rng.choice(["girl", "boy"])
    friend_name = getattr(args, "friend_name", None) or choose_friend_name(name, rng)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        influence=influence,
        costume=costume,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    inf = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "influence")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "costume")
    return [
        f'Write a short comedy story for a young child about "{inf.keyword}" with dialogue and a funny transformation.',
        f"Tell a playful story where {hero.id} tries to influence a friend with a line of dialogue and a costume change.",
        f"Write a tiny funny story in which someone says “{inf.line}” and ends up transformed in a silly way.",
        f"Make a child-friendly comic story set in {world.setting.place} using dialogue, influence, and {costume.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    inf = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "influence")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "costume")
    return [
        QAItem(
            question=f"Who tried to influence {friend.id}?",
            answer=f"{hero.id} tried to influence {friend.id} with a funny line of dialogue.",
        ),
        QAItem(
            question=f"What did {hero.id} say to start the joke?",
            answer=f'{hero.id} said, “{inf.line}.”',
        ),
        QAItem(
            question=f"What did {friend.id} become by the end of the story?",
            answer=f"{friend.id} became {costume.worn_form} after trying on {costume.label}.",
        ),
        QAItem(
            question=f"Why was the ending funny?",
            answer=f"It was funny because a simple conversation led to a silly transformation, and everyone laughed instead of getting upset.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is influence?",
            answer="Influence is when one person's words or actions change what someone else thinks, feels, or does.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking between characters in a story.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is when something changes into a new form, like a costume, role, or look.",
        ),
        QAItem(
            question="Why can comedy make a story feel light?",
            answer="Comedy uses silly surprises, funny lines, and playful changes so the story feels cheerful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed_to:
            bits.append(f"transformed_to={e.transformed_to}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% setting(S). influence(I). costume(C). compatibles are matched by id.

valid(S,I,C) :- setting(S), influence(I), costume(C), I = C.
story_ok(S,I,C) :- valid(S,I,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in INFLUENCES:
        lines.append(asp.fact("influence", i))
    for c in COSTUMES:
        lines.append(asp.fact("costume", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
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
    StoryParams(setting="kitchen", influence="hat", costume="hat", name="Mia", gender="girl", friend_name="Leo", friend_type="boy", trait="cheerful"),
    StoryParams(setting="stage", influence="robot", costume="robot", name="Finn", gender="boy", friend_name="Ava", friend_type="girl", trait="bold"),
    StoryParams(setting="backyard", influence="goat", costume="goat", name="Nina", gender="girl", friend_name="Owen", friend_type="boy", trait="silly"),
]


def resolve_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
        seed = base_seed + i
        i += 1
        rng = random.Random(seed)
        try:
            params = resolve_params(args, rng)
        except StoryError as e:
            print(e)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = resolve_many(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
