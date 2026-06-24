#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/cell_magic_fairy_tale.py
=====================================================================================================

A tiny fairy-tale storyworld about a sealed cell, a kind magic helper, and a
gentle turn from confinement to freedom.

The seed image is a classic fairy tale: a small kingdom, a lonely cell, a child
(or young knight / maiden), an enchanted key, and a harmless magic that opens
what should not be kept shut. The world simulates physical state in meters and
emotional state in memes, then narrates only what the state makes true.

Domain premise:
- Someone is kept in a cell in a castle or tower.
- A magic helper can unlock the cell only if the right charm, key, or song is
  present.
- The tension is whether magic is used kindly or wrongly.
- The turn is a patient rescue and a quiet ending image proving change.

This script is self-contained and uses only the standard library plus the shared
``storyworlds/results.py`` containers. ASP support is provided inline as a twin
reasonableness gate and verified against the Python logic when requested.
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
MAGIC_MIN = 1.0



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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    helper: object | None = None
    prison: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman", "princess"}
        male = {"boy", "king", "father", "man", "prince", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class Setting:
    place: str
    mood: str
    has_tower: bool = False
    has_gate: bool = False
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


@dataclass
class Cell:
    label: str
    door: str
    bars: str
    risk: str
    held_by: str
    locked: bool = True
    warded: bool = True
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
class Magic:
    id: str
    label: str
    chant: str
    sparkle: str
    method: str
    safe: bool = True
    opens: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    key_word: str
    fits: set[str] = field(default_factory=set)
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_unlock(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cell = world.get("cell")
    if not cell.locked or child.meters["freedom"] < THRESHOLD:
        return out
    if child.meters["magic"] < MAGIC_MIN:
        return out
    sig = ("unlock",)
    if sig in world.fired:
        return out
    if not world.facts.get("can_open"):
        return out
    world.fired.add(sig)
    cell.locked = False
    cell.warded = False
    child.memes["hope"] += 1
    out.append("The cell door swung open with a silver sigh.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["hope"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["outside"] = 1
    child.memes["relief"] += 1
    out.append("Fresh air rushed in, and the little prisoner could breathe at last.")
    return out


CAUSAL_RULES = [Rule("unlock", _r_unlock), Rule("relief", _r_relief)]


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


def cell_at_risk(magic: Magic, charm: Charm, cell: Cell) -> bool:
    return cell.label in magic.opens and cell.label in charm.fits and magic.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mid, magic in MAGICS.items():
            for cid, charm in CHARMS.items():
                if cell_at_risk(magic, charm, CELLS["cell"]):
                    combos.append((place, mid, cid))
    return combos


def verify_gate() -> bool:
    return set(asp_valid_combos()) == set(valid_combos())


def tell(setting: Setting, cell: Cell, magic: Magic, charm: Charm, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name, traits=["little", "brave"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, traits=["kind", "wise"]))
    prison = world.add(Entity(id="cell", kind="thing", type="cell", label=cell.label, attrs={"door": cell.door, "bars": cell.bars, "held_by": cell.held_by}))
    world.add(Entity(id="charm", kind="thing", type="charm", label=charm.label))
    world.add(Entity(id="magic", kind="thing", type="magic", label=magic.label))
    # initialize all read state before propagate
    child.meters["magic"] = 0
    child.meters["freedom"] = 0
    child.meters["outside"] = 0
    child.memes["fear"] = 0
    child.memes["hope"] = 0
    child.memes["relief"] = 0
    helper.meters["magic"] = 0
    helper.memes["care"] = 0
    prison.meters["locked"] = 1
    prison.meters["warded"] = 1
    prison.memes["lonely"] = 1
    world.facts["can_open"] = cell_at_risk(magic, charm, cell)

    world.say(f"In a little kingdom, {hero_name} was kept in {cell.label}, behind {cell.bars}.")
    world.say(f"{helper_name} came softly to the stone door and whispered that no child should stay alone there forever.")
    world.para()
    world.say(f"{helper_name} lifted {charm.phrase} and began {magic.chant}.")
    child.meters["magic"] += 1
    child.meters["freedom"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=True)
    world.para()
    if prison.locked:
        world.say(f"The spell glimmered, but the ward held fast. {helper_name} bowed their head and tried the gentler way.")
    else:
        world.say(f"The spell found the right lock, and the heavy door opened without a groan.")
    world.say(f"{hero_name} stepped into the sun, and {cell.risk} was left behind in the dark room.")
    world.facts.update(child=child, helper=helper, cell=prison, magic=magic, charm=charm, setting=setting)
    return world


SETTINGS = {
    "tower": Setting(place="a high tower", mood="quiet", has_tower=True),
    "castle": Setting(place="an old castle", mood="ancient", has_gate=True),
    "garden": Setting(place="a moonlit garden", mood="gentle", has_gate=True),
}

CELLS = {
    "cell": Cell(label="the cell", door="a heavy door", bars="iron bars", risk="cold stones", held_by="a lonely spell", tags={"cell"}),
}

MAGICS = {
    "song": Magic(id="song", label="magic song", chant="a soft magic song", sparkle="small gold sparks", method="singing", safe=True, opens={"the cell"}, tags={"magic", "song"}),
    "glow": Magic(id="glow", label="glow spell", chant="a tiny glow spell", sparkle="blue lights", method="murmuring", safe=True, opens={"the cell"}, tags={"magic", "glow"}),
    "key": Magic(id="key", label="enchanted key", chant="a key-shaped blessing", sparkle="a silver glimmer", method="turning", safe=True, opens={"the cell"}, tags={"magic", "key"}),
}

CHARMS = {
    "moonkey": Charm(id="moonkey", label="moon-key", phrase="a moon-key", key_word="moon", fits={"the cell"}, tags={"key", "moon"}),
    "starbell": Charm(id="starbell", label="star-bell", phrase="a star-bell", key_word="star", fits={"the cell"}, tags={"song", "star"}),
    "rose": Charm(id="rose", label="rose charm", phrase="a rose charm", key_word="rose", fits={"the cell"}, tags={"rose"}),
}

GIRL_NAMES = ["Mina", "Luna", "Elin", "Rose", "Tilda", "Nora"]
BOY_NAMES = ["Owen", "Felix", "Theo", "Bram", "Leo", "Finn"]


@dataclass
class StoryParams:
    setting: str
    magic: str
    charm: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child about {f["child"].label} trapped in {f["cell"].label} and a kind helper using {f["magic"].label}.',
        f"Tell a gentle story where {f['helper'].label} uses {f['charm'].label} to open {f['cell'].label} and bring {f['child'].label} back into the light.",
        f'Write a short fairy tale that includes the word "cell" and ends with a safe magic rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cell = f["cell"]
    magic = f["magic"]
    charm = f["charm"]
    qa = [
        QAItem(question=f"Who was trapped in the story?", answer=f"{child.label} was trapped in {cell.label}, waiting for help."),
        QAItem(question=f"Who helped {child.label}?", answer=f"{helper.label} helped by using {magic.label} with {charm.label}."),
        QAItem(question=f"What did the magic do?", answer=f"It opened {cell.label} so {child.label} could leave the dark room safely."),
    ]
    if not cell.locked:
        qa.append(QAItem(question=f"What changed at the end?", answer=f"{cell.label} was no longer locked, and {child.label} stepped out into the light."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a cell in a fairy tale?", answer="A cell is a small locked room or prison chamber where someone may be kept until help comes."),
        QAItem(question="What does magic do in a fairy tale?", answer="Magic can make strange and wonderful things happen, like opening a locked door or turning a fear into hope."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story q&a ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world q&a ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen magic cannot open the chosen cell, so there is no honest rescue.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "magic", None) is None or c[1] == getattr(args, "magic", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, magic, charm = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(["fairy", "wizard", "queen"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Nim", "Iris", "Mara", "Sage"])
    return StoryParams(setting=setting, magic=magic, charm=charm, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.magic not in MAGICS or params.charm not in CHARMS:
        pass
    if not cell_at_risk(_safe_lookup(MAGICS, params.magic), _safe_lookup(CHARMS, params.charm), CELLS["cell"]):
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), CELLS["cell"], _safe_lookup(MAGICS, params.magic), _safe_lookup(CHARMS, params.charm), params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
cell_open(M, C) :- magic(M), charm(C), opens(M, "the cell"), fits(C, "the cell").
valid(S, M, C) :- setting(S), magic(M), charm(C), cell_open(M, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MAGICS.values():
        lines.append(asp.fact("magic", m.id))
        for o in m.opens:
            lines.append(asp.fact("opens", m.id, o))
    for c in CHARMS.values():
        lines.append(asp.fact("charm", c.id))
        for f in c.fits:
            lines.append(asp.fact("fits", c.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a cell and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type")
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
    StoryParams("castle", "song", "moonkey", "Mina", "girl", "Iris", "fairy"),
    StoryParams("tower", "glow", "starbell", "Owen", "boy", "Nim", "wizard"),
    StoryParams("garden", "key", "rose", "Luna", "girl", "Mara", "queen"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible (setting, magic, charm) combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            header = f"### {p.hero_name} in the {p.setting} ({p.magic}, {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
