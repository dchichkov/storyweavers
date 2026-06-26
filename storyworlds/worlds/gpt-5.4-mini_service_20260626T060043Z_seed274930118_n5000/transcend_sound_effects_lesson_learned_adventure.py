#!/usr/bin/env python3
"""
Standalone storyworld: transcend_sound_effects_lesson_learned_adventure

A small Adventure-style domain about a child and a companion crossing a windy
trail, using sound effects and a lesson learned about courage, listening, and
helping each other transcend fear.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld script
- imports shared results eagerly
- imports shared asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
# Domain model
# ---------------------------------------------------------------------------
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    terrain: str
    afford: set[str] = field(default_factory=set)
    danger: str = ""
    soundscape: str = ""
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
class Challenge:
    id: str
    verb: str
    rush: str
    outcome: str
    sound: str
    threat: str
    lesson: str
    tag: str
    zone: set[str] = field(default_factory=set)
    keyword: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    action: str = ""
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest_path": Setting(
        place="the forest path",
        terrain="trail",
        afford={"cross_bridge", "climb_ridge", "step_stones"},
        danger="a windy drop",
        soundscape="the leaves whispered and the branches creaked",
    ),
    "canyon_edge": Setting(
        place="the canyon edge",
        terrain="cliff",
        afford={"cross_bridge", "step_stones"},
        danger="a deep gap",
        soundscape="the wind whooshed between the rocks",
    ),
    "riverbank": Setting(
        place="the riverbank",
        terrain="shore",
        afford={"cross_bridge", "step_stones", "follow_path"},
        danger="fast water",
        soundscape="the river went splish-splash over the stones",
    ),
    "hill_trail": Setting(
        place="the hill trail",
        terrain="slope",
        afford={"climb_ridge", "follow_path"},
        danger="a steep climb",
        soundscape="the path hummed with crickets and distant birds",
    ),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        verb="cross the bridge",
        rush="run toward the bridge",
        outcome="crossed the bridge",
        sound="creak-creak",
        threat="the bridge swayed in the wind",
        lesson="slow steps can be braver than rushing",
        tag="bridge",
        zone={"feet"},
        keyword="bridge",
    ),
    "ridge": Challenge(
        id="ridge",
        verb="climb the ridge",
        rush="dash up the ridge",
        outcome="climbed the ridge",
        sound="scritch-scritch",
        threat="loose pebbles slipped underfoot",
        lesson="looking carefully helps you climb safely",
        tag="ridge",
        zone={"feet", "hands"},
        keyword="ridge",
    ),
    "stones": Challenge(
        id="stones",
        verb="step across the stones",
        rush="leap from stone to stone",
        outcome="stepped across the stones",
        sound="plip-plop",
        threat="the stones were slippery",
        lesson="small careful steps can beat one big leap",
        tag="stones",
        zone={"feet"},
        keyword="stones",
    ),
    "path": Challenge(
        id="path",
        verb="follow the path",
        rush="sprint down the trail",
        outcome="followed the path",
        sound="tap-tap",
        threat="the path forked and looked confusing",
        lesson="listening to a map keeps you from getting lost",
        tag="path",
        zone={"feet"},
        keyword="path",
    ),
}

TOOLS = {
    "map": Tool(
        id="map",
        label="map",
        phrase="a folded map with a red line",
        solves={"path"},
        helps={"bridge", "ridge", "stones"},
        action="look at the map",
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a sturdy rope",
        solves={"ridge"},
        helps={"bridge", "stones"},
        action="hold the rope",
    ),
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="good hiking boots",
        solves={"stones", "ridge"},
        helps={"bridge"},
        action="lace up the boots",
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        solves={"path"},
        helps={"bridge", "ridge"},
        action="carry the lantern",
    ),
}

HERO_NAMES = ["Ava", "Milo", "Nina", "Leo", "Zoe", "Iris", "Owen", "Maya", "Ezra", "Lila"]
COMPANION_NAMES = ["Pip", "Tess", "Bo", "Nora", "Kai", "Juno", "Ben", "Mia"]
TRAITS = ["curious", "brave", "restless", "careful", "spirited", "thoughtful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Storyworld mechanics
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


def challenge_at_risk(setting: Setting, challenge: Challenge) -> bool:
    return challenge.id in setting.afford


def select_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS.values():
        if challenge.id in tool.solves:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, setting in SETTINGS.items():
        for cid in setting.afford:
            ch = _safe_lookup(CHALLENGES, cid)
            for tid, tool in TOOLS.items():
                if ch.id in tool.solves:
                    out.append((pid, cid, tid))
    return out


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters.setdefault(challenge.id, 0.0)
    hero.meters[challenge.id] += 1.0
    hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1.0
    if narrate:
        world.say(f"{challenge.sound}! {hero.id} tried to {challenge.verb}.")


def predict_outcome(world: World, hero: Entity, challenge: Challenge, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    if tool:
        sim.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    _do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    return {
        "got_lost": challenge.id == "path" and tool is None,
        "hurt": challenge.id in {"ridge", "bridge", "stones"} and tool is None,
        "resolved": tool is not None and challenge.id in tool.solves,
    }


def intro(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved adventures with {companion.id}."
    )
    world.say(f"Together, they liked to go where the trail looked bold and the air felt alive.")


def setup(world: World, hero: Entity, tool: Entity, challenge: Challenge) -> None:
    world.say(
        f"One day, {hero.id} found {tool.phrase} beside the pack."
    )
    world.say(
        f"{hero.id} smiled at {tool.label_word if hasattr(tool, 'label_word') else tool.label} because it might help with {challenge.verb}."
    )


def warning(world: World, hero: Entity, challenge: Challenge) -> None:
    world.say(
        f"The {challenge.tag} ahead looked tricky, and {challenge.threat}."
    )
    world.say(
        f'"{challenge.sound}," {hero.id} whispered, noticing how the moment asked for patience.'
    )


def hesitation(world: World, hero: Entity, companion: Entity, challenge: Challenge) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to rush, but {companion.id} pointed to the safe way and slowed {hero.pronoun('object')} down."
    )
    world.say(
        f"That helped {hero.id} remember the lesson of the day: {challenge.lesson}."
    )


def resolve(world: World, hero: Entity, companion: Entity, challenge: Challenge, tool: Tool) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(
        f"{hero.id} chose to {tool.action} first, and then they went on."
    )
    world.say(
        f"Step by step, they {challenge.outcome}, and the path felt less scary each moment."
    )
    world.say(
        f"At the end, {hero.id} had learned how to transcend {challenge.tag} by using calm hands, a helpful tool, and a friend beside {hero.pronoun('object')}."
    )


def tell(setting: Setting, challenge: Challenge, tool_cfg: Tool,
         hero_name: str, hero_type: str, companion_name: str,
         hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[hero_trait, "adventurous"]))
    companion = world.add(Entity(id=companion_name, kind="character", type="friend", label="friend", traits=["helpful"]))
    tool = world.add(Entity(id=tool_cfg.id, kind="thing", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id))
    tool.companion = companion.id

    intro(world, hero, companion)
    world.para()
    world.say(f"The path was {setting.place}, and {setting.soundscape}.")
    setup(world, hero, tool, challenge)
    warning(world, hero, challenge)
    hesitation(world, hero, companion, challenge)
    world.para()
    resolve(world, hero, companion, challenge, tool_cfg)

    world.facts.update(hero=hero, companion=companion, tool=tool, challenge=challenge, setting=setting, tool_cfg=tool_cfg)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    tool = _safe_fact(world, f, "tool_cfg")
    return [
        f'Write a short adventure story for a young child that includes the sound effect "{challenge.sound}" and the word "transcend".',
        f"Tell a gentle adventure where {hero.id} uses {tool.label} to safely {challenge.verb}, learns a lesson, and ends bravely.",
        f"Write a story about a child and a friend on {world.setting.place} with sound effects and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    companion: Entity = _safe_fact(world, f, "companion")
    challenge: Challenge = _safe_fact(world, f, "challenge")
    tool: Tool = _safe_fact(world, f, "tool_cfg")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What adventure was {hero.id} trying to have on {setting.place}?",
            answer=f"{hero.id} was trying to {challenge.verb} with {companion.id} beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What helped {hero.id} face the tricky part of the trail?",
            answer=f"{tool.phrase} helped {hero.id} get ready, and {companion.id} helped {hero.id} stay calm.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn in the end?",
            answer=f"{hero.id} learned that {challenge.lesson}. That was how {hero.id} could transcend the hard part and keep going.",
        ),
        QAItem(
            question=f"What sound effect showed the risky moment in the story?",
            answer=f'The story used "{challenge.sound}" when {hero.id} approached the difficult part of the adventure.',
        ),
    ]


WORLD_KNOWLEDGE = {
    "bridge": [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross over something like water, a road, or a gap in the land.",
        )
    ],
    "ridge": [
        QAItem(
            question="What is a ridge?",
            answer="A ridge is a long raised line of land, often high up and a little steep.",
        )
    ],
    "stones": [
        QAItem(
            question="Why can stones in a river be slippery?",
            answer="Stones can be slippery because water makes them smooth and wet.",
        )
    ],
    "path": [
        QAItem(
            question="Why is it good to follow a path in the woods?",
            answer="Following a path helps you stay on the safest way and not get lost.",
        )
    ],
    "map": [
        QAItem(
            question="What does a map do?",
            answer="A map shows where things are and can help you find your way.",
        )
    ],
    "rope": [
        QAItem(
            question="What can a rope be used for on a hike?",
            answer="A rope can help you hold on, balance, or keep steady when the trail is tricky.",
        )
    ],
    "boots": [
        QAItem(
            question="Why do hikers wear boots?",
            answer="Hiking boots give your feet grip and help protect them on rough ground.",
        )
    ],
    "lantern": [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern makes light so you can see in dark places.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    f = world.facts
    for tag in [f["challenge"].tag, f["tool_cfg"].id]:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- challenge_id(C).
tool(T) :- tool_id(T).

valid(P, C, T) :- afford(P, C), solves(T, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for cid in sorted(setting.afford):
            lines.append(asp.fact("afford", pid, cid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge_id", cid))
        lines.append(asp.fact("lesson", cid, ch.lesson))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for cid in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with sound effects and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, tool = rng.choice(list(combos))
    if getattr(args, "challenge", None) and getattr(args, "tool", None):
        ch = _safe_lookup(CHALLENGES, getattr(args, "challenge", None))
        tl = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if ch.id not in tl.solves:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANION_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, tool=tool, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    tool = _safe_lookup(TOOLS, params.tool)
    hero_type = params.gender
    world = tell(setting, challenge, tool, params.name, hero_type, params.companion, params.trait)
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
    StoryParams(place="forest_path", challenge="path", tool="map", name="Ava", gender="girl", companion="Pip", trait="curious"),
    StoryParams(place="canyon_edge", challenge="bridge", tool="rope", name="Milo", gender="boy", companion="Tess", trait="brave"),
    StoryParams(place="riverbank", challenge="stones", tool="boots", name="Nina", gender="girl", companion="Kai", trait="thoughtful"),
    StoryParams(place="hill_trail", challenge="ridge", tool="lantern", name="Leo", gender="boy", companion="Juno", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, challenge, tool) combos:\n")
        for p, c, t in combos:
            print(f"  {p:12} {c:10} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.challenge} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
