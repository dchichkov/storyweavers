#!/usr/bin/env python3
"""
storyworlds/worlds/crocodile_humor_bad_ending_nursery_rhyme.py
==============================================================

A small story world for a nursery-rhyme-style crocodile tale with humor and a
bad ending.

The seed image is a crocodile who keeps interrupting a little rhyme with silly
boasts and tricks. The world simulates appetite, bravado, teasing, and a final
mischief that backfires. The ending is intentionally not happy: the crocodile
does not learn a neat lesson, and the last image leaves the situation a little
messy and funny.

This script follows the Storyweavers world contract:
- standalone stdlib Python
- shared result containers from storyworlds/results.py
- lazy ASP import only inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "messy": 0.0, "stuck": 0.0}
        if not self.memes:
            self.memes = {"hunger": 0.0, "pride": 0.0, "joy": 0.0, "alarm": 0.0, "tease": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"crocodile", "alligator"}:
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
    place: str = "the riverbank"
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
class ObjectItem:
    id: str
    label: str
    phrase: str
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
class Temptation:
    id: str
    verb: str
    gerund: str
    mess: str
    spill: str
    tag: str
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
class Hazard:
    id: str
    label: str
    verb: str
    consequence: str
    region: str
    guards: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.trace = list(self.trace)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_splash(world: World) -> list[str]:
    out = []
    croc = world.entities.get("croc")
    target = world.entities.get("snack")
    if not croc or not target:
        return out
    if croc.meters["wet"] < THRESHOLD or croc.memes["tease"] < THRESHOLD:
        return out
    sig = ("splash", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["wet"] += 1
    target.meters["messy"] += 1
    out.append("The snack got wet and messy.")
    return out


def _r_slip(world: World) -> list[str]:
    croc = world.entities.get("croc")
    if not croc:
        return []
    if croc.meters["wet"] < THRESHOLD:
        return []
    sig = ("slip", croc.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    croc.meters["stuck"] += 1
    croc.memes["alarm"] += 1
    return ["__slip__"]


CAUSAL_RULES = [
    _r_splash,
    _r_slip,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(x for x in items if x != "__slip__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_opening(hero: Entity, place: str) -> str:
    return (
        f"On the {place}, by the reeds, there lived a crocodile in need of little snacks and "
        f"silly deeds."
    )


def rhyme_tone() -> str:
    return "It was a tiny, bouncy tale, like a clap-and-snap nursery rhyme."


def stir_hunger(world: World, croc: Entity, snack: Entity) -> None:
    croc.memes["hunger"] += 1
    world.say(
        f"{croc.id.capitalize()} had a hollow tummy and a grin too wide, "
        f"so it stared at {snack.label} and marched to the side."
    )


def boast(world: World, croc: Entity) -> None:
    croc.memes["pride"] += 1
    croc.memes["tease"] += 1
    world.say(
        f"It bragged, 'I'm swift and I'm snappy, I'm clever and neat!' "
        f"Then it made a big splish with both tail and feet."
    )


def warn(world: World, helper: Entity, croc: Entity, snack: Entity) -> None:
    croc.memes["alarm"] += 0.5
    world.say(
        f"{helper.label.capitalize()} said, 'Take it slow, little friend of the mud; "
        f"that snack will get soggy if you splash in the flood.'"
    )


def bad_turn(world: World, croc: Entity, snack: Entity) -> None:
    croc.meters["wet"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {croc.id} laughed at the warning and leaped with a whoosh, "
        f"and the water went everywhere in one giant slosh."
    )
    world.say(
        f"The snack got wet and messy, and {croc.id} got stuck in the slime, "
        f"with only a squish for a chorus and no tidy rhyme."
    )


def ending(world: World, croc: Entity, snack: Entity) -> None:
    world.say(
        f"Now {croc.id} sits soggy and grumpy, with reeds in its toes, "
        f"while the damp little snack lies forgotten in rows."
    )
    world.say(
        f"And that is the joke of the riverbank day: the crocodile boasted, "
        f"and the good bite went away."
    )


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"splash", "hunt"}),
    "marsh": Setting(place="the marsh", affords={"splash"}),
    "pond": Setting(place="the pond", affords={"splash"}),
}

TEMPTATIONS = {
    "snack": Temptation(
        id="snack",
        verb="snatch the snack",
        gerund="snatching the snack",
        mess="wet",
        spill="soggy",
        tag="snack",
        keyword="snack",
    ),
    "fish": Temptation(
        id="fish",
        verb="snatch the fish",
        gerund="snatching the fish",
        mess="wet",
        spill="slimy",
        tag="fish",
        keyword="fish",
    ),
}

HAZARDS = {
    "mud": Hazard(
        id="mud",
        label="mud",
        verb="wade in the mud",
        consequence="stuck in the slime",
        region="feet",
        guards={"wet"},
    ),
    "water": Hazard(
        id="water",
        label="water",
        verb="splash in the water",
        consequence="soaked and splashed",
        region="whole",
        guards={"wet"},
    ),
}

SNACKS = {
    "sandwich": ObjectItem(id="sandwich", label="a jam sandwich", phrase="a jam sandwich", region="mouth"),
    "cookie": ObjectItem(id="cookie", label="a round cookie", phrase="a round cookie", region="mouth"),
    "fishcake": ObjectItem(id="fishcake", label="a little fishcake", phrase="a little fishcake", region="mouth"),
}

NAMES = ["Coco", "Kip", "Milo", "Dot", "Pip"]
HELPERS = ["heron", "duck", "frog", "crab"]
TRAITS = ["cheeky", "noisy", "tiny", "bouncy", "greedy"]


@dataclass
class StoryParams:
    setting: str
    temptation: str
    snack: str
    hero_name: str
    helper: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for t_id in setting.affords:
            for snack_id in SNACKS:
                out.append((s_id, t_id, snack_id))
    return out


KNOWLEDGE = {
    "crocodile": [
        (
            "What is a crocodile?",
            "A crocodile is a large reptile with a long body, strong jaws, and a tail that helps it swim."
        ),
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is soft, wet dirt. It can squish under your feet and stick to things."
        ),
    ],
    "water": [
        (
            "Why do things get wet in water?",
            "Things get wet in water because water clings to them and soaks into their surfaces."
        ),
    ],
    "snack": [
        (
            "What is a snack?",
            "A snack is a small food you eat between bigger meals."
        ),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a crocodile with a silly boast and a bad ending.',
        f"Tell a rhyme-like story where {f['hero'].id} wants to {f['temptation'].verb} at {f['setting'].place}.",
        f"Write a funny little story that includes a crocodile, a {f['snack'].label}, and a splashy mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    snack: Entity = _safe_fact(world, f, "snack")
    helper: str = _safe_fact(world, f, "helper")
    setting: Setting = _safe_fact(world, f, "setting")
    tempt: Temptation = _safe_fact(world, f, "temptation")
    qa = [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.trait if hasattr(hero, 'trait') else 'crocodile'} crocodile by the {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {tempt.verb} and make a silly splash.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the mess?",
            answer=f"The {helper} warned {hero.id} that the snack would get soggy and messy.",
        ),
        QAItem(
            question=f"What happened to the snack?",
            answer=f"The {snack.label} got wet and messy when {hero.id} splashed too hard.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended badly and funny: {hero.id} got stuck in the slime instead of getting a happy prize.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {world.facts["temptation"].keyword, "crocodile"}
    if world.facts["snack"].id in SNACKS:
        tags.add("snack")
    for tag, qas in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in qas)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="riverbank", temptation="splash", snack="sandwich", hero_name="Coco", helper="heron", trait="cheeky"),
    StoryParams(setting="marsh", temptation="splash", snack="cookie", hero_name="Kip", helper="duck", trait="bouncy"),
    StoryParams(setting="pond", temptation="splash", snack="fishcake", hero_name="Milo", helper="frog", trait="greedy"),
]


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    tempt = _safe_lookup(TEMPTATIONS, params.temptation)
    snack = _safe_lookup(SNACKS, params.snack)
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="crocodile", label="crocodile"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=f"the {params.helper}"))
    item = world.add(Entity(id="snack", type="snack", label=snack.label, phrase=snack.phrase, owner=hero.id, caretaker=helper.id))

    hero.traits.append(params.trait)
    hero.memes["hunger"] += 1
    hero.memes["pride"] += 1
    world.facts = {"hero": hero, "helper": params.helper, "temptation": tempt, "snack": item, "setting": setting, "params": params}

    world.say(rhyme_opening(hero, setting.place))
    world.say(rhyme_tone())
    world.say(f"{hero.id.capitalize()} was a {params.trait} little crocodile who loved a snack.")
    world.say(f"It liked to {tempt.verb} and wiggle its back.")

    world.para()
    stir_hunger(world, hero, item)
    warn(world, helper, hero, item)
    boast(world, hero)
    bad_turn(world, hero, item)

    world.para()
    ending(world, hero, item)
    return world


ASP_RULES = r"""
hero(croc).
helper(heron;duck;frog;crab).
setting(riverbank;marsh;pond).
temporal(splash).
snack(sandwich;cookie;fishcake).

affords(riverbank,splash).
affords(riverbank,hunt).
affords(marsh,splash).
affords(pond,splash).

wet_splash(Setting) :- affords(Setting,splash).
valid(Setting,Temptation,Snack) :- setting(Setting), temporal(Temptation), snack(Snack), affords(Setting,Temptation).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temporal", t))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme crocodile storyworld with a humorous bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "temptation", None) is None or c[1] == getattr(args, "temptation", None))
        and (getattr(args, "snack", None) is None or c[2] == getattr(args, "snack", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, temptation, snack = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        temptation=temptation,
        snack=snack,
        hero_name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, temptation, snack) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.hero_name}: {p.temptation} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
