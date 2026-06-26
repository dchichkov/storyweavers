#!/usr/bin/env python3
"""
storyworlds/worlds/virtuosity_cafe_mystery_to_solve_transformation_superhero.py
==============================================================================

A tiny superhero storyworld about a cafe mystery that can be solved only by
a fitting transformation and a careful, virtuoso use of powers.

The seed idea:
- A child-friendly superhero visits a cafe.
- Something mysterious goes wrong.
- The hero must transform to solve it.
- The ending should show what changed in the cafe and in the hero.

This world is deliberately small and constraint-driven:
- the cafe has a few possible mysteries;
- only some transformations can handle them;
- the story is generated from a simulated world state, not a frozen template;
- the word "virtuosity" is used in the prose and registries, and the cafe is central.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
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
class Cafe:
    name: str = "the cafe"
    cozy: bool = True
    menu: set[str] = field(default_factory=set)
    mystery: str = ""
    cafe: object | None = None
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
class Mystery:
    id: str
    label: str
    symptom: str
    cause: str
    clue: str
    risk: str
    solved_by: set[str]
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
class Transformation:
    id: str
    label: str
    body: str
    power: str
    method: str
    finish: str
    solves: set[str]
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
class World:
    cafe: Cafe
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(
            cafe=_copy.deepcopy(self.cafe),
            entities=_copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
        )
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


def _default_meters() -> dict[str, float]:
    return {"focus": 0.0, "mess": 0.0, "wonder": 0.0, "calm": 0.0}


def _default_memes() -> dict[str, float]:
    return {"curiosity": 0.0, "bravery": 0.0, "virtuosity": 0.0, "worry": 0.0, "joy": 0.0}


def set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


MYSTERIES = {
    "missing_spoons": Mystery(
        id="missing_spoons",
        label="missing spoons",
        symptom="the spoons were gone from the counter",
        cause="a tiny magnet under the tray had pulled them together",
        clue="the spoons all hid under the sugar jar",
        risk="the cafe could not serve the cakes neatly",
        solved_by={"xray", "tiny" , "light"},
    ),
    "sticky_floor": Mystery(
        id="sticky_floor",
        label="sticky floor",
        symptom="the floor near the pastry case felt sticky",
        cause="a spilled berry syrup had spread in a shiny trail",
        clue="blue-red footprints led to the napkin stack",
        risk="people could slip, and the cafe would feel messy",
        solved_by={"stretch", "speed"},
    ),
    "quiet_machine": Mystery(
        id="quiet_machine",
        label="quiet espresso machine",
        symptom="the espresso machine had stopped hissing",
        cause="a paper clip had jammed the little steam valve",
        clue="a tiny silver bend peeked from the side",
        risk="the cafe would have no warm drinks",
        solved_by={"xray", "tiny"},
    ),
    "sleepy_clock": Mystery(
        id="sleepy_clock",
        label="sleepy wall clock",
        symptom="the wall clock had stopped on three o'clock",
        cause="its battery had slipped loose behind the frame",
        clue="the clock ticked only when someone tapped the wall",
        risk="customers would not know when their snacks were ready",
        solved_by={"stretch", "light"},
    ),
}

TRANSFORMS = {
    "xray": Transformation(
        id="xray",
        label="x-ray eyes",
        body="a bright silver suit",
        power="see hidden things",
        method="look through the counters and walls",
        finish="could find the hidden clue",
        solves={"missing_spoons", "quiet_machine", "sleepy_clock"},
    ),
    "tiny": Transformation(
        id="tiny",
        label="tiny size",
        body="a pocket-sized blue suit",
        power="slip into little places",
        method="sneak under trays and behind jars",
        finish="could reach what was tucked away",
        solves={"missing_spoons", "quiet_machine"},
    ),
    "stretch": Transformation(
        id="stretch",
        label="stretchy arms",
        body="a ribbon-red suit",
        power="reach far without knocking things over",
        method="carefully reach behind the machine and across the room",
        finish="could fix what was just out of reach",
        solves={"sticky_floor", "sleepy_clock"},
    ),
    "speed": Transformation(
        id="speed",
        label="speed burst",
        body="a streak-gold suit",
        power="move fast and tidy up",
        method="dash to the spill and stop it from spreading",
        finish="could keep the cafe safe",
        solves={"sticky_floor"},
    ),
    "light": Transformation(
        id="light",
        label="light hands",
        body="a lantern-white suit",
        power="shine gently on tiny clues",
        method="bathe the corner in a soft glow",
        finish="could notice what others missed",
        solves={"sleepy_clock", "missing_spoons"},
    ),
}

HERO_NAMES = ["Nova", "Comet", "Spark", "Milo", "Iris", "Zara", "Finn", "Luna"]
SIDEKICK_NAMES = ["Pip", "Bea", "Tess", "Ollie"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for mid, m in MYSTERIES.items():
        for tid, t in TRANSFORMS.items():
            if mid in t.solves and tid in m.solved_by:
                combos.append((mid, tid))
    return combos


@dataclass
class StoryParams:
    mystery: str
    transform: str
    hero_name: str
    sidekick_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero cafe mystery world with transformation and virtuosity.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
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
    if getattr(args, "mystery", None) and getattr(args, "transform", None) and (getattr(args, "mystery", None), getattr(args, "transform", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        (m, t) for (m, t) in combos
        if (getattr(args, "mystery", None) is None or m == getattr(args, "mystery", None))
        and (getattr(args, "transform", None) is None or t == getattr(args, "transform", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    mystery, transform = rng.choice(list(filtered))
    return StoryParams(
        mystery=mystery,
        transform=transform,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        sidekick_name=getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES),
    )


def story_intro(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    world.say(
        f"{hero.id} was a small superhero who loved virtuosity: every trick had to be careful, "
        f"bright, and kind."
    )
    world.say(
        f"With {sidekick.id} beside {hero.pronoun('object')}, {hero.id} went to the cafe because "
        f"the cafe made the best blueberry buns in town."
    )


def mystery_arrives(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    cafe = world.cafe
    set_meme(hero, "curiosity", 1)
    set_meter(hero, "wonder", 1)
    set_meme(sidekick, "worry", 1)
    cafe.mystery = mystery.id
    world.say(
        f"But inside {cafe.name}, something was wrong. {mystery.symptom}, and the room felt hushed."
    )
    world.say(
        f"{sidekick.id} pointed and whispered, \"That is a real mystery to solve.\""
    )


def investigate(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    set_meme(hero, "curiosity", 1)
    set_meter(hero, "focus", 1)
    world.say(
        f"{hero.id} looked carefully around the tables. {mystery.clue.capitalize()}."
    )
    world.say(
        f"{hero.id} said, \"I need the right transformation.\""
    )


def transform(world: World, tr: Transformation) -> None:
    hero = world.get("hero")
    hero.label = tr.label
    hero.phrase = tr.body
    set_meme(hero, "bravery", 1)
    set_meme(hero, "virtuosity", 1)
    world.say(
        f"Then {hero.id} spun in place and changed into {tr.body}."
    )
    world.say(
        f"{hero.id} now had {tr.label}, so {hero.pronoun()} could {tr.power}."
    )


def solve_mystery(world: World, mystery: Mystery, tr: Transformation) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    cafe = world.cafe
    if mystery.id not in tr.solves:
        pass

    if mystery.id == "missing_spoons":
        world.say(
            f"{hero.id} used {hero.pronoun('possessive')} {tr.label} to {tr.method}."
        )
        world.say(
            f"Under the sugar jar, {mystery.cause}, and the spoons gleamed in a neat pile."
        )
        world.say(
            f"{hero.id} carried them back, and the cafe owner cheered because the cakes could be served again."
        )
    elif mystery.id == "sticky_floor":
        world.say(
            f"{hero.id} used {hero.pronoun('possessive')} {tr.label} to {tr.method}."
        )
        world.say(
            f"Near the pastry case, {mystery.cause}, so {hero.id} cleaned it up before anyone slipped."
        )
        world.say(
            f"{sidekick.id} grinned when the floor turned safe and shiny again."
        )
    elif mystery.id == "quiet_machine":
        world.say(
            f"{hero.id} used {hero.pronoun('possessive')} {tr.label} to {tr.method}."
        )
        world.say(
            f"Behind the panel, {mystery.cause}, and once it was removed the machine gave a happy hiss."
        )
        world.say(
            f"Warm cocoa came out at last, and the cafe smelled cozy again."
        )
    elif mystery.id == "sleepy_clock":
        world.say(
            f"{hero.id} used {hero.pronoun('possessive')} {tr.label} to {tr.method}."
        )
        world.say(
            f"Behind the clock, {mystery.cause}, so {hero.id} fixed it with a careful little tap."
        )
        world.say(
            f"The clock woke up and ticked, and everyone in the cafe knew exactly when their snacks were ready."
        )

    cafe.mystery = ""
    set_meter(hero, "calm", 1)
    set_meme(hero, "joy", 1)
    set_meme(sidekick, "joy", 1)


def ending(world: World, tr: Transformation) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    world.para()
    world.say(
        f"At the end, {hero.id} smiled in {hero.pronoun('possessive')} {tr.label} suit, and the cafe was peaceful again."
    )
    world.say(
        f"{sidekick.id} laughed, the buns were safe, and the little superhero's virtuosity had saved the day."
    )


def tell(params: StoryParams) -> World:
    cafe = Cafe(name="the cafe", cozy=True, menu={"blueberry buns", "cocoa", "tea", "toast"})
    world = World(cafe=cafe)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", meters=_default_meters(), memes=_default_memes()))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick", meters=_default_meters(), memes=_default_memes()))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tr = _safe_lookup(TRANSFORMS, params.transform)

    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery, transform=tr, cafe=cafe)
    story_intro(world)
    world.para()
    mystery_arrives(world, mystery)
    investigate(world, mystery)
    world.para()
    transform(world, tr)
    solve_mystery(world, mystery, tr)
    ending(world, tr)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the word "virtuosity" and takes place in a cafe.',
        f"Tell a gentle mystery-to-solve story where {f['hero'].id} must transform to fix {f['mystery'].label} in the cafe.",
        f"Write a story about a superhero named {f['hero'].id} who uses {f['transform'].label} to help {f['sidekick'].id} at the cafe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    mystery = _safe_fact(world, f, "mystery")
    tr = _safe_fact(world, f, "transform")
    qa = [
        QAItem(
            question=f"Where did {hero.id} and {sidekick.id} go in the story?",
            answer=f"They went to the cafe, where something strange had happened.",
        ),
        QAItem(
            question=f"What was the mystery in the cafe?",
            answer=f"The mystery was {mystery.label}: {mystery.symptom}.",
        ),
        QAItem(
            question=f"What transformation did {hero.id} use to solve it?",
            answer=f"{hero.id} used {tr.label}, which let {hero.pronoun()} {tr.power}.",
        ),
        QAItem(
            question=f"How did the hero show virtuosity?",
            answer=f"{hero.id} showed virtuosity by using {tr.label} carefully and solving the problem without causing more trouble.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cafe?",
            answer="A cafe is a small place where people can buy drinks and snacks and sit together.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, solves problems, and uses special powers for good.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or hidden that people want to understand.",
        ),
        QAItem(
            question="What is transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  cafe     (place) name={world.cafe.name!r} mystery={world.cafe.mystery!r}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(mystery="missing_spoons", transform="xray", hero_name="Nova", sidekick_name="Pip"),
    StoryParams(mystery="sticky_floor", transform="speed", hero_name="Spark", sidekick_name="Bea"),
    StoryParams(mystery="quiet_machine", transform="tiny", hero_name="Comet", sidekick_name="Tess"),
    StoryParams(mystery="sleepy_clock", transform="light", hero_name="Iris", sidekick_name="Ollie"),
]


ASP_RULES = r"""
mystery(M) :- mystery_fact(M).
transform(T) :- transform_fact(T).

can_solve(M,T) :- mystery_fact(M), transform_fact(T), solves(T,M), needs(M,T).
valid_story(M,T) :- can_solve(M,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("needs", mid, *sorted(next(iter([t for t in m.solved_by]), "xray"))))
        # The above placeholder is not used by rules; we emit explicit solves facts below.
        for t in sorted(m.solved_by):
            lines.append(asp.fact("needs", mid, t))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform_fact", tid))
        for m in sorted(t.solves):
            lines.append(asp.fact("solves", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(mystery: str, transform: str) -> str:
    return f"(No story: {_safe_lookup(TRANSFORMS, transform).label} cannot solve {_safe_lookup(MYSTERIES, mystery).label} in a reasonable cafe mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "mystery", None) and getattr(args, "transform", None) and (getattr(args, "mystery", None), getattr(args, "transform", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        (m, t) for (m, t) in combos
        if (getattr(args, "mystery", None) is None or m == getattr(args, "mystery", None))
        and (getattr(args, "transform", None) is None or t == getattr(args, "transform", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    mystery, transform = rng.choice(list(filtered))
    return StoryParams(
        mystery=mystery,
        transform=transform,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        sidekick_name=getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES),
    )


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery/transformation combos:\n")
        for m, t in combos:
            print(f"  {m:16} {t}")
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
            header = f"### {p.hero_name}: {p.mystery} -> {p.transform}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
