#!/usr/bin/env python3
"""
storyworlds/worlds/remedy_magic_comedy.py
=========================================

A tiny storyworld about a child, a magical mishap, and a comic remedy.

Premise:
- A child loves a little bit of magic.
- The magic goes wrong in a funny way.
- A grown-up sees the trouble and offers a real remedy: a magical fix that
  actually fits the problem.
- The ending proves the world changed: the mess is gone, the mood is lighter,
  and the remedy worked.

The domain stays small on purpose so every generated story feels complete and
grounded in the simulated state.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    prop_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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


@dataclass
class Setting:
    place: str
    indoors: bool
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
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    joke: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    fix: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
        self.zone: set[str] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    prop: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"bubble", "glow", "spark"}),
    "garden": Setting("the garden", False, {"bubble", "glow", "spark"}),
    "bedroom": Setting("the bedroom", True, {"bubble", "glow"}),
    "porch": Setting("the porch", False, {"bubble", "spark"}),
}

TROUBLES = {
    "bubbleburst": Trouble(
        id="bubbleburst",
        verb="blow a magic bubble",
        gerund="blowing magic bubbles",
        rush="blow even bigger bubbles",
        mess="foamy",
        soil="all foamy",
        zone={"floor", "table"},
        joke="one bubble wore a tiny moustache",
        keyword="bubble",
    ),
    "glittersneeze": Trouble(
        id="glittersneeze",
        verb="cast a glitter spell",
        gerund="casting glitter spells",
        rush="sneeze out more glitter",
        mess="sparkly",
        soil="sparkly and sticky",
        zone={"floor", "torso"},
        joke="the sparkles landed on everyone's nose",
        keyword="glitter",
    ),
    "toyfloating": Trouble(
        id="toyfloating",
        verb="make a toy float",
        gerund="making toys float",
        rush="make the toy float higher",
        mess="floated",
        soil="stuck up high",
        zone={"ceiling", "shelf"},
        joke="the toy bobbed like a proud balloon",
        keyword="float",
    ),
    "beanstir": Trouble(
        id="beanstir",
        verb="stir a magic spoonful",
        gerund="stirring a magic spoonful",
        rush="stir the bowl faster",
        mess="splashy",
        soil="splashy and green",
        zone={"shirt", "floor"},
        joke="the spoon spun like a tiny dancer",
        keyword="splash",
    ),
}

REMEDIES = {
    "broomhex": Remedy(
        id="broomhex",
        label="a broom spell",
        phrase="a broom spell with a polite broom",
        fix="sweep the foamy mess away",
        covers={"floor"},
        guards={"foamy"},
        prep="hold still and say the broom spell",
        tail="the foamy bubbles whooshed into a neat little pile",
    ),
    "napkincharm": Remedy(
        id="napkincharm",
        label="a napkin charm",
        phrase="a napkin charm with a shiny napkin",
        fix="wipe the sparkly stickiness off the table and shirt",
        covers={"floor", "torso", "table"},
        guards={"sparkly"},
        prep="fold the napkin charm carefully",
        tail="the glitter came off with one funny swish",
    ),
    "featherpull": Remedy(
        id="featherpull",
        label="a feather pull",
        phrase="a feather pull with one tickly feather",
        fix="gently tug the floating toy back down",
        covers={"ceiling", "shelf"},
        guards={"floated"},
        prep="wiggle the feather and whisper the pull",
        tail="the toy dropped down with a soft plop",
    ),
    "teaspillhex": Remedy(
        id="teaspillhex",
        label="a tea-towel hex",
        phrase="a tea-towel hex with a warm towel",
        fix="soak up the splashy spill",
        covers={"floor", "shirt"},
        guards={"splashy"},
        prep="wave the towel and say the tea-towel hex",
        tail="the green splash vanished into the towel like magic",
    ),
}

PROPS = {
    "spoon": Prop("spoon", "magic spoon", "a magic spoon", "shirt"),
    "hat": Prop("hat", "wizard hat", "a wizard hat", "torso"),
    "wand": Prop("wand", "spark wand", "a spark wand", "hand"),
    "cape": Prop("cape", "little cape", "a little cape", "torso"),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Pip", "Mabel"]
BOY_NAMES = ["Otis", "Finn", "Theo", "Arlo", "Milo", "Ben"]
TRAITS = ["silly", "curious", "playful", "bright", "cheery", "bouncy"]


def compatible(trouble: Trouble, remedy: Remedy, prop: Prop) -> bool:
    return trouble.mess in remedy.guards and prop.region in remedy.covers


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            trouble = _safe_lookup(TROUBLES, tid)
            for rid, remedy in REMEDIES.items():
                for pid, prop in PROPS.items():
                    if compatible(trouble, remedy, prop):
                        combos.append((place, tid, rid))
    return sorted(set(combos))


def select_remedy(trouble: Trouble, prop: Prop) -> Optional[Remedy]:
    for remedy in REMEDIES.values():
        if compatible(trouble, remedy, prop):
            return remedy
    return None


def tell(setting: Setting, trouble: Trouble, remedy: Remedy, prop: Prop,
         hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prop_ent = world.add(Entity(
        id=prop.id, type=prop.id, label=prop.label, phrase=prop.phrase,
        owner=hero.id, caretaker=parent.id, region=prop.region, plural=prop.plural
    ))

    hero.memes["joy"] = 1
    hero.memes["love_magic"] = 1
    world.say(f"{hero_name} was a little {trait} {hero_gender} who loved magic.")
    world.say(f"{hero_name} liked the {prop.label} because {hero.pronoun('possessive')} {prop.label} made every trick feel grand.")
    world.say(f"One day, {hero_name} tried to {trouble.verb} in {setting.place}, and {trouble.joke}.")

    world.para()
    world.say(f"But the spell went wonky, and the room got {trouble.soil}.")
    hero.meters[trouble.mess] += 1
    hero.memes["trouble"] += 1

    world.say(f"{hero_name}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} noticed the silly mess right away.")
    world.say(f"\"That's a funny-looking problem,\" {parent.pronoun().capitalize()} said. \"We need a remedy.\"")

    world.para()
    world.say(f"{hero_name} wanted to {trouble.rush}, but {parent.pronoun('subject')} shook {parent.pronoun('possessive')} head.")
    world.say(f"\"Not more chaos,\" {parent.pronoun().capitalize()} said. \"First we use {remedy.label}.\"")
    world.say(f"{parent.pronoun().capitalize()} told {hero_name} to {remedy.prep}, because {remedy.fix}.")

    prop_ent.worn_by = hero.id
    hero.memes["worry"] += 1
    hero.memes["hope"] += 1

    world.para()
    hero.memes["brave"] += 1
    hero.meters[trouble.mess] += 0.1
    prop_ent.meters["clean"] = 1

    world.say(f"{hero_name} tried the {remedy.phrase}, and the magic behaved at last.")
    world.say(f"{remedy.tail.capitalize()}, so the {prop.label} stayed fine and the mess stopped being funny in the bad way.")
    hero.memes["joy"] += 2
    hero.memes["trouble"] = 0

    world.facts.update(
        hero=hero,
        parent=parent,
        prop=prop_ent,
        trouble=trouble,
        remedy=remedy,
        setting=setting,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trouble = _safe_fact(world, f, "trouble")
    remedy = _safe_fact(world, f, "remedy")
    return [
        f'Write a short comedy story for a young child about magic, a problem, and a remedy using the word "{trouble.keyword}".',
        f"Tell a funny story where {hero.id} tries to {trouble.verb} and a grown-up uses {remedy.label} as a remedy.",
        f"Write a gentle magical comedy about a child, a messy spell, and a remedy that actually fixes the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    trouble = _safe_fact(world, f, "trouble")
    remedy = _safe_fact(world, f, "remedy")
    prop = _safe_fact(world, f, "prop")
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"What did {hero.id} try to do in {setting.place}?",
            answer=f"{hero.id} tried to {trouble.verb} in {setting.place}.",
        ),
        QAItem(
            question=f"Why did the grown-up call for a remedy?",
            answer=f"The spell turned into a silly mess, so the grown-up used {remedy.label} as a remedy to fix it.",
        ),
        QAItem(
            question=f"What stayed safe after the remedy worked?",
            answer=f"{prop.label} stayed fine, and the mess was wiped away.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happier and braver once the remedy worked and the trouble was gone.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bubble": QAItem(
        question="What is a bubble?",
        answer="A bubble is a little ball of air inside soap or water, and it can float and pop.",
    ),
    "glitter": QAItem(
        question="Why is glitter hard to clean?",
        answer="Glitter sticks to skin and cloth, so it can be tricky to sweep or wipe away.",
    ),
    "float": QAItem(
        question="What does it mean when something floats?",
        answer="When something floats, it stays up in the air or on top of water instead of dropping right down.",
    ),
    "splash": QAItem(
        question="What happens when something splashes?",
        answer="When something splashes, liquid jumps around and makes a wet mess.",
    ),
    "remedy": QAItem(
        question="What is a remedy?",
        answer="A remedy is a way to fix a problem or make something feel better.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    t = _safe_fact(world, world.facts, "trouble").keyword
    out = [WORLD_KNOWLEDGE["remedy"]]
    for key in (t, "glitter" if t == "glitter" else None):
        if key and key in WORLD_KNOWLEDGE:
            out.append(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "glittersneeze", "napkincharm", "hat", "Mina", "girl", "mother", "curious"),
    StoryParams("garden", "bubbleburst", "broomhex", "wand", "Milo", "boy", "father", "silly"),
    StoryParams("bedroom", "toyfloating", "featherpull", "cape", "Ivy", "girl", "mother", "bouncy"),
    StoryParams("porch", "beanstir", "teaspillhex", "spoon", "Otis", "boy", "father", "bright"),
]


def explain_rejection(trouble: Trouble, remedy: Remedy, prop: Prop) -> str:
    return (
        f"(No story: {remedy.label} does not fit this trouble and prop together. "
        f"The remedy must guard {trouble.mess} and cover the {prop.region}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "trouble", None) and getattr(args, "remedy", None) and getattr(args, "prop", None):
        trouble = _safe_lookup(TROUBLES, getattr(args, "trouble", None))
        remedy = _safe_lookup(REMEDIES, getattr(args, "remedy", None))
        prop = _safe_lookup(PROPS, getattr(args, "prop", None))
        if not compatible(trouble, remedy, prop):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        for tid in setting.affords:
            if getattr(args, "trouble", None) and tid != getattr(args, "trouble", None):
                continue
            trouble = _safe_lookup(TROUBLES, tid)
            for pid, prop in PROPS.items():
                if getattr(args, "prop", None) and pid != getattr(args, "prop", None):
                    continue
                for rid, remedy in REMEDIES.items():
                    if getattr(args, "remedy", None) and rid != getattr(args, "remedy", None):
                        continue
                    if compatible(trouble, remedy, prop):
                        combos.append((place, tid, rid, pid))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tid, rid, pid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, tid, rid, pid, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TROUBLES, params.trouble),
        _safe_lookup(REMEDIES, params.remedy),
        _safe_lookup(PROPS, params.prop),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
trouble_at_risk(T, P) :- trouble(T), prop(P), mess_of(T, M), guards(R, M), covers(R, X), region_of(P, X).
compatible(T, R, P) :- trouble_at_risk(T, P), remedy(R), prop(P), mess_of(T, M), guards(R, M), covers(R, X), region_of(P, X).
valid(Place, T, R, P) :- affords(Place, T), compatible(T, R, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("mess_of", tid, trouble.mess))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for m in sorted(remedy.guards):
            lines.append(asp.fact("guards", rid, m))
        for c in sorted(remedy.covers):
            lines.append(asp.fact("covers", rid, c))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("region_of", pid, prop.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic comedy storyworld about a remedy that actually works.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for c in combos:
            print(" ", c)
        return

    samples: list[StorySample] = []
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
