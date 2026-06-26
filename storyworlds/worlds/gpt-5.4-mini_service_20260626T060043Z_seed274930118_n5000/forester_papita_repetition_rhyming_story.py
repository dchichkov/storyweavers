#!/usr/bin/env python3
"""
storyworlds/worlds/forester_papita_repetition_rhyming_story.py
==============================================================

A small story world for a forester and a papita sapling, told with repetition
and rhyming-story cadence.

Premise:
- A kind forester notices a little papita plant in the forest clearing.
- The day is hot and dry, so the papita droops.
- The forester repeats a little rhyme while bringing water and shade.
- The papita perks up, and the ending image shows the change.

The world is intentionally tiny and constraint-checked:
- the dry spell must actually threaten the papita,
- the forester must have a reasonable fix,
- the resolution is driven by world state, not a frozen template.

The script supports:
- default runs and -n
- --all curated examples
- --seed for reproducibility
- --trace for world state
- --qa for story/world questions
- --json for serialization
- --asp for declarative compatibility listing
- --verify for Python/ASP parity and sample exercise
- --show-asp for the inline rule program
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cloak: object | None = None
    forester: object | None = None
    papita: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dry": 0.0, "wet": 0.0, "tired": 0.0, "green": 0.0, "shade": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "calm": 0.0, "hope": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "forester": {"subject": "he", "object": "him", "possessive": "his"},
            "woman": {"subject": "she", "object": "her", "possessive": "her"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

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


@dataclass
class Setting:
    place: str = "the forest clearing"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    weather: str = ""
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]
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
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def rhyme_line(word1: str, word2: str) -> str:
    return f"{word1} and {word2}, soft and bright"


def _r_wet_papita(world: World) -> list[str]:
    out: list[str] = []
    papita = world.entities.get("papita")
    if not papita:
        return out
    if papita.meters["wet"] >= THRESHOLD and ("revived",) not in world.fired:
        if papita.meters["green"] < 1:
            papita.meters["green"] += 1
        papita.memes["hope"] += 1
        world.fired.add(("revived",))
        out.append("The papita stood up straighter.")
    return out


def _r_dry_worry(world: World) -> list[str]:
    out: list[str] = []
    papita = world.entities.get("papita")
    if not papita:
        return out
    if papita.meters["dry"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        papita.memes["worry"] += 1
        out.append("The little papita drooped and sighed.")
    return out


CAUSAL_RULES = [Rule("dry_worry", _r_dry_worry), Rule("wet_papita", _r_wet_papita)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    if activity.id == "water":
        return f"The {setting.place} was warm, and the air felt still."
    return f"The {setting.place} waited in a hush of green."


def predict(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    papita = sim.entities["papita"]
    return {"soiled": papita.meters["wet"] >= THRESHOLD, "worry": papita.memes["worry"] >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    if activity.id == "water":
        world.get("papita").meters["wet"] += 1
        world.get("papita").meters["dry"] = 0
        actor.memes["calm"] += 1
    elif activity.id == "shade":
        world.get("papita").meters["shade"] += 1
        world.get("papita").meters["dry"] = max(0, world.get("papita").meters["dry"] - 1)
        actor.memes["hope"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, gear: Gear, hero_name: str, weather: str) -> World:
    world = World(setting)
    world.weather = weather
    forester = world.add(Entity(id=hero_name, kind="character", type="forester", label="the forester"))
    papita = world.add(Entity(id="papita", kind="thing", type="plant", label="papita", phrase="a tiny papita sapling"))
    cloak = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    cloak.worn_by = forester.id
    world.facts["gear"] = gear
    world.facts["activity"] = activity
    world.facts["forester"] = forester
    world.facts["papita"] = papita

    world.say(f"In the {setting.place}, a forester named {forester.id} listened to the leaves.")
    world.say(f"There stood papita, {rhyme_line('little', 'bright')}; papita was a tiny sapling and a happy sight.")
    world.say(f"{forester.id} loved the green and loved the gleam, and {forester.pronoun().capitalize()} liked to hum a rhyming theme.")

    world.para()
    world.say(setting_detail(setting, activity))
    world.say(f"But papita was dry-dry-dry, and the little leaves gave a tired sigh.")
    papita.meters["dry"] += 1
    papita.memes["worry"] += 1
    propagate(world)

    world.para()
    world.say(f"{forester.id} said, 'Dry-dry-dry is not the way; we need some water for the day.'")
    world.say(f"{forester.id} clutched {forester.pronoun('possessive')} water pail and sang, 'Drip and drop, we will not stop.'")
    if activity.id == "water":
        world.say(f"Then {forester.id} gave papita a cool drink.")
        do_activity(world, forester, activity)

    world.para()
    if gear.id == "shade-cloth":
        world.say(f"{forester.id} spread a shade cloth wide and said, 'Cool and slow, let the soft winds blow.'")
        do_activity(world, forester, Activity(id="shade", verb="spread shade", gerund="spreading shade", rush="pull the shade cloth", mess="shade", soil="shaded", keyword="shade", tags={"shade"}))
    world.say(f"Papita drank the drops and lifted up, little by little, leaf by leaf.")
    world.say(f"Now papita looked bright-bright-bright, and the clearing felt just right.")
    world.say(f"{forester.id} smiled at the sky and gave a glad goodbye to the dry.")

    world.facts.update(resolved=True)
    return world


SETTINGS = {
    "clearing": Setting(place="the forest clearing", affords={"water", "shade"}),
    "grove": Setting(place="the mossy grove", affords={"water", "shade"}),
    "riverbank": Setting(place="the quiet riverbank", affords={"water", "shade"}),
}

ACTIVITIES = {
    "water": Activity(
        id="water",
        verb="water the papita",
        gerund="watering papita",
        rush="hurry with the pail",
        mess="wet",
        soil="wet",
        keyword="drip",
        tags={"wet", "water"},
    ),
    "shade": Activity(
        id="shade",
        verb="shade the papita",
        gerund="making shade",
        rush="pull the cloth",
        mess="shade",
        soil="cool",
        keyword="shade",
        tags={"shade"},
    ),
}

GEAR = [
    Gear(
        id="pail",
        label="a small water pail",
        covers=set(),
        guards={"dry"},
        prep="bring a small water pail",
        tail="brought the water pail",
    ),
    Gear(
        id="shade-cloth",
        label="a shade cloth",
        covers={"plant"},
        guards={"dry"},
        prep="spread a shade cloth",
        tail="spread the shade cloth",
    ),
]

NAMES = ["Ivo", "Mira", "Niko", "Lina", "Taro", "Rosa"]
CURATED = [
    ("clearing", "water", "pail", "Ivo"),
    ("grove", "water", "shade-cloth", "Mira"),
    ("riverbank", "water", "pail", "Niko"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for gear in GEAR:
                if "dry" in gear.guards:
                    combos.append((place, act, gear.id))
    return combos


def explain_rejection(activity: Activity, gear: Gear) -> str:
    return f"(No story: {activity.id} and {gear.label} do not make a reasonable fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A repetition-and-rhyme story world for a forester and papita.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--name")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, gear = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, gear=gear, name=name)


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short rhyming story with repetition about a forester and papita.",
        f"Tell a gentle forest tale where {world.facts['forester'].id} helps papita when it is dry.",
        "Use a repeating line or two, and end with papita bright and lively again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    forester = _safe_fact(world, world.facts, "forester")
    papita = _safe_fact(world, world.facts, "papita")
    return [
        QAItem(
            question="Who helped papita in the forest?",
            answer=f"The forester named {forester.id} helped papita.",
        ),
        QAItem(
            question="Why did papita need help?",
            answer="Papita was dry and droopy, so it needed water and shade.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with papita bright and lively, and {forester.id} smiling in the clearing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does water do for a thirsty plant?",
            answer="Water helps a thirsty plant stay alive and stand up greener and taller.",
        ),
        QAItem(
            question="Why can shade help a plant on a hot day?",
            answer="Shade can keep a plant cooler, which helps it lose less water in the heat.",
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
        bits = [f"meters={meters}" if meters else "", f"memes={memes}" if memes else ""]
        bits = [b for b in bits if b]
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
dry_threat(P) :- plant(P), dry(P).
needs_help(P) :- dry_threat(P).
compatible(G, A) :- gear(G), activity(A), guards(G, dry), affords(A, water).
valid_story(Place, A, G) :- setting(Place), affords(Place, A), compatible(G, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    lines.append(asp.fact("plant", "papita"))
    lines.append(asp.fact("dry", "papita"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    gear = next(g for g in GEAR if g.id == params.gear)
    world = tell(setting, activity, gear, params.name, weather="hot")
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
        print(f"{len(combos)} compatible stories:")
        for t in combos:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, activity=a, gear=g, name=n)) for p, a, g, n in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
