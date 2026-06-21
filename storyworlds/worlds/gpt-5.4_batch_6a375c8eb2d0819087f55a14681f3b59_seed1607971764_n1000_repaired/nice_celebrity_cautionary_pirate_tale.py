#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py
===================================================================

A standalone story world for a cautionary pirate-style tale about children who
want to impress a nice celebrity pirate with a banner, try an unsafe shortcut,
and learn a safer way to reach high places.

The domain is intentionally small and constraint-checked:
- the children are pretending to be pirates,
- a nice celebrity pirate from the harbor festival matters to their goal,
- one child wants to climb something wobbly to hang a banner too high,
- the other child may avert the risk, or fail to stop it,
- a grown-up then solves the problem with a safer method if that method
  genuinely fits the height of the chosen spot.

Run it
------
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py --spot mast_shelf
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py --spot low_chest
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py --fix hop_again
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nice_celebrity_cautionary_pirate_tale.py --verify
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
BOLDNESS_INIT = 6.0
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
    unstable: bool = False
    support_level: int = 0
    height_level: int = 0
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
    titles: tuple[str, str]
    quest: str
    send_off: str
    role_plural: str
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
class Celebrity:
    id: str
    name: str
    title: str
    nice_deed: str
    event: str
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
    wobble_word: str
    risk: int
    unstable: bool = True
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
class Spot:
    id: str
    label: str
    phrase: str
    height: int
    high: bool
    view_text: str
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
class Fix:
    id: str
    sense: int
    power: int
    label: str
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
        return [e for e in self.entities.values() if e.role in {"climber", "warning"}]

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
    climber = world.get("climber")
    perch = world.get("perch")
    spot = world.get("spot")
    banner = world.get("banner")
    if climber.meters["climbing"] < THRESHOLD:
        return out
    if not perch.unstable or spot.height_level < 2:
        return out
    sig = ("wobble", perch.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    climber.memes["fear"] += 1
    out.append("__wobble__")
    if banner.meters["raised"] >= THRESHOLD:
        banner.meters["crooked"] += 1
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    climber = world.get("climber")
    perch = world.get("perch")
    banner = world.get("banner")
    if perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("fall", climber.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    climber.meters["bumped"] += 1
    climber.meters["fallen"] += 1
    banner.meters["torn"] += 1
    banner.meters["hung"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] += 1
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
        for s in produced:
            world.say(s)
    return produced


def needs_risky_reach(perch: Perch, spot: Spot) -> bool:
    return perch.unstable and spot.high and spot.height >= 2


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def repair_severity(perch: Perch, spot: Spot, delay: int) -> int:
    return perch.risk + spot.height + delay


def can_finish(fix: Fix, perch: Perch, spot: Spot, delay: int) -> bool:
    return fix.power >= repair_severity(perch, spot, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, climber_age: int, warning_age: int, trait: str) -> bool:
    older = relation == "siblings" and warning_age > climber_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > BOLDNESS_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    _do_climb(sim, narrate=False)
    return {
        "will_fall": sim.get("climber").meters["fallen"] >= THRESHOLD,
        "banner_torn": sim.get("banner").meters["torn"] >= THRESHOLD,
    }


def _do_climb(world: World, narrate: bool = True) -> None:
    climber = world.get("climber")
    banner = world.get("banner")
    climber.meters["climbing"] += 1
    banner.meters["raised"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, celebrity: Celebrity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    first, second = theme.titles
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{first} {a.id} and {second} {b.id}!" {a.id} cried. "{theme.quest}!"'
    )
    world.say(
        f"Tomorrow, {celebrity.title} {celebrity.name}, a nice celebrity from {celebrity.event}, "
        f"was coming by, and the children wanted their pirate room to look extra grand."
    )


def plan_banner(world: World, b: Entity, spot: Spot, celebrity: Celebrity) -> None:
    banner = world.get("banner")
    world.say(
        f"They had painted {banner.label}, with gold swirls and a smiling skull, "
        f"because {celebrity.title} {celebrity.name} always {celebrity.nice_deed}."
    )
    world.say(
        f"{b.id} pointed to {spot.phrase}. \"If we hang it there, {spot.view_text},\" "
        f"{b.pronoun()} said."
    )


def tempt(world: World, a: Entity, perch: Perch) -> None:
    a.memes["pride"] += 1
    world.say(
        f'{a.id} looked at {world.get("perch").phrase} and grinned. "I can climb {perch.phrase} '
        f"and put it up myself."
    )
    world.say("For one shiny moment, the shortcut felt fast and clever.")


def warn(world: World, b: Entity, a: Entity, perch: Perch, parent: Entity) -> None:
    pred = predict_slip(world)
    b.memes["caution"] += 1
    world.facts["predicted_fall"] = pred["will_fall"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} held the banner tight and did not smile."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, {perch.label} can {perch.wobble_word}. '
        f"{parent.label_word.capitalize()} says chairs and stacks are not ladders.\"{extra}"
    )


def defy(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_sib:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"I will be quick," {a.id} said, and because {a.id} was {b.pronoun("possessive")} '
            f'{rel}, {b.id} could not stop {a.pronoun("object")}. Then {a.id} stepped onto '
            f"{perch.phrase}."
        )
    else:
        world.say(f'"I will be quick," {a.id} said, and stepped onto {perch.phrase}.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, then at the wobbly perch, and the brave grin slid away. '
        f'"You are right," {a.pronoun()} said. "Let\'s ask {parent.label_word} instead."'
    )
    world.say("They laid the banner flat on the rug so no one would try the shortcut again.")


def slip(world: World, a: Entity, perch: Perch, spot: Spot) -> None:
    _do_climb(world, narrate=False)
    world.say(
        f"{a.id} stretched up toward {spot.phrase}. Then {perch.phrase} gave a sudden {perch.wobble_word}. "
        f"{a.id}'s foot slid, the banner fluttered sideways, and down {a.pronoun()} came with a thump."
    )
    if world.get("banner").meters["torn"] >= THRESHOLD:
        world.say("A corner of the pirate banner ripped with a sad rrip.")
    if a.meters["bumped"] >= THRESHOLD:
        world.say(
            f"{a.id} was not badly hurt, but {a.pronoun('possessive')} knee stung and "
            f"{a.pronoun()} looked shocked."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} called. "The chair slipped!"')


def comfort(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came quickly, checked {a.id}'s knee, and hugged both children. "
        f'"I am glad you called me right away," {parent.pronoun()} said.'
    )


def safe_finish(world: World, parent: Entity, fix: Fix, spot: Spot, celebrity: Celebrity) -> None:
    banner = world.get("banner")
    banner.meters["hung"] += 1
    banner.meters["torn"] = 0.0
    world.say(
        f"Then {parent.label_word.capitalize()} {fix.text.replace('{spot}', spot.label)}."
    )
    world.say(
        f"Soon the banner was straight and proud, ready for {celebrity.title} {celebrity.name} to see."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, perch: Perch) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["safety"] += 1
    world.say(
        f'"Remember this," {parent.label_word.capitalize()} said softly. "{perch.label.capitalize()} is for '
        f"sitting or rolling, not for climbing high. When something is above your reach, ask for safe help."
    )
    world.say(f'"We will," whispered {a.id} and {b.id} together.')


def ending_visit(world: World, a: Entity, b: Entity, celebrity: Celebrity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"The next day, {celebrity.title} {celebrity.name} saw the room, smiled at the neat pirate banner, "
        f"and thanked them for making such a cheerful ship."
    )
    world.say(
        f"After that, whenever the crew needed to reach something high, the {theme.role_plural} stopped, "
        f"looked for safe help first, and {theme.send_off}."
    )


def failed_finish(world: World, parent: Entity, fix: Fix, spot: Spot, celebrity: Celebrity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} {fix.fail.replace('{spot}', spot.label)}."
    )
    world.say(
        f"The banner stayed crooked on the rug, and there was no time to hang it before {celebrity.title} "
        f"{celebrity.name} arrived."
    )


def disappointed_lesson(world: World, parent: Entity, a: Entity, b: Entity, perch: Perch,
                        celebrity: Celebrity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"When {celebrity.title} {celebrity.name} came, {parent.label_word} showed the torn banner and told the truth."
    )
    world.say(
        f"{celebrity.name} was still kind. \"A safe pirate is the best pirate,\" {celebrity.pronoun if False else 'the celebrity'} smiled."
    )
    world.say(
        f"{a.id} and {b.id} felt small and sorry, but they never forgot the lesson: {perch.label} is not a ladder, "
        f"and shortcuts can spoil the very thing you hoped to show."
    )
@dataclass
class StoryParams:
    theme: str
    celebrity: str
    perch: str
    spot: str
    fix: str
    climber: str
    climber_gender: str
    warning: str
    warning_gender: str
    parent: str
    trait: str
    delay: int = 0
    climber_age: int = 6
    warning_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "celebrity": [
        (
            "What is a celebrity?",
            "A celebrity is a person many people know about, like a singer, actor, or parade captain. Even if someone is famous, they still want children to be safe.",
        )
    ],
    "chair": [
        (
            "Why can a rolling chair be unsafe to climb on?",
            "A rolling chair can move when your foot presses on it. That means it can slide away before you are ready.",
        )
    ],
    "stack": [
        (
            "Why is a stack of cushions not a good ladder?",
            "Cushions are soft and squishy, so they sink and wobble under your feet. That makes it easy to lose your balance.",
        )
    ],
    "climb": [
        (
            "What should you do if something is too high to reach?",
            "Stop and ask a grown-up for help or use a safe step stool with help. A fast shortcut can turn into a fall.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool is a small sturdy stool that helps you reach a little higher. It works best when a grown-up keeps it steady.",
        )
    ],
    "help": [
        (
            "Why is grown-up help safer for high places?",
            "Grown-ups are taller and steadier, and they know how to move carefully. That makes reaching high places much safer.",
        )
    ],
    "safe_choice": [
        (
            "Is it okay to put something lower instead of higher?",
            "Yes. A safe place is better than a risky place. The best spot for a decoration is the one you can use safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["celebrity", "chair", "stack", "climb", "stool", "help", "safe_choice"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme in THEMES:
        for celeb in CELEBRITIES:
            for perch_id, perch in PERCHES.items():
                for spot_id, spot in SPOTS.items():
                    if not needs_risky_reach(perch, spot):
                        continue
                    combos.append((theme, celeb, perch_id, spot_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["climber"]
    b = f["warning"]
    celeb = f["celebrity"]
    perch = f["perch_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style cautionary story for a 3-to-5-year-old that includes the words "nice" '
        f'and "celebrity". Two children want to impress a nice celebrity pirate by hanging a banner '
        f'on {spot.label}, and one child tries to climb a {perch.label}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {a.id} wants the shortcut, but {b.id}, an older sibling, stops it before anyone falls.",
            f"Write a story where the children learn to ask for safe help before reaching high places, and the ending shows the celebrity smiling at their safe pirate room.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a cautionary story where {a.id} slips while trying to hang the banner, but a calm grown-up helps fix the problem safely.",
            f"Write a pirate-room story that begins with excitement, turns scary for a moment, and ends with a clear lesson that chairs and wobbly stacks are not ladders.",
        ]
    return [
        base,
        f"Tell a sadder cautionary pirate tale where the shortcut rips the banner, and the children learn that unsafe choices can spoil what they hoped to show the celebrity.",
        f"Write a story where the grown-up is kind, the celebrity is still nice, and the ending teaches that a safe plan matters more than showing off.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["climber"]
    b = f["warning"]
    parent = f["parent"]
    celeb = f["celebrity"]
    perch = f["perch_cfg"]
    spot = f["spot_cfg"]
    fix = f["fix"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing pirates at home. They were excited because {celeb.title} {celeb.name}, a nice celebrity pirate, was coming soon.",
        ),
        (
            "What did the children want to do?",
            f"They wanted to hang a pirate banner on {spot.label} so the room would look grand. They hoped the banner would impress {celeb.title} {celeb.name}.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because a {perch.label} can {perch.wobble_word}. That made the shortcut dangerous, especially with the banner held high over the floor.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and backed down before climbing. Because they stopped in time, nobody fell and the banner stayed safe.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The grown-up helped hang the banner safely, and the nice celebrity smiled when they saw it. The ending shows that the children changed because they asked for safe help first.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} tried the shortcut?",
                f"{a.id} slipped when the {perch.label} moved, and the banner tore. {a.id} was not badly hurt, but the scary moment proved the warning had been right.",
            )
        )
        qa.append(
            (
                f"How did {pw} solve the problem?",
                f"{pw.capitalize()} {fix.qa_text}. The calm fix worked because it was safer and strong enough for the high place they had chosen.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that a {perch.label} is not a ladder and that asking for help is the brave choice. The story ends happily because they used a safer method after the mistake.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the banner not get hung in time?",
                f"The shortcut made {a.id} slip and tore the banner first. After that, there was not enough time or support to finish hanging it before the celebrity arrived.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children feeling sorry, even though the grown-up and the celebrity stayed kind. The ending is cautionary because the unsafe shortcut spoiled the decoration they cared about.",
            )
        )
        qa.append(
            (
                "What lesson did they keep?",
                f"They kept the lesson that high places need safe help, not showing off. That mattered because one risky choice changed the whole day.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["celebrity"].tags) | set(f["perch_cfg"].tags)
    outcome = f["outcome"]
    if outcome in {"averted", "contained"}:
        tags |= set(f["fix"].tags)
    else:
        tags |= {"climb"}
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
        if e.unstable:
            bits.append("unstable=True")
        if e.support_level:
            bits.append(f"support={e.support_level}")
        if e.height_level:
            bits.append(f"height={e.height_level}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="parlor_ship",
        celebrity="starling",
        perch="rolling_chair",
        spot="door_hook",
        fix="grownup_arms",
        climber="Tom",
        climber_gender="boy",
        warning="Lily",
        warning_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        climber_age=6,
        warning_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="reef_hideout",
        celebrity="pearl",
        perch="cushion_stack",
        spot="bookcase_corner",
        fix="step_stool",
        climber="Mia",
        climber_gender="girl",
        warning="Ben",
        warning_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        climber_age=5,
        warning_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="harbor_deck",
        celebrity="marigold",
        perch="rolling_chair",
        spot="mast_shelf",
        fix="lower_spot",
        climber="Sam",
        climber_gender="boy",
        warning="Zoe",
        warning_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        climber_age=6,
        warning_age=4,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="parlor_ship",
        celebrity="pearl",
        perch="toy_chest",
        spot="door_hook",
        fix="step_stool",
        climber="Ava",
        climber_gender="girl",
        warning="Noah",
        warning_gender="boy",
        parent="father",
        trait="sensible",
        delay=0,
        climber_age=6,
        warning_age=5,
        relation="friends",
        trust=6,
    ),
    StoryParams(
        theme="reef_hideout",
        celebrity="starling",
        perch="rolling_chair",
        spot="mast_shelf",
        fix="grownup_arms",
        climber="Leo",
        climber_gender="boy",
        warning="Nora",
        warning_gender="girl",
        parent="mother",
        trait="steady",
        delay=1,
        climber_age=7,
        warning_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(perch: Perch, spot: Spot) -> str:
    if not spot.high:
        return (
            f"(No story: {spot.label} is low enough already, so no one needs a dangerous climb. "
            f"Pick a genuinely high place like a door hook or top shelf.)"
        )
    if not perch.unstable:
        return (
            f"(No story: {perch.label} is not modeled as an unsafe shortcut here.)"
        )
    return "(No story: this combination does not create a real reaching hazard.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of these safer fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.climber_age, params.warning_age, params.trait):
        return "averted"
    if can_finish(FIXES[params.fix], PERCHES[params.perch], SPOTS[params.spot], params.delay):
        return "contained"
    return "disappointed"


ASP_RULES = r"""
hazard(P, S) :- perch(P), unstable(P), spot(S), high(S), height(S, H), H >= 2.
sensible(F) :- fix(F), sense(F, X), sense_min(M), X >= M.
valid(T, C, P, S) :- theme(T), celebrity(C), hazard(P, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
warning_older :- relation(siblings), climber_age(CA), warning_age(WA), WA > CA.
bonus(4) :- warning_older.
bonus(0) :- not warning_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- warning_older, authority(A), boldness_init(BI), A > BI.

severity(R + H + D) :- chosen_perch(P), chosen_spot(S), risk(P, R), height(S, H), delay(D).
fix_power(PW) :- chosen_fix(F), power(F, PW).
contained :- fix_power(PW), severity(SV), PW >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(disappointed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid in CELEBRITIES:
        lines.append(asp.fact("celebrity", cid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        if perch.unstable:
            lines.append(asp.fact("unstable", pid))
        lines.append(asp.fact("risk", pid, perch.risk))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.high:
            lines.append(asp.fact("high", sid))
        lines.append(asp.fact("height", sid, spot.height))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("climber_age", params.climber_age),
            asp.fact("warning_age", params.warning_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens = set(asp_sensible())
    psens = {f.id for f in sensible_fixes()}
    if csens == psens:
        print(f"OK: sensible fixes match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(csens)} python={sorted(psens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cautionary pirate room tale about a nice celebrity, an unsafe climb, and a safer fix."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--celebrity", choices=CELEBRITIES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra trouble after the slip; higher makes some fixes too weak")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot:
        probe_perch = PERCHES[args.perch] if args.perch else next(iter(PERCHES.values()))
        if not needs_risky_reach(probe_perch, SPOTS[args.spot]):
            raise StoryError(explain_rejection(probe_perch, SPOTS[args.spot]))
    if args.perch and args.spot:
        perch = PERCHES[args.perch]
        spot = SPOTS[args.spot]
        if not needs_risky_reach(perch, spot):
            raise StoryError(explain_rejection(perch, spot))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.celebrity is None or c[1] == args.celebrity)
        and (args.perch is None or c[2] == args.perch)
        and (args.spot is None or c[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, celebrity, perch, spot = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    climber, climber_gender = _pick_child(rng)
    warning, warning_gender = _pick_child(rng, avoid=climber)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    climber_age, warning_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme,
        celebrity=celebrity,
        perch=perch,
        spot=spot,
        fix=fix,
        climber=climber,
        climber_gender=climber_gender,
        warning=warning,
        warning_gender=warning_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        climber_age=climber_age,
        warning_age=warning_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.celebrity not in CELEBRITIES:
        raise StoryError(f"(Invalid celebrity: {params.celebrity})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Invalid perch: {params.perch})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not needs_risky_reach(PERCHES[params.perch], SPOTS[params.spot]):
        raise StoryError(explain_rejection(PERCHES[params.perch], SPOTS[params.spot]))

    world = tell(
        theme=THEMES[params.theme],
        celebrity=CELEBRITIES[params.celebrity],
        perch=PERCHES[params.perch],
        spot=SPOTS[params.spot],
        fix=FIXES[params.fix],
        climber=params.climber,
        climber_gender=params.climber_gender,
        warning=params.warning,
        warning_gender=params.warning_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        climber_age=params.climber_age,
        warning_age=params.warning_age,
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
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, celebrity, perch, spot) combos:\n")
        for theme, celeb, perch, spot in combos:
            print(f"  {theme:12} {celeb:10} {perch:14} {spot}")
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
                f"### {p.climber} & {p.warning}: {p.perch} to reach {p.spot} "
                f"({p.theme}, {p.celebrity}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(theme: Theme, celebrity: Celebrity, perch: Perch, spot: Spot, fix: Fix,
         climber: str = "Tom", climber_gender: str = "boy",
         warning: str = "Lily", warning_gender: str = "girl",
         trait: str = "careful", parent_type: str = "mother",
         delay: int = 0, climber_age: int = 6, warning_age: int = 4,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(
        id=climber,
        kind="character",
        type=climber_gender,
        role="climber",
        age=climber_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=warning,
        kind="character",
        type=warning_gender,
        role="warning",
        age=warning_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        unstable=perch.unstable,
        support_level=perch.risk,
    ))
    world.add(Entity(
        id="spot",
        type="spot",
        label=spot.label,
        height_level=spot.height,
    ))
    world.add(Entity(
        id="banner",
        type="banner",
        label=f"a banner for {celebrity.title} {celebrity.name}",
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    world.facts.update(
        theme=theme,
        celebrity=celebrity,
        perch_cfg=perch,
        spot_cfg=spot,
        fix=fix,
        relation=relation,
        delay=delay,
    )

    play_setup(world, a, b, theme, celebrity)
    plan_banner(world, b, spot, celebrity)

    world.para()
    tempt(world, a, perch)
    warn(world, b, a, perch, parent)

    averted = would_avert(relation, climber_age, warning_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        safe_finish(world, parent, fix, spot, celebrity)
        lesson(world, parent, a, b, perch)
        world.para()
        ending_visit(world, a, b, celebrity, theme)
        severity = 0
        contained = True
    else:
        defy(world, a, b, perch)
        world.para()
        slip(world, a, perch, spot)
        alarm(world, b, parent)
        world.para()
        comfort(world, parent, a, b)
        severity = repair_severity(perch, spot, delay)
        contained = can_finish(fix, perch, spot, delay)
        if contained:
            safe_finish(world, parent, fix, spot, celebrity)
            lesson(world, parent, a, b, perch)
            world.para()
            ending_visit(world, a, b, celebrity, theme)
        else:
            failed_finish(world, parent, fix, spot, celebrity)
            world.para()
            disappointed_lesson(world, parent, a, b, perch, celebrity)

    outcome = "averted" if averted else ("contained" if contained else "disappointed")
    world.facts.update(
        climber=a,
        warning=b,
        parent=parent,
        banner=world.get("banner"),
        outcome=outcome,
        severity=severity,
        fell=a.meters["fallen"] >= THRESHOLD,
        bumped=a.meters["bumped"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "parlor_ship": Theme(
        id="parlor_ship",
        scene="a grand pirate cabin",
        rig="The sofa was their ship, a broom was the mast, a blue blanket was the sea, and a shoebox held their treasure coins.",
        titles=("Captain", "Mate"),
        quest="Let us make the finest ship in the room",
        send_off="went on with their game more wisely than before",
        role_plural="pirates",
    ),
    "reef_hideout": Theme(
        id="reef_hideout",
        scene="a hidden reef fort",
        rig="Two chairs became a rocky cave, the sofa was their ship, and a green blanket turned the carpet into a secret sea.",
        titles=("Captain", "Scout"),
        quest="Let us ready the reef fort",
        send_off="sailed their make-believe seas with safer hands",
        role_plural="pirates",
    ),
    "harbor_deck": Theme(
        id="harbor_deck",
        scene="a busy pirate deck",
        rig="The coffee table was the dock, the sofa was their ship, and a cardboard box became a chest full of maps.",
        titles=("Captain", "Lookout"),
        quest="Let us make the harbor ship gleam",
        send_off="set off on new pirate adventures the safe way",
        role_plural="pirates",
    ),
}

CELEBRITIES = {
    "starling": Celebrity(
        id="starling",
        name="Starling",
        title="Captain",
        nice_deed="always waved to every child at the harbor parade",
        event="the harbor parade",
        tags={"celebrity", "parade"},
    ),
    "pearl": Celebrity(
        id="pearl",
        name="Pearl Patch",
        title="Captain",
        nice_deed="signed shells and spoke in a warm, funny pirate voice",
        event="the library sea festival",
        tags={"celebrity", "library"},
    ),
    "marigold": Celebrity(
        id="marigold",
        name="Marigold",
        title="Captain",
        nice_deed="knelt to admire homemade costumes and said every crew looked brave",
        event="the town boat fair",
        tags={"celebrity", "festival"},
    ),
}

PERCHES = {
    "rolling_chair": Perch(
        id="rolling_chair",
        label="rolling chair",
        phrase="the rolling chair",
        wobble_word="skitter and roll",
        risk=2,
        tags={"chair", "climb"},
    ),
    "cushion_stack": Perch(
        id="cushion_stack",
        label="cushion stack",
        phrase="the stack of sofa cushions",
        wobble_word="sink and sway",
        risk=2,
        tags={"stack", "climb"},
    ),
    "toy_chest": Perch(
        id="toy_chest",
        label="toy chest lid",
        phrase="the closed toy chest",
        wobble_word="tip and bump",
        risk=1,
        tags={"box", "climb"},
    ),
}

SPOTS = {
    "mast_shelf": Spot(
        id="mast_shelf",
        label="the top shelf by the broom mast",
        phrase="the top shelf by the broom mast",
        height=3,
        high=True,
        view_text="everyone will see it from the whole room",
        tags={"high_place", "shelf"},
    ),
    "door_hook": Spot(
        id="door_hook",
        label="the brass hook by the door",
        phrase="the brass hook by the door",
        height=2,
        high=True,
        view_text="it will flutter above the doorway like a real ship sign",
        tags={"high_place", "hook"},
    ),
    "bookcase_corner": Spot(
        id="bookcase_corner",
        label="the top corner of the bookcase",
        phrase="the top corner of the bookcase",
        height=2,
        high=True,
        view_text="it will shine over the treasure chest",
        tags={"high_place", "bookcase"},
    ),
    "low_chest": Spot(
        id="low_chest",
        label="the side of the toy chest",
        phrase="the side of the toy chest",
        height=1,
        high=False,
        view_text="everyone will still see it nearby",
        tags={"low_place"},
    ),
}

FIXES = {
    "step_stool": Fix(
        id="step_stool",
        sense=3,
        power=4,
        label="step stool",
        text="brought the sturdy step stool, held it still, and helped hang the banner on {spot}",
        fail="brought the little step stool, but even standing safely it still would not reach {spot}",
        qa_text="used a sturdy step stool and helped hang the banner safely",
        tags={"stool", "ask_adult"},
    ),
    "grownup_arms": Fix(
        id="grownup_arms",
        sense=3,
        power=5,
        label="grown-up help",
        text="lifted the banner with calm grown-up arms and fixed it neatly on {spot}",
        fail="reached up with calm arms, but the damaged banner still would not stay on {spot}",
        qa_text="used calm grown-up help to place the banner safely",
        tags={"ask_adult", "help"},
    ),
    "lower_spot": Fix(
        id="lower_spot",
        sense=2,
        power=3,
        label="lower hook",
        text="said the room did not need a dangerous high spot at all and fastened the banner lower where everyone could admire it",
        fail="tried to save time by pressing the torn banner against the wall, but it drooped and slid down",
        qa_text="moved the banner to a lower safe place",
        tags={"safe_choice", "help"},
    ),
    "hop_again": Fix(
        id="hop_again",
        sense=1,
        power=1,
        label="hop again",
        text="told them to try one more jump",
        fail="refused the unsafe idea and would not let anyone hop at {spot} again",
        qa_text="tried another unsafe jump",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "thoughtful", "gentle"]

if __name__ == "__main__":
    main()
