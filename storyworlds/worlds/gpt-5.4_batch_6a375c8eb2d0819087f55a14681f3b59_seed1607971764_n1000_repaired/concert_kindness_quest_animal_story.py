#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py
=================================================================

A standalone story world for a tiny Animal Story domain built from the seed:
**concert + Kindness + Quest**.

Premise
-------
A small animal is excited to play in a forest concert, but an important part of
the performance goes missing on the way. The hero sets off on a short quest,
finds another animal in trouble, chooses kindness first, and that kindness leads
to the missing item being recovered. The ending image proves what changed: the
concert can happen because the hero helped before hurrying.

Run it
------
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --performance violin --helper squirrel
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --performance flute --helper mole
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --json
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/concert_kindness_quest_animal_story.py --verify
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Venue:
    id: str
    place: str
    glow: str
    affords: set[str] = field(default_factory=set)
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
class Performance:
    id: str
    instrument: str
    item: str
    item_phrase: str
    lost_place: str
    opening: str
    closing: str
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
class HelperKind:
    id: str
    animal: str
    skill_place: str
    problem: str
    ask: str
    kindness_text: str
    retrieve_text: str
    thanks: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_missing_worry(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["quest"] += 1
    return []


def _r_kindness_gratitude(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["kindness"] < THRESHOLD:
        return []
    sig = ("gratitude", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["gratitude"] += 1
    helper.memes["trust"] += 1
    return []


def _r_gratitude_recovers(world: World) -> list[str]:
    helper = world.get("helper")
    item = world.get("item")
    hero = world.get("hero")
    if helper.memes["gratitude"] < THRESHOLD or item.meters["missing"] < THRESHOLD:
        return []
    if helper.attrs.get("skill_place") != item.attrs.get("lost_place"):
        return []
    sig = ("recover", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["recovered"] += 1
    hero.memes["hope"] += 1
    hero.memes["worry"] = 0.0
    return []


def _r_recovered_ready(world: World) -> list[str]:
    hero = world.get("hero")
    concert = world.get("concert")
    item = world.get("item")
    if item.meters["recovered"] < THRESHOLD or hero.meters["at_concert"] < THRESHOLD:
        return []
    sig = ("ready", concert.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    concert.meters["ready"] += 1
    hero.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="kindness_gratitude", tag="social", apply=_r_kindness_gratitude),
    Rule(name="gratitude_recovers", tag="physical", apply=_r_gratitude_recovers),
    Rule(name="recovered_ready", tag="physical", apply=_r_recovered_ready),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def helper_can_reach(perf: Performance, helper: HelperKind) -> bool:
    return perf.lost_place == helper.skill_place


def venue_supports(venue: Venue, perf: Performance) -> bool:
    return perf.id in venue.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for perf_id, perf in PERFORMANCES.items():
            if not venue_supports(venue, perf):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_can_reach(perf, helper):
                    combos.append((venue_id, perf_id, helper_id))
    return combos


def explain_rejection(perf: Performance, helper: HelperKind) -> str:
    if perf.lost_place != helper.skill_place:
        return (
            f"(No story: {helper.animal.capitalize()} can help at the {helper.skill_place.replace('_', ' ')}, "
            f"but a {perf.item} would be lost at the {perf.lost_place.replace('_', ' ')}. "
            f"Pick a helper whose special skill matches the quest.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def explain_venue(venue: Venue, perf: Performance) -> str:
    return (
        f"(No story: {venue.place} does not host the {perf.instrument} act in this world. "
        f"Choose a venue that fits that concert performance.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_recovery(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["kindness"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "recovered": item.meters["recovered"] >= THRESHOLD,
        "helper_grateful": sim.get("helper").memes["gratitude"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, venue: Venue, perf: Performance) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        f"In the deep green woods, {hero.id} the {hero.type} woke early with a happy flutter in "
        f"{hero.pronoun('possessive')} chest. That evening there would be a concert at {venue.place}, "
        f"and {hero.pronoun()} had been chosen to {perf.opening}."
    )
    world.say(
        f"{venue.glow} All day long, the thought of the concert made even small stones on the path "
        f"seem easy to hop over."
    )


def discover_loss(world: World, hero: Entity, perf: Performance) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} checked {hero.pronoun('possessive')} {perf.instrument}, "
        f"{hero.pronoun()} gave a little gasp. {perf.item_phrase.capitalize()} was gone."
    )
    world.say(
        f"A breeze had carried it toward the {perf.lost_place.replace('_', ' ')}, and without it "
        f"{hero.pronoun()} could not {perf.closing} at the concert."
    )


def begin_quest(world: World, hero: Entity, perf: Performance) -> None:
    world.say(
        f'"I must find it before sunset," {hero.id} whispered, and off {hero.pronoun()} went on a quick quest '
        f"through the trees."
    )


def meet_helper(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    world.say(
        f"Near the path, {hero.id} found {helper.id} the {helper.type} in trouble. {helper_cfg.problem}"
    )
    world.say(
        f'"Oh dear," said {helper.id}. "{helper_cfg.ask}"'
    )


def choose_kindness(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    pred = predict_recovery(world)
    world.facts["predicted_recovery"] = pred["recovered"]
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    helper.meters["trouble"] = 0.0
    helper.meters["helped"] += 1
    world.say(
        f"{hero.id} looked toward the darkening woods, then back at {helper.id}. "
        f"Even with the concert waiting, {hero.pronoun()} stopped to help."
    )
    world.say(helper_cfg.kindness_text)


def retrieve_item(world: World, hero: Entity, helper: Entity, perf: Performance, helper_cfg: HelperKind) -> None:
    propagate(world, narrate=False)
    item = world.get("item")
    if item.meters["recovered"] < THRESHOLD:
        raise StoryError("The quest failed inside the world model: kindness did not lead to recovery.")
    world.say(helper_cfg.thanks)
    world.say(
        helper_cfg.retrieve_text.format(
            hero=hero.id,
            item=perf.item,
            lost_place=perf.lost_place.replace("_", " "),
        )
    )


def arrive_concert(world: World, hero: Entity, helper: Entity, venue: Venue, perf: Performance) -> None:
    hero.meters["at_concert"] += 1
    propagate(world, narrate=False)
    concert = world.get("concert")
    if concert.meters["ready"] < THRESHOLD:
        raise StoryError("The concert could not become ready after the item was recovered.")
    world.say(
        f"Together they hurried to {venue.place}, where lantern bugs were already blinking over the little stage."
    )
    world.say(
        f"When it was time, {hero.id} stepped forward and {perf.closing}. The concert sounded warm and bright, "
        f"as if the whole forest had learned the song of kindness too."
    )
    world.say(
        f"At the end, {hero.id} bowed toward {helper.id} first, and the animals clapped their paws, wings, and tails. "
        f"From then on, whenever anyone spoke of that concert, they remembered not just the music, but the kind stop "
        f"that made it possible."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    venue: Venue,
    perf: Performance,
    helper_cfg: HelperKind,
    hero_name: str = "Pip",
    hero_type: str = "rabbit",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=hero_type,
            role="hero",
            attrs={},
            tags={"hero"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.animal.capitalize(),
            kind="character",
            type=helper_cfg.animal,
            label=helper_cfg.animal,
            role="helper",
            attrs={"skill_place": helper_cfg.skill_place},
            tags=set(helper_cfg.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="music_item",
            label=perf.item,
            phrase=perf.item_phrase,
            role="missing_item",
            attrs={"lost_place": perf.lost_place},
            tags=set(perf.tags),
        )
    )
    concert = world.add(
        Entity(
            id="concert",
            kind="thing",
            type="concert",
            label="concert",
            phrase=f"the concert at {venue.place}",
            role="concert",
            attrs={"venue": venue.id},
            tags={"concert"} | set(venue.tags),
        )
    )

    helper.meters["trouble"] = 1.0
    item.meters["missing"] = 0.0
    item.meters["recovered"] = 0.0
    hero.meters["at_concert"] = 0.0
    concert.meters["ready"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    helper.memes["gratitude"] = 0.0
    helper.memes["trust"] = 0.0

    world.facts.update(
        venue=venue,
        performance=perf,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        item=item,
        concert=concert,
        recovered=False,
        solved_by_kindness=False,
    )

    introduce(world, hero, venue, perf)
    world.para()
    discover_loss(world, hero, perf)
    begin_quest(world, hero, perf)

    world.para()
    meet_helper(world, hero, helper, helper_cfg)
    choose_kindness(world, hero, helper, helper_cfg)
    retrieve_item(world, hero, helper, perf, helper_cfg)

    world.para()
    arrive_concert(world, hero, helper, venue, perf)

    world.facts.update(
        recovered=item.meters["recovered"] >= THRESHOLD,
        solved_by_kindness=hero.memes["kindness"] >= THRESHOLD and item.meters["recovered"] >= THRESHOLD,
        concert_ready=concert.meters["ready"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
VENUES = {
    "moonlit_meadow": Venue(
        id="moonlit_meadow",
        place="the moonlit meadow",
        glow="By evening, silver light would spill over the grass there.",
        affords={"violin", "drum"},
        tags={"meadow", "concert"},
    ),
    "willow_bank": Venue(
        id="willow_bank",
        place="the willow bank",
        glow="By evening, the willow leaves would whisper over the water there.",
        affords={"flute", "violin"},
        tags={"pond", "concert"},
    ),
    "hollow_stump": Venue(
        id="hollow_stump",
        place="the hollow stump clearing",
        glow="By evening, fireflies would circle the round old stump there.",
        affords={"drum", "flute"},
        tags={"clearing", "concert"},
    ),
}

PERFORMANCES = {
    "violin": Performance(
        id="violin",
        instrument="violin",
        item="bow",
        item_phrase="the smooth violin bow",
        lost_place="pine_branch",
        opening="play the violin for the first song",
        closing="drew the bow across the strings for the first sweet tune",
        tags={"violin", "music"},
    ),
    "flute": Performance(
        id="flute",
        instrument="flute",
        item="reed",
        item_phrase="the little singing reed",
        lost_place="pond_edge",
        opening="play the flute when the moon rose",
        closing="lifted the flute and sent a clear, floating note across the crowd",
        tags={"flute", "music"},
    ),
    "drum": Performance(
        id="drum",
        instrument="drum",
        item="drumstick",
        item_phrase="the striped drumstick",
        lost_place="burrow_mouth",
        opening="beat the drum for the marching song",
        closing="tapped the drum in a brave, steady rhythm",
        tags={"drum", "music"},
    ),
}

HELPERS = {
    "squirrel": HelperKind(
        id="squirrel",
        animal="squirrel",
        skill_place="pine_branch",
        problem="A basket of pinecones had tipped over, and the cones were rolling every which way.",
        ask="Would you help me gather these before they bump into the stream?",
        kindness_text="So {hero} set down the violin case, scampered after the pinecones, and stacked them neatly back into the basket.".format(
            hero="Pip"
        ),
        retrieve_text="{hero}'s friend flicked up the pine tree in a rustly flash and soon came down holding the {item} that had snagged on the pine branch.",
        thanks='"You helped me when you were in a hurry," said Squirrel. "Now let me help you."',
        tags={"squirrel", "tree"},
    ),
    "otter": HelperKind(
        id="otter",
        animal="otter",
        skill_place="pond_edge",
        problem="A bundle of cattail ribbons had slipped apart, and the water kept tugging them away.",
        ask="Could you hold my reed basket steady while I tie this bundle again?",
        kindness_text="So {hero} planted steady feet on the bank and held the basket still until the ribbons were safe again.".format(
            hero="Pip"
        ),
        retrieve_text="Otter slipped into the water with hardly a splash and came back with the {item}, which had drifted beside the pond edge like a tiny boat.",
        thanks='"That was a kind thing to do," said Otter. "Kind paws should not miss the concert."',
        tags={"otter", "pond"},
    ),
    "mole": HelperKind(
        id="mole",
        animal="mole",
        skill_place="burrow_mouth",
        problem="A little cart of seed cakes was stuck crooked at the mouth of a burrow, and Mole could not tug it free alone.",
        ask="Will you push from one side while I pull from the other?",
        kindness_text="So {hero} braced against the earth and pushed until the tiny cart bumped free with a soft puff of dust.".format(
            hero="Pip"
        ),
        retrieve_text="Mole nosed into the dark burrow mouth, then popped back out proudly carrying the {item} that had rolled just inside.",
        thanks='"You did not hurry past me," said Mole. "A helper like you deserves a happy song."',
        tags={"mole", "burrow"},
    ),
}

HERO_TYPES = ["rabbit", "mouse", "fox", "fawn", "hedgehog"]
HERO_NAMES = ["Pip", "Mimi", "Nettle", "Hazel", "Moss", "Tumble", "Poppy"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    venue: str
    performance: str
    helper: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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
    "concert": [
        (
            "What is a concert?",
            "A concert is a time when people or animals gather to listen to music. Different players or singers take turns making songs for everyone to hear.",
        )
    ],
    "violin": [
        (
            "What does a violin bow do?",
            "A violin bow is drawn across the strings to make them sing. Without the bow, the violin player cannot make the usual smooth notes.",
        )
    ],
    "flute": [
        (
            "Why does a flute need a reed or mouthpiece part?",
            "A flute needs the right part at the blowing end so the air can make a clear sound. If that piece is missing, the tune cannot come out properly.",
        )
    ],
    "drum": [
        (
            "What is a drumstick for?",
            "A drumstick is used to tap a drum and make a beat. It helps the music sound steady and strong.",
        )
    ],
    "squirrel": [
        (
            "Why are squirrels good at reaching high branches?",
            "Squirrels can climb trees quickly with their sharp claws and balance. That makes them good at reaching things caught up high.",
        )
    ],
    "otter": [
        (
            "Why are otters good at fetching things near water?",
            "Otters are strong swimmers, so they can slip through water easily. They are good at reaching things floating or bobbing near a bank.",
        )
    ],
    "mole": [
        (
            "Why can moles find things in burrows?",
            "Moles live close to tunnels and soft earth, so they know how to nose around in burrows. They are good at reaching small things hidden underground.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone. A kind act can change what happens next for both the giver and the one who is helped.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose, like going to find something important. Even a short trip can be a quest when there is a problem to solve.",
        )
    ],
}
KNOWLEDGE_ORDER = ["concert", "kindness", "quest", "violin", "flute", "drum", "squirrel", "otter", "mole"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    perf = world.facts["performance"]
    helper = world.facts["helper_cfg"]
    venue = world.facts["venue"]
    return [
        'Write a short Animal Story for a 3-to-5-year-old that includes the word "concert" and features kindness and a quest.',
        f"Tell a gentle forest story where {hero.id} the {hero.type} is on the way to a concert at {venue.place}, loses a {perf.item}, and helps a {helper.animal} before getting the missing piece back.",
        f"Write a child-facing story where a small animal chooses kindness first, and that kind choice is what lets the music be played at the concert in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    perf = world.facts["performance"]
    venue = world.facts["venue"]
    helper_cfg = world.facts["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who was hurrying to play at a concert, and {helper.id} the {helper.type}, who needed help on the path.",
        ),
        (
            f"Why did {hero.id} go on a quest?",
            f"{hero.id} went on a quest because the {perf.item} needed for the {perf.instrument} was missing. Without it, {hero.pronoun()} could not play properly at the concert.",
        ),
        (
            f"What trouble did {helper.id} have?",
            f"{helper.id} was in trouble because {helper_cfg.problem.lower()} {hero.id} met {helper.pronoun('object')} before the concert and had to decide whether to stop and help.",
        ),
        (
            f"How did kindness change what happened?",
            f"{hero.id} chose kindness first and helped {helper.id} even though the concert was waiting. Because of that kind stop, {helper.id} gladly used {helper.pronoun('possessive')} special skill to recover the missing {perf.item}.",
        ),
        (
            f"How did the story end?",
            f"The story ended at the concert in {venue.place}, where {hero.id} could finally play. The music itself showed what had changed, because the concert happened only after the kind deed on the quest.",
        ),
    ]
    if world.facts.get("concert_ready"):
        qa.append(
            (
                f"Why did the other animals remember that concert?",
                f"They remembered the concert because the music was lovely, but also because it had a kind beginning. The path to the concert became part of the story when kindness helped the song happen.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    perf = world.facts["performance"]
    helper_cfg = world.facts["helper_cfg"]
    tags = {"concert", "kindness", "quest", perf.id, helper_cfg.id}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_reach(H, P) :- helper(H), skill_place(H, P).
valid(V, Perf, H) :- venue(V), performance(Perf), helper(H),
                     affords(V, Perf), lost_place(Perf, P), can_reach(H, P).

recovered_by_kindness(Perf, H) :- lost_place(Perf, P), can_reach(H, P).
story_possible(V, Perf, H) :- valid(V, Perf, H), recovered_by_kindness(Perf, H).

#show valid/3.
#show story_possible/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for perf_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, perf_id))
    for perf_id, perf in PERFORMANCES.items():
        lines.append(asp.fact("performance", perf_id))
        lines.append(asp.fact("lost_place", perf_id, perf.lost_place))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill_place", helper_id, helper.skill_place))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_possible() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "story_possible")))


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a concert, a kind quest, and a missing music piece."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--performance", choices=PERFORMANCES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.performance and args.helper:
        perf = PERFORMANCES[args.performance]
        helper = HELPERS[args.helper]
        if not helper_can_reach(perf, helper):
            raise StoryError(explain_rejection(perf, helper))
    if args.venue and args.performance:
        venue = VENUES[args.venue]
        perf = PERFORMANCES[args.performance]
        if not venue_supports(venue, perf):
            raise StoryError(explain_venue(venue, perf))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.performance is None or combo[1] == args.performance)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, perf_id, helper_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    return StoryParams(
        venue=venue_id,
        performance=perf_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.performance not in PERFORMANCES:
        raise StoryError(f"(Unknown performance: {params.performance})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    venue = VENUES[params.venue]
    perf = PERFORMANCES[params.performance]
    helper_cfg = HELPERS[params.helper]

    if not venue_supports(venue, perf):
        raise StoryError(explain_venue(venue, perf))
    if not helper_can_reach(perf, helper_cfg):
        raise StoryError(explain_rejection(perf, helper_cfg))

    world = tell(
        venue=venue,
        perf=perf,
        helper_cfg=helper_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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


CURATED = [
    StoryParams(
        venue="moonlit_meadow",
        performance="violin",
        helper="squirrel",
        hero_name="Pip",
        hero_type="rabbit",
        seed=None,
    ),
    StoryParams(
        venue="willow_bank",
        performance="flute",
        helper="otter",
        hero_name="Mimi",
        hero_type="mouse",
        seed=None,
    ),
    StoryParams(
        venue="hollow_stump",
        performance="drum",
        helper="mole",
        hero_name="Hazel",
        hero_type="hedgehog",
        seed=None,
    ),
    StoryParams(
        venue="willow_bank",
        performance="violin",
        helper="squirrel",
        hero_name="Moss",
        hero_type="fawn",
        seed=None,
    ),
    StoryParams(
        venue="hollow_stump",
        performance="flute",
        helper="otter",
        hero_name="Poppy",
        hero_type="fox",
        seed=None,
    ),
]


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    possible_set = set(asp_story_possible())
    if possible_set == python_set:
        print("OK: story_possible/3 matches the valid combo set.")
    else:
        rc = 1
        print("MISMATCH in story_possible/3:")
        if python_set - possible_set:
            print("  missing in clingo:", sorted(python_set - possible_set))
        if possible_set - python_set:
            print("  extra in clingo:", sorted(possible_set - python_set))

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke test")
        finally:
            sys.stdout = old
        if not sample.story or "concert" not in sample.story:
            raise StoryError("Smoke test story did not render as expected.")
        sample.to_dict()
        print("OK: smoke test generate/emit/json succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story:
                raise StoryError("Generated empty story.")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation succeeded on 10 seeded runs.")

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
        print(f"{len(combos)} compatible (venue, performance, helper) combos:\n")
        for venue_id, perf_id, helper_id in combos:
            print(f"  {venue_id:15} {perf_id:8} {helper_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.performance} at {p.venue} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
