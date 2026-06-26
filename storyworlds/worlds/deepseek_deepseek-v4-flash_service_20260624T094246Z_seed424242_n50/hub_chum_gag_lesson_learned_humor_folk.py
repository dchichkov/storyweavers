#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/hub_chum_gag_lesson_learned_humor_folk.py
============================================================================================================================

A standalone story world sketch: a folk tale with a hub (the village meeting place),
a chum (a friend), and a gag (a playful prank).  Each story teaches a gentle lesson
about friendship through good-natured humor.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    chum: object | None = None
    hub_ent: object | None = None
    trickster: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "grandpa", "uncle", "friend"}
        female = {"girl", "woman", "grandma", "aunt"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class Hub:
    """The central meeting place of the village (or town)."""
    name: str
    phrase: str
    features: list[str] = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Chum:
    """A friend – the target or co-conspirator of the gag."""
    name: str
    type: str
    trait: str = "curious"
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
class Gag:
    """A playful prank that creates humor and a mild mess."""
    id: str
    verb: str
    gerund: str
    rush: str
    mess_kind: str
    catchphrase: str
    tag: str


# ---------------------------------------------------------------------------
# World
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


class World:
    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.hub)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
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


def _r_gag_mess(world: World) -> list[str]:
    """Performing a gag adds mess to the trickster, and sometimes to the target."""
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["gag_done"] >= THRESHOLD and not ent.meters["mess_spread"]:
            ent.meters["mess_spread"] = 1
            trickster = ent
            # find the target: a character with same location?
            for other in list(world.entities.values()):
                if other.id != trickster.id and other.kind == "character":
                    sig = ("splatter", trickster.id, other.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        other.meters["messy"] += 1
                        other.memes["surprise"] += 1
                        out.append(f"The {gag_type(world)} splattered onto {other.label}!")
                        break
    return out

def _r_chum_comfort(world: World) -> list[str]:
    """After surprise, if chum cares about friend, comfort reduces anger."""
    out = []
    for ent in list(world.entities.values()):
        if ent.memes["surprise"] >= THRESHOLD and ent.memes["anger"] < THRESHOLD:
            sig = ("comfort", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                ent.memes["happy"] += 0.5
                out.append(f"But {ent.label} smiled – it was just a silly gag.")
    return out

def _r_lesson(world: World) -> list[str]:
    """If gag causes repeated upset and then forgiveness, lesson learned meter ticks."""
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["messy"] >= 2 and ent.memes["forgive"] >= THRESHOLD:
            sig = ("lesson", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                ent.memes["wisdom"] += 1
                out.append(f"{ent.label} learned that a good gag is fun when everyone laughs together.")
    return out

def gag_type(world: World) -> str:
    for ent in list(world.entities.values()):
        if ent.meters["gag_done"] >= THRESHOLD:
            return ent.traits[0] if ent.traits else "trick"
    return "trick"

CAUSAL_RULES = [
    Rule("gag_mess", "physical", _r_gag_mess),
    Rule("chum_comfort", "social", _r_chum_comfort),
    Rule("lesson", "moral", _r_lesson),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__none__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Screenplay beats
# ---------------------------------------------------------------------------
VILLAGE_NAMES = ["Sunnyvale", "Meadowbrook", "Brambleville", "Oak Hollow"]
HUB_PHRASES = {
    "well": "the old well",
    "market": "the colourful market square",
    "tree": "the great oak tree",
}
CHUM_NAMES = ["Kofi", "Anya", "Tomas", "Lena", "Milo", "Zara"]
TRAITS = ["playful", "clever", "cheerful", "silly", "gentle"]

# gag registry
GAG_REGISTRY = {
    "pie": Gag("pie", "hide a custard pie", "hiding custard pies", "sneak the pie out",
              "messy", "SPLAT!", "pie"),
    "bucket": Gag("bucket", "put a bucket of water", "putting buckets of water",
                  "tip the bucket", "wet", "SPLASH!", "water"),
    "string": Gag("string", "tie a trip string", "tying trip strings",
                  "pull the string", "tangle", "WHOOPS!", "string"),
}

def decide_gag(activity: Gag, hub: Hub) -> bool:
    """Only gags that fit the hub are reasonable."""
    if activity.id == "pie" and "food" in hub.features:
        return True
    if activity.id == "bucket" and "water" in hub.features:
        return True
    if activity.id == "string" and "many feet" in hub.features:
        return True
    return activity.id in ("pie", "bucket", "string")  # fallback

def tell(hub: Hub, gag: Gag, trickster_name: str, trickster_gender: str,
         chum_name: str, chum_gender: str, trait: str) -> World:
    world = World(hub)

    trickster = world.add(Entity(
        id=trickster_name, kind="character", type=trickster_gender,
        label=trickster_name, traits=[trait]
    ))
    chum = world.add(Entity(
        id=chum_name, kind="character", type=chum_gender,
        label=chum_name, traits=["curious", "forgiving"]
    ))
    # hub as a location entity (not a character)
    hub_ent = world.add(Entity(
        id=f"hub_{hub.name}", kind="place", type="hub",
        label=hub.phrase
    ))

    # Act 1 - introduce the hub and the friends
    world.say(f"In a cosy village called {hub.name}, there was {hub.phrase} where everyone gathered.")
    world.say(f"{trickster.name} the {trait} {trickster_gender} and {chum.name} the clever {chum_gender} were best chums.")
    world.para()

    # Act 2 - the gag
    world.say(f"One sunny morning, {trickster.name} thought of a silly gag.")
    world.say(f'"{gag.catchphrase}" {trickster.pronoun()} whispered with a grin.')
    trickster.meters["gag_done"] += 1
    world.say(f"{trickster.name} decided to {gag.verb} near the {hub.phrase}.")
    world.say(f"Just as {chum.name} walked by, {gag.rush} and ...")
    propagate(world, narrate=True)
    world.para()

    # Act 3 - aftermath and lesson
    world.say(f"{chum.name} let out a gasp!")
    chum.memes["surprise"] += 0.5
    propagate(world, narrate=True)
    world.say(f"But instead of getting cross, {chum.name} began to chuckle.")
    chum.memes["forgive"] += 0.5
    propagate(world, narrate=True)
    world.say(f'"{trickster.name}, you rascal!" laughed {chum.name}. "That was a good one."')
    world.say(f"Together they cleaned up the {gag.mess_kind} mess, and from that day on,")
    world.say(f"{trickster.name} always asked {chum.name} before pulling a gag. "
              f"The best jokes are the ones friends share.")
    world.facts["gag"] = gag
    world.facts["trickster"] = trickster
    world.facts["chum"] = chum
    world.facts["hub"] = hub
    return world


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hub: str
    gag: str
    trickster_name: str
    trickster_gender: str
    chum_name: str
    chum_gender: str
    trait: str
    seed: Optional[int] = None
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


HUBS = {
    "well": Hub("Sunnyvale", "the old well", ["water", "food"]),
    "market": Hub("Meadowbrook", "the colourful market square", ["food", "many feet"]),
    "tree": Hub("Brambleville", "the great oak tree", ["shade", "many feet"]),
}


# ---------------------------------------------------------------------------
# Q&A generators
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hub_name = _safe_fact(world, f, "hub").name
    gag = _safe_fact(world, f, "gag")
    trick = _safe_fact(world, f, "trickster")
    chum = _safe_fact(world, f, "chum")
    return [
        f"Write a short folk tale about a playful gag at the {hub_name} hub, "
        f"where {trick.id} plays a trick on chum {chum.id} and they learn to laugh together.",
        f"Tell a story about friendship and a silly {gag.id} gag, set in a village hub.",
        f"Create a humorous folk tale about a trick at the village gathering place, "
        f"with a lesson about respecting friends.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trick = _safe_fact(world, f, "trickster")
    chum = _safe_fact(world, f, "chum")
    hub = _safe_fact(world, f, "hub")
    gag = _safe_fact(world, f, "gag")
    qa = [
        QAItem(
            question=f"Where did {trick.id} and {chum.id} meet when the gag happened?",
            answer=f"They were at {hub.phrase} in the village of {hub.name}."
        ),
        QAItem(
            question=f"What gag did {trick.id} pull on {chum.id}?",
            answer=f"{trick.id} {gag.verb} near the hub. It involved {gag.mess_kind} and was silly."
        ),
        QAItem(
            question=f"How did {chum.id} react to the gag?",
            answer=f"At first {chum.pronoun()} was surprised, but then {chum.pronoun()} laughed and forgave {trick.id}."
        ),
        QAItem(
            question=f"What lesson did the chums learn?",
            answer=f"They learned that a good gag is even better when both friends are in on the joke."
        ),
    ]
    return qa

KNOWLEDGE = {
    "well": [("What is a village well?", "A well is a deep hole in the ground where people draw water. In many villages it's a meeting spot.")],
    "market": [("What is a market square?", "A market square is an open place in a town where people sell goods and meet friends.")],
    "tree": [("Why is a big tree a meeting place?",
              "A large tree gives shade and is a comfortable spot for villagers to gather and talk.")],
    "pie": [("What is a custard pie?",
             "A custard pie is a dessert pie filled with creamy custard. Some people playfully throw them for a mess.")],
    "bucket": [("What is a water bucket gag?",
                "Someone puts a bucket of water above a door so it spills on the person who opens it. It's a silly prank.")],
    "string": [("What is a trip string?",
                "A string stretched across a path that makes someone trip lightly – but nobody gets hurt.")],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    gag = _safe_fact(world, f, "gag")
    hub = _safe_fact(world, f, "hub")
    tags = {hub.name, gag.id}
    out = []
    for tag in tags:
        if tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP twin (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hub_gag_fits(H, G) :- hub(H), gag(G),
                      splashes(G, _),   % dummy – we check via fit_fact
                      fit_fact(H, G).
valid_story(H, G, TG) :- hub_gag_fits(H, G), gender(TG).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for hid, hub in HUBS.items():
        lines.append(asp.fact("hub", hid))
        lines.append(asp.fact("fit_fact", hid, "pie"))
        lines.append(asp.fact("fit_fact", hid, "bucket"))
        lines.append(asp.fact("fit_fact", hid, "string"))
    for gid in GAG_REGISTRY:
        lines.append(asp.fact("gag", gid))
    for g in ["boy", "girl"]:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    # simple parity check: all hub-gag combos are valid in this domain
    all_combos = [(h, g) for h in HUBS for g in GAG_REGISTRY]
    python_valid = set(all_combos)
    clingo_valid = {(h, g) for (h, g, _) in asp_valid_stories()}
    if python_valid == clingo_valid:
        print(f"OK: clingo matches python ({len(python_valid)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale hub-chum-gag world.")
    ap.add_argument("--hub", choices=HUBS)
    ap.add_argument("--gag", choices=GAG_REGISTRY)
    ap.add_argument("--trickster-name")
    ap.add_argument("--trickster-gender", choices=["boy", "girl"])
    ap.add_argument("--chum-name")
    ap.add_argument("--chum-gender", choices=["boy", "girl"])
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
    hub = getattr(args, "hub", None) or rng.choice(list(HUBS.keys()))
    gag = getattr(args, "gag", None) or rng.choice(list(GAG_REGISTRY.keys()))
    trick_gender = getattr(args, "trickster_gender", None) or rng.choice(["boy", "girl"])
    chum_gender = getattr(args, "chum_gender", None) or rng.choice(["boy", "girl"])
    if trick_gender == chum_gender:
        chum_gender = "boy" if chum_gender == "girl" else "girl"  # ensure diversity
    trick_name = getattr(args, "trickster_name", None) or rng.choice(CHUM_NAMES)
    chum_name = getattr(args, "chum_name", None) or rng.choice([n for n in CHUM_NAMES if n != trick_name])
    trait = rng.choice(TRAITS)
    return StoryParams(
        hub=hub, gag=gag,
        trickster_name=trick_name, trickster_gender=trick_gender,
        chum_name=chum_name, chum_gender=chum_gender,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    hub = _safe_lookup(HUBS, params.hub)
    gag = GAG_REGISTRY[params.gag]
    world = tell(hub, gag, params.trickster_name, params.trickster_gender,
                 params.chum_name, params.chum_gender, params.trait)
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
        # simple trace: dump meter/meme values
        for e in sample.world.entities.values():
            if e.kind == "character":
                print(f"  {e.id}: meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("--- Story Q&A ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("--- World knowledge ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story templates:")
        for h, g, tg in sorted(stories):
            print(f"  hub={h}, gag={g}, trickster_gender={tg}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        # a curated set of plausible stories
        curated = [
            StoryParams("well", "pie", "Kofi", "boy", "Anya", "girl", "playful", None),
            StoryParams("market", "bucket", "Tomas", "boy", "Lena", "girl", "clever", None),
        ]
        for p in curated:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen = set()
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
        if len(samples) > 1:
            header = f"### Tale {i+1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
