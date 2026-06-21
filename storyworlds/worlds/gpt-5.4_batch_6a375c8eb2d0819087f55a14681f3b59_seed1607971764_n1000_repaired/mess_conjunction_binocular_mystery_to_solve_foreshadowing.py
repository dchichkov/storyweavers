#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mess_conjunction_binocular_mystery_to_solve_foreshadowing.py
========================================================================================

A standalone storyworld about a small superhero-style mystery: a child hero finds
the same strange mess again and again, notices a clue, waits with a binocular,
and learns that the "villain" is really a needy little animal. The turn comes
from looking carefully instead of guessing. The ending proves what changed: the
hero solves the mystery kindly, and the mess stops.

This world deliberately uses:
- mystery to solve
- foreshadowing
- repetition

Required seed words appear in the stories:
- mess
- conjunction
- binocular
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Scene:
    id: str
    label: str
    place_text: str
    mess_text: str
    clue_text: str
    culprit_ids: set[str] = field(default_factory=set)
    sky_hint: str = ""
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
class Culprit:
    id: str
    label: str
    type: str
    sign: str
    reveal_text: str
    motive_text: str
    repeat_object: str
    fix_id: str
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
class Lookout:
    id: str
    label: str
    watch_text: str
    sees: set[str] = field(default_factory=set)
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
    for_culprit: str
    setup_text: str
    result_text: str
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


def _r_concern(world: World) -> list[str]:
    scene = world.get("scene")
    hero = world.get("hero")
    helper = world.get("helper")
    if scene.meters["mess"] < THRESHOLD:
        return []
    sig = ("concern",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    helper.memes["concern"] += 1
    return []


def _r_solved(world: World) -> list[str]:
    scene = world.get("scene")
    if scene.meters["clean"] < THRESHOLD or scene.meters["safe_supply"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="concern", tag="emotion", apply=_r_concern),
    Rule(name="solved", tag="emotion", apply=_r_solved),
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


SCENES = {
    "roof_garden": Scene(
        id="roof_garden",
        label="rooftop garden",
        place_text="the little rooftop garden above the apartment hall",
        mess_text="purple berry smears on the railing, shiny paper scraps in the basil box, and one flowerpot tipped sideways",
        clue_text="a black feather tucked behind the tipped pot",
        culprit_ids={"crow"},
        sky_hint="The roofs would glow silver when the evening conjunction rose.",
        tags={"mess", "garden", "crow"},
    ),
    "sunflower_steps": Scene(
        id="sunflower_steps",
        label="sunflower steps",
        place_text="the front steps beside the tall sunflowers",
        mess_text="sunflower seed shells all over the mat, dirt sprinkled across the steps, and one bright ribbon dragged into the leaves",
        clue_text="a gnawed sunflower stem with tiny tooth marks",
        culprit_ids={"squirrel"},
        sky_hint="The fence would be easy to watch when the evening conjunction brightened the sky.",
        tags={"mess", "sunflower", "squirrel"},
    ),
    "shed_path": Scene(
        id="shed_path",
        label="shed path",
        place_text="the stone path beside the garden shed",
        mess_text="muddy hand-shaped prints on the stones, apple peels near the can, and the lid sitting a little crooked",
        clue_text="a neat row of damp prints leading toward the fence",
        culprit_ids={"raccoon"},
        sky_hint="The yard would stay bright enough to watch when the evening conjunction climbed over the trees.",
        tags={"mess", "shed", "raccoon"},
    ),
}

CULPRITS = {
    "crow": Culprit(
        id="crow",
        label="crow",
        type="animal",
        sign="feather",
        reveal_text="A glossy crow swooped down, pecked up one bright paper scrap, and hopped around the flowerpot with clever little steps.",
        motive_text="It was not trying to be bad. It was gathering shiny nest things and berry bits for its high crooked nest.",
        repeat_object="shiny paper",
        fix_id="nest_basket",
        tags={"crow", "bird", "nest"},
    ),
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        type="animal",
        sign="tooth_marks",
        reveal_text="A striped squirrel zipped along the rail, stuffed seeds into its cheeks, and tugged the ribbon as if it were treasure.",
        motive_text="It was not making trouble on purpose. It wanted seeds to eat and soft ribbon for its leaf nest.",
        repeat_object="ribbon",
        fix_id="seed_tray",
        tags={"squirrel", "seeds", "nest"},
    ),
    "raccoon": Culprit(
        id="raccoon",
        label="raccoon",
        type="animal",
        sign="prints",
        reveal_text="A small raccoon climbed onto the can, nudged the lid aside with both paws, and sniffed at the apple peels.",
        motive_text="It was not a villain at all. It was hungry and had found the easiest snacks in the yard.",
        repeat_object="apple peels",
        fix_id="latch_bin",
        tags={"raccoon", "yard", "food"},
    ),
}

LOOKOUTS = {
    "attic_window": Lookout(
        id="attic_window",
        label="attic window",
        watch_text="from the attic window under the slanted roof",
        sees={"roof_garden", "sunflower_steps"},
        tags={"window", "watch"},
    ),
    "treehouse_platform": Lookout(
        id="treehouse_platform",
        label="treehouse platform",
        watch_text="from the treehouse platform where the rail felt steady under superhero knees",
        sees={"sunflower_steps", "shed_path"},
        tags={"treehouse", "watch"},
    ),
    "hall_balcony": Lookout(
        id="hall_balcony",
        label="hall balcony",
        watch_text="from the narrow hall balcony where a cape could flutter without getting in the way",
        sees={"roof_garden"},
        tags={"balcony", "watch"},
    ),
    "porch_bench": Lookout(
        id="porch_bench",
        label="porch bench",
        watch_text="from the porch bench tucked beside the rain boots",
        sees={"shed_path"},
        tags={"porch", "watch"},
    ),
}

FIXES = {
    "nest_basket": Fix(
        id="nest_basket",
        label="a basket of safe shiny ribbons",
        for_culprit="crow",
        setup_text="hung a little basket high by the rail and filled it with safe shiny ribbons and a few berries far from the flowerpots",
        result_text="The crow chose the basket instead of the basil box, and the flowerpots stayed standing.",
        tags={"kind_fix", "crow"},
    ),
    "seed_tray": Fix(
        id="seed_tray",
        label="a seed tray near the fence",
        for_culprit="squirrel",
        setup_text="set out a seed tray by the fence and tied a plain ribbon there instead of leaving treasure by the steps",
        result_text="The squirrel rushed to the tray instead of the mat, and the front steps stayed neat.",
        tags={"kind_fix", "squirrel"},
    ),
    "latch_bin": Fix(
        id="latch_bin",
        label="a latched scraps bin",
        for_culprit="raccoon",
        setup_text="snapped the compost lid shut and placed a small scraps tub deep in the yard where it would not spill on the stones",
        result_text="The raccoon sniffed the yard tub instead of pawing at the path-side can, and the stones stayed clean.",
        tags={"kind_fix", "raccoon"},
    ),
}

HERO_ALIASES = [
    "Comet Kid",
    "Captain Star-Cape",
    "Thunder Flash",
    "Night Beam",
    "Meteor Mask",
]

GIRL_NAMES = ["Ruby", "Maya", "Luna", "Zoe", "Ava", "Nora", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Noah", "Sam", "Jack"]


@dataclass
class StoryParams:
    scene: str
    culprit: str
    lookout: str
    fix: str
    name: str
    gender: str
    helper: str
    alias: str
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


def culprit_fits(scene_id: str, culprit_id: str) -> bool:
    scene = SCENES[scene_id]
    return culprit_id in scene.culprit_ids


def lookout_fits(scene_id: str, lookout_id: str) -> bool:
    lookout = LOOKOUTS[lookout_id]
    return scene_id in lookout.sees


def fix_fits(culprit_id: str, fix_id: str) -> bool:
    return FIXES[fix_id].for_culprit == culprit_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for culprit_id in CULPRITS:
            if not culprit_fits(scene_id, culprit_id):
                continue
            for lookout_id in LOOKOUTS:
                if not lookout_fits(scene_id, lookout_id):
                    continue
                for fix_id in FIXES:
                    if fix_fits(culprit_id, fix_id):
                        out.append((scene_id, culprit_id, lookout_id, fix_id))
    return out


def _use_repeat(world: World) -> str:
    hero = world.get("hero")
    hero.memes["repeat"] += 1
    return '"Heroes look twice," ' + hero.id + " whispered."


def introduce(world: World, alias: str) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["joy"] += 1
    world.say(
        f"After supper, {hero.id} tied on a towel-cape and became {alias}, the smallest superhero on the block."
    )
    world.say(
        f"{helper.label_word.capitalize()} smiled and said that every hero needed sharp eyes and a kind heart."
    )


def discover_mess(world: World, scene: Scene) -> None:
    scene_ent = world.get("scene")
    scene_ent.meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Down at {scene.place_text}, {hero_name(world)} found the same mess again: {scene.mess_text}."
    )
    world.say(_use_repeat(world))


def hero_name(world: World) -> str:
    return world.get("hero").id


def clue_beat(world: World, scene: Scene) -> None:
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    world.facts["clue"] = scene.clue_text
    world.say(
        f"There was one clue too: {scene.clue_text}. It did not solve the mystery yet, but it felt important."
    )


def plan_watch(world: World, lookout: Lookout, scene: Scene) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    tool = world.get("tool")
    hero.memes["resolve"] += 1
    world.say(
        f'"Then we do not guess," {helper.label_word} said. "We watch."'
    )
    world.say(
        f"{helper.label_word.capitalize()} brought out a sturdy binocular, and {hero.id} held it with both hands as if it were superhero gear."
    )
    world.say(
        f"{scene.sky_hint} {helper.label_word.capitalize()} pointed at the first bright pair of lights and said the sky event was called a conjunction."
    )
    world.say(_use_repeat(world))
    tool.meters["ready"] += 1
    world.facts["watch_place"] = lookout.label


def watch_and_reveal(world: World, scene: Scene, culprit_cfg: Culprit, lookout: Lookout) -> None:
    hero = world.get("hero")
    culprit = world.get("culprit")
    scene_ent = world.get("scene")
    culprit.meters["seen"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"Very still, {hero.id} waited {lookout.watch_text}. The cape fluttered, the binocular felt cool, and the yard went hush-hush."
    )
    world.say(
        f"Then the mystery moved. {culprit_cfg.reveal_text}"
    )
    world.say(
        f"{hero.id} gasped. The clue from before suddenly made sense."
    )
    scene_ent.meters["culprit_known"] += 1
    world.facts["seen_doing"] = culprit_cfg.reveal_text
    world.facts["motive"] = culprit_cfg.motive_text


def choose_kindness(world: World, fix: Fix, culprit_cfg: Culprit) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    scene_ent = world.get("scene")
    hero.memes["kindness"] += 1
    world.say(
        f"{culprit_cfg.motive_text}"
    )
    world.say(
        f'''"So the answer is not "shoo!"' {hero.id} said. '"The answer is help.'''
    )
    world.say(
        f"Together, {hero.id} and {helper.label_word} cleaned the old mess and {fix.setup_text}."
    )
    scene_ent.meters["mess"] = 0.0
    scene_ent.meters["clean"] += 1
    scene_ent.meters["safe_supply"] += 1
    propagate(world, narrate=False)


def ending(world: World, alias: str, fix: Fix) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"The next evening, {fix.result_text}"
    )
    world.say(
        f"{hero.id} tapped the binocular against {hero.pronoun('possessive')} knee and grinned. {alias} had solved the mystery without scaring anyone away."
    )
    world.say(
        f'And whenever {hero.id} saw a puzzling mess after that, {hero.pronoun()} remembered the same rule: "Heroes look twice."'
    )


def tell(
    scene: Scene,
    culprit_cfg: Culprit,
    lookout: Lookout,
    fix: Fix,
    *,
    name: str,
    gender: str,
    helper_type: str,
    alias: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=gender, role="hero", label=name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    world.add(Entity(id="scene", kind="thing", type="place", role="scene", label=scene.label))
    world.add(Entity(id="tool", kind="thing", type="tool", role="tool", label="binocular"))
    world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, role="culprit", label=culprit_cfg.label))

    world.facts["alias"] = alias
    world.facts["repeat_line"] = "Heroes look twice."
    world.facts["scene_cfg"] = scene
    world.facts["culprit_cfg"] = culprit_cfg
    world.facts["lookout_cfg"] = lookout
    world.facts["fix_cfg"] = fix

    introduce(world, alias)
    world.para()
    discover_mess(world, scene)
    clue_beat(world, scene)
    world.para()
    plan_watch(world, lookout, scene)
    watch_and_reveal(world, scene, culprit_cfg, lookout)
    world.para()
    choose_kindness(world, fix, culprit_cfg)
    ending(world, alias, fix)

    world.facts.update(
        hero=hero,
        helper=helper,
        culprit=world.get("culprit"),
        scene=world.get("scene"),
        tool=world.get("tool"),
        solved=world.get("scene").meters["clean"] >= THRESHOLD and world.get("culprit").meters["seen"] >= THRESHOLD,
        repeat_count=int(hero.memes["repeat"]),
    )
    return world


KNOWLEDGE = {
    "binocular": [
        (
            "What is a binocular?",
            "A binocular helps you look at faraway things so they seem closer. People use it for watching birds, stars, or anything small in the distance.",
        )
    ],
    "conjunction": [
        (
            "What is a conjunction in the sky?",
            "A conjunction is when two bright things in the sky look close together from Earth. They are not really bumping into each other; they only seem near from where we stand.",
        )
    ],
    "crow": [
        (
            "Why do crows pick up shiny things?",
            "Crows are curious birds, and some of them like to investigate bright objects. They may carry small shiny bits the way children collect treasures.",
        )
    ],
    "squirrel": [
        (
            "Why do squirrels carry seeds away?",
            "Squirrels gather food to eat later, and they often carry seeds or nuts to safer places. They also pull at soft things when building nests.",
        )
    ],
    "raccoon": [
        (
            "Why do raccoons open lids and boxes?",
            "Raccoons have clever paws and strong curiosity, so they poke and pry at things that might hide food. That is why people close bins tightly around them.",
        )
    ],
    "kind_fix": [
        (
            "What is a kind way to solve an animal problem?",
            "A kind fix keeps the place neat and also gives the animal a better choice. It solves the problem without hurting or frightening the animal.",
        )
    ],
}
KNOWLEDGE_ORDER = ["binocular", "conjunction", "crow", "squirrel", "raccoon", "kind_fix"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene_cfg"]
    culprit = f["culprit_cfg"]
    alias = f["alias"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "mess", "conjunction", and "binocular".',
        f"Tell a mystery-to-solve story where {hero.id}, also called {alias}, finds a strange mess at {scene.label}, notices a clue, and waits to discover that a {culprit.label} is responsible.",
        f'Write a gentle superhero mystery with foreshadowing and repetition, using the repeated line "Heroes look twice." and ending with a kind solution instead of punishment.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scene_cfg = f["scene_cfg"]
    culprit_cfg = f["culprit_cfg"]
    lookout_cfg = f["lookout_cfg"]
    fix_cfg = f["fix_cfg"]
    alias = f["alias"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who pretends to be the superhero {alias}, and {hero.pronoun('possessive')} {helper_word} who helps with the mystery.",
        ),
        (
            "What was the mystery?",
            f"The mystery was who kept leaving a mess at the {scene_cfg.label}. The same strange mess kept coming back, so {hero.id} knew something was happening there on purpose.",
        ),
        (
            "What clue did the hero find first?",
            f"{hero.id} first found {f['clue']}. That clue mattered later because it matched the real culprit once the watching began.",
        ),
        (
            f"Why did {hero.id} use the binocular?",
            f"{hero.id} used the binocular to watch from the {lookout_cfg.label} without guessing too soon. Looking carefully helped {hero.pronoun('object')} solve the mystery with proof instead of blame.",
        ),
        (
            "How was the mystery solved?",
            f"The mystery was solved when {hero.id} watched quietly and saw the {culprit_cfg.label} making the mess. The earlier clue suddenly made sense because it belonged with that animal.",
        ),
        (
            f"Why did the {culprit_cfg.label} make the mess?",
            f"{culprit_cfg.motive_text} That is why the answer was to change the place, not to act as if the animal were mean.",
        ),
        (
            "What did the hero do at the end?",
            f"{hero.id} and {helper_word} cleaned up and made {fix_cfg.label}. Because the animal had a better place to go, the mess stopped coming back.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"binocular", "conjunction", "kind_fix", f["culprit_cfg"].id}
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="roof_garden",
        culprit="crow",
        lookout="hall_balcony",
        fix="nest_basket",
        name="Ruby",
        gender="girl",
        helper="grandfather",
        alias="Comet Kid",
    ),
    StoryParams(
        scene="sunflower_steps",
        culprit="squirrel",
        lookout="treehouse_platform",
        fix="seed_tray",
        name="Leo",
        gender="boy",
        helper="mother",
        alias="Captain Star-Cape",
    ),
    StoryParams(
        scene="shed_path",
        culprit="raccoon",
        lookout="porch_bench",
        fix="latch_bin",
        name="Maya",
        gender="girl",
        helper="father",
        alias="Night Beam",
    ),
    StoryParams(
        scene="sunflower_steps",
        culprit="squirrel",
        lookout="attic_window",
        fix="seed_tray",
        name="Finn",
        gender="boy",
        helper="grandmother",
        alias="Thunder Flash",
    ),
]


def explain_invalid(scene_id: str, culprit_id: str, lookout_id: str, fix_id: str) -> str:
    if scene_id in SCENES and culprit_id in CULPRITS and not culprit_fits(scene_id, culprit_id):
        return (
            f"(No story: a {CULPRITS[culprit_id].label} does not fit the clue pattern at {SCENES[scene_id].label}. "
            f"Pick a culprit that really matches that mess.)"
        )
    if scene_id in SCENES and lookout_id in LOOKOUTS and not lookout_fits(scene_id, lookout_id):
        return (
            f"(No story: the {LOOKOUTS[lookout_id].label} cannot honestly watch the action at {SCENES[scene_id].label}. "
            f"Pick a lookout that can really see the mystery happen.)"
        )
    if culprit_id in CULPRITS and fix_id in FIXES and not fix_fits(culprit_id, fix_id):
        return (
            f"(No story: {FIXES[fix_id].label} is not the right kind solution for a {CULPRITS[culprit_id].label}. "
            f"The fix must match the real culprit's need.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


ASP_RULES = r"""
compatible(Scene, Culprit) :- scene(Scene), culprit(Culprit), fits(Scene, Culprit).
watchable(Scene, Lookout) :- scene(Scene), lookout(Lookout), sees(Lookout, Scene).
kind_fix(Culprit, Fix) :- culprit(Culprit), fix(Fix), fix_for(Fix, Culprit).

valid(Scene, Culprit, Lookout, Fix) :-
    compatible(Scene, Culprit),
    watchable(Scene, Lookout),
    kind_fix(Culprit, Fix).

solved :- chosen_scene(S), chosen_culprit(C), chosen_lookout(L), chosen_fix(F),
          valid(S, C, L, F).

#show valid/4.
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for cid in sorted(scene.culprit_ids):
            lines.append(asp.fact("fits", sid, cid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for lid, lookout in LOOKOUTS.items():
        lines.append(asp.fact("lookout", lid))
        for sid in sorted(lookout.sees):
            lines.append(asp.fact("sees", lid, sid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_for", fid, fix.for_culprit))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_scene", params.scene),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_lookout", params.lookout),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero mystery storyworld: a child solves a recurring mess by watching carefully."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--lookout", choices=LOOKOUTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--alias", choices=HERO_ALIASES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.culprit and not culprit_fits(args.scene, args.culprit):
        raise StoryError(explain_invalid(args.scene, args.culprit, args.lookout or "attic_window", args.fix or "nest_basket"))
    if args.scene and args.lookout and not lookout_fits(args.scene, args.lookout):
        raise StoryError(explain_invalid(args.scene, args.culprit or "crow", args.lookout, args.fix or "nest_basket"))
    if args.culprit and args.fix and not fix_fits(args.culprit, args.fix):
        raise StoryError(explain_invalid(args.scene or "roof_garden", args.culprit, args.lookout or "attic_window", args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.lookout is None or combo[2] == args.lookout)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, culprit_id, lookout_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    alias = args.alias or rng.choice(HERO_ALIASES)

    return StoryParams(
        scene=scene_id,
        culprit=culprit_id,
        lookout=lookout_id,
        fix=fix_id,
        name=name,
        gender=gender,
        helper=helper,
        alias=alias,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.lookout not in LOOKOUTS:
        raise StoryError(f"(Unknown lookout: {params.lookout})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not culprit_fits(params.scene, params.culprit) or not lookout_fits(params.scene, params.lookout) or not fix_fits(params.culprit, params.fix):
        raise StoryError(explain_invalid(params.scene, params.culprit, params.lookout, params.fix))

    world = tell(
        SCENES[params.scene],
        CULPRITS[params.culprit],
        LOOKOUTS[params.lookout],
        FIXES[params.fix],
        name=params.name,
        gender=params.gender,
        helper_type=params.helper,
        alias=params.alias,
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed on seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        solved_py = params.scene in SCENES and params.culprit in CULPRITS and params.lookout in LOOKOUTS and params.fix in FIXES and (
            culprit_fits(params.scene, params.culprit) and lookout_fits(params.scene, params.lookout) and fix_fits(params.culprit, params.fix)
        )
        solved_asp = asp_solved(params)
        if solved_py != solved_asp:
            bad += 1
    if bad == 0:
        print(f"OK: ASP solved-state matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: solved-state differs on {bad}/{len(cases)} scenarios.")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("generated empty story")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
            rendered = buf.getvalue()
        if "Heroes look twice." not in sample.story:
            raise StoryError("missing repeated line in smoke sample")
        if not rendered.strip():
            raise StoryError("emit produced no output")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, culprit, lookout, fix) combos:\n")
        for scene_id, culprit_id, lookout_id, fix_id in combos:
            print(f"  {scene_id:16} {culprit_id:10} {lookout_id:18} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.name}: {p.scene} ({p.culprit}, {p.lookout}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
