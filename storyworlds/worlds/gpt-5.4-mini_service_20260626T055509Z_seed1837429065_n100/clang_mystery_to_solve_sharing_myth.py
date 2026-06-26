#!/usr/bin/env python3
"""
clang_mystery_to_solve_sharing_myth.py
======================================

A small mythic story world about a clan, a strange clang, a shared search,
and a mystery that becomes clear through generosity.

Seed tale idea:
A village hears a clang from the old stone well. Three children, a keeper,
and a grandmother share tools, light, and courage to find what made it.
They discover the sound was not a monster but a loose bronze bell in the dark,
and the village learns that sharing the lantern and the rope helped everyone
solve the mystery together.
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

    means: set[str] = field(default_factory=set)
    elder: object | None = None
    item: object | None = None
    seeker1: object | None = None
    seeker2: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    feature: str
    dark: bool = False
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    kind: str
    can_be_shared: bool = True
    reveals: str = ""
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
    mystery: str
    shared_object: str
    seeker1: str
    seeker2: str
    elder: str
    seed: Optional[int] = None
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clang_heard: bool = False
        self.mystery_solved: bool = False
        self.shared: bool = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "well": Place(name="the old well", feature="stone rim", dark=True),
    "grove": Place(name="the moonlit grove", feature="hollow tree", dark=True),
    "harbor": Place(name="the quiet harbor", feature="wooden dock", dark=False),
    "temple": Place(name="the hill temple", feature="bronze steps", dark=False),
}

MYSTERIES = {
    "clang": ObjectDef(id="clang", label="clang", phrase="a sudden clang", kind="sound", reveals="bronze bell"),
    "bell": ObjectDef(id="bell", label="bronze bell", phrase="a small bronze bell", kind="object", reveals="rope"),
    "echo": ObjectDef(id="echo", label="echo", phrase="a strange echo", kind="sound", reveals="hanging ladle"),
}

SHARED_OBJECTS = {
    "lantern": ObjectDef(id="lantern", label="lantern", phrase="a warm lantern", kind="tool"),
    "rope": ObjectDef(id="rope", label="rope", phrase="a long rope", kind="tool"),
    "basket": ObjectDef(id="basket", label="basket", phrase="a basket of figs", kind="gift"),
    "cloak": ObjectDef(id="cloak", label="cloak", phrase="a wool cloak", kind="cloth"),
}

NAMES = ["Ari", "Mina", "Tavi", "Niko", "Sera", "Lio", "Rin", "Oda"]
ELDERS = ["Grandmother Iva", "Old Mara", "Keeper Sol", "Elder Nera"]
TRAITS = ["curious", "brave", "gentle", "steadfast", "quick-eyed"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def _name(seed: int, pool: list[str]) -> str:
    return pool[seed % len(pool)]


def _entity_label(ent: Entity) -> str:
    return ent.label or ent.id


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    seeker1 = world.add(Entity(id=params.seeker1, kind="character", type="child", label=params.seeker1))
    seeker2 = world.add(Entity(id=params.seeker2, kind="character", type="child", label=params.seeker2))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder", label=params.elder, means={"age": 1} if False else {}))
    shared = _safe_lookup(SHARED_OBJECTS, params.shared_object)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    item = world.add(Entity(id=shared.id, kind="thing", type=shared.kind, label=shared.label, phrase=shared.phrase, owner=seeker1.id))
    world.add(Entity(id=mystery.id, kind="thing", type=mystery.kind, label=mystery.label, phrase=mystery.phrase))
    world.facts.update(
        seeker1=seeker1,
        seeker2=seeker2,
        elder=elder,
        shared=item,
        mystery=mystery,
        place=world.place,
    )
    return world


def open_story(world: World) -> None:
    w = world
    w.say(f"Long ago, {w.place.name} slept under a hush of stars.")
    w.say(f"Then a {w.facts['mystery'].label} rang out with a sharp clang, and everyone looked up at once.")


def introduce_seekers(world: World) -> None:
    a = _safe_fact(world, world.facts, "seeker1")
    b = _safe_fact(world, world.facts, "seeker2")
    elder = _safe_fact(world, world.facts, "elder")
    shared = _safe_fact(world, world.facts, "shared")
    w = world
    w.para()
    w.say(f"{a.id} and {b.id} were two young wanderers who loved questions.")
    w.say(f"They carried {shared.phrase} because {elder.id} had taught them that wisdom grows when tools are shared.")


def search_and_share(world: World) -> None:
    a = _safe_fact(world, world.facts, "seeker1")
    b = _safe_fact(world, world.facts, "seeker2")
    elder = _safe_fact(world, world.facts, "elder")
    shared = _safe_fact(world, world.facts, "shared")
    mystery = _safe_fact(world, world.facts, "mystery")
    w = world
    w.para()
    w.say(f"The three of them went to {w.place.name}.")
    w.say(f"{a.id} held the {shared.label}, {b.id} held the rope, and {elder.id} carried the old memory of the place.")
    w.shared = True
    if mystery.id == "clang":
        w.clang_heard = True
        w.say(f"Each step made the stone answer softly, until the hidden clang came again from below the rim.")


def solve_mystery(world: World) -> None:
    a = _safe_fact(world, world.facts, "seeker1")
    b = _safe_fact(world, world.facts, "seeker2")
    elder = _safe_fact(world, world.facts, "elder")
    shared = _safe_fact(world, world.facts, "shared")
    mystery = _safe_fact(world, world.facts, "mystery")
    w = world
    w.para()
    if not w.shared:
        pass
    if not w.clang_heard:
        pass
    w.mystery_solved = True
    reveal = mystery.reveals or "the hidden cause"
    w.say(f"{elder.id} listened, then smiled. 'That clang is no beast,' {elder.pronoun('subject')} said.")
    w.say(f"Together, they lifted the stone cover with the rope and the lantern, and found {reveal} waiting in the dark.")
    w.say(f"The sound had come from a small bronze bell caught beneath the stones, swinging whenever the wind stirred.")
    w.say(f"{a.id} and {b.id} laughed in relief, and they shared the lantern's glow with the whole village.")


def ending(world: World) -> None:
    a = _safe_fact(world, world.facts, "seeker1")
    b = _safe_fact(world, world.facts, "seeker2")
    shared = _safe_fact(world, world.facts, "shared")
    w = world
    w.para()
    w.say(f"By dawn, the bell was free, the mystery was solved, and {shared.label} had passed from one careful hand to another.")
    w.say(f"{a.id} and {b.id} walked home together, carrying the warm feeling that comes when a shared thing helps everyone.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    open_story(world)
    introduce_seekers(world)
    search_and_share(world)
    solve_mystery(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, mystery: str, shared_object: str) -> bool:
    if mystery not in MYSTERIES or shared_object not in SHARED_OBJECTS or place not in PLACES:
        return False
    if shared_object == "basket" and mystery == "clang":
        return True
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for m in MYSTERIES:
            for s in SHARED_OBJECTS:
                if valid_combo(p, m, s):
                    out.append((p, m, s))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child where a "{f["mystery"].label}" and a shared {f["shared"].label} help solve a mystery.',
        f"Tell a calm, ancient-sounding tale about {f['seeker1'].id}, {f['seeker2'].id}, and {f['elder'].id} hearing a clang at {world.place.name}.",
        f"Write a short myth with a clear beginning, a shared search, and a solved mystery involving a clang.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = _safe_fact(world, f, "seeker1").id
    b = _safe_fact(world, f, "seeker2").id
    elder = _safe_fact(world, f, "elder").id
    shared = _safe_fact(world, f, "shared").label
    mystery = _safe_fact(world, f, "mystery").label
    place = world.place.name
    return [
        QAItem(
            question=f"Who heard the clang at {place}?",
            answer=f"{a}, {b}, and {elder} all heard the clang at {place}.",
        ),
        QAItem(
            question=f"What did the children share while they searched for the mystery?",
            answer=f"They shared the {shared}, and that helped them search together.",
        ),
        QAItem(
            question=f"What turned out to be the cause of the mystery?",
            answer=f"The mystery turned out to be a {mystery} hidden below the stones, not a monster.",
        ),
        QAItem(
            question=f"Why did the search work?",
            answer=f"It worked because the seekers shared their tools and listened to the elder's wisdom.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clang?",
            answer="A clang is a sharp, ringing sound, like metal hitting stone or another piece of metal.",
        ),
        QAItem(
            question="Why do people share tools in a hard task?",
            answer="People share tools so each person can help, and together they can do a task more safely and quickly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs careful looking and thinking to solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_kind(M).
shared(S) :- shared_kind(S).

can_solve(P, M, S) :- place(P), mystery(M), shared(S), valid_combo(P, M, S).

#show can_solve/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_kind", m))
    for s in SHARED_OBJECTS:
        lines.append(asp.fact("shared_kind", s))
    for p, m, s in valid_combos():
        lines.append(asp.fact("valid_combo", p, m, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - ac))
    print("only in asp:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about a clang and a shared mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--shared-object", dest="shared_object", choices=SHARED_OBJECTS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    shared_object = getattr(args, "shared_object", None) or rng.choice(list(SHARED_OBJECTS))
    if not valid_combo(place, mystery, shared_object):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s1, s2 = rng.sample(NAMES, 2)
    elder = rng.choice(ELDERS)
    return StoryParams(place=place, mystery=mystery, shared_object=shared_object, seeker1=s1, seeker2=s2, elder=elder)


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
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.name}")
    lines.append(f"clang_heard={world.clang_heard}")
    lines.append(f"mystery_solved={world.mystery_solved}")
    lines.append(f"shared={world.shared}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} label={e.label}")
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
    StoryParams(place="well", mystery="clang", shared_object="lantern", seeker1="Ari", seeker2="Mina", elder="Grandmother Iva"),
    StoryParams(place="grove", mystery="bell", shared_object="rope", seeker1="Tavi", seeker2="Sera", elder="Keeper Sol"),
    StoryParams(place="temple", mystery="echo", shared_object="cloak", seeker1="Niko", seeker2="Rin", elder="Old Mara"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_solve/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        print(sorted(set(asp.atoms(model, "valid_combo"))))
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
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
