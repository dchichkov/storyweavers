#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py
==============================================================================

A standalone story world for a small fable-shaped domain:

A young helper works beside a careful forester. At a forest watering place,
something needs cleaning. The helper grows tense because of a flashback: once,
the word "chlorine" was part of a sharp, frightening mistake. In the present,
the forester chooses a wiser method, explains the old fear, and the two are
reconciled while making the place safe again for thirsty animals.

This world prefers a narrow set of plausible variants over loose coverage:
not every cleaning method fits every water place, and chlorine is known to the
world only as an unreasonable choice for these shared forest waters.

Run it
------
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --place birdbath --problem algae
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --method chlorine
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --all
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --trace
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --json
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --asp
    python storyworlds/worlds/gpt-5.4/forester_chlorine_flashback_reconciliation_fable.py --verify
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
        pron = self.attrs.get("pronouns", "they")
        table = {
            "she": {"subject": "she", "object": "her", "possessive": "her"},
            "he": {"subject": "he", "object": "him", "possessive": "his"},
            "they": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(pron, table["they"])[case]
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
class WaterPlace:
    id: str
    label: str
    phrase: str
    keeper_task: str
    animals: str
    material: str
    wildlife_shared: bool = True
    allowed_methods: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    sign: str
    harm: str
    fix_need: str
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
class Method:
    id: str
    label: str
    sense: int
    safe_for_wildlife: bool
    handles: set[str] = field(default_factory=set)
    allowed_places: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
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
    label: str
    sense: int
    opening: str
    follow: str
    closing: str
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


def _r_dirty_water(world: World) -> list[str]:
    place = world.get("place")
    if place.meters["dirty"] < THRESHOLD:
        return []
    sig = ("dirty_water",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["unfit"] += 1
    apprentice = world.get("apprentice")
    apprentice.memes["concern"] += 1
    return []


def _r_chemical_risk(world: World) -> list[str]:
    place = world.get("place")
    if place.meters["chemical_near"] < THRESHOLD:
        return []
    sig = ("chemical_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if place.attrs.get("wildlife_shared"):
        place.meters["danger"] += 1
    apprentice = world.get("apprentice")
    forester = world.get("forester")
    apprentice.memes["shame"] += 1
    apprentice.memes["fear"] += 1
    forester.memes["alarm"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    apprentice = world.get("apprentice")
    forester = world.get("forester")
    if apprentice.memes["heard_kindness"] < THRESHOLD or apprentice.memes["worked_together"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    apprentice.memes["trust"] += 1
    apprentice.memes["relief"] += 1
    apprentice.memes["fear"] = 0.0
    apprentice.memes["shame"] = 0.0
    forester.memes["warmth"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="dirty_water", tag="physical", apply=_r_dirty_water),
    Rule(name="chemical_risk", tag="physical", apply=_r_chemical_risk),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
            world.say(sent)
    return produced


PLACES = {
    "birdbath": WaterPlace(
        id="birdbath",
        label="birdbath",
        phrase="a stone birdbath in a sunlit clearing",
        keeper_task="fill the shallow bowl with clean water",
        animals="finches and robins",
        material="stone",
        wildlife_shared=True,
        allowed_methods={"brush_refill", "rake_skim", "drain_refill"},
        tags={"birdbath", "water_animals"},
    ),
    "trough": WaterPlace(
        id="trough",
        label="deer trough",
        phrase="a long wooden trough by the pines",
        keeper_task="keep the long trough sweet and clear",
        animals="deer and hares",
        material="wood",
        wildlife_shared=True,
        allowed_methods={"brush_refill", "rake_skim", "drain_refill"},
        tags={"trough", "water_animals"},
    ),
    "pond": WaterPlace(
        id="pond",
        label="lily pond",
        phrase="a small lily pond under willow shade",
        keeper_task="keep the pond open enough for thirsty paws and beaks",
        animals="frogs and sparrows",
        material="earth",
        wildlife_shared=True,
        allowed_methods={"rake_skim"},
        tags={"pond", "water_animals"},
    ),
}

PROBLEMS = {
    "algae": Problem(
        id="algae",
        label="green slime",
        sign="a green rim clung to the edge",
        harm="the water smelled sleepy and stale",
        fix_need="it needed a careful scrub and fresh water",
        tags={"algae", "dirty_water"},
    ),
    "leaves": Problem(
        id="leaves",
        label="wind-blown leaves",
        sign="wet leaves floated in little brown boats",
        harm="the water was hidden under a ragged lid of leaves",
        fix_need="it needed skimming before the animals could see their drink",
        tags={"leaves", "dirty_water"},
    ),
    "wrigglers": Problem(
        id="wrigglers",
        label="mosquito wrigglers",
        sign="tiny black commas twitched in the still water",
        harm="the water had stood too long",
        fix_need="it needed to be emptied and filled again",
        tags={"mosquitoes", "dirty_water"},
    ),
}

METHODS = {
    "brush_refill": Method(
        id="brush_refill",
        label="brush and fresh water",
        sense=3,
        safe_for_wildlife=True,
        handles={"algae"},
        allowed_places={"birdbath", "trough"},
        action="scrubbed the rim with a stiff brush, tipped the old water out onto thirsty roots, and filled the basin with fresh water from the hand pump",
        qa_text="scrubbed the place clean and filled it with fresh water",
        tags={"brush", "fresh_water"},
    ),
    "rake_skim": Method(
        id="rake_skim",
        label="rake and skimming net",
        sense=3,
        safe_for_wildlife=True,
        handles={"leaves", "algae"},
        allowed_places={"birdbath", "trough", "pond"},
        action="worked a small rake through the mess and lifted the drift away with a skimming net until the water shone again",
        qa_text="lifted the mess away with a rake and net",
        tags={"rake", "net"},
    ),
    "drain_refill": Method(
        id="drain_refill",
        label="drain and refill",
        sense=3,
        safe_for_wildlife=True,
        handles={"wrigglers", "algae"},
        allowed_places={"birdbath", "trough"},
        action="poured the old water onto the ferns, rinsed the basin, and filled it again with clear cold water",
        qa_text="emptied the old water and filled the place again",
        tags={"fresh_water", "drain"},
    ),
    "chlorine": Method(
        id="chlorine",
        label="chlorine",
        sense=1,
        safe_for_wildlife=False,
        handles={"algae", "wrigglers"},
        allowed_places={"birdbath", "trough"},
        action="uncorked the chlorine bottle and reached for the water",
        qa_text="reached for chlorine",
        tags={"chlorine", "chemical"},
    ),
}

REPAIRS = {
    "apology": Repair(
        id="apology",
        label="apology",
        sense=3,
        opening='The old forester saw the worry in the small face and spoke first. "Pip, I was too sharp that spring day," he said.',
        follow='"I was afraid for the thirsty creatures, not angry at your heart. A warning can be true and still be said more gently."',
        closing='The words landed softly, like pine needles on moss.',
        tags={"apology", "kind_words"},
    ),
    "shared_task": Repair(
        id="shared_task",
        label="shared task",
        sense=3,
        opening='The forester set the tools down between them. "Come beside me," he said. "I trust your careful paws."',
        follow='"We will mend the water together, and we will mend your worry with it."',
        closing='The invitation made room where fear had been.',
        tags={"praise", "kind_words"},
    ),
    "scold_again": Repair(
        id="scold_again",
        label="another scolding",
        sense=1,
        opening='"Do not touch anything," the forester snapped.',
        follow='"You always make a muddle of it."',
        closing='The words only made the old hurt louder.',
        tags={"hurtful"},
    ),
}

ANIMAL_CAST = [
    {"name": "Pip", "type": "otter", "pronouns": "they"},
    {"name": "Moss", "type": "fox", "pronouns": "he"},
    {"name": "Wren", "type": "rabbit", "pronouns": "she"},
    {"name": "Tumble", "type": "badger", "pronouns": "they"},
    {"name": "Nettle", "type": "squirrel", "pronouns": "she"},
]

FORESTER_CAST = [
    {"name": "Alder", "type": "badger", "pronouns": "he"},
    {"name": "Rowan", "type": "wolf", "pronouns": "she"},
    {"name": "Bramble", "type": "bear", "pronouns": "he"},
]


def compatible_methods(place_id: str, problem_id: str) -> list[str]:
    out = []
    for mid, method in METHODS.items():
        if method.sense < SENSE_MIN:
            continue
        if problem_id in method.handles and place_id in method.allowed_places and mid in PLACES[place_id].allowed_methods:
            out.append(mid)
    return sorted(out)


def sensible_repairs() -> list[str]:
    return sorted(rid for rid, repair in REPAIRS.items() if repair.sense >= SENSE_MIN)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id in sorted(PLACES):
        for problem_id in sorted(PROBLEMS):
            for method_id in compatible_methods(place_id, problem_id):
                for repair_id in sensible_repairs():
                    combos.append((place_id, problem_id, method_id, repair_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    method: str
    repair: str
    apprentice_name: str
    apprentice_type: str
    apprentice_pronouns: str
    forester_name: str
    forester_type: str
    forester_pronouns: str
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


def introduce(world: World, apprentice: Entity, forester: Entity, place: WaterPlace) -> None:
    apprentice.memes["respect"] += 1
    world.say(
        f"In the deep green part of the forest, where paths smelled of bark and rain, "
        f"young {apprentice.id} walked beside {forester.id}, the old forester. "
        f"Together they watched over {place.phrase}."
    )
    world.say(
        f"The forester's work was simple to say and hard to keep: {place.keeper_task}, "
        f"so that {place.animals} would always find a safe sip."
    )


def discover_problem(world: World, apprentice: Entity, place_ent: Entity, problem: Problem) -> None:
    place_ent.meters["dirty"] += 1
    apprentice.memes["attention"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That morning, {problem.sign}, and {problem.harm}. "
        f"{apprentice.id} knew at once that {problem.fix_need}."
    )


def tremble_with_memory(world: World, apprentice: Entity) -> None:
    apprentice.memes["fear"] += 1
    apprentice.memes["shame"] += 1
    world.say(
        f"But instead of reaching for the tools, {apprentice.id} tucked "
        f"{apprentice.pronoun('possessive')} paws close. An old worry stirred like "
        f"a leaf caught in an eddy."
    )


def flashback(world: World, apprentice: Entity, forester: Entity, place: WaterPlace) -> None:
    place_ent = world.get("place")
    place_ent.meters["chemical_near"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A flashback came over {apprentice.id}: last spring, when {place.label} had "
        f"turned cloudy, {apprentice.pronoun()} had found a bright bottle labeled "
        f'"chlorine" in the shed and lifted it proudly, thinking strong smells meant strong help.'
    )
    world.say(
        f"{forester.id} had knocked the bottle gently but quickly away from the water. "
        f'"Not here," {forester.pronoun()} had cried. "These forest mouths all drink from one bowl."'
    )
    world.say(
        f"The bottle had splashed only on the stones, not into the water, yet the sharp "
        f"voice had stung. Since then, {apprentice.id} had quietly wondered whether "
        f"{forester.id} still saw only the mistake."
    )


def choose_wise_method(world: World, apprentice: Entity, forester: Entity, method: Method) -> None:
    apprentice.memes["heard_kindness"] += 1
    world.say(
        f"In the present, {forester.id} did not reach for any harsh bottle. "
        f"{forester.pronoun().capitalize()} picked up {method.label} instead."
    )
    world.say(
        f'"Water for wild creatures must be made clean without making it cruel," '
        f'{forester.pronoun()} said.'
    )


def speak_repair(world: World, apprentice: Entity, forester: Entity, repair: Repair) -> None:
    apprentice.memes["heard_kindness"] += 1
    world.say(repair.opening)
    world.say(repair.follow)
    world.say(repair.closing)


def work_together(world: World, apprentice: Entity, forester: Entity, place_ent: Entity, method: Method) -> None:
    apprentice.memes["worked_together"] += 1
    forester.memes["worked_together"] += 1
    place_ent.meters["dirty"] = 0.0
    place_ent.meters["unfit"] = 0.0
    place_ent.meters["clear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then apprentice and forester set to work. Side by side, they {method.action}."
    )
    world.say(
        f"As the water cleared, so did the space between them."
    )


def ending_image(world: World, apprentice: Entity, forester: Entity, place: WaterPlace) -> None:
    apprentice.memes["joy"] += 1
    forester.memes["warmth"] += 1
    world.say(
        f"Soon {place.animals} came back. They bent their heads, drank without fear, "
        f"and left tiny rings trembling across the clean water."
    )
    world.say(
        f'{apprentice.id} looked up at {forester.id}, and this time did not look away. '
        f'"Will you show me the right way again tomorrow?" {apprentice.pronoun()} asked.'
    )
    world.say(
        f'"Gladly," said the forester. "A careful heart is worth teaching twice."'
    )
    world.say(
        "And so the forest kept two gifts that day: clear water for thirsty creatures, "
        "and clear trust between two workers."
    )


def tell(
    place: WaterPlace,
    problem: Problem,
    method: Method,
    repair: Repair,
    apprentice_name: str,
    apprentice_type: str,
    apprentice_pronouns: str,
    forester_name: str,
    forester_type: str,
    forester_pronouns: str,
) -> World:
    world = World()
    apprentice = world.add(
        Entity(
            id=apprentice_name,
            kind="character",
            type=apprentice_type,
            label=apprentice_name,
            role="apprentice",
            attrs={"pronouns": apprentice_pronouns},
        )
    )
    forester = world.add(
        Entity(
            id=forester_name,
            kind="character",
            type=forester_type,
            label=forester_name,
            role="forester",
            attrs={"pronouns": forester_pronouns},
        )
    )
    place_ent = world.add(
        Entity(
            id="place",
            kind="thing",
            type="water_place",
            label=place.label,
            attrs={"wildlife_shared": place.wildlife_shared, "material": place.material},
        )
    )
    tool_ent = world.add(
        Entity(
            id="method",
            kind="thing",
            type="tool",
            label=method.label,
            attrs={"safe_for_wildlife": method.safe_for_wildlife},
        )
    )
    world.facts.update(
        apprentice=apprentice,
        forester=forester,
        place_cfg=place,
        place=place_ent,
        problem=problem,
        method=method,
        repair=repair,
        flashback_happened=False,
        reconciled=False,
        moral="Use gentle wisdom to mend both water and hearts.",
    )

    introduce(world, apprentice, forester, place)
    discover_problem(world, apprentice, place_ent, problem)

    world.para()
    tremble_with_memory(world, apprentice)
    flashback(world, apprentice, forester, place)
    world.facts["flashback_happened"] = True

    world.para()
    choose_wise_method(world, apprentice, forester, method)
    speak_repair(world, apprentice, forester, repair)
    work_together(world, apprentice, forester, place_ent, method)
    propagate(world, narrate=False)
    world.facts["reconciled"] = apprentice.memes["trust"] >= THRESHOLD and apprentice.memes["relief"] >= THRESHOLD

    world.para()
    ending_image(world, apprentice, forester, place)
    world.facts["water_safe"] = place_ent.meters["clear"] >= THRESHOLD and place_ent.meters["danger"] < THRESHOLD
    world.facts["outcome"] = "reconciled" if world.facts["reconciled"] else "strained"
    world.facts["tool"] = tool_ent
    return world


KNOWLEDGE = {
    "chlorine": [
        (
            "What is chlorine?",
            "Chlorine is a strong cleaning chemical. It can be useful in some grown-up jobs, but it should be kept away from children and from places where wild animals drink.",
        )
    ],
    "algae": [
        (
            "What is algae?",
            "Algae is a green, slippery growth that can form in still water. A little can be normal, but too much can make water dirty and less pleasant to drink.",
        )
    ],
    "leaves": [
        (
            "Why should leaves be skimmed out of drinking water?",
            "Old leaves can make water look dirty and smell stale. Taking them out helps keep the water clear for animals.",
        )
    ],
    "mosquitoes": [
        (
            "Why do mosquito wrigglers appear in still water?",
            "Mosquitoes lay eggs in water that stands still for too long. Emptying and refilling small water bowls helps stop that.",
        )
    ],
    "fresh_water": [
        (
            "Why do animals need fresh water?",
            "Animals need fresh water to drink safely. If water grows dirty or stale, they may get sick or have trouble finding a good drink.",
        )
    ],
    "birdbath": [
        (
            "What is a birdbath?",
            "A birdbath is a shallow basin where birds can drink and splash. It needs clean water because many small birds may use it.",
        )
    ],
    "trough": [
        (
            "What is a trough?",
            "A trough is a long container that can hold water for animals. In a forest story, it can help thirsty creatures find a safe drink.",
        )
    ],
    "pond": [
        (
            "Why should a small pond be kept clear of too many leaves?",
            "Too many leaves can cover the surface and make the water murky. Clearing some away helps light and air reach the water.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology can soften a hurt when someone speaks too harshly or makes a mistake. It shows that the speaker wants to repair trust, not just win an argument.",
        )
    ],
    "kind_words": [
        (
            "Why do kind words matter when teaching?",
            "Kind words help someone stay brave enough to learn. Sharp words may stop a mistake in the moment, but gentle truth helps the lesson stay in the heart.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "chlorine",
    "algae",
    "leaves",
    "mosquitoes",
    "fresh_water",
    "birdbath",
    "trough",
    "pond",
    "apology",
    "kind_words",
]


def generation_prompts(world: World) -> list[str]:
    apprentice = world.facts["apprentice"]
    forester = world.facts["forester"]
    place = world.facts["place_cfg"]
    problem = world.facts["problem"]
    method = world.facts["method"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "forester" and "chlorine" and uses a flashback and reconciliation.',
        f"Tell a gentle forest fable where {apprentice.id}, a young {apprentice.type}, fears that {forester.id} the forester no longer trusts {apprentice.pronoun('object')} after an old chlorine mistake, but they make peace while cleaning a {place.label}.",
        f"Write a child-facing story where {problem.label} troubles a forest water place, the wise fix is {method.label}, and the ending shows trust restored as clearly as the water.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    apprentice = world.facts["apprentice"]
    forester = world.facts["forester"]
    place = world.facts["place_cfg"]
    problem = world.facts["problem"]
    method = world.facts["method"]
    repair = world.facts["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {apprentice.id}, a young {apprentice.type}, and {forester.id}, the old forester. They care for {place.phrase} so {place.animals} can drink there.",
        ),
        (
            f"What problem did they find at the {place.label}?",
            f"They found {problem.label}: {problem.sign}. The place needed help because {problem.harm}.",
        ),
        (
            f"Why did {apprentice.id} grow quiet instead of helping right away?",
            f"{apprentice.id} remembered a springtime mistake involving a bottle marked chlorine. The flashback made {apprentice.pronoun('object')} worry that the forester still remembered the sharp moment more than the good intention.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {apprentice.id} almost brought chlorine to the shared water, thinking it would help. The forester stopped it quickly because wild animals drank there, and the sharp warning stayed in {apprentice.pronoun('possessive')} heart.",
        ),
        (
            f"How did the forester fix both the water and the hurt feeling?",
            f"The forester chose {method.label}, not chlorine, and then used {repair.label} to speak kindly. After that, they worked side by side, so the cleaning itself became part of the reconciliation.",
        ),
        (
            "How did the story end?",
            f"The water turned clear again, and {place.animals} came back to drink. The clean water showed the outside change, and {apprentice.id}'s lifted heart showed the inside change.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"chlorine", "fresh_water"} | set(world.facts["problem"].tags) | set(world.facts["place_cfg"].tags) | set(world.facts["repair"].tags) | set(world.facts["method"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_method_rejection(method_id: str, place_id: Optional[str] = None, problem_id: Optional[str] = None) -> str:
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': {method.label} is too harsh and unsafe for these forest water places. "
            f"Use a gentle method such as {', '.join(sorted(m for m in METHODS if METHODS[m].sense >= SENSE_MIN))} instead.)"
        )
    if place_id and problem_id:
        return (
            f"(No story: {method.label} does not reasonably fix {PROBLEMS[problem_id].label} at the {PLACES[place_id].label}. "
            f"Choose one of: {', '.join(compatible_methods(place_id, problem_id))}.)"
        )
    return "(No story: that method does not fit this problem.)"


def explain_repair_rejection(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    return (
        f"(Refusing repair '{repair_id}': {repair.label} does not lead to reconciliation. "
        f"Choose one of: {', '.join(sensible_repairs())}.)"
    )


CURATED = [
    StoryParams(
        place="birdbath",
        problem="algae",
        method="brush_refill",
        repair="apology",
        apprentice_name="Pip",
        apprentice_type="otter",
        apprentice_pronouns="they",
        forester_name="Alder",
        forester_type="badger",
        forester_pronouns="he",
    ),
    StoryParams(
        place="trough",
        problem="wrigglers",
        method="drain_refill",
        repair="shared_task",
        apprentice_name="Wren",
        apprentice_type="rabbit",
        apprentice_pronouns="she",
        forester_name="Rowan",
        forester_type="wolf",
        forester_pronouns="she",
    ),
    StoryParams(
        place="pond",
        problem="leaves",
        method="rake_skim",
        repair="apology",
        apprentice_name="Moss",
        apprentice_type="fox",
        apprentice_pronouns="he",
        forester_name="Bramble",
        forester_type="bear",
        forester_pronouns="he",
    ),
    StoryParams(
        place="birdbath",
        problem="leaves",
        method="rake_skim",
        repair="shared_task",
        apprentice_name="Nettle",
        apprentice_type="squirrel",
        apprentice_pronouns="she",
        forester_name="Alder",
        forester_type="badger",
        forester_pronouns="he",
    ),
]


ASP_RULES = r"""
% Reasonableness gate: a combo is valid when the method is sensible,
% handles the problem, and is allowed at the place.
valid(P, Pr, M) :- place(P), problem(Pr), method(M),
                   sensible_method(M),
                   handles(M, Pr),
                   allowed_place(M, P),
                   place_allows(P, M).

sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
sensible_repair(R) :- repair(R), repair_sense(R, S), sense_min(Min), S >= Min.

% Outcome model: with a valid cleaning choice and a sensible repair move,
% the old wound can be reconciled.
outcome(reconciled) :- chosen_place(P), chosen_problem(Pr), chosen_method(M), chosen_repair(R),
                       valid(P, Pr, M), sensible_repair(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for method_id in sorted(place.allowed_methods):
            lines.append(asp.fact("place_allows", place_id, method_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for problem_id in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, problem_id))
        for place_id in sorted(method.allowed_places):
            lines.append(asp.fact("allowed_place", method_id, place_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_sense", repair_id, repair.sense))
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

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if (params.place, params.problem, params.method, params.repair) not in {
        (p, pr, m, r) for (p, pr, m, r) in valid_combos()
    }:
        return "?"
    return "reconciled"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a forester, a chlorine memory, and reconciliation by wise care."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method, args.place, args.problem))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair_rejection(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        if args.place and args.problem and args.method:
            raise StoryError(explain_method_rejection(args.method, args.place, args.problem))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, method_id, repair_id = rng.choice(sorted(combos))
    apprentice_cfg = dict(rng.choice(ANIMAL_CAST))
    forester_cfg = dict(rng.choice(FORESTER_CAST))
    if apprentice_cfg["name"] == forester_cfg["name"]:
        forester_cfg = dict(FORESTER_CAST[0])

    return StoryParams(
        place=place_id,
        problem=problem_id,
        method=method_id,
        repair=repair_id,
        apprentice_name=apprentice_cfg["name"],
        apprentice_type=apprentice_cfg["type"],
        apprentice_pronouns=apprentice_cfg["pronouns"],
        forester_name=forester_cfg["name"],
        forester_type=forester_cfg["type"],
        forester_pronouns=forester_cfg["pronouns"],
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method, params.place, params.problem))
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair_rejection(params.repair))
    if params.method not in compatible_methods(params.place, params.problem):
        raise StoryError(explain_method_rejection(params.method, params.place, params.problem))

    world = tell(
        place=PLACES[params.place],
        problem=PROBLEMS[params.problem],
        method=METHODS[params.method],
        repair=REPAIRS[params.repair],
        apprentice_name=params.apprentice_name,
        apprentice_type=params.apprentice_type,
        apprentice_pronouns=params.apprentice_pronouns,
        forester_name=params.forester_name,
        forester_type=params.forester_type,
        forester_pronouns=params.forester_pronouns,
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
    py_valid = sorted((p, pr, m) for (p, pr, m, _r) in valid_combos())
    py_valid_unique = sorted(set(py_valid))
    asp_valid = asp_valid_combos()
    if py_valid_unique == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(asp_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(set(py_valid_unique) - set(asp_valid)))
        print("  only in clingo:", sorted(set(asp_valid) - set(py_valid_unique)))

    py_repairs = sensible_repairs()
    asp_repairs = asp_sensible_repairs()
    if py_repairs == asp_repairs:
        print(f"OK: sensible repairs match ({', '.join(py_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: python={py_repairs} clingo={asp_repairs}")

    py_methods = sorted(mid for mid, method in METHODS.items() if method.sense >= SENSE_MIN)
    asp_methods = asp_sensible_methods()
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({', '.join(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={py_methods} clingo={asp_methods}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_method/1.\n#show sensible_repair/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible_methods())}")
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, method) combos:\n")
        for place, problem, method in combos:
            print(f"  {place:9} {problem:10} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.apprentice_name} and {p.forester_name}: {p.problem} at {p.place} ({p.method}, {p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
