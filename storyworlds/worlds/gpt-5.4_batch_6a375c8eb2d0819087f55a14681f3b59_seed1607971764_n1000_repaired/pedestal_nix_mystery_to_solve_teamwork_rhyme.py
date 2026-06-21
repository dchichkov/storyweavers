#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py
============================================================================

A small whodunit-style storyworld about a missing display object, a tidy little
mystery, and two children who solve it by working together.

The world is built around a few grounded constraints:

- A display object sits on a pedestal.
- A gentle "culprit" can only take objects that fit its habits and strength.
- Each culprit leaves a physical trace and is tied to one plausible hiding place.
- The final clue is a rhyme that only points honestly to that hiding place.
- The mystery is fully solved only when the team has both needed abilities:
  someone to read the rhyme pattern and someone to notice the trace.

This keeps the stories from becoming random noun swaps. The children really do
inspect the scene, rule out guesses, combine clues, and find what happened.

Run it
------
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/pedestal_nix_mystery_to_solve_teamwork_rhyme.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "librarian": "librarian",
            "caretaker": "caretaker",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
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
class Setting:
    id: str
    place: str
    host_type: str
    host_label: str
    intro: str
    audience: str
    affordances: set[str] = field(default_factory=set)
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
class Display:
    id: str
    label: str
    phrase: str
    shine: bool
    shape: str
    sound: str
    weight: int
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
class Culprit:
    id: str
    label: str
    kind: str
    preference: set[str]
    max_weight: int
    trace: str
    trace_noun: str
    motion: str
    hide_place: str
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
    rhyme_key: str
    rhyme_text: str
    found_text: str
    setting_ids: set[str] = field(default_factory=set)
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
class Skill:
    id: str
    label: str
    helps_with: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    display: str
    culprit: str
    sleuth1: str
    sleuth1_gender: str
    sleuth1_skill: str
    sleuth2: str
    sleuth2_gender: str
    sleuth2_skill: str
    host: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World + causal rules
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"sleuth1", "sleuth2"}]


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


def _r_missing_stirs_mystery(world: World) -> list[str]:
    obj = world.get("display")
    if obj.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", "display")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["curiosity"] += 1
        kid.memes["suspicion"] += 1
    world.get("room").memes["mystery"] += 1
    return ["__mystery__"]


def _r_trace_supports_suspect(world: World) -> list[str]:
    if not world.facts.get("trace_found"):
        return []
    sig = ("trace", world.facts.get("culprit_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["confidence"] += 1
    return []


def _r_teamwork_solves(world: World) -> list[str]:
    if not world.facts.get("trace_found"):
        return []
    if not world.facts.get("rhyme_read"):
        return []
    sig = ("solve", "team")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["solved"] = True
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    world.get("room").memes["mystery"] = 0.0
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs_mystery", tag="emotion", apply=_r_missing_stirs_mystery),
    Rule(name="trace_supports_suspect", tag="reasoning", apply=_r_trace_supports_suspect),
    Rule(name="teamwork_solves", tag="reasoning", apply=_r_teamwork_solves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def display_tags(display: Display) -> set[str]:
    tags = set(display.tags)
    if display.shine:
        tags.add("shiny")
    if display.sound == "jingle":
        tags.add("jangly")
    if display.shape == "nut":
        tags.add("nut")
    if display.shape == "round":
        tags.add("round")
    return tags


def culprit_can_take(display: Display, culprit: Culprit) -> bool:
    return display.weight <= culprit.max_weight and bool(display_tags(display) & culprit.preference)


def place_fits(setting_id: str, culprit: Culprit) -> bool:
    return setting_id in HIDING_PLACES[culprit.hide_place].setting_ids


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for display_id, display in DISPLAYS.items():
            for culprit_id, culprit in CULPRITS.items():
                if culprit_can_take(display, culprit) and place_fits(setting_id, culprit):
                    combos.append((setting_id, display_id, culprit_id))
    return sorted(combos)


def team_has_needed_skills(skill1: str, skill2: str) -> bool:
    helps = set(SKILLS[skill1].helps_with) | set(SKILLS[skill2].helps_with)
    return "trace" in helps and "rhyme" in helps


def valid_skill_pairs() -> list[tuple[str, str]]:
    pairs = []
    for s1 in SKILLS:
        for s2 in SKILLS:
            if team_has_needed_skills(s1, s2):
                pairs.append((s1, s2))
    return sorted(pairs)


def explain_combo_rejection(setting: Setting, display: Display, culprit: Culprit) -> str:
    if not culprit_can_take(display, culprit):
        return (
            f"(No story: {culprit.label} would not plausibly take {display.phrase}. "
            f"The object is either too heavy or not the kind of thing {culprit.pronoun()} goes for.)"
        )
    if not place_fits(setting.id, culprit):
        place = HIDING_PLACES[culprit.hide_place].phrase
        return (
            f"(No story: {culprit.label} would hide the object in {place}, "
            f"but that hiding place does not belong in {setting.place}.)"
        )
    return "(No story: this combination does not make a grounded mystery.)"


def explain_skill_rejection(skill1: str, skill2: str) -> str:
    return (
        f"(No story: {SKILLS[skill1].label} and {SKILLS[skill2].label} do not cover both "
        f"the trace clue and the rhyme clue. This world needs teamwork that can inspect and decode.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "solved" if team_has_needed_skills(params.sleuth1_skill, params.sleuth2_skill) else "guided"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, a: Entity, b: Entity, host: Entity, display: Display) -> None:
    world.say(
        f"{world.setting.intro} In the middle of it all, {display.phrase} stood on a small pedestal "
        f"so everyone could admire it."
    )
    world.say(
        f"{a.id} and {b.id} were helping {host.label_word} welcome {world.setting.audience}. "
        f"They liked feeling like tiny detectives on a very important day."
    )


def show_object(world: World, display: Display, host: Entity) -> None:
    extra = " It gave a small cheerful ring when the room grew quiet." if display.sound == "jingle" else ""
    world.say(
        f'"Please keep your eyes on the prize," {host.label_word} said with a smile.{extra}'
    )


def vanish(world: World, a: Entity, b: Entity, culprit: Culprit) -> None:
    obj = world.get("display")
    obj.meters["missing"] = 1.0
    world.facts["trace_found"] = False
    world.facts["rhyme_read"] = False
    propagate(world, narrate=False)
    world.say(
        f"But when the next group turned to look, the top of the pedestal was empty."
    )
    world.say(
        f'"Who took it?" whispered {a.id}. "{b.id}, this is a real mystery."'
    )
    world.say(
        f'{b.id} looked around at the floor and said, "First, let\'s nix the wild guesses and look for clues."'
    )
    world.facts["first_suspect"] = culprit.label


def inspect_trace(world: World, actor: Entity, culprit: Culprit, hiding: HidingPlace) -> None:
    world.facts["trace_found"] = True
    world.facts["trace_reader"] = actor.id
    propagate(world, narrate=False)
    world.say(
        f"{actor.id} crouched near the pedestal and spotted {culprit.trace}. "
        f'"That is not a person clue," {actor.pronoun()} said. "It points to {culprit.label}."'
    )
    world.say(
        f"The tiny sign beside the empty place had been bumped sideways, and on its back was a rhyme:"
    )
    world.say(f'"{hiding.rhyme_text}"')


def read_rhyme(world: World, actor: Entity, hiding: HidingPlace) -> None:
    world.facts["rhyme_read"] = True
    world.facts["rhyme_reader"] = actor.id
    propagate(world, narrate=False)
    world.say(
        f'{actor.id} tapped the last word and grinned. "{hiding.rhyme_key.capitalize()} tells us where to look," '
        f'{actor.pronoun()} said. "The clue is pointing straight at {hiding.phrase}."'
    )


def find_object(world: World, a: Entity, b: Entity, display: Display, culprit: Culprit, hiding: HidingPlace) -> None:
    obj = world.get("display")
    obj.meters["missing"] = 0.0
    obj.meters["found"] = 1.0
    world.facts["found_place"] = hiding.label
    world.facts["culprit_label"] = culprit.label
    world.say(
        f"Together they hurried to {hiding.phrase}. {hiding.found_text}"
    )
    world.say(
        f"There was {display.phrase}, safe and still, while {culprit.label} looked up with innocent, surprised eyes."
    )
    world.say(
        f'"So that was the whole whodunit," said {a.id}. "{culprit.label} was not being mean. '
        f'{culprit.pronoun().capitalize()} just carried it off {culprit.motion}."'
    )


def restore(world: World, host: Entity, a: Entity, b: Entity, display: Display) -> None:
    for kid in world.kids():
        kid.memes["pride"] += 1
    world.say(
        f"{host.label_word.capitalize()} laughed softly with relief and set {display.phrase} back on the pedestal."
    )
    world.say(
        f'"You solved it together," {host.pronoun()} said. "One of you found the trace, and one of you cracked the rhyme."'
    )
    world.say(
        f"{a.id} and {b.id} stood a little taller. The mystery was over, the room felt bright again, "
        f"and now everyone knew the best clues are easier to catch with four eyes and two good minds."
    )


def guided_end(world: World, host: Entity, a: Entity, b: Entity, display: Display, culprit: Culprit, hiding: HidingPlace) -> None:
    obj = world.get("display")
    obj.meters["missing"] = 0.0
    obj.meters["found"] = 1.0
    world.say(
        f"{a.id} and {b.id} gathered the clues, but they could not quite fit them together."
    )
    world.say(
        f'Then {host.label_word} bent near the crooked sign and said, "Listen to the rhyme one more time."'
    )
    world.say(
        f"With that gentle hint, all three of them checked {hiding.phrase}. {hiding.found_text}"
    )
    world.say(
        f"They found {display.phrase} there beside {culprit.label}. Back on the pedestal it went, "
        f"and {a.id} and {b.id} promised to practice both noticing and rhyme-play next time."
    )


def tell(
    setting: Setting,
    display: Display,
    culprit: Culprit,
    name1: str,
    gender1: str,
    skill1: str,
    name2: str,
    gender2: str,
    skill2: str,
    host_type: str,
) -> World:
    world = World(setting)
    world.facts["culprit_id"] = culprit.id
    world.facts["trace_found"] = False
    world.facts["rhyme_read"] = False
    world.facts["solved"] = False

    a = world.add(Entity(id=name1, kind="character", type=gender1, role="sleuth1", traits=[skill1]))
    b = world.add(Entity(id=name2, kind="character", type=gender2, role="sleuth2", traits=[skill2]))
    host = world.add(Entity(id="Host", kind="character", type=host_type, role="host", label=setting.host_label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    room.memes["mystery"] = 0.0
    obj = world.add(Entity(id="display", kind="thing", type="display", label=display.label))
    obj.meters["missing"] = 0.0
    obj.meters["found"] = 0.0

    hiding = HIDING_PLACES[culprit.hide_place]

    introduce(world, a, b, host, display)
    show_object(world, display, host)

    world.para()
    vanish(world, a, b, culprit)

    trace_actor = a if "trace" in SKILLS[skill1].helps_with else b
    rhyme_actor = a if "rhyme" in SKILLS[skill1].helps_with else b

    world.para()
    inspect_trace(world, trace_actor, culprit, hiding)
    if team_has_needed_skills(skill1, skill2):
        read_rhyme(world, rhyme_actor, hiding)
        world.para()
        find_object(world, a, b, display, culprit, hiding)
        restore(world, host, a, b, display)
    else:
        world.para()
        guided_end(world, host, a, b, display, culprit, hiding)

    world.facts.update(
        setting=setting,
        display_cfg=display,
        culprit=culprit,
        hiding=hiding,
        sleuth1=a,
        sleuth2=b,
        host=host,
        solved=world.facts.get("solved", False),
        trace_reader=world.facts.get("trace_reader", ""),
        rhyme_reader=world.facts.get("rhyme_reader", ""),
        outcome="solved" if world.facts.get("solved", False) else "guided",
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(
        id="library",
        place="the library hall",
        host_type="librarian",
        host_label="the librarian",
        intro="The library hall was dressed up for a tiny treasure display.",
        audience="families from the neighborhood",
        affordances={"curtain", "basket"},
        tags={"library"},
    ),
    "museum": Setting(
        id="museum",
        place="the museum room",
        host_type="caretaker",
        host_label="the caretaker",
        intro="The museum room was quiet except for soft shoes and eager whispers.",
        audience="the morning visitors",
        affordances={"curtain", "nest"},
        tags={"museum"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the school greenhouse",
        host_type="teacher",
        host_label="the teacher",
        intro="The school greenhouse smelled of leaves and damp soil on show-and-tell day.",
        audience="the other children",
        affordances={"flowerpot", "basket"},
        tags={"garden"},
    ),
}

DISPLAYS = {
    "bell": Display(
        id="bell",
        label="silver bell",
        phrase="a little silver bell",
        shine=True,
        shape="round",
        sound="jingle",
        weight=1,
        tags={"shiny", "jangly", "round"},
    ),
    "acorn": Display(
        id="acorn",
        label="golden acorn",
        phrase="a painted golden acorn",
        shine=True,
        shape="nut",
        sound="silent",
        weight=1,
        tags={"shiny", "nut"},
    ),
    "marble": Display(
        id="marble",
        label="blue marble",
        phrase="a big blue marble",
        shine=True,
        shape="round",
        sound="silent",
        weight=1,
        tags={"shiny", "round"},
    ),
    "plaque": Display(
        id="plaque",
        label="star plaque",
        phrase="a wooden star plaque",
        shine=False,
        shape="flat",
        sound="silent",
        weight=2,
        tags={"flat"},
    ),
}

CULPRITS = {
    "nix": Culprit(
        id="nix",
        label="Nix the cat",
        kind="cat",
        preference={"round", "jangly"},
        max_weight=1,
        trace="a neat line of dusty pawprints",
        trace_noun="pawprints",
        motion="for batting toys into shadows",
        hide_place="curtain",
        tags={"cat", "pawprints"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="a magpie",
        kind="bird",
        preference={"shiny"},
        max_weight=1,
        trace="one black feather caught beside the stand",
        trace_noun="feather",
        motion="for carrying bright things to a nest",
        hide_place="nest",
        tags={"bird", "feather"},
    ),
    "squirrel": Culprit(
        id="squirrel",
        label="a squirrel",
        kind="animal",
        preference={"nut"},
        max_weight=1,
        trace="crumbly dirt and a tiny scrape mark",
        trace_noun="dirt",
        motion="for tucking treasure into soil",
        hide_place="flowerpot",
        tags={"squirrel", "dirt"},
    ),
}

HIDING_PLACES = {
    "curtain": HidingPlace(
        id="curtain",
        label="the velvet curtain",
        phrase="the velvet curtain by the stage steps",
        rhyme_key="sway",
        rhyme_text="If the prize slipped out to play, look where velvet shadows sway.",
        found_text="Behind its hem, tucked against the wall, something small gave a faint silver glint.",
        setting_ids={"library", "museum"},
        tags={"curtain"},
    ),
    "nest": HidingPlace(
        id="nest",
        label="the twig nest",
        phrase="the twig nest near the high window",
        rhyme_key="tight",
        rhyme_text="If something bright has flown from sight, look where twigs hug tight.",
        found_text="In the nest, among the twigs, rested the missing prize.",
        setting_ids={"museum"},
        tags={"nest"},
    ),
    "flowerpot": HidingPlace(
        id="flowerpot",
        label="the flowerpot",
        phrase="the biggest flowerpot by the tomato vines",
        rhyme_key="pot",
        rhyme_text="If a treasure shaped like a nut is not in its spot, check the crumbly flowerpot.",
        found_text="At the edge of the soil, half-hidden beside a stem, was the missing object.",
        setting_ids={"greenhouse"},
        tags={"plant"},
    ),
}

SKILLS = {
    "tracker": Skill(id="tracker", label="sharp noticing", helps_with={"trace"}),
    "poet": Skill(id="poet", label="rhyme-hearing", helps_with={"rhyme"}),
    "careful": Skill(id="careful", label="careful checking", helps_with={"trace"}),
    "wordplay": Skill(id="wordplay", label="wordplay", helps_with={"rhyme"}),
}

GIRL_NAMES = ["Lila", "Mina", "Zoe", "Ava", "Nora", "Ruby", "Tess", "Ivy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Eli", "Noah", "Finn", "Leo"]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pedestal": [
        (
            "What is a pedestal?",
            "A pedestal is a stand that holds something up high so people can see it well. Museums and displays often use one for a special object.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue uses words that sound alike to help you remember an idea. It can make a hint easier to notice and repeat.",
        )
    ],
    "cat": [
        (
            "Why do cats bat small objects?",
            "Cats like to tap and chase little things that roll or jingle. To a cat, a tiny object can look like a toy.",
        )
    ],
    "bird": [
        (
            "Why might a magpie take something shiny?",
            "Some birds are drawn to bright, shiny objects. They may carry them away because the sparkle catches their eye.",
        )
    ],
    "squirrel": [
        (
            "Why would a squirrel hide something near dirt or plants?",
            "Squirrels like to tuck things into little hiding spots. Soil and pots can feel like good places to stash something small.",
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help in a mystery?",
            "Two people can notice different clues. When they share what each one found, the answer can become clearer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pedestal", "rhyme", "teamwork", "cat", "bird", "squirrel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["sleuth1"]
    b = f["sleuth2"]
    display = f["display_cfg"]
    culprit = f["culprit"]
    return [
        f'Write a gentle whodunit for ages 3 to 5 that includes the words "pedestal" and "nix".',
        f"Tell a mystery-to-solve story where {display.phrase} vanishes from a pedestal and two children solve the case through teamwork.",
        f"Write a child-friendly detective story in which {a.id} and {b.id} follow a trace clue and a rhyme clue to discover that {culprit.label} took the object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["sleuth1"]
    b = f["sleuth2"]
    host = f["host"]
    display = f["display_cfg"]
    culprit = f["culprit"]
    hiding = f["hiding"]

    qa: list[tuple[str, str]] = [
        (
            "What was missing at the start of the mystery?",
            f"{display.phrase.capitalize()} was missing from the pedestal. That empty spot is what turned the day into a little whodunit.",
        ),
        (
            "Why did the children stop guessing and start looking around?",
            f"They wanted a real answer, not a wild guess. {b.id} even said they should nix the guessing and look for clues instead.",
        ),
        (
            f"What clue showed who took the object?",
            f"The children found {culprit.trace}. That trace pointed to {culprit.label}, because it matched the kind of animal that had been near the pedestal.",
        ),
    ]
    if f["outcome"] == "solved":
        qa.append(
            (
                "How did teamwork help solve the mystery?",
                f"{f['trace_reader']} noticed the physical clue, and {f['rhyme_reader']} understood the rhyme on the sign. The mystery was solved because they put both clues together instead of each child working alone.",
            )
        )
        qa.append(
            (
                f"Where did they find the missing object?",
                f"They found it at {hiding.phrase}. The rhyme pointed there, and the trace clue told them which little culprit to look for.",
            )
        )
        qa.append(
            (
                f"Was {culprit.label} trying to be mean?",
                f"No. {culprit.label} was not trying to spoil the day. {culprit.pronoun().capitalize()} carried the object away because it seemed interesting like a toy or treasure.",
            )
        )
    else:
        qa.append(
            (
                "Did the children solve the mystery all by themselves?",
                f"Not quite. They gathered good clues, but {host.label_word} gave them one more hint before they found the object.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pedestal", "rhyme", "teamwork"}
    culprit = world.facts["culprit"]
    if culprit.id == "nix":
        tags.add("cat")
    elif culprit.id == "magpie":
        tags.add("bird")
    elif culprit.id == "squirrel":
        tags.add("squirrel")

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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} trace_reader={world.facts.get('trace_reader')} rhyme_reader={world.facts.get('rhyme_reader')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated samples
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="museum",
        display="bell",
        culprit="nix",
        sleuth1="Lila",
        sleuth1_gender="girl",
        sleuth1_skill="tracker",
        sleuth2="Ben",
        sleuth2_gender="boy",
        sleuth2_skill="poet",
        host="caretaker",
    ),
    StoryParams(
        setting="museum",
        display="marble",
        culprit="magpie",
        sleuth1="Max",
        sleuth1_gender="boy",
        sleuth1_skill="careful",
        sleuth2="Ruby",
        sleuth2_gender="girl",
        sleuth2_skill="wordplay",
        host="caretaker",
    ),
    StoryParams(
        setting="greenhouse",
        display="acorn",
        culprit="squirrel",
        sleuth1="Nora",
        sleuth1_gender="girl",
        sleuth1_skill="poet",
        sleuth2="Theo",
        sleuth2_gender="boy",
        sleuth2_skill="tracker",
        host="teacher",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_take(D, C) :- display(D), culprit(C), weight(D, W), max_weight(C, M), W <= M, likes(C, T), has_tag(D, T).
fits_place(S, C) :- setting(S), culprit(C), hide_place(C, H), place_has(S, H).

valid(S, D, C) :- setting(S), display(D), culprit(C), can_take(D, C), fits_place(S, C).

team_has(trace) :- chosen_skill1(S), helps(S, trace).
team_has(trace) :- chosen_skill2(S), helps(S, trace).
team_has(rhyme) :- chosen_skill1(S), helps(S, rhyme).
team_has(rhyme) :- chosen_skill2(S), helps(S, rhyme).

solved :- team_has(trace), team_has(rhyme).
guided :- not solved.

outcome(solved) :- solved.
outcome(guided) :- guided.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for setting_id, setting in SETTINGS.items():
        for place in sorted(setting.affordances):
            lines.append(asp.fact("place_has", setting_id, place))
    for display_id, display in DISPLAYS.items():
        lines.append(asp.fact("display", display_id))
        lines.append(asp.fact("weight", display_id, display.weight))
        for tag in sorted(display_tags(display)):
            lines.append(asp.fact("has_tag", display_id, tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("max_weight", culprit_id, culprit.max_weight))
        lines.append(asp.fact("hide_place", culprit_id, culprit.hide_place))
        for tag in sorted(culprit.preference):
            lines.append(asp.fact("likes", culprit_id, tag))
    for skill_id, skill in SKILLS.items():
        lines.append(asp.fact("skill", skill_id))
        for item in sorted(skill.helps_with):
            lines.append(asp.fact("helps", skill_id, item))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_skill1", params.sleuth1_skill),
            asp.fact("chosen_skill2", params.sleuth2_skill),
        ]
    )
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed unexpectedly for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny whodunit storyworld: a missing object on a pedestal, a rhyme clue, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--sleuth1-skill", choices=SKILLS)
    ap.add_argument("--sleuth2-skill", choices=SKILLS)
    ap.add_argument("--host", choices=["librarian", "caretaker", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.display and args.culprit:
        setting = SETTINGS[args.setting]
        display = DISPLAYS[args.display]
        culprit = CULPRITS[args.culprit]
        if not (culprit_can_take(display, culprit) and place_fits(setting.id, culprit)):
            raise StoryError(explain_combo_rejection(setting, display, culprit))

    if args.sleuth1_skill and args.sleuth2_skill:
        if not team_has_needed_skills(args.sleuth1_skill, args.sleuth2_skill):
            raise StoryError(explain_skill_rejection(args.sleuth1_skill, args.sleuth2_skill))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.display is None or combo[1] == args.display)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, display_id, culprit_id = rng.choice(combos)

    skill_pairs = [
        pair
        for pair in valid_skill_pairs()
        if (args.sleuth1_skill is None or pair[0] == args.sleuth1_skill)
        and (args.sleuth2_skill is None or pair[1] == args.sleuth2_skill)
    ]
    if not skill_pairs:
        raise StoryError("(No valid skill pair matches the given options.)")

    skill1, skill2 = rng.choice(skill_pairs)
    gender1 = rng.choice(["girl", "boy"])
    gender2 = rng.choice(["girl", "boy"])
    name1 = _pick_name(rng, gender1)
    name2 = _pick_name(rng, gender2, avoid=name1)
    setting = SETTINGS[setting_id]
    host = args.host or setting.host_type

    return StoryParams(
        setting=setting_id,
        display=display_id,
        culprit=culprit_id,
        sleuth1=name1,
        sleuth1_gender=gender1,
        sleuth1_skill=skill1,
        sleuth2=name2,
        sleuth2_gender=gender2,
        sleuth2_skill=skill2,
        host=host,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.display not in DISPLAYS:
        raise StoryError(f"Unknown display: {params.display}")
    if params.culprit not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit}")
    if params.sleuth1_skill not in SKILLS or params.sleuth2_skill not in SKILLS:
        raise StoryError("Unknown sleuth skill.")
    if params.host not in {"librarian", "caretaker", "teacher"}:
        raise StoryError(f"Unknown host type: {params.host}")

    setting = SETTINGS[params.setting]
    display = DISPLAYS[params.display]
    culprit = CULPRITS[params.culprit]

    if not (culprit_can_take(display, culprit) and place_fits(setting.id, culprit)):
        raise StoryError(explain_combo_rejection(setting, display, culprit))
    if not team_has_needed_skills(params.sleuth1_skill, params.sleuth2_skill):
        raise StoryError(explain_skill_rejection(params.sleuth1_skill, params.sleuth2_skill))

    world = tell(
        setting=setting,
        display=display,
        culprit=culprit,
        name1=params.sleuth1,
        gender1=params.sleuth1_gender,
        skill1=params.sleuth1_skill,
        name2=params.sleuth2,
        gender2=params.sleuth2_gender,
        skill2=params.sleuth2_skill,
        host_type=params.host,
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
        print(f"{len(combos)} compatible (setting, display, culprit) combos:\n")
        for setting_id, display_id, culprit_id in combos:
            print(f"  {setting_id:10} {display_id:8} {culprit_id}")
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
            header = f"### {p.sleuth1} & {p.sleuth2}: {p.display} at {p.setting} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
