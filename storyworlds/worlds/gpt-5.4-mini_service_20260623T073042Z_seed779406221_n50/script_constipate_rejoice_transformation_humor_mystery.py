#!/usr/bin/env python3
"""
storyworlds/worlds/script_constipate_rejoice_transformation_humor_mystery.py
============================================================================

A small standalone story world about a mysterious stage script, a comic
transformation, and a happy ending. The domain is intentionally tiny and
classical: one child, one odd script, one suspicious transformation, one
helpful reveal, and a final image that proves what changed.

Seed tale used to shape the model:
---
A child finds a strange stage script in a dusty prop box. Whenever the child
reads the next line aloud, something silly happens: a hat grows too large, a
shoe turns into a squeaky fish, or a costume piece changes shape. The child
worries that the weird script is cursed. A grown-up laughs, explains that the
"curse" is only a trick of theater lights and hidden props, and helps solve the
mystery. At the end, everyone rejoices, because the script turns out to be a
funny rehearsal for a play, not a spell.

This world keeps that premise while varying the setting, the transformation, and
the prop that changes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    plural: bool = False
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    def __post_init__(self):
        for key in ["mystery", "tension", "joy", "confusion", "relief", "curiosity", "laughter", "transformed"]:
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"
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
    label: str
    detail: str
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
class Transformation:
    id: str
    clue: str
    verb: str
    result: str
    shape: str
    comic: str
    reversible: bool = True
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


@dataclass
class Script:
    id: str
    title: str
    line: str
    prop: str
    misread: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    c: object | None = None
    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c
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


def _r_transformed(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["mystery"] < THRESHOLD:
        return out
    if child.meters["transformed"] >= THRESHOLD:
        return out
    child.meters["transformed"] += 1
    child.memes["confusion"] += 1
    out.append("something_changed")
    return out


def _r_rejoice(world: World) -> list[str]:
    out = []
    child = world.get("child")
    adult = world.get("adult")
    if child.memes["confusion"] < THRESHOLD or adult.memes["laughter"] < THRESHOLD:
        return out
    if world.facts.get("rejoiced"):
        return out
    world.facts["rejoiced"] = True
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    out.append("rejoice")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_transformed, _r_rejoice):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s == "something_changed":
                world.say("The clue finally clicked, and something changed at once.")
            elif s == "rejoice":
                world.say("That made everyone rejoice.")
    return produced


def conclude_predictive(world: World, script: Script, trans: Transformation) -> bool:
    sim = world.copy()
    sim.get("child").meters["mystery"] += 1
    propagate(sim, narrate=False)
    return sim.get("child").meters["transformed"] >= THRESHOLD


@dataclass
class StoryParams:
    setting: str
    script: str
    transformation: str
    name: str
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


SETTINGS = {
    "backstage": Setting("the backstage hallway", "dusty props and hanging curtains"),
    "attic": Setting("the attic", "old trunks and moonlit beams"),
    "library": Setting("the library", "quiet shelves and a reading lamp"),
}

SCRIPTS = {
    "mask_script": Script("mask_script", "a strange script", "read the next line aloud", "a paper mask", "constipate", {"script", "mystery"}),
    "shoe_script": Script("shoe_script", "a strange script", "read the next line aloud", "a prop shoe", "rejoice", {"script", "mystery"}),
    "hat_script": Script("hat_script", "a strange script", "read the next line aloud", "a paper hat", "twist", {"script", "mystery"}),
}

TRANSFORMATIONS = {
    "mask": Transformation("mask", "a grin in the wrong place", "turn into a huge mask", "a huge stage mask", "mask-like", "The mask looked serious in a silly way."),
    "shoe": Transformation("shoe", "a squeak from the floor", "become a squeaky fish", "a squeaky fish", "fishy", "The fish made everyone snicker."),
    "hat": Transformation("hat", "a wobble over the head", "grow into a giant hat", "a giant hat", "towering", "The hat was so tall it nearly brushed the lamp."),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Eli", "Theo", "Ben", "Max", "Finn"]
ROLES = ["curious", "careful", "cheerful", "skeptical"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for sc in SCRIPTS:
            for tr in TRANSFORMATIONS:
                out.append((s, sc, tr))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for sc in SCRIPTS:
        lines.append(asp.fact("script", sc))
    for tr in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tr))
    lines.append(asp.fact("valid_all", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(SC,TR) :- script(SC), transformation(TR).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    setting: str
    script: str
    transformation: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world with a comic transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--script", choices=SCRIPTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "script", None) is None or c[1] == getattr(args, "script", None))
              and (getattr(args, "transformation", None) is None or c[2] == getattr(args, "transformation", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, script, trans = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(setting, script, trans, name, gender, role)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity("child", kind="character", type=params.gender, label=params.name))
    adult = world.add(Entity("adult", kind="character", type="adult", label="the grown-up"))
    script = _safe_lookup(SCRIPTS, params.script)
    trans = _safe_lookup(TRANSFORMATIONS, params.transformation)
    child.memes["curiosity"] += 1
    world.say(f"{params.name} found {script.title} in {world.setting.label}, among {world.setting.detail}.")
    world.say(f"On the page, the line said to {script.line}, and that seemed like a clue.")
    world.para()
    world.say(f"{params.name} read the line aloud beside {script.prop}.")
    child.meters["mystery"] += 1
    if conclude_predictive(world, script, trans):
        child.meters["tension"] += 1
    propagate(world, narrate=False)
    if trans.id == "mask":
        world.say(f"At once, {script.prop} began to {trans.verb}, until it looked like {trans.result}.")
    elif trans.id == "shoe":
        world.say(f"At once, {script.prop} began to {trans.verb}, until it looked like {trans.result}.")
    else:
        world.say(f"At once, {script.prop} began to {trans.verb}, until it looked like {trans.result}.")
    world.say(f"{trans.comic}")
    world.para()
    adult.memes["laughter"] += 1
    world.say(f"The grown-up peered at the clue and laughed. {script.misread} was only a stage trick.")
    world.say(f"It was a rehearsal script, not a spell, and the hidden prop made the whole mystery a joke.")
    world.say(f"So {params.name} could {script.line} again without fear, and everyone could finally rejoice.")
    world.facts.update(child=child, adult=adult, script=script, trans=trans)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mystery story for a young child about {f['child'].label} finding {f['script'].title} in {world.setting.label}.",
        f"Tell a gentle story where a line from a {f['script'].label} makes {f['child'].label} think something is strange, but a grown-up explains the trick.",
        f"Write a comic transformation story that ends with {f['child'].label} and the grown-up able to rejoice because the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, script, trans = f["child"], f["script"], f["trans"]
    return [
        QAItem(question=f"What did {child.label} find in the setting?", answer=f"{child.label} found {script.title}, and it seemed mysterious at first."),
        QAItem(question=f"What changed after {child.label} read the line?", answer=f"{script.prop} changed into {trans.result}, which made the scene funny and surprising."),
        QAItem(question="Why did the grown-up laugh?", answer=f"The grown-up laughed because the scary-looking mystery was only a stage trick in a rehearsal script."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a script?", answer="A script is a set of lines for actors to read in a play or show."),
        QAItem(question="What does rejoice mean?", answer="To rejoice means to feel very glad and happy."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


def explain_rejection() -> str:
    return "(No story: the chosen options do not make a coherent mystery transformation.)"


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.script not in SCRIPTS or params.transformation not in TRANSFORMATIONS:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python combos")
    return 1


CURATED = [
    StoryParams("backstage", "mask_script", "mask", "Mina", "girl", "curious"),
    StoryParams("library", "shoe_script", "shoe", "Eli", "boy", "careful"),
    StoryParams("attic", "hat_script", "hat", "Nora", "girl", "skeptical"),
]


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
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
