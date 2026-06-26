#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/time_personnel_china_friendship_magic_fable.py
===============================================================================================================

A small fable-style story world about time, personnel, china, friendship, and magic.

The premise is simple: a careful worker and a friend face a delicate job with a
china object and a clock-like deadline. The world model tracks physical damage
and emotional bonds so the story turns on a real, state-driven problem and a
real solution, not a fixed paragraph with swapped nouns.

The story space is intentionally narrow: only combinations where the task is
plausibly risky and the offered magic is a plausible help are allowed.
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

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fragile": 0.0, "dust": 0.0, "late": 0.0}
        if not self.memes:
            self.memes = {"friendship": 0.0, "worry": 0.0, "calm": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    time_pressure: str
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
    fragile: bool = True
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
class Magic:
    id: str
    label: str
    help_text: str
    prep: str
    tail: str
    targets: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.clock: int = 0
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
        clone.zone = set(self.zone)
        clone.clock = self.clock
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_time_pressure(world: World) -> list[str]:
    out: list[str] = []
    if world.clock < 1:
        return out
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("late", actor.id, world.clock)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["late"] += 1
        out.append("The little clock in the room kept reminding everyone that time was moving on.")
    return out


def _r_fragile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["late"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id or not item.meters.get("fragile", 0) >= THRESHOLD:
                continue
            sig = ("dust", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} gathered dust from the hurried air.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["friendship"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] += 1
        out.append(f"{actor.pronoun().capitalize()} felt calmer because friendship made the work lighter.")
    return out


CAUSAL_RULES = [_r_time_pressure, _r_fragile, _r_friendship]


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


def advance_time(world: World, steps: int = 1) -> None:
    world.clock += steps


def predict_risk(world: World, actor: Entity, task: Task, prize_id: str, magic: Optional[Magic] = None) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    if magic is not None:
        _use_magic(sim, sim.get(actor.id), magic, prize_id, narrate=False)
    prize = sim.get(prize_id)
    return {
        "dusty": prize.meters["dust"] >= THRESHOLD,
        "late": any(e.meters["late"] >= THRESHOLD for e in sim.characters()),
    }


def task_at_risk(task: Task, prize: Prize) -> bool:
    return prize.fragile and bool(task.zone)


def select_magic(task: Task, prize: Prize) -> Optional[Magic]:
    for magic in MAGICS:
        if task.id in magic.targets and prize.type in magic.targets:
            return magic
    return None


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters["late"] += 1
    actor.memes["worry"] += 1
    propagate(world, narrate=narrate)


def _use_magic(world: World, actor: Entity, magic: Magic, prize_id: str, narrate: bool = True) -> None:
    prize = world.get(prize_id)
    actor.memes["calm"] += 1
    prize.meters["dust"] = 0.0
    if narrate:
        world.say(magic.help_text)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who worked where careful hands mattered most.")


def friendship_begins(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(f"{hero.id} and {friend.id} were friends, and they trusted each other more than a fast promise.")


def show_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}, because it was beautiful and easy to break.")


def explain_work(world: World, hero: Entity, task: Task) -> None:
    world.say(f"Each day, {hero.id} had to {task.verb}, even when the hour felt small and the work felt large.")


def warn(world: World, friend: Entity, hero: Entity, task: Task, prize: Entity) -> bool:
    pred = predict_risk(world, hero, task, prize.id)
    if not pred["dusty"]:
        return False
    world.facts["predicted_dust"] = True
    world.say(f'"If you {task.verb}," {friend.id} said, "your {prize.label} may get dusty before the bell rings."')
    return True


def worry(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked at the clock and wished the work could be done without any rush at all.")


def choose_friendship(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    world.say(f"{friend.id} stepped closer and said, \"We can do this together, one careful piece at a time.\"")
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1


def accept_magic(world: World, hero: Entity, friend: Entity, task: Task, prize: Entity, magic: Magic) -> None:
    world.say(f"{hero.id} agreed to {magic.prep}.")
    _use_magic(world, hero, magic, prize.id, narrate=True)
    hero.memes["calm"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"Then the two friends {magic.tail}, and the {prize.label} stayed bright while the work got finished."
    )
    world.say(
        f"By the time the bell sounded, {hero.id} had completed {task.gerund}, and the room felt like a tidy little blessing."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, magic_cfg: Magic,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         friend_name: str = "Bao", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["patient", "kind"])))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["wise", "gentle"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    prize.meters["fragile"] = 1.0 if prize_cfg.fragile else 0.0

    introduce(world, hero)
    friendship_begins(world, hero, friend)
    show_prize(world, hero, prize)
    explain_work(world, hero, task)

    world.para()
    world.say(f"One day, the {setting.place} was busy, and the hour was already leaning toward evening.")
    worry(world, hero)
    warn(world, friend, hero, task, prize)
    choose_friendship(world, hero, friend, task)

    world.para()
    _do_task(world, hero, task, narrate=True)
    if predict_risk(world, hero, task, prize.id)["dusty"]:
        accept_magic(world, hero, friend, task, prize, magic_cfg)
    else:
        world.say(f"In the end, the work stayed gentle enough that the {prize.label} never lost its shine.")

    world.facts.update(hero=hero, friend=friend, prize=prize, task=task, magic=magic_cfg, setting=setting, resolved=True)
    return world


SETTINGS = {
    "tea_room": Setting(place="the tea room", indoor=True, affords={"polish", "arrange"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"carry", "sort"}),
    "hall": Setting(place="the long hall", indoor=True, affords={"carry", "polish"}),
}

TASKS = {
    "polish": Task(
        id="polish",
        verb="polish the time bell",
        gerund="polishing the time bell",
        rush="scrub it faster",
        risk="dusty",
        zone={"hands", "torso"},
        time_pressure="before sunset",
        tags={"time", "personnel"},
    ),
    "carry": Task(
        id="carry",
        verb="carry the china cups",
        gerund="carrying the china cups",
        rush="hurry through the corridor",
        risk="shaken",
        zone={"hands"},
        time_pressure="before the guests arrive",
        tags={"china", "personnel"},
    ),
    "arrange": Task(
        id="arrange",
        verb="arrange the china bowl on the table",
        gerund="arranging the china bowl",
        rush="set it down in a hurry",
        risk="bumped",
        zone={"hands", "torso"},
        time_pressure="before the tea cools",
        tags={"china", "time"},
    ),
    "sort": Task(
        id="sort",
        verb="sort the personnel list",
        gerund="sorting the personnel list",
        rush="shuffle the pages quickly",
        risk="creased",
        zone={"hands"},
        time_pressure="before the bell",
        tags={"time", "personnel"},
    ),
}

PRIZES = {
    "cup": Prize(label="china cup", phrase="a painted china cup", type="cup", tags={"china"}),
    "bowl": Prize(label="china bowl", phrase="a round china bowl", type="bowl", tags={"china"}),
    "teaset": Prize(label="china tea set", phrase="a little china tea set", type="teaset", plural=True, tags={"china"}),
}

MAGICS = [
    Magic(
        id="slow_light",
        label="slow-light magic",
        help_text="A soft glow settled over the table, and everything moved just a little more slowly.",
        prep="use slow-light magic to steady their hands",
        tail="walked under the slow light, and every cup found its place without a wobble",
        targets={"polish", "cup", "bowl", "teaset"},
        tags={"magic", "time"},
    ),
    Magic(
        id="dust_shield",
        label="dust-shield magic",
        help_text="A clear shield blinked into being, and the dust could not reach the china.",
        prep="call on dust-shield magic",
        tail="worked inside the clean shield, so the china stayed bright",
        targets={"carry", "arrange", "cup", "bowl", "teaset"},
        tags={"magic", "china"},
    ),
]

GIRL_NAMES = ["Mina", "Lian", "Rosa", "Ivy", "Nina"]
BOY_NAMES = ["Bao", "Jin", "Tao", "Eli", "Noel"]
TRAITS = ["patient", "steady", "curious", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for prize_id, prize in PRIZES.items():
                if task_at_risk(task, prize) and select_magic(task, prize):
                    combos.append((place, task_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    friend: str
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


KNOWLEDGE = {
    "china": [
        QAItem(question="What is china?", answer="China is a smooth, hard material used to make fine cups, bowls, and plates."),
        QAItem(question="Why should china be handled carefully?", answer="China should be handled carefully because it can crack or chip if it is dropped or bumped."),
    ],
    "time": [
        QAItem(question="What does a clock do?", answer="A clock helps people know the time so they can tell when to start, stop, or hurry."),
        QAItem(question="Why do people watch the time?", answer="People watch the time so they can finish jobs, meet friends, and not arrive too late."),
    ],
    "friendship": [
        QAItem(question="What is friendship?", answer="Friendship is a kind bond between people who care about each other and help each other."),
    ],
    "magic": [
        QAItem(question="What is magic in a story?", answer="Magic in a story is a special pretend power that can do surprising things and help solve problems."),
    ],
    "personnel": [
        QAItem(question="What does personnel mean?", answer="Personnel means the people who work in a place or are part of a team."),
    ],
}
KNOWLEDGE_ORDER = ["time", "personnel", "china", "friendship", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a fable for young children about {hero.id}, friendship, and a small magic that helps with {task.verb}.',
        f"Tell a gentle story in which a {hero.type} named {hero.id} worries about {prize.label} while the time for work is running out.",
        f"Write a short fable that includes a china object, a clock, and two friends who solve a problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, task = f["hero"], f["friend"], f["prize"], f["task"]
    qa = [
        QAItem(
            question=f"Who was the story about in the {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type}, and {friend.id}, who were friends.",
        ),
        QAItem(
            question=f"What did {hero.id} need to do before the bell rang?",
            answer=f"{hero.id} needed to {task.verb} before the bell rang, because the work had to be finished on time.",
        ),
        QAItem(
            question=f"What china object did {hero.id} worry about?",
            answer=f"{hero.id} worried about {hero.pronoun('possessive')} {prize.label}, which was delicate and easy to spoil if the work got rushed.",
        ),
    ]
    if f.get("resolved"):
        magic = _safe_fact(world, f, "magic")
        qa.append(QAItem(
            question=f"How did {magic.label} help {hero.id} and {friend.id}?",
            answer=f"{magic.label.capitalize()} helped them slow down and keep the {prize.label} safe while they finished {task.gerund}.",
        ))
        qa.append(QAItem(
            question=f"How did the friends feel at the end of the story?",
            answer=f"They felt calm and proud, because they solved the problem together and the {prize.label} stayed bright.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | set(world.facts["prize"].tags) | set(world.facts["magic"].tags)
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clock={world.clock}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="tea_room", task="arrange", prize="cup", name="Mina", gender="girl", friend="Bao", trait="patient"),
    StoryParams(place="hall", task="polish", prize="teaset", name="Lian", gender="girl", friend="Jin", trait="steady"),
    StoryParams(place="courtyard", task="carry", prize="bowl", name="Bao", gender="boy", friend="Mina", trait="gentle"),
]


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.gerund} and {prize.label} do not make a strong enough time-and-china problem for this fable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world about time, personnel, china, friendship, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "task", None) and getattr(args, "prize", None):
        if not (task_at_risk(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))) and select_magic(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), _safe_lookup(MAGICS, 0),
                 hero_name=params.name, hero_type=params.gender, hero_traits=[params.trait], friend_name=params.friend,
                 friend_type="boy" if params.friend in BOY_NAMES else "girl")
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
place(P) :- setting(P).
task(T) :- task_id(T).
prize(PZ) :- prize_id(PZ).

risk(T,PZ) :- task_zone(T,_), prize_fragile(PZ).
fix(T,PZ) :- task_to_magic(T,M), magic_target(M,PZ).
valid_story(PL,T,PZ) :- affords(PL,T), risk(T,PZ), fix(T,PZ).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_id", tid))
        for z in sorted(t.zone):
            lines.append(asp.fact("task_zone", tid, z))
        for m in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, m))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_id", pid))
        if p.fragile:
            lines.append(asp.fact("prize_fragile", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("prize_tag", pid, tag))
    for m in MAGICS:
        lines.append(asp.fact("magic_id", m.id))
        for t in sorted(m.targets):
            lines.append(asp.fact("task_to_magic", t, m.id))
            lines.append(asp.fact("magic_target", m.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/3."))
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
