#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/artery_nuisance_curiosity_sharing_rhyme.py
======================================================================================================================

A nursery‑rhyme‑style story domain: a curious child lives beside a busy road
(the artery) that is a nuisance. The child longs to cross to share a rhyme with
a friend. The parent teaches a safe way: hold hands and wait for a quiet moment,
then sing the rhyme together. The domain models physical noise/danger, emotional
curiosity/joy, and a shared rhyme (the prize).

Seed words:  artery, nuisance
Features:    curiosity, sharing, rhyme
Style:       nursery rhyme

Concepts:
- Artery: a wide, busy road (the setting).
- Nuisance: the noise and danger of the road.
- Curiosity: the child's desire to cross and see what's on the other side.
- Sharing: the act of singing/reciting a rhyme together.
- Rhyme: the treasured verses (a prize the child carries).

World model: the road has meters `noise` and `danger`. The child has memes
`curiosity`, `fear`, `joy`. The rhyme is an object with a `shared` flag.
Rules: crossing alone raises danger; holding parent's hand reduces danger;
singing the rhyme after a safe crossing raises joy and marks the rhyme as shared.
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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entity
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
    kind: str = "thing"           # "character" | "object"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    parent: object | None = None
    prize_entity: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain dataclasses
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
class Road:
    name: str = "the big road"
    artery: bool = True
    noise: float = 0.0
    danger: float = 0.5

    road: object | None = None
    def description(self) -> str:
        if self.noise >= THRESHOLD * 2:
            return "a very noisy, busy artery"
        if self.noise >= THRESHOLD:
            return "a noisy, busy road"
        return "a quiet road"
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
class Rhyme:
    title: str
    lines: str
    theme: str = "friendship"
    shared: bool = False
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
class Setting:
    place: str = "the village"
    road: Road = field(default_factory=Road)
    affords: set[str] = field(default_factory=lambda: {"cross", "sing"})
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str] = field(default_factory=set)
    weather: str = ""
    keyword: str = ""
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
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.rhyme: Optional[Rhyme] = None
        self.crossed: bool = False
        self.sang: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.rhyme = self.rhyme
        clone.crossed = self.crossed
        clone.sang = self.sang
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: callable
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


def _r_nuisance_noise(world: World) -> list[str]:
    """The road's noise grows when cars pass (simulated by activity)."""
    out = []
    road = world.setting.road
    if road.noise < THRESHOLD:
        return out
    sig = ("noise", id(road))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    # increase danger
    road.danger += 0.3
    out.append("The traffic hummed and the artery grew loud.")
    return out


def _r_crossing_danger(world: World) -> list[str]:
    """If the child tries to cross alone, danger rises."""
    child = None
    for e in world.characters():
        if e.memes.get("crossing_attempt", 0) >= THRESHOLD and not world.facts.get("holding_hand"):
            child = e
            break
    if child is None:
        return []
    sig = ("danger", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.setting.road.danger += 0.5
    out = ["That would be too risky for a little one."]
    return out


def _r_rhyme_shared(world: World) -> list[str]:
    """After crossing safely and singing, the rhyme is shared."""
    if world.sang and world.crossed and world.rhyme and not world.rhyme.shared:
        world.rhyme.shared = True
        return ["The tidy rhyme was shared at last!"]
    return []


CAUSAL_RULES = [
    Rule("noise", "physical", _r_nuisance_noise),
    Rule("danger", "physical", _r_crossing_danger),
    Rule("shared", "social", _r_rhyme_shared),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries (nursery‑rhyme flavored)
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting(
        place="the little village",
        road=Road(name="the wide artery", noise=2.0, danger=0.8),
        affords={"cross", "sing"},
    ),
    "lane": Setting(
        place="the quiet lane",
        road=Road(name="the narrow lane", noise=0.5, danger=0.2),
        affords={"cross", "sing"},
    ),
}

RHymes = [
    Rhyme(title="Curious Cat", lines="Curious cat, where have you been?\nI've been to London to visit the Queen.",
          theme="curiosity"),
    Rhyme(title="Sharing Song", lines="Share your bread, share your bed,\nHappy heart with words well said.",
          theme="sharing"),
    Rhyme(title="Twinkle, Twinkle, Little Star", lines="Twinkle, twinkle, little star,\nHow I wonder what you are!",
          theme="wonder"),
]

ACTIVITIES = {
    "cross": Activity(
        id="cross",
        verb="cross the busy artery",
        gerund="crossing the road",
        rush="dash across without looking",
        mess="danger",
        soil="risky",
        zone={"body"},
        weather="",
        keyword="cross",
        tags={"crossing", "road"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing a rhyme together",
        gerund="singing a rhyme",
        rush="shout the rhyme alone",
        mess="noise",
        soil="unshared",
        zone={"voice"},
        weather="",
        keyword="rhyme",
        tags={"rhyme", "singing"},
    ),
}

PRIZES = {
    "rhyme_card": Prize(
        label="rhyme card",
        phrase="a brightly colored rhyme card with golden letters",
        type="prize",
        genders={"girl", "boy"},
    ),
    "tidy_rhyme": Prize(
        label="tidy rhyme",
        phrase="a tidy little rhyme about friendship",
        type="prize",
        genders={"girl", "boy"},
    ),
}

CHILD_NAMES = ["Lily", "Tom", "Molly", "Jack", "Emma", "Sam"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "gentle", "brave", "kind"]


def valid_combos():
    """Return list of (setting_key, activity_id, prize_id) that work."""
    combos = []
    for sk, s in SETTINGS.items():
        for aid in s.affords:
            for pk, p in PRIZES.items():
                combos.append((sk, aid, pk))
    return combos


# ---------------------------------------------------------------------------
# Rhyme selection
# ---------------------------------------------------------------------------
def pick_rhyme(rng: random.Random, theme: str = "curiosity") -> Rhyme:
    candidates = [r for r in RHymes if r.theme == theme] or RHymes
    return rng.choice(candidates)


# ---------------------------------------------------------------------------
# Story verbs (nursery‑rhyme prose)
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, road: Road) -> None:
    world.say(
        f"In {world.setting.place}, there lived a {child.type} named {child.id}, "
        f"with eyes full of wonder and a heart full of glee."
    )


def near_artery(world: World, child: Entity, road: Road) -> None:
    world.say(
        f"Beside the {road.description()} they would stand, "
        f"watching the cars zoom across the land."
    )
    if road.noise >= THRESHOLD:
        world.say("The artery roared — a terrible sound, a nuisance that shook the ground.")


def curiosity_wakes(world: World, child: Entity, rhyme: Rhyme) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"\"What lies beyond?\" the little one thought. "
        f"\"My friend waits there, a rhyme I've brought.\""
    )
    world.say(f"They clutched their {rhyme.title.lower()} card, so fine and true, "
              f"and dreamed of the words they'd share anew.")


def parent_warn(world: World, parent: Entity, child: Entity, road: Road) -> None:
    parent.memes["fear"] += 0.5
    world.say(
        f"But Mother said, \"Hold, my dear, stay near! "
        f"That artery is a nuisance, loud and severe. "
        f"You cannot cross it on your own; you'll need my hand, and we'll walk slow.\""
    )


def child_try(world: World, child: Entity) -> None:
    child.memes["crossing_attempt"] += 1
    world.say(
        f"{child.id} took a step, then another, so quick, "
        f"wishing the road were no more than a stick."
    )
    propagate(world)


def hand_hold(world: World, parent: Entity, child: Entity) -> None:
    world.facts["holding_hand"] = True
    child.memes["fear"] = 0.0
    parent.memes["joy"] += 0.5
    world.say(
        f"Mother's hand grasped {child.id}'s small hand then, "
        f"\"Together we'll cross, just count to ten.\""
    )


def cross_safely(world: World, child: Entity, parent: Entity) -> None:
    world.crossed = True
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.setting.road.danger = 0.0
    world.say(
        f"One, two, three — they stepped with care, "
        f"the roaring artery — now just air."
    )
    world.say("On the other side, the friend appeared, with a wave and a cheer.")


def share_rhyme(world: World, child: Entity, rhyme: Rhyme) -> None:
    world.sang = True
    child.memes["joy"] += 1
    rhyme.shared = True
    world.say(
        f"The tidy rhyme they sang aloud, "
        f"a happy, sharing, joyful crowd."
    )
    world.say(f"\"{rhyme.lines}\"")
    propagate(world)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting_key: str, activity_id: str, prize_id: str,
         child_name: str = "Lily", child_type: str = "girl",
         traits: list[str] = None,
         parent_type: str = "mother",
         seed: int = 0) -> World:
    setting = _safe_lookup(SETTINGS, setting_key)
    road = setting.road
    rng = random.Random(seed)
    rhyme = pick_rhyme(rng, "curiosity")

    world = World(setting)
    world.rhyme = rhyme

    child = world.add(Entity(id=child_name, kind="character", type=child_type,
                              label=child_name, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                               label="Parent", meters={}, memes={}))
    prize_entity = world.add(Entity(
        id="prize", kind="object", type="prize", label=prize_id,
        phrase=_safe_lookup(PRIZES, prize_id).phrase, owner=child.id,
        meters={}, memes={},
    ))

    # Act 1
    introduce(world, child, road)
    near_artery(world, child, road)
    curiosity_wakes(world, child, rhyme)

    # Act 2
    world.para()
    parent_warn(world, parent, child, road)
    child_try(world, child)
    hand_hold(world, parent, child)

    # Act 3
    world.para()
    cross_safely(world, child, parent)
    share_rhyme(world, child, rhyme)

    # store facts for QA
    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        road=road,
        rhyme=rhyme,
        prize=_safe_lookup(PRIZES, prize_id),
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    child_name: str
    child_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generation prompts and QA
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


KNOWLEDGE = {
    "crossing": [
        ("Why is it important to hold an adult's hand when crossing a busy road?",
         "A busy road has many cars that move fast. Holding a grown-up's hand keeps "
         "you safe because they can see and stop for cars."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is a short poem or song where the words at the end sound similar. "
         "Children learn and share rhymes for fun."),
        ("Why do people share rhymes?",
         "Sharing rhymes makes people happy and helps friends feel close. It is like "
         "a little gift of words."),
    ],
    "road": [
        ("What is an artery?",
         "An artery is a big, important road where many cars travel. It can be noisy "
         "and dangerous for little ones to cross alone."),
    ],
    "nuisance": [
        ("What does 'nuisance' mean?",
         "A nuisance is something that bothers you. A noisy road can be a nuisance "
         "because it is loud and makes it hard to play quietly."),
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling of wanting to know or learn something new. "
         "It makes children ask questions and explore."),
    ],
    "sharing": [
        ("Why is sharing good?",
         "Sharing makes other people happy and builds friendship. When you share "
         "a rhyme or a toy, you both feel good."),
    ],
}

KNOWLEDGE_ORDER = ["crossing", "rhyme", "road", "nuisance", "curiosity", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    road = _safe_fact(world, f, "road")
    rhyme = _safe_fact(world, f, "rhyme")
    return [
        f'Write a short nursery‑rhyme story for a child about curiosity, sharing, and a road.',
        f"Tell a gentle story where a {child.type} named {child.id} wants to cross "
        f"{road.name} to share a rhyme with a friend, and a parent helps them do it safely.",
        f"Write a rhyming story that includes the words 'artery' and 'nuisance' and "
        f"ends with the child singing '{rhyme.title}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    road = _safe_fact(world, f, "road")
    rhyme = _safe_fact(world, f, "rhyme")
    prize = _safe_fact(world, f, "prize")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do near {road.name}?",
            answer=f"{child.id} wanted to cross {road.name} to share a rhyme with a friend. "
                   f"{child.pronoun('possessive').capitalize()} {parent.type} helped {child.pronoun('object')} safe."
        ),
        QAItem(
            question=f"Why was {road.name} a nuisance?",
            answer=f"{road.name} was noisy with many cars, so it was dangerous to cross alone. "
                   f"That is why it was a nuisance for little {child.id}."
        ),
        QAItem(
            question=f"What rhyme did {child.id} share?",
            answer=f"{child.id} shared the rhyme '{rhyme.title}': \"{rhyme.lines}\"."
        ),
    ]
    # add a question about curiosity
    qa.append(QAItem(
        question=f"What made {child.id} want to cross the road?",
        answer=f"{child.pronoun('possessive').capitalize()} curiosity about the friend and "
               f"the wish to share the rhyme made {child.pronoun('object')} want to cross."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"crossing", "rhyme", "road", "nuisance", "curiosity", "sharing"}
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
# ASP twin (simplified)
# ---------------------------------------------------------------------------
ASP_RULES = """
% A story is valid if setting has road, prize is a rhyme, child is curious.
valid_story(S, A, P, G) :- setting(S), activity(A), prize(P), gender(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_verify() -> int:
    # Just check facts parse (basic)
    import asp
    program = asp_facts() + "\n" + ASP_RULES
    try:
        _ = asp.one_model(program + "\n#show valid_story/4.")
        print("ASP verification passed (syntax OK).")
        return 0
    except Exception as e:
        print(f"ASP error: {e}")
        return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: curiosity, sharing, rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true",
                    help="render all valid combos (small set)")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or "cross"
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        child_name=name,
        child_gender=gender,
        parent_type=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.activity, params.prize,
                 params.child_name, params.child_gender,
                 [params.trait],
                 params.parent_type,
                 seed=params.seed if params.seed is not None else 0)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        # simple trace
        w = sample.world
        print("--- world trace ---")
        print(f"  road noise={w.setting.road.noise}, danger={w.setting.road.danger}")
        print(f"  crossed={w.crossed}, sang={w.sang}, rhyme_shared={w.rhyme.shared if w.rhyme else False}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode: valid combos via inline twin (symbolic only).")
        print("(No clingo dependency for minimal run.)")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []

    if getattr(args, "all", None):
        # curated: one combo per setting/prize/gender
        for sk in SETTINGS:
            for pk in PRIZES:
                for g in ["girl", "boy"]:
                    p = StoryParams(
                        setting=sk, activity="cross", prize=pk,
                        child_name=g.capitalize(), child_gender=g,
                        parent_type="mother", trait="curious",
                        seed=base_seed,
                    )
                    try:
                        sample = generate(p)
                        samples.append(sample)
                    except Exception as e:
                        print(f"Skipping {p}: {e}", file=sys.stderr)
    else:
        seen_stories = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                continue
            params.seed = seed
            try:
                sample = generate(params)
            except Exception as e:
                print(f"Generate error: {e}", file=sys.stderr)
                continue
            if sample.story in seen_stories:
                continue
            seen_stories.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### Story {i+1}: {sample.params.child_name}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
