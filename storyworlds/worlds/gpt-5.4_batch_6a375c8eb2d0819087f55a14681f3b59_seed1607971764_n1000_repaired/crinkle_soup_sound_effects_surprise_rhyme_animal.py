#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py
==============================================================================

A standalone story world for a gentle animal-story domain built around a
mysterious crinkle, a pot of soup, a surprise helper, and a tiny rhyme.

Premise
-------
One small animal wants to carry warm soup to a sniffly friend. The soup starts
well, but one finishing ingredient is missing, so the cook worries the soup will
taste plain. Then a soft "crinkle, crinkle" sounds at the door. For a moment it
feels strange and worrying. When the cook opens the door, the sound turns out to
be a wrapped surprise from a thoughtful helper: exactly the missing finishing
ingredient, plus a small rhyming note. The soup is finished, shared, and the end
image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py --place burrow --soup carrot --gift parsley_bundle
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py --soup mushroom --gift honey_drizzle
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py --all
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crinkle_soup_sound_effects_surprise_rhyme_animal.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "fox", "mouse", "hedgehog", "squirrel", "otter", "badger"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    kitchen: str
    path: str
    door: str
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
class SoupKind:
    id: str
    label: str
    pot_phrase: str
    color: str
    simmer_sound: str
    needed_gift: str
    missing_line: str
    ending_image: str
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
class Gift:
    id: str
    label: str
    phrase: str
    wrap: str
    sound: str
    finish_verb: str
    note_first: str
    note_second: str
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
class AnimalTemplate:
    id: str
    label: str
    type: str
    home_touch: str
    carry_style: str
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


def _r_missing_worry(world: World) -> list[str]:
    soup = world.get("soup")
    cook = world.get("cook")
    if soup.meters["simmering"] >= THRESHOLD and soup.meters["complete"] < THRESHOLD:
        sig = ("missing_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            cook.memes["worry"] += 1
            return ["__worry__"]
    return []


def _r_surprise_completion(world: World) -> list[str]:
    soup = world.get("soup")
    gift = world.get("gift")
    cook = world.get("cook")
    if gift.meters["opened"] >= THRESHOLD and gift.attrs.get("matches_need"):
        sig = ("surprise_completion",)
        if sig not in world.fired:
            world.fired.add(sig)
            soup.meters["complete"] += 1
            soup.meters["plain"] = 0.0
            cook.memes["surprise"] += 1
            cook.memes["relief"] += 1
            return ["__complete__"]
    return []


def _r_share_comfort(world: World) -> list[str]:
    soup = world.get("soup")
    friend = world.get("friend")
    cook = world.get("cook")
    if soup.meters["shared"] >= THRESHOLD:
        sig = ("share_comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.meters["full"] += 1
            friend.meters["warm"] += 1
            friend.meters["sniffles"] = 0.0
            friend.memes["comfort"] += 1
            cook.memes["joy"] += 1
            return ["__comfort__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="surprise_completion", tag="emotion", apply=_r_surprise_completion),
    Rule(name="share_comfort", tag="care", apply=_r_share_comfort),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for text in produced:
            world.say(text)
    return produced


def gift_fits_soup(soup: SoupKind, gift: Gift) -> bool:
    return soup.needed_gift == gift.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for soup_id in sorted(place.affords):
            soup = SOUPS[soup_id]
            for gift_id, gift in GIFTS.items():
                if gift_fits_soup(soup, gift):
                    combos.append((place_id, soup_id, gift_id))
    return combos


def predict_plain_soup(world: World) -> dict:
    sim = world.copy()
    soup = sim.get("soup")
    soup.meters["simmering"] += 1
    propagate(sim, narrate=False)
    return {
        "plain": soup.meters["complete"] < THRESHOLD,
        "cook_worry": sim.get("cook").memes["worry"],
    }


def introduce(world: World, cook: Entity, friend: Entity, soup: SoupKind, place: Place) -> None:
    world.say(
        f"In {place.kitchen}, {cook.id} the {cook.type} stirred a pot of {soup.pot_phrase}. "
        f"The kitchen felt soft and small, and {cook.attrs['home_touch']}."
    )
    world.say(
        f"{friend.id} the {friend.type} had the sniffles, all {friend.attrs['sniff_sound']}, "
        f"so {cook.id} wanted to carry something warm across {place.path}."
    )


def begin_cooking(world: World, cook: Entity, soup: SoupKind) -> None:
    soup_ent = world.get("soup")
    soup_ent.meters["simmering"] += 1
    soup_ent.meters["plain"] += 1
    cook.memes["care"] += 1
    world.say(
        f'"{soup.simmer_sound}," sang the pot as {cook.id} stirred. '
        f"The {soup.color} soup smelled cozy already."
    )
    propagate(world, narrate=False)


def discover_missing(world: World, cook: Entity, soup: SoupKind) -> None:
    pred = predict_plain_soup(world)
    world.facts["predicted_plain"] = pred["plain"]
    world.facts["predicted_worry"] = pred["cook_worry"]
    world.say(
        f"Then {cook.id} looked at the shelf and blinked. {soup.missing_line}"
    )
    if pred["plain"]:
        world.say(
            f'"Oh dear," {cook.id} whispered. "Without the finishing touch, the soup may taste too plain."'
        )


def hear_crinkle(world: World, cook: Entity, helper: Entity, gift: Gift, place: Place) -> None:
    cook.memes["alert"] += 1
    gift_ent = world.get("gift")
    gift_ent.meters["at_door"] += 1
    world.say(
        f"Just then, from {place.door}, came a soft sound: "
        f'"{gift.sound}, {gift.sound}." {cook.id} stopped stirring and listened.'
    )
    world.say(
        f"For one small moment, {cook.id} wondered whether the wind was playing tricks on the {gift.wrap}."
    )
    world.facts["heard_crinkle"] = True
    world.facts["helper_waiting"] = helper.id


def open_gift(world: World, cook: Entity, helper: Entity, gift: Gift, soup: SoupKind) -> None:
    gift_ent = world.get("gift")
    soup_ent = world.get("soup")
    gift_ent.meters["opened"] += 1
    gift_ent.attrs["matches_need"] = gift_fits_soup(soup, gift)
    propagate(world, narrate=False)
    if soup_ent.meters["complete"] >= THRESHOLD:
        world.say(
            f"{cook.id} opened the {gift.wrap}, and there stood {helper.id} the {helper.type} with {gift.phrase}."
        )
        world.say(
            f'"Surprise!" said {helper.id}. "I thought your {soup.label} might need this."'
        )
    else:
        world.say(
            f"{cook.id} opened the {gift.wrap}, but inside was {gift.phrase}, which did not suit the pot at all."
        )


def add_finish(world: World, cook: Entity, gift: Gift, soup: SoupKind) -> None:
    soup_ent = world.get("soup")
    if soup_ent.meters["complete"] < THRESHOLD:
        return
    world.say(
        f"{cook.id} used {gift.phrase} to {gift.finish_verb}. At once the soup smelled brighter and rounder."
    )
    world.say(
        f"The little kitchen seemed to smile. Even the spoon made a happy tap-tap on the pot."
    )


def read_rhyme(world: World, cook: Entity, helper: Entity, gift: Gift) -> None:
    world.say(
        f"Tied to the {gift.label} was a tiny note. {cook.id} read it aloud: "
        f'"{gift.note_first} {gift.note_second}"'
    )
    helper.memes["care"] += 1
    cook.memes["love"] += 1


def carry_and_share(world: World, cook: Entity, friend: Entity, helper: Entity, soup: SoupKind, place: Place) -> None:
    soup_ent = world.get("soup")
    soup_ent.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon {cook.id} {cook.attrs['carry_style']} a warm bowl across {place.path} to {friend.id}."
    )
    world.say(
        f'{friend.id} took one careful sip. "Mmm," {friend.pronoun()} said, and the sniff-sniff quieted at once.'
    )
    world.say(
        f"{helper.id} padded along behind, pleased to see the surprise had worked."
    )
    world.say(
        f"By the end, {friend.id}'s eyes looked bright again, and {soup.ending_image}."
    )


def tell(place: Place, soup: SoupKind, gift: Gift, cook_cfg: AnimalTemplate, friend_cfg: AnimalTemplate, helper_cfg: AnimalTemplate) -> World:
    world = World(place)

    cook = world.add(Entity(
        id=cook_cfg.label,
        kind="character",
        type=cook_cfg.type,
        role="cook",
        attrs={"home_touch": cook_cfg.home_touch, "carry_style": cook_cfg.carry_style},
    ))
    friend = world.add(Entity(
        id=friend_cfg.label,
        kind="character",
        type=friend_cfg.type,
        role="friend",
        attrs={"sniff_sound": "sniff-sniff"},
    ))
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        attrs={"home_touch": helper_cfg.home_touch, "carry_style": helper_cfg.carry_style},
    ))
    soup_ent = world.add(Entity(
        id="soup",
        type="soup",
        label=soup.label,
        attrs={"needed_gift": soup.needed_gift},
    ))
    gift_ent = world.add(Entity(
        id="gift",
        type="gift",
        label=gift.label,
        attrs={"matches_need": False, "wrap": gift.wrap},
    ))

    cook.memes["care"] = 0.0
    cook.memes["worry"] = 0.0
    cook.memes["alert"] = 0.0
    cook.memes["surprise"] = 0.0
    cook.memes["relief"] = 0.0
    cook.memes["joy"] = 0.0
    cook.memes["love"] = 0.0
    friend.meters["sniffles"] = 1.0
    friend.meters["warm"] = 0.0
    friend.meters["full"] = 0.0
    friend.memes["comfort"] = 0.0
    helper.memes["care"] = 0.0
    soup_ent.meters["simmering"] = 0.0
    soup_ent.meters["plain"] = 0.0
    soup_ent.meters["complete"] = 0.0
    soup_ent.meters["shared"] = 0.0
    gift_ent.meters["at_door"] = 0.0
    gift_ent.meters["opened"] = 0.0

    world.facts.update(
        place=place,
        soup_cfg=soup,
        gift_cfg=gift,
        cook=cook,
        friend=friend,
        helper=helper,
        soup=soup_ent,
        gift=gift_ent,
        heard_crinkle=False,
        helper_waiting="",
        predicted_plain=False,
        predicted_worry=0.0,
    )

    introduce(world, cook, friend, soup, place)
    world.para()
    begin_cooking(world, cook, soup)
    discover_missing(world, cook, soup)
    hear_crinkle(world, cook, helper, gift, place)
    world.para()
    open_gift(world, cook, helper, gift, soup)
    add_finish(world, cook, gift, soup)
    read_rhyme(world, cook, helper, gift)
    world.para()
    carry_and_share(world, cook, friend, helper, soup, place)

    world.facts.update(
        completed=world.get("soup").meters["complete"] >= THRESHOLD,
        shared=world.get("soup").meters["shared"] >= THRESHOLD,
    )
    return world


PLACES = {
    "burrow": Place(
        id="burrow",
        label="burrow",
        kitchen="a round burrow kitchen",
        path="the mossy path",
        door="the little round door",
        affords={"carrot", "mushroom"},
    ),
    "cottage": Place(
        id="cottage",
        label="cottage",
        kitchen="a tidy cottage kitchen",
        path="the pebble path",
        door="the blue front step",
        affords={"carrot", "pumpkin", "mushroom"},
    ),
    "hollow": Place(
        id="hollow",
        label="hollow",
        kitchen="a warm tree-hollow kitchen",
        path="the rooty path",
        door="the barky doorway",
        affords={"pumpkin", "mushroom"},
    ),
}

SOUPS = {
    "carrot": SoupKind(
        id="carrot",
        label="carrot soup",
        pot_phrase="golden carrot soup",
        color="golden",
        simmer_sound="plip-plop",
        needed_gift="parsley_bundle",
        missing_line="The parsley was gone. The top of the soup needed one green, fresh flutter to finish it.",
        ending_image="three noses hovered over one golden bowl while steam curled like a ribbon",
        tags={"vegetable", "herb", "soup"},
    ),
    "pumpkin": SoupKind(
        id="pumpkin",
        label="pumpkin soup",
        pot_phrase="velvety pumpkin soup",
        color="orange",
        simmer_sound="bloop-bloop",
        needed_gift="seed_packet",
        missing_line="The crunchy pumpkin seeds were missing. Without them, the top of the soup would feel too sleepy and soft.",
        ending_image="their spoons clicked softly, and orange drops shone like sunset at the edge of the bowl",
        tags={"vegetable", "seed", "soup"},
    ),
    "mushroom": SoupKind(
        id="mushroom",
        label="mushroom soup",
        pot_phrase="creamy mushroom soup",
        color="brown",
        simmer_sound="hush-hush",
        needed_gift="thyme_bundle",
        missing_line="The thyme jar was empty. One small woodland smell was still missing from the pot.",
        ending_image="the bowl sent up warm curls while three small smiles gathered close beside it",
        tags={"vegetable", "herb", "soup"},
    ),
}

GIFTS = {
    "parsley_bundle": Gift(
        id="parsley_bundle",
        label="parsley",
        phrase="a fresh parsley bundle",
        wrap="crinkly paper parcel",
        sound="crinkle",
        finish_verb="scatter green parsley over the top",
        note_first="For sniffles and soup, a bright little loop!",
        note_second="A green sprinkle will make every spoonful swoop.",
        tags={"parsley", "herb", "crinkle"},
    ),
    "seed_packet": Gift(
        id="seed_packet",
        label="pumpkin seeds",
        phrase="a tiny packet of toasted pumpkin seeds",
        wrap="paper packet",
        sound="crinkle",
        finish_verb="shake the toasted seeds over the top",
        note_first="For soup in a heap, give crunch a small leap!",
        note_second="Sprinkle and munch, and the smiles will keep.",
        tags={"seed", "crinkle"},
    ),
    "thyme_bundle": Gift(
        id="thyme_bundle",
        label="thyme",
        phrase="a little thyme bundle tied with string",
        wrap="wax-paper parcel",
        sound="crinkle",
        finish_verb="tear in the thyme leaves and stir once more",
        note_first="For woodland soup, here's thyme in a group!",
        note_second="A tiny green breath makes the warm taste swoop.",
        tags={"thyme", "herb", "crinkle"},
    ),
    "honey_drizzle": Gift(
        id="honey_drizzle",
        label="honey",
        phrase="a small honey pot",
        wrap="cloth pouch",
        sound="swish",
        finish_verb="drizzle honey into the soup",
        note_first="Sweet is neat.",
        note_second="Sip and eat.",
        tags={"honey"},
    ),
}

ANIMALS = {
    "rabbit": AnimalTemplate(
        id="rabbit",
        label="Pip",
        type="rabbit",
        home_touch="the spoon rack softly clicked when the floorboards breathed",
        carry_style="carefully carried",
        tags={"rabbit"},
    ),
    "fox": AnimalTemplate(
        id="fox",
        label="Fern",
        type="fox",
        home_touch="the window curtain lifted and settled like a sleepy tail",
        carry_style="padded with",
        tags={"fox"},
    ),
    "mouse": AnimalTemplate(
        id="mouse",
        label="Mimi",
        type="mouse",
        home_touch="the tiny cups on the shelf shone like polished acorns",
        carry_style="tiptoed with",
        tags={"mouse"},
    ),
    "hedgehog": AnimalTemplate(
        id="hedgehog",
        label="Hob",
        type="hedgehog",
        home_touch="the basket by the stove smelled of dry leaves and clean towels",
        carry_style="trundled along with",
        tags={"hedgehog"},
    ),
    "squirrel": AnimalTemplate(
        id="squirrel",
        label="Tansy",
        type="squirrel",
        home_touch="the nut jars gave the room a sweet, woody smell",
        carry_style="scampered carefully with",
        tags={"squirrel"},
    ),
    "otter": AnimalTemplate(
        id="otter",
        label="Ripple",
        type="otter",
        home_touch="the kettle lid trembled with a happy little shine",
        carry_style="balanced",
        tags={"otter"},
    ),
}

COOK_CHOICES = ["rabbit", "fox", "mouse", "hedgehog"]
FRIEND_CHOICES = ["mouse", "squirrel", "rabbit", "hedgehog"]
HELPER_CHOICES = ["squirrel", "otter", "fox", "mouse"]


@dataclass
class StoryParams:
    place: str
    soup: str
    gift: str
    cook_animal: str
    friend_animal: str
    helper_animal: str
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
    "soup": [
        (
            "Why does warm soup feel comforting?",
            "Warm soup can help your body feel cozy, and the steam and warmth can be gentle when you are tired or sniffly."
        )
    ],
    "crinkle": [
        (
            "What makes a crinkle sound?",
            "Thin paper, wax paper, and dry wrappers can make a crinkle sound when they bend or rub together."
        )
    ],
    "herb": [
        (
            "What is an herb?",
            "An herb is a small leafy plant used to add smell and taste to food. Parsley and thyme are herbs."
        )
    ],
    "seed": [
        (
            "Why do toasted seeds feel crunchy?",
            "Seeds feel crunchy because they are small and firm, and toasting them makes them even crisper."
        )
    ],
}


def pair_name(a: Entity, b: Entity) -> str:
    return f"{a.id} the {a.type} and {b.id} the {b.type}"


def generation_prompts(world: World) -> list[str]:
    soup = world.facts["soup_cfg"]
    cook = world.facts["cook"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    gift = world.facts["gift_cfg"]
    place = world.facts["place"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the words "crinkle" and "soup". Use sound effects, a surprise, and a tiny rhyme.',
        f"Tell a story where {cook.id} the {cook.type} makes {soup.label} for {friend.id} the {friend.type}, hears a {gift.sound} at {place.door}, and finds a kind surprise.",
        f"Write a cozy animal tale with a worried cook, a helpful friend named {helper.id}, and a rhyming note that helps finish a pot of soup."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    cook = world.facts["cook"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    soup = world.facts["soup_cfg"]
    gift = world.facts["gift_cfg"]
    place = world.facts["place"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_name(cook, friend)}, and {helper.id} the {helper.type} too. {cook.id} wanted to help {friend.id} feel better with warm {soup.label}."
        ),
        (
            f"Why was {cook.id} making soup?",
            f"{cook.id} was making soup because {friend.id} had the sniffles. The warm bowl was meant to comfort {friend.pronoun('object')} and cheer {friend.pronoun('object')} up."
        ),
        (
            f"Why did {cook.id} start to worry?",
            f"{cook.id} noticed that the finishing ingredient was missing, so the soup might taste plain. That is why the little problem mattered before the surprise arrived."
        ),
        (
            f"What was the {gift.sound} sound at {place.door}?",
            f"It was {helper.id} arriving with {gift.phrase} wrapped in a {gift.wrap}. The crinkle sound first felt mysterious, then turned into a happy surprise."
        ),
        (
            f"How did the surprise help the soup?",
            f"The gift gave {cook.id} exactly what the pot still needed, so the soup could be finished properly. After that, the bowl smelled richer and more welcoming."
        ),
        (
            "What changed by the end of the story?",
            f"At the end, {friend.id} was warm, fed, and more comfortable. {cook.id} was no longer worried, because kindness and the surprise gift had turned the plain soup into a caring meal."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    soup = world.facts["soup_cfg"]
    gift = world.facts["gift_cfg"]
    tags: set[str] = {"soup", "crinkle"}
    if "herb" in soup.tags or "herb" in gift.tags or gift.id in {"parsley_bundle", "thyme_bundle"}:
        tags.add("herb")
    if "seed" in soup.tags or "seed" in gift.tags or gift.id == "seed_packet":
        tags.add("seed")
    ordered = ["soup", "crinkle", "herb", "seed"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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


def explain_rejection(place: Place, soup: SoupKind, gift: Gift) -> str:
    if soup.id not in place.affords:
        available = ", ".join(sorted(place.affords))
        return (
            f"(No story: {place.label} does not support {soup.label} in this tiny world. "
            f"Try a soup from: {available}.)"
        )
    return (
        f"(No story: {gift.label} is not the finishing touch for {soup.label}. "
        f"The surprise must solve the cook's real problem, so pick the matching gift instead.)"
    )


ASP_RULES = r"""
fits(S, G) :- soup_needs(S, G).
valid(P, S, G) :- affords(P, S), fits(S, G).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for soup_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, soup_id))
    for soup_id, soup in SOUPS.items():
        lines.append(asp.fact("soup", soup_id))
        lines.append(asp.fact("soup_needs", soup_id, soup.needed_gift))
    for gift_id in GIFTS:
        lines.append(asp.fact("gift", gift_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a crinkle at the door, a pot of soup, a surprise helper, and a rhyme."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--soup", choices=SOUPS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--cook-animal", dest="cook_animal", choices=ANIMALS)
    ap.add_argument("--friend-animal", dest="friend_animal", choices=ANIMALS)
    ap.add_argument("--helper-animal", dest="helper_animal", choices=ANIMALS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, soup, gift) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


CURATED = [
    StoryParams(
        place="burrow",
        soup="carrot",
        gift="parsley_bundle",
        cook_animal="rabbit",
        friend_animal="mouse",
        helper_animal="squirrel",
    ),
    StoryParams(
        place="cottage",
        soup="pumpkin",
        gift="seed_packet",
        cook_animal="fox",
        friend_animal="hedgehog",
        helper_animal="otter",
    ),
    StoryParams(
        place="hollow",
        soup="mushroom",
        gift="thyme_bundle",
        cook_animal="hedgehog",
        friend_animal="rabbit",
        helper_animal="mouse",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.soup and args.gift:
        place = PLACES[args.place]
        soup = SOUPS[args.soup]
        gift = GIFTS[args.gift]
        if (args.place, args.soup, args.gift) not in set(valid_combos()):
            raise StoryError(explain_rejection(place, soup, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.soup is None or combo[1] == args.soup)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, soup, gift = rng.choice(sorted(combos))
    cook_animal = args.cook_animal or rng.choice(COOK_CHOICES)
    friend_pool = [x for x in FRIEND_CHOICES if x != cook_animal]
    if not friend_pool:
        friend_pool = [x for x in ANIMALS if x != cook_animal]
    friend_animal = args.friend_animal or rng.choice(friend_pool)
    helper_pool = [x for x in HELPER_CHOICES if x not in {cook_animal, friend_animal}]
    if not helper_pool:
        helper_pool = [x for x in ANIMALS if x not in {cook_animal, friend_animal}]
    helper_animal = args.helper_animal or rng.choice(helper_pool)
    return StoryParams(
        place=place,
        soup=soup,
        gift=gift,
        cook_animal=cook_animal,
        friend_animal=friend_animal,
        helper_animal=helper_animal,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.soup not in SOUPS:
        raise StoryError(f"(No story: unknown soup '{params.soup}'.)")
    if params.gift not in GIFTS:
        raise StoryError(f"(No story: unknown gift '{params.gift}'.)")
    if params.cook_animal not in ANIMALS:
        raise StoryError(f"(No story: unknown cook animal '{params.cook_animal}'.)")
    if params.friend_animal not in ANIMALS:
        raise StoryError(f"(No story: unknown friend animal '{params.friend_animal}'.)")
    if params.helper_animal not in ANIMALS:
        raise StoryError(f"(No story: unknown helper animal '{params.helper_animal}'.)")

    if (params.place, params.soup, params.gift) not in set(valid_combos()):
        raise StoryError(explain_rejection(PLACES[params.place], SOUPS[params.soup], GIFTS[params.gift]))

    if len({params.cook_animal, params.friend_animal, params.helper_animal}) < 2:
        raise StoryError("(No story: the cook, friend, and helper should not all be the same animal kind.)")

    world = tell(
        place=PLACES[params.place],
        soup=SOUPS[params.soup],
        gift=GIFTS[params.gift],
        cook_cfg=ANIMALS[params.cook_animal],
        friend_cfg=ANIMALS[params.friend_animal],
        helper_cfg=ANIMALS[params.helper_animal],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        default_params.seed = 7
        sample = generate(default_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: default generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: default generate/emit crashed: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
            if "crinkle" not in sample.story.lower() or "soup" not in sample.story.lower():
                raise StoryError("required words missing from story text")
        except Exception as err:
            rc = 1
            print(f"CURATED TEST FAILED for {params}: {err}")

    if rc == 0:
        print(f"OK: curated generation passed on {len(CURATED)} stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, soup, gift) combos:\n")
        for place, soup, gift in combos:
            print(f"  {place:8} {soup:9} {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.cook_animal} cook, {p.soup} soup, {p.gift} surprise at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
