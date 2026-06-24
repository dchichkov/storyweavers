#!/usr/bin/env python3
"""
storyworlds/worlds/lease_fast_magic_adventure.py
=================================================

A small adventure storyworld about a child who wants to lease a magical,
very fast ride for a trip, but the grown-up worries about whether the ride
is safe, fair, and ready for the journey.
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
    leased_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    lease: object | None = None
    parent: object | None = None
    ride_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    name: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)
    has_path: bool = True
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
class Ride:
    id: str
    label: str
    phrase: str
    speed: str
    magic: str
    lease_fee: int
    risk: str
    requires: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    guards: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0

PLACES = {
    "harbor": Place(name="the harbor", outdoor=True, affords={"adventure"}),
    "forest": Place(name="the forest road", outdoor=True, affords={"adventure"}),
    "hill": Place(name="the hill path", outdoor=True, affords={"adventure"}),
}

RIDES = {
    "broom": Ride(
        id="broom",
        label="magic broom",
        phrase="a magic broom with a silver handle",
        speed="very fast",
        magic="sparkly",
        lease_fee=3,
        risk="wobbly",
        requires={"air"},
        tags={"magic", "fast"},
    ),
    "cart": Ride(
        id="cart",
        label="magic cart",
        phrase="a magic cart with bright wheels",
        speed="fast",
        magic="shiny",
        lease_fee=2,
        risk="bumpy",
        requires={"path"},
        tags={"magic", "fast"},
    ),
    "pony": Ride(
        id="pony",
        label="magic pony",
        phrase="a magic pony with a star on its forehead",
        speed="fast",
        magic="gentle",
        lease_fee=4,
        risk="tired",
        requires={"trail"},
        tags={"magic", "fast"},
    ),
}

CHARM = {
    "stability": Charm(
        id="stability",
        label="a steady charm",
        guards={"wobbly", "bumpy"},
        helps={"fast"},
        prep="borrow a steady charm too",
        tail="the charm kept the ride calm and steady",
    ),
    "rest": Charm(
        id="rest",
        label="a rest charm",
        guards={"tired"},
        helps={"fast"},
        prep="add a rest charm to the deal",
        tail="the rest charm kept the pony from getting too tired",
    ),
    "strap": Charm(
        id="strap",
        label="a safety strap",
        guards={"wobbly"},
        helps={"magic", "fast"},
        prep="fasten a safety strap first",
        tail="the safety strap helped the broom stay safe",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Tia", "Ivy", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn"]


def danger_of_ride(ride: Ride, place: Place) -> bool:
    return place.has_path and (ride.risk in {"wobbly", "bumpy", "tired"})


def compatible_charm(ride: Ride) -> Optional[Charm]:
    for c in CHARM.values():
        if ride.risk in c.guards:
            return c
    return None


def apply_ride(world: World, rider: Entity, ride: Ride, narrate: bool = True) -> list[str]:
    out: list[str] = []
    key = ("ride", ride.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    rider.meters["adventure"] = rider.meters.get("adventure", 0) + 1
    rider.memes["joy"] = rider.memes.get("joy", 0) + 1
    if ride.speed == "very fast":
        rider.meters["speed"] = rider.meters.get("speed", 0) + 2
    else:
        rider.meters["speed"] = rider.meters.get("speed", 0) + 1
    if narrate:
        out.append(f"{rider.id} zipped along on the {ride.label}.")
    return out


def predict_damage(world: World, rider: Entity, ride: Ride) -> bool:
    sim = world.copy()
    apply_ride(sim, sim.get(rider.id), ride, narrate=False)
    return bool(ride.risk == "wobbly")


def tell_story(place: Place, ride: Ride, name: str, gender: str, parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    lease = world.add(Entity(
        id="lease",
        type="paper",
        label="lease paper",
        phrase="a neat lease paper",
        owner=hero.id,
        caretaker=parent.id,
    ))
    ride_ent = world.add(Entity(
        id=ride.id,
        type=ride.id,
        label=ride.label,
        phrase=ride.phrase,
        owner="rental_shop",
        caretaker="rental_shop",
        leased_by=hero.id,
    ))

    world.say(f"{hero.id} was a curious child who loved adventure and anything {ride.magic}.")
    world.say(f"One day, {hero.id} saw {ride.phrase} at the shop and asked to lease it for the trip.")
    world.say(f"{hero.id}'s {parent.label} read the lease paper and worried because the ride was {ride.speed}.")

    world.para()
    if danger_of_ride(ride, place):
        world.say(f'"If it goes too fast, it could get {ride.risk}," {parent.label} said.')
        world.say(f"{hero.id} still wanted the ride, because the path looked like the start of a grand adventure.")
    else:
        world.say(f"The grown-up nodded, because the path matched the ride well.")

    charm = compatible_charm(ride)
    if charm and predict_damage(world, hero, ride):
        world.para()
        world.say(f"Then {hero.id} and {parent.label} found {charm.label}.")
        world.say(f"They chose to {charm.prep}, and the shopkeeper agreed to the lease.")
        world.say(f"{hero.id} climbed on, and {charm.tail}.")
        apply_ride(world, hero, ride)
        hero.memes["worry"] = 0
        hero.memes["joy"] += 1
        world.say(f"By the end, {hero.id} was smiling wide, and the {ride.label} stayed safe.")
    else:
        world.para()
        world.say(f"The grown-up said no, because the ride was not safe enough for this adventure.")
        world.say(f"So {hero.id} waited for a better day and kept the lease paper folded neat.")

    world.facts.update(hero=hero, parent=parent, ride=ride_ent, lease=lease, charm=charm, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ride = _safe_fact(world, f, "ride")
    return [
        f'Write a short adventure story about {hero.id} trying to lease a {ride.label} for a fast trip.',
        f"Tell a child-friendly magic adventure where {hero.id} wants to lease something {ride.speed}.",
        f'Write a simple story that includes the words "lease" and "fast" and ends with a safe adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    ride = _safe_fact(world, f, "ride")
    place = _safe_fact(world, f, "place")
    charm = _safe_fact(world, f, "charm")
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do with the {ride.label} at {place.name}?",
            answer=f"{hero.id} wanted to lease {ride.label} for a fast adventure trip at {place.name}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {ride.label}?",
            answer=f"{parent.label} worried because the {ride.label} was {ride.speed} and could become {ride.risk} on the trip.",
        ),
    ]
    if charm is not None:
        qs.append(
            QAItem(
                question=f"How did {hero.id} make the adventure safe with {charm.label}?",
                answer=f"{hero.id} and {parent.label} used {charm.label} so the {ride.label} could be leased safely.",
            )
        )
    else:
        qs.append(
            QAItem(
                question=f"Did {hero.id} get to lease the {ride.label}?",
                answer=f"{hero.id} did not get to lease it yet because the grown-up wanted a safer plan first.",
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lease?",
            answer="A lease is an agreement that lets someone use something for a while, often by paying a fee.",
        ),
        QAItem(
            question="What does fast mean?",
            answer="Fast means moving quickly or happening in a short time.",
        ),
        QAItem(
            question="What does a magic ride mean in a story?",
            answer="A magic ride is a pretend ride with special powers that can do things ordinary rides cannot.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    ride: str
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


CURATED = [
    StoryParams(place="harbor", ride="broom", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="forest", ride="cart", name="Leo", gender="boy", parent="father"),
    StoryParams(place="hill", ride="pony", name="Nora", gender="girl", parent="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magic adventure about leasing a fast ride.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ride", choices=RIDES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    ride = getattr(args, "ride", None) or rng.choice(list(RIDES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, ride=ride, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(RIDES, params.ride), params.name, params.gender, params.parent)
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
place(harbor). place(forest). place(hill).
ride(broom). ride(cart). ride(pony).
fast(broom). fast(cart). fast(pony).
magic(broom). magic(cart). magic(pony).
risk(broom,wobbly). risk(cart,bumpy). risk(pony,tired).
at(place,ride) :- place(place), ride(ride).
need_charm(ride) :- risk(ride,R), guard(Charm,R).
guard(stability,wobbly). guard(stability,bumpy). guard(rest,tired). guard(strap,wobbly).
valid(Place,Ride) :- place(Place), ride(Ride), magic(Ride), fast(Ride), need_charm(Ride).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in RIDES.values():
        lines.append(asp.fact("ride", r.id))
        lines.append(asp.fact("magic", r.id))
        lines.append(asp.fact("speed", r.id, r.speed))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = {(p, r.id) for p in PLACES for r in RIDES.values() if r.magic and r.speed in {"fast", "very fast"}}
    if clingo_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("ASP only:", sorted(clingo_set - py_set))
    print("Python only:", sorted(py_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
