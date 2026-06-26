#!/usr/bin/env python3
"""
storyworlds/worlds/tummy_proof_elapse_problem_solving_cautionary_pirate.py
==========================================================================

A small pirate-tale storyworld about a cautious crew, a tricky tummy, and the
proof they gather before time elapses and the problem becomes worse.

Seed tale:
---
A young pirate named Finn loved sweet plums from the dock market. One windy
afternoon, Finn ate too many before the ship sailed. Soon his tummy felt wrong.
The captain warned that the sea could make it worse, so the crew looked for proof
about what Finn had eaten and how long it had been. They checked the fruit crate,
counted the minutes, and remembered the baker's warning. When the proof was
clear, the crew gave Finn water, rested him below deck, and waited for the
ache to pass. Finn learned to listen next time, and the ship kept sailing.

World model idea:
---
- A pirate crew has one small trip, one suspicious snack, one upset tummy, and
  one careful fix.
- Physical meters track tummy pain, time passing, and how much proof has been
  gathered.
- Memes track worry, caution, and relief.
- The story turns when the crew uses proof to decide on a careful response
  before elapse makes the situation worse.

This script follows the storyworld contract:
- standalone stdlib script
- uses storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    clue: object | None = None
    fix: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "mate", "deckhand"}
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
    sea: bool = False
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
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    issue: str
    worsen_with_elapse: bool
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
class Proof:
    id: str
    label: str
    phrase: str
    method: str
    reveals: str
    resolves: str
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


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.problem_id: str = ""
        self.proof_id: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.problem_id = self.problem_id
        clone.proof_id = self.proof_id
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    proof: str
    remedy: str
    hero_name: str
    hero_type: str
    captain_name: str
    seed: Optional[int] = None
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
    "dock": Setting(place="the dock", affords={"plums", "fish"}, sea=True),
    "deck": Setting(place="the ship deck", affords={"plums", "fish"}, sea=True),
    "hold": Setting(place="the cargo hold", affords={"plums"}, sea=False),
    "market": Setting(place="the dock market", affords={"plums"}, sea=False),
}

PROBLEMS = {
    "tummy": Problem(
        id="tummy",
        verb="eat too many sweet plums",
        gerund="eating too many sweet plums",
        rush="grab another plum and keep eating",
        issue="a sore tummy",
        worsen_with_elapse=True,
        keyword="tummy",
        tags={"tummy", "plum", "food"},
    ),
    "fishbone": Problem(
        id="fishbone",
        verb="swallow a fishbone by mistake",
        gerund="swallowing a fishbone by mistake",
        rush="try to chew the fish faster",
        issue="a scratchy throat",
        worsen_with_elapse=True,
        keyword="proof",
        tags={"fish", "careful"},
    ),
}

PROOFS = {
    "receipt": Proof(
        id="receipt",
        label="a dock receipt",
        phrase="the plum receipt from the market stall",
        method="check the market paper",
        reveals="the fruit came from the old green crate",
        resolves="the plums were safe, but too many had been eaten",
        tags={"proof", "paper", "market"},
    ),
    "crate": Proof(
        id="crate",
        label="the fruit crate",
        phrase="the stamped crate of plums",
        method="inspect the crate mark",
        reveals="the baker's stamp was still on the lid",
        resolves="the crew could trust the fruit, but still needed to rest",
        tags={"proof", "crate", "plum"},
    ),
    "clock": Proof(
        id="clock",
        label="the ship's clock",
        phrase="the brass clock on the wall",
        method="count the minutes since snack time",
        reveals="too much time had passed for another snack",
        resolves="the crew should wait and drink water instead",
        tags={"proof", "time", "elapse"},
    ),
}

REMEDIES = {
    "water": Remedy(
        id="water",
        label="water",
        phrase="cool water in a tin cup",
        method="sip water slowly",
        effect="helped the tummy settle",
        tags={"water", "tummy"},
    ),
    "rest": Remedy(
        id="rest",
        label="rest",
        phrase="a blanket below deck",
        method="lie down below deck",
        effect="gave the stomach time to calm",
        tags={"rest", "elapse"},
    ),
}

HERO_NAMES = ["Finn", "Nora", "Mira", "Jory", "Lena", "Tess"]
CAPTAIN_NAMES = ["Captain Bram", "Captain Wren", "Captain Mace", "Captain Sila"]
HERO_TYPES = ["pirate", "mate"]
TRAITS = ["brave", "curious", "stubborn", "cheerful", "bold", "small"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            for proof_id in PROOFS:
                for remedy_id in REMEDIES:
                    if prob_id == "tummy" and proof_id in {"receipt", "crate", "clock"} and remedy_id in {"water", "rest"}:
                        combos.append((place, prob_id, proof_id))
                    if prob_id == "fishbone" and proof_id == "clock" and remedy_id == "water":
                        combos.append((place, prob_id, proof_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate cautionary storyworld about tummy trouble, proof, and elapse.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--proof", choices=PROOFS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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


def explain_rejection(problem: Problem, proof: Proof) -> str:
    return f"(No story: {problem.gerund} does not pair reasonably with {proof.label} for a clear pirate problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "proof", None):
        if (getattr(args, "problem", None), getattr(args, "proof", None)) not in {(p, pr) for _, p, pr in valid_combos()}:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "proof", None) is None or c[2] == getattr(args, "proof", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, proof = rng.choice(list(combos))
    remedy = getattr(args, "remedy", None) or rng.choice(sorted(REMEDIES))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = "pirate"
    captain = getattr(args, "parent", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(place=place, problem=problem, proof=proof, remedy=remedy, hero_name=name, hero_type=hero_type, captain_name=captain)


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _evolve(world: World, narrate: bool = True) -> list[str]:
    out = []
    hero = world.get("hero")
    prob = _safe_lookup(PROBLEMS, world.problem_id)
    if hero.meters.get("elapsed", 0.0) >= 1.0 and prob.worsen_with_elapse and hero.meters.get("tummy", 0.0) >= 1.0:
        sig = ("worsen", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meme(hero, "worry", 1)
            out.append("Time passed, and the tummy felt even grumpier.")
    if hero.meters.get("proof", 0.0) >= 1.0 and hero.memes.get("caution", 0.0) >= 1.0:
        sig = ("resolve", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meme(hero, "relief", 1)
            hero.memes["trouble"] = 0.0
            out.append("The proof helped the crew choose the safe way.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _advance_time(world: World, turns: int = 1) -> None:
    hero = world.get("hero")
    for _ in range(turns):
        _add_meter(hero, "elapsed", 1)
    _evolve(world)


def tell(setting: Setting, problem: Problem, proof: Proof, remedy: Remedy, hero_name: str, captain_name: str) -> World:
    world = World(setting)
    world.problem_id = problem.id
    world.proof_id = proof.id

    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=hero_name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=captain_name))
    snack = world.add(Entity(id="snack", type="thing", label="plums", phrase="sweet dock plums", caretaker="captain"))
    clue = world.add(Entity(id="clue", type="thing", label=proof.label, phrase=proof.phrase))
    fix = world.add(Entity(id="fix", type="thing", label=remedy.label, phrase=remedy.phrase))

    _add_meme(hero, "joy", 1)
    world.say(f"{hero_name} was a small pirate who loved the busy smell of the docks.")
    world.say(f"{hero_name} kept a careful eye on every snack, because a pirate never wanted trouble later.")
    world.say(f"At {setting.place}, the crew found {snack.phrase}, and {hero_name} ate too many.")

    world.para()
    _add_meter(hero, "tummy", 1)
    _add_meme(hero, "trouble", 1)
    world.say(f"Before long, {hero_name}'s {problem.keyword} felt wrong.")
    world.say(f"{hero_name} wanted to keep going, but {captain_name} raised a hand and warned that the sea could make it worse.")
    world.say(f"The crew needed proof before they chose a cure.")

    world.para()
    world.say(f"They decided to {proof.method}.")
    _add_meter(hero, "proof", 1)
    _add_meme(hero, "caution", 1)
    world.say(f"The proof showed that {proof.reveals}.")
    _advance_time(world, 1)
    world.say(f"That meant {proof.resolves}.")

    world.para()
    world.say(f"So the crew chose to {remedy.method}.")
    _add_meter(hero, "rest", 1)
    _add_meme(hero, "relief", 1)
    hero.meters["tummy"] = max(0.0, hero.meters.get("tummy", 0.0) - 1)
    world.say(f"{hero_name} held the cup, breathed slowly, and rested below deck.")
    world.say(f"After a little while, the ache eased, and the ship went on with a wiser pirate aboard.")

    world.facts.update(
        hero=hero,
        captain=captain,
        snack=snack,
        clue=clue,
        fix=fix,
        problem=problem,
        proof=proof,
        remedy=remedy,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prob = _safe_fact(world, f, "problem")
    proof = _safe_fact(world, f, "proof")
    return [
        f'Write a pirate tale for a little child that uses the words "{prob.keyword}", "proof", and "elapse".',
        f"Tell a cautionary story where {hero.label} gets {prob.issue} and the crew checks {proof.label} before time passes too far.",
        f"Write a short story about a pirate crew solving a problem by gathering proof and waiting for elapse to show what is true.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    captain = _safe_fact(world, f, "captain")
    problem = _safe_fact(world, f, "problem")
    proof = _safe_fact(world, f, "proof")
    remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"What problem did {hero.label} have after the plums?",
            answer=f"{hero.label} had a sore tummy after eating too many sweet plums at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {captain.label} want proof before choosing a fix?",
            answer=f"{captain.label} wanted proof so the crew could tell what was wrong and not make the tummy trouble worse.",
        ),
        QAItem(
            question=f"What proof did the crew check?",
            answer=f"They checked {proof.label}, and it showed that the plums were safe, but {hero.label} had eaten too many.",
        ),
        QAItem(
            question=f"What did the crew do to help {hero.label}?",
            answer=f"They gave {hero.label} water and let {hero.label} rest below deck until the tummy felt better.",
        ),
        QAItem(
            question=f"What happened after some time elapse?",
            answer=f"After some time passed, the ache eased, and the crew knew the careful choice had been right.",
        ),
        QAItem(
            question=f"What did {hero.label} learn?",
            answer=f"{hero.label} learned to listen to the captain, gather proof, and choose the safe way before a small problem grew bigger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is proof?",
            answer="Proof is information that helps show what is true.",
        ),
        QAItem(
            question="What does elapse mean?",
            answer="Elapse means to pass by, usually talking about time.",
        ),
        QAItem(
            question="What is a tummy?",
            answer="A tummy is the belly area of the body.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", problem="tummy", proof="crate", remedy="water", hero_name="Finn", hero_type="pirate", captain_name="Captain Wren"),
    StoryParams(place="market", problem="tummy", proof="receipt", remedy="rest", hero_name="Nora", hero_type="pirate", captain_name="Captain Bram"),
    StoryParams(place="deck", problem="tummy", proof="clock", remedy="water", hero_name="Mira", hero_type="pirate", captain_name="Captain Sila"),
]


ASP_RULES = r"""
% A pirate problem is at risk when time elapses and the tummy trouble can grow.
at_risk(P) :- problem(P), can_worsen(P).

% Proof is reasonable when it reveals what is true about the problem.
good_proof(PR, P) :- proof(PR), problem(P), reveals(PR, P).

% A remedy is a valid fix when the proof supports caution and the remedy helps.
valid_fix(R, P) :- remedy(R), problem(P), good_proof(_, P), helps(R, P).

valid_story(Place, P, PR) :- setting(Place), affords(Place, P), good_proof(PR, P), valid_fix(_, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.worsen_with_elapse:
            lines.append(asp.fact("can_worsen", pid))
    for prid, pr in PROOFS.items():
        lines.append(asp.fact("proof", prid))
        for t in sorted(pr.tags):
            lines.append(asp.fact("reveals", prid, "tummy" if "plum" in t or "time" in t else "tummy"))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("helps", rid, "tummy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((place, prob, pr) for place, prob, pr in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(PROOFS, params.proof), _safe_lookup(REMEDIES, params.remedy), params.hero_name, params.captain_name)
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
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
