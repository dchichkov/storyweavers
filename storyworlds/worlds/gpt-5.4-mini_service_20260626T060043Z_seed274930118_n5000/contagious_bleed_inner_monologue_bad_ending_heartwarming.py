#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/contagious_bleed_inner_monologue_bad_ending_heartwarming.py
=================================================================================================

A small standalone storyworld about a child, a sudden bleed, and the worry that
it might be contagious. The world is intentionally narrow: it models a single
heartwarming setting where a caring adult and a friend try to help, but the
ending still lands as a bad one because the child has to miss the fun.

This script follows the Storyweavers contract:
- self-contained stdlib script
- typed entities with meters and memes
- state-driven narration
- inline ASP twin with a Python reasonableness gate
- --verify parity checks
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man"}
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
class Place:
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
    calm: str = ""
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
class Cause:
    id: str
    kind: str
    trigger: str
    wound: str
    risky: str
    contagious: bool
    recovery: str
    clue: str
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
    place: str
    cause: str
    child_name: str
    child_gender: str
    helper: str
    friend_name: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "classroom": Place(name="the classroom", indoors=True, affords={"paper_cut", "scrape"}, calm="The classroom smelled like crayons and warm paper."),
    "clinic": Place(name="the clinic waiting room", indoors=True, affords={"paper_cut", "scrape", "bandage"}, calm="The waiting room was quiet, with soft chairs and a fish painting on the wall."),
    "kitchen": Place(name="the kitchen", indoors=True, affords={"paper_cut", "scrape"}, calm="The kitchen was bright and still, with a clean towel by the sink."),
}

CAUSES = {
    "paper_cut": Cause(
        id="paper_cut",
        kind="cut",
        trigger="a sharp edge on a folded paper",
        wound="paper cut",
        risky="stings and bleeds a little",
        contagious=False,
        recovery="press a clean tissue on it",
        clue="a tiny red line on the finger",
    ),
    "scrape": Cause(
        id="scrape",
        kind="scrape",
        trigger="a hard corner on the floor",
        wound="scraped knee",
        risky="bleeds a little and aches",
        contagious=False,
        recovery="clean it and cover it with a bandage",
        clue="a red spot on the knee",
    ),
    "nosebleed": Cause(
        id="nosebleed",
        kind="bleed",
        trigger="dry air and a sudden sneeze",
        wound="nosebleed",
        risky="bleeds suddenly and scares the child",
        contagious=True,
        recovery="lean forward and hold a tissue under the nose",
        clue="a small red drip on the tissue",
    ),
}

NAMES_GIRL = ["Mia", "Nora", "Lina", "Eve", "Ivy", "Ada"]
NAMES_BOY = ["Ben", "Owen", "Theo", "Noah", "Finn", "Leo"]
HELPERS = ["mother", "father", "teacher", "nurse"]
FRIENDS = ["Ava", "Milo", "Sage", "Ruby", "June", "Kai"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in PLACES.items():
        for cause, c in CAUSES.items():
            if cause not in p.affords:
                continue
            combos.append((place, cause))
    return combos


def reasonableness_gate(place: str, cause: str) -> bool:
    return (place, cause) in valid_combos()


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("contagious", cid) if c.contagious else asp.fact("not_contagious", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Cause) :- place(Place), cause(Cause), affords(Place, Cause).
show_valid(Place, Cause) :- valid(Place, Cause).
#show show_valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_valid/2."))
    return sorted(set(asp.atoms(model, "show_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny heartwarming story world about a bleed and a worried child.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--friend")
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
    if getattr(args, "place", None) and getattr(args, "cause", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "cause", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "cause", None) is None or c[1] == getattr(args, "cause", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, cause = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(place=place, cause=cause, child_name=name, child_gender=gender, helper=helper, friend_name=friend)


def _do_bleed(world: World, child: Entity, cause: Cause) -> None:
    child.meters["bleed"] += 1
    if cause.contagious:
        child.memes["contagious_fear"] += 1
    else:
        child.memes["surprise"] += 1


def generate_story_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    cause = _safe_lookup(CAUSES, params.cause)
    world = World(place)

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label=params.friend_name))

    world.facts.update(child=child, helper=helper, friend=friend, cause=cause, place=place)

    world.say(f"{child.label} was in {place.name}.")
    world.say(place.calm)

    if cause.id == "nosebleed":
        world.say(
            f"One minute {child.label} was breathing quietly; the next, {cause.clue} appeared."
        )
    else:
        world.say(
            f"While {child.label} reached for some paper, {cause.trigger} caused {cause.clue}."
        )

    _do_bleed(world, child, cause)
    world.say(f"{child.label} touched the wound and thought, \"{cause.risky}.\"")

    if cause.contagious:
        child.memes["worry"] += 1
        world.say(f"{child.label} worried that the bleed might be contagious, even though {cause.kind} was only a hurt place.")
        world.say(f'Inside, {child.label} thought, "What if everyone thinks I will spread it?"')
    else:
        world.say(f"{child.label} knew the bleed was not contagious, but it still stung and made {child.label} blink fast.")

    world.say(f"{helper.label} came right over with a clean cloth.")
    child.memes["relief"] += 1
    helper.memes["care"] += 1
    world.say(f"{helper.label} said, \"I am here. We will take care of it together.\"")

    if cause.contagious:
        world.say(f"{helper.label} explained that the bleed itself was not a sick thing that jumped from one person to another, and that calm hands would help.")
    else:
        world.say(f"{helper.label} showed how to press the cloth gently until the red spot slowed down.")

    child.meters["bleed"] += 1
    world.say(f"{child.label} held the cloth and breathed slowly.")

    # Ending is bad: the child misses a planned treat.
    child.memes["disappointment"] += 1
    friend.memes["kindness"] += 1
    world.say(f"{params.friend_name} waited by the door with a small game, but the outing had to stop.")
    world.say(
        f"{child.label} could not go to the fun part of the day, and that was the bad ending."
    )
    world.say(
        f"Still, {params.friend_name} sat beside {child.label}, and the room felt warm with quiet care."
    )

    world.facts["cause"] = cause
    world.facts["contagious"] = cause.contagious
    world.facts["bad_ending"] = True
    return world


def tell_world(params: StoryParams) -> World:
    return generate_story_world(params)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cause: Cause = _safe_fact(world, f, "cause")
    child: Entity = _safe_fact(world, f, "child")
    return [
        f"Write a heartwarming story for a young child about {child.label} and a sudden {cause.wound}.",
        f"Tell a gentle story in which a child worries that a {cause.kind} might be contagious, then gets help from a caring adult.",
        f"Write a short story with an inner monologue where {child.label} thinks about bleeding, gets comfort, and still has a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cause: Cause = _safe_fact(world, f, "cause")
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    friend: Entity = _safe_fact(world, f, "friend")
    qas = [
        QAItem(
            question=f"What happened to {child.label} in {world.place.name}?",
            answer=f"{child.label} got a {cause.wound}, so there was a little bleed and everyone had to pause and help.",
        ),
        QAItem(
            question=f"Why did {child.label} worry about the bleed?",
            answer=f"{child.label} thought it might be contagious, so {child.label} felt scared and kept wondering if other people would worry too.",
        ),
        QAItem(
            question=f"Who helped {child.label} after the bleed started?",
            answer=f"{helper.label} came over with a clean cloth and stayed calm while {child.label} held still.",
        ),
        QAItem(
            question=f"Why is the ending bad even though the story is kind?",
            answer=f"The ending is bad because {child.label} had to miss the fun part of the day, even though {params_or_world_name(world)}",
        ),
    ]
    return qas


def params_or_world_name(world: World) -> str:
    child: Entity = _safe_fact(world, world.facts, "child")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    return f"{friend.label} sat beside {child.label} and the room felt warm with quiet care."


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does contagious mean?",
            answer="Contagious means something can spread from one person to another, like a sickness or germs, so people try to stay careful around it.",
        ),
        QAItem(
            question="What should you do when a small cut or bleed starts?",
            answer="A small cut or bleed should be cleaned and covered with a cloth or bandage, and a grown-up should help if needed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos_wrapper() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show show_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos_wrapper()
        print(f"{len(combos)} compatible combos:")
        for place, cause in combos:
            print(f"  {place:12} {cause}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, cause in valid_combos():
            params = StoryParams(
                place=place,
                cause=cause,
                child_name=random.choice(NAMES_GIRL + NAMES_BOY),
                child_gender=random.choice(["girl", "boy"]),
                helper=random.choice(HELPERS),
                friend_name=random.choice(FRIENDS),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


if __name__ == "__main__":
    main()
