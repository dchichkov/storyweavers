#!/usr/bin/env python3
"""
storyworlds/worlds/tomorrow_might_moral_value_foreshadowing_fairy_tale.py
==========================================================================

A tiny fairy-tale storyworld about a child or a young townsfolk facing a moral
choice, with foreshadowing that makes the ending feel earned.

Premise:
- A hero finds or receives something precious.
- A small warning or omen hints that tomorrow might matter.
- A tempting choice creates tension around a moral value.
- A wise turn or brave act resolves the tale.

This world is intentionally small and constraint-checked so the generated story
stays in a classical fairy-tale shape rather than becoming a flat event log.
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
# Core meters / memes
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    kind: str
    omens: list[str] = field(default_factory=list)
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
class Promise:
    label: str
    phrase: str
    risk: str
    virtue: str
    omen: str
    should_share: bool = False
    should_tell_truth: bool = False
    should_help: bool = False
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
class Temptation:
    label: str
    phrase: str
    vice: str
    meter: str
    harm: str
    foil: str
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
class MoralPath:
    virtue: str
    lesson: str
    act: str
    closing: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "cottage": Setting(
        place="the little cottage at the edge of the wood",
        kind="cottage",
        omens=["the kettle sang before dawn", "the chimney smoke bent toward the east"],
    ),
    "market": Setting(
        place="the bright market square by the well",
        kind="market",
        omens=["the crows circled the bell tower", "the apples glowed like tiny suns"],
    ),
    "grove": Setting(
        place="the moonlit grove behind the village",
        kind="grove",
        omens=["the silver leaves shivered without any wind", "the brook whispered twice"],
    ),
}

PROMISES = {
    "bread": Promise(
        label="a loaf of sweet bread",
        phrase="a warm loaf of sweet bread wrapped in linen",
        risk="hunger",
        virtue="generosity",
        omen="the smell of fresh crust",
        should_share=True,
    ),
    "secret": Promise(
        label="a secret path",
        phrase="a whispered path through the brambles",
        risk="fear",
        virtue="honesty",
        omen="the old signpost pointing the wrong way",
        should_tell_truth=True,
    ),
    "lantern": Promise(
        label="a lantern",
        phrase="a little lantern with a steady gold flame",
        risk="darkness",
        virtue="courage",
        omen="the wick that smoked before it burned bright",
        should_help=True,
    ),
}

TEMPTATIONS = {
    "keep": Temptation(
        label="keeping it all",
        phrase="keeping the treasure all to herself",
        vice="greed",
        meter="greed",
        harm="someone else would go without",
        foil="sharing",
    ),
    "hide": Temptation(
        label="hiding the truth",
        phrase="hiding what she knew behind a quiet smile",
        vice="dishonesty",
        meter="dishonesty",
        harm="the wrong path would stay hidden",
        foil="telling",
    ),
    "flee": Temptation(
        label="running away",
        phrase="running away before the shadow reached her",
        vice="cowardice",
        meter="fear",
        harm="the lost thing would stay lost",
        foil="bravery",
    ),
}

MORAL_PATHS = {
    "generosity": MoralPath(
        virtue="generosity",
        lesson="a kind heart grows bigger when it is shared",
        act="shared the bread with the hungry child",
        closing="the last crumb was sweeter because it was given away",
    ),
    "honesty": MoralPath(
        virtue="honesty",
        lesson="the truth can feel small at first, but it lights the right road",
        act="told the old baker where the path really was",
        closing="the lantern of truth made the whole village safer",
    ),
    "courage": MoralPath(
        virtue="courage",
        lesson="brave hands can tremble and still do the right thing",
        act="walked back into the grove with the lantern held high",
        closing="the dark became only a shadow and the path became clear",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Alya", "Rosa", "Iris", "Nora", "Elin", "Sera"]
BOY_NAMES = ["Evan", "Robin", "Theo", "Milo", "Finn", "Nico", "Pax", "Oren"]
ROLES = ["girl", "boy"]
AUX_ROLES = ["mother", "father", "grandmother", "old baker", "little prince", "little shepherd"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    promise: str
    temptation: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def _say_omen(world: World, setting: Setting, promise: Promise) -> None:
    world.say(
        f"Long before the end of the day, {setting.place} held an omen: "
        f"{random.choice(setting.omens)}."
    )
    world.say(
        f"It was the sort of sign that made the village children whisper that "
        f"tomorrow might matter."
    )
    world.say(
        f"In the middle of that hush sat {promise.omen}, as if the world were "
        f"already hinting at a choice."
    )


def _introduce(world: World, hero: Entity, helper: Entity, promise: Promise, setting: Setting) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who lived near {setting.place} and "
        f"noticed every small sign."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {helper.label} and treasured {promise.phrase}."
    )


def _tempt(world: World, hero: Entity, promise: Promise, temptation: Temptation) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes[temptation.meter] = hero.memes.get(temptation.meter, 0.0) + 1
    world.say(
        f"When the chance came, {hero.id} felt pulled toward {temptation.phrase}; "
        f"it would be easy to choose {temptation.label}."
    )
    world.say(
        f"But the promise of {promise.label} made the choice feel heavier, "
        f"because {temptation.harm}."
    )


def _foreshadow(world: World, hero: Entity, promise: Promise, temptation: Temptation) -> None:
    if promise.should_share:
        world.say(
            f"Earlier, {hero.id} had seen a poor child staring at the bakery window, "
            f"which was a quiet foreshadowing of the hunger to come."
        )
    elif promise.should_tell_truth:
        world.say(
            f"Earlier, {hero.id} had noticed the old signpost leaning away from the "
            f"safe road, a small foreshadowing that someone might get lost."
        )
    else:
        world.say(
            f"Earlier, {hero.id} had watched the wick smoke and then settle, a tiny "
            f"foreshadowing that the dark would not stay kind."
        )


def _resolve(world: World, hero: Entity, helper: Entity, promise: Promise, path: MoralPath) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes[path.virtue] = hero.memes.get(path.virtue, 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    world.say(
        f"Then {hero.id} chose the better way: {path.act}. {path.lesson.capitalize()}."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, and by the time the moon rose, "
        f"{path.closing}."
    )


def tell(setting: Setting, promise: Promise, temptation: Temptation,
         hero_name: str, role: str, helper_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=role,
        label=hero_name,
    ))
    helper = world.add(Entity(
        id=helper_role.title().replace(" ", "_"),
        kind="character",
        type=helper_role,
        label=helper_role,
    ))
    hero.memes["wonder"] = 1.0
    helper.memes["care"] = 1.0

    _say_omen(world, setting, promise)
    world.para()
    _introduce(world, hero, helper, promise, setting)
    _foreshadow(world, hero, promise, temptation)
    world.para()
    _tempt(world, hero, promise, temptation)
    if promise.virtue == "generosity":
        world.say(
            f"Tomorrow, {hero.id} thought, {temptation.foil} would be harder to undo "
            f"than to prevent."
        )
    elif promise.virtue == "honesty":
        world.say(
            f"Tomorrow, the wrong path might still wait in the brush, unless someone "
            f"spoke up first."
        )
    else:
        world.say(
            f"Tomorrow might be dark, but brave light could still find the road."
        )
    world.para()
    _resolve(world, hero, helper, promise, _safe_lookup(MORAL_PATHS, promise.virtue))

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        promise=promise,
        temptation=temptation,
        path=_safe_lookup(MORAL_PATHS, promise.virtue),
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROMISES:
            for t in TEMPTATIONS:
                if _safe_lookup(PROMISES, p).virtue == _safe_lookup(TEMPTATIONS, t).foil or (
                    _safe_lookup(PROMISES, p).virtue == "generosity" and t == "keep"
                ) or (
                    _safe_lookup(PROMISES, p).virtue == "honesty" and t == "hide"
                ) or (
                    _safe_lookup(PROMISES, p).virtue == "courage" and t == "flee"
                ):
                    out.append((s, p, t))
    return out


def explain_rejection(promise: Promise, temptation: Temptation) -> str:
    return (
        f"(No story: {promise.label} and {temptation.label} do not make a fair moral "
        f"tale for this world.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(cottage;market;grove).

promise(bread;secret;lantern).
temptation(keep;hide;flee).

virtue(bread,generosity).
virtue(secret,honesty).
virtue(lantern,courage).

foil(keep,sharing).
foil(hide,telling).
foil(flee,bravery).

valid(S,P,T) :- setting(S), promise(P), temptation(T), virtue(P,V), foil(T,F), match(V,F).
match(generosity,sharing).
match(honesty,telling).
match(courage,bravery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROMISES:
        lines.append(asp.fact("promise", p))
        lines.append(asp.fact("virtue", p, _safe_lookup(PROMISES, p).virtue))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temptation", t))
        lines.append(asp.fact("foil", t, _safe_lookup(TEMPTATIONS, t).foil))
    lines.append(asp.fact("match", "generosity", "sharing"))
    lines.append(asp.fact("match", "honesty", "telling"))
    lines.append(asp.fact("match", "courage", "bravery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about {f["hero"].id} and a choice between {f["promise"].label} and {f["temptation"].label}.',
        f"Tell a story where tomorrow might matter, and a small omen leads {f['hero'].id} toward a moral choice.",
        f"Write a child-friendly fairy tale with foreshadowing, a tempting wrong choice, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    promise: Promise = _safe_fact(world, f, "promise")
    temptation: Temptation = _safe_fact(world, f, "temptation")
    path: MoralPath = _safe_fact(world, f, "path")
    return [
        QAItem(
            question=f"What did {hero.id} have to choose between in the story?",
            answer=(
                f"{hero.id} had to choose between {temptation.label} and the better path "
                f"of {path.virtue}, which matched the promise of {promise.label}."
            ),
        ),
        QAItem(
            question=f"Why was the story hinting that tomorrow might matter?",
            answer=(
                f"The story used foreshadowing: an omen at {world.setting.place} hinted that "
                f"a future problem could grow if {hero.id} chose poorly."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} at the end?",
            answer=f"{helper.label.capitalize()} helped {hero.id} see the kinder choice and finish the tale safely.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} show by the ending?",
            answer=(
                f"{hero.id} showed {path.virtue}, and the ending proved that "
                f"{path.lesson.lower()}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prom: Promise = _safe_fact(world, world.facts, "promise")
    temp: Temptation = _safe_fact(world, world.facts, "temptation")
    path: MoralPath = _safe_fact(world, world.facts, "path")
    return [
        QAItem(
            question="What is a moral value in a story?",
            answer=(
                "A moral value is a good way of acting, like generosity, honesty, or courage, "
                "that helps the characters choose well."
            ),
        ),
        QAItem(
            question="What is foreshadowing?",
            answer=(
                "Foreshadowing is a small hint early in a story that gives a clue about "
                "something important that may happen later."
            ),
        ),
        QAItem(
            question=f"What does {prom.label} mean in this fairy tale?",
            answer=f"{prom.label.capitalize()} is the important thing {world.facts['hero'].id} must use wisely.",
        ),
        QAItem(
            question=f"What does {temp.label} represent?",
            answer=f"{temp.label.capitalize()} represents the wrong choice that would cause trouble if the hero followed it.",
        ),
        QAItem(
            question=f"What lesson does {path.virtue} teach here?",
            answer=path.lesson.capitalize() + ".",
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


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about tomorrow, might, moral value, and foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--promise", choices=PROMISES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=AUX_ROLES)
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "promise", None) is None or c[1] == getattr(args, "promise", None))
              and (getattr(args, "temptation", None) is None or c[2] == getattr(args, "temptation", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, promise, temptation = rng.choice(list(combos))
    p = _safe_lookup(PROMISES, promise)
    t = _safe_lookup(TEMPTATIONS, temptation)
    if p.virtue != t.foil:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    role = getattr(args, "role", None) or rng.choice(ROLES)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if role == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(AUX_ROLES)
    return StoryParams(
        setting=setting,
        promise=promise,
        temptation=temptation,
        name=name,
        role=role,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(PROMISES, params.promise),
        _safe_lookup(TEMPTATIONS, params.temptation),
        params.name,
        params.role,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story triples:")
        for s, p, t in combos:
            print(f"  {s:8} {p:10} {t:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("cottage", "bread", "keep", "Mina", "girl", "mother"),
            StoryParams("market", "secret", "hide", "Theo", "boy", "grandmother"),
            StoryParams("grove", "lantern", "flee", "Lina", "girl", "old baker"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.promise} vs {p.temptation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
