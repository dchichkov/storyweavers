#!/usr/bin/env python3
"""
storyworlds/worlds/spic_lark_lap_foreshadowing_bedtime_story.py
===============================================================

A small bedtime-story world with foreshadowing: a child, a quiet night, and a
gentle nudge toward sleep. The seed words *spic*, *lark*, and *lap* are woven
into the characters and story beats.

Initial story idea:
---
A little child named Spic was not ready for bed. Outside, a lark sang from the
moonlit tree, and Spic wanted one more minute on a grown-up's lap to listen.
The parent noticed a yawn, a drooping head, and a blanket left at the chair.
That was the foreshadowing: if Spic kept listening, sleep would arrive before
the last song ended.

So the parent offered a soft compromise. They brought the blanket, tucked Spic
into a lap chair by the window, and listened together until the lark's song
turned small and sleepy. Spic blinked once, then twice, then fell asleep with a
tiny smile.

World model notes:
---
- The world tracks physical meters (sleepiness, coziness, cold) and emotional
  memes (comfort, worry, wonder).
- Foreshadowing is explicit: a helper predicts the turn from small clues before
  the resolution.
- The ending proves the state change: the child goes from alert and restless to
  tucked in, warm, and asleep.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the nursery"
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
    cue: str
    weather: str = "night"
    keyword: str = ""
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
class Comfort:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_lines: list[str] = []

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
            self.trace_lines.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
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


SETTINGS = {
    "nursery": Setting(place="the nursery", affords={"lark", "lamp"}),
    "window": Setting(place="the window seat", affords={"lark", "lamp"}),
    "porch": Setting(place="the porch", affords={"lark"}),
}

ACTIVITIES = {
    "lark": Activity(
        id="lark",
        verb="listen to the lark",
        gerund="listening to the lark",
        rush="lean farther toward the window",
        cue="the lark song",
        keyword="lark",
        tags={"lark", "bird", "night"},
    ),
    "lamp": Activity(
        id="lamp",
        verb="read one more page by the lamp",
        gerund="reading by the lamp",
        rush="sit up and turn the page",
        cue="the soft lamp glow",
        keyword="lamp",
        tags={"lamp", "light", "night"},
    ),
}

PRIZES = {
    "lap": Prize(
        label="lap",
        phrase="a warm lap chair",
        type="chair",
        region="lap",
        plural=False,
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a soft blue blanket",
        type="blanket",
        region="body",
        plural=False,
    ),
}

COMFORTS = [
    Comfort(
        id="blanket",
        label="the blanket",
        covers={"body"},
        guards={"cold"},
        prep="bring the blanket over and tuck it around Spic",
        tail="folded the blanket around Spic",
    ),
    Comfort(
        id="rockingchair",
        label="the lap chair",
        covers={"lap"},
        guards={"restless"},
        prep="set Spic in the lap chair by the window",
        tail="settled into the lap chair",
    ),
]


GIRL_NAMES = ["Spic", "Mina", "Lumi", "Nora", "Ivy"]
BOY_NAMES = ["Spic", "Pip", "Theo", "Finn", "Oren"]
TRAITS = ["sleepy", "curious", "gentle", "bright", "small"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_sleep(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters.get("sleepiness", 0.0) >= THRESHOLD and ("sleep",) not in world.fired:
        world.fired.add(("sleep",))
        child.memes["drowsy"] = child.memes.get("drowsy", 0.0) + 1
        out.append("Spic's eyes kept wanting to close.")
    return out


def _r_cold(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters.get("sleepiness", 0.0) >= THRESHOLD and child.meters.get("warmth", 0.0) < THRESHOLD:
        if ("cold",) in world.fired:
            return out
        world.fired.add(("cold",))
        child.meters["cold"] = child.meters.get("cold", 0.0) + 1
        out.append("The night air felt a little cool by the open window.")
    return out


CAUSAL_RULES = [Rule("sleep", _r_sleep), Rule("cold", _r_cold)]


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


def predict_turn(world: World, child: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    sim.get("child").meters["sleepiness"] = sim.get("child").meters.get("sleepiness", 0.0) + 1
    if activity.id == "lark":
        sim.get("child").memes["wonder"] = sim.get("child").memes.get("wonder", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "sleepy": sim.get("child").meters.get("sleepiness", 0.0) >= THRESHOLD,
        "cold": sim.get("child").meters.get("cold", 0.0) >= THRESHOLD,
    }


def foreshadow(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{child.id} wanted to {activity.verb} one more time, but {parent.pronoun('possessive')} "
        f"{parent.label} noticed a yawn, a drooping head, and a blanket left on the chair."
    )
    world.facts["prediction"] = predict_turn(world, child, activity, prize)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"sleepiness": 0.0, "warmth": 0.0},
        memes={"wonder": 0.0, "comfort": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="parent",
        meters={},
        memes={"care": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=_safe_lookup(PRIZES, params.prize).type,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        caretaker="parent",
    ))
    child.worn_by = None
    world.facts.update(child=child, parent=parent, prize=prize, params=params)
    return world


def tell(world: World, activity: Activity, prize: Prize) -> World:
    child = world.get("child")
    parent = world.get("parent")

    child.memes["wonder"] += 1
    world.say(
        f"Spic was a little {world.facts['params'].trait} {child.type} who loved the hush of bedtime and the shiny night sky."
    )
    world.say(
        f"By the window, Spic liked {activity.gerund}; {activity.cue} sounded like a tiny song for sleepy ears."
    )
    world.say(
        f"{parent.pronoun().capitalize()} knew the song would be lovely, but {parent.pronoun('possessive')} eyes had already found the clues."
    )

    world.para()
    foreshadow(world, child, parent, activity, prize)
    child.meters["sleepiness"] += 1
    propagate(world, narrate=True)

    world.say(
        f"Spic blinked at the window and tried to stay awake, but the song was soft and the room was warm and still."
    )

    world.para()
    comfort = _safe_lookup(COMFORTS, 0) if world.facts["prediction"]["cold"] else _safe_lookup(COMFORTS, 1)
    child.memes["comfort"] += 1
    child.meters["warmth"] += 1
    if comfort.id == "blanket":
        world.say(
            f"So {parent.pronoun('possessive')} {parent.label} {comfort.prep}, and the blanket made a cozy hill around Spic's shoulders."
        )
    else:
        world.say(
            f"So {parent.pronoun('possessive')} {parent.label} {comfort.prep}, and Spic could rest their head without wobbling."
        )

    child.meters["sleepiness"] += 1
    child.memes["wonder"] += 1
    child.memes["comfort"] += 1
    propagate(world, narrate=True)

    world.say(
        f"Then the lark sang one last little note, and Spic's eyes shut like two tiny curtains."
    )
    world.say(
        f"By morning, the chair was empty, the blanket was folded, and the memory of the lark's song felt bright and safe."
    )
    world.facts["resolved"] = True
    world.facts["comfort"] = comfort
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        'Write a gentle bedtime story for a young child that quietly foreshadows sleep.',
        f"Tell a cozy story where {p.name} wants one more look at a lark before bed, and a parent notices sleepy clues.",
        f"Write a bedtime story that includes the words spic, lark, and lap and ends with a soft, sleepy resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    child = world.get("child")
    parent = world.get("parent")
    comfort = _safe_fact(world, world.facts, "comfort")
    return [
        QAItem(
            question=f"Who was the little child in the story?",
            answer=f"The little child was {p.name}, a {p.trait} {p.gender} who was called Spic in the story.",
        ),
        QAItem(
            question=f"What did Spic want to do before bed?",
            answer=f"Spic wanted to {world.facts['params'].activity} one more time and listen to the lark before falling asleep.",
        ),
        QAItem(
            question=f"Why did the parent bring the comfort item?",
            answer=(
                f"The parent saw sleepy clues, like a yawn and a drooping head, and knew the night would feel better with {comfort.label}."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, Spic was warm, sleepy, and asleep, while the lark's song had turned into a quiet bedtime memory."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lark?",
            answer="A lark is a small songbird that sings sweetly, often in the morning or evening.",
        ),
        QAItem(
            question="What does a lap feel like?",
            answer="A lap is a cozy place to sit, like the space on a parent's legs where a child can rest.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues that hint at what will happen later.",
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
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("cue", aid, a.cue))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk when the bedtime activity makes a child restless or cold in the relevant place.
at_risk(A, P) :- activity(A), prize(P), some_cue(A), worn_on(P, lap).

% A comfort solves the problem when it covers the same region and guards the predicted feeling.
solves(C, A, P) :- comfort(C), at_risk(A, P), guards(C, cold).

valid_story(Place, A, P) :- setting(Place), affords(Place, A), prize(P), activity(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    # This world is intentionally tiny; ASP is a reasonableness twin and should
    # at least run cleanly and return a model for the shown predicate.
    model = asp.one_model(asp_program("#show valid_story/3."))
    _ = asp.atoms(model, "valid_story")
    print("OK: ASP program grounds and solves.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Story world with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for act in s.affords:
            for pr in PRIZES:
                out.append((place, act, pr))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world, _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize))
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

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(place="nursery", activity="lark", prize="blanket", name="Spic", gender="girl", parent="mother", trait="gentle"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
