#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py
=============================================================

A standalone story world for a small folk-tale domain about curiosity, disguise,
and the wiser path of asking honestly.

Base tale imagined from the seed
--------------------------------
Long ago, in a small village, a curious child saw a place that was meant for
grown-up work: a mill loft, a bell tower, or a herb room. The child wanted to
know what secret lay there. Instead of asking, the child decided to impersonate
the proper keeper by borrowing a cap, shawl, or coil of rope and climbing up
where small feet should not go alone. A wise elder warned that curiosity is a
good lantern only when carried with honesty. Sometimes the child listened at
once. Sometimes the child climbed, the ladder or barrel stack wobbled, and the
elder had to save them. In the end, the secret was shared the right way, and
the child learned that questions open more doors than costumes do.

Run it
------
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py --setting mill --mask miller_apron
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py --perch stone_bench
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/impersonate_curiosity_folk_tale.py --verify
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
CURIOSITY_INIT = 6.0
RECEPTIVE_TRAITS = {"heedful", "gentle", "patient", "careful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    village_intro: str
    place_name: str
    outer_view: str
    hidden_thing: str
    proper_role: str
    reveal_text: str
    closing_image: str
    perches: set[str] = field(default_factory=set)
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
class Mask:
    id: str
    role_name: str
    phrase: str
    borrowed_from: str
    costume_text: str
    belongs_to: str
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
    phrase: str
    wobble_text: str
    slip_text: str
    height: int
    wobble: int
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


@dataclass
class StoryParams:
    setting: str
    mask: str
    perch: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    delay: int = 0
    trust: int = 6
    token: str = ""
    pet: str = ""
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    perch = world.entities.get("perch")
    if child is None or perch is None:
        return out
    if perch.meters["wobbling"] < THRESHOLD:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.get("place").meters["danger"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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
    "mill": Setting(
        id="mill",
        village_intro="Long ago, beside a slow silver river, there stood a flour mill with a turning wheel.",
        place_name="the flour loft",
        outer_view="Through the upper slats, pale dust shone like moon-smoke.",
        hidden_thing="what the moon-smoke room looked like inside",
        proper_role="miller's helper",
        reveal_text="Inside were neat sacks of grain, a brass scoop, and flour drifting in soft white ribbons through the light.",
        closing_image="After that, the child climbed no farther than a doorstep without asking, and the mill loft seemed friendlier once its secret had been honestly shared.",
        perches={"ladder", "barrel_stack"},
        tags={"mill", "flour"},
    ),
    "tower": Setting(
        id="tower",
        village_intro="Long ago, on a hill above a little village, there stood a bell tower where swallows stitched the air.",
        place_name="the bell stair",
        outer_view="From the open arch, a bronze shine flashed whenever the sun moved.",
        hidden_thing="how the bell looked from up close",
        proper_role="bell-ringer",
        reveal_text="Inside waited the great bronze bell, swallow nests in the beams, and a thick rope smooth from many patient hands.",
        closing_image="From then on, the child listened first and climbed second, and the bell seemed to answer more kindly when questions were asked in daylight.",
        perches={"ladder", "winding_stairs"},
        tags={"bell", "tower"},
    ),
    "herb_house": Setting(
        id="herb_house",
        village_intro="Long ago, at the edge of a village garden, there stood a herb house with a door that always smelled of summer.",
        place_name="the drying room",
        outer_view="Blue jars lined the window, and bundles of leaves hung under the eaves.",
        hidden_thing="what scents and colors slept in the drying room",
        proper_role="herb-keeper",
        reveal_text="Inside hung mint, lavender, and thyme, and the blue jars glowed like little pieces of evening sky.",
        closing_image="After that day, the child kept curiosity bright but honest, and the herb house opened to questions more easily than it ever would to a costume.",
        perches={"ladder", "stool"},
        tags={"herbs", "garden"},
    ),
}

MASKS = {
    "miller_apron": Mask(
        id="miller_apron",
        role_name="miller's helper",
        phrase="a flour-dusted apron",
        borrowed_from="a peg near the grain sacks",
        costume_text="tied on a flour-dusted apron and tried to impersonate the miller's helper",
        belongs_to="mill",
        tags={"apron", "honesty"},
    ),
    "bell_coil": Mask(
        id="bell_coil",
        role_name="bell-ringer",
        phrase="an old rope coil",
        borrowed_from="a hook by the tower door",
        costume_text="slipped an old rope coil over one shoulder and tried to impersonate the bell-ringer",
        belongs_to="tower",
        tags={"rope", "honesty"},
    ),
    "herb_shawl": Mask(
        id="herb_shawl",
        role_name="herb-keeper",
        phrase="a green shawl",
        borrowed_from="a sunny bench by the herb house",
        costume_text="wrapped up in a green shawl and tried to impersonate the herb-keeper",
        belongs_to="herb_house",
        tags={"shawl", "honesty"},
    ),
    "crow_feathers": Mask(
        id="crow_feathers",
        role_name="crow",
        phrase="a handful of crow feathers",
        borrowed_from="the yard",
        costume_text="stuck on a few black feathers and tried to impersonate a crow",
        belongs_to="none",
        tags={"pretend"},
    ),
}

PERCHES = {
    "ladder": Perch(
        id="ladder",
        label="ladder",
        phrase="an old ladder",
        wobble_text="The ladder gave a thin wooden shiver under the small feet.",
        slip_text="One rung rolled under the child's shoe, and the whole ladder leaned with a dry clack.",
        height=2,
        wobble=1,
        tags={"ladder"},
    ),
    "barrel_stack": Perch(
        id="barrel_stack",
        label="barrel stack",
        phrase="a stack of flour barrels",
        wobble_text="The round barrels shifted under the child's weight like sleepy drums.",
        slip_text="A barrel turned half a handspan, and the child windmilled both arms to keep from tumbling.",
        height=3,
        wobble=2,
        tags={"barrels"},
    ),
    "winding_stairs": Perch(
        id="winding_stairs",
        label="winding stairs",
        phrase="the winding tower stairs",
        wobble_text="Dust skidded from the worn stone edge, and the child felt the steepness all at once.",
        slip_text="A foot slid on the dusty step, and the child lurched toward the open middle of the stair.",
        height=2,
        wobble=1,
        tags={"stairs"},
    ),
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="a three-legged stool",
        wobble_text="The three-legged stool rocked and clicked on the uneven floor.",
        slip_text="One leg slipped sideways, and the child pitched toward the herb bundles.",
        height=1,
        wobble=1,
        tags={"stool"},
    ),
    "stone_bench": Perch(
        id="stone_bench",
        label="stone bench",
        phrase="a low stone bench",
        wobble_text="The bench did not move at all.",
        slip_text="Nothing much happened.",
        height=0,
        wobble=0,
        tags={"bench"},
    ),
}

RESPONSES = {
    "steady": Response(
        id="steady",
        sense=3,
        power=2,
        text="caught hold of the {perch} and held it firm until the child could climb down slowly",
        fail="caught at the {perch}, but the child was already too high and off balance",
        qa_text="held the {perch} steady and helped the child climb down",
        tags={"help", "safety"},
    ),
    "catch": Response(
        id="catch",
        sense=3,
        power=3,
        text="spread a thick quilt below and caught the child against it before a hard fall could happen",
        fail="threw a quilt beneath the child, but the stumble had already gone too far",
        qa_text="caught the child with a thick quilt before a hard fall",
        tags={"help", "safety"},
    ),
    "guide_down": Response(
        id="guide_down",
        sense=2,
        power=1,
        text="stood close, gave calm step-by-step words, and guided the child down one careful foot at a time",
        fail="called out calm directions, but the child slipped before those words could help enough",
        qa_text="guided the child down with calm directions",
        tags={"help", "safety"},
    ),
    "scold": Response(
        id="scold",
        sense=1,
        power=0,
        text="only scolded from below",
        fail="only scolded from below, and the scolding did nothing to stop the slip",
        qa_text="scolded from below",
        tags={"warning"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tala", "Nia", "Sana", "Yara", "Pia", "Ayla"]
BOY_NAMES = ["Toma", "Ivo", "Milo", "Rian", "Luka", "Sami", "Niko", "Arin"]
TRAITS = ["heedful", "gentle", "patient", "careful", "restless", "bold", "eager", "quick"]
TOKENS = ["red ribbon", "smooth acorn", "little tin whistle", "blue bead", ""]
PETS = ["the cat", "the little goat", "the brown hen", ""]


def disguise_fits(mask: Mask, setting: Setting) -> bool:
    return mask.belongs_to == setting.id and mask.role_name == setting.proper_role


def perch_fits(setting: Setting, perch: Perch) -> bool:
    return perch.id in setting.perches and perch.height > 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id, setting in SETTINGS.items():
        for mask_id, mask in MASKS.items():
            for perch_id, perch in PERCHES.items():
                if disguise_fits(mask, setting) and perch_fits(setting, perch):
                    combos.append((setting_id, mask_id, perch_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_severity(perch: Perch, delay: int) -> int:
    return perch.wobble + perch.height + delay - 1


def is_contained(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= risk_severity(perch, delay)


def initial_caution(trait: str, trust: int) -> float:
    base = 5.0 if trait in RECEPTIVE_TRAITS else 3.0
    return base + (1.0 if trust >= 7 else 0.0)


def would_avert(trait: str, trust: int) -> bool:
    return initial_caution(trait, trust) + 1.0 > CURIOSITY_INIT


def predict_trouble(world: World, perch_id: str) -> dict:
    sim = world.copy()
    do_climb(sim, sim.get("child"), sim.get("perch"), narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "fear": sim.get("child").memes["fear"],
    }


def tale_opening(world: World, child: Entity, setting: Setting, token: str) -> None:
    world.say(setting.village_intro)
    if token:
        world.say(
            f"In that village lived {child.id}, a curious little {child.type} who kept {token} in "
            f"{child.pronoun('possessive')} pocket and a hundred questions in {child.pronoun('possessive')} head."
        )
    else:
        world.say(
            f"In that village lived {child.id}, a curious little {child.type} who carried a hundred questions in "
            f"{child.pronoun('possessive')} head."
        )
    world.say(
        f"Each day {child.pronoun()} passed {setting.place_name}, {child.pronoun()} glanced up. "
        f"{setting.outer_view}"
    )


def glimpse_secret(world: World, child: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Soon {child.pronoun('possessive')} heart was full of one wish: to learn {setting.hidden_thing}."
    )


def tempt(world: World, child: Entity, setting: Setting, mask: Mask) -> None:
    child.memes["scheming"] += 1
    world.say(
        f"One afternoon, when no one seemed to be looking, {child.pronoun()} saw {mask.phrase} hanging by "
        f"{mask.borrowed_from}. An idea as quick as a sparrow hopped into {child.pronoun('possessive')} mind."
    )
    world.say(
        f"{child.id} {mask.costume_text}. 'If I look the part, perhaps the door will not mind me,' "
        f"{child.pronoun()} whispered."
    )


def warn(world: World, elder: Entity, child: Entity, setting: Setting, perch: Perch) -> None:
    pred = predict_trouble(world, perch.id)
    child.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"But {child.id}'s {elder.label_word} had old eyes and missed little. "
        f'"Little one," {elder.pronoun()} said, "curiosity is a bright lantern, but it must not '
        f'be carried with borrowed faces. If you climb by {perch.phrase}, the place may turn dangerous before '
        f'you learn a thing."'
    )


def back_down(world: World, child: Entity, elder: Entity, mask: Mask) -> None:
    child.memes["relief"] += 1
    child.memes["honesty"] += 1
    child.memes["shame"] += 0.5
    world.say(
        f"{child.id} looked at the borrowed {mask.phrase} and then at {elder.pronoun('object')}. "
        f"The costume suddenly felt heavier than cloth."
    )
    world.say(
        f'"I did not need to impersonate anyone," {child.pronoun()} admitted. "I only needed to ask." '
        f"Then {child.pronoun()} hung the borrowed thing back where it belonged."
    )


def honest_reveal(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"{elder.label_word.capitalize()} smiled, for honest questions are easier to carry than secrets. "
        f"Together they opened the way to {setting.place_name}."
    )
    world.say(setting.reveal_text)
    pet = world.facts.get("pet", "")
    if pet:
        world.say(f"Even {pet} came nosing along after them, as if curiosity belonged to the whole yard.")
    world.say(
        f'"You may be curious," {elder.pronoun()} said, "but let your true name knock first."'
    )
    world.say(setting.closing_image)


def defy(world: World, child: Entity, perch: Perch) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the question in {child.id}'s chest was louder than caution. "
        f"{child.pronoun().capitalize()} set one foot on {perch.phrase} and began to climb."
    )


def do_climb(world: World, child: Entity, perch: Entity, narrate: bool = True) -> None:
    child.meters["height"] += 1
    perch.meters["wobbling"] += 1
    child.meters["off_balance"] += 1
    propagate(world, narrate=narrate)


def slip(world: World, child: Entity, perch_cfg: Perch) -> None:
    world.say(perch_cfg.wobble_text)
    world.say(perch_cfg.slip_text)
    child.meters["slipped"] += 1


def alarm(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'"{elder.label_word.capitalize()}!" cried {child.id}, and in that cry there was more truth than in the whole disguise.'
    )


def rescue(world: World, elder: Entity, child: Entity, perch_cfg: Perch, response: Response) -> None:
    child.meters["slipped"] = 0.0
    child.meters["off_balance"] = 0.0
    world.get("place").meters["danger"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    text = response.text.replace("{perch}", perch_cfg.label)
    world.say(
        f"{elder.label_word.capitalize()} moved quickly and {text}."
    )
    world.say(
        f"When both feet were safe on the ground again, {child.id} trembled like a leaf that has just escaped the wind."
    )


def lesson(world: World, elder: Entity, child: Entity, setting: Setting, mask: Mask) -> None:
    child.memes["honesty"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f'{elder.label_word.capitalize()} put a steady hand on {child.pronoun("possessive")} shoulder. '
        f'"A borrowed {mask.role_name} cannot carry borrowed wisdom," {elder.pronoun()} said. '
        f'"If you wish to know about {setting.place_name}, ask. Curiosity grows straighter in the open."'
    )


def small_reveal(world: World, elder: Entity, child: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then, because the lesson had landed softly instead of late, {elder.label_word} opened the way and showed "
        f"{child.pronoun('object')} what {child.pronoun()} had wanted to see all along."
    )
    world.say(setting.reveal_text)
    world.say(setting.closing_image)


def rescue_fail(world: World, elder: Entity, child: Entity, perch_cfg: Perch, response: Response) -> None:
    child.meters["hurt"] += 1
    child.meters["off_balance"] += 1
    world.get("place").meters["danger"] += 1
    body = response.fail.replace("{perch}", perch_cfg.label)
    world.say(f"{elder.label_word.capitalize()} {body}.")
    world.say(
        f"{child.id} fell in a tangle of limbs and borrowed cloth, not badly hurt, but sore enough to learn how hard the ground can answer foolish hurry."
    )


def sorrow(world: World, child: Entity, elder: Entity, pet: str) -> None:
    child.memes["shame"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{elder.label_word.capitalize()} lifted {child.pronoun('object')} gently and carried {child.pronoun('object')} to a bench in the shade."
    )
    if pet:
        world.say(f"{pet.capitalize()} sat nearby and watched with very round eyes.")
    world.say(
        f"For the rest of that day, {child.id} could only listen to village sounds from the ground, and each sound seemed to say, ask first."
    )


def grim_lesson(world: World, elder: Entity, child: Entity, setting: Setting) -> None:
    child.memes["wisdom"] += 1
    child.memes["honesty"] += 1
    world.say(
        f'"You are lucky," said {elder.label_word}, binding the scrape with cool cloth. '
        f'"Curiosity is a gift, but it turns thorny when it tries to sneak and impersonate instead of speak plainly."'
    )
    world.say(
        f"Many days later, when the scrape had faded, {child.id} returned and asked with {child.pronoun('possessive')} own voice. "
        f"Only then was {setting.place_name} opened."
    )
    world.say(setting.reveal_text)
    world.say(setting.closing_image)


def tell(
    setting: Setting,
    mask: Mask,
    perch_cfg: Perch,
    response: Response,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "heedful",
    delay: int = 0,
    trust: int = 6,
    token: str = "",
    pet: str = "",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            traits=[trait],
            role="child",
            attrs={"display_name": child_name, "trust": trust, "token": token},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            attrs={},
        )
    )
    place = world.add(
        Entity(
            id="place",
            type="place",
            label=setting.place_name,
            attrs={"setting": setting.id},
        )
    )
    perch = world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch_cfg.label,
            attrs={"height": perch_cfg.height, "wobble": perch_cfg.wobble},
        )
    )
    world.add(
        Entity(
            id="mask",
            type="mask",
            label=mask.role_name,
            attrs={"phrase": mask.phrase},
        )
    )

    child.memes["curiosity"] = CURIOSITY_INIT
    child.memes["trust"] = float(trust)
    child.memes["caution"] = initial_caution(trait, trust)
    world.facts["pet"] = pet

    tale_opening(world, child, setting, token)
    glimpse_secret(world, child, setting)

    world.para()
    tempt(world, child, setting, mask)
    warn(world, elder, child, setting, perch_cfg)

    averted = would_avert(trait, trust)

    if averted:
        back_down(world, child, elder, mask)
        world.para()
        honest_reveal(world, child, elder, setting)
        severity = 0
        contained = True
    else:
        defy(world, child, perch_cfg)

        world.para()
        do_climb(world, child, perch, narrate=False)
        slip(world, child, perch_cfg)
        alarm(world, child, elder)

        severity = risk_severity(perch_cfg, delay)
        contained = is_contained(response, perch_cfg, delay)

        world.para()
        if contained:
            rescue(world, elder, child, perch_cfg, response)
            lesson(world, elder, child, setting, mask)
            world.para()
            small_reveal(world, elder, child, setting)
        else:
            rescue_fail(world, elder, child, perch_cfg, response)
            sorrow(world, child, elder, pet)
            world.para()
            grim_lesson(world, elder, child, setting)

    outcome = "averted" if averted else ("contained" if contained else "hurt")
    world.facts.update(
        child=child,
        elder=elder,
        setting=setting,
        mask_cfg=mask,
        perch_cfg=perch_cfg,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        revealed=True,
        averted=averted,
        contained=contained,
        child_name=child_name,
        token=token,
    )
    return world


KNOWLEDGE = {
    "honesty": [
        (
            "What does it mean to impersonate someone?",
            "To impersonate someone means to pretend to be that person so others will mistake you for them. It can be unkind or unsafe when it is used to trick people instead of asking honestly."
        )
    ],
    "curiosity": [
        (
            "Is curiosity good or bad?",
            "Curiosity is good when it helps you ask questions and learn. It becomes unsafe when it pushes you to sneak, climb, or ignore a wise warning."
        )
    ],
    "ladder": [
        (
            "Why can a ladder be dangerous?",
            "A ladder is dangerous when it wobbles or when someone climbs without help. A small slip can turn into a hard fall very quickly."
        )
    ],
    "stairs": [
        (
            "Why should people be careful on steep stairs?",
            "Steep stairs need slow feet and a hand that can hold the rail or wall. Dust or hurry can make one step slide into a fall."
        )
    ],
    "stool": [
        (
            "Why can a three-legged stool tip?",
            "A three-legged stool can rock if the floor is uneven or if someone stands too high on it. When its balance shifts, the person on top can tumble."
        )
    ],
    "help": [
        (
            "What should you do if you feel yourself slipping from a high place?",
            "Call for a grown-up right away and stop trying to climb higher. Calm help is safer than trying to fix the danger alone."
        )
    ],
    "mill": [
        (
            "What is a mill?",
            "A mill is a place where grain is ground into flour. People bring grain there, and the mill turns it into powder for bread."
        )
    ],
    "bell": [
        (
            "What is a bell tower for?",
            "A bell tower holds a big bell high above the village. The bell can ring to tell time, call people together, or mark an important moment."
        )
    ],
    "herbs": [
        (
            "Why do people dry herbs?",
            "People dry herbs so they can keep their smell and flavor for longer. Dry leaves can be used later for cooking, tea, or medicine."
        )
    ],
}

KNOWLEDGE_ORDER = ["honesty", "curiosity", "ladder", "stairs", "stool", "help", "mill", "bell", "herbs"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    mask = f["mask_cfg"]
    outcome = f["outcome"]
    name = display_name(child)
    base = (
        f'Write a short folk tale for a 3-to-5-year-old about a curious child who tries to impersonate '
        f'the {mask.role_name} in order to learn a secret about {setting.place_name}. Include the word "impersonate".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle folk tale where {name} listens to a wise elder before climbing, asks honestly, and is shown the secret the right way.",
            f"Write a village tale where curiosity becomes wisdom because a child gives up a disguise and chooses a true question instead.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a folk tale where {name} climbs anyway, the {f['perch_cfg'].label} wobbles, and a calm elder rescues the child before a hard fall.",
            f"Write a cautionary but gentle village story where borrowed clothes cannot replace wisdom, and the secret is finally shared after the rescue.",
        ]
    return [
        base,
        f"Tell a folk tale where {name} ignores a warning, slips while climbing, and learns through a sore fall that honesty is safer than disguise.",
        f"Write a village cautionary tale where curiosity turns thorny when a child sneaks and tries to impersonate a keeper instead of asking plainly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    mask = f["mask_cfg"]
    perch = f["perch_cfg"]
    response = f["response"]
    name = display_name(child)
    ew = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a curious child named {name} and {name}'s {ew}. The child wanted to learn the secret of {setting.place_name}."
        ),
        (
            f"Why did {name} try to impersonate someone?",
            f"{name} was deeply curious about {setting.hidden_thing}. Instead of asking at first, {child.pronoun()} hoped a costume would help {child.pronoun('object')} slip into the place unnoticed."
        ),
        (
            f"What warning did {name}'s {ew} give?",
            f"{ew.capitalize()} warned that curiosity should not be carried with borrowed faces. {elder.pronoun().capitalize()} also warned that climbing by {perch.phrase} could turn dangerous very quickly."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"What did {name} do after hearing the warning?",
                f"{name} stopped, gave back the borrowed costume, and admitted that {child.pronoun()} only needed to ask. That honest choice changed the whole story before any climbing trouble began."
            ),
            (
                f"How did the child finally learn the secret of {setting.place_name}?",
                f"{ew.capitalize()} opened the way and showed {name} the place openly. The secret was shared because the child used a true question instead of a disguise."
            ),
        ])
    elif f["outcome"] == "contained":
        body = response.qa_text.replace("{perch}", perch.label)
        qa.extend([
            (
                f"What happened when {name} climbed?",
                f"The {perch.label} wobbled and the child began to slip. The danger came from climbing in a hurry while trying to impersonate the proper keeper."
            ),
            (
                f"How did {name}'s {ew} help?",
                f"{ew.capitalize()} {body}. That quick help turned a dangerous moment into a lesson instead of a hard injury."
            ),
            (
                "What did the child learn in the end?",
                f"The child learned that curiosity is good, but it must walk beside honesty. After the rescue, the secret was shown the right way, with open asking instead of pretending."
            ),
        ])
    else:
        qa.extend([
            (
                f"Was {name} badly hurt?",
                f"No, but {child.pronoun()} was sore and frightened after the fall. The scrape was enough to teach {child.pronoun('object')} that the ground answers foolish hurry very plainly."
            ),
            (
                "How did the ending prove that the child had changed?",
                f"Later, when the hurt had faded, the child came back and asked with {child.pronoun('possessive')} own voice. Only then was the place opened, showing that honesty had replaced sneaking."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"honesty", "curiosity", "help"} | set(f["setting"].tags) | set(f["perch_cfg"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="mill",
        mask="miller_apron",
        perch="ladder",
        response="steady",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        trait="heedful",
        delay=0,
        trust=8,
        token="red ribbon",
        pet="the cat",
    ),
    StoryParams(
        setting="tower",
        mask="bell_coil",
        perch="winding_stairs",
        response="guide_down",
        child_name="Toma",
        child_gender="boy",
        elder_type="grandfather",
        trait="bold",
        delay=0,
        trust=5,
        token="smooth acorn",
        pet="",
    ),
    StoryParams(
        setting="herb_house",
        mask="herb_shawl",
        perch="stool",
        response="catch",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        trait="restless",
        delay=0,
        trust=4,
        token="blue bead",
        pet="the brown hen",
    ),
    StoryParams(
        setting="mill",
        mask="miller_apron",
        perch="barrel_stack",
        response="guide_down",
        child_name="Milo",
        child_gender="boy",
        elder_type="grandfather",
        trait="eager",
        delay=1,
        trust=3,
        token="little tin whistle",
        pet="the little goat",
    ),
    StoryParams(
        setting="tower",
        mask="bell_coil",
        perch="ladder",
        response="catch",
        child_name="Ayla",
        child_gender="girl",
        elder_type="grandmother",
        trait="patient",
        delay=0,
        trust=7,
        token="",
        pet="",
    ),
]


def explain_rejection(setting: Setting, mask: Mask, perch: Perch) -> str:
    if not disguise_fits(mask, setting):
        return (
            f"(No story: {mask.phrase} would not honestly let a child impersonate the {setting.proper_role} of "
            f"{setting.place_name}. Pick the proper village role for that place.)"
        )
    if not perch_fits(setting, perch):
        return (
            f"(No story: {perch.phrase} is not a real way up into {setting.place_name}, so there is no believable "
            f"climbing danger or rescue. Pick a perch that belongs to that place.)"
        )
    return "(No story: this combination does not make a believable folk tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a calmer, more helpful rescue such as: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.trait, params.trust):
        return "averted"
    contained = is_contained(RESPONSES[params.response], PERCHES[params.perch], params.delay)
    return "contained" if contained else "hurt"


ASP_RULES = r"""
valid(S, M, P) :- setting(S), mask(M), perch(P), belongs_to(M, S), proper_role(S, R), role_name(M, R), allows(S, P), climb_height(P, H), H > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

receptive(T) :- trait(T), receptive_trait(T).
trust_bonus(1) :- trust(V), V >= 7.
trust_bonus(0) :- trust(V), V < 7.
init_caution(5 + B) :- trait(T), receptive(T), trust_bonus(B).
init_caution(3 + B) :- trait(T), not receptive(T), trust_bonus(B).
averted :- init_caution(C), curiosity_init(Q), C + 1 > Q.

severity(W + H + D - 1) :- chosen_perch(P), wobble(P, W), climb_height(P, H), delay(D).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
contained :- resp_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(hurt) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("proper_role", sid, setting.proper_role))
        for perch in sorted(setting.perches):
            lines.append(asp.fact("allows", sid, perch))
    for mid, mask in MASKS.items():
        lines.append(asp.fact("mask", mid))
        lines.append(asp.fact("role_name", mid, mask.role_name))
        lines.append(asp.fact("belongs_to", mid, mask.belongs_to))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("climb_height", pid, perch.height))
        lines.append(asp.fact("wobble", pid, perch.wobble))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(RECEPTIVE_TRAITS):
        lines.append(asp.fact("receptive_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curiosity, disguise, and the wiser path of asking honestly."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mask", choices=MASKS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to reach the child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.setting and args.mask and args.perch:
        setting = SETTINGS[args.setting]
        mask = MASKS[args.mask]
        perch = PERCHES[args.perch]
        if not (disguise_fits(mask, setting) and perch_fits(setting, perch)):
            raise StoryError(explain_rejection(setting, mask, perch))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mask is None or c[1] == args.mask)
        and (args.perch is None or c[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mask_id, perch_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trust = rng.randint(3, 9)
    token = rng.choice(TOKENS)
    pet = rng.choice(PETS)
    return StoryParams(
        setting=setting_id,
        mask=mask_id,
        perch=perch_id,
        response=response,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
        trait=trait,
        delay=delay,
        trust=trust,
        token=token,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mask not in MASKS:
        raise StoryError(f"(Unknown mask: {params.mask})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    mask = MASKS[params.mask]
    perch = PERCHES[params.perch]
    response = RESPONSES[params.response]

    if not disguise_fits(mask, setting) or not perch_fits(setting, perch):
        raise StoryError(explain_rejection(setting, mask, perch))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        mask=mask,
        perch_cfg=perch,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        delay=params.delay,
        trust=params.trust,
        token=params.token,
        pet=params.pet,
    )

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story is empty.)")
        _ = sample.to_json()
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, mask, perch) combos:\n")
        for setting, mask, perch in combos:
            print(f"  {setting:10} {mask:14} {perch}")
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
                f"### {p.child_name}: {p.setting} / {p.mask} / {p.perch} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
