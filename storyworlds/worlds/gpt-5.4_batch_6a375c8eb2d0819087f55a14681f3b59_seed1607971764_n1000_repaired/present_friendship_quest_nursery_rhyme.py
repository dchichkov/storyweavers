#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py
====================================================================

A standalone story world for a small nursery-rhyme-flavored friendship quest:
two friends carry a present across a tricky path to a third friend, notice what
might go wrong, choose the right helper, and arrive with the gift safe.

The world is intentionally narrow. A route has one main risk, a present has the
kind of trouble it cannot withstand, and a helper is only reasonable when it
both guards that risk and suits the present's shape. The story's middle turn is
driven by world state: the friends foresee trouble, feel the wobble of the
journey, fetch the right helper together, and then the ending image proves that
their friendship and care changed the outcome.

Run it
------
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py --route windy_hill --present paper_pinwheel
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py --helper little_wagon
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/present_friendship_quest_nursery_rhyme.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: list[str] = field(default_factory=list)
    helper_guards: set[str] = field(default_factory=set)
    helper_supports: set[str] = field(default_factory=set)
    present_shape: str = ""
    present_vulnerable: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose"}
        male = {"boy", "father", "frog", "toad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Route:
    id: str
    name: str
    risk: str
    path_line: str
    warning_line: str
    helper_line: str
    march_line: str
    arrival_line: str
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
class Present:
    id: str
    label: str
    phrase: str
    shape: str
    vulnerable: set[str]
    opening_line: str
    ending_line: str
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
    phrase: str
    guards: set[str]
    supports: set[str]
    carry_style: str
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
class StoryParams:
    route: str
    present: str
    helper: str
    friend1: str
    friend1_type: str
    friend2: str
    friend2_type: str
    recipient: str
    recipient_type: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_exposed_damage(world: World) -> list[str]:
    out: list[str] = []
    risk = world.facts["route_risk"]
    present = world.get("present")
    if present.meters["travelling"] < THRESHOLD:
        return out
    if risk not in present.present_vulnerable:
        return out
    protected = risk in present.helper_guards and present.present_shape in present.helper_supports
    if protected:
        return out
    sig = ("damage", risk)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    present.meters["damaged"] += 1
    present.meters["wobble"] += 1
    for kid_id in ("friend1", "friend2"):
        kid = world.get(kid_id)
        kid.memes["worry"] += 1
    out.append("__damage__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    present = world.get("present")
    if present.meters["travelling"] < THRESHOLD:
        return out
    if present.meters["helped"] < THRESHOLD:
        return out
    if len(present.carried_by) < 2:
        return out
    sig = ("teamwork", tuple(sorted(present.carried_by)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid_id in present.carried_by:
        kid = world.get(kid_id)
        kid.memes["teamwork"] += 1
        kid.memes["calm"] += 1
    present.meters["steady"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="exposed_damage", tag="physical", apply=_r_exposed_damage),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
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


ROUTES = {
    "windy_hill": Route(
        id="windy_hill",
        name="Windy Hill",
        risk="wind",
        path_line="Over Windy Hill the grass bent low, and every little bow went to and fro.",
        warning_line="The hill kept humming shoo and swish, the sort of wind that likes to tug and wish.",
        helper_line="A lid would hush the huffing breeze and keep the gift from flying with the trees.",
        march_line="Up Windy Hill they climbed in time while clover bells made chiming rhyme.",
        arrival_line="Beyond the hill stood Wren's round door with ivy curls about the floor.",
        tags={"wind", "hill"},
    ),
    "bumpy_lane": Route(
        id="bumpy_lane",
        name="Bumpy Lane",
        risk="bump",
        path_line="Down Bumpy Lane the cobbles bumped, and every cartwheel thudded, jumped, and thumped.",
        warning_line="The lane went bump and bob and bound, the sort of path that shakes what rides too round.",
        helper_line="A wagon would keep rolling level and save the gift from every stone and bevel.",
        march_line="Along Bumpy Lane they rolled with care and sang a soft-ta-ta into the air.",
        arrival_line="At lane's end shone Wren's garden gate, bright with peas and growing late.",
        tags={"bump", "lane"},
    ),
    "dusky_lane": Route(
        id="dusky_lane",
        name="Dusky Lane",
        risk="dark",
        path_line="Through Dusky Lane the hedges grew, and evening stitched the sky in blue.",
        warning_line="The lane went dim and dusky-deep, the sort of dark where tiny gifts can slip and sleep.",
        helper_line="A lantern would lay down a little road and help them mind each precious load.",
        march_line="Through Dusky Lane they stepped in light while one gold lantern held back night.",
        arrival_line="Past the lane was Wren's warm porch, lit now by their small friendly torch.",
        tags={"dark", "lane"},
    ),
}

PRESENTS = {
    "paper_pinwheel": Present(
        id="paper_pinwheel",
        label="pinwheel",
        phrase="a paper pinwheel tied with mint-green string",
        shape="light",
        vulnerable={"wind"},
        opening_line="It was a present bright and thin, a paper pinwheel packed with grin.",
        ending_line="The pinwheel spun in sunset air and painted little circles there.",
        tags={"present", "paper", "wind"},
    ),
    "flower_crown": Present(
        id="flower_crown",
        label="flower crown",
        phrase="a flower crown woven from daisies and thyme",
        shape="light",
        vulnerable={"wind"},
        opening_line="It was a present soft and sweet, a flower crown for dancing feet.",
        ending_line="The flower crown sat fresh and fair with petal stars in Wren's brown hair.",
        tags={"present", "flowers", "wind"},
    ),
    "berry_tart": Present(
        id="berry_tart",
        label="berry tart",
        phrase="a small berry tart with a crust like a golden moon",
        shape="soft",
        vulnerable={"bump"},
        opening_line="It was a present round and dear, a berry tart for festival cheer.",
        ending_line="The berry tart still held its dome, with shiny berries safe at home.",
        tags={"present", "food", "bump"},
    ),
    "plum_cake": Present(
        id="plum_cake",
        label="plum cake",
        phrase="a plum cake tucked in a blue cloth wrap",
        shape="soft",
        vulnerable={"bump"},
        opening_line="It was a present plump and neat, a plum cake made for sharing sweet.",
        ending_line="The plum cake reached the plate just right, all sugared top and purple bite.",
        tags={"present", "food", "bump"},
    ),
    "silver_bell": Present(
        id="silver_bell",
        label="silver bell",
        phrase="a tiny silver bell on a red thread bow",
        shape="tiny",
        vulnerable={"dark"},
        opening_line="It was a present small and fine, a silver bell with starry shine.",
        ending_line="The silver bell gave tink-tink-twee, a happy note for all to see.",
        tags={"present", "bell", "dark"},
    ),
    "button_charm": Present(
        id="button_charm",
        label="button charm",
        phrase="a little button charm tucked in a leaf-green pouch",
        shape="tiny",
        vulnerable={"dark"},
        opening_line="It was a present wee and bright, a button charm that caught the light.",
        ending_line="The button charm lay safe and sound, a moonlit speck that still was found.",
        tags={"present", "tiny", "dark"},
    ),
}

HELPERS = {
    "lidded_basket": Helper(
        id="lidded_basket",
        label="lidded basket",
        phrase="a little lidded basket",
        guards={"wind"},
        supports={"light"},
        carry_style="one held the handle while the other kept the lid snug tight",
        tags={"basket", "wind"},
    ),
    "little_wagon": Helper(
        id="little_wagon",
        label="little wagon",
        phrase="a little red wagon",
        guards={"bump"},
        supports={"soft"},
        carry_style="one pulled the wagon while the other walked beside to steady it",
        tags={"wagon", "bump"},
    ),
    "glow_lantern": Helper(
        id="glow_lantern",
        label="glow lantern",
        phrase="a glow lantern",
        guards={"dark"},
        supports={"tiny"},
        carry_style="one carried the lantern while the other cupped the present close in the light",
        tags={"lantern", "dark"},
    ),
}

GIRL_NAMES = ["Dot", "Mabel", "Lark", "Nell", "Tilly", "June"]
BOY_NAMES = ["Pip", "Robin", "Moss", "Tad", "Finn", "Kit"]
RECIPIENT_NAMES = [("Wren", "girl"), ("Bram", "boy"), ("Poppy", "girl"), ("Ned", "boy")]

KNOWLEDGE = {
    "present": [
        (
            "What is a present?",
            "A present is a gift you choose or make for someone else. You give it to show care, kindness, or celebration.",
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about another person and treating them kindly. Good friends help each other when something feels hard.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a purpose, like going somewhere to do something important. In stories, a quest often has a problem to solve on the way.",
        )
    ],
    "wind": [
        (
            "Why can wind be a problem for a light gift?",
            "Wind pushes and tugs at things that are light. A light paper or flower gift can blow away or bend if it is not covered.",
        )
    ],
    "bump": [
        (
            "Why can a bumpy road hurt a soft cake?",
            "A soft cake can wobble and squish when it is jolted. A smoother ride helps it keep its shape.",
        )
    ],
    "dark": [
        (
            "Why does darkness make a tiny object hard to carry?",
            "When it is dark, small things are harder to see. That makes them easier to drop or lose.",
        )
    ],
    "basket": [
        (
            "What does a basket lid do?",
            "A basket lid covers what is inside. It helps keep a light gift from being tugged by the wind.",
        )
    ],
    "wagon": [
        (
            "Why is a wagon useful for carrying food?",
            "A wagon can help carry food more level than hands alone. That makes bumps less likely to squish a soft treat.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes light so you can see where to step and what to hold. It helps people move carefully in the dark.",
        )
    ],
}
KNOWLEDGE_ORDER = ["present", "friendship", "quest", "wind", "bump", "dark", "basket", "wagon", "lantern"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for present_id, present in PRESENTS.items():
            for helper_id, helper in HELPERS.items():
                if route.risk in present.vulnerable and route.risk in helper.guards and present.shape in helper.supports:
                    combos.append((route_id, present_id, helper_id))
    return sorted(combos)


def explain_helper(route: Route, present: Present, helper: Helper) -> str:
    reasons: list[str] = []
    if route.risk not in helper.guards:
        reasons.append(f"{helper.label} does not solve the {route.risk} trouble on {route.name}")
    if present.shape not in helper.supports:
        reasons.append(f"{helper.label} is not a good carrier for a {present.shape} present like the {present.label}")
    if route.risk not in present.vulnerable:
        reasons.append(f"the {present.label} is not the kind of gift that would be at risk on {route.name}")
    if not reasons:
        reasons.append("that combination does not make a sensible story here")
    return "(No story: " + "; ".join(reasons) + ".)"


def predict_damage(world: World) -> dict:
    sim = world.copy()
    present = sim.get("present")
    present.meters["travelling"] += 1
    propagate(sim, narrate=False)
    return {
        "damaged": present.meters["damaged"] >= THRESHOLD,
        "wobble": present.meters["wobble"] >= THRESHOLD,
        "risk": sim.facts["route_risk"],
    }


def introduce(world: World, a: Entity, b: Entity, recipient: Entity, present_cfg: Present) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} met at morning light, with skipping steps and faces bright."
    )
    world.say(
        f'"For {recipient.id}!" they sang with cheer. {present_cfg.opening_line}'
    )
    world.say(
        f"They had made {present_cfg.phrase} as a present for their friend, and they wanted to carry it before the noon bells chimed."
    )


def choose_route(world: World, route: Route, recipient: Entity) -> None:
    world.say(route.path_line)
    world.say(
        f"{route.arrival_line} That was where {recipient.id} waited for the knock and the friendly surprise."
    )


def warning_beat(world: World, a: Entity, b: Entity, route: Route, present_cfg: Present) -> None:
    pred = predict_damage(world)
    world.facts["predicted_damage"] = pred["damaged"]
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(route.warning_line)
    world.say(
        f'{a.id} peeped at the {present_cfg.label} and said, "If we hurry just as we are, the {route.risk} may spoil our present."'
    )
    world.say(
        f'{b.id} nodded. "Then our quest needs thinking feet, not only quick ones."'
    )


def fetch_helper(world: World, a: Entity, b: Entity, helper_cfg: Helper, route: Route) -> Entity:
    helper = world.add(
        Entity(
            id="helper",
            kind="thing",
            type="helper",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            attrs={},
            helper_guards=set(helper_cfg.guards),
            helper_supports=set(helper_cfg.supports),
        )
    )
    world.say(route.helper_line)
    world.say(
        f"So back by the gate they fetched {helper_cfg.phrase}. {a.id} smiled first, and then {b.id} smiled too."
    )
    return helper


def travel(world: World, a: Entity, b: Entity, route: Route, helper_cfg: Helper) -> None:
    present = world.get("present")
    helper = world.get("helper")
    present.helper_guards = set(helper.helper_guards)
    present.helper_supports = set(helper.helper_supports)
    present.carried_by = ["friend1", "friend2"]
    present.meters["helped"] += 1
    present.meters["travelling"] += 1
    helper.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They set the present inside {helper_cfg.phrase}, and {helper_cfg.carry_style}."
    )
    world.say(route.march_line)
    if present.meters["steady"] >= THRESHOLD:
        world.say(
            f"The present stayed snug and steady, because the right helper matched the trouble on the road and both friends worked together."
        )


def deliver(world: World, a: Entity, b: Entity, recipient: Entity, present_cfg: Present) -> None:
    present = world.get("present")
    present.meters["arrived"] += 1
    recipient.memes["surprise"] += 1
    recipient.memes["joy"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    recipient.memes["friendship"] += 1
    world.say(
        f'{recipient.id} opened the door and blinked in delight. "{a.id} and {b.id}! You came!"'
    )
    world.say(
        f"They lifted out the present at last, safe and neat from first to last. {present_cfg.ending_line}"
    )
    world.say(
        f'Soon all three friends were laughing near, and the quest felt small because their friendship had carried it clear.'
    )


def tell(
    route: Route,
    present_cfg: Present,
    helper_cfg: Helper,
    friend1_name: str,
    friend1_type: str,
    friend2_name: str,
    friend2_type: str,
    recipient_name: str,
    recipient_type: str,
) -> World:
    world = World()
    world.facts["route_risk"] = route.risk
    world.facts["route"] = route
    world.facts["present_cfg"] = present_cfg
    world.facts["helper_cfg"] = helper_cfg

    a = world.add(
        Entity(
            id="friend1",
            kind="character",
            type=friend1_type,
            label=friend1_name,
            role="courier",
            attrs={"name": friend1_name},
        )
    )
    b = world.add(
        Entity(
            id="friend2",
            kind="character",
            type=friend2_type,
            label=friend2_name,
            role="courier",
            attrs={"name": friend2_name},
        )
    )
    recipient = world.add(
        Entity(
            id="recipient",
            kind="character",
            type=recipient_type,
            label=recipient_name,
            role="recipient",
            attrs={"name": recipient_name},
        )
    )
    present = world.add(
        Entity(
            id="present",
            kind="thing",
            type="present",
            label=present_cfg.label,
            phrase=present_cfg.phrase,
            role="present",
            attrs={},
            present_shape=present_cfg.shape,
            present_vulnerable=set(present_cfg.vulnerable),
        )
    )

    world.facts["friend1_name"] = friend1_name
    world.facts["friend2_name"] = friend2_name
    world.facts["recipient_name"] = recipient_name

    introduce(world, a, b, recipient, present_cfg)
    world.para()
    choose_route(world, route, recipient)
    warning_beat(world, a, b, route, present_cfg)
    world.para()
    fetch_helper(world, a, b, helper_cfg, route)
    travel(world, a, b, route, helper_cfg)
    world.para()
    deliver(world, a, b, recipient, present_cfg)

    world.facts.update(
        friend1=a,
        friend2=b,
        recipient=recipient,
        present=present,
        route=route,
        present_cfg=present_cfg,
        helper=world.get("helper"),
        helper_cfg=helper_cfg,
        arrived=present.meters["arrived"] >= THRESHOLD,
        damaged=present.meters["damaged"] >= THRESHOLD,
        teamwork=present.meters["steady"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    route = world.facts["route"]
    present_cfg = world.facts["present_cfg"]
    f1 = world.facts["friend1_name"]
    f2 = world.facts["friend2_name"]
    recipient = world.facts["recipient_name"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that uses the word "present" and features friendship and a quest.',
        f"Tell a gentle quest story where {f1} and {f2} carry a present to {recipient}, notice a problem on {route.name}, and solve it together.",
        f"Write a rhyming story about friends bringing {present_cfg.phrase} across a tricky path and arriving with the gift safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f1 = world.facts["friend1"]
    f2 = world.facts["friend2"]
    recipient = world.facts["recipient"]
    route = world.facts["route"]
    present_cfg = world.facts["present_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f1.label}, {f2.label}, and their friend {recipient.label}. {f1.label} and {f2.label} go on a little quest to bring a present to {recipient.label}.",
        ),
        (
            "What was the present?",
            f"The present was {present_cfg.phrase}. They had made or chosen it especially for their friend, which is why they wanted to carry it so carefully.",
        ),
        (
            "Where were they going?",
            f"They were going along {route.name} to {recipient.label}'s door. The trip was a quest because they had one kind job to finish before they arrived.",
        ),
        (
            "Why did they stop to think before hurrying on?",
            f"They knew the {route.risk} on {route.name} could spoil the {present_cfg.label}. The warning mattered because that gift was exactly the kind that could be hurt by that trouble.",
        ),
        (
            f"How did {f1.label} and {f2.label} solve the problem?",
            f"They went back and fetched {helper_cfg.phrase}. That helper matched both the road and the present, so it kept the gift safe while the two friends carried it together.",
        ),
        (
            "How did friendship help on the quest?",
            f"They did not try to rush alone. They talked, chose a good plan, and shared the carrying, so the present stayed steady and everyone reached the door happily.",
        ),
    ]
    if world.facts["arrived"] and not world.facts["damaged"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended with {recipient.label} opening the door to a safe present and smiling in delight. The ending proves the quest worked because the gift arrived neat and ready to give.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    route = world.facts["route"]
    helper_cfg = world.facts["helper_cfg"]
    tags = {"present", "friendship", "quest"} | set(route.tags) | set(helper_cfg.tags)
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"label={ent.label!r}"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.present_shape:
            bits.append(f"shape={ent.present_shape}")
        if ent.present_vulnerable:
            bits.append(f"vulnerable={sorted(ent.present_vulnerable)}")
        if ent.helper_guards:
            bits.append(f"guards={sorted(ent.helper_guards)}")
        if ent.helper_supports:
            bits.append(f"supports={sorted(ent.helper_supports)}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  route_risk={world.facts.get('route_risk')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
present_at_risk(R, P) :- route(R), present(P), risk_of(R, K), vulnerable(P, K).
helper_fits(P, H)     :- present(P), helper(H), shape_of(P, S), supports(H, S).
helper_solves(R, H)   :- route(R), helper(H), risk_of(R, K), guards(H, K).
valid(R, P, H)        :- present_at_risk(R, P), helper_fits(P, H), helper_solves(R, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("risk_of", route_id, route.risk))
    for present_id, present in PRESENTS.items():
        lines.append(asp.fact("present", present_id))
        lines.append(asp.fact("shape_of", present_id, present.shape))
        for risk in sorted(present.vulnerable):
            lines.append(asp.fact("vulnerable", present_id, risk))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for risk in sorted(helper.guards):
            lines.append(asp.fact("guards", helper_id, risk))
        for shape in sorted(helper.supports):
            lines.append(asp.fact("supports", helper_id, shape))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        route="windy_hill",
        present="paper_pinwheel",
        helper="lidded_basket",
        friend1="Pip",
        friend1_type="boy",
        friend2="Dot",
        friend2_type="girl",
        recipient="Wren",
        recipient_type="girl",
    ),
    StoryParams(
        route="windy_hill",
        present="flower_crown",
        helper="lidded_basket",
        friend1="Robin",
        friend1_type="boy",
        friend2="Mabel",
        friend2_type="girl",
        recipient="Poppy",
        recipient_type="girl",
    ),
    StoryParams(
        route="bumpy_lane",
        present="berry_tart",
        helper="little_wagon",
        friend1="Nell",
        friend1_type="girl",
        friend2="Finn",
        friend2_type="boy",
        recipient="Bram",
        recipient_type="boy",
    ),
    StoryParams(
        route="dusky_lane",
        present="silver_bell",
        helper="glow_lantern",
        friend1="June",
        friend1_type="girl",
        friend2="Kit",
        friend2_type="boy",
        recipient="Ned",
        recipient_type="boy",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: two friends carry a present on a quest and choose the right helper."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--present", choices=PRESENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.present and args.helper:
        route = ROUTES[args.route]
        present_cfg = PRESENTS[args.present]
        helper_cfg = HELPERS[args.helper]
        if (args.route, args.present, args.helper) not in set(valid_combos()):
            raise StoryError(explain_helper(route, present_cfg, helper_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.present is None or combo[1] == args.present)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        if args.route and args.present and args.helper:
            raise StoryError(explain_helper(ROUTES[args.route], PRESENTS[args.present], HELPERS[args.helper]))
        raise StoryError("(No valid combination matches the given options.)")

    route_id, present_id, helper_id = rng.choice(combos)
    recipient_name, recipient_type = rng.choice(RECIPIENT_NAMES)
    friend1_type = rng.choice(["girl", "boy"])
    friend2_type = rng.choice(["girl", "boy"])
    friend1 = _pick_name(rng, friend1_type, avoid={recipient_name})
    friend2 = _pick_name(rng, friend2_type, avoid={recipient_name, friend1})
    return StoryParams(
        route=route_id,
        present=present_id,
        helper=helper_id,
        friend1=friend1,
        friend1_type=friend1_type,
        friend2=friend2,
        friend2_type=friend2_type,
        recipient=recipient_name,
        recipient_type=recipient_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(No story: unknown route '{params.route}'.)")
    if params.present not in PRESENTS:
        raise StoryError(f"(No story: unknown present '{params.present}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if (params.route, params.present, params.helper) not in set(valid_combos()):
        raise StoryError(explain_helper(ROUTES[params.route], PRESENTS[params.present], HELPERS[params.helper]))

    world = tell(
        route=ROUTES[params.route],
        present_cfg=PRESENTS[params.present],
        helper_cfg=HELPERS[params.helper],
        friend1_name=params.friend1,
        friend1_type=params.friend1_type,
        friend2_name=params.friend2,
        friend2_type=params.friend2_type,
        recipient_name=params.recipient,
        recipient_type=params.recipient_type,
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
            emit(sample, trace=False, qa=True, header="### smoke test")
        finally:
            sys.stdout = old_stdout
        if not buffer.getvalue().strip():
            raise StoryError("emit produced no output")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(17))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved generation was empty")
        print("OK: default resolve_params()/generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, present, helper) combos:\n")
        for route_id, present_id, helper_id in combos:
            print(f"  {route_id:12} {present_id:15} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.friend1} and {p.friend2}: {p.present} on {p.route} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
