#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py
===================================================================================

A standalone story world for a tiny fable-like domain about an ostrich, a bottle
of perfume, a silly mistake, and a kind solution.

Premise
-------
An ostrich wants to seem especially grand for a small gathering. A bottle of
perfume promises a quick shortcut to admiration, but too much scent creates a
real physical problem in the shared space: sneezing friends or buzzing bees.
A kind helper does not mock the ostrich. Instead, the helper studies what kind
of perfume it is, chooses a fitting fix, and helps the ostrich solve the problem.
The ending image proves the lesson: gentle goodness and thoughtfulness smell
better than showing off.

Reasonableness constraint
-------------------------
Not every fix makes sense for every perfume in every place. Some places have
water for rinsing; some have dry sand that can absorb heavy oil perfume; some
only allow a breezy airing. The world refuses combinations where the chosen fix
would not really help.

Run it
------
python storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py
python storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py --all
python storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py --json
python storyworlds/worlds/gpt-5.4/ostrich_perfume_humor_kindness_problem_solving_fable.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "girl", "mother", "aunt"}
        male = {"rooster", "boy", "father", "uncle"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    image: str
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
class Occasion:
    id: str
    goal: str
    crowd_line: str
    ending_line: str
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
class Perfume:
    id: str
    label: str
    scent: str
    residue: str
    effect: str
    strength: int
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
class Dose:
    id: str
    amount: int
    apply_text: str
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
class Fix:
    id: str
    label: str
    solvents: set[str] = field(default_factory=set)
    soothes: set[str] = field(default_factory=set)
    power: int = 0
    action: str = ""
    lesson_image: str = ""
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


def severity_of(perfume: Perfume, dose: Dose) -> int:
    return perfume.strength + dose.amount


def issue_from(perfume: Perfume) -> str:
    return perfume.effect


def fix_works_here(setting: Setting, fix: Fix) -> bool:
    return fix.id in setting.affords


def fix_matches_perfume(perfume: Perfume, fix: Fix) -> bool:
    residue_ok = perfume.residue in fix.solvents or not fix.solvents
    effect_ok = perfume.effect in fix.soothes
    return residue_ok and effect_ok


def can_solve(setting: Setting, perfume: Perfume, dose: Dose, fix: Fix) -> bool:
    return (
        fix_works_here(setting, fix)
        and fix_matches_perfume(perfume, fix)
        and fix.power >= severity_of(perfume, dose)
    )


def _r_scent_bother(world: World) -> list[str]:
    ostrich = world.get("ostrich")
    if ostrich.meters["scent_cloud"] < THRESHOLD:
        return []
    sig = ("scent_bother", world.facts["issue"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    severity = world.facts["severity"]
    crowd = world.get("crowd")
    crowd.meters["discomfort"] += float(severity)
    helper = world.get("helper")
    helper.memes["concern"] += 1
    ostrich.memes["embarrassment"] += 1
    if world.facts["issue"] == "sneeze":
        helper.meters["sneezes"] += 1
        crowd.meters["sneezes"] += float(severity)
        return ["__sneeze__"]
    crowd.meters["buzzing"] += float(severity)
    ostrich.meters["bees"] += float(severity)
    return ["__bees__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="scent_bother", tag="physical", apply=_r_scent_bother),
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


SETTINGS = {
    "oasis": Setting(
        id="oasis",
        place="an oasis with cool reeds and a clear pool",
        image="Date palms leaned over the water, and dragonflies stitched blue lines through the air.",
        affords={"pond_rinse", "reed_fan"},
        tags={"water", "pond"},
    ),
    "market_road": Setting(
        id="market_road",
        place="the shady road beside the market",
        image="Bright cloth awnings flapped overhead, and the dust held the prints of many busy feet.",
        affords={"sand_roll", "reed_fan"},
        tags={"sand", "road"},
    ),
    "garden": Setting(
        id="garden",
        place="a walled garden full of herbs",
        image="Mint and basil nodded in neat rows, and a stone basin held fresh water for thirsty birds.",
        affords={"pond_rinse", "reed_fan", "sand_roll"},
        tags={"garden", "water", "sand"},
    ),
}

OCCASIONS = {
    "tea": Occasion(
        id="tea",
        goal="join the afternoon tea under the acacia tree",
        crowd_line="The little gathering had cups of mint tea, plates of figs, and a circle of cheerful animal neighbors.",
        ending_line="Soon the tea table was calm again, and laughter had room to sit down beside the cups.",
    ),
    "story_circle": Occasion(
        id="story_circle",
        goal="tell a story at sunset",
        crowd_line="The neighbors were gathering in a circle, ready to trade stories while the sun turned gold and small.",
        ending_line="Soon the story circle settled again, and even the shadows seemed to listen.",
    ),
    "berry_feast": Occasion(
        id="berry_feast",
        goal="help at the berry feast",
        crowd_line="Baskets of berries waited in the shade, and everyone was bringing something useful or kind.",
        ending_line="Soon the berry feast felt easy again, and the bowls of fruit shone like little rubies.",
    ),
}

PERFUMES = {
    "rose_mist": Perfume(
        id="rose_mist",
        label="rose perfume",
        scent="a pink, sweet smell like a whole bush of roses trying to sing at once",
        residue="water",
        effect="sneeze",
        strength=1,
        tags={"perfume", "sneeze", "rose"},
    ),
    "citrus_splash": Perfume(
        id="citrus_splash",
        label="citrus perfume",
        scent="a bright lemony smell that jumped into every nose in a hurry",
        residue="water",
        effect="sneeze",
        strength=2,
        tags={"perfume", "sneeze", "citrus"},
    ),
    "amber_oil": Perfume(
        id="amber_oil",
        label="amber perfume",
        scent="a thick honey-spice smell that drifted slowly and stuck to every feather",
        residue="oil",
        effect="bees",
        strength=2,
        tags={"perfume", "bees", "amber"},
    ),
}

DOSES = {
    "dab": Dose(
        id="dab",
        amount=1,
        apply_text="One neat dab would have been enough, but that did not seem grand enough to Ostrich.",
    ),
    "splash": Dose(
        id="splash",
        amount=2,
        apply_text="Ostrich tipped the bottle once, then once again, until the scent splashed across neck and wings.",
    ),
}

FIXES = {
    "pond_rinse": Fix(
        id="pond_rinse",
        label="a quick rinse in the cool water",
        solvents={"water"},
        soothes={"sneeze", "bees"},
        power=4,
        action="led Ostrich to the basin and helped swish the perfume away with cool water",
        lesson_image="When the last sharp smell floated off, the clean reeds and the warm earth smelled good enough all by themselves.",
        tags={"water", "washing"},
    ),
    "sand_roll": Fix(
        id="sand_roll",
        label="a roll in clean dry sand",
        solvents={"oil"},
        soothes={"bees"},
        power=4,
        action="showed Ostrich a patch of clean dry sand and helped brush the heavy perfume out feather by feather",
        lesson_image="The sand took the sticky scent with it, and Ostrich smelled once more like sunshine, dust, and plain honest feathers.",
        tags={"sand", "brushing"},
    ),
    "reed_fan": Fix(
        id="reed_fan",
        label="a patient fanning with broad reeds",
        solvents=set(),
        soothes={"sneeze"},
        power=3,
        action="stood beside Ostrich and fanned the air with broad reeds until the crowded smell grew thin and gentle",
        lesson_image="Soon the wind did the boasting for nobody, and the evening smelled only of tea, grass, and the little fire of sunset.",
        tags={"wind", "air"},
    ),
}

HELPERS = {
    "tortoise": {
        "label": "Tortoise",
        "type": "animal",
        "voice": "slow and steady",
        "kindness": "Tortoise never laughed when a friend made a foolish choice.",
    },
    "monkey": {
        "label": "Monkey",
        "type": "animal",
        "voice": "quick and bright",
        "kindness": "Monkey liked jokes, but liked helping even more.",
    },
    "gazelle": {
        "label": "Gazelle",
        "type": "animal",
        "voice": "gentle and graceful",
        "kindness": "Gazelle spoke so kindly that even embarrassment could listen.",
    },
}

OSTRICH_NAMES = ["Ostra", "Long-Step", "Feather-Foot", "Nella", "Pip", "Tall One"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for perfume_id, perfume in PERFUMES.items():
            for dose_id, dose in DOSES.items():
                for fix_id, fix in FIXES.items():
                    if can_solve(setting, perfume, dose, fix):
                        combos.append((setting_id, perfume_id, dose_id, fix_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    occasion: str
    perfume: str
    dose: str
    fix: str
    helper: str
    ostrich_name: str
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
        setting="oasis",
        occasion="tea",
        perfume="rose_mist",
        dose="splash",
        fix="pond_rinse",
        helper="tortoise",
        ostrich_name="Ostra",
    ),
    StoryParams(
        setting="market_road",
        occasion="story_circle",
        perfume="amber_oil",
        dose="dab",
        fix="sand_roll",
        helper="monkey",
        ostrich_name="Long-Step",
    ),
    StoryParams(
        setting="garden",
        occasion="berry_feast",
        perfume="citrus_splash",
        dose="dab",
        fix="reed_fan",
        helper="gazelle",
        ostrich_name="Pip",
    ),
    StoryParams(
        setting="garden",
        occasion="tea",
        perfume="amber_oil",
        dose="dab",
        fix="sand_roll",
        helper="tortoise",
        ostrich_name="Tall One",
    ),
]


def explain_rejection(setting: Setting, perfume: Perfume, dose: Dose, fix: Fix) -> str:
    if not fix_works_here(setting, fix):
        return (
            f"(No story: {fix.label} is not available in {setting.place}. "
            f"A fable needs a fix the helper can truly use in that place.)"
        )
    if not fix_matches_perfume(perfume, fix):
        return (
            f"(No story: {fix.label} does not fit {perfume.label}. "
            f"This perfume leaves a {perfume.residue} residue and causes {perfume.effect}, "
            f"so the chosen fix would not honestly solve the problem.)"
        )
    return (
        f"(No story: {fix.label} is too weak for this much {perfume.label}. "
        f"The solution must actually calm the trouble it caused.)"
    )


def predict_problem(world: World) -> dict:
    sim = world.copy()
    ostrich = sim.get("ostrich")
    ostrich.meters["scent_cloud"] += 1
    propagate(sim, narrate=False)
    return {
        "issue": sim.facts["issue"],
        "discomfort": sim.get("crowd").meters["discomfort"],
        "sneezes": sim.get("crowd").meters["sneezes"],
        "buzzing": sim.get("crowd").meters["buzzing"],
    }


def introduce(world: World, ostrich: Entity, occasion: Occasion) -> None:
    ostrich.memes["pride"] += 1
    world.say(
        f"In {world.setting.place}, there lived an ostrich named {ostrich.id} who liked to stand tall even when nobody had asked for a tall bird."
    )
    world.say(world.setting.image)
    world.say(
        f"That day, {ostrich.id} wanted to {occasion.goal}. {ostrich.pronoun('subject').capitalize()} hoped everyone would say not only, \"What a kind neighbor,\" but also, \"What a magnificent one.\""
    )


def find_perfume(world: World, ostrich: Entity, perfume: Perfume) -> None:
    bottle = world.get("bottle")
    bottle.attrs["perfume"] = perfume.id
    world.say(
        f"Beside the path lay a small bottle of {perfume.label}. It smelled like {perfume.scent}."
    )
    world.say(
        f"{ostrich.id} lifted the bottle and thought, \"If a little good smell is charming, then more must be splendid.\""
    )


def gather_scene(world: World, occasion: Occasion) -> None:
    world.say(occasion.crowd_line)


def apply_perfume(world: World, ostrich: Entity, perfume: Perfume, dose: Dose) -> None:
    world.say(dose.apply_text)
    ostrich.meters["scent_cloud"] += 1
    world.facts["applied_label"] = perfume.label
    propagate(world, narrate=False)
    severity = world.facts["severity"]
    if world.facts["issue"] == "sneeze":
        word = "strong" if severity >= 3 else "sharp"
        world.say(
            f"In another blink, the air around {ostrich.id} grew so {word} with perfume that the nearest noses wrinkled before the nearest mouths could smile."
        )
    else:
        world.say(
            f"In another blink, the sweet heavy trail of perfume drifted behind {ostrich.id} like an invisible ribbon, and every small buzzing thing in the neighborhood seemed to notice."
        )


def trouble(world: World, ostrich: Entity, helper: Entity) -> None:
    if world.facts["issue"] == "sneeze":
        sneezes = int(world.get("crowd").meters["sneezes"])
        if sneezes <= 1:
            crowd_line = f"{helper.id} gave one surprised sneeze."
        else:
            crowd_line = f"All around the circle came little explosions of sound: \"hff! hff! hff!\""
        world.say(
            f"{crowd_line} Cups rattled, feathers fluttered, and {ostrich.id} realized that perfume had walked into the gathering before kindness had."
        )
    else:
        world.say(
            f"A pair of bees began to loop curiously around {ostrich.id}'s neck, then three more joined them. {ostrich.id} tried to bow with dignity, but it is hard to bow grandly while tiptoeing away from bees."
        )
    ostrich.memes["embarrassment"] += 1
    world.say(
        f"The other animals were not angry, only uncomfortable, and that made {ostrich.id} feel smaller than if they had scolded."
    )


def kind_helper_step(world: World, helper: Entity, ostrich: Entity, fix: Fix) -> None:
    helper.memes["kindness"] += 1
    world.say(world.facts["helper_kindness"])
    world.say(
        f'"Come along," {helper.id} said in a calm voice. "A problem is easier to carry when two sets of feet are under it."'
    )
    world.say(
        f"{helper.id} sniffed once, looked at the feathers, and chose {fix.label} instead of blame."
    )


def solve(world: World, helper: Entity, ostrich: Entity, fix: Fix) -> None:
    helper.memes["cleverness"] += 1
    ostrich.memes["gratitude"] += 1
    helper.meters["helped"] += 1
    world.say(
        f"{helper.id} {fix.action}."
    )
    ostrich.meters["scent_cloud"] = 0.0
    ostrich.meters["bees"] = 0.0
    crowd = world.get("crowd")
    crowd.meters["discomfort"] = 0.0
    crowd.meters["sneezes"] = 0.0
    crowd.meters["buzzing"] = 0.0
    ostrich.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        "Little by little, the trouble loosened its grip on the air."
    )


def apology_and_turn(world: World, ostrich: Entity, helper: Entity) -> None:
    ostrich.memes["kindness"] += 1
    world.say(
        f'"I wanted to seem special," {ostrich.id} admitted, "and I forgot to think about everyone else\'s nose."'
    )
    world.say(
        f'"Then today you can be special by being thoughtful," {helper.id} replied.'
    )
    world.say(
        f"{ostrich.id} went back to the gathering more gently than before and offered the first seat in the shade to the animal who had sneezed the hardest."
    )


def ending(world: World, ostrich: Entity, occasion: Occasion, fix: Fix) -> None:
    ostrich.memes["wisdom"] += 1
    world.say(occasion.ending_line)
    world.say(fix.lesson_image)
    world.say(
        f"And when {ostrich.id} finally stood among the others, nobody praised the perfume. They praised the apology, the helping hands, and the laugh {ostrich.pronoun('subject')} could now share at {ostrich.pronoun('possessive')} own expense."
    )
    world.say(
        "So the animals remembered: borrowed show fades quickly, but kindness and good sense travel farther than any scent."
    )


def tell(
    setting: Setting,
    occasion: Occasion,
    perfume: Perfume,
    dose: Dose,
    fix: Fix,
    helper_id: str,
    ostrich_name: str,
) -> World:
    world = World(setting)
    helper_cfg = HELPERS[helper_id]
    ostrich = world.add(Entity(id=ostrich_name, kind="character", type="animal", role="hero"))
    helper = world.add(Entity(id=helper_cfg["label"], kind="character", type=helper_cfg["type"], role="helper"))
    crowd = world.add(Entity(id="Crowd", kind="thing", type="crowd", label="the neighbors"))
    bottle = world.add(Entity(id="bottle", kind="thing", type="bottle", label="the perfume bottle"))

    world.facts["issue"] = issue_from(perfume)
    world.facts["severity"] = severity_of(perfume, dose)
    world.facts["helper_kindness"] = helper_cfg["kindness"]
    world.facts["perfume_cfg"] = perfume
    world.facts["dose_cfg"] = dose
    world.facts["fix_cfg"] = fix
    world.facts["occasion"] = occasion
    world.facts["setting"] = setting
    world.facts["hero"] = ostrich
    world.facts["helper"] = helper
    world.facts["crowd"] = crowd

    introduce(world, ostrich, occasion)
    gather_scene(world, occasion)
    world.para()
    find_perfume(world, ostrich, perfume)
    pred = predict_problem(world)
    world.facts["predicted_issue"] = pred["issue"]
    world.facts["predicted_discomfort"] = pred["discomfort"]
    apply_perfume(world, ostrich, perfume, dose)
    trouble(world, ostrich, helper)
    world.para()
    kind_helper_step(world, helper, ostrich, fix)
    solve(world, helper, ostrich, fix)
    apology_and_turn(world, ostrich, helper)
    world.para()
    ending(world, ostrich, occasion, fix)

    world.facts["resolved"] = True
    return world


KNOWLEDGE = {
    "perfume": [
        (
            "What is perfume?",
            "Perfume is a liquid made to give a strong smell. A tiny bit can be pleasant, but too much can bother people nearby.",
        )
    ],
    "sneeze": [
        (
            "Why can a strong smell make someone sneeze?",
            "A strong smell can tickle or irritate the inside of the nose. Then the body sneezes to push the irritation away.",
        )
    ],
    "bees": [
        (
            "Why might bees come near a sweet smell?",
            "Bees look for sweet flower-like scents because flowers often have nectar. A strong sweet smell can make them curious, even if it comes from the wrong place.",
        )
    ],
    "water": [
        (
            "Why does washing help remove some smells?",
            "Water can carry away perfume that sits lightly on feathers, fur, or skin. When the smell is rinsed off, the air around it becomes gentler too.",
        )
    ],
    "sand": [
        (
            "How can clean sand help with a sticky smell?",
            "Dry sand can soak up oily, sticky perfume and help brush it away. That makes it useful when water alone would not be the best first fix.",
        )
    ],
    "wind": [
        (
            "Why can moving air help with a smell?",
            "Moving air spreads a smell out so it is not all crowded in one place. That can make the smell much softer for everyone nearby.",
        )
    ],
    "kindness": [
        (
            "What does kindness look like when someone makes a mistake?",
            "Kindness means helping without being cruel. You can notice the problem, speak gently, and still help fix what went wrong.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means looking closely at what is wrong and choosing a fix that truly fits. Good problem solving is thoughtful, not just fast.",
        )
    ],
}

KNOWLEDGE_ORDER = ["perfume", "sneeze", "bees", "water", "sand", "wind", "kindness", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    perfume = f["perfume_cfg"]
    occasion = f["occasion"]
    issue = f["issue"]
    issue_phrase = "a cloud of sneezing" if issue == "sneeze" else "a comic dance away from bees"
    return [
        (
            f'Write a short fable for a young child about an ostrich who uses {perfume.label} before trying to {occasion.goal}, '
            f'but causes {issue_phrase} and learns a lesson about kindness and good sense.'
        ),
        (
            f"Tell a gentle animal story where {hero.id} wants to seem impressive, makes a silly mistake with perfume, "
            f"and {helper.id} solves the problem kindly instead of teasing."
        ),
        (
            'Write a humorous fable using the words "ostrich" and "perfume" that ends by showing that thoughtfulness is better than showing off.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    perfume = f["perfume_cfg"]
    fix = f["fix_cfg"]
    occasion = f["occasion"]
    issue = f["issue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about an ostrich named {hero.id} and {helper.id}, the kind friend who helped. The story follows a silly mistake and a gentle solution.",
        ),
        (
            f"Why did {hero.id} use the perfume?",
            f"{hero.id} wanted to {occasion.goal} and hoped to seem especially grand. The perfume felt like a shortcut to admiration, so {hero.pronoun('subject')} forgot to think about everyone else first.",
        ),
    ]
    if issue == "sneeze":
        qa.append(
            (
                "What problem did the perfume cause?",
                f"The smell grew so strong that the gathering began to sneeze. The trouble was not meanness from the crowd; it was the crowded air around {hero.id}.",
            )
        )
    else:
        qa.append(
            (
                "What problem did the perfume cause?",
                f"The sweet heavy smell drew curious bees around {hero.id}. That made standing proudly impossible, because {hero.pronoun('subject')} had to keep fussing away from them.",
            )
        )
    qa.append(
        (
            f"How did {helper.id} help solve the problem?",
            f"{helper.id} chose {fix.label} and used it right away. The fix matched the kind of perfume trouble, so the air calmed and the gathering could feel easy again.",
        )
    )
    qa.append(
        (
            f"What did {hero.id} learn?",
            f"{hero.id} learned that being noticed is not the same as being good. At the end, the other animals admired the apology and the thoughtful behavior more than the perfume.",
        )
    )
    qa.append(
        (
            "Why is this story funny as well as kind?",
            f"It is funny because the problem is silly: perfume meant to make {hero.id} impressive makes everything awkward instead. It stays kind because nobody chooses cruelty; the laughter comes after the problem is solved and shared gently.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"perfume", "kindness", "problem_solving"}
    perfume = world.facts["perfume_cfg"]
    fix = world.facts["fix_cfg"]
    tags |= set(perfume.tags)
    tags |= set(fix.tags)
    if "washing" in tags or "water" in tags:
        tags.add("water")
    if "brushing" in tags or "sand" in tags:
        tags.add("sand")
    if "wind" in tags or "air" in tags:
        tags.add("wind")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: issue={world.facts.get('issue')} severity={world.facts.get('severity')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, D, F) :-
    setting(S), perfume(P), dose(D), fix(F),
    affords(S, F),
    soothes(F, E), effect(P, E),
    (
      residue(P, R), solvent(F, R)
      ;
      no_solvent_need(F)
    ),
    strength(P, PS), amount(D, DA), power(F, FP), FP >= PS + DA.

issue(P, sneeze) :- effect(P, sneeze).
issue(P, bees)   :- effect(P, bees).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for fid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, fid))
    for pid, perfume in PERFUMES.items():
        lines.append(asp.fact("perfume", pid))
        lines.append(asp.fact("residue", pid, perfume.residue))
        lines.append(asp.fact("effect", pid, perfume.effect))
        lines.append(asp.fact("strength", pid, perfume.strength))
    for did, dose in DOSES.items():
        lines.append(asp.fact("dose", did))
        lines.append(asp.fact("amount", did, dose.amount))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
        if not fix.solvents:
            lines.append(asp.fact("no_solvent_need", fid))
        for solvent in sorted(fix.solvents):
            lines.append(asp.fact("solvent", fid, solvent))
        for effect in sorted(fix.soothes):
            lines.append(asp.fact("soothes", fid, effect))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_issue(perfume_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_perfume", perfume_id), "#show issue/2."))
    atoms = asp.atoms(model, "issue")
    found = [issue for pid, issue in atoms if pid == perfume_id]
    return found[0] if found else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an ostrich, too much perfume, and a kind practical fix."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--perfume", choices=PERFUMES)
    ap.add_argument("--dose", choices=DOSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ostrich-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.perfume and args.dose and args.fix:
        setting = SETTINGS[args.setting]
        perfume = PERFUMES[args.perfume]
        dose = DOSES[args.dose]
        fix = FIXES[args.fix]
        if not can_solve(setting, perfume, dose, fix):
            raise StoryError(explain_rejection(setting, perfume, dose, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.perfume is None or combo[1] == args.perfume)
        and (args.dose is None or combo[2] == args.dose)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, perfume_id, dose_id, fix_id = rng.choice(sorted(combos))
    occasion_id = args.occasion or rng.choice(sorted(OCCASIONS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    ostrich_name = args.ostrich_name or rng.choice(OSTRICH_NAMES)

    return StoryParams(
        setting=setting_id,
        occasion=occasion_id,
        perfume=perfume_id,
        dose=dose_id,
        fix=fix_id,
        helper=helper_id,
        ostrich_name=ostrich_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        occasion = OCCASIONS[params.occasion]
        perfume = PERFUMES[params.perfume]
        dose = DOSES[params.dose]
        fix = FIXES[params.fix]
        if params.helper not in HELPERS:
            raise StoryError(f"(Unknown helper: {params.helper})")
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err})") from err

    if not can_solve(setting, perfume, dose, fix):
        raise StoryError(explain_rejection(setting, perfume, dose, fix))

    world = tell(
        setting=setting,
        occasion=occasion,
        perfume=perfume,
        dose=dose,
        fix=fix,
        helper_id=params.helper,
        ostrich_name=params.ostrich_name,
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

    bad_issue = []
    for perfume_id in sorted(PERFUMES):
        if asp_issue(perfume_id) != issue_from(PERFUMES[perfume_id]):
            bad_issue.append(perfume_id)
    if not bad_issue:
        print("OK: issue classification matches for every perfume.")
    else:
        rc = 1
        print("MISMATCH in issue classification:", bad_issue)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify behavior
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Default generate produced an empty story.)")
        print("OK: default random generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify behavior
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show issue/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, perfume, dose, fix) combos:\n")
        for setting_id, perfume_id, dose_id, fix_id in combos:
            print(f"  {setting_id:12} {perfume_id:14} {dose_id:6} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
                f"### {p.ostrich_name}: {p.perfume} at {p.setting} "
                f"({p.dose}, {p.fix}, helper={p.helper})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
