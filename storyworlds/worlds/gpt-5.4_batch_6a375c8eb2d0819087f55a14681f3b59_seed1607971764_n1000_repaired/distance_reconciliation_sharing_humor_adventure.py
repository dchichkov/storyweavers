#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py
==============================================================================

A standalone story world for a tiny adventure domain: two children set out on a
small expedition, one child rushes ahead with the only useful tool, a real
distance opens between them, and a funny moment softens the quarrel so they can
reconcile, share, and finish the adventure together.

The world is built around a reasonableness constraint: the chosen shared tool
must actually help with the chosen obstacle on the chosen route. A map helps at
a fork, a walking stick helps at a slippery brook, and a spyglass helps spot
trail ribbons through tall grass. The story then simulates what happens when one
child keeps that tool to themself at first.

Run it
------
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --route pinewoods --obstacle fork --tool map
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --route meadow --obstacle brook --tool map
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --all
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --qa --trace
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/distance_reconciliation_sharing_humor_adventure.py --verify
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
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Route:
    id: str
    place: str
    opening: str
    destination: str
    afford_obstacles: set[str] = field(default_factory=set)
    allow_comics: set[str] = field(default_factory=set)
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
    intro: str
    stuck: str
    together: str
    success: str
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
    helps: set[str] = field(default_factory=set)
    share_line: str = ""
    use_line: str = ""
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
class ComicBeat:
    id: str
    setup: str
    punch: str
    thaw: str
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


def _r_distance_gap(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    trail = world.get("trail")
    tool = world.get("tool")
    if leader.meters["ahead"] >= THRESHOLD and partner.meters["stuck"] >= THRESHOLD and tool.attrs.get("shared") == 0:
        sig = ("gap",)
        if sig not in world.fired:
            world.fired.add(sig)
            trail.meters["distance"] += 1
            leader.memes["guilt"] += 1
            partner.memes["hurt"] += 1
            partner.memes["annoyance"] += 1
            out.append("__distance__")
    return out


def _r_laughter_softens(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.memes["laughter"] >= THRESHOLD and partner.memes["laughter"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["softened"] += 1
            partner.memes["softened"] += 1
            if partner.memes["annoyance"] >= THRESHOLD:
                partner.memes["annoyance"] = max(0.0, partner.memes["annoyance"] - 1.0)
            out.append("__soften__")
    return out


def _r_shared_progress(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    partner = world.get("partner")
    trail = world.get("trail")
    tool = world.get("tool")
    if tool.attrs.get("shared") == 1 and partner.meters["stuck"] >= THRESHOLD:
        sig = ("shared_progress",)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.meters["stuck"] = 0.0
            partner.meters["progress"] += 1
            leader.meters["progress"] += 1
            trail.meters["distance"] = 0.0
            leader.meters["ahead"] = 0.0
            leader.memes["closeness"] += 1
            partner.memes["closeness"] += 1
            partner.memes["trust"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="distance_gap", tag="social", apply=_r_distance_gap),
    Rule(name="laughter_softens", tag="social", apply=_r_laughter_softens),
    Rule(name="shared_progress", tag="physical", apply=_r_shared_progress),
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


def valid_combo(route_id: str, obstacle_id: str, tool_id: str, comic_id: str) -> bool:
    route = ROUTES[route_id]
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    comic = COMICS[comic_id]
    return (
        obstacle.id in route.afford_obstacles
        and obstacle.id in tool.helps
        and comic.id in route.allow_comics
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for route_id in ROUTES:
        for obstacle_id in OBSTACLES:
            for tool_id in TOOLS:
                for comic_id in COMICS:
                    if valid_combo(route_id, obstacle_id, tool_id, comic_id):
                        out.append((route_id, obstacle_id, tool_id, comic_id))
    return out


def predict_gap(world: World) -> dict:
    sim = world.copy()
    leader = sim.get("leader")
    partner = sim.get("partner")
    leader.meters["ahead"] += 1
    partner.meters["stuck"] += 1
    sim.get("tool").attrs["shared"] = 0
    propagate(sim, narrate=False)
    return {
        "distance": sim.get("trail").meters["distance"],
        "partner_hurt": sim.get("partner").memes["hurt"],
    }


def introduce(world: World, leader: Entity, partner: Entity, route: Route, tool: Tool) -> None:
    leader.memes["excitement"] += 1
    partner.memes["excitement"] += 1
    world.say(
        f"{leader.id} and {partner.id} set off along {route.place} as if they were explorers on a grand expedition. "
        f"{route.opening}"
    )
    world.say(
        f"They were hunting for {route.destination}, and they carried {tool.phrase} like real adventurers."
    )


def reach_obstacle(world: World, leader: Entity, partner: Entity, obstacle: Obstacle) -> None:
    world.say(obstacle.intro)
    world.say(
        f"{partner.id} came up beside {leader.id}, ready to tackle it together."
    )


def hog_tool(world: World, leader: Entity, partner: Entity, tool: Tool, obstacle: Obstacle) -> None:
    pred = predict_gap(world)
    world.facts["predicted_distance"] = pred["distance"]
    tool_ent = world.get("tool")
    tool_ent.attrs["shared"] = 0
    leader.meters["ahead"] += 1
    partner.meters["stuck"] += 1
    leader.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I can do this faster," {leader.id} said, keeping {tool.label} close instead of passing it over.'
    )
    world.say(
        f"{leader.id} moved ahead, but {partner.id} had to stop. {obstacle.stuck}"
    )
    if world.get("trail").meters["distance"] >= THRESHOLD:
        world.say(
            f"Soon there was a real distance between them on the trail, and it felt bigger than a few steps."
        )


def complaint(world: World, partner: Entity, leader: Entity, tool: Tool) -> None:
    partner.memes["annoyance"] += 1
    world.say(
        f'"That is not an expedition, {leader.id}," {partner.id} called. "That is just you keeping {tool.label} to yourself."'
    )


def comic_turn(world: World, leader: Entity, partner: Entity, comic: ComicBeat) -> None:
    leader.memes["laughter"] += 1
    partner.memes["laughter"] += 1
    world.say(comic.setup.format(leader=leader.id, partner=partner.id))
    world.say(comic.punch.format(leader=leader.id, partner=partner.id))
    propagate(world, narrate=False)
    world.say(comic.thaw.format(leader=leader.id, partner=partner.id))


def reconcile_and_share(world: World, leader: Entity, partner: Entity, tool: Tool, obstacle: Obstacle) -> None:
    tool_ent = world.get("tool")
    tool_ent.attrs["shared"] = 1
    leader.memes["apology"] += 1
    partner.memes["forgiveness"] += 1
    world.say(
        f'{leader.id} looked back at the space between them and felt silly for making it so wide. '
        f'"You were right," {leader.pronoun()} said. "Adventurers are supposed to help each other."'
    )
    world.say(tool.share_line.format(leader=leader.id, partner=partner.id))
    propagate(world, narrate=False)
    world.say(obstacle.together.format(leader=leader.id, partner=partner.id, tool=tool.label))
    world.say(obstacle.success.format(leader=leader.id, partner=partner.id))


def ending(world: World, leader: Entity, partner: Entity, route: Route, tool: Tool) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"At last they found {route.destination}. The prize was only a tiny brass marker tied to a post, but to them it looked like treasure."
    )
    world.say(
        f"{partner.id} broke the last honey biscuit in half and shared it with {leader.id}, and {leader.id} let {partner.pronoun('object')} hold {tool.label} first for the walk back."
    )
    world.say(
        f"They laughed again and headed home side by side, with no distance between them except the long path curling behind."
    )


def tell(
    route: Route,
    obstacle: Obstacle,
    tool: Tool,
    comic: ComicBeat,
    *,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    partner_name: str = "Finn",
    partner_gender: str = "boy",
) -> World:
    world = World()
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner"))
    trail = world.add(Entity(id="trail", kind="thing", type="trail", label=route.place))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, attrs={"shared": 1}))
    world.facts["leader_name"] = leader_name
    world.facts["partner_name"] = partner_name
    world.facts["route"] = route
    world.facts["obstacle"] = obstacle
    world.facts["tool_cfg"] = tool
    world.facts["comic"] = comic
    world.facts["predicted_distance"] = 0.0

    introduce(world, leader, partner, route, tool)
    world.para()
    reach_obstacle(world, leader, partner, obstacle)
    hog_tool(world, leader, partner, tool, obstacle)
    complaint(world, partner, leader, tool)
    world.para()
    comic_turn(world, leader, partner, comic)
    reconcile_and_share(world, leader, partner, tool, obstacle)
    world.para()
    ending(world, leader, partner, route, tool)

    world.facts.update(
        leader=leader,
        partner=partner,
        trail=trail,
        tool=tool_ent,
        reconciled=leader.memes["apology"] >= THRESHOLD and partner.memes["forgiveness"] >= THRESHOLD,
        shared=tool_ent.attrs.get("shared") == 1,
        closed_distance=trail.meters["distance"] == 0.0,
    )
    return world


ROUTES = {
    "meadow": Route(
        id="meadow",
        place="the windy meadow trail",
        opening="Grass leaned and whispered on both sides, and every hill looked like the start of a secret map.",
        destination="the hilltop bell",
        afford_obstacles={"brook", "tall_grass"},
        allow_comics={"goose", "squeak"},
        tags={"trail", "meadow"},
    ),
    "pinewoods": Route(
        id="pinewoods",
        place="the pinewoods path",
        opening="Tall trees stood like watchtowers, and the path ducked in and out of cool green shadows.",
        destination="the old lookout stump",
        afford_obstacles={"fork", "brook"},
        allow_comics={"echo", "squeak"},
        tags={"trail", "forest"},
    ),
    "redcliffs": Route(
        id="redcliffs",
        place="the red-cliff path",
        opening="Red stones warmed in the sun, and scraps of ribbon flickered from bushes like tiny pirate flags.",
        destination="the driftwood flag at the ridge",
        afford_obstacles={"fork", "tall_grass"},
        allow_comics={"echo", "goose"},
        tags={"trail", "cliff"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="slippery brook",
        intro="Before long they reached a narrow brook full of shiny stepping stones.",
        stuck="The stones looked safe from the front, but from behind they were hard to judge, and one wrong step meant a cold splash.",
        together="{leader} passed the walking stick back and {partner} used it to test the stones. Then they crossed one after the other, trading steady hands and brave grins.",
        success="When they stepped onto the far bank together, the brook no longer felt like a wall.",
        tags={"brook", "water"},
    ),
    "fork": Obstacle(
        id="fork",
        label="forked trail",
        intro="Soon the trail split in two, with one path curling left and the other sneaking right between dark bushes.",
        stuck="Without the map, the little painted arrows were too far away to read, so guessing felt more like getting lost than exploring.",
        together="{leader} unfolded the map between them, and {partner} pointed out the tiny blue mark they had both missed. With heads close together, they chose the trail that bent toward the ridge.",
        success="The right path opened ahead of them, and the quarrel shrank behind like a wrong turn they had decided not to take.",
        tags={"map", "trail"},
    ),
    "tall_grass": Obstacle(
        id="tall_grass",
        label="tall grass",
        intro="After that the path vanished into tall grass that swished higher than their knees.",
        stuck="The red trail ribbons were hidden far ahead, so without help it was impossible to know which way the adventure was supposed to go.",
        together="{leader} handed over the spyglass first, and {partner} found the next red ribbon at once. They took turns spotting markers and calling directions until the path came back under their feet.",
        success="The grass stopped feeling like a maze once they searched it together.",
        tags={"grass", "trail"},
    ),
}

TOOLS = {
    "walking_stick": Tool(
        id="walking_stick",
        label="the walking stick",
        phrase="a smooth walking stick",
        helps={"brook"},
        share_line="{leader} held out the walking stick. \"You take the next turn,\" {leader} said, and {partner} smiled and took it.",
        use_line="They used the walking stick together.",
        tags={"stick", "sharing"},
    ),
    "map": Tool(
        id="map",
        label="the map",
        phrase="a folded map with corners rubbed soft",
        helps={"fork"},
        share_line="{leader} opened the map wide enough for both of them. This time {leader.pronoun} kept a finger still so {partner} could read too.",
        use_line="They read the map together.",
        tags={"map", "sharing"},
    ),
    "spyglass": Tool(
        id="spyglass",
        label="the spyglass",
        phrase="a brass spyglass that clicked when it opened",
        helps={"tall_grass"},
        share_line="{leader} put the spyglass into {partner}'s hands. \"Your turn to be lookout,\" {leader} said.",
        use_line="They took turns with the spyglass.",
        tags={"spyglass", "sharing"},
    ),
}

COMICS = {
    "echo": ComicBeat(
        id="echo",
        setup='"I am the greatest path-finder in the whole wood!" {leader} announced.',
        punch='From the trees came an echo that sounded much smaller: "whole wood... wood... wood..." It made {partner} snort first, and then {leader} did too.',
        thaw="The forest turned {leader}'s boast into a joke, and the angry part of the moment loosened.",
        tags={"echo", "laughter"},
    ),
    "goose": ComicBeat(
        id="goose",
        setup="Just then a very bossy goose waddled out from behind a rock.",
        punch='It stared at {leader}, honked right in the middle of the silence, and marched between them as if it were the captain of the expedition.',
        thaw="Both children burst out laughing, because even a goose seemed to know explorers were supposed to stick together.",
        tags={"goose", "laughter"},
    ),
    "squeak": ComicBeat(
        id="squeak",
        setup="{leader} took one more proud step ahead.",
        punch="The step landed on a patch of mud, and the boot made such a long squeak that it sounded like a tiny trumpet call for help.",
        thaw="For a second neither child could stay cross. The silly sound popped the quarrel like a bubble.",
        tags={"squeak", "laughter"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ava", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Finn", "Leo", "Max", "Sam", "Owen", "Theo", "Jack", "Ben"]


@dataclass
class StoryParams:
    route: str
    obstacle: str
    tool: str
    comic: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
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
    "map": [
        (
            "What does a map do?",
            "A map helps you see where paths and places are. It lets travelers choose a direction instead of guessing.",
        )
    ],
    "spyglass": [
        (
            "What is a spyglass?",
            "A spyglass is a small tube for seeing faraway things more clearly. Looking through it makes distant trail marks easier to spot.",
        )
    ],
    "stick": [
        (
            "Why can a walking stick help at a brook?",
            "A walking stick can tap the ground or a stone before you step. That helps you balance and check if a spot is safe.",
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of running water. Its stones can be slippery, so you need to cross carefully.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off far surfaces and comes back to you. That is why a voice can seem to answer itself in a wood or near rocks.",
        )
    ],
    "goose": [
        (
            "Why do geese honk?",
            "Geese honk to call, warn, or stay in touch with each other. Their loud sound can be very funny when it surprises people.",
        )
    ],
    "sharing": [
        (
            "Why is sharing important on an adventure?",
            "Sharing lets everyone use the things they need to stay involved and safe. It also helps a team feel close instead of left out.",
        )
    ],
    "laughter": [
        (
            "How can laughter help after an argument?",
            "Laughter can soften angry feelings for a moment. That small calm moment can make it easier to say sorry and start again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["map", "spyglass", "stick", "brook", "echo", "goose", "sharing", "laughter"]


def generation_prompts(world: World) -> list[str]:
    route = world.facts["route"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool_cfg"]
    comic = world.facts["comic"]
    leader_name = world.facts["leader_name"]
    partner_name = world.facts["partner_name"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "distance" and shows two children reconciling after one stops sharing {tool.label}.',
        f"Tell a gentle adventure where {leader_name} and {partner_name} meet {obstacle.label} on {route.place}, a funny {comic.id} moment breaks the tension, and they finish the journey together.",
        f"Write a child-facing story about sharing, humor, and reconciliation on a trail, where a shared tool helps friends close the distance between them.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    leader = world.facts["leader"]
    partner = world.facts["partner"]
    route = world.facts["route"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool_cfg"]
    comic = world.facts["comic"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {world.facts['leader_name']} and {world.facts['partner_name']}, two children pretending to be explorers. They wanted to reach {route.destination} together.",
        ),
        (
            "Why did a distance open between them?",
            f"A distance opened because one child kept {tool.label} instead of sharing it. That left the other child stuck at {obstacle.label}, so the space between them became both physical and emotional.",
        ),
        (
            f"Why did {world.facts['partner_name']} feel upset?",
            f"{world.facts['partner_name']} felt upset because the adventure had stopped being a team effort. Without {tool.label}, {partner.pronoun('subject')} could not get past the obstacle or help solve it.",
        ),
        (
            "What funny thing changed the mood?",
            f"The funny moment was the {comic.id}. Both children laughed, and that made the argument feel smaller for a moment, which helped them listen to each other again.",
        ),
        (
            "How did they reconcile?",
            f"They reconciled when the child in front looked back, admitted the mistake, and shared {tool.label}. After that, they used it together and the distance between them closed.",
        ),
        (
            "How did the story end?",
            f"They reached {route.destination} side by side and shared the last honey biscuit. The ending shows that the adventure felt right again because they were close and cooperative.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing", "laughter"} | set(world.facts["obstacle"].tags) | set(world.facts["tool_cfg"].tags)
    if world.facts["comic"].id in ("echo", "goose"):
        tags |= set(world.facts["comic"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="pinewoods",
        obstacle="fork",
        tool="map",
        comic="echo",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
    ),
    StoryParams(
        route="meadow",
        obstacle="brook",
        tool="walking_stick",
        comic="goose",
        leader_name="Max",
        leader_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
    ),
    StoryParams(
        route="redcliffs",
        obstacle="tall_grass",
        tool="spyglass",
        comic="echo",
        leader_name="Ava",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
    ),
    StoryParams(
        route="pinewoods",
        obstacle="brook",
        tool="walking_stick",
        comic="squeak",
        leader_name="Sam",
        leader_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
    ),
]


def explain_rejection(route_id: str, obstacle_id: str, tool_id: str, comic_id: str) -> str:
    route = ROUTES[route_id]
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    comic = COMICS[comic_id]
    if obstacle.id not in route.afford_obstacles:
        return (
            f"(No story: {route.place} does not include {obstacle.label} in this world, so the adventure has no grounded middle problem there.)"
        )
    if obstacle.id not in tool.helps:
        return (
            f"(No story: {tool.label} does not actually solve {obstacle.label}. Pick a tool that honestly helps, like "
            f"{', '.join(sorted(t.label for t in TOOLS.values() if obstacle.id in t.helps))}.)"
        )
    if comic.id not in route.allow_comics:
        return (
            f"(No story: the {comic.id} beat does not fit {route.place} in this world's registry.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
usable_tool(Tool, Obstacle) :- helps(Tool, Obstacle).
valid_story(Route, Obstacle, Tool, Comic) :-
    route(Route), obstacle(Obstacle), tool(Tool), comic(Comic),
    affords(Route, Obstacle),
    usable_tool(Tool, Obstacle),
    allows(Route, Comic).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        for obstacle_id in sorted(route.afford_obstacles):
            lines.append(asp.fact("affords", route_id, obstacle_id))
        for comic_id in sorted(route.allow_comics):
            lines.append(asp.fact("allows", route_id, comic_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.helps):
            lines.append(asp.fact("helps", tool_id, obstacle_id))
    for comic_id in COMICS:
        lines.append(asp.fact("comic", comic_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        params.seed = 123
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE resolve failed: {err}")
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            emit(sample, trace=False, qa=False)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE generation failed on case {idx}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny adventure storyworld about distance, reconciliation, sharing, and humor."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--comic", choices=COMICS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible route/obstacle/tool/comic combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.obstacle and args.tool and args.comic:
        if not valid_combo(args.route, args.obstacle, args.tool, args.comic):
            raise StoryError(explain_rejection(args.route, args.obstacle, args.tool, args.comic))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.comic is None or combo[3] == args.comic)
    ]
    if not combos:
        if args.route and args.obstacle and args.tool and args.comic:
            raise StoryError(explain_rejection(args.route, args.obstacle, args.tool, args.comic))
        raise StoryError("(No valid combination matches the given options.)")

    route_id, obstacle_id, tool_id, comic_id = rng.choice(sorted(combos))
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader_name = pick_name(rng, leader_gender)
    partner_name = pick_name(rng, partner_gender, avoid=leader_name)
    return StoryParams(
        route=route_id,
        obstacle=obstacle_id,
        tool=tool_id,
        comic=comic_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Invalid route: {params.route})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.comic not in COMICS:
        raise StoryError(f"(Invalid comic beat: {params.comic})")
    if not valid_combo(params.route, params.obstacle, params.tool, params.comic):
        raise StoryError(explain_rejection(params.route, params.obstacle, params.tool, params.comic))

    world = tell(
        ROUTES[params.route],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        COMICS[params.comic],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
    )
    return StorySample(
        params=params,
        story=world.render().replace("leader", params.leader_name).replace("partner", params.partner_name),
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, obstacle, tool, comic) combos:\n")
        for route_id, obstacle_id, tool_id, comic_id in combos:
            print(f"  {route_id:10} {obstacle_id:11} {tool_id:14} {comic_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.partner_name}: {p.route}, {p.obstacle}, {p.tool}, {p.comic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
