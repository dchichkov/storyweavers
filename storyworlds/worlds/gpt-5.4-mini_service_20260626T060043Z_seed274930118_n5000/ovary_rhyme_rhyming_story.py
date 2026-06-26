#!/usr/bin/env python3
"""
storyworlds/worlds/ovary_rhyme_rhyming_story.py
================================================

A tiny storyworld in rhyming style about a flower bud, its ovary, and a small
protective turn that keeps the future fruit safe.

The seed idea is a child-friendly rhyming tale:
- a flower is ready to bloom,
- someone notices that hail or hard rain could hurt the ovary inside,
- they cover the plant with a little shelter,
- the flower stays safe and later promises fruit.

The world is intentionally small and constraint-checked. We do not generate
random frozen prose; the state of the flower, the weather, and the shelter
drive what gets narrated.
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
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    assistant: object | None = None
    bloom: object | None = None
    child: object | None = None
    cover: object | None = None
    ovary: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father"}:
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
class World:
    setting: str
    weather: str = ""
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Parameters and registries
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
    plant: str
    weather: str
    shelter: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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
class PlantSpec:
    label: str
    flower: str
    ovary_threat: str
    bloom_rhyme: str
    fruit_hint: str
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
class ShelterSpec:
    label: str
    covers: set[str]
    helper_line: str
    ending_line: str
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


PLANTS = {
    "rose": PlantSpec("rose", "rose", "hail", "the rose gave a brave little glow", "a bright rose hip would someday grow"),
    "lily": PlantSpec("lily", "lily", "hard rain", "the lily wore droplets like pearls in a row", "a seed pod would bloom and then slowly grow"),
    "tulip": PlantSpec("tulip", "tulip", "wind", "the tulip stood tall in the soft garden flow", "a tidy seed case would soon say hello"),
}

WEATHERS = {
    "hail": "hail",
    "rain": "rain",
    "wind": "wind",
}

SHELTERS = {
    "basket": ShelterSpec(
        label="a little basket",
        covers={"flower", "ovary"},
        helper_line="They set the basket above the bloom so the flakes could not go through.",
        ending_line="The ovary stayed snug, and the flower held true.",
    ),
    "cloth": ShelterSpec(
        label="a soft cloth",
        covers={"flower", "ovary"},
        helper_line="They laid the cloth like a tiny roof in a leafy blue.",
        ending_line="The ovary stayed safe, and the garden sang through.",
    ),
    "umbrella": ShelterSpec(
        label="a small umbrella",
        covers={"flower", "ovary"},
        helper_line="They tipped the umbrella and made a round little hue.",
        ending_line="The ovary stayed dry, and the bright petals shone new.",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Ben", "Lily", "Theo"]
HELPERS = ["mother", "father", "gardener"]


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------
def rhyme_word(word: str) -> str:
    return {
        "hail": "pail",
        "rain": "glow again",
        "wind": "kind",
        "safe": "brave",
        "bloom": "room",
        "snug": "hug",
    }.get(word, word)


def threat_line(weather: str, plant: PlantSpec) -> str:
    if weather == "hail":
        return f"Small hail tapped hard, with a clackety clack,"
    if weather == "rain":
        return f"Big rain came down with a tappity smack,"
    return f"The wind blew briskly along the path back,"


def bloom_line(plant: PlantSpec) -> str:
    return f"And {plant.bloom_rhyme}."


def can_protect(shelter: ShelterSpec) -> bool:
    return "ovary" in shelter.covers


def predict_damage(world: World, shelter: ShelterSpec) -> bool:
    ovary = world.get("ovary")
    return ovary.meters.get("hurt", 0.0) >= 1.0 or shelter is None or not can_protect(shelter)


def apply_weather(world: World, plant: PlantSpec, weather: str) -> None:
    ovary = world.get("ovary")
    world.facts["threat"] = weather
    if weather == plant.ovary_threat:
        ovary.memes["worry"] = 1.0
        ovary.meters["risk"] = 1.0


def resolve_protection(world: World, shelter: ShelterSpec) -> None:
    ovary = world.get("ovary")
    if can_protect(shelter):
        world.facts["protected"] = True
        ovary.memes["worry"] = 0.0
        ovary.meters["risk"] = 0.0
    else:
        world.facts["protected"] = False
        ovary.meters["hurt"] = 1.0


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def tell(plant: PlantSpec, weather: str, shelter: ShelterSpec, name: str, gender: str, helper: str) -> World:
    world = World(setting="the garden", weather=weather)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    assistant = world.add(Entity(id="helper", kind="character", type=helper, label=helper))
    bloom = world.add(Entity(id="bloom", type=plant.label, label=plant.label))
    ovary = world.add(Entity(id="ovary", type="ovary", label="ovary", owner=bloom.id))
    cover = world.add(Entity(
        id="shelter",
        type=shelter.label,
        label=shelter.label,
        protective=True,
        covers=set(shelter.covers),
        caretaker=assistant.id,
    ))
    world.facts.update(child=child, assistant=assistant, bloom=bloom, ovary=ovary, shelter=cover, plant=plant, weather=weather)

    world.say(f"In the garden, a {plant.label} would soon bloom bright and fine,")
    world.say(f"and inside that flower lived an ovary, tiny and kind of shy in line.")
    world.say(f"{threat_line(weather, plant)}")
    world.say(f"The little ovary twitched with worry, like a pea in a vine.")
    world.say(f"{child.label} noticed the clouds and called for {helper} to join the sign.")

    world.para()
    world.say(f'"We need {shelter.label}," said {child.label}, "so the blossom stays prime."')
    world.say(f"The {helper} smiled at the idea and answered right on time,")
    world.say(f"{shelter.helper_line}")

    apply_weather(world, plant, weather)
    resolve_protection(world, shelter)

    world.para()
    if world.facts.get("protected"):
        world.say(f"The danger passed by, and the ovary stayed snug and clean.")
        world.say(f"The petals stayed shining in the sunbeam sheen.")
        world.say(f"{bloom_line(plant)}")
        world.say(f"{shelter.ending_line}")
        world.say(f"And {name} went home quite happy, with a garden story in between.")
    else:
        world.say(f"The cover was not enough, and the ovary felt keenly seen.")
        world.say(f"So the helper moved it closer, and made the shelter lean.")
        world.say(f"At last the bloom was covered, and the future fruit stayed green.")

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    plant: PlantSpec = _safe_fact(world, f, "plant")
    return [
        f'Write a short rhyming story for a young child about a {plant.label} and an ovary in a garden.',
        f"Tell a gentle rhyme where {f['child'].label} helps keep a flower's ovary safe from {f['weather']}.",
        f'Write a simple garden rhyme that includes the word "ovary" and ends with a safe shelter idea.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    assistant: Entity = _safe_fact(world, f, "assistant")
    plant: PlantSpec = _safe_fact(world, f, "plant")
    shelter: Entity = _safe_fact(world, f, "shelter")
    protected = f.get("protected", False)
    return [
        QAItem(
            question=f"What was the little child helping in the garden?",
            answer=f"{child.label} was helping a {plant.label} flower and its ovary stay safe in the garden.",
        ),
        QAItem(
            question=f"Why did {child.label} ask for {assistant.label}?",
            answer=f"{child.label} asked for {assistant.label} because {f['weather']} could hurt the ovary inside the flower.",
        ),
        QAItem(
            question=f"What did they use to protect the flower?",
            answer=f"They used {shelter.label} to cover the bloom and keep the ovary safe.",
        ),
        QAItem(
            question=f"Did the ovary end up safe?",
            answer="Yes, the ovary stayed safe and snug." if protected else "The first try was not enough, but they fixed the shelter and kept it safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ovary in a flower?",
            answer="A flower ovary is the part inside the flower that can help make seeds or fruit later.",
        ),
        QAItem(
            question="Why do gardeners sometimes cover flowers?",
            answer="Gardeners cover flowers to shield delicate parts from hail, hard rain, or strong wind.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
plant_safe(P) :- shelter(S), covers(S, ovary), weather_ok(P).
weather_ok(hail) :- threat(hail).
weather_ok(rain) :- threat(rain).
weather_ok(wind) :- threat(wind).

valid_story(Plant, Weather, Shelter) :- plant(Plant), threat(Weather), shelter(Shelter), valid_pair(Plant, Weather, Shelter).
valid_pair(Plant, Weather, Shelter) :- plant(Plant), threat(Weather), shelter(Shelter), covers(Shelter, ovary).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("ovary_threat", pid, p.ovary_threat))
    for w in WEATHERS:
        lines.append(asp.fact("threat", w))
    for sid, s in SHELTERS.items():
        lines.append(asp.fact("shelter", sid))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", sid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_stories() -> list[tuple]:
    out = []
    for p in PLANTS:
        for w in WEATHERS:
            for s, spec in SHELTERS.items():
                if can_protect(spec):
                    out.append((p, w, s))
    return sorted(out)


def asp_verify() -> int:
    py = set(python_valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combinations).")
        return 0
    print("MISMATCH between python and clingo:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: a flower ovary kept safe in the garden.")
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "plant", None) and getattr(args, "weather", None):
        spec = _safe_lookup(PLANTS, getattr(args, "plant", None))
        if getattr(args, "weather", None) != spec.ovary_threat:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    plants = list(PLANTS.keys()) if getattr(args, "plant", None) is None else [getattr(args, "plant", None)]
    valid = []
    for p in plants:
        spec = _safe_lookup(PLANTS, p)
        for w in ([getattr(args, "weather", None)] if getattr(args, "weather", None) else [spec.ovary_threat]):
            for s in ([getattr(args, "shelter", None)] if getattr(args, "shelter", None) else list(SHELTERS.keys())):
                if can_protect(_safe_lookup(SHELTERS, s)):
                    valid.append((p, w, s))
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    plant, weather, shelter = rng.choice(sorted(valid))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(plant=plant, weather=weather, shelter=shelter, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLANTS, params.plant), params.weather, _safe_lookup(SHELTERS, params.shelter), params.name, params.gender, params.helper)
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
        print()
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if ent.protective:
                bits.append(f"covers={sorted(ent.covers)}")
            print(f"{eid}: {ent.type} {' '.join(bits)}")
        print(f"facts: {sample.world.facts}")
    if qa:
        print()
        print(format_qa(sample))


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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for plant, plant_spec in PLANTS.items():
            for shelter in SHELTERS:
                params = StoryParams(
                    plant=plant,
                    weather=plant_spec.ovary_threat,
                    shelter=shelter,
                    name=_safe_lookup(CHILD_NAMES, 0),
                    gender="girl",
                    helper=_safe_lookup(HELPERS, 0),
                    seed=base_seed,
                )
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
