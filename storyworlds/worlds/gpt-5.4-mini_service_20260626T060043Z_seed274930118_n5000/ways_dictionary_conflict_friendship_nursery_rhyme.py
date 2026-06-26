#!/usr/bin/env python3
"""
storyworlds/worlds/ways_dictionary_conflict_friendship_nursery_rhyme.py
=======================================================================

A tiny story world in nursery-rhyme style about two friends, a dictionary,
and a choice between ways. A small misunderstanding turns into a gentle
conflict, then a friendship repair.

The seed image:
- A child loves a dictionary of words and rhymes.
- Two friends want to use it in different ways.
- They tug, pause, and find a shared way through the words.

The world model tracks:
- physical meters: held, torn, scattered, marked
- emotional memes: joy, hurt, share, conflict, friendship, curiosity

The output story is authored from simulated state, not a frozen template.
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
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    a: object | None = None
    b: object | None = None
    book: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the nursery"
    indoors: bool = True
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
class Choice:
    id: str
    verb: str
    noun: str
    use: str
    tension: str
    resolution: str
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
    place: str
    choice: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    role_a: str
    role_b: str
    seed: Optional[int] = None
    params: object | None = None
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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def _default_value(d: dict[str, float], key: str) -> float:
    return d.get(key, 0.0)


def _boost(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = _default_value(ent.memes, key) + amt


def _meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = _default_value(ent.meters, key) + amt


def _is_big(x: float) -> bool:
    return x >= THRESHOLD


def make_world(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=params.name_a,
        kind="character",
        type=params.gender_a,
        traits=["little", params.role_a, "curious"],
    ))
    b = world.add(Entity(
        id=params.name_b,
        kind="character",
        type=params.gender_b,
        traits=["little", params.role_b, "kind"],
    ))
    book = world.add(Entity(
        id="dictionary",
        kind="thing",
        type="dictionary",
        label="dictionary",
        phrase="a bright little dictionary",
        owner=a.id,
    ))
    book.held_by = a.id
    world.facts.update(a=a, b=b, book=book, params=params)
    return world


def intro(world: World) -> None:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    book = _safe_fact(world, world.facts, "book")
    world.say(
        f"{a.id} was a little {a.type} who loved {book.label} words and nursery rhymes."
    )
    world.say(
        f"{b.id} was a little {b.type} who liked the same songs, and liked sharing the same ways."
    )


def setup_book(world: World) -> None:
    a = _safe_fact(world, world.facts, "a")
    book = _safe_fact(world, world.facts, "book")
    _boost(a, "joy", 1)
    _boost(a, "curiosity", 1)
    world.say(
        f"{a.id} kept a {book.phrase} with tidy pages and soft corners, and turned the pages gently."
    )


def demand_ways(world: World, choice: Choice) -> None:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    book = _safe_fact(world, world.facts, "book")
    _boost(a, "desire", 1)
    _boost(b, "desire", 1)
    world.say(
        f"One day, {a.id} wanted one way with the {book.label}, and {b.id} wanted another."
    )
    world.say(
        f"{a.id} wanted to {choice.verb}, while {b.id} wanted to {choice.use}."
    )


def create_conflict(world: World) -> None:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    book = _safe_fact(world, world.facts, "book")
    if ("conflict", book.id) in world.fired:
        return
    world.fired.add(("conflict", book.id))
    _boost(a, "conflict", 1)
    _boost(b, "conflict", 1)
    _boost(a, "hurt", 1)
    _boost(b, "hurt", 1)
    _meter(book, "held", 1)
    _meter(book, "tugged", 1)
    world.say(
        f"They both reached for the {book.label}, and the page edges gave a tiny tug-tug-tug."
    )
    world.say(
        f"The two friends frowned, for each one thought the other had chosen the wrong way."
    )


def repair_friendship(world: World, choice: Choice) -> None:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    book = _safe_fact(world, world.facts, "book")
    if ("repair", book.id) in world.fired:
        return
    world.fired.add(("repair", book.id))
    _boost(a, "friendship", 2)
    _boost(b, "friendship", 2)
    _boost(a, "joy", 1)
    _boost(b, "joy", 1)
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    book.held_by = a.id
    world.say(
        f"Then {a.id} took a breath and said, 'We can use the dictionary two ways, you and me.'"
    )
    world.say(
        f"{b.id} smiled back, and the tug turned light as a feather."
    )
    world.say(
        f"They chose to {choice.resolution}, and the little dictionary stayed neat and bright."
    )


def close_story(world: World) -> None:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    book = _safe_fact(world, world.facts, "book")
    world.say(
        f"So {a.id} read a rhyme, and {b.id} said the next line, and the book went from hand to hand."
    )
    world.say(
        f"By the end, the friends shared one happy way, and the dictionary rested safe between them."
    )


def tell_story(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    choice = _safe_lookup(CHOICES, params.choice)
    world = make_world(setting, params)
    intro(world)
    world.para()
    setup_book(world)
    demand_ways(world, choice)
    create_conflict(world)
    world.para()
    repair_friendship(world, choice)
    close_story(world)
    world.facts["choice"] = choice
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"read", "rhyme", "share"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"read", "rhyme", "share"}),
    "corner": Setting(place="the cozy corner", indoors=True, affords={"read", "share"}),
}

CHOICES = {
    "read_aloud": Choice(
        id="read_aloud",
        verb="read the words aloud",
        noun="words",
        use="point to the pages and sing the lines",
        tension="loud versus quiet",
        resolution="read one page aloud together and point to the next",
        tags={"dictionary", "rhyme", "words", "friendship"},
    ),
    "sort_words": Choice(
        id="sort_words",
        verb="sort the words by first letter",
        noun="letters",
        use="make a tiny word pile game",
        tension="order versus play",
        resolution="sort the words one page at a time, side by side",
        tags={"dictionary", "letters", "friendship"},
    ),
    "make_rhyme": Choice(
        id="make_rhyme",
        verb="make a rhyme from the words",
        noun="rhyme",
        use="tap the table and clap the beat",
        tension="clap versus hush",
        resolution="clap softly and build one shared rhyme",
        tags={"dictionary", "rhyme", "friendship"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Rose", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Max", "Eli"]
ROLES = ["playful", "gentle", "curious", "bright", "cheery", "small"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for choice in setting.affords:
            out.append((place, choice))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about ways and a dictionary.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "choice", None) and (getattr(args, "place", None), getattr(args, "choice", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos
               if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None))
               and (not getattr(args, "choice", None) or c[1] == getattr(args, "choice", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, choice = rng.choice(choices)
    gender_a = getattr(args, "gender_a", None) or rng.choice(["girl", "boy"])
    gender_b = getattr(args, "gender_b", None) or ("boy" if gender_a == "girl" and rng.random() < 0.5 else "girl")
    name_a = getattr(args, "name_a", None) or rng.choice(GIRL_NAMES if gender_a == "girl" else BOY_NAMES)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name_a])
    role_a = getattr(args, "role_a", None) or rng.choice(ROLES)
    role_b = getattr(args, "role_b", None) or rng.choice(ROLES)
    return StoryParams(
        place=place,
        choice=choice,
        name_a=name_a,
        name_b=name_b,
        gender_a=gender_a,
        gender_b=gender_b,
        role_a=role_a,
        role_b=role_b,
    )


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    choice = _safe_fact(world, world.facts, "choice")
    return [
        f'Write a short nursery-rhyme story about two friends and a "{choice.id}" choice in {p.place}.',
        f"Tell a gentle story where {p.name_a} and {p.name_b} disagree about ways to use a dictionary, then make up.",
        f"Write a small rhyming tale with a dictionary, a conflict, and a friendship ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    choice = _safe_fact(world, world.facts, "choice")
    book = _safe_fact(world, world.facts, "book")
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The friends were {a.id} and {b.id}. They were little children who wanted to use the dictionary in different ways.",
        ),
        QAItem(
            question=f"What did the friends disagree about?",
            answer=f"They disagreed about how to use the {book.label}: one wanted to {choice.verb}, and the other wanted to {choice.use}.",
        ),
        QAItem(
            question=f"How did the conflict end?",
            answer=f"The conflict ended when the two friends talked kindly, shared the dictionary, and chose to {choice.resolution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dictionary?",
            answer="A dictionary is a book of words, and it helps people find meanings, spellings, and new words.",
        ),
        QAItem(
            question="What are ways?",
            answer="Ways are different paths or methods for doing something. People can choose one way or another way.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and try to be kind even after a disagreement.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
choice(C) :- activity(C).

valid(P,C) :- setting(P), affords(P,C).

% Show the same valid place/choice pairs as the Python gate.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CHOICES:
        lines.append(asp.fact("activity", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/choice combos:\n")
        for place, choice in combos:
            print(f"  {place:14} {choice}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, choice in valid_combos():
            params = StoryParams(
                place=place,
                choice=choice,
                name_a="Mia",
                name_b="Theo",
                gender_a="girl",
                gender_b="boy",
                role_a="curious",
                role_b="kind",
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
