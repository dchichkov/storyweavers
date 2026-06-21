#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py
==============================================================================

A standalone story world for a child-sized mystery: two young detectives guard a
special object, hear a strange sound in a shadowy place, study the clues, and
choose a rescue plan together. Some plans work; some are too weak or too late,
so the story can end sadly even though the children truly cooperate.

Seed features carried into the world:
- required words: "option", "dismay", "elect"
- features: Bad Ending, Teamwork
- style: Mystery

Run it
------
    python storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py
    python storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py --cause leak --target clue_book
    python storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py --response wait_and_watch
    python storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/option_dismay_elect_bad_ending_teamwork_mystery.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    corner: str
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
class Cause:
    id: str
    sound: str
    clue: str
    reveal: str
    severity: int
    threatens: set[str] = field(default_factory=set)
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
class Target:
    id: str
    label: str
    phrase: str
    damage_word: str
    fragility: int
    threatened_by: set[str] = field(default_factory=set)
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
    works_on: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    universal: bool = False
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"detective_a", "detective_b"}]

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


def _r_damage_dismay(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["damaged"] < THRESHOLD:
        return []
    sig = ("dismay", "target")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["dismay"] += 1
    return ["__damage__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_dismay", tag="emotional", apply=_r_damage_dismay),
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
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(cause: Cause, target: Target) -> bool:
    return target.id in cause.threatens and cause.id in target.threatened_by


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_applicable(response: Response, cause: Cause) -> bool:
    return response.universal or cause.id in response.works_on


def trouble_severity(cause: Cause, target: Target, delay: int) -> int:
    return cause.severity + target.fragility + delay


def is_contained(response: Response, cause: Cause, target: Target, delay: int) -> bool:
    if not response_applicable(response, cause):
        return False
    return response.power >= trouble_severity(cause, target, delay)


def predict_outcome(world: World, cause: Cause, target: Target, response: Response, delay: int) -> dict:
    sim = world.copy()
    contained = is_contained(response, cause, target, delay)
    if not contained:
        sim.get("target").meters["damaged"] += 1
        propagate(sim, narrate=False)
    return {
        "contained": contained,
        "damage": sim.get("target").meters["damaged"],
    }


def introduce_team(world: World, a: Entity, b: Entity, setting: Setting, target: Target) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} met in {setting.place}. "
        f"They called themselves the Lantern Knot Detectives, and tonight they were guarding {target.phrase}."
    )
    world.say(setting.opening)


def first_clue(world: World, a: Entity, b: Entity, cause: Cause, setting: Setting) -> None:
    world.say(
        f"Then a strange sound came from {setting.corner}: {cause.sound}. "
        f"{b.id} squeezed {a.id}'s sleeve, and the two detectives listened without speaking."
    )
    world.say(
        f"Together they followed the sound and found {cause.clue}. "
        f"The mystery suddenly felt real."
    )


def debate(world: World, a: Entity, b: Entity, cause: Cause, target: Target, response: Response, delay: int) -> None:
    pred = predict_outcome(world, cause, target, response, delay)
    world.facts["predicted_contained"] = pred["contained"]
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f'"We have more than one option," {a.id} whispered. '
        f'"But we should elect one before {target.label} gets hurt."'
    )
    if pred["contained"]:
        world.say(
            f'{b.id} nodded. "Then let\'s elect the careful plan and do it together."'
        )
    else:
        world.say(
            f'{b.id} frowned. "I hope this is enough," {b.pronoun()} said, though the shadows made that hope feel small.'
        )


def teamwork_action(world: World, a: Entity, b: Entity, response: Response, cause: Cause) -> None:
    for kid in (a, b):
        kid.memes["teamwork"] += 1
        kid.memes["resolve"] += 1
    if response.id == "tarp_cover":
        world.say(
            f"{a.id} held the lantern low while {b.id} spread the tarp, and then they switched places so each pair of hands could help."
        )
    elif response.id == "latch_window":
        world.say(
            f"{a.id} pushed the rattling frame while {b.id} snapped the latch shut, both of them leaning with all their small strength."
        )
    elif response.id == "tin_box":
        world.say(
            f"{a.id} lifted the tin lid while {b.id} gathered the precious things inside, and then they slid the box under the bench together."
        )
    elif response.id == "call_caretaker":
        world.say(
            f"{a.id} stayed by the mystery corner and kept watch while {b.id} ran for help, and then they returned side by side with a grown-up."
        )
    else:
        world.say(
            f"They stood shoulder to shoulder and tried their chosen plan together."
        )
    world.say(response.text.replace("{reveal}", cause.reveal))


def damage_target(world: World, target_ent: Entity, target: Target) -> None:
    target_ent.meters["damaged"] += 1
    target_ent.meters["ruined"] += 1
    propagate(world, narrate=False)
    world.say(
        f"To their dismay, {target.phrase} was {target.damage_word} before they could save it."
    )


def solve_mystery(world: World, a: Entity, b: Entity, cause: Cause, target: Target, adult: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"The mystery was solved at last: {cause.reveal}. "
        f"{adult.label_word.capitalize()} smiled when the children explained every clue."
    )
    world.say(
        f"In the bright hush that followed, {target.phrase} stayed safe, and {world.setting.ending_image}."
    )


def sad_ending(world: World, a: Entity, b: Entity, cause: Cause, target: Target, adult: Entity, response: Response) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"A moment later, {cause.reveal}, and the children knew their chosen plan had been the wrong one."
    )
    world.say(
        f"{adult.label_word.capitalize()} gathered them close and said, "
        f'"You worked as a team, and that was good. But when a mystery can ruin something precious, it is wiser to choose help quickly."'
    )
    world.say(
        f"That night ended sadly. {world.setting.ending_image}, but now the table where {target.phrase} should have shone was empty."
    )


def tell(
    setting: Setting,
    cause: Cause,
    target: Target,
    response: Response,
    *,
    detective_a: str = "Mira",
    detective_a_gender: str = "girl",
    detective_b: str = "Owen",
    detective_b_gender: str = "boy",
    adult_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=detective_a,
        kind="character",
        type=detective_a_gender,
        role="detective_a",
        attrs={},
    ))
    b = world.add(Entity(
        id=detective_b,
        kind="character",
        type=detective_b_gender,
        role="detective_b",
        attrs={},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
        attrs={},
    ))
    place = world.add(Entity(id="place", type="place", label=setting.place, attrs={}))
    target_ent = world.add(Entity(id="target", type="target", label=target.label, attrs={}))

    place.meters["mystery"] = 1.0
    target_ent.meters["damaged"] = 0.0
    target_ent.meters["ruined"] = 0.0
    world.facts["delay"] = delay

    introduce_team(world, a, b, setting, target)
    world.para()
    first_clue(world, a, b, cause, setting)
    debate(world, a, b, cause, target, response, delay)
    world.para()
    teamwork_action(world, a, b, response, cause)

    contained = is_contained(response, cause, target, delay)
    if contained:
        world.para()
        solve_mystery(world, a, b, cause, target, adult)
        outcome = "saved"
    else:
        damage_target(world, target_ent, target)
        world.para()
        sad_ending(world, a, b, cause, target, adult, response)
        outcome = "ruined"

    world.facts.update(
        detective_a=a,
        detective_b=b,
        adult=adult,
        place=place,
        cause=cause,
        target_cfg=target,
        target=target_ent,
        response=response,
        contained=contained,
        outcome=outcome,
        damage=target_ent.meters["damaged"],
        teamwork=a.memes["teamwork"] + b.memes["teamwork"],
    )
    return world


SETTINGS = {
    "greenhouse": Setting(
        id="greenhouse",
        place="the old greenhouse behind the school",
        opening="Moonlight made pale squares on the glass, and every pot cast a crooked shadow.",
        corner="the far potting bench",
        ending_image="silver drops still clung to the glass roof",
        affords={"leak", "wind", "mouse"},
        tags={"greenhouse", "mystery"},
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic above the town hall",
        opening="The rafters were dark as ship ribs, and one small bulb hummed over the trunks.",
        corner="the stack of old trunks",
        ending_image="the attic window showed one thin piece of moon",
        affords={"leak", "wind", "mouse"},
        tags={"attic", "mystery"},
    ),
    "boathouse": Setting(
        id="boathouse",
        place="the creaky boathouse by the pond",
        opening="Boards groaned under their shoes, and lantern-light wobbled over ropes and oars.",
        corner="the back shelf by the oars",
        ending_image="the pond outside lay black and still",
        affords={"leak", "wind", "mouse"},
        tags={"boathouse", "mystery"},
    ),
}

CAUSES = {
    "leak": Cause(
        id="leak",
        sound="tap...tap...tap",
        clue="a dark wet patch spreading wider and wider",
        reveal="rainwater was slipping through a cracked roof board",
        severity=1,
        threatens={"clue_book", "feather_mask", "seed_box"},
        tags={"leak", "water"},
    ),
    "wind": Cause(
        id="wind",
        sound="rattle...clack...rattle",
        clue="a window shaking and a cold draft sweeping the shelf",
        reveal="the night wind was sneaking through an unlatched window",
        severity=0,
        threatens={"clue_book", "feather_mask"},
        tags={"wind", "draft"},
    ),
    "mouse": Cause(
        id="mouse",
        sound="scratch-scratch-scratch",
        clue="tiny crumbs and a twitching shadow behind a crate",
        reveal="a hungry mouse had found the hiding place first",
        severity=1,
        threatens={"seed_box", "clue_book"},
        tags={"mouse", "nibble"},
    ),
}

TARGETS = {
    "clue_book": Target(
        id="clue_book",
        label="clue book",
        phrase="their hand-painted clue book for the school mystery fair",
        damage_word="blotched and bent",
        fragility=1,
        threatened_by={"leak", "wind", "mouse"},
        tags={"paper", "book"},
    ),
    "feather_mask": Target(
        id="feather_mask",
        label="feather mask",
        phrase="the moon-feather mask for the play",
        damage_word="sagging and misshapen",
        fragility=1,
        threatened_by={"leak", "wind"},
        tags={"mask", "craft"},
    ),
    "seed_box": Target(
        id="seed_box",
        label="seed box",
        phrase="the little cedar seed box for the spring fair",
        damage_word="spilled and spoiled",
        fragility=1,
        threatened_by={"leak", "mouse"},
        tags={"seeds", "box"},
    ),
}

RESPONSES = {
    "tarp_cover": Response(
        id="tarp_cover",
        sense=2,
        power=2,
        works_on={"leak", "wind"},
        text="They flung a clean tarp over the shelf and tucked the edges tight while they listened for the trouble to change. {reveal}.",
        fail="They spread a tarp, but the trouble slipped around it and reached the prize anyway.",
        qa_text="covered the shelf with a tarp to shield the special object",
        universal=False,
        tags={"tarp", "cover"},
    ),
    "latch_window": Response(
        id="latch_window",
        sense=2,
        power=2,
        works_on={"wind"},
        text="They wrestled the window shut and clicked the latch into place. {reveal}.",
        fail="They fought with the window, but that did not stop the real trouble at all.",
        qa_text="shut the rattling window and latched it",
        universal=False,
        tags={"window", "latch"},
    ),
    "tin_box": Response(
        id="tin_box",
        sense=2,
        power=2,
        works_on={"mouse"},
        text="They tucked the precious thing into a tall tin and slid it out of reach. {reveal}.",
        fail="They hid the prize in a tin, but the real trouble was not the kind a tin could stop.",
        qa_text="moved the object into a tall tin so the mouse could not reach it",
        universal=False,
        tags={"tin", "protect"},
    ),
    "call_caretaker": Response(
        id="call_caretaker",
        sense=3,
        power=4,
        works_on=set(),
        text="They called the caretaker at once, and quick grown-up hands fixed the trouble before it could grow. {reveal}.",
        fail="They called for help, but by the time help came the damage had already been done.",
        qa_text="called the caretaker right away for quick help",
        universal=True,
        tags={"adult_help", "caretaker"},
    ),
    "wait_and_watch": Response(
        id="wait_and_watch",
        sense=1,
        power=0,
        works_on={"leak", "wind", "mouse"},
        text="They crouched and watched, hoping the trouble would explain itself. {reveal}.",
        fail="They waited and watched, and the mystery kept working while they lost time.",
        qa_text="waited and watched instead of acting",
        universal=False,
        tags={"waiting"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "June", "Tess", "Ivy", "Ada", "Lucy"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Jude", "Eli", "Theo", "Sam", "Ben"]

KNOWLEDGE = {
    "leak": [(
        "What is a leak?",
        "A leak is water getting through a place where it should not come in. Even a small leak can spoil paper or seeds if nobody stops it."
    )],
    "wind": [(
        "Why can wind be a problem indoors?",
        "Wind can blow light things around, tip them over, or flap them against hard edges. That is why rattling windows should be shut."
    )],
    "mouse": [(
        "Why might a mouse spoil stored things?",
        "A mouse looks for food and nesting bits, so it may nibble seeds, paper, or cloth. Small teeth can make a big mess."
    )],
    "tarp": [(
        "What does a tarp do?",
        "A tarp is a strong cover that keeps water and dirt off things. It can be useful when you need to shield something quickly."
    )],
    "window": [(
        "Why does latching a window help?",
        "A latch holds the window closed so wind cannot push it open again. That can stop drafts and rattling."
    )],
    "tin": [(
        "Why is a tin box good for protecting small things?",
        "A tin box is hard and closed, so little animals cannot easily chew through it. It also keeps loose things together."
    )],
    "adult_help": [(
        "Why is it smart to call a grown-up for a bigger problem?",
        "A grown-up may have the tools, reach, or strength to fix the trouble quickly. Getting help fast can save the important thing."
    )],
    "paper": [(
        "Why does paper get ruined by water?",
        "Paper soaks up water and turns soft and wrinkly. Ink can blur too, so the writing may be hard to read."
    )],
    "seeds": [(
        "Why should seeds be kept dry and safe?",
        "Seeds can rot, spill, or get eaten if they are left unprotected. Keeping them dry helps them stay ready for planting."
    )],
    "mask": [(
        "Why can a costume mask be delicate?",
        "A costume mask may bend, sag, or tear if it gets wet or blown about. Decorations like feathers and paint can be damaged easily."
    )],
}
KNOWLEDGE_ORDER = ["leak", "wind", "mouse", "tarp", "window", "tin", "adult_help", "paper", "seeds", "mask"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for cause_id in sorted(setting.affords):
            cause = CAUSES[cause_id]
            for target_id, target in TARGETS.items():
                if hazard_at_risk(cause, target):
                    combos.append((setting_id, cause_id, target_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    cause: str
    target: str
    response: str
    detective_a: str
    detective_a_gender: str
    detective_b: str
    detective_b_gender: str
    adult: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["detective_a"]
    b = f["detective_b"]
    cause = f["cause"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short mystery story for a 3-to-5-year-old where two child detectives hear {cause.sound} in the dark and must protect {target.phrase}.'
    )
    if outcome == "ruined":
        return [
            base,
            f'Include the words "option", "dismay", and "elect", and let the children work as a team but choose a plan that ends sadly.',
            f"Tell a gentle bad-ending mystery where {a.id} and {b.id} cooperate bravely, yet the wrong choice still lets the special object be ruined.",
        ]
    return [
        base,
        f'Include the words "option", "dismay", and "elect", and let the children solve the mystery by choosing wisely together.',
        f"Tell a teamwork mystery where {a.id} and {b.id} study the clue, pick the best plan, and save the special object in time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["detective_a"]
    b = f["detective_b"]
    cause = f["cause"]
    target = f["target_cfg"]
    response = f["response"]
    adult = f["adult"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two child detectives, {a.id} and {b.id}, who were guarding {target.phrase}. They worked together in a shadowy place and tried to solve a mystery before it could turn into damage."
        ),
        (
            "What was the mystery clue?",
            f"The clue was {cause.clue}, along with the sound {cause.sound}. Those details helped the children figure out what kind of trouble was hiding in the dark."
        ),
        (
            "Why did the children talk about an option and elect a plan?",
            f"They knew they had to choose what to do before the trouble reached {target.label}. The mystery gave them more than one option, so they had to elect one quickly and act as a team."
        ),
    ]
    if outcome == "saved":
        qa.append((
            "How did they solve the mystery?",
            f"They used teamwork and {response.qa_text}. That worked because the real problem was that {cause.reveal}, and their plan matched the danger."
        ))
        qa.append((
            "Why did the ending feel safe?",
            f"The special object stayed unharmed, and the children understood the clue correctly. Their teamwork led to a careful choice, so the mystery ended with relief instead of loss."
        ))
    else:
        qa.append((
            "Why did the story end with dismay?",
            f"It ended with dismay because {target.phrase} was {target.damage_word}. The children cooperated, but their elected plan could not stop the real trouble in time."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that teamwork is important, but the right kind of help matters too. In a bigger mystery, choosing a wiser option sooner can save the precious thing."
        ))
    qa.append((
        "Was there teamwork even in the sad part?",
        f"Yes. The children stayed together, shared clues, and tried the plan side by side. The sad ending came from the choice being too weak or too late, not from them refusing to help each other."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cause"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="greenhouse",
        cause="leak",
        target="clue_book",
        response="tarp_cover",
        detective_a="Mira",
        detective_a_gender="girl",
        detective_b="Owen",
        detective_b_gender="boy",
        adult="mother",
        delay=0,
    ),
    StoryParams(
        setting="attic",
        cause="mouse",
        target="seed_box",
        response="tin_box",
        detective_a="Nora",
        detective_a_gender="girl",
        detective_b="Finn",
        detective_b_gender="boy",
        adult="father",
        delay=0,
    ),
    StoryParams(
        setting="boathouse",
        cause="wind",
        target="feather_mask",
        response="latch_window",
        detective_a="Ada",
        detective_a_gender="girl",
        detective_b="Theo",
        detective_b_gender="boy",
        adult="mother",
        delay=1,
    ),
    StoryParams(
        setting="greenhouse",
        cause="leak",
        target="seed_box",
        response="tin_box",
        detective_a="June",
        detective_a_gender="girl",
        detective_b="Milo",
        detective_b_gender="boy",
        adult="father",
        delay=0,
    ),
    StoryParams(
        setting="attic",
        cause="mouse",
        target="clue_book",
        response="call_caretaker",
        detective_a="Lucy",
        detective_a_gender="girl",
        detective_b="Ben",
        detective_b_gender="boy",
        adult="mother",
        delay=1,
    ),
]


def explain_rejection(cause: Cause, target: Target) -> str:
    return (
        f"(No story: {cause.id} does not reasonably threaten {target.phrase}. "
        f"The mystery needs a real risk to the guarded object.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these safer choices: {better}.)"
    )


def explain_inapplicable(response: Response, cause: Cause) -> str:
    return (
        f"(No story: the response '{response.id}' does not fit the mystery cause '{cause.id}'. "
        f"A plan must actually match the trouble.)"
    )


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]
    return "saved" if is_contained(response, cause, target, params.delay) else "ruined"


ASP_RULES = r"""
hazard(C, T) :- threatens(C, T), threatened_by(T, C).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

applicable(R, C) :- works_on(R, C).
applicable(R, C) :- universal(R), cause(C).

valid(S, C, T) :- setting(S), affords(S, C), hazard(C, T).

severity(V) :- chosen_cause(C), chosen_target(T), cause_severity(C, CS),
               fragility(T, F), delay(D), V = CS + F + D.
usable_response :- chosen_response(R), chosen_cause(C), applicable(R, C).
contained :- chosen_response(R), usable_response, power(R, P), severity(V), P >= V.

outcome(saved) :- contained.
outcome(ruined) :- not contained.

#show valid/3.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cause_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cause_id))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_severity", cid, cause.severity))
        for target_id in sorted(cause.threatens):
            lines.append(asp.fact("threatens", cid, target_id))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("fragility", tid, target.fragility))
        for cause_id in sorted(target.threatened_by):
            lines.append(asp.fact("threatened_by", tid, cause_id))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        if response.universal:
            lines.append(asp.fact("universal", rid))
        for cause_id in sorted(response.works_on):
            lines.append(asp.fact("works_on", rid, cause_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
        print("  python:", sorted(py_sensible))
        print("  asp   :", sorted(asp_sens))

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: two child detectives choose a rescue plan together. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.target:
        cause = CAUSES[args.cause]
        target = TARGETS[args.target]
        if not hazard_at_risk(cause, target):
            raise StoryError(explain_rejection(cause, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.response and args.cause:
        response = RESPONSES[args.response]
        cause = CAUSES[args.cause]
        if not response_applicable(response, cause):
            raise StoryError(explain_inapplicable(response, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cause_id, target_id = rng.choice(sorted(combos))
    cause = CAUSES[cause_id]
    response_choices = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN
        and (args.response is None or rid == args.response)
        and response_applicable(response, cause)
    ]
    if not response_choices:
        raise StoryError("(No sensible response matches the given options.)")

    detective_a, ga = _pick_name(rng)
    detective_b, gb = _pick_name(rng, avoid=detective_a)
    adult = args.adult or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        cause=cause_id,
        target=target_id,
        response=rng.choice(sorted(response_choices)),
        detective_a=detective_a,
        detective_a_gender=ga,
        detective_b=detective_b,
        detective_b_gender=gb,
        adult=adult,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]

    if not hazard_at_risk(cause, target):
        raise StoryError(explain_rejection(cause, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_applicable(response, cause):
        raise StoryError(explain_inapplicable(response, cause))

    world = tell(
        setting=setting,
        cause=cause,
        target=target,
        response=response,
        detective_a=params.detective_a,
        detective_a_gender=params.detective_a_gender,
        detective_b=params.detective_b,
        detective_b_gender=params.detective_b_gender,
        adult_type=params.adult,
        delay=params.delay,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (setting, cause, target) combos:\n")
        for setting_id, cause_id, target_id in combos:
            print(f"  {setting_id:10} {cause_id:8} {target_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.detective_a} & {p.detective_b}: {p.cause} in {p.setting} "
                f"({p.target}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
