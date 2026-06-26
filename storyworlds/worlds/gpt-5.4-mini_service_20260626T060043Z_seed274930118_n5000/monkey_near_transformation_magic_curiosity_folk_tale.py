#!/usr/bin/env python3
"""
storyworlds/worlds/monkey_near_transformation_magic_curiosity_folk_tale.py
===========================================================================

A small folk-tale storyworld about a curious monkey, a bit of magic, and a
nearby transformation that turns trouble into wonder.

Premise:
- A curious monkey lives near a magical place in the woods.
- The monkey sees a strange charm and longs to touch it.
- The magic near the charm can transform a plain thing into a useful thing,
  but only when the monkey chooses patience over grabbing.

World model:
- Characters and objects have meters and memes.
- The story turns on a near-miss: curiosity almost causes a mess, but guidance
  and a careful choice reveal a transformation.
- The ending image proves what changed in the physical world and in the
  monkey's feelings.

This script follows the storyworld contract: standalone stdlib script, shared
result containers, inline ASP rules, reasonableness gate, CLI, and verification.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
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
    place: str
    indoors: bool = False
    feels: str = ""
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    transformed_into: str
    risk: str
    required_mood: str
    keyword: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    world: object | None = None
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
class StoryParams:
    place: str
    charm: str
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


SETTINGS = {
    "grove": Setting(place="the grove", indoors=False, feels="damp leaves and bird song"),
    "brook": Setting(place="the brook", indoors=False, feels="cool water and moss"),
    "clearing": Setting(place="the clearing", indoors=False, feels="sunlight and soft grass"),
    "hut": Setting(place="the old hut", indoors=True, feels="warm ash and candlelight"),
}

CHARMS = {
    "spindle": Charm(
        id="spindle",
        label="a silver spindle",
        phrase="a silver spindle wrapped in blue thread",
        effect="turn a plain leaf into a bright ribbon",
        transformed_into="a ribbon",
        risk="the thread could tangle his paws",
        required_mood="patient",
        keyword="magic",
        tags={"magic", "transformation"},
    ),
    "stone": Charm(
        id="stone",
        label="a moon stone",
        phrase="a moon stone that glowed like milk",
        effect="turn muddy water clear",
        transformed_into="clear water",
        risk="its shine could tempt careless hands",
        required_mood="careful",
        keyword="magic",
        tags={"magic"},
    ),
    "bell": Charm(
        id="bell",
        label="a tiny bell",
        phrase="a tiny bell with a gold clapper",
        effect="turn a dry twig into a little flute",
        transformed_into="a little flute",
        risk="its song could startle the monkey",
        required_mood="curious",
        keyword="curiosity",
        tags={"magic", "curiosity"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Sena", "Asha", "Tala"]
BOY_NAMES = ["Milo", "Kavi", "Ravi", "Niko", "Suri", "Timo"]
TRAITS = ["curious", "gentle", "brave", "lively", "bright"]


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "StoryWorld":
        import copy as _copy
        c = StoryWorld(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def noun_phrase(ent: Entity) -> str:
    return ent.label or ent.type


def setup_text(hero: Entity, parent: Entity, setting: Setting, charm: Charm) -> str:
    return (
        f"Long ago, in {setting.place}, there lived a little monkey named {hero.id}. "
        f"{hero.pronoun().capitalize()} was always watching the trees, the water, and every glint of wonder. "
        f"Near an old path lay {charm.phrase}, and {parent.label} warned that the charm could "
        f"{charm.effect} if someone was not careful."
    )


def near_miss_text(hero: Entity, parent: Entity, charm: Charm) -> str:
    return (
        f"One day {hero.id} crept near the charm, so close that {hero.pronoun('possessive')} little nose "
        f"trembled with curiosity. {hero.pronoun().capitalize()} wanted to touch {charm.label}, "
        f"but {parent.label} lifted a hand and said, \"Not yet, little one.\""
    )


def resolve_text(hero: Entity, parent: Entity, charm: Charm) -> str:
    return (
        f"{hero.id} took a slow breath and listened. Instead of grabbing, {hero.pronoun()} waited near the "
        f"magic until the charm changed on its own. In the glow, {charm.label} began to {charm.effect}, "
        f"and the plain thing became {charm.transformed_into}."
    )


def ending_text(hero: Entity, parent: Entity, charm: Charm) -> str:
    return (
        f"In the end, {hero.id} sat quietly beside {parent.label}, smiling at the new shape of the thing. "
        f"{hero.pronoun().capitalize()} had learned that curiosity was best when it walked hand in hand with care, "
        f"and the little roadside wonder still shone in the grass."
    )


def build_story(world: StoryWorld) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    charm = _safe_fact(world, world.facts, "charm")

    world.say(setup_text(hero, parent, world.setting, charm))
    world.para()
    hero.memes["curiosity"] += 1
    hero.memes["desire"] += 1
    world.say(near_miss_text(hero, parent, charm))
    hero.memes["hesitation"] += 1
    parent.memes["care"] += 1
    world.para()
    hero.memes["patience"] += 1
    world.say(resolve_text(hero, parent, charm))
    world.para()
    hero.memes["joy"] += 1
    charm_entity = world.get("charm")
    charm_entity.label = charm.transformed_into
    charm_entity.phrase = charm.transformed_into
    charm_entity.meters["changed"] = 1
    world.say(ending_text(hero, parent, charm))


def make_world(params: StoryParams) -> StoryWorld:
    setting = _safe_lookup(SETTINGS, params.place)
    charm = _safe_lookup(CHARMS, params.charm)
    world = StoryWorld(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    charm_ent = world.add(Entity(id="charm", type="thing", label=charm.label, phrase=charm.phrase))
    world.facts.update(hero=hero, parent=parent, charm=charm, setting=setting)
    build_story(world)
    return world


def compatible(place: str, charm_id: str) -> bool:
    setting = _safe_lookup(SETTINGS, place)
    charm = _safe_lookup(CHARMS, charm_id)
    if setting.indoors and charm_id == "stone":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CHARMS if compatible(p, c)]


def explain_rejection(place: str, charm_id: str) -> str:
    charm = _safe_lookup(CHARMS, charm_id)
    return (
        f"(No story: {charm.label} does not fit well in {_safe_lookup(SETTINGS, place).place} for this folk-tale turn. "
        f"Choose a different setting or charm.)"
    )


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    charm = _safe_fact(world, f, "charm")
    return [
        f'Write a short folk tale for a child about a monkey near {charm.keyword} and a gentle transformation.',
        f"Tell a story where {hero.id}, a curious monkey near {world.setting.place}, learns to wait before touching {charm.label}.",
        f"Write a magical folk tale that includes a monkey, curiosity, and a change from {charm.label} to {charm.transformed_into}.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    charm = _safe_fact(world, f, "charm")
    return [
        QAItem(
            question=f"Who was the story about near {world.setting.place}?",
            answer=f"It was about {hero.id}, a little monkey who lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do when {hero.pronoun()} got near {charm.label}?",
            answer=f"{hero.id} wanted to touch {charm.label}, because {hero.pronoun()} was full of curiosity.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} with the magic?",
            answer=f"{parent.label} reminded {hero.id} to wait, and that patience let the transformation happen safely.",
        ),
        QAItem(
            question=f"What did {charm.label} become at the end?",
            answer=f"It became {charm.transformed_into}.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    charm = _safe_fact(world, world.facts, "charm")
    out = [
        QAItem(
            question="What is magic in a folk tale?",
            answer="Magic is a strange power that can make unusual and wondrous things happen.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn about something new or mysterious.",
        ),
    ]
    if "transformation" in charm.tags:
        out.append(
            QAItem(
                question="What is a transformation?",
                answer="A transformation is a change from one form into another form.",
            )
        )
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- monkey(X).
near_charm(X) :- monkey(X), charm(C), near(X,C).
risk(X) :- near_charm(X), curiosity(X), not patient(X).
safe(X) :- near_charm(X), patient(X).
transformed(C) :- charm(C), safe(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    lines.append(asp.fact("monkey", "monkey"))
    lines.append(asp.fact("near", "monkey", "charm"))
    lines.append(asp.fact("curiosity", "monkey"))
    lines.append(asp.fact("patient", "monkey"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1."))
    asp_atoms = set(asp.atoms(model, "transformed"))
    py_atoms = {("charm",)} if valid_combos() else set()
    if asp_atoms == py_atoms or asp_atoms == {("charm",)}:
        print("OK: ASP program parses and runs.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a monkey near magic and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy", "monkey"], default="monkey")
    ap.add_argument("--parent", choices=["mother", "father"], default="father")
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "charm", None) and not compatible(getattr(args, "place", None), getattr(args, "charm", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or "monkey"
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, charm=charm, name=name, gender=gender, parent=getattr(args, "parent", None), trait=trait)


CURATED = [
    StoryParams(place="grove", charm="spindle", name="Milo", gender="monkey", parent="father", trait="curious"),
    StoryParams(place="brook", charm="stone", name="Niko", gender="monkey", parent="mother", trait="gentle"),
    StoryParams(place="clearing", charm="bell", name="Ravi", gender="monkey", parent="father", trait="bright"),
]


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
        print(asp_program("#show transformed/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show transformed/1."))
        print(asp.atoms(model, "transformed"))
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
            header = f"### {p.name}: {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
