#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/catastrophe_lilac_bravery_friendship_slice_of_life.py
==============================================================================================

A small slice-of-life storyworld about a little neighborhood catastrophe,
a lilac-colored keepsake, and the bravery it takes to ask for help and be a
good friend.

The domain is intentionally compact: a child wants to give a shy friend a
lilac gift for the community bench-and-tea hour, but a sudden tiny catastrophe
spills the plan. The turn comes when someone acts bravely, asks for help, and
the friends repair the scene together.

The simulated world tracks:
- physical meters: dust, wetness, brokenness, neatness, bloom
- emotional memes: worry, bravery, friendship, relief, trust

The story is generated from state changes, not from a fixed paragraph with
swapped names.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    child: object | None = None
    friend: object | None = None
    gift: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Location:
    name: str
    indoor: bool = False
    weather: str = ""
    affordances: set[str] = field(default_factory=set)
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
class Scene:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    repair: str
    mess: str
    zones: set[str]
    keyword: str
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    colors: set[str] = field(default_factory=set)
    suits: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class RepairKit:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.active_scene: Optional[Scene] = None
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.active_scene = copy.deepcopy(self.active_scene)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    location: str
    scene: str
    gift: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
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


LOCATIONS = {
    "porch": Location(name="the front porch", indoor=False, weather="soft evening", affordances={"tea", "repair"}),
    "garden": Location(name="the little garden", indoor=False, weather="breezy afternoon", affordances={"tea", "repair"}),
    "kitchen": Location(name="the kitchen", indoor=True, weather="", affordances={"tea", "repair"}),
}

SCENES = {
    "catastrophe": Scene(
        id="catastrophe",
        verb="carry the lilac basket carefully",
        gerund="carrying the lilac basket carefully",
        rush="rush to catch the basket",
        risk="the basket can spill and scatter the flowers",
        repair="pick up the spilled flowers together",
        mess="broken",
        zones={"hands", "floor"},
        keyword="catastrophe",
        tags={"catastrophe", "lilac", "bravery", "friendship"},
    ),
    "tea": Scene(
        id="tea",
        verb="set out the lilac cups",
        gerund="setting out the lilac cups",
        rush="hurry to steady the tray",
        risk="the tray can wobble and tip the cups",
        repair="dry the table and make room again",
        mess="wet",
        zones={"hands", "table"},
        keyword="lilac",
        tags={"lilac", "friendship"},
    ),
}

GIFTS = {
    "lilac_bouquet": Gift(
        id="lilac_bouquet",
        label="lilac bouquet",
        phrase="a small lilac bouquet wrapped in white paper",
        region="hands",
        fragile=True,
        colors={"lilac"},
        suits={"girl", "boy"},
    ),
    "lilac_card": Gift(
        id="lilac_card",
        label="lilac card",
        phrase="a handmade lilac card with a ribbon on top",
        region="hands",
        fragile=False,
        colors={"lilac"},
        suits={"girl", "boy"},
    ),
    "lilac_jar": Gift(
        id="lilac_jar",
        label="lilac jar",
        phrase="a little jar of lilac jam",
        region="table",
        fragile=True,
        colors={"lilac"},
        suits={"girl", "boy"},
    ),
}

REPAIR_KITS = [
    RepairKit(
        id="towel",
        label="a clean towel",
        covers={"table", "floor"},
        helps={"wet"},
        prep="grab a clean towel and press it over the spill",
        tail="worked together to dry the table",
    ),
    RepairKit(
        id="box",
        label="a sturdy box",
        covers={"hands"},
        helps={"broken"},
        prep="bring a sturdy box and make a safe place for the flowers",
        tail="carefully moved the bouquet into the box",
    ),
    RepairKit(
        id="cloth",
        label="a soft cloth",
        covers={"hands", "table"},
        helps={"broken", "wet"},
        prep="use a soft cloth to tidy the mess",
        tail="wiped the spill and gathered the petals",
    ),
]

CHILD_NAMES = ["Mina", "Ari", "Noa", "Lena", "Pia", "Sage", "Iris", "Nina"]
FRIEND_NAMES = ["Jun", "Eli", "Theo", "Ruby", "Owen", "Ada", "Milo", "Tess"]
GENDERS = ["girl", "boy"]


def prize_at_risk(scene: Scene, gift: Gift) -> bool:
    return gift.region in scene.zones


def select_kit(scene: Scene, gift: Gift) -> Optional[RepairKit]:
    for kit in REPAIR_KITS:
        if scene.mess in kit.helps and gift.region in kit.covers:
            return kit
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc_key, loc in LOCATIONS.items():
        for scene_key in loc.affordances:
            scene = _safe_lookup(SCENES, scene_key)
            for gift_key, gift in GIFTS.items():
                if prize_at_risk(scene, gift) and select_kit(scene, gift):
                    combos.append((loc_key, scene_key, gift_key))
    return combos


def _do_scene(world: World, child: Entity, scene: Scene, narrate: bool = True) -> None:
    world.active_scene = scene
    child.meters.setdefault(scene.mess, 0.0)
    child.meters[scene.mess] += 1.0
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 0.5
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 0.25)
    if narrate:
        world.say(f"{child.id} {scene.verb} and tried to keep everything steady.")


def predict(world: World, child: Entity, scene: Scene, gift_id: str) -> dict:
    sim = world.copy()
    _do_scene(sim, sim.get(child.id), scene, narrate=False)
    gift = sim.get(gift_id)
    return {
        "broken": bool(gift and gift.meters.get("broken", 0.0) >= THRESHOLD),
        "wet": bool(gift and gift.meters.get("wet", 0.0) >= THRESHOLD),
    }


def intro(world: World, child: Entity, friend: Entity, gift: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked quiet afternoons, good plans, "
        f"and the color lilac."
    )
    world.say(
        f"{friend.id} was {friend.pronoun('possessive')} friend, and the two of them "
        f"liked to share snacks, stories, and small jobs that felt important."
    )
    world.say(
        f"That day, {child.id} had {child.pronoun('possessive')} {gift.label_word} ready "
        f"for a friendly little visit."
    )


def setup(world: World, child: Entity, friend: Entity, gift: Entity) -> None:
    world.say(
        f"They met at {world.location.name}, where the air felt calm and the lilac color "
        f"seemed to hang in the light."
    )
    world.say(
        f"{child.id} wanted to be brave and carry the {gift.label_word} without wobbling."
    )


def catastrophe(world: World, child: Entity, friend: Entity, scene: Scene, gift: Entity) -> None:
    pred = predict(world, child, scene, gift.id)
    world.facts["predicted_broken"] = pred["broken"]
    world.facts["predicted_wet"] = pred["wet"]
    world.say(
        f"Then a tiny catastrophe happened: {scene.risk}."
    )
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 0.5
    if pred["broken"] or pred["wet"]:
        world.say(
            f"{child.id} paused, because {gift.label_word} could get ruined if nobody helped."
        )


def brave_choice(world: World, child: Entity, friend: Entity, scene: Scene) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 0.5
    world.say(
        f"{child.id} took a breath and said, \"I need help.\" That was the brave part."
    )
    world.say(
        f"{friend.id} smiled right away, because good friends make room for honest words."
    )


def repair(world: World, child: Entity, friend: Entity, scene: Scene, gift: Entity) -> Optional[RepairKit]:
    kit = select_kit(scene, gift)
    if kit is None:
        return None
    world.facts["kit"] = kit
    world.say(
        f"{friend.id} found {kit.label} and said, \"Let's fix it together.\""
    )
    world.say(f"{kit.prep}.")
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    gift.meters["broken"] = 0.0
    gift.meters["wet"] = 0.0
    world.say(
        f"Together they {scene.repair}, and the little catastrophe stopped feeling big."
    )
    return kit


def ending(world: World, child: Entity, friend: Entity, gift: Entity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    world.say(
        f"In the end, {gift.label_word} was safe again, and the lilac color looked even "
        f"sweeter after the repair."
    )
    world.say(
        f"{child.id} and {friend.id} sat side by side, proud of their brave little fix."
    )


def tell(location: Location, scene: Scene, gift_cfg: Gift,
         child_name: str, child_gender: str,
         friend_name: str, friend_gender: str) -> World:
    world = World(location)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             meters={}, memes={"worry": 0.0, "bravery": 0.0,
                                               "friendship": 0.0, "relief": 0.0}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender,
                              meters={}, memes={"worry": 0.0, "bravery": 0.0,
                                                "friendship": 0.0, "relief": 0.0}))
    gift = world.add(Entity(
        id="gift",
        type="thing",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=child.id,
        caretaker=friend.id,
        region=gift_cfg.region,
    ))

    intro(world, child, friend, gift)
    world.para()
    setup(world, child, friend, gift)
    catastrophe(world, child, friend, scene, gift)
    brave_choice(world, child, friend, scene)
    world.para()
    kit = repair(world, child, friend, scene, gift)
    ending(world, child, friend, gift)

    world.facts.update(
        child=child,
        friend=friend,
        gift=gift,
        kit=kit,
        scene=scene,
        location=location,
        gift_cfg=gift_cfg,
    )
    return world


KNOWLEDGE = {
    "catastrophe": [
        (
            "What does catastrophe mean?",
            "A catastrophe is a sudden bad event that causes trouble or damage, like a spill or a break."
        )
    ],
    "lilac": [
        (
            "What color is lilac?",
            "Lilac is a pale purple color, like the blossoms of a lilac flower."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing something even when you feel nervous, like asking for help or facing a hard moment."
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is the caring bond between people who help each other, share with each other, and enjoy being together."
        )
    ],
    "repair": [
        (
            "Why do people repair things?",
            "People repair things to make them usable and safe again after something gets broken or messy."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, friend, scene, gift = f["child"], f["friend"], f["scene"], f["gift_cfg"]
    return [
        f'Write a gentle slice-of-life story for a young child that includes the word "{scene.keyword}".',
        f"Tell a story where {child.id} wants to be brave, {friend.id} helps as a friend, and a {gift.label} is part of the plan.",
        f'Write a short story about a lilac-colored gift, a small catastrophe, and two friends fixing it together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, scene, gift = f["child"], f["friend"], f["scene"], f["gift_cfg"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id} and {friend.id}, two friends in a quiet little moment."
        ),
        QAItem(
            question=f"What was {child.id} trying to do before the trouble started?",
            answer=f"{child.id} was trying to {scene.verb}, while keeping the {gift.label_word} safe."
        ),
        QAItem(
            question=f"What color was the gift?",
            answer=f"The gift was lilac, a soft pale purple color."
        ),
        QAItem(
            question=f"What made the moment a catastrophe?",
            answer=f"The catastrophe happened because {scene.risk}."
        ),
    ]
    if f.get("kit") is not None:
        kit = _safe_fact(world, f, "kit")
        qa.append(
            QAItem(
                question=f"How did {friend.id} help fix the problem?",
                answer=f"{friend.id} brought {kit.label} and helped {child.id} repair the mess together."
            )
        )
        qa.append(
            QAItem(
                question=f"What did {child.id} do that showed bravery?",
                answer=f"{child.id} was brave by saying, \"I need help,\" instead of pretending everything was fine."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["scene"].tags)
    out: list[QAItem] = []
    for tag in ["catastrophe", "lilac", "bravery", "friendship", "repair"]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(S, G) :- scene(S), gift(G), zones(S, R), region(G, R).
needs_help(S, G) :- prize_at_risk(S, G), scene(S), gift(G), helps_kit(S, G).
good_combo(L, S, G) :- location(L), afford(L, S), prize_at_risk(S, G), needs_help(S, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.indoor:
            lines.append(asp.fact("indoor", lid))
        for sc in sorted(loc.affordances):
            lines.append(asp.fact("afford", lid, sc))
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("zones", sid, *sorted(sc.zones)) if False else "")
        for z in sorted(sc.zones):
            lines.append(asp.fact("zones", sid, z))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("region", gid, g.region))
        if g.fragile:
            lines.append(asp.fact("fragile", gid))
        for c in sorted(g.colors):
            lines.append(asp.fact("color", gid, c))
        for s in sorted(g.suits):
            lines.append(asp.fact("suits", gid, s))
    for kid, kit in [(k.id, k) for k in REPAIR_KITS]:
        lines.append(asp.fact("kit", kid))
        for c in sorted(kit.covers):
            lines.append(asp.fact("covers", kid, c))
        for h in sorted(kit.helps):
            lines.append(asp.fact("helps", kid, h))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_py() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos_py())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def explain_rejection(scene: Scene, gift: Gift) -> str:
    if not prize_at_risk(scene, gift):
        return (
            f"(No story: the {gift.label} sits on the {gift.region}, but this scene splashes "
            f"{sorted(scene.zones)}. The gift would not actually be at risk.)"
        )
    if select_kit(scene, gift) is None:
        return (
            f"(No story: the {gift.label} would be at risk in this scene, but there is no repair kit "
            f"that can fix this kind of mess for that region.)"
        )
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with lilac, catastrophe, bravery, and friendship.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-gender", dest="child_gender", choices=GENDERS)
    ap.add_argument("--friend-name", dest="friend_name")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=GENDERS)
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
    if getattr(args, "scene", None) and getattr(args, "gift", None):
        scene = _safe_lookup(SCENES, getattr(args, "scene", None))
        gift = _safe_lookup(GIFTS, getattr(args, "gift", None))
        if not (prize_at_risk(scene, gift) and select_kit(scene, gift)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
        and (getattr(args, "scene", None) is None or c[1] == getattr(args, "scene", None))
        and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    location, scene, gift = rng.choice(list(combos))
    child_gender = getattr(args, "child_gender", None) or rng.choice(GENDERS)
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(GENDERS)
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != child_name])
    return StoryParams(
        location=location,
        scene=scene,
        gift=gift,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(LOCATIONS, params.location),
        _safe_lookup(SCENES, params.scene),
        _safe_lookup(GIFTS, params.gift),
        params.child_name,
        params.child_gender,
        params.friend_name,
        params.friend_gender,
    )
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


def asp_valid_stories() -> list[tuple]:
    return []


CURATED = [
    StoryParams(location="garden", scene="catastrophe", gift="lilac_bouquet", child_name="Mina", child_gender="girl", friend_name="Jun", friend_gender="boy"),
    StoryParams(location="porch", scene="tea", gift="lilac_card", child_name="Ari", child_gender="boy", friend_name="Tess", friend_gender="girl"),
    StoryParams(location="kitchen", scene="catastrophe", gift="lilac_jar", child_name="Iris", child_gender="girl", friend_name="Owen", friend_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (location, scene, gift) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.child_name}: {p.scene} at {p.location} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
