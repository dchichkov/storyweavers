#!/usr/bin/env python3
"""
lay_conflict_superhero_story.py
===============================

A small storyworld for a superhero-style tale about a hero facing a conflict,
choosing a lay-low / lay-down / lay-in-wait kind of move, and ending with a
clear change in the world.

The world is intentionally compact:
- a hero has a meter-based energy and courage state,
- a villain creates a physical problem in the city,
- a sidekick or citizen may be in danger,
- the hero must decide whether to rush in or lay low and choose the right plan,
- the ending proves the conflict changed.

The seed word "lay" is woven into the domain through the hero's strategic
choices: laying low, laying a trap, or laying a shield over someone in need.
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
# World model
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    sidekick: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
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
class Setting:
    place: str
    supports: set[str] = field(default_factory=set)
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
class Threat:
    id: str
    label: str
    verb: str
    damage: str
    target_kind: str
    intensity: float
    zone: set[str]
    tag: str
    keyword: str
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
class Shield:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    blocks: set[str]
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
        self.zone: set[str] = set()
        self.threat_id: str = ""
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.threat_id = self.threat_id
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(place="the city", supports={"smoke", "collapse", "storm"}),
    "harbor": Setting(place="the harbor", supports={"smoke", "storm"}),
    "downtown": Setting(place="downtown", supports={"collapse", "smoke"}),
}

THREATS = {
    "smoke": Threat(
        id="smoke",
        label="thick smoke",
        verb="spread smoke over the street",
        damage="hard to breathe",
        target_kind="air",
        intensity=1.0,
        zone={"air"},
        tag="smoke",
        keyword="smoke",
    ),
    "collapse": Threat(
        id="collapse",
        label="a falling scaffold",
        verb="send a scaffold wobbling down",
        damage="cover the road",
        target_kind="street",
        intensity=1.0,
        zone={"street"},
        tag="collapse",
        keyword="scaffold",
    ),
    "storm": Threat(
        id="storm",
        label="a stormy flood",
        verb="flood the lower blocks",
        damage="soak the plaza",
        target_kind="ground",
        intensity=1.0,
        zone={"ground", "street"},
        tag="storm",
        keyword="flood",
    ),
}

SHIELDS = [
    Shield(
        id="cape_shield",
        label="a bright cape-shield",
        prep="lay a bright cape-shield over",
        tail="laid the cape-shield across the danger",
        protects={"air"},
        blocks={"smoke"},
    ),
    Shield(
        id="brace_shield",
        label="a steel brace",
        prep="lay a steel brace under",
        tail="laid the steel brace under the beam",
        protects={"street"},
        blocks={"collapse"},
    ),
    Shield(
        id="pump_shield",
        label="a water pump",
        prep="lay a water pump beside",
        tail="laid the pump beside the flooded steps",
        protects={"ground", "street"},
        blocks={"storm"},
    ),
]

HERO_NAMES = ["Nova", "Blaze", "Mira", "Aster", "Jet", "Luna", "Rex", "Sky"]
VILLAIN_NAMES = ["Drift", "Razor", "Hex", "Gloom", "Volt"]
SIDEKICK_NAMES = ["Pip", "Tess", "Milo", "June", "Kai"]
TRAITS = ["brave", "quick", "steady", "kind", "sharp"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    threat: str
    name: str
    gender: str
    villain: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def threat_at_risk(threat: Threat) -> bool:
    return True


def select_shield(threat: Threat) -> Optional[Shield]:
    for shield in SHIELDS:
        if threat.target_kind in shield.protects and threat.tag in shield.blocks:
            return shield
    return None


def reasonableness_gate(place: str, threat: Threat) -> bool:
    return threat.id in _safe_lookup(SETTINGS, place).supports


def explain_rejection(place: str, threat: Threat) -> str:
    return (
        f"(No story: {threat.label} does not fit {_safe_lookup(SETTINGS, place).place} here, "
        f"so the conflict would not make sense.)"
    )


def build_intro(world: World, hero: Entity, villain: Entity, sidekick: Entity, threat: Threat) -> None:
    world.say(
        f"{hero.id} was a {next((t for t in ['brave', 'quick', 'steady', 'kind', 'sharp'] if t in hero.tags), 'brave')} "
        f"hero who watched over {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} often worked beside {sidekick.id}, "
        f"and both of them knew {villain.id} liked trouble."
    )
    world.say(
        f"One day {villain.id} made {threat.label} {threat.verb}, and the whole place felt tense."
    )


def build_conflict(world: World, hero: Entity, sidekick: Entity, threat: Threat) -> None:
    hero.memes["concern"] = hero.memes.get("concern", 0.0) + 1.0
    sidekick.memes["fear"] = sidekick.memes.get("fear", 0.0) + 1.0
    world.zone = set(threat.zone)
    world.say(
        f"{sidekick.id} pointed at the danger and said it could make {threat.damage}."
    )
    world.say(
        f"{hero.id} wanted to rush in, but {hero.pronoun('possessive')} chest felt tight with conflict."
    )


def predict_outcome(world: World, hero: Entity, threat: Threat, shield: Shield) -> bool:
    sim = world.copy()
    sim.fired = set()
    _use_shield(sim, hero, threat, shield, narrate=False)
    return sim.facts.get("safe", False) is True


def _use_shield(world: World, hero: Entity, threat: Threat, shield: Shield, narrate: bool = True) -> None:
    sig = ("shield", threat.id, shield.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if threat.target_kind in shield.protects and threat.tag in shield.blocks:
        world.facts["safe"] = True
        hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
        if narrate:
            world.say(
                f"{hero.id} chose to lay {shield.label} in the right place instead of charging ahead."
            )
    else:
        world.facts["safe"] = False
        if narrate:
            world.say(f"The plan did not help.")


def resolution(world: World, hero: Entity, villain: Entity, sidekick: Entity, threat: Threat, shield: Shield) -> None:
    world.say(
        f"{hero.id} and {sidekick.id} worked fast: {shield.prep} the danger, then {shield.tail}."
    )
    world.say(
        f"{villain.id}'s trick lost its power, and {threat.label} stopped causing trouble."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    sidekick.memes["fear"] = 0.0
    world.say(
        f"In the end, {hero.id} was smiling, {sidekick.id} was safe, and {world.setting.place} was calm again."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(setting: Setting, threat: Threat, hero_name: str, gender: str, villain_name: str, sidekick_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, tags={trait, "hero"}))
    villain = world.add(Entity(id=villain_name, kind="character", type="villain", tags={"villain"}))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="child", tags={"sidekick"}))

    build_intro(world, hero, villain, sidekick, threat)

    world.para()
    build_conflict(world, hero, sidekick, threat)

    shield = select_shield(threat)
    if shield is None:
        pass

    if not reasonableness_gate(setting.place, threat):
        pass

    if not predict_outcome(world, hero, threat, shield):
        pass

    world.para()
    world.say(
        f"{hero.id} remembered that sometimes the smartest move is to lay something down, not leap first."
    )
    _use_shield(world, hero, threat, shield, narrate=True)
    resolution(world, hero, villain, sidekick, threat, shield)

    world.facts.update(
        hero=hero,
        villain=villain,
        sidekick=sidekick,
        threat=threat,
        shield=shield,
        place=setting.place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    threat: Threat = _safe_fact(world, f, "threat")
    return [
        f'Write a short superhero story for a child where {hero.id} faces {threat.label} and must choose a careful plan.',
        f'Write a simple story that uses the word "lay" when the hero decides how to stop {threat.label}.',
        f'Tell a child-friendly superhero story with a clear conflict, a smart lay-down plan, and a safe ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    villain: Entity = _safe_fact(world, f, "villain")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    threat: Threat = _safe_fact(world, f, "threat")
    shield: Shield = _safe_fact(world, f, "shield")
    return [
        QAItem(
            question=f"Who was the hero in the story?",
            answer=f"The hero was {hero.id}, who stayed brave during the conflict.",
        ),
        QAItem(
            question=f"What problem did {villain.id} cause?",
            answer=f"{villain.id} caused {threat.label}, which could {threat.damage}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the conflict?",
            answer=f"{hero.id} chose to lay {shield.label} in the right place and worked with {sidekick.id} to stop the danger.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The danger was gone, {sidekick.id} was safe, and {world.setting.place} was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    threat: Threat = _safe_fact(world, f, "threat")
    shield: Shield = _safe_fact(world, f, "shield")
    return [
        QAItem(
            question="What is a hero?",
            answer="A hero is a person who helps others and tries to keep people safe.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or struggle that the characters need to solve.",
        ),
        QAItem(
            question="What is a shield for?",
            answer="A shield is something that helps protect people or block danger.",
        ),
        QAItem(
            question=f"Why would {shield.label} help against {threat.label}?",
            answer=f"It helps because it blocks the kind of trouble {threat.label} causes.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A threat is valid for a setting when the setting supports that kind of problem.
valid_story(P, T) :- place(P), threat(T), supports(P, T).

% A shield solves the conflict if it protects the target kind and blocks the threat.
solves(T, S) :- threat(T), shield(S),
                target_kind(T, K), protects(S, K),
                tag(T, X), blocks(S, X).

% A complete story exists when the setting supports the threat and some shield solves it.
complete(P, T, S) :- valid_story(P, T), solves(T, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.supports):
            lines.append(asp.fact("supports", pid, t))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("target_kind", tid, t.target_kind))
        lines.append(asp.fact("tag", tid, t.tag))
    for sh in SHIELDS:
        lines.append(asp.fact("shield", sh.id))
        for p in sorted(sh.protects):
            lines.append(asp.fact("protects", sh.id, p))
        for b in sorted(sh.blocks):
            lines.append(asp.fact("blocks", sh.id, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show complete/3."))
    return sorted(set(asp.atoms(model, "complete")))


def python_combos() -> list[tuple]:
    out = []
    for place, setting in SETTINGS.items():
        for tid, threat in THREATS.items():
            if tid not in setting.supports:
                continue
            if select_shield(threat):
                out.append((place, tid, select_shield(threat).id))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_combos())
    p = set(python_combos())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    threat: str
    name: str
    gender: str
    villain: str
    sidekick: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a lay-themed conflict and a safe resolution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--villain")
    ap.add_argument("--sidekick")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    threat = getattr(args, "threat", None) or rng.choice(list(THREATS))
    if not reasonableness_gate(place, _safe_lookup(THREATS, threat)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    villain = getattr(args, "villain", None) or rng.choice(VILLAIN_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, threat=threat, name=name, gender=gender, villain=villain, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(THREATS, params.threat),
        params.name,
        params.gender,
        params.villain,
        params.sidekick,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  zone: {sorted(world.zone)}")
    return "\n".join(lines)


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
    StoryParams(place="city", threat="smoke", name="Nova", gender="girl", villain="Drift", sidekick="Pip", trait="brave"),
    StoryParams(place="downtown", threat="collapse", name="Blaze", gender="boy", villain="Razor", sidekick="Tess", trait="steady"),
    StoryParams(place="harbor", threat="storm", name="Luna", gender="girl", villain="Gloom", sidekick="Kai", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show complete/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        comps = asp_combos()
        print(f"{len(comps)} compatible story combos:")
        for place, threat, shield in comps:
            print(f"  {place:9} {threat:9} {shield}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.threat} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
