#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py
================================================================================================

A standalone story world for a small animal tale set in a storm drain.

The core domain:
- Two small animals live in a storm drain.
- One child has gathered useful found pieces.
- Rain changes the drain: a nest starts dripping, or a path is cut by rushing water.
- The worried friend makes a repeated lament.
- The hero first clutches the pieces, then chooses to share.
- Together they transform the shared bits into something helpful.
- The ending image proves the change: dry nest, safe crossing, and a new habit of sharing.

Run it
------
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py --problem drip_nest --material bottle_cap --build roof
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py --material paper_scrap
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py --all
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/resolution_lament_storm_drain_repetition_sharing_transformation.py --verify
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
        if self.type in {"girl", "mother", "aunt", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "tom"}:
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
class AnimalPair:
    id: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    elder_name: str
    elder_kind: str
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
class Problem:
    id: str
    label: str
    opening: str
    repeat: str
    danger: str
    need: str
    solved_by: set[str] = field(default_factory=set)
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
class Material:
    id: str
    label: str
    plural_label: str
    phrase: str
    count: int
    floats: bool = False
    sheds_water: bool = False
    sturdy: bool = False
    pretty: str = ""
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
class Build:
    id: str
    label: str
    verb: str
    need: str
    needs_float: bool = False
    needs_shed: bool = False
    needs_sturdy: bool = False
    min_count: int = 1
    success_text: str = ""
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


def _r_wetness(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("drain")
    friend = world.get("friend")
    problem = world.facts["problem_cfg"]
    if problem.id == "drip_nest" and place.meters["dripping"] >= THRESHOLD:
        sig = ("wetness", "drip_nest")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.meters["wet"] += 1
            friend.memes["worry"] += 1
            out.append("__drip__")
    if problem.id == "flooded_gap" and place.meters["current"] >= THRESHOLD:
        sig = ("wetness", "flooded_gap")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["worry"] += 1
            friend.meters["stranded"] += 1
            out.append("__current__")
    return out


def _r_lament(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    hero = world.get("hero")
    if friend.memes["worry"] >= THRESHOLD and hero.memes["holding_back"] >= THRESHOLD:
        sig = ("lament",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["sad"] += 1
            out.append("__lament__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("drain")
    hero = world.get("hero")
    friend = world.get("friend")
    if place.meters["safe"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["care"] += 1
            hero.memes["relief"] += 1
            friend.memes["relief"] += 1
            friend.memes["worry"] = 0.0
            friend.meters["wet"] = 0.0
            friend.meters["stranded"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wetness", tag="physical", apply=_r_wetness),
    Rule(name="lament", tag="emotional", apply=_r_lament),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for s in produced:
            world.say(s)
    return produced


def supports_build(material: Material, build: Build) -> bool:
    if material.count < build.min_count:
        return False
    if build.needs_float and not material.floats:
        return False
    if build.needs_shed and not material.sheds_water:
        return False
    if build.needs_sturdy and not material.sturdy:
        return False
    return True


def build_fits_problem(problem: Problem, build: Build) -> bool:
    return build.id in problem.solved_by


def valid_combo(problem: Problem, material: Material, build: Build) -> bool:
    return build_fits_problem(problem, build) and supports_build(material, build)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for prob_id, problem in PROBLEMS.items():
        for material_id, material in MATERIALS.items():
            for build_id, build in BUILDS.items():
                if valid_combo(problem, material, build):
                    out.append((prob_id, material_id, build_id))
    return sorted(out)


def predict_solution(problem: Problem, material: Material, build: Build) -> dict[str, bool]:
    return {
        "fits_problem": build_fits_problem(problem, build),
        "has_support": supports_build(material, build),
        "will_work": valid_combo(problem, material, build),
    }


def introduce(world: World, pair: AnimalPair, material: Material) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    drain = world.get("drain")
    hero.memes["pride"] += 1
    world.say(
        f"In a round little room inside the storm drain, {hero.id} the {hero.type} "
        f"and {friend.id} the {friend.type} kept house with bottle-bright pebbles and "
        f"soft moss. All morning, {hero.id} had been gathering {material.plural_label} "
        f"and stacking them in a neat pile beside the wall."
    )
    if material.pretty:
        world.say(
            f"{hero.id} liked them because {material.pretty}. Each piece felt too special to give away."
        )
    drain.meters["calm"] = 1.0


def storm_begins(world: World, problem: Problem) -> None:
    drain = world.get("drain")
    friend = world.get("friend")
    world.say(
        f"Then rain began to drum above the grate. Soon {problem.opening}"
    )
    if problem.id == "drip_nest":
        drain.meters["dripping"] += 1
        friend.attrs["trouble_spot"] = "moss bed"
    else:
        drain.meters["current"] += 1
        friend.attrs["trouble_spot"] = "stone path"
    propagate(world, narrate=False)
    world.facts["problem_started"] = True


def notice_need(world: World, problem: Problem) -> None:
    friend = world.get("friend")
    world.say(
        f"{friend.id} stared at the trouble and felt small. {problem.danger}"
    )


def lament(world: World, problem: Problem) -> None:
    friend = world.get("friend")
    world.say(
        f'"{problem.repeat}, {problem.repeat}, {problem.repeat}," {friend.id} said in a tiny lament. '
        f'"What will happen to my {friend.attrs["trouble_spot"]}?"'
    )
    world.facts["lament_phrase"] = problem.repeat


def hesitate(world: World, material: Material) -> None:
    hero = world.get("hero")
    hero.memes["holding_back"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} curled both paws around the pile of {material.plural_label}. "
        f"{hero.pronoun('subject').capitalize()} wanted to keep every one."
    )


def elder_guides(world: World, build: Build) -> None:
    elder = world.get("elder")
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"Old {elder.id} the {elder.type} poked a whiskered face from a side pipe and listened. "
        f'"A pile that only sits there is lonely," {elder.id} said. "A shared pile can become {build.label}."'
    )
    world.say(
        f"{hero.id} looked at {friend.id}, and the repeated lament sounded different now: not noisy, but true."
    )


def share(world: World, material: Material) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    stash = world.get("stash")
    hero.memes["holding_back"] = 0.0
    hero.memes["care"] += 1
    friend.memes["trust"] += 1
    stash.meters["shared_count"] = float(material.count)
    world.facts["shared"] = True
    world.say(
        f'"Take them," said {hero.id} at last. "We can use the {material.plural_label} together." '
        f"{friend.id}'s shoulders dropped in relief."
    )
    world.say(
        f"{friend.id} shared a twist of string-cord from under the moss, and now both children had something to give."
    )


def transform(world: World, material: Material, build: Build, problem: Problem) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    stash = world.get("stash")
    drain = world.get("drain")
    stash.meters["transformed"] = 1.0
    drain.meters["safe"] = 1.0
    world.facts["transformation"] = build.label
    propagate(world, narrate=False)
    count_words = {
        1: "one by one",
        2: "two by two",
        3: "again and again",
        4: "again and again",
    }
    rhythm = count_words.get(material.count, "again and again")
    world.say(
        f"Then they worked {rhythm}. {hero.id} passed the {material.plural_label}; "
        f"{friend.id} tied and tucked; old {world.get('elder').id} nudged the corners straight."
    )
    world.say(build.success_text.format(material=material.plural_label, problem=problem.label))
    world.say(
        f"What had been only a secret pile was now a real transformation, made by sharing."
    )


def ending(world: World, problem: Problem, build: Build) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"The storm still muttered overhead, but inside the drain the danger had changed shape. "
        f"{problem.need} was no longer lost."
    )
    world.say(
        f"{friend.id} gave a happy sigh instead of a lament. "
        f'"This is our resolution," {friend.id} said, touching the {build.label}.'
    )
    world.say(
        f"After that, whenever {hero.id} found something useful, {hero.pronoun('subject')} no longer hid it first. "
        f"{hero.pronoun('subject').capitalize()} called for {friend.id}, and together they wondered what it might become."
    )


def tell(
    pair: AnimalPair,
    problem: Problem,
    material: Material,
    build: Build,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=pair.hero_name,
        kind="character",
        type=pair.hero_kind,
        role="hero",
        attrs={"animal": pair.hero_kind},
    ))
    friend = world.add(Entity(
        id=pair.friend_name,
        kind="character",
        type=pair.friend_kind,
        role="friend",
        attrs={"animal": pair.friend_kind, "trouble_spot": ""},
    ))
    elder = world.add(Entity(
        id=pair.elder_name,
        kind="character",
        type=pair.elder_kind,
        role="elder",
        attrs={"animal": pair.elder_kind},
    ))
    world.add(Entity(
        id="drain",
        kind="thing",
        type="place",
        label="storm drain",
        attrs={"setting": "storm drain"},
    ))
    world.add(Entity(
        id="stash",
        kind="thing",
        type="stash",
        label=material.plural_label,
        attrs={"material": material.id},
    ))

    world.facts.update(
        pair=pair,
        problem_cfg=problem,
        material_cfg=material,
        build_cfg=build,
        shared=False,
        transformation="",
        problem_started=False,
        lament_phrase=problem.repeat,
    )

    introduce(world, pair, material)
    world.para()
    storm_begins(world, problem)
    notice_need(world, problem)
    hesitate(world, material)
    lament(world, problem)

    world.para()
    elder_guides(world, build)
    share(world, material)
    transform(world, material, build, problem)

    world.para()
    ending(world, problem, build)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        outcome="resolved" if world.get("drain").meters["safe"] >= THRESHOLD else "unresolved",
        solved=world.get("drain").meters["safe"] >= THRESHOLD,
    )
    return world


PAIRINGS = {
    "mice": AnimalPair(
        id="mice",
        hero_name="Moss",
        hero_kind="mouse",
        friend_name="Pip",
        friend_kind="mouse",
        elder_name="Aunt Sedge",
        elder_kind="shrew",
        tags={"mouse", "sharing"},
    ),
    "voles": AnimalPair(
        id="voles",
        hero_name="Reed",
        hero_kind="vole",
        friend_name="Nip",
        friend_kind="vole",
        elder_name="Gran Thimble",
        elder_kind="toad",
        tags={"vole", "sharing"},
    ),
    "frogs": AnimalPair(
        id="frogs",
        hero_name="Pebble",
        hero_kind="frog",
        friend_name="Dab",
        friend_kind="frog",
        elder_name="Uncle Ripple",
        elder_kind="rat",
        tags={"frog", "storm_drain"},
    ),
}

PROBLEMS = {
    "drip_nest": Problem(
        id="drip_nest",
        label="a dripping nest corner",
        opening="cold drops slipped through the grate and began tapping on Pip's moss bed.",
        repeat="drip",
        danger="The bed was turning dark and wet, and the nicest sleeping corner in the drain was about to be spoiled.",
        need="The sleeping corner",
        solved_by={"roof"},
        tags={"rain", "nest"},
    ),
    "flooded_gap": Problem(
        id="flooded_gap",
        label="a rushing gap in the floor",
        opening="water swirled through the middle trench and cut the little stone path in two.",
        repeat="swirl",
        danger="The stepping stones had vanished under the current, and the safe side of the room suddenly felt far away.",
        need="The path across the room",
        solved_by={"raft", "bridge"},
        tags={"water", "crossing"},
    ),
}

MATERIALS = {
    "broad_leaf": Material(
        id="broad_leaf",
        label="broad leaf",
        plural_label="broad leaves",
        phrase="three broad leaves",
        count=3,
        sheds_water=True,
        pretty="the rain rolled off them in silver beads",
        tags={"leaf", "roof"},
    ),
    "bark_chip": Material(
        id="bark_chip",
        label="bark chip",
        plural_label="bark chips",
        phrase="three bark chips",
        count=3,
        floats=True,
        sturdy=True,
        pretty="they smelled warm and woody even in the damp air",
        tags={"bark", "float"},
    ),
    "bottle_cap": Material(
        id="bottle_cap",
        label="bottle cap",
        plural_label="bottle caps",
        phrase="four bottle caps",
        count=4,
        floats=True,
        sheds_water=True,
        sturdy=True,
        pretty="their tinny rims flashed like little moons",
        tags={"cap", "transform"},
    ),
    "paper_scrap": Material(
        id="paper_scrap",
        label="paper scrap",
        plural_label="paper scraps",
        phrase="two paper scraps",
        count=2,
        pretty="the colors looked cheerful for a moment",
        tags={"paper"},
    ),
}

BUILDS = {
    "roof": Build(
        id="roof",
        label="a tiny roof",
        verb="roof",
        need="keep a nest dry",
        needs_shed=True,
        min_count=2,
        success_text=(
            "They propped {material} over the moss bed and tied them to a bent wire. "
            "The drops struck the top and slid away, so the little bed stayed dry."
        ),
        tags={"roof", "dry"},
    ),
    "raft": Build(
        id="raft",
        label="a pocket raft",
        verb="raft",
        need="cross moving water",
        needs_float=True,
        min_count=2,
        success_text=(
            "They bound {material} into a pocket raft and set it on the current. "
            "It bobbed instead of sinking, so the crossing became gentle and safe."
        ),
        tags={"raft", "float"},
    ),
    "bridge": Build(
        id="bridge",
        label="a small bridge",
        verb="bridge",
        need="cross a narrow rushing gap",
        needs_sturdy=True,
        min_count=2,
        success_text=(
            "They laid {material} from one stone lip to the other and tied them snug. "
            "The new bridge held still above the water, and careful feet could pass across."
        ),
        tags={"bridge", "crossing"},
    ),
}


@dataclass
class StoryParams:
    pair: str
    problem: str
    material: str
    build: str
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


CURATED = [
    StoryParams(
        pair="mice",
        problem="drip_nest",
        material="bottle_cap",
        build="roof",
        seed=1,
    ),
    StoryParams(
        pair="voles",
        problem="flooded_gap",
        material="bark_chip",
        build="raft",
        seed=2,
    ),
    StoryParams(
        pair="frogs",
        problem="flooded_gap",
        material="bottle_cap",
        build="bridge",
        seed=3,
    ),
    StoryParams(
        pair="mice",
        problem="drip_nest",
        material="broad_leaf",
        build="roof",
        seed=4,
    ),
]


KNOWLEDGE = {
    "storm_drain": [
        (
            "What is a storm drain?",
            "A storm drain is a place where rainwater runs away under streets or along curbs. When heavy rain comes, water can rush through it very quickly."
        )
    ],
    "sharing": [
        (
            "Why can sharing help solve a problem?",
            "Sharing puts more useful things and more helping hands together. Sometimes one small thing is not enough alone, but together it can become something new."
        )
    ],
    "transform": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new form or use. In a story, an ordinary object can become helpful when characters imagine and build with it."
        )
    ],
    "roof": [
        (
            "Why does a roof keep a nest dry?",
            "A roof gives water a place to land first, so the drops roll away instead of falling into the nest. That helps the bedding stay dry underneath."
        )
    ],
    "raft": [
        (
            "Why does a raft float?",
            "A raft floats when it is made from things that stay on top of water instead of sinking. Then it can carry someone gently across."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge makes a path over a space that would be hard to cross. It lets feet go above the danger instead of through it."
        )
    ],
    "leaf": [
        (
            "Why can a broad leaf help in the rain?",
            "A broad leaf can catch raindrops on top of it. If it is placed well, the water slides off the sides."
        )
    ],
    "bark": [
        (
            "Why might bark chips float?",
            "Many pieces of bark are light and woody, so water can hold them up. That can make them useful for a tiny raft."
        )
    ],
    "cap": [
        (
            "Why are bottle caps good for little animal building games?",
            "Bottle caps are hard and light for their size, and rain does not soak into them. In a tiny world, they can become roofs, boats, or stepping pieces."
        )
    ],
    "paper": [
        (
            "Why is paper a poor choice in the rain?",
            "Paper gets soggy and weak when it is wet. That makes it a poor building material for puddles or dripping places."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "storm_drain",
    "sharing",
    "transform",
    "roof",
    "raft",
    "bridge",
    "leaf",
    "bark",
    "cap",
    "paper",
]


def generation_prompts(world: World) -> list[str]:
    pair = world.facts["pair"]
    problem = world.facts["problem_cfg"]
    material = world.facts["material_cfg"]
    build = world.facts["build_cfg"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        'Write a gentle animal story for a 3-to-5-year-old set in a storm drain that uses the words "resolution" and "lament".',
        f"Tell a story where {hero.id} the {hero.type} hears {friend.id}'s repeated lament about {problem.label}, shares some {material.plural_label}, and helps transform them into {build.label}.",
        f"Write a child-facing story with repetition, sharing, and transformation, where rain changes a storm drain and the ending clearly shows a resolution."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    problem = world.facts["problem_cfg"]
    material = world.facts["material_cfg"]
    build = world.facts["build_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type}, who live in a storm drain, and {elder.id}, the older {elder.type} who helps them think. The trouble starts when rain changes their little home."
        ),
        (
            f"What was {friend.id}'s lament about?",
            f"{friend.id} kept saying '{problem.repeat}, {problem.repeat}, {problem.repeat}' because {problem.label} was in danger. The repeated sound matched the trouble in the drain and showed how worried {friend.pronoun('subject')} felt."
        ),
        (
            f"Why did {hero.id} need to share the {material.plural_label}?",
            f"{hero.id} had gathered the {material.plural_label} and wanted to keep them, but the pile was the best chance to fix the trouble. When {hero.pronoun('subject')} shared them, the pieces could finally be used to help someone else."
        ),
        (
            "How did the transformation solve the problem?",
            f"The children turned the {material.plural_label} into {build.label}. That worked because this new shape matched the problem in the storm drain, so the danger stopped feeling bigger than they were."
        ),
        (
            "What was the resolution at the end?",
            f"The resolution was that the storm drain became safe again and the needed place was protected. The ending also showed a bigger change: {hero.id} stopped hiding useful things and started calling {friend.id} to build together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    material = world.facts["material_cfg"]
    build = world.facts["build_cfg"]
    tags = {"storm_drain", "sharing", "transform", build.id}
    if material.id == "broad_leaf":
        tags.add("leaf")
    elif material.id == "bark_chip":
        tags.add("bark")
    elif material.id == "bottle_cap":
        tags.add("cap")
    elif material.id == "paper_scrap":
        tags.add("paper")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, material: Material, build: Build) -> str:
    if not build_fits_problem(problem, build):
        return (
            f"(No story: {build.label.capitalize()} does not honestly solve {problem.label}. "
            f"Pick a build that matches the problem in the storm drain.)"
        )
    if material.count < build.min_count:
        return (
            f"(No story: {material.phrase} are not enough to make {build.label}. "
            f"The transformation needs enough pieces to feel real.)"
        )
    if build.needs_shed and not material.sheds_water:
        return (
            f"(No story: {material.plural_label.capitalize()} soak or fail in rain, so they would not make a good roof over a dripping nest.)"
        )
    if build.needs_float and not material.floats:
        return (
            f"(No story: {material.plural_label.capitalize()} do not float well enough for a raft, so the crossing would not be safe.)"
        )
    if build.needs_sturdy and not material.sturdy:
        return (
            f"(No story: {material.plural_label.capitalize()} are not sturdy enough to hold a bridge over rushing water.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


ASP_RULES = r"""
valid_problem_build(P,B) :- problem(P), build(B), solves(P,B).

supports(M,B) :- material(M), build(B), count(M,C), min_count(B,N), C >= N,
                 not needs_float(B), not needs_shed(B), not needs_sturdy(B).
supports(M,B) :- material(M), build(B), count(M,C), min_count(B,N), C >= N,
                 needs_float(B), floats(M), not needs_shed(B), not needs_sturdy(B).
supports(M,B) :- material(M), build(B), count(M,C), min_count(B,N), C >= N,
                 needs_shed(B), sheds_water(M), not needs_float(B), not needs_sturdy(B).
supports(M,B) :- material(M), build(B), count(M,C), min_count(B,N), C >= N,
                 needs_sturdy(B), sturdy(M), not needs_float(B), not needs_shed(B).

valid(P,M,B) :- problem(P), material(M), build(B), valid_problem_build(P,B), supports(M,B).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for bid, build in BUILDS.items():
        lines.append(asp.fact("build", bid))
        lines.append(asp.fact("min_count", bid, build.min_count))
        if build.needs_float:
            lines.append(asp.fact("needs_float", bid))
        if build.needs_shed:
            lines.append(asp.fact("needs_shed", bid))
        if build.needs_sturdy:
            lines.append(asp.fact("needs_sturdy", bid))
    for pid, problem in PROBLEMS.items():
        for bid in sorted(problem.solved_by):
            lines.append(asp.fact("solves", pid, bid))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("count", mid, material.count))
        if material.floats:
            lines.append(asp.fact("floats", mid))
        if material.sheds_water:
            lines.append(asp.fact("sheds_water", mid))
        if material.sturdy:
            lines.append(asp.fact("sturdy", mid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("FAILED: default resolve_params() raised StoryError:", err)

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "resolution" not in sample.story or "lament" not in sample.story:
                raise StoryError("required seed words missing from story")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-generated {len(smoke_cases)} stories.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print("FAILED: normal story generation crashed during smoke test:", err)

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: sharing and transformation in a storm drain."
    )
    ap.add_argument("--pair", choices=PAIRINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--build", choices=BUILDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.material and args.build:
        problem = PROBLEMS[args.problem]
        material = MATERIALS[args.material]
        build = BUILDS[args.build]
        if not valid_combo(problem, material, build):
            raise StoryError(explain_rejection(problem, material, build))

    combos = [
        c for c in valid_combos()
        if (args.problem is None or c[0] == args.problem)
        and (args.material is None or c[1] == args.material)
        and (args.build is None or c[2] == args.build)
    ]
    if not combos:
        if args.problem and args.material and args.build:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], MATERIALS[args.material], BUILDS[args.build]))
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, material_id, build_id = rng.choice(sorted(combos))
    pair_id = args.pair or rng.choice(sorted(PAIRINGS))
    return StoryParams(
        pair=pair_id,
        problem=problem_id,
        material=material_id,
        build=build_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pair not in PAIRINGS:
        raise StoryError(f"(Unknown pair: {params.pair})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.build not in BUILDS:
        raise StoryError(f"(Unknown build: {params.build})")

    pair = PAIRINGS[params.pair]
    problem = PROBLEMS[params.problem]
    material = MATERIALS[params.material]
    build = BUILDS[params.build]
    if not valid_combo(problem, material, build):
        raise StoryError(explain_rejection(problem, material, build))

    world = tell(pair=pair, problem=problem, material=material, build=build)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, material, build) combos:\n")
        for problem, material, build in combos:
            print(f"  {problem:12} {material:12} {build}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.pair}: {p.problem} with {p.material} -> {p.build}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
