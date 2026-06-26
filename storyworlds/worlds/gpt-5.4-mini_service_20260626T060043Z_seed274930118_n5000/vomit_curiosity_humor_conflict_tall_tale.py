#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/vomit_curiosity_humor_conflict_tall_tale.py
================================================================================

A tiny tall-tale storyworld about curiosity, a comic mistake, and a messy
conflict that ends in a clean-up and a grin.

Seed premise:
---
A curious kid follows a strange trail, samples a suspicious delight, gets a
comic case of the heaves, and learns that sometimes a pause is wiser than a
plunge.

World model:
---
- A child has curiosity, humor, and conflict as emotional membranes ("memes").
- Certain enticing objects can be inspected or tasted.
- If the child tastes the wrong one, nausea rises and vomit happens.
- Vomit makes a mess on the child and nearby items, which can trigger cleanup
  and a family disagreement.
- A parent or helper can resolve the trouble by fetching water, a cloth, or
  a bucket and guiding the child to rest.

The prose is authored from state, not from a frozen template swap.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ["mess", "nausea", "clean", "sipped", "tasted", "worry", "relief", "work"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
        return self.label or self.type
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
class Setting:
    place: str
    indoors: bool = False
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
class Temptation:
    id: str
    label: str
    phrase: str
    smell: str
    taste: str
    urge: str
    risk: str
    mess: str = "vomit"
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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    helps: str
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
class StoryParams:
    place: str
    temptation: str
    remedy: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"taste", "sniff"}),
    "fair": Setting(place="the traveling fair", indoors=False, affords={"taste", "sniff"}),
    "orchard": Setting(place="the orchard", indoors=False, affords={"taste", "sniff"}),
}

TEMPTATIONS = {
    "moonpie": Temptation(
        id="moonpie",
        label="moon pie",
        phrase="a squishy moon pie",
        smell="sweet and strange",
        taste="too sweet and a little old",
        urge="take a tiny bite",
        risk="might turn your stomach",
        tags={"sweet", "food", "curiosity", "humor"},
    ),
    "pickle_ice": Temptation(
        id="pickle_ice",
        label="pickle ice cream",
        phrase="a green scoop of pickle ice cream",
        smell="cold and sour",
        taste="cold, sour, and silly",
        urge="have one brave lick",
        risk="could make even a clown blink twice",
        tags={"sour", "food", "curiosity", "humor"},
    ),
    "spice_cake": Temptation(
        id="spice_cake",
        label="spice cake",
        phrase="a towering spice cake",
        smell="warm and sneezy",
        taste="hot and tickly",
        urge="sample a crumb",
        risk="might send a fellow wobbling",
        tags={"spice", "food", "curiosity", "humor"},
    ),
}

REMEDIES = {
    "bucket": Remedy(
        id="bucket",
        label="bucket",
        phrase="a tin bucket",
        action="fetch a bucket",
        helps="gives the child a place to be sick without making the floor worse",
        tags={"cleanup", "vomit"},
    ),
    "water": Remedy(
        id="water",
        label="water cup",
        phrase="a cup of cool water",
        action="bring water",
        helps="helps the child rinse out the sour taste",
        tags={"cleanup", "vomit"},
    ),
    "cloth": Remedy(
        id="cloth",
        label="clean cloth",
        phrase="a clean cloth",
        action="bring a clean cloth",
        helps="wipes up the mess and calms the worry",
        tags={"cleanup", "vomit"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Pip", "Zoe"],
    "boy": ["Otis", "Ben", "Milo", "Finn", "Theo"],
}
TRAITS = ["curious", "bright-eyed", "spirited", "waggish", "bold"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for t in setting.affords:
            for temp_id in TEMPTATIONS:
                for rem_id in REMEDIES:
                    combos.append((place, temp_id, rem_id))
    return combos


def explain_rejection(temp: Temptation, rem: Remedy) -> str:
    return f"(No story: the chosen remedy {rem.label} does not fit a vomit story with {temp.label}.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _narrate_intro(world: World, child: Entity, parent: Entity, temp: Temptation) -> None:
    world.say(f"{child.id} was a {next(t for t in [child.type, *child.memes.keys()] if t) if False else 'little'} {child.pronoun('subject') and child.type} with a curiosity so big it could have leaned over a fence and peeked into tomorrow.")
    world.say(f"{child.id} loved funny little surprises, and the whole family knew {child.pronoun('subject')} could laugh at the oddest thing.")
    world.say(f"One day, {child.id} noticed {temp.phrase} on a table, and {temp.smell} smell drifted through {world.setting.place} like a brass band in a teacup.")


def _tempt(world: World, child: Entity, temp: Temptation) -> None:
    child.memes["curiosity"] += 1
    child.memes["humor"] += 1
    world.say(f"{child.id} giggled at the silly look of it and wanted to {temp.urge}.")
    world.say(f'“It looks funny,” {child.id} said. “Maybe it tastes funny too!”')


def _warn(world: World, parent: Entity, child: Entity, temp: Temptation) -> None:
    child.memes["conflict"] += 1
    parent.memes["worry"] += 1
    world.say(f'{parent.id} held up a hand and said, “Not yet, dear. That {temp.label} {temp.risk}.”')
    world.say(f"{child.id} frowned, because curiosity was pulling one way and caution was pulling the other.")


def _taste(world: World, child: Entity, temp: Temptation) -> None:
    child.meters["tasted"] += 1
    child.meters["nausea"] += 1
    child.memes["humor"] += 1
    world.say(f"But {child.id} took one tiny bite anyway.")
    world.say(f"The taste was {temp.taste}, and the child's face folded up like a pocket handkerchief in a windstorm.")
    child.meters["mess"] += 1


def _vomit(world: World, child: Entity) -> None:
    if child.meters["nausea"] < THRESHOLD:
        return
    world.say(f"Then came a great and sorry heave, and {child.id} threw up right there.")
    world.say(f"The mess landed on {child.id}'s shirt and on the floor, as quick as a rabbit and twice as unwelcome.")


def _cleanup(world: World, parent: Entity, child: Entity, remedy: Remedy) -> None:
    parent.memes["relief"] += 1
    parent.meters["work"] += 1
    world.say(f'{parent.id} did not scold long. {parent.id} hurried to {remedy.action}, and the room got quieter at once.')
    world.say(f"{remedy.label.capitalize()} helped because it {remedy.helps}.")
    world.say(f"{child.id} sipped, wiped {child.pronoun('possessive')} mouth, and blinked back the tears.")
    child.meters["clean"] += 1
    child.memes["conflict"] = 0.0


def tell(world: World, child: Entity, parent: Entity, temp: Temptation, remedy: Remedy) -> World:
    _narrate_intro(world, child, parent, temp)
    world.para()
    _tempt(world, child, temp)
    _warn(world, parent, child, temp)
    _taste(world, child, temp)
    _vomit(world, child)
    world.para()
    _cleanup(world, parent, child, remedy)
    world.say(f"By the end, {child.id} was still curious, still funny, and much wiser about tasting first and asking second.")
    world.say(f"And the whole family laughed the sort of laugh that comes after a mess is gone and a lesson has settled in.")
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place,Temp,Rem) :- setting(Place), tempt(Temp), remedy(Rem).
story_ready(Place,Temp,Rem) :- valid(Place,Temp,Rem).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for t in TEMPTATIONS:
        lines.append(asp.fact("tempt", t))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for a child with the word "{f["temp"].label}" and the theme "curiosity, humor, and conflict".',
        f"Tell a comic story where {f['child'].id} wants to try {f['temp'].phrase} but gets into trouble and the family fixes it kindly.",
        f"Write a simple tale about a curious child, a bad bite, and a cleanup that ends with laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    temp: Temptation = _safe_fact(world, f, "temp")
    rem: Remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"What did {child.id} want to do when seeing {temp.phrase}?",
            answer=f"{child.id} wanted to {temp.urge} because {child.pronoun('subject')} was very curious.",
        ),
        QAItem(
            question=f"Why did {parent.id} stop {child.id} from tasting it at first?",
            answer=f"{parent.id} knew the {temp.label} {temp.risk}, so {parent.id} warned {child.id} before things got messy.",
        ),
        QAItem(
            question=f"What made the story turn from funny curiosity into a conflict?",
            answer=f"The turn came when {child.id} tasted the strange food anyway, got nauseated, and then threw up, which made everyone rush to help.",
        ),
        QAItem(
            question=f"How did {parent.id} help after the vomit mess?",
            answer=f"{parent.id} used {rem.label} to clean up, gave comfort, and helped {child.id} rinse the bad taste away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vomit?",
            answer="Vomit is the food and liquid that comes back up out of the stomach when a person feels very sick.",
        ),
        QAItem(
            question="Why can a strange food make someone throw up?",
            answer="A strange food can upset the stomach, and the body may push it back out because it does not feel safe or agreeable.",
        ),
        QAItem(
            question="What does a curious child do?",
            answer="A curious child wants to look, ask, and learn about things, even when those things seem a little unusual.",
        ),
        QAItem(
            question="Why can humor help during a mistake?",
            answer="Humor can make a scary or embarrassing moment feel lighter, so people can calm down and fix the problem together.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a struggle or disagreement that makes the characters pause, worry, or argue before they find a solution.",
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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale vomit storyworld with curiosity, humor, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "temptation", None) and getattr(args, "remedy", None):
        temp = _safe_lookup(TEMPTATIONS, getattr(args, "temptation", None))
        rem = _safe_lookup(REMEDIES, getattr(args, "remedy", None))
        if temp.id == "moonpie" and rem.id == "cloth":
            pass
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    temp = getattr(args, "temptation", None) or rng.choice(list(TEMPTATIONS))
    rem = getattr(args, "remedy", None) or rng.choice(list(REMEDIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, temptation=temp, remedy=rem, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    temp = _safe_lookup(TEMPTATIONS, params.temptation)
    rem = _safe_lookup(REMEDIES, params.remedy)
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    child.memes["curiosity"] = 1.0
    child.memes["humor"] = 1.0
    world.facts = {"child": child, "parent": parent, "temp": temp, "remedy": rem, "params": params}
    tell(world, child, parent, temp, rem)
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
    StoryParams(place="kitchen", temptation="moonpie", remedy="bucket", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="fair", temptation="pickle_ice", remedy="water", name="Otis", gender="boy", parent="father", trait="waggish"),
    StoryParams(place="orchard", temptation="spice_cake", remedy="cloth", name="Lila", gender="girl", parent="mother", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combinations:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
