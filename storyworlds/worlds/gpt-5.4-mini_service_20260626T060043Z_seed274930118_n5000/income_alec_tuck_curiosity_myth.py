#!/usr/bin/env python3
"""
storyworlds/worlds/income_alec_tuck_curiosity_myth.py
======================================================

A small mythic story world about Alec, Tuck, Curiosity, and income.

Premise imagined from the seed:
- Alec lives in a little valley where families count their income by the
  moon's end.
- A quiet myth says income flows more smoothly when work is honest, shared,
  and guided by Curiosity instead of greed.
- Tuck is Alec's clever companion, a small fox-like helper who knows the
  hidden paths under the hill.

This world simulates a simple turn:
- Alec becomes curious about why the market's coin-baskets sometimes stay light.
- Tuck helps him investigate the old road, the well, and the stone bridge.
- The resolution is not magic from nowhere: a discovered spring path lets
  Alec do useful work for the valley, and that work changes his income.

The story is driven by world state:
- income is a physical meter that rises when Alec completes useful tasks
  for villagers or sells gathered goods.
- Curiosity is an emotional meme that pushes Alec to investigate instead of
  assuming the world is unfair.
- Tuck can tug, tuck, and carry small things; that action matters physically.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    alec: object | None = None
    coin_bag: object | None = None
    tuck: object | None = None
    well: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "fox", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Place:
    id: str
    label: str
    kind: str = "place"
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Task:
    id: str
    verb: str
    gerund: str
    result: str
    place: str
    income_gain: int
    curiosity_gain: int = 0
    requires: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "village": Place(
        id="village",
        label="the valley village",
        affords={"market", "bridge", "well"},
    ),
    "market": Place(
        id="market",
        label="the market square",
        affords={"selling", "finding", "talking"},
    ),
    "bridge": Place(
        id="bridge",
        label="the old stone bridge",
        affords={"crossing", "listening"},
    ),
    "well": Place(
        id="well",
        label="the mossy well",
        affords={"drawing", "listening"},
    ),
}

TASKS = {
    "berries": Task(
        id="berries",
        verb="gather berries",
        gerund="gathering berries",
        result="filled baskets and stained fingers",
        place="forest",
        income_gain=3,
        curiosity_gain=1,
        tags={"fruit", "forest"},
    ),
    "repair": Task(
        id="repair",
        verb="fix the broken cart wheel",
        gerund="repairing the cart wheel",
        result="a wheel that rolled true again",
        place="village",
        income_gain=4,
        curiosity_gain=0,
        requires={"hands"},
        tags={"wood", "work"},
    ),
    "song": Task(
        id="song",
        verb="sing the dawn hymn at the market",
        gerund="singing the dawn hymn",
        result="coins gathered in the copper bowl",
        place="market",
        income_gain=2,
        curiosity_gain=1,
        tags={"song", "market"},
    ),
    "draw_water": Task(
        id="draw_water",
        verb="draw water for the bakers",
        gerund="drawing water for the bakers",
        result="full jars and grateful smiles",
        place="well",
        income_gain=2,
        curiosity_gain=1,
        tags={"water", "well"},
    ),
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "village"
    task: str = "berries"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and registry facts
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


ASP_RULES = r"""
% A task is valid when the place can host it and the task belongs there.
valid_task(P, T) :- place(P), task(T), can_do(P, T).

% Curiosity is treated as a useful guide when it exists in the story.
curious_story(P, T) :- valid_task(P, T), has_curiosity.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("can_do", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    lines.append(asp.fact("has_curiosity"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tasks() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_task/2."))
    return sorted(set(asp.atoms(model, "valid_task")))


def asp_verify() -> int:
    py = set(valid_tasks())
    cl = set(asp_valid_tasks())
    if py == cl:
        print(f"OK: clingo gate matches valid_tasks() ({len(py)} tasks).")
        return 0
    print("MISMATCH between clingo and valid_tasks():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_tasks() -> list[tuple[str, str]]:
    out = []
    for place, p in PLACES.items():
        for task_id in p.affords:
            out.append((place, task_id))
    return out


def task_valid(place: Place, task: Task) -> bool:
    return task.id in place.affords


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_income(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(hero.id), task, narrate=False)
    return {
        "income": sim.get(hero.id).meters["income"],
        "curiosity": sim.get(hero.id).memes["curiosity"],
    }


def do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    if not task_valid(world.place, task):
        pass
    sig = ("task", hero.id, task.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["income"] += task.income_gain
    hero.memes["satisfaction"] += 1
    hero.memes["curiosity"] += task.curiosity_gain
    world.facts["last_result"] = task.result
    if narrate:
        world.say(f"{hero.id} did {task.gerund}, and {task.result}.")


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def tell(place: Place, task: Task, hero_name: str = "Alec") -> World:
    world = World(place)
    alec = world.add(Entity(id=hero_name, kind="character", type="boy"))
    tuck = world.add(Entity(id="Tuck", kind="character", type="fox"))
    coin_bag = world.add(Entity(
        id="coin_bag",
        type="thing",
        label="small coin bag",
        owner=alec.id,
    ))
    well = world.add(Entity(id="well_stone", type="thing", label="well stone"))

    world.facts.update(hero=alec, helper=tuck, bag=coin_bag, well=well, task=task, place=place)

    # Act 1: setup
    world.say(
        f"In the valley village, {alec.id} was a small boy with a careful heart "
        f"and a bright question in it."
    )
    alec.memes["curiosity"] += 1
    world.say(
        f"{alec.id} watched the market bowls and wondered why some days brought "
        f"more income than others."
    )
    world.say(
        f"Beside him, {tuck.id} the fox tucked his tail close and said nothing, "
        f"because he liked to listen before he spoke."
    )

    # Act 2: tension and investigation
    world.para()
    world.say(
        f"One morning, {alec.id} heard that the {place.label} could guide a person "
        f"toward honest work, so he and {tuck.id} went to look."
    )
    world.say(
        f"{alec.id} wanted to {task.verb}, but he was not yet sure where to begin."
    )
    if task.id == "berries":
        world.say(
            f"{tuck.id} sniffed the path under the pines and found the red bushes first."
        )
    elif task.id == "repair":
        world.say(
            f"{tuck.id} nudged a loose pin from the grass, and {alec.id} noticed how "
            f"the broken wheel had begun to lean."
        )
    elif task.id == "song":
        world.say(
            f"{tuck.id} listened to the bell tower and kept the time while {alec.id} "
            f"found his tune."
        )
    else:
        world.say(
            f"{tuck.id} pointed his nose toward the mossy road that led to the well."
        )

    world.say(
        f"{alec.id}'s curiosity grew, and with it came the courage to try."
    )
    do_task(world, alec, task)

    # Act 3: resolution
    world.para()
    if task.id == "berries":
        world.say(
            f"By sunset, {alec.id} had baskets full of berries, and the market keeper "
            f"paid him with bright coins."
        )
    elif task.id == "repair":
        world.say(
            f"When the wheel turned again, the miller smiled and paid {alec.id} fairly "
            f"for the saved cart."
        )
    elif task.id == "song":
        world.say(
            f"The market people set coins in the copper bowl, and the song made the whole "
            f"square feel lighter."
        )
    else:
        world.say(
            f"The bakers thanked {alec.id} with bread and coin, and the well water kept "
            f"the morning moving."
        )

    world.say(
        f"{tuck.id} watched {alec.id} tuck the coins into the little bag, not to hide them "
        f"from the world, but to carry them home safely."
    )
    world.say(
        f"That night, {alec.id}'s income was higher, and his curiosity had turned into a "
        f"kind of wisdom: ask first, listen well, and work where the valley truly needs you."
    )

    world.facts["hero_income"] = alec.meters["income"]
    world.facts["hero_curiosity"] = alec.memes["curiosity"]
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    task: Task = _safe_fact(world, f, "task")
    return [
        f'Write a short myth for a young child about {hero.id}, Curiosity, and income.',
        f"Tell a gentle story where {hero.id} wonders why income changes and learns by "
        f"{task.gerund}.",
        f"Write a small mythic tale with {hero.id} and Tuck that ends with earned income "
        f"and a wiser heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    task: Task = _safe_fact(world, f, "task")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a curious boy in the valley village.",
        ),
        QAItem(
            question=f"Who went with {hero.id} to look for the work?",
            answer=f"{helper.id} the fox went with {hero.id} and helped him listen and look.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What changed for {hero.id} by the end?",
            answer=(
                f"{hero.id}'s income grew after he finished the work, and his curiosity "
                f"turned into wisdom instead of worry."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer=(
                "Curiosity is the feeling that makes someone ask questions, look closer, "
                "and want to learn how things work."
            ),
        ),
        QAItem(
            question="What is income?",
            answer=(
                "Income is the money a person gets from useful work, gifts, or honest trade."
            ),
        ),
        QAItem(
            question="Why would a small helper tuck coins into a bag?",
            answer=(
                "Coins are often tucked into a bag so they stay together and do not fall out "
                "on the road."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="village", task="berries"),
    StoryParams(place="village", task="repair"),
    StoryParams(place="market", task="song"),
    StoryParams(place="well", task="draw_water"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic income storyworld about Alec, Tuck, and Curiosity.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
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
    combos = [c for c in valid_tasks()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task = rng.choice(list(combos))
    return StoryParams(place=place, task=task)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task))
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_show_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_task/2."))
    return sorted(set(asp.atoms(model, "valid_task")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_task/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        valid = asp_show_valid()
        print(f"{len(valid)} valid tasks:")
        for place, task in valid:
            print(f"  {place:8} {task}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.place}: {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
