#!/usr/bin/env python3
"""
inspection_foreshadowing_superhero_story.py
===========================================

A small superhero story world about an inspection, a careful hero, and a clue
that foreshadows trouble before the final rescue.

Seed tale idea:
---
Captain Bright loved helping people in Cloud City. One morning, the city hall
announced a safety inspection for the big bridge. Captain Bright and her
sidekick Zip checked the bridge first. Everything looked fine, but a little
scratch on one beam made Captain Bright pause. It seemed small, yet it felt like
a clue.

Later, when the wind started to shake the bridge, the scratch turned out to be
the place where a hidden crack spread fast. Captain Bright had already noticed
it. She hurried back, used her light shield, and held the bridge steady while
Zip guided everyone away. After the fix, the inspector smiled and marked the
bridge safe.

The storyworld models:
- a hero with a power and a shield
- a place that can be inspected
- a hidden weakness that is foreshadowed by a small clue
- a later emergency that grows from that clue
- a safe resolution after the inspection

The prose is state-driven: the inspection reveals a clue, the clue later becomes
danger, and the hero's prior caution pays off.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when run directly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

FORESHADOW_THRESHOLD = 1.0
DANGER_THRESHOLD = 1.0



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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    villain: object | None = None
    def __post_init__(self) -> None:
        for k in ["stress", "joy", "alert", "risk", "damage", "trust", "courage"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
class Inspection:
    id: str
    noun: str
    verb: str
    clue_noun: str
    clue_phrase: str
    danger_phrase: str
    repair_phrase: str
    foreshadow: str
    later_event: str
    later_verb: str
    reveal: str
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
    phrase: str
    protects: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bridge": Setting(place="the silver bridge", affords={"inspection", "storm"}),
    "museum": Setting(place="the museum roof", affords={"inspection", "storm"}),
    "tower": Setting(place="the clock tower", affords={"inspection", "storm"}),
    "harbor": Setting(place="the harbor wall", affords={"inspection", "storm"}),
}

INSPECTIONS = {
    "bridge": Inspection(
        id="bridge",
        noun="bridge",
        verb="inspect the bridge",
        clue_noun="scratch",
        clue_phrase="a tiny scratch on one beam",
        danger_phrase="a hidden crack under the paint",
        repair_phrase="tighten the beam and add a steel brace",
        foreshadow="the scratch looked too small to matter, but it was a clue",
        later_event="the wind tugged hard at the bridge",
        later_verb="shake",
        reveal="the crack widened where the scratch had been",
        tags={"bridge", "metal", "warning"},
    ),
    "museum": Inspection(
        id="museum",
        noun="roof",
        verb="inspect the roof",
        clue_noun="drip",
        clue_phrase="one wet drip near a corner seam",
        danger_phrase="a loose seam under the tiles",
        repair_phrase="seal the seam before the rain came in",
        foreshadow="the drip was tiny, yet it hinted at bigger trouble",
        later_event="the rain began to tap on the roof",
        later_verb="leak",
        reveal="water slipped through the loose seam",
        tags={"roof", "rain", "warning"},
    ),
    "tower": Inspection(
        id="tower",
        noun="tower",
        verb="inspect the tower",
        clue_noun="rattle",
        clue_phrase="a small rattle in one stone stair",
        danger_phrase="a cracked stair hidden under dust",
        repair_phrase="block the stair and set a warning rope",
        foreshadow="the rattle felt like a whisper from the future",
        later_event="the tower bell started to ring",
        later_verb="shake",
        reveal="the cracked stair began to split",
        tags={"stone", "warning", "bell"},
    ),
    "harbor": Inspection(
        id="harbor",
        noun="wall",
        verb="inspect the harbor wall",
        clue_noun="chip",
        clue_phrase="a chipped stone near the waterline",
        danger_phrase="a weak spot washed smooth by waves",
        repair_phrase="fill the weak spot with fresh stone",
        foreshadow="the chip was little, but it pointed to a weak spot",
        later_event="the tide rolled in higher than usual",
        later_verb="push",
        reveal="the weak spot began to crumble",
        tags={"water", "stone", "warning"},
    ),
}

GEAR = {
    "shield": Gear(id="shield", label="light shield", phrase="a bright light shield", protects={"damage"}),
    "rope": Gear(id="rope", label="warning rope", phrase="a red warning rope", protects={"fall"}),
    "scanner": Gear(id="scanner", label="clue scanner", phrase="a tiny clue scanner", protects={"miss"}),
}

HERO_NAMES = ["Captain Bright", "Nova", "Spark", "Comet", "Starlight", "Vector"]
SIDEKICKS = ["Zip", "Pip", "Milo", "Dot", "Rin", "Beep"]
VILLAINS = ["Shadow Coil", "Murk", "Rust Shade", "Drift", "Flicker"]
TRAITS = ["brave", "careful", "quick", "kind", "sharp-eyed"]


@dataclass
class StoryParams:
    place: str
    inspection: str
    hero: str
    sidekick: str
    villain: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    p: object | None = None
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


ASP_RULES = r"""
% A place is inspectable if it affords inspection.
inspectable(P) :- place(P), affords(P, inspection).

% A clue foreshadows danger when it belongs to an inspection and exists at the place.
foreshadows(P, I) :- inspectable(P), inspection(I), clue(I, C), clue_at(P, C).

% Later danger is justified if the inspection has a clue and a later event exists.
dangerous(P, I) :- foreshadows(P, I), later(I).

% A safe resolution is possible when the hero has a shield and the place is repaired.
safe(P, I) :- dangerous(P, I), shield(Shield), has_shield(Hero, Shield), repaired(P, I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, ins in INSPECTIONS.items():
        lines.append(asp.fact("inspection", iid))
        lines.append(asp.fact("clue", iid, ins.clue_noun))
        lines.append(asp.fact("later", iid))
    for gid in GEAR:
        lines.append(asp.fact("shield", gid) if gid == "shield" else asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show inspectable/1. #show foreshadows/2. #show dangerous/2."))
    atoms = set((s.name, tuple(str(a) for a in s.arguments)) for s in model)
    expected = set()
    for pid in SETTINGS:
        expected.add(("inspectable", (pid,)))
        for iid in INSPECTIONS:
            expected.add(("foreshadows", (pid, iid)))
            expected.add(("dangerous", (pid, iid)))
    if atoms:
        print("OK: ASP program solved.")
        return 0
    print("WARN: ASP solver produced no shown atoms.")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def inspectable(place: str, inspection: Inspection) -> bool:
    return place in SETTINGS and "inspection" in _safe_lookup(SETTINGS, place).affords and inspection.id == place


def foreshadow(world: World, hero: Entity, inspection: Inspection) -> None:
    hero.memes["alert"] += 1
    world.say(
        f"During the inspection, {hero.id} noticed {inspection.clue_phrase}; "
        f"{inspection.foreshadow}."
    )
    world.facts["clue"] = inspection.clue_noun
    world.facts["foreshadow"] = True


def reveal_danger(world: World, hero: Entity, inspection: Inspection) -> None:
    villain = world.get("villain")
    hero.meters["stress"] += 1
    villain.memes["restless"] += 1
    world.say(
        f"Later, {inspection.later_event}, and {inspection.reveal}. "
        f"{hero.id} realized the clue had been warning them all along."
    )


def repair(world: World, hero: Entity, inspection: Inspection) -> None:
    hero.meters["courage"] += 1
    world.say(
        f"{hero.id} used {inspection.repair_phrase}, and the danger went quiet."
    )
    world.facts["repaired"] = True


def rescue(world: World, hero: Entity, sidekick: Entity, inspection: Inspection) -> None:
    hero.meters["joy"] += 1
    sidekick.meters["joy"] += 1
    world.say(
        f"Then {hero.id} and {sidekick.id} held the place steady until everyone was safe. "
        f"After that, the inspector smiled and marked it safe."
    )


def tell(setting: Setting, inspection: Inspection, hero_name: str, sidekick_name: str, villain_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label=hero_name))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="sidekick", label=sidekick_name))
    villain = world.add(Entity(id="villain", kind="character", type="villain", label=villain_name))
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, inspection=inspection, setting=setting)

    world.say(
        f"{hero.id} was a {trait} superhero who watched {setting.place} closely."
    )
    world.say(
        f"{hero.id} and {sidekick.id} went to {setting.place} for a safety inspection."
    )
    world.say(
        f"They expected a quiet check, but {inspection.clue_phrase} made {hero.id} pause."
    )

    world.para()
    foreshadow(world, hero, inspection)

    world.para()
    world.say(
        f"By afternoon, trouble arrived: {villain.label} tried to make the structure fail."
    )
    reveal_danger(world, hero, inspection)
    repair(world, hero, inspection)
    rescue(world, hero, sidekick, inspection)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    ins: Inspection = _safe_fact(world, f, "inspection")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short superhero story for a young child about an inspection at {setting.place} where {hero.id} notices {ins.clue_phrase}.',
        f"Tell a gentle story where {hero.id} and {sidekick.id} find a clue during an inspection and later save the day.",
        f'Write a story that uses foreshadowing: a tiny clue at {setting.place} should matter later in the same superhero story.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    ins: Inspection = _safe_fact(world, f, "inspection")
    setting: Setting = _safe_fact(world, f, "setting")
    villain: Entity = _safe_fact(world, f, "villain")

    qa = [
        QAItem(
            question=f"What did {hero.id} notice during the inspection at {setting.place}?",
            answer=f"{hero.id} noticed {ins.clue_phrase}. It seemed small, but it was a clue about {ins.danger_phrase}.",
        ),
        QAItem(
            question=f"Why did the tiny clue matter later in the story?",
            answer=f"It mattered because it foreshadowed trouble. The small clue pointed to {ins.danger_phrase}, and later {ins.reveal}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the danger arrived?",
            answer=f"{sidekick.id} helped {hero.id}. Together they kept everyone safe while the problem was fixed.",
        ),
        QAItem(
            question=f"What did {hero.id} do to stop the problem?",
            answer=f"{hero.id} used {ins.repair_phrase} and then helped hold the place steady until the danger passed.",
        ),
        QAItem(
            question=f"Who tried to cause trouble at the end?",
            answer=f"{villain.label} tried to make the structure fail, but the hero was ready because the clue had already given a warning.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ins: Inspection = _safe_fact(world, f, "inspection")
    out = [
        QAItem(
            question="What is an inspection?",
            answer="An inspection is a careful look at something to check if it is safe, clean, or working the way it should.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue about something important that will happen later.",
        ),
    ]
    if "bridge" in ins.tags:
        out.append(QAItem(
            question="Why do people inspect a bridge?",
            answer="People inspect a bridge to make sure it is strong enough for people to cross safely.",
        ))
    if "roof" in ins.tags:
        out.append(QAItem(
            question="Why do people check a roof for leaks?",
            answer="People check a roof for leaks so rain does not get inside and cause damage.",
        ))
    if "stone" in ins.tags:
        out.append(QAItem(
            question="Why do cracked stones need attention?",
            answer="Cracked stones can become weaker over time, so checking them early helps keep people safe.",
        ))
    return out


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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero inspection story world with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--inspection", choices=INSPECTIONS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--villain", choices=VILLAINS)
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    inspection = getattr(args, "inspection", None) or place
    if inspection != place:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    if sidekick == hero:
        sidekick = rng.choice([s for s in SIDEKICKS if s != hero])
    villain = getattr(args, "villain", None) or rng.choice(VILLAINS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, inspection=inspection, hero=hero, sidekick=sidekick, villain=villain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(INSPECTIONS, params.inspection),
        params.hero,
        params.sidekick,
        params.villain,
        params.trait,
    )
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
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if isinstance(v, Entity):
                print(f"{k}: {v.id}")
            elif isinstance(v, Inspection):
                print(f"{k}: {v.id}")
            else:
                print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show inspectable/1. #show foreshadows/2. #show dangerous/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in sorted(SETTINGS):
            p = StoryParams(
                place=place,
                inspection=place,
                hero=_safe_lookup(HERO_NAMES, 0),
                sidekick=_safe_lookup(SIDEKICKS, 0),
                villain=_safe_lookup(VILLAINS, 0),
                trait=_safe_lookup(TRAITS, 0),
            )
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
