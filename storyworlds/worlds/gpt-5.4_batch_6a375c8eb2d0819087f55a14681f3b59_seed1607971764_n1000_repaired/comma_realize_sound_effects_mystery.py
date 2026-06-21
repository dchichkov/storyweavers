#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py
=================================================================

A standalone story world for a tiny child-facing mystery driven by sound effects.

Premise
-------
A child hears a strange sound in a familiar place, follows small physical clues,
and then realizes the "mystery" has an ordinary cause. With a calm grown-up's
help, the child fixes the cause and the place becomes quiet again.

Reasonableness constraint
-------------------------
Not every sound source fits every place, and not every fix truly matches the
cause. This world only generates combinations where:

* the chosen place can plausibly host the sound source; and
* the chosen fix actually solves that source.

That constraint exists in both Python and an inline ASP twin, so ``--verify``
can check parity.

Run it
------
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py --place attic --source marble
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py --source branch --fix pocket_marble
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/comma_realize_sound_effects_mystery.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
    affordances: set[str] = field(default_factory=set)
    opening: str = ""
    ending: str = ""
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
class NoiseSource:
    id: str
    label: str
    sound: str
    sound_word: str
    place_text: str
    clue: str
    reveal: str
    mystery_name: str
    compatible_places: set[str] = field(default_factory=set)
    compatible_fixes: set[str] = field(default_factory=set)
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
    label: str
    action: str
    closing: str
    target_sources: set[str] = field(default_factory=set)
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
    beam: str
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


def _r_noise_spreads(world: World) -> list[str]:
    source = world.get("source")
    hero = world.get("hero")
    room = world.get("room")
    sig = ("noise_spreads",)
    if source.meters["noise"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["echo"] += 1
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_clue_reveals(world: World) -> list[str]:
    source = world.get("source")
    hero = world.get("hero")
    sig = ("clue_reveals",)
    if source.meters["clue_found"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["understanding"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    hero.memes["courage"] += 1
    return []


def _r_fix_quiets(world: World) -> list[str]:
    source = world.get("source")
    hero = world.get("hero")
    helper = world.get("helper")
    room = world.get("room")
    sig = ("fix_quiets",)
    if source.meters["fixed"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    if source.meters["noise"] >= THRESHOLD:
        source.meters["noise"] = 0.0
    room.meters["echo"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="noise_spreads", tag="emotional", apply=_r_noise_spreads),
    Rule(name="clue_reveals", tag="understanding", apply=_r_clue_reveals),
    Rule(name="fix_quiets", tag="resolution", apply=_r_fix_quiets),
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


def source_fits_place(setting: Setting, source: NoiseSource) -> bool:
    return source.id in setting.affordances and setting.id in source.compatible_places


def fix_matches_source(fix: Fix, source: NoiseSource) -> bool:
    return source.id in fix.target_sources and fix.id in source.compatible_fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for source_id, source in SOURCES.items():
            if not source_fits_place(setting, source):
                continue
            for fix_id, fix in FIXES.items():
                if fix_matches_source(fix, source):
                    combos.append((place_id, source_id, fix_id))
    return combos


def predict_understanding(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["clue_found"] += 1
    propagate(sim, narrate=False)
    return {
        "understands": sim.get("hero").memes["understanding"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
    }


def begin_mystery(world: World, hero: Entity, helper: Entity, light: Light, source: NoiseSource) -> None:
    hero.memes["curiosity"] += 1
    source_ent = world.get("source")
    source_ent.meters["noise"] += 1
    propagate(world, narrate=False)

    world.say(
        f"That evening, {hero.id} padded into {world.setting.label}. "
        f"{world.setting.opening}"
    )
    world.say(
        f"A pale comma of light from the {light.label} curved across the floor."
    )
    world.say(
        f"Then the sound came again: {source.sound} It seemed to come from {source.place_text}, "
        f"and it sounded like {source.mystery_name}."
    )
    world.say(
        f"{hero.id} stopped so fast that {helper.id}'s hand brushed {hero.pronoun('possessive')} shoulder. "
        f'"Did you hear that?" {hero.pronoun()} whispered.'
    )


def choose_to_investigate(world: World, hero: Entity, helper: Entity, source: NoiseSource, light: Light) -> None:
    pred = predict_understanding(world)
    world.facts["predicted_understands"] = pred["understands"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} listened too. "{source.sound_word.capitalize()} can sound spooky in the dark," '
        f'{helper.pronoun()} said, "but mysteries get smaller when we look closely."'
    )
    world.say(
        f"So they went together, step by step, while the {light.label} {light.beam}."
    )


def discover_clue(world: World, hero: Entity, helper: Entity, source: NoiseSource) -> None:
    world.get("source").meters["clue_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {source.place_text}, {hero.id} saw the clue at last: {source.clue}"
    )
    world.say(
        f'{helper.id} knelt beside {hero.pronoun("object")} and waited while {hero.id} looked again, '
        f"this time with more wondering than fear."
    )


def realize_truth(world: World, hero: Entity, source: NoiseSource) -> None:
    world.say(
        f"Then {hero.id} began to realize the truth. It was not a ghost or a secret creature at all, "
        f"but {source.reveal}."
    )
    world.say(
        f'The sound changed from a mystery into a clue, and {hero.id} felt {hero.pronoun("possessive")} chest loosen.'
    )


def mend(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    world.get("source").meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Working together, {helper.id} and {hero.id} {fix.action}."
    )
    world.say(
        fix.closing
    )


def ending(world: World, hero: Entity, helper: Entity, source: NoiseSource, light: Light) -> None:
    room = world.get("room")
    quiet = "quiet" if room.meters["echo"] < THRESHOLD else "still a little noisy"
    world.say(
        f"After that, they waited and listened. No {source.sound_word}, no jumpy shadows, only the soft hum of the house."
    )
    world.say(
        f"{world.setting.ending} {hero.id} smiled up at {helper.id}. The place felt {quiet} now, "
        f"and the {light.label} no longer looked like a detective's tool. It looked like an ordinary light in a safe place."
    )


def tell(
    setting: Setting,
    source_cfg: NoiseSource,
    fix_cfg: Fix,
    light_cfg: Light,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    helper_type: str = "mother",
    helper_name: str = "Mom",
    trait: str = "curious",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
        tags=set(),
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["calm"],
        attrs={},
        tags=set(),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=setting.label,
        role="room",
        attrs={},
        tags=set(setting.tags),
    ))
    light = world.add(Entity(
        id="light",
        kind="thing",
        type="light",
        label=light_cfg.label,
        role="light",
        attrs={},
        tags=set(light_cfg.tags),
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        role="source",
        attrs={},
        tags=set(source_cfg.tags),
    ))

    hero.memes["worry"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["understanding"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["courage"] = 0.0
    helper.memes["pride"] = 0.0
    room.meters["echo"] = 0.0
    source.meters["noise"] = 0.0
    source.meters["clue_found"] = 0.0
    source.meters["fixed"] = 0.0

    world.facts.update(
        hero=hero,
        helper=helper,
        room=room,
        light=light_cfg,
        setting=setting,
        source_cfg=source_cfg,
        fix_cfg=fix_cfg,
        clue_found=False,
        solved=False,
    )

    begin_mystery(world, hero, helper, light_cfg, source_cfg)
    world.para()
    choose_to_investigate(world, hero, helper, source_cfg, light_cfg)
    discover_clue(world, hero, helper, source_cfg)
    world.facts["clue_found"] = source.meters["clue_found"] >= THRESHOLD
    realize_truth(world, hero, source_cfg)
    world.para()
    mend(world, hero, helper, fix_cfg)
    world.facts["solved"] = source.meters["fixed"] >= THRESHOLD and source.meters["noise"] < THRESHOLD
    ending(world, hero, helper, source_cfg, light_cfg)

    world.facts["hero_worry"] = hero.memes["worry"]
    world.facts["hero_relief"] = hero.memes["relief"]
    world.facts["hero_understanding"] = hero.memes["understanding"]
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        label="the attic",
        affordances={"branch", "marble", "latch"},
        opening="The rafters made long triangles over old trunks and folded blankets.",
        ending="Over the trunks and folded blankets, the rafters rested without a single sudden knock.",
        tags={"attic", "mystery"},
    ),
    "hallway": Setting(
        id="hallway",
        label="the hallway",
        affordances={"branch"},
        opening="The runner rug lay straight as a path, and the window at the end wore the night like dark blue glass.",
        ending="Down the runner rug, the dark blue window looked peaceful instead of puzzling.",
        tags={"hallway", "mystery"},
    ),
    "shed": Setting(
        id="shed",
        label="the garden shed",
        affordances={"marble", "latch"},
        opening="Rakes stood along one wall, and the air smelled like wood, string, and flowerpots.",
        ending="Among the rakes and flowerpots, nothing clattered now except one sleepy cricket outside.",
        tags={"shed", "mystery"},
    ),
}

SOURCES = {
    "branch": NoiseSource(
        id="branch",
        label="branch at the glass",
        sound="Tap, tap, tap!",
        sound_word="tapping",
        place_text="the window",
        clue="thin leaf-shadows brushing the glass whenever the wind leaned in",
        reveal="an apple-tree branch patting the pane",
        mystery_name="someone knocking with tiny wooden fingers",
        compatible_places={"attic", "hallway"},
        compatible_fixes={"tie_branch", "close_shutter"},
        tags={"branch", "sound_effects", "wind"},
    ),
    "marble": NoiseSource(
        id="marble",
        label="rolling marble",
        sound="Tik... tik-tik... rrrr!",
        sound_word="rattling",
        place_text="an old toy box",
        clue="one bright marble rolling to the cracked corner every time the box tipped",
        reveal="a runaway marble inside a tilted toy box",
        mystery_name="a hidden creature scrambling around",
        compatible_places={"attic", "shed"},
        compatible_fixes={"pocket_marble", "level_box"},
        tags={"marble", "sound_effects", "toy"},
    ),
    "latch": NoiseSource(
        id="latch",
        label="loose latch",
        sound="Clack-clack!",
        sound_word="clacking",
        place_text="the door",
        clue="the metal hook jumping loose whenever the wind pushed the wood",
        reveal="a loose latch hopping against the door",
        mystery_name="a secret door trying to open itself",
        compatible_places={"attic", "shed"},
        compatible_fixes={"fasten_latch"},
        tags={"latch", "sound_effects", "wind"},
    ),
}

FIXES = {
    "tie_branch": Fix(
        id="tie_branch",
        label="tie the branch back",
        action="looped a bit of garden string around the branch and tied it gently away from the pane",
        closing="The window gave one last tiny shiver, and then the tapping stopped.",
        target_sources={"branch"},
        tags={"branch", "string", "problem_solving"},
    ),
    "close_shutter": Fix(
        id="close_shutter",
        label="close the shutter",
        action="pulled the shutter snug and set the little hook in place",
        closing="With the shutter shut tight, the branch could whisper outside, but it could not tap on the glass anymore.",
        target_sources={"branch"},
        tags={"window", "problem_solving"},
    ),
    "pocket_marble": Fix(
        id="pocket_marble",
        label="pick up the marble",
        action="lifted the lid and tucked the runaway marble into a small pocket",
        closing="Nothing rolled after that. The toy box sat still, as if the mystery had curled up and gone to sleep.",
        target_sources={"marble"},
        tags={"marble", "problem_solving"},
    ),
    "level_box": Fix(
        id="level_box",
        label="set the box straight",
        action="slid a flat board under the toy box until it stood level",
        closing="The marble had nowhere to race now, so the rattling gave up all at once.",
        target_sources={"marble"},
        tags={"marble", "problem_solving"},
    ),
    "fasten_latch": Fix(
        id="fasten_latch",
        label="fasten the latch",
        action="pressed the hook back into place and tightened the little latch until it held",
        closing="The door stayed still after that, and the clack-clack sound vanished into the night.",
        target_sources={"latch"},
        tags={"latch", "problem_solving"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        beam="made a round white spot that bounced over every box and board",
        tags={"flashlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="camp lantern",
        beam="glowed warm and steady, making the corners less shadowy",
        tags={"lantern"},
    ),
    "booklight": Light(
        id="booklight",
        label="book-light",
        beam="drew a slim silver line over handles, hooks, and dusty edges",
        tags={"light"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "June", "Ivy", "Tessa", "Ruby", "Clara"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Max", "Eli", "Sam", "Finn", "Leo"]
TRAITS = ["curious", "careful", "observant", "brave", "quiet"]
HELPERS = [
    ("mother", "Mom"),
    ("father", "Dad"),
    ("grandmother", "Grandma"),
    ("grandfather", "Grandpa"),
]


@dataclass
class StoryParams:
    place: str
    source: str
    fix: str
    light: str
    name: str
    gender: str
    helper_type: str
    helper_name: str
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
    "sound_effects": [
        (
            "What are sound effects in a story?",
            "Sound effects are words like tap, clack, or rattle that help your ears imagine what characters hear. They make a scene feel more alive because the sounds almost seem to happen beside you.",
        )
    ],
    "branch": [
        (
            "Why can a tree branch tap on a window?",
            "Wind can push a branch back and forth until it touches the glass. When it bumps the window again and again, it makes a tapping sound.",
        )
    ],
    "marble": [
        (
            "Why does a marble make noise when it rolls in a box?",
            "A marble is hard and round, so it clicks against wood or tin as it rolls. If the box tilts, gravity keeps the marble moving and the sound repeats.",
        )
    ],
    "latch": [
        (
            "What does a latch do on a door?",
            "A latch helps keep a door closed. If it is loose, wind can jiggle it and make a clacking sound.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight lets you see where a sound is coming from without guessing. Good light can turn a scary mystery into an ordinary problem.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives a steady light that spreads around a room. That makes it easier to notice clues in corners and on shelves.",
        )
    ],
    "wind": [
        (
            "How can wind make mysterious sounds?",
            "Wind can shake branches, doors, and latches even when nobody is there. That is why harmless things can sound mysterious at night.",
        )
    ],
    "problem_solving": [
        (
            "What does it mean to solve a mystery calmly?",
            "It means you look, listen, and think before you guess. Calm problem-solving helps you notice clues and understand what is really happening.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sound_effects",
    "branch",
    "marble",
    "latch",
    "flashlight",
    "lantern",
    "wind",
    "problem_solving",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    setting = world.facts["setting"]
    source = world.facts["source_cfg"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes sound effects, the words "comma" and "realize", and a child hearing {source.sound_word} in {setting.label}.',
        f"Tell a gentle mystery where a {hero.type} named {hero.id} follows a strange sound, finds a small clue, and realizes the sound has an ordinary cause.",
        f'Write a cozy suspense story that uses sound words like "{source.sound}" and ends with a calm grown-up helping fix the real problem.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    source = world.facts["source_cfg"]
    fix = world.facts["fix_cfg"]
    light = world.facts["light"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, who heard a strange sound in {setting.label}. Together they followed the noise instead of running away from it.",
        ),
        (
            "What made the place feel mysterious at the start?",
            f"The place felt mysterious because the sound came suddenly in the dark: {source.sound} {hero.id} did not know its cause yet, so the ordinary room seemed full of secrets.",
        ),
        (
            f"What clue helped {hero.id} understand the sound?",
            f"The clue was {source.clue}. Once {hero.id} saw that detail, {hero.pronoun()} could connect the sound to a real physical cause instead of a spooky guess.",
        ),
        (
            f"When did {hero.id} realize what was really happening?",
            f"{hero.id} realized it after looking closely at the clue near {source.place_text}. The sound stopped feeling magical because the clue showed exactly what was moving and why.",
        ),
        (
            f"How did they solve the mystery?",
            f"They solved it by {fix.action}. That fix matched the real cause, so the noise went quiet instead of coming back.",
        ),
        (
            f"Why did the {light.label} matter?",
            f"The {light.label} helped them see the clue clearly. Good light turned the mystery into something they could inspect and understand.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            (
                "How did the ending show that things had changed?",
                f"At the end, the place was quiet and safe instead of jumpy and puzzling. The silence proved that they had found the true cause and fixed it.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    setting = world.facts["setting"]
    source = world.facts["source_cfg"]
    fix = world.facts["fix_cfg"]
    light = world.facts["light"]
    tags = set(setting.tags) | set(source.tags) | set(fix.tags) | set(light.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        source="marble",
        fix="pocket_marble",
        light="flashlight",
        name="Nora",
        gender="girl",
        helper_type="grandmother",
        helper_name="Grandma",
        trait="observant",
        seed=101,
    ),
    StoryParams(
        place="hallway",
        source="branch",
        fix="close_shutter",
        light="booklight",
        name="Theo",
        gender="boy",
        helper_type="father",
        helper_name="Dad",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        place="shed",
        source="latch",
        fix="fasten_latch",
        light="lantern",
        name="Lila",
        gender="girl",
        helper_type="mother",
        helper_name="Mom",
        trait="brave",
        seed=103,
    ),
    StoryParams(
        place="attic",
        source="branch",
        fix="tie_branch",
        light="lantern",
        name="Eli",
        gender="boy",
        helper_type="grandfather",
        helper_name="Grandpa",
        trait="quiet",
        seed=104,
    ),
    StoryParams(
        place="shed",
        source="marble",
        fix="level_box",
        light="flashlight",
        name="Ruby",
        gender="girl",
        helper_type="mother",
        helper_name="Mom",
        trait="curious",
        seed=105,
    ),
]


def explain_rejection(place: Setting, source: NoiseSource, fix: Fix) -> str:
    if not source_fits_place(place, source):
        return (
            f"(No story: {source.label} does not fit {place.label}. "
            f"Choose a place that can plausibly contain that sound.)"
        )
    if not fix_matches_source(fix, source):
        return (
            f"(No story: {fix.label} would not solve the sound caused by {source.label}. "
            f"The fix must match the real cause of the mystery.)"
        )
    return "(No story: this combination is not a valid mystery in this world.)"


ASP_RULES = r"""
fits_place(P, S) :- affords(P, S), source_place(S, P).
matches_fix(S, F) :- targets(F, S), source_fix(S, F).
valid(P, S, F) :- place(P), source(S), fix(F), fits_place(P, S), matches_fix(S, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(setting.affordances):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for place_id in sorted(source.compatible_places):
            lines.append(asp.fact("source_place", source_id, place_id))
        for fix_id in sorted(source.compatible_fixes):
            lines.append(asp.fact("source_fix", source_id, fix_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for source_id in sorted(fix.target_sources):
            lines.append(asp.fact("targets", fix_id, source_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a strange sound, follows clues, and solves a small mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _helper_name(helper_type: str) -> str:
    return {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }[helper_type]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.fix:
        place = SETTINGS[args.place]
        source = SOURCES[args.source]
        fix = FIXES[args.fix]
        if not (source_fits_place(place, source) and fix_matches_source(fix, source)):
            raise StoryError(explain_rejection(place, source, fix))
    if args.place and args.source and not source_fits_place(SETTINGS[args.place], SOURCES[args.source]):
        raise StoryError(explain_rejection(SETTINGS[args.place], SOURCES[args.source], next(iter(FIXES.values()))))
    if args.source and args.fix and not fix_matches_source(FIXES[args.fix], SOURCES[args.source]):
        raise StoryError(explain_rejection(SETTINGS[args.place] if args.place else next(iter(SETTINGS.values())), SOURCES[args.source], FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, fix_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(sorted(ht for ht, _ in HELPERS))
    helper_name = _helper_name(helper_type)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        source=source_id,
        fix=fix_id,
        light=light_id,
        name=name,
        gender=gender,
        helper_type=helper_type,
        helper_name=helper_name,
        trait=trait,
        seed=None,
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    place = SETTINGS[params.place]
    source = SOURCES[params.source]
    fix = FIXES[params.fix]
    if not source_fits_place(place, source) or not fix_matches_source(fix, source):
        raise StoryError(explain_rejection(place, source, fix))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.place],
        source_cfg=SOURCES[params.source],
        fix_cfg=FIXES[params.fix],
        light_cfg=LIGHTS[params.light],
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
        trait=params.trait,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    parser = build_parser()
    smoke_cases = [CURATED[0]]
    try:
        resolved = resolve_params(parser.parse_args([]), random.Random(7))
        resolved.seed = 7
        smoke_cases.append(resolved)
    except StoryError as err:
        rc = 1
        print(f"SMOKE-TEST setup failed during resolve_params(): {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header=f"smoke {idx}")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE-TEST failed for case {idx}: {err}")
        else:
            print(f"OK: smoke test {idx} generated and emitted successfully.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, fix) combos:\n")
        for place_id, source_id, fix_id in combos:
            print(f"  {place_id:8} {source_id:8} {fix_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.source} in {p.place} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
