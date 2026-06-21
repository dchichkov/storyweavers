#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py
==========================================================

A standalone story world about a playful backyard adventure that turns into a
gentle rescue mission. Two children make an "expedition sea" out of a tub, spot
a tiny creature struggling in the water, and choose a kind, sensible way to
help.

The story is driven by simulated state:
- the tub becomes risky once a small creature is stuck in it
- waiting makes the creature more tired
- a rescue tool must be both gentle enough and sturdy enough
- if the creature is very tired, the children need a grown-up's steady help

The domain aims for:
- Kindness: the children pause their game to help something smaller than they are
- Humor: the adventure is full of silly captain talk and splashy imagination
- Adventure: the rescue is told like a tiny expedition with a real turn

Run it
------
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --mission river --creature snail
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --tool splash_cup
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --all
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --json
    python storyworlds/worlds/gpt-5.4/tub_kindness_humor_adventure.py --verify
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
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Mission:
    id: str
    scene: str
    opening: str
    titles: tuple[str, str]
    water_name: str
    joke_name: str
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
class Creature:
    id: str
    label: str
    article: str
    tiny_sound: str
    home: str
    step_text: str
    need_support: int
    delicacy: int
    risk: int
    tags: set[str] = field(default_factory=set)

    @property
    def phrase(self) -> str:
        return f"{self.article} {self.label}"
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    support: int
    gentleness: int
    power: int
    action_text: str
    wobble_text: str
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_stranded(world: World) -> list[str]:
    creature = world.get("creature")
    tub = world.get("tub")
    if creature.meters["in_water"] < THRESHOLD or creature.meters["rescued"] >= THRESHOLD:
        return []
    sig = ("stranded",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tub.meters["danger"] += 1
    creature.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["concern"] += 1
    return []


def _r_waiting(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["waiting"] < THRESHOLD or creature.meters["rescued"] >= THRESHOLD:
        return []
    sig = ("waiting", int(creature.meters["waiting"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["tired"] += creature.meters["waiting"]
    creature.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["concern"] += 1
    return []


def _r_rescue_relief(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["fear"] = 0.0
    world.get("tub").meters["danger"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["kindness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stranded", tag="physical", apply=_r_stranded),
    Rule(name="waiting", tag="physical", apply=_r_waiting),
    Rule(name="relief", tag="social", apply=_r_rescue_relief),
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
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rescue_possible(tool: Tool, creature: Creature) -> bool:
    return tool.gentleness >= creature.delicacy and tool.support >= creature.need_support


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def rescue_difficulty(creature: Creature, delay: int) -> int:
    return creature.risk + delay


def child_can_finish(tool: Tool, creature: Creature, delay: int) -> bool:
    return tool.power >= rescue_difficulty(creature, delay)


def predict_wobble(world: World, delay: int) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    creature.meters["waiting"] += delay
    propagate(sim, narrate=False)
    return {
        "tired": creature.meters["tired"],
        "fear": creature.memes["fear"],
        "danger": sim.get("tub").meters["danger"],
    }


def play_setup(world: World, captain: Entity, mate: Entity, mission: Mission) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    mate.memes["humor"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned the yard into "
        f"{mission.scene}. {mission.opening}"
    )
    world.say(
        f'"{mission.titles[0]} {captain.id}!" {mate.id} cried in a booming voice. '
        f'"{mission.titles[1]} {mate.id} is ready for {mission.water_name}!"'
    )


def sail(world: World, captain: Entity, mate: Entity, mission: Mission) -> None:
    world.say(
        f"They marched around the big tub as if it were {mission.water_name}, and "
        f"{mate.id} pointed at every wobble in the water as if it might be "
        f"{mission.joke_name}."
    )
    world.say(
        f"When {mate.id} made a terribly serious sea-monster face, {captain.id} laughed "
        f"so hard that {captain.pronoun()} almost dropped the cork boat."
    )


def spot_trouble(world: World, captain: Entity, creature: Creature, mission: Mission) -> None:
    bug = world.get("creature")
    bug.meters["in_water"] = 1.0
    bug.meters["wet"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {captain.id} stopped laughing. In the middle of the tub, {creature.phrase} "
        f"was going in a little circle beside the cork boat, making a tiny "
        f"{creature.tiny_sound} against the water."
    )
    world.say(
        f'"That is not {mission.joke_name}," {captain.id} said. "That is somebody who needs help."'
    )


def warning(world: World, mate: Entity, creature: Creature, delay: int) -> None:
    pred = predict_wobble(world, delay)
    world.facts["predicted_tired"] = pred["tired"]
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["tired"] >= 2:
        extra = " Another lap around the tub would make the tiny traveler even more tired."
    world.say(
        f"{mate.id} leaned close and stopped joking at once. "
        f'"Poor little {creature.label}," {mate.pronoun()} whispered.{extra}'
    )


def wait_beats(world: World, mate: Entity, delay: int) -> None:
    if delay <= 0:
        return
    creature = world.get("creature")
    creature.meters["waiting"] += float(delay)
    propagate(world, narrate=False)
    if delay == 1:
        world.say(
            f"As they hurried into rescue-team positions, the cork boat bumped the side of the tub "
            f"and made one small slosh. {mate.id} put both hands on {mate.pronoun('possessive')} cheeks "
            f"and said, \"No more monster jokes now.\""
        )
    else:
        world.say(
            f"For two worried breaths, the water kept wobbling. The little tub sea looked much too big "
            f"for such a tiny traveler, and even the funny game felt quiet."
        )


def choose_kindness(world: World, captain: Entity, mate: Entity, tool: Tool) -> None:
    captain.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    world.say(
        f'"Rescue gear!" said {captain.id}. Instead of splashing, the two children reached for '
        f"{tool.phrase} and knelt beside the tub together."
    )


def rescue_by_children(world: World, captain: Entity, mate: Entity,
                       creature: Creature, tool: Tool) -> None:
    bug = world.get("creature")
    bug.meters["rescued"] = 1.0
    bug.meters["in_water"] = 0.0
    propagate(world, narrate=False)
    world.say(tool.action_text.format(captain=captain.id, mate=mate.id, creature=creature.label))
    world.say(
        f"{creature.article.capitalize()} {creature.label} clung for one blink, then {creature.step_text} "
        f"onto the dry stone beside the tub."
    )


def grownup_steady_help(world: World, parent: Entity, captain: Entity, mate: Entity,
                        creature: Creature, tool: Tool) -> None:
    bug = world.get("creature")
    bug.meters["rescued"] = 1.0
    bug.meters["in_water"] = 0.0
    world.get("tub").meters["waves"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{captain.id} held very still, but the rescue wobbled. So {mate.id} called for "
        f"{parent.label_word}, and {parent.label_word} came over without teasing them for stopping the game."
    )
    world.say(
        f"{parent.label_word.capitalize()} steadied the rim of the tub while the children used {tool.phrase}. "
        f"{tool.wobble_text.format(captain=captain.id, mate=mate.id, creature=creature.label)}"
    )


def settle_and_release(world: World, captain: Entity, mate: Entity, mission: Mission,
                       creature: Creature, parent: Entity, outcome: str) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    if outcome == "grownup_help":
        world.say(
            f'"Best crew in the yard," {parent.label_word} said. That made both children sit a little taller.'
        )
    else:
        world.say(
            f'"Adventure captains can be gentle too," said {mate.id}, and this time the joke made everyone smile.'
        )
    world.say(
        f"They watched {creature.phrase} pause in the sun, then head toward {creature.home}. "
        f"After that, the tub was not just a pretend sea anymore. It was the place where their game turned kind."
    )
    world.say(mission.ending)


def tell(mission: Mission, creature_cfg: Creature, tool_cfg: Tool,
         captain_name: str = "Lily", captain_gender: str = "girl",
         mate_name: str = "Ben", mate_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=["bold", "kind"],
        attrs={},
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=["funny", "kind"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    tub = world.add(Entity(
        id="tub",
        type="tub",
        label="tub",
        attrs={},
    ))
    creature = world.add(Entity(
        id="creature",
        type="creature",
        label=creature_cfg.label,
        attrs={"home": creature_cfg.home},
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        attrs={},
    ))

    world.facts["predicted_tired"] = 0.0
    world.facts["predicted_danger"] = 0.0

    play_setup(world, captain, mate, mission)
    sail(world, captain, mate, mission)

    world.para()
    spot_trouble(world, captain, creature_cfg, mission)
    warning(world, mate, creature_cfg, delay)
    wait_beats(world, mate, delay)
    choose_kindness(world, captain, mate, tool_cfg)

    world.para()
    outcome = "child_rescue" if child_can_finish(tool_cfg, creature_cfg, delay) else "grownup_help"
    if outcome == "child_rescue":
        rescue_by_children(world, captain, mate, creature_cfg, tool_cfg)
    else:
        grownup_steady_help(world, parent, captain, mate, creature_cfg, tool_cfg)

    world.para()
    settle_and_release(world, captain, mate, mission, creature_cfg, parent, outcome)

    world.facts.update(
        mission=mission,
        creature_cfg=creature_cfg,
        tool_cfg=tool_cfg,
        captain=captain,
        mate=mate,
        parent=parent,
        tub=tub,
        creature=creature,
        tool=tool,
        delay=delay,
        outcome=outcome,
        rescued=creature.meters["rescued"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "river": Mission(
        id="river",
        scene="a roaring river expedition",
        opening="A big blue tub became the river, a laundry basket became the mountain camp, and a cork boat was their brave little ferry.",
        titles=("Captain", "Scout"),
        water_name="the wild river",
        joke_name="the tickle-splash monster",
        ending="Soon the cork boat was sailing again, but now the bravest thing on board was the kindness in the crew.",
        tags={"river", "adventure"},
    ),
    "jungle": Mission(
        id="jungle",
        scene="a jungle rescue trail",
        opening="A green tub became a jungle lagoon, a mop handle became a vine bridge, and a striped towel became the map to hidden reeds.",
        titles=("Leader", "Pathfinder"),
        water_name="the lagoon",
        joke_name="the bubble-snorting swamp dragon",
        ending="They went marching off again around the tub, laughing softly and keeping a watch for any other tiny traveler who might need a rescue.",
        tags={"jungle", "adventure"},
    ),
    "space": Mission(
        id="space",
        scene="a moon-mission landing zone",
        opening="A silver tub became a moon crater lake, a cardboard box became mission control, and the cork boat was promoted to emergency rescue shuttle.",
        titles=("Commander", "Pilot"),
        water_name="the crater sea",
        joke_name="the glug-glug moon beast",
        ending="The rescue shuttle made another lap around the tub, and both astronauts agreed that heroes use gentle hands as well as brave ones.",
        tags={"space", "adventure"},
    ),
}

CREATURES = {
    "ladybug": Creature(
        id="ladybug",
        label="ladybug",
        article="a",
        tiny_sound="tap-tap",
        home="the rose bush",
        step_text="opened its spotted wings and stepped",
        need_support=1,
        delicacy=2,
        risk=1,
        tags={"ladybug", "bug", "kindness"},
    ),
    "snail": Creature(
        id="snail",
        label="snail",
        article="a",
        tiny_sound="soft scrape",
        home="the damp flowerpot",
        step_text="lifted its feelers and slid",
        need_support=2,
        delicacy=3,
        risk=2,
        tags={"snail", "garden", "kindness"},
    ),
    "cricket": Creature(
        id="cricket",
        label="cricket",
        article="a",
        tiny_sound="tick",
        home="the tall grass",
        step_text="folded its legs and hopped",
        need_support=2,
        delicacy=2,
        risk=2,
        tags={"cricket", "insect", "kindness"},
    ),
}

TOOLS = {
    "leaf": Tool(
        id="leaf",
        label="leaf",
        phrase="a broad leaf",
        sense=3,
        support=2,
        gentleness=3,
        power=2,
        action_text="{captain} slid the broad leaf under the {creature} while {mate} whispered, \"Easy does it, crew.\"",
        wobble_text="Together they made a quiet little bridge, and the {creature} rode the leaf out of the water.",
        qa_text="They used a broad leaf like a tiny rescue raft.",
        tags={"leaf", "gentle", "garden"},
    ),
    "spoon": Tool(
        id="spoon",
        label="wooden spoon",
        phrase="a wooden spoon",
        sense=3,
        support=2,
        gentleness=2,
        power=3,
        action_text="{mate} held the wooden spoon steady while {captain} guided the {creature} onto it as if loading a treasure boat.",
        wobble_text="With the spoon held steady and patient hands on both sides, the {creature} was lifted out safely.",
        qa_text="They used a wooden spoon and kept it very still.",
        tags={"spoon", "gentle", "tool"},
    ),
    "net": Tool(
        id="net",
        label="little net",
        phrase="a little net",
        sense=3,
        support=3,
        gentleness=3,
        power=4,
        action_text="{captain} lowered the little net into the water, and {mate} tilted it just enough for the {creature} to climb aboard.",
        wobble_text="The grown-up kept the water calm, and the little net carried the {creature} out like a proper rescue boat.",
        qa_text="They lowered a little net and lifted the creature out gently.",
        tags={"net", "rescue", "tool"},
    ),
    "splash_cup": Tool(
        id="splash_cup",
        label="plastic cup",
        phrase="a plastic cup",
        sense=1,
        support=1,
        gentleness=1,
        power=1,
        action_text="",
        wobble_text="",
        qa_text="",
        tags={"cup"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for creature_id, creature in CREATURES.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and rescue_possible(tool, creature):
                    combos.append((mission_id, creature_id, tool_id))
    return combos


@dataclass
class StoryParams:
    mission: str
    creature: str
    tool: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
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
    "ladybug": [
        (
            "What is a ladybug?",
            "A ladybug is a small beetle with a round body and spots on its shell. It is tiny, so gentle hands are important around it.",
        )
    ],
    "snail": [
        (
            "Why does a snail need a gentle rescue?",
            "A snail has a soft body and moves slowly, so a rough poke can hurt it. A broad, gentle surface helps it stay safe.",
        )
    ],
    "cricket": [
        (
            "Why can a cricket be hard to rescue?",
            "A cricket is small and quick, and its legs can slip on wet surfaces. Calm, careful movements make it easier to help.",
        )
    ],
    "leaf": [
        (
            "Why can a leaf help in a tiny rescue?",
            "A broad leaf can float and gives a small creature a soft place to climb. It works like a tiny raft.",
        )
    ],
    "spoon": [
        (
            "Why would a wooden spoon help carefully?",
            "A wooden spoon has a smooth bowl that can hold something small without poking it. If you keep it steady, it can lift gently.",
        )
    ],
    "net": [
        (
            "What is a little net used for?",
            "A little net can scoop something light out of water without needing to grab it. That makes it useful for gentle rescue jobs.",
        )
    ],
    "bug": [
        (
            "Why is kindness important with tiny animals?",
            "Tiny animals are easy to scare and easy to hurt. Being kind means moving slowly and helping without rough hands.",
        )
    ],
    "garden": [
        (
            "Why do many little creatures live near plants and pots?",
            "Plants, damp soil, and grass can give tiny creatures food and hiding places. A garden is full of small homes.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ladybug", "snail", "cricket", "leaf", "spoon", "net", "bug", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    mission = f["mission"]
    creature = f["creature_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "grownup_help":
        return [
            f'Write an adventure story for a 3-to-5-year-old that includes the word "tub" and shows kindness and humor.',
            f"Tell a gentle rescue story where {captain.id} and {mate.id} turn a tub into {mission.water_name}, spot {creature.phrase} in trouble, and call a grown-up when the rescue gets wobbly.",
            f"Write a funny but caring backyard adventure where children stop pretending for a moment to help something tiny with {tool.phrase}.",
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "tub" and shows kindness and humor.',
        f"Tell a playful rescue story where {captain.id} and {mate.id} turn a tub into {mission.water_name}, then use {tool.phrase} to save {creature.phrase}.",
        f"Write a funny backyard adventure where a pretend mission becomes a real act of kindness for a tiny creature.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    mission = f["mission"]
    creature = f["creature_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    delay = f["delay"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {mate.id}, two children who turned a tub into {mission.water_name}. Their game changed when they noticed {creature.phrase} needed help.",
        ),
        (
            "What was funny at the beginning?",
            f"{mate.id} made silly monster faces and gave the pretend water a funny name. The jokes made the adventure feel cheerful before the real rescue began.",
        ),
        (
            f"Why did the children stop playing and start helping the {creature.label}?",
            f"They saw {creature.phrase} stuck in the tub water, and it looked too small for such a big splashy place. That made kindness more important than the game.",
        ),
        (
            "How did they try to help?",
            f"{tool.qa_text} They chose that tool because it was gentle instead of splashy.",
        ),
    ]
    if outcome == "child_rescue":
        qa.append(
            (
                "Did the children rescue the creature by themselves?",
                f"Yes. They worked together and kept very still, so the rescue stayed calm. Because the wait was only {delay} beat long, the {creature.label} was tired but not too tired for them to finish the job.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {captain.id} and {mate.id} call {parent.label_word}?",
                f"The rescue had become wobbly, and the little creature was more tired after waiting in the water. Asking a grown-up for steady help was part of being kind, because it gave the rescue a safer ending.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The {creature.label} got out of the tub safely and headed back toward {creature.home}. The children kept their adventure, but now they felt proud because they had been gentle heroes.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["creature_cfg"].tags) | set(f["tool_cfg"].tags)
    tags.add("bug")
    if "garden" in f["creature_cfg"].tags or f["creature_cfg"].id == "snail":
        tags.add("garden")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="river",
        creature="ladybug",
        tool="leaf",
        captain="Lily",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        mission="jungle",
        creature="snail",
        tool="net",
        captain="Max",
        captain_gender="boy",
        mate="Mia",
        mate_gender="girl",
        parent="father",
        delay=1,
    ),
    StoryParams(
        mission="space",
        creature="cricket",
        tool="spoon",
        captain="Ava",
        captain_gender="girl",
        mate="Theo",
        mate_gender="boy",
        parent="mother",
        delay=2,
    ),
    StoryParams(
        mission="river",
        creature="snail",
        tool="leaf",
        captain="Sam",
        captain_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="father",
        delay=2,
    ),
]


def explain_rejection(tool: Tool, creature: Creature) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.phrase} is too splashy and careless for a tiny rescue. "
            f"Pick a gentler tool like a broad leaf, a wooden spoon, or a little net.)"
        )
    if tool.gentleness < creature.delicacy:
        return (
            f"(No story: {tool.phrase} is not gentle enough for {creature.phrase}. "
            f"This world only tells rescues that treat small creatures carefully.)"
        )
    if tool.support < creature.need_support:
        return (
            f"(No story: {tool.phrase} is too small or narrow to carry {creature.phrase} out of the tub safely.)"
        )
    return "(No story: this rescue setup is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    creature = CREATURES[params.creature]
    tool = TOOLS[params.tool]
    return "child_rescue" if child_can_finish(tool, creature, params.delay) else "grownup_help"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
rescue_possible(C, T) :- creature(C), tool(T), delicacy(C, D), gentleness(T, G),
                         support_need(C, N), support(T, S), G >= D, S >= N.
sensible(T) :- tool(T), sense(T, V), sense_min(M), V >= M.
valid(Mission, C, T) :- mission(Mission), creature(C), tool(T), rescue_possible(C, T), sensible(T).

% --- outcome model ---------------------------------------------------------
difficulty(R + D) :- chosen_creature(C), risk(C, R), delay(D).
child_rescue :- chosen_tool(T), power(T, P), difficulty(Need), P >= Need.
outcome(child_rescue) :- child_rescue.
outcome(grownup_help) :- not child_rescue.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("support_need", cid, creature.need_support))
        lines.append(asp.fact("delicacy", cid, creature.delicacy))
        lines.append(asp.fact("risk", cid, creature.risk))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("support", tid, tool.support))
        lines.append(asp.fact("gentleness", tid, tool.gentleness))
        lines.append(asp.fact("power", tid, tool.power))
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
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tub adventure that becomes a kind rescue."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the creature wobbles in the tub before the rescue settles")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_rejection(TOOLS[args.tool], CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))))
    if args.tool and args.creature:
        tool = TOOLS[args.tool]
        creature = CREATURES[args.creature]
        if not rescue_possible(tool, creature) or tool.sense < SENSE_MIN:
            raise StoryError(explain_rejection(tool, creature))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.creature is None or combo[1] == args.creature)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, creature, tool = rng.choice(sorted(combos))
    captain, captain_gender = _pick_child(rng)
    mate, mate_gender = _pick_child(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        mission=mission,
        creature=creature,
        tool=tool,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    mission = MISSIONS[params.mission]
    creature = CREATURES[params.creature]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN or not rescue_possible(tool, creature):
        raise StoryError(explain_rejection(tool, creature))

    world = tell(
        mission=mission,
        creature_cfg=creature,
        tool_cfg=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        delay=params.delay,
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

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {tool.id for tool in sensible_tools()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible tools match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {s}.")
            break

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
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke, trace=False, qa=False, header="")
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, creature, tool) combos:\n")
        for mission, creature, tool in combos:
            print(f"  {mission:8} {creature:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.captain} & {p.mate}: {p.creature} in the tub ({p.mission}, {p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
