#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py
===============================================================================

A standalone story world in a folk-tale mode: a child hears a frightened bird
calling near a kennel, faces a noisy dog and a high nest, and learns that
bravery can mean either climbing carefully or asking for a steady hand.

Run it
------
    python storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py
    python storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py --nest beam --aid ladder
    python storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py --calm stick
    python storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py --all --qa
    python storyworlds/worlds/gpt-5.4/perspective_kennel_coo_bravery_sound_effects_folk.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Yard:
    id: str
    place: str
    season_line: str
    kennel_line: str
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
class Bird:
    id: str
    label: str
    little_one: str
    flock_sound: str
    mother_phrase: str
    color_line: str
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
class Nest:
    id: str
    label: str
    site: str
    height: int
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
class Aid:
    id: str
    label: str
    phrase: str
    reach: int
    steadiness: int
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
class CalmChoice:
    id: str
    label: str
    phrase: str
    sense: int
    calm_power: int
    text: str
    qa_text: str
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


def _r_bark_fear(world: World) -> list[str]:
    dog = world.get("dog")
    child = world.get("child")
    chick = world.get("chick")
    if dog.meters["barking"] < THRESHOLD:
        return []
    sig = ("bark_fear", int(dog.meters["barking"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    chick.memes["fear"] += 1
    return []


def _r_calm_quiet(world: World) -> list[str]:
    dog = world.get("dog")
    child = world.get("child")
    if child.meters["calming"] < THRESHOLD:
        return []
    sig = ("calm_quiet", int(child.meters["calming"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if child.meters["calming"] >= dog.meters["barking"]:
        dog.meters["barking"] = 0.0
        dog.memes["peace"] += 1
    return []


def _r_return_relief(world: World) -> list[str]:
    chick = world.get("chick")
    mother = world.get("mother_bird")
    child = world.get("child")
    if chick.meters["safe"] < THRESHOLD:
        return []
    sig = ("return_relief", chick.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mother.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="bark_fear", tag="emotional", apply=_r_bark_fear),
    Rule(name="calm_quiet", tag="social", apply=_r_calm_quiet),
    Rule(name="return_relief", tag="resolution", apply=_r_return_relief),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                continue
            else:
                continue
        current_count = len(world.fired)
        if produced or current_count:
            pass
        changed = len(world.fired) > current_count if False else changed
        again = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            out = rule.apply(world)
            if out:
                produced.extend(out)
            if len(world.fired) > before:
                again = True
        if again:
            changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def dog_noise(level: int) -> str:
    return {
        1: "Ruff! Ruff!",
        2: "Woof! Woof!",
        3: "BOW-WOW! BOW-WOW!",
    }[level]


def bravery_of(trait: str) -> int:
    return {
        "bold": 3,
        "steady": 2,
        "gentle": 2,
        "careful": 1,
    }[trait]


def sensible_calms() -> list[CalmChoice]:
    return [c for c in CALM_CHOICES.values() if c.sense >= SENSE_MIN]


def nest_reachable(aid: Aid, nest: Nest) -> bool:
    return aid.reach >= nest.height


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for yard_id in YARDS:
        for bird_id in BIRDS:
            for nest_id, nest in NESTS.items():
                for aid_id, aid in AIDS.items():
                    for calm_id, calm in CALM_CHOICES.items():
                        if nest_reachable(aid, nest) and calm.sense >= SENSE_MIN:
                            combos.append((yard_id, bird_id, nest_id, aid_id, calm_id))
    return combos


def explain_rejection(nest: Nest, aid: Aid) -> str:
    return (
        f"(No story: {aid.phrase} is not tall enough for the {nest.label} in {nest.site}. "
        f"Pick a steadier, taller way to reach the nest.)"
    )


def explain_calm(cid: str) -> str:
    calm = CALM_CHOICES[cid]
    better = ", ".join(sorted(c.id for c in sensible_calms()))
    return (
        f"(Refusing calm choice '{cid}': it scores too low on common sense "
        f"(sense={calm.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_quiet(world: World, calm: CalmChoice) -> bool:
    sim = world.copy()
    sim.get("child").meters["calming"] = float(calm.calm_power)
    propagate(sim, narrate=False)
    return sim.get("dog").meters["barking"] < THRESHOLD


def outcome_of(params: "StoryParams") -> str:
    nest = NESTS[params.nest]
    aid = AIDS[params.aid]
    calm = CALM_CHOICES[params.calm]
    brave = bravery_of(params.trait)
    bark = params.bark
    dog_quiet = calm.calm_power >= bark
    solo_power = brave + aid.steadiness + (1 if dog_quiet else 0)
    target = nest.height + bark
    return "alone" if solo_power >= target else "together"


def introduce(world: World, child: Entity, elder: Entity, yard: Yard, bird: Bird) -> None:
    world.say(
        f"In the old days, when wind talked in the reeds and chores were learned by song, "
        f"{child.id} lived beside {yard.place}. {yard.season_line}"
    )
    world.say(
        f"{yard.kennel_line} Near it, a little {bird.little_one} had slipped from home, "
        f'''while above, its mother wheeled in a gray ring and called, \"{bird.flock_sound}\"'''
    )


def show_problem(world: World, child: Entity, dog: Entity, chick: Entity, nest: Nest, bird: Bird) -> None:
    world.say(
        f"The little one shivered in the straw by the kennel, and the nest waited in "
        f"{nest.site}. {bird.color_line}"
    )
    world.say(
        f"Then the kennel dog sprang up. \"{dog_noise(int(dog.meters['barking']))}\" went the yard, "
        f"and the sound made the chick flatten itself smaller than a fallen leaf."
    )


def elder_perspective(world: World, child: Entity, elder: Entity, nest: Nest, bird: Bird) -> None:
    world.say(
        f"{child.id} took one step forward and one step back. "
        f"\"The way looks high from my perspective,\" {child.pronoun()} whispered."
    )
    world.say(
        f"{elder.id} knelt beside {child.pronoun('object')} and spoke as folk in that valley spoke: "
        f"\"From the little {bird.little_one}'s perspective, the world is all barking shadows. "
        f'''If you can help kindly, you should.\"'''
    )


def calm_dog(world: World, child: Entity, dog: Entity, calm: CalmChoice) -> None:
    child.meters["calming"] = float(calm.calm_power)
    child.memes["resolve"] += 1
    propagate(world, narrate=False)
    world.say(calm.text)
    if dog.meters["barking"] < THRESHOLD:
        world.say(
            f'The dog blinked, gave one last small "huff," and settled down inside the kennel.'
        )
    else:
        world.say(
            f'The dog still grumbled, "rrr-ruff, rrr-ruff," though not quite so fiercely as before.'
        )


def choose_aid(world: World, child: Entity, aid: Aid, nest: Nest) -> None:
    world.say(
        f"Then {child.id} fetched {aid.phrase} and set it below {nest.site}. "
        f"The wood gave a tiny \"tok\" on the ground."
    )


def climb_alone(world: World, child: Entity, chick: Entity, nest: Nest, bird: Bird) -> None:
    chick.meters["safe"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With knees that trembled a little but did not run away, {child.id} climbed alone. "
        f"Up, up, step by step, {child.pronoun()} reached {nest.site} and tucked the "
        f"{bird.little_one} back into the {nest.label}."
    )
    world.say(
        f'At once the mother bird dropped to the branch above and sang, "{bird.flock_sound}" '
        f'so softly that the whole yard seemed to listen.'
    )


def ask_help(world: World, child: Entity, elder: Entity, chick: Entity, aid: Aid, nest: Nest, bird: Bird) -> None:
    child.memes["wisdom"] += 1
    elder.memes["care"] += 1
    chick.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} laid a hand on the {aid.label} and then looked up at {elder.id}. "
        f'''\"I am brave enough to begin,\" {child.pronoun()} said, \"but not too proud to ask for help.\"'''
    )
    world.say(
        f"So {elder.id} held the {aid.label} steady from below while {child.id} climbed. "
        f"Together they reached {nest.site}, and together they set the {bird.little_one} back into the {nest.label}."
    )
    world.say(
        f'The mother bird swept near enough for them to hear each round note: "{bird.flock_sound}" '
        f'and then another, like thanks dropped into the air.'
    )


def ending(world: World, child: Entity, elder: Entity, yard: Yard, outcome: str) -> None:
    if outcome == "alone":
        world.say(
            f"After that day, whenever {child.id} passed the kennel, {child.pronoun()} remembered "
            f"that bravery was not the same as loudness. It was a steady heart, a gentle hand, and one good deed done in time."
        )
    else:
        world.say(
            f"After that day, whenever {child.id} passed the kennel, {child.pronoun()} remembered "
            f"that bravery could share its weight. A wise hand below can help a brave hand above."
        )
    world.say(
        f"And in the evenings, when dusk blue folded over {yard.place}, a soft coo drifted from the tree, "
        f"and the yard felt kinder than before."
    )

def tell(
    bird: Bird,
    nest: Nest,
    aid: Aid,
    calm: Calm,
    id: Id,
    label: Label,
    phrase: Phrase,
    sense: Sense,
    calm_power: CalmPower,
    text: Text,
    qa_text: QaText,
    tags: Tags,
    yard=None,
    child_name=None,
    child_gender=None,
    elder_type=None,
    trait=None,
    bark=None,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id=elder_type.capitalize(),
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={},
    ))
    dog = world.add(Entity(
        id="dog",
        kind="character",
        type="dog",
        role="dog",
        label="the kennel dog",
        attrs={"kennel": True},
    ))
    chick = world.add(Entity(
        id="chick",
        kind="thing",
        type="bird",
        role="chick",
        label=bird.little_one,
        attrs={},
    ))
    mother = world.add(Entity(
        id="mother_bird",
        kind="thing",
        type="bird",
        role="mother_bird",
        label=bird.label,
        attrs={},
    ))
    nest_ent = world.add(Entity(
        id="nest",
        kind="thing",
        type="nest",
        role="nest",
        label=nest.label,
        attrs={"site": nest.site},
    ))
    aid_ent = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        role="aid",
        label=aid.label,
        attrs={},
    ))

    child.memes["fear"] = 0.0
    child.memes["resolve"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["wisdom"] = 0.0
    child.memes["pride"] = 0.0
    elder.memes["care"] = 0.0
    dog.meters["barking"] = float(bark)
    dog.memes["peace"] = 0.0
    chick.memes["fear"] = 0.0
    chick.meters["safe"] = 0.0
    mother.memes["relief"] = 0.0
    aid_ent.meters["steadiness"] = float(aid.steadiness)
    nest_ent.meters["height"] = float(nest.height)

    world.facts.update(
        yard=yard,
        bird=bird,
        nest_cfg=nest,
        aid_cfg=aid,
        calm_cfg=calm,
        child=child,
        elder=elder,
        dog=dog,
        chick=chick,
        mother_bird=mother,
        bark=bark,
        trait=trait,
    )

    introduce(world, child, elder, yard, bird)
    show_problem(world, child, dog, chick, nest, bird)

    world.para()
    elder_perspective(world, child, elder, nest, bird)
    calm_dog(world, child, dog, calm)
    choose_aid(world, child, aid, nest)

    world.para()
    outcome = outcome_of(StoryParams(
        yard=yard.id,
        bird=bird.id,
        nest=nest.id,
        aid=aid.id,
        calm=calm.id,
        child_name=child_name,
        child_gender=child_gender,
        elder=elder_type,
        trait=trait,
        bark=bark,
        seed=None,
    ))
    if outcome == "alone":
        climb_alone(world, child, chick, nest, bird)
    else:
        ask_help(world, child, elder, chick, aid, nest, bird)

    world.para()
    ending(world, child, elder, yard, outcome)

    world.facts.update(
        outcome=outcome,
        dog_quiet=dog.meters["barking"] < THRESHOLD,
        returned=chick.meters["safe"] >= THRESHOLD,
    )
    return world
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


YARDS = {
    "farmyard": Yard(
        id="farmyard",
        place="the farmyard",
        season_line="It was spring, and the willow leaves shone like small green coins.",
        kennel_line="At the edge of the path stood a weathered kennel under a willow tree.",
        tags={"kennel", "yard"},
    ),
    "millyard": Yard(
        id="millyard",
        place="the millyard",
        season_line="It was early summer, and the mill wheel talked softly to the stream.",
        kennel_line="By the grain shed stood an old kennel with a roof silvered by rain.",
        tags={"kennel", "yard"},
    ),
    "orchard": Yard(
        id="orchard",
        place="the orchard yard",
        season_line="It was autumn, and the apples held the last warm gold of the day.",
        kennel_line="Near the gate stood a neat little kennel beside the fallen leaves.",
        tags={"kennel", "yard"},
    ),
}

BIRDS = {
    "dove": Bird(
        id="dove",
        label="dove",
        little_one="dove chick",
        flock_sound="coo, coo",
        mother_phrase="the mother dove",
        color_line="Its mother dove was pearl-gray, with a neck that flashed green in the sun.",
        tags={"coo", "bird"},
    ),
    "woodpigeon": Bird(
        id="woodpigeon",
        label="wood pigeon",
        little_one="pigeon chick",
        flock_sound="coo-ooo, coo",
        mother_phrase="the mother pigeon",
        color_line="Its mother pigeon was ash-gray, round as a plum and swift as a thought.",
        tags={"coo", "bird"},
    ),
}

NESTS = {
    "branch": Nest(
        id="branch",
        label="nest",
        site="the low fork of the willow",
        height=1,
        tags={"tree"},
    ),
    "beam": Nest(
        id="beam",
        label="nest",
        site="a beam above the shed door",
        height=2,
        tags={"beam"},
    ),
    "rafters": Nest(
        id="rafters",
        label="nest",
        site="the high orchard rafters",
        height=3,
        tags={"rafters"},
    ),
}

AIDS = {
    "crate": Aid(
        id="crate",
        label="crate",
        phrase="a turned apple crate",
        reach=1,
        steadiness=1,
        tags={"crate"},
    ),
    "stool": Aid(
        id="stool",
        label="stool",
        phrase="a three-legged milking stool",
        reach=2,
        steadiness=1,
        tags={"stool"},
    ),
    "ladder": Aid(
        id="ladder",
        label="ladder",
        phrase="the ash ladder from the shed wall",
        reach=3,
        steadiness=2,
        tags={"ladder"},
    ),
}

CALM_CHOICES = {
    "song": CalmChoice(
        id="song",
        label="song",
        phrase="a low song",
        sense=3,
        calm_power=1,
        text='So {name} began a low song, no louder than a warm kettle hum: "loo, loo, hush now."'.replace(
            "{name}", "{name}"
        ),
        qa_text="sang softly to settle the dog",
        tags={"song", "sound"},
    ),
    "biscuit": CalmChoice(
        id="biscuit",
        label="biscuit",
        phrase="a crust biscuit",
        sense=3,
        calm_power=3,
        text="{name} held out a crust biscuit on a flat palm and spoke in a quiet voice. "
             '"Easy now, old friend. Easy."',
        qa_text="offered the dog a biscuit and spoke gently",
        tags={"biscuit", "sound"},
    ),
    "cluck": CalmChoice(
        id="cluck",
        label="clucking tongue",
        phrase="a clucking tongue",
        sense=2,
        calm_power=2,
        text='{name} clicked {pos} tongue -- "tch-tch, easy, easy" -- and kept {pos} shoulders low.',
        qa_text="used a calm voice and a soft tongue-click",
        tags={"sound"},
    ),
    "stick": CalmChoice(
        id="stick",
        label="waving stick",
        phrase="a waving stick",
        sense=1,
        calm_power=0,
        text='{name} snatched up a stick and waved it about, which only made the kennel dog angrier.',
        qa_text="waved a stick at the dog",
        tags={"stick"},
    ),
}

GIRL_NAMES = ["Mara", "Anya", "Lina", "Tessa", "Nella", "Iva"]
BOY_NAMES = ["Ivo", "Milan", "Toma", "Bram", "Niko", "Pavel"]
TRAITS = ["bold", "steady", "gentle", "careful"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]


def _render_calm_text(calm: CalmChoice, child: Entity) -> str:
    return (
        calm.text
        .replace("{name}", child.id)
        .replace("{pos}", child.pronoun("possessive"))
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    bird = f["bird"]
    nest = f["nest_cfg"]
    return [
        f'Write a short folk-tale for a young child that includes the words "perspective", "kennel", and "coo".',
        f"Tell a folk-style story where {child.id} finds a {bird.little_one} beside a kennel and must help it back to {nest.site}.",
        "Write a gentle bravery story with sound effects, where barking turns quiet and a bird ends the tale with a soft coo.",
    ]


KNOWLEDGE = {
    "kennel": [(
        "What is a kennel?",
        "A kennel is a little house or shelter for a dog. It gives the dog a place to sleep and stay dry."
    )],
    "coo": [(
        "What does coo mean?",
        "Coo is a soft round bird sound, often made by doves and pigeons. It is much gentler than a bark."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps people reach places that are high up. It must be set carefully so it does not wobble."
    )],
    "stool": [(
        "What is a stool?",
        "A stool is a small seat with legs. A sturdy stool can help someone reach a little higher."
    )],
    "crate": [(
        "What is a crate?",
        "A crate is a box with firm sides, often used to carry fruit or other things. Turned over, it can make a low step."
    )],
    "bird_nest": [(
        "Why do birds build nests high up?",
        "Many birds build nests off the ground to keep their eggs and chicks safer. High places can help them stay away from danger."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery means doing the right thing even when you feel afraid. Sometimes bravery also means asking for help instead of pretending you do not need it."
    )],
    "gentle_dog": [(
        "How can someone calm a dog?",
        "A calm voice, quiet movements, and a trusted treat can help a dog settle. Sudden shouting or waving things can make a dog more upset."
    )],
}
KNOWLEDGE_ORDER = ["kennel", "coo", "bird_nest", "bravery", "gentle_dog", "crate", "stool", "ladder"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    bird = f["bird"]
    nest = f["nest_cfg"]
    calm = f["calm_cfg"]
    bark = f["bark"]
    dog_quiet = f["dog_quiet"]
    outcome = f["outcome"]

    calm_answer = {
        "song": f"{child.id} sang softly to the dog. The gentle sound helped take some of the sharpness out of the barking, even before the climbing began.",
        "biscuit": f"{child.id} offered the dog a biscuit and spoke in a quiet voice. That made the dog settle, because kindness felt safer than noise.",
        "cluck": f"{child.id} used a soft tongue-click and a low voice. The careful sound told the dog there was no danger.",
        "stick": f"{child.id} waved a stick, which was not a wise choice. In this world that choice is refused, because it would make the dog more upset instead of calmer.",
    }[calm.id]

    qa = [
        (
            "What problem began the story?",
            f"A little {bird.little_one} had fallen beside the kennel while its nest waited in {nest.site}. The barking dog made the place feel even more frightening for the bird."
        ),
        (
            "Why did the elder talk about perspective?",
            f"{elder.id} wanted {child.id} to look at the moment from the little bird's perspective, not only {child.pronoun('possessive')} own. That helped turn fear into kindness, because the chick's whole world felt loud and dangerous."
        ),
        (
            f"How did {child.id} calm the dog?",
            calm_answer
        ),
    ]
    if outcome == "alone":
        qa.append((
            f"How did {child.id} show bravery?",
            f"{child.id} was frightened by the barking and the height, but climbed carefully anyway and returned the bird alone. The bravery came from staying gentle and steady instead of rushing."
        ))
    else:
        qa.append((
            f"How did {child.id} show bravery?",
            f"{child.id} began the rescue but admitted help was needed, and {elder.id} steadied things from below. That is brave too, because wisdom can be part of courage."
        ))
    qa.append((
        "How did the story end?",
        f'The little bird was safe again, and the mother answered with a soft "{bird.flock_sound}" from above. That ending shows the yard had changed from barking alarm to quiet peace.'
    ))
    if dog_quiet:
        qa.append((
            "Why did the yard grow quiet before the ending?",
            f"The dog settled down before the climb, so the rescue could happen more safely. Once the barking stopped, the child could move with a clearer heart."
        ))
    else:
        qa.append((
            "Was the yard completely quiet before the climb?",
            f'No, the dog still made a low grumbling sound. Even so, {child.id} and {elder.id} found a careful way to finish the rescue.'
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kennel", "coo", "bird_nest", "bravery", "gentle_dog"}
    tags |= set(f["aid_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    yard: str
    bird: str
    nest: str
    aid: str
    calm: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    bark: int = 2
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        yard="farmyard",
        bird="dove",
        nest="branch",
        aid="crate",
        calm="biscuit",
        child_name="Mara",
        child_gender="girl",
        elder="grandmother",
        trait="bold",
        bark=1,
        seed=None,
    ),
    StoryParams(
        yard="millyard",
        bird="woodpigeon",
        nest="beam",
        aid="stool",
        calm="cluck",
        child_name="Ivo",
        child_gender="boy",
        elder="uncle",
        trait="steady",
        bark=2,
        seed=None,
    ),
    StoryParams(
        yard="orchard",
        bird="dove",
        nest="rafters",
        aid="ladder",
        calm="song",
        child_name="Nella",
        child_gender="girl",
        elder="grandfather",
        trait="careful",
        bark=2,
        seed=None,
    ),
    StoryParams(
        yard="farmyard",
        bird="woodpigeon",
        nest="rafters",
        aid="ladder",
        calm="biscuit",
        child_name="Bram",
        child_gender="boy",
        elder="aunt",
        trait="gentle",
        bark=3,
        seed=None,
    ),
]


ASP_RULES = r"""
reachable(N, A) :- nest(N), aid(A), need_height(N, H), reach(A, R), R >= H.
sensible(C) :- calm(C), sense(C, S), sense_min(M), S >= M.
valid(Y, B, N, A, C) :- yard(Y), bird(B), nest(N), aid(A), calm(C), reachable(N, A), sensible(C).

dog_quiet :- chosen_calm(C), chosen_bark(B), calm_power(C, P), P >= B.
solo_power(BR + ST + 1) :- chosen_trait(T), bravery(T, BR), chosen_aid(A), steadiness(A, ST), dog_quiet.
solo_power(BR + ST) :- chosen_trait(T), bravery(T, BR), chosen_aid(A), steadiness(A, ST), not dog_quiet.
target(H + B) :- chosen_nest(N), need_height(N, H), chosen_bark(B).
outcome(alone) :- solo_power(S), target(T), S >= T.
outcome(together) :- solo_power(S), target(T), S < T.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for yard_id in YARDS:
        lines.append(asp.fact("yard", yard_id))
    for bird_id in BIRDS:
        lines.append(asp.fact("bird", bird_id))
    for nest_id, nest in NESTS.items():
        lines.append(asp.fact("nest", nest_id))
        lines.append(asp.fact("need_height", nest_id, nest.height))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("reach", aid_id, aid.reach))
        lines.append(asp.fact("steadiness", aid_id, aid.steadiness))
    for calm_id, calm in CALM_CHOICES.items():
        lines.append(asp.fact("calm", calm_id))
        lines.append(asp.fact("sense", calm_id, calm.sense))
        lines.append(asp.fact("calm_power", calm_id, calm.calm_power))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("bravery", trait, bravery_of(trait)))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_nest", params.nest),
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_calm", params.calm),
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_bark", params.bark),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke test generate/emit ran.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a child, a kennel, a cooing bird, and a brave rescue."
    )
    ap.add_argument("--yard", choices=YARDS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--nest", choices=NESTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--calm", choices=CALM_CHOICES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--bark", type=int, choices=[1, 2, 3], help="how loudly the kennel dog starts out barking")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nest and args.aid:
        if not nest_reachable(AIDS[args.aid], NESTS[args.nest]):
            raise StoryError(explain_rejection(NESTS[args.nest], AIDS[args.aid]))
    if args.calm and CALM_CHOICES[args.calm].sense < SENSE_MIN:
        raise StoryError(explain_calm(args.calm))

    combos = [
        combo for combo in valid_combos()
        if (args.yard is None or combo[0] == args.yard)
        and (args.bird is None or combo[1] == args.bird)
        and (args.nest is None or combo[2] == args.nest)
        and (args.aid is None or combo[3] == args.aid)
        and (args.calm is None or combo[4] == args.calm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    yard_id, bird_id, nest_id, aid_id, calm_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    bark = args.bark if args.bark is not None else rng.choice([1, 2, 3])

    return StoryParams(
        yard=yard_id,
        bird=bird_id,
        nest=nest_id,
        aid=aid_id,
        calm=calm_id,
        child_name=name,
        child_gender=gender,
        elder=elder,
        trait=trait,
        bark=bark,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        yard = YARDS[params.yard]
        bird = BIRDS[params.bird]
        nest = NESTS[params.nest]
        aid = AIDS[params.aid]
        calm = CALM_CHOICES[params.calm]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err})") from None

    if not nest_reachable(aid, nest):
        raise StoryError(explain_rejection(nest, aid))
    if calm.sense < SENSE_MIN:
        raise StoryError(explain_calm(params.calm))

    world = tell(
        yard=yard,
        bird=bird,
        nest=nest,
        aid=aid,
        calm=CalmChoice(
            id=calm.id,
            label=calm.label,
            phrase=calm.phrase,
            sense=calm.sense,
            calm_power=calm.calm_power,
            text=_render_calm_text(calm, Entity(id=params.child_name, type=params.child_gender)),
            qa_text=calm.qa_text,
            tags=set(calm.tags),
        ),
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
        trait=params.trait,
        bark=params.bark,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (yard, bird, nest, aid, calm) combos:\n")
        for yard, bird, nest, aid, calm in combos:
            print(f"  {yard:9} {bird:10} {nest:8} {aid:7} {calm}")
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
                f"### {p.child_name}: {p.bird} at {p.yard} "
                f"({p.nest}, {p.aid}, {p.calm}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
