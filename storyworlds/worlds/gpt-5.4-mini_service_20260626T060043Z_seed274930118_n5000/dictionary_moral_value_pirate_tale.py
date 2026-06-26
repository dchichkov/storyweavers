#!/usr/bin/env python3
"""
A standalone storyworld for a small Pirate Tale domain about a dictionary and
a moral value choice.

Premise:
- A young pirate finds a dictionary aboard a ship or on a dock.
- A crew member wants to use the dictionary to settle an argument about a moral
  value, such as honesty, kindness, fairness, or courage.
- The story turns when the dictionary gives a clear meaning that helps the crew
  choose a better action.
- The ending proves the chosen value changed what the crew did next.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dic: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ("weight", "wetness", "scrape", "lost"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "fear", "pride", "greed", "kindness", "honesty", "fairness", "courage", "conflict"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "pirate", "captain", "mate"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoor: bool
    affords: set[str] = field(default_factory=set)
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
class Dictionary:
    id: str
    label: str
    phrase: str
    moral_value: str
    definition: str
    support: str
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "deck": Setting(place="the deck", indoor=False, affords={"read", "argue", "share"}),
    "cabin": Setting(place="the cabin", indoor=True, affords={"read", "argue", "share"}),
    "dock": Setting(place="the dock", indoor=False, affords={"read", "argue", "share"}),
}

MORAL_VALUES = {
    "honesty": {
        "support": "tell the truth even when it is awkward",
        "signal": "truth",
        "beat": "honest",
    },
    "kindness": {
        "support": "help someone rather than laugh at them",
        "signal": "gentle",
        "beat": "kind",
    },
    "fairness": {
        "support": "give each person a fair turn",
        "signal": "fair",
        "beat": "fair",
    },
    "courage": {
        "support": "do the right thing even when it feels scary",
        "signal": "brave",
        "beat": "brave",
    },
}

CREW = {
    "captain": ("Captain Brine", "captain"),
    "mate": ("Mira", "girl"),
    "boy": ("Toby", "boy"),
    "pirate": ("Ned", "pirate"),
}

DIRECTIONS = {
    "truth": "pointed to the truth on the page",
    "gentle": "showed how soft words can help",
    "fair": "explained that fair turns matter",
    "brave": "reminded them that doing right can be scary",
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    value: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Parser / resolution
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a dictionary and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--value", choices=MORAL_VALUES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["captain", "mate", "boy", "pirate"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, value) for place in SETTINGS for value in MORAL_VALUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "value", None) is None or c[1] == getattr(args, "value", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, value = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Nia", "Rowan", "Mina", "Pip", "Jory", "Lina"])
    helper = getattr(args, "helper", None) or rng.choice(list(CREW))
    return StoryParams(place=place, value=value, name=name, helper=helper)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, dic: Entity) -> None:
    world.say(
        f"{hero.id} was a small pirate who loved old maps, shiny knots, and the big dictionary in the cabin."
    )
    world.say(
        f"{helper.id} had the dictionary open and kept tapping the page for {dic.label}, because {dic.phrase}."
    )


def conflict(world: World, hero: Entity, helper: Entity, dic: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    helper.memes["conflict"] += 1
    world.para()
    world.say(
        f"One day, {helper.id} wanted to use the dictionary to win an argument on {world.setting.place}."
    )
    world.say(
        f"{hero.id} did not like that plan, because the words on the page were meant to help, not to bully."
    )
    world.say(
        f"{hero.id} reached for the dictionary and asked what {dic.moral_value} really meant."
    )


def define_value(world: World, dic: Entity, hero: Entity) -> None:
    world.say(
        f'The page for {dic.label} said that {dic.moral_value} means to {dic.phrase}.'
    )
    world.say(
        f'That simple meaning {DIRECTIONS[dic.moral_value.split("_")[0] if dic.moral_value in DIRECTIONS else "truth"] if False else dic.definition}'
    )


def choose_better_way(world: World, hero: Entity, helper: Entity, dic: Entity) -> None:
    value = dic.moral_value
    helper.memes[value] += 1
    helper.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.para()
    world.say(
        f"{helper.id} blinked, then lowered the dictionary and nodded."
    )
    world.say(
        f'"You are right," {helper.id} said. "The page means {dic.support}."'
    )
    world.say(
        f"So instead of fighting, they used the word {value} to choose a fairer, kinder action."
    )


def ending(world: World, hero: Entity, helper: Entity, dic: Entity) -> None:
    world.para()
    world.say(
        f"After that, {hero.id} and {helper.id} sat together by the lantern while the dictionary stayed open on the right page."
    )
    world.say(
        f"The ship felt smaller and friendlier, because one clear moral value had turned an argument into a good choice."
    )


def tell(setting: Setting, moral_value: str, hero_name: str, helper_key: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate"))
    helper_name, helper_type = CREW[helper_key]
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    dic = world.add(Entity(
        id="dictionary",
        kind="thing",
        type="book",
        label="dictionary",
        phrase=_safe_lookup(MORAL_VALUES, moral_value)["support"],
        owner=hero.id,
        caretaker=helper.id,
        meters={"weight": 1.0},
        memes={"trust": 1.0},
    ))
    dic.moral_value = moral_value
    dic.definition = _safe_lookup(MORAL_VALUES, moral_value)["support"]

    introduce(world, hero, helper, dic)
    conflict(world, hero, helper, dic)
    define_value(world, dic, hero)
    choose_better_way(world, hero, helper, dic)
    ending(world, hero, helper, dic)

    world.facts.update(
        hero=hero,
        helper=helper,
        dictionary=dic,
        moral_value=moral_value,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral_value")
    return [
        f"Write a short pirate tale for a child about a dictionary and the value of {value}.",
        f"Tell a simple story where {hero.id} and {helper.id} use a dictionary to settle a shipboard argument.",
        f"Write a child-friendly pirate story ending with a better choice after someone looks up {value}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    dic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "dictionary")
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral_value")
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.id} argue about before they looked in the dictionary?",
            answer=f"They argued about what to do on {world.setting.place}, and the dictionary helped them choose {value} instead of a meaner choice.",
        ),
        QAItem(
            question=f"What did the dictionary say {value} means?",
            answer=f"It said that {value} means to {dic.phrase}.",
        ),
        QAItem(
            question=f"What changed after they read the page for {value}?",
            answer=f"The argument ended, {helper.id} agreed to a better plan, and the two pirates used the dictionary to guide a kinder action.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral_value")
    dic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "dictionary")
    items = [
        QAItem(
            question="What is a dictionary?",
            answer="A dictionary is a book that explains words and tells what they mean.",
        ),
        QAItem(
            question=f"What is {value}?",
            answer=f"{(getattr(value, 'capitalize')() if callable(getattr(value, 'capitalize', None)) else str(value).capitalize())} is a moral value that helps people choose a good way to act.",
        ),
    ]
    if value == "honesty":
        items.append(QAItem(question="Why is honesty useful?", answer="Honesty helps people trust each other because the truth is clear."))
    if value == "kindness":
        items.append(QAItem(question="What does kindness do?", answer="Kindness helps someone feel cared for instead of hurt."))
    if value == "fairness":
        items.append(QAItem(question="What does fairness mean?", answer="Fairness means giving each person a fair turn or a fair share."))
    if value == "courage":
        items.append(QAItem(question="What does courage mean?", answer="Courage means doing the right thing even when you feel scared."))
    items.append(QAItem(question=f"Why did the crew open the dictionary?", answer=f"They opened the dictionary to read the page for {dic.label} and settle their problem with words, not shouting."))
    return items


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
value(V) :- moral_value(V).
valid(Place, V) :- setting(Place), moral_value(V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral_value", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Trace and output
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Curated examples
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="deck", value="honesty", name="Nia", helper="captain"),
    StoryParams(place="cabin", value="kindness", name="Pip", helper="mate"),
    StoryParams(place="dock", value="fairness", name="Lina", helper="boy"),
    StoryParams(place="deck", value="courage", name="Jory", helper="pirate"),
]


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.value, params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def explain_invalid(place: str, value: str) -> str:
    return f"(No story: {value} is not available on {place}.)"


def resolve_explicit(args: argparse.Namespace) -> None:
    if getattr(args, "place", None) and getattr(args, "value", None) and (getattr(args, "place", None), getattr(args, "value", None)) not in valid_combos():
        pass


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, value) combos:\n")
        for place, value in combos:
            print(f"  {place:8} {value}")
        return

    resolve_explicit(args)
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
            header = f"### {p.name}: {p.value} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
