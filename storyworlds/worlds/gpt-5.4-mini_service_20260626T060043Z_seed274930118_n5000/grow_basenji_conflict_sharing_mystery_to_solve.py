#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/grow_basenji_conflict_sharing_mystery_to_solve.py
==============================================================================================================================

A heartwarming tiny storyworld about a child, a growing basenji puppy, a small
sharing conflict, and a mystery that gets solved kindly.

Premise:
- A child cares for a basenji puppy that is growing fast.
- The puppy and a sibling/friend want the same cozy thing or treat.
- A mystery arises: who made the little mess or where did the missing item go?
- The answer is found by paying attention, sharing, and noticing the puppy's
  habits.

The domain keeps the story child-facing and concrete:
- physical meters: hunger, tiredness, size, mess, worry, joy
- emotional memes: affection, frustration, curiosity, patience, relief

The simulated state drives the prose: if the basenji grows, the bed becomes too
small; if two characters want the same snack or blanket, a conflict appears; if
the mystery is solved, a warm sharing moment resolves the tension.
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


# ---------------------------------------------------------------------------
# Domain model
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
    kind: str = "thing"   # "character" | "animal" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basenji: object | None = None
    child: object | None = None
    parent: object | None = None
    shared: object | None = None
    sibling: object | None = None
    def __post_init__(self) -> None:
        for k in ("hunger", "tiredness", "size", "mess", "worry", "joy"):
            self.meters.setdefault(k, 0.0)
        for k in ("affection", "frustration", "curiosity", "patience", "relief", "conflict"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                mapping = {"subject": "she", "object": "her", "possessive": "her"}
            elif self.type in {"boy", "father", "man"}:
                mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    child_name: str
    child_type: str
    sibling_name: str
    sibling_type: str
    parent_name: str
    basenji_name: str
    object_name: str
    setting: str
    seed: Optional[int] = None
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


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
    world: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


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


SETTINGS = {
    "backyard": "the backyard",
    "kitchen": "the kitchen",
    "living_room": "the living room",
    "porch": "the porch",
}

CHILD_NAMES = ["Mia", "Niko", "Tessa", "Owen", "Luna", "Eli", "Ruby", "Noah"]
SIBLING_NAMES = ["June", "Max", "Iris", "Ben", "Ada", "Theo"]
PARENT_NAMES = ["Mom", "Dad"]
OBJ_NAMES = ["blanket", "ball", "cookie", "rope toy", "bed", "bowl"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _name_word(name: str) -> str:
    return name


def _poss(name: str) -> str:
    return f"{name}'s"


def _article(noun: str) -> str:
    return "an" if noun[0].lower() in "aeiou" else "a"


def _capitalize_sentence(s: str) -> str:
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        # Basenji grows quickly.
        basenji = world.get("basenji")
        if basenji.meters["size"] < 2 and ("grow",) not in world.fired:
            world.fired.add(("grow",))
            basenji.meters["size"] = 2
            out.append(f"{basenji.label} stretched out and seemed to grow bigger overnight.")

        # If the object is too small for the growing basenji, the conflict rises.
        obj = world.get("shared_object")
        child = world.get("child")
        sibling = world.get("sibling")
        if basenji.meters["size"] >= 2 and obj.type == "bed" and obj.meters["size"] < 1 and ("too_small",) not in world.fired:
            world.fired.add(("too_small",))
            out.append(f"The little bed was not as big as {basenji.label} anymore.")

        # Mystery: missing object / little mess from basenji paws.
        if basenji.meters["mess"] >= 1 and ("mystery",) not in world.fired:
            world.fired.add(("mystery",))
            child.memes["curiosity"] += 1
            sibling.memes["curiosity"] += 1
            out.append(f"Someone had left tiny muddy prints, and that made a mystery to solve.")

        # Conflict if both want the same thing and patience is low.
        if world.facts.get("shared_want") and child.memes["frustration"] < 2 and sibling.memes["frustration"] < 2 and ("conflict",) not in world.fired:
            world.fired.add(("conflict",))
            child.memes["conflict"] += 1
            sibling.memes["conflict"] += 1
            out.append(f"{child.label} and {sibling.label} both reached for the same {obj.label}.")

        # Sharing resolves conflict.
        if child.memes["conflict"] >= 1 and sibling.memes["conflict"] >= 1 and world.facts.get("share_fixed") and ("share",) not in world.fired:
            world.fired.add(("share",))
            child.memes["conflict"] = 0
            sibling.memes["conflict"] = 0
            child.memes["joy"] += 1
            sibling.memes["joy"] += 1
            basenji.memes["affection"] += 1
            out.append(f"They chose to share, and the room felt kinder right away.")
        changed = False
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.setting))

    child = world.add(Entity(id="child", kind="character", label=_name_word(params.child_name), type=params.child_type))
    sibling = world.add(Entity(id="sibling", kind="character", label=_name_word(params.sibling_name), type=params.sibling_type))
    parent = world.add(Entity(id="parent", kind="character", label=params.parent_name, type="mother" if params.parent_name == "Mom" else "father"))
    basenji = world.add(Entity(id="basenji", kind="animal", label=params.basenji_name, type="basenji"))
    shared = world.add(Entity(id="shared_object", kind="thing", label=params.object_name, type=params.object_name, owner="child"))
    shared.meters["size"] = 0.5 if params.object_name in {"bed", "blanket"} else 1.0

    # Setup
    world.say(f"{child.label} had a basenji named {basenji.label}.")
    world.say(f"{basenji.label} was a small basenji, but it seemed to grow bigger every week.")
    world.say(f"{child.label} loved {basenji.label} very much, and {params.parent_name.lower()} watched over both of them.")

    world.para()
    # Conflict / mystery
    world.say(f"One day, {child.label} and {sibling.label} were at {world.place}.")
    if params.object_name == "bed":
        world.say(f"They both wanted the little {shared.label} for {basenji.label} to rest on.")
    elif params.object_name in {"cookie", "bowl"}:
        world.say(f"They both wanted the same {shared.label}, but only one of them could have it first.")
    else:
        world.say(f"They both wanted to use the same {shared.label} at the same time.")
    world.facts["shared_want"] = True
    child.memes["frustration"] += 1
    sibling.memes["frustration"] += 1
    propagate(world)

    world.say(f"Then they noticed tiny muddy prints near the doorway.")
    basenji.meters["mess"] += 1
    propagate(world)

    world.para()
    # Resolution
    world.say(f"{params.parent_name} knelt down and looked at the prints.")
    world.say(f"'{basenji.label} made the mess,' {params.parent_name.lower()} said with a smile.")
    world.say(f"'{It if False else ''}'")
    world.say(f"{child.label} laughed, because the answer was hiding in plain sight.")
    world.say(f"Instead of arguing, {child.label} shared the {shared.label} with {sibling.label}.")
    world.facts["share_fixed"] = True
    propagate(world)
    world.say(f"{basenji.label} curled up nearby, calm and happy, while everyone felt proud of how kindly they solved the problem.")

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        basenji=basenji,
        shared=shared,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a heartwarming story about a growing basenji named {world.facts['basenji'].label} and a child named {p.child_name}.",
        f"Tell a gentle tale where {p.child_name} and {p.sibling_name} must solve a small mystery and learn to share.",
        f"Write a child-friendly story in which a basenji grows, causes a small conflict, and the family finds a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    child = _safe_fact(world, world.facts, "child")
    sibling = _safe_fact(world, world.facts, "sibling")
    basenji = _safe_fact(world, world.facts, "basenji")
    shared = _safe_fact(world, world.facts, "shared")
    return [
        QAItem(
            question=f"Who had the basenji in the story?",
            answer=f"{child.label} had the basenji named {basenji.label}, and {child.label} loved {basenji.label} very much.",
        ),
        QAItem(
            question=f"What was the mystery that needed to be solved?",
            answer=f"The mystery was who made the tiny muddy prints, and the answer was {basenji.label}.",
        ),
        QAItem(
            question=f"How did {child.label} and {sibling.label} fix the conflict?",
            answer=f"They solved it by sharing the {shared.label} instead of arguing about it.",
        ),
        QAItem(
            question=f"What changed about {basenji.label} as time passed?",
            answer=f"{basenji.label} grew bigger, so the little space that once fit well did not seem as cozy anymore.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with everyone feeling warm and happy because the mystery was solved and the children chose to share kindly.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "basenji": (
        "What is a basenji?",
        "A basenji is a small dog breed. Basenjis are lively, clever, and often have lots of energy to play with."
    ),
    "sharing": (
        "Why is sharing helpful?",
        "Sharing helps people take turns, avoid hurt feelings, and enjoy things together."
    ),
    "mystery": (
        "What is a mystery?",
        "A mystery is something that is not known yet, so people look for clues to figure it out."
    ),
    "grow": (
        "What does it mean to grow?",
        "To grow means to get bigger, taller, or stronger over time."
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.
#show solved/4.

valid(C, S, P, O) :- child(C), sibling(S), parent(P), object(O), grows(basenji), shareable(O).
solved(C, S, P, O) :- valid(C, S, P, O), solved_by_sharing(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n))
    for n in SIBLING_NAMES:
        lines.append(asp.fact("sibling_name", n))
    for n in PARENT_NAMES:
        lines.append(asp.fact("parent_name", n))
    for o in OBJ_NAMES:
        lines.append(asp.fact("object_name", o))
    lines.append(asp.fact("grows", "basenji"))
    lines.append(asp.fact("shareable", "blanket"))
    lines.append(asp.fact("shareable", "bed"))
    lines.append(asp.fact("shareable", "cookie"))
    lines.append(asp.fact("solved_by_sharing", "blanket"))
    lines.append(asp.fact("solved_by_sharing", "bed"))
    lines.append(asp.fact("solved_by_sharing", "cookie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python = set(valid_combos())
    clingo = set(asp_valid())
    if python == clingo:
        print(f"OK: ASP and Python agree on {len(python)} valid combos.")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(python - clingo))
    print("asp only:", sorted(clingo - python))
    return 1


# ---------------------------------------------------------------------------
# Validity / selection
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for child in CHILD_NAMES:
        for sibling in SIBLING_NAMES:
            for parent in PARENT_NAMES:
                for obj in OBJ_NAMES:
                    combos.append((child, sibling, parent, obj))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming basenji storyworld.")
    ap.add_argument("--name", dest="child_name", choices=CHILD_NAMES)
    ap.add_argument("--sibling", dest="sibling_name", choices=SIBLING_NAMES)
    ap.add_argument("--parent", dest="parent_name", choices=PARENT_NAMES)
    ap.add_argument("--object", dest="object_name", choices=OBJ_NAMES)
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    sibling_name = getattr(args, "sibling_name", None) or rng.choice(SIBLING_NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    object_name = getattr(args, "object_name", None) or rng.choice(OBJ_NAMES)
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    child_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    sibling_type = "boy" if child_type == "girl" and rng.random() < 0.5 else "girl"
    if child_name == sibling_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=child_name,
        child_type=child_type,
        sibling_name=sibling_name,
        sibling_type=sibling_type,
        parent_name=parent_name,
        basenji_name=rng.choice(["Biscuit", "Tango", "Mochi", "Pepper", "Sunny"]),
        object_name=object_name,
        setting=setting,
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {e.label:10} {' '.join(bits)}")
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
        print(asp_program("#show valid/4.\n#show solved/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid()
        print(f"{len(combos)} ASP-valid combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for child in CHILD_NAMES[:3]:
            params = StoryParams(
                child_name=child,
                child_type="girl" if CHILD_NAMES.index(child) % 2 == 0 else "boy",
                sibling_name=_safe_lookup(SIBLING_NAMES, CHILD_NAMES.index(child) % len(SIBLING_NAMES)),
                sibling_type="boy",
                parent_name=_safe_lookup(PARENT_NAMES, CHILD_NAMES.index(child) % 2),
                basenji_name=["Biscuit", "Tango", "Mochi"][CHILD_NAMES.index(child) % 3],
                object_name=_safe_lookup(OBJ_NAMES, CHILD_NAMES.index(child) % len(OBJ_NAMES)),
                setting=list(SETTINGS)[CHILD_NAMES.index(child) % len(SETTINGS)],
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
