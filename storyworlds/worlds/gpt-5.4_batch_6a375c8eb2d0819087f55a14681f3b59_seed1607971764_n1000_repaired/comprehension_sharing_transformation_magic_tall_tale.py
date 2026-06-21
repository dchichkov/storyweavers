#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py
==================================================================================

A standalone storyworld for a tall-tale flavored domain where a child learns that
real sharing begins with comprehension: noticing somebody else's need clearly
enough to act on it. A small magical food changes shape when it is shared, but
only when the chosen vessel actually fits the kind of transformation and the
magic is strong enough for the hungry crowd.

Run it
------
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py --item peach --vessel pie_pan
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py --item bean --vessel pie_pan
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/comprehension_sharing_transformation_magic_tall_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
    opening: str
    scale_line: str
    ending_image: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    meal: str
    vessel_kind: str
    power: int
    boast: str
    transform_text: str
    ending_phrase: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    kind: str
    prep_text: str
    contain_power: int
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
class Recipients:
    id: str
    label: str
    count_text: str
    appetite: int
    arrive_text: str
    thanks_text: str
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
class Trait:
    id: str
    label: str
    starts_open: bool
    hesitation_text: str
    turn_text: str
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


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    vessel = world.get("vessel")
    crowd = world.get("crowd")
    feast = world.get("feast")
    if item.meters["shared"] < THRESHOLD:
        return out
    if feast.meters["abundance"] >= THRESHOLD:
        return out
    sig = ("transform", world.facts["item"].id, world.facts["vessel"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if not compatible(world.facts["item"], world.facts["vessel"]):
        raise StoryError(explain_vessel(world.facts["item"], world.facts["vessel"]))
    if not enough_for_crowd(world.facts["item"], world.facts["vessel"], world.facts["recipients"]):
        raise StoryError(explain_capacity(world.facts["item"], world.facts["vessel"], world.facts["recipients"]))
    item.meters["gone"] += 1
    crowd.meters["waiting"] += 1
    feast.meters["abundance"] += float(world.facts["item"].power)
    feast.attrs["meal"] = world.facts["item"].meal
    out.append("__transform__")
    return out


def _r_feed(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.get("crowd")
    feast = world.get("feast")
    hero = world.get("hero")
    town = world.get("town")
    if crowd.meters["hunger"] < THRESHOLD or feast.meters["abundance"] < THRESHOLD:
        return out
    sig = ("feed", world.facts["recipients"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if feast.meters["abundance"] < world.facts["recipients"].appetite:
        raise StoryError(explain_capacity(world.facts["item"], world.facts["vessel"], world.facts["recipients"]))
    crowd.meters["hunger"] = 0.0
    crowd.meters["full"] += 1
    town.memes["cheer"] += 1
    hero.memes["comprehension"] += 1
    hero.memes["joy"] += 1
    out.append("__fed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform", tag="magic", apply=_r_transform),
    Rule(name="feed", tag="sharing", apply=_r_feed),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
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


def compatible(item: MagicItem, vessel: Vessel) -> bool:
    return item.vessel_kind == vessel.kind


def enough_for_crowd(item: MagicItem, vessel: Vessel, recipients: Recipients) -> bool:
    return compatible(item, vessel) and min(item.power, vessel.contain_power) >= recipients.appetite


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for iid, item in MAGIC_ITEMS.items():
            for vid, vessel in VESSELS.items():
                for rid, recipients in RECIPIENT_GROUPS.items():
                    if enough_for_crowd(item, vessel, recipients):
                        combos.append((sid, iid, vid, rid))
    return combos


def explain_vessel(item: MagicItem, vessel: Vessel) -> str:
    return (
        f"(No story: {item.label} turns into {item.meal}, so it needs {article(vessel_kind_label(item.vessel_kind))} "
        f"that matches that kind of magic. {vessel.phrase.capitalize()} would not honestly set up the transformation.)"
    )


def explain_capacity(item: MagicItem, vessel: Vessel, recipients: Recipients) -> str:
    power = min(item.power, vessel.contain_power)
    return (
        f"(No story: {item.phrase} in {vessel.phrase} can feed a crowd appetite of about {power}, "
        f"but {recipients.label} are hungrier than that. Pick a stronger magic item, a roomier vessel, or a smaller crowd.)"
    )


def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def vessel_kind_label(kind: str) -> str:
    return {
        "kettle": "kettle",
        "griddle": "griddle",
        "pan": "pie pan",
    }.get(kind, kind)


def initial_generosity(trait: Trait) -> float:
    return 2.0 if trait.starts_open else 0.0


def predict_feast(world: World) -> dict:
    sim = world.copy()
    sim.get("item").meters["shared"] += 1
    propagate(sim, narrate=False)
    crowd = sim.get("crowd")
    feast = sim.get("feast")
    return {
        "fed": crowd.meters["full"] >= THRESHOLD,
        "abundance": feast.meters["abundance"],
    }


def introduce(world: World, hero: Entity, helper: Entity, item: MagicItem) -> None:
    world.say(
        f"{world.setting.opening} {world.setting.scale_line} "
        f"In that place lived {hero.id}, a {hero.traits[0]} {hero.type} with {item.phrase} tucked safe in {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"Folks said {item.boast}, and by sunset everybody in the county had heard the story twice."
    )
    world.say(
        f"{helper.label_word.capitalize()} used to tell {hero.id}, "
        f'"Real sharing begins with comprehension. First you notice another person\'s need, and then your hands know what to do."'
    )


def arrive_hungry(world: World, recipients: Recipients) -> None:
    crowd = world.get("crowd")
    crowd.meters["hunger"] = 1.0
    world.say(recipients.arrive_text)
    world.say(
        f"They looked hungry enough to nibble the paint off a fence, and there were {recipients.count_text} of them."
    )


def hesitate_or_offer(world: World, hero: Entity, trait: Trait, helper: Entity, item: MagicItem) -> str:
    if trait.starts_open:
        hero.memes["generosity"] += 1
        world.say(
            f"{hero.id} patted {hero.pronoun('possessive')} pocket and grinned. "
            f'"If this {item.label} is as magical as folks say, it ought to do more than sit there and brag."'
        )
        return "ready"
    hero.memes["greed"] += 1
    world.say(
        f"{hero.id} curled {hero.pronoun('possessive')} fingers around the {item.label}. {trait.hesitation_text}"
    )
    world.say(
        f"{helper.label_word.capitalize()} bent low and spoke softly. {trait.turn_text} "
        f'"That is comprehension," {helper.pronoun()} said. "You just made room for somebody else in your thinking."'
    )
    hero.memes["comprehension"] += 1
    hero.memes["generosity"] += 1
    return "turn"


def prepare_magic(world: World, hero: Entity, vessel: Vessel) -> None:
    vessel_ent = world.get("vessel")
    vessel_ent.meters["ready"] = 1.0
    world.say(
        f"Then {hero.id} fetched {vessel.phrase}. {vessel.prep_text}"
    )


def share_item(world: World, hero: Entity, recipients: Recipients, item: MagicItem, vessel: Vessel) -> None:
    pred = predict_feast(world)
    world.facts["predicted_fed"] = pred["fed"]
    world.facts["predicted_abundance"] = pred["abundance"]
    if not pred["fed"]:
        raise StoryError(explain_capacity(item, vessel, recipients))
    world.get("item").meters["shared"] += 1
    world.say(
        f'"No pocket was ever made to be a pantry for one," {hero.id} said, and {hero.pronoun()} dropped the {item.label} into the {vessel.label}.'
    )
    markers = propagate(world, narrate=False)
    if "__transform__" in markers:
        world.say(item.transform_text.format(vessel=vessel.label))
    if "__fed__" in markers:
        world.say(
            f"Soon the whole crowd was eating, laughing, and calling for seconds in voices that bounced off the clouds."
        )


def end_story(world: World, hero: Entity, helper: Entity, item: MagicItem, recipients: Recipients, mode: str) -> None:
    if mode == "ready":
        opener = f"{hero.id} had shared quickly, and that quick kindness made the magic seem even bigger."
    else:
        opener = f"{hero.id} had needed one good pause to understand the hungry faces, and that new comprehension changed everything."
    world.say(opener)
    world.say(
        f"{recipients.thanks_text} {helper.label_word.capitalize()} only smiled, because the best part was not the feast but the way {hero.id} now looked around for empty hands before supper."
    )
    world.say(
        f"After that, {world.setting.ending_image}, and {hero.id} kept {item.ending_phrase} ready for the next hungry soul."
    )


def tell(
    setting: Setting,
    item: MagicItem,
    vessel: Vessel,
    recipients: Recipients,
    trait: Trait,
    hero_name: str = "June",
    hero_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait.label],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the elder",
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="group",
        type="group",
        role="crowd",
        label=recipients.label,
    ))
    town = world.add(Entity(
        id="town",
        kind="place",
        type="place",
        role="town",
        label=setting.place,
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="magic_item",
        role="item",
        label=item.label,
    ))
    vessel_ent = world.add(Entity(
        id="vessel",
        kind="thing",
        type="vessel",
        role="vessel",
        label=vessel.label,
    ))
    feast = world.add(Entity(
        id="feast",
        kind="thing",
        type="feast",
        role="feast",
        label=item.meal,
    ))

    hero.memes["generosity"] = initial_generosity(trait)
    hero.memes["comprehension"] = 0.0
    crowd.meters["hunger"] = 0.0
    feast.meters["abundance"] = 0.0
    vessel_ent.meters["ready"] = 0.0
    item_ent.meters["shared"] = 0.0
    item_ent.meters["gone"] = 0.0

    world.facts.update(
        setting=setting,
        item=item,
        vessel=vessel,
        recipients=recipients,
        trait=trait,
        hero=hero,
        helper=helper,
        mode="",
        predicted_fed=False,
        predicted_abundance=0.0,
    )

    introduce(world, hero, helper, item)
    world.para()
    arrive_hungry(world, recipients)
    mode = hesitate_or_offer(world, hero, trait, helper, item)
    world.facts["mode"] = mode
    world.para()
    prepare_magic(world, hero, vessel)
    share_item(world, hero, recipients, item, vessel)
    world.para()
    end_story(world, hero, helper, item, recipients, mode)
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the prairie",
        opening="On the broad prairie, the grass waved so high it could tickle a passing cloud.",
        scale_line="The wind there was strong enough to iron shirts on a clothesline without any help from human hands.",
        ending_image="the supper smoke over the prairie curled into friendly shapes that looked like open palms",
        tags={"prairie", "sharing"},
    ),
    "riverbend": Setting(
        id="riverbend",
        place="the river bend",
        opening="At the river bend, the water rolled so wide and shiny it looked like somebody had spilled the sky.",
        scale_line="Catfish swore they needed maps to cross from one muddy side to the other.",
        ending_image="the river bend smelled sweet enough to make even the boats slow down and sniff",
        tags={"river", "sharing"},
    ),
    "mesa": Setting(
        id="mesa",
        place="the red mesa",
        opening="Out on the red mesa, the noon sun stood so tall it seemed to wear boots of fire.",
        scale_line="Even the shadows stretched themselves thin and lazy across the rocks.",
        ending_image="the red mesa glowed warm as a kitchen hearth long after the stars came out",
        tags={"mesa", "sharing"},
    ),
}

MAGIC_ITEMS = {
    "bean": MagicItem(
        id="bean",
        label="bean",
        phrase="a striped magic bean",
        meal="peppery bean stew",
        vessel_kind="kettle",
        power=4,
        boast="one striped magic bean could swell into a kettle of stew broad enough to mirror the moon",
        transform_text="The {vessel} gave one mighty burp of steam, and that little bean turned into peppery bean stew, rich and deep, enough to make spoons line up like horses at a trough.",
        ending_phrase="a bright clean spoon",
        tags={"bean", "stew", "magic"},
    ),
    "biscuit": MagicItem(
        id="biscuit",
        label="biscuit",
        phrase="a thumb-sized golden biscuit",
        meal="honey biscuits",
        vessel_kind="griddle",
        power=3,
        boast="one thumb-sized biscuit could bloom into a stack so high the crows used it for lookout practice",
        transform_text="The {vessel} sang and shimmered, and that one biscuit sprang into a stack of honey biscuits so tall they leaned politely into the wind.",
        ending_phrase="a folded napkin",
        tags={"biscuit", "griddle", "magic"},
    ),
    "peach": MagicItem(
        id="peach",
        label="peach",
        phrase="a sun-warm magic peach",
        meal="peach pie",
        vessel_kind="pan",
        power=5,
        boast="one peach could tumble into a pie wide enough to make a scarecrow loosen its belt",
        transform_text="The {vessel} glowed soft and gold, and the peach folded itself into a peach pie so broad and bubbling that the smell nearly lifted hats right off heads.",
        ending_phrase="an extra plate",
        tags={"peach", "pie", "magic"},
    ),
}

VESSELS = {
    "kettle": Vessel(
        id="kettle",
        label="kettle",
        phrase="a black iron kettle",
        kind="kettle",
        prep_text="When it touched the ground, the dirt under it hummed like a sleepy bass fiddle.",
        contain_power=5,
        tags={"kettle"},
    ),
    "griddle": Vessel(
        id="griddle",
        label="griddle",
        phrase="a flat griddle",
        kind="griddle",
        prep_text="It was warm before the fire even got the idea to start.",
        contain_power=3,
        tags={"griddle"},
    ),
    "pie_pan": Vessel(
        id="pie_pan",
        label="pie pan",
        phrase="a tin pie pan",
        kind="pan",
        prep_text="It flashed so bright in the sun that a hawk tipped one wing in respect.",
        contain_power=5,
        tags={"pan"},
    ),
    "wash_tub": Vessel(
        id="wash_tub",
        label="wash tub",
        phrase="a clean wash tub",
        kind="tub",
        prep_text="It was roomy as all get-out, but roomy is not the same thing as right.",
        contain_power=6,
        tags={"tub"},
    ),
}

RECIPIENT_GROUPS = {
    "cowhands": Recipients(
        id="cowhands",
        label="three cowhands",
        count_text="three of them",
        appetite=3,
        arrive_text="Just then three dusty cowhands came up the trail, hats low and stomachs rumbling louder than wagon wheels.",
        thanks_text="The cowhands tipped their hats and said they had not eaten so grandly since a county fair blew through by accident.",
        tags={"cowhands", "hunger"},
    ),
    "river_children": Recipients(
        id="river_children",
        label="four river children",
        count_text="four hungry children",
        appetite=4,
        arrive_text="Before long, four river children scrambled ashore, wet to the knees and hungry enough to stare hard at every lunch basket in sight.",
        thanks_text="The river children licked their fingers and laughed so hard the minnows splashed along with them.",
        tags={"children", "hunger"},
    ),
    "mail_riders": Recipients(
        id="mail_riders",
        label="five mail riders",
        count_text="five tired riders",
        appetite=5,
        arrive_text="At dusk five mail riders clattered in, tired from chasing miles and weather, with bellies sounding hollow as dry drums.",
        thanks_text="The mail riders declared that no road in the territory was too long after a supper like that.",
        tags={"riders", "hunger"},
    ),
}

TRAITS = {
    "openhearted": Trait(
        id="openhearted",
        label="openhearted",
        starts_open=True,
        hesitation_text="",
        turn_text="",
    ),
    "careful": Trait(
        id="careful",
        label="careful",
        starts_open=False,
        hesitation_text='"It is only one little thing," '
                        "she thought, as if one little magical thing might not matter to a whole hungry crowd.",
        turn_text='"Look at their faces," grandma said. "Comprehension is not a fancy word. It just means understanding someone else well enough to care."',
    ),
    "stingy_then_sorry": Trait(
        id="stingy_then_sorry",
        label="stingy",
        starts_open=False,
        hesitation_text='"Maybe I ought to save it for myself," '
                        "he thought, though the hungry sound around him was plain as thunder.",
        turn_text='"Listen to those stomachs," grandpa said. "Comprehension can be as simple as hearing what need sounds like."',
    ),
}

GIRL_NAMES = ["June", "Mabel", "Dora", "Nell", "Ruby", "Ada", "Minnie", "Pearl"]
BOY_NAMES = ["Eli", "Jasper", "Bo", "Toby", "Cal", "Hank", "Milo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    item: str
    vessel: str
    recipients: str
    trait: str
    hero_name: str
    hero_type: str
    helper_type: str
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
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting other people use or enjoy something with you instead of keeping it all to yourself. When people share food, toys, or time, everyone can feel included."
    )],
    "comprehension": [(
        "What does comprehension mean?",
        "Comprehension means understanding something clearly. In a story about people, it can also mean understanding how someone else feels or what they need."
    )],
    "magic": [(
        "What is magic in a story?",
        "Magic in a story is something that can happen in a wonderful impossible way. It lets an ordinary thing become surprising, like one peach turning into a giant pie."
    )],
    "bean": [(
        "How can a bean be used in food?",
        "A bean can be cooked in soup or stew. When many beans cook together, they make a warm meal people can share."
    )],
    "biscuit": [(
        "What is a biscuit?",
        "A biscuit is a small baked bread. It can be plain or sweet, and people often eat it warm."
    )],
    "peach": [(
        "What is a peach?",
        "A peach is a sweet fruit with soft skin and a pit in the middle. People can eat it fresh or bake it into pie."
    )],
    "kettle": [(
        "What is a kettle for?",
        "A kettle is a pot used for heating or cooking things, especially soups or stews. It is deep, so it can hold a lot."
    )],
    "griddle": [(
        "What is a griddle?",
        "A griddle is a flat cooking surface. People use it to cook things like pancakes or biscuits."
    )],
    "pan": [(
        "What is a pie pan?",
        "A pie pan is a shallow dish used to bake a pie. It helps hold the crust and filling in shape."
    )],
    "hunger": [(
        "What does it mean to be hungry?",
        "Being hungry means your body needs food. A hungry person may feel tired, weak, or ready for supper."
    )],
}
KNOWLEDGE_ORDER = ["sharing", "comprehension", "magic", "hunger", "bean", "biscuit", "peach", "kettle", "griddle", "pan"]


CURATED = [
    StoryParams(
        setting="prairie",
        item="bean",
        vessel="kettle",
        recipients="river_children",
        trait="careful",
        hero_name="June",
        hero_type="girl",
        helper_type="grandmother",
        seed=101,
    ),
    StoryParams(
        setting="riverbend",
        item="biscuit",
        vessel="griddle",
        recipients="cowhands",
        trait="openhearted",
        hero_name="Bo",
        hero_type="boy",
        helper_type="grandfather",
        seed=102,
    ),
    StoryParams(
        setting="mesa",
        item="peach",
        vessel="pie_pan",
        recipients="mail_riders",
        trait="stingy_then_sorry",
        hero_name="Ada",
        hero_type="girl",
        helper_type="grandmother",
        seed=103,
    ),
]


def outcome_of(params: StoryParams) -> str:
    trait = TRAITS[params.trait]
    return "ready" if trait.starts_open else "turn"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    recipients = f["recipients"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that uses the word "comprehension" and includes sharing, magic, and transformation.',
        f"Tell a gentle tall tale where a {hero.type} named {hero.id} uses {item.phrase} to feed {recipients.label} after learning that sharing begins with comprehension.",
        f"Write a child-facing story where {helper.label_word} helps a child understand someone else's hunger, and a magical food changes into a giant meal for everyone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    vessel = f["vessel"]
    recipients = f["recipients"]
    mode = f["mode"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {article(hero.type)} {hero.type}, and {helper.label_word} who helps {hero.pronoun('object')} think about other people. The hungry visitors matter too, because their need is what turns the story."
        ),
        (
            f"What magical thing did {hero.id} have?",
            f"{hero.id} had {item.phrase}. It was magical because, once it was shared the right way, it could transform into {item.meal}."
        ),
        (
            "Why did the visitors matter?",
            f"They arrived hungry, so {hero.id} had to notice that somebody else needed help. That is where comprehension entered the story, because understanding their hunger changed what {hero.pronoun()} chose to do."
        ),
        (
            f"How did the magic transformation happen?",
            f"{hero.id} put the {item.label} into {vessel.phrase}, and the magic changed it into {item.meal}. The transformation worked because the story's magic needed the right kind of vessel and a shared heart."
        ),
    ]
    if mode == "ready":
        qa.append((
            f"Did {hero.id} share right away?",
            f"Yes. {hero.id} offered the magic food quickly, and that showed {hero.pronoun('possessive')} kindness was already awake. The story still uses comprehension, because {hero.pronoun()} understood the hungry crowd before anyone had to argue."
        ))
    else:
        qa.append((
            f"Why did {hero.id} hesitate before sharing?",
            f"At first {hero.id} wanted to keep the magic food close, because one little treat can feel precious. Then {helper.label_word} helped {hero.pronoun('object')} understand the hungry faces and sounds around {hero.pronoun('object')}, so comprehension turned hesitation into sharing."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with everybody fed and thankful, and with {hero.id} changed on the inside too. By the end, {hero.pronoun()} was looking for empty hands before supper, which proves the lesson lasted longer than the magic meal."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "comprehension", "magic", "hunger"}
    tags |= set(f["item"].tags)
    tags |= set(f["vessel"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(I, V) :- item(I), vessel(V), needs_kind(I, K), vessel_kind(V, K).
effective_power(I, V, P) :- compatible(I, V), item_power(I, IP), vessel_cap(V, VC), IP <= VC, P = IP.
effective_power(I, V, P) :- compatible(I, V), item_power(I, IP), vessel_cap(V, VC), VC < IP, P = VC.
enough(I, V, R) :- effective_power(I, V, P), appetite(R, A), P >= A.
valid(S, I, V, R) :- setting(S), compatible(I, V), enough(I, V, R), recipients(R).

ready_trait(T) :- trait(T), starts_open(T).
outcome(ready) :- chosen_trait(T), ready_trait(T).
outcome(turn) :- chosen_trait(T), not ready_trait(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in MAGIC_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("needs_kind", iid, item.vessel_kind))
        lines.append(asp.fact("item_power", iid, item.power))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("vessel_kind", vid, vessel.kind))
        lines.append(asp.fact("vessel_cap", vid, vessel.contain_power))
    for rid, group in RECIPIENT_GROUPS.items():
        lines.append(asp.fact("recipients", rid))
        lines.append(asp.fact("appetite", rid, group.appetite))
    for tid, trait in TRAITS.items():
        lines.append(asp.fact("trait", tid))
        if trait.starts_open:
            lines.append(asp.fact("starts_open", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: sharing, comprehension, and a magical transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--recipients", choices=RECIPIENT_GROUPS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def explain_no_combo() -> str:
    return "(No valid combination matches the given options.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.vessel:
        item = MAGIC_ITEMS[args.item]
        vessel = VESSELS[args.vessel]
        if not compatible(item, vessel):
            raise StoryError(explain_vessel(item, vessel))
    if args.item and args.vessel and args.recipients:
        item = MAGIC_ITEMS[args.item]
        vessel = VESSELS[args.vessel]
        recipients = RECIPIENT_GROUPS[args.recipients]
        if compatible(item, vessel) and not enough_for_crowd(item, vessel, recipients):
            raise StoryError(explain_capacity(item, vessel, recipients))
    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.vessel is None or combo[2] == args.vessel)
        and (args.recipients is None or combo[3] == args.recipients)
    ]
    if not combos:
        raise StoryError(explain_no_combo())

    setting, item, vessel, recipients = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(sorted(TRAITS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        setting=setting,
        item=item,
        vessel=vessel,
        recipients=recipients,
        trait=trait,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in MAGIC_ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.recipients not in RECIPIENT_GROUPS:
        raise StoryError(f"(Unknown recipients: {params.recipients})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    setting = SETTINGS[params.setting]
    item = MAGIC_ITEMS[params.item]
    vessel = VESSELS[params.vessel]
    recipients = RECIPIENT_GROUPS[params.recipients]
    trait = TRAITS[params.trait]

    if not compatible(item, vessel):
        raise StoryError(explain_vessel(item, vessel))
    if not enough_for_crowd(item, vessel, recipients):
        raise StoryError(explain_capacity(item, vessel, recipients))

    world = tell(
        setting=setting,
        item=item,
        vessel=vessel,
        recipients=recipients,
        trait=trait,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (setting, item, vessel, recipients) combos:\n")
        for setting, item, vessel, recipients in combos:
            print(f"  {setting:10} {item:8} {vessel:8} {recipients}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = (
                f"### {p.hero_name}: {p.item} in {p.vessel} for {p.recipients} "
                f"({p.setting}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
