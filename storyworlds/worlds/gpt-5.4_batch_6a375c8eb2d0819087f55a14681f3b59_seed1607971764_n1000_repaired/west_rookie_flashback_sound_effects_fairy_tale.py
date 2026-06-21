#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py
============================================================================

A standalone storyworld for a small fairy-tale domain:

A rookie keeper is sent to a garden in the west part of a kingdom. One magical
flower droops at twilight, and only the right hidden helper can heal it. The
helper comes only when called by the right gentle sound. The rookie remembers an
older mentor's lesson in a flashback, chooses the fitting instrument, and the
flower blooms.

The world model enforces the common-sense core:
- the place must actually be a place where that helper lives,
- the sound-tool must be the helper's preferred gentle call,
- the helper must carry the kind of gift the flower needs.

Invalid choices are rejected with clear reasons. The story text is driven by the
simulated state: worry, memory, trust, presence, gift, and bloom.

Run it
------
    python storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/west_rookie_flashback_sound_effects_fairy_tale.py --verify
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

GENTLE_MIN = 1


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
        female = {"girl", "woman", "fairy_gardener"}
        male = {"boy", "man", "wizard_gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    label: str
    scene: str
    path: str
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
class Creature:
    id: str
    label: str
    the: str
    home: str
    likes_tool: str
    gift: str
    entry: str
    motion: str
    gift_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    sound: str
    sound_word: str
    verb: str
    gentle: int
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
class Flower:
    id: str
    label: str
    the: str
    color: str
    need: str
    droop: str
    bloom_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Mentor:
    id: str
    type: str
    label: str
    relation: str
    memory_open: str
    praise: str
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
        self.facts: dict = {
            "played": False,
            "flashback_happened": False,
            "gift_arrived": False,
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


def _r_worry(world: World) -> list[str]:
    flower = world.get("flower")
    rookie = world.get("rookie")
    if flower.meters["wilt"] < THRESHOLD:
        return []
    sig = ("worry", flower.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rookie.memes["worry"] += 1
    return []


def _r_song_summons(world: World) -> list[str]:
    if not world.facts.get("played"):
        return []
    creature = world.get("creature")
    tool = world.get("tool")
    sig = ("summon", creature.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if tool.attrs.get("matches_creature") and tool.attrs.get("gentle_ok"):
        creature.meters["present"] += 1
        creature.memes["trust"] += 1
        return ["__arrive__"]
    creature.memes["fear"] += 1
    return ["__hide__"]


def _r_gift(world: World) -> list[str]:
    creature = world.get("creature")
    flower = world.get("flower")
    if creature.meters["present"] < THRESHOLD:
        return []
    if creature.attrs.get("gift") != flower.attrs.get("need"):
        return []
    sig = ("gift", creature.id, flower.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["fed"] += 1
    world.facts["gift_arrived"] = True
    return []


def _r_bloom(world: World) -> list[str]:
    flower = world.get("flower")
    rookie = world.get("rookie")
    if flower.meters["fed"] < THRESHOLD:
        return []
    sig = ("bloom", flower.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flower.meters["bloom"] += 1
    flower.meters["wilt"] = 0.0
    rookie.memes["relief"] += 1
    rookie.memes["confidence"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="song_summons", tag="physical", apply=_r_song_summons),
    Rule(name="gift", tag="physical", apply=_r_gift),
    Rule(name="bloom", tag="physical", apply=_r_bloom),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent not in {"__arrive__", "__hide__"}:
                world.say(sent)
    return produced


def helper_available(setting: Setting, creature: Creature) -> bool:
    return creature.id in setting.affords


def matching_tool(tool: Tool, creature: Creature) -> bool:
    return tool.id == creature.likes_tool and tool.gentle >= GENTLE_MIN


def flower_can_be_helped(flower: Flower, creature: Creature) -> bool:
    return flower.need == creature.gift


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for creature_id, creature in CREATURES.items():
            if not helper_available(setting, creature):
                continue
            for flower_id, flower in FLOWERS.items():
                if not flower_can_be_helped(flower, creature):
                    continue
                for tool_id, tool in TOOLS.items():
                    if matching_tool(tool, creature):
                        combos.append((place_id, creature_id, flower_id, tool_id))
    return combos


def explain_place(setting: Setting, creature: Creature) -> str:
    return (
        f"(No story: {creature.the} does not live in {setting.label}. "
        f"The helper must truly belong to that west place before it can answer a call.)"
    )


def explain_tool(tool: Tool, creature: Creature) -> str:
    if tool.gentle < GENTLE_MIN:
        return (
            f"(No story: {tool.label} is too harsh for {creature.the}. "
            f"This fairy-tale world only accepts gentle calls for shy magical helpers.)"
        )
    want = TOOLS[creature.likes_tool].label
    return (
        f"(No story: {creature.the} listens for {want}, not {tool.label}. "
        f"The wrong sound would not honestly bring the helper near.)"
    )


def explain_flower(flower: Flower, creature: Creature) -> str:
    return (
        f"(No story: {creature.the} carries {creature.gift}, but {flower.the} needs "
        f"{flower.need}. The helper's gift must match the flower's need.)"
    )


def predict_help(world: World) -> dict:
    sim = world.copy()
    sim.facts["played"] = True
    propagate(sim, narrate=False)
    creature = sim.get("creature")
    flower = sim.get("flower")
    return {
        "helper_arrives": creature.meters["present"] >= THRESHOLD,
        "flower_blooms": flower.meters["bloom"] >= THRESHOLD,
    }


def opening(world: World, rookie: Entity, mentor: Entity, flower: Flower) -> None:
    world.say(
        f"At the far west edge of the kingdom, in {world.setting.label}, there was a small path of white stones."
    )
    world.say(
        f"That evening {rookie.id}, a rookie keeper with careful hands and a hopeful heart, was trusted to watch {flower.the} all alone for the first time."
    )
    world.say(world.setting.scene)
    world.say(
        f"But when twilight laid purple shadows on the leaves, {flower.the} began to {flower.droop}."
    )
    world.say(
        f"{rookie.id} thought of {mentor.label}, who had said the garden listened back when someone was gentle enough."
    )


def worry(world: World, rookie: Entity, flower: Flower) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{rookie.id} knelt beside {flower.the} and touched one cool leaf. It felt as if the whole little garden were holding its breath."
    )
    if rookie.memes["worry"] >= THRESHOLD:
        world.say(
            f'"Oh dear," {rookie.pronoun()} whispered. "{flower.The} cannot wait until morning."'
        )


def flashback(world: World, rookie: Entity, mentor: Mentor, creature: Creature, tool: Tool) -> None:
    rookie.memes["memory"] += 1
    rookie.memes["courage"] += 1
    world.facts["flashback_happened"] = True
    world.say(
        f"Then a breeze moved through the reeds with a soft hush, and all at once a flashback came to {rookie.id}."
    )
    world.say(
        f"{mentor.memory_open} {mentor.label} had bent low and said, "
        f'"When the night garden is troubled, do not shout at it. Call {creature.the} with {tool.phrase}, and let the sound be kind."'
    )
    world.say(
        f"Back in the present, {rookie.id} stood up straighter. Being a rookie no longer felt quite the same as being helpless."
    )


def choose_tool(world: World, rookie: Entity, tool: Tool, creature: Creature) -> None:
    tool_ent = world.get("tool")
    tool_ent.attrs["matches_creature"] = matching_tool(tool, creature)
    tool_ent.attrs["gentle_ok"] = tool.gentle >= GENTLE_MIN
    world.say(
        f"From a hook on the ivy wall, {rookie.id} took {tool.phrase}. {rookie.pronoun().capitalize()} remembered to lift it slowly, as if even the metal should not be startled."
    )


def play_sound(world: World, rookie: Entity, tool: Tool, creature: Creature) -> None:
    world.facts["played"] = True
    produced = propagate(world, narrate=False)
    world.say(
        f"{rookie.id} {tool.verb}. {tool.sound} went across the west garden and slipped between the branches."
    )
    if "__arrive__" in produced:
        world.say(
            f"For one tiny moment nothing happened, and then {creature.entry}."
        )
    else:
        world.say(
            f"The sound faded away, and only the leaves answered."
        )


def arrival(world: World, creature: Creature) -> None:
    creature_ent = world.get("creature")
    if creature_ent.meters["present"] < THRESHOLD:
        return
    world.say(
        f"{creature.The} {creature.motion}. Moonlight seemed to gather around it as if the night itself were glad to see it."
    )


def gift_and_bloom(world: World, rookie: Entity, creature: Creature, flower: Flower) -> None:
    flower_ent = world.get("flower")
    if flower_ent.meters["bloom"] < THRESHOLD:
        return
    world.say(
        creature.gift_line
    )
    world.say(
        f"The gift touched {flower.the}, and at once {flower.bloom_line}"
    )
    world.say(
        f"{rookie.id} laughed out loud, not with the shaky laugh of before, but with the bright laugh of someone who had truly helped."
    )


def ending(world: World, rookie: Entity, mentor: Mentor, flower: Flower, creature: Creature) -> None:
    flower_ent = world.get("flower")
    if flower_ent.meters["bloom"] >= THRESHOLD:
        world.say(
            f"When {mentor.label} returned, {rookie.id} was still standing beside {flower.the}, and the whole west garden shone softly around them."
        )
        world.say(
            f'{mentor.praise} From then on, whenever anyone called {rookie.id} a rookie, the word sounded warm instead of small.'
        )
        world.say(
            f"And every time the wind passed through {world.setting.path}, it seemed to whisper {creature.the}'s answer back again."
        )


def tell(
    setting: Setting,
    creature_cfg: Creature,
    flower_cfg: Flower,
    tool_cfg: Tool,
    rookie_name: str = "Mira",
    rookie_type: str = "girl",
    mentor_cfg: Optional[Mentor] = None,
) -> World:
    mentor_cfg = mentor_cfg or next(iter(MENTORS.values()))
    world = World(setting)
    rookie = world.add(Entity(id=rookie_name, kind="character", type=rookie_type, role="rookie", label=rookie_name))
    mentor_type = mentor_cfg.type
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, role="mentor", label=mentor_cfg.label))
    creature = world.add(Entity(id="creature", kind="thing", type="creature", role="helper", label=creature_cfg.label))
    flower = world.add(Entity(id="flower", kind="thing", type="flower", role="flower", label=flower_cfg.label))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", role="tool", label=tool_cfg.label))

    rookie.memes["hope"] = 1.0
    rookie.memes["worry"] = 0.0
    rookie.memes["memory"] = 0.0
    rookie.memes["confidence"] = 0.0
    creature.meters["present"] = 0.0
    creature.memes["trust"] = 0.0
    creature.memes["fear"] = 0.0
    creature.attrs["gift"] = creature_cfg.gift
    flower.meters["wilt"] = 1.0
    flower.meters["fed"] = 0.0
    flower.meters["bloom"] = 0.0
    flower.attrs["need"] = flower_cfg.need
    tool.attrs["matches_creature"] = False
    tool.attrs["gentle_ok"] = tool_cfg.gentle >= GENTLE_MIN

    world.facts.update(
        rookie=rookie,
        mentor=mentor,
        mentor_cfg=mentor_cfg,
        creature_cfg=creature_cfg,
        flower_cfg=flower_cfg,
        tool_cfg=tool_cfg,
        place=setting,
    )

    opening(world, rookie, mentor, flower_cfg)
    world.para()
    worry(world, rookie, flower_cfg)
    flashback(world, rookie, mentor_cfg, creature_cfg, tool_cfg)
    choose_tool(world, rookie, tool_cfg, creature_cfg)
    world.para()
    play_sound(world, rookie, tool_cfg, creature_cfg)
    arrival(world, creature_cfg)
    gift_and_bloom(world, rookie, creature_cfg, flower_cfg)
    world.para()
    ending(world, rookie, mentor_cfg, flower_cfg, creature_cfg)

    world.facts["resolved"] = world.get("flower").meters["bloom"] >= THRESHOLD
    world.facts["helper_arrived"] = world.get("creature").meters["present"] >= THRESHOLD
    return world


SETTINGS = {
    "west_glen": Setting(
        id="west_glen",
        label="the west glen",
        scene="Blue moss covered the roots there, and little lamps of foxfire blinked between the ferns.",
        path="the fern path",
        affords={"dewbird", "ember_moth"},
        tags={"west", "garden"},
    ),
    "west_orchard": Setting(
        id="west_orchard",
        label="the west orchard",
        scene="Old pear trees leaned close together there, and silver dew hung on every twig like tiny glass beads.",
        path="the pear-tree path",
        affords={"dewbird", "brook_turtle"},
        tags={"west", "orchard"},
    ),
    "west_pond": Setting(
        id="west_pond",
        label="the west pond",
        scene="Rushes made green curtains there, and the water held one long stripe of moonlight in its quiet middle.",
        path="the stepping-stone path",
        affords={"brook_turtle", "ember_moth"},
        tags={"west", "pond"},
    ),
}

CREATURES = {
    "dewbird": Creature(
        id="dewbird",
        label="dewbird",
        the="the dewbird",
        home="pear branches",
        likes_tool="silver_bell",
        gift="dew",
        entry="a white bird no bigger than a mitten fluttered down from the pear branches",
        motion="hopped near with one shining drop balanced in its beak",
        gift_line="Very gently, the dewbird tipped a pearl of dew onto the tired petals.",
        tags={"dewbird", "bell", "dew"},
    ),
    "ember_moth": Creature(
        id="ember_moth",
        label="ember moth",
        the="the ember moth",
        home="lantern flowers",
        likes_tool="willow_flute",
        gift="sunseed",
        entry="a warm gold flutter woke among the lantern flowers and an ember moth drifted out",
        motion="circled once over the path and let a glowing seed fall from its wings",
        gift_line="The ember moth brushed the blossom with a sunseed bright as a crumb of dawn.",
        tags={"moth", "flute", "sunseed"},
    ),
    "brook_turtle": Creature(
        id="brook_turtle",
        label="brook turtle",
        the="the brook turtle",
        home="the rushes",
        likes_tool="shell_rattle",
        gift="songdust",
        entry="the rushes parted with a sleepy swish, and a brook turtle pushed through them",
        motion="came slowly forward with sparkling songdust tucked in the lines of its shell",
        gift_line="The brook turtle shook loose a little trail of songdust, soft as sugar and bright as stars.",
        tags={"turtle", "rattle", "songdust"},
    ),
}

TOOLS = {
    "silver_bell": Tool(
        id="silver_bell",
        label="silver bell",
        phrase="a silver bell",
        sound="Ding-ding! Ding-ding!",
        sound_word="ding",
        verb="rang the bell twice",
        gentle=2,
        tags={"bell", "sound"},
    ),
    "willow_flute": Tool(
        id="willow_flute",
        label="willow flute",
        phrase="a willow flute",
        sound="Tee-oo! Tee-oo!",
        sound_word="tee-oo",
        verb="blew a willow-soft note",
        gentle=2,
        tags={"flute", "sound"},
    ),
    "shell_rattle": Tool(
        id="shell_rattle",
        label="shell rattle",
        phrase="a shell rattle",
        sound="Shrr-shrr! Shrr-shrr!",
        sound_word="shrr",
        verb="shook the shell rattle in a slow rhythm",
        gentle=2,
        tags={"rattle", "sound"},
    ),
    "copper_horn": Tool(
        id="copper_horn",
        label="copper horn",
        phrase="a copper horn",
        sound="BRAAAM! BRAAAM!",
        sound_word="braaam",
        verb="blew the copper horn",
        gentle=0,
        tags={"horn", "sound"},
    ),
}

FLOWERS = {
    "moon_rose": Flower(
        id="moon_rose",
        label="moon rose",
        the="the moon rose",
        color="silver",
        need="dew",
        droop="curl and bow its silver head",
        bloom_line="the moon rose unfolded again, bright and pale and sweet, until it looked as if a star had opened in the hedge.",
        tags={"flower", "dew"},
    ),
    "sun_tulip": Flower(
        id="sun_tulip",
        label="sun tulip",
        the="the sun tulip",
        color="gold",
        need="sunseed",
        droop="fold its golden cup shut tight",
        bloom_line="the sun tulip opened in a warm golden glow, as though morning had come early just for that one bed of flowers.",
        tags={"flower", "sunseed"},
    ),
    "hush_violet": Flower(
        id="hush_violet",
        label="hush violet",
        the="the hush violet",
        color="purple",
        need="songdust",
        droop="sink low and lose its little singing shimmer",
        bloom_line="the hush violet lifted itself and began its tiny evening hum again, a gentle tune that made the air feel kinder.",
        tags={"flower", "songdust"},
    ),
}

MENTORS = {
    "elm_fairy": Mentor(
        id="elm_fairy",
        type="fairy_gardener",
        label="Old Talla",
        relation="elder fairy gardener",
        memory_open="In the spring before this night",
        praise='"You listened well," Old Talla said, smiling. "That is how true keepers begin."',
        tags={"mentor"},
    ),
    "moss_wizard": Mentor(
        id="moss_wizard",
        type="wizard_gardener",
        label="Master Rowan",
        relation="old garden wizard",
        memory_open="On the first morning of training",
        praise='"You did not hurry past the lesson," Master Rowan said. "That is why the flower trusted your hands."',
        tags={"mentor"},
    ),
}

GIRL_NAMES = ["Mira", "Elin", "Tessa", "Luma", "Nia", "Suri", "Wren", "Ayla"]
BOY_NAMES = ["Ivo", "Tobin", "Ellis", "Rowe", "Perrin", "Nilo", "Cas", "Aren"]


@dataclass
class StoryParams:
    place: str
    creature: str
    flower: str
    tool: str
    name: str
    gender: str
    mentor: str
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


CURATED = [
    StoryParams(
        place="west_orchard",
        creature="dewbird",
        flower="moon_rose",
        tool="silver_bell",
        name="Mira",
        gender="girl",
        mentor="elm_fairy",
    ),
    StoryParams(
        place="west_glen",
        creature="ember_moth",
        flower="sun_tulip",
        tool="willow_flute",
        name="Ivo",
        gender="boy",
        mentor="moss_wizard",
    ),
    StoryParams(
        place="west_pond",
        creature="brook_turtle",
        flower="hush_violet",
        tool="shell_rattle",
        name="Tessa",
        gender="girl",
        mentor="elm_fairy",
    ),
    StoryParams(
        place="west_pond",
        creature="ember_moth",
        flower="sun_tulip",
        tool="willow_flute",
        name="Cas",
        gender="boy",
        mentor="moss_wizard",
    ),
    StoryParams(
        place="west_orchard",
        creature="brook_turtle",
        flower="hush_violet",
        tool="shell_rattle",
        name="Elin",
        gender="girl",
        mentor="elm_fairy",
    ),
]

KNOWLEDGE = {
    "bell": [
        (
            "What does a bell sound like?",
            "A bell makes a clear ringing sound, often something like ding-ding. In stories, a gentle bell can be a way to call someone without shouting.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a music instrument you blow into to make soft notes. Its sound can feel light and floaty, almost like wind singing.",
        )
    ],
    "rattle": [
        (
            "What is a rattle?",
            "A rattle is something you shake to make a rhythm. A soft rattle can sound like shells or seeds clicking together.",
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny water drops that gather on grass and petals when the air turns cool. In fairy tales, dew is often treated like a fresh little gift from the night.",
        )
    ],
    "sunseed": [
        (
            "What is a sunseed in a fairy tale?",
            "A sunseed is an imaginary magical seed that carries a bit of warmth and light. A fairy tale might use one to wake a flower or brighten a dark place.",
        )
    ],
    "songdust": [
        (
            "What is songdust in a fairy tale?",
            "Songdust is an imaginary sparkling dust that carries music or gentle magic. A story might use it to make something quiet sing again.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly turns to an earlier memory. It helps explain why a character understands something or makes a choice in the present.",
        )
    ],
    "west": [
        (
            "What does west mean?",
            "West is one of the directions people use to describe where something is. If a garden is in the west part of a kingdom, it is on that side of the land.",
        )
    ],
}
KNOWLEDGE_ORDER = ["flashback", "west", "bell", "flute", "rattle", "dew", "sunseed", "songdust"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rookie = f["rookie"]
    place = f["place"]
    tool = f["tool_cfg"]
    creature = f["creature_cfg"]
    flower = f["flower_cfg"]
    return [
        f'Write a short fairy tale that includes the words "west" and "rookie", uses a flashback, and includes sound effects as a magical helper is called.',
        f"Tell a gentle fairy-tale story where a rookie keeper in {place.label} remembers an older mentor's lesson and uses {tool.phrase} to call {creature.the} and save {flower.the}.",
        f"Write a bedtime story about {rookie.id}, a rookie guardian of a west garden, where a flashback helps the child solve a problem with a magical sound.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rookie = f["rookie"]
    mentor_cfg = f["mentor_cfg"]
    creature = f["creature_cfg"]
    flower = f["flower_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {rookie.id}, a rookie keeper in {place.label}. {rookie.pronoun('subject').capitalize()} has to care for {flower.the} on a difficult evening.",
        ),
        (
            f"Why was {rookie.id} worried?",
            f"{rookie.id} was worried because {flower.the} had started to {flower.droop}. If no help came soon, the flower would not stay bright through the night.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about a lesson from {mentor_cfg.label}. It reminded {rookie.id} not to shout at a troubled garden, but to use {tool.phrase} gently to call {creature.the}.",
        ),
        (
            f"How did the sound help {rookie.id}?",
            f"{rookie.id} used the right sound for {creature.the}, so the helper came instead of hiding. That mattered because {creature.the} carried exactly what {flower.the} needed.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            (
                f"How was {flower.the} saved?",
                f"{creature.The} brought {creature.gift}, and that gift healed the flower. After it touched the petals, {flower.the} bloomed again and the whole west garden changed from worried and dim to bright and alive.",
            )
        )
        qa.append(
            (
                f"Why did the word rookie feel different at the end?",
                f"At the beginning, rookie meant {rookie.id} was new and unsure. At the end, the same word felt warm because {rookie.pronoun('subject')} had listened, remembered, and truly helped.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"flashback", "west"}
    f = world.facts
    tool = f["tool_cfg"]
    creature = f["creature_cfg"]
    flower = f["flower_cfg"]
    for source in (tool.tags, creature.tags, flower.tags):
        for tag in source:
            if tag in KNOWLEDGE:
                tags.add(tag)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    shown_facts = {k: v for k, v in world.facts.items() if isinstance(v, (str, int, float, bool))}
    lines.append(f"  facts={shown_facts}")
    lines.append(f"  fired rules={sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
available(S,C) :- affords(S,C).
matching_tool(C,T) :- likes(C,T), gentle(T,G), gentle_min(M), G >= M.
gift_match(F,C) :- needs(F,G), carries(C,G).
valid(S,C,F,T) :- setting(S), creature(C), flower(F), tool(T),
                  available(S,C), matching_tool(C,T), gift_match(F,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for creature_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, creature_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("likes", creature_id, creature.likes_tool))
        lines.append(asp.fact("carries", creature_id, creature.gift))
    for flower_id, flower in FLOWERS.items():
        lines.append(asp.fact("flower", flower_id))
        lines.append(asp.fact("needs", flower_id, flower.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("gentle", tool_id, tool.gentle))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a rookie keeper in the west remembers a lesson, makes the right sound, and saves a magical flower."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include generation prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature:
        if not helper_available(SETTINGS[args.place], CREATURES[args.creature]):
            raise StoryError(explain_place(SETTINGS[args.place], CREATURES[args.creature]))
    if args.creature and args.tool:
        if not matching_tool(TOOLS[args.tool], CREATURES[args.creature]):
            raise StoryError(explain_tool(TOOLS[args.tool], CREATURES[args.creature]))
    if args.creature and args.flower:
        if not flower_can_be_helped(FLOWERS[args.flower], CREATURES[args.creature]):
            raise StoryError(explain_flower(FLOWERS[args.flower], CREATURES[args.creature]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.flower is None or combo[2] == args.flower)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creature, flower, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    return StoryParams(
        place=place,
        creature=creature,
        flower=flower,
        tool=tool,
        name=name,
        gender=gender,
        mentor=mentor,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.flower not in FLOWERS:
        raise StoryError(f"(Unknown flower: {params.flower})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mentor not in MENTORS:
        raise StoryError(f"(Unknown mentor: {params.mentor})")

    setting = SETTINGS[params.place]
    creature = CREATURES[params.creature]
    flower = FLOWERS[params.flower]
    tool = TOOLS[params.tool]

    if not helper_available(setting, creature):
        raise StoryError(explain_place(setting, creature))
    if not matching_tool(tool, creature):
        raise StoryError(explain_tool(tool, creature))
    if not flower_can_be_helped(flower, creature):
        raise StoryError(explain_flower(flower, creature))

    world = tell(
        setting=setting,
        creature_cfg=creature,
        flower_cfg=flower,
        tool_cfg=tool,
        rookie_name=params.name,
        rookie_type=params.gender,
        mentor_cfg=MENTORS[params.mentor],
    )

    pred = predict_help(world)
    world.facts["predicted_helper_arrives"] = pred["helper_arrives"]
    world.facts["predicted_flower_blooms"] = pred["flower_blooms"]

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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, flower, tool) combos:\n")
        for place, creature, flower, tool in combos:
            print(f"  {place:12} {creature:12} {flower:12} {tool}")
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
            header = f"### {p.name}: {p.place}, {p.creature}, {p.flower}, {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
