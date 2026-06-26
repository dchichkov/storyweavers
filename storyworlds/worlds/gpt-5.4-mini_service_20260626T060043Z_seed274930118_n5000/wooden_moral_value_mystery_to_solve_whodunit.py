#!/usr/bin/env python3
"""
storyworlds/worlds/wooden_moral_value_mystery_to_solve_whodunit.py
===================================================================

A small whodunit-style story world built from the seed word "wooden".

Premise:
- A child finds a wooden clue connected to a missing everyday item.
- The mystery can be solved only by careful noticing, honest sharing,
  and a fair choice that helps someone else.

The world supports a few constraint-checked variations with different clues,
settings, and moral values, while keeping the stories concrete and child-facing.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    hidden_in: Optional[str] = None
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    indoor: bool
    hiding_spots: list[str]
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
    label: str
    phrase: str
    material: str
    hiding_spot: str
    points_to: str
    clue_text: str
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
class Mystery:
    missing_item: str
    missing_phrase: str
    missing_owner: str
    motive: str
    solution_method: str
    moral_value: str
    value_tension: str
    resolution_value: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, hiding_spots=["trunk", "box", "beam"]),
    "shed": Setting(place="the garden shed", indoor=True, hiding_spots=["shelf", "crate", "corner"]),
    "library": Setting(place="the tiny library", indoor=True, hiding_spots=["desk", "cart", "globe stand"]),
    "market": Setting(place="the market alley", indoor=False, hiding_spots=["stall", "basket", "cart"]),
}

VALUES = {
    "honesty": {
        "moral_value": "honesty",
        "value_tension": "telling the truth even when it is awkward",
        "resolution_value": "honest words",
    },
    "fairness": {
        "moral_value": "fairness",
        "value_tension": "sharing what was found instead of keeping it",
        "resolution_value": "fair choices",
    },
    "kindness": {
        "moral_value": "kindness",
        "value_tension": "helping someone who is worried instead of teasing",
        "resolution_value": "kind help",
    },
}

CLUES = {
    "wooden_button": Clue(
        label="wooden button",
        phrase="a small wooden button",
        material="wooden",
        hiding_spot="box",
        points_to="wooden_toy",
        clue_text="It had one smooth side and one side marked with a tiny star.",
    ),
    "wooden_key": Clue(
        label="wooden key",
        phrase="a carved wooden key",
        material="wooden",
        hiding_spot="crate",
        points_to="wooden_box",
        clue_text="Its grooves matched a little latch on something nearby.",
    ),
    "wooden_spoon": Clue(
        label="wooden spoon",
        phrase="a wooden spoon",
        material="wooden",
        hiding_spot="basket",
        points_to="wooden_note",
        clue_text="It had a ribbon tied to the handle, like it was meant to be noticed.",
    ),
    "wooden_chip": Clue(
        label="wooden chip",
        phrase="a splintery wooden chip",
        material="wooden",
        hiding_spot="trunk",
        points_to="wooden_doll",
        clue_text="It smelled like fresh carving and pointed to a secret hiding place.",
    ),
}

MYSTERIES = {
    "toy": Mystery(
        missing_item="little red wagon",
        missing_phrase="a little red wagon",
        missing_owner="the baker",
        motive="the wagon had been borrowed without asking",
        solution_method="follow the clue and ask the right person kindly",
        moral_value="honesty",
        value_tension="someone wanted to hide what they had done",
        resolution_value="telling the truth",
    ),
    "book": Mystery(
        missing_item="green storybook",
        missing_phrase="a green storybook",
        missing_owner="the teacher",
        motive="the book had been taken to keep it safe from rain",
        solution_method="notice the clue and return it fairly",
        moral_value="fairness",
        value_tension="someone wanted to keep a shared thing",
        resolution_value="sharing what belongs to others",
    ),
    "feather": Mystery(
        missing_item="blue feather charm",
        missing_phrase="a blue feather charm",
        missing_owner="the milliner",
        motive="the charm had been tucked away after it fell off a hat",
        solution_method="listen carefully and help the worried owner",
        moral_value="kindness",
        value_tension="someone was afraid of making a mistake",
        resolution_value="gentle help",
    ),
}

HERO_NAMES = ["Nina", "Owen", "Mila", "Arlo", "Tess", "Mara", "Eli", "June"]
SIDEKICKS = ["grandpa", "mother", "father", "aunt"]
TRAITS = ["curious", "careful", "quiet", "brave", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    clue: str
    mystery: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue_id, clue in CLUES.items():
            for mystery_id, mystery in MYSTERIES.items():
                if clue.material == "wooden" and mystery.moral_value in VALUES:
                    if clue.points_to.startswith("wooden_"):
                        combos.append((setting, clue_id, mystery_id))
    return combos


def explain_rejection(setting: str, clue_id: str, mystery_id: str) -> str:
    clue = _safe_lookup(CLUES, clue_id)
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    return (
        f"(No story: the wooden clue '{clue.label}' does not make a clear whodunit "
        f"for the {mystery.moral_value} mystery in {setting}. Choose a clue that can "
        f"point to a believable hidden object.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    clue = _safe_lookup(CLUES, params.clue)
    mystery = _safe_lookup(MYSTERIES, params.mystery)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    missing = world.add(Entity(
        id="Missing",
        kind="thing",
        type=mystery.missing_item.replace(" ", "_"),
        label=mystery.missing_item,
        phrase=mystery.missing_phrase,
        owner=mystery.missing_owner,
        hidden_in=clue.hiding_spot,
        material="ordinary",
    ))
    clue_ent = world.add(Entity(
        id="Clue",
        kind="thing",
        type=clue.label.replace(" ", "_"),
        label=clue.label,
        phrase=clue.phrase,
        material=clue.material,
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        clue=clue_ent,
        clue_cfg=clue,
        mystery_cfg=mystery,
        value=_safe_lookup(VALUES, mystery.moral_value),
        setting=setting,
    )
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    missing: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing")
    clue_cfg: Clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue_cfg")
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery_cfg")
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "value")
    place = world.setting.place

    world.say(
        f"{hero.id} went to {place} with {helper.label} and noticed that something felt off."
    )
    world.say(
        f"Someone at {place} was missing {missing.phrase}, and nobody could find it."
    )
    world.say(
        f"Then {hero.id} spotted {clue_cfg.phrase}, a {clue_cfg.material} clue with a strange little sign on it. "
        f"{clue_cfg.clue_text}"
    )

    world.para()
    world.say(
        f"{hero.id} looked under the likely hiding spots one by one, while {helper.label} waited and watched."
    )
    world.say(
        f"The clue led toward {clue_cfg.hiding_spot}, which made the mystery feel close enough to touch."
    )

    world.para()
    if mystery.moral_value == "honesty":
        world.say(
            f"At last, {hero.id} found the missing item and learned that {mystery.motive}. "
            f"Instead of hiding it, {hero.id} told the truth."
        )
    elif mystery.moral_value == "fairness":
        world.say(
            f"At last, {hero.id} found the missing item and learned that {mystery.motive}. "
            f"Then {hero.id} gave it back so everyone could be treated fairly."
        )
    else:
        world.say(
            f"At last, {hero.id} found the missing item and learned that {mystery.motive}. "
            f"Then {hero.id} helped gently, so nobody felt ashamed or alone."
        )

    world.say(
        f"The mystery was solved when {hero.id} chose {value['resolution_value']} over {value['value_tension']}."
    )
    world.say(
        f"By the end, {missing.label} was safe again, and the wooden clue had done its job."
    )
    world.facts["solved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery_cfg")
    clue_cfg: Clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue_cfg")
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    return [
        f"Write a short whodunit for children that includes a wooden clue and a moral choice about {mystery.moral_value}.",
        f"Tell a gentle mystery where {hero.id} follows a {clue_cfg.material} clue and solves a small problem by choosing {mystery.resolution_value}.",
        f"Create a simple detective story in which a wooden object helps reveal who hid {mystery.missing_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    missing: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing")
    clue_cfg: Clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue_cfg")
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery_cfg")
    value = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "value")
    place = world.setting.place

    return [
        QAItem(
            question=f"Who solved the mystery at {place}?",
            answer=f"{hero.id} solved it with help from {helper.label}.",
        ),
        QAItem(
            question=f"What wooden clue did {hero.id} find?",
            answer=f"{hero.id} found {clue_cfg.phrase}, which was a wooden clue.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was {missing.phrase}.",
        ),
        QAItem(
            question=f"What moral value mattered in this story?",
            answer=f"The important moral value was {value['moral_value']}.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved when {hero.id} followed the clue and chose {mystery.resolution_method}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue_cfg: Clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue_cfg")
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery_cfg")
    out = [
        QAItem(
            question="What is wooden?",
            answer="Wooden means made from wood, like a chair, a spoon, or a carved toy.",
        )
    ]
    if clue_cfg.material == "wooden":
        out.append(
            QAItem(
                question="Why can a wooden clue matter in a mystery?",
                answer="A wooden clue can matter because its shape, marks, or place can point to what happened.",
            )
        )
    if mystery.moral_value == "honesty":
        out.append(
            QAItem(
                question="What does honesty mean?",
                answer="Honesty means telling the truth and not hiding what really happened.",
            )
        )
    elif mystery.moral_value == "fairness":
        out.append(
            QAItem(
                question="What does fairness mean?",
                answer="Fairness means treating people equally and not keeping something that should be shared or returned.",
            )
        )
    else:
        out.append(
            QAItem(
                question="What does kindness mean?",
                answer="Kindness means helping with care and being gentle with someone else's feelings.",
            )
        )
    return out


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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.material:
            bits.append(f"material={e.material}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S).
wooden_clue(C) :- clue(C), material(C, wooden).
moral_value(M) :- value(M).

valid_story(Setting, Clue, Mystery) :-
    setting(Setting),
    wooden_clue(Clue),
    clue_points_to(Clue, _),
    mystery(Mystery),
    mystery_value(Mystery, _).

solves(Clue, Mystery) :-
    clue_points_to(Clue, _),
    mystery(Mystery).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("material", cid, clue.material))
        lines.append(asp.fact("clue_points_to", cid, clue.points_to))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_value", mid, mystery.moral_value))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small wooden whodunit story world with a moral choice."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=SIDEKICKS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "clue", None) and getattr(args, "mystery", None):
        if (getattr(args, "place", None) or next(iter(SETTINGS))) not in SETTINGS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, mystery = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(SIDEKICKS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, mystery=mystery, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    narrate(world)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, mystery) combos:\n")
        for s, c, m in combos:
            print(f"  {s:10} {c:14} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting, clue, mystery in sorted(valid_combos()):
            params = StoryParams(
                setting=setting,
                clue=clue,
                mystery=mystery,
                name=random.choice(HERO_NAMES),
                helper=random.choice(SIDEKICKS),
                trait=random.choice(TRAITS),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
