#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a careful crystal display, a child who
wants to exceed a rule, a timely reminder, and a cautionary ending that still
leaves room for reconciliation.

Seed premise:
- A child wants to do one more playful thing around a crystal object.
- A caretaker reminds them to be careful.
- The child ignores the caution, exceeds the safe limit, and the crystal breaks.
- The story ends with an honest apology and a small reconciliation, but the
  broken object cannot be fully restored, so the ending remains cautionary.

The world is intentionally small and constraint-checked:
- crystals are delicate physical objects
- "exceed" means going beyond an agreed limit
- "remind" is a social action that can prevent trouble
- the bad ending is only valid if the crystal is actually damaged
- reconciliation is possible, but not magical repair
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
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    crystal: object | None = None
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


@dataclass
class Setting:
    place: str
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
    desire: str
    spill: str
    mess: str
    limit: int
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
class Crystal:
    label: str
    phrase: str
    type: str = "crystal"
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
class StoryParams:
    place: str
    activity: str
    crystal: str
    name: str
    gender: str
    caretaker: str
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
        self.lines: list[str] = []
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "shop": Setting(place="the little crystal shop", affords={"touch", "count"}),
    "home": Setting(place="the kitchen table", affords={"touch", "count"}),
    "museum": Setting(place="the quiet museum corner", affords={"touch", "count"}),
}

ACTIVITIES = {
    "touch": Activity(
        id="touch",
        verb="touch the crystal display",
        desire="reach for the crystal display",
        spill="reach too far",
        mess="scratch",
        limit=1,
        keyword="crystal",
        tags={"crystal", "delicate"},
    ),
    "count": Activity(
        id="count",
        verb="count the crystal pieces",
        desire="count the crystal pieces again and again",
        spill="keep adding one more",
        mess="crack",
        limit=3,
        keyword="exceed",
        tags={"crystal", "count", "exceed"},
    ),
}

CRYSTALS = {
    "orb": Crystal(label="crystal orb", phrase="a clear crystal orb"),
    "star": Crystal(label="crystal star", phrase="a tiny crystal star"),
    "pendant": Crystal(label="crystal pendant", phrase="a blue crystal pendant"),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Maya", "Zoe"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Ben", "Leo"]
TRAITS = ["quiet", "curious", "careful", "bright", "gentle", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for crys in CRYSTALS:
                combos.append((place, act_id, crys))
    return combos


def reasonableness_gate(activity: Activity, crystal: Crystal) -> bool:
    return activity.keyword == "crystal" or activity.keyword == "exceed"


def explain_rejection(activity: Activity, crystal: Crystal) -> str:
    return f"(No story: {activity.id} and {crystal.label} do not fit the cautionary crystal premise.)"


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_break(world: World) -> list[str]:
    out = []
    child = world.get("child")
    crystal = world.get("crystal")
    if child.memes.get("overlimit", 0) < THRESHOLD:
        return out
    if crystal.meters.get("damage", 0) >= THRESHOLD:
        return out
    crystal.meters["damage"] = crystal.meters.get("damage", 0) + 1
    out.append(f"The crystal gave a small, sharp crack.")
    return out


def _r_broken_sad(world: World) -> list[str]:
    crystal = world.get("crystal")
    child = world.get("child")
    if crystal.meters.get("damage", 0) < THRESHOLD:
        return []
    if child.memes.get("sad", 0) >= THRESHOLD:
        return []
    child.memes["sad"] = 1
    child.memes["guilt"] = child.memes.get("guilt", 0) + 1
    return [f"{child.id} felt the bad ending settle in their chest."]


RULES = [Rule("break", _r_break), Rule("sad", _r_broken_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def simulate_overlimit(world: World, child: Entity, activity: Activity) -> None:
    child.memes["overlimit"] = child.memes.get("overlimit", 0) + 1
    child.memes["restless"] = child.memes.get("restless", 0) + 1
    world.say(f"{child.id} kept going a little farther, trying to exceed the safe limit.")


def remind(world: World, caretaker: Entity, child: Entity, activity: Activity, crystal: Entity) -> None:
    child.memes["reminded"] = 1
    world.say(
        f"{caretaker.id} looked at the {crystal.label} and reminded {child.id}, "
        f'"Please be gentle. One more careful turn, and then stop."'
    )


def choose_bad_ending(world: World, child: Entity, crystal: Entity) -> None:
    if crystal.meters.get("damage", 0) >= THRESHOLD:
        world.say(
            f"{child.id} stared at the broken shine, and the day ended badly for the crystal."
        )


def reconcile(world: World, caretaker: Entity, child: Entity, crystal: Entity) -> None:
    child.memes["apology"] = 1
    child.memes["love"] = child.memes.get("love", 0) + 1
    caretaker.memes["soft"] = caretaker.memes.get("soft", 0) + 1
    world.say(
        f'{child.id} said, "I am sorry. I should have listened." '
        f'{caretaker.id} sighed, then knelt beside {child.id}. '
        f'They agreed to sweep up the glitter together.'
    )
    if crystal.meters.get("damage", 0) >= THRESHOLD:
        world.say(
            f"The crystal could not be made whole again, but the two of them were honest with each other."
        )


def tell(setting: Setting, activity: Activity, crystal_cfg: Crystal,
         name: str = "Mina", gender: str = "girl",
         caretaker_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=name, kind="character", type=gender, label=name,
        meters={"mess": 0.0}, memes={"joy": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker", kind="character", type=caretaker_type,
        label=caretaker_type, meters={"calm": 0.0}, memes={"care": 0.0},
    ))
    crystal = world.add(Entity(
        id="crystal", type="thing", label=crystal_cfg.label, phrase=crystal_cfg.phrase,
        caretaker=caretaker.id, fragile=True, meters={"damage": 0.0},
    ))

    world.say(
        f"{child.id} was a {trait} little {gender} who liked quiet corners and shiny things."
    )
    world.say(
        f"At {setting.place}, {child.id} loved {activity.desire}, especially when {crystal.phrase} caught the light."
    )
    world.say(
        f"One afternoon, {caretaker.id} set the {crystal.label} on a shelf and told {child.id} to be careful."
    )

    world.para()
    world.say(
        f"{child.id} wanted to {activity.verb}, but the wish to {activity.spill} kept growing."
    )
    remind(world, caretaker, child, activity, crystal)
    world.say(f"{child.id} nodded, but the nod did not last long.")
    simulate_overlimit(world, child, activity)
    propagate(world, narrate=True)

    world.para()
    choose_bad_ending(world, child, crystal)
    reconcile(world, caretaker, child, crystal)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        crystal=crystal,
        activity=activity,
        setting=setting,
        trait=trait,
        damaged=crystal.meters.get("damage", 0) >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    crystal = _safe_fact(world, f, "crystal")
    return [
        f'Write a short slice-of-life story for a young child about "{activity.keyword}", a reminder, and a crystal.',
        f"Tell a gentle cautionary story where {child.id} tries to {activity.verb} and must be reminded to stop before the crystal is hurt.",
        f'Write a simple story that includes the words "exceed", "crystal", and "remind", and ends with reconciliation after a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    caretaker: Entity = _safe_fact(world, f, "caretaker")
    crystal: Entity = _safe_fact(world, f, "crystal")
    activity: Activity = _safe_fact(world, f, "activity")

    qs = [
        QAItem(
            question=f"Who wanted to {activity.verb} in the story?",
            answer=f"{child.id} wanted to {activity.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {caretaker.id} remind {child.id} to be careful?",
            answer=f"{caretaker.id} reminded {child.id} because the {crystal.label} was delicate and could be hurt if {child.id} tried to exceed the safe limit.",
        ),
        QAItem(
            question=f"What happened after {child.id} ignored the reminder?",
            answer=f"{child.id} went too far, the crystal cracked, and the day turned into a bad ending for the crystal.",
        ),
        QAItem(
            question=f"How did the story end after the mistake?",
            answer=f"{child.id} apologized, {caretaker.id} answered kindly, and they cleaned up together, so the two were reconciled even though the crystal stayed broken.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crystal like?",
            answer="A crystal is often shiny and beautiful, but it can also be fragile and break if it is treated roughly.",
        ),
        QAItem(
            question="What does it mean to remind someone?",
            answer="To remind someone is to tell them again about something important, so they do not forget.",
        ),
        QAItem(
            question="What does exceed mean?",
            answer="To exceed means to go past a limit or do more than was allowed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shop", activity="touch", crystal="orb", name="Mina", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(place="home", activity="count", crystal="pendant", name="Theo", gender="boy", caretaker="father", trait="restless"),
    StoryParams(place="museum", activity="touch", crystal="star", name="Ivy", gender="girl", caretaker="mother", trait="gentle"),
]


ASP_RULES = r"""
% A crystal story is valid when the child exceeds a limit and the crystal is at risk.
at_risk(A, C) :- activity(A), crystal(C), wants(A, C).
valid_story(P, A, C) :- affords(P, A), at_risk(A, C), can_break(A, C).

% Simple declarative twin:
wants(touch, orb). wants(touch, star). wants(touch, pendant).
wants(count, orb). wants(count, star). wants(count, pendant).
can_break(touch, orb). can_break(touch, star). can_break(touch, pendant).
can_break(count, orb). can_break(count, star). can_break(count, pendant).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for cid in CRYSTALS:
        lines.append(asp.fact("crystal", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life crystal cautionary storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--crystal", choices=CRYSTALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "crystal", None) is None or c[2] == getattr(args, "crystal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, crystal = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, crystal=crystal, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(CRYSTALS, params.crystal),
                 params.name, params.gender, params.caretaker, params.trait)
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


def valid_story_set() -> set[tuple]:
    return set(valid_combos())


def asp_valid_story_set() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    p = valid_story_set()
    a = asp_valid_story_set()
    if p == a:
        print(f"OK: ASP matches Python ({len(p)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(p - a))
    print(" only in asp:", sorted(a - p))
    return 1


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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for item in stories:
            print(item)
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
            header = f"### {p.name}: {p.activity} at {p.place} (crystal: {p.crystal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
