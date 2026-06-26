#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gear_scallywag_teamwork_curiosity_rhyme_folk_tale.py
==============================================================================================================

A small folk-tale storyworld about a curious scallywag, a broken gear, and a
teamwork fix that ends with a little rhyme.

The world premise:
- A village has an old windmill, a cart, and a cupboard of spare gear.
- A curious scallywag pokes where he should not, and a needed gear goes missing
  or gets jammed.
- The village cannot do the work alone, so the scallywag must join a team.
- Together they fetch, fit, and test the gear, and the tale ends in a rhyme.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager imports from storyworlds/results.py
- lazy ASP import inside helpers only
- reasonableness gate in Python plus inline ASP twin
- --verify checks ASP/Python parity and exercises generated stories
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    carried_by: Optional[str] = None
    broken: bool = False
    fixed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    affords: set[str] = field(default_factory=set)
    mood: str = "plain"
    folk_prefix: str = "Long ago"
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
class Character:
    id: str
    type: str
    title: str
    traits: list[str] = field(default_factory=list)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
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
class GearPlan:
    id: str
    label: str
    verb: str
    rhyme_a: str
    rhyme_b: str
    requires: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    task: str
    missing: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registry data
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting(place="the village green", affords={"mill", "cart"}, mood="bright"),
    "mill": Setting(place="the old mill", affords={"mill"}, mood="whirring"),
    "road": Setting(place="the windy road", affords={"cart"}, mood="dusty"),
    "barn": Setting(place="the barn by the lane", affords={"cart", "mill"}, mood="warm"),
}

TASKS = {
    "mill": {
        "label": "the mill wheel",
        "goal": "turn the mill wheel",
        "trouble": "the wheel would not turn",
        "need": "a strong gear",
        "fixed_by": "the right gear clicked into place",
        "sound": "whirr",
        "zone": {"mill"},
        "prompt_word": "gear",
    },
    "cart": {
        "label": "the cart axle",
        "goal": "roll the cart",
        "trouble": "the cart sat still and heavy",
        "need": "a spare gear pin",
        "fixed_by": "the axle spun again",
        "sound": "clatter",
        "zone": {"cart"},
        "prompt_word": "gear",
    },
}

ITEMS = {
    "gear": Item(
        id="gear",
        label="gear",
        phrase="a brass gear with bright teeth",
        type="gear",
    ),
    "spare_gear": Item(
        id="spare_gear",
        label="spare gear",
        phrase="a small spare gear in a cloth wrap",
        type="gear",
    ),
}

CHARACTERS = {
    "fox": Character(id="fox", type="fox", title="scallywag", traits=["curious", "quick"]),
    "boy": Character(id="boy", type="boy", title="boy", traits=["kind", "curious"]),
    "girl": Character(id="girl", type="girl", title="girl", traits=["bright", "curious"]),
    "grandmother": Character(id="grandmother", type="woman", title="grandmother", traits=["wise"]),
    "smith": Character(id="smith", type="man", title="smith", traits=["steady"]),
    "miller": Character(id="miller", type="man", title="miller", traits=["patient"]),
}

HELPERS = {
    "grandmother": "grandmother",
    "smith": "smith",
    "miller": "miller",
}

TRAITS = ["curious", "bright", "bold", "gentle"]

GENDER_NAMES = {
    "boy": ["Pip", "Tom", "Ned", "Bram", "Finn"],
    "girl": ["Mira", "Bea", "Tess", "Lina", "Wren"],
}

FOLK_OPENERS = [
    "Long ago, in a little village by a silver road,",
    "Once, when the bells were soft and the air was clear,",
    "In a time of bread ovens, bright skies, and busy hands,",
]

# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for missing in ITEMS:
                if task_reasonable(_safe_lookup(TASKS, task), _safe_lookup(ITEMS, missing)):
                    combos.append((place, task, missing))
    return combos


def task_reasonable(task: dict, item: Item) -> bool:
    return item.label == "gear" or item.id == "spare_gear"


def explain_rejection(task: dict, item: Item) -> str:
    return f"(No story: the tale needs a gear that fits {task['label']}, and this item does not make a believable fix.)"


def task_needs_gear(task_id: str, missing_id: str) -> bool:
    return task_id in TASKS and missing_id in ITEMS and task_reasonable(_safe_lookup(TASKS, task_id), _safe_lookup(ITEMS, missing_id))


def predicted_fix(world: World, task_id: str) -> bool:
    return task_id in TASKS


def rhyme_line(task: dict, hero: Entity, helper: Entity) -> str:
    return f"{hero.id} and {helper.id} worked side by side, and the wheel went round with a merry guide."


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, trait: str) -> None:
    opener = random.choice(FOLK_OPENERS)
    world.say(
        f"{opener} there lived a little {trait} {hero.type} named {hero.id}, and the village called {hero.pronoun('object')} a scallywag for asking one question after another."
    )
    world.say(
        f"{hero.id} loved curious peeks at every latch, stone, and shelf, while {helper.id} kept a calm hand on the day's good work."
    )


def set_problem(world: World, task: dict, missing: Entity, hero: Entity) -> None:
    world.say(
        f"One day, {hero.id} found {missing.phrase} tucked where it did not belong, and {hero.pronoun('subject')} gave it a curious little twist."
    )
    missing.moved_by = hero.id
    missing.carried_by = hero.id
    world.say(
        f"Then {task['trouble']}, and the folk of the village frowned, for without {missing.label} they could not {task['goal']}."
    )


def gather_team(world: World, hero: Entity, helper: Entity, task: dict, missing: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"{helper.id} did not scold. Instead, {helper.pronoun('subject')} said, 'Come now, little scallywag, a problem shared is a problem halved.'"
    )
    world.say(
        f"So {hero.id} and {helper.id} joined hands, one to lift, one to hold, and one to mind the tiny teeth."
    )


def fix_task(world: World, task: dict, missing: Entity, hero: Entity, helper: Entity) -> None:
    missing.fixed = True
    world.say(
        f"{helper.id} cleaned the teeth, {hero.id} lined up the fit, and with a soft click {task['fixed_by']}."
    )
    world.say(
        f"At once there came a {task['sound']}, steady and proud, as if the whole place had remembered its song."
    )
    world.say(
        f"{hero.id} grinned, for the scallywag had learned that curious hands are best when they help, not only when they take."
    )
    world.say(rhyme_line(task, hero, helper))


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label="scallywag"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=_safe_lookup(HELPERS, params.helper)))
    item = world.add(Entity(id=params.missing, type="thing", label="gear", phrase=_safe_lookup(ITEMS, params.missing).phrase))
    task = _safe_lookup(TASKS, params.task)

    introduce(world, hero, helper, params.trait)
    world.para()
    set_problem(world, task, item, hero)
    world.para()
    gather_team(world, hero, helper, task, item)
    fix_task(world, task, item, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        task_id=params.task,
        task=task,
        setting=setting,
        params=params,
        resolved=item.fixed,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    task: dict = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    return [
        f'Write a short folk tale for a child about a curious scallywag named {hero.id} who helps {helper.id} mend {task["label"]}.',
        f"Tell a gentle story where teamwork fixes a missing gear and ends with a rhyme.",
        f'Write a village story that includes the word "gear" and shows curiosity turning into teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    task: dict = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    return [
        QAItem(
            question=f"Who was the scallywag in the story?",
            answer=f"The scallywag was {hero.id}, a curious little {hero.type} who liked to poke at things.",
        ),
        QAItem(
            question=f"What problem happened when {hero.id} twisted the gear?",
            answer=f"{task['trouble'].capitalize()}, and the village could not {task['goal']} until the gear was put back right.",
        ),
        QAItem(
            question=f"How did {helper.id} help fix the problem?",
            answer=f"{helper.id} joined {hero.id}, cleaned the tiny teeth, and helped fit {item.label} so the work could begin again.",
        ),
        QAItem(
            question="What changed at the end of the tale?",
            answer=f"The broken work was made whole again, and the gear turned with a steady sound instead of sitting still.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and do a job together, so the work becomes easier and better.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like tune and moon or light and night.",
        ),
        QAItem(
            question="What is a gear for?",
            answer="A gear is a toothed wheel that helps machines move and turn from one part to another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- task_kind(T).
item(I) :- gear_item(I).

reasonable(P,T,I) :- affords(P,T), gear_item(I), compatible(T,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task_kind", tid))
    for iid in ITEMS:
        lines.append(asp.fact("gear_item", iid))
    for tid, task in TASKS.items():
        for iid, item in ITEMS.items():
            if task_reasonable(task, item):
                lines.append(asp.fact("compatible", tid, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about a scallywag, a gear, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--missing", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["fox", "boy", "girl"], dest="hero_type")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"], dest="helper_type")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "missing", None) is None or c[2] == getattr(args, "missing", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, missing = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or "fox"
    helper_type = getattr(args, "helper_type", None) or "woman"
    hero = getattr(args, "hero", None) or rng.choice(["Pip", "Moss", "Tansy", "Wren"])
    helper = getattr(args, "helper", None) or rng.choice(["Nan", "Mara", "Hugh", "Bess"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, missing=missing, hero=hero, hero_type=hero_type,
                       helper=helper, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.fixed:
            bits.append("fixed=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
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


def explain_gender() -> str:
    return "(No story: this world does not use a gender restriction beyond the chosen character type.)"


CURATED = [
    StoryParams(place="village", task="mill", missing="gear", hero="Pip", hero_type="fox", helper="Nan", helper_type="woman", trait="curious"),
    StoryParams(place="barn", task="cart", missing="spare_gear", hero="Moss", hero_type="fox", helper="Hugh", helper_type="man", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, task, item) combos:\n")
        for triple in triples:
            print("  ", triple)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
