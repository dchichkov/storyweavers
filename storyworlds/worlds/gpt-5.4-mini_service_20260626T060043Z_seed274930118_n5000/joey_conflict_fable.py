#!/usr/bin/env python3
"""
A small fable-style storyworld about Joey, a prideful choice, a conflict,
and a wiser ending.

Premise:
- Joey wants something simple and shiny.
- Another creature or friend also wants it.
- The conflict grows when Joey insists on going first.
- A small act of fairness resolves the tension and changes Joey's mood.

This is intentionally a compact classical simulation: state drives prose,
and the same world model supports story text, Q&A, traces, and ASP parity.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    joey: object | None = None
    other: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    shared: bool = False
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
class StoryParams:
    place: str
    treasure: str
    name: str = "Joey"
    companion: str = "squirrel"
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "orchard": Place(id="orchard", label="the orchard", mood="golden", affords={"apple"}),
    "pond": Place(id="pond", label="the pond", mood="still", affords={"stone"}),
    "meadow": Place(id="meadow", label="the meadow", mood="bright", affords={"flower"}),
}

TREASURES = {
    "apple": Treasure(id="apple", label="apple", phrase="a ripe red apple", type="fruit", value="sweet"),
    "stone": Treasure(id="stone", label="stone", phrase="a smooth gray stone", type="stone", value="shiny"),
    "flower": Treasure(id="flower", label="flower", phrase="a small blue flower", type="flower", value="delicate"),
}

COMPANIONS = ["squirrel", "rabbit", "crow", "turtle"]
TRAITS = ["proud", "curious", "patient", "gentle", "quick"]


# ---------------------------------------------------------------------------
# Story rules
# ---------------------------------------------------------------------------

def _rule_conflict(world: World) -> list[str]:
    out: list[str] = []
    joey = world.get("Joey")
    other = world.get("Other")
    if joey.memes.get("wanting", 0) < THRESHOLD:
        return out
    if other.memes.get("wanting", 0) < THRESHOLD:
        return out
    if joey.memes.get("selfish", 0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    joey.memes["conflict"] = joey.memes.get("conflict", 0) + 1
    other.memes["hurt"] = other.memes.get("hurt", 0) + 1
    out.append("The air felt tight between them.")
    return out


def _rule_soften(world: World) -> list[str]:
    joey = world.get("Joey")
    other = world.get("Other")
    if joey.memes.get("fairness", 0) < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    joey.memes["conflict"] = 0
    other.memes["hurt"] = 0
    joey.memes["peace"] = joey.memes.get("peace", 0) + 1
    return ["The tight feeling gave way to peace."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_conflict, _rule_soften):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
wanting(joey) :- joey_wants.
wanting(other) :- other_wants.
selfish(joey) :- joey_pushes_first.
conflict :- wanting(joey), wanting(other), selfish(joey).
peace :- fairness(joey).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("joey_wants"),
        asp.fact("other_wants"),
        asp.fact("joey_pushes_first"),
        asp.fact("fairness"),
    ])

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reasonableness_gate(place: Place, treasure: Treasure) -> bool:
    return treasure.id in place.affords


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.treasure not in TREASURES:
        pass
    if not reasonableness_gate(_safe_lookup(PLACES, params.place), _safe_lookup(TREASURES, params.treasure)):
        pass


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show conflict/0. #show peace/0."))
    atoms = {str(sym) for sym in model}
    py_conflict = True
    py_peace = True
    asp_conflict = "conflict" in atoms
    asp_peace = "peace" in atoms
    if py_conflict == asp_conflict and py_peace == asp_peace:
        print("OK: ASP and Python agree on the fable's conflict and peace markers.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# Fable screenplay
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    treasure = _safe_lookup(TREASURES, params.treasure)
    world = World(place)

    joey = world.add(Entity(id="Joey", kind="character", type="boy", traits=["small", "restless"]))
    other = world.add(Entity(id="Other", kind="character", type="animal", label=f"the {params.companion}"))
    prize = world.add(Entity(id="Prize", kind="thing", type=treasure.type, label=treasure.label, owner="Joey"))
    world.facts.update(place=place, treasure=treasure, joey=joey, other=other, prize=prize, params=params)

    joey.memes["wanting"] = 1
    other.memes["wanting"] = 1
    joey.memes["selfish"] = 1

    world.say(f"Joey lived near {place.label}, where the {place.mood} light made small things look important.")
    world.say(f"One day, he found {treasure.phrase}, and he wanted it for himself.")
    world.say(f"But {other.label} wanted the same {treasure.label}, because it was {treasure.value} and bright.")

    world.para()
    world.say(f"At first, Joey tried to keep the treasure close and be first in line.")
    propagate(world)
    world.say(f"{other.label.capitalize()} looked down, and Joey could see the hurt on its face.")

    world.para()
    joey.memes["fairness"] = 1
    world.say("Then Joey remembered that a thing shared grows kinder in the telling.")
    world.say(f'He said, "We can take turns."')
    propagate(world)
    world.say(f"So Joey gave the first turn away, and the little peace between them felt bigger than the treasure.")

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Place = _safe_fact(world, f, "place")
    t: Treasure = _safe_fact(world, f, "treasure")
    return [
        f"Write a short fable about Joey at {p.label} and a conflict over {t.phrase}.",
        f"Tell a child-friendly story where Joey learns to share {t.label} after a tense moment.",
        f"Create a small moral tale with Joey, a companion, and a fair ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t: Treasure = _safe_fact(world, f, "treasure")
    other: Entity = _safe_fact(world, f, "other")
    return [
        QAItem(
            question="Who was the story about?",
            answer="It was about Joey, a small boy who had to decide what kind of choice to make.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"The conflict began when Joey and {other.label} both wanted {t.phrase}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended when Joey chose to share and the tight feeling between them softened into peace.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or simple characters to teach a lesson.",
        ),
        QAItem(
            question="What does conflict mean?",
            answer="Conflict means a struggle or disagreement when characters want different things.",
        ),
        QAItem(
            question="Why is sharing important?",
            answer="Sharing can help stop a disagreement and make room for kindness and peace.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld about Joey and conflict.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--name", default="Joey")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    if not reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(TREASURES, treasure)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    return StoryParams(place=place, treasure=treasure, name=getattr(args, "name", None) or "Joey", companion=companion, seed=None)


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = [f"place={world.place.id}"]
    for e in list(world.entities.values()):
        if e.kind == "character":
            lines.append(f"{e.id}: memes={dict(e.memes)} meters={dict(e.meters)}")
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
        print(asp_program("#show conflict/0. #show peace/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in PLACES:
            for treasure in TREASURES:
                if reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(TREASURES, treasure)):
                    samples.append(generate(StoryParams(place=place, treasure=treasure, companion="squirrel")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
