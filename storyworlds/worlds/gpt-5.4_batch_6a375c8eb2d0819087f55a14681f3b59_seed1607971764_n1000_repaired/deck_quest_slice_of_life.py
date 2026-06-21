#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py
======================================================

A standalone story world for a small, slice-of-life backyard quest:
a child is helping set up a cozy little treat on the deck, but one
important item slips into a narrow place. The child first wants to solve
the problem the quickest way, then a calm grown-up or older helper offers
a sensible tool, and the quest ends with a changed final image on the deck.

The world model prefers reasonable recovery methods:
some lost items are flat and light, some are soft and puffy, and some are
round and roll farther. Different tools work better for different gaps and
objects. Explicit mismatches are rejected with a clear StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --lost seed_packet --tool grabber
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --lost apple --tool ruler
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --asp
    python storyworlds/worlds/gpt-5.4/deck_quest_slice_of_life.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Quest:
    id: str
    title: str
    opening: str
    goal: str
    ending: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    shape: str
    size: str
    material: str
    place: str
    family_use: str
    can_roll: bool = False
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
class Gap:
    id: str
    label: str
    phrase: str
    width: str
    depth: str
    place_text: str
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
class ToolOption:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    works_for_shapes: set[str]
    works_for_widths: set[str]
    method: str
    qa_text: str
    fail_text: str
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


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    lost = world.get("lost")
    hero = world.get("hero")
    if lost.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck_worry", lost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["quest_drive"] += 1
    out.append("__stuck__")
    return out


def _r_recovered_relief(world: World) -> list[str]:
    out: list[str] = []
    lost = world.get("lost")
    hero = world.get("hero")
    helper = world.get("helper")
    if lost.meters["recovered"] < THRESHOLD:
        return out
    sig = ("recovered_relief", lost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["care"] += 1
    out.append("__recovered__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_worry", tag="emotional", apply=_r_stuck_worry),
    Rule(name="recovered_relief", tag="emotional", apply=_r_recovered_relief),
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


def tool_fits_gap(tool: ToolOption, gap: Gap) -> bool:
    return gap.width in tool.works_for_widths


def tool_handles_item(tool: ToolOption, lost: LostThing) -> bool:
    return lost.shape in tool.works_for_shapes


def can_recover(tool: ToolOption, lost: LostThing, gap: Gap) -> bool:
    return tool.sense >= SENSE_MIN and tool_fits_gap(tool, gap) and tool_handles_item(tool, lost)


def sensible_tools() -> list[ToolOption]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for quest_id in QUESTS:
        for lost_id, lost in LOST_THINGS.items():
            for gap_id, gap in GAPS.items():
                if any(can_recover(tool, lost, gap) for tool in sensible_tools()):
                    combos.append((quest_id, lost_id, gap_id))
    return combos


def best_tool_for(lost: LostThing, gap: Gap) -> ToolOption:
    fits = [tool for tool in sensible_tools() if can_recover(tool, lost, gap)]
    if not fits:
        raise StoryError("(No reasonable recovery tool fits this lost item and gap.)")
    return sorted(fits, key=lambda t: (-t.sense, -t.reach, t.id))[0]


def explain_rejection(tool: ToolOption, lost: LostThing, gap: Gap) -> str:
    reasons: list[str] = []
    if tool.sense < SENSE_MIN:
        reasons.append(
            f"'{tool.label}' is known in the world, but it scores too low on common sense"
        )
    if not tool_fits_gap(tool, gap):
        reasons.append(f"{tool.label} does not fit the {gap.label}")
    if not tool_handles_item(tool, lost):
        reasons.append(f"{tool.label} is a poor way to move {lost.phrase}")
    if not reasons:
        reasons.append("this combination is not reasonable")
    better = ", ".join(t.id for t in sensible_tools() if can_recover(t, lost, gap))
    if better:
        return f"(No story: {'; '.join(reasons)}. Try one of: {better}.)"
    return f"(No story: {'; '.join(reasons)}.)"


def predict_recovery(world: World, tool_id: str) -> dict:
    sim = world.copy()
    tool_cfg = TOOLS[tool_id]
    lost_cfg = sim.facts["lost_cfg"]
    gap_cfg = sim.facts["gap_cfg"]
    if can_recover(tool_cfg, lost_cfg, gap_cfg):
        sim.get("lost").meters["recovered"] += 1
        sim.get("lost").meters["stuck"] = 0.0
        propagate(sim, narrate=False)
    return {
        "recovered": sim.get("lost").meters["recovered"] >= THRESHOLD,
        "hero_relief": sim.get("hero").memes["relief"],
    }


def setup_morning(world: World, hero: Entity, helper: Entity, quest: Quest, lost: Entity, gap: Gap) -> None:
    hero.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a soft afternoon, {hero.id} padded out to the deck with {lost.phrase} in both hands. "
        f"{quest.opening}"
    )
    world.say(
        f"{helper.id} was already there, making room beside a striped cushion and a pitcher of water. "
        f'"{quest.goal}," {helper.pronoun()} said, and the little job felt to {hero.id} like a real quest.'
    )
    world.say(
        f"The deck boards were warm, and the breeze kept nudging at small things as if it wanted to join in."
    )
    world.facts["gap_label"] = gap.label


def slip(world: World, hero: Entity, lost_ent: Entity, lost_cfg: LostThing, gap: Gap) -> None:
    lost_ent.meters["dropped"] += 1
    lost_ent.meters["stuck"] += 1
    if lost_cfg.can_roll:
        lost_ent.meters["rolled"] += 1
        extra = "It bumped once, rolled in a small curve, and vanished "
    else:
        extra = "The breeze flipped it from the edge of the plate and it vanished "
    world.say(
        f"Then {extra}{gap.place_text}."
    )
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} dropped to {hero.pronoun('possessive')} knees and peered down. "
        f"{lost_cfg.phrase.capitalize()} was stuck in the shadowy space {gap.place_text}."
    )


def reach_by_hand(world: World, hero: Entity, gap: Gap) -> None:
    hero.memes["impatience"] += 1
    hero.meters["awkward_reach"] += 1
    world.say(
        f'"I can get it," {hero.id} said, stretching {hero.pronoun("possessive")} arm toward the {gap.label}.'
    )
    world.say(
        f"But the opening was too tricky, and {hero.pronoun()} could only wiggle {hero.pronoun('possessive')} fingers in the dust."
    )


def helper_guides(world: World, helper: Entity, hero: Entity, lost_cfg: LostThing, gap: Gap, tool_cfg: ToolOption) -> None:
    pred = predict_recovery(world, tool_cfg.id)
    world.facts["predicted_recovered"] = pred["recovered"]
    hero.memes["trust"] += 1
    world.say(
        f'{helper.id} knelt beside {hero.id} and smiled instead of hurrying. '
        f'"This is still your quest," {helper.pronoun()} said. '
        f'"We just need the right helper for {lost_cfg.label} in a {gap.label}."'
    )


def use_tool(world: World, hero: Entity, helper: Entity, tool_ent: Entity, tool_cfg: ToolOption, lost_ent: Entity, lost_cfg: LostThing) -> None:
    hero.memes["focus"] += 1
    tool_ent.meters["used"] += 1
    if tool_cfg.id == "grabber":
        lost_ent.meters["pinched"] += 1
    elif tool_cfg.id == "broom":
        lost_ent.meters["nudged"] += 1
    elif tool_cfg.id == "ruler":
        lost_ent.meters["slid"] += 1
    elif tool_cfg.id == "tongs":
        lost_ent.meters["lifted"] += 1
    lost_ent.meters["recovered"] += 1
    lost_ent.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} handed over {tool_cfg.phrase}, and {hero.id} {tool_cfg.method}."
    )
    world.say(
        f"In another second, {lost_cfg.phrase} was back in {hero.pronoun('possessive')} hands, a little dusty but safe."
    )


def finish_quest(world: World, hero: Entity, helper: Entity, quest: Quest, lost_cfg: LostThing) -> None:
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'{hero.id} brushed off the dust and set {lost_cfg.label} in place at last. '
        f'{quest.ending}'
    )
    world.say(
        f'"Quest done," {hero.id} whispered, and {helper.id} laughed the soft laugh that means everything is all right.'
    )
    world.say(
        f"The deck looked ordinary again, but to {hero.id} it felt brighter because a hard little moment had been solved the patient way."
    )


def tell(
    quest: Quest,
    lost_cfg: LostThing,
    gap_cfg: Gap,
    tool_cfg: ToolOption,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_name: str = "Grandma",
    helper_type: str = "grandmother",
    pet: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["small", "earnest"],
        attrs={"pet": pet},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={"pet": pet},
    ))
    lost_ent = world.add(Entity(
        id="lost",
        type="lost_thing",
        label=lost_cfg.label,
        phrase=lost_cfg.phrase,
        portable=True,
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        tool=True,
    ))
    world.add(Entity(id="deck", type="deck", label="deck"))
    world.facts.update(
        quest=quest,
        lost_cfg=lost_cfg,
        gap_cfg=gap_cfg,
        tool_cfg=tool_cfg,
        hero=hero,
        helper=helper,
        pet=pet,
    )

    setup_morning(world, hero, helper, quest, lost_ent, gap_cfg)
    world.para()
    slip(world, hero, lost_ent, lost_cfg, gap_cfg)
    reach_by_hand(world, hero, gap_cfg)
    helper_guides(world, helper, hero, lost_cfg, gap_cfg, tool_cfg)
    world.para()
    use_tool(world, hero, helper, tool_ent, tool_cfg, lost_ent, lost_cfg)
    finish_quest(world, hero, helper, quest, lost_cfg)

    world.facts.update(
        recovered=lost_ent.meters["recovered"] >= THRESHOLD,
        tried_hand=hero.meters["awkward_reach"] >= THRESHOLD,
        outcome="recovered",
        lost=lost_ent,
        tool=tool_ent,
    )
    return world


QUESTS = {
    "snack": Quest(
        id="snack",
        title="deck snack quest",
        opening="The mission was simple: carry one small treat to the shaded corner before the ice clinked itself warm.",
        goal="Bring our little deck snack over here",
        ending="Soon the plate was ready, the glasses shone with lemon slices, and the tiny deck feast could begin.",
        tags={"deck", "snack"},
    ),
    "planting": Quest(
        id="planting",
        title="deck planting quest",
        opening="The plan was to sort planting things on the deck before going down to the garden beds.",
        goal="Bring the planting bit right here so we can start",
        ending="Soon the cups of soil, the spoon, and the saved little treasure were lined up, ready for planting time.",
        tags={"deck", "garden", "planting"},
    ),
    "storytime": Quest(
        id="storytime",
        title="deck story quest",
        opening="The idea was to make a story corner on the deck before the sky turned peach at the edges.",
        goal="Bring the last story piece to the blanket fort corner",
        ending="Soon the blanket, the quiet seat, and the rescued little thing were waiting for storytime on the deck.",
        tags={"deck", "story"},
    ),
}

LOST_THINGS = {
    "seed_packet": LostThing(
        id="seed_packet",
        label="seed packet",
        phrase="a seed packet with painted marigolds on it",
        shape="flat",
        size="small",
        material="paper",
        place="deck",
        family_use="for planting",
        can_roll=False,
        tags={"seeds", "paper", "garden"},
    ),
    "napkin": LostThing(
        id="napkin",
        label="napkin",
        phrase="a folded yellow napkin",
        shape="flat",
        size="small",
        material="cloth",
        place="deck",
        family_use="for snack time",
        can_roll=False,
        tags={"cloth", "snack"},
    ),
    "apple": LostThing(
        id="apple",
        label="apple",
        phrase="a shiny red apple",
        shape="round",
        size="small",
        material="fruit",
        place="deck",
        family_use="for a snack plate",
        can_roll=True,
        tags={"fruit", "snack"},
    ),
    "mitten": LostThing(
        id="mitten",
        label="mitten",
        phrase="a small blue mitten",
        shape="soft",
        size="small",
        material="yarn",
        place="deck",
        family_use="for keeping hands warm later",
        can_roll=False,
        tags={"clothes", "soft"},
    ),
}

GAPS = {
    "between_boards": Gap(
        id="between_boards",
        label="gap between the deck boards",
        phrase="between the deck boards",
        width="narrow",
        depth="shallow",
        place_text="between two deck boards",
        tags={"deck", "narrow_gap"},
    ),
    "under_bench": Gap(
        id="under_bench",
        label="space under the deck bench",
        phrase="under the deck bench",
        width="wide",
        depth="shallow",
        place_text="under the deck bench",
        tags={"deck", "bench"},
    ),
    "by_step": Gap(
        id="by_step",
        label="crack beside the deck step",
        phrase="beside the deck step",
        width="medium",
        depth="deep",
        place_text="beside the bottom deck step",
        tags={"deck", "step"},
    ),
}

TOOLS = {
    "grabber": ToolOption(
        id="grabber",
        label="grabber",
        phrase="the long kitchen grabber",
        sense=3,
        reach=3,
        works_for_shapes={"flat", "soft", "round"},
        works_for_widths={"medium", "wide"},
        method="guided the grabber down carefully until the rubber tip pinched the thing just right",
        qa_text="used a long grabber to pinch and lift it out",
        fail_text="tried to lower a grabber in, but the opening was too tight for it",
        tags={"grabber", "tool"},
    ),
    "broom": ToolOption(
        id="broom",
        label="broom",
        phrase="the porch broom",
        sense=3,
        reach=3,
        works_for_shapes={"round", "soft"},
        works_for_widths={"wide", "medium"},
        method="lay on one elbow and nudged gently with the broom until the lost thing rolled back into reach",
        qa_text="used a broom to nudge it back within reach",
        fail_text="tried to poke with a broom, but the broom head was too clumsy for that spot",
        tags={"broom", "tool"},
    ),
    "ruler": ToolOption(
        id="ruler",
        label="ruler",
        phrase="a wooden ruler from the junk drawer",
        sense=2,
        reach=2,
        works_for_shapes={"flat"},
        works_for_widths={"narrow", "medium"},
        method="slid the ruler into the crack and drew the little thing back inch by inch",
        qa_text="slid a ruler into the crack and pulled it back",
        fail_text="tried to slide a ruler in, but it could not move that kind of item",
        tags={"ruler", "tool"},
    ),
    "tongs": ToolOption(
        id="tongs",
        label="tongs",
        phrase="the salad tongs",
        sense=2,
        reach=2,
        works_for_shapes={"soft", "round"},
        works_for_widths={"wide"},
        method="reached in with the tongs and lifted slowly so nothing slipped away again",
        qa_text="used tongs to lift it out",
        fail_text="tried to use tongs, but there was not enough room to open them",
        tags={"tongs", "tool"},
    ),
    "bare_hand": ToolOption(
        id="bare_hand",
        label="bare hand",
        phrase="just a hand",
        sense=1,
        reach=1,
        works_for_shapes={"flat", "soft", "round"},
        works_for_widths={"wide"},
        method="reached right in",
        qa_text="reached in by hand",
        fail_text="tried to reach in by hand, but that did not work",
        tags={"hand"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Anna", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Noah", "Jack"]
HELPERS = [
    {"name": "Grandma", "type": "grandmother"},
    {"name": "Grandpa", "type": "grandfather"},
    {"name": "Mom", "type": "mother"},
    {"name": "Dad", "type": "father"},
]
PETS = ["the cat", "the puppy", "their old dog", "the kitten", ""]


@dataclass
class StoryParams:
    quest: str
    lost: str
    gap: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    pet: str = ""
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
    "deck": [
        (
            "What is a deck?",
            "A deck is a flat outdoor platform attached to a house. People sit, eat, and rest there because it feels like part of the home and part of the yard.",
        )
    ],
    "seeds": [
        (
            "What is a seed packet?",
            "A seed packet is a small paper packet that holds seeds for planting. It keeps the tiny seeds together until it is time to put them in soil.",
        )
    ],
    "paper": [
        (
            "Why can a paper packet slip into a crack easily?",
            "Paper is thin and light, so a breeze can push it around. If there is a narrow crack, a flat paper thing can slide into it very quickly.",
        )
    ],
    "fruit": [
        (
            "Why does an apple roll away?",
            "An apple is round, so it can roll when it is nudged. On a smooth board or a small slope, it may keep moving until something stops it.",
        )
    ],
    "soft": [
        (
            "Why can a soft mitten be tricky to pick up?",
            "A soft mitten can fold and flop instead of holding one shape. That means a tool has to catch it gently or it may slip away.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool for?",
            "A grabber is a long tool that helps you reach something without crawling into a tight place. The pinching end lets you hold the object from farther away.",
        )
    ],
    "broom": [
        (
            "How can a broom help move something?",
            "A broom can push or sweep an object closer when it is too far away to reach. It works best when there is enough space to nudge gently.",
        )
    ],
    "ruler": [
        (
            "How can a ruler help in a crack?",
            "A thin ruler can slide into a narrow crack and pull a flat thing back. It is useful when a bigger tool will not fit.",
        )
    ],
    "tongs": [
        (
            "What are tongs good for?",
            "Tongs are good for picking something up by squeezing it between two arms. They need enough room to open and close around the object.",
        )
    ],
    "patience": [
        (
            "Why does patience help with a tricky problem?",
            "Patience helps you slow down and notice what will really work. When you stop rushing, you are more likely to solve the problem safely.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "deck",
    "seeds",
    "paper",
    "fruit",
    "soft",
    "grabber",
    "broom",
    "ruler",
    "tongs",
    "patience",
]


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest"]
    lost_cfg = world.facts["lost_cfg"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old about a small quest on a deck, and include the word "deck".',
        f"Tell a cozy home story where {hero.id} loses {lost_cfg.phrase} during {quest.title}, and {helper.id} helps {hero.pronoun('object')} solve the problem patiently.",
        f'Write a simple Quest story in a backyard setting where a little everyday problem becomes important for a moment and ends with a calm, happy image on the deck.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    quest = world.facts["quest"]
    lost_cfg = world.facts["lost_cfg"]
    gap_cfg = world.facts["gap_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was trying to finish {quest.title}, and {helper.id}, who stayed nearby to help. Their little job felt important because the family was getting something ready together on the deck.",
        ),
        (
            f"What was {hero.id}'s quest?",
            f"{hero.id}'s quest was to carry and place {lost_cfg.label} for {quest.title}. It was a small home job, but it mattered because it was the last piece they needed.",
        ),
        (
            f"What went wrong on the deck?",
            f"{lost_cfg.phrase.capitalize()} slipped {gap_cfg.place_text} and got stuck. That changed the quest at once, because {hero.id} could not finish the cozy plan until it came back.",
        ),
    ]
    if world.facts.get("tried_hand"):
        qa.append(
            (
                f"Why didn't {hero.id} just grab it right away?",
                f"{hero.id} tried to reach by hand first, but the opening was too awkward. The problem was not only distance; the shape of the gap made rushing useless.",
            )
        )
    qa.append(
        (
            f"How did {helper.id} help?",
            f"{helper.id} stayed calm and suggested the right tool instead of grabbing the job away. That helped {hero.id} keep going with the quest while learning a better method.",
        )
    )
    qa.append(
        (
            f"How did they get the {lost_cfg.label} back?",
            f"They {tool_cfg.qa_text}. It worked because that tool matched both the shape of the lost thing and the kind of space where it was stuck.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the small family plan ready at last on the deck. The final image shows that the quest was finished and the worried feeling had turned into pride and ease.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"deck", "patience"} | set(world.facts["lost_cfg"].tags) | set(world.facts["tool_cfg"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="planting",
        lost="seed_packet",
        gap="between_boards",
        tool="ruler",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Grandma",
        helper_type="grandmother",
        pet="the cat",
    ),
    StoryParams(
        quest="snack",
        lost="apple",
        gap="under_bench",
        tool="broom",
        hero_name="Ben",
        hero_gender="boy",
        helper_name="Grandpa",
        helper_type="grandfather",
        pet="their old dog",
    ),
    StoryParams(
        quest="storytime",
        lost="mitten",
        gap="by_step",
        tool="grabber",
        hero_name="Lucy",
        hero_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        pet="",
    ),
    StoryParams(
        quest="snack",
        lost="napkin",
        gap="between_boards",
        tool="ruler",
        hero_name="Theo",
        hero_gender="boy",
        helper_name="Dad",
        helper_type="father",
        pet="the puppy",
    ),
    StoryParams(
        quest="storytime",
        lost="apple",
        gap="by_step",
        tool="grabber",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Grandpa",
        helper_type="grandfather",
        pet="the kitten",
    ),
]


def outcome_of(params: StoryParams) -> str:
    lost_cfg = LOST_THINGS[params.lost]
    gap_cfg = GAPS[params.gap]
    tool_cfg = TOOLS[params.tool]
    return "recovered" if can_recover(tool_cfg, lost_cfg, gap_cfg) else "stuck"


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
works(T, L, G) :- sensible_tool(T), shape(L, Sh), tool_shape(T, Sh), width(G, W), tool_width(T, W).
valid(Q, L, G) :- quest(Q), lost(L), gap(G), works(_, L, G).

outcome(recovered) :- chosen_tool(T), chosen_lost(L), chosen_gap(G), works(T, L, G).
outcome(stuck) :- chosen_tool(T), chosen_lost(L), chosen_gap(G), not works(T, L, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for lost_id, lost in LOST_THINGS.items():
        lines.append(asp.fact("lost", lost_id))
        lines.append(asp.fact("shape", lost_id, lost.shape))
    for gap_id, gap in GAPS.items():
        lines.append(asp.fact("gap", gap_id))
        lines.append(asp.fact("width", gap_id, gap.width))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for sh in sorted(tool.works_for_shapes):
            lines.append(asp.fact("tool_shape", tool_id, sh))
        for wd in sorted(tool.works_for_widths):
            lines.append(asp.fact("tool_width", tool_id, wd))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_lost", params.lost),
            asp.fact("chosen_gap", params.gap),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sense = set(asp_sensible_tools())
    p_sense = {tool.id for tool in sensible_tools()}
    if c_sense == p_sense:
        print(f"OK: sensible tools match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            ns = parser.parse_args([])
            case = resolve_params(ns, random.Random(s))
            case.seed = s
            cases.append(case)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small deck quest with a lost thing and a sensible tool."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--gap", choices=GAPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.tool and args.lost and args.gap:
        tool_cfg = TOOLS[args.tool]
        lost_cfg = LOST_THINGS[args.lost]
        gap_cfg = GAPS[args.gap]
        if not can_recover(tool_cfg, lost_cfg, gap_cfg):
            raise StoryError(explain_rejection(tool_cfg, lost_cfg, gap_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.lost is None or combo[1] == args.lost)
        and (args.gap is None or combo[2] == args.gap)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, lost_id, gap_id = rng.choice(sorted(combos))
    lost_cfg = LOST_THINGS[lost_id]
    gap_cfg = GAPS[gap_id]

    valid_tools = [tool.id for tool in sensible_tools() if can_recover(tool, lost_cfg, gap_cfg)]
    if args.tool:
        if args.tool not in valid_tools:
            raise StoryError(explain_rejection(TOOLS[args.tool], lost_cfg, gap_cfg))
        tool_id = args.tool
    else:
        tool_id = rng.choice(sorted(valid_tools))

    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)

    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_lookup = {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }
    helper_name = helper_lookup[helper_type]
    pet = rng.choice(PETS)

    return StoryParams(
        quest=quest_id,
        lost=lost_id,
        gap=gap_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.lost not in LOST_THINGS:
        raise StoryError(f"(Unknown lost thing: {params.lost})")
    if params.gap not in GAPS:
        raise StoryError(f"(Unknown gap: {params.gap})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    quest = QUESTS[params.quest]
    lost_cfg = LOST_THINGS[params.lost]
    gap_cfg = GAPS[params.gap]
    tool_cfg = TOOLS[params.tool]

    if not can_recover(tool_cfg, lost_cfg, gap_cfg):
        raise StoryError(explain_rejection(tool_cfg, lost_cfg, gap_cfg))

    world = tell(
        quest=quest,
        lost_cfg=lost_cfg,
        gap_cfg=gap_cfg,
        tool_cfg=tool_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        pet=params.pet,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, lost, gap) combos:\n")
        for quest_id, lost_id, gap_id in combos:
            tools = [tool.id for tool in sensible_tools() if can_recover(tool, LOST_THINGS[lost_id], GAPS[gap_id])]
            print(f"  {quest_id:10} {lost_id:12} {gap_id:15} [{', '.join(sorted(tools))}]")
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
            header = f"### {p.hero_name}: {p.quest} on the deck ({p.lost}, {p.gap}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
