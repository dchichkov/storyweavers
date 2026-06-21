#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py
================================================================================

A standalone storyworld about a child on a small home quest: keeping a special
plant healthy for school or for someone they love. The child does research, gets
impatient, and is tempted to use a silly shortcut that promises faster growth.
A careful helper warns them. Sometimes the warning works; sometimes the shortcut
causes a mess and the plant droops; sometimes a grown-up can save it in time.

This world keeps the tone close to slice-of-life: a windowsill, a notebook,
plain water, a worried child, and a calm ending shaped by what the simulated
state became.

Run it
------
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py --quest fair --shortcut soda --plant bean
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py --plant paper_flower
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py --response glitter_fix
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/research_piddle_special_quest_cautionary_slice_of.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
PATIENCE_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    living: bool = False
    plant: bool = False
    helper_like: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Quest:
    id: str
    goal: str
    reason: str
    opening: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    where: str
    splash: str
    warning: str
    lesson: str
    severity: int
    sticky: bool = False
    corrosive: bool = False
    sugary: bool = False
    unsafe: bool = True
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
class PlantCfg:
    id: str
    label: str
    phrase: str
    pot: str
    leaves: str
    sensitivity: int
    living: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_plant_stress(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if plant is None:
        return out
    harm = plant.meters["sugar"] + plant.meters["soap"] + plant.meters["overfeed"]
    if harm < THRESHOLD:
        return out
    sig = ("stress", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["stress"] += 1
    plant.meters["droop"] += 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__droop__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    table = world.entities.get("table")
    jar = world.entities.get("shortcut")
    if table is None or jar is None:
        return out
    mess = jar.meters["spilled"]
    if mess < THRESHOLD:
        return out
    sig = ("spill", jar.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    table.meters["mess"] += 1
    if "hero" in world.entities:
        world.get("hero").memes["alarm"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="plant_stress", tag="physical", apply=_r_plant_stress),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def hazard_at_risk(shortcut: Shortcut, plant: PlantCfg) -> bool:
    return shortcut.unsafe and plant.living


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def trouble_severity(shortcut: Shortcut, plant: PlantCfg, delay: int) -> int:
    return shortcut.severity + plant.sensitivity + delay


def is_recovered(response: Response, shortcut: Shortcut, plant: PlantCfg, delay: int) -> bool:
    return response.power >= trouble_severity(shortcut, plant, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = (initial_care(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > PATIENCE_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    shortcut = sim.get("shortcut")
    cfg: Shortcut = sim.facts["shortcut_cfg"]
    if cfg.sugary:
        plant.meters["sugar"] += 1
    if cfg.corrosive:
        plant.meters["soap"] += 1
    if not cfg.sugary and not cfg.corrosive:
        plant.meters["overfeed"] += 1
    shortcut.meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "droop": sim.get("plant").meters["droop"] >= THRESHOLD,
        "mess": sim.get("table").meters["mess"] >= THRESHOLD,
    }


def setup_quest(world: World, hero: Entity, helper: Entity, quest: Quest, plant: PlantCfg) -> None:
    hero.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{quest.opening} {hero.id} had {quest.goal}. On the windowsill sat {plant.phrase} in {plant.pot}, "
        f"and it already felt special."
    )
    world.say(
        f"{hero.id} and {helper.id} made a little notebook page full of research about light, soil, and plain water."
    )


def need_patience(world: World, hero: Entity, quest: Quest, plant: PlantCfg) -> None:
    world.say(
        f"But the quest moved slowly. {plant.the.capitalize()} only had {plant.leaves}, and {hero.id} wanted it to look ready {quest.reason} right away."
    )
    world.say(
        f"{hero.id} leaned close to the pot and whispered, \"Grow, little plant. I need you for my special job.\""
    )


def tempt(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f"Then {hero.id} spotted {shortcut.phrase} {shortcut.where}. \"Maybe this will help,\" {hero.pronoun()} said. "
        f"The idea felt quick and clever."
    )


def warn(world: World, helper: Entity, hero: Entity, shortcut: Shortcut, adult: Entity, plant: PlantCfg) -> None:
    pred = predict_trouble(world)
    helper.memes["caution"] += 1
    world.facts["predicted_droop"] = pred["droop"]
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if helper.memes["caution"] >= 6:
        extra = f" {helper.pronoun().capitalize()} tapped the research page with one finger."
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "The research says plain water only," '
        f'{helper.pronoun()} said. "{shortcut.warning} Ask {adult.label_word} if you are not sure."{extra}'
    )


def defy(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    hero.memes["defiance"] += 1
    older_sib = hero.attrs.get("relation") == "siblings" and hero.age > helper.age
    if older_sib:
        rel = "big brother" if hero.type == "boy" else "big sister"
        world.say(
            f'"It will be fine," {hero.id} said, and because {hero.pronoun()} was {helper.pronoun("possessive")} {rel}, '
            f'{helper.id} could not stop {hero.pronoun("object")}.'
        )
    else:
        world.say(
            f'"It will be fine," {hero.id} said, and reached for it anyway.'
        )


def back_down(world: World, hero: Entity, helper: Entity, shortcut: Shortcut, adult: Entity) -> None:
    hero.memes["impatience"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    rel = "brother" if helper.type == "boy" else "sister"
    world.say(
        f'{hero.id} looked from the bottle to the notebook. Then {hero.pronoun()} sighed. '
        f'"Okay," {hero.pronoun()} said. "I only wanted the quest to go faster."'
    )
    world.say(
        f"{helper.id}, the older {rel}, put the shortcut back {shortcut.where}. Together they called for {adult.label_word} instead of guessing."
    )


def pour_shortcut(world: World, hero: Entity, shortcut: Shortcut, plant: Entity) -> None:
    tool = world.get("shortcut")
    tool.meters["spilled"] += 1
    if shortcut.sugary:
        plant.meters["sugar"] += 1
    if shortcut.corrosive:
        plant.meters["soap"] += 1
    if not shortcut.sugary and not shortcut.corrosive:
        plant.meters["overfeed"] += 1
    propagate(world, narrate=False)
    piddle_line = (
        f"A little piddle of {shortcut.splash} ran across the saucer and onto the sill."
        if world.get("table").meters["mess"] >= THRESHOLD
        else ""
    )
    leaf_line = (
        f"Almost at once, {plant.label}'s {world.facts['plant_cfg'].leaves} did not look so proud anymore."
        if plant.meters["droop"] >= THRESHOLD
        else ""
    )
    world.say(
        f"{hero.id} tipped in {shortcut.phrase}. {piddle_line} {leaf_line}".strip()
    )


def alarm(world: World, helper: Entity, hero: Entity, plant: PlantCfg, adult: Entity) -> None:
    world.say(
        f'"{hero.id}, look!" {helper.id} cried. "{plant.the.capitalize()} is drooping!"'
    )
    world.say(f'"{adult.label_word.upper()}!"')


def rescue(world: World, adult: Entity, response: Response, plant: Entity, plant_cfg: PlantCfg) -> None:
    plant.meters["droop"] = 0.0
    plant.meters["stress"] = 0.0
    world.get("table").meters["mess"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came quickly and {response.text.replace('{plant}', plant_cfg.label)}."
    )
    world.say(
        f"Soon the sill was clean again, and {plant_cfg.the} stood a little straighter in the light."
    )


def lesson(world: World, adult: Entity, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    for child in (hero, helper):
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        child.memes["worry"] = 0.0
    world.say(
        f'{adult.label_word.capitalize()} set the bottle far away and knelt beside them. '
        f'"I know you wanted to help," {adult.pronoun()} said softly. '
        f'"But {shortcut.lesson}. When a living thing is counting on you, guessing can hurt it."'
    )
    world.say(
        f"{hero.id} nodded and looked at the research page again."
    )


def patient_end(world: World, adult: Entity, hero: Entity, helper: Entity, quest: Quest, plant_cfg: PlantCfg) -> None:
    for child in (hero, helper):
        child.memes["joy"] += 1
        child.memes["patience"] += 1
    world.say(
        f"That evening, {adult.label_word} helped them make a tiny watering mark on the cup and write one new line in the notebook: plain water, a sunny window, and patience."
    )
    world.say(
        f"The next morning, {plant_cfg.the} looked fresh again. {quest.ending}"
    )


def rescue_fail(world: World, adult: Entity, response: Response, plant_cfg: PlantCfg) -> None:
    plant = world.get("plant")
    plant.meters["wilting"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried over and {response.fail.replace('{plant}', plant_cfg.label)}."
    )
    world.say(
        f"But by bedtime, {plant_cfg.the} had gone limp, and the room felt very quiet."
    )


def sad_lesson(world: World, adult: Entity, hero: Entity, helper: Entity, shortcut: Shortcut, quest: Quest) -> None:
    for child in (hero, helper):
        child.memes["lesson"] += 1
        child.memes["sadness"] += 1
    world.say(
        f'{adult.label_word.capitalize()} hugged them close. "We cannot rush every living thing," {adult.pronoun()} said. '
        f'"Next time we will follow the research from the start."'
    )
    world.say(
        f"{hero.id} put the notebook away very carefully. The quest was not over, but it had become a quieter one."
    )


def restart(world: World, adult: Entity, hero: Entity, helper: Entity, quest: Quest, plant_cfg: PlantCfg) -> None:
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"The next day, {adult.label_word} brought home a fresh packet of seeds. Together they planted one more, and this time {hero.id} measured every drop."
    )
    world.say(
        f"In the window, the new pot waited in clean soil. {quest.ending.replace('looked fresh again', 'was only dark soil for now')}"
    )


def tell(
    quest: Quest,
    shortcut: Shortcut,
    plant_cfg: PlantCfg,
    response: Response,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_name: str = "Leo",
    helper_gender: str = "boy",
    adult_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
        traits=["eager"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        attrs={"relation": relation},
        traits=[trait],
        helper_like=True,
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    plant = world.add(Entity(
        id="plant",
        kind="thing",
        type="plant",
        role="plant",
        label=plant_cfg.label,
        living=plant_cfg.living,
        plant=True,
    ))
    shortcut_ent = world.add(Entity(
        id="shortcut",
        kind="thing",
        type="bottle",
        role="shortcut",
        label=shortcut.label,
    ))
    world.add(Entity(
        id="table",
        kind="thing",
        type="windowsill",
        role="place",
        label="the windowsill",
    ))

    hero.memes["patience"] = PATIENCE_INIT
    helper.memes["caution"] = initial_care(trait)
    world.facts.update(
        quest=quest,
        shortcut_cfg=shortcut,
        plant_cfg=plant_cfg,
        response=response,
        relation=relation,
    )

    setup_quest(world, hero, helper, quest, plant_cfg)
    need_patience(world, hero, quest, plant_cfg)

    world.para()
    tempt(world, hero, shortcut)
    warn(world, helper, hero, shortcut, adult, plant_cfg)

    averted = would_avert(relation, hero_age, helper_age, trait)

    if averted:
        back_down(world, hero, helper, shortcut, adult)
        world.para()
        patient_end(world, adult, hero, helper, quest, plant_cfg)
        severity = 0
        recovered = True
    else:
        defy(world, hero, helper, shortcut)
        world.para()
        pour_shortcut(world, hero, shortcut, plant)
        alarm(world, helper, hero, plant_cfg, adult)

        severity = trouble_severity(shortcut, plant_cfg, delay)
        plant.meters["severity"] = float(severity)
        recovered = is_recovered(response, shortcut, plant_cfg, delay)

        world.para()
        if recovered:
            rescue(world, adult, response, plant, plant_cfg)
            lesson(world, adult, hero, helper, shortcut)
            world.para()
            patient_end(world, adult, hero, helper, quest, plant_cfg)
        else:
            rescue_fail(world, adult, response, plant_cfg)
            sad_lesson(world, adult, hero, helper, shortcut, quest)
            world.para()
            restart(world, adult, hero, helper, quest, plant_cfg)

    outcome = "averted" if averted else ("recovered" if recovered else "spoiled")
    world.facts.update(
        hero=hero,
        helper=helper,
        adult=adult,
        plant=plant,
        shortcut=shortcut_ent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        drooped=plant.meters["droop"] >= THRESHOLD or plant.meters["wilting"] >= THRESHOLD,
        promised=hero.memes["lesson"] >= THRESHOLD or hero.memes["patience"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "fair": Quest(
        id="fair",
        goal="a special quest for the school windowsill fair",
        reason="for the fair on Monday",
        opening="On Saturday morning,",
        ending="By breakfast, the children were smiling at the window again, already planning what careful notes to bring to the fair.",
        tags={"school", "quest"},
    ),
    "gift": Quest(
        id="gift",
        goal="a special quest to grow a tiny gift for Grandma",
        reason="before Grandma's visit",
        opening="After lunch on a bright Sunday,",
        ending="By breakfast, the children were smiling at the window again, eager to show Grandma a plant cared for the slow and proper way.",
        tags={"family", "quest"},
    ),
    "classroom": Quest(
        id="classroom",
        goal="a special quest to return the class plant looking strong",
        reason="when school opened again",
        opening="On a quiet weekend afternoon,",
        ending="By breakfast, the children were smiling at the window again, ready to bring back a better story about patience than about shortcuts.",
        tags={"school", "quest"},
    ),
}

SHORTCUTS = {
    "soda": Shortcut(
        id="soda",
        label="soda",
        phrase="a cup of fizzy soda",
        where="beside the toaster",
        splash="brown, sticky soda",
        warning="Sugar is for treats, not for roots",
        lesson="plants do not grow better with soda",
        severity=2,
        sugary=True,
        sticky=True,
        unsafe=True,
        tags={"soda", "plants"},
    ),
    "soap": Shortcut(
        id="soap",
        label="soapy water",
        phrase="a jar of soapy water",
        where="by the sink",
        splash="slippery bubbles",
        warning="Soap can hurt leaves and roots",
        lesson="soap belongs with washing dishes, not with watering plants",
        severity=3,
        corrosive=True,
        unsafe=True,
        tags={"soap", "plants"},
    ),
    "fertilizer": Shortcut(
        id="fertilizer",
        label="strong plant food",
        phrase="a capful of strong plant food",
        where="under the sink",
        splash="dark green drips",
        warning="Too much plant food can burn a little plant",
        lesson="more plant food is not the same as better care",
        severity=2,
        unsafe=True,
        tags={"fertilizer", "plants"},
    ),
    "plain_water": Shortcut(
        id="plain_water",
        label="plain water",
        phrase="a spoon of plain water",
        where="in the measuring cup",
        splash="clear water",
        warning="plain water is already the right choice",
        lesson="plain water is the safe thing to use",
        severity=0,
        unsafe=False,
        tags={"water"},
    ),
}

PLANTS = {
    "bean": PlantCfg(
        id="bean",
        label="bean plant",
        phrase="a little bean plant",
        pot="a red paper cup with a sun drawn on it",
        leaves="two soft leaves",
        sensitivity=1,
        living=True,
        tags={"bean", "plant"},
    ),
    "basil": PlantCfg(
        id="basil",
        label="basil plant",
        phrase="a small basil plant",
        pot="a striped clay pot",
        leaves="small green leaves that smelled sweet when touched",
        sensitivity=2,
        living=True,
        tags={"basil", "plant"},
    ),
    "marigold": PlantCfg(
        id="marigold",
        label="marigold seedling",
        phrase="a brave marigold seedling",
        pot="a yellow pot near the kitchen window",
        leaves="frilly leaves",
        sensitivity=2,
        living=True,
        tags={"marigold", "plant"},
    ),
    "paper_flower": PlantCfg(
        id="paper_flower",
        label="paper flower",
        phrase="a paper flower on a craft stick",
        pot="a pencil cup full of crayons",
        leaves="paper petals",
        sensitivity=0,
        living=False,
        tags={"craft"},
    ),
}

RESPONSES = {
    "flush": Response(
        id="flush",
        sense=3,
        power=5,
        text="carried the {plant} to the sink, gently flushed the soil with clean water, and blotted the sill dry",
        fail="carried the {plant} to the sink and tried to flush the soil, but the roots had already taken too much of the wrong liquid",
        qa_text="flushed the soil with clean water and cleaned the sill",
        tags={"flush", "plants"},
    ),
    "repot": Response(
        id="repot",
        sense=3,
        power=4,
        text="tipped the {plant} into fresh soil, trimmed away the worst wet clumps, and set it back in the sun",
        fail="repotted the {plant} into fresh soil, but it was already too shocked to recover that day",
        qa_text="repotted it into fresh soil and set it back in the sun",
        tags={"repot", "plants"},
    ),
    "wipe_only": Response(
        id="wipe_only",
        sense=2,
        power=2,
        text="wiped the sill, gave the pot one careful rinse, and turned the cup toward the light",
        fail="wiped the sill and gave the pot only a quick rinse, but that was not enough to undo the mistake",
        qa_text="wiped the sill and gave the pot a quick rinse",
        tags={"wipe", "plants"},
    ),
    "glitter_fix": Response(
        id="glitter_fix",
        sense=1,
        power=0,
        text="sprinkled craft glitter around the cup as if sparkles could cheer the plant up",
        fail="sprinkled craft glitter around the cup, which did nothing to help the plant at all",
        qa_text="tried a glitter fix",
        tags={"glitter"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Noah", "Finn", "Theo"]
TRAITS = ["careful", "patient", "thoughtful", "steady", "curious", "busy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for qid in QUESTS:
        for sid, shortcut in SHORTCUTS.items():
            for pid, plant in PLANTS.items():
                if hazard_at_risk(shortcut, plant):
                    combos.append((qid, sid, pid))
    return combos


@dataclass
class StoryParams:
    quest: str
    shortcut: str
    plant: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
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
    "plant": [(
        "Why do plants usually need plain water and light?",
        "Plants use water and light to grow. Fancy drinks do not make them stronger, and some can hurt the roots."
    )],
    "soda": [(
        "Why is soda bad for a plant?",
        "Soda has sugar and other things a plant does not need. Instead of helping the roots, it can leave a sticky mess and stress the plant."
    )],
    "soap": [(
        "Why can soapy water hurt a plant?",
        "Soap is for cleaning, not for feeding roots. It can bother leaves and roots and make a plant droop."
    )],
    "fertilizer": [(
        "Can too much plant food be a problem?",
        "Yes. A little plant only needs a small amount, and too much can burn or shock it instead of helping it grow."
    )],
    "flush": [(
        "Why might clean water help after the wrong liquid goes into a plant pot?",
        "Clean water can wash some of the wrong liquid out of the soil. That gives the roots a better chance to recover."
    )],
    "repot": [(
        "What does repotting a plant mean?",
        "Repotting means moving a plant into fresh soil or another pot. Fresh soil can help if the old soil has something harmful in it."
    )],
    "wipe": [(
        "Why should you wipe up a spill on a windowsill?",
        "A spill can stay sticky or slippery and make another mess. Cleaning it quickly keeps the place safe and tidy."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a job or mission you care about and keep working on. It can be something small and homey, like caring for one little plant."
    )],
    "research": [(
        "What is research?",
        "Research means looking up good information so you can learn before you act. Reading care notes first is one kind of research."
    )],
}
KNOWLEDGE_ORDER = ["quest", "research", "plant", "soda", "soap", "fertilizer", "flush", "repot", "wipe"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    shortcut = f["shortcut_cfg"]
    plant = f["plant_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old where a child does research for {quest.goal} '
        f'and is tempted to use {shortcut.label} on {plant.the}. Include the words "research", "special", and "piddle".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle quest story where {hero.id} wants a faster result, but {helper.id} points back to the research notes and stops the mistake before anything goes wrong.",
            "Write a quiet home story where patience becomes the real victory, and the ending image shows children caring for a plant the careful way.",
        ]
    if outcome == "spoiled":
        return [
            base,
            f"Tell a cautionary story where {hero.id} ignores the warning, {plant.the} is badly hurt, and the family must begin again more carefully the next day.",
            "Write a child-facing story with a sad but hopeful turn: the first try is spoiled by a shortcut, and the new beginning proves the lesson was learned.",
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {hero.id} makes a mistake with {shortcut.label}, a grown-up helps save {plant.the}, and the child learns that research and patience matter.",
        "Write a simple family story where the problem is fixed, the lesson is calm, and the ending image shows careful measuring instead of guessing.",
    ]


def relation_pair(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    quest = f["quest"]
    shortcut = f["shortcut_cfg"]
    plant = f["plant_cfg"]
    response = f["response"]
    pair = relation_pair(hero, helper, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, and the grown-up who helped them. Together they were trying to care for {plant.phrase}."
        ),
        (
            "What was the quest?",
            f"The children had {quest.goal}. The plant mattered because it was meant {quest.reason}, so it felt important and special to them."
        ),
        (
            "Why did they do research?",
            f"They wanted to care for the plant the right way, so they wrote down research about light, soil, and plain water. The notes were there to stop guessing when the quest felt slow."
        ),
        (
            f"Why did {hero.id} want to use {shortcut.label}?",
            f"{hero.id} was impatient and wanted the plant to look ready sooner. The shortcut seemed like a quick fix because the quest felt important."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How was the problem avoided?",
            f"{helper.id} pointed back to the research notes and made {hero.id} stop before pouring anything. Because the warning came in time, the plant never drooped and the windowsill stayed clean."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with careful measuring, plain water, and patience. The final picture shows the children trusting the slow, safe way instead of a shortcut."
        ))
    elif f["outcome"] == "recovered":
        qa.append((
            f"What happened when {hero.id} poured {shortcut.label} into the pot?",
            f"{plant.the.capitalize()} drooped, and a spill made a mess on the sill. A little piddle of the wrong liquid showed that the mistake affected both the plant and the room."
        ))
        qa.append((
            "How did the grown-up help?",
            f"The grown-up {response.qa_text.replace('{plant}', plant.label)}. That helped because quick cleanup and proper plant care gave the roots a chance to recover."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that research and patience are better than guessing. A living thing needs the right care, not whatever seems fast or fancy."
        ))
    else:
        qa.append((
            f"Could the plant be saved?",
            f"No, not that first plant. The wrong liquid had already hurt it too much, so the family had to begin again with new seeds the next day."
        ))
        qa.append((
            "Was the ending only sad?",
            f"No. It was sad because the first plant was spoiled, but it was hopeful too. The new seed and the careful measuring showed that the children had learned from the mistake."
        ))
        qa.append((
            "What is the caution in this story?",
            f"The caution is that a shortcut can hurt something living even when you mean well. The second chance matters because the children change how they act after the mistake."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest"].tags) | set(f["plant_cfg"].tags) | set(f["shortcut_cfg"].tags) | {"research"}
    outcome = f["outcome"]
    if outcome == "recovered":
        tags |= set(f["response"].tags)
    elif outcome == "spoiled":
        tags |= set(f["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.living:
            bits.append("living=True")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="fair",
        shortcut="soda",
        plant="bean",
        response="flush",
        hero="Mia",
        hero_gender="girl",
        helper="Leo",
        helper_gender="boy",
        adult="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        quest="gift",
        shortcut="soap",
        plant="basil",
        response="repot",
        hero="Ben",
        hero_gender="boy",
        helper="Ava",
        helper_gender="girl",
        adult="father",
        trait="thoughtful",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        quest="classroom",
        shortcut="fertilizer",
        plant="marigold",
        response="wipe_only",
        hero="Zoe",
        hero_gender="girl",
        helper="Max",
        helper_gender="boy",
        adult="mother",
        trait="patient",
        delay=1,
        hero_age=6,
        helper_age=4,
        relation="friends",
    ),
    StoryParams(
        quest="fair",
        shortcut="soap",
        plant="basil",
        response="flush",
        hero="Eli",
        hero_gender="boy",
        helper="Noah",
        helper_gender="boy",
        adult="father",
        trait="careful",
        delay=0,
        hero_age=5,
        helper_age=8,
        relation="siblings",
    ),
    StoryParams(
        quest="gift",
        shortcut="soda",
        plant="marigold",
        response="repot",
        hero="Lily",
        hero_gender="girl",
        helper="Maya",
        helper_gender="girl",
        adult="mother",
        trait="steady",
        delay=1,
        hero_age=7,
        helper_age=5,
        relation="siblings",
    ),
]


def explain_rejection(shortcut: Shortcut, plant: PlantCfg) -> str:
    if not plant.living:
        return (
            f"(No story: {plant.phrase} is not a living plant, so {shortcut.label} would not create a real care mistake. "
            f"Pick a living plant like bean, basil, or marigold.)"
        )
    if not shortcut.unsafe:
        return (
            f"(No story: {shortcut.label} is already the safe choice, so there is no cautionary turn to model. "
            f"Pick an unsafe shortcut like soda, soap, or fertilizer.)"
        )
    return "(No story: this combination does not create a real plant-care problem.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    return "recovered" if is_recovered(RESPONSES[params.response], SHORTCUTS[params.shortcut], PLANTS[params.plant], params.delay) else "spoiled"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try one of the safer fixes: {better}.)"
    )


ASP_RULES = r"""
hazard(S, P) :- unsafe_shortcut(S), living_plant(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Q, S, P) :- quest(Q), shortcut(S), plant(P), hazard(S, P).

careful_now(T) :- trait(T), is_careful(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).
helper_older :- relation(siblings), hero_age(HA), helper_age(HB), HB > HA.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- helper_older, authority(A), patience_init(P), A > P.

severity(Sv + Ps + D) :- chosen_shortcut(S), shortcut_severity(S, Sv), chosen_plant(P), plant_sensitivity(P, Ps), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(spoiled) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for sid, s in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        if s.unsafe:
            lines.append(asp.fact("unsafe_shortcut", sid))
        lines.append(asp.fact("shortcut_severity", sid, s.severity))
    for pid, p in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("plant_sensitivity", pid, p.sensitivity))
        if p.living:
            lines.append(asp.fact("living_plant", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("patience_init", int(PATIENCE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_plant", params.plant),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise AssertionError("empty story")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True, header="### smoke")


def asp_verify() -> int:
    rc = 0

    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: research, a special plant quest, and a cautionary shortcut."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the wrong liquid sits before the grown-up helps")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and not PLANTS[args.plant].living:
        shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
        raise StoryError(explain_rejection(shortcut, PLANTS[args.plant]))
    if args.shortcut and not SHORTCUTS[args.shortcut].unsafe:
        plant = PLANTS[args.plant] if args.plant else next(p for p in PLANTS.values() if p.living)
        raise StoryError(explain_rejection(SHORTCUTS[args.shortcut], plant))
    if args.shortcut and args.plant:
        if not hazard_at_risk(SHORTCUTS[args.shortcut], PLANTS[args.plant]):
            raise StoryError(explain_rejection(SHORTCUTS[args.shortcut], PLANTS[args.plant]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.shortcut is None or c[1] == args.shortcut)
        and (args.plant is None or c[2] == args.plant)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, shortcut, plant = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero, hero_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=hero)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([3, 4, 5, 6, 7, 8], 2)

    return StoryParams(
        quest=quest,
        shortcut=shortcut,
        plant=plant,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.adult not in {"mother", "father"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")

    shortcut = SHORTCUTS[params.shortcut]
    plant_cfg = PLANTS[params.plant]
    if not hazard_at_risk(shortcut, plant_cfg):
        raise StoryError(explain_rejection(shortcut, plant_cfg))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        QUESTS[params.quest],
        shortcut,
        plant_cfg,
        RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, shortcut, plant) combos:\n")
        for quest, shortcut, plant in combos:
            print(f"  {quest:10} {shortcut:10} {plant}")
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
            header = f"### {p.hero} & {p.helper}: {p.shortcut} near {p.plant} ({p.quest}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
