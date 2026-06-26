#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/payment_cylinder_symbiotic_teamwork_heartwarming.py
===============================================================================================

A small heartwarming storyworld about a child, a shared task, and a fragile
payment cylinder that only works well when everyone helps.

Seed tale shape:
- A child wants to carry a clear payment cylinder to a friendly booth.
- The cylinder is awkward and easy to wobble or spill.
- A caring helper notices the risk and suggests symbiotic teamwork.
- Together they steady the cylinder, make the payment safely, and end with
  something better than before: trust, calm, and a successful little sale.

This world models a small classical simulation:
- physical meters: wobble, spill, secure, load, polish
- emotional memes: joy, worry, pride, closeness, teamwork, relief
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    carried_by: Optional[str] = None
    used_by: set[str] = field(default_factory=set)
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    cyl: object | None = None
    helper: object | None = None
    def __post_init__(self) -> None:
        for k in ["wobble", "spill", "secure", "load", "polish"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "closeness", "teamwork", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    risk: str
    risk_meter: str
    zone: str
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
class Container:
    id: str
    label: str
    phrase: str
    region: str
    unstable: bool = False
    need_hands: int = 2
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
class Teamwork:
    id: str
    label: str
    prep: str
    done: str
    helps: set[str] = field(default_factory=set)
    cures: set[str] = field(default_factory=set)
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
        self.active_zone: str = ""

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
        clone.active_zone = self.active_zone
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    if not world.active_zone:
        return out
    carriers = [e for e in world.characters() if any(i.id == "cylinder" for i in world.carried_items(e))]
    if len(carriers) >= 2:
        sig = ("wobble", world.active_zone)
        if sig not in world.fired:
            world.fired.add(sig)
            cyl = world.get("cylinder")
            cyl.meters["secure"] += 1
            cyl.meters["wobble"] = max(0.0, cyl.meters["wobble"] - 1.0)
            out.append("Together they held the cylinder steady.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    cyl = world.entities.get("cylinder")
    if not cyl or cyl.meters["wobble"] < THRESHOLD or cyl.meters["secure"] >= THRESHOLD:
        return out
    sig = ("spill", cyl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cyl.meters["spill"] += 1
    out.append("The cylinder tipped and a few coins rattled toward the edge.")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and ("pride", "done") not in world.fired:
        world.fired.add(("pride", "done"))
        for e in world.characters():
            e.memes["pride"] += 1
            e.memes["closeness"] += 1
        out.append("That made everyone feel proud and close.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("spill", _r_spill), Rule("pride", _r_pride)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def select_teamwork(task: Task, container: Container) -> Optional[Teamwork]:
    for tw in TEAMWORKS:
        if task.id in tw.helps and container.id in tw.cures:
            return tw
    return None


def task_at_risk(task: Task, container: Container) -> bool:
    return task.zone == container.region


def predict_spill(world: World, actor: Entity, helper: Entity, task: Task) -> bool:
    sim = world.copy()
    _do_task(sim, actor.id, helper.id, task, narrate=False)
    return bool(sim.entities["cylinder"].meters["spill"] >= THRESHOLD)


def intro(world: World, child: Entity, helper: Entity, container: Entity) -> None:
    world.say(
        f"{child.id} was a {next((t for t in child.traits if t != 'little'), 'gentle')} {child.type} "
        f"who cared about little jobs that mattered."
    )
    world.say(
        f"{helper.id} was a {helper.type} who liked helping in quiet, careful ways."
    )
    world.say(
        f"Together they had a clear {container.label} for a tiny payment at the booth."
    )


def want_help(world: World, child: Entity, task: Task) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} loved {task.gerund} because it made the day feel useful and kind."
    )


def arrive(world: World, child: Entity, helper: Entity) -> None:
    world.say(f"One afternoon, {child.id} and {helper.id} went to {world.setting.place}.")
    world.say("The air was warm, and the booth was waiting for a small payment.")


def worry(world: World, helper: Entity, child: Entity, task: Task, container: Entity) -> bool:
    if not task_at_risk(task, container):
        return False
    world.facts["predicted_spill"] = predict_spill(world, child, helper, task)
    world.say(
        f'"If we hurry, the {container.label} might wobble," {helper.id} said. '
        f'"Then the payment could spill."'
    )
    helper.memes["worry"] += 1
    return True


def struggle(world: World, child: Entity, task: Task) -> None:
    child.memes["worry"] += 1
    child.meters["wobble"] += 1
    world.say(
        f"{child.id} tried to {task.verb}, but the cylinder felt too slippery to trust alone."
    )


def _do_task(world: World, actor_id: str, helper_id: str, task: Task, narrate: bool = True) -> None:
    world.active_zone = task.zone
    child = world.get(actor_id)
    helper = world.get(helper_id)
    cyl = world.get("cylinder")
    child.meters["wobble"] += 1
    cyl.meters["wobble"] += 1
    if helper_id in cyl.used_by:
        cyl.meters["secure"] += 1
    propagate(world, narrate=narrate)


def teamwork_offer(world: World, child: Entity, helper: Entity, task: Task, container: Entity) -> Optional[Teamwork]:
    tw = select_teamwork(task, container)
    if tw is None:
        return None
    if predict_spill(world, child, helper, task):
        return None
    world.say(
        f'{helper.id} smiled and said, "{tw.prep}."'
    )
    world.say(
        f"{child.id} nodded. The plan was simple: one would hold, and one would pay."
    )
    return tw


def accept(world: World, child: Entity, helper: Entity, task: Task, container: Entity, tw: Teamwork) -> None:
    cyl = world.get("cylinder")
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    cyl.meters["secure"] += 1
    cyl.meters["wobble"] = max(0.0, cyl.meters["wobble"] - 1.0)
    child.meters["load"] += 1
    helper.meters["load"] += 1
    child.used_by.add(helper.id)
    helper.used_by.add(child.id)
    world.say(
        f"{child.id} and {helper.id} worked side by side, and the cylinder became steady in their hands."
    )
    world.say(
        f"{tw.done}. The payment went through, and the little booth felt brighter for it."
    )
    world.facts["resolved"] = True
    propagate(world, narrate=True)
    world.say(
        f"At the end, {child.id} left with a lighter heart, and the {container.label} stayed safe and full of promise."
    )


def tell(setting: Setting, task: Task, container_cfg: Container, hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Grandpa", helper_type: str = "grandfather", traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (traits or ["gentle", "careful"])))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["kind"]))
    cyl = world.add(Entity(
        id="cylinder", type="container", label=container_cfg.label, phrase=container_cfg.phrase,
        owner=child.id, caretaker=helper.id, protective=False
    ))
    world.add(Entity(id="payment", type="thing", label="payment", phrase="a small payment", owner=child.id))
    intro(world, child, helper, cyl)
    want_help(world, child, task)
    world.para()
    arrive(world, child, helper)
    worry(world, helper, child, task, cyl)
    struggle(world, child, task)
    world.para()
    tw = teamwork_offer(world, child, helper, task, cyl)
    if tw:
        accept(world, child, helper, task, cyl, tw)
    world.facts.update(child=child, helper=helper, task=task, container=cyl, setting=setting, teamwork=tw,
                       resolved=bool(tw))
    return world


SETTINGS = {
    "booth": Setting(place="the little market booth", affords={"payment"}),
    "counter": Setting(place="the community counter", affords={"payment"}),
    "porch": Setting(place="the porch table", affords={"payment"}),
}

TASKS = {
    "payment": Task(
        id="payment",
        verb="make the payment",
        gerund="making the payment",
        risk="spill the coins",
        risk_meter="spill",
        zone="counter",
        keyword="payment",
        tags={"payment", "kindness"},
    ),
}

CONTAINERS = {
    "cylinder": Container(
        id="cylinder",
        label="payment cylinder",
        phrase="a clear payment cylinder with a soft cap",
        region="counter",
        unstable=True,
        need_hands=2,
        tags={"payment", "cylinder"},
    ),
}

TEAMWORKS = [
    Teamwork(
        id="symbiotic-teamwork",
        label="symbiotic teamwork",
        prep="Let's do this together so the cylinder stays steady",
        done="Their symbiotic teamwork worked beautifully",
        helps={"payment"},
        cures={"cylinder"},
    ),
]

CHILD_NAMES = ["Mina", "Luca", "Nia", "Arlo", "Ivy"]
HELPER_NAMES = ["Grandpa", "Grandma", "Aunt June", "Mr. Reed", "Mama"]
TRAITS = ["gentle", "kind", "thoughtful", "helpful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for t in TASKS:
            for c in CONTAINERS:
                if task_at_risk(_safe_lookup(TASKS, t), _safe_lookup(CONTAINERS, c)) and select_teamwork(_safe_lookup(TASKS, t), _safe_lookup(CONTAINERS, c)):
                    combos.append((s, t, c))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    container: str
    name: str
    helper: str
    gender: str
    helper_gender: str
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
    "payment": [
        ("What is a payment?", "A payment is something you give, like money or a token, to show that something has been bought or shared fairly."),
    ],
    "cylinder": [
        ("What is a cylinder?", "A cylinder is a shape with round ends and a long side, like a tube or a can."),
    ],
    "symbiotic": [
        ("What does symbiotic mean?", "Symbiotic means two living things or two helpers work closely together in a way that helps both of them."),
    ],
    "teamwork": [
        ("What is teamwork?", "Teamwork is when people help each other and do a job together instead of doing it alone."),
    ],
}
KNOWLEDGE_ORDER = ["payment", "cylinder", "symbiotic", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story about payment, cylinder, and symbiotic teamwork.',
        f"Tell a gentle story where {f['child'].id} and {f['helper'].id} work together with a {f['container'].label}.",
        f"Write a short story for a child that ends with {f['child'].id} and {f['helper'].id} feeling proud after a payment is made safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, task, container = f["child"], f["helper"], f["task"], f["container"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {task.verb} with the {container.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {container.label}?",
            answer=f"{helper.id} worried because the {container.label} could wobble and spill the payment if it was carried alone.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {helper.id}?",
            answer=f"They used symbiotic teamwork, made the payment safely, and felt proud and close at the end.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What kind of teamwork helped with the {container.label}?",
                answer="Symbiotic teamwork helped because one person held the cylinder steady while the other completed the payment.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set([world.facts["task"].id, world.facts["container"].id, "teamwork", "symbiotic", "payment"])
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="booth", task="payment", container="cylinder", name="Mina", helper="Grandpa", gender="girl", helper_gender="man", trait="gentle"),
    StoryParams(place="counter", task="payment", container="cylinder", name="Luca", helper="Grandma", gender="boy", helper_gender="woman", trait="helpful"),
    StoryParams(place="porch", task="payment", container="cylinder", name="Ivy", helper="Aunt June", gender="girl", helper_gender="woman", trait="thoughtful"),
]


def explain_rejection(task: Task, container: Container) -> str:
    return f"(No story: {task.gerund} does not create a real risk for the {container.label}, so the heartwarming teamwork would not be earned.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: a child, a payment, and symbiotic teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    if getattr(args, "task", None) and getattr(args, "container", None):
        task, container = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(CONTAINERS, getattr(args, "container", None))
        if not (task_at_risk(task, container) and select_teamwork(task, container)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "container", None) is None or c[2] == getattr(args, "container", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, container = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, container=container, name=name, helper=helper, gender=gender, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(CONTAINERS, params.container),
                 params.name, "girl" if params.gender == "girl" else "boy",
                 params.helper, "woman" if params.helper_gender == "woman" else "man",
                 [params.trait, "little"])
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
task_at_risk(T, C) :- task(T), container(C), zone(T, Z), region(C, Z).
has_teamwork(T, C) :- task_at_risk(T, C), teamwork(TW), helps(TW, T), cures(TW, C).
valid_story(P, T, C) :- setting(P), task(T), container(C), affords(P, T), task_at_risk(T, C), has_teamwork(T, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("zone", tid, t.zone))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("region", cid, c.region))
    for tw in TEAMWORKS:
        lines.append(asp.fact("teamwork", tw.id))
        for a in sorted(tw.helps):
            lines.append(asp.fact("helps", tw.id, a))
        for c in sorted(tw.cures):
            lines.append(asp.fact("cures", tw.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for p, t, c in triples:
            print(f"  {p:8} {t:10} {c:10}")
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
            header = f"### {p.name}: {p.task} at {p.place} (container: {p.container})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
