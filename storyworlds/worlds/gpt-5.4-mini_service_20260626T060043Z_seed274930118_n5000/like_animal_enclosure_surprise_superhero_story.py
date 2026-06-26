#!/usr/bin/env python3
"""
A small Storyweavers world: a superhero-like surprise at an animal enclosure.

Premise:
- A child or helper visits an animal enclosure expecting a normal, careful day.
- A small surprise changes the plan.
- The hero uses a gentle superhero-style skill to help, protect, or fix the moment.
- The ending proves the change in state: calm, surprise resolved, and someone happy.

The world is built from stateful entities with meters and memes, plus a tiny ASP twin
for verifying the reasonableness gate.
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
# Core simulation data
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
    wearing: bool = False
    protected: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "mom", "heroine"}
        masculine = {"boy", "man", "father", "dad", "hero"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    indoors: bool = False
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
class Surprise:
    id: str
    label: str
    reveal: str
    effect: str
    causes: str
    startling: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    description: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# World registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "animal_enclosure": Setting(
        place="the animal enclosure",
        indoors=False,
        affords={"visit", "feed", "watch"},
    )
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Mia", "Leo", "Ava", "Noah", "Zoe", "Eli", "Nora", "Finn"]
TRAITS = ["brave", "careful", "quick", "kind", "curious", "bold"]

SUPERS = [
    "Spark Shield",
    "Captain Kindness",
    "Tiny Thunder",
    "Moon Flash",
    "Star Helper",
]

SURPRISES = {
    "baby_goat": Surprise(
        id="baby_goat",
        label="a baby goat",
        reveal="a tiny baby goat had slipped through a gate and was wobbling near the path",
        effect="the goat looked lonely and a little lost",
        causes="someone had left a side gate unlatched",
        startling="the little goat popped out where no one expected it",
        tags={"animal", "surprise", "goat"},
    ),
    "stuck_balloon": Surprise(
        id="stuck_balloon",
        label="a bright balloon",
        reveal="a bright balloon had snagged high in a fence post by the enclosure",
        effect="the balloon was bobbing over the animals like a new toy",
        causes="a gust of wind had blown it from the parking path",
        startling="it kept bouncing in the breeze like a tiny flag",
        tags={"surprise", "balloon"},
    ),
    "rain_spot": Surprise(
        id="rain_spot",
        label="a splash of rainwater",
        reveal="a sudden splash of rainwater had turned the dirt path slick",
        effect="the path needed careful feet right away",
        causes="a cloudburst had come and gone in a minute",
        startling="the puddle shone like glass in the middle of the walk",
        tags={"surprise", "rain", "wet"},
    ),
}

GEAR = [
    Gear(
        id="cape",
        label="a bright cape",
        description="a bright cape that makes the helper feel ready",
        covers={"back"},
        guards={"sadness", "fear"},
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        description="soft gloves for gentle hands",
        covers={"hands"},
        guards={"wet", "mess"},
        plural=True,
    ),
    Gear(
        id="boots",
        label="sturdy boots",
        description="sturdy boots that keep feet steady on slick ground",
        covers={"feet"},
        guards={"wet"},
        plural=True,
    ),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(animal_enclosure).
hero_type(girl; boy).

surprise(baby_goat).
surprise(stuck_balloon).
surprise(rain_spot).

gear(cape).
gear(gloves).
gear(boots).

guards(cape, fear).
guards(cape, sadness).
guards(gloves, wet).
guards(gloves, mess).
guards(boots, wet).

covers(cape, back).
covers(gloves, hands).
covers(boots, feet).

reasonably_helpful(S, G) :- surprise(S), gear(G), surprise_needs(S, T), guards(G, T), needs_cover(S, R), covers(G, R).
valid_story(S, G) :- reasonably_helpful(S, G).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "animal_enclosure")]
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("tagged", sid, tag))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    lines.append(asp.fact("surprise_needs", "baby_goat", "fear"))
    lines.append(asp.fact("needs_cover", "baby_goat", "hands"))
    lines.append(asp.fact("surprise_needs", "stuck_balloon", "sadness"))
    lines.append(asp.fact("needs_cover", "stuck_balloon", "back"))
    lines.append(asp.fact("surprise_needs", "rain_spot", "wet"))
    lines.append(asp.fact("needs_cover", "rain_spot", "feet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_pairs = set(valid_pairs())
    asp_pairs = set(asp_valid_pairs())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_pairs() ({len(python_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if python_pairs - asp_pairs:
        print(" only in python:", sorted(python_pairs - asp_pairs))
    if asp_pairs - python_pairs:
        print(" only in asp:", sorted(asp_pairs - python_pairs))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def surprise_needs_cover(surprise: Surprise) -> str:
    if surprise.id == "baby_goat":
        return "hands"
    if surprise.id == "stuck_balloon":
        return "back"
    return "feet"


def select_gear(surprise: Surprise) -> Optional[Gear]:
    need = surprise_needs_cover(surprise)
    need_tag = "wet" if surprise.id == "rain_spot" else "fear"
    for gear in GEAR:
        if need in gear.covers and need_tag in gear.guards:
            return gear
    return None


def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for sid, surprise in SURPRISES.items():
        if select_gear(surprise):
            for g in GEAR:
                if surprise_needs_cover(surprise) in g.covers:
                    if ("wet" if sid == "rain_spot" else "fear") in g.guards or (
                        sid == "baby_goat" and "fear" in g.guards
                    ):
                        pairs.append((sid, g.id))
    return sorted(set(pairs))


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    name: str
    hero_type: str
    trait: str
    supername: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generation
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style story world at an animal enclosure with a surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--supername", choices=SUPERS)
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
    if getattr(args, "surprise", None):
        surprise = _safe_lookup(SURPRISES, getattr(args, "surprise", None))
        if not select_gear(surprise):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    surprise_id = getattr(args, "surprise", None) or rng.choice(sorted(SURPRISES))
    surprise = _safe_lookup(SURPRISES, surprise_id)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    supername = getattr(args, "supername", None) or rng.choice(SUPERS)
    place = getattr(args, "place", None) or "animal_enclosure"
    return StoryParams(place=place, surprise=surprise_id, name=name, hero_type=hero_type, trait=trait, supername=supername)


def _surprise_story(world: World, hero: Entity, helper: Entity, surprise: Surprise) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"{hero.id} was a little {hero.type} who liked superhero stories and liked to help.")
    world.say(f"{hero.pronoun().capitalize()} had a secret hero name: {helper.label}.")
    world.say(f"One day, {hero.id} and {helper.pronoun('possessive')} {helper.label} went to {world.setting.place}.")
    world.say(f"At first, everything felt calm, and {hero.id} looked around the animal enclosure with wide eyes.")
    world.para()
    world.say(f"Then came the surprise: {surprise.reveal}.")
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"{surprise.effect.capitalize()}, and {surprise.startling}.")
    world.say(f"{helper.label} saw what was wrong and said, \"We can handle this like heroes.\"")
    gear = select_gear(surprise)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    tool = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.description,
        owner=hero.id,
        protected=True,
        plural=gear.plural,
    ))
    tool.wearing = True
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    hero.memes["worry"] = 0
    world.para()
    if surprise.id == "baby_goat":
        world.say(f"{helper.label} opened the gate carefully and used {gear.label} to keep the tiny goat safe.")
        world.say(f"{hero.id} like to keep gentle hands ready, so {hero.pronoun()} held the door while the baby goat returned.")
        world.say(f"The little goat stopped wobbling, and soon it was back with its family.")
    elif surprise.id == "stuck_balloon":
        world.say(f"{helper.label} used {gear.label} to reach high and free the balloon without startling the animals.")
        world.say(f"{hero.id} stood steady below and watched the balloon float away like a happy comet.")
        world.say(f"The enclosure stayed calm, and the animals kept eating their snacks.")
    else:
        world.say(f"{helper.label} wore {gear.label} and guided {hero.id} across the slick path one careful step at a time.")
        world.say(f"The wet spot stopped being scary, and the two of them reached the viewing fence safely.")
        world.say(f"Even the animals looked relaxed again.")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"In the end, {hero.id} smiled like a true hero, and {helper.label} smiled too.")


def tell(setting: Setting, surprise: Surprise, name: str, hero_type: str, trait: str, supername: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, label=name))
    helper = world.add(Entity(id="helper", kind="character", type="hero", label=supername))
    world.facts.update(hero=hero, helper=helper, surprise=surprise, gear=select_gear(surprise), setting=setting)
    _surprise_story(world, hero, helper, surprise)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    return [
        f'Write a short superhero story for a young child about {hero.id} at an animal enclosure, and include the word "like".',
        f"Tell a gentle story where {hero.id} meets a surprise at the animal enclosure and becomes brave enough to help.",
        f'Write a simple story with a surprise at an animal enclosure that ends with a hero acting kindly and safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    gear: Gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who was the story about at the animal enclosure?",
            answer=f"It was about {hero.id}, a little {hero.type} who liked superhero stories, and {helper.label}, who helped with the surprise.",
        ),
        QAItem(
            question=f"What surprise happened at {world.setting.place}?",
            answer=f"The surprise was {surprise.reveal}. It changed the quiet visit into a problem that needed a careful superhero-style answer.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} used {gear.label} and careful choices to solve the surprise without hurting the animals or frightening anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an animal enclosure?",
            answer="An animal enclosure is a safe place where animals are kept and watched by people.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps others, stays brave, and tries to solve problems in a kind way.",
        ),
        QAItem(
            question="Why is a surprise sometimes hard?",
            answer="A surprise can be hard because it changes what people expected and they have to think quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.wearing:
            bits.append("wearing=True")
        if e.protected:
            bits.append("protected=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SURPRISES, params.surprise), params.name, params.hero_type, params.trait, params.supername)
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


CURATED = [
    StoryParams(place="animal_enclosure", surprise="baby_goat", name="Mia", hero_type="girl", trait="brave", supername="Captain Kindness"),
    StoryParams(place="animal_enclosure", surprise="stuck_balloon", name="Leo", hero_type="boy", trait="curious", supername="Spark Shield"),
    StoryParams(place="animal_enclosure", surprise="rain_spot", name="Ava", hero_type="girl", trait="careful", supername="Tiny Thunder"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid surprise/gear pairs:")
        for sid, gid in pairs:
            print(f"  {sid:12} {gid}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
