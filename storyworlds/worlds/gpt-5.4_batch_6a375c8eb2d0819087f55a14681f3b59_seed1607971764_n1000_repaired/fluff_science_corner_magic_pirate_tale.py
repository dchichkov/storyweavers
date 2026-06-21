#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py
====================================================================

A standalone story world for a tiny child-facing tale in a **science corner**
with **magic**, told in a playful **pirate-tale** style.

Short source tale imagined from the seed
----------------------------------------
Two children turn the science corner into a pirate ship. In a tray there is a
soft pinch of magic fluff used for a class experiment. One child wants to wake
it with a strong gust so it will dance like sea foam and reveal a treasure map.
The other child warns that loose fluff should be watched gently, not blasted.
If the warning fails, the fluff whirls out, clings to a nearby science display,
and the grown-up has to settle it with the right tool. The next day the children
use a sealed viewing jar and a hand lens instead, and the magic stays bright and
calm under glass.

Run it
------
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --fluff moon_fluff --target stool
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --response broom
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/fluff_science_corner_magic_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    clingy: bool = False
    makes_wind: bool = False
    settles_fluff: bool = False
    gives_view: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher_woman", "woman"}
        male = {"boy", "father", "teacher_man", "man"}
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
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    dark_spot: str
    nook_word: str
    role_solo: str
    role_plural: str
    send_off: str
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


@dataclass
class MagicFluff:
    id: str
    label: str
    phrase: str
    color: str
    tray: str
    wake_line: str
    lesson: str
    drift: int = 2
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
class Gust:
    id: str
    cry: str
    label: str
    phrase: str
    where: str
    start: str
    not_for: str
    plural: bool = False
    makes_wind: bool = True
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
class Target:
    id: str
    label: str
    the: str
    near: str
    dresses: str
    spread: int = 2
    clingy: bool = True
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
class SafeView:
    id: str
    label: str
    phrase: str
    glow: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["coated"] < THRESHOLD:
            continue
        sig = ("drift", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mess"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
            kid.memes["wonder"] += 1
        out.append("__fluff__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
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


def hazard_at_risk(gust: Gust, target: Target) -> bool:
    return gust.makes_wind and target.clingy


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fluff_severity(fluff: MagicFluff, target: Target, delay: int) -> int:
    return fluff.drift + target.spread + delay


def is_contained(fluff: MagicFluff, response: Response, target: Target, delay: int) -> bool:
    return response.power >= fluff_severity(fluff, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_escape(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_gust(sim, sim.get(target_id), narrate=False)
    return {
        "mess": sim.get("room").meters["mess"],
        "coated": sim.get(target_id).meters["coated"] >= THRESHOLD,
    }


def _do_gust(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["coated"] += 1
    target.meters["sparkled"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} turned the science corner into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal}!"'
    )


def spot_fluff(world: World, b: Entity, theme: Theme, fluff: MagicFluff, target: Target) -> None:
    world.say(
        f"Near {theme.dark_spot}, {target.dresses}, sat {fluff.tray}. "
        f"Inside it rested {fluff.phrase}, soft as cloud crumbs."
    )
    world.say(
        f'{b.id} leaned close. "Maybe the {fluff.label} will show us the treasure if it wakes," '
        f"{b.pronoun()} whispered."
    )


def tempt(world: World, a: Entity, gust: Gust, fluff: MagicFluff) -> None:
    a.memes["bravado"] += 1
    lit = "eyes lit up at once" if a.memes["bravery"] >= 6 else "eyes lit up"
    world.say(
        f'{a.id}\'s {lit}. "{gust.cry} I saw {gust.phrase} {gust.where}. '
        f'{fluff.wake_line}"'
    )
    world.say("For one bright second, the shortcut sounded wonderfully clever.")


def warn(world: World, b: Entity, a: Entity, gust: Gust, target: Target, helper: Entity) -> None:
    pred = predict_escape(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = (
            f" {b.pronoun().capitalize()} tucked {b.pronoun('possessive')} chin down "
            f"and looked very sure."
        )
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, we are not supposed to use '
        f'{gust.label} on loose experiments. {helper.label_word.capitalize()} said '
        f'that a wild gust can send things flying onto {target.the}."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, gust: Gust) -> None:
    a.memes["defiance"] += 1
    instigator_older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older_sib:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Don\'t be such a scaredy-cat," {a.id} said, and because {a.id} was '
            f'{b.id}\'s {rel}, {b.id} could not stop {a.pronoun("object")} in time. '
            f"Then {a.id} grabbed {gust.label}."
        )
    else:
        world.say(f'"Don\'t be such a scaredy-cat," {a.id} said, and grabbed {gust.label}.')


def back_down(world: World, a: Entity, b: Entity, gust: Gust, helper: Entity, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "big brother" if b.type == "boy" else "big sister"
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said. But {b.id} was {a.pronoun("possessive")} '
        f'{rel}, so {a.id} looked at {b.pronoun("object")}, thought again, and set '
        f'{gust.label} back where it belonged.'
    )
    world.say(
        f'Together they went to tell {helper.label_word} that the {theme.nook_word} needed a calm way '
        f'to wake the magic fluff.'
    )


def release(world: World, target_ent: Entity, gust: Gust, fluff: MagicFluff, target: Target) -> None:
    _do_gust(world, target_ent)
    world.say(
        f"{gust.start} The air rushed across the tray. At first the {fluff.label} only "
        f"shivered, {fluff.color} and soft. Then it leapt up in a glittery puff, sailed past "
        f"{target.near}, and clung to {target.the} in a whirling blanket of fluff."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, helper: Entity) -> None:
    world.say(f'"{a.id}! The fluff! {target.The}!" {b.id} cried.')
    world.say(f'"{helper.label_word.upper()}!"')


def rescue(world: World, helper: Entity, response: Response, target_ent: Entity, target: Target, fluff: MagicFluff, theme: Theme) -> None:
    target_ent.meters["coated"] = 0.0
    world.get("room").meters["mess"] = 0.0
    body = response.text.replace("{target}", target.label).replace("{fluff}", fluff.label)
    world.say(
        f"{helper.label_word.capitalize()} came quickly. In a blink {helper.pronoun()} {body}."
    )
    world.say(
        f"Soon the flying fluff settled down, leaving only a few sparkles in the air and two very quiet "
        f"{theme.role_plural}."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity, gust: Gust, fluff: MagicFluff) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody said anything.")
    world.say(
        f"Then {helper.label_word.capitalize()} knelt beside them. "
        f'"I am glad you called me," {helper.pronoun()} said softly. '
        f'"Magic fluff likes calm hands. {gust.not_for}, because big gusts wake it too fast and send it flying."'
    )
    world.say(f'"We know," whispered {a.id} and {b.id} together.')


def safe_gift(world: World, helper: Entity, a: Entity, b: Entity, theme: Theme, fluff: MagicFluff, v1: SafeView, v2: SafeView) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if world.facts.get("outcome") == "averted":
        lead = "The next day, after everyone talked it through"
    else:
        lead = "The next day, after the science corner was calm again"
    world.say(
        f"{lead}, {helper.label_word} had a surprise. {helper.pronoun().capitalize()} brought them "
        f"{v1.phrase} that {v1.glow}, and {v2.phrase} that {v2.glow}."
    )
    world.say(
        f'"Now," {helper.pronoun()} smiled, "what does {theme.role_solo} use to study {fluff.label} safely?"'
    )
    world.say(f"{a.id} held up the {v2.label}. {b.id} peered through the {v1.label}.")
    world.say('"Calm magic!" they cheered.')
    world.say(
        f"This time, the {theme.role_plural} {theme.send_off}, while the {fluff.label} drifted in tiny circles "
        f"under glass, bright, busy, and safe."
    )


def rescue_fail(world: World, helper: Entity, response: Response, target_ent: Entity, target: Target, fluff: MagicFluff) -> None:
    if "room" in world.entities:
        world.get("room").meters["mess"] += 1
    target_ent.meters["coated"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{target}", target.label).replace("{fluff}", fluff.label)
    world.say(f"{helper.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"But the {fluff.label} had already spread from {target.the} to the magnet tray and the little weather books."
    )


def cleanup_loss(world: World, helper: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"There was no more playing pirate scientists then. {helper.label_word.capitalize()} moved {a.id} and {b.id} "
        f"back from the table and closed the science corner for the rest of the afternoon."
    )
    world.say(
        f"From the rug, they watched the grown-ups lift books, wipe trays, and brush fluff from every shelf."
    )
    world.say(
        f"Their whole little voyage had to stop, and the room that had felt like a ship now looked tired and messy."
    )


def grim_lesson(world: World, helper: Entity, a: Entity, b: Entity, gust: Gust) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} sat with them on the rug and wrapped an arm around both of them. '
        f'"You are safe, and that matters most," {helper.pronoun()} said.'
    )
    world.say(
        f"But {a.id} and {b.id} did not forget the lesson: {gust.not_for.lower()}, and a wild shortcut can scatter a whole room."
    )
    world.say(
        "After that, when an experiment looked exciting, they asked for a calm science tool first."
    )


def tell(
    theme: Theme,
    fluff: MagicFluff,
    gust: Gust,
    target: Target,
    views: tuple[SafeView, SafeView],
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    helper_type: str = "teacher_woman",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the grown-up",
        )
    )
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.add(Entity(id="room", type="room", label="the science corner"))
    tool = world.add(Entity(id="tool", type="tool", label=gust.label, makes_wind=True))
    tgt = world.add(Entity(id="target", type="target", label=target.label, clingy=target.clingy))
    sample = world.add(Entity(id="fluff", type="fluff", label=fluff.label))

    play_setup(world, a, b, theme)
    spot_fluff(world, b, theme, fluff, target)

    world.para()
    tempt(world, a, gust, fluff)
    warn(world, b, a, gust, target, helper)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, gust, helper, theme)
        world.para()
        safe_gift(world, helper, a, b, theme, fluff, views[0], views[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, gust)

        world.para()
        release(world, tgt, gust, fluff, target)
        alarm(world, b, a, target, helper)

        severity = fluff_severity(fluff, target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(fluff, response, target, delay)

        world.para()
        if contained:
            rescue(world, helper, response, tgt, target, fluff, theme)
            lesson(world, helper, a, b, gust, fluff)
            world.para()
            safe_gift(world, helper, a, b, theme, fluff, views[0], views[1])
        else:
            rescue_fail(world, helper, response, tgt, target, fluff)
            cleanup_loss(world, helper, a, b, theme)
            grim_lesson(world, helper, a, b, gust)

    outcome = "averted" if averted else ("contained" if contained else "scattered")
    world.facts.update(
        instigator=a,
        cautioner=b,
        helper=helper,
        theme=theme,
        fluff_cfg=fluff,
        gust=gust,
        target_cfg=target,
        target=tgt,
        tool=tool,
        sample=sample,
        views=views,
        response=response,
        ignited=tgt.meters["sparkled"] >= THRESHOLD,
        outcome=outcome,
        rescued=contained,
        severity=severity,
        delay=delay,
        promised=a.memes["lesson"] >= THRESHOLD,
        relation=relation,
    )
    return world


@dataclass
class StoryParams:
    theme: str = "captain_lab"
    fluff: str = "moon_fluff"
    gust: str = "desk_fan"
    target: str = "chart"
    view1: str = "hand_lens"
    view2: str = "swirl_jar"
    response: str = "glass_dome"
    instigator: str = "Tom"
    instigator_gender: str = "boy"
    cautioner: str = "Lily"
    cautioner_gender: str = "girl"
    helper: str = "teacher_woman"
    trait: str = "careful"
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
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


THEMES = {
    "captain_lab": Theme(
        id="captain_lab",
        scene="a bright little pirate ship in the science corner",
        rig="The low shelf became their deck, the microscope was their brass spyglass, a tray of shells was treasure, and a paper chart showed the stars above their make-believe sea.",
        captain="Captain",
        mate="Navigator",
        goal="the hidden star treasure",
        dark_spot="the back shelf of the science corner",
        nook_word="science nook",
        role_solo="a pirate scientist",
        role_plural="pirate scientists",
        send_off="set sail again around the beakers and books",
    ),
    "storm_lab": Theme(
        id="storm_lab",
        scene="a trim little storm ship in the science corner",
        rig="The weather table became their deck, the magnifier was their spyglass, a box of magnets was treasure, and a chalk map showed where the secret squall might be hiding.",
        captain="Captain",
        mate="Lookout",
        goal="the storm treasure",
        dark_spot="the weather shelf",
        nook_word="science nook",
        role_solo="a storm pirate",
        role_plural="storm pirates",
        send_off="sailed on between the rain gauges and rocks",
    ),
    "specimen_crew": Theme(
        id="specimen_crew",
        scene="a tidy pirate cabin in the science corner",
        rig="The plant shelf became their quarterdeck, the hand lens was their spyglass, little jars were treasure chests, and a crayon map promised a secret island of clues.",
        captain="Captain",
        mate="Scout",
        goal="the clue island",
        dark_spot="the specimen shelf",
        nook_word="science nook",
        role_solo="a clue-seeking pirate",
        role_plural="clue-seeking pirates",
        send_off="marched off on a careful new voyage",
    ),
}

MAGIC_FLUFFS = {
    "moon_fluff": MagicFluff(
        id="moon_fluff",
        label="moon fluff",
        phrase="a pinch of moon fluff",
        color="silver-white",
        tray="a little blue observation tray",
        wake_line="One breeze, and the moon fluff will dance like sea foam.",
        lesson="Moon fluff likes calm hands.",
        drift=2,
        tags={"magic_fluff", "science_corner"},
    ),
    "comet_fluff": MagicFluff(
        id="comet_fluff",
        label="comet fluff",
        phrase="a curl of comet fluff",
        color="pale gold",
        tray="a black star tray",
        wake_line="A quick gust will send the comet fluff racing like a comet tail.",
        lesson="Comet fluff likes calm hands.",
        drift=3,
        tags={"magic_fluff", "science_corner"},
    ),
    "rainbow_fluff": MagicFluff(
        id="rainbow_fluff",
        label="rainbow fluff",
        phrase="a soft puff of rainbow fluff",
        color="pastel-bright",
        tray="a clear sorting tray",
        wake_line="If we whoosh it once, the rainbow fluff will show the whole map.",
        lesson="Rainbow fluff likes calm hands.",
        drift=2,
        tags={"magic_fluff", "science_corner"},
    ),
}

GUSTS = {
    "desk_fan": Gust(
        id="desk_fan",
        cry="The desk fan!",
        label="the desk fan",
        phrase="the little desk fan",
        where="on the helper's table",
        start="Whirr!",
        not_for="Desk fans are not for loose magic fluff",
        plural=False,
        tags={"fan", "wind"},
    ),
    "wand_swish": Gust(
        id="wand_swish",
        cry="My magic wand!",
        label="the wand",
        phrase="the shiny class wand",
        where="in the dress-up bucket",
        start="Swish!",
        not_for="Wands are not for whipping up loose magic fluff",
        plural=False,
        tags={"wand", "magic_fluff"},
    ),
    "dragon_breath": Gust(
        id="dragon_breath",
        cry="Dragon breath!",
        label="dragon breath",
        phrase="our biggest pretend dragon breath",
        where="right here",
        start="Whooo!",
        not_for="Big blowing games are not for loose magic fluff",
        plural=False,
        tags={"wind", "breathing"},
    ),
}

TARGETS = {
    "chart": Target(
        id="chart",
        label="paper star chart",
        the="the paper star chart",
        near="the hanging chart",
        dresses="a paper star chart curled at the edge",
        spread=2,
        clingy=True,
        tags={"chart", "paper"},
    ),
    "felt_board": Target(
        id="felt_board",
        label="felt planet board",
        the="the felt planet board",
        near="the felt planets",
        dresses="a felt planet board dotted with tiny stitched stars",
        spread=3,
        clingy=True,
        tags={"felt", "science_corner"},
    ),
    "wool_mitten": Target(
        id="wool_mitten",
        label="wool mitten for cold-weather experiments",
        the="the wool mitten",
        near="the mitten hanging by the weather tools",
        dresses="a wool mitten waiting beside the weather tools",
        spread=2,
        clingy=True,
        tags={"wool", "science_corner"},
    ),
    "stool": Target(
        id="stool",
        label="metal stool",
        the="the metal stool",
        near="the shiny stool leg",
        dresses="a smooth metal stool tucked under the table",
        spread=0,
        clingy=False,
        tags={"metal"},
    ),
}

SAFE_VIEWS = {
    "hand_lens": SafeView(
        id="hand_lens",
        label="hand lens",
        phrase="a hand lens",
        glow="made every sparkle look as big as a tiny moon",
        tags={"magnifier"},
    ),
    "swirl_jar": SafeView(
        id="swirl_jar",
        label="swirl jar",
        phrase="a sealed swirl jar",
        glow="held the fluff under a clear lid while it turned in slow circles",
        tags={"jar"},
    ),
    "light_box": SafeView(
        id="light_box",
        label="light box",
        phrase="a little light box",
        glow="lit the fluff from below with a soft blue glow",
        tags={"light_box"},
    ),
    "scope_card": SafeView(
        id="scope_card",
        label="viewing card",
        phrase="a viewing card with a round window",
        glow="let them watch one calm sparkle at a time",
        tags={"viewer"},
    ),
}

RESPONSES = {
    "glass_dome": Response(
        id="glass_dome",
        sense=3,
        power=6,
        text="slipped a clear glass dome over the {target} and gently guided the {fluff} back into its tray",
        fail="tried to cover the {target} with the dome, but the {fluff} had already drifted too far to gather quickly",
        qa_text="covered the mess with a glass dome and guided the fluff back into the tray",
        tags={"dome", "science_corner"},
    ),
    "fine_mist": Response(
        id="fine_mist",
        sense=3,
        power=5,
        text="used a fine mist bottle to settle the {fluff}, then lifted it away from the {target} with calm, slow hands",
        fail="sprayed a fine mist, but the {fluff} was already swirling through too much of the room",
        qa_text="used a fine mist bottle to settle the fluff and lift it away",
        tags={"mist", "science_corner"},
    ),
    "soft_net": Response(
        id="soft_net",
        sense=2,
        power=4,
        text="caught the biggest drifting puffs in a soft specimen net and eased them back into the tray",
        fail="scooped with the specimen net, but too much fluff had already scattered across the shelves",
        qa_text="caught the drifting fluff in a soft specimen net and returned it",
        tags={"net", "science_corner"},
    ),
    "broom": Response(
        id="broom",
        sense=1,
        power=1,
        text="swept at the {fluff} with a little broom until it gathered in a corner",
        fail="swept at the {fluff}, but the broom only pushed it into more flying clouds",
        qa_text="swept at the fluff with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "clever", "cautious", "steady", "sensible"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for fluff_id in MAGIC_FLUFFS:
            for gust_id, gust in GUSTS.items():
                for target_id, target in TARGETS.items():
                    if hazard_at_risk(gust, target):
                        combos.append((theme_id, fluff_id, gust_id, target_id))
    return combos


KNOWLEDGE = {
    "magic_fluff": [
        (
            "What is magic fluff?",
            "Magic fluff is a pretend-story experiment material that floats and shimmers when air wakes it. In this world, it must be handled gently so it does not scatter."
        )
    ],
    "science_corner": [
        (
            "What is a science corner?",
            "A science corner is a small classroom place for looking closely at shells, rocks, plants, magnets, and simple experiments. Children use careful tools there so they can observe without making a big mess."
        )
    ],
    "fan": [
        (
            "Why can a fan make loose things fly away?",
            "A fan pushes moving air. Light things like fluff or paper can get picked up by that air and blown somewhere else very quickly."
        )
    ],
    "wand": [
        (
            "Why is a pretend wand not a good tool for a real experiment?",
            "A pretend wand is for play, not for careful measuring or handling. Real experiments need calm hands and the right tool for the job."
        )
    ],
    "wind": [
        (
            "What does a strong gust do to light fluff?",
            "A strong gust can lift light fluff and carry it around the room. That is why gentle handling matters."
        )
    ],
    "paper": [
        (
            "Why does fluff stick to paper and felt so easily?",
            "Light fluff catches on rough or fuzzy surfaces more easily than on smooth ones. Paper edges and felt fibers can hold onto it."
        )
    ],
    "felt": [
        (
            "What is felt?",
            "Felt is a soft cloth made from pressed fibers. Because it is fuzzy, tiny bits of fluff can cling to it."
        )
    ],
    "dome": [
        (
            "What does a glass dome do in a science activity?",
            "A glass dome covers something so it stays in one place while you look at it. It helps keep light materials from drifting away."
        )
    ],
    "mist": [
        (
            "Why can a fine mist help floating fluff settle?",
            "A fine mist adds tiny drops of water that make the fluff a little heavier. When it is heavier, it does not fly around as easily."
        )
    ],
    "net": [
        (
            "What is a specimen net for?",
            "A specimen net is a soft net used to catch or move delicate things gently. It is better than grabbing with rough hands."
        )
    ],
    "magnifier": [
        (
            "What does a hand lens do?",
            "A hand lens makes small things look bigger so you can see details. It helps you observe carefully instead of touching too much."
        )
    ],
    "jar": [
        (
            "Why is a sealed jar useful for watching something float?",
            "A sealed jar keeps the floating thing inside while still letting you see it. That means you can watch safely without scattering it."
        )
    ],
    "light_box": [
        (
            "What is a light box?",
            "A light box shines light up through something so you can see shapes and colors clearly. It helps you look carefully without making wind or touching."
        )
    ],
    "viewer": [
        (
            "What is a viewing card?",
            "A viewing card is a simple card with a small window that helps you focus on one part of something at a time. It slows you down and helps careful looking."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "magic_fluff",
    "science_corner",
    "fan",
    "wand",
    "wind",
    "paper",
    "felt",
    "dome",
    "mist",
    "net",
    "magnifier",
    "jar",
    "light_box",
    "viewer",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    gust = f["gust"]
    fluff = f["fluff_cfg"]
    theme = f["theme"]
    target = f["target_cfg"]
    v1, v2 = f["views"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-tale-style story for a 3-to-5-year-old set in a science corner, with magic fluff and the word "fluff".'
    )
    if outcome == "averted":
        sib = "brother" if b.type == "boy" else "sister"
        return [
            base,
            f"Tell a near-miss story where {a.id} wants to use {gust.label} to wake {fluff.label}, but listens to {b.id}, {a.pronoun('possessive')} older {sib}, before the fluff escapes.",
            f"Write a gentle science-corner story where pirate play stays magical because the children choose {v1.phrase} and {v2.phrase} instead of a wild gust.",
        ]
    if outcome == "scattered":
        return [
            base,
            f"Tell a cautionary story where {a.id} ignores the warning, uses {gust.label}, and the {fluff.label} spreads from {target.the} through the science corner until the whole game has to stop.",
            f"Write a story with a sad but safe ending that teaches children to use calm science tools instead of wild shortcuts.",
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {a.id} uses {gust.label} on {fluff.label}, the fluff flies onto {target.the}, and a calm grown-up settles it with the right tool.",
        f"Write a simple magic story that ends with children studying {fluff.label} safely using {v1.phrase} and {v2.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    theme = f["theme"]
    fluff = f["fluff_cfg"]
    gust = f["gust"]
    target = f["target_cfg"]
    response = f["response"]
    v1, v2 = f["views"]
    pair = pair_noun(a, b, f["relation"])
    hw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing {theme.role_plural} in the science corner. A grown-up came to help when the magic fluff became a problem."
        ),
        (
            "Where does the story happen?",
            f"It happens in the science corner, which the children turned into {theme.scene}. The shelves and tools became part of their pirate game."
        ),
        (
            "What did the children find?",
            f"They found {fluff.phrase} in a tray. It looked soft and magical, so they hoped it might help them find {theme.goal}."
        ),
        (
            f"What did {a.id} want to use, and why did {b.id} warn against it?",
            f"{a.id} wanted to use {gust.label} to wake the {fluff.label}. {b.id} warned that a wild gust could send the fluff flying onto {target.the}, because loose experiments need calm tools."
        ),
    ]
    if f.get("outcome") == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} stopped and put {gust.label} back. Because {b.id} was older and sounded sure, the warning finally mattered more than the exciting shortcut."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely. The children studied the {fluff.label} with {v1.phrase} and {v2.phrase}, so the magic stayed calm and nothing scattered."
            )
        )
    elif f.get("outcome") == "contained":
        body = response.qa_text.replace("{target}", target.label).replace("{fluff}", fluff.label)
        qa.append(
            (
                "What happened when the gust hit the fluff?",
                f"The {fluff.label} burst up from the tray and clung to {target.the}. The trouble started because a strong gust moved something light and loose too quickly."
            )
        )
        qa.append(
            (
                f"How did the {hw} fix the problem?",
                f"The {hw} {body}. That worked because the response was calm and matched the kind of mess the children had made."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that magic experiments need gentle tools. The ending proves it, because they later used {v1.phrase} and {v2.phrase} instead of another gust."
            )
        )
    else:
        fail = response.fail.replace("{target}", target.label).replace("{fluff}", fluff.label)
        qa.append(
            (
                f"Could the {hw} stop the mess right away?",
                f"No. The {hw} {fail}. By then the fluff had already spread beyond {target.the}, so the science corner had to close for cleanup."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The children were safe, but their game had to stop while the room was cleaned. That sad ending shows how one wild shortcut can spoil the whole adventure."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned not to use {gust.label} on loose magic fluff. Later they knew to ask for a careful science tool first, because the mess had shown them why calm handling matters."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["fluff_cfg"].tags) | set(f["gust"].tags) | set(f["target_cfg"].tags)
    if f["outcome"] == "contained":
        tags |= set(f["response"].tags)
        for v in f["views"]:
            tags |= set(v.tags)
    elif f["outcome"] == "averted":
        for v in f["views"]:
            tags |= set(v.tags)
    else:
        tags |= set(f["response"].tags)
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
        flags = [n for n, on in (("clingy", e.clingy), ("makes_wind", e.makes_wind), ("settles_fluff", e.settles_fluff), ("gives_view", e.gives_view)) if on]
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="captain_lab",
        fluff="moon_fluff",
        gust="desk_fan",
        target="chart",
        view1="hand_lens",
        view2="swirl_jar",
        response="glass_dome",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="teacher_woman",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=8,
    ),
    StoryParams(
        theme="storm_lab",
        fluff="comet_fluff",
        gust="wand_swish",
        target="felt_board",
        view1="light_box",
        view2="scope_card",
        response="fine_mist",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="teacher_man",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        theme="specimen_crew",
        fluff="comet_fluff",
        gust="dragon_breath",
        target="felt_board",
        view1="hand_lens",
        view2="swirl_jar",
        response="soft_net",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        helper="teacher_woman",
        trait="cautious",
        delay=2,
        instigator_age=6,
        cautioner_age=4,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        theme="captain_lab",
        fluff="rainbow_fluff",
        gust="wand_swish",
        target="wool_mitten",
        view1="scope_card",
        view2="swirl_jar",
        response="soft_net",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        helper="teacher_woman",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(gust: Gust, target: Target) -> str:
    if not target.clingy:
        return (
            f"(No story: {gust.label} can blow loose fluff around, but {target.the} is smooth and does not really catch it. "
            f"That would make only a weak, short-lived mess, so choose a clingy target like the chart or felt board.)"
        )
    if not gust.makes_wind:
        return f"(No story: {gust.label} makes no gust, so the fluff would not burst free.)"
    return "(No story: this combination does not create a believable fluff escape.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try a calmer, more suitable response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(MAGIC_FLUFFS[params.fluff], RESPONSES[params.response], TARGETS[params.target], params.delay) else "scattered"


ASP_RULES = r"""
hazard(G, Tg) :- makes_wind(G), clingy(Tg).
sensible(R)   :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, G, Tg) :- theme(T), fluff(F), gust(G), target(Tg), hazard(G, Tg).

cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Df + Sp + Dl) :- chosen_fluff(F), drift(F, Df), chosen_target(Tg), spread(Tg, Sp), delay(Dl).
resp_power(P)          :- chosen_response(R), power(R, P).
contained              :- resp_power(P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(scattered) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in MAGIC_FLUFFS.items():
        lines.append(asp.fact("fluff", fid))
        lines.append(asp.fact("drift", fid, f.drift))
    for gid, g in GUSTS.items():
        lines.append(asp.fact("gust", gid))
        if g.makes_wind:
            lines.append(asp.fact("makes_wind", gid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.clingy:
            lines.append(asp.fact("clingy", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for vid in SAFE_VIEWS:
        lines.append(asp.fact("view", vid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_fluff", params.fluff),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(120):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(777))
        smoke_params.seed = 777
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke-test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play in a science corner, magic fluff, and the right tool for calm observation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--fluff", choices=MAGIC_FLUFFS)
    ap.add_argument("--gust", choices=GUSTS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["teacher_woman", "teacher_man", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the fluff swirls before the grown-up reaches it")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].clingy:
        gust = GUSTS[args.gust] if args.gust else next(iter(GUSTS.values()))
        raise StoryError(explain_rejection(gust, TARGETS[args.target]))
    if args.gust and args.target:
        gust = GUSTS[args.gust]
        target = TARGETS[args.target]
        if not hazard_at_risk(gust, target):
            raise StoryError(explain_rejection(gust, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.fluff is None or c[1] == args.fluff)
        and (args.gust is None or c[2] == args.gust)
        and (args.target is None or c[3] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, fluff, gust, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    view1, view2 = rng.sample(sorted(SAFE_VIEWS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    helper = args.helper or rng.choice(["teacher_woman", "teacher_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme,
        fluff=fluff,
        gust=gust,
        target=target,
        view1=view1,
        view2=view2,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        helper=helper,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.fluff not in MAGIC_FLUFFS:
        raise StoryError(f"(Unknown fluff: {params.fluff})")
    if params.gust not in GUSTS:
        raise StoryError(f"(Unknown gust: {params.gust})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.view1 not in SAFE_VIEWS or params.view2 not in SAFE_VIEWS:
        raise StoryError("(Unknown safe viewing tool.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response in RESPONSES and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(GUSTS[params.gust], TARGETS[params.target]):
        raise StoryError(explain_rejection(GUSTS[params.gust], TARGETS[params.target]))
    if params.helper not in {"teacher_woman", "teacher_man", "mother", "father"}:
        raise StoryError(f"(Unknown helper: {params.helper})")

    world = tell(
        theme=THEMES[params.theme],
        fluff=MAGIC_FLUFFS[params.fluff],
        gust=GUSTS[params.gust],
        target=TARGETS[params.target],
        views=(SAFE_VIEWS[params.view1], SAFE_VIEWS[params.view2]),
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        helper_type=params.helper,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, fluff, gust, target) combos:\n")
        for theme, fluff, gust, target in combos:
            print(f"  {theme:14} {fluff:13} {gust:13} {target}")
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
                f"### {p.instigator} & {p.cautioner}: {p.fluff} with {p.gust} near {p.target} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
