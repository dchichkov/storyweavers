#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/egg_dim_oodles_medal_reconciliation_friendship_cautionary.py
===============================================================================================================

A small Adventure-style storyworld about a cautious expedition, a friendship rift,
and a reconciliation after a medal-worthy rescue.

Seed tale:
---
A child and a friend go on a short adventure to a bright trail. They carry a tiny
egg for a trail beacon, have oodles of snacks, and hope to win a shiny medal at
the lookout. On the way, someone rushes ahead, the egg cracks, and the friend feels
blamed. A careful helper notices the danger, shares the oodles of snacks, and the
pair reconcile before the medal ceremony.

The world model tracks:
- physical meters: distance, crack, spill, supplies, fatigue, medal_presence
- emotional memes: trust, worry, anger, friendship, caution, gratitude, pride

The story generator uses those state changes to narrate a full beginning, turn,
and ending image, with reconciliation and friendship restored after a cautionary
lesson.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    egg: object | None = None
    friend: object | None = None
    hero: object | None = None
    medal: object | None = None
    snack: object | None = None
    def __post_init__(self) -> None:
        for key in ("distance", "crack", "spill", "supplies", "fatigue", "medal_presence"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "worry", "anger", "friendship", "caution", "gratitude", "pride"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    terrain: str
    feature: str
    allows: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    risk_region: str
    mess_kind: str
    safe_plan: str
    plural: bool = False
    answer: str = ""
    question: str = ""
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    caution: str
    mess: str
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
class Token:
    id: str
    label: str
    phrase: str
    reward: str
    requires_caution: bool = True
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
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.action_zone: set[str] = set()
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.lines = [[]]
        c.action_zone = set(self.action_zone)
        return c


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["spill"] < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            if item.risk_region not in world.action_zone:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["spill"] += 1
            item.meters["crack"] += 1 if item.id == "egg" else 0
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got damaged.")
    return out


def _r_fatigue(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["fatigue"] < THRESHOLD:
            continue
        sig = ("fatigue", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"{actor.id} started to feel tired and worried.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["anger"] < THRESHOLD or actor.memes["blamed"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["friendship"] -= 1
        actor.memes["worry"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_fatigue,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_reach_medal(action: Action, token: Token) -> bool:
    return token.id == "medal" and action.id in {"trail", "bridge", "lookout"}


def select_reconciliation_plan(action: Action, item: Item) -> Optional[str]:
    if action.mess != item.mess_kind:
        return None
    return item.safe_plan


def predict_damage(world: World, actor: Entity, action: Action, item_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    item = sim.entities[item_id]
    return {
        "damaged": item.meters["crack"] >= THRESHOLD or item.meters["spill"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.action_zone = set(action.zone)
    actor.meters["distance"] += 1
    actor.meters["spill"] += 1 if action.id == "rush" else 0
    actor.meters["fatigue"] += 1 if action.id in {"trail", "bridge"} else 0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} and {friend.id} were two friends with oodles of courage, ready for a small adventure."
    )


def setup(world: World, hero: Entity, friend: Entity, item: Entity, token: Token) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"They carried {hero.pronoun('possessive')} {item.label} and hoped the lookout would give them {token.reward}."
    )


def journey(world: World, hero: Entity, friend: Entity, action: Action, item: Entity) -> None:
    world.say(
        f"At {world.setting.place}, the trail was {world.setting.terrain} and {world.setting.feature} shone ahead like a clue."
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, while {friend.id} preferred to move with {action.caution}."
    )
    pred = predict_damage(world, hero, action, item.id)
    world.facts["predicted_damage"] = pred["damaged"]
    world.facts["predicted_worry"] = pred["worry"]
    if pred["damaged"]:
        world.say(
            f"{friend.id} warned, \"Careful—{action.mess} can crack a tiny egg and turn a good trip into a gloomy one.\""
        )


def conflict(world: World, hero: Entity, friend: Entity, action: Action, item: Entity) -> None:
    if world.facts.get("predicted_damage"):
        hero.memes["anger"] += 1
        hero.memes["blamed"] += 1
        friend.memes["worry"] += 1
        world.say(
            f"{hero.id} rushed ahead anyway, and the little egg slipped from {hero.pronoun('possessive')} hands."
        )
        world.say(f"It cracked open, and the two friends fell silent.")


def reconcile(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["anger"] = 0.0
    hero.memes["worry"] += 1
    friend.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"Then {friend.id} shared {friend.pronoun('possessive')} oodles of snacks and said sorry for not explaining the danger sooner."
    )
    world.say(
        f"{hero.id} listened, apologized for rushing, and the friends made up before the lookout."
    )


def finish(world: World, hero: Entity, friend: Entity, token: Token, item: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"At last they reached the lookout and earned the {token.label} for careful teamwork."
    )
    world.say(
        f"The tiny egg stayed in its shell, the oodles of snacks were still plenty, and the friendship felt stronger than before."
    )


def tell(setting: Setting, action: Action, item_cfg: Item, token: Token,
         hero_name: str = "Mina", friend_name: str = "Joss") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy"))
    egg = world.add(Entity(id="egg", label="tiny egg", phrase="a tiny egg", kind="thing", type="egg"))
    snack = world.add(Entity(id="snacks", label="oodles of snacks", phrase="oodles of snacks", kind="thing", type="snacks", plural=True))
    medal = world.add(Entity(id="medal", label="medal", phrase="a shiny medal", kind="thing", type="medal"))
    item = egg if item_cfg.id == "egg" else egg
    snack.carried_by = hero.id
    egg.carried_by = hero.id
    medal.meters["medal_presence"] = 1

    introduce(world, hero, friend)
    setup(world, hero, friend, item, token)
    world.para()
    journey(world, hero, friend, action, item)
    conflict(world, hero, friend, action, item)
    world.para()
    reconcile(world, hero, friend, item)
    finish(world, hero, friend, token, item)

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        snack=snack,
        medal=medal,
        action=action,
        setting=setting,
        token=token,
        resolved=True,
    )
    return world


SETTINGS = {
    "trailhead": Setting(place="the trailhead", terrain="dim and narrow", feature="a mossy sign", allows={"trail", "rush"}),
    "bridge": Setting(place="the old bridge", terrain="wobbly", feature="the river below", allows={"bridge", "rush"}),
    "lookout": Setting(place="the lookout hill", terrain="steep but bright", feature="a silver wind vane", allows={"trail", "lookout"}),
}

ACTIONS = {
    "trail": Action(
        id="trail",
        verb="hurry along the trail",
        gerund="hurrying along the trail",
        rush="dash ahead",
        caution="careful steps",
        mess="bump",
        zone={"hands", "pack"},
        keyword="trail",
        tags={"adventure", "cautionary"},
    ),
    "bridge": Action(
        id="bridge",
        verb="cross the bridge too fast",
        gerund="crossing the bridge",
        rush="run across",
        caution="slow balance",
        mess="jolt",
        zone={"hands", "pack"},
        keyword="bridge",
        tags={"adventure", "cautionary"},
    ),
    "lookout": Action(
        id="lookout",
        verb="climb up to the lookout",
        gerund="climbing to the lookout",
        rush="scramble upward",
        caution="steady breathing",
        mess="tumble",
        zone={"pack", "hands"},
        keyword="lookout",
        tags={"adventure", "cautionary", "medal"},
    ),
}

ITEMS = {
    "egg": Item(
        id="egg",
        label="tiny egg",
        phrase="a tiny egg",
        risk_region="hands",
        mess_kind="bump",
        safe_plan="hold it in a padded pocket",
    ),
}

TOKENS = {
    "medal": Token(
        id="medal",
        label="medal",
        phrase="a bright medal",
        reward="a bright medal",
    )
}

GIRL_NAMES = ["Mina", "Tia", "Rosa", "Ari", "Nina", "Lina", "Suri"]
BOY_NAMES = ["Joss", "Rey", "Tobin", "Eli", "Nico", "Pax", "Bram"]


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    token: str
    name: str
    friend: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.allows:
            for item_id, item in ITEMS.items():
                act = _safe_lookup(ACTIONS, act_id)
                if item.risk_region in act.zone or item_id == "egg":
                    combos.append((place, act_id, item_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    act = _safe_fact(world, f, "action")
    return [
        f'Write a short Adventure story for a child where {hero.id} and {friend.id} keep oodles of snacks safe while seeking a medal.',
        f"Tell a cautionary friendship story in which a tiny egg and a hurried choice create trouble, then reconciliation fixes it.",
        f'Write a story using the words "egg", "oodles", and "medal" where friends learn to slow down and help each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    act = _safe_fact(world, f, "action")
    item = _safe_fact(world, f, "item")
    token = _safe_fact(world, f, "token")
    qa = [
        QAItem(
            question=f"Who went on the adventure to {act.verb} and earn the {token.label}?",
            answer=f"{hero.id} and {friend.id} went together, carrying {hero.pronoun('possessive')} {item.label} and hoping for {token.reward}.",
        ),
        QAItem(
            question="What made the trip turn into a cautionary problem?",
            answer="The problem was that {0.id} rushed ahead, the tiny egg got cracked, and the friends felt upset for a moment.".format(hero),
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"{friend.id} shared {friend.pronoun('possessive')} oodles of snacks, apologized, and {hero.id} said sorry too. After that, their friendship felt stronger.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The friends made up, kept going carefully, and won the {token.label} without losing their kindness to each other.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an egg?", answer="An egg is a small shell that can crack if it is dropped or bumped hard."),
        QAItem(question="What are oodles?", answer="Oodles means a lot or plenty, like having more than enough snacks."),
        QAItem(question="What is a medal?", answer="A medal is a prize you can wear or hold to show someone did something well."),
        QAItem(question="What does caution mean?", answer="Caution means being careful so you can avoid trouble and stay safe."),
        QAItem(question="What does friendship mean?", answer="Friendship means caring about someone, helping them, and staying kind even when things go wrong."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means making up after a disagreement and becoming friendly again."),
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
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="trailhead", action="trail", item="egg", token="medal", name="Mina", friend="Joss"),
    StoryParams(place="bridge", action="bridge", item="egg", token="medal", name="Tia", friend="Rey"),
    StoryParams(place="lookout", action="lookout", item="egg", token="medal", name="Rosa", friend="Pax"),
]


def explain_rejection(action: Action) -> str:
    return f"(No story: the chosen action '{action.verb}' does not fit this cautionary adventure world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zones", aid, r))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk_region", iid, item.risk_region))
        lines.append(asp.fact("mess_kind", iid, item.mess_kind))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        if t.requires_caution:
            lines.append(asp.fact("cautionary_token", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Item) :- allows(Place, Act), action(Act), item(Item), risk_region(Item, R), zones(Act, R).
story(Place, Act, Item) :- valid(Place, Act, Item), cautionary_token("medal").
#show valid/3.
#show story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: egg, oodles, medal, reconciliation, friendship, cautionary.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(BOY_NAMES)
    return StoryParams(place=place, action=action, item=item, token="medal", name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(ITEMS, params.item), _safe_lookup(TOKENS, params.token), params.name, params.friend)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name} at {p.place} ({p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
