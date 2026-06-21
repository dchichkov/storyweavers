#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py
==========================================================================================

A standalone story world for a gentle bedtime cautionary tale about a child who
misunderstands what a house shaft is for.

Premise
-------
In an old tall home, inn, or lighthouse cottage, there is a narrow service
shaft used for laundry or a small dumbwaiter basket. A child hears about it and
misunderstands its purpose, thinking it is a clever shortcut for sending
something important downstairs before bed. The mistake creates a risky moment at
the open hatch. A calm grown-up explains the misunderstanding, uses a sensible
method instead, and the child learns that when something in a house is strange
or grown-up, it is better to ask than guess.

Run it
------
    python storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/shaft_cautionary_moral_value_misunderstanding_bedtime_story.py --verify
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
CAREFUL_TRAITS = {"careful", "thoughtful", "patient", "sensible"}
BOLD_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    narrow: bool = False
    soft: bool = False
    breakable: bool = False
    can_ride_shaft: bool = False
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
            "mother": "mom",
            "father": "dad",
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
    bedtime_glow: str
    shaft_kind: str
    shaft_name: str
    shaft_use: str
    sound: str
    down_to: str
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
class ShaftUse:
    id: str
    noun: str
    label: str
    mechanism: str
    safe_for: set[str] = field(default_factory=set)
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
    desire: str
    comfort: str
    narrow: bool = False
    soft: bool = False
    breakable: bool = False
    can_ride_shaft: bool = False
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
class Misunderstanding:
    id: str
    thought: str
    reason: str
    action: str
    risky_reach: str
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
class Remedy:
    id: str
    sense: int
    recovers_fallen: bool
    text: str
    answer_text: str
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


def _r_open_edge(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shaft = world.get("shaft")
    if shaft.meters["open"] < THRESHOLD:
        return out
    sig = ("open_edge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["near_edge"] += 1
    child.memes["wonder"] += 1
    out.append("__edge__")
    return out


def _r_reach_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["reaching"] < THRESHOLD or child.meters["near_edge"] < THRESHOLD:
        return out
    sig = ("reach_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["risk"] += 1
    child.memes["wobble"] += 1
    out.append("__risk__")
    return out


def _r_fall_clatter(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("prize")
    child = world.get("child")
    if item.meters["fallen"] < THRESHOLD:
        return out
    sig = ("fall_clatter", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["lost"] += 1
    child.memes["fear"] += 1
    child.memes["regret"] += 1
    out.append("__clatter__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="open_edge", tag="physical", apply=_r_open_edge),
    Rule(name="reach_risk", tag="physical", apply=_r_reach_risk),
    Rule(name="fall_clatter", tag="physical", apply=_r_fall_clatter),
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


def shaft_reasonable(shaft_use: ShaftUse, prize: Prize) -> bool:
    return prize.can_ride_shaft and prize.id in shaft_use.safe_for


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def cautious_weight(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_ask_first(relation: str, child_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > child_age
    return older and (cautious_weight(trait) + 1.0) > BOLD_INIT


def predict_shaft_trouble(world: World, misunderstanding: Misunderstanding, prize_id: str) -> dict:
    sim = world.copy()
    prize = sim.get(prize_id)
    open_hatch(sim, narrate=False)
    start_reaching(sim, misunderstanding, prize, narrate=False)
    drop_happens = not shaft_reasonable(sim.facts["shaft_use"], sim.facts["prize_cfg"])
    if drop_happens:
        drop_item(sim, prize, narrate=False)
    return {
        "risk": sim.get("child").meters["risk"],
        "fallen": sim.get("prize").meters["fallen"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"In {world.setting.place}, bedtime came softly. {world.setting.bedtime_glow} "
        f"{child.id} carried {prize.phrase} from room to room as if the evening would feel more settled with it close by."
    )
    world.say(
        f"{helper.id}, {child.pronoun('possessive')} {helper.label_word}, was finishing the last small jobs of the day while the house made its old sleepy sounds."
    )


def hear_about_shaft(world: World, child: Entity, helper: Entity, shaft_use: ShaftUse) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"From the hall came {world.setting.sound}. When {child.id} asked about it, {helper.id} explained that the house had {shaft_use.label}."
    )
    world.say(
        f'"It is for {world.setting.shaft_use}," {helper.id} said. "It goes down to {world.setting.down_to}, and it is not a place for children to lean or peek into."'
    )


def wish(world: World, child: Entity, prize: Entity) -> None:
    child.memes["want"] += 1
    world.say(
        f"But {child.id} had a little bedtime wish: {prize.desire}. The wish was small, yet it felt large in the quiet house."
    )


def misunderstand(world: World, child: Entity, misunderstanding: Misunderstanding, shaft_use: ShaftUse, prize: Entity) -> None:
    child.memes["mistaken"] += 1
    world.say(
        f"{child.id} thought about the {world.setting.shaft_name} and misunderstood. {misunderstanding.thought}"
    )
    world.say(
        f"{misunderstanding.reason} To {child.id}, that made the old {shaft_use.noun} sound like a clever bedtime shortcut for {prize.label}."
    )


def warn(world: World, cautioner: Entity, child: Entity, misunderstanding: Misunderstanding) -> None:
    pred = predict_shaft_trouble(world, misunderstanding, "prize")
    world.facts["predicted_risk"] = pred["risk"]
    cautioner.memes["caution"] += 1
    extra = ""
    if pred["fallen"]:
        extra = " and something could tumble all the way down"
    world.say(
        f'{cautioner.id} frowned in the thoughtful way children do when they picture a mistake before it happens. '
        f'"Please do not use the shaft that way," {cautioner.pronoun()} said. "If you open it and reach in, you could wobble{extra}."'
    )


def back_down(world: World, child: Entity, helper: Entity, prize: Entity, remedy: Remedy) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} looked again, this time with slower eyes, and understood that the idea had only sounded clever because {child.pronoun()} had guessed instead of asking."
    )
    world.say(
        f'"I thought the shaft was for sending anything down," {child.pronoun()} whispered. {helper.id} squeezed {child.pronoun("possessive")} shoulder kindly.'
    )
    world.say(remedy.text.replace("{prize}", prize.label))
    child.memes["lesson"] += 1


def open_hatch(world: World, narrate: bool = True) -> None:
    shaft = world.get("shaft")
    shaft.meters["open"] += 1
    propagate(world, narrate=narrate)


def start_reaching(world: World, misunderstanding: Misunderstanding, prize: Entity, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["reaching"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{misunderstanding.action} {misunderstanding.risky_reach} with {prize.label} held carefully at first, and then not quite carefully enough."
        )


def drop_item(world: World, prize: Entity, narrate: bool = True) -> None:
    prize.meters["fallen"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{prize.phrase[0].upper()}{prize.phrase[1:]} slipped from small fingers and vanished down the shaft with a hollow clatter."
        )


def calm_rescue(world: World, helper: Entity, remedy: Remedy, prize: Entity) -> None:
    prize.meters["lost"] = 0.0
    prize.meters["fallen"] = 0.0
    child = world.get("child")
    child.meters["risk"] = 0.0
    child.meters["reaching"] = 0.0
    child.memes["fear"] = 0.0
    world.say(
        f"{helper.id} came at once, shut the hatch, and stepped between {child.id} and the opening before anything else could happen."
    )
    world.say(remedy.text.replace("{prize}", prize.label))
    child.memes["relief"] += 1
    child.memes["lesson"] += 1


def lesson(world: World, helper: Entity, child: Entity) -> None:
    child.memes["love"] += 1
    world.say(
        f"When everything was safe again, {helper.id} sat beside {child.id} on the stair and spoke in a quiet bedtime voice."
    )
    world.say(
        f'"Old house things can be useful and still not be for play," {helper.pronoun()} said. "If you are not sure what something is for, ask first. Guessing near a shaft is not brave. Asking is brave."'
    )


def bedtime_end(world: World, child: Entity, prize: Entity) -> None:
    child.memes["peace"] += 1
    world.say(
        f"Soon {child.id} had {prize.label} safe again and tucked close. The house still hummed with its old sounds, but now they felt like ordinary sounds instead of secret invitations."
    )
    world.say(
        f"By the time the blanket was pulled up and the lamp was dimmed, {child.id} knew exactly what had changed: not the house, but the way {child.pronoun()} listened to it."
    )


def tell(
    setting: Setting,
    shaft_use: ShaftUse,
    prize_cfg: Prize,
    misunderstanding: Misunderstanding,
    remedy: Remedy,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    cautioner_name: str = "Ben",
    cautioner_gender: str = "boy",
    helper_type: str = "grandmother",
    trait: str = "careful",
    relation: str = "siblings",
    child_age: int = 5,
    cautioner_age: int = 7,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        age=child_age,
        traits=["curious"],
        attrs={"relation": relation},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    shaft = world.add(Entity(
        id="shaft",
        type="shaft",
        label=setting.shaft_name,
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.id,
        label=prize_cfg.label,
        attrs={"comfort": prize_cfg.comfort},
        narrow=prize_cfg.narrow,
        soft=prize_cfg.soft,
        breakable=prize_cfg.breakable,
        can_ride_shaft=prize_cfg.can_ride_shaft,
    ))

    child.memes["boldness"] = BOLD_INIT
    cautioner.memes["caution"] = cautious_weight(trait)

    world.facts.update(
        child=child,
        cautioner=cautioner,
        helper=helper,
        shaft_use=shaft_use,
        setting=setting,
        prize_cfg=prize_cfg,
        misunderstanding=misunderstanding,
        remedy=remedy,
    )

    introduce(world, child, helper, prize)
    wish(world, child, prize)
    world.para()
    hear_about_shaft(world, child, helper, shaft_use)
    misunderstand(world, child, misunderstanding, shaft_use, prize)
    warn(world, cautioner, child, misunderstanding)

    averted = would_ask_first(relation, child_age, cautioner_age, trait)

    if averted:
        world.para()
        back_down(world, child, helper, prize, remedy)
        lesson(world, helper, child)
        world.para()
        bedtime_end(world, child, prize)
        outcome = "averted"
        fell = False
    else:
        world.para()
        open_hatch(world)
        start_reaching(world, misunderstanding, prize)
        fell = not shaft_reasonable(shaft_use, prize_cfg)
        if fell:
            drop_item(world, prize)
        world.para()
        calm_rescue(world, helper, remedy, prize)
        lesson(world, helper, child)
        world.para()
        bedtime_end(world, child, prize)
        outcome = "rescued"

    world.facts.update(
        outcome=outcome,
        averted=averted,
        fell=fell,
        predicted_risk=world.facts.get("predicted_risk", 0.0),
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lighthouse": Setting(
        id="lighthouse",
        place="the old lighthouse cottage",
        bedtime_glow="A round moon lay on the window and the lamp on the landing made a honey-colored ring on the wall.",
        shaft_kind="dumbwaiter",
        shaft_name="little service shaft",
        shaft_use="sending folded laundry and trays between floors",
        sound="a soft rope-creak and a tiny wooden tap from inside the wall",
        down_to="the warm kitchen below",
        tags={"house", "shaft"},
    ),
    "inn": Setting(
        id="inn",
        place="the tall family inn",
        bedtime_glow="Hall rugs muffled the steps, and the last lantern on the landing glowed like a sleepy star.",
        shaft_kind="laundry",
        shaft_name="laundry shaft",
        shaft_use="sending bed linens down to the wash room",
        sound="a muffled swish, as if the wall itself were sighing",
        down_to="the wash room on the lower floor",
        tags={"inn", "shaft"},
    ),
    "manor": Setting(
        id="manor",
        place="the drafty old manor house",
        bedtime_glow="The corridor was blue with evening, except for one warm bedside lamp left shining by the stairs.",
        shaft_kind="service",
        shaft_name="old service shaft",
        shaft_use="moving small house things between the upstairs hall and the pantry",
        sound="a low thump and a whisper of pulley rope",
        down_to="the pantry below",
        tags={"house", "shaft"},
    ),
}

SHAFT_USES = {
    "laundry": ShaftUse(
        id="laundry",
        noun="shaft",
        label="a narrow laundry shaft hidden in the wall",
        mechanism="a linen drop",
        safe_for={"pajamas", "napkin"},
        tags={"shaft", "laundry"},
    ),
    "basket": ShaftUse(
        id="basket",
        noun="shaft",
        label="a tiny dumbwaiter shaft with a basket and rope",
        mechanism="a little basket lift",
        safe_for={"napkin", "note"},
        tags={"shaft", "basket"},
    ),
}

PRIZES = {
    "teddy": Prize(
        id="teddy",
        label="teddy bear",
        phrase="a soft teddy bear",
        desire="to have it downstairs for cocoa and then in bed again",
        comfort="soft and brave under one arm",
        soft=True,
        narrow=False,
        can_ride_shaft=False,
        tags={"teddy", "comfort"},
    ),
    "slippers": Prize(
        id="slippers",
        label="slippers",
        phrase="a pair of moon-blue slippers",
        desire="to get them downstairs without having to make a second trip in the dark hall",
        comfort="waiting for warm feet",
        soft=True,
        narrow=False,
        can_ride_shaft=False,
        tags={"slippers", "bedtime"},
    ),
    "note": Prize(
        id="note",
        label="folded note",
        phrase="a folded good-night note",
        desire="to send it down quickly before the kitchen light went out",
        comfort="creased with care",
        narrow=True,
        soft=True,
        can_ride_shaft=True,
        tags={"note", "message"},
    ),
    "napkin": Prize(
        id="napkin",
        label="little napkin",
        phrase="a little embroidered napkin",
        desire="to send it down to the table before supper things were put away",
        comfort="smelling faintly of soap",
        narrow=True,
        soft=True,
        can_ride_shaft=True,
        tags={"napkin", "linen"},
    ),
}

MISUNDERSTANDINGS = {
    "anything_goes": Misunderstanding(
        id="anything_goes",
        thought='The child decided that if the shaft could carry house things, it must be a magic inside-the-wall shortcut for anything small enough to hold.',
        reason="The grown-up had said what the shaft did, but the child had heard only the part about going down quickly",
        action="So the little hatch was lifted",
        risky_reach="Then a hand stretched over the dark opening",
        tags={"misunderstanding", "guessing"},
    ),
    "secret_mail": Misunderstanding(
        id="secret_mail",
        thought='The child imagined the shaft was a secret mail hole and that anything meant kindly would surely arrive kindly too.',
        reason="Because bedtime makes old houses feel mysterious, the quiet warning about safety was mistaken for part of the mystery instead of part of the rule",
        action="The hatch clicked open",
        risky_reach="A small arm leaned farther in than it should have",
        tags={"misunderstanding", "message"},
    ),
    "shortcut": Misunderstanding(
        id="shortcut",
        thought='The child thought the shaft was simply a faster set of stairs hidden in the wall for objects that did not wish to wait.',
        reason="The house seemed full of clever old solutions, and one clever thought slipped into another",
        action="The narrow door was opened",
        risky_reach="The child tipped forward to guide the object down by hand",
        tags={"misunderstanding", "shortcut"},
    ),
}

REMEDIES = {
    "stairs_together": Remedy(
        id="stairs_together",
        sense=3,
        recovers_fallen=True,
        text='Instead, {helper} took the safe way and said, "We will carry {prize} down the stairs together."',
        answer_text="They carried it safely by the stairs with a grown-up",
        tags={"stairs", "ask_first"},
    ),
    "basket_properly": Remedy(
        id="basket_properly",
        sense=3,
        recovers_fallen=True,
        text='Then {helper} showed how the dumbwaiter basket worked, placed only the right kind of thing inside, and kept small hands well back from the edge.',
        answer_text="The grown-up used the basket the proper way and kept hands away from the edge",
        tags={"basket", "ask_first"},
    ),
    "hook_recover": Remedy(
        id="hook_recover",
        sense=2,
        recovers_fallen=True,
        text='{helper} fetched the long house hook kept for dropped linen, reached from the safe side, and brought {prize} back without letting anyone lean over the opening.',
        answer_text="The grown-up used a house hook to recover it safely",
        tags={"hook", "recovery"},
    ),
    "reach_again": Remedy(
        id="reach_again",
        sense=1,
        recovers_fallen=False,
        text='{helper} tried to lean in by hand again, which was far too risky and not a good example.',
        answer_text="They tried reaching again by hand",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Ella", "Ruby", "Ivy", "Ada", "Lucy"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Owen", "Max", "Leo", "Jude", "Sam"]
TRAITS = ["careful", "thoughtful", "patient", "sensible", "curious", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for shaft_id, shaft_use in SHAFT_USES.items():
            for prize_id, prize in PRIZES.items():
                if shaft_reasonable(shaft_use, prize):
                    combos.append((setting_id, shaft_id, prize_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    shaft_use: str
    prize: str
    misunderstanding: str
    remedy: str
    child_name: str
    child_gender: str
    cautioner_name: str
    cautioner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    child_age: int = 5
    cautioner_age: int = 7
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
    "shaft": [
        (
            "What is a shaft in an old house?",
            "A shaft is a narrow space that runs up and down inside a building. Some old houses use one to move laundry or a small basket between floors."
        )
    ],
    "laundry": [
        (
            "Why would a house have a laundry shaft?",
            "A laundry shaft lets cloth things go down to the wash room without carrying each bundle by hand. It is for chores, not for play."
        )
    ],
    "basket": [
        (
            "What is a dumbwaiter basket?",
            "A dumbwaiter basket is a little lift for small objects in a house. A grown-up uses it carefully so no hands go near the opening."
        )
    ],
    "ask_first": [
        (
            "Why should you ask a grown-up before using a strange house thing?",
            "Because some things in a house can be useful and still be unsafe for children. Asking first helps you understand the rule before you make a risky guess."
        )
    ],
    "stairs": [
        (
            "Why are stairs safer than leaning over a shaft?",
            "Stairs are meant for people to use with their feet on the floor. A shaft has an edge and a drop, so leaning over it can make you slip or lose what you are holding."
        )
    ],
    "hook": [
        (
            "Why do grown-ups use special tools to reach dropped things?",
            "A tool can reach into a tricky place while the person stays back in a safe spot. That keeps bodies away from edges and openings."
        )
    ],
    "message": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or imagines something the wrong way. Asking a question can clear it up before trouble starts."
        )
    ],
    "teddy": [
        (
            "Why do children love teddy bears at bedtime?",
            "A teddy bear can feel soft, familiar, and comforting. Holding one can make bedtime feel calmer."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime rules matter more in the dark?",
            "In the dark, it is easier to miss edges and hard-to-see places. Calm rules help everyone stay safe when the house is sleepy."
        )
    ],
}
KNOWLEDGE_ORDER = ["shaft", "laundry", "basket", "ask_first", "stairs", "hook", "message", "teddy", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    misunderstanding = f["misunderstanding"]
    return [
        f'Write a short bedtime story for a 3-to-5-year-old that includes the word "shaft" and teaches that asking is safer than guessing.',
        f"Tell a gentle cautionary story set in {setting.place} where {child.id} misunderstands an old house shaft and nearly makes a mistake with a {prize.label}.",
        f"Write a warm moral story about a child whose misunderstanding turns an ordinary house rule into a risky idea, and let the ending show that careful listening changes everything.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    cautioner = f["cautioner"]
    helper = f["helper"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    misunderstanding = f["misunderstanding"]
    remedy = f["remedy"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was getting ready for bed in {setting.place}, and about {helper.label_word} who helped when a misunderstanding began to grow."
        ),
        (
            "What did the child misunderstand?",
            f"{child.id} misunderstood what the shaft was for. {misunderstanding.reason}, so the shaft sounded like a quick shortcut instead of a grown-up house thing with rules."
        ),
        (
            f"Why did {cautioner.id} warn {child.id}?",
            f"{cautioner.id} could picture the danger before it happened. Opening the hatch and reaching over the shaft could make {child.id} wobble, and something might fall down the dark opening."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What stopped the mistake before anything fell?",
                f"{child.id} listened before going farther. The warning turned a guessing-thought into a question, and that pause was enough to keep the hatch from becoming a bigger problem."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} tried to use the shaft?",
                f"{child.id} opened the hatch and reached in, which made the moment risky. Because the idea came from a misunderstanding, {prize.label} was not handled the safe way and the room suddenly felt much scarier."
            )
        )
        if f.get("fell"):
            qa.append(
                (
                    f"Why was the clatter down the shaft such an important moment?",
                    f"It showed that the shaft was not a magic shortcut at all. The noise proved that one wrong guess can turn a quiet bedtime wish into a frightened problem very quickly."
                )
            )
    answer = remedy.answer_text
    qa.append(
        (
            f"How did {helper.label_word} solve the problem?",
            f"{helper.label_word.capitalize()} stayed calm and {answer}. That fixed the trouble without letting anyone lean near the edge again."
        )
    )
    qa.append(
        (
            "What is the lesson of the story?",
            f"The lesson is that asking first is wiser than guessing, especially around old house things. {child.id} learned that careful listening is a kind of bravery because it keeps people safe."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"shaft", "ask_first"}
    tags |= set(f["shaft_use"].tags)
    tags |= set(f["misunderstanding"].tags)
    tags |= set(f["prize_cfg"].tags)
    tags |= set(f["remedy"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="lighthouse",
        shaft_use="basket",
        prize="note",
        misunderstanding="secret_mail",
        remedy="basket_properly",
        child_name="Mira",
        child_gender="girl",
        cautioner_name="Ben",
        cautioner_gender="boy",
        helper="grandmother",
        trait="careful",
        relation="siblings",
        child_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        setting="inn",
        shaft_use="laundry",
        prize="teddy",
        misunderstanding="anything_goes",
        remedy="hook_recover",
        child_name="Ruby",
        child_gender="girl",
        cautioner_name="Theo",
        cautioner_gender="boy",
        helper="grandfather",
        trait="thoughtful",
        relation="siblings",
        child_age=5,
        cautioner_age=8,
    ),
    StoryParams(
        setting="manor",
        shaft_use="laundry",
        prize="slippers",
        misunderstanding="shortcut",
        remedy="stairs_together",
        child_name="Leo",
        child_gender="boy",
        cautioner_name="Ada",
        cautioner_gender="girl",
        helper="mother",
        trait="curious",
        relation="friends",
        child_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        setting="lighthouse",
        shaft_use="laundry",
        prize="napkin",
        misunderstanding="secret_mail",
        remedy="stairs_together",
        child_name="Ella",
        child_gender="girl",
        cautioner_name="Finn",
        cautioner_gender="boy",
        helper="father",
        trait="patient",
        relation="siblings",
        child_age=4,
        cautioner_age=7,
    ),
]


def explain_rejection(shaft_use: ShaftUse, prize: Prize) -> str:
    return (
        f"(No story: {shaft_use.label} is only reasonable for specific small house things, "
        f"but {prize.phrase} is not one of them. A good story here needs a real misunderstanding "
        f"about the shaft, followed by a safe correction.)"
    )


def explain_remedy(rid: str) -> str:
    remedy = REMEDIES[rid]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{rid}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of these safer fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_ask_first(params.relation, params.child_age, params.cautioner_age, params.trait):
        return "averted"
    return "rescued"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
reasonable_shaft_use(SU, P) :- shaft_use(SU), prize(P), allowed(SU, P).
sensible_remedy(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(Setting, SU, P) :- setting(Setting), reasonable_shaft_use(SU, P), prize(P).

% --- outcome inference -----------------------------------------------------
careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).
older_sibling :- relation(siblings), child_age(CA), cautioner_age(ZA), ZA > CA.
authority(C + 1) :- init_caution(C).
averted :- older_sibling, authority(A), bold_init(B), A > B.

outcome(averted) :- averted.
outcome(rescued) :- not averted.

#show valid/3.
#show sensible_remedy/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for shaft_id, shaft_use in SHAFT_USES.items():
        lines.append(asp.fact("shaft_use", shaft_id))
        for prize_id in sorted(shaft_use.safe_for):
            lines.append(asp.fact("allowed", shaft_id, prize_id))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_remedies() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible_remedy"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime misunderstanding about an old house shaft. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shaft-use", dest="shaft_use", choices=SHAFT_USES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shaft_use and args.prize:
        shaft_use = SHAFT_USES[args.shaft_use]
        prize = PRIZES[args.prize]
        if not shaft_reasonable(shaft_use, prize):
            raise StoryError(explain_rejection(shaft_use, prize))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shaft_use is None or c[1] == args.shaft_use)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shaft_use_id, prize_id = rng.choice(sorted(combos))
    misunderstanding_id = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    child_name, child_gender = _pick_child(rng)
    cautioner_name, cautioner_gender = _pick_child(rng, avoid=child_name)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    child_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        setting=setting_id,
        shaft_use=shaft_use_id,
        prize=prize_id,
        misunderstanding=misunderstanding_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=child_gender,
        cautioner_name=cautioner_name,
        cautioner_gender=cautioner_gender,
        helper=helper,
        trait=trait,
        relation=relation,
        child_age=child_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        shaft_use = SHAFT_USES[params.shaft_use]
        prize = PRIZES[params.prize]
        misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not shaft_reasonable(shaft_use, prize):
        raise StoryError(explain_rejection(shaft_use, prize))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        setting=setting,
        shaft_use=shaft_use,
        prize_cfg=prize,
        misunderstanding=misunderstanding,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        cautioner_name=params.cautioner_name,
        cautioner_gender=params.cautioner_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
        child_age=params.child_age,
        cautioner_age=params.cautioner_age,
    )

    helper = world.facts["helper"]
    world.paragraphs = [
        [
            sent.replace("{helper}", helper.label_word)
            for sent in para
        ]
        for para in world.paragraphs
    ]

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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_remedies = set(asp_sensible_remedies())
    python_remedies = {r.id for r in sensible_remedies()}
    if clingo_remedies == python_remedies:
        print(f"OK: sensible remedies match ({sorted(clingo_remedies)}).")
    else:
        rc = 1
        print(f"MISMATCH in remedies: clingo={sorted(clingo_remedies)} python={sorted(python_remedies)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            continue

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        remedies = asp_sensible_remedies()
        print(f"sensible remedies: {', '.join(remedies)}\n")
        print(f"{len(combos)} compatible (setting, shaft_use, prize) combos:\n")
        for setting, shaft_use, prize in combos:
            print(f"  {setting:10} {shaft_use:8} {prize}")
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
            header = f"### {p.child_name}: {p.prize} at {p.setting} via {p.shaft_use} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
