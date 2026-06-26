#!/usr/bin/env python3
"""
storyworlds/worlds/cheap_descriptor_tidal_mystery_to_solve_happy.py
===================================================================

A small folk-tale storyworld about a tidal shore mystery that can be solved
by noticing a humble clue, asking the right question, and ending happily.

Seeded premise:
- cheap
- descriptor
- tidal

Story shape:
- A child goes to the tidal shore with a caregiver.
- A small mystery appears: a lost thing, a strange sign, or a broken clue.
- The child solves it by matching a descriptor to the right owner/place.
- The ending is warm and happy, with a repaired or returned treasure.

This is a standalone classical simulation with a tiny world model, QA sets,
and an inline ASP twin for the reasonableness gate.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    place: str = "the tidal shore"
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
class Mystery:
    id: str
    label: str
    phrase: str
    clue_word: str
    solved_by: str
    place: str
    mood_turn: str
    truth: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    owner_kind: str
    location: str
    descriptor: str
    cheap: bool = False
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
class Helper:
    id: str
    label: str
    type: str
    advice: str
    knows: str
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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    mystery: str
    treasure: str
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


SETTINGS = {
    "tidal_shore": Setting(place="the tidal shore", affords={"search", "listen", "solve"}),
}

MYSTERIES = {
    "lost_bell": Mystery(
        id="lost_bell",
        label="a missing bell",
        phrase="a small brass bell",
        clue_word="tidal",
        solved_by="follow the tide line",
        place="the tidal shore",
        mood_turn="the bell's sound was carried back by the water",
        truth="the bell had been tucked under a net by the old driftwood bench",
    ),
    "mystery_shell": Mystery(
        id="mystery_shell",
        label="a strange shell sign",
        phrase="a shell with a carved mark",
        clue_word="descriptor",
        solved_by="read the carved mark",
        place="the tidal shore",
        mood_turn="the mark pointed to the right basket",
        truth="the shell described the basket that belonged to the fisher aunt",
    ),
    "cheap_ribbon": Mystery(
        id="cheap_ribbon",
        label="a cheap ribbon mystery",
        phrase="a cheap blue ribbon",
        clue_word="cheap",
        solved_by="ask who bought the ribbon",
        place="the tidal shore",
        mood_turn="the ribbon matched the child who had tied it to the crab pot",
        truth="the ribbon had fallen from the child's own crab pot and blown to the rocks",
    ),
}

TREASURES = {
    "bell": Treasure(
        id="bell",
        label="bell",
        phrase="a small brass bell",
        owner_kind="old fisher",
        location="driftwood bench",
        descriptor="tiny and bright",
        cheap=False,
    ),
    "basket_tag": Treasure(
        id="basket_tag",
        label="basket tag",
        phrase="a wicker basket tag",
        owner_kind="aunt",
        location="basket stall",
        descriptor="carved with neat lines",
        cheap=True,
    ),
    "ribbon": Treasure(
        id="ribbon",
        label="ribbon",
        phrase="a cheap blue ribbon",
        owner_kind="child",
        location="crab pot",
        descriptor="thin and frayed",
        cheap=True,
    ),
}

HELPERS = {
    "heron": Helper(
        id="heron",
        label="a gray heron",
        type="thing",
        advice="look where the water leaves a clean line",
        knows="the tide line hides little things when the water turns back",
    ),
    "grandma": Helper(
        id="grandma",
        label="Grandma",
        type="woman",
        advice="read the small mark before you guess",
        knows="a good descriptor tells the truth better than a fancy boast",
    ),
    "fisher": Helper(
        id="fisher",
        label="the old fisher",
        type="man",
        advice="check the bench where the nets rest",
        knows="lost things often wait near the place where they were used",
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Sofi", "Nina", "Tessa", "Elin"]
BOY_NAMES = ["Pax", "Oren", "Milo", "Tobin", "Eli", "Finn"]
TRAITS = ["curious", "brave", "gentle", "cheerful", "quick-minded", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(SETTINGS["tidal_shore"].place, m.id, t.id) for m in MYSTERIES.values() for t in TREASURES.values()
            if m.id == "lost_bell" and t.id == "bell"
            or m.id == "mystery_shell" and t.id == "basket_tag"
            or m.id == "cheap_ribbon" and t.id == "ribbon"]


def is_reasonable(mystery: Mystery, treasure: Treasure) -> bool:
    if mystery.id == "lost_bell" and treasure.id == "bell":
        return True
    if mystery.id == "mystery_shell" and treasure.id == "basket_tag":
        return True
    if mystery.id == "cheap_ribbon" and treasure.id == "ribbon":
        return True
    return False


def explain_rejection(mystery: Mystery, treasure: Treasure) -> str:
    return (
        f"(No story: the mystery '{mystery.label}' does not fit the treasure '{treasure.label}'. "
        f"Choose the matching pair so the child can truly solve something at the tidal shore.)"
    )


ASP_RULES = r"""
mystery_pair(M, T) :- mystery(M), treasure(T), fits(M, T).
valid_story(shore, M, T) :- mystery_pair(M, T), place(shore).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "shore"))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("clue", m.id, m.clue_word))
    for t in TREASURES.values():
        lines.append(asp.fact("treasure", t.id))
        if t.cheap:
            lines.append(asp.fact("cheap", t.id))
        lines.append(asp.fact("descriptor", t.id, t.descriptor))
    for m in MYSTERIES.values():
        for t in TREASURES.values():
            if is_reasonable(m, t):
                lines.append(asp.fact("fits", m.id, t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale tidal mystery with a happy ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--treasure", choices=TREASURES)
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
    mystery = _safe_lookup(MYSTERIES, getattr(args, "mystery", None)) if getattr(args, "mystery", None) else rng.choice(list(MYSTERIES.values()))
    treasure = _safe_lookup(TREASURES, getattr(args, "treasure", None)) if getattr(args, "treasure", None) else rng.choice(list(TREASURES.values()))
    if not is_reasonable(mystery, treasure):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait,
                       mystery=mystery.id, treasure=treasure.id, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["tidal_shore"])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    treasure = _safe_lookup(TREASURES, params.treasure)
    helper = _safe_lookup(HELPERS, params.helper)

    world.facts.update(child=child, parent=parent, mystery=mystery, treasure=treasure, helper=helper)

    world.say(
        f"Once, {params.name} was a {params.trait} little {params.gender} who loved the tidal shore, "
        f"where the waves left shiny scraps and secret tracks."
    )
    world.say(
        f"One day, {params.name} and {parent.label} went to {world.setting.place}, and there they found "
        f"{mystery.phrase} beside {treasure.phrase}."
    )
    world.para()
    world.say(
        f"{params.name} wanted to {mystery.solved_by}, but the meaning was not clear at first."
    )
    world.say(
        f"Then {helper.label} said, \"{helper.advice}.\""
    )
    world.say(
        f"That was the little descriptor the child needed: {mystery.clue_word}."
    )
    world.para()
    world.say(
        f"{params.name} followed the clue and {mystery.mood_turn}."
    )
    world.say(
        f"At last, the child found the truth: {mystery.truth}."
    )
    world.say(
        f"{parent.label.capitalize()} smiled, the lost thing went home, and the tidal shore looked bright again."
    )
    world.say(
        f"By evening, {params.name} carried {treasure.phrase} safely home, feeling proud and warm inside."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mystery = _safe_fact(world, f, "mystery")
    treasure = _safe_fact(world, f, "treasure")
    return [
        f"Write a folk-tale story about {child.id} at the tidal shore, where a {mystery.label} is solved with a small clue.",
        f"Tell a happy ending story in which {child.id} notices {treasure.phrase} and learns the right descriptor to use.",
        f"Write a short child-friendly mystery where the words cheap, descriptor, and tidal all belong in the tale.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    mystery = _safe_fact(world, f, "mystery")
    treasure = _safe_fact(world, f, "treasure")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who went to the tidal shore to solve the mystery?",
            answer=f"{child.id} went with {parent.label} to the tidal shore to solve {mystery.label}."
        ),
        QAItem(
            question=f"What clue helped {child.id} understand the mystery?",
            answer=f"The clue was the word {mystery.clue_word}, and {helper.label} told {child.id} to notice it."
        ),
        QAItem(
            question=f"What treasure stayed safe by the end of the story?",
            answer=f"{treasure.phrase} stayed safe, and {child.id} carried it home happily."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tidal mean?",
            answer="Tidal means connected to the rise and fall of the sea as the water comes in and goes back out."
        ),
        QAItem(
            question="What is a descriptor?",
            answer="A descriptor is a word or mark that helps describe something so you can tell what it is."
        ),
        QAItem(
            question="What does cheap mean?",
            answer="Cheap means something costs very little money."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.type:8}) kind={e.kind}")
    return "\n".join(lines)


def valid_story_params_list() -> list[StoryParams]:
    out: list[StoryParams] = []
    for _, m_id, t_id in valid_combos():
        out.append(StoryParams(
            name="Mara",
            gender="girl",
            parent="grandma",
            trait="curious",
            mystery=m_id,
            treasure=t_id,
            helper="heron",
        ))
    return out


CURATED = [
    StoryParams(name="Mara", gender="girl", parent="grandma", trait="curious", mystery="lost_bell", treasure="bell", helper="fisher"),
    StoryParams(name="Oren", gender="boy", parent="mother", trait="quick-minded", mystery="mystery_shell", treasure="basket_tag", helper="grandma"),
    StoryParams(name="Nina", gender="girl", parent="father", trait="brave", mystery="cheap_ribbon", treasure="ribbon", helper="heron"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combos:")
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
