#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py
========================================================

A standalone storyworld for a tall-tale-flavored sharing story.

Premise
-------
A child in a wide, exaggerated landscape finds a piece of food so enormous it
belongs in a brag, not a lunch. The child first wants the whole marvel alone,
but the thing is too big to move without a struggle. A sibling or friend warns
that sharing will bring help. Depending on the child's generous nature, and how
long they wait before agreeing, the giant treat becomes either an easy town
feast, a saved feast after a clumsy delay, or a partly lost meal with a lesson:
something shared is better than something hoarded.

Run it
------
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py --food peach --serve bowls
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py --tool pocket_rope
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/struggle_sharing_tall_tale.py --verify
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
SENSE_MIN = 2
GENEROUS_TRAITS = {"fair", "kind", "bighearted"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "woman", "aunt"}
        male = {"boy", "father", "grandpa", "man", "uncle"}
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
            "grandma": "grandma",
            "grandpa": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    affords_tools: set[str] = field(default_factory=set)
    crowd: str = ""
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
class GiantFood:
    id: str
    label: str
    phrase: str
    boast: str
    weight: int
    patience: int
    styles: set[str] = field(default_factory=set)
    critters: str = ""
    flavor: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    capacity: int
    sense: int
    motion: str
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
class ServeStyle:
    id: str
    label: str
    cut: str
    table: str
    scraps: str
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
    def __init__(self, setting: Setting, delay: int) -> None:
        self.setting = setting
        self.delay = delay
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "shared": False,
            "helpers_called": 0,
            "dropped": False,
            "outcome": "",
            "predicted_crack": False,
            "predicted_loss": False,
            "community": "",
        }

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
        clone = World(self.setting, self.delay)
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


def _r_struggle(world: World) -> list[str]:
    hero = world.get(world.facts["hero_id"])
    food = world.get(world.facts["food_id"])
    if food.meters["dragged"] < THRESHOLD or world.facts["shared"]:
        return []
    if hero.attrs["strength"] >= food.attrs["weight"]:
        return []
    sig = ("struggle", hero.id, food.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["strain"] += float(food.attrs["weight"] - hero.attrs["strength"])
    hero.memes["frustration"] += 1
    food.meters["wobble"] += 1
    return ["__struggle__"]


def _r_crack(world: World) -> list[str]:
    food = world.get(world.facts["food_id"])
    if food.meters["wobble"] < THRESHOLD or world.facts["shared"] or world.delay < 1:
        return []
    sig = ("crack", food.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["dropped"] = True
    food.meters["cracked"] += 1
    return ["__crack__"]


def _r_nibbled(world: World) -> list[str]:
    food = world.get(world.facts["food_id"])
    if food.meters["cracked"] < THRESHOLD or world.delay < 2:
        return []
    sig = ("nibbled", food.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    food.meters["nibbled"] += 1
    return ["__nibbled__"]


def _r_served(world: World) -> list[str]:
    food = world.get(world.facts["food_id"])
    tool = world.get(world.facts["tool_id"])
    hero = world.get(world.facts["hero_id"])
    helper = world.get(world.facts["helper_id"])
    if not world.facts["shared"] or food.meters["loaded"] < THRESHOLD:
        return []
    if tool.attrs["capacity"] < food.attrs["weight"]:
        return []
    sig = ("served", food.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    food.meters["served"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["generosity"] += 1
    helper.memes["love"] += 1
    return ["__served__"]


CAUSAL_RULES = [
    Rule(name="struggle", tag="physical", apply=_r_struggle),
    Rule(name="crack", tag="physical", apply=_r_crack),
    Rule(name="nibbled", tag="physical", apply=_r_nibbled),
    Rule(name="served", tag="social", apply=_r_served),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def can_serve(food: GiantFood, style: ServeStyle) -> bool:
    return style.id in food.styles


def tool_fits(setting: Setting, tool: Tool) -> bool:
    return tool.id in setting.affords_tools


def sensible_tool(tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN


def valid_combo(setting: Setting, food: GiantFood, tool: Tool, style: ServeStyle) -> bool:
    return (
        tool_fits(setting, tool)
        and sensible_tool(tool)
        and can_serve(food, style)
        and tool.capacity >= food.weight
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for food_id, food in FOODS.items():
            for tool_id, tool in TOOLS.items():
                for style_id, style in SERVE_STYLES.items():
                    if valid_combo(setting, food, tool, style):
                        out.append((setting_id, food_id, tool_id, style_id))
    return out


def would_share_early(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    if trait in GENEROUS_TRAITS:
        return True
    return relation == "siblings" and helper_age > hero_age


def outcome_of(params: "StoryParams") -> str:
    if would_share_early(params.relation, params.hero_age, params.helper_age, params.trait):
        return "early_feast"
    if params.delay <= FOODS[params.food].patience:
        return "saved_feast"
    return "picked_clean"


def predict_solo_trouble(world: World) -> dict:
    sim = world.copy()
    food = sim.get(sim.facts["food_id"])
    food.meters["dragged"] += 1
    propagate(sim, narrate=False)
    return {
        "strain": sim.get(sim.facts["hero_id"]).meters["strain"],
        "crack": food.meters["cracked"] >= THRESHOLD,
        "nibbled": food.meters["nibbled"] >= THRESHOLD,
    }


def tell_tall_opening(world: World, hero: Entity, helper: Entity, food: GiantFood) -> None:
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"On a day when the sky seemed stretched extra wide over {world.setting.label}, "
        f"{hero.id} and {helper.id} came upon {food.phrase}. It was {food.boast}."
    )
    world.say(
        f"In a true tall tale, even the smell was oversized: {food.flavor}. "
        f"The whole place felt as if breakfast had grown up and learned bragging."
    )


def introduce_need(world: World, hero: Entity, food: GiantFood) -> None:
    world.say(
        f"{hero.id} licked {hero.pronoun('possessive')} lips and thought of keeping every bite. "
        f'But {food.label} was so huge that one child could not simply tuck it under an arm and trot away.'
    )


def warn_with_prediction(world: World, hero: Entity, helper: Entity, elder: Entity, food: GiantFood) -> None:
    pred = predict_solo_trouble(world)
    world.facts["predicted_crack"] = pred["crack"]
    world.facts["predicted_loss"] = pred["nibbled"]
    helper.memes["care"] += 1
    extra = ""
    if pred["crack"] and pred["nibbled"]:
        extra = f" If you try alone, it may split open and {food.critters} will beat us to it."
    elif pred["crack"]:
        extra = " If you try alone, it may thump right back onto the ground and split."
    world.say(
        f'"That is too much for one pair of hands," {helper.id} said. '
        f'"If we share it, {world.setting.crowd} will help us carry it, and everyone will taste the brag."{extra}'
    )
    world.say(
        f"{elder.label_word.capitalize()} always said that a wonder grows kinder when it is shared, "
        f"and the words came back to both children just then."
    )


def choose_to_share_now(world: World, hero: Entity) -> None:
    hero.memes["generosity"] += 1
    hero.memes["greed"] = 0.0
    world.say(
        f"{hero.id} looked again at the giant treat, then at the empty space all around it, "
        f"and felt smaller than the idea of keeping it alone."
    )
    world.say(
        f'"You are right," {hero.pronoun()} said. "A story this big ought to have room for more than me."'
    )


def refuse_to_share(world: World, hero: Entity, helper: Entity, food: GiantFood) -> None:
    hero.memes["greed"] += 1
    world.say(
        f'But {hero.id} hugged the thought of having it all. "I found it, so I can haul it," '
        f"{hero.pronoun()} said, planting {hero.pronoun('possessive')} feet."
    )
    world.say(
        f"{helper.id} stepped back, not unkindly, while {hero.id} bent to the job and began the struggle."
    )
    food.meters["dragged"] += 1
    propagate(world, narrate=False)


def narrate_struggle(world: World, hero: Entity, food: GiantFood) -> None:
    if hero.meters["strain"] >= THRESHOLD:
        world.say(
            f"{hero.id} pulled until {hero.pronoun('possessive')} hat slipped crooked and "
            f"{hero.pronoun('possessive')} boots scratched furrows in the earth. The struggle was so fierce "
            f"it looked as if the ground might move before {food.label} did."
        )
    if food.meters["cracked"] >= THRESHOLD:
        world.say(
            f"Then {food.label} gave a mighty wobble, rolled half a turn, and cracked with a sound like a cupboard door in a thunderstorm."
        )
    if food.meters["nibbled"] >= THRESHOLD:
        world.say(
            f"In no time, {food.critters} swooped in from nowhere, as if they had been waiting behind the wind itself."
        )


def elder_turn(world: World, hero: Entity, helper: Entity, elder: Entity, food: GiantFood) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"{elder.label_word.capitalize()} came over at a quick clip, took one look, and knelt beside the children."
    )
    if food.meters["nibbled"] >= THRESHOLD:
        world.say(
            f'"There now," {elder.pronoun()} said gently. "Hoarding made us late, but sharing can still make the last of it sweet."'
        )
    else:
        world.say(
            f'"There now," {elder.pronoun()} said gently. "No one wins a wrestling match with supper. Call the others and let the feast become a feast."'
        )
    world.say(
        f"{hero.id} nodded at last, because the truth was plain as a bell in the open air."
    )
    helper.memes["love"] += 1
    hero.memes["generosity"] += 1
    world.facts["shared"] = True


def gather_and_load(world: World, hero: Entity, helper: Entity, food: GiantFood, tool: Tool) -> None:
    food.meters["loaded"] += 1
    world.facts["helpers_called"] = 6
    world.facts["community"] = world.setting.crowd
    propagate(world, narrate=False)
    world.say(
        f"Soon {world.setting.crowd} came hurrying with cheers, and together they heaved {food.label} onto {tool.phrase}. "
        f"{tool.motion.capitalize()}."
    )
    world.say(
        f"{hero.id} no longer looked like a child trying to own a marvel. {hero.pronoun().capitalize()} looked like the host of one."
    )


def feast_ending(world: World, hero: Entity, helper: Entity, food: GiantFood, style: ServeStyle) -> None:
    world.say(
        f"At the long table, they {style.cut}. Then they {style.table}."
    )
    world.say(
        f"People laughed, traded stories taller than fence posts, and each time a plate passed by, "
        f"{hero.id} passed it farther instead of pulling it back."
    )
    if world.facts["outcome"] == "early_feast":
        world.say(
            f"By sundown, the giant meal had become a town memory, and {hero.id} learned that sharing early makes a wonder feel even bigger."
        )
    else:
        world.say(
            f"By sundown, enough was saved for a grand supper after all, and {hero.id} learned that sharing can rescue joy even after a stubborn start."
        )
    world.say(
        f"When the stars came up, {hero.id} and {helper.id} sat with sticky fingers and happy faces, watching the last empty platter shine like a small moon."
    )


def scraps_ending(world: World, hero: Entity, helper: Entity, food: GiantFood, style: ServeStyle) -> None:
    world.say(
        f"There was not enough left for the bragging feast {hero.id} had first imagined. Still, they gathered {style.scraps} and set them out carefully."
    )
    world.say(
        f"Each person got only a little taste, yet the little tasted bright because it was finally shared. "
        f"{hero.id} offered the first bit to {helper.id}, then the next to {elder_name(world)}."
    )
    world.say(
        f"That night, under a sky wide enough for any tall tale, {hero.id} understood that keeping too tight a fist can make a big gift small, "
        f"but sharing even the last crumbs can make hearts feel large again."
    )


def elder_name(world: World) -> str:
    elder = world.get(world.facts["elder_id"])
    return elder.label_word


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        label="the windy prairie",
        opening="where grass bowed like green waves",
        affords_tools={"wagon", "wheelbarrow"},
        crowd="the whole prairie neighborhood",
        tags={"prairie"},
    ),
    "orchard": Setting(
        id="orchard",
        label="the orchard",
        opening="where rows of trees made dappled aisles",
        affords_tools={"wagon", "wheelbarrow"},
        crowd="everyone from the orchard lane",
        tags={"orchard"},
    ),
    "riverside": Setting(
        id="riverside",
        label="the riverside",
        opening="where the water flashed like tin in the sun",
        affords_tools={"raft", "wagon"},
        crowd="the riverside families",
        tags={"river"},
    ),
    "fairground": Setting(
        id="fairground",
        label="the county fairground",
        opening="where every tent seemed ready to tell a lie bigger than the last",
        affords_tools={"wagon", "wheelbarrow"},
        crowd="the fair folk",
        tags={"fair"},
    ),
}

FOODS = {
    "peach": GiantFood(
        id="peach",
        label="the peach",
        phrase="a peach so big it threw its own shade",
        boast="round as a haystack and gold as late summer",
        weight=2,
        patience=1,
        styles={"slices", "bowls"},
        critters="yellow jackets and orchard birds",
        flavor="sweet enough to make the breeze smell sugary",
        tags={"peach", "fruit"},
    ),
    "cheese": GiantFood(
        id="cheese",
        label="the cheese wheel",
        phrase="a cheese wheel taller than a milk stool",
        boast="broad as a washtub and pale as the moon through cream",
        weight=3,
        patience=2,
        styles={"wedges", "cubes"},
        critters="mice and bold black crows",
        flavor="rich and buttery, with a smell that could wake a sleepy barn cat",
        tags={"cheese", "dairy"},
    ),
    "loaf": GiantFood(
        id="loaf",
        label="the corn loaf",
        phrase="a corn loaf as long as a canoe",
        boast="steaming like a bakery chimney and crusty as golden bark",
        weight=2,
        patience=2,
        styles={"slices", "chunks"},
        critters="sparrows and a marching ribbon of ants",
        flavor="warm as sunshine on a kitchen window",
        tags={"bread", "cornbread"},
    ),
    "melon": GiantFood(
        id="melon",
        label="the watermelon",
        phrase="a watermelon big enough to need its own weather",
        boast="striped like a green barn and cool as a shaded well",
        weight=3,
        patience=1,
        styles={"slices", "bowls"},
        critters="bees and thirsty field birds",
        flavor="fresh and cool, as if the whole river had turned sweet",
        tags={"melon", "fruit"},
    ),
}

TOOLS = {
    "wagon": Tool(
        id="wagon",
        label="wagon",
        phrase="the red wagon",
        capacity=3,
        sense=3,
        motion="the wheels groaned once, then rolled as steadily as a parade drum",
        tags={"wagon"},
    ),
    "wheelbarrow": Tool(
        id="wheelbarrow",
        label="wheelbarrow",
        phrase="the biggest wheelbarrow in sight",
        capacity=2,
        sense=3,
        motion="the single wheel squeaked bravely and carried the load like a tiny hero",
        tags={"wheelbarrow"},
    ),
    "raft": Tool(
        id="raft",
        label="raft",
        phrase="the broad flat raft",
        capacity=4,
        sense=3,
        motion="it bobbed once and then floated off as smooth as a leaf on soup",
        tags={"raft"},
    ),
    "pocket_rope": Tool(
        id="pocket_rope",
        label="pocket rope",
        phrase="a skinny pocket rope",
        capacity=0,
        sense=1,
        motion="it twitched and gave up",
        tags={"rope"},
    ),
}

SERVE_STYLES = {
    "slices": ServeStyle(
        id="slices",
        label="slices",
        cut="cut it into sunset-bright slices",
        table="lined the slices down a table as long as a fence",
        scraps="a few sticky slices",
        tags={"slices"},
    ),
    "bowls": ServeStyle(
        id="bowls",
        label="bowls",
        cut="scooped the soft fruit into waiting bowls",
        table="passed the bowls hand to hand like little treasure pails",
        scraps="one shy row of little bowls",
        tags={"bowls"},
    ),
    "wedges": ServeStyle(
        id="wedges",
        label="wedges",
        cut="cut it into stout wedges",
        table="stacked the wedges on platters from one end of the table to the other",
        scraps="a few modest wedges",
        tags={"wedges"},
    ),
    "cubes": ServeStyle(
        id="cubes",
        label="cubes",
        cut="trimmed it into neat cubes",
        table="filled every plate with little pale blocks like edible building stones",
        scraps="a small plate of cubes",
        tags={"cubes"},
    ),
    "chunks": ServeStyle(
        id="chunks",
        label="chunks",
        cut="broke it into warm, buttery chunks",
        table="passed the chunks around while steam still curled from them",
        scraps="a basket with a few warm chunks",
        tags={"chunks"},
    ),
}

GIRL_NAMES = ["Molly", "Ada", "June", "Lila", "Nell", "Ruby", "Tess", "Willa"]
BOY_NAMES = ["Hank", "Eli", "Bo", "Cal", "Jesse", "Ned", "Owen", "Silas"]
TRAITS = ["fair", "kind", "bighearted", "stubborn", "proud", "bossy"]
ELDERS = ["mother", "father", "grandma", "grandpa", "aunt", "uncle"]


@dataclass
class StoryParams:
    setting: str
    food: str
    tool: str
    serve: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    trait: str
    relation: str = "friends"
    hero_age: int = 6
    helper_age: int = 6
    delay: int = 1
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
        setting="orchard",
        food="peach",
        tool="wagon",
        serve="slices",
        hero="Molly",
        hero_gender="girl",
        helper="Eli",
        helper_gender="boy",
        elder="grandma",
        trait="fair",
        relation="friends",
        hero_age=6,
        helper_age=6,
        delay=0,
    ),
    StoryParams(
        setting="prairie",
        food="loaf",
        tool="wheelbarrow",
        serve="chunks",
        hero="Bo",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        elder="mother",
        trait="stubborn",
        relation="friends",
        hero_age=6,
        helper_age=6,
        delay=1,
    ),
    StoryParams(
        setting="riverside",
        food="melon",
        tool="raft",
        serve="bowls",
        hero="June",
        hero_gender="girl",
        helper="Lila",
        helper_gender="girl",
        elder="father",
        trait="proud",
        relation="siblings",
        hero_age=5,
        helper_age=7,
        delay=0,
    ),
    StoryParams(
        setting="fairground",
        food="cheese",
        tool="wagon",
        serve="wedges",
        hero="Hank",
        hero_gender="boy",
        helper="Nell",
        helper_gender="girl",
        elder="grandpa",
        trait="bossy",
        relation="friends",
        hero_age=7,
        helper_age=6,
        delay=2,
    ),
]


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.phrase} is not a sensible way to move a giant feast here "
        f"(sense={tool.sense} < {SENSE_MIN}). Pick a sturdier tool like "
        f"{', '.join(sorted(t.id for t in TOOLS.values() if t.sense >= SENSE_MIN))}.)"
    )


def explain_combo(setting: Setting, food: GiantFood, tool: Tool, style: ServeStyle) -> str:
    if not tool_fits(setting, tool):
        return (
            f"(No story: {tool.label} does not belong naturally in {setting.label}, "
            f"so the haul would not feel grounded in this world.)"
        )
    if not sensible_tool(tool):
        return explain_tool(tool.id)
    if not can_serve(food, style):
        return (
            f"(No story: {food.label} is not reasonably served as {style.label}. "
            f"Choose one of: {', '.join(sorted(food.styles))}.)"
        )
    if tool.capacity < food.weight:
        return (
            f"(No story: {tool.label} cannot carry {food.label}. "
            f"A tall tale may be big, but the fix still has to make sense.)"
        )
    return "(No story: that combination does not make sense in this world.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale sharing storyworld: a giant treat, a struggle, and a lesson about sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--serve", choices=SERVE_STYLES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child waits before agreeing to share")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid story combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not sensible_tool(TOOLS[args.tool]):
        raise StoryError(explain_tool(args.tool))
    if args.food and args.serve and not can_serve(FOODS[args.food], SERVE_STYLES[args.serve]):
        setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        tool = TOOLS[args.tool] if args.tool else next(t for t in TOOLS.values() if t.sense >= SENSE_MIN)
        raise StoryError(explain_combo(setting, FOODS[args.food], tool, SERVE_STYLES[args.serve]))
    if args.setting and args.tool and not tool_fits(SETTINGS[args.setting], TOOLS[args.tool]):
        food = FOODS[args.food] if args.food else next(iter(FOODS.values()))
        style = SERVE_STYLES[args.serve] if args.serve else SERVE_STYLES[next(iter(food.styles))]
        raise StoryError(explain_combo(SETTINGS[args.setting], food, TOOLS[args.tool], style))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.food is None or combo[1] == args.food)
        and (args.tool is None or combo[2] == args.tool)
        and (args.serve is None or combo[3] == args.serve)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, food_id, tool_id, style_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero = _pick_name(rng, hero_gender)
    helper = _pick_name(rng, helper_gender, avoid=hero)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    relation = args.relation or rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        food=food_id,
        tool=tool_id,
        serve=style_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        trait=trait,
        relation=relation,
        hero_age=ages[0],
        helper_age=ages[1],
        delay=delay,
    )


def tell(
    setting: Setting,
    food_cfg: GiantFood,
    tool_cfg: Tool,
    style_cfg: ServeStyle,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    elder_type: str,
    trait: str,
    relation: str,
    hero_age: int,
    helper_age: int,
    delay: int,
) -> World:
    world = World(setting=setting, delay=delay)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            age=hero_age,
            attrs={"strength": 1, "relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=["helpful"],
            age=helper_age,
            attrs={"strength": 1, "relation": relation},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            attrs={},
        )
    )
    food = world.add(
        Entity(
            id="food",
            kind="thing",
            type="food",
            label=food_cfg.label,
            phrase=food_cfg.phrase,
            role="food",
            attrs={"weight": food_cfg.weight, "patience": food_cfg.patience},
            tags=set(food_cfg.tags),
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            role="tool",
            attrs={"capacity": tool_cfg.capacity, "sense": tool_cfg.sense},
            tags=set(tool_cfg.tags),
        )
    )

    world.facts.update(
        hero_id=hero.id,
        helper_id=helper.id,
        elder_id=elder.id,
        food_id=food.id,
        tool_id=tool.id,
        setting=setting,
        food_cfg=food_cfg,
        tool_cfg=tool_cfg,
        style_cfg=style_cfg,
        relation=relation,
    )

    tell_tall_opening(world, hero, helper, food_cfg)
    world.say(
        f"{setting.opening.capitalize()}, the children stared so hard that even the crows on the fence seemed to stare with them."
    )
    introduce_need(world, hero, food_cfg)

    world.para()
    warn_with_prediction(world, hero, helper, elder, food_cfg)
    early = would_share_early(relation, hero_age, helper_age, trait)

    if early:
        choose_to_share_now(world, hero)
        world.para()
        world.facts["shared"] = True
        world.facts["outcome"] = "early_feast"
        gather_and_load(world, hero, helper, food, tool_cfg)
        feast_ending(world, hero, helper, food_cfg, style_cfg)
    else:
        refuse_to_share(world, hero, helper, food_cfg)
        narrate_struggle(world, hero, food)
        world.para()
        elder_turn(world, hero, helper, elder, food_cfg)
        world.facts["outcome"] = "saved_feast" if delay <= food_cfg.patience else "picked_clean"
        gather_and_load(world, hero, helper, food, tool_cfg)
        if world.facts["outcome"] == "picked_clean":
            scraps_ending(world, hero, helper, food_cfg, style_cfg)
        else:
            feast_ending(world, hero, helper, food_cfg, style_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        food=food,
        outcome=world.facts["outcome"],
        early_shared=early,
        struggle=hero.meters["strain"] >= THRESHOLD,
        cracked=food.meters["cracked"] >= THRESHOLD,
        nibbled=food.meters["nibbled"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    food_cfg = world.facts["food_cfg"]
    setting = world.facts["setting"]
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the word "struggle" and ends with a lesson about sharing.',
        f"Tell a giant-food story where {hero.id} finds {food_cfg.phrase} in {setting.label}, tries to claim it, and learns that sharing brings help.",
        f"Write a warm tall tale about {helper.id} warning that a wonder is too big for one child alone, and turn the story toward a shared feast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    elder = world.facts["elder"]
    food_cfg = world.facts["food_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    style_cfg = world.facts["style_cfg"]
    relation = world.facts["relation"]
    outcome = world.facts["outcome"]
    pair = pair_noun(hero, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, who find {food_cfg.phrase}. It is also about {elder.label_word}, who helps turn the trouble into a lesson.",
        ),
        (
            f"What made the giant food hard to handle?",
            f"It was far too big for one child to carry alone, so moving it became a real struggle. That is why {helper.id} warned that sharing would bring enough hands to help.",
        ),
        (
            f"Why did {helper.id} want to share the food?",
            f"{helper.id} knew the giant treat was too much for one child and too special to hide away. Sharing would bring people, a proper hauling plan, and joy for everyone instead of a lonely tug-of-war.",
        ),
    ]
    if world.facts["struggle"]:
        qa.append(
            (
                f"What happened when {hero.id} tried to move it alone?",
                f"{hero.id} strained and struggled, because the giant food was heavier than one child could manage. The hard pulling made it wobble, and that is what brought the trouble next.",
            )
        )
    if world.facts["cracked"] and not world.facts["nibbled"]:
        qa.append(
            (
                "Did the delay cause any trouble?",
                f"Yes. The giant food cracked after being handled the hard way, which showed that keeping it to one person was making things worse. They still saved the feast because they agreed to share before too much was lost.",
            )
        )
    if world.facts["nibbled"]:
        qa.append(
            (
                "What was lost because the child waited too long to share?",
                f"Some of the feast was lost to {food_cfg.critters}. The delay mattered because once the food cracked open, the waiting gave the hungry little thieves time to get there first.",
            )
        )
    if outcome == "early_feast":
        qa.append(
            (
                f"How did the story end?",
                f"It ended with an easy shared feast. {hero.id} chose sharing before the trouble grew, so the giant treat rode on {tool_cfg.phrase} and was served as {style_cfg.label} for everyone.",
            )
        )
    elif outcome == "saved_feast":
        qa.append(
            (
                f"How did the story end?",
                f"It ended with a saved feast after a rough start. Once {hero.id} agreed to share, people helped load the food onto {tool_cfg.phrase}, and there was still plenty to serve.",
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"It ended with only a little left, but that little was shared. The big feast became a smaller one because {hero.id} waited too long, and the ending proves the lesson by showing {hero.id} giving the first taste away.",
            )
        )
    return qa


KNOWLEDGE = {
    "sharing": [
        (
            "Why can sharing help with a hard job?",
            "Sharing can bring more hands, more ideas, and kinder feelings. A job that is too big for one person often becomes possible when people help one another.",
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is a little cart with wheels for carrying heavy things. It helps move a load that would be hard to drag by hand.",
        )
    ],
    "wheelbarrow": [
        (
            "What does a wheelbarrow do?",
            "A wheelbarrow lets one or two people push a heavy load with the help of a wheel. It is handy for gardens, yards, and fairgrounds.",
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a flat thing that floats on water. People can use it to carry loads across or along a river.",
        )
    ],
    "peach": [
        (
            "What is a peach?",
            "A peach is a soft, sweet fruit with a pit in the middle. It can be juicy and sticky when you cut it open.",
        )
    ],
    "cheese": [
        (
            "What is a cheese wheel?",
            "A cheese wheel is a big round piece of cheese. People cut it into pieces so many people can eat from it.",
        )
    ],
    "bread": [
        (
            "What is a loaf of bread?",
            "A loaf is bread baked in one big piece. You can slice it or break it into chunks to share.",
        )
    ],
    "melon": [
        (
            "What is a watermelon?",
            "A watermelon is a large fruit with a thick green outside and juicy inside. It is full of water and tastes cool and sweet.",
        )
    ],
    "tall_tale": [
        (
            "What is a tall tale?",
            "A tall tale is a story that uses playful exaggeration. Big things seem bigger than real life, but the feelings and lessons still make sense.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "tall_tale",
    "sharing",
    "wagon",
    "wheelbarrow",
    "raft",
    "peach",
    "cheese",
    "bread",
    "melon",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing", "tall_tale"}
    tags |= set(world.facts["tool_cfg"].tags)
    tags |= set(world.facts["food_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  delay={world.delay}")
    lines.append(f"  facts={{'outcome': {world.facts.get('outcome')!r}, 'shared': {world.facts.get('shared')}, 'helpers_called': {world.facts.get('helpers_called')}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- validity gate ----------------------------------------------------------
valid(Setting, Food, Tool, Serve) :-
    setting(Setting), food(Food), tool(Tool), serve(Serve),
    affords_tool(Setting, Tool),
    sensible(Tool),
    serves_as(Food, Serve),
    capacity(Tool, Cap),
    weight(Food, W),
    Cap >= W.

sensible(Tool) :- tool(Tool), sense(Tool, S), sense_min(M), S >= M.

% --- outcome model ----------------------------------------------------------
generous_now :- trait(T), generous_trait(T).
helper_older :- relation(siblings), helper_age(H), hero_age(A), H > A.
share_early :- generous_now.
share_early :- helper_older.

saved_in_time :- chosen_food(F), patience(F, P), delay(D), D <= P.

outcome(early_feast) :- share_early.
outcome(saved_feast) :- not share_early, saved_in_time.
outcome(picked_clean) :- not share_early, not saved_in_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for tool_id in sorted(setting.affords_tools):
            lines.append(asp.fact("affords_tool", setting_id, tool_id))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("weight", food_id, food.weight))
        lines.append(asp.fact("patience", food_id, food.patience))
        for style in sorted(food.styles):
            lines.append(asp.fact("serves_as", food_id, style))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("capacity", tool_id, tool.capacity))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    for style_id in SERVE_STYLES:
        lines.append(asp.fact("serve", style_id))
    for trait in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_food", params.food),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.serve not in SERVE_STYLES:
        raise StoryError(f"(Unknown serve style: {params.serve})")

    setting = SETTINGS[params.setting]
    food = FOODS[params.food]
    tool = TOOLS[params.tool]
    style = SERVE_STYLES[params.serve]

    if not valid_combo(setting, food, tool, style):
        raise StoryError(explain_combo(setting, food, tool, style))

    world = tell(
        setting=setting,
        food_cfg=food,
        tool_cfg=tool,
        style_cfg=style,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        delay=params.delay,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, food, tool, serve) combos:\n")
        for setting, food, tool, serve in combos:
            print(f"  {setting:10} {food:8} {tool:12} {serve}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.helper}: {p.food} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
