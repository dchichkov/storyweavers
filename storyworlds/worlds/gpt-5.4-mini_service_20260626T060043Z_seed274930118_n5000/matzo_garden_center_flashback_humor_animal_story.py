#!/usr/bin/env python3
"""
storyworlds/worlds/matzo_garden_center_flashback_humor_animal_story.py
======================================================================

A small animal-story world set in a garden center, with a light flashback and
humor beat built from a simple premise:

A young animal visits a garden center carrying matzo for a snack. The animal
wants to help with a plant display, but a funny flashback reminds them of a
previous crumbly mishap. They solve the problem by choosing a sensible place
to eat and by using the matzo crumbs to feed birds instead of making a mess.

This world models:
- physical meters: crumbs, dirt, water, bloom, cleanliness
- emotional memes: joy, worry, pride, embarrassment, laughter, memory

The prose is state-driven: the story begins with the visit, turns through a
flashback and a humorous problem, and ends with a concrete change in the world.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    eaten_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    bird: object | None = None
    child: object | None = None
    snack: object | None = None
    def __post_init__(self) -> None:
        for k in ["crumbs", "dirt", "water", "bloom", "cleanliness", "birdfeed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "embarrassment", "laughter", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "dog", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str = "the garden center"
    afford_help: bool = True
    afford_eat: bool = True
    afford_feed_birds: bool = True
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
class Snack:
    id: str
    label: str
    phrase: str
    crumbs: str
    crumbles: bool = True
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
class Animal:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used: bool = False

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.flashback_used = self.flashback_used
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_crumbs_on_hands(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters["crumbs"] < THRESHOLD:
            continue
        sig = ("crumbs", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["embarrassment"] += 1
        out.append(f"{char.label} ended up with crumbs on {char.pronoun('possessive')} paws.")
    return out


def _r_dirty_after_play(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters["dirt"] < THRESHOLD:
            continue
        sig = ("dirty", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["worry"] += 1
        out.append(f"That made {char.label} feel a little worried about making a mess.")
    return out


def _r_laughter_after_flashback(world: World) -> list[str]:
    out: list[str] = []
    if not world.flashback_used:
        return out
    for char in world.characters():
        sig = ("laugh", char.id)
        if sig in world.fired:
            continue
        if char.memes["memory"] >= THRESHOLD:
            world.fired.add(sig)
            char.memes["laughter"] += 1
            out.append(f"{char.label} chuckled at the memory.")
    return out


CAUSAL_RULES = [
    _r_crumbs_on_hands,
    _r_dirty_after_play,
    _r_laughter_after_flashback,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, child: Entity, snack: Entity) -> None:
    world.flashback_used = True
    child.memes["memory"] += 1
    world.say(
        f"That gave {child.label} a funny flashback to last week, when {child.pronoun()} "
        f"tried to eat {snack.phrase} while leaning over a flower pot and sent crumbs "
        f"everywhere."
    )
    world.say(
        f"{child.label} snorted a laugh, because the memory was silly now, even if it had "
        f"been embarrassing then."
    )


def help_in_garden(world: World, child: Entity, adult: Entity) -> None:
    child.memes["joy"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"{child.label} wanted to help with the tiny seedlings, and {adult.label} showed "
        f"{child.pronoun('object')} where the soft soil needed careful fingers."
    )


def eat_matzo(world: World, child: Entity, snack: Entity) -> None:
    if not world.setting.afford_eat:
        pass
    child.meters["crumbs"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Then {child.label} broke a piece of {snack.label} for a snack. "
        f"The matzo crackled loudly, and a few crumbs landed on {child.pronoun('possessive')} lap."
    )
    propagate(world, narrate=True)


def feed_birds(world: World, child: Entity, snack: Entity) -> None:
    if not world.setting.afford_feed_birds:
        return
    bird = world.get("birds")
    crumbs = child.meters["crumbs"]
    if crumbs < THRESHOLD:
        return
    bird.meters["birdfeed"] += crumbs
    child.meters["crumbs"] = 0
    child.memes["pride"] += 1
    world.say(
        f"Instead of brushing the crumbs away, {child.label} sprinkled them for the birds, "
        f"and the sparrows hopped in with bright little peeps."
    )
    world.say(
        f"{child.label} smiled, because the matzo had turned into birdfeed instead of a mess."
    )


def settle_story(world: World, child: Entity, adult: Entity, snack: Entity) -> None:
    child.meters["cleanliness"] += 1
    adult.memes["joy"] += 1
    world.say(
        f"In the end, {child.label} helped water the seedlings, shared the last bite of "
        f"{snack.label}, and watched the birds peck crumbs from the path."
    )
    world.say(
        f"The garden center smelled like wet leaves and potting soil, and {child.label} "
        f"left feeling proud, funny, and ready to come back."
    )


def tell(world: World, child: Entity, adult: Entity, snack: Entity) -> World:
    world.say(
        f"{child.label} came to {world.setting.place} with {adult.label} on a bright afternoon."
    )
    world.say(
        f"{child.label} loved the rows of herbs, pots, and baby tomato plants, because everything "
        f"looked like it was waiting to grow."
    )
    help_in_garden(world, child, adult)
    world.para()
    eat_matzo(world, child, snack)
    flashback(world, child, snack)
    world.say(
        f"{adult.label} laughed too and said it was a good thing the garden center had plenty of "
        f"soil, because the story of the flying crumbs had already become a family joke."
    )
    feed_birds(world, child, snack)
    world.para()
    settle_story(world, child, adult, snack)
    world.facts.update(child=child, adult=adult, snack=snack)
    return world


SETTINGS = {
    "garden_center": Setting(place="the garden center", afford_help=True, afford_eat=True, afford_feed_birds=True),
}

SNACKS = {
    "matzo": Snack(
        id="matzo",
        label="matzo",
        phrase="matzo crackers",
        crumbs="crumbly",
    ),
}

ANIMALS = {
    "rabbit": Animal(id="rabbit", type="rabbit", label="Ruby", traits=["curious", "gentle"]),
    "dog": Animal(id="dog", type="dog", label="Milo", traits=["bouncy", "helpful"]),
    "cat": Animal(id="cat", type="cat", label="Pippa", traits=["clever", "silly"]),
    "bird": Animal(id="bird", type="bird", label="Mabel", traits=["tiny", "watchful"]),
}

GROWNUPS = {
    "rabbit": Animal(id="adult_rabbit", type="rabbit", label="Aunt Juniper", traits=["patient"]),
    "dog": Animal(id="adult_dog", type="dog", label="Uncle Bram", traits=["patient"]),
    "cat": Animal(id="adult_cat", type="cat", label="Mrs. Thistle", traits=["patient"]),
}

NAMES = ["Ruby", "Milo", "Pippa", "Toby", "Nina", "Otis", "Benny", "Cora"]
TRAITS = ["curious", "cheerful", "silly", "gentle", "bouncy", "bright"]


@dataclass
class StoryParams:
    place: str
    child_type: str
    adult_name: str
    child_name: str
    snack: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story in a garden center with matzo, flashback, and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-type", choices=ANIMALS)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or "garden_center"
    child_type = getattr(args, "child_type", None) or rng.choice(list(ANIMALS))
    snack = getattr(args, "snack", None) or "matzo"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    child_name = getattr(args, "child_name", None) or _safe_lookup(ANIMALS, child_type).label
    adult_name = getattr(args, "adult_name", None) or _safe_lookup(GROWNUPS, child_type).label
    return StoryParams(
        place=place,
        child_type=child_type,
        adult_name=adult_name,
        child_name=child_name,
        snack=snack,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        memes={"joy": 0, "worry": 0, "pride": 0, "embarrassment": 0, "laughter": 0, "memory": 0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.child_type,
        label=params.adult_name,
    ))
    bird = world.add(Entity(
        id="birds",
        kind="character",
        type="bird",
        label="the birds",
        plural=True,
    ))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label=_safe_lookup(SNACKS, params.snack).label,
        phrase=_safe_lookup(SNACKS, params.snack).phrase,
        owner=child.id,
    ))
    tell(world, child, adult, snack)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    snack = _safe_fact(world, f, "snack")
    return [
        "Write a short animal story set in a garden center where matzo turns into a funny family memory.",
        f"Tell a gentle story about {child.label} at {world.setting.place} with {snack.label}, a flashback, and a happy ending.",
        "Write a child-friendly story in which a crumbly snack causes a comic memory and then becomes useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    snack: Entity = _safe_fact(world, f, "snack")
    return [
        QAItem(
            question=f"Where did {child.label} go with {adult.label}?",
            answer=f"{child.label} went to the garden center with {adult.label}.",
        ),
        QAItem(
            question=f"What snack was {child.label} carrying?",
            answer=f"{child.label} was carrying matzo, which is a very crumbly snack.",
        ),
        QAItem(
            question=f"Why did {child.label} laugh after eating the snack?",
            answer=(
                f"{child.label} remembered an older messy moment with the matzo crumbs, "
                f"and the flashback was so silly that it turned into a joke."
            ),
        ),
        QAItem(
            question=f"What did {child.label} do with the crumbs in the end?",
            answer=(
                f"{child.label} sprinkled the crumbs for the birds, so the matzo became "
                f"birdfeed instead of a mess."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garden center?",
            answer="A garden center is a place where people can buy plants, pots, soil, and things for gardening.",
        ),
        QAItem(
            question="What is matzo?",
            answer="Matzo is a flat, crisp bread that breaks easily into crumbs.",
        ),
        QAItem(
            question="Why can crumbs be messy?",
            answer="Crumbs can scatter onto clothes and the floor, so they are hard to keep neat.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_center", child_type="rabbit", adult_name="Aunt Juniper", child_name="Ruby", snack="matzo", trait="curious"),
    StoryParams(place="garden_center", child_type="dog", adult_name="Uncle Bram", child_name="Milo", snack="matzo", trait="bouncy"),
    StoryParams(place="garden_center", child_type="cat", adult_name="Mrs. Thistle", child_name="Pippa", snack="matzo", trait="silly"),
]


ASP_RULES = r"""
child(C).
adult(A).
snack(S).
at_garden_center(P) :- place(P).

crumbly(S) :- snack(S).
flashback(C) :- child(C), crumbly(snack).
humor(C) :- child(C), flashback(C).

crumbs(C) :- child(C), ate(C, snack), crumbly(snack).
birdfeed(C) :- crumbs(C), birds_nearby.
happy_end(C) :- humor(C), birdfeed(C).

#show flashback/1.
#show humor/1.
#show happy_end/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if pid == "garden_center":
            lines.append(asp.fact("at_garden_center", pid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for cid in ANIMALS:
        lines.append(asp.fact("child", cid))
    lines.append(asp.fact("birds_nearby"))
    lines.append(asp.fact("ate", "rabbit", "snack"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show flashback/1. #show humor/1. #show happy_end/1."))
    shown = set((s.name, tuple(getattr(a, "name", str(a)) for a in s.arguments)) for s in model)
    want = {("flashback", ("rabbit",)), ("humor", ("rabbit",)), ("happy_end", ("rabbit",))}
    if shown == want:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(shown))
    print("PY :", sorted(want))
    return 1


def asp_validity() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show flashback/1. #show humor/1. #show happy_end/1."))
    return sorted((s.name, tuple(getattr(a, "name", str(a)) for a in s.arguments)) for s in model)


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
        print(asp_program("#show flashback/1. #show humor/1. #show happy_end/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show flashback/1. #show humor/1. #show happy_end/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
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
            header = f"### {p.child_name}: matzo at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    return [
        QAItem(
            question=f"Where did {child.label} go with {adult.label}?",
            answer=f"{child.label} went to the garden center with {adult.label}.",
        ),
        QAItem(
            question=f"What snack was {child.label} carrying?",
            answer=f"{child.label} was carrying matzo, which is a very crumbly snack.",
        ),
        QAItem(
            question=f"Why did {child.label} laugh after the flashback?",
            answer=(
                f"{child.label} remembered a silly crumby moment from before, and that memory "
                f"made {child.pronoun('object')} laugh."
            ),
        ),
        QAItem(
            question=f"What happened to the matzo crumbs?",
            answer=f"{child.label} shared the matzo crumbs with the birds, so they became birdfeed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garden center?",
            answer="A garden center is a place where people can buy plants, pots, soil, and gardening supplies.",
        ),
        QAItem(
            question="What is matzo?",
            answer="Matzo is a flat, crisp bread that breaks easily into crumbs.",
        ),
        QAItem(
            question="Why is a flashback funny sometimes?",
            answer="A flashback can be funny when it reminds someone of an old mistake that is safe to laugh about now.",
        ),
    ]


if __name__ == "__main__":
    main()
