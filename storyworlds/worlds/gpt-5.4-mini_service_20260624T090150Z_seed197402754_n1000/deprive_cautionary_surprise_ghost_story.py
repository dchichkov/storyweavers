#!/usr/bin/env python3
"""
storyworlds/worlds/deprive_cautionary_surprise_ghost_story.py
=============================================================

A small ghost-story world with a cautionary turn and a surprise ending.

Seed tale sketch:
A curious child follows a cold glow into an old house at night. Inside, a
watchful ghost warns that taking the glow away would deprive the tiny mice of
their path home. The child expects a scare, but the surprise is that the ghost
is guarding a lost creature, not haunting the room. In the end, the child helps
return the light and leaves the house feeling brave, careful, and kind.

World model:
- Physical meters track light, cold, rustle, and carried objects.
- Emotional memes track fear, caution, relief, and trust.
- The story is driven by state changes: the ghost's warning, the child's
  temptation, the danger of deprivation, and a surprising act of help.

This script follows the Storyweavers contract:
- standalone stdlib storyworld
- eager results import
- lazy ASP import in ASP helpers only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify compares the Python reasonableness gate to the inline ASP twin
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    visible: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    obj: object | None = None
    def __post_init__(self) -> None:
        for k in ["light", "cold", "rustle", "weight", "wetness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "caution", "relief", "trust", "surprise"]:
            self.memes.setdefault(k, 0.0)

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
    dark: bool = True
    affordance: str = "haunting"
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    glow: str
    at_risk: str
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
class GhostDef:
    id: str
    label: str
    glow: str
    warning: str
    surprise: str
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
        self.misplaced_glow: bool = False
        self.revealed_surprise: bool = False

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
        clone.fired = set(self.fired)
        clone.misplaced_glow = self.misplaced_glow
        clone.revealed_surprise = self.revealed_surprise
        return clone


SETTINGS = {
    "old_house": Setting(place="the old house", dark=True, affordance="haunting"),
    "attic": Setting(place="the attic", dark=True, affordance="whispering"),
    "hallway": Setting(place="the hallway", dark=True, affordance="glowing"),
}

OBJECTS = {
    "lantern": ObjectDef(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        glow="warm",
        at_risk="lost and dim",
    ),
    "candle": ObjectDef(
        id="candle",
        label="candle",
        phrase="a small white candle",
        glow="soft",
        at_risk="melted away",
    ),
    "ball": ObjectDef(
        id="ball",
        label="ball",
        phrase="a bright red ball",
        glow="cheerful",
        at_risk="rolled into the dark",
    ),
}

GHOSTS = {
    "moth_ghost": GhostDef(
        id="moth_ghost",
        label="Mara",
        glow="pale",
        warning="If you take the light, the tiny mice will lose their way home.",
        surprise="I was not haunting the room. I was guiding a lost mouse family.",
    ),
    "bell_ghost": GhostDef(
        id="bell_ghost",
        label="Bram",
        glow="silver",
        warning="If you carry it away, the dark corner will swallow the path.",
        surprise="I was hiding a kitten behind the old crate so it would not be frightened.",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Theo"]
TRAITS = ["curious", "careful", "brave", "quiet", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    object: str
    ghost: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for obj in OBJECTS:
            for ghost in GHOSTS:
                combos.append((setting, obj, ghost))
    return combos


def select_reasonable_combo() -> list[tuple[str, str, str]]:
    # All combos are reasonable in this small domain.
    return valid_combos()


def explain_rejection(*_args) -> str:
    return "(No story: this ghost tale has no invalid object or setting combinations.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_deprive(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    obj = world.get("object")
    ghost = world.get("ghost")
    if child.meters["light"] >= THRESHOLD and obj.carried_by == child.id:
        sig = ("deprive",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.memes = getattr(world, "memes", {})
        child.memes["caution"] += 1
        ghost.memes["fear"] += 1
        world.misplaced_glow = True
        out.append(f"{ghost.label} stepped closer, worried the little light would be deprived.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if world.misplaced_glow and not world.revealed_surprise:
        sig = ("surprise",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.revealed_surprise = True
        child.memes["surprise"] += 1
        child.memes["trust"] += 1
        ghost.memes["relief"] += 1
        out.append("The child blinked. The ghost was not angry at all.")
    return out


CAUSAL_RULES = [
    Rule("deprive", _r_deprive),
    Rule("surprise", _r_surprise),
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


def reasonableness_gate(setting: Setting, obj: ObjectDef, ghost: GhostDef) -> bool:
    return bool(setting and obj and ghost)


def predict_misplacement(world: World, child: Entity, obj: Entity) -> bool:
    sim = world.copy()
    sim.get("child").meters["light"] += 1
    sim.get("object").carried_by = "child"
    propagate(sim, narrate=False)
    return sim.misplaced_glow


def build_world(setting: Setting, obj_def: ObjectDef, ghost_def: GhostDef,
                child_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="boy", label=child_name, traits=[trait, "little"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_def.label, visible=True))
    obj = world.add(Entity(
        id="object", kind="thing", type=obj_def.label, label=obj_def.label, phrase=obj_def.phrase,
        carried_by=child.id, owner=ghost.id, plural=obj_def.plural
    ))

    child.meters["light"] = 1.0
    child.memes["curiosity"] += 1
    ghost.meters["light"] = 0.4
    ghost.memes["caution"] += 1
    obj.meters["light"] = 1.0

    world.say(f"{child_name} was a {trait} child who wandered into {setting.place} after sunset.")
    world.say(f"In the dark, {child_name} spotted {obj_def.phrase} glowing on a shelf.")
    world.say(f"'{ghost_def.warning}' said {ghost_def.label}, his voice thin as paper.")
    world.para()

    world.say(f"{child_name} reached for {obj_def.phrase} anyway, because the glow looked warm and safe.")
    if predict_misplacement(world, child, obj):
        propagate(world, narrate=False)
        world.say(f"But the room went colder, and {ghost_def.label} looked more frightened than scary.")
        world.say(f"'{ghost_def.warning}'")
        world.para()
        world.say(f"{child_name} froze. The surprise was that the ghost was trying to protect something small.")
        world.say(f"Behind the crate, {ghost_def.surprise}")
        child.memes["caution"] += 1
        child.memes["trust"] += 1
        ghost.memes["relief"] += 1
        obj.carried_by = None
        world.say(f"{child_name} put {obj_def.phrase} back, so the light could help the little ones find their way.")
        world.say(f"The ghost smiled, and the room felt less haunted and more like a cozy path home.")
    else:
        world.say(f"{child_name} carried the light carefully, and nothing bad happened.")
    world.facts.update(child=child, ghost=ghost, obj=obj, ghost_def=ghost_def, obj_def=obj_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about {f["child"].label} finding {f["obj_def"].phrase} in {world.setting.place}.',
        f"Tell a cautionary story where taking the glow would deprive someone of help, but the surprise is that the ghost is kind.",
        f'Write a gentle haunted-house story that includes the word "deprive" and ends with the light being put back.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    obj = _safe_fact(world, world.facts, "obj")
    obj_def = _safe_fact(world, world.facts, "obj_def")
    qs = [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {child.label}, a {child.traits[0]} child who went into {world.setting.place} and met {ghost.label}.",
        ),
        QAItem(
            question=f"What glowing thing did {child.label} want to take?",
            answer=f"{child.label} wanted to take {obj_def.phrase}, which was glowing in the dark.",
        ),
        QAItem(
            question=f"Why did the ghost warn {child.label} about the light?",
            answer=f"The ghost warned {child.label} because taking it away would deprive the tiny mice of their path home.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {ghost.label} was not trying to scare {child.label}; {world.facts['ghost_def'].surprise}",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people use a lantern in the dark?",
            answer="People use a lantern in the dark because its light helps them see where they are going.",
        ),
        QAItem(
            question="What does deprive mean?",
            answer="To deprive someone of something means to keep them from having it when they need it.",
        ),
        QAItem(
            question="Why do ghosts in stories sometimes seem scary at first?",
            answer="Ghosts in stories can seem scary at first because they appear in dark places and speak in spooky ways.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  misplaced_glow: {world.misplaced_glow}")
    lines.append(f"  revealed_surprise: {world.revealed_surprise}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="old_house", object="lantern", ghost="moth_ghost", name="Mia", trait="curious"),
    StoryParams(setting="attic", object="candle", ghost="bell_ghost", name="Leo", trait="careful"),
    StoryParams(setting="hallway", object="ball", ghost="moth_ghost", name="Nora", trait="brave"),
]


ASP_RULES = r"""
% A story is reasonable whenever the registry provides all parts.
reasonable(S,O,G) :- setting(S), object(O), ghost(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary surprise ghost-story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
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
    if getattr(args, "setting", None) and getattr(args, "object_", None) and getattr(args, "ghost", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(OBJECTS, getattr(args, "object_", None)), _safe_lookup(GHOSTS, getattr(args, "ghost", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in select_reasonable_combo()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "object_", None) is None or c[1] == getattr(args, "object_", None))
        and (getattr(args, "ghost", None) is None or c[2] == getattr(args, "ghost", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, obj, ghost = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, object=obj, ghost=ghost, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(_safe_lookup(SETTINGS, params.setting), _safe_lookup(OBJECTS, params.object), _safe_lookup(GHOSTS, params.ghost), params.name, params.trait)
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
        print(asp_program("#show reasonable/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, object, ghost) combos:\n")
        for s, o, g in combos:
            print(f"  {s:10} {o:8} {g}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.object} in {p.setting} (ghost: {p.ghost})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
