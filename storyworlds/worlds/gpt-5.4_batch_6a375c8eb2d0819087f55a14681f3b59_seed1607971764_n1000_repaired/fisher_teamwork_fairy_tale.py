#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py
========================================================

A standalone story world for a small fairy-tale domain about a little fisher who
cannot solve a dawn problem alone and succeeds only through teamwork.

The world models:
- a child fisher with hopes, worry, trust, and gratitude
- a helpful creature or friend with useful traits
- physical things like a boat, net, path, and basket
- one concrete obstacle that must be solved by a matching helper + tool pair

The story shape is always:
1. A fairy-tale beginning and a village need
2. A grounded obstacle that blocks the fisher
3. A teamwork turn where the helper and the fisher each do a real part
4. A dawn catch and an ending image showing the village changed

Run it
------
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --place moonriver --obstacle torn_net
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --helper bear --tool shell_needle
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/fisher_teamwork_fairy_tale.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    name: str
    water: str
    bank: str
    village: str
    dawn_image: str
    catch_name: str
    catch_plural: str
    shimmer: str
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
class Obstacle:
    id: str
    label: str
    problem_line: str
    need_tag: str
    need_trait: str
    action_name: str
    solved_meter: str
    trouble_meter: str
    qa_reason: str
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
class HelperCfg:
    id: str
    label: str
    kind: str
    type: str
    traits: list[str]
    arrival: str
    teamwork_line: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    tags: set[str]
    use_line: str
    tags_for_qa: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "cast_ready": False,
            "catch_made": False,
            "teamwork": False,
            "solved": False,
        }

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


def _r_ready(world: World) -> list[str]:
    boat = world.get("boat")
    net = world.get("net")
    path = world.get("path")
    fisher = world.get("fisher")
    if boat.meters["free"] >= THRESHOLD and net.meters["whole"] >= THRESHOLD and path.meters["safe"] >= THRESHOLD:
        sig = ("ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            boat.meters["ready"] += 1
            fisher.memes["hope"] += 1
            world.facts["cast_ready"] = True
    return []


def _r_teamwork_glow(world: World) -> list[str]:
    fisher = world.get("fisher")
    helper = world.get("helper")
    if fisher.memes["worked_together"] >= THRESHOLD and helper.memes["worked_together"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            fisher.memes["trust"] += 1
            helper.memes["joy"] += 1
            world.facts["teamwork"] = True
    return []


def _r_catch(world: World) -> list[str]:
    boat = world.get("boat")
    basket = world.get("basket")
    fisher = world.get("fisher")
    if boat.meters["ready"] >= THRESHOLD and fisher.meters["cast"] >= THRESHOLD:
        sig = ("catch",)
        if sig not in world.fired:
            world.fired.add(sig)
            basket.meters["filled"] += 1
            fisher.memes["joy"] += 1
            world.facts["catch_made"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="teamwork_glow", tag="social", apply=_r_teamwork_glow),
    Rule(name="catch", tag="physical", apply=_r_catch),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "moonriver": Place(
        id="moonriver",
        name="Moonriver",
        water="the silver river",
        bank="a bank of pale reeds",
        village="Lantern Hollow",
        dawn_image="By sunrise, gold light lay across the river like a long ribbon.",
        catch_name="moonfish",
        catch_plural="moonfish",
        shimmer="their sides flashed like tiny moons",
        tags={"river", "fish"},
    ),
    "reedlake": Place(
        id="reedlake",
        name="Reedlake",
        water="the still lake",
        bank="a ring of whispering reeds",
        village="Reedbell Village",
        dawn_image="By sunrise, the lake wore a bright crown of light.",
        catch_name="sun-carp",
        catch_plural="sun-carp",
        shimmer="their scales gleamed like coins in a storybook",
        tags={"lake", "fish"},
    ),
    "starry_cove": Place(
        id="starry_cove",
        name="Starry Cove",
        water="the quiet cove",
        bank="a curve of smooth blue stones",
        village="Shellmere",
        dawn_image="By sunrise, the sea-edge shone as if someone had spilled stars there.",
        catch_name="pearl-herring",
        catch_plural="pearl-herring",
        shimmer="their bodies glinted like little pearls",
        tags={"cove", "fish"},
    ),
}

OBSTACLES = {
    "torn_net": Obstacle(
        id="torn_net",
        label="torn net",
        problem_line="the fishing net had a wide tear in it, shaped like a crooked moon",
        need_tag="stitch",
        need_trait="nimble",
        action_name="mend",
        solved_meter="whole",
        trouble_meter="torn",
        qa_reason="A torn net would let the fish slip straight back into the water.",
        tags={"net", "repair"},
    ),
    "stuck_boat": Obstacle(
        id="stuck_boat",
        label="stuck boat",
        problem_line="the little boat was wedged hard among the reeds",
        need_tag="push",
        need_trait="strong",
        action_name="free",
        solved_meter="free",
        trouble_meter="stuck",
        qa_reason="If the boat stayed stuck, the fisher could not reach the deep shining water.",
        tags={"boat", "push"},
    ),
    "misty_path": Obstacle(
        id="misty_path",
        label="misty path",
        problem_line="a blanket of pearl-gray mist covered the stone path to the landing",
        need_tag="guide",
        need_trait="careful",
        action_name="guide",
        solved_meter="safe",
        trouble_meter="foggy",
        qa_reason="Without a safe path, the fisher might slip or wander and miss the best dawn water.",
        tags={"mist", "path"},
    ),
}

HELPERS = {
    "otter": HelperCfg(
        id="otter",
        label="an otter",
        kind="character",
        type="animal",
        traits=["nimble", "playful", "bright"],
        arrival="Out popped an otter with whiskers silvered by dew.",
        teamwork_line="The otter held and twisted with quick little paws while the fisher worked.",
        tags={"otter", "animal", "friend"},
    ),
    "bear": HelperCfg(
        id="bear",
        label="a young bear",
        kind="character",
        type="animal",
        traits=["strong", "gentle", "steady"],
        arrival="From the alder shade came a young bear with kind dark eyes.",
        teamwork_line="The bear leaned its strong shoulder where the fisher pointed and shoved at the same time.",
        tags={"bear", "animal", "friend"},
    ),
    "crane": HelperCfg(
        id="crane",
        label="a white crane",
        kind="character",
        type="animal",
        traits=["careful", "graceful", "watchful"],
        arrival="Down from the pale morning sky stepped a white crane on quiet legs.",
        teamwork_line="The crane watched the safe stones and marked each one while the fisher followed.",
        tags={"crane", "animal", "friend"},
    ),
    "sister": HelperCfg(
        id="sister",
        label="an older sister",
        kind="character",
        type="girl",
        traits=["nimble", "careful", "loving"],
        arrival="Across the waking yard came the fisher's older sister with a shawl around her shoulders.",
        teamwork_line="The sister matched her hands to the fisher's hands so neither had to do the work alone.",
        tags={"sibling", "family", "friend"},
    ),
}

TOOLS = {
    "shell_needle": ToolCfg(
        id="shell_needle",
        label="shell needle",
        phrase="a shell needle and blue thread",
        tags={"stitch"},
        use_line="With the shell needle, the torn cords could be sewn tight again.",
        tags_for_qa={"needle", "repair"},
    ),
    "reed_thread": ToolCfg(
        id="reed_thread",
        label="reed thread",
        phrase="a bundle of reed thread",
        tags={"stitch"},
        use_line="The reed thread could lace the broken mesh back together.",
        tags_for_qa={"thread", "repair"},
    ),
    "willow_pole": ToolCfg(
        id="willow_pole",
        label="willow pole",
        phrase="a smooth willow pole",
        tags={"push"},
        use_line="The willow pole could pry and push where hands alone were too weak.",
        tags_for_qa={"pole", "boat"},
    ),
    "braided_rope": ToolCfg(
        id="braided_rope",
        label="braided rope",
        phrase="a braided rope",
        tags={"push", "guide"},
        use_line="The braided rope could pull a boat free or keep two friends steady on a hidden path.",
        tags_for_qa={"rope", "path", "boat"},
    ),
    "star_lantern": ToolCfg(
        id="star_lantern",
        label="star lantern",
        phrase="a star lantern",
        tags={"guide"},
        use_line="The star lantern cast a warm bead of light through the mist.",
        tags_for_qa={"lantern", "light"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tessa", "Wren", "Elin"]
BOY_NAMES = ["Tobin", "Rowan", "Finn", "Leo", "Aren", "Micah"]
TRAITS = ["patient", "brave", "gentle", "hopeful", "careful", "cheerful"]


def helper_can_solve(helper: HelperCfg, obstacle: Obstacle) -> bool:
    return obstacle.need_trait in helper.traits


def tool_can_solve(tool: ToolCfg, obstacle: Obstacle) -> bool:
    return obstacle.need_tag in tool.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for helper_id, helper in HELPERS.items():
                if not helper_can_solve(helper, obstacle):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_can_solve(tool, obstacle):
                        combos.append((place_id, obstacle_id, helper_id, tool_id))
    return combos


def explain_rejection(obstacle: Obstacle, helper: Optional[HelperCfg], tool: Optional[ToolCfg]) -> str:
    if helper is not None and not helper_can_solve(helper, obstacle):
        return (
            f"(No story: {helper.label} is not the right helper for a {obstacle.label}. "
            f"This problem needs someone {obstacle.need_trait}, so the teamwork would not honestly work.)"
        )
    if tool is not None and not tool_can_solve(tool, obstacle):
        return (
            f"(No story: {tool.label} does not solve a {obstacle.label}. "
            f"This problem needs a tool that can {obstacle.need_tag}, so the fix would feel false.)"
        )
    return "(No story: this combination does not make a reasonable teamwork solution.)"


def predict_success(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    solve_problem(sim, obstacle, narrate=False)
    sim.get("fisher").meters["cast"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim.facts["solved"],
        "ready": sim.facts["cast_ready"],
        "caught": sim.facts["catch_made"],
    }


def introduce(world: World, fisher: Entity, place: Place) -> None:
    trait = fisher.attrs.get("trait", "hopeful")
    world.say(
        f"Once, beside {place.water} near {place.village}, there lived a little fisher named {fisher.id}. "
        f"{fisher.pronoun().capitalize()} was {trait}, and each dawn {fisher.pronoun()} listened for the first hush of water against the shore."
    )
    world.say(
        f"In that village, people said the morning catch carried luck for the whole day. "
        f"So before the sky had fully brightened, {fisher.id} set out for {place.bank} with an empty basket and a hopeful heart."
    )


def village_need(world: World, fisher: Entity, place: Place) -> None:
    world.say(
        f"The ovens in {place.village} were still cool, and the lamps were burning low. "
        f"If {fisher.id} could bring back {place.catch_plural}, there would be breakfast for the neighbors and a bright supper after sunset."
    )
    fisher.memes["duty"] += 1
    fisher.memes["hope"] += 1


def find_trouble(world: World, fisher: Entity, obstacle: Obstacle) -> None:
    boat = world.get("boat")
    net = world.get("net")
    path = world.get("path")
    world.say(f"But when {fisher.id} reached the landing, {obstacle.problem_line}.")
    fisher.memes["worry"] += 1
    if obstacle.id == "torn_net":
        net.meters["torn"] += 1
        boat.meters["free"] += 1
        path.meters["safe"] += 1
    elif obstacle.id == "stuck_boat":
        boat.meters["stuck"] += 1
        net.meters["whole"] += 1
        path.meters["safe"] += 1
    elif obstacle.id == "misty_path":
        path.meters["foggy"] += 1
        net.meters["whole"] += 1
        boat.meters["free"] += 1
    world.say(
        f"{fisher.id} stood very still and tried to think. {obstacle.qa_reason}"
    )


def arrival(world: World, fisher: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(helper_cfg.arrival)
    world.say(
        f'"Why is your face so cloudy?" {helper.id if helper.type in {"girl", "boy"} else "the visitor"} asked.'
    )
    fisher.memes["trust"] += 0
    helper.memes["goodwill"] += 1


def explain_problem(world: World, fisher: Entity, obstacle: Obstacle, tool: ToolCfg) -> None:
    world.say(
        f'"I cannot fish alone this morning," said {fisher.id}. "There is a {obstacle.label}, and all I have is {tool.phrase}."'
    )
    world.say(tool.use_line)


def offer_help(world: World, fisher: Entity, helper: Entity, helper_cfg: HelperCfg, obstacle: Obstacle) -> None:
    world.say(
        f'{helper.id if helper.type in {"girl", "boy"} else helper_cfg.label.capitalize()} came closer. '
        f'"Then let us work together," {helper.pronoun()} said. "You know the fishing, and I can help where a {obstacle.need_trait} friend is needed."'
    )
    helper.memes["worked_together"] += 1
    fisher.memes["worked_together"] += 1
    propagate(world, narrate=False)


def solve_problem(world: World, obstacle: Obstacle, narrate: bool = True) -> None:
    fisher = world.get("fisher")
    helper = world.get("helper")
    helper_cfg = world.facts["helper_cfg"]
    tool = world.facts["tool_cfg"]
    boat = world.get("boat")
    net = world.get("net")
    path = world.get("path")
    if obstacle.id == "torn_net":
        net.meters["whole"] += 1
        net.meters["torn"] = 0.0
        text = (
            f"{helper_cfg.teamwork_line} {fisher.id} stitched one shining loop after another, "
            f"and soon the torn net lay whole across their knees."
        )
    elif obstacle.id == "stuck_boat":
        boat.meters["free"] += 1
        boat.meters["stuck"] = 0.0
        text = (
            f"{fisher.id} braced {tool.phrase} under the boat while {helper_cfg.teamwork_line} "
            f"With one long heave together, the boat slid free of the reeds."
        )
    else:
        path.meters["safe"] += 1
        path.meters["foggy"] = 0.0
        text = (
            f"{fisher.id} lifted {tool.phrase}, and {helper_cfg.teamwork_line} "
            f"Step by careful step, they found the landing without a slip."
        )
    world.facts["solved"] = True
    propagate(world, narrate=False)
    if narrate:
        world.say(text)


def cast_and_catch(world: World, fisher: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"When the way was ready at last, {fisher.id} cast the net while {helper.id if helper.type in {'girl', 'boy'} else helper.label} watched the water with bright, steady eyes."
    )
    fisher.meters["cast"] += 1
    propagate(world, narrate=False)
    basket = world.get("basket")
    if basket.meters["filled"] >= THRESHOLD:
        world.say(
            f"The water answered with a silver splash. Soon the basket held {place.catch_plural}, and {place.shimmer}."
        )


def return_home(world: World, fisher: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{place.dawn_image} {fisher.id} and {helper.id if helper.type in {'girl', 'boy'} else helper.label} carried the catch back toward {place.village} together."
    )
    world.say(
        f"The baker opened a window and smiled. Children came to the lane, and even the oldest neighbors said the morning seemed kinder than usual."
    )
    world.say(
        f"That evening the lamps in {place.village} burned warmly, and {fisher.id} knew a true net is not made only of cord and knots. "
        f"It is made of hands, hearts, and friends who pull together."
    )
    fisher.memes["gratitude"] += 1
    helper.memes["joy"] += 1


def tell(
    place: Place,
    obstacle: Obstacle,
    helper_cfg: HelperCfg,
    tool_cfg: ToolCfg,
    fisher_name: str = "Mira",
    fisher_gender: str = "girl",
    parent_type: str = "mother",
    fisher_trait: str = "hopeful",
) -> World:
    world = World(place=place)
    fisher = world.add(
        Entity(
            id=fisher_name,
            kind="character",
            type=fisher_gender,
            label=fisher_name,
            role="fisher",
            attrs={"trait": fisher_trait},
        )
    )
    helper_name = {
        "otter": "Otter",
        "bear": "Bear",
        "crane": "Crane",
        "sister": "Lysa",
    }[helper_cfg.id]
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            traits=list(helper_cfg.traits),
            attrs={},
        )
    )
    world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="boat", type="boat", label="little boat", attrs={}))
    world.add(Entity(id="net", type="net", label="fishing net", attrs={}))
    world.add(Entity(id="path", type="path", label="stone path", attrs={}))
    world.add(Entity(id="basket", type="basket", label="basket", attrs={}))

    world.facts.update(
        fisher=fisher,
        helper=helper,
        helper_cfg=helper_cfg,
        obstacle=obstacle,
        tool_cfg=tool_cfg,
        place=place,
        parent=world.get("parent"),
    )

    introduce(world, fisher, place)
    village_need(world, fisher, place)

    world.para()
    find_trouble(world, fisher, obstacle)
    arrival(world, fisher, helper, helper_cfg)
    explain_problem(world, fisher, obstacle, tool_cfg)
    offer_help(world, fisher, helper, helper_cfg, obstacle)

    world.para()
    solve_problem(world, obstacle, narrate=True)
    cast_and_catch(world, fisher, helper, place)

    world.para()
    return_home(world, fisher, helper, place)
    return world


@dataclass
class StoryParams:
    place: str
    obstacle: str
    helper: str
    tool: str
    fisher_name: str
    fisher_gender: str
    parent: str
    fisher_trait: str
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
    "fish": [
        (
            "What does a fisher do?",
            "A fisher catches fish from water using tools like nets, lines, or boats. A careful fisher also watches the weather and the water."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means two or more people help with the same job. Each one does a part, and together they can do more than either one could do alone."
        )
    ],
    "net": [
        (
            "Why does a torn net cause trouble?",
            "A net catches fish because its cords hold together in a pattern of little holes. If the net tears, the fish can slip right through the broken place."
        )
    ],
    "boat": [
        (
            "Why can a stuck boat be a problem?",
            "A boat that is stuck cannot move where the fisher needs to go. If it cannot reach deeper water, the fisher may miss the fish entirely."
        )
    ],
    "mist": [
        (
            "Why must people be careful in thick mist?",
            "Mist can hide stones, edges, and turns in a path. When you cannot see clearly, moving slowly and carefully helps keep you safe."
        )
    ],
    "needle": [
        (
            "What is a needle used for?",
            "A needle is used to pull thread through cloth or cord so things can be sewn together. In a fishing story, it can help mend a torn net."
        )
    ],
    "thread": [
        (
            "What does thread do?",
            "Thread is a thin strand used for sewing and tying things together. It can help join broken pieces so they hold again."
        )
    ],
    "pole": [
        (
            "What can a long pole help with near water?",
            "A long pole can push, pry, or steady something without putting your whole body into danger. Fishers often use poles to move boats in shallow places."
        )
    ],
    "rope": [
        (
            "What is rope good for?",
            "Rope helps people pull, tie, or steady things. It is useful when one person needs help moving something heavy or walking safely."
        )
    ],
    "lantern": [
        (
            "What does a lantern do in a story?",
            "A lantern gives light so people can see in dim places. In fairy tales, lantern light often stands for guidance and hope."
        )
    ],
    "otter": [
        (
            "What is an otter like?",
            "An otter is an animal that swims well and uses quick paws. In stories, otters often seem playful and nimble."
        )
    ],
    "bear": [
        (
            "Why is a bear often shown as strong in stories?",
            "Bears are large animals with heavy bodies and powerful muscles. Storytellers often use them when a job needs real strength."
        )
    ],
    "crane": [
        (
            "Why might a crane make a careful helper in a fairy tale?",
            "A crane stands lightly and watches the ground and water with sharp eyes. That makes it a good symbol for grace and careful steps."
        )
    ],
    "family": [
        (
            "How can family members help each other?",
            "Family members can share work, comfort each other, and notice when someone is struggling. Helping with a hard job is one way love becomes visible."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "fish",
    "teamwork",
    "net",
    "boat",
    "mist",
    "needle",
    "thread",
    "pole",
    "rope",
    "lantern",
    "otter",
    "bear",
    "crane",
    "family",
]


def generation_prompts(world: World) -> list[str]:
    fisher = world.facts["fisher"]
    obstacle = world.facts["obstacle"]
    place = world.facts["place"]
    helper_cfg = world.facts["helper_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old about a little fisher at {place.name} who faces a {obstacle.label} and succeeds through teamwork.',
        f"Tell a gentle fairy-tale story where {fisher.id} cannot fish at dawn alone, but {helper_cfg.label} helps using {tool_cfg.phrase}.",
        f'Write a simple story that includes the word "fisher", has a teamwork turn, and ends with a village made happier by the morning catch.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    fisher = world.facts["fisher"]
    helper = world.facts["helper"]
    helper_cfg = world.facts["helper_cfg"]
    obstacle = world.facts["obstacle"]
    tool_cfg = world.facts["tool_cfg"]
    place = world.facts["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little fisher named {fisher.id} and {helper.id if helper.type in {'girl', 'boy'} else helper_cfg.label}, who helped at dawn. They worked together beside {place.water} near {place.village}."
        ),
        (
            f"Why was {fisher.id} worried at the landing?",
            f"{fisher.id} was worried because there was a {obstacle.label}. {obstacle.qa_reason}"
        ),
        (
            f"How did the helper make a difference?",
            f"The helper did the part that needed someone {obstacle.need_trait}, and {fisher.id} did the fishing part. Because they shared the work, the problem truly changed instead of only being wished away."
        ),
        (
            "What tool did they use, and why did it matter?",
            f"They used {tool_cfg.phrase}. It mattered because that tool could {obstacle.need_tag}, which was exactly what the {obstacle.label} needed."
        ),
    ]
    if world.facts.get("catch_made"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with a real catch and a brighter village. The basket filled with {place.catch_plural} because the fisher and the helper solved the problem before casting."
            )
        )
    if world.facts.get("teamwork"):
        qa.append(
            (
                "What does the ending show about teamwork?",
                f"The ending shows that teamwork is not just standing nearby. Each friend did a different useful part, and together they made breakfast and evening light possible for the village."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fish", "teamwork"}
    obstacle = world.facts["obstacle"]
    helper_cfg = world.facts["helper_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    tags |= set(obstacle.tags)
    tags |= set(helper_cfg.tags)
    tags |= set(tool_cfg.tags_for_qa)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_help(H, O) :- helper(H), obstacle(O), needs_trait(O, T), helper_trait(H, T).
can_use(Tool, O) :- tool(Tool), obstacle(O), needs_tag(O, G), tool_tag(Tool, G).
valid(P, O, H, T) :- place(P), obstacle(O), helper(H), tool(T), can_help(H, O), can_use(T, O).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs_tag", obstacle_id, obstacle.need_tag))
        lines.append(asp.fact("needs_trait", obstacle_id, obstacle.need_trait))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for trait in sorted(helper.traits):
            lines.append(asp.fact("helper_trait", helper_id, trait))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tool_tag", tool_id, tag))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="moonriver",
        obstacle="torn_net",
        helper="otter",
        tool="shell_needle",
        fisher_name="Mira",
        fisher_gender="girl",
        parent="mother",
        fisher_trait="patient",
    ),
    StoryParams(
        place="reedlake",
        obstacle="stuck_boat",
        helper="bear",
        tool="willow_pole",
        fisher_name="Rowan",
        fisher_gender="boy",
        parent="father",
        fisher_trait="brave",
    ),
    StoryParams(
        place="starry_cove",
        obstacle="misty_path",
        helper="crane",
        tool="star_lantern",
        fisher_name="Nora",
        fisher_gender="girl",
        parent="mother",
        fisher_trait="gentle",
    ),
    StoryParams(
        place="moonriver",
        obstacle="misty_path",
        helper="sister",
        tool="braided_rope",
        fisher_name="Finn",
        fisher_gender="boy",
        parent="father",
        fisher_trait="hopeful",
    ),
    StoryParams(
        place="reedlake",
        obstacle="torn_net",
        helper="sister",
        tool="reed_thread",
        fisher_name="Lina",
        fisher_gender="girl",
        parent="mother",
        fisher_trait="cheerful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a little fisher faces a dawn problem and solves it through teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not helper_can_solve(helper, obstacle):
            raise StoryError(explain_rejection(obstacle, helper, None))
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_can_solve(tool, obstacle):
            raise StoryError(explain_rejection(obstacle, None, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, helper_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    fisher_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        helper=helper_id,
        tool=tool_id,
        fisher_name=name,
        fisher_gender=gender,
        parent=parent,
        fisher_trait=fisher_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]

    if not helper_can_solve(helper, obstacle):
        raise StoryError(explain_rejection(obstacle, helper, None))
    if not tool_can_solve(tool, obstacle):
        raise StoryError(explain_rejection(obstacle, None, tool))

    world = tell(
        place=place,
        obstacle=obstacle,
        helper_cfg=helper,
        tool_cfg=tool,
        fisher_name=params.fisher_name,
        fisher_gender=params.fisher_gender,
        parent_type=params.parent,
        fisher_trait=params.fisher_trait,
    )
    if not world.facts.get("catch_made"):
        raise StoryError("(Generation failed: the teamwork solution did not lead to a catch.)")

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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "fisher" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        if sample.world is None or not sample.world.facts.get("catch_made"):
            raise StoryError("smoke test world missing catch outcome")
        print("OK: curated smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story:
            raise StoryError("resolved-param smoke test generated empty story")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
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
        print(f"{len(combos)} compatible (place, obstacle, helper, tool) combos:\n")
        for place_id, obstacle_id, helper_id, tool_id in combos:
            print(f"  {place_id:12} {obstacle_id:11} {helper_id:8} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.fisher_name}: {p.obstacle} at {p.place} with {p.helper} and {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
