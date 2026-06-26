#!/usr/bin/env python3
"""
A standalone storyworld script for a small mystery about a nomadic team,
teamwork, misunderstanding, and a bad ending.

The premise:
- A traveling team moves from camp to camp with a shared toolkit.
- They are trying to solve a quiet mystery: where did the missing map go?
- A misunderstanding makes them suspect the wrong person.
- Their teamwork helps them search, but the ending is still bad because the
  map is found damaged too late.

This world is intentionally small and constraint-checked: it only generates
stories where the mystery has a real cause, the teamwork matters, and the final
state proves what changed.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    damaged: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    readable: object | None = None
    helper: object | None = None
    hero: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
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
class Place:
    id: str
    label: str
    moving: bool = False
    open_sky: bool = False
    hides: set[str] = field(default_factory=set)
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
class CrewRole:
    id: str
    label: str
    skill: str
    helps_with: set[str] = field(default_factory=set)
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
class MysteryThing:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    readable: bool = False
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "dunes": Place(id="dunes", label="the dune camp", moving=True, open_sky=True, hides={"crate", "satchel"}),
    "river": Place(id="river", label="the river camp", moving=True, open_sky=True, hides={"crate", "satchel", "cart"}),
    "trail": Place(id="trail", label="the trail camp", moving=True, open_sky=True, hides={"satchel"}),
    "market": Place(id="market", label="the roadside market camp", moving=True, open_sky=False, hides={"crate", "bag"}),
}

ROLES = {
    "tracker": CrewRole(id="tracker", label="tracker", skill="searching tracks", helps_with={"find", "follow"}),
    "mender": CrewRole(id="mender", label="mender", skill="repairing torn things", helps_with={"repair", "stitch"}),
    "caller": CrewRole(id="caller", label="caller", skill="asking careful questions", helps_with={"ask", "listen"}),
    "packer": CrewRole(id="packer", label="packer", skill="sorting packs", helps_with={"carry", "sort"}),
}

OBJECTS = {
    "map": MysteryThing(id="map", label="map", phrase="a folded map with red ink routes", region="crate", fragile=True, readable=True),
    "journal": MysteryThing(id="journal", label="journal", phrase="a travel journal with a blue clasp", region="satchel", fragile=False, readable=True),
    "signal_flag": MysteryThing(id="flag", label="signal flag", phrase="a striped signal flag", region="cart", fragile=False, readable=False),
}

NAMES = ["Mira", "Tavi", "Jori", "Nala", "Soren", "Pela", "Rin", "Aru"]
HELPER_NAMES = ["Kest", "Luma", "Bren", "Sila"]
TRAITS = ["careful", "restless", "brave", "quiet", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------
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


def _narrate_teamwork(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    world.say(
        f"{hero.id} and {helper.id} worked as a small nomadic team, "
        f"checking the camp's ropes, bags, and folded things together."
    )
    world.say(
        f"They thought the missing {obj.label} had to be nearby, because the camp had just moved and nothing stayed put for long."
    )


def _narrate_misunderstanding(world: World, hero: Entity, helper: Entity, obj: Entity, suspect: Entity) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    helper.memes["hurt"] = helper.memes.get("hurt", 0.0) + 1
    world.say(
        f"When {hero.id} found {suspect.id} near the crate, {hero.pronoun().capitalize()} thought {suspect.id} had taken the {obj.label}."
    )
    world.say(
        f"But {suspect.id} was only trying to keep the papers dry, and that made the mistake feel worse."
    )


def _search(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    helper.memes["focus"] = helper.memes.get("focus", 0.0) + 1
    world.say(
        f"The two of them searched the cart, the blanket roll, and every tied bundle they could reach."
    )
    if obj.hidden_in:
        world.say(
            f"At last they found the {obj.label} tucked inside the {obj.hidden_in}."
        )


def _bad_ending(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    obj.damaged = True
    world.facts["ending"] = "bad"
    world.say(
        f"By the time they opened it, the {obj.label} was bent and wet, and one corner had smeared so badly that the route was hard to read."
    )
    world.say(
        f"{hero.id} and {helper.id} stood in the quiet camp with the ruined {obj.label}, knowing the mystery was solved too late to save it."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type="person", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="person", label=params.helper))
    suspect = world.add(Entity(id="Sari", kind="character", type="person", label="Sari"))
    obj_cfg = _safe_lookup(OBJECTS, params.mystery)
    obj = world.add(
        Entity(
            id=obj_cfg.id,
            type="thing",
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            owner=hero.id,
            caretaker=helper.id,
            hidden_in="water bucket" if params.mystery == "map" else "packing cloth",
            readable=obj_cfg.readable,
        )
    )

    # Act 1: setup
    world.say(
        f"In a moving camp under a wide sky, {hero.id} was a {params.trait} nomadic {ROLES['tracker'].label}."
    )
    world.say(
        f"{helper.id} helped with the packs, and together they kept the little camp in order as they traveled."
    )
    world.say(
        f"That morning, the {obj.label} was missing, even though {hero.id} had seen it before the camp was tied up."
    )

    # Act 2: mystery and misunderstanding
    world.para()
    _narrate_teamwork(world, hero, helper, obj)
    _narrate_misunderstanding(world, hero, helper, obj, suspect)
    _search(world, hero, helper, obj)

    # Act 3: bad ending
    world.para()
    _bad_ending(world, hero, helper, obj)

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        obj=obj,
        place=place,
        params=params,
        teamwork=True,
        misunderstanding=True,
    )
    return world


# ---------------------------------------------------------------------------
# Question/answer generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short mystery story for a child about a nomadic team whose teamwork helps them search for a missing item, but the ending is sad.",
        f"Tell a simple story where {f['hero'].id} and {f['helper'].id} travel with a camp, make a misunderstanding, and find the {f['obj'].label} too late.",
        f"Write a child-friendly mystery that includes the word 'nomadic' and ends with a damaged {f['obj'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    suspect = _safe_fact(world, f, "suspect")
    obj = _safe_fact(world, f, "obj")
    place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Who was trying to solve the mystery of the missing {obj.label}?",
            answer=f"{hero.id} and {helper.id} were trying to solve it together as a small nomadic team at {place.label}.",
        ),
        QAItem(
            question=f"What misunderstanding made the search harder?",
            answer=f"{hero.id} thought {suspect.id} had taken the {obj.label}, but {suspect.id} was only trying to help keep things safe.",
        ),
        QAItem(
            question=f"What happened to the {obj.label} at the end?",
            answer=f"The {obj.label} was found, but it was bent and wet, so the ending was bad because the map could hardly be read.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does nomadic mean?",
            answer="Nomadic means moving from place to place instead of staying in one home all the time.",
        ),
        QAItem(
            question="Why do teams work together?",
            answer="Teams work together so different people can share jobs, solve problems, and finish hard tasks more safely.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they are wrong.",
        ),
        QAItem(
            question="What makes a mystery story feel like a mystery?",
            answer="A mystery story has a missing clue, careful searching, and a reveal that explains what happened.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
missing_object(O) :- object(O), hidden(O).
misunderstanding(H, S, O) :- hero(H), suspect(S), missing_object(O), blames(H, S, O).
teamwork(H, K) :- hero(H), helper(K), works_together(H, K).
bad_ending(O) :- missing_object(O), damaged(O), found_too_late(O).
story_ok(P, O) :- place(P), object(O), missing_object(O), teamwork(_, _), misunderstanding(_, _, O), bad_ending(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.moving:
            lines.append(asp.fact("moving", pid))
        for h in sorted(p.hides):
            lines.append(asp.fact("hides", pid, h))
    for rid, r in ROLES.items():
        lines.append(asp.fact("role", rid))
        for k in sorted(r.helps_with):
            lines.append(asp.fact("helps_with", rid, k))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("hidden", oid))
        lines.append(asp.fact("damaged", oid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("suspect", "suspect"))
    lines.append(asp.fact("works_together", "hero", "helper"))
    lines.append(asp.fact("blames", "hero", "suspect", "map"))
    lines.append(asp.fact("found_too_late", "map"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2.\n"))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = {(p, o) for p in PLACES for o in OBJECTS}
    py_set = {(p, o) for (p, o) in py_set if o == "map"}
    if asp_set == py_set:
        print("OK: ASP and Python parity check passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter selection and validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, mystery, "team") for place in PLACES for mystery in OBJECTS if mystery == "map"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a nomadic team.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=OBJECTS)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "mystery", None) and getattr(args, "mystery", None) != "map":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = "map"
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != hero])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if hero == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper, trait=trait)


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


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.damaged:
            bits.append("damaged=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="dunes", mystery="map", hero="Mira", helper="Kest", trait="careful"),
    StoryParams(place="river", mystery="map", hero="Tavi", helper="Luma", trait="sharp-eyed"),
    StoryParams(place="trail", mystery="map", hero="Jori", helper="Bren", trait="patient"),
    StoryParams(place="market", mystery="map", hero="Nala", helper="Sila", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        print(sorted(asp.atoms(model, "story_ok")))
        return

    rng_base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} at {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
