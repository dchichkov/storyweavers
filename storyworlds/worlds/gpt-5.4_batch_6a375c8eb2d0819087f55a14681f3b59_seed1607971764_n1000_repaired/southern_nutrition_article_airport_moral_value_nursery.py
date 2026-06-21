#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py
====================================================================================

A standalone story world in a nursery-rhyme style: a child in an airport is
tempted by a sweet treat, then learns to make a wiser, kinder food choice after
meeting a simple need for nutrition.

Seed constraints
----------------
- must include the words: southern, nutrition, article
- setting: airport
- feature: Moral Value
- style: Nursery Rhyme

This world models a tiny airport domain with a concrete causal spine:

    travel delay + hunger -> tempting sweet
    weak food choice      -> low energy / shaky mood before boarding
    nourishing food       -> steady energy / calm mood
    enough food           -> child can share kindly with another traveler

The rendered story is driven by world state, not by slot-filling a frozen
paragraph. Some choices are explicitly refused: a "helpful" snack must actually
provide enough nutrition for the wait, and a route that is too short for the
story's need is rejected.

Run it
------
    python storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py
    python storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py --destination southern --temptation candy_twist --meal yogurt_parfait
    python storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py --meal frosted_bun
    python storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py --all
    python storyworlds/worlds/gpt-5.4/southern_nutrition_article_airport_moral_value_nursery.py --verify
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
HELP_MIN = 2
WISE_VALUES = {"care", "kindness", "self_control"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Destination:
    id: str
    adjective: str
    place: str
    image: str
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
class Temptation:
    id: str
    label: str
    phrase: str
    rhyme: str
    sugar: int
    nutrition: int
    plural: bool = False
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
class Meal:
    id: str
    label: str
    phrase: str
    rhyme: str
    energy: int
    nutrition: int
    shareable: bool
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
class Article:
    id: str
    title: str
    line: str
    source: str
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
class MoralValue:
    id: str
    name: str
    lesson: str
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


def _r_hunger_drains(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["hunger"] >= THRESHOLD and child.meters["fuel"] < THRESHOLD:
        sig = ("drain", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["energy_low"] += 1
            child.memes["worry"] += 1
            out.append("__drain__")
    return out


def _r_good_food_steadies(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["fuel"] >= THRESHOLD:
        sig = ("steady", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["steady"] += 1
            child.memes["calm"] += 1
            if child.memes["worry"] >= THRESHOLD:
                child.memes["worry"] = 0.0
            out.append("__steady__")
    return out


def _r_article_teaches(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["noticed_article"] >= THRESHOLD:
        sig = ("article", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wisdom"] += 1
            out.append("__article__")
    return out


def _r_can_share(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    little = world.get("little")
    if (
        child.meters["steady"] >= THRESHOLD
        and child.meters["shares_food"] >= THRESHOLD
        and little.meters["hunger"] >= THRESHOLD
    ):
        sig = ("share", child.id, little.id)
        if sig not in world.fired:
            world.fired.add(sig)
            little.meters["fuel"] += 1
            little.meters["steady"] += 1
            child.memes["kind"] += 1
            little.memes["relief"] += 1
            out.append("__share__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hunger_drains", tag="physical", apply=_r_hunger_drains),
    Rule(name="good_food_steadies", tag="physical", apply=_r_good_food_steadies),
    Rule(name="article_teaches", tag="moral", apply=_r_article_teaches),
    Rule(name="can_share", tag="social", apply=_r_can_share),
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


def helps_trip(meal: Meal, wait_level: int) -> bool:
    return meal.energy >= wait_level and meal.nutrition >= HELP_MIN


def sensible_meals(wait_level: int) -> list[Meal]:
    return [m for m in MEALS.values() if helps_trip(m, wait_level)]


def predict_choice(world: World, meal: Meal) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["fuel"] += meal.energy
    child.meters["nutrition"] += meal.nutrition
    if meal.nutrition < HELP_MIN:
        child.meters["sugar_rush"] += 1
    propagate(sim, narrate=False)
    return {
        "steady": child.meters["steady"] >= THRESHOLD,
        "energy_low": child.meters["energy_low"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, grown: Entity, dest: Destination) -> None:
    world.say(
        f"In the airport, by the bright gate door, sat {child.id} with {child.pronoun('possessive')} "
        f"{grown.label_word}, ready to soar. They were flying to {dest.adjective} {dest.place}, "
        f"where {dest.image} waited beyond the clouds."
    )


def waiting(world: World, child: Entity, wait_level: int) -> None:
    child.meters["hunger"] = float(wait_level)
    world.say(
        f"The line was long, the steps were many, and soon {child.id}'s tummy gave a small, shy sound. "
        f"The airport hummed around {child.pronoun('object')} like a silver tune."
    )


def see_kiosk(world: World, child: Entity, temptation: Temptation, meal: Meal) -> None:
    child.memes["tempted"] += 1
    world.say(
        f"At a snack stand near the window, {child.pronoun()} saw {temptation.phrase} and "
        f"{meal.phrase}. '{temptation.rhyme},' sang the sweet little sign, and it almost pulled "
        f"{child.pronoun('object')} out of line."
    )


def read_article(world: World, child: Entity, article: Article) -> None:
    child.memes["noticed_article"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then a page on a bench gave a whispery start: it was {article.source}, opened to an article called "
        f'"{article.title}." Under the picture ran a line about nutrition: "{article.line}"'
    )


def counsel(world: World, grown: Entity, child: Entity, meal: Meal, temptation: Temptation) -> None:
    pred_good = predict_choice(world, meal)
    if pred_good["steady"]:
        world.say(
            f'{grown.label_word.capitalize()} bent close and spoke in a gentle tone. '
            f'"Sweet things can sparkle, but wise food helps you walk, wait, and fly. '
            f"Let us choose what will keep you strong."
        )
    else:
        world.say(
            f'{grown.label_word.capitalize()} looked thoughtful. "That snack is pretty, but it may not help for a long airport wait," '
            f'{grown.pronoun()} said.'
        )
    world.say(
        f'{child.id} looked from {temptation.label} to {meal.label}, and the little article words stayed warm in {child.pronoun("possessive")} mind.'
    )


def choose_meal(world: World, child: Entity, meal: Meal) -> None:
    child.meters["fuel"] += meal.energy
    child.meters["nutrition"] += meal.nutrition
    child.memes["choice"] += 1
    if meal.nutrition < HELP_MIN:
        child.meters["sugar_rush"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {child.id} chose {meal.phrase}. '{meal.rhyme},' {child.pronoun()} sang, and took a careful bite."
    )


def low_energy_turn(world: World, child: Entity, temptation: Temptation) -> None:
    world.say(
        f"But {temptation.label} was mostly sparkle and swish. Before the boarding song was sung, "
        f"{child.id}'s knees felt soft and {child.pronoun('possessive')} smile grew thin."
    )


def steady_turn(world: World, child: Entity) -> None:
    world.say(
        f"Soon {child.id}'s steps felt steady-steady, and {child.pronoun('possessive')} face looked bright and ready. "
        f"The long shiny hall did not seem quite so long."
    )


def meet_little(world: World, child: Entity, little: Entity) -> None:
    little.meters["hunger"] = 1.0
    little.memes["tired"] = 1.0
    world.say(
        f"By the next row of seats sat {little.id}, a smaller traveler with a droopy curl and a sleepy yawn. "
        f"{little.pronoun().capitalize()} looked hungry too."
    )


def share_if_possible(world: World, child: Entity, little: Entity, meal: Meal, value: MoralValue) -> None:
    if meal.shareable and child.meters["steady"] >= THRESHOLD:
        child.meters["shares_food"] = 1.0
        propagate(world, narrate=False)
        world.say(
            f"{child.id} broke off a neat little share and offered it kindly. "
            f'"Here you are," {child.pronoun()} said. "We can wait more sweetly when we share."'
        )
        world.say(
            f"{little.id} smiled, and the airport bench felt warmer than before. "
            f"{value.ending}"
        )
    else:
        world.say(
            f"{child.id} wished for a share to give, but there was not much to spare. "
            f"So {child.pronoun()} offered a seat-side song instead, and even that made the waiting gentler."
        )


def moral_close(world: World, child: Entity, grown: Entity, dest: Destination, value: MoralValue) -> None:
    world.say(
        f"When the plane to {dest.adjective} {dest.place} was called at last, {child.id} rose with a calm small grin. "
        f'{grown.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand and said, '
        f'"{value.lesson}"'
    )
    world.say(
        f"So off they went through the airport bright, under the soft gate light: a wise small heart, a nourished start, "
        f"and room for kindness too."
    )
@dataclass
class StoryParams:
    destination: str
    temptation: str
    meal: str
    article: str
    value: str
    child_name: str
    child_gender: str
    grown_type: str
    little_name: str
    little_gender: str
    wait_level: int = 2
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


def valid_combos() -> list[tuple[str, str, str, str, str, int]]:
    combos: list[tuple[str, str, str, str, str, int]] = []
    for dest_id in DESTINATIONS:
        for tempt_id in TEMPTATIONS:
            for meal_id, meal in MEALS.items():
                for article_id in ARTICLES:
                    for value_id in VALUES:
                        for wait_level in (1, 2, 3):
                            if helps_trip(meal, wait_level):
                                combos.append(
                                    (dest_id, tempt_id, meal_id, article_id, value_id, wait_level)
                                )
    return combos


CURATED = [
    StoryParams(
        destination="southern",
        temptation="candy_twist",
        meal="peach_oats",
        article="southern_column",
        value="kindness",
        child_name="Nora",
        child_gender="girl",
        grown_type="mother",
        little_name="Pip",
        little_gender="boy",
        wait_level=2,
    ),
    StoryParams(
        destination="mountain",
        temptation="frosted_bun",
        meal="yogurt_parfait",
        article="gate_magazine",
        value="care",
        child_name="Ben",
        child_gender="boy",
        grown_type="father",
        little_name="June",
        little_gender="girl",
        wait_level=2,
    ),
    StoryParams(
        destination="southern",
        temptation="glazed_bits",
        meal="egg_wrap",
        article="safety_paper",
        value="self_control",
        child_name="Ella",
        child_gender="girl",
        grown_type="aunt",
        little_name="Theo",
        little_gender="boy",
        wait_level=3,
    ),
    StoryParams(
        destination="island",
        temptation="candy_twist",
        meal="yogurt_parfait",
        article="gate_magazine",
        value="kindness",
        child_name="Max",
        child_gender="boy",
        grown_type="mother",
        little_name="Lila",
        little_gender="girl",
        wait_level=1,
    ),
]


KNOWLEDGE = {
    "airport": [
        (
            "What is an airport?",
            "An airport is a place where people wait for airplanes, check bags, and walk to gates before a trip."
        )
    ],
    "nutrition": [
        (
            "What does nutrition mean?",
            "Nutrition means the good food your body uses to grow, move, and stay strong. Food with more nutrition helps longer than food that is only sugary."
        )
    ],
    "article": [
        (
            "What is an article?",
            "An article is a piece of writing in a magazine, newspaper, or website that tells you about one subject."
        )
    ],
    "southern": [
        (
            "What does southern mean?",
            "Southern means from the south or toward the south. People might use it for places, weather, or foods from that part of a country."
        )
    ],
    "fruit": [
        (
            "Why can fruit be a good travel snack?",
            "Fruit gives your body useful energy and water, and it is easy to eat while traveling. It can help you feel fresh instead of too heavy."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because you notice another person's need and choose to help. A small share can make waiting feel easier for both people."
        )
    ],
}

KNOWLEDGE_ORDER = ["airport", "nutrition", "article", "southern", "fruit", "sharing"]


def explain_meal_rejection(meal_id: str, wait_level: int) -> str:
    meal = MEALS[meal_id]
    return (
        f"(No story: {meal.phrase} is too slight for this airport wait. "
        f"A helpful choice here must give enough nutrition and steady energy for wait level {wait_level}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dest = f["destination"]
    tempt = f["temptation"]
    meal = f["meal"]
    value = f["value"]
    return [
        f'Write a nursery-rhyme-style story set in an airport where a child is tempted by {tempt.label} but learns a lesson about nutrition.',
        f'Write a gentle moral story about {child.id} traveling to a {dest.adjective} place, reading an article, and choosing {meal.label} instead of a sweeter treat.',
        f'Write a child-facing airport story that uses the words "southern," "nutrition," and "article," and ends by teaching {value.name}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    little = f["little"]
    dest = f["destination"]
    tempt = f["temptation"]
    meal = f["meal"]
    article = f["article"]
    value = f["value"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child waiting in an airport with {child.pronoun('possessive')} {grown.label_word}. They are getting ready to fly to {dest.adjective} {dest.place}."
        ),
        (
            "What choice did the child have to make?",
            f"{child.id} had to choose between {tempt.phrase} and {meal.phrase}. The choice mattered because the airport wait was long and {child.pronoun('possessive')} body needed better nutrition than sugar alone."
        ),
        (
            "What did the article say that helped?",
            f'The article reminded {child.id} that good nutrition helps small travelers stay strong through a long wait. That is why the writing on the page changed the feeling of the choice.'
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                f"Why did {child.id} feel steady after eating?",
                f"{child.id} felt steady because {meal.label} gave enough fuel and nutrition for the airport wait. The wiser snack helped {child.pronoun('object')} walk calmly instead of growing shaky."
            )
        )
    else:
        qa.append(
            (
                f"Why did {child.id} feel wobbly?",
                f"{child.id} felt wobbly because the food choice did not give enough help for the wait. Sweetness came first, but steady energy did not last."
            )
        )
    if f["shared"]:
        qa.append(
            (
                f"How did {child.id} show {value.name}?",
                f"{child.id} noticed that {little.id} was hungry and shared part of the snack. That act turned a private good choice into kindness for someone else."
            )
        )
    else:
        qa.append(
            (
                "Did the story still teach a moral value even without sharing food?",
                f"Yes. The story still teaches {value.name} because {child.id} learned to choose what helps instead of only what dazzles. That thoughtful choice is part of good character too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"airport", "nutrition", "article"}
    if "southern" in f["destination"].tags:
        tags.add("southern")
    if "fruit" in f["meal"].tags or "southern" in f["meal"].tags:
        tags.add("fruit")
    if f["shared"]:
        tags.add("sharing")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A meal is helpful only when it matches the wait and clears the nutrition bar.
helpful(M, W) :- meal(M), energy(M, E), wait_level(W), nutrition(M, N), help_min(H), E >= W, N >= H.

valid(D, T, M, A, V, W) :- destination(D), temptation(T), article(A), value(V), wait_level(W), helpful(M, W).

% If a meal is shareable and helpful, the story can reach the sharing ending.
can_share(M, W) :- helpful(M, W), shareable(M).

#show valid/6.
#show can_share/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for mid, meal in MEALS.items():
        lines.append(asp.fact("meal", mid))
        lines.append(asp.fact("energy", mid, meal.energy))
        lines.append(asp.fact("nutrition", mid, meal.nutrition))
        if meal.shareable:
            lines.append(asp.fact("shareable", mid))
    for aid in ARTICLES:
        lines.append(asp.fact("article", aid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    for wait_level in (1, 2, 3):
        lines.append(asp.fact("wait_level", wait_level))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_shareable_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "can_share")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_share = {
        (meal.id, wait_level)
        for meal in MEALS.values()
        for wait_level in (1, 2, 3)
        if meal.shareable and helps_trip(meal, wait_level)
    }
    cl_share = set(asp_shareable_pairs())
    if py_share == cl_share:
        print(f"OK: shareability facts match ({len(py_share)} pairs).")
    else:
        rc = 1
        print("MISMATCH in shareability reasoning:")
        if cl_share - py_share:
            print("  only in clingo:", sorted(cl_share - py_share))
        if py_share - cl_share:
            print("  only in python:", sorted(py_share - cl_share))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme airport story world about nutrition, wise choices, and kindness."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--article", choices=ARTICLES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grown-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--little-name")
    ap.add_argument("--little-gender", choices=["girl", "boy"])
    ap.add_argument("--wait-level", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    wait_level = args.wait_level if args.wait_level is not None else rng.choice([1, 2, 3])

    if args.meal and not helps_trip(MEALS[args.meal], wait_level):
        raise StoryError(explain_meal_rejection(args.meal, wait_level))

    combos = [
        c
        for c in valid_combos()
        if (args.destination is None or c[0] == args.destination)
        and (args.temptation is None or c[1] == args.temptation)
        and (args.meal is None or c[2] == args.meal)
        and (args.article is None or c[3] == args.article)
        and (args.value is None or c[4] == args.value)
        and c[5] == wait_level
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, temptation, meal, article, value, chosen_wait = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    little_gender = args.little_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    little_name = args.little_name or _pick_name(rng, little_gender, avoid=child_name)
    grown_type = args.grown_type or rng.choice(["mother", "father", "aunt", "uncle"])

    return StoryParams(
        destination=destination,
        temptation=temptation,
        meal=meal,
        article=article,
        value=value,
        child_name=child_name,
        child_gender=child_gender,
        grown_type=grown_type,
        little_name=little_name,
        little_gender=little_gender,
        wait_level=chosen_wait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(Unknown temptation: {params.temptation})")
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal: {params.meal})")
    if params.article not in ARTICLES:
        raise StoryError(f"(Unknown article: {params.article})")
    if params.value not in VALUES:
        raise StoryError(f"(Unknown moral value: {params.value})")
    if params.wait_level not in (1, 2, 3):
        raise StoryError("(Wait level must be 1, 2, or 3.)")
    if not helps_trip(MEALS[params.meal], params.wait_level):
        raise StoryError(explain_meal_rejection(params.meal, params.wait_level))

    world = tell(
        DESTINATIONS[params.destination],
        TEMPTATIONS[params.temptation],
        MEALS[params.meal],
        ARTICLES[params.article],
        VALUES[params.value],
        child_name=params.child_name,
        child_gender=params.child_gender,
        grown_type=params.grown_type,
        little_name=params.little_name,
        little_gender=params.little_gender,
        wait_level=params.wait_level,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid airport story combos:\n")
        for destination, temptation, meal, article, value, wait_level in combos:
            print(
                f"  {destination:9} {temptation:12} {meal:14} {article:15} {value:12} wait={wait_level}"
            )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.child_name}: {p.destination}, {p.temptation} vs {p.meal}, "
                f"{p.value}, wait={p.wait_level}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    dest: Destination,
    temptation: Temptation,
    meal: Meal,
    article: Article,
    value: MoralValue,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    grown_type: str = "mother",
    little_name: str = "Pip",
    little_gender: str = "boy",
    wait_level: int = 2,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=["small", "thoughtful"],
            attrs={"destination": dest.id},
        )
    )
    grown = world.add(
        Entity(
            id="Grown",
            kind="character",
            type=grown_type,
            role="grown",
            label="the grown-up",
            attrs={},
        )
    )
    little = world.add(
        Entity(
            id=little_name,
            kind="character",
            type=little_gender,
            role="little",
            attrs={},
        )
    )

    child.meters["hunger"] = 0.0
    child.meters["fuel"] = 0.0
    child.meters["nutrition"] = 0.0
    child.meters["energy_low"] = 0.0
    child.meters["steady"] = 0.0
    child.meters["shares_food"] = 0.0
    child.meters["sugar_rush"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["wisdom"] = 0.0
    child.memes["kind"] = 0.0
    little.meters["hunger"] = 0.0
    little.meters["fuel"] = 0.0
    little.meters["steady"] = 0.0
    little.memes["relief"] = 0.0

    world.facts["wait_level"] = wait_level
    world.facts["destination"] = dest
    world.facts["temptation"] = temptation
    world.facts["meal"] = meal
    world.facts["article"] = article
    world.facts["value"] = value
    world.facts["child"] = child
    world.facts["grown"] = grown
    world.facts["little"] = little

    introduce(world, child, grown, dest)
    waiting(world, child, wait_level)
    propagate(world, narrate=False)
    see_kiosk(world, child, temptation, meal)

    world.para()
    read_article(world, child, article)
    counsel(world, grown, child, meal, temptation)
    choose_meal(world, child, meal)

    world.para()
    if child.meters["steady"] >= THRESHOLD:
        steady_turn(world, child)
    else:
        low_energy_turn(world, child, temptation)
    meet_little(world, child, little)
    share_if_possible(world, child, little, meal, value)

    world.para()
    moral_close(world, child, grown, dest, value)

    world.facts["outcome"] = "steady" if child.meters["steady"] >= THRESHOLD else "wobbly"
    world.facts["shared"] = child.memes["kind"] >= THRESHOLD
    return world


DESTINATIONS = {
    "southern": Destination(
        id="southern",
        adjective="southern",
        place="seaside town",
        image="warm porches and peach-colored sunset",
        tags={"southern"},
    ),
    "mountain": Destination(
        id="mountain",
        adjective="mountain",
        place="valley town",
        image="green hills and a river curling below",
        tags={"travel"},
    ),
    "island": Destination(
        id="island",
        adjective="sunny",
        place="island stop",
        image="bright water and bobbing boats",
        tags={"travel"},
    ),
}

TEMPTATIONS = {
    "candy_twist": Temptation(
        id="candy_twist",
        label="candy twist",
        phrase="a bright candy twist",
        rhyme="twisty and misty, sugar and shine",
        sugar=3,
        nutrition=0,
        plural=False,
        tags={"sweet"},
    ),
    "frosted_bun": Temptation(
        id="frosted_bun",
        label="frosted bun",
        phrase="a frosted bun with white curls of icing",
        rhyme="bun in a swirl, sweet as a whirl",
        sugar=2,
        nutrition=1,
        plural=False,
        tags={"sweet", "bun"},
    ),
    "glazed_bits": Temptation(
        id="glazed_bits",
        label="glazed bits",
        phrase="a little bag of glazed bits",
        rhyme="tiny and shiny, sticky and fine",
        sugar=2,
        nutrition=0,
        plural=True,
        tags={"sweet"},
    ),
}

MEALS = {
    "peach_oats": Meal(
        id="peach_oats",
        label="peach oats",
        phrase="a cup of peach oats",
        rhyme="oats with a peach make travel a breeze",
        energy=2,
        nutrition=3,
        shareable=True,
        tags={"nutrition", "fruit", "southern"},
    ),
    "yogurt_parfait": Meal(
        id="yogurt_parfait",
        label="yogurt parfait",
        phrase="a yogurt parfait with fruit and nuts",
        rhyme="layer by layer, strong for the way",
        energy=2,
        nutrition=3,
        shareable=True,
        tags={"nutrition", "dairy"},
    ),
    "egg_wrap": Meal(
        id="egg_wrap",
        label="egg wrap",
        phrase="a warm egg wrap",
        rhyme="wrap neat and snug for a gate-side hug",
        energy=3,
        nutrition=2,
        shareable=False,
        tags={"nutrition", "savory"},
    ),
    "juice_box": Meal(
        id="juice_box",
        label="juice box",
        phrase="a juice box with a striped straw",
        rhyme="sip and skip, quick little trip",
        energy=1,
        nutrition=1,
        shareable=False,
        tags={"drink"},
    ),
    "frosted_bun": Meal(
        id="frosted_bun",
        label="frosted bun",
        phrase="a frosted bun with white curls of icing",
        rhyme="bun in a swirl, sweet as a whirl",
        energy=1,
        nutrition=1,
        shareable=False,
        tags={"sweet"},
    ),
}

ARTICLES = {
    "gate_magazine": Article(
        id="gate_magazine",
        title="Tiny Travelers and Good Nutrition",
        line="food with fruit, grain, or protein helps small legs stay strong through a long wait",
        source="a family magazine from the airport rack",
        tags={"article", "nutrition"},
    ),
    "safety_paper": Article(
        id="safety_paper",
        title="A Calm Trip Starts with Good Snacks",
        line="a wise traveler eats more than sugar before a busy walk to the gate",
        source="a folded airport paper beside the window",
        tags={"article", "nutrition"},
    ),
    "southern_column": Article(
        id="southern_column",
        title="A Southern Auntie's Traveling Tray",
        line="peaches, oats, and yogurt make a gentle airport meal for growing children",
        source="a bright travel article in a small magazine",
        tags={"article", "nutrition", "southern"},
    ),
}

VALUES = {
    "care": MoralValue(
        id="care",
        name="care",
        lesson="Care means thinking ahead for your body as well as your wishes.",
        ending="That was care in action: a kind hand and a thoughtful choice.",
        tags={"care"},
    ),
    "kindness": MoralValue(
        id="kindness",
        name="kindness",
        lesson="Kindness grows best when we have enough and remember to share.",
        ending="That was kindness in action: one small snack, two brighter faces.",
        tags={"kindness"},
    ),
    "self_control": MoralValue(
        id="self_control",
        name="self-control",
        lesson="Self-control is choosing what helps, not only what glitters.",
        ending="That was self-control in bloom, and kindness followed close behind.",
        tags={"self_control"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mia", "June", "Ella", "Zoe", "Anna", "Ruby"]
BOY_NAMES = ["Pip", "Ben", "Theo", "Sam", "Max", "Eli", "Noah", "Finn"]

if __name__ == "__main__":
    main()
