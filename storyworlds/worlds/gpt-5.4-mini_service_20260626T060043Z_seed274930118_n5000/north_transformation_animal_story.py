#!/usr/bin/env python3
"""
storyworlds/worlds/north_transformation_animal_story.py
=======================================================

A small animal story world about a gentle trip north and a magical
transformation that helps the hero finish the journey.

The source tale behind this world is simple:
- a young animal wants to go north,
- the north path is cold, windy, or blocked,
- a helpful transformation changes the hero into a form that fits the north,
- the hero reaches the goal and ends changed.

This script models the story as a tiny simulation with physical meters
(distance, cold, tiredness) and emotional memes (hope, worry, joy, wonder).
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
    wears: Optional[str] = None
    transformed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    form: object | None = None
    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"rabbit", "hare", "mouse", "fox", "bear", "deer"}:
            # Keep this generic and child-friendly; animal stories often use it.
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    northness: int
    coldness: int
    allows: set[str] = field(default_factory=set)
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
class Form:
    id: str
    label: str
    phrase: str
    helps_in_cold: int
    grants: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    makes: str
    required: Optional[str] = None
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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


SETTINGS = {
    "meadow": Place("meadow", "the meadow", northness=0, coldness=0, allows={"walk", "travel"}),
    "riverbank": Place("riverbank", "the riverbank", northness=1, coldness=1, allows={"walk", "travel"}),
    "pinehill": Place("pinehill", "the pine hill", northness=2, coldness=2, allows={"walk", "travel"}),
    "northlake": Place("northlake", "the north lake", northness=3, coldness=3, allows={"walk", "travel"}),
}

ANIMALS = {
    "rabbit": "rabbit",
    "fox": "fox",
    "deer": "deer",
    "mouse": "mouse",
    "bear": "bear",
    "hare": "hare",
}

FORMS = {
    "snowhare": Form(
        id="snowhare",
        label="snow hare",
        phrase="a snow-white snow hare",
        helps_in_cold=3,
        grants={"run", "hide"},
    ),
    "arcticfox": Form(
        id="arcticfox",
        label="arctic fox",
        phrase="a bright arctic fox with a thick coat",
        helps_in_cold=3,
        grants={"run", "dig"},
    ),
    "winterdeer": Form(
        id="winterdeer",
        label="winter deer",
        phrase="a winter deer with strong legs",
        helps_in_cold=2,
        grants={"run", "climb"},
    ),
    "whitemouse": Form(
        id="whitemouse",
        label="white mouse",
        phrase="a tiny white mouse with warm fur",
        helps_in_cold=2,
        grants={"hide", "squeeze"},
    ),
}

CHARMS = {
    "moonstone": Charm("moonstone", "moonstone charm", "a moonstone charm that glows pale blue", makes="transform"),
    "snowbell": Charm("snowbell", "snowbell sprig", "a snowbell sprig tied with silk", makes="transform"),
    "northwind": Charm("northwind", "north wind song", "a soft north wind song", makes="transform"),
}

TRAITS = ["curious", "brave", "gentle", "playful", "quiet", "hopeful"]


@dataclass
class StoryParams:
    animal: str
    form: str
    place: str
    charm: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place_id, place in SETTINGS.items():
        for animal_id in ANIMALS:
            for form_id in FORMS:
                for charm_id in CHARMS:
                    if place.northness >= 1:
                        out.append((place_id, animal_id, form_id, charm_id))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("northness", pid, p.northness))
        lines.append(asp.fact("coldness", pid, p.coldness))
        for a in sorted(p.allows):
            lines.append(asp.fact("allows", pid, a))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for fid, f in FORMS.items():
        lines.append(asp.fact("form", fid))
        lines.append(asp.fact("helps_in_cold", fid, f.helps_in_cold))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("makes", cid, c.makes))
    return "\n".join(lines)


ASP_RULES = r"""
north_story(P,A,F,C) :- place(P), animal(A), form(F), charm(C), northness(P,N), N >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show north_story/4."))
    return sorted(set(asp.atoms(model, "north_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about a northward trip and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and _safe_lookup(SETTINGS, getattr(args, "place", None)).northness < 1:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "animal", None) is None or c[1] == getattr(args, "animal", None))
              and (getattr(args, "form", None) is None or c[2] == getattr(args, "form", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, animal, form, charm = rng.choice(list(combos))
    return StoryParams(
        animal=animal,
        form=form,
        place=place,
        charm=charm,
        name=getattr(args, "name", None) or rng.choice(["Pip", "Mimi", "Tavi", "Puck", "Nori", "Luna"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, meters={"cold": 0.0, "distance": 0.0}, memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "wonder": 0.0}))
    guide = world.add(Entity(id="Guide", kind="character", type="bear", label="an old bear", meters={}, memes={"kindness": 1.0}))
    form = world.add(Entity(id="Form", kind="thing", type=params.form, label=_safe_lookup(FORMS, params.form).label, phrase=_safe_lookup(FORMS, params.form).phrase))
    charm = world.add(Entity(id="Charm", kind="thing", type=params.charm, label=_safe_lookup(CHARMS, params.charm).label, phrase=_safe_lookup(CHARMS, params.charm).phrase))
    return hero, guide, form, charm


def _cold_step(world: World, hero: Entity, steps: int = 1) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + steps
    hero.meters["cold"] = hero.meters.get("cold", 0.0) + world.place.coldness * 0.5
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + (0.2 * world.place.coldness)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero, guide, form, charm = _setup(world, params)

    world.say(f"{params.name} was a {params.trait} {params.animal} who looked north and wondered what lay beyond the trees.")
    world.say(f"{params.name} loved the idea of going to {world.place.label}, because the air there felt different and the sky seemed to pull that way.")
    world.say(f"One morning, {params.name} found {_safe_lookup(CHARMS, params.charm).phrase} beside a root, and {guide.label} smiled and said it could help.")

    world.para()
    world.say(f"{params.name} set off toward {world.place.label}.")
    _cold_step(world, hero, 1)
    world.say(f"The farther {params.name} went, the colder the wind felt, and {params.name} began to shiver.")
    hero.memes["worry"] += 0.6
    hero.memes["hope"] += 0.3

    if world.place.northness >= 1:
        world.say(f"{guide.label} told {params.name}, \"The north asks you to change, not turn back.\"")
        hero.memes["wonder"] += 0.6
        world.say(f"{params.name} held the charm close, and a pale light wrapped around the little animal like falling snow.")
        hero.transformed_from = hero.type
        hero.type = form.id
        hero.label = form.label
        hero.phrase = form.phrase
        hero.meters["cold_resist"] = form.helps_in_cold
        hero.memes["joy"] += 1.0
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
        world.say(f"When the light faded, {params.name} was {form.phrase}, ready for the cold north.")
        world.say(f"Now {params.name} could run on and on without trembling, and the path felt easier under small feet.")

    world.para()
    _cold_step(world, hero, 1)
    hero.meters["distance"] = max(hero.meters.get("distance", 0.0), float(world.place.northness))
    hero.memes["joy"] += 0.5
    hero.memes["wonder"] += 0.4
    world.say(f"{params.name} finally reached {world.place.label}, where the wind was crisp and the ground shimmered pale.")
    if hero.transformed_from:
        world.say(f"{params.name} had not only made it north; {params.name} had become the kind of creature that belonged there.")
    else:
        world.say(f"{params.name} arrived still the same, but proud of the long trip.")

    world.facts.update(hero=hero, guide=guide, form=form, charm=charm, params=params, place=world.place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    return [
        f'Write a short animal story for a young child about going north and changing form, using the word "north".',
        f"Tell a gentle story about {p.name}, a {p.trait} {p.animal}, who goes north and is transformed by {_safe_lookup(CHARMS, p.charm).label}.",
        f"Write an animal tale where a small creature reaches {world.place.label} after a magical transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    hero = _safe_fact(world, f, "hero")
    form = _safe_fact(world, f, "form")
    guide = _safe_fact(world, f, "guide")
    qa = [
        QAItem(
            question=f"Who is the story about, and where did {p.name} want to go?",
            answer=f"The story is about {p.name}, a {p.trait} {p.animal}, and {p.name} wanted to go north to {world.place.label}.",
        ),
        QAItem(
            question=f"What made the trip hard for {p.name}?",
            answer=f"The trip got hard because the north air was cold, so {p.name} started to shiver and worry a little.",
        ),
        QAItem(
            question=f"Who helped {p.name} with the change?",
            answer=f"An old bear helped by encouraging {p.name} to use {_safe_lookup(CHARMS, p.charm).label} and keep going.",
        ),
        QAItem(
            question=f"What did {p.name} become by the end?",
            answer=f"{p.name} became {form.phrase}, and that new form fit the cold north much better.",
        ),
    ]
    if hero.transformed_from:
        qa.append(QAItem(
            question=f"How did the transformation change {p.name}'s journey north?",
            answer=f"The transformation changed {p.name} from a {hero.transformed_from} into {form.label}, so the cold north no longer felt too hard.",
        ))
    qa.append(QAItem(
        question=f"Why was the ending happy?",
        answer=f"The ending was happy because {p.name} reached {world.place.label} and arrived safely after the magical change.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does north mean?",
            answer="North is a direction. If you go north, you travel toward the north side of a map or place.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="Why might animals need thick fur in cold places?",
            answer="Thick fur helps animals stay warmer when the weather is cold and windy.",
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
        if e.transformed_from:
            bits.append(f"transformed_from={e.transformed_from}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="rabbit", form="snowhare", place="northlake", charm="moonstone", name="Pip", trait="curious"),
    StoryParams(animal="fox", form="arcticfox", place="pinehill", charm="snowbell", name="Mimi", trait="brave"),
    StoryParams(animal="deer", form="winterdeer", place="northlake", charm="northwind", name="Tavi", trait="hopeful"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a place with a real northward pull so the transformation has a reason to happen.)"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and _safe_lookup(SETTINGS, getattr(args, "place", None)).northness < 1:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "animal", None) is None or c[1] == getattr(args, "animal", None))
              and (getattr(args, "form", None) is None or c[2] == getattr(args, "form", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, animal, form, charm = rng.choice(list(combos))
    return StoryParams(
        animal=animal,
        form=form,
        place=place,
        charm=charm,
        name=getattr(args, "name", None) or rng.choice(["Pip", "Mimi", "Tavi", "Nori", "Luna", "Bean"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show north_story/4."))
    return sorted(set(asp.atoms(model, "north_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show north_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid_stories()
        print(f"{len(vals)} compatible north stories:\n")
        for row in vals[:50]:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.animal} -> {p.form} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
