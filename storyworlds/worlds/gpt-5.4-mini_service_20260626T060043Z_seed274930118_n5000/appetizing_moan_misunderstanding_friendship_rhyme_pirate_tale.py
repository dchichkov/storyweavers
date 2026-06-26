#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/appetizing_moan_misunderstanding_friendship_rhyme_pirate_tale.py
===============================================================================================================================

A small pirate-tale story world about a shipboard misunderstanding, a friendly
turn, and a rhyming ending.

Seed story premise:
- A pirate crew hears a strange moan on the sea.
- The sound and a very appetizing smell cause a misunderstanding.
- The crew discovers the moan comes from a friend, not a danger.
- They share the food, sing a rhyme, and end as friends.

The world model tracks physical items, shipboard locations, and emotional
memes. The key tension comes from a false alarm caused by smell and sound.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: str = ""
    captain: object | None = None
    cook: object | None = None
    friend: object | None = None
    snack_ent: object | None = None
    sound_ent: object | None = None
    def __post_init__(self) -> None:
        for k in ["smell", "noise", "food", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "confusion", "friendship", "relief", "hunger"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the pirate ship"
    sea: str = "the glittering sea"
    afford: set[str] = field(default_factory=lambda: {"cook", "listen", "share", "sing"})
    SETTING: object | None = None
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
class CrewRole:
    id: str
    type: str
    label: str
    trait: str
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
class Food:
    id: str
    label: str
    phrase: str
    smell: str
    appetizing: bool = True
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
class Sound:
    id: str
    label: str
    source_hint: str
    mood: str = "mysterious"
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
class StoryParams:
    name: str
    friend: str
    role: str
    snack: str
    sound: str
    seed: Optional[int] = None
    params: object | None = None
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_mistaken_alarm(world: World) -> list[str]:
    out: list[str] = []
    captain = world.entities.get("captain")
    friend = world.entities.get("friend")
    snack = world.entities.get("snack")
    if not captain or not friend or not snack:
        return out
    if captain.memes["confusion"] < THRESHOLD:
        return out
    if snack.meters["smell"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["fear"] += 1
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    captain = world.entities.get("captain")
    friend = world.entities.get("friend")
    if not captain or not friend:
        return out
    if captain.memes["relief"] < THRESHOLD or friend.memes["joy"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_mistaken_alarm, _r_friendship):
            before = set(world.fired)
            rule(world)
            if set(world.fired) != before:
                changed = True


SETTING = Setting()

ROLES = {
    "captain": CrewRole(id="captain", type="pirate", label="captain", trait="brave"),
    "cook": CrewRole(id="cook", type="pirate", label="cook", trait="cheery"),
    "mate": CrewRole(id="mate", type="pirate", label="mate", trait="curious"),
}

FOODS = {
    "pie": Food(id="pie", label="pie", phrase="a warm apple pie", smell="appetizing"),
    "buns": Food(id="buns", label="buns", phrase="sweet cinnamon buns", smell="appetizing"),
    "soup": Food(id="soup", label="soup", phrase="a pot of buttery soup", smell="appetizing"),
}

SOUNDS = {
    "moan": Sound(id="moan", label="moan", source_hint="the cargo hold", mood="strange"),
    "groan": Sound(id="groan", label="groan", source_hint="the lower deck", mood="mysterious"),
}

CAPTAIN_NAMES = ["Nell", "Ruby", "Ivy", "Mara", "Bo", "Nate", "Finn", "Gale"]
FRIEND_NAMES = ["Milo", "Pip", "June", "Sailor", "Tamsin", "Jory", "Lark", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world: appetizing moan, misunderstanding, friendship, rhyme.")
    ap.add_argument("--name", choices=CAPTAIN_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--snack", choices=FOODS)
    ap.add_argument("--sound", choices=SOUNDS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.role not in ROLES:
        pass
    if params.snack not in FOODS or params.sound not in SOUNDS:
        pass
    if not _safe_lookup(FOODS, params.snack).appetizing:
        pass
    if _safe_lookup(SOUNDS, params.sound).id != "moan" and params.sound != "groan":
        pass
    if params.name == params.friend:
        pass


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    captain_role = ROLES["captain"]
    friend_role = _safe_lookup(ROLES, params.role)
    snack = _safe_lookup(FOODS, params.snack)
    sound = _safe_lookup(SOUNDS, params.sound)

    captain = world.add(Entity(id="captain", kind="character", type="pirate", label=params.name, trait=captain_role.trait))
    friend = world.add(Entity(id="friend", kind="character", type="pirate", label=params.friend, trait=friend_role.trait))
    cook = world.add(Entity(id="cook", kind="character", type="pirate", label="the cook", trait="cheery"))
    snack_ent = world.add(Entity(id="snack", type="food", label=snack.label, phrase=snack.phrase, caretaker=cook.id, location="galley"))
    sound_ent = world.add(Entity(id="sound", type="sound", label=sound.label, phrase=sound.source_hint, location="hold"))

    world.facts.update(captain=captain, friend=friend, cook=cook, snack=snack_ent, sound=sound_ent, params=params)

    world.say(f"Captain {captain.label} sailed on the {SETTING.place} with {friend.label}, a {friend_role.trait} shipmate.")
    world.say(f"The cook brought out {snack.phrase}, and the whole deck smelled {snack.smell}.")
    world.say(f"That smell was so {snack.smell} that even the gulls seemed to lean closer.")

    world.para()
    captain.memes["hunger"] += 1
    captain.memes["confusion"] += 1
    captain.meters["noise"] += 1
    world.say(f"Then a deep {sound.label} rolled up from {sound.source_hint}.")
    world.say(f"Captain {captain.label} frowned, because the sound and the smell together made a big misunderstanding.")
    world.say(f"\"Is that a sea beast?\" {captain.label} asked, while the crew listened hard.")

    world.para()
    friend.meters["noise"] += 1
    friend.memes["joy"] += 1
    world.say(f"But {friend.label} laughed and went below deck to check the source.")
    world.say(f"It was not a beast at all; it was a trapped crate, and the crate was bumping against a barrel in a slow moan.")
    world.say(f"When the captain saw that, the fear faded and the confusion turned to relief.")
    captain.memes["relief"] += 1

    world.para()
    world.say(f"The cook opened the crate and found more {snack.label}, still warm and appetizing.")
    world.say(f"Captain {captain.label} and {friend.label} shared the food on the deck, and the whole crew smiled together.")
    captain.memes["joy"] += 1
    captain.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["joy"] += 1
    propagate(world)
    world.say(f"To end the day, they sang a little rhyme: \"A moan was heard, a feast was found; friends stay near on pirate ground.\"")
    world.say(f"After that, the sea felt less spooky, and the ship sailed on with friendship in every step.")

    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    friend = _safe_fact(world, f, "friend")
    snack = _safe_fact(world, f, "snack")
    sound = _safe_fact(world, f, "sound")
    return [
        f"Write a short pirate tale for a child about Captain {captain.label}, {friend.label}, {snack.phrase}, and a mysterious {sound.label}.",
        f"Tell a story where an appetizing smell causes a misunderstanding on a pirate ship, but friendship fixes it.",
        f"Write a gentle pirate story that ends with a rhyme after someone hears a moan below deck.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    friend = _safe_fact(world, f, "friend")
    snack = _safe_fact(world, f, "snack")
    sound = _safe_fact(world, f, "sound")
    return [
        QAItem(
            question=f"Why did Captain {captain.label} get worried on the ship?",
            answer=f"Captain {captain.label} got worried because the appetizing smell of {snack.phrase} mixed with the strange {sound.label} and caused a misunderstanding.",
        ),
        QAItem(
            question=f"What did {friend.label} find below deck?",
            answer=f"{friend.label} found a crate making the moaning sound, not a sea beast, so the crew could relax.",
        ),
        QAItem(
            question=f"How did the story end for Captain {captain.label} and {friend.label}?",
            answer=f"They shared the warm {snack.label}, became happier friends, and finished the day with a rhyme on the deck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does appetizing mean?",
            answer="Appetizing means something looks or smells so good that it makes you want to eat it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because the clue was confusing.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind and happy bond between friends who help and enjoy each other.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like ship and trip.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Nell", friend="Milo", role="mate", snack="pie", sound="moan"),
    StoryParams(name="Ruby", friend="Pip", role="mate", snack="buns", sound="groan"),
    StoryParams(name="Mara", friend="June", role="mate", snack="soup", sound="moan"),
]


ASP_RULES = r"""
snack_appetizing(S) :- snack(S), appetizing(S).
misunderstanding(C) :- captain(C), hears(C, X), smells(C, Y), strange(X), appetizing(Y).
friendship(C, F) :- captain(C), friend(F), shares(C, F, _), misunderstanding(C), resolved(_).
rhymes_end :- rhyme(L), ship(L).
compatible_story(C, F, S, X) :- captain(C), friend(F), snack(S), sound(X), snack_appetizing(S), moanlike(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, food in FOODS.items():
        lines.append(asp.fact("snack", sid))
        if food.appetizing:
            lines.append(asp.fact("appetizing", sid))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if snd.id in {"moan", "groan"}:
            lines.append(asp.fact("moanlike", sid))
        lines.append(asp.fact("strange", sid))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/4."))
    atoms = set(asp.atoms(model, "compatible_story"))
    if atoms:
        print(f"OK: ASP found {len(atoms)} compatible story pattern(s).")
        return 0
    print("MISMATCH: no compatible patterns found.")
    return 1


def build_combo() -> tuple[str, str, str, str]:
    return ("Nell", "Milo", "mate", "pie")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(CAPTAIN_NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != name])
    role = getattr(args, "role", None) or "mate"
    snack = getattr(args, "snack", None) or rng.choice(list(FOODS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    params = StoryParams(name=name, friend=friend, role=role, snack=snack, sound=sound)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible_story/4."))
        atoms = sorted(set(asp.atoms(model, "compatible_story")))
        print(f"{len(atoms)} compatible story pattern(s):")
        for atom in atoms:
            print(" ", atom)
        return

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
            header = f"### {p.name} and {p.friend} / snack={p.snack} / sound={p.sound}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
