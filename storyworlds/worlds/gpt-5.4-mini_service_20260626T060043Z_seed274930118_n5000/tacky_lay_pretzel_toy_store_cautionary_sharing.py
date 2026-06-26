#!/usr/bin/env python3
"""
A small storyworld for a cautionary fable about sharing in a toy store.

Seed tale:
- In a toy store, a child sees a tacky pretend pretzel toy and wants it.
- The child tries to lay claim to it without sharing.
- A gentle helper warns that grabbing first leaves everyone sad.
- The child learns to share, and the toy store feels bright again.

This script models the story as a tiny state machine with physical meters and
emotional memes, plus an ASP twin for reasonableness checks.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    toy: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"tacky": 0.0, "desired": 0.0, "kept": 0.0, "shared": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "greed": 0.0, "fear": 0.0, "care": 0.0, "wise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    id: str = "toy_store"
    label: str = "the toy store"
    indoors: bool = True
    shelves: list[str] = field(default_factory=lambda: ["blocks", "balls", "dolls", "pretzels"])
    place: object | None = None
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
    label: str
    phrase: str
    type: str
    value: str = "small"
    feature: str = "tacky"
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
    place: str = "toy_store"
    treasure: str = "pretzel"
    name: str = "Mia"
    gender: str = "girl"
    helper: str = "clerk"
    trait: str = "curious"
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


@dataclass
class World:
    place: Place
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
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w
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


TREASURES = {
    "pretzel": Treasure(
        label="pretzel toy",
        phrase="a tacky pretzel toy with shiny stripes",
        type="pretzel",
        value="small",
        feature="tacky",
    ),
    "duck": Treasure(
        label="duck toy",
        phrase="a bright duck toy with a squeaky beak",
        type="duck",
        value="small",
        feature="tacky",
    ),
    "rocket": Treasure(
        label="rocket toy",
        phrase="a tacky rocket toy with glittery fins",
        type="rocket",
        value="small",
        feature="tacky",
    ),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ava", "Ivy"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Noah"],
}

TRAITS = ["curious", "gentle", "brave", "playful", "thoughtful"]


def moral() -> str:
    return "A toy shared with kindness feels brighter than a toy held tight."


def build_world(params: StoryParams) -> World:
    place = Place()
    world = World(place=place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label="the clerk"))
    toy_cfg = _safe_lookup(TREASURES, params.treasure)
    toy = world.add(Entity(
        id="Toy",
        kind="thing",
        type=toy_cfg.type,
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        owner=None,
    ))

    hero.memes["joy"] += 1
    toy.meters["tacky"] += 1
    toy.meters["desired"] += 1
    world.facts.update(hero=hero, helper=helper, toy=toy, treasure_cfg=toy_cfg, params=params)

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved the toy store.")
    world.say(f"One day, {hero.id} noticed {toy.phrase} on a shelf.")
    world.say(f"It looked tacky, but in a bright and funny way, and {hero.id} smiled at once.")

    world.para()
    world.say(f"{hero.id} wanted to lay hands on it right away, and {hero.pronoun()} reached for the toy.")
    hero.memes["greed"] += 1
    toy.meters["kept"] += 1

    if hero.memes["greed"] >= THRESHOLD:
        world.say(f"But the clerk raised a careful hand and said, \"A toy is more fun when it is shared.\"")
        hero.memes["fear"] += 1
        hero.memes["wise"] += 1

    world.para()
    if hero.memes["wise"] >= THRESHOLD:
        toy.shared_with.add(hero.id)
        toy.shared_with.add(helper.id)
        toy.meters["shared"] += 1
        hero.memes["care"] += 1
        hero.memes["joy"] += 1
        hero.memes["greed"] = 0.0
        world.say(f"{hero.id} nodded, laid the toy back down, and waited for a turn instead of snatching it.")
        world.say(f"Then the clerk let {hero.id} play too, and the little toy became a shared delight.")
        world.say(f"{hero.id} laughed, and the toy store felt warm and fair again.")
    else:
        world.say(f"{hero.id} kept the toy too tightly, and the fun turned small and lonely.")

    world.para()
    world.say(moral())
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    toy = _safe_fact(world, f, "toy")
    return [
        f'Write a short fable set in a toy store about {hero.id} and a {toy.feature} {toy.type} toy.',
        f'Tell a cautionary story where a child wants to lay claim to a toy before sharing it.',
        f'Write a gentle moral tale including the words "tacky", "lay", and "pretzel".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    toy = _safe_fact(world, f, "toy")
    helper = _safe_fact(world, f, "helper")
    params = _safe_fact(world, f, "params")

    qa = [
        QAItem(
            question=f"What kind of place was the story set in?",
            answer=f"It was set in the toy store, where shelves were full of playful things.",
        ),
        QAItem(
            question=f"What did {hero.id} first notice?",
            answer=f"{hero.id} first noticed {toy.phrase} sitting on a shelf.",
        ),
        QAItem(
            question=f"Why did the clerk speak up?",
            answer="The clerk wanted the child to remember that a toy is more joyful when it is shared.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to wait, share, and enjoy the toy with kindness instead of grabbing first.",
        ),
    ]
    if toy.shared_with:
        qa.append(
            QAItem(
                question=f"How did {hero.id} and the clerk enjoy the toy at the end?",
                answer=f"They shared it together, so both {hero.id} and {helper.label} could enjoy the little {toy.label}.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing is when more than one person gets a turn with the same thing in a fair and kind way.",
        ),
        QAItem(
            question="Why can grabbing too fast cause trouble?",
            answer="Grabbing too fast can make other people feel left out, sad, or upset.",
        ),
        QAItem(
            question="What does tacky mean here?",
            answer="Here, tacky means a little flashy or silly-looking in a way that stands out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits.append(f"{e.id}: meters={e.meters} memes={e.memes} shared_with={sorted(e.shared_with)}")
    return "\n".join(bits)


def valid_story(params: StoryParams) -> bool:
    return params.place == "toy_store" and params.treasure in TREASURES


ASP_RULES = r"""
place(toy_store).
treasure(pretzel).
treasure(duck).
treasure(rocket).

valid_story(P, T) :- place(P), treasure(T), P = toy_store.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "toy_store")]
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("toy_store", t) for t in TREASURES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy-store cautionary fable storyworld.")
    ap.add_argument("--place", choices=["toy_store"])
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["clerk"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "toy_store":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or "clerk"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place="toy_store",
        treasure=treasure,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="toy_store", treasure="pretzel", name="Mia", gender="girl", helper="clerk", trait="curious"),
    StoryParams(place="toy_store", treasure="duck", name="Leo", gender="boy", helper="clerk", trait="thoughtful"),
    StoryParams(place="toy_store", treasure="rocket", name="Ivy", gender="girl", helper="clerk", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_stories())} compatible story(s):")
        for p, t in asp_valid_stories():
            print(f"  {p} {t}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.treasure} at toy_store"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
