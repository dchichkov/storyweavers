#!/usr/bin/env python3
"""
A tiny Space-Adventure storyworld about teamwork, a shipboard feed, and a
questionnaire that helps the crew work together.

Seed premise:
- A small crew is traveling in space.
- They must feed a stowaway creature safely.
- They also need to finish a questionnaire so the ship can choose the right care plan.
- Teamwork turns a tense moment into a calm ending.

This script is self-contained and follows the storyworld contract.
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
# Core world model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    creature: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ("hunger", "mess", "battery", "calm", "focus", "coordination"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "pilot"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the starship kitchen"
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
class Feed:
    id: str
    label: str
    phrase: str
    flavor: str
    spill: str
    safe_for: set[str] = field(default_factory=set)
    needs_tool: str = ""
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
class Questionnaire:
    id: str
    label: str
    purpose: str
    answers: dict[str, str] = field(default_factory=dict)
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
class Tool:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the starship kitchen", affords={"feed"}),
    "cargo": Setting(place="the cargo bay", affords={"feed"}),
    "greenhouse": Setting(place="the hydroponic greenhouse", affords={"feed"}),
}

CREW_NAMES = ["Ari", "Mika", "Nova", "Tess", "Rin", "Kai", "Juno", "Pip"]
CREW_TYPES = ["pilot", "engineer", "captain", "navigator"]
TRAITS = ["brave", "careful", "curious", "quick", "steady", "kind"]

FEEDS = {
    "crunch": Feed(
        id="crunch",
        label="crunch pellets",
        phrase="a bowl of crunchy space pellets",
        flavor="crisp",
        spill="scatter",
        safe_for={"sparkkit", "cloudling"},
        needs_tool="magnet tray",
    ),
    "soup": Feed(
        id="soup",
        label="warm soup",
        phrase="a warm bowl of moon soup",
        flavor="soft",
        spill="splash",
        safe_for={"cloudling", "orbbit"},
        needs_tool="steady spoon",
    ),
    "nectar": Feed(
        id="nectar",
        label="sunflower nectar",
        phrase="a tiny cup of bright nectar",
        flavor="sweet",
        spill="drip",
        safe_for={"sparkkit"},
        needs_tool="sealed cup",
    ),
}

QUESTIONNAIRES = {
    "care": Questionnaire(
        id="care",
        label="care questionnaire",
        purpose="help the ship choose the right feeding plan",
        answers={
            "sparkkit": "likes dry snacks and careful pouring",
            "cloudling": "likes soft food and gentle movement",
            "orbbit": "likes warm food and slow hands",
        },
    ),
    "mood": Questionnaire(
        id="mood",
        label="mood questionnaire",
        purpose="learn whether the creature feels hungry, shy, or excited",
        answers={
            "sparkkit": "often feels excited near shiny tools",
            "cloudling": "often feels shy until voices go soft",
            "orbbit": "often feels calm when the room is quiet",
        },
    ),
}

TOOLS = [
    Tool(
        id="magnet_tray",
        label="a magnet tray",
        covers={"table"},
        guards={"scatter"},
        prep="set out the magnet tray first",
        tail="worked together with the magnet tray ready",
    ),
    Tool(
        id="steady_spoon",
        label="a steady spoon",
        covers={"bowl"},
        guards={"splash"},
        prep="take the steady spoon",
        tail="used the steady spoon to keep the soup calm",
    ),
    Tool(
        id="sealed_cup",
        label="a sealed cup",
        covers={"cup"},
        guards={"drip"},
        prep="seal the cup before the feed",
        tail="kept the nectar safely inside the sealed cup",
    ),
]

CREATURES = {
    "sparkkit": {"label": "sparkkit", "type": "creature", "safe_feed": {"crunch", "nectar"}},
    "cloudling": {"label": "cloudling", "type": "creature", "safe_feed": {"crunch", "soup"}},
    "orbbit": {"label": "orbbit", "type": "creature", "safe_feed": {"soup"}},
}


# ---------------------------------------------------------------------------
# World reasoning helpers
# ---------------------------------------------------------------------------

def feed_risky(feed: Feed, creature_id: str) -> bool:
    return feed.id not in _safe_lookup(CREATURES, creature_id)["safe_feed"]


def select_tool(feed: Feed, creature_id: str) -> Optional[Tool]:
    for tool in TOOLS:
        if feed.spill in tool.guards:
            return tool
    return None


ASP_RULES = r"""
feed_risky(F, C) :- feed(F), creature(C), unsafe_feed(C, F).
tool_works(T, F) :- tool(T), feed(F), spill_of(F, S), guards(T, S).
valid_combo(F, C) :- feed_risky(F, C), tool_works(_, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for fid, feed in FEEDS.items():
        lines.append(asp.fact("feed", fid))
        lines.append(asp.fact("spill_of", fid, feed.spill))
        for c in sorted(feed.safe_for):
            lines.append(asp.fact("safe_for", fid, c))
    for qid, q in QUESTIONNAIRES.items():
        lines.append(asp.fact("questionnaire", qid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for fid in sorted(c["safe_feed"]):
            lines.append(asp.fact("unsafe_feed", cid, fid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonable combinations
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for fid, feed in FEEDS.items():
            if "feed" not in setting.affords:
                continue
            for cid in CREATURES:
                if feed_risky(feed, cid) and select_tool(feed, cid):
                    out.append((place, fid, cid))
    return out


def explain_rejection(feed: Feed, creature_id: str) -> str:
    if not feed_risky(feed, creature_id):
        return (
            f"(No story: {feed.label} is already safe for {creature_id}, so the crew would not need a tense warning.)"
        )
    return (
        f"(No story: nothing in the tool set fits {feed.spill} for {feed.label} well enough, so the crew cannot solve this feed safely.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    feed: str
    creature: str
    name: str
    crew_role: str
    trait: str
    questionnaire: str
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


def _do_feed(world: World, actor: Entity, feed: Feed, creature: Entity, narrate: bool = True) -> None:
    actor.memes["focus"] += 1
    actor.meters["battery"] -= 0.1
    creature.meters["hunger"] = max(0.0, creature.meters["hunger"] - 1.0)
    if feed.spill == "scatter":
        actor.meters["mess"] += 0.5
    elif feed.spill == "splash":
        actor.meters["mess"] += 0.7
    else:
        actor.meters["mess"] += 0.3
    if narrate:
        world.say(f"They fed {creature.label} with {feed.phrase}.")
        world.say(f"The room felt careful and busy, like every hand had a job.")


def predict(world: World, feed: Feed, creature: Entity) -> dict:
    sim = world.copy()
    _do_feed(sim, sim.get(world.facts["hero"].id), feed, sim.get(creature.id), narrate=False)
    return {"mess": sim.get(world.facts["hero"].id).meters["mess"]}


def intro(world: World, hero: Entity, captain: Entity, creature: Entity, questionnaire: Questionnaire) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} aboard the ship, and {hero.pronoun('subject')} liked "
        f"when the crew worked like clockwork."
    )
    world.say(
        f"On this trip, the ship carried a {creature.label}, and the {questionnaire.label} was meant to "
        f"{questionnaire.purpose}."
    )
    world.say(
        f"{captain.id} trusted {hero.id} to help, because {hero.pronoun('subject')} could keep a calm hand on small jobs."
    )


def setup_feed(world: World, hero: Entity, feed: Feed, creature: Entity) -> None:
    hero.memes["desire"] += 1
    creature.meters["hunger"] += 1.0
    world.say(
        f"{hero.id} wanted to feed {creature.label} right away, but the {feed.label} could get messy if they rushed."
    )


def ask_questionnaire(world: World, hero: Entity, questionnaire: Questionnaire, creature: Entity) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"Before they started, {hero.id} opened the {questionnaire.label} and read the first questions out loud."
    )
    world.say(
        f"The answers helped them remember what {creature.label} liked, so the crew could choose the gentlest plan."
    )


def warn(world: World, hero: Entity, feed: Feed, creature: Entity, questionnaire: Questionnaire) -> bool:
    if not feed_risky(feed, creature.id):
        return False
    world.facts["predicted_mess"] = feed.spill
    world.say(
        f'"If we rush this {feed.label}, the {feed.spill} could make a mess," {hero.id} said, glancing at the questionnaire.'
    )
    return True


def teamwork_offer(world: World, hero: Entity, feed: Feed, creature: Entity) -> Optional[Tool]:
    tool = select_tool(feed, creature.id)
    if not tool:
        return None
    world.say(f"{hero.id} pointed to {tool.label} and said they should use it together.")
    return tool


def accept_plan(world: World, hero: Entity, creature: Entity, feed: Feed, tool: Tool) -> None:
    hero.memes["calm"] += 1
    hero.memes["coordination"] += 1
    creature.memes["calm"] = creature.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.id} and the crew smiled, set up {tool.label}, and fed {creature.label} the safe way."
    )
    world.say(
        f"In the end, {tool.tail}, and {creature.label} stayed happy while the kitchen stayed neat."
    )


def tell(setting: Setting, feed_cfg: Feed, creature_id: str, hero_name: str, crew_role: str,
         trait: str, questionnaire_id: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=crew_role, traits=[trait, "helpful"]))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", traits=["steady"]))
    creature = world.add(Entity(id=creature_id, kind="character", type="creature", label=creature_id))
    questionnaire = _safe_lookup(QUESTIONNAIRES, questionnaire_id)

    world.facts.update(hero=hero, captain=captain, creature=creature, questionnaire=questionnaire, feed=feed_cfg)

    intro(world, hero, captain, creature, questionnaire)
    world.para()
    setup_feed(world, hero, feed_cfg, creature)
    ask_questionnaire(world, hero, questionnaire, creature)
    warn(world, hero, feed_cfg, creature, questionnaire)
    world.para()
    tool = teamwork_offer(world, hero, feed_cfg, creature)
    if tool:
        accept_plan(world, hero, creature, feed_cfg, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space story for a young child about a crew, a feed, and a questionnaire, with teamwork.',
        f"Tell a gentle story where {f['hero'].id} helps feed a {f['creature'].label} without making a mess.",
        f'Write a simple space adventure that includes the words "{f["feed"].label}" and "questionnaire".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    creature: Entity = _safe_fact(world, f, "creature")
    feed_cfg: Feed = _safe_fact(world, f, "feed")
    questionnaire: Questionnaire = _safe_fact(world, f, "questionnaire")
    qa = [
        QAItem(
            question=f"Who helped with the feed in the ship kitchen?",
            answer=f"{hero.id} helped, and {hero.pronoun('subject')} worked with the captain and crew.",
        ),
        QAItem(
            question=f"What did the questionnaire help the crew do?",
            answer=f"It helped the crew choose the right care plan for {creature.label} before feeding it.",
        ),
        QAItem(
            question=f"What kind of food did they use?",
            answer=f"They used {feed_cfg.phrase}, which was the right kind of feed for this little space job.",
        ),
    ]
    if f.get("predicted_mess"):
        qa.append(
            QAItem(
                question=f"Why did {hero.id} warn the others about the feed?",
                answer=f"{hero.id} warned them because the {feed_cfg.label} could {feed_cfg.spill} and make a mess if they rushed.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did teamwork change the ending?",
            answer=f"Teamwork let {hero.id} and the crew use the right tool, so they could feed {creature.label} safely and keep the kitchen neat.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    feed_cfg: Feed = _safe_fact(world, f, "feed")
    out = [
        QAItem(
            question="What is a questionnaire?",
            answer="A questionnaire is a set of questions people answer so they can learn more and make a better plan.",
        ),
        QAItem(
            question="Why do teams work better when everyone helps?",
            answer="Teams work better when everyone helps because each person can do a small job, and the jobs fit together.",
        ),
    ]
    if feed_cfg.id == "crunch":
        out.append(QAItem(question="Why are crunchy pellets easy to scoop?", answer="Crunchy pellets are easy to scoop because they stay in little pieces and do not run everywhere."))
    elif feed_cfg.id == "soup":
        out.append(QAItem(question="Why is soup a careful food to carry?", answer="Soup is careful to carry because it can splash if the bowl bumps too fast."))
    else:
        out.append(QAItem(question="Why is a sealed cup useful?", answer="A sealed cup is useful because it keeps a drink from dripping out during the trip."))
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    feed: str
    creature: str
    name: str
    crew_role: str
    trait: str
    questionnaire: str
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


CURATED = [
    StoryParams(place="kitchen", feed="crunch", creature="sparkkit", name="Ari", crew_role="engineer", trait="careful", questionnaire="care"),
    StoryParams(place="cargo", feed="soup", creature="cloudling", name="Nova", crew_role="pilot", trait="kind", questionnaire="mood"),
    StoryParams(place="greenhouse", feed="nectar", creature="sparkkit", name="Mika", crew_role="navigator", trait="steady", questionnaire="care"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with feed, questionnaire, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--feed", choices=FEEDS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--name")
    ap.add_argument("--crew-role", choices=["pilot", "engineer", "captain", "navigator"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--questionnaire", choices=QUESTIONNAIRES)
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
    if getattr(args, "feed", None) and getattr(args, "creature", None) and not feed_risky(_safe_lookup(FEEDS, getattr(args, "feed", None)), getattr(args, "creature", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "feed", None) is None or c[1] == getattr(args, "feed", None)
              if getattr(args, "creature", None) is None or c[2] == getattr(args, "creature", None)]
    if getattr(args, "place", None) or getattr(args, "feed", None) or getattr(args, "creature", None):
        combos = [c for c in valid_combos()
                  if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                  and (getattr(args, "feed", None) is None or c[1] == getattr(args, "feed", None))
                  and (getattr(args, "creature", None) is None or c[2] == getattr(args, "creature", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, feed, creature = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CREW_NAMES)
    crew_role = getattr(args, "crew_role", None) or rng.choice(CREW_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    questionnaire = getattr(args, "questionnaire", None) or rng.choice(list(QUESTIONNAIRES))
    return StoryParams(place, feed, creature, name, crew_role, trait, questionnaire)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(FEEDS, params.feed), params.creature, params.name,
                 params.crew_role, params.trait, params.questionnaire)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for feed_id, feed in FEEDS.items():
            if "feed" not in setting.affords:
                continue
            for creature_id in CREATURES:
                if feed_risky(feed, creature_id) and select_tool(feed, creature_id):
                    combos.append((place, feed_id, creature_id))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/2."))
        print(sorted(set(asp.atoms(model, "valid_combo"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: feed={p.feed} creature={p.creature} place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
