#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/alarm_kindness_conflict_cautionary_bedtime_story.py
==============================================================================================================================

A small bedtime-story world about an alarm, a gentle warning, a little conflict,
and a kind compromise.

Seed tale:
---
A child wants one more cozy moment at bedtime. An alarm clock rings, the parent
gives a cautionary warning about staying up too late, and the child feels torn.
With kindness, they choose a calmer path: one last hug, the light goes out, and
the alarm becomes part of a safe bedtime routine.

This script models that premise as a tiny simulation with physical meters and
emotional memes, then renders a complete child-facing story plus grounded Q&A.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    alarm: object | None = None
    blanket: object | None = None
    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Room:
    place: str = "the bedroom"
    quiet: bool = True
    bedtime_ready: bool = True
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
class Choice:
    id: str
    verb: str
    consequence: str
    concern: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters.get("sleepy", 0) < THRESHOLD:
            continue
        sig = ("sleepy", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.meters["heavy_eyes"] = child.meters.get("heavy_eyes", 0) + 1
        out.append(f"{child.pronoun('possessive').capitalize()} eyes felt heavy.")
    return out


def _r_conflict(world: World) -> list[str]:
    for child in world.characters():
        if child.memes.get("resist", 0) < THRESHOLD or child.memes.get("warning", 0) < THRESHOLD:
            continue
        sig = ("conflict", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["conflict"] = child.memes.get("conflict", 0) + 1
        return ["__conflict__"]
    return []


RULES = [
    _r_sleep,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    choice: str
    comfort: str
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


ROOMS = {
    "bedroom": Room(place="the bedroom", quiet=True, bedtime_ready=True, affords={"alarm", "one_more_story", "hug"}),
}

CHOICES = {
    "one_more_story": Choice(
        id="one_more_story",
        verb="read one more story",
        consequence="stayed up later",
        concern="too sleepy in the morning",
        keyword="story",
        tags={"bedtime", "cautionary"},
    ),
    "alarm": Choice(
        id="alarm",
        verb="listen to the alarm",
        consequence="went to bed on time",
        concern="miss bedtime",
        keyword="alarm",
        tags={"alarm", "cautionary"},
    ),
}

COMFORTS = [
    Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket",
        prep="wrap up in a soft blanket first",
        tail="wrapped up the blanket and climbed under the covers",
        helps={"alarm", "one_more_story"},
        covers=set(),
    ),
    Comfort(
        id="hug",
        label="a warm hug",
        phrase="a warm hug",
        prep="share one warm hug first",
        tail="shared a warm hug and snuggled down",
        helps={"alarm", "one_more_story"},
        covers=set(),
    ),
    Comfort(
        id="nightlight",
        label="a nightlight",
        phrase="a tiny nightlight",
        prep="keep the little nightlight on",
        tail="kept the little nightlight glowing softly",
        helps={"one_more_story"},
        covers=set(),
    ),
]

NAMES = ["Mia", "Nia", "Leo", "Eli", "Ava", "Milo", "Zoe", "Theo"]
TRAITS = ["sleepy", "curious", "gentle", "small", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for choice_id in room.affords:
            choice = _safe_lookup(CHOICES, choice_id)
            for comfort in COMFORTS:
                if choice_id in comfort.helps:
                    combos.append((room_id, choice_id, comfort.id))
    return combos


def _story_intro(child: Entity, parent: Entity, choice: Choice, comfort: Comfort) -> str:
    return (
        f"{child.id} was a little {child.type} who loved bedtime because it was "
        f"quiet and cozy. {child.pronoun().capitalize()} also loved {choice.keyword} moments, "
        f"and {child.pronoun('possessive')} {parent.label or 'parent'} always tried to be kind."
    )


def _warn(world: World, parent: Entity, child: Entity, choice: Choice) -> None:
    child.memes["warning"] = child.memes.get("warning", 0) + 1
    world.say(
        f'"If we {choice.verb.lower()}, you may feel {choice.consequence}," '
        f"{parent.pronoun('possessive')} {parent.label or 'parent'} said softly. "
        f'"It is a little {choice.concern} to stay up too long."'
    )


def _resist(world: World, child: Entity, choice: Choice) -> None:
    child.memes["resist"] = child.memes.get("resist", 0) + 1
    child.meters["restless"] = child.meters.get("restless", 0) + 1
    world.say(f"{child.id} wanted to {choice.verb}, but the cozy bed felt hard to leave.")


def _offer_comfort(world: World, parent: Entity, child: Entity, comfort: Comfort, choice: Choice) -> None:
    world.say(
        f"Then {parent.pronoun('possessive')} {parent.label or 'parent'} smiled kindly and said, "
        f'"How about we {comfort.prep} and still {choice.verb} in our own gentle way?"'
    )
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1


def _accept(world: World, child: Entity, parent: Entity, comfort: Comfort, choice: Choice) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["conflict"] = 0.0
    child.meters["restless"] = max(0.0, child.meters.get("restless", 0) - 1)
    world.say(
        f"{child.id}'s face softened. {child.pronoun().capitalize()} nodded, held {child.pronoun('possessive')} "
        f"{parent.label or 'parent'}'s hand, and said, 'Okay.'"
    )
    world.say(
        f"They {comfort.tail}, and the alarm became a kind reminder instead of a worry. "
        f"In the end, {child.id} {choice.consequence}, and the room stayed calm and warm."
    )


def tell(room: Room, choice: Choice, comfort: Comfort, child_name: str = "Mia", child_type: str = "girl",
         parent_type: str = "mother", trait: Optional[str] = None) -> World:
    world = World(room)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        meters={"sleepy": 1.0},
        memes={"kindness": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
        memes={"kindness": 1.0},
    ))
    alarm = world.add(Entity(
        id="alarm",
        type="alarm_clock",
        label="alarm clock",
        phrase="a little alarm clock",
        protective=False,
    ))
    blanket = world.add(Entity(
        id=comfort.id,
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
        protective=True,
    ))
    world.facts.update(child=child, parent=parent, alarm=alarm, comfort=blanket, choice=choice, room=room)

    world.say(_story_intro(child, parent, choice, comfort))
    world.say(
        f"One quiet night, the alarm clock on the dresser gave a small ring, and {child.id} looked up."
    )
    world.para()
    _warn(world, parent, child, choice)
    _resist(world, child, choice)
    propagate(world, narrate=True)

    world.para()
    _offer_comfort(world, parent, child, comfort, choice)
    _accept(world, child, parent, comfort, choice)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        if room.quiet:
            lines.append(asp.fact("quiet", room_id))
        if room.bedtime_ready:
            lines.append(asp.fact("bedtime_ready", room_id))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", room_id, a))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("concern", cid, c.concern.replace(" ", "_")))
        for t in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, t))
    for cm in COMFORTS:
        lines.append(asp.fact("comfort", cm.id))
        for a in sorted(cm.helps):
            lines.append(asp.fact("helps", cm.id, a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Room, Choice, Comfort) :- affords(Room, Choice), choice(Choice), comfort(Comfort), helps(Comfort, Choice).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    choice = _safe_fact(world, f, "choice")
    return [
        f'Write a bedtime story for a small child that includes an alarm clock and a gentle compromise.',
        f"Tell a calm story where {child.id} wants to {choice.verb.lower()} but a parent uses kindness and caution.",
        f'Write a short bedtime story with the word "alarm" and an ending that feels safe and cozy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    choice: Choice = _safe_fact(world, f, "choice")
    comfort: Entity = _safe_fact(world, f, "comfort")
    return [
        QAItem(
            question=f"Why did {child.id} feel torn when the alarm clock rang?",
            answer=(
                f"{child.id} wanted to {choice.verb.lower()}, but {parent.pronoun('possessive')} "
                f"{parent.label} worried that staying up too long would leave {child.pronoun('object')} "
                f"{choice.concern}."
            ),
        ),
        QAItem(
            question=f"What kind thing did {parent.pronoun('possessive')} {parent.label} offer to help?",
            answer=(
                f"{parent.pronoun('possessive').capitalize()} {parent.label} offered {comfort.phrase}, "
                f"so bedtime could stay calm and kind."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story for {child.id}?",
            answer=(
                f"{child.id} felt calmer, chose the gentle bedtime path, and the alarm became a friendly reminder "
                f"instead of a worry."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alarm clock for?",
            answer="An alarm clock is used to ring at a certain time so people can wake up or remember a routine.",
        ),
        QAItem(
            question="Why can staying up too late be hard?",
            answer="Staying up too late can make a child tired in the morning and less ready for the day.",
        ),
        QAItem(
            question="Why is kindness helpful at bedtime?",
            answer="Kindness helps everyone feel safe, calm, and loved, which makes it easier to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(child_name="Mia", child_type="girl", parent_type="mother", choice="one_more_story", comfort="blanket"),
    StoryParams(child_name="Leo", child_type="boy", parent_type="father", choice="alarm", comfort="hug"),
]


def explain_rejection(choice_id: str, comfort_id: str) -> str:
    choice = _safe_lookup(CHOICES, choice_id)
    return f"(No story: nothing in this bedtime world makes {comfort_id} a kind fix for {choice.verb.lower()}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with alarm, kindness, conflict, and caution.")
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--comfort", choices=[c.id for c in COMFORTS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "choice", None) and getattr(args, "comfort", None):
        if (getattr(args, "choice", None), getattr(args, "comfort", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "choice", None) is None or c[1] == getattr(args, "choice", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    _, choice, comfort = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(child_name=name, child_type=gender, parent_type=parent, choice=choice, comfort=comfort, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS["bedroom"], _safe_lookup(CHOICES, params.choice), next(c for c in COMFORTS if c.id == params.comfort),
                 child_name=params.child_name, child_type=params.child_type, parent_type=params.parent_type)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
