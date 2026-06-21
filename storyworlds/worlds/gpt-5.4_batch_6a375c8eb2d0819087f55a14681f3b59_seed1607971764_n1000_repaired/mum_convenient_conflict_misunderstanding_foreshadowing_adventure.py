#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mum_convenient_conflict_misunderstanding_foreshadowing_adventure.py

A standalone story world about a child who thinks mum has made an adventure too
small and convenient, only to discover that the changed route was a careful
choice. The world models conflict, misunderstanding, and foreshadowing through
state: a hinted hazard, a mistaken complaint, a revealing turn, and a safe
adventure ending.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mum", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)
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
    trail: str
    treasure_spot: str
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
class Hazard:
    id: str
    label: str
    hint: str
    reveal: str
    danger: str
    blocks: str
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
class Detour:
    id: str
    label: str
    route_text: str
    bypasses: set[str] = field(default_factory=set)
    sense: int = 2
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
class Treasure:
    id: str
    label: str
    image: str
    prize_text: str
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


def _r_hint_raises_tension(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.get("hazard")
    if hazard.meters["hint_seen"] >= THRESHOLD:
        for eid in ("hero", "mum", "companion"):
            ent = world.get(eid)
            sig = ("tension", eid)
            if sig in world.fired:
                continue
            if ent.role == "mum":
                ent.memes["worry"] += 1
            else:
                ent.memes["tension"] += 1
            world.fired.add(sig)
    return out


def _r_reveal_creates_understanding(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.get("hazard")
    hero = world.get("hero")
    if hazard.meters["revealed"] >= THRESHOLD and ("understand", hero.id) not in world.fired:
        world.fired.add(("understand", hero.id))
        hero.memes["understanding"] += 1
        hero.memes["anger"] = 0.0
        hero.memes["trust"] += 2
    return out


def _r_treasure_clears_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["found_treasure"] >= THRESHOLD and ("settled", hero.id) not in world.fired:
        world.fired.add(("settled", hero.id))
        hero.memes["joy"] += 1
        hero.memes["conflict"] = 0.0
        world.get("companion").memes["joy"] += 1
        world.get("mum").memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hint_tension", tag="emotion", apply=_r_hint_raises_tension),
    Rule(name="reveal_understanding", tag="emotion", apply=_r_reveal_creates_understanding),
    Rule(name="treasure_resolution", tag="emotion", apply=_r_treasure_clears_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in []):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def detour_works(setting: Setting, hazard: Hazard, detour: Detour) -> bool:
    return hazard.id in setting.affords and hazard.id in detour.bypasses and detour.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hazard_id, hazard in HAZARDS.items():
            if hazard_id not in setting.affords:
                continue
            for detour_id, detour in DETOURS.items():
                if not detour_works(setting, hazard, detour):
                    continue
                for treasure_id in TREASURES:
                    combos.append((setting_id, hazard_id, detour_id, treasure_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "guided" if params.trust >= 6 else "proof"


def foreshadow(world: World, hero: Entity, companion: Entity, hazard: Hazard) -> None:
    world.get("hazard").meters["hint_seen"] = 1.0
    propagate(world, narrate=False)
    hero.memes["curiosity"] += 1
    companion.memes["caution"] += 1
    world.say(
        f"{hero.id} and {companion.id} set out like explorers, following paper arrows through "
        f"{world.setting.place}. Ahead, {hazard.hint}"
    )


def introduce(world: World, hero: Entity, companion: Entity, treasure: Treasure) -> None:
    world.say(
        f"That morning, {hero.id} had a map with a star drawn at {world.setting.treasure_spot}. "
        f"If the clues were right, the explorers would find {treasure.prize_text}."
    )
    world.say(
        f"{companion.id} tucked the last clue into a pocket and promised to keep watch for hidden signs."
    )


def mum_changes_route(world: World, mum: Entity, detour: Detour) -> None:
    world.say(
        f"But by the gate, one arrow had been turned. It no longer pointed to the usual shortcut. "
        f"It pointed along {detour.route_text}."
    )
    world.say(
        f'"I changed that one," said {mum.label_word}. "Today we are taking {detour.label}."'
    )


def complain(world: World, hero: Entity, mum: Entity, detour: Detour) -> None:
    hero.memes["anger"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f'{hero.id} stopped short. "That route is too convenient," {hero.pronoun()} said. '
        f'"It cuts the adventure small. You moved the arrow because you do not want us to have a real quest."'
    )
    world.say(
        f"{mum.label_word.capitalize()} looked surprised, and for a moment nobody stepped forward."
    )


def companion_misreads(world: World, companion: Entity, mum: Entity) -> None:
    companion.memes["misunderstanding"] += 1
    world.say(
        f'{companion.id} whispered, "Maybe {mum.label_word} thinks we cannot do hard things." '
        f"That made the misunderstanding feel even bigger."
    )


def mum_warns(world: World, mum: Entity, hazard: Hazard, detour: Detour) -> None:
    mum.memes["care"] += 1
    world.say(
        f'"I am not shrinking the adventure," {mum.label_word} said. "I am choosing {detour.label} because '
        f'{hazard.danger}."'
    )


def guided_choice(world: World, hero: Entity, companion: Entity, mum: Entity, detour: Detour) -> None:
    hero.memes["hesitation"] += 1
    world.say(
        f"{hero.id} still frowned, but {hero.pronoun()} trusted {mum.label_word}'s voice enough to listen."
    )
    world.say(
        f"Together they followed {detour.route_text}. The path felt longer, but it also felt steady under their shoes."
    )


def proof_choice(world: World, hero: Entity, companion: Entity, mum: Entity, hazard: Hazard) -> None:
    hero.memes["defiance"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} marched toward {hazard.blocks} to prove the old route was better, and {companion.id} hurried after."
    )
    world.say(
        f"{mum.label_word.capitalize()} followed close behind without shouting, ready to stop them if the danger turned real."
    )


def reveal_hazard(world: World, hero: Entity, companion: Entity, mum: Entity, hazard: Hazard, detour: Detour) -> None:
    world.get("hazard").meters["revealed"] = 1.0
    propagate(world, narrate=False)
    world.say(hazard.reveal)
    world.say(
        f'{hero.id} stared. "Oh," {hero.pronoun()} said softly. "You changed the arrow because {hazard.danger}."'
    )
    companion.memes["understanding"] += 1
    world.say(
        f'{mum.label_word.capitalize()} nodded. "A good adventure is still brave when it goes the safe way."'
    )
    world.say(
        f"So they turned and took {detour.label} instead."
    )


def reach_treasure(world: World, hero: Entity, companion: Entity, mum: Entity, treasure: Treasure) -> None:
    hero.meters["found_treasure"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {world.setting.treasure_spot}, where {treasure.image}."
    )
    world.say(
        f"{hero.id} laughed first, then {companion.id}, and even {mum.label_word} joined in as "
        f"they lifted {treasure.prize_text} together."
    )


def ending(world: World, hero: Entity, mum: Entity, detour: Detour, treasure: Treasure) -> None:
    world.say(
        f'{hero.id} touched the map again. "Next time," {hero.pronoun()} said, "I will ask before I decide you made '
        f"the path too convenient."
    )
    world.say(
        f'{mum.label_word.capitalize()} squeezed {hero.pronoun("possessive")} shoulder. "Next time," '
        f'{mum.pronoun()} said, "we will plan another route together."'
    )
    world.say(
        f"They marched home feeling as if the world had grown larger, not smaller, because now they knew how to spot danger "
        f"and still keep the adventure."
    )
def tell(
    hazard: Hazard,
    detour: Detour,
    treasure: Treasure,
    hero_name: str,
    hero_type: HeroType,
    companion_name: str,
    companion_type: CompanionType,
    parent_type: ParentType,
    trust: Trust,
    setting=None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    companion = world.add(Entity(id="companion", kind="character", type=companion_type, label=companion_name, role="companion"))
    mum = world.add(Entity(id="mum", kind="character", type=parent_type, label="mum", role="mum"))
    world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label, role="hazard"))
    world.add(Entity(id="treasure", kind="thing", type="treasure", label=treasure.label, role="treasure"))

    hero.attrs["display"] = hero_name
    companion.attrs["display"] = companion_name
    mum.attrs["display"] = mum.label_word

    hero.memes["trust"] = float(trust)
    hero.memes["anger"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["understanding"] = 0.0
    hero.memes["joy"] = 0.0
    companion.memes["caution"] = 0.0
    companion.memes["misunderstanding"] = 0.0
    companion.memes["understanding"] = 0.0
    mum.memes["care"] = 0.0
    mum.memes["worry"] = 0.0
    mum.memes["relief"] = 0.0

    world.facts.update(
        hero=hero,
        companion=companion,
        mum=mum,
        setting=setting,
        hazard_cfg=hazard,
        detour=detour,
        treasure_cfg=treasure,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            hazard=hazard.id,
            detour=detour.id,
            treasure=treasure.id,
            hero_name=hero_name,
            hero_gender=hero_type,
            companion_name=companion_name,
            companion_gender=companion_type,
            parent=parent_type,
            trust=trust,
        )),
    )

    introduce(world, hero, companion, treasure)
    foreshadow(world, hero, companion, hazard)

    world.para()
    mum_changes_route(world, mum, detour)
    complain(world, hero, mum, detour)
    companion_misreads(world, companion, mum)
    mum_warns(world, mum, hazard, detour)

    world.para()
    if trust >= 6:
        guided_choice(world, hero, companion, mum, detour)
        reveal_hazard(world, hero, companion, mum, hazard, detour)
    else:
        proof_choice(world, hero, companion, mum, hazard)
        reveal_hazard(world, hero, companion, mum, hazard, detour)

    world.para()
    reach_treasure(world, hero, companion, mum, treasure)
    ending(world, hero, mum, detour, treasure)

    world.facts.update(
        misunderstanding=True,
        conflict=True,
        foreshadowed=True,
        trust=trust,
        learned=hero.memes["understanding"] >= THRESHOLD,
        found_treasure=hero.meters["found_treasure"] >= THRESHOLD,
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


SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the back garden behind the shed",
        trail="the garden trail",
        treasure_spot="the old apple tree",
        affords={"bridge", "geese", "thorns"},
        tags={"garden", "adventure"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard path beyond the fence",
        trail="the orchard trail",
        treasure_spot="the mossy stump",
        affords={"bridge", "thorns"},
        tags={"orchard", "adventure"},
    ),
    "dunes": Setting(
        id="dunes",
        place="the sandy dunes by the path",
        trail="the dune trail",
        treasure_spot="the driftwood arch",
        affords={"geese", "thorns"},
        tags={"sand", "adventure"},
    ),
}

HAZARDS = {
    "bridge": Hazard(
        id="bridge",
        label="wobbly plank bridge",
        hint="a thin wooden bridge gave a tiny creak each time the wind pressed it.",
        reveal="When they came close, the old plank bridge dipped hard in the middle, and one board cracked with a sharp snap.",
        danger="the old bridge was loose and could throw someone into the ditch",
        blocks="the little bridge",
        tags={"bridge", "safety"},
    ),
    "geese": Hazard(
        id="geese",
        label="goose nest",
        hint="from the reeds came a low, grumpy honk that did not sound friendly at all.",
        reveal="Near the reeds, a mother goose rose up with her wings wide, hissing over a hidden nest.",
        danger="a nesting goose was guarding the shortcut and could chase small explorers",
        blocks="the reeds by the shortcut",
        tags={"geese", "animals"},
    ),
    "thorns": Hazard(
        id="thorns",
        label="thorn patch",
        hint="brambles along the hedge twitched, and shiny thorns caught the light like tiny hooks.",
        reveal="At the hedge they saw that the narrow gap had filled with fresh brambles, all hooked with hard thorns.",
        danger="the hedge gap was choked with thorns that could scratch hands and faces",
        blocks="the hedge gap",
        tags={"thorns", "plants"},
    ),
}

DETOURS = {
    "stone_steps": Detour(
        id="stone_steps",
        label="the stepping-stone way",
        route_text="the stepping-stone way beside the beans",
        bypasses={"bridge", "geese"},
        sense=3,
        tags={"path", "stones"},
    ),
    "hill_path": Detour(
        id="hill_path",
        label="the hill path",
        route_text="the long hill path above the ditch",
        bypasses={"bridge", "thorns"},
        sense=3,
        tags={"path", "hill"},
    ),
    "gate_path": Detour(
        id="gate_path",
        label="the gate path",
        route_text="the wide gate path around the reeds",
        bypasses={"geese", "thorns"},
        sense=3,
        tags={"path", "gate"},
    ),
    "mud_cut": Detour(
        id="mud_cut",
        label="the muddy cut-through",
        route_text="the muddy cut-through behind the bins",
        bypasses={"bridge"},
        sense=1,
        tags={"mud"},
    ),
}

TREASURES = {
    "flag": Treasure(
        id="flag",
        label="bright flag",
        image="a bright red flag fluttered from a stick, tied above a biscuit tin",
        prize_text="the biscuit tin of explorer badges",
        tags={"flag", "treasure"},
    ),
    "lantern": Treasure(
        id="lantern",
        label="tin lantern",
        image="a tin lantern waited there with yellow paper stars glued all over it",
        prize_text="the little lantern and the note hidden beneath it",
        tags={"lantern", "treasure"},
    ),
    "shell_box": Treasure(
        id="shell_box",
        label="shell box",
        image="a wooden box painted with blue shells shone in a patch of sun",
        prize_text="the shell box full of smooth glass pebbles",
        tags={"shells", "treasure"},
    ),
}

GIRL_NAMES = ["Tara", "Mia", "Nora", "Zoe", "Lila", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Owen", "Eli"]


KNOWLEDGE = {
    "bridge": [
        (
            "Why can an old wooden bridge be dangerous?",
            "Old wooden boards can loosen or crack, so they may wobble or break under your feet. That is why a grown-up may choose a different path."
        )
    ],
    "geese": [
        (
            "Why should you stay away from a goose nest?",
            "A parent goose may hiss, flap, or chase if it thinks its nest is in danger. Giving wild animals space is the safe and kind thing to do."
        )
    ],
    "thorns": [
        (
            "What can thorns do?",
            "Thorns are sharp parts of some plants that can scratch skin or catch on clothes. They help protect the plant, so it is best not to push through them."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where to go and helps you follow a route. On an adventure, it can turn a walk into a quest."
        )
    ],
    "detour": [
        (
            "What is a detour?",
            "A detour is a different way to go when the usual route is blocked or unsafe. It can take longer, but it helps people get somewhere safely."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses the wrong reason for what another person did. Talking and checking the facts can clear it up."
        )
    ],
}
KNOWLEDGE_ORDER = ["map", "detour", "bridge", "geese", "thorns", "misunderstanding"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    hazard = f["hazard_cfg"]
    detour = f["detour"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "mum" and the word "convenient".',
        f"Tell a short adventure where {hero.attrs['display']} thinks mum changed the route to make the quest too convenient, but the real reason has to do with {hazard.label}.",
        f"Write a story with foreshadowing, conflict, and a misunderstanding, where {hero.attrs['display']} and {companion.attrs['display']} reach treasure safely by taking {detour.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    mum = f["mum"]
    hazard = f["hazard_cfg"]
    detour = f["detour"]
    treasure = f["treasure_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['display']}, {companion.attrs['display']}, and their mum on a small adventure. They are following clues toward {world.setting.treasure_spot}."
        ),
        (
            "What was the misunderstanding?",
            f"{hero.attrs['display']} thought mum changed the arrow only to make the journey too convenient and less exciting. That guess was wrong, because mum had changed it to lead them away from {hazard.label}."
        ),
        (
            "What was the foreshadowing at the beginning?",
            f"The story hinted at danger before the children understood it: {hazard.hint} That early clue prepared the reader for the later reveal."
        ),
        (
            "Why did mum choose the detour?",
            f"Mum chose {detour.label} because {hazard.danger}. She was not trying to spoil the quest; she was protecting the explorers while still letting them reach the treasure."
        ),
    ]
    if outcome == "guided":
        qa.append(
            (
                f"Did {hero.attrs['display']} trust mum right away?",
                f"{hero.attrs['display']} still felt upset, but listened before the danger was right in front of them. That trust let the argument soften before anyone got too close to the unsafe spot."
            )
        )
    else:
        qa.append(
            (
                f"What changed {hero.attrs['display']}'s mind?",
                f"{hero.attrs['display']} went close enough to see the danger for real, and then understood mum's reason. Seeing {hazard.label} made the misunderstanding fall apart."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They reached {world.setting.treasure_spot} and found {treasure.prize_text}. The ending proves the adventure stayed exciting even after they chose the safer route."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"map", "detour", "misunderstanding"} | set(f["hazard_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    hazard: str
    detour: str
    treasure: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
    parent: str
    trust: int = 5
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="backyard",
        hazard="bridge",
        detour="hill_path",
        treasure="flag",
        hero_name="Tara",
        hero_gender="girl",
        companion_name="Ben",
        companion_gender="boy",
        parent="mother",
        trust=4,
    ),
    StoryParams(
        setting="orchard",
        hazard="thorns",
        detour="gate_path",
        treasure="shell_box",
        hero_name="Max",
        hero_gender="boy",
        companion_name="Nora",
        companion_gender="girl",
        parent="mother",
        trust=7,
    ),
    StoryParams(
        setting="dunes",
        hazard="geese",
        detour="stone_steps",
        treasure="lantern",
        hero_name="Mia",
        hero_gender="girl",
        companion_name="Leo",
        companion_gender="boy",
        parent="mother",
        trust=3,
    ),
    StoryParams(
        setting="backyard",
        hazard="geese",
        detour="gate_path",
        treasure="shell_box",
        hero_name="Anna",
        hero_gender="girl",
        companion_name="Finn",
        companion_gender="boy",
        parent="mother",
        trust=8,
    ),
]


def explain_rejection(setting: Setting, hazard: Hazard, detour: Detour) -> str:
    if hazard.id not in setting.affords:
        return (
            f"(No story: {setting.place.capitalize()} does not contain the right kind of danger for {hazard.label}, "
            f"so mum would have no honest reason to redirect the route there.)"
        )
    if hazard.id not in detour.bypasses:
        return (
            f"(No story: {detour.label} does not actually bypass {hazard.label}. "
            f"The detour must solve the danger, not just sound adventurous.)"
        )
    if detour.sense < 2:
        return (
            f"(No story: {detour.label} is not a sensible route for a careful mum. "
            f"Pick a more reliable path.)"
        )
    return "(No story: this route does not make sense.)"


ASP_RULES = r"""
hazard_in(S, H) :- setting(S), hazard(H), affords(S, H).
sensible_detour(D) :- detour(D), sense(D, V), V >= 2.
works(S, H, D) :- hazard_in(S, H), bypasses(D, H), sensible_detour(D).
valid(S, H, D, T) :- works(S, H, D), treasure(T).

guided :- trust(V), V >= 6.
proof  :- trust(V), V < 6.
outcome(guided) :- guided.
outcome(proof)  :- proof.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for did, detour in DETOURS.items():
        lines.append(asp.fact("detour", did))
        lines.append(asp.fact("sense", did, detour.sense))
        for hid in sorted(detour.bypasses):
            lines.append(asp.fact("bypasses", did, hid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trust", params.trust)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} cases.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        smoke = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
            _ = buf.getvalue()
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child mistakes mum's careful detour for a boring shortcut."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--detour", choices=DETOURS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.detour:
        setting = SETTINGS[args.setting]
        hazard = HAZARDS[args.hazard]
        detour = DETOURS[args.detour]
        if not detour_works(setting, hazard, detour):
            raise StoryError(explain_rejection(setting, hazard, detour))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.detour is None or c[2] == args.detour)
        and (args.treasure is None or c[3] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, detour_id, treasure_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    companion_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    companion_name = args.companion_name or _pick_name(rng, companion_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trust = args.trust if args.trust is not None else rng.randint(2, 8)
    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        detour=detour_id,
        treasure=treasure_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        parent=parent,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        hazard = HAZARDS[params.hazard]
        detour = DETOURS[params.detour]
        treasure = TREASURES[params.treasure]
    except KeyError as err:
        raise StoryError(f"(Invalid story option: {err.args[0]})") from None

    if not detour_works(setting, hazard, detour):
        raise StoryError(explain_rejection(setting, hazard, detour))

    world = tell(
        setting=setting,
        hazard=hazard,
        detour=detour,
        treasure=treasure,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        companion_name=params.companion_name,
        companion_type=params.companion_gender,
        parent_type=params.parent,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("companion", params.companion_name),
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hazard, detour, treasure) combos:\n")
        for setting, hazard, detour, treasure in combos:
            print(f"  {setting:9} {hazard:7} {detour:11} {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.hazard} via {p.detour} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
