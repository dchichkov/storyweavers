#!/usr/bin/env python3
"""
A small mythic storyworld about a bright streak, a moral value, and a child
who must learn that some light is not meant to be hoarded.

Seed tale used to build the world:
---
On a high hill above a quiet village, a child saw a streak of dawn that ran
across the sky like a golden ribbon. The child wanted to keep it and hide it in
a jar, because it was beautiful. But an old keeper of stories warned that a
streak of light belongs to everyone who walks in the dark.

The child took the jar anyway and tried to trap the streak. Yet the light
slipped away and dimmed the path for the travelers below. Then the child felt
ashamed. The child opened the jar, and the streak flowed back into the sky.
The path brightened again, and the village could see its way home.

The moral value was clear: beauty grows when it is shared.
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
    path: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
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
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    blessed: bool = False
    aid: object | None = None
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
class Aid:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
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


@dataclass
class StoryParams:
    place: str
    action: str
    relic: str
    hero: str
    hero_type: str
    elder: str
    virtue: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _apply_reckless(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("desire", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("glow", 0.0) < THRESHOLD:
            continue
        relic = next((e for e in world.entities.values() if e.kind == "relic"), None)
        if relic is None:
            continue
        sig = ("reckless", hero.id, relic.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if relic.region in world.zone:
            relic.meters["hidden"] = relic.meters.get("hidden", 0.0) + 1
            hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
            out.append(f"The {relic.label} was taken too tightly, and its light grew shy.")
    return out


def _apply_dim_path(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    relic = next((e for e in world.entities.values() if e.kind == "relic"), None)
    if path is None or relic is None:
        return out
    if relic.meters.get("hidden", 0.0) >= THRESHOLD and path.meters.get("safe", 0.0) > 0:
        sig = ("dim",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        path.meters["safe"] -= 1
        path.meters["dark"] = path.meters.get("dark", 0.0) + 1
        out.append("The path lost some of its shine, and the travelers walked more slowly.")
    return out


CAUSAL_RULES = [_apply_reckless, _apply_dim_path]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, hero: Entity, action: str, relic_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["glow"] = sim.get(hero.id).meters.get("glow", 0.0) + 1
    sim.get(hero.id).memes["desire"] = sim.get(hero.id).memes.get("desire", 0.0) + 1
    sim.zone = {"path", "sky"}
    sim.get(relic_id).meters["hidden"] = sim.get(relic_id).meters.get("hidden", 0.0) + 1
    propagate(sim, narrate=False)
    path = sim.get("path")
    relic = sim.get(relic_id)
    return {
        "dimmed": path.meters.get("dark", 0.0) > 0,
        "hidden": relic.meters.get("hidden", 0.0) > 0,
    }


def reasonableness_gate(place: Place, action: str, relic: Relic, aid: Optional[Aid]) -> bool:
    if action not in place.affords:
        return False
    if relic.region not in {"sky", "path"}:
        return False
    if aid is None:
        return False
    return relic.risk in aid.wards and relic.region in aid.covers


def select_aid(action: str, relic: Relic) -> Optional[Aid]:
    for aid in AID_REGISTRY:
        if relic.risk in aid.wards and relic.region in aid.covers:
            return aid
    return None


def tell_myth(world: World, hero: Entity, elder: Entity, relic: Entity, action: str, aid: Aid) -> None:
    world.say(f"On a high hill above {world.place.name}, {hero.id} was a little {hero.type} who watched the heavens.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved the {relic.label} and said it was the kind of wonder that made old songs wake up.")
    world.para()
    world.say(f"One evening, the {hero.id} and the {elder.label} went to {world.place.name}.")
    world.say(f"The place was quiet, and the long {relic.label} lay over the {aid.label if aid else 'dark stones'} like a promise.")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.meters["glow"] = hero.meters.get("glow", 0.0) + 1
    world.say(f"{hero.pronoun('subject').capitalize()} wanted to {action}, because {relic.label} was beautiful and the sight filled {hero.pronoun('object')} with pride.")
    world.say(f'"If you trap what shines," {elder.pronoun("subject")} said, "you may leave the world with less light."')
    if predict(world, hero, action, relic.id)["dimmed"]:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        world.say(f"But {hero.id} did not listen at once. {hero.pronoun('subject').capitalize()} reached for the {relic.label} with both hands.")
        hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
        world.say(f"The {relic.label} was taken too tightly, and its glow slipped away from the path.")
        world.zone = {"path", "sky"}
        relic.meters["hidden"] = relic.meters.get("hidden", 0.0) + 1
        propagate(world, narrate=True)
        world.para()
        world.say(f"Then shame touched {hero.pronoun('object')} like cold rain. {hero.pronoun('subject').capitalize()} opened the hands and let the {relic.label} breathe again.")
        hero.memes["humility"] = hero.memes.get("humility", 0.0) + 1
        hero.memes["pride"] = 0.0
        relic.meters["hidden"] = 0.0
        path = world.get("path")
        path.meters["safe"] = path.meters.get("safe", 0.0) + 1
        path.meters["dark"] = max(0.0, path.meters.get("dark", 0.0) - 1)
        world.say(f"The {relic.label} flowed back into the sky, and the road below brightened for all who were coming home.")
        world.say(f"At the end, the village could see the way, and {hero.id} learned that a good thing becomes greater when it is shared.")
    else:
        world.say(f"{hero.id} found a wiser way and left the {relic.label} free to shine for everyone.")
    world.facts.update(hero=hero, elder=elder, relic=relic, aid=aid, action=action)


def build_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label="old keeper of stories"))
    relic = world.add(Entity(
        id="streak",
        kind="relic",
        type="relic",
        label="streak of dawn",
        phrase="a streak of dawn like a golden ribbon",
        owner=hero.id,
    ))
    path = world.add(Entity(id="path", kind="thing", type="path", label="path"))
    path.meters["safe"] = 1.0
    hero.memes["wonder"] = 1.0
    aid = select_aid(params.action, Relic(id="streak", label="streak of dawn", phrase="", region="sky", risk="fade"))
    if aid is None:
        pass
    tell_myth(world, hero, elder, relic, params.action, aid)
    return world


PLACE_REGISTRY = {
    "hill": Place(name="the high hill", kind="outdoors", affords={"trap", "carry"}),
    "gate": Place(name="the city gate", kind="outdoors", affords={"trap", "carry"}),
    "spring": Place(name="the spring valley", kind="outdoors", affords={"trap", "carry"}),
}

RELIC_REGISTRY = {
    "streak": Relic(id="streak", label="streak of dawn", phrase="a streak of dawn like a golden ribbon", region="sky", risk="fade"),
    "ember": Relic(id="ember", label="ember-streak", phrase="an ember-streak in the dusk", region="sky", risk="fade"),
}

AID_REGISTRY = [
    Aid(id="lanterns", label="lanterns", covers={"sky"}, wards={"fade"}, prep="carry lanterns instead", tail="walked on with the lanterns", plural=True),
    Aid(id="song", label="a shared song", covers={"sky"}, wards={"fade"}, prep="sing together instead", tail="sang the shared song", plural=False),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pname, place in PLACE_REGISTRY.items():
        for action in place.affords:
            for rid, relic in RELIC_REGISTRY.items():
                aid = select_aid(action, relic)
                if aid and reasonableness_gate(place, action, relic, aid):
                    out.append((pname, action, rid))
    return out


def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place, action, relic in valid_combos():
        for gender in {"girl", "boy"}:
            out.append((place, action, relic, gender))
    return out


KNOWLEDGE = {
    "streak": [("What is a streak?", "A streak is a long, thin line or band that seems to run across something.")],
    "dawn": [("What is dawn?", "Dawn is the time when the sun first begins to light up the sky.")],
    "lanterns": [("What are lanterns for?", "Lanterns hold light and help people see in the dark.")],
    "song": [("Why do people sing together?", "People sing together to share joy, keep a rhythm, and feel united.")],
    "moral": [("What is a moral?", "A moral is a lesson that tells people how to live well and kindly.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a short myth for a child about {hero.id}, a streak of dawn, and a lesson about sharing beauty.",
        f"Tell a gentle legend where {hero.id} learns not to trap the streak, but to let it shine for everyone.",
        f"Write a simple myth with the word 'streak' that ends with a moral value about generosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic, aid = f["hero"], f["elder"], f["relic"], f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {relic.label}?",
            answer=f"{hero.id} wanted to trap the {relic.label} in a jar, because it looked beautiful and {hero.pronoun('subject')} feared losing it.",
        ),
        QAItem(
            question=f"Why did the old keeper of stories warn {hero.id}?",
            answer=f"The keeper warned {hero.id} because a {relic.label} belongs to everyone who needs light, and trapping it could dim the path.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end of the story?",
            answer=f"{hero.id} changed from wanting to keep the light alone to opening the hands and sharing it, which made the road bright again.",
        ),
        QAItem(
            question="What was the moral value of the story?",
            answer="The moral value was that beauty grows when it is shared.",
        ),
        QAItem(
            question=f"What helped the village after {hero.id} let the streak go?",
            answer=f"The {relic.label} returned to the sky, the path grew brighter, and the people could see their way home.",
        ),
        QAItem(
            question=f"How did {aid.label} fit into the story?",
            answer=f"{aid.label.capitalize()} were the wise answer to the danger, because they helped guide the travelers without stealing the light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"streak", "dawn", "moral"}
    if world.facts.get("aid"):
        tags.add(world.facts["aid"].id)
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", action="trap", relic="streak", hero="Ari", hero_type="boy", elder="elder", virtue="generosity"),
    StoryParams(place="spring", action="carry", relic="ember", hero="Mina", hero_type="girl", elder="elder", virtue="humility"),
]


def explain_rejection(place: Place, action: str, relic: Relic) -> str:
    return f"(No story: {place.name} does not honestly support a tale where someone tries to {action} the {relic.label}.)"


def explain_gender(relic_id: str, gender: str) -> str:
    return f"(No story: this mythic world does not restrict the {relic_id} by gender, so the request is already allowed.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pname, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pname))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pname, a))
    for rid, relic in RELIC_REGISTRY.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("region", rid, relic.region))
        lines.append(asp.fact("risk", rid, relic.risk))
    for aid in AID_REGISTRY:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
        for w in sorted(aid.wards):
            lines.append(asp.fact("wards", aid.id, w))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(R) :- region(R, sky).
compatible(P, A, R) :- affords(P, A), at_risk(R), risk(R, fade), aid(X), covers(X, sky), wards(X, fade).
valid_story(P, A, R) :- compatible(P, A, R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about a streak and a moral lesson.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--action", choices=["trap", "carry"])
    ap.add_argument("--relic", choices=RELIC_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["elder"])
    ap.add_argument("--virtue", choices=["generosity", "humility"])
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
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos
                if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
                and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, relic = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(["Ari", "Mina", "Sora", "Lio"])
    elder = getattr(args, "elder", None) or "elder"
    virtue = getattr(args, "virtue", None) or rng.choice(["generosity", "humility"])
    return StoryParams(place=place, action=action, relic=relic, hero=hero, hero_type=gender, elder=elder, virtue=virtue)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACE_REGISTRY[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label="old keeper of stories"))
    relic = world.add(Entity(id="streak", kind="relic", type="relic", label="streak of dawn", phrase="a streak of dawn like a golden ribbon"))
    path = world.add(Entity(id="path", kind="thing", type="path", label="path"))
    path.meters["safe"] = 1.0
    aid = select_aid(params.action, RELIC_REGISTRY[params.relic])
    if aid is None:
        pass
    tell_myth(world, hero, elder, relic, params.action, aid)
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
        print(asp_program("#show valid_story/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
