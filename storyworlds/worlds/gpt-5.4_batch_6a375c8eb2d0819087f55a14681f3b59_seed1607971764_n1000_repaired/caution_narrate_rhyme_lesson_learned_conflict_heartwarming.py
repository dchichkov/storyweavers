#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py
=========================================================================================

A small story world about two children who find a tiny creature in a risky spot.
One child wants to help too quickly, another gives caution, and a grown-up helps
them choose a gentler method. The story ends with a warm rhyme and a clear lesson:
small hearts can help best when they slow down and handle living things gently.

Run it
------
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py --creature snail --hazard path --tool leaf --safe_place mint_patch
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py --tool broom
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/caution_narrate_rhyme_lesson_learned_conflict_heartwarming.py --verify
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
CARE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    fragile: bool = False
    alive: bool = False
    supports_creature: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class Creature:
    id: str
    label: str
    article: str
    move_word: str
    home_word: str
    rhyme_friend: str
    fragile: bool
    needs_damp: bool = False
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
class Hazard:
    id: str
    label: str
    place_line: str
    risk_line: str
    risk_kind: str
    hard_surface: bool = False
    windy: bool = False
    dry: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    care: int
    soft: bool
    supports: bool
    move_line: str
    rough_line: str
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
class SafePlace:
    id: str
    label: str
    phrase: str
    good_for: set[str] = field(default_factory=set)
    damp: bool = False
    sheltered: bool = False
    leafy: bool = False
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_hazard_scares(world: World) -> list[str]:
    creature = world.get("creature")
    hazard = world.facts["hazard_cfg"]
    if creature.meters["at_risk"] < THRESHOLD:
        return []
    sig = ("hazard_scares", hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("eager", "careful"):
        world.get(kid_id).memes["worry"] += 1
    return ["__worry__"]


def _r_rough_hurts(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["handled_roughly"] < THRESHOLD:
        return []
    sig = ("rough_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["afraid"] += 1
    creature.meters["unsafe"] += 1
    for kid_id in ("eager", "careful"):
        world.get(kid_id).memes["sad"] += 1
    return []


def _r_gentle_rescue(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("safe_place")
    if creature.meters["moved_gently"] < THRESHOLD or place.meters["ready"] < THRESHOLD:
        return []
    sig = ("gentle_rescue", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["at_risk"] = 0.0
    creature.meters["safe"] += 1
    for kid_id in ("eager", "careful"):
        world.get(kid_id).memes["relief"] += 1
        world.get(kid_id).memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hazard_scares", tag="emotion", apply=_r_hazard_scares),
    Rule(name="rough_hurts", tag="physical", apply=_r_rough_hurts),
    Rule(name="gentle_rescue", tag="physical", apply=_r_gentle_rescue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tool_works(creature: Creature, hazard: Hazard, tool: Tool) -> bool:
    if tool.care < CARE_MIN:
        return False
    if creature.fragile and not tool.soft:
        return False
    if not tool.supports:
        return False
    if hazard.hard_surface and not tool.soft:
        return False
    return True


def place_works(creature: Creature, safe_place: SafePlace) -> bool:
    if creature.id not in safe_place.good_for:
        return False
    if creature.needs_damp and not safe_place.damp:
        return False
    return True


def valid_combo(creature: Creature, hazard: Hazard, tool: Tool, safe_place: SafePlace) -> bool:
    return tool_works(creature, hazard, tool) and place_works(creature, safe_place)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for creature_id, creature in CREATURES.items():
        for hazard_id, hazard in HAZARDS.items():
            for tool_id, tool in TOOLS.items():
                for place_id, place in SAFE_PLACES.items():
                    if valid_combo(creature, hazard, tool, place):
                        out.append((creature_id, hazard_id, tool_id, place_id))
    return out


def explain_tool_rejection(creature: Creature, hazard: Hazard, tool: Tool) -> str:
    if tool.care < CARE_MIN:
        return (
            f"(No story: {tool.label} is too rough for a gentle rescue here. "
            f"Choose a softer helper like a leaf, a paper cup, or a cardboard square.)"
        )
    if creature.fragile and not tool.soft:
        return (
            f"(No story: {creature.label} is too delicate for {tool.label}. "
            f"The rescue tool must be soft enough for a tiny living creature.)"
        )
    if not tool.supports:
        return (
            f"(No story: {tool.label} cannot safely carry {creature.article} {creature.label}. "
            f"The children need something that can support the creature while moving it.)"
        )
    if hazard.hard_surface and not tool.soft:
        return (
            f"(No story: on a hard place like {hazard.label}, a softer tool is needed. "
            f"A rough sweep would make the danger worse, not better.)"
        )
    return "(No story: that tool does not fit this rescue.)"


def explain_place_rejection(creature: Creature, safe_place: SafePlace) -> str:
    if creature.id not in safe_place.good_for:
        return (
            f"(No story: {safe_place.phrase} is not a good home for {creature.article} {creature.label}. "
            f"Pick a safer resting place that suits the animal.)"
        )
    if creature.needs_damp and not safe_place.damp:
        return (
            f"(No story: {creature.label}s need damp places, but {safe_place.phrase} is too dry. "
            f"Choose a spot with cool leaves or damp soil.)"
        )
    return "(No story: that safe place does not fit this creature.)"


def predict_gentle(world: World, tool: Tool, safe_place: SafePlace) -> dict:
    sim = world.copy()
    sim.facts["tool_cfg"] = tool
    sim.facts["safe_place_cfg"] = safe_place
    sim.get("safe_place").meters["ready"] += 1
    sim.get("creature").meters["moved_gently"] += 1
    propagate(sim, narrate=False)
    creature = sim.get("creature")
    return {
        "safe": creature.meters["safe"] >= THRESHOLD,
        "at_risk": creature.meters["at_risk"] >= THRESHOLD,
    }


def introduce(world: World, eager: Entity, careful: Entity, caregiver: Entity, creature: Creature, hazard: Hazard) -> None:
    eager.memes["joy"] += 1
    careful.memes["joy"] += 1
    world.say(
        f"One soft afternoon, {eager.id} and {careful.id} were walking with "
        f"their {caregiver.label_word} when they spotted {creature.article} {creature.label} {hazard.place_line}."
    )
    world.say(
        f"It was so small that both children bent close to watch {creature.move_word}. "
        f"{hazard.risk_line}"
    )


def eager_reacts(world: World, eager: Entity, creature: Creature) -> None:
    eager.memes["urgency"] += 1
    world.say(
        f'"Oh! I can help right now," said {eager.id}. "{creature.article.capitalize()} {creature.label} should not stay there another minute."'
    )


def caution_line(world: World, careful: Entity, eager: Entity, tool: Tool, creature: Creature, hazard: Hazard) -> None:
    careful.memes["caution"] += 1
    world.say(
        f'{careful.id} reached out with caution. "Please do not use {tool.label}," '
        f'{careful.pronoun()} said. "{tool.rough_line}, and {creature.article} {creature.label} is too tiny for that."'
    )
    if hazard.id == "path":
        world.say(
            f'"The stones are hard there, so even a quick shove could scare {creature.pronoun("object")}."'
        )


def conflict_line(world: World, eager: Entity, careful: Entity) -> None:
    eager.memes["defiance"] += 1
    careful.memes["tension"] += 1
    world.say(
        f'"But I only want to save it," said {eager.id}. {eager.pronoun("subject").capitalize()} hugged '
        f'{eager.pronoun("possessive")} elbows and looked hurt. For a moment, the two children stood in a quiet little conflict, '
        f"one full of hurry and one full of care."
    )


def adult_guides(world: World, caregiver: Entity, eager: Entity, careful: Entity, tool: Tool, safe_place: SafePlace, creature: Creature) -> None:
    pred = predict_gentle(world, tool, safe_place)
    world.facts["predicted_safe"] = pred["safe"]
    caregiver.memes["calm"] += 1
    world.say(
        f'Their {caregiver.label_word} knelt beside them. "Both of you have kind hearts," '
        f'{caregiver.pronoun()} said. "Now let us narrate what the little one needs before we act."'
    )
    world.say(
        f'"Not a fast hand. A gentle hand. We can use {tool.phrase} and carry it to {safe_place.phrase}."'
    )


def rough_attempt(world: World, eager: Entity, tool: Tool) -> None:
    eager.memes["regret_seed"] += 1
    world.get("creature").meters["handled_roughly"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{eager.id} started to reach with {tool.phrase}, then stopped when the tiny creature pulled in tight. "
        f"The small frightened motion made {eager.pronoun('object')} freeze."
    )


def gentle_move(world: World, eager: Entity, careful: Entity, caregiver: Entity, tool: Tool, safe_place: SafePlace, creature: Creature) -> None:
    world.get("safe_place").meters["ready"] += 1
    world.get("creature").meters["moved_gently"] += 1
    propagate(world, narrate=False)
    eager.memes["humility"] += 1
    world.say(
        f"Together they slid {tool.phrase} under {creature.article} {creature.label}. "
        f"{tool.move_line}, and the little creature rested without tumbling."
    )
    world.say(
        f"{careful.id} carried the edge, {eager.id} steadied the other side, and their {caregiver.label_word} "
        f"guided them to {safe_place.phrase}."
    )


def rhyme_and_lesson(world: World, eager: Entity, careful: Entity, caregiver: Entity, creature: Creature, safe_place: SafePlace) -> None:
    eager.memes["lesson"] += 1
    careful.memes["lesson"] += 1
    eager.memes["love"] += 1
    careful.memes["love"] += 1
    creature_ent = world.get("creature")
    creature_ent.meters["home"] += 1
    world.say(
        f"When they set the tiny traveler among {safe_place.label}, it stretched out again and began {creature.move_word}."
    )
    world.say(
        f'Their {caregiver.label_word} smiled and whispered a rhyme for them to repeat: '
        f'"Slow and light, soft and right; little lives need gentle might."'
    )
    world.say(
        f"{eager.id} said it once, then twice, and this time the words felt true inside {eager.pronoun('object')}. "
        f'"I thought fast meant kind," {eager.pronoun()} said softly, "but careful was kinder."'
    )
    world.say(
        f'{careful.id} squeezed {eager.pronoun("possessive")} hand. Their {caregiver.label_word} nodded, and the three of them '
        f"watched until the small creature disappeared into its safer home."
    )


def tell(
    creature: Creature,
    hazard: Hazard,
    tool: Tool,
    safe_place: SafePlace,
    eager_name: str = "Mia",
    eager_gender: str = "girl",
    careful_name: str = "Ben",
    careful_gender: str = "boy",
    caregiver_type: str = "grandmother",
) -> World:
    world = World()
    eager = world.add(Entity(id=eager_name, kind="character", type=eager_gender, role="eager", label=eager_name, attrs={}))
    careful = world.add(Entity(id=careful_name, kind="character", type=careful_gender, role="careful", label=careful_name, attrs={}))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, role="caregiver", label="the caregiver", attrs={}))
    world.add(
        Entity(
            id="creature",
            kind="thing",
            type="creature",
            label=creature.label,
            movable=True,
            fragile=creature.fragile,
            alive=True,
            attrs={"creature_id": creature.id},
        )
    )
    world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label, attrs={"hazard_id": hazard.id}))
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            supports_creature=tool.supports,
            soft=tool.soft,
            attrs={"tool_id": tool.id},
        )
    )
    world.add(Entity(id="safe_place", kind="thing", type="place", label=safe_place.label, attrs={"safe_place_id": safe_place.id}))

    world.get("creature").meters["at_risk"] = 1.0
    world.get("safe_place").meters["ready"] = 0.0
    world.get("creature").meters["moved_gently"] = 0.0
    world.get("creature").meters["handled_roughly"] = 0.0
    world.facts.update(
        creature_cfg=creature,
        hazard_cfg=hazard,
        tool_cfg=tool,
        safe_place_cfg=safe_place,
    )
    propagate(world, narrate=False)

    introduce(world, eager, careful, caregiver, creature, hazard)
    world.para()
    eager_reacts(world, eager, creature)
    caution_line(world, careful, eager, tool, creature, hazard)
    conflict_line(world, eager, careful)
    world.para()
    adult_guides(world, caregiver, eager, careful, tool, safe_place, creature)
    if tool.care == CARE_MIN:
        rough_attempt(world, eager, tool)
    gentle_move(world, eager, careful, caregiver, tool, safe_place, creature)
    world.para()
    rhyme_and_lesson(world, eager, careful, caregiver, creature, safe_place)

    world.facts.update(
        eager=eager,
        careful=careful,
        caregiver=caregiver,
        rescued=world.get("creature").meters["safe"] >= THRESHOLD,
        lesson_learned=eager.memes["lesson"] >= THRESHOLD,
        rhyme_used=True,
        conflict=eager.memes["defiance"] >= THRESHOLD,
        gentle_tool=tool.care >= CARE_MIN,
    )
    return world


CREATURES = {
    "snail": Creature(
        id="snail",
        label="snail",
        article="a",
        move_word="gliding on",
        home_word="cool leaves",
        rhyme_friend="trail",
        fragile=True,
        needs_damp=True,
        tags={"snail", "gentle"},
    ),
    "caterpillar": Creature(
        id="caterpillar",
        label="caterpillar",
        article="a",
        move_word="curling and uncurling",
        home_word="leafy stems",
        rhyme_friend="pillar",
        fragile=True,
        needs_damp=False,
        tags={"caterpillar", "gentle"},
    ),
    "ladybug": Creature(
        id="ladybug",
        label="ladybug",
        article="a",
        move_word="opening and closing its tiny wings",
        home_word="a safe plant",
        rhyme_friend="hug",
        fragile=True,
        needs_damp=False,
        tags={"ladybug", "gentle"},
    ),
}

HAZARDS = {
    "path": Hazard(
        id="path",
        label="the stone path",
        place_line="on the stone path",
        risk_line="A shoe could come by before long.",
        risk_kind="step",
        hard_surface=True,
        tags={"path", "watch_steps"},
    ),
    "porch": Hazard(
        id="porch",
        label="the breezy porch rail",
        place_line="on the breezy porch rail",
        risk_line="The wind kept nudging the little body sideways.",
        risk_kind="wind",
        hard_surface=True,
        windy=True,
        tags={"porch", "wind"},
    ),
    "sunny_step": Hazard(
        id="sunny_step",
        label="the hot sunny step",
        place_line="on the hot sunny step",
        risk_line="The bright dry heat was not a good place to linger.",
        risk_kind="dry",
        hard_surface=True,
        dry=True,
        tags={"sun", "dry"},
    ),
}

TOOLS = {
    "leaf": Tool(
        id="leaf",
        label="a broad leaf",
        phrase="a broad leaf",
        care=3,
        soft=True,
        supports=True,
        move_line="The leaf made a small green boat",
        rough_line="it might slide too fast",
        tags={"leaf", "gentle_tool"},
    ),
    "cup": Tool(
        id="cup",
        label="a paper cup",
        phrase="a paper cup",
        care=3,
        soft=True,
        supports=True,
        move_line="The cup made a still little shelter",
        rough_line="it could bump if it were pressed down too fast",
        tags={"cup", "gentle_tool"},
    ),
    "cardboard": Tool(
        id="cardboard",
        label="a cardboard square",
        phrase="a cardboard square",
        care=2,
        soft=True,
        supports=True,
        move_line="The cardboard made a flat little bridge",
        rough_line="it could scrape if someone rushed",
        tags={"cardboard", "gentle_tool"},
    ),
    "broom": Tool(
        id="broom",
        label="a broom",
        phrase="a broom",
        care=1,
        soft=False,
        supports=False,
        move_line="The broom pushed much too hard",
        rough_line="the bristles would sweep too roughly",
        tags={"broom", "rough_tool"},
    ),
}

SAFE_PLACES = {
    "mint_patch": SafePlace(
        id="mint_patch",
        label="cool mint leaves",
        phrase="the cool mint patch",
        good_for={"snail", "ladybug", "caterpillar"},
        damp=True,
        sheltered=True,
        leafy=True,
        tags={"garden", "leaves"},
    ),
    "flowerpot": SafePlace(
        id="flowerpot",
        label="the flowerpot soil",
        phrase="the shaded flowerpot",
        good_for={"snail", "caterpillar"},
        damp=True,
        sheltered=True,
        leafy=False,
        tags={"flowerpot", "soil"},
    ),
    "rose_bush": SafePlace(
        id="rose_bush",
        label="the rose bush leaves",
        phrase="the rose bush",
        good_for={"ladybug", "caterpillar"},
        damp=False,
        sheltered=True,
        leafy=True,
        tags={"bush", "leaves"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Max", "Theo"]
CAREGIVERS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    creature: str
    hazard: str
    tool: str
    safe_place: str
    eager_name: str
    eager_gender: str
    careful_name: str
    careful_gender: str
    caregiver: str
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
        creature="snail",
        hazard="path",
        tool="leaf",
        safe_place="mint_patch",
        eager_name="Mia",
        eager_gender="girl",
        careful_name="Ben",
        careful_gender="boy",
        caregiver="grandmother",
    ),
    StoryParams(
        creature="ladybug",
        hazard="porch",
        tool="cup",
        safe_place="rose_bush",
        eager_name="Leo",
        eager_gender="boy",
        careful_name="Nora",
        careful_gender="girl",
        caregiver="father",
    ),
    StoryParams(
        creature="caterpillar",
        hazard="sunny_step",
        tool="cardboard",
        safe_place="flowerpot",
        eager_name="Ella",
        eager_gender="girl",
        careful_name="Sam",
        careful_gender="boy",
        caregiver="mother",
    ),
]


KNOWLEDGE = {
    "snail": [
        (
            "Why do snails like damp places?",
            "Snails can dry out if a place is too hot and dry. Damp leaves and cool soil help keep their bodies safe.",
        )
    ],
    "caterpillar": [
        (
            "Why should you be gentle with a caterpillar?",
            "A caterpillar has a soft little body that can be hurt easily. Gentle hands help keep it safe while it grows.",
        )
    ],
    "ladybug": [
        (
            "What does a ladybug do in a garden?",
            "A ladybug is a tiny beetle that crawls and flies among plants. Gardens can be a good home because there are leaves and little bugs to find there.",
        )
    ],
    "watch_steps": [
        (
            "Why is a stone path dangerous for a tiny animal?",
            "People may not see a very small creature on the path. A careful step for you can still be a huge danger for something tiny.",
        )
    ],
    "wind": [
        (
            "Why can wind be hard for tiny creatures?",
            "A strong breeze feels much bigger to a tiny body than to a person. Wind can push a little creature off the place where it is resting.",
        )
    ],
    "dry": [
        (
            "Why can a hot dry step be a bad place for a snail?",
            "A snail needs moisture to stay comfortable and safe. Hot dry stone can make it lose water too quickly.",
        )
    ],
    "gentle_tool": [
        (
            "Why is a leaf or cup better than a broom for moving a tiny animal?",
            "A leaf or cup can support a tiny creature without scraping it. A broom is made for sweeping, not for carrying delicate living things.",
        )
    ],
    "leaves": [
        (
            "Why are leaves a good hiding place for tiny garden animals?",
            "Leaves give shade and shelter. They can help a small creature rest where it is cooler and harder to spot.",
        )
    ],
    "soil": [
        (
            "Why can damp soil be safer than a hot stone step?",
            "Damp soil is cooler and softer than stone. For some tiny animals, that makes it easier to rest and move safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["snail", "caterpillar", "ladybug", "watch_steps", "wind", "dry", "gentle_tool", "leaves", "soil"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature = f["creature_cfg"]
    hazard = f["hazard_cfg"]
    place = f["safe_place_cfg"]
    eager = f["eager"]
    careful = f["careful"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "caution" and "narrate", where two children find {creature.article} {creature.label} in danger at {hazard.label}.',
        f"Tell a gentle conflict story where {eager.id} wants to help too fast, {careful.id} urges caution, and a grown-up teaches them to slow down and move the tiny creature safely.",
        f"Write a child-friendly story with a rhyme, a lesson learned, and a warm ending in which a tiny creature is carried to {place.phrase} with care.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eager = f["eager"]
    careful = f["careful"]
    caregiver = f["caregiver"]
    creature = f["creature_cfg"]
    hazard = f["hazard_cfg"]
    tool = f["tool_cfg"]
    place = f["safe_place_cfg"]
    out = [
        (
            "Who is the story about?",
            f"It is about {eager.id} and {careful.id}, who found {creature.article} {creature.label}, and their {caregiver.label_word} who helped them choose a gentle way to help.",
        ),
        (
            f"Why was the {creature.label} not safe where it was?",
            f"It was at {hazard.label}, which was risky for such a tiny creature. {hazard.risk_line} That is why the children felt they needed to help.",
        ),
        (
            f"Why did {careful.id} tell {eager.id} to use caution?",
            f"{careful.id} knew that helping too fast could hurt a tiny living thing. {tool.label.capitalize()} would only be safe if used gently, so caution mattered more than hurry.",
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was that {eager.id} wanted to save the creature right away, while {careful.id} wanted to slow down and protect it carefully. They both cared, but they disagreed about the safest way to help.",
        ),
        (
            "How did their grown-up help them?",
            f"Their {caregiver.label_word} told them to narrate what the little creature needed before acting. That helped them stop arguing and choose a calmer, gentler plan.",
        ),
    ]
    if f["rescued"]:
        out.append(
            (
                f"How did they move the {creature.label} safely?",
                f"They used {tool.phrase} and carried the tiny creature to {place.phrase}. The softer tool supported its body, and the new place suited what it needed.",
            )
        )
    if f["lesson_learned"]:
        out.append(
            (
                f"What lesson did {eager.id} learn?",
                f"{eager.id} learned that being fast is not always the kindest way to help. Careful, gentle actions can protect small creatures better than hurried ones.",
            )
        )
    out.append(
        (
            "What rhyme did they say, and why did it matter?",
            'They said, "Slow and light, soft and right; little lives need gentle might." The rhyme helped them remember the lesson and turned the rescue into a loving ending.',
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= set(f["creature_cfg"].tags)
    tags |= set(f["hazard_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["safe_place_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, ok in (("fragile", ent.fragile), ("alive", ent.alive), ("supports_creature", ent.supports_creature), ("soft", ent.soft)) if ok]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
works_tool(C,T,H) :- creature(C), tool(T), hazard(H),
                     care(T,S), care_min(M), S >= M,
                     supports(T),
                     fragile(C), soft(T).
works_tool(C,T,H) :- creature(C), tool(T), hazard(H),
                     care(T,S), care_min(M), S >= M,
                     supports(T),
                     not fragile(C), soft(T).
works_place(C,P) :- creature(C), safe_place(P), good_for(P,C), not needs_damp(C).
works_place(C,P) :- creature(C), safe_place(P), good_for(P,C), needs_damp(C), damp(P).

valid(C,H,T,P) :- creature(C), hazard(H), tool(T), safe_place(P),
                  works_tool(C,T,H), works_place(C,P).

chosen_valid :- choose_creature(C), choose_hazard(H), choose_tool(T), choose_place(P),
                valid(C,H,T,P).

outcome(rescued) :- chosen_valid.
#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("care_min", CARE_MIN))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if creature.fragile:
            lines.append(asp.fact("fragile", cid))
        if creature.needs_damp:
            lines.append(asp.fact("needs_damp", cid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("care", tid, tool.care))
        if tool.soft:
            lines.append(asp.fact("soft", tid))
        if tool.supports:
            lines.append(asp.fact("supports", tid))
    for pid, place in SAFE_PLACES.items():
        lines.append(asp.fact("safe_place", pid))
        if place.damp:
            lines.append(asp.fact("damp", pid))
        for creature_id in sorted(place.good_for):
            lines.append(asp.fact("good_for", pid, creature_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("choose_creature", params.creature),
            asp.fact("choose_hazard", params.hazard),
            asp.fact("choose_tool", params.tool),
            asp.fact("choose_place", params.safe_place),
            "#show outcome/1.",
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny rescue, a moment of caution, a rhyme, and a warm lesson learned."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--safe_place", choices=SAFE_PLACES)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.tool:
        creature = CREATURES[args.creature]
        hazard = HAZARDS[args.hazard] if args.hazard else next(iter(HAZARDS.values()))
        tool = TOOLS[args.tool]
        if not tool_works(creature, hazard, tool):
            raise StoryError(explain_tool_rejection(creature, hazard, tool))
    if args.creature and args.safe_place:
        creature = CREATURES[args.creature]
        safe_place = SAFE_PLACES[args.safe_place]
        if not place_works(creature, safe_place):
            raise StoryError(explain_place_rejection(creature, safe_place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
        and (args.safe_place is None or combo[3] == args.safe_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, hazard_id, tool_id, place_id = rng.choice(sorted(combos))
    eager_gender = rng.choice(["girl", "boy"])
    careful_gender = rng.choice(["girl", "boy"])
    eager_name = _pick_name(rng, eager_gender)
    careful_name = _pick_name(rng, careful_gender, avoid=eager_name)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(
        creature=creature_id,
        hazard=hazard_id,
        tool=tool_id,
        safe_place=place_id,
        eager_name=eager_name,
        eager_gender=eager_gender,
        careful_name=careful_name,
        careful_gender=careful_gender,
        caregiver=caregiver,
    )


def generate(params: StoryParams) -> StorySample:
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.safe_place not in SAFE_PLACES:
        raise StoryError(f"(Unknown safe place: {params.safe_place})")

    creature = CREATURES[params.creature]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    safe_place = SAFE_PLACES[params.safe_place]
    if not tool_works(creature, hazard, tool):
        raise StoryError(explain_tool_rejection(creature, hazard, tool))
    if not place_works(creature, safe_place):
        raise StoryError(explain_place_rejection(creature, safe_place))

    world = tell(
        creature=creature,
        hazard=hazard,
        tool=tool,
        safe_place=safe_place,
        eager_name=params.eager_name,
        eager_gender=params.eager_gender,
        careful_name=params.careful_name,
        careful_gender=params.careful_gender,
        caregiver_type=params.caregiver,
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

    cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("Default resolve failed:", err)

    mismatches = 0
    for params in cases:
        py = "rescued" if (params.creature, params.hazard, params.tool, params.safe_place) in python_set else "invalid"
        asp_res = asp_outcome(params)
        if py != asp_res:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, hazard, tool, safe_place) combos:\n")
        for creature, hazard, tool, place in combos:
            print(f"  {creature:12} {hazard:10} {tool:10} {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.creature} at {p.hazard} with {p.tool} to {p.safe_place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
