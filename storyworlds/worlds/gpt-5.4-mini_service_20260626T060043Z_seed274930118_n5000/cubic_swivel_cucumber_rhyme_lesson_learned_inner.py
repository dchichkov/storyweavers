#!/usr/bin/env python3
"""
A standalone storyworld: a small adventure about a cubic puzzle, a swivel seat,
and a cucumber that should not be forced into the wrong shape.

Premise seed:
- cubic
- swivel
- cucumber

Narrative instruments:
- Rhyme
- Lesson Learned
- Inner Monologue

The world is a compact classical simulation:
- typed entities with meters and memes
- a simple physical setup in a room
- a risky attempt to carry or store a cucumber in a cubic crate
- a swivel chair that helps the hero notice the real solution
- an ending that proves what changed

The story reads like an adventure: a child sets out with a goal, meets a small
problem, thinks through it, and returns with a better plan.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

ROOMS = {
    "workshop": "the workshop",
    "kitchen": "the kitchen",
    "shed": "the shed",
}

NAMES = ["Mina", "Toby", "Iris", "Pip", "Nico", "Lena", "Owen", "Ruby"]
ADJ = ["curious", "brave", "quick", "gentle", "spirited", "clever"]

# ---------------------------------------------------------------------------
# Entities
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    inside: Optional[str] = None
    region: str = ""
    shape: str = ""
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    chair: object | None = None
    crate: object | None = None
    cucumber: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["dust", "scrape", "wet", "carefulness", "worry", "joy", "resolve", "conflict"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Room:
    name: str
    place: str
    has_swivel_chair: bool = False
    has_cubic_crate: bool = False
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
    room: Room
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
        import copy as _copy
        clone = World(room=self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Params
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


@dataclass
class StoryParams:
    room: str
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


ROOM_REGISTRY = {
    "workshop": Room(name="workshop", place=ROOMS["workshop"], has_swivel_chair=True, has_cubic_crate=True),
    "kitchen": Room(name="kitchen", place=ROOMS["kitchen"], has_swivel_chair=False, has_cubic_crate=True),
    "shed": Room(name="shed", place=ROOMS["shed"], has_swivel_chair=True, has_cubic_crate=False),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(room: Room) -> bool:
    return room.has_swivel_chair and room.has_cubic_crate


def explain_rejection(room: Room) -> str:
    if not room.has_cubic_crate:
        return "(No story: the place needs a cubic crate for the cucumber adventure, but this room has none.)"
    if not room.has_swivel_chair:
        return "(No story: the adventure needs a swivel chair so the hero can rethink the plan, but this room has none.)"
    return "(No story: this setup is not reasonable.)"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    cube = world.get("crate")
    cucumber = world.get("cucumber")
    if hero.memes["resolve"] < THRESHOLD:
        return out
    if cube.inside == "mud" or cucumber.inside == "mud":
        sig = ("dust",)
        if sig not in world.fired:
            world.fired.add(sig)
            cube.meters["dust"] += 1
            cucumber.meters["dust"] += 1
            out.append("A little dust clung to the cubic crate and the cucumber.")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    cucumber = world.get("cucumber")
    cube = world.get("crate")
    if hero.memes["worry"] < THRESHOLD:
        return []
    if cucumber.inside == cube.id and cube.shape == "cubic":
        sig = ("conflict",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_conflict, _r_dust):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if b != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, hero: Entity) -> dict:
    sim = world.copy()
    attempt_store(sim, sim.get("hero"), narrate=False)
    cucumber = sim.get("cucumber")
    crate = sim.get("crate")
    return {
        "safely_stored": cucumber.inside == crate.id and crate.meters["scrape"] < THRESHOLD,
        "conflict": sim.get("hero").memes["conflict"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def rhymed_line(action: str, object_word: str) -> str:
    return {
        "seek": f"{action} and peek, then the answer would speak.",
        "think": f"{action} and blink, then the plan found its link.",
        "move": f"{action} and groove, with a careful small move.",
    }.get(action, f"{action} in stride, with a bright-eyed guide and a rhyming ride about {object_word}.")


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes['trait_word']} adventurer who loved strange little puzzles."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had heard of a cucumber, a cubic crate, and a swivel chair waiting in {world.room.place}."
    )


def set_out(world: World, hero: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"One bright morning, {hero.id} marched into {world.room.place} with a plan to carry the cucumber safely."
    )
    world.say(rhymed_line("seek", "cucumber"))


def inner_monologue(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"Inside, {hero.pronoun('subject')} thought, \"A cucumber is long and smooth, but a cubic crate is boxy and tight.\""
    )
    world.say(
        f"\"If I force it, I may only make a mess,\" {hero.pronoun('subject')} thought, turning once in the swivel chair."
    )
    world.say(
        f"\"Maybe the best adventure is the one where I learn the shape of things.\""
    )


def attempt_store(world: World, hero: Entity, narrate: bool = True) -> None:
    cube = world.get("crate")
    cucumber = world.get("cucumber")
    if cube.shape != "cubic":
        pass
    hero.memes["worry"] += 1
    cucumber.inside = cube.id
    cube.meters["scrape"] += 1
    if narrate:
        world.say(
            f"{hero.id} tried to press the cucumber into the cubic crate."
        )
        world.say(
            f"The corners looked stubborn, and the cucumber fit badly."
        )
    propagate(world, narrate=narrate)


def swivel_and_learn(world: World, hero: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} spun in the swivel chair, and the turning motion gave {hero.pronoun('object')} a new idea."
    )
    world.say(
        f"The child nodded. \"I was trying to make the cucumber match the crate. That was backwards.\""
    )
    world.say(
        f"Lesson learned: use the right container, not the wrong squeeze."
    )


def fix(world: World, hero: Entity) -> None:
    crate = world.get("crate")
    cucumber = world.get("cucumber")
    crate.meters["scrape"] = 0
    cucumber.inside = None
    cucumber.held_by = hero.id
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0
    world.say(
        f"{hero.id} lifted the cucumber out, found a wider basket, and set it there instead."
    )
    world.say(
        f"At once the cubic crate stayed neat, the cucumber stayed whole, and the room felt ready for the next adventure."
    )


def ending_image(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} smiled beside the swivel chair, the cucumber in the right basket, and the cubic crate resting proudly nearby."
    )


# ---------------------------------------------------------------------------
# Build and generate
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    room = ROOM_REGISTRY[params.room]
    world = World(room=room)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    cucumber = world.add(Entity(
        id="cucumber",
        kind="thing",
        type="cucumber",
        label="cucumber",
        phrase="a fresh cucumber",
        movable=True,
        meters={"dust": 0.0, "scrape": 0.0, "wet": 0.0, "carefulness": 0.0, "worry": 0.0, "joy": 0.0, "resolve": 0.0, "conflict": 0.0},
        memes={"trait_word": params.trait, "worry": 0.0, "joy": 0.0, "resolve": 0.0, "conflict": 0.0},
    ))
    crate = world.add(Entity(
        id="crate",
        kind="thing",
        type="crate",
        label="cubic crate",
        phrase="a cubic crate",
        shape="cubic",
        movable=False,
    ))
    chair = world.add(Entity(
        id="chair",
        kind="thing",
        type="chair",
        label="swivel chair",
        phrase="a swivel chair",
        movable=False,
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="basket",
        phrase="a wider basket",
        movable=False,
    ))
    world.facts.update(hero=hero, cucumber=cucumber, crate=crate, chair=chair, basket=basket, room=room)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get("hero")
    intro(world, hero)
    world.para()
    set_out(world, hero)
    inner_monologue(world, hero)
    attempt_store(world, hero)
    world.para()
    swivel_and_learn(world, hero)
    fix(world, hero)
    ending_image(world, hero)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a short adventure story for a child named {hero.label} about a cucumber, a cubic crate, and a swivel chair.",
        "Tell a child-facing story with an inner monologue where the hero realizes a lesson about matching shapes.",
        "Write an adventure where the ending proves the hero stopped forcing the wrong object into the wrong container.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    cucumber = _safe_fact(world, f, "cucumber")
    crate = _safe_fact(world, f, "crate")
    room = _safe_fact(world, f, "room")
    return [
        QAItem(
            question=f"What was {hero.label} trying to do with the cucumber in {room.place}?",
            answer=f"{hero.label} was trying to put the cucumber into the cubic crate, but that shape was a poor fit.",
        ),
        QAItem(
            question="What did the swivel chair help the hero realize?",
            answer="The swivel chair helped the hero realize that forcing a cucumber into a cubic crate was the wrong plan.",
        ),
        QAItem(
            question="What was the lesson learned in the story?",
            answer="The lesson learned was to use the right container instead of squeezing things into the wrong shape.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="At the end, the cucumber went into a wider basket, the cubic crate stayed neat, and the hero felt proud of the better choice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swivel chair?",
            answer="A swivel chair is a chair that can turn around, which makes it easy to spin and look in different directions.",
        ),
        QAItem(
            question="What is a cucumber?",
            answer="A cucumber is a long green vegetable with a smooth skin and a fresh, crisp taste.",
        ),
        QAItem(
            question="What does cubic mean?",
            answer="Cubic means shaped like a cube, with straight sides and square faces.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the room has both a swivel chair and a cubic crate.
valid_room(R) :- room(R), has_swivel(R), has_crate(R).

% The adventure premise is reasonable only if the hero can learn by turning
% and can safely reroute the cucumber into a better container.
valid_story(R) :- valid_room(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOM_REGISTRY.items():
        lines.append(asp.fact("room", rid))
        if room.has_swivel_chair:
            lines.append(asp.fact("has_swivel", rid))
        if room.has_cubic_crate:
            lines.append(asp.fact("has_crate", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_rooms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_room/1."))
    return sorted(set(asp.atoms(model, "valid_room")))


def asp_verify() -> int:
    py = sorted((rid,) for rid, room in ROOM_REGISTRY.items() if valid_story(room))
    cl = asp_valid_rooms()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid rooms).")
        return 0
    print("MISMATCH between ASP and Python:")
    if set(py) - set(cl):
        print("  only in python:", sorted(set(py) - set(cl)))
    if set(cl) - set(py):
        print("  only in ASP:", sorted(set(cl) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: cubic, swivel, cucumber.")
    ap.add_argument("--room", choices=ROOM_REGISTRY.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=ADJ)
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
    valid_rooms = [rid for rid, room in ROOM_REGISTRY.items() if valid_story(room)]
    if getattr(args, "room", None):
        if getattr(args, "room", None) not in valid_rooms:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        room = getattr(args, "room", None)
    else:
        room = rng.choice(valid_rooms)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(ADJ)
    return StoryParams(room=room, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"room: {world.room.name} ({world.room.place})")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shape:
            bits.append(f"shape={e.shape}")
        if e.inside:
            bits.append(f"inside={e.inside}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(room="workshop", name="Mina", gender="girl", trait="curious"),
    StoryParams(room="shed", name="Toby", gender="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_room/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        rooms = asp_valid_rooms()
        print(f"{len(rooms)} valid rooms:")
        for (rid,) in rooms:
            print(f"  {rid}")
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
            header = f"### {p.name} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
