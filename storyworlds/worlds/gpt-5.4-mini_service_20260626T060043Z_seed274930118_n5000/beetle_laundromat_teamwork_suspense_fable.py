#!/usr/bin/env python3
"""
storyworlds/worlds/beetle_laundromat_teamwork_suspense_fable.py
===============================================================

A small story world in a laundromat: a beetle, a helper, a missing thing,
and a suspenseful teamwork fable.

Seed tale behind the simulation:
---
A tiny beetle lived near a laundromat and loved order. One afternoon, a shiny
button slipped off a coat and vanished under a dryer. The beetle could not move
the heavy drum alone, but a mouse could slip into small places. Together they
timed their work before the cycle ended, found the button, and returned it just
in time. The beetle learned that small friends can do brave things when they
work together.
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
# Domain entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    beetle: object | None = None
    helper: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"beetle", "mouse", "sparrow", "child"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the laundromat"
    affords: set[str] = field(default_factory=lambda: {"button", "coin", "sock"})
    SETTING: object | None = None
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
    missing: str
    item: str
    hidden_in: str
    risky_cycle: str
    suspense_meter: str
    helper_type: str
    teamwork_move: str
    ending_image: str
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
class StoryParams:
    task: str
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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

TASKS = {
    "button": Task(
        id="button",
        missing="a shiny button",
        item="button",
        hidden_in="under the dryer",
        risky_cycle="spin cycle",
        suspense_meter="countdown",
        helper_type="mouse",
        teamwork_move="slip beneath the dryer and nudge the button loose",
        ending_image="the shiny button back in the coat pocket",
        tags={"button", "shiny", "metal"},
    ),
    "coin": Task(
        id="coin",
        missing="a copper coin",
        item="coin",
        hidden_in="behind the soap shelf",
        risky_cycle="tumble cycle",
        suspense_meter="timer",
        helper_type="sparrow",
        teamwork_move="flutter up to the shelf and point out the coin",
        ending_image="the copper coin resting on the counter",
        tags={"coin", "metal", "small"},
    ),
    "sock": Task(
        id="sock",
        missing="one striped sock",
        item="sock",
        hidden_in="inside the lint tray",
        risky_cycle="dry cycle",
        suspense_meter="minute hand",
        helper_type="mouse",
        teamwork_move="push open the lint tray door while the beetle held watch",
        ending_image="the striped sock hanging safe on the line",
        tags={"sock", "cloth", "clean"},
    ),
}

HELPERS = {
    "mouse": Entity(id="mouse", kind="character", type="mouse", label="mouse"),
    "sparrow": Entity(id="sparrow", kind="character", type="sparrow", label="sparrow"),
}

BEETLE_NAMES = ["Bramble", "Milo", "Tansy", "Pip", "Clover", "Juno", "Buzzy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A task is reasonable when the missing thing can be found in the laundromat
% and the helper type matches the task's teamwork shape.
valid(Task, Helper) :- task(Task), helper(Helper), needs(Task, Helper).

% The beetle must need help to move the story forward.
needs(Task, Helper) :- task(Task), helper(Helper), requires(Task, Helper).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("place", "laundromat"))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("missing", tid, t.item))
        lines.append(asp.fact("hidden_in", tid, t.hidden_in))
        lines.append(asp.fact("requires", tid, t.helper_type))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(tid, t.helper_type) for tid, t in TASKS.items()}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return sorted((tid, t.helper_type) for tid, t in TASKS.items())


def explain_rejection(task: Task, helper: str) -> str:
    return (
        f"(No story: the {task.item} tale needs a {task.helper_type}, not a {helper}. "
        f"The helper must fit the tiny opening in the problem, or the fable has no honest teamwork.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def story_intro(world: World, beetle: Entity, task: Task) -> None:
    world.say(
        f"{beetle.id} was a small beetle who liked neat floors and kind deeds."
    )
    world.say(
        f"One day, {beetle.id} found that {task.missing} had vanished {task.hidden_in} at {world.setting.place}."
    )


def story_suspense(world: World, beetle: Entity, task: Task) -> None:
    beetle.memes["worry"] += 1
    beetle.memes["determination"] += 1
    world.say(
        f"The {task.risky_cycle} was already humming, and the {task.suspense_meter} kept moving toward the end."
    )
    world.say(
        f"{beetle.id} peered under the machine, but the space was too small for one brave beetle alone."
    )


def story_teamwork(world: World, beetle: Entity, helper: Entity, task: Task) -> None:
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0) + 1
    beetle.memes["hope"] += 1
    world.say(
        f"Then {helper.id} arrived, and the two of them made a plan."
    )
    world.say(
        f"{helper.id} could {task.teamwork_move}, while {beetle.id} kept a sharp eye on the clock."
    )
    world.say(
        f"They worked together before the last blink of the {task.suspense_meter}."
    )


def story_resolution(world: World, beetle: Entity, helper: Entity, task: Task) -> None:
    beetle.memes["joy"] += 1
    beetle.memes["worry"] = 0
    world.say(
        f"At last, they found {task.missing} and brought it back where it belonged."
    )
    world.say(
        f"{task.ending_image} showed how two small friends could finish a hard job."
    )
    world.say(
        f"{beetle.id} learned that a little helper's strength grows bigger when it is shared."
    )


def generate_world(task_id: str, helper_id: str, name: str) -> World:
    task = _safe_lookup(TASKS, task_id)
    helper_kind = helper_id
    world = World(SETTING)

    beetle = world.add(Entity(id=name, kind="character", type="beetle", label="beetle"))
    helper = world.add(Entity(id=helper_kind, kind="character", type=helper_kind, label=helper_kind))
    missing = world.add(Entity(id=task.item, kind="thing", type=task.item, label=task.item))

    beetle.meters["small"] = 1
    beetle.memes["care"] = 1
    helper.meters["small"] = 1
    missing.meters["lost"] = 1

    story_intro(world, beetle, task)
    world.para()
    story_suspense(world, beetle, task)
    world.para()
    story_teamwork(world, beetle, helper, task)
    story_resolution(world, beetle, helper, task)

    world.facts.update(
        beetle=beetle,
        helper=helper,
        task=task,
        missing=missing,
        place=world.setting.place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = _safe_fact(world, f, "task")
    return [
        f'Write a short fable set in a laundromat about a beetle and a {task.helper_type} who work together to find {task.missing}.',
        f'Tell a suspenseful story for a young child about {f["beetle"].id} the beetle, a lost {task.item}, and a helpful {task.helper_type}.',
        f'Write a simple teamwork story in the laundromat that ends with {task.ending_image}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    beetle: Entity = _safe_fact(world, f, "beetle")
    helper: Entity = _safe_fact(world, f, "helper")
    task: Task = _safe_fact(world, f, "task")
    return [
        QAItem(
            question=f"What kind of creature is {beetle.id}?",
            answer=f"{beetle.id} is a beetle, a tiny insect who lives near the laundromat in this story.",
        ),
        QAItem(
            question=f"What went missing at the laundromat?",
            answer=f"{task.missing} went missing {task.hidden_in}, which made the beetle worry.",
        ),
        QAItem(
            question=f"Who helped {beetle.id} with the search?",
            answer=f"A {helper.type} helped by doing the small part that the beetle could not do alone.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the {task.suspense_meter} kept moving while the friends worked before the {task.risky_cycle} finished.",
        ),
        QAItem(
            question=f"How did the beetle and helper solve the problem?",
            answer=f"They used teamwork: the {helper.type} handled the tricky reaching, and {beetle.id} kept watch until they found {task.missing}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "beetle": [
        QAItem(
            question="What is a beetle?",
            answer="A beetle is a small insect with a hard shell that helps protect its body.",
        )
    ],
    "laundromat": [
        QAItem(
            question="What is a laundromat?",
            answer="A laundromat is a place where people wash and dry clothes in big machines.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other do a job together.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next and hoping things turn out well.",
        )
    ],
    "fable": [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often with animal characters.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for group in ["beetle", "laundromat", "teamwork", "suspense", "fable"] for qa in WORLD_KNOWLEDGE[group]]


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
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(task="button", helper="mouse", name="Bramble"),
    StoryParams(task="coin", helper="sparrow", name="Milo"),
    StoryParams(task="sock", helper="mouse", name="Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A beetle fable set in a laundromat, with teamwork and suspense."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=["mouse", "sparrow"])
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
    if getattr(args, "task", None) and getattr(args, "helper", None):
        if (getattr(args, "task", None), getattr(args, "helper", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    task_id, helper = rng.choice(valid_combos())
    if getattr(args, "task", None):
        task_id = getattr(args, "task", None)
    if getattr(args, "helper", None):
        helper = getattr(args, "helper", None)
    if (task_id, helper) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(BEETLE_NAMES)
    return StoryParams(task=task_id, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params.task, params.helper, params.name)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        import sys as _sys

        _sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible task/helper pairs:\n")
        for task, helper in combos:
            print(f"  {task:7} {helper}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
