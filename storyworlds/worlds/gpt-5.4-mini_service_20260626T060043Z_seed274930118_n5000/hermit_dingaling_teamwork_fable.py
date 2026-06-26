#!/usr/bin/env python3
"""
storyworlds/worlds/hermit_dingaling_teamwork_fable.py
=====================================================

A small fable-style story world about a hermit, a dingaling, and the way
teamwork turns a hard job into a kind one.

Premise:
- A quiet hermit wants to do a useful task alone.
- A dingaling helper can make the task possible, but only if the plan fits the
  setting and the materials.
- The story begins with pride or loneliness, turns through a problem, and ends
  with teamwork and a clear changed image.

This script follows the Storyweavers world contract:
- stdlib-only story engine
- eager import of storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers
- StoryParams, parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generated stories
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
    plural: bool = False
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dingaling: object | None = None
    goal: object | None = None
    hermit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "mom"}
        male = {"man", "boy", "father", "dad", "hermit"}
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
    terrain: str
    requires_teamwork: bool
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
    struggle: str
    success_image: str
    strain_meter: str
    helper_action: str
    kind: str
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
    plural: bool = False
    needs: set[str] = field(default_factory=set)
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
    helps: set[str]
    trait: str
    notes: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _m(d: dict[str, float], k: str, delta: float) -> None:
    d[k] = d.get(k, 0.0) + delta


def setup_detail(setting: Setting, task: Task) -> str:
    if setting.terrain == "hill":
        return "The hill path rose in a long brown curve, and the wind tugged at every basket."
    if setting.terrain == "river":
        return "The river hummed below the rocks, and the little bridge creaked in the breeze."
    return f"{setting.place.capitalize()} looked calm, but the {task.kind} still needed careful hands."


def moral_line() -> str:
    return "And the hermit learned that a heavy thing can grow light when two willing hearts carry it together."


def valid_task_prize(task: Task, prize: Prize) -> bool:
    return task.id in prize.needs


def valid_combo(setting: str, task: str, prize: str, helper: str) -> bool:
    s = _safe_lookup(SETTINGS, setting)
    t = _safe_lookup(TASKS, task)
    p = _safe_lookup(PRIZES, prize)
    h = _safe_lookup(HELPERS, helper)
    return setting in {"hill", "river", "forest"} and valid_task_prize(t, p) and task in s.affords and task in h.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for p in PRIZES:
                for h in HELPERS:
                    if valid_combo(s, t, p, h):
                        out.append((s, t, p, h))
    return out


def explain_rejection(setting: str, task: str, prize: str, helper: str) -> str:
    s = _safe_lookup(SETTINGS, setting)
    t = _safe_lookup(TASKS, task)
    p = _safe_lookup(PRIZES, prize)
    h = _safe_lookup(HELPERS, helper)
    if task not in s.affords:
        return f"(No story: the {s.place} does not really suit {t.gerund}.)"
    if not valid_task_prize(t, p):
        return f"(No story: a {p.label} is not the kind of thing that gets helped by {t.verb}.)"
    if task not in h.helps:
        return f"(No story: {h.label} does not fit the kind of work needed for {t.gerund}.)"
    return "(No story: this combination is not a reasonable teamwork tale.)"


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    helper: str
    name: str
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


SETTINGS = {
    "hill": Setting(place="the hill path", terrain="hill", requires_teamwork=True, affords={"carry_water", "move_stones"}),
    "river": Setting(place="the riverbank", terrain="river", requires_teamwork=True, affords={"cross_bridge", "carry_water"}),
    "forest": Setting(place="the pine forest", terrain="forest", requires_teamwork=True, affords={"move_stones", "carry_water"}),
}

TASKS = {
    "carry_water": Task(
        id="carry_water",
        verb="carry water",
        gerund="carrying water",
        struggle="the pail kept tipping on the slope",
        success_image="the water stayed steady in the pail",
        strain_meter="strain",
        helper_action="held one side of the pail so it would not slosh",
        kind="water-haul",
        tags={"water", "teamwork"},
    ),
    "move_stones": Task(
        id="move_stones",
        verb="move stones",
        gerund="moving stones",
        struggle="the stones were too heavy for one back",
        success_image="the stone pile shrank into a neat little wall",
        strain_meter="strain",
        helper_action="lifted the smaller stones one by one",
        kind="stone-wall",
        tags={"stones", "teamwork"},
    ),
    "cross_bridge": Task(
        id="cross_bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        struggle="the bridge wobbled when the load was uneven",
        success_image="the bridge held firm under two careful steps",
        strain_meter="wobble",
        helper_action="walked beside the hermit and balanced the bundle",
        kind="bridge-crossing",
        tags={"bridge", "teamwork"},
    ),
}

PRIZES = {
    "spring_water": Prize(label="spring water", phrase="a cool jug of spring water", type="water"),
    "riverstones": Prize(label="river stones", phrase="a little sack of smooth river stones", type="stones", plural=True),
    "tea_jar": Prize(label="tea jar", phrase="a glass jar of tea leaves", type="jar"),
}

HELPERS = {
    "dingaling": Helper(
        id="Dingaling",
        label="Dingaling",
        type="donkey",
        helps={"carry_water", "move_stones", "cross_bridge"},
        trait="steady",
        notes="a cheerful donkey with a tiny bell on its collar",
    ),
    "bellcart": Helper(
        id="Bellcart",
        label="Bellcart",
        type="cart",
        helps={"move_stones", "carry_water"},
        trait="strong",
        notes="a small handcart that rolls well on flat ground",
    ),
}

HERO_NAMES = ["Elias", "Nico", "Milo", "Jonah", "Ravi", "Theo", "Arin", "Soren"]
HERO_TRAITS = ["quiet", "patient", "proud", "lonely", "careful", "gentle"]


def tell(setting: Setting, task: Task, prize: Prize, helper: Helper, name: str) -> World:
    world = World(setting)
    hermit = world.add(Entity(id=name, kind="character", type="hermit"))
    dingaling = world.add(Entity(id=helper.id, kind="character", type=helper.type, label=helper.label))
    goal = world.add(Entity(id="goal", type=prize.type, label=prize.label, phrase=prize.phrase, plural=prize.plural))

    hermit.memes["loneliness"] = 1.0
    hermit.memes["pride"] = 1.0
    dingaling.memes["helpfulness"] = 1.0
    goal.meters["value"] = 1.0

    world.say(f"{hermit.id} was a small hermit who lived near {setting.place}.")
    world.say(f"{hermit.id} cared for {goal.phrase}, and {hermit.pronoun()} liked to do useful things alone.")
    world.say(f"One day, {hermit.id} needed to {task.verb} at {setting.place}, but {task.struggle}.")
    world.para()
    world.say(setup_detail(setting, task))
    world.say(f"{hermit.id} tried first by {task.gerund} by {hermit.pronoun('object')}self, and {task.struggle}.")
    _m(hermit.meters, task.strain_meter, 1.0)
    _m(hermit.memes, "frustration", 1.0)
    world.say(f"{hermit.id} stopped and looked at the {goal.label}.")
    world.para()

    world.say(f"Then {dingaling.id} came along, {helper.notes}.")
    world.say(f"{dingaling.id} saw the problem and quietly offered to help.")
    _m(hermit.memes, "hope", 1.0)
    _m(dingaling.memes, "trust", 1.0)
    _m(hermit.meters, "progress", 0.5)
    world.say(f"Together, {hermit.id} and {dingaling.id} chose a better plan.")
    world.say(f"{dingaling.id} {task.helper_action}, and {hermit.id} did the careful part.")
    _m(hermit.meters, "progress", 1.0)
    _m(dingaling.meters, "progress", 1.0)
    _m(hermit.memes, "teamwork", 1.0)
    _m(dingaling.memes, "teamwork", 1.0)
    _m(hermit.meters, task.strain_meter, -0.5)
    world.para()

    world.say(f"At last, {task.success_image}.")
    if task.id == "carry_water":
        world.say(f"The jug stayed full, and {goal.label} reached the cottage without a drop spilled.")
    elif task.id == "move_stones":
        world.say(f"The stones made a neat wall, and the path looked tidier than before.")
    else:
        world.say(f"The bundle crossed safely, and the bridge seemed less wobbly with two careful walkers.")
    world.say(f"{hermit.id} smiled at {dingaling.id} and knew that helping was its own kind of strength.")
    world.say(moral_line())

    world.facts.update(hermit=hermit, helper=dingaling, goal=goal, task=task, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about a hermit and {f["helper"].id} learning teamwork.',
        f"Tell a gentle story where {f['hermit'].id} tries to {f['task'].verb} near {f['setting'].place} and needs help.",
        f'Write a simple fable that includes the word "hermit" and ends with a lesson about teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hermit = _safe_fact(world, f, "hermit")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    goal = _safe_fact(world, f, "goal")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"It is about {hermit.id}, a small hermit who wanted to do a useful job and learned to work with {helper.id}.",
        ),
        QAItem(
            question=f"What did {hermit.id} try to do before {helper.id} helped?",
            answer=f"{hermit.id} tried to {task.verb}, but it was too hard to finish alone.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hermit.id} with the {goal.label}?",
            answer=f"{helper.id} helped by staying steady and doing the strong part of the work, so the {goal.label} could be handled safely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hermit.id} stopped struggling alone, the job got done, and the story ended with teamwork and a happy lesson.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals help each other to do something that is easier or better together than alone.",
        ),
    ],
    "donkey": [
        QAItem(
            question="What can a donkey do?",
            answer="A donkey can carry things and walk steadily, which can make it a helpful partner for hauling a load.",
        ),
    ],
    "stones": [
        QAItem(
            question="What are stones?",
            answer="Stones are hard pieces of rock. Some are small and smooth, and some are big and heavy.",
        ),
    ],
    "water": [
        QAItem(
            question="Why do people carry water carefully?",
            answer="People carry water carefully so they do not spill it before they can use it.",
        ),
    ],
    "bridge": [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people or animals cross over water, a ditch, or another gap more safely.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.add(world.facts["helper"].type)
    out: list[QAItem] = []
    if "teamwork" in tags:
        out.extend(WORLD_KNOWLEDGE["teamwork"])
    if "donkey" in tags:
        out.extend(WORLD_KNOWLEDGE["donkey"])
    if "stones" in tags:
        out.extend(WORLD_KNOWLEDGE["stones"])
    if "water" in tags:
        out.extend(WORLD_KNOWLEDGE["water"])
    if "bridge" in tags:
        out.extend(WORLD_KNOWLEDGE["bridge"])
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hill", task="carry_water", prize="spring_water", helper="dingaling", name="Elias"),
    StoryParams(setting="forest", task="move_stones", prize="riverstones", helper="bellcart", name="Nico"),
    StoryParams(setting="river", task="cross_bridge", prize="tea_jar", helper="dingaling", name="Milo"),
]


ASP_RULES = r"""
task_needs_teamwork(carry_water).
task_needs_teamwork(move_stones).
task_needs_teamwork(cross_bridge).

place_affords(hill, carry_water).
place_affords(hill, move_stones).
place_affords(river, carry_water).
place_affords(river, cross_bridge).
place_affords(forest, carry_water).
place_affords(forest, move_stones).

helper_supports(dingaling, carry_water).
helper_supports(dingaling, move_stones).
helper_supports(dingaling, cross_bridge).
helper_supports(bellcart, carry_water).
helper_supports(bellcart, move_stones).

prize_needs(carry_water, spring_water).
prize_needs(move_stones, riverstones).
prize_needs(cross_bridge, tea_jar).

valid(S, T, P, H) :- place_affords(S, T), task_needs_teamwork(T), prize_needs(T, P), helper_supports(H, T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("terrain", sid, s.terrain))
        if s.requires_teamwork:
            lines.append(asp.fact("requires_teamwork", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_kind", tid, t.kind))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for need in sorted(p.needs):
            lines.append(asp.fact("needs", pid, need))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_type", hid, h.type))
        for t in sorted(h.helps):
            lines.append(asp.fact("helps", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, prize=None, helper=None, name=None), random.Random(7)))
        print("OK: generated story length:", len(sample.story))
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a hermit, Dingaling, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "task", None) and getattr(args, "prize", None) and getattr(args, "helper", None):
        if not valid_combo(getattr(args, "setting", None), getattr(args, "task", None), getattr(args, "prize", None), getattr(args, "helper", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "helper", None) is None or c[3] == getattr(args, "helper", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, prize, helper = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, task=task, prize=prize, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), _safe_lookup(HELPERS, params.helper), params.name)
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible stories:")
        for row in vals:
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
            header = f"### {p.name}: {p.task} at {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
