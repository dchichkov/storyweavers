#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/money_maneuver_pharmacy_problem_solving_quest_friendship.py
======================================================================================

A standalone story world about two animal friends on a small quest to the pharmacy.

The core tale rebuilt here is simple and child-facing:
one animal friend has a small problem, the pair count their money, make a careful
maneuver around an obstacle on the way to the pharmacy, buy the right remedy,
and come home feeling better and closer than before.

The world model enforces three pieces of common sense:

1. The remedy must actually fit the problem.
2. The chosen maneuver must actually get past the obstacle.
3. The pair's combined money must be enough to buy the remedy.

Invalid explicit choices are rejected with a legible StoryError instead of being
silently repaired.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
class Creature:
    id: str
    species: str
    names: list[str]
    traits: list[str] = field(default_factory=list)
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
class Problem:
    id: str
    label: str
    discomfort: str
    place: str
    need_line: str
    comfort_line: str
    treated_by: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    phrase: str
    cost: int
    treats: set[str] = field(default_factory=set)
    use_text: str = ""
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
class Obstacle:
    id: str
    label: str
    scene: str
    blocks: set[str] = field(default_factory=set)
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
class Maneuver:
    id: str
    label: str
    verb: str
    handles: set[str] = field(default_factory=set)
    body: str = ""
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
class Budget:
    id: str
    hero_money: int
    friend_money: int
    note: str = ""

    @property
    def total(self) -> int:
        return self.hero_money + self.friend_money
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


CREATURES = {
    "rabbit": Creature(
        id="rabbit",
        species="rabbit",
        names=["Pip", "Mimi", "Tumble", "Dot", "Nibbles"],
        traits=["quick", "gentle"],
        tags={"animal"},
    ),
    "squirrel": Creature(
        id="squirrel",
        species="squirrel",
        names=["Hazel", "Acorn", "Pico", "Flick", "Moss"],
        traits=["nimble", "bright"],
        tags={"animal"},
    ),
    "otter": Creature(
        id="otter",
        species="otter",
        names=["Ollie", "Ripple", "Pebble", "Nori", "Merry"],
        traits=["clever", "kind"],
        tags={"animal"},
    ),
    "hedgehog": Creature(
        id="hedgehog",
        species="hedgehog",
        names=["Bramble", "Poppy", "Tuck", "Needle", "Bibi"],
        traits=["careful", "steady"],
        tags={"animal"},
    ),
}

PROBLEMS = {
    "scraped_paw": Problem(
        id="scraped_paw",
        label="a scraped paw",
        discomfort="stinging",
        place="by the berry path",
        need_line="The scrape needed something clean and gentle before the friend could walk comfortably again.",
        comfort_line="Soon the paw felt protected instead of sore.",
        treated_by={"bandage"},
        tags={"scrape", "pharmacy"},
    ),
    "sneezy_nose": Problem(
        id="sneezy_nose",
        label="a sneezy nose",
        discomfort="tickly",
        place="under the windy hill",
        need_line="The friend kept sneezing and wanted something soothing from the pharmacy.",
        comfort_line="Soon the nose stopped tickling so much.",
        treated_by={"honey_drops"},
        tags={"sneeze", "pharmacy"},
    ),
    "itchy_tail": Problem(
        id="itchy_tail",
        label="an itchy tail spot",
        discomfort="itchy",
        place="near the bramble fence",
        need_line="The itchy spot needed a gentle cream so the friend would stop wriggling and frowning.",
        comfort_line="Soon the tail stopped bothering the friend.",
        treated_by={"soothing_cream"},
        tags={"itch", "pharmacy"},
    ),
}

REMEDIES = {
    "bandage": Remedy(
        id="bandage",
        label="bandage",
        phrase="a soft bandage",
        cost=3,
        treats={"scraped_paw"},
        use_text="wrapped the paw in a soft bandage",
        tags={"bandage", "pharmacy"},
    ),
    "honey_drops": Remedy(
        id="honey_drops",
        label="honey drops",
        phrase="a little packet of honey drops",
        cost=4,
        treats={"sneezy_nose"},
        use_text="let the friend suck one honey drop slowly",
        tags={"pharmacy", "honey"},
    ),
    "soothing_cream": Remedy(
        id="soothing_cream",
        label="soothing cream",
        phrase="a tin of soothing cream",
        cost=5,
        treats={"itchy_tail"},
        use_text="dabbed soothing cream on the itchy spot",
        tags={"pharmacy", "cream"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="a little stream",
        scene="A little stream had spread across the path in a shiny ribbon.",
        blocks={"stone_hop", "bridge_loop"},
        tags={"water"},
    ),
    "crowd": Obstacle(
        id="crowd",
        label="the busy market crowd",
        scene="The market lane was packed with baskets, wagons, and busy feet.",
        blocks={"side_shuffle", "alley_loop"},
        tags={"market"},
    ),
    "fallen_sign": Obstacle(
        id="fallen_sign",
        label="a fallen signboard",
        scene="A painted signboard had tipped across the lane and blocked the middle.",
        blocks={"under_duck", "garden_curve"},
        tags={"street"},
    ),
}

MANEUVERS = {
    "stone_hop": Maneuver(
        id="stone_hop",
        label="stone hop",
        verb="hopped across the stepping stones",
        handles={"stream"},
        body="They made a careful maneuver from stone to stone, tails high and paws dry.",
        tags={"maneuver", "water"},
    ),
    "bridge_loop": Maneuver(
        id="bridge_loop",
        label="bridge loop",
        verb="looped to the tiny bridge",
        handles={"stream"},
        body="They chose a patient maneuver and looped to the tiny bridge where the planks were safe.",
        tags={"maneuver", "water"},
    ),
    "side_shuffle": Maneuver(
        id="side_shuffle",
        label="side shuffle",
        verb="side-shuffled between the baskets",
        handles={"crowd"},
        body="They used a polite little maneuver, side-shuffling between the baskets without bumping anyone.",
        tags={"maneuver", "market"},
    ),
    "alley_loop": Maneuver(
        id="alley_loop",
        label="alley loop",
        verb="took the quiet alley around the crowd",
        handles={"crowd"},
        body="They solved the jam with a calm maneuver and slipped through the quiet alley beside the bakery.",
        tags={"maneuver", "market"},
    ),
    "under_duck": Maneuver(
        id="under_duck",
        label="under duck",
        verb="ducked under the sign",
        handles={"fallen_sign"},
        body="They made a neat little maneuver, ducking under the sign one at a time.",
        tags={"maneuver", "street"},
    ),
    "garden_curve": Maneuver(
        id="garden_curve",
        label="garden curve",
        verb="curved through the herb garden",
        handles={"fallen_sign"},
        body="They picked a clever maneuver and curved through the herb garden path around the sign.",
        tags={"maneuver", "street"},
    ),
}

BUDGETS = {
    "exact_shared_3": Budget(id="exact_shared_3", hero_money=1, friend_money=2, note="They must share every coin."),
    "exact_shared_4": Budget(id="exact_shared_4", hero_money=2, friend_money=2, note="Neither friend has enough alone."),
    "exact_shared_5": Budget(id="exact_shared_5", hero_money=2, friend_money=3, note="It only works if they pool their money."),
    "hero_has_4": Budget(id="hero_has_4", hero_money=4, friend_money=0, note="The helper can pay alone."),
    "hero_has_5": Budget(id="hero_has_5", hero_money=5, friend_money=0, note="The helper has just enough money."),
    "plenty_6": Budget(id="plenty_6", hero_money=4, friend_money=2, note="Together they have a little extra."),
}

GIRLISH = []
BOYISH = []


# ---------------------------------------------------------------------------
# World and causal rules
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "shared": False,
            "at_obstacle": False,
            "maneuver_done": False,
            "at_pharmacy": False,
            "purchase_success": False,
            "healed": False,
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


def _r_shared_money(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    team = world.get("team")
    if not world.facts["shared"]:
        return []
    sig = ("shared_money",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.meters["money"] = hero.meters["money"] + friend.meters["money"]
    hero.memes["care"] += 1
    friend.memes["trust"] += 1
    team.memes["friendship"] += 1
    return []


def _r_pass_obstacle(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if world.facts["at_obstacle"] and world.facts["maneuver_done"]:
        sig = ("passed_obstacle",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        obstacle.meters["blocked"] = 0.0
        world.get("team").meters["progress"] += 1
        return []
    return []


def _r_buy_remedy(world: World) -> list[str]:
    team = world.get("team")
    remedy = world.get("remedy")
    if not world.facts["at_pharmacy"]:
        return []
    if team.meters["money"] < remedy.attrs["cost"]:
        return []
    sig = ("buy_remedy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.meters["money"] -= remedy.attrs["cost"]
    remedy.meters["owned"] += 1
    world.facts["purchase_success"] = True
    return []


def _r_heal(world: World) -> list[str]:
    remedy = world.get("remedy")
    friend = world.get("friend")
    if remedy.meters["owned"] < THRESHOLD:
        return []
    if not remedy.attrs["fits"]:
        return []
    sig = ("heal_friend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.meters["pain"] = 0.0
    friend.memes["relief"] += 1
    world.get("hero").memes["joy"] += 1
    world.get("team").memes["friendship"] += 1
    world.facts["healed"] = True
    return []


CAUSAL_RULES = [
    Rule(name="shared_money", tag="social", apply=_r_shared_money),
    Rule(name="passed_obstacle", tag="physical", apply=_r_pass_obstacle),
    Rule(name="buy_remedy", tag="physical", apply=_r_buy_remedy),
    Rule(name="heal_friend", tag="physical", apply=_r_heal),
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
        after = len(world.fired)
        # if any rule fired but returned no text, still count as changed
        if after > 0 and not changed:
            # detect by comparing a fresh loop state
            pass
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def propagate_fixpoint(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    prior = -1
    while prior != len(world.fired):
        prior = len(world.fired)
        produced.extend(propagate(world, narrate=narrate))
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def remedy_fits(problem: Problem, remedy: Remedy) -> bool:
    return problem.id in remedy.treats and remedy.id in problem.treated_by


def maneuver_works(obstacle: Obstacle, maneuver: Maneuver) -> bool:
    return obstacle.id in maneuver.handles and maneuver.id in obstacle.blocks


def enough_money(budget: Budget, remedy: Remedy) -> bool:
    return budget.total >= remedy.cost


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for problem_id, problem in PROBLEMS.items():
        for remedy_id, remedy in REMEDIES.items():
            if not remedy_fits(problem, remedy):
                continue
            for obstacle_id, obstacle in OBSTACLES.items():
                for maneuver_id, maneuver in MANEUVERS.items():
                    if not maneuver_works(obstacle, maneuver):
                        continue
                    for budget_id, budget in BUDGETS.items():
                        if enough_money(budget, remedy):
                            combos.append((problem_id, remedy_id, obstacle_id, maneuver_id, budget_id))
    return combos


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    problem: str = ""
    remedy: str = ""
    obstacle: str = ""
    maneuver: str = ""
    budget: str = ""
    hero_kind: str = ""
    hero_name: str = ""
    friend_kind: str = ""
    friend_name: str = ""
    pharmacist_name: str = "Moss"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
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


def introduce(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In the little lane beside the shops, {hero.id} the {hero.type} found "
        f"{friend.id} the {friend.type} sitting sadly {problem.place}."
    )
    world.say(
        f"{friend.id} had {problem.label}, and the sore spot felt {problem.discomfort}. "
        f"{problem.need_line}"
    )
    world.say(
        f'{hero.id} touched {friend.pronoun("possessive")} shoulder and said, '
        f'"Let us go on a small quest to the pharmacy together."'
    )


def count_money(world: World, hero: Entity, friend: Entity, budget: Budget, remedy: Remedy) -> None:
    team = world.get("team")
    team.meters["money"] = hero.meters["money"]
    solo_enough = hero.meters["money"] >= remedy.attrs["cost"]
    shared_needed = budget.total >= remedy.cost and not solo_enough and friend.meters["money"] > 0

    world.say(
        f"They counted their money on a flat stone: {hero.id} had {int(hero.meters['money'])} coin"
        f"{'' if int(hero.meters['money']) == 1 else 's'}, and {friend.id} had "
        f"{int(friend.meters['money'])} coin{'' if int(friend.meters['money']) == 1 else 's'}."
    )
    if shared_needed:
        world.facts["shared"] = True
        propagate_fixpoint(world, narrate=False)
        world.say(
            f'"Then we will pool our money," said {friend.id}. '
            f'"Friends can solve a hard thing together."'
        )
        world.say(
            f"The little coins clinked into one purse, and suddenly they had exactly enough for the {remedy.label}."
        )
    elif solo_enough:
        world.say(
            f"{hero.id} smiled. There was enough money already, but {friend.id} still walked close beside "
            f"{hero.pronoun('object')} for courage."
        )
    else:
        world.say(
            "They counted twice, hoping the coins might somehow grow, but they did not."
        )


def meet_obstacle(world: World, obstacle: Obstacle, maneuver: Maneuver) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocked"] = 1.0
    world.facts["at_obstacle"] = True
    world.say(obstacle.scene)
    world.say(
        f"For one moment the quest wobbled. Then they thought of a careful maneuver."
    )
    world.say(
        f"They {maneuver.verb}. {maneuver.body}"
    )
    world.facts["maneuver_done"] = True
    propagate_fixpoint(world, narrate=False)


def pharmacy_scene(world: World, hero: Entity, friend: Entity, pharmacist: Entity, remedy: Remedy) -> None:
    team = world.get("team")
    world.facts["at_pharmacy"] = True
    world.say(
        f"At last they reached the pharmacy, where {pharmacist.id} the {pharmacist.type} stood behind the counter in a clean blue apron."
    )
    world.say(
        f'"We came for {remedy.phrase}," said {hero.id}.'
    )
    before = int(team.meters["money"])
    propagate_fixpoint(world, narrate=False)
    after = int(team.meters["money"])
    if world.facts["purchase_success"]:
        world.say(
            f"{pharmacist.id} took the money kindly, and {before - after if before >= after else remedy.cost} coin"
            f"{'' if remedy.cost == 1 else 's'} later the remedy was theirs."
        )
    else:
        raise StoryError("(No story: the friends reached the pharmacy without enough money to buy the remedy.)")


def heal_and_end(world: World, hero: Entity, friend: Entity, remedy: Remedy, problem: Problem) -> None:
    propagate_fixpoint(world, narrate=False)
    if not world.facts["healed"]:
        raise StoryError("(No story: the chosen remedy would not help with this problem.)")
    shared = world.facts["shared"]
    world.say(
        f"Outside in the sunshine, {hero.id} {remedy.use_text}. {problem.comfort_line}"
    )
    if shared:
        world.say(
            f'{friend.id} looked at the now-light purse and smiled. "That was good problem solving," '
            f'{friend.pronoun("subject")} said. "{hero.id} brought the plan, and I brought the last coins."'
        )
    else:
        world.say(
            f'{friend.id} gave a grateful little laugh. "You stayed with me all the way," '
            f'{friend.pronoun("subject")} said. "That mattered even more than the money."'
        )
    world.say(
        f"They walked home more slowly than they had hurried out, side by side, with the pharmacy bag swinging between them like a tiny flag of friendship."
    )


def tell(
    problem: Problem,
    remedy: Remedy,
    obstacle: Obstacle,
    maneuver: Maneuver,
    budget: Budget,
    hero_kind: Creature,
    hero_name: str,
    friend_kind: Creature,
    friend_name: str,
    pharmacist_name: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind.species, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_kind.species, role="friend"))
    pharmacist = world.add(Entity(id=pharmacist_name, kind="character", type="badger", role="pharmacist"))
    team = world.add(Entity(id="team", kind="thing", type="team", label="the pair"))
    obstacle_ent = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=obstacle.label))
    remedy_ent = world.add(Entity(id="remedy", kind="thing", type="remedy", label=remedy.label))
    problem_ent = world.add(Entity(id="problem", kind="thing", type="problem", label=problem.label))

    hero.attrs["creature"] = hero_kind.id
    friend.attrs["creature"] = friend_kind.id
    pharmacist.attrs["counter"] = "pharmacy"
    remedy_ent.attrs["cost"] = remedy.cost
    remedy_ent.attrs["fits"] = remedy_fits(problem, remedy)

    hero.meters["money"] = float(budget.hero_money)
    friend.meters["money"] = float(budget.friend_money)
    friend.meters["pain"] = 1.0
    obstacle_ent.meters["blocked"] = 0.0
    team.meters["money"] = float(budget.hero_money)

    introduce(world, hero, friend, problem)
    world.para()
    count_money(world, hero, friend, budget, remedy)
    world.para()
    meet_obstacle(world, obstacle, maneuver)
    world.para()
    pharmacy_scene(world, hero, friend, pharmacist, remedy)
    world.para()
    heal_and_end(world, hero, friend, remedy, problem)

    world.facts.update(
        hero=hero,
        friend=friend,
        pharmacist=pharmacist,
        team=team,
        problem_cfg=problem,
        remedy_cfg=remedy,
        obstacle_cfg=obstacle,
        maneuver_cfg=maneuver,
        budget_cfg=budget,
        shared=world.facts["shared"],
        purchase_success=world.facts["purchase_success"],
        healed=world.facts["healed"],
        money_left=int(team.meters["money"]),
        spent=remedy.cost,
        friendship=team.memes["friendship"],
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pharmacy": [
        (
            "What is a pharmacy?",
            "A pharmacy is a shop where people get medicine and other health supplies. A pharmacist helps choose the right thing for the problem.",
        )
    ],
    "money": [
        (
            "What is money for?",
            "Money is what you use to pay for things at a shop. People count it carefully so they know whether they have enough.",
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a small scrape or cut and helps keep it clean. That can make the sore place feel safer and more comfortable.",
        )
    ],
    "honey": [
        (
            "Why can honey drops feel soothing for a throat or tickly nose?",
            "Honey drops melt slowly and can feel gentle in the mouth and throat. They do not fix everything, but they can make a tickly feeling calmer.",
        )
    ],
    "cream": [
        (
            "What is soothing cream for?",
            "Soothing cream is rubbed onto a sore or itchy spot on the skin. It helps the place feel calmer instead of scratchy.",
        )
    ],
    "maneuver": [
        (
            "What is a maneuver?",
            "A maneuver is a careful way of moving to solve a problem. It can help you get around something tricky without bumping or falling.",
        )
    ],
    "friendship": [
        (
            "How can friendship help with a hard problem?",
            "A friend can share ideas, courage, or help when something feels difficult. Working together often makes a problem smaller.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pharmacy", "money", "bandage", "honey", "cream", "maneuver", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem_cfg"]
    remedy = f["remedy_cfg"]
    obstacle = f["obstacle_cfg"]
    shared = f["shared"]
    prompts = [
        'Write a short animal story for a 3-to-5-year-old that includes the words "money", "maneuver", and "pharmacy".',
        f"Tell a gentle quest story where {hero.id} the {hero.type} helps {friend.id} the {friend.type}, who has {problem.label}, and they must get to the pharmacy.",
        f"Write a friendship story where an obstacle on the road is solved with a careful maneuver, and the ending shows what changed.",
    ]
    if shared:
        prompts.append(
            f"Make the pair solve the problem by pooling their money for {remedy.phrase} after getting around {obstacle.label}."
        )
    else:
        prompts.append(
            f"Make one friend have enough money for {remedy.phrase}, but show that staying close and helping through {obstacle.label} matters too."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    pharmacist = f["pharmacist"]
    problem = f["problem_cfg"]
    remedy = f["remedy_cfg"]
    obstacle = f["obstacle_cfg"]
    maneuver = f["maneuver_cfg"]
    budget = f["budget_cfg"]
    shared = f["shared"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type}. They are friends, and the story follows their small quest to the pharmacy.",
        ),
        (
            f"Why did {hero.id} and {friend.id} go to the pharmacy?",
            f"They went because {friend.id} had {problem.label} and needed the right remedy. The trip was not just for shopping; it was to help a friend feel better.",
        ),
        (
            "What problem did the friends solve with money?",
            f"They needed {remedy.phrase}, which cost {remedy.cost} coins, so they had to count their money carefully first. That counting told them whether one friend could pay alone or whether both friends had to share.",
        ),
        (
            "What obstacle was on the way, and how did they get past it?",
            f"They found {obstacle.label} in their path. They used the {maneuver.label} maneuver, because that was a safe way around the trouble.",
        ),
    ]
    if shared:
        qa.append(
            (
                "Did both friends help pay for the remedy?",
                f"Yes. {hero.id} had {budget.hero_money} coin{'' if budget.hero_money == 1 else 's'}, and {friend.id} had {budget.friend_money}, so they pooled their money to reach the cost. Sharing the coins also showed trust, because each friend gave what they had to the same plan.",
            )
        )
    else:
        qa.append(
            (
                "If one friend had enough money, how did friendship still matter?",
                f"{hero.id} had enough money to buy the remedy, but {friend.id} still stayed close through the whole trip. The friendship mattered because courage, company, and kindness helped the quest succeed too.",
            )
        )
    qa.append(
        (
            f"How did the story end for {friend.id}?",
            f"{friend.id} felt better after {hero.id} used the {remedy.label}. The last image shows them walking home side by side, which proves the problem was solved and the friendship felt stronger.",
        )
    )
    qa.append(
        (
            f"Who helped them at the pharmacy?",
            f"{pharmacist.id} the {pharmacist.type} helped them at the pharmacy counter. The pharmacist took the money kindly and gave them the right remedy for the problem.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pharmacy", "money", "maneuver", "friendship"}
    remedy = f["remedy_cfg"]
    if remedy.id == "bandage":
        tags.add("bandage")
    if remedy.id == "honey_drops":
        tags.add("honey")
    if remedy.id == "soothing_cream":
        tags.add("cream")

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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v or v == 0}
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  world facts: {world.facts}")
    lines.append(f"  fired rules: {sorted(name for name, *rest in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        problem="scraped_paw",
        remedy="bandage",
        obstacle="stream",
        maneuver="stone_hop",
        budget="exact_shared_3",
        hero_kind="otter",
        hero_name="Ollie",
        friend_kind="rabbit",
        friend_name="Pip",
        pharmacist_name="Moss",
    ),
    StoryParams(
        problem="sneezy_nose",
        remedy="honey_drops",
        obstacle="crowd",
        maneuver="side_shuffle",
        budget="exact_shared_4",
        hero_kind="squirrel",
        hero_name="Hazel",
        friend_kind="hedgehog",
        friend_name="Tuck",
        pharmacist_name="Brindle",
    ),
    StoryParams(
        problem="itchy_tail",
        remedy="soothing_cream",
        obstacle="fallen_sign",
        maneuver="garden_curve",
        budget="hero_has_5",
        hero_kind="rabbit",
        hero_name="Mimi",
        friend_kind="squirrel",
        friend_name="Flick",
        pharmacist_name="Moss",
    ),
    StoryParams(
        problem="scraped_paw",
        remedy="bandage",
        obstacle="crowd",
        maneuver="alley_loop",
        budget="plenty_6",
        hero_kind="hedgehog",
        hero_name="Bramble",
        friend_kind="otter",
        friend_name="Pebble",
        pharmacist_name="Brindle",
    ),
]


# ---------------------------------------------------------------------------
# Rejections and lookup helpers
# ---------------------------------------------------------------------------
def explain_remedy(problem: Problem, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.phrase} would not be the right thing for {problem.label}. "
        f"Pick a remedy that actually fits the problem.)"
    )


def explain_maneuver(obstacle: Obstacle, maneuver: Maneuver) -> str:
    return (
        f"(No story: the {maneuver.label} maneuver would not get past {obstacle.label}. "
        f"Choose a maneuver that really works for that obstacle.)"
    )


def explain_budget(remedy: Remedy, budget: Budget) -> str:
    return (
        f"(No story: the friends only have {budget.total} coin"
        f"{'' if budget.total == 1 else 's'}, but {remedy.phrase} costs {remedy.cost}. "
        f"They need enough money to buy the remedy.)"
    )


def get_registry_item(registry: dict, key: str, label: str):
    if key not in registry:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return registry[key]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits_problem(P,R) :- problem(P), remedy(R), treats(R,P), needs(P,R).
works_for(O,M)    :- obstacle(O), maneuver(M), blocks(O,M), handles(M,O).
can_afford(B,R)   :- budget(B), remedy(R), total_money(B,T), cost(R,C), T >= C.

valid(P,R,O,M,B) :- fits_problem(P,R), works_for(O,M), can_afford(B,R).

shared_needed(B,R) :- budget(B), remedy(R), hero_money(B,H), friend_money(B,F), cost(R,C),
                      H < C, H + F >= C, F > 0.

#show valid/5.
#show shared_needed/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for rid in sorted(problem.treated_by):
            lines.append(asp.fact("needs", pid, rid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("cost", rid, remedy.cost))
        for pid in sorted(remedy.treats):
            lines.append(asp.fact("treats", rid, pid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for mid in sorted(obstacle.blocks):
            lines.append(asp.fact("blocks", oid, mid))
    for mid, maneuver in MANEUVERS.items():
        lines.append(asp.fact("maneuver", mid))
        for oid in sorted(maneuver.handles):
            lines.append(asp.fact("handles", mid, oid))
    for bid, budget in BUDGETS.items():
        lines.append(asp.fact("budget", bid))
        lines.append(asp.fact("hero_money", bid, budget.hero_money))
        lines.append(asp.fact("friend_money", bid, budget.friend_money))
        lines.append(asp.fact("total_money", bid, budget.total))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_shared_needed() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "shared_needed")))


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    py_shared = {
        (bid, rid)
        for bid, budget in BUDGETS.items()
        for rid, remedy in REMEDIES.items()
        if budget.hero_money < remedy.cost and budget.total >= remedy.cost and budget.friend_money > 0
    }
    cl_shared = set(asp_shared_needed())
    if py_shared == cl_shared:
        print(f"OK: shared-needed cases match ASP ({len(py_shared)} cases).")
    else:
        rc = 1
        print("MISMATCH in shared-needed cases:")
        if py_shared - cl_shared:
            print("  only in python:", sorted(py_shared - cl_shared))
        if cl_shared - py_shared:
            print("  only in asp:", sorted(cl_shared - py_shared))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pharmacy" not in sample.story.lower():
            raise StoryError("(Verify failed: smoke test story did not render as expected.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(17))
        sample = generate(params)
        if not sample.story:
            raise StoryError("(Verify failed: random smoke test returned empty story.)")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: friends count money, make a maneuver, and go to the pharmacy."
    )
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--maneuver", choices=sorted(MANEUVERS))
    ap.add_argument("--budget", choices=sorted(BUDGETS))
    ap.add_argument("--hero-kind", choices=sorted(CREATURES))
    ap.add_argument("--friend-kind", choices=sorted(CREATURES))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--pharmacist-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_creature_name(rng: random.Random, kind: str, avoid: str = "") -> str:
    names = [n for n in CREATURES[kind].names if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.remedy:
        problem = PROBLEMS[args.problem]
        remedy = REMEDIES[args.remedy]
        if not remedy_fits(problem, remedy):
            raise StoryError(explain_remedy(problem, remedy))
    if args.obstacle and args.maneuver:
        obstacle = OBSTACLES[args.obstacle]
        maneuver = MANEUVERS[args.maneuver]
        if not maneuver_works(obstacle, maneuver):
            raise StoryError(explain_maneuver(obstacle, maneuver))
    if args.budget and args.remedy:
        budget = BUDGETS[args.budget]
        remedy = REMEDIES[args.remedy]
        if not enough_money(budget, remedy):
            raise StoryError(explain_budget(remedy, budget))

    combos = [
        combo
        for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.remedy is None or combo[1] == args.remedy)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.maneuver is None or combo[3] == args.maneuver)
        and (args.budget is None or combo[4] == args.budget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, remedy_id, obstacle_id, maneuver_id, budget_id = rng.choice(sorted(combos))

    hero_kind = args.hero_kind or rng.choice(sorted(CREATURES))
    friend_choices = [k for k in sorted(CREATURES) if k != hero_kind]
    friend_kind = args.friend_kind or rng.choice(friend_choices)
    if friend_kind == hero_kind and len(CREATURES) > 1 and args.friend_kind is None:
        friend_kind = rng.choice([k for k in sorted(CREATURES) if k != hero_kind])

    hero_name = args.hero_name or pick_creature_name(rng, hero_kind)
    friend_name = args.friend_name or pick_creature_name(rng, friend_kind, avoid=hero_name)
    pharmacist_name = args.pharmacist_name or rng.choice(["Moss", "Brindle", "Maple"])

    return StoryParams(
        problem=problem_id,
        remedy=remedy_id,
        obstacle=obstacle_id,
        maneuver=maneuver_id,
        budget=budget_id,
        hero_kind=hero_kind,
        hero_name=hero_name,
        friend_kind=friend_kind,
        friend_name=friend_name,
        pharmacist_name=pharmacist_name,
    )


def generate(params: StoryParams) -> StorySample:
    problem = get_registry_item(PROBLEMS, params.problem, "problem")
    remedy = get_registry_item(REMEDIES, params.remedy, "remedy")
    obstacle = get_registry_item(OBSTACLES, params.obstacle, "obstacle")
    maneuver = get_registry_item(MANEUVERS, params.maneuver, "maneuver")
    budget = get_registry_item(BUDGETS, params.budget, "budget")
    hero_kind = get_registry_item(CREATURES, params.hero_kind, "hero kind")
    friend_kind = get_registry_item(CREATURES, params.friend_kind, "friend kind")

    if not remedy_fits(problem, remedy):
        raise StoryError(explain_remedy(problem, remedy))
    if not maneuver_works(obstacle, maneuver):
        raise StoryError(explain_maneuver(obstacle, maneuver))
    if not enough_money(budget, remedy):
        raise StoryError(explain_budget(remedy, budget))
    if params.hero_name == params.friend_name:
        raise StoryError("(No story: the two animal friends need different names.)")

    world = tell(
        problem=problem,
        remedy=remedy,
        obstacle=obstacle,
        maneuver=maneuver,
        budget=budget,
        hero_kind=hero_kind,
        hero_name=params.hero_name,
        friend_kind=friend_kind,
        friend_name=params.friend_name,
        pharmacist_name=params.pharmacist_name or "Moss",
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        shared = set(asp_shared_needed())
        print(f"{len(combos)} compatible (problem, remedy, obstacle, maneuver, budget) combos:\n")
        for problem, remedy, obstacle, maneuver, budget in combos:
            note = "shared money needed" if (budget, remedy) in shared else "solo money enough"
            print(f"  {problem:12} {remedy:14} {obstacle:12} {maneuver:12} {budget:14}  [{note}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.hero_name} & {p.friend_name}: {p.problem}, {p.remedy}, "
                f"{p.obstacle} via {p.maneuver}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
