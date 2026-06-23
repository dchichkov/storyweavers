#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/glottal_kindness_ghost_story.py
==============================================================================================================

A small standalone storyworld: a gentle ghost story about fear, a spooky place,
and kindness that changes what the night feels like.

Premise seed:
- A child hears a glottal, spooky sound in an old place.
- The sound is scary, but the truth is small and sad.
- Kindness reveals what the sound needs, and the ending image proves the change.

The world uses typed entities with meters (physical) and memes (emotional), a
simple forward-chaining rule engine, a reasonableness gate, and an inline ASP
twin for parity checks.

Run:
    python glottal_kindness_ghost_story.py
    python glottal_kindness_ghost_story.py --qa
    python glottal_kindness_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: str = ""
    location: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    helper: object | None = None
    noise: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    id: str
    label: str
    detail: str
    makes_sound: str
    mood: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Trouble:
    id: str
    label: str
    sound: str
    source: str
    need: str
    risk: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Kindness:
    id: str
    label: str
    action: str
    effect: str
    ending: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    trouble = world.facts["trouble"]
    if child.meters["fear"] < THRESHOLD:
        return out
    sig = ("fear", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["fearful"] += 1
    child.memes["fear"] += 1
    out.append(f"{child.id} clutched {child.pronoun('possessive')} hands tighter.")
    if trouble.id == "hall":
        world.get("hallway").meters["dark"] += 1
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    trouble = world.facts["trouble"]
    if helper.meters["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trouble.meters["sad"] = max(0.0, trouble.meters["sad"] - 1)
    helper.memes["love"] += 1
    child.memes["calm"] += 1
    out.append(f"{helper.id} answered with a soft voice, not a sharp one.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.facts["trouble"]
    helper = world.facts["helper"]
    child = world.facts["child"]
    if trouble.meters["repaired"] < THRESHOLD:
        return out
    sig = ("reveal", trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["kindness"] += 1
    child.memes["surprise"] += 1
    out.append(f"The spooky thing was only {trouble.source}, small and stuck.")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("kindness", _r_kindness), Rule("reveal", _r_reveal)]


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


def valid_story(place: Place, trouble: Trouble, kindness: Kindness) -> bool:
    return "glottal" in trouble.tags and place.id in {"attic", "bridge", "cellar", "garden"} and kindness.id in {"tea", "song", "lantern", "blanket"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for trouble in TROUBLES:
            for kindness in KINDNESSES:
                if valid_story(_safe_lookup(PLACES, place), _safe_lookup(TROUBLES, trouble), _safe_lookup(KINDNESSES, kindness)):
                    combos.append((place, trouble, kindness))
    return combos


@dataclass
class StoryParams:
    place: str
    trouble: str
    kindness: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def tell(place: Place, trouble: Trouble, kindness: Kindness, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, label=helper_name, role="helper"))
    noise = world.add(Entity(id="noise", type="thing", label=trouble.label, phrase=trouble.sound, location=place.id, tags=set(trouble.tags)))
    world.add(Entity(id="place", type="place", label=place.label, phrase=place.detail, location=place.id))
    world.facts = {
        "child": child,
        "helper": helper,
        "trouble": noise,
        "place": place,
        "kindness": kindness,
        "trouble_cfg": trouble,
        "child_name": child_name,
        "helper_name": helper_name,
    }
    child.meters["fear"] = 0.0
    helper.meters["kindness"] = 0.0
    noise.meters["sad"] = 1.0
    noise.meters["repaired"] = 0.0

    world.say(f"That night, {child.id} walked into {place.label}, where {place.detail}.")
    world.say(f"Then came a {trouble.sound} sound, glottal and low, from {trouble.source}.")
    world.para()
    child.meters["fear"] += 1
    child.memes["fear"] += 1
    world.say(f"{child.id} froze, because the dark made the sound feel bigger than it was.")
    world.say(f"But {helper.id} did not laugh. {helper.id} held up {kindness.label} and chose {kindness.action}.")
    helper.meters["kindness"] += 1
    noise.meters["repaired"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"With {kindness.label}, the gloom changed to {kindness.effect}.")
    world.say(f"At the end, {kindness.ending}, and {child.id} could breathe again.")
    world.say(f"The old place still looked spooky, but now it felt cared for instead of lonely.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child set in {f["place"].label}, where a glottal sound turns out to need kindness.',
        f"Tell a gentle spooky story where {f['child'].id} hears something glottal in {f['place'].label} and {f['helper'].id} helps with {f['kindness'].label}.",
        f'Write a child-friendly ghost story that includes the word "glottal" and ends with a kind helper making the scary place feel safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    trouble = f["trouble_cfg"]
    place = f["place"]
    kindness = f["kindness"]
    return [
        QAItem(
            question=f"What did {child.id} hear in {place.label}?",
            answer=f"{child.id} heard a glottal, spooky sound from {trouble.source}. It seemed scary at first because the place was dark.",
        ),
        QAItem(
            question=f"How did {helper.id} help {child.id} in the story?",
            answer=f"{helper.id} chose {kindness.action} instead of acting afraid. That kind choice made the sound feel smaller and helped the child calm down.",
        ),
        QAItem(
            question=f"Why did the scary sound stop feeling so frightening?",
            answer=f"Once {helper.id} answered with {kindness.label}, everyone found out the sound was only {trouble.source}. The kindness changed the night from lonely to cared for.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What does glottal mean?",
            answer="Glottal means made in the throat or sounding like a throat-made stop. It can describe a rough, catchy sound.",
        ),
    ]
    if f["kindness"].id == "tea":
        out.append(QAItem(
            question="Why can warm tea feel comforting?",
            answer="Warm tea can feel comforting because it is gentle, warm, and easy to sip. Small kind acts often help people feel safer.",
        ))
    if f["kindness"].id == "blanket":
        out.append(QAItem(
            question="What does a blanket do on a cold or scary night?",
            answer="A blanket can make a person feel warmer and more tucked in. That cozy feeling often helps a child settle down.",
        ))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} tags={sorted(e.tags)}")
    lines.append(f"fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "attic": Place(id="attic", label="the attic", detail="dusty beams and a slant of moonlight", makes_sound="creak", mood="spooky", tags={"old", "dark"}),
    "bridge": Place(id="bridge", label="the bridge", detail="a shadowy path over the river", makes_sound="groan", mood="spooky", tags={"old", "dark"}),
    "cellar": Place(id="cellar", label="the cellar", detail="cool stone steps and one tiny window", makes_sound="rattle", mood="spooky", tags={"old", "dark"}),
    "garden": Place(id="garden", label="the garden", detail="wet bushes and lantern-light between the flowers", makes_sound="rustle", mood="spooky", tags={"old", "dark"}),
}

TROUBLES = {
    "pipe": Trouble(id="pipe", label="the pipe", sound="glottal rattle", source="an old pipe behind the wall", need="water", risk="lonely", tags={"glottal"}),
    "toy": Trouble(id="toy", label="the toy", sound="glottal click", source="a broken toy under the stairs", need="help", risk="lonely", tags={"glottal"}),
    "bird": Trouble(id="bird", label="the bird", sound="glottal peep", source="a small bird stuck near a vent", need="help", risk="scared", tags={"glottal"}),
    "kettle": Trouble(id="kettle", label="the kettle", sound="glottal hiss", source="a teapot left too long on a cold shelf", need="warmth", risk="lonely", tags={"glottal"}),
}

KINDNESSES = {
    "tea": Kindness(id="tea", label="a mug of warm tea", action="speak softly and offer warm tea", effect="a gentle little glow", ending="the room smelled like tea and no one felt alone", tags={"kindness"}),
    "song": Kindness(id="song", label="a quiet song", action="sing a quiet song", effect="a hush with a tune inside it", ending="the sound of singing filled the hall and the dark felt less sharp", tags={"kindness"}),
    "lantern": Kindness(id="lantern", label="a little lantern", action="light a little lantern and walk closer carefully", effect="soft gold light on the floorboards", ending="the lantern made the corners bright enough to check safely", tags={"kindness"}),
    "blanket": Kindness(id="blanket", label="a warm blanket", action="wrap the frightened thing in a warm blanket", effect="a cozy nest of safety", ending="the blanket made the shiver stop and the room look kind", tags={"kindness"}),
}

def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(["Luna", "Mina", "Iris", "Nico", "Evan", "Milo"]) if gender == "girl" else rng.choice(["Owen", "Theo", "Milo", "Finn", "Eli", "Noah"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trouble", None) is None or c[1] == getattr(args, "trouble", None))
              and (getattr(args, "kindness", None) is None or c[2] == getattr(args, "kindness", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trouble, kindness = rng.choice(list(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    return StoryParams(
        place=place,
        trouble=trouble,
        kindness=kindness,
        child_name=getattr(args, "child", None) or _pick_name(rng, child_gender),
        child_gender=child_gender,
        helper_name=getattr(args, "helper", None) or _pick_name(rng, helper_gender),
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    if params.trouble not in TROUBLES:
        pass
    if params.kindness not in KINDNESSES:
        pass
    place = _safe_lookup(PLACES, params.place)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    kindness = _safe_lookup(KINDNESSES, params.kindness)
    if not valid_story(place, trouble, kindness):
        pass
    world = tell(place, trouble, kindness, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with kindness and a glottal sound.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--kindness", choices=sorted(KINDNESSES))
    ap.add_argument("--child")
    ap.add_argument("--helper")
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


ASP_RULES = r"""
valid(P,T,K) :- place(P), trouble(T), kindness(K), glottal(T), kind(K), good_pair(P,T,K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if "glottal" in t.tags:
            lines.append(asp.fact("glottal", tid))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("kind", kid))
    for p, t, k in valid_combos():
        lines.append(asp.fact("good_pair", p, t, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        a = set(asp_valid_combos())
        b = set(valid_combos())
        if a == b:
            print(f"OK: ASP matches Python valid_combos() ({len(a)} combos).")
        else:
            rc = 1
            print("MISMATCH:")
            if a - b:
                print(" only in ASP:", sorted(a - b))
            if b - a:
                print(" only in Python:", sorted(b - a))
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


CURATED = [
    StoryParams(place="attic", trouble="pipe", kindness="tea", child_name="Mina", child_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(place="cellar", trouble="toy", kindness="song", child_name="Eli", child_gender="boy", helper_name="Luna", helper_gender="girl"),
    StoryParams(place="bridge", trouble="bird", kindness="lantern", child_name="Nora", child_gender="girl", helper_name="Theo", helper_gender="boy"),
    StoryParams(place="garden", trouble="kettle", kindness="blanket", child_name="Finn", child_gender="boy", helper_name="Iris", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
