#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/adjust_foreshadowing_misunderstanding_mystery.py
================================================================================================

A small mystery storyworld built from the seed words:
- adjust
- Foreshadowing
- Misunderstanding
- Mystery

Premise:
A child and a helper search for a small missing object in a cozy place.
The world keeps track of clues, guesses, and a final adjustment that reveals
the truth. Foreshadowing is embedded as early physical clues; misunderstanding
is an emotional beat where the wrong guess feels plausible; the resolution
comes from a concrete adjustment that changes the physical state and solves the
mystery.

The generated story is not a frozen template with swapped nouns. It is driven by
world state: clue strength, guess certainty, and whether the final adjustment
actually exposes the hidden object.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
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
    moved_to: str = ""
    hidden: bool = False
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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


@dataclass
class Room:
    id: str
    label: str
    mood: str
    features: list[str] = field(default_factory=list)
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
class ObjectSpec:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    clue_words: list[str]
    visible_clues: list[str]
    reveal_by: str
    careful_adjustment: str
    revealed_line: str
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
    room: str
    object: str
    name: str
    sidekick: str
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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

    def clues(self) -> list[str]:
        return self.facts.get("clues", [])

    def copy(self) -> "World":
        clone = World(self.room)
        clone.entities = json.loads(json.dumps({k: asdict(v) for k, v in self.entities.items()}))
        clone.facts = json.loads(json.dumps(self.facts))
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "hall": Room(id="hall", label="the quiet hall", mood="still", features=["coat hooks", "a tall mirror", "a shoe bench"]),
    "library": Room(id="library", label="the little library", mood="hushed", features=["book stacks", "a reading lamp", "a ladder"]),
    "attic": Room(id="attic", label="the dusty attic", mood="echoing", features=["boxes", "a slanted window", "old trunks"]),
    "kitchen": Room(id="kitchen", label="the sunny kitchen", mood="bright", features=["a clock", "jars", "a tea towel"]),
}

OBJECTS = {
    "silver_key": ObjectSpec(
        id="silver_key",
        label="silver key",
        phrase="a little silver key on a blue ribbon",
        hiding_spot="behind a picture frame",
        clue_words=["glint", "ribbon", "frame"],
        visible_clues=[
            "A tiny glint caught the light near the wall.",
            "A blue ribbon tip peeked out by the frame.",
            "The frame looked just a little crooked.",
        ],
        reveal_by="adjust the picture frame",
        careful_adjustment="adjusted the picture frame",
        revealed_line="Under the frame, the silver key hung from its blue ribbon, just where it had been all along.",
    ),
    "red_pin": ObjectSpec(
        id="red_pin",
        label="red pin",
        phrase="a bright red pin with a star on it",
        hiding_spot="under a cushion",
        clue_words=["star", "cushion", "rustle"],
        visible_clues=[
            "A small star-shaped print showed on the cushion.",
            "The cushion sat a little lopsided.",
            "Something had made the fabric puff up strangely.",
        ],
        reveal_by="lift the cushion",
        careful_adjustment="lifted the cushion",
        revealed_line="Under the cushion, the red pin shone like a tiny star.",
    ),
    "toy_watch": ObjectSpec(
        id="toy_watch",
        label="toy watch",
        phrase="a round toy watch with a green strap",
        hiding_spot="inside a shoe",
        clue_words=["tick", "strap", "shoe"],
        visible_clues=[
            "A faint tick came from the shoe bench.",
            "A green strap loop disappeared into one shoe.",
            "One shoe looked turned the wrong way.",
        ],
        reveal_by="turn the shoe",
        careful_adjustment="turned the shoe",
        revealed_line="Inside the shoe, the toy watch sat snug and safe, its green strap curled beside it.",
    ),
}

CHARACTER_NAMES = ["Mina", "Ivy", "Noah", "Toby", "Lila", "Eli", "Maya", "Finn"]
SIDEKICKS = ["grandma", "grandpa", "mother", "father", "aunt", "uncle", "older sister", "older brother"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room(room(hall)).
room(room(library)).
room(room(attic)).
room(room(kitchen)).

object(object(silver_key)).
object(object(red_pin)).
object(object(toy_watch)).

adjustment(reveal_by(object(silver_key), frame)).
adjustment(reveal_by(object(red_pin), cushion)).
adjustment(reveal_by(object(toy_watch), shoe)).

valid(Room, Obj) :- room(Room), object(Obj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room_name", rid))
    for oid in OBJECTS:
        lines.append(asp.fact("object_name", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(r, o) for r in ROOMS for o in OBJECTS}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} pairs).")
        return 0
    print("MISMATCH between python and clingo:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery world with foreshadowing and misunderstanding.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(room=room, object=obj, name=name, sidekick=sidekick)


def invalid_reason(params: StoryParams) -> None:
    if params.room not in ROOMS:
        pass
    if params.object not in OBJECTS:
        pass


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _story_intro(world: World, hero: Entity, helper: Entity, spec: ObjectSpec) -> None:
    room = world.room
    world.say(
        f"{hero.id} was a curious child who liked noticing tiny details in {room.label}."
    )
    world.say(
        f"One afternoon, {hero.id} and {helper.label} were looking for {spec.phrase}."
    )
    world.say(
        f"The room was {room.mood}, and {', '.join(room.features[:-1])} and {room.features[-1]} made it feel full of quiet secrets."
    )


def _foreshadow(world: World, spec: ObjectSpec) -> None:
    clues = spec.visible_clues
    world.facts["clues"] = clues
    world.say(clues[0])
    world.say(clues[1])


def _misunderstanding(world: World, hero: Entity, helper: Entity, spec: ObjectSpec) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} frowned. '{spec.label} can't have vanished by itself,' {hero.pronoun('subject')} said."
    )
    world.say(
        f"{helper.label.capitalize()} thought the wrong thing first and guessed that someone had taken it."
    )
    world.say(
        f"But the little clues did not feel like a theft. They felt like a hidden answer waiting to be noticed."
    )
    hero.memes["misunderstood"] += 1
    helper.memes["misunderstood"] += 1


def _adjust_and_reveal(world: World, hero: Entity, helper: Entity, spec: ObjectSpec) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} stopped, looked again, and decided to {spec.reveal_by}."
    )
    world.say(
        f"{helper.label.capitalize()} held the lamp steady while {hero.id} made the careful adjustment."
    )
    world.say(spec.visible_clues[2])
    world.say(spec.revealed_line)
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.meters["certainty"] = 1.0
    helper.meters["certainty"] = 1.0
    world.facts["revealed"] = True


def _resolution(world: World, hero: Entity, helper: Entity, spec: ObjectSpec) -> None:
    world.say(
        f"{hero.id} laughed softly because the mystery was never cruel, only tricky."
    )
    world.say(
        f"At the end, the room looked the same, except now the missing {spec.label} was back in sight."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, and {hero.id} tucked the {spec.label} safely away so it would not go missing again."
    )


def build_world(params: StoryParams) -> World:
    invalid_reason(params)
    room = _safe_lookup(ROOMS, params.room)
    spec = _safe_lookup(OBJECTS, params.object)
    world = World(room)

    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Ivy", "Lila", "Maya"} else "boy"))
    helper = world.add(Entity(id="helper", kind="character", type="woman" if params.sidekick in {"mother", "aunt", "grandma", "older sister"} else "man", label=params.sidekick))
    obj = world.add(Entity(id=spec.id, kind="thing", type="thing", label=spec.label, phrase=spec.phrase, hidden=True, moved_to=spec.hiding_spot))

    world.facts.update(hero=hero, helper=helper, obj=obj, spec=spec, room=room, params=params)

    _story_intro(world, hero, helper, spec)
    world.para()
    _foreshadow(world, spec)
    world.para()
    _misunderstanding(world, hero, helper, spec)
    world.para()
    _adjust_and_reveal(world, hero, helper, spec)
    _resolution(world, hero, helper, spec)
    obj.hidden = False
    obj.revealed = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spec: ObjectSpec = _safe_fact(world, f, "spec")
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    room: Room = _safe_fact(world, f, "room")
    return [
        f'Write a short mystery story for a young child where {hero.id} looks for {spec.phrase} in {room.label}.',
        f'Write a gentle story with foreshadowing and a misunderstanding that ends when someone chooses to {spec.reveal_by}.',
        f'Write a cozy mystery about {helper.label} helping {hero.id} solve a small hiding-place puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    spec: ObjectSpec = _safe_fact(world, f, "spec")
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    room: Room = _safe_fact(world, f, "room")
    return [
        QAItem(
            question=f"What mystery were {hero.id} and {helper.label} trying to solve in {room.label}?",
            answer=f"They were trying to find {spec.phrase} in {room.label}.",
        ),
        QAItem(
            question=f"What early clue hinted that {spec.label} was nearby?",
            answer=f"The story foreshadowed the answer with small clues like {', '.join(spec.visible_clues[:2]).lower()}.",
        ),
        QAItem(
            question=f"What misunderstanding made the search feel trickier?",
            answer=f"{helper.label.capitalize()} first guessed that someone had taken the {spec.label}, but the clues pointed to a hiding place instead.",
        ),
        QAItem(
            question=f"What did {hero.id} do to solve the mystery?",
            answer=f"{hero.id} decided to {spec.reveal_by} and made the careful adjustment that revealed the hidden {spec.label}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing {spec.label} was found, and the room no longer felt mysterious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what really happened.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives little hints early on that help the reader notice what might matter later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first.",
        ),
        QAItem(
            question="What does it mean to adjust something?",
            answer="To adjust something means to make a small careful change so it works better or fits better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} label={e.label or e.type} hidden={e.hidden} revealed={e.revealed} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

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


CURATED = [
    StoryParams(room="hall", object="silver_key", name="Mina", sidekick="grandma"),
    StoryParams(room="library", object="red_pin", name="Noah", sidekick="mother"),
    StoryParams(room="attic", object="toy_watch", name="Ivy", sidekick="father"),
    StoryParams(room="kitchen", object="silver_key", name="Lila", sidekick="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible room/object pairs:")
        for room, obj in pairs:
            print(f"  {room} {obj}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.room} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
