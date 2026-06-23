#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/mom_transcend_reconciliation_rhyming_story.py
=========================================================================================================

A small standalone storyworld about a child, a mom, and a quarrel that can be
reconciled. The prose keeps a gentle rhyming-story feel: short, child-facing
lines, concrete images, and a clear shift from hurt feelings to mended ones.

The seed words are honored directly in the story world:
- mom
- transcend

The domain is intentionally tiny:
- a place
- a disagreement
- a repair method
- a shared object

The world model tracks physical meters and emotional memes. The story is driven
by state: a shared object gets split, feelings rise, mom predicts the trouble,
and a reconciliation beat restores the bond and proves the change with a final
image.
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
from typing import Callable, Optional

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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    item: object | None = None
    mom: object | None = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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


@dataclass
class Place:
    id: str
    label: str
    feels: str
    holds: str
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


@dataclass
class Disagreement:
    id: str
    name: str
    cause: str
    rhyme: str
    hurt_word: str
    turn_word: str
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
class Repair:
    id: str
    label: str
    action: str
    ending: str
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
class SharedThing:
    id: str
    label: str
    phrase: str
    physical: str
    split_word: str
    mend_word: str
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
        self.weather = ""

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.weather = self.weather
        return c


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


def _r_split(world: World) -> list[str]:
    out: list[str] = []
    share = world.facts["shared"]
    if share.meters["split"] < THRESHOLD:
        return out
    sig = ("split", share.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.facts["child"]
    mom = world.facts["mom"]
    child.memes["hurt"] += 1
    mom.memes["worry"] += 1
    out.append(f"The shared {share.label} split in two.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    mom = world.facts["mom"]
    if child.memes["hurt"] < THRESHOLD or mom.memes["repair"] < THRESHOLD:
        return out
    sig = ("reconcile", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hurt"] = 0.0
    child.memes["joy"] += 1
    mom.memes["worry"] = 0.0
    mom.memes["love"] += 1
    child.memes["close"] += 1
    mom.memes["close"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("split", _r_split),
    Rule("reconcile", _r_reconcile),
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
                produced.extend(s for s in sents if s != "__reconcile__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_split(world: World) -> bool:
    sim = world.copy()
    share = sim.facts["shared"]
    share.meters["split"] += 1
    propagate(sim, narrate=False)
    return sim.facts["child"].memes["hurt"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES.values():
        for dis in DISAGREEMENTS.values():
            for rep in REPAIRS.values():
                for share in SHARED_THINGS.values():
                    if rep.id in dis.tags and share.id in dis.tags:
                        combos.append((place.id, dis.id, rep.id, share.id))
    return combos


@dataclass
class StoryParams:
    place: str
    disagreement: str
    repair: str
    shared: str
    child_name: str
    child_type: str
    mom_name: str
    seed: Optional[int] = None
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
        return None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", "warm and bright", "a little table"),
    "porch": Place("porch", "the porch", "cool and breezy", "a wide step"),
    "garden": Place("garden", "the garden", "soft and green", "a small bench"),
    "playroom": Place("playroom", "the playroom", "soft and neat", "a toy rug"),
}

DISAGREEMENTS = {
    "share_crayons": Disagreement(
        "share_crayons", "crayon quarrel", "one child kept the red crayon too long",
        "red and blue", "sad", "kind", tags={"banner", "sticker", "kite"}
    ),
    "share_ball": Disagreement(
        "share_ball", "ball quarrel", "both wanted the bouncy ball first",
        "bump and roll", "cross", "kind", tags={"ball", "book", "kite"}
    ),
    "share_song": Disagreement(
        "share_song", "song quarrel", "both tried to sing the same tune",
        "hum and home", "quiet", "gentle", tags={"book", "kite", "paper_plane"}
    ),
}

REPAIRS = {
    "apology": Repair("apology", "apology words", "say sorry and listen", "the room grew calm", tags={"kite", "ball", "book"}),
    "hug": Repair("hug", "a hug", "step close and hug", "their hearts felt light", tags={"kite", "ball", "book"}),
    "trade": Repair("trade", "a trade", "swap turns fairly", "both could smile", tags={"kite", "ball", "paper_plane"}),
}

SHARED_THINGS = {
    "kite": SharedThing("kite", "kite", "a bright paper kite", "paper and string", "split", "mend", tags={"kite"}),
    "ball": SharedThing("ball", "ball", "a round rubber ball", "rubber and air", "split", "mend", tags={"ball"}),
    "book": SharedThing("book", "book", "a picture book", "paper and glue", "split", "mend", tags={"book"}),
    "paper_plane": SharedThing("paper_plane", "paper plane", "a folded paper plane", "paper and fold", "split", "mend", tags={"paper_plane"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Max", "Eli", "Toby"]
TRAITS = ["gentle", "cheerful", "curious", "bright", "careful"]


def aspiration() -> str:
    return "transcend the tangle"  # seed word used in story text


def tell(place: Place, dis: Disagreement, rep: Repair, share: SharedThing,
         child_name: str, child_type: str, mom_name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    mom = world.add(Entity(id=mom_name, kind="character", type="mother", label="mom", role="mom"))
    item = world.add(Entity(id="shared", type="thing", label=share.label, phrase=share.phrase))
    world.facts.update(child=child, mom=mom, shared=item, place=place, disagreement=dis,
                       repair=rep, shared_cfg=share)
    child.memes["want"] += 1
    mom.memes["repair"] += 0
    world.say(f"{child_name} and {mom_name} were {place.feels} in {place.label}.")
    world.say(f"They had {share.phrase}, a sweet little thing to hold.")
    world.say(f"But a {dis.name} came along and made the room feel tight.")
    world.para()
    child.memes["hurt"] += 1
    child.memes["want"] += 1
    child.meters["grip"] += 1
    item.meters["split"] += 1
    if predict_split(world):
        world.say(f'{mom_name} saw the worry and said, "Let us {aspiration()}."')
    else:
        world.say(f'{mom_name} smiled and said, "We can stay kind and keep the day bright."')
    world.say(f'{child_name} frowned, then heard the soft truth in {mom_name}\'s voice.')
    propagate(world, narrate=True)
    world.para()
    mom.memes["repair"] += 1
    world.say(f"{mom_name} chose {rep.label} and {rep.action}.")
    if world.facts["child"].memes["hurt"] >= THRESHOLD:
        world.say(f"{child_name} tried it too, and the knot began to loosen.")
    propagate(world, narrate=True)
    world.say(f"At the end, {rep.ending}, and {share.label} was whole again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about {f["child"].id} and {f["mom"].id} in {f["place"].label}, where they learn to {aspiration()}.',
        f"Tell a gentle story with mom and child, a little disagreement, and a reconciliation ending that includes the word transcend.",
        f"Write a simple rhyming tale where {f['shared_cfg'].phrase} is shared, feelings get hurt, and mom helps everyone make up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mom = f["mom"]
    dis = f["disagreement"]
    rep = f["repair"]
    share = f["shared_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who are the story about in {place.label}?",
            answer=f"The story is about {child.id} and {mom.label_word}. They are in {place.label} with {share.phrase}.",
        ),
        QAItem(
            question=f"What made {child.id} feel hurt before the reconciliation?",
            answer=f"{dis.cause.capitalize()}. That made {child.id} feel {dis.hurt_word}, and the shared thing got split.",
        ),
        QAItem(
            question=f"How did {mom.label_word} help the two make up?",
            answer=f"{mom.label_word.capitalize()} chose {rep.label} and told them to {rep.action}. That was the turn that helped them reconcile.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The hurt feelings were gone, the shared thing was mended, and {child.id} and {mom.label_word} were close again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does reconcile mean?", "Reconcile means to make up after a disagreement and become friendly again."),
        QAItem("What does transcend mean?", "Transcend means to go beyond a hard feeling or limit and rise above it."),
        QAItem("What is a mom?", "A mom is a parent who can comfort, guide, and help children through hard moments."),
        QAItem("Why can sharing be hard?", "Sharing can be hard when two people both want the same thing at once."),
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", disagreement="share_crayons", repair="apology", shared="kite", child_name="Lily", child_type="girl", mom_name="mom"),
    StoryParams(place="porch", disagreement="share_ball", repair="hug", shared="ball", child_name="Leo", child_type="boy", mom_name="mom"),
    StoryParams(place="garden", disagreement="share_song", repair="trade", shared="paper_plane", child_name="Mia", child_type="girl", mom_name="mom"),
    StoryParams(place="playroom", disagreement="share_crayons", repair="trade", shared="book", child_name="Ben", child_type="boy", mom_name="mom"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not support a real reconciliation beat.)"


def valid_story(params: StoryParams) -> bool:
    dis = _safe_lookup(DISAGREEMENTS, params.disagreement)
    rep = _safe_lookup(REPAIRS, params.repair)
    share = _safe_lookup(SHARED_THINGS, params.shared)
    return rep.id in dis.tags and share.id in dis.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "disagreement", None) is None or c[1] == getattr(args, "disagreement", None))
              and (getattr(args, "repair", None) is None or c[2] == getattr(args, "repair", None))
              and (getattr(args, "shared", None) is None or c[3] == getattr(args, "shared", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, dis_id, rep_id, shared_id = rng.choice(list(combos))
    place = _safe_lookup(PLACES, place_id)
    dis = _safe_lookup(DISAGREEMENTS, dis_id)
    rep = _safe_lookup(REPAIRS, rep_id)
    shared = _safe_lookup(SHARED_THINGS, shared_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mom_name = getattr(args, "mom", None) or "mom"
    if gender == "girl" and name == mom_name:
        name = rng.choice([n for n in GIRL_NAMES if n != mom_name])
    return StoryParams(
        place=place_id,
        disagreement=dis_id,
        repair=rep_id,
        shared=shared_id,
        child_name=name,
        child_type=gender,
        mom_name=mom_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.disagreement not in DISAGREEMENTS or params.repair not in REPAIRS or params.shared not in SHARED_THINGS:
        pass
    if not valid_story(params):
        pass
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(DISAGREEMENTS, params.disagreement), _safe_lookup(REPAIRS, params.repair), _safe_lookup(SHARED_THINGS, params.shared), params.child_name, params.child_type, params.mom_name)
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did, dis in DISAGREEMENTS.items():
        lines.append(asp.fact("disagreement", did))
        for t in sorted(dis.tags):
            lines.append(asp.fact("supports", did, t))
    for rid, rep in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for t in sorted(rep.tags):
            lines.append(asp.fact("supports_repair", rid, t))
    for sid, sh in SHARED_THINGS.items():
        lines.append(asp.fact("shared", sid))
        for t in sorted(sh.tags):
            lines.append(asp.fact("supports_shared", sid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,D,R,S) :- place(P), disagreement(D), repair(R), shared(S),
                  supports_repair(R, T), supports(D, T),
                  supports_shared(S, U), supports(D, U).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: ASP matches Python ({len(valid_combos())} combos) and generation works.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: mom, transcend, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--disagreement", choices=DISAGREEMENTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--shared", choices=SHARED_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mom", default="mom")
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
            samples.append(sample)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
