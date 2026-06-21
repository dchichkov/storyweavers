#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py
====================================================================

A standalone story world for a tiny animal-story domain:

Two young animals are carrying a surprise gift to an elder animal when they meet
a risky shortcut. One animal is prudent and warns what might happen. Either the
warning is heeded at once, or there is a near-miss and a helpful neighbor offers
the right fix. Every branch ends happily, with the gift arriving safely and a
crooked little tag marked "abdc" making everyone smile.

Run it
------
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py --obstacle windy_knoll --gift flower_crown
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py --gift honey_jar --obstacle bramble_gap
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/prudent_abdc_happy_ending_animal_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    species: str = ""
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "doe", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "buck", "rooster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_species(self) -> str:
        if self.species:
            return f"{self.id} the {self.species}"
        return self.id
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    path_text: str
    home_text: str
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
class Obstacle:
    id: str
    label: str
    shortcut: str
    hazard: str
    severity: int
    sight: str
    danger_text: str
    mishap_text: str
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
class Gift:
    id: str
    label: str
    phrase: str
    fragile: int
    vulnerable_to: set[str]
    opening_text: str
    ending_image: str
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
class Fix:
    id: str
    label: str
    guards: set[str]
    helper_species: str
    helper_name: str
    offer_text: str
    use_text: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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
        self.facts: dict = {
            "mishap_kind": "",
            "predicted_risk": 0,
            "outcome": "",
            "delivered": False,
            "tag_word": "abdc",
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_endangered(world: World) -> list[str]:
    gift = world.get("gift")
    if gift.meters["endangered"] < THRESHOLD:
        return []
    sig = ("endangered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["alarm"] += 1
    friend.memes["alarm"] += 1
    world.get("path").meters["urgency"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="endangered", tag="physical", apply=_r_endangered),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the clover meadow",
        path_text="The path to Aunt Willow's hollow curled past a brook, a patch of berries, and a sleepy old stump.",
        home_text="Aunt Willow lived in a warm hollow under the hill.",
        tags={"meadow"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the apple orchard",
        path_text="The path to Aunt Willow's hollow wound between roots, low stone walls, and rows of fallen apples.",
        home_text="Aunt Willow lived in a warm hollow under the hill.",
        tags={"orchard"},
    ),
    "fern_glen": Setting(
        id="fern_glen",
        place="the fern glen",
        path_text="The path to Aunt Willow's hollow slipped through soft ferns and under bright strips of afternoon light.",
        home_text="Aunt Willow lived in a warm hollow under the hill.",
        tags={"forest"},
    ),
}

OBSTACLES = {
    "stepping_stones": Obstacle(
        id="stepping_stones",
        label="stepping stones",
        shortcut="a line of mossy stepping stones across the brook",
        hazard="tilt",
        severity=2,
        sight="The stones looked quick and clever, but each one leaned a little to one side.",
        danger_text="One wrong tilt could tip the gift right out of careful paws.",
        mishap_text="the gift tipped sharply as the stone rolled underfoot",
        tags={"brook", "balance"},
    ),
    "bramble_gap": Obstacle(
        id="bramble_gap",
        label="bramble gap",
        shortcut="a narrow gap in a bramble hedge",
        hazard="snag",
        severity=2,
        sight="The gap looked short, but thorny loops tugged at anything soft or loose.",
        danger_text="The brambles could catch and pull before anyone wriggled through.",
        mishap_text="a thorny loop snagged the gift and held it fast",
        tags={"bramble", "thorn"},
    ),
    "windy_knoll": Obstacle(
        id="windy_knoll",
        label="windy knoll",
        shortcut="the windy knoll above the path",
        hazard="wind",
        severity=2,
        sight="The hill was bare and bright, and every gust came skipping over it.",
        danger_text="A gust could lift light things and tug tags right into the air.",
        mishap_text="a sudden gust caught the gift and made it bob wildly",
        tags={"wind"},
    ),
    "rooty_slope": Obstacle(
        id="rooty_slope",
        label="rooty slope",
        shortcut="a rooty slope beside the old stump",
        hazard="jostle",
        severity=1,
        sight="The slope was faster than the long path, but the roots stuck up like knobby fingers.",
        danger_text="A bumpy scramble would shake any careful bundle.",
        mishap_text="the gift bounced and rattled against the roots",
        tags={"roots", "slope"},
    ),
}

GIFTS = {
    "berry_pie": Gift(
        id="berry_pie",
        label="berry pie",
        phrase="a little berry pie on a leaf tray",
        fragile=3,
        vulnerable_to={"tilt", "jostle"},
        opening_text="The pie smelled of warm berries and sweet crust.",
        ending_image="the berry pie sat on Aunt Willow's table with one fat blackberry shining on top",
        tags={"pie", "berries"},
    ),
    "flower_crown": Gift(
        id="flower_crown",
        label="flower crown",
        phrase="a daisy-and-buttercup flower crown",
        fragile=2,
        vulnerable_to={"wind", "snag"},
        opening_text="The crown was light as a whisper and still cool with morning dew.",
        ending_image="the flower crown rested over Aunt Willow's ears, bright as a ring of sunshine",
        tags={"flowers"},
    ),
    "honey_jar": Gift(
        id="honey_jar",
        label="honey jar",
        phrase="a small honey jar tied with blue grass",
        fragile=2,
        vulnerable_to={"tilt"},
        opening_text="The honey glowed gold when the light touched the glass.",
        ending_image="the honey jar glowed beside the teacups like a little lantern",
        tags={"honey"},
    ),
    "seed_cakes": Gift(
        id="seed_cakes",
        label="seed cakes",
        phrase="a stack of tiny seed cakes wrapped in dock leaves",
        fragile=2,
        vulnerable_to={"jostle", "wind"},
        opening_text="The seed cakes smelled nutty and toasty.",
        ending_image="the seed cakes waited on a moss plate, neat and safe in their leaf wrapping",
        tags={"seeds"},
    ),
}

FIXES = {
    "flat_tray": Fix(
        id="flat_tray",
        label="flat bark tray",
        guards={"tilt"},
        helper_species="beaver",
        helper_name="Moss",
        offer_text="set down a flat bark tray with little ridges on the sides",
        use_text="slid the gift onto the flat bark tray and carried it level, step by step",
        qa_text="They used a flat bark tray that kept the gift level.",
        tags={"tray", "balance"},
    ),
    "lidded_basket": Fix(
        id="lidded_basket",
        label="lidded reed basket",
        guards={"wind", "jostle"},
        helper_species="hedgehog",
        helper_name="Nib",
        offer_text="rolled over a lidded reed basket and clicked the lid snugly shut",
        use_text="tucked the gift inside the basket, where the lid held it steady and safe",
        qa_text="They tucked the gift into a lidded basket so the wind or bumps could not bother it.",
        tags={"basket", "wind"},
    ),
    "tunnel_way": Fix(
        id="tunnel_way",
        label="fern tunnel",
        guards={"snag"},
        helper_species="mole",
        helper_name="Pipkin",
        offer_text="poked up from the earth and showed them a smooth fern tunnel under the brambles",
        use_text="ducked through the fern tunnel, where no thorn could catch the gift",
        qa_text="They went through a smooth tunnel under the brambles.",
        tags={"tunnel", "bramble"},
    ),
}

GIRL_NAMES = ["Mira", "Tansy", "Poppy", "Luna", "Hazel", "Daisy"]
BOY_NAMES = ["Pip", "Otis", "Rowan", "Bram", "Nico", "Finn"]
SPECIES = ["rabbit", "mouse", "squirrel", "fox", "duck", "badger"]
TRAITS = ["bouncy", "cheerful", "eager", "quick", "gentle"]


def gift_at_risk(obstacle: Obstacle, gift: Gift) -> bool:
    return obstacle.hazard in gift.vulnerable_to


def matching_fixes(obstacle: Obstacle) -> list[str]:
    return [fid for fid, fx in FIXES.items() if obstacle.hazard in fx.guards]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for obstacle_id, obstacle in OBSTACLES.items():
            fixes = matching_fixes(obstacle)
            if not fixes:
                continue
            for gift_id, gift in GIFTS.items():
                if gift_at_risk(obstacle, gift):
                    for fix_id in fixes:
                        combos.append((setting_id, obstacle_id, gift_id, fix_id))
    return combos


def obvious_enough_to_heed(obstacle: Obstacle, gift: Gift) -> bool:
    return obstacle.severity + gift.fragile >= 5


def explain_rejection(obstacle: Obstacle, gift: Gift) -> str:
    return (
        f"(No story: {obstacle.label} mainly threatens things vulnerable to "
        f"{obstacle.hazard}, but {gift.label} is not honestly at risk that way. "
        f"Pick a gift that could really be troubled there.)"
    )


def explain_fix(obstacle: Obstacle, fix_id: str) -> str:
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} does not solve the problem at {obstacle.label}. "
        f"It guards {sorted(fix.guards)}, but this shortcut's real trouble is "
        f"{obstacle.hazard}.)"
    )


def predict_trouble(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    gift = sim.get("gift")
    gift.meters["endangered"] += 1
    gift.meters[obstacle.hazard] += 1
    propagate(sim, narrate=False)
    return {
        "endangered": gift.meters["endangered"] >= THRESHOLD,
        "hazard": obstacle.hazard,
        "risk": obstacle.severity + int(gift.meters["fragile"]),
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, gift: Gift) -> None:
    world.say(
        f"On a bright afternoon in {world.setting.place}, {hero.name_species()} and "
        f"{friend.name_species()} were carrying a surprise to {elder.name_species()}."
    )
    world.say(world.setting.home_text)
    world.say(
        f"They had made {gift.phrase}, and {gift.opening_text}"
    )
    world.say(
        f"Tied to it was a tiny tag where {hero.id} had practiced letters and written "
        f'"abdc" in a crooked row. {friend.id} thought the mistake looked sweet.'
    )


def set_character_state(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["hurry"] += 1
    friend.memes["care"] += 1
    friend.memes["prudence"] += 1


def walk_to_shortcut(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.say(world.setting.path_text)
    world.say(
        f"Soon they came to {obstacle.shortcut}. {obstacle.sight}"
    )
    world.say(
        f'"This way is faster," said {hero.id}, twitching with hurry.'
    )


def prudent_warning(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, elder: Entity) -> None:
    pred = predict_trouble(world, obstacle)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{friend.id} was a prudent little {friend.species}. "{obstacle.danger_text} '
        f'Let us carry it safely to {elder.id}," {friend.pronoun()} said.'
    )


def heed_warning(world: World, hero: Entity, friend: Entity, fix: Fix, elder: Entity) -> None:
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    helper = world.add(
        Entity(
            id=fix.helper_name,
            kind="character",
            type="neighbor",
            species=fix.helper_species,
            role="helper",
            label="the helper",
        )
    )
    helper.memes["kindness"] += 1
    world.say(
        f'{hero.id} looked again, saw the wobble in the shortcut, and nodded. '
        f'"You are right," {hero.pronoun()} said.'
    )
    world.say(
        f"Just then {helper.name_species()} came by and {fix.offer_text}. "
        f'"Here, this will help," {helper.pronoun()} said.'
    )
    world.say(
        f"Together they {fix.use_text}, taking the longer path with easy, careful steps."
    )
    world.facts["helper"] = helper


def try_shortcut(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    gift = world.get("gift")
    gift.meters["endangered"] += 1
    gift.meters[obstacle.hazard] += 1
    world.facts["mishap_kind"] = obstacle.hazard
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id} was still curious about the quick way, so {hero.pronoun()} stepped onto it first."
    )
    world.say(
        f"At once {obstacle.mishap_text}. The little tag with 'abdc' fluttered, and both friends gasped."
    )


def rescue_with_fix(world: World, friend: Entity, fix: Fix) -> None:
    gift = world.get("gift")
    gift.meters["secured"] += 1
    gift.meters["endangered"] = 0.0
    helper = world.add(
        Entity(
            id=fix.helper_name,
            kind="character",
            type="neighbor",
            species=fix.helper_species,
            role="helper",
            label="the helper",
        )
    )
    helper.memes["kindness"] += 1
    world.say(
        f"Out popped {helper.name_species()}, who had seen the trouble. "
        f"{helper.pronoun().capitalize()} {fix.offer_text}."
    )
    world.say(
        f'{friend.id} held the gift still while they {fix.use_text}. '
        f'Soon everyone was breathing slowly again.'
    )
    world.facts["helper"] = helper


def arrival(world: World, hero: Entity, friend: Entity, elder: Entity, gift_cfg: Gift) -> None:
    gift = world.get("gift")
    gift.meters["delivered"] += 1
    world.facts["delivered"] = True
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    elder.memes["love"] += 1
    world.say(
        f"When they reached {elder.id}'s hollow, {elder.name_species()} opened the door with a warm smile."
    )
    world.say(
        f"{elder.id} laughed softly at the crooked tag. "
        f'"{world.facts["tag_word"]} is not the usual order," {elder.pronoun()} said, '
        f'"but I would know your loving paws anywhere."'
    )
    world.say(
        f"They set the gift down, and soon {gift_cfg.ending_image}. "
        f"The whole hollow smelled sweet and safe."
    )


def lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'{hero.id} gave {friend.id} a thankful look. "Next time I will listen when you are careful first," '
        f'{hero.pronoun()} said.'
    )
    world.say(
        f'{friend.id} smiled. "And next time we can still be quick after we are safe," {friend.pronoun()} said.'
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    gift_cfg: Gift,
    fix_cfg: Fix,
    hero_name: str = "Pip",
    hero_gender: str = "boy",
    hero_species: str = "rabbit",
    friend_name: str = "Mira",
    friend_gender: str = "girl",
    friend_species: str = "mouse",
    elder_name: str = "Aunt Willow",
    elder_species: str = "otter",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            species=hero_species,
            role="hero",
            label="the hero",
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            species=friend_species,
            role="friend",
            label="the prudent friend",
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type="elder",
            species=elder_species,
            role="elder",
            label="the elder",
        )
    )
    gift = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift_cfg.label,
            role="gift",
        )
    )
    gift.meters["fragile"] = float(gift_cfg.fragile)
    world.add(Entity(id="path", kind="thing", type="path", label="the path", role="path"))

    set_character_state(world, hero, friend)
    introduce(world, hero, friend, elder, gift_cfg)

    world.para()
    walk_to_shortcut(world, hero, friend, obstacle)
    prudent_warning(world, hero, friend, obstacle, elder)

    world.para()
    if obvious_enough_to_heed(obstacle, gift_cfg):
        heed_warning(world, hero, friend, fix_cfg, elder)
        world.facts["outcome"] = "heeded"
    else:
        try_shortcut(world, hero, friend, obstacle)
        rescue_with_fix(world, friend, fix_cfg)
        world.facts["outcome"] = "rescued"

    world.para()
    arrival(world, hero, friend, elder, gift_cfg)
    lesson(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        gift_cfg=gift_cfg,
        obstacle=obstacle,
        fix=fix_cfg,
        setting=setting,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    gift: str
    fix: str
    hero_name: str
    hero_gender: str
    hero_species: str
    friend_name: str
    friend_gender: str
    friend_species: str
    elder_name: str = "Aunt Willow"
    elder_species: str = "otter"
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
    "brook": [
        (
            "Why can stepping stones be tricky?",
            "Stepping stones can tilt or be slippery. If you are carrying something carefully, one wobbly step can make it tip."
        )
    ],
    "bramble": [
        (
            "What are brambles?",
            "Brambles are thorny plants with long, scratchy stems. They can catch fur, ribbons, and soft things as you pass."
        )
    ],
    "wind": [
        (
            "Why can wind bother light things?",
            "Wind pushes on light things and can lift or tug them. That is why a lid or a firm basket helps on a windy hill."
        )
    ],
    "tray": [
        (
            "What does a tray help with?",
            "A tray gives something a flat place to rest. When you keep it level, it is less likely to tip or spill."
        )
    ],
    "basket": [
        (
            "Why use a basket with a lid?",
            "A lid keeps light things from blowing away and stops bumps from knocking them loose. It makes carrying safer."
        )
    ],
    "tunnel": [
        (
            "Why is a tunnel safer than pushing through thorns?",
            "A smooth tunnel lets you pass without sharp branches catching on you. It protects soft or delicate things from getting snagged."
        )
    ],
    "flowers": [
        (
            "Why is a flower crown delicate?",
            "Flowers bruise and bend easily. A little tug or strong gust can spoil the neat ring."
        )
    ],
    "pie": [
        (
            "Why must a pie stay level?",
            "A pie can slide or squish if it tips. Keeping it flat helps the filling and crust stay neat."
        )
    ],
    "honey": [
        (
            "Why can a honey jar be hard to carry?",
            "A jar can slip if it tilts, and sticky honey is messy if it spills. Careful, steady paws help."
        )
    ],
    "seeds": [
        (
            "Why wrap seed cakes carefully?",
            "Small cakes can crumble or scatter if they are bumped. Wrapping helps keep them together."
        )
    ],
}
KNOWLEDGE_ORDER = ["brook", "bramble", "wind", "tray", "basket", "tunnel", "flowers", "pie", "honey", "seeds"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    obstacle = world.facts["obstacle"]
    gift = world.facts["gift_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "heeded":
        return [
            f'Write a short animal story for a 3-to-5-year-old that uses the words "prudent" and "abdc".',
            f"Tell a gentle story where {friend.id}, a prudent {friend.species}, warns {hero.id} not to rush across {obstacle.label} while carrying a {gift.label}.",
            f"Write a happy animal story where a careful warning is listened to, a kind helper offers the right tool, and the gift arrives safely.",
        ]
    return [
        f'Write a short animal story for a 3-to-5-year-old that uses the words "prudent" and "abdc".',
        f"Tell a gentle animal story where {hero.id} tries a risky shortcut with a {gift.label}, there is a near-miss, and a helper shows a safer way.",
        f"Write a happy-ending story in which danger is small but real, the right fix is used, and everyone reaches home smiling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    gift = world.facts["gift_cfg"]
    obstacle = world.facts["obstacle"]
    fix = world.facts["fix"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.species} and {friend.id} the {friend.species} carrying a surprise to {elder.id}. They wanted their gift to reach the hollow safely."
        ),
        (
            "What was the gift, and what funny thing was on it?",
            f"They were carrying {gift.phrase}. A tiny tag on it showed the crooked letters 'abdc', which made the gift feel handmade and loving."
        ),
        (
            f"Why did {friend.id} warn {hero.id} about the shortcut?",
            f"{friend.id} warned {hero.id} because {obstacle.label} could trouble the {gift.label}. {obstacle.danger_text}"
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"What did {hero.id} do after the prudent warning?",
                f"{hero.id} looked more carefully and decided not to rush across the shortcut. That choice kept the gift out of danger before anything went wrong."
            )
        )
    else:
        qa.append(
            (
                "What happened when the quick way was tried?",
                f"The gift was endangered right away. {obstacle.mishap_text.capitalize()}, so the near-miss proved that the warning had been right."
            )
        )
    qa.append(
        (
            "How was the problem solved?",
            f"{fix.qa_text} A kind {fix.helper_species} helped at exactly the right moment, and that safe method let the friends finish the trip calmly."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They reached {elder.id}'s hollow with the gift safe and whole. The warm ending is shown when {gift.ending_image}."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle = world.facts["obstacle"]
    gift = world.facts["gift_cfg"]
    fix = world.facts["fix"]
    tags: set[str] = set()
    if obstacle.id == "stepping_stones":
        tags.add("brook")
    if obstacle.id == "bramble_gap":
        tags.add("bramble")
    if obstacle.id == "windy_knoll":
        tags.add("wind")
    if fix.id == "flat_tray":
        tags.add("tray")
    if fix.id == "lidded_basket":
        tags.add("basket")
    if fix.id == "tunnel_way":
        tags.add("tunnel")
    tags |= set(gift.tags)
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
        if ent.species:
            bits.append(f"species={ent.species}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k in {'mishap_kind', 'predicted_risk', 'outcome', 'delivered', 'tag_word'})}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow",
        obstacle="stepping_stones",
        gift="berry_pie",
        fix="flat_tray",
        hero_name="Pip",
        hero_gender="boy",
        hero_species="rabbit",
        friend_name="Mira",
        friend_gender="girl",
        friend_species="mouse",
    ),
    StoryParams(
        setting="fern_glen",
        obstacle="windy_knoll",
        gift="flower_crown",
        fix="lidded_basket",
        hero_name="Hazel",
        hero_gender="girl",
        hero_species="squirrel",
        friend_name="Otis",
        friend_gender="boy",
        friend_species="duck",
    ),
    StoryParams(
        setting="orchard",
        obstacle="bramble_gap",
        gift="flower_crown",
        fix="tunnel_way",
        hero_name="Daisy",
        hero_gender="girl",
        hero_species="rabbit",
        friend_name="Finn",
        friend_gender="boy",
        friend_species="badger",
    ),
    StoryParams(
        setting="meadow",
        obstacle="rooty_slope",
        gift="seed_cakes",
        fix="lidded_basket",
        hero_name="Rowan",
        hero_gender="boy",
        hero_species="fox",
        friend_name="Tansy",
        friend_gender="girl",
        friend_species="mouse",
    ),
]


ASP_RULES = r"""
gift_at_risk(O,G) :- obstacle(O), gift(G), hazard(O,H), vulnerable(G,H).
fix_matches(O,F) :- obstacle(O), fix(F), hazard(O,H), guards(F,H).
valid(S,O,G,F) :- setting(S), obstacle(O), gift(G), fix(F), gift_at_risk(O,G), fix_matches(O,F).

obvious_risk :- chosen_obstacle(O), chosen_gift(G), severity(O,Sev), fragile(G,Fr), Sev + Fr >= 5.
outcome(heeded) :- obvious_risk.
outcome(rescued) :- not obvious_risk.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("hazard", oid, obstacle.hazard))
        lines.append(asp.fact("severity", oid, obstacle.severity))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("fragile", gid, gift.fragile))
        for hazard in sorted(gift.vulnerable_to):
            lines.append(asp.fact("vulnerable", gid, hazard))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for hazard in sorted(fix.guards):
            lines.append(asp.fact("guards", fid, hazard))
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
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_gift", params.gift),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "heeded" if obvious_enough_to_heed(OBSTACLES[params.obstacle], GIFTS[params.gift]) else "rescued"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a prudent animal, a risky shortcut, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-species", choices=SPECIES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-species", choices=SPECIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name_gender(rng: random.Random, name: Optional[str], gender: Optional[str], avoid: str = "") -> tuple[str, str]:
    if gender is None:
        gender = rng.choice(["girl", "boy"])
    if name:
        return name, gender
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gift:
        obstacle = OBSTACLES[args.obstacle]
        gift = GIFTS[args.gift]
        if not gift_at_risk(obstacle, gift):
            raise StoryError(explain_rejection(obstacle, gift))
    if args.obstacle and args.fix:
        obstacle = OBSTACLES[args.obstacle]
        if args.fix not in matching_fixes(obstacle):
            raise StoryError(explain_fix(obstacle, args.fix))
    if args.gift and args.fix and args.obstacle:
        if (args.setting, args.obstacle, args.gift, args.fix) not in valid_combos():
            raise StoryError("(No valid combination matches the given options.)")

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gift is None or combo[2] == args.gift)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, gift_id, fix_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name_gender(rng, args.hero_name, args.hero_gender)
    friend_name, friend_gender = _pick_name_gender(rng, args.friend_name, args.friend_gender, avoid=hero_name)
    hero_species = args.hero_species or rng.choice(SPECIES)
    friend_species = args.friend_species or rng.choice([s for s in SPECIES if s != hero_species] or SPECIES)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        gift=gift_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_species=friend_species,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        obstacle = OBSTACLES[params.obstacle]
        gift = GIFTS[params.gift]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not gift_at_risk(obstacle, gift):
        raise StoryError(explain_rejection(obstacle, gift))
    if params.fix not in matching_fixes(obstacle):
        raise StoryError(explain_fix(obstacle, params.fix))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        gift_cfg=gift,
        fix_cfg=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_species=params.hero_species,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_species=params.friend_species,
        elder_name=params.elder_name,
        elder_species=params.elder_species,
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
        print(f"{len(combos)} compatible (setting, obstacle, gift, fix) combos:\n")
        for setting_id, obstacle_id, gift_id, fix_id in combos:
            print(f"  {setting_id:10} {obstacle_id:16} {gift_id:12} {fix_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.gift} at {p.obstacle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
