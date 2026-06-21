#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py
===================================================================

A standalone story world for a child-facing whodunit: someone keeps emptying the
backyard bird feeder, and a child sets out to solve the mystery. The story is a
small quest with inner-monologue beats, concrete clues, a reasonableness gate,
and an ASP twin that agrees with the Python world model.

Run it
------
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --culprit squirrel
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --feeder tube
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --helper grandpa
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/feeder_quest_inner_monologue_whodunit.py --verify
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
SOLVABLE_MIN = 2
CURIOUS_TRAITS = {"careful", "curious", "patient", "observant"}


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
        female = {"girl", "mother", "grandma", "woman", "aunt"}
        male = {"boy", "father", "grandpa", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandma": "grandma",
            "grandpa": "grandpa",
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
class Feeder:
    id: str
    label: str
    phrase: str
    clue: str
    access: set[str] = field(default_factory=set)
    spill_risk: int = 1
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
class Culprit:
    id: str
    label: str
    phrase: str
    track: str
    sign: str
    method: str
    likes: str
    movement: str
    leaves_shells: bool = False
    climbs: bool = False
    pecks: bool = False
    solvable: int = 3
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
    watch_spot: str
    ground: str
    tree: bool = False
    roof: bool = False
    fence: bool = False
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
    type: str
    phrase: str
    advice: str
    comfort: str
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
class Fix:
    id: str
    label: str
    phrase: str
    needs_tree: bool = False
    stops: set[str] = field(default_factory=set)
    sense: int = 3
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
        self.history: list[str] = []

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

    def remember(self, item: str) -> None:
        self.history.append(item)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
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


def _r_empty_feeder(world: World) -> list[str]:
    feeder = world.get("feeder")
    culprit = world.get("culprit")
    if culprit.meters["visited"] < THRESHOLD:
        return []
    sig = ("empty_feeder", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    feeder.meters["seed_missing"] += 1
    world.remember("feeder_emptied")
    return []


def _r_ground_clue(world: World) -> list[str]:
    feeder = world.get("feeder")
    culprit = world.get("culprit")
    place = world.get("place")
    if feeder.meters["seed_missing"] < THRESHOLD:
        return []
    sig = ("ground_clue", culprit.id, place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["disturbed_ground"] += 1
    world.facts["ground_clue"] = culprit.attrs["track"]
    world.remember("ground_clue_found")
    return []


def _r_tree_clue(world: World) -> list[str]:
    culprit = world.get("culprit")
    place = world.get("place")
    if culprit.attrs.get("climbs") and place.attrs.get("tree"):
        sig = ("tree_clue", culprit.id, place.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        place.meters["tree_clue"] += 1
        world.facts["tree_clue"] = "scratch marks on the bark"
        world.remember("tree_clue_found")
    return []


def _r_shell_clue(world: World) -> list[str]:
    culprit = world.get("culprit")
    place = world.get("place")
    if not culprit.attrs.get("leaves_shells"):
        return []
    sig = ("shell_clue", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["shells"] += 1
    world.facts["shell_clue"] = "tiny cracked seed shells"
    world.remember("shell_clue_found")
    return []


def _r_child_connects(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["thinking"] < THRESHOLD:
        return []
    if world.get("feeder").meters["seed_missing"] < THRESHOLD:
        return []
    clue_count = len(world.facts.get("clues", []))
    if clue_count < 2:
        return []
    sig = ("connects", clue_count)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["confidence"] += 1
    child.memes["wonder"] += 1
    world.remember("child_connected_clues")
    return []


CAUSAL_RULES = [
    Rule(name="empty_feeder", tag="physical", apply=_r_empty_feeder),
    Rule(name="ground_clue", tag="physical", apply=_r_ground_clue),
    Rule(name="tree_clue", tag="physical", apply=_r_tree_clue),
    Rule(name="shell_clue", tag="physical", apply=_r_shell_clue),
    Rule(name="child_connects", tag="social", apply=_r_child_connects),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        before = len(world.fired)
        # rules may only mutate state
        if len(world.fired) != before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def can_reach(feeder: Feeder, culprit: Culprit, place: Place) -> bool:
    if culprit.id not in feeder.access:
        return False
    if culprit.climbs and place.tree:
        return True
    if culprit.pecks:
        return True
    if culprit.id == "raccoon" and place.fence:
        return True
    return culprit.id == "cat" and place.roof


def sensible_fix(place: Place, culprit: Culprit, fix: Fix) -> bool:
    if fix.sense < SOLVABLE_MIN:
        return False
    if culprit.id not in fix.stops:
        return False
    if fix.needs_tree and not place.tree:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for feeder_id, feeder in FEEDERS.items():
        for culprit_id, culprit in CULPRITS.items():
            for place_id, place in PLACES.items():
                if can_reach(feeder, culprit, place):
                    combos.append((feeder_id, culprit_id, place_id))
    return combos


def helpful_fixes(place: Place, culprit: Culprit) -> list[str]:
    return sorted(
        fix_id for fix_id, fix in FIXES.items()
        if sensible_fix(place, culprit, fix)
    )


@dataclass
class StoryParams:
    feeder: str
    culprit: str
    place: str
    helper: str
    fix: str
    child_name: str
    child_gender: str
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


def introduce(world: World, child: Entity, helper: Entity, feeder: Feeder, place: Place) -> None:
    child.memes["care"] += 1
    world.say(
        f"Every morning, {child.id} liked to peek into the {place.label} and check {helper.label_word}'s {feeder.label}."
    )
    world.say(
        f"The little feeder hung by {feeder.clue}, and bright birds usually fluttered there before breakfast."
    )


def mystery_appears(world: World, child: Entity, feeder_ent: Entity) -> None:
    feeder_ent.meters["full"] = 0.0
    feeder_ent.meters["empty"] += 1
    child.memes["surprise"] += 1
    world.say(
        f"But three mornings in a row, the feeder was empty long before the birds finished their songs."
    )
    world.say(
        f'{child.id} put both hands on the porch rail. "That is strange," {child.pronoun()} whispered.'
    )


def inner_monologue_start(world: World, child: Entity, culprit: Culprit) -> None:
    child.memes["thinking"] += 1
    world.say(
        f'Inside, {child.id} had a detective thought: "Someone is sneaking seed away. Was it the wind? Was it a hungry visitor? I have to find out."'
    )
    world.facts["suspects"] = [c.label for c in CULPRITS.values() if c.id != culprit.id][:2] + [culprit.label]
    world.remember("mystery_named")


def ask_for_quest(world: World, child: Entity, helper: Entity) -> None:
    helper.memes["warmth"] += 1
    world.say(
        f'{child.id} hurried to {helper.label_word} and said, "May I go on a clue-finding quest before we fill it again?"'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "{helper.advice}"'
    )
    world.remember("quest_begun")


def culprit_visit(world: World) -> None:
    culprit = world.get("culprit")
    culprit.meters["visited"] += 1
    propagate(world, narrate=False)


def inspect_ground(world: World, child: Entity, place: Place) -> None:
    child.memes["thinking"] += 1
    clue = world.facts.get("ground_clue")
    if clue:
        world.facts.setdefault("clues", []).append(clue)
        world.say(
            f"First, {child.id} knelt by the {place.ground} under the feeder and found {clue}."
        )
        world.say(
            f'In {child.pronoun("possessive")} head, a new thought clicked: "Those marks were made on purpose. This was no gust of wind."'
        )
    world.remember("ground_checked")
    propagate(world, narrate=False)


def inspect_nearby(world: World, child: Entity, place: Place, culprit: Culprit) -> None:
    child.memes["thinking"] += 1
    lines: list[str] = []
    if world.facts.get("tree_clue"):
        clue = world.facts["tree_clue"]
        world.facts.setdefault("clues", []).append(clue)
        lines.append(
            f"Next, {child.id} looked up the trunk nearby and saw {clue}."
        )
    if world.facts.get("shell_clue"):
        clue = world.facts["shell_clue"]
        world.facts.setdefault("clues", []).append(clue)
        lines.append(
            f"Then {child.pronoun()} spotted {clue} on the porch step."
        )
    if not lines:
        lines.append(
            f"{child.id} checked the fence and the porch, but the best clue was how the feeder swayed as if a small body had clung to it."
        )
        world.facts.setdefault("clues", []).append(culprit.sign)
    for line in lines:
        world.say(line)
    world.say(
        f'Now {child.id} thought, "I know this pattern. One clue says where the visitor stood, and another says how it moved."'
    )
    world.remember("nearby_checked")
    propagate(world, narrate=False)


def decide_culprit(world: World, child: Entity, culprit: Culprit, helper: Entity) -> None:
    child.memes["thinking"] += 1
    child.memes["certainty"] += 1
    world.facts["solution"] = culprit.label
    world.say(
        f'{child.id} ran back to {helper.label_word}. "I solved it," {child.pronoun()} said. "The seed thief was {culprit.phrase}."'
    )
    world.say(
        f'{helper.label_word.capitalize()} bent down. "{helper.comfort}"'
    )
    world.say(
        f'{child.id} explained that the clues matched {culprit.method}. That was why the feeder kept going empty before the birds had their turn.'
    )
    world.remember("culprit_named")


def fix_problem(world: World, child: Entity, helper: Entity, culprit: Culprit, fix: Fix) -> None:
    world.facts["fix_used"] = fix.label
    world.get("feeder").meters["protected"] += 1
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Together they {fix.phrase}."
    )
    world.say(
        f'That evening, {child.id} watched from the window and thought, "Quest finished. Mystery solved. Now the birds can eat in peace."'
    )
    world.say(
        f"In the morning, {culprit.label} visited again, but this time it could not steal the seed. The feeder rocked a little, and then the birds came back."
    )
    world.remember("problem_fixed")


def tell(
    feeder: Feeder,
    culprit_cfg: Culprit,
    place_cfg: Place,
    helper_cfg: Helper,
    fix_cfg: Fix,
    child_name: str = "Nora",
    child_gender: str = "girl",
    trait: str = "observant",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.phrase,
        role="helper",
        traits=["calm"],
        attrs={},
    ))
    feeder_ent = world.add(Entity(
        id="feeder",
        kind="thing",
        type="feeder",
        label=feeder.label,
        role="feeder",
        attrs={"clue": feeder.clue, "access": set(feeder.access)},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="animal",
        label=culprit_cfg.label,
        role="culprit",
        attrs={
            "track": culprit_cfg.track,
            "sign": culprit_cfg.sign,
            "method": culprit_cfg.method,
            "likes": culprit_cfg.likes,
            "movement": culprit_cfg.movement,
            "leaves_shells": culprit_cfg.leaves_shells,
            "climbs": culprit_cfg.climbs,
            "pecks": culprit_cfg.pecks,
        },
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place_cfg.label,
        role="place",
        attrs={
            "tree": place_cfg.tree,
            "roof": place_cfg.roof,
            "fence": place_cfg.fence,
        },
    ))

    world.facts["clues"] = []
    world.facts["feeder_cfg"] = feeder
    world.facts["culprit_cfg"] = culprit_cfg
    world.facts["place_cfg"] = place_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["fix_cfg"] = fix_cfg
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["feeder"] = feeder_ent
    world.facts["culprit"] = culprit
    world.facts["place"] = place
    world.facts["trait"] = trait

    feeder_ent.meters["full"] = 1.0
    feeder_ent.meters["empty"] = 0.0
    feeder_ent.meters["seed_missing"] = 0.0
    culprit.meters["visited"] = 0.0
    place.meters["disturbed_ground"] = 0.0
    place.meters["tree_clue"] = 0.0
    place.meters["shells"] = 0.0
    child.memes["thinking"] = 0.0
    child.memes["certainty"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["relief"] = 0.0
    helper.memes["warmth"] = 0.0
    helper.memes["pride"] = 0.0

    introduce(world, child, helper, feeder, place_cfg)
    mystery_appears(world, child, feeder_ent)

    world.para()
    inner_monologue_start(world, child, culprit_cfg)
    ask_for_quest(world, child, helper)

    culprit_visit(world)
    world.para()
    inspect_ground(world, child, place_cfg)
    inspect_nearby(world, child, place_cfg, culprit_cfg)

    world.para()
    decide_culprit(world, child, culprit_cfg, helper)
    fix_problem(world, child, helper, culprit_cfg, fix_cfg)

    world.facts["clue_count"] = len(world.facts.get("clues", []))
    world.facts["solved"] = child.memes["certainty"] >= THRESHOLD
    return world


FEEDERS = {
    "tube": Feeder(
        id="tube",
        label="tube feeder",
        phrase="a clear tube feeder",
        clue="the maple branch",
        access={"squirrel", "woodpecker"},
        spill_risk=1,
        tags={"feeder", "birdseed"},
    ),
    "tray": Feeder(
        id="tray",
        label="tray feeder",
        phrase="a flat tray feeder",
        clue="the porch hook",
        access={"squirrel", "raccoon", "cat"},
        spill_risk=2,
        tags={"feeder", "birdseed"},
    ),
    "house": Feeder(
        id="house",
        label="little house feeder",
        phrase="a little house-shaped feeder",
        clue="the fence post",
        access={"squirrel", "woodpecker", "raccoon"},
        spill_risk=1,
        tags={"feeder", "birdseed"},
    ),
}

CULPRITS = {
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        phrase="a squirrel",
        track="tiny paw prints in the soft dirt",
        sign="nibbled seeds and a swishing tail shadow",
        method="climbing up the tree, leaping close, and hanging from the feeder",
        likes="sunflower seeds",
        movement="scrambled and twitched",
        leaves_shells=True,
        climbs=True,
        pecks=False,
        solvable=3,
        tags={"squirrel", "tracks"},
    ),
    "woodpecker": Culprit(
        id="woodpecker",
        label="woodpecker",
        phrase="a woodpecker",
        track="little hopping marks near the post",
        sign="a few pecked seed bits",
        method="landing neatly, pecking hard, and knocking extra seed free",
        likes="suet and seeds",
        movement="hopped and tapped",
        leaves_shells=False,
        climbs=False,
        pecks=True,
        solvable=2,
        tags={"bird", "pecking"},
    ),
    "raccoon": Culprit(
        id="raccoon",
        label="raccoon",
        phrase="a raccoon",
        track="hand-shaped prints in the mud",
        sign="the lid nudged crooked",
        method="reaching from the fence at night and prying seed loose",
        likes="easy snacks",
        movement="crept and pulled",
        leaves_shells=False,
        climbs=False,
        pecks=False,
        solvable=3,
        tags={"raccoon", "tracks"},
    ),
    "cat": Culprit(
        id="cat",
        label="neighbor's cat",
        phrase="the neighbor's cat",
        track="soft round paw prints",
        sign="a tuft of orange fur on the rail",
        method="jumping from the shed roof and bumping the feeder while chasing birds",
        likes="fluttering birds more than seed",
        movement="slunk and pounced",
        leaves_shells=False,
        climbs=False,
        pecks=False,
        solvable=2,
        tags={"cat", "pawprints"},
    ),
}

PLACES = {
    "maple_yard": Place(
        id="maple_yard",
        label="backyard maple corner",
        phrase="the backyard maple corner",
        watch_spot="the kitchen window",
        ground="soft dirt",
        tree=True,
        roof=False,
        fence=False,
        tags={"tree", "yard"},
    ),
    "porch_step": Place(
        id="porch_step",
        label="front porch",
        phrase="the front porch",
        watch_spot="the hall window",
        ground="brick step",
        tree=False,
        roof=True,
        fence=False,
        tags={"porch"},
    ),
    "garden_fence": Place(
        id="garden_fence",
        label="garden fence",
        phrase="the garden fence",
        watch_spot="the back door",
        ground="muddy patch",
        tree=False,
        roof=False,
        fence=True,
        tags={"fence", "garden"},
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        type="grandma",
        phrase="the kind grandma",
        advice="A good detective looks slowly and tells the truth of every clue.",
        comfort="Then tell me every clue in order, and we will see what story they make together.",
        tags={"family"},
    ),
    "grandpa": Helper(
        id="grandpa",
        type="grandpa",
        phrase="the patient grandpa",
        advice="Mysteries grow smaller when you notice little things.",
        comfort="Start with what the ground says, then what the feeder says.",
        tags={"family"},
    ),
    "mother": Helper(
        id="mother",
        type="mother",
        phrase="the smiling mom",
        advice="Go step by step. The best guess is the one the clues can hold up.",
        comfort="You did not just guess. You paid attention, and that is different.",
        tags={"family"},
    ),
    "father": Helper(
        id="father",
        type="father",
        phrase="the calm dad",
        advice="Ask what happened first, and then what had to happen next.",
        comfort="Your clues fit together like puzzle pieces.",
        tags={"family"},
    ),
}

FIXES = {
    "baffle": Fix(
        id="baffle",
        label="squirrel baffle",
        phrase="slid a shiny squirrel baffle onto the pole below the feeder",
        needs_tree=False,
        stops={"squirrel", "raccoon"},
        sense=3,
        tags={"fix", "pole"},
    ),
    "higher_hook": Fix(
        id="higher_hook",
        label="higher hook",
        phrase="moved the feeder to a higher hook farther from the fence and roof",
        needs_tree=False,
        stops={"cat", "raccoon"},
        sense=3,
        tags={"fix", "distance"},
    ),
    "tree_guard": Fix(
        id="tree_guard",
        label="tree guard",
        phrase="wrapped a smooth guard around the trunk so climbing feet could not grip it",
        needs_tree=True,
        stops={"squirrel"},
        sense=3,
        tags={"fix", "tree"},
    ),
    "suet_corner": Fix(
        id="suet_corner",
        label="separate suet corner",
        phrase="hung a suet cake on the far side of the yard so the pecking visitor had another place to eat",
        needs_tree=False,
        stops={"woodpecker"},
        sense=3,
        tags={"fix", "suet"},
    ),
    "scare_shout": Fix(
        id="scare_shout",
        label="scare shout",
        phrase="stood by the door and shouted every time something came near",
        needs_tree=False,
        stops={"squirrel", "cat", "raccoon", "woodpecker"},
        sense=1,
        tags={"fix"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Jack", "Finn"]
TRAITS = ["careful", "curious", "patient", "observant", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    culprit_cfg = f["culprit_cfg"]
    feeder = f["feeder_cfg"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "feeder" and follows a child on a clue-finding quest.',
        f"Tell a gentle mystery where {child.id} uses inner monologue to solve why a {feeder.label} keeps going empty, with help from {helper.label_word}.",
        f"Write a story where the culprit turns out to be {culprit_cfg.phrase}, and the ending shows a kind fix that lets the birds eat again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    culprit_cfg = f["culprit_cfg"]
    feeder = f["feeder_cfg"]
    place = f["place_cfg"]
    fix = f["fix_cfg"]
    clues = list(f.get("clues", []))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to solve the mystery of the empty feeder, and {helper.label_word}, who helped in a calm way."
        ),
        (
            "What was the mystery?",
            f"The feeder kept going empty before the birds were done eating. That made {child.id} wonder whether something sneaky was visiting it first."
        ),
        (
            f"Why did {child.id} go on a quest?",
            f"{child.id} wanted to find the truth instead of guessing. {helper.label_word.capitalize()} gave permission to look for clues carefully, so the search became a little quest."
        ),
    ]
    if clues:
        qa.append((
            f"What clues helped {child.id} solve the whodunit?",
            f"{child.id} found {', and '.join(clues[:2])}{',' if len(clues) > 2 else ''}{' and ' + clues[2] if len(clues) > 2 else ''}. Those clues matched how {culprit_cfg.label} moves and reaches the feeder."
        ))
    qa.append((
        f"How did {child.id} know who the culprit was?",
        f"{child.id} did not just make a wild guess. The clues around the {place.label} fit {culprit_cfg.phrase} and fit {culprit_cfg.label} better than anything else."
    ))
    qa.append((
        "How did the story end?",
        f"Together they used {fix.label} to protect the feeder, and the birds could eat again in the morning. The ending proves the mystery was solved because the same problem did not happen the next day."
    ))
    return qa


KNOWLEDGE = {
    "feeder": [
        ("What is a bird feeder?",
         "A bird feeder is a place where people put birdseed so birds can stop and eat. It helps birds find food, especially in yards and gardens."),
    ],
    "birdseed": [
        ("Why do birds visit a feeder?",
         "Birds visit a feeder because it has seeds or other food they like. A feeder can be an easy place for them to eat."),
    ],
    "squirrel": [
        ("Why might a squirrel climb to a feeder?",
         "Squirrels love seeds and nuts, so a feeder can look like a snack stand to them. They are good climbers and can reach places birds use."),
    ],
    "raccoon": [
        ("Why do raccoons get into things at night?",
         "Raccoons are curious animals that look for easy food, often after dark. Their front paws can grab and pull at lids and containers."),
    ],
    "cat": [
        ("Why might a cat bother birds near a feeder?",
         "Cats notice fluttering movement very quickly. A feeder can attract birds, and that can attract a cat too."),
    ],
    "bird": [
        ("What does a woodpecker do with its beak?",
         "A woodpecker pecks with its strong beak to reach food and tap on wood. That pecking can also knock little bits loose."),
    ],
    "tracks": [
        ("What can tracks tell a detective?",
         "Tracks can show who walked somewhere and how they moved. They are clues because different animals leave different shapes behind."),
    ],
    "pawprints": [
        ("What do paw prints mean?",
         "Paw prints are marks left by an animal's feet. They can help you figure out what animal passed by."),
    ],
    "pecking": [
        ("What does pecking mean?",
         "Pecking means tapping or striking with a beak. Birds use pecking to eat, explore, or break small things apart."),
    ],
    "suet": [
        ("What is suet for birds?",
         "Suet is a rich kind of bird food made to give birds extra energy. Some birds, like woodpeckers, enjoy it very much."),
    ],
}
KNOWLEDGE_ORDER = ["feeder", "birdseed", "tracks", "pawprints", "squirrel", "raccoon", "cat", "bird", "pecking", "suet"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["feeder_cfg"].tags) | set(world.facts["culprit_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(feeder: Feeder, culprit: Culprit, place: Place) -> str:
    if culprit.id not in feeder.access:
        return (
            f"(No story: {culprit.label} is not a reasonable culprit for the {feeder.label}. "
            f"This feeder shape does not give it a believable way to empty the seed.)"
        )
    if culprit.climbs and not place.tree:
        return (
            f"(No story: {culprit.label} needs a climb path, but {place.label} has no tree nearby.)"
        )
    if culprit.id == "raccoon" and not place.fence:
        return (
            f"(No story: the raccoon needs a fence or similar reach point near the {feeder.label}, "
            f"and {place.label} does not provide one.)"
        )
    if culprit.id == "cat" and not place.roof:
        return (
            f"(No story: the cat mystery needs a roof or rail jump path, but {place.label} does not provide it.)"
        )
    return "(No story: this culprit cannot reasonably reach this feeder in this place.)"


def explain_fix(place: Place, culprit: Culprit, fix: Fix) -> str:
    if fix.sense < SOLVABLE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it is too weak and noisy for this storyworld. "
            f"The solution should solve the mystery sensibly, not just chase everything away.)"
        )
    if fix.needs_tree and not place.tree:
        return (
            f"(No story: {fix.label} only makes sense where there is a tree trunk to guard.)"
        )
    if culprit.id not in fix.stops:
        return (
            f"(No story: {fix.label} does not reasonably stop {culprit.label} in this world.)"
        )
    return "(No story: the requested fix does not fit this mystery.)"


CURATED = [
    StoryParams(
        feeder="tube",
        culprit="squirrel",
        place="maple_yard",
        helper="grandma",
        fix="tree_guard",
        child_name="Nora",
        child_gender="girl",
        trait="observant",
    ),
    StoryParams(
        feeder="house",
        culprit="woodpecker",
        place="maple_yard",
        helper="grandpa",
        fix="suet_corner",
        child_name="Leo",
        child_gender="boy",
        trait="patient",
    ),
    StoryParams(
        feeder="house",
        culprit="raccoon",
        place="garden_fence",
        helper="mother",
        fix="baffle",
        child_name="Mia",
        child_gender="girl",
        trait="careful",
    ),
    StoryParams(
        feeder="tray",
        culprit="cat",
        place="porch_step",
        helper="father",
        fix="higher_hook",
        child_name="Ben",
        child_gender="boy",
        trait="curious",
    ),
]


ASP_RULES = r"""
% Reachability gate: only plausible feeder/culprit/place combinations.
reachable(F,C,P) :- feeder(F), culprit(C), place(P), access(F,C), pecks(C).
reachable(F,C,P) :- feeder(F), culprit(C), place(P), access(F,C), climbs(C), tree(P).
reachable(F,C,P) :- feeder(F), culprit(raccoon), place(P), access(F,raccoon), fence(P).
reachable(F,C,P) :- feeder(F), culprit(cat), place(P), access(F,cat), roof(P).

% Fix selection: sensible and actually stops that culprit.
helpful_fix(P,C,X) :- fix(X), culprit(C), place(P), stops(X,C), sense(X,S), solvable_min(M), S >= M, not needs_tree(X).
helpful_fix(P,C,X) :- fix(X), culprit(C), place(P), stops(X,C), sense(X,S), solvable_min(M), S >= M, needs_tree(X), tree(P).

valid(F,C,P) :- reachable(F,C,P).

chosen_ok :- chosen_feeder(F), chosen_culprit(C), chosen_place(P), valid(F,C,P),
             chosen_fix(X), helpful_fix(P,C,X).

solution(C) :- chosen_ok, chosen_culprit(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for feeder_id, feeder in FEEDERS.items():
        lines.append(asp.fact("feeder", feeder_id))
        for c in sorted(feeder.access):
            lines.append(asp.fact("access", feeder_id, c))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        if culprit.climbs:
            lines.append(asp.fact("climbs", culprit_id))
        if culprit.pecks:
            lines.append(asp.fact("pecks", culprit_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.tree:
            lines.append(asp.fact("tree", place_id))
        if place.roof:
            lines.append(asp.fact("roof", place_id))
        if place.fence:
            lines.append(asp.fact("fence", place_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        if fix.needs_tree:
            lines.append(asp.fact("needs_tree", fix_id))
        for c in sorted(fix.stops):
            lines.append(asp.fact("stops", fix_id, c))
    lines.append(asp.fact("solvable_min", SOLVABLE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_helpful_fixes(place_id: str, culprit_id: str) -> list[str]:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", place_id),
        asp.fact("chosen_culprit", culprit_id),
    ])
    model = asp.one_model(asp_program(extra, "#show helpful_fix/3."))
    return sorted(x for (_p, _c, x) in asp.atoms(model, "helpful_fix"))


def asp_solution(params: StoryParams) -> Optional[str]:
    import asp
    extra = "\n".join([
        asp.fact("chosen_feeder", params.feeder),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show solution/1."))
    atoms = asp.atoms(model, "solution")
    return atoms[0][0] if atoms else None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves the mystery of an empty feeder."
    )
    ap.add_argument("--feeder", choices=FEEDERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.feeder and args.culprit and args.place:
        feeder = FEEDERS[args.feeder]
        culprit = CULPRITS[args.culprit]
        place = PLACES[args.place]
        if not can_reach(feeder, culprit, place):
            raise StoryError(explain_rejection(feeder, culprit, place))
    combos = [
        combo for combo in valid_combos()
        if (args.feeder is None or combo[0] == args.feeder)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    feeder_id, culprit_id, place_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    culprit = CULPRITS[culprit_id]

    if args.fix:
        if not sensible_fix(place, culprit, FIXES[args.fix]):
            raise StoryError(explain_fix(place, culprit, FIXES[args.fix]))
        fix_id = args.fix
    else:
        options = helpful_fixes(place, culprit)
        if not options:
            raise StoryError("(No sensible fix matches the chosen mystery.)")
        fix_id = rng.choice(options)

    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        child_name = args.name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        feeder=feeder_id,
        culprit=culprit_id,
        place=place_id,
        helper=helper_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.feeder not in FEEDERS:
        raise StoryError(f"(Unknown feeder: {params.feeder})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    feeder = FEEDERS[params.feeder]
    culprit = CULPRITS[params.culprit]
    place = PLACES[params.place]
    helper = HELPERS[params.helper]
    fix = FIXES[params.fix]

    if not can_reach(feeder, culprit, place):
        raise StoryError(explain_rejection(feeder, culprit, place))
    if not sensible_fix(place, culprit, fix):
        raise StoryError(explain_fix(place, culprit, fix))

    world = tell(
        feeder=feeder,
        culprit_cfg=culprit,
        place_cfg=place,
        helper_cfg=helper,
        fix_cfg=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid mystery combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    for place_id, place in PLACES.items():
        for culprit_id, culprit in CULPRITS.items():
            py = set(helpful_fixes(place, culprit))
            asp_set = set(asp_helpful_fixes(place_id, culprit_id))
            if py != asp_set:
                rc = 1
                print(f"MISMATCH in helpful fixes for ({place_id}, {culprit_id}): python={sorted(py)} clingo={sorted(asp_set)}")

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL: default resolve_params failed:", err)

    for i, params in enumerate(smoke_cases, 1):
        try:
            solved = asp_solution(params)
            if solved != params.culprit:
                rc = 1
                print(f"ASP solution mismatch on smoke case {i}: expected {params.culprit}, got {solved}")
            sample = generate(params)
            if not sample.story.strip():
                rc = 1
                print(f"SMOKE FAIL: empty story on case {i}")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {i}: {err}")

    if rc == 0:
        print(f"OK: generation smoke test passed on {len(smoke_cases)} scenarios.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show helpful_fix/3.\n#show solution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (feeder, culprit, place) combos:\n")
        for feeder_id, culprit_id, place_id in combos:
            fixes = asp_helpful_fixes(place_id, culprit_id)
            print(f"  {feeder_id:6} {culprit_id:10} {place_id:12} fixes=[{', '.join(fixes)}]")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.culprit} at {p.feeder} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
