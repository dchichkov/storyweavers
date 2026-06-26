#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/buy_space_find_sound_effects_surprise_bad.py
==============================================================================================

A small ghost-story world where a child buys a strange little object, searches
an empty space, finds an unsettling clue, and ends with a bad surprise.

The domain is intentionally tiny:
- a child wants to buy something for exploring a spooky space
- they search a quiet room, attic, hallway, or cellar
- sound effects matter: creaks, whispers, taps, thumps, rattles
- a surprising clue appears
- the ending is bad, but still complete and story-shaped

This file follows the Storyweavers world contract:
- self-contained stdlib script
- shared result containers imported eagerly
- ASP helpers imported lazily
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

    child: object | None = None
    parent: object | None = None
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
    darkness: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    price: str
    use: str
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
class Space:
    id: str
    label: str
    phrase: str
    kind: str
    echo: str
    sounds: list[str] = field(default_factory=list)
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
class Clue:
    id: str
    label: str
    phrase: str
    surprise: str
    badness: str
    cause: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    space: str
    item: str
    clue: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "house": Setting(place="the old house", darkness="dim", affordances={"buy", "find"}),
    "attic": Setting(place="the attic", darkness="dark", affordances={"buy", "find"}),
    "hall": Setting(place="the long hall", darkness="dim", affordances={"buy", "find"}),
    "cellar": Setting(place="the cellar", darkness="dark", affordances={"buy", "find"}),
}

ITEMS = {
    "flashlight": Item(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight with a yellow button",
        type="flashlight",
        price="a few coins",
        use="shine through the dark",
        tags={"light", "sound"},
    ),
    "matches": Item(
        id="matches",
        label="matchbox",
        phrase="a tiny matchbox with three wooden matches",
        type="matches",
        price="a little pocket money",
        use="make a quick light",
        tags={"fire", "sound"},
    ),
    "bell": Item(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        type="bell",
        price="a shiny coin",
        use="ring if something moved",
        tags={"sound"},
    ),
}

SPACES = {
    "attic": Space(
        id="attic",
        label="attic",
        phrase="the dusty attic",
        kind="room",
        echo="every step sounded bigger there",
        sounds=["creak", "tap", "whisper"],
        tags={"dust", "ghost", "sound"},
    ),
    "hall": Space(
        id="hall",
        label="hall",
        phrase="the long hall",
        kind="hall",
        echo="the walls sent the sound back again",
        sounds=["creak", "rattle", "thump"],
        tags={"ghost", "sound"},
    ),
    "cellar": Space(
        id="cellar",
        label="cellar",
        phrase="the cold cellar",
        kind="room",
        echo="the dark corners answered softly",
        sounds=["drip", "thump", "whisper"],
        tags={"wet", "ghost", "sound"},
    ),
    "house": Space(
        id="house",
        label="parlor",
        phrase="the quiet parlor",
        kind="room",
        echo="the silence felt too careful",
        sounds=["soft tap", "tiny creak", "hush"],
        tags={"sound"},
    ),
}

CLUES = {
    "photo": Clue(
        id="photo",
        label="photo",
        phrase="an old black-and-white photo",
        surprise="the picture showed the child standing beside a pale face at the window",
        badness="it meant the ghost had been there all along",
        cause="someone had locked the room years ago",
        tags={"ghost", "surprise"},
    ),
    "key": Clue(
        id="key",
        label="key",
        phrase="a cold brass key",
        surprise="the key fit a tiny door behind the shelves",
        badness="and the door opened onto a place that should have stayed shut",
        cause="something inside had been waiting",
        tags={"ghost", "surprise"},
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note",
        surprise="the note said, 'Do not look behind the curtain after midnight'",
        badness="and the curtain moved by itself",
        cause="the house liked to hide its worst secrets",
        tags={"ghost", "surprise"},
    ),
}


GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Rose", "June", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Max", "Eli", "Noah", "Ben", "Leo"]
TRAITS = ["curious", "quiet", "brave", "nervy", "gentle", "restless"]


class Sound:
    def __init__(self, kind: str, line: str) -> None:
        self.kind = kind
        self.line = line


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for space in SPACES:
            for item in ITEMS:
                for clue in CLUES:
                    if place in setting.affordances and item in ITEMS and space in SPACES and clue in CLUES:
                        combos.append((place, space, item, clue))
    return combos


def reasonableness_gate(place: str, space: str, item: str, clue: str) -> bool:
    if place not in SETTINGS or space not in SPACES or item not in ITEMS or clue not in CLUES:
        return False
    if place not in _safe_lookup(SETTINGS, place).affordances:
        return False
    return True


def explain_rejection(place: str, space: str, item: str, clue: str) -> str:
    return (
        f"(No story: the requested combination is not reasonable here. "
        f"Try another place/space/item/clue mix that still lets the child buy something, "
        f"search the space, and find a surprise.)"
    )


def tell_sound(world: World, sound: str) -> None:
    world.say(sound)


def buy_item(world: World, child: Entity, parent: Entity, item: Item) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    world.say(
        f"{child.id} had been saving pocket money, so {child.pronoun('subject')} went to buy "
        f"{item.phrase}."
    )
    world.say(
        f"{parent.label or parent.id} handed over {item.price}, and {child.id} held the new {item.label} "
        f"like a tiny treasure."
    )


def enter_space(world: World, child: Entity, space: Space, item: Item) -> None:
    world.say(
        f"That night, {child.id} walked into {space.phrase} with the {item.label} in hand."
    )
    world.say(
        f"The {space.label} was {world.setting.darkness}, and {space.echo}."
    )


def search_space(world: World, child: Entity, space: Space, item: Item) -> None:
    child.meters["search"] = child.meters.get("search", 0.0) + 1
    for s in space.sounds:
        tell_sound(world, f"There was a {s} from the dark.")
    world.say(
        f"{child.id} listened hard and searched the {space.label} corner by corner."
    )


def find_clue(world: World, child: Entity, clue: Clue) -> None:
    child.memes["surprised"] = child.memes.get("surprised", 0.0) + 1
    world.say(f"Then {child.id} found {clue.phrase}.")
    world.say(clue.surprise)


def bad_ending(world: World, child: Entity, clue: Clue, item: Item) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    world.say(
        f"That was the bad part: {clue.badness}."
    )
    world.say(
        f"{child.id} tried to run back out, but the {item.label} flickered once and died, "
        f"and the dark stayed right behind {child.pronoun('object')}."
    )
    world.say(
        f"By the time the house went still again, the old secret was still there, and {child.id} had "
        f"learned to fear the quiet."
    )


def generate_story(world: World, child: Entity, parent: Entity, item: Item, space: Space, clue: Clue) -> None:
    world.say(
        f"One evening, {child.id} asked {parent.pronoun('possessive')} {parent.label or parent.id} "
        f"to buy {item.phrase}."
    )
    world.say(
        f"{child.id} wanted it for {space.phrase}, because the place felt spooky and strange."
    )
    world.para()
    buy_item(world, child, parent, item)
    enter_space(world, child, space, item)
    search_space(world, child, space, item)
    world.para()
    find_clue(world, child, clue)
    bad_ending(world, child, clue, item)
    world.facts.update(child=child, parent=parent, item=item, space=space, clue=clue)


def story_for_params(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"search": 0.0},
        memes={},
    ))
    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
        label=params.parent,
        memes={},
    ))
    item = _safe_lookup(ITEMS, params.item)
    space = _safe_lookup(SPACES, params.space)
    clue = _safe_lookup(CLUES, params.clue)
    generate_story(world, child, parent, item, space, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, item, space, clue = f["child"], f["item"], f["space"], f["clue"]
    return [
        f'Write a short ghost story for a child named {child.id} who buys {item.phrase}, '
        f'searches {space.phrase}, and finds something surprising.',
        f'Tell a spooky little story where {child.id} listens for sound effects in the {space.label}, '
        f'finds {clue.phrase}, and the ending turns bad.',
        f'Write a child-friendly ghost story with buying, searching, a surprise clue, and a gloomy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item, space, clue = f["child"], f["parent"], f["item"], f["space"], f["clue"]
    return [
        QAItem(
            question=f"What did {child.id} buy before going into the {space.label}?",
            answer=f"{child.id} bought {item.phrase} so {child.pronoun('subject')} could go into {space.phrase} and search in the dark.",
        ),
        QAItem(
            question=f"What sound effects did {child.id} hear while searching the {space.label}?",
            answer=f"{child.id} heard a set of spooky sounds, like the creaks, taps, whispers, and other noises coming from {space.phrase}.",
        ),
        QAItem(
            question=f"What surprising thing did {child.id} find?",
            answer=f"{child.id} found {clue.phrase}, and the surprise was that {clue.surprise.lower()}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {clue.badness.lower()}, so the story closed with fear instead of safety.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight makes a beam of light so people can see in dark places.",
        ),
        QAItem(
            question="Why do old houses sound creepy at night?",
            answer="Old houses can creak and echo at night because wood and walls make small sounds carry in the dark.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen.",
        ),
        QAItem(
            question="What makes a ghost story spooky?",
            answer="A ghost story feels spooky when it uses dark places, strange sounds, and mysterious events.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", space="attic", item="flashlight", clue="photo", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="cellar", space="cellar", item="matches", clue="key", name="Theo", gender="boy", parent="father"),
    StoryParams(place="hall", space="hall", item="bell", clue="note", name="Nora", gender="girl", parent="mother"),
]


@dataclass
class ASPState:
    place: str
    space: str
    item: str
    clue: str
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


ASP_RULES = r"""
valid_combo(P,S,I,C) :- place(P), space(S), item(I), clue(C), affords(P, buy), affords(P, find).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in sorted(_safe_lookup(SETTINGS, p).affordances):
            lines.append(asp.fact("affords", p, a))
    for s in SPACES:
        lines.append(asp.fact("space", s))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: buy, space, find, surprise, bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--space", choices=SPACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
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
    if getattr(args, "place", None) and getattr(args, "space", None) and getattr(args, "item", None) and getattr(args, "clue", None):
        if not reasonableness_gate(getattr(args, "place", None), getattr(args, "space", None), getattr(args, "item", None), getattr(args, "clue", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "space", None) is None or c[1] == getattr(args, "space", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "clue", None) is None or c[3] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, space, item, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, space=space, item=item, clue=clue, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = story_for_params(params)
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
        print(asp_program("#show valid_combo/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: buy {p.item} / search {p.space} / find {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
