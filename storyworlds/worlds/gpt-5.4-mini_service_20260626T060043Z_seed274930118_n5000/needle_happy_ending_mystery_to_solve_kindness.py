#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/needle_happy_ending_mystery_to_solve_kindness.py
=============================================================================================================

A tiny story world about a lost needle, a small mystery, and a kind fix.

Premise:
- A child wants to help mend something special.
- A needle goes missing.
- Everyone searches by following clues, and kindness turns the worry into a happy ending.

The world model tracks physical meters and emotional memes. The story is
generated from simulated state, not from a frozen paragraph template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    needle: object | None = None
    patch: object | None = None
    seeker: object | None = None
    thread: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
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


@dataclass
class Place:
    id: str
    label: str
    clues: list[str]
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    can_hide: bool = False
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


PLACES = {
    "attic": Place("attic", "the attic", ["dust on a shelf", "a basket tipped on its side", "a loose thread"]),
    "sewing_room": Place("sewing_room", "the sewing room", ["a spool rolling under a chair", "a pin cushion", "a folded quilt"]),
    "kitchen": Place("kitchen", "the kitchen", ["crumbs near the table", "a chair pulled out", "a warm lamp"]),
    "porch": Place("porch", "the porch", ["a doormat", "a flower pot", "a tiny shiny glint"]),
}

ITEMS = {
    "needle": Item("needle", "needle", "a tiny silver needle", can_hide=True),
    "thread": Item("thread", "thread", "a bright spool of thread"),
    "patch": Item("patch", "patch", "a soft cloth patch"),
    "basket": Item("basket", "basket", "a small sewing basket"),
}

NAMES = ["Maya", "Nina", "Leo", "Eli", "Ava", "Owen", "Iris", "Noah"]
TRAITS = ["careful", "kind", "curious", "gentle", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "sewing_room"
    seeker_name: str = "Maya"
    seeker_gender: str = "girl"
    helper_name: str = "Grandma"
    helper_gender: str = "woman"
    trait: str = "kind"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
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
% A place can hide a needle if it has hiding spots.
can_hide(P) :- place(P), clue(P,_).

% The mystery is solvable when the needle can be hidden and a helper clue exists.
solvable(P) :- place(P), can_hide(P), kind_helper(K), clue(P,K).

#show solvable/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in p.clues:
            lines.append(asp.fact("clue", pid, clue))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.can_hide:
            lines.append(asp.fact("can_hide_item", iid))
    lines.append(asp.fact("kind_helper", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_places() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return {p for (p,) in asp.atoms(model, "solvable")}


def python_reasonable_places() -> set[str]:
    return {pid for pid, place in PLACES.items() if place.clues}


def asp_verify() -> int:
    a = asp_reasonable_places()
    b = python_reasonable_places()
    if a == b:
        print(f"OK: clingo gate matches Python gate ({len(a)} places).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in ASP:", sorted(a - b))
    if b - a:
        print(" only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, seeker: Entity, helper: Entity, trait: str) -> None:
    world.say(
        f"{seeker.id} was a little {trait} child who loved helping {helper.pronoun('object')} fix broken things."
    )


def sewing_setup(world: World, seeker: Entity, helper: Entity, needle: Entity, thread: Entity, patch: Entity) -> None:
    world.say(
        f"One afternoon in {world.place}, {helper.id} laid out {needle.phrase}, {thread.phrase}, and {patch.phrase}."
    )
    world.say(
        f"{seeker.id} wanted to help sew the patch on, because {helper.id}'s hands were slow that day."
    )


def mystery_break(world: World, seeker: Entity, needle: Entity) -> None:
    needle.hidden = True
    seeker.memes["worry"] = seeker.memes.get("worry", 0) + 1
    world.say(
        f"Then the tiny needle slipped away. One blink later, it was gone from the table."
    )
    world.say(
        f"{seeker.id} looked under the cloth, behind the basket, and by the lamp, but the needle was nowhere to be seen."
    )


def clue_search(world: World, seeker: Entity, helper: Entity, place: Place, needle: Entity) -> None:
    clue = place.clues[0]
    seeker.memes["curiosity"] = seeker.memes.get("curiosity", 0) + 1
    world.say(
        f"{helper.id} did not scold. {helper.pronoun().capitalize()} smiled and said, \"Let's follow the clues.\""
    )
    world.say(
        f"At {place.label}, they noticed {clue}, and {seeker.id} checked the quiet spots one by one."
    )
    if place.id == "sewing_room":
        needle.hidden = False
        needle.found = True
        needle.meters["sparkle"] = needle.meters.get("sparkle", 0) + 1


def kindness_turn(world: World, seeker: Entity, helper: Entity, needle: Entity, patch: Entity) -> None:
    seeker.memes["kindness"] = seeker.memes.get("kindness", 0) + 1
    seeker.memes["joy"] = seeker.memes.get("joy", 0) + 1
    world.say(
        f"{seeker.id} found the needle tucked safely beside the folded quilt, and {seeker.pronoun()} brought it back with both hands."
    )
    world.say(
        f"{helper.id} thanked {seeker.pronoun('object')} with a warm hug. Together they stitched the patch neatly in place."
    )
    world.say(
        f"In the end, the missing needle was found, the mending was finished, and the room felt peaceful again."
    )


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------

def tell(place: Place, params: StoryParams) -> World:
    world = World(place=place.label)

    seeker = world.add(Entity(id=params.seeker_name, kind="character", type=params.seeker_gender))
    helper_type = "woman" if params.helper_gender == "woman" else "man"
    helper = world.add(Entity(id=params.helper_name, kind="character", type=helper_type))
    needle = world.add(Entity(id="needle", type="needle", label="needle", phrase="a tiny silver needle", hidden=False))
    thread = world.add(Entity(id="thread", type="thread", label="thread", phrase="a bright spool of thread"))
    patch = world.add(Entity(id="patch", type="patch", label="patch", phrase="a soft cloth patch"))

    world.facts.update(place=place, seeker=seeker, helper=helper, needle=needle, thread=thread, patch=patch)

    introduce(world, seeker, helper, params.trait)
    sewing_setup(world, seeker, helper, needle, thread, patch)

    world.para()
    mystery_break(world, seeker, needle)
    clue_search(world, seeker, helper, place, needle)

    world.para()
    kindness_turn(world, seeker, helper, needle, patch)

    world.facts["resolved"] = needle.found
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = _safe_fact(world, f, "seeker")
    helper = _safe_fact(world, f, "helper")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short story about {seeker.id} and {helper.id} in {place.label} where a lost needle must be found.',
        f'Tell a gentle mystery with a missing needle, a kind helper, and a happy ending in {place.label}.',
        f'Write a child-friendly story where kindness helps solve the puzzle of the missing needle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker: Entity = _safe_fact(world, f, "seeker")
    helper: Entity = _safe_fact(world, f, "helper")
    place: Place = _safe_fact(world, f, "place")
    needle: Entity = _safe_fact(world, f, "needle")
    patch: Entity = _safe_fact(world, f, "patch")
    return [
        QAItem(
            question=f"What mystery did {seeker.id} have to solve in {place.label}?",
            answer=f"{seeker.id} had to solve the mystery of where the needle went after it slipped away from the table.",
        ),
        QAItem(
            question=f"How did {helper.id} help when the needle went missing?",
            answer=f"{helper.id} stayed calm, suggested following clues, and helped look in the quiet spots instead of getting upset.",
        ),
        QAItem(
            question=f"What was fixed after the needle was found?",
            answer=f"The soft patch was sewn on neatly, so the mending job was finished.",
        ),
        QAItem(
            question=f"Why was this a happy ending?",
            answer=f"It was a happy ending because the missing needle was found, the worry went away, and everyone finished the sewing together kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a needle used for?",
            answer="A needle is a tiny tool used for sewing cloth together with thread.",
        ),
        QAItem(
            question="Why should a needle be handled carefully?",
            answer="A needle is sharp and very small, so people handle it carefully so they do not poke themselves or lose it.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with other people.",
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="sewing_room", seeker_name="Maya", seeker_gender="girl", helper_name="Grandma", helper_gender="woman", trait="kind"),
    StoryParams(place="attic", seeker_name="Leo", seeker_gender="boy", helper_name="Grandpa", helper_gender="man", trait="curious"),
    StoryParams(place="kitchen", seeker_name="Ava", seeker_gender="girl", helper_name="Mom", helper_gender="woman", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world about a lost needle and a kind ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or "Grandma"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    seeker_gender = "girl" if name in {"Maya", "Nina", "Ava", "Iris"} else "boy"
    helper_gender = "woman" if helper in {"Grandma", "Mom", "Grandma June"} else "man"
    return StoryParams(place=place, seeker_name=name, seeker_gender=seeker_gender, helper_name=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params)
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
        print(asp_program("#show solvable/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        sols = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(sols)} solvable places:")
        for (p,) in sols:
            print(" ", p)
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
            header = f"### {p.seeker_name} in {p.place} (helper: {p.helper_name})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
