#!/usr/bin/env python3
"""
A small fairy-tale school world with a cautionary rhyme.

Premise:
- A child at school wants to carry a shiny tube around at mid-day.
- A hulking helper warns that the tube is brittle and can break.
- The child nearly makes a mess, then learns a safer way to carry it.

This script follows the Storyweavers standalone-world contract:
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- imports results eagerly and asp lazily
- provides an inline ASP_RULES twin and asp_facts()
- supports trace, qa, json, all, seed, verify, show-asp
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
    fragile: bool = False
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    tube: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "hulk"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the school"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    consequence: str
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        self.zone: set[str] = set()

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


SETTINGS = {
    "school": Setting(place="the school", affords={"tube"}),
}

ACTIVITIES = {
    "tube": Activity(
        id="tube",
        verb="carry the tube through the hall",
        gerund="carrying the tube",
        rush="run with the tube down the hall",
        risk="the tube may crack and spill its bright dust",
        consequence="the tube can crack and make a mess",
        keyword="tube",
        tags={"tube", "school"},
    ),
}

GEAR = [
    Gear(
        id="basket",
        label="a padded basket",
        prep="put the tube in a padded basket first",
        tail="walked slowly with the padded basket",
        protects={"tube"},
    ),
    Gear(
        id="cloth",
        label="a soft cloth wrap",
        prep="wrap the tube in a soft cloth first",
        tail="carried the wrapped tube carefully",
        protects={"tube"},
    ),
]

CHILD_NAMES = ["Mina", "Pip", "Tala", "Nori", "Joss"]
HELPER_NAMES = ["Hulk", "Bran", "Moss"]
TRAITS = ["curious", "brave", "gentle", "spry"]


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tube = world.get("tube")
    helper = world.get("helper")
    if child.meters.get("rush", 0) < THRESHOLD:
        return out
    if tube.worn_by == child.id:
        if child.meters.get("care", 0) >= THRESHOLD:
            return out
        sig = ("break", tube.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        tube.meters["broken"] = 1
        helper.memes["worry"] += 1
        child.memes["shock"] += 1
        out.append("The tube gave a small crack and glittered with a sad little spill.")
    return out


def _r_warning(world: World) -> list[str]:
    child = world.get("child")
    if child.meters.get("warning", 0) < THRESHOLD:
        return []
    if ("warned", child.id) in world.fired:
        return []
    world.fired.add(("warned", child.id))
    child.memes["caution"] += 1
    return ["The warning rang like a bell in a fairy tale hall."]


CAUSAL_RULES = [_r_warning, _r_break]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters["rush"] = child.meters.get("rush", 0) + 1
    world.zone = {activity.id}
    propagate(world, narrate=narrate)


def predict_break(world: World, child: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get("child"), activity, narrate=False)
    return bool(sim.get("tube").meters.get("broken", 0) >= THRESHOLD)


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    helper: str
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


def intro(world: World, child: Entity, helper: Entity, tube: Entity, activity: Activity) -> None:
    world.say(
        f"At {world.setting.place}, little {child.id} was a {child.type} with a {child.memes.get('love', 0):.0f}-hearted smile. "
        f"{helper.id} the hulk stood tall like a kind giant, and the shiny tube waited by the window."
    )
    world.say(
        f"Mid-day light lay gold on the floor, and {child.id} loved {activity.gerund} through the school because it felt like a tiny adventure."
    )


def caution(world: World, child: Entity, helper: Entity, activity: Activity, tube: Entity) -> None:
    child.meters["warning"] = 1
    world.say(
        f"{helper.id} said, \"Dear child, at mid-day don't {activity.rush}, for {activity.risk}.\""
    )
    world.say(
        f"\"A careful step is a wiser step, and a gentle hand keeps a good thing fit.\""
    )


def defy(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubborn"] = child.memes.get("stubborn", 0) + 1
    world.say(
        f"But {child.id} was too eager and tried to {activity.rush}, humming a reckless little rhyme."
    )
    world.say(
        f"\"Quick as a wink, quick as a bee, I'll take the tube and you'll let me be.\""
    )


def warn_burst(world: World, child: Entity, helper: Entity, activity: Activity, tube: Entity) -> None:
    if predict_break(world, child, activity):
        world.say(
            f"{helper.id} hurried after {child.id}, for the hall had turned slippery with hurry and the tube was no toy."
        )
        world.say(
            f"\"If you rush, you'll lose your hush; if you heed, you'll meet your need,\" said {helper.id} the hulk."
        )


def offer_fix(world: World, child: Entity, helper: Entity, activity: Activity, tube: Entity) -> Optional[Gear]:
    gear = GEAR[0] if activity.id == "tube" else None
    if gear is None:
        return None
    world.say(
        f"Then {helper.id} pointed to {gear.label} and said, \"Let's {gear.prep}, and the hall can stay calm and bright.\""
    )
    return gear


def accept_fix(world: World, child: Entity, helper: Entity, activity: Activity, tube: Entity, gear: Gear) -> None:
    child.meters["care"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["stubborn"] = 0
    tube.protected = True
    world.say(
        f"{child.id} nodded, tucked the tube into {gear.label}, and {gear.tail} with {helper.id} beside {child.id}."
    )
    world.say(
        f"By the end, the tube stayed whole, the mid-day hall stayed tidy, and the child learned the fair tale truth: "
        f"kind caution is a lantern in the dark."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="hulk"))
    tube = world.add(Entity(id="tube", type="tube", label="tube", phrase="a shiny tube", caretaker=helper.id, fragile=True))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    intro(world, child, helper, tube, activity)
    world.para()
    caution(world, child, helper, activity, tube)
    defy(world, child, activity)
    warn_burst(world, child, helper, activity, tube)
    world.para()
    gear = offer_fix(world, child, helper, activity, tube)
    if gear:
        accept_fix(world, child, helper, activity, tube, gear)
    world.facts.update(child=child, helper=helper, tube=tube, activity=activity, gear=gear, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    activity = _safe_fact(world, f, "activity")
    return [
        f'Write a cautionary fairy tale rhyme about {child.id} at school and a shiny tube.',
        f"Tell a school story where {helper.id} the hulk warns {child.id} not to {activity.rush}.",
        f'Write a gentle rhyme that includes the words "mid" and "tube" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who wanted to {activity.rush} at school?",
            answer=f"{child.id} wanted to {activity.rush} at school, even though it was a risky idea.",
        ),
        QAItem(
            question=f"Who warned {child.id} about the tube?",
            answer=f"{helper.id} the hulk gave the warning because {activity.risk}.",
        ),
        QAItem(
            question="What did the child do at the end?",
            answer="The child put the tube in a padded basket and carried it carefully instead of rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a school?",
            answer="A school is a place where children learn, read, practice, and share time with teachers and classmates.",
        ),
        QAItem(
            question="What does mid-day mean?",
            answer="Mid-day means the middle of the day, around noon, when the sun is high and the day feels bright.",
        ),
        QAItem(
            question="What is a tube?",
            answer="A tube is a long hollow shape, often made of paper, metal, glass, or plastic.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.fragile:
            bits.append("fragile=True")
        if e.protected:
            bits.append("protected=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="school", activity="tube", name="Mina", helper="Hulk", trait="curious"),
    StoryParams(place="school", activity="tube", name="Pip", helper="Hulk", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale school storyworld: cautionary rhyme with a tube and Hulk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    place = getattr(args, "place", None) or "school"
    activity = getattr(args, "activity", None) or "tube"
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper = getattr(args, "helper", None) or "Hulk"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if place != "school":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if activity != "tube":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, name=name, helper=helper, trait=trait)


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


ASP_RULES = r"""
school(school).
activity(tube).
helper(hulk).
risk(tube, crack).
protects(basket, tube).

valid_story(Place, Activity, Helper) :- school(Place), activity(Activity), helper(Helper).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("school", "school"),
        asp.fact("activity", "tube"),
        asp.fact("helper", "hulk"),
        asp.fact("risk", "tube", "crack"),
        asp.fact("protects", "basket", "tube"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("school", "tube", "hulk")}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    rng_base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
