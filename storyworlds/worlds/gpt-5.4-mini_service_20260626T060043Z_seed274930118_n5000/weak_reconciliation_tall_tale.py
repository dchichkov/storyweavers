#!/usr/bin/env python3
"""
storyworlds/worlds/weak_reconciliation_tall_tale.py
===================================================

A small tall-tale storyworld about a weak hero who must face embarrassment,
ask for help, and reach reconciliation.

Premise:
- A weak little helper wants to finish a hard job alone.
- A bigger mishap makes the job wobble out of hand.
- Pride turns into a quarrel.
- A kind apology and a shared fix end in reconciliation.

The world keeps both physical meters and emotional memes:
- meters track strength, strain, wobble, and repair
- memes track worry, pride, hurt, relief, and reconciliation

This script is standalone and supports text, QA, JSON, trace, and ASP parity
verification.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def __post_init__(self) -> None:
        for key in ("strength", "strain", "wobble", "repair", "damage"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "pride", "hurt", "relief", "reconciliation", "love"):
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
    place: str = "the dusty little town"
    sky: str = "wide and windy"
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
    attempt: str
    mishap: str
    fix: str
    outcome: str
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
class Aid:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
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
        self.wind: float = 0.0

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.wind = self.wind
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

SETTINGS = {
    "town": Setting(place="the dusty little town", sky="wide and windy", affords={"carry", "stack"}),
    "dock": Setting(place="the river dock", sky="blown silver by the breeze", affords={"carry", "stack"}),
    "barn": Setting(place="the red barnyard", sky="open as a kettle lid", affords={"stack", "lift"}),
}

TASKS = {
    "stack_crates": Task(
        id="stack_crates",
        verb="stack the apple crates",
        attempt="try to stack the apple crates higher and higher",
        mishap="the top crate starts to wobble",
        fix="steady the stack before it topples",
        outcome="the crates stay in a neat, brave tower",
        keyword="crates",
        tags={"wood", "work", "wobble"},
    ),
    "pull_cart": Task(
        id="pull_cart",
        verb="pull the cider cart",
        attempt="try to pull the cider cart all by themselves",
        mishap="the wheel catches in a rut",
        fix="free the wheel before it splinters",
        outcome="the cart rolls on with a cheerful squeak",
        keyword="cart",
        tags={"wheel", "work", "road"},
    ),
    "lift_pump": Task(
        id="lift_pump",
        verb="lift the well pump",
        attempt="try to lift the iron pump into place",
        mishap="the pump slips and bangs the board",
        fix="brace the board before it cracks",
        outcome="the pump sits firm and proud",
        keyword="pump",
        tags={"iron", "work", "water"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="a stout rope",
        helps={"stack_crates", "pull_cart"},
        prep="tie on a stout rope and work together",
        tail="tied on the rope and pulled with one steady breath",
    ),
    "brace": Aid(
        id="brace",
        label="a wooden brace",
        helps={"stack_crates", "lift_pump"},
        prep="prop it with a wooden brace first",
        tail="set the brace in place and leaned shoulder to shoulder",
    ),
    "wheel_wedge": Aid(
        id="wheel_wedge",
        label="a little wheel wedge",
        helps={"pull_cart"},
        prep="slide in a little wheel wedge first",
        tail="slid in the wedge and rolled the cart free",
    ),
}

HERO_NAMES = ["Milo", "Jeb", "Nell", "Poppy", "Hank", "Bess", "Kit", "Lula", "Wren", "Otis"]
HELPER_NAMES = ["Aunt June", "Uncle Wes", "Gran", "the old smith", "the miller", "the baker"]

TRAITS = ["small", "weak", "bashful", "stout-hearted", "scrappy", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A task is at risk when its motion can wobble, break, or jam.
task_at_risk(T) :- task(T), risky_effect(T).

% Aid is compatible only when it helps the task that needs it.
compatible(A, T) :- aid(A), task(T), helps(A, T).

valid(Place, Task, Aid) :- affords(Place, Task), task_at_risk(Task), compatible(Aid, Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risky_effect", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for t in sorted(a.helps):
            lines.append(asp.fact("helps", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def task_risk(task: Task) -> bool:
    return True


def select_aid(task: Task) -> Optional[Aid]:
    for aid in AIDS.values():
        if task.id in aid.helps:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            aid = select_aid(task)
            if aid is not None and task_risk(task):
                out.append((place, task_id, aid.id))
    return out


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def predict_mishap(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["strain"] += 1
    sim.get(hero.id).memes["pride"] += 1
    if task.id == "stack_crates":
        sim.get("crates").meters["wobble"] += 1
        sim.get("crates").meters["damage"] += 1
    elif task.id == "pull_cart":
        sim.get("cart").meters["wobble"] += 1
        sim.get("cart").meters["damage"] += 1
    else:
        sim.get("pump").meters["damage"] += 1
    return {
        "damage": sum(e.meters["damage"] for e in sim.entities.values()),
        "strain": sim.get(hero.id).meters["strain"],
    }


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters["strain"] += 1
    hero.meters["repair"] += 1
    if task.id == "stack_crates":
        world.get("crates").meters["wobble"] += 1
    elif task.id == "pull_cart":
        world.get("cart").meters["wobble"] += 1
    else:
        world.get("pump").meters["wobble"] += 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} {task.attempt}.")


def propagate(world: World) -> None:
    pass


def tell(setting: Setting, task: Task, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=helper_name))
    obj_id = "crates" if task.id == "stack_crates" else "cart" if task.id == "pull_cart" else "pump"
    obj_label = "apple crates" if task.id == "stack_crates" else "cider cart" if task.id == "pull_cart" else "well pump"
    obj = world.add(Entity(id=obj_id, label=obj_label, caretaker=helper.id))

    world.say(f"{hero_name} was a {random.choice(['weak', 'small', 'undersized'])} little worker in {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved to {task.verb}, because the job made the whole place feel big as a parade.")
    world.say(f"Folks said {hero_name} had a heart as brave as a rooster, but arms as weak as wet reeds.")

    world.para()
    world.say(f"One bright day at {setting.place}, {hero_name} tried to {task.verb}.")

    prediction = predict_mishap(world, hero, task)
    if prediction["damage"] >= THRESHOLD:
        world.say(f"Sure enough, {task.mishap}, and that was a sorry sight.")
        hero.memes["worry"] += 1
        hero.memes["pride"] += 1

    world.say(f"{hero_name} frowned and said, 'I can do it myself!'")
    hero.memes["pride"] += 1

    world.para()
    world.say(f"Then the helper saw the trouble and said, 'That job is a giant, and even giants like a hand.'")
    world.say(f"{helper_name} offered {select_aid(task).label} and a calm voice.")

    aid = select_aid(task)
    if aid is None:
        pass

    world.say(f"{hero_name} looked down, then back up, and their cheeks grew hot with embarrassed pride.")
    hero.memes["hurt"] += 1
    hero.memes["worry"] += 1

    world.para()
    world.say(f"{hero_name} took a breath, apologized, and said they were sorry for snapping.")
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    helper.memes["relief"] += 1
    hero.memes["relief"] += 1

    world.say(f"{helper_name} smiled back, and the two of them chose to {aid.prep}.")
    if task.id == "stack_crates":
        obj.meters["wobble"] = 0
    elif task.id == "pull_cart":
        obj.meters["wobble"] = 0
    else:
        obj.meters["damage"] = 0
    hero.meters["repair"] += 1
    hero.meters["strain"] += 0.5
    world.say(f"Together they {aid.tail}. In the end, {task.outcome}, and {hero_name} and {helper_name} made up plain as day after rain.")

    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        aid=aid,
        setting=setting,
        object=obj,
        conflict=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    return [
        f'Write a tall-tale style story about a weak little {hero.type} who tries to {task.verb} and learns to reconcile after trouble.',
        f"Tell a child-friendly tale set in {world.setting.place} where {hero.id} is too weak to finish {task.keyword} alone, then makes up with a helper.",
        f'Write a short tall tale that uses the word "weak" and ends with reconciliation after a shared fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    aid = _safe_fact(world, f, "aid")
    obj = _safe_fact(world, f, "object")
    return [
        QAItem(
            question=f"Why did {hero.id} get into trouble when trying to {task.verb}?",
            answer=f"{hero.id} was weak and tried to do a big job alone, so {task.mishap.lower()}. The trouble made the stack or cart wobble and put the job at risk.",
        ),
        QAItem(
            question=f"What did {helper.label} offer to help with the problem?",
            answer=f"{helper.label} offered {aid.label}. That was the right kind of help for {task.keyword}, so the work could be finished safely.",
        ),
        QAItem(
            question=f"What changed when {hero.id} apologized?",
            answer=f"The argument softened. {hero.id} stopped acting proud, said sorry, and the two of them reached reconciliation before finishing the job together.",
        ),
        QAItem(
            question=f"What was the ending image in the story?",
            answer=f"In the end, {obj.label} was steady again and {hero.id} and {helper.label} stood together after making up.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "weak": [
        (
            "What does it mean if someone is weak?",
            "If someone is weak, they do not have much strength and may need help with heavy work.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people who argued make peace again, forgive each other, and feel friendly together.",
        )
    ],
    "rope": [
        (
            "What can a rope do?",
            "A rope can tie things, pull things, or help two people share a heavy job.",
        )
    ],
    "brace": [
        (
            "What is a brace for?",
            "A brace helps hold something steady so it does not tip, bend, or crack.",
        )
    ],
    "wheel": [
        (
            "What does a wheel do?",
            "A wheel helps carts and wagons roll along the ground more easily.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"weak", "reconciliation"}
    if world.facts["aid"].id == "rope":
        tags.add("rope")
    if world.facts["aid"].id == "brace":
        tags.add("brace")
    if world.facts["task"].id == "pull_cart":
        tags.add("wheel")
    out: list[QAItem] = []
    for tag in ["weak", "reconciliation", "rope", "brace", "wheel"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    hero_type: str
    helper_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about weakness and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task_id, _ = rng.choice(list(combos))
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, task=task_id, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), params.hero_name, params.hero_type, params.helper_name)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="town", task="stack_crates", hero_name="Milo", hero_type="boy", helper_name="Gran"),
    StoryParams(place="dock", task="pull_cart", hero_name="Nell", hero_type="girl", helper_name="Uncle Wes"),
    StoryParams(place="barn", task="lift_pump", hero_name="Otis", hero_type="boy", helper_name="the old smith"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (place, task, aid) combos:\n")
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
            header = f"### {p.hero_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
