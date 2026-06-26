#!/usr/bin/env python3
"""
storyworlds/worlds/diameter_aggressive_rehearsal_cautionary_kindness_ghost_story.py
====================================================================================

A tiny, standalone storyworld about a cautious child, a stubborn rehearsal,
and a ghost who would rather bang than whisper.

Seed-tale premise:
- A child and a ghost meet in an old theater.
- They must rehearse a scene with a round silver mirror whose diameter matters.
- The ghost keeps getting aggressive and loud, which risks breaking the rehearsal.
- Kindness and caution turn the problem into a safer, gentler performance.

This world keeps the prose close to a classic ghost story: chilly rooms, soft
lamplight, creaking floorboards, a frightened-but-brave child, and a ghost who
needs care instead of scolding.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    ghost: object | None = None
    prop: object | None = None
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
    name: str
    dim: float
    kind: str = "theater"
    cold: bool = True
    echoes: bool = True
    affords: set[str] = field(default_factory=set)
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    diameter: float
    fragile: bool = False
    safe_radius: float = 0.0
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    charm: str
    loudness: float
    mess: str
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
class StoryParams:
    place: str
    action: str
    prop: str
    name: str
    gender: str
    age_word: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "caretaker": v.caretaker, "worn_by": v.worn_by, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        return clone


def _meter_get(d: dict[str, float], key: str) -> float:
    return float(d.get(key, 0.0))


def _inc_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = _meter_get(e.meters, key) + amt


def _inc_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = float(e.memes.get(key, 0.0)) + amt


def _set_meme(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    prop = world.entities.get("prop")
    if not ghost or not prop:
        return out
    if _meter_get(ghost.meters, "loudness") < THRESHOLD:
        return out
    sig = ("echo",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if _meter_get(ghost.meters, "aggression") >= THRESHOLD:
        _inc_meter(prop, "wobble", 1.0)
        _inc_meme(ghost, "frighten", 1.0)
        out.append("The room answered with a hard echo, and the old prop shivered on its stand.")
    else:
        out.append("The room answered softly, like it was listening.")
    return out


def _r_spoil_rehearsal(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    prop = world.entities.get("prop")
    child = world.entities.get("child")
    if not ghost or not prop or not child:
        return out
    if _meter_get(prop.meters, "wobble") < THRESHOLD:
        return out
    sig = ("spoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc_meme(child, "fear", 1.0)
    _inc_meme(child, "resolve", 1.0)
    out.append("The child saw the wobble and stood very still, thinking hard about what to do next.")
    return out


RULES: list[Callable[[World], list[str]]] = [_r_echo, _r_spoil_rehearsal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_rehearsal(world: World, ghost: Entity, action: Action, prop: Prop) -> dict:
    sim = world.copy()
    sim.get("ghost").meters["loudness"] = action.loudness
    sim.get("ghost").meters["aggression"] = 1.0 if action.id == "aggressive" else 0.0
    propagate(sim, narrate=False)
    wobble = sim.get("prop").meters.get("wobble", 0.0)
    return {"wobble": wobble >= THRESHOLD}


def setting_detail(place: Place) -> str:
    if place.cold:
        return f"The old theater was cold, and the curtains hung like dark trees."
    return f"The room was warm, but the walls still seemed to keep secrets."


def intro(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} {child.type} who loved quiet rooms and brave little mysteries."
    )
    world.say(
        f"In the old theater, {ghost.id} waited beside the stage, pale as candle smoke and just as restless."
    )


def love_rehearsal(world: World, child: Entity, action: Action) -> None:
    _inc_meme(child, "curiosity", 1.0)
    world.say(
        f"{child.id} loved the rehearsal because {action.charm}; every squeak of the floorboards felt like part of the tale."
    )


def bring_prop(world: World, child: Entity, prop: Prop) -> None:
    world.say(
        f"On the stage stood {prop.phrase}, and its {prop.kind} had a careful diameter of {prop.diameter:g} inches."
    )
    world.say(
        f"{child.id} had to keep the prop steady, because the smallest bump could make it drift off center."
    )


def want_to_act(world: World, ghost: Entity, action: Action) -> None:
    _inc_meme(ghost, "desire", 1.0)
    world.say(
        f"{ghost.id} wanted to {action.verb}, but the wish came out too sharp and too loud."
    )


def warn(world: World, child: Entity, ghost: Entity, action: Action, prop: Prop) -> None:
    pred = predict_rehearsal(world, ghost, action, prop)
    if pred["wobble"]:
        world.facts["predicted_wobble"] = True
        world.say(
            f'"If you rush like that," {child.id} said, "the prop will wobble and the scene will fall apart."'
        )
        _inc_meme(child, "caution", 1.0)


def ghost_pushes(world: World, ghost: Entity, action: Action) -> None:
    _inc_meter(ghost, "aggression", 1.0)
    _inc_meter(ghost, "loudness", action.loudness)
    _inc_meme(ghost, "agitated", 1.0)
    world.say(f"{ghost.id} tried to {action.rush}, and the words rattled like a chain in the dark.")


def kind_hand(world: World, child: Entity, ghost: Entity) -> None:
    _inc_meme(child, "kindness", 1.0)
    _set_meme(ghost, "aggression", 0.0)
    _inc_meter(ghost, "loudness", -0.5)
    world.say(
        f"Instead of scolding, {child.id} held up a small lantern and spoke kindly, so the room would not feel hunted."
    )


def change_plan(world: World, child: Entity, ghost: Entity, action: Action, prop: Prop) -> None:
    world.say(
        f'"Let us rehearse the quiet way first," {child.id} said. "Then you can {action.verb} after we mark the circle."'
    )
    _inc_meme(ghost, "relief", 1.0)
    _set_meme(ghost, "aggression", 0.0)
    _inc_meter(prop, "stability", 1.0)


def finish(world: World, child: Entity, ghost: Entity, action: Action, prop: Prop) -> None:
    world.say(
        f"So they moved in a slow ring around the prop, counting the turns by moonlight."
    )
    world.say(
        f"{ghost.id} kept the loudness low, {child.id} kept the circle steady, and the rehearsal ended with the prop exactly where it belonged."
    )
    world.say(
        f"At the end, the theater was still cold, but it felt safer; even the shadows seemed to bow instead of stare."
    )


PLACEs = {
    "old theater": Place(name="old theater", dim=48.0, affords={"aggressive", "rehearsal"}),
    "attic stage": Place(name="attic stage", dim=22.0, affords={"aggressive", "rehearsal"}),
}

ACTIONS = {
    "aggressive": Action(
        id="aggressive",
        verb="growl through the lines",
        gerund="growling through the lines",
        rush="slam the cue card down",
        risk="shaking the prop loose",
        charm="it made the ghost sound powerful for a moment",
        loudness=1.5,
        mess="wobble",
        tags={"aggressive", "ghost"},
    ),
    "rehearsal": Action(
        id="rehearsal",
        verb="rehearse the scene",
        gerund="rehearsing the scene",
        rush="hurry through the moonlit marks",
        risk="making the scene too fast",
        charm="it let the child and ghost practice until the fear felt smaller",
        loudness=0.4,
        mess="steady",
        tags={"rehearsal", "cautionary", "kindness"},
    ),
}

PROPS = {
    "mirror": Prop(
        id="mirror",
        label="round mirror",
        phrase="a round silver mirror",
        kind="mirror",
        diameter=18.0,
        fragile=True,
        safe_radius=2.0,
    ),
    "lantern": Prop(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern",
        kind="lantern",
        diameter=10.0,
        fragile=True,
        safe_radius=1.5,
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lena", "Ivy", "Hazel"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Cal"]
TRAITS = ["cautious", "brave", "gentle", "careful", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACEs.values():
        for action in ACTIONS.values():
            for prop in PROPS.values():
                if place.name in {"old theater", "attic stage"} and action.id in {"aggressive", "rehearsal"}:
                    combos.append((place.name, action.id, prop.id))
    return combos


def explain_invalid(action: Action, prop: Prop) -> str:
    return (
        f"(No story: {action.verb} would not safely fit with {prop.label}; "
        f"this world only tells tales where the child can answer danger with care.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that includes the word "{f["action"].id}" and the idea of a careful rehearsal.',
        f'Tell a chilly but gentle story where {f["child"].id} helps a ghost keep a prop steady by paying attention to its diameter.',
        f'Write a short cautionary story with kindness in it, set in an old theater with a ghost and a round mirror.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    ghost: Entity = _safe_fact(world, f, "ghost")
    prop: Prop = _safe_fact(world, f, "prop")
    action: Action = _safe_fact(world, f, "action")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {child.id} trying to do in the old theater?",
            answer=f"{child.id} was trying to help {ghost.id} rehearse the scene without letting the round mirror wobble."
        ),
        QAItem(
            question=f"Why did {child.id} worry when {ghost.id} got aggressive?",
            answer=(
                f"{child.id} worried because the ghost's loud rush could shake the prop off center. "
                f"The mirror's diameter mattered, so even a small wobble could spoil the rehearsal."
            ),
        ),
        QAItem(
            question=f"How did kindness change the rehearsal at {place.name}?",
            answer=(
                f"{child.id} answered with kindness instead of fear, and that made {ghost.id} quieter. "
                f"Then they could keep the scene steady and finish the rehearsal safely."
            ),
        ),
        QAItem(
            question=f"What was special about the prop in the story?",
            answer=(
                f"It was {prop.phrase}, and its diameter was {prop.diameter:g} inches. "
                f"The circle had to stay centered for the rehearsal to work."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a diameter?",
            answer="A diameter is a straight line from one side of a circle to the other side through the middle."
        ),
        QAItem(
            question="What does aggressive mean?",
            answer="Aggressive means acting rough, pushy, or too forceful."
        ),
        QAItem(
            question="What is a rehearsal?",
            answer="A rehearsal is practice for a play, song, or show before the real performance."
        ),
        QAItem(
            question="Why is kindness useful in a scary room?",
            answer="Kindness helps everyone calm down, listen better, and make safer choices."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def tell(place: Place, action: Action, prop_cfg: Prop, name: str, gender: str, age_word: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, traits=[age_word, "cautious"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", traits=["restless"]))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type=prop_cfg.kind,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        meters={"stability": 1.0},
    ))

    world.say(f"{name} was a {age_word} {gender} who did not mind old halls if the light was kind.")
    world.say(setting_detail(place))
    intro(world, child, ghost)
    world.para()
    love_rehearsal(world, child, action)
    bring_prop(world, child, prop_cfg)
    world.say(f"The only trouble was that {ghost.id} could turn {action.id} into something far too sharp.")
    world.para()
    want_to_act(world, ghost, action)
    warn(world, child, ghost, action, prop_cfg)
    ghost_pushes(world, ghost, action)
    propagate(world, narrate=True)
    kind_hand(world, child, ghost)
    change_plan(world, child, ghost, action, prop_cfg)
    propagate(world, narrate=True)
    world.para()
    finish(world, child, ghost, action, prop_cfg)

    world.facts.update(
        child=child,
        ghost=ghost,
        prop=prop_cfg,
        action=action,
        place=place,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world about caution, kindness, and rehearsal.")
    ap.add_argument("--place", choices=PLACEs)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--age-word", choices=TRAITS)
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
    if getattr(args, "action", None) and getattr(args, "prop", None):
        if getattr(args, "action", None) == "aggressive" and getattr(args, "prop", None) not in PROPS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACEs))
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    age_word = getattr(args, "age_word", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prop=prop, name=name, gender=gender, age_word=age_word)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACEs[params.place], _safe_lookup(ACTIONS, params.action), _safe_lookup(PROPS, params.prop), params.name, params.gender, params.age_word)
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


ASP_RULES = r"""
place(old_theater).
place(attic_stage).

action(aggressive).
action(rehearsal).

prop(mirror).
prop(lantern).

compatible(P,A,R) :- place(P), action(A), prop(R).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACEs:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    atoms = sorted(set(asp.atoms(model, "compatible")))
    py = sorted(valid_combos())
    py2 = [(a, b, c) for (a, b, c) in py]
    if set(atoms) != set(py2):
        print("MISMATCH between ASP and Python combos.")
        print("asp:", atoms)
        print("py:", py2)
        return 1
    print(f"OK: ASP matches Python ({len(py2)} combos).")
    return 0


CURATED = [
    StoryParams(place="old theater", action="aggressive", prop="mirror", name="Mira", gender="girl", age_word="cautious"),
    StoryParams(place="attic stage", action="rehearsal", prop="lantern", name="Eli", gender="boy", age_word="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
