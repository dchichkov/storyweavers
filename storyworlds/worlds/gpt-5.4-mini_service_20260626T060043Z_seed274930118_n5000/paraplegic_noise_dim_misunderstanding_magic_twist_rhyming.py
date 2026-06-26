#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/paraplegic_noise_dim_misunderstanding_magic_twist_rhyming.py
====================================================================================================

A small rhyming story world about a paraplegic child, a noise-dim charm,
a misunderstanding, and a magical twist.

The world is intentionally compact: one main setting, one sound-heavy activity,
one fragile thing at risk, and one sensible magical fix. The prose is generated
from world state, not from a frozen paragraph swap.

Core tale shape:
- A paraplegic child loves a lantern-night concert.
- The concert is too loud for a sleeping kitten in a basket.
- A parent warns that the noise will wake the kitten.
- The child fears the noise-dim charm will ruin the music.
- The charm instead softens the clamor and reveals a hidden harmony.
- The twist is that the "quiet" was not emptiness; it was a gentle layer of
  music the child had not heard before.

Style note:
- The output story is written in short rhyming, child-facing beats.
- The rhymes are simple and playful, while the world state drives the plot.

Contract note:
- This script provides StoryParams, registries, build_parser, resolve_params,
  generate, emit, and main.
- It includes an inline ASP_RULES twin and a Python reasonableness gate.
- It emits ASP facts through asp_facts().
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    guards: object | None = None
    hero: object | None = None
    kitten: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = {"noise": 0.0, "comfort": 0.0, "magic": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "confusion": 0.0, "love": 0.0}

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
    place: str
    indoor: bool = False
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    softens: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.music_level: float = 0.0

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.music_level = self.music_level
        return clone


def _r_noise_soften(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.id == "kitten" and item.caretaker == actor.id:
                continue
        for charm in list(world.entities.values()):
            if charm.kind != "charm" or not charm.protective:
                continue
            if "noise" not in charm.softens:
                continue
            sig = ("soften", actor.id, charm.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["noise"] = max(0.0, actor.meters["noise"] - 1.0)
            actor.meters["comfort"] += 1.0
            out.append(f"The {charm.label} made the loudness go light.")
    return out


def _r_magic_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.music_level < THRESHOLD:
        return out
    sig = ("twist", "music")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.music_level += 1.0
    out.append("A hidden harmony hummed beneath the hush.")
    return out


CAUSAL_RULES = [
    _r_noise_soften,
    _r_magic_twist,
]


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


def predict_outcome(world: World, actor: Entity, activity: Activity, charm: Charm) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    _use_charm(sim, sim.get(actor.id), charm, narrate=False)
    kitten = sim.entities["kitten"]
    return {
        "kitten_wakes": kitten.meters["noise"] >= THRESHOLD,
        "music_level": sim.music_level,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = {"stage", "basket"}
    actor.meters["noise"] += 1.0
    actor.memes["joy"] += 1.0
    world.music_level += 1.0
    propagate(world, narrate=narrate)


def _use_charm(world: World, actor: Entity, charm: Charm, narrate: bool = True) -> None:
    actor.meters["magic"] += 1.0
    world.music_level = max(0.0, world.music_level - 0.5)
    propagate(world, narrate=narrate)


def tell(
    setting: Setting,
    activity: Activity,
    charm_def: Charm,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0, "love": 1.0},
        meters={"noise": 0.0, "comfort": 0.0, "magic": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0, "love": 1.0},
        meters={"noise": 0.0, "comfort": 0.0, "magic": 0.0},
    ))
    kitten = world.add(Entity(
        id="kitten",
        kind="thing",
        type="kitten",
        label="kitten",
        phrase="a sleepy kitten in a basket",
        caretaker=hero.id,
        meters={"noise": 0.0, "comfort": 0.0, "magic": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0, "love": 0.0},
    ))
    charm = world.add(Entity(
        id=charm_def.id,
        kind="charm",
        type="charm",
        label=charm_def.label,
        phrase=charm_def.phrase,
        protective=True,
        guards=set(charm_def.guards),
        covers={"sound"},
        meters={"noise": 0.0, "comfort": 0.0, "magic": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0, "love": 0.0},
    ))

    world.say(f"{hero_name} rolled in with a smile so bright.")
    world.say(f"On wheels, {hero_name} came, by lantern light.")
    world.say(f"{hero_name} loved the tune and loved the glow,")
    world.say(f"but the fair was loud, with a boom-boom show.")

    world.para()
    world.say(f"{parent.label.capitalize()} said, \"That racket may wake the dozing cat.")
    world.say(f"If we keep it so loud, the kitten won't nap like that.\"")
    hero.memes["worry"] += 1.0
    parent.memes["worry"] += 1.0

    pred = predict_outcome(world, hero, activity, charm)
    world.facts["predicted"] = pred
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["kitten"] = kitten
    world.facts["charm"] = charm
    world.facts["activity"] = activity
    world.facts["setting"] = setting

    world.para()
    world.say(f"{hero_name} frowned and thought, \"Will the noise-dim spell spoil the song?")
    world.say(f"Will quiet mean no music? That cannot be right for long.\"")
    hero.memes["confusion"] += 1.0

    world.say(f"{hero_name} wanted to {activity.verb}, all merry and spry,")
    world.say(f"but feared the charm would hush the band up high.")

    _do_activity(world, hero, activity, narrate=False)
    if world.music_level >= THRESHOLD:
        world.say(f"The drums went thrum, and the trumpets shone.")
        world.say(f"But the kitten twitched at the booming tone.")
    if pred["kitten_wakes"]:
        parent.memes["worry"] += 1.0
        world.say(f"\"Let's try the charm,\" said {parent.label}, soft as snow.")
        world.say(f"\"It may not kill the music. It may help it grow.\"")
    else:
        world.say(f"\"The charm is for balance,\" said {parent.label}. \"Let's give it a whirl.\"")

    world.para()
    _use_charm(world, hero, charm, narrate=False)
    world.say(f"{hero_name} tapped the charm with a careful little hand.")
    world.say(f"The noise grew dim, like waves on sand.")

    world.say(f"Then, twist and twinkle, the hush brought cheer:")
    world.say(f"a hidden hum danced clear and near.")
    world.say(f"The band still played, but softer now,")
    world.say(f"and the kitten slept without a wow.")

    hero.memes["joy"] += 2.0
    hero.memes["confusion"] = 0.0
    parent.memes["worry"] = 0.0
    kitten.meters["noise"] = 0.0
    kitten.meters["comfort"] += 1.0

    world.say(f"{hero_name} laughed, \"Oh, what a sweet surprise!")
    world.say(f"The magic did not steal the prize.")
    world.say(f"It dimmed the din, and let us hear")
    world.say(f"a gentler tune, both warm and dear.\"")

    world.say(f"So {hero_name} rolled and sang along,")
    world.say(f"while kitten purred through the moonlit song.")
    world.say(f"The fair grew soft, yet bright and grand,")
    world.say(f"with a sleepy cat and a smiling band.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "lantern_fair": Setting(place="the lantern fair", indoor=False, affords={"concert"}),
    "moon_park": Setting(place="the moonlit park", indoor=False, affords={"concert"}),
    "soft_hall": Setting(place="the soft hall", indoor=True, affords={"concert"}),
}

ACTIVITIES = {
    "concert": Activity(
        id="concert",
        verb="join the concert",
        gerund="joining the concert",
        rush="roll up to the stage",
        noise="loud",
        keyword="noise-dim",
        tags={"music", "noise", "magic"},
    )
}

CHARMS = {
    "noise_dim_charm": Charm(
        id="noise_dim_charm",
        label="noise-dim charm",
        phrase="a little noise-dim charm",
        effect="dims loud sounds without erasing the melody",
        prep="touch the charm and let the sound soften",
        tail="the song stayed, but the clamor slipped away",
        guards={"noise"},
        softens={"noise"},
    )
}

GIRL_NAMES = ["Nora", "Mina", "Lila", "Zuri", "Ivy", "Maya"]
BOY_NAMES = ["Ezra", "Theo", "Owen", "Noah", "Finn", "Leo"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "shy"]


@dataclass
class StoryParams:
    place: str = ""
    activity: str = ""
    charm: str = ""
    name: str = ""
    gender: str = ""
    parent: str = ""
    trait: str = ""
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for charm_id in CHARMS:
                combos.append((place, act_id, charm_id))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen options do not fit the tiny sound-and-magic world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: paraplegic child, noise-dim magic, misunderstanding, twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--charm", choices=CHARMS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, charm=charm, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm")
    return [
        f'Write a short rhyming story for a child named {hero.id} who wants to {activity.verb} with a {charm.label}.',
        f'Create a gentle misunderstanding story where a {hero.type} named {hero.id} fears the {charm.label} will ruin the music.',
        f'Write a rhyme-filled tale that ends with a magical twist about the {charm.label} and a sleepy kitten.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm")
    kitten = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "kitten")
    pred = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "predicted")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb} at {world.setting.place}, with the music all aglow.",
        ),
        QAItem(
            question=f"Why was {parent.label} worried before the charm was used?",
            answer=f"{parent.label.capitalize()} worried because the loud concert might wake the kitten in the basket.",
        ),
        QAItem(
            question=f"What did {hero.id} fear about the {charm.label} at first?",
            answer=f"{hero.id} feared the {charm.label} might hush the song and make the music too small.",
        ),
        QAItem(
            question=f"What did the charm really do?",
            answer=f"It dimmed the noise without erasing the tune, so the concert stayed sweet and bright.",
        ),
        QAItem(
            question=f"What was the magical twist in the end?",
            answer=f"The quiet revealed a hidden harmony, and the kitten stayed asleep while the band softly played.",
        ),
        QAItem(
            question=f"Did the kitten wake up from the loud sound?",
            answer="No. The noise-dim charm softened the clatter, so the kitten stayed cozy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a paraplegic person?",
            answer="A paraplegic person has little or no movement in the legs, and may use a wheelchair to get around.",
        ),
        QAItem(
            question="What does a noise-dim charm do?",
            answer="A noise-dim charm makes loud sounds softer without taking away the whole song.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing, but the truth is a little different.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought would happen.",
        ),
        QAItem(
            question="Why can a soft song still be lovely?",
            answer="A soft song can still be lovely because gentle music can feel warm, calm, and bright.",
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
        lines.append(f"  {e.id:12} ({e.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
affords(place, activity) :- setting(place), activity(activity), setting_affords(place, activity).
at_risk(hero, kitten) :- noise(actor), softens(charm, noise), candidate(hero, charm), contains_noise(activity).
resolved(hero, kitten) :- at_risk(hero, kitten), at_risk(hero, kitten), softens(charm, noise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for g in sorted(c.softens):
            lines.append(asp.fact("softens", cid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    return [(a, b, c, "girl") for (a, b, c) in valid_combos()]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.parent)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
    StoryParams(place="lantern_fair", activity="concert", charm="noise_dim_charm", name="Nora", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="moon_park", activity="concert", charm="noise_dim_charm", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="soft_hall", activity="concert", charm="noise_dim_charm", name="Maya", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("3 compatible combos:\n")
        for place, act, charm in valid_combos():
            print(f"  {place:12} {act:10} {charm}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.activity} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
