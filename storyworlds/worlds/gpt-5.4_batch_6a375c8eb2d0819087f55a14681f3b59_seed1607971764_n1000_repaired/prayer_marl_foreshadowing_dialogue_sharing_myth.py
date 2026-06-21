#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prayer_marl_foreshadowing_dialogue_sharing_myth.py
==============================================================================

A standalone story world for a tiny mythic domain: in a dry season, a child
finds a sacred spring leaking away through a crack. Pale marl can seal the
stone, but only if enough hands share water fast enough to keep the marl wet
while a prayer is spoken. The story world prefers a small set of plausible,
state-driven variants over broad coverage.

The seed asked for:
- the words "prayer" and "marl"
- Foreshadowing, Dialogue, Sharing
- a style close to myth

This script models:
- typed entities with physical meters and emotional memes
- a small causal rule system
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in simulated world state
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt", "priestess"}
        male = {"boy", "man", "father", "grandfather", "uncle", "priest"}
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
            "priestess": "priestess",
            "priest": "priest",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class Shrine:
    id: str
    place: str
    keeper_title: str
    spring_name: str
    omen: str
    image: str
    proverb: str
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
class Damage:
    id: str
    label: str
    the: str
    leak_from: str
    repair_need: int
    risk: str
    after_image: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class HelperGroup:
    id: str
    label: str
    count: int
    arrival: str
    closing: str
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
class SharingMethod:
    id: str
    label: str
    min_helpers: int
    flow: int
    action: str
    closing: str
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
class PrayerKind:
    id: str
    label: str
    line1: str
    line2: str
    promise: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
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


# ---------------------------------------------------------------------------
# Rules
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


def _r_thirst(world: World) -> list[str]:
    spring = world.get("spring")
    village = world.get("village")
    if spring.meters["leaking"] < THRESHOLD:
        return []
    sig = ("thirst",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["thirst"] += 1
    for eid in ("hero", "keeper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return ["__thirst__"]


def _r_seal(world: World) -> list[str]:
    crack = world.get("crack")
    marl = world.get("marl")
    spring = world.get("spring")
    if marl.meters["pressed"] < THRESHOLD:
        return []
    if marl.meters["wet"] < crack.meters["need"]:
        return []
    sig = ("seal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crack.meters["sealed"] += 1
    spring.meters["leaking"] = 0.0
    spring.meters["flow"] += 1
    return ["__sealed__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="thirst", tag="physical", apply=_r_thirst),
    Rule(name="seal", tag="physical", apply=_r_seal),
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
# Constraint helpers
# ---------------------------------------------------------------------------
def repair_possible(damage: Damage, helpers: HelperGroup, sharing: SharingMethod) -> bool:
    return helpers.count >= sharing.min_helpers and min(helpers.count, sharing.flow) >= damage.repair_need


def selected_combos(
    shrine_filter: Optional[str] = None,
    damage_filter: Optional[str] = None,
    helpers_filter: Optional[str] = None,
    sharing_filter: Optional[str] = None,
) -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for shrine_id in SHRINES:
        if shrine_filter is not None and shrine_id != shrine_filter:
            continue
        for damage_id, damage in DAMAGES.items():
            if damage_filter is not None and damage_id != damage_filter:
                continue
            for helpers_id, helpers in HELPERS.items():
                if helpers_filter is not None and helpers_id != helpers_filter:
                    continue
                for sharing_id, sharing in SHARING.items():
                    if sharing_filter is not None and sharing_id != sharing_filter:
                        continue
                    if repair_possible(damage, helpers, sharing):
                        combos.append((shrine_id, damage_id, helpers_id, sharing_id))
    return combos


def valid_combos() -> list[tuple[str, str, str, str]]:
    return selected_combos()


def explain_rejection(damage: Damage, helpers: HelperGroup, sharing: SharingMethod) -> str:
    if helpers.count < sharing.min_helpers:
        return (
            f"(No story: {sharing.label} needs at least {sharing.min_helpers} helpers, "
            f"but {helpers.label} provides only {helpers.count}. The marl would dry "
            f"before enough water could be shared from hand to hand.)"
        )
    return (
        f"(No story: {damage.the} needs a steady wetting of {damage.repair_need}, "
        f"but {helpers.label} using {sharing.label} reaches only "
        f"{min(helpers.count, sharing.flow)}. The marl would crumble instead of sealing.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.temperament == "secretive" and HELPERS[params.helpers].count <= 2:
        return "delayed"
    return "shared_early"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def foreshadow(world: World, hero: Entity, keeper: Entity, shrine: Shrine) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In the season when dust lay on the olive leaves, {hero.id} climbed to {shrine.place}, "
        f"where {shrine.spring_name} sang under stone. {shrine.image}"
    )
    world.say(
        f'{keeper.label_word.capitalize()} said, "{shrine.proverb}"'
    )
    world.say(shrine.omen)


def discover(world: World, hero: Entity, damage: Damage) -> None:
    spring = world.get("spring")
    crack = world.get("crack")
    spring.meters["leaking"] += 1
    crack.meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} bent to listen, {hero.pronoun()} saw water slipping from {damage.leak_from}. "
        f"{damage.The} was drinking the spring."
    )


def hide_attempt(world: World, hero: Entity, damage: Damage) -> None:
    hero.memes["fear"] += 1
    hero.memes["burden"] += 1
    marl = world.get("marl")
    marl.meters["pressed"] += 1
    marl.meters["wet"] += 1
    world.say(
        f'{hero.id} whispered, "If I work quickly, perhaps I can mend {damage.the} alone."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} scooped up pale marl from the bank and pressed it into the broken stone, "
        f"but there was only one pair of hands and too little water to keep it soft."
    )
    world.say(
        "The marl darkened for a breath, then paled again and began to crack like dry bread."
    )


def ask_for_help(world: World, hero: Entity, keeper: Entity, helpers: HelperGroup) -> None:
    hero.memes["sharing"] += 1
    helper_ent = world.get("helpers")
    helper_ent.memes["care"] += 1
    world.say(
        f'{hero.id} ran back and cried, "Please come. The spring is escaping through the stone!"'
    )
    world.say(
        f'{keeper.label_word.capitalize()} answered, "No spring is saved by one child alone. Call {helpers.label}, and let every hand be kind."'
    )
    world.say(helpers.arrival)


def prepare_repair(world: World, helpers: HelperGroup, sharing: SharingMethod, damage: Damage) -> None:
    marl = world.get("marl")
    crack = world.get("crack")
    crack.meters["need"] = float(damage.repair_need)
    marl.meters["wet"] = float(min(helpers.count, sharing.flow))
    marl.meters["pressed"] += 1
    world.say(
        f"They gathered cool marl in a shallow basket. Then {sharing.action}, so the marl never dried while it was pressed into {damage.the}."
    )


def pray(world: World, hero: Entity, keeper: Entity, prayer: PrayerKind, shrine: Shrine) -> None:
    hero.memes["hope"] += 1
    keeper.memes["hope"] += 1
    world.say(
        f'As the last handful of marl was smoothed into place, {keeper.label_word} lifted both hands and said a prayer: '
        f'"{prayer.line1} {prayer.line2}"'
    )
    world.say(
        f'{hero.id} answered, "{prayer.promise}"'
    )
    world.say(
        f"For a heartbeat the hill was quiet, as if {shrine.spring_name} itself were listening."
    )


def restoration(world: World, damage: Damage, shrine: Shrine, helpers: HelperGroup, sharing: SharingMethod) -> None:
    spring = world.get("spring")
    propagate(world, narrate=False)
    spring.meters["blessing"] += 1
    world.get("village").meters["thirst"] = 0.0
    world.say(
        f"Then the thin hiss from {damage.the} stopped. Water rose clear in the basin and ran where it belonged."
    )
    world.say(
        f"{damage.after_image} {sharing.closing} {helpers.closing}"
    )
    world.say(
        f"People said that day that {shrine.spring_name} loved the prayer, but loved the sharing even more."
    )


# ---------------------------------------------------------------------------
# Main screenplay
# ---------------------------------------------------------------------------
def tell(
    shrine: Shrine,
    damage: Damage,
    helpers_cfg: HelperGroup,
    sharing: SharingMethod,
    prayer: PrayerKind,
    hero_name: str,
    hero_gender: str,
    keeper_type: str,
    temperament: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", attrs={"name": hero_name, "temperament": temperament}))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the keeper", role="keeper"))
    spring = world.add(Entity(id="spring", type="spring", label=shrine.spring_name))
    crack = world.add(Entity(id="crack", type="crack", label=damage.label))
    marl = world.add(Entity(id="marl", type="marl", label="marl"))
    village = world.add(Entity(id="village", type="village", label="the village"))
    helper_ent = world.add(Entity(id="helpers", kind="character", type="group", label=helpers_cfg.label, role="helpers"))

    crack.meters["need"] = float(damage.repair_need)
    spring.meters["flow"] = 0.0
    spring.meters["leaking"] = 0.0
    marl.meters["wet"] = 0.0
    marl.meters["pressed"] = 0.0
    village.meters["thirst"] = 0.0

    world.facts.update(
        shrine=shrine,
        damage=damage,
        helpers_cfg=helpers_cfg,
        sharing=sharing,
        prayer=prayer,
        hero=hero,
        keeper=keeper,
        spring=spring,
        crack=crack,
        marl=marl,
        village=village,
    )

    foreshadow(world, hero, keeper, shrine)
    world.para()
    discover(world, hero, damage)

    if temperament == "secretive" and helpers_cfg.count <= 2:
        world.para()
        hide_attempt(world, hero, damage)
        world.para()
        ask_for_help(world, hero, keeper, helpers_cfg)
        world.facts["outcome"] = "delayed"
        world.facts["asked_early"] = False
    else:
        world.para()
        ask_for_help(world, hero, keeper, helpers_cfg)
        world.facts["outcome"] = "shared_early"
        world.facts["asked_early"] = True

    world.para()
    prepare_repair(world, helpers_cfg, sharing, damage)
    pray(world, hero, keeper, prayer, shrine)
    restoration(world, damage, shrine, helpers_cfg, sharing)

    world.facts.update(
        sealed=world.get("crack").meters["sealed"] >= THRESHOLD,
        thirst_ended=world.get("village").meters["thirst"] < THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SHRINES = {
    "hill_spring": Shrine(
        id="hill_spring",
        place="the hill spring of Dawn",
        keeper_title="grandmother",
        spring_name="the Spring of Dawn",
        omen="Before noon, a lizard flicked across the warm lip of the basin and vanished into a seam in the stone.",
        image="A laurel tree leaned over it, and its shadow looked like a dark hand spread on the rock.",
        proverb="When water is hidden, water grows lonely.",
        tags={"spring", "myth", "sharing"},
    ),
    "river_steps": Shrine(
        id="river_steps",
        place="the river steps of Sel",
        keeper_title="priest",
        spring_name="Sel's Little Mouth",
        omen="Even in the bright sun, one swallow circled low and cried as if warning the stones.",
        image="Old carved fish shone there, smooth from many hands and many years.",
        proverb="A spring remembers the hands that pass its cup.",
        tags={"river", "myth", "sharing"},
    ),
    "olive_court": Shrine(
        id="olive_court",
        place="the olive court of the old shrine",
        keeper_title="priestess",
        spring_name="the Hidden Vein",
        omen="A single olive leaf spun in the trickle below, though no wind touched the court.",
        image="Three worn pillars stood there, pale as moon-bones in the heat.",
        proverb="Stone keeps water only when hearts do not close.",
        tags={"olive", "myth", "sharing"},
    ),
}

DAMAGES = {
    "basin_rim": Damage(
        id="basin_rim",
        label="basin rim",
        the="the basin rim",
        leak_from="a crack in the basin rim",
        repair_need=2,
        risk="the lip would keep spilling the spring onto the dust",
        after_image="Soon even the sparrows came back to the edge to drink.",
        tags={"crack", "spring"},
    ),
    "channel_wall": Damage(
        id="channel_wall",
        label="channel wall",
        the="the channel wall",
        leak_from="a split in the channel wall",
        repair_need=3,
        risk="the little runnel would wander away before reaching the figs below",
        after_image="The fig roots drank again, and the leaves stopped curling at their tips.",
        tags={"channel", "figs"},
    ),
    "cistern_seam": Damage(
        id="cistern_seam",
        label="cistern seam",
        the="the cistern seam",
        leak_from="a dark line in the cistern seam",
        repair_need=4,
        risk="the cistern would empty itself stone by stone",
        after_image="By evening the jars filled without scraping the bottom for the last drops.",
        tags={"cistern", "water"},
    ),
}

HELPERS = {
    "siblings": HelperGroup(
        id="siblings",
        label="the two older children from the path below",
        count=2,
        arrival="Two older children came at once, breathing hard from the climb.",
        closing="They grinned at one another as if they had helped mend a star.",
        tags={"children", "sharing"},
    ),
    "neighbors": HelperGroup(
        id="neighbors",
        label="three neighbors from the fig terraces",
        count=3,
        arrival="Three neighbors left their baskets among the fig terraces and hurried up together.",
        closing="They carried the empty bowls home laughing, with wet lines shining on their wrists.",
        tags={"neighbors", "sharing"},
    ),
    "village": HelperGroup(
        id="village",
        label="half the village",
        count=5,
        arrival="Word flew downhill, and soon half the village climbed the path with bowls and jars.",
        closing="When they went home, each family carried water and a brighter face.",
        tags={"village", "sharing"},
    ),
}

SHARING = {
    "cup_line": SharingMethod(
        id="cup_line",
        label="a line of passing cups",
        min_helpers=2,
        flow=2,
        action="they made a line of passing cups from the spring to the broken stone",
        closing="The cups kept flashing in the sun like small moons",
        tags={"cups", "sharing"},
    ),
    "bowl_circle": SharingMethod(
        id="bowl_circle",
        label="a circle of clay bowls",
        min_helpers=3,
        flow=3,
        action="they knelt in a circle of clay bowls, passing water from palm to palm and bowl to bowl",
        closing="The clay bowls made a little ring like a second shrine around the first",
        tags={"bowls", "sharing"},
    ),
    "jar_chain": SharingMethod(
        id="jar_chain",
        label="a chain of little jars",
        min_helpers=4,
        flow=5,
        action="they formed a chain of little jars so quickly that every fresh splash reached the marl before the sun could bite it dry",
        closing="The jars clicked softly together like friendly teeth",
        tags={"jars", "sharing"},
    ),
}

PRAYERS = {
    "dawn_prayer": PrayerKind(
        id="dawn_prayer",
        label="dawn prayer",
        line1="Bright spring, keep your silver road.",
        line2="Do not go wandering into the dust.",
        promise="We will share your gift and remember the thirsty.",
        tags={"prayer", "spring"},
    ),
    "river_prayer": PrayerKind(
        id="river_prayer",
        label="river prayer",
        line1="Clear mother under stone, turn your face back to us.",
        line2="Let the cool path be whole again.",
        promise="No cup here will close against a neighbor.",
        tags={"prayer", "river"},
    ),
    "olive_prayer": PrayerKind(
        id="olive_prayer",
        label="olive prayer",
        line1="Hidden vein, wake softly beneath these roots.",
        line2="Hold fast where kind hands mend you.",
        promise="What flows to one roof will be shared with all.",
        tags={"prayer", "olive"},
    ),
}

GIRL_NAMES = ["Ione", "Dara", "Lysa", "Mira", "Thale", "Nera"]
BOY_NAMES = ["Tarin", "Lykos", "Pavel", "Nikos", "Damon", "Ivor"]
TEMPERAMENTS = ["openhearted", "careful", "secretive"]
KEEPERS = ["grandmother", "grandfather", "priestess", "priest"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    shrine: str
    damage: str
    helpers: str
    sharing: str
    prayer: str
    hero_name: str
    hero_gender: str
    keeper: str
    temperament: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "marl": [
        (
            "What is marl?",
            "Marl is a soft earth made from clay and lime. When it is damp, people can press it into cracks to help seal stone."
        )
    ],
    "prayer": [
        (
            "What is a prayer?",
            "A prayer is spoken words asking for help, giving thanks, or making a promise. People often say a prayer when something matters deeply to them."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground by itself. People may drink from it or guide it into channels and basins."
        )
    ],
    "sharing": [
        (
            "Why can sharing help in an emergency?",
            "Sharing lets many people do one hard job together. With more hands, water, tools, or food can reach the place that needs help much faster."
        )
    ],
    "crack": [
        (
            "Why is a crack in a water basin a problem?",
            "A crack lets water leak away instead of staying where people need it. If the leak keeps going, the basin or cistern can slowly empty."
        )
    ],
    "cistern": [
        (
            "What is a cistern?",
            "A cistern is a large container or stone tank that stores water. People use it to keep water for later."
        )
    ],
    "channel": [
        (
            "What is a water channel?",
            "A water channel is a little path that guides water from one place to another. If the wall breaks, the water can run the wrong way."
        )
    ],
}

KNOWLEDGE_ORDER = ["prayer", "marl", "spring", "sharing", "crack", "channel", "cistern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shrine = f["shrine"]
    damage = f["damage"]
    prayer = f["prayer"]
    hero = f["hero"]
    helpers = f["helpers_cfg"]
    return [
        f'Write a short mythic story for a 3-to-5-year-old that includes the words "prayer" and "marl".',
        f"Tell a small myth where {hero.label}, a child at {shrine.place}, discovers that {damage.the} is leaking and must ask others for help.",
        f"Write a gentle myth with foreshadowing, dialogue, and sharing, where {helpers.label} help mend a spring while a {prayer.label} is spoken.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    shrine = f["shrine"]
    damage = f["damage"]
    helpers = f["helpers_cfg"]
    sharing = f["sharing"]
    prayer = f["prayer"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who watched over {shrine.spring_name}, and {keeper.label_word}, who helped guide the repair."
        ),
        (
            "What was the problem at the spring?",
            f"Water was slipping out through {damage.leak_from}, so the spring was being lost into the dust. That mattered because {damage.risk}."
        ),
        (
            "What did they use to mend the stone?",
            "They used marl, pressing the damp earth into the crack. The marl had to stay wet, or it would dry, shrink, and fail to seal the leak."
        ),
        (
            "Why did other people need to help?",
            f"They needed enough hands to keep water moving while the marl was pressed in. {sharing.label.capitalize()} worked because {helpers.label} could share the work together."
        ),
        (
            "What prayer did they say?",
            f'They said a {prayer.label}, asking the spring to stay and promising to share its gift. The prayer mattered because it joined their words to their work.'
        ),
    ]
    if outcome == "delayed":
        qa.append(
            (
                f"Did {hero.label} ask for help right away?",
                f"No. {hero.label} first tried to fix the leak alone, but there was too little water and too few hands to keep the marl soft. After that failure, {hero.pronoun()} called others, and the shared repair worked."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.label} help save the spring?",
                f"{hero.label} told the truth quickly and asked others to come. Because help came early, the marl stayed wet and the crack sealed before more water could escape."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The leak stopped, the water ran where it belonged, and {damage.after_image} The ending proves the spring was restored because the village could trust its water again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"prayer", "marl", "spring", "sharing", "crack"}
    if f["damage"].id == "cistern_seam":
        tags.add("cistern")
    if f["damage"].id == "channel_wall":
        tags.add("channel")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, D, H, Sh) :- shrine(S), damage(D), helpers(H), sharing(Sh),
                      helper_count(H, HC), min_helpers(Sh, MH), HC >= MH,
                      flow(Sh, FL), repair_need(D, RN), FL >= RN, HC >= RN.

delayed :- temperament(secretive), helper_count_choice(HC), HC <= 2.
outcome(delayed) :- delayed.
outcome(shared_early) :- not delayed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHRINES:
        lines.append(asp.fact("shrine", sid))
    for did, damage in DAMAGES.items():
        lines.append(asp.fact("damage", did))
        lines.append(asp.fact("repair_need", did, damage.repair_need))
    for hid, helpers in HELPERS.items():
        lines.append(asp.fact("helpers", hid))
        lines.append(asp.fact("helper_count", hid, helpers.count))
    for shid, sharing in SHARING.items():
        lines.append(asp.fact("sharing", shid))
        lines.append(asp.fact("min_helpers", shid, sharing.min_helpers))
        lines.append(asp.fact("flow", shid, sharing.flow))
    for temperament in TEMPERAMENTS:
        lines.append(asp.fact("temperament_name", temperament))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("temperament", params.temperament),
            asp.fact("helper_count_choice", HELPERS[params.helpers].count),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        shrine="hill_spring",
        damage="basin_rim",
        helpers="siblings",
        sharing="cup_line",
        prayer="dawn_prayer",
        hero_name="Ione",
        hero_gender="girl",
        keeper="grandmother",
        temperament="secretive",
    ),
    StoryParams(
        shrine="river_steps",
        damage="channel_wall",
        helpers="neighbors",
        sharing="bowl_circle",
        prayer="river_prayer",
        hero_name="Tarin",
        hero_gender="boy",
        keeper="priest",
        temperament="careful",
    ),
    StoryParams(
        shrine="olive_court",
        damage="cistern_seam",
        helpers="village",
        sharing="jar_chain",
        prayer="olive_prayer",
        hero_name="Mira",
        hero_gender="girl",
        keeper="priestess",
        temperament="openhearted",
    ),
    StoryParams(
        shrine="hill_spring",
        damage="channel_wall",
        helpers="village",
        sharing="jar_chain",
        prayer="dawn_prayer",
        hero_name="Lykos",
        hero_gender="boy",
        keeper="grandfather",
        temperament="secretive",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a leaking spring, marl, prayer, and shared repair in a mythic style."
    )
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--helpers", choices=HELPERS)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--prayer", choices=PRAYERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.damage and args.helpers and args.sharing:
        damage = DAMAGES[args.damage]
        helpers = HELPERS[args.helpers]
        sharing = SHARING[args.sharing]
        if not repair_possible(damage, helpers, sharing):
            raise StoryError(explain_rejection(damage, helpers, sharing))

    combos = selected_combos(
        shrine_filter=args.shrine,
        damage_filter=args.damage,
        helpers_filter=args.helpers,
        sharing_filter=args.sharing,
    )
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shrine_id, damage_id, helpers_id, sharing_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice(KEEPERS)
    prayer = args.prayer or rng.choice(sorted(PRAYERS))
    temperament = args.temperament or rng.choice(TEMPERAMENTS)

    return StoryParams(
        shrine=shrine_id,
        damage=damage_id,
        helpers=helpers_id,
        sharing=sharing_id,
        prayer=prayer,
        hero_name=hero_name,
        hero_gender=hero_gender,
        keeper=keeper,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES:
        raise StoryError(f"(Unknown shrine: {params.shrine})")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage: {params.damage})")
    if params.helpers not in HELPERS:
        raise StoryError(f"(Unknown helpers: {params.helpers})")
    if params.sharing not in SHARING:
        raise StoryError(f"(Unknown sharing method: {params.sharing})")
    if params.prayer not in PRAYERS:
        raise StoryError(f"(Unknown prayer: {params.prayer})")
    if params.keeper not in KEEPERS:
        raise StoryError(f"(Unknown keeper: {params.keeper})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")

    damage = DAMAGES[params.damage]
    helpers = HELPERS[params.helpers]
    sharing = SHARING[params.sharing]
    if not repair_possible(damage, helpers, sharing):
        raise StoryError(explain_rejection(damage, helpers, sharing))

    world = tell(
        shrine=SHRINES[params.shrine],
        damage=damage,
        helpers_cfg=helpers,
        sharing=sharing,
        prayer=PRAYERS[params.prayer],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        keeper_type=params.keeper,
        temperament=params.temperament,
    )
    # Replace internal id with display name in rendered story.
    story = world.render().replace("hero", params.hero_name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shrine, damage, helpers, sharing) combos:\n")
        for shrine, damage, helpers, sharing in combos:
            print(f"  {shrine:12} {damage:12} {helpers:10} {sharing}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.damage} at {p.shrine} "
                f"({p.helpers}, {p.sharing}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
