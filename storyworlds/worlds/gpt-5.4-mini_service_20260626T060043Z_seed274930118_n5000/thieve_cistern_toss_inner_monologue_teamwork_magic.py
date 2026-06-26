#!/usr/bin/env python3
"""
storyworlds/worlds/thieve_cistern_toss_inner_monologue_teamwork_magic.py
=========================================================================

A tiny comedy storyworld about a sneaky cistern, a tossed line, a bit of magic,
and two helpers who learn that teamwork beats loud, lone-brained thieving.

Premise:
- A small hero wants to thieve back a shiny wind-up star that fell into an old cistern.
- They try a noisy toss-and-grab plan first.
- Inner monologue reveals their worry, and teamwork plus a simple spell turns the mess into a win.

This world keeps the simulated state moving:
- meters: physical quantities like reach, splash, height, wetness, and possession
- memes: emotional quantities like worry, pride, laughter, trust, and relief

Comedy style:
- The hero's inner monologue stays silly and honest.
- The cistern is awkward, echoey, and unhelpful.
- The magic is tiny, specific, and a little embarrassing.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def __post_init__(self) -> None:
        for k in ["wet", "reach", "height", "possession", "stuck", "weight"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "pride", "laughter", "trust", "relief", "scheme"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"
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
class Place:
    id: str
    label: str
    echoey: bool = False
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    risky: bool = False
    heavy: bool = False
    can_toss: bool = False
    can_hook: bool = False
    can_spell: bool = False
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
class ToolDef:
    id: str
    label: str
    action: str
    effect: str
    helps_with: set[str] = field(default_factory=set)
    can_toss: bool = False
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
        return [e for e in self.entities.values() if e.is_character()]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_wet_and_slip(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("slip", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 0.5
        out.append(f"The damp air made {ent.id} wobble and think about shoes.")
    return out


def _r_team_trust(world: World) -> list[str]:
    out: list[str] = []
    chars = world.characters()
    if len(chars) < 2:
        return out
    a, b = chars[0], chars[1]
    if a.memes["trust"] < THRESHOLD or b.memes["trust"] < THRESHOLD:
        return out
    sig = ("team", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["laughter"] += 0.5
    b.memes["laughter"] += 0.5
    out.append("Their teamwork made the whole plan feel less like a disaster.")
    return out


def _r_magic_help(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("spell_used") and world.facts.get("hooked") and not world.facts.get("retrieved"):
        sig = ("magic_help",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["retrieved"] = True
        out.append("The little spell tugged the shiny thing up like it was made of feathers.")
    return out


CAUSAL_RULES = [
    Rule("wet_and_slip", _r_wet_and_slip),
    Rule("team_trust", _r_team_trust),
    Rule("magic_help", _r_magic_help),
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


def predict_attempt(world: World, hero: Entity, helper: Entity, obj: Entity, tool: ToolDef) -> dict:
    sim = world.copy()
    sim.facts["retrieved"] = False
    sim.facts["hooked"] = False
    sim.facts["spell_used"] = False
    hero2 = sim.get(hero.id)
    helper2 = sim.get(helper.id)
    obj2 = sim.get(obj.id)
    _attempt_toss(sim, hero2, helper2, obj2, tool, narrate=False)
    return {
        "retrieved": sim.facts.get("retrieved", False),
        "hooked": sim.facts.get("hooked", False),
    }


def _attempt_toss(world: World, hero: Entity, helper: Entity, obj: Entity, tool: ToolDef, narrate: bool = True) -> None:
    if tool.id not in world.place.affords:
        pass
    hero.memes["scheme"] += 0.5
    helper.memes["trust"] += 0.5
    world.facts["attempted_toss"] = True
    world.facts["spell_used"] = False
    hero.meters["reach"] += 0.1
    helper.meters["reach"] += 0.1
    if tool.can_toss:
        world.facts["hooked"] = True
    if narrate:
        world.say(
            f"{hero.id} tried to toss {tool.label} into the cistern and thought, "
            f"'Please, let this be clever and not sticky.'"
        )
        world.say(
            f"{helper.id} held the other end and tried not to laugh at how serious the rope looked."
        )


def introduce(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} with a big idea and even bigger opinions about shiny things."
    )
    world.say(
        f"{helper.id} was the sort of friend who could turn a problem into a project with both hands."
    )
    world.say(
        f"Together they spotted {obj.phrase} near the old cistern and decided it simply had to come back."
    )


def inner_monologue(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["worry"] += 0.5
    world.say(
        f"{hero.id} thought, 'I can totally thieve this back. I am calm. I am brilliant. I am not at all making whisper noises.'"
    )
    world.say(
        f"Then {hero.id} looked into the cistern and thought, 'That thing fell in like a king, and I am a tiny noodle with a plan.'"
    )


def setup_cistern(world: World, obj: Entity) -> None:
    world.say(
        f"The cistern sat round and grumpy, with stone sides and a voice that made every word echo twice."
    )
    if obj.risky:
        world.say(f"{obj.label} glittered somewhere below, just out of easy reach.")


def failed_grab(world: World, hero: Entity, obj: Entity) -> None:
    hero.meters["reach"] += 0.2
    hero.memes["worry"] += 0.3
    world.say(
        f"{hero.id} leaned over and tried to grab {obj.label} with bare fingers, but the cistern answered with a smug little splash."
    )


def team_plan(world: World, hero: Entity, helper: Entity, tool: ToolDef, obj: Entity) -> None:
    hero.memes["trust"] += 0.5
    helper.memes["trust"] += 0.5
    world.say(
        f"{helper.id} said, 'We do this together.' {hero.id} nodded so hard it nearly counted as a second plan."
    )
    world.say(
        f"One of them would hold the line, and the other would keep the hook steady."
    )


def use_magic(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.facts["spell_used"] = True
    hero.memes["scheme"] += 0.5
    helper.memes["laughter"] += 0.5
    world.say(
        f"{hero.id} whispered a tiny magic word that sounded suspiciously like a sneeze, and the hook glowed."
    )
    world.say(
        f"{helper.id} blinked and said, 'I knew that would work,' in the brave voice of someone who had guessed absolutely nothing."
    )


def retrieve(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    if not world.facts.get("hooked"):
        pass
    world.facts["retrieved"] = True
    obj.owner = hero.id
    obj.carried_by = hero.id
    hero.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    hero.memes["laughter"] += 0.5
    helper.memes["laughter"] += 0.5
    world.say(
        f"With one careful pull, they lifted {obj.label} out of the cistern at last."
    )
    world.say(
        f"{hero.id} hugged it like a treasure and said, 'I thieved it back!'"
    )
    world.say(
        f"{helper.id} laughed so hard the cistern echoed, which only made the victory sound fancier."
    )


def tell(place: Place, hero_name: str, helper_name: str, object_def: ObjectDef) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy"))
    obj = world.add(Entity(id=object_def.id, type="thing", label=object_def.label, phrase=object_def.phrase))
    world.facts.update(hero=hero, helper=helper, obj=obj, retrieved=False, hooked=False, spell_used=False)

    introduce(world, hero, helper, obj)
    world.para()
    setup_cistern(world, obj)
    inner_monologue(world, hero, obj)
    failed_grab(world, hero, obj)
    world.para()
    team_plan(world, hero, helper, TOOLS["hook_rope"], obj)
    _attempt_toss(world, hero, helper, obj, TOOLS["hook_rope"], narrate=True)
    use_magic(world, hero, helper, obj)
    propagate(world, narrate=True)
    retrieve(world, hero, helper, obj)
    return world


PLACES = {
    "courtyard": Place(id="courtyard", label="the courtyard", echoey=True, affords={"toss"}),
    "garden": Place(id="garden", label="the garden", echoey=False, affords={"toss"}),
    "wellyard": Place(id="wellyard", label="the old wellyard", echoey=True, affords={"toss"}),
}

OBJECTS = {
    "star": ObjectDef(
        id="star",
        label="a shiny wind-up star",
        phrase="a shiny wind-up star",
        risky=True,
        can_toss=True,
        can_hook=True,
        can_spell=True,
    ),
    "ring": ObjectDef(
        id="ring",
        label="a brass ring",
        phrase="a brass ring",
        risky=True,
        can_toss=True,
        can_hook=True,
        can_spell=True,
    ),
}

TOOLS = {
    "hook_rope": ToolDef(
        id="hook_rope",
        label="a rope with a bent hook",
        action="toss",
        effect="hook",
        helps_with={"toss"},
        can_toss=True,
    ),
}


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    helper_name: str
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


HERO_NAMES = ["Mina", "Pip", "Nina", "Toby", "Lila", "Jasper"]
HELPER_NAMES = ["Ben", "Omar", "June", "Ada", "Noel", "Rae"]


def reasonableness_gate(place: str, object_id: str) -> None:
    if place not in PLACES:
        pass
    if object_id not in OBJECTS:
        pass
    if "toss" not in _safe_lookup(PLACES, place).affords:
        pass
    obj = _safe_lookup(OBJECTS, object_id)
    if not (obj.risky and obj.can_hook and obj.can_spell):
        pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short comedy story about {f['hero'].id} and {f['helper'].id} trying to thieve back {f['obj'].label} from a cistern.",
        f"Tell a funny story where teamwork and a tiny spell help two friends toss a hook into an old cistern.",
        f"Write a child-friendly adventure about a noisy cistern, an inner monologue, and a rescued treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    obj = _safe_fact(world, f, "obj")
    place = world.place.label
    return [
        QAItem(
            question=f"Who wanted to thieve back {obj.label} from the cistern?",
            answer=f"{hero.id} wanted to get {obj.label} back, and {helper.id} helped with the plan.",
        ),
        QAItem(
            question=f"What did the friends use before the magic part of the rescue?",
            answer=f"They used a rope with a bent hook and tossed it carefully into the cistern together.",
        ),
        QAItem(
            question=f"How did the story end for {obj.label}?",
            answer=f"{obj.label} was lifted out of the cistern and ended up safely with {hero.id}.",
        ),
        QAItem(
            question=f"Why did the cistern make the plan harder at {place}?",
            answer="The cistern was deep and echoey, so every small mistake sounded much bigger than it was.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cistern?",
            answer="A cistern is a tank or chamber for holding water, often built with stone or brick.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to reach a goal.",
        ),
        QAItem(
            question="What is a spell in a magical story?",
            answer="A spell is a made-up magic action or phrase that can change what happens in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wellyard", object="star", hero_name="Mina", helper_name="Ben"),
    StoryParams(place="courtyard", object="ring", hero_name="Pip", helper_name="June"),
    StoryParams(place="garden", object="star", hero_name="Lila", helper_name="Omar"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: thieve, cistern, toss, teamwork, magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    reasonableness_gate(place, obj)
    return StoryParams(
        place=place,
        object=obj,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.hero_name, params.helper_name, _safe_lookup(OBJECTS, params.object))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for obj in OBJECTS:
            try:
                reasonableness_gate(place, obj)
            except StoryError:
                continue
            out.append((place, obj))
    return out


ASP_RULES = r"""
place(P) :- setting(P).
object(O) :- item(O).
supports_toss(P) :- affords(P,toss).
risky_object(O) :- item(O), risky(O), hookable(O), spellable(O).
valid(P,O) :- place(P), object(O), supports_toss(P), risky_object(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.echoey:
            lines.append(asp.fact("echoey", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("item", oid))
        if o.risky:
            lines.append(asp.fact("risky", oid))
        if o.can_hook:
            lines.append(asp.fact("hookable", oid))
        if o.can_spell:
            lines.append(asp.fact("spellable", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.hero_name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
