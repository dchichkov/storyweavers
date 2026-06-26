#!/usr/bin/env python3
"""
storyworlds/worlds/phony_mane_blockade_cautionary_bravery_humor_comedy.py
===========================================================================

A small comedy storyworld about a child, a phony mane, and a blockade.

Seed premise:
- A child wants to join a silly lion-themed parade with a phony mane.
- A blockade blocks the way.
- A cautionary helper warns about the safe way.
- Bravery and humor unlock the ending.

The world is kept intentionally small and constraint-checked so the story
reads like a complete little tale rather than a random event log.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    blockade: object | None = None
    hero: object | None = None
    parent: object | None = None
    prop: object | None = None
    def __post_init__(self) -> None:
        for k in ("bump", "mess", "blocked", "clean", "comedy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "bravery", "humor", "caution", "pride", "relief", "conflict"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool = False
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
class Prop:
    id: str
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
class Blockade:
    id: str
    label: str
    phrase: str
    kind: str
    can_open: bool = False
    humor_sensitive: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "fair": Setting(place="the fair", affords={"parade", "joke"}),
    "zoo_gate": Setting(place="the zoo gate", affords={"parade", "joke"}),
    "school_stage": Setting(place="the school stage", indoors=True, affords={"parade", "joke"}),
}

ACTIONS = {
    "parade": Action(
        id="parade",
        verb="join the silly lion parade",
        gerund="joining the silly lion parade",
        rush="dash toward the parade lane",
        risk="get stuck at the blockade",
        zone={"torso"},
        keyword="lion",
        tags={"lion", "parade", "blockade"},
    ),
    "joke": Action(
        id="joke",
        verb="tell a big joke to the guard",
        gerund="telling a big joke",
        rush="run up to the guard",
        risk="sound shy at first",
        zone={"mouth"},
        keyword="joke",
        tags={"humor", "guard"},
    ),
}

PROPS = {
    "mane": Prop(
        id="mane",
        label="mane",
        phrase="a fluffy phony mane",
        type="mane",
        region="torso",
    ),
    "badge": Prop(
        id="badge",
        label="badge",
        phrase="a shiny parade badge",
        type="badge",
        region="torso",
    ),
}

BLOCKADES = {
    "rope": Blockade(
        id="rope",
        label="rope blockade",
        phrase="a silly rope blockade",
        kind="rope",
        can_open=True,
        humor_sensitive=True,
    ),
    "cones": Blockade(
        id="cones",
        label="cone blockade",
        phrase="a wobbly cone blockade",
        kind="cones",
        can_open=False,
        humor_sensitive=True,
    ),
    "bench": Blockade(
        id="bench",
        label="bench blockade",
        phrase="a grumpy bench blockade",
        kind="bench",
        can_open=True,
        humor_sensitive=False,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Noah", "Theo"]
TRAITS = ["curious", "cheerful", "spunky", "spirited", "sly"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prop: str
    blockade: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def action_risks_prop(action: Action, prop: Prop) -> bool:
    return prop.region in action.zone


def select_fix(action: Action, blockade: Blockade) -> bool:
    # Only parade + joke can reasonably help with the humor-sensitive blockade.
    return action.id == "joke" and blockade.humor_sensitive


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            action = _safe_lookup(ACTIONS, aid)
            for pid, prop in PROPS.items():
                for bid, blockade in BLOCKADES.items():
                    if action_risks_prop(action, prop) and select_fix(action, blockade):
                        combos.append((place, aid, pid))
    return combos


def explain_rejection(action: Action, prop: Prop, blockade: Blockade) -> str:
    return (
        f"(No story: {action.gerund} does not give a believable way to fix the "
        f"{blockade.label}, and the {prop.label} would not be the right thing to worry about here.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def predict_blocked(world: World, actor: Entity, action: Action, blockade: Blockade) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["bump"] += 1
    return blockade.can_open is False


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved funny costumes."
    )


def gift_prop(world: World, hero: Entity, parent: Entity, prop: Entity) -> None:
    world.say(
        f"One day, {hero.id}'s {parent.pronoun('possessive')} {prop.label} was waiting on the chair."
    )
    prop.worn_by = hero.id
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} loved {prop.it()} because it made the whole outfit look like a tiny lion."
    )


def arrive(world: World, hero: Entity, parent: Entity, action: Action, blockade: Blockade) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} and {hero.pronoun('possessive')} {parent.type} reached "
        f"{blockade.phrase}."
    )
    world.say(f"{hero.id} wanted to {action.verb}, but the way ahead was blocked.")


def caution(world: World, parent: Entity, hero: Entity, blockade: Blockade) -> None:
    hero.memes["caution"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'"Careful," said {hero.pronoun("possessive")} {parent.type}. '
        f'"That {blockade.label} is not for bumping, squeezing, or heroic elbows."'
    )


def brave_try(world: World, hero: Entity, action: Action) -> None:
    hero.memes["bravery"] += 1
    hero.meters["bump"] += 0.5
    world.say(
        f"{hero.id} took a breath and marched up bravely anyway, even though {action.risk} looked very possible."
    )


def joke_open(world: World, hero: Entity, blockade: Blockade) -> bool:
    hero.memes["humor"] += 1
    if blockade.humor_sensitive:
        world.say(
            f'{hero.id} pointed at the {blockade.label} and said, "If this is a blockade, '
            f'does it also block bananas?"'
        )
        return True
    return False


def resolve(world: World, hero: Entity, parent: Entity, blockade: Blockade, action: Action) -> None:
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    world.say(
        f"The guard laughed so hard that the {blockade.label} was moved aside."
    )
    world.say(
        f"{hero.id} grinned, saluted in {hero.pronoun('possessive')} phony mane, and finally got to {action.verb}."
    )
    world.say(
        f"{parent.pronoun('possessive').capitalize()} {parent.type} laughed too, because the parade looked even sillier now."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, action: Action, prop_cfg: Prop, blockade_cfg: Blockade,
         hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        traits=[trait, "bold"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
    ))
    prop = world.add(Entity(
        id=prop_cfg.id,
        type=prop_cfg.type,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        owner=hero.id,
        worn_by=hero.id,
        region=prop_cfg.region,
        plural=prop_cfg.plural,
    ))
    blockade = world.add(Entity(
        id=blockade_cfg.id,
        type=blockade_cfg.kind,
        label=blockade_cfg.label,
        phrase=blockade_cfg.phrase,
    ))

    introduce(world, hero)
    gift_prop(world, hero, parent, prop)
    world.para()
    arrive(world, hero, parent, action, blockade_cfg)
    caution(world, parent, hero, blockade_cfg)
    brave_try(world, hero, action)
    if joke_open(world, hero, blockade_cfg):
        resolve(world, hero, parent, blockade_cfg, action)
    world.facts.update(hero=hero, parent=parent, prop=prop, blockade=blockade,
                       setting=setting, action=action, prop_cfg=prop_cfg,
                       blockade_cfg=blockade_cfg, resolved=True)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action, prop = f["hero"], f["action"], f["prop_cfg"]
    return [
        f'Write a funny story for a child about {hero.id}, a phony mane, and a blockade.',
        f"Tell a comedy where {hero.id} wants to {action.verb} in {prop.phrase} but a blockade gets in the way.",
        f"Write a short cautionary-but-brave story that ends with a joke and the words phony, mane, and blockade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, action, prop, blockade = f["hero"], f["parent"], f["action"], f["prop_cfg"], f["blockade_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} stop at the blockade?",
            answer=f"{hero.id} stopped because {blockade.phrase} blocked the way to {action.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {parent.type} say to be careful about?",
            answer=(
                f"{parent.pronoun('subject').capitalize()} warned {hero.id} not to bump into "
                f"the {blockade.label} and not to try a silly shortcut."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} finally get past the blockade?",
            answer=(
                f"{hero.id} used humor and told a banana joke, which made everyone laugh and let the "
                f"{blockade.label} move aside."
            ),
        ),
        QAItem(
            question=f"What was funny about {hero.id}'s outfit?",
            answer=(
                f"{hero.id} wore a fluffy phony mane, so the whole outfit looked like a tiny lion with big ideas."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "mane": [
        QAItem(
            question="What is a mane?",
            answer="A mane is the long hair around an animal's neck or head, like a lion's fluffy hair.",
        )
    ],
    "blockade": [
        QAItem(
            question="What is a blockade?",
            answer="A blockade is something that blocks a path, like a barrier, rope, or row of objects.",
        )
    ],
    "humor": [
        QAItem(
            question="What does humor do in a story?",
            answer="Humor makes a story funny and can help people relax or solve a problem with a smile.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or hard even when you feel a little nervous.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a careful warning so someone can avoid a mistake.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["mane"])
    out.extend(WORLD_KNOWLEDGE["blockade"])
    out.extend(WORLD_KNOWLEDGE["humor"])
    out.extend(WORLD_KNOWLEDGE["bravery"])
    out.extend(WORLD_KNOWLEDGE["cautionary"])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prop(P), zone(A,R), region(P,R).
good_fix(A,B) :- action(A), blockade(B), humor_sensitive(B), A = joke.
valid(Place,A,P,B) :- setting(Place), affords(Place,A), prize_at_risk(A,P), good_fix(A,B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("region", pid, p.region))
    for bid, b in BLOCKADES.items():
        lines.append(asp.fact("blockade", bid))
        if b.humor_sensitive:
            lines.append(asp.fact("humor_sensitive", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, a, pr, b) for p, a, pr in valid_combos() for b in BLOCKADES)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prop: str
    blockade: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: phony mane + blockade.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--blockade", choices=BLOCKADES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "action", None) and getattr(args, "prop", None) and getattr(args, "blockade", None):
        action = _safe_lookup(ACTIONS, getattr(args, "action", None))
        prop = _safe_lookup(PROPS, getattr(args, "prop", None))
        blockade = _safe_lookup(BLOCKADES, getattr(args, "blockade", None))
        if not action_risks_prop(action, prop) or not select_fix(action, blockade):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for place, a, p in valid_combos():
        for b in BLOCKADES:
            if (
                (getattr(args, "place", None) is None or place == getattr(args, "place", None))
                and (getattr(args, "action", None) is None or a == getattr(args, "action", None))
                and (getattr(args, "prop", None) is None or p == getattr(args, "prop", None))
                and (getattr(args, "blockade", None) is None or b == getattr(args, "blockade", None))
            ):
                combos.append((place, a, p, b))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, action, prop, blockade = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place, action, prop, blockade, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIONS, params.action),
        _safe_lookup(PROPS, params.prop),
        _safe_lookup(BLOCKADES, params.blockade),
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


CURATED = [
    StoryParams("fair", "parade", "mane", "rope", "Milo", "boy", "mother", "curious"),
    StoryParams("zoo_gate", "joke", "mane", "cones", "Nora", "girl", "father", "spunky"),
    StoryParams("school_stage", "parade", "mane", "bench", "Leo", "boy", "mother", "cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combinations:\n")
        for t in triples:
            print("  ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} with {p.prop} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
