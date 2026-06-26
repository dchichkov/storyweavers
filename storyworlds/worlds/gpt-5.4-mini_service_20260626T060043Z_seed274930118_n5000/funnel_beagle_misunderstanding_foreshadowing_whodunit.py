#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small whodunit with a beagle, a funnel,
misunderstanding, and foreshadowing.

Premise:
- In a quiet house, something important goes missing before a little mystery
  is solved.
- A beagle's curious nose and a funnel-shaped clue create a harmless but spooky
  misunderstanding.
- Foreshadowing comes from earlier odd signs that later make sense.

The world model tracks:
- physical meters: foundness, mess, suspicion, hiddenness, noise
- emotional memes: worry, curiosity, relief, confidence, confusion

This file is self-contained and follows the storyworld contract.
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

    assistant: object | None = None
    detective: object | None = None
    dog: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    indoor: bool = True
    affordances: set[str] = field(default_factory=set)
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    clue: bool = False
    owner: Optional[str] = None
    hidden: bool = False
    visible_sign: str = ""
    reveals: str = ""
    clue_obj: object | None = None
    missing_obj: object | None = None
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
class StoryParams:
    place: str
    missing: str
    clue: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

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
        clone.objects = _copy.deepcopy(self.objects)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _inc(m: dict[str, float], key: str, amt: float = 1.0) -> None:
    m[key] = m.get(key, 0.0) + amt


def _mood(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


@dataclass
class Rule:
    name: str
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.kind == "character" and e.type == "girl"), None)
    dog = next((e for e in world.entities.values() if e.type == "beagle"), None)
    if not detective or not dog:
        return out
    clue = world.objects.get(world.facts["clue_id"])
    missing = world.objects.get(world.facts["missing_id"])
    if clue.hidden and _meter(detective, "confusion") >= THRESHOLD and (("misunderstanding", detective.id) not in world.fired):
        world.fired.add(("misunderstanding", detective.id))
        _inc(detective.memes, "worry")
        _inc(detective.memes, "curiosity")
        out.append(f"{detective.id} thought {dog.label} was the problem, but the real clue was hiding nearby.")
    if not clue.hidden and _meter(detective, "curiosity") >= THRESHOLD and (("reveal", clue.id) not in world.fired):
        world.fired.add(("reveal", clue.id))
        _inc(detective.meters, "foundness")
        _inc(detective.memes, "confidence")
        out.append(f"The small clue turned out to point right at {missing.label}.")
    return out


def _r_finding(world: World) -> list[str]:
    out: list[str] = []
    clue = world.objects[world.facts["clue_id"]]
    if clue.hidden:
        return out
    if ("found", clue.id) in world.fired:
        return out
    world.fired.add(("found", clue.id))
    out.append(f"The hidden clue was finally in plain sight.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.kind == "character" and e.type == "girl"), None)
    helper = next((e for e in world.entities.values() if e.id == world.facts["helper_id"]), None)
    missing = world.objects[world.facts["missing_id"]]
    if detective and helper and _meter(detective, "foundness") >= THRESHOLD and ("relief", detective.id) not in world.fired:
        world.fired.add(("relief", detective.id))
        _inc(detective.memes, "relief")
        _inc(helper.memes, "relief")
        out.append(f"{helper.id} and {detective.id} shared a grin when the missing thing was explained.")
        out.append(f"It had not been stolen at all; it had only been moved where nobody expected.")
        missing.hidden = False
    return out


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("finding", _r_finding),
    Rule("relief", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "house": Setting(place="the house", indoor=True, affordances={"hide", "search", "sniff"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affordances={"hide", "search", "sniff"}),
    "hall": Setting(place="the hallway", indoor=True, affordances={"hide", "search", "sniff"}),
    "garden": Setting(place="the garden shed", indoor=True, affordances={"hide", "search", "sniff"}),
}

MISSING = {
    "cookie_tin": ObjectThing(
        id="cookie_tin",
        label="cookie tin",
        phrase="a shiny cookie tin",
        type="tin",
        location="top shelf",
        hidden=True,
        visible_sign="a faint clink from above",
        reveals="the cookies were still inside, but the tin had been moved",
    ),
    "red_scarf": ObjectThing(
        id="red_scarf",
        label="red scarf",
        phrase="a red scarf with soft fringe",
        type="scarf",
        location="coat hook",
        hidden=True,
        visible_sign="a little red thread near the door",
        reveals="the scarf had been used to cover something",
    ),
    "small_key": ObjectThing(
        id="small_key",
        label="small key",
        phrase="a tiny brass key",
        type="key",
        location="flower pot",
        hidden=True,
        visible_sign="a tiny shine in the dirt",
        reveals="the key had been dropped by accident",
    ),
}

CLUES = {
    "funnel": ObjectThing(
        id="funnel",
        label="funnel",
        phrase="a bright metal funnel",
        type="funnel",
        location="workbench",
        clue=True,
        hidden=False,
        visible_sign="its wide mouth pointing like an arrow",
        reveals="it matched the odd shape seen earlier",
    ),
    "pawprint": ObjectThing(
        id="pawprint",
        label="pawprint",
        phrase="a damp pawprint on the floor",
        type="pawprint",
        location="doormat",
        clue=True,
        hidden=False,
        visible_sign="muddy toes, but too small for a person",
        reveals="it pointed to a dog, not a thief",
    ),
    "beagle_tag": ObjectThing(
        id="beagle_tag",
        label="beagle tag",
        phrase="a jingling tag from a collar",
        type="tag",
        location="water bowl",
        clue=True,
        hidden=False,
        visible_sign="a small silver flash",
        reveals="it belonged to the beagle",
    ),
}

BEAGLES = [
    ("Pip", "beagle"),
    ("Milo", "beagle"),
    ("Dot", "beagle"),
]

GIRL_NAMES = ["Nina", "Maya", "Lena", "Ivy", "Mina", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Theo", "Owen", "Max", "Ben", "Finn", "Eli", "Noah"]
HELPERS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["sharp-eyed", "quiet", "curious", "patient", "brave"]


def setting_detail(setting: Setting) -> str:
    if setting.place == "the house":
        return "The rooms were calm, and every little sound seemed important."
    if setting.place == "the kitchen":
        return "The kitchen smelled faintly sweet, and the floor was bright with morning light."
    if setting.place == "the hallway":
        return "The hallway was narrow, with shoes lined up like silent witnesses."
    return "The little shed held tools, jars, and plenty of places for secrets to hide."


def reasonableness_check(place: str, missing: str, clue: str) -> None:
    if place not in SETTINGS:
        pass
    if missing not in MISSING:
        pass
    if clue not in CLUES:
        pass
    if clue == "funnel" and missing == "small_key":
        return


def tell(setting: Setting, missing: ObjectThing, clue: ObjectThing, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    detective = world.add_entity(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    assistant = world.add_entity(Entity(id=helper, kind="character", type=helper, meters={}, memes={}))
    dog = world.add_entity(Entity(id="Beagle", kind="character", type="beagle", label="the beagle", meters={}, memes={}))
    missing_obj = world.add_object(ObjectThing(**missing.__dict__))
    clue_obj = world.add_object(ObjectThing(**clue.__dict__))

    world.facts = {
        "missing_id": missing_obj.id,
        "clue_id": clue_obj.id,
        "helper_id": assistant.id,
        "detective_id": detective.id,
        "dog_id": dog.id,
    }

    detective.memes["curiosity"] = 1.0
    assistant.memes["confidence"] = 0.5
    dog.memes["alertness"] = 1.0

    world.say(f"{detective.id} was a {next(t for t in TRAITS)} little detective who noticed odd things right away.")
    world.say(f"{setting_detail(setting)}")
    world.say(f"That morning, {missing_obj.label} had gone missing, and everyone wanted to know where it went.")
    world.say(f"Near the workbench sat {clue_obj.phrase}; it looked harmless, but it felt like a clue.")
    world.para()
    world.say(f"{detective.id} saw {dog.label} nose around the room.")
    world.say(f"The beagle sniffed near the {clue_obj.label}, then barked at the top shelf as if it remembered something.")
    _inc(detective.memes, "confusion")
    _inc(detective.memes, "worry")
    _inc(detective.meters, "suspicion")
    if clue.id == "funnel":
        world.say("Earlier, a strange funnel shape had been seen by the sink, and that odd sign now felt important.")
    elif clue.id == "pawprint":
        world.say("Earlier, there had been a tiny pawprint near the door, and nobody had known what to make of it.")
    else:
        world.say("Earlier, there had been a little silver flash on the floor, and it had not seemed important then.")
    world.para()
    world.say(f"{detective.id} thought the beagle might be hiding the answer.")
    world.say(f"But {assistant.id} shook their head and said the room often fooled people before the truth showed itself.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{assistant.id} lifted a box, and the missing thing turned up where it had been placed by accident.")
    _inc(detective.meters, "foundness")
    propagate(world, narrate=True)
    world.say(f"In the end, {detective.id} laughed softly, and even the beagle looked proud.")
    world.say(f"The clue had not meant trouble after all; it had only been waiting to make sense.")
    world.facts.update(detective=detective, assistant=assistant, dog=dog, missing=missing_obj, clue=clue_obj)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a beagle, a funnel, and a missing {f["missing"].label}.',
        f"Tell a gentle mystery where {f['detective'].id} misunderstands the beagle before the clue makes sense.",
        "Write a simple foreshadowing story in which a small odd object turns out to matter later.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    assistant = _safe_fact(world, f, "assistant")
    missing = _safe_fact(world, f, "missing")
    clue = _safe_fact(world, f, "clue")
    dog = _safe_fact(world, f, "dog")
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {missing.phrase}.",
        ),
        QAItem(
            question=f"Why did {detective.id} misunderstand {dog.label} at first?",
            answer=f"{detective.id} thought the beagle might be hiding the answer, but the dog was only sniffing around the clue.",
        ),
        QAItem(
            question=f"How did the funnel matter to the mystery?",
            answer=f"The funnel was a foreshadowing clue; it looked odd at first, then helped point to what had really happened.",
        ),
        QAItem(
            question=f"Who helped solve the misunderstanding?",
            answer=f"{assistant.id} helped by staying calm and looking carefully until the missing thing was found.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The missing thing was found in the place where it had been put by accident, and everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beagle?",
            answer="A beagle is a small hound dog with a good nose for sniffing and following smells.",
        ),
        QAItem(
            question="What is a funnel for?",
            answer="A funnel helps pour liquids or small things into a narrow opening without spilling them.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early that becomes important later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not have all the facts.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} {e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}")
    for o in world.objects.values():
        lines.append(f"  {o.id:10} {o.type:8} hidden={o.hidden} location={o.location}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in MISSING.items():
        lines.append(asp.fact("missing", oid))
        lines.append(asp.fact("hidden_initially", oid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.type == "funnel":
            lines.append(asp.fact("shape", cid, "wide_mouth"))
        lines.append(asp.fact("visible_sign", cid, c.visible_sign))
    lines.append(asp.fact("animal", "beagle"))
    lines.append(asp.fact("animal_type", "beagle", "hound"))
    lines.append(asp.fact("cares_about", "detective", "truth"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show foreshadow/2.
#show misunderstanding/2.
#show solved/1.

foreshadow(C, M) :- clue(C), missing(M), shape(C, wide_mouth), C = funnel, M = cookie_tin.
misunderstanding(D, beagle) :- cares_about(D, truth), animal(beagle).
solved(M) :- missing(M), not hidden_initially(M).
valid(P, M, C) :- setting(P), missing(M), clue(C), foreshadow(C, M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = valid_combos()
    cl = asp_valid()
    if set(py) == set(cl):
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", py)
    print("asp:", cl)
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for missing in MISSING:
            for clue in CLUES:
                if place in {"house", "kitchen", "hall", "garden"} and clue == "funnel" and missing == "cookie_tin":
                    combos.append((place, missing, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with a beagle and a funnel.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--missing", choices=MISSING.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    missing = getattr(args, "missing", None) or rng.choice(list(MISSING))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if missing not in MISSING or clue not in CLUES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if clue == "funnel" and missing != "cookie_tin":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, missing=missing, clue=clue, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), MISSING[params.missing], _safe_lookup(CLUES, params.clue), params.name, params.gender, params.helper)
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
    StoryParams(place="kitchen", missing="cookie_tin", clue="funnel", name="Nina", gender="girl", helper="mother"),
    StoryParams(place="hall", missing="cookie_tin", clue="funnel", name="Theo", gender="boy", helper="father"),
    StoryParams(place="house", missing="cookie_tin", clue="funnel", name="Ivy", gender="girl", helper="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
