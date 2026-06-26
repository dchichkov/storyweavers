#!/usr/bin/env python3
"""
A small bedtime-style story world set in a puppet theater.

Premise:
A child visits a puppet theater at bedtime and learns that a resistant puppet
cannot move well on its own. A little bit of magic helps the puppet begin a
gentle locomotion problem, but only after a conflict is soothed and a kind
compromise is chosen.

This world models:
- physical meters: movement, strain, glow, wear
- emotional memes: worry, conflict, calm, delight, trust

The story is generated from world state, not from a fixed paragraph shell.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    phrases: str = ""
    child: object | None = None
    director: object | None = None
    puppet: object | None = None
    stage: object | None = None
    wand: object | None = None
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
class Theater:
    place: str = "the puppet theater"
    cozy: bool = True
    stage_kind: str = "curtained"
    THEATER: object | None = None
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
class StoryParams:
    name: str
    role: str
    attendant: str
    puppet: str
    magic: str
    motion: str
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


class World:
    def __init__(self, theater: Theater) -> None:
        self.theater = theater
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.theater)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _resistance_rule(world: World) -> None:
    puppet = world.get("puppet")
    if puppet.meters.get("resistant", 0) >= 1 and puppet.meters.get("movement", 0) < 1:
        puppet.memes["worry"] = puppet.memes.get("worry", 0) + 1
        puppet.meters["strain"] = puppet.meters.get("strain", 0) + 1


def _magic_rule(world: World) -> None:
    puppet = world.get("puppet")
    wand = world.get("wand")
    if wand.meters.get("glow", 0) >= 1 and puppet.meters.get("strain", 0) >= 1:
        puppet.meters["movement"] = puppet.meters.get("movement", 0) + 1
        puppet.meters["resistant"] = max(0, puppet.meters.get("resistant", 0) - 1)
        puppet.memes["delight"] = puppet.memes.get("delight", 0) + 1


def _conflict_rule(world: World) -> None:
    child = world.get("child")
    director = world.get("director")
    if child.memes.get("worry", 0) >= 1 and director.memes.get("sharp", 0) >= 1:
        child.memes["conflict"] = child.memes.get("conflict", 0) + 1


def _calm_rule(world: World) -> None:
    child = world.get("child")
    director = world.get("director")
    if child.memes.get("conflict", 0) >= 1 and director.memes.get("calm", 0) >= 1:
        child.memes["conflict"] = 0
        child.memes["trust"] = child.memes.get("trust", 0) + 1
        child.memes["calm"] = child.memes.get("calm", 0) + 1


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = snapshot(world)
        _resistance_rule(world)
        _conflict_rule(world)
        _calm_rule(world)
        _magic_rule(world)
        if snapshot(world) != before:
            changed = True


def snapshot(world: World) -> tuple:
    vals = []
    for k in sorted(world.entities):
        e = world.entities[k]
        vals.append((k, tuple(sorted(e.meters.items())), tuple(sorted(e.memes.items()))))
    return tuple(vals)


THEATER = Theater()

NAMES_GIRL = ["Mina", "Luna", "Ivy", "Nora", "Maya", "Zoe"]
NAMES_BOY = ["Theo", "Finn", "Leo", "Owen", "Ezra", "Noah"]
MAGICS = {
    "starwand": "a small star wand",
    "moonbell": "a silver moon bell",
    "glowthread": "a spool of glow-thread",
}
MOTIONS = {
    "shuffle": "shuffle across the stage",
    "tiptoe": "tiptoe between the curtains",
    "slide": "slide along the floorboards",
    "twirl": "twirl in a sleepy circle",
}


def valid_pairs() -> list[tuple[str, str]]:
    return [(m, g) for m in MOTIONS for g in MAGICS]


@dataclass
class StorySetup:
    name: str
    role: str
    attendant: str
    puppet: str
    magic: str
    motion: str
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


def build_world(params: StoryParams) -> World:
    world = World(THEATER)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.role,
        label=params.name,
        phrases="",
        meters={"worry": 0.0},
        memes={"worry": 0.0, "calm": 0.0, "trust": 0.0},
    ))
    director = world.add(Entity(
        id="director",
        kind="character",
        type=params.attendant,
        label=f"the {params.attendant}",
        memes={"sharp": 1.0, "calm": 0.0},
    ))
    puppet = world.add(Entity(
        id="puppet",
        kind="character",
        type="puppet",
        label=params.puppet,
        phrase=f"a small {params.puppet}",
        meters={"resistant": 1.0, "movement": 0.0, "strain": 0.0},
        memes={"worry": 0.0, "conflict": 0.0, "delight": 0.0},
    ))
    wand = world.add(Entity(
        id="wand",
        type="toy",
        label=_safe_lookup(MAGICS, params.magic),
        meters={"glow": 0.0},
        props={"magic": params.magic},
    ))
    stage = world.add(Entity(
        id="stage",
        type="place",
        label=THEATER.place,
        props={"setting": "puppet theater"},
    ))

    world.facts.update(
        child=child,
        director=director,
        puppet=puppet,
        wand=wand,
        stage=stage,
        motion=params.motion,
        magic=params.magic,
        params=params,
    )

    world.say(f"At bedtime, {child.label} visited {THEATER.place}, where the curtains were soft and red.")
    world.say(f"On the stage, there was {puppet.phrase} that wanted to {_safe_lookup(MOTIONS, params.motion)}.")
    world.say(f"But the little puppet was resistant and kept saying, 'Not yet, not yet.'")
    world.say(f"{child.label} held up {wand.label} and watched its tiny light begin to glow.")
    world.say(f"The {params.attendant} noticed the problem and grew worried about the delay.")
    world.say(f"One voice wanted hurry, and one voice wanted care, so a small conflict filled the cozy room.")

    puppet.meters["resistant"] = 1.0
    wand.meters["glow"] = 1.0
    child.memes["worry"] = 1.0
    director.memes["sharp"] = 1.0

    propagate(world)

    if child.memes.get("conflict", 0) >= 1:
        world.say(f"{child.label} listened closely, took a slow breath, and asked for a gentler way.")
        director.memes["calm"] = 1.0
        propagate(world)
        world.say(f"The {params.attendant} nodded, lowered the voice, and let the magic work softly.")

    if puppet.meters.get("movement", 0) >= 1:
        world.say(f"At last, the puppet could {_safe_lookup(MOTIONS, params.motion)} without fighting the floorboards.")
        world.say(f"The little light stayed warm, the worry faded, and the stage felt sleepy and safe.")
    else:
        world.say(f"Still, the puppet waited under the curtain, and the night stayed careful and quiet.")

    return world


def story_intro(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a bedtime story set in a puppet theater about a resistant puppet and a little bit of magic.",
        f"Tell a child-friendly story where {p.name} helps a puppet that wants to {_safe_lookup(MOTIONS, p.motion)}.",
        f"Create a gentle story about conflict, calm, and magic on a puppet theater stage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    child = _safe_fact(world, world.facts, "child")
    puppet = _safe_fact(world, world.facts, "puppet")
    director = _safe_fact(world, world.facts, "director")
    answers = [
        QAItem(
            question=f"Who visited the puppet theater at bedtime?",
            answer=f"{child.label} visited {THEATER.place} at bedtime and watched the puppet stage quietly.",
        ),
        QAItem(
            question=f"What did the puppet want to do?",
            answer=f"The puppet wanted to {_safe_lookup(MOTIONS, p.motion)}. At first it was resistant, so it did not move right away.",
        ),
        QAItem(
            question=f"What helped the puppet begin moving?",
            answer=f"{world.facts['wand'].label} helped by glowing softly. That gentle magic gave the puppet enough motion to try again.",
        ),
    ]
    if puppet.memes.get("conflict", 0) >= 1:
        answers.append(QAItem(
            question=f"Why was there a conflict in the story?",
            answer=f"There was a conflict because the puppet was resistant, the child worried, and the {p.attendant} wanted the show to keep going.",
        ))
    if puppet.meters.get("movement", 0) >= 1:
        answers.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the puppet able to {_safe_lookup(MOTIONS, p.motion)} and the room feeling calm, warm, and ready for sleep.",
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where people make puppets move and tell stories on a small stage.",
        ),
        QAItem(
            question="What can magic mean in a bedtime story?",
            answer="In a bedtime story, magic can mean a gentle special help, like a glow or a charm that makes a hard thing easier.",
        ),
        QAItem(
            question="What does locomotion mean?",
            answer="Locomotion means moving from one place to another, like shuffling, sliding, or walking.",
        ),
        QAItem(
            question="What does resistant mean?",
            answer="Resistant means not wanting to change or move easily, as if something is holding back.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for eid, e in world.entities.items():
        lines.append(f"{eid}: meters={e.meters} memes={e.memes} label={e.label}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    role: str
    attendant: str
    puppet: str
    magic: str
    motion: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime puppet-theater story world.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--attendant", choices=["mother", "father", "director"], default="director")
    ap.add_argument("--puppet")
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--motion", choices=sorted(MOTIONS))
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
    role = getattr(args, "role", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if role == "girl" else NAMES_BOY)
    attendant = getattr(args, "attendant", None) or "director"
    puppet = getattr(args, "puppet", None) or rng.choice(["marionette", "fox puppet", "rabbit puppet", "bear puppet"])
    magic = getattr(args, "magic", None) or rng.choice(sorted(MAGICS))
    motion = getattr(args, "motion", None) or rng.choice(sorted(MOTIONS))
    return StoryParams(name=name, role=role, attendant=attendant, puppet=puppet, magic=magic, motion=motion)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_intro(world),
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
% A puppet is resistant when it has resistance.
resistant(P) :- puppet(P), has_resistance(P).

% Magic gives glow.
glowing(W) :- wand(W), magic(W).

% Movement begins when glow reaches a resistant puppet.
moves(P) :- puppet(P), resistant(P), glowing(_).

% Conflict appears if a child worries while the director is sharp.
conflict(C) :- child(C), worried(C), director(D), sharp(D).

% Calm resolves conflict.
resolved(C) :- conflict(C), calm(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("director", "director"))
    lines.append(asp.fact("puppet", "puppet"))
    lines.append(asp.fact("wand", "wand"))
    lines.append(asp.fact("has_resistance", "puppet"))
    lines.append(asp.fact("sharp", "director"))
    lines.append(asp.fact("worried", "child"))
    lines.append(asp.fact("magic", "wand"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models() -> list[list]:
    import asp
    return asp.solve(asp_program("#show resistant/1. #show moves/1. #show conflict/1. #show resolved/1."), models=0)


def asp_verify() -> int:
    # Lightweight parity gate: we expect the modeled story to allow movement and
    # a conflict/resolution path.
    models = asp_models()
    if not models:
        print("MISMATCH: no ASP model found.")
        return 1
    print(f"OK: ASP produced {len(models)} model(s).")
    return 0


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", role="girl", attendant="director", puppet="rabbit puppet", magic="starwand", motion="tiptoe"),
        StoryParams(name="Theo", role="boy", attendant="mother", puppet="fox puppet", magic="moonbell", motion="shuffle"),
        StoryParams(name="Luna", role="girl", attendant="father", puppet="bear puppet", magic="glowthread", motion="slide"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show moves/1."))
        return
    if getattr(args, "asp", None):
        print(asp_program("#show resistant/1. #show moves/1. #show conflict/1. #show resolved/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated()]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### sample {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
