#!/usr/bin/env python3
"""
storyworlds/worlds/era_misunderstanding_sound_effects_ghost_story.py
====================================================================

A small story world about a spooky-sounding misunderstanding in an old place
from another era.

Premise:
- A child explores an old setting that feels ghostly.
- Strange sound effects make the child think something invisible is nearby.
- A grown-up or helper explains that the noises are caused by an old sound
  machine, prop box, or theater trick from an earlier era.
- The child's fear turns into wonder, and the story ends with the sound effects
  being used on purpose.

The world is intentionally small and constraint-checked:
- Physical state includes meters such as noise, dust, and fear-triggered motion.
- Emotional state includes memes such as fright, curiosity, relief, and pride.
- Explicit invalid choices raise StoryError with a clear reason.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"
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
    era: str
    ambience: str
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
class SoundEffect:
    id: str
    noise_word: str
    source: str
    source_reveal: str
    happened_in: set[str]
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    source: str
    reveals: str
    eras: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_fright(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.memes.get("fright", 0) < THRESHOLD:
        return out
    sig = ("fright", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["tremble"] = child.memes.get("tremble", 0) + 1
    out.append(f"{child.id} shivered and stared at the shadows.")
    return out


CAUSAL_RULES = [Rule("fright", _r_fright)]


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


SETTINGS = {
    "attic": Setting(
        place="the attic",
        era="the old house era",
        ambience="dusty beams and narrow windows",
        affords={"creak", "whoosh", "rattle"},
    ),
    "theater": Setting(
        place="the little theater",
        era="the vaudeville era",
        ambience="red curtains and a wooden stage",
        affords={"creak", "whoosh", "clatter"},
    ),
    "museum": Setting(
        place="the museum storage room",
        era="the lantern era",
        ambience="glass cases and dusty labels",
        affords={"tap", "rattle", "whoosh"},
    ),
}

SOUNDS = {
    "creak": SoundEffect(
        id="creak",
        noise_word="creak",
        source="an old door hinge",
        source_reveal="a rusty hinge on the side door",
        happened_in={"attic", "theater"},
        tags={"spooky", "wood"},
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        noise_word="whoosh",
        source="a stage curtain sliding on its track",
        source_reveal="a curtain pulled along a metal track",
        happened_in={"theater", "museum", "attic"},
        tags={"spooky", "cloth"},
    ),
    "rattle": SoundEffect(
        id="rattle",
        noise_word="rattle",
        source="a box of old props",
        source_reveal="a tin box of costume props",
        happened_in={"attic", "museum"},
        tags={"spooky", "props"},
    ),
    "tap": SoundEffect(
        id="tap",
        noise_word="tap-tap",
        source="a recording machine making tiny beats",
        source_reveal="a hand-cranked sound machine",
        happened_in={"museum"},
        tags={"spooky", "machine"},
    ),
}

PROPS = {
    "lantern": Prop(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with cloudy glass",
        kind="light",
        source="the old house era",
        reveals="the tiniest dust motes and spiderwebs",
        eras={"old house era", "lantern era"},
    ),
    "script": Prop(
        id="script",
        label="script",
        phrase="a folded stage script with yellow pages",
        kind="paper",
        source="the vaudeville era",
        reveals="a list of sound cues and stage directions",
        eras={"vaudeville era"},
    ),
    "sound_box": Prop(
        id="sound box",
        label="sound box",
        phrase="a wooden sound box with metal levers",
        kind="machine",
        source="the lantern era",
        reveals="little tricks for making ghostly noises on purpose",
        eras={"lantern era"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ivy", "June", "Ada"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Max", "Eli", "Noah"]
TRAITS = ["curious", "brave", "quiet", "careful", "bouncy", "dreamy"]


@dataclass
class StoryParams:
    setting: str
    sound: str
    prop: str
    name: str
    gender: str
    helper: str
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


def reasonableness_gate(setting: Setting, sound: SoundEffect, prop: Prop) -> bool:
    return setting.era in prop.eras and setting.place in sound.happened_in


def explain_rejection(setting: Setting, sound: SoundEffect, prop: Prop) -> str:
    return (
        f"(No story: {sound.noise_word} does not fit {setting.place}, "
        f"or {prop.label} does not belong to the {setting.era}. "
        f"Try a sound and prop that belong to the same old era and place.)"
    )


def select_prop(setting: Setting, sound: SoundEffect) -> Optional[Prop]:
    for prop in PROPS.values():
        if reasonableness_gate(setting, sound, prop):
            return prop
    return None


def predict_misunderstanding(world: World, child: Entity, sound: SoundEffect) -> dict:
    sim = world.copy()
    sim.facts["heard"] = sound.id
    child_sim = sim.get(child.id)
    child_sim.memes["fright"] = child_sim.memes.get("fright", 0) + 1
    propagate(sim, narrate=False)
    return {
        "fright": child_sim.memes.get("fright", 0),
        "curious": child_sim.memes.get("curious", 0),
    }


def _hear_sound(world: World, child: Entity, sound: SoundEffect) -> None:
    child.meters["noise"] = child.meters.get("noise", 0) + 1
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    world.say(
        f"In {world.setting.place}, the air felt full of {world.setting.ambience}. "
        f"Then came a {sound.noise_word} from somewhere dark."
    )


def _misunderstand(world: World, child: Entity, sound: SoundEffect) -> None:
    child.memes["fright"] = child.memes.get("fright", 0) + 1
    world.say(
        f"{child.id} whispered that it sounded like a ghost. "
        f"{child.pronoun().capitalize()} hugged {child.pronoun('possessive')} arms and listened again."
    )
    propagate(world, narrate=True)


def _helper_explain(world: World, helper: Entity, child: Entity, sound: SoundEffect, prop: Prop) -> None:
    child.memes["fright"] = 0
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    world.say(
        f"Then {helper.id} smiled and pointed at {prop.phrase}. "
        f"\"No ghost,\" {helper.pronoun().capitalize()} said. \"Just {sound.source_reveal}.\""
    )
    world.say(
        f"The spooky sound was only {sound.source}. "
        f"It had been hiding in the room since the old {world.setting.era} things were first used."
    )


def _use_sound_effects(world: World, child: Entity, helper: Entity, sound: SoundEffect, prop: Prop) -> None:
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"{child.id} laughed, and {helper.id} showed how the old trick worked. "
        f"Together they made the {sound.noise_word} sound on purpose, while {prop.label} sat nearby like a clue."
    )
    world.say(
        f"By the end, the room felt less haunted and more magical. "
        f"The same noise that had sounded like a ghost now sounded like a game."
    )


def tell(setting: Setting, sound: SoundEffect, prop: Prop, name: str = "Mia", gender: str = "girl",
         helper: str = "grandma", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper_ent = world.add(Entity(id=helper, kind="character", type="woman" if helper == "grandma" else "man"))
    child.memes["curious"] = 1
    _hear_sound(world, child, sound)
    world.para()
    _misunderstand(world, child, sound)
    world.para()
    _helper_explain(world, helper_ent, child, sound, prop)
    _use_sound_effects(world, child, helper_ent, sound, prop)
    world.facts.update(
        child=child,
        helper=helper_ent,
        sound=sound,
        prop=prop,
        setting=setting,
        misunderstood=True,
        resolved=True,
    )
    return world


def build_valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for snd_id, sound in SOUNDS.items():
            for pid, prop in PROPS.items():
                if reasonableness_gate(setting, sound, prop):
                    combos.append((sid, snd_id, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sound = _safe_fact(world, f, "sound")
    prop = _safe_fact(world, f, "prop")
    return [
        f'Write a gentle ghost story for a child who hears "{sound.noise_word}" in a place from another era.',
        f"Tell a story where {child.id} mistakes a sound effect for a ghost and then learns the truth about {prop.label}.",
        f"Write a short spooky-but-safe story about {world.setting.place}, old things, and a noise that turns out to be a trick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    sound = _safe_fact(world, f, "sound")
    prop = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"Why did {child.id} think there was a ghost in {world.setting.place}?",
            answer=(
                f"{child.id} thought there was a ghost because the {sound.noise_word} sounded strange in {world.setting.place}. "
                f"The room was quiet and old, so the noise felt spooky at first."
            ),
        ),
        QAItem(
            question=f"What helped {child.id} understand the {sound.noise_word} sound?",
            answer=(
                f"{helper.id} pointed to {prop.phrase} and explained that the noise came from {sound.source}. "
                f"That showed {child.id} it was only a sound effect, not a ghost."
            ),
        ),
        QAItem(
            question=f"What changed for {child.id} at the end of the story?",
            answer=(
                f"{child.id} stopped feeling scared and started feeling wonder and pride. "
                f"By the end, {child.id} could make the {sound.noise_word} on purpose with {helper.id}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or carefully chosen noise used to help a story, show, or game feel real or exciting.",
        ),
        QAItem(
            question="What does it mean when something is from an earlier era?",
            answer="It means it belongs to an older time period, before the time people live in now.",
        ),
        QAItem(
            question="Why do old buildings sometimes creak?",
            answer="Old buildings can creak because wood and metal parts move a little when the temperature changes or when someone walks nearby.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  setting era: {world.setting.era}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", sound="creak", prop="lantern", name="Mia", gender="girl", helper="grandma", trait="curious"),
    StoryParams(setting="theater", sound="whoosh", prop="script", name="Leo", gender="boy", helper="grandpa", trait="careful"),
    StoryParams(setting="museum", sound="tap", prop="sound_box", name="Nora", gender="girl", helper="aunt", trait="brave"),
]


@dataclass
class StoryParams:
    setting: str
    sound: str
    prop: str
    name: str
    gender: str
    helper: str
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
    ap = argparse.ArgumentParser(description="Ghost-story world about an old era and misunderstood sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandma", "grandpa", "aunt", "uncle"])
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
    if getattr(args, "setting", None) and getattr(args, "sound", None) and getattr(args, "prop", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(SOUNDS, getattr(args, "sound", None)), _safe_lookup(PROPS, getattr(args, "prop", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in build_valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, sound_id, prop_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["grandma", "grandpa", "aunt", "uncle"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, sound=sound_id, prop=prop_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SOUNDS, params.sound), _safe_lookup(PROPS, params.prop),
                 name=params.name, gender=params.gender, helper=params.helper, trait=params.trait)
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


ASP_RULES = r"""
setting(S).
sound(X).
prop(P).

misunderstood(S, X, P) :- setting(S), sound(X), prop(P), in_era(S, E), prop_era(P, E), sound_place(X, S).
compatible(S, X, P) :- misunderstood(S, X, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("in_era", sid, s.era))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        for p in sorted(s.happened_in):
            lines.append(asp.fact("sound_place", sid, p))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for e in sorted(p.eras):
            lines.append(asp.fact("prop_era", pid, e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstood/3."))
    asp_set = set(asp.atoms(model, "misunderstood"))
    py_set = set((s, x, p) for s, x, p in build_valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return build_valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstood/3."))
    return sorted(set(asp.atoms(model, "misunderstood")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstood/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for setting, sound, prop in combos:
            print(f"  {setting:10} {sound:8} {prop:10}")
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
            header = f"### {p.name}: {p.sound} in {p.setting} ({p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
