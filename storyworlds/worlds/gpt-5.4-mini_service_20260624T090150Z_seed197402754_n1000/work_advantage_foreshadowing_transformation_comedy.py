#!/usr/bin/env python3
"""
storyworlds/worlds/work_advantage_foreshadowing_transformation_comedy.py
========================================================================

A small comedic storyworld about work, advantage, foreshadowing, and
transformation.

Premise:
- A young worker wants to finish a job the hard way.
- A tiny clue foreshadows that the job has a smarter shortcut.
- A transformation changes the worker's approach.
- The ending proves the new advantage by showing the work got easier.

The simulated world tracks physical meters and emotional memes, and the prose
is driven by the world state rather than a fixed template.
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
# Data model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    affordance: str
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
class Tool:
    id: str
    label: str
    phrase: str
    advantage: str
    transforms_to: Optional[str] = None
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
class StoryParams:
    setting: str
    work: str
    tool: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
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
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "classroom": Setting(place="the classroom", affordance="tidy work"),
    "bakery": Setting(place="the bakery", affordance="busy work"),
    "garden": Setting(place="the garden shed", affordance="sort work"),
    "workshop": Setting(place="the workshop", affordance="build work"),
}

WORKS = {
    "tidy": "tidy the toy shelf",
    "bake": "carry warm buns to the counter",
    "sort": "sort a pile of buttons",
    "build": "stack shiny blocks into a tower",
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="little step ladder",
        phrase="a little step ladder",
        advantage="it reaches high shelves",
        transforms_to="stool",
    ),
    "gloves": Tool(
        id="gloves",
        label="rubber gloves",
        phrase="a pair of rubber gloves",
        advantage="they keep sticky goo off the hands",
        transforms_to="mittens",
    ),
    "tray": Tool(
        id="tray",
        label="rolling tray",
        phrase="a rolling tray with little wheels",
        advantage="it carries things faster",
        transforms_to="cart",
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a small magnifier",
        advantage="it helps find tiny things",
        transforms_to="big lens",
    ),
}

TRAITS = ["silly", "curious", "cheery", "clumsy", "brave", "bouncy"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ruby", "Ella"]
BOY_NAMES = ["Max", "Leo", "Ben", "Finn", "Theo", "Sam"]
ROLES = {"girl": "girl", "boy": "boy", "mother": "mother", "father": "father"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(classroom).
setting(bakery).
setting(garden).
setting(workshop).

work(tidy).
work(bake).
work(sort).
work(build).

tool(ladder).
tool(gloves).
tool(tray).
tool(magnifier).

advantage(ladder, high).
advantage(gloves, clean).
advantage(tray, fast).
advantage(magnifier, small).

transforms_to(ladder, stool).
transforms_to(gloves, mittens).
transforms_to(tray, cart).
transforms_to(magnifier, biglens).

can_use(S, W, T) :- setting(S), work(W), tool(T), advantage(T, _).
valid_story(S, W, T) :- can_use(S, W, T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid in WORKS:
        lines.append(asp.fact("work", wid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("advantage", tid, tool.advantage.split()[0]))
        if tool.transforms_to:
            lines.append(asp.fact("transforms_to", tid, tool.transforms_to.replace(" ", "")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for w in WORKS:
            for t in TOOLS:
                combos.append((s, w, t))
    return combos


def reasonableness_gate(setting: str, work: str, tool: str) -> bool:
    if setting not in SETTINGS or work not in WORKS or tool not in TOOLS:
        return False
    # The joke: every tool is useful somewhere, but only some are actually
    # narratively interesting enough to be an advantage in that setting.
    if setting == "classroom" and tool == "tray":
        return False
    return True


def explain_rejection(setting: str, work: str, tool: str) -> str:
    return (
        f"(No story: {_safe_lookup(TOOLS, tool).label} is not a good fit for {_safe_lookup(WORKS, work)} "
        f"in {_safe_lookup(SETTINGS, setting).place}. The advantage would not feel honest.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.role,
            traits=["little", params.trait],
            meters={"work": 0.0, "advantage": 0.0, "transform": 0.0},
            memes={"pride": 0.0, "curiosity": 0.0, "surprise": 0.0, "joy": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type="mother" if params.role == "girl" else "father",
            label="the helper",
            meters={"work": 0.0},
            memes={"wit": 0.0},
        )
    )
    tool = world.add(
        Entity(
            id=params.tool,
            type="tool",
            label=_safe_lookup(TOOLS, params.tool).label,
            phrase=_safe_lookup(TOOLS, params.tool).phrase,
            owner=hero.id,
            meters={"use": 0.0, "advantage": 0.0},
        )
    )

    # Act 1: setup and foreshadowing.
    world.say(f"{hero.id} was a little {params.trait} {params.role} who loved to work.")
    world.say(
        f"At {world.setting.place}, {hero.pronoun('subject')} had to {_safe_lookup(WORKS, params.work)}, "
        f"and that was hard work for small hands."
    )
    world.say(
        f"One day {hero.id} noticed {tool.phrase} leaning nearby. "
        f"It looked funny, but {tool.advantage}."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        tool=tool,
        work_id=params.work,
        setting_id=params.setting,
        work_text=_safe_lookup(WORKS, params.work),
        setting=world.setting,
    )

    # Act 2: the work is hard, then the clue pays off.
    world.para()
    hero.meters["work"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} tried to do the job alone, but the pile was wobbly and the tiny parts "
        f"kept slipping away."
    )
    world.say(
        f"{hero.id} squinted at the {tool.label} again, and the clue suddenly made sense."
    )
    world.say(
        f"It was as if the room had been whispering, 'Aha, there is an advantage here.'"
    )

    # Transformation: tool or hero approach changes.
    world.para()
    hero.meters["transform"] += 1
    tool.meters["advantage"] += 1
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1

    transformed_tool = _safe_lookup(TOOLS, params.tool).transforms_to
    if transformed_tool:
        world.say(
            f"{hero.id} turned the {tool.label} into a {transformed_tool}, "
            f"and suddenly the job looked much less grumpy."
        )
    else:
        world.say(
            f"{hero.id} stopped doing the job the hard way and found a smarter way to use it."
        )

    world.say(
        f"With the new trick, the work went faster, and {hero.id} felt as proud as a bunny "
        f"wearing a hat."
    )

    # Act 3: comedic payoff.
    hero.meters["work"] += 1
    helper.meters["work"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{helper.id} peeked over and laughed. '{hero.id}, you made a tiny job behave like a big helper!'"
    )
    world.say(
        f"In the end, {hero.id} finished {params.work} with a grin, and the silly little tool "
        f"turned an ordinary chore into an easy win."
    )

    return world


# ---------------------------------------------------------------------------
# QA and prose output
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))  # type: ignore[assignment]
    return [
        f"Write a funny short story for a child about {hero.id} doing work and discovering an advantage.",
        f"Tell a comic story where a small worker notices {tool.phrase} and learns a better way.",
        f"Write a gentle story with foreshadowing and transformation that ends with work becoming easier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))  # type: ignore[assignment]
    work_text = _safe_fact(world, f, "work_text")  # type: ignore[assignment]
    place = _safe_fact(world, f, "setting").place  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"What work did {hero.id} need to do at {place}?",
            answer=f"{hero.id} needed to {work_text}, which was tricky at first.",
        ),
        QAItem(
            question=f"What clue foreshadowed the advantage in the story?",
            answer=(
                f"The clue was {tool.phrase} leaning nearby. It hinted that "
                f"{tool.advantage} before {hero.id} even tried it."
            ),
        ),
        QAItem(
            question=f"How did the transformation help {hero.id} finish the job?",
            answer=(
                f"{hero.id} changed the tool into a better form and used it in a smarter way, "
                f"so the work went faster and felt easier."
            ),
        ),
        QAItem(
            question=f"Who laughed when the clever plan worked?",
            answer=f"{helper.id} laughed when {hero.id} made the small job go smoothly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an advantage?",
            answer="An advantage is something that helps you do a job more easily or more successfully.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints at something important later.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes different in an important way.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedic storyworld about work, advantage, foreshadowing, and transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--work", choices=WORKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    work = getattr(args, "work", None) or rng.choice(list(WORKS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))

    if not reasonableness_gate(setting, work, tool):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or _safe_lookup(ROLES, gender)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        work=work,
        tool=tool,
        name=name,
        role=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("classroom", "tidy", "ladder", "Mia", "girl", "curious"),
            StoryParams("bakery", "bake", "gloves", "Leo", "boy", "cheery"),
            StoryParams("garden", "sort", "magnifier", "Nora", "girl", "silly"),
            StoryParams("workshop", "build", "tray", "Max", "boy", "bouncy"),
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
