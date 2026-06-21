#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/marmite_inner_monologue_bad_ending_sound_effects.py
==============================================================================

A standalone story world for a small folk-tale-like domain built around one
strong little thing: marmite.

In this world, a hungry child helps with a village pot in a cottage kitchen.
The child knows marmite smells powerful and thinks, in a private inner voice,
that more of it must make the meal grander. An elder warns that strong things
must be used with a light hand. If the child ignores that warning and heaps in
too much, the pot turns harsh and the supper is spoiled. Sometimes an elder can
save a nearly over-salted pot with a sensible fix, but when the child goes too
far, the ending is a bad one: bowls go untasted, the fire dies low, and the
lesson lands hard.

The model is state-driven:
- physical meters: heat, marmite level, saltiness, hunger, spoilage
- emotional memes: pride, caution, greed, shame, relief

It includes:
- a Python reasonableness gate
- an inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- trace/debug output for the simulated world
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
PRIDE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful", "obedient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    spoonable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
class Setting:
    id: str
    place: str
    season: str
    sound: str
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
class Dish:
    id: str
    label: str
    phrase: str
    vessel: str
    simmer_sound: str
    accepts_marmite: bool
    tolerance: int
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
class Portion:
    id: str
    label: str
    spoons: int
    sound: str
    thought: str
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
    power: int
    act: str
    fail: str
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


def _r_strength(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["marmite"] <= 0:
        return out
    sig = ("strength", int(pot.meters["marmite"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["saltiness"] = pot.meters["marmite"]
    if pot.meters["saltiness"] >= world.facts["dish"].tolerance + 1:
        pot.meters["harsh"] = 1.0
    if pot.meters["saltiness"] >= world.facts["dish"].tolerance + 2:
        pot.meters["ruined"] = 1.0
    return out


def _r_taste_reaction(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    child = world.get("child")
    if pot.meters["harsh"] < THRESHOLD:
        return out
    sig = ("taste_reaction", int(pot.meters["saltiness"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["shame"] += 1
    out.append("__harsh__")
    return out


def _r_ruin_hunger(world: World) -> list[str]:
    pot = world.get("pot")
    child = world.get("child")
    elder = world.get("elder")
    if pot.meters["ruined"] < THRESHOLD:
        return []
    sig = ("ruin", int(pot.meters["saltiness"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["hunger"] += 1
    elder.meters["hunger"] += 1
    child.memes["regret"] += 1
    return ["__ruined__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="strength", tag="physical", apply=_r_strength),
    Rule(name="taste_reaction", tag="emotional", apply=_r_taste_reaction),
    Rule(name="ruin_hunger", tag="physical", apply=_r_ruin_hunger),
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


def dish_works_with_marmite(dish: Dish) -> bool:
    return dish.accepts_marmite


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def is_contained(remedy: Remedy, dish: Dish, portion: Portion) -> bool:
    overflow = max(0, portion.spoons - dish.tolerance)
    return remedy.power >= overflow


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_listen(trait: str, child_age: int, elder_age: int, relation: str) -> bool:
    elder_authority = 2.0 if relation in {"grandmother", "grandfather"} else 1.0
    caution = initial_caution(trait) + elder_authority + (1.0 if elder_age - child_age >= 50 else 0.0)
    return caution > PRIDE_INIT


def predict_pot(world: World, portion_id: str) -> dict:
    sim = world.copy()
    portion = PORTIONS[portion_id]
    pot = sim.get("pot")
    pot.meters["marmite"] += portion.spoons
    propagate(sim, narrate=False)
    return {
        "harsh": pot.meters["harsh"] >= THRESHOLD,
        "ruined": pot.meters["ruined"] >= THRESHOLD,
        "saltiness": int(pot.meters["saltiness"]),
    }


def cottage_opening(world: World, child: Entity, elder: Entity, dish: Dish) -> None:
    setting = world.setting
    child.memes["hope"] += 1
    world.say(
        f"In {setting.season}, by {setting.place}, there lived a little {child.type} named {child.id} "
        f"with {child.pronoun('possessive')} {elder.label_word}. Wind went {setting.sound} at the shutters, "
        f"and in the black pot on the hearth {dish.phrase} sang {dish.simmer_sound}."
    )
    world.say(
        f"All day long the smell made {child.id}'s belly remember supper before supper had come."
    )


def task(world: World, child: Entity, elder: Entity, dish: Dish) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"Stir the {dish.label} while I fetch kindling," said {elder.label_word}. '
        f'"A steady hand makes a kind meal."'
    )


def temptation(world: World, child: Entity, elder: Entity, portion: Portion, dish: Dish) -> None:
    child.memes["greed"] += 1
    pred = predict_pot(world, portion.id)
    world.facts["predicted_harsh"] = pred["harsh"]
    world.facts["predicted_ruined"] = pred["ruined"]
    world.facts["predicted_saltiness"] = pred["saltiness"]
    jar = world.get("jar")
    world.say(
        f"Beside the spoon stood the little brown jar of marmite. {portion.sound} went the lid "
        f"when {child.id} loosened it, and the smell rose dark and deep."
    )
    thought = portion.thought.format(name=child.id, dish=dish.label)
    world.say(f'"{thought}" {child.id} thought.')
    world.say(
        f'{elder.label_word.capitalize()} glanced back from the doorway. "Only a little, child. '
        f'Strong things ask for a small spoon."'
    )
    jar.attrs["opened"] = True


def listen_turn(world: World, child: Entity, elder: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] = 0.0
    world.say(
        f"{child.id} held the spoon still. In the quiet between the crackling sticks, "
        f"{child.pronoun()} heard the warning settle inside {child.pronoun('object')} like a pebble in a shoe."
    )
    world.say(
        f'"No," {child.pronoun()} whispered to {child.pronoun("possessive")} own eager hand. '
        f'"A little is enough."'
    )


def defy(world: World, child: Entity, portion: Portion) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But hunger and pride began to argue inside {child.pronoun('object')}. "
        f'"If a little marmite is good, more must be grand," {child.id} thought.'
    )
    world.say(
        f"{portion.sound} went the spoon. {portion.sound} again. Then once more."
    )


def add_marmite(world: World, child: Entity, dish: Dish, portion: Portion) -> None:
    pot = world.get("pot")
    pot.meters["marmite"] += portion.spoons
    propagate(world, narrate=False)
    if pot.meters["harsh"] >= THRESHOLD:
        world.say(
            f"{dish.simmer_sound.capitalize()} sang the pot no longer. A sharp smell climbed up instead, "
            f"and {child.id}'s nose wrinkled before {child.pronoun('possessive')} courage could."
        )
    else:
        world.say(
            f"{dish.simmer_sound.capitalize()} went the pot, and the dark spoonful melted into the steam."
        )


def return_and_taste(world: World, child: Entity, elder: Entity, dish: Dish) -> None:
    pot = world.get("pot")
    elder.memes["care"] += 1
    world.say(
        f"Back came {elder.label_word} with the kindling. {child.id} stirred quickly, but truth has a smell of its own."
    )
    if pot.meters["harsh"] >= THRESHOLD:
        world.say(
            f'{elder.label_word.capitalize()} dipped a spoon, blew on it, and tasted. '
            f'"Oh," {elder.pronoun()} said, very softly.'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} dipped a spoon, blew on it, and nodded once. '
            f'"That is steady work," {elder.pronoun()} said.'
        )


def rescue(world: World, elder: Entity, remedy: Remedy, dish: Dish) -> None:
    pot = world.get("pot")
    overflow = max(0, int(pot.meters["marmite"] - world.facts["dish"].tolerance))
    pot.meters["saltiness"] = max(0.0, pot.meters["saltiness"] - overflow)
    pot.meters["harsh"] = 0.0
    pot.meters["ruined"] = 0.0
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["shame"] += 1
    world.say(
        f"{elder.label_word.capitalize()} did not shout. {elder.pronoun().capitalize()} {remedy.act}."
    )
    world.say(
        f"Soon the smell gentled. The spoon no longer bit the tongue, and the pot settled back to {dish.simmer_sound}."
    )


def rescue_fail(world: World, elder: Entity, remedy: Remedy, dish: Dish) -> None:
    world.say(
        f"{elder.label_word.capitalize()} tried to mend the meal and {remedy.fail}."
    )
    world.say(
        f"Still the pot answered with a fierce smell, and even the steam seemed to pull its face away."
    )


def lesson_good(world: World, child: Entity, elder: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'"Remember this," said {elder.label_word}, setting the ladle down. '
        f'"A strong thing may help a meal, but it does not wish to rule it."'
    )
    world.say(
        f"{child.id} lowered {child.pronoun('possessive')} eyes and nodded. The words stung, yet they stayed."
    )


def ending_good(world: World, child: Entity, elder: Entity, dish: Dish) -> None:
    child.meters["hunger"] = 0.0
    elder.meters["hunger"] = 0.0
    world.say(
        f"When the bowls were filled at last, the fire popped, {world.setting.sound} whispered at the shutters, "
        f"and {child.id} ate slowly, tasting care in every mouthful of {dish.label}."
    )


def ending_bad(world: World, child: Entity, elder: Entity, dish: Dish) -> None:
    child.memes["lesson"] += 1
    child.memes["shame"] += 1
    child.meters["hunger"] += 1
    elder.meters["hunger"] += 1
    world.say(
        f'"Tonight we shall not eat from this pot," said {elder.label_word}. '
        f'{child.id} looked into the black broth and wished the steam would hide {child.pronoun("possessive")} face.'
    )
    world.say(
        f"Plink went the ruined ladle against the rim. Crackle went the fire as it sank low. "
        f"Outside, the wind kept its old song, but inside the cottage there was no supper, only the long taste of regret."
    )


def tell(
    setting: Setting,
    dish: Dish,
    portion: Portion,
    remedy: Remedy,
    *,
    child_name: str = "Nell",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
    child_age: int = 7,
    elder_age: int = 67,
    relation: str = "grandmother",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={"relation": relation},
        )
    )
    world.add(
        Entity(
            id="pot",
            type="pot",
            label=dish.vessel,
            edible=True,
            attrs={"dish": dish.id},
        )
    )
    world.add(
        Entity(
            id="jar",
            type="jar",
            label="marmite jar",
            spoonable=True,
            attrs={"opened": False},
        )
    )

    child.meters["hunger"] = 1.0
    elder.meters["hunger"] = 1.0
    child.memes["pride"] = PRIDE_INIT
    child.memes["caution"] = initial_caution(trait)
    world.facts.update(
        dish=dish,
        portion=portion,
        remedy=remedy,
        setting=setting,
        relation=relation,
        child_age=child_age,
        elder_age=elder_age,
    )

    cottage_opening(world, child, elder, dish)
    task(world, child, elder, dish)

    world.para()
    temptation(world, child, elder, portion, dish)

    listens = would_listen(trait, child_age, elder_age, relation)
    if listens:
        listen_turn(world, child, elder)
        world.para()
        return_and_taste(world, child, elder, dish)
        lesson_good(world, child, elder)
        ending_good(world, child, elder, dish)
        outcome = "listened"
    else:
        defy(world, child, portion)
        add_marmite(world, child, dish, portion)

        world.para()
        return_and_taste(world, child, elder, dish)
        contained = is_contained(remedy, dish, portion)
        if contained and world.get("pot").meters["harsh"] >= THRESHOLD:
            rescue(world, elder, remedy, dish)
            lesson_good(world, child, elder)
            ending_good(world, child, elder, dish)
            outcome = "saved"
        elif contained:
            lesson_good(world, child, elder)
            ending_good(world, child, elder, dish)
            outcome = "saved"
        else:
            rescue_fail(world, elder, remedy, dish)
            ending_bad(world, child, elder, dish)
            outcome = "spoiled"

    world.facts.update(
        child=child,
        elder=elder,
        pot=world.get("pot"),
        outcome=outcome,
        served=outcome in {"listened", "saved"},
        spoiled=outcome == "spoiled",
        used_marmite=world.get("pot").meters["marmite"] > 0,
        harsh=world.get("pot").meters["harsh"] >= THRESHOLD,
        ruined=world.get("pot").meters["ruined"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "hill_cottage": Setting(
        id="hill_cottage",
        place="a hill cottage",
        season="late autumn",
        sound="whooo",
        tags={"cottage", "wind"},
    ),
    "pine_hut": Setting(
        id="pine_hut",
        place="a hut by the pines",
        season="deep winter",
        sound="hushhh",
        tags={"hut", "winter"},
    ),
    "river_house": Setting(
        id="river_house",
        place="a low house by the river",
        season="rainy spring",
        sound="tap-tap",
        tags={"river", "rain"},
    ),
}

DISHES = {
    "barley_broth": Dish(
        id="barley_broth",
        label="barley broth",
        phrase="barley broth",
        vessel="black pot",
        simmer_sound="glup glup",
        accepts_marmite=True,
        tolerance=1,
        tags={"broth", "soup"},
    ),
    "onion_soup": Dish(
        id="onion_soup",
        label="onion soup",
        phrase="onion soup",
        vessel="iron pot",
        simmer_sound="bloop bloop",
        accepts_marmite=True,
        tolerance=1,
        tags={"soup"},
    ),
    "bean_stew": Dish(
        id="bean_stew",
        label="bean stew",
        phrase="bean stew",
        vessel="heavy pot",
        simmer_sound="plup plup",
        accepts_marmite=True,
        tolerance=2,
        tags={"stew"},
    ),
    "berry_porridge": Dish(
        id="berry_porridge",
        label="berry porridge",
        phrase="sweet berry porridge",
        vessel="small pot",
        simmer_sound="puff puff",
        accepts_marmite=False,
        tolerance=0,
        tags={"porridge", "sweet"},
    ),
}

PORTIONS = {
    "dab": Portion(
        id="dab",
        label="a tiny dab",
        spoons=1,
        sound="scrape",
        thought="Just this much, and the {dish} will taste wise and rich.",
        tags={"small"},
    ),
    "spoonful": Portion(
        id="spoonful",
        label="one spoonful",
        spoons=2,
        sound="plop",
        thought="One brave spoonful will make the {dish} fit for feast day.",
        tags={"medium"},
    ),
    "heaping": Portion(
        id="heaping",
        label="a heaping spoonful",
        spoons=3,
        sound="glorp",
        thought="A heaping spoon will make the {dish} the finest in the valley.",
        tags={"large"},
    ),
}

REMEDIES = {
    "water_and_oats": Remedy(
        id="water_and_oats",
        label="water and oats",
        sense=3,
        power=2,
        act="poured in hot water, added a fist of oats, and let the pot thicken again",
        fail="poured in hot water and oats, but the harsh taste still sat on top of everything",
        qa_text="tried to thin the pot with hot water and oats",
        tags={"remedy", "water"},
    ),
    "more_beans": Remedy(
        id="more_beans",
        label="more beans",
        sense=2,
        power=1,
        act="added more beans and one ladle of water, hoping to spread the strong taste",
        fail="added more beans, but there was too much marmite for the pot to carry",
        qa_text="tried to balance the marmite by adding more beans",
        tags={"remedy", "beans"},
    ),
    "sugar": Remedy(
        id="sugar",
        label="sugar",
        sense=1,
        power=0,
        act="shook in sugar",
        fail="shook in sugar, a poor trick for a salty pot",
        qa_text="tried the poor fix of adding sugar",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Bess", "Ivy", "Tilda", "Rose"]
BOY_NAMES = ["Tom", "Bram", "Eli", "Ned", "Finn", "Ash"]
TRAITS = ["patient", "careful", "thoughtful", "bold", "eager", "proud"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for dish_id, dish in DISHES.items():
            if dish_works_with_marmite(dish):
                combos.append((setting_id, dish_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    dish: str
    portion: str
    remedy: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    child_age: int = 7
    elder_age: int = 67
    relation: str = "grandmother"
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
    "marmite": [
        (
            "What is marmite?",
            "Marmite is a very dark, salty spread made from yeast. People usually use only a little because the taste is strong.",
        )
    ],
    "broth": [
        (
            "What is broth?",
            "Broth is a thin soup made by cooking water with grains, vegetables, or meat until the flavor goes into the liquid.",
        )
    ],
    "stew": [
        (
            "What is stew?",
            "Stew is a thicker meal cooked slowly in a pot, with bits of food sitting in the liquid.",
        )
    ],
    "porridge": [
        (
            "What is porridge?",
            "Porridge is a soft hot meal made by boiling grains in water or milk until they turn thick and smooth.",
        )
    ],
    "remedy": [
        (
            "How can a cook make a soup taste less strong?",
            "A cook can sometimes add more plain ingredients and more liquid, so the strong taste spreads out. But if too much strong flavor went in at first, the soup may still be spoiled.",
        )
    ],
    "wind": [
        (
            "Why do folk tales use sounds like whooo and crackle?",
            "Those little sound words help you hear the place in your head. They make the story feel close, like you are standing by the fire too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["marmite", "broth", "stew", "porridge", "remedy", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dish = f["dish"]
    portion = f["portion"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk-tale-style story for a 3-to-5-year-old that includes the word "marmite", '
        f'uses inner monologue and sound effects, and centers on a child stirring {dish.label} in a cottage.'
    )
    if outcome == "spoiled":
        return [
            base,
            f"Tell a cautionary tale where {child.id} secretly adds {portion.label} of marmite to {dish.label}, and the ending is sad because the supper is spoiled.",
            'Write a folk tale with sound effects like "crackle" or "plop" where a child thinks greedy thoughts about marmite and learns too late that more is not always better.',
        ]
    return [
        base,
        f"Tell a gentle folk tale where {child.id} is tempted to add too much marmite to {dish.label}, but the warning is heard in time or the elder saves the pot.",
        'Write a simple old-fashioned kitchen story with inner monologue, a strong-tasting ingredient, and a lesson about using only a little.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    dish = f["dish"]
    portion = f["portion"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type} helping {child.pronoun('possessive')} {elder.label_word} with a pot of {dish.label}. The story stays close to {child.id}'s thoughts as the choice grows harder.",
        ),
        (
            "What tempted the child?",
            f"The child was hungry, proud, and standing beside a jar of marmite while the pot simmered. That made {child.pronoun('object')} think that one strong spoonful might make the whole meal grander.",
        ),
        (
            "What warning did the elder give?",
            f"{elder.label_word.capitalize()} warned that strong things need only a little. The warning matters because marmite can quickly make a pot too salty.",
        ),
    ]
    if outcome == "listened":
        qa.append(
            (
                f"Why did {child.id} stop?",
                f"{child.id} heard the warning and pulled {child.pronoun('possessive')} hand back before adding too much. The moment changed the story because caution became stronger than pride.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The meal was served, and the bowls were good to eat. The ending shows that careful listening kept the cottage warm and the supper whole.",
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                "How was the pot saved?",
                f"{elder.label_word.capitalize()} {remedy.qa_text}. That worked because the mistake had not gone too far, so the strong taste could still be spread out.",
            )
        )
        qa.append(
            (
                f"How did {child.id} feel afterward?",
                f"{child.id} felt ashamed but relieved. The lesson stayed because the elder fixed the pot without shouting, which made the mistake easier to remember honestly.",
            )
        )
    else:
        qa.append(
            (
                "Why was the supper ruined?",
                f"The child put in {portion.label} of marmite, and the taste grew too strong for the pot to carry. Even after the elder tried to mend it, the soup stayed harsh, so nobody could eat from it.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly: the supper was not served, the fire sank low, and the cottage felt full of regret. That ending proves the child's choice changed a warm meal into a hungry night.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"marmite", "wind"}
    dish = f["dish"]
    if "broth" in dish.tags or "soup" in dish.tags:
        tags.add("broth")
    if "stew" in dish.tags:
        tags.add("stew")
    if "porridge" in dish.tags:
        tags.add("porridge")
    if f["outcome"] in {"saved", "spoiled"}:
        tags.add("remedy")
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
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hill_cottage",
        dish="barley_broth",
        portion="heaping",
        remedy="more_beans",
        child_name="Nell",
        child_gender="girl",
        elder_type="grandmother",
        trait="bold",
        child_age=7,
        elder_age=67,
        relation="grandmother",
    ),
    StoryParams(
        setting="pine_hut",
        dish="bean_stew",
        portion="spoonful",
        remedy="water_and_oats",
        child_name="Bram",
        child_gender="boy",
        elder_type="grandfather",
        trait="eager",
        child_age=8,
        elder_age=70,
        relation="grandfather",
    ),
    StoryParams(
        setting="river_house",
        dish="onion_soup",
        portion="dab",
        remedy="water_and_oats",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        trait="patient",
        child_age=6,
        elder_age=68,
        relation="grandmother",
    ),
]


def explain_rejection(dish: Dish) -> str:
    if not dish.accepts_marmite:
        return (
            f"(No story: {dish.label} is sweet, and marmite would not be a reasonable flavor for it here. "
            f"Pick a savory pot such as barley_broth, onion_soup, or bean_stew.)"
        )
    return "(No story: this dish does not make a reasonable marmite tale.)"


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    listens = would_listen(params.trait, params.child_age, params.elder_age, params.relation)
    if listens:
        return "listened"
    if is_contained(REMEDIES[params.remedy], DISHES[params.dish], PORTIONS[params.portion]):
        return "saved"
    return "spoiled"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
valid(S, D) :- setting(S), dish(D), savory(D).
sensible(R) :- remedy(R), sense(R, N), sense_min(M), N >= M.

% --- outcome model ----------------------------------------------------------
init_caution(5) :- trait(T), cautious_trait(T).
init_caution(3) :- trait(T), not cautious_trait(T).

elder_bonus(2) :- relation(grandmother).
elder_bonus(2) :- relation(grandfather).
elder_bonus(1) :- relation(mother).
elder_bonus(1) :- relation(father).

long_gap_bonus(1) :- child_age(C), elder_age(E), E - C >= 50.
long_gap_bonus(0) :- child_age(C), elder_age(E), E - C < 50.

authority(C + EB + LB) :- init_caution(C), elder_bonus(EB), long_gap_bonus(LB).
listened :- authority(A), pride_init(P), A > P.

overflow(Ps - T) :- chosen_portion(P), spoons(P, Ps), chosen_dish(D), tolerance(D, T), Ps > T.
overflow(0) :- chosen_portion(P), spoons(P, Ps), chosen_dish(D), tolerance(D, T), Ps <= T.

contained :- chosen_remedy(R), power(R, Pow), overflow(O), Pow >= O.

outcome(listened) :- listened.
outcome(saved) :- not listened, contained.
outcome(spoiled) :- not listened, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, dish in DISHES.items():
        lines.append(asp.fact("dish", did))
        if dish.accepts_marmite:
            lines.append(asp.fact("savory", did))
        lines.append(asp.fact("tolerance", did, dish.tolerance))
    for pid, portion in PORTIONS.items():
        lines.append(asp.fact("portion", pid))
        lines.append(asp.fact("spoons", pid, portion.spoons))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_dish", params.dish),
            asp.fact("chosen_portion", params.portion),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("trait", params.trait),
            asp.fact("child_age", params.child_age),
            asp.fact("elder_age", params.elder_age),
            asp.fact("relation", params.relation),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_remedies()}
    if c_sens == p_sens:
        print(f"OK: sensible remedies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, marmite, a private thought, and a lesson from a cottage pot."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--portion", choices=PORTIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dish and not dish_works_with_marmite(DISHES[args.dish]):
        raise StoryError(explain_rejection(DISHES[args.dish]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.dish is None or combo[1] == args.dish)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, dish_id = rng.choice(sorted(combos))
    portion_id = args.portion or rng.choice(sorted(PORTIONS))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    relation = elder_type
    child_age = rng.choice([5, 6, 7, 8])
    elder_age = {
        "grandmother": rng.choice([62, 67, 71]),
        "grandfather": rng.choice([64, 69, 73]),
        "mother": rng.choice([31, 35, 39]),
        "father": rng.choice([33, 37, 41]),
    }[elder_type]

    return StoryParams(
        setting=setting_id,
        dish=dish_id,
        portion=portion_id,
        remedy=remedy_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
        trait=trait,
        child_age=child_age,
        elder_age=elder_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish '{params.dish}'.)")
    if params.portion not in PORTIONS:
        raise StoryError(f"(Unknown portion '{params.portion}'.)")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy '{params.remedy}'.)")
    if not dish_works_with_marmite(DISHES[params.dish]):
        raise StoryError(explain_rejection(DISHES[params.dish]))
    if REMEDIES[params.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))
    if params.elder_type not in {"grandmother", "grandfather", "mother", "father"}:
        raise StoryError(f"(Unknown elder '{params.elder_type}'.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender '{params.child_gender}'.)")

    world = tell(
        SETTINGS[params.setting],
        DISHES[params.dish],
        PORTIONS[params.portion],
        REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        child_age=params.child_age,
        elder_age=params.elder_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, dish) combos:\n")
        for setting_id, dish_id in combos:
            print(f"  {setting_id:12} {dish_id}")
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
            header = f"### {p.child_name}: {p.dish} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
