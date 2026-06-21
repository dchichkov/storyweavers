#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py
====================================================================

A standalone story world for a small fable-like domain:

Two little animals are gathering food for the cold season. One wants to save
time by making a jumble of dry food and juicy fruit in one container. Another
animal warns that the juice will spoil the dry food. Depending on who is
trusted, the warning is heeded at once or only after the first sticky drip.
Then the animals sort, dry, and share the food wisely, and the ending image
shows the storehouse made orderly again.

The world is constraint-checked. A story is only valid when:
- the chosen dry food is truly dry,
- the chosen juicy food is truly wet enough to cause trouble,
- the chosen fix is sensible and actually strong enough for the delay.

Run it
------
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py --all
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py --trace
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py --json
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py --asp
    python storyworlds/worlds/gpt-5.4/let_jumble_dialogue_happy_ending_fable.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"he"}
        female = {"she"}
        sex = self.attrs.get("sex", "")
        if sex in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if sex in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HeroSpec:
    id: str
    species: str
    title: str
    sex: str
    quick_trait: str
    careful_trait: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class DryFood:
    id: str
    label: str
    phrase: str
    plural: bool = True
    dryness: int = 3
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class JuicyFood:
    id: str
    label: str
    phrase: str
    juice: int = 2
    color: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    open_top: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_jumble_spoils(world: World) -> list[str]:
    basket = world.get("container")
    if basket.meters["jumbled"] < THRESHOLD or basket.meters["juice"] < THRESHOLD:
        return []
    sig = ("spoil", "container")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["sticky"] += 1
    basket.meters["risk"] += 1
    world.get("dry_food").meters["sticky"] += 1
    world.get("dry_food").meters["safe"] = 0.0
    for eid in ("quick_one", "careful_one"):
        world.get(eid).memes["worry"] += 1
    return ["__sticky__"]


def _r_sort_restores(world: World) -> list[str]:
    basket = world.get("container")
    if basket.meters["sorted"] < THRESHOLD:
        return []
    sig = ("restore", "container")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["risk"] = 0.0
    basket.meters["sticky"] = 0.0
    world.get("dry_food").meters["safe"] += 1
    world.get("juicy_food").meters["safe"] += 1
    for eid in ("quick_one", "careful_one"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="jumble_spoils", tag="physical", apply=_r_jumble_spoils),
    Rule(name="sort_restores", tag="physical", apply=_r_sort_restores),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def risk_exists(dry_food: DryFood, juicy_food: JuicyFood, container: Container) -> bool:
    return dry_food.dryness >= 2 and juicy_food.juice >= 2 and container.open_top


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def spoil_severity(juicy_food: JuicyFood, delay: int) -> int:
    return juicy_food.juice + delay


def is_saved(fix: Fix, juicy_food: JuicyFood, delay: int) -> bool:
    return fix.power >= spoil_severity(juicy_food, delay)


def trust_allows_warning(trust: int, carefulness: int) -> bool:
    return trust + carefulness >= 9


def predict_jumble(world: World) -> dict:
    sim = world.copy()
    sim.get("container").meters["jumbled"] += 1
    sim.get("container").meters["juice"] += float(sim.facts["juicy_food"].juice)
    propagate(sim, narrate=False)
    basket = sim.get("container")
    return {
        "sticky": basket.meters["sticky"] >= THRESHOLD,
        "risk": basket.meters["risk"],
    }


def introduce(world: World, quick_one: Entity, careful_one: Entity, container: Container) -> None:
    world.say(
        f"In a small hollow tree, {quick_one.id} the {quick_one.type} and "
        f"{careful_one.id} the {careful_one.type} were filling {container.phrase} for the cold days ahead."
    )
    world.say(
        f"{quick_one.id} was {quick_one.attrs['quick_trait']}, and {careful_one.id} was "
        f"{careful_one.attrs['careful_trait']}. They both wanted the winter shelf to look generous and full."
    )


def gather(world: World, quick_one: Entity, careful_one: Entity, dry_food: DryFood, juicy_food: JuicyFood) -> None:
    quick_one.memes["hope"] += 1
    careful_one.memes["hope"] += 1
    world.say(
        f"All morning they carried {dry_food.phrase} and {juicy_food.phrase}. "
        f"The dry food made a soft rustle, but the {juicy_food.color} fruit shone with juice."
    )


def tempt(world: World, quick_one: Entity, dry_food: DryFood, juicy_food: JuicyFood, container: Container) -> None:
    quick_one.memes["impatience"] += 1
    world.say(
        f'"Let us save time," said {quick_one.id}. "We can pour the {dry_food.label} and the '
        f'{juicy_food.label} into {container.phrase} and be done before sunset."'
    )
    world.say(
        f"The idea sounded neat for one blink, because one basket seemed easier than many little places."
    )


def warn(world: World, careful_one: Entity, dry_food: DryFood, juicy_food: JuicyFood) -> None:
    pred = predict_jumble(world)
    world.facts["predicted_risk"] = pred["risk"]
    careful_one.memes["care"] += 1
    world.say(
        f'"Do not let hurry make a jumble of things that need different care," said {careful_one.id}. '
        f'"If the {juicy_food.label} burst, their juice will creep into the {dry_food.label}, and our winter food will turn sticky."'
    )


def heed(world: World, quick_one: Entity, careful_one: Entity, fix: Fix) -> None:
    quick_one.memes["humility"] += 1
    world.say(
        f'{quick_one.id} lowered {quick_one.pronoun("possessive")} paws and listened. '
        f'"You are right," {quick_one.pronoun()} said. "I will not make the jumble after all."'
    )
    apply_fix(world, quick_one, careful_one, fix, delayed=False)


def defy(world: World, quick_one: Entity, careful_one: Entity, dry_food: DryFood, juicy_food: JuicyFood, container: Container) -> None:
    quick_one.memes["defiance"] += 1
    world.say(
        f'"Only for a moment," said {quick_one.id}. "Surely a little jumble can do no harm."'
    )
    world.say(
        f"Before {careful_one.id} could stop {quick_one.pronoun('object')}, {quick_one.pronoun()} tipped the "
        f"{juicy_food.label} and the {dry_food.label} into {container.label} together."
    )


def jumble(world: World, dry_food: DryFood, juicy_food: JuicyFood, container: Container) -> None:
    basket = world.get("container")
    basket.meters["jumbled"] += 1
    basket.meters["juice"] += float(juicy_food.juice)
    world.facts["jumbled"] = True
    propagate(world, narrate=False)
    world.say(
        f"At once the pretty heap sagged. A crushed {juicy_food.label[:-1] if juicy_food.label.endswith('s') else juicy_food.label} "
        f"left a bright smear, and the clean {dry_food.label} near it began to cling together."
    )


def notice(world: World, careful_one: Entity, quick_one: Entity, container: Container) -> None:
    careful_one.memes["worry"] += 1
    world.say(
        f'"Look," cried {careful_one.id}. "The sides of {container.label} are already sticky."'
    )
    world.say(
        f"{quick_one.id} stared at the mess and felt a hot pinch of shame."
    )


def apply_fix(world: World, quick_one: Entity, careful_one: Entity, fix: Fix, delayed: bool) -> None:
    basket = world.get("container")
    basket.meters["sorted"] += 1
    propagate(world, narrate=False)
    quick_one.memes["industry"] += 1
    careful_one.memes["industry"] += 1
    line = fix.text
    if delayed:
        world.say(
            f'"Then let us mend it while we still can," said {quick_one.id}.'
        )
    else:
        world.say(
            f'"Then let us do the wise thing first," said {quick_one.id}.'
        )
    world.say(line)
    world.facts["fix_used_text"] = fix.qa_text


def ending(world: World, quick_one: Entity, careful_one: Entity, dry_food: DryFood, juicy_food: JuicyFood, fix: Fix) -> None:
    quick_one.memes["joy"] += 1
    careful_one.memes["joy"] += 1
    world.say(
        f"By evening the shelf held neat stores: the {dry_food.label} dry, the {juicy_food.label} shining in their own place, "
        f"and not a drop wasted."
    )
    world.say(
        f'{fix.ending_text} "{careful_one.id} was right to speak, and {quick_one.id} was wise to listen at last," '
        f"said the old owl from the doorway."
    )
    world.say(
        "So the two little gatherers slept with easy hearts, and the hollow tree looked orderly enough for winter and kind enough for sharing."
    )


def tell(
    hero: HeroSpec,
    friend: HeroSpec,
    dry_food: DryFood,
    juicy_food: JuicyFood,
    container: Container,
    fix: Fix,
    delay: int,
    trust: int,
) -> World:
    world = World()
    quick_one = world.add(
        Entity(
            id=hero.title,
            kind="character",
            type=hero.species,
            role="quick_one",
            attrs={"sex": hero.sex, "quick_trait": hero.quick_trait},
        )
    )
    careful_one = world.add(
        Entity(
            id=friend.title,
            kind="character",
            type=friend.species,
            role="careful_one",
            attrs={"sex": friend.sex, "careful_trait": friend.careful_trait},
        )
    )
    basket = world.add(Entity(id="container", type="container", label=container.label))
    dry_ent = world.add(Entity(id="dry_food", type="food", label=dry_food.label))
    juicy_ent = world.add(Entity(id="juicy_food", type="food", label=juicy_food.label))
    owl = world.add(Entity(id="Owl", kind="character", type="owl", role="witness", attrs={"sex": ""}))

    dry_ent.meters["safe"] = 1.0
    juicy_ent.meters["safe"] = 1.0
    basket.meters["jumbled"] = 0.0
    basket.meters["juice"] = 0.0
    basket.meters["sticky"] = 0.0
    basket.meters["risk"] = 0.0
    basket.meters["sorted"] = 0.0
    quick_one.memes["worry"] = 0.0
    careful_one.memes["worry"] = 0.0

    world.facts.update(
        hero=quick_one,
        friend=careful_one,
        hero_spec=hero,
        friend_spec=friend,
        dry_food=dry_food,
        juicy_food=juicy_food,
        container_cfg=container,
        fix=fix,
        delay=delay,
        trust=trust,
        jumbled=False,
    )

    introduce(world, quick_one, careful_one, container)
    gather(world, quick_one, careful_one, dry_food, juicy_food)

    world.para()
    tempt(world, quick_one, dry_food, juicy_food, container)
    warn(world, careful_one, dry_food, juicy_food)

    if trust_allows_warning(trust, 3):
        heed(world, quick_one, careful_one, fix)
        outcome = "heeded"
    else:
        defy(world, quick_one, careful_one, dry_food, juicy_food, container)
        world.para()
        jumble(world, dry_food, juicy_food, container)
        notice(world, careful_one, quick_one, container)
        world.para()
        if not is_saved(fix, juicy_food, delay):
            raise StoryError(
                f"(No story: {fix.id} is too weak to save {juicy_food.label} after delay {delay}. "
                f"Choose a stronger fix or a smaller delay.)"
            )
        apply_fix(world, quick_one, careful_one, fix, delayed=True)
        outcome = "mended"

    world.para()
    ending(world, quick_one, careful_one, dry_food, juicy_food, fix)

    world.facts.update(
        outcome=outcome,
        saved=is_saved(fix, juicy_food, delay),
        sticky=world.get("container").meters["sticky"] >= THRESHOLD,
        sorted=world.get("container").meters["sorted"] >= THRESHOLD,
    )
    return world


HEROES = {
    "squirrel": HeroSpec(
        id="squirrel",
        species="squirrel",
        title="Pip",
        sex="he",
        quick_trait="quick-fingered",
        careful_trait="steady",
        tags={"squirrel", "gathering"},
    ),
    "mouse": HeroSpec(
        id="mouse",
        species="mouse",
        title="Mina",
        sex="she",
        quick_trait="nimble",
        careful_trait="thoughtful",
        tags={"mouse", "gathering"},
    ),
    "rabbit": HeroSpec(
        id="rabbit",
        species="rabbit",
        title="Tavi",
        sex="he",
        quick_trait="springy",
        careful_trait="patient",
        tags={"rabbit", "gathering"},
    ),
}

FRIENDS = {
    "wren": HeroSpec(
        id="wren",
        species="wren",
        title="Wren",
        sex="she",
        quick_trait="bright",
        careful_trait="careful",
        tags={"bird", "warning"},
    ),
    "tortoise": HeroSpec(
        id="tortoise",
        species="tortoise",
        title="Toma",
        sex="he",
        quick_trait="quiet",
        careful_trait="wise",
        tags={"tortoise", "warning"},
    ),
    "sparrow": HeroSpec(
        id="sparrow",
        species="sparrow",
        title="Suri",
        sex="she",
        quick_trait="light",
        careful_trait="watchful",
        tags={"bird", "warning"},
    ),
}

DRY_FOODS = {
    "acorns": DryFood(
        id="acorns",
        label="acorns",
        phrase="a pile of acorns",
        plural=True,
        dryness=3,
        tags={"acorns", "dry_food"},
    ),
    "wheat": DryFood(
        id="wheat",
        label="wheat seeds",
        phrase="a scoop of wheat seeds",
        plural=True,
        dryness=3,
        tags={"seeds", "dry_food"},
    ),
    "nuts": DryFood(
        id="nuts",
        label="hazelnuts",
        phrase="a little hill of hazelnuts",
        plural=True,
        dryness=3,
        tags={"nuts", "dry_food"},
    ),
}

JUICY_FOODS = {
    "berries": JuicyFood(
        id="berries",
        label="berries",
        phrase="a bowl of blackberries",
        juice=3,
        color="purple",
        tags={"berries", "fruit"},
    ),
    "plums": JuicyFood(
        id="plums",
        label="plums",
        phrase="three small plums",
        juice=2,
        color="blue",
        tags={"plums", "fruit"},
    ),
    "cherries": JuicyFood(
        id="cherries",
        label="cherries",
        phrase="a branch of cherries",
        juice=3,
        color="red",
        tags={"cherries", "fruit"},
    ),
}

CONTAINERS = {
    "basket": Container(
        id="basket",
        label="the willow basket",
        phrase="a willow basket",
        open_top=True,
        tags={"basket"},
    ),
    "tray": Container(
        id="tray",
        label="the bark tray",
        phrase="a bark tray",
        open_top=True,
        tags={"tray"},
    ),
    "leaf_bowl": Container(
        id="leaf_bowl",
        label="the leaf bowl",
        phrase="a broad leaf bowl",
        open_top=True,
        tags={"bowl"},
    ),
}

FIXES = {
    "separate_jars": Fix(
        id="separate_jars",
        sense=3,
        power=5,
        text="Together they set the fruit into little clay jars and spread the dry food on a clean shelf of bark, where nothing wet could touch it.",
        qa_text="They separated the juicy fruit into little jars and kept the dry food on its own dry shelf.",
        ending_text="The jars gleamed in a row, and the bark shelf smelled sweet and clean.",
        tags={"jars", "sorting"},
    ),
    "drying_cloth": Fix(
        id="drying_cloth",
        sense=2,
        power=4,
        text="Together they lifted everything onto a sunny cloth, wiped away the juice, and sorted the food into two tidy heaps before the damp could spread.",
        qa_text="They used a sunny drying cloth, wiped away the juice, and sorted the food into two heaps.",
        ending_text="The cloth fluttered on the branch, and the sorted food looked almost like a little festival.",
        tags={"cloth", "sorting", "sun"},
    ),
    "blow_on_it": Fix(
        id="blow_on_it",
        sense=1,
        power=1,
        text="They leaned close and blew on the sticky food, hoping the damp would simply disappear.",
        qa_text="They only blew on the sticky food and hoped it would dry.",
        ending_text="The basket still looked untidy.",
        tags={"weak_fix"},
    ),
}


@dataclass
class StoryParams:
    hero: str
    friend: str
    dry_food: str
    juicy_food: str
    container: str
    fix: str
    delay: int = 0
    trust: int = 6
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "berries": [
        (
            "Why should juicy berries be kept away from dry seeds or nuts?",
            "Juicy berries can burst and leak. Their juice makes dry food sticky, and sticky stores do not keep well."
        )
    ],
    "plums": [
        (
            "Why can plums make a basket messy?",
            "Plums are soft and full of juice. If they are squeezed beside dry food, they can smear and drip."
        )
    ],
    "cherries": [
        (
            "Why can cherries stain things?",
            "Cherries have dark, sweet juice. When they split, the juice can leave bright stains and sticky spots."
        )
    ],
    "sorting": [
        (
            "Why is it wise to sort food instead of making a jumble?",
            "Sorting keeps each kind of food in the place that suits it best. Dry things stay dry, juicy things stay contained, and less is spoiled."
        )
    ],
    "jars": [
        (
            "What is good about storing fruit in little jars?",
            "Jars keep juicy fruit together so the juice stays in one place. That helps the fruit stay tidy and keeps other food dry."
        )
    ],
    "cloth": [
        (
            "What does a drying cloth help with?",
            "A drying cloth soaks up dampness and gives wet things a place to air out. That can stop a small mess from spreading."
        )
    ],
    "winter": [
        (
            "Why do animals in fables gather food for winter?",
            "Winter can be cold and lean, so gathered food means they will have something ready later. A careful storehouse is a sign of planning ahead."
        )
    ],
}
KNOWLEDGE_ORDER = ["winter", "berries", "plums", "cherries", "sorting", "jars", "cloth"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for hero in HEROES:
        for friend in FRIENDS:
            if hero == friend:
                continue
            for dry_food_id, dry_food in DRY_FOODS.items():
                for juicy_food_id, juicy_food in JUICY_FOODS.items():
                    for container_id, container in CONTAINERS.items():
                        if risk_exists(dry_food, juicy_food, container):
                            combos.append((hero, friend, dry_food_id, juicy_food_id, container_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    dry_food = f["dry_food"]
    juicy_food = f["juicy_food"]
    fix = f["fix"]
    outcome = f["outcome"]
    if outcome == "heeded":
        middle = "the warning is believed before the mistake happens"
    else:
        middle = "a sticky mistake happens first, and then it is mended"
    return [
        f'Write a short fable with dialogue that includes the words "let" and "jumble". Two small animals are storing {dry_food.label} and {juicy_food.label}, and {middle}.',
        f"Tell a child-friendly fable about {hero.id} and {friend.id}: one wants to hurry, one warns that juicy fruit should not be mixed with dry food, and they end happily by using {fix.id.replace('_', ' ')}.",
        f"Write a gentle animal story with speaking characters, a tidy moral turn, and a happy ending image of a winter shelf set right."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    dry_food = f["dry_food"]
    juicy_food = f["juicy_food"]
    fix = f["fix"]
    container = f["container_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type}. They were gathering food for cold days and trying to keep their little storehouse in good order."
        ),
        (
            f"What problem did {friend.id} warn about?",
            f"{friend.id} warned that the juicy {juicy_food.label} could burst and leak into the dry {dry_food.label}. That would turn a tidy store into a sticky jumble."
        ),
        (
            f"Why did {hero.id} want to use {container.phrase} for everything?",
            f"{hero.id} wanted to save time by putting everything into one place. One basket seemed quicker, even though it was not wise."
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"Did {hero.id} listen right away?",
                f"Yes. {hero.id} listened before making the mistake and chose the wiser plan instead. The happy ending came because the warning was trusted in time."
            )
        )
    else:
        qa.append(
            (
                f"What happened after {hero.id} made the jumble?",
                f"A crushed {juicy_food.label[:-1] if juicy_food.label.endswith('s') else juicy_food.label} left juice in the basket, and the dry {dry_food.label} began to cling together. Seeing the sticky mess helped {hero.id} understand why the warning had mattered."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They worked together instead of blaming each other. {f['fix_used_text']} That fixed the danger and left the winter food safe again."
        )
    )
    qa.append(
        (
            "What is the lesson of the fable?",
            "Do not let hurry rule your hands when careful work is needed. A small pause for wisdom can save a great deal of trouble."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"winter", "sorting"}
    tags |= set(f["juicy_food"].tags)
    tags |= set(f["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="squirrel",
        friend="wren",
        dry_food="acorns",
        juicy_food="berries",
        container="basket",
        fix="separate_jars",
        delay=0,
        trust=7,
    ),
    StoryParams(
        hero="mouse",
        friend="tortoise",
        dry_food="wheat",
        juicy_food="plums",
        container="tray",
        fix="drying_cloth",
        delay=1,
        trust=4,
    ),
    StoryParams(
        hero="rabbit",
        friend="sparrow",
        dry_food="nuts",
        juicy_food="cherries",
        container="leaf_bowl",
        fix="separate_jars",
        delay=1,
        trust=5,
    ),
]


def explain_rejection(dry_food: DryFood, juicy_food: JuicyFood, container: Container) -> str:
    if not container.open_top:
        return f"(No story: {container.label} would hide the problem instead of creating a visible jumble.)"
    if dry_food.dryness < 2:
        return f"(No story: {dry_food.label} are not dry enough for this caution to matter.)"
    if juicy_food.juice < 2:
        return f"(No story: {juicy_food.label} are not juicy enough to threaten the dry food.)"
    return "(No story: this combination does not create a believable storage problem.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if trust_allows_warning(params.trust, 3):
        return "heeded"
    if is_saved(FIXES[params.fix], JUICY_FOODS[params.juicy_food], params.delay):
        return "mended"
    return "lost"


ASP_RULES = r"""
hazard(D, J, C) :- dry_food(D), juicy_food(J), container(C),
                   dryness(D, DD), DD >= 2,
                   juice(J, JJ), JJ >= 2,
                   open_top(C).

sensible(Fx) :- fix(Fx), sense(Fx, S), sense_min(M), S >= M.

valid(H, Fr, D, J, C) :- hero(H), friend(Fr), H != Fr, hazard(D, J, C).

heeded :- trust(T), care_threshold(C), T + C >= 9.
severity(V) :- chosen_juicy(J), juice(J, JJ), delay(D), V = JJ + D.
saved :- chosen_fix(Fx), power(Fx, P), severity(V), P >= V.

outcome(heeded) :- heeded.
outcome(mended) :- not heeded, saved.
outcome(lost) :- not heeded, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for friend_id in FRIENDS:
        lines.append(asp.fact("friend", friend_id))
    for dry_food_id, dry_food in DRY_FOODS.items():
        lines.append(asp.fact("dry_food", dry_food_id))
        lines.append(asp.fact("dryness", dry_food_id, dry_food.dryness))
    for juicy_food_id, juicy_food in JUICY_FOODS.items():
        lines.append(asp.fact("juicy_food", juicy_food_id))
        lines.append(asp.fact("juice", juicy_food_id, juicy_food.juice))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        if container.open_top:
            lines.append(asp.fact("open_top", container_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("care_threshold", 3))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_juicy", params.juicy_food),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {fix.id for fix in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        _smoke_emit(smoke)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: do not let hurry make a jumble."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--dry-food", dest="dry_food", choices=DRY_FOODS)
    ap.add_argument("--juicy-food", dest="juicy_food", choices=JUICY_FOODS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dry_food and args.juicy_food and args.container:
        if not risk_exists(DRY_FOODS[args.dry_food], JUICY_FOODS[args.juicy_food], CONTAINERS[args.container]):
            raise StoryError(explain_rejection(DRY_FOODS[args.dry_food], JUICY_FOODS[args.juicy_food], CONTAINERS[args.container]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.friend is None or combo[1] == args.friend)
        and (args.dry_food is None or combo[2] == args.dry_food)
        and (args.juicy_food is None or combo[3] == args.juicy_food)
        and (args.container is None or combo[4] == args.container)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero, friend, dry_food, juicy_food, container = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(fix.id for fix in sensible_fixes()))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    trust = args.trust if args.trust is not None else rng.randint(3, 9)

    if not trust_allows_warning(trust, 3) and not is_saved(FIXES[fix], JUICY_FOODS[juicy_food], delay):
        # Keep random generation in the happy domain.
        candidates = [
            fid for fid in sorted(f.id for f in sensible_fixes())
            if is_saved(FIXES[fid], JUICY_FOODS[juicy_food], delay)
        ]
        if not candidates:
            raise StoryError("(No sensible fix can save this story with the chosen delay.)")
        fix = rng.choice(candidates)

    return StoryParams(
        hero=hero,
        friend=friend,
        dry_food=dry_food,
        juicy_food=juicy_food,
        container=container,
        fix=fix,
        delay=delay,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")
    if params.dry_food not in DRY_FOODS:
        raise StoryError(f"(Unknown dry food: {params.dry_food})")
    if params.juicy_food not in JUICY_FOODS:
        raise StoryError(f"(Unknown juicy food: {params.juicy_food})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not risk_exists(DRY_FOODS[params.dry_food], JUICY_FOODS[params.juicy_food], CONTAINERS[params.container]):
        raise StoryError(explain_rejection(DRY_FOODS[params.dry_food], JUICY_FOODS[params.juicy_food], CONTAINERS[params.container]))
    if not trust_allows_warning(params.trust, 3) and not is_saved(FIXES[params.fix], JUICY_FOODS[params.juicy_food], params.delay):
        raise StoryError(
            f"(No story: fix '{params.fix}' cannot save {params.juicy_food} after delay {params.delay}.)"
        )

    world = tell(
        hero=HEROES[params.hero],
        friend=FRIENDS[params.friend],
        dry_food=DRY_FOODS[params.dry_food],
        juicy_food=JUICY_FOODS[params.juicy_food],
        container=CONTAINERS[params.container],
        fix=FIXES[params.fix],
        delay=params.delay,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (hero, friend, dry_food, juicy_food, container) combos:\n")
        for hero, friend, dry_food, juicy_food, container in combos:
            print(f"  {hero:8} {friend:9} {dry_food:8} {juicy_food:8} {container}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero} with {p.friend}: {p.dry_food} + {p.juicy_food} "
                f"in {p.container} ({outcome_of(p)}, {p.fix})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
