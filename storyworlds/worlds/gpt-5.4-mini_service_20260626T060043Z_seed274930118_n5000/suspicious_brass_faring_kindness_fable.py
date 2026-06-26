#!/usr/bin/env python3
"""
storyworlds/worlds/suspicious_brass_faring_kindness_fable.py
=============================================================

A tiny fable-style storyworld about suspicion, a brass object, and the way
kindness helps everyone fare better.

Seed tale used to build the simulation:
---
A small fox found a brass bell in the grass and felt suspicious of it.
The bell looked polished, but it had a strange knot tied to its loop, so the fox
feared it might be a trick. A mouse arrived and offered to help. Instead of
mocking the fox, the mouse used kindness: it listened, tested the bell safely,
and discovered that the bell was meant to call the village helpers together for
bread. The fox felt ashamed for doubting so quickly, then grateful. In the end,
the fox shared the bread, the mouse smiled, and the village fared better
because kindness had led the way.

World shape:
---
- Physical meters: shine, rust, weight, distance, carried
- Emotional memes: suspicion, kindness, trust, relief, shame, gratitude, joy

Narrative beats:
---
1. Setup: a fable-like village scene and a suspicious brass object.
2. Tension: the fox fears the object is a trick and hesitates.
3. Turn: a kind helper offers a safer test instead of scolding.
4. Resolution: the truth is revealed, and the village fares better.

The prose is generated from simulated state; it is not a frozen paragraph with
swapped nouns.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    fox: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "girl", "mother", "woman"}
        male = {"fox", "boy", "father", "man"}
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
class Place:
    name: str
    outdoors: bool = True
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    suspicious: bool = False
    can_call: bool = False
    guards: set[str] = field(default_factory=set)
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
class SceneDef:
    id: str
    action: str
    verb: str
    danger: str
    outcome: str
    keyword: str
    turn: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _nget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _inc_meme(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def scene_intro(place: Place, scene: SceneDef) -> str:
    if place.name == "the village lane":
        return "Along the village lane, the morning was quiet and the dew still clung to the grass."
    if place.name == "the market green":
        return "At the market green, the stalls had only just opened, and the air smelled of warm bread."
    return f"At {place.name}, the day was plain and bright, as if it were waiting for a lesson."


def object_detail(obj: ObjectDef) -> str:
    if obj.material == "brass":
        return "It shone gold in the sun, but its ring gave off a hollow little note."
    return f"It looked ordinary, though it waited there as if it knew a secret."


def predict_test(world: World, scene: SceneDef, fox_id: str, helper_id: str, obj_id: str) -> dict:
    sim = world.copy()
    fox = sim.get(fox_id)
    helper = sim.get(helper_id)
    obj = sim.get(obj_id)
    _inc_meme(fox, "suspicion", 1)
    _inc_meme(helper, "kindness", 1)
    _inc_meter(obj, "handled", 1)
    if obj.memes.get("truth_seen", 0.0) < THRESHOLD:
        _inc_meme(fox, "trust", 1)
    return {
        "safe": obj.memes.get("danger", 0.0) < THRESHOLD,
        "fare_better": _nget(helper, "kindness") + _nget(fox, "trust"),
    }


def setup(world: World, fox: Entity, helper: Entity, obj: Entity, scene: SceneDef) -> None:
    world.say(scene_intro(world.place, scene))
    world.say(
        f"{fox.id} was a little fox with a sharp nose for trouble, and {helper.id} was a mouse who liked to help."
    )
    world.say(
        f"One morning, {fox.id} found {obj.phrase} beside the lane. {object_detail(world.get(obj.id))}"
    )
    _inc_meme(fox, "suspicion", 1)
    world.facts["scene"] = scene
    world.facts["fox"] = fox
    world.facts["helper"] = helper
    world.facts["obj"] = obj


def fear(world: World, fox: Entity, obj: Entity, scene: SceneDef) -> None:
    _inc_meme(fox, "suspicion", 1)
    _inc_meme(fox, "shame", 0.5)
    world.say(
        f"{fox.id} stared at the {obj.label} and felt suspicious. "
        f"{fox.pronoun().capitalize()} feared the brass thing might be a trick."
    )
    world.say(f"{fox.id} kept back, because {scene.danger} seemed close in the little fox's mind.")


def kindness_offer(world: World, helper: Entity, fox: Entity, obj: Entity, scene: SceneDef) -> None:
    _inc_meme(helper, "kindness", 1)
    _inc_meme(fox, "trust", 1)
    world.say(
        f"{helper.id} came near without laughing. {helper.pronoun().capitalize()} said, "
        f'"Let us be careful together. Kindness can test a mystery without causing harm."'
    )
    world.say(
        f"{helper.id} used a twig to nudge the {obj.label} in a safe way, so they could see what it did."
    )


def reveal(world: World, fox: Entity, helper: Entity, obj: Entity, scene: SceneDef) -> None:
    _inc_meter(obj, "handled", 1)
    obj.meters["sound"] = 1.0
    obj.meters["used"] = 1.0
    obj.memes["truth_seen"] = 1.0
    _set_meme(fox, "suspicion", 0.0)
    _inc_meme(fox, "relief", 1.0)
    _inc_meme(fox, "gratitude", 1.0)
    world.say(
        f"At last, the {obj.label} rang clear and bright. It was not a trick at all; it was meant to call the helpers together."
    )
    world.say(
        f"The sound traveled down the lane, and the village fared better because the bread was shared instead of hidden away."
    )


def apology(world: World, fox: Entity, helper: Entity, obj: Entity) -> None:
    _inc_meme(fox, "shame", 1.0)
    _inc_meme(fox, "gratitude", 1.0)
    _inc_meme(helper, "joy", 1.0)
    world.say(
        f"{fox.id} lowered {fox.pronoun('possessive')} ears and said sorry for doubting so quickly."
    )
    world.say(
        f"{helper.id} only smiled. {helper.pronoun().capitalize()} said that a kind test was worth more than a harsh guess."
    )


def ending_image(world: World, fox: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f"In the end, {fox.id} carried the {obj.label} beside {helper.id}, and the two of them went to share the bread with the village."
    )


def run_story(place: Place, scene: SceneDef, obj: ObjectDef, fox_name: str, helper_name: str) -> World:
    world = World(place)
    fox = world.add(Entity(id=fox_name, kind="character", type="fox", traits=["cautious", "small"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="mouse", traits=["kind", "swift"]))
    brass = world.add(
        Entity(
            id=obj.id,
            type="thing",
            label=obj.label,
            phrase=obj.phrase,
            owner=helper.id,
            caretaker=helper.id,
            meters={"shine": 1.0, "handled": 0.0},
            memes={"truth_seen": 0.0},
        )
    )

    setup(world, fox, helper, brass, scene)
    world.para()
    fear(world, fox, brass, scene)
    kindness_offer(world, helper, fox, brass, scene)
    world.para()
    reveal(world, fox, helper, brass, scene)
    apology(world, fox, helper, brass)
    ending_image(world, fox, helper, brass)

    world.facts.update(fox=fox, helper=helper, obj=brass, scene=scene, place=place)
    return world


PLACE_REGISTRY = {
    "lane": Place(name="the village lane", outdoors=True, affords={"bell"}),
    "green": Place(name="the market green", outdoors=True, affords={"bell"}),
    "orchard": Place(name="the orchard edge", outdoors=True, affords={"bell"}),
}

OBJECT_REGISTRY = {
    "bell": ObjectDef(
        id="bell",
        label="brass bell",
        phrase="a small brass bell",
        material="brass",
        purpose="to call helpers together",
        suspicious=True,
        can_call=True,
        guards={"silence"},
    ),
}

SCENE_REGISTRY = {
    "bell": SceneDef(
        id="bell",
        action="find",
        verb="ring the bell",
        danger="a hidden trap",
        outcome="the village hears the call",
        keyword="brass",
        turn="kindness turns suspicion into trust",
        tags={"suspicious", "brass", "kindness", "fable", "faring"},
    ),
}

FOX_NAMES = ["Tobin", "Milo", "Ash", "Reed", "Perrin", "Clover"]
MOUSE_NAMES = ["Nip", "Mara", "Pip", "Lina", "Dot", "Sela"]
TRAITS = ["cautious", "wary", "gentle", "thoughtful", "small"]


@dataclass
class StoryParams:
    place: str
    scene: str
    obj: str
    fox_name: str
    helper_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable storyworld about suspicious brass and kindness."
    )
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--scene", choices=SCENE_REGISTRY)
    ap.add_argument("--object", dest="obj", choices=OBJECT_REGISTRY)
    ap.add_argument("--fox-name")
    ap.add_argument("--helper-name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACE_REGISTRY))
    scene = getattr(args, "scene", None) or rng.choice(list(SCENE_REGISTRY))
    obj = getattr(args, "obj", None) or rng.choice(list(OBJECT_REGISTRY))
    if place not in PLACE_REGISTRY or obj not in OBJECT_REGISTRY or scene not in SCENE_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if obj != "bell":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    fox_name = getattr(args, "fox_name", None) or rng.choice(FOX_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(MOUSE_NAMES)
    if fox_name == helper_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, scene=scene, obj=obj, fox_name=fox_name, helper_name=helper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fox = _safe_fact(world, f, "fox")
    helper = _safe_fact(world, f, "helper")
    obj = _safe_fact(world, f, "obj")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write a short fable for a child about {fox.id}, a suspicious fox, and {obj.phrase}.',
        f"Tell a gentle story where {helper.id} shows kindness after {fox.id} fears the brass bell is a trick.",
        f'Write a small moral tale in which "kindness" helps a fox and a mouse make the village fare better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fox = _safe_fact(world, f, "fox")
    helper = _safe_fact(world, f, "helper")
    obj = _safe_fact(world, f, "obj")
    scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"Why was {fox.id} suspicious of the {obj.label}?",
            answer=(
                f"{fox.id} was suspicious because the {obj.label} was brass, looked strange, and seemed like it might be a trick."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} show kindness to {fox.id}?",
            answer=(
                f"{helper.id} stayed calm, did not laugh, and helped test the {obj.label} safely so {fox.id} would not get hurt."
            ),
        ),
        QAItem(
            question=f"What happened after the {obj.label} rang out?",
            answer=(
                f"The bell called the helpers together, and the village fared better because the bread was shared openly."
            ),
        ),
        QAItem(
            question=f"What changed in {fox.id} by the end of the story?",
            answer=(
                f"{fox.id} moved from suspicion to relief and gratitude, and {fox.id} apologized for doubting the kind helper."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is brass?",
            answer="Brass is a shiny yellow metal often used for bells, coins, and decorations.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring instead of mean or cruel.",
        ),
        QAItem(
            question="What does it mean to fare well?",
            answer="To fare well means to do well or get along in a good way.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A brass object is suspicious when its suspicious flag is present.
suspicious_obj(O) :- object(O), suspicious(O).

% Kindness resolves a suspicious encounter when a helper offers a safe test.
safe_test(H, F, O) :- helper(H), fox(F), object(O), kindness(H), suspicious_obj(O).
resolved(F, O) :- safe_test(_, F, O).

% The village fares better if the bell is meant to call helpers and the truth is seen.
faring_better :- resolved(_, O), can_call(O), brass(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SCENE_REGISTRY.items():
        lines.append(asp.fact("scene", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for oid, o in OBJECT_REGISTRY.items():
        lines.append(asp.fact("object", oid))
        if o.material == "brass":
            lines.append(asp.fact("brass", oid))
        if o.suspicious:
            lines.append(asp.fact("suspicious", oid))
        if o.can_call:
            lines.append(asp.fact("can_call", oid))
    lines.append(asp.fact("kindness", "present"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("fox", "fox"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2.\n#show faring_better/0."))
    atoms = sorted((sym.name, len(sym.arguments)) for sym in model)
    expected = {("resolved", 2), ("faring_better", 0)}
    got = {(name, arity) for (name, arity) in atoms}
    if expected.issubset(got):
        print("OK: ASP model contains the expected kindness-resolution atoms.")
        return 0
    print("MISMATCH: ASP model did not contain the expected atoms.")
    print("Model:", atoms)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = run_story(
        PLACE_REGISTRY[params.place],
        SCENE_REGISTRY[params.scene],
        OBJECT_REGISTRY[params.obj],
        params.fox_name,
        params.helper_name,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="lane", scene="bell", obj="bell", fox_name="Tobin", helper_name="Pip"),
    StoryParams(place="green", scene="bell", obj="bell", fox_name="Clover", helper_name="Mara"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/2.\n#show faring_better/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/2.\n#show faring_better/0."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
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
            header = f"### {p.fox_name} and {p.helper_name} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
