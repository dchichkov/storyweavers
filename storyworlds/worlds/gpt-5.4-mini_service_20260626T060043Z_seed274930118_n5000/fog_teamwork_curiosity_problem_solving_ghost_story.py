#!/usr/bin/env python3
"""
storyworlds/worlds/fog_teamwork_curiosity_problem_solving_ghost_story.py
========================================================================

A small storyworld for a gentle ghost story in fog, with teamwork,
curiosity, and problem solving as the engine of the plot.

Premise:
- A child and a helper friend hear a soft mystery in the fog.
- Curiosity leads them toward the sound.
- Fog makes the path confusing and a little spooky.
- Teamwork and problem solving help them discover the "ghost" is only a shy
  kite, lantern, or sheet caught in the mist.
- The ending proves the change by showing the group safe, relieved, and proud
  of their good thinking.

This script is standalone and deterministic given its parameters.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
class Character:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    indoors: bool = False
    foggy: bool = True
    mystery: str = "soft whisper"
    affordances: set[str] = field(default_factory=set)
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
class ObjectItem:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    thing: object | None = None
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
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    safe_explanation: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Place(name="the foggy harbor", indoors=False, foggy=True, mystery="faint bell", affordances={"listen", "search", "signal"}),
    "garden": Place(name="the misty garden", indoors=False, foggy=True, mystery="rustling leaves", affordances={"listen", "search", "signal"}),
    "hill": Place(name="the misty hill path", indoors=False, foggy=True, mystery="soft tapping", affordances={"listen", "search", "signal"}),
    "attic": Place(name="the old attic", indoors=True, foggy=False, mystery="creaky floorboard", affordances={"listen", "search", "signal"}),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ivy", "Finn", "Zoe", "Theo"]
HELPER_NAMES = ["Ada", "Ben", "Milo", "June", "Nora", "Pip", "Rae", "Sam"]

CLUES = {
    "sheet": Clue(
        id="sheet",
        label="a white sheet",
        phrase="a white sheet",
        reveal="caught on a branch",
        safe_explanation="it was only fluttering in the fog",
        tags={"ghost", "fog", "curiosity", "problem_solving"},
    ),
    "kite": Clue(
        id="kite",
        label="a kite",
        phrase="a little kite with a loose tail",
        reveal="tangled in a tree",
        safe_explanation="the wind had lifted it up like a ghost",
        tags={"ghost", "fog", "teamwork"},
    ),
    "lantern": Clue(
        id="lantern",
        label="a lantern",
        phrase="a lantern with a dim little light",
        reveal="swaying on a rope",
        safe_explanation="its glow had made the fog look spooky",
        tags={"ghost", "fog", "problem_solving"},
    ),
}

TOOLS = {
    "rope": {"label": "a rope", "use": "tie the branch back", "help": "hold the clue steady", "covers": {"hands"}},
    "stick": {"label": "a long stick", "use": "lift the sheet down", "help": "reach the clue", "covers": {"hands"}},
    "lamp": {"label": "a lamp", "use": "shine a clearer path", "help": "show the way through the fog", "covers": {"hands"}},
    "whistle": {"label": "a whistle", "use": "call for help", "help": "signal their friend", "covers": {"mouth"}},
}

TRAITS = ["curious", "brave", "patient", "gentle", "thoughtful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    child_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A story is reasonable if the place is foggy and the clue can be mistaken for
% a ghost in that place.
ghost_story(P, C) :- place(P), clue(C), foggy(P), spooky(C).

% Teamwork is required when a helper tool can be used to resolve the mystery.
has_tool(T) :- tool(T).
can_solve(C) :- clue(C), has_tool(_).

valid_story(P, C) :- ghost_story(P, C), can_solve(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.foggy:
            lines.append(asp.fact("foggy", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("spooky", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, t))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A foggy ghost story about teamwork, curiosity, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if clue not in CLUES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, clue=clue, child_name=name, helper_name=helper, trait=trait)

def story_text(world: World) -> str:
    return world.render()

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for young children set in {_safe_fact(world, f, "place_name")} with fog.',
        f"Tell a short story where {_safe_fact(world, f, "child_name")} and {_safe_fact(world, f, "helper_name")} use teamwork to solve a spooky mystery.",
        f'Write a child-friendly story with curiosity, problem solving, and a mysterious "ghost" that turns out safe.',
    ]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    world = World(place)

    child = world.add(Character(
        id=params.child_name, type="child", label=params.child_name, role="curious child",
        meters={"fear": 0.0, "hope": 0.0, "fog": 0.0}, memes={"curiosity": 0.0, "courage": 0.0, "teamwork": 0.0, "problem_solving": 0.0}
    ))
    helper = world.add(Character(
        id=params.helper_name, type="child", label=params.helper_name, role="helpful friend",
        meters={"fear": 0.0, "hope": 0.0, "fog": 0.0}, memes={"curiosity": 0.0, "courage": 0.0, "teamwork": 0.0, "problem_solving": 0.0}
    ))
    thing = world.add(ObjectItem(
        id=clue.id, type="mystery", label=clue.label, phrase=clue.phrase,
        meters={"hidden": 1.0}, memes={"mystery": 1.0}
    ))

    # Act 1
    world.say(f"One foggy evening, {child.id} and {helper.id} stood in {place.name}.")
    world.say(f"The air was thick with fog, and the only clue was {place.mystery}.")
    world.say(f"{child.id} felt curious, because {child.pronoun('subject')} wanted to know what was making the strange sound.")
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.facts.update(place_name=place.name, child_name=child.id, helper_name=helper.id, clue=clue, tool=None, solved=False)

    world.para()

    # Act 2
    world.say(f"{helper.id} listened too, and together they followed the faint sound through the fog.")
    world.say(f"The mist made the path hard to see, so they had to stay close and use teamwork.")
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    child.meters["fog"] += 1
    helper.meters["fog"] += 1
    world.say(f"At last they found {clue.phrase} {clue.reveal}.")
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say(f"It looked like a ghost at first, but {child.id} took a careful breath and kept thinking.")

    world.para()

    # Act 3
    tool_key = "lamp" if params.place != "attic" else "stick"
    tool = _safe_lookup(TOOLS, tool_key)
    world.facts["tool"] = tool_key
    child.memes["problem_solving"] += 1
    helper.memes["problem_solving"] += 1
    world.say(f"{helper.id} held {tool['label']}, and {child.id} used it to {tool['help']}.")
    world.say(f"With their problem solving, they saw the truth: it was only {clue.safe_explanation}.")
    world.say(f"They fixed the little mystery safely, and the spooky feeling melted away.")
    world.say(f"{child.id} and {helper.id} smiled in the fog, proud that they had found the answer together.")
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    child.meters["hope"] += 1
    helper.meters["hope"] += 1
    world.facts["solved"] = True
    world.facts["tool"] = tool_key
    world.facts["clue_label"] = clue.label
    return world


def generation_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What kind of story is this one?",
            answer=f"It is a gentle ghost story set in {_safe_fact(world, f, "place_name")} with fog, curiosity, teamwork, and problem solving."
        ),
        QAItem(
            question=f"Why did {_safe_fact(world, f, "child_name")} and {_safe_fact(world, f, "helper_name")} stay close in the mist?",
            answer=f"They stayed close because the fog made the path hard to see, so teamwork helped them search safely."
        ),
        QAItem(
            question=f"What did the strange thing turn out to be?",
            answer=f"It turned out to be {_safe_fact(world, f, "clue").phrase}, which only looked spooky in the fog."
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They used {(f.get('tool') or next(iter(TOOLS.values())))} and careful thinking, so they could see what the clue really was and calm the spooky feeling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops near the ground that makes the world look blurry."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do something together."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions and find out how things work."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking step by step to figure out a good answer."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=generation_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CLUES if _safe_lookup(SETTINGS, p).foggy]


def asp_verify() -> int:
    try:
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_stories())
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1
    if python_set == clingo_set:
        print(f"OK: ASP matches Python for {len(python_set)} combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(python_set - clingo_set))
    print(" only in asp:", sorted(clingo_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in SETTINGS.items():
        if not p.foggy:
            continue
        for clue in CLUES:
            combos.append((place, clue))
    return combos


CURATED = [
    StoryParams(place="harbor", clue="sheet", child_name="Mia", helper_name="Ada", trait="curious"),
    StoryParams(place="garden", clue="kite", child_name="Noah", helper_name="June", trait="thoughtful"),
    StoryParams(place="hill", clue="lantern", child_name="Luna", helper_name="Pip", trait="brave"),
    StoryParams(place="attic", clue="sheet", child_name="Eli", helper_name="Rae", trait="patient"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if clue not in CLUES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        clue=clue,
        child_name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        rows = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(rows)} compatible stories:")
        for row in rows:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
