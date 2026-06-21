#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py
=====================================================================================

A standalone story world about a child hauling an absurdly huge fair prize in a
wagon. The cargo is put on one side first, making the load asymmetric; the hero
must solve the problem by putting a counterweight on the other side before a
risky crossing.

The domain is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate for sensible balancing choices
- a state-driven five-beat story with suspense and inner monologue
- an inline ASP twin for the gate and the ending model

Run it
------
    python storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py --cargo pumpkin --counterweight hay_bales
    python storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py --counterweight pillow_sack
    python storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/asymmetric_put_problem_solving_suspense_inner_monologue.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Cargo:
    id: str
    label: str
    phrase: str
    boast: str
    heft: int
    destination: str
    finish: str
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
class Counterweight:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    put_text: str
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
class Obstacle:
    id: str
    label: str
    scene: str
    danger_line: str
    safe_tilt: int
    success: str
    failure: str
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


def _r_tilt(world: World) -> list[str]:
    wagon = world.get("wagon")
    left = wagon.meters["left_weight"]
    right = wagon.meters["right_weight"]
    diff = abs(left - right)
    if diff < THRESHOLD:
        return []
    sig = ("tilt", int(diff))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wagon.meters["tilt"] = float(diff)
    world.get("hero").memes["worry"] += 1
    world.get("helper").memes["alert"] += 1
    return []


def _r_danger(world: World) -> list[str]:
    wagon = world.get("wagon")
    obstacle = world.facts.get("obstacle_cfg")
    if obstacle is None:
        return []
    if wagon.meters["on_obstacle"] < THRESHOLD:
        return []
    if wagon.meters["tilt"] <= obstacle.safe_tilt:
        return []
    sig = ("danger", obstacle.id, int(wagon.meters["tilt"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wagon.meters["danger"] += 1
    world.get("hero").memes["suspense"] += 1
    return []


def _r_hope(world: World) -> list[str]:
    wagon = world.get("wagon")
    obstacle = world.facts.get("obstacle_cfg")
    if obstacle is None:
        return []
    if wagon.meters["on_obstacle"] < THRESHOLD:
        return []
    if wagon.meters["tilt"] > obstacle.safe_tilt:
        return []
    sig = ("hope", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tilt", tag="physical", apply=_r_tilt),
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="hope", tag="emotional", apply=_r_hope),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def imbalance(cargo: Cargo, counterweight: Counterweight) -> int:
    return abs(cargo.heft - counterweight.power)


def is_stable(cargo: Cargo, counterweight: Counterweight, obstacle: Obstacle) -> bool:
    return imbalance(cargo, counterweight) <= obstacle.safe_tilt


def sensible_counterweights() -> list[Counterweight]:
    return [cw for cw in COUNTERWEIGHTS.values() if cw.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id in CARGOES:
        for counter_id, counter in COUNTERWEIGHTS.items():
            if counter.sense < SENSE_MIN:
                continue
            for obstacle_id in OBSTACLES:
                combos.append((cargo_id, counter_id, obstacle_id))
    return combos


def explain_counterweight(counter_id: str) -> str:
    cw = COUNTERWEIGHTS[counter_id]
    better = ", ".join(sorted(c.id for c in sensible_counterweights()))
    return (
        f"(Refusing counterweight '{counter_id}': it is too flimsy for this world "
        f"(sense={cw.sense} < {SENSE_MIN}). A balancing plan should sound sturdy enough "
        f"to matter. Try: {better}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.cargo not in CARGOES or params.counterweight not in COUNTERWEIGHTS or params.obstacle not in OBSTACLES:
        raise StoryError("(No story: one of the requested options is not in this world.)")
    return "success" if is_stable(CARGOES[params.cargo], COUNTERWEIGHTS[params.counterweight], OBSTACLES[params.obstacle]) else "spill"


def _do_put_cargo(world: World, cargo: Cargo) -> None:
    wagon = world.get("wagon")
    wagon.meters["left_weight"] = float(cargo.heft)
    wagon.meters["cargo_loaded"] = 1.0
    world.get("cargo").meters["loaded"] = 1.0
    propagate(world, narrate=False)


def _do_put_counterweight(world: World, counterweight: Counterweight) -> None:
    wagon = world.get("wagon")
    wagon.meters["right_weight"] = float(counterweight.power)
    world.get("counterweight").meters["loaded"] = 1.0
    propagate(world, narrate=False)


def _step_onto_obstacle(world: World) -> None:
    world.get("wagon").meters["on_obstacle"] = 1.0
    propagate(world, narrate=False)


def setup(world: World, hero: Entity, helper: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    world.say(
        f"In a valley so roomy that sunrise had to jog to reach it, {hero.id} set out with "
        f"{cargo.phrase} headed for {cargo.destination}. {helper.id}, the {helper.label}, "
        f"snorted beside the wagon as if hauling a cloud were ordinary work."
    )
    world.say(
        f"Folks said the thing was so big it could cast shade over a chicken coop, and {cargo.boast}."
    )
    world.say(
        f"Before noon they reached {obstacle.scene}, and even the wind seemed to hold its breath."
    )


def load_problem(world: World, hero: Entity, cargo: Cargo) -> None:
    _do_put_cargo(world, cargo)
    wagon = world.get("wagon")
    tilt = int(wagon.meters["tilt"])
    world.say(
        f"{hero.id} and {world.get('helper').id} puffed and strained and finally put the {cargo.label} onto the left side of the wagon."
    )
    world.say(
        f"At once the whole rig leaned in an asymmetric slant so crooked that one wheel looked ready to whisper goodbye. "
        f"The wagon dipped {tilt} hard notch{'es' if tilt != 1 else ''} to the side."
    )


def inner_monologue(world: World, hero: Entity, cargo: Cargo, counterweight: Counterweight, obstacle: Obstacle) -> None:
    predicted = predict_crossing(world, cargo, counterweight, obstacle)
    if predicted["stable"]:
        thought = (
            f'{hero.id} swallowed and thought, "If I put {counterweight.phrase} on the empty side, '
            f'the wagon might stand up straight enough to face {obstacle.label}."'
        )
    else:
        thought = (
            f'{hero.id} swallowed and thought, "If I put {counterweight.phrase} on the empty side, '
            f'it will help, but maybe not enough for {obstacle.label}. Still, doing nothing is worse."'
        )
    world.say(thought)
    world.say(
        f"{obstacle.danger_line} The boards and stones ahead looked as if they were listening for one wrong wobble."
    )


def solve(world: World, hero: Entity, counterweight: Counterweight) -> None:
    _do_put_counterweight(world, counterweight)
    wagon = world.get("wagon")
    tilt = int(wagon.meters["tilt"])
    if tilt == 0:
        shape = "stood level as a table in a careful baker's kitchen"
    elif tilt == 1:
        shape = "still leaned a hair, but no longer like trouble"
    else:
        shape = f"rose some, though it still kept a {tilt}-notch lean"
    world.say(
        f"Then {hero.id} {counterweight.put_text}. The wagon {shape}."
    )
    world.say(
        f"{world.get('helper').id} stamped once, testing the balance, and waited for the word to go."
    )


def crossing(world: World, hero: Entity, helper: Entity, cargo: Cargo, counterweight: Counterweight, obstacle: Obstacle) -> None:
    _step_onto_obstacle(world)
    wagon = world.get("wagon")
    world.say(
        f"Slow as moonrise, {hero.id} led {helper.id} onto {obstacle.label}. Every creak sounded twice as loud."
    )
    if wagon.meters["danger"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s heart thumped like a mallet in a barrel. {hero.pronoun().capitalize()} thought, "
            f'"Easy now. One more wobble and that {cargo.label} will go rolling clear to supper."'
        )
    else:
        world.say(
            f"{hero.id} kept one hand on the wagon rail and thought, "
            f'"Hold steady now. We solved the hard part; we only have to trust it."'
        )


def ending_success(world: World, hero: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    world.say(obstacle.success)
    world.say(
        f"By sunset {hero.id} rolled into {cargo.destination} with the {cargo.label} safe and proud. "
        f"{cargo.finish} After that day, folks stopped saying {hero.id} was merely strong; they said "
        f"{hero.pronoun()} could think a wagon straight."
    )


def ending_spill(world: World, hero: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    world.say(obstacle.failure)
    world.say(
        f"The {cargo.label} did not smash anyone, but it did thunder into a ditch and sit there like a stubborn moon. "
        f"{hero.id} tipped {hero.pronoun('possessive')} hat back and managed a rueful grin."
    )
    world.say(
        f'"Next time," {hero.pronoun()} told {world.get("helper").id}, "I will balance first and brag later." '
        f"They still reached town by dark, only slower, wiser, and muddy to the knees."
    )


def predict_crossing(world: World, cargo: Cargo, counterweight: Counterweight, obstacle: Obstacle) -> dict:
    sim = world.copy()
    sim.facts["obstacle_cfg"] = obstacle
    sim.get("wagon").meters["left_weight"] = float(cargo.heft)
    sim.get("wagon").meters["right_weight"] = float(counterweight.power)
    propagate(sim, narrate=False)
    sim.get("wagon").meters["on_obstacle"] = 1.0
    propagate(sim, narrate=False)
    return {
        "stable": sim.get("wagon").meters["danger"] < THRESHOLD,
        "tilt": int(sim.get("wagon").meters["tilt"]),
        "danger": int(sim.get("wagon").meters["danger"]),
    }


def tell(
    cargo: Cargo,
    counterweight: Counterweight,
    obstacle: Obstacle,
    hero_name: str = "Mae",
    hero_gender: str = "girl",
    helper_name: str = "Thistle",
    helper_type: str = "mule",
    parent_type: str = "father",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="animal", role="helper", label=helper_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    wagon = world.add(Entity(id="wagon", kind="thing", type="wagon", label="wagon"))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label))
    counter_ent = world.add(Entity(id="counterweight", kind="thing", type="counterweight", label=counterweight.label))

    wagon.meters["left_weight"] = 0.0
    wagon.meters["right_weight"] = 0.0
    wagon.meters["tilt"] = 0.0
    wagon.meters["danger"] = 0.0
    wagon.meters["on_obstacle"] = 0.0
    cargo_ent.meters["loaded"] = 0.0
    counter_ent.meters["loaded"] = 0.0

    hero.memes["worry"] = 0.0
    hero.memes["suspense"] = 0.0
    hero.memes["hope"] = 0.0
    helper.memes["alert"] = 0.0

    world.facts["obstacle_cfg"] = obstacle

    setup(world, hero, helper, cargo, obstacle)
    world.para()
    load_problem(world, hero, cargo)
    inner_monologue(world, hero, cargo, counterweight, obstacle)
    world.para()
    solve(world, hero, counterweight)
    crossing(world, hero, helper, cargo, counterweight, obstacle)
    world.para()

    stable = is_stable(cargo, counterweight, obstacle)
    if stable:
        ending_success(world, hero, cargo, obstacle)
    else:
        ending_spill(world, hero, cargo, obstacle)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        wagon=wagon,
        cargo_cfg=cargo,
        counterweight_cfg=counterweight,
        obstacle_cfg=obstacle,
        outcome="success" if stable else "spill",
        imbalance=imbalance(cargo, counterweight),
        stable=stable,
    )
    return world


CARGOES = {
    "pumpkin": Cargo(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so large it needed its own weather",
        boast="its stem was thicker than most porch posts",
        heft=4,
        destination="the county fair",
        finish="The blue ribbon looked almost surprised to meet something bigger than itself.",
        tags={"pumpkin", "fair"},
    ),
    "cheese_wheel": Cargo(
        id="cheese_wheel",
        label="cheese wheel",
        phrase="a cheese wheel broad as a millstone",
        boast="its smell drifted ahead of the wagon and made dogs daydream in three towns",
        heft=3,
        destination="the harvest market",
        finish="The market bell rang, and the cheesemonger laughed until tears shone in his beard.",
        tags={"cheese", "market"},
    ),
    "melon": Cargo(
        id="melon",
        label="melon",
        phrase="a striped melon with a shine like green moonlight",
        boast="it was said a family of field mice once used it for a summer porch",
        heft=5,
        destination="the river fair",
        finish="Children danced around it in a ring, certain no ordinary knife would ever reach the middle.",
        tags={"melon", "fair"},
    ),
}

COUNTERWEIGHTS = {
    "hay_bales": Counterweight(
        id="hay_bales",
        label="hay bales",
        phrase="three tight hay bales",
        power=3,
        sense=3,
        put_text="put three tight hay bales on the right side, one after another, and nudged them snug with a boot",
        qa_text="put three hay bales on the empty side to counter the heavy cargo",
        tags={"hay", "balance"},
    ),
    "stone_crates": Counterweight(
        id="stone_crates",
        label="stone crates",
        phrase="two crates of creek stones",
        power=4,
        sense=3,
        put_text="put two crates of creek stones on the right side until the axles stopped groaning so unevenly",
        qa_text="put two stone crates on the empty side to even the wagon",
        tags={"stone", "balance"},
    ),
    "water_casks": Counterweight(
        id="water_casks",
        label="water casks",
        phrase="a pair of sloshing water casks",
        power=2,
        sense=2,
        put_text="put a pair of sloshing water casks on the right side and tied them down with a rope",
        qa_text="put two water casks on the empty side to help steady the wagon",
        tags={"water", "balance"},
    ),
    "pillow_sack": Counterweight(
        id="pillow_sack",
        label="pillow sack",
        phrase="one soft sack of goose-feather pillows",
        power=1,
        sense=1,
        put_text="put a sack of pillows on the right side, though even the pillows seemed doubtful",
        qa_text="put a sack of pillows on the empty side",
        tags={"pillow"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="the plank bridge",
        scene="a plank bridge over a creek that talked back to every footstep",
        danger_line="Below, the creek flashed bright and quick between the rocks",
        safe_tilt=1,
        success="The wagon swayed, then found its manners and crossed the bridge without spilling so much as a seed.",
        failure="Halfway over, the wagon gave one mean lurch, and the load rolled loose with a gasp from the bridge itself.",
        tags={"bridge", "crossing"},
    ),
    "hill": Obstacle(
        id="hill",
        label="the wind-bent hill road",
        scene="the wind-bent hill road, where carts liked to lean and think bad thoughts",
        danger_line="Up the slope, loose gravel skittered under the wheels",
        safe_tilt=2,
        success="The wheels bit the road, the load held fast, and the wagon climbed the hill as steady as a church bell.",
        failure="Near the top, one wheel slipped in gravel, and the load slid sideways in a hurry too big to stop.",
        tags={"hill", "road"},
    ),
    "ford": Obstacle(
        id="ford",
        label="the shallow ford",
        scene="the shallow ford, where river water tugged at spokes and toes",
        danger_line="Cold water curled around the wheels and pulled at every weak decision",
        safe_tilt=0,
        success="The wagon entered the ford level as a tray, and it came out dripping but true on the far bank.",
        failure="The current found the crooked lean at once, and with one splashy heave it shoved the load out of line and over.",
        tags={"ford", "river"},
    ),
}

GIRL_NAMES = ["Mae", "June", "Tilda", "Ruth", "Nell", "Dora", "Lark"]
BOY_NAMES = ["Bo", "Eli", "Hank", "Jesse", "Cal", "Otis", "Finn"]
HELPERS = [
    ("Thistle", "mule"),
    ("Buck", "ox"),
    ("Pepper", "pony"),
    ("Blue", "mule"),
]


@dataclass
class StoryParams:
    cargo: str
    counterweight: str
    obstacle: str
    hero: str
    hero_gender: str
    helper: str
    helper_type: str
    parent: str
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
    "balance": [
        (
            "What does balance mean on a wagon?",
            "Balance means the weight is spread so one side is not much heavier than the other. If a wagon is badly unbalanced, it can tip or wobble when it moves."
        )
    ],
    "bridge": [
        (
            "Why can a bridge feel scary with a heavy wagon?",
            "A bridge can bounce or creak under a heavy load. If the wagon is leaning already, that extra wobble can make the load shift."
        )
    ],
    "ford": [
        (
            "Why is a shallow ford tricky to cross?",
            "Even shallow water pushes on wheels and legs. A crooked wagon can lose its balance faster when water tugs at one side."
        )
    ],
    "hill": [
        (
            "Why is a steep hill hard for a wagon?",
            "On a hill, weight pulls backward and sideways at the same time. If the load is uneven, the heavier side can drag the wagon off line."
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin?",
            "A pumpkin is a large round squash with a thick rind and seeds inside. People grow them in gardens and use them for cooking and carving."
        )
    ],
    "cheese": [
        (
            "What is a cheese wheel?",
            "A cheese wheel is a big round shape of cheese made and stored as one piece. Real ones can be quite heavy."
        )
    ],
    "melon": [
        (
            "What is a melon?",
            "A melon is a large fruit with a watery inside and lots of seeds. Some melons are striped, and many taste sweet."
        )
    ],
    "river": [
        (
            "What does a river current do?",
            "A current is moving water that keeps pushing in one direction. It can nudge wheels, legs, and floating things downstream."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    counter = f["counterweight_cfg"]
    obstacle = f["obstacle_cfg"]
    hero = f["hero"]
    if f["outcome"] == "success":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that uses the words "asymmetric" and "put" and features suspense, inner monologue, and problem solving.',
            f"Tell a tall story where {hero.id} puts a giant {cargo.label} on one side of a wagon, notices the asymmetric lean, and solves the problem by adding {counter.label} before crossing {obstacle.label}.",
            f"Write a child-facing story with a risky crossing, a brave inner thought, and a clever fix that keeps a huge wagon load safe.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that uses the words "asymmetric" and "put" and features suspense, inner monologue, and problem solving.',
        f"Tell a cautionary tall story where {hero.id} tries to steady a giant {cargo.label} with {counter.label}, but the wagon is still too uneven for {obstacle.label}.",
        f"Write a story with suspense and inner monologue where a child solves part of a problem, but learns that a better balance is needed next time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    counter = f["counterweight_cfg"]
    obstacle = f["obstacle_cfg"]
    out = f["outcome"]
    tilt = f["imbalance"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was hauling a giant {cargo.label} in a wagon, and {helper.id}, the {helper.label}, who helped pull it along."
        ),
        (
            f"What problem did {hero.id} have?",
            f"After {hero.id} put the {cargo.label} on one side of the wagon, the load leaned in an asymmetric way. That meant the wagon could wobble or tip when it reached {obstacle.label}."
        ),
        (
            f"What was {hero.id} thinking about before the crossing?",
            f"{hero.id} was thinking hard about how to steady the wagon. {hero.pronoun().capitalize()} knew that putting weight on the empty side might keep the load from sliding."
        ),
        (
            f"How did {hero.id} try to solve the problem?",
            f"{hero.pronoun().capitalize()} {counter.qa_text}. The idea was to make the two sides of the wagon closer in weight before the risky crossing."
        ),
    ]
    if out == "success":
        qa.append(
            (
                f"Why did the plan work at {obstacle.label}?",
                f"It worked because the wagon was balanced enough for that crossing. The remaining lean was only {tilt}, which was small enough to stay steady there."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The wagon made it across safely, and {hero.id} delivered the giant {cargo.label} to {cargo.destination}. The ending shows that careful thinking changed a dangerous trip into a proud one."
            )
        )
    else:
        qa.append(
            (
                f"Why did the wagon still spill at {obstacle.label}?",
                f"The counterweight helped, but not enough. The wagon still leaned more than {obstacle.label} could forgive, so the load shifted and rolled loose."
            )
        )
        qa.append(
            (
                "What did the hero learn?",
                f"{hero.id} learned that fixing part of a problem is not always the same as fixing all of it. Next time {hero.pronoun()} would balance the wagon better before starting the crossing."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cargo_cfg"].tags) | set(world.facts["counterweight_cfg"].tags) | set(world.facts["obstacle_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in ["balance", "bridge", "ford", "hill", "pumpkin", "cheese", "melon", "river"]:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:13} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="pumpkin",
        counterweight="stone_crates",
        obstacle="bridge",
        hero="Mae",
        hero_gender="girl",
        helper="Thistle",
        helper_type="mule",
        parent="father",
        seed=1,
    ),
    StoryParams(
        cargo="cheese_wheel",
        counterweight="hay_bales",
        obstacle="hill",
        hero="Bo",
        hero_gender="boy",
        helper="Buck",
        helper_type="ox",
        parent="mother",
        seed=2,
    ),
    StoryParams(
        cargo="melon",
        counterweight="water_casks",
        obstacle="ford",
        hero="June",
        hero_gender="girl",
        helper="Pepper",
        helper_type="pony",
        parent="father",
        seed=3,
    ),
    StoryParams(
        cargo="melon",
        counterweight="stone_crates",
        obstacle="bridge",
        hero="Eli",
        hero_gender="boy",
        helper="Blue",
        helper_type="mule",
        parent="mother",
        seed=4,
    ),
]


ASP_RULES = r"""
sensible(Cw) :- counterweight(Cw), sense(Cw,S), sense_min(M), S >= M.
valid(Cg,Cw,Ob) :- cargo(Cg), counterweight(Cw), obstacle(Ob), sensible(Cw).

absdiff(H,P,D) :- heft(Cg,H), chosen_cargo(Cg), power(Cw,P), chosen_counterweight(Cw), H >= P, D = H - P.
absdiff(H,P,D) :- heft(Cg,H), chosen_cargo(Cg), power(Cw,P), chosen_counterweight(Cw), P > H, D = P - H.

stable :- chosen_obstacle(Ob), safe_tilt(Ob,S), absdiff(_,_,D), D <= S.
outcome(success) :- stable.
outcome(spill) :- not stable.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("heft", cargo_id, cargo.heft))
    for counter_id, counter in COUNTERWEIGHTS.items():
        lines.append(asp.fact("counterweight", counter_id))
        lines.append(asp.fact("power", counter_id, counter.power))
        lines.append(asp.fact("sense", counter_id, counter.sense))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("safe_tilt", obstacle_id, obstacle.safe_tilt))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_counterweight", params.counterweight),
            asp.fact("chosen_obstacle", params.obstacle),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {c.id for c in sensible_counterweights()}
    if c_sens == p_sens:
        print(f"OK: sensible counterweights match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible counterweights: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: an asymmetric wagon load, a balancing plan, and a risky crossing."
    )
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--counterweight", choices=COUNTERWEIGHTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.counterweight and COUNTERWEIGHTS[args.counterweight].sense < SENSE_MIN:
        raise StoryError(explain_counterweight(args.counterweight))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.counterweight is None or combo[1] == args.counterweight)
        and (args.obstacle is None or combo[2] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, counter_id, obstacle_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name, helper_type = rng.choice(HELPERS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        cargo=cargo_id,
        counterweight=counter_id,
        obstacle=obstacle_id,
        hero=hero,
        hero_gender=gender,
        helper=helper_name,
        helper_type=helper_type,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOES:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if params.counterweight not in COUNTERWEIGHTS:
        raise StoryError(f"(No story: unknown counterweight '{params.counterweight}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if COUNTERWEIGHTS[params.counterweight].sense < SENSE_MIN:
        raise StoryError(explain_counterweight(params.counterweight))

    world = tell(
        cargo=CARGOES[params.cargo],
        counterweight=COUNTERWEIGHTS[params.counterweight],
        obstacle=OBSTACLES[params.obstacle],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible counterweights: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, counterweight, obstacle) combos:\n")
        for cargo_id, counter_id, obstacle_id in combos:
            sample_params = StoryParams(
                cargo=cargo_id,
                counterweight=counter_id,
                obstacle=obstacle_id,
                hero="Mae",
                hero_gender="girl",
                helper="Thistle",
                helper_type="mule",
                parent="father",
            )
            print(f"  {cargo_id:12} {counter_id:13} {obstacle_id:8} -> {outcome_of(sample_params)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.cargo} with {p.counterweight} at {p.obstacle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
