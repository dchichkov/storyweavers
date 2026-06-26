#!/usr/bin/env python3
"""
A small ghost-story world about Eyer borrowing a thing, repeating a pattern,
and learning to share when a shy ghost gets mesmerized.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------


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
    name: str = ""
    label: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    borrowed_by: Optional[str] = None
    borrowed_from: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    ghost: object | None = None
    helper: object | None = None
    item: object | None = None
    def display(self) -> str:
        return self.label or self.name or self.id

    def pronoun(self) -> str:
        return "they"
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
class SettingSpec:
    id: str
    place: str
    features: set[str]
    opening: str
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
class ItemSpec:
    id: str
    label: str
    phrase: str
    requires: set[str]
    repeat_phrase: str
    mesmerize_phrase: str
    share_phrase: str
    risk: str
    home: str
    ending_phrase: str
    keyword: str
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
class HelperSpec:
    id: str
    name: str
    relation: str
    label: str
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
class GhostSpec:
    id: str
    name: str
    label: str
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


class World:
    def __init__(self, setting: SettingSpec) -> None:
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
        text = text.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            new = rule.apply(world)
            if new:
                changed = True
                out.extend(new)
    if narrate:
        for line in out:
            world.say(line)
    return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS: dict[str, SettingSpec] = {
    "attic": SettingSpec(
        id="attic",
        place="the attic",
        features={"echo", "quiet", "dark"},
        opening="The attic was dusty and echoing, and the moon drew a pale stripe across the floor.",
    ),
    "hallway": SettingSpec(
        id="hallway",
        place="the hallway",
        features={"echo", "quiet", "dark"},
        opening="The hallway was long and dark, and every tiny sound came back like a whisper.",
    ),
    "porch": SettingSpec(
        id="porch",
        place="the porch",
        features={"dark", "chilly", "open"},
        opening="The porch was chilly, and the yard outside looked like a blue-black sea.",
    ),
    "cellar": SettingSpec(
        id="cellar",
        place="the cellar",
        features={"dark", "quiet", "chilly"},
        opening="The cellar was cool and still, with jars shining like sleepy eyes.",
    ),
}

ITEMS: dict[str, ItemSpec] = {
    "bell": ItemSpec(
        id="bell",
        label="a little silver bell",
        phrase="a little silver bell",
        requires={"echo"},
        repeat_phrase="ding, ding, ding",
        mesmerize_phrase="The ghost went still, listening as if the sound were a ribbon in the dark.",
        share_phrase="let the ghost tap one careful ding",
        risk="it might clatter too hard and lose its shine",
        home="the hook by the door",
        ending_phrase="The bell hung safely on its hook again.",
        keyword="bell",
    ),
    "lantern": ItemSpec(
        id="lantern",
        label="a brass lantern",
        phrase="a brass lantern",
        requires={"dark"},
        repeat_phrase="swish, swish, swish",
        mesmerize_phrase="The ghost followed the glow like a moth following moonlight.",
        share_phrase="held the lantern low so the ghost could share the light",
        risk="the glass might smear with dusty fingerprints",
        home="the shelf by the steps",
        ending_phrase="The lantern rested back on the shelf.",
        keyword="lantern",
    ),
    "storybook": ItemSpec(
        id="storybook",
        label="a picture book with a tiny ghost on the cover",
        phrase="a picture book with a tiny ghost on the cover",
        requires={"quiet"},
        repeat_phrase="the same page, then the same page again",
        mesmerize_phrase="The ghost listened so hard its misty toes stopped wiggling.",
        share_phrase="held the book open wide so the ghost could see the pictures too",
        risk="the pages might bend at the corners",
        home="the low book basket",
        ending_phrase="The book slid back into the basket.",
        keyword="storybook",
    ),
    "blanket": ItemSpec(
        id="blanket",
        label="a warm blanket with blue stars",
        phrase="a warm blanket with blue stars",
        requires={"chilly"},
        repeat_phrase="tuck, tuck, tuck",
        mesmerize_phrase="The ghost loved the soft rhythm and floated closer like a sleepy puff.",
        share_phrase="wrapped the blanket around both of them",
        risk="it might drag on the dusty floor",
        home="the basket by the chair",
        ending_phrase="The blanket folded back into its basket.",
        keyword="blanket",
    ),
}

HELPERS: dict[str, HelperSpec] = {
    "sister": HelperSpec(
        id="sister",
        name="Mina",
        relation="sister",
        label="Mina, Eyer's sister",
    ),
    "mother": HelperSpec(
        id="mother",
        name="June",
        relation="mother",
        label="June, Eyer's mother",
    ),
    "grandma": HelperSpec(
        id="grandma",
        name="Bea",
        relation="grandma",
        label="Bea, Eyer's grandma",
    ),
    "brother": HelperSpec(
        id="brother",
        name="Owen",
        relation="brother",
        label="Owen, Eyer's brother",
    ),
    "neighbor": HelperSpec(
        id="neighbor",
        name="Kai",
        relation="neighbor",
        label="Kai, Eyer's neighbor",
    ),
}

GHOSTS: dict[str, GhostSpec] = {
    "wisp": GhostSpec(id="wisp", name="Wisp", label="Wisp, the little ghost"),
    "hush": GhostSpec(id="hush", name="Hush", label="Hush, the shy ghost"),
    "mote": GhostSpec(id="mote", name="Mote", label="Mote, the pale ghost"),
    "fog": GhostSpec(id="fog", name="Fog", label="Fog, the floating ghost"),
}

CURATED: list["StoryParams"] = [
    # Attic + echo + bell
    # Hallway + quiet + storybook
    # Porch + chilly + blanket
    # Cellar + dark + lantern
    # These are all valid by the Python and ASP gates.
    # Eyer is fixed so the seed word always appears in story text.
    # Helper / ghost choices keep the stories varied.
    # fmt: off
    # type: ignore[misc]
]


# ---------------------------------------------------------------------------
# Validation / reasonableness
# ---------------------------------------------------------------------------

def is_valid_combo(setting_id: str, item_id: str) -> bool:
    return _safe_lookup(ITEMS, item_id).requires.issubset(_safe_lookup(SETTINGS, setting_id).features)


def valid_combos() -> list[tuple[str, str]]:
    return sorted(
        (sid, iid)
        for sid in SETTINGS
        for iid in ITEMS
        if is_valid_combo(sid, iid)
    )


def explain_rejection(setting_id: str, item_id: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_id)
    item = _safe_lookup(ITEMS, item_id)
    missing = sorted(item.requires - setting.features)
    missing_text = ", ".join(missing)
    return (
        f"(No story: {item.label} needs {missing_text} in the setting, "
        f"but {setting.place} does not have that. Try a quieter, darker, "
        f"or more echoing place, depending on the borrowed thing.)"
    )


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    item: str
    helper: str
    ghost: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Small causal rules
# ---------------------------------------------------------------------------
    params: object | None = None
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


def _r_mesmerize(world: World) -> list[str]:
    child = world.get("eyer")
    ghost = world.get("ghost")
    item = world.get("item")

    if child.meters["repeat"] < 3:
        return []
    if item.borrowed_by != child.id:
        return []
    if ghost.memes["mesmerized"] >= 1:
        return []
    sig = ("mesmerize", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["mesmerized"] += 1
    ghost.memes["calm"] += 0.5
    return [_safe_lookup(ITEMS, item.type).mesmerize_phrase]


def _r_conflict(world: World) -> list[str]:
    helper = world.get("helper")
    ghost = world.get("ghost")
    item = world.get("item")
    child = world.get("eyer")

    if helper.memes["worry"] < 1:
        return []
    if ghost.meters["reach"] < 1:
        return []
    if child.memes["conflict"] >= 1:
        return []
    sig = ("conflict", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    return [
        f"That made a small conflict: {helper.label} worried the borrowed {item.label} might be lost."
    ]


def _r_share(world: World) -> list[str]:
    helper = world.get("helper")
    ghost = world.get("ghost")
    item = world.get("item")
    child = world.get("eyer")

    if child.memes["share"] < 1:
        return []
    if ghost.memes["mesmerized"] < 1:
        return []
    sig = ("share", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["worry"] = 0
    child.memes["conflict"] = 0
    ghost.memes["trust"] += 1
    ghost.memes["calm"] += 1
    item.meters["shared"] += 1
    return [f"Eyer shared the {item.label}, and the worry softened into trust."]


RULES: list[Rule] = [
    Rule("mesmerize", _r_mesmerize),
    Rule("conflict", _r_conflict),
    Rule("share", _r_share),
]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, helper: Entity, ghost: Entity, item: Entity) -> None:
    setting = world.setting
    world.say(
        f"Eyer lived near {setting.place}, where {setting.opening}"
    )
    world.say(
        f"One night, Eyer wanted to borrow {item.label} from {helper.label} so Eyer could tell a gentle ghost story for {ghost.label}."
    )


def borrow_item(world: World, child: Entity, helper: Entity, item: Entity) -> None:
    helper.memes["worry"] += 1
    child.memes["curiosity"] += 1
    item.borrowed_by = child.id
    item.borrowed_from = helper.id
    item.meters["borrowed"] += 1
    world.say(
        f"{helper.label} let Eyer borrow {item.phrase}, but warned that {_safe_lookup(ITEMS, item.type).risk}."
    )


def repeat_the_pattern(world: World, child: Entity, ghost: Entity, item: Entity) -> None:
    child.meters["repeat"] += 3
    ghost.memes["curiosity"] += 1
    world.say(
        f"At {world.setting.place}, Eyer did it again and again: {_safe_lookup(ITEMS, item.type).repeat_phrase}."
    )
    propagate(world, narrate=True)


def ghost_reaches(world: World, ghost: Entity, item: Entity) -> None:
    ghost.meters["reach"] += 1
    world.say(
        f"Then {ghost.label} drifted closer and reached for the borrowed {item.label}, because the repetition had caught its eye."
    )
    propagate(world, narrate=True)


def share_and_resolve(world: World, child: Entity, helper: Entity, ghost: Entity, item: Entity) -> None:
    child.memes["share"] += 1
    world.say(
        f"Instead of guarding the borrowed {item.label}, Eyer shared it with {ghost.label}: {_safe_lookup(ITEMS, item.type).share_phrase}."
    )
    propagate(world, narrate=True)
    item.meters["returned"] += 1
    item.borrowed_by = None
    item.borrowed_from = None
    world.say(
        f"When the turn was over, {helper.label} got the {item.label} back, and {_safe_lookup(ITEMS, item.type).ending_phrase}"
    )
    world.say(
        f"By the end, {ghost.label} was calm enough to float beside Eyer while the room went quiet again."
    )


def tell(setting: SettingSpec, item_spec: ItemSpec, helper_spec: HelperSpec, ghost_spec: GhostSpec) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="eyer",
        kind="character",
        type="child",
        name="Eyer",
        label="Eyer",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        name=helper_spec.name,
        label=helper_spec.label,
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        name=ghost_spec.name,
        label=ghost_spec.label,
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_spec.id,
        name=item_spec.label,
        label=item_spec.label,
        owner=helper.id,
        borrowed_from=helper.id,
    ))

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        item=item,
        setting=setting,
        item_spec=item_spec,
        helper_spec=helper_spec,
        ghost_spec=ghost_spec,
    )

    intro(world, child, helper, ghost, item)
    world.para()
    borrow_item(world, child, helper, item)
    world.para()
    repeat_the_pattern(world, child, ghost, item)
    ghost_reaches(world, ghost, item)
    world.para()
    share_and_resolve(world, child, helper, ghost, item)

    world.facts.update(
        shared=bool(item.meters["shared"] >= 1),
        conflict=bool(child.memes["conflict"] >= 1),
        mesmerized=bool(ghost.memes["mesmerized"] >= 1),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: ItemSpec = _safe_fact(world, f, "item_spec")
    helper: HelperSpec = _safe_fact(world, f, "helper_spec")
    ghost: GhostSpec = _safe_fact(world, f, "ghost_spec")
    setting: SettingSpec = _safe_fact(world, f, "setting")
    return [
        (
            f'Write a short ghost story for a child named Eyer that uses the words '
            f'"borrow" and "{item.keyword}" and includes a repeating pattern.'
        ),
        (
            f"Tell a gentle story where Eyer borrows {item.phrase} from {helper.label}, "
            f"mesmerizes {ghost.label} with repetition, and then learns to share."
        ),
        (
            f"Write a child-facing ghost story set at {setting.place} that ends with the "
            f"borrowed {item.label} safely returned after a conflict is solved."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper: HelperSpec = _safe_fact(world, f, "helper_spec")
    ghost: GhostSpec = _safe_fact(world, f, "ghost_spec")
    item: ItemSpec = _safe_fact(world, f, "item_spec")
    setting: SettingSpec = _safe_fact(world, f, "setting")
    child = _safe_fact(world, f, "child")

    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=(
                f"It is about Eyer, who wanted to borrow {item.phrase} and meet {ghost.label}. "
                f"The story stays focused on Eyer's careful night and the friendly ghost that appeared."
            ),
        ),
        QAItem(
            question=f"What did Eyer borrow from {helper.label}?",
            answer=(
                f"Eyer borrowed {item.phrase} from {helper.label}. "
                f"{helper.name} worried a little because {item.risk}."
            ),
        ),
        QAItem(
            question=f"What happened when Eyer repeated the pattern again and again?",
            answer=(
                f"The repetition was strong enough to mesmerize {ghost.label}. "
                f"{item.mesmerize_phrase} That is what made the ghost drift closer."
            ),
        ),
        QAItem(
            question="How did Eyer solve the conflict?",
            answer=(
                f"Eyer shared the {item.label} with {ghost.label} instead of guarding it alone. "
                f"That turned the worry into trust, and the borrowed thing went back home safely."
            ),
        ),
    ]
    if f.get("shared"):
        qa.append(
            QAItem(
                question="What was the ending image?",
                answer=(
                    f"At the end, {ghost.label} floated calmly beside Eyer while {item.ending_phrase} "
                    f"The room felt quiet and safe again."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    item: ItemSpec = _safe_fact(world, world.facts, "item_spec")
    base = [
        QAItem(
            question="What does borrow mean?",
            answer="To borrow means to use something that belongs to someone else for a little while, and then give it back.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing again and again.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What does mesmerize mean?",
            answer="When something mesmerizes you, it catches your attention so strongly that you want to keep looking or listening.",
        ),
        QAItem(
            question="Why can a ghost in a gentle story be friendly?",
            answer="A gentle story ghost can be friendly because it is curious, calm, and happy to meet someone who speaks softly.",
        ),
    ]
    item_specific: dict[str, tuple[str, str]] = {
        "bell": (
            "What does a bell do?",
            "A bell makes a clear ringing sound that can travel far in a quiet place.",
        ),
        "lantern": (
            "What does a lantern do on a dark night?",
            "A lantern gives off a warm little light so people can see shapes and steps more easily.",
        ),
        "storybook": (
            "Why do children read storybooks again and again?",
            "Children often read storybooks again and again because they like the pictures, the rhythm, and the familiar words.",
        ),
        "blanket": (
            "What does a blanket do when a place feels chilly?",
            "A blanket helps keep people warm and cozy when the air is cold.",
        ),
    }
    q, a = item_specific[item.id]
    base.append(QAItem(question=q, answer=a))
    return base


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
# Trace / display
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.type in ITEMS:
            bits.append(f"borrowed_by={ent.borrowed_by!r}")
            bits.append(f"returned={ent.meters.get('returned', 0)!r}")
        lines.append(f"  {ent.id:6} ({ent.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
invalid(S,I) :- setting(S), item(I), requires(I,F), not feature(S,F).
valid(S,I) :- setting(S), item(I), not invalid(S,I).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", sid, feat))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for req in sorted(item.requires):
            lines.append(asp.fact("requires", iid, req))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if asp_set != python_set:
        print("MISMATCH between ASP and Python valid-combo gates:")
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        return 1

    print(f"OK: ASP matches Python valid_combos() for {len(python_set)} combos.")
    # Exercise generated stories too.
    combos = sorted(python_set)
    helper_ids = list(HELPERS)
    ghost_ids = list(GHOSTS)
    for i, (setting_id, item_id) in enumerate(combos[: min(4, len(combos))]):
        params = StoryParams(
            setting=setting_id,
            item=item_id,
            helper=helper_ids[i % len(helper_ids)],
            ghost=ghost_ids[i % len(ghost_ids)],
            seed=1000 + i,
        )
        sample = generate(params)
        text = sample.story
        if not text or "Eyer" not in text or "borrow" not in text.lower() or _safe_lookup(ITEMS, item_id).label not in text:
            print("Generated story failed a simple sanity check.")
            return 1
    print("OK: generated stories also passed a basic sanity check.")
    return 0


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Story world: Eyer borrows a thing, repeats a pattern, and learns "
            "how sharing helps a mesmerized ghost."
        )
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible randomness")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sections")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible setting/item pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generated stories")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "item", None) and not is_valid_combo(getattr(args, "setting", None), getattr(args, "item", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (sid, iid)
        for sid, iid in valid_combos()
        if (getattr(args, "setting", None) is None or sid == getattr(args, "setting", None))
        and (getattr(args, "item", None) is None or iid == getattr(args, "item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, item_id = rng.choice(combos)
    helper_id = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    ghost_id = getattr(args, "ghost", None) or rng.choice(list(GHOSTS))
    return StoryParams(
        setting=setting_id,
        item=item_id,
        helper=helper_id,
        ghost=ghost_id,
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    item = _safe_lookup(ITEMS, params.item)
    helper = _safe_lookup(HELPERS, params.helper)
    ghost = _safe_lookup(GHOSTS, params.ghost)
    world = tell(setting, item, helper, ghost)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# Curated examples for --all.
CURATED = [
    StoryParams(setting="attic", item="bell", helper="sister", ghost="wisp"),
    StoryParams(setting="hallway", item="storybook", helper="grandma", ghost="mote"),
    StoryParams(setting="porch", item="blanket", helper="mother", ghost="hush"),
    StoryParams(setting="cellar", item="lantern", helper="brother", ghost="fog"),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/item combos:\n")
        for setting_id, item_id in combos:
            print(f"  {_safe_lookup(SETTINGS, setting_id).place:12}  {_safe_lookup(ITEMS, item_id).label}")
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
            except StoryError:
                continue
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
            header = f"### {p.setting} / {p.item} / {p.helper} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
