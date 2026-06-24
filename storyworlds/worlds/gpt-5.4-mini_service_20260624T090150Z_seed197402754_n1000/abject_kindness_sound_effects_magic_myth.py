#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/abject_kindness_sound_effects_magic_myth.py
==============================================================================================

A small mythic story world about abject trouble, kindness, sound effects, and magic.

Seed tale imagined from the prompt:
---
In a dry old valley, a small keeper named Iri found a cracked bronze bell that only
rang with a sad clink. The bell had belonged to a forgotten fountain, and when it
silenced, the valley's little sparks of luck went thin and dim.

Iri wanted to throw the bell into the dust, because it felt abject and useless.
But the valley's elder said the bell was waiting for a kinder voice. So Iri washed
it, sang to it, and struck it with a reed wand. The bell woke with bright chimes,
the fountain stirred, and the valley filled with warm music again.
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


# ---------------------------------------------------------------------------
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "keeper"}:
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
    place: str = "the valley"
    mood: str = "dry"
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
class Trial:
    id: str
    name: str
    cue: str
    damage: str
    risk: str
    sound_on_fail: str
    sound_on_fix: str
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    burden: str
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
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    sound: str
    kindness_boost: str
    magic_boost: str
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
        self.sound: str = ""

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.sound = self.sound
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "valley": Setting(place="the valley", mood="dry", affords={"bell", "spring"}),
    "temple": Setting(place="the temple court", mood="echoing", affords={"bell"}),
    "grove": Setting(place="the moon grove", mood="murmuring", affords={"spring", "bell"}),
}

TRIALS = {
    "bell": Trial(
        id="bell",
        name="the cracked bronze bell",
        cue="clink",
        damage="silent and dull",
        risk="goes hollow",
        sound_on_fail="a sad clink",
        sound_on_fix="bright chimes",
        tags={"sound", "magic"},
    ),
    "spring": Trial(
        id="spring",
        name="the sleeping spring",
        cue="drip",
        damage="dry and dusty",
        risk="runs thin",
        sound_on_fail="a lonely drip",
        sound_on_fix="clear running notes",
        tags={"magic"},
    ),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="a little copper lantern",
        type="lantern",
        burden="dim and tarnished",
    ),
    "bell": Relic(
        id="bell",
        label="bell",
        phrase="a cracked bronze bell",
        type="bell",
        burden="silent and abject",
    ),
    "cup": Relic(
        id="cup",
        label="cup",
        phrase="a clay cup with a hairline crack",
        type="cup",
        burden="leaking and sad",
    ),
}

CHARMS = {
    "reed": Charm(
        id="reed",
        label="reed wand",
        phrase="a polished reed wand",
        guards={"bell", "spring"},
        covers={"sound", "magic"},
        sound="tink",
        kindness_boost="gentle care",
        magic_boost="a small spell",
    ),
    "water": Charm(
        id="water",
        label="holy water bowl",
        phrase="a bowl of shining water",
        guards={"spring"},
        covers={"magic"},
        sound="plink",
        kindness_boost="soft washing",
        magic_boost="a blessing",
    ),
    "song": Charm(
        id="song",
        label="hymn",
        phrase="an old kindness hymn",
        guards={"bell"},
        covers={"sound"},
        sound="hum",
        kindness_boost="a kind song",
        magic_boost="a warm vow",
    ),
}


# ---------------------------------------------------------------------------
# Params / parser
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trial: str
    relic: str
    charm: str
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


GIRL_NAMES = ["Iri", "Mina", "Lena", "Sera", "Nora", "Tala"]
BOY_NAMES = ["Oren", "Bram", "Doro", "Kian", "Rhett", "Lio"]
ELDER_NAMES = ["the elder", "the old guide", "the temple keeper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of abject trouble and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
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


def _compatible(trial: Trial, relic: Relic, charm: Charm) -> bool:
    return trial.id in charm.guards and relic.type in {"bell", "lantern", "cup"}


def explain_rejection(trial: Trial, relic: Relic) -> str:
    return f"(No story: {trial.name} and {relic.label} do not make a believable mythic problem together.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "trial", None) and getattr(args, "relic", None) and getattr(args, "charm", None):
        if not _compatible(_safe_lookup(TRIALS, getattr(args, "trial", None)), _safe_lookup(RELICS, getattr(args, "relic", None)), _safe_lookup(CHARMS, getattr(args, "charm", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for place, s in SETTINGS.items():
        for trial_id in s.affords:
            trial = _safe_lookup(TRIALS, trial_id)
            for relic_id, relic in RELICS.items():
                for charm_id, charm in CHARMS.items():
                    if _compatible(trial, relic, charm):
                        combos.append((place, trial_id, relic_id, charm_id))
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, trial_id, relic_id, charm_id = rng.choice(list(combos))
    relic = _safe_lookup(RELICS, relic_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(relic.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, trial=trial_id, relic=relic_id, charm=charm_id,
                       name=name, gender=gender, elder=elder)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def _perform(world: World, hero: Entity, trial: Trial, relic: Entity, charm: Charm, narrate: bool = True) -> None:
    hero.meters[trial.id] = hero.meters.get(trial.id, 0) + 1
    if world.setting.place in {"the valley", "the moon grove"}:
        if trial.id == "bell":
            world.sound = trial.sound_on_fix if hero.memes.get("kindness", 0) >= 1 and hero.memes.get("magic", 0) >= 1 else trial.sound_on_fail
    if narrate:
        world.say(f"The air answered with {world.sound or trial.sound_on_fail}.")


def tell(setting: Setting, trial: Trial, relic_cfg: Relic, charm: Charm, hero_name: str,
         hero_gender: str, elder_name: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_gender))
    elder = w.add(Entity(id="elder", kind="character", type="elder", label=elder_name))
    relic = w.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label,
                         phrase=relic_cfg.phrase, owner=hero.id, caretaker=elder.id,
                         plural=relic_cfg.plural))
    charm_ent = w.add(Entity(id=charm.id, type="charm", label=charm.label, phrase=charm.phrase))

    hero.memes["kindness"] = 1
    hero.memes["magic"] = 0
    w.sound = trial.sound_on_fail

    w.say(f"In {setting.place}, there was a story of {relic.phrase}, abject and worn like a forgotten prayer.")
    w.say(f"{hero.name if hasattr(hero, 'name') else hero.id} was a small {hero_gender} who did not want to leave the {relic.label} in silence.")
    w.say(f"{hero.id} loved kindness and the old ways, and {elder_name} said the relic would answer only to a gentle hand.")

    w.para()
    w.say(f"One dusk, {trial.name} began to {trial.risk}; its first note was {trial.sound_on_fail}.")
    w.say(f"{hero.id} lifted {hero.pronoun('possessive')} chin and held the {charm.label} near the relic.")
    hero.memes["dread"] = 1
    hero.memes["kindness"] += 1
    w.say(f"'{trial.name.capitalize()} must not be left abject,' {elder_name} whispered, 'for even broken things can remember their name.'")

    w.para()
    if trial.id == "bell":
        w.say(f"{hero.id} washed the bell, spoke a kind word, and tapped it with the {charm.label}.")
        hero.memes["magic"] += 1
        _perform(w, hero, trial, relic, charm, narrate=True)
        w.say(f"Then the relic answered with {trial.sound_on_fix}, and the whole court seemed to breathe again.")
    else:
        w.say(f"{hero.id} poured water with care, sang a kindness hymn, and traced a small spell in the air.")
        hero.memes["magic"] += 1
        _perform(w, hero, trial, relic, charm, narrate=True)
        w.say(f"The spring woke with {trial.sound_on_fix}, and the dry stones shone as if they had learned to hope.")

    w.facts.update(hero=hero, elder=elder, relic=relic, trial=trial, charm=charm, setting=setting)
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about "{f["trial"].name}" and a kind helper who uses magic.',
        f"Tell a gentle story in which {f['hero'].id} helps {f['elder'].label} heal {f['relic'].phrase} with {f['charm'].label}.",
        f'Write a mythic story that includes the word "abject" and ends with bright sound effects.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic, trial, charm = f["hero"], f["elder"], f["relic"], f["trial"], f["charm"]
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.id}, who tried to help {elder.label} and the {relic.label}.",
        ),
        QAItem(
            question=f"What made the problem feel abject at first?",
            answer=f"The {relic.label} felt {relic.burden}, and the {trial.name} sounded like {trial.sound_on_fail}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used {charm.label}, kindness, and a little magic to wake the relic again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {trial.sound_on_fix} and the sense that the {relic.label} had been restored.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does kindness mean?", answer="Kindness means acting gently, helping, and caring about how someone else feels."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words that help you hear the noises a story makes, like clink, hum, or chime."),
        QAItem(question="What is magic in a myth?", answer="In a myth, magic is a wondrous power that can wake, bless, transform, or protect things."),
        QAItem(question="What does abject mean?", answer="Abject means very bad, very sad, or very low, like something forgotten or in poor shape."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
compatible(T,R,C) :- trial(T), relic(R), charm(C), guards(C,T), relic_kind(R,K), can_heal(C,K).
valid_story(P,T,R,C) :- place(P), affords(P,T), compatible(T,R,C).
#show valid_story/4.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", p, t))
    for t in TRIALS.values():
        lines.append(asp.fact("trial", t.id))
    for r in RELICS.values():
        lines.append(asp.fact("relic", r.id))
        lines.append(asp.fact("relic_kind", r.id, r.type))
        if r.plural:
            lines.append(asp.fact("relic_plural", r.id))
    for c in CHARMS.values():
        lines.append(asp.fact("charm", c.id))
        for t in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, t))
        for k in sorted({"bell", "lantern", "cup"}):
            lines.append(asp.fact("can_heal", c.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in SETTINGS:
        for t in _safe_lookup(SETTINGS, p).affords:
            for r in RELICS:
                for c in CHARMS:
                    if _compatible(_safe_lookup(TRIALS, t), _safe_lookup(RELICS, r), _safe_lookup(CHARMS, c)):
                        out.append((p, t, r, c))
    return sorted(out)


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emit / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="valley", trial="bell", relic="bell", charm="reed", name="Iri", gender="girl", elder="the elder"),
    StoryParams(place="grove", trial="spring", relic="cup", charm="water", name="Oren", gender="boy", elder="the old guide"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(RELICS, params.relic),
                 _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  sound={world.sound}")
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


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(""))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories:")
        for t in vals:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 20, 20)):
            if len(samples) >= getattr(args, "n", None):
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
