#!/usr/bin/env python3
"""
storyworlds/worlds/jockey_monitor_dialogue_tall_tale.py
========================================================

A standalone story world for a tall-tale style scene about a jockey and a
monitor, told through dialogue and grounded in a small stateful simulation.

Premise:
- A daring jockey wants to race in a dusty little arena.
- A monitor in the tack room is supposed to show the route and the weather.
- The monitor starts flashing the wrong thing, making the race plan go sideways.
- The jockey and a helper talk it through, fix the monitor, and ride on.

The story model tracks:
- meters: dust, speed, brightness, signal, distance, steadiness
- memes: worry, pride, patience, trust, wonder, relief

The narration is intentionally tall-tale flavored: lively, concrete, and
dialogue-forward, while still driven by the world state rather than a frozen
template.
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
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    jockey: object | None = None
    mon: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "speed": 0.0, "brightness": 0.0, "signal": 0.0, "distance": 0.0, "steadiness": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "pride": 0.0, "patience": 0.0, "trust": 0.0, "wonder": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mare"}
        male = {"boy", "man", "father", "stallion"}
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


@dataclass
class Setting:
    place: str = "the county fairgrounds"
    outdoors: bool = True
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
class Event:
    id: str
    verb: str
    rush: str
    consequence: str
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
class MonitorSpec:
    label: str
    phrase: str
    issue: str
    fix: str
    helps_with: set[str]
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
class StoryParams:
    place: str
    event: str
    monitor: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.event: Optional[Event] = None
        self.monitor_ok: bool = False

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


def _line(world: World, speaker: str, text: str) -> None:
    world.say(f'"{text}" {speaker} said.')


def _race_flicker(world: World) -> list[str]:
    out: list[str] = []
    jockey = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    monitor = next((e for e in world.entities.values() if e.type == "monitor"), None)
    if not jockey or not monitor or not world.event:
        return out
    if jockey.meters["dust"] < THRESHOLD or monitor.meters["signal"] < THRESHOLD:
        return out
    sig = ("flicker", jockey.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jockey.memes["worry"] += 1
    monitor.meters["brightness"] = max(monitor.meters["brightness"], 0.5)
    out.append("The monitor flashed like a firefly in a jar, and that made the jockey frown.")
    return out


def _fix_monitor(world: World) -> list[str]:
    out: list[str] = []
    monitor = next((e for e in world.entities.values() if e.type == "monitor"), None)
    helper = next((e for e in world.entities.values() if e.id == world.facts.get("helper").id), None)
    if not monitor or not helper:
        return out
    if monitor.meters["signal"] >= 2 or world.monitor_ok:
        return out
    sig = ("fix", monitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    monitor.meters["signal"] += 2
    monitor.meters["brightness"] += 1
    helper.memes["patience"] += 1
    helper.memes["trust"] += 1
    world.monitor_ok = True
    out.append("The helper wiped the glass and tapped the little box until the picture came back true.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_race_flicker, _fix_monitor):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, event: Event, monitor: MonitorSpec, hero_name: str, hero_type: str,
         helper_type: str, trait: str) -> World:
    world = World(setting)
    world.event = event

    jockey = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"dust": 0.0, "speed": 0.0, "brightness": 0.0, "signal": 0.0, "distance": 0.0, "steadiness": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "patience": 0.0, "trust": 0.0, "wonder": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        meters={"dust": 0.0, "speed": 0.0, "brightness": 0.0, "signal": 0.0, "distance": 0.0, "steadiness": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "patience": 0.0, "trust": 0.0, "wonder": 0.0, "relief": 0.0},
    ))
    mon = world.add(Entity(
        id="Monitor",
        kind="thing",
        type="monitor",
        label=monitor.label,
        phrase=monitor.phrase,
        meters={"dust": 0.0, "speed": 0.0, "brightness": 0.0, "signal": 0.0, "distance": 0.0, "steadiness": 0.0},
    ))

    world.facts.update(hero=jockey, helper=helper, monitor=mon, event=event, setting=setting, trait=trait)

    world.say(f"{hero_name} was a little {trait} {hero_type} who could sit a horse as neatly as a crow on a fencepost.")
    world.say(f"{hero_name} liked the {event.keyword} race because the hooves kicked up dust and the wind sang in the rails.")
    world.say(f"The helper pointed to {monitor.label.lower()} and said it could show the route as clear as moonlight on a tin pail.")

    world.para()
    world.say(f"At {setting.place}, {hero_name} tightened the saddle and looked at the screen.")
    _line(world, hero_name, f"I'm ready to {event.verb} if that monitor can keep up.")
    _line(world, "the helper", f"Let's see if that box can tell a true story today.")

    jockey.meters["dust"] += 1
    jockey.meters["speed"] += 1
    jockey.meters["distance"] += 1
    monitor.meters["signal"] += 1
    propagate(world)

    world.para()
    _line(world, hero_name, f"Why is it blinking like a thunderbug?")
    _line(world, "the helper", f"Because the signal is weak, and a weak signal can make a bold picture lie.")
    jockey.memes["worry"] += 1
    helper.memes["wonder"] += 1
    world.say(f"{hero_name} leaned closer, and the dusty air made {hero_name}'s {event.rush} sound even grander.")

    monitor.meters["signal"] += 1
    propagate(world)

    world.para()
    _line(world, "the helper", f"Now hold still while I clean the lens and reset the dials.")
    _line(world, hero_name, f"If you can steady that monitor, I can ride straight as a fence rail.")
    helper.memes["patience"] += 1
    jockey.memes["trust"] += 1
    jockey.meters["steadiness"] += 1
    monitor.meters["signal"] += 1
    propagate(world)

    world.para()
    if world.monitor_ok:
        jockey.memes["relief"] += 1
        jockey.memes["pride"] += 1
        world.say(f"The screen cleared, and the route shone plain as a road on a bright noon.")
        _line(world, hero_name, f"There now! I can see every turn, and my horse can too.")
        _line(world, "the helper", f"Ride on, then. The monitor tells the truth again.")
        world.say(f"So {hero_name} rode off under a sky as wide as a blue quilt, and the monitor kept the map steady while the dust danced behind {jockey.pronoun('object')}.")
    else:
        jockey.memes["worry"] += 1
        world.say(f"The monitor never came right, so the race waited, grumbling gently like a kettle on the stove.")
        _line(world, hero_name, f"No sense racing a false picture.")
        _line(world, "the helper", f"Then let's mend it before the bell rings twice.")

    world.facts["resolved"] = world.monitor_ok
    return world


SETTINGS = {
    "fair": Setting(place="the county fairgrounds", outdoors=True, affords={"race"}),
    "track": Setting(place="the dusty track", outdoors=True, affords={"race"}),
    "stable_yard": Setting(place="the stable yard", outdoors=True, affords={"race"}),
}

EVENTS = {
    "race": Event(
        id="race",
        verb="race the moonbeam lane",
        rush="dash toward the starting gate",
        consequence="the horse could run straight",
        keyword="race",
        tags={"race", "horse", "dust"},
    ),
}

MONITORS = {
    "route_monitor": MonitorSpec(
        label="a route monitor",
        phrase="a small route monitor with a glassy face",
        issue="flickering",
        fix="a wiped lens and a reset dial",
        helps_with={"race"},
    ),
    "weather_monitor": MonitorSpec(
        label="a weather monitor",
        phrase="a weather monitor that showed clouds and wind",
        issue="blinking",
        fix="a steadier signal",
        helps_with={"race"},
    ),
}

GIRL_NAMES = ["Luna", "Mabel", "Ivy", "Nora", "Ruby", "Sadie"]
BOY_NAMES = ["Buck", "Eli", "Jace", "Milo", "Otis", "Wade"]
TRAITS = ["brave", "lively", "nimble", "curious", "spirited", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event_id in setting.affords:
            for mon_id, mon in MONITORS.items():
                if event_id in mon.helps_with:
                    combos.append((place, event_id, mon_id))
    return combos


@dataclass
class RunParams:
    place: str
    event: str
    monitor: str
    name: str
    gender: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a tall-tale story for a child about {hero.id}, a jockey, and a monitor that keeps blinking at the wrong time.',
        f'Tell a dialogue-heavy story where {hero.id} tries to {f["event"].verb} and a helper fixes the monitor first.',
        f'Write a short, funny cowboy-style race story that includes a monitor, a jockey, and a true picture at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    monitor = _safe_fact(world, f, "monitor")
    event = _safe_fact(world, f, "event")
    trait = _safe_fact(world, f, "trait")
    qa = [
        QAItem(
            question=f"Who was the story mainly about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {trait} {hero.type}, and {helper.label} helping with {monitor.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the monitor started blinking?",
            answer=f"{hero.id} wanted to {event.verb}. The race was big, dusty, and full of tall-tale excitement.",
        ),
        QAItem(
            question=f"Why did {hero.id} frown when the screen flashed?",
            answer=f"{hero.id} frowned because the monitor was not giving a clear signal, and a false screen can make a rider doubt the route.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How was the monitor fixed in the end?",
            answer=f"The helper wiped the lens, reset the dial, and made the signal steady again so the route could show plainly.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel after the monitor worked right?",
            answer=f"{hero.id} felt proud and relieved, because the picture turned clear and the race could go on the honest way.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jockey?",
            answer="A jockey is a person who rides a horse in a race.",
        ),
        QAItem(
            question="What is a monitor?",
            answer="A monitor is a screen or display that shows pictures, words, or signals so people can see information.",
        ),
        QAItem(
            question="Why does a screen need a good signal?",
            answer="A good signal helps the screen show the right picture without blinking or going fuzzy.",
        ),
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fair", event="race", monitor="route_monitor", name="Luna", gender="girl", helper="assistant", trait="brave"),
    StoryParams(place="track", event="race", monitor="weather_monitor", name="Buck", gender="boy", helper="stablehand", trait="bold"),
    StoryParams(place="stable_yard", event="race", monitor="route_monitor", name="Milo", gender="boy", helper="watcher", trait="nimble"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a jockey, a monitor, and a dialogue-driven fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--monitor", choices=MONITORS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
              and (getattr(args, "monitor", None) is None or c[2] == getattr(args, "monitor", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, monitor = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["assistant", "stablehand", "watcher", "coach"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, monitor=monitor, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EVENTS, params.event), _safe_lookup(MONITORS, params.monitor),
                 params.name, params.gender, params.helper, params.trait)
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
place(fair). place(track). place(stable_yard).
event(race).
monitor(route_monitor). monitor(weather_monitor).

affords(fair,race).
affords(track,race).
affords(stable_yard,race).

helps(route_monitor,race).
helps(weather_monitor,race).

valid(Place,Event,Monitor) :- affords(Place,Event), helps(Monitor,Event).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for e in _safe_lookup(SETTINGS, p).affords:
            lines.append(asp.fact("affords", p, e))
    for e in EVENTS:
        lines.append(asp.fact("event", e))
    for m in MONITORS:
        lines.append(asp.fact("monitor", m))
        for k in _safe_lookup(MONITORS, m).helps_with:
            lines.append(asp.fact("helps", m, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
            header = f"### {p.name}: {p.event} at {p.place} (monitor: {p.monitor})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
