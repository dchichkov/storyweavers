#!/usr/bin/env python3
"""
Story world: a small slice-of-life tale about a child, a muddy day, and a math
problem that keeps getting interrupted.

Seed image:
- A child is trying to solve an integral worksheet at home.
- Outside, the yard is muddy.
- A small mishap makes the child worry about muck on paper and shoes.
- A parent helps with a funny, practical fix.
- The story stays close to ordinary life, with humor and inner monologue.
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

@dataclass(frozen=True)
class Place:
    key: str
    label: str
    indoor: bool
    affordances: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Activity:
    key: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass(frozen=True)
class ObjectThing:
    key: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Remedy:
    key: str
    label: str
    plan: str
    tail: str
    covers: set[str]
    guards: set[str]
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    shoes: object | None = None
    worksheet: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"muck": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "inner_monologue": 0.0}

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
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    zone: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.region]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


SETTINGS = {
    "kitchen": Place("kitchen", "the kitchen", True, {"homework", "tea"}),
    "porch": Place("porch", "the porch", False, {"muck", "broom"}),
    "yard": Place("yard", "the yard", False, {"muck", "boots"}),
    "table": Place("table", "the kitchen table", True, {"homework"}),
}

ACTIVITIES = {
    "walk": Activity(
        key="walk",
        verb="take a walk",
        gerund="walking",
        mess="muck",
        soil="mucky",
        zone={"feet"},
        keyword="muck",
        tags={"muck", "walk"},
    ),
    "puddle": Activity(
        key="puddle",
        verb="step in the puddle",
        gerund="stepping in puddles",
        mess="muck",
        soil="mucky",
        zone={"feet", "legs"},
        keyword="muck",
        tags={"muck", "puddle"},
    ),
}

OBJECTS = {
    "worksheet": ObjectThing(
        key="worksheet",
        label="math worksheet",
        phrase="an integral worksheet with neat blue lines",
        region="torso",
        tags={"integral"},
    ),
    "shoes": ObjectThing(
        key="shoes",
        label="shoes",
        phrase="clean sneakers",
        region="feet",
        plural=True,
        tags={"muck"},
    ),
}

REMEDIES = [
    Remedy(
        key="mat",
        label="an old newspaper mat",
        plan="spread an old newspaper mat by the door",
        tail="spread the newspaper mat and stepped on it before coming inside",
        covers={"feet"},
        guards={"muck"},
    ),
    Remedy(
        key="slippers",
        label="dry house slippers",
        plan="change into dry house slippers",
        tail="changed into dry house slippers and left the wet ones by the mat",
        covers={"feet"},
        guards={"muck"},
        plural=True,
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    seed: Optional[int] = None
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: integral, muck, and a funny fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "cheerful", "quiet", "silly", "thoughtful"])
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


def reasonableness_gate(place: Place, activity: Activity) -> bool:
    return activity.key in place.affordances or place.key in {"porch", "yard", "kitchen"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    if not reasonableness_gate(_safe_lookup(SETTINGS, place), _safe_lookup(ACTIVITIES, activity)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Toby", "Lena", "Owen", "Ruby", "Eli"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(["curious", "cheerful", "quiet", "silly", "thoughtful"])
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


ASP_RULES = r"""
place(kitchen;porch;yard;table).
activity(walk;puddle).

affords(kitchen,homework).
affords(porch,muck).
affords(yard,muck).
affords(table,homework).

splashes(walk,feet).
splashes(puddle,feet).
splashes(puddle,legs).

prize(worksheet).
prize(shoes).
worn_on(worksheet,torso).
worn_on(shoes,feet).

valid(P,A,O) :- affords(P,_), splashes(A,R), worn_on(O,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.key))
        if p.indoor:
            lines.append(asp.fact("indoor", p.key))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", p.key, a))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.key))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", a.key, r))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.key))
        lines.append(asp.fact("worn_on", o.key, o.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set()
    for pk, p in SETTINGS.items():
        for ak, a in ACTIVITIES.items():
            for ok, o in OBJECTS.items():
                if reasonableness_gate(p, a) and o.region in a.zone:
                    python_set.add((pk, ak, ok))
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def pick_remedy(activity: Activity, obj: ObjectThing) -> Optional[Remedy]:
    for r in REMEDIES:
        if activity.mess in r.guards and obj.region in r.covers:
            return r
    return None


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    world = World(place=place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    worksheet = world.add(Entity(
        id="worksheet", type="worksheet", label="worksheet",
        phrase=OBJECTS["worksheet"].phrase, owner=child.id, caretaker=parent.id,
        region="torso",
    ))
    shoes = world.add(Entity(
        id="shoes", type="shoes", label="shoes",
        phrase=OBJECTS["shoes"].phrase, owner=child.id, caretaker=parent.id,
        region="feet", plural=True,
    ))
    shoes.meters["muck"] = 0.0

    child.memes["inner_monologue"] += 1
    world.say(f"{child.id} sat at {place.label} with {worksheet.phrase}.")
    world.say(f"{child.id} was trying to finish an integral problem, and {child.pronoun('possessive')} mind kept whispering, \"Just one clean answer, please.\"")
    world.say(f"{child.id} liked how the page looked so neat that even the pencil seemed to sit up straighter.")

    world.para()
    world.say(f"Outside, the {world.place.key} looked like it had been sprinkled with muck by a very busy squirrel.")
    world.say(f"{child.id} wanted to {_safe_lookup(ACTIVITIES, params.activity).verb}, because the day felt too plain to stay still.")
    world.say(f"\"I can do homework after a tiny walk,\" {child.id} thought, which was the sort of sentence that sounded harmless right before trouble.")

    activity = _safe_lookup(ACTIVITIES, params.activity)
    child.meters["muck"] += 1
    child.memes["joy"] += 1
    world.zone = set(activity.zone)

    if any(item.region in world.zone and not world.covered(child, item.region) for item in [shoes, worksheet]):
        shoes.meters["muck"] += 1
        worksheet.meters["muck"] += 1
        parent.meters["work"] += 1
        child.memes["worry"] += 1
        world.say(f"{child.id} came back with {child.pronoun('possessive')} shoes speckled and {worksheet.label} looking less than proud.")
        world.say(f"\"Uh-oh,\" {child.id} thought. \"The page is supposed to be integral, not muddy.\"")
        world.say(f"{parent.id.capitalize()} noticed the mess and sighed in the gentle way that meant, yes, this would become a small cleaning story.")

    world.para()
    remedy = pick_remedy(activity, OBJECTS["shoes"])
    if remedy is None:
        pass
    world.add(Entity(id=remedy.key, type="thing", label=remedy.label, protective=True, covers=set(remedy.covers)))
    world.say(f"{parent.id.capitalize()} pointed at the door and suggested to {child.id} that they {remedy.plan}.")
    world.say(f"{child.id} blinked, then laughed because the plan sounded like a secret mission for very ordinary people.")
    world.say(f"\"So the shoes get a bath and I get to stay a person,\" {child.id} thought, feeling much better already.")
    world.say(f"They {remedy.tail}, and after that {child.id} wiped the desk, returned to the integral problem, and finished the last line without any new muck.")

    world.facts.update(
        child=child,
        parent=parent,
        worksheet=worksheet,
        shoes=shoes,
        activity=activity,
        remedy=remedy,
        params=params,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about a child named {f["child"].id} who is doing an integral worksheet and gets a little muck on {f["shoes"].label}.',
        f'Tell a gentle, humorous home story where {f["child"].id} wants to {f["activity"].verb} but still needs to finish an integral problem.',
        f'Write an everyday story with inner monologue, muck, and a parent who helps a child clean up and get back to homework.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    worksheet = _safe_fact(world, f, "worksheet")
    shoes = _safe_fact(world, f, "shoes")
    activity = _safe_fact(world, f, "activity")
    remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"What was {child.id} working on at the beginning of the story?",
            answer=f"{child.id} was sitting with {worksheet.phrase} and trying to finish an integral problem.",
        ),
        QAItem(
            question=f"Why did {child.id} worry after coming back inside?",
            answer=f"{child.id} worried because {child.pronoun('possessive')} shoes were speckled with muck, and the homework page no longer looked as neat.",
        ),
        QAItem(
            question=f"What funny idea did {parent.id} suggest to help?",
            answer=f"{parent.id} suggested that they {remedy.plan}, which gave {child.id} a simple way to deal with the muck before going back to homework.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} wiping the desk, returning to the integral problem, and finishing the last line after the cleanup.",
        ),
        QAItem(
            question=f"What did {child.id} want to do besides homework?",
            answer=f"{child.id} wanted to {activity.verb}, and that ordinary wish helped make the day a little messy and funny.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is muck?",
            answer="Muck is wet, messy dirt that can cling to shoes, floors, and clothes.",
        ),
        QAItem(
            question="What is an integral in math?",
            answer="An integral is a kind of math problem that often asks you to think about area or total amount.",
        ),
        QAItem(
            question="Why do people wipe muddy shoes before walking inside?",
            answer="People wipe muddy shoes before walking inside so they do not track muck onto the floor.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(place="kitchen", activity="walk", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="puddle", name="Toby", gender="boy", parent="father", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        atoms = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(atoms)} compatible combos")
        for atom in atoms:
            print(atom)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        n = getattr(args, "n", None)
        attempts = 0
        while len(samples) < n and attempts < n * 50:
            attempts += 1
            try:
                params = resolve_params(args, random.Random(rng.randrange(2**31)))
            except StoryError:
                continue
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
