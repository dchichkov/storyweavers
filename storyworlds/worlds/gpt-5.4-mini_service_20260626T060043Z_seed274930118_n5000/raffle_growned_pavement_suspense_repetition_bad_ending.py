#!/usr/bin/env python3
"""
storyworlds/worlds/raffle_growned_pavement_suspense_repetition_bad_ending.py
============================================================================

A tiny nursery-rhyme-style story world about a raffle on the pavement, with
suspense, repetition, and a bad ending.

Premise:
- A child and a grown-up stand by a pavement raffle stall.
- The child longs for the shiny prize.
- The raffle is slow, the wait is repeated, and the tension builds.

Turn:
- The child hurries too close to the pavement edge.
- The ticket slips, or the prize wheel stalls, and the hoped-for win does not come.

Ending:
- The child goes home empty-handed, hearing the raffle bell go quiet behind them.

This world is intentionally constrained to one small domain and one story shape.
"""

from __future__ import annotations

import argparse
import copy
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
    grown: object | None = None
    stall: object | None = None
    ticket: object | None = None
    wheel: object | None = None
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
    place: str = "the pavement"
    outdoors: bool = True
    afford: set[str] = field(default_factory=set)
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
class Raffle:
    id: str
    label: str
    phrase: str
    shine: str
    wait: str
    loss: str
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


@dataclass
class StoryParams:
    place: str
    raffle: str
    name: str
    gender: str
    parent: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("waiting", 0.0) < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["suspense"] = child.memes.get("suspense", 0.0) + 1
    out.append("The little heart went thump-thump while the raffle wheel turned slow.")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ticket = world.entities.get("ticket")
    if not child or not ticket:
        return out
    if ticket.meters.get("lost", 0.0) < THRESHOLD:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["disappointment"] = child.memes.get("disappointment", 0.0) + 1
    out.append("The raffle prize was gone, and the child got only an empty hand.")
    return out


CAUSAL_RULES = [
    _r_suspense,
    _r_loss,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup_world(setting: Setting, raffle: Raffle, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, owner="parent"))
    grown = world.add(Entity(id="grownup", kind="character", type=parent, label=f"the {parent}"))
    ticket = world.add(Entity(
        id="ticket",
        kind="thing",
        type="ticket",
        label="raffle ticket",
        phrase=raffle.phrase,
        owner="child",
    ))
    wheel = world.add(Entity(id="wheel", kind="thing", type="wheel", label="raffle wheel"))
    stall = world.add(Entity(id="stall", kind="thing", type="stall", label="raffle stall"))

    child.memes["hope"] = 1
    child.memes["waiting"] = 0
    child.memes["suspense"] = 0
    child.memes["disappointment"] = 0

    world.facts.update(
        child=child,
        grownup=grown,
        ticket=ticket,
        wheel=wheel,
        stall=stall,
        raffle=raffle,
        trait=trait,
        setting=setting,
    )
    return world


def begin(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    grownup: Entity = _safe_fact(world, world.facts, "grownup")
    world.say(
        f"{child.label} went pat-pat along {world.setting.place}, with {grownup.label} beside {child.pronoun('object')}."
    )
    world.say(
        f"There was a little raffle stall there, and {child.label} loved the shiny {raffle.label} in the window."
    )


def longing(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    child.memes["want"] = child.memes.get("want", 0) + 1
    world.say(
        f"{child.label} wanted the {raffle.label} so much that {child.pronoun().capitalize()} whispered, "
        f"\"One raffle, one chance, one little dance.\""
    )


def suspense_wait(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    wheel: Entity = _safe_fact(world, world.facts, "wheel")
    child.memes["waiting"] = child.memes.get("waiting", 0) + 1
    world.say(
        f"The raffle wheel went click, then tick, then tick again, and nobody knew what it would do."
    )
    world.say(
        f"{child.label} stood still-still still, while the {raffle.label} seemed to shine and hide at once."
    )
    propagate(world, narrate=True)


def warn_and_hesitate(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    grownup: Entity = _safe_fact(world, world.facts, "grownup")
    world.say(
        f"{grownup.label} lifted a hand and said, \"Wait a little, wait a little, or the prize may slip away.\""
    )
    child.memes["nervous"] = child.memes.get("nervous", 0) + 1
    world.say(
        f"{child.label} tried to wait, but {child.pronoun()} kept looking at the pavement crack by the stall."
    )


def bad_turn(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    ticket: Entity = _safe_fact(world, world.facts, "ticket")
    world.say(
        f"Then came the hush-hush hush: the ticket slid from {child.pronoun('possessive')} fingers and skated on the pavement."
    )
    ticket.meters["lost"] = 1
    ticket.meters["scraped"] = 1
    child.memes["shock"] = child.memes.get("shock", 0) + 1
    propagate(world, narrate=True)


def ending(world: World, raffle: Raffle) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    grownup: Entity = _safe_fact(world, world.facts, "grownup")
    world.say(
        f"When the wheel stopped, the little bell had no happy ding for {child.label}."
    )
    world.say(
        f"{child.label} went home with empty hands, and {grownup.label} walked beside {child.pronoun('object')} in the quiet dusk."
    )
    world.say(
        f"Behind them, the pavement stayed cold and plain, and the raffle sign flapped once, then twice, then not at all."
    )


SETTINGS = {
    "pavement": Setting(place="the pavement", outdoors=True, afford={"raffle"}),
}

RAFFLES = {
    "golden": Raffle(
        id="golden",
        label="golden raffle prize",
        phrase="a golden prize box with a bright red bow",
        shine="bright",
        wait="slow",
        loss="gone",
        tags={"raffle", "pavement", "suspense", "repetition", "bad-ending"},
    ),
    "blue": Raffle(
        id="blue",
        label="blue raffle prize",
        phrase="a blue prize bundle with a silver ribbon",
        shine="cool",
        wait="slow",
        loss="gone",
        tags={"raffle", "pavement", "suspense", "repetition", "bad-ending"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Mia", "Rose", "Ivy"]
BOY_NAMES = ["Tom", "Leo", "Ben", "Max", "Finn", "Sam"]
TRAITS = ["brave", "tiny", "curious", "spry", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for raffle_id in setting.afford:
            combos.append((place, raffle_id))
    return combos


def explain_rejection(place: str, raffle_id: str) -> str:
    return f"(No story: the little raffle world only works on the pavement.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    raffle: Raffle = _safe_fact(world, f, "raffle")
    return [
        f'Write a nursery-rhyme story with the word "raffle" that takes place on the pavement and ends badly.',
        f"Tell a small suspense story where {child.label} waits for a {raffle.label} on the pavement and the wait repeats.",
        f'Write a rhythmic story about a child on the pavement, a raffle wheel, and an ending with no prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    grownup: Entity = _safe_fact(world, f, "grownup")
    raffle: Raffle = _safe_fact(world, f, "raffle")
    qa = [
        QAItem(
            question=f"Who was waiting by the pavement raffle stall?",
            answer=f"{child.label} was waiting there with {grownup.label}.",
        ),
        QAItem(
            question=f"What did {child.label} want from the raffle?",
            answer=f"{child.label} wanted {raffle.label}.",
        ),
        QAItem(
            question=f"Why was the story full of suspense?",
            answer="Because the raffle wheel turned slowly and nobody knew if the child would win.",
        ),
        QAItem(
            question=f"What happened to the ticket in the end?",
            answer="It slipped onto the pavement and was lost, so the child did not get the prize.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a raffle?",
            answer="A raffle is a game where people wait to see if a ticket or number wins a prize.",
        ),
        QAItem(
            question="What is pavement?",
            answer="Pavement is the hard ground people walk on beside roads and stalls.",
        ),
        QAItem(
            question="Why does repeating words make a nursery rhyme feel catchy?",
            answer="Repeating words makes a nursery rhyme sound bouncy and easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A raffle story is valid if it is on the pavement and a raffle is afforded there.
valid_story(P, R) :- place(P), raffle(R), afford(P, R).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for r in sorted(setting.afford):
            lines.append(asp.fact("afford", pid, r))
    for rid in RAFFLES:
        lines.append(asp.fact("raffle", rid))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small nursery-rhyme raffle world on the pavement.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--raffle", choices=RAFFLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "raffle", None) and getattr(args, "raffle", None) not in RAFFLES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "raffle", None) is None or c[1] == getattr(args, "raffle", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, raffle_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, raffle=raffle_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(_safe_lookup(SETTINGS, params.place), _safe_lookup(RAFFLES, params.raffle), params.name, params.gender, params.parent, params.trait)
    begin(world, _safe_lookup(RAFFLES, params.raffle))
    world.para()
    longing(world, _safe_lookup(RAFFLES, params.raffle))
    suspense_wait(world, _safe_lookup(RAFFLES, params.raffle))
    warn_and_hesitate(world, _safe_lookup(RAFFLES, params.raffle))
    world.para()
    bad_turn(world, _safe_lookup(RAFFLES, params.raffle))
    ending(world, _safe_lookup(RAFFLES, params.raffle))
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(place="pavement", raffle="golden", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="pavement", raffle="blue", name="Tom", gender="boy", parent="father", trait="spry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, raffle) combos:")
        for p, r in combos:
            print(f"  {p} {r}")
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
            header = f"### {p.name}: raffle={p.raffle} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
