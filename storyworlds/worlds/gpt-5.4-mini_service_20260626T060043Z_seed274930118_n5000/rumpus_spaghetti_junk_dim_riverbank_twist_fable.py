#!/usr/bin/env python3
"""
storyworlds/worlds/rumpus_spaghetti_junk_dim_riverbank_twist_fable.py
======================================================================

A small fable-style storyworld about a riverbank, a rumpus, spaghetti, and a
little twist that turns a mess into a kinder ending.

The seed image:
---
At the riverbank, a small fox and a small heron found a picnic basket with
spaghetti. A grumpy pile of junk lay in the dim reeds nearby. When the wind
made the basket wobble, the spaghetti slipped into the dirt and a rumpus
started. The fox blamed the heron, the heron blamed the wind, and both looked
unhappy.

Then a twist: the wise turtle suggested making a reed tray and sharing the
spaghetti by the water. They cleaned the junk-dim corner, set the tray on a
flat stone, and the rumpus faded. The picnic became calm, and everyone ate
together.

World model:
---
Typed entities carry physical meters and emotional memes. A small set of
forward rules turns actions into consequences: messy food can soil clothes or
fur, blame can raise rumpus, a helpful twist can lower it, and tidying the
riverbank can brighten the scene.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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

    companion: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    twist: object | None = None
    def __post_init__(self):
        for k in ["wet", "dirty", "full", "spilled", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "rumpus", "blame", "calm", "kindness", "worry"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heron"}
        male = {"boy", "father", "dad", "man", "fox", "turtle"}
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
    place: str = "the riverbank"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
class Twist:
    id: str
    label: str
    tool: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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


def _fable_voice(name: str) -> str:
    return {
        "fox": "A fox once learned",
        "heron": "A heron once learned",
        "turtle": "A turtle once knew",
    }.get(name, "A little one once learned")


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"spaghetti", "twist"}),
}

ACTIVITIES = {
    "spaghetti": Activity(
        id="spaghetti",
        verb="eat the spaghetti",
        gerund="eating spaghetti",
        rush="rush toward the basket",
        mess="saucy",
        soil="saucy and dirty",
        zone={"mouth", "chest", "paws"},
        keyword="spaghetti",
        tags={"spaghetti", "food", "mess"},
    ),
    "twist": Activity(
        id="twist",
        verb="make a twist",
        gerund="twisting reeds",
        rush="gather the reeds",
        mess="tidy",
        soil="neatly arranged",
        zone={"paws"},
        keyword="twist",
        tags={"twist", "help"},
    ),
}

PRIZES = {
    "sash": Prize(
        label="sash",
        phrase="a small bright sash",
        type="sash",
        region="chest",
    ),
    "apron": Prize(
        label="apron",
        phrase="a little apron",
        type="apron",
        region="chest",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a soft scarf",
        type="scarf",
        region="chest",
    ),
}

TWISTS = {
    "reedtray": Twist(
        id="reedtray",
        label="a reed tray",
        tool="reed tray",
        prep="weave a reed tray",
        tail="set the tray on a flat stone",
        helps={"spaghetti"},
    ),
    "stoneplate": Twist(
        id="stoneplate",
        label="a flat stone plate",
        tool="stone plate",
        prep="find a flat stone",
        tail="rest the basket on the stone",
        helps={"spaghetti"},
    ),
}

FOX_NAMES = ["Finn", "Toby", "Pip", "Milo", "Jasper"]
HERON_NAMES = ["Iris", "Nell", "Wren", "Luma", "Marigold"]
TURTLE_NAMES = ["Otto", "Bram", "Moss", "Tiko", "Sage"]
TRAITS = ["patient", "curious", "proud", "gentle", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    twist: str
    name: str
    companion: str
    helper: str
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
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                if place == "riverbank" and act == "spaghetti":
                    for tw in TWISTS:
                        combos.append((place, act, prize, tw))
    return combos


def reasonableness_gate(activity: Activity, prize: Prize, twist: Twist) -> bool:
    return activity.id == "spaghetti" and prize.region in {"chest"} and activity.mess in {"saucy"} and "spaghetti" in twist.helps


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not fit a fable about {prize.label}. "
        f"Try the spaghetti scene, where the mess can actually reach the prize.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a riverbank, spaghetti, and a small twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        tw = _safe_lookup(TWISTS, getattr(args, "twist", None)) if getattr(args, "twist", None) else TWISTS["reedtray"]
        if not reasonableness_gate(act, pr, tw):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "twist", None) is None or c[3] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, twist = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(FOX_NAMES + HERON_NAMES)
    companion = getattr(args, "companion", None) or rng.choice([n for n in FOX_NAMES + HERON_NAMES if n != name])
    helper = getattr(args, "helper", None) or rng.choice(TURTLE_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, twist=twist,
                       name=name, companion=companion, helper=helper, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    world.zone = set(activity.zone)
    if activity.id == "spaghetti":
        actor.memes["worry"] += 1
        actor.memes["rumpus"] += 1


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["saucy"] >= THRESHOLD and ("spill", actor.id) not in world.fired:
            world.fired.add(("spill", actor.id))
            actor.memes["rumpus"] += 1
            out.append(f"Their voices rose into a rumpus.")
        if actor.memes["blame"] >= THRESHOLD and ("blame", actor.id) not in world.fired:
            world.fired.add(("blame", actor.id))
            actor.memes["rumpus"] += 1
            out.append(f"Blame only made the rumpus louder.")
        if actor.memes["kindness"] >= THRESHOLD and ("calm", actor.id) not in world.fired:
            world.fired.add(("calm", actor.id))
            actor.memes["calm"] += 1
            actor.memes["rumpus"] = max(0.0, actor.memes["rumpus"] - 1.0)
            out.append(f"Kindness softened the fuss.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="fox" if params.name in FOX_NAMES else "heron"))
    companion = world.add(Entity(id=params.companion, kind="character", type="heron" if hero.type == "fox" else "fox"))
    helper = world.add(Entity(id=params.helper, kind="character", type="turtle"))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label,
                             phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=helper.id,
                             region=_safe_lookup(PRIZES, params.prize).region))
    twist = world.add(Entity(id=_safe_lookup(TWISTS, params.twist).id, type="tool", label=_safe_lookup(TWISTS, params.twist).label,
                             owner=helper.id, protective=True, covers={"chest"}))

    act = _safe_lookup(ACTIVITIES, params.activity)

    world.say(f"{_fable_voice(hero.type)} at {world.setting.place}.")
    world.say(
        f"{hero.id} and {companion.id} found {prize.phrase} beside the reeds, and both were eager for {act.gerund}."
    )

    world.para()
    world.say(
        f"They tried to {act.verb}, but the basket wobbled in the wind and the spaghetti slipped into the dirt."
    )
    _do_activity(world, hero, act)
    _do_activity(world, companion, act)
    hero.memes["blame"] += 1
    companion.memes["blame"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Their faces fell into a little rumpus. {hero.id} blamed the wind, and {companion.id} blamed the crumbs."
    )
    world.say(
        f"Then {helper.id} the turtle arrived with {params.trait} eyes and a calm shell."
    )
    helper.memes["kindness"] += 1

    world.para()
    world.say(
        f'"Let us {_safe_lookup(TWISTS, params.twist).prep}," {helper.id} said. '
        f"{hero.id} and {companion.id} listened."
    )
    twist.worn_by = helper.id
    if prize.region in twist.covers:
        world.say(f"Together they {_safe_lookup(TWISTS, params.twist).tail}.")
        helper.memes["calm"] += 1
        hero.memes["kindness"] += 1
        companion.memes["kindness"] += 1
        hero.memes["blame"] = 0.0
        companion.memes["blame"] = 0.0
        propagate(world)

    prize.meters["dirty"] += 1
    prize.meters["tidy"] += 1
    world.say(
        f"In the end, {hero.id} and {companion.id} ate spaghetti by the water while the dim old junk by the bank looked smaller after the cleaning."
    )

    world.facts.update(
        hero=hero, companion=companion, helper=helper, prize=prize, twist=twist, activity=act, params=params
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about "{f["activity"].keyword}", a riverbank, and a kind twist.',
        f"Tell a gentle story where {f['hero'].id} and {f['companion'].id} want to {f['activity'].verb} but a rumpus starts, then {f['helper'].id} helps.",
        f'Write a simple riverbank story that includes the word "{f["activity"].keyword}" and ends with a calmer picnic.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    twist = _safe_fact(world, f, "twist")
    return [
        QAItem(
            question=f"Who was the story about at the riverbank?",
            answer=f"It was about {hero.id}, with {companion.id} nearby and {helper.id} helping when the rumpus started.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} and {companion.id} tried to {act.verb}?",
            answer=f"The spaghetti slipped into the dirt, which made the picnic messy and started a rumpus.",
        ),
        QAItem(
            question=f"How did {helper.id} fix the rumpus?",
            answer=f"{helper.id} suggested {twist.label}, so they could share the spaghetti more calmly and clean the riverbank corner.",
        ),
        QAItem(
            question=f"What was special about the ending?",
            answer=f"The ending was calmer: the friends shared spaghetti by the water, and the junk-dim corner looked tidier.",
        ),
    ]


KNOWLEDGE = {
    "spaghetti": [
        ("What is spaghetti?", "Spaghetti is a long, thin pasta that people often eat with sauce."),
    ],
    "riverbank": [
        ("What is a riverbank?", "A riverbank is the land along the side of a river."),
    ],
    "twist": [
        ("What does it mean to twist something?", "To twist something is to turn it around and around."),
    ],
    "junk-dim": [
        ("What is junk?", "Junk is old or broken stuff that people do not use anymore."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["spaghetti", "riverbank", "twist", "junk-dim"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
spaghetti_scene(A) :- activity(A), A = spaghetti.
riverbank_scene(P) :- setting(P), P = riverbank.

at_risk(P, R) :- worn_on(P, R), splashes(spaghetti, R).
messy(A) :- activity(A), mess_of(A, saucy).

valid_story(P, A, Pr, T) :- riverbank_scene(P), spaghetti_scene(A),
                            prize(Pr), twist(T), at_risk(Pr, chest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


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


CURATED = [
    StoryParams(place="riverbank", activity="spaghetti", prize="sash", twist="reedtray",
                name="Finn", companion="Iris", helper="Sage", trait="patient"),
    StoryParams(place="riverbank", activity="spaghetti", prize="apron", twist="stoneplate",
                name="Wren", companion="Milo", helper="Otto", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
            print(json.dumps([asdict(s.params) | {"story": s.story, "prompts": s.prompts,
                                                  "story_qa": [asdict(q) for q in s.story_qa],
                                                  "world_qa": [asdict(q) for q in s.world_qa]}
                              for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
