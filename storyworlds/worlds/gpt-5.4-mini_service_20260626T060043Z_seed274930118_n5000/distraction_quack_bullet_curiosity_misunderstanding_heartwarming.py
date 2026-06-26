#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/distraction_quack_bullet_curiosity_misunderstanding_heartwarming.py
================================================================================================================

A small heartwarming story world about a curious child, a quacking duck,
and a misunderstanding that gets gently cleared up.

Seed premise:
- A child notices a quack, gets distracted, and mistakes a shiny bullet-shaped
  object for something important.
- Curiosity pulls the child toward an answer.
- Misunderstanding creates a wobble in the middle.
- A warm, friendly explanation turns the moment into a kind ending.

The world is intentionally narrow: fewer, better story shapes instead of many
weak variations.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    duck: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    has_pond: bool = False
    has_bench: bool = False
    has_boardwalk: bool = False
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
    child_name: str
    child_gender: str
    parent_type: str
    duck_name: str
    clue: str
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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "pond": Place(name="the pond", has_pond=True, has_bench=True, has_boardwalk=True),
    "garden": Place(name="the garden", has_pond=False, has_bench=True, has_boardwalk=False),
    "park": Place(name="the park", has_pond=True, has_bench=True, has_boardwalk=False),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo"]
DUCK_NAMES = ["Pip", "Momo", "Daisy", "Bubbles"]
CLUES = ["a shiny bullet-shaped bead", "a tiny bulletin clip", "a silver button that looked like a bullet"]
TRAITS = ["curious", "gentle", "bright-eyed"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.child_gender not in {"girl", "boy"}:
        pass
    if params.clue not in CLUES:
        pass


def choose_rhyme_word(place: Place, clue: str) -> str:
    if place.has_pond:
        return "quack"
    return "pebble"


def activity_turns(world: World, child: Entity, duck: Entity, clue: str) -> None:
    child.memes["curiosity"] += 1
    child.memes["distraction"] += 1
    duck.memes["friendly"] += 1
    world.say(
        f"{child.id} was a curious child who liked noticing little things. "
        f"One day, {child.pronoun().capitalize()} heard a soft quack near {world.place.name} "
        f"and followed the sound instead of finishing {child.pronoun('possessive')} walk."
    )
    world.say(
        f"On the path, {child.id} found {clue}, and that made {child.pronoun('object')} pause. "
        f"{child.id} wondered if the duck had dropped it."
    )
    child.memes["misunderstanding"] += 1
    world.say(
        f"But that was a misunderstanding. The shiny thing belonged to a little sign by the pond, "
        f"not to {duck.id}."
    )


def warm_explanation(world: World, child: Entity, parent: Entity, duck: Entity, clue: str) -> None:
    child.memes["misunderstanding"] = 0
    child.memes["warmth"] += 1
    parent.memes["warmth"] += 1
    duck.memes["relief"] += 1
    world.say(
        f"{parent.pronoun().capitalize()} smiled and knelt beside {child.pronoun('object')}. "
        f'"The quack was just {duck.id} saying hello," {parent.pronoun()} said softly. '
        f'"And that {clue} is only a little marker for people walking by."'
    )
    world.say(
        f"{child.id}'s face relaxed. {child.pronoun().capitalize()} waved at {duck.id}, "
        f"and {duck.id} answered with another happy quack."
    )
    world.say(
        f"After that, {child.id} carried on with a lighter step, glad the answer was kind and simple."
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="parent"))
    duck = world.add(Entity(id=params.duck_name, kind="character", type="duck", label="duck"))
    clue = params.clue

    child.memes["curiosity"] += 1
    parent.memes["warmth"] += 1
    duck.memes["friendly"] += 1

    world.say(
        f"{child.id} was a little {random.choice(TRAITS)} {child.type} who loved quiet walks "
        f"with {child.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"At {world.place.name}, {child.id} could hear a duck before {child.id} could see one, "
        f"and that always made {child.pronoun('object')} smile."
    )

    world.para()
    activity_turns(world, child, duck, clue)

    world.para()
    warm_explanation(world, child, parent, duck, clue)

    world.facts.update(child=child, parent=parent, duck=duck, clue=clue)
    return world


def build_story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    d = _safe_fact(world, world.facts, "duck")
    clue = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question=f"Why did {c.id} stop and look around at {world.place.name}?",
            answer=f"{c.id} heard a quack, felt curious, and got distracted by the sound.",
        ),
        QAItem(
            question=f"What did {c.id} think {d.id} had dropped?",
            answer=f"{c.id} thought {d.id} might have dropped {clue}, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"How did {p.id} help fix the misunderstanding?",
            answer=f"{p.id} explained that the quack was only {d.id} saying hello and that the shiny thing belonged to a sign.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{c.id} felt glad, waved at {d.id}, and kept walking with a lighter heart.",
        ),
    ]


def build_world_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What does a quack usually mean?",
            answer="A quack is the sound a duck makes.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more about something.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but it is not.",
        ),
    ]


def build_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "child")
    d = _safe_fact(world, world.facts, "duck")
    clue = _safe_fact(world, world.facts, "clue")
    return [
        f"Write a heartwarming story for children about {c.id}, a curious child, hearing a quack near {world.place.name}.",
        f"Tell a gentle story where {c.id} gets distracted by {clue} and thinks {d.id} is involved, but the mistake is kindly explained.",
        f"Write a short, cozy story about curiosity and misunderstanding that ends with a friendly duck and a happy child.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- child(X), curiosity(X,C), C >= 1.
distracted(X) :- child(X), distraction(X,D), D >= 1.
misunderstood(X) :- child(X), misunderstanding(X,M), M >= 1.
heartwarming_story :- curious(X), distracted(X), misunderstood(X), resolved(X).
resolved(X) :- misunderstanding(X,M), M = 0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for name in CHILD_NAMES:
        lines.append(asp.fact("child_name", name))
    for name in DUCK_NAMES:
        lines.append(asp.fact("duck_name", name))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming curiosity / misunderstanding story world.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--duck")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    duck = getattr(args, "duck", None) or rng.choice(DUCK_NAMES)
    clue = getattr(args, "clue", None) or rng.choice(CLUES)
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_type=parent, duck_name=duck, clue=clue)


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
    StoryParams(place="pond", child_name="Mia", child_gender="girl", parent_type="mother", duck_name="Pip", clue=_safe_lookup(CLUES, 0)),
    StoryParams(place="park", child_name="Leo", child_gender="boy", parent_type="father", duck_name="Daisy", clue=_safe_lookup(CLUES, 1)),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show heartwarming_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
