#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/complement_quest_myth.py
==================================================

A standalone storyworld for a small mythic quest: a young seeker learns that a
holy thing cannot do its work alone, because every sacred gift needs its
complement.

The world models a shrine out of balance, a guide whose help fits a real path,
a journey to recover the missing counterpart, and a return that visibly changes
the land. It refuses combinations that do not make common-sense mythic sense:
the realm must actually contain the needed path, and the chosen guide must know
how to cross it.

Run it
------
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --realm dawn_vale --lack moon_bowl --guide goat_keeper
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --realm ember_delta --lack moon_bowl
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --all
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --trace
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --json
    python storyworlds/worlds/gpt-5.4/complement_quest_myth.py --verify
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
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt", "priestess"}
        male = {"boy", "man", "hermit", "keeper", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Realm:
    id: str
    title: str
    opening: str
    shrine_name: str
    people_line: str
    ending_image: str
    affords: set[str] = field(default_factory=set)
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
class Complement:
    id: str
    label: str
    phrase: str
    complements: str
    source_place: str
    terrain: str
    vessel: str
    retrieve_text: str
    gleam: str
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
class Lack:
    id: str
    present_relic: str
    present_label: str
    missing_id: str
    missing_label: str
    imbalance: str
    warning: str
    blessing: str
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
class Guide:
    id: str
    label: str
    type: str
    home: str
    supports: set[str]
    tool: str
    help_line: str
    travel_line: str
    wisdom: str
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
    realm: str
    lack: str
    guide: str
    name: str
    gender: str
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


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm_cfg = realm
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
        clone = World(self.realm_cfg)
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


def _r_imbalance(world: World) -> list[str]:
    shrine = world.get("shrine")
    realm = world.get("realm")
    if shrine.meters["missing"] < THRESHOLD:
        return []
    sig = ("imbalance",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    realm.meters["blight"] += 1
    world.get("hero").memes["concern"] += 1
    return ["__imbalance__"]


def _r_restore(world: World) -> list[str]:
    shrine = world.get("shrine")
    realm = world.get("realm")
    hero = world.get("hero")
    relic = world.get("complement")
    if shrine.meters["completed_pair"] < THRESHOLD:
        return []
    sig = ("restore", relic.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["radiance"] += 1
    shrine.meters["missing"] = 0.0
    realm.meters["blight"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__restore__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="imbalance", tag="physical", apply=_r_imbalance),
    Rule(name="restore", tag="physical", apply=_r_restore),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


def valid_combo(realm_id: str, lack_id: str, guide_id: str) -> bool:
    if realm_id not in REALMS or lack_id not in LACKS or guide_id not in GUIDES:
        return False
    realm = REALMS[realm_id]
    lack = LACKS[lack_id]
    comp = COMPLEMENTS[lack.missing_id]
    guide = GUIDES[guide_id]
    return comp.terrain in realm.affords and comp.terrain in guide.supports


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for realm_id in REALMS:
        for lack_id in LACKS:
            for guide_id in GUIDES:
                if valid_combo(realm_id, lack_id, guide_id):
                    out.append((realm_id, lack_id, guide_id))
    return out


def predict_restoration(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["journey_done"] += 1
    sim.get("complement").meters["carried"] += 1
    sim.get("shrine").meters["completed_pair"] += 1
    propagate(sim, narrate=False)
    return {
        "restored": sim.get("shrine").meters["radiance"] >= THRESHOLD,
        "blight": sim.get("realm").meters["blight"],
    }


def introduce(world: World, hero: Entity, realm: Realm) -> None:
    world.say(
        f"In {realm.title}, {realm.opening}. {hero.id} was a young {hero.type} "
        f"with a {next((t for t in hero.traits if t), 'steady')} heart."
    )
    world.say(realm.people_line)


def show_lack(world: World, hero: Entity, lack: Lack, realm: Realm) -> None:
    shrine = world.get("shrine")
    shrine.meters["missing"] = 1.0
    shrine.attrs["present_relic"] = lack.present_relic
    shrine.attrs["missing_relic"] = lack.missing_id
    propagate(world, narrate=False)
    world.say(
        f"At the center of the land stood {realm.shrine_name}, where the "
        f"{lack.present_label} waited alone on an old stone dais."
    )
    world.say(
        f"Without its complement, {lack.imbalance}. {lack.warning}"
    )


def call_to_quest(world: World, hero: Entity, guide: Entity, lack: Lack, complement: Complement) -> None:
    pred = predict_restoration(world)
    world.facts["predicted_restored"] = pred["restored"]
    world.say(
        f"{hero.id} went to {guide.label}, who lived {guide.attrs['home']}."
    )
    world.say(
        f'"Every sacred thing has its complement," {guide.label} said. '
        f'"The {lack.present_label} is calling for {complement.label}. '
        f'{guide.attrs["wisdom"]}"'
    )
    if pred["restored"]:
        world.say(
            f"{guide.label} pointed toward {complement.source_place} and promised "
            f"that if the pair was made whole again, the land would breathe easier."
        )


def equip(world: World, hero: Entity, guide: Entity, guide_cfg: Guide) -> None:
    tool = world.get("tool")
    tool.meters["ready"] = 1.0
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{guide.label} placed {guide_cfg.tool} in {hero.id}'s hands and said, "
        f'"{guide_cfg.help_line}"'
    )


def journey(world: World, hero: Entity, guide_cfg: Guide, complement: Complement) -> None:
    hero.meters["on_path"] = 1.0
    hero.meters["distance"] += 1
    world.say(
        f"So the quest began. {guide_cfg.travel_line} until {hero.id} reached "
        f"{complement.source_place}."
    )


def retrieve(world: World, hero: Entity, complement: Complement) -> None:
    relic = world.get("complement")
    hero.meters["distance"] += 1
    hero.meters["carrying"] = 1.0
    relic.meters["carried"] = 1.0
    hero.memes["wonder"] += 1
    world.say(complement.retrieve_text)
    world.say(
        f"{hero.id} lifted {complement.phrase}, and {complement.gleam}."
    )


def return_and_restore(world: World, hero: Entity, lack: Lack, realm: Realm, guide: Entity) -> None:
    shrine = world.get("shrine")
    shrine.meters["completed_pair"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} hurried back to {realm.shrine_name} and set the "
        f"{lack.missing_label} beside the {lack.present_label}."
    )
    world.say(
        f"At once the pair answered one another. {lack.blessing}"
    )
    world.say(
        f"{guide.label} smiled, and {hero.id} understood that courage was not the "
        f"same as shining alone. True strength knew its complement."
    )
    world.say(realm.ending_image)


def tell(realm: Realm, lack: Lack, guide_cfg: Guide,
         hero_name: str = "Iria", hero_gender: str = "girl",
         trait: str = "patient") -> World:
    world = World(realm)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_cfg.type,
        label=guide_cfg.label,
        role="guide",
        attrs={
            "home": guide_cfg.home,
            "wisdom": guide_cfg.wisdom,
            "supports": sorted(guide_cfg.supports),
        },
    ))
    shrine = world.add(Entity(
        id="shrine",
        type="shrine",
        label=realm.shrine_name,
        attrs={"realm": realm.id, "present_relic": lack.present_relic, "missing_relic": lack.missing_id},
    ))
    realm_ent = world.add(Entity(
        id="realm",
        type="realm",
        label=realm.title,
        attrs={"affords": sorted(realm.affords)},
    ))
    comp_cfg = COMPLEMENTS[lack.missing_id]
    world.add(Entity(
        id="complement",
        type="relic",
        label=comp_cfg.label,
        phrase=comp_cfg.phrase,
        attrs={"terrain": comp_cfg.terrain, "complements": comp_cfg.complements},
    ))
    world.add(Entity(
        id="tool",
        type="gift",
        label=guide_cfg.tool,
        attrs={"terrain": sorted(guide_cfg.supports)},
    ))

    world.facts.update(
        realm=realm,
        lack=lack,
        guide_cfg=guide_cfg,
        complement_cfg=comp_cfg,
        hero=hero,
        guide=guide,
        restored=False,
    )

    introduce(world, hero, realm)
    show_lack(world, hero, lack, realm)

    world.para()
    call_to_quest(world, hero, guide, lack, comp_cfg)
    equip(world, hero, guide, guide_cfg)

    world.para()
    journey(world, hero, guide_cfg, comp_cfg)
    retrieve(world, hero, comp_cfg)

    world.para()
    return_and_restore(world, hero, lack, realm, guide)
    world.facts["restored"] = world.get("shrine").meters["radiance"] >= THRESHOLD
    return world


REALMS = {
    "dawn_vale": Realm(
        id="dawn_vale",
        title="Dawn Vale",
        opening="the first light used to slide over the orchards like honey on warm bread",
        shrine_name="the Basin of First Light",
        people_line="The shepherds there said morning birds sang two notes together, never one alone.",
        ending_image="By evening, apricot light lay on every roof tile, and even the lambs looked gold.",
        affords={"cloud_bridge", "echo_cave"},
        tags={"light", "valley"},
    ),
    "reedmere": Realm(
        id="reedmere",
        title="Reedmere",
        opening="the river once braided silver paths between tall green reeds",
        shrine_name="the Gate of Singing Water",
        people_line="Boat folk there swore that water remembered kindness and carried it downstream.",
        ending_image="The reeds bowed, the fish flashed like coins, and the river sang under the little boats.",
        affords={"reed_marsh", "cloud_bridge"},
        tags={"river", "water"},
    ),
    "ember_delta": Realm(
        id="ember_delta",
        title="Ember Delta",
        opening="warm springs curled through black stones and painted the mist with red-gold light",
        shrine_name="the Hearth of Mist",
        people_line="The potters there listened for small cracks in clay the way others listened for thunder.",
        ending_image="Soft steam rose in bright ribbons, and every kiln in the delta breathed easy again.",
        affords={"reed_marsh", "echo_cave"},
        tags={"fire", "mist"},
    ),
}

COMPLEMENTS = {
    "sun_lamp": Complement(
        id="sun_lamp",
        label="the Sun Lamp",
        phrase="the Sun Lamp",
        complements="moon_bowl",
        source_place="the Cloud Bridge above the cranes' road",
        terrain="cloud_bridge",
        vessel="a rope ring",
        retrieve_text="At the bridge's highest arch, a lamp of pale gold waited in a cradle of wind.",
        gleam="its warm glow rested on the seeker's face without burning",
        tags={"light", "sun"},
    ),
    "wind_reed": Complement(
        id="wind_reed",
        label="the Wind Reed",
        phrase="the Wind Reed",
        complements="river_harp",
        source_place="the whispering marsh beyond the reed beds",
        terrain="reed_marsh",
        vessel="a reed skiff",
        retrieve_text="Deep in the marsh, one reed stood taller than the rest, humming before any hand touched it.",
        gleam="its silver-green skin trembled with a song that sounded like water remembering its name",
        tags={"wind", "water"},
    ),
    "ember_shell": Complement(
        id="ember_shell",
        label="the Ember Shell",
        phrase="the Ember Shell",
        complements="dew_stone",
        source_place="the echo cave under the sleeping hill",
        terrain="echo_cave",
        vessel="a moss-thread lantern",
        retrieve_text="Inside the cave, a small shell lay in a pool of darkness, holding a red spark the size of a plum seed.",
        gleam="its glow answered every footstep with a warm red blink",
        tags={"fire", "echo"},
    ),
}

LACKS = {
    "moon_bowl": Lack(
        id="moon_bowl",
        present_relic="moon_bowl",
        present_label="Moon Bowl",
        missing_id="sun_lamp",
        missing_label="Sun Lamp",
        imbalance="morning came thin and pale, as if the sky had forgotten the bold half of its song",
        warning="Children had to wait for the frost to soften before they could find the garden paths.",
        blessing="The pale bowl filled with amber, and dawn unfurled across the vale in a single bright breath.",
        tags={"light", "balance"},
    ),
    "river_harp": Lack(
        id="river_harp",
        present_relic="river_harp",
        present_label="River Harp",
        missing_id="wind_reed",
        missing_label="Wind Reed",
        imbalance="the channels moved, but they moved in silence, and the boats drifted as if listening for a tune that would not come",
        warning="Nets came up light because the fish no longer followed the old singing current.",
        blessing="The harp drank the reed's breath, and every channel began to ring and ripple at once.",
        tags={"water", "song"},
    ),
    "dew_stone": Lack(
        id="dew_stone",
        present_relic="dew_stone",
        present_label="Dew Stone",
        missing_id="ember_shell",
        missing_label="Ember Shell",
        imbalance="the springs gave only chill mist, and bread cooled too fast on the morning tables",
        warning="Potters held their hands over empty kilns and wished for heat that would not wake.",
        blessing="Warmth threaded through the mist, and the springs shone as if dawn had nested inside them.",
        tags={"warmth", "mist"},
    ),
}

GUIDES = {
    "goat_keeper": Guide(
        id="goat_keeper",
        label="the Goat Keeper",
        type="keeper",
        home="in a hut below the high ledges",
        supports={"cloud_bridge"},
        tool="a braided rope ring",
        help_line="Step where the wind is already stepping, and the bridge will remember your feet.",
        travel_line="With the rope ring at the seeker's waist, the child climbed the high ledges and crossed the white bridge of cloud",
        wisdom="A bright thing still needs a quiet thing beside it, or else brightness becomes lonely.",
        tags={"mountain", "bridge"},
    ),
    "crane_hermit": Guide(
        id="crane_hermit",
        label="the Crane Hermit",
        type="hermit",
        home="in a reed house above the marsh water",
        supports={"reed_marsh"},
        tool="a small reed skiff",
        help_line="Push gently, listen first, and the marsh will open its path for you.",
        travel_line="Standing in the reed skiff, the child slipped between green walls of whispering marsh",
        wisdom="What sings over water is not the same as the water, yet each one completes the other.",
        tags={"marsh", "boat"},
    ),
    "cave_grandmother": Guide(
        id="cave_grandmother",
        label="the Cave Grandmother",
        type="grandmother",
        home="beside a hill door painted with old spirals",
        supports={"echo_cave"},
        tool="a moss-thread lantern",
        help_line="Do not hurry in the dark. The cave gives its gift to the child who can hear the echoes settle.",
        travel_line="Carrying the moss-thread lantern, the child walked into the hill while drops counted time from the ceiling",
        wisdom="Coolness and warmth are companions. One teaches the other where to rest.",
        tags={"cave", "echo"},
    ),
}

GIRL_NAMES = ["Iria", "Nesa", "Luma", "Tali", "Mira", "Seli", "Aven", "Nori"]
BOY_NAMES = ["Orin", "Taren", "Milo", "Rian", "Soren", "Ari", "Bram", "Nilo"]
TRAITS = ["patient", "brave", "gentle", "steady", "curious", "kind"]


CURATED = [
    StoryParams(
        realm="dawn_vale",
        lack="moon_bowl",
        guide="goat_keeper",
        name="Iria",
        gender="girl",
        trait="steady",
    ),
    StoryParams(
        realm="reedmere",
        lack="river_harp",
        guide="crane_hermit",
        name="Orin",
        gender="boy",
        trait="patient",
    ),
    StoryParams(
        realm="ember_delta",
        lack="dew_stone",
        guide="cave_grandmother",
        name="Mira",
        gender="girl",
        trait="brave",
    ),
    StoryParams(
        realm="reedmere",
        lack="moon_bowl",
        guide="goat_keeper",
        name="Soren",
        gender="boy",
        trait="curious",
    ),
    StoryParams(
        realm="ember_delta",
        lack="river_harp",
        guide="crane_hermit",
        name="Nesa",
        gender="girl",
        trait="gentle",
    ),
]


KNOWLEDGE = {
    "complement": [
        (
            "What is a complement?",
            "A complement is the thing that completes something else. Two parts can be different, but together they make a whole.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. In stories, a hero goes somewhere hard because something important needs to be found or repaired.",
        )
    ],
    "bridge": [
        (
            "Why would someone use a rope on a high bridge?",
            "A rope helps you keep balance and stay safe where the path is narrow or windy. It gives your hands and feet something steady to trust.",
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is wet land with shallow water and lots of reeds or grasses. It can be soft and tricky to cross without a boat or a safe path.",
        )
    ],
    "cave": [
        (
            "Why do people carry a light into a cave?",
            "Caves are dark, and a light helps people see where to step. It also helps them notice walls, pools, and low places before they bump into them.",
        )
    ],
    "balance": [
        (
            "Why do myths talk about balance?",
            "Myths often use balance to show that the world works best when different parts help each other. Too much of one thing, or a missing partner, can make trouble.",
        )
    ],
}
KNOWLEDGE_ORDER = ["complement", "quest", "balance", "bridge", "marsh", "cave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    realm = f["realm"]
    lack = f["lack"]
    guide_cfg = f["guide_cfg"]
    comp = f["complement_cfg"]
    hero = f["hero"]
    return [
        f'Write a short myth for young children about a quest to restore balance in {realm.title}. Include the word "complement".',
        f"Tell a gentle myth where {hero.id} must travel to {comp.source_place} so the {lack.present_label} can be joined with its complement, the {comp.label}.",
        f"Write a child-facing quest story with a wise guide, a sacred object pair, and an ending that shows the land changing for the better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    realm = f["realm"]
    lack = f["lack"]
    guide_cfg = f["guide_cfg"]
    comp = f["complement_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type} in {realm.title}. The story also includes {guide_cfg.label}, who helps start the quest.",
        ),
        (
            f"Why did {hero.id} begin the quest?",
            f"{hero.id} began the quest because the {lack.present_label} was standing alone, and the land was hurting without its complement. The missing partner was {comp.label}, so the shrine could not do its full work.",
        ),
        (
            f"Where did {hero.id} go, and how did {guide_cfg.label} help?",
            f"{hero.id} went to {comp.source_place}. {guide_cfg.label} helped by giving {hero.pronoun('object')} {guide_cfg.tool} and a wise instruction for the path.",
        ),
        (
            f"What changed when {hero.id} returned with {comp.label}?",
            f"When {hero.id} set {comp.label} beside the {lack.present_label}, the sacred pair became whole again. Then {lack.blessing}",
        ),
        (
            "What did the hero learn?",
            f"{hero.id} learned that shining alone is not the same as being complete. The story says true strength knows its complement, because different gifts can finish each other.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"complement", "quest", "balance"}
    terrain = world.facts["complement_cfg"].terrain
    if terrain == "cloud_bridge":
        tags.add("bridge")
    elif terrain == "reed_marsh":
        tags.add("marsh")
    elif terrain == "echo_cave":
        tags.add("cave")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:11} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(realm_id: str, lack_id: str, guide_id: Optional[str] = None) -> str:
    if realm_id not in REALMS or lack_id not in LACKS:
        return "(No story: the requested realm or shrine problem is unknown.)"
    realm = REALMS[realm_id]
    lack = LACKS[lack_id]
    comp = COMPLEMENTS[lack.missing_id]
    if comp.terrain not in realm.affords:
        return (
            f"(No story: {realm.title} does not contain the {comp.terrain.replace('_', ' ')} needed to reach "
            f"{comp.label}. This quest needs a realm whose paths can honestly hold that journey.)"
        )
    if guide_id is not None and guide_id in GUIDES:
        guide = GUIDES[guide_id]
        if comp.terrain not in guide.supports:
            return (
                f"(No story: {guide.label} does not know the {comp.terrain.replace('_', ' ')} path needed for "
                f"{comp.label}. Choose a guide whose help fits the journey.)"
            )
    return "(No story: this combination does not form a reasonable quest.)"


ASP_RULES = r"""
needs(L, C, T) :- lack(L), missing(L, C), complement(C), terrain_of(C, T).
valid(R, L, G) :- realm(R), lack(L), guide(G),
                  needs(L, C, T),
                  affords(R, T),
                  supports(G, T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for terrain in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, terrain))
    for lack_id, lack in LACKS.items():
        lines.append(asp.fact("lack", lack_id))
        lines.append(asp.fact("missing", lack_id, lack.missing_id))
    for comp_id, comp in COMPLEMENTS.items():
        lines.append(asp.fact("complement", comp_id))
        lines.append(asp.fact("terrain_of", comp_id, comp.terrain))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        for terrain in sorted(guide.supports):
            lines.append(asp.fact("supports", guide_id, terrain))
    return "\n".join(lines)


def asp_program(show_override: str = "") -> str:
    show = show_override or "#show valid/3."
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic quest storyworld: a young seeker restores a sacred pair by finding its complement."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--lack", choices=LACKS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid (realm, lack, guide) combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.lack and args.guide and not valid_combo(args.realm, args.lack, args.guide):
        raise StoryError(explain_rejection(args.realm, args.lack, args.guide))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.lack is None or combo[1] == args.lack)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        if args.realm and args.lack:
            raise StoryError(explain_rejection(args.realm, args.lack, args.guide))
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, lack_id, guide_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        realm=realm_id,
        lack=lack_id,
        guide=guide_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS or params.lack not in LACKS or params.guide not in GUIDES:
        raise StoryError("(No story: one or more requested parameters are unknown.)")
    if not valid_combo(params.realm, params.lack, params.guide):
        raise StoryError(explain_rejection(params.realm, params.lack, params.guide))

    world = tell(
        realm=REALMS[params.realm],
        lack=LACKS[params.lack],
        guide_cfg=GUIDES[params.guide],
        hero_name=params.name,
        hero_gender=params.gender,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    smoke_cases: list[StoryParams] = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(17))
        default_params.seed = 17
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL during default resolve_params(): {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header="" if idx > 1 else "")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAIL for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (realm, lack, guide) combos:\n")
        for realm_id, lack_id, guide_id in combos:
            print(f"  {realm_id:11} {lack_id:11} {guide_id}")
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
            header = f"### {p.name}: {p.lack} in {p.realm} with {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
