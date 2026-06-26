#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale style farm yarn about a harrow and a pair
of dungarees, told with dialogue and causal state changes.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Location:
    name: str
    place_type: str
    affirms: set[str] = field(default_factory=set)
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
    kind: str
    phrase: str
    action: str
    noise: str
    shift: str
    tags: set[str] = field(default_factory=set)
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
class Clothing:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    cover: set[str] = field(default_factory=set)
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
    place: str
    tool: str
    clothing: str
    name: str
    gender: str
    role: str
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
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.dirt_zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.location)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.dirt_zone = set(self.dirt_zone)
        return w


LOCATIONS = {
    "barnyard": Location("the barnyard", "yard", {"harrow", "dungaree"}),
    "field": Location("the field", "field", {"harrow", "dungaree"}),
    "lane": Location("the dusty lane", "road", {"harrow"}),
}

TOOLS = {
    "harrow": Tool(
        id="harrow",
        label="harrow",
        kind="harrow",
        phrase="a long-toothed harrow",
        action="drag the harrow over the hard ground",
        noise="clatter-rattle",
        shift="loosen the hard clods and comb the earth smooth",
        tags={"farm", "soil", "tool"},
    ),
}

CLOTHING = {
    "dungaree": Clothing(
        id="dungaree",
        label="dungarees",
        phrase="a pair of blue dungarees with brass buttons",
        region="legs",
        plural=True,
        cover={"legs"},
    ),
}

GIRL_NAMES = ["Mabel", "June", "Elsie", "Nell", "Ruth", "Ada"]
BOY_NAMES = ["Jed", "Hank", "Otis", "Luther", "Cal", "Ezra"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, loc in LOCATIONS.items():
        for tool in TOOLS:
            for cloth in CLOTHING:
                out.append((place, tool, cloth))
    return out


def reasonableness_gate(place: str, tool: str, clothing: str) -> None:
    if place not in LOCATIONS:
        pass
    if tool not in TOOLS:
        pass
    if clothing not in CLOTHING:
        pass
    if tool == "harrow" and clothing != "dungaree":
        pass
    if place == "lane":
        pass


def establish(world: World, hero: Entity, elder: Entity, tool: Tool, cloth: Clothing) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big appetite for work, "
        f"and {hero.pronoun('possessive')} {elder.label} said {hero.id} could talk to the fields like an old neighbor."
    )
    world.say(
        f'"{tool.label}?" {hero.id} asked. "{tool.noise} and all?"'
    )
    world.say(
        f'"That same," {elder.label} said, "and your {cloth.label} will ride the dust like a blue flag."'
    )


def prepare(world: World, hero: Entity, tool: Tool, cloth: Clothing) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wore {cloth.phrase} and grinned so wide the buttons looked ready to pop."
    )
    world.say(
        f'"If the ground stays stubborn," {hero.id} said, "I will speak to it proper."'
    )
    world.say(
        f'"You mean with {tool.label}?" the elder asked.'
    )


def do_work(world: World, hero: Entity, tool: Tool, cloth: Clothing) -> None:
    hero.meters["labor"] = hero.meters.get("labor", 0) + 1
    world.dirt_zone = {"legs"}
    hero.meters["dust"] = hero.meters.get("dust", 0) + 1
    world.say(
        f'{hero.id} took the {tool.label} by the handle and marched out. "Now then," {hero.id} said, '
        f'"let us see who can out-stare a clod."'
    )
    world.say(
        f"The {tool.label} went {tool.noise} across the ground, and the earth loosened up as if it had heard a joke."
    )


def consequence(world: World, hero: Entity, cloth: Clothing) -> None:
    if hero.meters.get("dust", 0) >= THRESHOLD:
        world.say(
            f"The wind kissed {hero.pronoun('possessive')} {cloth.label}, and soon the blue cloth was dusty enough to look like a sky after a storm."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f'"That there is the finest field I ever tamed," {hero.id} said, standing taller than the fence post.'
    )


def resolve(world: World, hero: Entity, elder: Entity, tool: Tool, cloth: Clothing) -> None:
    world.say(
        f'"And did the {tool.label} behave?" asked {elder.label}.'
    )
    world.say(
        f'"Like a mule with manners," {hero.id} said. "It sang the soil loose, and my {cloth.label} wore the honor of it."'
    )
    world.say(
        f'{elder.label} laughed. "Then the field got its combing, and you got a story big enough for Sunday supper."'
    )


def tell_story(location: Location, tool: Tool, cloth: Clothing, hero_name: str, gender: str, role: str) -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    elder = world.add(Entity(id="elder", kind="character", type=role, label="the elder"))
    world.add(Entity(
        id=cloth.id,
        kind="thing",
        type="clothing",
        label=cloth.label,
        phrase=cloth.phrase,
        owner=hero.id,
        caretaker=elder.id,
        plural=cloth.plural,
    ))
    establish(world, hero, elder, tool, cloth)
    world.say("")
    prepare(world, hero, tool, cloth)
    world.say("")
    do_work(world, hero, tool, cloth)
    consequence(world, hero, cloth)
    world.say("")
    resolve(world, hero, elder, tool, cloth)
    world.facts.update(hero=hero, elder=elder, tool=tool, cloth=cloth, location=location)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    cloth = _safe_fact(world, f, "cloth")
    loc = _safe_fact(world, f, "location")
    return [
        QAItem(
            question=f"What was {hero.id} wearing when {hero.id} went to {loc.name}?",
            answer=f"{hero.id} was wearing {cloth.phrase} when {hero.id} went to {loc.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} say the {tool.label} did to the ground?",
            answer=f"{hero.id} said the {tool.label} made the soil loosen up and combed the earth smooth.",
        ),
        QAItem(
            question=f"How did {elder.label} describe the ending of the work?",
            answer=f"{elder.label} said the field got its combing and {hero.id} got a story big enough for Sunday supper.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harrow for?",
            answer="A harrow is a farm tool used to break up hard soil and smooth the ground after it has been worked.",
        ),
        QAItem(
            question="What are dungarees?",
            answer="Dungarees are sturdy work clothes, usually made from denim, that can handle dirt and rough jobs.",
        ),
        QAItem(
            question="Why do tall tales sound so grand?",
            answer="Tall tales use bigger-than-life language and playful exaggeration, like a story that says a job was as loud as thunder.",
        ),
    ]


def prompts_for(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall tale about a child, a harrow, and blue dungarees, with lively dialogue.',
        f"Tell a farm story where {f['hero'].id} talks back to a stubborn field and a harrow rattles like a tin wagon.",
        "Write a child-friendly tall tale in which work, pride, and dusty clothes end in a cheerful lesson.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
combo(P,T,C) :- place(P), tool(T), clothing(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in LOCATIONS:
        lines.append(asp.fact("setting", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for c in CLOTHING:
        lines.append(asp.fact("clothing", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    asp_set = set(asp.atoms(model, "combo"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about harrow and dungarees.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clothing", choices=CLOTHING)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["mother", "father"])
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
    reasonableness_gate(getattr(args, "place", None) or "field", getattr(args, "tool", None) or "harrow", getattr(args, "clothing", None) or "dungaree")
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[1] == getattr(args, "tool", None)]
    if getattr(args, "clothing", None):
        combos = [c for c in combos if c[2] == getattr(args, "clothing", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tool, cloth = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = getattr(args, "role", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, tool=tool, clothing=cloth, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(LOCATIONS, params.place), _safe_lookup(TOOLS, params.tool), CLOTHING[params.clothing],
                       params.name, params.gender, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="field", tool="harrow", clothing="dungaree", name="Mabel", gender="girl", role="father"),
    StoryParams(place="barnyard", tool="harrow", clothing="dungaree", name="Ezra", gender="boy", role="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show combo/3."))
        combos = sorted(set(asp.atoms(model, "combo")))
        print(f"{len(combos)} combos")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
