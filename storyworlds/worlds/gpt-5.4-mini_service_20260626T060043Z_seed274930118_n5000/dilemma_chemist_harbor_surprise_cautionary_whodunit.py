#!/usr/bin/env python3
"""
A small whodunit-style story world set at a harbor, with a chemist facing a
dilemma after a surprising clue appears.

The premise is classical and child-facing: something goes missing or turns up
wrong, the chemist notices a suspicious trail, caution is needed before a hasty
accusation, and the truth is revealed by careful testing.
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

    chemist: object | None = None
    clue: object | None = None
    helper: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "mom"}
        male = {"man", "boy", "father", "dad"}
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
class Harbor:
    name: str = "the harbor"
    places: list[str] = field(default_factory=lambda: ["dock", "pier", "warehouse", "lab", "tugboat"])
    weather: str = "foggy"
    clue_kind: str = "salt"
    caution_level: float = 0.0
    surprise_level: float = 0.0
    harbor: object | None = None
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
class World:
    harbor: Harbor
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        w = World(self.harbor)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Story parameters and registries
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
    helper: str
    suspect: str
    clue: str
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


NAMES_GIRL = ["Mina", "Lina", "Nora", "Ruby", "Iris", "Tessa"]
NAMES_BOY = ["Evan", "Noah", "Milo", "Theo", "Finn", "Owen"]
HELPERS = ["dockhand", "captain", "porter"]
SUSPECTS = ["crate", "lantern", "net", "barrel"]
CLUES = ["salt crystals", "blue powder", "wet footprints", "missing label"]


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    harbor = Harbor()
    world = World(harbor=harbor)

    chemist = world.add(Entity(
        id=params.name,
        kind="character",
        type="woman" if params.gender == "girl" else "man",
        label="the chemist",
        meters={"focus": 1.0, "caution": 0.0, "surprise": 0.0},
        memes={"dilemma": 0.0, "curiosity": 1.0, "trust": 0.5},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="man" if params.helper in {"dockhand", "captain", "porter"} else "person",
        label=f"the {params.helper}",
        meters={"work": 1.0},
        memes={"helpfulness": 1.0},
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="thing",
        type="container",
        label=f"a {params.suspect}",
        phrase=f"a {params.suspect} near the wet planks",
        meters={"stillness": 1.0},
        memes={"suspicion": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="evidence",
        label=params.clue,
        phrase=params.clue,
        meters={"freshness": 1.0},
        memes={"importance": 1.0},
    ))

    world.facts.update(
        chemist=chemist,
        helper=helper,
        suspect=suspect,
        clue=clue,
        harbor=harbor,
    )
    return world


def predict_truth(world: World) -> str:
    clue = _safe_fact(world, world.facts, "clue").label
    if clue == "salt crystals":
        return "sea spray from the tide"
    if clue == "blue powder":
        return "powder from a broken crate label"
    if clue == "wet footprints":
        return "a boatman walking in from the pier"
    return "someone moved the label by mistake"


def increase_surprise(world: World, amount: float) -> None:
    world.harbor.surprise_level += amount
    world.facts["chemist"].memes["surprise"] += amount


def increase_caution(world: World, amount: float) -> None:
    world.harbor.caution_level += amount
    world.facts["chemist"].meters["caution"] += amount


def intro(world: World) -> None:
    c = _safe_fact(world, world.facts, "chemist")
    world.say(
        f"{c.id} was a chemist who worked at the harbor, where fog could hide a lot of small things."
    )
    world.say(
        f"{c.pronoun().capitalize()} liked neat jars, careful notes, and quiet checks before any big guess."
    )


def setup_dilemma(world: World) -> None:
    c = _safe_fact(world, world.facts, "chemist")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    clue = _safe_fact(world, world.facts, "clue")

    world.say(
        f"One morning, {helper.label} called {c.id} to the pier and pointed at {suspect.label}."
    )
    world.say(
        f"Next to it was a surprising sign: {clue.label}."
    )
    increase_surprise(world, 1.0)
    increase_caution(world, 1.0)
    c.memes["dilemma"] += 1.0
    world.say(
        f"{c.id} had a dilemma. {c.pronoun().capitalize()} could point to the {suspect.type} at once, or test the clue first."
    )


def investigate(world: World) -> None:
    c = _safe_fact(world, world.facts, "chemist")
    clue = _safe_fact(world, world.facts, "clue")
    truth = predict_truth(world)

    world.say(
        f"Instead of guessing, {c.id} lifted the {clue.label}, sniffed it, and wrote down the result."
    )
    world.say(
        f"The clue fit the harbor better than it fit a crime: it meant {truth}."
    )
    world.facts["truth"] = truth
    world.facts["dilemma_solved"] = True
    c.memes["dilemma"] = 0.0
    c.meters["focus"] += 1.0
    increase_caution(world, 1.0)


def resolve(world: World) -> None:
    c = _safe_fact(world, world.facts, "chemist")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    truth = _safe_fact(world, world.facts, "truth")

    world.para()
    world.say(
        f"{c.id} smiled and told {helper.label} that the {suspect.type} was not the problem."
    )
    world.say(
        f"The {world.facts['clue'].label} had come from {truth}, so the mystery was only a surprise, not a wrong deed."
    )
    world.say(
        f"Together they cleaned the damp patch, and the harbor felt calm again."
    )


# ---------------------------------------------------------------------------
# Rendering and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit-style story set at a harbor where a chemist faces a dilemma after a surprising clue appears.',
        f"Tell a child-friendly mystery about {f['chemist'].id}, a chemist at the harbor, who sees {f['clue'].label} near {f['suspect'].label} and must decide what to do.",
        "Write a careful detective story for young children with a harbor clue, a cautious test, and a gentle resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = _safe_fact(world, f, "chemist")
    h = _safe_fact(world, f, "helper")
    clue = _safe_fact(world, f, "clue")
    suspect = _safe_fact(world, f, "suspect")
    truth = _safe_fact(world, f, "truth")

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {c.id}, a chemist who worked at the harbor and solved a small mystery carefully.",
        ),
        QAItem(
            question=f"What surprising clue did {c.id} find near {suspect.label}?",
            answer=f"{c.id} found {clue.label} near {suspect.label}. That clue made the case feel surprising and important.",
        ),
        QAItem(
            question=f"What was {c.id}'s dilemma?",
            answer=f"{c.id} had to choose between guessing right away and testing the clue first. {c.id} chose the careful way.",
        ),
        QAItem(
            question=f"What did the clue really mean?",
            answer=f"The clue meant {truth}. It did not mean someone had done something terrible.",
        ),
        QAItem(
            question=f"Who helped at the harbor?",
            answer=f"{h.label} helped by calling {c.id} over and staying nearby while the chemist checked the evidence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chemist do?",
            answer="A chemist studies things by observing them and testing them carefully, often using jars, powders, and simple tools.",
        ),
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a safe place near the water where boats can stop, load, unload, and wait.",
        ),
        QAItem(
            question="Why is caution useful in a mystery?",
            answer="Caution is useful because it helps someone avoid a wrong guess and look at the facts first.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  harbor.caution={world.harbor.caution_level}")
    lines.append(f"  harbor.surprise={world.harbor.surprise_level}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% chemist(C). harbor(H). clue(X). suspect(S). label(X,Name). at(X,Place). clue_kind(X,K).

dilemma(C) :- chemist(C), clue(X), suspicious(X), not tested(X).
surprise(C) :- chemist(C), clue(X), surprising(X).
cautious(C) :- chemist(C), tested(X).
solved(C) :- chemist(C), clue(X), tested(X), explained(X).

suspicious(X) :- clue_kind(X, salt).
suspicious(X) :- clue_kind(X, powder).
surprising(X) :- clue_kind(X, salt).
surprising(X) :- clue_kind(X, footprints).

tested(X) :- clue(X), test_done(X).
explained(X) :- clue(X), truth(X).

#show dilemma/1.
#show surprise/1.
#show cautious/1.
#show solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("chemist", "chemist"))
    lines.append(asp.fact("harbor", "harbor"))
    lines.append(asp.fact("clue", "clue"))
    lines.append(asp.fact("suspect", "suspect"))
    lines.append(asp.fact("clue_kind", "clue", "salt"))
    lines.append(asp.fact("test_done", "clue"))
    lines.append(asp.fact("truth", "clue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show dilemma/1. #show surprise/1. #show cautious/1. #show solved/1."))
    atoms = set((a.name, tuple(sym.name if sym.type != sym.Number else sym.number for sym in a.arguments)) for a in model)
    expected = {("dilemma", ("chemist",)), ("surprise", ("chemist",)), ("cautious", ("chemist",)), ("solved", ("chemist",))}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH in ASP parity.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit harbor story world with a chemist, a surprise clue, and a careful resolution.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    suspect = getattr(args, "suspect", None) or rng.choice(SUSPECTS)
    clue = getattr(args, "clue", None) or rng.choice(CLUES)
    return StoryParams(name=name, gender=gender, helper=helper, suspect=suspect, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    intro(world)
    setup_dilemma(world)
    world.para()
    investigate(world)
    resolve(world)
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
        print(asp_program("#show dilemma/1. #show surprise/1. #show cautious/1. #show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show dilemma/1. #show surprise/1. #show cautious/1. #show solved/1."))
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Mina", gender="girl", helper="dockhand", suspect="crate", clue="salt crystals"),
            StoryParams(name="Evan", gender="boy", helper="captain", suspect="barrel", clue="wet footprints"),
            StoryParams(name="Iris", gender="girl", helper="porter", suspect="lantern", clue="blue powder"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
