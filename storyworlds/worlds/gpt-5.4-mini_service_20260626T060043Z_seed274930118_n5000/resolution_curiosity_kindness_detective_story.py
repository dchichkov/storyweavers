#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/resolution_curiosity_kindness_detective_story.py
==============================================================================================================

A small detective-style storyworld about curiosity, kindness, and resolution.

The seed tale behind this world:
A child detective notices a missing thing, follows clues with curiosity, and
uses kindness to ask gentle questions. The search turns up a surprising but
safe explanation, and the case ends with a clear resolution.

This world keeps the domain small on purpose:
- one young detective
- one missing object
- one place
- one gentle helper or creature
- one causal turn from curiosity to kindness to resolution

The prose is driven by a tiny world model rather than a frozen template:
meters track physical facts like clue visibility and object location, while
memes track curiosity, worry, and kindness.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class Case:
    id: str
    missing_label: str
    missing_phrase: str
    clue: str
    clue_kind: str
    explanation: str
    reveal: str
    kind_act: str
    curiosity_boost: float = 1.0
    kindness_boost: float = 1.0
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
class StoryParams:
    setting: str
    case: str
    name: str
    gender: str
    sidekick: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", affordances={"search"}),
    "garden": Setting(place="the garden", mood="bright", affordances={"search"}),
    "station": Setting(place="the old train station", mood="echoing", affordances={"search"}),
}

CASES = {
    "missing_cookie": Case(
        id="missing_cookie",
        missing_label="cookie",
        missing_phrase="a warm cookie on a blue plate",
        clue="a tiny trail of crumbs",
        clue_kind="crumbs",
        explanation="the puppy carried it to the reading rug and nibbled it there",
        reveal="the little puppy had tucked the cookie under a stack of storybooks",
        kind_act="ask the puppy gently",
    ),
    "missing_key": Case(
        id="missing_key",
        missing_label="key",
        missing_phrase="a brass key on a red ribbon",
        clue="a soft clink from the flower pot",
        clue_kind="sound",
        explanation="the key slipped from a pocket and landed beside a watering can",
        reveal="the brass key was caught under the flower pot",
        kind_act="look under the pot with a careful smile",
    ),
    "missing_hat": Case(
        id="missing_hat",
        missing_label="hat",
        missing_phrase="a small felt hat",
        clue="a ribbon fluttering near the bench",
        clue_kind="ribbon",
        explanation="the wind pushed the hat onto the bench, and a crow was peeking at it",
        reveal="the felt hat had blown onto the bench beside the crow",
        kind_act="speak kindly to the crow",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ruby", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Max", "Finn", "Eli"]
SIDEKICKS = ["a small dog", "a friendly cat", "a quiet crow", "a neighbor", "a little mouse"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny curiosity-and-kindness detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, case=case, name=name, gender=gender, sidekick=sidekick)


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASES]


def reasonableness_gate(setting: str, case: str) -> bool:
    return setting in SETTINGS and case in CASES


def _make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    world = World(setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 0.0, "worry": 0.0, "joy": 0.0},
        memes={"curiosity": 0.0, "kindness": 0.0, "care": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="creature" if "dog" in params.sidekick or "cat" in params.sidekick or "crow" in params.sidekick else "person",
        label=params.sidekick,
        meters={"nervous": 0.0},
        memes={"trust": 0.0},
    ))
    missing = world.add(Entity(
        id="missing",
        type=case.missing_label,
        label=case.missing_label,
        phrase=case.missing_phrase,
        owner="detective",
        location="missing",
        meters={"found": 0.0},
    ))
    world.facts = {
        "detective": detective,
        "helper": helper,
        "missing": missing,
        "case": case,
        "setting": setting,
    }
    return world


def _clue(world: World, detective: Entity, case: Case) -> None:
    detective.memes["curiosity"] += case.curiosity_boost
    detective.meters["curiosity"] += case.curiosity_boost
    world.say(
        f"{detective.label} was a small detective with bright eyes and a careful notebook. "
        f"{detective.pronoun().capitalize()} noticed {case.clue} and wrote it down."
    )


def _ask_kindly(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    detective.memes["kindness"] += case.kindness_boost
    detective.memes["care"] += 1.0
    helper.memes["trust"] += 1.0
    helper.meters["nervous"] = 0.0
    world.say(
        f"Instead of guessing, {detective.label} chose to {case.kind_act}. "
        f"{detective.pronoun().capitalize()} spoke softly to {helper.label}, and that gentle way made the room feel safer."
    )


def _reveal(world: World, detective: Entity, helper: Entity, case: Case, missing: Entity) -> None:
    detective.meters["joy"] += 1.0
    detective.memes["care"] += 1.0
    missing.meters["found"] = 1.0
    missing.location = "found"
    world.say(
        f"That was the resolution: {case.reveal}. "
        f"{detective.label} smiled, {helper.label} relaxed, and {detective.pronoun()} brought {missing.label} back where it belonged."
    )


def tell_story(params: StoryParams) -> World:
    world = _make_world(params)
    detective = world.get("detective")
    helper = world.get("helper")
    missing = world.get("missing")
    case = _safe_fact(world, world.facts, "case")

    world.say(
        f"At {world.setting.place}, the air felt {world.setting.mood}, and {detective.label} wanted to solve a mystery."
    )
    world.say(
        f"The problem was simple but puzzling: {detective.pronoun('possessive')} {missing.label} was gone."
    )
    world.para()

    _clue(world, detective, case)
    world.say(
        f"{detective.label}'s curiosity grew stronger, so {detective.pronoun()} followed the clue instead of rushing past it."
    )
    world.para()

    _ask_kindly(world, detective, helper, case)
    world.say(
        f"Because {detective.label} used kindness, {helper.label} did not hide anything. "
        f"{helper.pronoun().capitalize()} pointed to the right place with a tiny, helpful nod."
    )
    world.para()

    _reveal(world, detective, helper, case, missing)
    world.say(
        f"By the end, the mystery was solved, {detective.label}'s notebook was full, and the missing thing was safe again."
    )

    world.facts.update(
        setting=params.setting,
        case=params.case,
        name=params.name,
        gender=params.gender,
        sidekick=params.sidekick,
        story_complete=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    case = _safe_fact(world, f, "case")
    return [
        f"Write a short detective story for a young child where {detective.label} follows clues with curiosity.",
        f"Tell a gentle mystery about a missing {case.missing_label} and let kindness help solve it.",
        f"Write a story in which the words curiosity, kindness, and resolution all matter to the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    missing = _safe_fact(world, f, "missing")
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in the story?",
            answer=f"{detective.label} was the young detective trying to solve the mystery.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was {missing.phrase}.",
        ),
        QAItem(
            question=f"Why did the detective ask {helper.label} so gently?",
            answer=(
                f"{detective.label} used kindness because a gentle question helps other characters feel safe enough to share clues."
            ),
        ),
        QAItem(
            question=f"What clue helped the detective keep going?",
            answer=f"The clue was {case.clue}.",
        ),
        QAItem(
            question=f"What was the resolution of the mystery?",
            answer=f"The resolution was that {case.reveal}, so the missing {case.missing_label} was found and brought back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look closer, ask why, and learn more.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and caring so other people or animals feel safe and respected.",
        ),
        QAItem(
            question="What is a resolution in a story?",
            answer="A resolution is the part at the end when the problem gets solved or settled.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i + 1}. {p}" for i, p in enumerate(sample.prompts)], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: {ent.label or ent.type} meters={meters} memes={memes} location={ent.location}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
case(C) :- case_fact(C).
valid_story(S,C) :- setting(S), case(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy by contract inside ASP helpers
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for c in CASES:
        lines.append(asp.fact("case_fact", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate for {len(py)} combos.")
        return 0
    print("MISMATCH")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="library", case="missing_cookie", name="Mina", gender="girl", sidekick="a small dog"),
    StoryParams(setting="garden", case="missing_key", name="Theo", gender="boy", sidekick="a neighbor"),
    StoryParams(setting="station", case="missing_hat", name="Ruby", gender="girl", sidekick="a quiet crow"),
]


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, case=case, name=name, gender=gender, sidekick=sidekick)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/case combos:")
        for s, c in combos:
            print(f"  {s:8} {c}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
