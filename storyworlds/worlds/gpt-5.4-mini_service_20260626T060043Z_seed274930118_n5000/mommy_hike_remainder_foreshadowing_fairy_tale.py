#!/usr/bin/env python3
"""
storyworlds/worlds/mommy_hike_remainder_foreshadowing_fairy_tale.py
===================================================================

A small fairy-tale story world about a mommy, a hike, and a remainder.

Premise:
- A child goes on a forest hike with mommy.
- They carry a little basket with the remainder of a honey cake.
- Mommy notices signs in the woods and foreshadows trouble before it starts.

Tension:
- The child wants to hurry on and keep the basket open.
- If they leave the remainder exposed on the hike, little forest creatures may follow the smell.
- Mommy worries not because she is stern, but because she can read the road ahead.

Turn and resolution:
- Mommy points out the clues: buzzing bees, a bend in the path, and darkening clouds.
- She ties the basket shut and suggests saving the remainder for the stone bench at the hilltop.
- The child agrees, and the hike becomes calmer and sweeter.
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
# Shared world model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    mommy: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mommy", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Trail:
    place: str = "the whispering woods"
    afford_hike: bool = True
    has_bench: bool = True
    has_creek: bool = True
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
class Snack:
    label: str
    phrase: str
    scent: str
    leftover_name: str
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


@dataclass
class World:
    trail: Trail
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    w: object | None = None
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
        import copy as _copy
        w = World(self.trail)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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
class StoryParams:
    seed: Optional[int] = None
    name: str = "Lina"
    child_type: str = "girl"
    parent_type: str = "mother"
    trait: str = "brave"
    snack: str = "honey_cake"
    place: str = "whispering_woods"
    weather: str = "soft_wind"
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


TRAILS = {
    "whispering_woods": Trail(place="the whispering woods", afford_hike=True, has_bench=True, has_creek=True),
    "mossy_path": Trail(place="the mossy path", afford_hike=True, has_bench=False, has_creek=True),
    "hill_lane": Trail(place="the hill lane", afford_hike=True, has_bench=True, has_creek=False),
}

SNACKS = {
    "honey_cake": Snack(label="cake", phrase="a honey cake in a cloth wrap", scent="sweet honey", leftover_name="the remainder of the cake"),
    "berry_tart": Snack(label="tart", phrase="a berry tart in a basket", scent="ripe berries", leftover_name="the remainder of the tart"),
    "apple_pie": Snack(label="pie", phrase="an apple pie under a little lid", scent="warm apples", leftover_name="the remainder of the pie"),
}

NAMES = ["Lina", "Mira", "Toby", "June", "Nora", "Owen"]
TRAITS = ["curious", "gentle", "brave", "cheerful", "spirited", "patient"]


class Rule:
    def __init__(self, name: str, fn):
        self.name = name
        self.fn = fn


def _r_scent(world: World) -> list[str]:
    out = []
    child = world.get("child")
    snack = world.get("snack")
    if child.memes.get("snack_open", 0) >= THRESHOLD and snack.meters.get("open", 0) >= THRESHOLD:
        sig = ("scent",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["notice"] = child.memes.get("notice", 0) + 1
        out.append("A sweet smell drifted ahead on the wind.")
    return out


def _r_follow(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("notice", 0) < THRESHOLD:
        return out
    if child.memes.get("leave_path", 0) >= THRESHOLD:
        sig = ("follow",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["risk"] = child.memes.get("risk", 0) + 1
        out.append("__follow__")
    return out


RULES = [Rule("scent", _r_scent), Rule("follow", _r_follow)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__follow__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def foreshadow(world: World, mommy: Entity, child: Entity, snack: Entity) -> None:
    child.memes["snack_open"] = child.memes.get("snack_open", 0) + 1
    snack.meters["open"] = snack.meters.get("open", 0) + 1
    world.say(
        f"As they started down {world.trail.place}, mommy noticed bees dancing near the path "
        f"and a dark cloud resting on the hill. She glanced at {child.id}'s open snack and said, "
        f'"Keep the {snack.label} wrapped. The woods are making a sign."'
    )


def desire(world: World, child: Entity, snack: Entity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0) + 1
    world.say(
        f"{child.id} wanted to hurry on and nibble the {snack.label} at once, "
        f"because the sweet smell was already drifting out."
    )


def warn(world: World, mommy: Entity, child: Entity, snack: Entity) -> None:
    world.say(
        f"Mommy smiled kindly and pointed to the bees. "
        f'"If we leave {snack.owner}\'s {snack.label} open, the little forest folk will come nosing after the remainder," she said.'
    )
    world.facts["foreshadowed"] = True


def test_tension(world: World, child: Entity) -> None:
    child.memes["leave_path"] = child.memes.get("leave_path", 0) + 1
    world.say(
        f"{child.id} took a few quick steps toward the scent, then paused when mommy lifted a hand."
    )


def resolve(world: World, mommy: Entity, child: Entity, snack: Entity) -> None:
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    child.memes["risk"] = 0
    snack.meters["open"] = 0
    world.say(
        f"Mommy tied the basket shut with a blue ribbon and saved the remainder for the stone bench at the top of the hill. "
        f"{child.id} nodded, held mommy's hand, and the two of them walked on more slowly."
    )
    world.say(
        f"At last they reached the bench, where the air was still and the woods were bright. "
        f"They shared the remainder there, and it tasted even sweeter after the careful wait."
    )


def tell(params: StoryParams) -> World:
    trail = _safe_lookup(TRAILS, params.place)
    snack_cfg = _safe_lookup(SNACKS, params.snack)
    world = World(trail=trail)

    child = world.add(Entity(id=params.name, kind="character", type=params.child_type))
    mommy = world.add(Entity(id="mommy", kind="character", type=params.parent_type, label="mommy"))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=snack_cfg.label,
        phrase=snack_cfg.phrase,
        owner=child.id,
        caretaker=mommy.id,
        carried_by=child.id,
    ))

    world.say(
        f"Once upon a time, {child.id}, a {params.trait} little {params.child_type}, set out on a hike with mommy."
    )
    world.say(
        f"In the basket they carried {snack_cfg.phrase}, and {child.id} loved the promise of {snack_cfg.leftover_name} for later."
    )

    world.para()
    foreshadow(world, mommy, child, snack)
    warn(world, mommy, child, snack)
    desire(world, child, snack)
    test_tension(world, child)
    propagate(world)

    world.para()
    resolve(world, mommy, child, snack)

    world.facts.update(
        child=child,
        mommy=mommy,
        snack=snack,
        snack_cfg=snack_cfg,
        trail=trail,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f"Write a fairy-tale story about {child.id}, mommy, and a hike through the woods, with a careful foreshadowing of later trouble.",
        f"Tell a gentle story in which mommy notices a clue on a hike and helps {child.id} save the remainder of a snack.",
        f"Write a short fairy tale where the woods seem to warn a child to be patient with the remainder of the picnic food.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    snack_cfg = _safe_fact(world, f, "snack_cfg")
    trail = _safe_fact(world, f, "trail").place
    return [
        QAItem(
            question=f"Who went on the hike with mommy?",
            answer=f"{child.id} went on the hike with mommy through {trail}.",
        ),
        QAItem(
            question=f"What did mommy ask {child.id} to keep wrapped?",
            answer=f"Mommy asked {child.id} to keep the {snack_cfg.label} wrapped so the remainder would stay safe.",
        ),
        QAItem(
            question=f"What clue foreshadowed trouble on the hike?",
            answer="The bees near the path and the dark cloud on the hill foreshadowed that something might go wrong if the snack stayed open.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="Mommy tied the basket shut, and they shared the remainder at the stone bench after the hike.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little hints about what may happen later.",
        ),
        QAItem(
            question="What is a hike?",
            answer="A hike is a long walk on a trail, often through woods, hills, or other outdoor places.",
        ),
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left after some of something has been used, eaten, or shared.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A hike story is valid when the place supports hiking.
valid_place(P) :- trail(P).

% Mommy's foreshadowing is meaningful when the child has an open snack and the
% trail has a bench where the remainder can be saved for later.
foreshadowing(P) :- valid_place(P), has_bench(P), has_snack_remainder(P).

% A clean resolution requires a bench and a wrapped remainder.
safe_resolution(P) :- valid_place(P), has_bench(P), has_snack_remainder(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, trail in TRAILS.items():
        lines.append(asp.fact("trail", pid))
        if trail.afford_hike:
            lines.append(asp.fact("hike", pid))
        if trail.has_bench:
            lines.append(asp.fact("has_bench", pid))
        if trail.has_creek:
            lines.append(asp.fact("has_creek", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("leftover_name", sid, snack.leftover_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_place/1. #show safe_resolution/1."))
    places = sorted(set(asp.atoms(model, "valid_place")))
    safe = sorted(set(asp.atoms(model, "safe_resolution")))
    py_places = sorted([p for p, t in TRAILS.items() if t.afford_hike])
    py_safe = sorted([p for p, t in TRAILS.items() if t.afford_hike and t.has_bench])
    if places == [(p,) for p in py_places] and safe == [(p,) for p in py_safe]:
        print("OK: ASP matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP valid_place:", places)
    print("PY  valid_place:", py_places)
    print("ASP safe_resolution:", safe)
    print("PY  safe_resolution:", py_safe)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about mommy, a hike, and the remainder of a snack.")
    ap.add_argument("--place", choices=TRAILS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--snack", choices=SNACKS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(TRAILS))
    if not _safe_lookup(TRAILS, place).afford_hike:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or "mother"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(
        seed=None,
        name=name,
        child_type=gender,
        parent_type=parent,
        trait=trait,
        snack=snack,
        place=place,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(name="Lina", child_type="girl", parent_type="mother", trait="curious", snack="honey_cake", place="whispering_woods"),
    StoryParams(name="Toby", child_type="boy", parent_type="mother", trait="patient", snack="berry_tart", place="mossy_path"),
    StoryParams(name="Nora", child_type="girl", parent_type="mother", trait="brave", snack="apple_pie", place="hill_lane"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_place/1. #show safe_resolution/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_place/1. #show safe_resolution/1."))
        print("valid places:", sorted(set(asp.atoms(model, "valid_place"))))
        print("safe resolutions:", sorted(set(asp.atoms(model, "safe_resolution"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(getattr(args, "n", None) * 30, 30)):
            if len(samples) >= getattr(args, "n", None):
                break
            rng = random.Random(base_seed + i)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
