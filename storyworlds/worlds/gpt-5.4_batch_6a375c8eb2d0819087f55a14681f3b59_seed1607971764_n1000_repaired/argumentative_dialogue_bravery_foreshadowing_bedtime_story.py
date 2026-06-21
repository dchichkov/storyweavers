#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py
=========================================================================================

A standalone storyworld for a gentle bedtime tale about a child who hears a
nighttime sound, becomes argumentative about what it must mean, and then finds
bravery through a calm check with a grown-up. The world is built around harmless
causes of bedtime scares, small foreshadowing clues that appear before the scare,
and a reasonableness gate that only allows checks that could honestly reveal and
fix the cause.

Run it
------
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py --cause branch --sign tapping
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py --cause kitten --tool curtain_peek
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/argumentative_dialogue_bravery_foreshadowing_bedtime_story.py --verify
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
BRAVE_THRESHOLD = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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


@dataclass
class Sign:
    id: str
    label: str
    onset: str
    worry_line: str
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
class Cause:
    id: str
    label: str
    sign: str
    place: str
    clue: str
    reveal: str
    fix: str
    ending_image: str
    child_action: str
    safe_with: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    reaches: set[str] = field(default_factory=set)
    child_safe: bool = True
    help_line: str = ""
    action_line: str = ""
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
class Trait:
    id: str
    label: str
    bravery: int
    argumentative: int
    calming: str
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


def _r_fear_from_strange(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if room.meters["strange"] < THRESHOLD:
        return []
    sig = ("fear_from_strange",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return []


def _r_argument_from_fear(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD or child.attrs.get("argumentative_level", 0) <= 0:
        return []
    sig = ("argument",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["argument"] += 1
    return []


def _r_calm_after_fix(world: World) -> list[str]:
    child = world.get("child")
    if not world.facts.get("cause_fixed"):
        return []
    sig = ("calm_after_fix",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1
    child.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fear_from_strange", tag="emotional", apply=_r_fear_from_strange),
    Rule(name="argument_from_fear", tag="emotional", apply=_r_argument_from_fear),
    Rule(name="calm_after_fix", tag="emotional", apply=_r_calm_after_fix),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def cause_matches(sign: Sign, cause: Cause) -> bool:
    return sign.id == cause.sign


def tool_reaches(tool: Tool, cause: Cause) -> bool:
    return cause.place in tool.reaches and tool.id in cause.safe_with


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sign_id, sign in SIGNS.items():
        for cause_id, cause in CAUSES.items():
            if not cause_matches(sign, cause):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_reaches(tool, cause):
                    combos.append((sign_id, cause_id, tool_id))
    return combos


def bravery_outcome(trait: Trait, tool: Tool) -> str:
    if trait.bravery >= BRAVE_THRESHOLD and tool.child_safe:
        return "child_helps"
    return "hold_close"


def predict_check(cause: Cause, tool: Tool) -> dict:
    return {
        "found": tool_reaches(tool, cause),
        "fixable": tool_reaches(tool, cause),
        "place": cause.place,
    }


def bedroom_opening(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"At bedtime, {child.id}'s room was soft with lamplight, and {parent.label_word} "
        f"tucked the blanket under {child.pronoun('possessive')} chin."
    )
    world.say(
        f"{child.id} had been chatty all evening, asking one more question after another, "
        f"because sleep still felt a little far away."
    )


def foreshadow(world: World, cause: Cause) -> None:
    world.say(cause.clue)


def settle(world: World, child: Entity, trait: Trait) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f'"Good night," said {child.id}. But {child.pronoun().capitalize()} was still {trait.calming}, '
        f"listening to the room as if it might whisper back."
    )


def strange_sign(world: World, sign: Sign) -> None:
    room = world.get("room")
    room.meters["strange"] += 1
    propagate(world, narrate=False)
    world.say(sign.onset)


def argument(world: World, child: Entity, parent: Entity, sign: Sign) -> None:
    world.say(
        f'"{sign.worry_line}" {child.id} whispered. Then {child.pronoun()} sat up and grew argumentative. '
        f'"No, {parent.label_word}, do not say it is nothing. I heard it."'
    )
    if child.attrs.get("argumentative_level", 0) >= 2:
        world.say(
            f'"What if it is waiting for me to close my eyes?" {child.pronoun()} asked. '
            f'"What if it is a monster that knows bedtime?"'
        )


def reassurance(world: World, child: Entity, parent: Entity, tool: Tool, cause: Cause) -> None:
    pred = predict_check(cause, tool)
    world.facts["predicted_place"] = pred["place"]
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed and answered softly, '
        f'"Brave does not mean pretending you are not scared. Brave means we look carefully."'
    )
    world.say(
        f'"We can use {tool.phrase} and check the {cause.place} together," {parent.pronoun()} said.'
    )


def choose_bravery(world: World, child: Entity, tool: Tool, trait: Trait, outcome: str) -> None:
    child.memes["courage"] = float(trait.bravery)
    if outcome == "child_helps":
        world.say(
            f"{child.id} took a slow breath. {tool.help_line} {child.pronoun().capitalize()} was still scared, "
            f"but the fear no longer pushed {child.pronoun('object')} flat against the pillow."
        )
    else:
        world.say(
            f"{child.id} nodded and reached for {parental_hand_phrase(child)}. "
            f"{child.pronoun().capitalize()} was still scared, so {child.pronoun()} stayed tucked close "
            f"while {parent_role_word(world)} moved first."
        )


def parental_hand_phrase(child: Entity) -> str:
    return f"{child.pronoun('possessive')} grown-up's hand"


def parent_role_word(world: World) -> str:
    return world.get("parent").label_word


def inspect_and_fix(world: World, child: Entity, parent: Entity, cause: Cause, tool: Tool, outcome: str) -> None:
    if outcome == "child_helps":
        world.say(tool.action_line)
        world.say(cause.child_action)
    else:
        world.say(
            f"{parent.label_word.capitalize()} used {tool.phrase} first, while {child.id} watched from the bed "
            f"with wide eyes."
        )
    world.say(cause.reveal)
    world.facts["cause_fixed"] = True
    propagate(world, narrate=False)
    world.say(cause.fix)


def bedtime_end(world: World, child: Entity, parent: Entity, cause: Cause, trait: Trait, outcome: str) -> None:
    if outcome == "child_helps":
        child.memes["pride"] += 1
        world.say(
            f'"You helped solve it," said {parent.label_word}. "{trait.label.capitalize()} hearts can tremble and still be brave."'
        )
    else:
        world.say(
            f'"You stayed with me and listened," said {parent.label_word}. "That is brave too."'
        )
    world.say(
        f"{child.id} settled back under the blanket. {cause.ending_image}"
    )
    world.say(
        f"Soon the room sounded ordinary again, and {child.id} fell asleep before the next page of the bedtime book could even be turned."
    )


def tell(
    *,
    sign: Sign,
    cause: Cause,
    tool: Tool,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: Trait,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", kind="thing", type="bedroom", label="the bedroom", role="room"))

    child.attrs["display_name"] = child_name
    child.attrs["argumentative_level"] = trait.argumentative
    child.memes["fear"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["courage"] = float(trait.bravery)
    parent.memes["patience"] = 1.0
    room.meters["strange"] = 0.0

    world.facts["cause_fixed"] = False

    bedroom_opening(world, child, parent)
    foreshadow(world, cause)
    settle(world, child, trait)

    world.para()
    strange_sign(world, sign)
    argument(world, child, parent, sign)
    reassurance(world, child, parent, tool, cause)

    outcome = bravery_outcome(trait, tool)
    world.facts["outcome"] = outcome

    world.para()
    choose_bravery(world, child, tool, trait, outcome)
    inspect_and_fix(world, child, parent, cause, tool, outcome)

    world.para()
    bedtime_end(world, child, parent, cause, trait, outcome)

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        sign=sign,
        cause=cause,
        tool=tool,
        trait=trait,
        child_name=child_name,
        revealed=True,
        fixed=world.facts["cause_fixed"],
    )
    return world


SIGNS = {
    "tapping": Sign(
        id="tapping",
        label="tapping at the window",
        onset="A little later, a tap-tap-tap came through the dark.",
        worry_line="Something is tapping on my window",
        tags={"night_noise", "window"},
    ),
    "rustling": Sign(
        id="rustling",
        label="rustling under the bed",
        onset="Just when the house seemed still, a soft rustle slipped out from under the bed.",
        worry_line="Something is moving under my bed",
        tags={"night_noise", "under_bed"},
    ),
    "whispering": Sign(
        id="whispering",
        label="whispering by the curtain",
        onset="Then a hushy, brushing whisper shivered near the curtain.",
        worry_line="Something is whispering by the curtain",
        tags={"night_noise", "curtain"},
    ),
}

CAUSES = {
    "branch": Cause(
        id="branch",
        label="a windy branch",
        sign="tapping",
        place="window",
        clue="Before the lamp was switched low, a skinny tree branch had kept bowing across the moonlit glass outside.",
        reveal="At the window, the moon showed the truth at once: a small branch was bobbing in the wind and tapping the pane.",
        fix="Parent eased the window latch snug and drew the branch away from the glass with a gentle push, and the tapping stopped.",
        ending_image="The moon stayed silver on the floor, but now it looked peaceful instead of secret.",
        child_action='Holding very still, the child lifted the flashlight beam so the shine could catch the moving leaves.',
        safe_with={"flashlight", "window_latch"},
        tags={"branch", "wind", "window"},
    ),
    "kitten": Cause(
        id="kitten",
        label="the sleepy kitten",
        sign="rustling",
        place="under_bed",
        clue="At story time, the family kitten had chased a sock across the rug and vanished under the bed, though nobody had thought much of it then.",
        reveal="Under the bed, two round eyes blinked in the light, and a tiny gray kitten gave an offended little mew.",
        fix="Parent scooped the kitten into the basket beside the dresser, where it turned in a soft circle and settled down.",
        ending_image="The basket by the dresser rose and fell with tiny sleepy breaths.",
        child_action='The child knelt bravely at the bedside and held the light low enough to see the dust ruffle and the little whiskers twitch.',
        safe_with={"flashlight", "underbed_peek"},
        tags={"kitten", "pet", "under_bed"},
    ),
    "balloon": Cause(
        id="balloon",
        label="a drifting balloon ribbon",
        sign="whispering",
        place="curtain",
        clue="A shiny balloon from earlier in the day still floated near the dresser, its curling ribbon long enough to stir whenever the air moved.",
        reveal="By the curtain, the ribbon from the balloon was sliding back and forth across the fabric with a feathery hiss.",
        fix="Parent tied the ribbon short and moved the balloon to the reading chair, where it could not brush the curtain anymore.",
        ending_image="The balloon bobbed quietly in the corner like a tired moon of its own.",
        child_action='The child pointed the beam at the curtain and watched the silver ribbon glimmer into sight.',
        safe_with={"flashlight", "curtain_peek"},
        tags={"balloon", "curtain", "ribbon"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="the small flashlight from the bedside drawer",
        reaches={"window", "under_bed", "curtain"},
        child_safe=True,
        help_line="With careful fingers, the child accepted the flashlight and held it like a tiny star",
        action_line="Together they climbed out of bed, and the child made a bright path across the floor with the flashlight.",
        tags={"flashlight", "light"},
    ),
    "window_latch": Tool(
        id="window_latch",
        label="window latch",
        phrase="the brass window latch",
        reaches={"window"},
        child_safe=False,
        help_line="",
        action_line="",
        tags={"window", "latch"},
    ),
    "underbed_peek": Tool(
        id="underbed_peek",
        label="under-bed peek",
        phrase="a slow peek over the blanket edge and down to the floor",
        reaches={"under_bed"},
        child_safe=True,
        help_line="The child slid to the edge of the mattress and dared to look where the shadows had seemed deepest",
        action_line="Step by step, they leaned down together for a slow under-bed peek.",
        tags={"under_bed", "peek"},
    ),
    "curtain_peek": Tool(
        id="curtain_peek",
        label="curtain peek",
        phrase="a careful look behind the curtain",
        reaches={"curtain"},
        child_safe=True,
        help_line="The child swallowed once and decided to stand close enough to see for real",
        action_line="They walked to the window corner and took a careful look behind the curtain.",
        tags={"curtain", "peek"},
    ),
}

TRAITS = {
    "timid": Trait(
        id="timid",
        label="timid",
        bravery=3,
        argumentative=1,
        calming="quiet and watchful",
        tags={"feelings"},
    ),
    "curious": Trait(
        id="curious",
        label="curious",
        bravery=5,
        argumentative=1,
        calming="curious and wide-eyed",
        tags={"feelings"},
    ),
    "spirited": Trait(
        id="spirited",
        label="spirited",
        bravery=6,
        argumentative=2,
        calming="restless and bright",
        tags={"feelings"},
    ),
    "stubborn": Trait(
        id="stubborn",
        label="stubborn",
        bravery=4,
        argumentative=2,
        calming="frowning and unconvinced",
        tags={"feelings"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Noah"]


@dataclass
class StoryParams:
    sign: str
    cause: str
    tool: str
    name: str
    gender: str
    parent: str
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
    "night_noise": [
        (
            "Why can little sounds seem bigger at bedtime?",
            "At bedtime the house is quieter, so tiny taps and rustles are easier to notice. When you are already sleepy, your mind can make a small sound feel much bigger.",
        )
    ],
    "window": [
        (
            "Why does a branch tap a window?",
            "Wind can push a branch back and forth until it bumps the glass. The branch is outside, but the sound carries clearly into the room.",
        )
    ],
    "under_bed": [
        (
            "Why do under-bed sounds seem spooky?",
            "You cannot see under the bed easily from your pillow, so a harmless rustle can feel mysterious. Looking carefully with a grown-up helps turn the unknown into something ordinary.",
        )
    ],
    "curtain": [
        (
            "Why can a curtain make strange sounds?",
            "Curtains can brush and whisper when air moves around them. A ribbon or another light object can make the sound sharper.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for at night?",
            "A flashlight helps you see clearly in the dark without having to imagine what is there. Good light can make a scary mystery much smaller.",
        )
    ],
    "bravery": [
        (
            "What does being brave mean?",
            "Being brave does not mean never feeling scared. It means doing the careful right thing even while your heart is fluttering.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide under a bed?",
            "Kittens like warm, tucked-away places, and under a bed can feel like a little cave. They may crawl there for play or a nap.",
        )
    ],
    "balloon": [
        (
            "Why can a balloon ribbon make a whispery sound?",
            "A thin ribbon can slide across cloth with a soft hiss. If the air moves, the ribbon may keep brushing the same place again and again.",
        )
    ],
    "wind": [
        (
            "What does wind do outside a house at night?",
            "Wind can shake leaves, nudge branches, and rattle loose things gently. That is why nighttime sounds often come from ordinary moving things.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "night_noise",
    "window",
    "under_bed",
    "curtain",
    "flashlight",
    "bravery",
    "kitten",
    "balloon",
    "wind",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sign = f["sign"]
    cause = f["cause"]
    tool = f["tool"]
    outcome = f["outcome"]
    bravery_bit = (
        f"{child.attrs['display_name']} helps with {tool.label}"
        if outcome == "child_helps"
        else f"{child.attrs['display_name']} stays close while {parent.label_word} checks"
    )
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes dialogue, foreshadowing, and bravery, and uses the word "argumentative".',
        f"Tell a gentle nighttime story where a child hears {sign.label}, argues that it must be something scary, and then learns that {bravery_bit}.",
        f"Write a reassuring story in which {cause.label} seems frightening at first, but a calm grown-up and a careful check turn bedtime peaceful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sign = f["sign"]
    cause = f["cause"]
    tool = f["tool"]
    trait = f["trait"]
    outcome = f["outcome"]
    child_name = child.attrs["display_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child getting ready for bed, and {child_name}'s {pw}. The story follows what happens when a nighttime sound makes bedtime feel scary.",
        ),
        (
            "What was the foreshadowing clue before the scary moment?",
            f"The story quietly showed {cause.clue[0].lower() + cause.clue[1:] if cause.clue else 'a clue earlier in the room.'} That clue mattered later because it pointed toward the true cause before anyone understood it.",
        ),
        (
            f"Why did {child_name} become argumentative?",
            f"{child_name} heard {sign.label} in the dark and felt afraid, so {child.pronoun()} argued that it must mean something scary. Fear made the unknown feel larger, and that is why {child.pronoun()} pushed back when {pw} first answered calmly.",
        ),
        (
            f"How did {pw} answer the fear?",
            f"{pw.capitalize()} did not laugh or snap. {parent.pronoun().capitalize()} said that being brave means looking carefully, and then suggested using {tool.phrase} to check the {cause.place} together.",
        ),
    ]
    if outcome == "child_helps":
        qa.append(
            (
                f"How was {child_name} brave?",
                f"{child_name} was brave by helping with the check instead of hiding from the mystery. Even though {child.pronoun()} was scared, {child.pronoun()} used {tool.label} and stayed long enough to see the truth.",
            )
        )
    else:
        qa.append(
            (
                f"How was {child_name} brave even without leading the check?",
                f"{child_name} was brave by staying close and letting the careful check happen instead of running from the sound. Bravery in this story means facing the unknown with help, not pretending not to be scared.",
            )
        )
    qa.append(
        (
            "What was really making the sound?",
            f"It was {cause.label}. When they checked the {cause.place}, the strange bedtime mystery turned into something ordinary and understandable.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The cause was fixed, the room grew quiet again, and bedtime felt safe. The ending image shows the change clearly: {cause.ending_image[0].lower() + cause.ending_image[1:]}",
        )
    )
    qa.append(
        (
            f"What kind of child was {child_name} at the start, and what changed?",
            f"At the start, {child_name} was {trait.label} and frightened enough to argue. By the end, {child.pronoun()} had learned that careful looking can shrink a fear into a simple bedtime problem.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"night_noise", "bravery"}
    tags |= set(world.facts["sign"].tags)
    tags |= set(world.facts["cause"].tags)
    tags |= set(world.facts["tool"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sign="tapping",
        cause="branch",
        tool="flashlight",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="spirited",
    ),
    StoryParams(
        sign="rustling",
        cause="kitten",
        tool="underbed_peek",
        name="Ben",
        gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        sign="whispering",
        cause="balloon",
        tool="curtain_peek",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="stubborn",
    ),
    StoryParams(
        sign="tapping",
        cause="branch",
        tool="window_latch",
        name="Theo",
        gender="boy",
        parent="father",
        trait="timid",
    ),
]


def explain_rejection(sign: Sign, cause: Cause, tool: Tool) -> str:
    if not cause_matches(sign, cause):
        return (
            f"(No story: {cause.label} would not make {sign.label}. Pick a cause that honestly explains the sign.)"
        )
    if not tool_reaches(tool, cause):
        return (
            f"(No story: {tool.label} cannot carefully check and fix the {cause.place}. Pick a tool that can really reach the cause.)"
        )
    return "(No story: this bedtime mystery does not make sense together.)"


ASP_RULES = r"""
matches(S, C) :- sign(S), cause(C), cause_sign(C, S).
reaches(T, C) :- tool(T), cause(C), cause_place(C, P), tool_place(T, P), safe_with(C, T).
valid(S, C, T) :- matches(S, C), reaches(T, C).

child_helps :- chosen_trait(Tr), bravery(Tr, B), brave_threshold(M), B >= M,
               chosen_tool(T), child_safe(T).
hold_close  :- not child_helps.

outcome(child_helps) :- child_helps.
outcome(hold_close)  :- hold_close.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_sign", cause_id, cause.sign))
        lines.append(asp.fact("cause_place", cause_id, cause.place))
        for tid in sorted(cause.safe_with):
            lines.append(asp.fact("safe_with", cause_id, tid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for place in sorted(tool.reaches):
            lines.append(asp.fact("tool_place", tool_id, place))
        if tool.child_safe:
            lines.append(asp.fact("child_safe", tool_id))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("bravery", trait_id, trait.bravery))
    lines.append(asp.fact("brave_threshold", BRAVE_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    params = resolve_params(build_parser().parse_args([]), random.Random(123))
    params.seed = 123
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != bravery_outcome(TRAITS[p.trait], TOOLS[p.tool]):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime mystery, an argumentative child, and a brave careful check."
    )
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.cause and args.tool:
        if not (cause_matches(SIGNS[args.sign], CAUSES[args.cause]) and tool_reaches(TOOLS[args.tool], CAUSES[args.cause])):
            raise StoryError(explain_rejection(SIGNS[args.sign], CAUSES[args.cause], TOOLS[args.tool]))
    elif args.sign and args.cause:
        if not cause_matches(SIGNS[args.sign], CAUSES[args.cause]):
            tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
            raise StoryError(explain_rejection(SIGNS[args.sign], CAUSES[args.cause], tool))
    elif args.cause and args.tool:
        if not tool_reaches(TOOLS[args.tool], CAUSES[args.cause]):
            sign = SIGNS[args.sign] if args.sign else next(iter(SIGNS.values()))
            raise StoryError(explain_rejection(sign, CAUSES[args.cause], TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.sign is None or combo[0] == args.sign)
        and (args.cause is None or combo[1] == args.cause)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sign_id, cause_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        sign=sign_id,
        cause=cause_id,
        tool=tool_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    sign = SIGNS[params.sign]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]
    if not cause_matches(sign, cause) or not tool_reaches(tool, cause):
        raise StoryError(explain_rejection(sign, cause, tool))

    world = tell(
        sign=sign,
        cause=cause,
        tool=tool,
        child_name=params.name,
        child_gender=params.gender,
        parent_type=params.parent,
        trait=TRAITS[params.trait],
    )

    child_name = world.facts["child_name"]
    story = world.render().replace("child", child_name).replace("Parent", world.facts["parent"].label_word.capitalize())
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.replace("child", child_name), answer=a.replace("child", child_name)) for q, a in story_qa(world)],
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
        print(f"{len(combos)} compatible (sign, cause, tool) combos:\n")
        for sign, cause, tool in combos:
            print(f"  {sign:10} {cause:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.sign} from {p.cause} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
