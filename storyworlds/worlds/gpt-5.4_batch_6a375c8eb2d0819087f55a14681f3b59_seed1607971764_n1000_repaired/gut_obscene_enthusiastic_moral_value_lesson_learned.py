#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py
=================================================================================

A standalone story world about a small public mystery: two children arrive to
help at a cheerful neighborhood place, only to find an obscene scribble where a
kind sign should be. One child follows clues, trusts a gut feeling, pieces
together a flashback, and solves the mystery gently. The ending teaches a clear
lesson: do not repeat rude words you do not understand, and shared places should
be cared for with kind hands.

Run it
------
    python storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py --place bakery --surface chalkboard --medium chalk
    python storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py --cleaner dry_tissue
    python storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py --all --qa
    python storyworlds/worlds/gpt-5.4/gut_obscene_enthusiastic_moral_value_lesson_learned.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    keeper_word: str
    opening_image: str
    closing_image: str
    surfaces: set[str] = field(default_factory=set)
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
class Surface:
    id: str
    label: str
    phrase: str
    place_text: str
    washable: bool = True
    accepts: set[str] = field(default_factory=set)
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
class Medium:
    id: str
    label: str
    phrase: str
    clue: str
    stain: int
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
class Source:
    id: str
    label: str
    flashback: str
    innocent_reason: str
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
class Cleaner:
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


def _r_public_worry(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("surface")
    if sign.meters["obscene_mark"] < THRESHOLD:
        return out
    sig = ("public_worry", sign.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"sleuth", "friend", "keeper"}:
            ent.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("surface")
    if sign.meters["clean"] < THRESHOLD:
        return out
    sig = ("relief", sign.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"sleuth", "friend", "keeper", "culprit"}:
            ent.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="public_worry", tag="emotional", apply=_r_public_worry),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def can_mark(surface: Surface, medium: Medium) -> bool:
    return medium.id in surface.accepts and surface.washable


def sensible_cleaners() -> list[Cleaner]:
    return [c for c in CLEANERS.values() if c.sense >= SENSE_MIN]


def mystery_solved(cleaner: Cleaner, medium: Medium) -> bool:
    return cleaner.power >= medium.stain


def explain_surface_rejection(surface: Surface, medium: Medium) -> str:
    if not surface.washable:
        return (
            f"(No story: {surface.phrase} is not a washable shared surface here, so the "
            f"children cannot honestly clean up a {medium.label} mystery there.)"
        )
    return (
        f"(No story: {medium.label} would not make a believable mark on {surface.phrase}. "
        f"Choose a surface that can actually hold that kind of scribble.)"
    )


def explain_cleaner_rejection(cleaner_id: str) -> str:
    cleaner = CLEANERS[cleaner_id]
    better = " / ".join(sorted(c.id for c in sensible_cleaners()))
    return (
        f"(Refusing cleaner '{cleaner_id}': it scores too low on common sense "
        f"(sense={cleaner.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def inspect_mark(world: World, sleuth: Entity, friend: Entity,
                 surface_cfg: Surface, medium: Medium) -> None:
    sign = world.get("surface")
    sign.meters["obscene_mark"] += 1
    sleuth.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Early that morning, {sleuth.id} and {friend.id} hurried into {world.place.label}, "
        f"too enthusiastic to walk slowly. They had come to help before everyone else, and "
        f"{world.place.opening_image}"
    )
    world.say(
        f"Then they stopped. Across {surface_cfg.phrase}, where a kind morning message should "
        f"have been, someone had scrawled an obscene word in {medium.phrase}."
    )
    world.say(
        f"The room went quiet in the way mysteries do. {friend.id} whispered, "
        f'"Who would do that?"'
    )


def clue_beat(world: World, sleuth: Entity, medium: Medium) -> None:
    sleuth.memes["hunch"] += 1
    world.say(
        f"{sleuth.id} leaned close and saw a clue: {medium.clue}. A small gut feeling stirred. "
        f"Something about the mark did not feel mean so much as borrowed."
    )


def flashback_beat(world: World, sleuth: Entity, culprit: Entity, source: Source) -> None:
    culprit.memes["unease"] += 1
    sleuth.memes["memory"] += 1
    world.say(
        f"Then a flashback flickered through {sleuth.id}'s mind. {source.flashback}"
    )
    world.say(
        f"{sleuth.id} looked at {culprit.id}'s hands, then at the sign again, and the pieces "
        f"began to fit."
    )


def gentle_question(world: World, sleuth: Entity, culprit: Entity,
                    source: Source, medium: Medium) -> None:
    culprit.memes["shame"] += 1
    world.say(
        f'"{culprit.id}," {sleuth.id} said softly, "did you copy those letters from {source.label}?"'
    )
    world.say(
        f"{culprit.id}'s shoulders tucked in. {culprit.pronoun().capitalize()} nodded and admitted "
        f"that {culprit.pronoun()} had used {medium.label} because {source.innocent_reason}."
    )


def confession(world: World, culprit: Entity, keeper: Entity) -> None:
    culprit.memes["honesty"] += 1
    keeper.memes["care"] += 1
    world.say(
        f'"I did not know it was a bad word," {culprit.id} whispered. "{keeper.label_word.capitalize()} '
        f"always tells me to read letters, so I just copied them."
    )
    world.say(
        f"{keeper.label_word.capitalize()} knelt beside {culprit.pronoun('object')} instead of scolding. "
        f'"Some words are rude and hurtful," {keeper.pronoun()} said. "If you do not know a word, you must ask."'
    )


def cleaning_attempt(world: World, keeper: Entity, surface_cfg: Surface,
                     cleaner: Cleaner, medium: Medium) -> None:
    sign = world.get("surface")
    world.say(
        f"Now the mystery turned into a job. {keeper.label_word.capitalize()} {cleaner.text.format(surface=surface_cfg.label)}."
    )
    if mystery_solved(cleaner, medium):
        sign.meters["obscene_mark"] = 0.0
        sign.meters["clean"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Bit by bit, the rude mark faded away until {surface_cfg.phrase} looked ready for morning again."
        )
    else:
        sign.meters["stained"] += 1
        world.say(
            f"But a shadow of the scribble still clung to {surface_cfg.phrase}. The cleaner was too weak for that mark."
        )


def restore_kindness(world: World, sleuth: Entity, friend: Entity, culprit: Entity,
                     surface_cfg: Surface) -> None:
    culprit.memes["lesson"] += 1
    sleuth.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"To make the place gentle again, {sleuth.id}, {friend.id}, and {culprit.id} worked together. "
        f"They drew stars and leaves around {surface_cfg.place_text} and wrote a new message: Be kind."
    )


def repaint_finish(world: World, keeper: Entity, sleuth: Entity, friend: Entity,
                   culprit: Entity, surface_cfg: Surface) -> None:
    sign = world.get("surface")
    sign.meters["clean"] += 1
    propagate(world, narrate=False)
    culprit.memes["lesson"] += 1
    world.say(
        f"So {keeper.label_word.capitalize()} brought out a fresh board and covered the last shadow. "
        f"Then the children helped decorate {surface_cfg.place_text} with bright, careful drawings instead."
    )
    world.say(
        f"By opening time, the ugly mystery was gone, and kindness showed where the rude mark had been."
    )


def moral_end(world: World, keeper: Entity, culprit: Entity) -> None:
    world.say(
        f'Before the first visitors arrived, {keeper.label_word.capitalize()} held up the clean sign and said, '
        f'"A clever mystery was solved today, but the bigger lesson is this: never repeat a word just because you saw it somewhere."'
    )
    world.say(
        f"{culprit.id} nodded hard. {culprit.pronoun().capitalize()} had learned that brave honesty and kind words "
        f"can mend a mistake faster than hiding ever could."
    )
    world.say(world.place.closing_image)
@dataclass
class StoryParams:
    place: str
    surface: str
    medium: str
    source: str
    cleaner: str
    sleuth_name: str
    sleuth_gender: str
    friend_name: str
    friend_gender: str
    culprit_name: str
    culprit_gender: str
    keeper: str
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
    "obscene": [
        (
            "What does obscene mean?",
            "Obscene means very rude or hurtful in a way that is not right for polite places. "
            "If you see a word you do not understand, the safest thing is to ask a grown-up instead of repeating it.",
        )
    ],
    "gut": [
        (
            "What is a gut feeling?",
            "A gut feeling is a quiet inside feeling that tells you something might matter. "
            "It is not magic, so you still look for clues and think carefully.",
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery kindly?",
            "You look for clues, ask calm questions, and tell the truth when you learn something. "
            "Being gentle helps people explain what happened.",
        )
    ],
    "soap": [
        (
            "Why does soap help clean sticky marks?",
            "Soap helps loosen dirt and sticky stuff so water can lift it away. "
            "That is why a soapy sponge works better than plain rubbing for some messes.",
        )
    ],
    "chalk": [
        (
            "Why is chalk easy to wash away?",
            "Chalk sits on the surface as soft powder, so water and wiping can remove it easily. "
            "It usually does not soak in deeply.",
        )
    ],
    "charcoal": [
        (
            "Why does charcoal smudge?",
            "Charcoal is soft and dusty, so it slides and smears when it touches your fingers. "
            "That makes dark marks, but they can often be cleaned with careful wiping.",
        )
    ],
    "berries": [
        (
            "Why can berry juice stain?",
            "Berry juice has strong color in it, so it can sink into tiny spaces and leave purple marks. "
            "That is why it needs stronger cleaning than plain chalk.",
        )
    ],
    "shared_place": [
        (
            "Why should shared places be treated with care?",
            "A shared place belongs to many people at once, so everyone should help keep it welcoming. "
            "Kind words and clean hands make other people feel safe there.",
        )
    ],
}
KNOWLEDGE_ORDER = ["obscene", "gut", "mystery", "soap", "chalk", "charcoal", "berries", "shared_place"]

GIRL_NAMES = ["Nora", "Mila", "Ivy", "Lena", "Cora", "June", "Ruby", "Tess"]
BOY_NAMES = ["Theo", "Max", "Finn", "Owen", "Jude", "Eli", "Pip", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    place = f["place"]
    source = f["source"]
    medium = f["medium"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the words "gut", "obscene", and "enthusiastic".',
        f"Tell a story set in {place.label} where {sleuth.id} and {friend.id} find an obscene scribble, follow clues, and solve the mystery with kindness.",
        f"Write a mystery with a flashback in which a child copies a rude word from {source.label} without understanding it, and the lesson is to ask before repeating unknown words written in {medium.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    culprit = f["culprit"]
    keeper = f["keeper"]
    place = f["place"]
    surface_cfg = f["surface_cfg"]
    medium = f["medium"]
    source = f["source"]
    cleaner = f["cleaner"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, {friend.id}, and little {culprit.id} at {place.label}. "
            f"They are joined by the {keeper.label_word}, who helps turn a mystery into a lesson.",
        ),
        (
            "What was the mystery?",
            f"The children found an obscene word on {surface_cfg.phrase} when they arrived to help. "
            f"That rude scribble did not belong in a shared place, so they had to learn who wrote it and why.",
        ),
        (
            f"Why did {sleuth.id} get a gut feeling?",
            f"{sleuth.id} noticed the clue that the mark had been made at little-hand height and looked borrowed, not angry. "
            f"That made {sleuth.pronoun('object')} suspect that someone young had copied the word without understanding it.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {sleuth.id} remembered {culprit.id} studying words from {source.label}. "
            f"That memory explained where the rude letters had come from and helped solve the mystery gently.",
        ),
        (
            f"Why did {culprit.id} write the word?",
            f"{culprit.id} copied the letters because {source.innocent_reason}. "
            f"{culprit.pronoun().capitalize()} did not know the word was obscene, which is why telling the truth mattered so much afterward.",
        ),
    ]
    if outcome == "cleaned":
        qa.append(
            (
                f"How did the {keeper.label_word} fix the problem?",
                f"The {keeper.label_word} {cleaner.qa_text}. Then the children wrote a kind message and drew careful pictures in its place. "
                f"The clean sign showed right away that the mistake had been mended.",
            )
        )
    else:
        qa.append(
            (
                f"Did the first cleaning work?",
                f"No. The first cleaner was too weak, so a shadow of the mark stayed behind. "
                f"After that, the {keeper.label_word} covered it with a fresh board so the shared place could feel welcoming again.",
            )
        )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned not to repeat words they do not understand, especially rude ones. "
            f"They also learned that honesty and kindness help fix a mistake faster than hiding it.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"obscene", "gut", "mystery"} | set(f["place"].tags)
    cleaner = f["cleaner"]
    medium = f["medium"]
    tags |= set(cleaner.tags)
    tags |= set(medium.tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bakery",
        surface="chalkboard",
        medium="chalk",
        source="delivery_box",
        cleaner="wet_cloth",
        sleuth_name="Nora",
        sleuth_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        culprit_name="Pip",
        culprit_gender="boy",
        keeper="mother",
    ),
    StoryParams(
        place="library",
        surface="notice_board",
        medium="berry_juice",
        source="comic_page",
        cleaner="soapy_sponge",
        sleuth_name="Ivy",
        sleuth_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        culprit_name="Leo",
        culprit_gender="boy",
        keeper="father",
    ),
    StoryParams(
        place="garden",
        surface="window_step",
        medium="charcoal",
        source="whispered_joke",
        cleaner="eraser_pad",
        sleuth_name="June",
        sleuth_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        culprit_name="Eli",
        culprit_gender="boy",
        keeper="mother",
    ),
    StoryParams(
        place="bakery",
        surface="window_step",
        medium="berry_juice",
        source="delivery_box",
        cleaner="wet_cloth",
        sleuth_name="Ruby",
        sleuth_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        culprit_name="Pip",
        culprit_gender="boy",
        keeper="father",
    ),
]


def outcome_of(params: StoryParams) -> str:
    cleaner = CLEANERS[params.cleaner]
    medium = MEDIUMS[params.medium]
    return "cleaned" if mystery_solved(cleaner, medium) else "repainted"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Place, Surface, Medium) :-
    place(Place), surface(Surface), medium(Medium),
    has_surface(Place, Surface),
    washable(Surface),
    accepts(Surface, Medium),
    sensible_exists.

sensible_exists :- cleaner(C), sense(C, S), sense_min(M), S >= M.
sensible(C) :- cleaner(C), sense(C, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
cleaned :- chosen_cleaner(C), chosen_medium(M), power(C, P), stain(M, S), P >= S.
repainted :- not cleaned.
outcome(cleaned) :- cleaned.
outcome(repainted) :- repainted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for surface_id in sorted(place.surfaces):
            lines.append(asp.fact("has_surface", place_id, surface_id))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        if surface.washable:
            lines.append(asp.fact("washable", surface_id))
        for medium_id in sorted(surface.accepts):
            lines.append(asp.fact("accepts", surface_id, medium_id))
    for medium_id, medium in MEDIUMS.items():
        lines.append(asp.fact("medium", medium_id))
        lines.append(asp.fact("stain", medium_id, medium.stain))
    for cleaner_id, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cleaner_id))
        lines.append(asp.fact("sense", cleaner_id, cleaner.sense))
        lines.append(asp.fact("power", cleaner_id, cleaner.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cleaner", params.cleaner),
            asp.fact("chosen_medium", params.medium),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    a_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if a_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(a_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in clingo:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in python:", sorted(p_valid - a_valid))

    a_sens = set(asp_sensible())
    p_sens = {c.id for c in sensible_cleaners()}
    if a_sens == p_sens:
        print(f"OK: sensible cleaners match ({sorted(a_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible cleaners: clingo={sorted(a_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle mystery about an obscene scribble, a gut feeling, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--medium", choices=MEDIUMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and args.medium:
        surface = SURFACES[args.surface]
        medium = MEDIUMS[args.medium]
        if not can_mark(surface, medium):
            raise StoryError(explain_surface_rejection(surface, medium))
    if args.place and args.surface:
        if args.surface not in PLACES[args.place].surfaces:
            raise StoryError(
                f"(No story: {SURFACES[args.surface].label} does not belong in {PLACES[args.place].label} here.)"
            )
    if args.cleaner and CLEANERS[args.cleaner].sense < SENSE_MIN:
        raise StoryError(explain_cleaner_rejection(args.cleaner))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.surface is None or combo[1] == args.surface)
        and (args.medium is None or combo[2] == args.medium)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, surface_id, medium_id = rng.choice(sorted(combos))
    source_id = args.source or rng.choice(sorted(SOURCES))
    cleaner_id = args.cleaner or rng.choice(sorted(c.id for c in sensible_cleaners()))
    keeper = args.keeper or rng.choice(["mother", "father"])

    sleuth_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if sleuth_gender == "girl" else "girl"
    culprit_gender = rng.choice(["girl", "boy"])
    sleuth_name = _pick_name(rng, sleuth_gender, set())
    friend_name = _pick_name(rng, friend_gender, {sleuth_name})
    culprit_name = _pick_name(rng, culprit_gender, {sleuth_name, friend_name})

    return StoryParams(
        place=place_id,
        surface=surface_id,
        medium=medium_id,
        source=source_id,
        cleaner=cleaner_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        culprit_name=culprit_name,
        culprit_gender=culprit_gender,
        keeper=keeper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.medium not in MEDIUMS:
        raise StoryError(f"(Unknown medium: {params.medium})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.cleaner not in CLEANERS:
        raise StoryError(f"(Unknown cleaner: {params.cleaner})")
    place = PLACES[params.place]
    surface_cfg = SURFACES[params.surface]
    medium = MEDIUMS[params.medium]
    source = SOURCES[params.source]
    cleaner = CLEANERS[params.cleaner]

    if params.surface not in place.surfaces:
        raise StoryError(
            f"(No story: {surface_cfg.label} does not belong in {place.label} here.)"
        )
    if not can_mark(surface_cfg, medium):
        raise StoryError(explain_surface_rejection(surface_cfg, medium))
    if cleaner.sense < SENSE_MIN:
        raise StoryError(explain_cleaner_rejection(params.cleaner))

    world = tell(
        place=place,
        surface_cfg=surface_cfg,
        medium=medium,
        source=source,
        cleaner=cleaner,
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        culprit_name=params.culprit_name,
        culprit_gender=params.culprit_gender,
        keeper_type=params.keeper,
    )

    flashback = _flashback_text(world.facts["sleuth"], world.facts["culprit"], source)
    world.facts["flashback_text"] = flashback

    story_text = world.render().replace(
        "Then a flashback flickered through " + world.facts["sleuth"].id + "'s mind. " + source.flashback,
        "Then a flashback flickered through " + world.facts["sleuth"].id + "'s mind. " + flashback,
    )
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible cleaners: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, surface, medium) combos:\n")
        for place, surface, medium in combos:
            print(f"  {place:8} {surface:12} {medium}")
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
                f"### {p.sleuth_name}, {p.friend_name}, and {p.culprit_name}: "
                f"{p.medium} on {p.surface} at {p.place} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(place: Place, surface_cfg: Surface, medium: Medium, source: Source,
         cleaner: Cleaner, sleuth_name: str = "Nora", sleuth_gender: str = "girl",
         friend_name: str = "Theo", friend_gender: str = "boy",
         culprit_name: str = "Pip", culprit_gender: str = "boy",
         keeper_type: str = "mother") -> World:
    world = World(place)
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        traits=["careful", "curious"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["enthusiastic", "loyal"],
    ))
    culprit = world.add(Entity(
        id=culprit_name,
        kind="character",
        type=culprit_gender,
        role="culprit",
        traits=["little", "imitative"],
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=keeper_type,
        role="keeper",
        label="the keeper",
    ))
    surface = world.add(Entity(
        id="surface",
        kind="thing",
        type="surface",
        label=surface_cfg.label,
    ))
    world.facts.update(
        place=place,
        surface_cfg=surface_cfg,
        medium=medium,
        source=source,
        cleaner=cleaner,
        sleuth=sleuth,
        friend=friend,
        culprit=culprit,
        keeper=keeper,
        clue=medium.clue,
    )

    inspect_mark(world, sleuth, friend, surface_cfg, medium)
    clue_beat(world, sleuth, medium)

    world.para()
    flashback_beat(world, sleuth, culprit, source)
    gentle_question(world, sleuth, culprit, source, medium)
    confession(world, culprit, keeper)

    world.para()
    cleaning_attempt(world, keeper, surface_cfg, cleaner, medium)
    cleaned = mystery_solved(cleaner, medium)
    if cleaned:
        restore_kindness(world, sleuth, friend, culprit, surface_cfg)
    else:
        repaint_finish(world, keeper, sleuth, friend, culprit, surface_cfg)

    world.para()
    moral_end(world, keeper, culprit)
    world.facts["outcome"] = "cleaned" if cleaned else "repainted"
    world.facts["confessed"] = culprit.memes["honesty"] >= THRESHOLD
    world.facts["lesson_learned"] = culprit.memes["lesson"] >= THRESHOLD
    return world


PLACES = {
    "bakery": Place(
        id="bakery",
        label="the little bakery",
        keeper_word="baker",
        opening_image="warm buns were cooling on trays and the window still held the blue hush before opening",
        closing_image="Soon the window glowed with warm bread, the sign smiled kindly, and the mystery felt safely tucked away.",
        surfaces={"chalkboard", "window_step"},
        tags={"bakery", "shared_place"},
    ),
    "library": Place(
        id="library",
        label="the small library",
        keeper_word="librarian",
        opening_image="sunlight was only beginning to climb the shelves and the front hall smelled like paper and polish",
        closing_image="Soon children padded in for story time, and the clean board by the door looked ready for good words only.",
        surfaces={"chalkboard", "notice_board"},
        tags={"library", "shared_place"},
    ),
    "garden": Place(
        id="garden",
        label="the community garden shed",
        keeper_word="gardener",
        opening_image="dew still shone on the bean leaves and watering cans waited by the door like sleepy silver ducks",
        closing_image="Soon bees hummed over the flowers, and the neat sign by the shed looked as cheerful as the garden itself.",
        surfaces={"notice_board", "window_step"},
        tags={"garden", "shared_place"},
    ),
}

SURFACES = {
    "chalkboard": Surface(
        id="chalkboard",
        label="chalkboard sign",
        phrase="the black chalkboard sign",
        place_text="the sign",
        washable=True,
        accepts={"chalk", "charcoal"},
        tags={"sign", "board"},
    ),
    "notice_board": Surface(
        id="notice_board",
        label="painted notice board",
        phrase="the painted notice board",
        place_text="the board",
        washable=True,
        accepts={"chalk", "berry_juice"},
        tags={"sign", "board"},
    ),
    "window_step": Surface(
        id="window_step",
        label="white window step",
        phrase="the white window step",
        place_text="the step",
        washable=True,
        accepts={"berry_juice", "charcoal"},
        tags={"stone", "shared_place"},
    ),
}

MEDIUMS = {
    "chalk": Medium(
        id="chalk",
        label="chalk",
        phrase="red chalk",
        clue="powdery dust on the lower edge, almost at little-hand height",
        stain=1,
        tags={"chalk", "easy_clean"},
    ),
    "berry_juice": Medium(
        id="berry_juice",
        label="berry juice",
        phrase="dark berry juice",
        clue="a sticky purple shine and one tiny thumbprint beside the last letter",
        stain=3,
        tags={"berries", "stain"},
    ),
    "charcoal": Medium(
        id="charcoal",
        label="charcoal",
        phrase="smudgy charcoal",
        clue="soft black smears and a half-moon print where a small palm had dragged",
        stain=2,
        tags={"charcoal", "smudge"},
    ),
}

SOURCES = {
    "delivery_box": Source(
        id="delivery_box",
        label="a delivery box in the alley",
        flashback="Yesterday, while carrying napkins outside, {sleuth} had seen {culprit} tracing letters on a delivery box with one finger, fascinated by the shapes."
                  .replace("{sleuth}", "someone")
                  .replace("{culprit}", "someone"),
        innocent_reason="the same letters had been printed on a torn delivery box and looked interesting",
        tags={"copying", "print"},
    ),
    "comic_page": Source(
        id="comic_page",
        label="an old comic page",
        flashback="Last afternoon, near the broom closet, {sleuth} had glimpsed {culprit} studying a crumpled comic page with wide eyes, sounding out every letter as if each one were treasure."
                  .replace("{sleuth}", "someone")
                  .replace("{culprit}", "someone"),
        innocent_reason="the letters came from a crumpled comic page and looked like a puzzle",
        tags={"copying", "paper"},
    ),
    "whispered_joke": Source(
        id="whispered_joke",
        label="a rude joke heard outside",
        flashback="At sunset, by the gate, {sleuth} had heard bigger children giggle over a rude joke while {culprit} stood nearby, listening harder than anyone realized."
                  .replace("{sleuth}", "someone")
                  .replace("{culprit}", "someone"),
        innocent_reason="the word had been heard outside and sounded exciting without making sense",
        tags={"copying", "heard_word"},
    ),
}

CLEANERS = {
    "wet_cloth": Cleaner(
        id="wet_cloth",
        sense=2,
        power=1,
        text="took a wet cloth and wiped the {surface} in slow circles",
        fail="wiped with a wet cloth",
        qa_text="wiped the mark away with a wet cloth",
        tags={"cleaning", "cloth"},
    ),
    "soapy_sponge": Cleaner(
        id="soapy_sponge",
        sense=3,
        power=3,
        text="mixed soap in a little bucket and scrubbed the {surface} with a sponge",
        fail="scrubbed with a soapy sponge",
        qa_text="scrubbed the mark away with soap and a sponge",
        tags={"cleaning", "soap"},
    ),
    "eraser_pad": Cleaner(
        id="eraser_pad",
        sense=3,
        power=2,
        text="used a soft eraser pad and a dab of cleaner on the {surface}",
        fail="rubbed at the mark with an eraser pad",
        qa_text="rubbed the mark off with an eraser pad",
        tags={"cleaning", "eraser"},
    ),
    "dry_tissue": Cleaner(
        id="dry_tissue",
        sense=1,
        power=0,
        text="tried to rub the {surface} with a dry tissue",
        fail="rubbed with a dry tissue",
        qa_text="rubbed at the mark with a dry tissue",
        tags={"cleaning"},
    ),
}


def _flashback_text(sleuth: Entity, culprit: Entity, source: Source) -> str:
    mapping = {
        "delivery_box": (
            f"Yesterday, while carrying napkins outside, {sleuth.id} had seen {culprit.id} "
            f"tracing letters on a delivery box with one finger, fascinated by the shapes."
        ),
        "comic_page": (
            f"Last afternoon, near the broom closet, {sleuth.id} had glimpsed {culprit.id} "
            f"studying a crumpled comic page with wide eyes, sounding out every letter as if "
            f"each one were treasure."
        ),
        "whispered_joke": (
            f"At sunset, by the gate, {sleuth.id} had heard bigger children giggle over a rude "
            f"joke while {culprit.id} stood nearby, listening harder than anyone realized."
        ),
    }
    return mapping[source.id]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_cleaners():
        return combos
    for place_id, place in PLACES.items():
        for surface_id in sorted(place.surfaces):
            surface = SURFACES[surface_id]
            for medium_id, medium in MEDIUMS.items():
                if can_mark(surface, medium):
                    combos.append((place_id, surface_id, medium_id))
    return combos

if __name__ == "__main__":
    main()
