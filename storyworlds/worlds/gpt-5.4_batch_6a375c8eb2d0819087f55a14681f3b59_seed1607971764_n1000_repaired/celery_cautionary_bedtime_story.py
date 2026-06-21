#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py
=============================================================

A standalone story world about a child who wants to tuck a celery snack into bed
after bedtime has already begun. The world prefers plausible bedtime risks and
sensible fixes: a damp or sticky celery snack hidden in soft bedding makes a
lumpy mess, while a snack kept on a kitchen plate does not create enough danger
for a cautionary story and is refused.

This is a small cautionary bedtime domain:
- setup: warm bedtime, soft bed, leftover celery from supper
- tension: the child wants to hide the celery nearby for one more nibble
- turn: the celery gets squished or smeared into the bedding
- resolution: a grown-up fixes the bed the sensible way, or bedtime turns rough
  and uncomfortable until the lesson is learned

Run it
------
    python storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py --snack celery_hummus --spot pillowcase
    python storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py --spot bedside_plate
    python storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/celery_cautionary_bedtime_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class CelerySnack:
    id: str
    label: str
    phrase: str
    wetness: int
    stickiness: int
    smell: str
    tags: set[str] = field(default_factory=set)

    @property
    def severity(self) -> int:
        return self.wetness + self.stickiness
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
class BedSpot:
    id: str
    label: str
    phrase: str
    fabric: bool
    softness: int
    under_body: bool
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


def _r_bed_mess(world: World) -> list[str]:
    snack = world.entities.get("snack")
    spot = world.entities.get("spot")
    bed = world.entities.get("bed")
    child = world.entities.get("child")
    if not snack or not spot or not bed or not child:
        return []
    if snack.meters["hidden"] < THRESHOLD or snack.meters["squished"] < THRESHOLD:
        return []
    sig = ("bed_mess",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bed.meters["wet"] += snack.meters["wetness"]
    bed.meters["sticky"] += snack.meters["stickiness"]
    bed.meters["lumpy"] += max(1.0, spot.meters["softness"])
    child.memes["worry"] += 1
    child.memes["discomfort"] += 1
    return ["__mess__"]


def _r_parent_work(world: World) -> list[str]:
    bed = world.entities.get("bed")
    parent = world.entities.get("parent")
    if not bed or not parent:
        return []
    if bed.meters["wet"] < THRESHOLD and bed.meters["sticky"] < THRESHOLD:
        return []
    sig = ("wash_work",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.meters["workload"] += 1
    return []


def _r_bad_sleep(world: World) -> list[str]:
    bed = world.entities.get("bed")
    child = world.entities.get("child")
    if not bed or not child:
        return []
    if bed.meters["lumpy"] < THRESHOLD:
        return []
    sig = ("bad_sleep",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["sleep_loss"] += 1
    child.memes["sleepy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bed_mess", tag="physical", apply=_r_bed_mess),
    Rule(name="parent_work", tag="physical", apply=_r_parent_work),
    Rule(name="bad_sleep", tag="physical", apply=_r_bad_sleep),
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


def risky_combo(snack: CelerySnack, spot: BedSpot) -> bool:
    return spot.fabric and spot.under_body and snack.severity >= 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def mess_severity(snack: CelerySnack, spot: BedSpot, delay: int) -> int:
    return snack.severity + spot.softness + delay


def is_contained(response: Response, snack: CelerySnack, spot: BedSpot, delay: int) -> bool:
    return response.power >= mess_severity(snack, spot, delay)


def predict_mess(world: World, snack_cfg: CelerySnack, spot_cfg: BedSpot) -> dict:
    sim = world.copy()
    sim.get("snack").meters["wetness"] = float(snack_cfg.wetness)
    sim.get("snack").meters["stickiness"] = float(snack_cfg.stickiness)
    sim.get("spot").meters["softness"] = float(spot_cfg.softness)
    _do_hide(sim, narrate=False)
    bed = sim.get("bed")
    return {
        "wet": bed.meters["wet"],
        "sticky": bed.meters["sticky"],
        "lumpy": bed.meters["lumpy"],
        "workload": sim.get("parent").meters["workload"],
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, snack: CelerySnack) -> None:
    child.memes["cozy"] += 1
    child.memes["tempted"] += 1
    world.say(
        f"It was a quiet bedtime, and {child.id}'s room was soft with lamplight. "
        f"{parent.label_word.capitalize()} had already tucked the blanket around {child.pronoun('object')}"
        f" and set a storybook on the quilt."
    )
    world.say(
        f"From supper, one little snack was still on {child.pronoun('possessive')} mind: "
        f"{snack.phrase}. It smelled {snack.smell}, and {child.id} kept thinking about one more nibble."
    )


def bedtime_warning(world: World, child: Entity, parent: Entity, snack: CelerySnack, spot: BedSpot) -> None:
    pred = predict_mess(world, snack, spot)
    world.facts["predicted_wet"] = pred["wet"]
    world.facts["predicted_sticky"] = pred["sticky"]
    world.facts["predicted_lumpy"] = pred["lumpy"]
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"No snacks in bed," {parent.label_word} said softly when {child.id} glanced toward '
        f"{spot.phrase}. \"{snack.label.capitalize()} belongs at the table. In a soft bed, it can get "
        f"squished and leave the sheets wet or sticky.\""
    )
    if pred["workload"] >= THRESHOLD:
        world.say(
            f"{parent.label_word.capitalize()} smoothed the blanket and added, "
            f"\"Then someone has to wash everything instead of resting.\""
        )


def temptation(world: World, child: Entity, snack: CelerySnack, spot: BedSpot) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the room was warm, and the thought of {snack.label} right beside {child.pronoun('object')} "
        f"felt very cozy and very clever. When the hall grew quiet, {child.id} slipped the snack toward {spot.phrase}."
    )


def _do_hide(world: World, narrate: bool = True) -> None:
    snack = world.get("snack")
    snack.meters["hidden"] += 1
    snack.meters["squished"] += 1
    propagate(world, narrate=narrate)


def hide_and_squish(world: World, child: Entity, snack: CelerySnack, spot: BedSpot) -> None:
    _do_hide(world, narrate=False)
    world.say(
        f"{child.id} tucked the {snack.label} into {spot.phrase} and wriggled down into bed."
    )
    world.say(
        f"Then came a tiny crunch. Something cool and damp pressed through the cloth, "
        f"and the nice bed no longer felt quite nice."
    )


def call_parent(world: World, child: Entity, parent: Entity, spot: BedSpot) -> None:
    child.memes["honesty"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}?" {child.id} whispered into the dim room. '
        f"\"There is something squishy in {spot.phrase}.\""
    )


def rescue(world: World, parent: Entity, response: Response, spot: BedSpot) -> None:
    bed = world.get("bed")
    child = world.get("child")
    bed.meters["wet"] = 0.0
    bed.meters["sticky"] = 0.0
    bed.meters["lumpy"] = 0.0
    child.meters["sleep_loss"] = 0.0
    child.memes["discomfort"] = 0.0
    child.memes["relief"] += 1
    parent.meters["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in at once and {response.text.replace('{spot}', spot.label)}."
    )
    world.say(
        "Soon the bed felt smooth again, and the room settled back into a sleepy hush."
    )


def lesson(world: World, child: Entity, parent: Entity, snack: CelerySnack) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed and gave {child.id} a hug. '
        f'"I am glad you told me," {parent.pronoun()} said. "But even something as small as '
        f'{snack.label} can make a bedtime mess when it belongs in the kitchen."'
    )
    world.say(
        f'{child.id} nodded. The warning made sense now that the pillow had gone squishy.'
    )


def safe_end(world: World, child: Entity, parent: Entity, snack: CelerySnack) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} carried the celery back to the kitchen and left a glass of water by the bed instead."
    )
    world.say(
        f"With the sheets smooth, the light low, and no snack tucked anywhere it did not belong, "
        f"{child.id} listened to one more page of the story and drifted to sleep."
    )


def rescue_fail(world: World, parent: Entity, response: Response, spot: BedSpot) -> None:
    child = world.get("child")
    child.memes["worry"] += 1
    child.meters["sleep_loss"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail.replace('{spot}', spot.label)}."
    )
    world.say(
        "The wet place was too spread out, and the bed stayed rumpled and uncomfortable."
    )


def rough_night(world: World, child: Entity, parent: Entity, snack: CelerySnack) -> None:
    child.memes["lesson"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"{child.id} had to finish the night under a spare blanket while the bedding went to the wash."
    )
    world.say(
        f"In the gray morning, the little smell of {snack.label} was gone, but the lesson was not: "
        f"beds are for resting, not for hiding snacks."
    )
    world.say(
        f"That evening, when supper left a few crisp pieces of celery, {child.id} put them on a kitchen plate all by {child.pronoun('self') if False else 'alone'} and never tried to tuck them into bed again."
    )


CELERY_SNACKS = {
    "celery_plain": CelerySnack(
        id="celery_plain",
        label="celery",
        phrase="a few crisp celery sticks",
        wetness=1,
        stickiness=0,
        smell="green and fresh",
        tags={"celery"},
    ),
    "celery_hummus": CelerySnack(
        id="celery_hummus",
        label="celery with hummus",
        phrase="celery spread with a little hummus",
        wetness=1,
        stickiness=1,
        smell="savory and fresh",
        tags={"celery", "hummus"},
    ),
    "celery_cream_cheese": CelerySnack(
        id="celery_cream_cheese",
        label="celery with cream cheese",
        phrase="celery filled with soft cream cheese",
        wetness=1,
        stickiness=2,
        smell="cool and creamy",
        tags={"celery", "cream_cheese"},
    ),
}

BED_SPOTS = {
    "pillowcase": BedSpot(
        id="pillowcase",
        label="the pillowcase",
        phrase="the pillowcase",
        fabric=True,
        softness=2,
        under_body=True,
        tags={"pillow"},
    ),
    "under_quilt": BedSpot(
        id="under_quilt",
        label="the blanket fold",
        phrase="the fold under the quilt",
        fabric=True,
        softness=2,
        under_body=True,
        tags={"blanket"},
    ),
    "pajama_pocket": BedSpot(
        id="pajama_pocket",
        label="the pajama pocket",
        phrase="the little pajama pocket",
        fabric=True,
        softness=1,
        under_body=True,
        tags={"pajamas"},
    ),
    "bedside_plate": BedSpot(
        id="bedside_plate",
        label="the bedside plate",
        phrase="the bedside plate",
        fabric=False,
        softness=0,
        under_body=False,
        tags={"plate"},
    ),
}

RESPONSES = {
    "change_bedding": Response(
        id="change_bedding",
        sense=3,
        power=6,
        text="lifted the blanket, found the hidden snack in {spot}, and changed the damp bedding for clean, cool sheets",
        fail="found the snack in {spot}, but there were no fresh sheets ready and the bed could not be fully fixed yet",
        qa_text="changed the bedding and took the hidden snack away",
        tags={"sheets", "clean"},
    ),
    "wipe_and_flip": Response(
        id="wipe_and_flip",
        sense=2,
        power=4,
        text="wiped up the smear, turned the pillow over, and straightened the covers as best {subject} could".replace("{subject}", "she"),
        fail="tried to wipe and turn everything, but the damp place had soaked too far through {spot}",
        qa_text="wiped the mess and straightened the bed",
        tags={"clean"},
    ),
    "shake_blanket": Response(
        id="shake_blanket",
        sense=1,
        power=2,
        text="shook out the blanket and hoped that would be enough",
        fail="shook out the blanket, but the wet spot and lumps were still there",
        qa_text="shook out the blanket",
        tags={"blanket"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn", "Noah", "Eli", "Jack", "Owen"]
TRAITS = ["sleepy", "curious", "stubborn", "gentle", "restless", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for snack_id, snack in CELERY_SNACKS.items():
        for spot_id, spot in BED_SPOTS.items():
            if risky_combo(snack, spot):
                combos.append((snack_id, spot_id))
    return combos


@dataclass
class StoryParams:
    snack: str
    spot: str
    response: str
    name: str
    gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "celery": [
        (
            "What is celery?",
            "Celery is a crunchy green vegetable with long stalks. People often eat it raw as a snack or with a dip.",
        )
    ],
    "pillow": [
        (
            "Why should food stay out of a pillow?",
            "A pillow should stay clean and dry so it feels soft under your head. Food can make it lumpy, damp, or smelly.",
        )
    ],
    "blanket": [
        (
            "Why should a blanket stay clean at bedtime?",
            "A clean blanket feels warm and comfortable. If food gets on it, bedtime can feel sticky and unpleasant.",
        )
    ],
    "pajamas": [
        (
            "Why is a pajama pocket not a good place for a snack?",
            "A soft pocket can squash food when you twist and turn. Then the snack can leak onto pajamas and bedding.",
        )
    ],
    "sheets": [
        (
            "Why do sheets need to be changed when they get messy?",
            "Messy sheets can feel wet, sticky, or uncomfortable. Clean sheets help your body rest well at night.",
        )
    ],
    "clean": [
        (
            "Why is it good to tell a grown-up about a bedtime mess right away?",
            "A grown-up can help fix the problem before it gets bigger. Telling quickly is a brave way to keep bedtime calm and safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["celery", "pillow", "blanket", "pajamas", "sheets", "clean"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a cautionary bedtime story for a 3-to-5-year-old that includes the word "celery" '
        f"and features a child hiding {snack.label} in {spot.phrase}."
    )
    if outcome == "contained":
        return [
            base,
            f"Tell a gentle bedtime story where {child.id} sneaks {snack.label} into bed, feels the mistake at once, and a calm parent fixes the bed before sleep.",
            f"Write a cozy cautionary story about a child learning that snacks belong in the kitchen, not under blankets or pillows.",
        ]
    return [
        base,
        f"Tell a bedtime cautionary tale where {child.id} hides {snack.label} in bed, and the night becomes uncomfortable because the mess is not fully fixed.",
        f"Write a soft but firm story that teaches children not to tuck food into bedding, even if the snack seems small and harmless.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    spot = f["spot_cfg"]
    response = f["response_cfg"]
    pw = parent.label_word
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child getting ready for sleep, and {child.pronoun('possessive')} {pw} who helps at bedtime.",
        ),
        (
            f"What did {child.id} want to do with the {snack.label}?",
            f"{child.id} wanted to keep the {snack.label} close for one more nibble and tried to hide it in {spot.phrase}. The idea felt cozy, but it was not safe for the bed.",
        ),
        (
            f"Why did {pw} warn against that?",
            f"{pw.capitalize()} knew the snack could get squished in the soft bedding and make the bed wet, sticky, or lumpy. That would also mean extra washing instead of quiet sleep.",
        ),
        (
            "What changed when the snack went into bed?",
            f"The bed stopped feeling smooth and restful. A tiny crunch and a damp, squishy spot showed that the hidden snack had become a real bedtime problem.",
        ),
    ]
    if f["outcome"] == "contained":
        out.append(
            (
                f"How did {pw} fix the problem?",
                f"{pw.capitalize()} {response.qa_text}. Because the mess was handled quickly, the bed became smooth and comfortable again.",
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. The celery went back to the kitchen, and {child.id} fell asleep in a clean bed after learning the lesson.",
            )
        )
    else:
        out.append(
            (
                f"Could {pw} make the bed comfortable again right away?",
                f"No. {pw.capitalize()} tried to help, but the wet, lumpy mess was too spread out to fix completely that moment. {child.id} had a rougher night because the snack had been hidden in bed.",
            )
        )
        out.append(
            (
                "What did the child learn?",
                f"{child.id} learned that even a small celery snack can spoil bedtime when it is tucked into bedding. The next night, the snack stayed in the kitchen where it belonged.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["snack_cfg"].tags) | set(world.facts["spot_cfg"].tags)
    tags |= set(world.facts["response_cfg"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        snack="celery_plain",
        spot="pillowcase",
        response="change_bedding",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        snack="celery_hummus",
        spot="under_quilt",
        response="wipe_and_flip",
        name="Ben",
        gender="boy",
        parent="father",
        trait="restless",
        delay=0,
    ),
    StoryParams(
        snack="celery_cream_cheese",
        spot="pajama_pocket",
        response="wipe_and_flip",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="stubborn",
        delay=2,
    ),
    StoryParams(
        snack="celery_hummus",
        spot="pillowcase",
        response="change_bedding",
        name="Theo",
        gender="boy",
        parent="father",
        trait="sleepy",
        delay=1,
    ),
]


def explain_rejection(snack: CelerySnack, spot: BedSpot) -> str:
    if not spot.fabric or not spot.under_body:
        return (
            f"(No story: {spot.phrase} is not tucked into the bedding, so hiding {snack.label} there "
            f"does not make a strong bedtime problem. Pick a soft bed spot like the pillowcase or under the quilt.)"
        )
    return (
        f"(No story: {snack.label} in {spot.phrase} does not create enough mess to support this cautionary bedtime story.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def tell(
    snack_cfg: CelerySnack,
    spot_cfg: BedSpot,
    response_cfg: Response,
    *,
    name: str = "Lily",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    bed = world.add(
        Entity(
            id="bed",
            type="bed",
            label="bed",
            attrs={},
        )
    )
    snack = world.add(
        Entity(
            id="snack",
            type="snack",
            label=snack_cfg.label,
            attrs={},
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot_cfg.label,
            attrs={},
        )
    )

    snack.meters["wetness"] = float(snack_cfg.wetness)
    snack.meters["stickiness"] = float(snack_cfg.stickiness)
    spot.meters["softness"] = float(spot_cfg.softness)
    child.memes["sleepy"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["discomfort"] = 0.0
    parent.meters["workload"] = 0.0

    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["snack_cfg"] = snack_cfg
    world.facts["spot_cfg"] = spot_cfg
    world.facts["response_cfg"] = response_cfg

    bedtime_setup(world, child, parent, snack_cfg)
    world.para()
    bedtime_warning(world, child, parent, snack_cfg, spot_cfg)
    temptation(world, child, snack_cfg, spot_cfg)
    world.para()
    hide_and_squish(world, child, snack_cfg, spot_cfg)
    call_parent(world, child, parent, spot_cfg)
    world.para()

    if is_contained(response_cfg, snack_cfg, spot_cfg, delay):
        rescue(world, parent, response_cfg, spot_cfg)
        lesson(world, child, parent, snack_cfg)
        world.para()
        safe_end(world, child, parent, snack_cfg)
        outcome = "contained"
    else:
        rescue_fail(world, parent, response_cfg, spot_cfg)
        rough_night(world, child, parent, snack_cfg)
        outcome = "messy"

    world.facts["outcome"] = outcome
    world.facts["severity"] = mess_severity(snack_cfg, spot_cfg, delay)
    return world


ASP_RULES = r"""
risky(S, P) :- snack(S), spot(P), fabric(P), under_body(P), severity_of(S, V), V >= 2.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P) :- risky(S, P).

mess_severity(V + Sof + D) :-
    chosen_snack(S), severity_of(S, V),
    chosen_spot(P), softness(P, Sof),
    delay(D).

contained :- chosen_response(R), power(R, P), mess_severity(M), P >= M.
outcome(contained) :- contained.
outcome(messy) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, snack in CELERY_SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("severity_of", sid, snack.severity))
    for pid, spot in BED_SPOTS.items():
        lines.append(asp.fact("spot", pid))
        if spot.fabric:
            lines.append(asp.fact("fabric", pid))
        if spot.under_body:
            lines.append(asp.fact("under_body", pid))
        lines.append(asp.fact("softness", pid, spot.softness))
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

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.snack not in CELERY_SNACKS or params.spot not in BED_SPOTS or params.response not in RESPONSES:
        raise StoryError("(No story: unknown params.)")
    return "contained" if is_contained(RESPONSES[params.response], CELERY_SNACKS[params.snack], BED_SPOTS[params.spot], params.delay) else "messy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary bedtime story world about hiding celery in bed."
    )
    ap.add_argument("--snack", choices=CELERY_SNACKS)
    ap.add_argument("--spot", choices=BED_SPOTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long before the parent can fully deal with the mess")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.snack and args.spot:
        snack = CELERY_SNACKS[args.snack]
        spot = BED_SPOTS[args.spot]
        if not risky_combo(snack, spot):
            raise StoryError(explain_rejection(snack, spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.spot is None or combo[1] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, spot_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        snack=snack_id,
        spot=spot_id,
        response=response_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in CELERY_SNACKS:
        raise StoryError(f"(No story: unknown snack '{params.snack}'.)")
    if params.spot not in BED_SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not risky_combo(CELERY_SNACKS[params.snack], BED_SPOTS[params.spot]):
        raise StoryError(explain_rejection(CELERY_SNACKS[params.snack], BED_SPOTS[params.spot]))

    world = tell(
        CELERY_SNACKS[params.snack],
        BED_SPOTS[params.spot],
        RESPONSES[params.response],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    as_valid = set(asp_valid_combos())
    if py_valid == as_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - as_valid:
            print("  only in python:", sorted(py_valid - as_valid))
        if as_valid - py_valid:
            print("  only in clingo:", sorted(as_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    as_sensible = set(asp_sensible())
    if py_sensible == as_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(as_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, spot) combos:\n")
        for snack, spot in combos:
            print(f"  {snack:20} {spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.name}: {p.snack} in {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
