#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py
========================================================================

A standalone story world for a gentle rhyming mystery: a child visits a kind
broker's office, a special photo goes missing, clues point to where it slipped,
and the mystery is solved with a happy ending.

The world is built around a few compatible combinations:
- a missing-photo cause (breeze, brochure slip, folder cling)
- the place where the photo can plausibly end up
- the clue that truthfully points there
- the recovery method that actually works

The simulation tracks:
- physical meters: slipped, hidden, found, displayed
- emotional memes: wonder, worry, relief, pride

Run it
------
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py --cause breeze
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py --hiding_place drawer
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/broker_photo_mystery_to_solve_happy_ending.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"broker": "broker", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class OfficeMood:
    id: str
    place: str
    sparkle: str
    sound: str
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
    trigger: str
    motion: str
    source: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    near: str
    accept_causes: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    line: str
    points_to: set[str] = field(default_factory=set)
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
class Method:
    id: str
    sense: int
    needs: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
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


def _r_clue_worry(world: World) -> list[str]:
    photo = world.get("photo")
    child = world.get("child")
    broker = world.get("broker")
    if photo.meters["hidden"] < THRESHOLD:
        return []
    sig = ("worry", "mystery")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    broker.memes["worry"] += 1
    world.get("office").memes["hush"] += 1
    return ["__worry__"]


def _r_found_relief(world: World) -> list[str]:
    photo = world.get("photo")
    if photo.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "found")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("child", "broker", "parent"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="clue_worry", tag="emotional", apply=_r_clue_worry),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
        for s in produced:
            world.say(s)
    return produced


def combo_valid(cause: Cause, hiding_place: HidingPlace, clue: Clue, method: Method) -> bool:
    return (
        cause.id in hiding_place.accept_causes
        and hiding_place.id in clue.points_to
        and hiding_place.id in method.needs
        and method.sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cause_id, cause in CAUSES.items():
        for place_id, place in HIDING_PLACES.items():
            for clue_id, clue in CLUES.items():
                for method_id, method in METHODS.items():
                    if combo_valid(cause, place, clue, method):
                        combos.append((cause_id, place_id, clue_id, method_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def explain_rejection(cause: Cause, hiding_place: HidingPlace, clue: Clue, method: Method) -> str:
    if cause.id not in hiding_place.accept_causes:
        return (
            f"(No story: if the photo went missing because of {cause.trigger}, "
            f"it would not plausibly end up {hiding_place.phrase}. Pick a matching hiding place.)"
        )
    if hiding_place.id not in clue.points_to:
        return (
            f"(No story: the clue '{clue.id}' would not honestly point to {hiding_place.label}. "
            f"The mystery must be solved by a truthful clue.)"
        )
    if hiding_place.id not in method.needs:
        return (
            f"(No story: method '{method.id}' is not a sensible way to recover a photo from "
            f"{hiding_place.label}. Pick a method that fits the place.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}).)"
        )
    return "(No valid mystery fits those options.)"


def predict_place(cause_id: str) -> str:
    if cause_id == "breeze":
        return "behind_sign"
    if cause_id == "brochure":
        return "brochure_stack"
    return "folder_pocket"


def opening(world: World, child: Entity, parent: Entity, broker: Entity, mood: OfficeMood) -> None:
    child.memes["wonder"] += 1
    broker.memes["pride"] += 1
    world.say(
        f"In {mood.place}, where windows threw light, "
        f"the broker smiled warm in the soft morning bright."
    )
    world.say(
        f"{child.id} came in with {child.pronoun('possessive')} {parent.title_word}, step small, eyes aglow, "
        f"while {mood.sparkle} and {mood.sound} moved slow."
    )
    world.say(
        f'"Welcome," said {broker.id}. "I have one last little show: '
        f'a photo for the welcome board before your new-house hello."'
    )


def show_board(world: World, child: Entity, broker: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"On an easel there waited a board neat and bright, "
        f"with ribbons and houses cut out just right."
    )
    world.say(
        f'But when {broker.id} reached for the photo with care, '
        f"the corner sat empty. It simply was not there."
    )


def missing_beat(world: World, child: Entity, broker: Entity, cause: Cause) -> None:
    photo = world.get("photo")
    photo.meters["slipped"] += 1
    photo.meters["hidden"] += 1
    world.facts["predicted_place"] = predict_place(cause.id)
    propagate(world, narrate=False)
    world.say(
        f"{broker.id} looked left, then right, then low to the floor. "
        f'"My photo was here just a moment before."'
    )
    world.say(
        f"{cause.source.capitalize()} {cause.motion}, so quiet and sly, "
        f"and the room held a hush like a held little sigh."
    )


def inspect_clue(world: World, child: Entity, broker: Entity, clue: Clue) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{child.id} stood still, then whispered, {clue.line}"
    )
    world.say(
        f'{broker.id} bent down and nodded. "That clue is fine. '
        f'Let us follow it softly. The answer may shine."'
    )


def search(world: World, child: Entity, broker: Entity, hiding_place: HidingPlace) -> None:
    child.memes["brave"] += 1
    world.say(
        f"Past brochures and binders they searched with great care, "
        f"for the small missing photo that once had been there."
    )
    world.say(
        f"They paused by {hiding_place.near}, then peeped with bright eyes "
        f"toward {hiding_place.phrase}, where a secret might lie."
    )


def recover(world: World, child: Entity, broker: Entity, method: Method, hiding_place: HidingPlace) -> None:
    photo = world.get("photo")
    method_text = method.action_text.format(place=hiding_place.phrase)
    world.say(
        f"{broker.id} {method_text}, not rushed and not loud, "
        f"while {child.id} stayed close and hopeful and proud."
    )
    photo.meters["hidden"] = 0.0
    photo.meters["found"] += 1
    photo.meters["displayed"] += 1
    propagate(world, narrate=False)
    world.say(
        "Out slid the photo at last with a flutter and gleam, "
        "like the end of a riddle, like waking from dream."
    )


def ending(world: World, child: Entity, parent: Entity, broker: Entity) -> None:
    world.say(
        f'{broker.id} clipped up the photo and laughed, "Now it can stay." '
        f'The hush in the office just melted away.'
    )
    world.say(
        f"{child.id} clapped twice, and {parent.title_word} laughed too, "
        f"for the board looked complete in its ribboned-up hue."
    )
    world.say(
        "And the broker, the child, and the bright shining photo "
        "made home feel more near with a happy tip-toe."
    )


def tell(
    mood: OfficeMood,
    cause: Cause,
    hiding_place: HidingPlace,
    clue: Clue,
    method: Method,
    *,
    child_name: str = "Lila",
    child_type: str = "girl",
    parent_type: str = "mother",
    broker_name: str = "Mr. Reed",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    broker = world.add(Entity(id="broker", kind="character", type="broker", label=broker_name, role="broker"))
    office = world.add(Entity(id="office", kind="thing", type="office", label="office"))
    photo = world.add(Entity(id="photo", kind="thing", type="photo", label="photo"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.id))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=hiding_place.label))
    method_ent = world.add(Entity(id="method", kind="thing", type="method", label=method.id))

    office.memes["calm"] = 1.0
    photo.meters["slipped"] = 0.0
    photo.meters["hidden"] = 0.0
    photo.meters["found"] = 0.0
    photo.meters["displayed"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    broker.memes["worry"] = 0.0

    opening(world, child, parent, broker, mood)
    show_board(world, child, broker)

    world.para()
    missing_beat(world, child, broker, cause)
    inspect_clue(world, child, broker, clue)
    search(world, child, broker, hiding_place)

    world.para()
    recover(world, child, broker, method, hiding_place)
    ending(world, child, parent, broker)

    world.facts.update(
        mood=mood,
        cause=cause,
        hiding_place=hiding_place,
        clue=clue,
        method=method,
        child=child,
        parent=parent,
        broker=broker,
        office=office,
        photo=photo,
        found=photo.meters["found"] >= THRESHOLD,
        predicted_place=predict_place(cause.id),
        solved_truthfully=hiding_place.id == predict_place(cause.id) and hiding_place.id in clue.points_to,
    )
    return world


MOODS = {
    "sunny": OfficeMood(
        id="sunny",
        place="the broker's little office",
        sparkle="golden paper houses shimmered on a string",
        sound="the wall clock gave a patient tick-tick ring",
        tags={"office"},
    ),
    "rainy": OfficeMood(
        id="rainy",
        place="the broker's little office",
        sparkle="lamplight warmed the glossy maps in rows",
        sound="soft rain tapped the panes in tiptoe blows",
        tags={"office", "rain"},
    ),
    "cozy": OfficeMood(
        id="cozy",
        place="the broker's snug front room",
        sparkle="tiny key charms winked beside the door",
        sound="the heater hummed a sleepy little snore",
        tags={"office"},
    ),
}

CAUSES = {
    "breeze": Cause(
        id="breeze",
        trigger="a window breeze",
        motion="gave one sneaky flap and skated something by",
        source="the open window",
        tags={"air", "mystery"},
    ),
    "brochure": Cause(
        id="brochure",
        trigger="a brochure being lifted",
        motion="ruffled the paper stack with a whispering swish",
        source="a glossy brochure",
        tags={"paper", "mystery"},
    ),
    "folder": Cause(
        id="folder",
        trigger="a folder being closed",
        motion="pressed two papers snug with a papery click",
        source="a blue folder",
        tags={"paper", "mystery"},
    ),
}

HIDING_PLACES = {
    "behind_sign": HidingPlace(
        id="behind_sign",
        label="behind the welcome sign",
        phrase="behind the welcome sign on the easel",
        near="the bright easel",
        accept_causes={"breeze"},
        tags={"sign", "office"},
    ),
    "brochure_stack": HidingPlace(
        id="brochure_stack",
        label="inside the brochure stack",
        phrase="between two shiny house brochures",
        near="the neat brochure stack",
        accept_causes={"brochure"},
        tags={"brochure", "paper"},
    ),
    "folder_pocket": HidingPlace(
        id="folder_pocket",
        label="inside a folder pocket",
        phrase="in the clear pocket of a blue folder",
        near="the tall desk tray",
        accept_causes={"folder"},
        tags={"folder", "paper"},
    ),
}

CLUES = {
    "corner_peek": Clue(
        id="corner_peek",
        line='"I see a tiny white corner where it should not be."',
        points_to={"behind_sign"},
        tags={"look", "corner"},
    ),
    "glossy_edge": Clue(
        id="glossy_edge",
        line='"Something glossy is peeking from those brochures in a row."',
        points_to={"brochure_stack"},
        tags={"look", "brochure"},
    ),
    "blue_pocket": Clue(
        id="blue_pocket",
        line='"That blue folder looks puffed, as if it swallowed a square."',
        points_to={"folder_pocket"},
        tags={"look", "folder"},
    ),
}

METHODS = {
    "lift_sign": Method(
        id="lift_sign",
        sense=3,
        needs={"behind_sign"},
        action_text="gently lifted the sign from {place}",
        qa_text="lifted the sign carefully and found the photo behind it",
        tags={"careful", "search"},
    ),
    "separate_brochures": Method(
        id="separate_brochures",
        sense=3,
        needs={"brochure_stack"},
        action_text="carefully fanned apart the brochures at {place}",
        qa_text="fanned apart the brochures and slipped the photo free",
        tags={"careful", "search"},
    ),
    "open_folder": Method(
        id="open_folder",
        sense=3,
        needs={"folder_pocket"},
        action_text="opened the folder and slid two papers apart at {place}",
        qa_text="opened the folder pocket and slid the photo out",
        tags={"careful", "search"},
    ),
    "shake_room": Method(
        id="shake_room",
        sense=1,
        needs=set(),
        action_text="shook things all around {place}",
        qa_text="shook the room in a wild way",
        tags={"wild"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Ruby", "Nora", "Tessa", "Evie", "Poppy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Jude", "Noah"]
BROKER_NAMES = ["Mr. Reed", "Ms. Vale", "Mr. Stone", "Ms. Bell"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    mood: str
    cause: str
    hiding_place: str
    clue: str
    method: str
    child_name: str
    child_type: str
    parent_type: str
    broker_name: str
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
    "broker": [
        (
            "What does a broker do?",
            "A broker helps people with important choices, like finding a home or making a careful plan. A good broker pays attention to details and explains things clearly."
        )
    ],
    "photo": [
        (
            "What is a photo?",
            "A photo is a picture made with a camera that helps people remember a person, place, or moment. It can be kept on a wall, a desk, or in a folder."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a mystery. It points your thinking in the right direction instead of giving the whole answer at once."
        )
    ],
    "brochure": [
        (
            "What is a brochure?",
            "A brochure is a folded paper that shares information and pictures. People often use brochures to show homes, places, or plans."
        )
    ],
    "folder": [
        (
            "What is a folder pocket for?",
            "A folder pocket keeps papers together so they do not slide away. Thin things like notes or photos can slip into it if nobody notices."
        )
    ],
    "sign": [
        (
            "Why can paper slide behind a sign?",
            "A light piece of paper can move if air or another paper nudges it. Then it may hide flat behind something standing up."
        )
    ],
    "careful": [
        (
            "Why is it smart to search carefully?",
            "Searching carefully helps you notice small clues and keeps delicate things from getting bent. Calm looking is often faster than wild grabbing."
        )
    ],
}
KNOWLEDGE_ORDER = ["broker", "photo", "clue", "brochure", "folder", "sign", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cause = f["cause"]
    place = f["hiding_place"]
    child = f["child"]
    broker = f["broker"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "broker" and "photo", with a gentle mystery and a happy ending.',
        f"Tell a suspenseful but cozy rhyming story where {broker.label}, a broker, cannot find a photo, and {child.label} helps notice a clue.",
        f"Write a rhyming mystery where a missing photo is solved by following a small clue to {place.label}, after trouble begins with {cause.trigger}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    broker = f["broker"]
    cause = f["cause"]
    place = f["hiding_place"]
    clue = f["clue"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {child.pronoun('possessive')} {parent.title_word}, and {broker.label}, the broker. They were together in the broker's office when the mystery began."
        ),
        (
            "What was the mystery to solve?",
            "The mystery was that the photo for the welcome board had gone missing. Everyone could feel the quiet suspense because it had been there just a moment before."
        ),
        (
            f"Why did they start looking near {place.label}?",
            f"They followed a clue instead of guessing wildly. {clue.line.strip(chr(34))} That clue pointed them toward {place.label}."
        ),
        (
            "How was the mystery solved?",
            f"{broker.label} {method.qa_text}. The answer fit both the clue and the way the photo had slipped away, so the search ended happily."
        ),
        (
            "How do we know the ending was happy?",
            "The broker clipped the photo onto the board, and the office felt cheerful again. The child clapped because the missing piece was back where it belonged."
        ),
    ]
    if f.get("solved_truthfully"):
        qa.append(
            (
                "What caused the photo to go missing?",
                f"It went missing because of {cause.trigger}. That small change nudged the photo into a hiding place, which is why the clue mattered so much."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"broker", "photo", "clue", "careful"}
    place = world.facts["hiding_place"]
    if place.id == "brochure_stack":
        tags.add("brochure")
    if place.id == "folder_pocket":
        tags.add("folder")
    if place.id == "behind_sign":
        tags.add("sign")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    if world.facts:
        shown = {}
        for k, v in world.facts.items():
            if isinstance(v, (str, int, float, bool)):
                shown[k] = v
            elif hasattr(v, "id"):
                shown[k] = getattr(v, "id")
            elif isinstance(v, Entity):
                shown[k] = v.id
        lines.append(f"  facts: {shown}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mood="sunny",
        cause="breeze",
        hiding_place="behind_sign",
        clue="corner_peek",
        method="lift_sign",
        child_name="Lila",
        child_type="girl",
        parent_type="mother",
        broker_name="Mr. Reed",
    ),
    StoryParams(
        mood="rainy",
        cause="brochure",
        hiding_place="brochure_stack",
        clue="glossy_edge",
        method="separate_brochures",
        child_name="Milo",
        child_type="boy",
        parent_type="father",
        broker_name="Ms. Bell",
    ),
    StoryParams(
        mood="cozy",
        cause="folder",
        hiding_place="folder_pocket",
        clue="blue_pocket",
        method="open_folder",
        child_name="Ruby",
        child_type="girl",
        parent_type="mother",
        broker_name="Ms. Vale",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "solved"


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
valid(C,P,Cl,M) :- cause(C), hiding_place(P), clue(Cl), method(M),
                   accepts(P,C), points_to(Cl,P), needs(M,P), sensible_method(M).
outcome(solved) :- chosen_method(M), sensible_method(M).

#show valid/4.
#show sensible_method/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for place_id, place in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", place_id))
        for c in sorted(place.accept_causes):
            lines.append(asp.fact("accepts", place_id, c))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for p in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, p))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for p in sorted(method.needs):
            lines.append(asp.fact("needs", method_id, p))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra))
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

    clingo_methods = set(asp_sensible_methods())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(clingo_methods))
        print("  python:", sorted(python_methods))

    cases = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming mystery storyworld: a broker, a missing photo, a clue, and a happy ending."
    )
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--hiding_place", choices=sorted(HIDING_PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--child_type", choices=["girl", "boy"])
    ap.add_argument("--parent_type", choices=sorted(PARENT_TYPES))
    ap.add_argument("--child_name")
    ap.add_argument("--broker_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing method '{args.method}': it scores too low on common sense "
            f"(sense={METHODS[args.method].sense} < {SENSE_MIN}).)"
        )

    if args.cause and args.hiding_place and args.clue and args.method:
        cause = CAUSES[args.cause]
        place = HIDING_PLACES[args.hiding_place]
        clue = CLUES[args.clue]
        method = METHODS[args.method]
        if not combo_valid(cause, place, clue, method):
            raise StoryError(explain_rejection(cause, place, clue, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.hiding_place is None or combo[1] == args.hiding_place)
        and (args.clue is None or combo[2] == args.clue)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, place_id, clue_id, method_id = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    broker_name = args.broker_name or rng.choice(BROKER_NAMES)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)

    return StoryParams(
        mood=mood,
        cause=cause_id,
        hiding_place=place_id,
        clue=clue_id,
        method=method_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        broker_name=broker_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mood = MOODS[params.mood]
        cause = CAUSES[params.cause]
        hiding_place = HIDING_PLACES[params.hiding_place]
        clue = CLUES[params.clue]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not combo_valid(cause, hiding_place, clue, method):
        raise StoryError(explain_rejection(cause, hiding_place, clue, method))

    world = tell(
        mood=mood,
        cause=cause,
        hiding_place=hiding_place,
        clue=clue,
        method=method,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        broker_name=params.broker_name,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (cause, hiding_place, clue, method) combos:\n")
        for cause, place, clue, method in combos:
            print(f"  {cause:8} {place:15} {clue:12} {method}")
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
                f"### {p.child_name}: {p.cause} -> {p.hiding_place} "
                f"with {p.clue}/{p.method}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
