#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py
===========================================================================

A standalone story world for a tiny "space adventure" domain built around
sharing, scarcity, and a sometimes-sad ending.

Premise
-------
A small crew turns a play space into a rocket mission. They discover a limited
set of glowing supplies. There are **four** of them. One child -- often a child
named **Blu** -- must decide whether to share. If the supplies can be split or
passed around fairly, the mission ends warmly. If the captain hoards them, the
adventure falls apart and the ending turns lonely and sad.

This world models:
- typed entities with physical meters and emotional memes
- a clear beginning, turn, and ending
- a Python reasonableness gate plus an inline ASP twin
- three QA sets generated from world state, not from parsing prose

Run it
------
python storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py
python storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py --seed 7 --qa
python storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py --trace
python storyworlds/worlds/gpt-5.4/blu_four_sharing_bad_ending_space_adventure.py --verify
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
CREW_SIZE = 3


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
class Mission:
    id: str
    room: str
    rig: str
    destination: str
    danger: str
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
class Supply:
    id: str
    label: str
    plural_label: str
    glow: str
    use_text: str
    indivisible: bool
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
class Method:
    id: str
    label: str
    can_divide: bool
    kind_text: str
    success_text: str
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
class Choice:
    id: str
    sharing: bool
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

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "crew", "robot"}]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"captain", "crew"}]

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


def _r_left_out(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("hoarded"):
        return out
    if ("left_out",) in world.fired:
        return out
    world.fired.add(("left_out",))
    for ent in world.crew():
        if ent.role != "captain":
            ent.memes["left_out"] += 1
            ent.memes["sad"] += 1
    world.get("ship").meters["mission_trouble"] += 1
    out.append("__left_out__")
    return out


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared_fairly"):
        return out
    if ("shared_joy",) in world.fired:
        return out
    world.fired.add(("shared_joy",))
    for ent in world.crew():
        ent.memes["included"] += 1
        ent.memes["joy"] += 1
    world.get("ship").meters["mission_trouble"] = 0.0
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="left_out", tag="social", apply=_r_left_out),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
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


def can_share_evenly(supply: Supply, method: Method, count: int = 4, crew_size: int = CREW_SIZE) -> bool:
    if count < crew_size:
        return False
    if count % crew_size == 0:
        return True
    return method.can_divide and not supply.indivisible


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for supply_id, supply in SUPPLIES.items():
        for method_id, method in METHODS.items():
            if can_share_evenly(supply, method):
                combos.append((supply_id, method_id))
    return combos


def predict_outcome(supply: Supply, method: Method, choice: Choice) -> str:
    if choice.sharing and can_share_evenly(supply, method):
        return "shared"
    return "bad"


def explain_rejection(supply: Supply, method: Method) -> str:
    if supply.indivisible and method.can_divide:
        return (
            f"(No story: {supply.plural_label.capitalize()} cannot be cut into fair parts, "
            f"so {method.label} cannot honestly solve the sharing problem.)"
        )
    return (
        f"(No story: four {supply.plural_label} will not divide fairly among three crew "
        f"with {method.label}. Pick a supply that can be shared whole or a method that can divide it.)"
    )


def introduce(world: World, captain: Entity, crew_mate: Entity, robot: Entity, mission: Mission) -> None:
    for ent in world.crew():
        ent.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {captain.id}, {crew_mate.id}, and {robot.id} turned the room into {mission.room}. "
        f"{mission.rig}"
    )
    world.say(
        f'"Crew of three!" {captain.id} shouted. "Today we fly to {mission.destination}."'
    )


def discover_supplies(world: World, captain: Entity, supply: Supply) -> None:
    captain.meters["found"] += 1
    world.facts["count"] = 4
    world.say(
        f"Near the pretend control panel, {captain.id} found a small silver box. Inside were four {supply.plural_label} "
        f"that {supply.glow}."
    )
    world.say(
        f'"These can help us {supply.use_text}," {captain.id} said.'
    )


def need_fairness(world: World, crew_mate: Entity, robot: Entity, method: Method) -> None:
    world.say(
        f'{crew_mate.id} looked at the box, then at {robot.id}. "There are three of us," {crew_mate.pronoun()} said. '
        f'"We should use {method.kind_text} so everyone gets a turn."'
    )


def tempt(world: World, captain: Entity) -> None:
    captain.memes["greed"] += 1
    world.say(
        f"But the four glowing things looked so special in {captain.id}'s hands that, for one breath, keeping all of them felt tempting."
    )


def share_fairly(world: World, captain: Entity, crew_mate: Entity, robot: Entity, supply: Supply, method: Method) -> None:
    captain.memes["kindness"] += 1
    captain.memes["greed"] = 0.0
    world.facts["shared_fairly"] = True
    world.facts["hoarded"] = False
    captain.attrs["share_plan"] = method.label
    captain.meters["shares_given"] = 2
    crew_mate.meters["received"] = 1
    robot.meters["received"] = 1
    if method.can_divide and not supply.indivisible:
        world.say(
            f'{captain.id} nodded. "{method.success_text}," {captain.pronoun()} said. '
            f"Soon each crew member had a fair bright piece."
        )
    else:
        world.say(
            f'{captain.id} smiled and passed the {supply.plural_label} around one by one. '
            f'"We can take turns," {captain.pronoun()} said.'
        )
    propagate(world, narrate=False)


def hoard(world: World, captain: Entity, crew_mate: Entity, robot: Entity, supply: Supply) -> None:
    captain.memes["greed"] += 1
    captain.memes["defiance"] += 1
    world.facts["shared_fairly"] = False
    world.facts["hoarded"] = True
    captain.meters["kept"] = 4
    crew_mate.meters["received"] = 0
    robot.meters["received"] = 0
    world.say(
        f'"No," said {captain.id}, curling {captain.pronoun("possessive")} fingers around all four {supply.plural_label}. '
        f'"I found them, so I get them."'
    )
    propagate(world, narrate=False)


def mission_good(world: World, captain: Entity, crew_mate: Entity, robot: Entity, mission: Mission, supply: Supply) -> None:
    world.say(
        f"With everyone included, the pretend rocket hummed along toward {mission.destination}. "
        f"The glowing {supply.plural_label} bounced from hand to hand like tiny stars."
    )
    world.say(
        f"When they reached the pillows at the far end of the room, all three cheered. {mission.ending}"
    )


def mission_bad(world: World, captain: Entity, crew_mate: Entity, robot: Entity, mission: Mission, supply: Supply) -> None:
    crew_mate.memes["hurt"] += 1
    robot.memes["hurt"] += 1
    captain.memes["lonely"] += 1
    world.say(
        f"{crew_mate.id} stopped making rocket sounds. {robot.id}'s paper antenna drooped. "
        f"Without shared supplies, the mission to {mission.destination} no longer felt like a team adventure."
    )
    world.say(
        f"Soon the cardboard ship was quiet. The four {supply.plural_label} still glowed in {captain.id}'s lap, "
        f"but the game had gone dark. {mission.danger}"
    )


def closing_lesson(world: World, captain: Entity, crew_mate: Entity, robot: Entity, choice: Choice) -> None:
    if choice.sharing:
        world.say(
            f"At the end, {captain.id} felt bigger inside for sharing, and {crew_mate.id} and {robot.id} stayed close beside {captain.pronoun('object')}."
        )
    else:
        world.say(
            f"At the end, {captain.id} had all four treasures but no happy crew. That is the sad kind of ending that comes when nobody feels included."
        )


def tell(
    mission: Mission,
    supply: Supply,
    method: Method,
    choice: Choice,
    captain_name: str,
    captain_gender: str,
    crew_name: str,
    crew_gender: str,
    parent_type: str,
) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    crew_mate = world.add(Entity(id=crew_name, kind="character", type=crew_gender, role="crew"))
    robot = world.add(Entity(id="Roko", kind="thing", type="robot", label="the robot helper", role="robot"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the cardboard ship"))

    world.facts.update(
        mission=mission,
        supply=supply,
        method=method,
        choice=choice,
        count=4,
        shared_fairly=False,
        hoarded=False,
        captain=captain,
        crew_mate=crew_mate,
        robot=robot,
        parent=parent,
    )

    introduce(world, captain, crew_mate, robot, mission)
    discover_supplies(world, captain, supply)
    world.para()
    need_fairness(world, crew_mate, robot, method)
    tempt(world, captain)
    world.para()
    if choice.sharing:
        share_fairly(world, captain, crew_mate, robot, supply, method)
        mission_good(world, captain, crew_mate, robot, mission, supply)
    else:
        hoard(world, captain, crew_mate, robot, supply)
        mission_bad(world, captain, crew_mate, robot, mission, supply)
    closing_lesson(world, captain, crew_mate, robot, choice)
    world.facts["outcome"] = "shared" if world.facts["shared_fairly"] else "bad"
    world.facts["mission_trouble"] = ship.meters["mission_trouble"]
    return world


MISSIONS = {
    "nebula": Mission(
        id="nebula",
        room="a deep-space rocket bay",
        rig="A laundry basket became the cockpit, sofa cushions became moon rocks, and a blue blanket arched over the chairs like a night sky.",
        destination="the Soft Nebula",
        danger="Nobody cried loudly, but the quiet felt heavy and wrong.",
        ending="Their little ship landed in a nest of pillows, and the whole room felt warm and starry.",
        tags={"space", "team"},
    ),
    "rings": Mission(
        id="rings",
        room="a ring-runner starship",
        rig="A cardboard box became the control deck, tape lines became shiny space roads, and a blu scarf was tied to the side like a brave captain's flag.",
        destination="the Singing Rings",
        danger="The adventure ended early, not with a crash, but with hurt feelings and a lonely captain.",
        ending="They marched in a circle around the rug, laughing as if they really had orbited a silver world.",
        tags={"space", "sharing"},
    ),
    "comet": Mission(
        id="comet",
        room="a comet-chaser shuttle",
        rig="Dining chairs became rocket seats, a mixing bowl became a helmet, and a flashlight made stars jump across the ceiling.",
        destination="Comet Bluebell",
        danger="The game slipped away like smoke, because a crew cannot feel brave together when one friend keeps everything.",
        ending="By bedtime, the mission still sparkled in their minds because everyone had been part of it.",
        tags={"space", "adventure"},
    ),
}

SUPPLIES = {
    "moonfruit": Supply(
        id="moonfruit",
        label="moonfruit",
        plural_label="moonfruit slices",
        glow="glowed pale blue",
        use_text="keep our rocket picnic bright",
        indivisible=False,
        tags={"food", "share"},
    ),
    "star_crystals": Supply(
        id="star_crystals",
        label="star crystal",
        plural_label="star crystals",
        glow="winked like tiny lamps",
        use_text="light the dark side of the ship",
        indivisible=False,
        tags={"light", "share"},
    ),
    "rocket_badges": Supply(
        id="rocket_badges",
        label="rocket badge",
        plural_label="rocket badges",
        glow="shone with silver paint",
        use_text="show who belongs on the crew",
        indivisible=True,
        tags={"badge", "belonging"},
    ),
}

METHODS = {
    "turns": Method(
        id="turns",
        label="taking turns",
        can_divide=False,
        kind_text="taking turns",
        success_text="Let's take turns and pass them carefully",
        tags={"turns"},
    ),
    "splitter": Method(
        id="splitter",
        label="the snack splitter",
        can_divide=True,
        kind_text="the little snack splitter",
        success_text="Let's use the snack splitter and make fair little pieces",
        tags={"divide"},
    ),
    "shared_tray": Method(
        id="shared_tray",
        label="the shared tray",
        can_divide=False,
        kind_text="the shared tray in the middle",
        success_text="Let's set them in the middle so everyone can use them fairly",
        tags={"turns"},
    ),
}

CHOICES = {
    "share": Choice(id="share", sharing=True, tags={"sharing"}),
    "hoard": Choice(id="hoard", sharing=False, tags={"bad_ending"}),
}

GIRL_NAMES = ["Blu", "Mia", "Zoe", "Ava", "Luna", "Nora", "Skye"]
BOY_NAMES = ["Blu", "Max", "Leo", "Finn", "Theo", "Jax", "Owen"]


@dataclass
class StoryParams:
    mission: str
    supply: str
    method: str
    choice: str
    captain: str
    captain_gender: str
    crew_mate: str
    crew_gender: str
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
    "space": [
        (
            "What is a space adventure?",
            "A space adventure is a pretend journey to stars, moons, or planets. Children often use boxes, blankets, and lights to imagine a rocket trip."
        )
    ],
    "share": [
        (
            "What does sharing mean?",
            "Sharing means letting other people have a fair part or a fair turn. It helps everyone feel included instead of left out."
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person uses something first and then passes it to someone else. It is one way to share fairly when everyone cannot use it at once."
        )
    ],
    "divide": [
        (
            "Why do people split food into pieces?",
            "They split food into pieces to make the parts more fair. Smaller equal pieces help more people share."
        )
    ],
    "badge": [
        (
            "Why can a badge feel important in a game?",
            "A badge can make someone feel chosen or part of the team. That is why keeping all the badges can hurt other players' feelings."
        )
    ],
    "belonging": [
        (
            "Why do people feel sad when they are left out?",
            "People feel sad when they are left out because they want to belong with others. Being included helps games feel safe and happy."
        )
    ],
    "food": [
        (
            "Why is it kind to share food?",
            "Sharing food can help everyone feel cared for. It turns one person's treat into a friendly moment for the group."
        )
    ],
    "light": [
        (
            "Why do lights feel special in a pretend spaceship?",
            "Little lights make a room feel mysterious and starry. They help children imagine that they are really flying through space."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    supply = f["supply"]
    outcome = f["outcome"]
    captain = f["captain"]
    crew = f["crew_mate"]
    if outcome == "bad":
        return [
            f'Write a short space adventure story for a 3-to-5-year-old that includes the words "blu" and "four" and ends sadly because someone refuses to share.',
            f"Tell a gentle but bad-ending story where {captain.id} finds four {supply.plural_label} during a pretend mission to {mission.destination}, but keeps them all and hurts {crew.id}'s feelings.",
            f"Write a child-facing story about sharing on a cardboard spaceship, where the adventure goes wrong because one crew member wants all the special things."
        ]
    return [
        f'Write a short space adventure story for a 3-to-5-year-old that includes the words "blu" and "four" and shows how sharing saves the game.',
        f"Tell a pretend rocket story where {captain.id} finds four {supply.plural_label} on the way to {mission.destination} and chooses a fair way to share them.",
        f"Write a simple story about a small space crew learning that a fair turn or a fair piece can keep everyone on the adventure together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    crew = f["crew_mate"]
    robot = f["robot"]
    mission = f["mission"]
    supply = f["supply"]
    method = f["method"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who was in the space crew?",
            f"The crew was {captain.id}, {crew.id}, and {robot.id}. They were pretending to fly together, so the game worked best when all three felt included."
        ),
        (
            "What did they find?",
            f"They found four {supply.plural_label} in a silver box. The glowing supplies felt important because the crew wanted to use them on the mission."
        ),
        (
            "Why did sharing matter in the story?",
            f"Sharing mattered because there were three crew members and only one box of special things. The choice about those four treasures changed whether the mission felt friendly or lonely."
        ),
    ]
    if out == "shared":
        qa.extend(
            [
                (
                    f"How did {captain.id} solve the problem?",
                    f"{captain.id} chose {method.label} so the supplies could be shared fairly. That let every crew member join the mission instead of watching from the side."
                ),
                (
                    "How did the story end?",
                    f"It ended happily, with the crew reaching {mission.destination} together. The final feeling was bright because kindness kept the game alive."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Why was the ending sad?",
                    f"The ending was sad because {captain.id} kept all four {supply.plural_label} and would not share. That left {crew.id} and {robot.id} feeling pushed out, so the game quietly fell apart."
                ),
                (
                    f"Did keeping all four treasures make {captain.id} happy in the end?",
                    f"No. {captain.id} still had the treasures, but the crew was no longer having fun together. The story shows that having everything is not the same as feeling close to other people."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"space"}
    f = world.facts
    tags |= set(f["supply"].tags)
    tags |= set(f["method"].tags)
    tags |= set(f["choice"].tags)
    order = ["space", "share", "turns", "divide", "food", "light", "badge", "belonging"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} count={world.facts.get('count')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="rings",
        supply="star_crystals",
        method="shared_tray",
        choice="share",
        captain="Blu",
        captain_gender="girl",
        crew_mate="Max",
        crew_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="nebula",
        supply="moonfruit",
        method="splitter",
        choice="share",
        captain="Blu",
        captain_gender="boy",
        crew_mate="Luna",
        crew_gender="girl",
        parent="father",
    ),
    StoryParams(
        mission="comet",
        supply="rocket_badges",
        method="turns",
        choice="hoard",
        captain="Blu",
        captain_gender="girl",
        crew_mate="Finn",
        crew_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="rings",
        supply="moonfruit",
        method="turns",
        choice="hoard",
        captain="Mia",
        captain_gender="girl",
        crew_mate="Blu",
        crew_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
valid(S, M) :- supply(S), method(M), count(C), crew_size(N), C >= N, divisible(C, N), not needs_dividing(S).
valid(S, M) :- supply(S), method(M), count(C), crew_size(N), C >= N, not divisible(C, N), can_divide(M), not indivisible(S).

outcome(shared) :- chosen_choice(share), chosen_supply(S), chosen_method(M), valid(S, M).
outcome(bad) :- chosen_choice(hoard).
outcome(bad) :- chosen_choice(share), chosen_supply(S), chosen_method(M), not valid(S, M).

#show valid/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        if supply.indivisible:
            lines.append(asp.fact("indivisible", sid))
        else:
            lines.append(asp.fact("needs_dividing", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        if method.can_divide:
            lines.append(asp.fact("can_divide", mid))
    lines.append(asp.fact("count", 4))
    lines.append(asp.fact("crew_size", CREW_SIZE))
    if 4 % CREW_SIZE == 0:
        lines.append(asp.fact("divisible", 4, CREW_SIZE))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_supply", params.supply),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pretend space mission, four special supplies, and a choice to share or hoard."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (supply, method) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.supply and args.method:
        supply = SUPPLIES[args.supply]
        method = METHODS[args.method]
        if not can_share_evenly(supply, method):
            raise StoryError(explain_rejection(supply, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.supply is None or combo[0] == args.supply)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    supply_id, method_id = rng.choice(sorted(combos))
    mission_id = args.mission or rng.choice(sorted(MISSIONS))
    choice_id = args.choice or rng.choice(sorted(CHOICES))
    parent = args.parent or rng.choice(["mother", "father"])

    captain_gender = rng.choice(["girl", "boy"])
    crew_gender = rng.choice(["girl", "boy"])
    captain = _pick_name(rng, captain_gender)
    crew_mate = _pick_name(rng, crew_gender, avoid=captain)

    return StoryParams(
        mission=mission_id,
        supply=supply_id,
        method=method_id,
        choice=choice_id,
        captain=captain,
        captain_gender=captain_gender,
        crew_mate=crew_mate,
        crew_gender=crew_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        supply = SUPPLIES[params.supply]
        method = METHODS[params.method]
        choice = CHOICES[params.choice]
    except KeyError as exc:
        raise StoryError(f"(Unknown story parameter: {exc.args[0]})") from None

    if not can_share_evenly(supply, method):
        raise StoryError(explain_rejection(supply, method))

    world = tell(
        mission=mission,
        supply=supply,
        method=method,
        choice=choice,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        crew_name=params.crew_mate,
        crew_gender=params.crew_gender,
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


def outcome_of(params: StoryParams) -> str:
    return predict_outcome(SUPPLIES[params.supply], METHODS[params.method], CHOICES[params.choice])


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                mismatches += 1
        except Exception as exc:
            rc = 1
            print(f"ERROR during outcome parity check: {exc}")
            break

    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

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
        print(f"{len(combos)} compatible (supply, method) combos:\n")
        for supply_id, method_id in combos:
            print(f"  {supply_id:14} {method_id}")
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
            header = f"### {p.captain} and crew: {p.supply} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
