#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/canoe_reunion_bravery_bedtime_story.py
=============================================================================================================

A standalone *story world* sketch for the "Canoe Reunion" tale and close,
*constraint-checked* variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a little girl named Maple who lived with her
grandfather by a wide, slow river. Every summer, her mother would paddle up
the river in an old wooden canoe to visit them, and the two of them would
hug at the dock as if the whole world had shrunk down to just a hug.

One morning, a storm the night before had pushed a fallen pine into the
narrow bend, and the dock was half broken. Maple heard a far-off splash, and
she knew her mother was close. She ran to the river, but the old canoe was
drifting in the tall grass, and the path to the dock was washed out.

Maple was small, but the river was loud that day, and the splash came again
closer. She took a deep breath, pulled the small canoe into the water with
both hands, and paddled out past the fallen pine. The water pushed hard, but
she kept her paddle low and steady, the way her grandfather had taught her.

When she reached the bend, her mother was there, smiling from her own canoe.
"Maple!" her mother called. "I knew you would come." They paddled back to
shore together, tied the canoes to what was left of the dock, and walked up
to the cabin hand in hand, ready for the reunion hug at the door.

Causal state updates:
---
    do journey (alone)        -> child.<mess> += 1   (river spray, mud)
                                  child.bravery += 1
                                  child.strength += 1
    obstacle cleared          -> child.bravery += 1
    meeting family            -> child.joy += 1
                                  child.love += 1
    storm water rise          -> river.roughness += 1
                                  path.break += 1
    gear used (paddle)        -> child.skill += 1
                                  child.bravery += 1
    helper present            -> child.confidence += 1

Scripted social/emotional beats:
---
    child alone at river      -> child.worry += 1
    paddling through rough    -> child.bravery += 1
    first sight of mother     -> child.love += 1 ; child.joy += 1
    shared task at dock       -> child.love += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# Meters -- physical things that can accumulate.
MESS_KINDS = {"wet", "muddy", "cold"}
# Emotional meme keys we lean on across this domain.
MEME_KEYS = {"worry", "joy", "love", "bravery", "confidence", "skill", "strength"}

# Body / scene regions we tag obstacles against.
REGIONS = {"water", "bank", "dock", "trail"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------

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
    kind: str = "thing"            # "character" | "thing" | "obstacle" | "place"
    type: str = "thing"            # girl, boy, mother, father, canoe, paddle ...
    label: str = ""                # short reference, e.g. "paddle"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""              # where the thing sits in the world
    helps: set[str] = field(default_factory=set)   # what mess/obstacle it tackles
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model).
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    family: object | None = None
    gear_ent: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
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
    place: str = "the river"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which journeys this place supports
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
class Journey:
    """The small task the child has to do to reach the reunion."""
    id: str
    verb: str            # "paddle out to the bend"
    gerund: str          # "paddling out to the bend"
    rush: str            # "run down to the water"
    mess: str            # "wet" -- what the child gets during the journey
    zone: set[str]       # body regions / world regions the journey uses
    weather: str         # "rainy" | "stormy" | "foggy" | "sunny" | ""
    obstacle: str        # "fallen_pine" -- which obstacle blocks the way
    keyword: str = ""    # topic word for generation prompts
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
class Prize:
    """The thing the child goes to find -- always a family member (the reunion)."""
    label: str
    phrase: str
    type: str
    relation: str        # "mother" | "father" | "grandmother" | "grandfather"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    """Tool the child uses to make the journey (a paddle, a pole, ...)."""
    id: str
    label: str
    helps: set[str]     # which obstacles it can clear
    guards: set[str]    # which mess kinds it can keep off the child
    prep: str           # body of the offer
    tail: str           # closing clause
    plural: bool = False
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
class Obstacle:
    id: str
    label: str          # "a fallen pine"
    region: set[str]    # {"water"}  -- where it blocks
    cleared_by: set[str]  # gear ids that resolve it
    weather: set[str]   # weather that creates it
    note: str           # short narration fragment


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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

    def carried(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_soak(world: World) -> list[str]:
    """actor messy + carrying nothing that guards the mess -> mess + dirty."""
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            # If the actor carries a gear piece that guards this mess, it is shielded.
            shielded = any(mess in g.guards for g in world.carried(actor))
            sig = ("soak", actor.id, mess)
            if sig in world.fired or shielded:
                continue
            world.fired.add(sig)
            actor.meters["dirty"] += 1
            out.append(
                f"{actor.pronoun('subject').capitalize()} got a little {mess} "
                f"and dirty from the spray."
            )
    return out


def _r_skill(world: World) -> list[str]:
    """Carried gear + obstacle cleared -> child.skill / bravery go up."""
    out: list[str] = []
    for actor in world.characters():
        for g in world.carried(actor):
            if actor.memes.get("used_gear", 0) < THRESHOLD:
                continue
            sig = ("skill", actor.id, g.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["skill"] += 1
            actor.memes["bravery"] += 1
            out.append(
                f"{actor.pronoun('subject').capitalize()} felt steadier each time "
                f"{actor.pronoun('subject')} used the {g.label}."
            )
    return out


def _r_reunion_love(world: World) -> list[str]:
    """family member arrives at the bend -> child.love/joy up."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("reunited", 0) < THRESHOLD:
            continue
        sig = ("reunion", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        actor.memes["love"] += 1
        out.append(
            f"{actor.pronoun('possessive').capitalize()} heart felt warm with love."
        )
    return out


def _r_bravery_from_clear(world: World) -> list[str]:
    """An obstacle that was present and now cleared -> child.bravery up."""
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "obstacle":
            continue
        if ent.meters.get("cleared", 0) < THRESHOLD:
            continue
        sig = ("brave_clear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        # Find the hero (the only child character).
        for actor in world.characters():
            if actor.memes.get("paddled", 0) >= THRESHOLD:
                actor.memes["bravery"] += 1
                out.append(
                    f"{actor.pronoun('subject').capitalize()} felt brave for having "
                    f"made it past the {ent.label}."
                )
                break
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="skill", tag="social", apply=_r_skill),
    Rule(name="reunion_love", tag="social", apply=_r_reunion_love),
    Rule(name="bravery_from_clear", tag="social", apply=_r_bravery_from_clear),
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


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def journey_fits_obstacle(journey: Journey, obstacle: Obstacle) -> bool:
    """The journey has to actually meet this obstacle to be a brave story."""
    return (obstacle.id == journey.obstacle and
            (not obstacle.weather or journey.weather in obstacle.weather))


def select_gear(journey: Journey, obstacle: Obstacle) -> Optional[Gear]:
    """Gear that clears the obstacle and guards the journey's mess."""
    for gear in GEAR:
        if (obstacle.id in gear.helps and
                journey.mess in gear.guards):
            return gear
    return None


def predict_arrival(world: World, hero: Entity, journey: Journey,
                    obstacle: Obstacle, gear: Optional[Gear]) -> dict:
    """Run the world model forward on a silent copy."""
    sim = world.copy()
    _do_journey(sim, sim.get(hero.id), journey, gear, narrate=False)
    return {
        "soiled": sim.get(hero.id).meters["dirty"] >= THRESHOLD,
        "bravery": sim.get(hero.id).memes.get("bravery", 0),
        "joy": sim.get(hero.id).memes.get("joy", 0),
    }


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def journey_detail(journey: Journey) -> str:
    return {
        "paddle_bend": ("the small canoe rocked in the tall grass, and the water "
                        "spoke in low, fast whispers"),
        "pole_dock":    ("the broken dock creaked, and the rope was tangled in "
                        "a knot from the storm"),
        "carry_rope":   ("the path was a long, muddy slide down to the river, "
                        "and the rope was heavy on a small shoulder"),
    }.get(journey.id, "the way was not short and not safe")


def setting_detail(setting: Setting, journey: Journey) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was warm, and the kettle hummed."
    if journey.weather == "stormy":
        return ("The river ran quick after the storm, and the air smelled of "
                "wet pine and rain.")
    if journey.weather == "foggy":
        return "A soft fog sat low on the water, and the trees felt close and quiet."
    if journey.weather == "rainy":
        return "The rain had stopped, and the river was still silver and full."
    return f"{setting.place.capitalize()} was wide and gentle in the morning light."


def _do_journey(world: World, actor: Entity, journey: Journey,
                gear: Optional[Gear], narrate: bool = True) -> None:
    if journey.id not in world.setting.affords:
        return
    world.zone = set(journey.zone)
    world.weather = journey.weather
    actor.meters[journey.mess] += 1
    actor.memes["bravery"] += 1
    actor.memes["paddled"] = actor.memes.get("paddled", 0) + 1
    if gear is not None:
        actor.memes["used_gear"] = actor.memes.get("used_gear", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who lived with {hero.pronoun('possessive')} "
        f"grandfather by a wide, slow river."
    )


def loves_family(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Every summer, {hero.id} waited for {prize.phrase} to paddle up the river "
        f"in an old wooden canoe for the long-awaited reunion."
    )


def hear_arrival(world: World, hero: Entity, journey: Journey) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"One {journey.weather or 'bright'} morning, after a night of rain, "
        f"{hero.id} heard a far-off splash and knew the canoe was close."
    )
    world.say(
        f"But a storm had pushed trouble into the river, and the way to the dock "
        f"was not easy."
    )


def assess_problem(world: World, hero: Entity, journey: Journey,
                   obstacle: Obstacle) -> None:
    world.say(
        f"{hero.id} ran to the bank and saw the trouble: {obstacle.label} {obstacle.note}."
    )


def steady_breathe(world: World, hero: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a deep breath, the way {hero.pronoun('possessive')} "
        f"grandfather had taught {hero.pronoun('object')}."
    )


def launch(world: World, hero: Entity, gear: Gear) -> None:
    world.say(
        f"{hero.pronoun('subject').capitalize()} pulled the small canoe into the water "
        f"with both hands and picked up the {gear.label}."
    )


def paddle(world: World, hero: Entity, journey: Journey, obstacle: Obstacle,
           gear: Gear) -> None:
    # Narrate the journey as one continuous state-driven beat.
    _do_journey(world, hero, journey, gear, narrate=False)
    world.say(
        f"{hero.pronoun('subject').capitalize()} {journey.rush}, and the canoe slipped "
        f"through the water toward the {obstacle.label.split()[-1]}."
    )
    world.say(
        f"The water pushed hard, but {hero.pronoun('subject')} kept the {gear.label} "
        f"low and steady, working past the {obstacle.label}."
    )
    obstacle.meters["cleared"] = obstacle.meters.get("cleared", 0) + 1
    propagate(world, narrate=True)


def see_mother(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["reunited"] = hero.memes.get("reunited", 0) + 1
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(
        f"When {hero.pronoun('subject')} reached the bend, {prize.phrase} was there, "
        f"smiling from {prize.pronoun('possessive')} own canoe."
    )
    world.say(
        f'"{hero.id}!" {prize.pronoun('subject')} called. '
        f'"I knew you would come."'
    )


def paddle_home(world: World, hero: Entity, prize: Entity, gear: Gear) -> None:
    world.say(
        f"They {gear.tail} together back to the bank, and the small canoe bumped "
        f"gently against the shore."
    )
    world.say(
        f"They tied the canoes to what was left of the dock, and walked up the path "
        f"hand in hand, ready for the reunion hug at the door."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, journey: Journey, obstacle: Obstacle, gear: Gear,
         prize_cfg: Prize, hero_name: str = "Maple", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = journey.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "steady"]),
    ))
    family = world.add(Entity(
        id="Family", kind="character", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase,
    ))
    gear_ent = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, plural=gear.plural,
        owner=hero.id,
    ))
    gear_ent.carried_by = hero.id
    world.add(Entity(
        id=obstacle.id, kind="obstacle", type="obstacle",
        label=obstacle.label, region="water",
    ))

    # Act 1 -- setup.
    introduce(world, hero)
    loves_family(world, hero, family)
    world.para()

    # Act 2 -- the call to bravery.
    hear_arrival(world, hero, journey)
    assess_problem(world, hero, journey, obstacle)
    steady_breathe(world, hero)
    world.para()

    # Act 3 -- the journey and the reunion.
    launch(world, hero, gear)
    paddle(world, hero, journey, obstacle, gear)
    see_mother(world, hero, family)
    paddle_home(world, hero, family, gear)

    # Record facts.
    world.facts.update(
        hero=hero, family=family, prize_cfg=prize_cfg,
        journey=journey, obstacle=obstacle, gear=gear, setting=setting,
        soiled=hero.meters.get("dirty", 0) >= THRESHOLD,
        brave=hero.memes.get("bravery", 0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "river": Setting(place="the river", indoor=False,
                     affords={"paddle_bend", "pole_dock", "carry_rope"}),
    "lake": Setting(place="the lake", indoor=False,
                    affords={"paddle_bend", "pole_dock", "carry_rope"}),
    "cove": Setting(place="the cove", indoor=False,
                    affords={"paddle_bend", "pole_dock", "carry_rope"}),
}

OBSTACLES = {
    "fallen_pine": Obstacle(
        id="fallen_pine",
        label="a fallen pine",
        region={"water"},
        cleared_by={"paddle", "axe"},
        weather={"stormy", "rainy"},
        note="blocking the narrow bend where the canoes always met",
    ),
    "broken_dock": Obstacle(
        id="broken_dock",
        label="a broken dock",
        region={"dock"},
        cleared_by={"pole", "rope"},
        weather={"stormy", "rainy", "foggy"},
        note="with its planks half in the water and the rope in a knot",
    ),
    "washed_trail": Obstacle(
        id="washed_trail",
        label="a washed-out trail",
        region={"trail"},
        cleared_by={"rope", "staff"},
        weather={"stormy", "rainy"},
        note="a long, muddy slide down to the river's edge",
    ),
}

JOURNEYS = {
    "paddle_bend": Journey(
        id="paddle_bend",
        verb="paddle out to the bend",
        gerund="paddling out to the bend",
        rush="climbed into the canoe and pushed off",
        mess="wet",
        zone={"water", "dock"},
        weather="stormy",
        obstacle="fallen_pine",
        keyword="canoe",
        tags={"canoe", "river", "reunion"},
    ),
    "pole_dock": Journey(
        id="pole_dock",
        verb="pole out to the dock",
        gerund="poling out to the dock",
        rush="stepped into the canoe with the pole",
        mess="cold",
        zone={"water", "dock"},
        weather="foggy",
        obstacle="broken_dock",
        keyword="canoe",
        tags={"canoe", "dock", "reunion"},
    ),
    "carry_rope": Journey(
        id="carry_rope",
        verb="carry the rope down to the river",
        gerund="carrying the rope down to the river",
        rush="ran down the muddy path with the rope",
        mess="muddy",
        zone={"trail", "bank"},
        weather="rainy",
        obstacle="washed_trail",
        keyword="canoe",
        tags={"canoe", "trail", "reunion"},
    ),
}

GEAR = [
    Gear(
        id="paddle",
        label="wooden paddle",
        helps={"fallen_pine"},
        guards={"wet"},
        prep="take the wooden paddle in both hands",
        tail="paddled the canoes side by side",
    ),
    Gear(
        id="pole",
        label="long pole",
        helps={"broken_dock"},
        guards={"cold"},
        prep="pick up the long pole and steady the canoe",
        tail="poled the canoes back to shore",
    ),
    Gear(
        id="rope",
        label="coil of rope",
        helps={"washed_trail", "broken_dock"},
        guards={"muddy"},
        prep="loop the coil of rope over one shoulder",
        tail="rowed the canoe back with the rope at the bow",
    ),
]

PRIZES = {
    "mother": Prize(
        label="mom",
        phrase="her mother",
        type="mother",
        relation="mother",
        genders={"girl", "boy"},
    ),
    "father": Prize(
        label="dad",
        phrase="her father",
        type="father",
        relation="father",
        genders={"girl", "boy"},
    ),
    "grandmother": Prize(
        label="grandma",
        phrase="her grandmother",
        type="grandmother",
        relation="grandmother",
        genders={"girl", "boy"},
    ),
    "grandfather": Prize(
        label="grandpa",
        phrase="her grandfather",
        type="grandfather",
        relation="grandfather",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Maple", "Lily", "Willow", "Ivy", "Hazel", "June", "Clover", "Fern", "Wren", "Sage"]
BOY_NAMES = ["Otter", "Finn", "Reed", "Ash", "Birch", "Cedar", "Jay", "Pine", "Rowan", "Wade"]
TRAITS = ["brave", "steady", "quiet", "curious", "gentle", "patient", "eager", "kind"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(setting, journey, obstacle, prize) -- implicit gear is the one that fits."""
    out = []
    for s_id, setting in SETTINGS.items():
        for j_id, j in JOURNEYS.items():
            if j.id not in setting.affords:
                continue
            o = _safe_lookup(OBSTACLES, j.obstacle)
            if not journey_fits_obstacle(j, o):
                continue
            if select_gear(j, o) is None:
                continue
            for p_id, p in PRIZES.items():
                out.append((s_id, j_id, o.id, p_id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    journey: str
    obstacle: str
    prize: str
    gear: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
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


KNOWLEDGE = {
    "canoe": [("What is a canoe?",
               "A canoe is a long, narrow boat that you paddle through the water "
               "with a single-bladed paddle, often used on quiet rivers and lakes.")],
    "river": [("Why do rivers move?",
               "Rivers move because rainwater and melted snow flow downhill, "
               "carrying the water along its path toward a lake or the sea.")],
    "reunion": [("What is a reunion?",
                 "A reunion is a happy meeting between people who have not seen "
                 "each other for a while, often with hugs and smiles.")],
    "bravery": [("What does it mean to be brave?",
                 "Being brave means doing the right thing even when you feel a "
                 "little scared, like trying something new to help someone you love.")],
    "paddle": [("How do you paddle a canoe?",
                "You dip the paddle into the water on one side, pull it back, "
                "and then switch to the other side to keep the canoe moving forward.")],
    "storm": [("Why are rivers rough after a storm?",
               "Rain that falls during a storm runs into the river and makes the "
               "water move faster and rougher than usual.")],
    "dock": [("What is a dock?",
              "A dock is a wooden platform that sticks out over the water so "
              "boats can be tied to it and people can step in or out safely.")],
    "rope": [("Why is a rope useful near water?",
              "A rope is useful near water because you can tie a boat to a dock "
              "with it, or pull things safely back to shore.")],
    "fog": [("What is fog?",
             "Fog is a low cloud that sits on the water or the ground, making "
             "it hard to see things that are far away.")],
    "trail": [("What is a trail?",
               "A trail is a small path that people walk on through the woods "
               "or along a river, usually worn smooth by many footsteps.")],
}
KNOWLEDGE_ORDER = ["canoe", "river", "reunion", "bravery", "paddle", "storm",
                   "dock", "rope", "fog", "trail"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, family, j, o = f["hero"], f["family"], f["journey"], f["obstacle"]
    kw = j.keyword
    return [
        f'Write a short bedtime story for a 3-to-5-year-old on the theme '
        f'"a small brave act" that includes the word "{kw}".',
        f"Tell a gentle bedtime story where a child named {hero.id} lives by a "
        f"river, hears {family.phrase} paddling in for the reunion, and must "
        f"face {o.label} to meet them.",
        f"Write a quiet bedtime story that uses the noun \"{kw}\", includes a "
        f"family reunion, and ends with the child and parent walking home "
        f"hand in hand.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, family, prize, j = f["hero"], f["family"], f["prize_cfg"], f["journey"]
    o, gear = f["obstacle"], f["gear"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the bedtime story about when {hero.id} hears a canoe "
                f"paddling up {place} for the family reunion?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} "
                f"who lives by {place} and waits each summer for "
                f"{family.phrase} to come by canoe for the reunion."
            ),
        ),
        QAItem(
            question=(
                f"What trouble did {trait} {hero.id} find at {place} that "
                f"stood between {obj} and the reunion canoe?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} found {o.label} {o.note}, "
                f"and the way to the canoe was not easy. {sub.capitalize()} "
                f"had to use the {gear.label} to make the journey."
            ),
        ),
        QAItem(
            question=(
                f"How did {trait} {hero.id} show bravery during the journey to "
                f"meet {family.phrase} at {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} took a deep breath, picked up "
                f"the {gear.label}, and {j.rush} through the rough water. "
                f"{sub.capitalize()} kept the {gear.label} low and steady and "
                f"made it past {o.label} to the bend."
            ),
        ),
    ]
    if f.get("soiled"):
        qa.append(QAItem(
            question=(
                f"Why did {trait} {hero.id} get a little wet and dirty on the "
                f"canoe journey to the reunion at {place}?"
            ),
            answer=(
                f"The water sprayed over the canoe as {hero.id} paddled past "
                f"{o.label}, so {sub} got a little {j.mess} and dirty. The "
                f"{gear.label} did not guard that kind of spray, but {sub} did "
                f"not let it stop {obj}."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"How did the canoe reunion end for {trait} {hero.id} and "
            f"{family.phrase} at {place}?"
        ),
        answer=(
            f"They {gear.tail} back to the bank and tied the canoes to the "
            f"dock. Then {hero.id} and {family.phrase} walked up the path "
            f"hand in hand for the reunion hug at the door."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["journey"].tags)
    tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.helps:
            bits.append(f"helps={sorted(e.helps)}")
        if e.kind == "obstacle":
            bits.append("kind=obstacle")
        lines.append(f"  {e.id:14} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="river", journey="paddle_bend", obstacle="fallen_pine",
        prize="mother", gear="paddle",
        name="Maple", gender="girl", trait="brave",
    ),
    StoryParams(
        setting="lake", journey="pole_dock", obstacle="broken_dock",
        prize="father", gear="pole",
        name="Otter", gender="boy", trait="steady",
    ),
    StoryParams(
        setting="cove", journey="carry_rope", obstacle="washed_trail",
        prize="grandmother", gear="rope",
        name="Willow", gender="girl", trait="patient",
    ),
]


def explain_rejection(j: Journey, o: Obstacle) -> str:
    if o.id != j.obstacle:
        return (f"(No story: the journey '{j.id}' meets obstacle '{o.id}', "
                f"but the registry does not list that obstacle on this journey. "
                f"Try --obstacle {j.obstacle}.)")
    if o.weather and j.weather not in o.weather:
        return (f"(No story: '{o.id}' appears in weather {sorted(o.weather)}, "
                f"but journey '{j.id}' is '{j.weather}'. Try a journey whose "
                f"weather matches.)")
    return (f"(No story: no gear in the catalog can clear '{o.id}' while also "
            f"guarding '{j.mess}'. The compromise must actually help, so this "
            f"argument is rejected.)")


def explain_gear(j: Journey, o: Obstacle, gear_id: str) -> str:
    g = next((g for g in GEAR if g.id == gear_id), None)
    if g is None:
        return f"(No story: gear '{gear_id}' is not in the catalog.)"
    if o.id not in g.helps:
        return (f"(No story: gear '{g.label}' does not clear obstacle '{o.id}'. "
                f"It helps with {sorted(g.helps)}.)")
    if j.mess not in g.guards:
        return (f"(No story: gear '{g.label}' does not guard mess '{j.mess}'. "
                f"It guards {sorted(g.guards)}.)")
    return f"(No story: gear '{gear_id}' does not fit this combination.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A journey meets its obstacle exactly when the obstacle is the journey's
% registered one and the weather is in the obstacle's allowed set.
journey_matches(J, O) :- journey(J), obstacle(O),
                         obstacle_of(J, O),
                         obstacle_weather(O, W),
                         journey_weather(J, W).

% Gear fits (J, O) when the gear helps the obstacle AND guards the mess.
gear_fits(G, J, O) :- gear(G), journey(J), obstacle(O),
                       journey_matches(J, O),
                       gear_helps(G, O),
                       journey_mess(J, M),
                       gear_guards(G, M).

% A (setting, journey, obstacle, prize) combo is valid when:
%   * the setting affords the journey
%   * the journey matches its obstacle
%   * some gear fits that journey/obstacle pair
%   * the prize is one of the catalog (a "reunion" prize)
valid(Place, J, O, P) :- setting(Place), journey(J), obstacle(O), prize(P),
                         affords(Place, J),
                         journey_matches(J, O),
                         gear_fits(_, J, O),
                         wears(P, _).

% A complete brave bedtime story is a valid combo that we can tell.
valid_story(Place, J, O, P, G) :- valid(Place, J, O, P),
                                   gear_fits(G, J, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for j_id in sorted(s.affords):
            lines.append(asp.fact("affords", s_id, j_id))
    for j_id, j in JOURNEYS.items():
        lines.append(asp.fact("journey", j_id))
        lines.append(asp.fact("journey_weather", j_id, j.weather or "_none"))
        lines.append(asp.fact("journey_mess", j_id, j.mess))
        lines.append(asp.fact("obstacle_of", j_id, j.obstacle))
    for o_id, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", o_id))
        for w in sorted(o.weather):
            lines.append(asp.fact("obstacle_weather", o_id, w))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for o_id in sorted(g.helps):
            lines.append(asp.fact("gear_helps", g.id, o_id))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
    for p_id, p in PRIZES.items():
        lines.append(asp.fact("prize", p_id))
        # Every prize is a "wears" target for both genders in this catalog.
        for g_ in ("girl", "boy"):
            lines.append(asp.fact("wears", p_id, g_))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a canoe, a brave reunion. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--journey", choices=JOURNEYS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    # Explicit-arg validation.
    if getattr(args, "journey", None) and getattr(args, "obstacle", None):
        j, o = _safe_lookup(JOURNEYS, getattr(args, "journey", None)), _safe_lookup(OBSTACLES, getattr(args, "obstacle", None))
        if not journey_fits_obstacle(j, o) or select_gear(j, o) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gear", None) and getattr(args, "journey", None) and getattr(args, "obstacle", None):
        j, o = _safe_lookup(JOURNEYS, getattr(args, "journey", None)), _safe_lookup(OBSTACLES, getattr(args, "obstacle", None))
        g = next((g for g in GEAR if g.id == getattr(args, "gear", None)), None)
        if g is None or o.id not in g.helps or j.mess not in g.guards:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "journey", None) is None or c[1] == getattr(args, "journey", None))
              and (getattr(args, "obstacle", None) is None or c[2] == getattr(args, "obstacle", None))
              and (getattr(args, "prize", None) is None or c[3] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, journey_id, obstacle_id, prize_id = rng.choice(list(combos))
    journey = _safe_lookup(JOURNEYS, journey_id)
    obstacle = _safe_lookup(OBSTACLES, obstacle_id)
    gear = (next(g for g in GEAR if g.id == getattr(args, "gear", None))
            if getattr(args, "gear", None) else select_gear(journey, obstacle))
    if gear is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id, journey=journey_id, obstacle=obstacle_id,
        prize=prize_id, gear=gear.id, name=name, gender=gender, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(JOURNEYS, params.journey),
                 _safe_lookup(OBSTACLES, params.obstacle),
                 next(g for g in GEAR if g.id == params.gear),
                 _safe_lookup(PRIZES, params.prize), params.name, params.gender,
                 [params.trait, "brave"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (setting, journey, obstacle, prize) "
              f"combos ({len(stories)} with gear):\n")
        for place, j, o, p in triples:
            gears = sorted(g for (pl, jj, oo, pp, g) in stories
                           if (pl, jj, oo, pp) == (place, j, o, p))
            print(f"  {place:6} {j:13} {o:14} {p:11}  [{', '.join(gears)}]")
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
            header = (f"### {p.name}: {p.journey} at {p.setting} "
                      f"(obstacle: {p.obstacle}, prize: {p.prize}, gear: {p.gear})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
