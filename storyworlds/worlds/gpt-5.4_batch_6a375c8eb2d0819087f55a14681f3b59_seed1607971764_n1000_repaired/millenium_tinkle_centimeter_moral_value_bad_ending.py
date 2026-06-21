#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py
=================================================================================

A standalone storyworld about children pretending to be superheroes. A prized
hero item gets stuck high above the ground at a millenium landmark, one child
tries a risky shortcut to reach it, a sidekick warns about the danger, and a
grown-up may or may not save the day in time.

The moral value is simple and child-facing: real bravery includes asking for
help instead of taking a dangerous shortcut. Some valid stories end sadly: the
child stays safe, but the treasured hero item is lost because help came too
late or the chosen rescue was too weak.

Run it
------
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py --setting plaza --prize badge
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py --perch low_rail
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py --response leap
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/millenium_tinkle_centimeter_moral_value_bad_ending.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
CHILD_REACH_CM = 120
STRETCH_MARGIN_CM = 10
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    bell_line: str
    loss_place: str
    skyline: str
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
class Prize:
    id: str
    label: str
    phrase: str
    flair: str
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
class Perch:
    id: str
    label: str
    the: str
    height_cm: int
    snag_line: str
    risk: int
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
class Shortcut:
    id: str
    label: str
    phrase: str
    reach_bonus: int
    wobble_text: str
    risk: int
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
class Response:
    id: str
    sense: int
    power: int
    text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    support = world.get("support")
    if support.meters["climbed"] < THRESHOLD or not support.attrs.get("unstable", False):
        return out
    sig = ("wobble", support.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    support.meters["wobble"] += 1
    hero.memes["fear"] += 1
    world.get("place").meters["danger"] += 1
    out.append("__wobble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    support = world.get("support")
    if support.meters["wobble"] < THRESHOLD or prize.meters["snagged"] < THRESHOLD:
        return out
    sig = ("fall", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["falling"] += 1
    prize.meters["in_hand"] = 0.0
    hero = world.get("hero")
    hero.memes["shock"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


SETTINGS = {
    "plaza": Setting(
        id="plaza",
        place="Millenium Plaza",
        detail="At the edge of the square, an old sign still used the word millenium in peeling blue paint.",
        bell_line="From the clock tower came a soft tinkle that sounded like a hero signal.",
        loss_place="the storm drain beside the fountain",
        skyline="the bright square and its tall clock tower",
        tags={"clock", "plaza"},
    ),
    "library": Setting(
        id="library",
        place="Millenium Library Steps",
        detail="The stone arch above the doors still said millenium in tiny gold letters.",
        bell_line="A little service bell by the book return gave a neat tinkle in the breeze.",
        loss_place="the narrow grate by the curb",
        skyline="the broad steps and the lion statues",
        tags={"library", "bell"},
    ),
    "station": Setting(
        id="station",
        place="Millenium Station Walk",
        detail="A faded mural near the tracks spelled millenium the old funny way.",
        bell_line="Far down the platform, a crossing bell went tinkle-tinkle before falling quiet again.",
        loss_place="the gap behind the flower tubs",
        skyline="the windy walkway and the long red roof",
        tags={"station", "bell"},
    ),
}

PRIZES = {
    "cape": Prize(
        id="cape",
        label="cape",
        phrase="a shiny red cape with a silver star clasp",
        flair="The cloth flashed behind the child like a tiny comet tail.",
        tags={"cape", "costume"},
    ),
    "mask": Prize(
        id="mask",
        label="mask",
        phrase="a blue hero mask with little golden lightning bolts",
        flair="It made every serious look feel twice as brave.",
        tags={"mask", "costume"},
    ),
    "badge": Prize(
        id="badge",
        label="badge",
        phrase="a round rescue badge that glittered like a coin",
        flair="In the sun it looked almost important enough for a real city hero.",
        tags={"badge", "costume"},
    ),
}

PERCHES = {
    "statue_hand": Perch(
        id="statue_hand",
        label="statue hand",
        the="the bronze hero statue's hand",
        height_cm=170,
        snag_line="A gust had lifted it onto the raised hand of the bronze hero statue.",
        risk=2,
        tags={"statue", "high"},
    ),
    "tree_branch": Perch(
        id="tree_branch",
        label="tree branch",
        the="the low tree branch",
        height_cm=175,
        snag_line="A puff of wind had wrapped it over a branch above the path.",
        risk=2,
        tags={"tree", "high"},
    ),
    "lamp_hook": Perch(
        id="lamp_hook",
        label="lamp hook",
        the="the iron lamp hook",
        height_cm=182,
        snag_line="A swoop of wind had caught it on the old iron hook under a lamp.",
        risk=3,
        tags={"lamp", "high"},
    ),
    "low_rail": Perch(
        id="low_rail",
        label="low rail",
        the="the low rail",
        height_cm=126,
        snag_line="It had only landed on a low rail near the path.",
        risk=1,
        tags={"low"},
    ),
}

SHORTCUTS = {
    "crate_stack": Shortcut(
        id="crate_stack",
        label="stack of milk crates",
        phrase="a stack of milk crates",
        reach_bonus=45,
        wobble_text="The crates gave a hollow clack and shivered under small shoes.",
        risk=2,
        tags={"crates", "climb"},
    ),
    "rolling_bin": Shortcut(
        id="rolling_bin",
        label="rolling bin",
        phrase="a rolling recycling bin",
        reach_bonus=50,
        wobble_text="The bin twitched on its wheels and slid sideways with a scrape.",
        risk=3,
        tags={"bin", "climb"},
    ),
    "scooter_seat": Shortcut(
        id="scooter_seat",
        label="parked scooter seat",
        phrase="the seat of a parked scooter",
        reach_bonus=40,
        wobble_text="The scooter rocked sharply, making everything around it look suddenly too high.",
        risk=3,
        tags={"scooter", "climb"},
    ),
}

RESPONSES = {
    "ladder": Response(
        id="ladder",
        sense=4,
        power=5,
        text="brought the little folding ladder from the shed and climbed carefully until the {prize} was safe in one steady hand",
        fail="hurried over with the folding ladder, but the {prize} slipped away before it could be reached",
        qa_text="used a folding ladder and got the {prize} down safely",
        tags={"ladder", "help"},
    ),
    "grabber": Response(
        id="grabber",
        sense=3,
        power=4,
        text="used the long grabber claw from the closet to pinch the {prize} and lift it free",
        fail="stretched with the long grabber claw, but the {prize} spun just out of reach",
        qa_text="used a long grabber claw to lift the {prize} down",
        tags={"grabber", "help"},
    ),
    "blanket": Response(
        id="blanket",
        sense=2,
        power=3,
        text="spread a thick blanket under the wobbling place and caught the falling {prize} before it could vanish",
        fail="spread a blanket to catch the {prize}, but it bounced away too fast",
        qa_text="caught the falling {prize} with a blanket",
        tags={"blanket", "catch"},
    ),
    "leap": Response(
        id="leap",
        sense=1,
        power=1,
        text="jumped and snatched for the {prize}",
        fail="jumped for the {prize}, but missed",
        qa_text="jumped for the {prize}",
        tags={"jump"},
    ),
}

GIRL_NAMES = ["Nova", "Mia", "Lila", "Ava", "Ruby", "Zoe", "Nina", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Theo", "Sam", "Kai", "Noah"]
TRAITS = ["careful", "thoughtful", "quick", "kind", "steady", "cautious"]


def hazard_at_risk(perch: Perch, shortcut: Shortcut) -> bool:
    if perch.height_cm <= CHILD_REACH_CM + STRETCH_MARGIN_CM:
        return False
    max_reach = CHILD_REACH_CM + shortcut.reach_bonus + STRETCH_MARGIN_CM
    return perch.height_cm <= max_reach


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(perch: Perch, shortcut: Shortcut, delay: int) -> int:
    return perch.risk + shortcut.risk + delay


def is_recovered(response: Response, perch: Perch, shortcut: Shortcut, delay: int) -> bool:
    return response.power >= severity_of(perch, shortcut, delay)


def explain_rejection(perch: Perch, shortcut: Shortcut) -> str:
    if perch.height_cm <= CHILD_REACH_CM + STRETCH_MARGIN_CM:
        return (
            f"(No story: {perch.the} is only about {perch.height_cm} centimeters high, "
            f"so a child could likely reach it from the ground. There is no honest need "
            f"for a dangerous shortcut.)"
        )
    return (
        f"(No story: even using {shortcut.phrase}, the child still could not plausibly "
        f"reach {perch.the}. This world only tells tempting near-reach problems.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak or foolish for this world "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for prize_id in PRIZES:
            for perch_id, perch in PERCHES.items():
                for shortcut_id, shortcut in SHORTCUTS.items():
                    if hazard_at_risk(perch, shortcut):
                        combos.append((setting_id, prize_id, perch_id, shortcut_id))
    return combos


def predict_fall(world: World) -> dict:
    sim = world.copy()
    support = sim.get("support")
    support.meters["climbed"] += 1
    propagate(sim, narrate=False)
    prize = sim.get("prize")
    return {
        "wobble": support.meters["wobble"] >= THRESHOLD,
        "falling": prize.meters["falling"] >= THRESHOLD,
        "danger": sim.get("place").meters["danger"],
    }


def opening(world: World, hero: Entity, sidekick: Entity, setting: Setting, prize: Prize) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {sidekick.id} hurried across {setting.place} as if "
        f"they were on patrol over {setting.skyline}."
    )
    world.say(setting.detail)
    world.say(setting.bell_line)
    world.say(
        f"{hero.id} wore {prize.phrase}. {prize.flair}"
    )


def snag(world: World, hero: Entity, sidekick: Entity, prize: Prize, perch: Perch) -> None:
    world.say(
        f"Then trouble came in one windy swoop. {perch.snag_line} In one blink, "
        f"{hero.id}'s {prize.label} was stuck high above both children."
    )
    hero.memes["alarm"] += 1
    sidekick.memes["concern"] += 1


def boast(world: World, hero: Entity, shortcut: Shortcut, perch: Perch) -> None:
    gap = max(1, perch.height_cm - (CHILD_REACH_CM + shortcut.reach_bonus))
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} pointed to {shortcut.phrase}. "That will do it," {hero.pronoun()} said. '
        f'"I only need one more centimeter."'
    )
    if gap > 1:
        world.say(f"It was more than a centimeter, but the high-up prize made the shortcut feel clever anyway.")


def warn(world: World, sidekick: Entity, hero: Entity, shortcut: Shortcut, perch: Perch, parent: Entity) -> None:
    pred = predict_fall(world)
    sidekick.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{sidekick.id} grabbed {hero.pronoun("possessive")} sleeve. '
        f'"Real heroes ask for help," {sidekick.pronoun()} said. '
        f'"If you climb {shortcut.phrase}, it could wobble and make the {world.get("prize").label} fall. '
        f'Let\'s call {parent.label_word} instead."'
    )


def defy(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the mission felt too exciting to pause. {hero.id} put one foot on "
        f"{shortcut.phrase} and reached up."
    )


def climb_and_wobble(world: World, hero: Entity, shortcut: Shortcut, prize: Prize, perch: Perch) -> None:
    support = world.get("support")
    support.meters["climbed"] += 1
    propagate(world, narrate=False)
    world.say(shortcut.wobble_text)
    world.say(
        f"{hero.id}'s fingers brushed the {prize.label}, but only for a breath. "
        f"{perch.The} was still just far enough away to turn the superhero game into a real danger."
    )
    if world.get("prize").meters["falling"] >= THRESHOLD:
        world.say(
            f"Then the snag came loose. The {prize.label} slipped free, spun through the air, "
            f"and dropped toward the ground."
        )


def alarm(world: World, sidekick: Entity, parent: Entity, prize: Prize) -> None:
    sidekick.memes["fear"] += 1
    world.say(f'"{parent.label_word.capitalize()}! Help!" {sidekick.id} shouted.')
    world.say(
        f"{hero_side(world)} were brave enough to stop pretending and call for a grown-up."
    )


def hero_side(world: World) -> str:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    return f"{hero.id} and {sidekick.id}"


def rescue(world: World, parent: Entity, response: Response, prize: Prize) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["falling"] = 0.0
    prize_ent.meters["safe"] += 1
    world.get("place").meters["danger"] = 0.0
    parent.memes["relief"] += 1
    text = response.text.replace("{prize}", prize.label)
    world.say(
        f"{parent.label_word.capitalize()} came fast and {text}."
    )
    world.say(
        f"In a moment the {prize.label} was back on the ground, and the children were safe too."
    )


def fail_rescue(world: World, parent: Entity, response: Response, prize: Prize, setting: Setting) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["falling"] = 0.0
    prize_ent.meters["lost"] += 1
    prize_ent.attrs["lost_place"] = setting.loss_place
    parent.memes["sadness"] += 1
    text = response.fail.replace("{prize}", prize.label)
    world.say(
        f"{parent.label_word.capitalize()} came running and {text}."
    )
    world.say(
        f"But the {prize.label} skittered away and disappeared into {setting.loss_place}."
    )


def lesson(world: World, hero: Entity, sidekick: Entity, parent: Entity, prize: Prize) -> None:
    for kid in (hero, sidekick):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "A cape or badge is not worth a fall," '
        f'{parent.pronoun()} said softly. "Real courage means stopping and asking for help before someone gets hurt."'
    )
    world.say(
        f"{hero.id} looked at {sidekick.id} and nodded. The mission had changed, and now the bravest thing was telling the truth about the mistake."
    )


def replacement(world: World, hero: Entity, sidekick: Entity, parent: Entity, prize: Prize) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word} brought out a toy rescue claw with a red handle. "
        f'"Superheroes use tools and teamwork," {parent.pronoun()} said.'
    )
    world.say(
        f"{hero.id} clipped the {prize.label} on carefully this time, and {hero_side(world)} went back on patrol with both feet on the ground."
    )


def sad_ending(world: World, hero: Entity, sidekick: Entity, parent: Entity, prize: Prize) -> None:
    for kid in (hero, sidekick):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    lost_place = world.get("prize").attrs.get("lost_place", world.setting.loss_place)
    world.say(
        f'{parent.label_word.capitalize()} held both children close. "I am glad you are safe," {parent.pronoun()} said. '
        f'"But sometimes a bad choice means we lose something we love."'
    )
    world.say(
        f"{hero.id} stared at {lost_place}, now quiet and dark. Without the {prize.label}, the superhero game ended early, and the square did not feel magical anymore."
    )
    world.say(
        f"After that, {hero.id} remembered that asking for help is part of being brave."
    )


def tell(
    setting: Setting,
    prize: Prize,
    perch: Perch,
    shortcut: Shortcut,
    response: Response,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    sidekick_name: str = "Max",
    sidekick_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 6,
    sidekick_age: int = 6,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["bold"],
        age=hero_age,
        attrs={"name": hero_name},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        traits=[trait],
        age=sidekick_age,
        attrs={"name": sidekick_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={"name": parent_type},
    ))
    place = world.add(Entity(
        id="place",
        type="place",
        label=setting.place,
        attrs={"loss_place": setting.loss_place},
    ))
    prize_ent = world.add(Entity(
        id="prize",
        type="prize",
        label=prize.label,
        phrase=prize.phrase,
        attrs={"flair": prize.flair},
    ))
    support = world.add(Entity(
        id="support",
        type="support",
        label=shortcut.label,
        phrase=shortcut.phrase,
        attrs={"unstable": True, "reach_bonus": shortcut.reach_bonus},
    ))

    prize_ent.meters["snagged"] = 1.0
    prize_ent.meters["in_hand"] = 0.0
    support.meters["climbed"] = 0.0
    support.meters["wobble"] = 0.0
    place.meters["danger"] = 0.0
    hero.memes["fear"] = 0.0
    sidekick.memes["fear"] = 0.0

    opening(world, hero, sidekick, setting, prize)
    snag(world, hero, sidekick, prize, perch)

    world.para()
    boast(world, hero, shortcut, perch)
    warn(world, sidekick, hero, shortcut, perch, parent)
    defy(world, hero, shortcut)

    world.para()
    climb_and_wobble(world, hero, shortcut, prize, perch)
    alarm(world, sidekick, parent, prize)

    world.para()
    recovered = is_recovered(response, perch, shortcut, delay)
    if recovered:
        rescue(world, parent, response, prize)
        lesson(world, hero, sidekick, parent, prize)
        world.para()
        replacement(world, hero, sidekick, parent, prize)
    else:
        fail_rescue(world, parent, response, prize, setting)
        sad_ending(world, hero, sidekick, parent, prize)

    outcome = "recovered" if recovered else "lost"
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        setting=setting,
        prize_cfg=prize,
        perch=perch,
        shortcut=shortcut,
        response=response,
        delay=delay,
        severity=severity_of(perch, shortcut, delay),
        outcome=outcome,
        recovered=recovered,
        predicted_fall=world.facts.get("predicted_danger", 0) >= 1,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    prize: str
    perch: str
    shortcut: str
    response: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    sidekick_age: int = 6
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
    "clock": [(
        "What does a clock tower bell do?",
        "A clock tower bell rings to mark the time. Its sound can be soft and clear, like a tinkle drifting across a square."
    )],
    "bell": [(
        "What does tinkle mean?",
        "Tinkle means a small, light ringing sound. People often use it for tiny bells or delicate metal sounds."
    )],
    "centimeter": [(
        "What is a centimeter?",
        "A centimeter is a small unit for measuring length. It is much shorter than a ruler's full length, so saying 'one more centimeter' means 'just a tiny bit farther.'"
    )],
    "ladder": [(
        "Why is a ladder safer than climbing on wobbly things?",
        "A ladder is made for reaching high places with steady steps. Wobbly piles can tip or slide and make someone fall."
    )],
    "grabber": [(
        "What is a grabber claw?",
        "A grabber claw is a long tool that helps you pick up something far away. It lets a grown-up reach without dangerous climbing."
    )],
    "blanket": [(
        "How can a blanket help catch something falling?",
        "If people hold a blanket tight, it can soften a fall for a light object. But it only works when they are fast and close enough."
    )],
    "cape": [(
        "What is a superhero cape?",
        "A superhero cape is a piece of costume cloth that hangs from the shoulders. It can look exciting in the wind, but it does not give real flying powers."
    )],
    "mask": [(
        "What is a superhero mask for?",
        "A superhero mask is part of a costume people wear for pretend play. It can make a game feel brave and special."
    )],
    "badge": [(
        "What is a badge?",
        "A badge is a small sign or token that shows a role or team. In pretend play, it can make a child feel important and ready to help."
    )],
    "help": [(
        "Why is asking for help brave?",
        "Asking for help shows that you care more about safety than about showing off. A brave person can stop, think, and call someone who can really help."
    )],
}
KNOWLEDGE_ORDER = [
    "clock", "bell", "centimeter", "ladder", "grabber", "blanket",
    "cape", "mask", "badge", "help",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].attrs["name"]
    sidekick = f["sidekick"].attrs["name"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that uses the words '
        f'"millenium", "tinkle", and "centimeter". The story should happen at {setting.place} '
        f'and include a child trying to reach a stuck {prize.label}.'
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a superhero-style cautionary story where {hero} ignores {sidekick}'s warning, "
            f"takes a risky shortcut, and stays safe but loses the treasured {prize.label}.",
            "Write a moral-value story with a bad ending that teaches that asking for help is part of real bravery.",
        ]
    return [
        base,
        f"Tell a gentle superhero story where {hero} learns that real heroes use tools and teamwork instead of risky climbing.",
        "Write a moral-value story that ends with a safer way to keep playing superhero.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    parent = f["parent"]
    prize = f["prize_cfg"]
    perch = f["perch"]
    shortcut = f["shortcut"]
    response = f["response"]
    setting = f["setting"]
    hero_name = hero.attrs["name"]
    sidekick_name = sidekick.attrs["name"]
    pw = parent.label_word

    qa = [
        (
            "Who is the story about?",
            f"It is about two children pretending to be superheroes, {hero_name} and {sidekick_name}. "
            f"Their adventure goes wrong when {hero_name}'s {prize.label} gets stuck high above them."
        ),
        (
            f"Where were {hero_name} and {sidekick_name} playing?",
            f"They were playing at {setting.place}. The place felt dramatic because of the old millenium sign and the little bell sound going tinkle nearby."
        ),
        (
            f"Why did {hero_name} say 'one more centimeter'?",
            f"{hero_name} wanted to believe the {prize.label} was almost close enough to grab. "
            f"Saying 'one more centimeter' made the dangerous shortcut sound smaller and safer than it really was."
        ),
        (
            f"Why did {sidekick_name} want to call {pw}?",
            f"{sidekick_name} understood that climbing on {shortcut.phrase} could wobble. "
            f"{sidekick_name} was trying to protect both {hero_name} and the stuck {prize.label} by asking for real help."
        ),
    ]
    if f["outcome"] == "recovered":
        body = response.qa_text.replace("{prize}", prize.label)
        qa.extend([
            (
                f"How did {pw} solve the problem?",
                f"{pw.capitalize()} {body}. That worked because the grown-up used a steadier rescue method than a child balancing on something wobbly."
            ),
            (
                "What was the lesson of the story?",
                f"The lesson was that real courage is not showing off. It is stopping, telling the truth, and asking for help before someone gets hurt."
            ),
            (
                "How did the story end?",
                f"It ended safely. The {prize.label} was saved, and the children went back to their superhero game in a new, wiser way."
            ),
        ])
    else:
        qa.extend([
            (
                f"Could {pw} save the {prize.label} in time?",
                f"No. {pw.capitalize()} tried to help, but the {prize.label} disappeared into {setting.loss_place} before it could be recovered."
            ),
            (
                "Why is the ending sad?",
                f"The children were safe, which matters most, but they still lost something special. "
                f"The sadness comes from learning that a bad choice can have a real cost even when nobody is hurt."
            ),
            (
                "What moral did the children learn?",
                f"They learned that asking for help is part of being brave. "
                f"If they had stopped sooner, they might have kept both their safety and the treasured {prize.label}."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["prize_cfg"].tags) | set(f["response"].tags) | {"centimeter", "help"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        name = ent.attrs.get("name", ent.label or ent.id)
        lines.append(f"  {ent.id:8} ({ent.type:8}) {name:16} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="plaza",
        prize="badge",
        perch="statue_hand",
        shortcut="crate_stack",
        response="ladder",
        hero="Nova",
        hero_gender="girl",
        sidekick="Max",
        sidekick_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        sidekick_age=6,
    ),
    StoryParams(
        setting="library",
        prize="cape",
        perch="tree_branch",
        shortcut="rolling_bin",
        response="grabber",
        hero="Leo",
        hero_gender="boy",
        sidekick="Ruby",
        sidekick_gender="girl",
        parent="father",
        trait="steady",
        delay=1,
        hero_age=7,
        sidekick_age=6,
    ),
    StoryParams(
        setting="station",
        prize="mask",
        perch="lamp_hook",
        shortcut="scooter_seat",
        response="blanket",
        hero="Mia",
        hero_gender="girl",
        sidekick="Finn",
        sidekick_gender="boy",
        parent="mother",
        trait="cautious",
        delay=1,
        hero_age=6,
        sidekick_age=6,
    ),
    StoryParams(
        setting="plaza",
        prize="cape",
        perch="lamp_hook",
        shortcut="rolling_bin",
        response="ladder",
        hero="Theo",
        hero_gender="boy",
        sidekick="Ivy",
        sidekick_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=2,
        hero_age=7,
        sidekick_age=5,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "recovered" if is_recovered(RESPONSES[params.response], PERCHES[params.perch], SHORTCUTS[params.shortcut], params.delay) else "lost"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
base_reach(120).
stretch_margin(10).
hazard(Perch, Shortcut) :-
    perch(Perch), shortcut(Shortcut),
    perch_height(Perch, H), base_reach(B), stretch_margin(M),
    H > B + M,
    shortcut_bonus(Shortcut, S),
    H <= B + S + M.

valid(Setting, Prize, Perch, Shortcut) :-
    setting(Setting), prize(Prize), hazard(Perch, Shortcut).

sensible(Response) :-
    response(Response), sense(Response, S), sense_min(M), S >= M.

% --- outcome model ----------------------------------------------------------
severity(V) :-
    chosen_perch(P), perch_risk(P, PR),
    chosen_shortcut(S), shortcut_risk(S, SR),
    delay(D), V = PR + SR + D.

recovered :-
    chosen_response(R), power(R, P), severity(V), P >= V.

outcome(recovered) :- recovered.
outcome(lost) :- not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("perch_height", pid, perch.height_cm))
        lines.append(asp.fact("perch_risk", pid, perch.risk))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("shortcut_bonus", sid, shortcut.reach_bonus))
        lines.append(asp.fact("shortcut_risk", sid, shortcut.risk))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superhero play, a risky shortcut, and the bravery of asking for help."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before the grown-up can act")
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and args.shortcut:
        perch = PERCHES[args.perch]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_at_risk(perch, shortcut):
            raise StoryError(explain_rejection(perch, shortcut))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.prize is None or combo[1] == args.prize)
        and (args.perch is None or combo[2] == args.perch)
        and (args.shortcut is None or combo[3] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, prize_id, perch_id, shortcut_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_name(rng)
    sidekick_name, sidekick_gender = _pick_name(rng, avoid=hero_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_age, sidekick_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        setting=setting_id,
        prize=prize_id,
        perch=perch_id,
        shortcut=shortcut_id,
        response=response_id,
        hero=hero_name,
        hero_gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent_type,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        sidekick_age=sidekick_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        prize = PRIZES[params.prize]
        perch = PERCHES[params.perch]
        shortcut = SHORTCUTS[params.shortcut]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err})") from None

    if not hazard_at_risk(perch, shortcut):
        raise StoryError(explain_rejection(perch, shortcut))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        setting=setting,
        prize=prize,
        perch=perch,
        shortcut=shortcut,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        sidekick_age=params.sidekick_age,
    )

    story = world.render().replace(" hero and sidekick ", " children ")
    hero_name = params.hero
    sidekick_name = params.sidekick
    story = story.replace("hero", hero_name, 1) if "hero" in story else story
    story = story.replace("sidekick", sidekick_name, 1) if "sidekick" in story else story

    return StorySample(
        params=params,
        story=story
            .replace("hero's", f"{hero_name}'s")
            .replace("hero ", f"{hero_name} ")
            .replace("sidekick ", f"{sidekick_name} "),
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, prize, perch, shortcut) combos:\n")
        for setting_id, prize_id, perch_id, shortcut_id in combos:
            print(f"  {setting_id:8} {prize_id:6} {perch_id:12} {shortcut_id}")
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
            header = (
                f"### {p.hero} & {p.sidekick}: {p.prize} at {p.setting} "
                f"({p.perch}, {p.shortcut}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
