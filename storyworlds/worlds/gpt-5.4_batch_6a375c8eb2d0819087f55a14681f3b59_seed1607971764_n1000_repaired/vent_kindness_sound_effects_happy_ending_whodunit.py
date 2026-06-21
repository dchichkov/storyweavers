#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py
================================================================================

A standalone story world for a tiny child-facing whodunit: something small goes
missing, a suspicious sound comes from a vent, and a kind investigation solves
the mystery without blaming anyone.

Core premise
------------
Two children are enjoying a shared place when one child's treasured small item
goes missing. For a moment it looks as if the nearby friend may have taken it.
But the helper notices a sound -- clink, tap, or flutter -- coming from the vent.
They follow the clue kindly, ask questions instead of accusing, and a grown-up
uses the right tool to open or reach into the vent. The missing thing is found,
everyone feels relieved, and the ending image proves what changed: the children
play together again, now a little more gentle and trusting.

Reasonableness gate
-------------------
Not every item makes sense in a vent mystery. This world only tells stories when:
- the item is small enough to slip through a vent,
- the item makes an audible clue sound in that setting,
- and the chosen retrieval tool can actually retrieve that kind of item.

The Python gate and the inline ASP twin both enforce those constraints.

Run it
------
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py --item bell
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py --tool magnet
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py --all
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/vent_kindness_sound_effects_happy_ending_whodunit.py --verify
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
    small_enough: bool = False
    metal: bool = False
    paperlike: bool = False
    soft: bool = False
    vent_open: bool = False
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "janitor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher": "teacher",
            "librarian": "librarian",
            "janitor": "janitor",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
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
class Place:
    id: str
    label: str
    scene: str
    grownup_type: str
    grownup_label: str
    vent_kind: str
    hush: str
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


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    material: str
    sound_word: str
    sound_line: str
    motion_line: str
    fit_size: int
    sound_strength: int
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
class ToolCfg:
    id: str
    label: str
    works_for: set[str]
    act_line: str
    found_line: str
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
class SuspicionStyle:
    id: str
    question: str
    soften: str
    repair: str


# ---------------------------------------------------------------------------
# World + rules
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


def _r_hear_vent(world: World) -> list[str]:
    item = world.get("item")
    vent = world.get("vent")
    if item.meters["in_vent"] < THRESHOLD:
        return []
    sig = ("hear_vent",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["heard"] += 1
    for eid in ("owner", "helper"):
        world.get(eid).memes["curious"] += 1
    return ["__sound__"]


def _r_false_suspicion(world: World) -> list[str]:
    owner = world.get("owner")
    suspect = world.get("suspect")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    if item.meters["heard"] >= THRESHOLD:
        return []
    sig = ("suspicion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    suspect.memes["hurt"] += 1
    return []


def _r_kindness(world: World) -> list[str]:
    helper = world.get("helper")
    owner = world.get("owner")
    suspect = world.get("suspect")
    if helper.memes["kind_action"] < THRESHOLD:
        return []
    sig = ("kindness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["calm"] += 1
    suspect.memes["relief"] += 1
    helper.memes["pride"] += 1
    return []


def _r_retrieved(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("retrieved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["in_vent"] = 0.0
    owner = world.get("owner")
    helper = world.get("helper")
    suspect = world.get("suspect")
    owner.memes["relief"] += 1
    helper.memes["joy"] += 1
    suspect.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hear_vent", tag="physical", apply=_r_hear_vent),
    Rule(name="false_suspicion", tag="social", apply=_r_false_suspicion),
    Rule(name="kindness", tag="social", apply=_r_kindness),
    Rule(name="retrieved", tag="physical", apply=_r_retrieved),
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
# Constraints
# ---------------------------------------------------------------------------
def fits_vent(item: ItemCfg) -> bool:
    return item.fit_size <= 2


def audible_clue(item: ItemCfg) -> bool:
    return item.sound_strength >= 1


def tool_works(tool: ToolCfg, item: ItemCfg) -> bool:
    return item.material in tool.works_for


def valid_story(place: Place, item: ItemCfg, tool: ToolCfg) -> bool:
    return fits_vent(item) and audible_clue(item) and tool_works(tool, item)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if valid_story(place, item, tool):
                    combos.append((place_id, item_id, tool_id))
    return combos


def explain_rejection(item: ItemCfg, tool: Optional[ToolCfg] = None) -> str:
    if not fits_vent(item):
        return (
            f"(No story: {item.phrase} is too big to slip into a vent, so there is "
            f"no honest vent mystery to solve. Pick a smaller item.)"
        )
    if not audible_clue(item):
        return (
            f"(No story: {item.phrase} would not make a clue anyone could hear, "
            f"so the whodunit has no fair sound trail to follow.)"
        )
    if tool is not None and not tool_works(tool, item):
        return (
            f"(No story: {tool.label} cannot retrieve {item.phrase}. Choose a tool "
            f"that really works for a {item.material} item.)"
        )
    return "(No story: this combination does not make a fair vent mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_clue(world: World) -> dict:
    sim = world.copy()
    sim.get("item").meters["missing"] += 1
    sim.get("item").meters["in_vent"] += 1
    propagate(sim, narrate=False)
    return {
        "heard": sim.get("item").meters["heard"] >= THRESHOLD,
        "sound_word": sim.facts["item_cfg"].sound_word,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, owner: Entity, helper: Entity, suspect: Entity, item: Entity) -> None:
    place = world.place
    world.say(
        f"After snack time, {owner.id}, {helper.id}, and {suspect.id} were in {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f"{owner.id} had brought {world.facts['item_cfg'].phrase}, and all three children took turns "
        f"admiring it like a tiny treasure."
    )


def set_mood(world: World, owner: Entity, helper: Entity) -> None:
    world.say(
        f"{helper.id} liked pretending that every ordinary corner held a little secret, "
        f"and {owner.id} laughed and said this room could hide a mystery of its own."
    )


def lose_item(world: World, owner: Entity, item: Entity) -> None:
    cfg = world.facts["item_cfg"]
    item.meters["missing"] += 1
    item.meters["in_vent"] += 1
    item.meters["slipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, while {owner.id} set {cfg.label} on the low table for one moment, "
        f"{cfg.motion_line} and disappeared."
    )
    world.say(
        f"{owner.id} blinked at the empty spot. \"My {cfg.label}! It was just here!\""
    )


def first_suspicion(world: World, owner: Entity, suspect: Entity, style: SuspicionStyle) -> None:
    owner.memes["worry"] += 1
    suspect.memes["hurt"] += 1
    world.say(
        f"For one worried second, {owner.id} looked at {suspect.id}. "
        f"\"{style.question}\""
    )


def kind_pause(world: World, helper: Entity, owner: Entity, suspect: Entity, style: SuspicionStyle) -> None:
    helper.memes["kind_action"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {helper.id} stepped in gently. \"{style.soften}\""
    )
    world.say(
        f"{suspect.id} nodded, and the hard moment softened before it could turn into blame."
    )


def hear_sound(world: World, helper: Entity) -> None:
    pred = predict_clue(world)
    world.facts["predicted_heard"] = pred["heard"]
    world.facts["predicted_sound"] = pred["sound_word"]
    item_cfg = world.facts["item_cfg"]
    helper.memes["detective"] += 1
    world.say(
        f"Just then, {helper.id} tilted {helper.pronoun('possessive')} head. "
        f"From the vent came a tiny sound: \"{item_cfg.sound_word}! {item_cfg.sound_word}!\""
    )
    world.say(item_cfg.sound_line)


def inspect_vent(world: World, owner: Entity, helper: Entity, suspect: Entity) -> None:
    vent = world.get("vent")
    for child in (owner, helper, suspect):
        child.memes["curious"] += 1
    world.say(
        f"The three children crouched beside the vent. Through the slats they saw a dim little shape below."
    )
    vent.memes["mystery"] += 1


def ask_grownup(world: World, grownup: Entity, helper: Entity) -> None:
    helper.memes["trust"] += 1
    world.say(
        f"Instead of poking fingers into the vent, {helper.id} ran to get {grownup.label_word}. "
        f"That was the detective part that also kept everyone safe."
    )


def retrieve(world: World, grownup: Entity, tool_cfg: ToolCfg, item_cfg: ItemCfg) -> None:
    vent = world.get("vent")
    item = world.get("item")
    vent.vent_open = True
    item.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} came over, listened once, and smiled. "
        f"{tool_cfg.act_line}."
    )
    world.say(tool_cfg.found_line.format(item=item_cfg.label))


def repair_feelings(world: World, owner: Entity, suspect: Entity, style: SuspicionStyle) -> None:
    owner.memes["apology"] += 1
    suspect.memes["forgiven"] += 1
    world.say(
        f"{owner.id} looked at {suspect.id} and said, \"I'm sorry I wondered about you.\""
    )
    world.say(
        f"{suspect.id} gave a small smile. \"{style.repair}\""
    )


def ending(world: World, owner: Entity, helper: Entity, suspect: Entity, item_cfg: ItemCfg) -> None:
    for child in (owner, helper, suspect):
        child.memes["joy"] += 1
        child.memes["trust"] += 1
    world.say(
        f"Soon {owner.id} was holding {owner.pronoun('possessive')} {item_cfg.label} again, and this time "
        f"{owner.pronoun()} kept it safely in {owner.pronoun('possessive')} pocket."
    )
    world.say(world.place.ending_image)
    world.say(
        f"The mystery of the vent was solved, not by blame, but by careful listening and kindness."
    )


def tell(
    place: Place,
    item_cfg: ItemCfg,
    tool_cfg: ToolCfg,
    style: SuspicionStyle,
    owner_name: str = "Mia",
    owner_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    suspect_name: str = "Zoe",
    suspect_gender: str = "girl",
) -> World:
    world = World(place)

    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=place.grownup_type,
            role="grownup",
            label=place.grownup_label,
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="item",
            label=item_cfg.label,
            role="missing_item",
            small_enough=fits_vent(item_cfg),
            metal=item_cfg.material == "metal",
            paperlike=item_cfg.material == "paper",
            soft=item_cfg.material == "cloth",
        )
    )
    vent = world.add(Entity(id="vent", type="vent", label="vent", role="vent"))

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        style=style,
        owner=owner,
        helper=helper,
        suspect=suspect,
        grownup=grownup,
        item=item,
        vent=vent,
        outcome="found",
    )

    introduce(world, owner, helper, suspect, item)
    set_mood(world, owner, helper)

    world.para()
    lose_item(world, owner, item)
    first_suspicion(world, owner, suspect, style)
    kind_pause(world, helper, owner, suspect, style)

    world.para()
    hear_sound(world, helper)
    inspect_vent(world, owner, helper, suspect)
    ask_grownup(world, grownup, helper)

    world.para()
    retrieve(world, grownup, tool_cfg, item_cfg)
    repair_feelings(world, owner, suspect, style)
    ending(world, owner, helper, suspect, item_cfg)

    world.facts["resolved_kindly"] = helper.memes["kind_action"] >= THRESHOLD
    world.facts["apology"] = owner.memes["apology"] >= THRESHOLD
    world.facts["heard_sound"] = item.meters["heard"] >= THRESHOLD
    world.facts["retrieved"] = item.meters["retrieved"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place(
        id="library",
        label="the library reading room",
        scene="Tall shelves made soft corners, and the afternoon felt hushed and cozy.",
        grownup_type="librarian",
        grownup_label="the librarian",
        vent_kind="floor vent",
        hush="Even whispers sounded extra clear there.",
        ending_image="Soon the children were back on the rug, turning pages and grinning at one another.",
        tags={"library", "vent"},
    ),
    "music_room": Place(
        id="music_room",
        label="the music room",
        scene="Little drums, scarves, and song cards waited in neat baskets by the wall.",
        grownup_type="teacher",
        grownup_label="the music teacher",
        vent_kind="wall vent",
        hush="When the room grew still, tiny sounds seemed to bounce in the air.",
        ending_image="Soon the children were tapping a gentle rhythm together, softer and friendlier than before.",
        tags={"music", "vent"},
    ),
    "art_corner": Place(
        id="art_corner",
        label="the art corner",
        scene="Paper suns and painted clouds hung above a table full of crayons and glue sticks.",
        grownup_type="teacher",
        grownup_label="the art teacher",
        vent_kind="floor vent",
        hush="The room smelled like paper and paste, and every little rustle could be heard.",
        ending_image="Soon the children were drawing smiling detectives with bright chalky swirls around them.",
        tags={"art", "vent"},
    ),
}

ITEMS = {
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="a tiny silver bell",
        material="metal",
        sound_word="clink",
        sound_line="Something bright gave another soft clink from inside the vent.",
        motion_line="it gave a small wobble, rolled across the table edge with a tiny \"clink,\" and slipped through the vent",
        fit_size=1,
        sound_strength=2,
        tags={"metal", "sound", "bell"},
    ),
    "marble": ItemCfg(
        id="marble",
        label="marble",
        phrase="a shiny blue marble",
        material="glass",
        sound_word="tik",
        sound_line="The sound came again, a neat little tik-tik as something round touched metal below.",
        motion_line="it spun away, bounced once with a \"tik,\" and dropped through the vent slats",
        fit_size=1,
        sound_strength=2,
        tags={"glass", "sound", "marble"},
    ),
    "note": ItemCfg(
        id="note",
        label="note",
        phrase="a folded paper note with a heart on it",
        material="paper",
        sound_word="frrp",
        sound_line="A tiny frrp-frrp floated up, like paper brushing the metal sides.",
        motion_line="a breeze from the vent lifted it, and it whispered \"frrp\" as it fluttered down between the slats",
        fit_size=1,
        sound_strength=1,
        tags={"paper", "sound", "note"},
    ),
    "ribbon": ItemCfg(
        id="ribbon",
        label="ribbon",
        phrase="a soft yellow hair ribbon",
        material="cloth",
        sound_word="whuff",
        sound_line="From inside came a hushy whuff, the sound of cloth catching and slipping again.",
        motion_line="a curious puff of air twitched it, and it slid with a soft \"whuff\" into the vent",
        fit_size=1,
        sound_strength=1,
        tags={"cloth", "sound", "ribbon"},
    ),
    "block": ItemCfg(
        id="block",
        label="block",
        phrase="a chunky wooden block",
        material="wood",
        sound_word="thunk",
        sound_line="But this world does not use the block because it would not fit fairly into the vent mystery.",
        motion_line="it tipped toward the vent",
        fit_size=4,
        sound_strength=2,
        tags={"wood"},
    ),
}

TOOLS = {
    "magnet": ToolCfg(
        id="magnet",
        label="a magnet wand",
        works_for={"metal"},
        act_line="She fetched a magnet wand and lowered it through the loosened vent cover",
        found_line="Up came the {item}, swinging with one last merry clink.",
        tags={"magnet"},
    ),
    "grabber": ToolCfg(
        id="grabber",
        label="a long grabber tool",
        works_for={"glass", "cloth"},
        act_line="He unscrewed the vent cover a little and reached in with a long grabber tool",
        found_line="After one careful pinch, out came the {item}, safe and dusty but not lost anymore.",
        tags={"grabber"},
    ),
    "paper_hook": ToolCfg(
        id="paper_hook",
        label="a little paper hook",
        works_for={"paper"},
        act_line="She loosened the vent cover and slipped in a bent paper hook very carefully",
        found_line="The {item} caught on the hook and slid back up with a soft frrp.",
        tags={"paper_hook"},
    ),
}

STYLES = {
    "gentle": SuspicionStyle(
        id="gentle",
        question="Did you pick it up?",
        soften="Let's be detectives first. We can look for clues before we guess.",
        repair="It's all right. You were scared because it mattered to you.",
    ),
    "worried": SuspicionStyle(
        id="worried",
        question="Was it you? I can't find it anywhere.",
        soften="Wait. A good mystery needs clues, not blaming.",
        repair="I'm glad you asked nicely in the end.",
    ),
    "careful": SuspicionStyle(
        id="careful",
        question="Did you maybe move it by accident?",
        soften="Let's slow down and listen. Kind detectives notice before they accuse.",
        repair="Thank you for saying sorry. Friends can fix mix-ups together.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Noah", "Finn", "Jack"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    style: str
    owner_name: str
    owner_gender: str
    helper_name: str
    helper_gender: str
    suspect_name: str
    suspect_gender: str
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
    "vent": [(
        "What is a vent?",
        "A vent is an opening that lets air move in or out of a room. Some vents have slats or a cover, so small things can sometimes slip near them."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet can pull some kinds of metal without using fingers. That is why a magnet can help pick up certain lost things safely."
    )],
    "grabber": [(
        "What is a grabber tool?",
        "A grabber tool is a long tool that can pinch and hold something far away. Grown-ups use it to reach where hands should not go."
    )],
    "paper_hook": [(
        "What is a hook used for?",
        "A small hook can catch the edge of something light, like paper. It helps pull the thing back carefully."
    )],
    "sound": [(
        "Why can sound help solve a mystery?",
        "A sound tells you that something is moving or bumping somewhere. Listening carefully can help you find where the missing thing really went."
    )],
    "kindness": [(
        "Why is kindness important in a mystery?",
        "Kindness helps people slow down and listen instead of blaming someone right away. That makes it easier to solve the problem and keep everyone feeling safe."
    )],
    "apology": [(
        "What does an apology do?",
        "An apology tells someone you know you hurt their feelings and want to make things better. It can help friends trust each other again."
    )],
}
KNOWLEDGE_ORDER = ["vent", "sound", "kindness", "magnet", "grabber", "paper_hook", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    helper = f["helper"]
    place = f["place"]
    item = f["item_cfg"]
    return [
        f'Write a short whodunit story for a 3-to-5-year-old that includes the word "vent", has a happy ending, and uses kindness to solve the mystery.',
        f"Tell a gentle mystery set in {place.label} where {owner.id} loses {item.phrase}, {helper.id} notices a sound clue, and the children solve it without blaming anyone.",
        f'Write a child-facing detective story with sound effects like "{item.sound_word}" and a kind apology at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    helper = f["helper"]
    suspect = f["suspect"]
    grownup = f["grownup"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id}, {helper.id}, and {suspect.id} in {place.label}. They become little detectives when {owner.id}'s {item_cfg.label} goes missing."
        ),
        (
            f"Why did {owner.id} first look at {suspect.id}?",
            f"{owner.id} was worried because the {item_cfg.label} had just vanished, and {suspect.id} was nearby. For one moment, that worry felt bigger than the facts."
        ),
        (
            f"How did {helper.id} show kindness?",
            f"{helper.id} stopped the blaming and asked everyone to look for clues first. That kindness calmed the room and gave the mystery a fair chance to be solved."
        ),
        (
            "What clue solved the mystery?",
            f"The clue was the tiny sound coming from the vent: \"{item_cfg.sound_word}! {item_cfg.sound_word}!\" The sound told the children the missing thing had not been stolen at all, but had slipped into the vent."
        ),
        (
            f"How did {grownup.label_word} get the item back?",
            f"{grownup.label_word.capitalize()} used {tool_cfg.label} to reach into the vent and retrieve the {item_cfg.label}. The tool worked because it matched the kind of item that was stuck inside."
        ),
        (
            "How did the story end?",
            f"It ended happily with the {item_cfg.label} safely back in {owner.id}'s hands. {owner.id} apologized, {suspect.id} forgave {owner.pronoun('object')}, and the children played together again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vent", "sound", "kindness", "apology"}
    tags |= set(world.facts["tool_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [
            name for name, on in (
                ("small_enough", e.small_enough),
                ("metal", e.metal),
                ("paperlike", e.paperlike),
                ("soft", e.soft),
                ("vent_open", e.vent_open),
            ) if on
        ]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="library",
        item="bell",
        tool="magnet",
        style="gentle",
        owner_name="Mia",
        owner_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        suspect_name="Zoe",
        suspect_gender="girl",
    ),
    StoryParams(
        place="music_room",
        item="marble",
        tool="grabber",
        style="careful",
        owner_name="Leo",
        owner_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        suspect_name="Sam",
        suspect_gender="boy",
    ),
    StoryParams(
        place="art_corner",
        item="note",
        tool="paper_hook",
        style="worried",
        owner_name="Nora",
        owner_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        suspect_name="Ella",
        suspect_gender="girl",
    ),
    StoryParams(
        place="library",
        item="ribbon",
        tool="grabber",
        style="gentle",
        owner_name="Lucy",
        owner_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        suspect_name="Anna",
        suspect_gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
small_item(I) :- item(I), fit_size(I,S), s_limit(L), S <= L.
audible(I)    :- item(I), sound_strength(I,N), N >= 1.
compatible(T,I) :- tool(T), item(I), material(I,M), works_for(T,M).
valid(P,I,T)  :- place(P), small_item(I), audible(I), compatible(T,I).

outcome(found) :- chosen_place(P), chosen_item(I), chosen_tool(T), valid(P,I,T).
:- chosen_place(P), chosen_item(I), chosen_tool(T), not valid(P,I,T).

#show valid/3.
#show compatible/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("s_limit", 2))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("fit_size", iid, item.fit_size))
        lines.append(asp.fact("sound_strength", iid, item.sound_strength))
        lines.append(asp.fact("material", iid, item.material))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for mat in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, mat))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random param resolution at seed {s}.")
            break

    for params in cases:
        if asp_outcome(params) != "found":
            rc = 1
            print(f"MISMATCH outcome for {params}: ASP said {asp_outcome(params)}")
            break

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a kind little whodunit with a vent, sound clues, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, item, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item:
        item = ITEMS[args.item]
        if not fits_vent(item) or not audible_clue(item):
            raise StoryError(explain_rejection(item))
    if args.item and args.tool:
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not tool_works(tool, item):
            raise StoryError(explain_rejection(item, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, tool = rng.choice(sorted(combos))
    style = args.style or rng.choice(sorted(STYLES))
    owner_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    owner_name = _pick_name(rng, owner_gender, used)
    used.add(owner_name)
    helper_name = _pick_name(rng, helper_gender, used)
    used.add(helper_name)
    suspect_name = _pick_name(rng, suspect_gender, used)

    return StoryParams(
        place=place,
        item=item,
        tool=tool,
        style=style,
        owner_name=owner_name,
        owner_gender=owner_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.style not in STYLES:
        raise StoryError(f"(Invalid style: {params.style})")

    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    tool_cfg = TOOLS[params.tool]
    style = STYLES[params.style]

    if not valid_story(place, item_cfg, tool_cfg):
        raise StoryError(explain_rejection(item_cfg, tool_cfg))

    world = tell(
        place=place,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        style=style,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        suspect_name=params.suspect_name,
        suspect_gender=params.suspect_gender,
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
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place, item, tool in combos:
            print(f"  {place:12} {item:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.item} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
