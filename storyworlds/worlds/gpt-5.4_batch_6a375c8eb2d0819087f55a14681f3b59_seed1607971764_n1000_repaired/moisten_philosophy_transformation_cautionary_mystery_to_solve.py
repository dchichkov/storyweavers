#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py
=================================================================================================

A standalone folk-tale storyworld about a child, a thirsty magic seed, and a
mystery that must be solved before the seed changes forever.

The tiny domain:
- A village elder gives a child a moon-seed and a simple philosophy:
  living things answer patient care.
- The child tries to moisten the seed, but every morning it is dry again.
- A clue reveals the hidden cause: a goat drinks the water, a cracked bowl leaks,
  or a shaft of noon sun drinks it away.
- If the child finds the right fix soon enough, the seed transforms into a silver
  vine with lantern flowers.
- If the child delays too long, the seed hardens and transforms into a dull stone
  bead instead: a cautionary ending about hurrying late after ignoring a living need.

Run it
------
    python storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py --setting courtyard --culprit goat --remedy shelf
    python storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py --culprit sun --remedy clay_patch
    python storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py --all --qa
    python storyworlds/worlds/gpt-5.4/moisten_philosophy_transformation_cautionary_mystery_to_solve.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }
        return mapping.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
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
    image: str
    affords: set[str] = field(default_factory=set)
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
class Culprit:
    id: str
    label: str
    clue: str
    reveal: str
    urgency: int
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
    label: str
    action: str
    fixes: set[str] = field(default_factory=set)
    power: int = 1
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
class WaterSource:
    id: str
    label: str
    phrase: str
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


def _r_thirst(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    if not world.facts.get("culprit_active", False):
        return out
    sig = ("thirst", world.facts.get("day", 0))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["thirst"] += 1
    world.get("child").memes["worry"] += 1
    out.append("__thirst__")
    return out


def _r_harden(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    delay = int(world.facts.get("delay_progress", 0))
    if seed.meters["thirst"] < THRESHOLD or delay <= 0:
        return out
    sig = ("harden", delay)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["hardness"] += float(delay)
    world.get("child").memes["regret"] += float(delay)
    out.append("__harden__")
    return out


def _r_revive(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    if world.facts.get("culprit_active", False):
        return out
    if seed.meters["moisture"] < THRESHOLD:
        return out
    if seed.meters["hardness"] >= 2.0:
        return out
    sig = ("revive",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["sprout"] += 1
    world.get("child").memes["relief"] += 1
    out.append("__revive__")
    return out


CAUSAL_RULES = [
    Rule(name="thirst", tag="physical", apply=_r_thirst),
    Rule(name="harden", tag="physical", apply=_r_harden),
    Rule(name="revive", tag="physical", apply=_r_revive),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def culprit_in_setting(setting: Setting, culprit: Culprit) -> bool:
    return culprit.id in setting.affords


def remedy_fits(culprit: Culprit, remedy: Remedy) -> bool:
    return culprit.id in remedy.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, culprit in CULPRITS.items():
            if not culprit_in_setting(setting, culprit):
                continue
            for rid, remedy in REMEDIES.items():
                if remedy_fits(culprit, remedy):
                    combos.append((sid, cid, rid))
    return combos


def failure_limit(culprit: Culprit) -> int:
    return culprit.urgency + 1


def outcome_of(params: "StoryParams") -> str:
    culprit = CULPRITS[params.culprit]
    return "bloomed" if params.delay < failure_limit(culprit) else "stone"


def explain_rejection(setting: Optional[Setting], culprit: Optional[Culprit], remedy: Optional[Remedy]) -> str:
    if setting and culprit and not culprit_in_setting(setting, culprit):
        return (
            f"(No story: {culprit.label} does not fit {setting.place}. "
            f"The mystery needs a cause that could truly happen there.)"
        )
    if culprit and remedy and not remedy_fits(culprit, remedy):
        return (
            f"(No story: {remedy.label} would not stop {culprit.label}. "
            f"The child must solve the mystery with a remedy that matches the cause.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def predict_revival(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.facts["delay_progress"] = delay
    propagate(sim, narrate=False)
    return {
        "hardness": sim.get("seed").meters["hardness"],
        "can_bloom": delay < failure_limit(sim.facts["culprit_cfg"]),
    }


def opening(world: World, child: Entity, elder: Entity, water: WaterSource) -> None:
    seed = world.get("seed")
    child.memes["trust"] += 1
    world.say(
        f"In the days when people still listened to the night wind, {child.id} lived "
        f"beside {world.setting.place}. {world.setting.image}"
    )
    world.say(
        f"One evening {child.id}'s {elder.label_word} placed a pale moon-seed in "
        f"a shell bowl and said, \"Each dawn, {water.phrase} to moisten this seed. "
        f"My philosophy is simple: what is cared for grows honest roots.\""
    )
    seed.meters["hope"] += 1


def first_attempt(world: World, child: Entity, water: WaterSource) -> None:
    seed = world.get("seed")
    seed.meters["moisture"] += 1
    child.memes["care"] += 1
    world.say(
        f"So at first light, {child.id} carried {water.phrase} in both hands and "
        f"gently used it to moisten the seed."
    )


def mystery_appears(world: World, child: Entity, culprit: Culprit) -> None:
    world.facts["culprit_active"] = True
    world.facts["day"] = 1
    world.get("seed").meters["moisture"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"But on the next morning the bowl was dry as old bone. {child.id} bent low "
        f"and found {culprit.clue}."
    )
    world.say(
        f"That was the beginning of the mystery, and {child.id} felt worry tug where "
        f"sleep should still have been."
    )


def seek_answer(world: World, child: Entity, elder: Entity, culprit: Culprit, delay: int) -> None:
    pred = predict_revival(world, delay)
    world.facts["predicted_hardness"] = pred["hardness"]
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} carried the bowl to {elder.label_word} and whispered, '
        f'"Why does the seed dry even after I moisten it?"'
    )
    world.say(
        f'{elder.label_word.capitalize()} studied the clue and answered, "{culprit.reveal}"'
    )
    if delay > 0:
        world.say(
            f"But answers are not the same as haste. {child.id} lost {delay} day"
            f'{"s" if delay != 1 else ""} fetching what was needed and thinking the seed could wait.'
        )
    else:
        world.say(
            f"{child.id} did not waste even one shadow. The answer was clear enough to act on at once."
        )


def delay_and_hardening(world: World, child: Entity, delay: int) -> None:
    if delay <= 0:
        return
    world.facts["delay_progress"] = delay
    propagate(world, narrate=False)
    if world.get("seed").meters["hardness"] >= THRESHOLD:
        world.say(
            f"By the time {child.id} returned, the moon-seed had tightened inside "
            f"its skin like a fist."
        )


def fix_mystery(world: World, child: Entity, remedy: Remedy) -> None:
    child.memes["resolve"] += 1
    world.facts["culprit_active"] = False
    world.say(
        f"Then {child.id} {remedy.action}. At last the hidden trouble had a name "
        f"and a proper answer."
    )


def second_watering(world: World, child: Entity, water: WaterSource) -> None:
    seed = world.get("seed")
    seed.meters["moisture"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Once more {child.id} brought {water.phrase} and used it to moisten the seed, "
        f"this time after the mystery had truly been solved."
    )


def bloom_ending(world: World, child: Entity, elder: Entity) -> None:
    seed = world.get("seed")
    seed.meters["transformed"] += 1
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(
        "At moonrise the shell bowl trembled. A silver vine rose from it, curling up "
        "the post with lantern flowers pale as milk."
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled and touched one glowing petal. '
        f'"Now you know the old philosophy," {elder.pronoun()} said. '
        f'"Kindness must be timely, not merely true."'
    )
    world.say(
        f"And from that night on, whenever {child.id} passed {world.setting.place}, "
        f"{child.pronoun()} looked up at the shining flowers and remembered how a mystery "
        f"had become a blessing."
    )


def stone_ending(world: World, child: Entity, elder: Entity) -> None:
    seed = world.get("seed")
    seed.meters["stone"] += 1
    seed.meters["transformed"] += 1
    child.memes["sadness"] += 1
    world.say(
        "But the moon-seed had waited too long. Instead of sending up a vine, it "
        "shrank into a smooth gray bead that clicked sadly in the bowl."
    )
    world.say(
        f'{elder.label_word.capitalize()} closed {elder.pronoun("possessive")} fingers around '
        f'{child.id}\'s hand and said, "A living thing can forgive a mistake, but not always a delay. '
        f'That is why care must walk faster than excuses."'
    )
    world.say(
        f"{child.id} kept the little stone beside the bed ever after, a quiet warning "
        f"that some mysteries must be solved before the root goes still."
    )


def tell(
    setting: Setting,
    culprit: Culprit,
    remedy: Remedy,
    water: WaterSource,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    seed = world.add(Entity(
        id="seed",
        kind="thing",
        type="seed",
        label="moon-seed",
        role="seed",
    ))

    world.facts.update(
        child=child,
        elder=elder,
        seed=seed,
        setting_cfg=setting,
        culprit_cfg=culprit,
        remedy_cfg=remedy,
        water_cfg=water,
        culprit_active=False,
        day=0,
        delay_progress=0,
        delay=delay,
    )

    opening(world, child, elder, water)
    first_attempt(world, child, water)

    world.para()
    mystery_appears(world, child, culprit)
    seek_answer(world, child, elder, culprit, delay)

    world.para()
    delay_and_hardening(world, child, delay)
    fix_mystery(world, child, remedy)
    second_watering(world, child, water)

    world.para()
    outcome = "bloomed" if delay < failure_limit(culprit) else "stone"
    if outcome == "bloomed":
        bloom_ending(world, child, elder)
    else:
        stone_ending(world, child, elder)

    world.facts.update(
        outcome=outcome,
        clue=culprit.clue,
        reveal=culprit.reveal,
        fixed=not world.facts["culprit_active"],
        hardened=seed.meters["hardness"] >= THRESHOLD,
        transformed=seed.meters["transformed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard",
        image="A fig tree leaned over the wall, and swallows stitched the dusk together.",
        affords={"goat", "sun"},
    ),
    "porch": Setting(
        id="porch",
        place="the old porch",
        image="The rafters smelled of cedar, and the eaves kept one half in shade and one half in light.",
        affords={"crack", "sun"},
    ),
    "wellside": Setting(
        id="wellside",
        place="the village well",
        image="Buckets sang softly on their ropes, and mint grew between the cool stones.",
        affords={"goat", "crack"},
    ),
}

CULPRITS = {
    "goat": Culprit(
        id="goat",
        label="a thirsty goat",
        clue="a half-moon print and one white hair by the bowl",
        reveal="A thirsty goat comes in the dawn and drinks before the seed can drink.",
        urgency=1,
        tags={"goat", "thirst"},
    ),
    "crack": Culprit(
        id="crack",
        label="a cracked shell bowl",
        clue="a dark thread of water dried along the bowl's side",
        reveal="The shell bowl is cracked, and the water slips out before the seed can keep it.",
        urgency=0,
        tags={"crack", "bowl", "thirst"},
    ),
    "sun": Culprit(
        id="sun",
        label="a hot square of noon sun",
        clue="a bright square burned on the boards exactly where the bowl had rested",
        reveal="A sharp beam of noon sun falls there and drinks the water away.",
        urgency=1,
        tags={"sun", "thirst"},
    ),
}

REMEDIES = {
    "shelf": Remedy(
        id="shelf",
        label="a high shelf",
        action="set the bowl on a high shelf the goat could not nose",
        fixes={"goat"},
        power=2,
        tags={"shelf", "goat"},
    ),
    "clay_patch": Remedy(
        id="clay_patch",
        label="a clay patch",
        action="pressed cool river clay along the crack and smoothed it shut",
        fixes={"crack"},
        power=2,
        tags={"clay", "repair"},
    ),
    "shade_cloth": Remedy(
        id="shade_cloth",
        label="a strip of blue shade-cloth",
        action="tied a strip of blue cloth above the bowl so the noon beam could not strike it",
        fixes={"sun"},
        power=2,
        tags={"shade", "sun"},
    ),
}

WATERS = {
    "dew": WaterSource(
        id="dew",
        label="dew",
        phrase="a cupped handful of dew",
        tags={"dew", "water"},
    ),
    "wellwater": WaterSource(
        id="wellwater",
        label="well water",
        phrase="a little cup of cool well water",
        tags={"well", "water"},
    ),
    "springwater": WaterSource(
        id="springwater",
        label="spring water",
        phrase="a spoon of clear spring water",
        tags={"spring", "water"},
    ),
}

GIRL_NAMES = ["Mira", "Nila", "Suri", "Anya", "Lina", "Tala", "Rina", "Pema"]
BOY_NAMES = ["Toma", "Ilan", "Niko", "Ravi", "Milo", "Beren", "Jori", "Sami"]
TRAITS = ["patient", "curious", "gentle", "careful", "thoughtful", "earnest"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    culprit: str
    remedy: str
    water: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    delay: int = 0
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
    "dew": [(
        "What is dew?",
        "Dew is tiny drops of water that gather on grass and leaves when the air cools. In the morning it can make plants feel fresh and wet."
    )],
    "well": [(
        "What is a well for?",
        "A well is a deep place people use to draw water from the ground. Villages often gather there because clean water helps people, animals, and plants."
    )],
    "spring": [(
        "What is spring water?",
        "Spring water comes from water that rises naturally out of the earth. People often think of it as cool and clean."
    )],
    "goat": [(
        "Why might a goat drink from a bowl?",
        "A goat gets thirsty like any other animal, so it may drink if it finds water left low enough to reach. Animals do not know they are spoiling a careful plan."
    )],
    "crack": [(
        "Why does a cracked bowl leak?",
        "A crack gives water a little path to follow, so the water slips out drop by drop. Even a small crack can empty a bowl over time."
    )],
    "sun": [(
        "How can sun make water disappear?",
        "Warm sun can dry water into the air, especially if the bowl sits right in the light. That is why some plants need shade as well as water."
    )],
    "thirst": [(
        "Why do seeds need water?",
        "Seeds need water to soften and wake up before they can sprout. Without enough water, they stay hard and cannot begin to grow well."
    )],
    "repair": [(
        "Why is matching the fix to the problem important?",
        "A good fix must answer the real cause of the trouble. If you solve the wrong problem, the trouble simply comes back."
    )],
}
KNOWLEDGE_ORDER = ["dew", "well", "spring", "goat", "crack", "sun", "thirst", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    culprit = f["culprit_cfg"]
    outcome = f["outcome"]
    water = f["water_cfg"]
    if outcome == "stone":
        return [
            f'Write a folk tale for a young child that includes the words "moisten" and "philosophy". Make the tale a mystery about why a magic seed keeps drying out.',
            f"Tell a cautionary village tale where {child.id} discovers that {culprit.label} is stopping a moon-seed from growing, but acts too late and learns a sad lesson.",
            f"Write a folk-style story where a child uses {water.label} to care for a magical seed, solves a mystery, and learns that kindness must be timely.",
        ]
    return [
        f'Write a folk tale for a young child that includes the words "moisten" and "philosophy". Make the tale a mystery about why a magic seed keeps drying out.',
        f"Tell a gentle mystery tale where {child.id} discovers that {culprit.label} is stopping a moon-seed from growing and solves the trouble in time.",
        f"Write a folk-style transformation story where a child uses {water.label} to care for a magical seed, solves a hidden problem, and is rewarded with a shining change.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    culprit = f["culprit_cfg"]
    remedy = f["remedy_cfg"]
    water = f["water_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child trusted with a moon-seed, and {child.pronoun('possessive')} {elder.label_word} who teaches {child.pronoun('object')} how to care for it."
        ),
        (
            "What was the mystery in the story?",
            f"The mystery was why the moon-seed kept turning dry by morning even after {child.id} used {water.phrase} to moisten it. The clue showed that something in the world was stealing or losing the water."
        ),
        (
            "What clue helped solve the mystery?",
            f"The important clue was {culprit.clue}. That clue pointed to the real cause instead of making the trouble feel like magic with no answer."
        ),
        (
            "How did the child solve the problem?",
            f"{child.id} understood that the cause was {culprit.label}, then {child.pronoun()} used {remedy.label} by acting this way: {remedy.action}. The fix worked because it matched the true cause of the dryness."
        ),
    ]
    if outcome == "bloomed":
        qa.append((
            "What did the moon-seed turn into at the end?",
            "It transformed into a silver vine with lantern flowers. That shining change proved the child had solved the mystery in time and cared for the seed properly."
        ))
        qa.append((
            "What lesson did the elder teach?",
            f"{elder.label_word.capitalize()} taught that kindness must be timely, not just well meant. {child.id} learned that careful love means noticing a problem and answering it before it grows worse."
        ))
    else:
        qa.append((
            "What happened because the child waited too long?",
            "The moon-seed hardened and transformed into a small gray stone bead instead of a vine. The sad change showed that some living things cannot wait forever after their need is known."
        ))
        qa.append((
            "Why is the story cautionary?",
            f"It warns that solving a mystery late can still bring loss. {child.id} found the right answer, but delay let the seed grow too hard to bloom."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["culprit_cfg"].tags) | set(f["remedy_cfg"].tags) | set(f["water_cfg"].tags)
    tags.add("thirst")
    if "clay" in tags or "shade" in tags or "shelf" in tags:
        tags.add("repair")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} delay={world.facts.get('delay')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="courtyard",
        culprit="goat",
        remedy="shelf",
        water="dew",
        child_name="Mira",
        child_gender="girl",
        elder="grandmother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        setting="porch",
        culprit="crack",
        remedy="clay_patch",
        water="springwater",
        child_name="Niko",
        child_gender="boy",
        elder="grandfather",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="courtyard",
        culprit="sun",
        remedy="shade_cloth",
        water="wellwater",
        child_name="Tala",
        child_gender="girl",
        elder="grandmother",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="wellside",
        culprit="goat",
        remedy="shelf",
        water="wellwater",
        child_name="Ilan",
        child_gender="boy",
        elder="grandfather",
        trait="earnest",
        delay=2,
    ),
    StoryParams(
        setting="porch",
        culprit="sun",
        remedy="shade_cloth",
        water="dew",
        child_name="Lina",
        child_gender="girl",
        elder="grandmother",
        trait="patient",
        delay=2,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% reasonableness gate
valid(S, C, R) :- setting(S), culprit(C), remedy(R), affords(S, C), fixes(R, C).

% outcome model
limit(C, U + 1) :- urgency(C, U).
bloomed :- chosen_culprit(C), delay(D), limit(C, L), D < L.
stone   :- chosen_culprit(C), delay(D), limit(C, L), D >= L.

outcome(bloomed) :- bloomed.
outcome(stone)   :- stone.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("urgency", cid, culprit.urgency))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for cid in sorted(remedy.fixes):
            lines.append(asp.fact("fixes", rid, cid))
    for wid in WATERS:
        lines.append(asp.fact("water", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
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

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if "smoke" not in buf.getvalue() or child_safe_missing(sample.story):
            raise StoryError("smoke emit failed or story text looked broken")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def child_safe_missing(story: str) -> bool:
    bad_fragments = ["{", "}", "None", "  "]
    return any(fragment in story for fragment in bad_fragments)


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a thirsty magic seed, a mystery to solve, and a timely or late transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--water", choices=WATERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how many days pass before the child acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    culprit = CULPRITS.get(args.culprit) if args.culprit else None
    remedy = REMEDIES.get(args.remedy) if args.remedy else None

    if setting and culprit and not culprit_in_setting(setting, culprit):
        raise StoryError(explain_rejection(setting, culprit, remedy))
    if culprit and remedy and not remedy_fits(culprit, remedy):
        raise StoryError(explain_rejection(setting, culprit, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, remedy_id = rng.choice(sorted(combos))
    water_id = args.water or rng.choice(sorted(WATERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        remedy=remedy_id,
        water=water_id,
        child_name=child_name,
        child_gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.water not in WATERS:
        raise StoryError(f"(Unknown water source: {params.water})")

    setting = SETTINGS[params.setting]
    culprit = CULPRITS[params.culprit]
    remedy = REMEDIES[params.remedy]
    water = WATERS[params.water]

    if not culprit_in_setting(setting, culprit) or not remedy_fits(culprit, remedy):
        raise StoryError(explain_rejection(setting, culprit, remedy))

    world = tell(
        setting=setting,
        culprit=culprit,
        remedy=remedy,
        water=water,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, culprit, remedy) combos:\n")
        for setting, culprit, remedy in combos:
            print(f"  {setting:10} {culprit:8} {remedy}")
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
            header = f"### {p.child_name}: {p.culprit} at {p.setting} with {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
