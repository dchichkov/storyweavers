#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a patient process that transforms
simple ingredients into a sweet finished thing.

The seed tale is a short rhyme-shaped premise:
a child gathers ingredients, the mixture changes through a process, a small
problem appears, and a gentle helper turns the change into a happy finish.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    state: str = "raw"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the little kitchen"
    indoors: bool = True
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
class Process:
    id: str
    name: str
    verb: str
    gerund: str
    steps: list[str]
    input_label: str
    output_label: str
    transformed_state: str
    risk: str
    clue: str
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
    state: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Tool:
    id: str
    label: str
    allows: set[str]
    prep: str
    tail: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", indoors=True, affords={"mix", "bake", "stir"}),
    "garden": Setting(place="the sunny garden table", indoors=False, affords={"mix", "dry"}),
}

PROCESSES = {
    "cake": Process(
        id="cake",
        name="cake batter process",
        verb="make a cake",
        gerund="making a cake",
        steps=["pour", "stir", "bake"],
        input_label="batter",
        output_label="cake",
        transformed_state="golden",
        risk="burnt",
        clue="the spoon went round and round",
        tags={"process", "transformation", "cake", "bake"},
    ),
    "bread": Process(
        id="bread",
        name="bread dough process",
        verb="make bread",
        gerund="making bread",
        steps=["mix", "knead", "bake"],
        input_label="dough",
        output_label="loaf",
        transformed_state="warm",
        risk="too dry",
        clue="the dough puffed up like a cloud",
        tags={"process", "transformation", "bread", "bake"},
    ),
    "jam": Process(
        id="jam",
        name="jam-making process",
        verb="make jam",
        gerund="making jam",
        steps=["stir", "simmer", "jar"],
        input_label="fruit mash",
        output_label="jam",
        transformed_state="shiny",
        risk="sticky",
        clue="the berries turned bright and sweet",
        tags={"process", "transformation", "jam", "stir"},
    ),
}

PRIZES = {
    "flour": Prize(label="flour", phrase="a bowl of white flour", type="flour", state="raw"),
    "berries": Prize(label="berries", phrase="a basket of red berries", type="berries", state="raw", plural=True),
    "dough": Prize(label="dough", phrase="a soft lump of dough", type="dough", state="raw"),
}

TOOLS = [
    Tool(id="spoon", label="a wooden spoon", allows={"stir", "mix"}, prep="pick up a wooden spoon", tail="held the spoon all the way"),
    Tool(id="oven", label="the warm oven", allows={"bake"}, prep="open the warm oven", tail="waited while the oven did its work"),
    Tool(id="jar", label="a little jar", allows={"jar"}, prep="set out a little jar", tail="twisted the lid on tight"),
]

NAMES = ["Mia", "Lily", "Nora", "Finn", "Theo", "Ava", "Leo", "Zoe"]
PARENTS = ["mother", "father"]
TRAITS = ["tiny", "cheerful", "curious", "gentle", "bright"]


def process_at_risk(proc: Process, prize: Prize) -> bool:
    return True  # in this small world, every chosen prize begins in the process


def select_tool(proc: Process) -> Optional[Tool]:
    for tool in TOOLS:
        if any(step in tool.allows for step in proc.steps):
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, proc in PROCESSES.items():
            if pid == "jam" and place == "garden":
                pass
            for prize_id, prize in PRIZES.items():
                if process_at_risk(proc, prize) and select_tool(proc):
                    combos.append((place, pid, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    process: str
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


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.get("traits", [])), "")  # unused fallback
    _ = trait
    world.say(f"{hero.id} was a little {hero.type} with a happy heart and busy hands.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, proc: Process) -> None:
    world.say(
        f"{hero.id} loved the {proc.name}, because {proc.clue}."
    )
    world.say(
        f"One day, {hero.pronoun('possessive')} {parent.type} brought home {prize.phrase}."
    )
    prize.state = proc.input_label
    prize.owner = hero.id
    world.say(
        f"{hero.id} looked at the bowl and smiled; {prize.label} was ready for {proc.verb}."
    )


def begin_process(world: World, hero: Entity, proc: Process) -> None:
    hero.memes["eagerness"] = hero.memes.get("eagerness", 0) + 1
    world.say(
        f"Then {hero.id} began {proc.gerund}, step by step, as neat as a nursery rhyme."
    )


def process_step(world: World, hero: Entity, proc: Process, prize: Entity) -> None:
    if proc.id == "cake":
        prize.state = "mixed"
        world.say(f"First came the pour, then came the stir, and the batter turned smooth and light.")
    elif proc.id == "bread":
        prize.state = "mixed"
        world.say(f"First came the mix, then came the knead, and the dough grew soft and round.")
    elif proc.id == "jam":
        prize.state = "mixed"
        world.say(f"First came the stir, then came the simmer, and the fruit turned glossy red.")
    hero.meters["doing"] = hero.meters.get("doing", 0) + 1


def warn(world: World, parent: Entity, hero: Entity, prize: Entity, proc: Process) -> None:
    world.facts["risk"] = proc.risk
    world.say(
        f"But {hero.pronoun('possessive')} {parent.type} sniffed the air and frowned."
    )
    world.say(
        f'"Careful," {hero.pronoun("possessive")} {parent.type} said. "A little mistake could make it {proc.risk}."'
    )


def spoil(world: World, prize: Entity, proc: Process) -> None:
    prize.state = proc.risk
    prize.meters["ruined"] = prize.meters.get("ruined", 0) + 1
    world.say(f"And oh dear, the bowl began to wobble; the change looked ready to go wrong.")


def fix_with_tool(world: World, hero: Entity, parent: Entity, prize: Entity, proc: Process, tool: Tool) -> None:
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.type} fetched {tool.label} and smiled."
    )
    world.say(
        f'"Let us {proc.verb} the careful way," {hero.pronoun("possessive")} {parent.type} said.'
    )
    world.say(
        f"They {tool.prep}, and {hero.id} {tool.tail} while the little process carried on."
    )


def finish(world: World, hero: Entity, parent: Entity, prize: Entity, proc: Process) -> None:
    prize.state = proc.transformed_state
    prize.label = proc.output_label
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At last, the raw thing was not raw anymore; it had turned into {proc.output_label}."
    )
    world.say(
        f"{hero.id} clapped, {hero.pronoun('possessive')} {parent.type} laughed, and the room smelled sweet and warm."
    )


def tell(setting: Setting, proc: Process, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, state=prize_cfg.state))
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked tidy little tasks.")
    setup(world, hero, parent, prize, proc)
    world.para()
    begin_process(world, hero, proc)
    process_step(world, hero, proc, prize)
    warn(world, parent, hero, prize, proc)
    spoil(world, prize, proc)
    tool = select_tool(proc)
    if tool:
        world.para()
        fix_with_tool(world, hero, parent, prize, proc, tool)
        finish(world, hero, parent, prize, proc)
    world.facts.update(hero=hero, parent=parent, prize=prize, process=proc, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, proc, prize = f["hero"], f["process"], f["prize"]
    return [
        f'Write a short nursery-rhyme story about a child named {hero.id} and a {proc.name}.',
        f"Tell a gentle story in rhyme-leaning prose where {hero.id} tries to {proc.verb} with {prize.phrase}.",
        f'Write a tiny story about a process and transformation, using the word "process" and ending in a warm result.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, proc = f["hero"], f["parent"], f["prize"], f["process"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do with {prize.label}?",
            answer=f"{hero.id} was trying to {proc.verb}, and the little process changed {prize.label} step by step.",
        ),
        QAItem(
            question=f"Why did {parent.type} worry during the process?",
            answer=f"{parent.type.capitalize()} worried because the change could make it {proc.risk}.",
        ),
        QAItem(
            question=f"What did {hero.id} end up with at the end?",
            answer=f"In the end, the raw ingredients became {proc.output_label}, and the little room felt bright and done.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    proc = _safe_fact(world, f, "process")
    out = [
        QAItem(
            question="What is a process?",
            answer="A process is a set of steps that changes one thing into another thing.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form, like batter becoming cake.",
        ),
        QAItem(
            question=f"Why is stirring useful in {proc.name}?",
            answer="Stirring helps the pieces mix together smoothly so the process can keep going well.",
        ),
    ]
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.state:
            bits.append(f"state={e.state}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", process="cake", prize="flour", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="kitchen", process="bread", prize="dough", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="garden", process="jam", prize="berries", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


KNOWLEDGE_ORDER = ["process", "transformation", "cake", "bread", "jam"]


def explain_rejection(proc: Process, prize: Prize) -> str:
    return f"(No story: this little world always keeps the chosen ingredients in the process, so {prize.label} must fit {proc.name}.)"


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "process", None) is None or c[1] == getattr(args, "process", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        pass
    place, process_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, process=process_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "process", None) and getattr(args, "prize", None):
        proc, prize = _safe_lookup(PROCESSES, getattr(args, "process", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not process_at_risk(proc, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    return valid_story_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROCESSES, params.process), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
valid_story(Place, Proc, Prize) :- setting(Place), process(Proc), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.place))
    for pid in PROCESSES:
        lines.append(asp.fact("process", pid))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about process and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--process", choices=PROCESSES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.process} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
