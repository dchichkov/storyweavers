#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/personify_aqua_hide_repetition_friendship_transformation_folk.py
================================================================================================

A standalone folk-tale style storyworld about a shy little spring called Aqua.

The seed asked for the words "personify", "aqua", and "hide", with the features
Repetition, Friendship, and Transformation in a folk-tale style. This world turns
those requests into a small simulation:

- A hidden spring named Aqua wants to help thirsty travelers.
- A blockage keeps the water from rising, and Aqua also feels shy.
- Three visitors repeat the same need through the day.
- A suitable friend helps in the right physical way.
- The hidden spring transforms the place into a living pool or brook, and Aqua
  changes from timid to brave.

The world refuses unreasonable combinations. A friend can only solve a blockage
they plausibly know how to handle, and some places transform in different ways
once water begins to flow.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COURAGE_NEEDED = 3.0


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
        female = {"girl", "woman", "mother", "hen"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    intro: str
    transformed: str
    water_form: str
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
class Blockage:
    id: str
    label: str
    cover_text: str
    clear_text: str
    method: str
    severity: int
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
class Friend:
    id: str
    label: str
    phrase: str
    type: str
    ability: str
    help_text: str
    promise_text: str
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
class Visitor:
    id: str
    label: str
    phrase: str
    need_text: str
    drink_style: str
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
class Gift:
    id: str
    label: str
    phrase: str
    effect: str
    blessing: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.history: list[tuple[str, dict]] = []
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def can_clear(friend: Friend, blockage: Blockage) -> bool:
    return friend.ability == blockage.method


def transformed_form(place: Place, gift: Gift) -> str:
    if gift.effect == "sparkle":
        return f"a silver-bright {place.water_form}"
    if gift.effect == "sing":
        return f"a singing {place.water_form}"
    if gift.effect == "glow":
        return f"a moon-soft {place.water_form}"
    return f"a clear {place.water_form}"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for blockage_id, blockage in BLOCKAGES.items():
            for friend_id, friend in FRIENDS.items():
                if not can_clear(friend, blockage):
                    continue
                for visitor_id in VISITORS:
                    for gift_id in GIFTS:
                        combos.append((place_id, blockage_id, friend_id, visitor_id, gift_id))
    return combos


def explain_rejection(friend: Friend, blockage: Blockage) -> str:
    return (
        f"(No story: {friend.label} cannot sensibly clear {blockage.label}. "
        f"This blockage needs a helper who can {blockage.method.replace('_', ' ')}, "
        f"so choose a better-matched friend.)"
    )


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = ""
    blockage: str = ""
    friend: str = ""
    visitor: str = ""
    gift: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
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


PLACES = {
    "fern_hollow": Place(
        id="fern_hollow",
        label="Fern Hollow",
        intro="At the edge of Fern Hollow, under a round stone and a curtain of roots, a tiny hidden spring listened to the world.",
        transformed="Soon Fern Hollow was no longer a quiet, thirsty dip in the earth.",
        water_form="pool",
        tags={"spring", "fern", "hollow"},
    ),
    "reed_bank": Place(
        id="reed_bank",
        label="Reed Bank",
        intro="Beside the reeds where the wind whispered all day, a little spring slept under mud and rushes.",
        transformed="Soon Reed Bank was no longer a dull strip of brown earth.",
        water_form="brook",
        tags={"spring", "reeds", "bank"},
    ),
    "willow_foot": Place(
        id="willow_foot",
        label="Willow Foot",
        intro="At the foot of the oldest willow, where roots curled like fingers, a shy spring hid in the cool dark.",
        transformed="Soon Willow Foot was no longer only roots and dust.",
        water_form="rill",
        tags={"spring", "willow"},
    ),
}

BLOCKAGES = {
    "stones": Blockage(
        id="stones",
        label="a cap of little stones",
        cover_text="little stones had slipped across the mouth of the spring and made a hard gray lid",
        clear_text="rolled the little stones aside one by one",
        method="lift_stones",
        severity=2,
        tags={"stones"},
    ),
    "roots": Blockage(
        id="roots",
        label="a knot of roots",
        cover_text="a knot of roots had woven itself over the mouth of the spring and held the water down",
        clear_text="nibbled and tugged the root-knot loose",
        method="untangle_roots",
        severity=2,
        tags={"roots"},
    ),
    "mud": Blockage(
        id="mud",
        label="a plug of mud",
        cover_text="a heavy plug of mud had packed itself over the spring-mouth and smothered the water",
        clear_text="scraped and swept the mud away",
        method="scrape_mud",
        severity=2,
        tags={"mud"},
    ),
}

FRIENDS = {
    "frog": Friend(
        id="frog",
        label="the frog",
        phrase="a green frog with bright round eyes",
        type="frog",
        ability="scrape_mud",
        help_text="The frog set to work with quick wet feet and scraped a path through the mud.",
        promise_text='“Do not hide forever,” croaked the frog. “A little water can become a great song.”',
        tags={"frog", "friend"},
    ),
    "otter": Friend(
        id="otter",
        label="the otter",
        phrase="a smooth brown otter with clever paws",
        type="otter",
        ability="lift_stones",
        help_text="The otter braced those clever paws and rolled the stones away.",
        promise_text='“Do not hide forever,” said the otter. “Even a small spring can feed a thirsty world.”',
        tags={"otter", "friend"},
    ),
    "mouse": Friend(
        id="mouse",
        label="the mouse",
        phrase="a field mouse with patient teeth",
        type="mouse",
        ability="untangle_roots",
        help_text="The mouse worried the roots, pulled at the loose ends, and opened a breathing space.",
        promise_text='“Do not hide forever,” whispered the mouse. “A brave heart can begin in a very small place.”',
        tags={"mouse", "friend"},
    ),
}

VISITORS = {
    "deer": Visitor(
        id="deer",
        label="the doe",
        phrase="a weary doe",
        need_text='“Is there a drink here? I have walked since dawn.”',
        drink_style="lowered her head and drank in slow thankful sips",
        tags={"deer", "thirst"},
    ),
    "sparrow": Visitor(
        id="sparrow",
        label="the sparrow",
        phrase="a dusty sparrow",
        need_text='“Is there a drink here? My little throat is dry.”',
        drink_style="dipped its beak and shook bright drops into the air",
        tags={"bird", "thirst"},
    ),
    "hare": Visitor(
        id="hare",
        label="the hare",
        phrase="a long-eared hare",
        need_text='“Is there a drink here? The road has filled my mouth with dust.”',
        drink_style="lapped quickly, then sat still as if listening to the water speak",
        tags={"hare", "thirst"},
    ),
}

GIFTS = {
    "moon_pebble": Gift(
        id="moon_pebble",
        label="moon pebble",
        phrase="a little moon pebble",
        effect="glow",
        blessing='“For kindness,” said the traveler, “may your water shine even in the dusk.”',
        tags={"magic", "moon"},
    ),
    "reed_flute": Gift(
        id="reed_flute",
        label="reed flute",
        phrase="a hollow reed flute",
        effect="sing",
        blessing='“For kindness,” said the traveler, “may your water always carry a song.”',
        tags={"magic", "song"},
    ),
    "silver_scale": Gift(
        id="silver_scale",
        label="silver scale",
        phrase="a shining silver scale",
        effect="sparkle",
        blessing='“For kindness,” said the traveler, “may your water catch the light and keep it.”',
        tags={"magic", "silver"},
    ),
}


# ---------------------------------------------------------------------------
# State-driven beats
# ---------------------------------------------------------------------------
def introduce(world: World, place: Place, blockage: Blockage) -> None:
    spring = world.get("aqua")
    world.say(place.intro)
    world.say(
        "Old village tellers liked to personify such waters, and they gave this one a name: Aqua."
    )
    world.say(
        f"But Aqua could not rise, because {blockage.cover_text}."
    )
    spring.memes["shyness"] += 2
    spring.meters["blocked"] = float(blockage.severity)
    world.history.append(("introduced", {"blockage": blockage.id}))


def first_hide(world: World) -> None:
    spring = world.get("aqua")
    spring.memes["shyness"] += 1
    world.say(
        "Aqua wanted to help, yet each time the light touched the hiding place, the little spring tried to hide deeper in the cool earth."
    )
    world.history.append(("hide", {"count": 1}))


def visitor_call(world: World, visitor: Visitor, number: int) -> None:
    spring = world.get("aqua")
    world.say(
        f"The first traveler came at sunrise, {visitor.phrase}, and called, {visitor.need_text}"
        if number == 1
        else f"The second traveler came when the sun stood high and called the same words again: {visitor.need_text}"
        if number == 2
        else f"The third traveler came at evening and asked once more, {visitor.need_text}"
    )
    spring.memes["wish_to_help"] += 1
    spring.memes["sorrow"] += 1
    world.facts["repetition_count"] = number
    world.history.append(("visitor_call", {"number": number, "visitor": visitor.id}))


def hidden_response(world: World, number: int) -> None:
    spring = world.get("aqua")
    trickle = 0.2 * number
    spring.meters["flow"] += trickle
    spring.meters["flow"] -= trickle
    world.say(
        "But only a dark wet whisper answered from under the earth."
        if number == 1
        else "Again only a dark wet whisper answered, and not enough water rose to fill even a leaf cup."
        if number == 2
        else "Again the answer was only a hidden murmur, as if the spring were ashamed of its own small voice."
    )
    world.history.append(("hidden_response", {"number": number}))


def friend_arrives(world: World, friend: Friend) -> None:
    helper = world.get("friend")
    spring = world.get("aqua")
    helper.memes["kindness"] += 1
    spring.memes["trust"] += 1
    world.say(
        f"Then {friend.phrase} stopped, listened, and heard the sorrow under the ground."
    )
    world.say(friend.promise_text)
    world.history.append(("friend_arrives", {"friend": friend.id}))


def help_clear(world: World, friend: Friend, blockage: Blockage) -> None:
    spring = world.get("aqua")
    helper = world.get("friend")
    helper.meters["effort"] += 1
    spring.meters["blocked"] = 0.0
    spring.memes["trust"] += 1
    spring.memes["courage"] += 2
    world.say(friend.help_text)
    world.say(
        f"At last {helper.label} {blockage.clear_text}, and Aqua felt the hard pressure leave."
    )
    world.history.append(("help_clear", {"friend": friend.id, "blockage": blockage.id}))


def gift_encourages(world: World, gift: Gift) -> None:
    spring = world.get("aqua")
    spring.memes["courage"] += 1
    spring.meters["blessing"] += 1
    world.say(
        f"From beside the spring-mouth, {world.get('friend').label} found {gift.phrase} left long ago by wandering folk."
    )
    world.say(
        f"The little charm touched the water, and a soft change began. {gift.blessing}"
    )
    world.history.append(("gift", {"gift": gift.id}))


def rise_and_transform(world: World, place: Place, visitor: Visitor, gift: Gift) -> None:
    spring = world.get("aqua")
    place_ent = world.get("place")
    spring.meters["flow"] = 3.0
    spring.meters["visible"] = 1.0
    spring.memes["shyness"] = 0.0
    spring.memes["joy"] += 2
    spring.memes["friendship"] += 2
    place_ent.meters["green"] += 2
    place_ent.meters["water"] += 2
    world.facts["water_form_text"] = transformed_form(place, gift)
    world.say(
        "Aqua did not hide then."
    )
    world.say(
        f"Up came the water, clear and bright, first as a tremble, then as {transformed_form(place, gift)}."
    )
    world.say(
        f"{place.transformed} Ferns lifted, moss brightened, and the thirsty earth turned cool."
        if place.id == "fern_hollow"
        else f"{place.transformed} Reeds straightened, mud darkened to shining brown, and dragonflies came to look."
        if place.id == "reed_bank"
        else f"{place.transformed} The willow roots drank deep, the dust settled, and small white flowers opened near the damp ground."
    )
    world.history.append(("transform", {"place": place.id, "gift": gift.id, "visitor": visitor.id}))


def third_visitor_returns(world: World, visitor: Visitor) -> None:
    spring = world.get("aqua")
    visitor_ent = world.get("visitor")
    visitor_ent.meters["quenched"] += 1
    spring.memes["pride"] += 1
    world.say(
        f"Then {visitor.label} came near again, {visitor.drink_style}."
    )
    world.say(
        "The traveler looked into the clear water as if listening to a friend."
    )
    world.history.append(("drink", {"visitor": visitor.id}))


def friendship_sealed(world: World, friend: Friend) -> None:
    spring = world.get("aqua")
    helper = world.get("friend")
    spring.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f'“Stay with me,” said Aqua in the sound of the water. {helper.label.capitalize()} did, and from that day the two kept one another company.'
    )
    world.history.append(("friendship", {"friend": friend.id}))


def ending(world: World, place: Place, gift: Gift) -> None:
    world.say(
        f"So the old people said that if you pass {place.label} at dusk, you may see {gift.label} light in the water and hear a shy spring speaking bravely at last."
    )
    world.say(
        "That is why the travelers who stop there still call the water Aqua, and why no one laughs when a storyteller chooses to personify a spring."
    )
    world.history.append(("ending", {"place": place.id, "gift": gift.id}))


def tell(place: Place, blockage: Blockage, friend: Friend, visitor: Visitor, gift: Gift) -> World:
    if not can_clear(friend, blockage):
        raise StoryError(explain_rejection(friend, blockage))

    world = World()
    spring = world.add(Entity(id="aqua", kind="character", type="spring", label="Aqua", role="spring"))
    helper = world.add(Entity(id="friend", kind="character", type=friend.type, label=friend.label, role="friend"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, role="place"))
    visitor_ent = world.add(Entity(id="visitor", kind="character", type="traveler", label=visitor.label, role="visitor"))

    spring.meters["blocked"] = 0.0
    spring.meters["flow"] = 0.0
    spring.meters["visible"] = 0.0
    spring.meters["blessing"] = 0.0
    spring.memes["shyness"] = 0.0
    spring.memes["wish_to_help"] = 0.0
    spring.memes["sorrow"] = 0.0
    spring.memes["trust"] = 0.0
    spring.memes["courage"] = 0.0
    spring.memes["joy"] = 0.0
    spring.memes["friendship"] = 0.0
    spring.memes["pride"] = 0.0
    helper.meters["effort"] = 0.0
    helper.memes["kindness"] = 0.0
    helper.memes["friendship"] = 0.0
    place_ent.meters["green"] = 0.0
    place_ent.meters["water"] = 0.0
    visitor_ent.meters["quenched"] = 0.0

    world.facts.update(
        place=place,
        blockage=blockage,
        friend_cfg=friend,
        visitor_cfg=visitor,
        gift=gift,
        repetition_count=0,
    )

    introduce(world, place, blockage)
    first_hide(world)

    world.para()
    for n in (1, 2, 3):
        visitor_call(world, visitor, n)
        if n < 3:
            hidden_response(world, n)

    world.para()
    friend_arrives(world, friend)
    help_clear(world, friend, blockage)
    gift_encourages(world, gift)

    world.para()
    rise_and_transform(world, place, visitor, gift)
    third_visitor_returns(world, visitor)
    friendship_sealed(world, friend)

    world.para()
    ending(world, place, gift)

    world.facts.update(
        outcome="transformed" if spring.meters["flow"] >= THRESHOLD else "hidden",
        spring=spring,
        helper=helper,
        place_ent=place_ent,
        visitor_ent=visitor_ent,
        transformed=spring.meters["flow"] >= THRESHOLD,
        friendship=spring.memes["friendship"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where water comes up from the ground. If the path is open, the water can flow into a pool or a little stream.",
        )
    ],
    "frog": [
        (
            "Why is a frog often near water?",
            "Frogs like wet places because their bodies dry out easily. Ponds, puddles, and springs are good places for them to live.",
        )
    ],
    "otter": [
        (
            "What makes an otter good at moving small stones?",
            "Otters have strong bodies and clever paws. They are used to playing and searching among stones near water.",
        )
    ],
    "mouse": [
        (
            "How can a mouse help with roots?",
            "A mouse is small and patient, so it can work in tight spaces. Its teeth can nibble and loosen little roots.",
        )
    ],
    "mud": [
        (
            "Why can mud block water?",
            "Mud can pack into a heavy plug and stop water from moving. When the plug is cleared, the water can rise again.",
        )
    ],
    "roots": [
        (
            "How do roots change the ground around a tree?",
            "Roots hold the soil and drink water. Sometimes they also tangle across tiny spaces in the ground.",
        )
    ],
    "stones": [
        (
            "Can stones stop a little spring?",
            "Yes. A small spring can be covered by fallen stones, and then the water has trouble coming out.",
        )
    ],
    "friendship": [
        (
            "How can a friend help someone who is shy?",
            "A friend can listen, stay close, and help with the hard part. Kind help can make a shy heart feel brave enough to try.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new state. In a folk tale, a dry place may become green, or a timid character may become brave.",
        )
    ],
    "folk": [
        (
            "What is a folk tale?",
            "A folk tale is a story told and retold by many people. It often sounds simple and musical, and it may explain why a place is remembered.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "spring",
    "mud",
    "roots",
    "stones",
    "frog",
    "otter",
    "mouse",
    "friendship",
    "transformation",
    "folk",
]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    blockage = world.facts["blockage"]
    friend = world.facts["friend_cfg"]
    visitor = world.facts["visitor_cfg"]
    return [
        f'Write a short folk tale that includes the words "personify", "aqua", and "hide", where a shy spring named Aqua is hidden in {place.label}.',
        f"Tell a repetitive friendship tale in which {visitor.label} asks for water three times, but Aqua cannot answer until {friend.label} helps clear {blockage.label}.",
        f"Write a child-facing transformation story where a hidden spring becomes a bright {place.water_form} and a timid water spirit grows brave because of a friend.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    blockage = world.facts["blockage"]
    friend = world.facts["friend_cfg"]
    visitor = world.facts["visitor_cfg"]
    gift = world.facts["gift"]
    spring = world.facts["spring"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a shy little spring called Aqua, {friend.label} who became Aqua's friend, and {visitor.label} who came looking for a drink.",
        ),
        (
            "Why did Aqua hide at the beginning?",
            f"Aqua was hidden because {blockage.cover_text}. Aqua also felt shy, so the spring wanted to hide instead of pushing up into the light.",
        ),
        (
            "What was repeated in the story?",
            f"The visitor's wish for water came three times through the day. That repetition showed how badly the world needed the spring to rise.",
        ),
        (
            f"How did {friend.label} help Aqua?",
            f"{friend.label.capitalize()} helped by doing the right kind of work: {blockage.clear_text}. That removed the blockage and gave Aqua courage at the same time.",
        ),
        (
            "How did the place transform?",
            f"When Aqua stopped hiding, the water rose into {world.facts['water_form_text']}. The dry place changed into somewhere cool, green, and alive.",
        ),
        (
            "Why did the story end with friendship?",
            f"It ended with friendship because Aqua did not become brave alone. {friend.label.capitalize()} listened, helped, and stayed, so the new water and the new friendship began together.",
        ),
        (
            f"What magic gift touched the spring, and what changed after that?",
            f"The gift was {gift.phrase}. It blessed the water, and after that Aqua rose more boldly and the spring gained a special {gift.effect} quality.",
        ),
    ]
    if spring.memes["pride"] >= THRESHOLD:
        qa.append(
            (
                "How did Aqua feel at the end?",
                "Aqua felt brave and proud instead of hidden and ashamed. The clear flowing water proved that change, because the spring could finally help others.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"spring", "friendship", "transformation", "folk"}
    tags |= set(world.facts["blockage"].tags)
    tags |= set(world.facts["friend_cfg"].tags)
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
# CLI helpers / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  history: {[name for name, _ in world.history]}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fern_hollow",
        blockage="stones",
        friend="otter",
        visitor="deer",
        gift="silver_scale",
    ),
    StoryParams(
        place="reed_bank",
        blockage="mud",
        friend="frog",
        visitor="sparrow",
        gift="reed_flute",
    ),
    StoryParams(
        place="willow_foot",
        blockage="roots",
        friend="mouse",
        visitor="hare",
        gift="moon_pebble",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,B,F,V,G) :- place(P), blockage(B), friend(F), visitor(V), gift(G), can_clear(F,B).

transformed(P,G,W) :- place_water_form(P,W0), gift_effect(G,sparkle), W = "silver-bright".
transformed(P,G,W) :- place_water_form(P,W0), gift_effect(G,sing), W = "singing".
transformed(P,G,W) :- place_water_form(P,W0), gift_effect(G,glow), W = "moon-soft".

outcome(transformed) :- chosen_place(P), chosen_blockage(B), chosen_friend(F), chosen_visitor(V), chosen_gift(G),
                        valid(P,B,F,V,G).
:- chosen_place(P), chosen_blockage(B), chosen_friend(F), not can_clear(F,B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_water_form", pid, place.water_form))
    for bid, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", bid))
        lines.append(asp.fact("needs_method", bid, blockage.method))
    for fid, friend in FRIENDS.items():
        lines.append(asp.fact("friend", fid))
        lines.append(asp.fact("friend_ability", fid, friend.ability))
        if can_clear(friend, BLOCKAGES["stones"]):
            lines.append(asp.fact("can_clear", fid, "stones"))
        if can_clear(friend, BLOCKAGES["roots"]):
            lines.append(asp.fact("can_clear", fid, "roots"))
        if can_clear(friend, BLOCKAGES["mud"]):
            lines.append(asp.fact("can_clear", fid, "mud"))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_effect", gid, gift.effect))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_blockage", params.blockage),
            asp.fact("chosen_friend", params.friend),
            asp.fact("chosen_visitor", params.visitor),
            asp.fact("chosen_gift", params.gift),
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
        print("MISMATCH in valid combos.")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        py = "transformed"
        asp_res = asp_outcome(params)
        if py != asp_res:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py} asp={asp_res}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test failed: generation returned incomplete sample")
        emit(sample, trace=False, qa=False)
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a shy spring named Aqua, a repeated plea, a friend, and a transformation."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--blockage", choices=sorted(BLOCKAGES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--visitor", choices=sorted(VISITORS))
    ap.add_argument("--gift", choices=sorted(GIFTS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.friend and args.blockage:
        friend = FRIENDS[args.friend]
        blockage = BLOCKAGES[args.blockage]
        if not can_clear(friend, blockage):
            raise StoryError(explain_rejection(friend, blockage))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.blockage is None or combo[1] == args.blockage)
        and (args.friend is None or combo[2] == args.friend)
        and (args.visitor is None or combo[3] == args.visitor)
        and (args.gift is None or combo[4] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, blockage, friend, visitor, gift = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        blockage=blockage,
        friend=friend,
        visitor=visitor,
        gift=gift,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.blockage not in BLOCKAGES:
        raise StoryError(f"(Unknown blockage: {params.blockage})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")

    place = PLACES[params.place]
    blockage = BLOCKAGES[params.blockage]
    friend = FRIENDS[params.friend]
    visitor = VISITORS[params.visitor]
    gift = GIFTS[params.gift]
    if not can_clear(friend, blockage):
        raise StoryError(explain_rejection(friend, blockage))

    world = tell(place, blockage, friend, visitor, gift)
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, blockage, friend, visitor, gift) combos:\n")
        for place, blockage, friend, visitor, gift in combos:
            print(f"  {place:12} {blockage:8} {friend:6} {visitor:8} {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
                f"### {p.place}: {p.blockage} with {p.friend} for {p.visitor} ({p.gift})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
