#!/usr/bin/env python3
"""
storyworlds/worlds/rev_twist_fable.py
=====================================

A small fable-style storyworld about a quick little rev, a careful twist,
and a wiser ending.

Premise:
- A young woodland helper loves to rev a tiny hand-crank machine.
- The machine can make good things, but if it is used too fast, it can spill,
  scatter, or frighten the smaller creatures nearby.
- A mentor sees the risk and offers a twist: not a punishment, but a safer way
  to use the same tool.

This world keeps the tone close to a fable:
- simple animal characters
- a concrete problem
- a turn of thought
- a gentle moral image at the end

The simulated state tracks:
- physical meters: speed, spill, dust, smoothness, safety, order
- emotional memes: pride, worry, patience, joy, trust, relief

The "rev" seed word appears in the story as the action that creates the tension.
The "Twist" feature appears as the turn: a clever twist of the lever, rope,
or latch changes the outcome without changing the heart of the story.
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
SAFE_SPEED = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    risk_meter: object | None = None
    hero: object | None = None
    mentor: object | None = None
    prize: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for key in ("speed", "spill", "dust", "smoothness", "safety", "order"):
            self.meters.setdefault(key, 0.0)
        for key in ("pride", "worry", "patience", "joy", "trust", "relief", "curiosity"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "hen"}
        male = {"boy", "father", "dad", "man", "brother", "rooster"}
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
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
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
    risk: str
    effect: str
    keyword: str
    mess: str
    zone: set[str] = field(default_factory=set)
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
    risk_meter: str
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
    prep: str
    tail: str
    guards: set[str]
    fixes: set[str]
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
        self.trace_log: list[str] = []

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

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind != "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _apply_rev(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["speed"] < THRESHOLD:
            continue
        for item in world.things():
            if item.owner != hero.id:
                continue
            sig = ("rev", hero.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["speed"] += 1
            item.meters["spill"] += 1
            hero.memes["pride"] += 1
            out.append(f"The {item.label} shook and spun too fast.")
    return out


def _apply_spill(world: World) -> list[str]:
    out: list[str] = []
    for item in world.things():
        if item.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["order"] += 1
        item.meters["safety"] -= 1
        out.append(f"That could make a mess if no one steadied it.")
    return out


def _apply_worry(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["curiosity"] < THRESHOLD:
            continue
        if hero.meters["speed"] < THRESHOLD:
            continue
        sig = ("worry", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] += 1
        out.append(f"A wise friend noticed the rush and grew concerned.")
    return out


CAUSAL_RULES = [_apply_rev, _apply_spill, _apply_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_of(activity: Activity, prize: Prize) -> bool:
    return prize.risk_meter in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.risk_meter in gear.fixes:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "rabbit",
         mentor_name: str = "Wren", mentor_type: str = "owl",
         trait: str = "eager") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", trait, "quick"],
    ))
    mentor = world.add(Entity(
        id=mentor_name, kind="character", type=mentor_type,
        traits=["wise", "calm"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id,
        risk_meter=prize_cfg.risk_meter, plural=prize_cfg.plural,
    ))
    tool = world.add(Entity(
        id="tool", kind="thing", type="tool", label="little hand-crank",
        phrase="a little hand-crank machine", owner=hero.id,
    ))

    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"At {setting.place}, little {hero.id} loved to {activity.verb}. "
        f"{hero.pronoun().capitalize()} thought the world was most fun when it moved."
    )
    world.say(
        f"{hero.id} also had {hero.pronoun('possessive')} {prize.label}, which stayed close "
        f"whenever {hero.id} worked the {tool.label}."
    )

    world.para()
    world.say(
        f"One bright morning, {hero.id} wanted to {activity.verb} again. "
        f"{hero.pronoun().capitalize()} leaned in and began to {activity.rush}."
    )
    hero.meters["speed"] += 1
    tool.used_by = hero.id
    propagate(world, narrate=True)

    if activity.id == "rev":
        world.say(
            f"The crank began to rev, and the little machine hummed like a buzzing bee."
        )
    else:
        world.say(f"{activity.effect}.")

    world.para()
    if risk_of(activity, prize):
        world.say(
            f"{mentor.id} saw {prize.label} wobble and said, "
            f'"Careful now. {prize.label.capitalize()} can get {activity.risk}."'
        )
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} paused, because {hero.id} did not want {prize.label} ruined."
        )
        gear = select_gear(activity, prize)
        if gear is not None:
            world.say(
                f"{mentor.id} smiled and offered a twist: "
                f'"How about we {gear.prep}?"'
            )
            hero.memes["trust"] += 1
            hero.memes["patience"] += 1
            hero.meters["speed"] = 0.0
            prize.meters["safety"] += 1
            tool.meters["smoothness"] += 1
            world.say(
                f"{hero.id} gave the lever a small twist and listened. "
                f"The machine slowed, and the work became neat instead of wild."
            )
            world.say(
                f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, "
                f"and {mentor.id} was pleased to see a fast heart choose a careful hand."
            )
            hero.memes["joy"] += 1
            hero.memes["relief"] += 1
        else:
            world.say(
                f"No safe twist was needed for this one, so {mentor.id} simply helped "
                f"{hero.id} slow down."
            )
    else:
        world.say(
            f"{mentor.id} watched and nodded, because this kind of play did not trouble {prize.label}."
        )
        hero.memes["joy"] += 1
        hero.meters["speed"] = 0.0
        world.say(
            f"{hero.id} kept going, and the morning stayed light and peaceful."
        )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        prize=prize,
        tool=tool,
        activity=activity,
        setting=setting,
        resolved=True,
        gear=select_gear(activity, prize),
    )
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"rev", "twist"}, mood="bright"),
    "barnyard": Setting(place="the barnyard", affords={"rev", "twist"}, mood="dusty"),
    "riverside": Setting(place="the riverside path", affords={"rev", "twist"}, mood="windy"),
}

ACTIVITIES = {
    "rev": Activity(
        id="rev",
        verb="rev the little hand-crank",
        gerund="reving the little hand-crank",
        rush="spin the handle faster and faster",
        risk="shaken",
        effect="The whole machine hummed and clicked.",
        keyword="rev",
        mess="speed",
        zone={"speed"},
        tags={"rev", "speed", "machine"},
    ),
    "twist": Activity(
        id="twist",
        verb="twist the latch",
        gerund="twisting the latch",
        rush="turn the latch all at once",
        risk="jarred",
        effect="The latch settled into place with a tiny click.",
        keyword="Twist",
        mess="order",
        zone={"order"},
        tags={"twist", "order", "fix"},
    ),
}

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a berry basket",
        type="basket",
        risk_meter="spill",
        plural=False,
    ),
    "cups": Prize(
        label="cups",
        phrase="three little cups",
        type="cups",
        risk_meter="spill",
        plural=True,
    ),
    "jamjar": Prize(
        label="jam jar",
        phrase="a glass jam jar",
        type="jar",
        risk_meter="spill",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="slow-rope",
        label="a slow rope",
        prep="tie the rope to the crank and let it turn in a calm circle",
        tail="used the slow rope to keep the wheel from racing",
        guards={"speed"},
        fixes={"spill"},
    ),
    Gear(
        id="soft-latch",
        label="a soft latch",
        prep="twist the soft latch halfway before the handle moved",
        tail="kept the machine steady with the soft latch",
        guards={"order"},
        fixes={"spill"},
    ),
]

HERO_NAMES = ["Milo", "Pip", "Nina", "Tess", "Robin", "Ivy"]
MENTOR_NAMES = ["Wren", "Owl", "Moss", "Brim"]
TRAITS = ["eager", "curious", "bold", "bright", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if risk_of(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    mentor: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, act, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    return [
        f'Write a short fable for a child about "{act.keyword}" and a wise choice.',
        f"Tell a woodland story where {hero.id} wants to {act.verb} at {world.setting.place} "
        f"but {mentor.id} worries about {prize.label}.",
        f'Write a gentle tale that includes the word "{act.keyword}" and ends with a safer, clever twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, act, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    gear = f.get("gear")
    qs = [
        QAItem(
            question=f"Who wanted to {act.verb} at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {mentor.id} worry about {prize.label}?",
            answer=f"{mentor.id} worried because {prize.label} could get {act.risk} if the machine moved too fast.",
        ),
    ]
    if gear:
        qs.append(
            QAItem(
                question=f"What twist helped the story end well?",
                answer=f"They used {gear.label} so the machine could stay safe while {hero.id} kept working.",
            )
        )
    qs.append(
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved after choosing the careful way.",
        )
    )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that shows a wise lesson.",
        ),
        QAItem(
            question="What does it mean to twist something?",
            answer="To twist something is to turn it around or give it a turning motion.",
        ),
        QAItem(
            question="What does rev mean?",
            answer="To rev means to make a machine or engine turn quickly and make a buzzing sound.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", activity="rev", prize="basket", name="Milo", mentor="Wren", trait="eager"),
    StoryParams(place="barnyard", activity="twist", prize="cups", name="Pip", mentor="Owl", trait="curious"),
    StoryParams(place="riverside", activity="rev", prize="jamjar", name="Nina", mentor="Moss", trait="bright"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risk_on(P,R), zone(A,R).
needs_gear(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), fixes(G,F), risk_on(P,F).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), needs_gear(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risk_on", pid, p.risk_meter))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for x in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, x))
        for x in sorted(g.fixes):
            lines.append(asp.fact("fixes", g.id, x))
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
    print("MISMATCH between clingo and Python gate:")
    print(" only python:", sorted(py - cl))
    print(" only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world of revs and twists.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--mentor")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would not honestly threaten {prize.label}, "
        f"so there is no real fable to tell here.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (risk_of(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        mentor=getattr(args, "mentor", None) or rng.choice(MENTOR_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        hero_name=params.name,
        mentor_name=params.mentor,
        trait=params.trait,
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
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
        for place, act, prize in triples:
            genders = sorted(g for (p, a, pr, g) in stories if (p, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:6} {prize:8} [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
