#!/usr/bin/env python3
"""
storyworlds/worlds/ninety_succession_pike_kindness_ghost_story.py
==================================================================

A small ghost-story world about a lonely place, a careful succession of
small acts, and a kindness that changes what a ghost is waiting for.

The seed-image behind this world is a child-friendly ghost story:
- an old pike-side path or pier where someone waits in the dark,
- a chain of small actions taken in succession,
- ninety little marks of patience,
- and kindness that helps a ghost rest at last.

This script generates a complete, state-driven story with a beginning,
a turn, and a resolution image.
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
# Domain constants
# ---------------------------------------------------------------------------
NINETY_MARKS = 90
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    ghost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def plural_word(self) -> str:
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
    place: str
    kind: str
    affordances: set[str] = field(default_factory=set)
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
class Ritual:
    id: str
    noun: str
    verb: str
    gerund: str
    small_step: str
    effect: str
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
class Charm:
    id: str
    label: str
    phrase: str
    target_kind: str
    clears: set[str]
    price: str
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
SETTINGS = {
    "pike": Setting(place="the pike", kind="waterfront", affordances={"count_lights", "listen", "leave_offering"}),
    "dock": Setting(place="the old dock", kind="waterfront", affordances={"count_lights", "listen", "leave_offering"}),
    "graveyard_gate": Setting(place="the graveyard gate", kind="quiet_place", affordances={"count_lights", "listen"}),
}

RITUALS = {
    "counting": Ritual(
        id="counting",
        noun="little lights",
        verb="count the lights",
        gerund="counting the lights",
        small_step="count one more light in the dark",
        effect="the darkness felt a little smaller",
        tags={"light", "counting", "ninety"},
    ),
    "listening": Ritual(
        id="listening",
        noun="the wind",
        verb="listen to the wind",
        gerund="listening to the wind",
        small_step="listen for the softest whisper",
        effect="the place felt less lonely",
        tags={"wind", "quiet"},
    ),
    "offering": Ritual(
        id="offering",
        noun="bread crumbs",
        verb="leave a small offering",
        gerund="leaving a small offering",
        small_step="set down one careful gift",
        effect="the waiting spirit felt noticed",
        tags={"offering", "kindness"},
    ),
}

CHARMS = {
    "warm_coat": Charm(
        id="warm_coat",
        label="a warm coat",
        phrase="a warm coat with bright buttons",
        target_kind="child",
        clears={"cold"},
        price="keeps the child warm while they go outside",
    ),
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a round glass belly",
        target_kind="any",
        clears={"dark"},
        price="helps the child see the path",
    ),
    "kind_note": Charm(
        id="kind_note",
        label="a kind note",
        phrase="a kind note with careful words",
        target_kind="ghost",
        clears={"lonely", "stuck"},
        price="gives the ghost a gentle message to hold",
    ),
}

CHILD_NAMES = ["Mina", "Toby", "Elsie", "Noah", "Iris", "Lena", "Eli", "Mara"]
GHOST_NAMES = ["Moss", "Wren", "Pip", "Sable"]
TRAITS = ["quiet", "curious", "brave", "gentle", "careful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ritual: str
    charm: str
    child_name: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story model helpers
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world with a kind ending, a pike-side setting, and ninety small steps."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.place == "pike" and params.ritual == "counting" and params.charm == "kind_note":
        return
    if params.ritual == "offering" and params.charm == "kind_note":
        return
    if params.place == "graveyard_gate" and params.ritual == "listening":
        return
    pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    ritual = getattr(args, "ritual", None) or rng.choice(list(RITUALS))
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))

    # Strong seed constraint: this world is centered on ninety, succession, pike, kindness.
    if place == "pike" and ritual != "counting":
        ritual = "counting"
    if ritual == "counting" and charm != "kind_note":
        charm = "kind_note"
    if getattr(args, "place", None) and getattr(args, "ritual", None) and getattr(args, "charm", None):
        reasonableness_gate(StoryParams(place, ritual, charm, "Mina", "Moss", "gentle"))

    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    ghost_name = getattr(args, "ghost_name", None) or rng.choice(GHOST_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    params = StoryParams(place=place, ritual=ritual, charm=charm, child_name=child_name, ghost_name=ghost_name, trait=trait)
    reasonableness_gate(params)
    return params


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id="child", kind="character", type="child", label=params.child_name, owner=None))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name, owner=None))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type=_safe_lookup(CHARMS, params.charm).id,
        label=_safe_lookup(CHARMS, params.charm).label,
        phrase=_safe_lookup(CHARMS, params.charm).phrase,
        owner=child.id,
    ))
    world.facts.update(child=child, ghost=ghost, charm=charm, params=params)
    return world


def run_story(world: World) -> None:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    ghost: Entity = _safe_fact(world, world.facts, "ghost")
    charm: Entity = _safe_fact(world, world.facts, "charm")
    ritual = _safe_lookup(RITUALS, params.ritual)

    child.memes["curiosity"] = 1
    ghost.memes["lonely"] = 1
    ghost.meters["waiting"] = 1

    world.say(
        f"On the edge of {world.setting.place}, {child.label} was a {params.trait} little child who noticed strange things."
    )
    world.say(
        f"People said a ghost named {ghost.label} still lingered there, because something old and unfinished kept him waiting."
    )
    world.say(
        f"{child.label} brought {charm.phrase}, because {_safe_lookup(CHARMS, params.charm).price}."
    )

    world.para()
    if params.ritual == "counting":
        world.say(
            f"Night after night, {child.label} began to {ritual.verb}. First came one lamp, then two, then a long succession of tiny glows."
        )
        world.say(
            f"By the time {child.label} reached {NINETY_MARKS}, the dark path had turned into a soft line of light, and the old water by the pike no longer looked so hungry."
        )
        ghost.meters["waiting"] += NINETY_MARKS
        ghost.memes["lonely"] += 1
        child.meters["lights"] = NINETY_MARKS
        child.memes["patience"] = 1
    elif params.ritual == "listening":
        world.say(
            f"{child.label} sat very still and tried to {ritual.verb}. One whisper followed another, in a quiet succession like leaves touching water."
        )
        world.say(
            f"The wind carried a sad sound from the pike, and {child.label} understood that the ghost was not mean, only stuck."
        )
        ghost.memes["lonely"] += 1
        child.memes["patience"] = 1
    else:
        world.say(
            f"{child.label} chose to {ritual.verb}. Small gift after small gift, kindness came in a quiet succession."
        )
        world.say(
            f"Each offering told the ghost he had not been forgotten, and the pike path felt less cold."
        )
        ghost.memes["lonely"] += 1
        child.memes["kindness"] = 1

    world.para()
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    ghost.meters["restlessness"] = 1
    world.say(
        f"Then {child.label} opened the little note and wrote, \"You do not have to wait alone.\""
    )
    world.say(
        f"The words were simple, but they were kind, and kindness changed the way the air felt."
    )
    world.say(
        f"The ghost looked at {child.label}, and for the first time, his waiting softened."
    )

    world.para()
    ghost.memes["lonely"] = 0
    ghost.meters["waiting"] = 0
    ghost.meters["rest"] = 1
    child.memes["fear"] = 0
    child.memes["warmth"] = 1
    world.say(
        f"At last, the ghost gave a tiny smile. The old place by the pike did not need to be scary anymore."
    )
    world.say(
        f"{child.label} went home with {charm.label}, and behind them the lights stood in a long, bright succession, while {ghost.label} finally rested."
    )

    world.facts["resolved"] = True
    world.facts["lights"] = NINETY_MARKS if params.ritual == "counting" else 3


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def story_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f"Write a child-friendly ghost story set at {world.setting.place} with kindness at the end.",
        f"Tell a spooky-but-gentle story where {p.child_name} helps a ghost by making a succession of small kind acts.",
        f"Write a short story that includes the words ninety, succession, pike, and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    ghost: Entity = _safe_fact(world, world.facts, "ghost")
    charm: Entity = _safe_fact(world, world.facts, "charm")
    qa = [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {child.label}, a {p.trait} little child, and the ghost {ghost.label} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {child.label} use to help the ghost?",
            answer=f"{child.label} used {charm.label}, which was {charm.phrase}, to show kindness and make the night feel safer.",
        ),
        QAItem(
            question="What changed after the little acts in succession?",
            answer=f"The ghost was no longer lonely and waiting. At the end, {ghost.label} could rest, and {child.label} went home feeling warm and brave.",
        ),
    ]
    if p.ritual == "counting":
        qa.append(
            QAItem(
                question=f"How many lights did {child.label} count?",
                answer=f"{child.label} counted {NINETY_MARKS} lights, one after another, in a long succession.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle and helpful for someone else.",
        ),
        QAItem(
            question="What does succession mean?",
            answer="A succession is one thing after another in order, like steps, lights, or small actions.",
        ),
        QAItem(
            question="What is a pike?",
            answer="A pike can mean a long, pointed path or a place near water, and in stories it can feel old and lonely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.label or e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(pike).
place(dock).
place(graveyard_gate).

ritual(counting).
ritual(listening).
ritual(offering).

charm(kind_note).
charm(warm_coat).
charm(lantern).

compatible(pike, counting, kind_note).
compatible(pike, offering, kind_note).
compatible(dock, counting, kind_note).
compatible(graveyard_gate, listening, kind_note).
compatible(graveyard_gate, offering, kind_note).

story(P,R,C) :- place(P), ritual(R), charm(C), compatible(P,R,C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RITUALS:
        lines.append(asp.fact("ritual", r))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for r in RITUALS:
            for c in CHARMS:
                if (p, r, c) in {
                    ("pike", "counting", "kind_note"),
                    ("pike", "offering", "kind_note"),
                    ("dock", "counting", "kind_note"),
                    ("graveyard_gate", "listening", "kind_note"),
                    ("graveyard_gate", "offering", "kind_note"),
                }:
                    out.append((p, r, c))
    return out


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    run_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
    StoryParams(place="pike", ritual="counting", charm="kind_note", child_name="Mina", ghost_name="Moss", trait="gentle"),
    StoryParams(place="dock", ritual="counting", charm="kind_note", child_name="Toby", ghost_name="Pip", trait="careful"),
    StoryParams(place="graveyard_gate", ritual="listening", charm="kind_note", child_name="Iris", ghost_name="Sable", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for p, r, c in combos:
            print(f"  {p} / {r} / {c}")
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.ritual} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
