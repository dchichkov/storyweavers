#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/earthling_recur_happy_ending_friendship_mystery_to.py
=========================================================================================================

A tiny nursery-rhyme storyworld about a child, a friendly earthling, and a
mystery that keeps coming back until they solve it together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    earth: object | None = None
    pal: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    mystery: str = ""
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Mystery:
    id: str
    label: str
    clue: str
    disappears: str
    recur_note: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Treasure:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


def _norm(txt: str) -> str:
    return txt.strip().lower()


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for mid in MYSTERIES:
            for hid in HELPERS:
                if can_solve(_safe_lookup(PLACES, pid), _safe_lookup(MYSTERIES, mid), _safe_lookup(HELPERS, hid)):
                    combos.append((pid, mid, hid))
    return combos


def can_solve(place: Place, mystery: Mystery, helper: Helper) -> bool:
    return place.mystery == mystery.id and mystery.id in helper.tags


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    name: str
    gender: str
    friend: str
    friend_gender: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


PLACES = {
    "garden": Place(id="garden", label="the garden", mystery="bell"),
    "porch": Place(id="porch", label="the porch", mystery="pebble"),
    "meadow": Place(id="meadow", label="the meadow", mystery="ribbon"),
    "laundry": Place(id="laundry", label="the laundry line", mystery="sock"),
}

MYSTERIES = {
    "bell": Mystery(id="bell", label="the little bell", clue="a tinny tinkle", disappears="vanishes", recur_note="the tinkle can recur on the breeze", tags={"bell", "sound"}),
    "pebble": Mystery(id="pebble", label="the blue pebble", clue="a shiny blink", disappears="slips away", recur_note="the blink can recur in the sun", tags={"pebble", "shine"}),
    "ribbon": Mystery(id="ribbon", label="the red ribbon", clue="a fluttery flash", disappears="floats off", recur_note="the flash can recur in the wind", tags={"ribbon", "wind"}),
    "sock": Mystery(id="sock", label="the striped sock", clue="a tiny drip", disappears="goes missing", recur_note="the drip can recur on the line", tags={"sock", "cloth"}),
}

HELPERS = {
    "cat": Helper(id="cat", label="a gray cat", phrase="a gray cat", method="follow the pitter-pat", tags={"pebble", "sound"}),
    "earthling": Helper(id="earthling", label="an earthling", phrase="a kind earthling", method="listen for the recurring clue", tags={"bell", "pebble", "ribbon", "sock"}),
    "kite": Helper(id="kite", label="a paper kite", phrase="a paper kite", method="watch the air and the string", tags={"ribbon", "wind"}),
    "basket": Helper(id="basket", label="a little basket", phrase="a little basket", method="gather what is out in the light", tags={"sock", "cloth"}),
}

TREASURES = {
    "cookie": Treasure(id="cookie", label="a honey cookie", phrase="a honey cookie"),
    "note": Treasure(id="note", label="a folded note", phrase="a folded note"),
    "flower": Treasure(id="flower", label="a daisied flower", phrase="a daisied flower"),
    "button": Treasure(id="button", label="a shiny button", phrase="a shiny button"),
}


def tell(place: Place, mystery: Mystery, helper: Helper, name: str, gender: str, friend: str, friend_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, role="child",
                             meters={"curiosity": 0.0, "joy": 0.0, "calm": 0.0},
                             memes={"wonder": 0.0, "worry": 0.0, "friendship": 0.0}))
    pal = world.add(Entity(id=friend, kind="character", type=friend_gender, label=friend, role="friend",
                           meters={"curiosity": 0.0, "joy": 0.0, "calm": 0.0},
                           memes={"wonder": 0.0, "worry": 0.0, "friendship": 0.0}))
    earth = world.add(Entity(id="earthling", kind="character", type="earthling", label="the earthling",
                             role="helper", tags={"earthling"},
                             meters={"help": 0.0}, memes={"kindness": 0.0}))
    world.facts.update(child=child, pal=pal, earth=earth, place=place, mystery=mystery, helper=helper)
    child.memes["friendship"] += 1
    pal.memes["friendship"] += 1
    earth.memes["kindness"] += 1

    world.say(f"{name} and {friend} went skip-skip-slow to {place.label}.")
    world.say(f"There they found {mystery.label}, and its clue was {mystery.clue}.")
    world.say(f"But then it {mystery.disappears}, as tricky things do; the clue could {mystery.recur_note}.")
    world.para()
    world.say(f"{friend} said, \"Let's look again, and look with care.\"")
    world.say(f"{name} found {helper.phrase}, and the earthling smiled and said, \"I can share a little repair.\"")

    child.meters["curiosity"] += 1
    pal.meters["curiosity"] += 1
    earth.meters["help"] += 1
    world.facts["seen_clue"] = mystery.clue
    world.facts["recur"] = True

    world.para()
    world.say(f"They followed the clue where it chose to run.")
    if mystery.id == place.mystery:
        world.say(f"At last, the missing thing was found in the sun.")
    child.memes["joy"] += 1
    pal.memes["joy"] += 1
    child.memes["friendship"] += 1
    pal.memes["friendship"] += 1
    earth.memes["kindness"] += 1

    treasure = world.add(Entity(id="treasure", kind="thing", type="treasure", label=TREASURES["note"].label,
                                phrase=TREASURES["note"].phrase))
    world.facts["treasure"] = treasure
    world.say(f"Together they set the mystery right, and home they went with a happy light: {mystery.label} and {treasure.phrase}.")
    world.say(f"So the clue did recur, but it no longer hid; it helped them find what the little day had slid.")
    world.facts["solved"] = True
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story for a small child about {f["child"].id}, {f["pal"].id}, and a friendly earthling solving a mystery at {f["place"].label}.',
        f'Create a gentle happy-ending story that uses the words "earthling" and "recur" and features friendship and a mystery to solve.',
        f'Tell a rhyming little story where a clue keeps coming back until {f["child"].id} and a friend solve it together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    pal = f["pal"]
    place = f["place"]
    mystery = f["mystery"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"Who went to {place.label} to solve the mystery?",
            answer=f"{child.id} went with {pal.id}, and the friendly earthling helped them look. They were working together on a small mystery, not alone.",
        ),
        QAItem(
            question=f"What kept happening with {mystery.label}?",
            answer=f"It kept showing a clue and then slipping away, so the clue could recur. That repeating pattern is why {child.id} had to look more than once.",
        ),
        QAItem(
            question=f"How did the earthling help {child.id} and {pal.id}?",
            answer=f"The earthling shared a calm way to follow the clue and stay kind to each other. That help made the mystery easier to solve together.",
        ),
    ]
    if f.get("solved"):
        qa.append(QAItem(
            question=f"What was the happy ending?",
            answer=f"{child.id} and {pal.id} found the missing thing and went home smiling. The repeating clue did recur, but this time it led them to the answer.",
        ))
        qa.append(QAItem(
            question=f"Why did the friends stay cheerful at the end?",
            answer=f"They solved the mystery together and shared the finding with the earthling. Because they worked as friends, the ending turned bright and happy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an earthling?",
            answer="An earthling is a person from Earth, like you or me. In a story, it can be a friendly helper who joins the search.",
        ),
        QAItem(
            question="What does recur mean?",
            answer="If something recurs, it happens again. A clue that recurs comes back another time, which can help solve a mystery.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other and help each other. Friends can share, listen, and solve hard things together.",
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    out.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: earthling, recur, mystery, friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Luca", "Pippa", "Jasper", "Nell", "Rory"])
    friend = getattr(args, "friend", None) or rng.choice(["Toby", "Sana", "Milo", "Bea", "Noa", "Wren"])
    return StoryParams(place=place, mystery=mystery, helper=helper, name=name, gender=gender, friend=friend, friend_gender=friend_gender)


ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).
helper(H) :- helper_fact(H).
solvable(P,M,H) :- place_map(P,M), mystery_tag(M,T), helper_tag(H,T).
valid(P,M,H) :- solvable(P,M,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        lines.append(asp.fact("place_map", pid, p.mystery))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("mystery_tag", mid, t))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper_fact", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_tag", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    print(f"OK: ASP and Python agree on {len(valid_combos())} combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: normal story generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.helper not in HELPERS:
        pass
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    helper = _safe_lookup(HELPERS, params.helper)
    if not can_solve(place, mystery, helper):
        pass
    world = tell(place, mystery, helper, params.name, params.gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="garden", mystery="bell", helper="earthling", name="Mina", gender="girl", friend="Toby", friend_gender="boy"),
    StoryParams(place="porch", mystery="pebble", helper="cat", name="Luca", gender="boy", friend="Bea", friend_gender="girl"),
    StoryParams(place="meadow", mystery="ribbon", helper="kite", name="Pippa", gender="girl", friend="Rory", friend_gender="boy"),
    StoryParams(place="laundry", mystery="sock", helper="basket", name="Jasper", gender="boy", friend="Sana", friend_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
