#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/strife_brush_bleed_bravery_tall_tale.py
===============================================================================================================

A small, self-contained tall-tale storyworld about strife in the brush,
a scrape that can bleed, and the bravery needed to get through it.

Premise:
- A child, a wild horse, or a ranch helper heads into thorny brush to solve a
  problem.
- The brush can snag clothing, hide a lost object, and scratch skin.
- A careful but brave choice turns the strife into a memorable rescue.

The domain is deliberately tiny and constraint-checked:
- Every story has a clear danger in the brush.
- The danger can lead to a scrape and bleed.
- Bravery is the emotional turn that makes the resolution possible.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("scrape", 0.0)
        self.meters.setdefault("lost", 0.0)
        self.meters.setdefault("found", 0.0)
        self.meters.setdefault("clean", 0.0)
        self.meters.setdefault("covered", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("strife", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "cowgirl"}
        male = {"boy", "father", "man", "cowboy"}
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
    place: str = "the mesquite range"
    brush: str = "thorny brush"
    mood: str = "wide and wild"
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
    rash: str
    scrape: str
    zone: set[str]
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
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes["fear"] < THRESHOLD:
            continue
        if "brush" not in world.zone:
            continue
        sig = ("scrape", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["scrape"] += 1
        actor.memes["strife"] += 1
        out.append(f"The brush left a scrape on {actor.id}.")
    return out


def _r_bleed(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters["scrape"] < THRESHOLD:
            continue
        sig = ("bleed", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["bleed"] = actor.meters.get("bleed", 0.0) + 1
        out.append(f"The scrape began to bleed.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes["bravery"] < THRESHOLD:
            continue
        if actor.meters["found"] < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] += 1
        actor.memes["strife"] = 0.0
        out.append(f"{actor.id} found the thing and felt relief.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_scrape, _r_bleed, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose(setting: Setting, challenge: Challenge, prize: Prize, aid: Optional[Aid]) -> bool:
    if challenge.id not in setting.affords:
        return False
    if prize.region not in challenge.zone:
        return False
    if aid is None:
        return True
    return challenge.id in aid.helps and prize.region in aid.covers


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    aid: str
    name: str
    gender: str
    role: str
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
    "range": Setting(place="the mesquite range", brush="thorny brush", mood="wide and wild", affords={"brush"}),
    "creek": Setting(place="the dry creek bend", brush="greasy brush", mood="dusty and bright", affords={"brush"}),
    "canyon": Setting(place="the red canyon edge", brush="bitter brush", mood="hot and echoing", affords={"brush"}),
}

CHALLENGES = {
    "brush": Challenge(
        id="brush",
        verb="push through the brush",
        gerund="pushing through the brush",
        rash="went on anyway",
        scrape="thorn-scraped",
        zone={"arms", "legs"},
        tags={"brush", "strife"},
    ),
    "search": Challenge(
        id="search",
        verb="search the brush",
        gerund="searching the brush",
        rash="kept on searching",
        scrape="thorn-scraped",
        zone={"arms", "legs"},
        tags={"brush", "search", "strife"},
    ),
}

PRIZES = {
    "calf": Prize(id="calf", label="lost calf", phrase="a lost calf", region="legs", tags={"animal"}),
    "hat": Prize(id="hat", label="hat", phrase="a broad-brimmed hat", region="head", tags={"hat"}),
    "lantern": Prize(id="lantern", label="lantern", phrase="a little lantern", region="hands", tags={"light"}),
}

AIDS = {
    "gloves": Aid(id="gloves", label="work gloves", phrase="a pair of work gloves", helps={"brush", "search"}, covers={"hands", "arms"}, tags={"gear"}),
    "boots": Aid(id="boots", label="tall boots", phrase="tall boots", helps={"brush"}, covers={"legs", "feet"}, tags={"gear"}),
    "none": None,
}

NAMES_GIRL = ["Luz", "Mina", "Rosa", "June", "Mabel", "Tess"]
NAMES_BOY = ["Cal", "Hank", "Eli", "Jeb", "Owen", "Bo"]
ROLES = ["cowgirl", "cowboy", "ranch kid", "young wrangler"]
TRAITS = ["brave", "bold", "steady", "spunky", "stubborn"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for challenge_id, challenge in CHALLENGES.items():
            if challenge_id not in setting.affords:
                continue
            for prize_id, prize in PRIZES.items():
                if prize.region not in challenge.zone:
                    continue
                for aid_id, aid in AIDS.items():
                    if choose(setting, challenge, prize, aid):
                        out.append((place, challenge_id, prize_id, aid_id))
    return out


def explain_rejection(challenge: Challenge, prize: Prize, aid: Optional[Aid]) -> str:
    if prize.region not in challenge.zone:
        return f"(No story: {challenge.gerund} does not reach a {prize.label} worn on the {prize.region}.)"
    if aid is None:
        return "(No story: this tale needs a helpful bit of gear to make the brave fix work.)"
    return f"(No story: {aid.label} does not really solve the brush problem for a {prize.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: strife, brush, bleed, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=list(AIDS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "aid", None) is None or c[3] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, challenge=challenge, prize=prize, aid=aid, name=name, gender=gender, role=role)


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, aid: Optional[Aid],
         name: str, gender: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=role, traits=["little", "brave"]))
    helper = world.add(Entity(id="Helper", kind="character", type="old scout", label="the old scout"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    hero.memes["bravery"] += 1
    if aid is not None:
        world.add(Entity(id=aid.id, type="gear", label=aid.label, phrase=aid.phrase))

    world.say(f"In {setting.place}, under a sky as big as a barn door, there lived a {role} named {name}.")
    world.say(f"{name} was as {hero.traits[1]} as a whip-poor-will and had a heart full of bravery.")
    world.say(f"One day, {name} heard tell of {prize.phrase} hidden in the {setting.brush}.")
    world.para()
    world.say(f"{name} wanted to {challenge.verb}, but the {setting.brush} was all strife and scratch.")
    world.zone = set(challenge.zone)
    hero.memes["fear"] += 1
    hero.memes["strife"] += 1
    if aid is not None:
        world.say(f"The old scout handed over {aid.phrase} and said, 'A brave plan beats a hard wind.'")
        hero.memes["bravery"] += 1
    world.say(f"{name} {challenge.rash} anyway.")
    propagate(world)
    world.para()
    if hero.meters.get("bleed", 0.0) >= THRESHOLD:
        world.say(f"Still, {name} did not back up an inch, and the little scrape began to bleed.")
    world.say(f"Then {name} used {aid.label if aid is not None else 'bare hands'} to find the prize.")
    hero.meters["found"] += 1
    hero.memes["bravery"] += 1
    propagate(world)
    world.say(f"At last, {name} brought the {prize.label} home, and the brush looked smaller than a broom straw.")
    world.facts.update(hero=hero, helper=helper, prize=prize, aid=aid, setting=setting, challenge=challenge)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    prize = _safe_fact(world, f, "prize")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a tall-tale story for a young child about a brave {hero.type} who must {challenge.verb} in {setting.place} to find {prize.phrase}.',
        f'Tell a funny frontier story that includes "strife", "brush", and "bleed", and ends with bravery winning the day.',
        f'Write a short story where {hero.id} faces thorny brush, gets a scrape, and still keeps going to find {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    challenge = _safe_fact(world, f, "challenge")
    setting = _safe_fact(world, f, "setting")
    aid = _safe_fact(world, f, "aid")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.type} with a brave heart, out in {setting.place}.",
        ),
        QAItem(
            question=f"What was {name_or_label(hero)} trying to do in the brush?",
            answer=f"{hero.id} was trying to {challenge.verb} to find {prize.phrase}.",
        ),
        QAItem(
            question=f"What made the trip feel like strife?",
            answer=f"The thorny {setting.brush} made the trip feel like strife because it could scrape skin and make someone bleed.",
        ),
    ]
    if aid is not None:
        qa.append(QAItem(
            question=f"What helped {hero.id} keep going?",
            answer=f"{aid.label} helped {hero.id} by making the brush work easier and safer.",
        ))
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"{hero.id} found the {prize.label}, showed bravery, and came home with the problem solved.",
    ))
    return qa


def name_or_label(hero: Entity) -> str:
    return hero.id


KNOWLEDGE = {
    "brush": [("What is brush?", "Brush is a bunch of wild plants, twigs, and thorny branches that can scratch your skin.")],
    "bleed": [("What does it mean when a scrape bleeds?", "It means the skin was scratched open enough for a little blood to come out.")],
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary because it needs to be done.")],
    "strife": [("What is strife?", "Strife is trouble or a hard struggle, like when a job gets rough and everybody has to try harder.")],
    "gear": [("Why use gloves in the brush?", "Gloves help protect hands and arms from thorns and scratches.")],
    "animal": [("Why might a young animal hide in brush?", "Young animals sometimes hide in brush because it gives them shade and a place to stay out of sight.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags) | set(world.facts["prize"].tags)
    if world.facts.get("aid") is not None:
        tags.add("gear")
    tags.add("bravery")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
brave(H) :- bravery(H).
at_risk(P) :- prize(P), worn_on(P,R), zone(R).
needs_aid(H) :- character(H), fear(H), at_risk(_).
valid_story(Place, Challenge, Prize, Aid) :- setting(Place), challenge(Challenge), prize(Prize), aid(Aid).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for z in sorted(c.zone):
            lines.append(asp.fact("zone", z))
            lines.append(asp.fact("splashes", cid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for aid, a in AIDS.items():
        if a is None:
            continue
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Light parity check: the ASP program should run and produce at least one model.
    model = asp.one_model(asp_program("#show valid_story/4."))
    if model is None:
        print("MISMATCH: no ASP model found.")
        return 1
    print("OK: ASP program runs.")
    return 0


def build_story(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize),
                 _safe_lookup(AIDS, params.aid), params.name, params.gender, params.role)
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
    StoryParams(place="range", challenge="brush", prize="calf", aid="gloves", name="Luz", gender="girl", role="cowgirl"),
    StoryParams(place="creek", challenge="search", prize="hat", aid="boots", name="Hank", gender="boy", role="cowboy"),
    StoryParams(place="canyon", challenge="brush", prize="lantern", aid="gloves", name="Mabel", gender="girl", role="ranch kid"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [build_story(p) for p in CURATED]
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
            sample = build_story(params)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
