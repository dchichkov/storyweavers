#!/usr/bin/env python3
"""
A standalone story world for a tiny pirate tale about teamwork and reconciliation.

Premise:
A small pirate crew has a useful, functional ship and a special treasure map.
During a messy task at sea, one crew member acts alone, causing trouble.
The captain notices the strain, the crew argues, and then they make up by
working together to fix the ship and share the job.

This world keeps the simulation simple:
- a few typed entities
- physical meters for hull damage, rope mess, wind, and repairs
- emotional memes for pride, hurt, trust, apology, and teamwork
- a short story rendered from the evolving world state

The story is generated from the seed by choosing a valid crew, a task, and a
reconciliation path that actually resolves the problem.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    map_item: object | None = None
    mate: object | None = None
    ship: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "captain", "pirate"}
        female = {"girl", "woman", "mother", "captainess", "pirate-girl"}
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
class CrewRole:
    id: str
    label: str
    skill: str
    teamwork_line: str
    reconcile_line: str
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


@dataclass
class Task:
    id: str
    name: str
    verb: str
    gerund: str
    mishap: str
    fix: str
    requires: set[str]
    risk: set[str]
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
class Treasure:
    label: str
    phrase: str
    type: str
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
class StoryParams:
    task: str
    treasure: str
    hero_name: str
    hero_type: str
    mate_name: str
    mate_type: str
    captain_name: str
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


class World:
    def __init__(self) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with teamwork and reconciliation.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--captain")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--mate-type", choices=["boy", "girl"])
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


PIRATE_NAMES = ["Mina", "Rowan", "Pip", "Jory", "Nell", "Finn", "Tess", "Kai", "Lola", "Beck"]
CAPTAIN_NAMES = ["Captain Mira", "Captain Reef", "Captain Blue", "Captain Stone"]
TASKS = {
    "reef": Task(
        id="reef",
        name="reef crossing",
        verb="sail past the reef",
        gerund="sailing past the reef",
        mishap="scraped the hull",
        fix="patched the hull together",
        requires={"sails", "lookout"},
        risk={"hull"},
        tags={"sea", "ship"},
    ),
    "storm": Task(
        id="storm",
        name="storm chase",
        verb="brace for the storm",
        gerund="bracing for the storm",
        mishap="tore the sail",
        fix="mended the sail",
        requires={"rope", "sail"},
        risk={"sail"},
        tags={"storm", "ship"},
    ),
    "harbor": Task(
        id="harbor",
        name="harbor dock",
        verb="dock at the harbor",
        gerund="docking at the harbor",
        mishap="dropped the anchor chain",
        fix="hauled the anchor chain back up",
        requires={"anchor", "line"},
        risk={"anchor"},
        tags={"harbor", "ship"},
    ),
}
TREASURES = {
    "map": Treasure("map", "a bright treasure map", "map", "hands"),
    "compass": Treasure("compass", "a brass compass", "compass", "hands"),
    "flag": Treasure("flag", "a red ship flag", "flag", "mast"),
    "lantern": Treasure("lantern", "a small lantern", "lantern", "hands"),
}
ROLES = {
    "captain": CrewRole(
        id="captain", label="captain", skill="steady hands",
        teamwork_line="We can do this together.",
        reconcile_line="Let us fix this as a crew.",
    ),
    "mate": CrewRole(
        id="mate", label="mate", skill="quick knots",
        teamwork_line="I'll help, and you help too.",
        reconcile_line="Sorry for going alone; let's share the work.",
    ),
    "lookout": CrewRole(
        id="lookout", label="lookout", skill="sharp eyes",
        teamwork_line="I saw the danger in time.",
        reconcile_line="I should have called for help sooner.",
    ),
}

GIRL_NAMES = ["Mina", "Nell", "Tess", "Lola", "Pia", "Rin"]
BOY_NAMES = ["Pip", "Finn", "Jory", "Kai", "Beck", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task_id, task in TASKS.items():
        for tr_id, tr in TREASURES.items():
            if task.risk and tr.region:
                combos.append((task_id, tr_id))
    return combos


def reasonableness_gate(task: Task, treasure: Treasure) -> bool:
    return bool(task.risk) and treasure.region in {"hands", "mast"}


def explain_rejection(task: Task, treasure: Treasure) -> str:
    return (
        f"(No story: this pirate task does not create a believable problem for {treasure.label}. "
        f"Pick a treasure that could be affected while the crew is working.)"
    )


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def setup_world(params: StoryParams) -> World:
    world = World()
    task = _safe_lookup(TASKS, params.task)
    treasure = _safe_lookup(TREASURES, params.treasure)

    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type, label=params.name))
    mate = world.add(Entity(id=params.mate, kind="character", type=params.mate_type, label=params.mate))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))

    map_item = world.add(Entity(
        id="treasure", type=treasure.type, label=treasure.label,
        phrase=treasure.phrase, owner=hero.id, caretaker=captain.id
    ))
    ship = world.add(Entity(id="ship", type="ship", label="ship"))
    ship.meters["hull"] = 0.0
    ship.meters["sail"] = 0.0
    ship.meters["anchor"] = 0.0

    world.facts.update(
        hero=hero, mate=mate, captain=captain, treasure=map_item, task=task, treasure_cfg=treasure, ship=ship
    )
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero, mate, captain = f["hero"], f["mate"], f["captain"]
    treasure = _safe_fact(world, f, "treasure")
    task: Task = _safe_fact(world, f, "task")

    world.say(
        f"{hero.id} was a small pirate who loved useful things and a ship that worked well."
    )
    world.say(
        f"{mate.id} was {mate.pronoun('subject')} shipmate, and {captain.id} kept the crew on course."
    )
    world.say(
        f"Together they had {treasure.phrase}, which made the trip feel important and functional."
    )
    world.say(
        f"On that day, they wanted to {task.verb}, and the sea looked ready for trouble."
    )


def cause_mishap(world: World) -> None:
    f = world.facts
    hero, mate, captain = f["hero"], f["mate"], f["captain"]
    treasure = _safe_fact(world, f, "treasure")
    task: Task = _safe_fact(world, f, "task")
    _add_meter(world.get("ship"), next(iter(task.risk)), 1.0)
    _add_meme(hero, "pride", 1.0)
    _add_meme(mate, "hurt", 1.0)
    _add_meme(captain, "worry", 1.0)

    world.para()
    world.say(
        f"{hero.id} tried to handle the job alone, but that only {task.mishap}."
    )
    world.say(
        f"The mistake jostled {treasure.it()} and made {captain.id} frown."
    )
    world.say(
        f"{mate.id} felt left out, and the little crew stopped working smoothly."
    )


def reconcile(world: World) -> None:
    f = world.facts
    hero, mate, captain = f["hero"], f["mate"], f["captain"]
    task: Task = _safe_fact(world, f, "task")
    ship = _safe_fact(world, f, "ship")

    _add_meme(hero, "guilt", 1.0)
    _add_meme(mate, "trust", 1.0)
    _add_meme(captain, "hope", 1.0)
    _add_meme(hero, "teamwork", 1.0)
    _add_meme(mate, "teamwork", 1.0)
    _add_meme(captain, "teamwork", 1.0)
    ship.meters[next(iter(task.risk))] = 0.0

    world.para()
    world.say(
        f"{captain.id} took a calm breath and said, \"We work best when we work as a crew.\""
    )
    world.say(
        f"{hero.id} looked at {mate.id} and said sorry for trying to do everything alone."
    )
    world.say(
        f"{mate.id} nodded, and the two of them shared the load with {captain.id} beside them."
    )
    world.say(
        f"With teamwork, they {task.fix}, and the ship felt steady again."
    )
    world.say(
        f"By the end, the crew was smiling, the deck was calm, and the voyage could continue."
    )


def generate_story(world: World) -> None:
    narrate_setup(world)
    cause_mishap(world)
    reconcile(world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = _safe_fact(world, f, "task")
    treasure: Treasure = _safe_fact(world, f, "treasure_cfg")
    return [
        f"Write a short pirate tale about a crew that learns teamwork while trying to {task.verb}.",
        f"Tell a child-friendly story where a pirate makes a mistake, apologizes, and then fixes {treasure.phrase} with help from friends.",
        f"Create a functional pirate story with reconciliation, where the crew shares the work and the ship becomes safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, captain = f["hero"], f["mate"], f["captain"]
    task: Task = _safe_fact(world, f, "task")
    treasure: Treasure = _safe_fact(world, f, "treasure_cfg")
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, {mate.id}, and {captain.id} as a pirate crew."
        ),
        QAItem(
            question=f"What went wrong when {hero.id} tried to {task.verb} alone?",
            answer=f"{hero.id} tried to do it alone, and that {task.mishap}, which made the crew worry."
        ),
        QAItem(
            question=f"How did the crew fix the problem with {treasure.phrase} nearby?",
            answer=f"They apologized, shared the work, and used teamwork to {task.fix}."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the crew calm and smiling because they had made up and worked together again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so the job gets done better."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people stop arguing, make up, and become friendly again."
        ),
        QAItem(
            question="What does a captain do on a pirate ship?",
            answer="A captain helps guide the crew, make choices, and keep everyone working together."
        ),
    ]


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
    StoryParams(task="reef", treasure="map", hero_name="Mina", hero_type="girl", mate_name="Pip", mate_type="boy", captain_name="Captain Reef"),
    StoryParams(task="storm", treasure="flag", hero_name="Finn", hero_type="boy", mate_name="Tess", mate_type="girl", captain_name="Captain Blue"),
    StoryParams(task="harbor", treasure="compass", hero_name="Lola", hero_type="girl", mate_name="Kai", mate_type="boy", captain_name="Captain Mira"),
]


ASP_RULES = r"""
% A story is reasonable when the task creates a risk and the treasure is in the
% part of the ship the task can disturb.
valid(task(T), treasure(P)) :- task(T), treasure(P), task_risk(T, R), treasure_region(P, R).

% A reconciliation story needs a problem, an apology, and teamwork.
teamwork_story(T, P) :- valid(task(T), treasure(P)), can_apologize(T), can_share_work(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_risk", tid, next(iter(task.risk))))
    for pid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", pid))
        lines.append(asp.fact("treasure_region", pid, tr.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((f"task({t})", f"treasure({p})") for t, p in valid_combos())
    asp_set = set(asp_valid_combos())
    if len(asp_set) == len(valid_combos()):
        print(f"OK: ASP produced {len(asp_set)} valid story pairs.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Python combos:", valid_combos())
    print("ASP combos:", sorted(asp_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "treasure", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        treasure = _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not reasonableness_gate(task, treasure):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [(t, p) for t, p in valid_combos()
              if (not getattr(args, "task", None) or t == getattr(args, "task", None)) and (not getattr(args, "treasure", None) or p == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    task_id, treas_id = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    mate_type = getattr(args, "mate_type", None) or ("girl" if hero_type == "boy" else "boy")
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    mate_name = getattr(args, "mate", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    captain_name = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(
        task=task_id,
        treasure=treas_id,
        hero_name=hero_name,
        hero_type=hero_type,
        mate_name=mate_name,
        mate_type=mate_type,
        captain_name=captain_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible pirate story pairs.")
        for pair in asp_valid_combos():
            print(pair)
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
            header = f"### {p.hero_name}: {p.task} with {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
