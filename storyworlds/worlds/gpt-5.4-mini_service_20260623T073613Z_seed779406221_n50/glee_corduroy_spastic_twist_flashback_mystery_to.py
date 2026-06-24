#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073613Z_seed779406221_n50/glee_corduroy_spastic_twist_flashback_mystery_to.py
===============================================================================================================

A standalone storyworld script for a small superhero-style mystery tale.

Premise:
- A child superhero loves to help in the city.
- Their corduroy cape is part of the signature look.
- A spastic, jumpy clue trail leads to a mystery to solve.
- A twist and a flashback reveal who needs help and why.
- The ending proves the change in the world state: the mystery is solved,
  the helper is calmer, and the city is safer.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of results.py containers
- lazy import of asp.py in ASP helpers only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- JSON / QA / trace / ASP / verify / show-asp support
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
    location: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    clue: object | None = None
    hidden: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class HeroCfg:
    id: str
    label: str
    type: str
    phrase: str
    cape: str
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
class MysteryCfg:
    id: str
    clue: str
    culprit: str
    hidden: str
    resolution: str
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
class TwistCfg:
    id: str
    reveal: str
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
class FlashbackCfg:
    id: str
    memory: str
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
        return c


SETTING = Setting(
    place="the city square",
    mood="bright",
    affords={"patrol", "chase", "solve"},
)

HEROES = {
    "glee": HeroCfg(
        id="Glee",
        label="Glee",
        type="hero",
        phrase="a kid superhero named Glee",
        cape="corduroy cape",
        tags={"glee", "cape", "corduroy"},
    ),
    "glimmer": HeroCfg(
        id="Glimmer",
        label="Glimmer",
        type="hero",
        phrase="a kid superhero named Glimmer",
        cape="corduroy cape",
        tags={"glee", "cape", "corduroy"},
    ),
}

MYSTERIES = {
    "bell": MysteryCfg(
        id="bell",
        clue="a jangly clue trail",
        culprit="a stuck clock rope",
        hidden="the old bell",
        resolution="the bell rang again",
        tags={"mystery", "solve", "twist"},
    ),
    "kite": MysteryCfg(
        id="kite",
        clue="a fluttering clue trail",
        culprit="a windy rooftop knot",
        hidden="the missing kite",
        resolution="the kite was found",
        tags={"mystery", "solve", "twist"},
    ),
    "musicbox": MysteryCfg(
        id="musicbox",
        clue="a tinkly clue trail",
        culprit="a loose spring",
        hidden="the music box",
        resolution="the music box played again",
        tags={"mystery", "solve", "twist"},
    ),
}

TWISTS = {
    "helper": TwistCfg(
        id="helper",
        reveal="the 'mystery' was actually a friend asking for help",
        tags={"twist"},
    ),
    "echo": TwistCfg(
        id="echo",
        reveal="the strange sound came from a helpful echo under the bridge",
        tags={"twist"},
    ),
    "pet": TwistCfg(
        id="pet",
        reveal="the clue trail belonged to a lost pet trying to get home",
        tags={"twist"},
    ),
}

FLASHBACKS = {
    "promise": FlashbackCfg(
        id="promise",
        memory="the hero remembered promising to listen for trouble in the square",
        tags={"flashback"},
    ),
    "training": FlashbackCfg(
        id="training",
        memory="the hero remembered training to follow small clues one by one",
        tags={"flashback"},
    ),
    "lantern": FlashbackCfg(
        id="lantern",
        memory="the hero remembered how a lantern glow once showed the way home",
        tags={"flashback"},
    ),
}

TRAITS = ["brave", "curious", "kind", "quick", "steady"]


@dataclass
class StoryParams:
    hero: str
    mystery: str
    twist: str
    flashback: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for h in HEROES:
        for m in MYSTERIES:
            for t in TWISTS:
                for f in FLASHBACKS:
                    combos.append((h, m, t, f))
    return combos


def explain_rejection() -> str:
    return "(No story: this mystery needs a hero, a clue, a twist, and a flashback.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero mystery with a corduroy cape, a twist, and a flashback."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
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
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "hero", None) and getattr(args, "hero", None) not in HEROES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mystery", None) and getattr(args, "mystery", None) not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "twist", None) and getattr(args, "twist", None) not in TWISTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "flashback", None) and getattr(args, "flashback", None) not in FLASHBACKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in combos
        if (getattr(args, "hero", None) is None or c[0] == getattr(args, "hero", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
        and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))
        and (getattr(args, "flashback", None) is None or c[3] == getattr(args, "flashback", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero, mystery, twist, flashback = rng.choice(list(combos))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(hero=hero, mystery=mystery, twist=twist, flashback=flashback, trait=trait)


def asp_facts() -> str:
    import asp
    lines = []
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for f in FLASHBACKS:
        lines.append(asp.fact("flashback", f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H,M,T,F) :- hero(H), mystery(M), twist(T), flashback(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def _hero(world: World, cfg: HeroCfg, trait: str) -> Entity:
    return world.add(Entity(
        id=cfg.id,
        kind="character",
        type="hero",
        label=cfg.label,
        phrase=cfg.phrase,
        role="hero",
        meters={"speed": 0.0},
        memes={"glee": 1.0, "curiosity": 1.0},
        tags=set(cfg.tags) | {trait},
    ))


def tell(setting: Setting, hero_cfg: HeroCfg, mystery: MysteryCfg, twist: TwistCfg,
         flashback: FlashbackCfg, trait: str) -> World:
    world = World(setting)
    hero = _hero(world, hero_cfg, trait)
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue, tags=set(mystery.tags)))
    hidden = world.add(Entity(id="hidden", type="thing", label=mystery.hidden, tags=set(mystery.tags)))
    world.add(Entity(id="cape", type="thing", label=hero_cfg.cape, worn_by=hero.id, tags={"corduroy"}))

    hero.meters["glee"] += 1
    hero.memes["glee"] += 1
    world.say(
        f"{hero.label} stood in {setting.place} with a {hero_cfg.cape}, feeling all glee and ready to help."
    )
    world.say(
        f"{hero.label} noticed {mystery.clue}. It looked like a mystery to solve."
    )

    world.para()
    hero.memes["curiosity"] += 1
    hero.meters["search"] += 1
    world.say(
        f"{hero.label} followed the clue trail through the square, step by step, "
        f"while {flashback.memory}."
    )
    world.say(
        f"Then came the twist: {twist.reveal}."
    )

    world.para()
    if twist.id == "helper":
        hidden.label = "a worried helper"
        world.say(
            f"The clue trail led to {hidden.label}, who needed a hand fixing {mystery.culprit}."
        )
        hero.memes["kindness"] += 1
    elif twist.id == "pet":
        hidden.label = "a lost little pet"
        world.say(
            f"The clue trail led to {hidden.label}, who had been trying to get back to its home."
        )
        hero.memes["kindness"] += 1
    else:
        world.say(
            f"The clue trail led under the bridge, where the sound bounced back as an echo."
        )
        hero.memes["attention"] += 1

    world.para()
    hero.meters["speed"] += 1
    hero.memes["glee"] += 1
    hidden.meters["safe"] += 1
    world.say(
        f"{hero.label} solved the mystery to solve the day: {mystery.resolution}. "
        f"The corduroy cape swished, and the city square felt calm again."
    )
    world.say(
        f"{hero.label} smiled with glee, because the big clue was no longer a puzzle."
    )

    world.facts.update(
        hero=hero,
        hero_cfg=hero_cfg,
        mystery=mystery,
        twist=twist,
        flashback=flashback,
        trait=trait,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a superhero story for a young child that includes the words "glee" and "corduroy".',
        f"Tell a mystery to solve about {hero.label} in {f['setting'].place} with a twist and a flashback.",
        f"Write a child-friendly superhero story where a clue trail leads to a surprising reveal and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    twist = f["twist"]
    flashback = f["flashback"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.label}, who wears a corduroy cape and helps in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"The mystery was {mystery.hidden}. {mystery.clue} led {hero.label} toward the answer.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}. That changed what the clue trail really meant.",
        ),
        QAItem(
            question=f"What flashback helped the hero?",
            answer=f"The flashback was that {flashback.memory}. It helped {hero.label} stay focused and solve the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {mystery.resolution}, and {hero.label} felt bright with glee again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is corduroy?",
            answer="Corduroy is a cloth with soft ridges, often used for clothes like pants or jackets.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the reader can understand the present better.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem with hidden parts that people try to figure out by following clues.",
        ),
    ]


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="glee", mystery="bell", twist="helper", flashback="promise", trait="brave"),
    StoryParams(hero="glimmer", mystery="kite", twist="pet", flashback="training", trait="curious"),
    StoryParams(hero="glee", mystery="musicbox", twist="echo", flashback="lantern", trait="steady"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING,
        _safe_lookup(HEROES, params.hero),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(TWISTS, params.twist),
        _safe_lookup(FLASHBACKS, params.flashback),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible hero/mystery/twist/flashback combos:")
        for h, m, t, f in combos[:25]:
            print(f"  {h:8} {m:10} {t:8} {f}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero} / {p.mystery} / {p.twist} / {p.flashback}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
