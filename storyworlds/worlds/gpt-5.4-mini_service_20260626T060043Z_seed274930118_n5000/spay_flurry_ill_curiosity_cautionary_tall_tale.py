#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spay_flurry_ill_curiosity_cautionary_tall_tale.py
==========================================================================================================================

A small storyworld built from the seed words:
- spay
- flurry
- ill

This world tells a child-facing tall tale about Curiosity, Cautionary, and a
barn-breezy little pet named Flurry. The simulated turn is practical and gentle:
a vet visit for spaying, a brief spell of feeling ill afterward, and a careful
recovery that proves what changed.

The model keeps physical meters and emotional memes, and the prose is driven by
state changes rather than a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
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

    cautionary: object | None = None
    child: object | None = None
    pet: object | None = None
    vet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
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
class CarePlan:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    calms: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def pets(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "pet"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_ill(world: World) -> list[str]:
    out: list[str] = []
    for pet in world.pets():
        if pet.meters.get("sore", 0.0) < THRESHOLD:
            continue
        sig = ("ill", pet.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pet.meters["ill"] = 1.0
        pet.memes["miserable"] = pet.memes.get("miserable", 0.0) + 1.0
        out.append(f"{pet.label} felt ill and wanted nothing but a quiet blanket.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for pet in world.pets():
        if pet.meters.get("rest", 0.0) < THRESHOLD:
            continue
        sig = ("calm", pet.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pet.meters["ill"] = max(0.0, pet.meters.get("ill", 0.0) - 1.0)
        pet.memes["comfort"] = pet.memes.get("comfort", 0.0) + 1.0
        out.append(f"With a soft rest, {pet.label} began to feel steadier.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["caution"] = char.memes.get("caution", 0.0) + 1.0
        out.append(f"{char.id} kept a careful eye on the little patient.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("ill", _r_ill),
    Rule("calm", _r_calm),
    Rule("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_spay(world: World, vet: Entity, pet: Entity, narrate: bool = True) -> None:
    pet.meters["spayed"] = 1.0
    pet.meters["sore"] = 1.0
    pet.memes["trust"] = pet.memes.get("trust", 0.0) + 1.0
    propagate(world, narrate=narrate)


def predict_after_spay(world: World, pet_id: str) -> dict:
    sim = world.copy()
    sim_pet = sim.get(pet_id)
    _do_spay(sim, sim.get("Vet"), sim_pet, narrate=False)
    return {
        "ill": sim_pet.meters.get("ill", 0.0) >= THRESHOLD,
        "sore": sim_pet.meters.get("sore", 0.0) >= THRESHOLD,
    }


def setting_line(setting: Setting) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the light sat still as a butter dish."
    return f"{setting.place.capitalize()} stretched wide under a sky that could hold a whole flurry of weather."


def introduce(world: World, child: Entity, pet: Entity) -> None:
    world.say(
        f"{child.id} was the sort of child whose curiosity could outrun a dust devil."
        f" {pet.label} was a lively little pet with more bounce than a hailstone on a tin roof."
    )


def name_themes(world: World) -> None:
    world.say(
        "People around the ranch called one child Curiosity and one old hand Cautionary,"
        " because one wanted to peek behind every gate and the other liked a safe plan."
    )


def set_scene(world: World, child: Entity, pet: Entity) -> None:
    world.say(
        f"Every morning {child.id} followed {pet.label} through a flurry of hay, pawprints, and tall tales."
    )


def visit_vet(world: World, child: Entity, vet: Entity, pet: Entity) -> None:
    world.say(
        f"One bright day, {child.id} and {pet.label} went to the little vet house at the edge of {world.setting.place}."
    )
    world.say(
        f"The vet said {pet.label} should be spayed so the pet could stay healthy and not wander into trouble later."
    )


def worry_and_warn(world: World, cautionary: Entity, child: Entity, pet: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{cautionary.id} warned, \"A brave plan still needs a careful blanket and a soft hand.\""
    )
    world.say(
        f"{child.id} wanted to stay close, because even Curiosity could feel a pinch of worry."
    )


def cause_flurry(world: World, child: Entity, pet: Entity) -> None:
    world.say(
        f"The room went busy as a flurry in a windbreak, but the vet worked gently and soon the hard part was over."
    )
    _do_spay(world, world.get("Vet"), pet, narrate=True)


def recover(world: World, child: Entity, cautionary: Entity, pet: Entity, plan: CarePlan) -> None:
    pet.meters["rest"] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["worry"] = 0.0
    world.say(
        f"Then {cautionary.id} set out {plan.label}, and {plan.tail}."
    )
    world.say(
        f"{child.id} tucked {pet.label} into the blanket, and by supper time {pet.label} was still a little ill but much more snug."
    )
    world.say(
        f"Before the moon climbed high, {pet.label} was resting like a pebble in warm sand, and {child.id} knew the spay had helped."
    )


def tell(setting: Setting, hazard: Hazard, plan: CarePlan,
         child_name: str = "Curiosity",
         cautionary_name: str = "Cautionary") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl", traits=["curious", "gentle"]))
    cautionary = world.add(Entity(id=cautionary_name, kind="character", type="woman", traits=["careful"]))
    vet = world.add(Entity(id="Vet", kind="character", type="man", label="the vet"))
    pet = world.add(Entity(
        id="Flurry",
        kind="pet",
        type="cat",
        label="Flurry",
        traits=["tiny", "spry"],
        owner=child.id,
        caretaker=cautionary.id,
    ))

    world.say(setting_line(setting))
    introduce(world, child, pet)
    name_themes(world)
    set_scene(world, child, pet)

    world.para()
    visit_vet(world, child, vet, pet)
    worry_and_warn(world, cautionary, child, pet)
    cause_flurry(world, child, pet)

    world.para()
    recover(world, child, cautionary, pet, plan)

    world.facts.update(
        child=child,
        cautionary=cautionary,
        vet=vet,
        pet=pet,
        setting=setting,
        hazard=hazard,
        plan=plan,
    )
    return world


SETTINGS = {
    "ranch": Setting(place="the windy ranch", indoor=False, affords={"spay", "rest"}),
    "barn": Setting(place="the old barn", indoor=True, affords={"spay", "rest"}),
}

HAZARDS = {
    "spay": Hazard(
        id="spay",
        verb="spay Flurry",
        gerund="spaying Flurry",
        rush="dash to the vet",
        risk="be sore and a little ill afterward",
        zone={"body"},
        keyword="spay",
        tags={"vet", "care", "ill"},
    ),
}

PLANS = {
    "blanket": CarePlan(
        id="blanket",
        label="a quilted blanket, a water bowl, and a basket by the stove",
        prep="lay out a quilted blanket, a water bowl, and a basket by the stove",
        tail="laid out the quilt, filled the bowl, and set the basket in the warmest spot",
        helps={"rest"},
        calms={"ill"},
    ),
}

TRAITS = ["curious", "careful", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    plan: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hz in setting.affords:
            for plan in PLANS:
                combos.append((place, hz, plan))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        "Write a tall tale for young children about Curiosity, Cautionary, and a pet named Flurry.",
        f"Tell a gentle story where {child.id} helps {f['pet'].label} after a vet visit and a spay.",
        "Write a short, bouncy ranch story that uses the words spay, flurry, and ill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    cautionary = _safe_fact(world, f, "cautionary")
    pet = _safe_fact(world, f, "pet")
    qas = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id}, {cautionary.id}, and {pet.label}, a tiny ranch pet named Flurry.",
        ),
        QAItem(
            question=f"Why did the vet want to spay {pet.label}?",
            answer=f"The vet said spaying would help {pet.label} stay healthy and keep from wandering into trouble later.",
        ),
        QAItem(
            question=f"How did {pet.label} feel after the visit?",
            answer=f"{pet.label} felt a little ill and sore at first, so the family gave gentle rest and a warm blanket.",
        ),
    ]
    if f["pet"].meters.get("ill", 0.0) >= THRESHOLD:
        qas.append(
            QAItem(
                question=f"What helped {pet.label} get better?",
                answer=f"A soft blanket, a quiet basket, and careful watching from {cautionary.id} helped {pet.label} recover.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does spay mean for a female pet?",
            answer="To spay a female pet means a veterinarian performs an operation so the pet cannot have babies later.",
        ),
        QAItem(
            question="Why should a pet rest after an operation?",
            answer="A pet should rest after an operation so the body can heal and the sore feeling can fade away.",
        ),
        QAItem(
            question="What is a flurry?",
            answer="A flurry is a quick, busy burst of movement, like a flurry of wind, feathers, or snow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
spay_story(P) :- setting(P), affords(P, spay).
valid_story(P) :- spay_story(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p,) for p, a, pl in valid_combos() if a == "spay")
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def explain_rejection(place: str, hazard: str, plan: str) -> str:
    return f"(No story: {place}, {hazard}, and {plan} do not form a valid little-tale path here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about Curiosity, Cautionary, and Flurry.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--plan", choices=PLANS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "hazard", None) is None or c[1] == getattr(args, "hazard", None))
              and (getattr(args, "plan", None) is None or c[2] == getattr(args, "plan", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hazard, plan = rng.choice(list(combos))
    return StoryParams(place=place, hazard=hazard, plan=plan)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(HAZARDS, params.hazard), _safe_lookup(PLANS, params.plan))
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
    StoryParams(place="ranch", hazard="spay", plan="blanket"),
    StoryParams(place="barn", hazard="spay", plan="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(asp.atoms(model, "valid_story"))
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
