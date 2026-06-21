#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py
============================================================================

A standalone storyworld for a tiny bedtime mystery: a small treasured thing goes
missing, a child follows gentle clues, and a kind act explains the loss.

The world model is state-driven rather than slot-swapped. A child has a bedtime
ritual with a tiny comfort object ("bitsy"), notices it is missing, looks in a
few plausible places, and discovers that another small sleeper needed it more.
The tension turns on uncertainty, not danger: where did bitsy go? The resolution
comes from kindness, with the family making a new bedtime habit that proves what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/bitsy_mystery_to_solve_kindness_bedtime_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    hidden: bool = False
    sleepy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Room:
    id: str
    label: str
    cozy: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    tiny_word: str
    feel: str
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
class SeekerMood:
    id: str
    opening: str
    search_style: str
    comfort_line: str
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
class Recipient:
    id: str
    label: str
    phrase: str
    relation: str
    type: str
    need: str
    clue_text: str
    bedtime_change: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    clue: str
    found_text: str
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
class TransferReason:
    id: str
    action: str
    explanation: str
    kindness: str
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


def _r_missing_worry(world: World) -> list[str]:
    seeker = world.get("seeker")
    bitsy = world.get("bitsy")
    if seeker.memes["searching"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    if bitsy.attrs.get("location") != "seeker":
        world.fired.add(sig)
        seeker.memes["worry"] += 1
        return ["__worry__"]
    return []


def _r_clue_hope(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters["clues"] < THRESHOLD:
        return []
    sig = ("clue_hope", int(seeker.meters["clues"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["hope"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    seeker = world.get("seeker")
    bitsy = world.get("bitsy")
    if bitsy.attrs.get("location") != "recipient":
        return []
    if seeker.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["relief"] += 1
    seeker.memes["worry"] = 0.0
    return []


def _r_kindness_glow(world: World) -> list[str]:
    seeker = world.get("seeker")
    parent = world.get("parent")
    if seeker.memes["shared"] < THRESHOLD:
        return []
    sig = ("kindness_glow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["kindness"] += 1
    parent.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="kindness_glow", tag="social", apply=_r_kindness_glow),
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


def compatible_place(place: HidingPlace, recipient: Recipient) -> bool:
    return place.id in RECIPIENT_TO_PLACES.get(recipient.id, set())


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for room_id in ROOMS:
        for bitsy_id in KEEPSAKES:
            for mood_id in SEEKER_MOODS:
                for rec_id, recipient in RECIPIENTS.items():
                    for place_id, place in PLACES.items():
                        if compatible_place(place, recipient):
                            combos.append((room_id, bitsy_id, mood_id, rec_id, place_id))
    return combos


def predict_story(room_id: str, recipient_id: str, place_id: str) -> dict:
    recipient = RECIPIENTS[recipient_id]
    place = PLACES[place_id]
    return {
        "hidden": compatible_place(place, recipient),
        "need": recipient.need,
        "clue": place.clue,
        "room": ROOMS[room_id].label,
    }


def introduce(world: World, seeker: Entity, room: Room, bitsy: Keepsake, mood: SeekerMood) -> None:
    seeker.memes["love"] += 1
    world.say(
        f"In {room.label}, where {room.cozy}, {seeker.id} was getting ready for bed."
    )
    world.say(
        f"Every night, {seeker.pronoun()} tucked {bitsy.phrase} under {seeker.pronoun('possessive')} chin. "
        f"It was such a {bitsy.tiny_word} thing that everyone simply called it bitsy."
    )
    world.say(mood.opening)


def notice_missing(world: World, seeker: Entity, bitsy: Entity, mood: SeekerMood) -> None:
    seeker.memes["searching"] += 1
    bitsy.attrs["location"] = "missing"
    propagate(world, narrate=False)
    world.say(
        f"But when {seeker.pronoun()} reached for bitsy, the little space beside the pillow was empty."
    )
    world.say(
        f"{seeker.id} sat very still and looked once, then twice. {mood.search_style}"
    )


def comfort(world: World, parent: Entity, seeker: Entity, mood: SeekerMood) -> None:
    seeker.memes["trust"] += 1
    world.say(
        f'"Let us look slowly," {parent.label_word} whispered. "{mood.comfort_line}"'
    )


def search_place(world: World, seeker: Entity, place: HidingPlace, index: int) -> None:
    seeker.meters["searched_places"] += 1
    if index < 2:
        seeker.meters["clues"] += 1
        propagate(world, narrate=False)
        world.say(place.clue)
    else:
        seeker.meters["found"] += 1
        propagate(world, narrate=False)
        world.say(place.found_text)


def reveal(world: World, seeker: Entity, parent: Entity, recipient: Entity,
           recipient_cfg: Recipient, reason: TransferReason, bitsy: Keepsake) -> None:
    seeker.meters["understood"] += 1
    world.say(
        f"There, curled in a sleepy little ball, was {recipient_cfg.phrase} with bitsy tucked close."
    )
    world.say(
        f'{parent.label_word.capitalize()} touched {seeker.pronoun("possessive")} shoulder softly. '
        f'"I {reason.action}," {parent.pronoun()} said. "{reason.explanation}"'
    )
    seeker.memes["empathy"] += 1


def choose_kindness(world: World, seeker: Entity, recipient: Entity,
                    recipient_cfg: Recipient, bitsy: Keepsake, reason: TransferReason) -> None:
    seeker.memes["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{seeker.id} looked at {recipient_cfg.phrase}, then at bitsy, and nodded."
    )
    world.say(
        f'"Bitsy can stay there tonight," {seeker.pronoun()} whispered. "{reason.kindness}"'
    )


def new_plan(world: World, seeker: Entity, parent: Entity, recipient_cfg: Recipient, bitsy: Keepsake) -> None:
    seeker.memes["sleepy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled and spread a blanket around {seeker.pronoun("object")}. '
        f'"Then we will make a new bedtime place for bitsy tomorrow," {parent.pronoun()} said.'
    )
    world.say(
        f"That night {seeker.id} fell asleep listening to the house grow quiet, knowing where bitsy was and why."
    )
    world.say(
        f"In the morning, they made {recipient_cfg.bedtime_change}, so bitsy would never feel lost again."
    )


def tell(room: Room, bitsy_cfg: Keepsake, mood_cfg: SeekerMood, recipient_cfg: Recipient,
         place_cfg: HidingPlace, reason_cfg: TransferReason,
         seeker_name: str = "Mina", seeker_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        role="seeker",
        traits=[mood_cfg.id],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient_cfg.type,
        role="recipient",
        label=recipient_cfg.label,
        sleepy=True,
        attrs={"need": recipient_cfg.need},
    ))
    bitsy = world.add(Entity(
        id="bitsy",
        kind="thing",
        type="comfort",
        label=bitsy_cfg.label,
        portable=True,
        attrs={"location": "seeker", "home_room": room.id},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place_cfg.label,
        hidden=True,
        attrs={"place_id": place_cfg.id},
    ))

    world.facts.update(
        room=room,
        bitsy_cfg=bitsy_cfg,
        mood_cfg=mood_cfg,
        recipient_cfg=recipient_cfg,
        place_cfg=place_cfg,
        reason_cfg=reason_cfg,
        seeker=seeker,
        parent=parent,
        recipient=recipient,
        bitsy=bitsy,
    )

    bitsy.attrs["location"] = "seeker"
    seeker.memes["searching"] = 0.0
    seeker.meters["clues"] = 0.0
    seeker.meters["found"] = 0.0
    seeker.memes["shared"] = 0.0
    propagate(world, narrate=False)

    introduce(world, seeker, room, bitsy_cfg, mood_cfg)

    world.para()
    notice_missing(world, seeker, bitsy, mood_cfg)
    comfort(world, parent, seeker, mood_cfg)

    world.para()
    search_place(world, seeker, HidingPlace(
        id="bed_skirt",
        label="bed skirt",
        phrase="under the bed skirt",
        clue=f"First they looked {('under the bed skirt' if room.id != 'window_nook' else 'under the little daybed')}, but found only a silver button and a sleepy dust bunny.",
        found_text="",
        tags={"search"},
    ), 0)
    search_place(world, seeker, HidingPlace(
        id="book_stack",
        label="book stack",
        phrase="by the books",
        clue="Next they checked by the storybooks and found a soft trail of crinkled blanket threads.",
        found_text="",
        tags={"search", "clue"},
    ), 1)

    bitsy.attrs["location"] = "recipient"
    bitsy.attrs["place"] = place_cfg.id
    world.facts["found_place"] = place_cfg.id

    search_place(world, seeker, place_cfg, 2)

    world.para()
    reveal(world, seeker, parent, recipient, recipient_cfg, reason_cfg, bitsy_cfg)
    choose_kindness(world, seeker, recipient, recipient_cfg, bitsy_cfg, reason_cfg)

    world.para()
    new_plan(world, seeker, parent, recipient_cfg, bitsy_cfg)

    world.facts.update(
        outcome="kindly_solved",
        predicted=predict_story(room.id, recipient_cfg.id, place_cfg.id),
        clues_found=int(seeker.meters["clues"]),
        searched_places=int(seeker.meters["searched_places"]),
        shared=seeker.memes["shared"] >= THRESHOLD,
        understood=seeker.meters["understood"] >= THRESHOLD,
    )
    return world


ROOMS = {
    "moon_bedroom": Room(
        id="moon_bedroom",
        label="a moonlit bedroom",
        cozy="the curtains glowed pale blue and the lamp made a warm puddle of light",
        tags={"bedroom", "bedtime"},
    ),
    "attic_nest": Room(
        id="attic_nest",
        label="a snug attic room",
        cozy="the slanted ceiling felt like a little roof for dreams",
        tags={"bedroom", "attic"},
    ),
    "window_nook": Room(
        id="window_nook",
        label="a quiet window nook",
        cozy="night stars pressed softly against the glass",
        tags={"bedroom", "window"},
    ),
}

KEEPSAKES = {
    "button_rabbit": Keepsake(
        id="button_rabbit",
        label="rabbit scrap",
        phrase="a rabbit-shaped scrap of cloth with one blue button eye",
        tiny_word="bitsy",
        feel="soft and cool",
        tags={"comfort", "rabbit"},
    ),
    "star_pillowlet": Keepsake(
        id="star_pillowlet",
        label="star pillowlet",
        phrase="a tiny star-shaped pillow no bigger than a hand",
        tiny_word="bitsy",
        feel="soft and puffy",
        tags={"comfort", "star"},
    ),
    "felt_boat": Keepsake(
        id="felt_boat",
        label="felt boat",
        phrase="a tiny felt boat stitched with yellow thread",
        tiny_word="bitsy",
        feel="smooth and thin",
        tags={"comfort", "boat"},
    ),
}

SEEKER_MOODS = {
    "patient": SeekerMood(
        id="patient",
        opening="Just looking at bitsy always made the room feel smaller, calmer, and safe.",
        search_style="The mystery made a small flutter in the room, but not a storm.",
        comfort_line="We will follow the little clues, one at a time.",
        tags={"patience"},
    ),
    "curious": SeekerMood(
        id="curious",
        opening="Bitsy was part of the bedtime game, so sleep never seemed far away when it was near.",
        search_style="The mystery made curiosity wake up inside her like a tiny lantern.",
        comfort_line="A small mystery likes calm eyes best.",
        tags={"curious"},
    ),
    "gentle": SeekerMood(
        id="gentle",
        opening="Holding bitsy before sleep was like hearing a favorite goodnight word.",
        search_style="The mystery tugged at her heart, yet she tried to keep her hands quiet and gentle.",
        comfort_line="Nothing kind is truly gone while we are still looking with love.",
        tags={"gentle"},
    ),
}

RECIPIENTS = {
    "baby_brother": Recipient(
        id="baby_brother",
        label="baby brother",
        phrase="the baby brother in the basket crib",
        relation="brother",
        type="boy",
        need="he had woken with a wobbling lip and could not settle",
        clue_text="a thread led toward the basket crib",
        bedtime_change="a tiny pocket on the side of the basket crib",
        tags={"baby", "family"},
    ),
    "little_sister": Recipient(
        id="little_sister",
        label="little sister",
        phrase="the little sister on the quilt pallet",
        relation="sister",
        type="girl",
        need="she had been fighting tears and reaching for something soft",
        clue_text="a thread led toward the quilt pallet",
        bedtime_change="a soft ribbon loop beside the little quilt",
        tags={"sister", "family"},
    ),
    "kitten": Recipient(
        id="kitten",
        label="kitten",
        phrase="the sleepy kitten in the laundry basket",
        relation="pet",
        type="thing",
        need="it had been mewing in the dark and needed something warm to lean against",
        clue_text="a thread led toward the laundry basket",
        bedtime_change="a small cloth nest beside the laundry basket",
        tags={"kitten", "pet"},
    ),
}

PLACES = {
    "crib": HidingPlace(
        id="crib",
        label="basket crib",
        phrase="in the basket crib",
        clue="At last they saw the faintest blue thread caught on the side of the basket crib.",
        found_text="Then they followed the clue all the way to the basket crib.",
        tags={"crib", "clue"},
    ),
    "quilt": HidingPlace(
        id="quilt",
        label="quilt pallet",
        phrase="on the quilt pallet",
        clue="At last they noticed the corner of the quilt puffed up in one small sleepy hill.",
        found_text="Then they followed the clue all the way to the quilt pallet.",
        tags={"quilt", "clue"},
    ),
    "basket": HidingPlace(
        id="basket",
        label="laundry basket",
        phrase="in the laundry basket",
        clue="At last a tiny paw peeped over the rim of the laundry basket beside the dresser.",
        found_text="Then they followed the clue all the way to the laundry basket.",
        tags={"basket", "clue"},
    ),
}

RECIPIENT_TO_PLACES = {
    "baby_brother": {"crib"},
    "little_sister": {"quilt"},
    "kitten": {"basket"},
}

REASONS = {
    "lent_to_comfort": TransferReason(
        id="lent_to_comfort",
        action="borrowed bitsy for a while",
        explanation="someone smaller than you needed comfort first tonight.",
        kindness="Bitsy is good at helping little ones feel brave.",
        tags={"sharing", "comfort"},
    ),
    "used_as_soft_friend": TransferReason(
        id="used_as_soft_friend",
        action="tucked bitsy there for a little while",
        explanation="that sleepy heart needed a soft friend before sleep would come.",
        kindness="We can let bitsy do one extra kind job tonight.",
        tags={"sharing", "comfort"},
    ),
    "carried_to_settle": TransferReason(
        id="carried_to_settle",
        action="carried bitsy over very gently",
        explanation="the room was peaceful for you, but not yet for someone else.",
        kindness="Bitsy can visit and still belong with us.",
        tags={"sharing", "comfort"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "June", "Tessa", "Etta", "Mara"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Milo", "Jasper", "Noah", "Finn", "Arlo"]


@dataclass
class StoryParams:
    room: str
    bitsy: str
    mood: str
    recipient: str
    place: str
    reason: str
    seeker_name: str
    seeker_type: str
    parent_type: str
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
    "comfort": [(
        "Why do children sometimes keep a tiny bedtime object?",
        "A tiny bedtime object can feel familiar in the dark. Familiar things help many children relax because they make bedtime feel steady and safe."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. In a mystery, clues guide you step by step toward the answer."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means choosing to help or comfort someone else. Sometimes kindness means sharing something you love for a little while."
    )],
    "kitten": [(
        "Why might a kitten want something soft at night?",
        "Kittens like warmth and soft places because it helps them feel safe. A soft nest can help a kitten settle down to sleep."
    )],
    "baby": [(
        "Why do babies sometimes need help falling asleep?",
        "Babies can wake up feeling lonely, hungry, or surprised by the dark. A calm grown-up and something soft can help them settle again."
    )],
    "family": [(
        "How can families solve a small bedtime problem together?",
        "Families can slow down, look carefully, and speak gently. When everyone stays calm, it is easier to find a kind answer."
    )],
}
KNOWLEDGE_ORDER = ["clue", "kindness", "comfort", "baby", "kitten", "family"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    recipient_cfg = f["recipient_cfg"]
    room = f["room"]
    return [
        'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "bitsy" and a small mystery.',
        f"Tell a cozy story set in {room.label} where {seeker.id} cannot find bitsy, follows clues, and solves the mystery with kindness.",
        f"Write a bedtime tale where a child discovers that bitsy was borrowed to comfort {recipient_cfg.label}, and the ending shows a new loving bedtime habit.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    parent = f["parent"]
    recipient_cfg = f["recipient_cfg"]
    place_cfg = f["place_cfg"]
    bitsy_cfg = f["bitsy_cfg"]
    reason_cfg = f["reason_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id}, bitsy, and {seeker.pronoun('possessive')} {parent.label_word}. The bedtime mystery also involves {recipient_cfg.label}."
        ),
        (
            "What was the mystery?",
            f"The mystery was that bitsy was missing at bedtime. {seeker.id} expected to find {bitsy_cfg.label} by the pillow, so the empty spot felt strange right away."
        ),
        (
            "How did they solve the mystery?",
            f"They looked slowly and followed little clues from one place to another until they reached the {place_cfg.label}. The clues helped them stay calm instead of guessing wildly."
        ),
        (
            f"Why was bitsy in the {place_cfg.label}?",
            f"Bitsy had been taken there to comfort {recipient_cfg.label}. {parent.label_word.capitalize()} explained that {reason_cfg.explanation}"
        ),
        (
            f"How did {seeker.id} show kindness?",
            f"{seeker.id} chose to let bitsy stay with {recipient_cfg.label} for the night. That was kind because {seeker.pronoun()} understood someone smaller needed comfort first."
        ),
        (
            "How did the story end?",
            f"It ended peacefully, with the mystery solved and everyone calmer. In the morning they made {recipient_cfg.bedtime_change}, which showed they had turned the problem into a caring new habit."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"clue", "kindness", "comfort", "family"}
    recipient_id = f["recipient_cfg"].id
    if recipient_id in {"baby_brother", "little_sister"}:
        tags.add("baby")
    if recipient_id == "kitten":
        tags.add("kitten")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("portable", e.portable), ("hidden", e.hidden), ("sleepy", e.sleepy)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="moon_bedroom",
        bitsy="button_rabbit",
        mood="gentle",
        recipient="baby_brother",
        place="crib",
        reason="lent_to_comfort",
        seeker_name="Mina",
        seeker_type="girl",
        parent_type="mother",
    ),
    StoryParams(
        room="attic_nest",
        bitsy="star_pillowlet",
        mood="patient",
        recipient="little_sister",
        place="quilt",
        reason="used_as_soft_friend",
        seeker_name="Theo",
        seeker_type="boy",
        parent_type="father",
    ),
    StoryParams(
        room="window_nook",
        bitsy="felt_boat",
        mood="curious",
        recipient="kitten",
        place="basket",
        reason="carried_to_settle",
        seeker_name="Lila",
        seeker_type="girl",
        parent_type="mother",
    ),
    StoryParams(
        room="moon_bedroom",
        bitsy="star_pillowlet",
        mood="patient",
        recipient="kitten",
        place="basket",
        reason="lent_to_comfort",
        seeker_name="Owen",
        seeker_type="boy",
        parent_type="father",
    ),
    StoryParams(
        room="attic_nest",
        bitsy="button_rabbit",
        mood="gentle",
        recipient="baby_brother",
        place="crib",
        reason="carried_to_settle",
        seeker_name="Nora",
        seeker_type="girl",
        parent_type="mother",
    ),
]


def explain_rejection(recipient: Recipient, place: HidingPlace) -> str:
    return (
        f"(No story: {recipient.label} would not reasonably be found in the {place.label}. "
        f"This bedtime mystery needs a gentle clue path to a place that fits the sleeper.)"
    )


ASP_RULES = r"""
valid(Room, Bitsy, Mood, Recipient, Place) :-
    room(Room), bitsy(Bitsy), mood(Mood), recipient(Recipient), place(Place),
    allowed_place(Recipient, Place).

outcome(kindly_solved) :- chosen_place(P), chosen_recipient(R), allowed_place(R, P).

#show valid/5.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for bid in KEEPSAKES:
        lines.append(asp.fact("bitsy", bid))
    for mid in SEEKER_MOODS:
        lines.append(asp.fact("mood", mid))
    for rid in RECIPIENTS:
        lines.append(asp.fact("recipient", rid))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, place_ids in RECIPIENT_TO_PLACES.items():
        for pid in sorted(place_ids):
            lines.append(asp.fact("allowed_place", rid, pid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_recipient", params.recipient),
        asp.fact("chosen_place", params.place),
    ])
    model = asp.one_model(asp_program(scenario))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny bedtime mystery solved with kindness."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--bitsy", choices=KEEPSAKES)
    ap.add_argument("--mood", choices=SEEKER_MOODS)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--reason", choices=REASONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipient and args.place:
        if not compatible_place(PLACES[args.place], RECIPIENTS[args.recipient]):
            raise StoryError(explain_rejection(RECIPIENTS[args.recipient], PLACES[args.place]))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.bitsy is None or c[1] == args.bitsy)
        and (args.mood is None or c[2] == args.mood)
        and (args.recipient is None or c[3] == args.recipient)
        and (args.place is None or c[4] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, bitsy_id, mood_id, recipient_id, place_id = rng.choice(sorted(combos))
    reason_id = args.reason or rng.choice(sorted(REASONS))
    seeker_type = args.gender or rng.choice(["girl", "boy"])
    seeker_name = args.name or rng.choice(GIRL_NAMES if seeker_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        room=room_id,
        bitsy=bitsy_id,
        mood=mood_id,
        recipient=recipient_id,
        place=place_id,
        reason=reason_id,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        room = ROOMS[params.room]
        bitsy_cfg = KEEPSAKES[params.bitsy]
        mood_cfg = SEEKER_MOODS[params.mood]
        recipient_cfg = RECIPIENTS[params.recipient]
        place_cfg = PLACES[params.place]
        reason_cfg = REASONS[params.reason]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not compatible_place(place_cfg, recipient_cfg):
        raise StoryError(explain_rejection(recipient_cfg, place_cfg))

    world = tell(
        room=room,
        bitsy_cfg=bitsy_cfg,
        mood_cfg=mood_cfg,
        recipient_cfg=recipient_cfg,
        place_cfg=place_cfg,
        reason_cfg=reason_cfg,
        seeker_name=params.seeker_name,
        seeker_type=params.seeker_type,
        parent_type=params.parent_type,
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

    cases = list(CURATED)
    for s in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != "kindly_solved")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generation succeeded.")
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
        print(f"{len(combos)} compatible (room, bitsy, mood, recipient, place) combos:\n")
        for room_id, bitsy_id, mood_id, recipient_id, place_id in combos:
            print(f"  {room_id:13} {bitsy_id:14} {mood_id:8} {recipient_id:13} {place_id}")
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
                f"### {p.seeker_name}: bitsy mystery in {p.room} "
                f"({p.recipient} at {p.place})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
