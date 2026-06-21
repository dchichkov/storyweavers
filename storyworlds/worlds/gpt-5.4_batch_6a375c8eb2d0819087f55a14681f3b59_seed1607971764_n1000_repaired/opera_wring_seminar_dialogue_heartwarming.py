#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py
=======================================================================

A standalone story world about a child at a little music seminar where an opera
exercise turns into a moment of worry, help, and brave singing.

The domain is intentionally small and constraint-checked:
- a child comes to a friendly seminar about opera
- a tiny problem appears before the child sings
- a helper chooses a support that must actually fit the problem
- the world state drives a warm ending that shows what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py --trouble dry_throat --support warm_water
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py --trouble forgotten_line --support hand_squeeze
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/opera_wring_seminar_dialogue_heartwarming.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f", "coach_f"}
        male = {"boy", "father", "man", "teacher_m", "coach_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "coach_f": "coach",
            "coach_m": "coach",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Config registries
# ---------------------------------------------------------------------------
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
class Seminar:
    id: str
    place: str
    room_detail: str
    opera_title: str
    image: str
    final_image: str
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
class Trouble:
    id: str
    cue: str
    visible: str
    child_line: str
    need: str
    risk: str
    wring_text: str
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
class Support:
    id: str
    label: str
    helps: set[str]
    action_text: str
    helper_line: str
    effect_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


def _r_anxiety_shows(world: World) -> list[str]:
    child = world.get("child")
    trouble = world.facts["trouble"]
    out: list[str] = []
    if child.memes["anxiety"] >= THRESHOLD and trouble.id == "stage_fright":
        sig = ("wring", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["wringing"] += 1
            child.meters["voice_shaky"] += 1
            out.append("__wring__")
    return out


def _r_dry_voice(world: World) -> list[str]:
    child = world.get("child")
    trouble = world.facts["trouble"]
    out: list[str] = []
    if trouble.id == "dry_throat" and child.memes["anxiety"] >= THRESHOLD:
        sig = ("dry_voice", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["voice_shaky"] += 1
            child.meters["throat_dry"] += 1
    return out


def _r_memory_gap(world: World) -> list[str]:
    child = world.get("child")
    trouble = world.facts["trouble"]
    out: list[str] = []
    if trouble.id == "forgotten_line" and child.memes["anxiety"] >= THRESHOLD:
        sig = ("memory_gap", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["memory_gap"] += 1
    return out


def _r_supported(world: World) -> list[str]:
    child = world.get("child")
    support = world.facts["support"]
    trouble = world.facts["trouble"]
    out: list[str] = []
    if child.meters["supported"] < THRESHOLD:
        return out
    sig = ("resolved", support.id, trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if support.id in support_for(trouble.id):
        child.memes["anxiety"] = 0.0
        child.memes["courage"] += 1
        child.meters["voice_steady"] += 1
        child.meters["ready"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="anxiety_shows", tag="emotional", apply=_r_anxiety_shows),
    Rule(name="dry_voice", tag="physical", apply=_r_dry_voice),
    Rule(name="memory_gap", tag="mental", apply=_r_memory_gap),
    Rule(name="supported", tag="repair", apply=_r_supported),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def support_for(trouble_id: str) -> set[str]:
    return {sid for sid, sup in SUPPORTS.items() if trouble_id in sup.helps}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for seminar_id in SEMINARS:
        for trouble_id in TROUBLES:
            for support_id, support in SUPPORTS.items():
                if trouble_id in support.helps:
                    combos.append((seminar_id, trouble_id, support_id))
    return combos


def explain_support(trouble: Trouble, support: Support) -> str:
    if support.id == "warm_water":
        return (
            f"(No story: {support.label} can soothe a dry throat, but it does not fix "
            f"{trouble.need}. Choose a support that really matches the child's need.)"
        )
    if support.id == "breathing_count":
        return (
            f"(No story: {support.label} helps a frightened singer feel steady, but it does "
            f"not directly fix {trouble.need}. Choose a support that really matches the child's need.)"
        )
    if support.id == "picture_card":
        return (
            f"(No story: {support.label} helps a child remember words, but it does not fix "
            f"{trouble.need}. Choose a support that really matches the child's need.)"
        )
    return (
        f"(No story: {support.label} does not solve {trouble.need}. Pick a support that fits the problem.)"
    )


def predict_success(world: World, support_id: str) -> bool:
    sim = world.copy()
    sim.facts["support"] = SUPPORTS[support_id]
    sim.get("child").meters["supported"] += 1
    propagate(sim, narrate=False)
    return sim.get("child").meters["ready"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, seminar: Seminar) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After school, {child.id} went with {helper.pronoun('possessive')} {helper.label_word} "
        f"to a little seminar at {seminar.place}. It was all about opera for children, and "
        f"{seminar.room_detail}"
    )
    world.say(
        f'On the front board, someone had written "{seminar.opera_title}" in big curly letters.'
    )


def welcome(world: World, leader: Entity, child: Entity, seminar: Seminar) -> None:
    world.say(
        f'"Today," {leader.id} said with a smile, "we are going to learn how a tiny opera story '
        f'can fill a whole room with feeling."'
    )
    world.say(
        f'{child.id} smiled back. {seminar.image}'
    )


def invite(world: World, leader: Entity, child: Entity) -> None:
    world.say(
        f'Near the end of the seminar, {leader.id} knelt beside {child.id} and said, '
        f'"Would you like to sing the last little line for us?"'
    )
    child.memes["anxiety"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=False)


def trouble_appears(world: World, child: Entity, trouble: Trouble) -> None:
    world.say(trouble.cue)
    if child.meters["wringing"] >= THRESHOLD:
        world.say(trouble.wring_text)
    world.say(f'"{trouble.child_line}" {child.id} whispered.')


def helper_notices(world: World, helper: Entity, child: Entity, trouble: Trouble) -> None:
    child.memes["trust"] += 1
    world.say(
        f'{helper.id} bent close so the room would still feel small and kind. '
        f'"I see it," {helper.pronoun()} said softly. "{trouble.visible}"'
    )


def give_support(world: World, helper: Entity, child: Entity, support: Support) -> None:
    world.say(
        f'{helper.id} {support.action_text} '
        f'"{support.helper_line}"'
    )
    child.meters["supported"] += 1
    propagate(world, narrate=False)
    world.say(support.effect_text)


def sing(world: World, leader: Entity, child: Entity, seminar: Seminar) -> None:
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    world.say(
        f'{leader.id} gave a tiny nod. {child.id} took one careful breath and sang the last line of '
        f'"{seminar.opera_title}."'
    )
    world.say(
        "The note was not huge, but it was clear and brave, and it reached every chair in the room."
    )


def ending(world: World, helper: Entity, child: Entity, seminar: Seminar) -> None:
    helper_word = helper.label_word
    world.say(
        f'Everyone clapped. "{child.id}, that was lovely," someone said from the back.'
    )
    world.say(
        f'{child.id} looked at {helper.pronoun("possessive")} {helper_word} and smiled the kind of '
        f'smile that stays warm for a long time. {seminar.final_image}'
    )


def tell(
    seminar: Seminar,
    trouble: Trouble,
    support: Support,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_name: str = "Mama",
    helper_type: str = "mother",
    leader_name: str = "Ms. Vale",
    leader_type: str = "teacher_f",
    child_trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
        attrs={"trait": child_trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_name,
    ))
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_type,
        role="leader",
        label=leader_name,
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="seminar room",
    ))

    room.meters["chairs"] = 1
    child.memes["anxiety"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["courage"] = 0.0
    child.meters["supported"] = 0.0
    child.meters["ready"] = 0.0
    world.facts["seminar"] = seminar
    world.facts["trouble"] = trouble
    world.facts["support"] = support

    introduce(world, child, helper, seminar)
    welcome(world, leader, child, seminar)

    world.para()
    invite(world, leader, child)
    trouble_appears(world, child, trouble)
    helper_notices(world, helper, child, trouble)

    world.para()
    give_support(world, helper, child, support)
    if child.meters["ready"] < THRESHOLD:
        raise StoryError(explain_support(trouble, support))
    sing(world, leader, child, seminar)

    world.para()
    ending(world, helper, child, seminar)

    world.facts.update(
        child=child,
        helper=helper,
        leader=leader,
        room=room,
        success=child.meters["ready"] >= THRESHOLD,
        wrung_hands=child.meters["wringing"] >= THRESHOLD,
        supported_with=support.id,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SEMINARS = {
    "library_evening": Seminar(
        id="library_evening",
        place="the library meeting room",
        room_detail="paper stars hung over the chairs, and a little piano waited by the window.",
        opera_title="The Moon Soup Opera",
        image="A stack of song cards sat beside the piano like tiny doors into a story.",
        final_image="On the way home, the paper stars still seemed to glitter inside her chest.",
        tags={"library", "opera", "seminar"},
    ),
    "school_music": Seminar(
        id="school_music",
        place="the school music room",
        room_detail="the xylophone bars gleamed, and the dusty curtains made the room feel secret and soft.",
        opera_title="The Sparrow's Red Umbrella",
        image="Even the old drum in the corner looked as if it was listening.",
        final_image="Outside, the hallway sounded ordinary again, but the brave note seemed to walk beside them.",
        tags={"school", "opera", "seminar"},
    ),
    "community_hall": Seminar(
        id="community_hall",
        place="the community hall",
        room_detail="folding chairs stood in a half-circle, and a bowl of lemon drops sat near the sign-in sheet.",
        opera_title="The Baker and the Blue Bird",
        image="The room smelled faintly of wood polish and warm coats drying by the door.",
        final_image="At the door, two neighbors smiled at her as if she had lit a very small lamp for everyone.",
        tags={"hall", "opera", "seminar"},
    ),
}

TROUBLES = {
    "stage_fright": Trouble(
        id="stage_fright",
        cue="When all the chairs turned toward her, the room suddenly felt bigger than before.",
        visible="You do not have to be loud right away. First we can make your brave breath come back.",
        child_line="My tummy feels fluttery, and I want to wring my hands instead of sing",
        need="calm breathing and courage",
        risk="fear could make the voice shake",
        wring_text="Her fingers began to wring together in her lap.",
        tags={"feelings", "fear"},
    ),
    "dry_throat": Trouble(
        id="dry_throat",
        cue="When she opened her mouth to try the line, it came out as a tiny scratchy sound.",
        visible="Your throat sounds dry. We can make it feel easier before you sing.",
        child_line="My voice feels dusty",
        need="a soothed throat and a steadier voice",
        risk="a dry throat could make the line thin and scratchy",
        wring_text="She touched her neck and swallowed, wishing the words would slide out more easily.",
        tags={"body", "voice"},
    ),
    "forgotten_line": Trouble(
        id="forgotten_line",
        cue="She knew the tune, but suddenly the last words drifted away as if a breeze had carried them off.",
        visible="The tune is still there. We only need to help the words come back.",
        child_line="I know it was in my head a minute ago",
        need="a clear reminder of the words",
        risk="forgetting the line could stop the song in the middle",
        wring_text="She stared at the floor and tried to catch the missing words before they flew any farther.",
        tags={"memory", "voice"},
    ),
}

SUPPORTS = {
    "breathing_count": Support(
        id="breathing_count",
        label="counting breaths together",
        helps={"stage_fright"},
        action_text='sat beside her and lifted one finger, then another. ',
        helper_line='Let us breathe in for three, and out for three. We do not have to hurry the song."',
        effect_text="By the third slow breath, the flutter in her chest stopped bumping so hard, and the room felt closer again.",
        qa_text="sat with the child and counted slow breaths until the fear settled",
        tags={"breathing", "calm"},
    ),
    "warm_water": Support(
        id="warm_water",
        label="a cup of warm water",
        helps={"dry_throat"},
        action_text='poured a little warm water from a silver flask and held out the cup. ',
        helper_line='A small sip can help your throat feel smooth again."',
        effect_text="The warm sip slid down gently, and the next practice word came out rounder and easier.",
        qa_text="gave the child a little warm water to soothe the dry throat",
        tags={"water", "voice"},
    ),
    "picture_card": Support(
        id="picture_card",
        label="the picture cue card",
        helps={"forgotten_line"},
        action_text='turned over one of the seminar cards and showed the painted blue bird on it. ',
        helper_line='Look here. The picture can carry the words back to you."',
        effect_text="As soon as she saw the little blue bird, the missing line hopped back into place inside her mind.",
        qa_text="showed the child the picture card so the missing words came back",
        tags={"memory", "card"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mina", "Eva", "Lucy", "Ada", "Rosa", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Ben", "Noah", "Leo", "Max", "Finn"]
CHILD_TRAITS = ["gentle", "curious", "bright", "thoughtful", "eager", "tender"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seminar: str
    trouble: str
    support: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    leader_name: str
    leader_type: str
    child_trait: str
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
    "opera": [
        (
            "What is an opera?",
            "An opera is a story that people tell with music and singing. The feelings are often carried by the voices as much as by the words.",
        )
    ],
    "seminar": [
        (
            "What is a seminar?",
            "A seminar is a small learning meeting where people gather to listen, practice, and ask questions together. It is usually more personal than a big show.",
        )
    ],
    "breathing": [
        (
            "Why can slow breathing help before singing?",
            "Slow breathing helps the body calm down and gives the voice a steadier start. When a singer feels less frightened, the sound can come out more smoothly.",
        )
    ],
    "water": [
        (
            "Why can warm water help a singer?",
            "Warm water can make a dry throat feel more comfortable. When the throat feels less scratchy, it is easier to make a clear sound.",
        )
    ],
    "memory": [
        (
            "How can a picture help someone remember words?",
            "A picture can remind the brain of the idea connected to the words. That little clue can help the missing line come back.",
        )
    ],
    "calm": [
        (
            "What does it mean to wring your hands?",
            "When someone starts to wring their hands, they twist or squeeze them together because they feel worried. It is one way nervous feelings can show on the outside.",
        )
    ],
}
KNOWLEDGE_ORDER = ["opera", "seminar", "breathing", "water", "memory", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seminar = f["seminar"]
    trouble = f["trouble"]
    support = f["support"]
    child = f["child"]
    return [
        f'Write a heartwarming story for a young child about an opera seminar where a child faces a small problem before singing and gets kind help. Include the words "opera", "wring", and "seminar".',
        f"Tell a gentle story with dialogue where {child.id} is at a seminar called \"{seminar.opera_title}\" and needs help with {trouble.need} before singing one brave line.",
        f"Write a warm story in which a helper uses {support.label} to solve a child's singing trouble, and the ending shows the child feeling changed inside.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    leader = f["leader"]
    seminar = f["seminar"]
    trouble = f["trouble"]
    support = f["support"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who goes to a small seminar about opera, and {helper.id}, the {helper_word} who helps when singing suddenly feels hard.",
        ),
        (
            "Where does the story happen?",
            f"It happens at {seminar.place} during a children's seminar about opera. The room matters because the child is asked to sing there in front of everyone.",
        ),
        (
            f"What problem did {child.id} have before singing?",
            f"{child.id} had {trouble.need} trouble just before the last line. {trouble.risk[0].upper()}{trouble.risk[1:]}, so the little song felt harder than it had a moment before.",
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} {support.qa_text}. That help matched the real problem, so the child could feel ready instead of stuck.",
        ),
        (
            f"Why was the ending heartwarming?",
            f"The child did not become huge or perfect; {child.id} simply became brave enough to sing. The warm part is that careful help changed a frightened moment into a proud one.",
        ),
    ]
    if f.get("wrung_hands"):
        qa.append(
            (
                f"Why did {child.id} start to wring {child.pronoun('possessive')} hands?",
                f"{child.id} began to wring {child.pronoun('possessive')} hands because the room suddenly felt big and scary. The gesture showed that the fear was in the body before the singing even started.",
            )
        )
    qa.append(
        (
            f"What did {leader.id} do?",
            f"{leader.id} invited {child.id} to sing the last little line and then waited kindly. That gentle invitation is what turned practice into a brave moment.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"opera", "seminar"}
    support_id = world.facts["support"].id
    trouble_id = world.facts["trouble"].id
    if support_id == "breathing_count":
        tags |= {"breathing", "calm"}
    elif support_id == "warm_water":
        tags |= {"water"}
    elif support_id == "picture_card":
        tags |= {"memory"}
    if trouble_id == "stage_fright":
        tags |= {"calm"}
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(
        f"  scenario: seminar={world.facts['seminar'].id} trouble={world.facts['trouble'].id} support={world.facts['support'].id}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Sem, Tr, Sup) :- seminar(Sem), trouble(Tr), support(Sup), helps(Sup, Tr).

success :- chosen_support(Sup), chosen_trouble(Tr), helps(Sup, Tr).
outcome(success) :- success.
outcome(fail) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for seminar_id in SEMINARS:
        lines.append(asp.fact("seminar", seminar_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        for trouble_id in sorted(support.helps):
            lines.append(asp.fact("helps", support_id, trouble_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_support", params.support),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "fail"


def outcome_of(params: StoryParams) -> str:
    return "success" if params.support in support_for(params.trouble) else "fail"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI / interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        seminar="library_evening",
        trouble="stage_fright",
        support="breathing_count",
        child_name="Nora",
        child_gender="girl",
        helper_name="Mama",
        helper_type="mother",
        leader_name="Ms. Vale",
        leader_type="teacher_f",
        child_trait="gentle",
    ),
    StoryParams(
        seminar="community_hall",
        trouble="dry_throat",
        support="warm_water",
        child_name="Owen",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        leader_name="Mr. Bell",
        leader_type="teacher_m",
        child_trait="thoughtful",
    ),
    StoryParams(
        seminar="school_music",
        trouble="forgotten_line",
        support="picture_card",
        child_name="Maya",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        leader_name="Ms. Vale",
        leader_type="teacher_f",
        child_trait="bright",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child at an opera seminar needs the right kind help before singing."
    )
    ap.add_argument("--seminar", choices=SEMINARS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--leader", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible seminar/trouble/support combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.support:
        if args.support not in support_for(args.trouble):
            raise StoryError(explain_support(TROUBLES[args.trouble], SUPPORTS[args.support]))

    combos = [
        combo for combo in valid_combos()
        if (args.seminar is None or combo[0] == args.seminar)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.support is None or combo[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    seminar_id, trouble_id, support_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    if args.helper:
        helper_type = args.helper
        helper_name = "Mom" if helper_type == "mother" else "Dad"
    else:
        helper_type = rng.choice(["mother", "father"])
        helper_name = "Mama" if helper_type == "mother" else "Dad"

    if args.leader:
        leader_type = args.leader
    else:
        leader_type = rng.choice(["teacher_f", "teacher_m"])
    leader_name = "Ms. Vale" if leader_type == "teacher_f" else "Mr. Bell"

    child_trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        seminar=seminar_id,
        trouble=trouble_id,
        support=support_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        leader_name=leader_name,
        leader_type=leader_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.seminar not in SEMINARS:
        raise StoryError(f"(Unknown seminar: {params.seminar})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.support not in support_for(params.trouble):
        raise StoryError(explain_support(TROUBLES[params.trouble], SUPPORTS[params.support]))

    world = tell(
        seminar=SEMINARS[params.seminar],
        trouble=TROUBLES[params.trouble],
        support=SUPPORTS[params.support],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        leader_name=params.leader_name,
        leader_type=params.leader_type,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (seminar, trouble, support) combos:\n")
        for seminar_id, trouble_id, support_id in combos:
            print(f"  {seminar_id:15} {trouble_id:15} {support_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            p = sample.params
            header = f"### {p.child_name}: {p.trouble} at {p.seminar} with {p.support}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
