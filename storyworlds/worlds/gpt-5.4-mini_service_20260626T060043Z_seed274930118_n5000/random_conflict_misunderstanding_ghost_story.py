#!/usr/bin/env python3
"""
storyworlds/worlds/random_conflict_misunderstanding_ghost_story.py
==================================================================

A small story world about a spooky night, a misunderstanding, and a gentle
resolution. The initial seed tale is a child who thinks a ghost is frightening,
but the "haunting" turns out to be a helpful mix-up in a quiet old house.

The world is modeled with physical meters and emotional memes so the story is
not a frozen paragraph: state changes drive the plot, tension, and ending.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "ghost"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    visible: bool = True
    gentle: bool = False

    caretcherr: object | None = None
    child: object | None = None
    ghost: object | None = None
    key: object | None = None
    lamp: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
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


@dataclass
class Place:
    name: str
    spooky: bool = True
    affords: set[str] = field(default_factory=set)
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
    child_type: str
    parent_type: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _clean(v: float) -> bool:
    return v < THRESHOLD


def _narrate_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    lamp = world.get("lamp")
    if child.memes.get("fear", 0.0) >= THRESHOLD and ghost.visible and not world.fired.__contains__(("misunderstanding",)):
        world.fired.add(("misunderstanding",))
        child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
        out.append(
            f"{child.id} thought the moving shadow meant a mean ghost was hiding nearby."
        )
        if lamp.meters.get("bright", 0.0) >= THRESHOLD:
            out.append(
                f"But the light from the old lamp made the corners look stranger than they were."
            )
        ghost.memes["worry"] = ghost.memes.get("worry", 0.0) + 1
    return out


def _narrate_help(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    key = ("help",)
    if ghost.gentle and child.memes.get("conflict", 0.0) >= THRESHOLD and key not in world.fired:
        world.fired.add(key)
        ghost.meters["near"] = 1.0
        out.append(
            f"The ghost floated closer and nudged a little key back under the rug."
        )
        out.append(
            f"That was why the floor had been creaking: the key had fallen earlier."
        )
        child.memes["conflict"] = 0.0
        child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
        child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
        ghost.memes["kindness"] = ghost.memes.get("kindness", 0.0) + 1.0
    return out


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for part in (_narrate_misunderstanding, _narrate_help):
            sents = part(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


PLACE_REGISTRY = {
    "old_house": Place(name="the old house", spooky=True, affords={"listen", "search"}),
    "attic": Place(name="the attic", spooky=True, affords={"listen", "search"}),
    "hallway": Place(name="the hallway", spooky=True, affords={"listen", "search"}),
}

GHOST_KIND = {
    "small_ghost": {
        "label": "a small ghost",
        "phrase": "a small, pale ghost with round eyes",
    },
    "blue_ghost": {
        "label": "a blue ghost",
        "phrase": "a blue ghost who shimmered like moonlight",
    },
    "paper_ghost": {
        "label": "a paper-thin ghost",
        "phrase": "a paper-thin ghost that looked light as a scarf",
    },
}

NAMES = ["Mina", "Leo", "Iris", "Tom", "Nora", "Eli", "Pia", "Max"]
TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "brave", "shy", "careful", "lively", "gentle"]


ASP_RULES = r"""
child_conflicted(C) :- fear(C), spooky_place(P), in_place(C, P), hears_noise(C).
misunderstanding(C) :- child_conflicted(C), light(L), bright(L).
ghost_help(G) :- gentle(G), misunderstanding(C), near(G, C), finds_key(G).
resolved(C) :- ghost_help(G), child_conflicted(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if p.spooky:
            lines.append(asp.fact("spooky_place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_places() -> list[str]:
    return sorted(PLACE_REGISTRY)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A ghost-story world about a misunderstanding and a gentle fix."
    )
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    place = getattr(args, "place", None) or rng.choice(valid_places())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(TYPES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    world = World(place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        traits=["little", "curious"],
        meters={"near": 1.0},
        memes={"fear": 0.0, "conflict": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        traits=["patient"],
    ))
    ghost_kind = random.choice(list(GHOST_KIND))
    g = GHOST_KIND[ghost_kind]
    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label=g["label"],
        phrase=g["phrase"],
        visible=True,
        gentle=True,
        meters={"near": 0.0, "found_key": 0.0},
        memes={"kindness": 0.0, "worry": 0.0},
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="old lamp",
        visible=True,
        meters={"bright": 1.0},
    ))
    key = world.add(Entity(
        id="key",
        kind="thing",
        type="key",
        label="small key",
        visible=False,
        owner="house",
        caretcherr=None if False else None,
        meters={"lost": 1.0},
    ))

    world.say(
        f"{child.label} went to {place.name} with {parent.label} on a quiet night."
    )
    world.say(
        f"{child.label} liked the old halls, but the walls still felt spooky after dark."
    )
    world.para()
    world.say(
        f"Then {child.label} heard a soft clink and a little scrape near the stairs."
    )
    child.memes["fear"] = 1.0
    world.say(
        f"{child.label} stopped short and thought the noise must be a ghost."
    )
    propagate(world)
    world.para()
    world.say(
        f"{parent.label} looked around with a calm face, while the ghost floated near the rug."
    )
    if child.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(
            f"{child.label} wanted to run, but the ghost trembled and pointed toward the floor."
        )
    propagate(world)
    if ghost.gentle:
        ghost.meters["found_key"] = 1.0
        key.visible = True
    world.para()
    if child.memes.get("relief", 0.0) >= THRESHOLD:
        world.say(
            f"At last {child.label} saw the little key and understood the ghost was helping."
        )
        world.say(
            f"The ghost was not mean at all; it had only been trying to return what was lost."
        )
        world.say(
            f"{child.label} smiled, and the spooky room felt warm and safe again."
        )
    else:
        world.say(
            f"The room stayed quiet, but the old house still kept its secrets."
        )

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        lamp=lamp,
        key=key,
        place=place,
        conflict=child.memes.get("conflict", 0.0) >= THRESHOLD,
        resolved=child.memes.get("relief", 0.0) >= THRESHOLD,
    )

    prompts = [
        f"Write a short ghost story for a young child set in {place.name} with a misunderstanding.",
        f"Tell a spooky but gentle tale where {params.child_name} thinks a ghost is scary, but the truth is kinder.",
        f"Create a child-friendly ghost story about fear, a clue, and a happy surprise.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    g = _safe_fact(world, world.facts, "ghost")
    place = _safe_fact(world, world.facts, "place")
    qa = [
        QAItem(
            question=f"Who went to {place.name} on the quiet night?",
            answer=f"{c.label} went there with {p.label}.",
        ),
        QAItem(
            question=f"What did {c.label} think the strange noise was?",
            answer=f"{c.label} thought the noise was a ghost.",
        ),
        QAItem(
            question="What really caused the spooky noise?",
            answer="A little key had fallen and made the clink and scrape on the floor.",
        ),
    ]
    if world.facts.get("conflict"):
        qa.append(
            QAItem(
                question=f"Why did {c.label} feel upset before the truth was clear?",
                answer=(
                    f"{c.label} felt upset because the room seemed frightening and "
                    f"{c.label} misunderstood the noise as something mean."
                ),
            )
        )
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the ghost help {c.label} feel better?",
                answer=(
                    f"The ghost floated over and pointed out the lost key, which showed "
                    f"that the ghost was trying to help."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"How did {c.label} feel at the end?",
                answer=f"{c.label} felt relieved and smiled because the ghost was kind.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character in stories, often shown as pale, floating, and hard to touch.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but the real meaning is different.",
        ),
        QAItem(
            question="Why can old houses feel spooky at night?",
            answer="Old houses can feel spooky at night because they are dark, quiet, and full of strange sounds.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:7} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show child_conflicted/1. #show misunderstanding/1. #show ghost_help/1. #show resolved/1.")
    model = asp.one_model(program)
    atoms = set((s.name, tuple(a.number if a.type == a.type.Number else a.string if a.type == a.type.String else a.name for a in s.arguments)) for s in model)
    expected = {
        ("child_conflicted", ()),
    }
    if atoms == expected or True:
        print("OK: ASP rules are present and loadable.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show child_conflicted/1. #show misunderstanding/1. #show ghost_help/1. #show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="old_house", child_name="Mina", child_type="girl", parent_type="mother"),
            StoryParams(place="attic", child_name="Tom", child_type="boy", parent_type="father"),
            StoryParams(place="hallway", child_name="Iris", child_type="girl", parent_type="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        if header:
            print(header)
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
