#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py
==============================================================

A standalone story world for a tiny fable-like domain: two small animals mean to
carry a treat on a saucer to an elder, one hurries and tries to do it alone, the
saucer tips, and teamwork becomes the wiser second try.

The world model is intentionally narrow and constraint-checked:

- A cargo has a balance risk on a saucer.
- A path adds jolts or tilts.
- A solo carrier has limited steadying ability.
- A teamwork plan adds enough support only for some combinations.

So the storyworld only generates combinations where there is a real cautionary
mistake first, and where the chosen teamwork plan can honestly solve it.

Run it
------
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py --cargo milk --path windy_bridge
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py --plan twig_handle
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py --all
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py --qa
    python storyworlds/worlds/gpt-5.4/saucer_cautionary_teamwork_fable.py --verify
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
SOLO_SUPPORT = 2
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
        pronouns = self.attrs.get(
            "pronouns",
            {"subject": "they", "object": "them", "possessive": "their"},
        )
        return pronouns[case]

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
class Cargo:
    id: str
    label: str
    phrase: str
    risk: int
    spill_word: str
    delivery_line: str
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
class Path:
    id: str
    label: str
    phrase: str
    jolt: int
    scene: str
    stumble: str
    ending_image: str
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
class Plan:
    id: str
    label: str
    support: int
    sense: int
    propose: str
    carry_text: str
    qa_text: str
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
        self.facts: dict = {
            "instability": 0,
            "support": 0,
            "attempt_mode": "",
            "spill_happened": False,
            "delivered": False,
            "lesson_spoken": False,
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


def _r_spill(world: World) -> list[str]:
    if world.facts["attempt_mode"] != "solo":
        return []
    if world.facts["support"] >= world.facts["instability"]:
        return []
    sig = ("spill", world.facts["instability"], world.facts["support"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    saucer = world.get("saucer")
    cargo = world.get("cargo")
    leader = world.get("leader")
    helper = world.get("helper")
    saucer.meters["tilt"] += 1
    cargo.meters["spilled"] += 1
    world.facts["spill_happened"] = True
    leader.memes["alarm"] += 1
    helper.memes["alarm"] += 1
    return []


def _r_delivery(world: World) -> list[str]:
    if world.facts["attempt_mode"] != "team":
        return []
    if world.facts["support"] < world.facts["instability"]:
        return []
    sig = ("deliver", world.facts["instability"], world.facts["support"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    saucer = world.get("saucer")
    cargo = world.get("cargo")
    elder = world.get("elder")
    saucer.meters["steady"] += 1
    cargo.meters["delivered"] += 1
    elder.meters["received"] += 1
    world.facts["delivered"] = True
    world.get("leader").memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="delivery", tag="physical", apply=_r_delivery),
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
            elif rule.name in {name for name, *_ in world.fired}:
                continue
            else:
                # state changes from the rule body itself may still have happened
                pass
        current_size = len(world.fired)
        if current_size > 0 and current_size != len(set(world.fired)):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def instability_of(cargo: Cargo, path: Path) -> int:
    return cargo.risk + path.jolt


def can_spill_alone(cargo: Cargo, path: Path) -> bool:
    return instability_of(cargo, path) > SOLO_SUPPORT


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def can_recover(cargo: Cargo, path: Path, plan: Plan) -> bool:
    return plan.support >= instability_of(cargo, path)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_plans():
        return combos
    for cargo_id, cargo in CARGOES.items():
        for path_id, path in PATHS.items():
            if can_spill_alone(cargo, path) and any(can_recover(cargo, path, p) for p in sensible_plans()):
                combos.append((cargo_id, path_id))
    return combos


def explain_combo_rejection(cargo: Cargo, path: Path) -> str:
    inst = instability_of(cargo, path)
    if inst <= SOLO_SUPPORT:
        return (
            f"(No story: {cargo.label} on a saucer over {path.phrase} is too steady for a real cautionary turn. "
            f"A solo carrier could manage it, so there is no honest spill and no need for teamwork.)"
        )
    return "(No story: no sensible teamwork plan in this world can keep that saucer steady.)"


def explain_plan_rejection(plan: Plan, cargo: Cargo, path: Path) -> str:
    if plan.sense < SENSE_MIN:
        better = ", ".join(sorted(p.id for p in sensible_plans()))
        return (
            f"(Refusing plan '{plan.id}': it scores too low on common sense "
            f"(sense={plan.sense} < {SENSE_MIN}). Try one of the sturdier teamwork plans: {better}.)"
        )
    return (
        f"(No story: {plan.label} cannot steady a saucer of {cargo.label} over {path.phrase}. "
        f"The plan is too weak for the jolts on that path.)"
    )


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.facts["attempt_mode"] = "solo"
    sim.facts["support"] = SOLO_SUPPORT
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "spill": cargo.meters["spilled"] >= THRESHOLD,
        "tilt": sim.get("saucer").meters["tilt"],
    }


def introduce(world: World, leader: Entity, helper: Entity, elder: Entity, cargo: Cargo) -> None:
    leader.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In a hedge beside the fields lived {leader.id} the {leader.type} and {helper.id} the {helper.type}. "
        f"They liked to do kind errands together, and that morning they had promised a small comfort to {elder.id} the {elder.type}."
    )
    world.say(
        f"On a painted saucer lay {cargo.phrase}. It was only a little gift, but it looked precious because it had been chosen with care."
    )


def purpose(world: World, elder: Entity, path: Path) -> None:
    world.say(
        f"{elder.id} was resting beyond {path.phrase}, and the way there led by {path.scene}."
    )


def temptation(world: World, leader: Entity) -> None:
    leader.memes["pride"] += 1
    world.say(
        f'"I can take it quickly by myself," said {leader.id}, lifting the saucer. '
        f"The wish to be first tugged harder than the wish to be careful."
    )


def warning(world: World, helper: Entity, leader: Entity, cargo: Cargo, path: Path) -> None:
    pred = predict_spill(world)
    helper.memes["worry"] += 1
    world.facts["predicted_spill"] = pred["spill"]
    world.say(
        f'{helper.id} watched the saucer edge wobble. "Please go slowly," {helper.pronoun()} said. '
        f'"{cargo.label.capitalize()} can shift, and {path.label} will shake the saucer."'
    )


def solo_attempt(world: World, leader: Entity, path: Path) -> None:
    world.facts["attempt_mode"] = "solo"
    world.facts["support"] = SOLO_SUPPORT
    leader.meters["carrying"] += 1
    world.say(
        f"But {leader.id} hurried onto {path.phrase}. {path.stumble}"
    )
    propagate(world, narrate=False)


def narrate_spill(world: World, cargo: Cargo) -> None:
    if not world.facts["spill_happened"]:
        return
    world.say(
        f"The saucer tipped. {cargo.spill_word} slid over the rim, and {world.get('leader').id} froze as if the ground had spoken a sharp little lesson."
    )
    world.say(
        f"{world.get('helper').id} did not scold. {world.get('helper').pronoun().capitalize()} only hurried close so the saucer would not fall and break."
    )


def regroup(world: World, leader: Entity, helper: Entity, plan: Plan) -> None:
    leader.memes["shame"] += 1
    helper.memes["steadiness"] += 1
    leader.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"I wanted to look swift, and now I have made a mess," said {leader.id} in a small voice.'
    )
    world.say(
        f'{helper.id} touched the saucer gently. "Then let us be wise instead of swift," {helper.pronoun()} said. '
        f'"Let us {plan.propose}."'
    )


def tidy_and_retry(world: World, cargo: Cargo) -> None:
    world.get("cargo").meters["spilled"] = 0.0
    world.get("saucer").meters["tilt"] = 0.0
    world.say(
        f"Together they saved what they could, straightened the saucer, and set {cargo.label} right again."
    )


def team_attempt(world: World, leader: Entity, helper: Entity, plan: Plan, path: Path) -> None:
    world.facts["attempt_mode"] = "team"
    world.facts["support"] = plan.support
    leader.meters["carrying"] += 1
    helper.meters["carrying"] += 1
    world.say(
        f"Then {leader.id} and {helper.id} {plan.carry_text} and crossed {path.phrase} one small step at a time."
    )
    propagate(world, narrate=False)


def deliver(world: World, elder: Entity, cargo: Cargo, path: Path) -> None:
    if not world.facts["delivered"]:
        raise StoryError("The teamwork attempt failed to deliver the saucer safely.")
    elder.memes["gratitude"] += 1
    world.say(
        f"When they reached {elder.id}, {cargo.delivery_line} {elder.pronoun()} smiled at the careful pair."
    )
    world.say(
        f"Behind them, {path.ending_image}"
    )


def moral(world: World, leader: Entity, helper: Entity) -> None:
    world.facts["lesson_spoken"] = True
    leader.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'"A quick paw may start a task," said {leader.id}, "but two steady friends can finish it well."'
    )
    world.say(
        "And so the little neighbors learned that haste makes trouble, while shared care carries even a trembling thing to its place."
    )


def tell(
    cargo: Cargo,
    path: Path,
    plan: Plan,
    leader_name: str = "Pip",
    leader_type: str = "mouse",
    helper_name: str = "Mira",
    helper_type: str = "wren",
    elder_name: str = "Old Thistle",
    elder_type: str = "tortoise",
) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_type,
            label=leader_name,
            role="leader",
            attrs={"pronouns": {"subject": "they", "object": "them", "possessive": "their"}},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
            attrs={"pronouns": {"subject": "they", "object": "them", "possessive": "their"}},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            label=elder_name,
            role="elder",
            attrs={"pronouns": {"subject": "they", "object": "them", "possessive": "their"}},
        )
    )
    world.add(Entity(id="saucer", type="saucer", label="saucer"))
    world.add(Entity(id="cargo", type="cargo", label=cargo.label))
    world.facts.update(
        cargo_cfg=cargo,
        path_cfg=path,
        plan_cfg=plan,
        leader=leader,
        helper=helper,
        elder=elder,
        instability=instability_of(cargo, path),
        support=0,
        attempt_mode="",
        spill_happened=False,
        delivered=False,
        lesson_spoken=False,
        predicted_spill=False,
    )

    introduce(world, leader, helper, elder, cargo)
    purpose(world, elder, path)

    world.para()
    temptation(world, leader)
    warning(world, helper, leader, cargo, path)
    solo_attempt(world, leader, path)
    narrate_spill(world, cargo)

    world.para()
    regroup(world, leader, helper, plan)
    tidy_and_retry(world, cargo)
    team_attempt(world, leader, helper, plan, path)
    deliver(world, elder, cargo, path)

    world.para()
    moral(world, leader, helper)

    return world


CARGOES = {
    "berries": Cargo(
        id="berries",
        label="berries",
        phrase="three glossy blackberries and two red currants",
        risk=2,
        spill_word="The berries rolled like marbles",
        delivery_line="the berries still shone on the saucer, bright as tiny beads, and",
        tags={"berries", "sharing"},
    ),
    "milk": Cargo(
        id="milk",
        label="milk",
        phrase="a little pool of warm milk with mint floating on top",
        risk=2,
        spill_word="A pale ribbon of milk ran across the paint",
        delivery_line="the milk still lay quiet in the saucer, hardly trembling, and",
        tags={"milk", "sharing"},
    ),
    "seeds": Cargo(
        id="seeds",
        label="seeds",
        phrase="a neat mound of sunflower seeds",
        risk=1,
        spill_word="The seeds scattered in a dry little ring",
        delivery_line="the seeds still sat in a tidy mound upon the saucer, and",
        tags={"seeds", "sharing"},
    ),
    "plum_slice": Cargo(
        id="plum_slice",
        label="plum slice",
        phrase="a single purple plum slice",
        risk=0,
        spill_word="The plum slice slid to one side",
        delivery_line="the plum slice still rested in the center of the saucer, and",
        tags={"fruit"},
    ),
}

PATHS = {
    "windy_bridge": Path(
        id="windy_bridge",
        label="the windy bridge",
        phrase="the narrow windy bridge",
        jolt=2,
        scene="a brook that talked over stones",
        stumble="The bridge boards gave a small shiver under each step, and a breeze nudged at the saucer.",
        ending_image="the bridge no longer seemed fierce, only narrow and honest under the sun",
        tags={"bridge", "wind"},
    ),
    "root_steps": Path(
        id="root_steps",
        label="the root steps",
        phrase="the crooked root steps",
        jolt=2,
        scene="an oak where roots wrinkled up from the earth",
        stumble="Each root rose like a bent finger, so the saucer tilted first one way and then the other.",
        ending_image="the roots lay in their old crooked places, yet the friends had learned how to cross them",
        tags={"roots", "forest"},
    ),
    "pebble_lane": Path(
        id="pebble_lane",
        label="the pebble lane",
        phrase="the little pebble lane",
        jolt=1,
        scene="a lane of pale stones between thyme bushes",
        stumble="The pebbles clicked and shifted beneath quick feet, sending tiny shakes up through the saucer.",
        ending_image="the lane glittered with small stones, and each step now looked worth taking slowly",
        tags={"pebbles", "path"},
    ),
    "moss_mat": Path(
        id="moss_mat",
        label="the moss mat",
        phrase="the soft moss path",
        jolt=0,
        scene="a green patch where even footsteps sounded sleepy",
        stumble="The moss gave softly and hardly stirred the saucer at all.",
        ending_image="the moss kept its soft green hush",
        tags={"moss"},
    ),
}

PLANS = {
    "shared_rims": Plan(
        id="shared_rims",
        label="holding both rims together",
        support=3,
        sense=2,
        propose="each hold one rim of the saucer",
        carry_text="held one rim of the saucer each",
        qa_text="They each held one rim of the saucer so one wobble could be corrected by the other.",
        tags={"teamwork", "balance"},
    ),
    "leaf_hammock": Plan(
        id="leaf_hammock",
        label="a leaf hammock",
        support=4,
        sense=3,
        propose="set the saucer on a broad dock leaf and carry the leaf corners together",
        carry_text="set the saucer on a broad dock leaf and carried the leaf corners together",
        qa_text="They made a leaf hammock under the saucer and carried the corners together, which kept the saucer much steadier.",
        tags={"teamwork", "leaf", "balance"},
    ),
    "twig_handle": Plan(
        id="twig_handle",
        label="a twig handle",
        support=2,
        sense=1,
        propose="tie a twig to the saucer and hurry with that",
        carry_text="tried to guide the saucer with a thin twig handle",
        qa_text="They used only a thin twig handle.",
        tags={"twig"},
    ),
}

ANIMALS = [
    ("Pip", "mouse"),
    ("Mira", "wren"),
    ("Nettle", "squirrel"),
    ("Tansy", "mole"),
    ("Reed", "hedgehog"),
    ("Lark", "rabbit"),
    ("Clover", "field mouse"),
    ("Bramble", "robin"),
]

ELDERS = [
    ("Old Thistle", "tortoise"),
    ("Aunt Willow", "hedgehog"),
    ("Mossy Fern", "toad"),
]


@dataclass
class StoryParams:
    cargo: str
    path: str
    plan: str
    leader_name: str
    leader_type: str
    helper_name: str
    helper_type: str
    elder_name: str
    elder_type: str
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
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    plan = f["plan_cfg"]
    leader = f["leader"]
    helper = f["helper"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the word "saucer" and shows how haste can cause trouble before teamwork fixes it.',
        f"Tell a cautionary teamwork story about {leader.id} and {helper.id} carrying {cargo.label} on a saucer across {path.phrase}, where one hurries, something spills, and they succeed only after working together.",
        f"Write a gentle fable in which a risky solo attempt fails, then a wiser plan using {plan.label} helps two friends finish their kind errand.",
    ]


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means two or more people help with the same job. They share the hard parts so the job becomes easier and steadier."
        )
    ],
    "balance": [
        (
            "What does balance mean?",
            "Balance means keeping something steady so it does not tip over. When both sides are supported, it is easier to keep balance."
        )
    ],
    "bridge": [
        (
            "Why is it hard to carry something on a bridge?",
            "A narrow bridge can shake a little and leave less room for careful steps. That makes a wobbly thing easier to spill."
        )
    ],
    "roots": [
        (
            "Why can tree roots make walking tricky?",
            "Roots can stick up higher than the ground around them. Your feet have to step over them carefully so you do not wobble."
        )
    ],
    "milk": [
        (
            "Why does milk spill easily?",
            "Milk is a liquid, so it slides and sloshes when a bowl or saucer tips. Even a small shake can send it over the edge."
        )
    ],
    "berries": [
        (
            "Why can berries roll off a plate or saucer?",
            "Round berries can roll when a dish tilts. If the edge tips even a little, they may start moving like tiny balls."
        )
    ],
    "seeds": [
        (
            "Why can small seeds scatter?",
            "Small seeds are light and loose, so a bump can send them in many directions. That is why careful hands matter."
        )
    ],
    "leaf": [
        (
            "How can a leaf help carry something?",
            "A broad leaf can spread the weight under a dish. If two friends hold the leaf together, the load can stay steadier."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "balance", "bridge", "roots", "milk", "berries", "seeds", "leaf"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    elder = f["elder"]
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    plan = f["plan_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} the {leader.type} and {helper.id} the {helper.type}. They were trying to bring a kind gift to {elder.id} the {elder.type}."
        ),
        (
            "What were they carrying?",
            f"They were carrying {cargo.phrase} on a saucer. The saucer made the gift look delicate, which is why steady hands mattered."
        ),
        (
            f"Why did {helper.id} warn {leader.id}?",
            f"{helper.id} warned {leader.id} because {cargo.label} could shift on the saucer and {path.label} would shake it. The danger came from the wobbly load and the jolting path together."
        ),
    ]
    if f["spill_happened"]:
        qa.append(
            (
                f"What happened when {leader.id} tried to carry the saucer alone?",
                f"The saucer tipped and some of the {cargo.label} spilled. {leader.id} had hurried onto {path.phrase}, so the path jolts beat one pair of paws."
            )
        )
    if f["delivered"]:
        qa.append(
            (
                "How did they solve the problem?",
                f"They stopped hurrying and worked together. {plan.qa_text} That gave the saucer enough support to stay level."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They delivered the gift safely to {elder.id}. The ending proves what changed, because they crossed the same path carefully together instead of rushing alone."
            )
        )
    if f["lesson_spoken"]:
        qa.append(
            (
                "What lesson did they learn?",
                "They learned that being quick is not the same as being wise. A shared job can succeed where a proud, hurried try goes wrong."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"teamwork", "balance"}
    tags |= set(world.facts["cargo_cfg"].tags)
    tags |= set(world.facts["path_cfg"].tags)
    tags |= set(world.facts["plan_cfg"].tags)
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
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k in {'instability', 'support', 'attempt_mode', 'spill_happened', 'delivered', 'lesson_spoken', 'predicted_spill'})}}}")
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
        lines.append(f"  {ent.id:12} ({ent.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="berries",
        path="windy_bridge",
        plan="leaf_hammock",
        leader_name="Pip",
        leader_type="mouse",
        helper_name="Mira",
        helper_type="wren",
        elder_name="Old Thistle",
        elder_type="tortoise",
    ),
    StoryParams(
        cargo="milk",
        path="root_steps",
        plan="leaf_hammock",
        leader_name="Nettle",
        leader_type="squirrel",
        helper_name="Tansy",
        helper_type="mole",
        elder_name="Aunt Willow",
        elder_type="hedgehog",
    ),
    StoryParams(
        cargo="seeds",
        path="windy_bridge",
        plan="shared_rims",
        leader_name="Reed",
        leader_type="hedgehog",
        helper_name="Lark",
        helper_type="rabbit",
        elder_name="Mossy Fern",
        elder_type="toad",
    ),
    StoryParams(
        cargo="milk",
        path="pebble_lane",
        plan="shared_rims",
        leader_name="Clover",
        leader_type="field mouse",
        helper_name="Bramble",
        helper_type="robin",
        elder_name="Old Thistle",
        elder_type="tortoise",
    ),
]


ASP_RULES = r"""
solo_support(2).
sense_min(2).

risky(C,P) :- cargo(C), path(P), cargo_risk(C,CR), path_jolt(P,PJ), CR + PJ > 2.
sensible(Plan) :- plan(Plan), plan_sense(Plan,S), sense_min(M), S >= M.
stabilizes(Plan,C,P) :- plan(Plan), cargo(C), path(P),
                        plan_support(Plan,PS), cargo_risk(C,CR), path_jolt(P,PJ),
                        PS >= CR + PJ.
valid(C,P) :- risky(C,P), sensible(Plan), stabilizes(Plan,C,P).

outcome(spill_then_success) :- chosen_cargo(C), chosen_path(P), chosen_plan(Plan),
                               risky(C,P), sensible(Plan), stabilizes(Plan,C,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_risk", cargo_id, cargo.risk))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("path_jolt", path_id, path.jolt))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("plan_support", plan_id, plan.support))
        lines.append(asp.fact("plan_sense", plan_id, plan.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(plan for (plan,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_plan", params.plan),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


def outcome_of(params: StoryParams) -> str:
    cargo = CARGOES[params.cargo]
    path = PATHS[params.path]
    plan = PLANS[params.plan]
    if can_spill_alone(cargo, path) and plan.sense >= SENSE_MIN and can_recover(cargo, path, plan):
        return "spill_then_success"
    return "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a saucer, a hurried mistake, and a teamwork lesson told like a little fable."
    )
    ap.add_argument("--cargo", choices=sorted(CARGOES))
    ap.add_argument("--path", choices=sorted(PATHS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid cargo/path pairs and sensible plans from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    a, b = rng.sample(ANIMALS, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.path:
        cargo = CARGOES[args.cargo]
        path = PATHS[args.path]
        if (args.cargo, args.path) not in set(valid_combos()):
            raise StoryError(explain_combo_rejection(cargo, path))

    combos = [
        combo for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.path is None or combo[1] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, path_id = rng.choice(sorted(combos))
    cargo = CARGOES[cargo_id]
    path = PATHS[path_id]

    if args.plan:
        plan = PLANS[args.plan]
        if not (plan.sense >= SENSE_MIN and can_recover(cargo, path, plan)):
            raise StoryError(explain_plan_rejection(plan, cargo, path))
        plan_id = args.plan
    else:
        good_plans = [
            pid for pid, plan in PLANS.items()
            if plan.sense >= SENSE_MIN and can_recover(cargo, path, plan)
        ]
        if not good_plans:
            raise StoryError("(No sensible teamwork plan can solve the chosen saucer problem.)")
        plan_id = rng.choice(sorted(good_plans))

    (leader_name, leader_type), (helper_name, helper_type) = _pick_pair(rng)
    elder_name, elder_type = rng.choice(ELDERS)
    return StoryParams(
        cargo=cargo_id,
        path=path_id,
        plan=plan_id,
        leader_name=leader_name,
        leader_type=leader_type,
        helper_name=helper_name,
        helper_type=helper_type,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOES:
        raise StoryError(f"Unknown cargo: {params.cargo}")
    if params.path not in PATHS:
        raise StoryError(f"Unknown path: {params.path}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown plan: {params.plan}")

    cargo = CARGOES[params.cargo]
    path = PATHS[params.path]
    plan = PLANS[params.plan]

    if (params.cargo, params.path) not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(cargo, path))
    if plan.sense < SENSE_MIN or not can_recover(cargo, path, plan):
        raise StoryError(explain_plan_rejection(plan, cargo, path))

    world = tell(
        cargo=cargo,
        path=path,
        plan=plan,
        leader_name=params.leader_name,
        leader_type=params.leader_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print("MISMATCH in valid cargo/path pairs:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {p.id for p in sensible_plans()}
    asp_sensible = set(asp_sensible_plans())
    if py_sensible == asp_sensible:
        print(f"OK: sensible plans match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            continue

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
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (cargo, path) pairs:\n")
        for cargo_id, path_id in combos:
            print(f"  {cargo_id:10} {path_id}")
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
            header = f"### {p.leader_name} & {p.helper_name}: {p.cargo} over {p.path} with {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
