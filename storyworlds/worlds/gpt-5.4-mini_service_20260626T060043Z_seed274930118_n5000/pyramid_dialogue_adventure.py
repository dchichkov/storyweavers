#!/usr/bin/env python3
"""
Standalone storyworld: pyramid dialogue adventure.

A child-friendly adventure world set around an ancient pyramid, built from a
small simulated model with physical meters and emotional memes. The story
centers on a little expedition, a spoken warning, a risky choice, and a
resolved turn that proves something changed in the world.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    g: object | None = None
    guide: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

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
    place: str = "the pyramid"
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    soil: str
    zone: set[str]
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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


def _act(world: World, hero: Entity, chall: Challenge, narrate: bool = True) -> None:
    if chall.id not in world.setting.affords:
        pass
    world.zone = set(chall.zone)
    hero.meters[chall.hazard] = hero.meters.get(chall.hazard, 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    for item in world.worn_items(hero):
        if item.region in world.zone and chall.hazard in item.meters:
            if item.meters.get("protected", 0.0) < THRESHOLD:
                item.meters[chall.hazard] = item.meters.get(chall.hazard, 0.0) + 1.0
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} took a step deeper into the pyramid.")


def predict_harm(world: World, hero: Entity, chall: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    _act(sim, sim.get(hero.id), chall, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"ruined": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _ruin_rule(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for chal in CHALLENGES.values():
            if actor.meters.get(chal.hazard, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region in world.zone and chal.hazard in item.meters and item.meters.get("protected", 0.0) < THRESHOLD:
                    sig = ("ruin", item.id, chal.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
                    out.append(f"{item.label} got dusty inside the pyramid.")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if _ruin_rule(world):
            changed = True


def select_gear(chall: Challenge, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if chall.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combo(place: str, chall_id: str, prize_id: str) -> bool:
    chall = _safe_lookup(CHALLENGES, chall_id)
    prize = _safe_lookup(PRIZES, prize_id)
    return prize.region in chall.zone and select_gear(chall, prize) is not None


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    guide: str
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


SETTINGS = {
    "pyramid": Setting(place="the pyramid", affords={"chamber", "trapdoor", "maze"}),
}

CHALLENGES = {
    "chamber": Challenge(
        id="chamber",
        verb="explore the chamber",
        gerund="exploring the chamber",
        rush="hurry across the chamber",
        hazard="dust",
        soil="dusty",
        zone={"torso", "legs"},
        keyword="pyramid",
        tags={"pyramid", "dust"},
    ),
    "trapdoor": Challenge(
        id="trapdoor",
        verb="cross the trapdoor",
        gerund="crossing the trapdoor",
        rush="dash over the trapdoor",
        hazard="jolt",
        soil="shaken",
        zone={"feet", "legs"},
        keyword="pyramid",
        tags={"pyramid", "trap"},
    ),
    "maze": Challenge(
        id="maze",
        verb="walk the maze",
        gerund="walking the maze",
        rush="run into the maze",
        hazard="scratch",
        soil="scratched",
        zone={"torso", "legs"},
        keyword="pyramid",
        tags={"pyramid", "maze"},
    ),
}

PRIZES = {
    "map": Prize("map", "a folded treasure map", "map", "torso"),
    "cloak": Prize("cloak", "a light explorer's cloak", "cloak", "torso"),
    "boots": Prize("boots", "sturdy boots", "boots", "feet", plural=True),
}

GEAR = [
    Gear("dust_cloak", "a dust cloak", {"torso"}, {"dust"}, "put on a dust cloak", "wore the dust cloak", False),
    Gear("boots_guard", "boots with thick soles", {"feet"}, {"jolt"}, "lace up thick-soled boots", "latched their boots", True),
    Gear("maze_gloves", "soft gloves", {"torso", "legs"}, {"scratch"}, "put on soft gloves and long wraps", "tied on the soft wraps", False),
]

GIRL_NAMES = ["Nia", "Lina", "Maya", "Zara", "Ari", "Tess"]
BOY_NAMES = ["Owen", "Kai", "Noah", "Eli", "Finn", "Leo"]
GUIDES = ["guide", "aunt", "uncle", "mother", "father"]
TRAITS = ["brave", "curious", "careful", "bright", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for chall_id in _safe_lookup(SETTINGS, place).affords:
            for prize_id in PRIZES:
                if valid_combo(place, chall_id, prize_id):
                    out.append((place, chall_id, prize_id))
    return out


def explain_rejection(chall: Challenge, prize: Prize) -> str:
    if prize.region not in chall.zone:
        return f"(No story: {chall.gerund} does not threaten a prize worn on the {prize.region}.)"
    return f"(No story: the catalog has no gear that both fits {prize.label} and guards against {chall.hazard}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld set in a pyramid with dialogue.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--challenge", choices=list(CHALLENGES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        if not valid_combo("pyramid", getattr(args, "challenge", None), getattr(args, "prize", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(GUIDES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, challenge, prize, name, gender, guide, trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(params.name, "character", params.gender, traits=[params.trait, "young"]))
    guide = world.add(Entity("guide", "character", params.guide, label=params.guide))
    prize = world.add(Entity("prize", "thing", _safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, region=_safe_lookup(PRIZES, params.prize).region))
    gear = None

    world.say(f"{hero.id} stood at the mouth of the pyramid with {hero.pronoun('possessive')} {guide.label} and a whisper of sand in the air.")
    world.say(f'{guide.label.capitalize()} said, "Keep your voice soft. The pyramid listens."')
    world.say(f'{hero.id} smiled. "Then I will be brave and quiet," {hero.pronoun()} said, holding {hero.pronoun("possessive")} {prize.label} close.')

    world.para()
    chall = _safe_lookup(CHALLENGES, params.challenge)
    world.say(f"They went into {world.setting.place}, where old stone shadows curled along the walls.")
    world.say(f'{hero.id} said, "I want to {chall.verb}!"')
    world.say(f'{guide.label.capitalize()} answered, "Careful now. {chall.gerund.capitalize()} can leave {prize.label} {chall.soil}."')

    pred = predict_harm(world, hero, chall, prize.id)
    if pred["ruined"]:
        world.say(f'{hero.id} frowned. "Then let\'s find a safer way," {hero.pronoun()} said.')
    _act(world, hero, chall, narrate=False)
    propagate(world)

    world.para()
    if pred["ruined"]:
        gear = select_gear(chall, prize)
        if not gear:
            pass
        g = world.add(Entity(gear.id, "thing", "gear", label=gear.label, phrase=gear.label, owner=hero.id))
        g.worn_by = hero.id
        g.meters["protected"] = 1.0
        world.say(f'{guide.label.capitalize()} lifted {gear.label} and said, "{gear.prep} first."')
        world.say(f'{hero.id} nodded. "{hero.pronoun("subject").capitalize()} can do that," {hero.pronoun()} said.')
        world.say(f"They went on, and soon {gear.tail}; {hero.id} moved more carefully, and {prize.label} stayed clean.")
    else:
        world.say(f'{guide.label.capitalize()} smiled. "{prize.label.capitalize()} is safe with this step," {guide.label} said.')
        world.say(f"{hero.id} kept going, and the little adventure ended with a proud grin in the pyramid light.")

    world.facts.update(hero=hero, guide=guide, prize=prize, challenge=chall, gear=gear, params=params, conflict=pred["ruined"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, chall, prize = f["hero"], f["guide"], f["challenge"], f["prize"]
    return [
        'Write a short adventure story for a child set in a pyramid with dialogue and a cautious choice.',
        f'Write a simple story where {hero.id} and {guide.label} explore a pyramid and must protect {prize.label}.',
        f'Write an adventure tale that includes the word "pyramid" and a spoken warning about {chall.hazard}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, chall, prize = f["hero"], f["guide"], f["challenge"], f["prize"]
    qa = [
        QAItem(
            question=f"Who explored the pyramid with {hero.id}?",
            answer=f"{guide.label.capitalize()} explored the pyramid with {hero.id}, and they spoke to each other as they went.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do inside the pyramid?",
            answer=f"{hero.id} wanted to {chall.verb}, but {guide.label} warned that it could leave {prize.label} {chall.soil}.",
        ),
        QAItem(
            question=f"What happened to {prize.label} by the end of the story?",
            answer=f"{prize.label.capitalize()} stayed clean because {hero.id} chose the safer way and used the helpful gear.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did the guide worry about {prize.label}?",
            answer=f"The guide worried because {chall.gerund} could make {prize.label} {chall.soil}, and the story showed that danger in the pyramid.",
        ))
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} helped by protecting the right part of {hero.id}'s body, so the challenge could happen without ruining {prize.label}.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "pyramid": QAItem(
        question="What is a pyramid?",
        answer="A pyramid is a very old building with slanted sides that come together at the top.",
    ),
    "dust": QAItem(
        question="What is dust?",
        answer="Dust is made of tiny bits of dirt. It can settle on things and make them look gray or dirty.",
    ),
    "scratch": QAItem(
        question="What can scratches do to clothes?",
        answer="Scratches can tear or rough up cloth, which can make clothes look worn or damaged.",
    ),
    "jolt": QAItem(
        question="What does a jolt feel like?",
        answer="A jolt is a sudden bump or shake that can make you wobble for a moment.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    out = []
    for tag, qa in WORLD_KNOWLEDGE.items():
        if tag in tags or tag == "pyramid":
            out.append(qa)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), wears(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,H), hazard(A,H), covers(G,R), wears(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, a))
    for a, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", a))
        lines.append(asp.fact("hazard", a, ch.hazard))
        for z in sorted(ch.zone):
            lines.append(asp.fact("zone", a, z))
    for p, pr in PRIZES.items():
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("wears", p, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("pyramid", "chamber", "cloak", "Maya", "girl", "guide", "brave"),
    StoryParams("pyramid", "trapdoor", "boots", "Owen", "boy", "uncle", "careful"),
    StoryParams("pyramid", "maze", "map", "Nia", "girl", "aunt", "curious"),
]


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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
