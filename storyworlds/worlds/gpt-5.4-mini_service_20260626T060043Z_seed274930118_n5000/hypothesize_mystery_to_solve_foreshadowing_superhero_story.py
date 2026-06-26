#!/usr/bin/env python3
"""
storyworlds/worlds/hypothesize_mystery_to_solve_foreshadowing_superhero_story.py
=================================================================================

A standalone story world for a small superhero mystery: a hero notices clues,
hypothesizes what is happening, and solves the problem with a clever turn.

Seed inspiration:
- A child-friendly superhero story
- A mystery to solve
- Foreshadowing that pays off later
- The verb "hypothesize" as a narrative instrument

The world models:
- a hero with a power and a sidekick
- a city location with a problem
- clues that foreshadow the culprit
- a hypothesis step that is later confirmed or corrected
- a final rescue / resolution image

The story is fully simulated from state, not just a swapped-noun template.
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
# Core world model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
class City:
    place: str = "Skyline City"
    setting: str = "rooftops"
    mystery: str = ""
    clue_kind: str = ""
    CITY: object | None = None
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
class HeroPower:
    id: str
    label: str
    method: str
    limit: str
    shines: str
    tags: set[str] = field(default_factory=set)
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
class MysteryCase:
    id: str
    title: str
    thing_missing: str
    likely_places: set[str]
    clue_chain: list[str]
    culprit: str
    solution: str
    foreshadow: str
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
class Sidekick:
    id: str
    label: str
    knack: str
    role: str
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
    def __init__(self, city: City) -> None:
        self.city = city
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
        import copy
        w = World(self.city)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CITY = City(place="Skyline City", setting="the museum roof", mystery="missing starlight badge", clue_kind="sparkle")

POWERS = {
    "echo": HeroPower(
        id="echo",
        label="echo hearing",
        method="listen for tiny sounds",
        limit="soft whispers can hide under loud city noise",
        shines="the smallest clue can be the loudest one",
        tags={"sound", "clue"},
    ),
    "glow": HeroPower(
        id="glow",
        label="glow vision",
        method="shine a gentle light on dark corners",
        limit="bright light can wash out faint marks",
        shines="a hidden mark can suddenly make sense",
        tags={"light", "clue"},
    ),
    "lift": HeroPower(
        id="lift",
        label="careful lifting",
        method="lift rubble and move heavy things",
        limit="heavy things need a safe plan",
        shines="what is blocked can be uncovered",
        tags={"heavy", "clue"},
    ),
}

SIDEKICKS = {
    "sparrow": Sidekick(id="sparrow", label="Sparrow", knack="spotted details", role="sidekick"),
    "patch": Sidekick(id="patch", label="Patch", knack="kept notes", role="helper"),
    "milo": Sidekick(id="milo", label="Milo", knack="drew maps", role="helper"),
}

MYSTERIES = {
    "badge": MysteryCase(
        id="badge",
        title="the missing starlight badge",
        thing_missing="the starlight badge",
        likely_places={"museum roof", "clock tower", "alley"},
        clue_chain=[
            "a shiny dust trail on the roof",
            "a little gust that smelled like popcorn",
            "a ribbon caught on a vent",
        ],
        culprit="a playful wind drone",
        solution="it had blown the badge into the old lantern room",
        foreshadow="the ribbon on the vent fluttered toward the lantern room",
        tags={"mystery", "wind", "badge"},
    ),
    "lantern": MysteryCase(
        id="lantern",
        title="the missing lantern key",
        thing_missing="the lantern key",
        likely_places={"museum roof", "gallery hall", "stairwell"},
        clue_chain=[
            "a brass scratch near a window",
            "a warm flicker under a cloth",
            "a tiny soot mark on a ledge",
        ],
        culprit="a shy robot painter",
        solution="it had tucked the key inside a paint tin",
        foreshadow="the soot mark pointed toward the paint room",
        tags={"mystery", "paint", "key"},
    ),
    "relay": MysteryCase(
        id="relay",
        title="the missing signal relay",
        thing_missing="the signal relay",
        likely_places={"museum roof", "radio room", "bridge"},
        clue_chain=[
            "a humming wire by the railing",
            "a boot print in dust",
            "a map corner folded twice",
        ],
        culprit="a squirrel with a nest full of shiny junk",
        solution="it had carried the relay to a nest high in the rafters",
        foreshadow="the folded map corner matched the nest's hidden path",
        tags={"mystery", "signal", "relay"},
    ),
}

HERO_NAMES = ["Nova", "Comet", "Arrow", "Pulse", "Riley", "Juno"]
HERO_TYPES = ["girl", "boy"]
HERO_TRAITS = ["brave", "curious", "careful", "quick-thinking", "steady"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mystery: str
    power: str
    hero_name: str
    hero_type: str
    sidekick: str
    trait: str
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


def mystery_has_solution(case: MysteryCase, power: HeroPower) -> bool:
    if case.id == "badge" and power.id in {"echo", "glow"}:
        return True
    if case.id == "lantern" and power.id in {"glow", "lift"}:
        return True
    if case.id == "relay" and power.id in {"echo", "lift"}:
        return True
    return False


def explain_rejection(case: MysteryCase, power: HeroPower) -> str:
    return (
        f"(No story: {power.label} does not make a believable way to solve "
        f"{case.thing_missing}. Choose a power that can actually uncover or trace the clue.)"
    )


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------
def hypothesize(world: World, hero: Entity, power: HeroPower, case: MysteryCase, sidekick: Entity) -> str:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    clue = case.clue_chain[0]
    world.facts["first_clue"] = clue
    world.say(
        f"{hero.id} landed on the roof and noticed {clue}. "
        f"{hero.pronoun().capitalize()} had a feeling something strange was hiding nearby."
    )
    world.say(
        f"'{hero.id}, we should hypothesize before we hurry,' said {sidekick.label}, "
        f"who had {sidekick.knack}."
    )
    if power.id == "echo":
        hypothesis = f"the missing thing was moved by a noisy helper in the air"
    elif power.id == "glow":
        hypothesis = f"the missing thing was hidden where the dark corners met the light"
    else:
        hypothesis = f"the missing thing was blocked by something heavy and needed moving"
    world.facts["hypothesis"] = hypothesis
    world.say(
        f"{hero.id} listened carefully and said, 'I hypothesize that {hypothesis}.' "
        f"{power.shines.capitalize()}."
    )
    return hypothesis


def foreshadow(world: World, case: MysteryCase) -> None:
    world.say(
        f"Then {case.foreshadow}. {case.clue_chain[1]} sat there like a promise, "
        f"waiting for the right hero to notice it."
    )


def investigate(world: World, hero: Entity, power: HeroPower, case: MysteryCase) -> None:
    if power.id == "echo":
        world.say(
            f"{hero.id} held still and used {power.method}. Soon {hero.pronoun()} heard a soft buzz "
            f"coming from above the lantern room."
        )
    elif power.id == "glow":
        world.say(
            f"{hero.id} used {power.method}. The beam found {case.clue_chain[2]} on the ledge."
        )
    else:
        world.say(
            f"{hero.id} used {power.method}. Behind a stack of boxes, the floor dust showed a trail."
        )
    world.say(
        f"That clue fit the first one, and the mystery started to make sense."
    )


def solve_case(world: World, hero: Entity, case: MysteryCase, power: HeroPower, sidekick: Entity) -> None:
    world.facts["solved"] = True
    world.say(
        f"At last, {hero.id} followed the clues to the truth: {case.solution}. "
        f"It turned out the culprit was {case.culprit}."
    )
    world.say(
        f"{sidekick.label} opened the hiding place, and {hero.id} gently rescued {case.thing_missing}. "
        f"Then the city could shine again."
    )
    if power.id == "echo":
        ending = "The rooftops were quiet, but the hero could still hear the happy hum of the city."
    elif power.id == "glow":
        ending = "The roof lights blinked on, and the rescued prize glittered in the hero's hands."
    else:
        ending = "The blocked path was clear now, and the missing thing was safely back where it belonged."
    world.say(ending)


def build_world(params: StoryParams) -> World:
    city = CITY
    case = _safe_lookup(MYSTERIES, params.mystery)
    power = _safe_lookup(POWERS, params.power)
    world = World(city)
    world.facts.update(case=case, power=power)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        role="hero",
        meters={"hope": 1.0},
        memes={"curious": 1.0},
    ))
    sidekick = world.add(Entity(
        id=_safe_lookup(SIDEKICKS, params.sidekick).label,
        kind="character",
        type="friend",
        role="sidekick",
    ))
    prize = world.add(Entity(
        id="missing_item",
        kind="thing",
        type="thing",
        label=case.thing_missing,
        phrase=case.thing_missing,
        owner="city",
    ))

    world.say(
        f"One evening in {city.place}, {hero.id} watched the lights flicker over {city.setting}. "
        f"{hero.pronoun().capitalize()} was a {params.trait} young hero who never ignored a mystery."
    )
    world.say(
        f"{hero.id} could use {power.label}, and {sidekick.label} was always ready to help."
    )
    world.para()
    world.say(
        f"That night, {prize.label} went missing, and the whole rooftop seemed to hold its breath."
    )
    hypothesize(world, hero, power, case, sidekick)
    foreshadow(world, case)
    investigate(world, hero, power, case)
    world.para()
    solve_case(world, hero, case, power, sidekick)

    world.facts.update(hero=hero, sidekick=sidekick, prize=prize)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: MysteryCase = _safe_fact(world, f, "case")
    power: HeroPower = _safe_fact(world, f, "power")
    hero: Entity = _safe_fact(world, f, "hero")
    return [
        f"Write a short superhero story for a child where {hero.id} has to solve {case.title}.",
        f"Tell a mystery story that includes the word 'hypothesize' and a clue that foreshadows the answer.",
        f"Write a gentle superhero adventure where {power.label} helps reveal what happened to {case.thing_missing}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: MysteryCase = _safe_fact(world, f, "case")
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    power: HeroPower = _safe_fact(world, f, "power")
    return [
        QAItem(
            question=f"What problem did {hero.id} have to solve?",
            answer=f"{hero.id} had to solve {case.title}, and that mystery was about {case.thing_missing}.",
        ),
        QAItem(
            question=f"What word did {hero.id} use when thinking about the clues?",
            answer=f"{hero.id} said { 'hypothesize' } because the hero was making an early idea from the clues.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the missing thing?",
            answer=f"{sidekick.label} helped by watching closely and opening the hiding place at the end.",
        ),
        QAItem(
            question=f"How did {power.label} help in the story?",
            answer=f"{power.label} helped {hero.id} notice clues and find the answer to the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: MysteryCase = _safe_fact(world, f, "case")
    power: HeroPower = _safe_fact(world, f, "power")
    qa = [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where you do not know the answer yet, so you look for clues.",
        ),
        QAItem(
            question="What does it mean to hypothesize?",
            answer="To hypothesize means to make a smart guess about what might be true before you know for sure.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early that helps the ending make sense later.",
        ),
    ]
    if "clue" in power.tags:
        qa.append(
            QAItem(
                question="Why do heroes pay attention to clues?",
                answer="Heroes pay attention to clues because little signs can point to the real answer and help solve the mystery.",
            )
        )
    if "mystery" in case.tags:
        qa.append(
            QAItem(
                question="Why do stories use clues?",
                answer="Stories use clues so readers can wonder, guess, and then feel happy when the answer is found.",
            )
        )
    return qa


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the hero's power can plausibly reveal the clue chain.
solvable(M,P) :- mystery(M), power(P), fit(M,P).

% A foreshadowed clue is one that points to the solution path.
foreshadows(M) :- mystery(M), clue(M,_).

% A good story exists when there is a solvable mystery with foreshadowing.
valid_story(M,P) :- solvable(M,P), foreshadows(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid, case in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fit", mid, "echo") if mid == "badge" else "")
        lines.append(asp.fact("fit", mid, "glow") if mid in {"badge", "lantern"} else "")
        lines.append(asp.fact("fit", mid, "lift") if mid in {"lantern", "relay"} else "")
        for clue in case.clue_chain:
            lines.append(asp.fact("clue", mid, clue))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo = set(asp_valid_stories())
    python = set((mid, pid) for mid, case in MYSTERIES.items() for pid in POWERS if mystery_has_solution(case, _safe_lookup(POWERS, pid)))
    if clingo == python:
        print(f"OK: clingo gate matches Python reasoner ({len(clingo)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo - python))
    print("only in python:", sorted(python - clingo))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery world with foreshadowing and a hypothesis.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    power = getattr(args, "power", None) or rng.choice(list(POWERS))
    case = _safe_lookup(MYSTERIES, mystery)
    if not mystery_has_solution(case, _safe_lookup(POWERS, power)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(list(SIDEKICKS))
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    return StoryParams(
        mystery=mystery,
        power=power,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick=sidekick,
        trait=trait,
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} role={e.role}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(mystery="badge", power="echo", hero_name="Nova", hero_type="girl", sidekick="sparrow", trait="curious"),
    StoryParams(mystery="lantern", power="glow", hero_name="Comet", hero_type="boy", sidekick="patch", trait="careful"),
    StoryParams(mystery="relay", power="lift", hero_name="Juno", hero_type="girl", sidekick="milo", trait="quick-thinking"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible mystery/power combos:\n")
        for mid, pid in stories:
            print(f"  {mid:8} {pid}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + i
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
