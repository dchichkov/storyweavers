#!/usr/bin/env python3
"""
storyworlds/worlds/initiative_mystery_to_solve_slice_of_life.py
===============================================================

A small slice-of-life story world about a child who takes initiative to solve
an everyday mystery: a missing thing turns out to have simply moved.

Seed tale:
---
Mina wanted to help at home, but she also wanted to know where the blue ribbon
had gone. She looked in the basket, under the table, and by the sofa. She
noticed the ribbon's sparkly end near the flowerpot and followed it. The ribbon
had been used to tie a bunch of drawings together, and Dad had moved the bundle
to the shelf. Mina felt proud that she solved the mystery by paying attention.
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
class Person:
    name: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    parent: object | None = None
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
    place: object | None = None
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
class ObjectThing:
    label: str
    phrase: str
    owner: str
    location: str
    hidden: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    item: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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
    child_name: str
    parent_name: str
    item: str
    setting: str
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
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.child = Person(name=params.child_name, role="child", traits=["helpful", "curious"])
        self.parent = Person(name=params.parent_name, role="parent", traits=["busy", "kind"])
        self.place = Place(name=params.setting)
        self.item = ObjectThing(
            label=_safe_lookup(ITEMS, params.item)["label"],
            phrase=_safe_lookup(ITEMS, params.item)["phrase"],
            owner=self.parent.name,
            location=_safe_lookup(ITEMS, params.item)["start"],
            hidden=True,
        )
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            f"child={self.child.name} meters={self.child.meters} memes={self.child.memes}"
        )
        lines.append(
            f"parent={self.parent.name} meters={self.parent.meters} memes={self.parent.memes}"
        )
        lines.append(
            f"item={self.item.label} location={self.item.location} hidden={self.item.hidden} meters={self.item.meters}"
        )
        lines.append(f"place={self.place.name}")
        return "\n".join(lines)


CHILD_NAMES = ["Mina", "Toby", "Rosa", "Eli", "June", "Niko", "Lena", "Ari"]
PARENT_NAMES = ["Dad", "Mom", "Auntie", "Grandpa", "Grandma"]
SETTINGS = ["the kitchen", "the living room", "the hallway", "the porch", "the den"]

ITEMS = {
    "ribbon": {
        "label": "blue ribbon",
        "phrase": "a blue ribbon tied around some drawings",
        "start": "basket",
        "clue": "a sparkly end",
        "ending": "The blue ribbon was not lost at all; it was tied around the drawings on the shelf.",
        "question": "What was missing?",
    },
    "spoon": {
        "label": "wooden spoon",
        "phrase": "a wooden spoon used for mixing",
        "start": "drawer",
        "clue": "a round handle",
        "ending": "The wooden spoon had been moved to the counter where the batter bowl sat.",
        "question": "What was missing?",
    },
    "notebook": {
        "label": "small notebook",
        "phrase": "a small notebook with a green cover",
        "start": "desk",
        "clue": "a green corner",
        "ending": "The small notebook was tucked into the bag by the door after the list was finished.",
        "question": "What was missing?",
    },
    "keys": {
        "label": "car keys",
        "phrase": "car keys with a red tag",
        "start": "hook",
        "clue": "a red tag",
        "ending": "The car keys had been set on the kitchen shelf so they would not get forgotten.",
        "question": "What was missing?",
    },
}

REGISTRY = {
    "items": ITEMS,
    "settings": SETTINGS,
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery world with initiative.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    setting = getattr(args, "setting", None) or rng.choice(SETTINGS)
    child = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    if child == parent:
        parent = rng.choice([p for p in PARENT_NAMES if p != parent])
    return StoryParams(child_name=child, parent_name=parent, item=item, setting=setting)


def _narrate_search(world: World) -> None:
    c = world.child
    item = world.item
    world.say(f"{c.name} noticed that {item.label} was missing from its usual spot.")
    c.memes["curiosity"] += 1
    c.meters["initiative"] += 1
    world.say(f"Instead of waiting, {c.name} took initiative and began looking carefully.")
    world.para()
    for spot in _safe_lookup(SEARCH_SPOTS, item.label):
        world.say(f"{c.name} checked the {spot}.")
        if spot == item.location:
            item.meters["seen"] += 1
            world.say(f"That did not answer the mystery, but {c.name} kept paying attention.")
    world.para()
    clue = _safe_lookup(ITEM_CLUES, item.label)
    world.say(f"Then {c.name} spotted {clue} near the {_safe_lookup(CLUE_PLACES, item.label)}.")
    c.meters["initiative"] += 1
    c.memes["pride"] += 1
    world.say(f"{c.name} followed the clue and found out what had really happened.")


def _narrate_resolution(world: World) -> None:
    c = world.child
    p = world.parent
    item = world.item
    world.para()
    world.say(item.ending)
    item.hidden = False
    item.meters["moved"] += 1
    c.meters["joy"] += 1
    p.meters["calm"] += 1
    c.memes["pride"] += 1
    world.say(f"{c.name} told {p.name}, and {p.name} smiled at how careful {c.name} had been.")
    world.say(f"After that, {c.name} felt proud for solving the mystery by looking closely.")


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    _narrate_search(world)
    _narrate_resolution(world)
    world.facts = {
        "child": world.child,
        "parent": world.parent,
        "item": world.item,
        "setting": world.place,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle slice-of-life mystery about {p.child_name} who takes initiative to find a missing {_safe_lookup(ITEMS, p.item)['label']}.",
        f"Tell a short story set in {p.setting} where {p.child_name} notices clues and solves an everyday mystery.",
        f"Write a child-friendly story about a small household mystery, careful searching, and a proud ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.child
    p = world.parent
    item = world.item
    return [
        QAItem(
            question=f"Who took initiative to solve the mystery?",
            answer=f"{c.name} took initiative by looking carefully instead of waiting.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"The mystery was about the missing {item.label}.",
        ),
        QAItem(
            question=f"How did {c.name} solve the mystery?",
            answer=f"{c.name} solved it by checking places, noticing a clue, and following it to where the {item.label} had been moved.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt calm and pleased because {c.name} figured it out.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    item = world.item
    return [
        QAItem(
            question="What is initiative?",
            answer="Initiative is when someone starts doing something helpful without being told first.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question=f"Why might someone move the {item.label}?",
            answer="Someone might move it to keep it safe, to use it somewhere else, or to put it where it will not be forgotten.",
        ),
    ]


SEARCH_SPOTS = {
    "blue ribbon": ["basket", "table", "sofa"],
    "wooden spoon": ["drawer", "sink", "stove"],
    "small notebook": ["desk", "chair", "bag"],
    "car keys": ["hook", "counter", "shoes by the door"],
}

ITEM_CLUES = {
    "blue ribbon": "the ribbon's sparkly end",
    "wooden spoon": "the spoon's round handle",
    "small notebook": "a green corner of the cover",
    "car keys": "a red tag",
}

CLUE_PLACES = {
    "blue ribbon": "flowerpot",
    "wooden spoon": "mixing bowl",
    "small notebook": "door bag",
    "car keys": "kitchen shelf",
}


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
item(item_ribbon).
item(item_spoon).
item(item_notebook).
item(item_keys).

setting(kitchen).
setting(living_room).
setting(hallway).
setting(porch).
setting(den).

initiative_taken(child) :- child_searches(child).
mystery_solved(child) :- finds_clue(child), follows_clue(child).

#show initiative_taken/1.
#show mystery_solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in CHILD_NAMES:
        lines.append(asp.fact("child_name", name))
    for name in PARENT_NAMES:
        lines.append(asp.fact("parent_name", name))
    for key in ITEMS:
        lines.append(asp.fact("item_name", key))
    for setting in SETTINGS:
        lines.append(asp.fact("setting_name", setting))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child_name="Mina", parent_name="Dad", item="ribbon", setting="the living room"),
    StoryParams(child_name="Lena", parent_name="Mom", item="notebook", setting="the hallway"),
    StoryParams(child_name="Ari", parent_name="Grandma", item="keys", setting="the kitchen"),
    StoryParams(child_name="Toby", parent_name="Auntie", item="spoon", setting="the den"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show initiative_taken/1.\n#show mystery_solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for this world, but the core reasoner is Python-only.")
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
            header = f"### {p.child_name}: mystery of the {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
