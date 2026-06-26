#!/usr/bin/env python3
"""
storyworlds/worlds/extinguish_foreshadowing_friendship_twist_whodunit.py
======================================================================

A small whodunit story world about a light going out, a trail of clues,
a friendship-based twist, and a careful reveal.

Seed tale:
---
At twilight in a tiny museum, a lantern in the reading corner went out.
A child detective noticed a trail of wax, a snapped ribbon, and a puff of
cold air by the door. Their best friend seemed suspicious at first because
they had been near the lamp, but the clues pointed somewhere else.
In the end, the lantern had been extinguished by a draft from the cracked
window, and the friend had only rushed in to protect the clue card.
The detective thanked the friend, and they solved the case together.

World model:
---
- physical meters track light, warmth, wax spill, and tidy/fixup progress
- emotional memes track suspicion, worry, trust, relief, and friendship
- clues foreshadow the reveal instead of being pasted in after the fact
- the final turn proves who did what and why the friendship matters
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

    cat: object | None = None
    friend: object | None = None
    hero: object | None = None
    lamp: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    detail: str
    drafty: bool
    clues: list[str] = field(default_factory=list)
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
class Cause:
    id: str
    name: str
    method: str
    foreshadow: str
    twist_hint: str
    can_be_misread_as_friend: bool = False
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


@dataclass
class StoryParams:
    setting: str
    cause: str
    name: str
    friend_name: str
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
        self.fired: set[str] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "museum": Setting(
        place="the tiny museum",
        detail="A reading corner sat beside a cracked window and a glass display case.",
        drafty=True,
        clues=["wax", "ribbon", "draft", "footprints"],
    ),
    "library": Setting(
        place="the little library",
        detail="A soft chair, tall shelves, and a narrow door made the room feel quiet and careful.",
        drafty=False,
        clues=["bookmark", "dust", "ink", "lampshade"],
    ),
    "attic": Setting(
        place="the attic room",
        detail="Old boxes, a slanted roof, and a small round window made every sound feel important.",
        drafty=True,
        clues=["string", "ash", "window latch", "footprints"],
    ),
}

CAUSES = {
    "draft": Cause(
        id="draft",
        name="a cold draft",
        method="slipped in through the cracked window and blew the flame out",
        foreshadow="the curtain had been twitching all evening",
        twist_hint="the friend only shut the window after the light was already gone",
        can_be_misread_as_friend=True,
    ),
    "cat": Cause(
        id="cat",
        name="a sleepy cat",
        method="bumped the table and sniffed the flame too closely",
        foreshadow="tiny pawprints circled the chair before anyone looked up",
        twist_hint="the friend was chasing the cat away, not hiding anything",
        can_be_misread_as_friend=False,
    ),
    "breeze": Cause(
        id="breeze",
        name="a quick breeze",
        method="slipped through the door just as it opened and snuffed the candle",
        foreshadow="the door kept clicking because it never latched well",
        twist_hint="the friend had been holding a clue card and could not have reached the flame",
        can_be_misread_as_friend=True,
    ),
}

NAMES = ["Nina", "Pip", "Mara", "Theo", "Lena", "Owen", "June", "Sami"]
FRIEND_NAMES = ["Pip", "Milo", "Anya", "Rafi", "Tess", "Noor", "Kai", "Bea"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_draft(world: World) -> list[str]:
    out = []
    cause = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cause")
    if cause.id != "draft" or "draft" in world.fired:
        return out
    if world.get("lamp").meters["light"] < THRESHOLD:
        world.fired.add("draft")
        world.get("lamp").meters["light"] = 0
        world.get("room").meters["warmth"] -= 1
        out.append("The flame vanished when the draft slipped under the curtain.")
    return out


def _r_cat(world: World) -> list[str]:
    out = []
    cause = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cause")
    if cause.id != "cat" or "cat" in world.fired:
        return out
    if world.get("lamp").meters["light"] < THRESHOLD:
        world.fired.add("cat")
        world.get("cat").meters["restless"] += 1
        world.get("lamp").meters["light"] = 0
        out.append("The candle went dark after the cat nudged the table.")
    return out


def _r_breeze(world: World) -> list[str]:
    out = []
    cause = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cause")
    if cause.id != "breeze" or "breeze" in world.fired:
        return out
    if world.get("lamp").meters["light"] < THRESHOLD:
        world.fired.add("breeze")
        world.get("lamp").meters["light"] = 0
        out.append("A quick breeze found the flame and whisked it away.")
    return out


RULES = [Rule("draft", _r_draft), Rule("cat", _r_cat), Rule("breeze", _r_breeze)]


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def predict_outcome(world: World, cause: Cause) -> dict:
    sim = world.copy()
    sim.facts["cause"] = cause
    sim.get("lamp").meters["light"] = 0
    propagate(sim)
    return {
        "light": sim.get("lamp").meters["light"],
        "friend_suspicion": sim.get("friend").memes.get("suspicion", 0),
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little detective who liked neat clues and quiet rooms."
    )
    world.say(
        f"{hero.pronoun().capitalize()} trusted {friend.id}, who always hurried in with a helpful smile."
    )


def set_scene(world: World, setting: Setting) -> None:
    world.say(
        f"That evening, {setting.place} was soft with dim light. {setting.detail}"
    )


def foreshadow(world: World, cause: Cause) -> None:
    world.say(
        f"One small thing kept standing out: {cause.foreshadow}."
    )


def suspicion_beats(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["suspicion"] += 1
    friend.memes["worry"] += 1
    if cause.can_be_misread_as_friend:
        world.say(
            f"{friend.id} had been near the lamp, so {hero.id} glanced at {friend.pronoun('object')} first."
        )
    else:
        world.say(
            f"{friend.id} looked nervous because {friend.pronoun('subject')} was carrying the clue card."
        )


def investigate(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    world.say(
        f"{hero.id} followed the little trail of clues: {', '.join(world.setting.clues[:2])}, then a careful look at the floor."
    )
    if cause.id == "cat":
        world.say("Tiny pawprints curved by the chair leg, and that made the cat seem important.")
    elif cause.id == "draft":
        world.say("The curtain fluttered again, as if the room itself were trying to whisper the answer.")
    else:
        world.say("The door clicked open and shut, and the air moved in a quick, chilly puff.")


def twist(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["suspicion"] = max(0, hero.memes.get("suspicion", 0) - 1)
    hero.memes["relief"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"Then the truth turned over like a card being flipped: {cause.name} had done it, not {friend.id}."
    )
    world.say(
        f"The clue made sense at once, and {cause.twist_hint}."
    )


def resolve(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    lamp = world.get("lamp")
    lamp.meters["light"] = 1
    lamp.memes["safe"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{friend.id} fetched a fresh match while {hero.id} straightened the candle holder."
    )
    world.say(
        f"Together they relit the lamp, and the room felt warm again."
    )
    world.say(
        f"{hero.id} smiled at {friend.id} and said the best clue of all was how {friend.id} had helped."
    )


def tell(setting: Setting, cause: Cause, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy"))
    lamp = world.add(Entity(id="lamp", type="lamp", label="lamp", meters={"light": 1, "warmth": 1}, memes={"safe": 1}))
    room = world.add(Entity(id="room", type="room", label=setting.place, meters={"warmth": 1}))
    cat = world.add(Entity(id="cat", kind="character", type="cat", label="cat", meters={"restless": 0}))
    world.facts.update(hero=hero, friend=friend, lamp=lamp, room=room, cat=cat, cause=cause)

    introduce(world, hero, friend)
    world.para()
    set_scene(world, setting)
    foreshadow(world, cause)
    suspicion_beats(world, hero, friend, cause)
    investigate(world, hero, friend, cause)
    world.para()
    world.say("The room held its breath while the detective thought.")
    world.say("At last, the smallest clue pulled the whole story into place.")
    twist(world, hero, friend, cause)
    resolve(world, hero, friend, cause)
    return world


KNOWLEDGE = {
    "draft": [
        QAItem(
            question="What is a draft?",
            answer="A draft is moving air that slips through a crack, door, or window and can make a room feel chilly.",
        ),
    ],
    "cat": [
        QAItem(
            question="Why can a cat make a mess by accident?",
            answer="A cat can make a mess by accident because it may jump, nudge, or bump things without meaning to cause trouble.",
        ),
    ],
    "breeze": [
        QAItem(
            question="What is a breeze?",
            answer="A breeze is a light wind that moves gently through the air.",
        ),
    ],
    "extinguish": [
        QAItem(
            question="What does extinguish mean?",
            answer="To extinguish something means to put it out so it stops burning or shining.",
        ),
    ],
    "friendship": [
        QAItem(
            question="What does a good friend do in a hard moment?",
            answer="A good friend helps, listens, and stays kind when something goes wrong.",
        ),
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the truth look different from what people first thought.",
        ),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child where a lamp gets extinguished in {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}.',
        f"Tell a mystery story with foreshadowing, friendship, and a twist, and include {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cause").name}.",
        f"Write a gentle detective story in which {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend").id} solve who made the light go out.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, cause = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cause")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little detective, and {friend.id}, who stayed close as the mystery unfolded.",
        ),
        QAItem(
            question=f"What happened to the lamp in {world.setting.place}?",
            answer=f"The lamp was extinguished and the room went dim until the clue trail helped solve the case.",
        ),
        QAItem(
            question=f"What first made {hero.id} look at {friend.id}?",
            answer=(
                f"{friend.id} had been near the lamp, so {hero.id} wondered about {friend.pronoun('object')} first, "
                f"but that suspicion did not last."
            ),
        ),
        QAItem(
            question=f"What clue foreshadowed the answer?",
            answer=f"{cause.foreshadow.capitalize()}. That small detail quietly hinted at the real cause before the reveal.",
        ),
        QAItem(
            question=f"Who really extinguished the light?",
            answer=f"{cause.name} did it, by {cause.method}. The friend was not the culprit.",
        ),
        QAItem(
            question=f"How did the friendship matter at the end?",
            answer=f"{friend.id} helped relight the lamp, and {hero.id} thanked {friend.id} for staying calm and kind.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"extinguish", "friendship", "twist", _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cause").id}
    out = []
    for tag in ["extinguish", "friendship", "twist", "draft", "cat", "breeze"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", cause="draft", name="Nina", friend_name="Pip"),
    StoryParams(setting="library", cause="cat", name="Mara", friend_name="Tess"),
    StoryParams(setting="attic", cause="breeze", name="June", friend_name="Rafi"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    cause = getattr(args, "cause", None) or rng.choice(list(CAUSES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if friend == name:
        friend = rng.choice([n for n in FRIEND_NAMES if n != name])
    if setting not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if cause not in CAUSES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, cause=cause, name=name, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    cause = _safe_lookup(CAUSES, params.cause)
    world = tell(setting, cause, params.name, params.friend_name)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.can_be_misread_as_friend:
            lines.append(asp.fact("misread_as_friend", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, C) :- setting(S), cause(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((s, c) for s in SETTINGS for c in CAUSES)
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about an extinguished light.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for s, c in asp_valid():
            print(f"{s} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
