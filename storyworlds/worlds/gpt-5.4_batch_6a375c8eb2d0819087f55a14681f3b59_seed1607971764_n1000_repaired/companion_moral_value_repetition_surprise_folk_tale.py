#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py
================================================================================

A standalone storyworld for a small folk-tale domain about a traveler, a small
companion, three repeated chances to be kind, and a surprising ending.

The seed asked for:
- the word "companion"
- Moral Value
- Repetition
- Surprise
- a Folk Tale style

So this world models a child walking to an elder's cottage with a basket of food
and a little animal companion. Three hungry strangers appear along the road and
ask the same small favor. The child may share or refuse according to the chosen
heart. If kindness is repeated all three times, the companion reveals a hidden,
magical nature and the basket is filled again. If kindness is partial, the elder
still teaches the lesson in a gentle, grounded way. If kindness is refused
entirely, the ending stays safe but feels hollow.

Run it
------
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py --road pine_path --companion sparrow --heart hesitant
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py --food plum_tart --heart generous
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/companion_moral_value_repetition_surprise_folk_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    plural: bool = False
    can_speak: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Domain config
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Road:
    id: str
    place: str
    opening: str
    first_image: str
    cottage_image: str
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
class CompanionCfg:
    id: str
    type: str
    label: str
    phrase: str
    move: str
    nudge: str
    reveal: str
    reveal_action: str
    suited_roads: set[str] = field(default_factory=set)
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
class Food:
    id: str
    label: str
    phrase: str
    unit: str
    portions: int
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
class Heart:
    id: str
    pattern: tuple[bool, bool, bool]
    need: int
    description: str
    line: str
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
class EncounterCfg:
    id: str
    who: str
    title: str
    request: str


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "shares": [],
            "refusals": [],
            "encounters": [],
            "surprise": False,
            "outcome": "",
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_shared_portion(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "asker" or ent.meters["fed"] < THRESHOLD:
            continue
        sig = ("shared", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero = world.get("hero")
        companion = world.get("companion")
        hero.memes["kindness"] += 1
        hero.memes["worry"] += 1
        companion.memes["trust"] += 1
        out.append("__kindness__")
    return out


def _r_refusal_sadness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "asker" or ent.meters["refused"] < THRESHOLD:
            continue
        sig = ("refused", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero = world.get("hero")
        companion = world.get("companion")
        hero.memes["hardness"] += 1
        companion.memes["sadness"] += 1
        out.append("__refusal__")
    return out


def _r_threefold_blessing(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["kindness"] < 3:
        return []
    sig = ("blessing_ready", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["blessing_ready"] = True
    return ["__blessing__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="shared_portion", tag="moral", apply=_r_shared_portion),
    Rule(name="refusal_sadness", tag="moral", apply=_r_refusal_sadness),
    Rule(name="threefold_blessing", tag="folk_magic", apply=_r_threefold_blessing),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def road_suits_companion(road_id: str, companion_id: str) -> bool:
    return road_id in COMPANIONS[companion_id].suited_roads


def enough_portions(food_id: str, heart_id: str) -> bool:
    return FOODS[food_id].portions >= HEARTS[heart_id].need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for road_id in ROADS:
        for companion_id in COMPANIONS:
            if not road_suits_companion(road_id, companion_id):
                continue
            for food_id in FOODS:
                for heart_id in HEARTS:
                    if enough_portions(food_id, heart_id):
                        combos.append((road_id, companion_id, food_id, heart_id))
    return combos


def explain_rejection(road_id: str, companion_id: str, food_id: str, heart_id: str) -> str:
    if road_id and companion_id and not road_suits_companion(road_id, companion_id):
        road = ROADS[road_id]
        companion = COMPANIONS[companion_id]
        return (
            f"(No story: {companion.phrase} is not a good traveler for {road.place}. "
            f"This little tale only sends that companion along roads it could plausibly travel.)"
        )
    if food_id and heart_id and not enough_portions(food_id, heart_id):
        food = FOODS[food_id]
        heart = HEARTS[heart_id]
        return (
            f"(No story: {food.phrase} has only {food.portions} shareable portion"
            f"{'' if food.portions == 1 else 's'}, but a {heart.description} child would need "
            f"{heart.need} for the repeated asking on this road.)"
        )
    return "(No story: that combination does not fit this folk-tale world.)"


def outcome_from_params(params: "StoryParams") -> str:
    shares = sum(1 for x in HEARTS[params.heart].pattern if x)
    if shares >= 3:
        return "miracle"
    if shares >= 1:
        return "modest"
    return "hollow"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_sharing(world: World, heart: Heart) -> dict:
    sim = world.copy()
    basket = sim.get("basket")
    shares = 0
    for will_share in heart.pattern:
        if will_share and basket.meters["portions_left"] >= THRESHOLD:
            basket.meters["portions_left"] -= 1
            shares += 1
    return {
        "shares": shares,
        "portions_left": int(basket.meters["portions_left"]),
        "miracle": shares >= 3,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def opening(world: World, road: Road, hero: Entity, elder: Entity, food: Food, companion: CompanionCfg) -> None:
    basket = world.get("basket")
    hero.memes["duty"] += 1
    hero.memes["love"] += 1
    world.say(
        f"In the old days, when small roads were said to listen, {hero.id} set out along "
        f"{road.place} with a basket holding {food.phrase} for {hero.pronoun('possessive')} "
        f"{elder.label_word}."
    )
    world.say(
        f"{road.opening} At {hero.pronoun('possessive')} heels went {companion.phrase}, "
        f"a faithful companion that {companion.move} beside the basket."
    )
    world.say(road.first_image)
    basket.meters["portions_left"] = float(food.portions)
    basket.attrs["food_label"] = food.label
    basket.attrs["food_unit"] = food.unit
    basket.attrs["food_plural"] = food.plural


def elder_need(world: World, elder: Entity, food: Food) -> None:
    world.say(
        f"{elder.label_word.capitalize()} was waiting for supper, and {hero.id} knew the little gift "
        f"would matter before nightfall."
    )
    world.say(
        f"That is why {hero.pronoun()} walked carefully and counted the {food.unit}"
        f"{'' if food.portions == 1 else 's'} in {hero.pronoun('possessive')} mind."
    )


def foresee(world: World, hero: Entity, heart: Heart) -> None:
    pred = predict_sharing(world, heart)
    world.facts["predicted_shares"] = pred["shares"]
    world.facts["predicted_left"] = pred["portions_left"]
    world.say(
        f"{hero.id} had a {heart.description} heart. {heart.line}"
    )
    if pred["shares"] >= 3:
        world.say(
            f"If {hero.pronoun()} shared every time a hand was held out, the basket would be empty "
            f"before the cottage gate."
        )
    elif pred["shares"] >= 1:
        world.say(
            f"{hero.pronoun().capitalize()} did not think {hero.pronoun()} would share with everyone, "
            f"only once the road had taught a lesson."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} meant to guard every bite and let no one touch the basket."
        )


def ask(world: World, encounter: EncounterCfg) -> None:
    asker = world.get(encounter.id)
    asker.meters["hungry"] = 1.0
    world.say(
        f"Before long, {encounter.who} stood by the road. "
        f'"Traveler," {encounter.title} asked, "{encounter.request}"'
    )
    world.facts["encounters"].append(encounter.id)


def share(world: World, hero: Entity, companion: Entity, encounter: EncounterCfg, food: Food) -> None:
    asker = world.get(encounter.id)
    basket = world.get("basket")
    if basket.meters["portions_left"] < THRESHOLD:
        raise StoryError("(Story bug: tried to share from an empty basket.)")
    basket.meters["portions_left"] -= 1
    asker.meters["hungry"] = 0.0
    asker.meters["fed"] = 1.0
    world.facts["shares"].append(encounter.id)
    propagate(world, narrate=False)
    left = int(basket.meters["portions_left"])
    world.say(
        f"{hero.id} broke off {food.unit if not food.plural else 'one ' + food.unit[:-1] if food.unit.endswith('s') else 'one ' + food.unit} "
        f"and placed it in the waiting hands."
    )
    world.say(
        f'{companion.id.capitalize()} {companion.attrs["nudge_past"]}, and the road seemed quieter after that. '
        f"There were {left} portion{'s' if left != 1 else ''} left in the basket."
    )


def refuse(world: World, hero: Entity, companion: Entity, encounter: EncounterCfg) -> None:
    asker = world.get(encounter.id)
    asker.meters["refused"] = 1.0
    world.facts["refusals"].append(encounter.id)
    propagate(world, narrate=False)
    world.say(
        f'"No," said {hero.id}, holding the basket close. "These are promised elsewhere."'
    )
    world.say(
        f'{companion.id.capitalize()} {companion.attrs["sad_past"]}, and even the leaves seemed to hush.'
    )


def repeated_walk(world: World, hero: Entity, companion: Entity, food: Food, heart: Heart) -> None:
    for idx, encounter in enumerate(ENCOUNTERS):
        ask(world, encounter)
        if heart.pattern[idx]:
            if heart.id == "hesitant":
                world.say(
                    f'{companion.id.capitalize()} {companion.attrs["nudge_present"]} against {hero.pronoun("possessive")} ankle as if to say, '
                    f'"A small gift is still a gift."'
                )
                world.say(
                    f"{hero.id} looked at the basket, looked at the hungry face, and sighed."
                )
            elif heart.id == "mixed" and idx < 2:
                world.say(
                    f'{hero.id} almost turned away, but {companion.id} would not leave the poor stranger alone with those sharp hungry eyes.'
                )
            share(world, hero, companion, encounter, food)
        else:
            refuse(world, hero, companion, encounter)
        if idx < 2:
            world.say("Then the road bent onward, and the same test came again in a different coat.")


def arrival(world: World, road: Road, hero: Entity, elder: Entity) -> None:
    basket = world.get("basket")
    left = int(basket.meters["portions_left"])
    world.say(
        f"At last {hero.id} came to {elder.label_word}'s cottage, where {road.cottage_image}"
    )
    if left == 0:
        world.say(
            f"The basket was light as a leaf, and {hero.id} felt the truth of that lightness in {hero.pronoun('possessive')} chest."
        )
    else:
        world.say(
            f"There were still {left} portion{'s' if left != 1 else ''} in the basket, yet {hero.id} felt heavier than when the walk began."
        )


def miracle_ending(world: World, hero: Entity, companion: Entity, elder: Entity, food: Food, road: Road) -> None:
    basket = world.get("basket")
    hero.memes["wonder"] += 1
    hero.memes["relief"] += 1
    companion.can_speak = True
    basket.meters["portions_left"] = float(food.portions + 3)
    world.facts["surprise"] = True
    world.facts["outcome"] = "miracle"
    world.say(
        f"Before {hero.id} could speak, {companion.id} {companion.attrs['reveal_action']} and for the first time said words in a clear small voice."
    )
    world.say(
        f'"{companion.attrs["reveal_line"]}"'
    )
    world.say(
        f"Then, to {hero.id}'s amazement, the basket grew warm. When {hero.pronoun()} lifted the cloth, "
        f"there lay {food.phrase} again, more than at morning."
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled as if old tales had come true once more. "
        f'"A kindness given three times never walks home alone," {elder.pronoun()} said.'
    )
    world.say(
        f"That evening they ate with grateful hearts, and the lamp in the cottage seemed to shine on "
        f"{road.place} itself."
    )


def modest_ending(world: World, hero: Entity, companion: Entity, elder: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.facts["outcome"] = "modest"
    left = int(world.get("basket").meters["portions_left"])
    world.say(
        f"{elder.label_word.capitalize()} listened to the whole journey and set a simple pot of soup between them."
    )
    world.say(
        f'"You kept some and gave some," {elder.pronoun()} said. "That is a beginning, but a full heart does not count kindness on one finger alone."'
    )
    if left > 0:
        world.say(
            f"{hero.id} set the remaining food on the table without hiding it. {companion.id.capitalize()} curled close, and the meal tasted warmer for the part that had been shared."
        )
    else:
        world.say(
            f"Though the basket was empty, the room did not feel poor. {companion.id.capitalize()} settled by the fire, and {hero.id} knew one brave gift had changed the taste of supper."
        )


def hollow_ending(world: World, hero: Entity, companion: Entity, elder: Entity) -> None:
    hero.memes["lesson"] += 1
    world.facts["outcome"] = "hollow"
    world.say(
        f"{elder.label_word.capitalize()} thanked {hero.id} for bringing the basket, but {elder.pronoun()} looked long at the little companion and then at the road behind them."
    )
    world.say(
        f'"Food can fill a stomach," {elder.pronoun()} said softly, "yet a closed hand leaves the room hungry in another way."'
    )
    world.say(
        f"{hero.id} ate, but every bite seemed smaller than it had in the morning. Beside the hearth, "
        f"{companion.id} lay quiet, and {hero.pronoun()} wished the road had been walked more wisely."
    )


def tell(
    road: Road,
    companion_cfg: CompanionCfg,
    food: Food,
    heart: Heart,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    companion = world.add(
        Entity(
            id=companion_cfg.label,
            kind="character",
            type=companion_cfg.type,
            label=companion_cfg.label,
            phrase=companion_cfg.phrase,
            role="companion",
            attrs={
                "nudge_present": companion_cfg.nudge,
                "nudge_past": {
                    "sparrow": "gave a pleased little chirrup",
                    "dog": "thumped its tail against the dust",
                    "tortoise": "blinked as if it had expected no less",
                }[companion_cfg.id],
                "sad_past": {
                    "sparrow": "gave one small disappointed flutter",
                    "dog": "let out a low unhappy sigh",
                    "tortoise": "drew its head in for a breath",
                }[companion_cfg.id],
                "reveal_line": companion_cfg.reveal,
                "reveal_action": companion_cfg.reveal_action,
            },
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label="basket",
            phrase=f"a basket of {food.label}",
            role="basket",
            plural=False,
        )
    )

    for encounter in ENCOUNTERS:
        world.add(
            Entity(
                id=encounter.id,
                kind="character",
                type="person",
                label=encounter.who,
                role="asker",
                attrs={"title": encounter.title},
            )
        )

    world.facts.update(
        road=road,
        companion_cfg=companion_cfg,
        food=food,
        heart=heart,
        hero=hero,
        elder=elder,
    )
    world.facts["blessing_ready"] = False

    opening(world, road, hero, elder, food, companion_cfg)
    elder_need(world, elder, food)

    world.para()
    foresee(world, hero, heart)
    repeated_walk(world, hero, companion, food, heart)

    world.para()
    arrival(world, road, hero, elder)
    if hero.memes["kindness"] >= 3:
        miracle_ending(world, hero, companion, elder, food, road)
    elif hero.memes["kindness"] >= 1:
        modest_ending(world, hero, companion, elder)
    else:
        hollow_ending(world, hero, companion, elder)

    world.facts.update(
        share_count=int(hero.memes["kindness"]),
        refusal_count=len(world.facts["refusals"]),
        portions_left=int(world.get("basket").meters["portions_left"]),
        companion_spoke=companion.can_speak,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROADS = {
    "pine_path": Road(
        id="pine_path",
        place="the pine path",
        opening="The pines whispered over the narrow track, and the needles made a soft brown carpet.",
        first_image="A cool smell of sap followed every step.",
        cottage_image="blue smoke was curling from the crooked chimney",
        tags={"forest", "path"},
    ),
    "river_lane": Road(
        id="river_lane",
        place="the river lane",
        opening="The river ran beside the lane like a strip of moving glass.",
        first_image="Reeds bowed and straightened as if they too were greeting travelers.",
        cottage_image="the window was bright with the last silver of the river light",
        tags={"river", "lane"},
    ),
    "stone_way": Road(
        id="stone_way",
        place="the stone way",
        opening="Flat warm stones led over the hill where larks sang above the fields.",
        first_image="The far roofs looked like toys beneath the sky.",
        cottage_image="the door stood open to the amber evening",
        tags={"hill", "stones"},
    ),
}

COMPANIONS = {
    "sparrow": CompanionCfg(
        id="sparrow",
        type="bird",
        label="Pip",
        phrase="a brown sparrow no bigger than a mitten",
        move="hopped and fluttered",
        nudge="fluttered up to the basket handle",
        reveal="Kindness flies farther than crumbs.",
        reveal_action="fluttered to the basket rim, bright-eyed and solemn",
        suited_roads={"pine_path", "river_lane", "stone_way"},
        tags={"bird", "companion"},
    ),
    "dog": CompanionCfg(
        id="dog",
        type="dog",
        label="Moss",
        phrase="a little moss-colored dog with wise ears",
        move="trotted",
        nudge="pressed its nose",
        reveal="A road remembers the hand that opens.",
        reveal_action="stood straight, ears high, as old as a tale",
        suited_roads={"pine_path", "river_lane", "stone_way"},
        tags={"dog", "companion"},
    ),
    "tortoise": CompanionCfg(
        id="tortoise",
        type="tortoise",
        label="Shell",
        phrase="a slow green tortoise with bright patient eyes",
        move="plodded",
        nudge="tapped its shell lightly",
        reveal="Slow kindness still arrives before night.",
        reveal_action="lifted its head and shone as if polished by moonlight",
        suited_roads={"pine_path", "river_lane"},
        tags={"tortoise", "companion"},
    ),
}

FOODS = {
    "oat_cakes": Food(
        id="oat_cakes",
        label="oat cakes",
        phrase="three round oat cakes",
        unit="cakes",
        portions=3,
        plural=True,
        tags={"food", "cakes"},
    ),
    "pears": Food(
        id="pears",
        label="pears",
        phrase="three golden pears",
        unit="pears",
        portions=3,
        plural=True,
        tags={"food", "fruit"},
    ),
    "chestnuts": Food(
        id="chestnuts",
        label="chestnuts",
        phrase="six roasted chestnuts wrapped in cloth",
        unit="chestnuts",
        portions=6,
        plural=True,
        tags={"food", "nuts"},
    ),
    "plum_tart": Food(
        id="plum_tart",
        label="plum tart",
        phrase="one small plum tart",
        unit="tart",
        portions=1,
        plural=False,
        tags={"food", "tart"},
    ),
}

HEARTS = {
    "generous": Heart(
        id="generous",
        pattern=(True, True, True),
        need=3,
        description="generous",
        line="Again and again, kindness pulled at the sleeve of duty.",
        tags={"kindness", "moral"},
    ),
    "hesitant": Heart(
        id="hesitant",
        pattern=(True, True, True),
        need=3,
        description="hesitant",
        line="Kindness lived there too, though it had to be called out each time.",
        tags={"kindness", "moral"},
    ),
    "mixed": Heart(
        id="mixed",
        pattern=(False, False, True),
        need=1,
        description="mixed-up",
        line="One thought said keep everything, and another said a road is not walked alone.",
        tags={"lesson", "moral"},
    ),
    "proud": Heart(
        id="proud",
        pattern=(False, False, False),
        need=0,
        description="proud",
        line="It is easy for pride to mistake keeping for wisdom.",
        tags={"lesson", "moral"},
    ),
}

ENCOUNTERS = [
    EncounterCfg(
        id="asker1",
        who="an old woman with a bundle of sticks",
        title="the old woman",
        request="Will you spare one small bite for the road?",
    ),
    EncounterCfg(
        id="asker2",
        who="a tired mason with dust on his sleeves",
        title="the mason",
        request="Will you spare one small bite for the road?",
    ),
    EncounterCfg(
        id="asker3",
        who="a child with wind-red cheeks",
        title="the child",
        request="Will you spare one small bite for the road?",
    ),
]

GIRL_NAMES = ["Mira", "Anya", "Lina", "Talia", "Iris", "Nella", "Suri", "Elin"]
BOY_NAMES = ["Toma", "Milo", "Nico", "Pavel", "Luka", "Ari", "Ivo", "Stefan"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    road: str
    companion: str
    food: str
    heart: str
    hero_name: str
    hero_gender: str
    elder_type: str = "grandmother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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
    "companion": [
        (
            "What is a companion?",
            "A companion is someone, or sometimes an animal, who goes with you and stays by your side. A good companion can help you make better choices."
        )
    ],
    "kindness": [
        (
            "Why is sharing a kind thing to do?",
            "Sharing means you notice that another person has a need and you choose to help. Even a small gift can make someone feel seen and cared for."
        )
    ],
    "repetition": [
        (
            "Why do folk tales often repeat something three times?",
            "Repeating something three times helps listeners remember the story and notice the pattern. It also makes the last turn feel important when something finally changes."
        )
    ],
    "surprise": [
        (
            "What is a surprise ending in a story?",
            "A surprise ending is when something unexpected happens near the end, but it still fits the story. It makes readers look back and see earlier clues in a new way."
        )
    ],
    "bird": [
        (
            "What does a sparrow do?",
            "A sparrow is a small bird that hops, flutters, and chirps. In stories, a tiny bird can seem small but still notice important things."
        )
    ],
    "dog": [
        (
            "Why are dogs often good companions in stories?",
            "Dogs stay close, pay attention, and show their feelings clearly. That makes them good story companions when a character needs loyalty or a gentle nudge."
        )
    ],
    "tortoise": [
        (
            "Why can a tortoise fit a folk tale?",
            "A tortoise moves slowly, so it can stand for patience and steady wisdom. Folk tales often give quiet, slow creatures an important truth to carry."
        )
    ],
    "food": [
        (
            "Why does food matter in stories about kindness?",
            "Food is something people truly need, so sharing it can cost you something real. That makes a kind choice feel honest and important."
        )
    ],
}
KNOWLEDGE_ORDER = ["companion", "kindness", "repetition", "surprise", "bird", "dog", "tortoise", "food"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion_cfg = f["companion_cfg"]
    road = f["road"]
    food = f["food"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "companion" and follows a child walking along {road.place} with {companion_cfg.phrase}.',
        f"Tell a simple story where {hero.label} carries {food.phrase}, faces the same small test three times, and learns what kind hands bring back.",
        "Write a gentle moral tale with repetition, a surprising ending, and a small animal companion who helps reveal the lesson.",
    ]
    if outcome == "miracle":
        prompts.append(
            "Make the ending surprising but kind: after the child shares three times, the little companion speaks and the loss turns into abundance."
        )
    elif outcome == "modest":
        prompts.append(
            "Use a warm folk-tale tone where the child is only partly generous, so the ending brings a lesson instead of magic."
        )
    else:
        prompts.append(
            "Use a calm cautionary ending where the child keeps everything, reaches home safely, but learns that closed hands make a room feel poor."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    companion_cfg = f["companion_cfg"]
    food = f["food"]
    share_count = f["share_count"]
    refusal_count = f["refusal_count"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child walking to {hero.pronoun('possessive')} {elder.label_word}'s cottage with {companion_cfg.phrase} as a companion."
        ),
        (
            "What happened three times on the road?",
            "Three different hungry strangers asked for the same small bite for the road. The repeated asking is the pattern that tested the child's heart again and again."
        ),
        (
            f"Why did {hero.label} worry about sharing the food?",
            f"{hero.label} was carrying {food.phrase} for {elder.label_word}, so every portion seemed important. Sharing meant risking that the basket might be empty by the time the cottage was reached."
        ),
    ]
    if share_count >= 3:
        qa.append(
            (
                f"Why did the basket fill again at the end?",
                f"It filled again after {hero.label} shared all three times, so the story treats repeated kindness as the key that opened the wonder. The surprise came through the small companion, who finally spoke and revealed that kindness would not return empty."
            )
        )
        qa.append(
            (
                "What was the surprise in the story?",
                f"The surprise was that the little companion was more than an ordinary animal. At the cottage it spoke aloud, and right after that the basket became full again."
            )
        )
    elif share_count >= 1:
        qa.append(
            (
                f"Did {hero.label} learn anything even without a miracle?",
                f"Yes. {hero.label} learned that one kind act warms a meal, but kindness grows stronger when it is repeated and not rationed too tightly. {elder.label_word.capitalize()} explained the lesson at supper, so the change happened inside the child instead of in the basket."
            )
        )
    else:
        qa.append(
            (
                f"Why did the ending feel sad even though {hero.label} arrived safely?",
                f"{hero.label} kept all the food, so the body of the trip was safe but the heart of it stayed shut. {elder.label_word.capitalize()} pointed out that a closed hand can leave a room hungry in another way."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            "The story says that kindness should be practiced, not just admired from far away. When care is given again and again, it changes both the road behind you and the home you reach."
        )
    )
    if refusal_count:
        qa.append(
            (
                "How did the companion react when kindness was refused?",
                f"The companion grew quiet and sad whenever a hungry stranger was turned away. That reaction mattered because it showed the child, step by step, that the road itself felt different after a hard choice."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"companion", "kindness", "repetition", "surprise", "food"}
    companion_id = world.facts["companion_cfg"].id
    if companion_id == "sparrow":
        tags.add("bird")
    elif companion_id == "dog":
        tags.add("dog")
    elif companion_id == "tortoise":
        tags.add("tortoise")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.can_speak:
            bits.append("can_speak=True")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: share_count={world.facts.get('share_count')} outcome={world.facts.get('outcome')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(R,C,F,H) :- road(R), companion(C), food(F), heart(H),
                  suited(C,R), portions(F,P), need(H,N), P >= N.

share_count(H,S) :- shares(H,S).

outcome(miracle) :- chosen_heart(H), share_count(H,S), S >= 3.
outcome(modest)  :- chosen_heart(H), share_count(H,S), S >= 1, S < 3.
outcome(hollow)  :- chosen_heart(H), share_count(H,0).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for road_id in ROADS:
        lines.append(asp.fact("road", road_id))
    for cid, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        for rid in sorted(companion.suited_roads):
            lines.append(asp.fact("suited", cid, rid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("portions", fid, food.portions))
    for hid, heart in HEARTS.items():
        lines.append(asp.fact("heart", hid))
        lines.append(asp.fact("need", hid, heart.need))
        lines.append(asp.fact("shares", hid, sum(1 for x in heart.pattern if x)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_heart", params.heart)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_from_params(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        road="pine_path",
        companion="sparrow",
        food="oat_cakes",
        heart="generous",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        road="river_lane",
        companion="dog",
        food="pears",
        heart="hesitant",
        hero_name="Milo",
        hero_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        road="stone_way",
        companion="dog",
        food="chestnuts",
        heart="mixed",
        hero_name="Talia",
        hero_gender="girl",
        elder_type="grandfather",
    ),
    StoryParams(
        road="pine_path",
        companion="tortoise",
        food="plum_tart",
        heart="proud",
        hero_name="Ivo",
        hero_gender="boy",
        elder_type="grandmother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a child, a companion, three repeated chances to be kind, and a surprising ending."
    )
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--heart", choices=HEARTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="verify Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the generated ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.road and args.companion and not road_suits_companion(args.road, args.companion):
        raise StoryError(explain_rejection(args.road, args.companion, args.food or "oat_cakes", args.heart or "mixed"))
    if args.food and args.heart and not enough_portions(args.food, args.heart):
        raise StoryError(explain_rejection(args.road or "pine_path", args.companion or "sparrow", args.food, args.heart))

    combos = [
        combo
        for combo in valid_combos()
        if (args.road is None or combo[0] == args.road)
        and (args.companion is None or combo[1] == args.companion)
        and (args.food is None or combo[2] == args.food)
        and (args.heart is None or combo[3] == args.heart)
    ]
    if not combos:
        road_id = args.road or "pine_path"
        companion_id = args.companion or "sparrow"
        food_id = args.food or "oat_cakes"
        heart_id = args.heart or "mixed"
        raise StoryError(explain_rejection(road_id, companion_id, food_id, heart_id))

    road_id, companion_id, food_id, heart_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        road=road_id,
        companion=companion_id,
        food=food_id,
        heart=heart_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS:
        raise StoryError(f"(No story: unknown road '{params.road}'.)")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(No story: unknown companion '{params.companion}'.)")
    if params.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{params.food}'.)")
    if params.heart not in HEARTS:
        raise StoryError(f"(No story: unknown heart '{params.heart}'.)")
    if not road_suits_companion(params.road, params.companion):
        raise StoryError(explain_rejection(params.road, params.companion, params.food, params.heart))
    if not enough_portions(params.food, params.heart):
        raise StoryError(explain_rejection(params.road, params.companion, params.food, params.heart))

    world = tell(
        ROADS[params.road],
        COMPANIONS[params.companion],
        FOODS[params.food],
        HEARTS[params.heart],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} valid (road, companion, food, heart) combinations:\n")
        for road_id, companion_id, food_id, heart_id in combos:
            print(f"  {road_id:10} {companion_id:9} {food_id:10} {heart_id}")
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
            header = f"### {p.hero_name}: {p.companion} on {p.road} with {p.food} ({outcome_from_params(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
