#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pate_fern_smush_kindness_cautionary_curiosity_detective.py
=====================================================================================

A standalone story world for a gentle detective-story domain built from the seed
words "pate", "fern", and "smush", with the features Kindness, Cautionary, and
Curiosity.

Premise
-------
Two children play detectives in a cozy public place. A clue for their case is
stuck high up behind a fern. One child grows too curious and wants to reach it
the unsafe way by climbing something unsteady. The other child warns them. A
kind grown-up helps, cleans up the mess, and teaches the safer rule: curious
detectives still ask for help when something is too high.

The simulation tracks both physical state (tilted fern, smushed lunch, danger,
recovered clue) and emotional state (curiosity, worry, relief, kindness). The
story text is rendered from that state rather than from one frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/pate_fern_smush_kindness_cautionary_curiosity_detective.py
    python storyworlds/worlds/gpt-5.4/pate_fern_smush_kindness_cautionary_curiosity_detective.py --all
    python storyworlds/worlds/gpt-5.4/pate_fern_smush_kindness_cautionary_curiosity_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pate_fern_smush_kindness_cautionary_curiosity_detective.py --verify
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
CURIOSITY_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "sensible"}


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
    fragile: bool = False
    edible: bool = False
    climbable: bool = False
    stable: bool = True
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "cook"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "librarian": "librarian",
            "cook": "cook",
            "mother": "mom",
            "father": "dad",
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
    room: str
    shelf: str
    adult_label: str
    adult_type: str
    lunch_spot: str
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
class CaseFile:
    id: str
    title: str
    missing: str
    clue: str
    ending: str
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
class Perch:
    id: str
    label: str
    phrase: str
    stable: bool
    wobble_text: str
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
class HelpMethod:
    id: str
    label: str
    sense: int
    power: int
    text: str
    clue_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "partner"}]

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
    perch = world.get("perch")
    if perch.meters["climbed"] < THRESHOLD or perch.attrs.get("stable", True):
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__wobble__")
    return out


def _r_bump_fern(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    fern = world.get("fern")
    if perch.meters["climbed"] < THRESHOLD or fern.meters["tilted"] >= THRESHOLD:
        return out
    if perch.attrs.get("stable", True):
        return out
    sig = ("bump_fern", fern.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fern.meters["tilted"] += 1
    fern.meters["soil_spilled"] += 1
    out.append("__fern__")
    return out


def _r_smush_lunch(world: World) -> list[str]:
    out: list[str] = []
    fern = world.get("fern")
    lunch = world.get("lunch")
    if fern.meters["tilted"] < THRESHOLD or lunch.meters["smushed"] >= THRESHOLD:
        return out
    sig = ("smush", lunch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lunch.meters["smushed"] += 1
    lunch.meters["messy"] += 1
    for kid in world.kids():
        kid.memes["guilt"] += 1
    out.append("__smush__")
    return out


def _r_need_help(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["danger"] < THRESHOLD and world.get("fern").meters["tilted"] < THRESHOLD:
        return out
    sig = ("need_help", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("adult").memes["alert"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="bump_fern", tag="physical", apply=_r_bump_fern),
    Rule(name="smush_lunch", tag="physical", apply=_r_smush_lunch),
    Rule(name="need_help", tag="social", apply=_r_need_help),
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


def sensible_methods() -> list[HelpMethod]:
    return [m for m in HELP_METHODS.values() if m.sense >= SENSE_MIN]


def mess_severity(perch: Perch, delay: int) -> int:
    return (2 if not perch.stable else 1) + delay


def can_restore(method: HelpMethod, perch: Perch, delay: int) -> bool:
    return method.power >= mess_severity(perch, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, partner_age: int, trait: str) -> bool:
    older_partner = relation == "siblings" and partner_age > instigator_age
    authority = initial_care(trait) + 1.0 + (4.0 if older_partner else 0.0)
    return older_partner and authority > CURIOSITY_INIT


def predict_mess(world: World) -> dict:
    sim = world.copy()
    do_climb(sim, narrate=False)
    return {
        "fern_tilted": sim.get("fern").meters["tilted"] >= THRESHOLD,
        "lunch_smushed": sim.get("lunch").meters["smushed"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def detective_setup(world: World, a: Entity, b: Entity, case: CaseFile) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} opened their little detective notebook in "
        f"{world.setting.place}. They were working on {case.title}, the case of the missing {case.missing}."
    )
    world.say(
        f"They whispered over clues, looked under chairs, and followed a tiny paper corner all the way to {world.setting.shelf}, where a green fern spilled soft leaves over the edge."
    )
    world.say(
        f'On the table below sat their lunch box, still holding a small pate sandwich for later, because detectives get hungry while they think.'
    )


def spot_clue(world: World, a: Entity, b: Entity, case: CaseFile) -> None:
    world.say(
        f'{a.id} narrowed {a.pronoun("possessive")} eyes. "There!" {a.pronoun()} whispered. '
        f'Behind the fern was {case.clue}.'
    )
    world.say(
        f'{b.id} stretched up on tiptoe, but the clue was too high to reach from the floor.'
    )


def tempt(world: World, a: Entity, perch: Perch) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'{a.id} looked at {perch.phrase}. "A real detective would climb up for a closer look," {a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, perch: Perch, adult: Entity) -> None:
    pred = predict_mess(world)
    b.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fern"] = pred["fern_tilted"]
    world.facts["predicted_smush"] = pred["lunch_smushed"]
    extra = ""
    if pred["lunch_smushed"]:
        extra = " and that little pate sandwich could go smush on the floor"
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{perch.label.capitalize()}s are not for climbing. You could bump the fern{extra}. Let\'s ask the {adult.label_word} instead."'
    )


def back_down(world: World, a: Entity, b: Entity, adult: Entity, method: HelpMethod, case: CaseFile) -> None:
    a.memes["curiosity"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked up at the shelf, then back at {b.id}, and took a slow breath. "You are right," {a.pronoun()} said. "Good detectives notice danger too."'
    )
    world.say(
        f"They went to the {adult.label_word} together and politely explained the mystery."
    )
    world.para()
    safe_help(world, adult, method, case, a, b, averted=True)


def defy(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I will only be one second," {a.id} said. Because {a.id} was {b.pronoun("possessive")} older sibling, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"I will only be one second," {a.id} said, and before {b.id} could answer, {a.pronoun()} put a foot on {perch.phrase}.'
        )


def do_climb(world: World, narrate: bool = True) -> None:
    perch = world.get("perch")
    perch.meters["climbed"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        if perch.attrs.get("stable", True):
            world.say("The climb was awkward, but the perch held still.")
        else:
            world.say(perch.attrs.get("wobble_text", "At once the perch gave a little wobble."))


def accident(world: World, a: Entity, b: Entity) -> None:
    fern = world.get("fern")
    lunch = world.get("lunch")
    if fern.meters["tilted"] >= THRESHOLD:
        world.say(
            f"The fern pot tipped, dark soil spilled onto the shelf, and a frond brushed {a.id}'s sleeve."
        )
    if lunch.meters["smushed"] >= THRESHOLD:
        world.say(
            f"The lunch box flipped open below, and the pate sandwich landed with a soft smush."
        )
    world.say(
        f'"Oh no!" cried {b.id}. "{a.id}, the clue can wait!"'
    )


def call_for_help(world: World, adult: Entity) -> None:
    world.say(f'"{adult.label_word.capitalize()}!" the children called together.')


def safe_help(
    world: World,
    adult: Entity,
    method: HelpMethod,
    case: CaseFile,
    a: Entity,
    b: Entity,
    averted: bool = False,
) -> None:
    world.get("room").meters["danger"] = 0.0
    world.get("fern").meters["tilted"] = 0.0
    world.get("fern").meters["upright"] += 1
    world.get("clue").meters["found"] += 1
    world.get("adult").memes["kindness"] += 1
    if not averted:
        world.get("lunch").meters["cleaned"] += 1
    world.say(
        f"The {adult.label_word} came over at once, calm and kind, and {method.text}"
    )
    world.say(method.clue_text.format(case_ending=case.ending))
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'"Curiosity is wonderful," the {adult.label_word} said softly, "but detectives ask for help when a clue is too high."'
    )


def failed_help(world: World, adult: Entity, method: HelpMethod, case: CaseFile) -> None:
    world.get("room").meters["danger"] += 1
    world.get("fern").meters["broken_pot"] += 1
    world.get("lunch").meters["smushed"] += 1
    world.say(
        f"The {adult.label_word} hurried over and {method.text}, but the wobbling had already done its work."
    )
    world.say(
        "The pot cracked on the corner of the shelf, soil scattered wider, and the clue fluttered down into the mess."
    )


def kind_lesson(world: World, adult: Entity, a: Entity, b: Entity) -> None:
    lunch = world.get("lunch")
    if lunch.meters["smushed"] >= THRESHOLD:
        world.say(
            f"The {adult.label_word} set the fern upright, wiped the floor, and even wrapped the poor smushed pate sandwich so no one would step on it."
        )
    world.say(
        f"Neither child got scolded with sharp words. Instead, the {adult.label_word} knelt beside them and made sure they were safe first."
    )
    world.say(
        f'{a.id} whispered sorry. {b.id} squeezed {a.pronoun("possessive")} hand, and the room felt steady again.'
    )


def sad_lesson(world: World, adult: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"The {adult.label_word} checked that both children were safe, then sighed at the cracked pot and the ruined lunch."
    )
    world.say(
        f'"A clue is never worth a tumble," the {adult.label_word} said. {a.id} and {b.id} nodded, because now they understood how quickly one curious choice could make a bigger mess than a mystery.'
    )


def bright_ending(world: World, case: CaseFile, a: Entity, b: Entity, method: HelpMethod) -> None:
    world.say(
        f"With the clue safe at last, the young detectives solved {case.title}. {case.ending}"
    )
    world.say(
        f"After that, whenever something sat too high, {a.id} and {b.id} fetched the {method.label} first and grinned at each other like true detectives."
    )


def tell(
    setting: Setting,
    case: CaseFile,
    perch: Perch,
    method: HelpMethod,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    partner: str = "Ben",
    partner_gender: str = "boy",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 5,
    partner_age: int = 7,
    delay: int = 0,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=partner,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=setting.adult_type,
        role="adult",
        label=setting.adult_label,
        helpful=True,
    ))
    world.add(Entity(id="room", type="room", label=setting.room))
    world.add(Entity(id="fern", type="plant", label="fern", fragile=True))
    world.add(Entity(id="lunch", type="food", label="pate sandwich", edible=True))
    world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        climbable=True,
        stable=perch.stable,
        attrs={"stable": perch.stable, "wobble_text": perch.wobble_text},
    ))
    world.add(Entity(id="clue", type="clue", label=case.clue))

    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["care"] = initial_care(trait)
    world.facts.update(
        setting=setting,
        case=case,
        perch_cfg=perch,
        method=method,
        instigator=a,
        partner=b,
        adult=adult,
        relation=relation,
        delay=delay,
    )

    detective_setup(world, a, b, case)
    spot_clue(world, a, b, case)

    world.para()
    tempt(world, a, perch)
    warn(world, b, a, perch, adult)

    averted = would_avert(relation, instigator_age, partner_age, trait)

    if averted:
        back_down(world, a, b, adult, method, case)
        outcome = "averted"
    else:
        defy(world, a, b, perch)
        world.para()
        do_climb(world, narrate=True)
        accident(world, a, b)
        call_for_help(world, adult)

        world.para()
        contained = can_restore(method, perch, delay)
        if contained:
            safe_help(world, adult, method, case, a, b, averted=False)
            kind_lesson(world, adult, a, b)
            world.para()
            bright_ending(world, case, a, b, method)
            outcome = "contained"
        else:
            failed_help(world, adult, method, case)
            sad_lesson(world, adult, a, b)
            outcome = "broken"

    world.facts.update(
        outcome=outcome,
        averted=outcome == "averted",
        recovered=world.get("clue").meters["found"] >= THRESHOLD,
        lunch_smushed=world.get("lunch").meters["smushed"] >= THRESHOLD,
        fern_tilted=world.get("fern").meters["tilted"] >= THRESHOLD or world.get("fern").meters["broken_pot"] >= THRESHOLD,
        promised=world.get("instigator").memes["lesson"] >= THRESHOLD if "instigator" in world.entities else a.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the little library reading room",
        room="reading room",
        shelf="the tall map shelf",
        adult_label="librarian",
        adult_type="librarian",
        lunch_spot="the puzzle table",
        tags={"library", "books"},
    ),
    "tea_shop": Setting(
        id="tea_shop",
        place="the corner tea shop",
        room="tea shop",
        shelf="the biscuit shelf",
        adult_label="cook",
        adult_type="cook",
        lunch_spot="the window table",
        tags={"shop", "snack"},
    ),
    "museum": Setting(
        id="museum",
        place="the tiny town museum",
        room="museum hall",
        shelf="the display shelf",
        adult_label="librarian",
        adult_type="librarian",
        lunch_spot="the bench by the window",
        tags={"museum", "clues"},
    ),
}

CASES = {
    "ribbon": CaseFile(
        id="ribbon",
        title="The Case of the Missing Blue Ribbon",
        missing="blue ribbon",
        clue="a folded note tied with blue thread",
        ending="The ribbon had been pinned inside the notebook all along, and the note was only a helpful hint left by a kind grown-up.",
        tags={"ribbon", "note"},
    ),
    "button": CaseFile(
        id="button",
        title="The Case of the Silver Button",
        missing="silver button",
        clue="a paper arrow with a shiny button drawn on it",
        ending="The real button was found tucked into a coat pocket, where it had been safe the whole time.",
        tags={"button", "arrow"},
    ),
    "stamp": CaseFile(
        id="stamp",
        title="The Case of the Red Stamp",
        missing="red stamp",
        clue="a tiny envelope marked with red ink",
        ending="The stamp turned up in the return basket, and the children laughed at how ordinary the hiding place had been.",
        tags={"stamp", "envelope"},
    ),
}

PERCHES = {
    "rolling_chair": Perch(
        id="rolling_chair",
        label="rolling chair",
        phrase="the rolling chair",
        stable=False,
        wobble_text="The wheels gave a sudden squeak and the chair slipped sideways.",
        tags={"chair", "unsafe"},
    ),
    "book_stack": Perch(
        id="book_stack",
        label="book stack",
        phrase="the stack of books",
        stable=False,
        wobble_text="The books slid with a hushy scrape, and the whole pile leaned.",
        tags={"books", "unsafe"},
    ),
    "footstool": Perch(
        id="footstool",
        label="footstool",
        phrase="the wooden footstool",
        stable=True,
        wobble_text="",
        tags={"stool", "steady"},
    ),
}

HELP_METHODS = {
    "step_stool": HelpMethod(
        id="step_stool",
        label="step stool",
        sense=3,
        power=4,
        text="brought over a sturdy step stool, steadied the fern pot with one hand, and reached the clue without any more wobbling.",
        clue_text='Then the {adult} tucked the clue into the children\'s notebook and said, "{case_ending}"'.replace("{adult}", "librarian"),
        qa_text="used a sturdy step stool and a careful hand to reach the clue safely",
        tags={"step_stool", "ask_help"},
    ),
    "long_reacher": HelpMethod(
        id="long_reacher",
        label="long reacher",
        sense=3,
        power=3,
        text="used a long reacher to lift the clue free and set the fern upright again before the soil spread farther.",
        clue_text="A moment later the clue was safe, and the mystery could go on without another spill.",
        qa_text="used a long reacher to free the clue and steady the fern",
        tags={"reacher", "ask_help"},
    ),
    "quick_grab": HelpMethod(
        id="quick_grab",
        label="quick grab",
        sense=1,
        power=1,
        text="made a quick grab for the clue from the floor",
        clue_text="The clue came loose, but the mess had already grown.",
        qa_text="grabbed for the clue too quickly",
        tags={"grab"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Sam", "Theo", "Eli", "Jack"]
TRAITS = ["careful", "patient", "steady", "sensible", "curious", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_methods():
        return combos
    for setting_id in SETTINGS:
        for case_id in CASES:
            for perch_id, perch in PERCHES.items():
                if not perch.stable:
                    combos.append((setting_id, case_id, perch_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    case: str
    perch: str
    method: str
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    relation: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    partner_age: int = 7
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
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery. A good detective also notices danger and asks for help when needed.",
        )
    ],
    "fern": [
        (
            "What is a fern?",
            "A fern is a green plant with many feathery leaves called fronds. Ferns can tip over if their pots are bumped.",
        )
    ],
    "pate": [
        (
            "What is pate?",
            "Pate is a soft spread that people can put in a sandwich. Because it is soft, it can smush easily if it falls.",
        )
    ],
    "smush": [
        (
            "What does smush mean?",
            "Smush means something soft gets squashed flat or messy. A sandwich can go smush if it lands hard on the floor.",
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something high in a steadier, safer way. Children should still use one with a grown-up's help when needed.",
        )
    ],
    "reacher": [
        (
            "What is a reacher tool?",
            "A reacher is a long tool that helps pick up or pull down things from far away. It can help a grown-up reach safely without climbing.",
        )
    ],
    "ask_help": [
        (
            "Why should children ask a grown-up for help with high things?",
            "High places can be tricky, wobbly, or full of things that might fall. Asking a grown-up keeps people, plants, and objects safer.",
        )
    ],
    "chair": [
        (
            "Why is a rolling chair bad for climbing?",
            "A rolling chair can move when you put your weight on it. That makes it easy to slip and bump nearby things.",
        )
    ],
    "books": [
        (
            "Why is a stack of books unsafe to stand on?",
            "Books can slide and tip because they are not made to be steps. A pile that looks still can suddenly lean.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "fern", "pate", "smush", "chair", "books", "step_stool", "reacher", "ask_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    a = f["instigator"]
    b = f["partner"]
    perch = f["perch_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a gentle detective story for a 3-to-5-year-old where two children investigate {case.title} and a clue is hidden behind a fern.',
            f"Tell a curiosity-and-kindness story where {a.id} wants to climb {perch.phrase}, but {b.id} warns about the danger and they ask a grown-up instead.",
            'Write a cautionary detective tale that includes the words "pate", "fern", and "smush", but ends safely because the children choose help over climbing.',
        ]
    if outcome == "broken":
        return [
            f'Write a sadder cautionary detective story where a clue behind a fern leads to an unsafe climb and a bigger mess.',
            f'Tell a mystery story for young children that includes the words "pate", "fern", and "smush" and shows why high clues should be left to grown-ups.',
            f"Write a detective-story warning tale where {a.id}'s curiosity causes trouble before the mystery is solved.",
        ]
    return [
        f'Write a detective story for a 3-to-5-year-old where two children follow clues in {world.setting.place} and one clue is hidden behind a fern.',
        f'Tell a child-friendly mystery in which curiosity causes a wobble, a pate sandwich goes smush, and a kind grown-up helps fix the problem.',
        f'Write a simple cautionary story with kindness, curiosity, and a safe ending, using the words "pate", "fern", and "smush".',
    ]


def relation_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    adult = f["adult"]
    case = f["case"]
    perch = f["perch_cfg"]
    method = f["method"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation_noun(a, b, relation)}, {a.id} and {b.id}, who were pretending to be detectives. They were trying to solve {case.title} in {world.setting.place}.",
        ),
        (
            "What mystery were they trying to solve?",
            f"They were working on {case.title}, looking for the missing {case.missing}. The clue they needed was hidden behind a fern on a high shelf.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to climb?",
            f"{b.id} could tell that {perch.phrase} was not safe for climbing. {b.pronoun().capitalize()} worried it could wobble, bump the fern, and make an even bigger mess.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} listened and stepped back instead of climbing. Then both children asked the {adult.label_word} for help, which kept the fern safe and let the mystery continue.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely and happily. The clue was reached the careful way, and the children learned that curious detectives can still be patient detectives.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened during the accident?",
                f"The perch wobbled, the fern tipped, and the pate sandwich below went smush. The trouble started because curiosity moved faster than caution.",
            )
        )
        qa.append(
            (
                f"How did the {adult.label_word} help?",
                f"The {adult.label_word} {method.qa_text}. That kind help made the room safe again and let the children solve the case without more damage.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that curiosity is good, but climbing unsafe things is not. Next time they would ask for help before reaching for a high clue.",
            )
        )
    else:
        qa.append(
            (
                "Did the grown-up fix everything right away?",
                f"No. The grown-up hurried to help, but the wobbling had already broken the fern pot and ruined the lunch. The children were safe, yet they could see how one risky choice had made the mystery sadder.",
            )
        )
        qa.append(
            (
                "What lesson did the ending teach?",
                f"It taught that a clue is never worth climbing something unsafe. Asking for help early would have protected the fern, the lunch, and the children's detective game.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "fern", "pate", "smush", "ask_help"}
    tags |= set(world.facts["perch_cfg"].tags)
    if world.facts["outcome"] != "broken":
        tags |= set(world.facts["method"].tags)
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
        flags = [name for name, on in (
            ("fragile", e.fragile),
            ("edible", e.edible),
            ("climbable", e.climbable),
            ("stable", e.stable),
            ("helpful", e.helpful),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_perch(perch: Perch) -> str:
    return (
        f"(No story: {perch.phrase} is already steady enough that the cautionary accident disappears. "
        f"Choose an unsafe perch like a rolling chair or a stack of books.)"
    )


def explain_method(method_id: str) -> str:
    m = HELP_METHODS[method_id]
    better = " / ".join(sorted(x.id for x in sensible_methods()))
    return (
        f"(Refusing help method '{method_id}': it scores too low on common sense "
        f"(sense={m.sense} < {SENSE_MIN}). A kinder story uses a steadier, safer fix. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.partner_age, params.trait):
        return "averted"
    return "contained" if can_restore(HELP_METHODS[params.method], PERCHES[params.perch], params.delay) else "broken"


ASP_RULES = r"""
unsafe_perch(P) :- perch(P), not stable(P).
sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
valid(S,C,P) :- setting(S), case(C), unsafe_perch(P).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).
older_partner :- relation(siblings), instigator_age(IA), partner_age(PA), PA > IA.
bonus(4) :- older_partner.
bonus(0) :- not older_partner.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- older_partner, authority(A), curiosity_init(CI), A > CI.

severity(2 + D) :- chosen_perch(P), unsafe_perch(P), delay(D).
severity(1 + D) :- chosen_perch(P), stable(P), delay(D).
method_power(P) :- chosen_method(M), power(M,P).
contained :- method_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        if perch.stable:
            lines.append(asp.fact("stable", pid))
    for mid, method in HELP_METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_method", params.method),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


CURATED = [
    StoryParams(
        setting="library",
        case="ribbon",
        perch="rolling_chair",
        method="step_stool",
        instigator="Nora",
        instigator_gender="girl",
        partner="Ben",
        partner_gender="boy",
        relation="friends",
        trait="careful",
        delay=0,
        instigator_age=5,
        partner_age=5,
    ),
    StoryParams(
        setting="tea_shop",
        case="button",
        perch="book_stack",
        method="long_reacher",
        instigator="Max",
        instigator_gender="boy",
        partner="Ruby",
        partner_gender="girl",
        relation="siblings",
        trait="patient",
        delay=0,
        instigator_age=5,
        partner_age=7,
    ),
    StoryParams(
        setting="museum",
        case="stamp",
        perch="rolling_chair",
        method="long_reacher",
        instigator="Ava",
        instigator_gender="girl",
        partner="Leo",
        partner_gender="boy",
        relation="friends",
        trait="steady",
        delay=1,
        instigator_age=6,
        partner_age=6,
    ),
    StoryParams(
        setting="library",
        case="button",
        perch="book_stack",
        method="quick_grab",
        instigator="Finn",
        instigator_gender="boy",
        partner="Mia",
        partner_gender="girl",
        relation="friends",
        trait="curious",
        delay=1,
        instigator_age=6,
        partner_age=6,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: curious child detectives, a high clue, a fern, a pate sandwich, and a kind cautionary lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--method", choices=HELP_METHODS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the mess grows before help settles it")
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
    if args.perch and PERCHES[args.perch].stable:
        raise StoryError(explain_perch(PERCHES[args.perch]))
    if args.method and HELP_METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.case is None or c[1] == args.case)
        and (args.perch is None or c[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, case_id, perch_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    relation = args.relation or rng.choice(["siblings", "friends"])
    instigator, ig = _pick_child(rng)
    partner, pg = _pick_child(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    instigator_age, partner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        setting=setting_id,
        case=case_id,
        perch=perch_id,
        method=method_id,
        instigator=instigator,
        instigator_gender=ig,
        partner=partner,
        partner_gender=pg,
        relation=relation,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.method not in HELP_METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if PERCHES[params.perch].stable:
        raise StoryError(explain_perch(PERCHES[params.perch]))
    if HELP_METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        case=CASES[params.case],
        perch=PERCHES[params.perch],
        method=HELP_METHODS[params.method],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        partner_age=params.partner_age,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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

    py_sense = {m.id for m in sensible_methods()}
    cl_sense = set(asp_sensible())
    if py_sense == cl_sense:
        print(f"OK: sensible methods match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(cl_sense)} python={sorted(py_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, case, perch) combos:\n")
        for setting_id, case_id, perch_id in combos:
            print(f"  {setting_id:10} {case_id:8} {perch_id}")
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
            header = f"### {p.instigator} & {p.partner}: {p.case} at {p.setting} ({p.perch}, {p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
