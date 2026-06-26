#!/usr/bin/env python3
"""
storyworlds/worlds/faggot_conflict_adventure.py
================================================

A small adventure storyworld about a child, a trail, a bundle of sticks, and a
gentle conflict that turns into a safer plan.

The seed idea:
---
A child is helping on a woodland walk. They find a faggot of sticks and want
to carry it back to the campfire spot, but the bundle is too heavy and the path
is narrow. A grown-up worries about dropping it, the child gets upset, and then
they solve the problem by tying the sticks together and sharing the load.

World model:
---
- Physical meters track weight, balance, dryness, tiredness, and strain.
- Emotional memes track excitement, worry, conflict, pride, and trust.
- The story changes because state changes: carrying, slipping, helping, and
  choosing a better method all affect what happens next.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py in ASP helpers
- generate / emit / main / parser / parameter resolution
- inline ASP twin and verification
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def _gender(self) -> str:
        if self.type in {"girl", "mother", "woman"}:
            return "f"
        if self.type in {"boy", "father", "man"}:
            return "m"
        return "n"

    def pronoun(self, case: str = "subject") -> str:
        g = self._gender()
        if g == "f":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if g == "m":
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
    place: str = "the woods"
    path_narrow: bool = True
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
    strain: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    start_meter: float = 1.0
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
    id: str
    label: str
    phrase: str
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    reduces: set[str] = field(default_factory=set)
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "woods": Setting(place="the woods", path_narrow=True, affords={"carry_faggot", "cross_log", "build_fire"}),
    "camp": Setting(place="the camp clearing", path_narrow=False, affords={"carry_faggot", "build_fire"}),
    "ridge": Setting(place="the ridge trail", path_narrow=True, affords={"carry_faggot", "cross_log"}),
}

TASKS = {
    "carry_faggot": Task(
        id="carry_faggot",
        verb="carry the faggot to camp",
        gerund="carrying the faggot",
        rush="hurry along with the faggot",
        risk="drop the bundle",
        strain="feel the heavy bundle tug at both arms",
        keyword="faggot",
        tags={"faggot", "wood", "carry"},
        start_meter=1.0,
    ),
    "cross_log": Task(
        id="cross_log",
        verb="cross the fallen log",
        gerund="crossing the log",
        rush="dash over the log",
        risk="slip on the bark",
        strain="keep balance on the narrow wood",
        keyword="log",
        tags={"log", "balance"},
        start_meter=1.0,
    ),
    "build_fire": Task(
        id="build_fire",
        verb="build the fire",
        gerund="stacking the sticks",
        rush="feed the fire too fast",
        risk="scatter the kindling",
        strain="carefully place each stick",
        keyword="fire",
        tags={"fire", "wood", "warmth"},
        start_meter=1.0,
    ),
}

PRIZES = {
    "bundle": Prize(id="bundle", label="faggot", phrase="a faggot of dry sticks", region="arms"),
    "basket": Prize(id="basket", label="basket", phrase="a woven basket for wood", region="hands"),
}

GEAR = {
    "cord": Gear(
        id="cord",
        label="a length of cord",
        prep="tie the sticks together with a length of cord first",
        tail="tied the sticks into a steadier bundle",
        helps={"carry_faggot"},
        reduces={"strain", "risk"},
    ),
    "gloves": Gear(
        id="gloves",
        label="work gloves",
        prep="put on work gloves before lifting it",
        tail="pulled on the gloves and lifted more carefully",
        helps={"carry_faggot", "build_fire"},
        reduces={"strain"},
    ),
    "pole": Gear(
        id="pole",
        label="a short carrying pole",
        prep="slide the bundle onto a short carrying pole",
        tail="slid the bundle onto the pole and shared the weight",
        helps={"carry_faggot"},
        reduces={"strain", "risk"},
    ),
}

NAMES = ["Ari", "Milo", "Nia", "Pip", "Lina", "Theo", "June", "Owen"]
TRAITS = ["curious", "brave", "stubborn", "quick", "careful", "cheerful"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_risky(T) :- task(T), task_tag(T, faggot), setting_affords(S, T), narrow(S).
compatible(G,T) :- gear(G), task(T), helps(G,T), task_risky(T).
valid_story(S,T,P,G) :- setting(S), task(T), prize(P), gear(G), compatible(G,T), prize_region(P, arms).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.path_narrow:
            lines.append(asp.fact("narrow", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_tag", tid, t.keyword))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for t in sorted(g.helps):
            lines.append(asp.fact("helps", gid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python story gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def risk_for(task: Task, prize: Prize) -> bool:
    return task.keyword == "faggot" and prize.region == "arms"


def choose_gear(task: Task, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if task.id in gear.helps:
            return gear
    return None


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        # strain can trigger conflict if the child is excited and the load is high
        for ent in world.characters():
            if ent.meters.get("strain", 0.0) >= THRESHOLD and ent.memes.get("worry", 0.0) >= THRESHOLD:
                sig = ("conflict", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["conflict"] = ent.memes.get("conflict", 0.0) + 1
                    changed = True
        # strong conflict can lower trust temporarily
        for ent in world.characters():
            if ent.memes.get("conflict", 0.0) >= THRESHOLD and ent.memes.get("trust", 0.0) < THRESHOLD:
                sig = ("pride", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["pride"] = ent.memes.get("pride", 0.0) + 1
                    changed = True


def predict_problem(world: World, actor: Entity, task: Task, prize: Prize) -> dict:
    sim = world.copy()
    _do_task(sim, actor.id, task.id, narrate=False)
    return {
        "conflict": any(e.memes.get("conflict", 0.0) >= THRESHOLD for e in sim.characters()),
        "strain": sim.get(prize.id).meters.get("strain", 0.0),
    }


def _do_task(world: World, actor_id: str, task_id: str, narrate: bool = True) -> None:
    actor = world.get(actor_id)
    task = _safe_lookup(TASKS, task_id)
    actor.meters[task_id] = actor.meters.get(task_id, 0.0) + task.start_meter
    actor.meters["strain"] = actor.meters.get("strain", 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    propagate(world)
    if narrate:
        world.say(f"{actor.id} started {task.gerund}, and the trail already felt close and steep.")


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventures in the woods.")


def setting_line(world: World, task: Task) -> None:
    if world.setting.path_narrow:
        world.say(f"The path was narrow, and the trees leaned close as if they were listening.")
    else:
        world.say(f"The clearing was open, with a ring of stones waiting for a careful fire.")
    world.say(f"{task.strain.capitalize()} made the day feel like a real expedition.")


def want(world: World, hero: Entity, task: Task, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(f"{hero.id} wanted to {task.verb}, because {hero.pronoun('possessive')} {prize.label} looked useful and important.")


def warn(world: World, parent: Entity, hero: Entity, task: Task, prize: Entity) -> bool:
    pred = predict_problem(world, hero, task, prize)
    if not risk_for(task, prize):
        return False
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1.0
    world.say(f'"Careful," {parent.id} said. "If you hurry, you may {task.risk}."')
    world.facts["predicted_strain"] = pred["strain"]
    return True


def conflict_beats(world: World, hero: Entity, task: Task) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(f"{hero.id} frowned. {hero.pronoun().capitalize()} did not like being told to slow down.")
    world.say(f"{hero.pronoun().capitalize()} tried to {task.rush},")


def join_help(world: World, parent: Entity, hero: Entity, task: Task, prize: Entity) -> Optional[Gear]:
    gear = choose_gear(task, prize)
    if gear is None:
        return None
    world.say(f"Then {parent.id} looked at the bundle and said, \"Let's {gear.prep}.\"")
    world.say(f"That sounded like a better adventure, so they {gear.tail}.")
    return gear


def resolve(world: World, hero: Entity, parent: Entity, task: Task, prize: Entity, gear: Gear) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(f"{hero.id}'s face softened, and {hero.pronoun()} nodded.")
    world.say(f"Together they used {gear.label}, so the load felt lighter and the path felt wide enough after all.")
    world.say(f"By the end, {hero.id} was {task.gerund}, and the {prize.label} stayed steady in safe hands.")


def tell(setting: Setting, task: Task, prize_cfg: Prize,
         hero_name: str = "Ari", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region, plural=prize_cfg.plural))

    intro(world, hero)
    world.para()
    setting_line(world, task)
    want(world, hero, task, prize)
    warn(world, parent, hero, task, prize)
    conflict_beats(world, hero, task)
    world.para()
    gear = join_help(world, parent, hero, task, prize)
    if gear:
        resolve(world, hero, parent, task, prize, gear)
        world.facts["gear"] = gear
    world.facts.update(hero=hero, parent=parent, prize=prize, task=task, setting=setting, resolved=gear is not None)
    return world


# ---------------------------------------------------------------------------
# Story generation and Q&A
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            task = _safe_lookup(TASKS, tid)
            for pid, prize in PRIZES.items():
                if risk_for(task, prize) and choose_gear(task, prize):
                    for gender in GENDERS:
                        combos.append((sid, tid, pid, gender))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    task: Task = _safe_fact(world, f, "task")
    prize: Prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short adventure story for a young child about "{task.keyword}" and a {prize.label}.',
        f"Tell a gentle story where {hero.id} wants to {task.verb} but a grown-up worries about the {prize.label}.",
        f"Write a woodland adventure with a conflict, a safer plan, and the word faggot in its older meaning of a bundle of sticks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    task: Task = _safe_fact(world, f, "task")
    prize: Prize = _safe_fact(world, f, "prize")
    gear: Gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the woods?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because if {hero.id} hurried, the {prize.label} could be dropped or strained on the narrow path.",
        ),
        QAItem(
            question=f"What helped the two of them solve the problem?",
            answer=f"{gear.label.capitalize()} helped them share the load and keep the bundle steady.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt proud and calmer after the plan worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [
        QAItem(
            question="What is a faggot in this story?",
            answer="In this story, a faggot means a bundle of sticks tied together for carrying or burning.",
        ),
        QAItem(
            question="Why do people use a carrying pole?",
            answer="People use a carrying pole to share weight more evenly and make a heavy load easier to carry.",
        ),
        QAItem(
            question="What is a narrow path?",
            answer="A narrow path is a trail with little room on either side, so people need to walk carefully.",
        ),
    ]
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="woods", task="carry_faggot", prize="bundle", name="Ari", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="camp", task="build_fire", prize="bundle", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="ridge", task="cross_log", prize="basket", name="Nia", gender="girl", parent="mother", trait="brave"),
]


def explain_rejection(task: Task, prize: Prize) -> str:
    if not risk_for(task, prize):
        return "(No story: that task does not honestly put the prize at risk.)"
    return "(No story: there is no reasonable way to solve this conflict with the gear in the catalog.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld with a conflict around a faggot of sticks.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "prize", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not risk_for(task, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_stories()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "gender", None) is None or c[3] == getattr(args, "gender", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize, gender = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
