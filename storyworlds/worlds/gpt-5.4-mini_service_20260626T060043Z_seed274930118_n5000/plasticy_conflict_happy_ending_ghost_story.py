#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plasticy_conflict_happy_ending_ghost_story.py
===============================================================================================================

A small standalone story world for a gentle ghost-story premise with a
plasticy object, a visible conflict, and a happy ending.

Premise:
- A child visits a quiet old house and meets a shy ghost.
- The child loves a plasticy toy that makes a sharp little clatter.
- The ghost fears the noise will scare away the calm of the house.
- They disagree, then find a kinder way to play together.

The story is driven by simulated state:
- physical meters: noise, glow, chill, dust, comfort, tidy
- emotional memes: curiosity, worry, courage, friendship, conflict, relief

The prose is written from the evolving state, not from a frozen template.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False
    spooky: bool = False

    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    id: str
    name: str
    dim: str
    echoes: bool = False
    still: bool = False
    allows: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    kind: str
    kind_tag: str = "plasty"
    noisy: bool = True
    gentle_fix: str = "wrap it in a soft cloth"
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
    place: str
    prize: str
    child_name: str
    child_type: str
    parent_type: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone
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


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = meter(ent, key) + amount


def add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def place_line(place: Place) -> str:
    if place.id == "attic":
        return "The old attic was dim and still, with moonlight slipping through one small window."
    if place.id == "hallway":
        return "The hallway was long and quiet, with the floorboards giving tiny whispers under each step."
    if place.id == "porch":
        return "The porch was calm under the night sky, and the rails shone pale in the moonlight."
    return f"{place.name.capitalize()} was quiet, and the air felt like it was holding its breath."


def prize_risk(prize: Prize, place: Place) -> bool:
    return prize.noisy and place.echoes


def reasonableness_gate(place: Place, prize: Prize) -> bool:
    return prize_risk(prize, place)


def predict_conflict(world: World, child: Entity, ghost: Entity, prize: Prize) -> dict:
    sim = world.copy()
    _touch_prize(sim, sim.get(child.id), sim.get(prize.id), narrate=False)
    return {
        "noise": meter(sim.get(prize.id), "noise"),
        "conflict": meter(sim.get(ghost.id), "conflict"),
        "relief": meter(sim.get(ghost.id), "relief"),
    }


def _touch_prize(world: World, child: Entity, prize: Entity, narrate: bool = True) -> None:
    add_meter(prize, "noise", 1.0)
    add_meter(child, "delight", 1.0)
    if prize.noisy:
        for ent in world.characters():
            if ent.type == "ghost":
                add_meme(ent, "worry", 1.0)
                add_meme(ent, "conflict", 1.0)
    if narrate and prize.noisy:
        world.say(f"The little {prize.label} made a plasticy clack that carried through the room.")


def _soften_noise(world: World, prize: Entity) -> None:
    if meter(prize, "noise") >= THRESHOLD:
        add_meter(prize, "noise", -0.5)
        add_meter(prize, "quiet", 1.0)


def _resolve_ghost(world: World, ghost: Entity) -> None:
    if ghost.memes.get("conflict", 0.0) >= THRESHOLD:
        add_meme(ghost, "relief", 1.0)
        ghost.memes["conflict"] = 0.0


def introduce(world: World, child: Entity, ghost: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved quiet adventures and tiny surprises."
    )
    world.say(
        f"In the old house, {ghost.label} was a shy ghost who drifted near the rafters and listened to every sound."
    )
    world.say(
        f"{child.id} carried a {prize.phrase}, because {child.pronoun('possessive')} favorite things always seemed to be made for play."
    )


def desire(world: World, child: Entity, prize: Entity) -> None:
    add_meme(world.get(child.id), "curiosity", 1.0)
    world.say(
        f"{child.id} wanted to tap the {prize.label} and hear its little plasticy click bounce around the room."
    )


def warning(world: World, ghost: Entity, prize: Entity, place: Place) -> bool:
    pred = predict_conflict(world, world.get(world.facts["child"].id), ghost, prize)
    if pred["noise"] < THRESHOLD:
        return False
    ghost.memes["worry"] = ghost.memes.get("worry", 0.0) + 1.0
    world.say(
        f'"Please be gentle," {ghost.id} said. "That {prize.label} sounds too bright for this sleepy place."'
    )
    return True


def conflict_beats(world: World, child: Entity, ghost: Entity, prize: Entity) -> None:
    add_meme(child, "stubbornness", 1.0)
    add_meme(ghost, "conflict", 1.0)
    world.say(
        f"{child.id} frowned and hugged the {prize.label} closer, because the click sounded fun."
    )
    world.say(
        f"{ghost.id} floated back a little, and the room felt colder for a moment."
    )


def compromise(world: World, child: Entity, ghost: Entity, prize: Entity, place: Place) -> None:
    world.say(
        f"Then {child.id} looked at the moonlit floor and thought of a kinder way."
    )
    world.say(
        f"{child.id} used {PrizeRegistry[prize.id].gentle_fix} so the little noise would not chase away the calm."
    )
    _soften_noise(world, prize)
    add_meme(child, "courage", 1.0)
    add_meme(ghost, "hope", 1.0)
    world.say(
        f"{ghost.id} drifted closer, and together they carried the toy to the quiet {place.name}."
    )


def happy_ending(world: World, child: Entity, ghost: Entity, prize: Entity) -> None:
    _resolve_ghost(world, ghost)
    add_meme(child, "friendship", 1.0)
    add_meme(ghost, "friendship", 1.0)
    world.say(
        f"At last, the {prize.label} made only a soft little patter, and {ghost.id} smiled like a lantern in fog."
    )
    world.say(
        f"{child.id} laughed, {ghost.id} smiled, and the plasticy toy became a shared secret instead of a worry."
    )
    world.say(
        f"By the end, the old house felt warm and kind, and the moonlight on the floor looked almost like silver confetti."
    )


def tell(place: Place, prize: Prize, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ghost = world.add(Entity(id="Glim", kind="character", type="ghost", label="Glim"))
    toy = world.add(Entity(id=prize.id, kind="thing", type=prize.kind, label=prize.label, phrase=prize.phrase))
    toy.meters["noise"] = 0.0
    ghost.meters["chill"] = 1.0
    world.facts = {"child": child, "parent": parent, "ghost": ghost, "toy": toy, "prize": prize, "place": place}

    introduce(world, child, ghost, toy)
    world.para()
    world.say(place_line(place))
    desire(world, child, toy)
    warning(world, ghost, toy, place)
    conflict_beats(world, child, ghost, toy)
    world.para()
    compromise(world, child, ghost, toy, place)
    happy_ending(world, child, ghost, toy)
    return world


PLACE_REGISTRY = {
    "attic": Place(id="attic", name="the attic", dim="dim", echoes=True, still=True, allows={"toy", "ghost"}),
    "hallway": Place(id="hallway", name="the hallway", dim="long", echoes=True, still=True, allows={"toy", "ghost"}),
    "porch": Place(id="porch", name="the porch", dim="open", echoes=False, still=True, allows={"toy", "ghost"}),
}

PrizeRegistry = {
    "ball": Prize(id="ball", label="ball", phrase="a small plasticy ball", kind="ball", gentle_fix="wrap it in a soft cloth"),
    "duck": Prize(id="duck", label="duck", phrase="a bright plasticy duck", kind="duck", gentle_fix="set it on a towel"),
    "train": Prize(id="train", label="train", phrase="a little plasticy toy train", kind="train", gentle_fix="lay it on a soft blanket"),
}

CHILD_NAMES = ["Mina", "Toby", "Nina", "Ezra", "Ivy", "Leo"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father", "grown-up"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACE_REGISTRY.items():
        for tid, prize in PrizeRegistry.items():
            if reasonableness_gate(place, prize):
                out.append((pid, tid))
    return out


def explain_rejection(place: Place, prize: Prize) -> str:
    return (
        f"(No story: {prize.label} is supposed to make a tiny plasticy clack, "
        f"but {place.name} is too still for that conflict to matter. "
        f"Choose a place with echoes, like the attic or hallway.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost story world with a plasticy object, conflict, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--prize", choices=PrizeRegistry)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if getattr(args, "place", None) and getattr(args, "prize", None):
        place = PLACE_REGISTRY[getattr(args, "place", None)]
        prize = PrizeRegistry[getattr(args, "prize", None)]
        if not reasonableness_gate(place, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [(p, t) for p, t in valid_combos()
              if getattr(args, "place", None) in (None, p) and getattr(args, "prize", None) in (None, t)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(CHILD_TYPES)
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, prize=prize, child_name=name, child_type=gender, parent_type=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    prize = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short ghost story for a young child that uses the word "plasticy" and takes place in {place.name}.',
        f"Tell a gentle story where {child.id} wants to play with a {prize.phrase}, but a shy ghost worries about the noise.",
        f"Write a spooky-but-kind story about a toy, a disagreement, and a happy ending in {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    prize = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who wanted to play with the {prize.label} in {place.name}?",
            answer=f"{child.id} wanted to play with the {prize.label}, because it looked fun and plasticy.",
        ),
        QAItem(
            question=f"Why did {ghost.id} worry about the toy?",
            answer=f"{ghost.id} worried because the {prize.label} made a sharp little noise in the quiet old house.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {child.id} and {ghost.id} sharing the toy in a calmer way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word plasticy mean here?",
            answer="It means made of plastic or like plastic, with a smooth, shiny, lightweight feel.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story about a ghost or a spooky place, but it can still be gentle or kind.",
        ),
        QAItem(
            question="Why can a noisy toy cause conflict in a quiet place?",
            answer="Because a loud toy can make a shy listener worry that the peaceful feeling will be broken.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        if e.kind == "character" or e.id in PrizeRegistry:
            lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(attic). place(hallway). place(porch).
echoes(attic). echoes(hallway).
prize(ball). prize(duck). prize(train).
noisy(ball). noisy(duck). noisy(train).

risk(P, T) :- place(P), prize(T), noisy(T), echoes(P).
valid(P, T) :- risk(P, T).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("place", pid))
        if PLACE_REGISTRY[pid].echoes:
            lines.append(asp.fact("echoes", pid))
    for tid in PrizeRegistry:
        lines.append(asp.fact("prize", tid))
        if PrizeRegistry[tid].noisy:
            lines.append(asp.fact("noisy", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACE_REGISTRY[params.place], PrizeRegistry[params.prize],
                 params.child_name, params.child_type, params.parent_type)
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
        print(format_qa(sample))


CURATED = [
    StoryParams(place="attic", prize="train", child_name="Mina", child_type="girl", parent_type="mother"),
    StoryParams(place="hallway", prize="duck", child_name="Toby", child_type="boy", parent_type="father"),
    StoryParams(place="attic", prize="ball", child_name="Ivy", child_type="girl", parent_type="grown-up"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible place/prize combos:\n")
        for p, t in pairs:
            print(f"  {p:8} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.prize} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
