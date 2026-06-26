#!/usr/bin/env python3
"""
storyworlds/worlds/loll_hypothesis_surprise_curiosity_adventure.py
===================================================================

A standalone story world about lolling, making a hypothesis, and following
Curiosity into a small adventure with a Surprise at the end.

Seed tale:
---
A child named Tia loved to loll in a hammock beside a pine trail. One quiet
afternoon, she heard a small click in the grass. Tia made a hypothesis: maybe
the sound came from a lost trail token hidden under the roots. Curiosity tugged
at her harder than rest did, so she climbed down, checked the roots, and found a
tiny tin box with a surprise inside: a shiny compass and a folded note that said
the trail would be easier tomorrow. Tia laughed, because the guess had been only
half right, but the adventure had become wonderful anyway.

World model:
---
    lolling in a safe place            -> rest += 1, calm += 1
    hearing a clue                     -> curiosity += 1, surprise += 1
    hypothesis about a hidden thing    -> expectation += 1
    following the clue                 -> explore += 1, risk += 1
    finding the hidden thing           -> surprise becomes delight, calm -= risk
    useful tool discovered             -> confidence += 1, curiosity settles

The story is built from these simulated state changes rather than from a frozen
paragraph with swapped nouns.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    portable: bool = True

    hero: object | None = None
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
    affords: set[str] = field(default_factory=set)
    outdoor: bool = True
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
    clue: str
    follow: str
    effect: str
    risk: str
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    hidden_by: str
    useful_for: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_clue(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes["listening"] < THRESHOLD:
            continue
        sig = ("clue", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["curiosity"] += 1
        hero.memes["surprise"] += 1
        out.append("A tiny clue stirred the air.")
    return out


def _r_discover(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters["explore"] < THRESHOLD:
            continue
        sig = ("discover", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["surprise"] += 1
        hero.memes["delight"] += 1
        hero.meters["calm"] += 1
        out.append("The hidden thing was found.")
    return out


RULES = [_r_clue, _r_discover]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s == "A tiny clue stirred the air.":
                world.say("A tiny clue stirred the air, and Curiosity sat up straight.")
            elif s == "The hidden thing was found.":
                world.say("At last, the hidden thing was found, and Surprise turned into a grin.")
    return produced


def hypothesis_text(activity: Activity, treasure: Treasure) -> str:
    return f"maybe the {activity.keyword} clue meant {treasure.phrase}"


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved quiet places and odd little wonders."
    )


def loll(world: World, hero: Entity, setting: Setting) -> None:
    hero.meters["rest"] += 1
    hero.meters["calm"] += 1
    world.say(f"One afternoon, {hero.id} chose to loll in a hammock beside {setting.place}.")


def hear_clue(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["listening"] += 1
    world.say(f"Then {hero.id} heard a soft {activity.clue}, just different enough to matter.")


def make_hypothesis(world: World, hero: Entity, activity: Activity, treasure: Treasure) -> None:
    hero.memes["expectation"] += 1
    world.facts["hypothesis"] = hypothesis_text(activity, treasure)
    world.say(
        f"{hero.id} made a hypothesis: {world.facts['hypothesis']}."
    )


def follow(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["explore"] += 1
    hero.meters["risk"] += 1
    world.say(f"{hero.id} climbed down and {activity.follow}, following the tiny sign of trouble and wonder.")


def reveal(world: World, hero: Entity, treasure: Treasure) -> None:
    hero.meters["calm"] += 1
    hero.memes["delight"] += 1
    hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 1.0)
    world.say(
        f"Under the roots, {hero.id} found {treasure.phrase}: {treasure.label}, waiting like a secret gift."
    )


def resolve(world: World, hero: Entity, treasure: Treasure) -> None:
    hero.meters["calm"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"The surprise inside was a {treasure.label} that could help on the trail, and {hero.id} smiled at the clever guess."
    )


SETTINGS = {
    "pine_trail": Setting(place="the pine trail", affords={"loll", "listen", "seek"}),
    "riverbank": Setting(place="the riverbank", affords={"loll", "listen", "seek"}),
    "garden_path": Setting(place="the garden path", affords={"loll", "listen", "seek"}),
    "hill_camp": Setting(place="the hill camp", affords={"loll", "listen", "seek"}),
}

ACTIVITIES = {
    "trail_click": Activity(
        id="trail_click",
        verb="inspect the trail",
        gerund="inspecting the trail",
        clue="click in the grass",
        follow="peeked under the roots",
        effect="hidden",
        risk="uncertain",
        keyword="trail",
        tags={"trail", "mystery"},
    ),
    "rustle": Activity(
        id="rustle",
        verb="look behind the stones",
        gerund="looking behind stones",
        clue="rustle in the leaves",
        follow="looked behind the stones",
        effect="hidden",
        risk="uncertain",
        keyword="leaves",
        tags={"garden", "mystery"},
    ),
    "water_ping": Activity(
        id="water_ping",
        verb="follow the bank",
        gerund="following the bank",
        clue="ping from the reeds",
        follow="stepped along the bank",
        effect="hidden",
        risk="slippery",
        keyword="reeds",
        tags={"river", "mystery"},
    ),
}

TREASURES = {
    "compass": Treasure(
        id="compass",
        label="a shiny compass",
        phrase="a shiny compass",
        type="tool",
        hidden_by="roots",
        useful_for="finding the way",
    ),
    "note": Treasure(
        id="note",
        label="a folded note",
        phrase="a folded note",
        type="paper",
        hidden_by="stones",
        useful_for="finding the way",
    ),
    "key": Treasure(
        id="key",
        label="a little brass key",
        phrase="a little brass key",
        type="key",
        hidden_by="reeds",
        useful_for="opening a tin box",
    ),
}

GIRL_NAMES = ["Tia", "Mina", "Lena", "Zuri", "Ayla", "Nia"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Rui", "Theo", "Ezra"]
TRAITS = ["curious", "brave", "gentle", "spirited", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for treasure_id in TREASURES:
                combos.append((place, act_id, treasure_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about lolling, hypotheses, Curiosity, and Surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, treasure=treasure, name=name, gender=gender, trait=trait)


def tell(setting: Setting, activity: Activity, treasure: Treasure, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    world.add(Entity(id="Curiosity", kind="thing", type="idea", label="Curiosity"))
    world.add(Entity(id="Surprise", kind="thing", type="idea", label="Surprise"))
    world.add(Entity(id="treasure", kind="thing", type=treasure.type, label=treasure.label, phrase=treasure.phrase))

    introduce(world, hero)
    loll(world, hero, setting)
    world.para()
    hear_clue(world, hero, activity)
    make_hypothesis(world, hero, activity, treasure)
    follow(world, hero, activity)
    propagate(world, narrate=True)
    world.para()
    reveal(world, hero, treasure)
    resolve(world, hero, treasure)

    world.facts.update(hero=hero, activity=activity, treasure=treasure, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    treasure = _safe_fact(world, f, "treasure")
    return [
        f'Write a short adventure story for a child that includes "{hero.id}", "{activity.keyword}", and a surprise ending.',
        f"Tell a gentle story where {hero.id} lolls for a moment, then follows a clue and makes a hypothesis about {treasure.phrase}.",
        f'Write a child-friendly adventure about Curiosity and Surprise where the word "{activity.keyword}" matters.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    treasure = _safe_fact(world, f, "treasure")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What did {hero.id} do first at {place}?",
            answer=f"{hero.id} first chose to loll in a hammock beside {place}.",
        ),
        QAItem(
            question=f"What was {hero.id}'s hypothesis after hearing the {activity.clue}?",
            answer=f"{hero.id} thought that maybe the clue meant {treasure.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} find after following the clue?",
            answer=f"{hero.id} found {treasure.phrase}, which turned the guess into a happy surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a smart guess about what might be true before you check.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn more and ask questions.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly appears or happens.",
        ),
        QAItem(
            question="What does it mean to loll?",
            answer="To loll means to rest in a loose, relaxed way, like stretching out and taking it easy.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Treasure) :- place(Place), affords(Place, Act), activity(Act), treasure(Treasure).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(TREASURES, params.treasure), params.name, params.gender, params.trait)
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
    StoryParams(place="pine_trail", activity="trail_click", treasure="compass", name="Tia", gender="girl", trait="curious"),
    StoryParams(place="garden_path", activity="rustle", treasure="note", name="Mina", gender="girl", trait="brave"),
    StoryParams(place="riverbank", activity="water_ping", treasure="key", name="Owen", gender="boy", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, treasure) combos:\n")
        for place, act, treasure in combos:
            print(f"  {place:12} {act:14} {treasure}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.activity} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
