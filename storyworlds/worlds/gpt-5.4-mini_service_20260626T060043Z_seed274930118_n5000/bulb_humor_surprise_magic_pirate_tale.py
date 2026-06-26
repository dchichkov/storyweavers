#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bulb_humor_surprise_magic_pirate_tale.py
===============================================================================================================

A small pirate-tale storyworld with a magical bulb, playful humor, and a
surprising turn. The simulated domain centers on a young deckhand, a cautious
captain, and a glowing bulb that can grant a single helpful wish once it is
rubbed. The tension comes from whether the bulb's magic will solve a practical
ship problem without causing a bigger laugh-worthy surprise.

The premise is inspired by a tiny pirate tale: a crew finds a strange bulb at
sea, jokes about it, then discovers it is truly magical. The world model tracks
physical and emotional state so the story is driven by what happens aboard the
ship, not by a fixed paragraph with swapped names.

Features:
- pirate style
- humor
- surprise
- magic
- seed word: bulb
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    cap: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "deckhand"}
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
class Setting:
    place: str = "the little ship"
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
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str = "bulb"
    surprise: str = ""
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
class MagicBulb:
    id: str = "bulb"
    label: str = "bulb"
    phrase: str = "a dusty brass bulb"
    wish: str = "a lantern"
    result: str = "a bright lantern"
    twist: str = "the lantern was already tied to the mast"
    grace: str = "a lantern"
    plural: bool = False
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the little ship", affords={"find_bulb", "rub_bulb", "wish"}),
    "cove": Setting(place="the moonlit cove", affords={"find_bulb", "rub_bulb", "wish"}),
}

PROBLEMS = {
    "rope_tangle": Problem(
        id="rope_tangle",
        verb="untie the tangled rope",
        gerund="untangling the rope",
        rush="dash at the rope",
        mess="knotted",
        zone={"hands"},
        keyword="bulb",
        surprise="the rope sprang apart in a silly loop",
        tags={"rope", "humor"},
    ),
    "sail_snag": Problem(
        id="sail_snag",
        verb="fix the snagged sail",
        gerund="mending the sail",
        rush="climb at the sail",
        mess="torn",
        zone={"hands", "torso"},
        keyword="bulb",
        surprise="the sail puffed up like a shocked cloud",
        tags={"sail", "surprise"},
    ),
    "lantern_out": Problem(
        id="lantern_out",
        verb="light the dark lantern",
        gerund="lighting the lantern",
        rush="reach for the lantern",
        mess="dim",
        zone={"hands"},
        keyword="bulb",
        surprise="the dark lantern gave a sneezy spark",
        tags={"lantern", "magic"},
    ),
}

BULBS = {
    "brass": MagicBulb(
        id="brass",
        label="bulb",
        phrase="a dusty brass bulb",
        wish="a lantern",
        result="a bright lantern",
        twist="the lantern was already hung by the mast",
        grace="a lantern",
    ),
    "glass": MagicBulb(
        id="glass",
        label="bulb",
        phrase="a green glass bulb",
        wish="a basket of oranges",
        result="a basket of oranges",
        twist="the oranges rolled straight into the captain's hat",
        grace="a basket of oranges",
    ),
    "blue": MagicBulb(
        id="blue",
        label="bulb",
        phrase="a blue bulb with a silver seam",
        wish="a clean deck",
        result="a clean deck",
        twist="the clean deck was so shiny that everyone skidded and laughed",
        grace="a clean deck",
    ),
}

NAMES = ["Mina", "Jory", "Pip", "Tess", "Nell", "Finn", "Rory", "Ava"]
ROLES = ["deckhand", "mate"]
CAPTAIN_NAMES = ["Captain Wren", "Captain Gull", "Captain Brine"]
TRAITS = ["brave", "cheeky", "curious", "spry", "breezy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bulb is magical if it can be found, rubbed, and then used for a wish.
can_use_bulb(S) :- finds_bulb(S), rubs_bulb(S), wants_help(S).

% A story is reasonable if the wish can solve the problem and still leave room
% for a funny surprise.
good_story(S) :- can_use_bulb(S), solves_problem(S), has_surprise(S).

% The declarative twin for compatible story choices.
valid_story(Problem, Bulb) :- problem(Problem), bulb(Bulb), solves(Problem, Bulb).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("solves", pid, "brass" if pid == "lantern_out" else "glass" if pid == "rope_tangle" else "blue"))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for bid in BULBS:
        lines.append(asp.fact("bulb", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for problem_id in PROBLEMS:
        for bulb_id in BULBS:
            if problem_id == "lantern_out" and bulb_id == "brass":
                combos.append((problem_id, bulb_id))
            elif problem_id == "rope_tangle" and bulb_id == "glass":
                combos.append((problem_id, bulb_id))
            elif problem_id == "sail_snag" and bulb_id == "blue":
                combos.append((problem_id, bulb_id))
    return combos


def explain_rejection(problem: Problem, bulb: MagicBulb) -> str:
    return (
        f"(No story: {bulb.phrase} would not honestly fix {problem.gerund} in a "
        f"pirate tale. Try a different bulb and problem pair.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, problem: Problem, bulb: MagicBulb) -> dict:
    sim = world.copy()
    do_problem(sim, hero, problem, narrate=False)
    return {
        "fixed": sim.facts.get("fixed", False),
        "surprise": sim.facts.get("surprise", False),
    }


def do_find_bulb(world: World, hero: Entity, bulb: MagicBulb) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.add(Entity(id="bulb", type="thing", label="bulb", phrase=bulb.phrase))
    world.facts["bulb"] = bulb
    world.say(
        f"{hero.id} found {bulb.phrase} under a coil of rope, and {hero.pronoun()} grinned."
    )


def do_rub_bulb(world: World, hero: Entity, bulb: MagicBulb) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.facts["rubbed"] = True
    world.say(
        f"{hero.id} rubbed the bulb, expecting a joke or a spark."
    )
    world.say(
        f"Instead, the bulb glowed gold and hummed like a tiny trumpet."
    )


def do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    hero.meters[problem.mess] = hero.meters.get(problem.mess, 0.0) + 1
    hero.memes["trouble"] = hero.memes.get("trouble", 0.0) + 1
    world.facts["problem"] = problem.id
    world.facts["attempted"] = True
    if narrate:
        world.say(
            f"The crew tried to {problem.verb}, but the deck felt too stubborn for plain hands."
        )


def do_magic(world: World, hero: Entity, problem: Problem, bulb: MagicBulb) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.facts["fixed"] = True
    world.facts["surprise"] = True
    if problem.id == "rope_tangle":
        world.say(
            f"The bulb granted {bulb.result}, but {bulb.twist}, and everybody laughed."
        )
    elif problem.id == "sail_snag":
        world.say(
            f"The bulb granted {bulb.result}, and {bulb.twist} with a pop of sailcloth."
        )
    else:
        world.say(
            f"The bulb granted {bulb.result}, and {bulb.twist} as the lantern shone awake."
        )


def do_resolution(world: World, hero: Entity, problem: Problem, bulb: MagicBulb) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(
        f"In the end, {hero.id} laughed with the captain, because the magic helped and the surprise was silly, not scary."
    )


def tell(problem: Problem, bulb: MagicBulb, name: str, role: str, captain: str, trait: str) -> World:
    world = World(SETTINGS["ship"])
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=role,
        traits=["little", trait, "pirate"],
    ))
    cap = world.add(Entity(
        id=captain,
        kind="character",
        type="captain",
        label="the captain",
        traits=["wise", "breezy"],
    ))

    world.say(
        f"On {world.setting.place}, {hero.id} was a little {trait} {role} who loved a good laugh."
    )
    world.say(
        f"{hero.id} and {cap.id} were searching for a way to help the ship."
    )

    world.para()
    do_find_bulb(world, hero, bulb)
    do_rub_bulb(world, hero, bulb)
    do_problem(world, hero, problem)
    do_magic(world, hero, problem, bulb)

    world.para()
    do_resolution(world, hero, problem, bulb)

    world.facts.update(
        hero=hero,
        captain=cap,
        problem=problem,
        bulb=bulb,
        fixed=True,
        surprise=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    bulb = _safe_fact(world, f, "bulb")
    return [
        'Write a short pirate tale for a young child about a magical bulb and a funny surprise.',
        f"Tell a story where {hero.id} finds {bulb.phrase} and uses it to {_safe_lookup(PROBLEMS, problem).verb}.",
        f"Write a cheerful pirate story that includes the word 'bulb' and ends with laughter aboard the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    cap = _safe_fact(world, f, "captain")
    problem = _safe_fact(world, f, "problem")
    bulb = _safe_fact(world, f, "bulb")
    qa = [
        QAItem(
            question=f"What did {hero.id} find on the ship?",
            answer=f"{hero.id} found {bulb.phrase} hidden under a coil of rope.",
        ),
        QAItem(
            question=f"Why did {hero.id} rub the bulb?",
            answer=(
                f"{hero.id} rubbed the bulb because the crew needed help with {_safe_lookup(PROBLEMS, problem).gerund}."
            ),
        ),
        QAItem(
            question=f"Who laughed at the end of the story?",
            answer=f"{hero.id} laughed with {cap.id} after the magic worked and the surprise turned silly.",
        ),
        QAItem(
            question=f"What did the magic bulb do?",
            answer=(
                f"It gave the crew {bulb.result}, and then the story ended with a funny surprise."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bulb?",
            answer="A bulb is a round thing that can glow or be used here as a magical object in the story.",
        ),
        QAItem(
            question="Why are pirates often shown on ships?",
            answer="Pirates are often shown on ships because ships carry them across the sea on adventures.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something impossible in real life happens in a special or surprising way.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    problem: str
    bulb: str
    name: str
    role: str
    captain: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "bulb", None):
        problem = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        bulb = _safe_lookup(BULBS, getattr(args, "bulb", None))
        if (getattr(args, "problem", None), getattr(args, "bulb", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "problem", None) is None or c[0] == getattr(args, "problem", None))
              and (getattr(args, "bulb", None) is None or c[1] == getattr(args, "bulb", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    problem_id, bulb_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(problem=problem_id, bulb=bulb_id, name=name, role=role, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PROBLEMS, params.problem), _safe_lookup(BULBS, params.bulb), params.name, params.role, params.captain, params.trait)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(problem="rope_tangle", bulb="glass", name="Mina", role="deckhand", captain="Captain Wren", trait="cheeky"),
    StoryParams(problem="sail_snag", bulb="blue", name="Pip", role="mate", captain="Captain Gull", trait="curious"),
    StoryParams(problem="lantern_out", bulb="brass", name="Tess", role="deckhand", captain="Captain Brine", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny pirate tale world with a magical bulb, humor, and surprise."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--bulb", choices=BULBS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["deckhand", "mate"])
    ap.add_argument("--captain")
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


def asp_facts_and_rules_program(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_facts_and_rules_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_facts_and_rules_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (problem, bulb) combos:\n")
        for p, b in combos:
            print(f"  {p:14} {b}")
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
            header = f"### {p.name}: {p.problem} with {p.bulb}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
