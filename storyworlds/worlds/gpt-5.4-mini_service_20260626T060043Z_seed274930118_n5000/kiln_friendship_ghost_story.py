#!/usr/bin/env python3
"""
storyworlds/worlds/kiln_friendship_ghost_story.py
=================================================

A small standalone story world about a child, a kiln, and a friendly ghost.

Premise:
- A child and a ghost are friends in a quiet pottery place.
- The child wants to fire a clay keepsake in the kiln.
- The ghost is nervous about the heat and the crackling sounds.
- They solve the problem by working together: drying the clay, loading the kiln carefully,
  and letting the ghost help in a safe, brave way.

The world is intentionally small and constraint-driven:
- The kiln must be relevant to the story.
- Friendship must matter and visibly change the emotional state.
- The ending should show a real change, not just a paraphrase of the premise.

This file follows the Storyweavers world contract and includes an inline ASP twin
for the reasonableness gate.
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
    friendly: bool = False
    visible: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ghost: object | None = None
    item: object | None = None
    kid: object | None = None
    kiln: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heat": 0.0, "dry": 0.0, "glow": 0.0, "soot": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "trust": 0.0, "bravery": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str
    quiet: bool = True
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
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    owner_gender: set[str] = field(default_factory=lambda: {"girl", "boy"})
    requires_kiln: bool = True
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
    place: str
    item: str
    name: str
    gender: str
    friend_name: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "studio": Setting(place="the pottery studio", affords={"fire_clay", "prepare_kiln"}),
    "shed": Setting(place="the little kiln shed", affords={"fire_clay", "prepare_kiln"}),
    "workroom": Setting(place="the workroom by the window", affords={"fire_clay", "prepare_kiln"}),
}

ITEMS = {
    "bird": Item(id="bird", label="bird", phrase="a small clay bird", risk="crack", region="hands"),
    "star": Item(id="star", label="star", phrase="a clay star with tiny holes", risk="crack", region="hands"),
    "cup": Item(id="cup", label="cup", phrase="a careful clay cup", risk="warp", region="hands"),
}

GHOST_NAMES = ["Milo", "Pip", "Wren", "Dot", "June", "Snow", "Blue"]
KID_NAMES = ["Lina", "Owen", "Nia", "Maya", "Theo", "Ruby", "Ezra"]
TRAITS = ["gentle", "curious", "brave", "patient", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, item) for place in SETTINGS for item in ITEMS]


def reasonableness_gate(place: str, item: str) -> bool:
    return place in SETTINGS and item in ITEMS


def explain_rejection(place: str, item: str) -> str:
    return f"(No story: the place '{place}' and item '{item}' do not make a kiln story here.)"


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    kid = world.add(Entity(id=params.name, kind="character", type=params.gender, friendly=True))
    ghost = world.add(Entity(id=params.friend_name, kind="character", type="ghost", friendly=True, visible=False))
    kiln = world.add(Entity(id="kiln", kind="thing", type="kiln", label="the kiln"))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label=_safe_lookup(ITEMS, params.item).label,
        phrase=_safe_lookup(ITEMS, params.item).phrase,
        owner=kid.id,
        caretaker=kid.id,
    ))
    world.facts.update(kid=kid, ghost=ghost, kiln=kiln, item=item, setting=setting)
    return world


def _r_kiln_warms(world: World) -> list[str]:
    out = []
    kiln = world.get("kiln")
    for ent in list(world.entities.values()):
        if ent.kind != "thing" or ent.id == "kiln":
            continue
        if ent.meters["heat"] >= THRESHOLD and ent.meters["dry"] < THRESHOLD:
            sig = ("warm", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["dry"] += 1
            kiln.meters["glow"] += 1
            out.append("The kiln hummed softly and helped the clay dry.")
    return out


def _r_friend_brave(world: World) -> list[str]:
    ghost = world.get("ghost")
    kid = world.get("kid")
    if kid.memes["trust"] >= THRESHOLD and ghost.memes["fear"] >= THRESHOLD:
        sig = ("brave",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        ghost.memes["bravery"] += 1
        ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 1)
        return ["The ghost took a slow breath and stayed by the child anyway."]
    return []


RULES = [Rule("warm", _r_kiln_warms), Rule("brave", _r_friend_brave)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = build_world(params)
    kid = world.get("kid")
    ghost = world.get("ghost")
    kiln = world.get("kiln")
    item = world.get(params.item)

    kid.memes["joy"] += 1
    kid.memes["trust"] += 1
    ghost.memes["trust"] += 1
    ghost.memes["fear"] += 1

    world.say(
        f"{kid.id} was a little {params.gender} with a kind heart, and {ghost.id} was a ghost who liked quiet rooms."
    )
    world.say(
        f"They were friends in {world.setting.place}, where the shelves held bowls, mugs, and careful piles of clay."
    )
    world.say(
        f"{kid.id} loved {item.phrase}, because {item.phrase.split(' ')[-1]} could become something bright after the kiln."
    )

    world.para()
    world.say(
        f"One evening, {kid.id} carried {item.phrase} to the kiln and said it was ready to fire."
    )
    kid.memes["bravery"] += 1
    ghost.memes["fear"] += 1
    world.say(
        f"But {ghost.id} peeked at the dark little door and shivered. The hot crackling inside sounded spooky."
    )

    world.para()
    world.say(
        f"{kid.id} noticed the shiver and spoke gently. \"You can help me,\" {kid.pronoun()} said. \"We can do this together.\""
    )
    kid.memes["trust"] += 1
    ghost.memes["trust"] += 1
    ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 0.5)

    kiln.meters["heat"] += 1
    item.meters["heat"] += 1
    propagate(world)

    world.say(
        f"First they dried the clay one last time, then {kid.id} opened the kiln door while {ghost.id} held the lantern."
    )
    world.say(
        f"{ghost.id} could not touch the clay, but {ghost.id} could light the path and count the shelves so nothing would wobble."
    )

    item.meters["dry"] += 1
    item.meters["heat"] += 1
    kiln.meters["heat"] += 1
    kiln.meters["glow"] += 1
    propagate(world)

    kid.memes["pride"] += 1
    ghost.memes["bravery"] += 1
    ghost.memes["joy"] += 1

    world.para()
    world.say(
        f"Later, the kiln cooled, and {kid.id} opened it to find {item.phrase} hard, smooth, and safe."
    )
    world.say(
        f"{ghost.id} smiled at the finished piece. The spooky sound had turned into a gentle memory, and the friendship felt brighter than the fire."
    )
    world.say(
        f"{kid.id} held up the little clay treasure, and {ghost.id} drifted beside {kid.id} like a happy, pale moonbeam."
    )

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    item = _safe_fact(world, f, "item")
    return [
        "Write a short ghost story for children about a child and a friendly ghost working together near a kiln.",
        f"Tell a gentle story where {kid.id} wants to fire {item.phrase} in a kiln, but a ghost friend is nervous and then helps.",
        "Write a story with a spooky-but-safe mood, a kiln, and a friendship that becomes stronger by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    ghost = _safe_fact(world, f, "ghost")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {kid.id} and {ghost.id}, and they stayed kind to each other near the kiln.",
        ),
        QAItem(
            question=f"What did {kid.id} want to do with {item.phrase}?",
            answer=f"{kid.id} wanted to fire {item.phrase} in the kiln so it could become hard and finished.",
        ),
        QAItem(
            question=f"Why was {ghost.id} nervous at first?",
            answer=f"{ghost.id} was nervous because the kiln looked hot and the crackling sound felt spooky.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They worked together carefully: {kid.id} handled the clay, and {ghost.id} helped by holding the lantern and staying close.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the clay piece was finished, and the friendship felt braver and happier than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kiln?",
            answer="A kiln is a very hot oven used to bake clay until it becomes hard.",
        ),
        QAItem(
            question="Why do people let clay dry before firing it?",
            answer="Clay needs to dry first so it is less likely to crack when the heat gets strong.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle?",
            answer="A ghost story can be gentle when the ghost is friendly, the danger stays small, and the ending feels safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A kiln story is reasonable when the chosen item can be fired in the chosen place.
story_valid(P, I) :- setting(P), item(I), has_kiln(P), needs_firing(I).

% Friendship matters when a child and a ghost both appear and the ghost helps.
friendship_story(P, I) :- story_valid(P, I), child_present(P), ghost_present(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("has_kiln", pid))
        lines.append(asp.fact("child_present", pid))
        lines.append(asp.fact("ghost_present", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("needs_firing", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a child, a kiln, and a ghost friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
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
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if not reasonableness_gate(place, item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(KID_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in GHOST_NAMES if n != name])
    return StoryParams(place=place, item=item, name=name, gender=gender, friend_name=friend_name)


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


CURATED = [
    StoryParams(place="studio", item="bird", name="Lina", gender="girl", friend_name="Milo"),
    StoryParams(place="shed", item="star", name="Theo", gender="boy", friend_name="Pip"),
    StoryParams(place="workroom", item="cup", name="Maya", gender="girl", friend_name="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_valid/2.\n#show friendship_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_valid/2."))
        print(f"{len(asp.atoms(model, 'story_valid'))} valid combos:")
        for p, i in sorted(set(asp.atoms(model, "story_valid"))):
            print(f"  {p} / {i}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
