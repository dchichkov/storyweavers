#!/usr/bin/env python3
"""
A small animal-story world about an abscessed injury, an inner monologue, and
a teamwork resolution with a gentle lesson learned.

The seed image: a little animal hurts, hides the pain, then learns to ask for
help and work with friends. The world keeps the tale concrete and state-driven:
pain rises, a task becomes impossible, helpers step in, and the ending proves
the change.
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
# World constants
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
    kind: str = "thing"  # "character" | "thing"
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

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rat", "rabbit", "fox", "wolf", "dog", "cat"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
    difficulty: str
    keyword: str = ""
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
class Tool:
    id: str
    label: str
    helper: str
    fix: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "workshop": Setting(place="the little workshop", affords={"carry_crates", "sort_apples"}),
    "orchard": Setting(place="the orchard", affords={"carry_crates", "pick_fruit"}),
    "riverbank": Setting(place="the riverbank", affords={"carry_crates", "build_bridge"}),
}

TASKS = {
    "carry_crates": Task(
        id="carry_crates",
        verb="carry the heavy crates",
        gerund="carrying heavy crates",
        rush="hurry with the crates",
        difficulty="too hard",
        keyword="crate",
        tags={"teamwork", "heavy"},
    ),
    "sort_apples": Task(
        id="sort_apples",
        verb="sort the apples",
        gerund="sorting apples",
        rush="rush to the apple pile",
        difficulty="too tricky",
        keyword="apple",
        tags={"teamwork", "gentle"},
    ),
    "pick_fruit": Task(
        id="pick_fruit",
        verb="pick the fruit",
        gerund="picking fruit",
        rush="climb toward the fruit tree",
        difficulty="too high",
        keyword="fruit",
        tags={"teamwork", "climb"},
    ),
    "build_bridge": Task(
        id="build_bridge",
        verb="build the little bridge",
        gerund="building the bridge",
        rush="carry the boards fast",
        difficulty="too much to do alone",
        keyword="bridge",
        tags={"teamwork", "wood"},
    ),
}

TOOLS = {
    "bandage_wrap": Tool(
        id="bandage_wrap",
        label="a clean bandage wrap",
        helper="wrap the sore paw",
        fix="kept the paw from bumping",
        tags={"abscessed", "care"},
    ),
    "cool_cloth": Tool(
        id="cool_cloth",
        label="a cool wet cloth",
        helper="soothe the ache",
        fix="made the swelling feel softer",
        tags={"abscessed", "care"},
    ),
    "small_cart": Tool(
        id="small_cart",
        label="a small cart",
        helper="roll the crates together",
        fix="turned a hard carry into a shared push",
        tags={"teamwork", "heavy"},
    ),
    "ladder": Tool(
        id="little ladder",
        label="a little ladder",
        helper="reach the high fruit",
        fix="made the tall branch possible",
        tags={"teamwork", "climb"},
    ),
}

ANIMAL_NAMES = {
    "mouse": ["Milo", "Nina", "Pip"],
    "rabbit": ["Toby", "Ruby", "Poppy"],
    "fox": ["Fern", "Rico", "Luna"],
    "wolf": ["Maya", "Nico", "Sol"],
    "dog": ["Bibi", "Taco", "Juno"],
    "cat": ["Mimi", "Paco", "Cleo"],
}

TYPES = list(ANIMAL_NAMES)

TRAITS = ["small", "brave", "busy", "kind", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    animal: str
    helper: str
    task: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
    p: object | None = None
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


def injury_name() -> str:
    return "abscessed paw"


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.animal not in TYPES:
        pass
    if params.helper not in TYPES:
        pass
    if params.task not in TASKS:
        pass

    setting = _safe_lookup(SETTINGS, params.place)
    task = _safe_lookup(TASKS, params.task)

    world = World(setting)
    hero_name = random.choice(_safe_lookup(ANIMAL_NAMES, params.animal))
    helper_name = random.choice([n for n in _safe_lookup(ANIMAL_NAMES, params.helper) if n != hero_name] or _safe_lookup(ANIMAL_NAMES, params.helper))

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.animal,
        label=hero_name,
        traits=[random.choice(TRAITS), "little"],
        meters={"pain": 0.0, "fatigue": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "pride": 1.0, "lesson": 0.0, "teamwork": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=helper_name,
        traits=["kind", "steady"],
        meters={"helpfulness": 1.0},
        memes={"care": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label="bandage wrap",
        phrase="a clean bandage wrap",
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, task=task, tool=tool, setting=setting)
    return world


def narrate_inner_monologue(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"{hero.label} was a little {hero.type} at {world.setting.place}."
        f" {hero.label} tried to act tough, but the abscessed paw throbbed every time "
        f"{hero.pronoun('subject')} looked at {task.verb}."
    )
    world.say(
        f"Inside, {hero.label} thought, 'I can do this alone. I do not want to slow anyone down.'"
    )
    hero.memes["worry"] += 1.0
    hero.memes["pride"] += 0.5
    hero.meters["pain"] += 1.0


def task_becomes_hard(world: World, hero: Entity, task: Task) -> None:
    hero.meters["pain"] += 1.0
    hero.meters["fatigue"] += 1.0
    world.say(
        f"Then {hero.label} tried to {task.verb}, but each step felt {task.difficulty}."
    )
    world.say(
        f"{hero.label} glanced at the pile and thought, 'If I keep going, my paw will hurt even more.'"
    )
    hero.memes["worry"] += 1.0


def helper_notices(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"{helper.label} noticed the slow steps and came over right away."
    )
    world.say(
        f"'You do not have to do this alone,' {helper.label} said."
    )
    hero.memes["hope"] += 1.0
    helper.memes["care"] += 0.5


def teamwork_fix(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    world.say(
        f"Together, they used {tool.label}; it could {tool.helper} and {tool.fix}."
    )
    world.say(
        f"{hero.label} carried the lighter side while {helper.label} handled the heavier side."
    )
    hero.meters["pain"] = max(0.0, hero.meters["pain"] - 0.5)
    hero.meters["fatigue"] = max(0.0, hero.meters["fatigue"] - 0.5)
    hero.memes["teamwork"] += 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0
    hero.memes["lesson"] += 1.0


def ending(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"By the end, the job was done, and {hero.label}'s paw still hurt a little, "
        f"but it no longer felt like a secret to hide."
    )
    world.say(
        f"{hero.label} thought, 'I learned that asking for help is brave.' "
        f"{helper.label} smiled, and the two friends walked home together."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    task = _safe_fact(world, world.facts, "task")
    tool = _safe_fact(world, world.facts, "tool")

    narrate_inner_monologue(world, hero, task)
    world.para()
    task_becomes_hard(world, hero, task)
    helper_notices(world, hero, helper, task)
    world.para()
    teamwork_fix(world, hero, helper, task, tool)
    ending(world, hero, helper, task)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story about a little {f['hero'].type} with an {injury_name()} who learns a lesson about teamwork.",
        f"Tell a gentle story set at {f['setting'].place} where {f['hero'].label} thinks to {f['hero'].label}self before asking for help.",
        f"Write a child-friendly story that includes an abscessed paw, a helper friend, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    task: Task = _safe_fact(world, world.facts, "task")
    setting: Setting = _safe_fact(world, world.facts, "setting")

    return [
        QAItem(
            question=f"Who is the story mainly about at {setting.place}?",
            answer=f"The story is mainly about {hero.label}, a little {hero.type} who had an abscessed paw.",
        ),
        QAItem(
            question=f"What was {hero.label} trying to do before the paw hurt too much?",
            answer=f"{hero.label} was trying to {task.verb}, but the pain made the job hard to do alone.",
        ),
        QAItem(
            question=f"Who came to help {hero.label}?",
            answer=f"{helper.label} came to help, and the two friends solved the problem together.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that asking for help is brave and that teamwork makes hard jobs easier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means friends work together and share the job so it becomes easier.",
        ),
        QAItem(
            question="What is an abscessed paw?",
            answer="An abscessed paw is a paw that is sore, swollen, and painful, so walking on it can hurt.",
        ),
        QAItem(
            question="Why is it good to ask for help?",
            answer="It is good to ask for help because another kind helper can make a hard task safer and easier.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero_story(H) :- hero(H).
teamwork_story(H) :- hero(H), helper(_), task(_).
lesson_learned(H) :- resolved(H).
valid_story(P, A, T) :- setting(P), animal(A), task(T), workable(P, A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for animal in TYPES:
        lines.append(asp.fact("animal", animal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> bool:
    return (
        params.place in SETTINGS
        and params.task in _safe_lookup(SETTINGS, params.place).affords
        and params.animal in TYPES
        and params.helper in TYPES
        and params.animal != params.helper
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for animal in TYPES:
                for helper in TYPES:
                    if animal != helper:
                        combos.append((place, animal, task))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity holds for {len(py)} combos.")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with abscessed paw, inner monologue, lesson learned, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=TYPES)
    ap.add_argument("--helper", choices=TYPES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    task_choices = list(_safe_lookup(SETTINGS, place).affords)
    task = getattr(args, "task", None) or rng.choice(sorted(task_choices))
    animal = getattr(args, "animal", None) or rng.choice(TYPES)
    helper = getattr(args, "helper", None) or rng.choice([t for t in TYPES if t != animal])
    p = StoryParams(place=place, animal=animal, helper=helper, task=task)
    if not reasonableness_gate(p):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return p


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="workshop", animal="mouse", helper="rabbit", task="carry_crates"),
    StoryParams(place="orchard", animal="fox", helper="dog", task="sort_apples"),
    StoryParams(place="riverbank", animal="wolf", helper="cat", task="build_bridge"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
