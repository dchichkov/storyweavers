#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/zipper_flashback_repetition_mystery_to_solve_folk.py
=============================================================================================================

A tiny folk-tale storyworld about a zipper mystery, told with a flashback,
repetition, and a small puzzle that gets solved by careful thinking.

Premise:
A child wants to wear a treasured coat, but its zipper has gone stiff and will
not close. The child remembers an old lesson from a grandparent, repeats the
lesson aloud, and solves the mystery with a simple fix.

The storyworld is deliberately small:
- one child
- one treasured garment with a zipper
- one elder helper
- one problem: a stuck zipper
- one resolution: the zipper slides after the right treatment

The prose is generated from a live state model, not from a fixed paragraph.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    coat: object | None = None
    elder: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather", "uncle"}:
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
    place: str = "the village lane"
    weather: str = "cold"
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
class Problem:
    id: str
    verb: str
    detail: str
    symptom: str
    fix_hint: str
    keyword: str = "zipper"
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    region: str = "torso"
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
class Remedy:
    id: str
    label: str
    prep: str
    action: str
    tail: str
    tool: str
    guards: set[str] = field(default_factory=set)
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def zip_state(world: World, coat: Entity) -> str:
    if coat.meters.get("stuck", 0.0) >= THRESHOLD:
        return "stuck"
    if coat.meters.get("fixed", 0.0) >= THRESHOLD:
        return "smooth"
    return "unclear"


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    coat = world.get("coat")
    if coat.meters.get("stuck", 0.0) < THRESHOLD:
        return out
    sig = ("mystery", coat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["mystery"] = True
    out.append("The zipper would not budge, and the child frowned at the little metal teeth.")
    return out


def _r_remedy(world: World) -> list[str]:
    out: list[str] = []
    coat = world.get("coat")
    tool = world.get("tool")
    if coat.meters.get("stuck", 0.0) < THRESHOLD:
        return out
    if tool.meters.get("used", 0.0) < THRESHOLD:
        return out
    sig = ("fix", coat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    coat.meters["stuck"] = 0.0
    coat.meters["fixed"] = 1.0
    out.append("After that, the zipper slid along as if it had been waiting for the right song.")
    return out


CAUSAL_RULES = [_r_mystery, _r_remedy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_fix(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.get("coat").meters.get("fixed", 0.0) >= THRESHOLD


def introduce(world: World, child: Entity, elder: Entity, coat: Entity) -> None:
    world.say(
        f"Once in a little village, {child.id} loved a warm {coat.label} that "
        f"{child.pronoun('possessive')} {elder.label} had saved for cold days."
    )
    world.say(
        f"The coat had a bright zipper, and the child liked how it shone like a "
        f"small silver river."
    )


def flashback(world: World, child: Entity, elder: Entity, coat: Entity) -> None:
    world.say(
        f"Then {child.id} remembered a story from long ago: {elder.id} had once said, "
        f'"A zipper likes a gentle hand, a straight start, and patience."'
    )
    world.say(
        f"That old lesson stayed in {child.pronoun('possessive')} mind like a lantern "
        f"kept near the hearth."
    )


def repeat_lesson(world: World, child: Entity) -> None:
    child.memes["resolve"] = child.memes.get("resolve", 0.0) + 1
    world.say(
        f"So {child.id} whispered the lesson again and again: "
        f'"A gentle hand, a straight start, and patience."'
    )
    world.say(
        f'"A gentle hand, a straight start, and patience," {child.id} repeated, '
        f"as if the words themselves could help."
    )


def pose_mystery(world: World, child: Entity, coat: Entity) -> None:
    coat.meters["stuck"] = 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"But when {child.id} tried to wear the coat, the zipper caught on itself and would not close."
    )
    propagate(world, narrate=True)


def ask_helper(world: World, child: Entity, elder: Entity, coat: Entity) -> None:
    world.say(
        f"{child.id} called for {elder.id}, who came with calm eyes and a small tin of wax."
    )
    world.say(
        f'"What hides the zipper?" {elder.id} asked. "A little thread, a dry tooth, or a crooked pull?"'
    )
    world.facts["mystery_question"] = "What is blocking the zipper?"


def solve(world: World, child: Entity, elder: Entity, coat: Entity, tool: Entity) -> None:
    if not predict_fix(world):
        pass
    tool.meters["used"] = 1.0
    world.say(
        f"{elder.id} rubbed a touch of wax on the zipper and nudged it with a small pull tab."
    )
    world.say(
        f"{child.id} held the coat still, just as {elder.id} showed {child.pronoun('object')}."
    )
    propagate(world, narrate=True)
    child.memes["worry"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"At last the coat closed, warm and neat, and {child.id} smiled at the solved little mystery."
    )


def tell(setting: Setting, problem: Problem, treasure: Treasure, remedy: Remedy) -> World:
    world = World(setting)
    child = world.add(Entity(id="Pip", kind="character", type="boy", traits=["small", "patient"]))
    elder = world.add(Entity(id="Gran", kind="character", type="grandmother", label="grandmother"))
    coat = world.add(Entity(
        id="coat",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=child.id,
        caretaker=elder.id,
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=remedy.tool,
        phrase=remedy.tool,
        owner=elder.id,
    ))

    world.facts.update(child=child, elder=elder, coat=coat, tool=tool, problem=problem, remedy=remedy)

    introduce(world, child, elder, coat)
    world.para()
    pose_mystery(world, child, coat)
    flashback(world, child, elder, coat)
    repeat_lesson(world, child)
    ask_helper(world, child, elder, coat)
    world.para()
    solve(world, child, elder, coat, tool)
    return world


SETTINGS = {
    "village": Setting(place="the village lane", weather="cold", affords={"zipper"}),
    "cottage": Setting(place="the cottage door", weather="windy", affords={"zipper"}),
    "market": Setting(place="the market path", weather="chilly", affords={"zipper"}),
}

PROBLEMS = {
    "zipper": Problem(
        id="zipper",
        verb="zip",
        detail="a tiny metal zipper on a coat",
        symptom="it would not close",
        fix_hint="wax, patience, and a straight pull",
        keyword="zipper",
        tags={"zipper", "mystery", "flashback", "repetition"},
    ),
}

TREASURES = {
    "coat": Treasure(id="coat", label="coat", phrase="a warm wool coat", type="coat"),
    "cloak": Treasure(id="cloak", label="cloak", phrase="a blue cloak with a bright lining", type="cloak"),
}

REMEDIES = {
    "wax": Remedy(
        id="wax",
        label="wax",
        prep="rub wax on the zipper",
        action="rubbed",
        tail="the zipper learned to slide",
        tool="a little tin of wax",
        guards={"zipper"},
    ),
}

CURATED = [
    ("village", "zipper", "coat"),
    ("cottage", "zipper", "cloak"),
]


@dataclass
class StoryParams:
    setting: str
    problem: str
    treasure: str
    seed: Optional[int] = None
    combos: list = field(default_factory=list)
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
    ap = argparse.ArgumentParser(description="A folk-tale zipper mystery with flashback and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--treasure", choices=TREASURES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or "zipper"
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    if problem != "zipper":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, problem=problem, treasure=treasure)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a child about a zipper that will not close.',
        f"Tell a gentle story where {f['child'].id} remembers an old lesson from {f['elder'].id} and solves the zipper mystery.",
        "Write a repetitive, cozy story with a flashback and a solved little problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, coat = f["child"], f["elder"], f["coat"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was that {child.id}'s {coat.label} had a zipper that would not close.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the problem?",
            answer=f"{elder.id}, the grandmother, helped by giving calm advice and using wax.",
        ),
        QAItem(
            question="What lesson did the child repeat?",
            answer='The child repeated, "A gentle hand, a straight start, and patience."',
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The zipper slid closed, and the {coat.label} became warm and neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zipper for?",
            answer="A zipper joins two sides of cloth or another material so they can close and open again.",
        ),
        QAItem(
            question="Why can a zipper get stuck?",
            answer="A zipper can get stuck if the teeth are crooked, dirty, or caught on cloth.",
        ),
        QAItem(
            question="What is wax used for in this story?",
            answer="Wax can help a stiff zipper slide more easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(Zip) :- zipper(Zip), stuck(Zip).
solved(Zip) :- zipper(Zip), fixed(Zip).
compatible(Zip) :- zipper(Zip), wax_help(Zip).

valid_story(Setting, Zip, Treasure) :- setting(Setting), zipper(Zip), treasure(Treasure),
                                      allowed(Setting, Zip), compatible(Zip).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("allowed", sid, a))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("zipper", pid))
        lines.append(asp.fact("stuck", pid))
        lines.append(asp.fact("wax_help", pid))
    for tid, tre in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {(s, "zipper", t) for s in SETTINGS for t in TREASURES}
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python.")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(TREASURES, params.treasure), REMEDIES["wax"])
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = [StoryParams(setting=s, problem=p, treasure=t) for s, p, t in CURATED]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
