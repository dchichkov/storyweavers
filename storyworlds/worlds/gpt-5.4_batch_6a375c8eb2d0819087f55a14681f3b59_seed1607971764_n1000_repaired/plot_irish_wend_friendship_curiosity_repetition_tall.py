#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py
==================================================================================

A standalone storyworld for a tall-tale garden story about two friends, a giant
garden plot, an Irish helper animal, and the way curiosity can lead children to
wend farther and farther into a mystery. The world model enforces one simple
piece of reasonableness: each kind of giant-growth cause has a matching sensible
fix, and some causes only make sense for some crops.

Run it
------
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py --crop beans --cause moonseed
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py --cause compost --crop beans
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py --all
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/plot_irish_wend_friendship_curiosity_repetition_tall.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"dog", "pony", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Crop:
    id: str
    label: str
    patch: str
    plural_label: str
    stalk_word: str
    giant_shape: str
    risk: str
    ending_image: str
    base_height: int
    compatible_causes: set[str] = field(default_factory=set)
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
    label: str
    clue: str
    discovery: str
    boost: int
    danger: int
    fits_crops: set[str] = field(default_factory=set)
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
    sense: int
    targets: str
    action: str
    qa_text: str
    ending: str
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
    intro: str
    warn: str
    celebrate: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "friend"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_giant_blocks(world: World) -> list[str]:
    crop = world.get("crop")
    plot = world.get("plot")
    if crop.meters["giant"] < THRESHOLD:
        return []
    sig = ("giant_blocks", int(crop.meters["giant"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plot.meters["blocked"] = max(plot.meters["blocked"], 1.0)
    for kid in world.kids():
        kid.memes["awe"] += 1
    return ["__giant__"]


def _r_curiosity_pulls(world: World) -> list[str]:
    plot = world.get("plot")
    out: list[str] = []
    if plot.meters["blocked"] < THRESHOLD:
        return out
    for kid in world.kids():
        if kid.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curiosity_pulls", kid.id, int(kid.memes["curiosity"]))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="giant_blocks", tag="physical", apply=_r_giant_blocks),
    Rule(name="curiosity_pulls", tag="emotional", apply=_r_curiosity_pulls),
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


CROPS = {
    "beans": Crop(
        id="beans",
        label="bean",
        patch="bean plot",
        plural_label="beans",
        stalk_word="vines",
        giant_shape="green ropes that seemed determined to lasso the moon",
        risk="twisted across the path like sleepy snakes",
        ending_image="the bean tunnel stood grand but gentle, cool enough for two friends and one dog to walk through side by side",
        base_height=2,
        compatible_causes={"hose", "moonseed"},
        tags={"beans", "garden"},
    ),
    "pumpkins": Crop(
        id="pumpkins",
        label="pumpkin",
        patch="pumpkin plot",
        plural_label="pumpkins",
        stalk_word="leaves",
        giant_shape="orange hills with leaves broad as picnic blankets",
        risk="hid the stepping stones under a quilt of green",
        ending_image="the pumpkins rested in neat rows, still so round and grand that the shadows looked like sleepy orange moons",
        base_height=2,
        compatible_causes={"hose", "compost"},
        tags={"pumpkin", "garden"},
    ),
    "sunflowers": Crop(
        id="sunflowers",
        label="sunflower",
        patch="sunflower plot",
        plural_label="sunflowers",
        stalk_word="stalks",
        giant_shape="golden towers that nodded high enough to gossip with clouds",
        risk="leaned over the lane and made a striped green tunnel",
        ending_image="the sunflowers kept their tall-tale height, but they stood straight again, bright as a row of small suns over the gate",
        base_height=3,
        compatible_causes={"hose", "compost", "moonseed"},
        tags={"sunflower", "garden"},
    ),
}

CAUSES = {
    "hose": Cause(
        id="hose",
        label="a forgotten hose",
        clue="mud glimmered in a silver ribbon all the way down the row",
        discovery="At the far end, a brass spigot chattered to itself while a hose poured and poured, as if it meant to water the whole county before lunch.",
        boost=2,
        danger=1,
        fits_crops={"beans", "pumpkins", "sunflowers"},
        tags={"water", "garden"},
    ),
    "compost": Cause(
        id="compost",
        label="a split compost basket",
        clue="rich dark crumbs lay in fat little drifts between the roots",
        discovery="By the fence, the compost basket had popped its side and spilled rich black food around the roots like a feast for giants.",
        boost=2,
        danger=1,
        fits_crops={"pumpkins", "sunflowers"},
        tags={"compost", "garden"},
    ),
    "moonseed": Cause(
        id="moonseed",
        label="a moonseed packet",
        clue="silver seed husks winked in the dirt like tiny fish scales",
        discovery="Under the last leaf lay a silver packet marked MOONSEED in curly letters, and just one sparkly seed still hummed inside it.",
        boost=3,
        danger=2,
        fits_crops={"beans", "sunflowers"},
        tags={"seed", "moonseed"},
    ),
}

FIXES = {
    "close_spigot": Fix(
        id="close_spigot",
        sense=3,
        targets="hose",
        action="took turns bracing their shoes in the mud and turned the chattering spigot shut",
        qa_text="They turned the spigot shut so the water stopped rushing into the plot",
        ending="Once the extra water stopped, the row quit charging ahead and settled into one splendid, sensible giant patch.",
        tags={"water", "fix"},
    ),
    "patch_compost": Fix(
        id="patch_compost",
        sense=3,
        targets="compost",
        action="held the basket together with twine and scooped the spilled compost back where it belonged",
        qa_text="They tied the split basket and scooped the rich compost back into place",
        ending="Once the roots stopped feasting on the loose compost, the plants relaxed and remembered how to be merely enormous instead of impossible.",
        tags={"compost", "fix"},
    ),
    "move_moonseed": Fix(
        id="move_moonseed",
        sense=3,
        targets="moonseed",
        action="wrapped the shining moonseed in a handkerchief and tucked it into an empty tin where it could not whisper to the roots anymore",
        qa_text="They wrapped the moonseed up and moved it away from the roots",
        ending="When the moonseed stopped humming under the stems, the wild growing slowed to a proud, storybook stretch.",
        tags={"seed", "fix"},
    ),
    "sing_at_it": Fix(
        id="sing_at_it",
        sense=1,
        targets="moonseed",
        action="sang a loud song at the row",
        qa_text="They sang at the plants",
        ending="The row did not care one bit for singing.",
        tags={"nonsense"},
    ),
}

HELPERS = {
    "irish_setter": Helper(
        id="irish_setter",
        label="an Irish setter named Bramble",
        type="dog",
        intro="An Irish setter named Bramble trotted after them with ears like red silk flags.",
        warn="Bramble gave a sharp bark and pawed the ground whenever the row looked too wild.",
        celebrate="Bramble bounced in three happy circles and sneezed a puff of dirt into the sunshine.",
        tags={"dog", "irish"},
    ),
    "irish_pony": Helper(
        id="irish_pony",
        label="a little Irish pony named Clover",
        type="pony",
        intro="A little Irish pony named Clover clip-clopped beside them, neat as a toy and twice as brave.",
        warn="Clover snorted and stamped whenever the path vanished under the giant leaves.",
        celebrate="Clover tossed its mane and trotted a tiny victory march around the watering can.",
        tags={"pony", "irish"},
    ),
    "irish_goat": Helper(
        id="irish_goat",
        label="a bearded Irish goat named Moss",
        type="goat",
        intro="A bearded Irish goat named Moss followed along, bright-eyed and springy as a coiled rug.",
        warn="Moss bleated and butted the air whenever the stalks leaned too close.",
        celebrate="Moss kicked up its heels and nibbled one loose weed as if it had won a medal.",
        tags={"goat", "irish"},
    ),
}

GIRL_NAMES = ["Molly", "Nora", "Maeve", "Anna", "Lily", "Rose", "Clara", "Elsie"]
BOY_NAMES = ["Finn", "Owen", "Jack", "Sam", "Leo", "Tom", "Evan", "Ben"]

LANDMARKS = [
    "past the rain barrel",
    "past the bean poles",
    "past the scarecrow",
    "past the gate",
    "past the shed",
    "almost to the orchard stone wall",
]


def cause_fits_crop(crop: Crop, cause: Cause) -> bool:
    return cause.id in crop.compatible_causes and crop.id in cause.fits_crops


def fix_matches_cause(cause: Cause, fix: Fix) -> bool:
    return fix.targets == cause.id and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for cause_id, cause in CAUSES.items():
            if not cause_fits_crop(crop, cause):
                continue
            for fix_id, fix in FIXES.items():
                if fix_matches_cause(cause, fix):
                    combos.append((crop_id, cause_id, fix_id))
    return combos


def explain_rejection(crop: Crop, cause: Cause) -> str:
    if not cause_fits_crop(crop, cause):
        return (
            f"(No story: {cause.label} is not a sensible reason for giant {crop.plural_label} here. "
            f"Pick a crop-cause pair the world knows how to explain.)"
        )
    return "(No story: that crop and cause do not make a reasonable tall tale together.)"


def explain_fix(cause: Cause, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Pick a real solution instead.)"
        )
    return (
        f"(No story: {fix.id} does not fix {cause.label}. Choose the fix that actually matches the cause.)"
    )


def giantness(crop: Crop, cause: Cause) -> int:
    return crop.base_height + cause.boost


def follow_steps(stage: int) -> list[str]:
    return LANDMARKS[: max(3, min(stage, len(LANDMARKS)))]


def _do_giant_growth(world: World, crop_cfg: Crop, cause_cfg: Cause, narrate: bool = True) -> None:
    crop = world.get("crop")
    plot = world.get("plot")
    crop.meters["giant"] = float(giantness(crop_cfg, cause_cfg))
    plot.meters["danger"] = float(cause_cfg.danger)
    propagate(world, narrate=narrate)


def predict_path(world: World, crop_cfg: Crop, cause_cfg: Cause) -> dict:
    sim = world.copy()
    _do_giant_growth(sim, crop_cfg, cause_cfg, narrate=False)
    crop = sim.get("crop")
    plot = sim.get("plot")
    return {
        "giant": int(crop.meters["giant"]),
        "blocked": plot.meters["blocked"] >= THRESHOLD,
        "danger": int(plot.meters["danger"]),
    }


def introduce(world: World, a: Entity, b: Entity, helper: Entity, crop_cfg: Crop) -> None:
    for kid in (a, b):
        kid.memes["friendship"] += 1
        kid.memes["curiosity"] = 1.0
    world.say(
        f"{a.id} and {b.id} were the sort of friends who could turn one small chore into a whole shining adventure."
    )
    world.say(
        f"That morning they walked to the village {crop_cfg.patch}, and the good brown plot looked tidy enough to fit inside an apron pocket."
    )
    world.say(helper.attrs["intro"])


def notice(world: World, a: Entity, b: Entity, crop_cfg: Crop, cause_cfg: Cause) -> None:
    pred = predict_path(world, crop_cfg, cause_cfg)
    world.facts["predicted_giant"] = pred["giant"]
    world.facts["predicted_blocked"] = pred["blocked"]
    _do_giant_growth(world, crop_cfg, cause_cfg)
    world.say(
        f"But one row had gone taller than a tall tale. Its {crop_cfg.stalk_word} had become {crop_cfg.giant_shape}, and they {crop_cfg.risk}."
    )
    world.say(
        f'{a.id} blinked. "{crop_cfg.plural_label.capitalize()} do not usually grow past the scarecrow\'s hat," {a.pronoun()} said.'
    )
    world.say(
        f'{b.id} leaned in with a grin. "Then we had better find out why," {b.pronoun()} said.'
    )


def wend_deeper(world: World, a: Entity, b: Entity, helper: Entity, crop_cfg: Crop) -> None:
    steps = follow_steps(int(world.get("crop").meters["giant"]))
    world.facts["landmarks"] = list(steps)
    world.say(
        f"So the three of them began to wend down the row."
    )
    for i, step in enumerate(steps, 1):
        for kid in (a, b):
            kid.memes["curiosity"] += 1
        propagate(world, narrate=False)
        if i == 1:
            world.say(
                f"They went {step}, and the row only grew stranger."
            )
        elif i == 2:
            world.say(
                f"They went {step}, and still there was more plot ahead of them."
            )
        else:
            world.say(
                f"They went {step}, and still they wended on, shoulder to shoulder, too curious to quit."
            )
    world.say(helper.attrs["warn"])


def discover(world: World, a: Entity, b: Entity, cause_cfg: Cause) -> None:
    plot = world.get("plot")
    plot.meters["mystery_found"] = 1.0
    world.say(
        f"At last they noticed the clue: {cause_cfg.clue}."
    )
    world.say(cause_cfg.discovery)
    world.say(
        f'{a.id} and {b.id} looked at each other at the very same moment. Friendship made the thinking quicker, as if two guesses had clicked together into one answer.'
    )


def fix_it(world: World, a: Entity, b: Entity, helper: Entity, fix_cfg: Fix) -> None:
    crop = world.get("crop")
    plot = world.get("plot")
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    plot.meters["danger"] = 0.0
    plot.meters["blocked"] = 0.0
    crop.meters["calm"] = 1.0
    world.say(
        f"Together they {fix_cfg.action}."
    )
    world.say(fix_cfg.ending)
    world.say(helper.attrs["celebrate"])


def ending(world: World, a: Entity, b: Entity, crop_cfg: Crop) -> None:
    for kid in (a, b):
        kid.memes["friendship"] += 1
        kid.memes["wonder"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f"When they turned back, the same plot no longer felt like a puzzle trying to swallow them. It felt like a story they had helped set right."
    )
    world.say(
        f"{crop_cfg.ending_image}."
    )
    world.say(
        f"From then on, whenever the village needed a mystery minded into shape, people said, \"Send those two friends. They can wend through wonder without losing each other.\""
    )


def tell(
    crop_cfg: Crop,
    cause_cfg: Cause,
    fix_cfg: Fix,
    helper_cfg: Helper,
    friend1: str = "Molly",
    friend1_gender: str = "girl",
    friend2: str = "Finn",
    friend2_gender: str = "boy",
) -> World:
    world = World()
    a = world.add(Entity(id=friend1, kind="character", type=friend1_gender, role="friend"))
    b = world.add(Entity(id=friend2, kind="character", type=friend2_gender, role="friend"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={
                "intro": helper_cfg.intro,
                "warn": helper_cfg.warn,
                "celebrate": helper_cfg.celebrate,
            },
            tags=set(helper_cfg.tags),
        )
    )
    plot = world.add(Entity(id="plot", type="plot", label="plot"))
    crop = world.add(
        Entity(
            id="crop",
            type="crop",
            label=crop_cfg.plural_label,
            tags=set(crop_cfg.tags),
        )
    )

    world.facts.update(
        crop_cfg=crop_cfg,
        cause_cfg=cause_cfg,
        fix_cfg=fix_cfg,
        helper_cfg=helper_cfg,
        friend1=a,
        friend2=b,
        helper=helper,
        plot=plot,
        crop=crop,
        landmarks=[],
        predicted_giant=0,
        predicted_blocked=False,
    )

    introduce(world, a, b, helper, crop_cfg)
    world.para()
    notice(world, a, b, crop_cfg, cause_cfg)
    wend_deeper(world, a, b, helper, crop_cfg)
    world.para()
    discover(world, a, b, cause_cfg)
    fix_it(world, a, b, helper, fix_cfg)
    world.para()
    ending(world, a, b, crop_cfg)

    world.facts.update(
        giantness=int(crop.meters["giant"]),
        solved=crop.meters["calm"] >= THRESHOLD,
        friendship=max(a.memes["friendship"], b.memes["friendship"]),
    )
    return world


KNOWLEDGE = {
    "garden": [
        (
            "What is a garden plot?",
            "A garden plot is a small piece of ground set aside for growing plants. People loosen the soil there and care for the rows so vegetables or flowers can grow well.",
        )
    ],
    "irish": [
        (
            "What does Irish mean in a name like Irish setter or Irish pony?",
            "Irish means the animal breed or kind is connected with Ireland. It is part of the name, like saying a golden retriever or a mountain pony.",
        )
    ],
    "dog": [
        (
            "Why might a dog bark when something on a path looks unsafe?",
            "Dogs often notice movement, trouble, or strange changes before people do. A bark can be a warning that something needs attention.",
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small kind of horse. Ponies are sturdy and can be very steady on paths and around gardens.",
        )
    ],
    "goat": [
        (
            "What is a goat like?",
            "A goat is a nimble animal with quick feet and a curious nature. Goats often notice new things and like to poke around.",
        )
    ],
    "beans": [
        (
            "How do bean plants grow?",
            "Bean plants often make long vines that climb and curl around supports. If they have room and care, they can spread quickly.",
        )
    ],
    "pumpkin": [
        (
            "Why do pumpkin plants take up so much space?",
            "Pumpkin plants send long runners and wide leaves over the ground. That helps feed the pumpkins, but it also means they can cover a lot of garden space.",
        )
    ],
    "sunflower": [
        (
            "Why are sunflowers tall?",
            "Sunflowers grow tall so their flowers can reach the sun. A strong stalk helps hold up the heavy flower head.",
        )
    ],
    "water": [
        (
            "Why can too much water make plants grow oddly?",
            "Plants need water, but too much can throw their growing pattern out of balance. In a story, that makes a fun tall-tale reason for wild overgrowth.",
        )
    ],
    "compost": [
        (
            "What is compost?",
            "Compost is old plant material that has broken down into rich, dark food for the soil. Gardeners use it to help plants grow strong.",
        )
    ],
    "seed": [
        (
            "What does a seed do?",
            "A seed is a tiny beginning for a plant. When it gets water, warmth, and soil, it can sprout roots and leaves.",
        )
    ],
    "moonseed": [
        (
            "What is a made-up moonseed in a tall tale?",
            "A moonseed in a tall tale is a pretend magical seed that makes things grow in impossible ways. It belongs to storybook wonder, not ordinary gardening.",
        )
    ],
    "fix": [
        (
            "Why is it smart to match a fix to the real cause of a problem?",
            "A problem gets solved faster when you fix what is actually causing it. Guessing at random can waste time and leave the trouble in place.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "garden",
    "irish",
    "dog",
    "pony",
    "goat",
    "beans",
    "pumpkin",
    "sunflower",
    "water",
    "compost",
    "seed",
    "moonseed",
    "fix",
]


@dataclass
class StoryParams:
    crop: str
    cause: str
    fix: str
    helper: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crop_cfg = f["crop_cfg"]
    helper_cfg = f["helper_cfg"]
    cause_cfg = f["cause_cfg"]
    a = f["friend1"]
    b = f["friend2"]
    return [
        f'Write a short Tall Tale for ages 3 to 5 that includes the words "plot", "irish", and "wend", and centers on friendship and curiosity in a giant {crop_cfg.patch}.',
        f"Tell a tall story where two friends, {a.id} and {b.id}, wend farther and farther through a garden plot with {helper_cfg.label}, repeating the journey beat until they discover why the row has grown wild.",
        f"Write a child-facing story about friendship where curiosity leads two children through an impossible garden mystery caused by {cause_cfg.label}, and end with an image that proves the plot is calm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    helper = f["helper"]
    crop_cfg = f["crop_cfg"]
    cause_cfg = f["cause_cfg"]
    fix_cfg = f["fix_cfg"]
    giant = f["giantness"]
    landmarks = f["landmarks"]
    helper_name = helper.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and {helper_name}. They work together when a giant row in the garden plot turns into a mystery.",
        ),
        (
            f"Why did {a.id} and {b.id} keep going down the row?",
            f"They were curious because the {crop_cfg.plural_label} had grown far beyond anything ordinary. Their friendship helped them keep wending on together instead of turning back alone.",
        ),
        (
            "What made the story feel like a repetition?",
            f"The children kept going farther and farther down the same row again and again. They passed {', '.join(landmarks[:-1])}, and then {landmarks[-1]}, with each step proving the plot was even bigger than they first thought.",
        ),
        (
            f"What was really causing the giant {crop_cfg.plural_label}?",
            f"The trouble came from {cause_cfg.label}. They figured it out because they found the clue at the end of the row and matched it to what they were seeing in the plot.",
        ),
        (
            "How did they solve the problem?",
            f"{fix_cfg.qa_text}. Because they fixed the real cause, the wild growing slowed down and the path became safe again.",
        ),
        (
            "How tall was the row in the story?",
            f"It was tall-tale tall: the world model gave the row a giantness of {giant}, which is why the children had so many landmarks to pass. In the story, that turned into a row that seemed to go on and on before it finally made sense.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["crop_cfg"].tags) | set(f["cause_cfg"].tags) | set(f["fix_cfg"].tags) | set(f["helper_cfg"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="beans",
        cause="hose",
        fix="close_spigot",
        helper="irish_setter",
        friend1="Molly",
        friend1_gender="girl",
        friend2="Finn",
        friend2_gender="boy",
    ),
    StoryParams(
        crop="pumpkins",
        cause="compost",
        fix="patch_compost",
        helper="irish_goat",
        friend1="Rose",
        friend1_gender="girl",
        friend2="Owen",
        friend2_gender="boy",
    ),
    StoryParams(
        crop="sunflowers",
        cause="moonseed",
        fix="move_moonseed",
        helper="irish_pony",
        friend1="Nora",
        friend1_gender="girl",
        friend2="Jack",
        friend2_gender="boy",
    ),
    StoryParams(
        crop="sunflowers",
        cause="hose",
        fix="close_spigot",
        helper="irish_setter",
        friend1="Anna",
        friend1_gender="girl",
        friend2="Leo",
        friend2_gender="boy",
    ),
    StoryParams(
        crop="pumpkins",
        cause="hose",
        fix="close_spigot",
        helper="irish_pony",
        friend1="Maeve",
        friend1_gender="girl",
        friend2="Ben",
        friend2_gender="boy",
    ),
]


ASP_RULES = r"""
crop_cause_ok(C, K) :- crop(C), cause(K), crop_allows(C, K), cause_fits(K, C).
sensible_fix(F)     :- fix(F), sense(F, S), sense_min(M), S >= M.
matches(K, F)       :- cause(K), fix(F), fixes(F, K).

valid(C, K, F)      :- crop_cause_ok(C, K), sensible_fix(F), matches(K, F).

#show valid/3.
#show sensible_fix/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        for cause_id in sorted(crop.compatible_causes):
            lines.append(asp.fact("crop_allows", crop_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for crop_id in sorted(cause.fits_crops):
            lines.append(asp.fact("cause_fits", cause_id, crop_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("fixes", fix_id, fix.targets))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {fix_id for fix_id, fix in FIXES.items() if fix.sense >= SENSE_MIN}
    asp_sensible = set(asp_sensible_fixes())
    if py_sensible == asp_sensible:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  clingo:", sorted(asp_sensible))
        print("  python:", sorted(py_sensible))

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: two friends wend through a giant garden plot with an Irish animal helper."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid crop/cause/fix combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_friend(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.cause:
        crop = CROPS[args.crop]
        cause = CAUSES[args.cause]
        if not cause_fits_crop(crop, cause):
            raise StoryError(explain_rejection(crop, cause))
    if args.cause and args.fix:
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not fix_matches_cause(cause, fix):
            raise StoryError(explain_fix(cause, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, cause_id, fix_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    friend1, g1 = _pick_friend(rng)
    friend2, g2 = _pick_friend(rng, avoid=friend1)
    return StoryParams(
        crop=crop_id,
        cause=cause_id,
        fix=fix_id,
        helper=helper_id,
        friend1=friend1,
        friend1_gender=g1,
        friend2=friend2,
        friend2_gender=g2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    crop_cfg = CROPS[params.crop]
    cause_cfg = CAUSES[params.cause]
    fix_cfg = FIXES[params.fix]
    helper_cfg = HELPERS[params.helper]

    if not cause_fits_crop(crop_cfg, cause_cfg):
        raise StoryError(explain_rejection(crop_cfg, cause_cfg))
    if not fix_matches_cause(cause_cfg, fix_cfg):
        raise StoryError(explain_fix(cause_cfg, fix_cfg))

    world = tell(
        crop_cfg=crop_cfg,
        cause_cfg=cause_cfg,
        fix_cfg=fix_cfg,
        helper_cfg=helper_cfg,
        friend1=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2=params.friend2,
        friend2_gender=params.friend2_gender,
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
        sensible = asp_sensible_fixes()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (crop, cause, fix) combos:\n")
        for crop_id, cause_id, fix_id in combos:
            print(f"  {crop_id:10} {cause_id:10} {fix_id}")
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
            header = f"### {p.friend1} & {p.friend2}: {p.crop} / {p.cause} / {p.fix} ({p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
