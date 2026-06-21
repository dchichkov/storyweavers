#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py
=====================================================================================

A small story world for a child-facing ghost-story misunderstanding: in a dim
corner of the house, a child sees an ordinary object move in the glow of a
one-watt bulb, mistakes it for a ghost, and learns a moral about checking
kindly, speaking honestly, and being brave in the right way.

The world model is classical and state-driven:

- typed entities with physical meters and emotional memes
- a tiny forward-chaining rule engine
- a reasonableness gate for plausible (place, source, motion) combinations
- an inline ASP twin for the same gate and for the simple outcome model
- prose driven by simulated state, including an inner-monologue beat

Run it
------
    python storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py
    python storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py --place attic --source sheet --motion breeze
    python storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py --all
    python storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/watt_misunderstanding_inner_monologue_moral_value_ghost.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    approach: str
    detail: str
    afford_sources: set[str] = field(default_factory=set)
    afford_motions: set[str] = field(default_factory=set)
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
class Source:
    id: str
    label: str
    phrase: str
    ordinary_name: str
    reveal_line: str
    hangs: bool = True
    pale: bool = True
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
class Motion:
    id: str
    label: str
    spooky_line: str
    reveal_line: str
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
class ValueLesson:
    id: str
    title: str
    lesson_line: str
    second_line: str
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
    label: str
    quiet: bool
    child_line: str
    helper_intro: str
    outcome: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_spooky_shape(world: World) -> list[str]:
    child = world.get("child")
    scene = world.get("scene")
    source = world.get("source")
    if child.meters["dim_light"] < THRESHOLD:
        return []
    if source.meters["moving"] < THRESHOLD:
        return []
    sig = ("spooky_shape", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scene.meters["spooky_shape"] += 1
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    return ["__spooky__"]


def _r_alarm_spreads(world: World) -> list[str]:
    child = world.get("child")
    sibling = world.get("sibling")
    if child.memes["alarm"] < THRESHOLD:
        return []
    sig = ("alarm_spreads", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sibling.memes["fear"] += 1
    sibling.memes["confusion"] += 1
    return ["__alarm__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="spooky_shape", tag="perception", apply=_r_spooky_shape),
    Rule(name="alarm_spreads", tag="social", apply=_r_alarm_spreads),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def plausible(place: Place, source: Source, motion: Motion) -> bool:
    return source.id in place.afford_sources and motion.id in place.afford_motions and source.hangs


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            for motion_id, motion in MOTIONS.items():
                if plausible(place, source, motion):
                    combos.append((place_id, source_id, motion_id))
    return combos


def explain_rejection(place: Place, source: Source, motion: Motion) -> str:
    if source.id not in place.afford_sources:
        return (
            f"(No story: {source.phrase} does not belong naturally in {place.label}, "
            f"so the ghostly misunderstanding would feel forced there.)"
        )
    if motion.id not in place.afford_motions:
        return (
            f"(No story: {motion.label} is not a plausible reason for something to move in "
            f"{place.label}, so the 'ghost' would have no honest cause.)"
        )
    if not source.hangs:
        return "(No story: the chosen object does not hang or drape enough to look ghostly.)"
    return "(No story: this combination does not make a reasonable ghost-like misunderstanding.)"


def outcome_of(params: "StoryParams") -> str:
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    return RESPONSES[params.response].outcome


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_spook(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["dim_light"] = 1
    sim.get("source").meters["moving"] = 1
    propagate(sim, narrate=False)
    return {
        "looks_spooky": sim.get("scene").meters["spooky_shape"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup(world: World, child: Entity, sibling: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    sibling.memes["sleepy"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"The house had gone very still for the night. {child.id} padded past {place.approach} "
        f"while {sibling.id} followed in quiet little steps."
    )
    world.say(place.detail)
    world.say(
        f"Near the dark corner, a one-watt bulb burned with a tiny pearl-colored glow."
    )


def glimpse(world: World, child: Entity, place: Place, source: Source, motion: Motion) -> None:
    world.get("scene").attrs["place"] = place.id
    world.get("source").meters["moving"] = 1
    child.meters["dim_light"] = 1
    propagate(world, narrate=False)
    world.say(
        f"In that weak light, {source.phrase} did not look ordinary at all. {motion.spooky_line}"
    )


def inner_monologue(world: World, child: Entity) -> None:
    child.memes["thinking"] += 1
    scared = "A ghost? No... maybe. But what else could float like that?" if child.memes["fear"] >= THRESHOLD else (
        "That shape was strange, and strange things sometimes felt bigger in the dark."
    )
    brave = "If I run, it might follow me. If I look again, maybe I will know the truth."
    world.say(
        f"{child.id}'s heart gave a jump. Inside {child.pronoun('possessive')} head, "
        f"the thoughts came quick and whispery: {scared} {brave}"
    )


def choose_response(world: World, child: Entity, sibling: Entity, helper: Entity,
                    response: Response) -> None:
    if response.quiet:
        child.memes["restraint"] += 1
        world.say(
            f'{response.child_line} {child.id} reached for {helper.label_word}\'s sleeve instead of filling the hall with fear.'
        )
    else:
        child.memes["alarm"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{response.child_line} The cry bounced off the walls, and {sibling.id} froze at once.'
        )


def helper_checks(world: World, child: Entity, sibling: Entity, helper: Entity,
                  source: Source, motion: Motion, response: Response) -> None:
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    sibling.memes["trust"] += 1
    world.say(
        f"{helper.label_word.capitalize()} did not laugh and did not scold. {response.helper_intro}"
    )
    world.say(
        f"{helper.pronoun().capitalize()} lifted the lamp, and the pale shape turned back into {source.reveal_line}. "
        f"{motion.reveal_line}"
    )
    world.get("scene").meters["revealed"] += 1
    world.get("source").meters["ordinary"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    sibling.memes["relief"] += 1


def repair_if_needed(world: World, child: Entity, sibling: Entity, response: Response) -> None:
    if response.quiet:
        return
    child.memes["honesty"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'"I scared {sibling.id}," {child.id} said in a small voice. "{child.pronoun("subject").capitalize()} only looked ghostly because I did not know what I was seeing."'
    )
    world.say(
        f"{sibling.id} took a bigger breath after hearing the truth, and the hall stopped feeling full of monsters."
    )


def lesson(world: World, child: Entity, helper: Entity, value: ValueLesson) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} put a warm hand on {child.id}\'s shoulder. '
        f'"{value.lesson_line}"'
    )
    world.say(value.second_line)


def ending(world: World, child: Entity, sibling: Entity, place: Place, response: Response) -> None:
    if response.quiet:
        world.say(
            f"Soon the shadowy corner in {place.label} looked small again. {child.id} and {sibling.id} walked back to bed together, "
            f"and even the one-watt bulb seemed gentle now."
        )
    else:
        world.say(
            f"A little later, {child.id} and {sibling.id} passed {place.label} again. This time they looked twice, saw only an ordinary shape, "
            f"and the one-watt bulb no longer seemed haunted."
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, source: Source, motion: Motion, value: ValueLesson, response: Response,
         child_name: str = "Mira", child_gender: str = "girl",
         sibling_name: str = "Owen", sibling_gender: str = "boy",
         helper_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"name": child_name},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=sibling_gender,
        label=sibling_name,
        phrase=sibling_name,
        role="sibling",
        attrs={"name": sibling_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        phrase=helper_type,
        role="helper",
    ))
    scene = world.add(Entity(
        id="scene",
        type="place",
        label=place.label,
        phrase=place.label,
        tags=set(place.tags),
    ))
    source_ent = world.add(Entity(
        id="source",
        type="source",
        label=source.label,
        phrase=source.phrase,
        tags=set(source.tags),
    ))

    # Initialize meters/memes/facts read by rules before propagation.
    child.meters["dim_light"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["alarm"] = 0.0
    child.memes["thinking"] = 0.0
    child.memes["relief"] = 0.0
    sibling.memes["fear"] = 0.0
    sibling.memes["confusion"] = 0.0
    sibling.memes["relief"] = 0.0
    helper.memes["calm"] = 0.0
    source_ent.meters["moving"] = 0.0
    source_ent.meters["ordinary"] = 0.0
    scene.meters["spooky_shape"] = 0.0
    scene.meters["revealed"] = 0.0

    pred = predict_spook(world)
    world.facts["predicted_spook"] = pred["looks_spooky"]
    world.facts["predicted_fear"] = pred["fear"]

    setup(world, child, sibling, helper, place)
    world.para()
    glimpse(world, child, place, source, motion)
    inner_monologue(world, child)
    choose_response(world, child, sibling, helper, response)
    world.para()
    helper_checks(world, child, sibling, helper, source, motion, response)
    repair_if_needed(world, child, sibling, response)
    lesson(world, child, helper, value)
    world.para()
    ending(world, child, sibling, place, response)

    world.facts.update(
        child=child,
        sibling=sibling,
        helper=helper,
        place=place,
        source_cfg=source,
        source=source_ent,
        motion=motion,
        value=value,
        response=response,
        outcome=response.outcome,
        alarmed_sibling=sibling.memes["fear"] >= THRESHOLD,
        revealed=scene.meters["revealed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(
        id="attic",
        label="the attic stairs",
        approach="the attic stairs",
        detail="Above them, old floorboards gave a sleepy creak, and the rafters kept pockets of shadow that looked deeper than they were.",
        afford_sources={"sheet", "coat"},
        afford_motions={"breeze", "cat"},
        tags={"attic", "shadow"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        approach="the upstairs hallway",
        detail="The long hallway carried every tiny sound, so even the hush of cloth seemed important.",
        afford_sources={"coat", "mop"},
        afford_motions={"breeze", "drip"},
        tags={"hallway", "shadow"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        approach="the back porch door",
        detail="On the other side of the glass, the porch boards shone dull and silver, and the night pressed close around them.",
        afford_sources={"sheet", "mop"},
        afford_motions={"breeze", "cat"},
        tags={"porch", "night"},
    ),
}

SOURCES = {
    "sheet": Source(
        id="sheet",
        label="sheet",
        phrase="a bedsheet hung over the clothesline",
        ordinary_name="bedsheet",
        reveal_line="a plain bedsheet drying where someone had left it",
        hangs=True,
        pale=True,
        tags={"cloth", "white"},
    ),
    "coat": Source(
        id="coat",
        label="coat",
        phrase="a pale raincoat hanging from a hook",
        ordinary_name="raincoat",
        reveal_line="a pale raincoat with one sleeve turned inside out",
        hangs=True,
        pale=True,
        tags={"coat", "white"},
    ),
    "mop": Source(
        id="mop",
        label="mop",
        phrase="an old mop standing beside the wall with a towel over it",
        ordinary_name="mop",
        reveal_line="an old mop with a towel drooping over the handle",
        hangs=True,
        pale=True,
        tags={"mop", "white"},
    ),
}

MOTIONS = {
    "breeze": Motion(
        id="breeze",
        label="a little breeze",
        spooky_line="The cloth lifted and dipped as if it were breathing all by itself.",
        reveal_line="A little breeze from the loose window had been stirring it the whole time.",
        tags={"breeze", "air"},
    ),
    "cat": Motion(
        id="cat",
        label="the cat brushing past",
        spooky_line="Now and then it jerked sideways in small, sudden hops that made it seem eager to come closer.",
        reveal_line="Their cat had been slipping underneath it and brushing it with a curious back.",
        tags={"cat", "animal"},
    ),
    "drip": Motion(
        id="drip",
        label="water dripping nearby",
        spooky_line="Each soft drip made the shape twitch and shiver in the dim glow.",
        reveal_line="Water had been dripping from a leaky umbrella stand and nudging the hanging cloth.",
        tags={"water", "drip"},
    ),
}

VALUES = {
    "honesty": ValueLesson(
        id="honesty",
        title="honesty",
        lesson_line="When we are afraid, telling the truth matters more than telling the biggest story.",
        second_line="The best brave words are the truest ones, even when your cheeks feel hot.",
        tags={"honesty"},
    ),
    "kindness": ValueLesson(
        id="kindness",
        title="kindness",
        lesson_line="If something scares you, ask for help before you pass the fright to someone smaller.",
        second_line="Kind hearts do not toss fear around like a ball; they carry it carefully until it can be understood.",
        tags={"kindness"},
    ),
    "courage": ValueLesson(
        id="courage",
        title="courage",
        lesson_line="Real courage is not pretending you are never scared; it is looking twice and asking wisely.",
        second_line="Once the truth was found, the dark corner lost its power to boss anyone's heart around.",
        tags={"courage"},
    ),
}

RESPONSES = {
    "whisper_help": Response(
        id="whisper_help",
        label="whisper for help",
        quiet=True,
        child_line='"Grandma... please come look,"',
        helper_intro="Grandma came close with the little lamp, moving slowly so the shadows would not jump.",
        outcome="calm_reveal",
        tags={"ask_help", "calm"},
    ),
    "shout_ghost": Response(
        id="shout_ghost",
        label="shout ghost",
        quiet=False,
        child_line='"Ghost!"',
        helper_intro="Grandma gathered both children close first, then stepped forward with the little lamp.",
        outcome="spread_scare",
        tags={"alarm", "honesty"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Ivy", "Tessa", "Eva", "June", "Clara"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Eli", "Jude", "Noah", "Sam"]

HELPERS = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    source: str
    motion: str
    value: str
    response: str
    child_name: str
    child_gender: str
    sibling_name: str
    sibling_gender: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "watt": [
        (
            "What is a watt?",
            "A watt is a way to talk about how much power a light uses. A one-watt bulb is very dim, so it can make shadows look bigger and stranger."
        )
    ],
    "shadow": [
        (
            "Why can shadows look scary at night?",
            "In dim light, your eyes do not catch as many details. Then an ordinary shape can seem mysterious until you look more closely."
        )
    ],
    "breeze": [
        (
            "Why does cloth move when a breeze touches it?",
            "Moving air can push light cloth very easily. That makes a sheet or coat sway and flap even when nobody is touching it."
        )
    ],
    "honesty": [
        (
            "Why is honesty important when you feel scared?",
            "Honesty helps other people understand what really happened. That makes it easier to solve the problem instead of spreading confusion."
        )
    ],
    "kindness": [
        (
            "What does kindness mean when someone is frightened?",
            "Kindness means helping the scared person feel safer, not making the fear bigger. A calm voice and careful truth can help a lot."
        )
    ],
    "courage": [
        (
            "What is real courage?",
            "Real courage is doing the wise thing even while you feel afraid. Sometimes that means asking for help and checking the truth."
        )
    ],
    "ask_help": [
        (
            "What should a child do if something in the dark feels scary?",
            "Pause and ask a trusted grown-up to look with you. Getting help is a smart and brave choice."
        )
    ],
    "cat": [
        (
            "Why can a cat make strange shadows?",
            "A cat can slip under cloth or brush past hanging things very quietly. In dim light, those little movements can look much bigger than they really are."
        )
    ],
    "water": [
        (
            "Can a drip make something move?",
            "Yes. A small drip can tap or nudge something light again and again, making it twitch in a way that looks odd."
        )
    ],
}
KNOWLEDGE_ORDER = ["watt", "shadow", "breeze", "cat", "water", "ask_help", "honesty", "kindness", "courage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    place = f["place"]
    source = f["source_cfg"]
    value = f["value"]
    response = f["response"]
    if response.quiet:
        ending = "asks for help quietly before the fear spreads"
    else:
        ending = "shouts first, then learns to tell the truth and calm someone smaller"
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "watt" and ends with a misunderstanding being explained.',
        f"Tell a spooky-but-safe story where {child.label} mistakes {source.ordinary_name} for a ghost near {place.label}, thinks worried thoughts inside {child.pronoun('possessive')} head, and learns about {value.title}.",
        f"Write a child-facing ghost tale where {child.label} and {sibling.label} see a dim shape in the house, and the child {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    motion = f["motion"]
    value = f["value"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {sibling.label}, and their {helper.label_word}. {child.label} is the one who first thinks the shape might be a ghost."
        ),
        (
            "Why did the shape look like a ghost?",
            f"It was seen in the weak glow of a one-watt bulb, so the details were hard to see. {motion.reveal_line}"
        ),
        (
            f"What was {child.label} thinking when {child.pronoun('subject')} saw the shape?",
            f"{child.label} felt afraid and wondered if the shape might be a ghost. Inside {child.pronoun('possessive')} head, {child.pronoun('subject')} also knew that looking again might reveal the truth."
        ),
    ]
    if response.quiet:
        qa.append(
            (
                f"What did {child.label} do when {child.pronoun('subject')} felt scared?",
                f"{child.label} whispered for {helper.label_word}'s help instead of shouting. That kept the fear from leaping straight into {sibling.label}'s heart."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.label}'s choice affect {sibling.label}?",
                f"When {child.label} shouted, {sibling.label} became frightened too. Later, telling the truth helped mend that moment because everyone could see the shape was ordinary."
            )
        )
    qa.append(
        (
            "What was the ghost really?",
            f"It was {source.reveal_line}. The moving came from an ordinary cause, not from anything magical."
        )
    )
    qa.append(
        (
            "What did the child learn?",
            f"{value.lesson_line} The story shows that fear grows in the dark, but it shrinks when people look carefully and speak truthfully."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the dark place feeling small again instead of haunted. The final image proves what changed: the same one-watt bulb was still there, but it no longer fooled anyone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"watt"} | set(f["place"].tags) | set(f["source_cfg"].tags) | set(f["motion"].tags) | set(f["value"].tags) | set(f["response"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="attic",
        source="sheet",
        motion="breeze",
        value="courage",
        response="whisper_help",
        child_name="Mira",
        child_gender="girl",
        sibling_name="Owen",
        sibling_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        place="hallway",
        source="coat",
        motion="drip",
        value="honesty",
        response="shout_ghost",
        child_name="Theo",
        child_gender="boy",
        sibling_name="Ivy",
        sibling_gender="girl",
        helper_type="father",
    ),
    StoryParams(
        place="porch",
        source="mop",
        motion="cat",
        value="kindness",
        response="whisper_help",
        child_name="Lena",
        child_gender="girl",
        sibling_name="Milo",
        sibling_gender="boy",
        helper_type="aunt",
    ),
    StoryParams(
        place="attic",
        source="coat",
        motion="cat",
        value="kindness",
        response="shout_ghost",
        child_name="June",
        child_gender="girl",
        sibling_name="Finn",
        sibling_gender="boy",
        helper_type="grandfather",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
plausible(P,S,M) :- place(P), source(S), motion(M), allows_source(P,S), allows_motion(P,M), hangs(S).

outcome(calm_reveal) :- chosen_response(R), quiet(R).
outcome(spread_scare) :- chosen_response(R), noisy(R), not outcome(calm_reveal).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sid in sorted(place.afford_sources):
            lines.append(asp.fact("allows_source", place_id, sid))
        for mid in sorted(place.afford_motions):
            lines.append(asp.fact("allows_motion", place_id, mid))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.hangs:
            lines.append(asp.fact("hangs", source_id))
    for motion_id in MOTIONS:
        lines.append(asp.fact("motion", motion_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        if response.quiet:
            lines.append(asp.fact("quiet", response_id))
        else:
            lines.append(asp.fact("noisy", response_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_response", params.response)
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

    cases = list(CURATED)
    for seed in range(25):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError as err:
            rc = 1
            print("resolve_params failed during verification:", err)
            break
        params.seed = seed
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a ghostly misunderstanding in a dim house corner."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--motion", choices=MOTIONS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.motion:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        motion = MOTIONS[args.motion]
        if not plausible(place, source, motion):
            raise StoryError(explain_rejection(place, source, motion))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.source is None or c[1] == args.source)
        and (args.motion is None or c[2] == args.motion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, motion_id = rng.choice(sorted(combos))
    value_id = args.value or rng.choice(sorted(VALUES))
    response_id = args.response or rng.choice(sorted(RESPONSES))
    helper_type = args.helper or rng.choice(HELPERS)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    sibling_name = args.sibling_name or _pick_name(rng, sibling_gender, avoid=child_name)

    return StoryParams(
        place=place_id,
        source=source_id,
        motion=motion_id,
        value=value_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.motion not in MOTIONS:
        raise StoryError(f"(No story: unknown motion '{params.motion}'.)")
    if params.value not in VALUES:
        raise StoryError(f"(No story: unknown value '{params.value}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper_type}'.)")
    if not plausible(PLACES[params.place], SOURCES[params.source], MOTIONS[params.motion]):
        raise StoryError(explain_rejection(PLACES[params.place], SOURCES[params.source], MOTIONS[params.motion]))

    world = tell(
        place=PLACES[params.place],
        source=SOURCES[params.source],
        motion=MOTIONS[params.motion],
        value=VALUES[params.value],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        sibling_name=params.sibling_name,
        sibling_gender=params.sibling_gender,
        helper_type=params.helper_type,
    )

    story_text = world.render()
    story_text = story_text.replace("child", params.child_name)
    story_text = story_text.replace("sibling", params.sibling_name)

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
        print(asp_program("", "#show plausible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, motion) combos:\n")
        for place, source, motion in combos:
            print(f"  {place:8} {source:6} {motion}")
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
                f"### {p.child_name} at {p.place}: {p.source} + {p.motion} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
