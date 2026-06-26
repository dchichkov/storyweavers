#!/usr/bin/env python3
"""
A standalone story world: a bedtime story with lame sound effects and gentle suspense.

Premise:
- A child is trying to fall asleep.
- The house makes weird little noises.
- The child feels suspense, then discovers the "monster sounds" are only harmless, ordinary things.
- The ending proves safety and calm through the world state.

This script is self-contained and follows the Storyworld contract.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Room:
    name: str
    quiet: bool
    makes_sounds: list[str] = field(default_factory=list)
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
class SoundEvent:
    id: str
    onomatopoeia: str
    source: str
    source_label: str
    suspense: float
    safe_explanation: str
    harmless: bool = True
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
class StoryParams:
    room: str
    sound: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    trait: str = ""
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        return clone


def _tick_suspense(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not child:
        return out
    if child.memes.get("suspense", 0.0) < THRESHOLD:
        return out
    if ("suspense", child.id) in world.fired:
        return out
    world.fired.add(("suspense", child.id))
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    out.append("The dark room felt extra quiet.")
    return out


def _resolve_sound(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not child:
        return out
    sound = world.facts.get("sound")
    if not sound:
        return out
    if child.memes.get("suspense", 0.0) < THRESHOLD:
        return out
    if ("resolve", sound.id) in world.fired:
        return out
    world.fired.add(("resolve", sound.id))
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["suspense"] = 0.0
    out.append(sound.safe_explanation)
    return out


RULES = [_tick_suspense, _resolve_sound]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ROOMS = {
    "bedroom": Room(name="the bedroom", quiet=True, makes_sounds=["creak", "tap", "swish"]),
    "hallway": Room(name="the hallway", quiet=True, makes_sounds=["creak", "tick", "thump"]),
    "nursery": Room(name="the nursery", quiet=True, makes_sounds=["hush", "tap", "whirr"]),
}

SOUNDS = {
    "floorboard": SoundEvent(
        id="floorboard",
        onomatopoeia="creak",
        source="the old floorboard",
        source_label="floorboard",
        suspense=1.0,
        safe_explanation="It was only the old floorboard saying a tiny creak as the house settled.",
    ),
    "window": SoundEvent(
        id="window",
        onomatopoeia="tap",
        source="the window shade",
        source_label="window shade",
        suspense=1.0,
        safe_explanation="It was only the window shade tapping softly at the glass.",
    ),
    "pipe": SoundEvent(
        id="pipe",
        onomatopoeia="thump",
        source="the warm pipe",
        source_label="pipe",
        suspense=1.2,
        safe_explanation="It was only the warm pipe making a small thump as it cooled down.",
    ),
    "toy": SoundEvent(
        id="toy",
        onomatopoeia="whirr",
        source="the wind-up toy",
        source_label="toy",
        suspense=1.1,
        safe_explanation="It was only the forgotten toy winding itself down with a tiny whirr.",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Eli", "Zoe", "Finn"]
TRAITS = ["sleepy", "brave", "curious", "gentle", "lively"]


def bedtime_start(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"{child.id} was a little {next(t for t in child.memes.get('traits', ['sleepy'])) if False else 'sleepy'} {child.type} who was tucked into bed.")
    world.say(f"{child.pronoun().capitalize()} liked bedtime stories, soft blankets, and the safe glow of the night light.")
    world.say(f"Before sleep, {child.id}'s {parent.pronoun('possessive')} voice said, 'Time to rest now.'")


def tell(world_room: Room, sound: SoundEvent, name: str = "Mia", gender: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(world_room)
    child = world.add(Entity(id=name, kind="character", type=gender, location=world_room.name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, location=world_room.name))

    child.memes["suspense"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["traits"] = [trait, "sleepy"]  # not rendered directly

    world.facts.update(child=child, parent=parent, sound=sound, room=world_room)

    world.say(f"It was bedtime in {world_room.name}.")
    world.say(f"{child.id} snuggled under the blanket and tried to be sleepy.")
    world.say(f"Then came a little sound: {sound.onomatopoeia}!")

    child.memes["suspense"] += sound.suspense
    propagate(world, narrate=True)

    world.para()
    world.say(f"{child.id} blinked and listened again.")
    world.say(f"The room was dark, and the tiny noise sounded a bit mysterious.")
    world.say(f"{child.id} whispered, 'What was that?'")
    child.memes["suspense"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{parent.id} smiled in the doorway and turned on the little lamp.")
    world.say(f"Together they looked around the room.")
    world.say(sound.safe_explanation)
    world.say(f"{child.id} laughed a small laugh, because the big scary sound was only a lame little bedtime noise after all.")
    child.memes["calm"] += 1.0
    child.memes["suspense"] = 0.0

    world.para()
    world.say(f"At last, {child.id} lay back down.")
    world.say(f"{child.id} listened to the quiet room, and the quiet room listened back.")
    world.say(f"The only sound left was a soft, sleepy {sound.onomatopoeia}, and then {child.id} drifted off to sleep.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sound = _safe_fact(world, f, "sound")
    return [
        f'Write a bedtime story for a small child where a suspicious "{sound.onomatopoeia}" turns out to be harmless.',
        f"Tell a gentle suspense story about {child.id} hearing a weird little sound at bedtime and feeling safe again.",
        f'Write a child-friendly story that includes the sound effect "{sound.onomatopoeia}" and ends with sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    sound = _safe_fact(world, f, "sound")
    room = _safe_fact(world, f, "room")
    return [
        QAItem(
            question=f"Why did {child.id} feel worried when the {sound.source_label} made a sound in {room.name}?",
            answer=f"{child.id} felt worried because the little {sound.onomatopoeia} sounded mysterious in the dark room, even though it was harmless.",
        ),
        QAItem(
            question=f"What did {parent.id} show {child.id} when they checked the noise together?",
            answer=f"{parent.id} showed {child.id} that it was only {sound.source}, and the sound was not dangerous at all.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"The story ended with {child.id} calm in bed, listening to the quiet room and falling asleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a gentle story told at night to help a child feel cozy, calm, and ready to sleep.",
        ),
        QAItem(
            question="Why can small sounds seem bigger at night?",
            answer="Small sounds can seem bigger at night because everything is quiet, so little noises are easier to notice.",
        ),
        QAItem(
            question="What does it mean when a sound is harmless?",
            answer="A harmless sound is one that is safe and cannot hurt you.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the worried, waiting feeling a story can create when someone wonders what will happen next.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:9}/{e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with lame sound effects and suspense.")
    ap.add_argument("--room", choices=ROOMS.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(r, s) for r in ROOMS for s in SOUNDS if s in _safe_lookup(ROOMS, r).makes_sounds or True]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(room=room, sound=sound, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(ROOMS, params.room), _safe_lookup(SOUNDS, params.sound), params.name, params.gender, params.parent, params.trait)
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
sound_source(S) :- sound(S).
suspense(E) :- hears(C,S), sound_source(S), worried(C).
safe(E) :- explains(P,S), sound_source(S).
resolved :- safe(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.quiet:
            lines.append(asp.fact("quiet", rid))
        for s in room.makes_sounds:
            lines.append(asp.fact("makes_sound", rid, s))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("onomatopoeia", sid, sound.onomatopoeia))
        lines.append(asp.fact("source", sid, sound.source_label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show sound/1."))
    if model is None:
        print("No ASP model.")
        return 1
    print("OK: ASP program parsed and solved.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show sound/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        for room in ROOMS:
            for sound in SOUNDS:
                params = StoryParams(room=room, sound=sound, name="Mia", gender="girl", parent="mother", trait="curious")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
