#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py
===============================================================================

A standalone fairy-tale story world about a child preparing for a moonlit feast,
a tray of manicotti that goes missing, and a small mystery solved by noticing a
strange sweep and rhythm in the room.

This world models a gentle "Mystery to Solve" domain:
- a feast is being prepared
- a treasured dish of manicotti disappears
- clues appear in the world state
- the hero follows those clues
- the missing dish is found
- the ending reveals a kind surprise rather than a villain

The simulation uses:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining causal engine
- a reasonableness gate over culprit/hideout combinations
- an inline ASP twin for parity checks
- state-grounded Q&A sets

Run it
------
python storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py
python storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py --all
python storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py --verify
python storyworlds/worlds/gpt-5.4/sweep_rhythm_manicotti_surprise_mystery_to_solve.py --json
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
    kind: str = "thing"          # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fairy_godmother", "princess"}
        male = {"boy", "father", "man", "wizard", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "fairy_godmother": "godmother",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
    glow: str
    sweep_line: str
    feast_name: str
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
class Culprit:
    id: str
    label: str
    type: str
    motive: str
    clue_kind: str
    rhythm_sound: str
    move_verb: str
    kind_heart: bool = True
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
class Hideout:
    id: str
    label: str
    phrase: str
    warm: bool
    sheltered: bool
    clue_surface: str
    fits: set[str] = field(default_factory=set)
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
    type: str
    arrival: str
    comfort: str
    lesson: str
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
    use: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_missing_causes_worry(world: World) -> list[str]:
    tray = world.get("tray")
    hero = world.get("hero")
    hall = world.get("hall")
    if tray.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", "tray_missing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hall.meters["feast_risk"] += 1
    return ["__worry__"]


def _r_hidden_makes_clues(world: World) -> list[str]:
    tray = world.get("tray")
    clues = world.get("clues")
    if tray.meters["hidden"] < THRESHOLD:
        return []
    sig = ("clues", "hidden_tray")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clues.meters["trail"] += 1
    clues.meters["rhythm"] += 1
    return ["__clues__"]


def _r_found_relief(world: World) -> list[str]:
    tray = world.get("tray")
    hero = world.get("hero")
    hall = world.get("hall")
    if tray.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "tray_found")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    hall.meters["feast_risk"] = 0.0
    return ["__relief__"]


def _r_kind_truth_softens_fear(world: World) -> list[str]:
    culprit = world.get("culprit")
    hero = world.get("hero")
    if culprit.memes["forgiven"] < THRESHOLD:
        return []
    sig = ("forgiveness", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0.0
    hero.memes["gratitude"] += 1
    culprit.memes["belonging"] += 1
    return ["__forgiveness__"]


CAUSAL_RULES = [
    Rule(name="missing_causes_worry", tag="emotional", apply=_r_missing_causes_worry),
    Rule(name="hidden_makes_clues", tag="physical", apply=_r_hidden_makes_clues),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="kind_truth_softens_fear", tag="social", apply=_r_kind_truth_softens_fear),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def hideout_fits(culprit: Culprit, hideout: Hideout) -> bool:
    return culprit.id in hideout.fits


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id, culprit in CULPRITS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if not hideout_fits(culprit, hideout):
                    continue
                for helper_id in HELPERS:
                    combos.append((setting_id, culprit_id, hideout_id, helper_id))
    return combos


def explain_rejection(culprit: Culprit, hideout: Hideout) -> str:
    return (
        f"(No story: {culprit.label} would not sensibly hide the manicotti in "
        f"{hideout.phrase}. Pick a hideout that fits this culprit's way of moving and motive.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_clues(culprit: Culprit, hideout: Hideout) -> dict:
    trail = {
        "broom_sprite": "silver sweep marks",
        "mouse_page": "tiny floury footmarks",
        "wind_sprite": "a curling ribbon of flour dust",
    }[culprit.id]
    rhythm = culprit.rhythm_sound
    return {
        "trail_text": trail,
        "rhythm_text": rhythm,
        "warm": hideout.warm,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, setting: Setting, helper: Helper) -> None:
    world.say(
        f"Once, in {setting.place}, there lived {hero.id}, a little {hero.type} "
        f"with a patient heart. On the night of the {setting.feast_name}, "
        f"{hero.pronoun()} helped {helper.label} make the hall ready."
    )
    world.say(setting.glow)
    world.say(setting.sweep_line)


def cook(world: World, hero: Entity, helper: Helper) -> None:
    tray = world.get("tray")
    hero.memes["joy"] += 1
    tray.meters["warm"] = 1.0
    world.say(
        f"From the oven came a grand tray of manicotti, wrapped in steam and "
        f"smelling of cheese, herbs, and butter. {helper.label.capitalize()} set it "
        f"on the table to cool while {hero.id} hummed a happy rhythm and laid out plates."
    )


def turn_away(world: World, hero: Entity, helper: Helper) -> None:
    world.say(
        f"For only a minute, {helper.label} stepped into the pantry for a jar of "
        f"moon-pear jam, and {hero.id} turned to hang a garland of little gold stars."
    )


def vanish(world: World, culprit: Culprit, hideout: Hideout) -> None:
    tray = world.get("tray")
    culprit_ent = world.get("culprit")
    tray.meters["missing"] += 1
    tray.meters["hidden"] += 1
    tray.attrs["hideout"] = hideout.id
    culprit_ent.attrs["hideout"] = hideout.id
    culprit_ent.attrs["motive"] = culprit.motive
    culprit_ent.memes["secret"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {hero_name(world)} looked back, the tray was gone. Not a single manicotti "
        f"rested on the table, only a startled empty cloth."
    )


def worry(world: World, hero: Entity, helper: Helper) -> None:
    world.say(
        f'"Oh!" cried {hero.id}. "The manicotti has vanished!" '
        f"{helper.label.capitalize()} hurried back, and both of them stared in astonishment."
    )
    world.say(
        f"{hero.id}'s heart gave one worried thump. Without the feast dish, the hall felt "
        f"as if one bright candle had gone dim."
    )


def notice_clues(world: World, hero: Entity, culprit: Culprit, hideout: Hideout) -> None:
    pred = predict_clues(culprit, hideout)
    world.facts["predicted_trail"] = pred["trail_text"]
    world.facts["predicted_rhythm"] = pred["rhythm_text"]
    world.say(
        f"Then {hero.id} knelt and looked carefully. Across {hideout.clue_surface}, "
        f"{hero.pronoun()} saw {pred['trail_text']} curling away from the table."
    )
    world.say(
        f"And from far off came a tiny rhythm — {pred['rhythm_text']} — as if the room "
        f"itself were whispering where to search."
    )


def follow_clues(world: World, hero: Entity, hideout: Hideout) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'"This is not a wicked spell," said {hero.id}. "It is a clue." So {hero.pronoun()} '
        f"followed the marks past the candles, around the long bench, and toward {hideout.phrase}."
    )


def discover(world: World, hero: Entity, culprit: Culprit, hideout: Hideout) -> None:
    tray = world.get("tray")
    culprit_ent = world.get("culprit")
    tray.meters["found"] += 1
    tray.meters["missing"] = 0.0
    culprit_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There, tucked {hideout.label}, sat the missing tray of manicotti — still safe, "
        f"and nearly as warm as before."
    )
    world.say(
        f"Beside it was {culprit.label}, looking more shy than sly."
    )


def truth(world: World, hero: Entity, culprit: Culprit, helper: Helper, hideout: Hideout) -> None:
    culprit_ent = world.get("culprit")
    culprit_ent.memes["forgiven"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did not mean to steal supper," {culprit.label} confessed. "I {culprit.move_verb} it to '
        f"{hideout.phrase} because {culprit.motive}." 
    )
    world.say(
        f"{helper.label.capitalize()} listened, and the hard edge of the mystery melted away. "
        f"It had been a foolish choice, but not a cruel one."
    )


def surprise(world: World, hero: Entity, culprit: Culprit, helper: Helper, gift: Gift) -> None:
    hero.memes["joy"] += 1
    culprit_ent = world.get("culprit")
    culprit_ent.memes["joy"] += 1
    world.say(
        f"Then came the surprise. Instead of sending {culprit.label} away, {helper.label} smiled "
        f"and brought out {gift.phrase}."
    )
    world.say(
        f'"If you wished to help," {helper.label} said, "then help us properly." Soon {culprit.label} '
        f"used {gift.label} {gift.use}, and the whole hall seemed to wake into song."
    )


def ending(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"When the feast began, the manicotti shone on the table, the candles trembled in a gentle "
        f"golden light, and every broom, spoon, and slipper seemed to keep a merry rhythm together."
    )
    world.say(
        f"From that night on, whenever {hero.id} heard a soft sweep in the corner, "
        f"{hero.pronoun()} smiled instead of worrying, for {hero.pronoun()} knew that mysteries "
        f"could end in kindness as well as surprise."
    )


def hero_name(world: World) -> str:
    return world.get("hero").id


# ---------------------------------------------------------------------------
# Story orchestration
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    culprit: Culprit,
    hideout: Hideout,
    helper: Helper,
    gift: Gift,
    *,
    hero_name_value: str = "Mira",
    hero_type: str = "girl",
) -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name_value,
        kind="character",
        type=hero_type,
        label=hero_name_value,
        role="hero",
        traits=["careful", "kind"],
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type,
        label=helper.label,
        role="helper",
        tags=set(helper.tags),
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="character",
        type=culprit.type,
        label=culprit.label,
        role="culprit",
        tags=set(culprit.tags),
    ))
    hall = world.add(Entity(
        id="hall",
        kind="place",
        type="hall",
        label=setting.place,
        role="setting",
        tags=set(setting.tags),
    ))
    tray = world.add(Entity(
        id="tray",
        kind="thing",
        type="food",
        label="tray of manicotti",
        role="treasure",
        tags={"manicotti", "feast"},
    ))
    clues = world.add(Entity(
        id="clues",
        kind="thing",
        type="clue",
        label="clues",
        role="clues",
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        role="gift",
        tags=set(gift.tags),
    ))

    world.facts.update(
        setting=setting,
        culprit_cfg=culprit,
        hideout_cfg=hideout,
        helper_cfg=helper,
        gift_cfg=gift,
        hero=hero,
        helper=helper_ent,
        culprit=culprit_ent,
        hall=hall,
        tray=tray,
        clues=clues,
        found=False,
        resolved=False,
        surprise=False,
    )

    introduce(world, hero, setting, helper)
    cook(world, hero, helper)
    turn_away(world, hero, helper)

    world.para()
    vanish(world, culprit, hideout)
    worry(world, hero, helper)
    notice_clues(world, hero, culprit, hideout)
    follow_clues(world, hero, hideout)

    world.para()
    discover(world, hero, culprit, hideout)
    truth(world, hero, culprit, helper, hideout)
    surprise(world, hero, culprit, helper, gift)
    ending(world, hero, setting)

    world.facts.update(
        found=tray.meters["found"] >= THRESHOLD,
        resolved=culprit_ent.memes["forgiven"] >= THRESHOLD,
        surprise=True,
        hideout=hideout,
        tray_warm=hideout.warm,
        clue_kind=culprit.clue_kind,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_hall": Setting(
        id="moon_hall",
        place="the Moonbeam Hall beside the silver well",
        glow="Blue lanterns shone in the windows, and the floor sparkled like a lake under the moon.",
        sweep_line="With a willow broom, the child gave the floor a gentle sweep, and the bristles whispered over the stones.",
        feast_name="Lantern Feast",
        tags={"hall", "feast"},
    ),
    "rose_kitchen": Setting(
        id="rose_kitchen",
        place="the Rose Kitchen under the old castle stairs",
        glow="Copper pans glimmered overhead, and rose-colored firelight danced across the tiles.",
        sweep_line="A soft sweep of straw over the kitchen floor sent flour dust floating like tiny stars.",
        feast_name="Lantern Feast",
        tags={"kitchen", "castle"},
    ),
    "sunny_bakery": Setting(
        id="sunny_bakery",
        place="the Sunlit Bakery at the edge of the market square",
        glow="Sugar jars winked on the shelves, and warm lamplight made the window glass glow like amber.",
        sweep_line="Before the guests came, the little helper made one neat sweep after another, until the bakery floor shone clean.",
        feast_name="Lantern Feast",
        tags={"bakery", "market"},
    ),
}

CULPRITS = {
    "broom_sprite": Culprit(
        id="broom_sprite",
        label="a broom sprite with a straw-bright cap",
        type="sprite",
        motive="it feared the tray would cool before the guests arrived and wanted to tuck it somewhere snug",
        clue_kind="sweep",
        rhythm_sound="swish-tap, swish-tap",
        move_verb="swept",
        kind_heart=True,
        tags={"sprite", "sweep"},
    ),
    "mouse_page": Culprit(
        id="mouse_page",
        label="a palace mouse in a pageboy ribbon",
        type="mouse",
        motive="its hungry little brothers were peeking from the shadows and it wished to guard a warm corner for them",
        clue_kind="footprints",
        rhythm_sound="patter-pat, patter-pat",
        move_verb="dragged",
        kind_heart=True,
        tags={"mouse", "mystery"},
    ),
    "wind_sprite": Culprit(
        id="wind_sprite",
        label="a wind sprite with flour on its nose",
        type="sprite",
        motive="it heard the window rattling and wanted to hide the dish where no cold draft could touch it",
        clue_kind="flour_swirl",
        rhythm_sound="hush-hum, hush-hum",
        move_verb="blew",
        kind_heart=True,
        tags={"wind", "rhythm"},
    ),
}

HIDEOUTS = {
    "bench_nook": Hideout(
        id="bench_nook",
        label="beneath the moon-carved bench",
        phrase="beneath the moon-carved bench",
        warm=True,
        sheltered=True,
        clue_surface="the flagstones",
        fits={"broom_sprite", "mouse_page"},
        tags={"bench"},
    ),
    "oven_alcove": Hideout(
        id="oven_alcove",
        label="inside the warm oven alcove",
        phrase="inside the warm oven alcove",
        warm=True,
        sheltered=True,
        clue_surface="the flour-dusted tiles",
        fits={"broom_sprite", "wind_sprite"},
        tags={"oven", "warmth"},
    ),
    "curtain_cradle": Hideout(
        id="curtain_cradle",
        label="behind the velvet curtain cradle",
        phrase="behind the velvet curtain cradle",
        warm=False,
        sheltered=True,
        clue_surface="the polished floor",
        fits={"mouse_page", "wind_sprite"},
        tags={"curtain"},
    ),
}

HELPERS = {
    "godmother": Helper(
        id="godmother",
        label="the fairy godmother",
        type="fairy_godmother",
        arrival="with slippers soft as feathers",
        comfort="kind eyes",
        lesson="look closely before you blame",
        tags={"fairy"},
    ),
    "baker": Helper(
        id="baker",
        label="the village baker",
        type="woman",
        arrival="with flour on her sleeves",
        comfort="warm hands",
        lesson="look closely before you blame",
        tags={"baker"},
    ),
    "gardener": Helper(
        id="gardener",
        label="the castle gardener",
        type="man",
        arrival="with rosemary tucked behind one ear",
        comfort="a calm voice",
        lesson="look closely before you blame",
        tags={"garden"},
    ),
}

GIFTS = {
    "bell_spoon": Gift(
        id="bell_spoon",
        label="a silver bell-spoon",
        phrase="a silver bell-spoon tied with a blue ribbon",
        use="to tap a bright table-rhythm while the guests came in",
        tags={"spoon", "rhythm"},
    ),
    "star_napkin": Gift(
        id="star_napkin",
        label="a star-stitched napkin",
        phrase="a star-stitched napkin folded like a lily",
        use="to carry warm plates from guest to guest",
        tags={"napkin", "feast"},
    ),
    "tiny_apron": Gift(
        id="tiny_apron",
        label="a tiny blue apron",
        phrase="a tiny blue apron with moon-thread at the hem",
        use="to help set out bread without getting dust on the dishes",
        tags={"apron", "help"},
    ),
}

GIRL_NAMES = ["Mira", "Elin", "Tessa", "Lina", "Nora", "Pia", "Wren", "Sela"]
BOY_NAMES = ["Tobin", "Milo", "Arin", "Leo", "Nico", "Bram", "Oren", "Finn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    culprit: str
    hideout: str
    helper: str
    gift: str
    hero_name: str
    hero_type: str
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
    "manicotti": [
        (
            "What is manicotti?",
            "Manicotti is a kind of pasta shaped like little tubes, often filled with cheese or other soft food and baked in sauce."
        )
    ],
    "sweep": [
        (
            "What does sweep mean?",
            "To sweep means to move a broom across the floor to gather dust or crumbs together. It can also describe a soft, gliding motion."
        )
    ],
    "rhythm": [
        (
            "What is a rhythm?",
            "A rhythm is a pattern of sounds or beats that repeats, like tap-tap, pause, tap-tap. People can hear rhythm in music, footsteps, or little working sounds."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. It points your mind in the right direction."
        )
    ],
    "sprite": [
        (
            "What is a sprite in a fairy tale?",
            "A sprite is a tiny magical creature from stories. Sprites are often quick, secretive, and tied to wind, water, light, or household things."
        )
    ],
    "kindness": [
        (
            "Why is it good to ask questions before blaming someone?",
            "It helps you learn what really happened. Sometimes a mistake comes from worry or confusion, not meanness."
        )
    ],
}
KNOWLEDGE_ORDER = ["manicotti", "sweep", "rhythm", "clue", "sprite", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    culprit = f["culprit_cfg"]
    return [
        (
            f'Write a fairy-tale story for a 3-to-5-year-old where a child in {setting.place} '
            f'must solve a gentle mystery after a tray of manicotti disappears. Include the words '
            f'"sweep" and "rhythm".'
        ),
        (
            f"Tell a magical mystery where {hero.id} notices a strange clue on the floor and follows "
            f"it to discover that {culprit.label} took the food for a surprising reason."
        ),
        (
            'Write a child-facing fairy tale with a surprise ending in which missing manicotti leads '
            "to worry first, then careful clue-following, then kindness."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper_cfg = f["helper_cfg"]
    culprit = f["culprit_cfg"]
    hideout = f["hideout_cfg"]
    trail = f.get("predicted_trail", "a trail")
    rhythm = f.get("predicted_rhythm", "a tiny sound")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} helping {helper_cfg.label} get ready for the feast. "
            f"The story also includes {culprit.label}, who caused the mystery."
        ),
        (
            "What went missing?",
            "A tray of manicotti went missing from the table. That disappearance is what turned the feast into a mystery."
        ),
        (
            f"How did {hero.id} begin to solve the mystery?",
            f"{hero.id} looked closely instead of panicking and noticed {trail}. "
            f"{hero.pronoun().capitalize()} also listened to the tiny rhythm, {rhythm}, which pointed toward the hiding place."
        ),
        (
            f"Where was the manicotti found?",
            f"It was found {hideout.phrase}. The tray was hidden there because that spot felt safer or warmer than the table."
        ),
        (
            f"Why did {culprit.label} take the manicotti?",
            f"{culprit.label.capitalize()} took it because {culprit.motive}. "
            f"It was still a mistake, but the reason came from worry and wanting to help, not from cruelty."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that the helper did not chase the culprit away. Instead, {helper_cfg.label} invited the culprit to help with the feast and gave a small gift for the work."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"manicotti", "sweep", "rhythm", "clue", "kindness"}
    culprit = world.facts["culprit_cfg"]
    if "sprite" in culprit.tags:
        tags.add("sprite")
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
        bits: list[str] = []
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(C,H) :- culprit(C), hideout(H), fit(C,H).

valid(S,C,H,Hp) :- setting(S), culprit(C), hideout(H), helper(Hp), fits(C,H).

found_warm :- chosen_hideout(H), warm(H).
found_cool :- chosen_hideout(H), not warm(H).

clue_sweep :- chosen_culprit(broom_sprite).
clue_footprints :- chosen_culprit(mouse_page).
clue_flour_swirl :- chosen_culprit(wind_sprite).

outcome(kind_surprise) :- valid(_,_,_,_), chosen_setting(_), chosen_culprit(_), chosen_hideout(_), chosen_helper(_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if hideout.warm:
            lines.append(asp.fact("warm", hid))
        for cid in sorted(hideout.fits):
            lines.append(asp.fact("fit", cid, hid))
    for hp in HELPERS:
        lines.append(asp.fact("helper", hp))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for p in cases:
        if asp_outcome(p) != "kind_surprise":
            rc = 1
            print("MISMATCH in outcome:", p)

    try:
        sample = generate(CURATED[0])
        if not sample.story or "manicotti" not in sample.story:
            raise StoryError("Smoke test failed: generated story missing expected content.")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery storyworld: a missing tray of manicotti, a curious child, and a kind surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.hideout:
        culprit = CULPRITS[args.culprit]
        hideout = HIDEOUTS[args.hideout]
        if not hideout_fits(culprit, hideout):
            raise StoryError(explain_rejection(culprit, hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, hideout_id, helper_id = rng.choice(sorted(combos))
    gift_id = args.gift or rng.choice(sorted(GIFTS.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        hideout=hideout_id,
        helper=helper_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")

    culprit = CULPRITS[params.culprit]
    hideout = HIDEOUTS[params.hideout]
    if not hideout_fits(culprit, hideout):
        raise StoryError(explain_rejection(culprit, hideout))

    world = tell(
        SETTINGS[params.setting],
        culprit,
        hideout,
        HELPERS[params.helper],
        GIFTS[params.gift],
        hero_name_value=params.hero_name,
        hero_type=params.hero_type,
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


CURATED = [
    StoryParams(
        setting="moon_hall",
        culprit="broom_sprite",
        hideout="oven_alcove",
        helper="godmother",
        gift="bell_spoon",
        hero_name="Mira",
        hero_type="girl",
    ),
    StoryParams(
        setting="rose_kitchen",
        culprit="mouse_page",
        hideout="bench_nook",
        helper="baker",
        gift="tiny_apron",
        hero_name="Tobin",
        hero_type="boy",
    ),
    StoryParams(
        setting="sunny_bakery",
        culprit="wind_sprite",
        hideout="curtain_cradle",
        helper="gardener",
        gift="star_napkin",
        hero_name="Elin",
        hero_type="girl",
    ),
    StoryParams(
        setting="moon_hall",
        culprit="wind_sprite",
        hideout="oven_alcove",
        helper="baker",
        gift="bell_spoon",
        hero_name="Arin",
        hero_type="boy",
    ),
    StoryParams(
        setting="rose_kitchen",
        culprit="broom_sprite",
        hideout="bench_nook",
        helper="godmother",
        gift="tiny_apron",
        hero_name="Lina",
        hero_type="girl",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, culprit, hideout, helper) combos:\n")
        for setting_id, culprit_id, hideout_id, helper_id in combos:
            print(f"  {setting_id:13} {culprit_id:12} {hideout_id:15} {helper_id}")
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
            header = (
                f"### {p.hero_name}: {p.culprit} hid the manicotti in {p.hideout} "
                f"at {p.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
