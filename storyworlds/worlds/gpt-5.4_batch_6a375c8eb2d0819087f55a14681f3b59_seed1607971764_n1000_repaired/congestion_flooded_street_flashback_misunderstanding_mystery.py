#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/congestion_flooded_street_flashback_misunderstanding_mystery.py

A standalone storyworld about a small mystery on a flooded street: traffic slows
into congestion, something important goes missing near the water, a child
misreads another person's actions, and a flashback helps solve the puzzle.

The world model tracks:
- physical meters: wetness, drift, trapped, recovered
- emotional memes: worry, suspicion, relief, trust

A reasonableness gate keeps only combinations where:
- the flood can plausibly move the missing item to the chosen place
- the chosen recovery method can actually reach and lift it there

The story always includes:
- a flooded street
- the word "congestion"
- a misunderstanding
- a flashback
- a mystery-shaped resolution
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
    buoyant: bool = False
    waterproof: bool = False
    reachable_depth: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class LostItem:
    id: str
    label: str
    phrase: str
    article: str
    buoyant: bool
    precious: str
    clue: str
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
class Place:
    id: str
    label: str
    phrase: str
    depth: int
    traps_floaters: bool
    traps_sinkers: bool
    image: str
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
    reach: int
    lifts: bool
    text: str
    qa_text: str
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
class SuspectRole:
    id: str
    label: str
    action: str
    innocent_goal: str
    reveal: str
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


def _r_flood_moves_item(world: World) -> list[str]:
    item = world.get("item")
    place = world.get("place")
    if item.meters["in_water"] < THRESHOLD:
        return []
    if item.meters["trapped"] >= THRESHOLD:
        return []
    sig = ("moved", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["drift"] += 1
    item.meters["trapped"] += 1
    place.meters["holding"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return ["__drift__"]


def _r_recovery_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    suspect = world.get("suspect")
    hero.memes["relief"] += 1
    hero.memes["suspicion"] = 0.0
    hero.memes["trust"] += 1
    suspect.memes["relief"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="flood_moves_item", tag="physical", apply=_r_flood_moves_item),
    Rule(name="recovery_relief", tag="emotional", apply=_r_recovery_relief),
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


def can_trap(item: LostItem, place: Place) -> bool:
    return (item.buoyant and place.traps_floaters) or ((not item.buoyant) and place.traps_sinkers)


def tool_fits(place: Place, tool: Tool) -> bool:
    return tool.lifts and tool.reach >= place.depth


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for place_id, place in PLACES.items():
            if can_trap(item, place):
                combos.append((item_id, place_id))
    return combos


def predict_loss(item: LostItem, place: Place) -> dict:
    return {
        "drifts": can_trap(item, place),
        "depth": place.depth,
    }


def _do_loss(world: World) -> None:
    item = world.get("item")
    item.meters["in_water"] += 1
    item.meters["wet"] += 1
    propagate(world, narrate=False)


def opening(world: World, hero: Entity, parent: Entity, item_cfg: LostItem) -> None:
    hero.memes["care"] += 1
    world.say(
        f"The rain had stopped, but the street still looked like a long gray river. "
        f"Cars edged forward in tired congestion while {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} picked their way along the flooded curb."
    )
    world.say(
        f"In {hero.id}'s hand was {item_cfg.phrase}, {item_cfg.precious}. "
        f"{hero.pronoun().capitalize()} kept checking that it was still there."
    )


def hint_and_drop(world: World, hero: Entity, item_cfg: LostItem, place_cfg: Place) -> None:
    pred = predict_loss(item_cfg, place_cfg)
    world.facts["predicted_drifts"] = pred["drifts"]
    world.facts["predicted_depth"] = pred["depth"]
    hero.memes["worry"] += 1
    world.say(
        f"A bus rolled past and pushed a shivering wave over the curb. {hero.id} hopped back, "
        f"but in that splashy bump, {item_cfg.article} slipped from {hero.pronoun('possessive')} fingers."
    )
    _do_loss(world)
    world.say(
        f"It vanished into the rushing water. All {hero.id} could see was {place_cfg.image}."
    )
    world.say(
        f'"My {item_cfg.label}!" {hero.id} whispered. The flooded street suddenly felt like a puzzle.'
    )


def suspicious_sighting(world: World, hero: Entity, suspect: Entity, role_cfg: SuspectRole, place_cfg: Place) -> None:
    hero.memes["suspicion"] += 1
    suspect.memes["focus"] += 1
    world.say(
        f"Then {hero.id} saw {suspect.id}, the {role_cfg.label}, {role_cfg.action} beside {place_cfg.phrase}. "
        f"In the wobbling water, it looked secret and sneaky."
    )
    world.say(
        f"{hero.id}'s heart thumped. Maybe {suspect.id} had seen the missing thing first. "
        f"Maybe {suspect.pronoun()} had taken it."
    )


def accuse(world: World, hero: Entity, suspect: Entity, item_cfg: LostItem) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'{hero.id} hurried closer. "Did you take my {item_cfg.label}?" {hero.pronoun()} asked.'
    )
    world.say(
        f"For one tight moment, the little mystery seemed solved in the worst possible way."
    )


def misunderstanding(world: World, suspect: Entity, role_cfg: SuspectRole) -> None:
    suspect.memes["surprise"] += 1
    world.say(
        f'{suspect.id} blinked. "No," {suspect.pronoun()} said. "{role_cfg.innocent_goal}."'
    )
    world.say(
        f"But the answer came so quickly that {hero_name(world).lower()} was not sure whether to believe it."
    )


def flashback(world: World, hero: Entity, item_cfg: LostItem, place_cfg: Place) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Just then, a bright little flashback flickered through {hero.id}'s mind: "
        f"{item_cfg.clue}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered the splash, the twist of water, and the way it rushed toward {place_cfg.phrase}. "
        f"The mystery did not point to a thief anymore. It pointed to the flood."
    )


def search_together(world: World, hero: Entity, suspect: Entity, tool_cfg: Tool, place_cfg: Place) -> None:
    hero.memes["hope"] += 1
    suspect.memes["kindness"] += 1
    world.say(
        f'"Then maybe it drifted there," {hero.id} said softly. {suspect.id} nodded and reached for {tool_cfg.phrase}.'
    )
    world.say(
        f"Together they peered into the brown water by {place_cfg.phrase}, looking for one small sign."
    )


def recover(world: World, suspect: Entity, tool_cfg: Tool, item_cfg: LostItem, place_cfg: Place) -> None:
    item = world.get("item")
    item.meters["recovered"] += 1
    world.facts["recovery_place"] = place_cfg.label
    world.facts["recovery_tool"] = tool_cfg.label
    world.facts["misunderstanding_cleared"] = True
    propagate(world, narrate=False)
    world.say(
        f"At last {suspect.id} {tool_cfg.text}, and up came {item_cfg.article} from the water."
    )
    world.say(
        f"It was wet, but safe. The answer to the mystery had been hiding exactly where the flood had carried it."
    )


def apology(world: World, hero: Entity, suspect: Entity, role_cfg: SuspectRole) -> None:
    hero.memes["shame"] += 1
    world.say(
        f'{hero.id} felt {hero.pronoun("possessive")} cheeks grow warm. "I thought you were hiding something," '
        f'{hero.pronoun()} admitted.'
    )
    world.say(
        f'{suspect.id} smiled and shook {suspect.pronoun("possessive")} head. "{role_cfg.reveal}," {suspect.pronoun()} said.'
    )


def ending(world: World, hero: Entity, parent: Entity, item_cfg: LostItem) -> None:
    world.say(
        f"{hero.id}'s {parent.label_word} squeezed {hero.pronoun('possessive')} shoulder. "
        f'"A flooded street can make things look strange," {parent.pronoun()} said.'
    )
    world.say(
        f"As the line of cars crawled on through the congestion, {hero.id} held {item_cfg.article} close. "
        f"The water still swirled and whispered, but the mystery was over, and the street no longer felt full of suspects."
    )


def hero_name(world: World) -> str:
    return world.get("hero").id


def tell(
    item_cfg: LostItem,
    place_cfg: Place,
    tool_cfg: Tool,
    role_cfg: SuspectRole,
    *,
    hero_name_value: str = "Mina",
    hero_type: str = "girl",
    suspect_name: str = "Mr. Vale",
    suspect_type: str = "man",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name_value, kind="character", type=hero_type, role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_type, role="suspect"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            buoyant=item_cfg.buoyant,
            waterproof=False,
        )
    )
    place = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place_cfg.label,
            reachable_depth=place_cfg.depth,
        )
    )

    world.facts.update(
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        tool_cfg=tool_cfg,
        role_cfg=role_cfg,
        hero=hero,
        parent=parent,
        suspect=suspect,
        item=item,
        place=place,
        misunderstanding_cleared=False,
    )

    opening(world, hero, parent, item_cfg)
    hint_and_drop(world, hero, item_cfg, place_cfg)

    world.para()
    suspicious_sighting(world, hero, suspect, role_cfg, place_cfg)
    accuse(world, hero, suspect, item_cfg)
    misunderstanding(world, suspect, role_cfg)

    world.para()
    flashback(world, hero, item_cfg, place_cfg)
    search_together(world, hero, suspect, tool_cfg, place_cfg)
    recover(world, suspect, tool_cfg, item_cfg, place_cfg)

    world.para()
    apology(world, hero, suspect, role_cfg)
    ending(world, hero, parent, item_cfg)
    return world


ITEMS = {
    "key_tin": LostItem(
        id="key_tin",
        label="key tin",
        phrase="a tiny blue key tin for the apartment mailbox",
        article="the tiny blue tin",
        buoyant=False,
        precious="because the family needed it to open the mailbox",
        clue="a moment ago, before the bus wave, the tiny blue tin had knocked once against the curb and tipped toward the storm-drain bars",
        tags={"key", "mailbox", "flood"},
    ),
    "note_bottle": LostItem(
        id="note_bottle",
        label="note bottle",
        phrase="a little corked bottle with a folded note inside",
        article="the little bottle",
        buoyant=True,
        precious="because it held a note from Grandpa",
        clue="the little bottle had bobbed once like a toy boat and then spun toward the blocked curb corner",
        tags={"bottle", "note", "flood"},
    ),
    "silver_badge": LostItem(
        id="silver_badge",
        label="silver badge",
        phrase="a small silver badge from the school fair",
        article="the silver badge",
        buoyant=False,
        precious="because it was the prize {hero} had won that morning".replace("{hero}", "the child"),
        clue="the silver badge had flashed in the water for one second before slipping under beside the drain",
        tags={"badge", "school", "flood"},
    ),
}

PLACES = {
    "storm_drain": Place(
        id="storm_drain",
        label="storm drain",
        phrase="the storm drain",
        depth=2,
        traps_floaters=False,
        traps_sinkers=True,
        image="the dark bars of the storm drain under a skin of rippling water",
        tags={"drain"},
    ),
    "blocked_curb": Place(
        id="blocked_curb",
        label="blocked curb",
        phrase="the blocked curb",
        depth=1,
        traps_floaters=True,
        traps_sinkers=False,
        image="a clump of leaves pressed against the blocked curb",
        tags={"curb"},
    ),
    "shop_step": Place(
        id="shop_step",
        label="shop step",
        phrase="the shop step",
        depth=1,
        traps_floaters=True,
        traps_sinkers=False,
        image="the first stone step of a little shop where the water curled in circles",
        tags={"step"},
    ),
}

TOOLS = {
    "umbrella_hook": Tool(
        id="umbrella_hook",
        label="umbrella",
        phrase="a closed umbrella",
        reach=2,
        lifts=True,
        text="slid the crook of the umbrella under it and lifted carefully",
        qa_text="used the hooked handle of an umbrella to lift it out",
        tags={"umbrella"},
    ),
    "long_net": Tool(
        id="long_net",
        label="long net",
        phrase="a long net from a delivery cart",
        reach=2,
        lifts=True,
        text="dipped the long net into the water and scooped gently",
        qa_text="scooped it out with a long net",
        tags={"net"},
    ),
    "broom_handle": Tool(
        id="broom_handle",
        label="broom handle",
        phrase="a broom handle",
        reach=1,
        lifts=True,
        text="nudged it free with the broom handle and drew it close enough to grab",
        qa_text="nudged it free with a broom handle and pulled it close",
        tags={"broom"},
    ),
}

SUSPECTS = {
    "shopkeeper": SuspectRole(
        id="shopkeeper",
        label="shopkeeper",
        action="bending low with rolled sleeves",
        innocent_goal="I was clearing leaves so the water would stop climbing onto my step",
        reveal="I only wanted to help the water move away, not hide anything",
        tags={"shopkeeper"},
    ),
    "crossing_guard": SuspectRole(
        id="crossing_guard",
        label="crossing guard",
        action="peering into the water with a worried frown",
        innocent_goal="I was checking whether the drain was blocked before the crossing got worse",
        reveal="I was watching the water, not taking treasures from it",
        tags={"crossing_guard"},
    ),
    "delivery_rider": SuspectRole(
        id="delivery_rider",
        label="delivery rider",
        action="crouching beside a half-submerged cart",
        innocent_goal="I was trying to free my wheel from the leaves and wrappers",
        reveal="I was rescuing my cart, not sneaking off with your things",
        tags={"delivery"},
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Lina", "Nora", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Noah", "Eli", "Sam"]
SUSPECT_NAMES = ["Mr. Vale", "Ms. Reed", "Uncle Jo", "Aunt Bea"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    item: str
    place: str
    tool: str
    suspect_role: str
    hero_name: str
    hero_type: str
    suspect_name: str
    suspect_type: str
    parent_type: str
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
    "congestion": [
        (
            "What is congestion on a street?",
            "Congestion means too many cars are trying to use the street at once, so traffic moves very slowly. When roads are wet or partly blocked, congestion can become even worse."
        )
    ],
    "drain": [
        (
            "What does a storm drain do?",
            "A storm drain lets rainwater leave the street. If leaves block it, water can pile up and make a street flood."
        )
    ],
    "flood": [
        (
            "Why can water carry small things away?",
            "Moving water pushes on light or loose objects and can sweep them along. That is why dropped things can drift toward curbs, drains, or steps."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a character remembers something from a little earlier or from the past. That memory can help explain what is happening now."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. Asking questions and checking clues can clear it up."
        )
    ],
    "umbrella": [
        (
            "How can an umbrella help reach something?",
            "A closed umbrella has a curved handle that can hook or lift a small object. It can help someone reach into water without stepping in."
        )
    ],
    "net": [
        (
            "What is a net good for?",
            "A net can scoop and hold something while water slips through. That makes it useful for lifting small things out of puddles or shallow floodwater."
        )
    ],
    "broom": [
        (
            "How can a broom handle help in water?",
            "A broom handle can push or nudge something that is just out of reach. It works best when the object is shallow and not tightly stuck."
        )
    ],
}

KNOWLEDGE_ORDER = ["congestion", "flood", "drain", "flashback", "misunderstanding", "umbrella", "net", "broom"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    place_cfg = f["place_cfg"]
    role_cfg = f["role_cfg"]
    return [
        'Write a gentle mystery for a 3-to-5-year-old set on a flooded street that includes the word "congestion".',
        f"Tell a story where {hero.id} loses {item_cfg.phrase}, suspects a {role_cfg.label}, and then solves the mystery with a flashback.",
        f"Write a child-facing mystery in which floodwater carries a missing object toward {place_cfg.phrase}, causing a misunderstanding before the truth is discovered.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    suspect = f["suspect"]
    item_cfg = f["item_cfg"]
    place_cfg = f["place_cfg"]
    tool_cfg = f["tool_cfg"]
    role_cfg = f["role_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who lost {item_cfg.phrase} on a flooded street, and {suspect.id}, the {role_cfg.label} {hero.pronoun()} first misunderstood. The mystery changes when they begin looking at the water instead of blaming a person."
        ),
        (
            f"What made the day feel strange at the beginning?",
            f"The street was full of floodwater and traffic congestion, so everything moved slowly and looked wobbly in the water. That made the whole place feel mysterious before the missing item was even gone."
        ),
        (
            f"Why did {hero.id} think {suspect.id} had taken the {item_cfg.label}?",
            f"{hero.id} saw {suspect.id} {role_cfg.action} beside {place_cfg.phrase}, and from far away it looked sneaky. Because the item had just vanished, {hero.id} connected the two things and made a mistaken guess."
        ),
        (
            "How did the flashback help solve the mystery?",
            f"The flashback reminded {hero.id} that the water had pushed the {item_cfg.label} toward {place_cfg.phrase}. That memory turned the search away from blame and toward the true path the flood had made."
        ),
        (
            f"How did they get the {item_cfg.label} back?",
            f"{suspect.id} {tool_cfg.qa_text}. They could do that because the item was trapped at {place_cfg.phrase}, where the flood had carried it."
        ),
        (
            "What was the misunderstanding?",
            f"The misunderstanding was that {hero.id} thought {suspect.id} had stolen the missing thing. Really, {suspect.pronoun()} was busy {role_cfg.innocent_goal[:-1].lower()}, and the water was the real cause."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"congestion", "flood", "flashback", "misunderstanding"}
    place_tags = f["place_cfg"].tags
    if "drain" in place_tags:
        tags.add("drain")
    tags |= f["tool_cfg"].tags
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="key_tin",
        place="storm_drain",
        tool="umbrella_hook",
        suspect_role="crossing_guard",
        hero_name="Mina",
        hero_type="girl",
        suspect_name="Mr. Vale",
        suspect_type="man",
        parent_type="mother",
    ),
    StoryParams(
        item="note_bottle",
        place="blocked_curb",
        tool="broom_handle",
        suspect_role="shopkeeper",
        hero_name="Owen",
        hero_type="boy",
        suspect_name="Ms. Reed",
        suspect_type="woman",
        parent_type="father",
    ),
    StoryParams(
        item="note_bottle",
        place="shop_step",
        tool="long_net",
        suspect_role="delivery_rider",
        hero_name="Lina",
        hero_type="girl",
        suspect_name="Aunt Bea",
        suspect_type="woman",
        parent_type="mother",
    ),
    StoryParams(
        item="silver_badge",
        place="storm_drain",
        tool="long_net",
        suspect_role="crossing_guard",
        hero_name="Ben",
        hero_type="boy",
        suspect_name="Uncle Jo",
        suspect_type="man",
        parent_type="father",
    ),
]


def explain_combo(item: LostItem, place: Place) -> str:
    if item.buoyant and not place.traps_floaters:
        return (
            f"(No story: {item.phrase} would not stay at {place.phrase}. It would float past instead of getting trapped there.)"
        )
    if (not item.buoyant) and not place.traps_sinkers:
        return (
            f"(No story: {item.phrase} would sink, but {place.phrase} only makes sense as a place that catches floating things.)"
        )
    return "(No story: this flood path is not plausible.)"


def explain_tool(place: Place, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} cannot reasonably recover something from {place.phrase}. "
        f"The place is too deep or awkward for that method.)"
    )


ASP_RULES = r"""
% item/place plausibility
can_trap(I,P) :- item(I), buoyant(I), place(P), traps_floaters(P).
can_trap(I,P) :- item(I), sinks(I), place(P), traps_sinkers(P).

% tool/place fit
tool_fits(T,P) :- tool(T), lifts(T), place(P), reach(T,R), depth(P,D), R >= D.

valid(I,P) :- can_trap(I,P).
recoverable(I,P,T) :- valid(I,P), tool_fits(T,P).

#show valid/2.
#show recoverable/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.buoyant:
            lines.append(asp.fact("buoyant", item_id))
        else:
            lines.append(asp.fact("sinks", item_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("depth", place_id, place.depth))
        if place.traps_floaters:
            lines.append(asp.fact("traps_floaters", place_id))
        if place.traps_sinkers:
            lines.append(asp.fact("traps_sinkers", place_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.lifts:
            lines.append(asp.fact("lifts", tool_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_recoverable() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "recoverable")))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_recoverable = {
        (item_id, place_id, tool_id)
        for item_id, place_id in valid_combos()
        for tool_id, tool in TOOLS.items()
        if tool_fits(PLACES[place_id], tool)
    }
    asp_rec = set(asp_recoverable())
    if py_recoverable == asp_rec:
        print(f"OK: ASP recoverable triples match ({len(py_recoverable)} triples).")
    else:
        rc = 1
        print("MISMATCH in recoverable triples:")
        if asp_rec - py_recoverable:
            print("  only in ASP:", sorted(asp_rec - py_recoverable))
        if py_recoverable - asp_rec:
            print("  only in Python:", sorted(py_recoverable - asp_rec))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "congestion" not in sample.story:
            raise StoryError("smoke test story missing required content")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a missing object on a flooded street, a misunderstanding, and a flashback that solves the puzzle."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--suspect-role", choices=SUSPECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid item/place pairs and recoverable triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.place:
        item = ITEMS[args.item]
        place = PLACES[args.place]
        if not can_trap(item, place):
            raise StoryError(explain_combo(item, place))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.place is None or combo[1] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, place_id = rng.choice(sorted(combos))

    possible_tools = [
        tool_id for tool_id, tool in TOOLS.items()
        if tool_fits(PLACES[place_id], tool)
        and (args.tool is None or tool_id == args.tool)
    ]
    if not possible_tools:
        if args.tool is not None:
            raise StoryError(explain_tool(PLACES[place_id], TOOLS[args.tool]))
        raise StoryError("(No valid recovery tool matches the given options.)")

    tool_id = rng.choice(sorted(possible_tools))
    suspect_role = args.suspect_role or rng.choice(sorted(SUSPECTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name_value = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    suspect_name = rng.choice(SUSPECT_NAMES)
    suspect_type = "woman" if suspect_name.startswith(("Ms.", "Aunt")) else "man"

    return StoryParams(
        item=item_id,
        place=place_id,
        tool=tool_id,
        suspect_role=suspect_role,
        hero_name=hero_name_value,
        hero_type=hero_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.suspect_role not in SUSPECTS:
        raise StoryError(f"(Unknown suspect role: {params.suspect_role})")
    item_cfg = ITEMS[params.item]
    place_cfg = PLACES[params.place]
    tool_cfg = TOOLS[params.tool]
    role_cfg = SUSPECTS[params.suspect_role]
    if not can_trap(item_cfg, place_cfg):
        raise StoryError(explain_combo(item_cfg, place_cfg))
    if not tool_fits(place_cfg, tool_cfg):
        raise StoryError(explain_tool(place_cfg, tool_cfg))

    world = tell(
        item_cfg=item_cfg,
        place_cfg=place_cfg,
        tool_cfg=tool_cfg,
        role_cfg=role_cfg,
        hero_name_value=params.hero_name,
        hero_type=params.hero_type,
        suspect_name=params.suspect_name,
        suspect_type=params.suspect_type,
        parent_type=params.parent_type,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid item/place pairs:\n")
        for item_id, place_id in asp_valid_combos():
            print(f"  {item_id:12} {place_id}")
        print("\nrecoverable triples:\n")
        for item_id, place_id, tool_id in asp_recoverable():
            print(f"  {item_id:12} {place_id:12} {tool_id}")
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
            header = f"### {p.hero_name}: {p.item} at {p.place} ({p.tool}, {p.suspect_role})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
