#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py
============================================================================

A standalone story world for a tall-tale snack-sharing story: one enormous treat,
one old steel slicer, a curious child, and a crowd that can only all eat if the
child notices how to make thinner slices and then chooses to share.

The world is built around a simple common-sense constraint:

    cutter power must meet the food's toughness
    AND
    the food's base slices plus the cutter's thin-slice bonus must feed the crowd

If that does not hold, the world refuses the story. In the stories it *does*
tell, curiosity is not decorative: the child studies the steel cutter, notices
the mysterious "cut-gerund" stamp on its side, discovers the thin-slice notch,
and that discovery changes the physical state of the world by increasing how
many slices the food yields. Sharing then resolves the social tension.

Run it
------
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py --food cheese_wheel --cutter river_saw
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py --food molasses_cake --cutter wagon_wheel
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4/steel_cut_gerund_curiosity_sharing_tall_tale.py --verify
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
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    boast: str
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
class Food:
    id: str
    label: str
    phrase: str
    hardness: int
    base_slices: int
    giant_line: str
    aroma: str
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
class Cutter:
    id: str
    label: str
    phrase: str
    power: int
    thin_bonus: int
    motion: str
    discover: str
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
class Crowd:
    id: str
    label: str
    phrase: str
    need: int
    line_image: str
    smallest: str
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


SETTINGS = {
    "mesa_picnic": Setting(
        id="mesa_picnic",
        place="the red mesa picnic grounds",
        boast="The wind there was so wide it could have dried a lake before supper.",
        ending="By sunset, even the mesa shadows looked full and friendly.",
        tags={"picnic"},
    ),
    "river_fair": Setting(
        id="river_fair",
        place="the river fair",
        boast="The river shone so bright that minnows had to squint.",
        ending="By dusk, the fair lights winked on, and nobody went home hungry.",
        tags={"fair"},
    ),
    "barn_social": Setting(
        id="barn_social",
        place="the old barn social",
        boast="The barn roof was said to creak polite hellos to every swallow that passed.",
        ending="When the lanterns glowed, the whole barn hummed like a happy fiddle.",
        tags={"barn"},
    ),
}

FOODS = {
    "apple_pie": Food(
        id="apple_pie",
        label="apple pie",
        phrase="a mountain-high apple pie",
        hardness=1,
        base_slices=6,
        giant_line="It was so broad that two bluebirds could have landed on the crust and argued about rent.",
        aroma="The smell of apples and cinnamon drifted so far that even the fence posts seemed hungry.",
        tags={"pie", "food"},
    ),
    "peach_cobbler": Food(
        id="peach_cobbler",
        label="peach cobbler",
        phrase="a bubbling peach cobbler in a pan big as a washtub",
        hardness=1,
        base_slices=7,
        giant_line="It bubbled at the edges like a little sunset trying to climb out.",
        aroma="Sweet peach steam rolled up in curls as soft as summer blankets.",
        tags={"cobbler", "food"},
    ),
    "cheese_wheel": Food(
        id="cheese_wheel",
        label="cheese wheel",
        phrase="a cheese wheel taller than a stepping stool",
        hardness=2,
        base_slices=5,
        giant_line="The rind looked stout enough to stop a sneeze in midair.",
        aroma="It smelled rich and warm, like the good part of a picnic basket.",
        tags={"cheese", "food"},
    ),
    "molasses_cake": Food(
        id="molasses_cake",
        label="molasses cake",
        phrase="a dark molasses cake with a shine like polished boots",
        hardness=2,
        base_slices=4,
        giant_line="It stood there as solemn as a town clock and almost as tall.",
        aroma="Its deep sweet smell made the air feel slow and cozy.",
        tags={"cake", "food"},
    ),
}

CUTTERS = {
    "wagon_wheel": Cutter(
        id="wagon_wheel",
        label="wagon-wheel slicer",
        phrase="an old steel wagon-wheel slicer",
        power=1,
        thin_bonus=2,
        motion="rolled forward with a bright singing whisper",
        discover="a narrow notch hidden under the steel handle",
        tags={"steel", "slicer"},
    ),
    "river_saw": Cutter(
        id="river_saw",
        label="river saw",
        phrase="a long steel river saw",
        power=2,
        thin_bonus=3,
        motion="glided through food as neat as a fish through water",
        discover="a tiny silver pin that set the blade for thin slices",
        tags={"steel", "slicer"},
    ),
    "sun_crank": Cutter(
        id="sun_crank",
        label="sun-crank slicer",
        phrase="a steel sun-crank slicer with brass knobs",
        power=2,
        thin_bonus=4,
        motion="turned in a smooth shining circle that hardly seemed to touch the food at all",
        discover="a little brass lever tucked behind the steel guard",
        tags={"steel", "slicer"},
    ),
}

CROWDS = {
    "porch_club": Crowd(
        id="porch_club",
        label="porch club",
        phrase="the whole porch club",
        need=7,
        line_image="Children lined up along the railing like bright buttons on a coat.",
        smallest="Pip",
        tags={"sharing"},
    ),
    "cousin_line": Crowd(
        id="cousin_line",
        label="cousin line",
        phrase="a line of cousins from tall to tiny",
        need=8,
        line_image="The cousins stretched across the yard so far that the last one had to wave from around a barrel.",
        smallest="June",
        tags={"sharing"},
    ),
    "school_table": Crowd(
        id="school_table",
        label="school table",
        phrase="the whole school picnic table",
        need=9,
        line_image="The children sat shoulder to shoulder, knees swinging, waiting for a taste.",
        smallest="Bess",
        tags={"sharing"},
    ),
    "berry_team": Crowd(
        id="berry_team",
        label="berry team",
        phrase="the berry-picking team",
        need=6,
        line_image="The berry team crowded close with purple fingertips and hopeful eyes.",
        smallest="Nell",
        tags={"sharing"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Tess", "Wren", "Nora", "Ada", "Maisie", "June"]
BOY_NAMES = ["Bo", "Eli", "Finn", "Jeb", "Theo", "Cal", "Owen", "Ned"]
TRAITS = ["curious", "quick", "kind", "bright-eyed", "careful", "hopeful"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
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


def _r_discover(world: World) -> list[str]:
    hero = world.get("hero")
    cutter = world.get("cutter")
    if hero.memes["curiosity"] < THRESHOLD:
        return []
    if cutter.meters["inspected"] < THRESHOLD:
        return []
    sig = ("discover", hero.id, cutter.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cutter.meters["thin_mode"] = 1.0
    hero.memes["wonder"] += 1
    world.facts["discovered"] = True
    return ["__discover__"]


def _r_slice(world: World) -> list[str]:
    cutter = world.get("cutter")
    food = world.get("food")
    if cutter.meters["engaged"] < THRESHOLD:
        return []
    sig = ("slice", cutter.id, food.id, int(cutter.meters["thin_mode"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bonus = world.facts["thin_bonus"] if cutter.meters["thin_mode"] >= THRESHOLD else 0
    total = world.facts["base_slices"] + bonus
    food.meters["sliced"] = float(total)
    food.meters["cut"] = 1.0
    world.facts["slice_count"] = total
    return ["__slice__"]


def _r_enough(world: World) -> list[str]:
    food = world.get("food")
    crowd = world.get("crowd")
    if food.meters["sliced"] < THRESHOLD:
        return []
    sig = ("enough", food.id, crowd.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if int(food.meters["sliced"]) >= world.facts["need"]:
        crowd.meters["served"] = float(world.facts["need"])
        world.facts["enough"] = True
        return ["__enough__"]
    world.facts["enough"] = False
    return ["__short__"]


RULES = [
    Rule(name="discover", tag="social", apply=_r_discover),
    Rule(name="slice", tag="physical", apply=_r_slice),
    Rule(name="enough", tag="physical", apply=_r_enough),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def cutter_can_cut(food: Food, cutter: Cutter) -> bool:
    return cutter.power >= food.hardness


def enough_for_crowd(food: Food, cutter: Cutter, crowd: Crowd) -> bool:
    return food.base_slices + cutter.thin_bonus >= crowd.need


def valid_story(food: Food, cutter: Cutter, crowd: Crowd) -> bool:
    return cutter_can_cut(food, cutter) and enough_for_crowd(food, cutter, crowd)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for food_id, food in FOODS.items():
            for cutter_id, cutter in CUTTERS.items():
                for crowd_id, crowd in CROWDS.items():
                    if valid_story(food, cutter, crowd):
                        combos.append((setting_id, food_id, cutter_id, crowd_id))
    return combos


def explain_rejection(food: Food, cutter: Cutter, crowd: Crowd) -> str:
    if not cutter_can_cut(food, cutter):
        return (
            f"(No story: {cutter.phrase} is not strong enough for {food.phrase}. "
            f"The cutter would only skid and fuss instead of making neat slices.)"
        )
    total = food.base_slices + cutter.thin_bonus
    return (
        f"(No story: even with the thin-slice trick, {food.label} would make only "
        f"{total} slices for {crowd.phrase}, who need {crowd.need}. The world "
        f"won't pretend sharing worked when there still would not be enough.)"
    )


def outcome_of(params: "StoryParams") -> str:
    food = FOODS[params.food]
    cutter = CUTTERS[params.cutter]
    crowd = CROWDS[params.crowd]
    if not cutter_can_cut(food, cutter):
        return "stuck"
    if not enough_for_crowd(food, cutter, crowd):
        return "short"
    return "shared"


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, food: Food, crowd: Crowd) -> None:
    world.say(
        f"In the days when stories liked to stretch their legs, {hero.id} came to "
        f"{world.setting.place} with {hero.pronoun('possessive')} {helper.label_word}."
    )
    world.say(world.setting.boast)
    world.say(
        f"On the long table sat {food.phrase}. {food.giant_line} {food.aroma}"
    )
    world.say(crowd.line_image)


def worry(world: World, hero: Entity, helper: Entity, crowd: Crowd) -> None:
    hero.memes["desire"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} looked from the big treat to {crowd.phrase} and whispered, '
        f'"That is a mighty lot of mouths for one dessert."'
    )
    world.say(
        f'{helper.label_word.capitalize()} nodded. "Aye," {helper.pronoun()} said, '
        f'"unless somebody has a good idea, the last child in line may only get a smell."'
    )


def inspect_cutter(world: World, hero: Entity, cutter: Entity, cutter_cfg: Cutter) -> None:
    hero.memes["curiosity"] += 1
    cutter.meters["inspected"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Beside the table leaned {cutter_cfg.phrase}. The frame was steel, cool and bright, "
        f"and on its side someone had stamped the odd word 'cut-gerund.'"
    )
    world.say(
        f"{hero.id} was too curious to let a word like that sit still. "
        f"{hero.pronoun().capitalize()} ran one finger along the letters and peered under the handle."
    )
    if world.facts.get("discovered"):
        world.say(
            f"There {hero.pronoun()} found {cutter_cfg.discover}. "
            f'"Maybe this is what the funny word is trying to tell us," {hero.pronoun()} said.'
        )


def predict_slices(world: World) -> dict:
    sim = world.copy()
    sim.get("cutter").meters["engaged"] = 1.0
    propagate(sim, narrate=False)
    return {
        "slice_count": sim.facts.get("slice_count", 0),
        "enough": bool(sim.facts.get("enough", False)),
    }


def boast_and_try(world: World, hero: Entity, helper: Entity, cutter_cfg: Cutter, crowd: Crowd) -> None:
    pred = predict_slices(world)
    world.facts["predicted_slice_count"] = pred["slice_count"]
    world.say(
        f'{helper.label_word.capitalize()} lifted the cutter, and {hero.id} showed '
        f'{helper.pronoun("object")} the hidden setting.'
    )
    world.say(
        f'"Let us see what this old steel wonder can do," {helper.pronoun()} said.'
    )
    world.say(
        f"When the blade moved, it {cutter_cfg.motion}. Everyone in {crowd.phrase} leaned in so far "
        f"the line looked like a row of sunflowers in one wind."
    )
    world.get("cutter").meters["engaged"] = 1.0
    propagate(world, narrate=False)


def share(world: World, hero: Entity, helper: Entity, crowd: Crowd) -> None:
    food_ent = world.get("food")
    hero.memes["sharing"] += 1
    hero.memes["joy"] += 1
    crowd.memes["gratitude"] += 1
    smallest = crowd.attrs["smallest"]
    world.say(
        f"When the slices lay out at last, there were {int(food_ent.meters['sliced'])} of them, "
        f"thin and tidy as little moons."
    )
    world.say(
        f'{hero.id} got the first piece in {hero.pronoun("possessive")} hand, then spotted {smallest} '
        f"at the end of the line standing on tiptoe."
    )
    world.say(
        f'{hero.pronoun().capitalize()} carried that first piece clear to the back and gave it away. '
        f'"We eat better when we all eat," {hero.pronoun()} said.'
    )
    world.say(
        f"After that, the slices went round and round until every plate in {crowd.phrase} held a share."
    )
    helper.memes["pride"] += 1


def ending(world: World, hero: Entity, helper: Entity, food: Food) -> None:
    world.say(
        f'{helper.label_word.capitalize()} laughed so warmly that even the pie tin seemed to shine. '
        f'"Your curiosity found the trick," {helper.pronoun()} said, "and your sharing made it worth finding."'
    )
    world.say(
        f"{hero.id} took the last neat slice for {hero.pronoun('object')}self and found it tasted better "
        f"because nobody had been left out."
    )
    world.say(world.setting.ending)
    world.say(
        f"And that is how one child, one steel cutter, and one strange little word helped turn {food.label} "
        f"into a feast big enough for a tall tale."
    )


def tell(
    setting: Setting,
    food_cfg: Food,
    cutter_cfg: Cutter,
    crowd_cfg: Crowd,
    *,
    name: str = "Mira",
    gender: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    world.facts.update(
        base_slices=food_cfg.base_slices,
        thin_bonus=cutter_cfg.thin_bonus,
        need=crowd_cfg.need,
        enough=False,
        discovered=False,
        slice_count=0,
        predicted_slice_count=0,
    )

    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            label=name,
            traits=[trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            traits=["steady"],
            attrs={},
        )
    )
    food_ent = world.add(
        Entity(
            id="food",
            kind="thing",
            type="food",
            label=food_cfg.label,
            phrase=food_cfg.phrase,
            attrs={},
        )
    )
    cutter_ent = world.add(
        Entity(
            id="cutter",
            kind="thing",
            type="cutter",
            label=cutter_cfg.label,
            phrase=cutter_cfg.phrase,
            material="steel",
            attrs={},
        )
    )
    crowd_ent = world.add(
        Entity(
            id="crowd",
            kind="thing",
            type="crowd",
            label=crowd_cfg.label,
            phrase=crowd_cfg.phrase,
            attrs={"smallest": crowd_cfg.smallest},
        )
    )

    introduce(world, hero, helper, food_cfg, crowd_cfg)
    world.para()
    worry(world, hero, helper, crowd_cfg)
    inspect_cutter(world, hero, cutter_ent, cutter_cfg)
    world.para()
    boast_and_try(world, hero, helper, cutter_cfg, crowd_cfg)
    share(world, hero, helper, crowd_cfg)
    world.para()
    ending(world, hero, helper, food_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        food_cfg=food_cfg,
        cutter_cfg=cutter_cfg,
        crowd_cfg=crowd_cfg,
        food=food_ent,
        cutter=cutter_ent,
        crowd=crowd_ent,
        outcome="shared",
        shared=hero.memes["sharing"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    food: str
    cutter: str
    crowd: str
    name: str
    gender: str
    helper: str
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


CURATED = [
    StoryParams(
        setting="mesa_picnic",
        food="apple_pie",
        cutter="wagon_wheel",
        crowd="porch_club",
        name="Mira",
        gender="girl",
        helper="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="river_fair",
        food="cheese_wheel",
        cutter="river_saw",
        crowd="cousin_line",
        name="Bo",
        gender="boy",
        helper="grandfather",
        trait="quick",
    ),
    StoryParams(
        setting="barn_social",
        food="molasses_cake",
        cutter="sun_crank",
        crowd="school_table",
        name="Tess",
        gender="girl",
        helper="grandmother",
        trait="bright-eyed",
    ),
    StoryParams(
        setting="river_fair",
        food="peach_cobbler",
        cutter="wagon_wheel",
        crowd="berry_team",
        name="Finn",
        gender="boy",
        helper="grandfather",
        trait="kind",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "steel": [
        (
            "What is steel?",
            "Steel is a very strong metal. People use it to make tools because it can stay sturdy and sharp.",
        )
    ],
    "curiosity": [
        (
            "What does it mean to be curious?",
            "Being curious means wanting to learn how something works or why something happens. Curiosity can help you notice a good idea.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing helps more people feel included and cared for. When everyone gets a turn or a piece, a happy moment can grow instead of shrinking.",
        )
    ],
    "pie": [
        (
            "What is a pie slice?",
            "A pie slice is one wedge-shaped piece cut from a whole pie. Cutting thinner slices can help a pie feed more people.",
        )
    ],
    "cheese": [
        (
            "What is a cheese wheel?",
            "A cheese wheel is a big round shape of cheese. People cut it into smaller pieces so everyone can eat some.",
        )
    ],
    "cake": [
        (
            "Why do people cut cake into pieces?",
            "People cut cake into pieces so many people can share it. Smaller pieces can still feel special when everyone gets one.",
        )
    ],
    "slicer": [
        (
            "What does a slicer do?",
            "A slicer is a tool that cuts food into pieces. If it is set carefully, it can make thinner or thicker slices.",
        )
    ],
}
KNOWLEDGE_ORDER = ["steel", "curiosity", "sharing", "pie", "cheese", "cake", "slicer"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    food = world.facts["food_cfg"]
    crowd = world.facts["crowd_cfg"]
    return [
        'Write a tall-tale story for a 3-to-5-year-old that includes the words "steel" and "cut-gerund" and shows Curiosity and Sharing.',
        f"Tell a warm tall tale where a curious {hero.type} named {hero.id} helps cut {food.label} for {crowd.phrase} and makes sure everyone gets some.",
        f"Write a child-facing story in which a strange word on a steel cutter leads to a clever discovery, and the discovery ends in sharing instead of grabbing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    food = world.facts["food_cfg"]
    cutter = world.facts["cutter_cfg"]
    crowd = world.facts["crowd_cfg"]
    smallest = crowd.smallest
    slice_count = world.facts["slice_count"]
    pred = world.facts["predicted_slice_count"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a curious child, and {hero.pronoun('possessive')} {helper.label_word} at {world.setting.place}. They were trying to feed {crowd.phrase} from one giant {food.label}.",
        ),
        (
            "Why was everyone worried at first?",
            f"They worried because there was only one huge treat for a big crowd. At the start, it was not clear whether the slices would stretch far enough for everyone.",
        ),
        (
            f"What did {hero.id} notice on the cutter?",
            f"{hero.id} noticed that the cutter was made of steel and had the funny word 'cut-gerund' stamped on it. That made {hero.pronoun('object')} curious enough to look underneath the handle for a trick.",
        ),
        (
            f"How did curiosity help solve the problem?",
            f"{hero.id}'s curiosity led to a hidden thin-slice setting on the cutter. Because of that discovery, the cutter made {slice_count} slices instead of the thicker ordinary cut everyone feared at first.",
        ),
        (
            "How did sharing change the ending?",
            f"{hero.id} gave the first piece to {smallest}, who was all the way at the back of the line. That choice showed the others to pass the slices around until everybody had a share.",
        ),
        (
            "Why did the food taste better at the end?",
            f"It tasted better because nobody had been left out. The happy ending came from both the clever discovery and the decision to share it fairly.",
        ),
    ]
    if pred:
        qa.append(
            (
                "How many slices did the cutter make after the hidden setting was found?",
                f"It made {slice_count} slices. That was enough for the crowd because {crowd.phrase} needed {crowd.need}, and the thin setting stretched the food far enough.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"steel", "curiosity", "sharing", "slicer"}
    food = world.facts["food_cfg"]
    if "pie" in food.tags:
        tags.add("pie")
    if "cheese" in food.tags:
        tags.add("cheese")
    if "cake" in food.tags:
        tags.add("cake")
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
# Trace / emit
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(
        f"  facts: slice_count={world.facts.get('slice_count')} "
        f"need={world.facts.get('need')} discovered={world.facts.get('discovered')}"
    )
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_cut(F,C) :- food(F), cutter(C), hardness(F,H), power(C,P), P >= H.
feeds(F,C,Cr) :- food(F), cutter(C), crowd(Cr),
                 base_slices(F,B), thin_bonus(C,T), need(Cr,N),
                 B + T >= N.
valid(S,F,C,Cr) :- setting(S), can_cut(F,C), feeds(F,C,Cr).

chosen_can_cut :- chosen_food(F), chosen_cutter(C), can_cut(F,C).
chosen_feeds   :- chosen_food(F), chosen_cutter(C), chosen_crowd(Cr), feeds(F,C,Cr).

outcome(shared) :- chosen_can_cut, chosen_feeds.
outcome(stuck)  :- not chosen_can_cut.
outcome(short)  :- chosen_can_cut, not chosen_feeds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("hardness", fid, food.hardness))
        lines.append(asp.fact("base_slices", fid, food.base_slices))
    for cid, cutter in CUTTERS.items():
        lines.append(asp.fact("cutter", cid))
        lines.append(asp.fact("power", cid, cutter.power))
        lines.append(asp.fact("thin_bonus", cid, cutter.thin_bonus))
    for gid, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", gid))
        lines.append(asp.fact("need", gid, crowd.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_food", params.food),
            asp.fact("chosen_cutter", params.cutter),
            asp.fact("chosen_crowd", params.crowd),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    default_args = parser.parse_args([])
    for _ in range(40):
        try:
            cases.append(resolve_params(default_args, rng))
        except StoryError:
            rc = 1
            print("resolve_params unexpectedly failed during verify.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a curious child finds a slicing trick and shares a giant treat."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--cutter", choices=CUTTERS)
    ap.add_argument("--crowd", choices=CROWDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.cutter and args.crowd:
        food = FOODS[args.food]
        cutter = CUTTERS[args.cutter]
        crowd = CROWDS[args.crowd]
        if not valid_story(food, cutter, crowd):
            raise StoryError(explain_rejection(food, cutter, crowd))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.food is None or combo[1] == args.food)
        and (args.cutter is None or combo[2] == args.cutter)
        and (args.crowd is None or combo[3] == args.crowd)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, food_id, cutter_id, crowd_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        food=food_id,
        cutter=cutter_id,
        crowd=crowd_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.cutter not in CUTTERS:
        raise StoryError(f"(Unknown cutter: {params.cutter})")
    if params.crowd not in CROWDS:
        raise StoryError(f"(Unknown crowd: {params.crowd})")

    food = FOODS[params.food]
    cutter = CUTTERS[params.cutter]
    crowd = CROWDS[params.crowd]
    if not valid_story(food, cutter, crowd):
        raise StoryError(explain_rejection(food, cutter, crowd))

    world = tell(
        SETTINGS[params.setting],
        food,
        cutter,
        crowd,
        name=params.name,
        gender=params.gender,
        helper_type=params.helper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, food, cutter, crowd) combos:\n")
        for setting_id, food_id, cutter_id, crowd_id in combos:
            print(f"  {setting_id:12} {food_id:14} {cutter_id:12} {crowd_id}")
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
            header = (
                f"### {p.name}: {p.food} with {p.cutter} for {p.crowd} "
                f"at {p.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
