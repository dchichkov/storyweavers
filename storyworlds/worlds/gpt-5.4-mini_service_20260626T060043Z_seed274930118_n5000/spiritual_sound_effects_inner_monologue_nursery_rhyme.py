#!/usr/bin/env python3
"""
Story world: spiritual sound effects, inner monologue, nursery-rhyme style.

A small child, a soft sound, a worried inner thought, and a gentle turn
toward calm and care. The simulated world tracks physical meters and emotional
memes so the prose is driven by state, not just a fixed template.
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
# World model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    parent: object | None = None
    sound: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the little chapel garden"
    indoor: bool = False
    echo: str = "soft"
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
class Sound:
    id: str
    sound: str
    source: str
    feeling: str
    worry: str
    soothe: str
    keyword: str = "spiritual"
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    kind: str
    comfort: str
    reason: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "chapel_garden": Setting(place="the little chapel garden", indoor=False, echo="soft"),
    "quiet_room": Setting(place="the quiet room", indoor=True, echo="gentle"),
    "moon_yard": Setting(place="the moon yard", indoor=False, echo="hushed"),
}

SOUNDS = {
    "bells": Sound(
        id="bells",
        sound="ding-dong",
        source="the little chapel bell",
        feeling="spiritual",
        worry="felt too big and echo-y",
        soothe="grew calm and brave",
        tags={"spiritual", "sound"},
    ),
    "chime": Sound(
        id="chime",
        sound="ting-ting",
        source="a hanging wind chime",
        feeling="mystery",
        worry="made a trembling thought",
        soothe="became a tiny music prayer",
        tags={"sound"},
    ),
    "drum": Sound(
        id="drum",
        sound="boom-boom",
        source="a tiny hand drum",
        feeling="heartbeat",
        worry="felt loud in the chest",
        soothe="felt like a steady walk",
        tags={"sound"},
    ),
    "hush": Sound(
        id="hush",
        sound="shh-shh",
        source="a folding of quiet curtains",
        feeling="peace",
        worry="made the room feel still",
        soothe="made breathing slow and soft",
        tags={"spiritual", "quiet"},
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a paper lantern",
        phrase="a little paper lantern with a gold star",
        kind="lantern",
        comfort="shone like a tiny moon",
        reason="it gave the child a bright thing to hold",
    ),
    "blanket": Charm(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket with a blue edge",
        kind="blanket",
        comfort="felt like a hug in cloth",
        reason="it helped the child sit and breathe",
    ),
    "beads": Charm(
        id="beads",
        label="a string of prayer beads",
        phrase="a string of smooth prayer beads",
        kind="beads",
        comfort="clicked like tiny raindrops of peace",
        reason="it gave little fingers a steady path",
    ),
}

NAMES = ["Luna", "Milo", "Nina", "Eli", "Pia", "Noa", "Mira", "Toby"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "gentle", "shy", "brave", "tiny", "thoughtful"]
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    sound: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation helpers
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def sound_line(sound: Sound) -> str:
    return f"{sound.sound}, went the {sound.source}."


def inner_monologue(child: Entity, sound: Sound) -> str:
    if sound.id == "bells":
        return f'In {child.pronoun("possessive")} little heart, {child.id} thought, "Is that a prayer or a path?"'
    if sound.id == "chime":
        return f'In {child.pronoun("possessive")} little heart, {child.id} thought, "That sound is shy, like a secret star."'
    if sound.id == "drum":
        return f'In {child.pronoun("possessive")} little heart, {child.id} thought, "My chest can match that beat."'
    return f'In {child.pronoun("possessive")} little heart, {child.id} thought, "I can be still and listen."'


def soothe_line(child: Entity, charm: Charm) -> str:
    return f"{child.id} held {charm.label} and felt {charm.comfort}."


def setup_world(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", meters={}, memes={}))
    charm = world.add(Entity(id="Charm", type=params.charm, label=_safe_lookup(CHARMS, params.charm).label, phrase=_safe_lookup(CHARMS, params.charm).phrase))
    sound = world.add(Entity(id="Sound", type=params.sound, label=_safe_lookup(SOUNDS, params.sound).id))
    world.facts.update(child=child, parent=parent, charm=charm, sound=sound, setting=setting)
    return world


def play_sound(world: World) -> None:
    sound = _safe_lookup(SOUNDS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sound").label)
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    child.meters["startle"] = child.meters.get("startle", 0.0) + 1
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(sound_line(sound))
    world.say(inner_monologue(child, sound))


def worry(world: World) -> None:
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent")
    sound = _safe_lookup(SOUNDS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sound").label)
    if child.meters.get("startle", 0.0) >= THRESHOLD:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.say(f"{child.id} felt a fluttery worry, because {sound.worry}.")
        world.say(f"{parent.label.capitalize()} came close and said, 'Listen softly; the sound means no harm.'")


def comfort(world: World) -> None:
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent")
    charm = _safe_lookup(CHARMS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "charm").label)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["worry"] = 0.0
    world.say(f"{parent.label.capitalize()} brought {charm.label}, because {charm.reason}.")
    world.say(soothe_line(child, charm))
    world.say(f"Then the little sound became kind and easy, and the garden felt wider than before.")


def tell_story(world: World) -> None:
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent")
    setting = world.setting
    sound = _safe_lookup(SOUNDS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sound").label)
    charm = _safe_lookup(CHARMS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "charm").label)

    world.say(f"Once in {setting.place}, {child.id} was a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params").trait if 'params' in world.facts else 'small'} child who loved quiet things.")
    world.say(f"{child.id} listened for spiritual little sounds, and {sound_line(sound)}")
    world.para()
    world.say(f"One day, {child.id} and {parent.label} sat in {setting.place}.")
    world.say(f"{child.id} wanted to know what the sound meant, but the echo was {setting.echo} and strange.")
    play_sound(world)
    worry(world)
    world.para()
    world.say(f"Then {parent.label} placed {charm.label} in {child.id}'s hands.")
    comfort(world)
    world.para()
    world.say(f"At the end, {child.id} was calm, and the little {sound.id} sound felt like a song instead of a fright.")
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_worries(C,S) :- child(C), sound(S), startle(C).
child_calms(C) :- child(C), charm(K), comforts(K).
resolved(C) :- child_calms(C), child_worries(C,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
        if "spiritual" in _safe_lookup(SOUNDS, sid).tags:
            lines.append(asp.fact("spiritual", sid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[str]:
    import asp
    return [str(a) for a in asp.one_model(asp_program("#show resolved/1."))]


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for sound in SOUNDS.values():
            for charm in CHARMS.values():
                if sound.id == "bells" and charm.id == "lantern":
                    combos.append((setting, sound.id, charm.id))
                elif sound.id == "chime" and charm.id == "beads":
                    combos.append((setting, sound.id, charm.id))
                elif sound.id == "drum" and charm.id == "blanket":
                    combos.append((setting, sound.id, charm.id))
                elif sound.id == "hush":
                    combos.append((setting, sound.id, charm.id))
    return combos


def explain_rejection(sound: Sound, charm: Charm) -> str:
    return (
        f"(No story: {sound.id} and {charm.label} do not make a clear little turn. "
        f"Try a pair where the charm can truly calm the sound.)"
    )


# ---------------------------------------------------------------------------
# Story generation and Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f'Write a nursery-rhyme style story with the word "{_safe_lookup(SOUNDS, p.sound).keyword}" and a gentle spiritual sound.',
        f"Tell a short story where {p.name} hears {_safe_lookup(SOUNDS, p.sound).sound} and then finds comfort with {_safe_lookup(CHARMS, p.charm).label}.",
        f"Write a child-friendly rhyme about a little sound, an inner thought, and a calm ending in {_safe_lookup(SETTINGS, p.setting).place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent")
    sound = _safe_lookup(SOUNDS, p.sound)
    charm = _safe_lookup(CHARMS, p.charm)
    return [
        QAItem(
            question=f"What did {p.name} hear in {_safe_lookup(SETTINGS, p.setting).place}?",
            answer=f"{p.name} heard {sound.sound} from {sound.source}. It felt {sound.feeling} at first.",
        ),
        QAItem(
            question=f"What did {p.name} think inside {child.pronoun('possessive')} head?",
            answer=inner_monologue(child, sound).replace("In his little heart, ", "").replace("In her little heart, ", "").replace("In its little heart, ", ""),
        ),
        QAItem(
            question=f"How did {parent.label} help {p.name} feel better?",
            answer=f"{parent.label.capitalize()} brought {charm.label}, and that helped {p.name} calm down and listen again.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{p.name} went from a fluttery worry to calm brave listening, and the sound felt friendly instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    sound = _safe_lookup(SOUNDS, p.sound)
    charm = _safe_lookup(CHARMS, p.charm)
    qa = [
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, sing-song story or poem for children, often with a repeating beat and simple words.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special sounds like ding-dong, ting-ting, or shh-shh that help a story feel alive.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character says to themself inside their head.",
        ),
    ]
    if "spiritual" in sound.tags:
        qa.append(QAItem(
            question="What does spiritual mean here?",
            answer="Here, spiritual means the sound feels gentle, thoughtful, and a little like a prayer or a calm sacred moment.",
        ))
    if charm.id == "beads":
        qa.append(QAItem(
            question="What are prayer beads for?",
            answer="Prayer beads are little beads people may hold while they breathe, pray, or think calm thoughts.",
        ))
    if charm.id == "lantern":
        qa.append(QAItem(
            question="What does a lantern do?",
            answer="A lantern gives a soft light that helps a place feel warm, safe, and easy to see.",
        ))
    return qa


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main story API
# ---------------------------------------------------------------------------

def valid_story_pairs() -> list[tuple[str, str]]:
    return [(s, c) for _, s, c in valid_combos()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny spiritual sound-effect nursery rhyme world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "sound", None) and getattr(args, "charm", None) and (getattr(args, "setting", None) is None or True):
        if (getattr(args, "setting", None) or "chapel_garden", getattr(args, "sound", None), getattr(args, "charm", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    options = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
        and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))
    ]
    if not options:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, sound, charm = rng.choice(sorted(options))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, sound=sound, charm=charm, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(_safe_lookup(SETTINGS, params.setting), params)
    world.facts["params"] = params
    tell_story(world)
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
    StoryParams(setting="chapel_garden", sound="bells", charm="lantern", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="quiet_room", sound="hush", charm="blanket", name="Milo", gender="boy", parent="father", trait="gentle"),
    StoryParams(setting="moon_yard", sound="chime", charm="beads", name="Nina", gender="girl", parent="mother", trait="shy"),
    StoryParams(setting="chapel_garden", sound="drum", charm="blanket", name="Eli", gender="boy", parent="father", trait="thoughtful"),
]


def asp_program_for_show() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n#show valid_story/4.\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_for_show())
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_for_show())
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program_for_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for setting, sound, charm in triples:
            print(f"  {setting:14} {sound:8} {charm:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.sound} with {p.charm} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
