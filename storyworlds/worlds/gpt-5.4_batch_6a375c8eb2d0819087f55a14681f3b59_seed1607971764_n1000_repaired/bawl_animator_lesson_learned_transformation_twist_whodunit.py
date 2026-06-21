#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py
=========================================================================================

A standalone story world about a young animator, a changed stop-motion figure,
and a child-sized whodunit with a twist.

Seed requirements rebuilt as world state:
- include the words "bawl" and "animator"
- feature a lesson learned
- feature a transformation
- keep the style close to a whodunit

Core premise
------------
A child animator makes a tiny stop-motion figure for a small show. Later the
figure looks strangely changed. The child nearly starts to bawl and wonders who
did it. A few suspicious clues point toward a person or pet, but the investigation
reveals a twist: the true culprit is heat from the room, not a naughty someone.
Then the child either reshapes the figure in time or cleverly rewrites the film
to fit the transformed figure. The lesson is not to blame before checking the
facts, and to adapt calmly when something changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py
    python storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py --material clay --heat heater
    python storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py --material clay --heat sunbeam
    python storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/bawl_animator_lesson_learned_transformation_twist_whodunit.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman", "aunt", "teacher"}
        male = {"boy", "father", "man", "uncle"}
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
            "teacher": "teacher",
            "aunt": "aunt",
        }.get(self.type, self.label or self.type)
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
class Theme:
    id: str
    title: str
    figure_name: str
    start_pose: str
    changed_pose: str
    set_piece: str
    film_line: str
    new_line: str
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
class Material:
    id: str
    label: str
    phrase: str
    soften_at: int
    damage_word: str
    texture: str
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
class HeatSource:
    id: str
    label: str
    place: str
    clue: str
    power: int
    warmth_text: str
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
class RedHerring:
    id: str
    label: str
    footprint: str
    suspicion_text: str
    exoneration_text: str
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
class Repair:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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


def _r_heat_softens(world: World) -> list[str]:
    out: list[str] = []
    figure = world.get("figure")
    room = world.get("room")
    if room.meters["heat"] < THRESHOLD:
        return out
    if room.meters["heat"] < figure.attrs.get("soften_at", 99):
        return out
    sig = ("soften", figure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    figure.meters["softened"] += 1
    figure.meters["changed"] += 1
    hero = world.get("hero")
    hero.memes["alarm"] += 1
    hero.memes["sadness"] += 1
    out.append("__changed__")
    return out


def _r_changed_suspicion(world: World) -> list[str]:
    out: list[str] = []
    figure = world.get("figure")
    if figure.meters["changed"] < THRESHOLD:
        return out
    hero = world.get("hero")
    sig = ("suspect", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    out.append("__suspect__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_softens", tag="physical", apply=_r_heat_softens),
    Rule(name="changed_suspicion", tag="social", apply=_r_changed_suspicion),
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


def is_heat_risk(material: Material, heat: HeatSource) -> bool:
    return heat.power >= material.soften_at


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def damage_severity(material: Material, heat: HeatSource) -> int:
    return heat.power - material.soften_at + 1


def repair_holds(repair: Repair, material: Material, heat: HeatSource) -> bool:
    return repair.power >= damage_severity(material, heat)


def explain_rejection(material: Material, heat: HeatSource) -> str:
    return (
        f"(No story: {heat.label} in {heat.place} is not warm enough to change "
        f"{material.phrase}. Without a real transformation, there is no honest mystery to solve.)"
    )


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try {better}.)"
    )


def predict_change(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    figure = sim.get("figure")
    return {
        "changed": figure.meters["changed"] >= THRESHOLD,
        "severity": damage_severity(
            MATERIALS[sim.facts["material"].id],
            HEAT_SOURCES[sim.facts["heat"].id],
        ),
    }


def introduce(world: World, hero: Entity, helper: Entity, theme: Theme, material: Material) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} was a little animator who loved making stories one tiny move at a time."
    )
    world.say(
        f"On the long craft table, {hero.pronoun()} shaped {material.phrase} into "
        f"{theme.figure_name}, a character for {hero.pronoun('possessive')} new mystery film. "
        f"{theme.film_line}"
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} {helper.attrs.get('relation', 'helper')}, "
        f"helped build {theme.set_piece} and clapped at the careful {theme.start_pose} pose."
    )


def place_figure(world: World, hero: Entity, heat: HeatSource) -> None:
    world.say(
        f"Before snack time, {hero.id} set the little figure on a tray in {heat.place}, "
        f"so it could wait for the after-school showing."
    )


def discover_change(world: World, hero: Entity, theme: Theme, material: Material) -> None:
    figure = world.get("figure")
    if figure.meters["changed"] >= THRESHOLD:
        world.say(
            f"When {hero.id} came back, {theme.figure_name} was no longer standing in the neat "
            f"{theme.start_pose} pose. The {material.label} figure had {material.damage_word} into "
            f"{theme.changed_pose} instead."
        )
        world.say(
            f"{hero.id}'s face went hot. For one worried second, {hero.pronoun()} thought "
            f"{hero.pronoun()} might bawl."
        )


def suspect_someone(world: World, hero: Entity, herring: RedHerring) -> None:
    hero.memes["blame"] += 1
    world.say(
        f"Then {hero.pronoun()} saw {herring.footprint} and whispered, "
        f"\"Aha! Maybe {herring.label} did it.\" {herring.suspicion_text}"
    )


def investigate(world: World, helper: Entity, herring: RedHerring, heat: HeatSource) -> None:
    pred = predict_change(world)
    world.facts["predicted_changed"] = pred["changed"]
    world.facts["predicted_severity"] = pred["severity"]
    world.say(
        f'But {helper.id} did not point a finger. "{herring.exoneration_text} '
        f'Let\'s look for real clues," {helper.pronoun()} said.'
    )
    world.say(
        f"Together they touched the tray, saw the shiny soft edge on the figure, and noticed "
        f"{heat.clue}. The air there felt {heat.warmth_text}."
    )


def reveal_twist(world: World, hero: Entity, helper: Entity, heat: HeatSource) -> None:
    hero.memes["blame"] = 0.0
    hero.memes["understanding"] += 1
    world.say(
        f'That was the twist. Nobody had sneaked in to ruin the model at all. '
        f'The real culprit was {heat.label}.'
    )
    world.say(
        f'{helper.id} smiled gently. "{heat.label.capitalize()} changed it because it was too warm," '
        f'{helper.pronoun()} explained. "Warmth can make soft art bend before anyone even touches it."'
    )


def lesson(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{hero.id} took a slow breath and looked back at the clue trail. "
        f"{hero.pronoun().capitalize()} had almost blamed someone before knowing the truth."
    )
    world.say(
        f'"Next time, I will check the facts first," {hero.pronoun()} said. '
        f'{helper.id} nodded. "That is what good detectives do, and good friends too."'
    )


def repair_success(world: World, hero: Entity, helper: Entity, repair: Repair, theme: Theme) -> None:
    figure = world.get("figure")
    figure.meters["changed"] = 0.0
    figure.meters["softened"] = 0.0
    figure.meters["repaired"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Then they {repair.text}, set the model in a cooler place, and waited a moment."
    )
    world.say(
        f"Soon {theme.figure_name} was ready again, standing in the brave {theme.start_pose} pose. "
        f"At the showing, everyone cheered for the tiny detective film."
    )


def rewrite_success(world: World, hero: Entity, helper: Entity, theme: Theme) -> None:
    figure = world.get("figure")
    figure.meters["rewritten"] += 1
    hero.memes["creativity"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"The figure was too changed to look exactly the same again, so {hero.id} chose a new plan."
    )
    world.say(
        f"{hero.pronoun().capitalize()} rewrote the ending and turned the bent little model into a new "
        f"character on purpose. In the finished film, {theme.new_line}"
    )
    world.say(
        f"The crowd loved the surprise, and {helper.id} whispered that the mystery had become the best "
        f"twist in the whole show."
    )


def tell(
    theme: Theme,
    material: Material,
    heat: HeatSource,
    repair: Repair,
    herring: RedHerring,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_name: str = "Uncle Ben",
    helper_type: str = "man",
    relation: str = "uncle",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["careful", "imaginative"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={"relation": relation},
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label="the room",
        )
    )
    figure = world.add(
        Entity(
            id="figure",
            type="figure",
            label=theme.figure_name,
            attrs={"soften_at": material.soften_at, "material": material.id},
        )
    )

    room.meters["heat"] = float(heat.power)
    figure.meters["changed"] = 0.0
    figure.meters["softened"] = 0.0
    hero.memes["alarm"] = 0.0
    hero.memes["sadness"] = 0.0
    hero.memes["suspicion"] = 0.0
    hero.memes["blame"] = 0.0
    hero.memes["understanding"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["creativity"] = 0.0
    helper.memes["care"] = 0.0

    world.facts.update(
        theme=theme,
        material=material,
        heat=heat,
        repair=repair,
        herring=herring,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, theme, material)
    place_figure(world, hero, heat)

    world.para()
    propagate(world, narrate=False)
    discover_change(world, hero, theme, material)
    suspect_someone(world, hero, herring)

    world.para()
    investigate(world, helper, herring, heat)
    reveal_twist(world, hero, helper, heat)
    lesson(world, hero, helper)

    world.para()
    if repair_holds(repair, material, heat):
        repair_success(world, hero, helper, repair, theme)
        outcome = "repaired"
    else:
        rewrite_success(world, hero, helper, theme)
        outcome = "rewritten"

    world.facts.update(
        outcome=outcome,
        changed=is_heat_risk(material, heat),
        severity=damage_severity(material, heat),
    )
    return world


THEMES = {
    "detective_mouse": Theme(
        id="detective_mouse",
        title="The Missing Crumb Case",
        figure_name="Detective Minto the mouse",
        start_pose="tiptoe pose with one paw lifted",
        changed_pose="a droopy bowing pose",
        set_piece="a cardboard alley with tiny paper lamps",
        film_line='"Tonight I solve The Missing Crumb Case!"',
        new_line="Detective Minto bowed on purpose and uncovered the clue hiding under his own hat.",
        tags={"mystery", "detective"},
    ),
    "rocket_fox": Theme(
        id="rocket_fox",
        title="The Moon Map Mystery",
        figure_name="Rocket Fox",
        start_pose="salute pose on the launch ramp",
        changed_pose="a sleepy sideways lean",
        set_piece="a silver rocket made from a juice box and foil",
        film_line='"No moon map can hide from me!"',
        new_line="Rocket Fox pretended the strange lean was a secret moon-wind move and still found the map.",
        tags={"mystery", "space"},
    ),
    "bakery_cat": Theme(
        id="bakery_cat",
        title="The Vanishing Cherry",
        figure_name="Baker Pip the cat",
        start_pose="proud pose beside a pretend tart",
        changed_pose="a soft swooping curtsy",
        set_piece="a bakery window cut from pink paper",
        film_line='"I will find who took the last cherry before breakfast!"',
        new_line="Baker Pip turned the swoop into a grand bakery bow and revealed the cherry under the tray.",
        tags={"mystery", "bakery"},
    ),
}

MATERIALS = {
    "chocolate": Material(
        id="chocolate",
        label="chocolate",
        phrase="a little chocolate model",
        soften_at=1,
        damage_word="melted and slumped",
        texture="glossy",
        tags={"chocolate", "heat"},
    ),
    "wax": Material(
        id="wax",
        label="wax",
        phrase="a wax figure",
        soften_at=2,
        damage_word="softened and bent",
        texture="smooth",
        tags={"wax", "heat"},
    ),
    "clay": Material(
        id="clay",
        label="clay",
        phrase="an air-dry clay figure",
        soften_at=3,
        damage_word="sagged and drooped",
        texture="matte",
        tags={"clay", "heat"},
    ),
}

HEAT_SOURCES = {
    "sunbeam": HeatSource(
        id="sunbeam",
        label="a bright sunbeam",
        place="the sunny windowsill",
        clue="a rectangle of gold light across the tray",
        power=1,
        warmth_text="warm like toast",
        tags={"sun", "heat"},
    ),
    "lamp": HeatSource(
        id="lamp",
        label="the desk lamp",
        place="the corner table under the lamp",
        clue="the lamp shining low and close above the tray",
        power=2,
        warmth_text="much warmer than the rest of the room",
        tags={"lamp", "heat"},
    ),
    "heater": HeatSource(
        id="heater",
        label="the humming heater",
        place="the shelf above the heater",
        clue="a little ribbon of hot air wobbling above the vent",
        power=3,
        warmth_text="almost hot on their knuckles",
        tags={"heater", "heat"},
    ),
}

RED_HERRINGS = {
    "puppy": RedHerring(
        id="puppy",
        label="the puppy",
        footprint="a tiny paw print nearby in spilled glitter",
        suspicion_text="It was just the sort of clue that makes a mystery feel solved too fast.",
        exoneration_text="The paw print is old, and the puppy cannot reach this high.",
        tags={"pet", "clue"},
    ),
    "little_brother": RedHerring(
        id="little_brother",
        label="your little brother",
        footprint="one blue crayon lying under the table",
        suspicion_text="The fallen crayon looked suspicious, but it did not prove a thing.",
        exoneration_text="That crayon only tells us he was drawing earlier.",
        tags={"family", "clue"},
    ),
    "friend": RedHerring(
        id="friend",
        label="your friend Tessa",
        footprint="a paper star sticker stuck to the tray",
        suspicion_text="It looked dramatic enough to belong in a detective movie.",
        exoneration_text="That sticker came from the set decorations, not from trouble.",
        tags={"friend", "clue"},
    ),
}

REPAIRS = {
    "cool_reshape": Repair(
        id="cool_reshape",
        sense=3,
        power=2,
        text="cooled it carefully and reshaped the bent parts with slow, steady fingers",
        qa_text="cooled the figure and reshaped it carefully",
        tags={"repair", "cool"},
    ),
    "frame_rebuild": Repair(
        id="frame_rebuild",
        sense=3,
        power=4,
        text="used the changed model as a guide and rebuilt the pose frame by frame",
        qa_text="rebuilt the pose frame by frame",
        tags={"repair", "rebuild"},
    ),
    "press_harder": Repair(
        id="press_harder",
        sense=1,
        power=1,
        text="pressed on the soft parts harder and harder",
        qa_text="just pressed on the soft parts harder",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Noah", "Eli", "Theo", "Sam"]
HELPERS = [
    {"name": "Aunt June", "type": "aunt", "relation": "aunt"},
    {"name": "Dad", "type": "father", "relation": "dad"},
    {"name": "Ms. Reed", "type": "teacher", "relation": "teacher"},
    {"name": "Uncle Ben", "type": "man", "relation": "uncle"},
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for material_id, material in MATERIALS.items():
            for heat_id, heat in HEAT_SOURCES.items():
                if is_heat_risk(material, heat):
                    combos.append((theme_id, material_id, heat_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    material: str
    heat: str
    repair: str
    herring: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    relation: str
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


KNOWLEDGE = {
    "animator": [
        (
            "What does an animator do?",
            "An animator makes pictures or models seem to move by changing them a tiny bit at a time and showing the steps in order."
        )
    ],
    "heat": [
        (
            "Why can heat change soft art materials?",
            "Heat can make some materials softer and bendier. When that happens, a model may droop even if nobody touched it."
        )
    ],
    "sun": [
        (
            "Can sunshine warm things by a window?",
            "Yes. A bright patch of sunshine can make a windowsill warmer than the rest of the room."
        )
    ],
    "lamp": [
        (
            "Can a lamp make things warm?",
            "Yes, some lamps give off heat as well as light. If something soft sits too close, it can change shape."
        )
    ],
    "heater": [
        (
            "What does a heater do?",
            "A heater warms the air in a room. Things left too close to it can get warmer than you expect."
        )
    ],
    "clay": [
        (
            "What is clay?",
            "Clay is a soft material people shape into models and let dry. Before it is fully hard, warmth and pressure can change it."
        )
    ],
    "wax": [
        (
            "What is wax like?",
            "Wax can be smooth and useful for modeling, but warmth can make it soften and bend."
        )
    ],
    "chocolate": [
        (
            "Why does chocolate melt?",
            "Chocolate gets soft when it becomes warm. That is why people keep it away from heat."
        )
    ],
    "repair": [
        (
            "What is a good way to solve a mystery fairly?",
            "A good detective checks clues before blaming anyone. Looking carefully helps you find the true cause instead of guessing."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "animator",
    "heat",
    "sun",
    "lamp",
    "heater",
    "clay",
    "wax",
    "chocolate",
    "repair",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme, material, heat = f["theme"], f["material"], f["heat"]
    hero = f["hero"]
    if f["outcome"] == "repaired":
        end = "and calmly repairs the figure in time for the show"
    else:
        end = "and rewrites the story so the transformed figure becomes part of the twist"
    return [
        f'Write a child-facing whodunit about a young animator whose {material.label} figure changes shape near {heat.label}, and include the word "bawl".',
        f"Tell a mystery story where {hero.id} almost blames the wrong suspect, then learns the true culprit was heat and {end}.",
        f'Write a simple detective-style story with a lesson about checking clues before accusing anyone, plus a transformation and a surprise ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    theme = f["theme"]
    material = f["material"]
    heat = f["heat"]
    herring = f["herring"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little animator, and {helper.id}, who helped investigate what happened to {theme.figure_name}."
        ),
        (
            f"What happened to {theme.figure_name}?",
            f"The figure changed shape and no longer stood in its neat {theme.start_pose} pose. The {material.label} had been warmed until it {material.damage_word}."
        ),
        (
            f"Why did {hero.id} almost bawl?",
            f"{hero.id} thought someone had ruined the model just before the showing. The changed figure felt like a disaster because {hero.pronoun()} had worked so carefully on it."
        ),
        (
            "Who did they suspect at first?",
            f"They first suspected {herring.label} because of {herring.footprint}. That clue looked dramatic, but it turned out not to explain the change."
        ),
        (
            "What was the twist in the mystery?",
            f"The twist was that no person or pet had done it. {heat.label.capitalize()} warmed the figure where it had been left in {heat.place}, and the heat changed its shape."
        ),
        (
            "What lesson did the hero learn?",
            f"{hero.id} learned to check the facts before blaming anyone. Looking at the warm tray and the real clues showed the true cause of the problem."
        ),
    ]
    if f["outcome"] == "repaired":
        qa.append(
            (
                "How did they save the show?",
                f"They {repair.qa_text} and moved it to a cooler place. That careful fix let the mystery film go on as planned."
            )
        )
    else:
        qa.append(
            (
                "How did the ending show a transformation?",
                f"The damaged figure stayed changed, but {hero.id} transformed the problem into a new ending for the film. Instead of giving up, {hero.pronoun()} turned the bent pose into the story's big surprise."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"animator", "heat", f["material"].id}
    tags |= set(f["heat"].tags)
    tags.add("repair")
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="detective_mouse",
        material="chocolate",
        heat="sunbeam",
        repair="cool_reshape",
        herring="puppy",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Aunt June",
        helper_type="aunt",
        relation="aunt",
    ),
    StoryParams(
        theme="rocket_fox",
        material="wax",
        heat="lamp",
        repair="cool_reshape",
        herring="friend",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Ms. Reed",
        helper_type="teacher",
        relation="teacher",
    ),
    StoryParams(
        theme="bakery_cat",
        material="clay",
        heat="heater",
        repair="frame_rebuild",
        herring="little_brother",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Dad",
        helper_type="father",
        relation="dad",
    ),
    StoryParams(
        theme="detective_mouse",
        material="wax",
        heat="heater",
        repair="cool_reshape",
        herring="puppy",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Uncle Ben",
        helper_type="man",
        relation="uncle",
    ),
    StoryParams(
        theme="rocket_fox",
        material="chocolate",
        heat="heater",
        repair="cool_reshape",
        herring="friend",
        hero_name="Ava",
        hero_gender="girl",
        helper_name="Dad",
        helper_type="father",
        relation="dad",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risk(M,H) :- material(M), heat(H), soften_at(M,S), power(H,P), P >= S.
valid(T,M,H) :- theme(T), risk(M,H).

sensible(R) :- repair(R), sense(R,S), sense_min(M), S >= M.

% --- ending model ----------------------------------------------------------
severity(V) :- chosen_material(M), chosen_heat(H),
               soften_at(M,S), power(H,P), V = P - S + 1.
holds :- chosen_repair(R), power_repair(R,RP), severity(V), RP >= V.

outcome(repaired)  :- holds.
outcome(rewritten) :- not holds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("soften_at", material_id, material.soften_at))
    for heat_id, heat in HEAT_SOURCES.items():
        lines.append(asp.fact("heat", heat_id))
        lines.append(asp.fact("power", heat_id, heat.power))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power_repair", repair_id, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_heat", params.heat),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return (
        "repaired"
        if repair_holds(REPAIRS[params.repair], MATERIALS[params.material], HEAT_SOURCES[params.heat])
        else "rewritten"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a young animator solves a tiny whodunit about a transformed model."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--heat", choices=HEAT_SOURCES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--herring", choices=RED_HERRINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.heat:
        material = MATERIALS[args.material]
        heat = HEAT_SOURCES[args.heat]
        if not is_heat_risk(material, heat):
            raise StoryError(explain_rejection(material, heat))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.material is None or combo[1] == args.material)
        and (args.heat is None or combo[2] == args.heat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, material_id, heat_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    herring_id = args.herring or rng.choice(sorted(RED_HERRINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_cfg = rng.choice(HELPERS)

    return StoryParams(
        theme=theme_id,
        material=material_id,
        heat=heat_id,
        repair=repair_id,
        herring=herring_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_cfg["name"],
        helper_type=helper_cfg["type"],
        relation=helper_cfg["relation"],
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        material = MATERIALS[params.material]
        heat = HEAT_SOURCES[params.heat]
        repair = REPAIRS[params.repair]
        herring = RED_HERRINGS[params.herring]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not is_heat_risk(material, heat):
        raise StoryError(explain_rejection(material, heat))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        theme=theme,
        material=material,
        heat=heat,
        repair=repair,
        herring=herring,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        relation=params.relation,
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

    c_sense = set(asp_sensible_repairs())
    p_sense = {r.id for r in sensible_repairs()}
    if c_sense == p_sense:
        print(f"OK: sensible repairs match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        repairs = asp_sensible_repairs()
        print(f"sensible repairs: {', '.join(repairs)}\n")
        print(f"{len(combos)} compatible (theme, material, heat) combos:\n")
        for theme_id, material_id, heat_id in combos:
            print(f"  {theme_id:16} {material_id:10} {heat_id}")
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
                f"### {p.hero_name}: {p.material} by {p.heat} "
                f"({p.theme}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
