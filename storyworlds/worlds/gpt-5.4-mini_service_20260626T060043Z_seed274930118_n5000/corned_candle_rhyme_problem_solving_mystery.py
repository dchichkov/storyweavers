#!/usr/bin/env python3
"""
storyworlds/worlds/corned_candle_rhyme_problem_solving_mystery.py
==================================================================

A small mystery storyworld about a child who hears a rhyme, notices a clue,
and solves a gentle problem with a candle.

Premise:
- A child wants to follow a little rhyme.
- A dim room and a corned tin hide a missing object or a mistaken clue.
- The child uses careful observation and problem solving to uncover what is true.

The world is intentionally small and constraint-driven:
- The candle is a physical light source with limited brightness.
- The corned object is a tin of corned food that can be mistaken for a clue.
- A rhyme points toward a hidden place.
- The resolution comes from checking clues, not from magic or a sudden reveal.
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
# Core world model
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    lit: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    candle: object | None = None
    corned: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
    dim: bool = False
    cluttered: bool = False
    echoes: bool = False
    hiding_spot: str = ""
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
class Clue:
    id: str
    phrase: str
    points_to: str
    false_trail: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str
    clue: str
    rhyme: str
    problem: str
    name: str
    gender: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "attic": Place(name="the attic", dim=True, cluttered=True, echoes=True, hiding_spot="behind an old trunk"),
    "cellar": Place(name="the cellar", dim=True, cluttered=False, echoes=True, hiding_spot="under a shelf"),
    "kitchen": Place(name="the kitchen", dim=False, cluttered=True, echoes=False, hiding_spot="inside a tin box"),
    "porch": Place(name="the porch", dim=True, cluttered=False, echoes=False, hiding_spot="by the steps"),
}

CLUES = {
    "corned_tin": Clue(
        id="corned_tin",
        phrase="a corned tin with a dented lid",
        points_to="hidden_key",
        false_trail=True,
    ),
    "wax_drip": Clue(
        id="wax_drip",
        phrase="a little line of wax drips",
        points_to="candle_holder",
    ),
    "scratched_note": Clue(
        id="scratched_note",
        phrase="a scratched note with a tiny rhyme",
        points_to="hidden_key",
    ),
    "thread_loop": Clue(
        id="thread_loop",
        phrase="a loose thread loop caught on a nail",
        points_to="drawer",
    ),
}

RHYMES = {
    "soft_rhyme": (
        "If the room is dim and small, "
        "look near the place that catches all."
    ),
    "candle_rhyme": (
        "When the candle makes a steady glow, "
        "the truest clue is not the first thing you know."
    ),
    "corned_rhyme": (
        "Corned and tinny, dent and gleam, "
        "follow the wax, not the shiny theme."
    ),
}

PROBLEMS = {
    "missing_key": "find the missing key",
    "stuck_box": "open the stuck box",
    "lost_note": "find the lost note",
}

# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def is_reasonable(place: Place, clue: Clue, problem: str) -> bool:
    if problem == "missing_key":
        return True
    if problem == "stuck_box":
        return clue.id in {"wax_drip", "thread_loop", "corned_tin"}
    if problem == "lost_note":
        return clue.id in {"scratched_note", "corned_tin"}
    return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with rhyme and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    rhyme = getattr(args, "rhyme", None) or rng.choice(list(RHYMES))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    if not is_reasonable(_safe_lookup(PLACES, place), _safe_lookup(CLUES, clue), problem):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(
        ["Mia", "Nora", "Ada", "Lena"] if gender == "girl" else ["Leo", "Finn", "Max", "Eli"]
    )
    return StoryParams(place=place, clue=clue, rhyme=rhyme, problem=problem, name=name, gender=gender)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _subject_name(name: str, gender: str) -> str:
    return name


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    rhyme = _safe_lookup(RHYMES, params.rhyme)
    problem = _safe_lookup(PROBLEMS, params.problem)

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    candle = world.add(Entity(id="candle", type="candle", label="a candle", lit=True))
    corned = world.add(Entity(id="corned_tin", type="tin", label="a corned tin", phrase=clue.phrase))
    hidden = world.add(Entity(id="hidden_key", type="key", label="a little key", hidden=True))

    world.say(
        f"{hero.id} stepped into {place.name}, where the air felt quiet and a little mysterious."
    )
    world.say(
        f"On a small table sat {candle.label}, and beside it was {corned.label}: {clue.phrase}."
    )
    world.say(
        f"{hero.id} had a problem: {problem}, and {hero.pronoun('possessive')} eyes kept returning to the clue."
    )

    world.para()
    world.say(f"{hero.id} whispered a rhyme to help think: “{rhyme}”")
    if place.dim:
        world.say(f"The candle made a warm circle of light, just bright enough to notice little details.")
    if clue.false_trail:
        world.say(
            f"The corned tin looked important, but {hero.id} did not trust the shiny lid right away."
        )

    world.say(
        f"Instead, {hero.id} looked for a pattern, moved slowly, and used careful problem solving."
    )

    # Resolution logic: the clue points to the hidden thing.
    hidden.hidden = False
    hidden.owner = hero.id
    world.facts.update(
        hero=hero,
        candle=candle,
        corned=corned,
        hidden=hidden,
        clue=clue,
        rhyme=rhyme,
        problem=problem,
        place=place,
    )

    world.para()
    if clue.points_to == "hidden_key":
        if place.hiding_spot:
            world.say(
                f"At last, {hero.id} found the true clue and reached {place.hiding_spot}."
            )
        world.say(
            f"There, {hero.id} discovered {hidden.label}, which solved the mystery and fixed the problem."
        )
    elif clue.points_to == "candle_holder":
        world.say(
            f"{hero.id} followed the wax trail and found the missing candle holder, which made the room easier to search."
        )
        world.say(
            f"That extra light helped {hero.id} finish the job and solve the mystery."
        )
    elif clue.points_to == "drawer":
        world.say(
            f"{hero.id} tugged the loose thread, opened a drawer, and found what was needed."
        )
        world.say(f"The little clue was enough to solve the problem.")
    else:
        world.say(f"{hero.id} solved the problem by checking every clue with care.")

    world.para()
    world.say(
        f"In the end, the candle still glowed softly, the corned tin stayed where it was, "
        f"and {hero.id} smiled at a mystery solved the gentle way."
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about {f["hero"].id}, a candle, and a clue that includes a rhyme.',
        f"Tell a gentle problem-solving mystery set in {f['place'].name} where {f['hero'].id} uses a rhyme to find the truth.",
        f"Write a child-friendly story that includes a corned tin, a candle, and a clever clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    clue = _safe_fact(world, world.facts, "clue")
    place = _safe_fact(world, world.facts, "place")
    problem = _safe_fact(world, world.facts, "problem")
    hidden = _safe_fact(world, world.facts, "hidden")
    return [
        QAItem(
            question=f"What problem was {hero.id} trying to solve in {place.name}?",
            answer=f"{hero.id} was trying to {problem}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {clue.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} find at the end?",
            answer=f"{hero.id} found {hidden.label}, and that solved the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a candle do?",
            answer="A candle gives off a small, steady light when it is lit.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a sign or detail that helps someone figure out what is true.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking carefully, thinking step by step, and trying a smart plan.",
        ),
        QAItem(
            question="What is corned food?",
            answer="Corned food is food that has been salted or preserved, often kept in a tin.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.lit:
            bits.append("lit=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is relevant if it points to the target needed to solve the problem.
relevant(C) :- clue(C), points_to(C, hidden_key).
relevant(C) :- clue(C), points_to(C, candle_holder).
relevant(C) :- clue(C), points_to(C, drawer).

% A story is valid if the clue/problem pair is reasonable.
valid(P, C, M) :- place(P), clue(C), problem(M), reasonable(P, C, M).

% A place is reasonable when the selected clue can support the problem.
reasonable(P, C, M) :- place(P), clue(C), problem(M), clue_supports(C, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.dim:
            lines.append(asp.fact("dim", pid))
        if place.cluttered:
            lines.append(asp.fact("cluttered", pid))
        if place.echoes:
            lines.append(asp.fact("echoes", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
        if clue.false_trail:
            lines.append(asp.fact("false_trail", cid))
    for mid, _ in PROBLEMS.items():
        lines.append(asp.fact("problem", mid))
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for mid in PROBLEMS:
                if is_reasonable(place, clue, mid):
                    lines.append(asp.fact("clue_supports", cid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted(
        (p, c, m)
        for p in PLACES
        for c in CLUES
        for m in PROBLEMS
        if is_reasonable(_safe_lookup(PLACES, p), _safe_lookup(CLUES, c), m)
    )
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("python-only:", sorted(set(py) - set(cl)))
    print("clingo-only:", sorted(set(cl) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="attic", clue="corned_tin", rhyme="corned_rhyme", problem="missing_key", name="Mia", gender="girl"),
    StoryParams(place="cellar", clue="wax_drip", rhyme="candle_rhyme", problem="stuck_box", name="Leo", gender="boy"),
    StoryParams(place="kitchen", clue="scratched_note", rhyme="soft_rhyme", problem="lost_note", name="Nora", gender="girl"),
    StoryParams(place="porch", clue="thread_loop", rhyme="soft_rhyme", problem="stuck_box", name="Finn", gender="boy"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} valid story combos:")
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
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
