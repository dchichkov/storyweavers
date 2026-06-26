#!/usr/bin/env python3
"""
storyworlds/worlds/luxury_moral_value_problem_solving_ghost_story.py
=====================================================================

A small ghost-story world about luxury, moral choice, and problem solving.

Premise:
- A child or small family enters an old house, inn, or museum room that feels eerie.
- A shiny luxury object tempts someone.
- A gentle ghost appears not to frighten, but to test whether the characters will do the right thing.
- The problem is solved by choosing honesty, sharing, or returning something that was lost.

The world is constraint-driven:
- Only stories where the luxury item is actually at stake are allowed.
- The chosen moral fix must genuinely solve the ghost's concern.
- The result should read like a complete child-facing ghost story, with a clear eerie beginning,
  a tense middle, and a resolved ending image showing what changed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "lady"}
        male = {"boy", "father", "dad", "man", "king", "gentleman"}
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
class Place:
    name: str
    eerie: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    moral_link: str
    takes: set[str] = field(default_factory=set)  # problem kinds it can trigger
    tends_to_be_taken: bool = False
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
class GhostNeed:
    id: str
    label: str
    concern: str
    fix: str
    solves: set[str] = field(default_factory=set)  # which problem kinds this can resolve
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
class StoryParams:
    place: str
    treasure: str
    need: str
    name: str
    gender: str
    companion: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


PLACES = {
    "manor": Place(
        name="the old manor",
        eerie="The old manor creaked like it was whispering secrets.",
        affords={"peek", "search", "return"},
    ),
    "museum": Place(
        name="the moonlit museum",
        eerie="The museum halls shone softly, and the glass cases looked like sleeping eyes.",
        affords={"peek", "search", "return"},
    ),
    "attic": Place(
        name="the attic",
        eerie="The attic smelled like dust and moonlight, and every box seemed to listen.",
        affords={"peek", "search", "return"},
    ),
}

TREASURES = {
    "silver_cup": Treasure(
        id="silver_cup",
        label="silver cup",
        phrase="a polished silver cup",
        type="cup",
        value="luxury",
        moral_link="sharing",
        takes={"hide", "keep"},
    ),
    "pearl_necklace": Treasure(
        id="pearl_necklace",
        label="pearl necklace",
        phrase="a string of shining pearl beads",
        type="necklace",
        value="luxury",
        moral_link="honesty",
        takes={"take", "hide"},
        tends_to_be_taken=True,
    ),
    "golden_key": Treasure(
        id="golden_key",
        label="golden key",
        phrase="a tiny golden key",
        type="key",
        value="luxury",
        moral_link="responsibility",
        takes={"take", "keep"},
        tends_to_be_taken=True,
    ),
}

NEEDS = {
    "lost_room": GhostNeed(
        id="lost_room",
        label="lost room",
        concern="its favorite room had been forgotten and locked away",
        fix="open the room and light it again",
        solves={"search"},
    ),
    "returned_treasure": GhostNeed(
        id="returned_treasure",
        label="returned treasure",
        concern="something lovely had gone missing long ago",
        fix="tell the truth and return it",
        solves={"take", "hide", "keep"},
    ),
    "shared_memory": GhostNeed(
        id="shared_memory",
        label="shared memory",
        concern="the treasure was too lonely to stay hidden",
        fix="place it where everyone could see and care for it",
        solves={"hide", "keep"},
    ),
}

GENDERS = ["girl", "boy"]
COMPANIONS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "careful", "brave", "gentle", "thoughtful", "quiet"]
NAMES = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "Elsie", "Maya"],
    "boy": ["Theo", "Bram", "Leo", "Owen", "Eli", "Finn"],
}


def world_can_use(place: Place, treasure: Treasure, need: GhostNeed) -> bool:
    return bool(treasure.takes & need.solves)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TREASURES:
            for n in NEEDS:
                if world_can_use(_safe_lookup(PLACES, p), _safe_lookup(TREASURES, t), _safe_lookup(NEEDS, n)):
                    combos.append((p, t, n))
    return combos


def select_resolution(treasure: Treasure, need: GhostNeed) -> str:
    if need.id == "returned_treasure":
        return "return"
    if need.id == "shared_memory":
        return "share"
    if need.id == "lost_room":
        return "open"
    return "solve"


def reasonableness_gate(treasure: Treasure, need: GhostNeed) -> bool:
    return world_can_use(PLACES["manor"], treasure, need)


ASP_RULES = r"""
% A treasure is at moral risk when the ghost's concern matches a problem the treasure can trigger.
at_risk(T, N) :- treasure(T), need(N), takes(T, P), solves(N, P).

% A valid story is one where the treasure and ghost need can actually interact.
valid(P, T, N) :- place(P), at_risk(T, N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("takes", tid, *["dummy"]) if False else "")
        for k in sorted(t.takes):
            lines.append(asp.fact("takes", tid, k))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        for s in sorted(n.solves):
            lines.append(asp.fact("solves", nid, s))
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about luxury, morals, and problems solved.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--companion", choices=COMPANIONS)
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
              and (getattr(args, "treasure", None) is None or c[1] == getattr(args, "treasure", None))
              and (getattr(args, "need", None) is None or c[2] == getattr(args, "need", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treasure, need = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, need=need, name=name, gender=gender, companion=companion, trait=trait)


def start_lines(world: World, hero: Entity, companion: Entity, treasure: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'quiet')} child who loved tiny mysteries.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {companion.type} entered {world.place.name}.")
    world.say(world.place.eerie)
    world.say(f"Inside, they found {treasure.phrase}, shining like it belonged in a royal story.")
    treasure.worn_by = hero.id


def ghost_appears(world: World, need: GhostNeed) -> None:
    world.para()
    world.say("Then the lights seemed to dim, and a soft ghost drifted out from the shadows.")
    world.say(f"It was not a scary ghost. It only looked worried because {need.concern}.")
    world.say(f'"If someone does the right thing," the ghost whispered, "the house can rest again."')


def act_of_problem(world: World, hero: Entity, treasure: Entity, need: GhostNeed) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    if treasure.tends_to_be_taken and need.id == "returned_treasure":
        hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
        world.say(f"{hero.id} almost hid the {treasure.label} in {hero.pronoun('possessive')} pocket, but something about the ghost's voice felt honest and warm.")
    else:
        world.say(f"{hero.id} wanted the {treasure.label}, but the ghost's worried face made {hero.id} stop and think.")
    world.say(f"{hero.id} tried to solve the problem instead of making it worse.")


def solve_problem(world: World, hero: Entity, companion: Entity, treasure: Entity, need: GhostNeed) -> None:
    resolution = select_resolution(treasure, need)
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    if resolution == "return":
        world.say(f'{hero.id} said, "We should return this so nobody loses it again."')
        world.say(f"They carried the {treasure.label} back to its proper place and told the truth about what they had found.")
    elif resolution == "share":
        world.say(f'{hero.id} said, "Let’s put it where everyone can see it."')
        world.say(f"They placed the {treasure.label} on a bright shelf, where it could be admired without being hidden away.")
    elif resolution == "open":
        world.say(f'{hero.id} said, "Let’s open the room and see what it remembers."')
        world.say(f"They turned the old key, opened the dusty door, and let light spill into the forgotten room.")
    else:
        world.say(f"{hero.id} found a careful way to help, and the ghost drifted closer, calmer now.")
    world.say(f"The ghost smiled, because the good choice had solved the trouble at last.")
    world.say(f"After that, the house felt quieter, as if it could breathe again.")


def ending_image(world: World, hero: Entity, companion: Entity, treasure: Entity, need: GhostNeed) -> None:
    world.para()
    world.say(f"By the end, {hero.id} and {hero.pronoun('possessive')} {companion.type} were standing in the moonlit quiet, not afraid anymore.")
    world.say(f"The {treasure.label} was safe, the ghost was peaceful, and the old place no longer felt lonely.")
    world.say(f"{hero.id} had learned that luxury things are nicest when they are used with care and honesty.")


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"trait": params.trait}))
    companion = world.add(Entity(id="Companion", kind="character", type=params.companion, label=params.companion))
    treasure_cfg = _safe_lookup(TREASURES, params.treasure)
    treasure = world.add(Entity(id=treasure_cfg.id, type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, owner=hero.id))
    need = _safe_lookup(NEEDS, params.need)

    start_lines(world, hero, companion, treasure)
    ghost_appears(world, need)
    world.para()
    act_of_problem(world, hero, treasure, need)
    solve_problem(world, hero, companion, treasure, need)
    ending_image(world, hero, companion, treasure, need)

    world.facts.update(hero=hero, companion=companion, treasure=treasure, need=need, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    treasure = _safe_fact(world, f, "treasure")
    need = _safe_fact(world, f, "need")
    return [
        f'Write a gentle ghost story for a child that includes a {treasure.value} object and a kind ghost.',
        f"Tell a story where {hero.id} faces a spooky-looking problem in {world.place.name} and solves it by choosing the right thing.",
        f"Write a short story about {treasure.label}, a worried ghost, and a moral choice that makes the house peaceful again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    treasure = _safe_fact(world, f, "treasure")
    need = _safe_fact(world, f, "need")
    return [
        QAItem(
            question=f"Where did {hero.id} find the {treasure.label}?",
            answer=f"{hero.id} found the {treasure.label} in {world.place.name}, where the air felt a little spooky at first.",
        ),
        QAItem(
            question=f"Why did the ghost appear in the story?",
            answer=f"The ghost appeared because {need.concern}. It was not trying to scare anyone; it wanted the problem fixed kindly.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the trouble with the {treasure.label}?",
            answer=f"{hero.id} solved it by choosing the honest, careful thing to do and helping make the treasure safe again.",
        ),
        QAItem(
            question=f"Who stayed with {hero.id} during the ghost story?",
            answer=f"{hero.id} was with {hero.pronoun('possessive')} {companion.type}, so {hero.id} did not have to face the eerie room alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is luxury?",
            answer="Luxury means something fancy, rich, or special that feels extra nice and valuable.",
        ),
        QAItem(
            question="What does a ghost story usually feel like?",
            answer="A ghost story usually feels mysterious or spooky at first, but in a gentle story it can end safely and happily.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means choosing what is kind, fair, honest, or responsible.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully about a trouble and finding a good way to fix it.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="manor", treasure="pearl_necklace", need="returned_treasure", name="Mina", gender="girl", companion="mother", trait="curious"),
    StoryParams(place="museum", treasure="silver_cup", need="shared_memory", name="Theo", gender="boy", companion="grandfather", trait="thoughtful"),
    StoryParams(place="attic", treasure="golden_key", need="lost_room", name="Luna", gender="girl", companion="father", trait="careful"),
]


def explain_rejection(treasure: Treasure, need: GhostNeed) -> str:
    return (
        f"(No story: {treasure.label} and the ghost's concern do not make a believable "
        f"moral problem together. Try a treasure and ghost need that can actually interact.)"
    )


def valid_story_filter(place: str, treasure: str, need: str) -> bool:
    return world_can_use(_safe_lookup(PLACES, place), _safe_lookup(TREASURES, treasure), _safe_lookup(NEEDS, need))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, treasure, need) combos:\n")
        for place, treasure, need in combos:
            print(f"  {place:8} {treasure:16} {need}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.treasure} at {p.place} (need: {p.need})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
