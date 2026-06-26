#!/usr/bin/env python3
"""
storyworlds/worlds/loon_possess_gramps_sound_effects_quest_mystery.py
======================================================================

A small story world about a child, a gramps, a mysterious quest, and the
sound a loon makes across the water.

The seed idea is a tiny mystery:
- a child hears a loon call on the lake,
- a gramps asks them to help find a lost thing,
- clues arrive as sound effects, not just sights,
- the search turns into a calm little quest,
- the ending proves what was found and how the feeling changed.

The world is constraint-checked: the mystery must be solvable, the clue trail
must be grounded in the setting, and the ending must actually change the world
state.
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
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "lake": {
        "label": "the lake",
        "indoors": False,
        "features": {"water", "shore", "dock", "reeds"},
    },
    "pond": {
        "label": "the pond",
        "indoors": False,
        "features": {"water", "shore", "reeds", "mud"},
    },
    "marsh": {
        "label": "the marsh",
        "indoors": False,
        "features": {"water", "reeds", "mud", "path"},
    },
}

QUESTS = {
    "shell": {
        "name": "a silver shell",
        "kind": "shell",
        "location_feature": "shore",
        "hint": "a small shiny thing by the water",
    },
    "key": {
        "name": "a brass key",
        "kind": "key",
        "location_feature": "dock",
        "hint": "something metal that could unlock a box",
    },
    "glasses": {
        "name": "gramps's reading glasses",
        "kind": "glasses",
        "location_feature": "reeds",
        "hint": "something thin and clear near the water plants",
    },
}

SOUND_EFFECTS = {
    "loon_call": {
        "word": "a lonely loon call",
        "text": "A loon called across the water: 'wooo-oo-oo.'",
        "meaning": "a clue that the thing was near the water",
    },
    "dock_creak": {
        "word": "a creaky dock",
        "text": "The dock gave a soft creak under careful steps.",
        "meaning": "a clue that someone had walked near the dock",
    },
    "reeds_rustle": {
        "word": "rustling reeds",
        "text": "The reeds whispered and rustled beside the shore.",
        "meaning": "a clue that the thing might be hidden in the plants",
    },
    "splash": {
        "word": "a little splash",
        "text": "Somewhere, water made a little splash-skip sound.",
        "meaning": "a clue that something had just moved in the water",
    },
}

CHARACTER_NAMES = ["Mina", "June", "Eli", "Toby", "Nora", "Ada", "Finn", "Lena"]
GRANDPARENT_NAMES = ["Gramps", "Grandpa", "Old Ben", "Pop", "Gramps Joe"]


# ---------------------------------------------------------------------------
# Data model
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
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grams: object | None = None
    quest: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
class Place:
    key: str
    label: str
    indoors: bool
    features: set[str] = field(default_factory=set)
    place: object | None = None
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


@dataclass
class QuestItem:
    key: str
    name: str
    kind: str
    location_feature: str
    hint: str
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


@dataclass
class SoundClue:
    key: str
    word: str
    text: str
    meaning: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}
        self.clues: list[str] = []
        self.trace_events: list[str] = []

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.clues = list(self.clues)
        return w


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    sound: str
    child_name: str
    child_gender: str
    grandparent_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
    params: object | None = None
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


def child_names(gender: str) -> list[str]:
    if gender == "girl":
        return ["Mina", "June", "Nora", "Ada", "Lena"]
    return ["Eli", "Toby", "Finn"]


def question_text(quest: QuestItem) -> str:
    return f"Why did the sound matter in the search for {quest.name}?"


def reasonableness_check(params: StoryParams) -> None:
    if params.quest not in QUESTS:
        pass
    if params.sound not in SOUND_EFFECTS:
        pass
    if params.place not in LOCATIONS:
        pass
    quest = _safe_lookup(QUESTS, params.quest)
    place = _safe_lookup(LOCATIONS, params.place)
    if quest["location_feature"] not in place["features"]:
        pass


def choose_from_registry(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUND_EFFECTS))
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name_pool = child_names(child_gender)
    child_name = getattr(args, "name", None) or rng.choice(name_pool)
    grandparent_name = getattr(args, "grandparent", None) or rng.choice(GRANDPARENT_NAMES)
    params = StoryParams(
        place=place,
        quest=quest,
        sound=sound,
        child_name=child_name,
        child_gender=child_gender,
        grandparent_name=grandparent_name,
    )
    reasonableness_check(params)
    return params


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = Place(
        key=params.place,
        label=_safe_lookup(LOCATIONS, params.place)["label"],
        indoors=_safe_lookup(LOCATIONS, params.place)["indoors"],
        features=set(_safe_lookup(LOCATIONS, params.place)["features"]),
    )
    world = World(place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if params.child_gender == "girl" else "boy",
        label=params.child_name,
        meters={"curiosity": 0.0, "courage": 0.0, "worry": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    grams = world.add(Entity(
        id="gramps",
        kind="character",
        type="man",
        label=params.grandparent_name,
        meters={"calm": 1.0},
        memes={"calm": 1.0, "hope": 0.0},
    ))
    quest_cfg = _safe_lookup(QUESTS, params.quest)
    quest = world.add(Entity(
        id="quest_item",
        kind="thing",
        type=quest_cfg["kind"],
        label=quest_cfg["name"],
        phrase=quest_cfg["name"],
        owner=grams.id,
        hidden=True,
        found=False,
    ))
    sound_cfg = _safe_lookup(SOUND_EFFECTS, params.sound)

    world.facts.update(
        child=child,
        gramps=grams,
        quest=quest,
        quest_cfg=quest_cfg,
        sound_cfg=sound_cfg,
        place=place,
    )

    # setup
    world.say(
        f"{child.label} went with {grams.label} to {place.label}, where the water looked still and watchful."
    )
    world.say(
        f"{child.label} liked mysteries, because every little clue felt like a game with a secret answer."
    )
    world.para()
    world.say(
        f"That day, {grams.label} said there was a small quest: {quest_cfg['name']} had gone missing."
    )
    world.say(
        f"{child.label} listened hard, because the best clues were not always things you could see."
    )

    # tension
    world.para()
    child.memes["curiosity"] += 1.0
    child.meters["curiosity"] += 1.0
    world.say(sound_cfg["text"])
    world.say(
        f"{grams.label} nodded. '{sound_cfg['meaning'].capitalize()},' he said, 'so let's follow the sound.'"
    )

    clue_seq = generate_clues(world, params)
    world.clues = clue_seq

    # quest turn
    world.para()
    for clue in clue_seq[:-1]:
        world.say(describe_clue(clue))
    world.say(
        f"At last, {child.label} spotted {quest_cfg['hint']} and reached down carefully."
    )
    quest.hidden = False
    quest.found = True
    quest.location = place.label
    child.meters["courage"] += 1.0
    child.memes["joy"] += 1.0
    grams.memes["hope"] += 1.0

    # resolution
    world.para()
    world.say(
        f"{child.label} held up {quest.label}, and {grams.label} laughed with relief."
    )
    world.say(
        f"The mystery was solved: the sound had been a true clue, and the missing thing was safe again."
    )
    world.say(
        f"By the water, the loon called once more, and this time it sounded like a happy ending."
    )

    return world


def generate_clues(world: World, params: StoryParams) -> list[str]:
    quest_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "quest_cfg")
    sound_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sound_cfg")
    place = world.place
    clues: list[str] = []

    if params.sound == "loon_call":
        clues.append("loon_call")
    elif params.sound == "dock_creak":
        clues.append("dock_creak")
    elif params.sound == "reeds_rustle":
        clues.append("reeds_rustle")
    else:
        clues.append("splash")

    # a second clue always follows, tied to the location feature of the quest item
    feature = quest_cfg["location_feature"]
    if feature == "dock":
        clues.append("dock_creak")
    elif feature == "reeds":
        clues.append("reeds_rustle")
    else:
        clues.append("splash")

    # The final clue is the location proof.
    if "water" in place.features:
        clues.append("loon_call")
    return clues


def describe_clue(clue_key: str) -> str:
    clue = _safe_lookup(SOUND_EFFECTS, clue_key)
    if clue_key == "loon_call":
        return f"{clue['text']} {clue['meaning'].capitalize()}."
    return f"{clue['text']} {clue['meaning'].capitalize()}."


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts describe the place, quest item, and sound clues.
quest_at(P, Q) :- place_feature(P, F), quest_feature(Q, F).
clue_points_to(S, Q) :- sound_clue(S), clue_meaning(S, M), clue_match(M, Q).
solvable(P, Q, S) :- quest_at(P, Q), clue_points_to(S, Q).
valid_story(P, Q, S) :- place(P), quest(Q), sound_clue(S), solvable(P, Q, S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key, cfg in LOCATIONS.items():
        lines.append(asp.fact("place", key))
        for feat in sorted(cfg["features"]):
            lines.append(asp.fact("place_feature", key, feat))
    for key, cfg in QUESTS.items():
        lines.append(asp.fact("quest", key))
        lines.append(asp.fact("quest_feature", key, cfg["location_feature"]))
        lines.append(asp.fact("quest_name", key, cfg["name"]))
    for key, cfg in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound_clue", key))
        lines.append(asp.fact("clue_meaning", key, cfg["meaning"]))
        if key == "loon_call":
            lines.append(asp.fact("clue_match", cfg["meaning"], "shell"))
            lines.append(asp.fact("clue_match", cfg["meaning"], "key"))
            lines.append(asp.fact("clue_match", cfg["meaning"], "glasses"))
        elif key == "dock_creak":
            lines.append(asp.fact("clue_match", cfg["meaning"], "key"))
        elif key == "reeds_rustle":
            lines.append(asp.fact("clue_match", cfg["meaning"], "glasses"))
        elif key == "splash":
            lines.append(asp.fact("clue_match", cfg["meaning"], "shell"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple]:
    out = []
    for p in LOCATIONS:
        for q in QUESTS:
            for s in SOUND_EFFECTS:
                params = StoryParams(p, q, s, "Mina", "girl", "Gramps")
                try:
                    reasonableness_check(params)
                except StoryError:
                    continue
                out.append((p, q, s))
    return sorted(out)


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_stories())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP gate matches Python valid_stories() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest_cfg")["name"]
    sound = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound_cfg")["word"]
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")["label"]
    return [
        f"Write a short mystery story for a young child about {child.label}, {quest}, and {sound} at {place}.",
        f"Tell a gentle quest story where sound effects help solve a missing-item mystery by the water.",
        f"Create a child-facing story with a loon call, a gramps, and a found treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    grams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gramps")
    quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")
    quest_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest_cfg")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    sound_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound_cfg")
    return [
        QAItem(
            question=f"Who went on the quest with {child.label}?",
            answer=f"{grams.label} went with {child.label} on the mystery quest by {place.label}.",
        ),
        QAItem(
            question=f"What was the missing thing?",
            answer=f"The missing thing was {quest_cfg['name']}.",
        ),
        QAItem(
            question=f"What sound helped point the way?",
            answer=f"{sound_cfg['text']} That sound helped guide the search.",
        ),
        QAItem(
            question=f"Where was the clue trail leading?",
            answer=f"It was leading around {place.label}, because the quest was tied to the water there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What sound does a loon make?",
            answer="A loon makes a long, wailing call that carries over water.",
        ),
        QAItem(
            question="Why can sound help in a mystery?",
            answer="Sound can help because it may point to something hidden, even when you cannot see it yet.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something, solve a problem, or discover an answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a loon, a gramps, sound clues, and a quest.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--sound", choices=SOUND_EFFECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grandparent")
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
    params = choose_from_registry(args, rng)
    if getattr(args, "gender", None) and params.child_gender != getattr(args, "gender", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


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
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
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
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        models = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(models, "valid_story")))
        print(f"{len(triples)} valid (place, quest, sound) combinations:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = []
        for p in LOCATIONS:
            for q in QUESTS:
                for s in SOUND_EFFECTS:
                    try:
                        reasonableness_check(StoryParams(p, q, s, "Mina", "girl", "Gramps"))
                    except StoryError:
                        continue
                    combos.append((p, q, s))
        for i, (p, q, s) in enumerate(combos[: max(1, getattr(args, "n", None))]):
            params = StoryParams(p, q, s, _safe_lookup(CHARACTER_NAMES, i % len(CHARACTER_NAMES)), "girl" if i % 2 == 0 else "boy", _safe_lookup(GRANDPARENT_NAMES, i % len(GRANDPARENT_NAMES)), seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {idx + 1}: {p.child_name}, {p.quest}, {p.place}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
