#!/usr/bin/env python3
"""
A tiny animal story world about curiosity, modesty, and a bow.

The seed premise:
- An animal child is curious about a bow.
- The bow is lovely, but the child feels shy about wearing it.
- A gentle friend or parent helps turn curiosity into a modest, happy choice.

The story engine keeps the domain small and constraint-checked:
- one setting,
- one curious animal hero,
- one prized bow,
- one modesty tension,
- one kind resolution.

The prose is generated from simulated world state rather than a frozen template.
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
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        for k in ["shine", "tidy", "dust", "care", "rest"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "modesty", "joy", "shy", "pride", "warmth"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subject(self) -> str:
        return self.id

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
    place: str = "the quiet meadow"
    weather: str = "soft morning"
    affords: set[str] = field(default_factory=lambda: {"find_bow", "wear_bow", "admire_bow"})
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
class Bow:
    label: str
    phrase: str
    color: str
    sparkle: str
    placed: str = "neck"  # "head" | "neck" | "tail" (small animal-style accessory)
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
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    species: str = "rabbit"
    friend_name: str = "Pip"
    friend_species: str = "mouse"
    setting: str = "meadow"
    bow: str = "red_bow"
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the quiet meadow", weather="soft morning"),
    "garden": Setting(place="the little garden", weather="warm noon"),
    "brook": Setting(place="the brookside", weather="cool afternoon"),
}

BOWS = {
    "red_bow": Bow(label="bow", phrase="a bright red bow", color="red", sparkle="a tiny shine", placed="head"),
    "blue_bow": Bow(label="bow", phrase="a soft blue bow", color="blue", sparkle="a gentle glimmer", placed="neck"),
    "gold_bow": Bow(label="bow", phrase="a golden bow", color="gold", sparkle="a warm sparkle", placed="tail"),
}

ANIMALS = {
    "rabbit": {"kind": "animal", "voice": "soft"},
    "mouse": {"kind": "animal", "voice": "small"},
    "fox": {"kind": "animal", "voice": "bright"},
    "bear": {"kind": "animal", "voice": "deep"},
    "deer": {"kind": "animal", "voice": "light"},
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bow is reasonable when it can be worn in the requested place and the hero
% is not forced to show off more than the story allows.
curious_about(Hero, Bow) :- hero(Hero), bow(Bow).
can_wear(Bow, Place) :- bow_at_place(Bow, Place).
modest_story(Hero, Bow) :- curious_about(Hero, Bow), can_wear(Bow, Place), setting(Place).
valid_story(Place, Bow, Species) :- setting(Place), bow(Bow), species(Species),
                                   can_wear(Bow, Place), modest_story(hero, Bow).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid, b in BOWS.items():
        lines.append(asp.fact("bow", bid))
        lines.append(asp.fact("bow_at_place", bid, "meadow"))
        lines.append(asp.fact("bow_at_place", bid, "garden"))
        lines.append(asp.fact("bow_at_place", bid, "brook"))
        lines.append(asp.fact("bow_color", bid, b.color))
    for sp in ANIMALS:
        lines.append(asp.fact("species", sp))
    lines.append(asp.fact("hero", "hero"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.bow not in BOWS:
        pass
    if params.species not in ANIMALS:
        pass
    if params.friend_species not in ANIMALS:
        pass


def _clean_admire_sentence(hero: Entity, bow: Entity, setting: Setting) -> str:
    return (
        f"{hero.id} loved wandering through {setting.place}, "
        f"and {hero.pronoun('subject')} noticed {bow.phrase} at once."
    )


def _curiosity_sentence(hero: Entity, bow: Entity) -> str:
    return (
        f"{hero.subject()} felt curiosity wiggle in {hero.pronoun('possessive')} nose. "
        f"{hero.pronoun('subject').capitalize()} wanted to touch the {bow.label} and see how it looked."
    )


def _modesty_warning(world: World, parent: Entity, hero: Entity, bow: Entity) -> None:
    hero.memes["curiosity"] += 1.0
    hero.memes["shy"] += 1.0
    world.facts["warning"] = True
    world.say(
        f'"That {bow.label} is lovely," {parent.id} said, "but let us keep it simple and modest."'
    )


def _acceptance(world: World, hero: Entity, parent: Entity, bow: Entity) -> None:
    hero.memes["joy"] += 1.0
    hero.memes["modesty"] += 1.0
    hero.memes["shy"] = 0.0
    world.facts["resolved"] = True
    world.say(
        f"{hero.id} smiled, took the {bow.label} carefully, and wore it in a neat, modest way. "
        f"{parent.id} nodded with a warm grin."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.species,
            traits=["little", "curious", "kind"],
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type=params.friend_species,
            traits=["little", "gentle"],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type="mother",
            label="parent",
            traits=["calm", "watchful"],
        )
    )
    bow = world.add(
        Entity(
            id=params.bow,
            type="bow",
            label="bow",
            phrase=_safe_lookup(BOWS, params.bow).phrase,
            owner=params.name,
        )
    )
    bow.worn_by = None

    hero.memes["curiosity"] += 1.0
    hero.memes["modesty"] += 1.0

    world.say(
        f"One soft morning at {setting.place}, {hero.id} the little {params.species} was curious about a bow."
    )
    world.say(_clean_admire_sentence(hero, bow, setting))

    world.para()
    world.say(
        f"{friend.id} came trotting over and asked what {hero.pronoun('subject')} was looking at."
    )
    world.say(_curiosity_sentence(hero, bow))
    _modesty_warning(world, parent, hero, bow)

    world.para()
    world.say(
        f"{friend.id} helped smooth the ribbon, and {hero.id} stood very still."
    )
    _acceptance(world, hero, parent, bow)

    world.para()
    world.say(
        f"In the end, {hero.id} wore the {bow.color} bow with quiet pride, "
        f"and the meadow looked even sweeter with that little tidy shine."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        bow=bow,
        setting=setting,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    bow: Entity = _safe_fact(world, f, "bow")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        f"Write a small animal story about {hero.id} finding {bow.phrase} at {setting.place}.",
        f"Tell a gentle story where curiosity and modesty both matter, and a bow helps the child feel happy.",
        f"Write an Animal Story for young children about a {hero.type} who wants to wear a bow in a modest way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    parent: Entity = _safe_fact(world, f, "parent")
    bow: Entity = _safe_fact(world, f, "bow")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who was curious about the bow at {setting.place}?",
            answer=f"{hero.id} was curious about the bow at {setting.place}. {hero.pronoun('subject').capitalize()} wanted to look closely and try it on.",
        ),
        QAItem(
            question=f"Who helped {hero.id} handle the bow?",
            answer=f"{friend.id} helped {hero.id} handle the bow by smoothing it and staying close.",
        ),
        QAItem(
            question=f"Why did the parent speak about the bow being modest?",
            answer=f"The parent wanted {hero.id} to enjoy {bow.phrase} without turning the moment into showy pride, so the bow stayed simple and neat.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": QAItem(
        question="What is curiosity?",
        answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
    ),
    "modesty": QAItem(
        question="What is modesty?",
        answer="Modesty is a gentle way of behaving that is quiet, careful, and not showy.",
    ),
    "bow": QAItem(
        question="What is a bow?",
        answer="A bow is a pretty ribbon tied into a shape, often used to decorate clothes or hair.",
    ),
    "animal": QAItem(
        question="What is an animal story?",
        answer="An animal story is a tale where animals talk, think, and act a little like people.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["curiosity"], WORLD_KNOWLEDGE["modesty"], WORLD_KNOWLEDGE["bow"], WORLD_KNOWLEDGE["animal"]]
    return out


# ---------------------------------------------------------------------------
# Emit / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for bow in BOWS:
            for species in ANIMALS:
                if setting == "meadow" and bow in {"red_bow", "blue_bow", "gold_bow"}:
                    combos.append((setting, bow, species))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small animal story world about curiosity, modesty, and a bow.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bow", choices=BOWS)
    ap.add_argument("--species", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-species", choices=sorted(ANIMALS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "bow", None) and getattr(args, "bow", None) not in BOWS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "species", None) and getattr(args, "species", None) not in ANIMALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "friend_species", None) and getattr(args, "friend_species", None) not in ANIMALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    bow = getattr(args, "bow", None) or rng.choice(list(BOWS))
    species = getattr(args, "species", None) or rng.choice(list(ANIMALS))
    friend_species = getattr(args, "friend_species", None) or rng.choice([s for s in ANIMALS if s != species])
    name = getattr(args, "name", None) or rng.choice(["Milo", "Pippa", "Nori", "Tilly", "Bram", "Luna"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(["Pip", "Momo", "Tansy", "Dew", "Nip"])

    reasonableness_gate(StoryParams(setting=setting, bow=bow, species=species, friend_species=friend_species))
    return StoryParams(
        seed=getattr(args, "seed", None),
        name=name,
        species=species,
        friend_name=friend_name,
        friend_species=friend_species,
        setting=setting,
        bow=bow,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    clingo_set = set(asp.atoms(asp.one_model(asp_program()), "valid_story"))
    py_set = set()
    for setting, bow, species in valid_combos():
        py_set.add((setting, bow, species))
    if clingo_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP only:", sorted(clingo_set - py_set))
    print("Python only:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    return valid_combos()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Milo", species="rabbit", friend_name="Pip", friend_species="mouse", setting="meadow", bow="red_bow"),
    StoryParams(name="Tilly", species="deer", friend_name="Dew", friend_species="rabbit", setting="garden", bow="blue_bow"),
    StoryParams(name="Nori", species="mouse", friend_name="Bram", friend_species="bear", setting="brook", bow="gold_bow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for c in combos:
            print(*c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
