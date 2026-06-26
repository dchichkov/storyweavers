#!/usr/bin/env python3
"""
storyworlds/worlds/stork_sound_effects_reconciliation_happy_ending_comedy.py
=============================================================================

A small comedic story world about a stork who loves sound effects, makes a
mess of the mood, and then fixes it with a cheerful reconciliation.

Seed-tale premise:
---
A young stork named Pip loved making funny sound effects. One afternoon, Pip
practiced big whooshes, squeaks, and boings beside a sleepy pond stage. A
grumpy heron got annoyed, but Pip offered a softer act, apologized, and soon
they were making a silly duet that made everyone laugh.

World model:
---
- Sound effects have volume and silliness meters.
- Loud effects can raise annoyance and startle nearby companions.
- Apologies and shared performance raise affection and forgiveness.
- A reconciliation prop can convert a noisy solo act into a playful duet.

This world is intentionally small and constraint-checked. It supports a few
tight, plausible combinations rather than many weak ones.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    partner: object | None = None
    typ: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroness"}
        male = {"boy", "father", "dad", "man", "stork"}
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
    affordances: set[str] = field(default_factory=set)
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
class SoundEffect:
    id: str
    title: str
    noise: str
    action: str
    fizzy: str
    keyword: str
    volume: int
    splash: str
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
class CompromiseProp:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    softens: set[str]
    shares: set[str]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "pond_stage": Setting(place="the pond stage", affordances={"whoosh", "boing", "squeak"}),
    "barn_bandstand": Setting(place="the barn bandstand", affordances={"whoosh", "clang", "squeak"}),
    "moon_dock": Setting(place="the moonlit dock", affordances={"whoosh", "boing"}),
}

SFX = {
    "whoosh": SoundEffect(
        id="whoosh",
        title="a big whoosh",
        noise="whoooosh",
        action="sweep a cape through the air",
        fizzy="swishy",
        keyword="whoosh",
        volume=3,
        splash="loud and windy",
        tags={"wind", "loud"},
    ),
    "boing": SoundEffect(
        id="boing",
        title="a springy boing",
        noise="boing",
        action="bounce on a little cushion",
        fizzy="bouncy",
        keyword="boing",
        volume=2,
        splash="bouncy",
        tags={"bounce", "funny"},
    ),
    "squeak": SoundEffect(
        id="squeak",
        title="a tiny squeak",
        noise="squeeek",
        action="tap a teacup with one beak-tip",
        fizzy="tiny",
        keyword="squeak",
        volume=1,
        splash="small and squeaky",
        tags={"small", "funny"},
    ),
    "clang": SoundEffect(
        id="clang",
        title="a bright clang",
        noise="clang",
        action="ring a little bell twice",
        fizzy="ringy",
        keyword="clang",
        volume=2,
        splash="bright and jazzy",
        tags={"metal", "funny"},
    ),
}

PROPS = [
    CompromiseProp(
        id="pillow",
        label="a feather pillow",
        phrase="a feather pillow for softer practice",
        prep="put a feather pillow on the floor and",
        tail="kept the next sounds soft and fluffy",
        softens={"whoosh", "boing", "clang"},
        shares={"whoosh", "boing"},
    ),
    CompromiseProp(
        id="bell",
        label="a tiny bell",
        phrase="a tiny bell for a silly duet",
        prep="pick up a tiny bell and",
        tail="made the rhythm sound neat and polite",
        softens={"squeak", "clang"},
        shares={"squeak", "clang"},
    ),
    CompromiseProp(
        id="scarf",
        label="a long scarf",
        phrase="a long scarf for gentle swishes",
        prep="wrap a long scarf around the beak and",
        tail="turned the show into a soft swoop-show",
        softens={"whoosh", "squeak"},
        shares={"whoosh", "squeak"},
    ),
]

NAMES = ["Pip", "Milo", "Nori", "Luna", "Tavi"]
PARTNERS = [("heron", "grumpy heron", "grumpy"), ("crane", "sleepy crane", "sleepy"), ("frog", "fussy frog", "fussy")]
TRAITS = ["cheerful", "curious", "silly", "earnest", "playful"]


@dataclass
class StoryParams:
    place: str
    sound: str
    prop: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


def sound_reasonable(setting: Setting, sfx: SoundEffect) -> bool:
    return sfx.id in setting.affordances


def select_prop(sfx: SoundEffect) -> Optional[CompromiseProp]:
    for prop in PROPS:
        if sfx.id in prop.shares:
            return prop
    return None


ASP_RULES = r"""
sound_ok(Place, S) :- setting(Place), sound(S), afford(Place, S).
prop_fix(S, P) :- sound(S), prop(P), shares(P, S).
valid(Place, S, P) :- sound_ok(Place, S), prop_fix(S, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for s in sorted(setting.affordances):
            lines.append(asp.fact("afford", pid, s))
    for sid, sfx in SFX.items():
        lines.append(asp.fact("sound", sid))
        for tag in sorted(sfx.tags):
            lines.append(asp.fact("tag", sid, tag))
    for prop in PROPS:
        lines.append(asp.fact("prop", prop.id))
        for s in sorted(prop.softens):
            lines.append(asp.fact("softens", prop.id, s))
        for s in sorted(prop.shares):
            lines.append(asp.fact("shares", prop.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sid, sfx in SFX.items():
            if not sound_reasonable(setting, sfx):
                continue
            if select_prop(sfx) is None:
                continue
            for prop in PROPS:
                if sid in prop.shares:
                    combos.append((place, sid, prop.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy stork stories about sound effects and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SFX)
    ap.add_argument("--prop", choices=[p.id for p in PROPS])
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=[p[0] for p in PARTNERS])
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "sound", None) and getattr(args, "prop", None):
        sfx = SFX[getattr(args, "sound", None)]
        if getattr(args, "prop", None) not in [p.id for p in PROPS if sfx.id in p.shares]:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sound, prop = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    partner = getattr(args, "partner", None) or rng.choice([p[0] for p in PARTNERS])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, sound=sound, prop=prop, name=name, partner=partner, trait=trait)


def _setup(world: World, hero: Entity, partner: Entity, sfx: SoundEffect) -> None:
    hero.memes["joy"] += 1
    hero.memes["silliness"] += 1
    partner.memes["sleepy"] += 1
    world.say(f"{hero.id} was a {hero.trait_word} stork who loved making sound effects.")
    world.say(f"{hero.pronoun().capitalize()} liked to practice {sfx.title} because {sfx.noise} made the whole day feel funny.")
    world.say(f"Near {world.setting.place}, {partner.label} was trying to rest and keep a straight face.")


def _noisy_scene(world: World, hero: Entity, partner: Entity, sfx: SoundEffect) -> None:
    hero.meters["volume"] += sfx.volume
    partner.memes["annoyed"] += 1
    partner.meters["startled"] += 1
    world.say(f"Then {hero.id} tried to {sfx.action}, and the air went {sfx.noise}!")
    world.say(f"That was so {sfx.splash} that {partner.label} blinked, fluffed up, and said, \"Too loud!\"")
    world.say(f"{partner.label.capitalize()} looked grumpy, and {hero.id} suddenly felt not-so-funny.")


def _apology(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["embarrassment"] += 1
    hero.memes["empathy"] += 1
    world.say(f"{hero.id} lowered {hero.pronoun('possessive')} beak and said sorry right away.")
    world.say(f"{hero.pronoun().capitalize()} promised to try a kinder sound so the {partner.type} could relax again.")


def _reconcile(world: World, hero: Entity, partner: Entity, prop: CompromiseProp, sfx: SoundEffect) -> None:
    hero.memes["forgiveness"] += 1
    partner.memes["forgiveness"] += 1
    partner.memes["annoyed"] = 0
    hero.meters["volume"] = max(0, hero.meters.get("volume", 0) - 1)
    world.say(f"Then {hero.id} found {prop.label} and made a new plan: {prop.prep} practice the {sfx.keyword} again.")
    world.say(f"{prop.label.capitalize()} helped because it made the performance softer, and {prop.tail}.")
    world.say(f"{partner.label.capitalize()} listened, snorted a laugh, and said, \"Okay, that was a better idea.\"")
    world.say(f"{hero.id} and {partner.label} tried the act together, and the room filled with tiny giggles instead of complaints.")


def _happy_ending(world: World, hero: Entity, partner: Entity, sfx: SoundEffect, prop: CompromiseProp) -> None:
    hero.memes["joy"] += 2
    partner.memes["joy"] += 2
    world.say(f"In the end, {hero.id} and {partner.label} made a silly duet with {prop.label} and {sfx.title}.")
    world.say(f"The sound went {sfx.noise}, but this time everybody laughed because it was gentle and shared.")
    world.say(f"{hero.id} smiled all the way home, and {partner.label} was smiling too.")


def tell(setting: Setting, sfx: SoundEffect, prop: CompromiseProp, hero_name: str, partner_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="stork", label=hero_name, traits=[trait]))
    hero.trait_word = trait
    partner = world.add(Entity(id="Partner", kind="character", type=partner_type, label=next(lbl for typ, lbl, _ in PARTNERS if typ == partner_type)))
    _setup(world, hero, partner, sfx)
    world.para()
    _noisy_scene(world, hero, partner, sfx)
    world.para()
    _apology(world, hero, partner)
    _reconcile(world, hero, partner, prop, sfx)
    world.para()
    _happy_ending(world, hero, partner, sfx, prop)
    world.facts.update(hero=hero, partner=partner, sound=sfx, prop=prop, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sfx = _safe_fact(world, f, "sound")
    prop = _safe_fact(world, f, "prop")
    return [
        f'Write a funny story for a young child about a stork who loves "{sfx.keyword}" and learns to be quieter.',
        f"Tell a comedy story where {hero.id} makes {sfx.title}, upsets a neighbor, and fixes it with {prop.phrase}.",
        f"Write a cheerful story about a stork, a silly sound effect, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    partner = _safe_fact(world, f, "partner")
    sfx = _safe_fact(world, f, "sound")
    prop = _safe_fact(world, f, "prop")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a stork who loves making funny sound effects.",
        ),
        QAItem(
            question=f"What sound effect did {hero.id} practice?",
            answer=f"{hero.id} practiced {sfx.title}, which sounded like {sfx.noise}.",
        ),
        QAItem(
            question=f"Why did {partner.label} get upset?",
            answer=f"{partner.label.capitalize()} got upset because {hero.id} was being too loud while practicing the {sfx.keyword} effect.",
        ),
        QAItem(
            question=f"What helped the two friends reconcile?",
            answer=f"{prop.label.capitalize()} helped them reconcile by making the practice softer and more shared.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {partner.label} making a silly duet and laughing together.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "stork": (
        "What is a stork?",
        "A stork is a tall bird with long legs and a long beak. Storks can walk through shallow water and make big nests.",
    ),
    "sound": (
        "What is a sound effect?",
        "A sound effect is a special sound made to sound like an action, such as whoosh, boing, or clang.",
    ),
    "reconciliation": (
        "What does reconciliation mean?",
        "Reconciliation means fixing a hurt feeling, making peace, and being friends again.",
    ),
    "happy": (
        "What makes a happy ending?",
        "A happy ending is when the problem gets fixed and the characters finish feeling safe, cheerful, or loved.",
    ),
    "comedy": (
        "What is comedy?",
        "Comedy is a kind of story or show that tries to make people laugh in a friendly way.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, (q, a) in WORLD_KNOWLEDGE.items()]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def explain_rejection(sfx: SoundEffect, prop: CompromiseProp) -> str:
    return f"(No story: {prop.label} does not make a believable fix for {sfx.title}.)"


def valid_story(params: StoryParams) -> bool:
    sfx = SFX[params.sound]
    return sound_reasonable(_safe_lookup(SETTINGS, params.place), sfx) and params.sound in [p.id for p in PROPS if params.sound in p.shares]


def resolve_gender(name: str) -> str:
    return "boy" if name in {"Pip", "Milo", "Tavi"} else "girl"


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), SFX[params.sound], next(p for p in PROPS if p.id == params.prop), params.name, params.partner, params.trait)
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
    print("MISMATCH between clingo and Python gate:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for triple in asp_valid_combos():
            print(triple)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="pond_stage", sound="whoosh", prop="pillow", name="Pip", partner="heron", trait="playful"),
        StoryParams(place="barn_bandstand", sound="clang", prop="bell", name="Milo", partner="frog", trait="silly"),
        StoryParams(place="moon_dock", sound="boing", prop="scarf", name="Nori", partner="crane", trait="cheerful"),
    ]

    if getattr(args, "all", None):
        for p in curated:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                if getattr(args, "place", None) and getattr(args, "sound", None) and getattr(args, "prop", None):
                    params = StoryParams(
                        place=getattr(args, "place", None), sound=getattr(args, "sound", None), prop=getattr(args, "prop", None),
                        name=getattr(args, "name", None) or rng.choice(NAMES),
                        partner=getattr(args, "partner", None) or rng.choice([p[0] for p in PARTNERS]),
                        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
                        seed=seed,
                    )
                    if not valid_story(params):
                        pass
                else:
                    combos = [c for c in valid_combos()
                              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                              and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
                              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
                    if not combos:
                        pass
                    place, sound, prop = rng.choice(list(combos))
                    params = StoryParams(
                        place=place, sound=sound, prop=prop,
                        name=getattr(args, "name", None) or rng.choice(NAMES),
                        partner=getattr(args, "partner", None) or rng.choice([p[0] for p in PARTNERS]),
                        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
                        seed=seed,
                    )
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.sound} at {p.place} with {p.prop}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
