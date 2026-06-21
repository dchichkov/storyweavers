#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py
=======================================================================

A standalone storyworld for a tiny detective-quest domain: a child detective
must recover a missing small object by reading clues, talking with a helper, and
measuring a hiding place in millimeters before choosing the right retrieval
method.

The stories are gentle detective tales with dialogue, a clear quest, a state-
driven middle turn, and an ending image that proves the case changed the room.

Run it
------
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/millimeter_quest_dialogue_detective_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    opening_scene: str
    quest_goal: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    material: str
    size_mm: int
    importance: str
    sound: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    opening_mm: int
    open_place: bool = False
    narrow_place: bool = False
    dust_clue: str = ""
    ending_image: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "setting": setting,
            "case_place": "",
            "case_tool": "",
            "gap_mm": 0,
            "fit_margin_mm": 0,
            "clue_seen": False,
            "found": False,
        }

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


def fits(item: MissingItem, place: HidingPlace) -> bool:
    return item.size_mm <= place.opening_mm


def choose_tool(item: MissingItem, place: HidingPlace) -> Optional[Tool]:
    if not fits(item, place):
        return None
    if place.open_place:
        return TOOLS["hand"]
    if place.narrow_place and item.material == "metal":
        return TOOLS["magnet_wand"]
    if place.narrow_place:
        return TOOLS["ruler_hook"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid in sorted(setting.affords):
            place = PLACES[pid]
            for iid, item in ITEMS.items():
                if choose_tool(item, place) is not None:
                    combos.append((sid, iid, pid))
    return combos


def explain_rejection(item: MissingItem, place: HidingPlace) -> str:
    if not fits(item, place):
        return (
            f"(No story: {item.phrase} is {item.size_mm} millimeters across, but "
            f"{place.phrase} is only {place.opening_mm} millimeters wide. "
            f"It would not honestly fit there, so there is no fair detective case.)"
        )
    return (
        f"(No story: {item.phrase} could fit in {place.phrase}, but there is no "
        f"reasonable way to retrieve it with the tools in this world.)"
    )


def _r_missing_worry(world: World) -> list[str]:
    detective = world.get("detective")
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD or detective.meters["noticed_missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["worry"] += 1
    detective.memes["resolve"] += 1
    return []


def _r_clue(world: World) -> list[str]:
    detective = world.get("detective")
    item = world.get("item")
    place_id = world.facts["case_place"]
    if not place_id:
        return []
    place_ent = world.get(place_id)
    if place_ent.meters["searched"] < THRESHOLD:
        return []
    if item.attrs.get("hidden_in") != place_id or item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("clue", place_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place_ent.meters["clue"] += 1
    detective.memes["hope"] += 1
    world.facts["clue_seen"] = True
    return []


def _r_recover(world: World) -> list[str]:
    detective = world.get("detective")
    helper = world.get("helper")
    item = world.get("item")
    place_id = world.facts["case_place"]
    tool_id = world.facts["case_tool"]
    if not place_id or not tool_id:
        return []
    place_ent = world.get(place_id)
    if place_ent.meters["reached"] < THRESHOLD:
        return []
    if item.attrs.get("hidden_in") != place_id or item.meters["hidden"] < THRESHOLD:
        return []
    item_cfg: MissingItem = world.facts["item_cfg"]
    place_cfg: HidingPlace = world.facts["place_cfg"]
    tool_cfg = choose_tool(item_cfg, place_cfg)
    if tool_cfg is None or tool_cfg.id != tool_id:
        return []
    sig = ("recover", place_id, tool_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["hidden"] = 0.0
    item.meters["found"] += 1
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.facts["found"] = True
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue", tag="physical", apply=_r_clue),
    Rule(name="recover", tag="physical", apply=_r_recover),
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
        for sent in produced:
            world.say(sent)
    return produced


def predict_case(item: MissingItem, place: HidingPlace) -> dict:
    tool = choose_tool(item, place)
    return {
        "fits": fits(item, place),
        "tool": tool.id if tool else "",
        "margin": place.opening_mm - item.size_mm,
    }


def introduce(world: World, detective: Entity, helper: Entity, item: MissingItem) -> None:
    setting = world.setting
    detective.memes["curiosity"] += 1
    helper.memes["attention"] += 1
    world.say(
        f"{setting.opening_scene} {detective.id} called {detective.pronoun('possessive')}self "
        f"the best little detective on the block, and {helper.id} was {detective.pronoun('possessive')} "
        f"faithful partner."
    )
    world.say(
        f"That day they had one cheerful quest: {item.importance}."
    )


def discover_loss(world: World, detective: Entity, helper: Entity, item_ent: Entity, item: MissingItem) -> None:
    detective.meters["noticed_missing"] += 1
    item_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {detective.id} patted {detective.pronoun('possessive')} pocket and froze. "
        f"{item.phrase.capitalize()} was gone."
    )
    world.say(
        f'"Detective {detective.id}, what is the case?" {helper.id} asked.'
    )
    world.say(
        f'"My {item.label} has vanished," {detective.id} said. '
        f'"We cannot finish {world.setting.quest_goal} without it."'
    )


def interview(world: World, detective: Entity, helper: Entity, place: HidingPlace) -> None:
    helper.memes["suspicion"] += 1
    if place.open_place:
        guess = f"something open, like {place.phrase}"
    else:
        guess = f"a low space, like {place.phrase}"
    world.say(
        f'"Think like detectives," {helper.id} said. "The last clue points to {guess}."'
    )
    world.say(
        f'"Then we follow the clue and ask the room to tell us the truth," {detective.id} said.'
    )


def inspect_place(world: World, detective: Entity, helper: Entity, place_ent: Entity,
                  item: MissingItem, place: HidingPlace) -> None:
    place_ent.meters["searched"] += 1
    propagate(world, narrate=False)
    margin = world.facts["fit_margin_mm"]
    if place.open_place:
        world.say(
            f"They hurried to {place.phrase}. {helper.id} knelt and pointed. "
            f'"Look at that little trail," {helper.pronoun()} whispered.'
        )
    else:
        world.say(
            f"They crouched beside {place.phrase}. {detective.id} laid a ruler flat on the floor "
            f"and read the tiny marks."
        )
        world.say(
            f'"{place.opening_mm} millimeters," {detective.id} whispered. '
            f'"Not even a spare millimeter to waste. If the {item.label} is only {item.size_mm} '
            f"millimeters across, it could slip in with {margin} millimeters left."
        )
    world.say(place.dust_clue)


def decide_method(world: World, detective: Entity, helper: Entity, item: MissingItem,
                  tool: Tool, place: HidingPlace) -> None:
    detective.attrs["tool"] = tool.id
    world.say(
        f'"So the hiding place is real," {helper.id} said. "How do we get it back?"'
    )
    if tool.id == "magnet_wand":
        world.say(
            f'"With {tool.phrase}," {detective.id} said. '
            f'"The {item.label} is {item.material}, so it should listen."'
        )
    elif tool.id == "ruler_hook":
        world.say(
            f'"With {tool.phrase}," {detective.id} said. '
            f'"It can slide into the narrow space and coax the {item.label} out."'
        )
    else:
        world.say(
            f'"With {tool.phrase}," {detective.id} said. '
            f'"This case is open enough for a careful hand."'
        )


def recover(world: World, detective: Entity, helper: Entity, place_ent: Entity,
            item: MissingItem, tool: Tool) -> None:
    place_ent.meters["reached"] += 1
    propagate(world, narrate=False)
    item_ent = world.get("item")
    if item_ent.meters["found"] < THRESHOLD:
        raise StoryError("The recovery step failed; the chosen tool did not solve the case.")
    helper_line = {
        "magnet_wand": f'"I see a flash!" {helper.id} cried.',
        "ruler_hook": f'"Easy now," {helper.id} murmured.',
        "hand": f'"There it is!" {helper.id} said.',
    }[tool.id]
    world.say(
        f"{detective.id} {tool.method}. {helper_line}"
    )
    world.say(
        f"A moment later, {item.phrase} slid back into the light."
    )


def celebrate(world: World, detective: Entity, helper: Entity, item: MissingItem,
              place: HidingPlace, tool: Tool) -> None:
    detective.memes["gratitude"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'"Case closed," {detective.id} said, smiling at {helper.id}. '
        f'"You saw the clue, and {tool.qa_text}."'
    )
    world.say(
        f"They finished {world.setting.quest_goal}, and {place.ending_image}"
    )
@dataclass
class StoryParams:
    setting: str
    item: str
    place: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
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


CURATED = [
    StoryParams(
        setting="playroom",
        item="marble",
        place="under_sofa",
        detective="Nora",
        detective_gender="girl",
        helper="Max",
        helper_gender="boy",
        seed=None,
    ),
    StoryParams(
        setting="hallway",
        item="bell",
        place="radiator_gap",
        detective="Ben",
        detective_gender="boy",
        helper="Lily",
        helper_gender="girl",
        seed=None,
    ),
    StoryParams(
        setting="reading_nook",
        item="badge",
        place="window_crack",
        detective="Mia",
        detective_gender="girl",
        helper="Theo",
        helper_gender="boy",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        item="badge",
        place="toy_chest",
        detective="Eli",
        detective_gender="boy",
        helper="Anna",
        helper_gender="girl",
        seed=None,
    ),
    StoryParams(
        setting="hallway",
        item="marble",
        place="boot_tray",
        detective="Ava",
        detective_gender="girl",
        helper="Finn",
        helper_gender="boy",
        seed=None,
    ),
]


KNOWLEDGE = {
    "millimeter": [
        (
            "What is a millimeter?",
            "A millimeter is a very tiny unit for measuring length. People use millimeters when something is small and they need to be exact.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some kinds of metal toward it. That is why it can help fetch a small metal thing from a narrow spot.",
        )
    ],
    "ruler": [
        (
            "Why do detectives measure things?",
            "Measuring helps detectives check whether an idea is really possible. A fair guess becomes a better clue when the sizes match.",
        )
    ],
    "marble": [
        (
            "Why can a marble roll away so easily?",
            "A marble is smooth and round, so even a little slope can make it roll. That is why marbles often slip into corners and under furniture.",
        )
    ],
    "bell": [
        (
            "Why is a small bell easy to notice?",
            "A small bell can shine in the light and make a tiny jingle when it moves. Those little clues can help someone find it.",
        )
    ],
    "badge": [
        (
            "What is a badge for?",
            "A badge is a small sign that shows a job, team, or special role. It can make a child feel proud because it stands for something important.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tests ideas. Good detectives do not just guess; they look for reasons.",
        )
    ],
}
KNOWLEDGE_ORDER = ["millimeter", "detective", "magnet", "ruler", "marble", "bell", "badge"]


def generation_prompts(world: World) -> list[str]:
    item: MissingItem = world.facts["item_cfg"]
    place: HidingPlace = world.facts["place_cfg"]
    detective: Entity = world.facts["detective"]
    helper: Entity = world.facts["helper"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "millimeter" and follows a quest to find a missing {item.label}.',
        f"Tell a gentle dialogue-rich mystery where {detective.id} and {helper.id} solve the case of a missing {item.label} by checking {place.phrase}.",
        f"Write a TinyStories-style detective quest in which a child measures a clue, chooses the right tool, and finds a missing object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective: Entity = world.facts["detective"]
    helper: Entity = world.facts["helper"]
    item: MissingItem = world.facts["item_cfg"]
    place: HidingPlace = world.facts["place_cfg"]
    tool: Tool = world.facts["tool_cfg"]
    gap = world.facts["gap_mm"]
    margin = world.facts["fit_margin_mm"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {helper.id}, the helper who stayed beside {detective.pronoun('object')} through the case. Together they went on a quest to recover the missing {item.label}.",
        ),
        (
            f"Why was the missing {item.label} important?",
            f"It mattered because they needed it {item.importance}. Losing it turned an ordinary game into a real detective case.",
        ),
        (
            f"How did {detective.id} know to inspect {place.phrase}?",
            f"They followed the clues and looked for the kind of place a small object could slip into or hide inside. The idea fit the case because {place.phrase} matched what they had been noticing.",
        ),
    ]
    if place.narrow_place:
        out.append(
            (
                "What did the millimeter measurement tell them?",
                f"The ruler showed that the gap was {gap} millimeters high, while the {item.label} was {item.size_mm} millimeters across. That left only {margin} millimeters, so the measurement proved the object could fit and made the clue feel real.",
            )
        )
    out.append(
        (
            f"How did they get the {item.label} back?",
            f"They used {tool.phrase}, and that worked because the hiding place and the object matched the method. {tool.qa_text[0].upper()}{tool.qa_text[1:]}.",
        )
    )
    out.append(
        (
            "How did the story end?",
            f"It ended happily with the missing {item.label} back in the light and the quest finished. The room stopped feeling mysterious because the clue had been explained.",
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item: MissingItem = world.facts["item_cfg"]
    tool: Tool = world.facts["tool_cfg"]
    tags = {"millimeter", "detective"}
    if tool.id == "magnet_wand":
        tags.add("magnet")
    if tool.id == "ruler_hook":
        tags.add("ruler")
    tags |= set(item.tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    facts_show = {
        "case_place": world.facts.get("case_place"),
        "case_tool": world.facts.get("case_tool"),
        "gap_mm": world.facts.get("gap_mm"),
        "fit_margin_mm": world.facts.get("fit_margin_mm"),
        "clue_seen": world.facts.get("clue_seen"),
        "found": world.facts.get("found"),
    }
    lines.append(f"  facts={facts_show}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(I,P) :- item(I), place(P), size_mm(I,S), opening_mm(P,O), S <= O.

chosen_tool(I,P,hand) :-
    fits(I,P), open_place(P).

chosen_tool(I,P,magnet_wand) :-
    fits(I,P), narrow_place(P), material(I,metal), not open_place(P).

chosen_tool(I,P,ruler_hook) :-
    fits(I,P), narrow_place(P), not material(I,metal), not open_place(P).

valid(S,I,P) :-
    setting(S), affords(S,P), fits(I,P), chosen_tool(I,P,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for pid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("size_mm", iid, item.size_mm))
        lines.append(asp.fact("material", iid, item.material))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("opening_mm", pid, place.opening_mm))
        if place.open_place:
            lines.append(asp.fact("open_place", pid))
        if place.narrow_place:
            lines.append(asp.fact("narrow_place", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_tool_for(item_id: str, place_id: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("query_item", item_id),
        asp.fact("query_place", place_id),
    ])
    show = """
chosen_query(T) :- query_item(I), query_place(P), chosen_tool(I,P,T).
#show chosen_query/1.
"""
    model = asp.one_model(asp_program(extra, show))
    atoms = asp.atoms(model, "chosen_query")
    return atoms[0][0] if atoms else ""


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos() matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    tool_mismatches: list[tuple[str, str, str, str]] = []
    for iid, item in ITEMS.items():
        for pid, place in PLACES.items():
            py_tool = choose_tool(item, place)
            py_tool_id = py_tool.id if py_tool else ""
            asp_tool_id = asp_tool_for(iid, pid)
            if py_tool_id != asp_tool_id:
                tool_mismatches.append((iid, pid, py_tool_id, asp_tool_id))
    if not tool_mismatches:
        print("OK: tool selection matches ASP.")
    else:
        rc = 1
        print("MISMATCH in tool selection:")
        for row in tool_mismatches:
            print(" ", row)

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed at seed {seed}: {err}")
            continue
        smoke_cases.append(params)

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated story was empty.")
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise StoryError("Generated sample was missing QA or prompts.")
        print(f"OK: smoke-tested generation on {len(smoke_cases)} scenarios.")
    except Exception as err:
        rc = 1
        print(f"SMOKE generation failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective-quest storyworld with dialogue and millimeter clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    if not choices:
        raise StoryError("No available names for the requested genders.")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.place:
        item = ITEMS[args.item]
        place = PLACES[args.place]
        if choose_tool(item, place) is None:
            raise StoryError(explain_rejection(item, place))
    if args.setting and args.place and args.place not in SETTINGS[args.setting].affords:
        raise StoryError(
            f"(No story: {PLACES[args.place].phrase} does not belong in {SETTINGS[args.setting].label} in this world.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, place_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective or pick_name(rng, detective_gender)
    helper_name = args.helper or pick_name(rng, helper_gender, avoid=detective_name)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        place=place_id,
        detective=detective_name,
        detective_gender=detective_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.place not in SETTINGS[params.setting].affords:
        raise StoryError(
            f"{PLACES[params.place].phrase} is not available in {SETTINGS[params.setting].label}."
        )

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    place = PLACES[params.place]
    if choose_tool(item, place) is None:
        raise StoryError(explain_rejection(item, place))

    world = tell(
        setting=setting,
        item=item,
        place=place,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/3.\n#show chosen_tool/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid detective cases:\n")
        for setting_id, item_id, place_id in combos:
            tool_id = choose_tool(ITEMS[item_id], PLACES[place_id]).id
            print(f"  {setting_id:12} {item_id:8} {place_id:14} tool={tool_id}")
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
            tool = choose_tool(ITEMS[p.item], PLACES[p.place])
            header = f"### {p.detective} & {p.helper}: {p.item} at {p.place} ({p.setting}, {tool.id})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(setting: Setting, item: MissingItem, place: HidingPlace,
         detective_name: str = "Nora", detective_gender: str = "girl",
         helper_name: str = "Max", helper_gender: str = "boy") -> World:
    tool = choose_tool(item, place)
    if tool is None:
        raise StoryError(explain_rejection(item, place))

    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["careful", "curious"],
        attrs={},
        tags={"detective"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["bright", "loyal"],
        attrs={},
        tags={"helper"},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="object",
        label=item.label,
        role="missing_item",
        attrs={"hidden_in": place.id},
        tags=set(item.tags),
    ))
    place_ent = world.add(Entity(
        id=place.id,
        kind="thing",
        type="place",
        label=place.label,
        role="hiding_place",
        attrs={},
        tags=set(place.tags),
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        item_cfg=item,
        place_cfg=place,
        tool_cfg=tool,
        case_place=place.id,
        case_tool=tool.id,
        gap_mm=place.opening_mm,
        fit_margin_mm=place.opening_mm - item.size_mm,
    )

    introduce(world, detective, helper, item)
    discover_loss(world, detective, helper, item_ent, item)

    world.para()
    interview(world, detective, helper, place)
    inspect_place(world, detective, helper, place_ent, item, place)
    decide_method(world, detective, helper, item, tool, place)

    world.para()
    recover(world, detective, helper, place_ent, item, tool)
    celebrate(world, detective, helper, item, place, tool)

    return world


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        label="the playroom",
        opening_scene="In the playroom, under a lamp shaped like a moon,",
        quest_goal="their hallway-to-castle treasure quest before snack time",
        affords={"under_sofa", "toy_chest"},
        tags={"indoor", "quest"},
    ),
    "hallway": Setting(
        id="hallway",
        label="the hallway",
        opening_scene="In the hallway, while rain tapped at the door,",
        quest_goal="their mission to leave with every lucky thing they needed",
        affords={"radiator_gap", "boot_tray"},
        tags={"home", "quest"},
    ),
    "reading_nook": Setting(
        id="reading_nook",
        label="the reading nook",
        opening_scene="In the reading nook, beside a basket of blankets,",
        quest_goal="their secret detective-book quest before the library clock chimed",
        affords={"window_crack", "book_basket"},
        tags={"books", "quest"},
    ),
}

ITEMS = {
    "marble": MissingItem(
        id="marble",
        label="blue marble",
        phrase="a blue marble",
        material="glass",
        size_mm=14,
        importance="to carry a lucky clue-token to the end of the game",
        sound="clicked softly",
        tags={"marble", "small_object"},
    ),
    "bell": MissingItem(
        id="bell",
        label="brass bell",
        phrase="a brass bell",
        material="metal",
        size_mm=18,
        importance="to ring the last signal at the end of the quest",
        sound="gave a tiny jingle",
        tags={"bell", "metal"},
    ),
    "badge": MissingItem(
        id="badge",
        label="silver badge",
        phrase="a silver badge",
        material="metal",
        size_mm=12,
        importance="to pin the detective title on the winner",
        sound="tapped like a coin",
        tags={"badge", "metal"},
    ),
}

PLACES = {
    "under_sofa": HidingPlace(
        id="under_sofa",
        label="sofa gap",
        phrase="the gap under the sofa",
        opening_mm=20,
        open_place=False,
        narrow_place=True,
        dust_clue="A bright dot winked back through the dust bunnies, and beside it lay a tiny curved line where something had rolled.",
        ending_image="the blue rug no longer looked suspicious, only cozy again.",
        tags={"sofa", "gap"},
    ),
    "toy_chest": HidingPlace(
        id="toy_chest",
        label="toy chest corner",
        phrase="the toy chest corner",
        opening_mm=200,
        open_place=True,
        narrow_place=False,
        dust_clue="At the bottom, under capes and blocks, a little shine peeked out as if it were waiting to be discovered.",
        ending_image="the toy chest stood open like a witness that had finally told the truth.",
        tags={"toy_chest", "open_place"},
    ),
    "radiator_gap": HidingPlace(
        id="radiator_gap",
        label="radiator gap",
        phrase="the narrow gap beside the radiator",
        opening_mm=19,
        open_place=False,
        narrow_place=True,
        dust_clue="On the floor sat a fresh crescent in the dust, and deep inside the dark space something gave the faintest glint.",
        ending_image="the warm radiator hummed, but it no longer seemed to be hiding secrets.",
        tags={"radiator", "gap"},
    ),
    "boot_tray": HidingPlace(
        id="boot_tray",
        label="boot tray",
        phrase="the boot tray by the door",
        opening_mm=180,
        open_place=True,
        narrow_place=False,
        dust_clue="Between two damp boots rested a small bright shape, half-hidden under a curled scarf.",
        ending_image="the boot tray looked messy, but the case was neat at last.",
        tags={"boots", "open_place"},
    ),
    "window_crack": HidingPlace(
        id="window_crack",
        label="window-seat crack",
        phrase="the crack beside the window seat",
        opening_mm=15,
        open_place=False,
        narrow_place=True,
        dust_clue="A silver sparkle slept in the shadow, and the cloth on the seat showed the tiny path where it had slipped away.",
        ending_image="sunlight crossed the window seat, and every corner suddenly looked honest.",
        tags={"window_seat", "gap"},
    ),
    "book_basket": HidingPlace(
        id="book_basket",
        label="book basket",
        phrase="the book basket",
        opening_mm=170,
        open_place=True,
        narrow_place=False,
        dust_clue="A flash of color gleamed between two fat picture books, as if the basket had been saving the answer.",
        ending_image="the blanket basket looked soft and ordinary again, not mysterious at all.",
        tags={"books", "open_place"},
    ),
}

TOOLS = {
    "magnet_wand": Tool(
        id="magnet_wand",
        label="magnet wand",
        phrase="the magnet wand",
        method="slid the magnet wand into the gap and drew it back slowly",
        qa_text="the magnet wand reached into the narrow place and pulled the metal clue home",
        tags={"magnet"},
    ),
    "ruler_hook": Tool(
        id="ruler_hook",
        label="ruler hook",
        phrase="the bent ruler hook",
        method="eased the bent ruler hook into the gap and nudged with patient little movements",
        qa_text="the ruler hook slipped into the narrow place and nudged the object out",
        tags={"ruler"},
    ),
    "hand": Tool(
        id="hand",
        label="careful hand",
        phrase="a careful hand",
        method="reached in with a careful hand and lifted the answer free",
        qa_text="a careful hand simply picked the object up from the open place",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Max", "Ben", "Leo", "Theo", "Finn", "Sam", "Jack", "Eli"]

if __name__ == "__main__":
    main()
