#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py
==============================================================

A standalone story world for a small tall-tale misunderstanding story.

Premise
-------
In an oversized frontier town, a loud *clack clack* rolls across the place.
The grown-ups jump to a wild conclusion about what is making the sound.
One bold child goes to look, finds the ordinary cause behind the big rumor,
and fixes the real problem so the town can laugh and calm down.

This world models:
- a physical sound source with meters like noise and wobble
- a town whose fear and confusion rise when the clack goes unexplained
- a misunderstanding that must be plausible for the chosen source
- a sensible remedy that fits the real source

Run it
------
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py --place ford --source ferry_chain
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py --source windmill_tail --mistake giant_boots
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py --source seed_wagon --mistake giant_beaver
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/clack_misunderstanding_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import io
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mayor_f"}
        male = {"boy", "man", "father", "mayor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    wide_claim: str
    landmark: str
    affords: set[str] = field(default_factory=set)
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
class Source:
    id: str
    label: str
    place_word: str
    clack_line: str
    clue: str
    reveal: str
    height: str
    remedy: str
    mistake: str
    aftermath: str
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
class Mistake:
    id: str
    label: str
    rumor: str
    worry: str
    reason: str
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
class Remedy:
    id: str
    label: str
    action: str
    result: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_rumor(world: World) -> list[str]:
    src = world.get("source")
    town = world.get("town")
    if src.meters["noise"] < THRESHOLD:
        return []
    if ("rumor",) in world.fired:
        return []
    world.fired.add(("rumor",))
    town.memes["fear"] += 1
    town.memes["confusion"] += 1
    world.facts["heard_clack"] = True
    return ["__rumor__"]


def _r_calm(world: World) -> list[str]:
    src = world.get("source")
    town = world.get("town")
    if src.meters["noise"] >= THRESHOLD:
        return []
    if town.memes["fear"] <= 0 and town.memes["confusion"] <= 0:
        return []
    if ("calm",) in world.fired:
        return []
    world.fired.add(("calm",))
    town.memes["fear"] = 0.0
    town.memes["confusion"] = 0.0
    town.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="rumor", tag="social", apply=_r_rumor),
    Rule(name="calm", tag="social", apply=_r_calm),
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


PLACES = {
    "valley": Place(
        id="valley",
        label="Cactus Valley",
        wide_claim="where even the fence posts looked tall enough to wear hats",
        landmark="the flour mill on the ridge",
        affords={"windmill_tail", "seed_wagon"},
        tags={"frontier"},
    ),
    "prairie": Place(
        id="prairie",
        label="Sagebrush Prairie",
        wide_claim="so broad a sneeze at one end could scare rabbits at the other",
        landmark="the road by the grain shed",
        affords={"windmill_tail", "seed_wagon"},
        tags={"frontier"},
    ),
    "ford": Place(
        id="ford",
        label="Cottonwood Ford",
        wide_claim="where the river ran wide enough to practice its elbows",
        landmark="the ferry dock under the cottonwoods",
        affords={"ferry_chain"},
        tags={"river"},
    ),
}

SOURCES = {
    "windmill_tail": Source(
        id="windmill_tail",
        label="the windmill's loose tail board",
        place_word="up on the mill",
        clack_line="Whenever the wind shoved the mill around, the tail board flew sideways and came back with a hard clack against the frame.",
        clue="The sound came from high in the air and kept a steady beat with the gusts.",
        reveal="There was no giant at all, only a windmill tail wobbling like a loose tooth in a windy mouth.",
        height="higher than three haystacks standing on one another's shoulders",
        remedy="tighten_tail",
        mistake="giant_boots",
        aftermath="After that, the mill turned as smooth as a spoon in honey.",
        tags={"windmill", "sound"},
    ),
    "seed_wagon": Source(
        id="seed_wagon",
        label="Old Juniper Jim's seed wagon with a dry axle",
        place_word="down on the road",
        clack_line="Every time the wagon wheel rolled over a rut, the dry axle gave a clack loud enough to startle dust off a cactus.",
        clue="The noise moved along the road and smelled of grease that should have been there but wasn't.",
        reveal="There was no outlaw raid at all, only a wagon complaining because its axle had gone as dry as toast.",
        height="bigger than a porch and fussier than a rooster before sunrise",
        remedy="grease_axle",
        mistake="outlaw_train",
        aftermath="Then the wagon rolled with a low hum instead of a sharp complaint.",
        tags={"wagon", "sound"},
    ),
    "ferry_chain": Source(
        id="ferry_chain",
        label="the ferry chain slapping the dock post",
        place_word="by the water",
        clack_line="Each shove of the river swung the chain loose, and it came back with a clack that skipped over the water like a flat stone.",
        clue="The sound came from the dock and landed in splashes between the cottonwoods.",
        reveal="There was no giant beaver at all, only a ferry chain knocking the post every time the river nudged it.",
        height="long enough to make the river seem as if it wore suspenders",
        remedy="rope_chain",
        mistake="giant_beaver",
        aftermath="Soon the ferry bobbed quietly, and the dock just creaked like any honest dock.",
        tags={"river", "sound"},
    ),
}

MISTAKES = {
    "giant_boots": Mistake(
        id="giant_boots",
        label="a hill giant in wooden boots",
        rumor='“A hill giant is stomping this way in wooden boots!”',
        worry="Folks snatched pies off windowsills and peered at the ridge.",
        reason="That rumor only makes sense when the sound comes from high up and thumps in a marching rhythm.",
        tags={"giant", "misunderstanding"},
    ),
    "outlaw_train": Mistake(
        id="outlaw_train",
        label="an outlaw wagon train",
        rumor='“It is an outlaw wagon train, coming to rattle every lock in town!”',
        worry="Storekeepers counted their biscuit tins and shut their doors half an inch tighter.",
        reason="That rumor fits a clack that rolls along the road as if wheels are carrying it.",
        tags={"outlaws", "misunderstanding"},
    ),
    "giant_beaver": Mistake(
        id="giant_beaver",
        label="a giant beaver chewing the dock",
        rumor='“A giant beaver is gnawing the dock down to toothpicks!”',
        worry="The ferry man stared at the river and held his hat with both hands.",
        reason="That rumor belongs to the water, where a sharp knock can sound like big teeth on wet wood.",
        tags={"beaver", "misunderstanding"},
    ),
}

REMEDIES = {
    "tighten_tail": Remedy(
        id="tighten_tail",
        label="a wrench and two brave turns",
        action="climbed the ladder, braced against the wind, and gave the tail bolts two brave turns with a wrench",
        result="The board quit flying loose, and the next gust spun past without a single clack.",
        qa_text="tightened the loose tail board with a wrench",
        tags={"wrench", "fix"},
    ),
    "grease_axle": Remedy(
        id="grease_axle",
        label="a bucket of axle grease",
        action="ducked under the wagon and painted the axle with a shine of grease",
        result="The wheel stopped protesting, and the wagon rolled on with only a soft wooden rumble.",
        qa_text="greased the wagon axle so it would stop clacking",
        tags={"grease", "fix"},
    ),
    "rope_chain": Remedy(
        id="rope_chain",
        label="a rope wrap on the chain",
        action="looped a thick rope around the chain where it slapped the post and tied it snug",
        result="The chain still moved, but it no longer smacked the wood, so the river sounded peaceful again.",
        qa_text="wrapped the chain with rope so it would stop hitting the dock",
        tags={"rope", "fix"},
    ),
}

GIRL_NAMES = ["Mira", "Tess", "June", "Della", "Ruth", "Nell"]
BOY_NAMES = ["Boone", "Eli", "Wade", "Jasper", "Cal", "Toby"]
TRAITS = ["bold", "steady", "sharp-eyed", "cheerful", "fearless", "quick-thinking"]


def source_fits(place_id: str, source_id: str) -> bool:
    return source_id in PLACES[place_id].affords


def misunderstanding_fits(source_id: str, mistake_id: str) -> bool:
    return SOURCES[source_id].mistake == mistake_id


def remedy_fits(source_id: str, remedy_id: str) -> bool:
    return SOURCES[source_id].remedy == remedy_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for source_id in SOURCES:
            if not source_fits(place_id, source_id):
                continue
            for mistake_id in MISTAKES:
                if not misunderstanding_fits(source_id, mistake_id):
                    continue
                for remedy_id in REMEDIES:
                    if remedy_fits(source_id, remedy_id):
                        combos.append((place_id, source_id, mistake_id, remedy_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str = "valley"
    source: str = "windmill_tail"
    mistake: str = "giant_boots"
    remedy: str = "tighten_tail"
    hero: str = "Mira"
    gender: str = "girl"
    mayor: str = "Mayor Peg"
    trait: str = "bold"
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


def explain_source_place(place_id: str, source_id: str) -> str:
    return (
        f"(No story: {SOURCES[source_id].label} does not belong in {PLACES[place_id].label}. "
        f"That place does not afford that source of clack.)"
    )


def explain_mistake(source_id: str, mistake_id: str) -> str:
    return (
        f"(No story: mistaking {SOURCES[source_id].label} for {MISTAKES[mistake_id].label} "
        f"does not fit the clues of the sound. {MISTAKES[mistake_id].reason})"
    )


def explain_remedy(source_id: str, remedy_id: str) -> str:
    return (
        f"(No story: {REMEDIES[remedy_id].label} would not fix {SOURCES[source_id].label}. "
        f"A tall tale can be big, but the repair still has to match the real cause.)"
    )


def opening(world: World, hero: Entity, mayor: Entity, place: Place) -> None:
    world.say(
        f"In {place.label}, {place.wide_claim}, lived {hero.id}, a {hero.traits[0]} "
        f"young {hero.type} who could hear trouble before most folks heard their own names."
    )
    world.say(
        f"The town mayor, {mayor.id}, said {hero.id} had ears so sharp {hero.pronoun()} "
        f"could count raindrops on a hat brim."
    )


def first_clack(world: World, hero: Entity, source: Source, place: Place) -> None:
    src = world.get("source")
    src.meters["noise"] = 1.0
    src.meters["wobble"] = 1.0
    src.attrs["revealed"] = False
    world.say(
        f"One bright morning, a clack came from {place.landmark}, then another, then a whole string of them."
    )
    world.say(source.clack_line)
    propagate(world, narrate=False)
    hero.memes["alert"] += 1


def rumor(world: World, mayor: Entity, mistake: Mistake) -> None:
    town = world.get("town")
    town.attrs["mistake"] = mistake.id
    world.facts["rumor_spoken"] = mistake.rumor
    world.say(f"{mayor.id} heard the racket and cried, {mistake.rumor}")
    world.say(mistake.worry)


def investigate(world: World, hero: Entity, source: Source) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'But {hero.id} tipped back {hero.pronoun("possessive")} hat and listened again. '
        f'"That does not sound right," {hero.pronoun()} said. '
        f"{source.clue}"
    )
    world.say(
        f"So {hero.pronoun()} strode off toward the noise in steps so long the dust had to jog to keep up."
    )


def reveal(world: World, hero: Entity, source: Source, mistake: Mistake) -> None:
    src = world.get("source")
    src.attrs["revealed"] = True
    world.facts["investigated"] = True
    world.say(
        f"When {hero.id} reached the spot, {hero.pronoun()} found the truth at once. {source.reveal}"
    )
    world.say(
        f"{hero.id} laughed so kindly even the rumor seemed less silly, because {MISTAKES[mistake.id].label} "
        f"had only been a misunderstanding grown fat on echoes."
    )


def repair(world: World, hero: Entity, source: Source, remedy: Remedy) -> None:
    src = world.get("source")
    world.say(
        f"Being the sort of child who never left a real problem wobbling, {hero.id} {remedy.action}."
    )
    src.meters["noise"] = 0.0
    src.meters["wobble"] = 0.0
    hero.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(remedy.result)
    world.say(source.aftermath)
    world.facts["fixed"] = True


def ending(world: World, hero: Entity, mayor: Entity, mistake: Mistake, place: Place) -> None:
    town = world.get("town")
    hero.memes["joy"] += 1
    town.memes["trust"] += 1
    world.say(
        f"By suppertime, {mayor.id} was laughing with everyone else and telling the tale smaller each time {mayor.pronoun()} told it."
    )
    world.say(
        f'“Next time we hear a clack in {place.label},” {mayor.pronoun()} said, '
        f'“we will look before we leap.”'
    )
    world.say(
        f"And {hero.id} walked home under a sky wide as a county fair, while the whole town listened to the peaceful quiet and felt proud it had traded {mistake.label} for the plain truth."
    )


def tell(
    place: Place,
    source_cfg: Source,
    mistake_cfg: Mistake,
    remedy_cfg: Remedy,
    hero_name: str = "Mira",
    gender: str = "girl",
    mayor_name: str = "Mayor Peg",
    trait: str = "bold",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"heard_first": False},
            tags={"hero"},
        )
    )
    mayor_type = "mayor_f" if "Peg" in mayor_name or "Mae" in mayor_name or "Belle" in mayor_name else "mayor_m"
    mayor = world.add(
        Entity(
            id=mayor_name,
            kind="character",
            type=mayor_type,
            label="the mayor",
            role="mayor",
            attrs={"worried": False},
            tags={"mayor"},
        )
    )
    town = world.add(
        Entity(
            id="town",
            kind="thing",
            type="town",
            label=place.label,
            role="town",
            attrs={"mistake": ""},
            tags={"town"},
        )
    )
    src = world.add(
        Entity(
            id="source",
            kind="thing",
            type="source",
            label=source_cfg.label,
            role="source",
            attrs={"revealed": False},
            tags=set(source_cfg.tags),
        )
    )

    world.facts.update(
        place=place,
        source_cfg=source_cfg,
        mistake_cfg=mistake_cfg,
        remedy_cfg=remedy_cfg,
        hero=hero,
        mayor=mayor,
        heard_clack=False,
        rumor_spoken="",
        investigated=False,
        fixed=False,
    )

    opening(world, hero, mayor, place)
    world.para()
    first_clack(world, hero, source_cfg, place)
    rumor(world, mayor, mistake_cfg)
    world.para()
    investigate(world, hero, source_cfg)
    reveal(world, hero, source_cfg, mistake_cfg)
    world.para()
    repair(world, hero, source_cfg, remedy_cfg)
    ending(world, hero, mayor, mistake_cfg, place)

    world.facts.update(
        source=src,
        town=town,
        peaceful=src.meters["noise"] < THRESHOLD,
        misunderstanding_cleared=town.memes["confusion"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "windmill": [
        (
            "What does a windmill do?",
            "A windmill uses the wind to turn big blades. It can grind grain or pump water when its parts are working properly.",
        )
    ],
    "wagon": [
        (
            "Why does a wagon axle need grease?",
            "Grease helps the wheel turn smoothly. Without it, the wood and metal can scrape and make loud noises.",
        )
    ],
    "river": [
        (
            "Why do sounds carry over water?",
            "Open water gives sound fewer things to bump into and lose energy on. That can make a knock or shout seem louder and farther away.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is true but gets it wrong. Looking carefully and listening well can help fix it.",
        )
    ],
    "wrench": [
        (
            "What is a wrench for?",
            "A wrench is a tool for turning nuts and bolts. It helps tighten loose parts so they do not wobble.",
        )
    ],
    "grease": [
        (
            "What does grease do on a wheel?",
            "Grease makes rubbing parts slide more easily. That lowers squeaks, groans, and sharp clacks.",
        )
    ],
    "rope": [
        (
            "Why might rope make a chain quieter?",
            "A rope wrap can soften a hard hit. When the chain bumps the wood through rope instead of bare metal, the sound is smaller.",
        )
    ],
}
KNOWLEDGE_ORDER = ["misunderstanding", "windmill", "wagon", "river", "wrench", "grease", "rope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    source = f["source_cfg"]
    mistake = f["mistake_cfg"]
    return [
        f'Write a short tall tale for a 3-to-5-year-old that includes the word "clack" and turns on a misunderstanding.',
        f"Tell a frontier-style tall tale where {hero.id} hears a clack in {place.label} and finds out that {mistake.label} was only a misunderstanding.",
        f"Write a gentle exaggerated story in which a whole town guesses wrong about {source.label}, and one sharp child discovers the true cause.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mayor = f["mayor"]
    place = f["place"]
    source = f["source_cfg"]
    mistake = f["mistake_cfg"]
    remedy = f["remedy_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.traits[0]} young {hero.type}, and the people of {place.label}. The mayor and the whole town join in once the clack starts.",
        ),
        (
            "What misunderstanding did the town have?",
            f"The town thought the sound was {mistake.label}. They guessed too quickly because the clack sounded big and strange before anyone checked the real cause.",
        ),
        (
            f"Why did {hero.id} not believe the rumor right away?",
            f"{hero.id} listened carefully to the clack and noticed a clue in how it sounded. {source.clue}",
        ),
        (
            f"What was really making the clack?",
            f"The real cause was {source.label}. The story turns because the scary idea was only a misunderstanding, not a real danger.",
        ),
        (
            f"How did {hero.id} fix the problem?",
            f"{hero.id} {remedy.qa_text}. That stopped the clack, so the town could hear that the trouble had been ordinary all along.",
        ),
        (
            "How did the story end?",
            f"It ended with the town calm again and laughing at its mistake. Even {mayor.id} admitted they should look before they leap.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    source = f["source_cfg"]
    remedy = f["remedy_cfg"]
    tags = {"misunderstanding"} | set(source.tags) | set(remedy.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="valley",
        source="windmill_tail",
        mistake="giant_boots",
        remedy="tighten_tail",
        hero="Mira",
        gender="girl",
        mayor="Mayor Peg",
        trait="sharp-eyed",
    ),
    StoryParams(
        place="prairie",
        source="seed_wagon",
        mistake="outlaw_train",
        remedy="grease_axle",
        hero="Boone",
        gender="boy",
        mayor="Mayor Buck",
        trait="steady",
    ),
    StoryParams(
        place="ford",
        source="ferry_chain",
        mistake="giant_beaver",
        remedy="rope_chain",
        hero="June",
        gender="girl",
        mayor="Mayor Mae",
        trait="fearless",
    ),
]


ASP_RULES = r"""
fits_place(P,S) :- affords(P,S).
fits_mistake(S,M) :- actual_mistake(S,M).
fits_remedy(S,R) :- actual_remedy(S,R).

valid(P,S,M,R) :- place(P), source(S), mistake(M), remedy(R),
                  fits_place(P,S), fits_mistake(S,M), fits_remedy(S,R).

heard_clack :- chosen_source(S), source(S).
town_fears  :- heard_clack.
misunderstanding :- town_fears, chosen_mistake(M), actual_mistake(S, M), chosen_source(S).

peaceful :- chosen_source(S), chosen_remedy(R), actual_remedy(S, R).
cleared  :- peaceful.
outcome(cleared) :- misunderstanding, cleared.
outcome(confused) :- misunderstanding, not cleared.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, sid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("actual_mistake", sid, source.mistake))
        lines.append(asp.fact("actual_remedy", sid, source.remedy))
    for mid in MISTAKES:
        lines.append(asp.fact("mistake", mid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    if (
        source_fits(params.place, params.source)
        and misunderstanding_fits(params.source, params.mistake)
        and remedy_fits(params.source, params.remedy)
    ):
        return "cleared"
    return "confused"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_mistake", params.mistake),
            asp.fact("chosen_remedy", params.remedy),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a loud clack, a wild misunderstanding, and the real fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mayor")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and not source_fits(args.place, args.source):
        raise StoryError(explain_source_place(args.place, args.source))
    if args.source and args.mistake and not misunderstanding_fits(args.source, args.mistake):
        raise StoryError(explain_mistake(args.source, args.mistake))
    if args.source and args.remedy and not remedy_fits(args.source, args.remedy):
        raise StoryError(explain_remedy(args.source, args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.mistake is None or combo[2] == args.mistake)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, mistake_id, remedy_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mayor = args.mayor or rng.choice(["Mayor Peg", "Mayor Mae", "Mayor Buck", "Mayor Reed"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        source=source_id,
        mistake=mistake_id,
        remedy=remedy_id,
        hero=hero,
        gender=gender,
        mayor=mayor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if not source_fits(params.place, params.source):
        raise StoryError(explain_source_place(params.place, params.source))
    if not misunderstanding_fits(params.source, params.mistake):
        raise StoryError(explain_mistake(params.source, params.mistake))
    if not remedy_fits(params.source, params.remedy):
        raise StoryError(explain_remedy(params.source, params.remedy))

    world = tell(
        place=PLACES[params.place],
        source_cfg=SOURCES[params.source],
        mistake_cfg=MISTAKES[params.mistake],
        remedy_cfg=REMEDIES[params.remedy],
        hero_name=params.hero,
        gender=params.gender,
        mayor_name=params.mayor,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with io.StringIO() as buf:
            old = sys.stdout
            sys.stdout = buf
            try:
                emit(smoke, trace=False, qa=True, header="### smoke")
            finally:
                sys.stdout = old
        if not smoke.story or "clack" not in smoke.story.lower():
            raise StoryError("(Smoke test story was empty or missed the required word 'clack'.)")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, mistake, remedy) combos:\n")
        for place_id, source_id, mistake_id, remedy_id in combos:
            print(f"  {place_id:8} {source_id:14} {mistake_id:13} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.source} in {p.place} ({p.mistake} -> {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
