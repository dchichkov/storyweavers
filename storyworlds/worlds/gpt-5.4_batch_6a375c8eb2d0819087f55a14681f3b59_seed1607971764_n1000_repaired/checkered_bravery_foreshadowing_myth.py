#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py
==================================================================

A standalone storyworld for a small mythic domain: when an omen appears above a
village's checkered temple court, a child must carry the right offering to the
right shrine before night. The world models omen, fear, courage, route, helper,
and resolution, so the prose changes with simulated state instead of swapping
nouns into one frozen paragraph.

The core shape is:

    omen appears -> village fear rises
    elder interprets omen -> foreshadowing becomes a concrete task
    child accepts quest -> courage rises
    child sets out -> danger and helper effects fire
    if courage is enough -> offering reaches shrine, spirit sleeps, village rests
    else -> child returns honestly, and the village solves it together at dawn

Run it
------
    python storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py
    python storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py --omen red_comet --spirit river_serpent --offering milk_bowl --helper fisher_skiff
    python storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py --offering honey_cake --spirit river_serpent
    python storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/checkered_bravery_foreshadowing_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
QUEST_BONUS = 1
BRAVERY_SCORES = {"timid": 0, "steady": 1, "bold": 2, "faithful": 1}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "priestess"}
        male = {"boy", "man", "grandfather", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Omen:
    id: str
    sign: str
    sky_text: str
    warns: str
    whisper: str
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
class Spirit:
    id: str
    title: str
    route_tag: str
    route_text: str
    shrine: str
    danger: int
    hush_text: str
    stir_text: str
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
class Offering:
    id: str
    label: str
    phrase: str
    appeases: str
    place_text: str
    gift_text: str
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
class Helper:
    id: str
    label: str
    phrase: str
    supports: str
    power: int
    assist_text: str
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


def _r_omen_fear(world: World) -> list[str]:
    out: list[str] = []
    village = world.get("village")
    spirit = world.get("spirit")
    hero = world.get("hero")
    if village.meters["omen_seen"] >= THRESHOLD and spirit.meters["awake"] >= THRESHOLD:
        sig = ("omen_fear", spirit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            village.memes["fear"] += 1
            hero.memes["foreboding"] += 1
            out.append("__omen__")
    return out


def _r_route_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    spirit = world.get("spirit")
    if hero.meters["on_route"] >= THRESHOLD and spirit.meters["awake"] >= THRESHOLD:
        sig = ("route_fear", spirit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("__route__")
    return out


def _r_helper_courage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    spirit = world.get("spirit")
    if hero.meters["on_route"] >= THRESHOLD and helper.attrs.get("supports") == spirit.attrs.get("route_tag"):
        sig = ("helper_courage", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["courage"] += float(helper.attrs.get("power", 0))
            out.append("__helper__")
    return out


def _r_offering_soothes(world: World) -> list[str]:
    out: list[str] = []
    offering = world.get("offering")
    spirit = world.get("spirit")
    village = world.get("village")
    hero = world.get("hero")
    if offering.meters["placed"] >= THRESHOLD and offering.attrs.get("appeases") == spirit.id:
        sig = ("offering_soothes", spirit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            spirit.meters["awake"] = 0.0
            spirit.meters["sleeping"] += 1
            village.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            out.append("__soothed__")
    return out


CAUSAL_RULES = [
    Rule(name="omen_fear", tag="emotional", apply=_r_omen_fear),
    Rule(name="route_fear", tag="emotional", apply=_r_route_fear),
    Rule(name="helper_courage", tag="emotional", apply=_r_helper_courage),
    Rule(name="offering_soothes", tag="physical", apply=_r_offering_soothes),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def base_courage(trait: str) -> int:
    return BRAVERY_SCORES[trait]


def success_possible(trait: str, helper: Helper, spirit: Spirit) -> bool:
    return base_courage(trait) + QUEST_BONUS + helper.power >= spirit.danger


def valid_combo(omen: Omen, spirit: Spirit, offering: Offering, helper: Helper) -> bool:
    return (
        omen.warns == spirit.id
        and offering.appeases == spirit.id
        and helper.supports == spirit.route_tag
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for omen_id, omen in OMENS.items():
        for spirit_id, spirit in SPIRITS.items():
            for offering_id, offering in OFFERINGS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(omen, spirit, offering, helper):
                        combos.append((omen_id, spirit_id, offering_id, helper_id))
    return combos


def predict_quest(world: World, trait: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    helper = sim.get("helper")
    spirit = sim.get("spirit")
    hero.memes["courage"] = float(base_courage(trait) + QUEST_BONUS)
    hero.meters["on_route"] += 1
    propagate(sim, narrate=False)
    total_courage = int(hero.memes["courage"])
    return {
        "danger": spirit.attrs["danger"],
        "courage": total_courage,
        "success": total_courage >= spirit.attrs["danger"],
        "helper": helper.label,
    }


def introduce(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"In the old days, when the gods still leaned down to listen, {hero.id} lived "
        f"beside a temple court paved in checkered stone. {elder.id}, the village "
        f"{elder.label_word}, taught the children that signs in the sky were never empty."
    )


def omen_appears(world: World, omen: Omen) -> None:
    village = world.get("village")
    spirit = world.get("spirit")
    village.meters["omen_seen"] += 1
    spirit.meters["awake"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That evening, {omen.sky_text}. At once the old warning came back to every door: "
        f"{omen.whisper}."
    )


def interpret(world: World, elder: Entity, hero: Entity, omen: Omen, spirit: Spirit, offering: Offering) -> None:
    pred = predict_quest(world, world.facts["trait"])
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_courage"] = pred["courage"]
    world.say(
        f'{elder.id} touched the temple rail and said, "{omen.sign} means {spirit.title} is stirring. '
        f'Only {offering.phrase} at {spirit.shrine} will quiet {spirit.pronoun("object") if hasattr(spirit, "pronoun") else "it"} before night."'
    )
    world.say(
        f"{hero.id} looked from the darkening sky to {spirit.route_text}. The path itself seemed to answer the omen."
    )


def volunteer(world: World, hero: Entity, elder: Entity, helper: Helper) -> None:
    hero.memes["courage"] = float(base_courage(world.facts["trait"]))
    hero.memes["courage"] += QUEST_BONUS
    hero.memes["duty"] += 1
    world.say(
        f'"Then I will go," said {hero.id}. The words came out small at first, but they grew strong as they crossed the court.'
    )
    world.say(
        f'{elder.id} placed {helper.phrase} in {hero.pronoun("possessive")} hands. "{helper.assist_text}," {elder.pronoun()} said.'
    )


def set_out(world: World, hero: Entity, spirit: Spirit, helper: Helper) -> None:
    hero.meters["on_route"] += 1
    propagate(world, narrate=False)
    fear_bit = ""
    if hero.memes["fear"] >= THRESHOLD:
        fear_bit = " Even so, the dark water and long shadows tugged at the edge of the hero's heart."
    world.say(
        f"{hero.id} stepped away from the warm lamps and followed {spirit.route_text}. "
        f"{helper.phrase.capitalize()} went with {hero.pronoun('object')}, and {helper.assist_text}.{fear_bit}"
    )


def turn_success(world: World, hero: Entity, spirit: Spirit, offering: Offering, helper: Helper) -> None:
    offering_ent = world.get("offering")
    offering_ent.meters["placed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A gust rose where {spirit.title} was waking, but {helper.phrase} held true. "
        f"{hero.id} did not run."
    )
    world.say(
        f"At {spirit.shrine}, {hero.pronoun()} set down {offering.phrase} {offering.place_text}. "
        f"{offering.gift_text}."
    )


def ending_success(world: World, hero: Entity, elder: Entity, spirit: Spirit) -> None:
    world.say(
        f"Then the sign in the sky softened, and {spirit.hush_text}. From the temple court, the villagers saw the night grow gentle again."
    )
    world.say(
        f"When {hero.id} came home, {elder.id} bowed as if greeting a young hero from the oldest songs. "
        f"The checkered stones shone under lamplight, and no one would ever look at them quite the same way again."
    )


def turn_return(world: World, hero: Entity, elder: Entity, spirit: Spirit, helper: Helper) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"But halfway along, {spirit.stir_text}. {helper.phrase.capitalize()} could help, yet the path still felt larger than one small child."
    )
    world.say(
        f"{hero.id} stopped, hugged the gift close, and chose not to pretend to be fearless. "
        f"{hero.pronoun().capitalize()} turned back and told {elder.id} the truth."
    )


def ending_return(world: World, hero: Entity, elder: Entity, spirit: Spirit, offering: Offering) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'{elder.id} did not scold. "{hero.pronoun("possessive").capitalize()} brave enough to speak the truth," {elder.pronoun()} said, '
        f'"and brave enough to ask for many hands when many hands are needed."'
    )
    world.say(
        f"Before dawn, the whole village crossed the court together, carrying drums, lamps, and {offering.phrase}. "
        f"At sunrise they reached {spirit.shrine}, and {spirit.hush_text}."
    )
    world.say(
        f"After that, the children of the village said that bravery was not only a lonely step into darkness. "
        f"Sometimes it was the honest step back that brought the whole village forward."
    )


def tell(
    omen: Omen,
    spirit_cfg: Spirit,
    offering_cfg: Offering,
    helper_cfg: Helper,
    hero_name: str = "Ione",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "steady",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="keeper", role="elder"))
    village = world.add(Entity(id="village", type="village", label="the village"))
    spirit = world.add(
        Entity(
            id="spirit",
            type="spirit",
            label=spirit_cfg.title,
            role="spirit",
            attrs={"route_tag": spirit_cfg.route_tag, "danger": spirit_cfg.danger},
            tags=set(spirit_cfg.tags),
        )
    )
    offering = world.add(
        Entity(
            id="offering",
            type="offering",
            label=offering_cfg.label,
            attrs={"appeases": offering_cfg.appeases},
            tags=set(offering_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="helper",
            label=helper_cfg.label,
            attrs={"supports": helper_cfg.supports, "power": helper_cfg.power},
            tags=set(helper_cfg.tags),
        )
    )

    world.facts["trait"] = trait
    world.facts["hero_name"] = hero_name
    world.facts["hero_gender"] = hero_gender
    world.facts["elder_type"] = elder_type
    world.facts["omen"] = omen
    world.facts["spirit_cfg"] = spirit_cfg
    world.facts["offering_cfg"] = offering_cfg
    world.facts["helper_cfg"] = helper_cfg

    introduce(world, hero, elder)
    omen_appears(world, omen)

    world.para()
    interpret(world, elder, hero, omen, spirit_cfg, offering_cfg)
    volunteer(world, hero, elder, helper_cfg)

    world.para()
    set_out(world, hero, spirit_cfg, helper_cfg)
    saved = success_possible(trait, helper_cfg, spirit_cfg)
    if saved:
        turn_success(world, hero, spirit_cfg, offering_cfg, helper_cfg)
        world.para()
        ending_success(world, hero, elder, spirit_cfg)
        outcome = "saved"
    else:
        turn_return(world, hero, elder, spirit_cfg, helper_cfg)
        world.para()
        ending_return(world, hero, elder, spirit_cfg, offering_cfg)
        outcome = "dawn_help"

    world.facts.update(
        hero=hero,
        elder=elder,
        village=village,
        spirit=world.get("spirit"),
        offering=world.get("offering"),
        helper=world.get("helper"),
        omen_seen=village.meters["omen_seen"] >= THRESHOLD,
        outcome=outcome,
        saved=outcome == "saved",
        truth_told=outcome == "dawn_help",
    )
    return world


OMENS = {
    "red_comet": Omen(
        id="red_comet",
        sign="The red comet",
        sky_text="a red comet unstitched the western sky above the temple roof",
        warns="river_serpent",
        whisper="when that red fire walks the heavens, the River Serpent tests the ford",
        tags={"comet", "omen", "river"},
    ),
    "ash_ring": Omen(
        id="ash_ring",
        sign="The ash ring around the moon",
        sky_text="an ash-gray ring closed around the moon like a warning thumb",
        warns="mountain_lion",
        whisper="when the moon wears ash, the Mountain Lion wakes on the high stair",
        tags={"moon", "omen", "mountain"},
    ),
    "still_reeds": Omen(
        id="still_reeds",
        sign="The still reeds",
        sky_text="the marsh reeds went still though the evening wind kept moving everywhere else",
        warns="mist_crane",
        whisper="when even the reeds refuse to whisper, the Mist Crane is abroad",
        tags={"reeds", "omen", "marsh"},
    ),
}

SPIRITS = {
    "river_serpent": Spirit(
        id="river_serpent",
        title="the River Serpent",
        route_tag="water_edge",
        route_text="the slick checkered stepping-stones of the ford",
        shrine="the river arch",
        danger=3,
        hush_text="the black water flattened, and the river curled itself back into one silver band",
        stir_text="the water slapped the stones in a hard, cold rhythm like scales against a drum",
        tags={"river", "serpent", "shrine"},
    ),
    "mountain_lion": Spirit(
        id="mountain_lion",
        title="the Mountain Lion",
        route_tag="heights",
        route_text="the wind-cut stair that climbed to the sun ledge",
        shrine="the sun ledge",
        danger=2,
        hush_text="the stone wind gentled, and the mountain kept only its own deep breathing",
        stir_text="a tawny roar rolled down the rocks and made the stair feel narrow as a ribbon",
        tags={"mountain", "lion", "shrine"},
    ),
    "mist_crane": Spirit(
        id="mist_crane",
        title="the Mist Crane",
        route_tag="marsh",
        route_text="the dim marsh causeway where lantern-light could lose its own feet",
        shrine="the reed gate",
        danger=2,
        hush_text="the white mist thinned into morning threads, and the marsh pools showed the stars again",
        stir_text="the mist rose in pale wings and turned every pool into a watching eye",
        tags={"marsh", "crane", "shrine"},
    ),
}

OFFERINGS = {
    "milk_bowl": Offering(
        id="milk_bowl",
        label="milk bowl",
        phrase="a bowl of moon-milk",
        appeases="river_serpent",
        place_text="beneath the arch where the current bent inward",
        gift_text="The current took the white offering as gently as a sleeping child takes a blanket",
        tags={"offering", "milk", "river"},
    ),
    "honey_cake": Offering(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake",
        appeases="mountain_lion",
        place_text="on the flat altar of warm stone",
        gift_text="The sweet smell climbed into the high air, and the hard rocks seemed to remember summer",
        tags={"offering", "honey", "mountain"},
    ),
    "silver_bell": Offering(
        id="silver_bell",
        label="silver bell",
        phrase="a silver bell tied with reed thread",
        appeases="mist_crane",
        place_text="upon the moss-dark gatepost",
        gift_text="Its clear note trembled once, and the listening fog drew back to hear it better",
        tags={"offering", "bell", "marsh"},
    ),
}

HELPERS = {
    "fisher_skiff": Helper(
        id="fisher_skiff",
        label="fisher's skiff",
        phrase="the little fisher's skiff",
        supports="water_edge",
        power=2,
        assist_text="Keep the bow straight and the river will remember you are passing, not fighting",
        tags={"boat", "river"},
    ),
    "river_rope": Helper(
        id="river_rope",
        label="river rope",
        phrase="the knotted river rope",
        supports="water_edge",
        power=1,
        assist_text="Grip each knot and step where the old heroes stepped",
        tags={"rope", "river"},
    ),
    "eagle_guide": Helper(
        id="eagle_guide",
        label="eagle feather guide",
        phrase="an eagle-feather guide",
        supports="heights",
        power=2,
        assist_text="Hold it into the wind and the high path will show its honest edge",
        tags={"feather", "mountain"},
    ),
    "bronze_sandals": Helper(
        id="bronze_sandals",
        label="bronze sandals",
        phrase="the bronze sandals of the shrine runners",
        supports="heights",
        power=1,
        assist_text="Plant your heels well and let the stair feel your weight",
        tags={"sandals", "mountain"},
    ),
    "reed_lantern": Helper(
        id="reed_lantern",
        label="reed lantern",
        phrase="the reed lantern",
        supports="marsh",
        power=1,
        assist_text="Lift it high and the mist will have to make room for light",
        tags={"lantern", "marsh"},
    ),
    "heron_skiff": Helper(
        id="heron_skiff",
        label="heron skiff",
        phrase="the white heron skiff",
        supports="marsh",
        power=2,
        assist_text="Push softly and the marsh paths hidden under water will rise to meet you",
        tags={"boat", "marsh"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Mira", "Nysa", "Eirene", "Daphne"]
BOY_NAMES = ["Pelas", "Orin", "Timon", "Leander", "Nikos", "Ilias"]
TRAITS = ["timid", "steady", "bold", "faithful"]


@dataclass
class StoryParams:
    omen: str
    spirit: str
    offering: str
    helper: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "omen": [(
        "What is an omen in a myth?",
        "An omen is a sign people believe points ahead to something important. In myths, an omen often warns that trouble is coming before anyone can see the trouble itself."
    )],
    "comet": [(
        "What is a comet?",
        "A comet is a ball of ice and dust that travels through space. When it comes near the sun, it can glow and leave a bright tail in the sky."
    )],
    "moon": [(
        "What is a ring around the moon?",
        "A ring around the moon is a circle of light that can appear when moonlight shines through tiny ice crystals high in the sky. People in old stories often treated it like a warning sign."
    )],
    "river": [(
        "Why can a river crossing be dangerous?",
        "Wet stones can be slippery, and moving water can push harder than it looks. That is why even a small crossing can feel risky."
    )],
    "mountain": [(
        "Why is a mountain stair hard to climb?",
        "A mountain stair can be steep, windy, and narrow. Your legs get tired, and the height can make each careful step matter."
    )],
    "marsh": [(
        "What is a marsh?",
        "A marsh is wet land with grasses and shallow water. It can be muddy and misty, so paths there are easy to lose."
    )],
    "shrine": [(
        "What is a shrine?",
        "A shrine is a small sacred place where people leave gifts or prayers. In myths, it is often where humans and gods seem closest."
    )],
    "offering": [(
        "What is an offering?",
        "An offering is a gift given with respect. In many old tales, people give offerings to ask for peace, thanks, or help."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery is doing what is right even when you feel afraid. It does not mean having no fear at all."
    )],
}
KNOWLEDGE_ORDER = ["omen", "comet", "moon", "river", "mountain", "marsh", "shrine", "offering", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    omen = f["omen"]
    spirit = f["spirit_cfg"]
    offering = f["offering_cfg"]
    helper = f["helper_cfg"]
    if f["outcome"] == "saved":
        return [
            'Write a short child-facing myth that includes the word "checkered" and uses foreshadowing through a sky omen.',
            f"Tell a mythic story where {hero.label} sees {omen.sign.lower()}, bravely carries {offering.phrase} with {helper.phrase}, and calms {spirit.title}.",
            f"Write a simple myth about bravery in which a child crosses danger after an omen warns the village, and the ending image shows what peace looks like afterward.",
        ]
    return [
        'Write a short child-facing myth that includes the word "checkered" and uses foreshadowing through a sky omen.',
        f"Tell a mythic story where {hero.label} sets out after {omen.sign.lower()} but learns that honesty and asking for help can also be brave.",
        f"Write a myth for young children where an omen warns a village, a child begins a quest, and the ending teaches that bravery is not only going alone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    omen = f["omen"]
    spirit_cfg = f["spirit_cfg"]
    offering_cfg = f["offering_cfg"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child from a village with a checkered temple court, and {elder.id}, the old {elder.type} who keeps the warnings. The story turns when an omen says danger is waking."
        ),
        (
            "What foreshadowed the trouble?",
            f"{omen.sign} appeared before the real danger reached the village. That sign warned everyone that {spirit_cfg.title} was already stirring."
        ),
        (
            f"Why did {hero.label} set out?",
            f"{hero.label} went because only {offering_cfg.phrase} at {spirit_cfg.shrine} could quiet {spirit_cfg.title}. The child chose to act before night, which is the brave middle turn of the story."
        ),
        (
            f"What did {elder.id} give {hero.pronoun('object')}?",
            f"{elder.id} gave {hero.pronoun('object')} {helper_cfg.phrase}. It was meant to help on {spirit_cfg.route_text} because that route fit the kind of danger they faced."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How did {hero.label} save the village?",
                f"{hero.label} kept going to {spirit_cfg.shrine} and placed {offering_cfg.phrase} there. Because the gift matched the waking spirit and the helper suited the path, the danger quieted instead of growing."
            )
        )
        qa.append(
            (
                "How did the ending show that things had changed?",
                f"The sky softened and {spirit_cfg.hush_text}. The villagers could see peace from the temple court, so the last image proved the omen had been answered."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} turn back?",
                f"{hero.label} felt that the path had become too much for one small child. Turning back was not cowardice in this story, because {hero.pronoun()} told the truth quickly enough for the village to act together."
            )
        )
        qa.append(
            (
                "What did the child learn about bravery?",
                f"The child learned that bravery is not only walking alone into danger. Sometimes bravery means admitting the danger is too big and calling others to help before it gets worse."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"omen", "shrine", "offering", "bravery"}
    omen = f["omen"]
    if "comet" in omen.tags:
        tags.add("comet")
    if "moon" in omen.tags:
        tags.add("moon")
    if "river" in f["spirit_cfg"].tags:
        tags.add("river")
    if "mountain" in f["spirit_cfg"].tags:
        tags.add("mountain")
    if "marsh" in f["spirit_cfg"].tags:
        tags.add("marsh")
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != 0}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        omen="red_comet",
        spirit="river_serpent",
        offering="milk_bowl",
        helper="fisher_skiff",
        name="Ione",
        gender="girl",
        elder="grandmother",
        trait="bold",
    ),
    StoryParams(
        omen="ash_ring",
        spirit="mountain_lion",
        offering="honey_cake",
        helper="bronze_sandals",
        name="Timon",
        gender="boy",
        elder="priest",
        trait="steady",
    ),
    StoryParams(
        omen="still_reeds",
        spirit="mist_crane",
        offering="silver_bell",
        helper="reed_lantern",
        name="Mira",
        gender="girl",
        elder="priestess",
        trait="timid",
    ),
    StoryParams(
        omen="ash_ring",
        spirit="mountain_lion",
        offering="honey_cake",
        helper="eagle_guide",
        name="Orin",
        gender="boy",
        elder="grandfather",
        trait="faithful",
    ),
    StoryParams(
        omen="still_reeds",
        spirit="mist_crane",
        offering="silver_bell",
        helper="heron_skiff",
        name="Nysa",
        gender="girl",
        elder="grandmother",
        trait="steady",
    ),
]


def explain_rejection(omen_id: str, spirit_id: str, offering_id: str, helper_id: str) -> str:
    parts = []
    if omen_id in OMENS and spirit_id in SPIRITS and OMENS[omen_id].warns != spirit_id:
        parts.append(
            f"{OMENS[omen_id].sign} warns of {SPIRITS[OMENS[omen_id].warns].title}, not {SPIRITS[spirit_id].title}"
        )
    if offering_id in OFFERINGS and spirit_id in SPIRITS and OFFERINGS[offering_id].appeases != spirit_id:
        parts.append(
            f"{OFFERINGS[offering_id].phrase} would not soothe {SPIRITS[spirit_id].title}"
        )
    if helper_id in HELPERS and spirit_id in SPIRITS and HELPERS[helper_id].supports != SPIRITS[spirit_id].route_tag:
        parts.append(
            f"{HELPERS[helper_id].phrase} does not suit the route to {SPIRITS[spirit_id].shrine}"
        )
    if not parts:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(parts) + ".)"


def outcome_of(params: StoryParams) -> str:
    spirit = SPIRITS[params.spirit]
    helper = HELPERS[params.helper]
    return "saved" if success_possible(params.trait, helper, spirit) else "dawn_help"


ASP_RULES = r"""
warns_spirit(O,S) :- omen(O), warns(O,S).
gift_for(G,S) :- offering(G), appeases(G,S).
path_fit(H,S) :- helper(H), spirit(S), supports(H,R), route_tag(S,R).

valid(O,S,G,H) :- warns_spirit(O,S), gift_for(G,S), path_fit(H,S).

base_bravery(0) :- chosen_trait(timid).
base_bravery(1) :- chosen_trait(steady).
base_bravery(2) :- chosen_trait(bold).
base_bravery(1) :- chosen_trait(faithful).

total_courage(B + Q + P) :-
    base_bravery(B),
    quest_bonus(Q),
    chosen_helper(H),
    power(H,P).

saved :- chosen_spirit(S), danger(S,D), total_courage(C), C >= D.
outcome(saved) :- saved.
outcome(dawn_help) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("warns", omen_id, omen.warns))
    for spirit_id, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", spirit_id))
        lines.append(asp.fact("route_tag", spirit_id, spirit.route_tag))
        lines.append(asp.fact("danger", spirit_id, spirit.danger))
    for offering_id, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", offering_id))
        lines.append(asp.fact("appeases", offering_id, offering.appeases))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("supports", helper_id, helper.supports))
        lines.append(asp.fact("power", helper_id, helper.power))
    lines.append(asp.fact("quest_bonus", QUEST_BONUS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spirit", params.spirit),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(50):
        rng = random.Random(seed)
        try:
            p = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mythic storyworld of omens, bravery, and a shrine quest. Unspecified choices are seeded and randomized from valid combinations."
    )
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--spirit", choices=sorted(SPIRITS))
    ap.add_argument("--offering", choices=sorted(OFFERINGS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "priest", "priestess"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the inline clingo model")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.omen and args.spirit and args.offering and args.helper:
        if not valid_combo(OMENS[args.omen], SPIRITS[args.spirit], OFFERINGS[args.offering], HELPERS[args.helper]):
            raise StoryError(explain_rejection(args.omen, args.spirit, args.offering, args.helper))
    elif any(x is not None for x in (args.omen, args.spirit, args.offering, args.helper)):
        omen_id = args.omen or next(iter(OMENS))
        spirit_id = args.spirit or next(iter(SPIRITS))
        offering_id = args.offering or next(iter(OFFERINGS))
        helper_id = args.helper or next(iter(HELPERS))
        if not valid_combo(OMENS[omen_id], SPIRITS[spirit_id], OFFERINGS[offering_id], HELPERS[helper_id]):
            combos = [
                c for c in valid_combos()
                if (args.omen is None or c[0] == args.omen)
                and (args.spirit is None or c[1] == args.spirit)
                and (args.offering is None or c[2] == args.offering)
                and (args.helper is None or c[3] == args.helper)
            ]
            if not combos:
                raise StoryError(explain_rejection(omen_id, spirit_id, offering_id, helper_id))

    combos = [
        c for c in valid_combos()
        if (args.omen is None or c[0] == args.omen)
        and (args.spirit is None or c[1] == args.spirit)
        and (args.offering is None or c[2] == args.offering)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    omen_id, spirit_id, offering_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "priest", "priestess"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        omen=omen_id,
        spirit=spirit_id,
        offering=offering_id,
        helper=helper_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [
        ("omen", OMENS),
        ("spirit", SPIRITS),
        ("offering", OFFERINGS),
        ("helper", HELPERS),
    ]:
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if not valid_combo(OMENS[params.omen], SPIRITS[params.spirit], OFFERINGS[params.offering], HELPERS[params.helper]):
        raise StoryError(explain_rejection(params.omen, params.spirit, params.offering, params.helper))

    world = tell(
        omen=OMENS[params.omen],
        spirit_cfg=SPIRITS[params.spirit],
        offering_cfg=OFFERINGS[params.offering],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.name,
        hero_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
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
        print(f"{len(combos)} valid (omen, spirit, offering, helper) combos:\n")
        for omen_id, spirit_id, offering_id, helper_id in combos:
            print(f"  {omen_id:12} {spirit_id:15} {offering_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
                f"### {p.name}: {p.omen} -> {p.spirit} with {p.offering} and {p.helper} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
