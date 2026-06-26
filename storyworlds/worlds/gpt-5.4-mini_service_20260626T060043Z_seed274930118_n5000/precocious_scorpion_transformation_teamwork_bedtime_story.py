#!/usr/bin/env python3
"""
A small bedtime story world about a precocious scorpion, a gentle
transformation, and teamwork that helps the night end happily.

The source tale behind this world is simple:
a bright little scorpion wants one more adventure before bed, but the room is
not ready and the scorpion is a little too lively to settle down. With help
from a kind helper, the scorpion changes into a sleepy sparkly form, tidies the
room together, and finally curls up for sleep.

This script turns that premise into a tiny simulation with stateful physical
and emotional meters, grounded story generation, and an inline ASP twin.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    item_kind: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    covers: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = __import__('collections').defaultdict(float)
        if self.memes is None:
            self.memes = __import__('collections').defaultdict(float)

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
    indoor: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
class Transformation:
    id: str
    label: str
    prep: str
    result_label: str
    calm_bonus: float
    teamwork_bonus: float
    covers: set[str] = field(default_factory=set)
    transforms_to: str = ""
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
    activity: str
    transformation: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _physical_tick(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("restless", 0.0) >= THRESHOLD and not e.memes.get("calmed", 0.0):
            e.meters["wiggle"] = e.meters.get("wiggle", 0.0) + 1
            out.append(f"{e.id} could not stay still.")
    return out


def _transform_tick(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("trust", 0.0) < THRESHOLD:
        return out
    if helper.meters.get("prepared", 0.0) < THRESHOLD:
        return out
    sig = ("transformed", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    form = _safe_fact(world, world.facts, "transformation")
    hero.type = form.transforms_to
    hero.label = form.result_label
    hero.meters["glow"] = hero.meters.get("glow", 0.0) + 1
    hero.memes["calmed"] = hero.memes.get("calmed", 0.0) + form.calm_bonus
    out.append(f"{hero.id} grew still and became a {form.result_label}.")
    return out


def _teamwork_tick(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("cooperate", 0.0) >= THRESHOLD and helper.memes.get("care", 0.0) >= THRESHOLD:
        sig = ("teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["safe"] = hero.memes.get("safe", 0.0) + 1
        helper.meters["prepared"] = helper.meters.get("prepared", 0.0) + 1
        out.append("They worked together quietly, like two stars sharing one sky.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_physical_tick, _teamwork_tick, _transform_tick):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(place: Place) -> str:
    if place.name == "the moonlit bedroom":
        return "The bedroom was soft and blue with moonlight."
    if place.name == "the quiet nursery":
        return "The nursery glowed gently, and the curtains breathed with the night air."
    return f"{place.name.capitalize()} was cozy and calm."


def tell(place: Place, act: Activity, trans: Transformation,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str,
         trait: str) -> World:
    world = World(place)
    world.facts["activity"] = act
    world.facts["transformation"] = trans

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label="a bright little scorpion",
        traits=["little", trait, "precocious"],
        meters={"restless": 1.0},
        memes={"joy": 1.0, "curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="a gentle helper",
        traits=["patient", "kind"],
        meters={"prepared": 1.0},
        memes={"care": 1.0, "trust": 1.0},
    ))

    world.say(f"{hero_name} was a {trait} little scorpion who loved bedtime stories and one more peek at the night sky.")
    world.say(f"{helper_name} was nearby, ready to help {hero_name} settle down kindly.")

    world.para()
    world.say(setting_detail(place))
    world.say(f"One evening, {hero_name} wanted to {act.verb}, but the room was already whisper-quiet for sleep.")
    world.say(f"{helper_name} smiled and said, '{trans.prep} and we can make bedtime feel special together.'")
    hero.memes["cooperate"] = 1.0
    helper.meters["prepared"] = 1.0
    propagate(world, narrate=True)

    world.para()
    if hero.type != trans.transforms_to:
        world.say(f"{hero_name} blinked, listened, and held still as the little change began.")
        propagate(world, narrate=True)

    world.para()
    hero.meters["restless"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + trans.calm_bonus
    helper.memes["care"] = helper.memes.get("care", 0.0) + trans.teamwork_bonus
    world.say(f"Together, they tidied the pillows, dimmed the lamp, and made a cozy nest.")
    world.say(f"At last, {hero_name} was {trans.gerund if hasattr(trans, 'gerund') else 'resting'} and the night felt soft again.")
    world.say(f"{hero_name} curled up as a {trans.result_label}, while {helper_name} watched the room glow like a tiny promise.")
    world.facts.update(hero=hero, helper=helper, place=place, transformed=(hero.type == trans.transforms_to))
    return world


PLACES = {
    "bedroom": Place(name="the moonlit bedroom", indoor=True, affords={"pause", "tidy", "read"}),
    "nursery": Place(name="the quiet nursery", indoor=True, affords={"pause", "tidy", "sing"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek under the moon curtains",
        gerund="peeking under the moon curtains",
        rush="scuttle to the window",
        mess="restless",
        soil="too wakeful",
        zone={"feet"},
        keyword="moon",
        tags={"night", "moon"},
    ),
    "twirl": Activity(
        id="twirl",
        verb="twirl around the rug",
        gerund="twirling around the rug",
        rush="dash in circles",
        mess="restless",
        soil="too lively",
        zone={"feet", "tail"},
        keyword="twirl",
        tags={"motion", "bedtime"},
    ),
}

TRANSFORMATIONS = {
    "lantern": Transformation(
        id="lantern",
        label="lantern",
        prep="Let us make a tiny bedtime change",
        result_label="sleepy lantern-scorpion",
        calm_bonus=1.0,
        teamwork_bonus=1.0,
        covers={"body"},
        transforms_to="lantern-scorpion",
    ),
    "blanket": Transformation(
        id="blanket",
        label="blanket wrap",
        prep="Let us turn the restless feeling into a cozy wrap",
        result_label="blanket-scorpion",
        calm_bonus=1.0,
        teamwork_bonus=1.0,
        covers={"body"},
        transforms_to="blanket-scorpion",
    ),
}

TRAITS = ["precocious", "curious", "bright", "gentle", "spirited"]
NAMES = ["Iris", "Milo", "Nina", "Theo", "Luna", "Pip"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in PLACES:
        for act in ACTIVITIES:
            for tr in TRANSFORMATIONS:
                out.append((place, act, tr))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act: Activity = _safe_fact(world, f, "activity")
    trans: Transformation = _safe_fact(world, f, "transformation")
    return [
        f'Write a bedtime story for a small child about a precocious scorpion who wants to {act.verb}.',
        f"Tell a gentle tale where teamwork helps a scorpion change with a {trans.label}.",
        f'Write a cozy story that includes the words "{act.keyword}" and "teamwork" and ends with sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    act: Activity = _safe_fact(world, f, "activity")
    trans: Transformation = _safe_fact(world, f, "transformation")
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id}, a precocious little scorpion who needed help settling down for bed.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before sleep?",
            answer=f"{hero.id} wanted to {act.verb}, but the room was already meant to be quiet for bedtime.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{hero.id} and {helper.id} worked together, and that teamwork helped the scorpion make the gentle {trans.label} change.",
        ),
        QAItem(
            question=f"What changed at the end for {hero.id}?",
            answer=f"By the end, {hero.id} had transformed into a {trans.result_label} and curled up peacefully for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is for getting ready to sleep so the body can rest and be strong again in the morning.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together kindly to do something that is easier or nicer when shared.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="What is a scorpion?",
            answer="A scorpion is a small animal with claws and a curved tail.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={ {k: v for k, v in e.meters.items() if v} } "
            f"memes={ {k: v for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(H). helper(K). activity(A). transformation(T).
precocious_story(H,A,T) :- hero(H), activity(A), transformation(T).

teamwork(H,K) :- trust(H,K), care(K,H).
can_transform(H,T) :- teamwork(H,K), prepared(K), calm_bonus(T,C), C >= 1.
resolved(H) :- can_transform(H,T), transforms_to(T,_).

#show precocious_story/3.
#show teamwork/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    lines.append(asp.fact("trust", "hero", "helper"))
    lines.append(asp.fact("care", "helper", "hero"))
    lines.append(asp.fact("prepared", "helper"))
    for t in TRANSFORMATIONS.values():
        lines.append(asp.fact("calm_bonus", t.id, int(t.calm_bonus)))
        lines.append(asp.fact("transforms_to", t.id, t.transforms_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show precocious_story/3."))
    return sorted(set(asp.atoms(model, "precocious_story")))


def asp_verify() -> int:
    python_set = set((p, a, t) for p, a, t in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a precocious scorpion, teamwork, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "transformation", None):
        combos = [c for c in combos if c[2] == getattr(args, "transformation", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, trans = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Mira", "Nora", "Sage", "Lia"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        transformation=trans,
        hero_name=hero_name,
        hero_type="scorpion",
        helper_name=helper_name,
        helper_type="parent",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(TRANSFORMATIONS, params.transformation),
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        params.trait,
    )
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


CURATED = [
    StoryParams(place="bedroom", activity="peek", transformation="lantern", hero_name="Iris", hero_type="scorpion", helper_name="Mira", helper_type="parent", trait="precocious"),
    StoryParams(place="nursery", activity="twirl", transformation="blanket", hero_name="Pip", hero_type="scorpion", helper_name="Nora", helper_type="parent", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show precocious_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show precocious_story/3.\n#show teamwork/2.\n#show resolved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
