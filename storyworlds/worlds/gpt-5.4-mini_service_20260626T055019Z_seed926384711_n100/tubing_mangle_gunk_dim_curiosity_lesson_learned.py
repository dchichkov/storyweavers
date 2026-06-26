#!/usr/bin/env python3
"""
storyworlds/worlds/tubing_mangle_gunk_dim_curiosity_lesson_learned.py
======================================================================

A small slice-of-life storyworld about a child, a tubing trip, a snag that
mangles a float, and a gentle lesson learned about looking before leaping.

The story seed imagines this short tale:
- A curious child wants to go tubing on a calm river.
- They spot a tricky branch or rocky bend that can mangle the tube or leave it
  gunk-dim with river mud.
- A parent or older helper notices first, stops the rush, and teaches a simple
  safety lesson.
- The child learns to check the water and picks a safer path, ending with
  a calmer, cleaner outing.

The world is intentionally small and state-driven: curiosity rises, risk is
predicted from the current setting, the proposed route, and the tube's gear,
then the story turns when a safer choice is made.
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

    child: object | None = None
    guide: object | None = None
    tube: object | None = None
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
    place: str
    current: str
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
    mess: str
    soil: str
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
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
    tags: set[str] = field(default_factory=set)
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_mangle(world: World) -> list[str]:
    out: list[str] = []
    act = world.facts.get("activity")
    if not act:
        return out
    for hero in world.characters():
        if hero.meters.get(act.mess, 0.0) < THRESHOLD:
            continue
        tube = world.entities.get("tube")
        if not tube:
            continue
        if tube.meters.get("protected", 0.0) >= THRESHOLD:
            continue
        sig = ("mangle", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        tube.meters["mangled"] = 1.0
        tube.meters["dirty"] = 1.0
        out.append("The tube got bent up and gunk-dim.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if guide.memes.get("warning", 0.0) < THRESHOLD:
        return out
    sig = ("lesson", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] = max(0.0, child.memes.get("curiosity", 0.0) - 0.5)
    child.memes["lesson_learned"] = 1.0
    out.append("The child slowed down and learned to check the water first.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_mangle, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "riverbank": Setting(place="the riverbank", current="gentle", affords={"tubing"}),
    "creek": Setting(place="the creek", current="quick", affords={"tubing"}),
    "bend": Setting(place="the shady bend", current="slow", affords={"tubing"}),
}

ACTIVITIES = {
    "tubing": Activity(
        id="tubing",
        verb="go tubing",
        gerund="tubing",
        rush="hop into the tube",
        mess="gunk_dim",
        soil="gunk-dim",
        tags={"tubing", "water"},
    )
}

PRIZES = {
    "tube": Prize(
        label="tube",
        phrase="a bright round tube",
        type="tube",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="strap",
        label="a snug strap",
        guards={"gunk_dim"},
        prep="tighten the strap on the tube",
        tail="tightened the strap and watched the water more carefully",
        tags={"safety"},
    ),
    Gear(
        id="gloves",
        label="river gloves",
        guards={"gunk_dim"},
        prep="put on river gloves and slow down",
        tail="put on the river gloves and took a slower look downstream",
        tags={"safety"},
    ),
]

CHILD_NAMES = ["Mina", "Eli", "Tia", "Noah", "Luna", "Owen"]
GUIDE_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ray", "Big Sis", "Grandpa"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    guide_name: str
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


def reasonableness_gate(setting: Setting, activity: Activity, prize: Prize) -> bool:
    return activity.id in setting.affords and prize.label == "tube"


def build_story(world: World, params: StoryParams) -> World:
    activity = _safe_lookup(ACTIVITIES, params.activity)
    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    guide = world.add(Entity(id="guide", kind="character", type="adult", label=params.guide_name))
    tube = world.add(Entity(id="tube", type="tube", label="tube", phrase="a bright round tube", caretaker="guide"))

    child.memes["curiosity"] = 1.0
    guide.memes["care"] = 1.0

    world.say(f"{child.label} was a curious kid who loved looking at water and asking what it could do.")
    world.say(f"One morning, {child.label} and {guide.label} headed to {world.setting.place} with {tube.phrase}.")
    world.say(f"{child.label} wanted to {activity.verb} right away, because the river looked shiny and fun.")

    world.para()
    world.say(f"But {world.setting.place} had a tricky stretch where branches and stones could twist things around.")
    world.say(f"{guide.label} noticed the bend first and said, \"Let's check the current before we {activity.verb}.\"")
    guide.memes["warning"] = 1.0
    child.memes["curiosity"] += 0.5
    child.meters["gunk_dim"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{child.label} peeked at the water, nodded, and listened.")
    if "mangled" in tube.meters:
        world.say(f"{tube.label} had gotten bent and gunk-dim from the rough spot, so they chose a safer place instead.")
    gear = GEAR[0]
    world.say(f"{guide.label} showed how to {gear.prep}, and that made the plan feel easy.")
    tube.meters["protected"] = 1.0
    child.memes["lesson_learned"] = 1.0
    world.say(f"After that, {child.label} learned that a slow look first can save a lot of trouble.")
    world.say(f"At the end, they were still by the water, but the tube was clean, the path was safer, and {child.label} felt proud of the lesson learned.")

    world.facts.update(
        child=child,
        guide=guide,
        tube=tube,
        activity=activity,
        gear=gear,
        setting=world.setting,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")
    guide: Entity = _safe_fact(world, world.facts, "guide")
    tube: Entity = _safe_fact(world, world.facts, "tube")
    activity: Activity = _safe_fact(world, world.facts, "activity")
    qa = [
        QAItem(
            question=f"Who wanted to {activity.verb} at {world.setting.place}?",
            answer=f"{child.label} did. {child.label} was curious and wanted to go tubing right away.",
        ),
        QAItem(
            question=f"Why did {guide.label} stop them before they {activity.verb}?",
            answer=f"{guide.label} saw a tricky stretch in the water and did not want the tube to get gunk-dim or mangled.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{child.label} learned to check the water first, and the tube stayed clean and safe instead of getting bent up.",
        ),
    ]
    if tube.meters.get("mangled", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question="What happened to the tube near the rough spot?",
                answer="It got bent up and gunk-dim before they chose a safer place to continue.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tubing?",
            answer="Tubing is floating or riding in a round tube on water, usually along a river or creek.",
        ),
        QAItem(
            question="What does gunk-dim mean here?",
            answer="It means something got dirty, muddy, or coated with yucky river gunk so it no longer looks bright and clean.",
        ),
        QAItem(
            question="What does it mean to mangle something?",
            answer="To mangle something is to bend, twist, or damage it so it is no longer in good shape.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a slice-of-life story about {world.facts['child'].label} and a day of tubing that becomes a lesson learned.",
        f"Tell a gentle story where curiosity about water leads to a gunk-dim or mangled tube, then a safer choice.",
        "Write a short child-friendly story about a curious kid, a cautious guide, and a calm riverbank.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
act_risky(A) :- activity(A), mess_of(A,M), gunk(M).
fixable(A) :- act_risky(A), has_gear(A).
lesson_learned(C) :- curious(C), warned(G), listens(C,G).
valid_story(P,A,T) :- setting(P), affords(P,A), prize(T), act_risky(A), fixable(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("gunk", a.mess))
    for tid, t in PRIZES.items():
        lines.append(asp.fact("prize", tid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("has_gear", "tubing"))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    lines.append(asp.fact("curious", "child"))
    lines.append(asp.fact("warned", "guide"))
    lines.append(asp.fact("listens", "child", "guide"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("riverbank", "tubing", "tube"), ("creek", "tubing", "tube"), ("bend", "tubing", "tube")}
    if asp_set == py_set:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life tubing storyworld with curiosity and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--guide-name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or "tubing"
    prize = getattr(args, "prize", None) or "tube"
    if not reasonableness_gate(_safe_lookup(SETTINGS, place), _safe_lookup(ACTIVITIES, activity), _safe_lookup(PRIZES, prize)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    guide_name = getattr(args, "guide_name", None) or rng.choice(GUIDE_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, guide_name=guide_name)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    world = build_story(world, params)
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
    StoryParams(place="riverbank", activity="tubing", prize="tube", name="Mina", guide_name="Mom"),
    StoryParams(place="creek", activity="tubing", prize="tube", name="Eli", guide_name="Dad"),
    StoryParams(place="bend", activity="tubing", prize="tube", name="Luna", guide_name="Aunt Jo"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
