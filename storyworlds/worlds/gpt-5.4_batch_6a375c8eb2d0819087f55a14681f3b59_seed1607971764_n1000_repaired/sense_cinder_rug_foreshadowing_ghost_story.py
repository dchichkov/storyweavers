#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py
========================================================================

A standalone storyworld for a small child-facing ghost story domain built from
the seed words "sense", "cinder", and "rug", with explicit foreshadowing.

Premise
-------
A child sleeps in an old room with a cold hearth and feels a strange sense that
someone is waiting. A single cinder on the rug foreshadows the real clue: a
trail of soot leading to a hidden keepsake that a gentle ghost cannot rest
without. If the grown-up responds with calm attention soon enough, the clue is
followed and the room grows warm again. If the clue is delayed too long, it
smears away and the ghost must wait a little longer.

Run it
------
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py --room sunroom
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py --ghost chimney_boy
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py --response bring_lamp --delay 0
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py --all --qa
python storyworlds/worlds/gpt-5.4/sense_cinder_rug_foreshadowing_ghost_story.py --verify
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
    intro: str
    rug: str
    hearth: str
    has_hearth: bool = True
    caches: set[str] = field(default_factory=set)
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
class Ghost:
    id: str
    name: str
    relic: str
    relic_phrase: str
    cache: str
    cache_phrase: str
    whisper: str
    shimmer: str
    patience: int
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
    start_text: str
    success_text: str
    fail_text: str
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


def _r_haunt(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    hearth = world.get("hearth")
    ghost = world.get("ghost")
    relic = world.get("relic")
    if ghost.meters["present"] < THRESHOLD or relic.meters["returned"] >= THRESHOLD:
        return []
    sig = ("haunt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    hearth.meters["cinder"] += 1
    hearth.meters["trail"] += float(world.facts["ghost_cfg"].patience)
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    ghost.memes["lonely"] += 1
    return ["__omen__"]


def _r_rest(world: World) -> list[str]:
    room = world.get("room")
    hearth = world.get("hearth")
    ghost = world.get("ghost")
    relic = world.get("relic")
    if relic.meters["returned"] < THRESHOLD:
        return []
    sig = ("rest",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] = 0.0
    room.meters["warm"] += 1
    hearth.meters["cinder"] = 0.0
    hearth.meters["trail"] = 0.0
    ghost.memes["lonely"] = 0.0
    ghost.memes["peace"] += 1
    return ["__peace__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="physical", apply=_r_haunt),
    Rule(name="rest", tag="emotional", apply=_r_rest),
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


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for room_id, room in ROOMS.items():
        for ghost_id, ghost in GHOSTS.items():
            if room.has_hearth and ghost.cache in room.caches:
                combos.append((room_id, ghost_id))
    return combos


def clue_strength(ghost: Ghost, delay: int) -> int:
    return max(0, ghost.patience - delay)


def clue_holds(response: Response, ghost: Ghost, delay: int) -> bool:
    return response.power >= max(1, ghost.patience - delay)


def predict_resolution(world: World, response_id: str, delay: int) -> dict:
    sim = world.copy()
    ghost_cfg = sim.facts["ghost_cfg"]
    response = RESPONSES[response_id]
    return {
        "trail_strength": clue_strength(ghost_cfg, delay),
        "holds": clue_holds(response, ghost_cfg, delay),
    }


def introduce(world: World, child: Entity, guardian: Entity, room_cfg: Room) -> None:
    world.say(
        f"That evening, {child.id} was staying with {child.pronoun('possessive')} "
        f"{guardian.label_word} in {room_cfg.label}. {room_cfg.intro}"
    )
    world.say(
        f"A quiet fire had burned there earlier, but now the hearth was dark, and "
        f"{room_cfg.rug} lay flat in the moonlight."
    )


def foreshadow(world: World, child: Entity, room_cfg: Room) -> None:
    child.memes["sense"] += 1
    world.say(
        f"As {child.id} stood by the bed, {child.pronoun()} had a strange sense "
        f"that the room was waiting for something."
    )
    world.say(
        f"The feeling was small enough to ignore, yet it stayed, like a held breath "
        f"behind the walls."
    )
    ghost = world.get("ghost")
    ghost.meters["present"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} noticed one black cinder resting on the edge of the rug, "
        f"though the fire was out and the ashes should have been still."
    )


def confide(world: World, child: Entity, guardian: Entity, ghost_cfg: Ghost, room_cfg: Room) -> None:
    world.say(
        f'"{guardian.label_word.capitalize()}," {child.id} whispered, "I think '
        f"someone wants us to look at the hearth."
    )
    world.say(
        f"{guardian.label_word.capitalize()} sat up, saw the cinder on the rug, "
        f"and felt the cold that had crept across {room_cfg.label}."
    )
    world.say(
        f'From the chimney came the faintest sound, almost a voice: "{ghost_cfg.whisper}"'
    )


def respond(world: World, guardian: Entity, child: Entity, response: Response) -> None:
    child.memes["trust"] += 1
    guardian.memes["care"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} did not laugh. {guardian.pronoun().capitalize()} "
        f"{response.start_text}."
    )


def investigate_success(
    world: World,
    child: Entity,
    guardian: Entity,
    room_cfg: Room,
    ghost_cfg: Ghost,
    response: Response,
) -> None:
    relic = world.get("relic")
    child.memes["courage"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"Soon there was not just one cinder but a tiny crooked line of them, "
        f"crossing the rug toward {ghost_cfg.cache_phrase}."
    )
    world.say(
        f"{guardian.label_word.capitalize()} {response.success_text}, and together they found "
        f"{ghost_cfg.relic_phrase} tucked away in the dust."
    )
    relic.meters["found"] += 1
    world.say(
        f"When {child.id} lifted it, the room gave a soft sigh, as if it had been "
        f"holding that breath all night."
    )
    relic.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the gray air above the hearth stood {ghost_cfg.name}, {ghost_cfg.shimmer}. "
        f"The ghost smiled at {child.id}, then placed one hand over a quiet heart "
        f"before fading like steam from a teacup."
    )
    world.say(
        f"The cold went away. Only the clean rug, the sleeping hearth, and "
        f"{ghost_cfg.relic_phrase} resting where it belonged remained."
    )


def investigate_fail(
    world: World,
    child: Entity,
    guardian: Entity,
    room_cfg: Room,
    ghost_cfg: Ghost,
    response: Response,
) -> None:
    child.memes["fear"] += 1
    child.memes["resolve"] += 1
    world.say(
        f"But by the time they bent close, the cinder had smeared into the weave "
        f"of the rug, and the rest of the trail was too faint to follow."
    )
    world.say(
        f"{guardian.label_word.capitalize()} {response.fail_text}, yet all they found "
        f"was a hush of soot and a room that still felt patient and sad."
    )
    world.say(
        f'{child.id} tucked a note by the hearth that said, "We will keep looking." '
        f"The whisper did not come again, but the cold stayed in one corner, waiting for morning."
    )


def dawn_close(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["comfort"] += 1
    guardian.memes["care"] += 1
    world.say(
        f"At dawn, {guardian.label_word.capitalize()} poured warm milk and listened "
        f"while {child.id} told the whole story again."
    )
    world.say(
        f"Because {guardian.pronoun()} had trusted that first strange sense, "
        f"{child.id} no longer felt alone in the old house."
    )
@dataclass
class StoryParams:
    room: str
    ghost: str
    response: str
    child_name: str
    child_gender: str
    guardian: str
    child_trait: str
    delay: int = 0
    keepsake_detail: str = ""
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
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story about someone spooky or mysterious, often in an old place at night. In stories for children, the ghost is sometimes sad or lonely instead of mean.",
        )
    ],
    "cinder": [
        (
            "What is a cinder?",
            "A cinder is a small dark piece left after wood or coal burns in a fire. It can look black and dusty and may still show where a fire has been.",
        )
    ],
    "rug": [
        (
            "What is a rug?",
            "A rug is a piece of thick cloth or woven fabric that lies on the floor. It can make a room feel soft and warm under your feet.",
        )
    ],
    "lamp": [
        (
            "Why would a lamp help in the dark?",
            "A lamp makes a steady light so people can see small details clearly. In a spooky room, that helps them notice clues instead of guessing.",
        )
    ],
    "listening": [
        (
            "Why is it helpful to listen carefully when something seems wrong?",
            "Listening carefully can help you notice clues before you rush past them. It also shows that you are paying calm attention instead of pretending nothing happened.",
        )
    ],
    "sewing": [
        (
            "What is a thimble for?",
            "A thimble is a small cap people wear on a finger while sewing. It protects the finger when they push a needle through cloth.",
        )
    ],
    "books": [
        (
            "Why do people press flowers in books?",
            "People press flowers in books to flatten and dry them so they can keep them. It is a quiet way to save a pretty thing from a special day.",
        )
    ],
    "chimney": [
        (
            "What does a chimney do?",
            "A chimney lets smoke from a fire rise up and out of a house. If soot falls, it can leave dark dust near the hearth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "cinder", "rug", "lamp", "listening", "sewing", "books", "chimney"]


def response_start_text(response: Response, child: Entity) -> str:
    return response.start_text.replace("{child}", child.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    ghost_cfg = f["ghost_cfg"]
    room_cfg = f["room_cfg"]
    if f["outcome"] == "rested":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "sense", "cinder", and "rug". Use foreshadowing with an early cinder on a rug.',
            f"Tell a ghost story where a child named {child.id} feels a strange sense in {room_cfg.label}, finds a cinder clue, and with {child.pronoun('possessive')} {guardian.label_word} helps {ghost_cfg.name} rest.",
            f"Write a spooky-but-kind story in which an early tiny clue foreshadows a hidden keepsake near a hearth, and the ending makes the room feel warm again.",
        ]
    return [
        f'Write a child-facing ghost story that includes the words "sense", "cinder", and "rug" and uses foreshadowing through one small clue near a dead fire.',
        f"Tell a ghost story where {child.id} feels a strange sense in {room_cfg.label}, but the cinder clue grows too faint to solve that night.",
        f"Write a gentle unresolved ghost story in which a child and a trusted grown-up listen carefully to a whisper from the hearth and promise to return in the morning.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    room_cfg = f["room_cfg"]
    ghost_cfg = f["ghost_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who spent the night in {room_cfg.label}, and {child.pronoun('possessive')} {guardian.label_word}, who chose to listen instead of brushing the feeling aside.",
        ),
        (
            f"What was the first spooky sign in {room_cfg.label}?",
            f"The first sign was one black cinder on the rug even though the fire was already out. That little clue also foreshadowed the larger cinder trail that would matter later.",
        ),
        (
            f"Why did {child.id} think the room wanted attention?",
            f"{child.id} had a strange sense that someone was waiting, and then the room turned cold around the hearth. The cold and the cinder made the feeling seem real instead of imagined.",
        ),
        (
            f"What did {child.id}'s {guardian.label_word} do when the child told the truth?",
            f"{guardian.label_word.capitalize()} did not laugh or scold. {guardian.pronoun().capitalize()} {response_start_text(response, child)}, because calm attention was the safest way to understand the clue.",
        ),
    ]
    if f["outcome"] == "rested":
        qa.extend(
            [
                (
                    "How did the early cinder clue help them later?",
                    f"It showed them where to start looking, and soon a whole line of cinders crossed the rug toward {ghost_cfg.cache_phrase}. The first cinder was foreshadowing because it hinted at the path before the path appeared.",
                ),
                (
                    f"What did they find, and why did it matter to the ghost?",
                    f"They found {ghost_cfg.relic_phrase}. It mattered because the ghost had been waiting for that lost thing to be put back where it belonged, and returning it let the lonely feeling in the room finally settle.",
                ),
                (
                    "How did the story end?",
                    f"The ghost faded peacefully, the cold left the room, and the hearth grew quiet again. The ending image proves what changed: the rug was clean, the clue was understood, and the room no longer felt like it was waiting.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "Why could they not solve the mystery that night?",
                    f"They waited too long for the fading clue, so the cinder trail sank into the rug and could not be followed. The room still felt patient and sad because the ghost's missing keepsake had not been found yet.",
                ),
                (
                    "How did the story still show kindness at the end?",
                    f"{child.id} and {child.pronoun('possessive')} {guardian.label_word} promised to keep looking in the morning instead of giving up. That promise matters because the child was listened to and did not have to carry the spooky feeling alone.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "cinder", "rug"}
    tags |= set(f["response"].tags)
    tags |= set(f["ghost_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="parlor",
        ghost="chimney_boy",
        response="bring_lamp",
        child_name="Nora",
        child_gender="girl",
        guardian="aunt",
        child_trait="quiet",
        delay=0,
        keepsake_detail="with one corner bent from years in a pocket",
    ),
    StoryParams(
        room="nursery",
        ghost="chimney_boy",
        response="hold_hand",
        child_name="Owen",
        child_gender="boy",
        guardian="mother",
        child_trait="careful",
        delay=1,
        keepsake_detail="that felt cold at first and warm a moment later",
    ),
    StoryParams(
        room="parlor",
        ghost="seamstress_aunt",
        response="bring_lamp",
        child_name="Mina",
        child_gender="girl",
        guardian="father",
        child_trait="dreamy",
        delay=0,
        keepsake_detail="that looked as if someone had polished it many times before",
    ),
    StoryParams(
        room="library",
        ghost="lost_reader",
        response="hold_hand",
        child_name="Theo",
        child_gender="boy",
        guardian="uncle",
        child_trait="curious",
        delay=0,
        keepsake_detail="with a scratch across one side like a tiny crescent moon",
    ),
    StoryParams(
        room="nursery",
        ghost="chimney_boy",
        response="hold_hand",
        child_name="Lucy",
        child_gender="girl",
        guardian="aunt",
        child_trait="gentle",
        delay=2,
        keepsake_detail="with one corner bent from years in a pocket",
    ),
]


def explain_room(room: Room) -> str:
    return (
        f"(No story: {room.label} has no hearth, so a cinder clue on the rug would "
        f"not make good sense here. Pick a room with a fireplace.)"
    )


def explain_combo(room: Room, ghost: Ghost) -> str:
    return (
        f"(No story: {ghost.name} hides {ghost.relic_phrase} in {ghost.cache_phrase}, "
        f"but {room.label} has no matching place for that clue. Pick a room and ghost "
        f"that fit the same hidden spot.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer, more careful response: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    ghost = GHOSTS[params.ghost]
    return "rested" if clue_holds(response, ghost, params.delay) else "waiting"


ASP_RULES = r"""
valid(Room, Ghost) :- room(Room), ghost(Ghost), has_hearth(Room), hides(Room, Cache), needs(Ghost, Cache).
sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.

trail_strength(Ghost, D, P - D) :- patience(Ghost, P), delay(D), P - D > 0.
trail_strength(Ghost, D, 0) :- patience(Ghost, P), delay(D), P - D <= 0.

outcome(rested) :- chosen_ghost(G), chosen_response(R), delay(D), trail_strength(G, D, T), T <= power(R).
outcome(waiting) :- chosen_ghost(G), chosen_response(R), delay(D), trail_strength(G, D, T), T > power(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        if room.has_hearth:
            lines.append(asp.fact("has_hearth", room_id))
        for cache in sorted(room.caches):
            lines.append(asp.fact("hides", room_id, cache))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("needs", ghost_id, ghost.cache))
        lines.append(asp.fact("patience", ghost_id, ghost.patience))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_ghost", params.ghost),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    clingo_sense = set(asp_sensible())
    python_sense = {resp.id for resp in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} "
            f"python={sorted(python_sense)}"
        )

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(100):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a cinder clue, and a gentle ghost."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo/Python parity and smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    if name:
        return name, chosen_gender
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return rng.choice(pool), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room:
        room = ROOMS[args.room]
        if not room.has_hearth:
            raise StoryError(explain_room(room))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.room and args.ghost:
        room = ROOMS[args.room]
        ghost = GHOSTS[args.ghost]
        if not (room.has_hearth and ghost.cache in room.caches):
            if not room.has_hearth:
                raise StoryError(explain_room(room))
            raise StoryError(explain_combo(room, ghost))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.ghost is None or combo[1] == args.ghost)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, ghost_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng, args.gender, args.name)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    child_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    keepsake_detail = rng.choice(DETAILS)
    return StoryParams(
        room=room_id,
        ghost=ghost_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        guardian=guardian,
        child_trait=child_trait,
        delay=delay,
        keepsake_detail=keepsake_detail,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    room_cfg = ROOMS[params.room]
    ghost_cfg = GHOSTS[params.ghost]
    response = RESPONSES[params.response]

    if not room_cfg.has_hearth:
        raise StoryError(explain_room(room_cfg))
    if ghost_cfg.cache not in room_cfg.caches:
        raise StoryError(explain_combo(room_cfg, ghost_cfg))

    response = Response(
        id=response.id,
        sense=response.sense,
        power=response.power,
        start_text=response.start_text.replace("{child}", params.child_name),
        success_text=response.success_text,
        fail_text=response.fail_text,
        qa_text=response.qa_text,
        tags=set(response.tags),
    )

    world = tell(
        room_cfg=room_cfg,
        ghost_cfg=ghost_cfg,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian,
        child_trait=params.child_trait,
        delay=params.delay,
        keepsake_detail=params.keepsake_detail,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, ghost) combos:\n")
        for room, ghost in combos:
            print(f"  {room:8} {ghost}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.child_name}: {sample.params.room} / "
                f"{sample.params.ghost} / {sample.params.response} ({outcome_of(sample.params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    room_cfg: Room,
    ghost_cfg: Ghost,
    response: Response,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    guardian_type: str = "aunt",
    child_trait: str = "quiet",
    delay: int = 0,
    keepsake_detail: str = "",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[child_trait],
            attrs={"keepsake_detail": keepsake_detail},
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            label="the guardian",
            role="guardian",
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=room_cfg.label,
            attrs={"room_id": room_cfg.id},
        )
    )
    hearth = world.add(
        Entity(
            id="hearth",
            kind="thing",
            type="hearth",
            label="hearth",
            attrs={"has_hearth": room_cfg.has_hearth},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label=ghost_cfg.name,
            role="ghost",
            attrs={"cache": ghost_cfg.cache},
        )
    )
    relic = world.add(
        Entity(
            id="relic",
            kind="thing",
            type="relic",
            label=ghost_cfg.relic,
            attrs={"cache": ghost_cfg.cache, "detail": keepsake_detail},
        )
    )

    world.facts["room_cfg"] = room_cfg
    world.facts["ghost_cfg"] = ghost_cfg
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["keepsake_detail"] = keepsake_detail

    introduce(world, child, guardian, room_cfg)
    foreshadow(world, child, room_cfg)

    world.para()
    confide(world, child, guardian, ghost_cfg, room_cfg)
    prediction = predict_resolution(world, response.id, delay)
    world.facts["predicted_trail"] = prediction["trail_strength"]
    respond(world, guardian, child, response)

    world.para()
    if prediction["holds"]:
        investigate_success(world, child, guardian, room_cfg, ghost_cfg, response)
        outcome = "rested"
    else:
        investigate_fail(world, child, guardian, room_cfg, ghost_cfg, response)
        outcome = "waiting"

    world.para()
    dawn_close(world, child, guardian)

    world.facts.update(
        child=child,
        guardian=guardian,
        room=room,
        hearth=hearth,
        ghost=ghost,
        relic=relic,
        outcome=outcome,
        resolved=relic.meters["returned"] >= THRESHOLD,
        clue_holds=prediction["holds"],
        foreshadowed=True,
    )
    return world


ROOMS = {
    "parlor": Room(
        id="parlor",
        label="the front parlor",
        intro="Tall curtains watched the windows, and a clock ticked as if it knew old secrets.",
        rug="a round braided rug with a pale middle",
        hearth="a marble hearth",
        has_hearth=True,
        caches={"mantel_box", "under_rug"},
        tags={"hearth", "rug"},
    ),
    "nursery": Room(
        id="nursery",
        label="the old nursery",
        intro="The wallpaper had tiny moons on it, and the rocking chair moved when no one touched it.",
        rug="a faded star-pattern rug",
        hearth="a narrow nursery hearth",
        has_hearth=True,
        caches={"toy_trunk", "under_rug"},
        tags={"hearth", "rug"},
    ),
    "library": Room(
        id="library",
        label="the small library",
        intro="Books climbed to the ceiling, and the shadows between them looked deeper than the room itself.",
        rug="a long red rug worn smooth in the middle",
        hearth="a black iron hearth",
        has_hearth=True,
        caches={"book_niche", "mantel_box"},
        tags={"hearth", "rug", "books"},
    ),
    "sunroom": Room(
        id="sunroom",
        label="the glass sunroom",
        intro="Fern shadows lay over the floor, and the rain tapped softly at every pane.",
        rug="a thin summer rug",
        hearth="no hearth at all",
        has_hearth=False,
        caches={"flowerpot"},
        tags={"glass", "rain"},
    ),
}

GHOSTS = {
    "chimney_boy": Ghost(
        id="chimney_boy",
        name="a soot-smudged chimney boy",
        relic="tin whistle",
        relic_phrase="the little tin whistle",
        cache="under_rug",
        cache_phrase="a loose fold near the hearthstone",
        whisper="Find what fell.",
        shimmer="with bright eyes and ash on his sleeves",
        patience=2,
        tags={"ghost", "chimney", "relic"},
    ),
    "seamstress_aunt": Ghost(
        id="seamstress_aunt",
        name="an old seamstress aunt",
        relic="silver thimble",
        relic_phrase="the silver thimble",
        cache="mantel_box",
        cache_phrase="the cracked blue box on the mantel",
        whisper="My little silver one.",
        shimmer="in a soft gray dress stitched with moon-pale thread",
        patience=3,
        tags={"ghost", "sewing", "relic"},
    ),
    "lost_reader": Ghost(
        id="lost_reader",
        name="a pale library child",
        relic="pressed violets",
        relic_phrase="the packet of pressed violets",
        cache="book_niche",
        cache_phrase="a gap behind the lowest books",
        whisper="Please keep the page.",
        shimmer="with paper-thin hands and a smile as shy as dust",
        patience=2,
        tags={"ghost", "books", "relic"},
    ),
}

RESPONSES = {
    "bring_lamp": Response(
        id="bring_lamp",
        sense=3,
        power=3,
        start_text="lit a lamp, wrapped a shawl around both of them, and came close enough to see every grain of soot",
        success_text="held the lamp low and followed the marks without hurrying",
        fail_text="searched carefully with the lamp for any hidden seam or box",
        qa_text="brought a lamp and followed the cinder marks carefully",
        tags={"lamp", "listening"},
    ),
    "hold_hand": Response(
        id="hold_hand",
        sense=2,
        power=2,
        start_text="took {child}'s hand and listened before moving a single thing",
        success_text="followed the cinders slowly while keeping one hand around the child",
        fail_text="kept a steady arm around the child and checked the hearth and floorboards",
        qa_text="held the child's hand and followed the cinder trail",
        tags={"comfort", "listening"},
    ),
    "sweep_first": Response(
        id="sweep_first",
        sense=1,
        power=1,
        start_text="reached for the brush to sweep up the mess before studying it",
        success_text="brushed at the ashes and looked for a clue afterward",
        fail_text="swept away the clearest marks before the clue could be understood",
        qa_text="swept at the ashes first",
        tags={"cleanup"},
    ),
}


GIRL_NAMES = ["Nora", "Mina", "Elsie", "Clara", "Lucy", "May", "Ivy", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Miles", "Evan", "Finn", "Jude", "Noel", "Leo"]
TRAITS = ["quiet", "careful", "dreamy", "curious", "brave", "gentle"]
DETAILS = [
    "with one corner bent from years in a pocket",
    "that felt cold at first and warm a moment later",
    "with a scratch across one side like a tiny crescent moon",
    "that looked as if someone had polished it many times before",
]

if __name__ == "__main__":
    main()
