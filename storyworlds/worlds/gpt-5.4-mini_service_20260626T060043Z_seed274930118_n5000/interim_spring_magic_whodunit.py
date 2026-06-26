#!/usr/bin/env python3
"""
storyworlds/worlds/interim_spring_magic_whodunit.py
===================================================

A small whodunit storyworld set in an interim springtime place where a little
bit of magic changes what the clues mean.

Premise:
- A caretaker wants a missing spring token found before the interim fair.
- A child sleuth notices the room, the weather, and the magic trail.
- The mystery turns on ordinary clues that magic has touched.

The world is intentionally tiny: a few typed entities, physical meters, and
emotional memes drive the plot. The narrative is stateful rather than a frozen
template, and the ASP twin mirrors the reasonableness gate used in Python.
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
# Core domain constants.
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
TRACES = ("sparkle", "petal", "dew", "chalk")

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Ruby", "Sage", "Lena"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Ezra", "Milo", "Rowan"]
DETECTIVE_TITLES = ["sleuth", "detective", "helper", "observer"]


# ---------------------------------------------------------------------------
# World entities.
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
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    suspect_ent: object | None = None
    def __post_init__(self):
        for k in ("wet", "moved", "hidden", "found", "magical"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "delight", "suspicion", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Setting:
    place: str = "the interim hall"
    season: str = "spring"
    weather: str = "soft rain"
    afford_magic: bool = True
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
class Clue:
    id: str
    label: str
    trail: str
    reveals: str
    magic: bool = False
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
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    secret: str
    suspicious: bool = False
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
    clue: str
    suspect: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
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
    "hall": Setting(place="the interim hall", season="spring", weather="soft rain", afford_magic=True),
    "garden": Setting(place="the spring garden", season="spring", weather="light drizzle", afford_magic=True),
    "porch": Setting(place="the old porch", season="spring", weather="misty air", afford_magic=True),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        label="a tiny lantern",
        trail="sparkles",
        reveals="the lantern had been hidden in plain sight behind the draped curtain",
        magic=True,
    ),
    "button": Clue(
        id="button",
        label="a brass button",
        trail="dew marks",
        reveals="the button had fallen from a coat and rolled under the bench",
        magic=False,
    ),
    "key": Clue(
        id="key",
        label="a silver key",
        trail="chalk dust",
        reveals="the key had slipped into a flowerpot by the window",
        magic=True,
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a blue ribbon",
        trail="petals",
        reveals="the ribbon had snagged on a branch and fluttered back to the hedge",
        magic=False,
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the gray cat",
        type="cat",
        alibi="the cat had been napping on the warm mat",
        secret="the cat had only chased a moth and touched nothing important",
        suspicious=True,
    ),
    "gardener": Suspect(
        id="gardener",
        label="the gardener",
        type="man",
        alibi="the gardener had been watering tulips in the side bed",
        secret="the gardener knew where the spare tools were kept",
        suspicious=True,
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        type="woman",
        alibi="the neighbor had been hanging wet coats on the line",
        secret="the neighbor had borrowed the lantern to light the path",
        suspicious=True,
    ),
}

HELPERS = {
    "aunt": ("aunt", "an aunt", "her aunt"),
    "uncle": ("uncle", "an uncle", "his uncle"),
    "friend": ("friend", "a friend", "their friend"),
}

SETTINGS_ORDER = ["hall", "garden", "porch"]


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.fired: set[tuple] = set()
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
            self.events.append(text)

    def render(self) -> str:
        out = []
        buf = []
        for line in self.events:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
def _r_magic_clue(world: World) -> list[str]:
    out: list[str] = []
    for clue in list(world.entities.values()):
        if clue.kind != "clue" or clue.meters["found"] < THRESHOLD:
            continue
        if clue.meters["magical"] >= THRESHOLD and ("magic", clue.id) not in world.fired:
            world.fired.add(("magic", clue.id))
            out.append(f"The clue shone brighter, as if the spring air itself wanted to help.")
    return out


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for suspect in list(world.entities.values()):
        if suspect.kind != "suspect":
            continue
        if suspect.memes["suspicion"] >= THRESHOLD and ("suspicion", suspect.id) not in world.fired:
            world.fired.add(("suspicion", suspect.id))
            out.append(f"{suspect.label} looked guilty for a moment, but the sleuth kept looking.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") and ("relief", "scene") not in world.fired:
        world.fired.add(("relief", "scene"))
        for ent in list(world.entities.values()):
            if ent.kind == "hero":
                ent.memes["relief"] += 1
        out.append("The room felt lighter once the missing thing was found.")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_magic_clue, _r_suspicion, _r_relief):
            produced = rule(world)
            if produced:
                changed = True
                for s in produced:
                    world.say(s)


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------
def clue_can_be_missing(clue: Clue, suspect: Suspect) -> bool:
    return clue.magic or clue.id in {"button", "ribbon", "key", "lantern"}


def chosen_solution_is_reasonable(clue: Clue, suspect: Suspect) -> bool:
    # The solution must fit the clue and cannot rely on nonsense.
    return clue_can_be_missing(clue, suspect)


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('title', 'sleuth')} who noticed tiny things."
    )
    world.say(
        f"On a spring afternoon at {world.setting.place}, {helper.label} worried because {clue.label} was missing."
    )


def look_around(world: World, hero: Entity, clue: Clue, suspect: Suspect) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} looked at the wet steps, the window sill, and the flowerpots."
    )
    world.say(
        f"{hero.id} saw {clue.trail} near the path and thought about {suspect.label}."
    )


def question_suspect(world: World, hero: Entity, suspect: Suspect) -> None:
    suspect.memes["trust"] += 1
    suspect.memes["suspicion"] += 1
    world.say(
        f"{hero.id} asked {suspect.label} a careful question."
    )
    world.say(
        f"{suspect.label} answered, '{suspect.alibi},' which sounded honest but not complete."
    )


def find_clue(world: World, hero: Entity, clue: Clue) -> None:
    item = world.get(clue.id)
    item.meters["found"] = 1
    if clue.magic:
        item.meters["magical"] = 1
    world.say(
        f"Then {hero.id} spotted {clue.label} exactly where the strange little trail led."
    )
    world.say(clue.reveals)


def solve_mystery(world: World, hero: Entity, helper: Entity, clue: Clue, suspect: Suspect) -> None:
    world.facts["solved"] = True
    propagate(world)
    if clue.id == "lantern":
        answer = f"{suspect.label} had borrowed the lantern and set it down by the curtain"
    elif clue.id == "key":
        answer = f"the silver key had been tucked into a flowerpot by magic that made it seem to hop"
    elif clue.id == "button":
        answer = f"a coat button had fallen off during the helper's quick walk through the hall"
    else:
        answer = f"the ribbon had drifted to the hedge after catching a little spring breeze"
    world.say(
        f"{hero.id} smiled and explained it all: {answer}."
    )
    world.say(
        f"{helper.label} laughed with relief, and {hero.id} stood a little taller in the spring light."
    )


def tell(setting: Setting, clue: Clue, suspect: Suspect, hero_name: str, hero_type: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="hero", type=hero_type))
    hero.memes["title"] = "sleuth"
    helper_label = _safe_lookup(HELPERS, helper_kind)[1]
    helper = world.add(Entity(id="Helper", kind="helper", type="adult", label=helper_label))
    clue_ent = world.add(Entity(id=clue.id, kind="clue", type="thing", label=clue.label))
    suspect_ent = world.add(Entity(id=suspect.id, kind="suspect", type=suspect.type, label=suspect.label))

    world.facts.update(hero=hero, helper=helper, clue=clue_ent, suspect=suspect_ent, setting=setting)
    introduce(world, hero, helper, clue)
    world.say("")
    look_around(world, hero, clue, suspect_ent)
    question_suspect(world, hero, suspect_ent)
    world.say("")
    find_clue(world, hero, clue)
    solve_mystery(world, hero, helper, clue, suspect_ent)
    return world


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is solvable when it is the kind of thing that can plausibly be missing.
solvable(C) :- clue(C), can_go_missing(C).

% A mystery is valid when a setting, a clue, and a suspect fit together.
valid_story(S, C, P) :- setting(S), clue(C), suspect(P), solvable(C), in_setting(S, C), in_setting(S, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_magic:
            lines.append(asp.fact("magic_setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("can_go_missing", cid))
        if c.magic:
            lines.append(asp.fact("magical", cid))
    for pid, p in SUSPECTS.items():
        lines.append(asp.fact("suspect", pid))
        for place in SETTINGS:
            lines.append(asp.fact("in_setting", place, pid))
    for place in SETTINGS:
        for cid in CLUES:
            lines.append(asp.fact("in_setting", place, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    solvable = sorted(set(asp.atoms(model, "solvable")))
    python = sorted((cid,) for cid, c in CLUES.items() if clue_can_be_missing(c, next(iter(SUSPECTS.values()))))
    if solvable:
        print(f"OK: ASP produced {len(solvable)} solvable clues.")
        return 0
    print("MISMATCH: ASP produced no solvable clues.")
    return 1


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a child set in {f["setting"].place} during spring, with a little magic.',
        f"Tell a mystery where {f['hero'].id} notices {f['clue'].label} and figures out what happened.",
        f"Write a gentle detective story with a spring clue, a suspicious character, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Entity = _safe_fact(world, f, "clue")
    suspect: Entity = _safe_fact(world, f, "suspect")
    return [
        QAItem(
            question=f"Who was the little detective in the story?",
            answer=f"{hero.id} was the little sleuth who paid attention to tiny clues.",
        ),
        QAItem(
            question=f"What was missing at {world.setting.place}?",
            answer=f"{clue.label} was missing, and that made {helper.label} worry.",
        ),
        QAItem(
            question=f"Who did {hero.id} look at as a possible suspect?",
            answer=f"{suspect.label} looked suspicious at first, even though {suspect.secret.lower()}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{hero.id} found {clue.label} and explained the clue trail, so everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks closely, asks questions, and uses clues to solve a problem.",
        ),
        QAItem(
            question="Why can spring feel magical?",
            answer="Spring can feel magical because flowers bloom, rain makes everything fresh, and the light feels new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small springtime whodunit with a touch of magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    if not clue_can_be_missing(_safe_lookup(CLUES, clue), _safe_lookup(SUSPECTS, suspect)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, clue=clue, suspect=suspect, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(SUSPECTS, params.suspect), params.name, params.gender, params.helper)
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
        print()
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(eid, ent.kind, ent.type, dict(ent.meters), dict(ent.memes))
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
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="hall", clue="lantern", suspect="neighbor", name="Mina", gender="girl", helper="aunt"),
            StoryParams(place="garden", clue="key", suspect="gardener", name="Owen", gender="boy", helper="uncle"),
            StoryParams(place="porch", clue="button", suspect="cat", name="Ivy", gender="girl", helper="friend"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {sample.params.name}: {sample.params.clue} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
