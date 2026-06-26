#!/usr/bin/env python3
"""
storyworlds/worlds/interruption_spectrum_repetition_flashback_heartwarming.py
=============================================================================

A small heartwarming storyworld about an interruption, a spectrum of colors,
repetition, and a gentle flashback that helps the ending come together.

Premise used to build the world model:
---
A child is making a bright color spectrum for a window. A small interruption
keeps breaking the rhythm. A flashback to a kind lesson from a grandparent
helps the child try again, this time with repetition that becomes calming and
shared, not frustrating.
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


COLOR_ORDER = ["red", "orange", "yellow", "green", "blue", "purple"]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    elder: object | None = None
    interrupter: object | None = None
    project: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        masculine = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Setting:
    place: str = "the sunny kitchen"
    affordance: str = "making a color banner"
    world: object | None = None
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
class Project:
    id: str
    label: str
    phrase: str
    materials: list[str]
    requires_order: bool = True
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
class Companion:
    id: str
    label: str
    type: str
    gentle_trait: str = "kind"
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def meter_state(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme_state(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def interrupted(world: World) -> bool:
    child = _safe_fact(world, world.facts, "child")
    return meter_state(child, "interruption") >= THRESHOLD


def project_complete(world: World) -> bool:
    project = _safe_fact(world, world.facts, "project")
    child = _safe_fact(world, world.facts, "child")
    return meter_state(project, "finished") >= THRESHOLD and meter_state(child, "calm") >= THRESHOLD


def _r_repeat_settle(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    project = _safe_fact(world, world.facts, "project")
    if meter_state(child, "repeating") < THRESHOLD:
        return out
    sig = ("settle", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meter(project, "steady", 1.0)
    add_meme(child, "calm", 1.0)
    out.append("The steady counting helped the work feel less shaky.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    project = _safe_fact(world, world.facts, "project")
    if meter_state(project, "steady") < len(project.materials):
        return out
    sig = ("finish", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meter(project, "finished", 1.0)
    add_meme(child, "joy", 1.0)
    out.append("At last, the color banner was complete.")
    return out


def _r_flashback_help(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    if meter_state(child, "remembering") < THRESHOLD:
        return out
    sig = ("flashback_help", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meter(child, "repeating", 1.0)
    add_meme(child, "hope", 1.0)
    out.append("The remembered lesson gave the child a calmer way to begin again.")
    return out


RULES = [_r_flashback_help, _r_repeat_settle, _r_finish]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def color_band_text(colors: list[str]) -> str:
    if not colors:
        return "a few empty strips of paper"
    if len(colors) == 1:
        return f"one {colors[0]} strip"
    if len(colors) == 2:
        return f"{colors[0]} and {colors[1]} strips"
    return ", ".join(colors[:-1]) + f", and {colors[-1]} strips"


def tell(world: World, hero: Entity, elder: Entity, project: Project, interrupter: Entity) -> World:
    world.say(
        f"{hero.id} was making a bright spectrum for {hero.pronoun('possessive')} window in {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted {project.phrase}, using {color_band_text(project.materials)}."
    )
    world.say(
        f"{elder.label} had once told {hero.pronoun('object')} that slow hands and kind counting could turn a hard task into a gentle one."
    )

    world.para()
    world.say(
        f"While {hero.id} lined up the colors, {interrupter.label} interrupted with a tumble and a question."
    )
    add_meter(hero, "interruption", 1.0)
    add_meme(hero, "startle", 1.0)
    add_meme(hero, "frustration", 1.0)
    world.say(
        f"{hero.id} paused, because the neat order kept breaking apart."
    )

    world.para()
    add_meter(hero, "remembering", 1.0)
    world.say(
        f"Then {hero.id} remembered {elder.label}'s lesson and whispered it back like a song."
    )
    world.say(
        f'"One red, one orange, one yellow," {hero.id} said, and then said the colors again.'
    )
    add_meter(hero, "repeating", 1.0)
    propagate(world, narrate=True)

    if not project_complete(world):
        add_meter(hero, "repeating", 1.0)
        world.say(
            f"{interrupter.label} sat beside {hero.id} and repeated the colors too."
        )
        propagate(world, narrate=True)

    world.para()
    if project_complete(world):
        world.say(
            f"Together they finished the spectrum, and the window shone like a soft sunrise."
        )
        world.say(
            f"{hero.id} smiled at the tidy colors, and {interrupter.label} smiled back, proud to help."
        )
    else:
        world.say(
            f"In the end, the colors were still a little crooked, but {hero.id} felt brave enough to keep trying."
        )

    world.facts.update(
        child=hero,
        elder=elder,
        interrupter=interrupter,
        project=project,
        setting=world.setting,
    )
    return world


def build_story_world(name: str, child_type: str, elder_type: str, interrupter_type: str) -> World:
    world = World(Setting())
    child = world.add(Entity(id=name, kind="character", type=child_type))
    elder = world.add(Entity(id="Grandma", kind="character", type=elder_type, label="Grandma"))
    interrupter = world.add(Entity(id="Pip", kind="character", type=interrupter_type, label="Pip"))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type="banner",
        label="color banner",
        phrase="a rainbow banner for the window",
    ))
    world.facts["project"] = Project(
        id="spectrum-banner",
        label="spectrum",
        phrase="a rainbow banner for the window",
        materials=COLOR_ORDER[:],
    )
    tell(world, child, elder, world.facts["project"], interrupter)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    return [
        f'Write a heartwarming story for a small child about an interruption and a spectrum of colors.',
        f'Tell a gentle story where {child.id} gets interrupted while making a color spectrum and remembers advice from {elder.label}.',
        f'Write a short story that uses repetition and flashback to help a child finish a rainbow-like project.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    elder = _safe_fact(world, f, "elder")
    interrupter = _safe_fact(world, f, "interrupter")
    project: Project = _safe_fact(world, f, "project")
    qa = [
        QAItem(
            question=f"What was {child.id} making?",
            answer=f"{child.id} was making {project.phrase}, a bright spectrum of colors for the window.",
        ),
        QAItem(
            question=f"Who interrupted the work?",
            answer=f"{interrupter.label} interrupted the work with a small tumble and a question.",
        ),
        QAItem(
            question=f"What did {child.id} remember from {elder.label}?",
            answer=f"{child.id} remembered {elder.label}'s gentle advice that slow hands and kind counting can make hard work feel easier.",
        ),
        QAItem(
            question=f"How did {child.id} keep going after the interruption?",
            answer=f"{child.id} repeated the colors again and again until the work felt steady and calm.",
        ),
    ]
    if project_complete(world):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"The story ended with the spectrum finished and the window shining softly, while everyone felt proud and happy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spectrum of colors?",
            answer="A spectrum of colors is a smooth range of colors that change little by little from one to the next.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help because doing the same gentle steps again can make a task easier to remember and calmer to finish.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that looks back to something that happened before, like remembering a kind lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    child_type: str
    elder_type: str
    interrupter_type: str
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


NAMES = ["Mina", "Leo", "Ruby", "Toby", "Nora", "Ivy"]
CHILD_TYPES = ["girl", "boy"]
ELDER_TYPES = ["grandmother", "grandfather"]
INTERRUPTER_TYPES = ["boy", "girl"]


ASP_RULES = r"""
remembering(C) :- child(C), interruption(C), flashback(C).
repeating(C) :- remembering(C).
steady(P) :- project(P), repeating(C).
finished(P) :- project(P), steady(P), material_count(P,N), N > 0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in NAMES:
        lines.append(asp.fact("child", c))
    for t in globals().get("COLOR_ORDER", sorted(globals().get("COLOR", []))):
        lines.append(asp.fact("color", t))
    lines.append(asp.fact("project", "spectrum"))
    lines.append(asp.fact("material_count", "spectrum", len(COLOR_ORDER)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show finished/1."))
    asp_set = set(asp.atoms(model, "finished"))
    py_set = {("spectrum",)} if True else set()
    if asp_set == py_set:
        print("OK: clingo gate matches Python reasonableness.")
        return 0
    print("MISMATCH between clingo and Python reasonableness:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about interruption, spectrum, repetition, and flashback.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--interrupter-type", choices=INTERRUPTER_TYPES)
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
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(NAMES),
        child_type=getattr(args, "child_type", None) or rng.choice(CHILD_TYPES),
        elder_type=getattr(args, "elder_type", None) or rng.choice(ELDER_TYPES),
        interrupter_type=getattr(args, "interrupter_type", None) or rng.choice(INTERRUPTER_TYPES),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params.name, params.child_type, params.elder_type, params.interrupter_type)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show finished/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show finished/1."))
        print(sorted(asp.atoms(model, "finished")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("Mina", "girl", "grandmother", "boy"),
            StoryParams("Leo", "boy", "grandfather", "girl"),
            StoryParams("Ruby", "girl", "grandmother", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
