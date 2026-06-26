#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Pirate Tale about an angelic maestro,
an inner monologue, and a misunderstanding that gets cleared up with music.

Seed premise:
- A pirate crew on a small ship
- A shy pirate wants to be accustom to the captain's music time
- An angelic maestro helps teach the right way
- A misunderstanding happens because the hero thinks the song is a scolding
- Inner monologue reveals the hero's worry, then the turn resolves it

The world is intentionally small and constraint-checked:
- Simulated meters: sound, courage, trust, chaos, order, calm
- Simulated memes: worry, pride, relief, wonder, misunderstanding
- State drives prose; the ending proves what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    maestro: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "captain", "singer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "pirate", "maestro"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
class Ship:
    name: str
    place: str = "the deck"
    afford_music: bool = True
    afford_talk: bool = True
    afford_practice: bool = True
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
class Melody:
    id: str
    label: str
    kind: str
    effect: str
    has_beat: bool
    requires_listening: bool
    keyword: str = "music"
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


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    tied_to_music: bool = False
    can_be_misread: bool = False
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
    ship: str
    melody: str
    prop: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _py_name(entity: Entity) -> str:
    return entity.label or entity.id


def _setting_line(world: World) -> str:
    return f"The ship {world.ship.name} rocked on the blue sea, and the deck smelled like salt and rope."


def _hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a {hero.traits[0]} little pirate who listened hard and tried to do things right."


def _melody_line(melody: Melody) -> str:
    return {
        "anthem": "The tune was bold and round, like a marching stomp with a bright horn on top.",
        "lullaby": "The tune was soft and smooth, like a wave tucking little lights to sleep.",
        "drumroll": "The tune beat quick and neat, like fingers tapping on a barrel lid.",
    }.get(melody.id, "The tune sounded lively and new.")


def _prop_line(prop: Prop) -> str:
    return {
        "sheet": "A folded music sheet sat near the mast, covered with neat notes.",
        "whistle": "A small silver whistle hung from a cord, shiny as moonlight.",
        "bell": "A brass bell waited by the rail, ready to call the crew together.",
    }.get(prop.id, f"A {prop.label} rested near the captain's feet.")


def _think(hero: Entity, text: str) -> str:
    return f"{hero.id} thought, “{text}”"


def _inner_monologue(hero: Entity, melody: Melody, prop: Prop) -> str:
    return (
        _think(hero, f"Was that song meant for me? Maybe I messed up the {prop.label}.") + " "
        + _think(hero, "I want to be accustom to ship music time, but I don't want to be shooed away.")
    )


def _predict_misunderstanding(world: World, hero: Entity, melody: Melody, prop: Prop) -> bool:
    sim = world.copy()
    sim.facts["heard"] = True
    sim.facts["misread"] = prop.can_be_misread and melody.requires_listening
    return bool(sim.facts["misread"])


def _start_song(world: World, hero: Entity, maestro: Entity, melody: Melody, prop: Prop) -> None:
    hero.meters["courage"] += 1
    maestro.meters["order"] += 1
    world.say(f"At dusk, {maestro.id} lifted a hand and began the {melody.label}.")
    world.say(_melody_line(melody))
    world.say(_prop_line(prop))


def _misunderstanding(world: World, hero: Entity, maestro: Entity, melody: Melody, prop: Prop) -> None:
    hero.memes["worry"] += 1
    hero.memes["misunderstanding"] += 1
    hero.meters["chaos"] += 1
    world.say(_inner_monologue(hero, melody, prop))
    world.say(
        f"{hero.id} heard the tune and thought {maestro.id} was frowning about the {prop.label}, "
        f"so {hero.pronoun('subject')} took a small step back."
    )


def _clear_up(world: World, hero: Entity, maestro: Entity, melody: Melody) -> None:
    hero.memes["worry"] = 0
    hero.memes["misunderstanding"] = 0
    hero.memes["relief"] += 1
    hero.meters["courage"] += 1
    hero.meters["calm"] += 1
    maestro.meters["trust"] += 1
    world.say(
        f"Then {maestro.id} smiled, tapped the beat again, and showed {hero.id} the easy pattern with a nod."
    )
    world.say(
        f"{hero.id} copied the rhythm, and the worry melted away like spray in the sun."
    )


def _resolution(world: World, hero: Entity, maestro: Entity, melody: Melody, prop: Prop) -> None:
    hero.meters["order"] += 1
    maestro.meters["calm"] += 1
    world.say(
        f"Soon {hero.id} was humming along beside {maestro.id}, and the {prop.label} stayed safe and sound."
    )
    world.say(
        f"By the end, {hero.id} was accustom to the {melody.label}, and the deck felt steady again."
    )


def tell_world(world: World, hero: Entity, maestro: Entity, melody: Melody, prop: Prop) -> None:
    world.say(_setting_line(world))
    world.say(_hero_intro(hero))
    world.say(
        f"{hero.id} loved the sea, but {hero.pronoun('subject')} was still learning how to be accustom to the crew's music times."
    )
    world.say(
        f"{maestro.id}, an angelic maestro with a lantern-bright coat, kept the sailors in time with gentle gestures."
    )
    world.say(
        f"{hero.id} especially watched {maestro.pronoun('object')} because {maestro.id} always looked calm, kind, and sure."
    )

    world.para()
    _start_song(world, hero, maestro, melody, prop)
    if _predict_misunderstanding(world, hero, melody, prop):
        _misunderstanding(world, hero, maestro, melody, prop)
    else:
        hero.meters["calm"] += 1
        world.say(f"{hero.id} listened closely and understood at once, so no misunderstanding came.")

    world.para()
    if hero.memes["misunderstanding"] >= THRESHOLD:
        _clear_up(world, hero, maestro, melody)
    _resolution(world, hero, maestro, melody, prop)

    world.facts.update(hero=hero, maestro=maestro, melody=melody, prop=prop)
    world.facts["resolved"] = hero.memes["misunderstanding"] < THRESHOLD


SHIP_REGISTRY = {
    "skiff": Ship(name="the skiff", afford_music=True, afford_talk=True, afford_practice=True),
    "brig": Ship(name="the brig", afford_music=True, afford_talk=True, afford_practice=True),
    "cutter": Ship(name="the cutter", afford_music=True, afford_talk=True, afford_practice=True),
}

MELODIES = {
    "anthem": Melody(
        id="anthem",
        label="ship anthem",
        kind="music",
        effect="brave",
        has_beat=True,
        requires_listening=True,
        keyword="anthem",
    ),
    "lullaby": Melody(
        id="lullaby",
        label="lantern lullaby",
        kind="music",
        effect="gentle",
        has_beat=False,
        requires_listening=True,
        keyword="lullaby",
    ),
    "drumroll": Melody(
        id="drumroll",
        label="barrel drumroll",
        kind="music",
        effect="quick",
        has_beat=True,
        requires_listening=True,
        keyword="drumroll",
    ),
}

PROPS = {
    "sheet": Prop(
        id="sheet",
        label="music sheet",
        phrase="a folded music sheet",
        kind="paper",
        tied_to_music=True,
        can_be_misread=True,
    ),
    "whistle": Prop(
        id="whistle",
        label="whistle",
        phrase="a silver whistle",
        kind="tool",
        tied_to_music=True,
        can_be_misread=True,
    ),
    "bell": Prop(
        id="bell",
        label="bell",
        phrase="a brass bell",
        kind="tool",
        tied_to_music=True,
        can_be_misread=True,
    ),
}

HERO_TRAITS = ["shy", "brave", "curious", "careful", "eager"]
GIRL_NAMES = ["Mira", "Nell", "Ruby", "Tess", "Luna"]
BOY_NAMES = ["Finn", "Jack", "Milo", "Pip", "Rowan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIP_REGISTRY:
        for melody in MELODIES:
            for prop in PROPS:
                if _safe_lookup(PROPS, prop).can_be_misread and _safe_lookup(MELODIES, melody).requires_listening:
                    combos.append((ship, melody, prop))
    return combos


@dataclass
class StoryConfig:
    ship: str
    melody: str
    prop: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate storyworld with an angelic maestro and a misunderstanding.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--melody", choices=MELODIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryConfig:
    combos = [c for c in valid_combos()
              if (getattr(args, "ship", None) is None or c[0] == getattr(args, "ship", None))
              and (getattr(args, "melody", None) is None or c[1] == getattr(args, "melody", None))
              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    ship, melody, prop = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    return StoryConfig(ship=ship, melody=melody, prop=prop, name=name, gender=gender, trait=trait)


def generate(params: StoryConfig) -> StorySample:
    world = World(SHIP_REGISTRY[params.ship])
    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, traits=[params.trait, "pirate"]))
    maestro = world.add(Entity(id="Maestro", kind="character", type="maestro", label="the maestro"))
    maestro.meters["order"] = 1.0
    maestro.memes["wonder"] = 1.0
    melody = _safe_lookup(MELODIES, params.melody)
    prop = _safe_lookup(PROPS, params.prop)
    world.add(Entity(id=prop.id, kind="thing", type=prop.kind, label=prop.label, phrase=prop.phrase, owner=maestro.id))
    tell_world(world, hero, maestro, melody, prop)

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
    melody = _safe_fact(world, f, "melody")
    return [
        f"Write a child-friendly pirate tale about {hero.id}, an angelic maestro, and a misunderstanding on a ship.",
        f"Tell a short story where a pirate learns to be accustom to the {melody.label} with help from a kind maestro.",
        f"Write a simple sea story that includes an inner monologue and ends with the crew understanding each other.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    maestro: Entity = _safe_fact(world, f, "maestro")
    melody: Melody = _safe_fact(world, f, "melody")
    prop: Prop = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.traits[0]} little pirate who was learning ship life, and {maestro.id}, the angelic maestro.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand?",
            answer=f"{hero.id} thought {maestro.id} might be upset about the {prop.label}, but that was not true.",
        ),
        QAItem(
            question=f"What helped clear up the misunderstanding?",
            answer=f"{maestro.id} showed the beat again and helped {hero.id} understand the {melody.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maestro?",
            answer="A maestro is a person who leads music and helps other people keep the right rhythm together.",
        ),
        QAItem(
            question="What does it mean to accustom yourself to something?",
            answer="To accustom yourself to something means to get used to it little by little until it feels familiar.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character has in their own thoughts.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something wrong and needs a gentle explanation.",
        ),
        QAItem(
            question="Why do sailors follow a beat?",
            answer="Sailors follow a beat so they can move together at the same time, which makes work and music easier.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


ASP_RULES = r"""
ship(S) :- setting(S).
melody(M) :- tune(M).
prop(P) :- object(P).

misunderstanding(H,M,P) :- hero(H), maestro(M), prop(P), can_be_misread(P), requires_listening(Mel), tune(Mel), melody_on_ship(H,Mel), hears_wrong(H,P).
resolved(H) :- misunderstanding(H,_,_), cleared_by_music(H).

valid_story(S, Mel, P) :- ship(S), melody(Mel), prop(P), can_be_misread(P), requires_listening(Mel).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHIP_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for mid, m in MELODIES.items():
        lines.append(asp.fact("tune", mid))
        if m.requires_listening:
            lines.append(asp.fact("requires_listening", mid))
        if m.has_beat:
            lines.append(asp.fact("has_beat", mid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("object", pid))
        if p.can_be_misread:
            lines.append(asp.fact("can_be_misread", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryConfig(ship="skiff", melody="anthem", prop="sheet", name="Mira", gender="girl", trait="shy"),
    StoryConfig(ship="brig", melody="lullaby", prop="whistle", name="Finn", gender="boy", trait="curious"),
    StoryConfig(ship="cutter", melody="drumroll", prop="bell", name="Ruby", gender="girl", trait="eager"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
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
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.melody} aboard {p.ship}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
