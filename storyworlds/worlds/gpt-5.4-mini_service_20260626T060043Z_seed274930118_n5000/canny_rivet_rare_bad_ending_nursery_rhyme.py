#!/usr/bin/env python3
"""
storyworlds/worlds/canny_rivet_rare_bad_ending_nursery_rhyme.py
===============================================================

A small nursery-rhyme story world about a canny little helper, a rare shiny
rivet, and a bad ending when the fix comes too late.

The seed image:
- A canny child hears a tiny clink in an old playhouse.
- A rare golden rivet is meant to hold a little gate shut.
- The child tries to be clever, but the gate loosens anyway.
- The ending is a bad one: the treat is lost, the lantern goes out, and the
  rhyme closes on a quiet, wistful note.

This world keeps to nursery-rhyme style: short beats, concrete objects, a
repeated cadence, and simple cause and effect.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    gate: object | None = None
    hero: object | None = None
    prize: object | None = None
    rivet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the old playhouse"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    danger: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Fix:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_ding(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("caution", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("unease", 0.0) < THRESHOLD:
            continue
        if ("ding", actor.id) in world.fired:
            continue
        world.fired.add(("ding", actor.id))
        out.append("A tiny ding went in the air like a warning bell.")
    return out


def _r_fail(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("rush", 0.0) < THRESHOLD:
            continue
        if ("fail", actor.id) in world.fired:
            continue
        if world.facts.get("loss") == "lost treat":
            world.fired.add(("fail", actor.id))
            actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1
            out.append("The little plan went wrong.")
    return out


RULES = [
    Rule("ding", _r_ding),
    Rule("fail", _r_fail),
]


def select_fix(trouble: Trouble, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if trouble.mess in fix.guards and prize.region in fix.covers:
            return fix
    return None


def troubled_by(trouble: Trouble, prize: Prize) -> bool:
    return prize.region in trouble.tags


def predict_bad_end(world: World, actor: Entity, trouble: Trouble, prize_id: str) -> dict:
    sim = world.copy()
    actor2 = sim.get(actor.id)
    actor2.meters["caution"] = actor2.meters.get("caution", 0.0) + 1
    actor2.meters["rush"] = actor2.meters.get("rush", 0.0) + 1
    actor2.memes["unease"] = actor2.memes.get("unease", 0.0) + 1
    prop = sim.get(prize_id)
    if troubled_by(trouble, Prize(prop.label, prop.phrase, prop.type, "lamp")):
        pass
    return {
        "loss": True,
        "fix": False,
    }


def build_nursery_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def setup(world: World, hero: Entity, elder: Entity, prize: Entity, trouble: Trouble) -> None:
    world.say(f"{hero.id} was a canny little {hero.type} who liked to listen to every tiny sound.")
    world.say(
        f"In {world.setting.place}, {hero.id} found a rare little {prize.label} "
        f"that shone like morning honey."
    )
    world.say(
        f"The old place had a {trouble.label} {trouble.id}, and it made a soft clink-clink sound."
    )


def warn(world: World, elder: Entity, hero: Entity, prize: Entity, trouble: Trouble) -> None:
    world.say(
        f'"That {trouble.keyword} may slip," said {elder.id}. "If it slips, '
        f'we may lose {hero.pronoun("possessive")} {prize.label}."'
    )


def try_fix(world: World, hero: Entity, elder: Entity, prize: Entity, trouble: Trouble) -> Optional[Fix]:
    fix = select_fix(trouble, prize)
    if fix is None:
        return None
    world.say(
        f"{hero.id} tried a canny fix and brought out {fix.label}; "
        f"it looked neat in the dim little light."
    )
    return fix


def bad_ending(world: World, hero: Entity, elder: Entity, prize: Entity, trouble: Trouble, fix: Optional[Fix]) -> None:
    world.para()
    world.say(
        f"But the {trouble.keyword} gave a sharp little twang, and the gate let go."
    )
    world.say(
        f"The rare {prize.label} rolled under the floorboard, and no one could reach it."
    )
    world.say(
        f"{elder.id} sighed, and {hero.id} felt the hush of a very bad ending."
    )
    world.say(
        f"The lantern dimmed, the crumb was gone, and the canny trick came too late."
    )


def tell(setting: Setting, trouble: Trouble, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         elder_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="grandmother"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
                             plural=prize_cfg.plural))
    gate = world.add(Entity(id="gate", type="gate", label="little gate"))
    rivet = world.add(Entity(id="rivet", type="rivet", label="rare golden rivet"))

    world.facts.update(hero=hero, elder=elder, prize=prize, trouble=trouble, gate=gate, rivet=rivet)
    setup(world, hero, elder, prize, trouble)
    world.para()
    warn(world, elder, hero, prize, trouble)
    hero.meters["caution"] = 1
    hero.memes["unease"] = 1
    fix = try_fix(world, hero, elder, prize, trouble)
    hero.meters["rush"] = 1
    propagate(world, narrate=True)
    bad_ending(world, hero, elder, prize, trouble, fix)
    world.facts["fix"] = fix
    world.facts["ending"] = "bad"
    return world


SETTING = Setting(place="the old playhouse", indoor=True, affords={"rivet"})
TROUBLES = {
    "rivet": Trouble(
        id="rivet",
        verb="tighten the rivet",
        gerund="tightening the rivet",
        rush="run to the gate",
        mess="loose",
        soil="lost",
        danger="the gate may fall open",
        keyword="rivet",
        tags={"rivet", "rare"},
    ),
    "bell": Trouble(
        id="bell",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="run to the bell rope",
        mess="loud",
        soil="startled",
        danger="the rope may snap",
        keyword="bell",
        tags={"bell"},
    ),
}

PRIZES = {
    "crumb": Prize(
        label="crumb cake",
        phrase="a small crumb cake",
        type="cake",
        region="tray",
    ),
    "star": Prize(
        label="star biscuit",
        phrase="a tiny star biscuit",
        type="biscuit",
        region="tray",
    ),
}

FIXES = [
    Fix(
        id="wedge",
        label="a wooden wedge",
        covers={"tray"},
        guards={"loose"},
        prep="set a wooden wedge beneath the gate",
        tail="set the wedge under the gate",
    ),
    Fix(
        id="pin",
        label="a spare pin",
        covers={"tray"},
        guards={"loose"},
        prep="hold the gate steady with a spare pin",
        tail="held the gate with the spare pin",
    ),
]

NAMES_GIRL = ["Mina", "Lena", "Nell", "Tess", "Pippa", "Rose"]
NAMES_BOY = ["Pip", "Tom", "Ben", "Sam", "Noah", "Jasper"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    prize: str
    name: str
    gender: str
    elder: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery rhyme about a canny child, a rare rivet, and a bad ending.',
        f"Tell a gentle rhyme where {f['hero'].id} tries to fix a {f['trouble'].keyword} problem "
        f"for {f['elder'].label}, but the precious {f['prize'].label} is lost.",
        f"Write a simple story with the words canny, rivet, and rare, and end it sadly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, trouble = f["hero"], f["elder"], f["prize"], f["trouble"]
    fix = f.get("fix")
    qas = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a canny little {hero.type}, and {elder.label}, who watches over the old playhouse.",
        ),
        QAItem(
            question=f"What rare thing did {hero.id} find?",
            answer=f"{hero.id} found a rare golden rivet, and it shone like morning honey in the dim little room.",
        ),
        QAItem(
            question=f"What went wrong at the end?",
            answer=f"The {trouble.keyword} slipped, the gate gave way, and the rare {prize.label} rolled under the floorboard where no one could reach it.",
        ),
    ]
    if fix:
        qas.append(
            QAItem(
                question=f"How did {hero.id} try to help before the bad ending?",
                answer=f"{hero.id} tried a canny fix with {fix.label}, hoping to keep the gate steady and save the treat.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rivet?",
            answer="A rivet is a small metal piece used to fasten things together so they stay joined.",
        ),
        QAItem(
            question="What does canny mean?",
            answer="Canny means clever and careful, as if someone is thinking ahead before acting.",
        ),
        QAItem(
            question="What does rare mean?",
            answer="Rare means not common. A rare thing is special because you do not see it every day.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
% A trouble is at risk when it targets the same region as the prize.
at_risk(T, P) :- trouble(T), prize(P), troubled_region(T, R), prize_region(P, R).

% A fix is compatible when it guards the troubled mess and covers the prize region.
compatible(F, T, P) :- fix(F), at_risk(T, P),
                       guards(F, M), trouble_mess(T, M),
                       covers(F, R), prize_region(P, R).

valid_story(T, P) :- at_risk(T, P), compatible(_, T, P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "playhouse")]
    if SETTING.indoor:
        lines.append(asp.fact("indoor", "playhouse"))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_mess", tid, t.mess))
        lines.append(asp.fact("troubled_region", tid, "tray"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = sorted((t, p) for t in TROUBLES for p in PRIZES if troubled_by(_safe_lookup(TROUBLES, t), _safe_lookup(PRIZES, p)) and select_fix(_safe_lookup(TROUBLES, t), _safe_lookup(PRIZES, p)))
    cl = sorted(set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story")))
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", py)
    print("asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a canny child, a rare rivet, and a bad ending.")
    ap.add_argument("--place", choices=["playhouse"], default="playhouse")
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"], default="grandmother")
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
    if getattr(args, "trouble", None) and getattr(args, "prize", None):
        if not troubled_by(_safe_lookup(TROUBLES, getattr(args, "trouble", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if not select_fix(_safe_lookup(TROUBLES, getattr(args, "trouble", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    troubles = [getattr(args, "trouble", None)] if getattr(args, "trouble", None) else list(TROUBLES)
    prizes = [getattr(args, "prize", None)] if getattr(args, "prize", None) else list(PRIZES)
    combos = [(t, p) for t in troubles for p in prizes if troubled_by(_safe_lookup(TROUBLES, t), _safe_lookup(PRIZES, p)) and select_fix(_safe_lookup(TROUBLES, t), _safe_lookup(PRIZES, p))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    trouble, prize = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place="playhouse", trouble=trouble, prize=prize, name=name, gender=gender, elder=getattr(args, "elder", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, _safe_lookup(TROUBLES, params.trouble), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.elder)
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
    StoryParams(place="playhouse", trouble="rivet", prize="crumb", name="Mina", gender="girl", elder="grandmother"),
    StoryParams(place="playhouse", trouble="rivet", prize="star", name="Pip", gender="boy", elder="grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
