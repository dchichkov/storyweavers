#!/usr/bin/env python3
"""
Story world: achoo-dim rhyming suspense with a small transformation and a bad ending.

The seed inspiration is a tiny rhyming tale where a dim room, a building sneeze,
and a strange change in shape create a suspenseful turn. The story ends badly:
the fix arrives too late, the change is irreversible, and the final image proves
what has changed.

This script is self-contained and follows the Storyweavers contract.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    dim: bool = True
    echo: str = ""
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    spark: str
    danger: str
    change_to: str
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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


@dataclass
class Twist:
    id: str
    label: str
    cause: str
    result: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
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
        self.trace_events: list[str] = []
        self.weather = "dim"

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
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def _apply_spark(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    if hero.meters.get("sneeze", 0.0) < THRESHOLD:
        return out
    if ("spark", hero.id) in world.fired:
        return out
    world.fired.add(("spark", hero.id))
    world.facts["sparked"] = True
    out.append("A tiny spark of change began to glow.")
    return out


def _apply_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    twist: Twist = _safe_fact(world, world.facts, "twist")
    if hero.meters.get("sneeze", 0.0) < THRESHOLD:
        return out
    if ("transform", hero.id, twist.id) in world.fired:
        return out
    world.fired.add(("transform", hero.id, twist.id))
    hero.type = twist.result
    hero.label = twist.result
    hero.meters["changed"] = 1.0
    out.append("__transform__")
    return out


def _apply_bad_ending(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    if hero.meters.get("changed", 0.0) < THRESHOLD:
        return []
    if ("ending", hero.id) in world.fired:
        return []
    world.fired.add(("ending", hero.id))
    world.facts["bad_end"] = True
    return ["__ending__"]


RULES = [_apply_spark, _apply_transform, _apply_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            items = rule(world)
            if items:
                changed = True
                for item in items:
                    if item not in {"__transform__", "__ending__"}:
                        produced.append(item)
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def build_setting() -> Setting:
    return Setting(
        place="the dim den",
        dim=True,
        echo="soft",
        affords={"peek", "sneeze", "search"},
    )


SETTINGS = {
    "dim_den": build_setting(),
    "dim_hall": Setting(place="the dim hall", dim=True, echo="hollow", affords={"peek", "sneeze"}),
    "dim_attic": Setting(place="the dim attic", dim=True, echo="creaky", affords={"search", "sneeze"}),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="peek at the box",
        gerund="peeking at the box",
        rush="tiptoe to the box",
        spark="a flicker in the dark",
        danger="the lid might snap shut",
        change_to="owl",
        tags={"dim", "suspense"},
    ),
    "sneeze": Action(
        id="sneeze",
        verb="let out an achoo",
        gerund="sneezing in the gloom",
        rush="cover the nose and cry achoo",
        spark="the air could wobble",
        danger="dust could swirl and bite",
        change_to="mouse",
        tags={"achoo-dim", "suspense", "transformation"},
    ),
    "search": Action(
        id="search",
        verb="search the shadows",
        gerund="searching the shadows",
        rush="feel along the wall",
        spark="the floor might shimmer",
        danger="the room could turn strange",
        change_to="cat",
        tags={"dim", "transformation"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a little brass lantern", type="lantern", region="hand"),
    "cloak": Prize(label="cloak", phrase="a soft blue cloak", type="cloak", region="back"),
}

TWISTS = {
    "mouse": Twist(
        id="mouse",
        label="mouse",
        cause="the sneeze and dust",
        result="mouse",
        ending_image="A small mouse blinked in the dim den, with whiskers where a smile had been.",
        tags={"achoo-dim", "transformation"},
    ),
    "owl": Twist(
        id="owl",
        label="owl",
        cause="the hush and the shadow",
        result="owl",
        ending_image="A round owl sat where a child had stood, and the night felt colder than before.",
        tags={"dim", "transformation"},
    ),
    "cat": Twist(
        id="cat",
        label="cat",
        cause="the shadowed search",
        result="cat",
        ending_image="A skinny cat stared from the dark, but the way home was gone.",
        tags={"dim", "transformation"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Eli"]
KINDS = {"girl", "boy"}
TRAITS = ["tiny", "curious", "brave", "sleepy", "lively"]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    twist: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for a_id in s.affords:
            for p_id in PRIZES:
                if a_id == "sneeze":
                    combos.append((s_id, a_id, p_id))
                elif a_id == "peek" and p_id == "lantern":
                    combos.append((s_id, a_id, p_id))
                elif a_id == "search" and p_id == "cloak":
                    combos.append((s_id, a_id, p_id))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return f"(No story: {action.verb} does not fit with {prize.phrase} in a way that would make a real suspenseful change.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming suspense story world with achoo-dim transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        if (getattr(args, "setting", None) and (getattr(args, "setting", None), getattr(args, "action", None), getattr(args, "prize", None)) not in combos):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos
                if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
                and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, action, prize = rng.choice(list(filtered))
    twist = getattr(args, "twist", None) or rng.choice(sorted(TWISTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, action, prize, twist, name, gender, trait)


def _build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label,
                             phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id))
    twist = _safe_lookup(TWISTS, params.twist)
    world.facts.update(hero=hero, prize=prize, twist=twist, action=_safe_lookup(ACTIONS, params.action))

    world.say(f"{hero.id} was a {params.trait} {hero.type} in {world.setting.place}, where the lamps were dim and dim.")
    world.say(f"{hero.id} held {prize.phrase}, and {hero.pronoun('possessive')} heart beat with a rim of whim.")
    world.para()
    act = _safe_lookup(ACTIONS, params.action)
    world.say(f"{hero.id} wanted to {act.verb}, but the room grew hush and the shadow grew grim.")
    world.say(f"Then came the warning: {act.danger}, and the air felt thin and trim.")
    hero.meters["sneeze"] += 1.0
    hero.memes["suspense"] += 1.0
    propagate(world, narrate=False)
    if params.action == "sneeze":
        world.say(f"{hero.id} tried to hold it back, but the sneeze rose up with a little odd hymn.")
        world.say(f'"Achoo," went {hero.id}, and the dark seemed to spin and skim.')
    elif params.action == "peek":
        world.say(f"{hero.id} leaned in to peek, and the lantern flame shivered and slim.")
    else:
        world.say(f"{hero.id} searched the shadows, and the floor gave a soft, strange dim.")
    # Finish the bad ending after transformation.
    world.para()
    if world.facts.get("bad_end"):
        world.say(twist.ending_image)
        world.say(f"Too late for a fix, and too late for a grin; the change was set in its brim.")
        world.say(f"{hero.id} stayed changed in the dim den, and the night closed over the rim.")
    else:
        world.say("The room settled down, but the ending still felt quiet and slim.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act: Action = _safe_fact(world, f, "action")
    twist: Twist = _safe_fact(world, f, "twist")
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short rhyming story for a child about "{act.id}" in a dim room.',
        f"Tell a suspenseful tiny story where {hero.id} wants to {act.verb} and a {twist.label} transformation follows.",
        f'Write a simple story that includes the word "achoo-dim" and ends with a bad ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    action: Action = _safe_fact(world, f, "action")
    twist: Twist = _safe_fact(world, f, "twist")
    qa = [
        QAItem(
            question=f"Who was in the dim room with {prize.label}?",
            answer=f"{hero.id} was in the dim room with {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the strange change?",
            answer=f"{hero.id} wanted to {action.verb}, but the room felt tense and dim.",
        ),
        QAItem(
            question=f"What kind of change happened in the story?",
            answer=f"A {twist.label} transformation happened after the {action.id}, and it was not fixed in time.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {twist.ending_image}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright. A dim room has low light, so it can feel quiet and a little spooky.",
        ),
        QAItem(
            question="What is a sneeze?",
            answer="A sneeze is a sudden burst of air from your nose and mouth. It often sounds like 'achoo!'",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another, like when something becomes a different kind of thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("dim_den", "sneeze", "lantern", "mouse", "Mia", "girl", "tiny"),
    StoryParams("dim_hall", "peek", "lantern", "owl", "Leo", "boy", "curious"),
    StoryParams("dim_attic", "search", "cloak", "cat", "Nora", "girl", "brave"),
]


ASP_RULES = r"""
setting(dim_den).
setting(dim_hall).
setting(dim_attic).

affords(dim_den, peek).
affords(dim_den, sneeze).
affords(dim_den, search).
affords(dim_hall, peek).
affords(dim_hall, sneeze).
affords(dim_attic, search).
affords(dim_attic, sneeze).

prize(lantern).
prize(cloak).

valid(Setting, Action, Prize) :- affords(Setting, Action), action(Action), prize(Prize),
                                  compatible(Action, Prize).

action(peek). action(sneeze). action(search).

compatible(sneeze, lantern).
compatible(sneeze, cloak).
compatible(peek, lantern).
compatible(search, cloak).

heroic_story(Setting, Action, Prize) :- valid(Setting, Action, Prize).
#show valid/3.
#show heroic_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


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


def build_world_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
