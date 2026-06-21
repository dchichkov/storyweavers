#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py
=================================================================

A standalone story world for a tiny pirate-style tale about a costume quarrel,
a remembered mistake, and a better way to keep playing together.

Seed cues rebuilt as world state
--------------------------------
- required word: tutu
- required features: Conflict, Flashback
- style: Pirate Tale

This world imagines two children turning a room into a pirate ship. One child
wants to wear a swishy tutu as part of the captain outfit. The other objects for
a concrete reason. Their game stalls. Then one of them remembers an earlier
dress-up quarrel that spoiled a whole afternoon, and that flashback helps them
choose a compromise.

The model prefers only combinations where:
- the objection is plausible,
- the proposed fix actually answers that objection, and
- the remembered lesson supports that fix.

A second layer decides whether the children truly mend the quarrel or stay
stuck for the rest of the day, based on trust, temper, and the strength of the
remembered lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py --asp
    python storyworlds/worlds/gpt-5.4/tutu_conflict_flashback_pirate_tale.py --verify
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
TRUST_THRESHOLD = 7
PRIDE_INIT = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    sail_end: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    hiding_place: str
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
class Objection:
    id: str
    line: str
    reason: str
    need_tag: str
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
class Flashback:
    id: str
    item: str
    scene: str
    result: str
    lesson_tag: str
    power: int
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
class Fix:
    id: str
    line: str
    action: str
    solves: set[str]
    lessons: set[str]
    soothe: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"dreamer", "guard"}]

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


def _r_game_stalls(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["quarrel"] < THRESHOLD:
        return []
    sig = ("stall",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["play_stopped"] += 1
    for kid in world.kids():
        kid.memes["joy"] = max(0.0, kid.memes["joy"] - 1.0)
        kid.memes["sadness"] += 1.0
    return ["__stall__"]


def _r_memory_softens(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["remembered"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rememberer = world.get(world.facts["rememberer"])
    rememberer.memes["care"] += 1.0
    rememberer.memes["share"] += float(world.facts["flashback"].power)
    return ["__memory__"]


def _r_mend(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["compromise"] < THRESHOLD:
        return []
    sig = ("mend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["quarrel"] = 0.0
    room.meters["play_stopped"] = 0.0
    room.meters["shared_play"] += 1.0
    for kid in world.kids():
        kid.memes["joy"] += 2.0
        kid.memes["sadness"] = 0.0
        kid.memes["trust"] += 1.0
    return ["__mended__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="game_stalls", tag="social", apply=_r_game_stalls),
    Rule(name="memory_softens", tag="memory", apply=_r_memory_softens),
    Rule(name="mend", tag="social", apply=_r_mend),
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


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a bright little pirate cove",
        rig="The sofa was their ship, a broom was the mast, a blue blanket became the sea, and a crayon map curled across the rug.",
        titles=("Captain", "Lookout"),
        goal="the buried gold under the window-seat cliffs",
        sail_end="sailed after the treasure with the curtain-light on their cheeks",
        tags={"pirates", "dress_up"},
    ),
    "storm_crew": Theme(
        id="storm_crew",
        scene="a stormy deck at the edge of the world",
        rig="The sofa was their ship, a laundry basket was the crow's-nest, a striped towel became the sail, and a spoon tapped the rail like a bell.",
        titles=("Captain", "Navigator"),
        goal="the pearl hidden beyond the thunder rocks",
        sail_end="steered for the pearl while the towel-sail snapped above them",
        tags={"pirates", "storm"},
    ),
    "island_queens": Theme(
        id="island_queens",
        scene="a glittering island sea",
        rig="The sofa was their ship, a cardboard box was the treasure chest, a green scarf became the waves, and chalk shells marked the shore.",
        titles=("Captain", "Scout"),
        goal="the singing shell hidden by the tide cave",
        sail_end="glided toward the tide cave with happy feet and brave hearts",
        tags={"pirates", "sparkle"},
    ),
}

TREASURES = {
    "gold": Treasure(
        id="gold",
        label="gold",
        phrase="a shoebox of gold buttons",
        hiding_place="under the window seat",
        tags={"treasure"},
    ),
    "pearl": Treasure(
        id="pearl",
        label="moon pearl",
        phrase="a smooth moon pearl",
        hiding_place="behind the curtain cave",
        tags={"treasure", "pearl"},
    ),
    "shell": Treasure(
        id="shell",
        label="singing shell",
        phrase="a singing shell with a pink curl",
        hiding_place="inside the blanket cave",
        tags={"treasure", "shell"},
    ),
}

OBJECTIONS = {
    "not_piratey": Objection(
        id="not_piratey",
        line='Pirates wear rough coats and boots. That tutu looks too party-swish for a captain.',
        reason="the guard thinks the costume does not look pirate enough",
        need_tag="pirate_look",
        tags={"sharing", "pirates"},
    ),
    "too_swishy": Objection(
        id="too_swishy",
        line='That tutu is so wide it will flap in the ropes and slow the captain down.',
        reason="the guard worries the costume will get in the way of ship work",
        need_tag="practical",
        tags={"clothes", "safety"},
    ),
    "captain_only": Objection(
        id="captain_only",
        line='If the tutu is the special captain thing, then only one of us gets the best part.',
        reason="the guard thinks the costume would make the game feel unfair",
        need_tag="fairness",
        tags={"sharing", "fairness"},
    ),
}

FLASHBACKS = {
    "crown": Flashback(
        id="crown",
        item="a cardboard crown",
        scene="last week by the toy chest",
        result="they tugged it from both sides until it bent flat, and the game ended in tears",
        lesson_tag="combine",
        power=2,
        tags={"flashback", "sharing"},
    ),
    "compass": Flashback(
        id="compass",
        item="a shiny toy compass",
        scene="one rainy afternoon under the kitchen table",
        result="they argued over whose turn it was until the pretend voyage never even began",
        lesson_tag="take_turns",
        power=2,
        tags={"flashback", "turns"},
    ),
    "banner": Flashback(
        id="banner",
        item="a silver paper banner",
        scene="the day of the pillow fort parade",
        result="they laughed only after giving it a new pirate name and using it in a different way",
        lesson_tag="rename",
        power=1,
        tags={"flashback", "naming"},
    ),
}

FIXES = {
    "coat_over": Fix(
        id="coat_over",
        line='What if the tutu stays on, and we put the black captain coat over it so it looks bold and piratey?',
        action="They settled the black play coat over the tutu until only a ring of silver fluff peeked out.",
        solves={"pirate_look"},
        lessons={"combine", "rename"},
        soothe=2,
        ending_image="The silver edge of the tutu fluttered under the captain coat like a secret wave.",
        tags={"tutu", "coat"},
    ),
    "knot_up": Fix(
        id="knot_up",
        line='What if we tie the tutu up with the red sash so it stays neat for climbing and running the ship?',
        action="They tucked the soft tutu into a red sash, making it short and tidy for ship work.",
        solves={"practical"},
        lessons={"combine", "rename"},
        soothe=2,
        ending_image="The tucked-up tutu bounced like a brave little sail as the captain stomped across the rug.",
        tags={"tutu", "sash"},
    ),
    "co_captains": Fix(
        id="co_captains",
        line='What if the tutu is not the captain prize at all? We can both be captains and trade the wheel each time the bell rings.',
        action="They made two captain turns and set a spoon-bell beside the mast to mark each swap.",
        solves={"fairness"},
        lessons={"take_turns", "rename"},
        soothe=3,
        ending_image="The tutu rested at the wheel for one turn and then twirled to the map for the next.",
        tags={"tutu", "turns"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "thoughtful", "gentle", "fiery", "stubborn", "proud"]


def valid_combo(theme_id: str, treasure_id: str, objection_id: str, flashback_id: str, fix_id: str) -> bool:
    if theme_id not in THEMES or treasure_id not in TREASURES:
        return False
    if objection_id not in OBJECTIONS or flashback_id not in FLASHBACKS or fix_id not in FIXES:
        return False
    objection = OBJECTIONS[objection_id]
    flashback = FLASHBACKS[flashback_id]
    fix = FIXES[fix_id]
    return objection.need_tag in fix.solves and flashback.lesson_tag in fix.lessons


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for theme_id in THEMES:
        for treasure_id in TREASURES:
            for objection_id in OBJECTIONS:
                for flashback_id in FLASHBACKS:
                    for fix_id in FIXES:
                        if valid_combo(theme_id, treasure_id, objection_id, flashback_id, fix_id):
                            combos.append((theme_id, treasure_id, objection_id, flashback_id, fix_id))
    return combos


def trait_bonus(trait: str) -> int:
    return {"careful": 2, "thoughtful": 2, "gentle": 1, "fiery": -1, "stubborn": -2, "proud": -1}.get(trait, 0)


def repaired_outcome(params: "StoryParams") -> str:
    flashback = FLASHBACKS[params.flashback]
    fix = FIXES[params.fix]
    score = params.trust + flashback.power + fix.soothe + trait_bonus(params.guard_trait)
    return "mended" if score >= TRUST_THRESHOLD else "stalled"


def explain_rejection(objection_id: str, flashback_id: str, fix_id: str) -> str:
    parts = []
    if objection_id in OBJECTIONS and fix_id in FIXES:
        objection = OBJECTIONS[objection_id]
        fix = FIXES[fix_id]
        if objection.need_tag not in fix.solves:
            parts.append(
                f"'{fix_id}' does not solve the problem behind '{objection_id}'"
            )
    if flashback_id in FLASHBACKS and fix_id in FIXES:
        flashback = FLASHBACKS[flashback_id]
        fix = FIXES[fix_id]
        if flashback.lesson_tag not in fix.lessons:
            parts.append(
                f"the flashback lesson from '{flashback_id}' does not point toward '{fix_id}'"
            )
    if not parts:
        return "(No story: that combination does not make a sensible pirate quarrel and repair.)"
    return "(No story: " + "; ".join(parts) + ".)"


def predict_repair(world: World, fix_id: str) -> dict:
    sim = world.copy()
    sim.facts["chosen_fix"] = fix_id
    fix = FIXES[fix_id]
    score = sim.facts["trust"] + sim.facts["flashback"].power + fix.soothe + trait_bonus(sim.facts["guard"].traits[0])
    return {"score": score, "mended": score >= TRUST_THRESHOLD}


def play_setup(world: World, dreamer: Entity, guard: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in (dreamer, guard):
        kid.memes["joy"] += 1.0
    world.say(
        f"On a bright afternoon, {dreamer.id} and {guard.id} turned the living room into {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.titles[0]} {dreamer.id} and {theme.titles[1]} {guard.id}!" {dreamer.id} cried. "Today we sail for {theme.goal}."'
    )
    world.say(
        f"They said the treasure would be {treasure.phrase} hidden {treasure.hiding_place}."
    )


def discover_tutu(world: World, dreamer: Entity) -> None:
    tutu = world.get("tutu")
    dreamer.memes["delight"] += 1.0
    world.say(
        f"Then {dreamer.id} lifted the lid of the dress-up box and found a silver {tutu.label}. It shimmered like fish scales in a sunbeam."
    )
    world.say(
        f'"This will be my captain skirt!" {dreamer.id} said, slipping the tutu on and spinning once on the rug.'
    )


def object(world: World, guard: Entity, dreamer: Entity, objection: Objection) -> None:
    room = world.get("room")
    room.meters["quarrel"] += 1.0
    dreamer.memes["pride"] += 1.0
    guard.memes["worry"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f'''But {guard.id} frowned. "{objection.line}"'''
    )
    world.say(
        f'{dreamer.id} stopped spinning. "It is too a captain skirt," {dreamer.pronoun()} said, and the game went still for a moment.'
    )


def deepen_conflict(world: World, dreamer: Entity, guard: Entity) -> None:
    room = world.get("room")
    if room.meters["play_stopped"] >= THRESHOLD:
        world.say(
            f"The spoon-bell did not ring. The ship felt less like a ship and more like a room with two crossed arms in it."
        )
    world.say(
        f'{guard.id} held the map tight. {dreamer.id} tugged at the soft silver hem of the tutu, both of them wanting the game to go their own way.'
    )


def remember(world: World, rememberer: Entity, flashback: Flashback) -> None:
    room = world.get("room")
    room.meters["remembered"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {rememberer.id} remembered {flashback.scene}, when {rememberer.pronoun()} and {world.facts['other'].id} had fought over {flashback.item}. In a blink of memory, {flashback.result}."
    )
    world.say(
        f"The memory made {rememberer.id}'s chest feel small. {rememberer.pronoun().capitalize()} did not want this pirate day to sink the same way."
    )


def propose_fix(world: World, guard: Entity, fix: Fix) -> None:
    pred = predict_repair(world, fix.id)
    world.facts["repair_score"] = pred["score"]
    world.say(
        f'{guard.id} let the map loosen a little. "{fix.line}"'
    )
    if pred["score"] >= TRUST_THRESHOLD:
        world.say(
            f"The idea sounded calm instead of bossy, and the room seemed to breathe again."
        )
    else:
        world.say(
            f"It was a good idea, but the hurt in the room was still heavy and hard to move."
        )


def accept_fix(world: World, dreamer: Entity, guard: Entity, fix: Fix, theme: Theme, treasure: Treasure) -> None:
    room = world.get("room")
    room.meters["compromise"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"{dreamer.id} looked at the tutu, then at {guard.id}, and nodded. {fix.action}"
    )
    world.say(
        f"Soon the quarrel was gone. One held the map, one watched the waves, and then they traded jobs as their ship chased {treasure.phrase}."
    )
    world.say(
        f'{fix.ending_image} By the time they reached {treasure.hiding_place}, both children were laughing again.'
    )
    world.say(
        f"And the little pirate crew {theme.sail_end}."
    )


def refuse_fix(world: World, dreamer: Entity, guard: Entity, fix: Fix, parent: Entity) -> None:
    dreamer.memes["stubbornness"] += 1.0
    guard.memes["sadness"] += 1.0
    world.say(
        f"But {dreamer.id}'s face stayed tight. {dreamer.pronoun().capitalize()} shook {dreamer.pronoun('possessive')} head and held the silver tutu close."
    )
    world.say(
        f'{guard.id} put the map down on the rug. Neither child felt like being captain anymore.'
    )
    world.say(
        f"After a quiet while, {parent.label_word} came to the doorway and helped them fold the blanket sea. The ship could wait until they were ready to share it better tomorrow."
    )

def tell(
    treasure: Treasure,
    objection: Objection,
    flashback: Flashback,
    fix: Fix,
    dreamer_name: str,
    dreamer_gender: str,
    guard_name: str,
    guard_gender: str,
    parent_type: ParentType,
    relation: Relation,
    trust: Trust,
    dreamer_age: DreamerAge,
    guard_age: GuardAge,
    guard_trait: GuardTrait,
    theme=None,
) -> World:
    world = World()
    dreamer = world.add(Entity(
        id=dreamer_name,
        kind="character",
        type=dreamer_gender,
        role="dreamer",
        age=dreamer_age,
        attrs={"relation": relation},
    ))
    guard = world.add(Entity(
        id=guard_name,
        kind="character",
        type=guard_gender,
        role="guard",
        age=guard_age,
        traits=[guard_trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="the room",
    ))
    tutu = world.add(Entity(
        id="tutu",
        type="costume",
        label="tutu",
        tags={"tutu", "costume"},
    ))

    dreamer.memes["trust"] = float(trust)
    guard.memes["trust"] = float(trust)
    dreamer.memes["pride"] = float(PRIDE_INIT)
    guard.memes["care"] = 1.0
    room.meters["quarrel"] = 0.0
    room.meters["remembered"] = 0.0
    room.meters["compromise"] = 0.0
    room.meters["play_stopped"] = 0.0
    room.meters["shared_play"] = 0.0

    world.facts.update(
        theme=theme,
        treasure=treasure,
        objection=objection,
        flashback=flashback,
        fix=fix,
        dreamer=dreamer,
        guard=guard,
        other=dreamer,
        parent=parent,
        trust=trust,
        relation=relation,
        rememberer=guard.id,
    )

    play_setup(world, dreamer, guard, theme, treasure)
    world.para()
    discover_tutu(world, dreamer)
    object(world, guard, dreamer, objection)
    deepen_conflict(world, dreamer, guard)

    world.para()
    remember(world, guard, flashback)
    propose_fix(world, guard, fix)

    outcome = repaired_outcome(StoryParams(
        theme=theme.id,
        treasure=treasure.id,
        objection=objection.id,
        flashback=flashback.id,
        fix=fix.id,
        dreamer=dreamer_name,
        dreamer_gender=dreamer_gender,
        guard=guard_name,
        guard_gender=guard_gender,
        parent=parent_type,
        relation=relation,
        trust=trust,
        dreamer_age=dreamer_age,
        guard_age=guard_age,
        guard_trait=guard_trait,
        seed=None,
    ))

    world.para()
    if outcome == "mended":
        accept_fix(world, dreamer, guard, fix, theme, treasure)
    else:
        refuse_fix(world, dreamer, guard, fix, parent)

    world.facts.update(
        outcome=outcome,
        conflict_started=room.meters["play_stopped"] >= THRESHOLD or True,
        repaired=(outcome == "mended"),
        repair_score=world.facts.get("repair_score", 0),
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


KNOWLEDGE = {
    "tutu": [
        (
            "What is a tutu?",
            "A tutu is a skirt made of many light, fluffy layers. People often wear one for dancing or dress-up play."
        )
    ],
    "pirates": [
        (
            "What is a pirate in pretend play?",
            "In pretend play, a pirate is a make-believe sailor who hunts treasure and sails a ship. Children often use blankets, boxes, and maps to imagine the sea."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in a game?",
            "Sharing helps everyone stay in the game together. When children share turns or ideas, the fun can keep going instead of stopping in the middle."
        )
    ],
    "fairness": [
        (
            "What does fair mean when children play together?",
            "Fair means each person gets a real chance to join in and enjoy the game. It does not always mean exactly the same thing, but it should feel kind and balanced."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story remembers something that happened earlier. That old memory can help a character decide what to do now."
        )
    ],
    "coat": [
        (
            "Why do costumes change when you add another piece?",
            "A costume can look different when you layer clothes or add a hat, coat, or sash. One new piece can help it fit a new pretend role."
        )
    ],
    "sash": [
        (
            "What is a sash?",
            "A sash is a long strip of cloth that can tie around a waist or shoulder. In dress-up, it can help hold something in place or make an outfit look special."
        )
    ],
    "turns": [
        (
            "Why do taking turns help with arguments?",
            "Taking turns gives each person a chance instead of leaving one child out. That often turns a fight into a plan both players can accept."
        )
    ],
}
KNOWLEDGE_ORDER = ["tutu", "pirates", "flashback", "sharing", "fairness", "coat", "sash", "turns"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dreamer = f["dreamer"]
    guard = f["guard"]
    theme = f["theme"]
    objection = f["objection"]
    outcome = f["outcome"]
    if outcome == "mended":
        return [
            'Write a pirate-style story for a 3-to-5-year-old that includes the word "tutu" and uses a flashback to help solve a quarrel.',
            f"Tell a gentle pirate tale where {dreamer.id} wants to wear a tutu as part of the captain costume, {guard.id} objects because {objection.reason}, and a remembered mistake helps them play together again.",
            f"Write a story with conflict and flashback where two children nearly ruin a treasure game, but a kind compromise saves the adventure."
        ]
    return [
        'Write a pirate-style story for a 3-to-5-year-old that includes the word "tutu" and uses a flashback during a costume quarrel.',
        f"Tell a pirate tale where {dreamer.id} and {guard.id} fight over a tutu captain costume, remember an older quarrel, and still struggle to fix the game.",
        f"Write a story with conflict and flashback where a pirate game goes quiet because the children cannot share their dress-up idea in time."
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dreamer = f["dreamer"]
    guard = f["guard"]
    parent = f["parent"]
    theme = f["theme"]
    treasure = f["treasure"]
    objection = f["objection"]
    flashback = f["flashback"]
    fix = f["fix"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(dreamer, guard, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {dreamer.id} and {guard.id}, who were pretending to be pirates in the living room. Their pirate game matters because both children cared about it very much."
        ),
        (
            "What started the conflict?",
            f"The conflict started when {dreamer.id} found a silver tutu and wanted it to be part of the captain outfit. {guard.id} objected because {objection.reason}, so the pirate game stopped feeling easy and shared."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {flashback.item} from {flashback.scene}. They remembered that {flashback.result}, which warned {guard.id} that this new quarrel could sink the game too."
        ),
    ]
    if outcome == "mended":
        qa.extend([
            (
                "How did the flashback help them solve the problem?",
                f"The memory made {guard.id} want to save the game instead of winning the argument. Because {guard.pronoun()} remembered the earlier mess, {guard.pronoun()} offered a calmer fix: {fix.line[:-1] if fix.line.endswith('?') else fix.line}."
            ),
            (
                "How did they fix the tutu problem?",
                f"They used the tutu in a new way that answered the real problem, and then the quarrel melted. {fix.action} That let both children get back to the treasure game instead of standing still and upset."
            ),
            (
                "How did the story end?",
                f"It ended with the pirate game alive again. They went after {treasure.phrase}, and the last picture shows that the tutu had become part of a shared adventure instead of a fight."
            ),
        ])
    else:
        qa.extend([
            (
                "Did the flashback solve the conflict right away?",
                f"No. The memory gave them a better idea, but the hurt feelings were still too strong. Even with a sensible fix, they could not let go of the quarrel before the game sank for the day."
            ),
            (
                f"What did {pw} do at the end?",
                f"{pw.capitalize()} came to the doorway and helped them put the pretend sea away. That ending shows the adventure paused because the children were still learning how to share it."
            ),
            (
                "How did the story end?",
                f"It ended quietly instead of triumphantly. Nobody was in danger, but the pirate ship had to wait for another day because the conflict stayed bigger than the compromise."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tutu", "pirates", "flashback", "sharing"}
    if f["objection"].need_tag == "fairness":
        tags.add("fairness")
    if f["fix"].id == "coat_over":
        tags.add("coat")
    if f["fix"].id == "knot_up":
        tags.add("sash")
    if f["fix"].id == "co_captains":
        tags.add("turns")
        tags.add("fairness")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    theme: str
    treasure: str
    objection: str
    flashback: str
    fix: str
    dreamer: str
    dreamer_gender: str
    guard: str
    guard_gender: str
    parent: str
    relation: str = "siblings"
    trust: int = 5
    dreamer_age: int = 5
    guard_age: int = 6
    guard_trait: str = "thoughtful"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        theme="pirates",
        treasure="gold",
        objection="not_piratey",
        flashback="crown",
        fix="coat_over",
        dreamer="Lily",
        dreamer_gender="girl",
        guard="Tom",
        guard_gender="boy",
        parent="mother",
        relation="siblings",
        trust=6,
        dreamer_age=5,
        guard_age=6,
        guard_trait="thoughtful",
    ),
    StoryParams(
        theme="storm_crew",
        treasure="pearl",
        objection="too_swishy",
        flashback="banner",
        fix="knot_up",
        dreamer="Mia",
        dreamer_gender="girl",
        guard="Ben",
        guard_gender="boy",
        parent="father",
        relation="friends",
        trust=5,
        dreamer_age=6,
        guard_age=6,
        guard_trait="careful",
    ),
    StoryParams(
        theme="island_queens",
        treasure="shell",
        objection="captain_only",
        flashback="compass",
        fix="co_captains",
        dreamer="Ava",
        dreamer_gender="girl",
        guard="Ella",
        guard_gender="girl",
        parent="mother",
        relation="siblings",
        trust=4,
        dreamer_age=5,
        guard_age=7,
        guard_trait="gentle",
    ),
    StoryParams(
        theme="pirates",
        treasure="gold",
        objection="captain_only",
        flashback="banner",
        fix="co_captains",
        dreamer="Sam",
        dreamer_gender="boy",
        guard="Zoe",
        guard_gender="girl",
        parent="father",
        relation="friends",
        trust=2,
        dreamer_age=6,
        guard_age=6,
        guard_trait="proud",
    ),
    StoryParams(
        theme="storm_crew",
        treasure="shell",
        objection="not_piratey",
        flashback="banner",
        fix="coat_over",
        dreamer="Nora",
        dreamer_gender="girl",
        guard="Leo",
        guard_gender="boy",
        parent="mother",
        relation="siblings",
        trust=1,
        dreamer_age=5,
        guard_age=7,
        guard_trait="stubborn",
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(T, Tr, O, Fb, Fx) :-
    theme(T), treasure(Tr), objection(O), flashback(Fb), fix(Fx),
    need(O, Need), solves(Fx, Need),
    lesson(Fb, Lesson), allows(Fx, Lesson).

% --- outcome model ---------------------------------------------------------
trait_bonus(careful, 2).
trait_bonus(thoughtful, 2).
trait_bonus(gentle, 1).
trait_bonus(fiery, -1).
trait_bonus(stubborn, -2).
trait_bonus(proud, -1).

repair_score(Trust + Pow + Soothe + Bonus) :-
    trust(Trust),
    chosen_flashback(Fb), power(Fb, Pow),
    chosen_fix(Fx), soothe(Fx, Soothe),
    guard_trait(Trait), trait_bonus(Trait, Bonus).

mended :- repair_score(S), trust_threshold(T), S >= T.
outcome(mended) :- mended.
outcome(stalled) :- not mended.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for trid in TREASURES:
        lines.append(asp.fact("treasure", trid))
    for oid, obj in OBJECTIONS.items():
        lines.append(asp.fact("objection", oid))
        lines.append(asp.fact("need", oid, obj.need_tag))
    for fbid, fb in FLASHBACKS.items():
        lines.append(asp.fact("flashback", fbid))
        lines.append(asp.fact("lesson", fbid, fb.lesson_tag))
        lines.append(asp.fact("power", fbid, fb.power))
    for fxid, fx in FIXES.items():
        lines.append(asp.fact("fix", fxid))
        lines.append(asp.fact("soothe", fxid, fx.soothe))
        for need in sorted(fx.solves):
            lines.append(asp.fact("solves", fxid, need))
        for lesson in sorted(fx.lessons):
            lines.append(asp.fact("allows", fxid, lesson))
    lines.append(asp.fact("trust_threshold", TRUST_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("trust", params.trust),
        asp.fact("chosen_flashback", params.flashback),
        asp.fact("chosen_fix", params.fix),
        asp.fact("guard_trait", params.guard_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate dress-up quarrel, a flashback, and a better way to play."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--objection", choices=OBJECTIONS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.objection and args.flashback and args.fix:
        if not valid_combo(args.theme or next(iter(THEMES)), args.treasure or next(iter(TREASURES)), args.objection, args.flashback, args.fix):
            raise StoryError(explain_rejection(args.objection, args.flashback, args.fix))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.treasure is None or c[1] == args.treasure)
        and (args.objection is None or c[2] == args.objection)
        and (args.flashback is None or c[3] == args.flashback)
        and (args.fix is None or c[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, treasure_id, objection_id, flashback_id, fix_id = rng.choice(sorted(combos))
    dreamer_name, dreamer_gender = _pick_kid(rng)
    guard_name, guard_gender = _pick_kid(rng, avoid=dreamer_name)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    dreamer_age, guard_age = rng.sample([4, 5, 6, 7], 2)
    guard_trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        treasure=treasure_id,
        objection=objection_id,
        flashback=flashback_id,
        fix=fix_id,
        dreamer=dreamer_name,
        dreamer_gender=dreamer_gender,
        guard=guard_name,
        guard_gender=guard_gender,
        parent=parent,
        relation=relation,
        trust=trust,
        dreamer_age=dreamer_age,
        guard_age=guard_age,
        guard_trait=guard_trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        (params.theme, THEMES),
        (params.treasure, TREASURES),
        (params.objection, OBJECTIONS),
        (params.flashback, FLASHBACKS),
        (params.fix, FIXES),
    ):
        if key not in table:
            raise StoryError(f"(No story: unknown registry key '{key}'.)")
    if not valid_combo(params.theme, params.treasure, params.objection, params.flashback, params.fix):
        raise StoryError(explain_rejection(params.objection, params.flashback, params.fix))

    world = tell(
        theme=THEMES[params.theme],
        treasure=TREASURES[params.treasure],
        objection=OBJECTIONS[params.objection],
        flashback=FLASHBACKS[params.flashback],
        fix=FIXES[params.fix],
        dreamer_name=params.dreamer,
        dreamer_gender=params.dreamer_gender,
        guard_name=params.guard,
        guard_gender=params.guard_gender,
        parent_type=params.parent,
        relation=params.relation,
        trust=params.trust,
        dreamer_age=params.dreamer_age,
        guard_age=params.guard_age,
        guard_trait=params.guard_trait,
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


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: compatibility gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = repaired_outcome(params)
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treasure, objection, flashback, fix) combos:\n")
        for theme, treasure, objection, flashback, fix in combos:
            print(f"  {theme:13} {treasure:7} {objection:13} {flashback:8} {fix}")
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
                f"### {p.dreamer} & {p.guard}: {p.objection} -> {p.fix} "
                f"({p.theme}, {repaired_outcome(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
