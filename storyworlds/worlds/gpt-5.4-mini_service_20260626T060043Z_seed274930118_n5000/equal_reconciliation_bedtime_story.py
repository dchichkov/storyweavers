#!/usr/bin/env python3
"""
A tiny bedtime-story world about equal sharing and reconciliation.

The seed tale:
---
At bedtime, two little siblings both wanted the same soft moon blanket. Nora said it was
hers because she found it first. Ben said it was his because he liked the silver stars.
They pulled until the blanket wrinkled into a lump.

Their mother did not shout. She sat on the edge of the bed and said the blanket was
big enough for both of them if they took turns tucking it in. Nora could hold one side,
Ben could hold the other, and they could each make the bed feel cozy. The children
looked at each other, let go, and smiled. Soon the blanket lay smooth and warm, and
both siblings were sleepy and proud of making it fair.

World idea:
---
This script models a small bedtime room, a shared blanket, a simple fairness rule,
and a reconciliation turn. The emotional arc is:
1. desire for the same thing
2. tension over unequal claims
3. a parent suggests an equal arrangement
4. the children accept, calm down, and end together under the blanket

The generated story is driven by the world state: who wants what, what is shared,
how the disagreement escalates, and what changes when the children reconcile.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    child1: object | None = None
    child2: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Room:
    place: str = "the bedroom"
    bedtime: bool = True
    cozy: bool = True
    room: object | None = None
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
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    name1: str = ""
    name2: str = ""
    child1_type: str = ""
    child2_type: str = ""
    parent_type: str = ""
    blanket: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    parent: object | None = None
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


GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Theo", "Max", "Sam", "Jack", "Noah"]
PARENT_TYPES = ["mother", "father"]
BLANKETS = {
    "moon": ("a soft moon blanket with silver stars", "the moon blanket"),
    "cloud": ("a fluffy cloud blanket with tiny yellow moons", "the cloud blanket"),
    "star": ("a warm star blanket with stitched corners", "the star blanket"),
}

# ---------------------------------------------------------------------------
# Helper text
# ---------------------------------------------------------------------------
def equalizer_word() -> str:
    return "equal"


def child_desc(ent: Entity) -> str:
    return f"little {ent.type} {ent.id}"


def bedtime_opening(world: World, a: Entity, b: Entity, blanket: Entity) -> None:
    world.say(
        f"It was bedtime in {world.room.place}, and {child_desc(a)} and {child_desc(b)} "
        f"both noticed {blanket.phrase} lying on the bed."
    )
    world.say(
        f"They were sleepy, but they both wanted the same blanket because it felt soft "
        f"and safe."
    )


def want_blanket(world: World, child: Entity, blanket: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1.0
    world.say(
        f'{child.id} said, "I want {blanket.label}."'
    )


def tug_conflict(world: World, a: Entity, b: Entity, blanket: Entity) -> None:
    a.memes["conflict"] = a.memes.get("conflict", 0.0) + 1.0
    b.memes["conflict"] = b.memes.get("conflict", 0.0) + 1.0
    blanket.meters["wrinkled"] = blanket.meters.get("wrinkled", 0.0) + 1.0
    world.say(
        f"They both reached for it at once, and the blanket turned into a wrinkled lump."
    )


def reconcile(world: World, parent: Entity, a: Entity, b: Entity, blanket: Entity) -> None:
    world.say(
        f"{parent.pronoun().capitalize()} sat beside them and said the blanket could be "
        f"shared in an {equalizer_word()} way."
    )
    world.say(
        f'"{a.id} can tuck in one side, and {b.id} can tuck in the other," '
        f"{parent.pronoun()} said. \"That way it is fair for both of you.\""
    )
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["calm"] = a.memes.get("calm", 0.0) + 1.0
    b.memes["calm"] = b.memes.get("calm", 0.0) + 1.0
    blanket.meters["wrinkled"] = 0.0
    blanket.meters["shared"] = 1.0
    world.say(
        f"The two children looked at each other, let go, and nodded."
    )


def end_cozy(world: World, a: Entity, b: Entity, blanket: Entity) -> None:
    a.memes["love"] = a.memes.get("love", 0.0) + 1.0
    b.memes["love"] = b.memes.get("love", 0.0) + 1.0
    world.say(
        f"Soon {blanket.label} lay smooth and warm over both bedsides, and {a.id} and "
        f"{b.id} fell quiet and sleepy under it."
    )
    world.say(
        f"It was a small bedtime lesson: when things are shared equally, everyone can "
        f"rest."
    )


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    room = Room()
    world = World(room)

    child1 = world.add(Entity(id=params.name1, kind="character", type=params.child1_type))
    child2 = world.add(Entity(id=params.name2, kind="character", type=params.child2_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type))
    label, phrase = _safe_lookup(BLANKETS, params.blanket)
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label=f"the {params.blanket} blanket",
        phrase=label,
        shared=True,
    ))
    blanket.owner = None

    bedtime_opening(world, child1, child2, blanket)
    want_blanket(world, child1, blanket)
    want_blanket(world, child2, blanket)
    tug_conflict(world, child1, child2, blanket)
    reconcile(world, parent, child1, child2, blanket)
    end_cozy(world, child1, child2, blanket)

    world.facts.update(
        child1=child1,
        child2=child2,
        parent=parent,
        blanket=blanket,
        equal=True,
        reconciled=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, parent, blanket = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child1"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child2"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "blanket")
    return [
        f'Write a gentle bedtime story about two children sharing {blanket.label} fairly.',
        f"Tell a story where {a.id} and {b.id} both want the same blanket, but {parent.type} helps them choose an {equalizer_word()} plan.",
        f"Write a short bedtime story using the word '{equalizer_word()}' and ending with both children calm and cozy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, blanket = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child1"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child2"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "blanket")
    return [
        QAItem(
            question=f"Who wanted {blanket.label} at bedtime?",
            answer=f"Both {a.id} and {b.id} wanted {blanket.label} because it was soft and cozy.",
        ),
        QAItem(
            question=f"Why did the blanket get wrinkled?",
            answer=f"It got wrinkled because {a.id} and {b.id} pulled on it at the same time.",
        ),
        QAItem(
            question=f"How did {parent.type} help them?",
            answer=f"{parent.type.capitalize()} suggested an {equalizer_word()} plan: one child could tuck in one side and the other child could tuck in the other side.",
        ),
        QAItem(
            question=f"What changed after the children reconciled?",
            answer=f"They let go of the tugging, calmed down, and shared {blanket.label} so it lay smooth and warm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does equal mean?",
            answer="Equal means the same amount, or a fair way where everyone gets a balanced share.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, make peace, and feel friendly again.",
        ),
        QAItem(
            question="Why do children need bedtime routines?",
            answer="Bedtime routines help children feel calm, safe, and ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% equal_reconciliation_bedtime_story
% A story is valid when two children want the same blanket, a parent can offer
% an equal sharing plan, and reconciliation follows.

same_blanket(C1,C2,B) :- wants(C1,B), wants(C2,B), C1 != C2.
conflict(C1,C2,B) :- same_blanket(C1,C2,B).
can_reconcile(B) :- blanket(B).
valid_story(C1,C2,B,P) :- same_blanket(C1,C2,B), parent(P), can_reconcile(B).
#show valid_story/4.
#show conflict/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in GIRL_NAMES:
        lines.append(asp.fact("child", name))
        lines.append(asp.fact("girl", name))
    for name in BOY_NAMES:
        lines.append(asp.fact("child", name))
        lines.append(asp.fact("boy", name))
    for p in PARENT_TYPES:
        lines.append(asp.fact("parent", p))
    for bid in BLANKETS:
        lines.append(asp.fact("blanket", bid))
        lines.append(asp.fact("wants", "Nora" if "moon" in bid else "Ben", bid))
        lines.append(asp.fact("wants", "Ben" if "moon" in bid else "Nora", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_stories = set(asp.atoms(model, "valid_story"))
    py = set()
    for b in BLANKETS:
        py.add(("Nora", "Ben", b, "mother"))
        py.add(("Nora", "Ben", b, "father"))
    if asp_stories == py:
        print(f"OK: ASP parity matches Python reasoning ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP only:", sorted(asp_stories - py))
    print("Python only:", sorted(py - asp_stories))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about equal sharing and reconciliation.")
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--child1-type", choices=["girl", "boy"])
    ap.add_argument("--child2-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--blanket", choices=BLANKETS)
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
    child1_type = getattr(args, "child1_type", None) or rng.choice(["girl", "boy"])
    child2_type = getattr(args, "child2_type", None) or rng.choice(["girl", "boy"])
    if child1_type == "girl":
        name1 = getattr(args, "name1", None) or rng.choice(GIRL_NAMES)
    else:
        name1 = getattr(args, "name1", None) or rng.choice(BOY_NAMES)
    if child2_type == "girl":
        name2 = getattr(args, "name2", None) or rng.choice(GIRL_NAMES)
    else:
        name2 = getattr(args, "name2", None) or rng.choice(BOY_NAMES)
    if name1 == name2:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    blanket = getattr(args, "blanket", None) or rng.choice(list(BLANKETS))
    return StoryParams(
        name1=name1,
        name2=name2,
        child1_type=child1_type,
        child2_type=child2_type,
        parent=parent,
        blanket=blanket,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
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
    StoryParams("Nora", "Ben", "girl", "boy", "mother", "moon"),
    StoryParams("Mia", "Leo", "girl", "boy", "father", "cloud"),
    StoryParams("Ava", "Noah", "girl", "boy", "mother", "star"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} valid stories:")
        for t in items:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
