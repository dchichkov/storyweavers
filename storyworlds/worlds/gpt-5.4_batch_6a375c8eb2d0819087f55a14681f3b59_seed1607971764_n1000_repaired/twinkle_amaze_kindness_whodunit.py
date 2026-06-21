#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py
=============================================================

A standalone storyworld for a tiny, child-facing whodunit shaped by kindness.

Premise:
    A small shiny thing has gone missing from a cozy shared place. Two children
    decide to solve the mystery. The clues look suspicious at first, but the
    "culprit" turns out to have borrowed the object for a kind reason. Together,
    the children repair the missing sparkle and end with even more twinkle than
    before.

Run it
------
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/twinkle_amaze_kindness_whodunit.py --verify
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
KIND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    display: str
    display_the: str
    hush: str
    search_path: str
    repair_spot: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    shine: str
    from_display: str
    replacement: str
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
class KindAct:
    id: str
    need: str
    recipient_need: str
    location: str
    clue_one: str
    clue_two: str
    reveal_line: str
    fix_line: str
    ending_image: str
    requires: set[str] = field(default_factory=set)
    settings: set[str] = field(default_factory=set)
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
class Approach:
    id: str
    kindness: int
    ask_line: str
    explain: str
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
class Temperament:
    id: str
    openness: int
    blush: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"investigator", "friend", "culprit", "recipient"}]

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


def _r_missing_dims(world: World) -> list[str]:
    item = world.entities.get("lost")
    room = world.entities.get("room")
    sleuth = world.entities.get("investigator")
    if not item or not room or not sleuth:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_dims", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["dim"] += 1
    sleuth.memes["curious"] += 1
    return ["__missing__"]


def _r_clues_focus(world: World) -> list[str]:
    case = world.entities.get("case")
    sleuth = world.entities.get("investigator")
    if not case or not sleuth:
        return []
    if case.meters["clues"] < 2:
        return []
    sig = ("clues_focus", case.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sleuth.memes["confidence"] += 1
    return []


def _r_kindness_warms(world: World) -> list[str]:
    culprit = world.entities.get("culprit")
    room = world.entities.get("room")
    if not culprit or not room:
        return []
    if culprit.memes["kind_revealed"] < THRESHOLD:
        return []
    sig = ("kindness_warms", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["warmth"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_dims", tag="physical", apply=_r_missing_dims),
    Rule(name="clues_focus", tag="social", apply=_r_clues_focus),
    Rule(name="kindness_warms", tag="emotional", apply=_r_kindness_warms),
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
        for sent in produced:
            world.say(sent)
    return produced


def item_suits_act(lost: LostThing, act: KindAct) -> bool:
    return bool(set(lost.tags) & set(act.requires))


def setting_supports(setting: Setting, act: KindAct) -> bool:
    return act.id in setting.affords and setting.id in act.settings


def kind_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.kindness >= KIND_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for lid, lost in LOST_THINGS.items():
            for aid, act in KIND_ACTS.items():
                if setting_supports(setting, act) and item_suits_act(lost, act):
                    combos.append((sid, lid, aid))
    return sorted(combos)


def reveal_outcome(approach: Approach, temperament: Temperament) -> str:
    return "quick" if approach.kindness + temperament.openness >= 4 else "shy"


def predict_kind_reveal(setting: Setting, lost: LostThing, act: KindAct,
                        approach: Approach, temperament: Temperament) -> dict:
    if not setting_supports(setting, act):
        return {"works": False, "outcome": "blocked"}
    if not item_suits_act(lost, act):
        return {"works": False, "outcome": "blocked"}
    if approach.kindness < KIND_MIN:
        return {"works": False, "outcome": "blocked"}
    return {"works": True, "outcome": reveal_outcome(approach, temperament)}


def introduce(world: World, sleuth: Entity, friend: Entity, setting: Setting, teacher: Entity) -> None:
    world.say(
        f"Morning light lay softly across {setting.place}, and {setting.display_the} gave a small {sleuth.pronoun('possessive')}-favorite twinkle. "
        f"{sleuth.id} and {friend.id} liked to notice little things before anyone else did."
    )
    world.say(
        f"{teacher.label_word.capitalize()} was straightening books nearby, and the whole place felt so quiet that even a whisper sounded important."
    )
    world.say(setting.hush)


def discover_missing(world: World, sleuth: Entity, friend: Entity, setting: Setting, lost: LostThing) -> None:
    item = world.get("lost")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {sleuth.id} looked closely, {lost.from_display} was gone."
    )
    world.say(
        f'"Something is missing," {sleuth.id} whispered. {friend.id} leaned in beside {sleuth.pronoun("object")}, and both of them stared at the empty spot.'
    )
    world.say(
        f"The missing shine made the mystery feel real at once."
    )


def open_case(world: World, sleuth: Entity, friend: Entity, lost: LostThing) -> None:
    sleuth.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f'"Who borrowed the {lost.label}?" {friend.id} asked. {sleuth.id} pressed {sleuth.pronoun("possessive")} lips together like a tiny detective.'
    )
    world.say(
        f'"Let\'s look for clues before we blame anyone," {sleuth.pronoun()} said.'
    )


def find_first_clue(world: World, sleuth: Entity, friend: Entity, act: KindAct, setting: Setting) -> None:
    world.get("case").meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They searched along {setting.search_path} and found the first clue: {act.clue_one}."
    )
    world.say(
        f'{friend.id}\'s eyes grew round. "That means someone carried it this way," {friend.pronoun()} said.'
    )


def find_second_clue(world: World, sleuth: Entity, friend: Entity, act: KindAct) -> None:
    world.get("case").meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A little farther on, they found the second clue: {act.clue_two}."
    )
    world.say(
        f'"This case might amaze us," {sleuth.id} murmured. Now the trail led straight toward {act.location}.'
    )


def ask_kindly(world: World, sleuth: Entity, culprit: Entity, approach: Approach, lost: LostThing) -> None:
    sleuth.memes["kindness"] += 1
    world.say(
        f"There they saw {culprit.id}. {approach.ask_line.format(culprit=culprit.id, item=lost.label)}"
    )
    world.say(approach.explain)


def confess_quick(world: World, culprit: Entity, recipient: Entity, act: KindAct,
                  lost: LostThing, temperament: Temperament) -> None:
    culprit.memes["kind_revealed"] += 1
    culprit.memes["worry"] = 0.0
    recipient.memes["comfort"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{culprit.id} {temperament.blush} and nodded right away. {act.reveal_line.format(recipient=recipient.id, item=lost.label)}"
    )
    world.say(
        f'"I was going to bring it back after I helped," {culprit.pronoun()} said.'
    )


def confess_shy(world: World, culprit: Entity, recipient: Entity, teacher: Entity,
                act: KindAct, lost: LostThing, temperament: Temperament) -> None:
    culprit.memes["worry"] += 1
    world.say(
        f"{culprit.id} {temperament.blush} and looked down at the floor. For a moment, {culprit.pronoun()} could not get the words out."
    )
    world.say(
        f"{teacher.label_word.capitalize()} came closer, not angry at all, and waited beside {culprit.pronoun('object')}."
    )
    culprit.memes["kind_revealed"] += 1
    culprit.memes["worry"] = 0.0
    recipient.memes["comfort"] += 1
    propagate(world, narrate=False)
    world.say(
        act.reveal_line.format(recipient=recipient.id, item=lost.label)
    )
    world.say(
        f'"I did not want the room to lose its sparkle forever," {culprit.pronoun()} added. "I just wanted {recipient.id} to feel a little better first."'
    )


def explain_need(world: World, recipient: Entity, act: KindAct) -> None:
    world.say(
        f"Then everyone saw the reason: {recipient.id} {act.recipient_need}."
    )
    world.say(
        f"The mystery stopped feeling sharp and began to feel warm."
    )


def repair_together(world: World, sleuth: Entity, friend: Entity, culprit: Entity,
                    recipient: Entity, teacher: Entity, setting: Setting,
                    lost: LostThing, act: KindAct) -> None:
    room = world.get("room")
    item = world.get("lost")
    room.meters["dim"] = 0.0
    room.meters["twinkle"] += 1
    item.meters["missing"] = 0.0
    item.meters["shared"] += 1
    sleuth.memes["joy"] += 1
    friend.memes["joy"] += 1
    culprit.memes["relief"] += 1
    recipient.memes["joy"] += 1
    world.say(
        f"{teacher.label_word.capitalize()} smiled. {act.fix_line.format(replacement=lost.replacement, repair_spot=setting.repair_spot)}"
    )
    world.say(
        f"Soon {recipient.id} had the borrowed {lost.label}, and {setting.display_the} had {lost.replacement} in its place."
    )
    world.say(
        act.ending_image.format(display=setting.display, recipient=recipient.id)
    )


def close_case(world: World, sleuth: Entity, friend: Entity, culprit: Entity) -> None:
    world.say(
        f'"Case closed," {friend.id} announced softly.'
    )
    world.say(
        f'{sleuth.id} shook {sleuth.pronoun("possessive")} head. "Not a stealing case," {sleuth.pronoun()} said. "A kindness case."'
    )
    world.say(
        f"{culprit.id} smiled then, and everyone smiled back."
    )


def tell(setting: Setting, lost: LostThing, act: KindAct, approach: Approach,
         temperament: Temperament,
         investigator_name: str = "Lily", investigator_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         culprit_name: str = "Mia", culprit_gender: str = "girl",
         recipient_name: str = "Noah", recipient_gender: str = "boy",
         teacher_type: str = "teacher") -> World:
    world = World(setting)

    room = world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="case", type="case", label="the case"))
    sleuth = world.add(Entity(
        id="investigator", kind="character", type=investigator_gender, label=investigator_name,
        role="investigator", attrs={"name": investigator_name}, traits=["observant"],
    ))
    friend = world.add(Entity(
        id="friend", kind="character", type=friend_gender, label=friend_name,
        role="friend", attrs={"name": friend_name}, traits=["eager"],
    ))
    culprit = world.add(Entity(
        id="culprit", kind="character", type=culprit_gender, label=culprit_name,
        role="culprit", attrs={"name": culprit_name}, traits=[temperament.id],
    ))
    recipient = world.add(Entity(
        id="recipient", kind="character", type=recipient_gender, label=recipient_name,
        role="recipient", attrs={"name": recipient_name}, traits=["tender"],
    ))
    teacher = world.add(Entity(
        id="teacher", kind="character", type=teacher_type, label="the teacher", role="teacher"
    ))
    world.add(Entity(
        id="lost", type="object", label=lost.label, tags=set(lost.tags), attrs={"phrase": lost.phrase}
    ))

    room.meters["twinkle"] = 1.0
    culprit.memes["worry"] = 0.0
    recipient.memes["comfort"] = 0.0
    sleuth.memes["kindness"] = 0.0

    world.facts.update(
        setting=setting,
        lost_cfg=lost,
        act=act,
        approach=approach,
        temperament=temperament,
        investigator=sleuth,
        friend=friend,
        culprit=culprit,
        recipient=recipient,
        teacher=teacher,
    )

    introduce(world, sleuth, friend, setting, teacher)
    discover_missing(world, sleuth, friend, setting, lost)
    world.para()
    open_case(world, sleuth, friend, lost)
    find_first_clue(world, sleuth, friend, act, setting)
    find_second_clue(world, sleuth, friend, act)
    world.para()
    ask_kindly(world, sleuth, culprit, approach, lost)

    outcome = reveal_outcome(approach, temperament)
    if outcome == "quick":
        confess_quick(world, culprit, recipient, act, lost, temperament)
    else:
        confess_shy(world, culprit, recipient, teacher, act, lost, temperament)

    explain_need(world, recipient, act)
    world.para()
    repair_together(world, sleuth, friend, culprit, recipient, teacher, setting, lost, act)
    close_case(world, sleuth, friend, culprit)

    world.facts.update(
        outcome=outcome,
        clues=int(world.get("case").meters["clues"]),
        dimmed=room.meters["dim"] <= 0 and world.get("lost").meters["shared"] >= THRESHOLD,
        kindness_revealed=culprit.memes["kind_revealed"] >= THRESHOLD,
        recipient_comforted=recipient.memes["comfort"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        display="the reading-corner moon mobile",
        display_the="the reading-corner moon mobile",
        hush="Above the rug, paper stars hung around a moon, and every silver edge seemed to twinkle when the children walked by.",
        search_path="the paint shelf and the cubbies",
        repair_spot="the art table",
        affords={"welcome_card", "bandage_box", "quiet_blanket"},
        tags={"school", "mystery"},
    ),
    "library": Setting(
        id="library",
        place="the little library room",
        display="the window-night garland",
        display_the="the window-night garland",
        hush="Blue paper clouds and tiny stars swayed in the window, and their foil corners gave a sleepy twinkle over the cushions.",
        search_path="the picture-book baskets and the return cart",
        repair_spot="the low craft desk",
        affords={"welcome_card", "bookmark", "quiet_blanket"},
        tags={"library", "mystery"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        display="the cardboard castle sky",
        display_the="the cardboard castle sky",
        hush="Over the block castle, little moon pieces and stars leaned from strings and made the whole fort look ready to twinkle.",
        search_path="the block bins and the costume hooks",
        repair_spot="the big play table",
        affords={"bandage_box", "bookmark", "quiet_blanket"},
        tags={"play", "mystery"},
    ),
}

LOST_THINGS = {
    "silver_star": LostThing(
        id="silver_star",
        label="silver star",
        phrase="a silver paper star",
        shine="silver",
        from_display="one silver paper star from the display",
        replacement="a new folded silver star",
        tags={"flat", "sparkly", "star"},
    ),
    "gold_moon": LostThing(
        id="gold_moon",
        label="gold moon",
        phrase="a gold paper moon",
        shine="gold",
        from_display="a gold moon piece from the display",
        replacement="a fresh gold moon cutout",
        tags={"flat", "sparkly", "moon"},
    ),
    "foil_heart": LostThing(
        id="foil_heart",
        label="foil heart",
        phrase="a shiny foil heart",
        shine="foil",
        from_display="a foil heart from the display",
        replacement="a bright new foil heart",
        tags={"flat", "sparkly", "heart"},
    ),
}

KIND_ACTS = {
    "welcome_card": KindAct(
        id="welcome_card",
        need="a welcome card for a new child",
        recipient_need="was sitting quietly because the room still felt new",
        location="the art table",
        clue_one="a curl of tape with silver glitter on it",
        clue_two="a folded card that had one empty spot shaped exactly like the missing piece",
        reveal_line='"I borrowed the {item} for {recipient}\'s welcome card," {culprit} said. "The card looked plain, and I wanted the first hello to shine."',
        fix_line='Together they cut {replacement} at {repair_spot} and taped it carefully where the old one had been.',
        ending_image='By snack time, {display} was twinkling again, and {recipient} kept touching the welcome card and smiling.',
        requires={"flat", "sparkly"},
        settings={"classroom", "library"},
        tags={"welcome", "craft", "kindness"},
    ),
    "bandage_box": KindAct(
        id="bandage_box",
        need="a cheery bandage box for a hurt child",
        recipient_need="had a sore knee and was trying very hard not to cry",
        location="the quiet bench",
        clue_one="a tiny paper scrap with gold or silver dust on one side",
        clue_two="the class bandage box, now decorated with a lonely empty patch where one last shiny piece should go",
        reveal_line='"I borrowed the {item} to brighten the bandage box for {recipient}," {culprit} said. "I thought one brave little shine might help more than an empty wall."',
        fix_line='Then they made {replacement} at {repair_spot}, and even the scissors sounded busy and cheerful.',
        ending_image='Soon {display} shone again, and {recipient} sat taller on the bench with the bright bandage box beside them.',
        requires={"flat", "sparkly"},
        settings={"classroom", "playroom"},
        tags={"care", "injury", "kindness"},
    ),
    "quiet_blanket": KindAct(
        id="quiet_blanket",
        need="a cozy quiet-corner blanket tag",
        recipient_need="felt shy and wanted a soft place to rest for a minute",
        location="the quiet corner",
        clue_one="a ribbon string leading toward the cushions",
        clue_two="a blanket tag with a neat blank shape waiting for something shiny",
        reveal_line='"I borrowed the {item} to make the quiet blanket tag for {recipient}," {culprit} said. "I wanted the cozy corner to feel welcoming."',
        fix_line='So they crafted {replacement} at {repair_spot} and promised the quiet corner and the display could both look cared for.',
        ending_image='When the work was done, {display} gave a gentle twinkle, and {recipient} curled under the blanket looking peaceful at last.',
        requires={"flat", "sparkly"},
        settings={"classroom", "library", "playroom"},
        tags={"comfort", "rest", "kindness"},
    ),
    "bookmark": KindAct(
        id="bookmark",
        need="a shiny bookmark for a worried reader",
        recipient_need="kept peeking at the same page because reading aloud still felt a little scary",
        location="the book nook",
        clue_one="a paper strip tucked under a cushion with a shiny dusting at one end",
        clue_two="a half-finished bookmark on the floor beside a favorite book",
        reveal_line='"I borrowed the {item} to finish a bookmark for {recipient}," {culprit} said. "I thought a brave little marker might make reading time feel friendlier."',
        fix_line='At {repair_spot}, they made {replacement} and laughed softly when the glue stuck to nobody\'s fingers for once.',
        ending_image='After that, {display} had its twinkle back, and {recipient} held the bookmark like a tiny prize.',
        requires={"flat", "sparkly"},
        settings={"library", "playroom"},
        tags={"reading", "care", "kindness"},
    ),
}

APPROACHES = {
    "soft_question": Approach(
        id="soft_question",
        kindness=3,
        ask_line='"{culprit}," {sleuth} said gently, "did you borrow the {item}? If you did, we want to understand."'.replace("{sleuth}", "{culprit}"),
        explain="No one pointed a finger. The question sounded warm enough for the truth to come out.",
        tags={"ask", "kind"},
    ),
    "share_clues": Approach(
        id="share_clues",
        kindness=2,
        ask_line='"{culprit}," {investigator} said softly, "we found clues, but we are not here to scold. Did the {item} go somewhere important?"'.replace("{investigator}", "{culprit}"),
        explain="The words were careful instead of sharp, and that mattered.",
        tags={"ask", "kind"},
    ),
    "circle_help": Approach(
        id="circle_help",
        kindness=3,
        ask_line='"{culprit}," {friend} whispered, "if something happened, we can fix it together. Was it the {item}?"'.replace("{friend}", "{culprit}"),
        explain="The mystery still mattered, but kindness mattered first.",
        tags={"ask", "kind"},
    ),
    "accuse": Approach(
        id="accuse",
        kindness=1,
        ask_line='"You took the {item}, didn\'t you?" {culprit} heard from across the room.'.format(culprit="{culprit}", item="{item}"),
        explain="The words came out too sharp for this storyworld.",
        tags={"harsh"},
    ),
}

TEMPERAMENTS = {
    "open": Temperament(
        id="open",
        openness=2,
        blush="looked surprised",
        tags={"easy"},
    ),
    "shy": Temperament(
        id="shy",
        openness=1,
        blush="went pink in the cheeks",
        tags={"hesitant"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


@dataclass
class StoryParams:
    setting: str
    lost: str
    act: str
    approach: str
    temperament: str
    investigator: str
    investigator_gender: str
    friend: str
    friend_gender: str
    culprit: str
    culprit_gender: str
    recipient: str
    recipient_gender: str
    teacher: str
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


CURATED = [
    StoryParams(
        setting="classroom",
        lost="silver_star",
        act="welcome_card",
        approach="soft_question",
        temperament="open",
        investigator="Lily",
        investigator_gender="girl",
        friend="Ben",
        friend_gender="boy",
        culprit="Mia",
        culprit_gender="girl",
        recipient="Noah",
        recipient_gender="boy",
        teacher="teacher",
    ),
    StoryParams(
        setting="library",
        lost="foil_heart",
        act="quiet_blanket",
        approach="share_clues",
        temperament="shy",
        investigator="Ava",
        investigator_gender="girl",
        friend="Leo",
        friend_gender="boy",
        culprit="Nora",
        culprit_gender="girl",
        recipient="Finn",
        recipient_gender="boy",
        teacher="teacher",
    ),
    StoryParams(
        setting="playroom",
        lost="gold_moon",
        act="bandage_box",
        approach="circle_help",
        temperament="open",
        investigator="Theo",
        investigator_gender="boy",
        friend="Rose",
        friend_gender="girl",
        culprit="Sam",
        culprit_gender="boy",
        recipient="Ella",
        recipient_gender="girl",
        teacher="teacher",
    ),
    StoryParams(
        setting="library",
        lost="silver_star",
        act="bookmark",
        approach="soft_question",
        temperament="shy",
        investigator="Maya",
        investigator_gender="girl",
        friend="Jack",
        friend_gender="boy",
        culprit="Lucy",
        culprit_gender="girl",
        recipient="Owen",
        recipient_gender="boy",
        teacher="teacher",
    ),
    StoryParams(
        setting="classroom",
        lost="foil_heart",
        act="quiet_blanket",
        approach="share_clues",
        temperament="open",
        investigator="Max",
        investigator_gender="boy",
        friend="Anna",
        friend_gender="girl",
        culprit="Zoe",
        culprit_gender="girl",
        recipient="Eli",
        recipient_gender="boy",
        teacher="teacher",
    ),
]


KNOWLEDGE = {
    "mystery": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues point you toward the true answer."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help someone or make them feel better. It can be quiet and gentle, not loud or showy."
        )
    ],
    "welcome": [
        (
            "Why can a welcome card help a new child?",
            "A welcome card shows a new child that other people are glad they are there. That can make a strange place feel friendlier."
        )
    ],
    "comfort": [
        (
            "Why do children sometimes need a quiet corner?",
            "A quiet corner gives someone a calm place to rest when a room feels too busy. A soft, peaceful spot can help big feelings settle down."
        )
    ],
    "care": [
        (
            "Why do people decorate things for someone who is worried or hurt?",
            "A bright little decoration cannot fix everything, but it can show care. Feeling cared for often helps a person feel braver."
        )
    ],
    "reading": [
        (
            "How can a bookmark help during reading time?",
            "A bookmark keeps your place in a book so you can find the page again easily. It can also make reading time feel more special."
        )
    ],
    "craft": [
        (
            "What does tape or glue do in a craft?",
            "Tape and glue hold paper pieces in place so a craft stays together. They help turn loose parts into one finished thing."
        )
    ],
    "injury": [
        (
            "Why might a child want a cheerful bandage box nearby?",
            "When someone has a scrape or sore knee, a cheerful object can make the moment feel less scary. Small comfort can matter a lot."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "kindness", "welcome", "comfort", "care", "reading", "craft", "injury"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    lost = f["lost_cfg"]
    act = f["act"]
    investigator = f["investigator"]
    culprit = f["culprit"]
    recipient = f["recipient"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old where a missing {lost.label} from {setting.display} leads to a kind surprise. Include the word "twinkle".',
        f"Tell a mystery story where {investigator.label} and a friend follow two clues to {culprit.label}, then learn the missing object was borrowed to help {recipient.label}.",
        f'Write a child-facing story in a whodunit style where the answer will amaze the children because the culprit was acting out of kindness, not meanness.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["investigator"]
    friend = f["friend"]
    culprit = f["culprit"]
    recipient = f["recipient"]
    teacher = f["teacher"]
    setting = f["setting"]
    lost = f["lost_cfg"]
    act = f["act"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What mystery did the children try to solve?",
            f"They wanted to find out who had borrowed the {lost.label} from {setting.display}. The empty spot made the room seem less bright, so the mystery mattered right away."
        ),
        (
            f"How did {sleuth.label} and {friend.label} act like detectives?",
            f"They looked for clues instead of blaming someone at once. First they found {act.clue_one}, and then they found {act.clue_two}, which led them toward {act.location}."
        ),
        (
            f"Why did the missing object seem important?",
            f"It was part of {setting.display}, so its absence changed how the place looked. The missing shine took away some twinkle and made everyone notice the gap."
        ),
        (
            f"What did {culprit.label} really do with the {lost.label}?",
            f"{culprit.label} had borrowed it for {act.need}. {culprit.pronoun('subject').capitalize()} was trying to help {recipient.label}, not trying to ruin anything."
        ),
        (
            f"Why was the answer a kindness mystery instead of a stealing mystery?",
            f"The object was taken to comfort or welcome someone, not to keep it selfishly. Once the children learned the reason, the suspicious feeling melted into understanding."
        ),
    ]
    if outcome == "quick":
        qa.append(
            (
                f"How did {sleuth.label}'s kind question change the mystery?",
                f"{sleuth.label} asked gently, so {culprit.label} felt safe enough to tell the truth right away. The soft question solved the case faster because kindness opened the door to honesty."
            )
        )
    else:
        qa.append(
            (
                f"Why did {culprit.label} need extra time to explain?",
                f"{culprit.label} felt shy and worried at first, even though the reason was kind. When {teacher.label_word} waited calmly instead of scolding, {culprit.pronoun('subject')} could finally explain."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They made a replacement for the display together and kept the borrowed piece where it was helping. In the end, {setting.display} twinkled again, and {recipient.label} felt more cared for."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "kindness"} | set(f["act"].tags)
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(setting: Optional[str], lost: Optional[str], act: Optional[str]) -> str:
    if setting and act:
        s = SETTINGS[setting]
        a = KIND_ACTS[act]
        if not setting_supports(s, a):
            return (
                f"(No story: {a.need} does not fit naturally in {s.place}. "
                f"Pick an act the setting can honestly support.)"
            )
    if lost and act:
        l = LOST_THINGS[lost]
        a = KIND_ACTS[act]
        if not item_suits_act(l, a):
            return (
                f"(No story: {l.phrase} does not fit the craft or comfort job in {a.need}. "
                f"The borrowed object must make sense for the kind act.)"
            )
    return "(No valid combination matches the given options.)"


def explain_approach(aid: str) -> str:
    app = APPROACHES[aid]
    return (
        f"(Refusing approach '{aid}': it is too unkind for this storyworld "
        f"(kindness={app.kindness} < {KIND_MIN}). This mystery must be solved with gentle words.)"
    )


ASP_RULES = r"""
usable(L, A) :- lost(L), act(A), requires(A, T), has_tag(L, T).
supported(S, A) :- setting(S), act(A), affords(S, A), act_setting(A, S).
valid(S, L, A) :- supported(S, A), act(A), lost(L), usable(L, A).

kind_approach(P) :- approach(P), kindness(P, K), kind_min(M), K >= M.

reveal(quick) :- chosen_approach(P), chosen_temperament(T),
                 kindness(P, K), openness(T, O), K + O >= 4.
reveal(shy) :- chosen_approach(P), chosen_temperament(T),
               kindness(P, K), openness(T, O), K + O < 4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act_id))
    for lid, lost in LOST_THINGS.items():
        lines.append(asp.fact("lost", lid))
        for tag in sorted(lost.tags):
            lines.append(asp.fact("has_tag", lid, tag))
    for aid, act in KIND_ACTS.items():
        lines.append(asp.fact("act", aid))
        for tag in sorted(act.requires):
            lines.append(asp.fact("requires", aid, tag))
        for sid in sorted(act.settings):
            lines.append(asp.fact("act_setting", aid, sid))
    for pid, app in APPROACHES.items():
        lines.append(asp.fact("approach", pid))
        lines.append(asp.fact("kindness", pid, app.kindness))
    for tid, temp in TEMPERAMENTS.items():
        lines.append(asp.fact("temperament", tid))
        lines.append(asp.fact("openness", tid, temp.openness))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_approaches() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show kind_approach/1."))
    return sorted(p for (p,) in asp.atoms(model, "kind_approach"))


def asp_reveal(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_approach", params.approach),
        asp.fact("chosen_temperament", params.temperament),
    ])
    model = asp.one_model(asp_program(extra, "#show reveal/1."))
    atoms = asp.atoms(model, "reveal")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_kind = {a.id for a in kind_approaches()}
    asp_kind = set(asp_kind_approaches())
    if py_kind == asp_kind:
        print(f"OK: kind approaches match ({sorted(py_kind)}).")
    else:
        rc = 1
        print(f"MISMATCH in kind approaches: clingo={sorted(asp_kind)} python={sorted(py_kind)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_reveal(params) != reveal_outcome(APPROACHES[params.approach], TEMPERAMENTS[params.temperament]):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: reveal outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} reveal outcomes differ.")

    try:
        smoke_params = copy.deepcopy(CURATED[0])
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Kind whodunit storyworld: a missing twinkle, two clues, and a gentle reveal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--act", choices=KIND_ACTS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("--teacher", choices=["teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and kind approaches from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n not in avoid]
    if not options:
        raise StoryError("(No distinct names available for the requested cast.)")
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.approach and APPROACHES[args.approach].kindness < KIND_MIN:
        raise StoryError(explain_approach(args.approach))
    if args.setting and args.act and not setting_supports(SETTINGS[args.setting], KIND_ACTS[args.act]):
        raise StoryError(explain_combo(args.setting, args.lost, args.act))
    if args.lost and args.act and not item_suits_act(LOST_THINGS[args.lost], KIND_ACTS[args.act]):
        raise StoryError(explain_combo(args.setting, args.lost, args.act))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.lost is None or combo[1] == args.lost)
        and (args.act is None or combo[2] == args.act)
    ]
    if not combos:
        raise StoryError(explain_combo(args.setting, args.lost, args.act))

    setting_id, lost_id, act_id = rng.choice(combos)
    approach_id = args.approach or rng.choice(sorted(a.id for a in kind_approaches()))
    temperament_id = args.temperament or rng.choice(sorted(TEMPERAMENTS))
    teacher = args.teacher or "teacher"

    investigator_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    recipient_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    investigator = _pick_name(rng, investigator_gender, used)
    used.add(investigator)
    friend = _pick_name(rng, friend_gender, used)
    used.add(friend)
    culprit = _pick_name(rng, culprit_gender, used)
    used.add(culprit)
    recipient = _pick_name(rng, recipient_gender, used)

    return StoryParams(
        setting=setting_id,
        lost=lost_id,
        act=act_id,
        approach=approach_id,
        temperament=temperament_id,
        investigator=investigator,
        investigator_gender=investigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        recipient=recipient,
        recipient_gender=recipient_gender,
        teacher=teacher,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.lost not in LOST_THINGS:
        raise StoryError(f"(Unknown lost object: {params.lost})")
    if params.act not in KIND_ACTS:
        raise StoryError(f"(Unknown act: {params.act})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    if APPROACHES[params.approach].kindness < KIND_MIN:
        raise StoryError(explain_approach(params.approach))
    if (params.setting, params.lost, params.act) not in set(valid_combos()):
        raise StoryError(explain_combo(params.setting, params.lost, params.act))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)

    world = tell(
        setting=SETTINGS[params.setting],
        lost=LOST_THINGS[params.lost],
        act=KIND_ACTS[params.act],
        approach=APPROACHES[params.approach],
        temperament=TEMPERAMENTS[params.temperament],
        investigator_name=params.investigator,
        investigator_gender=params.investigator_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        recipient_name=params.recipient,
        recipient_gender=params.recipient_gender,
        teacher_type=params.teacher,
    )

    story_text = world.render()
    replacements = {
        "investigator": params.investigator,
        "friend": params.friend,
        "culprit": params.culprit,
        "recipient": params.recipient,
    }
    story_text = story_text.replace(" investigator ", f" {params.investigator} ")
    story_text = story_text.replace(" friend ", f" {params.friend} ")
    story_text = story_text.replace(" culprit ", f" {params.culprit} ")
    story_text = story_text.replace(" recipient ", f" {params.recipient} ")
    for key, value in replacements.items():
        story_text = story_text.replace(f'"{{{key}}}', value)

    story_text = story_text.replace("investigator", params.investigator)
    story_text = story_text.replace("friend", params.friend)
    story_text = story_text.replace("culprit", params.culprit)
    story_text = story_text.replace("recipient", params.recipient)

    sample = StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/3.\n#show kind_approach/1.\n#show reveal/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        apps = asp_kind_approaches()
        print(f"kind approaches: {', '.join(apps)}\n")
        print(f"{len(combos)} valid (setting, lost, act) combos:\n")
        for setting, lost, act in combos:
            print(f"  {setting:10} {lost:12} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(copy.deepcopy(p)) for p in CURATED]
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
            header = f"### {p.investigator} solves the {p.lost} case at {p.setting} ({p.act}, {p.approach}, {p.temperament})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
