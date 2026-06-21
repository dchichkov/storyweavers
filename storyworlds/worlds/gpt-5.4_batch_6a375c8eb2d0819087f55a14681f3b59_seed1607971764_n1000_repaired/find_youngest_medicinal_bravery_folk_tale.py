#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py
=======================================================================

A standalone story world for a small folk-tale domain:

    A family member falls ill.
    The youngest child must find a medicinal plant in a risky place.
    Fear and bravery matter.
    A helper, a tool, or a careful method can turn danger into success.
    The story ends with healing, or with a wise retreat and a later safer cure.

The world model tracks:
- physical meters: sickness, danger, storm, scratches, found, brewed, healed
- emotional memes: fear, bravery, hope, relief, trust, humility

The domain is intentionally narrow. It prefers fewer strong stories over many
weak combinations, and rejects unreasonable pairings with legible StoryError
messages.

Run it
------
    python storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py --quest moonleaf --place cliffside
    python storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py --place market
    python storyworlds/worlds/gpt-5.4/find_youngest_medicinal_bravery_folk_tale.py --verify
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
COURAGE_NEEDED = 5
GUIDANCE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    safe_climber: bool = False
    good_in_dark: bool = False
    knows_paths: bool = False
    cures: set[str] = field(default_factory=set)
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
            "mother": "mother",
            "father": "father",
            "grandmother": "grandmother",
            "grandfather": "grandfather",
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
class Quest:
    id: str
    need_label: str
    patient_type: str
    symptom: str
    opening: str
    lesson: str
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
class Place:
    id: str
    label: str
    phrase: str
    risk: str
    danger: int
    dark: bool = False
    steep: bool = False
    distant: bool = False
    grows: set[str] = field(default_factory=set)
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
class Herb:
    id: str
    label: str
    phrase: str
    brew_name: str
    cures: set[str] = field(default_factory=set)
    medicinal: bool = True
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
class Guide:
    id: str
    label: str
    phrase: str
    helps_dark: bool = False
    helps_steep: bool = False
    helps_distant: bool = False
    courage: int = 0
    wisdom: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_dark: bool = False
    helps_steep: bool = False
    helps_distant: bool = False
    courage: int = 0
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_sickness_worry(world: World) -> list[str]:
    patient = world.get("patient")
    hero = world.get("hero")
    if patient.meters["sick"] < THRESHOLD:
        return []
    sig = ("worry", patient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["love"] += 1
    hero.memes["hope"] += 1
    return []


def _r_danger_fear(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    if place.meters["danger"] < THRESHOLD:
        return []
    sig = ("fear", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return []


def _r_found_hope(world: World) -> list[str]:
    herb = world.get("herb")
    hero = world.get("hero")
    if herb.meters["found"] < THRESHOLD:
        return []
    sig = ("found", herb.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    return []


def _r_brew_heal(world: World) -> list[str]:
    patient = world.get("patient")
    herb = world.get("herb")
    if herb.meters["brewed"] < THRESHOLD:
        return []
    if not (set(patient.attrs.get("needs", [])) & set(herb.cures)):
        return []
    sig = ("heal", patient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["sick"] = 0.0
    patient.meters["healed"] += 1
    hero = world.get("hero")
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="sickness_worry", tag="emotional", apply=_r_sickness_worry),
    Rule(name="danger_fear", tag="emotional", apply=_r_danger_fear),
    Rule(name="found_hope", tag="emotional", apply=_r_found_hope),
    Rule(name="brew_heal", tag="physical", apply=_r_brew_heal),
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
        if not any(rule.apply(world) for rule in []):
            pass
        if any(sig for sig in world.fired):
            changed = any(rule.apply(world) for rule in [])
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def guidance_score(place: Place, guide: Guide, tool: Tool) -> int:
    score = guide.courage + tool.courage
    if place.dark and (guide.helps_dark or tool.helps_dark):
        score += 2
    if place.steep and (guide.helps_steep or tool.helps_steep):
        score += 2
    if place.distant and (guide.helps_distant or tool.helps_distant):
        score += 1
    return score


def herb_reachable(place: Place, herb: Herb) -> bool:
    return herb.id in place.grows


def herb_matches(quest: Quest, herb: Herb) -> bool:
    return bool(set(quest.tags) & set(herb.cures))


def is_reasonable(quest: Quest, place: Place, herb: Herb, guide: Guide, tool: Tool) -> bool:
    if not herb_reachable(place, herb):
        return False
    if not herb_matches(quest, herb):
        return False
    if place.danger > 3 and guidance_score(place, guide, tool) < GUIDANCE_MIN:
        return False
    return True


def explain_rejection(quest: Quest, place: Place, herb: Herb, guide: Guide, tool: Tool) -> str:
    if not herb_reachable(place, herb):
        return (
            f"(No story: {herb.label} does not grow in {place.label}, so the youngest child "
            f"cannot honestly find it there.)"
        )
    if not herb_matches(quest, herb):
        return (
            f"(No story: {herb.label} is medicinal, but it is not the right cure for "
            f"{quest.symptom}.)"
        )
    if place.danger > 3 and guidance_score(place, guide, tool) < GUIDANCE_MIN:
        return (
            f"(No story: {place.label} is too dangerous for this guide-and-tool pairing. "
            f"The world expects some real help for a risky journey.)"
        )
    return "(No story: this combination is unreasonable.)"


def courage_total(hero: Entity, guide: Guide, tool: Tool, place: Place) -> int:
    total = int(hero.memes["bravery"]) + guide.courage + tool.courage
    if place.dark and guide.helps_dark:
        total += 1
    if place.dark and tool.helps_dark:
        total += 1
    if place.steep and guide.helps_steep:
        total += 1
    if place.steep and tool.helps_steep:
        total += 1
    if place.distant and guide.helps_distant:
        total += 1
    return total


def journey_succeeds(hero: Entity, guide: Guide, tool: Tool, place: Place) -> bool:
    return courage_total(hero, guide, tool, place) >= place.danger + COURAGE_NEEDED


def predict_journey(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    place_ent = sim.get("place")
    guide = sim.facts["guide"]
    tool = sim.facts["tool"]
    success = journey_succeeds(hero, guide, tool, sim.facts["place_cfg"])
    if not success:
        hero.meters["scratches"] += 1
        hero.memes["fear"] += 1
    return {
        "success": success,
        "fear": hero.memes["fear"],
        "scratches": hero.meters["scratches"],
    }


def introduce_house(world: World, hero: Entity, patient: Entity, elder1: Entity, elder2: Entity, quest: Quest) -> None:
    world.say(
        f"In a little valley village, there lived three children with their {elder1.label_word} "
        f"and {elder2.label_word}. The youngest was {hero.id}, small in size but quick in heart."
    )
    world.say(
        f"One autumn evening, {patient.label_word} grew {quest.symptom}. {quest.opening}"
    )


def elders_hesitate(world: World, elder1: Entity, elder2: Entity, hero: Entity, place: Place) -> None:
    world.say(
        f"{elder1.label_word.capitalize()} looked toward {place.phrase}, and {elder2.label_word} did the same. "
        f"The path was known for {place.risk}."
    )
    world.say(
        f'"Who will go?" asked {elder1.label_word}. The older children lowered their eyes, '
        f"but {hero.id} listened closely."
    )


def youngest_offers(world: World, hero: Entity, herb: Herb, patient: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"I will go and find the {herb.label}," said {hero.id}. '
        f'"If it is truly medicinal and can help {patient.label_word}, I must try."'
    )


def wise_warning(world: World, elder1: Entity, hero: Entity, place: Place, guide: Guide, tool: Tool) -> None:
    pred = predict_journey(world)
    world.facts["predicted_success"] = pred["success"]
    elder_name = elder1.label_word.capitalize()
    extra = ""
    if pred["success"]:
        extra = " Yet the child had enough help to make the road possible."
    else:
        extra = " Without better help, the road would bite back."
    world.say(
        f'{elder_name} answered softly, "Bravery is not loud feet on a dangerous path. '
        f'Bravery is keeping your wits." {guide.label.capitalize()} would go near, and {tool.phrase} would go too.{extra}'
    )


def set_out(world: World, hero: Entity, place: Place, guide: Guide, tool: Tool) -> None:
    place_ent = world.get("place")
    place_ent.meters["danger"] = float(place.danger)
    propagate(world, narrate=False)
    world.say(
        f"So before moonrise, {hero.id} set out for {place.phrase} with {guide.phrase} and {tool.phrase}."
    )


def journey_win(world: World, hero: Entity, place: Place, herb: Herb, guide: Guide, tool: Tool) -> None:
    herb_ent = world.get("herb")
    herb_ent.meters["found"] += 1
    propagate(world, narrate=False)
    hero.memes["bravery"] += 1
    detail = []
    if place.dark:
        detail.append("the dark between the trees no longer seemed to swallow the path")
    if place.steep:
        detail.append("the steep stones felt less cruel under careful feet")
    if place.distant:
        detail.append("the long road grew shorter with each steady step")
    bridge = " and ".join(detail) if detail else "the path felt less dreadful"
    world.say(
        f"The wind muttered, but {hero.id} did not turn back. With {guide.label} close and {tool.label} in hand, "
        f"{bridge}."
    )
    world.say(
        f"At last the youngest child found the {herb.label}, silver with dew. "
        f"{hero.pronoun().capitalize()} gathered the medicinal leaves carefully and hurried home."
    )


def journey_fail(world: World, hero: Entity, place: Place, guide: Guide, tool: Tool) -> None:
    hero.meters["scratches"] += 1
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    world.say(
        f"But the night winds rose around {place.phrase}, and even with {guide.label} and {tool.label}, "
        f"the way was harsher than {hero.id} had hoped."
    )
    world.say(
        f"{hero.id} came home with scratched hands and wise eyes. "
        f'{hero.pronoun().capitalize()} said, "I was brave enough to begin, and brave enough to turn back before the path took more than it should."'
    )


def brew_medicine(world: World, elder2: Entity, herb: Herb, patient: Entity) -> None:
    herb_ent = world.get("herb")
    herb_ent.meters["brewed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder2.label_word.capitalize()} crushed the {herb.label} into {herb.brew_name} and gave it to {patient.label_word}."
    )


def healing_end(world: World, hero: Entity, patient: Entity, quest: Quest) -> None:
    world.say(
        f"By dawn, the fever had loosened its grip. Color returned to {patient.label_word}'s face, "
        f"and the house felt warm again."
    )
    world.say(
        f"From that day on, the village remembered that the youngest among them had shown true Bravery: "
        f"not wild rushing, but a steady heart that could find help and carry it home."
    )
    world.facts["outcome"] = "healed"


def retreat_end(world: World, elder1: Entity, patient: Entity, guide: Guide) -> None:
    patient.meters["sick"] = max(0.0, patient.meters["sick"] - 0.5)
    patient.memes["comfort"] += 1
    world.say(
        f"{elder1.label_word.capitalize()} sent for a traveling healer at first light, and {guide.label} showed the quickest road."
    )
    world.say(
        f"Before the next night had fallen, fresh medicine came. {patient.label_word.capitalize()} rested easier, and everyone understood that true Bravery can also mean knowing when to ask for more help."
    )
    world.facts["outcome"] = "retreated"


def tell(
    quest: Quest,
    place: Place,
    herb: Herb,
    guide: Guide,
    tool: Tool,
    youngest_name: str = "Mira",
    youngest_gender: str = "girl",
    elder1_type: str = "mother",
    elder2_type: str = "grandmother",
    older1_name: str = "Iven",
    older2_name: str = "Sela",
    bravery_base: int = 4,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=youngest_name,
        kind="character",
        type=youngest_gender,
        role="youngest",
        traits=["youngest", "kind"],
    ))
    elder1 = world.add(Entity(
        id="Elder1",
        kind="character",
        type=elder1_type,
        role="elder",
        label=elder1_type,
    ))
    elder2 = world.add(Entity(
        id="Elder2",
        kind="character",
        type=elder2_type,
        role="elder",
        label=elder2_type,
    ))
    world.add(Entity(
        id=older1_name,
        kind="character",
        type="boy",
        role="older_sibling",
        traits=["older"],
    ))
    world.add(Entity(
        id=older2_name,
        kind="character",
        type="girl",
        role="older_sibling",
        traits=["older"],
    ))
    patient = world.add(Entity(
        id="patient",
        kind="character",
        type=quest.patient_type,
        role="patient",
        label=quest.patient_type,
        attrs={"needs": set(quest.tags)},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
    ))
    herb_ent = world.add(Entity(
        id="herb",
        kind="thing",
        type="herb",
        label=herb.label,
        cures=set(herb.cures),
    ))

    hero.memes["bravery"] = float(bravery_base)
    hero.memes["fear"] = 0.0
    hero.memes["hope"] = 0.0
    patient.meters["sick"] = 1.0
    place_ent.meters["danger"] = 0.0
    herb_ent.meters["found"] = 0.0
    herb_ent.meters["brewed"] = 0.0

    world.facts.update(
        quest=quest,
        place_cfg=place,
        herb_cfg=herb,
        guide=guide,
        tool=tool,
        hero=hero,
        patient=patient,
        elder1=elder1,
        elder2=elder2,
    )

    propagate(world, narrate=False)

    introduce_house(world, hero, patient, elder1, elder2, quest)
    elders_hesitate(world, elder1, elder2, hero, place)

    world.para()
    youngest_offers(world, hero, herb, patient)
    wise_warning(world, elder1, hero, place, guide, tool)

    world.para()
    set_out(world, hero, place, guide, tool)
    success = journey_succeeds(hero, guide, tool, place)
    world.facts["journey_success"] = success
    if success:
        journey_win(world, hero, place, herb, guide, tool)
        world.para()
        brew_medicine(world, elder2, herb, patient)
        healing_end(world, hero, patient, quest)
    else:
        journey_fail(world, hero, place, guide, tool)
        world.para()
        retreat_end(world, elder1, patient, guide)

    world.facts.update(
        bravery_total=courage_total(hero, guide, tool, place),
        place_danger=place.danger,
        herb_found=herb_ent.meters["found"] >= THRESHOLD,
        healed=patient.meters["healed"] >= THRESHOLD,
        scratches=hero.meters["scratches"],
    )
    return world


QUESTS = {
    "fever": Quest(
        id="fever",
        need_label="fever",
        patient_type="grandmother",
        symptom="with fever and a dry brow that still burned",
        opening="The old women whispered that only a mountain herb might cool her.",
        lesson="steady courage",
        tags={"fever"},
    ),
    "cough": Quest(
        id="cough",
        need_label="cough",
        patient_type="grandfather",
        symptom="with a hard cough that shook his chest",
        opening="The neighbors said a bitter brew from the wild places could soothe him.",
        lesson="gentle courage",
        tags={"cough"},
    ),
    "sleep": Quest(
        id="sleep",
        need_label="sleeplessness",
        patient_type="mother",
        symptom="so weary that sleep would not stay with her",
        opening="People remembered an old medicinal leaf that calmed both breath and heart.",
        lesson="quiet courage",
        tags={"sleep"},
    ),
}

PLACES = {
    "moonwood": Place(
        id="moonwood",
        label="the moonwood",
        phrase="the moonwood beyond the mill",
        risk="shifting shadows and owl-cries",
        danger=2,
        dark=True,
        grows={"moonleaf", "silvermint"},
        tags={"forest", "dark"},
    ),
    "cliffside": Place(
        id="cliffside",
        label="the cliffside",
        phrase="the cliffside above the river",
        risk="loose stones and thin ledges",
        danger=4,
        steep=True,
        distant=True,
        grows={"sunroot"},
        tags={"cliff", "steep"},
    ),
    "marsh": Place(
        id="marsh",
        label="the marsh",
        phrase="the reed marsh by the black pond",
        risk="cold mist and hidden water",
        danger=3,
        dark=True,
        distant=True,
        grows={"silvermint"},
        tags={"marsh", "mist"},
    ),
    "market": Place(
        id="market",
        label="the market square",
        phrase="the market square",
        risk="noise and cart wheels",
        danger=0,
        grows=set(),
        tags={"village"},
    ),
}

HERBS = {
    "moonleaf": Herb(
        id="moonleaf",
        label="moonleaf",
        phrase="a braid of moonleaf",
        brew_name="a pale moonleaf tea",
        cures={"sleep"},
        tags={"medicinal", "leaf"},
    ),
    "sunroot": Herb(
        id="sunroot",
        label="sunroot",
        phrase="a bundle of sunroot",
        brew_name="a golden sunroot broth",
        cures={"fever"},
        tags={"medicinal", "root"},
    ),
    "silvermint": Herb(
        id="silvermint",
        label="silvermint",
        phrase="a handful of silvermint",
        brew_name="a sharp silvermint steam",
        cures={"cough"},
        tags={"medicinal", "mint"},
    ),
}

GUIDES = {
    "goat": Guide(
        id="goat",
        label="the sure-footed goat",
        phrase="the sure-footed goat",
        helps_steep=True,
        courage=1,
        wisdom="It knew where stone held firm.",
        tags={"animal", "cliff"},
    ),
    "owl": Guide(
        id="owl",
        label="the old owl",
        phrase="the old owl that knew the night paths",
        helps_dark=True,
        courage=1,
        wisdom="It blinked toward the safest branch and hollow.",
        tags={"animal", "night"},
    ),
    "reed_boat": Guide(
        id="reed_boat",
        label="the reed boat",
        phrase="a narrow reed boat guided by the ferryman",
        helps_distant=True,
        courage=1,
        wisdom="It cut straight through slow water.",
        tags={"boat", "water"},
    ),
    "none": Guide(
        id="none",
        label="no guide",
        phrase="only the village silence",
        courage=0,
        wisdom="No guide came.",
        tags=set(),
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a lantern with a horn window",
        helps_dark=True,
        courage=1,
        tags={"light"},
    ),
    "staff": Tool(
        id="staff",
        label="a walking staff",
        phrase="a walking staff of ash wood",
        helps_steep=True,
        courage=1,
        tags={"staff"},
    ),
    "satchel": Tool(
        id="satchel",
        label="a satchel",
        phrase="a satchel for leaves and roots",
        helps_distant=True,
        courage=0,
        tags={"bag"},
    ),
    "none": Tool(
        id="none",
        label="bare hands",
        phrase="bare hands and a thin shawl",
        courage=0,
        tags=set(),
    ),
}


def default_guide_for(place_id: str) -> str:
    if place_id == "cliffside":
        return "goat"
    if place_id == "moonwood":
        return "owl"
    if place_id == "marsh":
        return "reed_boat"
    return "none"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id, quest in QUESTS.items():
        for place_id, place in PLACES.items():
            for herb_id, herb in HERBS.items():
                for tool_id, tool in TOOLS.items():
                    guide_id = default_guide_for(place_id)
                    guide = GUIDES[guide_id]
                    if is_reasonable(quest, place, herb, guide, tool):
                        combos.append((quest_id, place_id, herb_id, tool_id))
    return combos


@dataclass
class StoryParams:
    quest: str
    place: str
    herb: str
    guide: str
    tool: str
    youngest_name: str
    youngest_gender: str
    elder1_type: str
    elder2_type: str
    older1_name: str
    older2_name: str
    bravery_base: int = 4
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


GIRL_NAMES = ["Mira", "Anya", "Lina", "Tala", "Niva", "Elin", "Sora", "Vela"]
BOY_NAMES = ["Tarin", "Oren", "Milo", "Pavel", "Jorin", "Niko", "Ilan", "Ravi"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    herb = f["herb_cfg"]
    place = f["place_cfg"]
    outcome = f.get("outcome", "")
    tail = "and returns with healing" if outcome == "healed" else "and learns wise courage"
    return [
        f'Write a short Folk Tale for a 3-to-5-year-old where the youngest child must find a medicinal plant.',
        f"Tell a folk tale in which {hero.id}, the youngest child, shows Bravery by going to {place.label} to find {herb.label} for {quest.patient_type}.",
        f'Write a gentle village tale that includes the words "find", "youngest", and "medicinal", {tail}.',
    ]


KNOWLEDGE = {
    "medicinal": [(
        "What does medicinal mean?",
        "Medicinal means something can help treat sickness or make a body feel better. Many plants were used as medicine in old tales."
    )],
    "herb": [(
        "What is an herb?",
        "An herb is a plant people use for smell, taste, or healing. Some herbs are cooked or brewed into tea."
    )],
    "lantern": [(
        "Why does a lantern help in the dark?",
        "A lantern makes light so people can see where they are stepping. Seeing the path can keep them safer."
    )],
    "staff": [(
        "Why can a walking staff help on a steep path?",
        "A staff gives a traveler another point to lean on. That helps with balance on rocks and hills."
    )],
    "owl": [(
        "Why might an owl be a good guide at night?",
        "Owls see well in the dark and know quiet night places. In folk tales, they often stand for wisdom."
    )],
    "goat": [(
        "Why is a goat good on a cliffside?",
        "Goats are good at climbing on narrow rocky places. Their sure feet make them symbols of balance."
    )],
    "tea": [(
        "How can leaves become medicine?",
        "People can steep certain leaves or roots in hot water or broth. The drink carries the useful part of the plant."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery is doing a hard thing while still being careful and thoughtful. It is not the same as being wild or careless."
    )],
}

KNOWLEDGE_ORDER = ["medicinal", "herb", "bravery", "lantern", "staff", "owl", "goat", "tea"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    patient = f["patient"]
    quest = f["quest"]
    herb = f["herb_cfg"]
    place = f["place_cfg"]
    guide = f["guide"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the youngest child in a village family. {hero.pronoun().capitalize()} set out because {patient.label_word} was ill and the house needed help."
        ),
        (
            f"Why did {hero.id} leave home?",
            f"{hero.id} left home to find {herb.label}, a medicinal plant. The family hoped it could help {patient.label_word}, who was {quest.symptom}."
        ),
        (
            f"Why was the journey to {place.label} frightening?",
            f"The journey was frightening because {place.phrase} was known for {place.risk}. That danger is why the tale treats the trip as a test of Bravery, not just a walk."
        ),
    ]
    if f["journey_success"]:
        qa.append((
            f"How did {hero.id} manage to find the herb?",
            f"{hero.id} kept going with {guide.label} and {tool.label}. Their help matched the trouble of the path, so the youngest child could stay brave and careful at the same time."
        ))
        qa.append((
            f"What happened after they brought back the {herb.label}?",
            f"{f['elder2'].label_word.capitalize()} brewed it into medicine for {patient.label_word}. By dawn, the patient felt better, which showed why the herb mattered."
        ))
        qa.append((
            "How does the ending show true Bravery?",
            f"The ending shows Bravery because the youngest child did not boast or rush wildly. {hero.id} faced fear, found what was needed, and carried help home."
        ))
    else:
        qa.append((
            f"Did {hero.id} bring back the {herb.label}?",
            f"No. {hero.id} turned back when the path grew too harsh. That choice still mattered, because it kept the child safe enough for the family to seek help another way."
        ))
        qa.append((
            "How was the problem solved in the end?",
            f"The family sent for a healer at first light. The patient rested easier once new medicine came, so the ending still resolves the danger with wisdom instead of stubbornness."
        ))
        qa.append((
            "How does the ending still show Bravery?",
            f"It shows Bravery because the youngest child was brave enough to begin and brave enough to stop. In the tale, wisdom and courage belong together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"medicinal", "herb", "bravery", "tea"}
    tool = world.facts["tool"]
    guide = world.facts["guide"]
    if tool.id == "lantern":
        tags.add("lantern")
    if tool.id == "staff":
        tags.add("staff")
    if guide.id == "owl":
        tags.add("owl")
    if guide.id == "goat":
        tags.add("goat")
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="fever",
        place="cliffside",
        herb="sunroot",
        guide="goat",
        tool="staff",
        youngest_name="Mira",
        youngest_gender="girl",
        elder1_type="mother",
        elder2_type="grandmother",
        older1_name="Iven",
        older2_name="Sela",
        bravery_base=4,
    ),
    StoryParams(
        quest="sleep",
        place="moonwood",
        herb="moonleaf",
        guide="owl",
        tool="lantern",
        youngest_name="Tarin",
        youngest_gender="boy",
        elder1_type="father",
        elder2_type="grandmother",
        older1_name="Jorin",
        older2_name="Niva",
        bravery_base=3,
    ),
    StoryParams(
        quest="cough",
        place="marsh",
        herb="silvermint",
        guide="reed_boat",
        tool="satchel",
        youngest_name="Anya",
        youngest_gender="girl",
        elder1_type="mother",
        elder2_type="grandfather",
        older1_name="Milo",
        older2_name="Elin",
        bravery_base=4,
    ),
]


ASP_RULES = r"""
reachable(H,P) :- grows(P,H).
matches(Q,H) :- quest_need(Q,N), cures(H,N).
guide_score(P,G,T,S) :- place(P), guide(G), tool(T),
                        S = CG + CT + A + B + C,
                        guide_courage(G,CG), tool_courage(T,CT),
                        A = #count{1 : dark(P), guide_dark(G); 1 : dark(P), tool_dark(T)},
                        B = #count{1 : steep(P), guide_steep(G); 1 : steep(P), tool_steep(T)},
                        C = #count{1 : distant(P), guide_distant(G)}.
reasonable(Q,P,H,G,T) :- reachable(H,P), matches(Q,H), place_danger(P,D), D <= 3, guide(G), tool(T).
reasonable(Q,P,H,G,T) :- reachable(H,P), matches(Q,H), place_danger(P,D), D > 3, guide_score(P,G,T,S), S >= 2.

courage_total(B,G,T,P,Sum) :- bravery_base(B), chosen_guide(G), chosen_tool(T), chosen_place(P),
                              guide_courage(G,CG), tool_courage(T,CT),
                              A = #count{1 : dark(P), guide_dark(G); 1 : dark(P), tool_dark(T)},
                              B2 = #count{1 : steep(P), guide_steep(G); 1 : steep(P), tool_steep(T)},
                              C = #count{1 : distant(P), guide_distant(G)},
                              Sum = B + CG + CT + A + B2 + C.
journey_success :- chosen_place(P), place_danger(P,D), courage_total(_,_,_,_,S), S >= D + 5.
outcome(healed) :- journey_success.
outcome(retreated) :- not journey_success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        for need in sorted(quest.tags):
            lines.append(asp.fact("quest_need", quest_id, need))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_danger", place_id, place.danger))
        if place.dark:
            lines.append(asp.fact("dark", place_id))
        if place.steep:
            lines.append(asp.fact("steep", place_id))
        if place.distant:
            lines.append(asp.fact("distant", place_id))
        for herb_id in sorted(place.grows):
            lines.append(asp.fact("grows", place_id, herb_id))
    for herb_id, herb in HERBS.items():
        lines.append(asp.fact("herb", herb_id))
        for need in sorted(herb.cures):
            lines.append(asp.fact("cures", herb_id, need))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        lines.append(asp.fact("guide_courage", guide_id, guide.courage))
        if guide.helps_dark:
            lines.append(asp.fact("guide_dark", guide_id))
        if guide.helps_steep:
            lines.append(asp.fact("guide_steep", guide_id))
        if guide.helps_distant:
            lines.append(asp.fact("guide_distant", guide_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_courage", tool_id, tool.courage))
        if tool.helps_dark:
            lines.append(asp.fact("tool_dark", tool_id))
        if tool.helps_steep:
            lines.append(asp.fact("tool_steep", tool_id))
        if tool.helps_distant:
            lines.append(asp.fact("tool_distant", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show reasonable/5."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_guide", params.guide),
        asp.fact("chosen_tool", params.tool),
        asp.fact("bravery_base", params.bravery_base),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.quest not in QUESTS or params.place not in PLACES or params.herb not in HERBS:
        raise StoryError("(No story: unknown quest, place, or herb.)")
    if params.guide not in GUIDES or params.tool not in TOOLS:
        raise StoryError("(No story: unknown guide or tool.)")
    quest = QUESTS[params.quest]
    place = PLACES[params.place]
    herb = HERBS[params.herb]
    guide = GUIDES[params.guide]
    tool = TOOLS[params.tool]
    if not is_reasonable(quest, place, herb, guide, tool):
        raise StoryError(explain_rejection(quest, place, herb, guide, tool))
    hero = Entity(id="x", kind="character", type=params.youngest_gender)
    hero.memes["bravery"] = float(params.bravery_base)
    return "healed" if journey_succeeds(hero, guide, tool, place) else "retreated"


def asp_verify() -> int:
    rc = 0
    python_set = set((q, p, h, default_guide_for(p), t) for (q, p, h, t) in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed for seed {s}.")
    bad = 0
    for p in cases:
        try:
            py = outcome_of(p)
            cl = asp_outcome(p)
            if py != cl:
                bad += 1
        except StoryError as err:
            rc = 1
            print(f"Unexpected StoryError during parity check: {err}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: the youngest child must find a medicinal herb with Bravery in a folk-tale world."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--youngest-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder1", choices=["mother", "father"])
    ap.add_argument("--elder2", choices=["grandmother", "grandfather"])
    ap.add_argument("--bravery-base", type=int, choices=[3, 4, 5], dest="bravery_base")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_place = args.place
    explicit_guide = args.guide or (default_guide_for(explicit_place) if explicit_place else None)

    if args.quest and args.place and args.herb:
        guide_id = explicit_guide or default_guide_for(args.place)
        tool_id = args.tool or "none"
        quest = QUESTS[args.quest]
        place = PLACES[args.place]
        herb = HERBS[args.herb]
        guide = GUIDES[guide_id]
        tool = TOOLS[tool_id]
        if not is_reasonable(quest, place, herb, guide, tool):
            raise StoryError(explain_rejection(quest, place, herb, guide, tool))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.place is None or c[1] == args.place)
        and (args.herb is None or c[2] == args.herb)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, place_id, herb_id, tool_id = rng.choice(sorted(combos))
    guide_id = default_guide_for(place_id)
    if args.guide and args.guide != guide_id:
        raise StoryError(
            f"(No story: {args.guide} is not the guide used for {place_id} in this small tale world. "
            f"Try --guide {guide_id}.)"
        )

    gender = args.gender or rng.choice(["girl", "boy"])
    youngest_name = args.youngest_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder1_type = args.elder1 or rng.choice(["mother", "father"])
    elder2_type = args.elder2 or rng.choice(["grandmother", "grandfather"])
    older1_name = rng.choice([n for n in BOY_NAMES if n != youngest_name] or BOY_NAMES)
    older2_name = rng.choice([n for n in GIRL_NAMES if n != youngest_name] or GIRL_NAMES)
    bravery_base = args.bravery_base if args.bravery_base is not None else rng.choice([3, 4, 5])

    return StoryParams(
        quest=quest_id,
        place=place_id,
        herb=herb_id,
        guide=guide_id,
        tool=tool_id,
        youngest_name=youngest_name,
        youngest_gender=gender,
        elder1_type=elder1_type,
        elder2_type=elder2_type,
        older1_name=older1_name,
        older2_name=older2_name,
        bravery_base=bravery_base,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.place not in PLACES or params.herb not in HERBS:
        raise StoryError("(No story: unknown quest, place, or herb.)")
    if params.guide not in GUIDES or params.tool not in TOOLS:
        raise StoryError("(No story: unknown guide or tool.)")

    quest = QUESTS[params.quest]
    place = PLACES[params.place]
    herb = HERBS[params.herb]
    guide = GUIDES[params.guide]
    tool = TOOLS[params.tool]

    if params.guide != default_guide_for(params.place):
        raise StoryError(
            f"(No story: this world pairs {params.place} with guide {default_guide_for(params.place)}.)"
        )
    if not is_reasonable(quest, place, herb, guide, tool):
        raise StoryError(explain_rejection(quest, place, herb, guide, tool))

    world = tell(
        quest=quest,
        place=place,
        herb=herb,
        guide=guide,
        tool=tool,
        youngest_name=params.youngest_name,
        youngest_gender=params.youngest_gender,
        elder1_type=params.elder1_type,
        elder2_type=params.elder2_type,
        older1_name=params.older1_name,
        older2_name=params.older2_name,
        bravery_base=params.bravery_base,
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
        print(asp_program("", "#show reasonable/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, place, herb, guide, tool) combos:\n")
        for quest, place, herb, guide, tool in combos:
            print(f"  {quest:6} {place:10} {herb:10} {guide:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.youngest_name}: {p.quest} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
