#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py
======================================================================

A standalone story world for a funny ghost-story mystery: a child hears and sees
something ghostly, gathers courage, and solves the mystery with a light and a
stick. The "ghost" is always real enough to scare someone for a moment, but the
cause is always ordinary and a little silly once the world state is uncovered.

Run it
------
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py --place attic --cause sheet_trunk
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py --light candle_lamp
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/stick_humor_mystery_to_solve_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "mother", "grandma", "aunt", "sister", "woman"}
        male = {"boy", "father", "grandpa", "uncle", "brother", "man"}
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
            "grandma": "grandma",
            "grandpa": "grandpa",
            "brother": "brother",
            "sister": "sister",
        }.get(self.type, self.type)
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
    phrase: str
    dark_word: str
    draft_word: str
    affords: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    label: str
    ghost_shape: str
    sound_line: str
    clue_line: str
    reveal_line: str
    tidy_line: str
    darkness: int
    needs_breeze: bool = False
    indoors: bool = True
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
class Light:
    id: str
    label: str
    phrase: str
    glow_line: str
    brightness: int
    sense: int
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
class Companion:
    id: str
    label: str
    type: str
    opening_line: str
    steady_line: str
    laugh_line: str
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    cause_ent = world.get("cause")
    hero = world.get("hero")
    companion = world.get("companion")
    if cause_ent.meters["moving"] < THRESHOLD and cause_ent.meters["rattling"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["mystery"] += 1
    hero.memes["fear"] += 1
    hero.memes["curiosity"] += 1
    companion.memes["curiosity"] += 1
    out.append("__spook__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    cause_ent = world.get("cause")
    light_ent = world.get("light")
    hero = world.get("hero")
    companion = world.get("companion")
    if light_ent.meters["on"] < THRESHOLD or hero.meters["near_cause"] < THRESHOLD:
        return out
    if world.facts["light_cfg"].brightness < world.facts["cause_cfg"].darkness:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cause_ent.meters["seen"] += 1
    hero.memes["focus"] += 1
    companion.memes["focus"] += 1
    out.append("__clue__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    cause_ent = world.get("cause")
    hero = world.get("hero")
    companion = world.get("companion")
    if cause_ent.meters["seen"] < THRESHOLD or hero.meters["poking"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cause_ent.meters["revealed"] += 1
    world.get("place").meters["mystery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["laughter"] += 1
    companion.memes["relief"] += 1
    companion.memes["laughter"] += 1
    out.append("__revealed__")
    return out


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="clue", tag="perception", apply=_r_clue),
    Rule(name="reveal", tag="resolution", apply=_r_reveal),
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
        for s in produced:
            if s.startswith("__"):
                continue
            world.say(s)
    return produced


def place_supports(place: Place, cause: Cause) -> bool:
    return cause.id in place.affords


def light_suffices(light: Light, cause: Cause) -> bool:
    return light.brightness >= cause.darkness


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id in sorted(place.affords):
            cause = CAUSES[cause_id]
            for light_id, light in LIGHTS.items():
                if light.sense >= 2 and light_suffices(light, cause):
                    combos.append((place_id, cause_id, light_id))
    return sorted(combos)


def explain_place_rejection(place: Place, cause: Cause) -> str:
    return (
        f"(No story: {cause.label} does not belong in {place.label}. "
        f"This world only tells mysteries where the ordinary cause fits the place.)"
    )


def explain_light_rejection(light: Light, cause: Cause) -> str:
    if light.sense < 2:
        return (
            f"(No story: {light.label} is too weak or awkward for solving a ghost mystery. "
            f"Pick a steadier light like a flashlight or lantern.)"
        )
    return (
        f"(No story: {light.label} is too dim to show what {cause.ghost_shape} really is. "
        f"Pick a brighter light.)"
    )


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["near_cause"] += 1
    sim.get("light").meters["on"] += 1
    sim.get("hero").meters["poking"] += 1
    propagate(sim, narrate=False)
    return {
        "clue": sim.get("cause").meters["seen"] >= THRESHOLD,
        "revealed": sim.get("cause").meters["revealed"] >= THRESHOLD,
    }


def opening_scene(world: World, hero: Entity, companion: Entity, place: Place) -> None:
    hero.memes["calm"] += 1
    companion.memes["calm"] += 1
    world.say(
        f"One evening, {hero.id} and {companion.label_word} were in {place.phrase}. "
        f"It was the kind of quiet that made tiny sounds seem big."
    )
    world.say(companion.attrs["opening_line"])


def first_spook(world: World, hero: Entity, cause: Cause, place: Place) -> None:
    cause_ent = world.get("cause")
    cause_ent.meters["moving"] += 1
    if cause.needs_breeze:
        cause_ent.meters["rattling"] += 1
    else:
        cause_ent.meters["rattling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something pale wobbled in the {place.dark_word}, and {cause.sound_line}. "
        f'"A ghost!" whispered {hero.id}.'
    )


def joke_and_guess(world: World, hero: Entity, companion: Entity) -> None:
    fear = world.get("hero").memes["fear"]
    extra = " even though the whisper came out squeaky" if fear >= THRESHOLD else ""
    world.say(
        f"{hero.id} grabbed {hero.pronoun('possessive')} own elbows{extra}. "
        f"{companion.attrs['steady_line']}"
    )


def fetch_tools(world: World, hero: Entity, companion: Entity, light: Light) -> None:
    world.say(
        f"They took {light.phrase}, and {hero.id} also picked up a long stick from the corner. "
        f"{hero.pronoun().capitalize()} did not want to grab the ghost with bare hands."
    )
    world.say(light.glow_line)


def approach(world: World, hero: Entity, companion: Entity, place: Place) -> None:
    hero.meters["near_cause"] += 1
    world.say(
        f"Step by step, they went closer to the {place.dark_word}. The mystery felt big, "
        f"but their feet kept moving."
    )
    pred = predict_reveal(world)
    world.facts["predicted_clue"] = pred["clue"]
    world.facts["predicted_reveal"] = pred["revealed"]


def shine_light(world: World, hero: Entity, cause: Cause) -> None:
    world.get("light").meters["on"] += 1
    propagate(world, narrate=False)
    if world.get("cause").meters["seen"] >= THRESHOLD:
        world.say(
            f"In the beam, they noticed a clue: {cause.clue_line}. It did not look spooky and magical anymore. "
            f"It looked mixed-up and ordinary."
        )


def nudge_with_stick(world: World, hero: Entity, companion: Entity, cause: Cause) -> None:
    world.get("hero").meters["poking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stretched out the stick and gave the ghostly shape a tiny nudge. "
        f"{cause.reveal_line}"
    )
    if world.get("cause").meters["revealed"] >= THRESHOLD:
        world.say(companion.attrs["laugh_line"])


def tidy_up(world: World, hero: Entity, companion: Entity, cause: Cause) -> None:
    world.say(
        f"Together they fixed the mess: {cause.tidy_line}. "
        f"The corner stopped groaning, and the whole place felt friendly again."
    )
    world.say(
        f"After that, whenever a strange sound floated through {world.place.label}, "
        f"{hero.id} smiled first and wondered second. A mystery might still be spooky, "
        f"but now {hero.pronoun()} knew it could also be funny."
    )


def tell(
    place: Place,
    cause: Cause,
    light: Light,
    companion_cfg: Companion,
    *,
    hero_name: str = "Mina",
    hero_type: str = "girl",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["careful", "curious"],
        attrs={},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=companion_cfg.type,
        role="companion",
        label=companion_cfg.label,
        attrs={
            "opening_line": companion_cfg.opening_line,
            "steady_line": companion_cfg.steady_line,
            "laugh_line": companion_cfg.laugh_line,
        },
    ))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="cause", type="cause", label=cause.label))
    world.add(Entity(id="light", type="tool", label=light.label))

    world.facts.update(
        hero=hero,
        companion=companion,
        place_cfg=place,
        cause_cfg=cause,
        light_cfg=light,
        used_stick=True,
        predicted_clue=False,
        predicted_reveal=False,
    )

    opening_scene(world, hero, companion, place)

    world.para()
    first_spook(world, hero, cause, place)
    joke_and_guess(world, hero, companion)

    world.para()
    fetch_tools(world, hero, companion, light)
    approach(world, hero, companion, place)
    shine_light(world, hero, cause)

    world.para()
    nudge_with_stick(world, hero, companion, cause)
    tidy_up(world, hero, companion, cause)

    world.facts.update(
        solved=world.get("cause").meters["revealed"] >= THRESHOLD,
        clue_seen=world.get("cause").meters["seen"] >= THRESHOLD,
        fear_started=hero.memes["relief"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        phrase="the attic above the stairs",
        dark_word="far corner",
        draft_word="rafters",
        affords={"sheet_trunk", "coat_hook"},
        tags={"attic"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        phrase="the back porch by the garden door",
        dark_word="shadowy railing",
        draft_word="screen door",
        affords={"bucket_sheet", "coat_hook"},
        tags={"porch"},
    ),
    "shed": Place(
        id="shed",
        label="the shed",
        phrase="the little shed beside the yard",
        dark_word="tool shelf",
        draft_word="loose window",
        affords={"sheet_trunk", "bucket_sheet"},
        tags={"shed"},
    ),
}

CAUSES = {
    "sheet_trunk": Cause(
        id="sheet_trunk",
        label="a sheet snagged on an old trunk latch",
        ghost_shape="a sheety shape by an old trunk",
        sound_line="the cloth puffed out and the trunk lid gave a mournful creak",
        clue_line="a white sheet caught on a trunk latch, with one corner rising and falling in the draft",
        reveal_line="The sheet slipped free, and underneath it sat only a dusty trunk with a squeaky hinge",
        tidy_line="they folded the sheet and pushed the trunk lid down properly",
        darkness=2,
        needs_breeze=True,
        indoors=True,
        tags={"sheet", "draft"},
    ),
    "coat_hook": Cause(
        id="coat_hook",
        label="a raincoat hanging from a crooked hook",
        ghost_shape="a long white figure by the wall",
        sound_line="something swayed and the hook clicked against the wood like tiny teeth",
        clue_line="buttons glinting on a pale raincoat that was hanging from a bent hook",
        reveal_line="The hook gave one silly twang, and the ghost turned out to be only a raincoat with puffed sleeves",
        tidy_line="they straightened the hook and hung the coat flat",
        darkness=1,
        needs_breeze=False,
        indoors=True,
        tags={"coat", "hook"},
    ),
    "bucket_sheet": Cause(
        id="bucket_sheet",
        label="a wash sheet draped over a bucket and garden stick",
        ghost_shape="a bobbing white lump by the wall",
        sound_line="a bucket knocked softly while the cloth flapped and moaned",
        clue_line="a wash sheet draped over a bucket, with a garden stick holding one side too high",
        reveal_line="The cloth slid down, and there was the whole terrible ghost: one bucket, one garden stick, and a very silly sheet",
        tidy_line="they pulled the sheet off the bucket and laid the stick flat on the floor",
        darkness=2,
        needs_breeze=True,
        indoors=False,
        tags={"bucket", "stick", "sheet"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        glow_line="When the flashlight clicked on, the beam cut a clean path through the dark.",
        brightness=2,
        sense=3,
        tags={"flashlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a warm camping lantern",
        glow_line="The lantern glowed steady and round, making the shadows shrink back a little.",
        brightness=2,
        sense=3,
        tags={"lantern"},
    ),
    "candle_lamp": Light(
        id="candle_lamp",
        label="tiny candle lamp",
        phrase="a tiny candle lamp",
        glow_line="The little lamp trembled more than it shone.",
        brightness=1,
        sense=1,
        tags={"lamp"},
    ),
}

COMPANIONS = {
    "grandma": Companion(
        id="grandma",
        label="Grandma",
        type="grandma",
        opening_line='"If the house sighs, it is probably old wood," Grandma said. "Houses are chatty at night."',
        steady_line='"Maybe," Grandma whispered back, "or maybe it is a mystery asking to be solved."',
        laugh_line='Grandma laughed so hard she had to hold her cardigan. "That ghost needs laundry lessons," she said.',
        tags={"grandma"},
    ),
    "brother": Companion(
        id="brother",
        label="big brother",
        type="brother",
        opening_line='"I can hear the wind poking around," said her big brother. "It always wants to know our business."',
        steady_line='"If it is a ghost, it is the clumsiest one I have ever met," her brother whispered.',
        laugh_line='Her brother bent over laughing. "That ghost forgot how to be scary," he said.',
        tags={"brother"},
    ),
    "dad": Companion(
        id="dad",
        label="Dad",
        type="father",
        opening_line='"Old places make funny noises," Dad said, setting down his book. "Let us use our eyes before we use our imagination too much."',
        steady_line='"A real ghost would not bonk like that," Dad whispered. "Come on. Let us check."',
        laugh_line='Dad snorted with laughter. "I think we just frightened a bucket," he said.',
        tags={"dad"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Ava", "Nora", "Tess", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Max", "Eli", "Theo", "Finn", "Noah", "Sam", "Leo"]


@dataclass
class StoryParams:
    place: str
    cause: str
    light: str
    companion: str
    name: str
    gender: str
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
    "flashlight": [(
        "What is a flashlight?",
        "A flashlight is a small light you can carry in your hand. It helps you see in the dark without guessing."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light that glows all around. People use it when they want steady light in a dark place."
    )],
    "sheet": [(
        "Why can a sheet look spooky in the dark?",
        "A sheet is big, pale, and floppy, so it can look like a ghost shape when light is low. If wind moves it, the shape can seem even stranger."
    )],
    "draft": [(
        "What is a draft?",
        "A draft is a small moving stream of air. It can make cloth flutter or a loose thing creak."
    )],
    "mystery": [(
        "What does it mean to solve a mystery?",
        "Solving a mystery means finding the real answer to something puzzling. You look for clues instead of stopping at the first scary guess."
    )],
    "stick": [(
        "What is a stick useful for?",
        "A stick can help you reach something without putting your hand right on it. In a mystery, that can help you test what an object really is."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "flashlight", "lantern", "sheet", "draft", "stick"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    cause = f["cause_cfg"]
    return [
        'Write a funny ghost-story mystery for a 3-to-5-year-old that includes the word "stick".',
        f"Tell a gentle spooky story where a child named {hero.id} hears a ghost in {place.label}, but solves the mystery with clues instead of running away.",
        f"Write a child-facing ghost story with humor where the scary shape turns out to be {cause.label}, and the ending feels silly instead of truly frightening.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    cause = f["cause_cfg"]
    place = f["place_cfg"]
    light = f["light_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {companion.label_word} in {place.label}. They hear something ghostly and decide to solve the mystery."
        ),
        (
            f"Why did {hero.id} think there might be a ghost?",
            f"{hero.id} saw a pale shape and heard {cause.sound_line}. In the dark, those two clues felt spooky before the real answer was known."
        ),
        (
            f"What did they take with them to investigate?",
            f"They took {light.phrase} and a long stick. The light helped them see, and the stick let {hero.id} test the shape without grabbing it first."
        ),
    ]
    if f.get("clue_seen"):
        qa.append((
            "What clue helped them solve the mystery?",
            f"They saw {cause.clue_line}. That clue showed them the shape was made from ordinary things, not a real ghost."
        ))
    if f.get("solved"):
        qa.append((
            "How was the mystery solved?",
            f"{hero.id} nudged the shape with the stick, and {cause.reveal_line.lower()}. Once the hidden objects were clear, the fear turned into laughter."
        ))
        qa.append((
            "How did the story end?",
            f"They fixed the little mess and {place.label} felt friendly again. The ending proves what changed, because {hero.id} now meets strange sounds with curiosity before fear."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "stick"} | set(f["cause_cfg"].tags) | set(f["light_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        cause="sheet_trunk",
        light="flashlight",
        companion="grandma",
        name="Mina",
        gender="girl",
    ),
    StoryParams(
        place="porch",
        cause="bucket_sheet",
        light="lantern",
        companion="dad",
        name="Owen",
        gender="boy",
    ),
    StoryParams(
        place="porch",
        cause="coat_hook",
        light="flashlight",
        companion="brother",
        name="Ava",
        gender="girl",
    ),
    StoryParams(
        place="shed",
        cause="sheet_trunk",
        light="lantern",
        companion="grandma",
        name="Leo",
        gender="boy",
    ),
]


ASP_RULES = r"""
fits_place(P,C) :- place(P), cause(C), affords(P,C).
sensible_light(L) :- light(L), light_sense(L,S), sense_min(M), S >= M.
bright_enough(L,C) :- light(L), cause(C), brightness(L,B), darkness(C,D), B >= D.
valid(P,C,L) :- fits_place(P,C), sensible_light(L), bright_enough(L,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, cid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("darkness", cid, cause.darkness))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("brightness", lid, light.brightness))
        lines.append(asp.fact("light_sense", lid, light.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra_show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=True, header=f"### smoke {idx}")
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if "stick" not in sample.story.lower():
                raise StoryError('story did not include required word "stick"')
        except Exception as err:
            rc = 1
            print(f"SMOKE generation failed for case {idx}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny ghost-story mystery: a child solves a spooky-looking problem with clues, a light, and a stick."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, cause, light) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not place_supports(place, cause):
            raise StoryError(explain_place_rejection(place, cause))
    if args.light and args.cause:
        light = LIGHTS[args.light]
        cause = CAUSES[args.cause]
        if not (light.sense >= 2 and light_suffices(light, cause)):
            raise StoryError(explain_light_rejection(light, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.light is None or combo[2] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause, light = rng.choice(combos)
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        cause=cause,
        light=light,
        companion=companion,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    light = LIGHTS[params.light]
    if not place_supports(place, cause):
        raise StoryError(explain_place_rejection(place, cause))
    if not (light.sense >= 2 and light_suffices(light, cause)):
        raise StoryError(explain_light_rejection(light, cause))

    world = tell(
        place=place,
        cause=cause,
        light=light,
        companion_cfg=COMPANIONS[params.companion],
        hero_name=params.name,
        hero_type=params.gender,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, light) combos:\n")
        for place, cause, light in combos:
            print(f"  {place:8} {cause:12} {light}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.cause} in {p.place} with {p.light}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
