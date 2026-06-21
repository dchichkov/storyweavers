#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py
================================================================================

A standalone story world for a gentle bedtime tale shaped by magic and
foreshadowing: a child prepares a small moonlit bedtime ritual, an omen warns
that a little scoundrel is near, and the family must either prevent a theft or
win the magic object back before the whole sleepy plan is a goner.

This world models:
- typed entities with physical meters and emotional memes,
- a short causal chain for loss, worry, and recovery,
- an explicit reasonableness gate over which scoundrels plausibly steal which
  treasures in which places,
- a Python/ASP parity check,
- state-grounded prose and three Q&A sets.

Run it
------
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py --place porch --scoundrel magpie --treasure moonbell
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py --response warm_milk
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scoundrel_goner_magic_foreshadowing_bedtime_story.py --verify
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
CAREFUL_TRAITS = {"careful", "patient", "cautious"}


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


@dataclass
class Place:
    id: str
    label: str
    opening: str
    bedtime_image: str
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
class Scoundrel:
    id: str
    label: str
    phrase: str
    likes: str
    speed: int
    omen: str
    omen_strength: int
    sneak: str
    carry: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    tag: str
    magic: str
    glow: str
    safe_place: str
    ending: str
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
    label: str
    sense: int
    power: int
    works_for: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "omen_seen": False,
            "theft_happened": False,
            "recovered": False,
            "outcome": "",
        }

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
        clone = World(self.place)
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


def _r_missing_causes_worry(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.entities.get("treasure")
    child = world.entities.get("child")
    if treasure is None or child is None:
        return out
    if treasure.meters["missing"] < THRESHOLD:
        return out
    sig = ("worry_missing", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__missing__")
    return out


def _r_recovered_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.entities.get("treasure")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if treasure is None or child is None or helper is None:
        return out
    if treasure.meters["recovered"] < THRESHOLD:
        return out
    sig = ("relief_recovered", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["trust"] += 1
    out.append("__recovered__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_causes_worry", tag="emotion", apply=_r_missing_causes_worry),
    Rule(name="recovered_brings_relief", tag="emotion", apply=_r_recovered_brings_relief),
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


def treasure_at_risk(place: Place, scoundrel: Scoundrel, treasure: Treasure) -> bool:
    return scoundrel.id in place.affords and scoundrel.likes == treasure.tag


def sensible_responses() -> list[Response]:
    return [
        response
        for response in RESPONSES.values()
        if response.sense >= SENSE_MIN
    ]


def response_works(response: Response, scoundrel: Scoundrel) -> bool:
    return scoundrel.id in response.works_for


def chase_severity(scoundrel: Scoundrel, delay: int) -> int:
    return scoundrel.speed + delay


def is_recovered(response: Response, scoundrel: Scoundrel, delay: int) -> bool:
    return response_works(response, scoundrel) and response.power >= chase_severity(scoundrel, delay)


def would_avert(trait: str, scoundrel: Scoundrel) -> bool:
    return trait in CAREFUL_TRAITS and scoundrel.omen_strength >= 2


def predict_trouble(world: World, scoundrel: Scoundrel, treasure: Treasure, response: Response, delay: int) -> dict:
    if would_avert(world.facts["trait"], scoundrel):
        return {"averted": True, "recovered": True, "severity": 0}
    recovered = is_recovered(response, scoundrel, delay)
    return {"averted": False, "recovered": recovered, "severity": chase_severity(scoundrel, delay)}


def introduce(world: World, child: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"At bedtime, {world.place.opening}. {child.id} carried {treasure.phrase}, "
        f"because {treasure.magic}."
    )
    world.say(
        f"{helper.label_word.capitalize()} said the little treasure {treasure.glow}, "
        f"and that was how the place always began to feel ready for sleep."
    )


def foreshadow(world: World, child: Entity, helper: Entity, scoundrel: Scoundrel, treasure: Treasure) -> None:
    world.facts["omen_seen"] = True
    child.memes["wonder"] += 1
    helper.memes["caution"] += 1
    world.say(scoundrel.omen)
    world.say(
        f'{helper.label_word.capitalize()} looked that way and whispered, '
        f'"That is the sort of sign a little scoundrel leaves behind."'
    )
    world.say(
        f'"Best tuck {treasure.label} into {treasure.safe_place}," '
        f'{helper.pronoun()} added. "If it wanders off tonight, our sleepy plan will be a goner."'
    )


def dismiss_or_heed(world: World, child: Entity, treasure: Treasure, scoundrel: Scoundrel) -> bool:
    careful = would_avert(world.facts["trait"], scoundrel)
    if careful:
        child.memes["care"] += 1
        world.say(
            f"{child.id} nodded, slipped {treasure.label} into {treasure.safe_place}, "
            f"and listened to the small warning in the air."
        )
        return True
    child.memes["confidence"] += 1
    world.say(
        f'But {child.id} gave a sleepy little shrug. "It will be fine," '
        f"{child.pronoun()} said, setting {treasure.label} down for just one minute."
    )
    return False


def avert_scene(world: World, child: Entity, helper: Entity, scoundrel: Scoundrel, treasure: Treasure) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"A shadow rustled near the railing, and {scoundrel.phrase} peeped out. "
        f"But there was nothing to snatch, so the scoundrel flicked away into the dark."
    )
    world.say(
        f"{helper.label_word.capitalize()} smiled. "
        f'"Foreshadowing only helps if we listen," {helper.pronoun()} said gently.'
    )


def steal(world: World, child: Entity, scoundrel: Scoundrel, treasure_ent: Entity, treasure: Treasure) -> None:
    treasure_ent.meters["missing"] += 1
    treasure_ent.attrs["holder"] = scoundrel.id
    world.facts["theft_happened"] = True
    propagate(world, narrate=False)
    world.say(
        f"Just then, {scoundrel.sneak}. In a blink, {scoundrel.phrase} grabbed "
        f"{treasure.label} and {scoundrel.carry}."
    )
    world.say(
        f"{child.id} gasped. Without it, the bedtime magic suddenly felt far away."
    )


def pursue(world: World, child: Entity, helper: Entity) -> None:
    child.memes["hope"] += 1
    helper.memes["resolve"] += 1
    world.say(
        f'{helper.label_word.capitalize()} took {child.id} by the hand. '
        f'"Come softly," {helper.pronoun()} said. "We will not shout at the night. We will fix it the wise way."'
    )


def recover(world: World, helper: Entity, scoundrel: Scoundrel, treasure_ent: Entity, treasure: Treasure, response: Response) -> None:
    treasure_ent.meters["missing"] = 0.0
    treasure_ent.meters["recovered"] += 1
    treasure_ent.attrs["holder"] = "child"
    world.facts["recovered"] = True
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {response.text.format(scoundrel=scoundrel.label, treasure=treasure.label)}."
    )
    world.say(
        f"Soon {treasure.label} was back in warm hands, and the night seemed to let out a soft breath."
    )


def lose(world: World, helper: Entity, scoundrel: Scoundrel, treasure_ent: Entity, treasure: Treasure, response: Response) -> None:
    world.say(
        f"{helper.label_word.capitalize()} {response.fail.format(scoundrel=scoundrel.label, treasure=treasure.label)}."
    )
    world.say(
        f"By then, {scoundrel.phrase} had tucked the treasure too deep away, and tonight's little wonder was truly a goner."
    )


def lesson_happy(world: World, child: Entity, helper: Entity, treasure: Treasure) -> None:
    child.memes["lesson"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id}. '
        f'"Magic likes kind hands," {helper.pronoun()} said, "but it also likes careful ones."'
    )
    world.say(
        f"{child.id} held {treasure.label} close and promised to mind the next warning before it had to become trouble."
    )


def ending_happy(world: World, child: Entity, helper: Entity, treasure: Treasure) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then {child.id} used {treasure.label}, and {treasure.ending}. {world.place.bedtime_image}"
    )
    world.say(
        f"Soon even {helper.label_word} was smiling into the hush, and the whole place felt sleepy, mended, and safe."
    )


def lesson_sad(world: World, child: Entity, helper: Entity, treasure: Treasure) -> None:
    child.memes["lesson"] += 1
    child.memes["sadness"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{helper.label_word.capitalize()} wrapped an arm around {child.id}. '
        f'"The magic can wait until tomorrow," {helper.pronoun()} murmured. "You are not a goner. Only our little plan is."'
    )
    world.say(
        f"{child.id} leaned close and learned that omens matter because they whisper before trouble shouts."
    )


def ending_sad(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"That night they went to bed without the usual sparkle. Still, {place.bedtime_image.lower()}"
    )
    world.say(
        f"And with {helper.label_word}'s hand in {child.id}'s, the room was quiet enough for sleep and wise enough for tomorrow."
    )


def tell(
    place: Place,
    scoundrel: Scoundrel,
    treasure: Treasure,
    response: Response,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World(place=place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    treasure_ent = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        role="treasure",
        attrs={"holder": "child"},
        tags=set(treasure.tags),
    ))
    world.add(Entity(
        id="scoundrel",
        kind="character",
        type="animal",
        label=scoundrel.label,
        role="scoundrel",
        attrs={"speed": scoundrel.speed},
        tags=set(scoundrel.tags),
    ))
    world.facts["trait"] = trait

    introduce(world, child, helper, treasure)
    world.para()
    foreshadow(world, child, helper, scoundrel, treasure)
    heeded = dismiss_or_heed(world, child, treasure, scoundrel)

    if heeded:
        world.para()
        avert_scene(world, child, helper, scoundrel, treasure)
        world.para()
        lesson_happy(world, child, helper, treasure)
        ending_happy(world, child, helper, treasure)
        severity = 0
        outcome = "averted"
    else:
        world.para()
        steal(world, child, scoundrel, treasure_ent, treasure)
        pursue(world, child, helper)
        severity = chase_severity(scoundrel, delay)
        treasure_ent.meters["severity"] = float(severity)
        got_back = is_recovered(response, scoundrel, delay)
        world.para()
        if got_back:
            recover(world, helper, scoundrel, treasure_ent, treasure, response)
            lesson_happy(world, child, helper, treasure)
            world.para()
            ending_happy(world, child, helper, treasure)
            outcome = "recovered"
        else:
            lose(world, helper, scoundrel, treasure_ent, treasure, response)
            lesson_sad(world, child, helper, treasure)
            world.para()
            ending_sad(world, child, helper, place)
            outcome = "gone"

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        scoundrel=scoundrel,
        treasure_cfg=treasure,
        treasure=treasure_ent,
        response=response,
        severity=severity,
        delay=delay,
        outcome=outcome,
        promised=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "porch": Place(
        id="porch",
        label="the moon porch",
        opening="the moon porch was washed in pale silver, and the rocking chair made the tiniest creak",
        bedtime_image="The porch boards glowed softly under the moon, and the crickets sang as if they had been waiting all along",
        affords={"magpie", "kitten"},
    ),
    "garden": Place(
        id="garden",
        label="the sleepy garden",
        opening="the sleepy garden smelled of mint and damp earth, with stars caught in the birdbath",
        bedtime_image="The mint leaves nodded in the dark, and the garden lay down under its quilt of dew",
        affords={"magpie", "mouse"},
    ),
    "nursery": Place(
        id="nursery",
        label="the nursery window seat",
        opening="the nursery window seat held a stripe of moonlight and a heap of pillows",
        bedtime_image="The curtains settled still, and the nursery looked as calm as a tucked-in nest",
        affords={"mouse", "kitten"},
    ),
}

SCOUNDRELS = {
    "magpie": Scoundrel(
        id="magpie",
        label="magpie",
        phrase="the magpie",
        likes="shiny",
        speed=2,
        omen="Near the rail, one silver feather lay where no feather had been before.",
        omen_strength=2,
        sneak="a black-and-white flutter dipped out of the dark",
        carry="flapped up to the gutter with it",
        tags={"magpie", "bird", "foreshadowing"},
    ),
    "mouse": Scoundrel(
        id="mouse",
        label="mouse",
        phrase="the mouse",
        likes="sweet",
        speed=1,
        omen="By the flowerpot, three neat crumbs sat in a moonlit row.",
        omen_strength=2,
        sneak="a tiny whiskered nose popped from the shadows",
        carry="zipped behind the pot with it",
        tags={"mouse", "crumbs", "foreshadowing"},
    ),
    "kitten": Scoundrel(
        id="kitten",
        label="kitten",
        phrase="the kitten",
        likes="soft",
        speed=1,
        omen="A curl of pale fluff drifted across the floor and caught on a slipper.",
        omen_strength=1,
        sneak="a velvet paw slid out from under the bench",
        carry="bounded off under the chair with it",
        tags={"kitten", "soft", "foreshadowing"},
    ),
}

TREASURES = {
    "moonbell": Treasure(
        id="moonbell",
        label="moonbell",
        phrase="a little moonbell on a blue cord",
        tag="shiny",
        magic="its silver ring called the drowsy glowbugs to their lantern leaves",
        glow="rang with a bright, clear note that made even the shadows sit politely",
        safe_place="the buttoned pocket of her robe",
        ending="tiny glowbugs floated home in a sleepy circle",
        tags={"moonbell", "magic", "shiny"},
    ),
    "honeycake": Treasure(
        id="honeycake",
        label="honeycake",
        phrase="a warm honeycake wrapped in a napkin of stars",
        tag="sweet",
        magic="its sweet steam coaxed the dream-mice into their little walnut beds",
        glow="let a cozy smell drift out, as if the room itself had started to yawn",
        safe_place="the covered tin by the rocking chair",
        ending="the dream-mice tucked themselves away with full bellies and drooping whiskers",
        tags={"honeycake", "magic", "sweet"},
    ),
    "cloudribbon": Treasure(
        id="cloudribbon",
        label="cloud ribbon",
        phrase="a cloud ribbon soft as a sigh",
        tag="soft",
        magic="its floating weave tied the wandering pillow-dreams gently back to bed",
        glow="seemed to hum in the air, light as a sleepy breath",
        safe_place="the cedar box with the brass clasp",
        ending="the pillow-dreams settled into a neat, moon-pale row",
        tags={"cloudribbon", "magic", "soft"},
    ),
}

RESPONSES = {
    "mirror_lure": Response(
        id="mirror_lure",
        label="mirror lure",
        sense=3,
        power=2,
        works_for={"magpie"},
        text="held up a hand mirror, and the {scoundrel} traded {treasure} for the better sparkle at once",
        fail="tried a hand mirror, but the {scoundrel} had already hidden {treasure} too far away to tempt back",
        qa_text="used a little mirror to lure the magpie into trading the treasure back",
        tags={"mirror", "magic_fix"},
    ),
    "crumb_trail": Response(
        id="crumb_trail",
        label="crumb trail",
        sense=3,
        power=1,
        works_for={"mouse"},
        text="set down a neat trail of sugared crumbs, and the {scoundrel} forgot all about {treasure} and came trotting back",
        fail="set down a crumb trail, but the {scoundrel} had already whisked {treasure} into a crack too small to reach",
        qa_text="made a crumb trail so the mouse came back and dropped the treasure",
        tags={"crumbs", "magic_fix"},
    ),
    "warm_milk": Response(
        id="warm_milk",
        label="warm milk",
        sense=3,
        power=1,
        works_for={"kitten"},
        text="poured a saucer of warm milk, and the {scoundrel} left {treasure} to lap the better comfort",
        fail="offered warm milk, but the {scoundrel} had already curled up somewhere hidden with {treasure}",
        qa_text="used a saucer of warm milk so the kitten let go of the treasure",
        tags={"milk", "magic_fix"},
    ),
    "chase_shout": Response(
        id="chase_shout",
        label="chase and shout",
        sense=1,
        power=0,
        works_for={"magpie", "mouse", "kitten"},
        text="ran and shouted until the whole place echoed",
        fail="ran and shouted, which only made the night noisier and the scoundrel faster",
        qa_text="tried chasing and shouting",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ivy", "Tessa", "Lucy", "Rose"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Ben", "Noah", "Leo"]
TRAITS = ["careful", "curious", "sleepy", "patient", "cautious", "dreamy"]


@dataclass
class StoryParams:
    place: str
    scoundrel: str
    treasure: str
    response: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
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


KNOWLEDGE = {
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a little hint before something important happens later. The hint helps the later trouble feel surprising and sensible at the same time.",
        )
    ],
    "magic": [
        (
            "What is magic in a bedtime story?",
            "Magic in a bedtime story is a gentle, make-believe power that changes the feeling of the world. It often makes ordinary things glow, sing, or help sleepy creatures settle down.",
        )
    ],
    "magpie": [
        (
            "Why might a magpie take something shiny?",
            "Magpies are birds that often notice bright, shiny things. In stories, that makes a bell or sparkle especially tempting to them.",
        )
    ],
    "mouse": [
        (
            "Why would a mouse follow crumbs?",
            "A mouse has a tiny nose that is very good at finding food. A trail of crumbs can lead it exactly where you want it to go.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten grab something soft?",
            "Kittens like batting, chasing, and curling up with soft things. A ribbon or fluffy cloth can seem like a toy to them.",
        )
    ],
    "moonbell": [
        (
            "What is a moonbell?",
            "A moonbell is a make-believe little bell for a bedtime story. Its soft ring can be imagined as a signal for sleepy magic.",
        )
    ],
    "honeycake": [
        (
            "What is honeycake?",
            "Honeycake is a sweet cake flavored with honey. In a story, its warm smell can make a place feel cozy and calm.",
        )
    ],
    "cloudribbon": [
        (
            "What is a cloud ribbon?",
            "A cloud ribbon is a pretend ribbon described as soft and light as a cloud. Bedtime stories use things like that to make the world feel dreamy.",
        )
    ],
    "mirror": [
        (
            "How can a mirror lure a shiny-loving bird?",
            "A little mirror flashes light back at the bird. If the bird likes sparkle more than what it stole, it may come closer to the brighter thing.",
        )
    ],
    "crumbs": [
        (
            "What is a crumb trail?",
            "A crumb trail is a line of tiny food pieces placed one after another. It can gently lead a hungry animal along a path.",
        )
    ],
    "milk": [
        (
            "Why might warm milk calm a kitten?",
            "Warm milk feels cozy and comforting in stories. A sleepy kitten may stop chasing and settle down for the nicer treat.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "foreshadowing",
    "magic",
    "magpie",
    "mouse",
    "kitten",
    "moonbell",
    "honeycake",
    "cloudribbon",
    "mirror",
    "crumbs",
    "milk",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for scoundrel_id, scoundrel in SCOUNDRELS.items():
            for treasure_id, treasure in TREASURES.items():
                if treasure_at_risk(place, scoundrel, treasure):
                    combos.append((place_id, scoundrel_id, treasure_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    scoundrel = world.facts["scoundrel"]
    treasure = world.facts["treasure_cfg"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    base = (
        f'Write a short bedtime story with magic and foreshadowing. Include the words "scoundrel" and "goner", '
        f"and set it on {place.label} with a {scoundrel.label} and a {treasure.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {child.id} notices an omen, listens to a warning, and keeps a little bedtime magic safe before the scoundrel can steal it.",
            f"Write a calm bedtime tale where foreshadowing helps a child prevent trouble, and the ending proves that careful listening can protect a magical ritual.",
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell a bedtime story where {child.id} ignores a warning sign, a little scoundrel steals the magical object, and a wise grown-up gets it back in a gentle way.",
            f"Write a child-facing magical story with a clear omen, a small theft, and a cozy ending where the bedtime ritual still happens at last.",
        ]
    return [
        base,
        f"Tell a softer sad bedtime story where an omen is ignored, the magical object is lost, and the child learns why warnings matter before sleep.",
        f"Write a magical cautionary tale where the bedtime plan becomes a goner for one night, but the ending is still loving and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    scoundrel = world.facts["scoundrel"]
    treasure = world.facts["treasure_cfg"]
    response = world.facts["response"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    pw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and a little {scoundrel.label}. The bedtime trouble starts because the magical {treasure.label} matters to everyone in that quiet place.",
        ),
        (
            f"What was magical about the {treasure.label}?",
            f"The {treasure.label} was magical because {treasure.magic}. That made losing it matter for the whole bedtime ritual, not just for one object.",
        ),
        (
            "What was the foreshadowing hint?",
            f"The hint was this: {scoundrel.omen} It warned that the {scoundrel.label} was probably nearby before the real trouble began.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How did {child.id} stop the problem before it happened?",
                f"{child.id} listened to the warning and tucked the {treasure.label} into {treasure.safe_place}. Because the treasure was hidden safely, the scoundrel found nothing to steal and the trouble never truly began.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the bedtime magic still working: {treasure.ending}. The final image shows that listening early changed the whole night.",
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when the scoundrel took the {treasure.label}?",
                f"{child.id} grew worried at once because the bedtime magic could not happen properly without it. That is why {pw} led the search gently instead of shouting into the dark.",
            )
        )
        qa.append(
            (
                f"How did {child.id}'s {pw} get the treasure back?",
                f"{pw.capitalize()} {response.qa_text}. The fix worked because it matched what that scoundrel wanted better than the stolen treasure itself.",
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{child.id} learned that omens matter and that careful listening can protect a magical plan. The warning came before the theft, so the lesson is about noticing danger early, not only fixing it later.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the bedtime plan become a goner for that night?",
                f"It became a goner because the warning was ignored, the {scoundrel.label} stole the {treasure.label}, and it could not be recovered in time. Without the magical object, the usual bedtime wonder had to wait for another night.",
            )
        )
        qa.append(
            (
                "Was the ending still safe?",
                f"Yes. The ending was sad but safe because {child.id} was comforted by {pw} and went to bed loved. The loss was only the little ritual, not the people in the story.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"foreshadowing", "magic"}
    scoundrel = world.facts["scoundrel"]
    treasure = world.facts["treasure_cfg"]
    response = world.facts["response"]
    tags |= set(scoundrel.tags)
    tags |= set(treasure.tags)
    if world.facts["outcome"] == "recovered":
        tags |= set(response.tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if entity.role:
            parts.append(f"role={entity.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v or v == 0}
            if shown:
                parts.append(f"attrs={shown}")
        if entity.tags:
            parts.append(f"tags={sorted(entity.tags)}")
        lines.append(f"  {entity.id:10} ({entity.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        scoundrel="magpie",
        treasure="moonbell",
        response="mirror_lure",
        child_name="Mina",
        child_gender="girl",
        helper_type="grandmother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        place="nursery",
        scoundrel="mouse",
        treasure="honeycake",
        response="crumb_trail",
        child_name="Owen",
        child_gender="boy",
        helper_type="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        place="porch",
        scoundrel="kitten",
        treasure="cloudribbon",
        response="warm_milk",
        child_name="Lila",
        child_gender="girl",
        helper_type="father",
        trait="dreamy",
        delay=1,
    ),
    StoryParams(
        place="porch",
        scoundrel="magpie",
        treasure="moonbell",
        response="mirror_lure",
        child_name="Theo",
        child_gender="boy",
        helper_type="grandfather",
        trait="sleepy",
        delay=1,
    ),
]


def explain_rejection(place: Place, scoundrel: Scoundrel, treasure: Treasure) -> str:
    if scoundrel.id not in place.affords:
        possible = ", ".join(sorted(place.affords))
        return (
            f"(No story: {place.label} does not plausibly host a {scoundrel.label} in this world. "
            f"Try a scoundrel that fits this place, such as: {possible}.)"
        )
    if scoundrel.likes != treasure.tag:
        return (
            f"(No story: the {scoundrel.label} goes after {scoundrel.likes} things, but {treasure.label} is a {treasure.tag} treasure. "
            f"The theft would feel ungrounded, so this combination is refused.)"
        )
    return "(No story: this combination does not make a reasonable bedtime theft.)"


def explain_response(response_id: str, scoundrel_id: str) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). The world prefers calm, matching fixes.)"
        )
    if scoundrel_id not in response.works_for:
        return (
            f"(Refusing response '{response_id}': it does not fit the {scoundrel_id}. "
            f"Choose a response that matches what this scoundrel would actually follow.)"
        )
    return "(Refusing response: it does not fit this scenario.)"


def outcome_of(params: StoryParams) -> str:
    scoundrel = SCOUNDRELS[params.scoundrel]
    if would_avert(params.trait, scoundrel):
        return "averted"
    response = RESPONSES[params.response]
    return "recovered" if is_recovered(response, scoundrel, params.delay) else "gone"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risk(P, S, T) :- place(P), scoundrel(S), treasure(T), affords(P, S), likes(S, K), treasure_tag(T, K).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

% --- outcome model ---------------------------------------------------------
careful_now :- chosen_trait(T), careful_trait(T), chosen_scoundrel(S), omen_strength(S, O), O >= 2.
severity(Sp + D) :- chosen_scoundrel(S), speed(S, Sp), delay(D).
usable_response :- chosen_response(R), chosen_scoundrel(S), works_for(R, S).
recovered :- usable_response, chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- careful_now.
outcome(recovered) :- not careful_now, recovered.
outcome(gone) :- not careful_now, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for scoundrel_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, scoundrel_id))
    for scoundrel_id, scoundrel in SCOUNDRELS.items():
        lines.append(asp.fact("scoundrel", scoundrel_id))
        lines.append(asp.fact("likes", scoundrel_id, scoundrel.likes))
        lines.append(asp.fact("speed", scoundrel_id, scoundrel.speed))
        lines.append(asp.fact("omen_strength", scoundrel_id, scoundrel.omen_strength))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("treasure_tag", treasure_id, treasure.tag))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for sid in sorted(response.works_for):
            lines.append(asp.fact("works_for", response_id, sid))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show risk/3.\n#show sensible/1."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_scoundrel", params.scoundrel),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_trait", params.trait),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    py_sens = {response.id for response in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append(params)
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a magical treasure, a foreshadowing omen, and a tiny scoundrel."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--scoundrel", choices=SCOUNDRELS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the scoundrel gets to hide before the fix")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, scoundrel, treasure) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.scoundrel and args.treasure:
        place = PLACES[args.place]
        scoundrel = SCOUNDRELS[args.scoundrel]
        treasure = TREASURES[args.treasure]
        if not treasure_at_risk(place, scoundrel, treasure):
            raise StoryError(explain_rejection(place, scoundrel, treasure))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.scoundrel is None or combo[1] == args.scoundrel)
        and (args.treasure is None or combo[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, scoundrel_id, treasure_id = rng.choice(sorted(combos))

    possible_responses = [
        rid
        for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and scoundrel_id in response.works_for
    ]
    if args.response is not None:
        if args.response not in RESPONSES:
            raise StoryError("(Unknown response.)")
        if RESPONSES[args.response].sense < SENSE_MIN or scoundrel_id not in RESPONSES[args.response].works_for:
            raise StoryError(explain_response(args.response, scoundrel_id))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(possible_responses))

    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        scoundrel=scoundrel_id,
        treasure=treasure_id,
        response=response_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.scoundrel not in SCOUNDRELS:
        raise StoryError(f"(Invalid scoundrel: {params.scoundrel})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Invalid treasure: {params.treasure})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")

    place = PLACES[params.place]
    scoundrel = SCOUNDRELS[params.scoundrel]
    treasure = TREASURES[params.treasure]
    response = RESPONSES[params.response]

    if not treasure_at_risk(place, scoundrel, treasure):
        raise StoryError(explain_rejection(place, scoundrel, treasure))
    if response.sense < SENSE_MIN or scoundrel.id not in response.works_for:
        raise StoryError(explain_response(params.response, scoundrel.id))

    world = tell(
        place=place,
        scoundrel=scoundrel,
        treasure=treasure,
        response=response,
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show risk/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, scoundrel, treasure) combos:\n")
        for place_id, scoundrel_id, treasure_id in combos:
            print(f"  {place_id:8} {scoundrel_id:8} {treasure_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.scoundrel} and {p.treasure} at {p.place} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
