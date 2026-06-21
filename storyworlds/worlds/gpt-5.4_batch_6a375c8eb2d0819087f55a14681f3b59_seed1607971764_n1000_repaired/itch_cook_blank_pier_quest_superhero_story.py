#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py
========================================================================

A standalone story world for a tiny "superhero quest on a pier" domain.

A child in a superhero costume visits a pier snack stand. A salty splash turns
the last line of the cook's recipe card blank, so the dish cannot be finished.
The child launches a quest around the pier to fetch the missing finishing
ingredient from the right helper. The twist is physical and concrete: something
in the costume makes the hero itch, which can slow the quest unless the hero
uses a sensible fix. The ending shows whether the hero returns in time for the
cook to finish the special snack.

This world always includes the words "itch", "cook", and "blank" in natural
story prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py --dish chowder --ingredient dill --helper gardener
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py --irritant wool_cape --remedy scratch_harder
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/itch_cook_blank_pier_quest_superhero_story.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Dish:
    id: str
    label: str
    pot_word: str
    stall_text: str
    finish_options: set[str] = field(default_factory=set)
    serving_text: str = ""
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
class Ingredient:
    id: str
    label: str
    clue_text: str
    finish_text: str
    aroma_text: str
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
class Helper:
    id: str
    label: str
    type: str
    place: str
    stocks: set[str] = field(default_factory=set)
    handoff_text: str = ""
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
class Irritant:
    id: str
    label: str
    wear_text: str
    itch_place: str
    severity: int
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
    sense: int
    relief: int
    fixes: set[str] = field(default_factory=set)
    use_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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
class StoryParams:
    dish: str
    ingredient: str
    helper: str
    irritant: str
    remedy: str
    hero_name: str
    hero_gender: str
    cook_name: str
    cook_type: str
    title: str
    delay: int = 0
    sidekick: str = ""
    gull: str = ""
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


def _r_blank_recipe(world: World) -> list[str]:
    card = world.entities.get("card")
    cook = world.entities.get("cook")
    pot = world.entities.get("pot")
    if card is None or cook is None or pot is None:
        return []
    if card.meters["wet"] < THRESHOLD:
        return []
    sig = ("blank_recipe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    card.meters["blank"] += 1
    cook.memes["worry"] += 1
    pot.meters["unfinished"] += 1
    return []


def _r_itch_slow(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["itch"] < THRESHOLD or hero.meters["soothed"] >= THRESHOLD:
        return []
    sig = ("itch_slow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["slow"] += 1
    hero.memes["frustration"] += 1
    return []


def _r_finish_dish(world: World) -> list[str]:
    pot = world.entities.get("pot")
    cook = world.entities.get("cook")
    hero = world.entities.get("hero")
    if pot is None or cook is None or hero is None:
        return []
    if pot.meters["unfinished"] < THRESHOLD or pot.meters["seasoned"] < THRESHOLD:
        return []
    sig = ("finish_dish",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pot.meters["ready"] += 1
    cook.memes["relief"] += 1
    hero.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blank_recipe", tag="physical", apply=_r_blank_recipe),
    Rule(name="itch_slow", tag="physical", apply=_r_itch_slow),
    Rule(name="finish_dish", tag="physical", apply=_r_finish_dish),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def plausible_combo(dish: Dish, ingredient: Ingredient, helper: Helper) -> bool:
    return ingredient.id in dish.finish_options and ingredient.id in helper.stocks


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def quest_pressure(irritant: Irritant, delay: int) -> int:
    return irritant.severity + delay


def quest_saved(remedy: Remedy, irritant: Irritant, delay: int) -> bool:
    return remedy.relief >= quest_pressure(irritant, delay)


def explain_combo(dish: Dish, ingredient: Ingredient, helper: Helper) -> str:
    if ingredient.id not in dish.finish_options:
        opts = ", ".join(sorted(dish.finish_options))
        return (
            f"(No story: {ingredient.label} does not belong on {dish.label}. "
            f"That cook needs one of: {opts}.)"
        )
    if ingredient.id not in helper.stocks:
        stock = ", ".join(sorted(helper.stocks)) or "nothing useful"
        return (
            f"(No story: {helper.label} at {helper.place} does not keep {ingredient.label}. "
            f"{helper.label.capitalize()} has: {stock}.)"
        )
    return "(No story: that quest clue would not lead to the right helper.)"


def explain_remedy(rid: str) -> str:
    remedy = REMEDIES[rid]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{rid}': it is too weak to be a sensible fix for the itch "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    irritant = IRRITANTS[params.irritant]
    remedy = REMEDIES[params.remedy]
    return "saved" if quest_saved(remedy, irritant, params.delay) else "late"


def predict_quest(world: World, helper_id: str, ingredient_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    helper = sim.get("helper")
    ingredient = sim.get("ingredient")
    quest_step(sim, hero, helper, ingredient, narrate=False)
    return {
        "found": sim.get("ingredient").meters["fetched"] >= THRESHOLD,
        "itch": sim.get("hero").meters["itch"],
        "slow": sim.get("hero").meters["slow"],
    }


def introduce(world: World, hero: Entity, title: str, sidekick: str, dish: Dish, irritant: Irritant) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On a bright afternoon at the pier, {hero.id} wore {irritant.wear_text} "
        f"and called {hero.pronoun('object')}self {title}."
    )
    if sidekick:
        world.say(f"{sidekick} trotted behind like a tiny sidekick, keeping pace on the wooden boards.")
    world.say(
        f"At the end of the pier, a snack stand sent out warm smells while a big pot of "
        f"{dish.pot_word} bubbled for the evening crowd."
    )


def meet_cook(world: World, hero: Entity, cook: Entity, dish: Dish, gull: str) -> None:
    cook.memes["care"] += 1
    world.say(
        f"{cook.id}, the pier cook, was stirring {dish.label} and humming over the spoon."
    )
    world.say(f'"This is my best batch yet," {cook.pronoun()} said. "{dish.serving_text}"')
    if gull:
        world.say(f"Even {gull} hopped along the rail to sniff the steam.")


def splash_problem(world: World, cook: Entity, dish: Dish) -> None:
    card = world.get("card")
    pot = world.get("pot")
    card.meters["wet"] += 1
    pot.meters["steam"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then a wave slapped the pilings below, and a salty mist skipped right up onto the stand."
    )
    world.say(
        f"A drop landed on the recipe card. The last line ran into a pale, blank blur."
    )
    world.say(
        f'{cook.id} blinked. "Oh no," {cook.pronoun()} said. "I remember every step but the last little finish."'
    )


def vow_quest(world: World, hero: Entity, cook: Entity, ingredient: Ingredient, helper: Helper) -> None:
    pred = predict_quest(world, helper.id, ingredient.id)
    world.facts["predicted_found"] = pred["found"]
    hero.memes["duty"] += 1
    world.say(
        f'{hero.id} put both hands on {hero.pronoun("possessive")} hips. "A superhero can help!" '
        f'{hero.pronoun().capitalize()} promised.'
    )
    world.say(
        f'{cook.id} tapped the blurry card. "The missing bit had a clue," {cook.pronoun()} said. '
        f'"It needed something {ingredient.clue_text}. If you ask the right person on the pier, '
        f'they may know."'
    )


def start_quest(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["quest"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"So {hero.id} dashed along the pier on a quest, heading for {helper.label} at {helper.attrs['place']}."
    )


def itch_hits(world: World, hero: Entity, irritant: Irritant) -> None:
    hero.meters["itch"] += 1
    hero.attrs["itch_place"] = irritant.itch_place
    propagate(world, narrate=False)
    world.say(
        f"Halfway there, {hero.pronoun('possessive')} {irritant.label} began to itch at {irritant.itch_place}."
    )
    world.say(
        f"The itch made {hero.pronoun('object')} wriggle and lose one brave step."
    )


def use_remedy(world: World, hero: Entity, remedy: Remedy, works: bool) -> None:
    if works:
        hero.meters["soothed"] += 1
        hero.meters["slow"] = 0.0
        hero.memes["focus"] += 1
        world.say(remedy.use_text.format(name=hero.id, pos=hero.pronoun("possessive")))
    else:
        hero.memes["frustration"] += 1
        world.say(remedy.fail_text.format(name=hero.id, pos=hero.pronoun("possessive")))


def quest_step(world: World, hero: Entity, helper: Entity, ingredient: Entity, narrate: bool = True) -> None:
    ingredient.meters["fetched"] += 1
    hero.meters["found"] += 1
    hero.memes["hope"] += 1
    if narrate:
        world.say(
            f"At {helper.attrs['place']}, {helper.id} listened, smiled, and {helper.attrs['handoff_text']}."
        )


def return_in_time(world: World, hero: Entity, cook: Entity, ingredient: Ingredient, dish: Dish) -> None:
    pot = world.get("pot")
    ingredient_ent = world.get("ingredient")
    ingredient_ent.meters["used"] += 1
    pot.meters["seasoned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} hurried back with {ingredient.label}, and {cook.id} finished the {dish.label} with it."
    )
    world.say(ingredient.finish_text)
    world.say(
        f"Soon the stand smelled even better, and the pier line began to smile before anyone took a bite."
    )


def celebrate(world: World, hero: Entity, cook: Entity, dish: Dish, title: str) -> None:
    hero.memes["joy"] += 1
    cook.memes["gratitude"] += 1
    world.say(
        f'"Saved!" laughed {cook.id}. "{dish.serving_text}"'
    )
    world.say(
        f'{cook.pronoun().capitalize()} set the first bowl in front of {hero.id}. '
        f'"For {title}," {cook.pronoun()} said.'
    )
    world.say(
        f"{hero.id} took one proud taste while the sunset turned the pier rails gold."
    )


def return_late(world: World, hero: Entity, cook: Entity, ingredient: Ingredient, dish: Dish) -> None:
    world.say(
        f"{hero.id} still found {ingredient.label} and ran back, but the line at the stand was already long."
    )
    world.say(
        f'{cook.id} had to serve the {dish.label} plain so nobody had to wait and wait with rumbling tummies.'
    )


def gentle_loss(world: World, hero: Entity, cook: Entity, ingredient: Ingredient) -> None:
    cook.memes["gratitude"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f'{cook.id} knelt beside {hero.id}. "You were kind to try," {cook.pronoun()} said. '
        f'"You kept going even when that itch slowed you down."'
    )
    world.say(
        f"{cook.pronoun().capitalize()} tucked the rescued {ingredient.label} beside the spoon and clipped a fresh card over the old blank one."
    )
    world.say(
        "Next time, the recipe would have a backup, and the hero would be ready even sooner."
    )


def tell(
    dish: Dish,
    ingredient: Ingredient,
    helper_cfg: Helper,
    irritant: Irritant,
    remedy: Remedy,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    cook_name: str = "Marin",
    cook_type: str = "aunt",
    title: str = "Captain Starflash",
    delay: int = 0,
    sidekick: str = "",
    gull: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        attrs={"title": title},
    ))
    cook = world.add(Entity(
        id=cook_name,
        kind="character",
        type=cook_type,
        role="cook",
        label="the cook",
    ))
    helper = world.add(Entity(
        id=helper_cfg.label.capitalize(),
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        attrs={"place": helper_cfg.place, "handoff_text": helper_cfg.handoff_text},
        tags=set(helper_cfg.tags),
    ))
    card = world.add(Entity(id="card", type="recipe_card", label="recipe card"))
    pot = world.add(Entity(id="pot", type="pot", label=dish.pot_word))
    ingredient_ent = world.add(Entity(
        id="ingredient",
        type="ingredient",
        label=ingredient.label,
        tags=set(ingredient.tags),
    ))

    world.facts["sidekick"] = sidekick
    world.facts["gull"] = gull

    introduce(world, hero, title, sidekick, dish, irritant)
    meet_cook(world, hero, cook, dish, gull)

    world.para()
    splash_problem(world, cook, dish)
    vow_quest(world, hero, cook, ingredient, helper)
    start_quest(world, hero, helper)

    world.para()
    itch_hits(world, hero, irritant)
    works = irritant.id in remedy.fixes
    use_remedy(world, hero, remedy, works)
    quest_step(world, hero, helper, ingredient_ent, narrate=True)

    saved = quest_saved(remedy, irritant, delay)
    world.para()
    if saved:
        return_in_time(world, hero, cook, ingredient, dish)
        celebrate(world, hero, cook, dish, title)
    else:
        return_late(world, hero, cook, ingredient, dish)
        gentle_loss(world, hero, cook, ingredient)

    world.facts.update(
        hero=hero,
        cook=cook,
        helper=helper,
        dish=dish,
        ingredient_cfg=ingredient,
        ingredient=ingredient_ent,
        irritant=irritant,
        remedy=remedy,
        title=title,
        saved=saved,
        outcome="saved" if saved else "late",
        delay=delay,
        blank=card.meters["blank"] >= THRESHOLD,
        itch=hero.meters["itch"] >= THRESHOLD,
        soothed=hero.meters["soothed"] >= THRESHOLD,
        pot_ready=pot.meters["ready"] >= THRESHOLD,
        helper_place=helper_cfg.place,
    )
    return world


DISHES = {
    "chowder": Dish(
        id="chowder",
        label="pier chowder",
        pot_word="creamy chowder",
        stall_text="Hot bowls are best when the top sings with the last little bright thing.",
        finish_options={"lemon", "dill"},
        serving_text="The chowder needs one tiny finishing touch before it can shine.",
        tags={"soup", "cook", "pier_food"},
    ),
    "fries": Dish(
        id="fries",
        label="crispy pier fries",
        pot_word="crispy fries",
        stall_text="The basket is almost ready, but the final sprinkle matters.",
        finish_options={"vinegar", "paprika"},
        serving_text="The fries need one bold final touch before I can serve them.",
        tags={"fries", "cook", "pier_food"},
    ),
    "buns": Dish(
        id="buns",
        label="berry buns",
        pot_word="warm berry buns",
        stall_text="The buns are puffy and sweet, but the top still needs its last kiss.",
        finish_options={"cinnamon", "honey"},
        serving_text="The buns need one soft finishing touch before they feel complete.",
        tags={"buns", "cook", "pier_food"},
    ),
}

INGREDIENTS = {
    "lemon": Ingredient(
        id="lemon",
        label="a bright lemon wedge",
        clue_text="bright and sunny",
        finish_text="A bright squeeze woke up the whole pot, and the steam smelled fresh and lively.",
        aroma_text="sunny and sharp",
        tags={"lemon", "flavor"},
    ),
    "dill": Ingredient(
        id="dill",
        label="a feathery pinch of dill",
        clue_text="green and feathery",
        finish_text="The green dill floated on top like little sea leaves, and the pot smelled garden-fresh.",
        aroma_text="green and fresh",
        tags={"dill", "herb"},
    ),
    "vinegar": Ingredient(
        id="vinegar",
        label="a dash of vinegar",
        clue_text="sharp and splashy",
        finish_text="The tiny splash of vinegar made the hot fries smell bright and snappy.",
        aroma_text="sharp and tangy",
        tags={"vinegar", "condiment"},
    ),
    "paprika": Ingredient(
        id="paprika",
        label="a red shake of paprika",
        clue_text="red and bold",
        finish_text="A red cloud of paprika drifted over the fries, making them look brave and warm.",
        aroma_text="smoky and warm",
        tags={"paprika", "spice"},
    ),
    "cinnamon": Ingredient(
        id="cinnamon",
        label="a cinnamon sprinkle",
        clue_text="brown and sweet",
        finish_text="The cinnamon fell like sweet dust, and the berry buns smelled cozy at once.",
        aroma_text="sweet and cozy",
        tags={"cinnamon", "spice"},
    ),
    "honey": Ingredient(
        id="honey",
        label="a spoon of honey",
        clue_text="golden and sticky",
        finish_text="The honey shone on top, and each bun looked as if it had caught a little sunset.",
        aroma_text="golden and sweet",
        tags={"honey", "sweet"},
    ),
}

HELPERS = {
    "fishmonger": Helper(
        id="fishmonger",
        label="the fishmonger",
        type="man",
        place="the silver fish table",
        stocks={"lemon"},
        handoff_text="lifted a lemon wedge from a tray of ice and tucked it carefully into the hero's hand",
        tags={"fishmonger", "lemon"},
    ),
    "gardener": Helper(
        id="gardener",
        label="the gardener",
        type="woman",
        place="the herb box by the rail",
        stocks={"dill"},
        handoff_text="snipped a feathery pinch of dill from the herb box and wrapped it in a clean paper",
        tags={"gardener", "dill"},
    ),
    "condiment_keeper": Helper(
        id="condiment_keeper",
        label="the condiment keeper",
        type="woman",
        place="the little sauce shelf",
        stocks={"vinegar"},
        handoff_text="filled a tiny cup with vinegar and pressed a lid tight so not one drop would spill",
        tags={"condiment", "vinegar"},
    ),
    "spice_seller": Helper(
        id="spice_seller",
        label="the spice seller",
        type="man",
        place="the market crate with bright jars",
        stocks={"paprika", "cinnamon"},
        handoff_text="shook a careful spoonful from a bright jar into a folded paper packet",
        tags={"spice", "paprika", "cinnamon"},
    ),
    "tea_vendor": Helper(
        id="tea_vendor",
        label="the tea vendor",
        type="woman",
        place="the tea cart with striped cups",
        stocks={"honey"},
        handoff_text="dipped a spoon into a honey pot and sealed the golden swirl in a tiny jar",
        tags={"tea", "honey"},
    ),
}

IRRITANTS = {
    "wool_cape": Irritant(
        id="wool_cape",
        label="wool cape",
        wear_text="a red wool cape that fluttered like a flag",
        itch_place="the back of the neck",
        severity=2,
        tags={"cape", "itch"},
    ),
    "rope_belt": Irritant(
        id="rope_belt",
        label="rope belt",
        wear_text="a blue cape and a scratchy rope belt tied in a superhero knot",
        itch_place="the waist",
        severity=1,
        tags={"belt", "itch"},
    ),
    "feather_mask": Irritant(
        id="feather_mask",
        label="feather mask",
        wear_text="a silver cape and a feathery mask with brave eye holes",
        itch_place="the nose",
        severity=3,
        tags={"mask", "itch"},
    ),
}

REMEDIES = {
    "rinse_neck": Remedy(
        id="rinse_neck",
        label="rinse with cool water",
        sense=3,
        relief=2,
        fixes={"wool_cape"},
        use_text="{name} stopped at the hand pump, dabbed cool water on {pos} neck, and the worst of the itch faded away.",
        fail_text="{name} splashed on a little water, but the itch was in the wrong place and kept bothering {pos} anyway.",
        qa_text="used cool water to calm the scratchy spot",
        tags={"water", "itch_fix"},
    ),
    "loosen_knot": Remedy(
        id="loosen_knot",
        label="loosen the knot",
        sense=3,
        relief=1,
        fixes={"rope_belt"},
        use_text="{name} tugged the superhero knot looser, took one deep breath, and could move quickly again.",
        fail_text="{name} tugged at the knot, but that did not help the itch much, and the delay kept growing.",
        qa_text="loosened the scratchy knot",
        tags={"knot", "itch_fix"},
    ),
    "swap_mask": Remedy(
        id="swap_mask",
        label="swap for a plain mask",
        sense=3,
        relief=3,
        fixes={"feather_mask"},
        use_text="{name} borrowed a plain paper mask from a ticket booth, and the nose itch stopped tickling at once.",
        fail_text="{name} changed things around a little, but the feathery tickle kept sneaking back.",
        qa_text="changed the itchy mask for a plain one",
        tags={"mask", "itch_fix"},
    ),
    "scratch_harder": Remedy(
        id="scratch_harder",
        label="scratch harder",
        sense=1,
        relief=0,
        fixes=set(),
        use_text="{name} scratched and scratched, which only made the itch feel bigger.",
        fail_text="{name} scratched harder, but that only made the itch worse and stole more time from the quest.",
        qa_text="scratched harder",
        tags={"bad_fix"},
    ),
}

HERO_NAMES = ["Nova", "Jet", "Skye", "Milo", "Ruby", "Finn", "Ivy", "Theo", "Luna", "Kai"]
COOK_NAMES = ["Marin", "Tessa", "Bram", "Pilar", "June", "Oren"]
TITLES = ["Captain Starflash", "Thunder Harbor", "Comet Kid", "Pier Guardian", "Mighty Beacon"]
SIDEKICKS = ["Pebble the dog", "Flash the scooter", "Pip the gull friend", ""]
GULLS = ["a cheeky gull", "one bold seagull", "a white gull", ""]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for dish_id, dish in DISHES.items():
        for ingredient_id, ingredient in INGREDIENTS.items():
            for helper_id, helper in HELPERS.items():
                if plausible_combo(dish, ingredient, helper):
                    combos.append((dish_id, ingredient_id, helper_id))
    return combos


KNOWLEDGE = {
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. People can walk on it, fish from it, or visit little shops and stands there.",
        )
    ],
    "itch": [
        (
            "What is an itch?",
            "An itch is a tickly, scratchy feeling on your skin that makes you want to rub or scratch. Sometimes the smartest fix is to remove what is bothering you, not just scratch harder.",
        )
    ],
    "recipe": [
        (
            "What is a recipe card?",
            "A recipe card is a little note that tells a cook what ingredients and steps to use. If the writing gets wet, the words can blur and go blank.",
        )
    ],
    "lemon": [
        (
            "What does lemon do in food?",
            "Lemon adds a bright, fresh taste. Just a little squeeze can make soup or fish taste more lively.",
        )
    ],
    "dill": [
        (
            "What is dill?",
            "Dill is a soft green herb with feathery leaves. Cooks use it to add a fresh, grassy smell and taste to food.",
        )
    ],
    "vinegar": [
        (
            "What is vinegar?",
            "Vinegar is a sharp, sour liquid used to add a bright taste to food. A tiny splash can change the flavor a lot.",
        )
    ],
    "paprika": [
        (
            "What is paprika?",
            "Paprika is a red spice made from dried peppers. It gives food color and a warm flavor.",
        )
    ],
    "cinnamon": [
        (
            "What is cinnamon?",
            "Cinnamon is a sweet-smelling brown spice. It makes baked treats smell cozy and warm.",
        )
    ],
    "honey": [
        (
            "What is honey?",
            "Honey is a thick, golden sweet food made by bees. It tastes sweet and shines when you drizzle it on top of food.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a clear goal, like finding a needed thing or helping someone. In stories, a quest often tests courage and patience along the way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pier", "quest", "itch", "recipe", "lemon", "dill", "vinegar", "paprika", "cinnamon", "honey"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cook = f["cook"]
    dish = f["dish"]
    ingredient = f["ingredient_cfg"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a superhero story for a 3-to-5-year-old set on a pier where a child helps a cook after a recipe card goes blank. Include the words "itch", "cook", and "blank".',
            f"Tell a quest story where {hero.id} races along the pier to find {ingredient.label} so {cook.id} can finish {dish.label} in time.",
            f'Write a bright, child-facing story where a hero solves an itch problem sensibly and saves a cook\'s special dish.',
        ]
    return [
        f'Write a gentle superhero story set on a pier where a child tries to help a cook after a splash turns part of a recipe card blank. Include the words "itch", "cook", and "blank".',
        f"Tell a quest story where {hero.id} still finds the missing ingredient, but an itch slows the trip and the cook must serve the food plain.",
        f'Write a story with a kind, bittersweet ending where trying to help still matters, even when the hero is a little late.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    cook = f["cook"]
    helper = f["helper"]
    dish = f["dish"]
    ingredient = f["ingredient_cfg"]
    remedy = f["remedy"]
    irritant = f["irritant"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero on the pier, and {cook.id}, the cook at the snack stand. The story also includes {helper.label}, who helps with the quest.",
        ),
        (
            "What problem started the quest?",
            f"A salty splash hit the recipe card and made the last line go blank. Because of that, {cook.id} could not remember the final finishing ingredient for the {dish.label}.",
        ),
        (
            f"Why did {hero.id} go to {helper.attrs['place']}?",
            f"{hero.id} went there to ask {helper.label} about the missing ingredient. {cook.id} remembered a clue about something {ingredient.clue_text}, so the quest had a real reason and direction.",
        ),
        (
            f"What made the hero slow down?",
            f"{hero.id}'s {irritant.label} caused an itch at {irritant.itch_place}. That physical itch slowed the run along the pier and made the quest harder.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How did {hero.id} still save the dish?",
                f"{hero.id} {remedy.qa_text} and kept going, which let the quest stay fast enough. Then {helper.label} handed over {ingredient.label}, and {cook.id} finished the {dish.label} in time.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the cook serving the finished food and giving the first taste to {hero.id}. The sunset over the pier showed that the quest really changed the day for everyone at the stand.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} finish the quest?",
                f"Yes, {hero.pronoun()} still found {ingredient.label} and brought it back. But the itch slowed the trip so much that {cook.id} had to serve the {dish.label} plain first.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently, not angrily. {cook.id} thanked {hero.id} for trying, saved the ingredient for next time, and clipped a fresh card over the old blank one so the same problem would not happen again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pier", "quest", "itch", "recipe"}
    ingredient = f["ingredient_cfg"]
    tags |= set(ingredient.tags)
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
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        dish="chowder",
        ingredient="lemon",
        helper="fishmonger",
        irritant="wool_cape",
        remedy="rinse_neck",
        hero_name="Nova",
        hero_gender="girl",
        cook_name="Marin",
        cook_type="aunt",
        title="Captain Starflash",
        delay=0,
        sidekick="Pebble the dog",
        gull="a cheeky gull",
    ),
    StoryParams(
        dish="chowder",
        ingredient="dill",
        helper="gardener",
        irritant="rope_belt",
        remedy="loosen_knot",
        hero_name="Finn",
        hero_gender="boy",
        cook_name="Tessa",
        cook_type="mother",
        title="Pier Guardian",
        delay=0,
        sidekick="",
        gull="one bold seagull",
    ),
    StoryParams(
        dish="buns",
        ingredient="honey",
        helper="tea_vendor",
        irritant="feather_mask",
        remedy="swap_mask",
        hero_name="Ruby",
        hero_gender="girl",
        cook_name="June",
        cook_type="aunt",
        title="Comet Kid",
        delay=0,
        sidekick="Pip the gull friend",
        gull="a white gull",
    ),
    StoryParams(
        dish="fries",
        ingredient="paprika",
        helper="spice_seller",
        irritant="wool_cape",
        remedy="loosen_knot",
        hero_name="Milo",
        hero_gender="boy",
        cook_name="Bram",
        cook_type="uncle",
        title="Thunder Harbor",
        delay=1,
        sidekick="Flash the scooter",
        gull="",
    ),
    StoryParams(
        dish="buns",
        ingredient="cinnamon",
        helper="spice_seller",
        irritant="feather_mask",
        remedy="rinse_neck",
        hero_name="Luna",
        hero_gender="girl",
        cook_name="Pilar",
        cook_type="mother",
        title="Mighty Beacon",
        delay=1,
        sidekick="Pebble the dog",
        gull="a cheeky gull",
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
plausible(D, I, H) :- dish(D), ingredient(I), helper(H),
                      finishes(D, I), stocks(H, I).

% --- outcome model ---------------------------------------------------------
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
pressure(V) :- chosen_irritant(I), severity(I, S), delay(D), V = S + D.
saved       :- chosen_remedy(R), relief(R, RL), pressure(V), RL >= V.
outcome(saved) :- saved.
outcome(late)  :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dish_id, dish in DISHES.items():
        lines.append(asp.fact("dish", dish_id))
        for ingredient_id in sorted(dish.finish_options):
            lines.append(asp.fact("finishes", dish_id, ingredient_id))
    for ingredient_id in INGREDIENTS:
        lines.append(asp.fact("ingredient", ingredient_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for ingredient_id in sorted(helper.stocks):
            lines.append(asp.fact("stocks", helper_id, ingredient_id))
    for irritant_id, irritant in IRRITANTS.items():
        lines.append(asp.fact("irritant", irritant_id))
        lines.append(asp.fact("severity", irritant_id, irritant.severity))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("relief", remedy_id, remedy.relief))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_sensible_remedies() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_irritant", params.irritant),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: compatibility gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    c_rem = set(asp_sensible_remedies())
    p_rem = {r.id for r in sensible_remedies()}
    if c_rem == p_rem:
        print(f"OK: sensible remedies match ({sorted(c_rem)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_rem)} python={sorted(p_rem)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero child goes on a pier quest to help a cook after a recipe card goes blank."
    )
    ap.add_argument("--dish", choices=sorted(DISHES))
    ap.add_argument("--ingredient", choices=sorted(INGREDIENTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--irritant", choices=sorted(IRRITANTS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--cook-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time pressure on the quest")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible dish/ingredient/helper combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dish and args.ingredient and args.helper:
        dish = DISHES[args.dish]
        ingredient = INGREDIENTS[args.ingredient]
        helper = HELPERS[args.helper]
        if not plausible_combo(dish, ingredient, helper):
            raise StoryError(explain_combo(dish, ingredient, helper))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.dish is None or combo[0] == args.dish)
        and (args.ingredient is None or combo[1] == args.ingredient)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    dish_id, ingredient_id, helper_id = rng.choice(sorted(combos))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    irritant_id = args.irritant or rng.choice(sorted(IRRITANTS))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = rng.choice([n for n in HERO_NAMES if (gender == "girl" and n not in {"Milo", "Finn", "Theo", "Kai"}) or (gender == "boy" and n not in {"Nova", "Ruby", "Ivy", "Luna", "Skye"})])
    cook_name = rng.choice(COOK_NAMES)
    cook_type = args.cook_type or rng.choice(["mother", "father", "aunt", "uncle"])
    title = rng.choice(TITLES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    sidekick = rng.choice(SIDEKICKS)
    gull = rng.choice(GULLS)
    return StoryParams(
        dish=dish_id,
        ingredient=ingredient_id,
        helper=helper_id,
        irritant=irritant_id,
        remedy=remedy_id,
        hero_name=hero_name,
        hero_gender=gender,
        cook_name=cook_name,
        cook_type=cook_type,
        title=title,
        delay=delay,
        sidekick=sidekick,
        gull=gull,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        dish = DISHES[params.dish]
        ingredient = INGREDIENTS[params.ingredient]
        helper = HELPERS[params.helper]
        irritant = IRRITANTS[params.irritant]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not plausible_combo(dish, ingredient, helper):
        raise StoryError(explain_combo(dish, ingredient, helper))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(remedy.id))

    world = tell(
        dish=dish,
        ingredient=ingredient,
        helper_cfg=helper,
        irritant=irritant,
        remedy=remedy,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        cook_name=params.cook_name,
        cook_type=params.cook_type,
        title=params.title,
        delay=params.delay,
        sidekick=params.sidekick,
        gull=params.gull,
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
        print(asp_program("", "#show plausible/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible_remedies())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (dish, ingredient, helper) combos:\n")
        for dish, ingredient, helper in combos:
            print(f"  {dish:8} {ingredient:10} {helper}")
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
            header = (
                f"### {p.hero_name}: {p.dish} + {p.ingredient} via {p.helper} "
                f"({p.irritant}, {p.remedy}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
