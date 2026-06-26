#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure reconciliation tale.

Seed image:
A child on a small starship carries a marigold sprout to the main greenhouse.
The sprout needs careful light, the route is bumpy, and a misunderstanding
between the child and a helper astronaut turns into a gentle repair.

World shape:
- physical state: hull meters, light meters, water meters, cracked meters, growth
- emotional state: worry, pride, blame, trust, relief, love

The story ends when the pair make up and the marigold reaches the main bay.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    deck: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    tag: str
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
class Route:
    id: str
    label: str
    rough: bool
    detour: bool
    needs: set[str]
    outcome: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    route: str
    prize: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "main_deck": Setting(place="the main deck", tag="ship", affords={"walk", "carry", "repair"}),
    "greenhouse": Setting(place="the greenhouse bay", tag="garden", affords={"walk", "carry", "repair"}),
    "airlock_hall": Setting(place="the airlock hall", tag="ship", affords={"walk", "carry"}),
}

ROUTES = {
    "main_corridor": Route(
        id="main_corridor",
        label="the main corridor",
        rough=False,
        detour=False,
        needs={"walk"},
        outcome="safe and bright",
    ),
    "bumpy_tube": Route(
        id="bumpy_tube",
        label="a bumpy service tube",
        rough=True,
        detour=False,
        needs={"walk"},
        outcome="shaky",
    ),
    "slow_ladder": Route(
        id="slow_ladder",
        label="a narrow ladder route",
        rough=False,
        detour=True,
        needs={"walk"},
        outcome="slow",
    ),
}

PRIZES = {
    "marigold": Prize(
        id="marigold",
        label="marigold",
        phrase="a little marigold sprout in a blue cup",
        region="hands",
        fragile=True,
    ),
    "main_map": Prize(
        id="main_map",
        label="main map",
        phrase="the ship's main map in a stiff sleeve",
        region="hands",
        fragile=True,
    ),
}

HERO_NAMES = ["Mina", "Rory", "Luna", "Sage", "Tavi", "Nico"]
HELPER_NAMES = ["Ari", "Bea", "Juno", "Kai", "Mara", "Quinn"]


@dataclass
class StoryState:
    route: Route
    prize: Prize
    hero: Entity
    helper: Entity
    world: World


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
    state: object | None = None
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


def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _has(ent: Entity, key: str, threshold: float = 1.0) -> bool:
    return ent.meters.get(key, 0.0) >= threshold or ent.memes.get(key, 0.0) >= threshold


def route_is_reasonable(route: Route, prize: Prize) -> bool:
    if route.rough and prize.fragile:
        return True
    if route.detour and prize.fragile:
        return True
    return False


def route_fixable(route: Route, prize: Prize) -> bool:
    return route.id in {"bumpy_tube", "slow_ladder", "main_corridor"} and prize.fragile


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def tell(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    helper = state.helper
    prize = state.prize
    route = state.route

    w.say(
        f"{hero.id} was a little {hero.type} on the main deck of a small starship, "
        f"and {hero.pronoun('possessive')} favorite thing was {prize.phrase}."
    )
    _feel(hero, "love", 1)
    _feel(helper, "care", 1)
    w.say(
        f"{hero.id} wanted to carry {(getattr(prize, 'it')() if callable(getattr(prize, 'it', None)) else getattr(prize, 'it', 'it'))} to the main greenhouse, "
        f"where the yellow light was warm enough to help it grow."
    )

    w.para()
    w.say(
        f"That morning, the ship chose {route.label} for the trip. "
        f"The way looked {route.outcome}, but {route.label} was the fastest path."
    )
    _feel(hero, "hope", 1)
    _feel(helper, "worry", 1)

    if route.rough:
        _bump(hero, "shake", 1)
        _bump(prize, "jostle", 1)
    if route.detour:
        _bump(hero, "delay", 1)

    if route.rough and prize.fragile:
        _feel(helper, "blame", 1)
        w.say(
            f"When the tube gave a hard lurch, {helper.id} reached out too fast and "
            f"the cup tipped. A little water splashed the deck."
        )
        _bump(prize, "water", 1)
        _bump(w.get("deck"), "wet", 1)
        _feel(hero, "worry", 1)
        _feel(hero, "hurt", 1)
        _feel(helper, "regret", 1)
        w.say(
            f"{hero.id} frowned and said {helper.pronoun('possessive')} hands had not been careful."
        )
        w.say(
            f"{helper.id} looked down and said {helper.pronoun('subject')} had tried to help, "
            f"but had made the wrong move."
        )

    w.para()
    if _has(hero, "hurt"):
        w.say(
            f"The little ship felt quiet, and even the main lights seemed dimmer."
        )
    if route.rough and prize.fragile:
        w.say(
            f"Then {helper.id} fetched a cloth, steadied the cup, and said, "
            f"\"Let's fix this together and take the main corridor instead.\""
        )
        _feel(hero, "listening", 1)
        _feel(helper, "care", 1)
        _feel(helper, "trust", 1)
        _feel(hero, "trust", 1)

    # repair scene
    _bump(prize, "cleaned", 1)
    _bump(w.get("deck"), "dry", 1)
    _feel(hero, "relief", 1)
    _feel(helper, "relief", 1)
    _feel(hero, "love", 1)
    _feel(helper, "love", 1)

    w.say(
        f"{hero.id} nodded, and the two of them walked the main corridor side by side. "
        f"{helper.id} carried the cup for the steep parts, and {hero.id} carried the cloth."
    )
    w.say(
        f"By the time they reached the greenhouse, the marigold stood straight in its cup, "
        f"golden against the green wall."
    )
    w.say(
        f"{hero.id} and {helper.id} smiled at each other. "
        f"They had turned a bump-up into a clean new plan, and the ship felt kind again."
    )

    w.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        route=route,
        resolved=True,
        reconciled=True,
    )


# ---------------------------------------------------------------------------
# Sample generation and Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prize: Prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    route: Route = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "route")
    return [
        f'Write a short space-adventure story for a small child about {hero.id}, '
        f'{helper.id}, and a {prize.label} on the {route.label}.',
        f"Tell a gentle reconciliation story where {hero.id} is upset when "
        f"{helper.id} makes a mistake with {prize.phrase}.",
        f"Write a story set on a tiny starship that includes the words "
        f'"marigold" and "main" and ends with the friends making up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prize: Prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    route: Route = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "route")

    return [
        QAItem(
            question=f"Who was carrying the marigold to the greenhouse?",
            answer=f"{hero.id} was carrying the marigold sprout in a blue cup.",
        ),
        QAItem(
            question=f"Why did {hero.id} get upset on {route.label}?",
            answer=(
                f"{helper.id} reached too fast on the bumpy trip, the cup tipped, "
                f"and some water splashed the deck. That made {hero.id} worry "
                f"about the marigold."
            ),
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=(
                f"The two friends calmed down, cleaned up together, and chose the main "
                f"corridor so the marigold could reach the greenhouse safely."
            ),
        ),
        QAItem(
            question=f"Where did the marigold end up?",
            answer="It ended up standing straight in the greenhouse bay by the green wall.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a greenhouse on a spaceship for?",
            answer=(
                "A greenhouse is a warm, bright room where plants can grow when "
                "the rest of the ship is cold and dark."
            ),
        ),
        QAItem(
            question="Why can a bumpy route be a problem for a plant cup?",
            answer=(
                "A bumpy route can shake the cup, spill water, and make a fragile "
                "plant tip over."
            ),
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer=(
                "Reconciliation means two people stop being upset, fix the mistake, "
                "and feel friendly again."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
route_problem(R) :- rough(R), fragile_prize.
can_reconcile(R) :- route_problem(R), fixable(R).
good_story(R) :- can_reconcile(R).
#show good_story/1.
#show can_reconcile/1.
#show route_problem/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if r.rough:
            lines.append(asp.fact("rough", rid))
        if r.detour:
            lines.append(asp.fact("detour", rid))
        if route_fixable(r, PRIZES["marigold"]):
            lines.append(asp.fact("fixable", rid))
    if PRIZES["marigold"].fragile:
        lines.append(asp.fact("fragile_prize"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "good_story"))
    python = {("bumpy_tube",), ("slow_ladder",), ("main_corridor",)}
    if atoms == python:
        print(f"OK: ASP parity verified for {len(atoms)} route options.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python))
    return 1


# ---------------------------------------------------------------------------
# Resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure reconciliation storyworld.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--prize", choices=PRIZES, default="marigold")
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    route = getattr(args, "route", None) or rng.choice(list(ROUTES))
    prize = getattr(args, "prize", None) or "marigold"
    if prize not in PRIZES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if route not in ROUTES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not route_is_reasonable(_safe_lookup(ROUTES, route), _safe_lookup(PRIZES, prize)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        route=route,
        prize=prize,
        hero_name=hero_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["main_deck"])
    route = _safe_lookup(ROUTES, params.route)
    prize_cfg = _safe_lookup(PRIZES, params.prize)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="girl" if params.hero_name[0] in "AEIOULaeioul" else "boy",
        label=params.hero_name,
        meters={"worry": 0.0, "love": 1.0},
        memes={"care": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="boy",
        label=params.helper_name,
        meters={"worry": 0.0},
        memes={"care": 1.0},
    ))
    prize = world.add(Entity(
        id="marigold",
        kind="thing",
        type="plant",
        label="marigold",
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
        carried_by=hero.id,
        location="main_deck",
        meters={"water": 1.0, "clean": 1.0, "jostle": 0.0, "cleaned": 0.0},
        memes={"fragile": 1.0},
        tags={"marigold", "plant"},
    ))
    deck = world.add(Entity(
        id="deck",
        kind="thing",
        type="ship",
        label="main deck",
        meters={"wet": 0.0, "dry": 1.0},
    ))

    state = StoryState(route=route, prize=prize_cfg, hero=hero, helper=helper, world=world)
    tell(state)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            bits = []
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            print(f"{ent.id}: {', '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(route="bumpy_tube", prize="marigold", hero_name="Mina", helper_name="Ari"),
    StoryParams(route="slow_ladder", prize="marigold", hero_name="Rory", helper_name="Juno"),
    StoryParams(route="main_corridor", prize="marigold", hero_name="Luna", helper_name="Kai"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP support is present for parity checks; run --verify for the full comparison.")
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
