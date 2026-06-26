#!/usr/bin/env python3
"""
A standalone storyworld about a small adventure where a child follows directions,
runs into conflict, and finds a braver way forward.

This world is built around:
- direction as the guiding theme
- conflict as the central tension
- adventure as the style
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    supports: set[str] = field(default_factory=set)
    gear: object | None = None
    guide: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "conflict": 0.0, "worry": 0.0, "curiosity": 0.0}

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
class Place:
    name: str
    outdoors: bool
    paths: set[str] = field(default_factory=set)
    landmarks: list[str] = field(default_factory=list)
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
class DirectionPuzzle:
    id: str
    goal: str
    wrong_turn: str
    conflict_word: str
    clue: str
    resolution: str
    risk: str
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
class Gear:
    id: str
    label: str
    helps: str
    supports: set[str] = field(default_factory=set)
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    path_taken: list[str] = field(default_factory=list)
    direction_state: str = "unknown"

    c: object | None = None
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
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.path_taken = list(self.path_taken)
        c.direction_state = self.direction_state
        return c
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


def _r_conflict(world: World) -> None:
    hero = world.get(world.facts["hero"])
    if hero.memes["worry"] >= THRESHOLD and hero.memes["curiosity"] >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1


def propagate(world: World) -> None:
    _r_conflict(world)


def choose_turn(puzzle: DirectionPuzzle) -> str:
    return puzzle.wrong_turn


def correct_turn(puzzle: DirectionPuzzle) -> str:
    return puzzle.resolution


PLACES = {
    "forest": Place(
        name="the forest trail",
        outdoors=True,
        paths={"left", "right", "straight"},
        landmarks=["a bent pine", "a bright stream", "a stone arch"],
    ),
    "cliff": Place(
        name="the cliff path",
        outdoors=True,
        paths={"left", "right", "straight"},
        landmarks=["a windy edge", "a lookout sign", "a rope post"],
    ),
    "harbor": Place(
        name="the harbor road",
        outdoors=True,
        paths={"left", "right", "straight"},
        landmarks=["a red buoy", "a dock lantern", "a gull nest"],
    ),
}

PUZZLES = {
    "map": DirectionPuzzle(
        id="map",
        goal="find the hidden camp",
        wrong_turn="take the shiny shortcut to the right",
        conflict_word="direction",
        clue="the map arrow pointed toward the old stream",
        resolution="follow the stream and then turn left at the bent pine",
        risk="getting lost before sunset",
        tags={"direction", "map"},
    ),
    "lantern": DirectionPuzzle(
        id="lantern",
        goal="reach the lighthouse",
        wrong_turn="walk toward the louder path",
        conflict_word="direction",
        clue="the lantern light blinked from the quiet side",
        resolution="go straight until the dock lantern, then turn left",
        risk="missing the lighthouse in the dark",
        tags={"direction", "light"},
    ),
    "bridge": DirectionPuzzle(
        id="bridge",
        goal="cross to the hill fort",
        wrong_turn="rush across the cracked boards",
        conflict_word="direction",
        clue="the rope post pointed to the safer side path",
        resolution="take the side path and cross at the stone arch",
        risk="falling into the mud below",
        tags={"direction", "bridge"},
    ),
}

GEAR = {
    "compass": Gear(id="compass", label="a tiny compass", helps="keep the hero facing the right way", supports={"direction", "map"}),
    "lantern": Gear(id="lantern", label="a lantern", helps="show the path in the dark", supports={"light"}),
    "boots": Gear(id="boots", label="sturdy boots", helps="keep feet safe on rough ground", supports={"bridge"}),
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Ivy", "Nora", "Rae"]
BOY_NAMES = ["Jasper", "Noah", "Eli", "Theo", "Finn", "Milo"]
TRAITS = ["brave", "curious", "quick", "careful", "spirited", "bold"]


@dataclass
class StoryParams:
    place: str
    puzzle: str
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for path in sorted(p.paths):
            lines.append(asp.fact("path", pid, path))
    for pid, puz in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        for t in sorted(puz.tags):
            lines.append(asp.fact("tag", pid, t))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for s in sorted(g.supports):
            lines.append(asp.fact("supports", gid, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, PUZ) :- place(P), puzzle(PUZ), tag(PUZ, direction).
has_gear(PUZ) :- valid(_, PUZ), puzzle(PUZ).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return [(p, puz) for p in PLACES for puz in PUZZLES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about directions and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    puzzle = getattr(args, "puzzle", None) or rng.choice(list(PUZZLES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, puzzle=puzzle, name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    puz = _safe_lookup(PUZZLES, params.puzzle)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"dust": 0.0},
                            memes={"joy": 1.0, "conflict": 0.0, "worry": 0.0, "curiosity": 1.0}))
    guide = world.add(Entity(id="Guide", kind="character", type="adult", label="the guide"))
    gear = world.add(Entity(id="Compass", type="gear", label="a tiny compass", protective=True, supports={"direction", "map"}))
    world.facts.update(hero=hero.id, guide=guide.id, puzzle=puz, params=params, gear=gear)

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved adventure and secret paths.")
    world.say(f"One morning, {hero.id} and {guide.label} set out on {place.name} to {puz.goal}.")
    world.para()
    world.say(f"{hero.id} held up {gear.label}, but the trail split in three.")
    world.say(f"The {puz.conflict_word} felt tricky: {puz.clue}, yet the shiny way looked faster.")
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    propagate(world)
    world.say(f"{hero.id} wanted to {puz.wrong_turn}, and that caused a small conflict.")
    hero.memes["conflict"] = 1.0
    world.para()
    world.say(f"Then {guide.label} pointed carefully and said, \"{puz.clue.capitalize()}\"")
    world.say(f"So {hero.id} took a breath, chose to {puz.resolution}, and kept going.")
    world.path_taken = [puz.wrong_turn, puz.resolution]
    world.direction_state = "found"
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"At last, {hero.id} reached {puz.goal}, and the map, the path, and the brave choice all matched.")
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    puz: DirectionPuzzle = _safe_fact(world, world.facts, "puzzle")
    return [
        f"Write a short adventure story about a child named {params.name} who must follow a direction clue to {puz.goal}.",
        f"Tell a child-friendly tale where a {params.trait} {params.gender} meets a conflict about which direction to take.",
        f"Write an adventure story with a map, a wrong turn, and a brave correction on {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    puz: DirectionPuzzle = _safe_fact(world, world.facts, "puzzle")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {params.name}, a {params.trait} little {params.gender} who loves adventure.",
        ),
        QAItem(
            question=f"What conflict did {params.name} face on {world.place.name}?",
            answer=f"{params.name} had to choose the right direction, but the shiny shortcut made the choice feel hard.",
        ),
        QAItem(
            question=f"How did {params.name} solve the problem?",
            answer=f"{params.name} listened to the clue, chose to {puz.resolution}, and kept going the safe way.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{params.name} reached {puz.goal}, so the adventure ended with the right direction found.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compass for?",
            answer="A compass helps you know which direction you are facing so you can find your way.",
        ),
        QAItem(
            question="What can a wrong turn cause?",
            answer="A wrong turn can cause confusion or conflict because the traveler may get lost or miss the goal.",
        ),
        QAItem(
            question="Why do adventurers look at clues?",
            answer="Adventurers look at clues because clues help them choose the best direction to go next.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    lines.append(f"  path_taken={world.path_taken}")
    lines.append(f"  direction_state={world.direction_state}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, q in enumerate(sample.prompts, 1):
            print(f"P{i}: {q}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="forest", puzzle="map", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="cliff", puzzle="bridge", name="Theo", gender="boy", trait="brave"),
    StoryParams(place="harbor", puzzle="lantern", name="Ivy", gender="girl", trait="careful"),
]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
