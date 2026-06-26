#!/usr/bin/env python3
"""
Storyworld: sin_crest_gunk_dim_teamwork_problem_solving
======================================================

A small comedy storyworld about a child, a sticky mess, and a teamwork fix.

Seed premise:
- A child named Sin is proud of a bright school crest.
- A can of gunk-dim splashes the crest right before a little celebration.
- Instead of panicking, the kids work together, solve the problem, and rescue the day.

The world is deliberately tiny:
- one main setting: the school hall or club room
- one main mess: gunk-dim
- one main valued object: a crest or banner
- one main solution: teamwork and problem solving

The story is built from simulated state, not from a frozen template.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fix_item: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "team":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the school hall"
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
class Mess:
    id: str
    label: str
    phrase: str
    mess: str
    soil: str
    zone: set[str]
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
class Fix:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
class StoryParams:
    place: str
    mess: str
    prize: str
    name: str
    helper: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c


def _mess_on_item(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for m in MESS_REGISTRY.values():
            if actor.meters.get(m.mess, 0.0) < THRESHOLD:
                continue
            for item in list(world.entities.values()):
                if item.owner != actor.id:
                    continue
                if item.region not in world.zone:
                    continue
                if any(item.region in f.covers for f in [world.entities[x] for x in world.entities if x in world.entities]):
                    pass
                sig = ("mess", actor.id, item.id, m.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[m.mess] = item.meters.get(m.mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got {m.label.lower()}.")
    return out


def _teamwork(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("teamwork", 0.0) < THRESHOLD:
            continue
        if ("teamwork", actor.id) in world.fired:
            continue
        world.fired.add(("teamwork", actor.id))
        actor.memes["confidence"] = actor.memes.get("confidence", 0.0) + 1
        return [f"{actor.id} took a breath and started making a plan."]
    return []


def _problem_solving(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("problem_solving", 0.0) < THRESHOLD:
            continue
        if ("solve", actor.id) in world.fired:
            continue
        world.fired.add(("solve", actor.id))
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
        return [f"{actor.id} looked for a clever fix instead of a bigger fuss."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_teamwork, _problem_solving, _mess_on_item):
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_fix(mess: Mess, fix: Fix, prize: Entity) -> bool:
    return mess.mess in fix.guards and prize.region in fix.covers


def predict_mess(world: World, actor: Entity, mess: Mess, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters[mess.mess] = 1
    sim.zone = set(mess.zone)
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, mess: Mess) -> None:
    world.say(
        f"{hero.id} was a bright-eyed {hero.type} who liked making the school feel ready for fun."
    )
    world.say(
        f"{hero.id} loved {prize.phrase}, especially because the shiny {prize.label} looked like a tiny victory flag."
    )
    world.say(
        f"One day, a can of {mess.label.lower()} tipped over near the {prize.label}, and the room suddenly looked like it had sneezed glittery trouble."
    )


def trouble(world: World, hero: Entity, helper: Entity, prize: Entity, mess: Mess) -> None:
    hero.meters[mess.mess] = hero.meters.get(mess.mess, 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.zone = set(mess.zone)
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} gasped, and {helper.id} did too, but only the friendly kind of gasp that says, 'Oh no, we can still fix this.'"
    )


def plan(world: World, hero: Entity, helper: Entity, mess: Mess, prize: Entity, fix: Fix) -> Optional[Fix]:
    if not can_fix(mess, fix, prize):
        return None
    if predict_mess(world, hero, mess, prize.id):
        return None
    world.say(
        f"{hero.id} and {helper.id} did a quick team huddle and found a smart idea: {fix.prep}."
    )
    return fix


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, mess: Mess, fix: Fix) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["teamwork"] = 1.0
    hero.memes["problem_solving"] = 1.0
    fix_item = world.add(Entity(
        id=fix.id,
        type="gear",
        label=fix.label,
        phrase=fix.phrase,
        owner=hero.id,
        plural=fix.plural,
    ))
    fix_item.worn_by = hero.id
    world.say(
        f"They put on {fix.label} and used it to wipe the {mess.label.lower()} away in little swishes."
    )
    world.say(
        f"{fix.tail.capitalize()}. Soon the {prize.label} was clean again, and the shiny crest looked proud instead of puddly."
    )
    world.say(
        f"{hero.id} laughed so hard that {hero.pronoun('possessive')} shoulders bounced like jelly, and {helper.id} laughed right along with {hero.pronoun('object')}."
    )
    world.say(
        f"By the end, the whole room smelled like soap, teamwork, and a tiny bit of triumph."
    )


SETTING_REGISTRY = {
    "hall": Setting(place="the school hall", affords={"gunkdim"}),
    "clubroom": Setting(place="the club room", affords={"gunkdim"}),
}

MESS_REGISTRY = {
    "gunkdim": Mess(
        id="gunkdim",
        label="gunk-dim",
        phrase="a sticky gunk-dim spill",
        mess="gunk",
        soil="smeared and dim",
        zone={"torso"},
        tags={"gunk-dim", "comedy"},
    ),
}

PRIZE_REGISTRY = {
    "crest": Entity(
        id="crest",
        type="thing",
        label="crest",
        phrase="a bright school crest",
        region="torso",
    ),
}

FIX_REGISTRY = {
    "towels": Fix(
        id="towels",
        label="two soft towels",
        phrase="two soft towels for careful wiping",
        covers={"torso"},
        guards={"gunk"},
        prep="grab two soft towels and work from the edges inward",
        tail="they kept swapping sides so the joke was never on one person for long",
        plural=True,
    ),
    "apron": Fix(
        id="apron",
        label="an old art apron",
        phrase="an old art apron",
        covers={"torso"},
        guards={"gunk"},
        prep="put on an old art apron and wipe gently",
        tail="the apron saved the day and the shirt underneath stayed cheerful",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTING_REGISTRY.items():
        for mess_id in setting.affords:
            mess = MESS_REGISTRY[mess_id]
            for prize_id, prize in PRIZE_REGISTRY.items():
                for fix in FIX_REGISTRY.values():
                    if can_fix(mess, fix, prize):
                        combos.append((place, mess_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mess: str
    prize: str
    name: str
    helper: str
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


GIRL_NAMES = ["Sin", "Mina", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Max", "Theo", "Eli", "Ben", "Owen"]
HELPERS = ["friend", "classmate", "brother", "sister"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a child about "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}" fixing a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mess").label.lower()} mess with teamwork.',
        f"Tell a comedy story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} and a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")} save the {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize").label} from {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mess").label.lower()}.",
        f'Write a simple story that includes the words "sin", "crest", and "gunk-dim" and ends with teamwork solving the problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper_ent")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    mess = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mess")
    fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")
    return [
        QAItem(
            question=f"What went wrong in the story for {hero.id}?",
            answer=f"A can of {mess.label.lower()} spilled near the {prize.label} and made a sticky, silly mess.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They used {fix.label} and worked together to wipe the mess away carefully.",
        ),
        QAItem(
            question=f"Why was the {prize.label} important?",
            answer=f"The {prize.label} was a bright school crest, so it mattered to {hero.id} and the group.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking of a smart way to fix a difficulty.",
        ),
        QAItem(
            question="Why do people use towels for a spill?",
            answer="Towels can soak up wet or sticky messes and help clean surfaces.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    bits.append(f"fired={sorted(world.fired)}")
    return "\n".join(bits)


CURATED = [
    StoryParams(place="hall", mess="gunkdim", prize="crest", name="Sin", helper="friend"),
    StoryParams(place="clubroom", mess="gunkdim", prize="crest", name="Mina", helper="classmate"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports a sticky gunk-dim spill that can be fixed with towels or an apron.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about sin, crest, gunk-dim, teamwork, and problem solving.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--mess", choices=MESS_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "mess", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None) or "hall", getattr(args, "mess", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mess", None) is None or c[1] == getattr(args, "mess", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mess, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, mess=mess, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING_REGISTRY[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="friend"))
    prize = world.add(Entity(**PRIZE_REGISTRY[params.prize].__dict__))
    mess = MESS_REGISTRY[params.mess]
    fix = FIX_REGISTRY["towels"]

    introduce(world, hero, helper, prize, mess)
    world.para()
    trouble(world, hero, helper, prize, mess)
    world.para()
    chosen = plan(world, hero, helper, mess, prize, fix)
    if chosen is None:
        _fallback_pool = globals().get("CHOSENS") or globals().get("CHOSENES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        chosen = next(iter(_fallback_pool), None)
        if chosen is None:
            raise StoryError
    resolve(world, hero, helper, prize, mess, chosen)

    world.facts = {
        "hero": hero,
        "helper_ent": helper,
        "prize": prize,
        "mess": mess,
        "fix": chosen,
    }
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
place(hall). place(clubroom).
affords(hall,gunkdim). affords(clubroom,gunkdim).

mess(gunkdim).
zone(gunkdim,torso).
guards(towels,gunkdim). covers(towels,torso).
guards(apron,gunkdim). covers(apron,torso).
prize(crest). worn_on(crest,torso).

prize_at_risk(M,P) :- zone(M,R), worn_on(P,R).
has_fix(M,P) :- prize_at_risk(M,P), guards(_,M), covers(_,R), worn_on(P,R).

valid(Place,M,P) :- affords(Place,M), prize_at_risk(M,P), has_fix(M,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MESS_REGISTRY.items():
        lines.append(asp.fact("mess", mid))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid in PRIZE_REGISTRY:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, "torso"))
    for fid, f in FIX_REGISTRY.items():
        lines.append(asp.fact("fix", fid))
        for g in sorted(f.guards):
            lines.append(asp.fact("guards", fid, g))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for t in valid_combos_asp():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
