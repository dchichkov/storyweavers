#!/usr/bin/env python3
"""
storyworlds/worlds/expressive_ritual_happy_ending_whodunit.py
==============================================================

A small whodunit-style story world with an expressive ritual, a puzzling
disappearance, and a happy ending.

Seed idea:
---
During a quiet community ritual, something small and important goes missing.
A careful child notices the clues, asks gentle questions, and discovers what
really happened. The lost thing is found, the worry lifts, and the ritual ends
with everyone smiling.

World idea:
---
- Physical state: a ritual space, a missing token, crumbs / footprints / signs
  of movement, and a found object.
- Emotional state: curiosity, worry, suspicion, relief, and joy.
- The story is driven by state changes: who noticed what, what clue was found,
  and how the truth resolved the tension.

Style:
---
Whodunit, but child-facing and warm. The story should feel like a small mystery
with an expressive ritual, not a grim crime tale.
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
# Small world constants.
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    detective: object | None = None
    helper: object | None = None
    missing: object | None = None
    def __post_init__(self) -> None:
        for key in ["dust", "crumbs", "missing", "found", "tidy"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "suspicion", "relief", "joy", "care"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
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
    place: str = "the community room"
    time: str = "evening"
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
class Ritual:
    name: str
    verb: str
    expressive_detail: str
    clue_rich: bool
    requires: list[str] = field(default_factory=list)
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
class MissingThing:
    label: str
    phrase: str
    type: str
    hiding_places: list[str]
    value_word: str = "special"
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
class Culprit:
    label: str
    type: str
    motive: str
    clue: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "community_room": Setting(place="the community room", time="evening"),
    "library_corner": Setting(place="the library corner", time="afternoon"),
    "garden_hall": Setting(place="the garden hall", time="sunset"),
}

RITUALS = {
    "bell_circle": Ritual(
        name="the bell circle",
        verb="ring the little bell and pass the story cards",
        expressive_detail="The bell made a bright ding, and everyone took one careful breath together.",
        clue_rich=True,
        requires=["bell", "cards"],
    ),
    "tea_pause": Ritual(
        name="the tea pause",
        verb="sip warm tea and share one kind sentence each",
        expressive_detail="The teacups were tiny, and the room felt calm and cozy.",
        clue_rich=True,
        requires=["tea", "tray"],
    ),
    "lantern_wish": Ritual(
        name="the lantern wish",
        verb="light the lantern and whisper a wish into the soft glow",
        expressive_detail="The lantern glowed gold, and the shadows looked gentle instead of scary.",
        clue_rich=True,
        requires=["lantern"],
    ),
}

MISSING_THINGS = {
    "blue_ribbon": MissingThing(
        label="blue ribbon",
        phrase="a bright blue ribbon",
        type="ribbon",
        hiding_places=["chair", "bookstack", "window ledge"],
        value_word="important",
    ),
    "star_cookie": MissingThing(
        label="star cookie",
        phrase="a star-shaped cookie",
        type="cookie",
        hiding_places=["tray", "napkin basket", "rug"],
        value_word="special",
    ),
    "silver_key": MissingThing(
        label="silver key",
        phrase="a tiny silver key",
        type="key",
        hiding_places=["pocket", "flowerpot", "pencil cup"],
        value_word="little",
    ),
}

CULPRITS = {
    "mouse": Culprit(
        label="the mouse",
        type="mouse",
        motive="it wanted a crumb of something tasty",
        clue="tiny nibble marks",
    ),
    "puppy": Culprit(
        label="the puppy",
        type="puppy",
        motive="it chased the scent of cookies and knocked the item aside",
        clue="soft paw prints",
    ),
    "wind": Culprit(
        label="the breeze",
        type="wind",
        motive="it slid through the room and blew the item away",
        clue="an open window",
    ),
}

CHILD_NAMES = ["Mina", "Noah", "Lia", "Owen", "Sara", "Eli", "Pia", "Toby"]


# ---------------------------------------------------------------------------
# Parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    ritual: str
    missing: str
    culprit: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin.
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


ASP_RULES = r"""
ritual_valid(S, R, M) :- setting(S), ritual(R), missing(M),
                         requires(R, Req), supports(S, Req).
mystery_valid(S, R, M, C) :- ritual_valid(S, R, M), culprit(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, rit in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        for req in rit.requires:
            lines.append(asp.fact("requires", rid, req))
    for mid in MISSING_THINGS:
        lines.append(asp.fact("missing", mid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    # Simple support facts: every setting supports every required object here.
    for sid in SETTINGS:
        for rit in RITUALS.values():
            for req in rit.requires:
                lines.append(asp.fact("supports", sid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ritual_valid/3."))
    return sorted(set(asp.atoms(model, "ritual_valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid, rit in RITUALS.items():
            for mid in MISSING_THINGS:
                if rit.clue_rich:
                    combos.append((sid, rid, mid))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen ritual would not leave enough clues for a gentle whodunit.)"


# ---------------------------------------------------------------------------
# World simulation.
# ---------------------------------------------------------------------------
def _mystery_stirs(world: World, detective: Entity, missing: Entity, culprit: Entity) -> None:
    detective.memes["curiosity"] += 1
    missing.meters["missing"] = 1
    culprit.memes["suspicion"] += 1
    world.say(
        f"{detective.id} looked around the room and noticed something was off: "
        f"{missing.label} was gone."
    )
    world.say(
        f"That made {detective.pronoun('possessive')} curiosity wake up like a little lamp."
    )


def _clue_one(world: World, detective: Entity, missing: Entity, culprit: Entity) -> None:
    if culprit.type == "mouse":
        world.say(
            f"Near the table, {detective.id} found {culprit.clue} and a crumb trail."
        )
    elif culprit.type == "puppy":
        world.say(
            f"By the rug, {detective.id} found {culprit.clue} and one tiny wobble in the chairs."
        )
    else:
        world.say(
            f"By the window, {detective.id} found {culprit.clue} and a cool draft slipping in."
        )
    detective.memes["suspicion"] += 1


def _clue_two(world: World, detective: Entity, missing: Entity, culprit: Entity) -> None:
    if culprit.type == "mouse":
        missing.hidden_in = "napkin basket"
        world.say(
            f"Then {detective.id} followed the crumbs to the napkin basket, where {missing.label} was tucked away."
        )
    elif culprit.type == "puppy":
        missing.hidden_in = "rug"
        world.say(
            f"Then {detective.id} lifted the edge of the rug, and there was {missing.label}, safe and sound."
        )
    else:
        missing.hidden_in = "flowerpot"
        world.say(
            f"Then {detective.id} checked the flowerpot, and there was {missing.label}, resting under a leaf."
        )
    missing.meters["found"] = 1
    detective.memes["relief"] += 1
    detective.memes["joy"] += 1


def _resolve(world: World, detective: Entity, helper: Entity, missing: Entity, culprit: Entity, ritual: Ritual) -> None:
    helper.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} smiled, because the mystery had a kind answer after all."
    )
    if culprit.type == "mouse":
        world.say(
            f"They gave the mouse a few crumbs far away from the table so it would not steal again."
        )
    elif culprit.type == "puppy":
        world.say(
            f"They gave the puppy a soft chew toy, and it wagged happily beside the chairs."
        )
    else:
        world.say(
            f"They closed the window, and the breeze no longer had a chance to play tricks."
        )
    world.say(
        f"At last, the room was ready again for {ritual.name}, and {missing.label} was back where it belonged."
    )


def tell(setting: Setting, ritual: Ritual, missing_cfg: MissingThing, culprit_cfg: Culprit,
         hero_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl",
        label=hero_name,
    ))
    helper = world.add(Entity(
        id="Aunt June",
        kind="character",
        type="woman",
        label="Aunt June",
    ))
    culprit = world.add(Entity(
        id=culprit_cfg.label,
        kind="character" if culprit_cfg.type in {"mouse", "puppy"} else "thing",
        type=culprit_cfg.type,
        label=culprit_cfg.label,
    ))
    missing = world.add(Entity(
        id=missing_cfg.label,
        kind="thing",
        type=missing_cfg.type,
        label=missing_cfg.label,
        phrase=missing_cfg.phrase,
        owner="Aunt June",
    ))

    world.say(
        f"On {setting.place}, everyone gathered for {ritual.name}."
    )
    world.say(ritual.expressive_detail)
    world.say(
        f"{hero_name} loved how the ritual felt expressive and calm, like a small story told with hands, voices, and light."
    )

    world.para()
    _mystery_stirs(world, detective, missing, culprit)
    world.say(
        f"Aunt June frowned softly. 'Let's look carefully,' she said."
    )
    world.say(
        f"{hero_name} nodded, because a good whodunit starts with noticing."
    )

    world.para()
    _clue_one(world, detective, missing, culprit)
    _clue_two(world, detective, missing, culprit)
    _resolve(world, detective, helper, missing, culprit, ritual)

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        missing=missing,
        ritual=ritual,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit about {f["ritual"].name} in {f["setting"].place} where {f["missing"].label} goes missing.',
        f"Tell an expressive mystery story with a ritual, a clue, and a happy ending.",
        f'Write a gentle detective story for young children that includes the word "ritual" and ends with the missing thing found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    culprit = _safe_fact(world, f, "culprit")
    missing = _safe_fact(world, f, "missing")
    ritual = _safe_fact(world, f, "ritual")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What was the mystery in {place} during {ritual.name}?",
            answer=f"The mystery was that {missing.label} disappeared during {ritual.name}. {detective.id} noticed it was missing and decided to look for clues.",
        ),
        QAItem(
            question=f"How did {detective.id} solve the whodunit?",
            answer=f"{detective.id} looked carefully, found a clue, and followed it to where {missing.label} had been hidden. That is how the mystery was solved.",
        ),
        QAItem(
            question=f"Who helped make the ending happy after the clue was found?",
            answer=f"{helper.id} helped by staying calm, listening to the clues, and making sure everything was safe again. Then the whole room could return to {ritual.name}.",
        ),
        QAItem(
            question=f"What really happened to {missing.label}?",
            answer=f"{culprit.label} caused the trouble in a small way, and {missing.label} ended up in its hiding place. The clue led {detective.id} to it, and the lost thing was found.",
        ),
    ]


KNOWLEDGE = {
    "ritual": [
        QAItem(
            question="What is a ritual?",
            answer="A ritual is something people do in a special order again and again, like lighting a candle or saying kind words together.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that helps someone figure out what happened, like footprints, crumbs, or a note.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not know yet, so you look carefully and ask questions to find the answer.",
        )
    ],
    "happy": [
        QAItem(
            question="What makes an ending happy?",
            answer="An ending feels happy when the worry is solved, the missing thing is found, and the characters feel safe again.",
        )
    ],
    "expressive": [
        QAItem(
            question="What does expressive mean?",
            answer="Expressive means showing feelings clearly with words, faces, voices, or actions.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *KNOWLEDGE["ritual"],
        *KNOWLEDGE["clue"],
        *KNOWLEDGE["mystery"],
        *KNOWLEDGE["happy"],
        *KNOWLEDGE["expressive"],
    ]


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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:16} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly whodunit with an expressive ritual and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--missing", choices=MISSING_THINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name", choices=CHILD_NAMES)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "ritual", None) is None or c[1] == getattr(args, "ritual", None))
        and (getattr(args, "missing", None) is None or c[2] == getattr(args, "missing", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, ritual, missing = rng.choice(list(combos))
    culprit = getattr(args, "culprit", None) or rng.choice(sorted(CULPRITS))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(setting=setting, ritual=ritual, missing=missing, culprit=culprit, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(RITUALS, params.ritual),
                 _safe_lookup(MISSING_THINGS, params.missing), _safe_lookup(CULPRITS, params.culprit),
                 params.name)
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
        print(asp_program("#show ritual_valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show ritual_valid/3."))
        combos = sorted(set(asp.atoms(model, "ritual_valid")))
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("community_room", "bell_circle", "blue_ribbon", "mouse", "Mina"),
            StoryParams("library_corner", "tea_pause", "star_cookie", "puppy", "Noah"),
            StoryParams("garden_hall", "lantern_wish", "silver_key", "wind", "Lia"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.ritual} at {p.setting} (missing: {p.missing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
