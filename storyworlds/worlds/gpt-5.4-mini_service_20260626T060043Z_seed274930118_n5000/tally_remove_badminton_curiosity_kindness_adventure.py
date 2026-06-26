#!/usr/bin/env python3
"""
Standalone storyworld: a curious badminton adventure about tallying points,
learning when to remove a barrier, and choosing kindness over frustration.

This world follows the Storyweavers contract:
- self-contained stdlib script
- story-driven world model with physical meters and emotional memes
- inline ASP twin and Python reasonableness gate
- generation, QA, trace, JSON, and verification support
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
# Core domain registers
# ---------------------------------------------------------------------------

TARGET_ACTIVITY = "badminton"

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Nora", "Ava", "Ivy", "Ella", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Ben", "Max", "Owen", "Sam"]
NEUTRAL_NAMES = ["Pip", "Kai", "Remy", "Ari"]

PLACES = {
    "court": {
        "label": "the little court",
        "outdoor": True,
        "affords": {"badminton"},
        "detail": "The little court waited under a bright sky, with chalk lines like tiny paths."
    },
    "yard": {
        "label": "the backyard",
        "outdoor": True,
        "affords": {"badminton"},
        "detail": "The backyard was open and breezy, with enough room for a quick game."
    },
    "gym": {
        "label": "the gym",
        "outdoor": False,
        "affords": {"badminton"},
        "detail": "The gym was quiet except for squeaky shoes and a soft echo from the walls."
    },
}

ACTIVITIES = {
    "badminton": {
        "verb": "play badminton",
        "gerund": "playing badminton",
        "rush": "run after the shuttlecock",
        "keyword": "badminton",
        "kind": "sport",
        "mess": "scuffed",
        "zone": {"feet", "hands"},
        "soil": "scuffed and tired",
        "detail": "The birdie skipped and spun like a white feather on a mission.",
        "tags": {"badminton", "sport", "tally"},
    }
}

ACTIONS = {
    "tally": {
        "verb": "tally the points",
        "noun": "tally",
        "effect": "counted each good hit with a careful finger",
        "tags": {"tally", "counting"},
    },
    "remove": {
        "verb": "remove the tangled tape",
        "noun": "remove",
        "effect": "lifted away the sticky strip so the shuttle could fly straight",
        "tags": {"remove", "helping"},
    },
}

PROBLEMS = {
    "tape": {
        "label": "the sticky tape",
        "phrase": "a strip of sticky tape",
        "place": "near the net",
        "risk": "it could snag the shuttlecock and spoil the game",
    },
    "branch": {
        "label": "the low branch",
        "phrase": "a low branch hanging over the court",
        "place": "above the court",
        "risk": "it could knock the birdie off course",
    },
}

GENTLE_ITEMS = {
    "scorecard": {
        "label": "scorecard",
        "phrase": "a small scorecard with bright squares",
        "kind": "paper",
    },
    "racket": {
        "label": "racket",
        "phrase": "a light blue racket",
        "kind": "sport gear",
    },
    "birdie": {
        "label": "shuttlecock",
        "phrase": "a white shuttlecock",
        "kind": "sport gear",
    },
}

TRAITS = ["curious", "kind", "brave", "careful", "gentle"]

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    birdie: object | None = None
    hero: object | None = None
    partner: object | None = None
    problem: object | None = None
    racket: object | None = None
    scorecard: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    label: str
    outdoor: bool
    affords: set[str]
    detail: str
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
    activity: str
    action: str
    problem: str
    name: str
    partner: str
    gender: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for ent in self.entities.values():
            bits = []
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            if ent.plural:
                bits.append("plural=True")
            if ent.protective:
                bits.append("protective=True")
            out.append(f"  {ent.id:10} ({ent.kind:7}) {' '.join(bits)}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place affords badminton and the story uses a
% matching action/problem combination.
valid(Place, Activity, Action, Problem) :-
    afford(Place, Activity),
    has_action(Action),
    has_problem(Problem),
    activity_supports(Activity, Action),
    problem_matches(Activity, Problem).

% The kindness turn is considered reasonable when the action removes the
% obstacle that blocks the game.
kind_turn(Place, Activity, Action, Problem) :-
    valid(Place, Activity, Action, Problem),
    action_kind(Action, remove),
    problem_is_removable(Problem).

#show valid/4.
#show kind_turn/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in PLACES.items():
        lines.append(asp.fact("place", key))
        if setting["outdoor"]:
            lines.append(asp.fact("outdoor", key))
        for act in sorted(setting["affords"]):
            lines.append(asp.fact("afford", key, act))
    for key in ACTIVITIES:
        lines.append(asp.fact("activity", key))
        lines.append(asp.fact("activity_supports", key, key))
    for key in ACTIONS:
        lines.append(asp.fact("has_action", key))
    lines.append(asp.fact("action_kind", "tally", "tally"))
    lines.append(asp.fact("action_kind", "remove", "remove"))
    for key in PROBLEMS:
        lines.append(asp.fact("problem", key))
        lines.append(asp.fact("problem_is_removable", key))
        lines.append(asp.fact("problem_matches", "badminton", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_turns() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_turn/4."))
    return sorted(set(asp.atoms(model, "kind_turn")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for activity in ACTIVITIES:
            for action in ACTIONS:
                for problem in PROBLEMS:
                    if activity == "badminton" and action in {"tally", "remove"}:
                        combos.append((place, activity, action, problem))
    return combos


def explain_rejection(place: str, activity: str, action: str, problem: str) -> str:
    return (
        f"(No story: {action} does not fit a {activity} adventure at {place} "
        f"with {problem} in this world.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_setting(place_key: str) -> Setting:
    p = _safe_lookup(PLACES, place_key)
    return Setting(place=place_key, label=p["label"], outdoor=p["outdoor"], affords=set(p["affords"]), detail=p["detail"])


def choose_name(gender: str, rng: random.Random) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    if gender == "boy":
        return rng.choice(BOY_NAMES)
    return rng.choice(NEUTRAL_NAMES)


def select_problem(rng: random.Random) -> str:
    return rng.choice(sorted(PROBLEMS))


def select_action() -> str:
    return "remove"


def select_trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)


def build_world(params: StoryParams) -> World:
    setting = make_setting(params.place)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["small", params.trait],
        meters={"joy": 0.0, "energy": 1.0},
        memes={"curiosity": 1.0, "kindness": 1.0},
    ))
    partner = world.add(Entity(
        id="Partner",
        kind="character",
        type=params.partner,
        label=f"the {params.partner}",
        meters={"patience": 1.0},
        memes={"kindness": 1.0},
    ))
    racket = world.add(Entity(
        id="racket",
        type="racket",
        label="racket",
        phrase="a light blue racket",
        owner=hero.id,
    ))
    scorecard = world.add(Entity(
        id="scorecard",
        type="scorecard",
        label="scorecard",
        phrase="a small scorecard with bright squares",
        caretaker=partner.id,
    ))
    birdie = world.add(Entity(
        id="birdie",
        type="birdie",
        label="shuttlecock",
        phrase="a white shuttlecock",
        owner=None,
    ))
    problem = world.add(Entity(
        id=params.problem,
        type=params.problem,
        label=_safe_lookup(PROBLEMS, params.problem)["label"],
        phrase=_safe_lookup(PROBLEMS, params.problem)["phrase"],
        meters={"blocking": 1.0},
    ))

    world.facts.update(hero=hero, partner=partner, racket=racket, scorecard=scorecard, birdie=birdie, problem=problem)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    partner: Entity = _safe_fact(world, world.facts, "partner")  # type: ignore[assignment]
    problem: Entity = _safe_fact(world, world.facts, "problem")  # type: ignore[assignment]

    activity = _safe_lookup(ACTIVITIES, params.activity)
    action = _safe_lookup(ACTIONS, params.action)
    problem_cfg = _safe_lookup(PROBLEMS, params.problem)

    world.say(f"{hero.id} was a {params.trait} child who loved {activity['verb']} and noticed little details everywhere.")
    world.say(f"One afternoon, {hero.id} and {partner.label} went to {world.setting.label}. {world.setting.detail}")
    world.say(f"{hero.id} brought a {world.facts['racket'].phrase} and a {world.facts['scorecard'].phrase} to {action['verb']}.")
    world.say(f"{hero.id} even wanted to {activity['verb']} while keeping a careful {action['noun']} of every good hit.")

    # Curiosity reveals the obstacle.
    world.say(f"Then {hero.id} looked up and saw {problem_cfg['phrase']} {problem_cfg['place']}.")
    world.say(f"{problem_cfg['risk'].capitalize()}. That made the game feel stuck, even before the first serve.")

    # Kindness and adventure turn.
    hero.meters["curiosity"] += 1
    hero.memes["kindness"] += 1
    partner.memes["kindness"] += 1
    world.say(f"{hero.id}'s curiosity said to look closely instead of giving up.")
    world.say(f"{hero.id}'s kindness said to help first, so the game could be fun for both of them.")

    if params.action == "remove":
        problem.meters["blocking"] = 0.0
        world.say(f"Together they moved to {action['verb']} {problem_cfg['label']}.")
        world.say(f"They worked gently, and soon the path was clear.")
        world.say(f"After that, {hero.id} could keep {activity['gerund']} while {partner.label} helped {hero.id} {action['effect']}.")
    else:
        world.say(f"They chose to {action['verb']} the points anyway, but the story wants a kinder turn than that.")

    # Tallying and resolution image.
    hero.meters["joy"] += 1
    world.say(f"They began to {action['verb']}, and {hero.id} would {action['verb']} with a bright finger after each clean hit.")
    world.say(f"{hero.id} made a neat {action['noun']} beside the scorecard, and every point felt like a small adventure.")
    world.say(f"By the end, the shuttlecock sailed cleanly, the obstacle was gone, and {hero.id} smiled at the tidy little court.")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    hero: Entity = p["hero"]  # type: ignore[assignment]
    activity = ACTIVITIES["badminton"]
    return [
        f'Write a short adventure story for a child named {hero.id} who wants to play {activity["keyword"]} and keep a {ACTIONS["tally"]["noun"]} of the points.',
        f"Tell a gentle story where curiosity helps {hero.id} notice a problem and kindness helps {hero.id} {ACTIONS['remove']['verb']} before the game begins.",
        f'Write a simple badminton adventure that includes the words "{ACTIONS["tally"]["noun"]}", "{ACTIONS["remove"]["noun"]}", and "{activity["keyword"]}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    partner: Entity = _safe_fact(world, world.facts, "partner")  # type: ignore[assignment]
    problem: Entity = _safe_fact(world, world.facts, "problem")  # type: ignore[assignment]
    place = world.setting.label

    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to play badminton and tally the points on a little scorecard."
        ),
        QAItem(
            question=f"What problem did {hero.id} notice before the game could start?",
            answer=f"{hero.id} noticed {problem.phrase} near the court, and it could have spoiled the game."
        ),
        QAItem(
            question=f"How did kindness help {hero.id} and {partner.label}?",
            answer=f"Kindness helped them remove the obstacle together so they could play safely and happily."
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The shuttlecock flew cleanly, the obstacle was gone, and {hero.id} smiled beside the tidy little court."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is badminton?",
            answer="Badminton is a sport where players hit a shuttlecock over a net with rackets."
        ),
        QAItem(
            question="What does tally mean?",
            answer="To tally means to count and keep track of numbers or points."
        ),
        QAItem(
            question="What does remove mean?",
            answer="To remove means to take something away or move it out of the way."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to other people."
        ),
    ]
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return world.trace()


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def valid_gender_for_name(gender: str) -> str:
    return gender if gender in {"girl", "boy", "friend"} else "friend"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    activity = getattr(args, "activity", None) or "badminton"
    action = getattr(args, "action", None) or select_action()
    problem = getattr(args, "problem", None) or select_problem(rng)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy", "friend"])
    if activity != "badminton" or action not in ACTIONS or problem not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if (place, activity, action, problem) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or choose_name(valid_gender_for_name(gender), rng)
    partner = getattr(args, "partner", None) or rng.choice(["mother", "father", "friend"])
    trait = getattr(args, "trait", None) or select_trait(rng)
    return StoryParams(place=place, activity=activity, action=action, problem=problem, name=name, partner=partner, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a curious badminton adventure with tallying, removal, and kindness.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--gender", choices=["girl", "boy", "friend"])
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=["mother", "father", "friend"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
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


CURATED = [
    StoryParams(place="court", activity="badminton", action="tally", problem="tape", name="Mia", partner="mother", gender="girl", trait="curious"),
    StoryParams(place="yard", activity="badminton", action="remove", problem="branch", name="Leo", partner="father", gender="boy", trait="kind"),
    StoryParams(place="gym", activity="badminton", action="remove", problem="tape", name="Pip", partner="friend", gender="friend", trait="brave"),
]


def asp_program_with_show(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_with_show("#show valid/4.\n#show kind_turn/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        turns = asp_kind_turns()
        print(f"{len(triples)} compatible combos, {len(turns)} kind turns\n")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.action} / {p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
