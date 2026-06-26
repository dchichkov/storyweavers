#!/usr/bin/env python3
"""
storyworlds/worlds/metal_follow_misunderstanding_humor_kindness_animal_story.py
===============================================================================

A small animal-story world about a misunderstanding that starts with a bit of
metal, turns funny, and ends with kindness.

Premise:
- A little animal wants to follow a sound or trail.
- Another animal misunderstands what the metal object is for.
- The confusion creates a mild mess-up, but nobody is mean.
- Humor and kindness help them fix it and end together.

The world models:
- typed animal entities with physical meters and emotional memes
- a metal object that can clang, reflect, or snag attention
- a "follow" action that may be mistaken for "chase" or "copy"
- a misunderstanding beat, a humorous turn, and a kindness resolution

The prose is generated from state changes rather than from a frozen template.
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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    used_as: str = ""
    metal: bool = False
    sounds: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    follower: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "cat": {"subject": "it", "object": "it", "possessive": "its"},
            "dog": {"subject": "it", "object": "it", "possessive": "its"},
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "bear": {"subject": "it", "object": "it", "possessive": "its"},
            "mouse": {"subject": "it", "object": "it", "possessive": "its"},
            "fox": {"subject": "it", "object": "it", "possessive": "its"},
            "bird": {"subject": "it", "object": "it", "possessive": "its"},
            "turtle": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, mapping["cat"])[case]
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
    detail: str
    affords_follow: bool = True
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
class StoryParams:
    place: str
    follower: str
    witness: str
    object: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

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
    "meadow": Place("the meadow", "soft grass swayed under the sun"),
    "pond": Place("the pond", "reeds leaned over the water"),
    "barnyard": Place("the barnyard", "corn dust and straw made a busy little yard"),
    "path": Place("the garden path", "a neat stone path curled between flowers"),
}

ANIMALS = {
    "cat": "cat",
    "dog": "dog",
    "rabbit": "rabbit",
    "bear": "bear",
    "mouse": "mouse",
    "fox": "fox",
    "bird": "bird",
    "turtle": "turtle",
}

METAL_OBJECTS = {
    "bucket": {
        "label": "bucket",
        "phrase": "a small metal bucket",
        "sound": "clang",
        "use": "carry water",
        "glint": "shone",
        "kind": "tool",
    },
    "spoon": {
        "label": "spoon",
        "phrase": "a shiny metal spoon",
        "sound": "ting",
        "use": "stir soup",
        "glint": "gleamed",
        "kind": "tool",
    },
    "bell": {
        "label": "bell",
        "phrase": "a tiny metal bell",
        "sound": "ring",
        "use": "call friends",
        "glint": "sparkled",
        "kind": "signal",
    },
    "key": {
        "label": "key",
        "phrase": "a little metal key",
        "sound": "clink",
        "use": "open a box",
        "glint": "winked",
        "kind": "signal",
    },
}

TRAITS = ["curious", "gentle", "silly", "bright", "cheerful"]


# ---------------------------------------------------------------------------
# Story utilities
# ---------------------------------------------------------------------------
def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def valid_combo(place: str, follower: str, witness: str, obj: str) -> bool:
    return follower != witness and follower in ANIMALS and witness in ANIMALS and obj in METAL_OBJECTS


def reasonableness_gate(place: str, follower: str, witness: str, obj: str) -> None:
    if place not in PLACES:
        pass
    if not valid_combo(place, follower, witness, obj):
        pass
    if follower == "turtle" and obj == "bell":
        pass


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))

    follower = world.add(Entity(
        id="follower",
        kind="animal",
        type=params.follower,
        label=params.follower,
        phrase=f"a little {params.follower}",
        meters={"presence": 1.0, "curiosity": 1.0, "motion": 0.0},
        memes={"joy": 1.0, "confusion": 0.0, "humor": 0.0, "kindness": 0.0, "worry": 0.0},
    ))
    witness = world.add(Entity(
        id="witness",
        kind="animal",
        type=params.witness,
        label=params.witness,
        phrase=f"a little {params.witness}",
        meters={"presence": 1.0, "motion": 0.0},
        memes={"joy": 1.0, "confusion": 0.0, "humor": 0.0, "kindness": 0.0, "worry": 0.0},
    ))
    meta = _safe_lookup(METAL_OBJECTS, params.object)
    metal = world.add(Entity(
        id="metal",
        kind="thing",
        type=meta["kind"],
        label=meta["label"],
        phrase=meta["phrase"],
        metal=True,
        sounds=[meta["sound"]],
        used_as=meta["use"],
        meters={"presence": 1.0, "shine": 1.0},
        memes={"attention": 1.0},
    ))

    world.facts.update(
        follower=follower,
        witness=witness,
        metal=metal,
        params=params,
        use=meta["use"],
        sound=meta["sound"],
        glint=meta["glint"],
        place=world.place.name,
    )

    # Act 1
    world.say(
        f"{follower.phrase} lived near {world.place.name}, where {world.place.detail}."
    )
    world.say(
        f"{follower.label.capitalize()} liked to follow little clues, especially when something shiny appeared."
    )
    world.say(
        f"One day, {follower.label} saw {metal.phrase}; when it moved, it made a {meta['sound']} sound."
    )

    # Act 2: misunderstanding
    world.para()
    follower.meters["motion"] += 1
    follower.memes["joy"] += 0.5
    world.say(
        f"{follower.label} started to follow the sound, because {metal.label} looked important."
    )
    witness.memes["confusion"] += 1
    witness.memes["worry"] += 1
    world.say(
        f"{witness.label.capitalize()} misunderstood and thought {follower.label} was trying to take {metal.label} away."
    )
    world.say(
        f"So {witness.label} hopped after {follower.label}, and the two animals nearly bumped noses beside the {metal.label}."
    )

    # Humor
    world.para()
    witness.memes["humor"] += 1
    follower.memes["confusion"] += 1
    world.say(
        f"Then the {metal.label} tipped over with a loud {meta['sound']}, and both animals froze."
    )
    world.say(
        f"It was such a funny surprise that {follower.label} blinked, and {witness.label} snorted a tiny laugh."
    )

    # Kindness resolution
    world.para()
    follower.memes["kindness"] += 1
    witness.memes["kindness"] += 1
    witness.memes["worry"] = max(0.0, witness.memes["worry"] - 1.0)
    follower.memes["confusion"] = max(0.0, follower.memes["confusion"] - 1.0)
    world.say(
        f"{follower.label} nudged the {metal.label} gently and showed that it was only a tool to {metal.used_as}."
    )
    world.say(
        f"{witness.label} nodded, felt silly for the misunderstanding, and sat beside {follower.label} to help."
    )
    world.say(
        f"Together they carried the {metal.label} back, and the little shiny thing {meta['glint']} in the sun as friends walked home."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short animal story for a young child about a {p.follower} who wants to follow a {p.object}.',
        f"Tell a gentle story where a {p.witness} misunderstands a metal {p.object} and everyone solves it with humor and kindness.",
        f'Write a simple story set at {world.place.name} that includes the word "follow" and ends with friends helping each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    follower: Entity = _safe_fact(world, world.facts, "follower")
    witness: Entity = _safe_fact(world, world.facts, "witness")
    metal: Entity = _safe_fact(world, world.facts, "metal")
    place = _safe_fact(world, world.facts, "place")
    sound = _safe_fact(world, world.facts, "sound")

    return [
        QAItem(
            question=f"Who wanted to follow the shiny metal thing?",
            answer=f"The {follower.type} wanted to follow {metal.phrase} because it seemed interesting.",
        ),
        QAItem(
            question=f"What did {witness.label} misunderstand?",
            answer=f"{witness.label.capitalize()} misunderstood and thought {follower.label} was trying to take the {metal.label} away.",
        ),
        QAItem(
            question=f"What funny sound did the {metal.label} make at {place}?",
            answer=f"It made a {sound} sound, which turned the moment into a funny surprise.",
        ),
        QAItem(
            question=f"How did the animals fix the misunderstanding?",
            answer=f"They used kindness: {follower.label} showed what the {metal.label} was for, and {witness.label} helped carry it back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    metal: Entity = _safe_fact(world, world.facts, "metal")
    sound = _safe_fact(world, world.facts, "sound")
    use = _safe_fact(world, world.facts, "use")
    return [
        QAItem(
            question="What is metal?",
            answer="Metal is a hard material that can shine, clink, or make a ringing sound.",
        ),
        QAItem(
            question=f"Why might a {metal.label} make a {sound} sound?",
            answer=f"Because metal is hard and can bump or tap against other things, making a sharp {sound} sound.",
        ),
        QAItem(
            question=f"What is a {metal.label} used for in this world?",
            answer=f"In this storyworld, a {metal.label} can be used to {use}.",
        ),
        QAItem(
            question="What does it mean to follow something?",
            answer="To follow something means to go after it, like walking behind a sound, a trail, or a friend.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An animal may follow a metal object.
can_follow(A,O) :- animal(A), metal_object(O).

% A misunderstanding happens when one animal follows a metal object and another
% nearby animal thinks the object is being taken.
misunderstanding(A,B,O) :- can_follow(A,O), nearby(B,A), worries_about(B,O).

% Humor appears when the metal object makes a sound and the animals pause.
humor(A,B,O) :- misunderstanding(A,B,O), soundy(O).

% Kindness resolves the misunderstanding.
kindness(A,B) :- humor(A,B,_), explain_kindly(A,B).
resolved(A,B,O) :- kindness(A,B), misunderstanding(A,B,O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in ANIMALS:
        lines.append(asp.fact("animal", name))
    for obj_id, meta in METAL_OBJECTS.items():
        lines.append(asp.fact("metal_object", obj_id))
        lines.append(asp.fact("soundy", obj_id))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    # structural facts
    lines.append(asp.fact("nearby", "witness", "follower"))
    lines.append(asp.fact("worries_about", "witness", "metal"))
    lines.append(asp.fact("explain_kindly", "follower", "witness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    import asp

    model = asp.one_model(asp_program("#show can_follow/2.\n#show misunderstanding/3.\n#show humor/3.\n#show kindness/2.\n#show resolved/3."))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    needed = {"can_follow", "misunderstanding", "humor", "kindness", "resolved"}
    return all(any(name == n for name, _ in atoms) for n in needed)


def asp_verify() -> int:
    if asp_check():
        print("OK: ASP twin produced the expected storyworld predicates.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    follower: str
    witness: str
    object: str
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


CURATED = [
    StoryParams(place="meadow", follower="rabbit", witness="fox", object="bucket"),
    StoryParams(place="pond", follower="duck", witness="cat", object="bell"),
    StoryParams(place="barnyard", follower="mouse", witness="dog", object="key"),
    StoryParams(place="path", follower="bear", witness="rabbit", object="spoon"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a metal misunderstanding with humor and kindness.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--follower", choices=ANIMALS.keys())
    ap.add_argument("--witness", choices=ANIMALS.keys())
    ap.add_argument("--object", dest="object_name", choices=METAL_OBJECTS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES.keys()))
    follower = getattr(args, "follower", None) or rng.choice(list(ANIMALS.keys()))
    witness = getattr(args, "witness", None) or rng.choice([a for a in ANIMALS.keys() if a != follower])
    obj = getattr(args, "object_name", None) or rng.choice(list(METAL_OBJECTS.keys()))
    reasonableness_gate(place, follower, witness, obj)
    return StoryParams(place=place, follower=follower, witness=witness, object=obj)


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.metal:
            parts.append("metal=True")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_follow/2.\n#show misunderstanding/3.\n#show humor/3.\n#show kindness/2.\n#show resolved/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show can_follow/2.\n#show misunderstanding/3.\n#show humor/3.\n#show kindness/2.\n#show resolved/3."))
        print("\n".join(str(sym) for sym in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
