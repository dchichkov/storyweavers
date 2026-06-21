#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py
====================================================================================

A small storyworld about a gentle little mystery on a bench: a kindness gift goes
missing, a child investigates, a silly clue reading "ropbl" points the wrong way,
and dialogue reveals that someone moved the gift for a kind reason.

The world is built around three ideas:

* a gift is briefly left on a bench
* a real threat makes the gift unsafe there
* one friend moves it to a safer spot, creating a whodunit-style misunderstanding

The lesson is not "catch the culprit," but "ask kindly before blaming, and tell
people when you move their things."

Run it
------
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py --gift card --threat drizzle
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py --gift muffin --threat gust
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ropbl_bench_lesson_learned_kindness_dialogue_whodunit.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    location: str = ""
    carries: str = ""
    material: str = ""
    edible: bool = False
    light: bool = False
    paper: bool = False
    # shared state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    bench_desc: str
    recipient: str
    affords: set[str] = field(default_factory=set)
    safe_spots: set[str] = field(default_factory=set)
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
class Gift:
    id: str
    label: str
    phrase: str
    material: str
    vulnerable: set[str] = field(default_factory=set)
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
class Threat:
    id: str
    label: str
    arrival: str
    danger_text: str
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
class SafePlace:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
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


SETTINGS = {
    "playground": Setting(
        id="playground",
        place="the playground",
        bench_desc="a red bench near the slide",
        recipient="the crossing guard",
        affords={"drizzle", "gust", "dog"},
        safe_spots={"cubby", "basket", "porch_box"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard",
        bench_desc="a long wooden bench beside the fence",
        recipient="the librarian",
        affords={"drizzle", "gust"},
        safe_spots={"cubby", "porch_box"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the courtyard",
        bench_desc="a stone bench by the flower bed",
        recipient="the gardener",
        affords={"drizzle", "gust", "dog"},
        safe_spots={"basket", "porch_box"},
    ),
}

GIFTS = {
    "card": Gift(
        id="card",
        label="card",
        phrase="a paper thank-you card covered in bright hearts",
        material="paper",
        vulnerable={"drizzle", "gust"},
        tags={"card", "paper"},
    ),
    "muffin": Gift(
        id="muffin",
        label="muffin",
        phrase="a blueberry muffin on a little napkin",
        material="food",
        vulnerable={"dog"},
        tags={"muffin", "food"},
    ),
    "crown": Gift(
        id="crown",
        label="flower crown",
        phrase="a flower crown woven with tiny white daisies",
        material="flowers",
        vulnerable={"drizzle", "gust"},
        tags={"flower", "gift"},
    ),
}

THREATS = {
    "drizzle": Threat(
        id="drizzle",
        label="drizzle",
        arrival="Small rain drops began to tap on the bench.",
        danger_text="would get soggy if it stayed outside",
        tags={"rain", "wet"},
    ),
    "gust": Threat(
        id="gust",
        label="gust of wind",
        arrival="A playful gust came skipping through the yard and shook the papers and leaves.",
        danger_text="might blow away if it stayed on the bench",
        tags={"wind"},
    ),
    "dog": Threat(
        id="dog",
        label="sniffing dog",
        arrival="A neighbor's curious little dog trotted close, nose twitching.",
        danger_text="might be sniffed or nibbled if it stayed there",
        tags={"dog"},
    ),
}

SAFE_PLACES = {
    "cubby": SafePlace(
        id="cubby",
        label="cubby",
        phrase="the dry cubby by the classroom door",
        protects={"drizzle", "gust"},
        tags={"cubby", "safe_place"},
    ),
    "basket": SafePlace(
        id="basket",
        label="lidded basket",
        phrase="a lidded basket under the bench",
        protects={"gust", "dog"},
        tags={"basket", "safe_place"},
    ),
    "porch_box": SafePlace(
        id="porch_box",
        label="porch box",
        phrase="the little porch box beside the office steps",
        protects={"drizzle", "gust", "dog"},
        tags={"box", "safe_place"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ruby", "Ella", "Zoe", "Ava", "Mina"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Sam", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["careful", "curious", "gentle", "thoughtful", "cheerful", "steady"]
TONES = {"kind", "hasty"}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    gift: str
    threat: str
    safe_place: str
    tone: str
    hero_name: str
    hero_gender: str
    mover_name: str
    mover_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    hero_trait: str
    mover_trait: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World + rules
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


def _r_risk(world: World) -> list[str]:
    gift = world.get("gift")
    threat = world.facts["threat_cfg"]
    if gift.location != "bench":
        return []
    if threat.id not in world.facts["gift_cfg"].vulnerable:
        return []
    sig = ("risk", gift.id, threat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["risk"] += 1
    world.get("bench").meters["risk"] += 1
    for kid_id in ("hero", "mover", "friend"):
        world.get(kid_id).memes["worry"] += 1
    return ["__risk__"]


def _r_protected(world: World) -> list[str]:
    gift = world.get("gift")
    safe = world.facts["safe_cfg"]
    threat = world.facts["threat_cfg"]
    if gift.location != safe.id:
        return []
    if threat.id not in safe.protects:
        return []
    sig = ("protected", gift.id, safe.id, threat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["protected"] += 1
    gift.meters["risk"] = 0.0
    return ["__protected__"]


RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="protected", tag="physical", apply=_r_protected),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def gift_at_risk(gift: Gift, threat: Threat) -> bool:
    return threat.id in gift.vulnerable


def safe_for(safe_place: SafePlace, threat: Threat) -> bool:
    return threat.id in safe_place.protects


def valid_combo(place: str, gift: str, threat: str, safe_place: str) -> bool:
    setting = SETTINGS[place]
    g = GIFTS[gift]
    t = THREATS[threat]
    s = SAFE_PLACES[safe_place]
    return (
        threat in setting.affords
        and safe_place in setting.safe_spots
        and gift_at_risk(g, t)
        and safe_for(s, t)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for gift_id in GIFTS:
            for threat_id in setting.affords:
                for safe_id in setting.safe_spots:
                    if valid_combo(place, gift_id, threat_id, safe_id):
                        out.append((place, gift_id, threat_id, safe_id))
    return sorted(out)


def explain_rejection(place: str, gift: Gift, threat: Threat, safe_place: SafePlace) -> str:
    setting = SETTINGS[place]
    if threat.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not really support the threat "
            f"'{threat.id}', so the mystery would have no honest trigger.)"
        )
    if not gift_at_risk(gift, threat):
        return (
            f"(No story: a {gift.label} would not be in real trouble from "
            f"{threat.label}, so there is no good reason to move it from the bench.)"
        )
    if safe_place.id not in setting.safe_spots:
        return (
            f"(No story: {safe_place.phrase} is not available in {setting.place}, "
            f"so the helper would have nowhere plausible to take the gift.)"
        )
    if not safe_for(safe_place, threat):
        return (
            f"(No story: {safe_place.phrase} does not actually protect a {gift.label} "
            f"from {threat.label}. The kind helper needs a sensible fix.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "gentle_solve" if params.tone == "kind" else "lesson_apology"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_loss(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    gift = sim.get("gift")
    return {
        "risk": gift.meters["risk"],
        "danger": gift.meters["risk"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, mover: Entity, friend: Entity, gift_cfg: Gift) -> None:
    recipient = world.setting.recipient
    world.say(
        f"After school, {hero.id}, {mover.id}, and {friend.id} sat by "
        f"{world.setting.bench_desc}. They were making {gift_cfg.phrase} for {recipient}."
    )
    world.say(
        f"{hero.id} set the {gift_cfg.label} in the middle of the bench and smiled. "
        f'"It looks kind," {hero.pronoun()} said.'
    )


def ropbl_clue(world: World, friend: Entity) -> None:
    friend.attrs["note_text"] = "ropbl"
    world.say(
        f"{friend.id} had also been practicing silly secret-code letters on a scrap of paper. "
        f'On it, in crooked pencil marks, was the word "ropbl."'
    )


def step_away(world: World, hero: Entity) -> None:
    hero.location = "fountain"
    world.say(
        f'"I forgot the ribbon," said {hero.id}. "I will be right back." '
        f"{hero.pronoun().capitalize()} skipped to the fountain path for one minute."
    )


def danger_arrives(world: World, threat_cfg: Threat) -> None:
    world.facts["threat_active"] = True
    world.say(threat_cfg.arrival)
    propagate(world, narrate=False)


def move_to_safety(world: World, mover: Entity, safe_cfg: SafePlace) -> None:
    gift = world.get("gift")
    mover.carries = gift.id
    gift.location = safe_cfg.id
    gift.meters["moved"] += 1
    mover.memes["kindness"] += 1
    mover.memes["urgency"] += 1
    propagate(world, narrate=False)
    world.facts["moved_before_telling"] = True


def return_to_empty_bench(world: World, hero: Entity, friend: Entity) -> None:
    hero.location = "bench"
    world.get("bench").meters["empty"] += 1
    world.say(
        f"When {hero.id} came back, the bench was empty except for the scrap that said "
        f'"{friend.attrs["note_text"]}". {hero.id} stopped short.'
    )
    world.say(f'"Oh!" {hero.id} whispered. "The {world.facts["gift_cfg"].label} is gone."')


def wonder(world: World, hero: Entity) -> None:
    hero.memes["mystery"] += 1
    world.say(
        f"It felt like a very small whodunit. The bench, the clue, and the missing gift "
        f"all seemed to be pointing at a secret."
    )


def ask_friend_kindly(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"{friend.id}," said {hero.id}, keeping {hero.pronoun("possessive")} voice soft, '
        f'"did you move it? I found your "ropbl" paper on the bench."'
    )
    world.say(
        f'"No," said {friend.id}. "{friend.attrs["note_text"]} is just my nonsense code. '
        f'I was trying to make the funniest word I could think of."'
    )


def accuse_then_pause(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["suspicion"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f'"Aha!" said {hero.id}. "It must have been you, {friend.id}. Your "ropbl" note was right here."'
    )
    world.say(
        f'{friend.id} blinked and hugged the scrap to {friend.pronoun("possessive")} shirt. '
        f'"I did write ropbl," {friend.pronoun()} said, "but I did not take the gift."'
    )
    world.say(
        f"Hearing the wobble in {friend.id}'s voice, {hero.id} felt a little sorry for jumping too fast."
    )


def ask_again_gently(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["lesson"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"I am sorry," said {hero.id}. "Let me ask again kindly. Did you see where it went?"'
    )
    world.say(
        f'"Only that {mover_name(world)} ran off in a hurry," said {friend.id}. '
        f'"I thought {mover_pron(world).capitalize()} was helping."'
    )


def mover_name(world: World) -> str:
    return world.get("mover").id


def mover_pron(world: World) -> str:
    return world.get("mover").pronoun()


def ask_mover(world: World, hero: Entity, mover: Entity, tone: str) -> None:
    if tone == "kind":
        world.say(
            f'"{mover.id}," asked {hero.id}, "did you move the {world.facts["gift_cfg"].label}?"'
        )
    else:
        world.say(
            f'{hero.id} turned to {mover.id}. "Did you move it?" {hero.pronoun()} asked, '
            f"much more gently this time."
        )


def reveal(world: World, mover: Entity, safe_cfg: SafePlace, threat_cfg: Threat) -> None:
    gift_cfg = world.facts["gift_cfg"]
    mover.memes["relief"] += 1
    world.say(
        f'"Yes," said {mover.id}. "I saw that the {gift_cfg.label} {threat_cfg.danger_text}, '
        f'so I put it in {safe_cfg.phrase}. I wanted to be kind, but I forgot to tell you first."'
    )
    world.say(
        f"{mover.id} led them to {safe_cfg.phrase}, and there it was, safe and neat."
    )


def apology(world: World, hero: Entity, friend: Entity, mover: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    mover.memes["relief"] += 1
    world.say(
        f'"I am sorry I blamed you, {friend.id}," said {hero.id}. '
        f'"And thank you, {mover.id}, for protecting it."'
    )


def gentle_close(world: World, hero: Entity, mover: Entity, friend: Entity) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    mover.memes["joy"] += 1
    world.say(
        f'"Next time," said {friend.id}, "we should ask kindly first and tell people when we move their things."'
    )
    world.say(
        f'"That is the real answer to the mystery," said {hero.id}. "{mover.id} did it out of kindness."'
    )


def ending(world: World, hero: Entity, mover: Entity, friend: Entity) -> None:
    recipient = world.setting.recipient
    gift_cfg = world.facts["gift_cfg"]
    world.say(
        f"They carried the {gift_cfg.label} together, and the bench behind them looked ordinary again."
    )
    world.say(
        f"When they gave it to {recipient}, all three children were smiling, because the little mystery "
        f"had ended with honesty, kindness, and better dialogue."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    gift_cfg: Gift,
    threat_cfg: Threat,
    safe_cfg: SafePlace,
    tone: str,
    hero_name: str,
    hero_gender: str,
    mover_name_: str,
    mover_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    hero_trait: str,
    mover_trait: str,
    friend_trait: str,
) -> World:
    world = World(setting)
    world.facts["gift_cfg"] = gift_cfg
    world.facts["threat_cfg"] = threat_cfg
    world.facts["safe_cfg"] = safe_cfg
    world.facts["tone"] = tone
    world.facts["moved_before_telling"] = False
    world.facts["threat_active"] = False

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    mover = world.add(Entity(
        id="mover",
        kind="character",
        type=mover_gender,
        label=mover_name_,
        role="mover",
        traits=[mover_trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the grown-up",
        role="parent",
    ))
    bench = world.add(Entity(
        id="bench",
        kind="thing",
        type="bench",
        label="bench",
        role="bench",
        location=setting.place,
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift_cfg.id,
        label=gift_cfg.label,
        role="gift",
        location="bench",
        material=gift_cfg.material,
        edible=(gift_cfg.id == "muffin"),
        light=(gift_cfg.id == "crown"),
        paper=(gift_cfg.id == "card"),
    ))

    for kid in (hero, mover, friend):
        kid.memes["curiosity"] = 1.0
        kid.memes["kindness"] = 1.0 if "gentle" in kid.traits or "thoughtful" in kid.traits else 0.0
        kid.attrs["known_safe_place"] = safe_cfg.id

    introduce(world, hero, mover, friend, gift_cfg)
    ropbl_clue(world, friend)
    step_away(world, hero)

    world.para()
    danger_arrives(world, threat_cfg)
    move_to_safety(world, mover, safe_cfg)
    return_to_empty_bench(world, hero, friend)
    wonder(world, hero)

    world.para()
    if tone == "kind":
        ask_friend_kindly(world, hero, friend)
    else:
        accuse_then_pause(world, hero, friend)
        ask_again_gently(world, hero, friend)

    ask_mover(world, hero, mover, tone)
    reveal(world, mover, safe_cfg, threat_cfg)
    if tone == "hasty":
        apology(world, hero, friend, mover)

    world.para()
    gentle_close(world, hero, mover, friend)
    ending(world, hero, mover, friend)

    world.facts.update(
        hero=hero,
        mover=mover,
        friend=friend,
        parent=parent,
        bench=bench,
        gift=gift,
        outcome=outcome_of(StoryParams(
            place=setting.id,
            gift=gift_cfg.id,
            threat=threat_cfg.id,
            safe_place=safe_cfg.id,
            tone=tone,
            hero_name=hero_name,
            hero_gender=hero_gender,
            mover_name=mover_name_,
            mover_gender=mover_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            parent=parent_type,
            hero_trait=hero_trait,
            mover_trait=mover_trait,
            friend_trait=friend_trait,
        )),
        recipient=setting.recipient,
        clue_text=friend.attrs["note_text"],
        protected=gift.meters["protected"] >= THRESHOLD,
        at_risk=threat_cfg.id in gift_cfg.vulnerable,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bench": [(
        "What is a bench?",
        "A bench is a long seat for people to sit on. You often see one in a playground, yard, or park."
    )],
    "rain": [(
        "Why is drizzle a problem for paper?",
        "Paper soaks up water easily, so drizzle can make it bend, tear, or turn soggy. That is why paper things should be kept dry."
    )],
    "wind": [(
        "Why can wind carry light things away?",
        "A strong gust can push light things like paper or flowers because they do not weigh very much. That is why people hold them down or put them somewhere safe."
    )],
    "dog": [(
        "Why should food be kept away from a curious dog?",
        "A dog may sniff or nibble food if it is left where the dog can reach it. Moving the food keeps both the treat and the dog safer."
    )],
    "card": [(
        "What is a thank-you card for?",
        "A thank-you card is a kind way to show someone you are grateful. People often decorate it with drawings or sweet words."
    )],
    "muffin": [(
        "What is a muffin?",
        "A muffin is a small baked treat. People often put it on a plate or napkin when they want to share it."
    )],
    "flower": [(
        "What is a flower crown?",
        "A flower crown is a ring made from flowers and stems. It is pretty, but it can be delicate."
    )],
    "dialogue": [(
        "What does dialogue help people do in a story?",
        "Dialogue lets characters ask questions, explain what happened, and understand each other. Talking kindly can solve confusion before it grows bigger."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help or care for someone in a gentle way. Sometimes it means protecting something important for them."
    )],
}
KNOWLEDGE_ORDER = ["bench", "card", "muffin", "flower", "rain", "wind", "dog", "dialogue", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mover = f["mover"]
    friend = f["friend"]
    gift_cfg = f["gift_cfg"]
    threat_cfg = f["threat_cfg"]
    return [
        f'Write a short whodunit-style story for a 3-to-5-year-old that includes the words "ropbl" and "bench".',
        f"Tell a gentle mystery where {hero.label} finds a kindness gift missing from a bench, questions {friend.label} and {mover.label}, and learns what really happened through dialogue.",
        f"Write a simple story where a {gift_cfg.label} seems to disappear, but the true answer is that someone moved it because {threat_cfg.label} made the bench unsafe, ending with a lesson about kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mover = f["mover"]
    friend = f["friend"]
    gift_cfg = f["gift_cfg"]
    threat_cfg = f["threat_cfg"]
    safe_cfg = f["safe_cfg"]
    recipient = f["recipient"]
    out: list[tuple[str, str]] = [
        (
            "What was the little mystery?",
            f"The {gift_cfg.label} for {recipient} seemed to vanish from the bench. "
            f"The empty bench and the funny ropbl note made it feel like a tiny whodunit."
        ),
        (
            'What did the word "ropbl" mean?',
            f'It was not a real clue at all. {friend.label} had written "ropbl" as a silly nonsense code word while practicing letters.'
        ),
        (
            f"Who moved the {gift_cfg.label}, and why?",
            f"{mover.label} moved it to {safe_cfg.phrase}. {mover.pronoun().capitalize()} saw that the {gift_cfg.label} {threat_cfg.danger_text}, so moving it was a kind way to protect it."
        ),
    ]
    if f["outcome"] == "lesson_apology":
        out.append((
            f"What lesson did {hero.label} learn?",
            f"{hero.label} learned not to blame someone too quickly. "
            f"When {hero.pronoun()} stopped, listened, and asked kindly, the real answer came out and {friend.label}'s hurt feelings could be mended."
        ))
    else:
        out.append((
            f"How did kind dialogue help solve the mystery?",
            f"{hero.label} asked questions in a calm voice instead of accusing anyone. "
            f"That made space for {friend.label} to explain the ropbl note and for {mover.label} to tell the truth about moving the gift."
        ))
    out.append((
        "How did the story end?",
        f"It ended with the children carrying the {gift_cfg.label} together and smiling. "
        f"The ending shows that honesty and kindness mattered more than having a dramatic culprit."
    ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"bench", "dialogue", "kindness"}
    gift_cfg = f["gift_cfg"]
    threat_cfg = f["threat_cfg"]
    tags |= set(gift_cfg.tags)
    tags |= set(threat_cfg.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.carries:
            bits.append(f"carries={ent.carries}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A combo is valid when the place affords the threat, the gift is really at risk,
% the safe place exists there, and the safe place truly protects against that threat.
valid(P,G,T,S) :- setting(P), gift(G), threat(T), safe_place(S),
                  affords(P,T), available(P,S), vulnerable(G,T), protects(S,T).

smooth_outcome :- chosen_tone(kind).
apology_outcome :- chosen_tone(hasty).

outcome(gentle_solve) :- smooth_outcome.
outcome(lesson_apology) :- apology_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(place.affords):
            lines.append(asp.fact("affords", pid, t))
        for s in sorted(place.safe_spots):
            lines.append(asp.fact("available", pid, s))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for t in sorted(gift.vulnerable):
            lines.append(asp.fact("vulnerable", gid, t))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for sid, safe in SAFE_PLACES.items():
        lines.append(asp.fact("safe_place", sid))
        for t in sorted(safe.protects):
            lines.append(asp.fact("protects", sid, t))
    for tone in sorted(TONES):
        lines.append(asp.fact("tone", tone))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            asp.fact("chosen_tone", params.tone),
            "#show outcome/1."
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    checks = CURATED[:]
    for params in checks:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params, asp_outcome(params), outcome_of(params))
            break
    else:
        print(f"OK: outcome model matches on {len(checks)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="playground",
        gift="card",
        threat="drizzle",
        safe_place="cubby",
        tone="kind",
        hero_name="Lina",
        hero_gender="girl",
        mover_name="Owen",
        mover_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        parent="mother",
        hero_trait="gentle",
        mover_trait="thoughtful",
        friend_trait="curious",
    ),
    StoryParams(
        place="courtyard",
        gift="muffin",
        threat="dog",
        safe_place="basket",
        tone="hasty",
        hero_name="Ben",
        hero_gender="boy",
        mover_name="Ruby",
        mover_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="father",
        hero_trait="cheerful",
        mover_trait="careful",
        friend_trait="curious",
    ),
    StoryParams(
        place="schoolyard",
        gift="crown",
        threat="gust",
        safe_place="porch_box",
        tone="kind",
        hero_name="Nora",
        hero_gender="girl",
        mover_name="Sam",
        mover_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        parent="mother",
        hero_trait="steady",
        mover_trait="gentle",
        friend_trait="cheerful",
    ),
    StoryParams(
        place="playground",
        gift="crown",
        threat="drizzle",
        safe_place="porch_box",
        tone="hasty",
        hero_name="Theo",
        hero_gender="boy",
        mover_name="Ava",
        mover_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="father",
        hero_trait="curious",
        mover_trait="thoughtful",
        friend_trait="cheerful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit-style storyworld about a missing kindness gift on a bench."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--safe-place", dest="safe_place", choices=SAFE_PLACES)
    ap.add_argument("--tone", choices=sorted(TONES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.gift and args.threat and args.safe_place:
        if not valid_combo(args.place, args.gift, args.threat, args.safe_place):
            raise StoryError(explain_rejection(
                args.place,
                GIFTS[args.gift],
                THREATS[args.threat],
                SAFE_PLACES[args.safe_place],
            ))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.gift is None or combo[1] == args.gift)
        and (args.threat is None or combo[2] == args.threat)
        and (args.safe_place is None or combo[3] == args.safe_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, gift, threat, safe_place = rng.choice(combos)
    tone = args.tone or rng.choice(sorted(TONES))
    parent = args.parent or rng.choice(["mother", "father"])

    hero_gender = rng.choice(["girl", "boy"])
    mover_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])

    hero_name = _pick_name(rng, hero_gender, set())
    mover_name_ = _pick_name(rng, mover_gender, {hero_name})
    friend_name = _pick_name(rng, friend_gender, {hero_name, mover_name_})

    return StoryParams(
        place=place,
        gift=gift,
        threat=threat,
        safe_place=safe_place,
        tone=tone,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mover_name=mover_name_,
        mover_gender=mover_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        hero_trait=rng.choice(TRAITS),
        mover_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.threat not in THREATS:
        raise StoryError(f"(Unknown threat: {params.threat})")
    if params.safe_place not in SAFE_PLACES:
        raise StoryError(f"(Unknown safe place: {params.safe_place})")
    if params.tone not in TONES:
        raise StoryError(f"(Unknown tone: {params.tone})")
    if not valid_combo(params.place, params.gift, params.threat, params.safe_place):
        raise StoryError(explain_rejection(
            params.place,
            GIFTS[params.gift],
            THREATS[params.threat],
            SAFE_PLACES[params.safe_place],
        ))

    world = tell(
        setting=SETTINGS[params.place],
        gift_cfg=GIFTS[params.gift],
        threat_cfg=THREATS[params.threat],
        safe_cfg=SAFE_PLACES[params.safe_place],
        tone=params.tone,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mover_name_=params.mover_name,
        mover_gender=params.mover_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        mover_trait=params.mover_trait,
        friend_trait=params.friend_trait,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, gift, threat, safe_place) combos:\n")
        for place, gift, threat, safe_place in combos:
            print(f"  {place:11} {gift:7} {threat:8} {safe_place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero_name}, {p.mover_name}, {p.friend_name}: "
                f"{p.gift} on a bench at {p.place} ({p.threat}, {p.tone})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
