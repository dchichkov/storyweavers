#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/erupt_grip_dim_teamwork_quest_ghost_story.py
=====================================================================================================

A small, constraint-checked story world in a gentle ghost-story style.

Premise:
- A child and a friendly ghost go on a quest through a dim old place.
- The place has a pressure point that can erupt if the wrong object is gripped too hard
  or if the light grows too dim.
- Teamwork can keep the world calm and lead to a small, spooky-but-kind resolution.

Seed words used:
- erupt
- grip-dim

This script follows the Storyworld contract:
- typed entities with physical meters and emotional memes
- world-driven prose, state changes, and Q&A
- lazy ASP helper import
- reasonableness gate + inline ASP twin
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ghost: object | None = None
    hero: object | None = None
    tool_entity: object | None = None
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
    dim: bool
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
class Quest:
    id: str
    title: str
    action: str
    search: str
    danger: str
    turn: str
    end: str
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
class Relic:
    label: str
    phrase: str
    type: str
    keeper: str
    plural: bool = False
    useful_for: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    calms: set[str]
    provides: set[str]
    prep: str
    finish: str
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
        self.quest_zone: str = ""
        self.quest_light: float = 1.0

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
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.quest_zone = self.quest_zone
        c.quest_light = self.quest_light
        return c


def _do_event(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        pass
    world.quest_zone = quest.id
    actor.memes["brave"] = actor.memes.get("brave", 0.0) + 1
    actor.meters["dust"] = actor.meters.get("dust", 0.0) + 1
    world.quest_light -= 0.2
    if world.quest_light < 0:
        world.quest_light = 0
    propagate(world, narrate=narrate)


def _r_dim_warning(world: World) -> list[str]:
    out: list[str] = []
    if world.quest_light >= THRESHOLD:
        return out
    sig = ("dim_warning", world.quest_zone)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The light dimmed, and the old place felt even quieter.")
    return out


def _r_grip_shake(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("grip", 0.0) < THRESHOLD or actor.meters.get("dust", 0.0) < THRESHOLD:
            continue
        sig = ("grip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        out.append(f"{actor.id} felt a shaky chill run up {actor.pronoun('possessive')} arms.")
    return out


def _r_eruption(world: World) -> list[str]:
    out: list[str] = []
    if world.quest_light >= THRESHOLD:
        return out
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("erupt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["ash"] = actor.meters.get("ash", 0.0) + 1
        out.append("A tiny burst of ash puffed up from the floor stones.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("teamwork", 0.0) < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = max(0.0, actor.memes.get("fear", 0.0) - 1)
        actor.meters["ash"] = max(0.0, actor.meters.get("ash", 0.0) - 1)
        out.append(f"Working together made the scary feeling shrink.")
    return out


CAUSAL_RULES = [_r_dim_warning, _r_grip_shake, _r_eruption, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, quest: Quest, relic: Relic) -> dict:
    sim = world.copy()
    a = sim.get(actor.id)
    a.memes["grip"] = a.memes.get("grip", 0.0) + 1
    sim.quest_light -= 0.3
    propagate(sim, narrate=False)
    return {
        "eruption": a.meters.get("ash", 0.0) >= THRESHOLD,
        "fear": a.memes.get("fear", 0.0),
    }


def setting_intro(setting: Setting, quest: Quest) -> str:
    if setting.dim:
        return f"The old place was dim, and every corner looked ready to whisper."
    return "The old place waited in a soft gray hush."


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.type} who liked gentle mysteries and brave footsteps."


def ghost_intro(ghost: Entity) -> str:
    return f"{ghost.id} was a friendly ghost who knew every creak in the old halls."


def quest_intro(hero: Entity, quest: Quest) -> str:
    return f"{hero.id} loved quests, and {quest.title} sounded spooky in the best way."


def relic_intro(hero: Entity, relic: Relic) -> str:
    return f"On a shelf nearby, {hero.pronoun('possessive')} {relic.label} waited to be carried carefully."


def start_story(world: World, hero: Entity, ghost: Entity, quest: Quest, relic: Relic) -> None:
    world.say(hero_intro(hero))
    world.say(ghost_intro(ghost))
    world.say(quest_intro(hero, quest))
    world.say(relic_intro(hero, relic))


def begin_quest(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    world.para()
    world.say(setting_intro(world.setting, quest))
    world.say(f"One night, {hero.id} and {ghost.id} went on a {quest.keyword} quest through {world.setting.place}.")
    world.say(f"They wanted to {quest.action}, but the path was getting dim.")


def tension(world: World, hero: Entity, ghost: Entity, quest: Quest, relic: Relic) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    hero.memes["grip"] = hero.memes.get("grip", 0.0) + 1
    pred = predict_risk(world, hero, quest, relic)
    if pred["eruption"]:
        world.facts["predicted_eruption"] = True
        world.say(
            f"{hero.id} reached for the {relic.label}, but {ghost.id} raised a cool hand and said, "
            f'"If we grip it too hard in the dim, something might erupt."'
        )
    else:
        world.say(f"{hero.id} reached for the {relic.label}, and {ghost.id} said to hold it very gently.")


def turn_to_teamwork(world: World, hero: Entity, ghost: Entity, quest: Quest, relic: Relic, tool: Tool) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    ghost.memes["teamwork"] = ghost.memes.get("teamwork", 0.0) + 1
    tool_entity = world.add(Entity(
        id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id,
        plural=tool.plural,
    ))
    tool_entity.worn_by = hero.id
    world.say(
        f"Then {ghost.id} found a {tool.label}, and {hero.id} held it with both hands while {ghost.id} guided the way."
    )
    world.say(f'"{tool.prep}," {ghost.id} whispered, "and we can finish the quest together."')
    _do_event(world, hero, quest, narrate=True)
    world.say(
        f"The {quest.keyword} quest worked because {hero.id} and {ghost.id} kept the light up and the grip calm."
    )
    world.say(
        f"They {tool.finish}, and the old place stayed quiet instead of erupting."
    )
    world.facts["tool"] = tool_entity
    world.facts["resolved"] = True


def ending(world: World, hero: Entity, ghost: Entity, relic: Relic) -> None:
    world.para()
    world.say(
        f"In the end, {hero.id} carried the {relic.label} with a steady {hero.pronoun('possessive')} hands, "
        f"and {ghost.id} floated beside {hero.pronoun('object')} like a happy moonbeam."
    )
    world.say(
        f"The room was still dim, but it felt friendly now, because teamwork had kept the small eruption away."
    )


SETTINGS = {
    "old_hall": Setting(place="the old hall", dim=True, affords={"lantern", "bells", "attic"}),
    "moon_stairs": Setting(place="the moon stairs", dim=True, affords={"lantern", "keys"}),
    "quiet_attic": Setting(place="the quiet attic", dim=False, affords={"attic", "boxes"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        title="the Lantern Quest",
        action="find the lantern",
        search="the lantern",
        danger="the light might go dim",
        turn="working together with a careful grip",
        end="the hall stayed calm",
        keyword="Quest",
        tags={"light", "lantern"},
    ),
    "bells": Quest(
        id="bells",
        title="the Bell Quest",
        action="bring back the silver bell",
        search="the silver bell",
        danger="the bell might rattle the dust awake",
        turn="using teamwork and a soft touch",
        end="the dust stayed asleep",
        keyword="Quest",
        tags={"bell", "sound"},
    ),
    "attic": Quest(
        id="attic",
        title="the Attic Quest",
        action="carry the map box upstairs",
        search="the map box",
        danger="the stairs might shake when gripped too hard",
        turn="sharing the load",
        end="the stairs stayed still",
        keyword="Teamwork",
        tags={"box", "stairs"},
    ),
}

RELICS = {
    "lantern": Relic(label="lantern", phrase="a little brass lantern", type="lantern", keeper="ghost"),
    "bell": Relic(label="bell", phrase="a tiny silver bell", type="bell", keeper="ghost"),
    "box": Relic(label="box", phrase="a flat map box", type="box", keeper="ghost"),
}

TOOLS = {
    "lantern_glove": Tool(
        id="lantern_glove",
        label="a soft glove",
        phrase="a soft glove",
        covers={"hands"},
        calms={"grip", "fear"},
        provides={"light"},
        prep="hold the lantern with a soft glove",
        finish="set the lantern on a safe shelf",
    ),
    "rope_loop": Tool(
        id="rope_loop",
        label="a rope loop",
        phrase="a rope loop",
        covers={"hands"},
        calms={"grip"},
        provides={"carry"},
        prep="share the load with a rope loop",
        finish="lifted the box without shaking it",
    ),
}

GHOST_NAMES = ["Moss", "Bram", "Wisp", "Mina", "Hush"]
KID_NAMES = ["Lena", "Owen", "Mira", "Nico", "Tess", "Ivy"]
TRAITS = ["curious", "brave", "gentle", "careful", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            combos.append((place, qid))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    ghost_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write a gentle ghost story for a small child about a {quest.keyword} quest in {f["setting"].place}.',
        f"Tell a story where {hero.id} and a friendly ghost solve {quest.title} with teamwork before anything can erupt.",
        f'Write a child-friendly spooky story using the words "{quest.keyword}" and "teamwork" and ending safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    ghost: Entity = _safe_fact(world, f, "ghost")
    quest: Quest = _safe_fact(world, f, "quest")
    relic: Relic = _safe_fact(world, f, "relic")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who went on the {quest.keyword} quest in {place}?",
            answer=f"{hero.id} and {ghost.id} went on the {quest.title} in {place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry when {hero.id} reached for the {relic.label}?",
            answer=(
                f"{hero.id} worried because the place was dim, and if the {relic.label} was gripped too hard, "
                f"the old room might erupt in a tiny puff of ash."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} and {ghost.id} finish the quest safely?",
            answer=(
                f"Teamwork helped them. They used {(f.get('tool') or next(iter(TOOLS.values()))).label} and kept the grip gentle, so the quest stayed calm."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="A ghost can be a spooky-looking friend in a story, sometimes floaty and quiet, but still kind.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something or solve a problem.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like when a room has only a little light.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  quest_zone={world.quest_zone}")
    lines.append(f"  quest_light={world.quest_light}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dim:
            lines.append(asp.fact("dim", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("keyword", qid, q.keyword))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("keeper", rid, r.keeper))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
        for c in sorted(t.calms):
            lines.append(asp.fact("calms", tid, c))
    return "\n".join(lines)


ASP_RULES = r"""
can_run(P,Q) :- affords(P,Q).
dim_risk(P) :- dim(P).
gear_help(T,Q) :- tool(T), keyword(Q,"Quest"), calms(T,"grip").
teamwork_fix(Q) :- quest(Q), keyword(Q,"Quest").
valid_story(P,Q) :- can_run(P,Q), dim_risk(P), teamwork_fix(Q).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with teamwork and a quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "quest", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(list(combos))
    return StoryParams(
        place=place,
        quest=quest,
        name=getattr(args, "name", None) or rng.choice(KID_NAMES),
        ghost_name=getattr(args, "ghost_name", None) or rng.choice(GHOST_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Lena", "Mira", "Tess", "Ivy"} else "boy"))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost"))
    quest = _safe_lookup(QUESTS, params.quest)
    relic = RELICS["lantern" if params.quest == "lantern" else "bell" if params.quest == "bells" else "box"]

    start_story(world, hero, ghost, quest, relic)
    world.para()
    begin_quest(world, hero, ghost, quest)
    tension(world, hero, ghost, quest, relic)
    world.para()
    turn_to_teamwork(world, hero, ghost, quest, relic, TOOLS["lantern_glove" if params.quest == "lantern" else "rope_loop"])
    ending(world, hero, ghost, relic)

    world.facts.update(hero=hero, ghost=ghost, quest=quest, relic=relic, setting=world.setting, tool=world.facts["tool"])
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
    StoryParams(place="old_hall", quest="lantern", name="Lena", ghost_name="Moss", trait="curious"),
    StoryParams(place="moon_stairs", quest="bells", name="Nico", ghost_name="Wisp", trait="brave"),
    StoryParams(place="quiet_attic", quest="attic", name="Tess", ghost_name="Hush", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, q in combos:
            print(f"  {p:12} {q}")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
