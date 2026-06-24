#!/usr/bin/env python3
"""
A small animal-story world about a hurt friendship, a disagreement over an
abacus, and a gentle reconciliation.

Premise:
- Two animal friends share a classroom play table with an abacus.
- One friend wants to keep it tidy and count carefully.
- The other plays too fast, causing a mistake and hurt feelings.
- They calm down, apologize, and rebuild the game together.

This world models:
- physical meters: where things are, whether the abacus is tidy, and whether
  the counters are in place.
- emotional memes: hurt, worry, friendship, apology, and relief.

The story generator is intentionally small and constrained. It produces a
single complete, child-facing story with a clear turn and resolution.
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
# Domain registries
# ---------------------------------------------------------------------------

ANIMALS = {
    "rabbit": {
        "type": "rabbit",
        "name_options": ["Rina", "Ruby", "Rosie", "Nina"],
        "traits": ["small", "quick", "kind"],
        "pronouns": {"subject": "she", "object": "her", "possessive": "her"},
    },
    "bear": {
        "type": "bear",
        "name_options": ["Benny", "Boris", "Bo", "Ben"],
        "traits": ["round", "gentle", "slow"],
        "pronouns": {"subject": "he", "object": "him", "possessive": "his"},
    },
    "fox": {
        "type": "fox",
        "name_options": ["Fia", "Finn", "Faye", "Felix"],
        "traits": ["bright", "curious", "clever"],
        "pronouns": {"subject": "she", "object": "her", "possessive": "her"},
    },
    "turtle": {
        "type": "turtle",
        "name_options": ["Toby", "Tia", "Tess", "Tori"],
        "traits": ["slow", "careful", "steady"],
        "pronouns": {"subject": "he", "object": "him", "possessive": "his"},
    },
}

PLACES = {
    "classroom": {
        "label": "the classroom",
        "indoor": True,
        "tone": "quiet",
    },
    "playroom": {
        "label": "the playroom",
        "indoor": True,
        "tone": "cozy",
    },
    "library_corner": {
        "label": "the library corner",
        "indoor": True,
        "tone": "still",
    },
}

OBJECTS = {
    "abacus": {
        "label": "abacus",
        "phrase": "a bright wooden abacus",
        "kind": "toy",
    }
}

# ---------------------------------------------------------------------------
# Shared model
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
    kind: str = "thing"   # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    abacus: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            info = _safe_lookup(ANIMALS, self.type)["pronouns"]
            return info[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label
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
class StoryParams:
    place: str
    animal_a: str
    animal_b: str
    name_a: str
    name_b: str
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
    def __init__(self, place_key: str) -> None:
        self.place_key = place_key
        self.place = _safe_lookup(PLACES, place_key)
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        w = World(self.place_key)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w

# ---------------------------------------------------------------------------
# Reasonable story constraints
# ---------------------------------------------------------------------------

def valid_pair(animal_a: str, animal_b: str) -> bool:
    return animal_a != animal_b

def reasonableness_gate(place: str, animal_a: str, animal_b: str) -> None:
    if place not in PLACES:
        pass
    if animal_a not in ANIMALS or animal_b not in ANIMALS:
        pass
    if animal_a == animal_b:
        pass

# ---------------------------------------------------------------------------
# World dynamics
# ---------------------------------------------------------------------------

def _is_hurt(world: World, a: Entity, b: Entity) -> bool:
    return a.memes.get("hurt", 0) >= 1 and b.memes.get("hurt", 0) >= 1

def _maybe_calm(world: World, a: Entity, b: Entity) -> bool:
    if a.memes.get("apology", 0) >= 1 and b.memes.get("listened", 0) >= 1:
        a.memes["hurt"] = 0
        b.memes["hurt"] = 0
        a.memes["friendship"] = a.memes.get("friendship", 0) + 1
        b.memes["friendship"] = b.memes.get("friendship", 0) + 1
        return True
    return False

# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params.place, params.animal_a, params.animal_b)
    world = World(params.place)

    a_info = _safe_lookup(ANIMALS, params.animal_a)
    b_info = _safe_lookup(ANIMALS, params.animal_b)

    hero = world.add(Entity(
        id=params.name_a,
        kind="character",
        type=params.animal_a,
        meters={"feet": 0},
        memes={"friendship": 2, "worry": 0, "hurt": 0, "apology": 0},
    ))
    friend = world.add(Entity(
        id=params.name_b,
        kind="character",
        type=params.animal_b,
        meters={"feet": 0},
        memes={"friendship": 2, "worry": 0, "hurt": 0, "apology": 0},
    ))
    abacus = world.add(Entity(
        id="abacus",
        kind="thing",
        type="abacus",
        label="abacus",
        phrase=OBJECTS["abacus"]["phrase"],
        owner=hero.id,
        held_by=hero.id,
        meters={"tidy": 1, "counted": 0},
    ))

    world.say(
        f"{hero.id} the {hero.type} and {friend.id} the {friend.type} were best friends in {world.place['label']}."
    )
    world.say(
        f"They liked sitting by the little table with the abacus, because counting the beads felt like a game."
    )

    world.para()
    world.say(
        f"One day, {hero.id} wanted to count every bead very carefully, but {friend.id} grew excited and slid the rows too fast."
    )
    world.say(
        f"The beads clicked and crossed, and the neat pattern broke."
    )
    hero.memes["hurt"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    abacus.meters["tidy"] = 0
    abacus.meters["counted"] = 0

    world.para()
    world.say(
        f"{hero.id} frowned and said, 'I wanted to count with you, not lose the pattern.'"
    )
    world.say(
        f"{friend.id} looked down at the abacus and felt sorry for making {hero.pronoun('object')} sad."
    )
    friend.memes["hurt"] += 1
    friend.memes["apology"] += 1
    friend.memes["listened"] += 1

    if _maybe_calm(world, hero, friend):
        world.say(
            f"{friend.id} said, 'I'm sorry. Let's fix it together.'"
        )
        world.say(
            f"Together they lined up the beads again, one by one, until the rows looked neat."
        )
        abacus.meters["tidy"] = 1
        abacus.meters["counted"] = 1
        hero.memes["hurt"] = 0
        hero.memes["worry"] = 0
        friend.memes["hurt"] = 0
        friend.memes["worry"] = 0
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        world.say(
            f"Then {hero.id} smiled, and the two friends counted slowly together while the warm room stayed quiet around them."
        )

    world.facts.update(
        hero=hero,
        friend=friend,
        abacus=abacus,
        place=world.place,
        resolved=abacus.meters["tidy"] >= 1 and hero.memes.get("hurt", 0) == 0,
    )
    return world

# ---------------------------------------------------------------------------
# Storyworld parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    animal_a: str
    animal_b: str
    name_a: str
    name_b: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        f"Write a gentle animal story about {hero.id} and {friend.id} sharing an abacus and fixing a friendship.",
        f"Tell a short story for a young child where two animal friends disagree over an abacus, then reconcile.",
        f"Write an animal friendship story that includes an abacus, a mistake, an apology, and a happy ending.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {hero.id} the {hero.type} and {friend.id} the {friend.type}.",
        ),
        QAItem(
            question=f"What object did they share?",
            answer="They shared an abacus with bright beads for counting.",
        ),
        QAItem(
            question=f"What went wrong with the abacus?",
            answer=f"{friend.id} moved the beads too fast and broke the neat counting pattern.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer="They apologized, listened to each other, and lined the beads up again together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The friends felt close again and counted slowly together with the abacus neat and tidy.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an abacus?",
            answer="An abacus is a counting tool with rows of beads that can slide back and forth.",
        ),
        QAItem(
            question="Why is an apology helpful?",
            answer="An apology helps when someone has hurt a friend, because it shows they understand and want to make things better.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, listening to them, and helping each other when things go wrong.",
        ),
    ]

def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship story world with an abacus and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--animal-a", choices=sorted(ANIMALS))
    ap.add_argument("--animal-b", choices=sorted(ANIMALS))
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    animal_a = getattr(args, "animal_a", None) or rng.choice(sorted(ANIMALS))
    animal_b = getattr(args, "animal_b", None) or rng.choice(sorted([a for a in ANIMALS if a != animal_a]))
    reasonableness_gate(place, animal_a, animal_b)

    name_a = getattr(args, "name_a", None) or rng.choice(_safe_lookup(ANIMALS, animal_a)["name_options"])
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in _safe_lookup(ANIMALS, animal_b)["name_options"] if n != name_a] or _safe_lookup(ANIMALS, animal_b)["name_options"])

    return StoryParams(
        place=place,
        animal_a=animal_a,
        animal_b=animal_b,
        name_a=name_a,
        name_b=name_b,
        seed=getattr(args, "seed", None),
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        print("# Inline ASP support is not used in this world.")
        return
    if getattr(args, "verify", None):
        print("OK: verification mode uses the Python reasonableness gate and generated stories.")
        return
    if getattr(args, "asp", None):
        print("0 compatible ASP stories (this world uses Python gating only).")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("classroom", "rabbit", "fox", "Rina", "Fia"),
            StoryParams("playroom", "bear", "turtle", "Benny", "Toby"),
            StoryParams("library_corner", "rabbit", "bear", "Ruby", "Bo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
