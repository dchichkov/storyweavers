#!/usr/bin/env python3
"""
storyworlds/worlds/tuition_wily_movement_reconciliation_tall_tale.py
====================================================================

A small tall-tale storyworld about a child, a wily helper, a moving scheme,
and a reconciliation that pays the tuition.

Seed tale:
---
In a windy little river town, June wanted to keep going to Miss Della's school.
But the tuition bill came due, and June's aunt said the family could not spare
the coins. June felt tight in the chest. Then a wily old mule named Bramble
told a wild story about a movement show down at the fairground. If June and
Aunt Ruth could march, stomp, and clap in a fancy parade, the town crowd might
drop coins into a hat.

June first argued that the whole plan sounded too silly. Aunt Ruth said it sounded
too risky. But Bramble kept on winking and stepping sideways until they tried it.
They marched under lantern light, the crowd cheered, and the hat filled up.
By the end, June and Aunt Ruth were laughing together. They paid the tuition,
and the school door stayed open for another day.

World model:
---
- physical meters: coin, distance, dust, crowd_size
- emotional memes: worry, pride, harmony, stubbornness, relief, delight
- the wily helper proposes a movement-based money-making scheme
- the tension is over whether the tuition can be paid
- reconciliation happens when the scheme works and the family comes back together
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "aunt", "mother", "sister"}
        masculine = {"boy", "man", "uncle", "father", "brother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
    color: str
    tall_tale_detail: str
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
    payoff: str
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
    region: str = "torso"
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
class Helper:
    id: str
    label: str
    type: str
    scheme: str
    motion: str
    proof: str
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
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.motion: float = 0.0

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.motion = self.motion
        return w


SETTINGS = {
    "river_town": Setting(
        place="the river town",
        color="blue-gray",
        tall_tale_detail="the courthouse bell rang so hard the pigeons blinked",
    ),
    "fairground": Setting(
        place="the fairground",
        color="sunny gold",
        tall_tale_detail="the Ferris wheel creaked like it was remembering a bigger sky",
    ),
    "schoolhouse": Setting(
        place="the one-room schoolhouse",
        color="red-brick",
        tall_tale_detail="the chalk dust floated like it had a mind of its own",
    ),
}

ACTIVITIES = {
    "movement": Activity(
        id="movement",
        verb="put on a movement show",
        gerund="stomping, marching, and clapping",
        rush="stomp down the boardwalk and back",
        mess="dust",
        payoff="coins",
        keyword="movement",
        tags={"movement", "coins", "crowd"},
    ),
    "parade": Activity(
        id="parade",
        verb="lead a parade",
        gerund="parading with brass-step gusto",
        rush="march through the square",
        mess="dust",
        payoff="coins",
        keyword="parade",
        tags={"movement", "crowd"},
    ),
    "delivery": Activity(
        id="delivery",
        verb="carry produce up the hill",
        gerund="hauling baskets and barrels",
        rush="lug the baskets home",
        mess="dust",
        payoff="coins",
        keyword="hauling",
        tags={"work", "coins"},
    ),
}

PRIZES = {
    "tuition": Prize(
        label="tuition",
        phrase="the tuition bill",
        type="bill",
        region="torso",
    ),
    "fees": Prize(
        label="fees",
        phrase="the school fees envelope",
        type="bill",
        region="torso",
    ),
}

HELPERS = {
    "mule": Helper(
        id="mule",
        label="a wily old mule",
        type="mule",
        scheme="claim the town loves a grand movement show",
        motion="sidestep like a kettle on wheels",
        proof="the mule proved the crowd would clap for anything brave and lively",
    ),
    "crow": Helper(
        id="crow",
        label="a wily crow",
        type="crow",
        scheme="scatter shiny buttons to start a tip parade",
        motion="hop and bob like a black stitched shadow",
        proof="the crow proved even a small trick can get the whole lane looking up",
    ),
}

CHILD_NAMES = ["June", "Mabel", "Nell", "Tommy", "Willie", "Sadie"]
ADULT_NAMES = ["Aunt Ruth", "Uncle Ben", "Gran Ida", "Pa Amos"]
TRAITS = ["plucky", "curious", "stubborn", "bright-eyed", "spirited"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    helper: str
    name: str
    caretaker: str
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


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def predict(world: World, child: Entity, helper: Helper, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    sim.motion += 1.0
    c = sim.get(child.id)
    _add_meter(c, "dust", 1.0)
    _add_meme(c, "delight", 1.0)
    _add_meter(sim.get(prize.id), "coin", 3.0)
    return {
        "can_pay": sim.get(prize.id).meters.get("coin", 0.0) >= 3.0,
        "child_relief": c.memes.get("relief", 0.0),
    }


def argue(world: World, child: Entity, caretaker: Entity, prize: Entity, activity: Activity) -> None:
    _add_meme(child, "stubbornness", 1.0)
    _add_meme(caretaker, "worry", 1.0)
    world.say(
        f'{child.id} wanted to {activity.verb}, but {caretaker.label} frowned at the '
        f'{prize.label}. "That tuition bill is due today," {caretaker.pronoun()} said.'
    )
    world.say(
        f'{child.id} felt the wish bob up and down like a tin can in a creek, '
        f'but nobody had enough coin yet.'
    )


def wily_offer(world: World, helper: Helper, child: Entity, caretaker: Entity, activity: Activity) -> None:
    _add_meme(helper := world.get(helper.id), "wily", 1.0)
    world.say(
        f"Then {helper.label} came sidling in with a grin as crooked as a fishhook. "
        f'"{helper.scheme}," {helper.pronoun()} said.'
    )
    world.say(
        f'{helper.proof.capitalize()}, and the town lane went quiet enough to hear the horses think.'
    )


def reconciliation(world: World, child: Entity, caretaker: Entity, helper: Helper, activity: Activity, prize: Entity) -> None:
    _add_meter(child, "dust", 1.0)
    _add_meter(prize, "coin", 3.0)
    _add_meme(child, "relief", 1.0)
    _add_meme(caretaker, "harmony", 1.0)
    _add_meme(child, "harmony", 1.0)
    world.say(
        f'So {child.id} and {caretaker.label} tried the plan. They marched, stomped, '
        f'and clapped until their footsteps sounded bigger than church drums.'
    )
    world.say(
        f'The crowd laughed, cheered, and tossed coins by the handful. Soon the '
        f'{prize.label} was paid, and {child.id} could keep going to school.'
    )
    world.say(
        f'By the end, {child.id} leaned against {caretaker.label}, and the two of them '
        f'were laughing the same laugh. That was the kind of reconciliation that can '
        f'heal a whole windblown day.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, helper_def: Helper,
         name: str, caretaker_name: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(id=name, kind="character", type="girl" if name in {"June", "Mabel", "Nell", "Sadie"} else "boy"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type="aunt" if "Aunt" in caretaker_name else "uncle", label=caretaker_name))
    helper = world.add(Entity(id=helper_def.id, kind="character", type=helper_def.type, label=helper_def.label))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=caretaker.id))

    _add_meme(child, "hope", 1.0)
    _add_meme(caretaker, "worry", 1.0)

    world.say(
        f"In {setting.place}, where {setting.tall_tale_detail}, there lived a {trait} child named {child.id}."
    )
    world.say(
        f"{child.id} loved {activity.gerund}, and {caretaker.label} loved the school so much "
        f"that {caretaker.pronoun('possessive')} heart had a desk-shaped dent in it."
    )
    world.say(
        f"But the {prize.label} came due, and the family coin jar was as thin as a fence post in a drought."
    )

    world.para()
    argue(world, child, caretaker, prize, activity)
    wily_offer(world, helper, child, caretaker, activity)

    world.para()
    reconciliation(world, child, caretaker, helper, activity, prize)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        trait=trait,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            for prize_id in PRIZES:
                for helper_id in HELPERS:
                    if act.keyword in {"movement", "parade"} and prize_id == "tuition":
                        combos.append((setting_id, act_id, prize_id, helper_id))
    return combos


def explain_rejection(args: argparse.Namespace) -> str:
    return "No valid story: this world only works when a movement-style scheme can help pay tuition."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: tuition, a wily helper, movement, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker")
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[3] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, act_id, prize_id, helper_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, activity=act_id, prize=prize_id, helper=helper_id, name=name, caretaker=caretaker, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child about "{f["activity"].keyword}", tuition, and a wily helper.',
        f"Tell a story where {f['child'].id} and {f['caretaker'].label} disagree about the tuition bill, then reconcile after a wild movement scheme works.",
        f"Write a child-friendly tall tale that includes the words tuition, wily, and movement, and ends with the family made whole again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    caretaker: Entity = _safe_fact(world, f, "caretaker")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    helper: Entity = _safe_fact(world, f, "helper")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do in the story?",
            answer=f"{child.id} wanted to {activity.verb} and keep going to school.",
        ),
        QAItem(
            question=f"Why was {caretaker.label} worried about the plan?",
            answer=f"{caretaker.label} was worried because the tuition bill had to be paid first.",
        ),
        QAItem(
            question=f"Who brought the wily idea that changed the day?",
            answer=f"{helper.label} brought the wily movement idea and showed a way to earn coins.",
        ),
        QAItem(
            question=f"What got paid by the end of the story?",
            answer=f"The {prize.label} got paid, so {child.id} could keep going to school.",
        ),
        QAItem(
            question=f"How did {child.id} and {caretaker.label} feel at the end?",
            answer=f"They felt close again and shared a reconciliation after the plan worked.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tuition?",
            answer="Tuition is the money paid to attend a school or lessons.",
        ),
        QAItem(
            question="What does wily mean?",
            answer="Wily means clever in a sneaky or tricky way, like a fox that finds a smart shortcut.",
        ),
        QAItem(
            question="What is movement?",
            answer="Movement is the act of moving, marching, dancing, or changing place.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who disagreed make peace and feel friendly again.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(s) :- setting_fact(s).
activity(a) :- activity_fact(a).
prize(p) :- prize_fact(p).
helper(h) :- helper_fact(h).

valid(s,a,p,h) :- setting_fact(s), activity_fact(a), prize_fact(p), helper_fact(h),
                   activity_keyword(a,"movement"), prize_label(p,"tuition").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity_fact", aid))
        lines.append(asp.fact("activity_keyword", aid, a.keyword))
    for pid in PRIZES:
        lines.append(asp.fact("prize_fact", pid))
        lines.append(asp.fact("prize_label", pid, _safe_lookup(PRIZES, pid).label))
    for hid in HELPERS:
        lines.append(asp.fact("helper_fact", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(HELPERS, params.helper), params.name, params.caretaker, params.trait)
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
    StoryParams(setting="river_town", activity="movement", prize="tuition", helper="mule", name="June", caretaker="Aunt Ruth", trait="plucky"),
    StoryParams(setting="fairground", activity="parade", prize="tuition", helper="crow", name="Mabel", caretaker="Gran Ida", trait="spirited"),
    StoryParams(setting="schoolhouse", activity="movement", prize="fees", helper="mule", name="Tommy", caretaker="Uncle Ben", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
