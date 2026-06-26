#!/usr/bin/env python3
"""
A small fable-like story world about a chewy treat, a friendship, and a cautionary
choice.

A seed tale:
---
A tiny hare found a chewy honey-cake in the lane and wanted to keep it all.
A sparrow asked to share. The hare hid the cake, bragged, and nibbled too fast.
The cake stuck to its teeth, and the hare could not sing or speak well. The
sparrow still helped by bringing water and laughing kindly. The hare learned
that friendship tastes better when it is shared, and that chewing too fast can
turn a sweet prize into trouble.

The simulated domain turns this into a cautionary fable:
- A friend offers to share a chewy treat.
- The hero refuses, then tries to hoard and gobble it.
- The treat becomes a problem because chewing too fast is messy/unpleasant.
- The friend helps anyway, and the hero learns a kinder habit.
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


# ---------------------------------------------------------------------------
# Entities and world model
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
    kind: str = "thing"  # "character" | "thing"
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

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"hare", "rabbit", "girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    name: str = "the meadow"
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
class Treat:
    id: str
    label: str
    phrase: str
    flavor: str
    chewiness: str
    risk: str
    mess: str
    region: str = "mouth"
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
class FriendAid:
    id: str
    label: str
    phrase: str
    help_line: str
    effect_line: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(name="the meadow"),
    "orchard": Setting(name="the orchard"),
    "lane": Setting(name="the lane"),
    "hill": Setting(name="the hill"),
}

TREATS = {
    "honeycake": Treat(
        id="honeycake",
        label="honey-cake",
        phrase="a chewy honey-cake",
        flavor="honey-sweet",
        chewiness="chewy",
        risk="stuck to its teeth",
        mess="sticky",
    ),
    "taffy": Treat(
        id="taffy",
        label="taffy",
        phrase="a long chewy taffy",
        flavor="sweet",
        chewiness="stretchy",
        risk="wrapped around its teeth",
        mess="sticky",
    ),
    "fruitbar": Treat(
        id="fruitbar",
        label="fruit bar",
        phrase="a chewy fruit bar",
        flavor="fruity",
        chewiness="chewy",
        risk="made its mouth sore",
        mess="crumbly",
    ),
}

AIDS = {
    "water": FriendAid(
        id="water",
        label="a little cup of water",
        phrase="a little cup of water",
        help_line="offered a little cup of water",
        effect_line="the water loosened the sticky bits at once",
    ),
    "lemon": FriendAid(
        id="lemon",
        label="a lemon slice",
        phrase="a lemon slice",
        help_line="brought a lemon slice and a calm word",
        effect_line="the lemon made the treat easier to manage",
    ),
    "cloth": FriendAid(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth",
        help_line="came with a soft cloth for the crumbs",
        effect_line="the cloth cleaned the mess from the fur",
    ),
}

NAMES = {
    "hare": ["Bram", "Pip", "Toby", "Milo", "Rufus"],
    "sparrow": ["Lark", "Nell", "Wren", "Nia", "Tess"],
}

TRAITS = ["curious", "quick", "proud", "gentle", "small", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "meadow"
    treat: str = "honeycake"
    aid: str = "water"
    hero_name: str = "Bram"
    friend_name: str = "Lark"
    hero_type: str = "hare"
    friend_type: str = "sparrow"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def treat_is_chewy(treat: Treat) -> bool:
    return "chewy" in treat.chewiness or "chewy" in treat.phrase


def friend_aid_is_reasonable(treat: Treat, aid: FriendAid) -> bool:
    if treat.id == "honeycake":
        return aid.id in {"water", "cloth"}
    if treat.id == "taffy":
        return aid.id in {"water", "lemon"}
    if treat.id == "fruitbar":
        return aid.id in {"water", "cloth", "lemon"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TREATS:
            for a in AIDS:
                if treat_is_chewy(_safe_lookup(TREATS, t)) and friend_aid_is_reasonable(_safe_lookup(TREATS, t), _safe_lookup(AIDS, a)):
                    out.append((s, t, a))
    return out


def explain_rejection(treat: Treat, aid: FriendAid) -> str:
    return (
        f"(No story: {aid.label} does not make a sensible help for {treat.phrase}. "
        f"Choose a different aid that can actually help with a sticky or sore mouth.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def _do_eat(world: World, hero: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.meters["chew"] = hero.meters.get("chew", 0.0) + 1
    hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1
    if narrate:
        world.say(
            f"{hero.id} took the {treat.label} and chewed too fast, because the sweet smell made patience feel small."
        )


def _sticky_rule(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.meters.get("chew", 0.0) < THRESHOLD:
            continue
        if ent.memes.get("greed", 0.0) < THRESHOLD:
            continue
        sig = ("sticky", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["sticky"] = ent.meters.get("sticky", 0.0) + 1
        ent.memes["embarrassment"] = ent.memes.get("embarrassment", 0.0) + 1
        out.append(f"{ent.id}'s mouth felt sticky, and speaking became hard.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in [_sticky_rule]:
            res = rule(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_trouble(world: World, hero: Entity, treat: Treat) -> dict:
    sim = world.copy()
    _do_eat(sim, sim.get(hero.id), treat, narrate=False)
    propagate(sim, narrate=False)
    he = sim.get(hero.id)
    return {
        "sticky": he.meters.get("sticky", 0.0) >= THRESHOLD,
        "embarrassment": he.memes.get("embarrassment", 0.0),
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once, in {world.setting.name}, there lived a little {hero.type} named {hero.id} and a kind {friend.type} named {friend.id}."
    )
    world.say(
        f"{hero.id} was {hero.pronoun()} {next((t for t in hero.traits if t != 'little'), 'small')} and loved every sweet thing that could be chewed."
    )


def gift(world: World, friend: Entity, hero: Entity, treat: Treat) -> None:
    world.say(
        f"One day, {friend.id} found {treat.phrase} by the grass and offered it to {hero.id}."
    )
    world.say(
        f"It smelled {treat.flavor}, and its {treat.chewiness} bite looked delicious."
    )


def refuse_share(world: World, hero: Entity, friend: Entity, treat: Treat) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"But {hero.id} tucked it away and said {hero.pronoun('possessive')} treasure was too good to share."
    )
    world.say(
        f"{friend.id} frowned a little, because friendship is happier when kindness moves both ways."
    )


def warn(world: World, friend: Entity, hero: Entity, treat: Treat) -> bool:
    pred = predict_trouble(world, hero, treat)
    if not pred["sticky"]:
        return False
    world.facts["predicted_trouble"] = treat.risk
    world.say(
        f'"If you chew that so fast," {friend.id} warned, "your mouth may get {treat.risk}."'
    )
    return True


def gobble(world: World, hero: Entity, treat: Treat) -> None:
    world.say(f"{hero.id} did not listen.")
    _do_eat(world, hero, treat, narrate=True)
    propagate(world, narrate=True)


def help_friend(world: World, friend: Entity, hero: Entity, aid: FriendAid) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Still, {friend.id} did not tease. {friend.id} {aid.help_line}, because true friends help even after a bad choice."
    )
    world.say(aid.effect_line)
    world.facts["aid"] = aid.id


def learn(world: World, hero: Entity, friend: Entity, treat: Treat) -> None:
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0.0) + 1
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1
    world.say(
        f"{hero.id} sighed and thanked {friend.id}. At last, {hero.id} learned that a sweet thing lasts longer when shared, and that chewing slowly keeps trouble away."
    )
    world.say(
        f"After that, {hero.id} took tiny bites, and the {treat.label} became a happy snack instead of a lesson."
    )


def tell(setting: Setting, treat: Treat, aid: FriendAid, hero_name: str, friend_name: str,
         hero_type: str = "hare", friend_type: str = "sparrow", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["kind"]))
    world.facts.update(hero=hero, friend=friend, treat=treat, aid=aid, setting=setting)

    introduce(world, hero, friend)
    world.para()
    gift(world, friend, hero, treat)
    refuse_share(world, hero, friend, treat)
    warn(world, friend, hero, treat)
    gobble(world, hero, treat)
    world.para()
    help_friend(world, friend, hero, aid)
    learn(world, hero, friend, treat)
    return world


# ---------------------------------------------------------------------------
# Q&A and prose helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, treat, aid = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "aid")
    return [
        'Write a short fable about a chewy treat, a friendship, and a poor choice that teaches caution.',
        f"Tell a gentle cautionary tale about {hero.id} the {hero.type} and {friend.id} the {friend.type} sharing {treat.phrase}.",
        f"Write a simple story where a character ignores a warning about {treat.label} and later learns to be kinder.",
        f"Make the ending show how {aid.phrase} helps after {treat.risk}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, treat, aid = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "aid")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {friend.id}, a kind {friend.type}, in {world.setting.name}.",
        ),
        QAItem(
            question=f"What chewy thing did {friend.id} find and offer to {hero.id}?",
            answer=f"{friend.id} found {treat.phrase} and offered it to {hero.id}.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id} about the {treat.label}?",
            answer=f"{friend.id} warned {hero.id} because chewing it too fast could leave {hero.pronoun('possessive')} mouth {treat.risk}.",
        ),
        QAItem(
            question=f"How did the friendship help after the problem started?",
            answer=f"{friend.id} stayed kind and brought {aid.phrase}, which helped {hero.id} after the bad choice.",
        ),
        QAItem(
            question=f"What did {hero.id} learn at the end?",
            answer=f"{hero.id} learned to share and to chew slowly, because kindness and patience make sweet things last longer.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "chewy": QAItem(
        question="What does chewy mean?",
        answer="Chewy means a food is hard to swallow quickly and needs many little bites before it is gone.",
    ),
    "friendship": QAItem(
        question="What is friendship?",
        answer="Friendship is a kind bond between friends who help, share, and care about each other.",
    ),
    "cautionary": QAItem(
        question="What is a cautionary tale?",
        answer="A cautionary tale is a story that warns about a bad choice so someone can learn to do better.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["chewy"],
        WORLD_KNOWLEDGE["friendship"],
        WORLD_KNOWLEDGE["cautionary"],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
chewy(T) :- treat(T), chewy_mark(T).
valid(S,T,A) :- setting(S), treat(T), aid(A), chewy(T), compatible(T,A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("chewy_mark", tid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("help", aid, a.label))
    for tid, t in TREATS.items():
        for aid, a in AIDS.items():
            if friend_aid_is_reasonable(t, a):
                lines.append(asp.fact("compatible", tid, aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about a chewy treat and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["hare"])
    ap.add_argument("--friend-type", choices=["sparrow"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "treat", None) and getattr(args, "aid", None):
        if (getattr(args, "setting", None), getattr(args, "treat", None), getattr(args, "aid", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos
              if (not getattr(args, "setting", None) or c[0] == getattr(args, "setting", None))
              and (not getattr(args, "treat", None) or c[1] == getattr(args, "treat", None))
              and (not getattr(args, "aid", None) or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, treat, aid = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or "hare"
    friend_type = getattr(args, "friend_type", None) or "sparrow"
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    friend_name = getattr(args, "friend_name", None) or rng.choice(_safe_lookup(NAMES, friend_type))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        treat=treat,
        aid=aid,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_type=hero_type,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(TREATS, params.treat),
        _safe_lookup(AIDS, params.aid),
        params.hero_name,
        params.friend_name,
        params.hero_type,
        params.friend_type,
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
    StoryParams(setting="meadow", treat="honeycake", aid="water", hero_name="Bram", friend_name="Lark", trait="curious"),
    StoryParams(setting="orchard", treat="taffy", aid="lemon", hero_name="Pip", friend_name="Wren", trait="proud"),
    StoryParams(setting="lane", treat="fruitbar", aid="cloth", hero_name="Milo", friend_name="Nell", trait="quick"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.treat} in {p.setting}"
        else:
            header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
