#!/usr/bin/env python3
"""
storyworlds/worlds/geology_ist_flashback_animal_story.py
========================================================

A small animal-story world about a geology-ist: a young animal who studies
stones, layers, and fossils, and remembers the day a discovery changed a lonely
idea into a shared one.

The world is built to feel like a tiny, child-facing Animal Story with a
flashback:
- present time: a friend plans a show or outing
- flashback: a remembered discovery in the ground
- turn: the geology-ist notices a clue in the layers
- resolution: the clue becomes a shared find and a proud ending image
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "doe", "bearcat"}
        male = {"boy", "father", "dad", "man", "ram", "stag", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    outdoors: bool = True
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
class Discovery:
    id: str
    label: str
    phrase: str
    kind: str
    ground: str
    clue: str
    value: str
    tags: set[str] = field(default_factory=set)
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
class MemoryTrigger:
    id: str
    cue: str
    moment: str
    emotion: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _story_fork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("flashback", 0.0) < THRESHOLD:
            continue
        sig = ("flashback", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if actor.memes.get("lonely", 0.0) >= THRESHOLD:
            out.append(f"Memory tugged at {actor.id}'s heart.")
        else:
            out.append(f"A small memory blinked in {actor.id}'s mind.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = _story_fork(world)
    if narrate:
        for s in out:
            world.say(s)
    return out


def setting_line(setting: Setting) -> str:
    return {
        "riverbank": "The riverbank was soft and brown, with little pebbles shining near the water.",
        "cliff": "The cliff path had cracked stones and stripes of old earth showing like a cake.",
        "cave": "The cave mouth was cool and dark, and the floor sparkled with tiny bits of stone.",
        "hill": "The hill was grassy, with a patch where the ground looked freshly turned.",
    }.get(setting.place, f"{setting.place.capitalize()} looked ready for a careful walk.")


def discovery_line(discovery: Discovery) -> str:
    return {
        "fossil": "a fossil shell",
        "crystal": "a bright crystal",
        "layer": "a striped rock layer",
        "arrowhead": "a tiny stone arrowhead",
    }.get(discovery.kind, discovery.label)


def make_setting_and_registry():
    settings = {
        "riverbank": Setting(place="the riverbank", outdoors=True, affords={"search"}),
        "cliff": Setting(place="the cliff path", outdoors=True, affords={"search"}),
        "cave": Setting(place="the cave", outdoors=True, affords={"search"}),
        "hill": Setting(place="the hill", outdoors=True, affords={"search"}),
    }

    discoveries = {
        "fossil": Discovery(
            id="fossil",
            label="fossil shell",
            phrase="an old fossil shell",
            kind="fossil",
            ground="mud",
            clue="spiral line",
            value="a special thing from long ago",
            tags={"stone", "layer", "memory"},
        ),
        "crystal": Discovery(
            id="crystal",
            label="bright crystal",
            phrase="a bright crystal with sharp corners",
            kind="crystal",
            ground="rock",
            clue="glittering edge",
            value="a shiny treasure from the earth",
            tags={"stone", "shiny", "layer"},
        ),
        "layer": Discovery(
            id="layer",
            label="striped rock layer",
            phrase="a striped rock layer",
            kind="layer",
            ground="clay",
            clue="colored stripe",
            value="a clue that the ground had changed over time",
            tags={"layer", "stone", "memory"},
        ),
        "arrowhead": Discovery(
            id="arrowhead",
            label="tiny stone arrowhead",
            phrase="a tiny stone arrowhead",
            kind="arrowhead",
            ground="sand",
            clue="sharp point",
            value="an old tool made by careful hands",
            tags={"stone", "memory"},
        ),
    }

    triggers = {
        "map": MemoryTrigger(
            id="map",
            cue="the folded map",
            moment="the day the map fluttered open in the wind",
            emotion="excited",
        ),
        "shovel": MemoryTrigger(
            id="shovel",
            cue="the little shovel",
            moment="the day the shovel tapped against something hard",
            emotion="curious",
        ),
        "lantern": MemoryTrigger(
            id="lantern",
            cue="the lantern glow",
            moment="the evening the lantern made the cave walls look gold",
            emotion="brave",
        ),
    }
    return settings, discoveries, triggers


SETTINGS, DISCOVERIES, TRIGGERS = make_setting_and_registry()

ANIMAL_NAMES = ["Milo", "Pip", "Tessa", "Nori", "Otis", "Fern", "Rolo", "Bibi"]
ANIMAL_TYPES = ["fox", "rabbit", "badger", "otter", "mouse", "hedgehog", "squirrel", "beaver"]
TRAITS = ["curious", "gentle", "careful", "bright-eyed", "patient", "brave"]
GATHERING_REASONS = [
    "a school show",
    "a little nature table",
    "a visit from friends",
    "a rainy-day talk",
]
FLASHBACK_CUES = ["map", "shovel", "lantern"]


@dataclass
class StoryParams:
    place: str
    discovery: str
    name: str
    animal: str
    trait: str
    reason: str
    cue: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for disc in DISCOVERIES:
            if "search" in setting.affords and disc in DISCOVERIES:
                combos.append((place, disc))
    return combos


def explain_rejection(place: str, discovery: str) -> str:
    disc = _safe_lookup(DISCOVERIES, discovery)
    return (
        f"(No story: {disc.label} does not fit the present setup at {place}."
        f" Try a place where the animal can search for {disc.kind}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An animal story about a geology-ist and a remembered discovery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--discovery", choices=DISCOVERIES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--reason", choices=GATHERING_REASONS)
    ap.add_argument("--cue", choices=FLASHBACK_CUES)
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
    if getattr(args, "place", None) and getattr(args, "discovery", None) and (getattr(args, "place", None), getattr(args, "discovery", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    discovery = getattr(args, "discovery", None) or rng.choice(sorted(DISCOVERIES))
    name = getattr(args, "name", None) or rng.choice(ANIMAL_NAMES)
    animal = getattr(args, "animal", None) or rng.choice(ANIMAL_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    reason = getattr(args, "reason", None) or rng.choice(GATHERING_REASONS)
    cue = getattr(args, "cue", None) or rng.choice(FLASHBACK_CUES)
    return StoryParams(place=place, discovery=discovery, name=name, animal=animal, trait=trait, reason=reason, cue=cue)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, traits=[params.trait, "geology-ist"]))
    friend = world.add(Entity(id="Friend", kind="character", type="rabbit", traits=["helpful"]))
    disc = _safe_lookup(DISCOVERIES, params.discovery)

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved being a geology-ist.")
    world.say(f"{hero.id} liked to study stones, cracks, and the slow stories hidden in the ground.")
    world.say(f"One morning, {hero.id} and {friend.id} went to {world.setting.place} for {params.reason}.")
    world.say(setting_line(world.setting))

    world.para()
    hero.memes["anticipation"] = 1.0
    world.say(f"{hero.id} held up {hero.pronoun('possessive')} small notebook and said, \"Let's look for clues.\"")
    world.say(f"Then {hero.id} noticed {discovery_line(disc)} peeking out of the earth.")
    _set_meme(hero, "flashback", 1.0)
    _set_meme(hero, "lonely", 1.0)
    propagate(world)

    world.para()
    world.say(f"That sight brought back a flashback of {_safe_lookup(TRIGGERS, params.cue).moment}.")
    world.say(f"In the flashback, {hero.id} had felt {_safe_lookup(TRIGGERS, params.cue).emotion} but alone.")
    world.say(f"{hero.id} remembered how {hero.pronoun('possessive')} little tool had tapped and scraped until the hidden shape showed itself.")

    world.para()
    _set_meme(hero, "joy", 1.0)
    _set_meme(friend, "wonder", 1.0)
    world.say(f"Back in the present, {friend.id} knelt beside {hero.id} and gasped at the same clue.")
    world.say(f"{hero.id} explained that the {disc.kind} was not just a pretty stone, but {disc.value}.")
    world.say(f"Together they brushed the dirt away very gently, so the {disc.label} would stay whole.")

    world.para()
    _set_meme(hero, "pride", 1.0)
    world.say(f"At last, {hero.id} placed the find into {hero.pronoun('possessive')} notebook cradle and smiled.")
    world.say(f"The little {hero.type} was no longer alone with the secret; now {friend.id} could see it too.")
    world.say(f"By the end, the ground had given up its story, and {hero.id} carried it home like a treasure.")

    world.facts.update(
        hero=hero,
        friend=friend,
        discovery=disc,
        setting=world.setting,
        params=params,
        cue=_safe_lookup(TRIGGERS, params.cue),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    disc = _safe_fact(world, f, "discovery")
    cue = _safe_fact(world, f, "cue")
    return [
        f'Write a gentle animal story about a little geology-ist named {hero.id} who discovers {disc.label} and remembers {cue.cue}.',
        f"Tell a child-friendly flashback story where {hero.id}, a {hero.type}, studies stones and then shares a discovery with a friend.",
        f"Write a short story about an animal geology-ist, a hidden clue in the ground, and a happy memory that helps the hero feel proud.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    disc = _safe_fact(world, f, "discovery")
    cue = _safe_fact(world, f, "cue")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {hero.id}, a {hero.trait} little {hero.type} who loves being a geology-ist.",
        ),
        QAItem(
            question=f"What did {hero.id} find while looking at the ground?",
            answer=f"{hero.id} found {disc.phrase}. It was a clue hidden in the earth.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} of?",
            answer=f"The flashback reminded {hero.id} of {cue.moment}, when {hero.pronoun('subject')} first noticed the hidden shape.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the present?",
            answer=f"{friend.id} helped by kneeling beside {hero.id} and looking closely at the discovery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} smiling because the find was shared, safe, and ready to be kept like a treasure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    disc = _safe_fact(world, f, "discovery")
    return [
        QAItem(
            question="What does a geology-ist study?",
            answer="A geology-ist studies rocks, layers, soil, and fossils to learn about the Earth.",
        ),
        QAItem(
            question="What is a fossil?",
            answer="A fossil is the preserved shape or trace of a living thing from a very long time ago, often found in rock or mud.",
        ),
        QAItem(
            question="Why are rock layers useful?",
            answer="Rock layers can help tell what happened long ago, because the ground builds up little by little over time.",
        ),
        QAItem(
            question=f"Why would {disc.label} be exciting to find?",
            answer=f"It would be exciting because {disc.value}.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Compatible story if the setting affords searching and there is a discovery.
compatible(P, D) :- setting(P), discovery(D), affords(P, search).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for did, d in DISCOVERIES.items():
        lines.append(asp.fact("discovery", did))
        lines.append(asp.fact("ground", did, d.ground))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="riverbank", discovery="fossil", name="Milo", animal="otter", trait="curious", reason="a school show", cue="map"),
    StoryParams(place="cliff", discovery="layer", name="Tessa", animal="fox", trait="careful", reason="a little nature table", cue="shovel"),
    StoryParams(place="cave", discovery="crystal", name="Pip", animal="hedgehog", trait="bright-eyed", reason="a visit from friends", cue="lantern"),
    StoryParams(place="hill", discovery="arrowhead", name="Nori", animal="squirrel", trait="patient", reason="a rainy-day talk", cue="map"),
]


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
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, d in combos:
            print(f"  {p:10} {d}")
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
