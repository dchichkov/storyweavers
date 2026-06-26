#!/usr/bin/env python3
"""
storyworlds/worlds/hypnotist_ration_quest_friendship_problem_solving_bedtime.py
===============================================================================

A small bedtime-story world about a gentle quest, a careful ration, and a
friend who helps solve a problem with calm words and a little hypnotist trick:
counting slowly until everyone feels brave and sleepy.

Premise:
- A child and a friend want their bedtime ration: one small bowl of warm oats
  and a honey toast square.
- The ration has been packed into the wrong tin and the lid is stuck.
- A kind hypnotist visits with a soft voice, helping everyone breathe, count,
  and think of a better plan.

The story is intentionally compact:
- the physical state tracks things like stuck lids, crumbs, and sleepy readiness
- the emotional state tracks excitement, worry, friendship, and calm
- the ending proves what changed by showing the ration served and the room
  settling into bedtime quiet
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
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    hypnotist: object | None = None
    tin: object | None = None
    tray: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    bedtime: bool = True
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    challenge: str
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
class Ration:
    id: str
    label: str
    phrase: str
    amount: str
    container: str
    target: str
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
class Helper:
    id: str
    label: str
    method: str
    offer: str
    result: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _bump(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    ent = world.get(eid)
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mem(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    ent = world.get(eid)
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_stuck(world: World) -> list[str]:
    out: list[str] = []
    tin = world.get("ration_tin")
    if tin.meters.get("stuck", 0.0) < THRESHOLD:
        return out
    sig = ("stuck",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The little tin would not open, and the bedtime ration stayed hidden inside.")
    _mem(world, "child", "worry", 1)
    _mem(world, "friend", "worry", 1)
    return out


def _rule_patience(world: World) -> list[str]:
    out: list[str] = []
    hypnotist = world.get("hypnotist")
    if hypnotist.memes.get("calm", 0.0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The room grew quieter, because the kind hypnotist kept speaking in slow, soft numbers.")
    _mem(world, "child", "calm", 1)
    _mem(world, "friend", "calm", 1)
    return out


def _rule_share(world: World) -> list[str]:
    out: list[str] = []
    tin = world.get("ration_tin")
    tray = world.get("bedtray")
    if tin.meters.get("open", 0.0) < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tray.meters["served"] = 1
    out.append("At last, the warm oats and honey toast square were placed on the bedside tray.")
    return out


CAUSAL_RULES = [_rule_stuck, _rule_patience, _rule_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_open(world: World, actor: Entity, quest: Quest) -> bool:
    sim = world.copy()
    _bump(sim, "ration_tin", "stuck", 0.0)
    _mem(sim, actor.id, "focus", 1)
    _mem(sim, actor.id, "calm", 1)
    sim.get("ration_tin").meters["open"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("bedtray").meters.get("served", 0.0) >= THRESHOLD


def introduce(world: World, child: Entity, friend: Entity, hypnotist: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} was a {child.traits[0]} little {child.type} who liked gentle quests."
    )
    world.say(
        f"{friend.id} was {friend.traits[0]} too, and {friend.pronoun().capitalize()} loved helping {child.pronoun('object')} solve small problems."
    )
    world.say(
        f"Near the pillow, a kind hypnotist named {hypnotist.id} smiled and promised to help with soft words."
    )


def set_scene(world: World, quest: Quest, ration: Ration) -> None:
    world.say(
        f"The night light glowed in the {world.setting.place}, and the bedtime quest began with a tiny ration to share."
    )
    world.say(
        f"They wanted {ration.phrase}, but it was tucked in {ration.container} and the lid was stuck."
    )


def try_problem(world: World, child: Entity, friend: Entity, quest: Quest, ration: Ration) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    friend.memes["desire"] = friend.memes.get("desire", 0.0) + 1
    world.say(
        f"{child.id} tried to {quest.verb}, but the lid gave no wiggle at all."
    )
    world.say(
        f"{friend.id} tugged once, then twice, but the tin only made a stubborn little click."
    )
    _bump(world, "ration_tin", "stuck", 1)


def hypnotist_help(world: World, hypnotist: Entity, child: Entity, friend: Entity) -> None:
    _mem(world, hypnotist.id, "calm", 1)
    world.say(
        f"Then {hypnotist.id} lifted a hand and said, \"Breathe in... breathe out... count three stars.\""
    )
    world.say(
        f"{child.id} and {friend.id} listened, and their shoulders stopped feeling so tight."
    )
    propagate(world, narrate=True)


def solve_it(world: World, child: Entity, friend: Entity, hypnotist: Entity, ration: Ration) -> None:
    tin = world.get("ration_tin")
    if tin.meters.get("stuck", 0.0) < THRESHOLD:
        return
    world.say(
        f"{hypnotist.id} asked them to look for a better place to hold the tin, and {friend.id} found the rubber pad on the bedside tray."
    )
    world.say(
        f"With the tin resting on the pad, {child.id} turned the lid again. This time it opened with a soft pop."
    )
    tin.meters["open"] = 1
    tin.meters["stuck"] = 0
    propagate(world, narrate=True)


def ending(world: World, child: Entity, friend: Entity, hypnotist: Entity, ration: Ration) -> None:
    world.para()
    tray = world.get("bedtray")
    world.say(
        f"Soon the {ration.amount} of {ration.label} sat on the tray, and the three friends shared the warm snack in the quiet room."
    )
    world.say(
        f"{child.id} felt sleepy, {friend.id} felt proud, and {hypnotist.id} gave one last slow smile before the lamps went soft."
    )
    world.say(
        f"It was a small bedtime victory: the quest was finished, the ration was shared, and the room was ready for dreams."
    )


SETTINGS = {
    "bedroom": Setting(place="bedroom", bedtime=True, affords={"quest"}),
    "nursery": Setting(place="nursery", bedtime=True, affords={"quest"}),
    "campbed": Setting(place="camp bed", bedtime=True, affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="find the bedtime ration",
        gerund="finding the bedtime ration",
        rush="hurry to the tin",
        challenge="a stuck lid and a sleepy room",
        keyword="quest",
        tags={"quest", "problem solving", "friendship", "bedtime"},
    ),
}

RATIONS = {
    "oats": Ration(
        id="oats",
        label="warm oats",
        phrase="a small bowl of warm oats and a honey toast square",
        amount="little bowl",
        container="a snug blue tin",
        target="bedtray",
    ),
    "porridge": Ration(
        id="porridge",
        label="porridge",
        phrase="a tiny bowl of porridge with a sweet spoon of jam",
        amount="tiny bowl",
        container="a round tin with a sleepy moon on it",
        target="bedtray",
    ),
}

HYPNOTISTS = {
    "milo": Helper(
        id="Milo",
        label="kind hypnotist",
        method="slow counting",
        offer="breathe and count stars",
        result="calm",
        tags={"hypnotist", "friendship", "problem solving", "bedtime"},
    ),
    "luna": Helper(
        id="Luna",
        label="gentle hypnotist",
        method="soft humming",
        offer="hum until the lid feels easy",
        result="calm",
        tags={"hypnotist", "friendship", "problem solving", "bedtime"},
    ),
}

CHILD_NAMES = ["Nora", "Maya", "Leo", "Ava", "Eli"]
FRIEND_NAMES = ["Pip", "Mina", "Toby", "Rae", "Finn"]


@dataclass
class StoryParams:
    place: str
    quest: str
    ration: str
    hypnotist: str
    child: str
    friend: str
    seed: Optional[int] = None
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


def tell(setting: Setting, quest: Quest, ration: Ration, helper: Helper, child_name: str, friend_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in {"Nora", "Maya", "Ava"} else "boy",
                             traits=["sleepy", "kind"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_name in {"Mina", "Rae"} else "boy",
                              traits=["helpful", "patient"]))
    hypnotist = world.add(Entity(id=helper.id, kind="character", type="adult", traits=["gentle", "calm"]))
    tin = world.add(Entity(id="ration_tin", type="tin", label="ration tin"))
    tray = world.add(Entity(id="bedtray", type="tray", label="bedside tray"))
    world.facts.update(child=child, friend=friend, hypnotist=hypnotist, quest=quest, ration=ration, helper=helper)

    introduce(world, child, friend, hypnotist)
    world.para()
    set_scene(world, quest, ration)
    try_problem(world, child, friend, quest, ration)
    hypnotist_help(world, hypnotist, child, friend)
    solve_it(world, child, friend, hypnotist, ration)
    ending(world, child, friend, hypnotist, ration)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest: Quest = _safe_fact(world, f, "quest")
    ration: Ration = _safe_fact(world, f, "ration")
    helper: Helper = _safe_fact(world, f, "helper")
    child: Entity = _safe_fact(world, f, "child")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        f'Write a bedtime story about a small quest, a friendship, and a problem that gets solved with a calm idea.',
        f"Tell a gentle story where {child.id} and {friend.id} need {ration.phrase}, but the tin is stuck until {helper.id} helps.",
        f'Write a child-friendly story that includes a hypnotist, a ration, and a quest ending with everyone sleepy and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    friend: Entity = _safe_fact(world, f, "friend")
    hypnotist: Entity = _safe_fact(world, f, "hypnotist")
    quest: Quest = _safe_fact(world, f, "quest")
    ration: Ration = _safe_fact(world, f, "ration")
    qa = [
        QAItem(
            question=f"What was the bedtime quest in the story?",
            answer=f"The bedtime quest was to {quest.verb}. The children wanted to do it before sleep, but the tin was stuck.",
        ),
        QAItem(
            question=f"Why did {child.id} and {friend.id} need help?",
            answer=f"They needed help because the lid on the {ration.label} tin would not open. The problem was solved with calm counting and a better place to hold the tin.",
        ),
        QAItem(
            question=f"Who helped {child.id} and {friend.id} solve the problem?",
            answer=f"The kind hypnotist {hypnotist.id} helped them solve it by speaking softly, counting slowly, and guiding them to a better plan.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the tin opened, the {ration.label} was placed on the bedside tray, and the room grew quiet and sleepy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries to find something, fix something, or reach a goal.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about one another, help one another, and like being together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a hard thing and trying one idea after another until it works.",
        ),
        QAItem(
            question="Why do bedtime stories often feel calm?",
            answer="Bedtime stories often feel calm because they use soft words, quiet endings, and sleepy ideas that help children relax.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", quest="quest", ration="oats", hypnotist="milo", child="Nora", friend="Pip"),
    StoryParams(place="nursery", quest="quest", ration="porridge", hypnotist="luna", child="Leo", friend="Mina"),
    StoryParams(place="campbed", quest="quest", ration="oats", hypnotist="milo", child="Ava", friend="Finn"),
]


ASP_RULES = r"""
% The quest is valid when the place supports it and the ration can be shared.
valid_story(P, Q, R, H) :- setting(P), quest(Q), ration(R), helper(H),
                            affords(P, Q), bedtime_place(P), help_kind(H).
bedtime_place(P) :- setting(P).
help_kind(H) :- helper(H).
% A stuck tin is the problem; calm help lets it open.
problem(stuck_tin).
solves_help(H) :- helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.bedtime:
            lines.append(asp.fact("bedtime_place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid in RATIONS:
        lines.append(asp.fact("ration", rid))
    for hid in HYPNOTISTS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    if not asp_valid_stories():
        print("MISMATCH: no ASP valid stories found.")
        return 1
    print(f"OK: ASP produced {len(asp_valid_stories())} valid story tuples.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime quest storyworld with a hypnotist and a ration.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ration", choices=RATIONS)
    ap.add_argument("--hypnotist", choices=HYPNOTISTS)
    ap.add_argument("--child")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or "quest"
    ration = getattr(args, "ration", None) or rng.choice(list(RATIONS))
    hypnotist = getattr(args, "hypnotist", None) or rng.choice(list(HYPNOTISTS))
    child = getattr(args, "child", None) or rng.choice(CHILD_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if child == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, quest=quest, ration=ration, hypnotist=hypnotist, child=child, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(RATIONS, params.ration), _safe_lookup(HYPNOTISTS, params.hypnotist), params.child, params.friend)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
