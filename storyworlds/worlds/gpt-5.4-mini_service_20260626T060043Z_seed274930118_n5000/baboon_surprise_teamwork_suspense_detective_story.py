#!/usr/bin/env python3
"""
A small detective-story world about a baboon, a surprising clue, suspense,
and teamwork.

The baboon detective solves a simple mystery: something important goes missing,
the clues look strange, and the friends work together to find the answer.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    missing: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    place_detail: str
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
class Mystery:
    id: str
    title: str
    missing: str
    clue: str
    surprise: str
    suspense_line: str
    teamwork_line: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Helper:
    id: str
    label: str
    type: str
    help_action: str
    clue_action: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


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
    place: str = ""
    mystery: str = ""
    helper: str = ""
    name: str = ""
    companion: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


SETTINGS = {
    "garden_gate": Setting(
        place="the garden gate",
        place_detail="The garden gate stood between the path and the bushes, where little things could hide.",
        affords={"missing_cookie", "missing_hat"},
    ),
    "river_path": Setting(
        place="the river path",
        place_detail="The river path was narrow, with muddy footprints and reeds that bent in the wind.",
        affords={"missing_hat", "missing_map"},
    ),
    "museum_yard": Setting(
        place="the museum yard",
        place_detail="The museum yard had stone benches, flower pots, and a quiet corner behind a statue.",
        affords={"missing_cookie", "missing_map"},
    ),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        id="missing_cookie",
        title="the missing cookie",
        missing="cookie",
        clue="a tiny crumb trail",
        surprise="the crumbs pointed under a flower pot",
        suspense_line="The baboon detective watched the crumb trail with wide eyes.",
        teamwork_line="The baboon asked the sparrow to look above and the rabbit to look below.",
        resolution="The cookie had rolled into a basket, and everyone laughed when it was found.",
        tags={"cookie", "crumbs", "food"},
    ),
    "missing_hat": Mystery(
        id="missing_hat",
        title="the missing hat",
        missing="hat",
        clue="a ribbon caught on a branch",
        surprise="the ribbon matched the hatband exactly",
        suspense_line="The baboon detective felt the case grow quieter and stranger.",
        teamwork_line="The baboon climbed carefully while the otter checked the ground and the sparrow watched the branch.",
        resolution="The hat was hanging in a low tree, as if the wind had borrowed it for a game.",
        tags={"hat", "wind", "branch"},
    ),
    "missing_map": Mystery(
        id="missing_map",
        title="the missing map",
        missing="map",
        clue="a torn corner beside a bench",
        surprise="the torn corner showed the same blue ink as the map",
        suspense_line="The baboon detective frowned at the silent bench and listened for clues.",
        teamwork_line="The baboon, the otter, and the sparrow searched together, each looking in a different place.",
        resolution="The map was tucked inside a notebook, safe and dry the whole time.",
        tags={"map", "ink", "paper"},
    ),
}

HELPERS = {
    "sparrow": Helper(
        id="sparrow",
        label="a sparrow",
        type="bird",
        help_action="looked from above",
        clue_action="pointed out the shiny clue",
    ),
    "rabbit": Helper(
        id="rabbit",
        label="a rabbit",
        type="rabbit",
        help_action="searched near the ground",
        clue_action="sniffed the crumb trail",
    ),
    "otter": Helper(
        id="otter",
        label="an otter",
        type="otter",
        help_action="checked the water edge",
        clue_action="noticed what had been washed aside",
    ),
}

BABOON_NAMES = ["Bobo", "Momo", "Tari", "Zuri", "Niko", "Lani"]
COMPANIONS = ["sparrow", "rabbit", "otter"]
TRAITS = ["curious", "careful", "brave", "quick-thinking", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mystery_id in setting.affords:
            for helper in HELPERS:
                out.append((place, mystery_id, helper))
    return out


def explain_rejection(place: str, mystery_id: str, helper_id: str) -> str:
    if mystery_id not in _safe_lookup(SETTINGS, place).affords:
        return f"(No story: {place} does not fit {mystery_id} in a way that makes a real mystery here.)"
    if helper_id not in HELPERS:
        return "(No story: that helper is not part of this detective world.)"
    return "(No story: the requested combination is not reasonable.)"


def choose_name(rng: random.Random) -> str:
    return rng.choice(BABOON_NAMES)


def choose_trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)


def tell(setting: Setting, mystery: Mystery, helper: Helper, name: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="baboon", traits=["little", trait, "detective"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=helper.type, label=helper.label))
    missing = world.add(Entity(id="missing", type=mystery.missing, label=mystery.missing, owner=detective.id))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue))

    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        missing=missing,
        clue=clue,
        mystery=mystery,
        helper=helper,
        setting=setting,
    )

    world.say(
        f"{detective.id} was a little {trait} baboon detective who loved solving puzzles at {setting.place}."
    )
    world.say(
        f"One day, {detective.id} noticed that {detective.pronoun('possessive')} {mystery.missing} was gone."
    )

    world.para()
    world.say(setting.place_detail)
    world.say(mystery.suspense_line)
    world.say(
        f"Then came a surprise: {mystery.clue}, and it pointed toward {mystery.surprise.split('under')[-1].strip()}."
    )
    world.say(f"{helper.label.capitalize()} {helper.help_action}, which made the case even more interesting.")

    world.para()
    world.say(
        f"{detective.id} and {sidekick.label} kept looking. {mystery.teamwork_line}"
    )
    world.say(
        f"Together, they followed the clue until the answer popped out."
    )
    world.say(
        f"{mystery.resolution}"
    )
    world.say(
        f"In the end, {detective.id} smiled, {sidekick.label} nodded, and the mystery was solved with teamwork."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        f"Write a short detective story for young children about {detective.id}, a baboon, solving {mystery.title} at {setting.place}.",
        f"Tell a suspenseful but gentle story where {detective.id} gets a surprise clue and works with {helper.label} to find {mystery.missing}.",
        f"Create a small mystery story with teamwork, suspense, and a happy ending set at {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {detective.id}, a baboon who keeps calm and looks for clues.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{detective.id} was trying to find {detective.pronoun('possessive')} {mystery.missing}.",
        ),
        QAItem(
            question=f"Who helped {detective.id} solve the mystery?",
            answer=f"{helper.label.capitalize()} helped by looking in a helpful way while {detective.id} followed the clues.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The missing {mystery.missing} and the strange clue at {setting.place} made the search feel suspenseful.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with teamwork, because the clue led them to the answer and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person or character who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while the answer is not known yet.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
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
        lines.append(f"  {e.id:10} ({e.type:8})")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(place).
mystery(missing_cookie).
mystery(missing_hat).
mystery(missing_map).
helper(sparrow).
helper(rabbit).
helper(otter).

compatible(Place, Mystery, Helper) :- setting(Place), mystery(Mystery), helper(Helper).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A baboon detective story world with surprise, suspense, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
        and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, helper = rng.choice(list(filtered))
    name = getattr(args, "name", None) or choose_name(rng)
    return StoryParams(place=place, mystery=mystery, helper=helper, name=name, companion=helper, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), _safe_lookup(HELPERS, params.helper), params.name, choose_trait(random.Random(params.seed or 0)))
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
    StoryParams(place="garden_gate", mystery="missing_cookie", helper="sparrow", name="Bobo"),
    StoryParams(place="river_path", mystery="missing_hat", helper="otter", name="Momo"),
    StoryParams(place="museum_yard", mystery="missing_map", helper="rabbit", name="Tari"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_combos()
        print(f"{len(combos)} compatible story combos:")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
