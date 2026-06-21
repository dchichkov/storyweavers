#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py
=========================================================================================

A standalone story world for a gentle animal tale about an overgrown fringe, one
careful snip, and the transformation that comes from learning to listen.

The seed asked for the words "snip" and "subsidiary", plus the narrative
features Lesson Learned and Transformation in an Animal Story style. This world
models a young animal whose shaggy coat blocks clear sight. A wiser grown-up
predicts trouble, the child either listens or rushes ahead, and a small trim
changes both how the child looks and how the child behaves.

Run it
------
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py --animal lamb --challenge bramble_path
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py --animal tortoise
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/snip_subsidiary_lesson_learned_transformation_animal_story.py --verify
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
LISTENING_TRAITS = {"patient", "thoughtful", "careful"}


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
        female = {"girl", "mother", "aunt"}
        male = {"boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
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
class Animal:
    id: str
    species: str
    coat_label: str
    coat_phrase: str
    trim_tool: str
    home: str
    movement: str
    sound: str
    tags: set[str] = field(default_factory=set)
    trimmable: bool = True
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
class Challenge:
    id: str
    label: str
    place: str
    risk: bool
    mishap: str
    rescue: str
    safe_after: str
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


def _r_mishap(world: World) -> list[str]:
    hero = world.get("hero")
    challenge = world.facts["challenge_cfg"]
    if not world.facts.get("hero_dashing"):
        return []
    if hero.meters["vision_blocked"] < THRESHOLD:
        return []
    if not challenge.risk:
        return []
    sig = ("mishap", challenge.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["mishap"] += 1
    hero.memes["fear"] += 1
    if challenge.id == "bramble_path":
        hero.meters["snagged"] += 1
    elif challenge.id == "brook_stones":
        hero.meters["splashed"] += 1
    elif challenge.id == "root_tunnel":
        hero.meters["bumped"] += 1
    return ["__mishap__"]


CAUSAL_RULES = [
    Rule(name="mishap", tag="physical", apply=_r_mishap),
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


def valid_combo(animal: Animal, challenge: Challenge) -> bool:
    return animal.trimmable and challenge.risk


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for challenge_id, challenge in CHALLENGES.items():
            if valid_combo(animal, challenge):
                combos.append((animal_id, challenge_id))
    return combos


def would_listen(trait: str) -> bool:
    return trait in LISTENING_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "averted" if would_listen(params.trait) else "mishap"


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sim.facts["hero_dashing"] = True
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "mishap": hero.meters["mishap"] >= THRESHOLD,
        "snagged": hero.meters["snagged"] >= THRESHOLD,
        "splashed": hero.meters["splashed"] >= THRESHOLD,
        "bumped": hero.meters["bumped"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, animal: Animal) -> None:
    hero.meters["vision_blocked"] = 1.0
    hero.memes["play"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"In the green country around {animal.home}, {hero.id} was a little {animal.species} "
        f"who loved to {animal.movement}. {hero.pronoun('possessive').capitalize()} "
        f"{animal.coat_phrase} often swung low enough to tickle {hero.pronoun('possessive')} nose."
    )
    world.say(
        f"When the breeze stirred, that soft {animal.coat_label} slid over {hero.pronoun('possessive')} eyes, "
        f"but {hero.id} only gave a proud little {animal.sound} and kept on hurrying."
    )


def setting_beat(world: World, challenge: Challenge) -> None:
    world.say(
        f"Near the main lane there was a subsidiary path that led toward {challenge.place}. "
        f"It looked smaller and twistier than the safe broad way, and that made it seem exciting."
    )


def warning(world: World, elder: Entity, hero: Entity, animal: Animal, challenge: Challenge) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_mishap"] = pred
    hero.memes["stubborn"] += 1
    if challenge.id == "bramble_path":
        reason = "the thorny branches would catch that hanging fringe"
    elif challenge.id == "brook_stones":
        reason = "the wet stones would be hard to see clearly"
    else:
        reason = "the low roots would look nearer than they really were"
    world.say(
        f'{elder.id}, {hero.id}\'s {elder.label_word}, watched {hero.pronoun("object")} glance toward {challenge.label}. '
        f'"Wait a moment," {elder.pronoun()} said gently. "If you dash there with {animal.coat_label} over your eyes, '
        f'{reason}."'
    )
    world.say(
        f'"Let me trim just a little first. Then you can go in with a clear view and a calm head."'
    )


def hurry_off(world: World, hero: Entity, challenge: Challenge) -> None:
    world.facts["hero_dashing"] = True
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} twitched with impatience. Before anyone could say another word, "
        f"{hero.pronoun()} scampered toward {challenge.label}."
    )


def mishap_scene(world: World, hero: Entity, challenge: Challenge) -> None:
    propagate(world, narrate=False)
    if hero.meters["snagged"] >= THRESHOLD:
        world.say(
            f"One step later, the brambles tugged at the wool across {hero.pronoun('possessive')} face. "
            f"{hero.id} gave a startled squeak and stood stuck among the prickly stems."
        )
    elif hero.meters["splashed"] >= THRESHOLD:
        world.say(
            f"At the brook, {hero.id} guessed at the first stone, missed the next one, and landed with a splash. "
            f"Cold water slapped {hero.pronoun('possessive')} legs, and suddenly hurrying did not feel brave at all."
        )
    elif hero.meters["bumped"] >= THRESHOLD:
        world.say(
            f"In the root tunnel, the hanging fringe turned roots into blurry shadows. "
            f"{hero.id} bonked {hero.pronoun('possessive')} forehead, sat down with a tiny gasp, and blinked hard."
        )


def rescue(world: World, elder: Entity, hero: Entity, challenge: Challenge) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{elder.id} came quickly and {challenge.rescue}. {elder.pronoun().capitalize()} did not scold. "
        f"{elder.pronoun().capitalize()} only steadied {hero.pronoun('object')} until the frightened feeling slowed down."
    )


def trim_now(world: World, elder: Entity, hero: Entity, animal: Animal, challenge: Challenge, mishap_happened: bool) -> None:
    hero.meters["vision_blocked"] = 0.0
    hero.meters["trimmed"] = 1.0
    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["lesson"] += 1
    lead = "On the mossy bank, " if mishap_happened else "Right there by the path, "
    world.say(
        f"{lead}{elder.id} lifted {animal.trim_tool} and moved very carefully. There came one soft snip, "
        f"then another snip, and the heavy fringe fell away from {hero.id}'s eyes."
    )
    world.say(
        f"{hero.id} blinked. The world looked larger now: bright berries, shiny stones, and leaf-shadows all sat in their proper places."
    )
    world.say(
        f'"Oh," whispered {hero.id}. "I thought the extra fluff made me grand. It only kept me from seeing well."'
    )


def preemptive_trim_dialogue(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} looked again, this time with a slower breath. The warning felt true, and {hero.pronoun()} leaned close instead of bolting away."
    )
    world.say(
        f'"All right," {hero.pronoun()} said. "Just a little, please."'
    )


def lesson(world: World, elder: Entity, hero: Entity, challenge: Challenge) -> None:
    hero.memes["humility"] += 1
    world.say(
        f'{elder.id} touched {hero.pronoun("possessive")} shoulder. "A wise heart does not hurry past help," '
        f'{elder.pronoun()} said. "A small change can make room for good seeing and good choosing."'
    )
    world.say(
        f"{hero.id} nodded. This time the nod was small and serious, the kind that means a lesson has gone all the way in."
    )


def after_trim_adventure(world: World, hero: Entity, challenge: Challenge, animal: Animal, mishap_happened: bool) -> None:
    hero.meters["safe_crossing"] = 1.0
    world.say(
        f"Then {hero.id} tried again. {challenge.safe_after}"
    )
    if mishap_happened:
        world.say(
            f"Because {hero.pronoun()} could finally see well, the place that had frightened {hero.pronoun('object')} a moment before now felt manageable instead of mean."
        )
    else:
        world.say(
            f"The danger never had a chance to become a problem, because {hero.id} had paused long enough to accept help."
        )
    world.say(
        f"By sunset, {challenge.ending_image}"
    )


def ending_image(world: World, hero: Entity, challenge: Challenge, animal: Animal) -> None:
    world.say(
        f"From then on, when the wind pushed {animal.coat_label} toward {hero.pronoun('possessive')} eyes, "
        f"{hero.id} did not pretend not to notice. {hero.pronoun().capitalize()} remembered the little snip, "
        f"the true lesson behind it, and the way clear sight had changed everything."
    )


def tell(
    animal: Animal,
    challenge: Challenge,
    name: str = "Pip",
    gender: str = "boy",
    elder_kind: str = "mother",
    trait: str = "patient",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        traits=[trait],
        role="hero",
    ))
    elder = world.add(Entity(
        id="Fern",
        kind="character",
        type=elder_kind,
        label="the elder",
        role="elder",
    ))
    world.facts["challenge_cfg"] = challenge
    world.facts["animal_cfg"] = animal
    world.facts["hero_dashing"] = False

    introduce(world, hero, animal)
    setting_beat(world, challenge)

    world.para()
    warning(world, elder, hero, animal, challenge)

    listened = would_listen(trait)
    if listened:
        preemptive_trim_dialogue(world, hero, elder)
        world.para()
        trim_now(world, elder, hero, animal, challenge, mishap_happened=False)
        lesson(world, elder, hero, challenge)
        world.para()
        after_trim_adventure(world, hero, challenge, animal, mishap_happened=False)
    else:
        hurry_off(world, hero, challenge)
        world.para()
        mishap_scene(world, hero, challenge)
        rescue(world, elder, hero, challenge)
        trim_now(world, elder, hero, animal, challenge, mishap_happened=True)
        lesson(world, elder, hero, challenge)
        world.para()
        after_trim_adventure(world, hero, challenge, animal, mishap_happened=True)

    ending_image(world, hero, challenge, animal)

    world.facts.update(
        hero=hero,
        elder=elder,
        listened=listened,
        outcome="averted" if listened else "mishap",
        mishap=hero.meters["mishap"] >= THRESHOLD,
        challenge=challenge,
        animal=animal,
        transformed=hero.meters["trimmed"] >= THRESHOLD and hero.meters["safe_crossing"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "lamb": Animal(
        id="lamb",
        species="lamb",
        coat_label="wool fringe",
        coat_phrase="round wool fringe",
        trim_tool="small silver shears",
        home="Clover Hill",
        movement="skip between clover patches",
        sound="baa",
        tags={"wool", "shears", "farm"},
        trimmable=True,
    ),
    "pony": Animal(
        id="pony",
        species="pony",
        coat_label="long forelock",
        coat_phrase="silky forelock",
        trim_tool="short grooming scissors",
        home="the Willow Meadow stable",
        movement="trot in springy circles",
        sound="snort",
        tags={"mane", "scissors", "stable"},
        trimmable=True,
    ),
    "sheepdog": Animal(
        id="sheepdog",
        species="sheepdog pup",
        coat_label="shaggy bangs",
        coat_phrase="shaggy bangs",
        trim_tool="round-tipped scissors",
        home="the stone cottage by the pasture",
        movement="bound after fluttering leaves",
        sound="woof",
        tags={"fur", "scissors", "dog"},
        trimmable=True,
    ),
    "tortoise": Animal(
        id="tortoise",
        species="young tortoise",
        coat_label="none",
        coat_phrase="smooth bright shell",
        trim_tool="none",
        home="the warm garden wall",
        movement="plod patiently",
        sound="hmph",
        tags={"shell"},
        trimmable=False,
    ),
}

CHALLENGES = {
    "bramble_path": Challenge(
        id="bramble_path",
        label="the thorny bramble path",
        place="the berry hedge",
        risk=True,
        mishap="snagged",
        rescue="eased the thorns apart and freed the caught wool",
        safe_after="With the fringe gone, the thorns stayed where they belonged, far from those bright careful eyes.",
        ending_image="the little one was carrying home a leaf-basket of berries and even showing two younger animals where not to brush the thorns",
        tags={"brambles", "berries"},
    ),
    "brook_stones": Challenge(
        id="brook_stones",
        label="the stepping stones over the brook",
        place="the singing brook",
        risk=True,
        mishap="splashed",
        rescue="helped the little one back onto the bank and rubbed the cold water away with a soft cloth",
        safe_after="Now each stepping stone showed its dry top plainly, and the brook was crossed one neat hop at a time.",
        ending_image="the little one was trotting home with dry feet and calling out which stones were steady and which were slick",
        tags={"brook", "stones"},
    ),
    "root_tunnel": Challenge(
        id="root_tunnel",
        label="the willow-root tunnel",
        place="the old willow roots",
        risk=True,
        mishap="bumped",
        rescue="ducked into the tunnel, guided the little one out, and kissed the sore spot between the ears",
        safe_after="This time every root and curve showed itself properly, so the tunnel felt like a puzzle that had been solved instead of a trap.",
        ending_image="the little one was leading a neat line of playmates through the tunnel, slow enough for everyone to laugh and fit",
        tags={"roots", "tunnel"},
    ),
    "sun_patch": Challenge(
        id="sun_patch",
        label="the warm sunny patch",
        place="the dandelion field",
        risk=False,
        mishap="none",
        rescue="did nothing at all",
        safe_after="There was nothing risky there in the first place.",
        ending_image="the little one was napping in the sun",
        tags={"sun"},
    ),
}

GIRL_NAMES = ["Miri", "Poppy", "Tansy", "Nell", "Luma", "Hazel", "Daisy", "Bramble"]
BOY_NAMES = ["Pip", "Moss", "Toby", "Rune", "Ollie", "Nico", "Thistle", "Bram"]
TRAITS = ["patient", "thoughtful", "careful", "hasty", "proud", "restless"]


@dataclass
class StoryParams:
    animal: str
    challenge: str
    name: str
    gender: str
    elder_kind: str
    trait: str
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
    "shears": [
        (
            "What are shears?",
            "Shears are strong scissors used for cutting thick wool or fur. A grown-up uses them carefully so the animal stays safe and comfortable.",
        )
    ],
    "scissors": [
        (
            "What do scissors do?",
            "Scissors cut hair, paper, or cloth. They should be used carefully and usually with a grown-up helping.",
        )
    ],
    "wool": [
        (
            "What is wool?",
            "Wool is the soft curly coat that grows on sheep and lambs. It keeps them warm, but if it hangs too low it can get in their way.",
        )
    ],
    "mane": [
        (
            "What is a mane?",
            "A mane is the long hair that grows on a horse or pony's neck and forehead. If it falls over the eyes, it can make seeing harder.",
        )
    ],
    "fur": [
        (
            "Why can shaggy fur be a problem?",
            "Shaggy fur can be cozy, but if it drops over the eyes it can block clear sight. Then an animal may bump into things or choose the wrong step.",
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny bushes with prickly stems. They can catch fur or clothes if you push through too quickly.",
        )
    ],
    "brook": [
        (
            "Why are stepping stones slippery?",
            "Water can make stones smooth and slick. If you cannot see clearly where to place your feet, you may slip.",
        )
    ],
    "roots": [
        (
            "Why should you slow down in a root tunnel?",
            "Roots twist and cross the ground in uneven ways. Going slowly helps you see where to duck and where to step.",
        )
    ],
    "farm": [
        (
            "Why do grown-ups trim some animals' coats?",
            "A trim can help an animal see, stay cool, and move comfortably. The point is not to make the animal fancy but to help the animal feel well.",
        )
    ],
    "stable": [
        (
            "Why do ponies need grooming?",
            "Grooming keeps a pony clean and comfortable. It also helps a grown-up notice when hair is too long and bothering the pony.",
        )
    ],
    "dog": [
        (
            "Why might a sheepdog pup need its bangs trimmed?",
            "A sheepdog pup uses its eyes and nose while running and learning. If bangs cover the eyes, the pup may miss what is right in front of it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["shears", "scissors", "wool", "mane", "fur", "brambles", "brook", "roots", "farm", "stable", "dog"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    animal = world.facts["animal"]
    challenge = world.facts["challenge"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            f'Write a gentle animal story that includes the words "snip" and "subsidiary" and follows a young {animal.species} who pauses to accept help before rushing into trouble.',
            f"Tell a story about {hero.id}, a little {animal.species}, whose hair hangs over the eyes until a careful trim changes how {hero.pronoun()} sees the world.",
            f"Write a lesson-learned transformation story where a grown-up prevents danger at {challenge.label} by making one small snip at the right time.",
        ]
    return [
        f'Write a gentle animal story that includes the words "snip" and "subsidiary" and follows a young {animal.species} who learns from a small mishap.',
        f"Tell a story about {hero.id}, a little {animal.species}, who ignores a warning, gets into trouble at {challenge.label}, and then changes after a careful trim.",
        f"Write a lesson-learned transformation story where a childlike animal becomes wiser after one preventable mistake and one thoughtful snip.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    animal = world.facts["animal"]
    challenge = world.facts["challenge"]
    listened = world.facts["listened"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {animal.species}, and {elder.id}, {hero.pronoun('possessive')} {elder.label_word}. The story follows how one small problem with sight changed a whole day.",
        ),
        (
            f"What was wrong with {hero.id}'s {animal.coat_label}?",
            f"It hung over {hero.pronoun('possessive')} eyes and made clear seeing hard. That mattered because {challenge.label} needed careful looking, not rushing.",
        ),
        (
            f"Why did {elder.id} warn {hero.id} before {challenge.label}?",
            f"{elder.id} could see that the hanging hair would make the place harder to judge. The warning was about safety, because hidden thorns, slick stones, or low roots can surprise someone who cannot see properly.",
        ),
    ]
    if listened:
        qa.append(
            (
                f"Did {hero.id} listen right away?",
                f"Yes. {hero.id} slowed down, trusted {elder.id}, and agreed to a little trim before going on. Because of that choice, the danger never turned into an accident.",
            )
        )
    else:
        if challenge.id == "bramble_path":
            mishap = "the brambles caught the wool across the face"
        elif challenge.id == "brook_stones":
            mishap = "the wet stones were hard to judge and a splash followed"
        else:
            mishap = "the roots looked blurry and a bump came before the stop"
        qa.append(
            (
                f"What happened when {hero.id} rushed ahead?",
                f"{mishap}. The trouble came from hurrying while {animal.coat_label} still covered the eyes.",
            )
        )
        qa.append(
            (
                f"How did {elder.id} help after the mishap?",
                f"{elder.id} came quickly, calmed {hero.id}, and then gave a careful trim. The help fixed the immediate problem and also showed a kinder, safer way to act.",
            )
        )
    qa.append(
        (
            f"How did the trim transform {hero.id}?",
            f"After the snip, {hero.id} could see the path clearly and moved with more confidence. Inside, the change mattered too, because pride and hurry gave way to patience and better judgment.",
        )
    )
    qa.append(
        (
            "What lesson did the story teach?",
            f"It taught that accepting help can be wiser than rushing to prove something. A small change on the outside helped {hero.id} make a bigger change on the inside.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    animal = world.facts["animal"]
    challenge = world.facts["challenge"]
    tags = set(animal.tags) | set(challenge.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="lamb",
        challenge="bramble_path",
        name="Pip",
        gender="boy",
        elder_kind="mother",
        trait="hasty",
        seed=101,
    ),
    StoryParams(
        animal="pony",
        challenge="brook_stones",
        name="Miri",
        gender="girl",
        elder_kind="aunt",
        trait="patient",
        seed=102,
    ),
    StoryParams(
        animal="sheepdog",
        challenge="root_tunnel",
        name="Moss",
        gender="boy",
        elder_kind="father",
        trait="proud",
        seed=103,
    ),
    StoryParams(
        animal="lamb",
        challenge="brook_stones",
        name="Daisy",
        gender="girl",
        elder_kind="mother",
        trait="thoughtful",
        seed=104,
    ),
]


def explain_rejection(animal: Animal, challenge: Challenge) -> str:
    if not animal.trimmable:
        return (
            f"(No story: a {animal.species} in this world does not have an overgrown fringe that can be improved with a careful snip. "
            f"The lesson depends on a visible trim and a transformation in how the hero moves.)"
        )
    if not challenge.risk:
        return (
            f"(No story: {challenge.label} is too harmless. This world needs a place where blocked sight could honestly cause trouble and make the warning meaningful.)"
        )
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
can_trim(A) :- animal(A), trimmable(A).
needs_clear_sight(C) :- challenge(C), risky(C).
valid(A, C) :- can_trim(A), needs_clear_sight(C).

listens :- chosen_trait(T), listening_trait(T).
outcome(averted) :- listens.
outcome(mishap) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        if animal.trimmable:
            lines.append(asp.fact("trimmable", animal_id))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        if challenge.risk:
            lines.append(asp.fact("risky", challenge_id))
    for trait in sorted(LISTENING_TRAITS):
        lines.append(asp.fact("listening_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: one careful snip, one learned lesson, and a gentle transformation."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-kind", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (animal, challenge) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.challenge:
        animal = ANIMALS[args.animal]
        challenge = CHALLENGES[args.challenge]
        if not valid_combo(animal, challenge):
            raise StoryError(explain_rejection(animal, challenge))
    if args.animal and not ANIMALS[args.animal].trimmable:
        challenge = CHALLENGES[args.challenge] if args.challenge else CHALLENGES[next(iter(CHALLENGES))]
        raise StoryError(explain_rejection(ANIMALS[args.animal], challenge))
    if args.challenge and not CHALLENGES[args.challenge].risk:
        animal = ANIMALS[args.animal] if args.animal else ANIMALS[next(a for a in ANIMALS if ANIMALS[a].trimmable)]
        raise StoryError(explain_rejection(animal, CHALLENGES[args.challenge]))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.challenge is None or combo[1] == args.challenge)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, challenge_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_kind = args.elder_kind or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        animal=animal_id,
        challenge=challenge_id,
        name=name,
        gender=gender,
        elder_kind=elder_kind,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    animal = ANIMALS[params.animal]
    challenge = CHALLENGES[params.challenge]
    if not valid_combo(animal, challenge):
        raise StoryError(explain_rejection(animal, challenge))

    world = tell(
        animal=animal,
        challenge=challenge,
        name=params.name,
        gender=params.gender,
        elder_kind=params.elder_kind,
        trait=params.trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, challenge) combos:\n")
        for animal, challenge in combos:
            print(f"  {animal:10} {challenge}")
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
            header = f"### {p.name}: {p.animal} at {p.challenge} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
