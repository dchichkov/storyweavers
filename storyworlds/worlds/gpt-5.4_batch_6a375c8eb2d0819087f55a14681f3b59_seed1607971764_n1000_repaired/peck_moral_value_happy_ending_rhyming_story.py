#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py
=========================================================================

A standalone story world for a tiny rhyming tale about birds, pecking, and the
moral value of sharing. Two young birds find a treat. One wants to peck it all
at once, but that choice would waste food and hurt feelings. A calm grown-up
helps them choose a fair sharing method, and the story ends happily with full
tummies and a kinder habit.

The world is state-driven: food can be scattered or saved, hunger can ease,
jealousy can rise, and kindness can grow. The prose is rendered from those
changes rather than from a single frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py --food berry_cluster
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py --food seed_pile --method split_bowl
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/peck_moral_value_happy_ending_rhyming_story.py --verify
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
        female = {"girl", "hen", "mother", "woman"}
        male = {"boy", "rooster", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"hen": "hen", "rooster": "rooster", "mother": "mom", "father": "dad"}.get(
            self.type, self.type
        )
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    wind: str
    helper_type: str
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
class Food:
    id: str
    label: str
    phrase: str
    plural: bool
    texture: str
    unit_kind: str
    size: int
    scatter_risk: int
    split_word: str
    rhyme_line: str
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
class ShareMethod:
    id: str
    sense: int
    works_on: set[str]
    keeps_food: bool
    fair: bool
    text: str
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


@dataclass
class Mood:
    id: str
    brave_line: str
    warning_style: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def birds(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    food = world.get("food")
    if food.meters["rushed_peck"] < THRESHOLD:
        return out
    sig = ("scatter", food.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    risk = int(food.attrs.get("scatter_risk", 1))
    food.meters["saved"] = max(0.0, food.meters["saved"] - float(risk))
    food.meters["lost"] += float(risk)
    for bird in world.birds():
        bird.meters["hunger"] += 1.0
    world.get("room").meters["mess"] += 1.0
    out.append("__scatter__")
    return out


def _r_fairness(world: World) -> list[str]:
    out: list[str] = []
    food = world.get("food")
    if food.meters["shared"] < THRESHOLD:
        return out
    sig = ("fair", food.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for bird in world.birds():
        bird.meters["hunger"] = 0.0
        bird.memes["relief"] += 1.0
        bird.memes["kindness"] += 1.0
    world.get("room").meters["mess"] = 0.0
    out.append("__fair__")
    return out


def _r_jealousy(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("instigator")
    b = world.get("cautioner")
    if a.memes["greed"] < THRESHOLD:
        return out
    sig = ("jealousy", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    b.memes["sad"] += 1.0
    b.memes["jealousy"] += 1.0
    out.append("__sad__")
    return out


CAUSAL_RULES = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
    Rule(name="fairness", tag="social", apply=_r_fairness),
    Rule(name="jealousy", tag="emotional", apply=_r_jealousy),
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


def method_fits(food: Food, method: ShareMethod) -> bool:
    return food.unit_kind in method.works_on and method.sense >= SENSE_MIN and method.fair and method.keeps_food


def sensible_methods() -> list[ShareMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN and m.fair and m.keeps_food]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for food_id, food in FOODS.items():
            for method_id, method in METHODS.items():
                for mood_id in MOODS:
                    if method_fits(food, method):
                        combos.append((setting_id, food_id, method_id, mood_id))
    return combos


def predict_rush(world: World) -> dict:
    sim = world.copy()
    food = sim.get("food")
    food.meters["rushed_peck"] += 1.0
    sim.get("instigator").memes["greed"] += 1.0
    propagate(sim, narrate=False)
    return {
        "lost": int(food.meters["lost"]),
        "saved": int(food.meters["saved"]),
        "mess": int(sim.get("room").meters["mess"]),
        "cautioner_sad": sim.get("cautioner").memes["sad"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, beneath a sky so bright, "
        f"{a.id} and {b.id} hopped out in the light."
    )
    world.say(
        f"{setting.image} and {setting.wind}, soft and slow, "
        f"made even the smallest feather glow."
    )


def discover_food(world: World, a: Entity, b: Entity, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["saved"] = float(food.size)
    world.say(
        f"Then there by a stone lay {food.phrase} to see. "
        f'"A snack!" chirped {a.id}. "A snack for me!"'
    )
    world.say(
        f'{b.id} blinked at the treat with a hopeful peep. '
        f'"If we share it kindly, we both can eat."'
    )


def tempt(world: World, a: Entity, mood: Mood, food: Food) -> None:
    a.memes["desire"] += 1.0
    a.memes["greed"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f'But {a.id} felt hungry and bold as a drum. '
        f'"I can peck it all up before others come!"'
    )
    world.say(mood.brave_line.format(name=a.id, food=food.label))


def warn(world: World, b: Entity, helper: Entity, food: Food, mood: Mood) -> None:
    pred = predict_rush(world)
    world.facts["predicted_lost"] = pred["lost"]
    world.facts["predicted_saved"] = pred["saved"]
    world.facts["predicted_mess"] = pred["mess"]
    b.memes["care"] += 1.0
    world.say(
        mood.warning_style.format(
            cautioner=b.id,
            helper=helper.label_word,
            food=food.label,
            lost=pred["lost"],
        )
    )
    if pred["cautioner_sad"]:
        world.say(
            f'"A greedy peck can leave one friend blue, '
            f'and spilled little bits help neither of you."'
        )


def rush_peck(world: World, a: Entity, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["rushed_peck"] += 1.0
    propagate(world, narrate=False)
    lost = int(food_ent.meters["lost"])
    saved = int(food_ent.meters["saved"])
    world.say(
        f"Still {a.id} darted with clickety beak, "
        f"trying to peck every morsel in streak after streak."
    )
    world.say(
        f"But {food.texture} flew left and {food.texture} flew right; "
        f"{lost} little bites were soon out of sight."
    )
    if saved > 0:
        world.say(
            f"Only {saved} good bites stayed close by the stone, "
            f"and suddenly sharing looked wiser than owning alone."
        )


def helper_arrives(world: World, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Just then came the {helper.label_word} with steps soft and slow, "
        f"watching the fuss and the crumbs down below."
    )


def guide_share(world: World, helper: Entity, a: Entity, b: Entity, method: ShareMethod, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["rushed_peck"] = 0.0
    food_ent.meters["shared"] += 1.0
    propagate(world, narrate=False)
    a.memes["greed"] = 0.0
    a.memes["shame"] += 1.0
    a.memes["kindness"] += 1.0
    b.memes["trust"] += 1.0
    world.say(
        f'"Little beaks," said the {helper.label_word}, "there is a better way. '
        f'{method.text}"'
    )
    world.say(
        f"So {a.id} took a breath and stepped back from the heap. "
        f"{b.id} stepped closer, no longer too meek."
    )
    world.say(
        f"They shared {food.split_word} and pecked without shove, "
        f"and the snack tasted sweeter with fairness and love."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity, food: Food) -> None:
    world.say(
        f'The {helper.label_word} smiled. "When hunger says, \'Mine!\' '
        f'pause first and be kind. A gentle beak leaves good cheer behind."'
    )
    world.say(
        f"{a.id} looked at {b.id} and bowed {a.pronoun('possessive')} head low. "
        f'"I should not have rushed. I know now, I know."'
    )
    world.say(
        f'"I forgive you," said {b.id}. "Now side by side we can peck, '
        f'and nobody has to feel small or a wreck."'
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting, food: Food) -> None:
    world.say(
        food.rhyme_line.format(a=a.id, b=b.id)
    )
    world.say(
        f"Home through {setting.place} they skipped in delight, "
        f"with full little bellies and hearts shining bright."
    )


def tell(
    setting: Setting,
    food: Food,
    method: ShareMethod,
    mood: Mood,
    instigator_name: str = "Pip",
    cautioner_name: str = "Dot",
) -> World:
    world = World(setting)
    world.add(Entity(id="room", type="place", label=setting.place))
    a = world.add(Entity(id="instigator", kind="character", type="bird", label=instigator_name, role="instigator"))
    b = world.add(Entity(id="cautioner", kind="character", type="bird", label=cautioner_name, role="cautioner"))
    helper = world.add(Entity(id="helper", kind="character", type=setting.helper_type, label=setting.helper_type, role="helper"))
    food_ent = world.add(
        Entity(
            id="food",
            type="food",
            label=food.label,
            attrs={"scatter_risk": food.scatter_risk, "size": food.size, "unit_kind": food.unit_kind},
            tags=set(food.tags),
        )
    )

    a.meters["hunger"] = 1.0
    b.meters["hunger"] = 1.0
    food_ent.meters["saved"] = float(food.size)
    food_ent.meters["lost"] = 0.0
    food_ent.meters["rushed_peck"] = 0.0
    food_ent.meters["shared"] = 0.0
    world.get("room").meters["mess"] = 0.0
    a.memes["greed"] = 0.0
    b.memes["sad"] = 0.0
    b.memes["jealousy"] = 0.0
    a.memes["kindness"] = 0.0
    b.memes["kindness"] = 0.0
    b.memes["trust"] = 0.0

    introduce(world, a, b, setting)
    discover_food(world, a, b, food)

    world.para()
    tempt(world, a, mood, food)
    warn(world, b, helper, food, mood)
    rush_peck(world, a, food)

    world.para()
    helper_arrives(world, helper, setting)
    guide_share(world, helper, a, b, method, food)
    lesson(world, helper, a, b, food)

    world.para()
    ending(world, a, b, setting, food)

    world.facts.update(
        setting=setting,
        food_cfg=food,
        method=method,
        mood=mood,
        instigator_name=instigator_name,
        cautioner_name=cautioner_name,
        helper=helper,
        food=food_ent,
        instigator=a,
        cautioner=b,
        shared=food_ent.meters["shared"] >= THRESHOLD,
        lost=int(food_ent.meters["lost"]),
        saved=int(food_ent.meters["saved"]),
        mess=world.get("room").meters["mess"] >= THRESHOLD,
        moral="sharing makes enough feel sweeter",
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden path",
        image="Daisies nodded by the gate",
        wind="the breeze hummed like a tiny flute",
        helper_type="hen",
        tags={"garden"},
    ),
    "farmyard": Setting(
        id="farmyard",
        place="the farmyard lane",
        image="Warm straw glowed beside the pen",
        wind="a sleepy breeze brushed feathers thin",
        helper_type="hen",
        tags={"farm"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard grass",
        image="Apple shadows danced in rings",
        wind="the leaves made whispery, rustly strings",
        helper_type="rooster",
        tags={"orchard"},
    ),
}

FOODS = {
    "seed_pile": Food(
        id="seed_pile",
        label="seeds",
        phrase="a small pile of yellow seeds",
        plural=True,
        texture="tiny seeds",
        unit_kind="loose",
        size=4,
        scatter_risk=2,
        split_word="seed by seed",
        rhyme_line="{a} and {b} pecked neat little rows, then sang to the breeze as homeward they rose.",
        tags={"seed", "sharing"},
    ),
    "berry_cluster": Food(
        id="berry_cluster",
        label="berries",
        phrase="a bright berry cluster",
        plural=True,
        texture="round red berries",
        unit_kind="cluster",
        size=4,
        scatter_risk=1,
        split_word="berry by berry",
        rhyme_line="{a} and {b} nibbled berries so round, while happy bird music hopped over the ground.",
        tags={"berry", "sharing"},
    ),
    "bread_crust": Food(
        id="bread_crust",
        label="bread crust",
        phrase="a soft bread crust with crumbs on the side",
        plural=False,
        texture="soft crumbs",
        unit_kind="piece",
        size=3,
        scatter_risk=2,
        split_word="bit after bit",
        rhyme_line="{a} and {b} pecked crumbs with delight, and the path felt gentle and golden and right.",
        tags={"bread", "sharing"},
    ),
}

METHODS = {
    "two_spots": ShareMethod(
        id="two_spots",
        sense=3,
        works_on={"loose"},
        keeps_food=True,
        fair=True,
        text="Let's tap the seeds into two tidy spots, one for each chick, with no grabbing and no hasty pecks.",
        qa_text="moved the seeds into two tidy spots so each bird had a fair share",
        tags={"sharing", "turns"},
    ),
    "split_bowl": ShareMethod(
        id="split_bowl",
        sense=3,
        works_on={"cluster", "piece"},
        keeps_food=True,
        fair=True,
        text="Let's split it in two and set the halves side by side, so each little bird can peck with pride.",
        qa_text="split the food into two fair halves and set them side by side",
        tags={"sharing", "fairness"},
    ),
    "take_turns": ShareMethod(
        id="take_turns",
        sense=2,
        works_on={"cluster", "piece"},
        keeps_food=True,
        fair=True,
        text="Let's take turns with patient feet: one peck for you, one peck for your friend, until the snack is complete.",
        qa_text="had the birds take turns, one peck each, until the snack was shared",
        tags={"sharing", "patience"},
    ),
    "big_scramble": ShareMethod(
        id="big_scramble",
        sense=1,
        works_on={"loose", "cluster", "piece"},
        keeps_food=False,
        fair=False,
        text="Just rush together and peck wherever bits may fly.",
        qa_text="rushed together in a messy scramble",
        tags={"mess"},
    ),
}

MOODS = {
    "boastful": Mood(
        id="boastful",
        brave_line='"{name} puffed up {name}\'s chest and gave a hungry peep: '
        '\'One peck, two pecks, and the whole snack I keep!\'"',
        warning_style='"{cautioner} shook {cautioner}\'s head. "If you peck too fast, {lost} bites may be lost, '
        'and the {helper} would call that a sad little cost."',
    ),
    "bouncy": Mood(
        id="bouncy",
        brave_line='"{name} hopped in a circle and chirped with a leap: '
        '\'I\'ll peck it so quickly that none can keep!\'"',
        warning_style='"{cautioner} whispered, "Fast pecks make a tumble and toss. '
        'With {food} flying about, {lost} bites may be lost."',
    ),
    "showy": Mood(
        id="showy",
        brave_line='"{name} flicked {name}\'s tail and sang with a sweep: '
        '\'Watch me peck first and the best bits I\'ll keep!\'"',
        warning_style='"{cautioner} said softly, "A showy first peck can turn into a mess. '
        'If {lost} bites go flying, then both of us get less."',
    ),
}

BIRD_NAMES = ["Pip", "Dot", "Wren", "Nip", "Tess", "Moss", "Lark", "Poppy"]


@dataclass
class StoryParams:
    setting: str
    food: str
    method: str
    mood: str
    instigator_name: str
    cautioner_name: str
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
    "seed": [
        (
            "Why do birds peck seeds?",
            "Birds use their beaks to pick up and crack small food like seeds. Pecking helps them eat tiny things from the ground."
        )
    ],
    "berry": [
        (
            "What is a berry cluster?",
            "A berry cluster is a small bunch of berries growing close together. Birds and other animals may nibble them one by one."
        )
    ],
    "bread": [
        (
            "Why can bread make crumbs?",
            "Bread breaks into tiny dry pieces when it is pecked or torn. Those little pieces are called crumbs."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets more than one person enjoy something good. It helps everyone feel included and cared for."
        )
    ],
    "fairness": [
        (
            "What does fair mean?",
            "Fair means people are treated in a balanced and honest way. In a snack, fair often means each friend gets a share."
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one friend goes, then the other goes. It helps people share without pushing or grabbing."
        )
    ],
    "patience": [
        (
            "Why does patience help when sharing?",
            "Patience helps because waiting calmly gives everyone a chance. It keeps a small problem from turning into a quarrel."
        )
    ],
}
KNOWLEDGE_ORDER = ["seed", "berry", "bread", "sharing", "fairness", "turns", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    food = f["food_cfg"]
    setting = f["setting"]
    a = f["instigator_name"]
    b = f["cautioner_name"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the word "peck" and takes place in {setting.place}.',
        f"Tell a gentle moral story in rhyme where {a} wants to peck {food.label} too quickly, but {b} learns with {a} that sharing is sweeter.",
        f"Write a happy-ending bird story in couplets about a small snack, a selfish moment, and a fair way to share.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    food = f["food_cfg"]
    method = f["method"]
    helper = f["helper"]
    a = f["instigator_name"]
    b = f["cautioner_name"]
    lost = f["lost"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little birds named {a} and {b}, and a grown {helper.label_word} who helps them share. They find a snack and learn how to be kind with it.",
        ),
        (
            f"Why did {b} warn {a} before the first big peck?",
            f"{b} warned {a} because pecking too fast would send some of the {food.label} flying away. That would waste food and leave hurt feelings too.",
        ),
        (
            f"What happened when {a} tried to peck too quickly?",
            f"{a} rushed in and some of the {food.label} scattered instead of staying where both birds could eat. The greedy choice made the snack smaller and the moment less happy.",
        ),
        (
            "How did the helper solve the problem?",
            f"The {helper.label_word} showed them a fair method and {method.qa_text}. That fixed both problems at once: less food was wasted, and both birds got to eat.",
        ),
        (
            "What is the moral of the story?",
            f"The moral is that sharing is kinder than grabbing. When {a} stopped trying to keep everything, the snack felt sweeter and the friendship felt better.",
        ),
    ]
    if lost > 0:
        qa.append(
            (
                "How do we know the greedy choice was not the best one?",
                f"We know because {lost} bites were lost when the pecking got wild. The story shows the cost clearly: rushing for more left everyone with less.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["food_cfg"].tags) | set(world.facts["method"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        food="seed_pile",
        method="two_spots",
        mood="boastful",
        instigator_name="Pip",
        cautioner_name="Dot",
    ),
    StoryParams(
        setting="orchard",
        food="berry_cluster",
        method="split_bowl",
        mood="bouncy",
        instigator_name="Wren",
        cautioner_name="Tess",
    ),
    StoryParams(
        setting="farmyard",
        food="bread_crust",
        method="take_turns",
        mood="showy",
        instigator_name="Moss",
        cautioner_name="Poppy",
    ),
]


def explain_rejection(food: Food, method: ShareMethod) -> str:
    if method.sense < SENSE_MIN or not method.fair or not method.keeps_food:
        return (
            f"(No story: method '{method.id}' is known to the world, but it is not a sensible fair fix. "
            f"A sharing story should prefer methods that keep the food and treat both birds kindly.)"
        )
    return (
        f"(No story: {method.id} does not fit {food.label}. "
        f"This food is a {food.unit_kind} item, so choose a method that can share that shape sensibly.)"
    )


def _name_pair(rng: random.Random) -> tuple[str, str]:
    names = rng.sample(BIRD_NAMES, 2)
    return names[0], names[1]


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M,S), sense_min(Min), S >= Min, fair(M), keeps_food(M).
fits(F,M) :- food(F), unit_kind(F,U), works_on(M,U), sensible_method(M).
valid(S,F,M,Mood) :- setting(S), food(F), method(M), mood(Mood), fits(F,M).

#show valid/4.
#show sensible_method/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("unit_kind", fid, food.unit_kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.fair:
            lines.append(asp.fact("fair", mid))
        if method.keeps_food:
            lines.append(asp.fact("keeps_food", mid))
        for kind in sorted(method.works_on):
            lines.append(asp.fact("works_on", mid, kind))
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bird storyworld about pecking, sharing, and a happy moral ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--instigator-name")
    ap.add_argument("--cautioner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.method:
        food = FOODS[args.food]
        method = METHODS[args.method]
        if not method_fits(food, method):
            raise StoryError(explain_rejection(food, method))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.food is None or c[1] == args.food)
        and (args.method is None or c[2] == args.method)
        and (args.mood is None or c[3] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, food_id, method_id, mood_id = rng.choice(sorted(combos))
    if args.instigator_name and args.cautioner_name:
        if args.instigator_name == args.cautioner_name:
            raise StoryError("(No story: the two birds need different names.)")
        instigator_name = args.instigator_name
        cautioner_name = args.cautioner_name
    else:
        instigator_name, cautioner_name = _name_pair(rng)
        if args.instigator_name:
            if args.instigator_name == cautioner_name:
                cautioner_name = next(n for n in BIRD_NAMES if n != args.instigator_name)
            instigator_name = args.instigator_name
        if args.cautioner_name:
            if args.cautioner_name == instigator_name:
                instigator_name = next(n for n in BIRD_NAMES if n != args.cautioner_name)
            cautioner_name = args.cautioner_name
    return StoryParams(
        setting=setting_id,
        food=food_id,
        method=method_id,
        mood=mood_id,
        instigator_name=instigator_name,
        cautioner_name=cautioner_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{params.food}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    if params.mood not in MOODS:
        raise StoryError(f"(No story: unknown mood '{params.mood}'.)")
    if params.instigator_name == params.cautioner_name:
        raise StoryError("(No story: the two birds need different names.)")
    food = FOODS[params.food]
    method = METHODS[params.method]
    if not method_fits(food, method):
        raise StoryError(explain_rejection(food, method))
    world = tell(
        setting=SETTINGS[params.setting],
        food=food,
        method=method,
        mood=MOODS[params.mood],
        instigator_name=params.instigator_name,
        cautioner_name=params.cautioner_name,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    py_methods = {m.id for m in sensible_methods()}
    asp_methods = set(asp_sensible_methods())
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_methods)} clingo={sorted(asp_methods)}")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    rng = random.Random(123)
    parser = build_parser()
    for i in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 10_000)))
            _ = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED on case {i + 1}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")
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
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (setting, food, method, mood) combos:\n")
        for setting_id, food_id, method_id, mood_id in combos:
            print(f"  {setting_id:8} {food_id:13} {method_id:10} {mood_id}")
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
            header = f"### {p.instigator_name} and {p.cautioner_name}: {p.food} at {p.setting} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
