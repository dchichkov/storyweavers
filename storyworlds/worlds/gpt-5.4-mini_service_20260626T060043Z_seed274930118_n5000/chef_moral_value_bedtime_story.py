#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chef_moral_value_bedtime_story.py
===============================================================================================================

A small bedtime-story world about a chef, a warm kitchen, and a moral value
that changes what happens at the end.

The simulated premise is simple:
- A chef prepares a gentle bedtime snack or supper.
- Something tempting or worrisome happens.
- A child, guest, or helper is affected.
- The chef chooses a moral value such as sharing, honesty, patience, or care.
- The ending image proves that the choice changed the world.

The story prose is generated from world state, not from a fixed paragraph swap.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    apron: object | None = None
    chef: object | None = None
    child: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle", "chef"}
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
class Action:
    id: str
    verb: str
    gerund: str
    temptation: str
    risk: str
    fear: str
    zone: set[str]
    value: str
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
class MoralValue:
    id: str
    name: str
    choice_line: str
    ending_line: str
    guard: str
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"porridge", "soup", "cookies", "tea"}),
    "bakery": Setting(place="the bakery", indoor=True, affords={"bread", "cookies", "tea"}),
    "cottage": Setting(place="the cottage kitchen", indoor=True, affords={"porridge", "soup", "tea"}),
}

ACTIONS = {
    "porridge": Action(
        id="porridge",
        verb="stir the porridge",
        gerund="stirring porridge",
        temptation="take the biggest spoonful first",
        risk="the bowl could spill",
        fear="a sleepy child might go without supper",
        zone={"hands", "torso"},
        value="sharing",
        keyword="porridge",
        tags={"sharing", "warm"},
    ),
    "soup": Action(
        id="soup",
        verb="serve the soup",
        gerund="serving soup",
        temptation="keep the last warm ladle for yourself",
        risk="someone hungry could be left waiting",
        fear="the little ones may stay hungry",
        zone={"hands", "torso"},
        value="kindness",
        keyword="soup",
        tags={"kindness", "warm"},
    ),
    "cookies": Action(
        id="cookies",
        verb="set out the cookies",
        gerund="setting out cookies",
        temptation="hide the prettiest cookie for later",
        risk="a bedtime treat might be missing",
        fear="a child could feel left out",
        zone={"hands"},
        value="honesty",
        keyword="cookies",
        tags={"honesty", "sweet"},
    ),
    "tea": Action(
        id="tea",
        verb="pour the tea",
        gerund="pouring tea",
        temptation="rush and spill the cup",
        risk="the warm drink could splash",
        fear="someone might get scared by the mess",
        zone={"hands", "torso"},
        value="patience",
        keyword="tea",
        tags={"patience", "warm"},
    ),
}

PRIZES = {
    "apron": Prize("apron", "a clean blue apron", "apron", "torso"),
    "cup": Prize("cup", "a little cup", "cup", "hands"),
    "tray": Prize("tray", "a bedtime tray", "tray", "hands"),
    "hat": Prize("hat", "a soft kitchen hat", "hat", "head"),
}

VALUES = {
    "sharing": MoralValue(
        id="sharing",
        name="sharing",
        choice_line="share the warm treat evenly",
        ending_line="Everyone got a little, and nobody had to go to bed hungry.",
        guard="everyone has enough",
        tags={"sharing", "warm"},
    ),
    "honesty": MoralValue(
        id="honesty",
        name="honesty",
        choice_line="tell the truth about the hidden cookie",
        ending_line="The chef told the truth, and the cookie was put back on the tray for the child to see.",
        guard="nothing is hidden",
        tags={"honesty", "sweet"},
    ),
    "patience": MoralValue(
        id="patience",
        name="patience",
        choice_line="slow down and pour carefully",
        ending_line="The tea stayed in the cup, and the kitchen stayed quiet and calm.",
        guard="move gently",
        tags={"patience", "warm"},
    ),
    "kindness": MoralValue(
        id="kindness",
        name="kindness",
        choice_line="give the warm bowl to the smallest hungry guest first",
        ending_line="The smallest guest ate first, and the chef felt a soft glow in the heart.",
        guard="care for others",
        tags={"kindness", "warm"},
    ),
}

CHEF_NAMES = ["Milo", "Nina", "Luca", "Suri", "Iris", "Theo", "Mara", "Owen"]
HELPER_NAMES = ["Pip", "June", "Toby", "Lena", "Bea", "Finn"]
TRAITS = ["gentle", "busy", "cheerful", "tidy", "thoughtful", "sleepy"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
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


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_fix(action: Action, prize: Prize) -> Optional[MoralValue]:
    return VALUES.get(action.value)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = _safe_lookup(ACTIONS, action_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_fix(action, prize):
                    out.append((place, action_id, prize_id))
    return out


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_spill(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for act in ACTIONS.values():
            if actor.meters.get(act.id, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                sig = ("spill", item.id, act.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["messy"] = item.meters.get("messy", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    actor.meters[action.id] = actor.meters.get(action.id, 0) + 1
    actor.memes["want"] = actor.memes.get("want", 0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         name: str = "Milo", helper: str = "Pip", trait: str = "gentle") -> World:
    world = World(setting)
    chef = world.add(Entity(id=name, kind="character", type="chef", label="the chef"))
    child = world.add(Entity(id=helper, kind="character", type="child", label="the little helper", plural=False))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=chef.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    apron = world.add(Entity(
        id="apron",
        type="apron",
        label="apron",
        phrase="a soft apron",
        owner=chef.id,
        protective=True,
        covers={"torso"},
    ))
    apron.worn_by = chef.id

    world.say(f"{chef.id} was a {trait} chef who worked in {setting.place}.")
    world.say(f"{chef.pronoun().capitalize()} liked the quiet hours before bed, when the kitchen glowed warm and small.")
    world.say(f"Every night, {chef.id} cooked {action.gerund}, and {helper} liked to watch from a stool.")
    world.say(f"One night, {chef.id} had {prize_cfg.phrase} ready for a sleepy bedtime treat.")

    world.para()
    world.say(f"{helper} smiled and asked for one more bite, but {chef.id} noticed a temptation: {action.temptation}.")
    world.say(f"If {chef.id} chose badly, {action.fear}.")

    if action.id == "cookies":
        prize.worn_by = chef.id
    _do_action(world, chef, action, narrate=False)

    world.para()
    if action.id == "cookies":
        world.say(f"{chef.id} reached toward the prettiest cookie, then paused.")
        world.say(f"{chef.pronoun().capitalize()} remembered that bedtime feels kinder when grown-ups tell the truth.")
    elif action.id == "soup":
        world.say(f"The last warm bowl looked very tempting, but {chef.id} listened to the small hungry voice in the room.")
    elif action.id == "porridge":
        world.say(f"The spoon wanted to hurry, yet {chef.id} knew that a calm hand makes porridge taste better.")
    else:
        world.say(f"The cup wobbled in {chef.id}'s hand, and the room asked for a slower, safer choice.")

    moral = select_fix(action, prize)
    if moral is None:
        pass
    world.say(f"So {chef.id} chose to {moral.choice_line}.")
    world.say(moral.ending_line)

    world.facts.update(
        chef=chef,
        child=child,
        prize=prize,
        action=action,
        setting=setting,
        moral=moral,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chef = _safe_fact(world, f, "chef")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    moral = _safe_fact(world, f, "moral")
    return [
        f'Write a bedtime story for a small child about a chef who learns {moral.name}.',
        f"Tell a gentle kitchen story where {chef.id} wants to {action.verb} but chooses {moral.guard} instead.",
        f'Write a cozy story with a chef, a little helper, and "{action.keyword}" that ends with {moral.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chef = _safe_fact(world, f, "chef")
    child = _safe_fact(world, f, "child")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    moral = _safe_fact(world, f, "moral")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {chef.id}, a gentle chef, and the little helper named {child.id}.",
        ),
        QAItem(
            question=f"What did {chef.id} want to do in the kitchen?",
            answer=f"{chef.id} wanted to {action.verb} while getting the bedtime treat ready.",
        ),
        QAItem(
            question=f"What was the tempting thing that could have caused trouble?",
            answer=f"The tempting choice was to {action.temptation}. That could have made the bedtime moment less fair or less calm.",
        ),
        QAItem(
            question=f"What moral value did {chef.id} choose in the end?",
            answer=f"{chef.id} chose {moral.name}. That meant choosing to {moral.choice_line}.",
        ),
        QAItem(
            question=f"What stayed important at the end of the story?",
            answer=f"The bedtime treat stayed safe and warm, and {prize.label} was handled the right way so the little helper could enjoy the night.",
        ),
    ]


KNOWLEDGE = {
    "sharing": [(
        "What is sharing?",
        "Sharing means letting other people have some of what you have so everyone can enjoy it.",
    )],
    "honesty": [(
        "What is honesty?",
        "Honesty means telling the truth, even when it is a little bit hard.",
    )],
    "patience": [(
        "What is patience?",
        "Patience means waiting calmly and not rushing when something needs care.",
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means acting gently and helping someone because you care about them.",
    )],
    "warm": [(
        "Why do warm foods feel comforting at bedtime?",
        "Warm foods can feel comforting because they make the body feel cozy and safe before sleep.",
    )],
    "sweet": [(
        "Why should cookies be treated carefully?",
        "Cookies can crumble easily, so careful hands help them stay nice and ready to eat.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["moral"].tags) | set(f["action"].tags)
    out: list[QAItem] = []
    for tag in ["sharing", "honesty", "patience", "kindness", "warm", "sweet"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} would not affect a {prize.label}.)"
    return "(No story: this world does not have a distinct moral-value fix for that combination.)"


CURATED = [
    StoryParams(place="kitchen", action="cookies", prize="cup", name="Milo", helper="Pip", trait="gentle"),
    StoryParams(place="cottage", action="porridge", prize="tray", name="Nina", helper="June", trait="thoughtful"),
    StoryParams(place="bakery", action="tea", prize="hat", name="Luca", helper="Bea", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a chef, a gentle moral choice, and a cozy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=CHEF_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHEF_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.helper, params.trait)
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


ASP_RULES = r"""
valid_combo(Place, Action, Prize) :- setting(Place), affords(Place, Action), action(Action), prize(Prize), risked(Action, Prize), has_moral(Action).
risked(Action, Prize) :- zone(Action, Region), worn_on(Prize, Region).
has_moral(Action) :- value_of(Action, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("value_of", aid, a.value))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
