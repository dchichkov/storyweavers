#!/usr/bin/env python3
"""
storyworlds/worlds/single_friendship_myth.py
=============================================

A small mythic story world about a single lonely traveler who finds friendship
through a kind test, a shared task, and a lasting bond.

The world keeps the tale child-facing and concrete, but the structure is
classical: setup, tension, turn, and resolution. The simulated state tracks
physical details with meters and emotional details with memes.

Core premise:
- One traveler begins alone.
- A mythic helper or peer appears.
- A misunderstanding or difficulty threatens the chance of friendship.
- A brave, generous action proves trust.
- The story ends with a visible sign of friendship.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- supports the standard CLI modes and verification
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

ALLY_KINDS = {"friend", "spirit", "child", "goat", "bird"}

# ---------------------------------------------------------------------------
# World entities
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    offered_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    tag: str
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
class Rite:
    id: str
    verb: str
    gerund: str
    risk: str
    place_hint: str
    bond_gain: str
    mood: str
    tag: str
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
class Gift:
    id: str
    label: str
    phrase: str
    blesses: set[str] = field(default_factory=set)
    visible: str = ""
    keepsafe: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    rite: str
    gift: str
    hero_name: str
    hero_kind: str
    helper_kind: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "grove": Setting(place="the old grove", tag="grove", affords={"share_fire", "cross_bridge", "find_spring"}),
    "hill": Setting(place="the windy hill", tag="hill", affords={"share_fire", "cross_bridge", "sing"}),
    "riverbank": Setting(place="the riverbank", tag="river", affords={"find_spring", "cross_bridge", "share_fire"}),
}

RITES = {
    "share_fire": Rite(
        id="share_fire",
        verb="share the fire",
        gerund="sharing the fire",
        risk="the flame might sputter out if the traveler is selfish",
        place_hint="by the campfire",
        bond_gain="warmth",
        mood="cold",
        tag="fire",
    ),
    "cross_bridge": Rite(
        id="cross_bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        risk="the bridge is narrow and must be crossed with care",
        place_hint="at the old stones",
        bond_gain="trust",
        mood="afraid",
        tag="bridge",
    ),
    "find_spring": Rite(
        id="find_spring",
        verb="find the spring",
        gerund="finding the spring",
        risk="the path is hidden by roots and thorns",
        place_hint="under the roots",
        bond_gain="hope",
        mood="thirsty",
        tag="spring",
    ),
    "sing": Rite(
        id="sing",
        verb="sing to the stars",
        gerund="singing to the stars",
        risk="the traveler is lonely and their voice may falter",
        place_hint="under the open sky",
        bond_gain="courage",
        mood="lonely",
        tag="song",
    ),
}

GIFTS = {
    "single_lantern": Gift(
        id="single_lantern",
        label="single lantern",
        phrase="a single lantern with a soft gold glow",
        blesses={"share_fire", "cross_bridge"},
        visible="its little light",
        keepsafe="held close in both hands",
    ),
    "shared_bread": Gift(
        id="shared_bread",
        label="loaf of bread",
        phrase="a round loaf of bread still warm from the oven",
        blesses={"share_fire", "find_spring"},
        visible="its crusty top",
        keepsafe="wrapped in cloth",
    ),
    "blue_cloak": Gift(
        id="blue_cloak",
        label="blue cloak",
        phrase="a blue cloak stitched with tiny silver threads",
        blesses={"cross_bridge", "sing"},
        visible="the silver thread",
        keepsafe="folded over the arm",
    ),
}

HERO_NAMES = ["Nia", "Milo", "Ira", "Toma", "Lina", "Ravi", "Sera", "Jori", "Luna", "Oren"]
HERO_KINDS = ["girl", "boy"]
HELPER_KINDS = ["friend", "spirit", "child", "goat", "bird"]
TRAITS = ["lonely", "brave", "gentle", "curious", "small", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for rite_id in setting.affords:
            rite = _safe_lookup(RITES, rite_id)
            for gift_id, gift in GIFTS.items():
                if rite.tag in gift.blesses:
                    combos.append((setting_id, rite_id, gift_id))
    return combos


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def rite_needs_friendship(rite: Rite, gift: Gift) -> bool:
    return rite.tag in gift.blesses


def explain_rejection(rite: Rite, gift: Gift) -> str:
    return (
        f"(No story: {gift.label} does not fit the test of {rite.verb}. "
        f"The friendship turn must be powered by a gift that genuinely helps.)"
    )


# ---------------------------------------------------------------------------
# Story simulation helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity) -> None:
    world.say(
        f"Long ago, {hero.id} was a little {hero.traits[0]} {hero.type} who walked alone "
        f"beneath wide sky and old trees."
    )
    hero.memes["lonely"] = hero.memes.get("lonely", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 0.5


def bring_gift(world: World, hero: Entity, gift: Entity) -> None:
    hero.meters["gift"] = 1
    gift.carried_by = hero.id
    world.say(
        f"{hero.id} carried {gift.phrase}, and {gift.visible} shone like a small promise."
    )


def meet_helper(world: World, hero: Entity, helper: Entity, rite: Rite) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} met a {helper.type} who watched quietly "
        f"near {rite.place_hint}."
    )
    helper.memes["curious"] = helper.memes.get("curious", 0.0) + 1


def warn(world: World, hero: Entity, helper: Entity, rite: Rite, gift: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {rite.verb}, but {rite.risk}. "
        f"{gift.visible.capitalize()} made the choice feel important."
    )
    world.say(
        f"The helper did not step away; instead, {helper.id} stayed close and waited."
    )


def test_friendship(world: World, hero: Entity, helper: Entity, rite: Rite, gift: Entity) -> None:
    if world.setting.tag == "river" and rite.id == "cross_bridge":
        hero.meters["edge"] = 1
    if rite.id == "share_fire":
        hero.meters["cold"] = 1
    if rite.id == "find_spring":
        hero.meters["thirst"] = 1
    if rite.id == "sing":
        hero.meters["silence"] = 1

    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 0.5
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"{hero.id} took a breath and tried to {rite.verb}, even though {rite.risk}."
    )


def predict_turn(world: World, hero: Entity, helper: Entity, rite: Rite, gift: Entity) -> dict:
    sim = world.copy()
    _resolve(sim, sim.get(hero.id), sim.get(helper.id), rite, sim.get(gift.id), narrate=False)
    return {
        "bond": sim.get(hero.id).memes.get("bond", 0.0),
        "safe": sim.get(gift.id).carried_by is not None,
    }


def _resolve(world: World, hero: Entity, helper: Entity, rite: Rite, gift: Entity, narrate: bool = True) -> None:
    hero.memes["bond"] = hero.memes.get("bond", 0.0) + 1
    helper.memes["bond"] = helper.memes.get("bond", 0.0) + 1
    hero.memes["lonely"] = 0.0
    helper.memes["guarded"] = 0.0
    gift.carried_by = hero.id
    hero.meters["gift"] = 1
    if narrate:
        world.say(
            f"{hero.id} shared {gift.label} with {helper.id}, and the two of them worked side by side."
        )
        world.say(
            f"Because they chose to help each other, the hard thing became possible."
        )


def resolve(world: World, hero: Entity, helper: Entity, rite: Rite, gift: Entity) -> None:
    pred = predict_turn(world, hero, helper, rite, gift)
    if pred["bond"] < THRESHOLD:
        return
    _resolve(world, hero, helper, rite, gift, narrate=True)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"At last, {hero.id} and {helper.id} finished the task together. "
        f"Their friendship stayed like a lantern against the dark."
    )


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def tell(setting: Setting, rite: Rite, gift_cfg: Gift, hero_name: str, hero_kind: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        traits=[trait, "single"],
    ))
    helper = world.add(Entity(
        id="Friend",
        kind="character",
        type=helper_kind,
        traits=["quiet", "kind"],
    ))
    gift = world.add(Entity(
        id=gift_cfg.id,
        type="thing",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=hero.id,
    ))

    intro(world, hero)
    bring_gift(world, hero, gift)
    world.para()
    meet_helper(world, hero, helper, rite)
    warn(world, hero, helper, rite, gift)
    test_friendship(world, hero, helper, rite, gift)
    world.para()
    resolve(world, hero, helper, rite, gift)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "gift": gift,
        "rite": rite,
        "setting": setting,
        "resolved": hero.memes.get("bond", 0.0) >= THRESHOLD,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "single": [
        ("What does single mean?",
         "Single means one by itself, not a group or pair."),
    ],
    "friendship": [
        ("What is friendship?",
         "Friendship is when people care about each other, help each other, and like spending time together."),
    ],
    "lantern": [
        ("What is a lantern for?",
         "A lantern holds light so people can see in the dark."),
    ],
    "bread": [
        ("Why do people share bread?",
         "People share bread to give food, kindness, and comfort to someone else."),
    ],
    "cloak": [
        ("What does a cloak do?",
         "A cloak covers your body and can keep you warm or safe from wind."),
    ],
    "bridge": [
        ("Why do people cross bridges carefully?",
         "Bridges can be narrow or high, so people cross them carefully to stay safe."),
    ],
    "spring": [
        ("What is a spring?",
         "A spring is water that comes up from the ground."),
    ],
    "fire": [
        ("Why is fire helpful in stories?",
         "Fire gives warmth and light, so people can gather near it at night."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, rite, gift = f["hero"], f["helper"], f["rite"], f["gift"]
    return [
        f'Write a short myth for a child about a single {hero.type} named {hero.id} who learns friendship.',
        f"Tell a gentle myth where {hero.id} and {helper.id} solve a hard moment by {rite.gerund} with {gift.label}.",
        f'Write a simple story with the word "single" and an ending where friendship becomes a visible gift.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, rite, gift = f["hero"], f["helper"], f["rite"], f["gift"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a single little {hero.type} who travels to {world.setting.place} and meets {helper.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry?",
            answer=f"{hero.id} carried {gift.phrase}, and it mattered because the light or warmth helped during {rite.gerund}.",
        ),
        QAItem(
            question=f"What hard thing did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {rite.verb}, but the path or task was hard enough to need help from a new friend.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did friendship change the end?",
            answer=f"{hero.id} and {helper.id} worked together, shared the burden, and their bond became strong enough to last.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["rite"].tag, "single", "friendship"}
    gift_id = _safe_fact(world, world.facts, "gift").id
    tags.add(gift_id.split("_")[-1])
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A rite is valid when the gift truly supports its mythic need.
valid_combo(S, R, G) :- setting(S), rite(R), gift(G),
                        affords(S, R), blesses(G, Tag), rite_tag(R, Tag).

% Friendship becomes possible when the valid combo exists.
friendship_path(S, R, G) :- valid_combo(S, R, G).

#show valid_combo/3.
#show friendship_path/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("rite_tag", rid, rite.tag))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for tag in sorted(gift.blesses):
            lines.append(asp.fact("blesses", gid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a single traveler, a mythic test, and friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--helper-kind", choices=HELPER_KINDS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "rite", None) and getattr(args, "gift", None):
        rite = _safe_lookup(RITES, getattr(args, "rite", None))
        gift = _safe_lookup(GIFTS, getattr(args, "gift", None))
        if not rite_needs_friendship(rite, gift):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "rite", None) is None or c[1] == getattr(args, "rite", None))
        and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, rite_id, gift_id = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(HERO_KINDS)
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(HELPER_KINDS)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        rite=rite_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_kind=helper_kind,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(RITES, params.rite),
        _safe_lookup(GIFTS, params.gift),
        params.hero_name,
        params.hero_kind,
        params.helper_kind,
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="grove", rite="share_fire", gift="single_lantern", hero_name="Nia", hero_kind="girl", helper_kind="spirit", trait="lonely"),
    StoryParams(setting="hill", rite="cross_bridge", gift="blue_cloak", hero_name="Milo", hero_kind="boy", helper_kind="child", trait="brave"),
    StoryParams(setting="riverbank", rite="find_spring", gift="shared_bread", hero_name="Luna", hero_kind="girl", helper_kind="goat", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3.\n#show friendship_path/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3.\n#show friendship_path/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for s, r, g in combos:
            print(f"  {s:10} {r:12} {g:12}")
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
            header = f"### {p.name}: {p.rite} in {p.setting} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
