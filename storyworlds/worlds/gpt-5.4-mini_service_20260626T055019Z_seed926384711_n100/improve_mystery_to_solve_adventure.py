#!/usr/bin/env python3
"""
storyworlds/worlds/improve_mystery_to_solve_adventure.py
=========================================================

A small adventure storyworld about a child who wants to solve a mystery and
must improve a tool before the search can safely continue.

Seed image:
- A child is eager to investigate a puzzling clue outdoors or in a tucked-away
  place.
- An adult notices a problem with the child's gear or clue sheet.
- They improve the tool, follow the trail, and solve the mystery together.

The domain is intentionally narrow: every valid story is a short adventure
with a clear mystery, a concrete improvement, and a payoff that reveals what
changed.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    entities: set[str] = field(default_factory=set)
    gear_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    indoor: bool
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
    verb: str
    gerund: str
    rush: str
    danger: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "forest": Setting("the forest", False, {"track", "mystery", "trail"}),
    "cave": Setting("the cave", False, {"mystery", "map", "search"}),
    "harbor": Setting("the harbor", False, {"track", "search", "signal"}),
    "attic": Setting("the attic", True, {"search", "mystery", "map"}),
}

MYSTERIES = {
    "tracks": Mystery(
        id="tracks",
        verb="follow the tracks",
        gerund="following the tracks",
        rush="run after the tracks",
        danger="muddy",
        clue="hoofprints",
        keyword="tracks",
        tags={"track", "muddy"},
    ),
    "map": Mystery(
        id="map",
        verb="read the map",
        gerund="reading the map",
        rush="hurry to the map",
        danger="torn",
        clue="a torn corner",
        keyword="map",
        tags={"map", "torn"},
    ),
    "signal": Mystery(
        id="signal",
        verb="search for the signal",
        gerund="searching for the signal",
        rush="dash toward the signal",
        danger="dark",
        clue="a blinking light",
        keyword="signal",
        tags={"signal", "dark"},
    ),
    "dust": Mystery(
        id="dust",
        verb="search through the dusty boxes",
        gerund="searching through dusty boxes",
        rush="scramble through the dust",
        danger="dusty",
        clue="a hidden note",
        keyword="dust",
        tags={"search", "dusty"},
    ),
}

PRIZES = {
    "lantern": Prize("lantern", "a little brass lantern", "lantern", "hands"),
    "boots": Prize("boots", "sturdy boots", "boots", "feet", plural=True),
    "bag": Prize("bag", "a canvas bag", "bag", "hands"),
    "hat": Prize("hat", "a sun hat", "hat", "head"),
}

GEAR = [
    Gear("tape", "some bright tape", {"hands"}, {"torn"}, "tape up the torn corner", "taped the map corner together"),
    Gear("oil", "a drop of oil", {"hands"}, {"stuck"}, "oil the lantern wick", "oiled the lantern wick"),
    Gear("gloves", "soft gloves", {"hands"}, {"dusty"}, "put on soft gloves first", "pulled on the soft gloves"),
    Gear("bootsgear", "mud boots", {"feet"}, {"muddy"}, "put on mud boots first", "went to get the mud boots", plural=True),
]

NAMES_GIRL = ["Mina", "Luna", "Nora", "Ivy", "Zoe", "Lia"]
NAMES_BOY = ["Finn", "Theo", "Jude", "Owen", "Noah", "Pip"]
TRAITS = ["brave", "curious", "patient", "eager", "clever"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    gender: str
    parent: str
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


def prize_at_risk(mystery: Mystery, prize: Prize) -> bool:
    return prize.region in {"hands", "feet"} and (
        ("torn" in mystery.tags and prize.region == "hands")
        or ("muddy" in mystery.tags and prize.region == "feet")
        or ("dusty" in mystery.tags and prize.region == "hands")
        or ("dark" in mystery.tags and prize.region == "hands")
    )


def select_gear(mystery: Mystery, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and any(tag in mystery.tags for tag in gear.guards):
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mystery = _safe_lookup(MYSTERIES, mid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(mystery, prize) and select_gear(mystery, prize):
                    out.append((place, mid, pid))
    return out


def explain_rejection(mystery: Mystery, prize: Prize) -> str:
    return (
        f"(No story: {mystery.gerund} does not create a reasonable risk for {prize.label}, "
        f"or there is no believable way to improve the gear for that problem.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} does not fit a typical {gender} story here; try {ok}.)"


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mkey in ["muddy", "torn", "dusty", "dark"]:
            if actor.meters.get(mkey, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("risk", item.id, mkey)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mkey] = item.meters.get(mkey, 0.0) + 1
                item.meters["hurt"] = item.meters.get("hurt", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mkey}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("hurt", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would make {carer.label_word} worry.")
    return out


def _r_solve(world: World) -> list[str]:
    if world.facts.get("mystery_solved"):
        return []
    if world.facts.get("improved") and world.facts.get("clue_found"):
        world.facts["mystery_solved"] = True
        return ["__solve__"]
    return []


CAUSAL_RULES = [Rule("risk", _r_risk), Rule("worry", _r_worry), Rule("solve", _r_solve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__solve__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World, actor: Entity, mystery: Mystery, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.facts = dict(world.facts)
    hero = sim.get(actor.id)
    hero.meters[mystery.danger] = hero.meters.get(mystery.danger, 0.0) + 1
    sim.zone = {"hands" if prize_id in {"lantern", "bag"} else "feet"}
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": prize.meters.get(mystery.danger, 0.0) >= THRESHOLD, "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters())}


def tell(setting: Setting, mystery: Mystery, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity("parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id=prize_cfg.type,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.say(f"{hero.id} was a little {trait} {hero_type} who loved an adventure.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {mystery.verb} and solve the mystery.")
    world.say(f"On the way, {hero.id} carried {hero.pronoun('possessive')} {prize.label} like treasure.")
    world.para()

    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {setting.place}.")
    world.say(f"There, they found {mystery.clue}, and {hero.id} wanted to rush ahead.")
    hero.meters[mystery.danger] = hero.meters.get(mystery.danger, 0.0) + 1
    world.zone = {"hands" if prize.region == "hands" else "feet"}
    pred = predict_problem(world, hero, mystery, prize.id)
    if pred["damaged"]:
        world.say(f'"If you hurry like that, your {prize.label} could get {mystery.danger}," {parent.label_word} said.')
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} paused, but still wanted to keep going.")
    world.para()

    gear = select_gear(mystery, prize)
    if not gear:
        pass
    gear_ent = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear.covers), plural=gear.plural
    ))
    gear_ent.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} knew how to improve the plan.")
    world.say(f'"Let\'s {gear.prep}," {parent.label_word} said.')
    world.facts["improved"] = True
    world.facts["gear"] = gear
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["prize"] = prize
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    propagate(world, narrate=False)

    world.para()
    world.facts["clue_found"] = True
    world.say(f"With {gear.label}, {hero.id} could go on.")
    world.say(f"{hero.id} followed the {mystery.keyword} trail, found the hidden clue, and solved the mystery.")
    world.say(f"At the end, {hero.id} was {mystery.gerund}, and {prize.phrase} stayed safe and ready for the next adventure.")
    return world


KNOWLEDGE = {
    "tracks": [("What are tracks?", "Tracks are marks left by feet or hooves, and they can help you follow where something went.")],
    "map": [("What is a map?", "A map is a drawing that shows places and helps you find your way.")],
    "signal": [("What is a signal?", "A signal is a sign or message that helps someone know what to do or where to look.")],
    "dust": [("Why do dusty places need careful searching?", "Dusty places can hide little things, so careful searching helps you notice them.")],
    "torn": [("What does it mean when something is torn?", "Torn means it has a rip or a hole in it, so it may need fixing.")],
    "dark": [("Why do people use lanterns in the dark?", "Lanterns make light, so people can see clues and walk safely in dark places.")],
    "muddy": [("What is muddy ground?", "Muddy ground is wet dirt that can stick to shoes and make them heavy.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    mystery = _safe_fact(world, f, "mystery")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short adventure story for a young child about "{mystery.keyword}" and one important improvement.',
        f"Tell a mystery-solving story where {hero.id} wants to {mystery.verb}, but {parent.label_word} helps improve the plan so {prize.label} stays safe.",
        f"Write a child-friendly adventure with a clue, a fix, and a happy ending at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, mystery, prize = f["hero"], f["parent"], f["mystery"], f["prize"]
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {mystery.verb} and solve the mystery.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} stop {hero.id} for a moment?",
            answer=f"{parent.label_word.capitalize()} worried that {hero.id}'s {prize.label} could get {mystery.danger} during the search.",
        ),
        QAItem(
            question=f"What did they do to improve the plan?",
            answer=f"They used {gear.label} to improve the plan before going on with the search.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"They found the hidden clue, solved the mystery, and finished the adventure with {prize.phrase} still safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "tracks", "boots", "Mina", "girl", "mother", "brave"),
    StoryParams("cave", "map", "lantern", "Finn", "boy", "father", "curious"),
    StoryParams("attic", "dust", "bag", "Luna", "girl", "mother", "clever"),
    StoryParams("harbor", "signal", "lantern", "Theo", "boy", "father", "eager"),
]


ASP_RULES = r"""
prize_at_risk(M, P) :- danger(M, D), prize_region(P, R), needs_region(D, R).
fix(G, M, P) :- gear(G), prize_at_risk(M, P), guards(G, D), danger(M, D), covers(G, R), prize_region(P, R).
valid(Place, M, P) :- affords(Place, M), prize_at_risk(M, P), fix(_, M, P).
valid_story(Place, M, P, Gender) :- valid(Place, M, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("danger", mid, m.danger))
        lines.append(asp.fact("needs_region", m.danger, "hands" if m.danger in {"torn", "dark", "dusty"} else "feet"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Adventure mystery storyworld with a concrete improvement.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "mystery", None) and getattr(args, "prize", None):
        m, p = _safe_lookup(MYSTERIES, getattr(args, "mystery", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(m, p) and select_gear(m, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mid, pid = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, pid)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, mid, pid, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, mystery, prize) combos ({len(stories)} with gender):\n")
        for place, mid, pid in triples:
            genders = sorted(g for (pl, m, p, g) in stories if (pl, m, p) == (place, mid, pid))
            print(f"  {place:9} {mid:8} {pid:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.mystery} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
