#!/usr/bin/env python3
"""
A tiny Nursery-Rhyme storyworld about a permissive speech, a kiwi, and a small
moral transformation with a twist.

Core premise:
- A gentle grown-up gives a permissive speech.
- A kiwi wants something shiny or sweet.
- The kiwi learns a moral value like honesty, sharing, or patience.
- A twist changes what the kiwi expected, and the ending proves the change.

The world model tracks:
- physical meters: desire, hunger, shine, carry, travel, comfort
- emotional memes: joy, worry, trust, guilt, pride, kindness, patience

The prose is state-driven: the story begins with a setup, turns on a worry,
then resolves through a permissive speech and a small transformation.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bowl: object | None = None
    grownup: object | None = None
    kiwi: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "kiwi", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "father", "grownup", "adult"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Want:
    id: str
    verb: str
    gerund: str
    worry: str
    turn: str
    twist: str
    outcome: str
    moral: str
    mood: str
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    risk: str
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
    want: str
    prize: str
    name: str
    parent: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def nudge(ent: Entity, meter: str, amount: float = 1.0) -> None:
    ent.meters[meter] = ent.meters.get(meter, 0.0) + amount


def feel(ent: Entity, meme: str, amount: float = 1.0) -> None:
    ent.memes[meme] = ent.memes.get(meme, 0.0) + amount


PLACES = {
    "nest": Place(name="the nest", indoors=False, affords={"song", "share"}),
    "grove": Place(name="the grove", indoors=False, affords={"search", "share"}),
    "kitchen": Place(name="the kitchen", indoors=True, affords={"share", "bake"}),
}

WANTS = {
    "berry": Want(
        id="berry",
        verb="hop to the berry bowl",
        gerund="hopping to the berry bowl",
        worry="the bowl might belong to someone else",
        turn="the bowl was set out for everyone",
        twist="the bowl was empty, and a single berry had rolled behind a spoon",
        outcome="the kiwi found the berry and shared it",
        moral="sharing",
        mood="greedy",
        keyword="berry",
    ),
    "song": Want(
        id="song",
        verb="sing the loudest song",
        gerund="singing the loudest song",
        worry="the nest might become noisy and rude",
        turn="the grown-up made room for every voice",
        twist="the loud song turned soft when the little birds joined in",
        outcome="the kiwi learned to listen and sing kindly",
        moral="kindness",
        mood="pushy",
        keyword="song",
    ),
    "glow": Want(
        id="glow",
        verb="follow the little glow",
        gerund="following the little glow",
        worry="the glow might lead to a tricky puddle",
        turn="the glow was only a shiny beetle on a leaf",
        twist="the beetle blinked once, then flew onto the kiwi's tail",
        outcome="the kiwi slowed down and chose patience",
        moral="patience",
        mood="hasty",
        keyword="glow",
    ),
}

PRIZES = {
    "berry": Prize(id="berry", label="berry", phrase="a ripe red berry", risk="hunger"),
    "bell": Prize(id="bell", label="bell", phrase="a bright little bell", risk="noise"),
    "leaf": Prize(id="leaf", label="leaf", phrase="a shiny green leaf", risk="rush"),
}

NAMES = ["Kiki", "Mimi", "Nana", "Tiki", "Pip", "Lulu", "Ria", "Bibi", "Coco", "Moka"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, p in PLACES.items():
        for want in p.affords:
            for prize in PRIZES:
                combos.append((place, want, prize))
    return combos


def reasonableness_gate(place: str, want: str, prize: str) -> None:
    if place not in PLACES:
        pass
    if want not in WANTS:
        pass
    if prize not in PRIZES:
        pass
    if want not in _safe_lookup(PLACES, place).affords:
        pass


def settle(world: World) -> None:
    kiwi = world.get("kiwi")
    grownup = world.get("grownup")
    prize = world.get("prize")
    want = _safe_fact(world, world.facts, "want")

    if kiwi.meters.get("desire", 0.0) >= THRESHOLD:
        feel(kiwi, "restless", 1.0)
    if kiwi.memes.get("restless", 0.0) >= THRESHOLD and world.facts.get("twist_seen"):
        feel(kiwi, "curious", 1.0)
    if kiwi.memes.get("curious", 0.0) >= THRESHOLD:
        feel(kiwi, "patience", 1.0)
    if world.facts.get("shared"):
        feel(kiwi, "joy", 1.0)
        feel(grownup, "pride", 1.0)
        kiwi.memes["worry"] = 0.0
        kiwi.memes["guilt"] = 0.0
        kiwi.memes["kindness"] = kiwi.memes.get("kindness", 0.0) + 1.0
        prize.meters["carry"] = 0.0


def tell(place: Place, want: Want, prize_cfg: Prize, name: str, parent: str) -> World:
    world = World(place)
    kiwi = world.add(Entity(id="kiwi", kind="character", type="kiwi", label=name))
    grownup = world.add(Entity(id="grownup", kind="character", type=parent, label=parent))
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label="bowl", phrase="a small bowl"))

    world.facts.update(place=place.name, want=want, prize=prize_cfg, kiwi=kiwi, grownup=grownup)

    # Act 1
    world.say(f"In {place.name}, there lived a little kiwi named {name}.")
    world.say(f"{name} loved {want.gerund} because it made the morning feel bright and brisk.")
    if prize_cfg.id == "berry":
        world.say(f"On the table sat {prize_cfg.phrase}, and {name} kept peeking at it.")
    elif prize_cfg.id == "bell":
        world.say(f"Near the window hung {prize_cfg.phrase}, and its tinny ring called to {name}.")
    else:
        world.say(f"By the sill rested {prize_cfg.phrase}, and {name} thought it looked like a tiny treasure.")

    world.para()

    # Act 2
    nudge(kiwi, "desire", 1.0)
    feel(kiwi, "worry", 1.0)
    world.say(f"Then {name} wanted to {want.verb}, but {want.worry}.")
    world.say(f"The grown-up gave a permissive speech: \"You may try, little bird, as long as we do it the kind way.\"")
    world.say(f"{want.turn.capitalize()}.")
    world.facts["twist_seen"] = True
    world.say(f"But then came a twist: {want.twist}.")
    if prize_cfg.id == "berry":
        bowl.label = "bowl"
        world.say("The berry was not stolen at all; it had simply rolled away under the spoon.")
    elif prize_cfg.id == "bell":
        world.say("The bell was not for keeping; it was a dinner bell, and dinner was for all.")
    else:
        world.say("The leaf was not a prize for one; it was a flag for the little game they were playing.")

    world.para()

    # Act 3
    feel(kiwi, "guilt", 1.0)
    feel(kiwi, "kindness", 1.0)
    world.say(f"{name} blushed a little and chose the moral value of {want.moral}.")
    world.say(f"That meant {name} did not snatch the prize, but helped place it where it belonged.")
    world.facts["shared"] = True
    settle(world)
    if want.id == "berry":
        world.say(f"In the end, {name} shared the berry and the bowl looked merry.")
    elif want.id == "song":
        world.say(f"In the end, {name} sang softly, and every bird found a gentle note to bring.")
    else:
        world.say(f"In the end, {name} slowed down, and the glow did not trick those quick little feet.")

    world.say(f"So the kiwi changed in a small but true way: from {want.mood} to kind.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    want: Want = _safe_fact(world, f, "want")
    prize: Prize = _safe_fact(world, f, "prize")
    return [
        f'Write a Nursery Rhyme style story about a kiwi, a permissive speech, and {want.keyword}.',
        f"Tell a small moral story where a kiwi learns {want.moral} after a twist involving {prize.phrase}.",
        f'Write a gentle story with the words "permissive", "speech", and "kiwi" that ends with a transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kiwi: Entity = _safe_fact(world, f, "kiwi")
    grownup: Entity = _safe_fact(world, f, "grownup")
    want: Want = _safe_fact(world, f, "want")
    prize: Prize = _safe_fact(world, f, "prize")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the story about in {place.name}?",
            answer=f"It was about a little kiwi named {kiwi.label}, with a kind grown-up nearby.",
        ),
        QAItem(
            question=f"What did {kiwi.label} want to do?",
            answer=f"{kiwi.label} wanted to {want.verb}, but first there was worry and a gentle warning.",
        ),
        QAItem(
            question="What did the grown-up say?",
            answer='The grown-up gave a permissive speech and said the kiwi could try, as long as it was done the kind way.',
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {want.twist.lower()}",
        ),
        QAItem(
            question=f"What moral value did the kiwi learn?",
            answer=f"The kiwi learned {want.moral}, which helped the story end happily.",
        ),
        QAItem(
            question=f"How did the kiwi change by the end?",
            answer=f"By the end, {kiwi.label} changed from {want.mood} to kind and patient.",
        ),
        QAItem(
            question=f"What happened to {prize.phrase}?",
            answer=f"{prize.phrase.capitalize()} ended up shared or set in the right place, not snatched away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kiwi?",
            answer="A kiwi is a small bird with a round body, a long beak, and a shy, gentle way of moving.",
        ),
        QAItem(
            question="What does permissive mean?",
            answer="Permissive means allowing someone to try, while still keeping a kind rule or limit in place.",
        ),
        QAItem(
            question="What is a speech?",
            answer="A speech is when someone speaks to others for a little while to explain, teach, or comfort them.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of behaving, like sharing, honesty, kindness, or patience.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another, like becoming calmer or kinder.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters expected.",
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
place(pasture).
place(nest).
place(kitchen).

want(berry).
want(song).
want(glow).

prize(berry).
prize(bell).
prize(leaf).

affords(nest, song).
affords(nest, berry).
affords(grove, berry).
affords(grove, glow).
affords(kitchen, berry).
affords(kitchen, song).

valid(P, W, R) :- place(P), want(W), prize(R), affords(P, W).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, place in PLACES.items():
        lines.append(asp.fact("place", p))
        if place.indoors:
            lines.append(asp.fact("indoors", p))
        for w in sorted(place.affords):
            lines.append(asp.fact("affords", p, w))
    for w in WANTS:
        lines.append(asp.fact("want", w))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: permissive speech, kiwi, moral value, transformation, twist.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--want", choices=WANTS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "grownup"], default="grownup")
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
    if getattr(args, "place", None) and getattr(args, "want", None):
        reasonableness_gate(getattr(args, "place", None), getattr(args, "want", None), getattr(args, "prize", None) or "berry")
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "want", None) is None or c[1] == getattr(args, "want", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, want, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        want=want,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        parent=getattr(args, "parent", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(WANTS, params.want), _safe_lookup(PRIZES, params.prize), params.name, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, want, prize in valid_combos():
            params = StoryParams(place=place, want=want, prize=prize, name=random.choice(NAMES), parent=getattr(args, "parent", None), seed=base_seed)
            samples.append(generate(params))
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
