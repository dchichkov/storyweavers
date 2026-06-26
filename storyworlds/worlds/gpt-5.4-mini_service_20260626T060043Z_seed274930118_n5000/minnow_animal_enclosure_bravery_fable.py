#!/usr/bin/env python3
"""
A tiny fable-world about bravery in an animal enclosure.

A small minnow lives in a clear water pool inside an animal enclosure. A wide
crack in the filter gate makes the water shiver and the other fish hide. The
minnow is not the biggest creature there, but it notices a brave plan: swim
through the narrow tunnel, tug a reed into the crack, and help the keeper save
the pond. The little act of courage changes how the enclosure feels.

The world model tracks physical state in meters and emotional state in memes.
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
# Small world model
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gate: object | None = None
    keeper: object | None = None
    minnow: object | None = None
    reed: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "keeper":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.kind == "character" and self.type == "minnow":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Enclosure:
    place: str = "the animal enclosure"
    name: str = "the animal enclosure"
    water_depth: float = 0.8
    has_filter_gate: bool = True
    has_reeds: bool = True
    world: object | None = None
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
    def __init__(self, enclosure: Enclosure) -> None:
        self.enclosure = enclosure
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.enclosure)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "animal enclosure"
    animal: str = "minnow"
    feature: str = "Bravery"
    keeper_name: str = "Mara"
    samples: list = field(default_factory=list)
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
class Choice:
    id: str
    label: str
    detail: str
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


ANIMALS = {
    "minnow": Choice(
        id="minnow",
        label="minnow",
        detail="a small silver fish with quick fins",
    ),
}

FEATURES = {
    "Bravery": Choice(
        id="Bravery",
        label="Bravery",
        detail="the courage to do a hard thing for a good reason",
    ),
}

KEEPER_NAMES = ["Mara", "Nina", "Otis", "Sage", "Tala"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, minnow: Entity, keeper: Entity) -> None:
    world.say(
        f"In the animal enclosure, there lived a little {minnow.label} named {minnow.id}. "
        f"{keeper.id} kept the water clean and the reeds fresh."
    )
    world.say(
        f"The {minnow.label} was small, but it had a bright heart and a curious eye for trouble."
    )


def setup_problem(world: World, minnow: Entity, keeper: Entity) -> None:
    gate = world.get("gate")
    gate.meters["crack"] = 1.0
    minnow.memes["worry"] += 1.0
    keeper.memes["worry"] += 1.0
    world.say(
        f"One morning, a crack opened in the filter gate, and the pond water began to tremble."
    )
    world.say(
        f"The other fish hid near the stones, but {minnow.id} saw that the water was slipping away."
    )


def brave_choice(world: World, minnow: Entity, keeper: Entity) -> None:
    minnow.memes["bravery"] += 1.0
    minnow.memes["fear"] += 0.5
    world.say(
        f"{minnow.id} felt a shiver of fear, yet it also felt a stronger pull: the pull of {FEATURES['Bravery'].label}."
    )
    world.say(
        f"So the little {minnow.label} swam toward the narrow tunnel beside the gate, where the current was strongest."
    )


def act_and_fix(world: World, minnow: Entity, keeper: Entity) -> None:
    gate = world.get("gate")
    reed = world.get("reed")
    gate.meters["crack"] = 0.0
    reed.meters["placed"] = 1.0
    keeper.memes["relief"] += 1.0
    keeper.memes["admiration"] += 1.0
    minnow.memes["bravery"] += 1.0
    minnow.memes["joy"] += 1.0
    world.say(
        f"With a tiny but determined push, {minnow.id} nudged a reed into the crack."
    )
    world.say(
        f"{keeper.id} hurried over, fixed the latch, and smiled at the brave little helper."
    )


def ending(world: World, minnow: Entity, keeper: Entity) -> None:
    minnow.memes["worry"] = 0.0
    keeper.memes["worry"] = 0.0
    world.say(
        f"Before long, the water grew steady again, and the whole enclosure felt calm."
    )
    world.say(
        f"The {minnow.label} still was not big, but it had shown that true {FEATURES['Bravery'].label.lower()} can be small and strong at once."
    )
    world.say(
        f"And from that day on, the other fish did not only see a minnow; they saw a friend who could be brave."
    )


def tell_story(params: StoryParams) -> World:
    world = World(Enclosure())
    minnow = world.add(Entity(id="Milo", kind="character", type="minnow", label="minnow"))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type="keeper", label="keeper"))
    gate = world.add(Entity(id="gate", label="filter gate", type="gate"))
    reed = world.add(Entity(id="reed", label="reed", type="reed"))

    introduce(world, minnow, keeper)
    world.para()
    setup_problem(world, minnow, keeper)
    world.para()
    brave_choice(world, minnow, keeper)
    act_and_fix(world, minnow, keeper)
    world.para()
    ending(world, minnow, keeper)

    world.facts.update(
        minnow=minnow,
        keeper=keeper,
        gate=gate,
        reed=reed,
        feature=FEATURES["Bravery"],
        enclosure=world.enclosure,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    keeper = _safe_fact(world, world.facts, "keeper").id
    return [
        "Write a short fable about a minnow in an animal enclosure who learns bravery.",
        f"Tell a child-friendly story where {keeper} and a minnow face a problem in the water garden.",
        "Write a gentle fable with a tiny fish, a broken gate, and a brave fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    minnow = _safe_fact(world, world.facts, "minnow")
    keeper = _safe_fact(world, world.facts, "keeper")
    return [
        QAItem(
            question="Who was the brave little helper in the enclosure?",
            answer=f"The brave little helper was {minnow.id}, the minnow.",
        ),
        QAItem(
            question="What problem made the pond water shiver?",
            answer="A crack opened in the filter gate, and the water began to slip away.",
        ),
        QAItem(
            question="How did the minnow help?",
            answer=f"{minnow.id} swam to the gate and nudged a reed into the crack so {keeper.id} could fix it.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The water grew steady again, the enclosure became calm, and the minnow was seen as brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a minnow?",
            answer="A minnow is a small fish, and small fish often move quickly through water.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a hard thing even when you feel scared, because it is the right thing to do.",
        ),
        QAItem(
            question="Why do animal enclosures need careful keepers?",
            answer="Animal enclosures need careful keepers so the animals stay safe, fed, and clean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% enclosure(e).
% character(c).
% kind(c,minnow).
% kind(k,keeper).
% problem(crack).
% feature(bravery).

% The minnow is brave if it helps fix the crack.
brave(C) :- kind(C,minnow), fixes(C,crack).

% Fixing the crack resolves the water problem.
resolved :- fixes(_,crack).

% A compatible story needs a minnow, a keeper, bravery, and a water problem.
valid_story :- kind(C,minnow), kind(K,keeper), feature(bravery), problem(crack).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("enclosure", "animal_enclosure"),
        asp.fact("character", "minnow"),
        asp.fact("character", "keeper"),
        asp.fact("kind", "minnow", "minnow"),
        asp.fact("kind", "keeper", "keeper"),
        asp.fact("problem", "crack"),
        asp.fact("feature", "bravery"),
        asp.fact("fixes", "minnow", "crack"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show brave/1.\n#show resolved/0.\n#show valid_story/0.\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show resolved/0.\n#show valid_story/0."))
    names = {sym.name for sym in model}
    if {"brave", "resolved", "valid_story"}.issubset(names):
        print("OK: ASP story twin is consistent.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-world about a brave minnow in an animal enclosure.")
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
    return StoryParams(
        seed=getattr(args, "seed", None),
        keeper_name=rng.choice(KEEPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(parts) if parts else f"{e.id} ({e.type})")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_check())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(seed=base_seed + i, keeper_name=name)) for i, name in enumerate(KEEPER_NAMES[:3])]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### sample {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
