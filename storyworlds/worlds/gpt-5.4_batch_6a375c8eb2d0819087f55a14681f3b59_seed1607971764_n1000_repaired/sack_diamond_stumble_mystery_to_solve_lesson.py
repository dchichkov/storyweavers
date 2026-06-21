#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py
===========================================================================

A standalone story world for a fairy-tale mystery: a child finds a diamond on a
path, notices signs of a torn sack and a stumble, follows the clues with a
helper, and learns that careful honesty solves mysteries better than greedy
guessing.

Run it
------
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py --place forest_path --carrier peddler --path roots
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py --path carpet   # rejected: too soft for a telling spill
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py --response keep # rejected: the world refuses the dishonest ending
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py --all
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sack_diamond_stumble_mystery_to_solve_lesson.py --verify
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
        female = {"girl", "woman", "queen", "mother"}
        male = {"boy", "man", "king", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"old_woman": "old woman", "old_man": "old man"}.get(self.type, self.type)
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
class Place:
    id: str
    name: str
    opening: str
    path_word: str
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
class Carrier:
    id: str
    label: str
    type: str
    phrase: str
    burden: str
    reason: str
    grateful_line: str
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
class PathType:
    id: str
    label: str
    phrase: str
    roughness: int
    clue_text: str
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
class Helper:
    id: str
    label: str
    kind: str
    notice: str
    ending_line: str
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
class SackType:
    id: str
    label: str
    adjective: str
    tear_word: str
    holds: str
    sturdy: int
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
class Response:
    id: str
    sense: int
    solves: bool
    honest: bool
    text: str
    qa_text: str
    fail_text: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    sack = world.get("sack")
    path = world.get("path")
    owner = world.get("owner")
    if sack.meters["torn"] < THRESHOLD or owner.meters["stumbled"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    severity = int(path.attrs.get("roughness", 0))
    if severity <= 0:
        return out
    sack.meters["spilled"] += 1
    sack.meters["diamonds_lost"] += float(severity)
    path.meters["clues"] += float(severity)
    owner.memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    path = world.get("path")
    if path.meters["clues"] < THRESHOLD or hero.meters["found_diamond"] < THRESHOLD:
        return out
    sig = ("mystery",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["care"] += 1
    out.append("__mystery__")
    return out


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    owner = world.get("owner")
    if hero.meters["returned"] < THRESHOLD:
        return out
    sig = ("returned",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    hero.memes["lesson"] += 1
    out.append("__return__")
    return out


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="mystery", tag="cognitive", apply=_r_mystery),
    Rule(name="return", tag="social", apply=_r_return),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "forest_path": Place(
        id="forest_path",
        name="the pine-wood path",
        opening="At the edge of an old kingdom, where pines whispered over a narrow path,",
        path_word="path",
        ending="the pines seemed to nod, as if the forest itself approved.",
        tags={"forest", "path"},
    ),
    "castle_road": Place(
        id="castle_road",
        name="the road below the castle hill",
        opening="Below the king's old castle, where banners snapped above a winding road,",
        path_word="road",
        ending="the castle windows shone like warm stars over the road.",
        tags={"castle", "road"},
    ),
    "river_lane": Place(
        id="river_lane",
        name="the lane by the silver river",
        opening="Beside a silver river, where reeds bent and minnows flashed in the shallows,",
        path_word="lane",
        ending="the river carried the evening light away in bright ribbons.",
        tags={"river", "lane"},
    ),
}

CARRIERS = {
    "peddler": Carrier(
        id="peddler",
        label="peddler",
        type="man",
        phrase="an old peddler in a patched blue cloak",
        burden="a sack slung over one shoulder",
        reason="He was hurrying to market before the sun climbed too high.",
        grateful_line="You have returned more than jewels; you have returned my peace.",
        tags={"peddler", "market"},
    ),
    "queen_messenger": Carrier(
        id="queen_messenger",
        label="messenger",
        type="woman",
        phrase="the queen's messenger in a green riding cape",
        burden="a stout sack tied to her saddle",
        reason="She was carrying the queen's bright stones to the palace jeweler.",
        grateful_line="The queen will hear that a truthful heart shines brighter than a diamond.",
        tags={"messenger", "queen"},
    ),
    "jeweler": Carrier(
        id="jeweler",
        label="jeweler",
        type="man",
        phrase="a careful jeweler with silver spectacles",
        burden="a sack hugged close to his chest",
        reason="He was taking cut gems to the spring fair in the next village.",
        grateful_line="A steady eye and an honest hand are worth a chest of treasure.",
        tags={"jeweler", "gems"},
    ),
}

PATHS = {
    "roots": PathType(
        id="roots",
        label="roots",
        phrase="twisted roots that pushed up through the earth",
        roughness=2,
        clue_text="bent fern tips and a scraped mark beside the roots",
        tags={"roots", "rough"},
    ),
    "steps": PathType(
        id="steps",
        label="stone steps",
        phrase="a tumble of old stone steps",
        roughness=3,
        clue_text="tiny chips on a step and a glittering line between the cracks",
        tags={"steps", "rough"},
    ),
    "bridge": PathType(
        id="bridge",
        label="bridge planks",
        phrase="hollow bridge planks over a brook",
        roughness=2,
        clue_text="a loose thread caught on the rail and bright specks near the boards",
        tags={"bridge", "rough"},
    ),
    "carpet": PathType(
        id="carpet",
        label="moss carpet",
        phrase="a thick carpet of moss under the trees",
        roughness=0,
        clue_text="nothing more than soft moss",
        tags={"soft"},
    ),
}

HELPERS = {
    "sparrow": Helper(
        id="sparrow",
        label="sparrow",
        kind="bird",
        notice="tilted its head and hopped toward the next bright speck",
        ending_line="The sparrow chirped as if it had solved the riddle too.",
        tags={"bird", "sparrow"},
    ),
    "fox": Helper(
        id="fox",
        label="fox",
        kind="animal",
        notice="sniffed the air and paused where the trail bent",
        ending_line="Even the fox gave one solemn nod before slipping back into the brush.",
        tags={"fox", "animal"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        kind="animal",
        notice="stamped once and stared at the torn thread on a briar",
        ending_line="The goat shook its bell and sounded pleased with the ending.",
        tags={"goat", "animal"},
    ),
}

SACKS = {
    "burlap": SackType(
        id="burlap",
        label="burlap sack",
        adjective="rough",
        tear_word="frayed",
        holds="diamond packets wrapped in cloth",
        sturdy=1,
        tags={"burlap", "sack"},
    ),
    "velvet": SackType(
        id="velvet",
        label="velvet sack",
        adjective="deep blue",
        tear_word="split",
        holds="loose diamonds meant for a crown setting",
        sturdy=1,
        tags={"velvet", "sack"},
    ),
    "leather": SackType(
        id="leather",
        label="leather sack",
        adjective="brown",
        tear_word="cracked",
        holds="small diamonds and bright crystal samples",
        sturdy=2,
        tags={"leather", "sack"},
    ),
}

RESPONSES = {
    "follow": Response(
        id="follow",
        sense=3,
        solves=True,
        honest=True,
        text="followed the glittering trail and asked, at each turn, who might have lost the sack",
        qa_text="followed the trail, solved the mystery, and returned the lost diamonds",
        fail_text="",
        tags={"honesty", "mystery"},
    ),
    "wait_gate": Response(
        id="wait_gate",
        sense=2,
        solves=True,
        honest=True,
        text="carried the diamond to the village gate and waited carefully until the worried owner came searching",
        qa_text="waited at the village gate and returned the diamond to its owner",
        fail_text="",
        tags={"honesty", "patience"},
    ),
    "keep": Response(
        id="keep",
        sense=1,
        solves=False,
        honest=False,
        text="slipped the diamond into a pocket and said nothing",
        qa_text="kept the diamond",
        fail_text="kept the diamond and never solved who had lost the sack",
        tags={"greed"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elin", "Tessa", "Nora", "Ada", "Mila", "Rosa"]
BOY_NAMES = ["Tobin", "Rowan", "Eli", "Bram", "Nico", "Perrin", "Leo", "Finn"]
TRAITS = ["gentle", "careful", "bright", "curious", "kind", "thoughtful"]


def spill_possible(sack: SackType, path: PathType) -> bool:
    return path.roughness > 0 and path.roughness >= sack.sturdy


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN and r.honest]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for carrier_id in CARRIERS:
            for sack_id, sack in SACKS.items():
                for path_id, path in PATHS.items():
                    if spill_possible(sack, path):
                        combos.append((place_id, carrier_id, sack_id, path_id))
    return combos


@dataclass
class StoryParams:
    place: str
    carrier: str
    sack: str
    path: str
    helper: str
    response: str
    hero_name: str
    hero_gender: str
    parent_type: str
    trait: str
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


def predict_owner_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("owner").meters["stumbled"] += 1
    sim.get("sack").meters["torn"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": int(sim.get("sack").meters["diamonds_lost"]),
        "clues": int(sim.get("path").meters["clues"]),
        "worry": int(sim.get("owner").memes["worry"]),
    }


def introduce(world: World, hero: Entity, place: Place, trait: str) -> None:
    world.say(
        f"{place.opening} there lived a {trait} child named {hero.id} who listened to small things."
    )
    world.say(
        f"{hero.id} could hear acorns drop, brook water laugh, and even the hush that comes before a mystery."
    )


def morning_walk(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"One golden morning, {hero.id} walked along {place.name} with {hero.pronoun('possessive')} {parent.label_word}, carrying an empty basket for herbs."
    )


def find_diamond(world: World, hero: Entity) -> None:
    hero.meters["found_diamond"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"Then {hero.pronoun()} saw a bright blink in the dust and stooped to pick up a diamond no bigger than a raindrop."
    )
    world.say(
        f"It lay all alone beside the path, too fine for a pebble and too lonely for treasure."
    )


def inspect(world: World, hero: Entity, place: Place, path_cfg: PathType, sack_cfg: SackType) -> None:
    pred = predict_owner_loss(world)
    world.facts["predicted_lost"] = pred["lost"]
    world.facts["predicted_clues"] = pred["clues"]
    hero.memes["attention"] += 1
    world.say(
        f"{hero.id} did not run off with the shining stone. Instead, {hero.pronoun()} looked around and saw {path_cfg.clue_text}."
    )
    world.say(
        f"Nearby lay one {sack_cfg.tear_word} thread from a {sack_cfg.label}. Something had torn, and someone had surely had a stumble."
    )


def puzzle(world: World, hero: Entity, parent: Entity, carrier_cfg: Carrier) -> None:
    propagate(world, narrate=False)
    world.say(
        f'"Whose diamond could this be?" {hero.id} whispered. {parent.label_word.capitalize()} only said, "The road tells stories if we read it slowly."'
    )
    world.say(
        f"So the mystery stood before them: somewhere ahead or behind, {carrier_cfg.phrase} might be missing more than a single jewel."
    )


def helper_arrives(world: World, helper_cfg: Helper) -> None:
    helper = world.get("helper")
    helper.memes["interest"] += 1
    world.say(
        f"Just then a {helper_cfg.label} came near, {helper_cfg.notice}."
    )


def follow_trail(world: World, hero: Entity, owner: Entity, helper_cfg: Helper, response_cfg: Response, place: Place) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} {response_cfg.text}. Each little gleam led to the next, like moon-drops scattered by an unseen hand."
    )
    world.say(
        f"At the bend of the {place.path_word}, they found the owner kneeling beside a torn sack, searching the ground with worried eyes."
    )
    owner.memes["worry"] += 1


def wait_and_meet(world: World, hero: Entity, owner: Entity, response_cfg: Response) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} {response_cfg.text}. Before long, footsteps hurried near, and a troubled traveler came asking whether anyone had seen a fallen diamond."
    )
    world.say(
        f"The traveler's voice shook, and the torn sack under one arm told the rest of the tale."
    )
    owner.memes["worry"] += 1


def return_treasure(world: World, hero: Entity, owner: Entity, carrier_cfg: Carrier, helper_cfg: Helper, sack_cfg: SackType) -> None:
    hero.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} placed the diamond in the owner\'s hand and pointed out the {sack_cfg.tear_word} place in the sack. "This belongs with the rest," {hero.pronoun()} said.'
    )
    world.say(
        f"The {carrier_cfg.label} looked into the torn sack and saw that more bright stones had slipped loose from among {sack_cfg.holds}."
    )
    world.say(
        f'"{carrier_cfg.grateful_line}" {owner.pronoun()} said, with such relief that the whole air seemed lighter.'
    )
    world.say(helper_cfg.ending_line)


def lesson(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"As they walked home, {hero.id}'s {parent.label_word} said, \"A quick hand may grab a glittering thing, but a careful heart finds the truth.\""
    )
    world.say(
        f"{hero.id} closed {hero.pronoun('possessive')} empty hand around the memory of the diamond and felt richer than before."
    )


def ending_image(world: World, place: Place) -> None:
    world.say(
        f"That evening, the last sun touched the path like a pale gold ribbon, and {place.ending}"
    )


def tell(
    place: Place,
    carrier_cfg: Carrier,
    sack_cfg: SackType,
    path_cfg: PathType,
    helper_cfg: Helper,
    response_cfg: Response,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    owner = world.add(Entity(id="owner", kind="character", type=carrier_cfg.type, label=carrier_cfg.label, role="owner"))
    sack = world.add(Entity(id="sack", kind="thing", type="sack", label=sack_cfg.label, role="sack"))
    path = world.add(Entity(id="path", kind="thing", type="path", label=path_cfg.label, role="path"))
    helper = world.add(Entity(id="helper", kind="thing", type=helper_cfg.kind, label=helper_cfg.label, role="helper"))

    hero.attrs["name"] = hero_name
    parent.attrs["relation"] = "parent"
    owner.attrs["phrase"] = carrier_cfg.phrase
    sack.attrs["holds"] = sack_cfg.holds
    path.attrs["roughness"] = path_cfg.roughness
    path.attrs["place_name"] = place.name
    helper.attrs["notice"] = helper_cfg.notice

    hero.meters["found_diamond"] = 0.0
    hero.meters["returned"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["attention"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["lesson"] = 0.0
    parent.memes["calm"] = 1.0
    owner.meters["stumbled"] = 0.0
    owner.memes["worry"] = 0.0
    owner.memes["gratitude"] = 0.0
    sack.meters["torn"] = 0.0
    sack.meters["spilled"] = 0.0
    sack.meters["diamonds_lost"] = 0.0
    path.meters["clues"] = 0.0

    world.facts["hero_name"] = hero_name
    world.facts["carrier_cfg"] = carrier_cfg
    world.facts["sack_cfg"] = sack_cfg
    world.facts["path_cfg"] = path_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["response_cfg"] = response_cfg
    world.facts["place"] = place
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["owner"] = owner
    world.facts["sack"] = sack
    world.facts["path"] = path
    world.facts["helper"] = helper

    introduce(world, hero, place, trait)
    morning_walk(world, hero, parent, place)

    world.para()
    find_diamond(world, hero)
    sack.meters["torn"] += 1
    owner.meters["stumbled"] += 1
    inspect(world, hero, place, path_cfg, sack_cfg)
    propagate(world, narrate=False)
    puzzle(world, hero, parent, carrier_cfg)
    helper_arrives(world, helper_cfg)

    world.para()
    if response_cfg.id == "follow":
        follow_trail(world, hero, owner, helper_cfg, response_cfg, place)
    else:
        wait_and_meet(world, hero, owner, response_cfg)
    return_treasure(world, hero, owner, carrier_cfg, helper_cfg, sack_cfg)

    world.para()
    lesson(world, hero, parent)
    ending_image(world, place)

    world.facts.update(
        outcome="returned",
        solved=True,
        owner_worried=owner.memes["worry"] >= THRESHOLD,
        owner_relieved=owner.memes["relief"] >= THRESHOLD,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
        diamonds_lost=int(sack.meters["diamonds_lost"]),
    )
    return world


KNOWLEDGE = {
    "diamond": [
        (
            "What is a diamond?",
            "A diamond is a very hard, bright stone that can sparkle when light touches it. People value diamonds because they are beautiful and rare."
        )
    ],
    "sack": [
        (
            "What is a sack?",
            "A sack is a strong bag used to carry things. If a sack tears, small things inside it can fall out."
        )
    ],
    "stumble": [
        (
            "What does it mean to stumble?",
            "To stumble means to trip or lose your step for a moment. When someone stumbles, they may drop what they are carrying."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something hidden or puzzling that you have to figure out. You solve a mystery by noticing clues and thinking carefully."
        )
    ],
    "honesty": [
        (
            "Why is honesty important when you find something that belongs to someone else?",
            "Honesty matters because the lost thing may be very important to its owner. Returning it helps another person and lets people trust you."
        )
    ],
    "patience": [
        (
            "How can patience help solve a problem?",
            "Patience gives you time to look closely and make a wise choice. When you rush, you can miss the clue that explains everything."
        )
    ],
    "roots": [
        (
            "Why can tree roots make walking hard?",
            "Tree roots can push up through the ground and make the path uneven. That makes it easier for someone to trip or stumble."
        )
    ],
    "steps": [
        (
            "Why are old stone steps easy to trip on?",
            "Old stone steps can be chipped, steep, or uneven. Feet can catch on them if a person is hurrying."
        )
    ],
    "bridge": [
        (
            "Why must you walk carefully on bridge planks?",
            "Bridge planks can creak, shift, or feel narrow under your feet. Careful steps help you keep your balance."
        )
    ],
}

KNOWLEDGE_ORDER = ["diamond", "sack", "stumble", "mystery", "honesty", "patience", "roots", "steps", "bridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    carrier_cfg = f["carrier_cfg"]
    path_cfg = f["path_cfg"]
    helper_cfg = f["helper_cfg"]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "sack", "diamond", and "stumble", and centers on a mystery to solve.',
        f"Tell a gentle fairy-tale mystery where {f['hero_name']} finds a diamond on {place.name}, notices a torn sack after someone had a stumble on {path_cfg.label}, and chooses honesty over greed.",
        f"Write a story in which a child and a {helper_cfg.label} solve the mystery of a missing diamond for {carrier_cfg.phrase}, ending with a lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    owner = f["owner"]
    carrier_cfg = f["carrier_cfg"]
    sack_cfg = f["sack_cfg"]
    path_cfg = f["path_cfg"]
    helper_cfg = f["helper_cfg"]
    response_cfg = f["response_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a careful child who finds a diamond on {place.name}. It is also about {carrier_cfg.phrase}, who lost it, and a {helper_cfg.label} that helps point the way."
        ),
        (
            f"What made the story become a mystery to solve?",
            f"The mystery began when {f['hero_name']} found a diamond lying alone on the ground. A {sack_cfg.tear_word} thread, signs of a stumble, and the odd place where the diamond lay showed that someone must have lost it."
        ),
        (
            f"Why did {f['hero_name']} think someone had dropped more than one diamond?",
            f"{f['hero_name']} saw clues around the path, not just the single jewel. The torn sack and the marks near the {path_cfg.label} suggested that more bright stones had spilled when the owner stumbled."
        ),
        (
            f"How was the mystery solved?",
            f"{f['hero_name']} {response_cfg.qa_text}. Solving it took slow looking and trust in the small clues instead of a quick guess."
        ),
        (
            f"What lesson did {f['hero_name']} learn?",
            f"{f['hero_name']} learned that a glittering thing is not a gift just because you find it. Careful honesty solved the mystery and helped the person who was worried."
        ),
    ]
    if world.facts.get("owner_relieved"):
        qa.append(
            (
                f"How did the owner feel when the diamond was returned?",
                f"The owner felt deep relief and gratitude. The lost jewel mattered because it belonged with the rest of the torn sack's precious stones."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"diamond", "sack", "stumble", "mystery", "honesty", "patience"}
    path_cfg = world.facts["path_cfg"]
    if path_cfg.id in {"roots", "steps", "bridge"}:
        tags.add(path_cfg.id)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(sack: SackType, path: PathType) -> str:
    if path.roughness <= 0:
        return (
            f"(No story: {path.phrase} is too soft for a telling spill. Without a real stumble, the torn {sack.label} would leave no clear diamond trail and no strong mystery to solve.)"
        )
    if path.roughness < sack.sturdy:
        return (
            f"(No story: a {sack.label} is too sturdy for {path.label} to tear in this fairy tale. Pick a rougher place for the stumble.)"
        )
    return "(No story: this sack and path do not make a believable spilled-diamond mystery.)"


def explain_response(response_id: str) -> str:
    resp = RESPONSES[response_id]
    options = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is not an honest or sensible way to solve the mystery (sense={resp.sense} < {SENSE_MIN}). Try one of: {options}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "returned"


ASP_RULES = r"""
spill_possible(S, P) :- sack(S), path(P), sturdy(S, St), roughness(P, R), R > 0, R >= St.
sensible(R) :- response(R), sense(R, S), sense_min(M), honest(R), S >= M.
valid(Pl, C, S, P) :- place(Pl), carrier(C), sack(S), path(P), spill_possible(S, P).
outcome(returned) :- chosen_response(R), sensible(R).
#show valid/4.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CARRIERS:
        lines.append(asp.fact("carrier", cid))
    for sid, sack in SACKS.items():
        lines.append(asp.fact("sack", sid))
        lines.append(asp.fact("sturdy", sid, sack.sturdy))
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("roughness", pid, path.roughness))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        if resp.honest:
            lines.append(asp.fact("honest", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_response", params.response)
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery storyworld: a torn sack, a fallen diamond, a stumble, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--sack", choices=SACKS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and args.sack:
        if not spill_possible(SACKS[args.sack], PATHS[args.path]):
            raise StoryError(explain_rejection(SACKS[args.sack], PATHS[args.path]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.response and not RESPONSES[args.response].honest:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.carrier is None or combo[1] == args.carrier)
        and (args.sack is None or combo[2] == args.sack)
        and (args.path is None or combo[3] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, carrier_id, sack_id, path_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        carrier=carrier_id,
        sack=sack_id,
        path=path_id,
        helper=helper_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        carrier_cfg = CARRIERS[params.carrier]
        sack_cfg = SACKS[params.sack]
        path_cfg = PATHS[params.path]
        helper_cfg = HELPERS[params.helper]
        response_cfg = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not spill_possible(sack_cfg, path_cfg):
        raise StoryError(explain_rejection(sack_cfg, path_cfg))
    if response_cfg.sense < SENSE_MIN or not response_cfg.honest:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        carrier_cfg=carrier_cfg,
        sack_cfg=sack_cfg,
        path_cfg=path_cfg,
        helper_cfg=helper_cfg,
        response_cfg=response_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent_type,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="forest_path",
        carrier="peddler",
        sack="burlap",
        path="roots",
        helper="sparrow",
        response="follow",
        hero_name="Lina",
        hero_gender="girl",
        parent_type="mother",
        trait="careful",
    ),
    StoryParams(
        place="castle_road",
        carrier="queen_messenger",
        sack="velvet",
        path="steps",
        helper="fox",
        response="follow",
        hero_name="Tobin",
        hero_gender="boy",
        parent_type="father",
        trait="bright",
    ),
    StoryParams(
        place="river_lane",
        carrier="jeweler",
        sack="leather",
        path="bridge",
        helper="goat",
        response="wait_gate",
        hero_name="Mira",
        hero_gender="girl",
        parent_type="mother",
        trait="kind",
    ),
]


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    for params in CURATED:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            rc = 1
            print(f"MISMATCH in outcome for {params}: clingo={ao} python={po}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, carrier, sack, path) combos:\n")
        for place_id, carrier_id, sack_id, path_id in combos:
            print(f"  {place_id:12} {carrier_id:16} {sack_id:8} {path_id}")
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
            header = f"### {p.hero_name}: {p.sack} on {p.path} ({p.place}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
