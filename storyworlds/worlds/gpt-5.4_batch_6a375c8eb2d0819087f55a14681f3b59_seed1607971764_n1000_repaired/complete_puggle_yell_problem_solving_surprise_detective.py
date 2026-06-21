#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py
=====================================================================================

A standalone storyworld for a tiny detective tale: a child detective and a
faithful puggle solve a small mystery without yelling, then uncover a happy
surprise.

The world models:

- a setting with plausible hiding spots
- a missing item the child needs to complete something
- a mover/cause that left a clue trail
- a detective tool that may be strong enough to solve the case alone

The story is driven by simulated state: the item becomes missing, clues are
noticed, the detective gathers evidence, and either solves the case alone or
gets one gentle hint from a grown-up. The ending always includes a concrete
surprise image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py
    python storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py --all
    python storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py --json
    python storyworlds/worlds/gpt-5.4/complete_puggle_yell_problem_solving_surprise_detective.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    id: str
    label: str
    opener: str
    affordances: set[str] = field(default_factory=set)
    spots: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    material: str
    shape: str
    goal: str
    need_line: str
    surprise_use: str
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
class Cause:
    id: str
    label: str
    clue_type: str
    clue_text: str
    move_text: str
    stash_text: str
    difficulty: int
    allowed_materials: set[str] = field(default_factory=set)
    allowed_shapes: set[str] = field(default_factory=set)
    settings: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    sees: set[str] = field(default_factory=set)
    bonus: int = 1
    line: str = ""
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
class Spot:
    id: str
    label: str
    phrase: str
    in_settings: set[str] = field(default_factory=set)
    fits_shapes: set[str] = field(default_factory=set)
    find_line: str = ""
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


def _r_missing_case(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    detective = world.get("detective")
    puggle = world.get("puggle")
    if item.meters["hidden"] >= THRESHOLD and ("missing_case",) not in world.fired:
        world.fired.add(("missing_case",))
        detective.memes["worry"] += 1
        detective.memes["curiosity"] += 1
        puggle.memes["alert"] += 1
    return out


def _r_observation_solves(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    detective = world.get("detective")
    need = world.facts["difficulty"]
    if detective.meters["observed"] >= need and case.meters["solved"] < THRESHOLD:
        world.fired.add(("solved_by_observation",))
        case.meters["solved"] += 1
        detective.memes["confidence"] += 1
    return out


def _r_found_item(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    item = world.get("item")
    badge = world.get("badge")
    detective = world.get("detective")
    if case.meters["solved"] >= THRESHOLD and item.meters["hidden"] >= THRESHOLD:
        sig = ("found_item",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        item.meters["hidden"] = 0.0
        item.meters["found"] += 1
        badge.meters["hidden"] = 0.0
        badge.meters["found"] += 1
        detective.memes["relief"] += 1
        detective.memes["surprise"] += 1
        detective.memes["pride"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="missing_case", tag="emotion", apply=_r_missing_case),
    Rule(name="observation_solves", tag="reasoning", apply=_r_observation_solves),
    Rule(name="found_item", tag="resolution", apply=_r_found_item),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
            elif any(sig[0] == rule.name for sig in world.fired if isinstance(sig, tuple) and sig):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def movable(cause: Cause, item: MissingItem) -> bool:
    return item.material in cause.allowed_materials and item.shape in cause.allowed_shapes


def tool_can_read(tool: Tool, cause: Cause) -> bool:
    return cause.clue_type in tool.sees


def spot_fits(setting: Setting, spot: Spot, item: MissingItem) -> bool:
    return setting.id in spot.in_settings and item.shape in spot.fits_shapes and spot.id in setting.spots


def valid_combo(setting: Setting, item: MissingItem, cause: Cause, tool: Tool, spot: Spot) -> bool:
    return (
        cause.id in setting.affordances
        and cause.id in cause.settings
        and setting.id in cause.settings
        and movable(cause, item)
        and tool_can_read(tool, cause)
        and spot_fits(setting, spot, item)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for cid, cause in CAUSES.items():
                for tid, tool in TOOLS.items():
                    for spid, spot in SPOTS.items():
                        if valid_combo(setting, item, cause, tool, spot):
                            combos.append((sid, iid, cid, tid, spid))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    cause = CAUSES[params.cause]
    return "solved_alone" if tool.bonus >= cause.difficulty else "solved_with_hint"


def predict_solution(tool: Tool, cause: Cause) -> dict:
    observed = float(tool.bonus)
    return {"observed": observed, "solves": observed >= float(cause.difficulty)}


def introduce(world: World, detective: Entity, puggle: Entity, setting: Setting) -> None:
    world.say(
        f"{setting.opener} {detective.id} liked to pretend {detective.pronoun()} was a great detective, "
        f"and {detective.pronoun('possessive')} little puggle {puggle.id} padded beside {detective.pronoun('object')} like a furry assistant."
    )


def setup_goal(world: World, detective: Entity, item_cfg: MissingItem) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"That afternoon, {detective.id} needed {item_cfg.phrase} because {detective.pronoun()} wanted to {item_cfg.goal}."
    )
    world.say(item_cfg.need_line)


def discover_missing(world: World, detective: Entity, item: Entity) -> None:
    item.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {detective.id} reached for it, {item.label} was gone."
    )
    world.say(
        f'{detective.id} opened wide eyes. "This case is not complete at all," {detective.pronoun()} whispered.'
    )


def almost_yell(world: World, detective: Entity, parent: Entity) -> None:
    detective.memes["frustration"] += 1
    world.say(
        f"For one hot second, {detective.id} wanted to yell for everyone to stop and look."
    )
    world.say(
        f"Then {detective.pronoun()} took a breath and remembered what {detective.pronoun('possessive')} {parent.label_word} always said: "
        f'"A detective thinks first."'
    )


def inspect_clue(world: World, detective: Entity, puggle: Entity, tool: Tool, cause: Cause) -> None:
    detective.meters["observed"] += tool.bonus
    puggle.memes["sniffing"] += 1
    world.say(tool.line)
    world.say(
        f"Soon {detective.id} and {puggle.id} noticed {cause.clue_text}."
    )


def deduce(world: World, detective: Entity, cause: Cause, spot: Spot) -> None:
    world.say(
        f'{detective.id} crouched low. "If I follow this clue, I will know what moved it," {detective.pronoun()} said.'
    )
    world.say(
        f"The trail pointed toward {spot.phrase}, where {cause.stash_text}."
    )


def gentle_hint(world: World, detective: Entity, parent: Entity, spot: Spot) -> None:
    detective.meters["observed"] += 1
    parent.memes["guidance"] += 1
    world.say(
        f"{detective.id} still had one piece missing in the puzzle of the case, so {detective.pronoun('possessive')} {parent.label_word} knelt down beside {detective.pronoun('object')}."
    )
    world.say(
        f'"You already found the clue," {parent.pronoun()} said softly. "Now ask where that clue would end. What is close to {spot.label}?"'
    )
    propagate(world, narrate=False)


def solve_and_find(world: World, detective: Entity, item_cfg: MissingItem, cause: Cause, spot: Spot) -> None:
    case = world.get("case")
    if case.meters["solved"] < THRESHOLD:
        propagate(world, narrate=False)
    world.say(spot.find_line)
    world.say(
        f"There lay {item_cfg.phrase}. {cause.move_text}."
    )


def reveal_surprise(world: World, detective: Entity, parent: Entity, badge: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"Beside it was {badge.label}: a gold paper badge that said, {badge.attrs['title']}."
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "That was my surprise for you," {parent.pronoun()} said. '
        f'"You solved the case without yelling, and real detectives use calm eyes."'
    )
    world.say(
        f"{detective.id} laughed, clipped the badge on, and used {item_cfg.phrase} to {item_cfg.surprise_use} at last."
    )


def ending_image(world: World, detective: Entity, puggle: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"By the end, the mystery was solved, the plan was complete, and {puggle.id} sat very straight beside Detective {detective.id}, as proud as any partner in a storybook case."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    cause: Cause,
    tool: Tool,
    spot: Spot,
    detective_name: str = "Mia",
    detective_gender: str = "girl",
    puggle_name: str = "Biscuit",
    parent_type: str = "mother",
) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    puggle = world.add(Entity(id=puggle_name, kind="character", type="dog", label="the puggle", role="sidekick"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    case = world.add(Entity(id="case", type="case", label="the case"))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label))
    badge = world.add(Entity(id="badge", type="badge", label="a shiny paper star", attrs={"title": '"Junior Detective"'}))
    place = world.add(Entity(id="place", type="place", label=setting.label))
    place.meters["quiet"] = 1.0
    badge.meters["hidden"] = 1.0

    world.facts["difficulty"] = float(cause.difficulty)
    world.facts["setting"] = setting
    world.facts["item_cfg"] = item_cfg
    world.facts["cause"] = cause
    world.facts["tool"] = tool
    world.facts["spot"] = spot
    world.facts["detective_name"] = detective_name
    world.facts["puggle_name"] = puggle_name

    introduce(world, detective, puggle, setting)
    setup_goal(world, detective, item_cfg)
    world.para()
    discover_missing(world, detective, item)
    almost_yell(world, detective, parent)

    world.para()
    inspect_clue(world, detective, puggle, tool, cause)
    deduce(world, detective, cause, spot)

    solved_alone = tool.bonus >= cause.difficulty
    if solved_alone:
        propagate(world, narrate=False)
    else:
        world.para()
        gentle_hint(world, detective, parent, spot)

    world.para()
    solve_and_find(world, detective, item_cfg, cause, spot)
    propagate(world, narrate=False)
    reveal_surprise(world, detective, parent, badge, item_cfg)
    ending_image(world, detective, puggle, item_cfg)

    world.facts.update(
        detective=detective,
        puggle=puggle,
        parent=parent,
        item=item,
        badge=badge,
        solved_alone=solved_alone,
        outcome="solved_alone" if solved_alone else "solved_with_hint",
        used_hint=not solved_alone,
    )
    return world


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        label="the playroom",
        opener="In the playroom, light lay across the rug in bright squares.",
        affordances={"puggle", "vacuum"},
        spots={"toy_chest", "blanket_fort"},
        tags={"room"},
    ),
    "kitchen": Setting(
        id="kitchen",
        label="the kitchen",
        opener="In the kitchen, chairs stood like quiet witnesses around the table.",
        affordances={"puggle", "breeze"},
        spots={"laundry_basket", "chair_cushion"},
        tags={"kitchen"},
    ),
    "garden": Setting(
        id="garden",
        label="the garden",
        opener="In the garden, every leaf seemed to hold a small secret.",
        affordances={"puggle", "breeze"},
        spots={"flower_pot", "porch_box"},
        tags={"garden"},
    ),
}

ITEMS = {
    "puzzle_piece": MissingItem(
        id="puzzle_piece",
        label="the last puzzle piece",
        phrase="the last puzzle piece",
        material="cardboard",
        shape="small",
        goal="complete a moon puzzle on the floor",
        need_line="Only one piece was missing, so everything else waited around a moon with a tiny empty bite taken from it.",
        surprise_use="complete the moon puzzle",
        tags={"puzzle"},
    ),
    "clue_card": MissingItem(
        id="clue_card",
        label="the blue clue card",
        phrase="the blue clue card",
        material="paper",
        shape="flat",
        goal="complete a homemade treasure map",
        need_line="The map already had red arrows and dotted lines, but without the blue clue card the ending made no sense at all.",
        surprise_use="complete the treasure map",
        tags={"card"},
    ),
    "ribbon_roll": MissingItem(
        id="ribbon_roll",
        label="the silver ribbon roll",
        phrase="the silver ribbon roll",
        material="cloth",
        shape="round",
        goal="complete wrapping a thank-you parcel",
        need_line="The parcel sat on the table with neat paper around it, but the top still looked plain without one shining bow.",
        surprise_use="complete the parcel with a bright bow",
        tags={"ribbon"},
    ),
}

CAUSES = {
    "puggle": Cause(
        id="puggle",
        label="the puggle",
        clue_type="pawprints",
        clue_text="tiny pawprints and one happy wiggle of fur on the floor",
        move_text="The little puggle must have picked it up, trotted away, and tucked it into a cozy place.",
        stash_text="a playful puppy might carry small things for safekeeping",
        difficulty=1,
        allowed_materials={"cardboard", "paper", "cloth"},
        allowed_shapes={"small", "flat", "round"},
        settings={"playroom", "kitchen", "garden"},
        tags={"dog", "pawprints"},
    ),
    "breeze": Cause(
        id="breeze",
        label="the breeze",
        clue_type="flutter",
        clue_text="a faint flutter by the floor and a scrap of paper twitching near the wall",
        move_text="A sneaky breeze must have slid it along until it came to rest somewhere sheltered.",
        stash_text="a small draft could push light things into a snug corner",
        difficulty=2,
        allowed_materials={"paper", "cardboard"},
        allowed_shapes={"small", "flat"},
        settings={"kitchen", "garden"},
        tags={"wind", "flutter"},
    ),
    "vacuum": Cause(
        id="vacuum",
        label="the robot vacuum",
        clue_type="wheel_line",
        clue_text="a neat wheel line and one crumb-free stripe under the furniture",
        move_text="The little robot vacuum must have nudged it along while it hummed past on its tidy path.",
        stash_text="the humming cleaner might push flat things where hands do not usually look",
        difficulty=3,
        allowed_materials={"paper", "cardboard"},
        allowed_shapes={"small", "flat"},
        settings={"playroom"},
        tags={"vacuum", "tracks"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass with a red handle",
        sees={"pawprints", "wheel_line"},
        bonus=2,
        line="Mia lifted a magnifying glass with a red handle and let it swim slowly over the floorboards.",
        tags={"magnifier"},
    ),
    "notebook": Tool(
        id="notebook",
        label="detective notebook",
        phrase="a tiny detective notebook",
        sees={"pawprints", "flutter"},
        bonus=1,
        line="Mia opened a tiny detective notebook and wrote down every little sign before looking again with careful eyes.",
        tags={"notebook"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        sees={"wheel_line", "flutter"},
        bonus=3,
        line="Mia clicked on a small flashlight and swept the beam low, making dust, tracks, and hidden corners stand out.",
        tags={"flashlight"},
    ),
}

SPOTS = {
    "toy_chest": Spot(
        id="toy_chest",
        label="the toy chest",
        phrase="the toy chest",
        in_settings={"playroom"},
        fits_shapes={"small", "flat", "round"},
        find_line="At the bottom edge of the toy chest, tucked just behind a wooden wheel, something glimmered.",
        tags={"storage"},
    ),
    "blanket_fort": Spot(
        id="blanket_fort",
        label="the blanket fort",
        phrase="the blanket fort",
        in_settings={"playroom"},
        fits_shapes={"small", "flat", "round"},
        find_line="Inside the blanket fort, where the air smelled soft and warm, a small shape waited on the rug.",
        tags={"fort"},
    ),
    "laundry_basket": Spot(
        id="laundry_basket",
        label="the laundry basket",
        phrase="the laundry basket",
        in_settings={"kitchen"},
        fits_shapes={"small", "flat", "round"},
        find_line="Peeking beside the laundry basket, under one striped towel, was the missing thing itself.",
        tags={"basket"},
    ),
    "chair_cushion": Spot(
        id="chair_cushion",
        label="the chair cushion",
        phrase="the chair cushion",
        in_settings={"kitchen"},
        fits_shapes={"small", "flat"},
        find_line="Under the chair cushion, where crumbs and secrets both liked to hide, the missing piece waited quietly.",
        tags={"chair"},
    ),
    "flower_pot": Spot(
        id="flower_pot",
        label="the flower pot",
        phrase="the flower pot",
        in_settings={"garden"},
        fits_shapes={"small", "flat", "round"},
        find_line="Behind the flower pot, safe from the path, the missing thing lay in a patch of shade.",
        tags={"garden"},
    ),
    "porch_box": Spot(
        id="porch_box",
        label="the porch box",
        phrase="the porch box",
        in_settings={"garden"},
        fits_shapes={"small", "flat", "round"},
        find_line="Inside the porch box, beside one tiny garden glove, something important shone back.",
        tags={"porch"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Anna", "Ava", "Ella"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Noah"]
PUGGLE_NAMES = ["Biscuit", "Bean", "Pebble", "Waffles"]
TRAITS = ["careful", "bright", "patient", "curious"]


@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    tool: str
    spot: str
    detective_name: str
    detective_gender: str
    puggle_name: str
    parent: str
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


CURATED = [
    StoryParams(
        setting="playroom",
        item="puzzle_piece",
        cause="puggle",
        tool="notebook",
        spot="blanket_fort",
        detective_name="Mia",
        detective_gender="girl",
        puggle_name="Biscuit",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="kitchen",
        item="clue_card",
        cause="breeze",
        tool="notebook",
        spot="chair_cushion",
        detective_name="Theo",
        detective_gender="boy",
        puggle_name="Bean",
        parent="father",
        trait="bright",
    ),
    StoryParams(
        setting="playroom",
        item="clue_card",
        cause="vacuum",
        tool="magnifier",
        spot="toy_chest",
        detective_name="Nora",
        detective_gender="girl",
        puggle_name="Pebble",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        setting="garden",
        item="ribbon_roll",
        cause="puggle",
        tool="magnifier",
        spot="porch_box",
        detective_name="Ben",
        detective_gender="boy",
        puggle_name="Waffles",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        setting="garden",
        item="clue_card",
        cause="breeze",
        tool="flashlight",
        spot="flower_pot",
        detective_name="Ava",
        detective_gender="girl",
        puggle_name="Bean",
        parent="mother",
        trait="careful",
    ),
]


def explain_rejection(
    setting: Optional[Setting],
    item: Optional[MissingItem],
    cause: Optional[Cause],
    tool: Optional[Tool],
    spot: Optional[Spot],
) -> str:
    if setting and cause and setting.id not in cause.settings:
        return f"(No story: {cause.label} does not make this kind of clue in {setting.label}.)"
    if setting and cause and cause.id not in setting.affordances:
        return f"(No story: {setting.label} does not support the clue path for {cause.label}.)"
    if cause and item and not movable(cause, item):
        return f"(No story: {cause.label} would not reasonably move {item.phrase}.)"
    if tool and cause and not tool_can_read(tool, cause):
        return f"(No story: {tool.phrase} is not a good way to read a {cause.clue_type} clue.)"
    if setting and spot and item and not spot_fits(setting, spot, item):
        return f"(No story: {spot.phrase} does not fit both {setting.label} and {item.phrase}.)"
    return "(No story: that combination does not make a reasonable detective case.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    puggle = f["puggle"]
    item_cfg = f["item_cfg"]
    setting = f["setting"]
    cause = f["cause"]
    if f["outcome"] == "solved_alone":
        turn = "solves the case alone by following clues"
    else:
        turn = "follows clues carefully and then uses one gentle hint to solve the case"
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "complete", "puggle", and "yell".',
        f"Tell a gentle mystery set in {setting.label} where a child detective and a puggle notice that {item_cfg.phrase} is missing and {turn}.",
        f"Write a story where {detective.id} stays calm instead of choosing to yell, studies a clue left by {cause.label}, and finds both the missing item and a surprise reward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    puggle = f["puggle"]
    parent = f["parent"]
    item_cfg = f["item_cfg"]
    cause = f["cause"]
    tool = f["tool"]
    spot = f["spot"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {puggle.id}, the puggle who helped on the case. They worked together to find {item_cfg.phrase}.",
        ),
        (
            f"Why did {detective.id} care about the missing item?",
            f"{detective.id} needed {item_cfg.phrase} to {item_cfg.goal}. Without it, the plan could not be complete.",
        ),
        (
            f"Why did {detective.id} decide not to yell?",
            f"{detective.id} felt frustrated for a moment, but stopped before yelling. {detective.pronoun().capitalize()} remembered that detectives think first, so being calm helped {detective.pronoun('object')} notice the clue.",
        ),
        (
            f"What clue helped solve the mystery?",
            f"The clue was {cause.clue_text}. {detective.id} used {tool.phrase} to study it and figure out where it led.",
        ),
    ]
    if f["outcome"] == "solved_alone":
        qa.append(
            (
                f"How did {detective.id} solve the case?",
                f"{detective.id} solved it alone by following the clue trail to {spot.phrase}. {detective.pronoun().capitalize()} had gathered enough evidence to understand what moved the item and where it had ended up.",
            )
        )
    else:
        qa.append(
            (
                f"Did anyone help {detective.id} at the end?",
                f"Yes. {detective.id}'s {parent.label_word} gave one gentle hint instead of taking over the case. That hint helped {detective.pronoun('object')} connect the last idea and look in the right place.",
            )
        )
    qa.append(
        (
            "What was the surprise at the end?",
            f"Beside the missing item was a gold paper badge that named {detective.id} a Junior Detective. The surprise mattered because it showed that staying calm and solving the problem carefully had been noticed.",
        )
    )
    return qa


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tries to solve a problem by thinking. Detectives notice small details that other people might miss.",
        )
    ],
    "puggle": [
        (
            "What is a puggle?",
            "A puggle is a small dog that is usually lively and curious. A curious dog can notice smells, tracks, and hidden things very quickly.",
        )
    ],
    "pawprints": [
        (
            "What can pawprints tell you?",
            "Pawprints can show where an animal walked. If they lead toward one spot, they can help you guess where something went.",
        )
    ],
    "wind": [
        (
            "How can a breeze move something light?",
            "A breeze can push paper or other light things across the floor or ground. Small, flat objects are easiest for moving air to carry.",
        )
    ],
    "vacuum": [
        (
            "How can a robot vacuum move an object by accident?",
            "A robot vacuum rolls along the floor and can bump light things with its edge. If an object is flat and small, the machine might nudge it into a corner.",
        )
    ],
    "magnifier": [
        (
            "What is a magnifying glass for?",
            "A magnifying glass makes tiny details look bigger. That helps you see little tracks or marks more clearly.",
        )
    ],
    "flashlight": [
        (
            "Why can a flashlight help you find clues?",
            "A flashlight makes dark corners brighter and helps lines, dust, or hidden shapes stand out. Good light can turn a hard search into an easy one.",
        )
    ],
    "notebook": [
        (
            "Why do detectives use notebooks?",
            "A notebook helps you remember every clue in order. Writing things down keeps your thinking neat and careful.",
        )
    ],
    "calm": [
        (
            "Why is staying calm useful when solving a problem?",
            "When you stay calm, it is easier to notice details and make a good plan. Yelling can make your thoughts feel jumbled.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you were not expecting that suddenly happens or is discovered. A happy surprise often makes the ending feel warm and special.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "puggle", "pawprints", "wind", "vacuum", "magnifier", "flashlight", "notebook", "calm", "surprise"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "puggle", "calm", "surprise"}
    cause = world.facts["cause"]
    tool = world.facts["tool"]
    if "pawprints" in cause.tags:
        tags.add("pawprints")
    if "wind" in cause.tags:
        tags.add("wind")
    if "vacuum" in cause.tags:
        tags.add("vacuum")
    if tool.id == "magnifier":
        tags.add("magnifier")
    if tool.id == "flashlight":
        tags.add("flashlight")
    if tool.id == "notebook":
        tags.add("notebook")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A reasonable case needs a setting that affords the mover, a spot in that
% setting that fits the item, and a tool that can detect the mover's clue.
valid(S, I, C, T, Sp) :-
    setting(S), item(I), cause(C), tool(T), spot(Sp),
    affords(S, C),
    cause_setting(C, S),
    movable(C, I),
    clue_of(C, Cl),
    sees(T, Cl),
    spot_setting(Sp, S),
    fits(Sp, I).

solved_alone(T, C) :-
    tool_bonus(T, B),
    cause_difficulty(C, D),
    B >= D.

solved_with_hint(T, C) :-
    valid(_, _, C, T, _),
    not solved_alone(T, C).

outcome(solved_alone) :- chosen_tool(T), chosen_cause(C), solved_alone(T, C).
outcome(solved_with_hint) :- chosen_tool(T), chosen_cause(C), not solved_alone(T, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cause in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, cause))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("material", iid, item.material))
        lines.append(asp.fact("shape", iid, item.shape))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("clue_of", cid, cause.clue_type))
        lines.append(asp.fact("cause_difficulty", cid, cause.difficulty))
        for sid in sorted(cause.settings):
            lines.append(asp.fact("cause_setting", cid, sid))
        for iid, item in ITEMS.items():
            if movable(cause, item):
                lines.append(asp.fact("movable", cid, iid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_bonus", tid, tool.bonus))
        for clue in sorted(tool.sees):
            lines.append(asp.fact("sees", tid, clue))
    for spid, spot in SPOTS.items():
        lines.append(asp.fact("spot", spid))
        for sid in sorted(spot.in_settings):
            lines.append(asp.fact("spot_setting", spid, sid))
        for iid, item in ITEMS.items():
            if item.shape in spot.fits_shapes:
                lines.append(asp.fact("fits", spid, iid))
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
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_cause", params.cause),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle detective-story world: a child, a puggle, a missing item, and a surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--puggle-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    item = ITEMS.get(args.item) if args.item else None
    cause = CAUSES.get(args.cause) if args.cause else None
    tool = TOOLS.get(args.tool) if args.tool else None
    spot = SPOTS.get(args.spot) if args.spot else None

    explicitly_complete = all(x is not None for x in (setting, item, cause, tool, spot))
    if explicitly_complete and not valid_combo(setting, item, cause, tool, spot):
        raise StoryError(explain_rejection(setting, item, cause, tool, spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.tool is None or combo[3] == args.tool)
        and (args.spot is None or combo[4] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chosen = rng.choice(combos)
    setting_id, item_id, cause_id, tool_id, spot_id = chosen
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    puggle_name = args.puggle_name or rng.choice(PUGGLE_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        tool=tool_id,
        spot=spot_id,
        detective_name=name,
        detective_gender=gender,
        puggle_name=puggle_name,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        cause = CAUSES[params.cause]
        tool = TOOLS[params.tool]
        spot = SPOTS[params.spot]
    except KeyError as exc:
        raise StoryError(f"(No story: unknown parameter value {exc!s}.)") from exc

    if not valid_combo(setting, item, cause, tool, spot):
        raise StoryError(explain_rejection(setting, item, cause, tool, spot))

    world = tell(
        setting=setting,
        item_cfg=item,
        cause=cause,
        tool=tool,
        spot=spot,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        puggle_name=params.puggle_name,
        parent_type=params.parent,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(25):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_sample = generate(smoke_params)
        emit(smoke_sample, trace=False, qa=False, header="")
        print("\nOK: smoke-test generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify mode should surface failures
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

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
        print(f"{len(combos)} compatible (setting, item, cause, tool, spot) combos:\n")
        for row in combos:
            print("  " + "  ".join(f"{part:12}" for part in row))
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
            header = (
                f"### {p.detective_name}: {p.item} in {p.setting} "
                f"({p.cause}, {p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
