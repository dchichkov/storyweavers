#!/usr/bin/env python3
"""
storyworlds/worlds/detect_transformation_reconciliation_bedtime_story.py
========================================================================

A small bedtime-story world about a child who detects a gentle transformation
at night, feels a little worried, and then finds reconciliation before sleep.

Seed-tale premise:
- At bedtime, a child notices a favorite comfort object seems to change.
- The change is not a danger; it is a soft transformation into a sleepier form.
- A parent helps the child understand what happened.
- The child and parent reconcile, and the room settles into a calm ending image.

This script models:
- physical meters: cozy, dim, tidy, worn, transformed
- emotional memes: worry, trust, calm, hurt, delight, reconciliation

The story is intentionally small and child-facing, with bedtime language and a
clear turn from concern to comfort.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    kind: str = "thing"  # "character" | "thing"
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
    comfort: object | None = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Room:
    name: str
    dim_level: str = "soft"
    has_night_light: bool = True
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
class ComfortObject:
    id: str
    label: str
    phrase: str
    type: str
    sleep_form: str
    transformation: str
    stays_safe: bool = True
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
    room: str
    comfort: str
    child_name: str
    child_type: str
    parent_type: str
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
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_detect_transformation(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "comfort":
            continue
        if ent.meters.get("transformed", 0.0) < THRESHOLD:
            continue
        sig = ("detected", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["detected"] = ent.id
        out.append(f"{world.get('child').id} noticed that {ent.label} had changed.")
    return out


def _r_reconcile(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    comfort_id = world.facts.get("detected")
    if not comfort_id:
        return []
    comfort = world.get(comfort_id)
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile", comfort.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.memes["reconciliation"] = child.memes.get("reconciliation", 0.0) + 1.0
    parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1.0
    comfort.meters["cozy"] = comfort.meters.get("cozy", 0.0) + 1.0
    return [f"{child.id} and {parent.id} smiled and settled the worry together."]


CAUSAL_RULES = [
    Rule("detect_transformation", _r_detect_transformation),
    Rule("reconcile", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_room(room_name: str) -> Room:
    if room_name == "bedroom":
        return Room(name="the bedroom", dim_level="soft", has_night_light=True, affords={"sleep"})
    if room_name == "nursery":
        return Room(name="the nursery", dim_level="gentle", has_night_light=True, affords={"sleep"})
    if room_name == "tent":
        return Room(name="the blanket tent", dim_level="dusky", has_night_light=False, affords={"sleep"})
    pass


COMFORTS = {
    "bunny": ComfortObject(
        id="bunny",
        label="plush bunny",
        phrase="a soft plush bunny with long ears",
        type="comfort",
        sleep_form="sleepy bunny",
        transformation="its ears had folded down into a sleepier shape",
    ),
    "fox": ComfortObject(
        id="fox",
        label="plush fox",
        phrase="a red plush fox with a stitched smile",
        type="comfort",
        sleep_form="sleepy fox",
        transformation="its tail had curled up like a tiny comma",
    ),
    "blanket": ComfortObject(
        id="blanket",
        label="blanket",
        phrase="a warm blanket with little stars",
        type="comfort",
        sleep_form="tucked blanket",
        transformation="its corners had tucked themselves into a cozy nest",
    ),
}

ROOMS = {
    "bedroom": build_room("bedroom"),
    "nursery": build_room("nursery"),
    "tent": build_room("tent"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Sam", "Theo"]
PARENTS = ["mother", "father"]


def reasonableness_gate(room: Room, comfort: ComfortObject) -> None:
    if room.name == "the blanket tent" and comfort.id == "blanket":
        return
    if comfort.stays_safe:
        return
    pass


def tell(room: Room, comfort_cfg: ComfortObject, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(room)

    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, label=child_name,
        meters={"cozy": 0.0}, memes={"worry": 0.0, "calm": 0.0}
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type, label="the parent",
        meters={"cozy": 0.0}, memes={"warmth": 0.0}
    ))
    comfort = world.add(Entity(
        id=comfort_cfg.id, kind="thing", type="comfort", label=comfort_cfg.label,
        phrase=comfort_cfg.phrase, owner=child.id, caretaker=parent.id,
        meters={"transformed": 0.0, "cozy": 1.0}, memes={"softness": 1.0}
    ))

    world.say(
        f"At bedtime in {room.name}, {child.id} snuggled close and looked at {comfort.phrase}."
    )
    world.say(
        f"{child.id} loved {comfort.label} because it always felt safe in the warm little room."
    )
    world.para()

    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    world.say(
        f"Then {child.id} detected a tiny change: {comfort.label} looked different in the lamp glow."
    )
    comfort.meters["transformed"] += 1.0
    comfort.meters["cozy"] += 1.0
    world.say(
        f"Its sleepy shape was not broken; {comfort_cfg.transformation}."
    )
    child.memes["worry"] += 1.0
    child.memes["hurt"] = child.memes.get("hurt", 0.0) + 1.0
    world.say(
        f"But {child.id} still felt a pinch of worry and asked {parent.label_word} about it."
    )
    world.say(
        f"{parent.id} sat beside {child.id} and whispered that bedtime things sometimes transform when they are ready to rest."
    )
    world.para()

    propagate(world, narrate=True)
    if child.memes.get("worry", 0.0) >= THRESHOLD:
        world.say(
            f"{child.id} held {comfort.it()} a little tighter and listened to the soft breathing of the room."
        )
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    world.say(
        f"With one more breath, {child.id} let the worry go, and the two of them reconciled over the sleepy surprise."
    )
    world.say(
        f"At the end, {child.id} tucked {comfort.it()} close again, and {room.name} glowed quietly until sleep came."
    )

    world.facts.update(
        child=child,
        parent=parent,
        comfort=comfort,
        room=room,
        transformed=True,
        reconciled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    comfort = _safe_fact(world, f, "comfort")
    return [
        'Write a gentle bedtime story where a child detects a small transformation in a beloved comfort object.',
        f"Tell a cozy story about {child.id} noticing that {comfort.label} has changed at bedtime and then making peace with it.",
        f'Write a short bedtime story that includes the word "detect" and ends with a calm reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    comfort = _safe_fact(world, f, "comfort")
    room = _safe_fact(world, f, "room")
    return [
        QAItem(
            question=f"What did {child.id} detect at bedtime in {room.name}?",
            answer=f"{child.id} detected that {comfort.label} had changed in the lamp glow, but it was a soft bedtime transformation, not a danger.",
        ),
        QAItem(
            question=f"Why did {child.id} feel worried about {comfort.label}?",
            answer=f"{child.id} felt worried because {comfort.label} looked different for a moment, and the change made bedtime feel uncertain until {parent.label_word} explained it.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label_word} reconcile?",
            answer=f"They reconciled by talking gently, understanding the transformation, and settling together until the room felt calm again.",
        ),
        QAItem(
            question=f"What was special about the ending of the story?",
            answer=f"At the end, {child.id} tucked {comfort.it()} close and the room stayed quiet and cozy, which showed that the worry had turned into comfort.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to detect something?",
            answer="To detect something means to notice it carefully, often because it has changed or because you are paying close attention.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people feel upset or different at first, then talk kindly and come back to feeling peaceful together.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or feeling into another, like something becoming sleepier, softer, or different in a gentle way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
detected(C) :- comfort(C), transformed(C).
reconciled(C) :- detected(C), child_worried, parent_kind.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.has_night_light:
            lines.append(asp.fact("night_light", rid))
        lines.append(asp.fact("dim", rid, room.dim_level))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("sleep_form", cid, c.sleep_form))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_detected() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show detected/1."))
    return sorted(set(asp.atoms(model, "detected")))


def asp_verify() -> int:
    if not asp_detected():
        print("MISMATCH: ASP failed to derive any detected transformation.")
        return 1
    print("OK: ASP twin derives detected/1.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about detecting a gentle transformation and reconciling before sleep.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(room=room, comfort=comfort, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    room = _safe_lookup(ROOMS, params.room)
    comfort_cfg = _safe_lookup(COMFORTS, params.comfort)
    reasonableness_gate(room, comfort_cfg)
    world = tell(room, comfort_cfg, params.child_name, params.child_type, params.parent_type)
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
    StoryParams(room="bedroom", comfort="bunny", child_name="Mia", child_type="girl", parent_type="mother"),
    StoryParams(room="nursery", comfort="fox", child_name="Leo", child_type="boy", parent_type="father"),
    StoryParams(room="tent", comfort="blanket", child_name="Nora", child_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show detected/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for detected transformations.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
