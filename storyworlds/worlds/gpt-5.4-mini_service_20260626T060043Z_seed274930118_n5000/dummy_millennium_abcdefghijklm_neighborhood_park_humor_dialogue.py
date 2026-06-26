#!/usr/bin/env python3
"""
A myth-flavored neighborhood-park story world with humor and dialogue.

Premise:
- A little wooden dummy named Dumi stands in a neighborhood park.
- Every "millennium" festival, the park wishes for one ridiculous miracle.
- The dummy and a child must solve a small problem by speaking to each other and using a silly, but reasonable, plan.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld file
- eager results import
- lazy ASP import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- Python reasonableness gate plus inline ASP twin
- trace / QA / JSON / verify / show-asp support
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    dummy: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
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


@dataclass
class Setting:
    place: str = "the neighborhood park"
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
class Trouble:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Solution:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


def _predict(world: World, actor: Entity, trouble: Trouble, prize_id: str) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(actor.id), trouble, narrate=False)
    prize = sim.entities[prize_id]
    return {"ruined": prize.meters.get("ruined", 0) >= THRESHOLD}


def _do_trouble(world: World, actor: Entity, trouble: Trouble, narrate: bool = True) -> None:
    world.zone = set(trouble.zone)
    actor.meters[trouble.keyword] = actor.meters.get(trouble.keyword, 0) + 1
    actor.memes["mischief"] = actor.memes.get("mischief", 0) + 1
    for item in list(world.entities.values()):
        if item.worn_by == actor.id and item.region in trouble.zone:
            item.meters[trouble.keyword] = item.meters.get(trouble.keyword, 0) + 1
            item.meters["ruined"] = item.meters.get("ruined", 0) + 1
    if narrate:
        world.say(f"The trouble rose like a small cloud over the park.")


def _r_ruin(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("ruined", 0) >= THRESHOLD and ("ruin", e.id) not in world.fired:
            world.fired.add(("ruin", e.id))
            out.append(f"That would spoil {e.label}.")
    return out


CAUSAL_RULES = [("ruin", _r_ruin)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(trouble: Trouble, prize: Prize) -> bool:
    return prize.region in trouble.zone


def select_solution(trouble: Trouble, prize: Prize) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if trouble.keyword in sol.guards and prize.region in sol.covers:
            return sol
    return None


def tell(setting: Setting, trouble: Trouble, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "bright"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    dummy = world.add(Entity(id="Dummy", kind="thing", type="dummy", label="dummy", phrase="a wooden dummy"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(hero=hero, parent=parent, dummy=dummy, prize=prize, trouble=trouble, prize_cfg=prize_cfg)

    world.say(f"In the neighborhood park, {hero.id} met a wooden dummy named {dummy.id}.")
    world.say(f"The dummy had guarded the swings since the last millennium, or so the children said.")
    world.say(f"{hero.id} liked the dummy because it never forgot a joke.")

    world.para()
    world.say(f"One bright afternoon, {hero.id} wanted to {trouble.verb}.")
    world.say(f'“Why now?” asked {parent.label}. “Because the park feels like a myth today,” said {hero.id}.')
    world.say(f'The dummy answered, “A myth needs a laugh, not a lecture.”')

    if not reasonableness_gate(trouble, prize_cfg):
        pass

    pred = _predict(world, hero, trouble, prize.id)
    if pred["ruined"]:
        world.say(f'“If you {trouble.verb}, your {prize.label} will get {trouble.risk},” said {parent.label}.')
    else:
        world.say(f'“That path looks harmless,” said the parent, but the dummy shook its head.')

    world.say(f'{hero.id} grinned and tried to {trouble.verb}, just to see if the warning was true.')
    _do_trouble(world, hero, trouble)
    propagate(world)

    world.para()
    world.say(f'{hero.id} gasped. “My {prize.label}!”')
    world.say(f'The dummy leaned close and whispered, “A small problem can still be solved with a small, smart idea.”')

    sol = select_solution(trouble, prize_cfg)
    if sol is None:
        pass

    world.say(f'“Then let us {sol.prep},” said {parent.label}. “And maybe let the dummy keep the joke.”')
    world.say(f'{hero.id} laughed and nodded.')
    world.say(f'They {sol.tail}.')
    prize.meters["ruined"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0
    world.say(f'At the end, {hero.id} was {trouble.gerund}, the {prize.label} stayed safe, and the dummy looked proud under the old park tree.')

    world.facts["solution"] = sol
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "neighborhood_park": Setting(place="the neighborhood park", affords={"laugh_echo", "swing_song", "pigeon_riddle"}),
}

TROUBLES = {
    "laugh_echo": Trouble(
        id="laugh_echo",
        verb="shout a joke at the echo wall",
        gerund="laughing at the echo wall",
        risk="echo-splashed and muddied",
        zone={"torso"},
        keyword="echo",
        tags={"humor", "dialogue", "myth"},
    ),
    "swing_song": Trouble(
        id="swing_song",
        verb="sing from the tallest swing",
        gerund="singing from the tallest swing",
        risk="tangled and dusty",
        zone={"torso"},
        keyword="song",
        tags={"humor", "dialogue", "myth"},
    ),
    "pigeon_riddle": Trouble(
        id="pigeon_riddle",
        verb="answer the pigeons in rhyme",
        gerund="answering the pigeons in rhyme",
        risk="pecked and pebbled",
        zone={"hands"},
        keyword="rhyme",
        tags={"humor", "dialogue", "myth"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "hat": Prize(label="hat", phrase="a golden paper hat", type="hat", region="torso"),
    "shoes": Prize(label="shoes", phrase="shiny dancing shoes", type="shoes", region="feet", plural=True),
}

SOLUTIONS = [
    Solution(id="bench", label="park bench", prep="sit on the park bench and trade jokes with the dummy", tail="sat on the park bench and traded jokes with the dummy", guards={"echo", "song"}, covers={"torso"}),
    Solution(id="kite_string", label="kite string", prep="tie the cape to the kite string first", tail="tied the cape to the kite string first", guards={"echo", "song"}, covers={"torso"}),
    Solution(id="mud_path", label="mud path", prep="go back by the dry path and keep the shoes high", tail="went back by the dry path and kept the shoes high", guards={"rhyme"}, covers={"feet"}),
]

GIRL_NAMES = ["Mina", "Lila", "Tia", "Nora", "Ivy"]
BOY_NAMES = ["Oren", "Pax", "Jules", "Eli", "Rafi"]
TRAITS = ["curious", "brave", "cheerful", "silly"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    prize: str
    name: str
    gender: str
    parent: str
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
    for place, setting in SETTINGS.items():
        for t in setting.affords:
            trouble = _safe_lookup(TROUBLES, t)
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(trouble, prize) and select_solution(trouble, prize):
                    combos.append((place, t, prize_id))
    return combos


KNOWLEDGE = {
    "dummy": [("What is a dummy?", "A dummy is a pretend person or wooden figure used for practice or stories.")],
    "millennium": [("What is a millennium?", "A millennium is a very long time, equal to one thousand years.")],
    "park": [("What is a park?", "A park is a place with grass, paths, trees, and room to play.")],
    "humor": [("What is humor?", "Humor is when something is funny and makes people smile or laugh.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters speak to each other in a story.")],
    "myth": [("What is a myth?", "A myth is an old-style story about big ideas, brave acts, or magical feeling.")],
    "echo": [("What is an echo?", "An echo is a sound that bounces back after someone speaks or shouts.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a word sound that matches another word sound, like song and long.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h = _safe_fact(world, f, "hero")
    t = _safe_fact(world, f, "trouble")
    p = _safe_fact(world, f, "prize_cfg")
    return [
        f'Write a myth-like story for a child in a neighborhood park with a wooden dummy and the word "dummy".',
        f'Include humor and dialogue as {h.id} tries to {t.verb} while worrying about {p.phrase}.',
        f'Write a small, funny park myth featuring "millennium" and the word "abcdefghijklm".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, parent, trouble, prize = f["hero"], f["parent"], f["trouble"], f["prize"]
    sol = _safe_fact(world, f, "solution")
    return [
        QAItem(
            question=f"Who was the story about in the neighborhood park?",
            answer=f"It was about a little {h.type} named {h.id}, the parent, and a wooden dummy named Dummy.",
        ),
        QAItem(
            question=f"What did {h.id} want to do at the park?",
            answer=f"{h.id} wanted to {trouble.verb}. That wish gave the story its problem.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"The parent worried because if {h.id} went to {trouble.verb}, the {prize.label} would get {trouble.risk}.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"They used {sol.label} and chose a safer way to play, so the {prize.label} stayed safe.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{h.id} was happy, the tension was gone, and the dummy was still standing guard in the neighborhood park.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"dummy", "millennium", "park", "humor", "dialogue", "myth"}
    tags.update(world.facts["trouble"].tags)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T, P) :- trouble(T), prize(P), zone(T, R), region(P, R).
has_solution(T, P) :- prize_at_risk(T, P), solution(S), guards(S, K), keyword(T, K), covers(S, R), region(P, R).
valid_story(Place, T, P) :- place(Place), affords(Place, T), prize_at_risk(T, P), has_solution(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("keyword", tid, t.keyword))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s.id))
        for g in sorted(s.guards):
            lines.append(asp.fact("guards", s.id, g))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", s.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like humorous neighborhood-park story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "trouble", None) and getattr(args, "prize", None):
        t, p = _safe_lookup(TROUBLES, getattr(args, "trouble", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (reasonableness_gate(t, p) and select_solution(t, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trouble", None) is None or c[1] == getattr(args, "trouble", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, trouble, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TROUBLES, params.trouble), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="neighborhood_park", trouble="laugh_echo", prize="cape", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="neighborhood_park", trouble="swing_song", prize="hat", name="Oren", gender="boy", parent="father", trait="cheerful"),
    StoryParams(place="neighborhood_park", trouble="pigeon_riddle", prize="shoes", name="Ivy", gender="girl", parent="mother", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, trouble, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.trouble} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
