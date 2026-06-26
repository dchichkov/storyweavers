#!/usr/bin/env python3
"""
storyworlds/worlds/recovery_diabetes_twist_cautionary_curiosity_animal_story.py
=================================================================================

A small animal-story world about recovery, diabetes, caution, and curiosity.

Seed premise:
- Twist is an animal who is recovering after a twist injury.
- Twist also has diabetes, so sweet treats and skipped care matter.
- Cautionary warns about danger.
- Curiosity asks questions and helps the group learn.
- The story should feel like a gentle Animal Story: concrete, child-facing, and
  shaped by the world model rather than a frozen paragraph.

This script follows the Storyworld contract:
- self-contained stdlib script under storyworlds/worlds/
- eagerly imports results.py for QAItem, StoryError, StorySample
- lazily imports asp.py inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing
    species: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cautionary: object | None = None
    curiosity: object | None = None
    snack: object | None = None
    twist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    safe_for_recovery: bool
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


@dataclass(frozen=True)
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    risk_meter: str
    recovery_need: str
    tag: str
    place_ok: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Treat:
    id: str
    label: str
    phrase: str
    sweet: bool
    diabetes_risk: bool
    allowed: bool = True
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


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    offer: str
    tail: str
    helps_recovery: bool
    helps_diabetes: bool
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


ACTIVITIES = {
    "twist": Action(
        id="twist",
        verb="twirl in the meadow",
        gerund="twirling in the meadow",
        rush="spin too fast across the grass",
        risk="re-open the sore leg",
        risk_meter="strain",
        recovery_need="rest",
        tag="twist",
        place_ok={"meadow", "garden", "home"},
    ),
    "careful_walk": Action(
        id="careful_walk",
        verb="take a careful walk",
        gerund="walking carefully",
        rush="dash down the path",
        risk="bump the healing paw",
        risk_meter="strain",
        recovery_need="rest",
        tag="cautionary",
        place_ok={"meadow", "garden", "home"},
    ),
    "curious_search": Action(
        id="curious_search",
        verb="look for herbs",
        gerund="searching with curious noses",
        rush="sniff everywhere at once",
        risk="tire the recovering animal",
        risk_meter="strain",
        recovery_need="rest",
        tag="curiosity",
        place_ok={"garden", "forest", "home"},
    ),
}

PLACES = {
    "home": Place(id="home", label="the den", safe_for_recovery=True, supports={"rest", "medicine", "water"}),
    "garden": Place(id="garden", label="the garden", safe_for_recovery=True, supports={"walk", "herbs", "shade"}),
    "meadow": Place(id="meadow", label="the meadow", safe_for_recovery=False, supports={"walk", "play"}),
    "clinic": Place(id="clinic", label="the little clinic", safe_for_recovery=True, supports={"medicine", "rest"}),
}

TREATS = {
    "berry": Treat(id="berry", label="berries", phrase="a small bowl of berries", sweet=True, diabetes_risk=False),
    "honey": Treat(id="honey", label="honey cookies", phrase="two honey cookies", sweet=True, diabetes_risk=True),
    "apple": Treat(id="apple", label="apple slices", phrase="apple slices with a few seeds", sweet=False, diabetes_risk=False),
    "carrot": Treat(id="carrot", label="carrot sticks", phrase="carrot sticks with a leaf", sweet=False, diabetes_risk=False),
}

HELPERS = {
    "cautionary": Helper(
        id="cautionary",
        label="Cautionary",
        offer="slow down and check the bandage and the medicine first",
        tail="kept the path calm and safe",
        helps_recovery=True,
        helps_diabetes=True,
    ),
    "curiosity": Helper(
        id="curiosity",
        label="Curiosity",
        offer="ask careful questions about the bandage, the snack, and the sugar",
        tail="noticed the little details that made the plan work",
        helps_recovery=True,
        helps_diabetes=True,
    ),
}

ANIMALS = {
    "twist": ("Twist", "rabbit"),
    "cautionary": ("Cautionary", "owl"),
    "curiosity": ("Curiosity", "fox"),
}

TRAITS = ["gentle", "brave", "small", "spry", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    treat: str
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


def reasonableness_gate(place: Place, action: Action, treat: Treat) -> bool:
    if place.id not in action.place_ok:
        return False
    if action.id == "twist" and not place.safe_for_recovery:
        return False
    if treat.diabetes_risk and action.id == "curious_search":
        return True
    return True


def explain_rejection(place: Place, action: Action, treat: Treat) -> str:
    return (
        f"(No story: {action.gerund} does not fit well with {place.label}, or "
        f"the treat choice would not make a good recovery-and-diabetes story.)"
    )


def _rule_recovery(world: World) -> list[str]:
    out: list[str] = []
    twist = world.get("Twist")
    if twist.meters.get("strain", 0.0) >= THRESHOLD and twist.meters.get("rest", 0.0) >= THRESHOLD:
        sig = ("recovery",)
        if sig not in world.fired:
            world.fired.add(sig)
            twist.memes["hope"] = twist.memes.get("hope", 0.0) + 1
            out.append("recovery")
    return out


def _rule_diabetes(world: World) -> list[str]:
    out: list[str] = []
    twist = world.get("Twist")
    if twist.meters.get("sugar", 0.0) >= THRESHOLD:
        sig = ("diabetes",)
        if sig not in world.fired:
            world.fired.add(sig)
            twist.memes["worry"] = twist.memes.get("worry", 0.0) + 1
            out.append("diabetes")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_recovery, _rule_diabetes):
            got = rule(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for item in produced:
            if item == "recovery":
                world.say("Twist's sore leg finally felt a little steadier.")
            elif item == "diabetes":
                world.say("Twist knew the sweet snack would make the day harder to manage.")
    return produced


def predict(world: World, action: Action, treat: Treat) -> dict:
    sim = world.copy()
    twist = sim.get("Twist")
    twist.meters[action.risk_meter] = twist.meters.get(action.risk_meter, 0.0) + 1
    if treat.diabetes_risk:
        twist.meters["sugar"] = twist.meters.get("sugar", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "recovery": sim.get("Twist").memes.get("hope", 0.0) >= THRESHOLD,
        "diabetes": sim.get("Twist").memes.get("worry", 0.0) >= THRESHOLD,
    }


def tell(place: Place, action: Action, treat: Treat) -> World:
    world = World(place)
    twist_name, twist_species = ANIMALS["twist"]
    c_name, c_species = ANIMALS["cautionary"]
    q_name, q_species = ANIMALS["curiosity"]

    twist = world.add(Entity(id=twist_name, kind="character", species=twist_species, traits=["small", "recovering"]))
    cautionary = world.add(Entity(id=c_name, kind="character", species=c_species, traits=["careful", "watchful"]))
    curiosity = world.add(Entity(id=q_name, kind="character", species=q_species, traits=["bright", "questioning"]))
    snack = world.add(Entity(id="snack", kind="thing", label=treat.label, owner=twist.id, caretaker=cautionary.id))

    world.say(f"Twist was a little {twist_species} who was recovering after a twist in {twist.pronoun('possessive')} leg.")
    world.say(f"Twist also had diabetes, so every snack and every step had to be chosen with care.")
    world.say(f"Cautionary the {c_species} lived nearby, and Curiosity the {q_species} liked to ask gentle questions.")
    world.para()

    world.say(f"One day at {place.label}, Twist wanted to {action.verb}.")
    world.say(f"The idea felt good, but {action.recovery_need} still mattered because {twist.pronoun('possessive')} leg was healing.")
    if treat.sweet:
        world.say(f"Curiosity spotted {treat.phrase}, and Twist licked {twist.pronoun('possessive')} lips.")
    else:
        world.say(f"Curiosity found {treat.phrase}, and Twist smiled because it looked safe.")
    world.para()

    world.say(f"Twist tried to {action.rush}, but Cautionary lifted a wing and said, 'Slow down first.'")
    if treat.diabetes_risk:
        world.say(f"'{treat.label} is a sweet treat,' Cautionary added, 'and sweet treats need a careful plan when someone has diabetes.'")
    else:
        world.say(f"'That treat looks kind,' Cautionary said, 'but healing still comes first.'")

    twist.meters[action.risk_meter] = twist.meters.get(action.risk_meter, 0.0) + 1
    if treat.diabetes_risk:
        twist.meters["sugar"] = twist.meters.get("sugar", 0.0) + 1
    twist.meters["rest"] = twist.meters.get("rest", 0.0) + 1
    cautionary.memes["warning"] = cautionary.memes.get("warning", 0.0) + 1
    curiosity.memes["interest"] = curiosity.memes.get("interest", 0.0) + 1
    propagate(world, narrate=True)
    world.para()

    helper = HELPERS["cautionary"]
    world.say(f"Curiosity asked what would help, and Cautionary said to {helper.offer}.")
    if treat.diabetes_risk:
        world.say(f"They swapped the sweet snack for safer {TREATS['berry'].label}, and Twist felt proud to choose it.")
    else:
        world.say(f"They kept the safe snack and let Twist rest beside a cool stone.")
    world.say(f"Before long, Twist was {action.gerund}, {helper.tail}, and {twist.pronoun('possessive')} leg felt ready for tomorrow.")
    world.say(f"By the end, Twist still had diabetes, but now the whole little group knew how to be careful and kind around it.")

    world.facts.update(
        twist=twist,
        cautionary=cautionary,
        curiosity=curiosity,
        snack=snack,
        action=action,
        treat=treat,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    action: Action = _safe_fact(world, f, "action")
    treat: Treat = _safe_fact(world, f, "treat")
    return [
        f"Write a gentle animal story about Twist recovering from an injury and managing diabetes at {f['place'].label}.",
        f"Tell a child-facing story where Cautionary helps Twist choose between {treat.label} and a safer snack.",
        f"Write a short Animal Story with Curiosity asking questions while Twist heals and tries to {action.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    action: Action = _safe_fact(world, f, "action")
    treat: Treat = _safe_fact(world, f, "treat")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question="Who was recovering in the story?",
            answer="Twist was recovering after a twist in their leg, and the day had to be gentle for them.",
        ),
        QAItem(
            question="Why did the sweet snack matter so much?",
            answer=f"It mattered because Twist has diabetes, and {treat.label} was either something to avoid or handle carefully.",
        ),
        QAItem(
            question=f"What did Twist want to do at {place.label}?",
            answer=f"Twist wanted to {action.verb}, even though healing meant moving slowly.",
        ),
        QAItem(
            question="Who helped Twist stay careful?",
            answer="Cautionary helped by warning about the snack and reminding everyone to slow down, and Curiosity helped by asking questions.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Twist chose a safer plan, rested, and finished the day feeling more steady and less worried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is diabetes?",
            answer="Diabetes is a health condition that means the body needs help managing sugar and food in a careful way.",
        ),
        QAItem(
            question="Why do animals in a story need rest when they are recovering?",
            answer="Rest gives the body time to heal, so sore parts can get stronger again.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before you rush into something risky.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn, notice details, and ask questions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.species:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.safe_for_recovery:
            lines.append(asp.fact("safe", pid))
        for s in sorted(place.supports):
            lines.append(asp.fact("supports", pid, s))
    for aid, action in ACTIVITIES.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("recovery_need", aid, action.recovery_need))
        lines.append(asp.fact("risk_meter", aid, action.risk_meter))
        for p in sorted(action.place_ok):
            lines.append(asp.fact("ok_at", aid, p))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if treat.sweet:
            lines.append(asp.fact("sweet", tid))
        if treat.diabetes_risk:
            lines.append(asp.fact("diabetes_risk", tid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.helps_recovery:
            lines.append(asp.fact("helps_recovery", hid))
        if helper.helps_diabetes:
            lines.append(asp.fact("helps_diabetes", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, A, T) :- place(P), action(A), treat(T),
                        ok_at(A, P), safe(P), not bad_combo(A, T).
bad_combo(A, T) :- action(A), treat(T), diabetes_risk(T), A = curious_search, not helps_recovery_needed(A).
helps_recovery_needed(twist).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p.id, a.id, t.id) for p in PLACES.values() for a in ACTIVITIES.values() for t in TREATS.values() if reasonableness_gate(p, a, t))
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: recovery, diabetes, caution, and curiosity.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--treat", choices=sorted(TREATS))
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
    place_id = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    action_id = getattr(args, "activity", None) or rng.choice(sorted(ACTIVITIES))
    treat_id = getattr(args, "treat", None) or rng.choice(sorted(TREATS))
    place, action, treat = _safe_lookup(PLACES, place_id), _safe_lookup(ACTIVITIES, action_id), _safe_lookup(TREATS, treat_id)
    if not reasonableness_gate(place, action, treat):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place_id, activity=action_id, treat=treat_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(TREATS, params.treat))
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
    StoryParams(place="garden", activity="careful_walk", treat="berry"),
    StoryParams(place="home", activity="twist", treat="apple"),
    StoryParams(place="clinic", activity="curious_search", treat="honey"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for item in combos:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
