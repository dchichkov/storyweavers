#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py
==================================================

A standalone story world for a tiny mythic domain: a child carries a mint offering
to a hill shrine, meets a weary stranger on the path, and must choose whether to
keep the offering for ritual duty or share it in kindness.

The world is built around a moral value rather than a puzzle. The simulated state
tracks a child's duty, compassion, shame, and the visible response of the shrine,
the spring, and the mint patch below it. Stories are generated from the world
model, not from slot-swapped text.

Run it
------
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py --choice share --offering mint_water
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py --offering mint_cakes --visitor thirsty_traveler
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py --all
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/mint_moral_value_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
    village: str
    shrine: str
    path: str
    sky: str
    patch: str
    ending: str
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
class Offering:
    id: str
    label: str
    phrase: str
    kind: str
    amount: int
    scent: str
    carry_text: str
    share_text: str
    shrine_text: str
    repair_text: str
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
    need_kind: str
    need_word: str
    ask: str
    relief: str
    reveal: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    supports: set[str]
    capacity: int
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_help(world: World) -> list[str]:
    hero = world.get("hero")
    visitor = world.get("visitor")
    if visitor.meters["received_help"] < THRESHOLD:
        return []
    sig = ("help",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    visitor.meters["need"] = 0.0
    visitor.memes["gratitude"] += 1
    hero.memes["compassion"] += 1
    return ["__helped__"]


def _r_bless(world: World) -> list[str]:
    hero = world.get("hero")
    visitor = world.get("visitor")
    spring = world.get("spring")
    mint = world.get("mint_patch")
    shrine = world.get("shrine")
    if visitor.memes["gratitude"] < THRESHOLD:
        return []
    sig = ("bless",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spring.meters["flow"] += 1
    mint.meters["bloom"] += 1
    shrine.memes["favor"] += 1
    hero.memes["wonder"] += 1
    return ["__blessing__"]


def _r_wilt(world: World) -> list[str]:
    hero = world.get("hero")
    shrine = world.get("shrine")
    mint = world.get("mint_patch")
    if shrine.meters["offering_delivered"] < THRESHOLD or hero.memes["refusal"] < THRESHOLD:
        return []
    sig = ("wilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mint.meters["wilt"] += 1
    hero.memes["shame"] += 1
    shrine.memes["silence"] += 1
    return ["__wilt__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="help", tag="moral", apply=_r_help),
    Rule(name="bless", tag="myth", apply=_r_bless),
    Rule(name="wilt", tag="moral", apply=_r_wilt),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s == "__blessing__":
                world.say(
                    "At once the air changed. A cool wind moved over the stones, and the "
                    "scent of mint grew bright as if the hill itself had begun to breathe."
                )
            elif s == "__wilt__":
                world.say(
                    "But when the offering touched the altar, the lamp gave only a thin flame, "
                    "and the mint below the steps drooped as if the hill had heard a hard answer."
                )
    return produced


def helpful(offering: Offering, visitor: Visitor) -> bool:
    return offering.kind == visitor.need_kind


def carry_ok(carrier: Carrier, offering: Offering) -> bool:
    return offering.kind in carrier.supports and carrier.capacity >= offering.amount


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id in PLACES:
        for offering_id, offering in OFFERINGS.items():
            for visitor_id, visitor in VISITORS.items():
                for carrier_id, carrier in CARRIERS.items():
                    if helpful(offering, visitor) and carry_ok(carrier, offering):
                        combos.append((place_id, offering_id, visitor_id, carrier_id))
    return combos


def explain_rejection(offering: Offering, visitor: Visitor, carrier: Optional[Carrier]) -> str:
    if not helpful(offering, visitor):
        return (
            f"(No story: {offering.label} cannot honestly help a {visitor.label}. "
            f"This world only tells myths where the mint offering fits the stranger's need.)"
        )
    if carrier is not None and not carry_ok(carrier, offering):
        return (
            f"(No story: {carrier.label} is not a sensible way to carry {offering.label}. "
            f"The carrier must suit the offering and hold enough of it for the tale.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: "StoryParams") -> str:
    return "blessing" if params.choice == "share" else "lesson"


def predict_sharing(world: World, choice: str) -> dict:
    sim = world.copy()
    if choice == "share":
        sim.get("visitor").meters["received_help"] += 1
        sim.get("offering").meters["remaining"] = 0.0
    else:
        sim.get("hero").memes["refusal"] += 1
        sim.get("shrine").meters["offering_delivered"] += 1
    propagate(sim, narrate=False)
    return {
        "visitor_need": sim.get("visitor").meters["need"],
        "spring_flow": sim.get("spring").meters["flow"],
        "mint_bloom": sim.get("mint_patch").meters["bloom"],
        "mint_wilt": sim.get("mint_patch").meters["wilt"],
    }


def introduce(world: World, hero: Entity, elder: Entity, place: Place, offering: Offering, carrier: Carrier) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In the old days, when people still listened for meaning in wind and water, "
        f"{hero.id} lived in {place.village} below {place.shrine}."
    )
    world.say(
        f"Each midsummer, {elder.label} sent one child up {place.path} with {carrier.phrase} "
        f"holding {offering.phrase}. The gift smelled of mint and promised coolness in the heat."
    )
    world.say(place.sky)


def charge(world: World, hero: Entity, elder: Entity, offering: Offering) -> None:
    world.say(
        f'"Carry it steadily," said {elder.label}. "What is laid before the shrine should '
        f'be brought with a clean heart."'
    )
    world.say(
        f"{hero.id} lifted the offering carefully. {offering.carry_text}"
    )


def encounter(world: World, hero: Entity, visitor: Entity, visitor_cfg: Visitor, place: Place) -> None:
    visitor.meters["need"] = 1.0
    world.say(
        f"Halfway up, where wild mint grew between the stones near {place.patch}, "
        f"{hero.id} saw {visitor_cfg.label} sitting in the dust."
    )
    world.say(
        f'{visitor_cfg.ask}'
    )


def warning(world: World, hero: Entity, choice: str) -> None:
    pred = predict_sharing(world, choice)
    world.facts["predicted"] = pred
    if choice == "share":
        world.say(
            f"{hero.id} looked down into the gift and understood that the bowl might reach the shrine empty, "
            f"yet the stranger's need would end at once."
        )
    else:
        world.say(
            f"{hero.id} looked up the last steep steps and understood that the altar could be filled, "
            f"yet the stranger would remain in want."
        )


def share(world: World, hero: Entity, visitor: Entity, offering: Offering, visitor_cfg: Visitor) -> None:
    hero.memes["generosity"] += 1
    visitor.meters["received_help"] += 1
    world.get("offering").meters["remaining"] = 0.0
    world.say(
        f"Then {hero.id} knelt and {offering.share_text}. {visitor_cfg.relief}"
    )
    propagate(world, narrate=True)
    world.say(visitor_cfg.reveal)


def refuse(world: World, hero: Entity, visitor_cfg: Visitor) -> None:
    hero.memes["refusal"] += 1
    world.say(
        f"But {hero.id} drew the gift close and said, \"This belongs to the shrine.\" "
        f"Without another word, {hero.pronoun()} climbed on, leaving the stranger behind."
    )


def deliver(world: World, hero: Entity, place: Place, offering: Offering) -> None:
    shrine = world.get("shrine")
    shrine.meters["offering_delivered"] += 1
    world.say(
        f"At the top, {hero.id} stepped before {place.shrine} and {offering.shrine_text}."
    )
    propagate(world, narrate=True)


def elder_lesson(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["understanding"] += 1
    world.say(
        f'{elder.label.capitalize()} laid a hand on {hero.id}\'s shoulder and said, '
        f'"The gods do not count full bowls before they count open hands."'
    )
    world.say(
        f"The words stung, because they were true, and {hero.id} felt shame settle where pride had been."
    )


def repair(world: World, hero: Entity, place: Place, offering: Offering) -> None:
    hero.memes["generosity"] += 1
    hero.memes["understanding"] += 1
    mint = world.get("mint_patch")
    spring = world.get("spring")
    mint.meters["wilt"] = 0.0
    mint.meters["bloom"] += 1
    spring.meters["flow"] += 1
    world.say(
        f"Before nightfall, {hero.id} hurried back down the path. The stranger was gone, "
        f"but dew had gathered on the stones where {visitor_label(world)} had sat."
    )
    world.say(
        f"{hero.id} {offering.repair_text} for the next weary traveler and planted fresh mint beside the spring."
    )
    world.say(
        f"By dawn, the little leaves stood upright and sweet. From then on, people said {place.ending}"
    )


def blessed_ending(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"When {hero.id} reached the shrine, the empty vessel no longer looked empty. "
        f"The lamp burned clear, and cool water whispered somewhere inside the rock."
    )
    world.say(
        f'{elder.label.capitalize()} bowed to the hill and smiled. "Now you know the oldest law," '
        f'{elder.pronoun()} said. "What is shared in mercy returns in abundance."'
    )
    world.say(
        f"Below them the mint patch shone green in the evening light, and people later said {place.ending}"
    )


def visitor_label(world: World) -> str:
    return world.facts["visitor_cfg"].label
def tell(
    offering: Offering,
    visitor_cfg: Visitor,
    carrier: Carrier,
    choice: str,
    name: str,
    gender: str,
    elder_type: ElderType,
    place=None,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, role="hero"))
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label="the village elder" if elder_type not in {"mother", "father"} else f"{hero.pronoun('possessive')} {elder_type}",
            role="elder",
        )
    )
    visitor = world.add(Entity(id="visitor", kind="character", type="person", label=visitor_cfg.label, role="visitor"))
    offering_ent = world.add(Entity(id="offering", type="offering", label=offering.label))
    shrine = world.add(Entity(id="shrine", type="shrine", label=place.shrine))
    spring = world.add(Entity(id="spring", type="spring", label="the spring"))
    mint_patch = world.add(Entity(id="mint_patch", type="plant", label="the mint patch"))

    offering_ent.meters["remaining"] = float(offering.amount)
    visitor.meters["need"] = 0.0
    spring.meters["flow"] = 0.0
    mint_patch.meters["bloom"] = 0.0
    mint_patch.meters["wilt"] = 0.0
    shrine.meters["offering_delivered"] = 0.0
    hero.memes["generosity"] = 0.0
    hero.memes["refusal"] = 0.0

    world.facts.update(
        place=place,
        offering=offering,
        visitor_cfg=visitor_cfg,
        carrier=carrier,
        choice=choice,
        hero=hero,
        elder=elder,
        visitor=visitor,
    )

    introduce(world, hero, elder, place, offering, carrier)
    charge(world, hero, elder, offering)

    world.para()
    encounter(world, hero, visitor, visitor_cfg, place)
    warning(world, hero, choice)

    world.para()
    if choice == "share":
        share(world, hero, visitor, offering, visitor_cfg)
        world.para()
        blessed_ending(world, hero, elder, place)
    else:
        refuse(world, hero, visitor_cfg)
        world.para()
        deliver(world, hero, place, offering)
        elder_lesson(world, hero, elder)
        world.para()
        repair(world, hero, place, offering)

    world.facts.update(
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                offering=offering.id,
                visitor=visitor_cfg.id,
                carrier=carrier.id,
                choice=choice,
                name=name,
                gender=gender,
                elder=elder_type,
            )
        ),
        shared=choice == "share",
        refused=choice == "refuse",
        blessing=world.get("spring").meters["flow"] >= THRESHOLD and choice == "share",
        learned=hero.memes["understanding"] >= THRESHOLD or choice == "share",
    )
    return world
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


PLACES = {
    "hill_shrine": Place(
        id="hill_shrine",
        village="Juniper Hollow",
        shrine="the Shrine of the Listening Hill",
        path="the white goat-path",
        sky="The evening sky was coppery, and even the cicadas sounded thirsty.",
        patch="a low spring",
        ending="the hill remembered that kindness and answered it with water",
        tags={"shrine", "hill"},
    ),
    "river_steps": Place(
        id="river_steps",
        village="Reed Lantern Village",
        shrine="the Shrine Above the River Steps",
        path="the worn stair of river-stones",
        sky="Cloudless light lay over the valley, and the air held the warm hush of a waiting prayer.",
        patch="the old river spring",
        ending="the river gave sweetest water to hands that did not close too quickly",
        tags={"shrine", "river"},
    ),
    "sun_gate": Place(
        id="sun_gate",
        village="Cedar Gate",
        shrine="the Gate Shrine of Dawn",
        path="the sun-baked path of carved lions",
        sky="The western sky burned gold, while the valley below already darkened into shadow.",
        patch="the lion spring",
        ending="the dawn gate opened widest for the generous heart",
        tags={"shrine", "gate"},
    ),
}

OFFERINGS = {
    "mint_water": Offering(
        id="mint_water",
        label="mint water",
        phrase="a bowl of cool mint water",
        kind="liquid",
        amount=2,
        scent="cool and green",
        carry_text="The mint smell rose around her face, cool and green, and for a moment she felt almost as solemn as a priestess.",
        share_text="tilted the bowl and let the stranger drink the mint water",
        shrine_text="set down the bowl meant for the altar",
        repair_text="left a fresh bowl of mint water on the spring stone",
        tags={"mint", "water"},
    ),
    "mint_bread": Offering(
        id="mint_bread",
        label="mint bread",
        phrase="rounds of warm mint bread",
        kind="food",
        amount=2,
        scent="soft and sweet",
        carry_text="Warm bread and crushed mint made the path smell kinder than the hard summer dust.",
        share_text="broke the mint bread and placed the soft pieces into the stranger's hands",
        shrine_text="laid the mint bread before the carved stone",
        repair_text="wrapped fresh mint bread in clean cloth and left it at the spring",
        tags={"mint", "bread"},
    ),
    "mint_bundle": Offering(
        id="mint_bundle",
        label="mint bundle",
        phrase="a braided bundle of fresh mint",
        kind="herb",
        amount=2,
        scent="sharp and bright",
        carry_text="Its leaves brushed her wrist, and the sharp scent of mint kept the climb from feeling lonely.",
        share_text="placed the braided mint beneath the stranger's hands so its cool leaves touched the hot skin there",
        shrine_text="hung the mint braid beside the shrine lamp",
        repair_text="tied a new mint braid above the spring for any traveler worn by fever or heat",
        tags={"mint", "herb"},
    ),
}

VISITORS = {
    "thirsty_traveler": Visitor(
        id="thirsty_traveler",
        label="a thirsty traveler",
        need_kind="liquid",
        need_word="thirst",
        ask='"Child," the traveler whispered, "my mouth is dry as chalk. Will you spare even a little?"',
        relief="The stranger drank slowly, and color came back to the cracked lips.",
        reveal="Then the traveler's dusty cloak stirred though no hand touched it, and for one heartbeat the child's face was lit by eyes as clear as spring water.",
        tags={"traveler", "thirst"},
    ),
    "hungry_wanderer": Visitor(
        id="hungry_wanderer",
        label="a hungry wanderer",
        need_kind="food",
        need_word="hunger",
        ask='"Child," said the wanderer, "I have crossed three ridges on an empty belly. Is there any kindness in your basket?"',
        relief="The stranger ate with careful gratitude, as if each bite were a small rescue.",
        reveal="When the last crumb was gone, the dust around the wanderer's sandals lifted in a bright ring, and the child could not tell whether a mortal or a spirit sat there.",
        tags={"traveler", "hunger"},
    ),
    "fevered_shepherd": Visitor(
        id="fevered_shepherd",
        label="a fevered shepherd",
        need_kind="herb",
        need_word="fever",
        ask='"Child," murmured the shepherd, "the sun is hammering inside my head. Have you any cool herb to ease it?"',
        relief="As the mint touched the brow, the stranger's breathing eased and the tightness left the face.",
        reveal="A breeze moved through the dry grass, carrying the smell of rain, and the shepherd's worn cloak flashed green as a leaf before looking old again.",
        tags={"traveler", "fever"},
    ),
}

CARRIERS = {
    "clay_bowl": Carrier(
        id="clay_bowl",
        label="a clay bowl",
        phrase="a clay bowl",
        supports={"liquid"},
        capacity=2,
        tags={"bowl"},
    ),
    "reed_basket": Carrier(
        id="reed_basket",
        label="a reed basket",
        phrase="a reed basket",
        supports={"food", "herb"},
        capacity=3,
        tags={"basket"},
    ),
    "linen_wrap": Carrier(
        id="linen_wrap",
        label="a linen wrap",
        phrase="a clean linen wrap",
        supports={"herb"},
        capacity=2,
        tags={"cloth"},
    ),
    "bronze_plate": Carrier(
        id="bronze_plate",
        label="a bronze plate",
        phrase="a bronze plate",
        supports={"food"},
        capacity=2,
        tags={"plate"},
    ),
}

GIRL_NAMES = ["Nera", "Ione", "Thale", "Mira", "Cyra", "Dara"]
BOY_NAMES = ["Lykos", "Timon", "Aren", "Damon", "Pelas", "Orin"]
TRAITS = ["gentle", "careful", "earnest", "thoughtful", "bright-hearted"]
@dataclass
class StoryParams:
    place: str
    offering: str
    visitor: str
    carrier: str
    choice: str
    name: str
    gender: str
    elder: str
    trait: str = "earnest"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="hill_shrine",
        offering="mint_water",
        visitor="thirsty_traveler",
        carrier="clay_bowl",
        choice="share",
        name="Nera",
        gender="girl",
        elder="mother",
        trait="gentle",
    ),
    StoryParams(
        place="river_steps",
        offering="mint_bread",
        visitor="hungry_wanderer",
        carrier="reed_basket",
        choice="share",
        name="Timon",
        gender="boy",
        elder="father",
        trait="careful",
    ),
    StoryParams(
        place="sun_gate",
        offering="mint_bundle",
        visitor="fevered_shepherd",
        carrier="linen_wrap",
        choice="share",
        name="Ione",
        gender="girl",
        elder="mother",
        trait="thoughtful",
    ),
    StoryParams(
        place="hill_shrine",
        offering="mint_water",
        visitor="thirsty_traveler",
        carrier="clay_bowl",
        choice="refuse",
        name="Aren",
        gender="boy",
        elder="father",
        trait="earnest",
    ),
    StoryParams(
        place="river_steps",
        offering="mint_bundle",
        visitor="fevered_shepherd",
        carrier="reed_basket",
        choice="refuse",
        name="Mira",
        gender="girl",
        elder="mother",
        trait="bright-hearted",
    ),
]


KNOWLEDGE = {
    "mint": [
        (
            "What is mint?",
            "Mint is a green herb with a cool smell and taste. People use it in drinks, food, and healing because it feels fresh."
        )
    ],
    "water": [
        (
            "Why does cool water help a thirsty person?",
            "Cool water helps because thirst means the body needs more water. Drinking it can make a tired, dry person feel better."
        )
    ],
    "bread": [
        (
            "Why can bread help a hungry traveler?",
            "Bread gives the body food and strength. A hungry traveler can keep walking more safely after eating."
        )
    ],
    "herb": [
        (
            "Why might people use herbs when someone feels hot or sick?",
            "Some herbs smell cool or soothing and can help a person feel calmer and fresher. In old stories, herbs are often part of caring for someone."
        )
    ],
    "shrine": [
        (
            "What is a shrine?",
            "A shrine is a special place where people bring prayers or gifts. In myths, it is often where people try to honor gods or spirits."
        )
    ],
    "generosity": [
        (
            "What does generosity mean?",
            "Generosity means giving help or sharing what you have. It matters most when it would be easy to hold everything for yourself."
        )
    ],
    "traveler": [
        (
            "Why do stories often show travelers asking for help?",
            "A traveler is far from home and may be tired, hungry, or thirsty. In many myths, helping a traveler shows what kind of heart a person has."
        )
    ],
}
KNOWLEDGE_ORDER = ["mint", "water", "bread", "herb", "shrine", "traveler", "generosity"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    offering = world.facts["offering"]
    visitor = world.facts["visitor_cfg"]
    hero = world.facts["hero"]
    outcome = world.facts["outcome"]
    if outcome == "blessing":
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "mint" and teaches generosity.',
            f"Tell a myth where {hero.id} carries {offering.phrase} to {place.shrine}, meets {visitor.label}, and shares the gift before reaching the altar.",
            "Write a gentle myth where a child chooses mercy over strict duty, and the world answers with a blessing."
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "mint" and teaches a moral value.',
        f"Tell a myth where {hero.id} carries {offering.phrase} to {place.shrine}, refuses {visitor.label} at first, and learns that kindness matters more than pride.",
        "Write a myth with a child-facing lesson: a closed hand may finish a task, but only an open hand brings peace."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    place = world.facts["place"]
    offering = world.facts["offering"]
    visitor = world.facts["visitor_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child from {place.village}, and {visitor.label} on the way to {place.shrine}. The story also includes {elder.label}, who helps explain the lesson at the end."
        ),
        (
            f"What was {hero.id} carrying?",
            f"{hero.id} was carrying {offering.phrase} up the hill. The mint gift was meant for the shrine, which is why the choice felt hard."
        ),
        (
            "What was the problem on the path?",
            f"{visitor.label.capitalize()} asked for help before {hero.id} reached the shrine. That put duty on one side and kindness on the other."
        ),
    ]
    if outcome == "blessing":
        qa.append(
            (
                f"Why did the hill bless {hero.id}?",
                f"The hill blessed {hero.id} because {hero.pronoun()} shared the offering with someone who truly needed it. In this myth, mercy mattered more than arriving with a full gift."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"The spring flowed, the mint patch brightened, and the shrine answered with clear favor. Those changes show that the world itself welcomed the generous choice."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} refused to help?",
                f"The offering reached the shrine, but the answer was thin and sad instead of bright. The drooping mint showed that the hard choice had been the wrong one."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that the gods care about open hands, not only full bowls. That is why {hero.pronoun()} went back and began leaving help for strangers beside the spring."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    offering = world.facts["offering"]
    tags = {"mint", "shrine", "traveler", "generosity"}
    if offering.kind == "liquid":
        tags.add("water")
    elif offering.kind == "food":
        tags.add("bread")
    elif offering.kind == "herb":
        tags.add("herb")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
helpful(O, V) :- offering(O), visitor(V), helps(O, K), needs(V, K).
carry_ok(C, O) :- carrier(C), offering(O), helps(O, K), supports(C, K), amount(O, A), capacity(C, Cap), Cap >= A.
valid(P, O, V, C) :- place(P), helpful(O, V), carry_ok(C, O).

outcome(blessing) :- chosen_choice(share).
outcome(lesson)   :- chosen_choice(refuse).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("helps", oid, offering.kind))
        lines.append(asp.fact("amount", oid, offering.amount))
    for vid, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", vid))
        lines.append(asp.fact("needs", vid, visitor.need_kind))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, carrier.capacity))
        for support in sorted(carrier.supports):
            lines.append(asp.fact("supports", cid, support))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_choice", params.choice)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    rows = asp.atoms(model, "outcome")
    return rows[0][0] if rows else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True)
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a mint offering, a weary stranger, and a moral choice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--choice", choices=["share", "refuse"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.offering and args.visitor:
        carrier = CARRIERS[args.carrier] if args.carrier else None
        offering = OFFERINGS[args.offering]
        visitor = VISITORS[args.visitor]
        if not helpful(offering, visitor) or (carrier is not None and not carry_ok(carrier, offering)):
            raise StoryError(explain_rejection(offering, visitor, carrier))
    if args.carrier and args.offering and not carry_ok(CARRIERS[args.carrier], OFFERINGS[args.offering]):
        raise StoryError(explain_rejection(OFFERINGS[args.offering], VISITORS[args.visitor] if args.visitor else next(iter(VISITORS.values())), CARRIERS[args.carrier]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.offering is None or combo[1] == args.offering)
        and (args.visitor is None or combo[2] == args.visitor)
        and (args.carrier is None or combo[3] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, offering_id, visitor_id, carrier_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father"])
    choice = args.choice or rng.choice(["share", "refuse"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        offering=offering_id,
        visitor=visitor_id,
        carrier=carrier_id,
        choice=choice,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Unknown offering: {params.offering})")
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.choice not in {"share", "refuse"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    place = PLACES[params.place]
    offering = OFFERINGS[params.offering]
    visitor = VISITORS[params.visitor]
    carrier = CARRIERS[params.carrier]
    if not helpful(offering, visitor) or not carry_ok(carrier, offering):
        raise StoryError(explain_rejection(offering, visitor, carrier))

    world = tell(
        place=place,
        offering=offering,
        visitor_cfg=visitor,
        carrier=carrier,
        choice=params.choice,
        name=params.name,
        gender=params.gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, offering, visitor, carrier) combos:\n")
        for place, offering, visitor, carrier in combos:
            print(f"  {place:12} {offering:11} {visitor:16} {carrier}")
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
            header = f"### {p.name}: {p.choice} {p.offering} for {p.visitor} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
