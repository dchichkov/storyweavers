#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py
=================================================================================

A standalone story world for a bedtime tale about two friends, a mysterious
night sound, some fizzy kefir, and the moment a silly piece of malarkey turns
into a lesson about honesty and friendship.

Premise
-------
Two children are settling down for the night when they hear a tiny tapping
sound nearby. One child, trying to seem exciting and brave, blurts out a scary
explanation. The other child gets frightened. The real cause is ordinary and
physical: a chilled bottle or jar of kefir softly fizzing and tapping against a
resonant surface. The turn comes when the children choose whether to keep
feeding the fear or to face it together, kindly and honestly. The ending image
shows what changed: the scary sound is understood, the friendship is steadied,
and bedtime becomes peaceful again.

Run it
------
    python storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py
    python storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py --room window_nook --source bottle --perch saucer
    python storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py --perch quilt
    python storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py --all --qa
    python storyworlds/worlds/gpt-5.4/kefir_malarkey_twist_moral_value_friendship_bedtime.py --verify
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    place: str
    bed_line: str
    nearby: str
    hush: str
    glow: str
    echo: int
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
class KefirSource:
    id: str
    phrase: str
    vessel: str
    fizz_word: str
    hard: bool
    fizzy: bool
    noise: int
    chill_line: str
    reveal_line: str
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
class Perch:
    id: str
    phrase: str
    resonant: bool
    echo: int
    tap_word: str
    reveal_tail: str
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
class Scare:
    id: str
    whisper: str
    correction: str
    scare: int
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
class Response:
    id: str
    sense: int
    power: int
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"teller", "friend"}]

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


def _r_sound_spreads(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    perch = world.get("perch")
    if source.meters["fizzing"] < THRESHOLD or perch.meters["ready"] < THRESHOLD:
        return out
    sig = ("sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    noise = source.meters["fizzing"] + perch.meters["echo"]
    world.get("room").meters["sound"] += noise
    out.append("__sound__")
    return out


def _r_fear_grows(world: World) -> list[str]:
    out: list[str] = []
    teller = world.get("teller")
    friend = world.get("friend")
    room = world.get("room")
    if room.meters["sound"] < THRESHOLD or teller.memes["pretend_scary"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["fear"] += 2
    teller.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_friendship_steadies(world: World) -> list[str]:
    out: list[str] = []
    teller = world.get("teller")
    friend = world.get("friend")
    if teller.memes["honesty"] < THRESHOLD or friend.memes["comforted"] < THRESHOLD:
        return out
    sig = ("steady",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    teller.memes["trust"] += 1
    friend.memes["trust"] += 1
    teller.memes["fear"] = max(0.0, teller.memes["fear"] - 1)
    friend.memes["fear"] = max(0.0, friend.memes["fear"] - 1)
    out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule(name="sound_spreads", tag="physical", apply=_r_sound_spreads),
    Rule(name="fear_grows", tag="emotional", apply=_r_fear_grows),
    Rule(name="friendship_steadies", tag="social", apply=_r_friendship_steadies),
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


def valid_combo(source: KefirSource, perch: Perch) -> bool:
    return source.fizzy and source.hard and perch.resonant


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fright_level(source: KefirSource, perch: Perch, scare: Scare, room: Room) -> int:
    return source.noise + perch.echo + scare.scare + room.echo


def children_can_solve(response: Response, source: KefirSource, perch: Perch,
                       scare: Scare, room: Room, bond: int, honesty: int) -> bool:
    return response.power + (1 if bond >= 7 else 0) + (1 if honesty >= 7 else 0) >= fright_level(source, perch, scare, room)


def explain_rejection(source: KefirSource, perch: Perch) -> str:
    if not source.fizzy:
        return (f"(No story: {source.phrase} would not fizz at bedtime, so there is no honest "
                f"mystery sound to start the tale.)")
    if not source.hard:
        return (f"(No story: {source.phrase} is too soft-sided to make the neat little tapping "
                f"that this bedtime story needs.)")
    if not perch.resonant:
        return (f"(No story: {perch.phrase} would muffle the sound, so the children would not "
                f"hear a clear bedtime tapping. Pick a resonant perch like a saucer or shelf.)")
    return "(No story: this combination does not make a plausible bedtime sound.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(sr.id for sr in sensible_responses()))
    return (f"(Refusing response '{rid}': it scores too low on common sense "
            f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)")


def predict_sound(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["fizzing"] += 1
    sim.get("perch").meters["ready"] += 1
    sim.get("perch").meters["echo"] = float(sim.facts["perch_cfg"].echo)
    propagate(sim, narrate=False)
    return {
        "heard": sim.get("room").meters["sound"] >= THRESHOLD,
        "sound": sim.get("room").meters["sound"],
    }


def introduce(world: World, teller: Entity, friend: Entity, room: Room) -> None:
    teller.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"It was bedtime in {room.place}. {room.bed_line} {room.glow}"
    )
    world.say(
        f"{teller.id} and {friend.id} were having a sleepover, tucked under one quilt and "
        f"still warm from whispering about stars and puddle-silver moonlight."
    )


def settle(world: World, room: Room, adult: Entity) -> None:
    world.say(
        f"Nearby, {room.nearby}. The whole house felt quiet except for {room.hush}."
    )
    world.say(
        f"{adult.label_word.capitalize()} had already kissed the tops of their heads and said it was time to rest."
    )


def first_sound(world: World, teller: Entity, friend: Entity, source: KefirSource,
                perch: Perch) -> None:
    pred = predict_sound(world)
    world.facts["predicted_sound"] = pred["sound"]
    world.get("source").meters["fizzing"] += 1
    world.get("perch").meters["ready"] += 1
    world.get("perch").meters["echo"] = float(perch.echo)
    propagate(world, narrate=False)
    world.say(
        f"Then, from nearby, came a tiny sound: {perch.tap_word}. Then again: {perch.tap_word}."
    )
    world.say(
        f"{friend.id} lifted {friend.pronoun('possessive')} head from the pillow. "
        f'"Did you hear that?" {friend.pronoun()} whispered.'
    )
    teller.memes["attention"] += 1


def spin_malarkey(world: World, teller: Entity, friend: Entity, scare: Scare) -> None:
    teller.memes["pretend_scary"] += 1
    world.say(
        f'{teller.id} tried to sound bold and mysterious. "{scare.whisper}" '
        f"{teller.pronoun()} murmured."
    )
    world.say(
        f"For one moment, the words felt exciting. Then they made the dark seem bigger than it really was."
    )
    propagate(world, narrate=False)


def fear_beat(world: World, teller: Entity, friend: Entity) -> None:
    if friend.memes["fear"] >= THRESHOLD:
        world.say(
            f"{friend.id} scooted closer and caught hold of the quilt with both hands. "
            f"{friend.pronoun().capitalize()} wished the sound would stop."
        )
    if teller.memes["fear"] >= THRESHOLD:
        world.say(
            f"Even {teller.id}, who had started the scary talk, felt a small cold flutter in "
            f"{teller.pronoun('possessive')} tummy."
        )


def choose_response(world: World, teller: Entity, friend: Entity, response: Response,
                    lamp_name: str) -> None:
    if response.id == "peek_together":
        teller.memes["courage"] += 1
        friend.memes["comforted"] += 1
        world.say(
            f'"Let\'s not guess in the dark," {friend.id} said softly. "We can look together with the {lamp_name}."'
        )
        world.say(
            f"They slid their feet to the rug and held hands before either one took a step."
        )
    else:
        teller.memes["courage"] += 1
        friend.memes["comforted"] += 1
        world.say(
            f'"Let\'s ask {world.get("adult").label_word}," {friend.id} said. "Things are less scary when we tell the truth about them."'
        )
        world.say(
            f"{teller.id} nodded. It felt better to move toward help than to sit still with a story growing too large."
        )


def confess(world: World, teller: Entity, scare: Scare, adult_needed: bool) -> None:
    teller.memes["honesty"] += 1
    if adult_needed:
        world.say(
            f'Before anyone opened the door, {teller.id} whispered, "I think that was malarkey. '
            f'{scare.correction}"'
        )
    else:
        world.say(
            f'{teller.id} squeezed {world.get("friend").id}\'s hand and whispered, "That monster talk was malarkey. '
            f'{scare.correction}"'
        )
    propagate(world, narrate=False)


def child_reveal(world: World, teller: Entity, friend: Entity, source: KefirSource,
                 perch: Perch, lamp_name: str) -> None:
    world.say(
        f"By the little pool of {lamp_name} light, they saw the answer at once: {source.reveal_line}, "
        f"{perch.reveal_tail}."
    )
    world.say(
        f"It was only kefir, gently fizzing and giving the smallest taps as the bubbles nudged the {source.vessel}."
    )
    teller.memes["relief"] += 1
    friend.memes["relief"] += 1
    teller.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0


def adult_reveal(world: World, adult: Entity, teller: Entity, friend: Entity,
                 source: KefirSource, perch: Perch, lamp_name: str) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came in with the {lamp_name} and listened for one quiet breath."
    )
    world.say(
        f'Then {adult.pronoun()} smiled. "Oh, that?" {adult.pronoun()} said. "That is only {source.reveal_line}, '
        f"{perch.reveal_tail}. Nothing spooky at all."
    )
    world.say(
        f"The kefir was fizzy, and every soft bubble made a tiny tap against the {source.vessel}."
    )
    teller.memes["relief"] += 1
    friend.memes["relief"] += 1
    teller.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0


def lesson(world: World, adult: Entity, teller: Entity, friend: Entity) -> None:
    teller.memes["love"] += 1
    friend.memes["love"] += 1
    teller.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{adult.label_word.capitalize()} tucked the quilt around them again. "Scary guesses can grow fast in the dark," '
        f'{adult.pronoun()} said, "but honesty and kindness make a better lamp."'
    )
    world.say(
        f"{teller.id} turned to {friend.id}. \"Next time, I will not fill bedtime with malarkey,\" "
        f"{teller.pronoun()} said."
    )
    world.say(
        f'"Next time, we will be brave together," {friend.id} answered, and that made them both smile.'
    )


def ending_image(world: World, teller: Entity, friend: Entity, source: KefirSource) -> None:
    teller.memes["sleepy"] += 1
    friend.memes["sleepy"] += 1
    world.say(
        f"Soon the room was only a room again, not a place for shadows to pretend. "
        f"The little kefir sound did not frighten them anymore."
    )
    world.say(
        f"Hand in hand above the quilt, {teller.id} and {friend.id} listened until the house grew soft and still, "
        f"and friendship was the last warm thing awake before sleep."
    )
@dataclass
class StoryParams:
    room: str
    source: str
    perch: str
    scare: str
    response: str
    teller_name: str
    teller_gender: str
    friend_name: str
    friend_gender: str
    adult: str
    lamp_name: str
    bond: int = 7
    honesty: int = 7
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
    "kefir": [
        (
            "What is kefir?",
            "Kefir is a tangy milk drink that can have tiny bubbles in it. Those bubbles can make soft fizzy sounds."
        )
    ],
    "fizzy": [
        (
            "Why can fizzy drinks make little noises?",
            "Tiny bubbles move and pop inside them. If the drink is in a hard bottle or jar, those bubbles can make light tapping sounds."
        )
    ],
    "truth": [
        (
            "Why is it better to tell the truth when something feels scary?",
            "The truth helps people solve the real problem. Silly guesses can make fear bigger than it needs to be."
        )
    ],
    "adult": [
        (
            "Why is it okay to ask a grown-up for help at night?",
            "Grown-ups can help check what is real and keep children calm. Asking for help is brave, not babyish."
        )
    ],
    "friendship": [
        (
            "How can friendship help when you feel afraid?",
            "A kind friend can hold your hand, speak gently, and help you think clearly. Feeling together often makes a scary moment feel smaller."
        )
    ],
}
KNOWLEDGE_ORDER = ["kefir", "fizzy", "truth", "adult", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teller = f["teller"]
    friend = f["friend"]
    room = f["room"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "kefir" and "malarkey".',
        f"Tell a gentle twist story where {teller.id} and {friend.id} hear a mysterious sound at bedtime in {room.place}, but the sound has an ordinary cause.",
        "Write a soft bedtime tale about friendship, honesty, and a scary guess that turns out not to be true.",
    ]


def pair_noun(teller: Entity, friend: Entity) -> str:
    if teller.type == "girl" and friend.type == "girl":
        return "two friends"
    if teller.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    teller = f["teller"]
    friend = f["friend"]
    adult = f["adult"]
    room = f["room"]
    source = f["source"]
    perch = f["perch"]
    scare = f["scare"]
    response = f["response"]
    lamp_name = f["lamp_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(teller, friend)}, {teller.id} and {friend.id}, spending bedtime together. A kind {adult.label_word} also helps them when the mystery is solved."
        ),
        (
            "What scary thing happened at bedtime?",
            f"They heard a tiny tapping sound in the room after the house had grown quiet. Because it was dark and unexpected, the sound felt bigger and stranger than it really was."
        ),
        (
            f"Why did {friend.id} get more scared?",
            f"{teller.id} made up a scary idea instead of saying {scare.correction.lower()} {friend.id} listened to the story in the dark, so fear grew before the truth arrived."
        ),
    ]
    if f["outcome"] == "children_solve":
        qa.append(
            (
                "How did the children solve the mystery?",
                f"They chose to {response.text} and stay together. In the {lamp_name} light, they saw that the sound came from kefir fizzing softly and tapping on {perch.phrase}."
            )
        )
    else:
        qa.append(
            (
                f"Why did they ask {adult.label_word} for help?",
                f"The sound and the scary guess felt too large to sort out alone. Telling the truth brought calm help, and {adult.label_word} showed them that the noise was only kefir."
            )
        )
    qa.append(
        (
            "What was the twist?",
            f"The children first imagined something spooky, but the sound was ordinary all along. It was just {source.phrase} making tiny taps as bubbles nudged the {source.vessel}."
        )
    )
    qa.append(
        (
            "What did the children learn?",
            f"They learned that malarkey can make fear grow in the dark. They also learned that friendship and honesty help people face small mysteries more gently."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"kefir", "fizzy", "truth", "friendship"}
    if f["outcome"] == "adult_reveal" or f["response"].id == "ask_grownup":
        tags.add("adult")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="window_nook",
        source="bottle",
        perch="saucer",
        scare="cupboard_sprite",
        response="peek_together",
        teller_name="Nora",
        teller_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        adult="grandmother",
        lamp_name="star lamp",
        bond=8,
        honesty=8,
    ),
    StoryParams(
        room="guest_room",
        source="jar",
        perch="tin_tray",
        scare="shadow_slurper",
        response="ask_grownup",
        teller_name="Ella",
        teller_gender="girl",
        friend_name="Ruby",
        friend_gender="girl",
        adult="grandfather",
        lamp_name="night-lamp",
        bond=6,
        honesty=5,
    ),
    StoryParams(
        room="cabin_loft",
        source="bottle",
        perch="wood_shelf",
        scare="moon_mouse",
        response="peek_together",
        teller_name="Theo",
        teller_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        adult="father",
        lamp_name="little lantern",
        bond=7,
        honesty=7,
    ),
    StoryParams(
        room="guest_room",
        source="jar",
        perch="saucer",
        scare="cupboard_sprite",
        response="ask_grownup",
        teller_name="Mia",
        teller_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        adult="mother",
        lamp_name="star lamp",
        bond=9,
        honesty=9,
    ),
]


ASP_RULES = r"""
valid(Source, Perch) :- source(Source), perch(Perch), fizzy(Source), hard(Source), resonant(Perch).

fright(F) :- chosen_source(S), chosen_perch(P), chosen_scare(C), chosen_room(R),
             source_noise(S, SN), perch_echo(P, PE), scare_value(C, CV), room_echo(R, RE),
             F = SN + PE + CV + RE.

bonus_bond(1) :- bond(B), B >= 7.
bonus_bond(0) :- bond(B), B < 7.
bonus_honesty(1) :- honesty(H), H >= 7.
bonus_honesty(0) :- honesty(H), H < 7.

can_solve :- chosen_response(R), response_power(R, RP), fright(F),
             bonus_bond(BB), bonus_honesty(BH), RP + BB + BH >= F.

confessed :- honesty(H), H >= 7.
confessed :- bond(B), B >= 8.

outcome(children_solve) :- can_solve, chosen_response(peek_together).
outcome(adult_reveal) :- not outcome(children_solve).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("room_echo", rid, ROOMS[rid].echo))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if source.fizzy:
            lines.append(asp.fact("fizzy", sid))
        if source.hard:
            lines.append(asp.fact("hard", sid))
        lines.append(asp.fact("source_noise", sid, source.noise))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        if perch.resonant:
            lines.append(asp.fact("resonant", pid))
        lines.append(asp.fact("perch_echo", pid, perch.echo))
    for cid, scare in SCARES.items():
        lines.append(asp.fact("scare", cid))
        lines.append(asp.fact("scare_value", cid, scare.scare))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("response_power", rid, response.power))
        lines.append(asp.fact("response_sense", rid, response.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_room", params.room),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_scare", params.scare),
            asp.fact("chosen_response", params.response),
            asp.fact("bond", params.bond),
            asp.fact("honesty", params.honesty),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if params.room not in ROOMS or params.source not in SOURCES or params.perch not in PERCHES or params.scare not in SCARES:
        raise StoryError("(No story: one or more requested options are unknown.)")
    can_solve = children_can_solve(
        RESPONSES[params.response],
        SOURCES[params.source],
        PERCHES[params.perch],
        SCARES[params.scare],
        ROOMS[params.room],
        params.bond,
        params.honesty,
    )
    return "children_solve" if can_solve and params.response == "peek_together" else "adult_reveal"


def asp_verify() -> int:
    rc = 0
    python_set = set((s, p) for _, s, p in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid combos ({len(clingo_set)} source/perch pairs).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Failed to resolve params for seed {seed}.")
            break

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
            if py != cl:
                bad += 1
        except Exception as err:
            rc = 1
            print(f"Outcome check crashed for {params}: {err}")
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke generation failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: fizzy kefir, a bit of malarkey, and friendship in the dark."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--scare", choices=SCARES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--teller-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--teller-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--bond", type=int, choices=range(4, 11), default=None)
    ap.add_argument("--honesty", type=int, choices=range(4, 11), default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.perch:
        source = SOURCES[args.source]
        perch = PERCHES[args.perch]
        if not valid_combo(source, perch):
            raise StoryError(explain_rejection(source, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.source is None or combo[1] == args.source)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, source_id, perch_id = rng.choice(sorted(combos))
    scare_id = args.scare or rng.choice(sorted(SCARES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    adult = args.adult or rng.choice(ADULTS)
    teller_gender = args.teller_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    teller_name = args.teller_name or _pick_name(rng, teller_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=teller_name)
    lamp_name = rng.choice(LAMPS)
    bond = args.bond if args.bond is not None else rng.randint(4, 10)
    honesty = args.honesty if args.honesty is not None else rng.randint(4, 10)

    return StoryParams(
        room=room_id,
        source=source_id,
        perch=perch_id,
        scare=scare_id,
        response=response_id,
        teller_name=teller_name,
        teller_gender=teller_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
        lamp_name=lamp_name,
        bond=bond,
        honesty=honesty,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("room", ROOMS), ("source", SOURCES), ("perch", PERCHES), ("scare", SCARES), ("response", RESPONSES)]:
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(No story: unknown {key} '{value}'.)")
    if params.response in RESPONSES and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not valid_combo(SOURCES[params.source], PERCHES[params.perch]):
        raise StoryError(explain_rejection(SOURCES[params.source], PERCHES[params.perch]))

    world = tell(
        room=ROOMS[params.room],
        source=SOURCES[params.source],
        perch=PERCHES[params.perch],
        scare=SCARES[params.scare],
        response=RESPONSES[params.response],
        teller_name=params.teller_name,
        teller_gender=params.teller_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        lamp_name=params.lamp_name,
        bond=params.bond,
        honesty=params.honesty,
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
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (source, perch) pairs:\n")
        for source, perch in pairs:
            print(f"  {source:10} {perch}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.teller_name} & {p.friend_name}: {p.source} on {p.perch} "
                f"({p.room}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(room: Room, source: KefirSource, perch: Perch, scare: Scare, response: Response,
         teller_name: str = "Nora", teller_gender: str = "girl",
         friend_name: str = "Milo", friend_gender: str = "boy",
         adult_type: str = "grandmother", lamp_name: str = "night-lamp",
         bond: int = 7, honesty: int = 7) -> World:
    world = World()
    teller = world.add(Entity(id=teller_name, kind="character", type=teller_gender, role="teller"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="room", type="room", label=room.place))
    world.add(Entity(id="source", type="food", label="kefir"))
    world.add(Entity(id="perch", type="surface", label=perch.phrase))

    teller.memes["friendship"] = float(bond)
    friend.memes["friendship"] = float(bond)
    teller.memes["honesty_seed"] = float(honesty)
    teller.memes["trust"] = float(max(1, bond - 1))
    friend.memes["trust"] = float(bond)
    world.facts["room_cfg"] = room
    world.facts["source_cfg"] = source
    world.facts["perch_cfg"] = perch
    world.facts["scare_cfg"] = scare
    world.facts["response_cfg"] = response
    world.facts["lamp_name"] = lamp_name
    world.facts["bond"] = bond
    world.facts["honesty"] = honesty

    introduce(world, teller, friend, room)
    settle(world, room, adult)

    world.para()
    first_sound(world, teller, friend, source, perch)
    spin_malarkey(world, teller, friend, scare)
    fear_beat(world, teller, friend)

    world.para()
    choose_response(world, teller, friend, response, lamp_name)
    can_solve = children_can_solve(response, source, perch, scare, room, bond, honesty)
    confessed = honesty >= 7 or bond >= 8
    if confessed:
        confess(world, teller, scare, adult_needed=not can_solve)

    if can_solve and response.id == "peek_together":
        child_reveal(world, teller, friend, source, perch, lamp_name)
        outcome = "children_solve"
    else:
        if not confessed:
            confess(world, teller, scare, adult_needed=True)
        adult_reveal(world, adult, teller, friend, source, perch, lamp_name)
        outcome = "adult_reveal"

    world.para()
    lesson(world, adult, teller, friend)
    ending_image(world, teller, friend, source)
    world.facts.update(
        teller=teller,
        friend=friend,
        adult=adult,
        room=room,
        source=source,
        perch=perch,
        scare=scare,
        response=response,
        outcome=outcome,
        confessed=confessed,
        fright=fright_level(source, perch, scare, room),
        can_solve=can_solve,
    )
    return world


ROOMS = {
    "window_nook": Room(
        id="window_nook",
        place="a small room under the eaves",
        bed_line="Two little beds stood close together under the slanted ceiling",
        nearby="a narrow windowsill held tomorrow's breakfast things",
        hush="the slow settling of old wood",
        glow="A pearly moonbeam lay on the floorboards like folded ribbon.",
        echo=1,
        tags={"bedroom", "window"},
    ),
    "guest_room": Room(
        id="guest_room",
        place="the guest room at grandma's house",
        bed_line="A patchwork quilt covered the bed where two pillows waited side by side",
        nearby="a tray near the dresser held a bedtime snack",
        hush="the clock breathing from the hall",
        glow="The curtains made the moonlight soft as milk.",
        echo=1,
        tags={"bedroom", "grandma"},
    ),
    "cabin_loft": Room(
        id="cabin_loft",
        place="a tiny cabin loft",
        bed_line="Blankets were tucked into a nest under the rafters",
        nearby="a little shelf near the ladder kept a few cups and jars",
        hush="the wind brushing the shingles",
        glow="A star-shaped lamp left a faint gold circle by the bed.",
        echo=2,
        tags={"cabin", "bedroom"},
    ),
}

SOURCES = {
    "bottle": KefirSource(
        id="bottle",
        phrase="a glass bottle of kefir",
        vessel="glass bottle",
        fizz_word="plink",
        hard=True,
        fizzy=True,
        noise=2,
        chill_line="It had been set out to warm a little before breakfast.",
        reveal_line="a glass bottle of kefir on the windowsill",
        tags={"kefir", "fizzy"},
    ),
    "jar": KefirSource(
        id="jar",
        phrase="a little jar of kefir",
        vessel="jar",
        fizz_word="tik",
        hard=True,
        fizzy=True,
        noise=1,
        chill_line="Grandma had poured it earlier and forgotten to carry it away.",
        reveal_line="a little jar of kefir near the bed tray",
        tags={"kefir", "fizzy"},
    ),
    "skin_pouch": KefirSource(
        id="skin_pouch",
        phrase="a soft travel pouch of kefir",
        vessel="soft pouch",
        fizz_word="ff",
        hard=False,
        fizzy=True,
        noise=0,
        chill_line="It was tucked into a lunch wrap.",
        reveal_line="a soft pouch of kefir",
        tags={"kefir"},
    ),
    "flat_cup": KefirSource(
        id="flat_cup",
        phrase="a quiet cup of kefir",
        vessel="cup",
        fizz_word="none",
        hard=True,
        fizzy=False,
        noise=0,
        chill_line="It had gone flat long ago.",
        reveal_line="a quiet cup of kefir",
        tags={"kefir"},
    ),
}

PERCHES = {
    "saucer": Perch(
        id="saucer",
        phrase="a saucer",
        resonant=True,
        echo=1,
        tap_word="tik-tik",
        reveal_tail="resting on a saucer that answered each tiny tap",
        tags={"dish"},
    ),
    "tin_tray": Perch(
        id="tin_tray",
        phrase="a tin tray",
        resonant=True,
        echo=2,
        tap_word="ping... ping",
        reveal_tail="standing on a tin tray that made the sound brighter",
        tags={"metal"},
    ),
    "wood_shelf": Perch(
        id="wood_shelf",
        phrase="a wooden shelf",
        resonant=True,
        echo=1,
        tap_word="tok... tok",
        reveal_tail="standing on a wooden shelf that carried the taps through the room",
        tags={"wood"},
    ),
    "quilt": Perch(
        id="quilt",
        phrase="a folded quilt",
        resonant=False,
        echo=0,
        tap_word="mff",
        reveal_tail="hidden in the folds of a quilt",
        tags={"soft"},
    ),
}

SCARES = {
    "moon_mouse": Scare(
        id="moon_mouse",
        whisper="Maybe a moon-mouse is knocking with a silver spoon.",
        correction="I was only trying to sound interesting.",
        scare=1,
        tags={"pretend"},
    ),
    "cupboard_sprite": Scare(
        id="cupboard_sprite",
        whisper="Maybe it is the cupboard sprite who counts sleepy toes.",
        correction="I made up a sprite because the sound surprised me too.",
        scare=2,
        tags={"pretend"},
    ),
    "shadow_slurper": Scare(
        id="shadow_slurper",
        whisper="Maybe it is a shadow slurper looking for midnight socks.",
        correction="I said something silly instead of something true.",
        scare=3,
        tags={"pretend"},
    ),
}

RESPONSES = {
    "peek_together": Response(
        id="peek_together",
        sense=2,
        power=3,
        text="look together with the lamp",
        qa_text="They looked together with the lamp and found the real source of the sound.",
        tags={"look", "truth"},
    ),
    "ask_grownup": Response(
        id="ask_grownup",
        sense=3,
        power=5,
        text="ask a grown-up for help",
        qa_text="They told the grown-up the truth and asked for help.",
        tags={"adult", "truth"},
    ),
    "hide_under_quilt": Response(
        id="hide_under_quilt",
        sense=1,
        power=1,
        text="hide and keep guessing",
        qa_text="They only hid under the quilt and kept guessing.",
        tags={"hide"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mia", "Ella", "Sana", "Ivy", "Ruby", "Clara"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Owen", "Finn", "Leo", "Jude", "Sam"]
LAMPS = ["night-lamp", "star lamp", "little lantern"]
TRAITS = ["truthful", "playful", "imaginative", "kind"]
ADULTS = ["mother", "father", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id in ROOMS:
        for source_id, source in SOURCES.items():
            for perch_id, perch in PERCHES.items():
                if valid_combo(source, perch):
                    combos.append((room_id, source_id, perch_id))
    return combos

if __name__ == "__main__":
    main()
