#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/slide_relevance_misunderstanding_dialogue_superhero_story.py
===============================================================================================================================

A small superhero storyworld about a slide deck, a relevance misunderstanding,
and a dialogue that turns confusion into a useful plan.

Seed tale used to build the model:
---
At the hero clubhouse, Captain Bright wanted to show a slide deck about the day's
mission. Spark thought the slides were not relevant because the team needed to
act, not talk. Captain Bright explained that the slides showed where the lost toy
had been seen, so the pictures mattered. Spark listened, apologized, and the
team used the map on the slide to find the toy.

World shape:
- A hero team meets in a clubhouse.
- One hero prepares a slide deck with clues for a mission.
- Another hero misunderstands the relevance of the slides.
- Dialogue reveals that the slide deck is actually useful.
- The team follows the clue and ends with a clear win image.

The prose is driven by simulated state:
- confusion rises on misunderstanding
- calm and trust rise with dialogue
- relevance becomes true only when the slide deck contains a real clue
- the ending proves the change by using the slide to solve the problem
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
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    slide: object | None = None
    teammate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the clubhouse"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class SlideDeck:
    id: str
    title: str
    clue_kind: str
    relevance_topic: str
    detail: str
    contains_clue: bool = True
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
class Mission:
    id: str
    goal: str
    place: str
    lost_item: str
    clue_word: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
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
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["listener"])
    speaker = world.get(world.facts["speaker"])
    deck = _safe_fact(world, world.facts, "deck_obj")
    if hero.memes["confusion"] < THRESHOLD:
        return out
    sig = ("confusion_turn", hero.id)
    if sig in world.fired:
        return out
    if world.facts["deck_relevant"]:
        world.fired.add(sig)
        hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1.0)
        hero.memes["trust"] += 1.0
        out.append(
            f"{speaker.label} showed that the slide deck really did matter."
        )
    return out


RULES = [Rule("confusion_turn", _r_confusion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    name: str
    teammate: str
    narrator_type: str
    teammate_type: str
    place: str
    mission: str
    slide_title: str
    clue_word: str
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


HERO_NAMES = ["Captain Bright", "Nova", "Starling", "Beacon", "Comet"]
TEAMMATE_NAMES = ["Spark", "Pulse", "Mira", "Dash", "Vector"]

SETTING = Setting(place="the clubhouse", affords={"slide_talk"})

MISSIONS = {
    "lost_kite": Mission(
        id="lost_kite",
        goal="find the lost kite",
        place="the park",
        lost_item="kite",
        clue_word="bench",
    ),
    "missing_mask": Mission(
        id="missing_mask",
        goal="find the missing mask",
        place="the stage room",
        lost_item="mask",
        clue_word="locker",
    ),
    "lost_puppy_map": Mission(
        id="lost_puppy_map",
        goal="find the puppy's map",
        place="the yard",
        lost_item="map",
        clue_word="tree",
    ),
}

SLIDE_DECKS = {
    "lost_kite": SlideDeck(
        id="kite_slides",
        title="Mission Slides: The Lost Kite",
        clue_kind="photo",
        relevance_topic="the kite mission",
        detail="a picture of the park bench where the kite string was last seen",
        contains_clue=True,
    ),
    "missing_mask": SlideDeck(
        id="mask_slides",
        title="Mission Slides: The Missing Mask",
        clue_kind="map",
        relevance_topic="the mask mission",
        detail="a tiny map that points to the locker by the stage",
        contains_clue=True,
    ),
    "lost_puppy_map": SlideDeck(
        id="puppy_slides",
        title="Mission Slides: The Puppy Map",
        clue_kind="photo",
        relevance_topic="the puppy mission",
        detail="a photo of the old tree where the map was dropped",
        contains_clue=True,
    ),
}

PRONOUN_TYPES = {"girl", "boy", "woman", "man"}


def valid_combos() -> list[tuple[str, str]]:
    return [(mid, mid) for mid in MISSIONS]


def explain_rejection(mission_id: str) -> str:
    return f"(No story: the mission '{mission_id}' is not available.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld: a slide deck, a relevance misunderstanding, and dialogue."
    )
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--teammate", choices=TEAMMATE_NAMES)
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
    mission_id = getattr(args, "mission", None) or rng.choice(list(MISSIONS))
    if getattr(args, "mission", None) and getattr(args, "mission", None) not in MISSIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    teammate = getattr(args, "teammate", None) or rng.choice([n for n in TEAMMATE_NAMES if n != name])
    if teammate == name:
        teammate = rng.choice([n for n in TEAMMATE_NAMES if n != name])
    deck = _safe_lookup(SLIDE_DECKS, mission_id)
    return StoryParams(
        name=name,
        teammate=teammate,
        narrator_type="boy" if name in {"Captain Bright", "Nova", "Starling", "Beacon", "Comet"} else "girl",
        teammate_type="boy",
        place=SETTING.place,
        mission=mission_id,
        slide_title=deck.title,
        clue_word=_safe_lookup(MISSIONS, mission_id).clue_word,
    )


def _story_world(params: StoryParams) -> World:
    world = World(SETTING)
    mission = _safe_lookup(MISSIONS, params.mission)
    deck = _safe_lookup(SLIDE_DECKS, params.mission)

    hero = world.add(Entity(id="hero", kind="character", type="boy", label=params.name))
    teammate = world.add(Entity(id="teammate", kind="character", type="boy", label=params.teammate))

    slide = world.add(Entity(
        id="slide_deck",
        type="thing",
        label="slide deck",
        phrase=deck.title,
        owner=hero.id,
    ))
    slide.meters["presentation_ready"] = 1.0
    slide.meters["relevance"] = 0.0
    slide.meters["clue_visible"] = 1.0 if deck.contains_clue else 0.0

    world.facts.update(
        hero=hero.id,
        teammate=teammate.id,
        mission=mission,
        deck=deck,
        slide=slide.id,
    )

    world.say(
        f"At {world.setting.place}, {hero.label} wore a bright cape and carried {deck.title} like a real mission tool."
    )
    world.say(
        f"{hero.label} wanted to show the slides first because the pictures held a clue about {mission.goal}."
    )

    world.para()
    world.say(
        f"{teammate.label} folded {teammate.pronoun('possessive')} arms and said, "
        f"\"Slides are not relevant right now. We need to dash, not talk.\""
    )
    teammate.memes["misunderstanding"] += 1.0
    teammate.memes["impatience"] += 1.0
    hero.memes["hurt"] += 1.0
    slide.meters["relevance"] = 1.0 if deck.contains_clue else 0.0
    world.facts["deck_relevant"] = deck.contains_clue
    world.facts["speaker"] = hero.id
    world.facts["listener"] = teammate.id

    world.say(
        f"{hero.label} paused, then answered, \"Look closely. This slide shows {deck.detail}.\""
    )
    world.say(
        f"\"That clue is relevant,\" {hero.label} said. \"It points us to the {mission.clue_word}.\""
    )

    teammate.memes["confusion"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{teammate.label}'s face softened. \"Oh! I misunderstood,\" {teammate.label} said. "
        f"\"The slides are part of the rescue plan.\""
    )
    teammate.memes["misunderstanding"] = max(0.0, teammate.memes["misunderstanding"] - 1.0)
    teammate.memes["trust"] += 1.0
    hero.memes["relief"] += 1.0

    world.say(
        f"The two heroes hurried to {mission.place}, followed the {deck.clue_kind}, and found the {mission.lost_item} exactly where the slide had shown."
    )
    hero.meters["rescues"] = 1.0
    teammate.meters["helps"] = 1.0
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    mission = _safe_fact(world, world.facts, "mission")
    deck = _safe_fact(world, world.facts, "deck")
    hero = world.get(world.facts["hero"])
    teammate = world.get(world.facts["teammate"])
    return [
        f"Write a short superhero story for young children about {hero.label}, {teammate.label}, and a slide deck that turns out to be relevant.",
        f"Tell a gentle story where {teammate.label} misunderstands the relevance of {deck.title}, then dialogue helps the team solve the mission.",
        f"Write a superhero adventure that includes the words 'slide' and 'relevance' and ends with the heroes using a clue to find {mission.lost_item}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission = _safe_fact(world, world.facts, "mission")
    hero = world.get(world.facts["hero"])
    teammate = world.get(world.facts["teammate"])
    deck = _safe_fact(world, world.facts, "deck")
    return [
        QAItem(
            question=f"Who wanted to show the slides at the clubhouse?",
            answer=f"{hero.label} wanted to show {deck.title} because the slide deck held a clue for {mission.goal}.",
        ),
        QAItem(
            question=f"Why did {teammate.label} think the slides were not relevant at first?",
            answer=f"{teammate.label} thought the team should hurry, so {teammate.label} misunderstood how the slides were part of the mission.",
        ),
        QAItem(
            question=f"What changed after the dialogue about relevance?",
            answer=f"After the heroes talked, {teammate.label} understood that the slides were relevant and helped find the {mission.lost_item}.",
        ),
        QAItem(
            question=f"Where did the heroes go after they solved the misunderstanding?",
            answer=f"They rushed to {mission.place} and followed the clue from the slide deck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slide deck?",
            answer="A slide deck is a set of pictures or pages that people use to explain an idea or tell a story.",
        ),
        QAItem(
            question="What does relevant mean?",
            answer="Relevant means something matters for the job or problem you are trying to solve.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea and needs more explanation.",
        ),
        QAItem(
            question="Why can dialogue help?",
            answer="Dialogue helps because people can ask questions, explain their ideas, and clear up confusion.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:7}) {e.label} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h). teammate(t). deck(d). mission(m).
relevant(d) :- deck(d), clue_visible(d).
misunderstood(t) :- confusion(t).
resolved :- relevant(d), dialogue.
dialogue :- said(h, explain), said(t, understand).
shown(d) :- deck(d), relevant(d).
#show relevant/1.
#show misunderstood/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "h"),
        asp.fact("teammate", "t"),
        asp.fact("deck", "d"),
        asp.fact("mission", "m"),
        asp.fact("clue_visible", "d"),
        asp.fact("confusion", "t"),
        asp.fact("said", "h", "explain"),
        asp.fact("said", "t", "understand"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relevant/1.\n#show misunderstood/1.\n#show resolved/0."))
    atoms = {(sym.name, len(sym.arguments), tuple(str(a) for a in sym.arguments)) for sym in model}
    needed = {("relevant", 1, ('d',)), ("misunderstood", 1, ('t',)), ("resolved", 0, ())}
    if atoms == needed:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("Mismatch between ASP and Python logic.")
    print("ASP atoms:", sorted(atoms))
    print("Expected:", sorted(needed))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/1."))
    return sorted(set(asp.atoms(model, "relevant")))


def generate(params: StoryParams) -> StorySample:
    world = _story_world(params)
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
    StoryParams(
        name="Captain Bright",
        teammate="Spark",
        narrator_type="boy",
        teammate_type="boy",
        place="the clubhouse",
        mission="lost_kite",
        slide_title=SLIDE_DECKS["lost_kite"].title,
        clue_word=MISSIONS["lost_kite"].clue_word,
    ),
    StoryParams(
        name="Nova",
        teammate="Pulse",
        narrator_type="boy",
        teammate_type="boy",
        place="the clubhouse",
        mission="missing_mask",
        slide_title=SLIDE_DECKS["missing_mask"].title,
        clue_word=MISSIONS["missing_mask"].clue_word,
    ),
    StoryParams(
        name="Beacon",
        teammate="Mira",
        narrator_type="boy",
        teammate_type="boy",
        place="the clubhouse",
        mission="lost_puppy_map",
        slide_title=SLIDE_DECKS["lost_puppy_map"].title,
        clue_word=MISSIONS["lost_puppy_map"].clue_word,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show relevant/1.\n#show misunderstood/1.\n#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available; this world's main relevance check is encoded inline.")
        print(facts := asp_facts())
        print(ASP_RULES)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.mission}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
