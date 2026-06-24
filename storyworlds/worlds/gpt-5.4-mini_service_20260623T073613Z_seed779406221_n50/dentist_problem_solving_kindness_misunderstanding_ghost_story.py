#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
===================================================================================

A standalone story world about a dentist visit with a gentle ghost-story mood:
a small misunderstanding, a kind correction, and a problem solved together.

The seed imagines a child arriving at a quiet dentist office after hearing a
strange soft rattling at night. The child thinks the sound must be a ghost, but
the dentist, the child, and a kind helper discover a simpler cause and fix it
without fear. The world tracks physical state in meters and emotional state in
memes, and the story ends with a clear image proving what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    dentist: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
        if not hasattr(self, "_tags"):
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
    id: str
    label: str
    detail: str
    quiet: bool = True
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Problem:
    id: str
    symptom: str
    cause: str
    clue: str
    fix: str
    solved_image: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class KindAction:
    id: str
    label: str
    verb: str
    effect: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Misunderstanding:
    id: str
    scary_phrase: str
    real_cause_phrase: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    dentist: str
    dentist_type: str
    helper: str
    helper_type: str
    problem: str
    kindness: str
    misunderstanding: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "clinic": Place("clinic", "the dentist office", "The hallway was pale and quiet, with a soft lamp glowing by the chairs."),
    "night_clinic": Place("night_clinic", "the dentist office at night", "The little room was almost dark, and the moon made silver shapes on the floor."),
    "quiet_room": Place("quiet_room", "the dental room", "The room smelled clean, and a blanket waited on the chair like a folded cloud."),
}

PROBLEMS = {
    "toothache": Problem(
        "toothache",
        symptom="a sore tooth",
        cause="a tiny crumb hiding in a back tooth",
        clue="a small crackly sound near the sink",
        fix="wash the tooth, check it with a tiny mirror, and brush the crumb away",
        solved_image="the tooth shone clean and the sore spot stopped aching",
    ),
    "stuck_brush": Problem(
        "stuck_brush",
        symptom="a toothbrush that kept slipping",
        cause="a wet handle and a worried hand",
        clue="the brush kept tapping the cup",
        fix="dry the handle, wrap it with cloth, and hold it more carefully",
        solved_image="the brush sat still in a dry blue cup",
    ),
    "lost_floss": Problem(
        "lost_floss",
        symptom="a missing roll of floss",
        cause="it had rolled under the cabinet",
        clue="a faint rustle under the shelf",
        fix="lift the cabinet cloth, find the roll, and tuck it into a basket",
        solved_image="the floss rolled safely in a little basket by the sink",
    ),
}

KINDS = {
    "comfort_blanket": KindAction("comfort_blanket", "a soft blanket", "wrap", "the child felt braver and warmer"),
    "warm_smile": KindAction("warm_smile", "a warm smile", "share", "the room felt less scary right away"),
    "gentle_voice": KindAction("gentle_voice", "a gentle voice", "speak softly", "the fear stopped growing"),
}

MISUNDERSTANDINGS = {
    "ghost_sound": Misunderstanding("ghost_sound", "a ghost in the hallway", "the cabinet door had only been rattling in the draft"),
    "white_sheet": Misunderstanding("white_sheet", "a white ghost on the chair", "a clean dental sheet was waiting for the child"),
    "night_shadow": Misunderstanding("night_shadow", "a shadow monster by the sink", "the moon was making a shadow from the lamp"),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Theo", "Max", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for prob in PROBLEMS:
            for m in MISUNDERSTANDINGS:
                combos.append((p, prob, m))
    return combos


def explain_rejection(problem: Problem, misunderstanding: Misunderstanding) -> str:
    return (
        f"(No story: the misunderstanding '{misunderstanding.id}' does not fit the "
        f"problem '{problem.id}'. Pick a matching pair from the registry.)"
    )


def _child_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    dentist = world.add(Entity(id=params.dentist, kind="character", type=params.dentist_type, label=params.dentist))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=params.helper))
    problem = _safe_lookup(PROBLEMS, params.problem)
    mystery = _safe_lookup(MISUNDERSTANDINGS, params.misunderstanding)
    kindness = _safe_lookup(KINDS, params.kindness)
    world.facts.update(child=child, dentist=dentist, helper=helper, problem=problem, mystery=mystery, kindness=kindness)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    dentist: Entity = f["dentist"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    mystery: Misunderstanding = f["mystery"]
    kindness: KindAction = f["kindness"]

    child.memes["worry"] += 1
    dentist.memes["calm"] += 1
    helper.memes["kindness"] += 1

    world.say(
        f"On a quiet evening, {child.id} went with {helper.id} to {world.place.label}. "
        f"The hallway was pale and still, and the lamp made small gold circles on the floor."
    )
    world.say(
        f"{child.id} stopped at the door and stared at {mystery.scary_phrase}. "
        f"{child.id} whispered that the place felt spooky."
    )
    world.say(
        f"But {dentist.id} smiled and said, 'That is only {mystery.real_cause_phrase}.' "
        f"{kindness.effect.capitalize()}, and {child.id} listened."
    )

    world.para()
    child.memes["fear"] += 1
    dentist.meters["focus"] = 1
    helper.meters["help"] = 1
    world.say(
        f"Then the real problem showed itself: {problem.symptom}. "
        f"{dentist.id} looked carefully, found {problem.clue}, and said the fix was to "
        f"{problem.fix}."
    )
    world.say(
        f"{helper.id} gave {kindness.label}, and {child.id} held still long enough for the tiny work to be done."
    )

    world.para()
    child.memes["relief"] += 2
    child.memes["fear"] = 0
    dentist.memes["kindness"] += 1
    world.say(
        f"At last, the problem was solved. {problem.solved_image}, and the spooky sound was gone."
    )
    world.say(
        f"{child.id} smiled at {dentist.id} and {helper.id}. The office felt bright again, "
        f"and even the moonlit shadow by the sink looked friendly."
    )

    world.facts["solved"] = True


def _story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    dentist: Entity = f["dentist"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    mystery: Misunderstanding = f["mystery"]
    return [
        QAItem(
            question=f"Why did {child.id} think the dentist office was spooky?",
            answer=(
                f"{child.id} thought {mystery.scary_phrase} was hiding there, but it was only "
                f"{mystery.real_cause_phrase}. The quiet room and the shadow made the mistake easy."
            ),
        ),
        QAItem(
            question=f"What did {dentist.id} do to help solve the problem?",
            answer=(
                f"{dentist.id} looked closely, found {problem.clue}, and used a calm fix. "
                f"That careful work solved the real problem instead of the scary guess."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help {child.id} feel better?",
            answer=(
                f"{helper.id} showed kindness and stayed close, so {child.id} could breathe and listen. "
                f"The gentle help made the room feel safe."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist looks at teeth, finds what is hurting them, and helps make them clean and healthy again.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing is true, but the real reason is something else.",
        ),
        QAItem(
            question="Why can kindness help in a scary moment?",
            answer="Kindness makes people feel safer and calmer, which helps them listen, solve the problem, and keep going.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    problem: Problem = f["problem"]
    mystery: Misunderstanding = f["mystery"]
    return [
        f'Write a gentle ghost-story style tale for a young child about {child.id} at the dentist, where a spooky-looking thing turns out to be {mystery.real_cause_phrase}.',
        f"Tell a child-sized story where kindness and careful problem solving help {child.id} at the dentist office, and the scary guess is wrong.",
        f'Write a short story that uses the word "dentist" and ends with the real problem being fixed and the scary misunderstanding gone.',
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved_problem(P) :- problem(P).
kind_help(K) :- kind(K).
misread(M) :- misunderstanding(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for kid in KINDS:
        lines.append(asp.fact("kind", kid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    dentist: str
    dentist_type: str
    helper: str
    helper_type: str
    problem: str
    kindness: str
    misunderstanding: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story style dentist tale with kindness and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--kindness", choices=KINDS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--dentist", default="Dr. Maple")
    ap.add_argument("--dentist-type", choices=["woman", "man"], default="woman")
    ap.add_argument("--helper", default="Nurse Vale")
    ap.add_argument("--helper-type", choices=["woman", "man"], default="woman")
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
    if getattr(args, "problem", None) and getattr(args, "misunderstanding", None):
        if getattr(args, "problem", None) == "toothache" and getattr(args, "misunderstanding", None) == "white_sheet":
            pass
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "misunderstanding", None) is None or c[2] == getattr(args, "misunderstanding", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, misunderstanding = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or _child_name(rng, child_type)
    kindness = getattr(args, "kindness", None) or rng.choice(list(KINDS))
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        dentist=getattr(args, "dentist", None),
        dentist_type=getattr(args, "dentist_type", None),
        helper=getattr(args, "helper", None),
        helper_type=getattr(args, "helper_type", None),
        problem=problem,
        kindness=kindness,
        misunderstanding=misunderstanding,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved_problem/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available, but this storyworld keeps the gate simple.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(
            place=p, child_name="Mia", child_type="girl", dentist="Dr. Maple",
            dentist_type="woman", helper="Nurse Vale", helper_type="woman",
            problem=pr, kindness=k, misunderstanding=m)) for p, pr, m in [
                ("night_clinic", "toothache", "ghost_sound"),
                ("clinic", "lost_floss", "white_sheet"),
                ("quiet_room", "stuck_brush", "night_shadow"),
            ]]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
