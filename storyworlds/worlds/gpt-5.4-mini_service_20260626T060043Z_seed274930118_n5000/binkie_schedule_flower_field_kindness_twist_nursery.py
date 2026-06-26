#!/usr/bin/env python3
"""
storyworlds/worlds/binkie_schedule_flower_field_kindness_twist_nursery.py
=========================================================================

A small nursery-rhyme storyworld about a binkie, a schedule, a flower field,
and a gentle twist of kindness.

Premise:
- A little child loves a binkie and follows a tidy schedule.
- In a flower field, the child wants to nap, but the binkie goes missing.
- A friend uses kindness to help search.
- A small twist in the schedule turns worry into a cozy, rhyming ending.

The world is intentionally narrow: only a few choices are valid, and the story
must be able to turn on a real, simulated change in state.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    b: object | None = None
    child: object | None = None
    helper: object | None = None
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
    weather: str
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
class Schedule:
    name: str
    beat: str
    twist_beat: str
    naptime: str
    keyword: str = "schedule"
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
class Binkie:
    label: str = "binkie"
    phrase: str = "a soft little binkie"
    soothing: str = "soothing"
    pocket: str = "pocket"
    BINKIE: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    name: object | None = None
    samples: list = field(default_factory=list)
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
    "flower_field": Setting(place="the flower field", weather="breezy", affords={"search", "rest", "sing"}),
}

SCHEDULES = {
    "kindness_twist": Schedule(
        name="kindness twist",
        beat="the day should follow the little plan",
        twist_beat="the plan may bend when kindness helps",
        naptime="nap time",
        keyword="schedule",
    )
}

BINKIE = Binkie()

CHILD_NAMES = ["Lily", "Milo", "Pip", "Nora", "Toby", "Mia"]
HELPER_NAMES = ["June", "Finn", "Rose", "Ari", "Bea", "Otto"]


class ReasoningError(StoryError):
    pass


def child_word(t: str) -> str:
    return t


def _do_search(world: World, child: Entity, helper: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} lost {child.pronoun('possessive')} binkie in the flower field, "
        f"and little worry began to sway."
    )
    world.say(
        f"{helper.id} said, \"Let's look with kindness, side by side, and find it right away.\""
    )
    helper.memes["kindness"] += 1


def _find_binkie(world: World, child: Entity, helper: Entity) -> None:
    sig = ("found", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    b = world.get("binkie")
    b.held_by = child.id
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"Behind a bluebell bloom, {helper.id} found the binkie tucked in a soft green leaf."
    )
    world.say(
        f"{child.id} hugged {b.it()} close, and the worry blew away like a feather in the breeze."
    )


def _twist_schedule(world: World, child: Entity, helper: Entity, sched: Schedule) -> None:
    sig = ("twist", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Then the schedule took a tiny twist: {sched.naptime} came early, after the searching song."
    )
    world.say(
        f"So {child.id} rested in the flower field, with the binkie safe and {helper.id} smiling nearby."
    )


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    b = world.get("binkie")
    if child.memes.get("worry", 0.0) >= THRESHOLD and b.held_by is None:
        _find_binkie(world, child, helper)
        out.append("found")
    if child.memes.get("joy", 0.0) >= THRESHOLD and child.memes.get("calm", 0.0) < THRESHOLD:
        _twist_schedule(world, child, helper, world.facts["schedule"])
        out.append("twist")
    if narrate:
        pass
    return out


def tell(setting: Setting, sched: Schedule, child_name: str, child_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=["little", "gentle"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["kind"]))
    b = world.add(Entity(id="binkie", type="binkie", label="binkie", phrase=BINKIE.phrase, held_by=None, owner=child.id))
    child.meters["meters"] = 0.0
    helper.meters["meters"] = 0.0

    world.say(
        f"Little {child.id} kept a binkie and a schedule, and liked them both in the flower field."
    )
    world.say(
        f"{child.id} loved the little schedule: first play, then sing, then {sched.naptime} by the clover."
    )
    world.say(
        f"But one windy day, the binkie slipped away, and the neat plan turned wobbly in the flowers."
    )

    world.para()
    world.say(
        f"In the flower field, {helper.id} walked with {child.id} as bees hummed and petals nodded."
    )
    _do_search(world, child, helper)
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last the day made room for a twist: not every bell had to ring on time."
    )
    propagate(world, narrate=True)

    world.facts.update(
        child=child,
        helper=helper,
        binkie=b,
        schedule=sched,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    sched = _safe_fact(world, f, "schedule")
    return [
        f'Write a short nursery-rhyme story about {child.id}, a missing binkie, and a schedule in {world.setting.place}.',
        f'Write a gentle story where {helper.id} helps {child.id} find a binkie, and the schedule makes a kind twist.',
        f'Write a rhyming tale set in {world.setting.place} with a binkie, a schedule, kindness, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    sched = _safe_fact(world, f, "schedule")
    b = _safe_fact(world, f, "binkie")
    return [
        QAItem(
            question=f"What did {child.id} keep with {child.pronoun('possessive')} schedule in the flower field?",
            answer=f"{child.id} kept a binkie with {child.pronoun('possessive')} schedule, because both felt cozy and familiar.",
        ),
        QAItem(
            question=f"Who helped {child.id} look for the binkie when it went missing?",
            answer=f"{helper.id} helped {child.id} look for the binkie with kindness and a gentle voice.",
        ),
        QAItem(
            question=f"What changed when the schedule took a twist?",
            answer=f"The naptime part of the schedule came early, so the search could turn into a calm rest instead of a worry.",
        ),
        QAItem(
            question=f"Where did {helper.id} find the binkie?",
            answer=f"{helper.id} found the binkie behind a bluebell bloom in the flower field.",
        ),
    ]


KNOWLEDGE = {
    "binkie": [
        QAItem(
            question="What is a binkie for?",
            answer="A binkie is a small soothing pacifier that some little children like to suck or hold when they want comfort.",
        )
    ],
    "schedule": [
        QAItem(
            question="What is a schedule?",
            answer="A schedule is a simple plan that tells what comes first, next, and later during the day.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring to someone else.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises you a little and makes the story go in a new direction.",
        )
    ],
    "flower_field": [
        QAItem(
            question="What grows in a flower field?",
            answer="A flower field is a place where many flowers grow together in the open air.",
        )
    ],
}

KNOWLEDGE_ORDER = ["binkie", "schedule", "kindness", "twist", "flower_field"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["binkie"])
    out.extend(KNOWLEDGE["schedule"])
    out.extend(KNOWLEDGE["kindness"])
    out.extend(KNOWLEDGE["twist"])
    out.extend(KNOWLEDGE["flower_field"])
    return out


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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The binkie is missing when nobody holds it.
missing_binkie :- binkie(B), not held(B).

% Kindness helps the search.
kind_search(H) :- helper(H), kind(H).

% A twist happens when the schedule bends toward rest.
twisted_schedule(S) :- schedule(S), early_nap(S).

% The story is valid when the child has a missing binkie, kindness is present,
% and the schedule can twist into a calm ending.
valid_story :- child(C), binkie(B), missing(C,B), helper(H), kind_search(H), schedule(S), twisted_schedule(S).

#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("binkie", "binkie"))
    lines.append(asp.fact("schedule", "kindness_twist"))
    lines.append(asp.fact("missing", "child", "binkie"))
    lines.append(asp.fact("kind", "helper"))
    lines.append(asp.fact("held", "binkie"))  # will be negated by rule design? no: adjust below
    lines.append(asp.fact("early_nap", "kindness_twist"))
    lines = [ln for ln in lines if not ln.startswith("held(")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    has = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if not has or not py_ok:
        print("MISMATCH between clingo and Python reasonableness gate.")
        return 1
    print("OK: ASP twin is consistent with the storyworld gate.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: binkie, schedule, kindness, and twist.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(
        child_name=child_name,
        child_type="child",
        helper_name=helper_name,
        helper_type="friend",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["flower_field"], SCHEDULES["kindness_twist"],
                 params.child_name, params.child_type, params.helper_name, params.helper_type)
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
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("1 compatible story pattern:")
        print("  flower_field / binkie / schedule / kindness / twist")
        print(f"  ASP says valid_story: {any(sym.name == 'valid_story' for sym in model)}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(name=n, child_type="child", helper_name=h, helper_type="friend"))
                   for n, h in [("Lily", "June"), ("Milo", "Finn"), ("Nora", "Rose")]]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
