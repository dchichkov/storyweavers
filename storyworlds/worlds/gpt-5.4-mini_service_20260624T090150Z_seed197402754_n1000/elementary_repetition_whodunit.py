#!/usr/bin/env python3
"""
A small elementary whodunit world built around repetition of clues.

Premise:
- A school object goes missing.
- A child notices a repeated pattern of clues.
- A helper follows the repeated pattern and solves the case.

This script keeps the simulation concrete: clues are physical items in meters
and suspicion/morale are emotional memes. The story prose is driven by the
state of the investigation, not a frozen paragraph.
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
# Data model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    adult: object | None = None
    child: object | None = None
    missing: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher", "principal", "librarian"}
        male = {"boy", "man", "teacher", "principal", "librarian"}
        if self.type in female and self.type not in {"teacher", "principal", "librarian"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type not in {"teacher", "principal", "librarian"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.label or self.id
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
    detail: str
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


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    place: str
    kind: str
    repeats: int = 2
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
class Case:
    missing: str
    culprit: str
    motive: str
    clue_path: list[str]
    reveal_place: str
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


class World:
    def __init__(self, setting: Place) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "classroom": Place("classroom", "the classroom", "The desks were neat, and the chalkboard looked freshly wiped.", {"search", "hide"}),
    "hallway": Place("hallway", "the hallway", "The hallway was long and echoey, with bright drawings on the walls.", {"search", "hide"}),
    "library": Place("library", "the library", "The library smelled like paper and glue, and the shelves stood in quiet rows.", {"search", "hide"}),
    "playground": Place("playground", "the playground", "The playground had a slide, a bench, and a patch of soft sand near the fence.", {"search", "hide"}),
}

MISSING_OBJECTS = {
    "globe": ("globe", "the class globe", "A round blue globe sat on a shelf for lessons about maps.", "classroom"),
    "red_crayon": ("crayon", "the red crayon box", "A bright red crayon box had a lid that clicked shut.", "classroom"),
    "library_stamp": ("stamp", "the library stamp", "A little ink stamp lived in a drawer beside the book cart.", "library"),
    "spelling_card": ("card", "the spelling-card pouch", "A pouch of spelling cards helped children practice their words.", "classroom"),
}

CHARACTERS = [
    ("child", "boy", "boy", ["curious", "careful"]),
    ("child", "girl", "girl", ["curious", "careful"]),
]

ADULTS = [
    ("teacher", "teacher", "Ms. Pine"),
    ("librarian", "librarian", "Mr. Reed"),
    ("principal", "principal", "Mrs. Vale"),
]

CARRYABLE_SPOTS = ["desk", "shelf", "cart", "bench", "locker"]

CLUE_LIBRARY = {
    "smudge": ("smudge", "a small blue smudge", "blue"),
    "crumb": ("crumb", "a trail of cracker crumbs", "crumbs"),
    "tape": ("tape", "a strip of yellow tape", "tape"),
    "shoeprint": ("shoeprint", "two little shoe prints", "prints"),
    "note": ("note", "a folded note that said 'check the reading corner'", "note"),
}

REPETITION_PATTERNS = [
    ["smudge", "smudge", "note"],
    ["crumb", "crumb", "shoeprint"],
    ["tape", "tape", "note"],
    ["shoeprint", "shoeprint", "smudge"],
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    missing: str
    child_gender: str
    child_name: str
    adult_role: str
    adult_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
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


def choose(seq, rng: random.Random):
    return seq[rng.randrange(len(seq))]


def article(noun: str) -> str:
    return "an" if noun[0].lower() in "aeiou" else "a"


def pronoun_name(entity: Entity) -> str:
    return entity.id


def case_story_name(entity: Entity) -> str:
    return entity.ref()


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if "search" not in place.affordances:
            continue
        for miss_id, (_, _, _, where) in MISSING_OBJECTS.items():
            if where == place_id:
                combos.append((place_id, miss_id))
    return combos


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_case(rng: random.Random, place_id: str, missing_id: str) -> Case:
    pattern = choose(REPETITION_PATTERNS, rng)
    clue_names = pattern[:]  # repeated clues, key to the whodunit style
    culprit = "teacher"
    motive = "tidying the room quickly before the next lesson"
    reveal_place = "desk drawer" if place_id == "classroom" else "supply shelf"
    return Case(
        missing=missing_id,
        culprit=culprit,
        motive=motive,
        clue_path=clue_names,
        reveal_place=reveal_place,
    )


def simulate(params: StoryParams) -> World:
    setting = _safe_lookup(PLACES, params.place)
    world = World(setting)

    child_type = "girl" if params.child_gender == "girl" else "boy"
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=child_type,
        label=params.child_name,
        traits=[] if False else [],
    ))
    adult = world.add(Entity(
        id=params.adult_name,
        kind="character",
        type=params.adult_role,
        label=params.adult_name,
    ))
    missing_type, missing_label, missing_phrase, home_place = _safe_lookup(MISSING_OBJECTS, params.missing)
    missing = world.add(Entity(
        id=params.missing,
        kind="thing",
        type=missing_type,
        label=missing_label,
        phrase=missing_phrase,
        owner=child.id,
        hidden_in=params.place,
        meters={"missing": 1.0},
        memes={"important": 1.0},
    ))

    case = build_case(random.Random(params.seed or 0), params.place, params.missing)
    world.facts.update(case=case, child=child, adult=adult, missing=missing, setting=setting)

    clue_objs = []
    for i, clue_key in enumerate(case.clue_path):
        cid, label, detail = CLUE_LIBRARY[clue_key]
        clue_id = f"{clue_key}_{i}"
        clue_place = [params.place, "shelf", "drawer", "reading corner", "cart"][i % 5]
        obj = world.add(Entity(
            id=clue_id,
            kind="thing",
            type=cid,
            label=label,
            phrase=detail,
            hidden_in=clue_place,
            meters={"clue": 1.0},
        ))
        clue_objs.append(obj)

    world.facts["clues"] = clue_objs

    # Act 1: set up mystery.
    world.say(f"In {setting.label}, {child.id} noticed that {missing.phrase} was gone.")
    world.say(f"{setting.detail} The room felt strange because something important had vanished.")
    world.para()

    # Act 2: repeated clues.
    world.say(f"{child.id} looked under a desk, then at a shelf, then near a cart.")
    world.say(f"Each place held the same kind of clue again and again.")
    world.say(f"{' '.join(['Again,'] * 1)} the clues repeated: {case.clue_path[0]}, {case.clue_path[1]}, and {case.clue_path[2]}.")
    world.para()

    # Investigation and deduction.
    world.say(f"{adult.id} knelt beside {child.id} and listened carefully.")
    world.say(f'"If the clue repeats, it is probably trying to point somewhere," {adult.id} said.')
    world.say(f"{child.id} followed the repeated signs and searched the {case.reveal_place}.")
    missing.hidden_in = case.reveal_place
    missing.carried_by = adult.id
    missing.meters["missing"] = 0.0
    world.para()

    world.say(f"Inside the {case.reveal_place}, they found {missing.phrase}.")
    world.say(f"It had been tucked away by {adult.id}, who had been tidying in a hurry so the room would look ready.")
    world.say(f"{child.id} smiled, because the mystery now made sense: the clues had repeated, and the repeated clues had told the truth.")
    child.memes["relief"] = 1.0
    adult.memes["regret"] = 1.0
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = _safe_fact(world, f, "case")
    child: Entity = _safe_fact(world, f, "child")
    missing: Entity = _safe_fact(world, f, "missing")
    return [
        f"Write a short elementary whodunit where {child.id} notices repeated clues and solves the mystery of the missing {missing.label}.",
        f"Tell a child-friendly mystery story in which clues repeat and point to the place where {missing.phrase} was hidden.",
        f"Write a simple detective story for kids that uses repetition to reveal who moved the {missing.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = _safe_fact(world, f, "case")
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    missing: Entity = _safe_fact(world, f, "missing")
    return [
        QAItem(
            question=f"What went missing in the story?",
            answer=f"The missing thing was {missing.phrase}.",
        ),
        QAItem(
            question=f"Who noticed the mystery first?",
            answer=f"{child.id} noticed that something was wrong and started following the clues.",
        ),
        QAItem(
            question=f"What clue pattern helped solve the case?",
            answer=f"The clues repeated again and again, which helped point to the place where the missing item had been hidden.",
        ),
        QAItem(
            question=f"Who had moved the missing item?",
            answer=f"{adult.id} had moved it while tidying the room in a hurry.",
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found in the {case.reveal_place}.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a clue?",
        answer="A clue is a small piece of information that can help solve a mystery.",
    ),
    QAItem(
        question="Why can repetition help in a whodunit?",
        answer="Repetition can make a pattern easier to notice, and a pattern can point to the answer.",
    ),
    QAItem(
        question="What does a detective do?",
        answer="A detective looks carefully at clues, asks questions, and tries to figure out what happened.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is valid when a missing object belongs in the chosen setting.
valid_place(P, M) :- place(P), missing(M), home_of(M, P).

% Repetition is the heart of this world: a clue is repeated when the same clue
% kind appears more than once in the pattern.
repeated(K) :- clue_kind(K), 2 { clue_pattern(K, I) : clue_index(I) }.

% A case is solvable if a repeated clue exists and the reveal place is searched.
solvable(P, M) :- valid_place(P, M), repeated(_), reveal_place(P, R), searched(R).

#show valid_place/2.
#show repeated/1.
#show solvable/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, (_, _, _, home) in MISSING_OBJECTS.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("home_of", mid, home))
    for idx, pat in enumerate(REPETITION_PATTERNS):
        for clue in pat:
            lines.append(asp.fact("clue_kind", clue))
            lines.append(asp.fact("clue_pattern", clue, idx))
            lines.append(asp.fact("clue_index", idx))
    for pid in PLACES:
        lines.append(asp.fact("searched", "desk_drawer" if pid == "classroom" else "supply_shelf"))
        lines.append(asp.fact("reveal_place", pid, "desk_drawer" if pid == "classroom" else "supply_shelf"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/2."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = {(p, m) for (p, m) in asp_valid_combos()}
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Elementary whodunit story world with repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING_OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-role", choices=["teacher", "librarian", "principal"])
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "missing", None):
        if (getattr(args, "place", None), getattr(args, "missing", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        (p, m) for (p, m) in combos
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "missing", None) is None or m == getattr(args, "missing", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, missing = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or (rng.choice(["Mia", "Nora", "Ella", "Ava"]) if gender == "girl" else rng.choice(["Leo", "Finn", "Max", "Theo"]))
    adult_role = getattr(args, "adult_role", None) or rng.choice(["teacher", "librarian", "principal"])
    adult_name = getattr(args, "adult_name", None) or {"teacher": "Ms. Pine", "librarian": "Mr. Reed", "principal": "Mrs. Vale"}[adult_role]
    return StoryParams(place=place, missing=missing, child_gender=gender, child_name=name, adult_role=adult_role, adult_name=adult_name)


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:16} ({e.kind:9}) {' '.join(bits)}")
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
    StoryParams(place="classroom", missing="globe", child_gender="girl", child_name="Mia", adult_role="teacher", adult_name="Ms. Pine"),
    StoryParams(place="library", missing="library_stamp", child_gender="boy", child_name="Leo", adult_role="librarian", adult_name="Mr. Reed"),
    StoryParams(place="classroom", missing="spelling_card", child_gender="girl", child_name="Nora", adult_role="principal", adult_name="Mrs. Vale"),
]

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solvable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solvable/2."))
        sols = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(sols)} solvable cases:")
        for p, m in sols:
            print(f"  {p:10} {m}")
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
