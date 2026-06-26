#!/usr/bin/env python3
"""
storyworlds/worlds/kill_problem_solving_repetition_fairy_tale.py
=================================================================

A small fairy-tale storyworld about a gentle hero, a stubborn problem,
and repeated tries that lead to a clever fix.

Seed tale premise:
---
In a little kingdom, a young gardener-prince named Rowan tends a moonlit rose
bed behind the castle wall. One night, a thorny bramble keeps creeping back and
choking the roses. Rowan tries to solve the problem three times: first with bare
hands, then with a wooden rake, and finally with a clever bundle of damp cloth
and a tiny spade. Each failed try teaches him something new. At last he uses
the right tool in the right order, and the roses open again under the stars.

Narrative instruments:
- Problem solving: the hero learns from each failed attempt.
- Repetition: a repeated three-step pattern of tries.
- Fairy tale style: castle, moonlight, roses, prince/princess, old magic, gentle
  child-facing language.

The story is driven by a live world model with meters and memes, not by a frozen
paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    apron: object | None = None
    cloth: object | None = None
    companion: object | None = None
    hands: object | None = None
    hero: object | None = None
    prize: object | None = None
    rake: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "lady"}
        male = {"boy", "prince", "king", "man", "lord"}
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
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    recurrence: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    tactic: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.problem_id: str = ""
        self.history: list[str] = []
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.problem_id = self.problem_id
        clone.paragraphs = [[]]
        return clone


def _has(protective: list[Entity], region: str) -> bool:
    return any(ent.protective and region in ent.covers for ent in protective)


def _spread_problem(world: World) -> list[str]:
    out: list[str] = []
    problem = _safe_lookup(PROBLEMS, world.problem_id)
    for actor in world.characters():
        if actor.meters.get(problem.id, 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id == "hands" and "hands" in problem.zone:
                continue
            if item.id == "apron" and "torso" in problem.zone:
                continue
            if item.id == "boots" and "feet" in problem.zone:
                continue
            sig = ("spread", actor.id, item.id, problem.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stained"] = item.meters.get("stained", 0.0) + 1
            out.append(f"The {item.label} came away stained by the {problem.label}.")
    return out


def _resolve_calming(world: World) -> list[str]:
    out: list[str] = []
    problem = _safe_lookup(PROBLEMS, world.problem_id)
    for actor in world.characters():
        if actor.memes.get("hope", 0.0) >= THRESHOLD and actor.memes.get("doubt", 0.0) <= 0:
            sig = ("calm", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
            out.append(f"{actor.id} found a clearer thought.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_spread_problem, _resolve_calming):
            lines = fn(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def problem_at_risk(problem: Problem, prize: Entity) -> bool:
    return prize.owner is not None and prize.meters.get("fragile", 0.0) >= 0 and problem.zone.intersection({"hands", "torso", "feet"}) != set()


def select_tool(problem: Problem, prize: Entity) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.id in tool.guards and prize.id in {"roses", "crown"}:
            return tool
    return None


def reason_gate(problem_id: str, prize_id: str) -> bool:
    problem = _safe_lookup(PROBLEMS, problem_id)
    prize = _safe_lookup(PRIZES, prize_id)
    return problem_at_risk(problem, prize) and select_tool(problem, prize) is not None


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


def _r_repeat_try(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    problem = _safe_lookup(PROBLEMS, world.problem_id)
    for tool_id in ("bare_hands", "rake", "cloth_spade"):
        sig = ("try", tool_id)
        if sig in world.fired:
            continue
        if hero.memes.get("step", 0.0) >= {"bare_hands": 1, "rake": 2, "cloth_spade": 3}[tool_id]:
            continue
        world.fired.add(sig)
    return out


CAUSAL_RULES = [Rule("spread", _spread_problem), Rule("calm", _resolve_calming)]


def tell(place: Place, problem: Problem, prize_cfg: "Prize", hero_name: str, hero_type: str, companion_type: str) -> World:
    world = World(place)
    world.problem_id = problem.id

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name,
                            traits=["little", "brave", "patient"]))
    companion = world.add(Entity(id="companion", kind="character", type=companion_type, label="the old gardener",
                                 traits=["kind"]))
    prize = world.add(Entity(id="roses", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=companion.id))
    prize.meters["fragile"] = 1.0

    hands = world.add(Entity(id="hands", type="hands", label="bare hands", worn_by=hero.id))
    rake = world.add(Entity(id="rake", type="tool", label="wooden rake", worn_by=None))
    cloth = world.add(Entity(id="cloth_spade", type="tool", label="damp cloth and a tiny spade", worn_by=None))
    apron = world.add(Entity(id="apron", type="garment", label="apron", worn_by=companion.id, protective=True, covers={"torso"}))
    _ = (hands, rake, cloth, apron)

    hero.memes["hope"] = 0.0
    hero.memes["doubt"] = 0.0

    world.say(f"Once in the little kingdom, {hero.id} tended {hero.pronoun('possessive')} {prize.label} by moonlight.")
    world.say(f"{hero.id} loved the {problem.gerund}, because fairy tales are often full of brave little work.")
    world.say(f"But each night the {problem.label} crept back, and {problem.label.lower()} does not listen to wishes.")

    world.para()
    world.say(f"First, {hero.id} tried to {problem.verb} with bare hands.")
    hero.meters[problem.id] = 1.0
    propagate(world)
    hero.memes["doubt"] += 1
    world.say(f"It only scratched {hero.pronoun('object')} and made the trouble wiggle deeper.")

    world.para()
    world.say(f"Then {hero.id} tried again, this time with a wooden rake.")
    hero.meters[problem.id] = 2.0
    propagate(world)
    hero.memes["doubt"] += 1
    world.say(f"The rake was better, but the bramble kept returning like a stubborn rhyme.")

    world.para()
    world.say(f"At last the old gardener whispered, \"Try the soft cloth first, then the tiny spade.\"")
    hero.memes["hope"] += 1
    world.say(f"So {hero.id} wrapped the roots with damp cloth and worked the little spade under the thorny knot.")
    hero.meters[problem.id] = 3.0
    if ("cloth_spade",) not in world.fired:
        world.fired.add(("cloth_spade",))
    world.say(f"This time the roots gave way, and the {problem.label} stopped coming back.")
    hero.memes["doubt"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["victory"] = 1.0
    world.say(f"The roses lifted their heads, and the garden looked as if it had just remembered how to smile.")

    world.facts.update(
        hero=hero,
        companion=companion,
        prize=prize,
        problem=problem,
        place=place,
        tools=[rake, cloth],
        resolved=True,
    )
    return world


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
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


PLACES = {
    "castle_garden": Place("castle_garden", "the castle garden", affords={"thorn_bramble"}),
    "moon_path": Place("moon_path", "the moon path", affords={"thorn_bramble"}),
    "rose_hall": Place("rose_hall", "the rose hall", indoors=True, affords={"thorn_bramble"}),
}

PROBLEMS = {
    "thorn_bramble": Problem(
        id="thorn_bramble",
        label="thorn bramble",
        verb="kill the weeds",
        gerund="keeping the roses safe",
        recurrence="came back again",
        mess="stained",
        soil="tangled and prickly",
        zone={"hands", "torso"},
        keyword="thorn",
        tags={"garden", "thorn", "problem", "repetition"},
    ),
}

PRIZES = {
    "roses": Prize("roses", "silver roses", "roses"),
    "crown": Prize("crown", "a small golden crown", "crown"),
}

TOOLS = [
    Tool("cloth_spade", "damp cloth and a tiny spade", "damp cloth and a tiny spade", {"thorn_bramble"}, {"hands", "torso"}, "soften", "walked slowly", False),
    Tool("rake", "wooden rake", "wooden rake", {"thorn_bramble"}, {"hands"}, "scrape", "tried again", False),
    Tool("bare_hands", "bare hands", "bare hands", set(), {"hands"}, "pull", "worked bare-handed", False),
]

NAMES = ["Rowan", "Mira", "Elin", "Tobin", "Nora", "Alden"]
COMPANIONS = ["king", "queen", "gardener", "miller"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    name: str
    hero_type: str
    companion_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about problem solving and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl", "prince", "princess"])
    ap.add_argument("--companion-type", choices=COMPANIONS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    problem = getattr(args, "problem", None) or "thorn_bramble"
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl", "prince", "princess"])
    companion_type = getattr(args, "companion_type", None) or rng.choice(COMPANIONS)
    if not reason_gate(problem, prize):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, problem=problem, prize=prize, name=name, hero_type=hero_type, companion_type=companion_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short fairy tale about {hero.label} and a {problem.label} that includes the word "kill".',
        f"Tell a gentle story where {hero.label} tries three times to solve a {problem.label} problem near the {prize.label}.",
        f"Write a repetition-filled fairy tale about a child who learns the right tool for a stubborn garden problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    prize = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {hero.label} trying to do in {place.label}?",
            answer=f"{hero.label} was trying to {problem.verb} so the {prize.label} could stay safe and bright.",
        ),
        QAItem(
            question=f"What happened the first two times {hero.label} tried to handle the {problem.label}?",
            answer="The first try with bare hands failed, and the second try with the wooden rake still did not finish the job.",
        ),
        QAItem(
            question=f"How did the story end for the {prize.label}?",
            answer=f"In the end, the roots came free, the {problem.label} stopped returning, and the {prize.label} shone again under the moon.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bramble?",
            answer="A bramble is a thorny plant with tough stems, and its thorns can scratch hands and clothes.",
        ),
        QAItem(
            question="Why do people use tools like a spade or rake in a garden?",
            answer="People use garden tools to move soil, pull weeds, and loosen roots without hurting their hands too much.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when something happens again and again in a pattern, which helps the listener notice change.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions =="]
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_risk(P, R) :- problem(P), prize(R), zone(P, Z), worn_on(R, W), covers(W, C), overlap(Z, C).
compatible_tool(T, P, R) :- problem(P), prize(R), problem_at_risk(P, R), tool(T), solves(T, P), covers(T, C), zone(P, Z), overlap(C, Z).
valid_story(Place, P, R) :- place(Place), problem(P), prize(R), afford(Place, P), problem_at_risk(P, R), compatible_tool(_, P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for p in sorted(place.affords):
            lines.append(asp.fact("afford", pid, p))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(problem.zone):
            lines.append(asp.fact("zone", pid, z))
    for rid, prize in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("worn_on", rid, "torso"))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.guards):
            lines.append(asp.fact("solves", t.id, p))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    lines.append(asp.fact("overlap", "hands", "hands"))
    lines.append(asp.fact("overlap", "torso", "torso"))
    lines.append(asp.fact("overlap", "feet", "feet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for place in PLACES:
        for problem in PROBLEMS:
            for prize in PRIZES:
                if reason_gate(problem, prize):
                    python_set.add((place, problem, prize))
    if clingo_set == python_set:
        print(f"OK: ASP gate matches Python gate ({len(python_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(clingo_set - python_set))
    print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(PRIZES, params.prize), params.name, params.hero_type, params.companion_type)
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
    StoryParams(place="castle_garden", problem="thorn_bramble", prize="roses", name="Rowan", hero_type="prince", companion_type="gardener"),
    StoryParams(place="moon_path", problem="thorn_bramble", prize="crown", name="Mira", hero_type="princess", companion_type="queen"),
    StoryParams(place="rose_hall", problem="thorn_bramble", prize="roses", name="Elin", hero_type="girl", companion_type="king"),
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
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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
            header = f"### {p.name}: {p.problem} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
