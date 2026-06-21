#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py
============================================================================

A standalone story world for a tiny detective-story misunderstanding:
a child sees the clue-word "trim-gerund", notices that an -ing word card has
been shortened, and briefly invents a mysterious culprit named Trim-Gerund.
The world model tracks the physical board, the trimmed card, the scrap envelope,
and the children's shifting feelings as they investigate and learn what the
note really meant.

Run it
------
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py --card painting
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py --card kitten
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/trim_gerund_misunderstanding_detective_story.py --qa --json
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", self.type)
        female = {"girl", "woman", "female"}
        male = {"boy", "man", "male"}
        if gender in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    display: str
    event: str
    mood: str
    staff: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
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
class WordCard:
    id: str
    full_word: str
    base_word: str
    tail: str
    material: str
    editable: bool
    clue_line: str
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
class Helper:
    id: str
    label: str
    type: str
    gender: str
    role_line: str
    explain_line: str
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
    asks_adult: bool
    finds_envelope: bool
    compares_list: bool
    opening: str
    discovery: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_mystery(world: World) -> list[str]:
    card = world.get("card")
    note = world.get("note")
    detective = world.get("detective")
    room = world.get("room")
    if card.meters["trimmed"] >= THRESHOLD and note.meters["visible"] >= THRESHOLD:
        sig = ("mystery", card.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["confusion"] += 1
            detective.memes["suspicion"] += 1
            room.meters["mystery"] += 1
            return ["__mystery__"]
    return []


def _r_evidence(world: World) -> list[str]:
    envelope = world.get("envelope")
    detective = world.get("detective")
    buddy = world.get("buddy")
    if envelope.meters["found"] >= THRESHOLD:
        sig = ("evidence", envelope.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["curiosity"] += 1
            buddy.memes["hope"] += 1
            return ["__evidence__"]
    return []


def _r_explanation(world: World) -> list[str]:
    helper = world.get("helper")
    detective = world.get("detective")
    buddy = world.get("buddy")
    room = world.get("room")
    if helper.memes["explained"] >= THRESHOLD:
        sig = ("explained", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["understanding"] += 1
            detective.memes["relief"] += 1
            detective.memes["suspicion"] = 0.0
            detective.memes["confusion"] = 0.0
            buddy.memes["relief"] += 1
            room.meters["mystery"] = 0.0
            return ["__solved__"]
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="evidence", tag="physical", apply=_r_evidence),
    Rule(name="explanation", tag="social", apply=_r_explanation),
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


def is_valid_card(card: WordCard) -> bool:
    return card.editable and card.tail == "ing"


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    sensible = {m.id for m in sensible_methods()}
    for place_id, setting in SETTINGS.items():
        for card_id, card in WORD_CARDS.items():
            if not is_valid_card(card):
                continue
            for helper_id in setting.staff:
                for method_id in setting.methods:
                    if method_id in sensible and helper_id in HELPERS:
                        combos.append((place_id, card_id, helper_id, method_id))
    return combos


def explain_rejection(card: WordCard) -> str:
    if not card.editable:
        return (
            f"(No story: '{card.full_word}' is not the kind of classroom word the note "
            f"'trim-gerund' would apply to. The misunderstanding only works when the card "
            f"is an -ing action word that can honestly be trimmed.)"
        )
    if card.tail != "ing":
        return (
            f"(No story: '{card.full_word}' does not end with 'ing', so a trim-gerund note "
            f"would not match what is on the board.)"
        )
    return "(No story: this card does not fit the misunderstanding.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A detective should look for evidence "
        f"or ask a grown-up before blaming someone. Try: {better}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if method.asks_adult:
        return "cleared_fast"
    if method.finds_envelope or method.compares_list:
        return "cleared_after_search"
    return "unclear"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("card").meters["trimmed"] += 1
    sim.get("note").meters["visible"] += 1
    propagate(sim, narrate=False)
    detective = sim.get("detective")
    return {
        "mystery": sim.get("room").meters["mystery"],
        "suspicion": detective.memes["suspicion"],
        "confusion": detective.memes["confusion"],
    }


def introduce(world: World, detective: Entity, buddy: Entity, setting: Setting) -> None:
    detective.memes["eager"] += 1
    buddy.memes["calm"] += 1
    world.say(
        f"On a bright school morning, {detective.id} marched into {setting.place} "
        f"with {buddy.id} at {detective.pronoun('possessive')} side. {detective.id} "
        f"loved detective stories, and {setting.display} already looked like the start "
        f"of a very fine case."
    )
    world.say(
        f"They were helping with {setting.event}. {setting.mood}"
    )


def show_board(world: World, detective: Entity, buddy: Entity, card: WordCard, helper: Entity) -> None:
    world.say(
        f"Across the board, neat paper cards were lined up in {card.material}. "
        f"One card should have said {card.full_word!r}, but now it only said {card.base_word!r}."
    )
    world.say(
        f"Above it, {helper.label_word.capitalize()} had left a tiny note in pencil: "
        f'"trim-gerund."'
    )


def misread_clue(world: World, detective: Entity, buddy: Entity, card: WordCard) -> None:
    world.get("card").meters["trimmed"] += 1
    world.get("note").meters["visible"] += 1
    propagate(world, narrate=False)
    pred = predict_misunderstanding(world)
    world.facts["predicted_mystery"] = pred["mystery"]
    world.facts["predicted_confusion"] = pred["confusion"]
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes. "
        f'"A clue," {detective.pronoun()} whispered. "Someone named Trim-Gerund '
        f'trimmed the card!"'
    )
    if buddy.memes["calm"] >= THRESHOLD:
        world.say(
            f'{buddy.id} tilted {buddy.pronoun("possessive")} head. "Maybe," '
            f'{buddy.pronoun()} said, "but clues can mean more than one thing."'
        )


def choose_method(world: World, detective: Entity, buddy: Entity, method: Method) -> None:
    detective.memes["determined"] += 1
    world.say(method.opening)
    if method.id == "follow_scraps":
        world.say(
            f"{detective.id} crouched low and spotted a few curly paper bits under the board."
        )
    elif method.id == "compare_list":
        world.say(
            f"{buddy.id} opened the planning sheet and ran a finger down the list of words."
        )
    elif method.id == "ask_helper":
        world.say(
            f"{buddy.id} gave the note one more careful look before they went to find a grown-up."
        )


def find_evidence(world: World, detective: Entity, buddy: Entity, card: WordCard, method: Method) -> None:
    envelope = world.get("envelope")
    if method.finds_envelope:
        envelope.meters["found"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{method.discovery} Inside was a neat little pile of paper tails, each one cut with "
            f"the letters {card.tail!r} on it."
        )
    elif method.compares_list:
        envelope.meters["found"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{method.discovery} The list showed both versions of the word: {card.full_word!r} "
            f"first, and then the shorter {card.base_word!r} with a check mark beside it."
        )


def explain(world: World, helper: Entity, detective: Entity, buddy: Entity, card: WordCard, method: Method) -> None:
    helper.memes["explained"] += 1
    propagate(world, narrate=False)
    extra = ""
    if method.finds_envelope or method.compares_list:
        extra = " When the children showed the paper bits and the list, the whole puzzle clicked into place."
    world.say(
        f"{helper.label_word.capitalize()} smiled instead of gasping. "
        f'"No thief at all," {helper.pronoun()} said. "{helper.attrs["explain_line"]} '
        f'I was trimming the gerund ending so the board would fit the title."{extra}'
    )
    world.say(
        f"{detective.id} blinked, then laughed a little. Trim-Gerund was not a sneaky villain. "
        f"It was just a work note about the word {card.full_word!r}."
    )


def restore(world: World, detective: Entity, buddy: Entity, helper: Entity, card: WordCard, setting: Setting) -> None:
    detective.memes["pride"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"Together they tucked the little {card.tail} tail into the scrap envelope, straightened the board, "
        f"and pinned up the shorter card exactly where it belonged."
    )
    world.say(
        f"By the time {setting.event} began, {setting.display} looked tidy and bright. "
        f"{detective.id} still felt like a detective, but now {detective.pronoun()} knew that the best detectives "
        f"check what words mean before they accuse a mystery shadow."
    )
def tell(
    card_cfg: Card,
    helper_cfg: Helper,
    method: Method,
    detective_name: str,
    detective_gender: str,
    buddy_name: str,
    buddy_gender: str,
    setting=None,
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        attrs={"gender": detective_gender},
        traits=["curious", "dramatic"],
        tags={"detective"},
    ))
    buddy = world.add(Entity(
        id=buddy_name,
        kind="character",
        type=buddy_gender,
        role="buddy",
        attrs={"gender": buddy_gender},
        traits=["steady", "careful"],
        tags={"helper_friend"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="adult",
        label=helper_cfg.label,
        attrs={"gender": helper_cfg.gender, "explain_line": helper_cfg.explain_line},
        tags=set(helper_cfg.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=setting.place,
        tags=set(setting.tags),
    ))
    card = world.add(Entity(
        id="card",
        kind="thing",
        type="word_card",
        label=card_cfg.full_word,
        attrs={
            "full_word": card_cfg.full_word,
            "base_word": card_cfg.base_word,
            "tail": card_cfg.tail,
            "material": card_cfg.material,
        },
        tags=set(card_cfg.tags),
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="trim-gerund",
        attrs={"text": "trim-gerund"},
        tags={"note", "clue"},
    ))
    envelope = world.add(Entity(
        id="envelope",
        kind="thing",
        type="envelope",
        label="scrap envelope",
        attrs={"contains": f"{card_cfg.tail} tails"},
        tags={"envelope", "paper"},
    ))

    world.facts.update(
        setting=setting,
        card_cfg=card_cfg,
        helper_cfg=helper_cfg,
        method=method,
        detective=detective,
        buddy=buddy,
        helper=helper,
        note_word="trim-gerund",
        evidence_found=False,
        outcome="",
    )

    introduce(world, detective, buddy, setting)
    show_board(world, detective, buddy, card_cfg, helper)
    world.para()
    misread_clue(world, detective, buddy, card_cfg)
    choose_method(world, detective, buddy, method)

    if method.finds_envelope or method.compares_list:
        find_evidence(world, detective, buddy, card_cfg, method)
        world.facts["evidence_found"] = True

    world.para()
    explain(world, helper, detective, buddy, card_cfg, method)
    world.para()
    restore(world, detective, buddy, helper, card_cfg, setting)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            place=setting.id,
            card=card_cfg.id,
            helper=helper_cfg.id,
            method=method.id,
            detective=detective_name,
            detective_gender=detective_gender,
            buddy=buddy_name,
            buddy_gender=buddy_gender,
            seed=None,
        )
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        display="the grammar board by the window",
        event="Word Day",
        mood="Sunlight made the tape and paper gleam like real clues.",
        staff=["teacher"],
        methods=["ask_helper", "compare_list"],
        tags={"classroom"},
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        display="the reading display near the beanbags",
        event="Reading Week",
        mood="The shelves stood tall and quiet, as if they were guarding secrets.",
        staff=["librarian"],
        methods=["ask_helper", "follow_scraps"],
        tags={"library"},
    ),
    "art_room": Setting(
        id="art_room",
        place="the art room",
        display="the wall of word posters by the paint sink",
        event="Family Open House",
        mood="Tiny flecks of paper shone on the floor like detective dust.",
        staff=["art_aide"],
        methods=["follow_scraps", "ask_helper"],
        tags={"art_room"},
    ),
}

WORD_CARDS = {
    "running": WordCard(
        id="running",
        full_word="running",
        base_word="run",
        tail="ing",
        material="blue card",
        editable=True,
        clue_line="The long word had to shrink to fit.",
        tags={"gerund", "running"},
    ),
    "painting": WordCard(
        id="painting",
        full_word="painting",
        base_word="paint",
        tail="ing",
        material="gold card",
        editable=True,
        clue_line="The title was too crowded.",
        tags={"gerund", "painting"},
    ),
    "hopping": WordCard(
        id="hopping",
        full_word="hopping",
        base_word="hop",
        tail="ing",
        material="green card",
        editable=True,
        clue_line="The word needed one neat trim.",
        tags={"gerund", "hopping"},
    ),
    "kitten": WordCard(
        id="kitten",
        full_word="kitten",
        base_word="kitten",
        tail="",
        material="pink card",
        editable=False,
        clue_line="A noun card does not have a gerund ending.",
        tags={"noun", "kitten"},
    ),
    "picnic": WordCard(
        id="picnic",
        full_word="picnic",
        base_word="picnic",
        tail="",
        material="orange card",
        editable=False,
        clue_line="A picnic card would not be trimmed as a gerund.",
        tags={"noun", "picnic"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        label="the teacher",
        type="woman",
        gender="female",
        role_line="She had been arranging the board before the bell.",
        explain_line="That note was for me",
        tags={"teacher"},
    ),
    "librarian": Helper(
        id="librarian",
        label="the librarian",
        type="man",
        gender="male",
        role_line="He had been labeling the display for Reading Week.",
        explain_line="That note was my reminder",
        tags={"librarian"},
    ),
    "art_aide": Helper(
        id="art_aide",
        label="the art aide",
        type="woman",
        gender="female",
        role_line="She had been trimming posters with careful little scissors.",
        explain_line="That note was taped there to help me remember the last step",
        tags={"art"},
    ),
}

METHODS = {
    "ask_helper": Method(
        id="ask_helper",
        sense=3,
        asks_adult=True,
        finds_envelope=False,
        compares_list=False,
        opening="Instead of shouting for suspects, the two young detectives decided to ask the grown-up who had been working at the board.",
        discovery="",
        qa_text="They asked the grown-up who made the note before blaming anyone.",
        tags={"ask", "clue"},
    ),
    "follow_scraps": Method(
        id="follow_scraps",
        sense=2,
        asks_adult=False,
        finds_envelope=True,
        compares_list=False,
        opening="They chose a quieter kind of detective work and followed the tiny scraps of paper like a trail.",
        discovery="The trail led to a small scrap envelope on the work table.",
        qa_text="They followed the little paper scraps until those scraps led them to the envelope of cut endings.",
        tags={"evidence", "paper"},
    ),
    "compare_list": Method(
        id="compare_list",
        sense=3,
        asks_adult=False,
        finds_envelope=False,
        compares_list=True,
        opening="They checked the planning list first, because good detectives compare a clue with the facts they already have.",
        discovery="Folded under the board clips was the planning sheet from that morning.",
        qa_text="They compared the board with the planning list and saw that the shorter word had been planned all along.",
        tags={"list", "evidence"},
    ),
    "blame_janitor": Method(
        id="blame_janitor",
        sense=1,
        asks_adult=False,
        finds_envelope=False,
        compares_list=False,
        opening="They decided to blame the janitor at once.",
        discovery="",
        qa_text="They blamed someone without checking first.",
        tags={"blame"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ella", "Ivy", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Leo", "Sam", "Eli", "Jack"]
@dataclass
class StoryParams:
    place: str
    card: str
    helper: str
    method: str
    detective: str
    detective_gender: str
    buddy: str
    buddy_gender: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="classroom",
        card="running",
        helper="teacher",
        method="ask_helper",
        detective="Nora",
        detective_gender="girl",
        buddy="Ben",
        buddy_gender="boy",
        seed=None,
    ),
    StoryParams(
        place="library",
        card="painting",
        helper="librarian",
        method="follow_scraps",
        detective="Theo",
        detective_gender="boy",
        buddy="Maya",
        buddy_gender="girl",
        seed=None,
    ),
    StoryParams(
        place="art_room",
        card="hopping",
        helper="art_aide",
        method="follow_scraps",
        detective="Ella",
        detective_gender="girl",
        buddy="Finn",
        buddy_gender="boy",
        seed=None,
    ),
    StoryParams(
        place="classroom",
        card="painting",
        helper="teacher",
        method="compare_list",
        detective="Max",
        detective_gender="boy",
        buddy="Ivy",
        buddy_gender="girl",
        seed=None,
    ),
]


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully at clues and asks good questions. A good detective checks the facts before deciding what happened."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small piece of information that helps you solve a puzzle. One clue alone can be confusing, so detectives look for more than one."
        )
    ],
    "gerund": [
        (
            "What is a gerund?",
            "A gerund is an action word ending in -ing, like running or painting, used as a naming word. In this story, the trim-gerund note meant someone was shortening that -ing ending on purpose."
        )
    ],
    "paper": [
        (
            "Why do paper scraps matter in a mystery?",
            "Paper scraps can show that something was cut or moved nearby. They help a detective follow what happened step by step."
        )
    ],
    "teacher": [
        (
            "Why is it smart to ask a teacher or other grown-up about a clue?",
            "A grown-up might know what the clue was for in the first place. Asking can stop a misunderstanding before it grows bigger."
        )
    ],
    "library": [
        (
            "Why is a library a good place to notice little clues?",
            "Libraries are often calm and quiet, so small details stand out. That makes it easier to spot notes, scraps, and missing things."
        )
    ],
    "art": [
        (
            "Why might an art room have paper scraps on the floor?",
            "People cut paper and trim posters in an art room all the time. The scraps are often leftovers from making something neat."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "gerund", "paper", "teacher", "library", "art"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    buddy = f["buddy"]
    setting = f["setting"]
    card = f["card_cfg"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the word "trim-gerund" and centers on a misunderstanding.',
        f"Tell a gentle school mystery where {detective.id} thinks a clue about {card.full_word!r} points to a villain, but the case is really about words and paper trimming in {setting.place}.",
        f"Write a child-friendly detective tale where {buddy.id} helps slow down a misunderstanding, and the ending shows how asking what a clue means can solve the mystery."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    buddy = f["buddy"]
    helper = f["helper"]
    setting = f["setting"]
    card = f["card_cfg"]
    method = f["method"]
    evidence_found = f["evidence_found"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who loves detective stories, and {buddy.id}, the friend who helps with the case. They are working in {setting.place} when the mystery begins."
        ),
        (
            "What made the mystery start?",
            f"The card that should have said {card.full_word!r} only said {card.base_word!r}, and a note above it said 'trim-gerund.' That made {detective.id} think someone named Trim-Gerund had snipped the word."
        ),
        (
            f"Why was that a misunderstanding?",
            f"It looked like a villain's name, but it was really an instruction about the word card. The note was about trimming the -ing ending, not about a thief at all."
        ),
        (
            f"How did {detective.id} investigate?",
            f"{method.qa_text} That choice helped move the case from guessing to real evidence."
        ),
    ]
    if evidence_found:
        qa.append(
            (
                "What evidence did they find?",
                f"They found proof that the cut part was only the little {card.tail!r} ending from the word. That showed the card had been shortened on purpose, not stolen by a secret crook."
            )
        )
    qa.append(
        (
            f"How was the case solved?",
            f"{helper.label_word.capitalize()} explained that the trim-gerund note was a work reminder about making the board fit. After that, the children understood the clue and the mystery disappeared."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They fixed the display together and got it ready for {setting.event}. The ending shows that {detective.id} still felt clever, but also wiser about checking what a clue really means."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"detective", "clue", "gerund"}
    method = f["method"]
    if method.finds_envelope:
        tags.add("paper")
    if method.asks_adult or f["helper_cfg"].id == "teacher":
        tags.add("teacher")
    tags |= set(f["setting"].tags)
    tags |= set(f["helper_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid_card(C) :- card(C), editable(C), tail(C, ing).
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(P, C, H, M) :- setting(P), valid_card(C), staff(P, H), place_method(P, M), sensible_method(M).

% --- outcome model ---------------------------------------------------------
outcome(cleared_fast) :- chosen_method(M), asks_adult(M).
outcome(cleared_after_search) :- chosen_method(M), not asks_adult(M), finds_envelope(M).
outcome(cleared_after_search) :- chosen_method(M), not asks_adult(M), compares_list(M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for helper_id in setting.staff:
            lines.append(asp.fact("staff", place_id, helper_id))
        for method_id in setting.methods:
            lines.append(asp.fact("place_method", place_id, method_id))
    for card_id, card in WORD_CARDS.items():
        lines.append(asp.fact("card", card_id))
        if card.editable:
            lines.append(asp.fact("editable", card_id))
        if card.tail:
            lines.append(asp.fact("tail", card_id, card.tail))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.asks_adult:
            lines.append(asp.fact("asks_adult", method_id))
        if method.finds_envelope:
            lines.append(asp.fact("finds_envelope", method_id))
        if method.compares_list:
            lines.append(asp.fact("compares_list", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
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

    clingo_methods = set(asp_sensible_methods())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_methods)} python={sorted(python_methods)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective, a clue word, and a misunderstanding. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--card", choices=WORD_CARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.card:
        card = WORD_CARDS[args.card]
        if not is_valid_card(card):
            raise StoryError(explain_rejection(card))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.place and args.helper and args.helper not in SETTINGS[args.place].staff:
        raise StoryError(f"(No story: {args.helper} does not normally run the display in {args.place}.)")
    if args.place and args.method and args.method not in SETTINGS[args.place].methods:
        raise StoryError(f"(No story: method '{args.method}' is not available in {args.place}.)")

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.card is None or combo[1] == args.card)
        and (args.helper is None or combo[2] == args.helper)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, card, helper, method = rng.choice(sorted(combos))
    detective, detective_gender = _pick_name(rng)
    buddy, buddy_gender = _pick_name(rng, avoid=detective)
    return StoryParams(
        place=place,
        card=card,
        helper=helper,
        method=method,
        detective=detective,
        detective_gender=detective_gender,
        buddy=buddy,
        buddy_gender=buddy_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.card not in WORD_CARDS:
        raise StoryError(f"(Unknown card: {params.card})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    setting = SETTINGS[params.place]
    card = WORD_CARDS[params.card]
    helper = HELPERS[params.helper]
    method = METHODS[params.method]

    if not is_valid_card(card):
        raise StoryError(explain_rejection(card))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if params.helper not in setting.staff:
        raise StoryError(f"(No story: {params.helper} does not belong in {params.place}.)")
    if params.method not in setting.methods:
        raise StoryError(f"(No story: method '{params.method}' is not available in {params.place}.)")

    world = tell(
        setting=setting,
        card_cfg=card,
        helper_cfg=helper,
        method=method,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        buddy_name=params.buddy,
        buddy_gender=params.buddy_gender,
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
        print(asp_program("", "#show valid/4.\n#show sensible_method/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = asp_sensible_methods()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (place, card, helper, method) combos:\n")
        for place, card, helper, method in combos:
            print(f"  {place:10} {card:10} {helper:10} {method}")
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
            header = f"### {p.detective} & {p.buddy}: {p.card} in {p.place} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
