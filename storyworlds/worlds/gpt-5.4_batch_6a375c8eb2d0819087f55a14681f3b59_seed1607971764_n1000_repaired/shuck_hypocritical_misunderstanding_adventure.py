#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py
============================================================================

A standalone story world for a small child-facing adventure tale built around a
misunderstanding. Two children head into an exciting place to look for something
important. One child sees the other collecting trail markers and mistakes that
careful act for rule-breaking, even calling it "hypocritical." The misunderstanding
creates the turn; the explanation and the state of the trail solve it.

This world models:
- physical meters: distance, lostness, marker coverage, safety, tiredness
- emotional memes: excitement, worry, trust, shame, relief, courage
- a misunderstanding that comes from world state rather than template swapping

The key domain word "shuck" appears as a noun and verb in the corn-maze stories:
corn shucks can be braided into little trail ties. In other settings, other safe
marker materials are used.

Run it
------
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py --place maze --quest gosling --material shuck
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py --place cave --material chalk
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py --all
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shuck_hypocritical_misunderstanding_adventure.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    entry: str
    paths: str
    mood: str
    guide_type: str
    affords_quests: set[str] = field(default_factory=set)
    offers_materials: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    target: str
    clue: str
    sound: str
    ending_image: str
    needs_tracking: bool = True
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
    verb: str
    visible_score: int
    gentle: bool = True
    place_only: set[str] = field(default_factory=set)
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
class Delay:
    id: str
    misunderstanding_steps: int
    lost_risk: int
    line: str
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


def _r_marked_path(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    if leader.meters["markers"] < THRESHOLD:
        return out
    sig = ("marked_path",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trail = world.get("trail")
    trail.meters["visible_path"] += 1
    trail.meters["lost_risk"] = 0.0
    out.append("__path__")
    return out


def _r_unmarked_wander(world: World) -> list[str]:
    out: list[str] = []
    trail = world.get("trail")
    if trail.meters["visible_path"] >= THRESHOLD:
        return out
    if trail.meters["distance"] < THRESHOLD:
        return out
    sig = ("wander",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trail.meters["lost_risk"] += 1
    for eid in ("leader", "partner"):
        world.get(eid).memes["worry"] += 1
    out.append("__wander__")
    return out


def _r_quarrel(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.memes["misunderstood"] < THRESHOLD:
        return out
    sig = ("quarrel",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.memes["hurt"] += 1
    partner.memes["shame"] += 0.0
    partner.memes["anger"] += 1
    partner.memes["trust"] -= 1
    out.append("__quarrel__")
    return out


def _r_explained(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.memes["explained"] < THRESHOLD:
        return out
    sig = ("explained",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    partner.memes["anger"] = 0.0
    partner.memes["shame"] += 1
    partner.memes["trust"] += 2
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    out.append("__explained__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    trail = world.get("trail")
    if trail.meters["visible_path"] < THRESHOLD:
        return out
    if trail.meters["distance"] < THRESHOLD:
        return out
    sig = ("found",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["found"] += 1
    for eid in ("leader", "partner"):
        world.get(eid).memes["courage"] += 1
        world.get(eid).memes["joy"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="marked_path", tag="physical", apply=_r_marked_path),
    Rule(name="wander", tag="risk", apply=_r_unmarked_wander),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="explained", tag="social", apply=_r_explained),
    Rule(name="found", tag="resolution", apply=_r_found),
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


def material_fits(place: Place, material: Material) -> bool:
    if material.place_only and place.id not in material.place_only:
        return False
    return material.id in place.offers_materials


def quest_fits(place: Place, quest: Quest) -> bool:
    return quest.id in place.affords_quests


def valid_combo(place: Place, quest: Quest, material: Material) -> bool:
    return quest_fits(place, quest) and material_fits(place, material)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            for material_id, material in MATERIALS.items():
                if valid_combo(place, quest, material):
                    combos.append((place_id, quest_id, material_id))
    return combos


def predicted_safety(place: Place, material: Material, delay: Delay) -> dict:
    visible = material.visible_score
    safe = visible > delay.lost_risk
    return {
        "visible_score": visible,
        "safe": safe,
        "lost_risk": max(0, delay.lost_risk - visible),
    }


def outcome_of(params: "StoryParams") -> str:
    place = _lookup(PLACES, params.place, "place")
    quest = _lookup(QUESTS, params.quest, "quest")
    material = _lookup(MATERIALS, params.material, "material")
    delay = _lookup(DELAYS, params.delay, "delay")
    if not valid_combo(place, quest, material):
        return "invalid"
    pred = predicted_safety(place, material, delay)
    return "smooth" if pred["safe"] else "scared"


def introduce(world: World, leader: Entity, partner: Entity, guide: Entity, quest: Quest) -> None:
    world.say(
        f"{leader.id} and {partner.id} stood at {world.place.entry}, where {world.place.paths} "
        f"and the air felt {world.place.mood}. {guide.label_word.capitalize()} had sent them on a small "
        f"adventure to find {quest.target} before supper."
    )
    world.say(
        f'"Listen for {quest.sound}," {guide.label_word} had said. '
        f'"And stay calm if the path twists."'
    )
    for kid in (leader, partner):
        kid.memes["excitement"] += 1


def clue_and_plan(world: World, leader: Entity, partner: Entity, quest: Quest, material: Material) -> None:
    world.say(
        f"Soon they found the first clue: {quest.clue}. {leader.id} looked down and noticed {material.phrase}."
    )
    if material.id == "shuck":
        world.say(
            f'"I can shuck a few loose pieces and braid them into little ties," {leader.id} said. '
            f'"Then we will know which way is home."'
        )
    else:
        world.say(
            f'"I can use {material.label} to mark our turns," {leader.id} said. '
            f'"Then we will know which way is home."'
        )
    leader.attrs["material_word"] = material.label
    world.facts["plan"] = "mark trail"


def start_marking(world: World, leader: Entity, material: Material) -> None:
    leader.meters["markers"] += 1
    world.get("trail").meters["distance"] += 1
    propagate(world, narrate=False)
    if material.id == "shuck":
        world.say(
            f"{leader.id} looped pale {material.label} around a tall stalk near the first corner."
        )
    else:
        world.say(
            f"{leader.id} left a neat {material.label} mark at the first corner."
        )


def misunderstanding(world: World, partner: Entity, leader: Entity, material: Material, delay: Delay) -> None:
    leader.memes["misunderstood"] += 1
    world.get("trail").meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(delay.line)
    if material.id == "shuck":
        world.say(
            f'{partner.id} stared at the dangling trail tie. '
            f'"You told me not to yank at the corn, and now you are shucking it yourself. '
            f"That is hypocritical!"
        )
    else:
        world.say(
            f'{partner.id} frowned at the new mark. '
            f'"You told me to follow the rules, and now you are making marks everywhere. '
            f'That is hypocritical!"'
        )


def explain(world: World, leader: Entity, partner: Entity, material: Material) -> None:
    leader.memes["explained"] += 1
    propagate(world, narrate=False)
    if material.id == "shuck":
        world.say(
            f'{leader.id} stopped at once. "I am not tearing the field," {leader.pronoun()} said. '
            f'"These are loose corn shucks already on the ground. I am using them like ribbons so we do not get lost."'
        )
    else:
        world.say(
            f'{leader.id} took a breath. "I am not breaking the rules," {leader.pronoun()} said. '
            f'"I am using {material.label} as trail signs so we can find our way back."'
        )
    world.say(
        f"{partner.id}'s face changed. The angry look melted into a worried one, because getting home safely suddenly seemed more important than winning the argument."
    )


def apology(world: World, partner: Entity, leader: Entity) -> None:
    partner.memes["shame"] += 1
    world.say(
        f'"I was wrong," {partner.id} said quietly. "I thought you were being hypocritical, '
        f'but you were trying to protect us."'
    )


def press_on(world: World, leader: Entity, partner: Entity, quest: Quest, material: Material) -> None:
    world.get("trail").meters["distance"] += 1
    leader.meters["markers"] += 1
    propagate(world, narrate=False)
    if material.id == "shuck":
        world.say(
            f"Together they tied one more {material.label} where the path bent, then listened hard."
        )
    else:
        world.say(
            f"Together they added one more clear {material.label} sign where the path bent, then listened hard."
        )
    world.say(
        f"From deeper ahead came {quest.sound}, faint but real."
    )


def worried_branch(world: World, partner: Entity) -> None:
    world.say(
        f"For one fluttery minute the path seemed to fold into itself, and {partner.id} squeezed {partner.pronoun('possessive')} own hands. "
        f"But when {partner.pronoun()} looked back, the trail signs were there, waiting like friendly arrows."
    )


def find_target(world: World, leader: Entity, partner: Entity, quest: Quest) -> None:
    propagate(world, narrate=False)
    target = world.get("target")
    if target.meters["found"] < THRESHOLD:
        target.meters["found"] += 1
    world.say(
        f"They hurried toward the sound and found {quest.target}. {quest.ending_image}"
    )
    world.say(
        f"Then they followed their own marks all the way back, no longer arguing, just walking side by side like real explorers."
    )
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    world.get("trail").meters["home_reached"] += 1


def closing(world: World, guide: Entity, partner: Entity, material: Material) -> None:
    if material.id == "shuck":
        world.say(
            f"At the gate, {guide.label_word} smiled at the braided shuck ties and at {partner.id}'s careful apology. "
            f"The adventure had started with a misunderstanding, but it ended with a wiser team."
        )
    else:
        world.say(
            f"At the gate, {guide.label_word} smiled at the clever trail signs and at {partner.id}'s careful apology. "
            f"The adventure had started with a misunderstanding, but it ended with a wiser team."
        )
def tell(
    quest: Quest,
    material: Material,
    delay: Delay,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
    place=None,
) -> World:
    world = World(place)
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner"))
    guide = world.add(Entity(id="guide", kind="character", type=place.guide_type, label="the guide", role="guide"))
    trail = world.add(Entity(id="trail", type="trail", label="the trail"))
    target = world.add(Entity(id="target", type="target", label=quest.target))
    leader.id = leader_name
    partner.id = partner_name
    guide.id = guide.label_word.capitalize()

    leader.attrs["material"] = material.id
    partner.attrs["material"] = material.id
    leader.meters["markers"] = 0.0
    trail.meters["distance"] = 0.0
    trail.meters["visible_path"] = 0.0
    trail.meters["lost_risk"] = 0.0
    target.meters["found"] = 0.0
    leader.memes["misunderstood"] = 0.0
    leader.memes["explained"] = 0.0
    partner.memes["trust"] = 5.0

    introduce(world, leader, partner, guide, quest)
    world.para()
    clue_and_plan(world, leader, partner, quest, material)
    start_marking(world, leader, material)
    misunderstanding(world, partner, leader, material, delay)
    world.para()
    explain(world, leader, partner, material)
    apology(world, partner, leader)
    press_on(world, leader, partner, quest, material)
    if outcome_of(
        StoryParams(
            place=place.id,
            quest=quest.id,
            material=material.id,
            delay=delay.id,
            leader=leader_name,
            leader_gender=leader_gender,
            partner=partner_name,
            partner_gender=partner_gender,
            seed=None,
        )
    ) == "scared":
        worried_branch(world, partner)
    world.para()
    find_target(world, leader, partner, quest)
    closing(world, guide, partner, material)

    world.facts.update(
        place=place,
        quest=quest,
        material=material,
        delay=delay,
        leader=leader,
        partner=partner,
        guide=guide,
        target=target,
        trail=trail,
        misunderstood=True,
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                quest=quest.id,
                material=material.id,
                delay=delay.id,
                leader=leader_name,
                leader_gender=leader_gender,
                partner=partner_name,
                partner_gender=partner_gender,
                seed=None,
            )
        ),
        used_markers=leader.meters["markers"] >= THRESHOLD,
        found_target=target.meters["found"] >= THRESHOLD,
    )
    return world
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


PLACES = {
    "maze": Place(
        id="maze",
        label="corn maze",
        entry="the tall corn maze",
        paths="golden walls rustled on both sides",
        mood="crackly and brave",
        guide_type="grandfather",
        affords_quests={"gosling", "compass"},
        offers_materials={"shuck", "ribbon"},
        tags={"maze", "farm"},
    ),
    "cave": Place(
        id="cave",
        label="sea cave",
        entry="the mouth of the sea cave",
        paths="stone passages forked like sleepy dragon teeth",
        mood="cool and echoey",
        guide_type="grandmother",
        affords_quests={"shell", "compass"},
        offers_materials={"chalk", "ribbon"},
        tags={"cave", "shore"},
    ),
    "reedbank": Place(
        id="reedbank",
        label="reed path",
        entry="the reed path by the pond",
        paths="green reeds whispered over the narrow trail",
        mood="soft and secret",
        guide_type="mother",
        affords_quests={"gosling", "shell"},
        offers_materials={"ribbon"},
        tags={"pond", "reeds"},
    ),
}

QUESTS = {
    "gosling": Quest(
        id="gosling",
        target="a lost gosling",
        clue="a line of tiny webbed footprints",
        sound="a small worried peep-peep",
        ending_image="It stood in a patch of sun, blinking beside a puddle, and hurried into their arms.",
        tags={"bird", "rescue"},
    ),
    "compass": Quest(
        id="compass",
        target="the brass toy compass Grandpa had dropped",
        clue="a nick in the dirt and one bright button of sunlight",
        sound="the faint clink of metal against stone",
        ending_image="It flashed under a leaf like a hidden star.",
        tags={"compass", "search"},
    ),
    "shell": Quest(
        id="shell",
        target="a moon-white shell for the supper table",
        clue="a trail of silver snail shine",
        sound="the hush and slap of water nearby",
        ending_image="It rested in a pocket of sand, smooth as a little moon.",
        tags={"shell", "search"},
    ),
}

MATERIALS = {
    "shuck": Material(
        id="shuck",
        label="shuck strips",
        phrase="a drift of dry corn shucks at the roots of the stalks",
        verb="tie",
        visible_score=2,
        place_only={"maze"},
        tags={"shuck", "trail"},
    ),
    "chalk": Material(
        id="chalk",
        label="chalk arrows",
        phrase="a stub of blue chalk in a coat pocket",
        verb="draw",
        visible_score=2,
        place_only={"cave"},
        tags={"chalk", "trail"},
    ),
    "ribbon": Material(
        id="ribbon",
        label="ribbon knots",
        phrase="a red ribbon tucked around a wrist",
        verb="knot",
        visible_score=1,
        tags={"ribbon", "trail"},
    ),
}

DELAYS = {
    "quick": Delay(
        id="quick",
        misunderstanding_steps=1,
        lost_risk=0,
        line="But before they had gone three turns, the misunderstanding burst out.",
        tags={"quick"},
    ),
    "lingering": Delay(
        id="lingering",
        misunderstanding_steps=2,
        lost_risk=1,
        line="They tramped on in a tight, unhappy silence until the misunderstanding burst out in the middle of a crooked turn.",
        tags={"lingering", "worry"},
    ),
    "tangled": Delay(
        id="tangled",
        misunderstanding_steps=3,
        lost_risk=2,
        line="They argued for so long at a fork that the wind spun the leaves around their shoes before the misunderstanding finally burst out.",
        tags={"tangled", "worry"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Tess", "Nora", "Ivy", "June", "Wren"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Eli", "Jude", "Theo", "Max"]
@dataclass
class StoryParams:
    place: str
    quest: str
    material: str
    delay: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="maze",
        quest="gosling",
        material="shuck",
        delay="quick",
        leader="Lina",
        leader_gender="girl",
        partner="Owen",
        partner_gender="boy",
        seed=None,
    ),
    StoryParams(
        place="maze",
        quest="compass",
        material="ribbon",
        delay="tangled",
        leader="Finn",
        leader_gender="boy",
        partner="Ivy",
        partner_gender="girl",
        seed=None,
    ),
    StoryParams(
        place="cave",
        quest="shell",
        material="chalk",
        delay="lingering",
        leader="Nora",
        leader_gender="girl",
        partner="Milo",
        partner_gender="boy",
        seed=None,
    ),
    StoryParams(
        place="reedbank",
        quest="gosling",
        material="ribbon",
        delay="quick",
        leader="Theo",
        leader_gender="boy",
        partner="June",
        partner_gender="girl",
        seed=None,
    ),
]


def _lookup(registry: dict, key: str, label: str):
    if key not in registry:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return registry[key]


def explain_rejection(place: Optional[Place], quest: Optional[Quest], material: Optional[Material]) -> str:
    if place and quest and not quest_fits(place, quest):
        return (
            f"(No story: {quest.target} does not fit {place.label}. "
            f"Pick a quest that belongs in that setting.)"
        )
    if place and material and not material_fits(place, material):
        return (
            f"(No story: {material.label} is not a sensible trail material at {place.label}. "
            f"Pick a material that the place actually offers.)"
        )
    return "(No story: that combination does not make a sensible adventure.)"


KNOWLEDGE = {
    "shuck": [
        (
            "What is a shuck?",
            "A shuck is the dry outer covering around an ear of corn. When it comes loose, it can be twisted or braided."
        )
    ],
    "maze": [
        (
            "What is a maze?",
            "A maze is a place with many twisting paths. You have to notice clues so you can find your way through it."
        )
    ],
    "trail": [
        (
            "Why do explorers leave trail markers?",
            "Trail markers help people remember which way they came. They make it easier to return safely instead of getting lost."
        )
    ],
    "hypocritical": [
        (
            "What does hypocritical mean?",
            "Hypocritical means telling someone else to follow a rule while seeming not to follow it yourself. Sometimes it only looks that way because there has been a misunderstanding."
        )
    ],
    "chalk": [
        (
            "Why is chalk useful for marking a path?",
            "Chalk can make clear signs on stone or wood. It is easy to see and can help explorers remember where to turn."
        )
    ],
    "ribbon": [
        (
            "Why can a ribbon help on a trail?",
            "A ribbon can be tied where a path bends. Its bright color helps people notice the right way."
        )
    ],
    "gosling": [
        (
            "What is a gosling?",
            "A gosling is a baby goose. It is small, fluffy, and often peeps for its family."
        )
    ],
    "compass": [
        (
            "What does a compass help you do?",
            "A compass helps you know direction, like north and south. Explorers use it so they can travel without wandering the wrong way."
        )
    ],
    "shell": [
        (
            "Why do shells wash up near water?",
            "Shells come from animals that lived in water. Waves can carry the empty shells onto sand or stones."
        )
    ],
}
KNOWLEDGE_ORDER = ["shuck", "maze", "trail", "hypocritical", "chalk", "ribbon", "gosling", "compass", "shell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    quest = f["quest"]
    material = f["material"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "shuck" and "hypocritical" and turns on a misunderstanding.',
        f"Tell a child-friendly adventure where {leader.id} and {partner.id} search for {quest.target} in {place.label}, and one child mistakes a careful trail-marking plan for rule-breaking.",
        f"Write a simple adventure about a misunderstanding: a child sees {material.label} being used on the trail, says it is hypocritical, then learns the signs were meant to help everyone get home safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    guide = f["guide"]
    place = f["place"]
    quest = f["quest"]
    material = f["material"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children on a small adventure in {place.label}. {guide.label_word.capitalize()} sends them to look for {quest.target}."
        ),
        (
            "What was their adventure?",
            f"They had to follow clues and twisting paths to find {quest.target}. The journey felt exciting because the place was full of turns and sounds to notice."
        ),
        (
            f"Why did {leader.id} use {material.label}?",
            f"{leader.id} used {material.label} to mark the path. That way, they could remember the safe way home after each turn."
        ),
        (
            f"Why did {partner.id} call {leader.id} hypocritical?",
            f"{partner.id} thought {leader.id} was breaking the same rule {leader.pronoun('subject')} had just talked about. It looked unfair, but the angry word came from a misunderstanding, not from the real plan."
        ),
        (
            "What was the misunderstanding really about?",
            f"The misunderstanding was about the trail markers. {leader.id} was not making trouble; {leader.pronoun('subject')} was trying to keep them from getting lost."
        ),
    ]
    if outcome == "scared":
        qa.append(
            (
                "Did the misunderstanding make the adventure harder?",
                f"Yes. Their argument delayed them long enough for the path to feel confusing for a moment. But the trail signs still helped them steady themselves and keep going."
            )
        )
    else:
        qa.append(
            (
                "How was the problem solved?",
                f"{leader.id} explained the trail-marking plan, and {partner.id} understood and apologized. Once they trusted each other again, they could keep exploring together."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They found {quest.target} and followed their own signs back home. The ending shows that they became a better team after clearing up the misunderstanding."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"trail", "hypocritical"}
    tags |= set(f["place"].tags)
    tags |= set(f["quest"].tags)
    tags |= set(f["material"].tags)
    if f["material"].id == "shuck":
        tags.add("shuck")
    if f["place"].id == "maze":
        tags.add("maze")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_fits(P,Q) :- place(P), quest(Q), affords(P,Q).
material_fits(P,M) :- place(P), material(M), offers(P,M), not place_block(M,P).
valid(P,Q,M) :- quest_fits(P,Q), material_fits(P,M).

smooth(P,M,D) :- valid(P,_,M), visible(M,V), lost_risk(D,R), V > R.
scared(P,M,D) :- valid(P,_,M), visible(M,V), lost_risk(D,R), V <= R.

outcome(smooth) :- chosen_place(P), chosen_quest(Q), chosen_material(M), chosen_delay(D), valid(P,Q,M), smooth(P,M,D).
outcome(scared) :- chosen_place(P), chosen_quest(Q), chosen_material(M), chosen_delay(D), valid(P,Q,M), scared(P,M,D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(place.affords_quests):
            lines.append(asp.fact("affords", pid, q))
        for m in sorted(place.offers_materials):
            lines.append(asp.fact("offers", pid, m))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for mid, mat in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("visible", mid, mat.visible_score))
        for pid in PLACES:
            if mat.place_only and pid not in mat.place_only:
                lines.append(asp.fact("place_block", mid, pid))
    for did, delay in DELAYS.items():
        lines.append(asp.fact("delay", did))
        lines.append(asp.fact("lost_risk", did, delay.lost_risk))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_quest", params.quest),
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for s in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure misunderstanding with trail markers. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--delay", choices=DELAYS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    quest = QUESTS.get(args.quest) if args.quest else None
    material = MATERIALS.get(args.material) if args.material else None

    if args.place and place is None:
        raise StoryError(f"(No story: unknown place '{args.place}'.)")
    if args.quest and quest is None:
        raise StoryError(f"(No story: unknown quest '{args.quest}'.)")
    if args.material and material is None:
        raise StoryError(f"(No story: unknown material '{args.material}'.)")

    if place and quest and not quest_fits(place, quest):
        raise StoryError(explain_rejection(place, quest, material))
    if place and material and not material_fits(place, material):
        raise StoryError(explain_rejection(place, quest, material))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.quest is None or combo[1] == args.quest)
        and (args.material is None or combo[2] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, quest_id, material_id = rng.choice(sorted(combos))
    delay_id = args.delay or rng.choice(sorted(DELAYS))
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=leader_name)
    return StoryParams(
        place=place_id,
        quest=quest_id,
        material=material_id,
        delay=delay_id,
        leader=leader_name,
        leader_gender=leader_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    place = _lookup(PLACES, params.place, "place")
    quest = _lookup(QUESTS, params.quest, "quest")
    material = _lookup(MATERIALS, params.material, "material")
    delay = _lookup(DELAYS, params.delay, "delay")
    if not valid_combo(place, quest, material):
        raise StoryError(explain_rejection(place, quest, material))

    world = tell(
        place=place,
        quest=quest,
        material=material,
        delay=delay,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, material) combos:\n")
        for place, quest, material in combos:
            print(f"  {place:8} {quest:8} {material}")
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
            header = f"### {p.leader} & {p.partner}: {p.place}/{p.quest}/{p.material} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
