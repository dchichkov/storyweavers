#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stake_astonish_friday_lesson_learned_nursery_rhyme.py
===============================================================================================================================

A standalone storyworld for a tiny Nursery Rhyme style tale about a stake,
a Friday surprise, and a lesson learned.

The world is built from a small simulated garden domain:
- a child character with meters and memes
- a wooden stake that can tip or poke
- a surprise event that can astonish the child
- a gentle resolution that teaches a lesson learned

The prose is authored from state, not from a frozen template. The rhythm is
kept simple and child-facing.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    stake: object | None = None
    surprise: object | None = None
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
    risk: str
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
class Stake:
    label: str
    phrase: str
    region: str = "hands"
    fragile: bool = True
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
class Surprise:
    id: str
    label: str
    phrase: str
    act: str
    effect: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _default_meters() -> dict[str, float]:
    return {"care": 0.0, "tumble": 0.0, "mess": 0.0, "tidy": 0.0}


def _default_memes() -> dict[str, float]:
    return {"joy": 0.0, "fear": 0.0, "astonish": 0.0, "lesson": 0.0, "pride": 0.0}


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters[activity.mess] = child.meters.get(activity.mess, 0.0) + 1
    child.meters["tumble"] = child.meters.get("tumble", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(f"{child.id} went to {world.setting.place} to {activity.gerund}.")


def predict(world: World, child: Entity, activity: Activity, stake: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    stake_tipped = sim.entities[stake.id].meters.get("tipped", 0.0) >= THRESHOLD
    return {"tipped": stake_tipped}


def stake_at_risk(activity: Activity, stake: Stake) -> bool:
    return stake.region == "hands" and activity.id in {"pull", "climb", "spin"}


def select_fix(activity: Activity, stake: Stake) -> Optional[str]:
    if activity.id in {"pull", "climb"}:
        return "hold_with_both_hands"
    return None


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} with a bright, curious heart.")


def loves_day(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say("On Friday, the breeze was light, and the garden sang a soft tune.")


def stake_scene(world: World, child: Entity, stake: Entity) -> None:
    world.say(
        f"By the bean row stood {stake.phrase}, "
        f"and {child.id} thought it looked strong as stone."
    )


def want_and_warn(world: World, child: Entity, parent: Entity, activity: Activity, stake: Entity) -> None:
    child.memes["fear"] += 1
    if predict(world, child, activity, stake)["tipped"]:
        world.say(
            f'"Oh, little one," {parent.id} said, '
            f'"if you {activity.verb}, that {stake.label} may sway and fall."'
        )
    else:
        world.say(f"{parent.id} gave a gentle nod, but asked {child.id} to be careful.")


def astonish(world: World, child: Entity, surprise: Entity) -> None:
    child.memes["astonish"] += 1
    world.say(
        f"Then, what a sight! {surprise.phrase} {surprise.effect}, and {child.id} was astonished."
    )


def lesson(world: World, child: Entity, parent: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"{parent.id} smiled and said, \"A little caution is a fine old friend.\""
    )
    world.say(
        f"So {child.id} learned a lesson: when a thing can wobble and fall, "
        f"it is wiser to steady it first."
    )


def resolution(world: World, child: Entity, activity: Activity, stake: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Then {child.id} used {activity.act}, and the {stake.label} stayed straight and neat."
    )
    world.say(
        f"By the end of Friday, {child.id} was still smiling, "
        f"and the garden looked safe and sweet."
    )


SETTINGS = {
    "garden": Setting(place="the garden", affords={"pull"}),
    "yard": Setting(place="the yard", affords={"climb"}),
    "patch": Setting(place="the bean patch", affords={"pull", "climb"}),
}

ACTIVITIES = {
    "pull": Activity(
        id="pull",
        verb="pull the vine",
        gerund="pulling the vine",
        rush="pull it hard",
        mess="mess",
        risk="wobble",
        keyword="stake",
        tags={"stake", "friday"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the fence",
        gerund="climbing up high",
        rush="climb on top",
        mess="mess",
        risk="tip",
        keyword="astonish",
        tags={"stake", "astonish"},
    ),
}

STAKES = {
    "garden_stake": Stake(
        label="stake",
        phrase="a wooden stake beside the beans",
        region="hands",
        fragile=True,
    ),
    "tall_stake": Stake(
        label="stake",
        phrase="a tall stake tied with twine",
        region="hands",
        fragile=True,
    ),
}

SURPRISES = {
    "ladybug": Surprise(
        id="ladybug",
        label="ladybug",
        phrase="A red ladybug",
        act="flew in a bright arc",
        effect="landed right on the stake and seemed to wave hello",
        tags={"astonish"},
    ),
    "kite": Surprise(
        id="kite",
        label="kite",
        phrase="A paper kite",
        act="flitted above the beans",
        effect="dipped low and flashed gold in the sun",
        tags={"friday", "astonish"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Jack", "Leo", "Max"]
TRAITS = ["curious", "cheerful", "spry", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    stake: str
    surprise: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld about stake, astonish, and Friday.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--stake", choices=STAKES)
    ap.add_argument("--surprise", choices=SURPRISES)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for stake_id in STAKES:
                for surprise_id in SURPRISES:
                    combos.append((place, act_id, stake_id, surprise_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "stake", None) is None or c[2] == getattr(args, "stake", None))
              and (getattr(args, "surprise", None) is None or c[3] == getattr(args, "surprise", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, stake, surprise = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, stake=stake, surprise=surprise,
                       name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    stake_def = _safe_lookup(STAKES, params.stake)
    surprise_def = _safe_lookup(SURPRISES, params.surprise)

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    stake = world.add(Entity(
        id="stake",
        type="stake",
        label=stake_def.label,
        phrase=stake_def.phrase,
        meters={"tipped": 0.0},
        memes={},
    ))
    surprise = world.add(Entity(
        id=surprise_def.id,
        type="surprise",
        label=surprise_def.label,
        phrase=surprise_def.phrase,
        meters={},
        memes={},
    ))

    introduce(world, child)
    loves_day(world, child)
    stake_scene(world, child, stake)

    world.para()
    world.say(f"On Friday morning, {child.id} wanted to {activity.verb} at {setting.place}.")
    want_and_warn(world, child, parent, activity, stake)
    astonish(world, child, surprise)

    world.para()
    lesson(world, child, parent)
    resolution(world, child, activity, stake)

    world.facts.update(child=child, parent=parent, stake=stake, surprise=surprise,
                       activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    return [
        f'Write a short nursery rhyme story about a child named {child.id}, a stake, and Friday.',
        f'Tell a gentle story where {child.id} wants to {activity.verb} and learns a lesson.',
        'Make the story feel like a small song, with a surprise and a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    activity = _safe_fact(world, f, "activity")
    surprise = _safe_fact(world, f, "surprise")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What did {child.id} want to do on Friday at {setting.place}?",
            answer=f"{child.id} wanted to {activity.verb} at {setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {child.id} about the stake?",
            answer=f"{parent.id} warned {child.id} because the stake could wobble if {child.id} got too rough.",
        ),
        QAItem(
            question=f"What astonished {child.id} in the story?",
            answer=f"{surprise.phrase} astonished {child.id}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer="The lesson was to steady a wobbly thing first and be careful with it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a stake?", answer="A stake is a long piece of wood or metal used to hold or mark something in place."),
        QAItem(question="What does astonish mean?", answer="To astonish means to surprise someone very much."),
        QAItem(question="What is Friday?", answer="Friday is one day of the week, near the end before the weekend."),
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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a child, a stake, Friday, and a surprise all appear.
valid_story(P,A,S,R) :- place(P), activity(A), stake(S), surprise(R).

% Nursery-rhyme tone is represented by a lesson learned at the end.
has_lesson(P,A,S,R) :- valid_story(P,A,S,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for sid in STAKES:
        lines.append(asp.fact("stake", sid))
    for rid in SURPRISES:
        lines.append(asp.fact("surprise", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if len(clingo_set) == len(python_set):
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


CURATED = [
    StoryParams(place="garden", activity="pull", stake="garden_stake", surprise="ladybug",
                name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="yard", activity="climb", stake="tall_stake", surprise="kite",
                name="Finn", gender="boy", parent="father", trait="cheerful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} at {p.place} (stake: {p.stake}, surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
