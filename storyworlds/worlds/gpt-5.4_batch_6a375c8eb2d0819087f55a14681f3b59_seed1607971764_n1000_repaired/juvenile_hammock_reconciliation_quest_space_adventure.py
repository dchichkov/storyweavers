#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py
====================================================================================

A standalone story world for a tiny space-adventure tale: two young explorers on
a small starship or moon camp have a quarrel over a hammock-nest, then must go
on a short quest together to fix a problem, reconcile, and come home changed.

The world model drives:
- a playful beginning in a child-facing science-fantasy setting
- a concrete disagreement about sharing a hammock
- a quest with an obstacle that requires cooperation
- either a reconciled happy ending or, in explicitly weaker variants, a lonely
  partial ending when the children refuse to work together

Run it
------
    python storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py
    python storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py --place moonbase --mission beacon --helper rover
    python storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py --obstacle storm --tool feather
    python storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py --all --qa
    python storyworlds/worlds/gpt-5.4/juvenile_hammock_reconciliation_quest_space_adventure.py --verify
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
HELP_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    supports_rest: bool = False
    helpful: int = 0
    # physical + emotional
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    home: str
    sky: str
    ground: str
    quest_site: str
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
class Mission:
    id: str
    need: str
    item_label: str
    item_phrase: str
    ending_use: str
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
    risk_text: str
    blocks: str
    severity: int
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
    solves: set[str] = field(default_factory=set)
    helpful: int = 0
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
    helpful: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "navigator"}]

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


def _r_quarrel(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("kid_a")
    b = world.get("kid_b")
    if a.memes["snit"] >= THRESHOLD and b.memes["snit"] >= THRESHOLD:
        sig = ("quarrel",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["distance"] += 1
            b.memes["distance"] += 1
            out.append("__quarrel__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("kid_a")
    b = world.get("kid_b")
    if a.memes["apology"] >= THRESHOLD and b.memes["apology"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["trust"] += 1
            b.memes["trust"] += 1
            a.memes["distance"] = 0.0
            b.memes["distance"] = 0.0
            world.facts["team_ready"] = True
            out.append("__team__")
    return out


def _r_complete(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("quest_progress", 0) >= world.facts.get("quest_need", 99):
        sig = ("complete",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["completed"] = True
            for kid in world.kids():
                kid.memes["hope"] += 1
                kid.memes["joy"] += 1
            out.append("__complete__")
    return out


CAUSAL_RULES = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="complete", tag="physical", apply=_r_complete),
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


PLACES = {
    "starship": Place(
        id="starship",
        label="the little starship Sunskip",
        home="the round sleep cabin",
        sky="a velvet window full of stars",
        ground="the silver floor",
        quest_site="the blinking service bay",
        tags={"space", "ship"},
    ),
    "moonbase": Place(
        id="moonbase",
        label="the Moonberry Base",
        home="the warm dome room",
        sky="a black sky sprinkled with cold stars",
        ground="the dusty moon tiles",
        quest_site="the cracked beacon hill",
        tags={"space", "moon"},
    ),
    "orbital_garden": Place(
        id="orbital_garden",
        label="the Ring Garden station",
        home="the leaf-green rest pod",
        sky="glass walls with drifting planets beyond",
        ground="the soft moss path",
        quest_site="the dark water pump nook",
        tags={"space", "garden"},
    ),
}

MISSIONS = {
    "beacon": Mission(
        id="beacon",
        need="re-light the path beacon",
        item_label="glow crystal",
        item_phrase="a glow crystal",
        ending_use="set the beacon shining again",
        tags={"beacon", "light"},
    ),
    "map": Mission(
        id="map",
        need="wake the sleepy star map",
        item_label="singing key",
        item_phrase="a singing key",
        ending_use="wake the star map so the constellations glimmered back on",
        tags={"map", "navigation"},
    ),
    "garden": Mission(
        id="garden",
        need="start the air-garden fan",
        item_label="wind seed",
        item_phrase="a wind seed",
        ending_use="start the fan so the tiny garden leaves danced again",
        tags={"garden", "air"},
    ),
}

OBSTACLES = {
    "storm": Obstacle(
        id="storm",
        label="a fizzing meteor dust storm",
        risk_text="tiny sparks pattered on the rails and made the path hard to see",
        blocks="the dusty sparks kept swirling across the route",
        severity=2,
        tags={"storm", "space"},
    ),
    "gap": Obstacle(
        id="gap",
        label="a narrow moon-rift",
        risk_text="the path broke at a crack too wide for one nervous jump",
        blocks="the rift split the route in two",
        severity=2,
        tags={"gap", "space"},
    ),
    "dark": Obstacle(
        id="dark",
        label="a pocket of space-dark",
        risk_text="the corridor ahead was so dim that shapes melted into shadow",
        blocks="the dark hid the right hatch and every turn looked the same",
        severity=1,
        tags={"dark", "light"},
    ),
}

TOOLS = {
    "magnet_rope": Tool(
        id="magnet_rope",
        label="magnet rope",
        phrase="a coil of magnet rope",
        solves={"gap", "storm"},
        helpful=2,
        tags={"rope", "tool"},
    ),
    "star_lantern": Tool(
        id="star_lantern",
        label="star lantern",
        phrase="a star lantern",
        solves={"dark"},
        helpful=2,
        tags={"light", "tool"},
    ),
    "bubble_umbrella": Tool(
        id="bubble_umbrella",
        label="bubble umbrella",
        phrase="a bubble umbrella",
        solves={"storm"},
        helpful=2,
        tags={"umbrella", "tool"},
    ),
    "feather": Tool(
        id="feather",
        label="feather",
        phrase="a single decorative feather",
        solves=set(),
        helpful=0,
        tags={"feather"},
    ),
}

HELPERS = {
    "rover": Helper(
        id="rover",
        label="rover",
        phrase="their little rover Pip",
        helpful=1,
        action="beeped and pointed its nose-light toward the safe path",
        tags={"robot", "helper"},
    ),
    "drone": Helper(
        id="drone",
        label="drone",
        phrase="a buzzing helper drone",
        helpful=1,
        action="hovered ahead with a tiny lamp and a cheerful hum",
        tags={"robot", "helper"},
    ),
    "glow_moth": Helper(
        id="glow_moth",
        label="glow moth",
        phrase="a glow moth from the garden ring",
        helpful=1,
        action="fluttered in front of them like a living star",
        tags={"moth", "helper", "light"},
    ),
}

GIRL_NAMES = ["Nova", "Lina", "Mira", "Tara", "Aya", "Zoe", "Nia", "Iris"]
BOY_NAMES = ["Orion", "Leo", "Milo", "Finn", "Tao", "Ben", "Eli", "Kai"]
TRAITS = ["bold", "curious", "careful", "cheerful", "steady", "gentle"]


def mission_possible(obstacle: Obstacle, tool: Tool, helper: Helper) -> bool:
    return tool.id in TOOLS and helper.id in HELPERS and (tool.helpful + helper.helpful) >= obstacle.severity and obstacle.id in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for mission in MISSIONS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for tool_id, tool in TOOLS.items():
                    for helper_id, helper in HELPERS.items():
                        if mission_possible(obstacle, tool, helper):
                            combos.append((place, mission, obstacle_id, tool_id, helper_id))
    # reduce to one combo per tool/helper by including all 5-tuple in filters later
    return sorted(set((p, m, o, t) for p, m, o, t, _h in combos))


def valid_full_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place in PLACES:
        for mission in MISSIONS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for tool_id, tool in TOOLS.items():
                    for helper_id, helper in HELPERS.items():
                        if mission_possible(obstacle, tool, helper):
                            combos.append((place, mission, obstacle_id, tool_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    mission: str
    obstacle: str
    tool: str
    helper: str
    captain: str
    captain_gender: str
    navigator: str
    navigator_gender: str
    mentor: str
    trait_a: str
    trait_b: str
    hammock_style: str = "net"
    reconcile: bool = True
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


def predict_success(world: World, obstacle: Obstacle, tool: Tool, helper: Helper, reconcile: bool) -> dict:
    sim = world.copy()
    sim.facts["quest_progress"] = 0
    sim.facts["quest_need"] = obstacle.severity
    if reconcile:
        sim.get("kid_a").memes["apology"] += 1
        sim.get("kid_b").memes["apology"] += 1
        propagate(sim, narrate=False)
        sim.facts["quest_progress"] += tool.helpful + helper.helpful
    else:
        sim.facts["quest_progress"] += max(tool.helpful - 1, 0)
    propagate(sim, narrate=False)
    return {
        "team_ready": bool(sim.facts.get("team_ready")),
        "completed": bool(sim.facts.get("completed")),
        "progress": sim.facts.get("quest_progress", 0),
    }


def introduce(world: World, place: Place, a: Entity, b: Entity, hammock_text: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On {place.label}, {place.sky} shone over {place.home}. "
        f"There, {a.id} and {b.id}, two juvenile space explorers, had made a snug {hammock_text} between two bunks."
    )
    world.say(
        f"They liked to pretend the hammock was a tiny shuttle drifting above a thousand secret worlds."
    )


def quarrel(world: World, a: Entity, b: Entity, hammock_text: str) -> None:
    a.memes["snit"] += 1
    b.memes["snit"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That morning they both wanted the middle of the {hammock_text} at once. "
        f"{a.id} pulled one side, {b.id} pulled the other, and the soft nest swung crooked."
    )
    world.say(
        f'"I found it first," said {a.id}. '
        f'"But I fixed the blanket stars," said {b.id}.'
    )
    world.say(
        "Soon neither of them felt like laughing anymore."
    )


def mentor_need(world: World, mentor: Entity, place: Place, mission: Mission) -> None:
    world.say(
        f"Just then {mentor.label.capitalize()} came hurrying in from {place.quest_site}. "
        f'"Explorers," {mentor.pronoun()} said, "we need to {mission.need}, and the kit is missing {mission.item_phrase}."'
    )


def choose_quest(world: World, a: Entity, b: Entity, place: Place, mission: Mission, obstacle: Obstacle) -> None:
    world.say(
        f"The missing piece lay somewhere past {obstacle.label}. "
        f"If they could cross {place.ground} and search the lockers near {place.quest_site}, they could bring it back."
    )
    world.say(
        f"But the way was not easy: {obstacle.risk_text}."
    )


def refusal_or_apology(world: World, a: Entity, b: Entity, reconcile: bool) -> None:
    if reconcile:
        a.memes["apology"] += 1
        b.memes["apology"] += 1
        a.memes["kindness"] += 1
        b.memes["kindness"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{a.id} looked at the drooping hammock and then at {b.id}. "
            f'"I was tugging too hard," {a.pronoun()} said.'
        )
        world.say(
            f'"I was too," said {b.id}. "Let\'s be a team again."'
        )
    else:
        world.say(
            f"{a.id} folded {a.pronoun('possessive')} arms, and {b.id} turned away. "
            f"They marched out together because the ship needed help, but the hurt feeling stayed between them."
        )


def gather_gear(world: World, tool: Tool, helper: Helper) -> None:
    world.say(
        f"They packed {tool.phrase}, and {helper.phrase} came too."
    )


def solve_obstacle(world: World, a: Entity, b: Entity, obstacle: Obstacle, tool: Tool, helper: Helper, reconcile: bool) -> None:
    if reconcile:
        world.facts["quest_progress"] += tool.helpful + helper.helpful
        a.meters["steps"] += 1
        b.meters["steps"] += 1
        a.memes["courage"] += 1
        b.memes["courage"] += 1
        world.say(
            f"When they reached {obstacle.label}, {tool.label} finally mattered. "
            f"{a.id} held one end while {b.id} steadied the other."
        )
        world.say(
            f"{helper.phrase.capitalize()} {helper.action}."
        )
        world.say(
            "Because they were listening to each other again, the hard part stopped feeling impossible."
        )
    else:
        world.facts["quest_progress"] += max(tool.helpful - 1, 0)
        a.meters["steps"] += 1
        b.meters["steps"] += 1
        world.say(
            f"They tried to face {obstacle.label}, but they kept reaching at the wrong time and talking over one another."
        )
        world.say(
            f"Even with {tool.phrase}, {obstacle.blocks}, and nobody trusted the next move."
        )
    propagate(world, narrate=False)


def find_item(world: World, mission: Mission, place: Place) -> None:
    if world.facts.get("completed"):
        world.say(
            f"At the lockers by {place.quest_site}, they found {mission.item_phrase} tucked behind a toolbox."
        )


def ending_happy(world: World, a: Entity, b: Entity, mentor: Entity, mission: Mission, hammock_text: str) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"Back home, {mentor.label} used it to {mission.ending_use}. "
        f"Soft light spread over the room, and everything felt brave and bright again."
    )
    world.say(
        f"Then {a.id} and {b.id} went back to their {hammock_text}. "
        f"This time they scooted close, counted planets together, and let the hammock swing nice and even."
    )


def ending_partial(world: World, a: Entity, b: Entity, mentor: Entity, mission: Mission, hammock_text: str) -> None:
    a.memes["regret"] += 1
    b.memes["regret"] += 1
    world.say(
        f"They had to turn back without {mission.item_label}. "
        f"{mentor.label.capitalize()} was gentle, but {mentor.pronoun()} could see they had not worked as one crew."
    )
    world.say(
        f"Later the {hammock_text} hung quiet between the bunks. "
        f"{a.id} and {b.id} both missed the easy swinging they had before the quarrel."
    )
    world.say(
        "That was when they understood that a quest goes farther when hearts pull in the same direction."
    )


def tell(
    place: Place,
    mission: Mission,
    obstacle: Obstacle,
    tool: Tool,
    helper: Helper,
    captain: str,
    captain_gender: str,
    navigator: str,
    navigator_gender: str,
    mentor_type: str,
    trait_a: str,
    trait_b: str,
    hammock_style: str,
    reconcile: bool,
) -> World:
    world = World()
    world.facts["quest_progress"] = 0
    world.facts["quest_need"] = obstacle.severity
    world.facts["team_ready"] = False
    world.facts["completed"] = False

    hammock_word = "hammock" if hammock_style == "net" else f"{hammock_style} hammock"

    a = world.add(Entity(
        id="kid_a",
        kind="character",
        type=captain_gender,
        label=captain,
        traits=[trait_a],
        role="captain",
    ))
    b = world.add(Entity(
        id="kid_b",
        kind="character",
        type=navigator_gender,
        label=navigator,
        traits=[trait_b],
        role="navigator",
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type=mentor_type,
        label={"mother": "mom", "father": "dad"}.get(mentor_type, "mentor"),
        role="mentor",
    ))
    world.add(Entity(
        id="rest",
        type="hammock",
        label=hammock_word,
        supports_rest=True,
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        portable=True,
        helpful=tool.helpful,
    ))
    world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        helpful=helper.helpful,
    ))

    introduce(world, place, a, b, hammock_word)
    world.para()
    quarrel(world, a, b, hammock_word)
    mentor_need(world, mentor, place, mission)
    choose_quest(world, a, b, place, mission, obstacle)
    world.para()
    refusal_or_apology(world, a, b, reconcile)
    gather_gear(world, tool, helper)
    solve_obstacle(world, a, b, obstacle, tool, helper, reconcile)
    find_item(world, mission, place)
    world.para()
    if world.facts.get("completed"):
        ending_happy(world, a, b, mentor, mission, hammock_word)
        outcome = "reconciled"
    else:
        ending_partial(world, a, b, mentor, mission, hammock_word)
        outcome = "strained"

    world.facts.update(
        place=place,
        mission=mission,
        obstacle=obstacle,
        tool_cfg=tool,
        helper_cfg=helper,
        captain=a,
        navigator=b,
        mentor=mentor,
        reconcile=reconcile,
        outcome=outcome,
        hammock_word=hammock_word,
        item_found=world.facts.get("completed", False),
    )
    return world


KNOWLEDGE = {
    "space": [(
        "What is a space beacon?",
        "A space beacon is a bright signal light that helps travelers know where to go. It is useful because it can guide people through dark places."
    )],
    "ship": [(
        "What is a starship?",
        "A starship is a make-believe or story spaceship that travels among the stars. In stories, children often use it as a place for adventures."
    )],
    "moon": [(
        "What is the Moon like?",
        "The Moon is rocky and dusty, and there is no air there like on Earth. That is why moon stories often use domes, suits, and careful paths."
    )],
    "beacon": [(
        "Why is a beacon helpful?",
        "A beacon is helpful because it gives light or a signal that shows the safe way. When a path is dark, a beacon can keep explorers from getting lost."
    )],
    "map": [(
        "What does a map do?",
        "A map helps you know where things are and which way to go. A good map turns a confusing trip into a clear plan."
    )],
    "garden": [(
        "Why would a space garden need air?",
        "Plants need air and moving water to stay healthy. In a space story, a fan can help the little garden keep growing."
    )],
    "storm": [(
        "What is a storm?",
        "A storm is rough, windy, or dangerous weather. In a space adventure, a storm can also mean swirling dust or flying sparkly bits that make travel harder."
    )],
    "gap": [(
        "Why is a gap hard to cross?",
        "A gap is hard to cross because there is open space between two safe spots. Explorers need a careful way across so nobody slips or gets scared."
    )],
    "dark": [(
        "Why is darkness hard on a quest?",
        "Darkness makes it hard to see the path, clues, and safe places to step. A light helps because it turns confusion into something you can understand."
    )],
    "rope": [(
        "What can a rope do on an adventure?",
        "A rope can help explorers pull, climb, or make a safe line across a hard place. It works best when people hold and use it together."
    )],
    "light": [(
        "What does a lantern do?",
        "A lantern makes light so people can see in the dark. Good light helps explorers notice the safe path and the things they are looking for."
    )],
    "robot": [(
        "How can a little robot helper help?",
        "A little robot helper can point the way, carry tools, or shine a light. Even a small helper can make a hard job feel easier."
    )],
    "helper": [(
        "Why is teamwork good on a quest?",
        "Teamwork is good because one explorer can do what another cannot do alone. When people listen and help each other, a quest becomes safer and kinder."
    )],
}
KNOWLEDGE_ORDER = ["space", "ship", "moon", "beacon", "map", "garden", "storm", "gap", "dark", "rope", "light", "robot", "helper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    mission = f["mission"]
    obstacle = f["obstacle"]
    outcome = f["outcome"]
    if outcome == "reconciled":
        return [
            f'Write a gentle space adventure for a 3-to-5-year-old that includes the words "juvenile" and "hammock".',
            f"Tell a story where two juvenile explorers quarrel in a hammock, then go on a quest to {mission.need} past {obstacle.label} and make up along the way.",
            f"Write a reconciliation quest on {place.label} where a small problem between friends is healed by working together."
        ]
    return [
        f'Write a soft cautionary space adventure that includes the words "juvenile" and "hammock".',
        f"Tell a story where two juvenile explorers argue before a quest to {mission.need}, and the trouble grows because they do not cooperate well.",
        f"Write a child-facing tale showing that even in space, a team must reconcile to finish a quest."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["captain"]
    b = f["navigator"]
    mentor = f["mentor"]
    mission = f["mission"]
    obstacle = f["obstacle"]
    tool = f["tool_cfg"]
    helper = f["helper_cfg"]
    place = f["place"]
    hammock_word = f["hammock_word"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two juvenile space explorers, {a.label} and {b.label}, on {place.label}. They begin in a {hammock_word} and then have to help {mentor.label} on a quest."
        ),
        (
            f"Why did {a.label} and {b.label} start to argue?",
            f"They both wanted the middle of the {hammock_word} at the same time, and each thought the cozy spot should be theirs. The tugging turned a playful resting place into the start of a quarrel."
        ),
        (
            "What was the quest?",
            f"The quest was to {mission.need} by finding {mission.item_phrase}. They had to go past {obstacle.label} to reach the place where the missing piece was hidden."
        ),
    ]
    if f["outcome"] == "reconciled":
        qa.extend([
            (
                "How did they reconcile?",
                f"They each admitted being unfair and chose to be a team again. That apology mattered because once they listened to each other, they could use the {tool.label} and follow help from {helper.label} the right way."
            ),
            (
                f"How did they get past {obstacle.label}?",
                f"They got past it by using the {tool.label} while {helper.phrase} helped them. Working together turned the obstacle from something scary into something they could solve step by step."
            ),
            (
                "How did the story end?",
                f"It ended with the mission fixed and the room bright again. Back at the {hammock_word}, they sat close together and let it swing evenly, which showed their friendship had healed."
            ),
        ])
    else:
        qa.extend([
            (
                "Why did the quest go badly?",
                f"It went badly because they kept the hurt feeling between them instead of making up. Even though they carried the {tool.label}, they were not listening well enough to use it as one team."
            ),
            (
                "What did they learn at the end?",
                f"They learned that a quest is harder when people pull against each other. The quiet {hammock_word} at the end reminded them of the friendship they needed to mend."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["mission"].tags) | set(f["obstacle"].tags) | set(f["tool_cfg"].tags) | set(f["helper_cfg"].tags)
    tags.add("helper")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.helpful:
            bits.append(f"helpful={ent.helpful}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} completed={world.facts.get('completed')} progress={world.facts.get('quest_progress')}/{world.facts.get('quest_need')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="starship",
        mission="beacon",
        obstacle="dark",
        tool="star_lantern",
        helper="rover",
        captain="Nova",
        captain_gender="girl",
        navigator="Leo",
        navigator_gender="boy",
        mentor="mother",
        trait_a="bold",
        trait_b="gentle",
        hammock_style="net",
        reconcile=True,
    ),
    StoryParams(
        place="moonbase",
        mission="map",
        obstacle="gap",
        tool="magnet_rope",
        helper="drone",
        captain="Mira",
        captain_gender="girl",
        navigator="Kai",
        navigator_gender="boy",
        mentor="father",
        trait_a="careful",
        trait_b="curious",
        hammock_style="woven",
        reconcile=True,
    ),
    StoryParams(
        place="orbital_garden",
        mission="garden",
        obstacle="storm",
        tool="bubble_umbrella",
        helper="glow_moth",
        captain="Iris",
        captain_gender="girl",
        navigator="Milo",
        navigator_gender="boy",
        mentor="mother",
        trait_a="cheerful",
        trait_b="steady",
        hammock_style="leafy",
        reconcile=True,
    ),
    StoryParams(
        place="starship",
        mission="beacon",
        obstacle="storm",
        tool="bubble_umbrella",
        helper="rover",
        captain="Aya",
        captain_gender="girl",
        navigator="Finn",
        navigator_gender="boy",
        mentor="father",
        trait_a="bold",
        trait_b="curious",
        hammock_style="net",
        reconcile=False,
    ),
]


def explain_combo(obstacle: Obstacle, tool: Tool, helper: Helper) -> str:
    if obstacle.id not in tool.solves:
        return (
            f"(No story: {tool.phrase} does not solve {obstacle.label}. "
            f"Choose a tool that can really help with that obstacle.)"
        )
    if (tool.helpful + helper.helpful) < obstacle.severity:
        return (
            f"(No story: {tool.phrase} and {helper.phrase} together are too weak for {obstacle.label}. "
            f"The quest needs enough real help to feel reasonable.)"
        )
    if tool.helpful < HELP_MIN and helper.helpful < 1:
        return (
            "(No story: the chosen aid is too weak for this adventure.)"
        )
    return "(No story: this combination is not a reasonable quest setup.)"


ASP_RULES = r"""
can_solve(O,T) :- obstacle(O), tool(T), solves(T,O).
strong_enough(O,T,H) :- obstacle(O), tool(T), helper(H),
                        severity(O,S), helpful_tool(T,TT), helpful_helper(H,HH),
                        TT + HH >= S.
valid(P,M,O,T,H) :- place(P), mission(M), obstacle(O), tool(T), helper(H),
                    can_solve(O,T), strong_enough(O,T,H).

quest_progress(T + H) :- chosen_tool(TT), helpful_tool(TT,T), chosen_helper(HH), helpful_helper(HH,H), reconcile.
quest_progress(TT1)   :- chosen_tool(TT), helpful_tool(TT,Raw), TT1 = Raw - 1, not reconcile, Raw > 0.
quest_progress(0)     :- chosen_tool(TT), helpful_tool(TT,0), not reconcile.
completed             :- chosen_obstacle(O), severity(O,S), quest_progress(P), P >= S.
outcome(reconciled)   :- reconcile, completed.
outcome(strained)     :- not reconcile.
outcome(strained)     :- reconcile, not completed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("severity", oid, obstacle.severity))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helpful_tool", tid, tool.helpful))
        for oid in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, oid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helpful_helper", hid, helper.helpful))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_full_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if params.reconcile and (tool.helpful + helper.helpful) >= obstacle.severity and params.obstacle in tool.solves:
        return "reconciled"
    return "strained"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_helper", params.helper),
        "reconcile." if params.reconcile else "",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_full_combos())
    python_set = set(valid_full_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_full_combos() ({len(clingo_set)} combos).")
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
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a hammock quarrel, a space quest, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--reconcile", choices=["yes", "no"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        helper = HELPERS[args.helper]
        if not mission_possible(obstacle, tool, helper):
            raise StoryError(explain_combo(obstacle, tool, helper))
    if args.tool and args.obstacle and not args.helper:
        compatible = [
            hid for hid, helper in HELPERS.items()
            if mission_possible(OBSTACLES[args.obstacle], TOOLS[args.tool], helper)
        ]
        if not compatible:
            raise StoryError(explain_combo(OBSTACLES[args.obstacle], TOOLS[args.tool], next(iter(HELPERS.values()))))

    combos = [
        c for c in valid_full_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.tool is None or c[3] == args.tool)
        and (args.helper is None or c[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission, obstacle, tool, helper = rng.choice(combos)
    captain, captain_gender = _pick_kid(rng)
    navigator, navigator_gender = _pick_kid(rng, avoid=captain)
    mentor = args.mentor or rng.choice(["mother", "father"])
    reconcile = {"yes": True, "no": False}.get(args.reconcile, rng.choice([True, True, True, False]))
    return StoryParams(
        place=place,
        mission=mission,
        obstacle=obstacle,
        tool=tool,
        helper=helper,
        captain=captain,
        captain_gender=captain_gender,
        navigator=navigator,
        navigator_gender=navigator_gender,
        mentor=mentor,
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        hammock_style=rng.choice(["net", "woven", "leafy"]),
        reconcile=reconcile,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        mission = MISSIONS[params.mission]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not mission_possible(obstacle, tool, helper):
        raise StoryError(explain_combo(obstacle, tool, helper))

    world = tell(
        place=place,
        mission=mission,
        obstacle=obstacle,
        tool=tool,
        helper=helper,
        captain=params.captain,
        captain_gender=params.captain_gender,
        navigator=params.navigator,
        navigator_gender=params.navigator_gender,
        mentor_type=params.mentor,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
        hammock_style=params.hammock_style,
        reconcile=params.reconcile,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_full_combos()
        print(f"{len(combos)} compatible (place, mission, obstacle, tool, helper) combos:\n")
        for place, mission, obstacle, tool, helper in combos:
            print(f"  {place:14} {mission:8} {obstacle:7} {tool:15} {helper}")
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
            header = f"### {p.captain} & {p.navigator}: {p.mission} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
