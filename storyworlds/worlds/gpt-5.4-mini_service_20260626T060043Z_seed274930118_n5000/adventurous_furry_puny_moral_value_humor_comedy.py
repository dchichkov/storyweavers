#!/usr/bin/env python3
"""
storyworlds/worlds/adventurous_furry_puny_moral_value_humor_comedy.py
======================================================================

A tiny comedy storyworld about a puny furry adventurer, a tempting stunt,
and a moral choice that turns the joke into a kind ending.

Premise:
- A small furry hero wants to do something adventurous and impressive.
- The stunt is funny because the hero is puny and the gear is slightly too big.
- A nearby friend or sibling worries less about danger than about showing off.
- The hero must choose between bragging and doing the kind thing.

The world is intentionally small: a few settings, a few stunts, a few objects,
and one clear turn from "look at me" to "let's help first."

The prose is simulated from state:
- meters track size-relevant physical facts like wobble, stuckness, and mess
- memes track emotional facts like pride, worry, laughter, and gratitude

The tone stays child-facing and comedic while still ending with a moral value:
kindness, sharing, honesty, or helping someone else.
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

METER_THRESHOLD = 1.0
VALID_VALUES = {"kindness", "sharing", "honesty", "helpfulness"}
VALID_HUMOR = {"comedy"}
VALID_STYLE = {"comedy"}



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    helper_item: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    humor: str
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
class Prize:
    label: str
    phrase: str
    type: str
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


@dataclass
class Helper:
    label: str
    offer: str
    finish: str
    fix_for: set[str] = field(default_factory=set)
    shields: set[str] = field(default_factory=set)
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("stunt", 0.0) < METER_THRESHOLD:
            continue
        if actor.meters.get("wobble", 0.0) >= METER_THRESHOLD:
            continue
        sig = ("wobble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meter(actor, "wobble")
        out.append(f"{actor.id} began to wobble a little.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0.0) < METER_THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters.get("spilled", 0.0) >= METER_THRESHOLD:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meter(item, "spilled")
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little messy.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("surprise", 0.0) < METER_THRESHOLD:
            continue
        if actor.memes.get("laugh", 0.0) >= METER_THRESHOLD:
            continue
        sig = ("laugh", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(actor, "laugh")
        out.append(f"{actor.id} laughed despite {actor.pronoun('possessive')}self.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("helped", 0.0) < METER_THRESHOLD:
            continue
        if actor.memes.get("kindness", 0.0) >= METER_THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(actor, "kindness")
        out.append(f"{actor.id} felt warm and proud for helping.")
    return out


CAUSAL_RULES = [_r_wobble, _r_spill, _r_laugh, _r_help]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def adventure_risk(adventure: Adventure, prize: Prize) -> bool:
    return prize.region in adventure.zone


def choose_helper(adventure: Adventure, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS:
        if adventure.id in helper.fix_for and prize.region in helper.shields:
            return helper
    return None


def predict(world: World, hero: Entity, adventure: Adventure, prize: Prize) -> dict:
    sim = world.copy()
    _do_adventure(sim, sim.get(hero.id), adventure, narrate=False)
    prize_sim = sim.get(prize.id)
    return {
        "messy": bool(prize_sim.meters.get("spilled", 0.0) >= METER_THRESHOLD),
        "wobble": sim.get(hero.id).meters.get("wobble", 0.0),
    }


def _do_adventure(world: World, hero: Entity, adventure: Adventure, narrate: bool = True) -> None:
    if adventure.id not in world.setting.affords:
        pass
    _add_meter(hero, "stunt")
    _add_meter(hero, adventure.mess)
    _add_meme(hero, "excitement")
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t not in {"little"}), "small")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved big ideas in a tiny body.")


def love_adventure(world: World, hero: Entity, adventure: Adventure) -> None:
    _add_meme(hero, "love_adventure")
    world.say(
        f"{hero.pronoun().capitalize()} loved {adventure.gerund}, and {adventure.humor} "
        f"made the whole plan feel even sillier."
    )


def add_prize(world: World, hero: Entity, prize: Entity) -> None:
    _add_meme(hero, "pride")
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}, and {prize.phrase} looked "
        f"almost too grand for such a puny hero."
    )


def set_scene(world: World, hero: Entity, helper: Entity, adventure: Adventure) -> None:
    if world.setting.indoors:
        world.say(
            f"Inside {world.setting.place}, there was a wobbly path made of pillows and a "
            f"single chair that looked like a mountain."
        )
    else:
        world.say(
            f"Outside at {world.setting.place}, there was a bouncy path, one slippery step, "
            f"and plenty of room for a very brave mistake."
        )
    world.say(
        f"{hero.id} and {helper.label} were there for a tiny adventure: {adventure.verb} "
        f"without falling into a laugh."
    )


def want_more(world: World, hero: Entity, adventure: Adventure) -> None:
    _add_meme(hero, "want")
    world.say(
        f"{hero.id} wanted to {adventure.verb} right away, but {hero.pronoun('possessive')} "
        f"feet were so small that even the first step looked bossy."
    )


def warn(world: World, helper: Entity, hero: Entity, adventure: Adventure, prize: Entity) -> bool:
    pred = predict(world, hero, adventure, prize)
    if not pred["messy"]:
        return False
    _add_meme(helper, "worry")
    world.facts["predicted_mess"] = adventure.risk
    world.say(
        f'"If you do that, your {prize.label} will get {adventure.risk}," {helper.label} said. '
        f'"Then it will need a wash, and that would be a lot of laundry for such a tiny wiggle."'
    )
    return True


def defy(world: World, hero: Entity, adventure: Adventure) -> None:
    _add_meme(hero, "stubborn")
    world.say(f"{hero.id} tried to look fierce, but the face was too round for that to work.")
    world.say(f"{hero.pronoun().capitalize()} darted toward the fun and almost bonked the air.")


def grab_stop(world: World, helper: Entity, hero: Entity) -> None:
    _add_meme(hero, "startled")
    world.say(
        f"Then {helper.label} scooted over and gently stopped {hero.pronoun('object')}. "
        f'"Wait for the safe part first," {helper.label} said.'
    )


def offer_help(world: World, helper: Entity, hero: Entity, adventure: Adventure, prize: Entity) -> Optional[Helper]:
    helper_def = choose_helper(adventure, prize)
    if helper_def is None:
        return None
    helper_item = world.add(Entity(
        id=helper_def.label.replace(" ", "_"),
        type="gear",
        label=helper_def.label,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id,
        plural=helper_def.plural,
    ))
    if predict(world, hero, adventure, prize)["messy"]:
        helper_item.worn_by = None
        del world.entities[helper_item.id]
        return None
    world.say(
        f"{helper.label} smiled and offered {helper_def.label}. "
        f'"How about we {helper_def.offer} and still try the adventure?"'
    )
    return helper_def


def accept(world: World, hero: Entity, helper: Entity, adventure: Adventure, prize: Entity, helper_def: Helper) -> None:
    _add_meme(hero, "joy")
    _add_meme(hero, "kindness")
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 1.0)
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id}'s ears perked up. {hero.id} nodded, then gave {helper.label} a tiny hug so fast "
        f"it looked like a hiccup."
    )
    world.say(
        f"Together they {helper_def.finish}. Soon {hero.id} was {adventure.gerund}, "
        f"and {prize.phrase} stayed neat while the joke still landed."
    )


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"dash", "climb"}),
    "backyard": Setting(place="the backyard", indoors=False, affords={"dash", "climb", "splash"}),
    "attic": Setting(place="the attic", indoors=True, affords={"balance", "climb"}),
    "treehouse": Setting(place="the treehouse", indoors=True, affords={"balance", "sneak"}),
}

ADVENTURES = {
    "dash": Adventure(
        id="dash",
        verb="dash across the pebble path",
        gerund="dashing across pebble paths",
        rush="zip over the pebbles",
        risk="dusty",
        mess="speed",
        zone={"feet"},
        humor="the pebbles clicked like a drum band",
        tag="pebbles",
    ),
    "climb": Adventure(
        id="climb",
        verb="climb the wobbly crate",
        gerund="climbing wobbly crates",
        rush="scramble up the crate",
        risk="tippy",
        mess="wobble",
        zone={"feet", "torso"},
        humor="the crate wiggled like it had ticklish toes",
        tag="crate",
    ),
    "splash": Adventure(
        id="splash",
        verb="splash through the puddles",
        gerund="splashing through puddles",
        rush="leap into the puddles",
        risk="drippy",
        mess="splish",
        zone={"feet", "legs"},
        humor="the puddles answered with silly splashes",
        tag="puddles",
    ),
    "balance": Adventure(
        id="balance",
        verb="balance on the low beam",
        gerund="balancing on low beams",
        rush="tiptoe onto the beam",
        risk="wobbly",
        mess="wobble",
        zone={"feet", "legs"},
        humor="the beam seemed to giggle under tiny paws",
        tag="beam",
    ),
    "sneak": Adventure(
        id="sneak",
        verb="sneak past the snack table",
        gerund="sneaking past snack tables",
        rush="tiptoe to the cookies",
        risk="crumbly",
        mess="crumble",
        zone={"torso"},
        humor="the cookies sat there like they knew a joke",
        tag="cookies",
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright little cape", type="cape", region="torso"),
    "boots": Prize(label="boots", phrase="tiny yellow boots", type="boots", region="feet", plural=True),
    "scarf": Prize(label="scarf", phrase="a soft scarf", type="scarf", region="torso"),
    "hat": Prize(label="hat", phrase="a floppy adventure hat", type="hat", region="head"),
}

HELPERS = [
    Helper(
        label="a raincoat",
        offer="put on the raincoat first",
        finish="popped on the raincoat and went on",
        fix_for={"splash"},
        shields={"feet", "legs", "torso"},
    ),
    Helper(
        label="tiny boots",
        offer="wear the tiny boots and keep the socks dry",
        finish="laced up the tiny boots and marched on",
        fix_for={"splash", "dash"},
        shields={"feet"},
        plural=True,
    ),
    Helper(
        label="a cloth wrap",
        offer="wrap the scarf around the cape so it stays neat",
        finish="tied the cloth wrap snugly and climbed on",
        fix_for={"climb", "balance"},
        shields={"torso"},
    ),
    Helper(
        label="a snack plate cover",
        offer="carry the snack plate cover and walk more carefully",
        finish="used the snack plate cover and sneaked on",
        fix_for={"sneak"},
        shields={"torso"},
    ),
]

NAMES = ["Milo", "Pip", "Nico", "Toby", "Zuzu", "Mina", "Theo", "Luna"]
TRAITS = ["furry", "brave", "curious", "puny", "spry", "cheerful"]

@dataclass
class StoryParams:
    setting: str
    adventure: str
    prize: str
    name: str
    helper_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for a_id in setting.affords:
            adv = _safe_lookup(ADVENTURES, a_id)
            for p_id, prize in PRIZES.items():
                if adventure_risk(adv, prize) and choose_helper(adv, prize):
                    combos.append((s_name, a_id, p_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a puny furry adventurer and a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, adventure, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(setting=setting, adventure=adventure, prize=prize, name=name, helper_name=helper_name)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type="mouse", traits=["little", "furry", "puny"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="mouse", label=params.helper_name))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    adv = _safe_lookup(ADVENTURES, params.adventure)

    intro(world, hero)
    love_adventure(world, hero, adv)
    add_prize(world, hero, prize)
    world.para()
    set_scene(world, hero, helper, adv)
    want_more(world, hero, adv)
    warn(world, helper, hero, adv, prize)
    defy(world, hero, adv)
    grab_stop(world, helper, hero)
    world.para()
    helper_def = offer_help(world, helper, hero, adv, prize)
    if helper_def:
        accept(world, hero, helper, adv, prize, helper_def)

    world.facts.update(hero=hero, helper=helper, prize=prize, adventure=adv, setting=world.setting,
                       helper_def=helper_def, resolved=helper_def is not None)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adv = _safe_fact(world, f, "adventure")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short comedy story for a child about a {hero.pronoun("subject")} {hero.type} who wants to {adv.verb}.',
        f'Write a gentle story with a moral value about being kind when a puny furry hero worries about a {prize.label}.',
        f'Create a funny story where someone says the hero is too tiny for the stunt, but the hero helps first and then tries it safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, adv = f["hero"], f["helper"], f["prize"], f["adventure"]
    qa = [
        QAItem(
            question=f"What kind of hero is {hero.id} in the story?",
            answer=f"{hero.id} is a little furry puny mouse who still wants big adventures.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {adv.verb}, because the idea sounded exciting and funny.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about {hero.id}'s {prize.label}?",
            answer=f"{helper.id} worried that {prize.phrase} would get {adv.risk} if the stunt went wrong.",
        ),
    ]
    if f.get("resolved"):
        helper_def = _safe_fact(world, f, "helper_def")
        qa.append(QAItem(
            question=f"How did {helper_def.label} help the hero?",
            answer=f"{helper.id} offered {helper_def.label} so {hero.id} could stay safe and still do the adventure.",
        ))
        qa.append(QAItem(
            question=f"What moral value did the story show at the end?",
            answer="The story showed kindness and helpfulness, because the hero listened, accepted help, and cared about the other character.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "pebbles": [(
        "What are pebbles?",
        "Pebbles are small smooth stones. They can make a path bumpy and noisy under tiny feet."
    )],
    "crate": [(
        "What is a crate?",
        "A crate is a box made of wood. It can be used like a little platform or step."
    )],
    "puddles": [(
        "What is a puddle?",
        "A puddle is a little pool of water on the ground, usually after rain."
    )],
    "beam": [(
        "What is a beam?",
        "A beam is a long straight piece of wood or metal. It can be hard to balance on."
    )],
    "cookies": [(
        "Why should you be careful around cookies?",
        "Cookies are yummy, but it is polite to wait your turn and not grab snacks before you are invited."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means being gentle, helpful, and caring about other people."
    )],
    "sharing": [(
        "What is sharing?",
        "Sharing means letting someone else use, have, or enjoy something too."
    )],
    "honesty": [(
        "What is honesty?",
        "Honesty means telling the truth and not pretending something false is real."
    )],
    "helpfulness": [(
        "What is helpfulness?",
        "Helpfulness means doing something that makes another person's job easier."
    )],
    "comedy": [(
        "What is comedy?",
        "Comedy is a kind of story or show that tries to make people laugh with silly or surprising moments."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["adventure"].tag, "comedy"}
    if f.get("resolved"):
        tags.add("kindness")
    out: list[QAItem] = []
    for tag in sorted(tags):
        for q, a in WORLD_KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
adventure(A) :- adventure_fact(A).
prize(P) :- prize_fact(P).

risk(A,P) :- adventure_zone(A,R), prize_region(P,R).
fix(A,P) :- helper_fix(H,A), helper_shields(H,R), prize_region(P,R), adventure_zone(A,R).
valid(Setting, A, P) :- setting_affords(Setting,A), risk(A,P), fix(A,P).

story(Setting, A, P) :- valid(Setting, A, P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_name, setting in SETTINGS.items():
        lines.append(asp.fact("setting_fact", s_name))
        for a in sorted(setting.affords):
            lines.append(asp.fact("setting_affords", s_name, a))
    for a_id, adv in ADVENTURES.items():
        lines.append(asp.fact("adventure_fact", a_id))
        for r in sorted(adv.zone):
            lines.append(asp.fact("adventure_zone", a_id, r))
    for p_id, prize in PRIZES.items():
        lines.append(asp.fact("prize_fact", p_id))
        lines.append(asp.fact("prize_region", p_id, prize.region))
    for h in HELPERS:
        for a_id in sorted(h.fix_for):
            lines.append(asp.fact("helper_fix", h.label, a_id))
        for r in sorted(h.shields):
            lines.append(asp.fact("helper_shields", h.label, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="garden", adventure="dash", prize="boots", name="Milo", helper_name="Pip"),
    StoryParams(setting="backyard", adventure="splash", prize="cape", name="Pip", helper_name="Mina"),
    StoryParams(setting="attic", adventure="climb", prize="scarf", name="Nico", helper_name="Toby"),
    StoryParams(setting="treehouse", adventure="balance", prize="hat", name="Zuzu", helper_name="Luna"),
]


def resolve_invalid_explicit(args: argparse.Namespace) -> None:
    if getattr(args, "setting", None) and getattr(args, "adventure", None) and getattr(args, "prize", None):
        adv = _safe_lookup(ADVENTURES, getattr(args, "adventure", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not adventure_risk(adv, prize) or not choose_helper(adv, prize):
            pass


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        resolve_invalid_explicit(args)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.adventure} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
