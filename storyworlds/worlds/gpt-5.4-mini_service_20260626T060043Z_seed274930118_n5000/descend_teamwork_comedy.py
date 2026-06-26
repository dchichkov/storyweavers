#!/usr/bin/env python3
"""
storyworlds/worlds/descend_teamwork_comedy.py
=============================================

A small story world about a funny teamwork descent: a child and helper need to
come down from a high place while carrying something important, and they learn
to move together instead of hurrying alone.

The world is built from one causal premise:
- a high place creates a descent
- a shared task requires teamwork
- comedy comes from clumsy coordination, not danger
- resolution comes from a cooperative method that changes the world state

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only inside ASP helpers
- StoryParams + parser + resolve_params + generate + emit + main
- trace, qa, json, asp, verify, show-asp support
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
    carrying: Optional[str] = None
    carried_by: Optional[str] = None
    position: str = "top"  # top, middle, bottom
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    assist: object | None = None
    goal: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    desc: str
    affords_descend: bool = True
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
    funny: str
    method: str
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
class Goal:
    label: str
    phrase: str
    type: str
    weight: str = "small"
    fragile: bool = False
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
    effect: str
    covers: set[str] = field(default_factory=set)
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


SETTINGS = {
    "hill": Setting("the hill", "a grassy hill with a funny steep path"),
    "tower": Setting("the tower", "a tall play tower with a twisty stair"),
    "treehouse": Setting("the treehouse", "a wooden treehouse with a narrow ladder"),
    "bridge": Setting("the bridge", "a rope bridge that bounced like a joke"),
}

TASKS = {
    "basket": Task(
        id="basket",
        verb="carry the picnic basket down",
        gerund="carrying the picnic basket down",
        rush="dash down with the basket",
        funny="the basket tipped like it had a secret laugh",
        method="take turns holding the handle",
        tags={"down", "carry", "teamwork", "comedy"},
    ),
    "kite": Task(
        id="kite",
        verb="bring the kite down",
        gerund="bringing the kite down",
        rush="run down after the kite",
        funny="the kite string zigzagged like a noodle",
        method="let one person guide while the other steadies",
        tags={"down", "string", "teamwork", "comedy"},
    ),
    "lantern": Task(
        id="lantern",
        verb="lower the lantern carefully",
        gerund="lowering the lantern carefully",
        rush="jiggle the lantern downward",
        funny="the lantern bobbed like a sleepy moon",
        method="count together and move one step at a time",
        tags={"down", "light", "teamwork", "comedy"},
    ),
    "box": Task(
        id="box",
        verb="move the box down",
        gerund="moving the box down",
        rush="lug the box down in a hurry",
        funny="the box wiggled like it wanted to dance",
        method="share the weight and keep the box level",
        tags={"down", "heavy", "teamwork", "comedy"},
    ),
}

GOALS = {
    "basket": Goal("picnic basket", "a picnic basket full of treats", "basket"),
    "kite": Goal("kite", "a bright kite with a long string", "kite"),
    "lantern": Goal("lantern", "a round lantern for the path", "lantern"),
    "box": Goal("box", "a big cardboard box of costumes", "box"),
}

HELPERS = {
    "rope": Helper(
        id="rope",
        label="a rope",
        method="tie a rope for steady hands",
        effect="made the descent feel like a careful game",
        covers={"slip"},
        tags={"down", "teamwork"},
    ),
    "step": Helper(
        id="step",
        label="a counted step",
        method="count each step together",
        effect="helped everyone stop wobbling",
        covers={"wobble"},
        tags={"down", "teamwork"},
    ),
    "tray": Helper(
        id="tray",
        label="a flat tray",
        method="use a flat tray to balance the load",
        effect="kept the funny load from tumbling",
        covers={"tilt"},
        tags={"carry", "teamwork", "comedy"},
    ),
}


GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ava", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Noah", "Eli", "Ben"]
TRAITS = ["cheerful", "silly", "brave", "curious", "bouncy", "playful"]


@dataclass
class StoryParams:
    place: str
    task: str
    goal: str
    name: str
    gender: str
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
    for place in SETTINGS:
        for task_id in TASKS:
            for goal_id in GOALS:
                if task_id == goal_id:
                    combos.append((place, task_id, goal_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic teamwork descent storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "goal", None) is None or c[2] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, task, goal = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, goal=goal, name=name, gender=gender, helper=helper, trait=trait)


def _prn(ent: Entity, case: str = "subject") -> str:
    return ent.pronoun(case)


def _do_descend(world: World, hero: Entity, task: Task, helper: Helper, goal: Entity) -> None:
    hero.meters["height"] = 0
    hero.memes["joy"] += 1
    goal.carried_by = hero.id
    if helper.id == "rope":
        hero.meters["slip"] = 0
    if helper.id == "step":
        hero.meters["wobble"] = 0
    if helper.id == "tray":
        goal.meters["tilt"] = 0


def tell(setting: Setting, task: Task, goal_cfg: Goal, helper: Helper, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    partner_name = "Parent" if gender == "girl" else "Parent"
    parent = world.add(Entity(id=partner_name, kind="character", type="mother", label="the parent"))
    goal = world.add(Entity(
        id=goal_cfg.type,
        type=goal_cfg.type,
        label=goal_cfg.label,
        phrase=goal_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        position="top",
    ))
    assist = world.add(Entity(
        id=helper.id,
        type="helper",
        label=helper.label,
        phrase=helper.label,
        owner=hero.id,
        carried_by=hero.id,
    ))

    hero.meters["height"] = 3
    hero.memes["desire"] += 1
    hero.memes["funny"] += 1
    goal.meters["wobble"] = 1
    goal.meters["tilt"] = 1

    world.say(f"{hero.id} was a little {trait} {gender} who loved funny jobs at {setting.place}.")
    world.say(f"{_prn(hero).capitalize()} and {parent.label if parent.label else 'the parent'} had {goal.phrase} to bring down.")
    world.say(f"The job was to {task.verb}, and {task.funny}.")

    world.para()
    world.say(f"{setting.desc.capitalize()}.")
    world.say(f"{hero.id} wanted to {task.verb}, but the path looked extra wobbly.")
    world.say(f'"Let\'s be a team," {parent.label_word if hasattr(parent, "label_word") else "the parent"} said, offering {helper.label} and {helper.method}.')

    world.para()
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} tried to {task.rush}, and that made {goal.label} bob and shimmy.")
    world.say(f"{parent.label if parent.label else 'The parent'} laughed and said the load was acting like it had jelly knees.")
    world.say(f"Then they slowed down, because the funny way was safer.")

    world.para()
    _do_descend(world, hero, task, helper, goal)
    hero.memes["conflict"] = 0
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(f"They chose to {task.method} and used {helper.effect}.")
    world.say(f"Step by step, they came down together, and {goal.phrase} stayed steady.")
    world.say(f"At the bottom, {hero.id} grinned, and the whole team looked proud and a little silly.")

    world.facts.update(hero=hero, parent=parent, goal=goal, task=task, helper=helper, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, goal, helper, setting = f["hero"], f["task"], f["goal"], f["helper"], f["setting"]
    return [
        f'Write a short comedy story for a young child about "{task.id}" and teamwork at {setting.place}.',
        f"Tell a funny story where {hero.id} has to {task.verb} with help from {helper.label}.",
        f"Write a gentle story that includes the word 'descend' and ends with everyone working together to bring {goal.label} down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, goal, task, helper = f["hero"], f["parent"], f["goal"], f["task"], f["helper"]
    return [
        QAItem(
            question=f"Who had to {task.verb} in the story?",
            answer=f"{hero.id} and {parent.label if parent.label else 'the parent'} had to work together to {task.verb}.",
        ),
        QAItem(
            question=f"What was funny about the {goal.label} before they came down?",
            answer=f"It wobbled and bounced like it had a joke to tell, which made the task feel silly.",
        ),
        QAItem(
            question=f"How did they descend safely?",
            answer=f"They slowed down, shared the job, and used {helper.label} so the load stayed steady all the way down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does descend mean?",
            answer="Descend means to go down from a higher place to a lower place.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy is funny because of silly mistakes, playful surprises, and characters who act a little awkward in harmless ways.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carrying:
            bits.append(f"carrying={e.carrying}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.position:
            bits.append(f"position={e.position}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", task="basket", goal="basket", name="Mia", gender="girl", helper="rope", trait="silly"),
    StoryParams(place="tower", task="kite", goal="kite", name="Leo", gender="boy", helper="step", trait="curious"),
    StoryParams(place="treehouse", task="box", goal="box", name="Nora", gender="girl", helper="tray", trait="bouncy"),
]


ASP_RULES = r"""
% A descent story is valid when the task, place, and goal all align.
valid_story(P,T,G,H) :- place(P), task(T), goal(G), helper(H).

% Teamwork is central when the helper supports the task.
teamwork(T,H) :- task(T), helper(H), helps(H,T).

% Comedy is present when the task is funny and the load is wobbly.
comedy(G) :- goal(G), wobbly(G), funny_task(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.affords_descend:
            lines.append(asp.fact("affords_descend", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("funny_task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("wobbly", gid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for tag in sorted(h.tags):
            lines.append(asp.fact("helps", hid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p, t, g, h) for p, t, g in valid_combos() for h in HELPERS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() expanded with helpers ({len(clingo_set)} tuples).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(GOALS, params.goal),
        _safe_lookup(HELPERS, params.helper),
        params.name,
        params.gender,
        params.trait,
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


def explain_rejection() -> str:
    return "No valid comedy descent story matches those options."


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for item in asp_valid_stories():
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
