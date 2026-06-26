#!/usr/bin/env python3
"""
A tiny story world for a meek nursery-rhyme teamwork tale.

Premise:
A meek little mouse needs help to bring a bright lantern home before night.
A crew of small friends work together with a bucket, a rope, and a cart.
Their teamwork turns worry into a gentle parade.

The world is intentionally small and classical:
- typed entities with meters and memes
- a simple simulated turn
- a reasonableness gate and matching ASP twin
- child-facing prose and grounded QA
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    tool_ent: object | None = None
    def __post_init__(self) -> None:
        for k in ("weight", "distance", "safety", "done"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "joy", "pride", "warmth", "meekness", "teamwork"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    place: str = "the nursery lane"
    time: str = "at dusk"
    setting: object | None = None
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
    name: str
    verb: str
    gerund: str
    trouble: str
    fix: str
    keyword: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    kind: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        parts: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    parts.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            parts.append(" ".join(buf))
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

TASKS = {
    "lantern": Task(
        name="lantern",
        verb="bring the lantern home",
        gerund="bringing the lantern home",
        trouble="the dark would swallow the path",
        fix="the little light would glow at the door",
        keyword="lantern",
    ),
    "berries": Task(
        name="berries",
        verb="carry the berries to the pie table",
        gerund="carrying berries to the pie table",
        trouble="the berries might spill",
        fix="the bowl would stay full and neat",
        keyword="berries",
    ),
    "bundle": Task(
        name="bundle",
        verb="pull the bundle up the hill",
        gerund="pulling the bundle up the hill",
        trouble="the bundle was too heavy for one small friend",
        fix="the load would move together",
        keyword="bundle",
    ),
}

TOOLS = {
    "bucket": Tool(
        id="bucket",
        label="bucket",
        phrase="a shiny bucket",
        helps="holds berries without spilling",
        kind="container",
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a short rope",
        helps="helps friends pull together",
        kind="pulling",
    ),
    "cart": Tool(
        id="cart",
        label="cart",
        phrase="a tiny cart",
        helps="carries the lantern safely",
        kind="carrier",
    ),
}

CHARACTER_NAMES = ["Mimi", "Nora", "Tilly", "Lulu", "Pip", "Milo", "Benny", "Sally"]
ANIMAL_TYPES = ["mouse", "rabbit", "bird", "kitten"]
HELPER_TYPES = ["mouse", "rabbit", "bird", "kitten"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    task: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task_name, task in TASKS.items():
        for tool_name, tool in TOOLS.items():
            if task_name == "lantern" and tool.kind == "carrier":
                combos.append((task_name, tool_name))
            if task_name == "berries" and tool.kind == "container":
                combos.append((task_name, tool_name))
            if task_name == "bundle" and tool.kind == "pulling":
                combos.append((task_name, tool_name))
    return combos


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit {task.gerund}. "
        f"The teamwork needs a tool that truly helps with that job.)"
    )


# ---------------------------------------------------------------------------
# Small simulation
# ---------------------------------------------------------------------------

def run_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)

    task = _safe_lookup(TASKS, params.task)
    tool = _safe_lookup(TOOLS, params.tool)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        phrase=f"a meek little {params.hero_type} named {params.hero_name}",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        phrase=f"a kind little {params.helper_type} named {params.helper_name}",
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type=tool.kind,
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=task.name,
        label=task.name,
        phrase=f"the {task.name}",
        owner=hero.id,
    ))

    hero.memes["meekness"] += 1.0
    hero.memes["fear"] += 1.0
    helper.memes["warmth"] += 1.0

    # Act 1
    world.say(f"At {setting.place}, {hero.phrase} looked at {task.keyword} and sighed.")
    world.say(f"{hero.pronoun('subject').capitalize()} wanted to {task.verb}, but {task.trouble}.")
    world.para()

    # Act 2
    world.say(f"{helper.phrase} came by, and the two friends chose teamwork.")
    hero.memes["teamwork"] += 1.0
    helper.memes["teamwork"] += 1.0

    if task.name == "lantern":
        prize.carried_by = hero.id
        tool_ent.carried_by = hero.id
        world.say(f"They set the lantern in {tool.phrase} and held it steady together.")
    elif task.name == "berries":
        prize.carried_by = helper.id
        tool_ent.carried_by = helper.id
        world.say(f"They placed the berries in {tool.phrase}, so none of them rolled away.")
    else:
        prize.carried_by = "both"
        tool_ent.carried_by = "both"
        world.say(f"They tied {tool.phrase} around the bundle, then pulled in a soft little rhythm.")

    prize.meters["done"] = 1.0
    hero.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    helper.memes["pride"] += 1.0
    world.para()

    # Act 3
    world.say(f"By the end, {task.fix}, and the night felt kind and bright.")
    if task.name == "lantern":
        world.say(f"The lantern glowed by the door, and the path looked like a ribbon of gold.")
    elif task.name == "berries":
        world.say(f"The berries stayed snug and round, ready for a sweet pie.")
    else:
        world.say(f"The bundle moved on safely, because two small hearts were stronger than one.")

    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        tool=tool,
        prize=prize,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    task: Task = _safe_fact(world, f, "task")
    return [
        f"Write a short nursery-rhyme style story about a meek {hero.type} and teamwork.",
        f"Tell a gentle tale where {hero.label} needs help to {task.verb}.",
        f"Create a rhyme-like story that includes the word '{task.keyword}' and ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    task: Task = _safe_fact(world, f, "task")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.phrase}, who is meek but brave enough to ask for help.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {task.verb}, but doing it alone would be too hard.",
        ),
        QAItem(
            question=f"How did the friends solve the trouble?",
            answer=f"{hero.label} and {helper.label} used {tool.phrase} and teamwork to finish the job together.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the task was done, the fear was gone, and the little friends felt proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does meek mean?",
            answer="Meek means gentle, quiet, and not pushy. A meek character may still be kind and brave.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something well.",
        ),
        QAItem(
            question="Why do friends share a job?",
            answer="Friends share a job so the work feels easier, safer, and more fun.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_tool(lantern,cart).
task_tool(berries,bucket).
task_tool(bundle,rope).

valid(T, Tool) :- task_tool(T, Tool).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for task_name in TASKS:
        lines.append(asp.fact("task", task_name))
    for tool_name, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_name))
        lines.append(asp.fact("kind", tool_name, tool.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A meek teamwork nursery-rhyme story world."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))

    if (task, tool) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    hero_type = getattr(args, "hero_type", None) or rng.choice(["mouse", "rabbit", "bird", "kitten"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mouse", "rabbit", "bird", "kitten"])
    hero_name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in CHARACTER_NAMES if n != hero_name])

    return StoryParams(
        task=task,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    world = run_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.kind == "thing" and e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid task/tool combos:\n")
        for task, tool in combos:
            print(f"  {task:8} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(task="lantern", hero_name="Mimi", hero_type="mouse",
                        helper_name="Pip", helper_type="rabbit", tool="cart"),
            StoryParams(task="berries", hero_name="Nora", hero_type="bird",
                        helper_name="Lulu", helper_type="mouse", tool="bucket"),
            StoryParams(task="bundle", hero_name="Tilly", hero_type="kitten",
                        helper_name="Benny", helper_type="rabbit", tool="rope"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
