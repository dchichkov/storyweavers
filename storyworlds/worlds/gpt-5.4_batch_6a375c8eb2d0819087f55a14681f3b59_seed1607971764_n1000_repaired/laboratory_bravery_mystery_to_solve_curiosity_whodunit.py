#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py
====================================================================================

A standalone storyworld about a small whodunit in a children's laboratory.

A curious child and a friend are doing a simple science activity in the laboratory
when an important object goes missing. A clue appears. The children must decide
what the clue means, gather their bravery, and investigate a slightly spooky spot.
Sometimes the hero is brave enough to check it directly; sometimes asking the
teacher to help is the brave move. Either way, the mystery is solved by following
world-state constraints rather than swapping nouns into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py --item badge --cause gecko
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py --cause draft --item vial
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/laboratory_bravery_mystery_to_solve_curiosity_whodunit.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher_f", "mother"}
        male = {"boy", "man", "teacher_m", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    shape: str
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
class CauseCfg:
    id: str
    label: str
    clue: str
    places: set[str]
    item_tags: set[str]
    first_guess: str
    reveal: str
    ending_image: str
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
class ClueCfg:
    id: str
    label: str
    sentence: str
    points_to: str
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
class PlaceCfg:
    id: str
    label: str
    phrase: str
    mood: str
    scariness: int
    needs: set[str]
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    comfort: int
    action: str
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


def _r_missing_curiosity(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("hero", "friend"):
        kid = world.get(eid)
        sig = ("curious", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["curiosity"] += 1
        out.append("__curious__")
    return out


def _r_search_fear(world: World) -> list[str]:
    place = world.get("place")
    if place.meters["searched"] < THRESHOLD:
        return []
    if int(place.attrs.get("scariness", 0)) < 2:
        return []
    hero = world.get("hero")
    sig = ("fear", hero.id, place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return ["__fear__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("hero", "friend"):
        kid = world.get(eid)
        sig = ("relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        out.append("__relief__")
    teacher = world.get("teacher")
    tsig = ("teacher_relief", teacher.id)
    if tsig not in world.fired:
        world.fired.add(tsig)
        teacher.memes["relief"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_curiosity", tag="emotional", apply=_r_missing_curiosity),
    Rule(name="search_fear", tag="emotional", apply=_r_search_fear),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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


ITEMS = {
    "badge": ItemCfg(
        id="badge",
        label="star badge",
        phrase="a silver star badge for the science fair table",
        shape="light",
        tags={"light", "flat", "badge"},
    ),
    "notebook": ItemCfg(
        id="notebook",
        label="lab notebook",
        phrase="a striped lab notebook full of careful notes",
        shape="flat",
        tags={"light", "flat", "paper", "notebook"},
    ),
    "vial": ItemCfg(
        id="vial",
        label="blue sample vial",
        phrase="a tiny blue sample vial with a cork top",
        shape="small",
        tags={"small", "fragile", "vial"},
    ),
}

CLUES = {
    "tail_dust": ClueCfg(
        id="tail_dust",
        label="a dusty tail-swish mark",
        sentence="A pale, curvy streak of dust ran across the table like something small had swished by with its tail.",
        points_to="an animal clue",
        tags={"dust", "animal"},
    ),
    "wheel_tracks": ClueCfg(
        id="wheel_tracks",
        label="tiny wheel tracks",
        sentence="Two neat lines of tiny wheel tracks rolled through a patch of spilled chalk dust and vanished under a cabinet.",
        points_to="a rolling helper",
        tags={"tracks", "robot"},
    ),
    "fluttered_papers": ClueCfg(
        id="fluttered_papers",
        label="fluttered papers",
        sentence="The paper labels by the open window were all tipped the same way, as if a sneaky gust had brushed past them.",
        points_to="moving air",
        tags={"paper", "wind"},
    ),
}

PLACES = {
    "lamp_shelf": PlaceCfg(
        id="lamp_shelf",
        label="the heat-lamp shelf",
        phrase="the tall shelf under the warm heat lamp",
        mood="It was high, warm, and a little shadowy up near the top jars.",
        scariness=2,
        needs={"high"},
        tags={"high", "warm"},
    ),
    "under_cabinet": PlaceCfg(
        id="under_cabinet",
        label="under the sample cabinet",
        phrase="the dark space under the sample cabinet",
        mood="It was dark under there, with only a thin strip of light on the floor.",
        scariness=2,
        needs={"dark"},
        tags={"dark", "low"},
    ),
    "behind_chart": PlaceCfg(
        id="behind_chart",
        label="behind the weather chart",
        phrase="the corner behind the big weather chart",
        mood="The chart rustled softly, but the corner behind it was not very scary once someone peeked there.",
        scariness=1,
        needs=set(),
        tags={"corner"},
    ),
}

TOOLS = {
    "stool": ToolCfg(
        id="stool",
        label="step stool",
        phrase="a little step stool",
        helps_with={"high"},
        comfort=2,
        action="set the step stool in place and climbed carefully",
        tags={"stool", "reach"},
    ),
    "flashlight": ToolCfg(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        helps_with={"dark"},
        comfort=2,
        action="clicked on the flashlight and shone the beam ahead",
        tags={"flashlight", "light"},
    ),
    "magnifier": ToolCfg(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        helps_with=set(),
        comfort=0,
        action="held up the magnifying glass and squinted hard",
        tags={"magnifier", "clue"},
    ),
}

CAUSES = {
    "gecko": CauseCfg(
        id="gecko",
        label="the little gecko",
        clue="tail_dust",
        places={"lamp_shelf"},
        item_tags={"light", "badge"},
        first_guess="At first, they wondered if someone had tucked it away by mistake.",
        reveal="The little gecko had carried it toward the warm lamp because the shiny edge glimmered there.",
        ending_image="The gecko blinked from the warm shelf while the badge flashed safely in the light.",
        tags={"animal", "gecko"},
    ),
    "robot": CauseCfg(
        id="robot",
        label="the cleaning robot",
        clue="wheel_tracks",
        places={"under_cabinet"},
        item_tags={"small", "light", "flat", "fragile"},
        first_guess="At first, they whispered about who could have taken it, but nobody had even left the room.",
        reveal="The cleaning robot had bumped it while sweeping up chalk and gently nudged it under the cabinet.",
        ending_image="The little robot hummed past again while the found object sat back where it belonged.",
        tags={"robot", "machine"},
    ),
    "draft": CauseCfg(
        id="draft",
        label="a draft from the window",
        clue="fluttered_papers",
        places={"behind_chart"},
        item_tags={"flat", "paper", "light", "badge"},
        first_guess="At first, the mystery felt like a real whodunit, because nothing makes a louder story than an object vanishing in plain sight.",
        reveal="A draft from the cracked window had lifted it and skated it across the room behind the chart.",
        ending_image="The chart stood still after the window was latched, and the found object rested flat and calm on the table.",
        tags={"wind", "air"},
    ),
}

HERO_TRAITS = {
    "bold": 3,
    "steady": 2,
    "cautious": 1,
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Ella", "Ruby", "Ivy", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Eli", "Noah", "Finn", "Leo"]
TEACHERS = {
    "ms_rivera": ("Ms. Rivera", "teacher_f"),
    "mr_park": ("Mr. Park", "teacher_m"),
}


def clue_matches(cause_id: str, clue_id: str) -> bool:
    return clue_id == CAUSES[cause_id].clue


def item_movable(cause_id: str, item_id: str) -> bool:
    return bool(CAUSES[cause_id].item_tags & ITEMS[item_id].tags)


def place_matches(cause_id: str, place_id: str) -> bool:
    return place_id in CAUSES[cause_id].places


def tool_usable(tool_id: str, place_id: str) -> bool:
    needs = PLACES[place_id].needs
    return needs.issubset(TOOLS[tool_id].helps_with)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for item_id in ITEMS:
        for cause_id in CAUSES:
            for clue_id in CLUES:
                for place_id in PLACES:
                    for tool_id in TOOLS:
                        if not clue_matches(cause_id, clue_id):
                            continue
                        if not item_movable(cause_id, item_id):
                            continue
                        if not place_matches(cause_id, place_id):
                            continue
                        if not tool_usable(tool_id, place_id):
                            continue
                        combos.append((item_id, cause_id, clue_id, place_id, tool_id))
    return combos


def courage_score(trait: str, tool_id: str) -> int:
    return HERO_TRAITS[trait] + TOOLS[tool_id].comfort


def outcome_of(params: "StoryParams") -> str:
    if courage_score(params.trait, params.tool) >= PLACES[params.place].scariness:
        return "direct_find"
    return "teacher_help"


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    place = sim.get("place")
    item = sim.get("item")
    place.meters["searched"] += 1
    propagate(sim, narrate=False)
    if sim.facts["predicted_outcome"] == "direct_find":
        item.meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("hero").memes["fear"],
        "finds_directly": item.meters["found"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, teacher: Entity) -> None:
    world.say(
        f"After school, {hero.id} and {friend.id} hurried into the laboratory for science club. "
        f"{teacher.id} had set out beakers, labels, and one clean tray for the afternoon's work."
    )


def setup_case(world: World, hero: Entity, friend: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On the tray sat {item_cfg.phrase}. {hero.id} liked how important it looked, "
        f"and {friend.id} leaned close to read every little mark."
    )


def vanish(world: World, hero: Entity, friend: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} turned back from the sink, the {item_cfg.label} was gone."
    )
    world.say(
        f'"Wait," whispered {friend.id}. "It was right here."'
    )


def notice_clue(world: World, hero: Entity, friend: Entity, clue_cfg: ClueCfg, cause_cfg: CauseCfg) -> None:
    world.say(cause_cfg.first_guess)
    world.say(
        f"Then {hero.id}'s curiosity tugged harder than worry. {clue_cfg.sentence}"
    )
    world.say(
        f'"That is our clue," {hero.id} said. "{clue_cfg.label.capitalize()} means {clue_cfg.points_to}."'
    )


def inspect_clue(world: World, hero: Entity, friend: Entity, teacher: Entity, place_cfg: PlaceCfg) -> None:
    pred = predict_outcome(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{friend.id} followed the clue with one careful finger until it pointed toward {place_cfg.phrase}."
    )
    if pred["fear"] >= THRESHOLD:
        world.say(
            f'{friend.id} stopped and looked up. "{place_cfg.mood} Do you think we should check?"'
        )
    else:
        world.say(
            f'{friend.id} tipped {friend.pronoun("possessive")} head. "{place_cfg.mood} That must be where it went."'
        )
    world.say(
        f'{teacher.id} stayed near the long table and said, "Use your eyes, use your brains, and if you need help, ask."'
    )


def decide_to_search(world: World, hero: Entity, friend: Entity, tool_cfg: ToolCfg, place_cfg: PlaceCfg) -> None:
    hero.memes["bravery"] = float(HERO_TRAITS[world.facts["trait"]])
    world.say(
        f"{hero.id} took {tool_cfg.phrase}, because mysteries in a laboratory are easier to solve when hands and eyes are ready."
    )
    world.say(
        f"Curiosity pushed {hero.pronoun('object')} forward, even though the clue led to {place_cfg.label}."
    )


def direct_search(world: World, hero: Entity, friend: Entity, item: Entity, place: Entity,
                  item_cfg: ItemCfg, tool_cfg: ToolCfg, cause_cfg: CauseCfg) -> None:
    place.meters["searched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {hero.id} {tool_cfg.action}."
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s stomach gave a tiny flutter, but {hero.pronoun()} kept going."
        )
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There it was: the {item_cfg.label}, tucked exactly where the clue had led."
    )
    world.say(
        f'"Aha!" cried {friend.id}. "So the mystery was {cause_cfg.label}!"'
    )


def ask_teacher(world: World, hero: Entity, friend: Entity, teacher: Entity, item: Entity, place: Entity,
                item_cfg: ItemCfg, tool_cfg: ToolCfg, cause_cfg: CauseCfg) -> None:
    place.meters["searched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} started toward the clue, then stopped. Being brave did not feel like pretending not to be scared."
    )
    world.say(
        f'"{teacher.id}," {hero.pronoun()} called, "will you come with us to {place.label}?"'
    )
    teacher.memes["care"] += 1
    world.say(
        f'{teacher.id} smiled. "That is a brave question," {teacher.pronoun()} said, and {teacher.pronoun()} came over while {hero.id} {tool_cfg.action}.'
    )
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they spotted the {item_cfg.label} hidden there."
    )
    world.say(
        f'"So that was it," said {friend.id}. "The mystery was {cause_cfg.label}, not a thief at all."'
    )


def explain_solution(world: World, teacher: Entity, cause_cfg: CauseCfg) -> None:
    world.say(
        f"{teacher.id} looked at the clue again and nodded. {cause_cfg.reveal}"
    )


def restore_order(world: World, hero: Entity, friend: Entity, teacher: Entity,
                  item_cfg: ItemCfg, cause_cfg: CauseCfg) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"{hero.id} carried the {item_cfg.label} back to the tray, and {friend.id} straightened the labels."
    )
    world.say(
        f'"Good detectives notice small things," said {teacher.id}. "Good detectives are brave enough to check them carefully too."'
    )
    world.say(cause_cfg.ending_image)


def tell(item_cfg: ItemCfg, cause_cfg: CauseCfg, clue_cfg: ClueCfg, place_cfg: PlaceCfg,
         tool_cfg: ToolCfg, trait: str, hero_name: str = "Lina", hero_type: str = "girl",
         friend_name: str = "Owen", friend_type: str = "boy",
         teacher_id: str = "ms_rivera") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=[trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["careful"]))
    teacher_name, teacher_type = TEACHERS[teacher_id]
    teacher = world.add(Entity(id=teacher_name, kind="character", type=teacher_type, role="teacher", label="teacher"))
    item = world.add(Entity(id="item", type="object", label=item_cfg.label, attrs={"shape": item_cfg.shape}))
    place = world.add(
        Entity(
            id="place",
            type="place",
            label=place_cfg.label,
            attrs={"scariness": place_cfg.scariness, "needs": sorted(place_cfg.needs)},
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            attrs={"comfort": tool_cfg.comfort, "helps_with": sorted(tool_cfg.helps_with)},
        )
    )

    world.facts["trait"] = trait
    world.facts["predicted_outcome"] = "direct_find" if courage_score(trait, tool_cfg.id) >= place_cfg.scariness else "teacher_help"
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["teacher"] = teacher
    world.facts["item_cfg"] = item_cfg
    world.facts["cause_cfg"] = cause_cfg
    world.facts["clue_cfg"] = clue_cfg
    world.facts["place_cfg"] = place_cfg
    world.facts["tool_cfg"] = tool_cfg

    introduce(world, hero, friend, teacher)
    setup_case(world, hero, friend, item, item_cfg)

    world.para()
    vanish(world, hero, friend, item, item_cfg)
    notice_clue(world, hero, friend, clue_cfg, cause_cfg)
    inspect_clue(world, hero, friend, teacher, place_cfg)

    world.para()
    decide_to_search(world, hero, friend, tool_cfg, place_cfg)
    if world.facts["predicted_outcome"] == "direct_find":
        direct_search(world, hero, friend, item, place, item_cfg, tool_cfg, cause_cfg)
        outcome = "direct_find"
    else:
        ask_teacher(world, hero, friend, teacher, item, place, item_cfg, tool_cfg, cause_cfg)
        outcome = "teacher_help"

    world.para()
    explain_solution(world, teacher, cause_cfg)
    restore_order(world, hero, friend, teacher, item_cfg, cause_cfg)

    world.facts["outcome"] = outcome
    world.facts["found"] = item.meters["found"] >= THRESHOLD
    world.facts["felt_fear"] = hero.memes["fear"] >= THRESHOLD
    world.facts["asked_for_help"] = outcome == "teacher_help"
    world.facts["curious"] = hero.memes["curiosity"] >= THRESHOLD
    world.facts["brave"] = True
    return world


KNOWLEDGE = {
    "laboratory": [
        (
            "What is a laboratory?",
            "A laboratory is a room where people do careful experiments, look closely at things, and use tools to learn. It is a place for noticing details."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives and curious children use clues to solve mysteries."
        )
    ],
    "gecko": [
        (
            "What is a gecko?",
            "A gecko is a small lizard. Some geckos like warm places, so they may rest near a lamp or sunny spot."
        )
    ],
    "robot": [
        (
            "What does a cleaning robot do?",
            "A cleaning robot rolls along the floor and picks up dust or crumbs. Because it moves things gently, it can sometimes bump a small object by accident."
        )
    ],
    "wind": [
        (
            "What can a draft do inside a room?",
            "A draft is moving air. It can flutter paper and slide light things across a smooth table or floor."
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help in a dark place?",
            "A flashlight makes a bright beam so you can see where you are looking. That makes it easier to check a dark place carefully."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps someone reach a place that is too high. It lets you climb carefully instead of stretching unsafely."
        )
    ],
    "magnifier": [
        (
            "What is a magnifying glass for?",
            "A magnifying glass makes small details look bigger. It helps you study tiny clues."
        )
    ],
    "bravery": [
        (
            "What does bravery mean?",
            "Bravery does not mean never feeling scared. Bravery means doing the careful right thing even when something feels a little scary."
        )
    ],
}
KNOWLEDGE_ORDER = ["laboratory", "clue", "gecko", "robot", "wind", "flashlight", "stool", "magnifier", "bravery"]


@dataclass
class StoryParams:
    item: str
    cause: str
    clue: str
    place: str
    tool: str
    trait: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    teacher: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    place_cfg = f["place_cfg"]
    outcome = f["outcome"]
    if outcome == "teacher_help":
        return [
            f'Write a short whodunit for a 3-to-5-year-old set in a laboratory where a missing {item_cfg.label} is found by following {clue_cfg.label}.',
            f"Tell a gentle mystery story where {hero.id}'s curiosity leads to a clue, but asking the teacher for help is the brave choice.",
            f'Write a child-facing mystery that includes the word "laboratory", has a slightly spooky clue trail to {place_cfg.label}, and ends with a calm solution.'
        ]
    return [
        f'Write a short whodunit for a 3-to-5-year-old set in a laboratory where a missing {item_cfg.label} is found by following {clue_cfg.label}.',
        f"Tell a curious, brave mystery story where {hero.id} follows one clue after another and solves the case.",
        f'Write a gentle detective story that includes the word "laboratory", uses a clue to reach {place_cfg.label}, and ends by showing what really moved the missing object.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    teacher = f["teacher"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    cause_cfg = f["cause_cfg"]
    place_cfg = f["place_cfg"]
    tool_cfg = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            "It happens in a laboratory during science club. The careful tools and labels make the room feel like the right place for a little mystery."
        ),
        (
            f"What was missing?",
            f"The missing object was the {item_cfg.label}. Its disappearance started the mystery because everyone had just seen it on the tray."
        ),
        (
            "What clue did the children find?",
            f"They found {clue_cfg.label}. That clue mattered because it pointed them toward {cause_cfg.label} instead of a person taking the object."
        ),
        (
            f"Why did {hero.id} go toward {place_cfg.label}?",
            f"{hero.id} followed the clue there. Curiosity made {hero.pronoun('object')} want to test the idea instead of only guessing."
        ),
    ]
    if f["outcome"] == "direct_find":
        answer = (
            f"{hero.id} used {tool_cfg.phrase} and checked {place_cfg.label} directly. "
            f"{hero.pronoun().capitalize()} felt a little scared, but kept going, and that brave search led straight to the {item_cfg.label}."
        )
        qa.append((f"How was {hero.id} brave?", answer))
    else:
        answer = (
            f"{hero.id} was brave by asking {teacher.id} to come along. "
            f"{hero.pronoun().capitalize()} did not pretend the place felt easy; asking for help was the careful choice that let them solve the mystery safely."
        )
        qa.append((f"How was {hero.id} brave?", answer))
    qa.append(
        (
            "What really happened to the missing object?",
            f"{cause_cfg.reveal} The clue matched that cause, which is why the children could solve the whodunit."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The {item_cfg.label} was returned to the tray, and the laboratory felt calm again. {friend.id}, {hero.id}, and {teacher.id} all knew that careful curiosity had solved the case."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"laboratory", "clue", "bravery"}
    cause_cfg = f["cause_cfg"]
    tool_cfg = f["tool_cfg"]
    if "gecko" in cause_cfg.tags:
        tags.add("gecko")
    if "robot" in cause_cfg.tags:
        tags.add("robot")
    if "wind" in cause_cfg.tags:
        tags.add("wind")
    if tool_cfg.id == "flashlight":
        tags.add("flashlight")
    if tool_cfg.id == "stool":
        tags.add("stool")
    if tool_cfg.id == "magnifier":
        tags.add("magnifier")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted_fear={world.facts.get('predicted_fear', 0)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="badge",
        cause="gecko",
        clue="tail_dust",
        place="lamp_shelf",
        tool="stool",
        trait="steady",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        teacher="ms_rivera",
    ),
    StoryParams(
        item="notebook",
        cause="robot",
        clue="wheel_tracks",
        place="under_cabinet",
        tool="flashlight",
        trait="bold",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        teacher="mr_park",
    ),
    StoryParams(
        item="notebook",
        cause="draft",
        clue="fluttered_papers",
        place="behind_chart",
        tool="magnifier",
        trait="cautious",
        hero_name="Tess",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        teacher="ms_rivera",
    ),
    StoryParams(
        item="vial",
        cause="robot",
        clue="wheel_tracks",
        place="under_cabinet",
        tool="magnifier",
        trait="cautious",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        teacher="mr_park",
    ),
    StoryParams(
        item="badge",
        cause="draft",
        clue="fluttered_papers",
        place="behind_chart",
        tool="magnifier",
        trait="steady",
        hero_name="Ivy",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        teacher="ms_rivera",
    ),
]


def explain_item(cause_id: str, item_id: str) -> str:
    return (
        f"(No story: {CAUSES[cause_id].label} is not a good match for moving the {ITEMS[item_id].label}. "
        f"Pick an item that this cause could reasonably shift.)"
    )


def explain_clue(cause_id: str, clue_id: str) -> str:
    return (
        f"(No story: {CLUES[clue_id].label} does not fit {CAUSES[cause_id].label}. "
        f"This mystery needs the clue and cause to agree.)"
    )


def explain_place(cause_id: str, place_id: str) -> str:
    return (
        f"(No story: {CAUSES[cause_id].label} would not leave the object at {PLACES[place_id].label}. "
        f"Choose a place that matches the real cause.)"
    )


def explain_tool(tool_id: str, place_id: str) -> str:
    needs = ", ".join(sorted(PLACES[place_id].needs)) or "nothing special"
    return (
        f"(No story: {TOOLS[tool_id].label} does not fit {PLACES[place_id].label}. "
        f"That place needs help with {needs}.)"
    )


ASP_RULES = r"""
clue_matches(C, Cl) :- clue_of(C, Cl).
movable(C, I) :- allows(C, Tag), item_tag(I, Tag).
place_matches(C, P) :- hides_in(C, P).
usable(T, P) :- place(P), tool(T), not need_missing(T, P).
need_missing(T, P) :- needs(P, Need), not helps(T, Need).

valid(I, C, Cl, P, T) :- item(I), cause(C), clue(Cl), place(P), tool(T),
                         clue_matches(C, Cl), movable(C, I), place_matches(C, P), usable(T, P).

direct_find :- chosen_place(P), chosen_tool(T), chosen_trait(Tr),
               scariness(P, S), bravery(Tr, B), comfort(T, C), B + C >= S.
teacher_help :- chosen_place(P), chosen_tool(T), chosen_trait(Tr),
                scariness(P, S), bravery(Tr, B), comfort(T, C), B + C < S.

outcome(direct_find) :- direct_find.
outcome(teacher_help) :- teacher_help.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("scariness", place_id, place.scariness))
        for need in sorted(place.needs):
            lines.append(asp.fact("needs", place_id, need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("comfort", tool_id, tool.comfort))
        for help_tag in sorted(tool.helps_with):
            lines.append(asp.fact("helps", tool_id, help_tag))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("clue_of", cause_id, cause.clue))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("hides_in", cause_id, place_id))
        for tag in sorted(cause.item_tags):
            lines.append(asp.fact("allows", cause_id, tag))
    for trait, score in HERO_TRAITS.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("bravery", trait, score))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a laboratory whodunit with curiosity and bravery."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--trait", choices=sorted(HERO_TRAITS))
    ap.add_argument("--teacher", choices=TEACHERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
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
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.clue and not clue_matches(args.cause, args.clue):
        raise StoryError(explain_clue(args.cause, args.clue))
    if args.cause and args.item and not item_movable(args.cause, args.item):
        raise StoryError(explain_item(args.cause, args.item))
    if args.cause and args.place and not place_matches(args.cause, args.place):
        raise StoryError(explain_place(args.cause, args.place))
    if args.place and args.tool and not tool_usable(args.tool, args.place):
        raise StoryError(explain_tool(args.tool, args.place))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.place is None or combo[3] == args.place)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id, clue_id, place_id, tool_id = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(sorted(HERO_TRAITS))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    teacher = args.teacher or rng.choice(sorted(TEACHERS))
    return StoryParams(
        item=item_id,
        cause=cause_id,
        clue=clue_id,
        place=place_id,
        tool=tool_id,
        trait=trait,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher=teacher,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.trait not in HERO_TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.teacher not in TEACHERS:
        raise StoryError(f"(Unknown teacher: {params.teacher})")
    if not clue_matches(params.cause, params.clue):
        raise StoryError(explain_clue(params.cause, params.clue))
    if not item_movable(params.cause, params.item):
        raise StoryError(explain_item(params.cause, params.item))
    if not place_matches(params.cause, params.place):
        raise StoryError(explain_place(params.cause, params.place))
    if not tool_usable(params.tool, params.place):
        raise StoryError(explain_tool(params.tool, params.place))

    world = tell(
        item_cfg=ITEMS[params.item],
        cause_cfg=CAUSES[params.cause],
        clue_cfg=CLUES[params.clue],
        place_cfg=PLACES[params.place],
        tool_cfg=TOOLS[params.tool],
        trait=params.trait,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        teacher_id=params.teacher,
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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, cause, clue, place, tool) combos:\n")
        for item_id, cause_id, clue_id, place_id, tool_id in combos:
            print(f"  {item_id:10} {cause_id:8} {clue_id:16} {place_id:14} {tool_id}")
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
                f"### {p.hero_name} & {p.friend_name}: {p.item} / {p.cause} / "
                f"{p.place} / {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
