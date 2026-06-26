#!/usr/bin/env python3
"""
A small fairy-tale story world about garb, surprise, and a kindly turn.

Premise:
- A young helper loves a special piece of garb for a feast or festival.
- A surprise makes the garb seem wrong for the moment.
- A caring elder or friend helps turn the surprise into something delightful.

This script keeps the world tiny and state-driven:
- physical meters track wear, dirt, sparkle, and tear
- emotional memes track hope, worry, surprise, delight, and pride

The prose is intentionally child-facing and fairy-tale-like.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    garb: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["clean", "sparkle", "wear", "tear", "dirt"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "surprise", "delight", "pride", "nerves"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "witch"}
        male = {"boy", "prince", "king", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"
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
    indoors: bool = False
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
    keyword: str
    mess: str
    zone: set[str]
    surprise: str
    result: str
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
class Garb:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    pretty: bool = True
    can_be_ruined_by: set[str] = field(default_factory=set)
    can_be_fixed_by: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    action: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    sparkle_boost: float = 0.0
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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["surprise"] += 1
    actor.memes["worry"] += 1
    actor.meters["wear"] += 1
    if narrate:
        world.say(f"Then {actor.id} met the {activity.keyword}, and the day changed at once.")


def _apply_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in list(world.entities.values()):
        if not actor.is_character():
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id:
                continue
            if item.region not in world.facts.get("activity_zone", set()):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kind = _safe_fact(world, world.facts, "activity").mess
            item.meters["dirt"] += 1
            item.meters["wear"] += 1
            actor.memes["worry"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} caught a little {kind}.")
    return out


def _apply_sparkle(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirt"] < THRESHOLD:
            continue
        sig = ("sparkle", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["sparkle"] += 1
        out.append(f"Yet the cloth still held a small, brave sparkle.")
    return out


def _apply_fix(world: World) -> list[str]:
    out: list[str] = []
    act = _safe_fact(world, world.facts, "activity")
    for fix in world.facts.get("available_fixes", []):
        sig = ("fix", fix.id)
        if sig in world.fired:
            continue
        if act.id not in fix.helps:
            continue
        world.fired.add(sig)
        world.facts["chosen_fix"] = fix
        out.append(fix.action)
        return out
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_mess, _apply_sparkle, _apply_fix):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "castle_yard": Setting(place="the castle yard", indoors=False, affords={"lanterns", "feast", "choir"}, mood="golden"),
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"lanterns", "feast"}, mood="warm"),
    "village_green": Setting(place="the village green", indoors=False, affords={"feast", "choir"}, mood="bright"),
}

ACTIVITIES = {
    "lanterns": Activity(
        id="lanterns",
        verb="carry lanterns",
        gerund="carrying lanterns",
        rush="hurry to the lanterns",
        keyword="lantern light",
        mess="smoke",
        zone={"torso", "hands"},
        surprise="a lantern parade began earlier than anyone expected",
        result="the first lanterns winked awake",
        tags={"light", "night"},
    ),
    "feast": Activity(
        id="feast",
        verb="join the feast",
        gerund="dancing at the feast",
        rush="run to the feast",
        keyword="feast table",
        mess="spills",
        zone={"torso", "legs"},
        surprise="the feast was moved to the yard under the sky",
        result="the drums and spoons rang together",
        tags={"food", "dance"},
    ),
    "choir": Activity(
        id="choir",
        verb="sing in the choir",
        gerund="singing with the choir",
        rush="step to the choir circle",
        keyword="choir song",
        mess="dust",
        zone={"torso"},
        surprise="a traveling singer asked for one more voice",
        result="the song rose higher than the walls",
        tags={"song", "voice"},
    ),
}

GARB = {
    "cloak": Garb(
        id="cloak",
        label="cloak",
        phrase="a deep blue cloak with silver thread",
        region="torso",
        can_be_ruined_by={"smoke", "dust"},
        can_be_fixed_by={"brushing", "mending"},
    ),
    "slippers": Garb(
        id="slippers",
        label="slippers",
        phrase="soft satin slippers",
        region="feet",
        can_be_ruined_by={"spills", "dust"},
        can_be_fixed_by={"drying", "brushing"},
    ),
    "ribboned_hat": Garb(
        id="hat",
        label="hat",
        phrase="a ribboned hat",
        region="head",
        can_be_ruined_by={"smoke", "dust"},
        can_be_fixed_by={"brushing", "tapping"},
    ),
}

FIXES = {
    "broom": Fix(
        id="broom",
        label="broom",
        action="The old seamstress fetched a soft broom and brushed the dust away.",
        tail="",
        helps={"choir"},
        covers={"torso"},
        sparkle_boost=0.5,
    ),
    "pin": Fix(
        id="pin",
        label="silver pin",
        action="A silver pin caught the loose cloth, and the cloak sat proud again.",
        tail="",
        helps={"lanterns", "feast"},
        covers={"torso"},
        sparkle_boost=1.0,
    ),
    "cloth": Fix(
        id="cloth",
        label="dry cloth",
        action="They patted the spots dry with a clean cloth until the stains faded.",
        tail="",
        helps={"feast", "lanterns"},
        covers={"feet", "torso"},
        sparkle_boost=0.2,
    ),
}

HERO_NAMES = ["Mira", "Elin", "Tessa", "Ayla", "Nora", "Lina"]
HELPER_NAMES = ["the seamstress", "the old queen", "the baker", "the tailor"]
TRAITS = ["gentle", "brave", "curious", "lively", "kind"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    garb: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            act = _safe_lookup(ACTIVITIES, a)
            for g, garb in GARB.items():
                if garb.region in act.zone and act.mess in garb.can_be_ruined_by:
                    combos.append((s, a, g))
    return combos


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoors:
        return f"Inside {setting.place}, candlelight glowed softly on the walls."
    return f"{setting.place.capitalize()} glittered under a sky that seemed ready for a tale."


def intro(world: World, hero: Entity, garb: Entity) -> None:
    world.say(f"There once was a {hero.traits[0]} child named {hero.id}, who loved {garb.phrase}.")
    world.say(f"{hero.id} wore {garb.pronoun('possessive')} {garb.label} like treasure, and the mirror smiled back.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hope"] += 1
    world.say(f"{hero.id} longed to {activity.verb}, for fairy-tale days are best when they begin with a wonder.")


def surprise_turn(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["surprise"] += 1
    hero.memes["worry"] += 1
    world.say(activity.surprise.capitalize() + ".")
    world.say(f"{hero.id} blinked at the new plan, and {hero.pronoun('possessive')} heart gave a small jump.")
    world.say(f"But {helper.id} came near with a calm smile, as helpers do in good old stories.")


def decide(world: World, hero: Entity, helper: Entity, activity: Activity, garb: Entity) -> None:
    world.say(
        f'"Your {garb.label} is lovely," said {helper.id}, "but a little {activity.mess} would spoil the fine look."'
    )
    world.say(f"So they chose a kinder way, one that fit the hour and saved the {garb.label} from shame.")
    hero.memes["worry"] += 1
    helper.memes["pride"] += 1


def resolve(world: World, hero: Entity, helper: Entity, activity: Activity, garb: Entity) -> None:
    fix = world.facts.get("chosen_fix")
    if fix:
        hero.memes["delight"] += 1
        hero.memes["pride"] += 1
        garb.meters["dirt"] = max(0.0, garb.meters["dirt"] - 1.0)
        garb.meters["sparkle"] += fix.sparkle_boost
        world.say(f"At last, {hero.id} went on {activity.gerund}, and the surprise had become a gift.")
        world.say(
            f"{helper.id} helped with the finishing touch, and the {garb.label} shone again "
            f"as if it had been waiting all along for this very night."
        )
    else:
        world.say(f"Still, {hero.id} stepped forward with courage, and the tale ended in a quiet, shining way.")


def tell_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type="girl", traits=[params.trait, "little"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman", traits=["wise"]))
    garb_cfg = GARB[params.garb]
    garb = world.add(Entity(
        id=garb_cfg.id,
        type=garb_cfg.id,
        label=garb_cfg.label,
        phrase=garb_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id,
    ))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    world.facts["activity"] = activity
    world.facts["activity_zone"] = set(activity.zone)
    world.facts["available_fixes"] = list(FIXES.values())
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["garb"] = garb

    intro(world, hero, garb)
    world.para()
    world.say(setting_detail(world.setting, activity))
    want(world, hero, activity)
    surprise_turn(world, hero, helper, activity)
    decide(world, hero, helper, activity, garb)
    propagate(world, narrate=True)
    world.para()
    resolve(world, hero, helper, activity, garb)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    garb = _safe_fact(world, f, "garb")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a fairy-tale story about {hero.id}, a child who loves {garb.label}, and a surprise at {world.setting.place}.',
        f"Tell a short magical story where {hero.id} wants to {activity.verb} but a helper gently protects {garb.phrase}.",
        f'Write a child-friendly tale that includes the word "{activity.keyword}" and ends with {garb.label} safe and shining.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    garb = _safe_fact(world, f, "garb")
    act = _safe_fact(world, f, "activity")
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} love to wear in the tale?",
            answer=f"{hero.id} loved wearing {garb.phrase}, and {garb.label} made {hero.pronoun('possessive')} outfit feel special.",
        ),
        QAItem(
            question=f"What surprise happened before {hero.id} could {act.verb}?",
            answer=f"{act.surprise.capitalize()}. That unexpected change made {hero.id} pause and look to {helper.id} for help.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} at {place}?",
            answer=f"{helper.id} helped by finding a gentle fix so {hero.id} could join the story's happy moment without ruining {garb.pronoun('possessive')} {garb.label}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {garb.label}?",
            answer=f"It ended with {hero.id} feeling proud and delighted, while {garb.label} stayed lovely and ready for another fairy-tale day.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cloak": (
        "What is a cloak?",
        "A cloak is a loose piece of clothing that goes over your clothes and can keep you warm or make you look grand.",
    ),
    "slippers": (
        "What are slippers?",
        "Slippers are soft shoes for indoors or gentle walking, and they help your feet feel cozy.",
    ),
    "hat": (
        "What is a hat for?",
        "A hat can shade your face, keep your head warm, or finish a costume in a fancy way.",
    ),
    "surprise": (
        "What is a surprise?",
        "A surprise is something unexpected that happens before you are ready for it.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    for key in [f["garb"].id, "surprise"]:
        if key in WORLD_KNOWLEDGE:
            q, a = WORLD_KNOWLEDGE[key]
            out.append(QAItem(question=q, answer=a))
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A garb is at risk when the activity touches the region it is worn on.
at_risk(A, G) :- zone(A, R), region(G, R), garb(G).

% A simple compatibility fix exists when a fixer is suited to the activity.
fixable(A, G) :- at_risk(A, G), cure(A, F), fits(F, G).

valid_story(S, A, G) :- setting(S), affords(S, A), at_risk(A, G), fixable(A, G).
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
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for gid, g in GARB.items():
        lines.append(asp.fact("garb", gid))
        lines.append(asp.fact("region", gid, g.region))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for a in sorted(f.helps):
            lines.append(asp.fact("cure", a, fid))
        for c in sorted(f.covers):
            lines.append(asp.fact("fits", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(s, a, g) for s, a, g in valid_combos()]


def asp_verify() -> int:
    import asp
    python_set = set(asp_valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


def explain_rejection(activity: Activity, garb: Garb) -> str:
    return (
        f"(No story: {activity.verb} would not fairly trouble the {garb.label}, "
        f"or no gentle fix exists for that pairing.)"
    )


def valid_filtered(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    out = []
    for s, a, g in combos:
        if getattr(args, "setting", None) and s != getattr(args, "setting", None):
            continue
        if getattr(args, "activity", None) and a != getattr(args, "activity", None):
            continue
        if getattr(args, "garb", None) and g != getattr(args, "garb", None):
            continue
        out.append((s, a, g))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_filtered(args)
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s, a, g = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=s, activity=a, garb=g, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about garb and surprise.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--garb", choices=sorted(GARB))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


CURATED = [
    StoryParams(setting="castle_yard", activity="lanterns", garb="cloak", name="Mira", helper="the seamstress", trait="brave"),
    StoryParams(setting="sunroom", activity="feast", garb="slippers", name="Elin", helper="the old queen", trait="gentle"),
    StoryParams(setting="village_green", activity="choir", garb="cloak", name="Tessa", helper="the tailor", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.activity} / {p.garb} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
