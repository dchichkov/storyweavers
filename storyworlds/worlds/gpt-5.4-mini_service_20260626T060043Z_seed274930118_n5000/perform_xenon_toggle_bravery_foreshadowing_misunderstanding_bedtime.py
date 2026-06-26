#!/usr/bin/env python3
"""
A bedtime-story world about a small stage performance, a glowing xenon lamp,
and a brave child who untangles a misunderstanding before sleep.

Seed tale:
A child wants to perform a tiny bedtime show for a parent and a stuffed friend.
A new xenon nightlight has a toggle switch, but the child misunderstands which
way makes the room cozy and which way makes it too bright. With a little bravery,
they test the lamp, notice the foreshadowed shadow on the wall, and choose the
gentle setting so everyone can sleep happily.
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


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------


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
class Place:
    id: str
    label: str
    indoors: bool = True
    cozy: bool = True
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
class Act:
    id: str
    verb: str
    noun: str
    stage_prop: str
    turns: str
    foreshadow: str
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
class Lamp:
    id: str
    label: str
    glow: str
    strong_glow: str
    gentle_glow: str
    toggle_left: str
    toggle_right: str
    safe_setting: str
    risky_setting: str
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
    act: str
    lamp: str
    name: str
    parent: str
    stuffed_friend: str
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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    state: dict[str, str] = field(default_factory=dict)
    child: object | None = None
    friend: object | None = None
    nightlight: object | None = None
    parent: object | None = None
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


class World:
    def __init__(self, place: Place, act: Act, lamp: Lamp):
        self.place = place
        self.act = act
        self.lamp = lamp
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", indoors=True, cozy=True),
    "nursery": Place(id="nursery", label="the nursery", indoors=True, cozy=True),
    "attic_room": Place(id="attic_room", label="the little attic room", indoors=True, cozy=True),
}

ACTS = {
    "perform": Act(
        id="perform",
        verb="perform",
        noun="performance",
        stage_prop="pillow stage",
        turns="a tiny bedtime show",
        foreshadow="a tall shadow on the wall",
        tags={"perform", "show", "bedtime", "foreshadowing"},
    ),
    "story": Act(
        id="story",
        verb="tell",
        noun="story",
        stage_prop="blanket fort",
        turns="a sleepy story",
        foreshadow="a shadow that looked like a fox",
        tags={"bedtime", "foreshadowing"},
    ),
}

LAMPS = {
    "xenon": Lamp(
        id="xenon",
        label="xenon nightlight",
        glow="a cool white glow",
        strong_glow="a bright, shiny glare",
        gentle_glow="a soft moonlike glow",
        toggle_left="left",
        toggle_right="right",
        safe_setting="gentle",
        risky_setting="bright",
    ),
}

GENTLE_NAMES = ["Mina", "Leo", "Ari", "Nina", "Owen", "Ivy", "June", "Theo"]
STUFFED_FRIENDS = ["bear", "rabbit", "fox", "owl", "dog", "cat"]
PARENT_NAMES = ["mom", "dad", "grandma", "grandpa", "aunt"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    act = _safe_lookup(ACTS, params.act)
    lamp = _safe_lookup(LAMPS, params.lamp)
    world = World(place, act, lamp)

    child = world.add(Entity(id="child", kind="character", label=params.name))
    parent = world.add(Entity(id="parent", kind="character", label=params.parent))
    friend = world.add(Entity(id="friend", kind="stuffed", label=f"stuffed {params.stuffed_friend}"))
    nightlight = world.add(Entity(id="lamp", kind="object", label=lamp.label))
    nightlight.state["toggle"] = lamp.toggle_left
    nightlight.state["glow"] = lamp.gentle_glow

    child.memes.update({"curiosity": 1.0, "bravery": 0.0, "confusion": 0.0, "joy": 0.0})
    parent.memes.update({"care": 1.0, "worry": 0.0, "relief": 0.0})
    friend.meters.update({"shadow": 0.0})
    nightlight.meters.update({"brightness": 0.0})

    world.facts.update(
        child=child,
        parent=parent,
        friend=friend,
        lamp=nightlight,
    )
    return world


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def introduce(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    f = world.get("friend")
    world.say(
        f"{c.label} was a little child who loved quiet nights, soft blankets, and "
        f"the stuffed {f.label} tucked close beside the pillow."
    )
    world.say(
        f"Every bedtime, {c.label} liked to {world.act.verb} a tiny show for {p.label}, "
        f"because the little stage made sleep feel friendly."
    )


def foreshadow(world: World) -> None:
    c = world.get("child")
    lamp = world.get("lamp")
    world.say(
        f"That evening, a new {lamp.label} waited by the bed. Its toggle could make "
        f"{lamp.glow}, and {c.label} noticed {world.act.foreshadow} on the wall."
    )
    world.say(
        f"{c.label} thought the {lamp.label} would be easy to use, but the switch "
        f"looked tricky in the dim room."
    )


def misunderstanding(world: World) -> None:
    c = world.get("child")
    lamp = world.get("lamp")
    c.memes["confusion"] += 1.0
    world.say(
        f"When {c.label} reached for the toggle, {c.label} misunderstood which way "
        f"was gentle and which way was bright."
    )
    lamp.state["toggle"] = lamp.toggle_right
    lamp.state["glow"] = lamp.strong_glow
    lamp.meters["brightness"] = 1.0
    world.say(
        f"The lamp clicked to the wrong side, and the room filled with {lamp.strong_glow}."
    )


def bravery_turn(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    lamp = world.get("lamp")
    c.memes["bravery"] += 1.0
    p.memes["worry"] += 1.0
    world.say(
        f"{c.label} took a brave breath and said, 'I can fix it.'"
    )
    world.say(
        f"Instead of hiding, {c.label} looked at the switch again, noticed the little "
        f"marks near the toggle, and learned the brighter side was not the cozy side."
    )


def resolution(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    friend = world.get("friend")
    lamp = world.get("lamp")
    lamp.state["toggle"] = lamp.toggle_left
    lamp.state["glow"] = lamp.gentle_glow
    lamp.meters["brightness"] = 0.0
    c.memes["joy"] += 1.0
    p.memes["relief"] += 1.0
    world.say(
        f"{c.label} toggled the lamp back to the soft side, and the room sank into "
        f"{lamp.gentle_glow}."
    )
    world.say(
        f"The shadow on the wall grew small and sleepy. {c.label} finished the tiny "
        f"{world.act.noun}, hugged the stuffed {friend.label}, and climbed under the blanket."
    )
    world.say(
        f"{p.label} smiled, because the bedtime mistake had turned into a brave little lesson."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.say("")
    foreshadow(world)
    world.say("")
    misunderstanding(world)
    bravery_turn(world)
    world.say("")
    resolution(world)

    world.facts.update(
        place=_safe_lookup(PLACES, params.place),
        act=_safe_lookup(ACTS, params.act),
        lamp=_safe_lookup(LAMPS, params.lamp),
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    act = _safe_fact(world, f, "act")
    lamp = _safe_fact(world, f, "lamp")
    return [
        f'Write a bedtime story for a small child named {child.label} that includes the word "toggle".',
        f"Tell a gentle story where {child.label} tries to {act.verb} beside a {lamp.label} and learns from a misunderstanding.",
        f"Write a cozy story about bravery, foreshadowing, and a lamp switch in {f['place'].label}.",
        f"Create a bedtime tale where {parent.label} helps {child.label} choose the safe setting on a xenon light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    lamp = _safe_fact(world, f, "lamp")
    act = _safe_fact(world, f, "act")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {child.label} want to do at bedtime?",
            answer=f"{child.label} wanted to {act.verb} a tiny show for {parent.label} before sleep.",
        ),
        QAItem(
            question=f"What caused the misunderstanding with the lamp?",
            answer=f"{child.label} misunderstood which way the toggle made the {lamp.label} gentle, so the room became too bright at first.",
        ),
        QAItem(
            question=f"How did {child.label} show bravery?",
            answer=f"{child.label} showed bravery by taking another careful look at the toggle and fixing the lamp instead of giving up.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The {lamp.label} was switched back to its soft setting, the shadow grew small, and bedtime felt calm again in {place.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = _safe_fact(world, f, "act")
    lamp = _safe_fact(world, f, "lamp")
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about something important that will matter later.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or a little scary even when you feel nervous.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is happening.",
        ),
        QAItem(
            question=f"Why might a {lamp.label} have a toggle?",
            answer="A toggle lets you choose between different settings, like a brighter light or a softer one.",
        ),
        QAItem(
            question=f"Why is a bedtime {act.noun} often gentle?",
            answer="Bedtime stories are often gentle because they help a child feel safe, calm, and ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
act(A) :- act_fact(A).
lamp(L) :- lamp_fact(L).

gentle_toggle(L) :- lamp(L), safe_setting(L, gentle).
risky_toggle(L) :- lamp(L), risky_setting(L, bright).

misunderstanding(P, A, L) :- place(P), act(A), lamp(L).
brave_fix(P, A, L) :- misunderstanding(P, A, L), gentle_toggle(L).

#show gentle_toggle/1.
#show risky_toggle/1.
#show misunderstanding/3.
#show brave_fix/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.cozy:
            lines.append(asp.fact("cozy", pid))
    for aid, act in ACTS.items():
        lines.append(asp.fact("act_fact", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
    for lid, lamp in LAMPS.items():
        lines.append(asp.fact("lamp_fact", lid))
        lines.append(asp.fact("safe_setting", lid, lamp.safe_setting))
        lines.append(asp.fact("risky_setting", lid, lamp.risky_setting))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show misunderstanding/3.\n#show brave_fix/3.\n")
    model = asp.one_model(program)
    atoms = { (sym.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in sym.arguments))
              for sym in model }
    expected = {
        ("misunderstanding", ("bedroom", "perform", "xenon")),
        ("misunderstanding", ("nursery", "perform", "xenon")),
        ("misunderstanding", ("attic_room", "perform", "xenon")),
        ("misunderstanding", ("bedroom", "story", "xenon")),
        ("misunderstanding", ("nursery", "story", "xenon")),
        ("misunderstanding", ("attic_room", "story", "xenon")),
        ("brave_fix", ("bedroom", "perform", "xenon")),
        ("brave_fix", ("nursery", "perform", "xenon")),
        ("brave_fix", ("attic_room", "perform", "xenon")),
        ("brave_fix", ("bedroom", "story", "xenon")),
        ("brave_fix", ("nursery", "story", "xenon")),
        ("brave_fix", ("attic_room", "story", "xenon")),
    }
    if atoms != expected:
        print("ASP mismatch")
        print("expected:", sorted(expected))
        print("got:", sorted(atoms))
        return 1
    print("OK: ASP parity check passed.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a xenon lamp, a toggle, and a brave fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--stuffed-friend", choices=STUFFED_FRIENDS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    act = getattr(args, "act", None) or rng.choice(list(ACTS))
    lamp = getattr(args, "lamp", None) or "xenon"
    name = getattr(args, "name", None) or rng.choice(GENTLE_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    stuffed_friend = getattr(args, "stuffed_friend", None) or rng.choice(STUFFED_FRIENDS)
    return StoryParams(place=place, act=act, lamp=lamp, name=name, parent=parent, stuffed_friend=stuffed_friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k in {"child", "parent", "friend", "lamp"}:
                continue
            print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="bedroom", act="perform", lamp="xenon", name="Mina", parent="mom", stuffed_friend="bear"),
    StoryParams(place="nursery", act="story", lamp="xenon", name="Theo", parent="dad", stuffed_friend="rabbit"),
    StoryParams(place="attic_room", act="perform", lamp="xenon", name="Ivy", parent="grandma", stuffed_friend="owl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding/3.\n#show brave_fix/3.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show gentle_toggle/1.\n#show risky_toggle/1.\n#show misunderstanding/3.\n#show brave_fix/3.\n"))
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} in {p.place} with {p.act} and {p.lamp}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
