#!/usr/bin/env python3
"""
storyworlds/worlds/junket_cue_humor_inner_monologue_sharing_tall.py
===================================================================

A small tall-tale storyworld about a carnival junket, a cue, a shy worry,
and a shared solution that turns a near-disaster into a laugh.

Premise:
- A child wants to join a grand junket through town.
- A cue is needed for the show to begin, but the hero's prop is misplaced.
- The hero's inner monologue spirals into comic worry.
- A helper shares a trick, and the group fixes the trouble together.

The world is modeled with physical meters and emotional memes:
- meters track tangible state like distance, noise, sparkle, and balance
- memes track feelings like confidence, worry, delight, and camaraderie

The story variants are constrained so the fix is always plausible:
- the junket must actually need the cue
- the cue must be lost, too small, too noisy, or otherwise unusable
- the shared fix must genuinely restore the cue
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cue: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class Cue:
    id: str
    label: str
    phrase: str
    fit: str
    fix: str
    size: str
    humorous_angle: str
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
class Junket:
    id: str
    label: str
    verb: str
    gerund: str
    start: str
    travel: str
    need: str
    cue_kind: str
    keyword: str = "junket"
    tags: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    offers: str
    shared_fix: str
    handoff: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
            self.trace_bits.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        if ("worry_echo", actor.id) in world.fired:
            continue
        world.fired.add(("worry_echo", actor.id))
        actor.memes["confidence"] = actor.memes.get("confidence", 0.0) - 0.5
        out.append(f"{actor.label_word} felt the worry thumping like a kettle drum.")
    return out


def _r_shared_fix(world: World) -> list[str]:
    out: list[str] = []
    cue = world.facts.get("cue_entity")
    if not cue:
        return out
    cue_ent: Entity = cue
    if cue_ent.meters.get("broken", 0.0) >= THRESHOLD and cue_ent.carried_by:
        if ("shared_fix", cue_ent.id) in world.fired:
            return out
        world.fired.add(("shared_fix", cue_ent.id))
        cue_ent.meters["broken"] = 0.0
        cue_ent.meters["usable"] = 1.0
        fixer = world.get(world.facts["helper"].id)
        hero = world.get(world.facts["hero"].id)
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        out.append(f"{fixer.label_word} shared a clever fix, and the cue came back ready as a rooster at dawn.")
    return out


CAUSAL_RULES = [
    Rule("worry", _r_worry),
    Rule("shared_fix", _r_shared_fix),
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


def _do_junket(world: World, actor: Entity, junket: Junket, narrate: bool = True) -> None:
    actor.meters["distance"] = actor.meters.get("distance", 0.0) + 1.0
    actor.memes["delight"] = actor.memes.get("delight", 0.0) + 1.0
    actor.meters["noise"] = actor.meters.get("noise", 0.0) + 1.0
    propagate(world, narrate=narrate)


def predict_problem(world: World, hero: Entity, junket: Junket, cue: Entity) -> dict:
    sim = world.copy()
    _do_junket(sim, sim.get(hero.id), junket, narrate=False)
    cue2 = sim.get(cue.id)
    return {
        "usable": cue2.meters.get("usable", 0.0) >= THRESHOLD and cue2.meters.get("broken", 0.0) < THRESHOLD,
        "worry": sim.get(hero.id).memes.get("worry", 0.0),
    }


def prize_at_risk(junket: Junket, cue: Cue) -> bool:
    return junket.cue_kind == cue.id and cue.fit in {"fits_junket", "fits_show", "fits_band"}


def select_helper(junket: Junket, cue: Cue) -> Optional[Helper]:
    for h in HELPERS:
        if cue.fix == h.shared_fix:
            return h
    return None


SETTINGS = {
    "town": Place(name="the town square", indoors=False, affords={"march", "sing", "show"}),
    "fair": Place(name="the county fair", indoors=False, affords={"march", "show"}),
    "station": Place(name="the train station", indoors=True, affords={"show"}),
    "hill": Place(name="the windy hill", indoors=False, affords={"march"}),
}

JUNKETS = {
    "march": Junket(
        id="march",
        label="a grand junket parade",
        verb="join the junket parade",
        gerund="parading with the procession",
        start="the parade rolled forward",
        travel="marched down the lane",
        need="a start cue",
        cue_kind="whistle",
        tags={"junket", "cue", "humor", "sharing"},
    ),
    "show": Junket(
        id="show",
        label="a barn-busting show junket",
        verb="take part in the show junket",
        gerund="showing off in the traveling act",
        start="the curtains waited like sleepy eyelids",
        travel="performed under the striped tent",
        need="a stage cue",
        cue_kind="bell",
        tags={"junket", "cue", "humor", "sharing"},
    ),
    "song": Junket(
        id="song",
        label="a rolling song junket",
        verb="ride along on the song junket",
        gerund="singing on the road",
        start="the chorus gathered its breath",
        travel="sang across the square",
        need="a tune cue",
        cue_kind="kazoo",
        tags={"junket", "cue", "humor", "sharing"},
    ),
}

CUES = {
    "whistle": Cue(
        id="whistle",
        label="whistle cue",
        phrase="a polished whistle cue",
        fit="fits_junket",
        fix="shared_breath",
        size="small",
        humorous_angle="it could squeak louder than a goose in boots",
    ),
    "bell": Cue(
        id="bell",
        label="bell cue",
        phrase="a bright brass bell cue",
        fit="fits_show",
        fix="shared_rhyme",
        size="medium",
        humorous_angle="it rang like a spoon in a tub",
    ),
    "kazoo": Cue(
        id="kazoo",
        label="kazoo cue",
        phrase="a tiny kazoo cue",
        fit="fits_band",
        fix="shared_song",
        size="small",
        humorous_angle="it buzzed like a bee with a secret",
    ),
}

HELPERS = [
    Helper(
        id="Aunt Pru",
        label="Aunt Pru",
        offers="a pocketful of timing",
        shared_fix="shared_breath",
        handoff="shared a deep breath and a counting wink",
    ),
    Helper(
        id="Milo",
        label="Milo",
        offers="a tune that sticks like honey",
        shared_fix="shared_song",
        handoff="shared a tune from his hat brim",
    ),
    Helper(
        id="Nell",
        label="Nell",
        offers="a rhyme as neat as a fence rail",
        shared_fix="shared_rhyme",
        handoff="shared a rhyme and a tap of her spoon",
    ),
]

HERO_NAMES = ["June", "Toby", "Rosa", "Pip", "Annie", "Ned", "Lula", "Eli"]
TRAITS = ["bold", "curious", "spirited", "sly", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    junket: str
    cue: str
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
    for place, setting in SETTINGS.items():
        for jid in setting.affords:
            jk = _safe_lookup(JUNKETS, jid)
            cue = _safe_lookup(CUES, jk.cue_kind)
            if prize_at_risk(jk, cue):
                combos.append((place, jid, cue.id))
    return combos


ASP_RULES = r"""
junket_needs_cue(J, C) :- junket(J), cue(C), cue_kind(J, C).
problem(P, J, C) :- place(P), affords(P, J), junket_needs_cue(J, C), cue(C), cue_kind(J, C).
fix_available(J, C) :- problem(_, J, C), helper_fix(C, _).
valid_story(P, J, C) :- problem(P, J, C), fix_available(J, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for jid, j in JUNKETS.items():
        lines.append(asp.fact("junket", jid))
        lines.append(asp.fact("cue_kind", jid, j.cue_kind))
    for cid, c in CUES.items():
        lines.append(asp.fact("cue", cid))
        lines.append(asp.fact("fits", cid, c.fit))
        lines.append(asp.fact("helper_fix", cid, c.fix))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("shared_fix", h.shared_fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def tell(place: Place, junket: Junket, cue_def: Cue, hero_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name, traits=[trait, "little"]))
    helper_def = random.choice(HELPERS)
    helper = world.add(Entity(id=helper_def.id, kind="character", type="adult", label=helper_def.label))
    cue = world.add(Entity(
        id=cue_def.id, type="thing", label=cue_def.label, phrase=cue_def.phrase,
        caretaker=helper.id, carried_by=helper.id,
    ))
    world.facts = {"hero": hero, "helper": helper, "cue_entity": cue, "junket": junket, "cue_def": cue_def}

    hero.memes["joy"] = 1.0
    hero.memes["confidence"] = 1.0

    world.say(f"{hero_name} had a {trait} grin and a heart set on the {junket.label}.")
    world.say(f"{hero_name} loved the whole tall-tale bustle of it, because {junket.start} and everyone was laughing already.")
    world.say(f"But the junket needed {junket.need}, and the cue was as important as a rooster in a clock shop.")
    world.para()
    world.say(f"One bright day at {place.name}, {hero_name} wanted to {junket.verb}.")
    world.say(f"{hero_name} looked for {cue_def.phrase}, while the little mind inside the hero's hat went round and round.")

    hero.memes["worry"] = 1.0
    if predict_problem(world, hero, junket, cue)["usable"]:
        world.say(f"The cue looked fine, so the tall tale would not have any trouble at all.")
    else:
        world.say(f'“What if the cue is lost?” {hero_name} wondered, and the inner monologue got louder than a washboard band.')
        world.say(f"{hero_name} tried to remember whether the cue had been left in a boot, a pocket, or maybe the moon.")
        cue.meters["broken"] = 1.0
        cue.carried_by = helper.id

    world.para()
    world.say(f"{helper.label} came by, saw the face, and said, “Easy now, little whirlwind.”")
    world.say(f"{helper.label} offered {helper.offers} and {helper.handoff}.")
    helper.memes["kindness"] = 1.0
    if cue.meters.get("broken", 0.0) >= THRESHOLD:
        world.say(f"Together they fixed the {cue.label_word}, and it popped back into shape like a jack-in-the-box with manners.")
        cue.meters["usable"] = 1.0
        cue.meters["broken"] = 0.0
    propagate(world, narrate=True)

    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(f"Then {hero_name} shared a laugh with {helper.label}, and the two of them passed the cue hand to hand.")
    world.say(f"At last, {junket.travel}, the cue sounded true, and the whole crowd moved off like a line of cheerful geese.")
    world.say(f"{hero_name} felt big as a barn and light as a feather, all at once.")
    world.facts.update({
        "hero": hero,
        "helper": helper,
        "cue": cue,
        "junket": junket,
        "place": place,
        "resolved": True,
    })
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    junket = _safe_fact(world, f, "junket")
    cue_def = _safe_fact(world, f, "cue_def")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a short tall tale for a child about a {junket.label} where a {cue_def.label} gets fixed by sharing.',
        f"Tell a humorous story in which {hero.label_word} has an inner monologue about losing a cue, then {helper.label} helps.",
        f'Write a playful story using the words "junket" and "cue" that ends with people sharing a solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    junket = _safe_fact(world, f, "junket")
    cue_def = _safe_fact(world, f, "cue_def")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {hero.label_word} want to do at {place.name}?",
            answer=f"{hero.label_word} wanted to {junket.verb}, because the big junket felt like a parade with extra sparkle.",
        ),
        QAItem(
            question=f"Why did {hero.label_word} get worried about the {cue_def.label}?",
            answer=f"{hero.label_word} worried because the cue was needed to start the {junket.label}, and without it the show could not get going.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label_word}?",
            answer=f"{helper.label} helped by sharing {helper.offers} and fixing the cue together with {hero.label_word}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the cue worked again, the worry faded, and {hero.label_word} joined the junket with a laugh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a junket?",
            answer="A junket is a lively trip or outing, often with a lot of noise, movement, and people going together.",
        ),
        QAItem(
            question="What is a cue?",
            answer="A cue is a signal or small thing that tells everyone it is time to begin.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use what you have, or helping together so one person is not alone.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the funny part of a story that makes people smile or laugh.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="town", junket="march", cue="whistle", name="June", trait="bold"),
    StoryParams(place="fair", junket="show", cue="bell", name="Toby", trait="curious"),
    StoryParams(place="station", junket="show", cue="bell", name="Rosa", trait="cheerful"),
    StoryParams(place="hill", junket="march", cue="whistle", name="Pip", trait="stubborn"),
    StoryParams(place="town", junket="song", cue="kazoo", name="Lula", trait="sly"),
]


def explain_rejection(junket: Junket, cue_def: Cue) -> str:
    return (
        f"(No story: the {junket.label} needs a {cue_def.label}, but this world has no "
        f"plausible shared fix for that pairing.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: junket, cue, humor, inner monologue, sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--junket", choices=JUNKETS)
    ap.add_argument("--cue", choices=CUES)
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
    if getattr(args, "junket", None) and getattr(args, "cue", None):
        jk, cue = _safe_lookup(JUNKETS, getattr(args, "junket", None)), _safe_lookup(CUES, getattr(args, "cue", None))
        if not prize_at_risk(jk, cue):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "junket", None) is None or c[1] == getattr(args, "junket", None))
              and (getattr(args, "cue", None) is None or c[2] == getattr(args, "cue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, junket, cue = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, junket=junket, cue=cue, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(JUNKETS, params.junket), _safe_lookup(CUES, params.cue), params.name, params.trait)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, junket, cue) combos:\n")
        for place, junket, cue in combos:
            print(f"  {place:10} {junket:8} {cue:8}")
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
            header = f"### {p.name}: {p.junket} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
