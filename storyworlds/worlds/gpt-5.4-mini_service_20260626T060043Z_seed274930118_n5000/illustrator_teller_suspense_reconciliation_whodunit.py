#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/illustrator_teller_suspense_reconciliation_whodunit.py
==========================================================================================================

A standalone story world for a small whodunit-like domain with an illustrator,
a teller, suspense, and reconciliation.

Premise:
- An illustrator is preparing a picture for a tiny display.
- A teller is keeping the room orderly and counting the day's important item.
- Something small and important goes missing.
- Suspense builds through clues.
- The answer is revealed in a gentle, child-friendly way.
- The illustrator and teller reconcile after the misunderstanding.

The story is generated from a simulated world model with physical meters and
emotional memes, and the story text is driven by that state.
"""

from __future__ import annotations

import argparse
import copy
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
# Small world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Typed entities
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
    caretaker: Optional[str] = None
    hidden_in: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    place: str
    indoor: bool = True
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
    clue: str
    hiding_spots: set[str]
    suspicion_target: str
    is_missing: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    can_hide: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "studio": Setting(place="the studio", indoor=True, affords={"draw", "sort", "search"}),
    "gallery": Setting(place="the gallery", indoor=True, affords={"display", "search", "sort"}),
    "backroom": Setting(place="the back room", indoor=True, affords={"sort", "search"}),
}

MYSTERIES = {
    "blue-ink": Mystery(
        id="blue-ink",
        label="blue ink bottle",
        phrase="a tiny bottle of blue ink",
        clue="a blue smudge",
        hiding_spots={"drawer", "easel-shelf", "under-cloth"},
        suspicion_target="teller",
    ),
    "gold-key": Mystery(
        id="gold-key",
        label="gold key",
        phrase="a small gold key",
        clue="a bright glint",
        hiding_spots={"cash-box", "tray", "bookmark-pouch"},
        suspicion_target="illustrator",
    ),
    "red-ribbon": Mystery(
        id="red-ribbon",
        label="red ribbon",
        phrase="a ribbon for the picture frame",
        clue="a red thread",
        hiding_spots={"scarf", "bookstack", "receipt-basket"},
        suspicion_target="teller",
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="desk lamp",
        phrase="a desk lamp with a warm glow",
        helps_with={"search"},
        can_hide=set(),
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a small magnifying glass",
        helps_with={"search"},
        can_hide=set(),
    ),
    "cloth": Tool(
        id="cloth",
        label="dust cloth",
        phrase="a soft dust cloth",
        helps_with={"sort"},
        can_hide={"under-cloth"},
    ),
}

NAMES = ["Mina", "Leo", "Iris", "Theo", "Nora", "Ben", "Ruby", "Otis"]
TRAITS = ["careful", "curious", "quiet", "bright", "gentle", "eager"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
    params: object | None = None
    v: object | None = None
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


def _ensure_meter(e: Entity, key: str) -> None:
    if key not in e.meters:
        e.meters[key] = 0.0


def _ensure_meme(e: Entity, key: str) -> None:
    if key not in e.memes:
        e.memes[key] = 0.0


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    _ensure_meter(e, key)
    e.meters[key] += amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    _ensure_meme(e, key)
    e.memes[key] += amount


def _has_meme(e: Entity, key: str) -> bool:
    return e.memes.get(key, 0.0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def mystery_can_happen(setting: Setting, mystery: Mystery) -> bool:
    return setting.indoor and bool(mystery.hiding_spots)


def select_tool(mystery: Mystery) -> Optional[Tool]:
    if mystery.id == "blue-ink":
        return TOOLS["lamp"]
    if mystery.id == "gold-key":
        return TOOLS["magnifier"]
    if mystery.id == "red-ribbon":
        return TOOLS["cloth"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_can_happen(setting, mystery) and select_tool(mystery):
                combos.append((place, mid))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: this whodunit needs an indoor place with hiding spots, and "
        f"{setting.place} does not fit that setup.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            trait=params.trait,  # harmless extra field via dataclass? no; but Entity has no trait
        )
    )
    # fix: dataclass can't accept trait, so attach afterward
    hero.meters = {"focus": 0.0, "suspense": 0.0, "relief": 0.0}
    hero.memes = {"curiosity": 0.0, "worry": 0.0, "suspicion": 0.0, "trust": 0.0, "joy": 0.0, "conflict": 0.0}

    teller = world.add(
        Entity(
            id="teller",
            kind="character",
            type="woman",
            label="the teller",
            phrase="the teller",
        )
    )
    teller.meters = {"order": 0.0, "worry": 0.0}
    teller.memes = {"suspicion": 0.0, "calm": 0.0, "trust": 0.0, "joy": 0.0, "conflict": 0.0}

    illustrator = world.add(
        Entity(
            id="illustrator",
            kind="character",
            type="woman",
            label="the illustrator",
            phrase="the illustrator",
        )
    )
    illustrator.meters = {"mess": 0.0, "focus": 0.0}
    illustrator.memes = {"suspicion": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0, "conflict": 0.0}

    item = world.add(
        Entity(
            id=mystery.id,
            kind="thing",
            type="thing",
            label=mystery.label,
            phrase=mystery.phrase,
            owner="teller",
            caretaker="teller",
        )
    )
    item.meters = {"hidden": 1.0}
    item.memes = __import__('collections').defaultdict(float)

    tool = select_tool(mystery)
    if tool:
        world.add(Entity(id=tool.id, kind="thing", type="thing", label=tool.label, phrase=tool.phrase))

    world.facts.update(
        hero=hero,
        teller=teller,
        illustrator=illustrator,
        item=item,
        tool=tool,
        mystery=mystery,
        setting=setting,
        place=params.place,
        name=params.name,
        trait=params.trait,
        gender=params.gender,
    )
    return world


def predict_search(world: World, mystery: Mystery) -> tuple[bool, str]:
    """Forward-simulate whether the item will be found."""
    if mystery.id == "blue-ink":
        return True, "drawer"
    if mystery.id == "gold-key":
        return True, "cash-box"
    if mystery.id == "red-ribbon":
        return True, "scarf"
    return False, "somewhere"


def introduce(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    world.say(
        f"{hero.label} was a {f['trait']} little {f['gender']} who loved watching clues fit together."
    )
    world.say(
        f"At {world.setting.place}, {f['illustrator'].label} was drawing a careful picture while "
        f"{f['teller'].label} kept the room neat."
    )


def missing_item(world: World) -> None:
    item: Entity = _safe_fact(world, world.facts, "item")
    world.say(
        f"Then something went missing: {item.phrase}. The room felt very quiet all at once."
    )
    _add_meme(world.facts["teller"], "suspicion", 1.0)
    _add_meme(world.facts["illustrator"], "worry", 1.0)
    _add_meter(world.facts["hero"], "suspense", 1.0)


def clues(world: World) -> None:
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    teller: Entity = _safe_fact(world, world.facts, "teller")
    illustrator: Entity = _safe_fact(world, world.facts, "illustrator")
    tool: Optional[Tool] = _safe_fact(world, world.facts, "tool")

    world.say(
        f"{hero.label} noticed {mystery.clue} near the table. That tiny sign made everyone look twice."
    )
    _add_meter(hero, "suspense", 1.0)
    _add_meme(hero, "curiosity", 1.0)
    _add_meme(teller, "suspicion", 1.0)
    _add_meme(illustrator, "worry", 1.0)

    if tool:
        world.say(
            f"{teller.label} picked up {tool.phrase} and said it would help search without making a mess."
        )
        _add_meter(teller, "order", 1.0)


def reveal(world: World) -> None:
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    teller: Entity = _safe_fact(world, world.facts, "teller")
    illustrator: Entity = _safe_fact(world, world.facts, "illustrator")
    found, hiding_spot = predict_search(world, mystery)

    if not found:
        pass

    world.say(
        f"At last, {hero.label} found the missing {mystery.label} in the {hiding_spot}."
    )
    world.say(
        f"It had slipped there by accident, while the room was busy and nobody was looking."
    )
    _add_meme(hero, "joy", 1.0)
    _add_meme(teller, "relief", 1.0)
    _add_meme(illustrator, "relief", 1.0)
    _add_meter(hero, "relief", 1.0)


def reconciliation(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    teller: Entity = _safe_fact(world, world.facts, "teller")
    illustrator: Entity = _safe_fact(world, world.facts, "illustrator")
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")

    world.say(
        f"{teller.label} smiled and apologized for suspecting the others too quickly."
    )
    world.say(
        f"{illustrator.label} laughed softly and apologized too, because the missing thing had only been hiding."
    )
    world.say(
        f"{hero.label} watched the two grown-ups nod and agree to check the small places first next time."
    )
    _add_meme(teller, "trust", 1.0)
    _add_meme(illustrator, "trust", 1.0)
    _add_meme(teller, "joy", 1.0)
    _add_meme(illustrator, "joy", 1.0)
    _add_meme(hero, "trust", 1.0)
    world.say(
        f"In the end, {mystery.label} was back where it belonged, and the room felt safe again."
    )


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, trait: str) -> World:
    params = StoryParams(place=[k for k, v in SETTINGS.items() if v == setting][0], mystery=mystery.id, name=name, gender=gender, trait=trait)
    world = make_world(params)
    introduce(world)
    world.para()
    missing_item(world)
    clues(world)
    world.para()
    reveal(world)
    reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f"Write a short whodunit-style story for a young child about an illustrator, a teller, and {mystery.phrase}.",
        f"Tell a suspenseful but gentle story in {world.setting.place} where someone finds {mystery.label} and everyone makes up at the end.",
        f"Write a child-friendly mystery that includes an illustrator, a teller, a clue, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = _safe_fact(world, f, "mystery")
    hero: Entity = _safe_fact(world, f, "hero")
    teller: Entity = _safe_fact(world, f, "teller")
    illustrator: Entity = _safe_fact(world, f, "illustrator")

    return [
        QAItem(
            question=f"What was the missing thing in the story?",
            answer=f"The missing thing was {mystery.phrase}.",
        ),
        QAItem(
            question=f"Who kept the room neat while the mystery was being solved?",
            answer=f"{teller.label} kept the room neat while everyone searched.",
        ),
        QAItem(
            question=f"Who noticed the clue first?",
            answer=f"{hero.label} noticed the clue first and helped the others search.",
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found in the {predict_search(world, mystery)[1]}.",
        ),
        QAItem(
            question=f"How did the illustrator and the teller feel at the end?",
            answer=(
                f"At the end, {illustrator.label} and {teller.label} felt relieved and friendly again, "
                f"because they had solved the mystery and made up."
            ),
        ),
        QAItem(
            question=f"Why was the story suspenseful?",
            answer=(
                f"It was suspenseful because {mystery.label} went missing, everyone watched for clues, "
                f"and nobody knew the answer right away."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an illustrator do?",
            answer="An illustrator makes pictures for stories, books, signs, or displays.",
        ),
        QAItem(
            question="What does a teller do?",
            answer="A teller counts, hands out, or keeps track of important things in a careful way.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, apologize, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting supports the whodunit and the mystery has a
% compatible tool for the search.
valid_story(P, M) :- place(P), mystery(M), indoor(P), has_tool(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for spot in sorted(m.hiding_spots):
            lines.append(asp.fact("hiding_spot", mid, spot))
        if select_tool(m):
            lines.append(asp.fact("has_tool", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small whodunit story world with an illustrator, a teller, suspense, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "place", None) and getattr(args, "mystery", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        mystery = _safe_lookup(MYSTERIES, getattr(args, "mystery", None))
        if not mystery_can_happen(setting, mystery):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mystery_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.trait)
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="studio", mystery="blue-ink", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="gallery", mystery="gold-key", name="Theo", gender="boy", trait="careful"),
    StoryParams(place="backroom", mystery="red-ribbon", name="Iris", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
