#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py
=====================================================================

A standalone story world for a friendly ghost-story domain: a child in an old
building hears spooky sounds, meets a sad ghost lyric-ist, and discovers that
the rattling and whispering come from a hungry ghost cat and a missing page of
lyrics. With a sensible light and a tuna treat, the child helps the cat reveal
the hidden page, the ghost finishes his song, and the place grows peaceful.

The world enforces a small reasonableness gate:

* the hiding place must actually belong to the chosen setting
* the light must be bright enough for that setting's darkness
* drafty places reject flame lights
* low-sense lights are known to the world but refused
* the tuna offer must be strong-smelling enough to lure the shy ghost cat in
  that setting

Run it
------
python storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py
python storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py --place lighthouse --spot under_trunk --light lantern --tuna tin
python storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py --place attic --light candle
python storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py --all --qa
python storyworlds/worlds/gpt-5.4/tuna_lyric_ist_happy_ending_ghost_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    intro: str
    eerie: str
    dark_word: str
    darkness: int
    cat_need: int
    drafty: bool
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
class HidingSpot:
    id: str
    label: str
    clue: str
    reach: str
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
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    brightness: int
    sense: int
    flame: bool = False
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
class TunaOffer:
    id: str
    label: str
    phrase: str
    smell: int
    open_text: str
    cat_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "page_found": False,
            "song_finished": False,
            "cat_led_way": False,
            "outcome": "unresolved",
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


def _r_tuna_cat(world: World) -> list[str]:
    cat = world.get("cat")
    if cat.meters["hungry"] < THRESHOLD or world.get("offer").meters["opened"] < THRESHOLD:
        return []
    sig = ("cat_comes",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cat.meters["nearby"] += 1
    cat.memes["trust"] += 1
    world.facts["cat_led_way"] = True
    return []


def _r_cat_reveals_page(world: World) -> list[str]:
    cat = world.get("cat")
    light = world.get("light")
    page = world.get("page")
    if cat.meters["nearby"] < THRESHOLD or light.meters["on"] < THRESHOLD:
        return []
    sig = ("page_found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    page.meters["found"] += 1
    page.meters["safe"] += 1
    world.facts["page_found"] = True
    return []


def _r_finish_song(world: World) -> list[str]:
    ghost = world.get("ghost")
    page = world.get("page")
    room = world.get("room")
    child = world.get("child")
    if ghost.meters["present"] < THRESHOLD or page.meters["found"] < THRESHOLD:
        return []
    sig = ("song_finished",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["song"] += 1
    ghost.memes["relief"] += 1
    ghost.memes["joy"] += 1
    room.meters["rattle"] = 0.0
    room.memes["peace"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    world.facts["song_finished"] = True
    world.facts["outcome"] = "peaceful"
    return []


CAUSAL_RULES = [
    Rule(name="tuna_cat", tag="physical", apply=_r_tuna_cat),
    Rule(name="cat_reveals_page", tag="physical", apply=_r_cat_reveals_page),
    Rule(name="finish_song", tag="emotional", apply=_r_finish_song),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def spot_in_place(setting: Setting, spot: HidingSpot) -> bool:
    return spot.id in setting.affords


def usable_light(setting: Setting, light: Light) -> bool:
    if light.brightness < setting.darkness:
        return False
    if setting.drafty and light.flame:
        return False
    return True


def sensible_lights() -> list[Light]:
    return [light for light in LIGHTS.values() if light.sense >= SENSE_MIN]


def good_tuna(setting: Setting, offer: TunaOffer) -> bool:
    return offer.smell >= setting.cat_need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for spot_id, spot in SPOTS.items():
            if not spot_in_place(setting, spot):
                continue
            for light_id, light in LIGHTS.items():
                if not usable_light(setting, light):
                    continue
                if light.sense < SENSE_MIN:
                    continue
                for tuna_id, offer in TUNA_OFFERS.items():
                    if good_tuna(setting, offer):
                        combos.append((place_id, spot_id, light_id, tuna_id))
    return combos


@dataclass
class StoryParams:
    place: str
    spot: str
    light: str
    tuna: str
    name: str
    gender: str
    guardian: str
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


def explain_spot(setting: Setting, spot: HidingSpot) -> str:
    return (
        f"(No story: {spot.label} does not belong in {setting.place}, so the missing lyric page "
        f"could not honestly be hidden there. Pick one of: {', '.join(sorted(setting.affords))}.)"
    )


def explain_light(setting: Setting, light: Light) -> str:
    if light.sense < SENSE_MIN:
        return (
            f"(Refusing light '{light.id}': it scores too low on common sense "
            f"(sense={light.sense} < {SENSE_MIN}). This world prefers safer lights like "
            f"{', '.join(sorted(l.id for l in sensible_lights()))}.)"
        )
    if light.brightness < setting.darkness:
        return (
            f"(No story: {light.label} is too dim for {setting.place}. The child needs a brighter light "
            f"to find the lyric page in that much dark.)"
        )
    if setting.drafty and light.flame:
        return (
            f"(No story: {setting.place} is too drafty for {light.label}. A small flame would flutter and "
            f"leave the search unsafe.)"
        )
    return "(No story: this light is not suitable for the setting.)"


def explain_tuna(setting: Setting, offer: TunaOffer) -> str:
    return (
        f"(No story: {offer.phrase} is not strong-smelling enough to coax the shy ghost cat out in "
        f"{setting.place}. Pick a tuna offer with a stronger fishy smell.)"
    )


def predict_success(setting: Setting, light: Light, offer: TunaOffer) -> dict:
    return {
        "page_found": usable_light(setting, light) and good_tuna(setting, offer),
        "peaceful": usable_light(setting, light) and good_tuna(setting, offer),
    }


def open_light(world: World, child: Entity, light: Light) -> None:
    lamp = world.get("light")
    lamp.meters["on"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} clicked on {light.phrase}, and {light.glow}. The beam made the dark look less like a threat and more like a place that could be searched."
    )


def reveal_ghost(world: World, child: Entity, ghost: Entity, guardian: Entity) -> None:
    room = world.get("room")
    room.meters["rattle"] += 1
    child.memes["fear"] += 1
    ghost.meters["present"] += 1
    ghost.memes["sadness"] += 1
    world.say(
        f"A pale shape drifted from the shadows, not with claws or a roar, but with a worried sigh. \"Please don't run,\" the ghost whispered. \"I am a lyric-ist, and I have lost the last page of my moon song.\""
    )
    world.say(
        f"{child.id} took one step back, then noticed how the ghost kept looking toward the floor instead of lunging at anyone. Even {guardian.label_word} could hear that the voice sounded lonely, not mean."
    )


def explain_problem(world: World, ghost: Entity, spot: HidingSpot, offer: TunaOffer) -> None:
    world.say(
        f"The ghost pointed with a thin silver hand. \"My cat batted the page away,\" {ghost.pronoun()} said. \"Now the house keeps shivering because the song has no ending. I think the paper slid {spot.reach}, and Brine will only come out for tuna.\""
    )
    pred = world.facts["prediction"]
    if pred["page_found"]:
        world.say(
            "That made sense: if the child could bring enough light and a fishy treat, the hidden page could be found and the rattling could stop."
        )


def open_tuna(world: World, child: Entity, offer: TunaOffer) -> None:
    world.get("offer").meters["opened"] += 1
    child.memes["kindness"] += 1
    world.say(offer.open_text)
    world.say(offer.cat_text)


def cat_leads(world: World, spot: HidingSpot) -> None:
    if not world.facts.get("cat_led_way"):
        return
    world.say(
        f"Brine's whiskers twitched, and the little ghost cat padded through the dust. With one bright paw, the cat tapped {spot.clue}."
    )


def find_page(world: World, child: Entity, spot: HidingSpot) -> None:
    if not world.facts.get("page_found"):
        return
    world.say(
        f"{child.id} knelt down and reached {spot.reach}. There, folded and a little crinkled, was the missing lyric page."
    )


def mend_song(world: World, ghost: Entity, child: Entity, guardian: Entity, setting: Setting) -> None:
    if not world.facts.get("song_finished"):
        return
    world.say(
        f"The ghost smoothed the page with careful fingers and sang the last lines at last. The sound floated through {setting.place} like moonlight on water, and every creak in the walls softened into a hush."
    )
    world.say(
        f"Brine purred around {child.id}'s ankles. The ghost bowed to {child.id} and {guardian.label_word}, and {ghost.pronoun()} smiled so gently that the room stopped feeling haunted and began to feel grateful."
    )


def happy_ending(world: World, child: Entity, guardian: Entity, light: Light, offer: TunaOffer) -> None:
    world.say(
        f"By the time bedtime came, the spooky bumps were gone. {child.id} set the empty {offer.label} by the sink, and {guardian.label_word} tucked {child.pronoun('object')} in while the finished song hummed softly through the beams."
    )
    world.say(
        f"After that night, {child.id} was never quite so afraid of whispers in the dark. Sometimes a careful light, a kind heart, and a bit of tuna were enough to turn a ghost story into a happy one."
    )


def tell(
    setting: Setting,
    spot: HidingSpot,
    light: Light,
    offer: TunaOffer,
    name: str = "Mina",
    gender: str = "girl",
    guardian_type: str = "grandfather",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    guardian = world.add(
        Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the guardian")
    )
    ghost = world.add(Entity(id="Morrow", kind="character", type="ghost", role="ghost"))
    cat = world.add(Entity(id="cat", kind="thing", type="cat", label="Brine"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    page = world.add(Entity(id="page", kind="thing", type="paper", label="lyric page"))
    light_ent = world.add(Entity(id="light", kind="thing", type="light", label=light.label))
    offer_ent = world.add(Entity(id="offer", kind="thing", type="food", label=offer.label))

    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0
    ghost.meters["present"] = 0.0
    ghost.memes["sadness"] = 0.0
    cat.meters["hungry"] = 1.0
    cat.meters["nearby"] = 0.0
    room.meters["rattle"] = 0.0
    room.memes["peace"] = 0.0
    page.meters["found"] = 0.0
    page.meters["safe"] = 0.0
    light_ent.meters["on"] = 0.0
    offer_ent.meters["opened"] = 0.0

    prediction = predict_success(setting, light, offer)
    world.facts.update(
        child=child,
        guardian=guardian,
        ghost=ghost,
        cat=cat,
        setting=setting,
        spot_cfg=spot,
        light_cfg=light,
        tuna_cfg=offer,
        prediction=prediction,
    )

    world.say(
        f"{name} was spending the night in {setting.place}. {setting.intro}"
    )
    world.say(
        f"When the lamps were low, {setting.eerie} and a thin tune drifted through the dark. It sounded spooky enough to raise goosebumps, but sad enough to make {name} listen."
    )

    world.para()
    open_light(world, child, light)
    reveal_ghost(world, child, ghost, guardian)
    explain_problem(world, ghost, spot, offer)

    world.para()
    open_tuna(world, child, offer)
    propagate(world, narrate=False)
    cat_leads(world, spot)
    find_page(world, child, spot)
    propagate(world, narrate=False)
    mend_song(world, ghost, child, guardian, setting)

    world.para()
    happy_ending(world, child, guardian, light, offer)
    return world


SETTINGS = {
    "lighthouse": Setting(
        id="lighthouse",
        place="the old lighthouse",
        intro="Salt wind hummed around the stair and the windows wore rings of mist.",
        eerie="somewhere above, loose glass chimed and the stair gave a lonely knock",
        dark_word="sea-dark",
        darkness=2,
        cat_need=2,
        drafty=True,
        affords={"under_trunk", "behind_coat"},
        tags={"ghost", "lighthouse"},
    ),
    "theater": Setting(
        id="theater",
        place="the closed seaside theater",
        intro="Red curtains slept in folds, and dust lay on the stage like pale flour.",
        eerie="from the balcony came a soft thump and a whisper of song",
        dark_word="velvet-dark",
        darkness=1,
        cat_need=1,
        drafty=False,
        affords={"inside_piano", "behind_backdrop"},
        tags={"ghost", "theater"},
    ),
    "attic": Setting(
        id="attic",
        place="the creaky attic room",
        intro="The rafters smelled of cedar, rain, and old paper.",
        eerie="the shutters trembled and a scratchy melody slipped between the trunks",
        dark_word="rafter-dark",
        darkness=2,
        cat_need=2,
        drafty=True,
        affords={"under_trunk", "inside_hatbox"},
        tags={"ghost", "attic"},
    ),
}

SPOTS = {
    "under_trunk": HidingSpot(
        id="under_trunk",
        label="under an old trunk",
        clue="the trunk's curved shadow",
        reach="under the old trunk",
        tags={"trunk"},
    ),
    "behind_coat": HidingSpot(
        id="behind_coat",
        label="behind a hanging raincoat",
        clue="the raincoat hem",
        reach="behind the hanging raincoat",
        tags={"coat"},
    ),
    "inside_piano": HidingSpot(
        id="inside_piano",
        label="inside the piano bench",
        clue="the piano bench lid",
        reach="inside the piano bench",
        tags={"piano"},
    ),
    "behind_backdrop": HidingSpot(
        id="behind_backdrop",
        label="behind a painted moon backdrop",
        clue="the painted moon backdrop",
        reach="behind the painted moon backdrop",
        tags={"backdrop"},
    ),
    "inside_hatbox": HidingSpot(
        id="inside_hatbox",
        label="inside a round hatbox",
        clue="the hatbox ribbon",
        reach="inside the round hatbox",
        tags={"hatbox"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        glow="its warm circle of light reached all the way to the corners",
        brightness=2,
        sense=3,
        flame=False,
        tags={"light", "lantern"},
    ),
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="a bright white beam slid over the floorboards",
        brightness=2,
        sense=3,
        flame=False,
        tags={"light", "flashlight"},
    ),
    "candle": Light(
        id="candle",
        label="candle",
        phrase="a stubby candle",
        glow="its tiny flame shook in the air",
        brightness=1,
        sense=1,
        flame=True,
        tags={"light", "candle"},
    ),
}

TUNA_OFFERS = {
    "tin": TunaOffer(
        id="tin",
        label="tuna tin",
        phrase="a tin of tuna",
        smell=2,
        open_text="Very carefully, the child opened a tin of tuna. At once, a salty, fishy smell spread through the room.",
        cat_text="Two moon-pale eyes blinked from the shadows.",
        tags={"tuna"},
    ),
    "sandwich": TunaOffer(
        id="sandwich",
        label="tuna sandwich",
        phrase="a tuna sandwich",
        smell=1,
        open_text="The child unwrapped a tuna sandwich, and the soft smell of fish drifted into the dark.",
        cat_text="Somewhere nearby, a faint little mew answered.",
        tags={"tuna"},
    ),
    "pastry": TunaOffer(
        id="pastry",
        label="tuna pastry",
        phrase="a flaky tuna pastry",
        smell=1,
        open_text="The child broke open a flaky tuna pastry, and the buttery fish smell slipped under the rafters.",
        cat_text="A pair of whiskers twitched behind a shadow.",
        tags={"tuna"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Rosa", "Ella"]
BOY_NAMES = ["Theo", "Owen", "Leo", "Max", "Finn", "Eli", "Noah", "Jude"]

KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale about strange sounds, shadows, or spirits. Sometimes it is scary, but sometimes the ghost only needs help."
        )
    ],
    "lyricist": [
        (
            "What is a lyric-ist?",
            "A lyric-ist is someone who writes the words of a song. In this story, the ghost was a lyric-ist because he cared about finishing his song."
        )
    ],
    "tuna": [
        (
            "What is tuna?",
            "Tuna is a kind of fish that people can eat in sandwiches or from a tin. It has a strong smell, so cats often notice it quickly."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see in dark places. A good lantern helps you search calmly instead of stumbling in the dark."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small light that shines a bright beam when you switch it on. It helps people see without using a flame."
        )
    ],
    "lighthouse": [
        (
            "What is a lighthouse?",
            "A lighthouse is a tall building near the sea that shines light to help ships. Wind and waves can make it sound lonely at night."
        )
    ],
    "theater": [
        (
            "What is a theater?",
            "A theater is a place where people sing, act, and put on shows. Big curtains and empty seats can make it feel mysterious after dark."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room under the roof where trunks, boxes, and old things are often kept. Because it is high and quiet, it can sound creaky."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "lyricist", "tuna", "lantern", "flashlight", "lighthouse", "theater", "attic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    light = f["light_cfg"]
    tuna = f["tuna_cfg"]
    spot = f["spot_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "tuna" and "lyric-ist" and ends happily.',
        f"Tell a story where {child.id} hears spooky sounds in {setting.place}, meets a sad ghost lyric-ist, and uses {light.phrase} plus {tuna.phrase} to solve the mystery.",
        f"Write a child-facing ghost tale in which a missing song page is hidden {spot.reach}, a ghost cat comes out for tuna, and the house becomes peaceful by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    ghost = f["ghost"]
    setting = f["setting"]
    spot = f["spot_cfg"]
    light = f["light_cfg"]
    tuna = f["tuna_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child spending the night in {setting.place}, a ghost lyric-ist named Morrow, and the ghost cat Brine. The grown-up nearby was {child.pronoun('possessive')} {guardian.label_word}, who heard the strange song too."
        ),
        (
            "Why did the place seem spooky at first?",
            f"It seemed spooky because bumps, creaks, and a thin tune were coming through the dark. Those sounds were not an attack, though; they were signs that the ghost's song was unfinished and the house was restless."
        ),
        (
            "What problem did the ghost have?",
            f"Morrow had lost the last page of his moon song, so he could not finish singing it. Without the ending, the house kept rattling and the ghost felt sad instead of peaceful."
        ),
        (
            f"How did {child.id} help solve the mystery?",
            f"{child.id} used {light.phrase} to see into the dark and opened {tuna.phrase} to coax Brine out. When the cat led the way to the hiding place, {child.id} could reach {spot.reach} and find the missing lyric page."
        ),
    ]
    if f.get("song_finished"):
        qa.append(
            (
                "How did the story end?",
                f"It ended happily because the ghost got the missing page back and finished his song. Once the song was whole, the spooky rattling stopped and the place felt calm and grateful."
            )
        )
        qa.append(
            (
                f"Why was tuna important in the story?",
                f"Tuna mattered because Brine was shy and hungry, and the fishy smell brought the cat close enough to help. Without the tuna, the child would not have had such a clear clue about where the page was hidden."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "lyricist", "tuna"}
    setting = world.facts["setting"]
    light = world.facts["light_cfg"]
    if setting.id in KNOWLEDGE:
        tags.add(setting.id)
    if light.id in KNOWLEDGE:
        tags.add(light.id)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="lighthouse",
        spot="under_trunk",
        light="lantern",
        tuna="tin",
        name="Mina",
        gender="girl",
        guardian="grandfather",
    ),
    StoryParams(
        place="theater",
        spot="inside_piano",
        light="flashlight",
        tuna="sandwich",
        name="Theo",
        gender="boy",
        guardian="aunt",
    ),
    StoryParams(
        place="attic",
        spot="inside_hatbox",
        light="flashlight",
        tuna="tin",
        name="Nora",
        gender="girl",
        guardian="grandmother",
    ),
    StoryParams(
        place="theater",
        spot="behind_backdrop",
        light="lantern",
        tuna="pastry",
        name="Eli",
        gender="boy",
        guardian="uncle",
    ),
]


ASP_RULES = r"""
usable_light(P,L) :- setting(P), light(L), brightness(L,B), darkness(P,D), B >= D, not blocked_flame(P,L).
blocked_flame(P,L) :- drafty(P), flame(L).
sensible_light(L) :- light(L), sense(L,S), sense_min(M), S >= M.
good_tuna(P,T) :- setting(P), tuna(T), smell(T,S), cat_need(P,N), S >= N.
valid(P,Sp,L,T) :- setting(P), spot(Sp), light(L), tuna(T),
                   affords(P,Sp), usable_light(P,L), sensible_light(L), good_tuna(P,T).

page_found(P,L,T) :- setting(P), light(L), tuna(T), usable_light(P,L), good_tuna(P,T).
outcome(P,peaceful) :- page_found(P,L,T), sensible_light(L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("darkness", pid, setting.darkness))
        lines.append(asp.fact("cat_need", pid, setting.cat_need))
        if setting.drafty:
            lines.append(asp.fact("drafty", pid))
        for spot_id in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, spot_id))
    for sid in SPOTS:
        lines.append(asp.fact("spot", sid))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("brightness", lid, light.brightness))
        lines.append(asp.fact("sense", lid, light.sense))
        if light.flame:
            lines.append(asp.fact("flame", lid))
    for tid, offer in TUNA_OFFERS.items():
        lines.append(asp.fact("tuna", tid))
        lines.append(asp.fact("smell", tid, offer.smell))
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

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_tuna", params.tuna),
            f"page_found(chosen_place,chosen_light,chosen_tuna) :- usable_light({params.place},{params.light}), good_tuna({params.place},{params.tuna}).",
            f"outcome(chosen_place,peaceful) :- page_found(chosen_place,chosen_light,chosen_tuna), sensible_light({params.light}).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/2."))
    atoms = asp.atoms(model, "outcome")
    for place, outcome in atoms:
        if place == "chosen_place":
            return outcome
    for _, outcome in atoms:
        return outcome
    return "?"


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.place]
    light = LIGHTS[params.light]
    tuna = TUNA_OFFERS[params.tuna]
    return "peaceful" if usable_light(setting, light) and light.sense >= SENSE_MIN and good_tuna(setting, tuna) else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Friendly ghost-story world: a child helps a ghost lyric-ist recover a lost song page with light and tuna."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--tuna", choices=TUNA_OFFERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle", "grandmother", "grandfather"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.spot:
        setting = SETTINGS[args.place]
        spot = SPOTS[args.spot]
        if not spot_in_place(setting, spot):
            raise StoryError(explain_spot(setting, spot))
    if args.place and args.light:
        setting = SETTINGS[args.place]
        light = LIGHTS[args.light]
        if not usable_light(setting, light) or light.sense < SENSE_MIN:
            raise StoryError(explain_light(setting, light))
    if args.place and args.tuna:
        setting = SETTINGS[args.place]
        offer = TUNA_OFFERS[args.tuna]
        if not good_tuna(setting, offer):
            raise StoryError(explain_tuna(setting, offer))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.spot is None or c[1] == args.spot)
        and (args.light is None or c[2] == args.light)
        and (args.tuna is None or c[3] == args.tuna)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, spot, light, tuna = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle", "grandmother", "grandfather"])
    return StoryParams(
        place=place,
        spot=spot,
        light=light,
        tuna=tuna,
        name=name,
        gender=gender,
        guardian=guardian,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.tuna not in TUNA_OFFERS:
        raise StoryError(f"(Unknown tuna option: {params.tuna})")

    setting = SETTINGS[params.place]
    spot = SPOTS[params.spot]
    light = LIGHTS[params.light]
    tuna = TUNA_OFFERS[params.tuna]

    if not spot_in_place(setting, spot):
        raise StoryError(explain_spot(setting, spot))
    if not usable_light(setting, light) or light.sense < SENSE_MIN:
        raise StoryError(explain_light(setting, light))
    if not good_tuna(setting, tuna):
        raise StoryError(explain_tuna(setting, tuna))

    world = tell(
        setting=setting,
        spot=spot,
        light=light,
        offer=tuna,
        name=params.name,
        gender=params.gender,
        guardian_type=params.guardian,
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
        print(asp_program("", "#show valid/4.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, spot, light, tuna) combos:\n")
        for place, spot, light, tuna in combos:
            print(f"  {place:10} {spot:16} {light:10} {tuna}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.place}, {p.spot}, {p.light}, {p.tuna}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
