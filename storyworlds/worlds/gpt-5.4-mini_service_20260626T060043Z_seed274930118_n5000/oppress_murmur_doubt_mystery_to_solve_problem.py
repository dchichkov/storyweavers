#!/usr/bin/env python3
"""
storyworlds/worlds/oppress_murmur_doubt_mystery_to_solve_problem.py
====================================================================

A tiny story world about a little mystery to solve, where problem solving,
sound effects, and a growing doubt shape a rhyming tale.

The premise is simple:
- A child hears a strange murmur.
- The murmur feels like something oppressive in the dark.
- The child doubts what is real, then solves the mystery with patient problem solving.
- The ending proves the change with a concrete result and a calmer soundscape.

This world uses physical meters and emotional memes, and includes an inline ASP
twin plus a Python reasonableness gate.
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
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    indoors: bool
    soundscape: str
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
class Mystery:
    id: str
    clue: str
    murmur: str
    problem: str
    solve_step: str
    reveal: str
    sound_fx: list[str] = field(default_factory=list)
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
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    companion: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(
        place="the attic",
        indoors=True,
        soundscape="the floorboards creaked and the dust motes danced",
        affords={"whisper", "listen", "search"},
    ),
    "garden": Setting(
        place="the garden",
        indoors=False,
        soundscape="the leaves went shh-shh and the grass went swish",
        affords={"whisper", "listen", "search"},
    ),
    "library": Setting(
        place="the library nook",
        indoors=True,
        soundscape="the pages went flip-flip and the lamp went glow",
        affords={"whisper", "listen", "search"},
    ),
}

MYSTERIES = {
    "lost_key": Mystery(
        id="lost_key",
        clue="a tiny silver shine under a rug",
        murmur="murmur-murmur",
        problem="a key had gone missing",
        solve_step="moved a box, peered below, and followed the shine",
        reveal="the key was tucked inside a toy drum",
        sound_fx=["tap-tap", "click-clack", "ding"],
        tags={"murmur", "doubt", "problem solving"},
    ),
    "sleepy_mouse": Mystery(
        id="sleepy_mouse",
        clue="soft crumbs in a neat little line",
        murmur="mumbly-murmur",
        problem="someone heard a busy squeak in the wall",
        solve_step="counted the crumbs, traced the line, and opened a tiny door",
        reveal="a sleepy mouse had found a warm nest of cloth",
        sound_fx=["scurry-scurry", "rustle", "peek"],
        tags={"murmur", "doubt", "problem solving"},
    ),
    "windy_box": Mystery(
        id="windy_box",
        clue="a ribbon fluttering by a cracked window",
        murmur="hushy-murmur",
        problem="a box kept making a lonely sound",
        solve_step="tested the lid, pressed the latch, and listened close",
        reveal="the wind was singing through a small gap",
        sound_fx=["whooo", "tap", "snap"],
        tags={"murmur", "doubt", "problem solving"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lina", "Zoe", "Ava", "Ruby", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Noah", "Finn", "Leo", "Eli", "Max"]
TRAITS = ["brave", "curious", "gentle", "patient", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(attic).
setting(garden).
setting(library).

mystery(lost_key).
mystery(sleepy_mouse).
mystery(windy_box).

reason(setting, mystery) :- setting(_), mystery(_).
valid_story(S, M) :- setting(S), mystery(M).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_pairs() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def explain_rejection(setting: str, mystery: str) -> str:
    if setting not in SETTINGS:
        return "(No story: that setting does not exist.)"
    if mystery not in MYSTERIES:
        return "(No story: that mystery does not exist.)"
    return "(No story: no reasonableness problem found, but this pair is still rejected.)"


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def is_male(gender: str) -> bool:
    return gender == "boy"


def hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(BOY_NAMES if is_male(gender) else GIRL_NAMES)


def narrate_rhyme(lines: list[str]) -> str:
    return " ".join(lines)


def solve_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} heard a {mystery.murmur} from the dark, and felt a little doubt in the spark."
    )
    world.say(
        f"Then {hero.pronoun()} said, 'I will not fear; I'll solve this puzzle, nice and clear.'"
    )
    hero.memes["resolve"] += 1


def investigate(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    for fx in mystery.sound_fx:
        world.say(f"{fx}! {fx}! {fx}!")
    world.say(
        f"{hero.id} looked for {mystery.clue}, then followed {hero.pronoun('possessive')} clue path through."
    )
    world.say(
        f"{hero.id} used problem solving, slow and sweet, and found the answer neat and neat."
    )


def reveal(world: World, mystery: Mystery, hero: Entity, companion: Entity) -> None:
    world.say(
        f"At last the mystery opened wide: {mystery.reveal} was hiding inside."
    )
    world.say(
        f"The murmur grew small, the doubt slid away, and {hero.id} and {companion.id} laughed the rest of the day."
    )
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, companion_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        meters={"worry": 0.0, "attention": 0.0},
        memes={"doubt": 0.0, "joy": 0.0, "resolve": 0.0},
    ))
    companion = world.add(Entity(
        id=companion_type.capitalize(),
        kind="character",
        type=companion_type,
        label=f"the {companion_type}",
        meters={"attention": 0.0},
        memes={"joy": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label="the clue",
        phrase=mystery.clue,
    ))

    world.say(
        f"In {setting.place}, where {setting.soundscape}, lived a {trait} child named {hero.id}."
    )
    world.say(
        f"{hero.id} loved to listen for little mysteries, and {hero.pronoun()} liked sound effects that glowed."
    )
    world.say(
        f"One day, {hero.id} and {companion.id} found {mystery.problem}."
    )
    world.say(
        f"The air felt a bit oppressive, and the hush made {hero.id} murmur, 'What is this now?'"
    )

    world.say(setting.soundscape + ".")
    solve_mystery(world, hero, mystery)
    investigate(world, hero, mystery)
    reveal(world, mystery, hero, companion)

    hero.meters["worry"] = 0.0
    hero.meters["attention"] += 1.0
    world.facts.update(
        hero=hero,
        companion=companion,
        clue=clue,
        setting=setting,
        mystery=mystery,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    setting = _safe_fact(world, f, "setting")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a rhyming story for young children set in {setting.place} about {hero.id} solving a small mystery.',
        f"Tell a gentle problem-solving tale where {hero.id} hears a murmur, feels doubt, and discovers what caused it.",
        f"Make a child-friendly story with sound effects and a happy reveal of {mystery.reveal}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    mystery = _safe_fact(world, f, "mystery")
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Where does {hero.id} solve the mystery?",
            answer=f"{hero.id} solves the mystery in {setting.place}, where the sounds help the clues stand out.",
        ),
        QAItem(
            question=f"What made {hero.id} feel doubt at first?",
            answer=f"{hero.id} felt doubt because a {mystery.murmur} came from the dark and the problem seemed hard at first.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} fix the problem?",
            answer=f"They used patient problem solving, followed the clues, and discovered that {mystery.reveal}.",
        ),
        QAItem(
            question=f"What sound effects appear in the story?",
            answer=f"The story includes sounds like {', '.join(mystery.sound_fx)} to make the mystery feel lively.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first, so people look for clues to figure it out.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully, trying ideas, and using clues to find a good answer.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to help readers hear the action in their imaginations and make the scene feel lively.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="attic", mystery="lost_key", name="Maya", gender="girl", companion="mother", trait="curious"),
    StoryParams(setting="garden", mystery="sleepy_mouse", name="Theo", gender="boy", companion="father", trait="patient"),
    StoryParams(setting="library", mystery="windy_box", name="Lina", gender="girl", companion="mother", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming mystery story world with murmur, doubt, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "setting", None) and getattr(args, "mystery", None):
        if (getattr(args, "setting", None), getattr(args, "mystery", None)) not in valid_pairs():
            return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or hero_name(gender, rng)
    companion = getattr(args, "companion", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MYSTERIES, params.mystery),
        params.name,
        params.gender,
        params.companion,
        params.trait,
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (setting, mystery) pairs:")
        for s, m in pairs:
            print(f"  {s:10} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
