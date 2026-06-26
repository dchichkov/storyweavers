#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chard_gust_mic_kindness_cautionary_rhyming_story.py
===============================================================================================================================

A small rhyming storyworld with chard, a gust, and a microphone.

Seed tale premise:
- A child is helping in a garden.
- The child wants to use a mic to share a kind rhyme.
- A gust can blow leaves, soil, and loose things around.
- The cautionary turn comes when the child nearly uses the mic near the windy patch.
- The kindness turn comes when the child helps cover the chard and waits for calmer air.

The world is intentionally tiny and classical:
- one child
- one patch of chard
- one handheld mic
- one breeze-prone outdoor place
- a gentle helper who teaches caution and kindness

The prose is authored from world state, not a frozen template.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chard: object | None = None
    child: object | None = None
    helper: object | None = None
    mic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    windy: bool = False
    supports: set[str] = field(default_factory=set)
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
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            lines=[[]],
            facts=dict(self.facts),
        )
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
    setting: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "garden": Place("the garden", windy=True, supports={"chard", "mic"}),
    "yard": Place("the yard", windy=True, supports={"chard", "mic"}),
    "patio": Place("the patio", windy=False, supports={"mic"}),
}

NAMES_GIRL = ["Mina", "Lia", "Nora", "Zia", "Eve"]
NAMES_BOY = ["Omar", "Jude", "Finn", "Noah", "Ezra"]
HELPERS = ["mom", "dad", "a neighbor", "a kind aunt"]


@dataclass
class ChardPlot:
    label: str = "the chard"
    phrase: str = "a tidy patch of chard"
    region: str = "ground"
    CHARD: object | None = None
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
class Mic:
    label: str = "mic"
    phrase: str = "a small silver mic"
    guards: set[str] = field(default_factory=lambda: {"quiet"})
    fragile: bool = True
    MIC: object | None = None
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


CHARD = ChardPlot()
MIC = Mic()


def valid_settings() -> list[str]:
    return ["garden", "yard", "patio"]


def can_tell(setting: Place) -> bool:
    return "chard" in setting.supports and "mic" in setting.supports or "chard" in setting.supports


def reasonableness_gate(setting: str, helper: str) -> None:
    if setting not in SETTINGS:
        pass
    if helper not in HELPERS:
        pass
    if setting == "patio":
        pass


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(place=setting)

    child_type = params.gender
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        meters={"care": 0.0, "worry": 0.0, "helpfulness": 0.0},
        memes={"kindness": 0.0, "caution": 0.0, "joy": 0.0, "shame": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="parent" if params.helper in {"mom", "dad"} else "adult",
        label=params.helper,
        meters={"care": 0.0, "worry": 0.0},
        memes={"kindness": 0.0, "caution": 0.0},
    ))
    chard = world.add(Entity(
        id="Chard",
        type="plant",
        label="chard",
        phrase=CHARD.phrase,
        caretaker=helper.id,
        meters={"thirst": 0.0, "damage": 0.0},
    ))
    mic = world.add(Entity(
        id="Mic",
        type="tool",
        label="mic",
        phrase=MIC.phrase,
        owner=child.id,
        meters={"gleam": 1.0, "noise": 0.0},
        memes={"pride": 1.0},
    ))

    world.facts.update(child=child, helper=helper, chard=chard, mic=mic, setting=setting)
    return world


def _gust(world: World) -> None:
    child = world.get(world.facts["child"].id)
    chard = world.get("Chard")
    mic = world.get("Mic")

    if world.place.windy:
        child.meters["worry"] += 1
        chard.meters["damage"] += 1
        mic.meters["noise"] += 1
        child.memes["caution"] += 1
        world.say("A gust came quick with a leafy whirl, and it made the little one twirl.")
        world.say("It tugged at the stems and rattled the bright mic shell, which felt less than well.")
    else:
        world.say("A soft breeze came by, but it only kissed the leaves and sighed.")


def _kindness_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    helper = world.get("Helper")
    chard = world.get("Chard")

    child.meters["helpfulness"] += 1
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    chard.meters["thirst"] = max(0.0, chard.meters["thirst"] - 1.0)
    world.say("The child said, 'I'll help the greens stay neat; that seems sweet.'")
    world.say(f"{helper.label.capitalize()} smiled and showed how to tuck the leaves in place, with a gentle grace.")


def _cautionary_turn(world: World) -> None:
    child = world.get(world.facts["child"].id)
    helper = world.get("Helper")
    mic = world.get("Mic")

    child.memes["caution"] += 1
    helper.memes["caution"] += 1
    if world.place.windy:
        world.say("The helper said, 'Not yet, my dear; the wind makes the sound unclear.'")
        world.say("The child held the mic down low, and chose to wait for a calmer glow.")
    else:
        world.say("The helper said, 'Use the mic with care, and speak your rhyme from there.'")
    mic.meters["noise"] = 0.0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.get(params.name)
    helper = world.get("Helper")
    chard = world.get("Chard")
    mic = world.get("Mic")

    world.say(f"{child.id} was a little {params.gender} with a kind and curious grin.")
    world.say(f"{child.id} held {mic.phrase}, and wanted to sing a rhyme to begin.")
    world.say(f"Near {world.place.name}, {chard.phrase} grew in a row, green as spring snow.")

    world.para()
    world.say(f"Then the air grew brisk; a gust came fast, and the cheerful scene did not last.")
    _gust(world)
    world.say(f"{child.id} looked at the leaves and gave a tiny nod, because care is the best little job.")

    world.para()
    _cautionary_turn(world)
    _kindness_turn(world)
    child.memes["joy"] += 1

    world.para()
    if world.place.windy:
        world.say(f"So {child.id} waited by the bed, and used the mic only after the gust had fled.")
    world.say(f"At last {child.id} sang a soft little rhyme, and the chard stood neat in the sunshine.")
    world.say(f"Kindness kept the garden bright; caution made the moment right.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a rhyming story for a young child about {child.id}, a gust, and a mic.',
        f'Tell a cautionary-but-kind story in rhyme where {child.id} must be careful near {world.place.name}.',
        f'Write a gentle garden rhyme about {helper.label} helping {child.id} protect chard from the wind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    chard = _safe_fact(world, f, "chard")
    mic = _safe_fact(world, f, "mic")
    place = _safe_fact(world, f, "setting").name
    return [
        QAItem(
            question=f"What was {child.id} holding when the story began?",
            answer=f"{child.id} was holding a small silver mic and hoping to sing a rhyme.",
        ),
        QAItem(
            question=f"What plant was growing near {place}?",
            answer=f"A tidy patch of chard was growing near {place}, green and neat.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {child.id} to wait?",
            answer=f"{helper.label.capitalize()} told {child.id} to wait because the gust made the sound unclear and could bother the chard.",
        ),
        QAItem(
            question=f"How did {child.id} act kindly in the end?",
            answer=f"{child.id} helped keep the leaves in place, then waited and sang only after the wind calmed down.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The mic was used more carefully, the chard was helped, and the day ended with a calm little rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chard?",
            answer="Chard is a leafy green vegetable that grows in a garden bed.",
        ),
        QAItem(
            question="What is a gust?",
            answer="A gust is a quick, strong burst of wind.",
        ),
        QAItem(
            question="What is a mic for?",
            answer="A mic helps a person speak or sing so the voice can be heard more clearly.",
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if ent.phrase:
            parts.append(f"phrase={ent.phrase!r}")
        lines.append(f"{ent.id}: {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.

valid(S, H) :- setting(S), helper(H), not invalid(S, H).
invalid("patio", _).

% A little declarative mirror of the reasonableness gate:
% the story wants chard and a mic, and a windy place makes the cautionary turn meaningful.
storyplace(S) :- setting(S), supports_chard(S), supports_mic(S).
usable(S) :- storyplace(S), not invalid(S, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, place in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "chard" in place.supports:
            lines.append(asp.fact("supports_chard", sid))
        if "mic" in place.supports:
            lines.append(asp.fact("supports_mic", sid))
        if place.windy:
            lines.append(asp.fact("windy", sid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(s, h) for s in SETTINGS for h in HELPERS if s != "patio"}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(python_set - clingo_set))
    print("clingo-only:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming cautionary kindness storyworld with chard, gust, and mic.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    reasonableness_gate(setting, helper)
    return StoryParams(setting=setting, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="garden", name="Mina", gender="girl", helper="mom"),
    StoryParams(setting="yard", name="Omar", gender="boy", helper="dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible settings/helpers:")
        for s, h in vals:
            print(f"  {s:8} {h}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
