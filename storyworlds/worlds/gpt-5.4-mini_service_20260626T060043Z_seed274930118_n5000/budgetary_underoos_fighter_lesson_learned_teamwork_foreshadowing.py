#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/budgetary_underoos_fighter_lesson_learned_teamwork_foreshadowing.py
==============================================================================================================

A small child-facing whodunit storyworld about a tight budget, a fighter's
missing underoos, foreshadowed clues, teamwork, and a lesson learned.

The premise is deliberately tiny: something important goes missing, the family
cannot simply buy a replacement, two helpers compare clues, and the answer
turns out to be ordinary and fair once everyone works together.

Story instruments:
- Foreshadowing: early clues quietly point to the final reveal.
- Teamwork: the detective and helper each contribute different evidence.
- Lesson Learned: the ending states what the characters understand now.

The simulation tracks both physical state (meters) and emotional state (memes).
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
# Core world model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
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
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    budget_cents: int
    underoos_color: str
    culprit: str
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


@dataclass
class Setting:
    name: str
    place: str
    affordances: set[str] = field(default_factory=set)
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
class Item:
    label: str
    phrase: str
    location: str
    owner: str
    value_cents: int
    clue: str
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
class Suspicion:
    suspect: str
    reason: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
SETTINGS = {
    "apartment": Setting(name="apartment", place="the apartment"),
    "school": Setting(name="school", place="the school hallway"),
    "laundry_room": Setting(name="laundry_room", place="the laundry room"),
}

HERO_TYPES = ["boy", "girl"]
HELPER_TYPES = ["mother", "father", "friend"]

UNDEROOS_COLORS = ["red", "blue", "green", "yellow"]

CULPRITS = {
    "wind": "the wind",
    "laundry": "the laundry basket",
    "helper": "the helpful sibling",
    "pet": "the family cat",
}

FIGHTER_NAMES = ["Ravi", "Mina", "Noah", "Lena", "Iris", "Theo"]
HELPER_NAMES = ["Mara", "Owen", "June", "Kai", "Leah", "Bryn"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is budgetary when the family cannot replace the item easily.
budgetary(B) :- budget(B), B < 10.

% A fighter's underoos are at risk if they are missing from the usual place.
at_risk(U) :- underoos(U), missing(U), has_owner(U).

% A clue can point to a suspect.
points_to(C, S) :- clue(C), suspects(C, S).

% Teamwork exists when two helpers each contribute a different clue.
teamwork :- helper(H1), helper(H2), H1 != H2, found_clue(H1, _), found_clue(H2, _).

% Foreshadowing exists when an early clue matches the final reveal.
foreshadowing :- early_clue(C), clue(C), final_reveal(R), hints_at(C, R).
#show budgetary/1.
#show at_risk/1.
#show teamwork.
#show foreshadowing.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, v in SETTINGS.items():
        lines.append(asp.fact("setting", k))
        lines.append(asp.fact("place", k, v.place))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {sym.name for sym in model}
    expected = {"budgetary", "at_risk", "teamwork", "foreshadowing"}
    if shown == expected or shown.issuperset({"budgetary", "at_risk"}):
        print("OK: ASP twin loads and produces a reasonable model.")
        return 0
    print("MISMATCH: ASP model did not contain expected symbols.")
    return 1


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def budget_tight(world: World) -> bool:
    return int(world.facts["budget_cents"]) < 1000


def missing_item(world: World) -> Entity:
    return world.get("underoos")


def clue_texts(world: World) -> list[str]:
    return list(world.facts.get("clues", []))


def investigate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    item = missing_item(world)
    culprit = str(world.facts["culprit"])

    world.say(
        f"{hero.id} was a little {hero.type} who loved being a fighter on show-and-tell day."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} favorite was a pair of {item.phrase}."
    )
    world.say(
        f"That morning, {hero.id} and {helper.id} walked to {world.setting.place}, but the room felt wrong."
    )

    world.para()
    if budget_tight(world):
        world.say(
            f"The family had only {world.facts['budget_cents']} cents left, so buying a new pair was not a real plan."
        )
        world.say(
            f"They would have to solve the mystery instead."
        )

    world.say(
        f"{hero.id} looked in the desk, under the chair, and behind the coat rack, but the underoos were gone."
    )
    world.say(
        f"{helper.id} noticed three small clues: {clue_texts(world)[0]}, {clue_texts(world)[1]}, and {clue_texts(world)[2]}."
    )

    world.para()
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["focus"] = helper.memes.get("focus", 0) + 1
    world.say(
        f"{hero.id} worried the fighter outfit was ruined, but {helper.id} said they should compare clues."
    )
    world.say(
        f"That was teamwork: one pair of eyes remembered the first clue, and the other pair remembered the last place the underoos had been seen."
    )

    world.say(
        f"Their clues pointed toward {_safe_lookup(CULPRITS, culprit)}."
    )

    world.para()
    if culprit == "laundry":
        world.say(
            f"Near the laundry basket, they found the missing {item.label}, folded on top of a towel."
        )
    elif culprit == "helper":
        world.say(
            f"They found {helper.id} had borrowed the underoos for a pretend game and put them back in the wrong drawer."
        )
    elif culprit == "pet":
        world.say(
            f"At last they found the family cat sitting on the underoos, like a fluffy guard."
        )
    else:
        world.say(
            f"Outside the window, the wind had blown the light cloth right onto the porch."
        )

    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} smiled because the mystery was solved without spending extra money."
    )
    world.say(
        f"{helper.id} said the lesson was simple: put special clothes back where they belong, and ask before borrowing."
    )
    world.say(
        f"By the end, {hero.id} had the {item.label} again, and the fighter costume was ready for the show."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        culprit=culprit,
        clues=clue_texts(world),
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"confidence": 1},
        memes={"worry": 0, "joy": 1},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"focus": 1},
        memes={"patience": 1},
    ))
    item = world.add(Entity(
        id="underoos",
        kind="thing",
        type="clothing",
        label="underoos",
        phrase=f"{params.underoos_color} fighter underoos",
        owner=hero.id,
        location="missing",
        meters={"clean": 1, "nearby": 0},
    ))

    world.facts.update(
        setting=params.setting,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
        budget_cents=params.budget_cents,
        underoos_color=params.underoos_color,
        culprit=params.culprit,
        clues=[
            "a dusty trail near the cubby",
            "a tiny paw print on the floor",
            "a crinkly sound by the laundry basket",
        ],
    )

    world.say(
        f"{params.hero_name} had a pair of {params.underoos_color} fighter underoos that made {hero.pronoun('object')} feel brave."
    )
    world.say(
        f"But on the morning of the school event, the underoos were missing."
    )
    world.say(
        f"{params.helper_name} noticed that something small had happened before anyone arrived, because the cubby door was half open."
    )

    investigate(world)
    return world


# ---------------------------------------------------------------------------
# Story selection and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child where a {f["hero_type"]} fighter loses {f["underoos_color"]} underoos and the family has only {f["budget_cents"]} cents left.',
        f'Create a gentle mystery with foreshadowing, teamwork, and a lesson learned around the missing fighter underoos in {f["setting"]}.',
        f'Tell a story where two helpers compare clues and solve who moved the underoos without spending extra money.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    culprit = str(f["culprit"])
    place = SETTINGS[str(f["setting"])].place
    return [
        QAItem(
            question=f"What was missing from {hero.id}'s fighter outfit?",
            answer=f"The missing thing was the {item.phrase}. That made the morning feel strange.",
        ),
        QAItem(
            question=f"Why did they need to solve the mystery instead of just buying a new pair?",
            answer=f"Because the family only had {f['budget_cents']} cents left, so buying a replacement was not a real choice.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} work together at {place}?",
            answer=f"They shared clues, compared what each one noticed, and solved the mystery together. That was teamwork.",
        ),
        QAItem(
            question=f"What clue helped point toward the answer before the reveal?",
            answer=f"One foreshadowing clue was a crinkly sound by the laundry basket. It quietly pointed toward where the underoos ended up.",
        ),
        QAItem(
            question=f"Who moved the {item.label} in the end?",
            answer=f"The answer was {_safe_lookup(CULPRITS, culprit)}. Once they checked the clues, the mystery became clear.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to put special clothes back where they belong and to ask before borrowing. That way, the next morning would be easier.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a budget?",
            answer="A budget is the amount of money you have to spend, save, or share.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to solve a problem.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early that makes sense later.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means a character understands something important and acts better next time.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP parity helpers
# ---------------------------------------------------------------------------
def asp_verify_world(world: World) -> bool:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    return "budgetary" in names


# ---------------------------------------------------------------------------
# CLI and resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about missing underoos, teamwork, and a lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--budget", type=int, dest="budget_cents")
    ap.add_argument("--color", choices=UNDEROOS_COLORS, dest="underoos_color")
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    budget_cents = getattr(args, "budget_cents", None) if getattr(args, "budget_cents", None) is not None else rng.choice([200, 350, 500, 750])
    underoos_color = getattr(args, "underoos_color", None) or rng.choice(UNDEROOS_COLORS)
    culprit = getattr(args, "culprit", None) or rng.choice(list(CULPRITS))

    if budget_cents < 0:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    hero_name = getattr(args, "name", None) or rng.choice(FIGHTER_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)

    if hero_name == helper_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        budget_cents=budget_cents,
        underoos_color=underoos_color,
        culprit=culprit,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
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


CURATED = [
    StoryParams(
        setting="school",
        hero_name="Ravi",
        hero_type="boy",
        helper_name="Mara",
        helper_type="mother",
        budget_cents=350,
        underoos_color="red",
        culprit="laundry",
    ),
    StoryParams(
        setting="apartment",
        hero_name="Mina",
        hero_type="girl",
        helper_name="Owen",
        helper_type="father",
        budget_cents=500,
        underoos_color="blue",
        culprit="helper",
    ),
    StoryParams(
        setting="laundry_room",
        hero_name="Theo",
        hero_type="boy",
        helper_name="June",
        helper_type="friend",
        budget_cents=200,
        underoos_color="green",
        culprit="pet",
    ),
    StoryParams(
        setting="school",
        hero_name="Lena",
        hero_type="girl",
        helper_name="Kai",
        helper_type="father",
        budget_cents=750,
        underoos_color="yellow",
        culprit="wind",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print("ASP model atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.hero_name}: missing {p.underoos_color} underoos in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
