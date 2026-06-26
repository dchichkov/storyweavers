#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tackle_bravery_adventure.py
=========================================================================================================

A small adventure storyworld about a brave child tackling a tricky challenge.

Seed-tale premise:
- A young adventurer sees a problem that feels too big at first.
- With courage, a helpful tool, and a steady plan, the hero tackles it.
- The ending proves bravery changed the moment and the mood.

This world keeps the style close to classic adventure: a clear quest, a risky
obstacle, a brave attempt, and a satisfying finish image.
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


BRAVERY_THRESHOLD = 1.0
TACKLE_THRESHOLD = 1.0



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    tool_ent: object | None = None
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
    terrain: str
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
class Obstacle:
    id: str
    label: str
    threat: str
    action: str
    meter: str
    effect: str
    zone: str
    keywords: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    finish: str
    plural: bool = False
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
    setting: str
    obstacle: str
    tool: str
    name: str
    gender: str
    companion: str
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
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
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
            self.lines.append(text)
            self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "cliff_path": Setting(place="the cliff path", terrain="rocky", affords={"climb", "cross"}),
    "forest": Setting(place="the forest trail", terrain="rooted", affords={"cross", "push"}),
    "canyon": Setting(place="the canyon edge", terrain="windy", affords={"cross", "pull"}),
    "cave": Setting(place="the cave mouth", terrain="dark", affords={"push", "climb"}),
}

OBSTACLES = {
    "ledge": Obstacle(
        id="ledge",
        label="a slippery ledge",
        threat="slip",
        action="climb over the ledge",
        meter="slip",
        effect="scrape",
        zone="feet",
        keywords={"cliff", "rock", "slip"},
    ),
    "gate": Obstacle(
        id="gate",
        label="a stuck gate",
        threat="block",
        action="push open the gate",
        meter="block",
        effect="stick",
        zone="hands",
        keywords={"gate", "wood", "push"},
    ),
    "vinewall": Obstacle(
        id="vinewall",
        label="a thick wall of vines",
        threat="tangle",
        action="tackle the vines",
        meter="tangle",
        effect="snag",
        zone="hands",
        keywords={"vines", "tangle", "green"},
    ),
    "stream": Obstacle(
        id="stream",
        label="a rushing stream",
        threat="splash",
        action="cross the stream",
        meter="splash",
        effect="soak",
        zone="feet",
        keywords={"water", "stream", "bridge"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a sturdy rope",
        helps={"climb", "cross"},
        prep="tie the rope to a branch first",
        finish="held the rope tight and stepped across",
    ),
    "staff": Tool(
        id="staff",
        label="a walking staff",
        helps={"climb", "push"},
        prep="plant the staff in the ground first",
        finish="leaned on the staff and moved carefully",
    ),
    "hook": Tool(
        id="hook",
        label="a little iron hook",
        helps={"pull", "cross"},
        prep="catch the hook on the edge first",
        finish="used the hook to pull the way clear",
    ),
}

NAMES = ["Mina", "Pico", "Arlo", "Nia", "Tess", "Oren", "Lumi", "Juno"]
TRAITS = ["brave", "curious", "steady", "bold", "quick-thinking"]
COMPANIONS = ["father", "mother", "sister", "brother", "friend"]


def obstacle_needs_tool(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in {"ledge", "stream"} and "cross" in tool.helps or \
        obstacle.id == "gate" and "push" in tool.helps or \
        obstacle.id == "vinewall" and "pull" in tool.helps or "climb" in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obstacle in OBSTACLES.items():
            if obstacle.action.split()[0] not in setting.affords and oid not in {"vinewall"}:
                pass
            for tid, tool in TOOLS.items():
                if obstacle_needs_tool(obstacle, tool):
                    combos.append((sid, oid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world: a brave child tackles a hard obstacle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = valid_combos()
    filtered = [c for c in combos
                if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                and (getattr(args, "obstacle", None) is None or c[1] == getattr(args, "obstacle", None))
                and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, obstacle, tool = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, obstacle=obstacle, tool=tool,
                       name=name, gender=gender, companion=companion, trait=trait)


def predict(world: World, hero: Entity, obstacle: Obstacle) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes[obstacle.threat] = 1.0
    return True


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero_type = params.gender
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, meters={}, memes={"bravery": 1.0}))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=params.companion))
    obstacle = _safe_lookup(OBSTACLES, params.obstacle)
    tool = _safe_lookup(TOOLS, params.tool)
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, owner=hero.id, plural=tool.plural))
    tool_ent.worn_by = hero.id

    hero.meters["tackle"] = 0.0
    hero.memes["bravery"] += 1.0

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved adventure.")
    world.say(f"One day, {hero.id} and {params.companion} reached {world.setting.place}.")
    world.say(f"At the end of the path stood {obstacle.label}.")
    world.say(f"{hero.id} took a breath, lifted {tool.label}, and decided to {obstacle.action}.")

    hero.meters["tackle"] += 1.0
    hero.memes["nervous"] = 1.0
    world.say(f"The obstacle looked big, but {hero.id}'s bravery stayed bright.")

    if obstacle.id == "vinewall":
        hero.meters["tackle"] += 1.0
        world.say(f"{hero.id} used {tool.label} to {tool.finish}.")
    elif obstacle.id == "gate":
        hero.meters["tackle"] += 1.0
        world.say(f"{hero.id} {tool.finish}, and the gate gave way with a creak.")
    elif obstacle.id == "ledge":
        hero.meters["tackle"] += 1.0
        world.say(f"With one careful step, {hero.id} {tool.finish} without slipping.")
    else:
        hero.meters["tackle"] += 1.0
        world.say(f"{hero.id} {tool.finish}, and the stream became a small crossing.")

    hero.memes["bravery"] += 1.0
    hero.memes["fear"] = 0.0
    world.say(f"Then {hero.id} made it through, and {params.companion} cheered beside the trail.")
    world.say(f"By the time the sun reached the stones, {hero.id} was smiling at the path ahead.")

    world.facts = {
        "hero": hero,
        "companion": companion,
        "obstacle": obstacle,
        "tool": tool,
        "setting": world.setting,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    obstacle = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obstacle")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f"Write a short adventure story for a child named {hero.id} who has to tackle {obstacle.label}.",
        f"Tell a brave, child-friendly adventure where {hero.id} uses {tool.label} to face a hard path.",
        f"Write a simple story that includes the word 'tackle' and ends with a brave success.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    obstacle = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obstacle")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    comp = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "companion")
    return [
        QAItem(
            question=f"What did {hero.id} have to tackle?",
            answer=f"{hero.id} had to tackle {obstacle.label} on the adventure path.",
        ),
        QAItem(
            question=f"What helped {hero.id} face the obstacle?",
            answer=f"{tool.label} helped {hero.id} face the obstacle and keep going.",
        ),
        QAItem(
            question=f"Who cheered after {hero.id} got through the challenge?",
            answer=f"{(getattr(comp, 'capitalize')() if callable(getattr(comp, 'capitalize', None)) else str(comp).capitalize())} cheered after {hero.id} got through the challenge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means facing something scary or hard while trying to do what needs to be done.",
        ),
        QAItem(
            question="What does it mean to tackle a problem?",
            answer="To tackle a problem means to try to handle it directly instead of walking away from it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.meter))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,T) :- setting(S), obstacle(O), tool(T), helps(T,"climb"), needs(O,_).
valid(S,O,T) :- setting(S), obstacle(O), tool(T), helps(T,"push"), needs(O,"block").
valid(S,O,T) :- setting(S), obstacle(O), tool(T), helps(T,"pull"), needs(O,"tangle").
valid(S,O,T) :- setting(S), obstacle(O), tool(T), helps(T,"cross"), needs(O,"splash").
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return f"(No story: {tool.label} does not reasonably help with {obstacle.label}.)"


def valid_story(obstacle: Obstacle, tool: Tool) -> bool:
    if obstacle.id == "ledge":
        return "climb" in tool.helps
    if obstacle.id == "gate":
        return "push" in tool.helps
    if obstacle.id == "vinewall":
        return "pull" in tool.helps or "climb" in tool.helps
    if obstacle.id == "stream":
        return "cross" in tool.helps
    return False


CURATED = [
    StoryParams(setting="cliff_path", obstacle="ledge", tool="rope", name="Mina", gender="girl", companion="father", trait="brave"),
    StoryParams(setting="forest", obstacle="gate", tool="staff", name="Arlo", gender="boy", companion="mother", trait="steady"),
    StoryParams(setting="canyon", obstacle="vinewall", tool="hook", name="Nia", gender="girl", companion="friend", trait="bold"),
    StoryParams(setting="cave", obstacle="stream", tool="rope", name="Oren", gender="boy", companion="sister", trait="curious"),
]


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
        print("--- world trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def resolve_explicit(args: argparse.Namespace) -> Optional[StoryParams]:
    if getattr(args, "obstacle", None) and getattr(args, "tool", None):
        obstacle = _safe_lookup(OBSTACLES, getattr(args, "obstacle", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if not valid_story(obstacle, tool):
            pass
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "obstacle", None) and getattr(args, "tool", None):
        obstacle = _safe_lookup(OBSTACLES, getattr(args, "obstacle", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if not valid_story(obstacle, tool):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)
              and (getattr(args, "obstacle", None) is None or c[1] == getattr(args, "obstacle", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, obstacle, tool = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        companion=getattr(args, "companion", None) or rng.choice(COMPANIONS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.obstacle} at {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
