#!/usr/bin/env python3
"""
amber_matzo_craft_workshop_repetition_misunderstanding_slice.py
================================================================

A small slice-of-life storyworld set in a craft workshop.

Premise:
- A child works in a craft workshop.
- They are excited about making something with amber-colored pieces and matzo-inspired paper shapes.
- Repetition helps the craft, but a misunderstanding briefly causes trouble.
- A gentle explanation and a patient fix bring the workshop back to calm.

The world models:
- physical meters: neatness, glue, dryness, stiffness, sparkle
- emotional memes: excitement, patience, misunderstanding, pride, worry

The story is generated from world state rather than a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    material: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def setm(self, key: str, val: float) -> None:
        self.meters[key] = val

    def sete(self, key: str, val: float) -> None:
        self.memes[key] = val

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def who(self) -> str:
        return self.label or self.type
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
    workspace: bool = True
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
class Material:
    id: str
    label: str
    phrase: str
    kind: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
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
    material: str
    pattern: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
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


THRESHOLD = 1.0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "workshop": Place(
        id="workshop",
        label="the craft workshop",
        workspace=True,
        affords={"stringing", "stacking", "folding"},
    )
}

MATERIALS = {
    "amber": Material(
        id="amber",
        label="amber beads",
        phrase="bright amber beads in a small bowl",
        kind="beads",
        plural=True,
        tags={"amber", "glossy"},
    ),
    "matzo": Material(
        id="matzo",
        label="matzo squares",
        phrase="plain matzo squares for stamping and collage",
        kind="squares",
        plural=True,
        tags={"matzo", "brittle"},
    ),
}

PATTERNS = {
    "repeat": "a repeating border of dots and lines",
    "braid": "a braid pattern with three looping strips",
    "rows": "tidy rows that match from one side to the other",
}

TOOLS = {
    "string": Tool(
        id="string",
        label="string",
        phrase="a spool of string",
        supports={"stringing"},
        helps={"repeat"},
    ),
    "tray": Tool(
        id="tray",
        label="tray",
        phrase="a shallow tray",
        supports={"stacking"},
        helps={"rows"},
    ),
    "folder": Tool(
        id="folder",
        label="paper folder",
        phrase="a paper folder",
        supports={"folding"},
        helps={"braid"},
    ),
}

GREETINGS = [
    "The workshop smelled like paper, glue, and warm tea.",
    "Light came through the high windows and shone on the craft table.",
    "Little scraps of thread and paper waited in neat piles.",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A craft is reasonable if the place supports the activity,
% the chosen material needs the matching activity, and a tool helps the pattern.
material_ok(M, A) :- material(M), needs_activity(M, A).
pattern_ok(P, T) :- pattern(P), tool(T), helps(T, P).

valid(Place, Material, Pattern) :-
    place(Place), affords(Place, Act),
    material_ok(Material, Act),
    pattern_ok(Pattern, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, mat in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("needs_activity", mid, "stringing" if mid == "amber" else "folding"))
        for t in sorted(mat.tags):
            lines.append(asp.fact("tag", mid, t))
    for pid in PATTERNS:
        lines.append(asp.fact("pattern", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mat_id, mat in MATERIALS.items():
            act = "stringing" if mat_id == "amber" else "folding"
            if act not in place.affords:
                continue
            for pat_id in PATTERNS:
                if pat_id == "repeat" and mat_id == "amber":
                    out.append((place_id, mat_id, pat_id))
                if pat_id == "braid" and mat_id == "matzo":
                    out.append((place_id, mat_id, pat_id))
                if pat_id == "rows":
                    out.append((place_id, mat_id, pat_id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(place: Place, material: Material, pattern: str) -> bool:
    if material.id == "amber" and pattern != "repeat":
        return False
    if material.id == "matzo" and pattern not in {"braid", "rows"}:
        return False
    if material.id not in MATERIALS:
        return False
    return "stringing" in place.affords or "folding" in place.affords


def explain_rejection(place: Place, material: Material, pattern: str) -> str:
    return (
        f"(No story: {material.label} and the {pattern} pattern do not make a "
        f"reasonable workshop scene here.)"
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    mat = _safe_lookup(MATERIALS, params.material)
    world = World(place)

    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, label=params.child))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=params.helper))
    material = world.add(Entity(id=mat.id, type=mat.kind, label=mat.label, phrase=mat.phrase, plural=mat.plural))

    world.facts.update(child=child, helper=helper, material=material, pattern=params.pattern, place=place)

    child.sete("excitement", 1.0)
    helper.sete("patience", 1.0)
    material.setm("sparkle", 1.0 if mat.id == "amber" else 0.0)
    material.setm("crumbles", 1.0 if mat.id == "matzo" else 0.0)

    return world


def initial_lines(world: World) -> None:
    child = next(e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    helper = next(e for e in world.entities.values() if e.kind == "character" and e is not child)
    material: Entity = _safe_fact(world, world.facts, "material")
    pattern = _safe_fact(world, world.facts, "pattern")

    world.say(random.choice(GREETINGS))
    world.say(
        f"{child.who} was at {world.place.label} with {helper.who}, eager to make something careful and pretty."
    )
    world.say(
        f"On the table sat {material.phrase}, and {child.who} kept glancing at them because the color looked like little pieces of sunlight."
    )
    world.para()
    world.say(
        f"{child.who} wanted to make {pattern} over and over again, because repeating the same shape felt calm and steady."
    )
    if material.id == "matzo":
        world.say(
            f"The matzo squares were dry and crisp, so they needed gentle hands and a soft touch."
        )
    else:
        world.say(
            f"The amber beads were smooth and warm-looking, and they rolled in a tiny shiny line when the table tilted."
        )


def misunderstand(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    material: Entity = _safe_fact(world, world.facts, "material")
    pattern = _safe_fact(world, world.facts, "pattern")

    child.sete("misunderstanding", 1.0)
    helper.sete("worry", 1.0)
    world.para()
    world.say(
        f"{child.who} heard {helper.who} say, \"Try it again,\" and thought that meant the first try was wrong."
    )
    world.say(
        f"So {child.who} pressed harder and repeated the same motion too fast, hoping the {material.label} would look perfect on the next try."
    )
    if material.id == "matzo":
        material.setm("crumbles", material.m("crumbles") + 1.0)
        material.setm("dust", 1.0)
    else:
        material.setm("scatter", 1.0)
    child.sete("worry", 1.0)
    world.say(
        f"That made the pieces shift, and for a moment the neat {pattern} did not line up the way {child.pronoun('possessive')} hands expected."
    )


def repair(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    material: Entity = _safe_fact(world, world.facts, "material")
    pattern = _safe_fact(world, world.facts, "pattern")

    world.para()
    helper.sete("patience", helper.e("patience") + 1.0)
    world.say(
        f"{helper.who} smiled and said, \"I meant try the same shape again, not squeeze harder.\""
    )
    world.say(
        f"Then {helper.who} showed {child.pronoun('object')} a slower way: one piece at a time, then a pause, then the next piece."
    )
    if material.id == "amber":
        material.setm("sparkle", material.m("sparkle") + 1.0)
        material.setm("scatter", 0.0)
    else:
        material.setm("crumbles", max(0.0, material.m("crumbles") - 1.0))
    child.sete("misunderstanding", 0.0)
    child.sete("pride", 1.0)
    child.sete("joy", 1.0)
    world.say(
        f"With the slower rhythm, the {pattern} came together, and the repeated line looked tidy instead of rushed."
    )
    world.say(
        f"In the end, {child.who} held up the finished craft and grinned while {helper.who} set the glue aside."
    )


def tell_story(world: World) -> None:
    initial_lines(world)
    misunderstand(world)
    repair(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child: Entity = _safe_fact(world, world.facts, "child")
    material: Entity = _safe_fact(world, world.facts, "material")
    pattern = _safe_fact(world, world.facts, "pattern")
    return [
        f"Write a slice-of-life story set in a craft workshop about {child.who} making a {pattern} with {material.label}.",
        f"Tell a gentle story where repetition helps a child at a craft table, but a misunderstanding briefly causes trouble.",
        f"Write a short workshop story that uses the words amber and matzo and ends with a calmer, better craft.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    material: Entity = _safe_fact(world, world.facts, "material")
    pattern: str = _safe_fact(world, world.facts, "pattern")
    return [
        QAItem(
            question=f"What was {child.who} making in the craft workshop?",
            answer=f"{child.who} was making a {pattern} craft with {material.label}.",
        ),
        QAItem(
            question=f"Why did the first try at the craft go wrong?",
            answer=(
                f"It went wrong because {child.who} misunderstood {helper.who} and pressed too hard instead of repeating the motion slowly."
            ),
        ),
        QAItem(
            question=f"How did {helper.who} fix the problem?",
            answer=(
                f"{helper.who} explained the instruction again and showed a slower, repeated way to place each piece."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the craft looked neat and {child.who} felt proud instead of worried."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    material: Entity = _safe_fact(world, world.facts, "material")
    out = [
        QAItem(
            question="What is a craft workshop?",
            answer="A craft workshop is a place where people make things with their hands, like paper art, beads, glue, and string.",
        ),
        QAItem(
            question="What does repetition mean in craft?",
            answer="Repetition means doing the same step again and again, which can help make a pattern neat and steady.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks something the wrong way, even if nobody meant to confuse them.",
        ),
    ]
    if material.id == "amber":
        out.append(
            QAItem(
                question="What are amber beads like?",
                answer="Amber beads are smooth and golden, so they can look warm and bright on a craft table.",
            )
        )
    else:
        out.append(
            QAItem(
                question="What is matzo?",
                answer="Matzo is a dry, crisp flat bread that can break easily, so it needs gentle handling.",
            )
        )
    return out


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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Noah", "Levi", "Ari", "Lia", "Tess", "Eli", "Ruth"]
HELPERS = {
    "mother": ("mother", "mother"),
    "father": ("father", "father"),
    "teacher": ("teacher", "teacher"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--material", choices=MATERIALS.keys())
    ap.add_argument("--pattern", choices=PATTERNS.keys())
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS.keys()))
    ap.add_argument("--helper-type", choices=["mother", "father", "teacher"])
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
    place = getattr(args, "place", None) or "workshop"
    material = getattr(args, "material", None) or rng.choice(list(MATERIALS.keys()))
    pattern = getattr(args, "pattern", None) or rng.choice(list(PATTERNS.keys()))
    if not reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(MATERIALS, material), pattern):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child = getattr(args, "child", None) or rng.choice(NAMES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father", "teacher"])
    helper = getattr(args, "helper", None) or helper_type
    return StoryParams(
        place=place,
        material=material,
        pattern=pattern,
        child=child,
        child_type=child_type,
        helper=helper,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for material in MATERIALS:
            if material == "amber":
                pattern = "repeat"
            else:
                pattern = "braid"
            params = StoryParams(
                place="workshop",
                material=material,
                pattern=pattern,
                child="Mina" if material == "amber" else "Noah",
                child_type="girl" if material == "amber" else "boy",
                helper="mother" if material == "amber" else "teacher",
                helper_type="mother" if material == "amber" else "teacher",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
