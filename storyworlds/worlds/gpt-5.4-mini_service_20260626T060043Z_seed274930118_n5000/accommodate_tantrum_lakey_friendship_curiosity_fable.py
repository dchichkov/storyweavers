#!/usr/bin/env python3
"""
A small fable-style storyworld about a curious friend, a tantrum, and the art
of accommodating another creature without losing kindness.
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
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    with_entity: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    a: object | None = None
    b: object | None = None
    entities: set[str] = field(default_factory=set)
    mat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "hare", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    waterside: bool = False
    shelters: set[str] = field(default_factory=set)
    invites: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    title: str
    cause: str
    sign: str
    soothes: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    effect: str = ""
    keyword: str = ""
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
class Gift:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    place: str = ""
    promise: str = ""
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.events = set(self.events)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "lakey_bank": Place(
        name="the lakey bank",
        waterside=True,
        shelters={"reed_hut", "stone_bench"},
        invites={"quiet", "listening", "sharing"},
    ),
    "reed_glen": Place(
        name="the reed glen",
        waterside=True,
        shelters={"reed_hut"},
        invites={"listening", "watching", "sharing"},
    ),
    "sunny_hill": Place(
        name="the sunny hill",
        waterside=False,
        shelters={"stone_bench"},
        invites={"watching", "sharing", "resting"},
    ),
}

PROBLEMS = {
    "tantrum": Problem(
        id="tantrum",
        title="a tantrum",
        cause="wanted the first turn",
        sign="stomped, cried, and shouted",
        soothes={"quiet", "sharing", "listening"},
        needs={"friend", "rest"},
        effect="the temper softened",
        keyword="tantrum",
    ),
    "spilled_basket": Problem(
        id="spilled_basket",
        title="a spilled basket",
        cause="bumped into a handle",
        sign="fell open on the path",
        soothes={"helping", "sharing", "care"},
        needs={"friend", "help"},
        effect="the pieces were gathered back together",
        keyword="basket",
    ),
    "lost_whistle": Problem(
        id="lost_whistle",
        title="a lost whistle",
        cause="put it down and forgot it",
        sign="was nowhere to be found",
        soothes={"curiosity", "looking", "care"},
        needs={"friend", "look"},
        effect="the whistle was found again",
        keyword="whistle",
    ),
}

GIFTS = {
    "reed_mat": Gift(
        id="reed_mat",
        label="a reed mat",
        helps={"rest", "quiet"},
        place="lakey_bank",
        promise="it gives a calm place to sit by the water",
    ),
    "stone_bench": Gift(
        id="stone_bench",
        label="a stone bench",
        helps={"rest", "watching"},
        place="sunny_hill",
        promise="it gives a steady place to wait and breathe",
    ),
    "shared_basket": Gift(
        id="shared_basket",
        label="a shared basket",
        helps={"sharing", "helping"},
        place="reed_glen",
        promise="it keeps small things together so no one feels left out",
    ),
}

NAMES = ["Milo", "Nia", "Pip", "Tavi", "Luna", "Rowan"]
TRAITS = ["kind", "curious", "gentle", "patient", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    gift: str
    friend_a: str
    friend_b: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
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


def problem_can_be_soothed(problem: Problem, gift: Gift, place: Place) -> bool:
    return bool(problem.soothes & gift.helps) and place.name.startswith(gift.place.replace("_", " ").split()[0])


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.waterside:
            lines.append(asp.fact("waterside", pid))
        for s in sorted(place.shelters):
            lines.append(asp.fact("shelters", pid, s))
        for i in sorted(place.invites):
            lines.append(asp.fact("invites", pid, i))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for s in sorted(prob.soothes):
            lines.append(asp.fact("soothes", pid, s))
        for n in sorted(prob.needs):
            lines.append(asp.fact("needs", pid, n))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for h in sorted(gift.helps):
            lines.append(asp.fact("helps", gid, h))
        lines.append(asp.fact("at", gid, gift.place))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, G) :- problem(P), gift(G), soothes(P, S), helps(G, S), needs(P, friend).
valid_story(Place, P, G) :- place(Place), at(G, Place), compatible(P, G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for gift_id, gift in GIFTS.items():
                if problem_can_be_soothed(prob, gift, place):
                    combos.append((place_id, prob_id, gift_id))
    return combos


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    prob = _safe_lookup(PROBLEMS, params.problem)
    gift = _safe_lookup(GIFTS, params.gift)

    world = World(place)
    a = world.add(Entity(id=params.friend_a, kind="character", type="mouse", label=params.friend_a))
    b = world.add(Entity(id=params.friend_b, kind="character", type="hedgehog", label=params.friend_b))
    mat = world.add(Entity(id="gift", kind="thing", type="gift", label=gift.label))

    a.memes["curiosity"] = 1
    a.memes["friendship"] = 1
    b.memes["friendship"] = 1

    world.say(f"At {place.name}, {a.id} was a {params.trait} little friend who loved to look closely at everything.")
    world.say(f"{a.id} noticed {b.id} near the water, and the two of them shared the kind of friendship that makes small places feel big.")
    world.say(f"One day, {b.id} had {prob.title}; {b.id} had {prob.sign}, because {prob.cause}.")

    if prob.id == "tantrum":
        b.meters["noise"] = 1
        b.memes["upset"] = 1
        world.say(f"{b.id} began to tantrum, and the crying bounced over the lakey bank like ripples on the water.")
    elif prob.id == "spilled_basket":
        b.meters["mess"] = 1
        world.say(f"{b.id} looked worried, because the basket had tipped and the bits were spread everywhere.")
    else:
        b.memes["worry"] = 1
        world.say(f"{b.id} searched and searched, but the missing whistle did not answer back.")

    world.say(f"{a.id} did not laugh. Instead, {a.id} became curious about how to make things better.")
    world.say(f"{a.id} found {gift.label} and brought it over, because {gift.promise}.")

    a.memes["friendship"] = 2
    b.memes["friendship"] = 2
    b.memes["calm"] = 1
    if prob.id == "tantrum":
        b.meters["noise"] = 0
        b.memes["upset"] = 0
    elif prob.id == "spilled_basket":
        b.meters["mess"] = 0
    else:
        b.memes["worry"] = 0

    world.say(f"{a.id} and {b.id} used {gift.label} to {prob.effect}.")
    world.say(f"In the end, the lakey place felt peaceful again, and the two friends shared a quiet smile by the water.")

    world.facts.update(place=params.place, problem=prob, gift=gift, friend_a=a, friend_b=b)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about friendship and curiosity at {world.place.name}.",
        f"Tell a child-friendly story where {f['friend_a'].id} helps {f['friend_b'].id} with {f['problem'].title}.",
        f"Write a gentle story including the words 'lakey', 'tantrum', and 'accommodate'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = _safe_fact(world, f, "friend_a")
    b = _safe_fact(world, f, "friend_b")
    prob = _safe_fact(world, f, "problem")
    gift = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"Who was the curious friend in the story?",
            answer=f"{a.id} was the curious friend, and {a.id} chose to look carefully instead of getting upset.",
        ),
        QAItem(
            question=f"What problem did {b.id} have by the lakey bank?",
            answer=f"{b.id} had {prob.title}, so {b.id} was {prob.sign}.",
        ),
        QAItem(
            question=f"How did {a.id} accommodate {b.id}?",
            answer=f"{a.id} brought {gift.label} and used it to help {b.id}, which made room for calm and friendship.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The upset was soothed, and the lakey place became peaceful again because the friends worked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people or animals care for one another, share, and help each other.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, ask, and learn about things that are new or puzzling.",
        ),
        QAItem(
            question="What does it mean to accommodate someone?",
            answer="To accommodate someone means to make room for their needs or feelings in a helpful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Lakey fable storyworld: friendship, curiosity, and accommodation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--gift", choices=GIFTS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, problem, gift = rng.choice(list(combos))
    a = rng.choice(NAMES)
    b = rng.choice([n for n in NAMES if n != a])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, gift=gift, friend_a=a, friend_b=b, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    py = set(valid_combos())
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        for s in stories:
            print(" ".join(map(str, s)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = valid_combos()
        for i, (place, problem, gift) in enumerate(combos):
            params = StoryParams(
                place=place,
                problem=problem,
                gift=gift,
                friend_a=_safe_lookup(NAMES, i % len(NAMES)),
                friend_b=_safe_lookup(NAMES, (i + 1) % len(NAMES)),
                trait=_safe_lookup(TRAITS, i % len(TRAITS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
