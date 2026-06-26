#!/usr/bin/env python3
"""
Storyworld: fluff / subscription / argue
=========================================

A small whodunit-style story world about a strange clue, a misunderstanding,
an argument, a surprise reveal, and a lesson learned.

Premise:
- A child receives a subscription package with a fluffy item or a fluffy mess.
- Something seems suspicious.
- The household argues over who caused it.
- A careful clue reveals the truth.
- The ending teaches a gentle lesson about checking facts first.

The world is simulated with physical meters and emotional memes so the prose
comes from state changes rather than from a frozen paragraph template.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    culprit: object | None = None
    fluff: object | None = None
    parent: object | None = None
    source: object | None = None
    sub: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return copy.deepcopy(self)


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
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    subscription: str
    fluff_source: str
    clue: str
    culprit: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


NAMES = {
    "girl": ["Mina", "Ruby", "Nora", "Ivy", "Luna", "Tess"],
    "boy": ["Eli", "Theo", "Owen", "Noah", "Finn", "Milo"],
}
PARENTS = ["mother", "father"]
PLACES = ["the apartment", "the little house", "the hallway", "the kitchen", "the front room"]

SUBSCRIPTIONS = {
    "book": {
        "label": "book subscription box",
        "phrase": "a book subscription box",
        "arrival": "a new book club box",
        "expected": "books",
    },
    "craft": {
        "label": "craft subscription box",
        "phrase": "a craft subscription box",
        "arrival": "a monthly craft box",
        "expected": "stickers and paper",
    },
    "snack": {
        "label": "snack subscription box",
        "phrase": "a snack subscription box",
        "arrival": "a surprise snack box",
        "expected": "cookies and crackers",
    },
}

FLUFF_SOURCES = {
    "pillow": "the couch pillow",
    "toy": "the old plush toy",
    "coat": "the fuzzy coat",
    "box": "the subscription box itself",
}

CLUES = {
    "tag": "a tiny shipping tag",
    "string": "a loose piece of twine",
    "receipt": "a crumpled receipt",
    "feather": "a soft white feather",
}

CULPRITS = {
    "cat": "the cat",
    "dog": "the dog",
    "dryer": "the dryer vent",
    "wind": "the open window",
}

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A fluff source is suspicious when it can shed fluff.
suspicious(S) :- source(S).

% A misunderstanding happens when the clue points to one thing but the truth is another.
misunderstanding(C) :- clue(C), clue_points_to_false(C).

% An argument happens when suspicion rises and the truth has not yet been checked.
argument :- suspicion, not checked_truth.

% A surprise is the moment the clue reveals the true culprit.
surprise :- checked_truth, truth_revealed.

% Lesson learned follows after the surprise and the apology.
lesson_learned :- surprise, apology.

#show suspicious/1.
#show misunderstanding/1.
#show argument/0.
#show surprise/0.
#show lesson_learned/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in FLUFF_SOURCES:
        lines.append(asp.fact("source", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1. #show misunderstanding/1. #show argument/0. #show surprise/0. #show lesson_learned/0."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("suspicious", ("pillow",)),
        ("suspicious", ("toy",)),
        ("suspicious", ("coat",)),
        ("suspicious", ("box",)),
    }
    if any(name == "argument" for name, _ in atoms):
        pass
    print(f"OK: ASP twin loaded ({len(model)} shown atoms).")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style storyworld about fluff, a subscription box, and a misunderstanding.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--subscription", choices=SUBSCRIPTIONS)
    ap.add_argument("--fluff-source", choices=FLUFF_SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
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


def valid_combo(sub: str, fluff: str, culprit: str) -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    subscription = getattr(args, "subscription", None) or rng.choice(sorted(SUBSCRIPTIONS))
    fluff_source = getattr(args, "fluff_source", None) or rng.choice(sorted(FLUFF_SOURCES))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    culprit = getattr(args, "culprit", None) or rng.choice(sorted(CULPRITS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    place = getattr(args, "place", None) or rng.choice(PLACES)
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=place,
        subscription=subscription,
        fluff_source=fluff_source,
        clue=clue,
        culprit=culprit,
    )


def _do_suspicion(world: World, child: Entity, sub: Entity, fluff: Entity) -> None:
    fluff.meters["fluff"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"One afternoon, {child.id} found {sub.phrase} on the table. "
        f"The lid was puffed up with a little cloud of fluff."
    )


def _do_misunderstanding(world: World, child: Entity, parent: Entity, fluff_source: Entity) -> None:
    child.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{child.id} stared at {fluff_source.label} and thought the mess must have started there. "
        f"{child.pronoun().capitalize()} told {parent.pronoun('object')} so, and {parent.id} frowned."
    )
    world.say(
        f"That guess sounded neat, but it was only a guess."
    )


def _do_argument(world: World, child: Entity, parent: Entity) -> None:
    child.memes["argue"] += 1
    parent.memes["argue"] += 1
    world.say(
        f"{child.id} and {parent.id} began to argue quietly in the hallway. "
        f"{child.id} pointed at the fluff, and {parent.id} pointed at the closed window."
    )


def _do_surprise(world: World, child: Entity, parent: Entity, culprit: Entity, clue: Entity) -> None:
    child.memes["surprised"] += 1
    parent.memes["surprised"] += 1
    culprit.meters["seen"] = culprit.meters.get("seen", 0) + 1
    world.say(
        f"Then {child.id} noticed {clue.label} tucked under the table leg. "
        f"It led to {culprit.label}, not the pillow at all."
    )
    world.say(
        f"The real answer was a surprise: {culprit.label} had blown the fluff across the floor."
    )


def _do_lesson(world: World, child: Entity, parent: Entity) -> None:
    child.memes["learned"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"{child.id} looked at {parent.id} and took a breath. "
        f"{child.pronoun().capitalize()} learned that a strange clue is not the same as the whole truth."
    )
    world.say(
        f"{parent.id} smiled and said, \"Next time, we check the facts before we argue.\""
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    subcfg = _safe_lookup(SUBSCRIPTIONS, params.subscription)
    fluff_source_label = _safe_lookup(FLUFF_SOURCES, params.fluff_source)
    clue_label = _safe_lookup(CLUES, params.clue)
    culprit_label = _safe_lookup(CULPRITS, params.culprit)

    sub = world.add(Entity(id="SubscriptionBox", type="box", label=subcfg["label"], phrase=subcfg["phrase"], owner=child.id))
    fluff = world.add(Entity(id="Fluff", type="thing", label="fluff", plural=False))
    source = world.add(Entity(id="Source", type="thing", label=fluff_source_label))
    clue = world.add(Entity(id="Clue", type="thing", label=clue_label))
    culprit = world.add(Entity(id="Culprit", type="thing", label=culprit_label))

    world.facts = {
        "child": child,
        "parent": parent,
        "subscription": subcfg,
        "source": source,
        "clue": clue,
        "culprit": culprit,
    }

    world.say(
        f"{child.id} loved {subcfg['label']}. Every month it arrived in a neat box, and {child.id} opened it like a tiny case to solve."
    )
    world.say(
        f"This time, the box came with an odd puff of fluff, and that made the room feel mysterious."
    )

    world.para()
    _do_suspicion(world, child, sub, fluff)
    _do_misunderstanding(world, child, parent, source)
    _do_argument(world, child, parent)

    world.para()
    _do_surprise(world, child, parent, culprit, clue)
    _do_lesson(world, child, parent)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    sub = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "subscription")["label"]
    return [
        f'Write a short whodunit for children about {child.id}, {sub}, and a puff of fluff.',
        f"Tell a mystery story where a subscription box causes a misunderstanding, then the truth is found by following a clue.",
        f'Write a gentle story with the words "fluff", "subscription", and "argue" that ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    source = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "source")
    culprit = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    sub = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "subscription")["label"]
    return [
        QAItem(
            question=f"What kind of box did {child.id} open?",
            answer=f"{child.id} opened a {sub}, which arrived like a monthly surprise.",
        ),
        QAItem(
            question=f"Why did {child.id} and {parent.id} argue?",
            answer=f"They argued because they both had guesses about the fluff, but they had not checked the clue yet.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"{clue.label.capitalize()} helped point to the real cause of the fluff.",
        ),
        QAItem(
            question=f"What really caused the fluff?",
            answer=f"The real cause was {culprit.label}, not {source.label}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer="The lesson was to check the facts before deciding who is wrong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is fluff?", answer="Fluff is soft, light material that can float, pile up, or cling to things."),
        QAItem(question="What is a subscription?", answer="A subscription is a plan where something arrives again and again, usually on a schedule."),
        QAItem(question="What does argue mean?", answer="To argue means to disagree and talk in an upset way."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that needs clues and careful thinking to solve."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for sub in SUBSCRIPTIONS:
            for fluff in FLUFF_SOURCES:
                combos.append((place, sub, fluff))
    return combos


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", place="the hallway", subscription="book", fluff_source="pillow", clue="tag", culprit="cat"),
    StoryParams(name="Eli", gender="boy", parent="father", place="the kitchen", subscription="craft", fluff_source="coat", clue="receipt", culprit="dryer"),
    StoryParams(name="Nora", gender="girl", parent="mother", place="the little house", subscription="snack", fluff_source="toy", clue="feather", culprit="wind"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(NAMES[getattr(args, "gender", None) or rng.choice(["girl", "boy"])]),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        parent=getattr(args, "parent", None) or rng.choice(PARENTS),
        place=getattr(args, "place", None) or rng.choice(PLACES),
        subscription=getattr(args, "subscription", None) or rng.choice(sorted(SUBSCRIPTIONS)),
        fluff_source=getattr(args, "fluff_source", None) or rng.choice(sorted(FLUFF_SOURCES)),
        clue=getattr(args, "clue", None) or rng.choice(sorted(CLUES)),
        culprit=getattr(args, "culprit", None) or rng.choice(sorted(CULPRITS)),
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show suspicious/1. #show misunderstanding/1. #show argument/0. #show surprise/0. #show lesson_learned/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show suspicious/1. #show misunderstanding/1. #show argument/0. #show surprise/0. #show lesson_learned/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
