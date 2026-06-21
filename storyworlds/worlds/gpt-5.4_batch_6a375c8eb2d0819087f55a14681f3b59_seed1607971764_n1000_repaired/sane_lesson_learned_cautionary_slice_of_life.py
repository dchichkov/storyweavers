#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py
===========================================================================

A standalone storyworld for a small cautionary slice-of-life domain:
a child wants to help make a snack, reaches for a grown-up knife, and learns
the sane, safe way to help in the kitchen.

The world models:
- typed entities with physical meters and emotional memes
- a reasonableness gate over foods, unsafe tools, and child-safe tools
- a simple causal engine for "minor nick -> fear/care" and
  "snack ready -> pride/relief"
- a declarative ASP twin for valid combinations and story outcome parity

Run it
------
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --food apple
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --food yogurt
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --asp
    python storyworlds/worlds/gpt-5.4/sane_lesson_learned_cautionary_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}
BRAVERY_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sharp: bool = False
    child_safe: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Food:
    id: str
    label: str
    phrase: str
    firmness: int
    slippery: int
    slices: str
    accident: str
    needs_cut: bool = True
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
class UnsafeTool:
    id: str
    label: str
    phrase: str
    sharpness: int
    warning: str
    qa_text: str
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
class SafeTool:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    finish_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "sibling"}]

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


def _r_nick_emotions(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    parent = world.entities.get("parent")
    sibling = world.entities.get("sibling")
    if hero is None:
        return out
    if hero.meters["nicked"] < THRESHOLD:
        return out
    sig = ("nick_emotions", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["regret"] += 1
    if parent is not None:
        parent.memes["care"] += 1
    if sibling is not None:
        sibling.memes["worry"] += 1
    out.append("__nick__")
    return out


def _r_ready_pride(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    hero = world.entities.get("hero")
    sibling = world.entities.get("sibling")
    if bowl is None or hero is None or sibling is None:
        return []
    if bowl.meters["ready"] < THRESHOLD:
        return []
    sig = ("ready_pride", bowl.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    return ["__ready__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="nick_emotions", tag="social", apply=_r_nick_emotions),
    Rule(name="ready_pride", tag="social", apply=_r_ready_pride),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(line for line in lines if not line.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


FOODS = {
    "apple": Food(
        id="apple",
        label="apple",
        phrase="a shiny red apple",
        firmness=3,
        slippery=2,
        slices="little crescent slices",
        accident="The apple skidded on the board just as the knife came down.",
        needs_cut=True,
        tags={"apple", "kitchen", "ask_first"},
    ),
    "banana": Food(
        id="banana",
        label="banana",
        phrase="a ripe banana",
        firmness=1,
        slippery=1,
        slices="soft round banana coins",
        accident="The banana bent under the blade and the hand holding it slipped too close.",
        needs_cut=True,
        tags={"banana", "kitchen", "ask_first"},
    ),
    "cucumber": Food(
        id="cucumber",
        label="cucumber",
        phrase="a cool green cucumber",
        firmness=2,
        slippery=2,
        slices="crisp green cucumber moons",
        accident="The cucumber rolled a little on the board and the blade scraped the wrong place.",
        needs_cut=True,
        tags={"cucumber", "kitchen", "ask_first"},
    ),
    "strawberry": Food(
        id="strawberry",
        label="strawberry",
        phrase="a bright strawberry",
        firmness=1,
        slippery=2,
        slices="small red strawberry pieces",
        accident="The strawberry squished and slid, and the quick little cut went the wrong way.",
        needs_cut=True,
        tags={"strawberry", "kitchen", "ask_first"},
    ),
    "yogurt": Food(
        id="yogurt",
        label="yogurt cup",
        phrase="a little yogurt cup",
        firmness=0,
        slippery=0,
        slices="",
        accident="",
        needs_cut=False,
        tags={"kitchen"},
    ),
}

UNSAFE_TOOLS = {
    "chef_knife": UnsafeTool(
        id="chef_knife",
        label="chef's knife",
        phrase="the big chef's knife",
        sharpness=3,
        warning="That knife is for grown-up hands.",
        qa_text="reached for the big chef's knife",
        tags={"knife", "sharp_tool"},
    ),
    "paring_knife": UnsafeTool(
        id="paring_knife",
        label="paring knife",
        phrase="the small paring knife",
        sharpness=2,
        warning="That little knife is still a real sharp knife.",
        qa_text="reached for the paring knife",
        tags={"knife", "sharp_tool"},
    ),
    "serrated_knife": UnsafeTool(
        id="serrated_knife",
        label="serrated knife",
        phrase="the serrated knife",
        sharpness=3,
        warning="That knife can bite skin before you even mean to.",
        qa_text="reached for the serrated knife",
        tags={"knife", "sharp_tool"},
    ),
}

SAFE_TOOLS = {
    "apple_slicer": SafeTool(
        id="apple_slicer",
        label="apple slicer",
        phrase="an apple slicer with two easy handles",
        supports={"apple"},
        finish_text="pressed the apple slicer down with both hands",
        tags={"apple_slicer", "safe_tool"},
    ),
    "kid_knife": SafeTool(
        id="kid_knife",
        label="kid knife",
        phrase="a child-safe kitchen knife with a blunt edge",
        supports={"banana", "cucumber", "strawberry"},
        finish_text="used the kid knife with slow little sawing motions",
        tags={"kid_knife", "safe_tool"},
    ),
    "crinkle_cutter": SafeTool(
        id="crinkle_cutter",
        label="crinkle cutter",
        phrase="a crinkle cutter with a broad handle",
        supports={"cucumber", "strawberry"},
        finish_text="pushed the crinkle cutter straight down",
        tags={"crinkle_cutter", "safe_tool"},
    ),
    "banana_slicer": SafeTool(
        id="banana_slicer",
        label="banana slicer",
        phrase="a banana slicer that pressed neat round shapes",
        supports={"banana"},
        finish_text="pressed the banana slicer through the soft fruit",
        tags={"banana_slicer", "safe_tool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["careful", "steady", "sensible", "curious", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for food_id, food in FOODS.items():
        if not food.needs_cut:
            continue
        for unsafe_id, unsafe in UNSAFE_TOOLS.items():
            if unsafe.sharpness < 2:
                continue
            for safe_id, safe in SAFE_TOOLS.items():
                if food_id in safe.supports:
                    combos.append((food_id, unsafe_id, safe_id))
    return sorted(combos)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, sibling_age: int, trait: str) -> bool:
    sibling_older = relation == "siblings" and sibling_age > hero_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if sibling_older else 0.0)
    return sibling_older and authority > BRAVERY_INIT


def explain_rejection(food: Food, safe_tool: Optional[SafeTool] = None) -> str:
    if not food.needs_cut:
        return (
            f"(No story: {food.phrase} does not need slicing here, so there is no honest "
            f"reason for a child to reach for a knife. Pick a snack like an apple, banana, "
            f"cucumber, or strawberry.)"
        )
    if safe_tool is not None and food.id not in safe_tool.supports:
        return (
            f"(No story: {safe_tool.label} is not a sane child-safe tool for {food.label}. "
            f"The safer tool has to actually work for the food being prepared.)"
        )
    return "(No story: this combination does not fit the kitchen-helping world.)"


def explain_combo(food_id: str, unsafe_id: str, safe_id: str) -> str:
    food = FOODS[food_id]
    safe = SAFE_TOOLS[safe_id]
    return (
        f"(No story: {food.label} with {safe.label} is not a supported safe fix here. "
        f"The world only tells stories where the child-safe tool can really finish the snack.)"
    )


def predict_nick(world: World, food_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    food = sim.get("food")
    cfg = FOODS[food_id]
    _do_unsafe_attempt(sim, hero, food, cfg, narrate=False)
    return {
        "nicked": hero.meters["nicked"] >= THRESHOLD,
        "fear": hero.memes["fear"],
    }


def _do_unsafe_attempt(world: World, hero: Entity, food_ent: Entity, food: Food,
                       narrate: bool = True) -> None:
    food_ent.meters["cut_started"] += 1
    food_ent.meters["slipped"] += float(food.slippery)
    hero.meters["nicked"] += 1
    propagate(world, narrate=narrate)


def _do_safe_finish(world: World, hero: Entity, food_ent: Entity, bowl: Entity,
                    safe_tool: SafeTool, food: Food, narrate: bool = True) -> None:
    food_ent.meters["prepared"] += 1
    bowl.meters["ready"] += 1
    hero.memes["confidence"] += 1
    hero.memes["joy"] += 1
    world.facts["finished_with"] = safe_tool.id
    propagate(world, narrate=narrate)


def kitchen_setup(world: World, hero: Entity, sibling: Entity, parent: Entity,
                  food: Food) -> None:
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"Late in the afternoon, {hero.id} and {sibling.id} stood on kitchen stools while "
        f"{parent.label_word} rinsed {food.phrase} at the sink."
    )
    world.say(
        f"They were making a small snack plate for home, and the whole room smelled clean and bright."
    )
    world.say(
        f'{hero.id} wanted to help so much that {hero.pronoun()} kept leaning closer to the cutting board.'
    )


def temptation(world: World, hero: Entity, unsafe: UnsafeTool, food: Food) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f"On the counter beside the board lay {unsafe.phrase}. "
        f"{hero.id} looked at it, then at {food.phrase}, and said, "
        f'"I can do it fast."'
    )


def warning(world: World, sibling: Entity, hero: Entity, parent: Entity,
            unsafe: UnsafeTool, food: Food) -> None:
    pred = predict_nick(world, food.id)
    world.facts["predicted_nick"] = pred["nicked"]
    sibling.memes["caution"] += 1
    extra = ""
    if sibling.memes["caution"] >= 6:
        extra = f" {sibling.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{sibling.id} shook {sibling.pronoun("possessive")} head. "{unsafe.warning} '
        f'If {food.label} slips, you could cut your finger."{extra}'
    )
    world.say(
        f'{parent.label_word.capitalize()} turned from the sink and added, "Ask first, and we will find the safe way to help."'
    )


def back_down(world: World, hero: Entity, sibling: Entity, parent: Entity) -> None:
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    hero.memes["bravery"] = 0.0
    world.say(
        f"{hero.id} looked at the knife again, then at {sibling.id}, and let out a small breath."
    )
    world.say(
        f'"Okay," {hero.pronoun()} said. "I want to help the sane way."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled right away, glad {hero.id} had asked instead of grabbing first.'
    )


def defy(world: World, hero: Entity, sibling: Entity, unsafe: UnsafeTool) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But wanting to seem big tugged harder for one more moment. '
        f'{hero.id} reached for {unsafe.phrase} before anyone could stop {hero.pronoun("object")}.'
    )


def accident(world: World, hero: Entity, sibling: Entity, parent: Entity,
             food_ent: Entity, food: Food) -> None:
    _do_unsafe_attempt(world, hero, food_ent, food, narrate=False)
    world.say(food.accident)
    world.say(
        f"{hero.id} gave a startled gasp and pulled {hero.pronoun('possessive')} hand back. "
        f"A tiny red line showed on one finger."
    )
    world.say(f'"{parent.label_word.upper()}!" {sibling.id} cried.')
    world.facts["accident_happened"] = True


def first_aid(world: World, hero: Entity, parent: Entity) -> None:
    hero.meters["cleaned"] += 1
    hero.meters["bandaged"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came quickly, set the knife far back on the counter, "
        f"and carried {hero.id} to the sink."
    )
    world.say(
        f"{parent.pronoun().capitalize()} rinsed the little cut with cool water, wrapped a bandage around the finger, "
        f"and held {hero.id} close until the trembling stopped."
    )
    world.say(
        f'"Helping is kind," {parent.pronoun()} said softly, "but the sane way to help in a kitchen is to ask first '
        f'and use tools made for you."'
    )


def safe_lesson(world: World, hero: Entity, sibling: Entity, parent: Entity,
                safe_tool: SafeTool) -> None:
    hero.memes["lesson"] += 1
    sibling.memes["lesson"] += 1
    world.say(
        f"Then {parent.label_word} brought out {safe_tool.phrase} and set it beside the board."
    )
    world.say(
        f'"You can still help," {parent.pronoun()} said. "Now we do it the safe way, together."'
    )


def safe_finish(world: World, hero: Entity, sibling: Entity, parent: Entity,
                food_ent: Entity, bowl: Entity, safe_tool: SafeTool, food: Food,
                after_accident: bool) -> None:
    _do_safe_finish(world, hero, food_ent, bowl, safe_tool, food, narrate=False)
    opener = "With the bandage on and everyone calmer," if after_accident else "A moment later,"
    world.say(
        f"{opener} {hero.id} {safe_tool.finish_text}, while {sibling.id} held the board steady."
    )
    world.say(
        f"Soon the plate held {food.slices}, and nothing else got hurt."
    )
    world.say(
        f"When they carried the snack to the table, {hero.id} lifted {hero.pronoun('possessive')} bandaged hand a little and smiled."
    )
    world.say(
        "The lesson stayed there in the quiet kitchen: helping felt best when it was careful, calm, and safe."
    )


def tell(food: Food, unsafe: UnsafeTool, safe_tool: SafeTool,
         hero_name: str = "Lily", hero_gender: str = "girl",
         sibling_name: str = "Ben", sibling_gender: str = "boy",
         sibling_trait: str = "careful", parent_type: str = "mother",
         hero_age: int = 5, sibling_age: int = 7, relation: str = "siblings",
         trust: int = 6) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        age=hero_age,
        traits=["eager"],
        attrs={"name": hero_name, "relation": relation},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=sibling_gender,
        label=sibling_name,
        role="sibling",
        age=sibling_age,
        traits=[sibling_trait],
        attrs={"name": sibling_name, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    food_ent = world.add(Entity(
        id="food",
        type="food",
        label=food.label,
        edible=True,
        attrs={},
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="plate",
        label="snack plate",
        attrs={},
    ))
    knife = world.add(Entity(
        id="unsafe_tool",
        type="tool",
        label=unsafe.label,
        sharp=True,
        attrs={},
    ))
    safe_ent = world.add(Entity(
        id="safe_tool",
        type="tool",
        label=safe_tool.label,
        child_safe=True,
        attrs={},
    ))

    hero.memes["bravery"] = BRAVERY_INIT
    sibling.memes["caution"] = initial_caution(sibling_trait)
    sibling.memes["trust"] = float(trust)
    parent.memes["care"] = 0.0
    hero.meters["nicked"] = 0.0
    bowl.meters["ready"] = 0.0
    world.facts.update(
        hero=hero,
        sibling=sibling,
        parent=parent,
        food_cfg=food,
        unsafe_cfg=unsafe,
        safe_cfg=safe_tool,
        relation=relation,
        accident_happened=False,
    )

    kitchen_setup(world, hero, sibling, parent, food)
    world.para()
    temptation(world, hero, unsafe, food)
    warning(world, sibling, hero, parent, unsafe, food)

    averted = would_avert(relation, hero_age, sibling_age, sibling_trait)
    world.facts["outcome"] = "averted" if averted else "nicked"

    world.para()
    if averted:
        back_down(world, hero, sibling, parent)
        safe_lesson(world, hero, sibling, parent, safe_tool)
        safe_finish(world, hero, sibling, parent, food_ent, bowl, safe_tool, food, after_accident=False)
    else:
        defy(world, hero, sibling, unsafe)
        accident(world, hero, sibling, parent, food_ent, food)
        world.para()
        first_aid(world, hero, parent)
        safe_lesson(world, hero, sibling, parent, safe_tool)
        world.para()
        safe_finish(world, hero, sibling, parent, food_ent, bowl, safe_tool, food, after_accident=True)

    world.facts.update(
        food=food_ent,
        bowl=bowl,
        knife=knife,
        safe_tool_ent=safe_ent,
        snack_ready=bowl.meters["ready"] >= THRESHOLD,
        bandaged=hero.meters["bandaged"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    food: str
    unsafe_tool: str
    safe_tool: str
    hero_name: str
    hero_gender: str
    sibling_name: str
    sibling_gender: str
    parent: str
    sibling_trait: str
    hero_age: int = 5
    sibling_age: int = 7
    relation: str = "siblings"
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
    "knife": [
        (
            "Why are kitchen knives not toys?",
            "Kitchen knives are made to cut food with very sharp edges. They can cut skin quickly, so children should only use them with a grown-up's help."
        )
    ],
    "sharp_tool": [
        (
            "What can happen if a sharp tool slips?",
            "If a sharp tool slips, it can cut the hand that is holding the food. That is why steady hands and the right tool matter."
        )
    ],
    "safe_tool": [
        (
            "What is a child-safe kitchen tool?",
            "It is a kitchen tool made so a child can help more safely, often with blunt edges or handles that are easier to hold. A grown-up should still stay nearby."
        )
    ],
    "ask_first": [
        (
            "Why should children ask before using kitchen tools?",
            "A grown-up can choose the right tool for the job and stay close to help. Asking first is a safe habit because not every tool is made for little hands."
        )
    ],
    "apple": [
        (
            "Why do apples need a different tool than soft fruit?",
            "Apples are firm, so they take more force to cut. A tool with good handles, like an apple slicer, helps keep little hands farther from danger."
        )
    ],
    "banana": [
        (
            "Why is a banana easier to slice than an apple?",
            "A banana is soft, so it does not need a very strong blade. That is why a gentler tool can work for it."
        )
    ],
    "cucumber": [
        (
            "Why can a cucumber be tricky to cut?",
            "A cucumber can feel smooth and roll on a board. If the food moves, the tool can go the wrong way."
        )
    ],
    "strawberry": [
        (
            "Why can a strawberry slip when you cut it?",
            "A strawberry is small, soft, and juicy, so it can squish and slide. That makes it harder for little hands to hold steady."
        )
    ],
    "apple_slicer": [
        (
            "What does an apple slicer do?",
            "An apple slicer presses down from the top and cuts the apple into pieces at once. Its side handles help your hands stay away from the cutting part."
        )
    ],
    "kid_knife": [
        (
            "What is a kid knife?",
            "A kid knife is a child-safe kitchen knife with a blunter edge than a grown-up knife. It helps children learn slowly with a grown-up nearby."
        )
    ],
    "crinkle_cutter": [
        (
            "What is a crinkle cutter?",
            "A crinkle cutter is a handled cutter that goes straight down into soft food. The broad handle gives a steadier grip than a small sharp knife."
        )
    ],
    "banana_slicer": [
        (
            "What is a banana slicer?",
            "A banana slicer is a tool that presses soft banana into neat round slices. It works because bananas are gentle and easy to cut."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a small cut and helps keep it clean. It also reminds you to be gentle while the skin heals."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "knife",
    "sharp_tool",
    "safe_tool",
    "ask_first",
    "apple",
    "banana",
    "cucumber",
    "strawberry",
    "apple_slicer",
    "kid_knife",
    "crinkle_cutter",
    "banana_slicer",
    "bandage",
]


CURATED = [
    StoryParams(
        food="apple",
        unsafe_tool="chef_knife",
        safe_tool="apple_slicer",
        hero_name="Lily",
        hero_gender="girl",
        sibling_name="Ben",
        sibling_gender="boy",
        parent="mother",
        sibling_trait="careful",
        hero_age=5,
        sibling_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        food="banana",
        unsafe_tool="paring_knife",
        safe_tool="banana_slicer",
        hero_name="Max",
        hero_gender="boy",
        sibling_name="Ava",
        sibling_gender="girl",
        parent="father",
        sibling_trait="gentle",
        hero_age=6,
        sibling_age=6,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        food="cucumber",
        unsafe_tool="serrated_knife",
        safe_tool="crinkle_cutter",
        hero_name="Nora",
        hero_gender="girl",
        sibling_name="Theo",
        sibling_gender="boy",
        parent="mother",
        sibling_trait="steady",
        hero_age=4,
        sibling_age=8,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        food="strawberry",
        unsafe_tool="paring_knife",
        safe_tool="kid_knife",
        hero_name="Sam",
        hero_gender="boy",
        sibling_name="Mia",
        sibling_gender="girl",
        parent="father",
        sibling_trait="curious",
        hero_age=5,
        sibling_age=5,
        relation="friends",
        trust=4,
    ),
]


def pair_noun(hero: Entity, sibling: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and sibling.type == "boy":
            return "two brothers"
        if hero.type == "girl" and sibling.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    parent = f["parent"]
    food = f["food_cfg"]
    unsafe = f["unsafe_cfg"]
    safe = f["safe_cfg"]
    outcome = f["outcome"]
    name = hero.label
    sib = sibling.label
    base = (
        f'Write a short slice-of-life cautionary story for a 3-to-5-year-old about a child helping in the kitchen. '
        f'Include the word "sane" and make the lesson be about asking first.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {name} wants to cut {food.label} with {unsafe.label}, but listens to {sib} and learns the sane way to help.",
            f"Write a homey kitchen story where {parent.label_word} offers {safe.phrase} after a warning, and the ending shows the snack finished safely.",
        ]
    return [
        base,
        f"Tell a cautionary kitchen story where {name} reaches for {unsafe.label} to cut {food.label}, gets a small nick, and then learns to use {safe.label}.",
        f"Write a story where a child wants to help fast, a grown-up gives first aid, and the ending proves the lesson with a safe tool and a finished snack plate.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    parent = f["parent"]
    food = f["food_cfg"]
    unsafe = f["unsafe_cfg"]
    safe = f["safe_cfg"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(hero, sibling, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.label} and {sibling.label}, helping in the kitchen with their {parent.label_word}. They are trying to make a simple snack at home."
        ),
        (
            f"Why did {hero.label} reach for the {unsafe.label}?",
            f"{hero.label} wanted to help quickly and feel big. Seeing the knife beside the board made using it seem like the fastest way to cut the {food.label}."
        ),
        (
            f"Why did {sibling.label} warn {hero.label}?",
            f"{sibling.label} knew the {unsafe.label} was meant for grown-ups and that the {food.label} could slip. The warning came from the risk of a fast sharp blade near small fingers."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed after {sibling.label}'s warning?",
                f"{hero.label} stopped and asked for help instead of grabbing the knife. That choice changed the whole story, because they could finish the snack without anyone getting hurt."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} tried to use the {unsafe.label}?",
                f"The {food.label} slipped and {hero.label} got a small cut on one finger. The danger became real because the sharp tool moved faster than little hands could control."
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} help after the accident?",
                f"{parent.label_word.capitalize()} moved the knife away, washed the cut, and put on a bandage. After that, {parent.pronoun()} showed {hero.label} a safer tool so the helping could continue calmly."
            )
        )
    qa.append(
        (
            "What was the lesson of the story?",
            f"The lesson was that helping is good, but the sane way to help is to ask first and use tools made for children. The ending proves it, because the snack only gets finished safely once the right tool comes out."
        )
    )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with {food.slices} on the plate and everyone calmer. The final picture shows that careful help worked better than rushing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["unsafe_cfg"].tags) | set(f["safe_cfg"].tags) | set(f["food_cfg"].tags)
    if f["outcome"] == "nicked":
        tags.add("bandage")
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.sharp:
            bits.append("sharp=True")
        if ent.child_safe:
            bits.append("child_safe=True")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
needs_story(F) :- food(F), needs_cut(F).
valid(F, U, S) :- needs_story(F), unsafe_tool(U), sharpness(U, Sh), Sh >= 2,
                  safe_tool(S), supports(S, F).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
sibling_older :- relation(siblings), hero_age(H), sibling_age(S), S > H.
bonus(4) :- sibling_older.
bonus(0) :- not sibling_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- sibling_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(nicked) :- not averted.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        if food.needs_cut:
            lines.append(asp.fact("needs_cut", food_id))
    for unsafe_id, unsafe in UNSAFE_TOOLS.items():
        lines.append(asp.fact("unsafe_tool", unsafe_id))
        lines.append(asp.fact("sharpness", unsafe_id, unsafe.sharpness))
    for safe_id, safe in SAFE_TOOLS.items():
        lines.append(asp.fact("safe_tool", safe_id))
        for food_id in sorted(safe.supports):
            lines.append(asp.fact("supports", safe_id, food_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("sibling_age", params.sibling_age),
        asp.fact("trait", params.sibling_trait),
    ])
    model = asp.one_model(asp_program(scenario))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(
        params.relation,
        params.hero_age,
        params.sibling_age,
        params.sibling_trait,
    ) else "nicked"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child learns the sane, safe way to help in the kitchen."
    )
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--unsafe-tool", choices=UNSAFE_TOOLS, dest="unsafe_tool")
    ap.add_argument("--safe-tool", choices=SAFE_TOOLS, dest="safe_tool")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (food, unsafe, safe) combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name_gender(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food:
        food = FOODS[args.food]
        if not food.needs_cut:
            raise StoryError(explain_rejection(food))
    if args.food and args.safe_tool:
        food = FOODS[args.food]
        safe = SAFE_TOOLS[args.safe_tool]
        if food.id not in safe.supports:
            raise StoryError(explain_rejection(food, safe))
    combos = [
        combo for combo in valid_combos()
        if (args.food is None or combo[0] == args.food)
        and (args.unsafe_tool is None or combo[1] == args.unsafe_tool)
        and (args.safe_tool is None or combo[2] == args.safe_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    food_id, unsafe_id, safe_id = rng.choice(combos)
    hero_name, hero_gender = _pick_name_gender(rng)
    sibling_name, sibling_gender = _pick_name_gender(rng, avoid=hero_name)
    relation = rng.choice(["siblings", "friends"])
    hero_age, sibling_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        food=food_id,
        unsafe_tool=unsafe_id,
        safe_tool=safe_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        sibling_trait=rng.choice(TRAITS),
        hero_age=hero_age,
        sibling_age=sibling_age,
        relation=relation,
        trust=rng.randint(0, 10),
    )


def generate(params: StoryParams) -> StorySample:
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.unsafe_tool not in UNSAFE_TOOLS:
        raise StoryError(f"(Unknown unsafe tool: {params.unsafe_tool})")
    if params.safe_tool not in SAFE_TOOLS:
        raise StoryError(f"(Unknown safe tool: {params.safe_tool})")

    food = FOODS[params.food]
    unsafe = UNSAFE_TOOLS[params.unsafe_tool]
    safe = SAFE_TOOLS[params.safe_tool]

    if not food.needs_cut:
        raise StoryError(explain_rejection(food))
    if params.food not in safe.supports:
        raise StoryError(explain_combo(params.food, params.unsafe_tool, params.safe_tool))

    world = tell(
        food=food,
        unsafe=unsafe,
        safe_tool=safe,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sibling_name=params.sibling_name,
        sibling_gender=params.sibling_gender,
        sibling_trait=params.sibling_trait,
        parent_type=params.parent,
        hero_age=params.hero_age,
        sibling_age=params.sibling_age,
        relation=params.relation,
        trust=params.trust,
    )

    world.get("hero").label = params.hero_name
    world.get("sibling").label = params.sibling_name

    story = world.render().replace("hero", params.hero_name).replace("sibling", params.sibling_name)

    story = story.replace("hero", params.hero_name)
    story = story.replace("sibling", params.sibling_name)

    for src, dst in (
        ("hero", params.hero_name),
        ("sibling", params.sibling_name),
    ):
        story = story.replace(f"{src}'s", f"{dst}'s")
        story = story.replace(f"{src}.", f"{dst}.")
        story = story.replace(f"{src},", f"{dst},")
        story = story.replace(f"{src} ", f"{dst} ")
    return StorySample(
        params=params,
        story=story,
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
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    for s in range(200):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (food, unsafe_tool, safe_tool) combos:\n")
        for food, unsafe, safe in combos:
            print(f"  {food:10} {unsafe:14} {safe}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.food} with {p.unsafe_tool} -> {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
