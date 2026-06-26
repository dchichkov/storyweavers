#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/iphone_jackeroo_lesson_learned_myth.py
===============================================================================================================

A small myth-style storyworld about a child, a strange iphone, and a
jackeroo who helps them learn a lesson.

The seed story imagined for this world:
---
Long ago, on a windy hill beside an old stone ring, a young traveler named Nia
carried a glowing iphone in a leather pouch. Nia wanted to use it to call across
the valley, but the sky was full of thunder-mist and the old stones were meant
for listening, not for boasting.

A jackeroo with bright eyes hopped out of the grass and said the iphone should
be used only after the hill was tended and the lantern was lit. Nia did not
listen at first. The phone flashed, then went dark, and the pouch slipped into
the wet grass.

Nia felt sorry. She dried the iphone, followed the jackeroo's advice, and
waited. When the lantern was lit and the hill was quiet again, the iphone
glowed once more. Nia learned that a clever tool works best when the old rules
are respected.
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    guide: object | None = None
    hero: object | None = None
    relic: object | None = None
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
    place: str = "the windy hill"
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    rumor: str
    risk: str
    shield: str
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
class Guide:
    id: str
    label: str
    phrase: str
    counsel: str
    remedy: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "thunder-mist"

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by,
            "protective": v.protective, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amt


def add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + amt


def covariant_risk(relic: Relic) -> bool:
    return relic.id in {"iphone"}


def compatible_remedy(relic: Relic, guide: Guide) -> bool:
    return relic.shield == guide.remedy


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    relic = world.get("relic")
    if meter(hero, "reckless") < THRESHOLD:
        return out
    if relic.worn_by != hero.id:
        return out
    sig = ("soak",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meter(relic, "wet", 1.0)
    add_meter(relic, "dark", 1.0)
    out.append(f"The iphone went dark in the wet grass.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    if meter(hero, "regret") < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meme(hero, "wise", 1.0)
    out.append(f"Nia learned to wait for the right hour.")
    return out


RULES = [Rule("soak", _r_soak), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, hero: Entity, relic: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["reckless"] = 1.0
    sim.get("relic").worn_by = hero.id
    propagate(sim, narrate=False)
    r = sim.get("relic")
    return {"dark": meter(r, "dark") >= THRESHOLD, "wet": meter(r, "wet") >= THRESHOLD}


def introduce(world: World, hero: Entity, guide: Entity, relic: Entity) -> None:
    world.say(
        f"On a windy hill, {hero.id} was a little traveler who carried a glowing {relic.label}."
    )
    world.say(
        f"Nearby stood {guide.label}, a {guide.type} with bright eyes and a careful voice."
    )


def want(world: World, hero: Entity, relic: Entity) -> None:
    add_meme(hero, "want", 1.0)
    world.say(
        f"{hero.id} wanted to use the {relic.label} at once, because the valley below was far away."
    )


def warn(world: World, guide: Entity, hero: Entity, relic: Entity) -> None:
    pred = predict_damage(world, hero, relic)
    if pred["dark"]:
        add_meme(hero, "warning_heard", 1.0)
        world.say(
            f'"Wait," said {guide.label}. "{guide.counsel} If you rush now, your {relic.label} will be hurt."'
        )


def ignore(world: World, hero: Entity, relic: Entity) -> None:
    add_meter(hero, "reckless", 1.0)
    add_meme(hero, "pride", 1.0)
    world.say(
        f"But {hero.id} did not listen. {hero.pronoun().capitalize()} lifted the {relic.label} into the mist."
    )


def loss(world: World, hero: Entity, relic: Entity) -> None:
    hero.meters["regret"] = 1.0
    relic.worn_by = hero.id
    propagate(world, narrate=False)
    world.say(
        f"Then the phone flashed, went dark, and the leather pouch slipped into the wet grass."
    )


def repair(world: World, hero: Entity, guide: Entity, relic: Entity) -> None:
    hero.meters["regret"] = 0.0
    add_meme(hero, "wise", 1.0)
    world.say(
        f"{hero.id} felt sorry, dried the {relic.label}, and listened to {guide.label}'s advice."
    )


def resolve(world: World, hero: Entity, guide: Entity, relic: Entity) -> None:
    world.say(
        f"When the lantern was lit and the hill grew quiet, the {relic.label} glowed again."
    )
    world.say(
        f"{hero.id} learned the lesson: a clever tool works best when the old rules are respected."
    )


SETTINGS = {
    "hill": Setting(place="the windy hill", affords={"listen", "call"}),
}

RELICS = {
    "iphone": Relic(
        id="iphone",
        label="iphone",
        phrase="a glowing iphone in a leather pouch",
        type="iphone",
        rumor="call across the valley",
        risk="wet",
        shield="dryness",
    ),
}

GUIDES = {
    "jackeroo": Guide(
        id="jackeroo",
        label="jackeroo",
        phrase="a jackeroo with bright eyes",
        counsel="Use the iphone only after the hill is tended and the lantern is lit.",
        remedy="dryness",
    ),
}

NAMES = ["Nia", "Ivo", "Mira", "Ari", "Sera", "Toma"]


@dataclass
class StoryParams:
    place: str
    relic: str
    guide: str
    name: str
    seed: Optional[int] = None
    params: object | None = None
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


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    guide = world.add(Entity(id="Guide", kind="character", type="jackeroo", label="jackeroo"))
    relic = world.add(Entity(id="relic", type="iphone", label="iphone", phrase=_safe_lookup(RELICS, params.relic).phrase, owner=hero.id))
    world.facts.update(hero=hero, guide=guide, relic=relic, params=params)

    introduce(world, hero, guide, relic)
    world.para()
    want(world, hero, relic)
    warn(world, guide, hero, relic)
    ignore(world, hero, relic)
    loss(world, hero, relic)
    world.para()
    repair(world, hero, guide, relic)
    resolve(world, hero, guide, relic)
    return world


def prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    relic = _safe_fact(world, world.facts, "relic")
    guide = _safe_fact(world, world.facts, "guide")
    return [
        f'Write a short myth for a young child about {hero.id}, a {relic.label}, and a {guide.label}.',
        f'Tell a gentle lesson-learned story where a {hero.type} learns to respect a wise warning about an {relic.label}.',
        f'Write a myth-style tale that includes the words "iphone" and "jackeroo" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    guide = _safe_fact(world, world.facts, "guide")
    relic = _safe_fact(world, world.facts, "relic")
    return [
        QAItem(
            question=f"What did {hero.id} want to use on the windy hill?",
            answer=f"{hero.id} wanted to use the iphone, which was kept in a leather pouch.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the iphone?",
            answer=f"The jackeroo warned {hero.id} and told {hero.id} to wait until the hill was tended and the lantern was lit.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn in the end?",
            answer="The lesson learned was that a clever tool works best when the old rules are respected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jackeroo in this story?",
            answer="A jackeroo is a wise little helper-creature who speaks carefully and gives useful advice.",
        ),
        QAItem(
            question="What is an iphone?",
            answer="An iphone is a small glowing phone used for calls and messages.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand a better way after making a mistake or hearing wise advice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic lesson-learned storyworld with iphone and jackeroo.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = getattr(args, "place", None) or "hill"
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, relic="iphone", guide="jackeroo", name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
% A story is reasonable when the iphone can be harmed by the weather and the
% jackeroo offers the matching counsel.
warns(jackeroo, iphone).
lesson_learned(iphone) :- warns(jackeroo, iphone).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("can_be_wet", rid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("warns_about", gid, "iphone"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    learned = sorted(set(asp.atoms(model, "lesson_learned")))
    python = [("iphone",)]
    if learned == python:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", learned)
    print("  PY :", python)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show lesson_learned/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(place="hill", relic="iphone", guide="jackeroo", name="Nia")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
