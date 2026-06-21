#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py
=======================================================================================

A standalone story world for a tiny rhyming, problem-solving tale about a child
in a raincoat hood who notices a small emergency and helps solve it step by
step.

Reference seed, rebuilt as a world model:
-----------------------------------------
A child walks in light rain with a raincoat hood. A small animal gets stuck in a
raining-day problem spot. The child first wants to help too quickly, but a calm
grown-up turns the rescue into a step-by-step progression: notice the danger,
pick the right helper, use the right tool, and bring the animal to safety. The
ending proves what changed: the child now thinks in steps instead of rushing.

Run it
------
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py --animal kitten --trap drain_grate
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py --tool towel
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/progression_emergency_hood_problem_solving_rhyming_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Animal:
    id: str
    label: str
    cry: str
    motion: str
    comfort: str
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
class Trap:
    id: str
    label: str
    the: str
    danger: str
    place_line: str
    rescue_need: str
    risk_level: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    action: str
    kind: str
    sense: int
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
    type: str
    phrase: str
    skill: str
    kind: str
    sense: int
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


def _r_emergency(world: World) -> list[str]:
    animal = world.get("animal")
    trap = world.get("trap")
    child = world.get("child")
    if animal.meters["stuck"] < THRESHOLD or trap.meters["hazard"] < THRESHOLD:
        return []
    sig = ("emergency", animal.id, trap.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["concern"] += 1
    world.facts["emergency"] = True
    return ["__emergency__"]


def _r_soothe(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    if child.memes["calm_plan"] < THRESHOLD or animal.meters["stuck"] < THRESHOLD:
        return []
    sig = ("soothe", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["trust"] += 1
    return []


def _r_rescue(world: World) -> list[str]:
    animal = world.get("animal")
    tool = world.get("tool")
    helper = world.get("helper")
    if animal.meters["stuck"] < THRESHOLD:
        return []
    if tool.meters["ready"] < THRESHOLD or helper.meters["arrived"] < THRESHOLD:
        return []
    sig = ("rescue", animal.id, tool.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["stuck"] = 0.0
    animal.meters["safe"] += 1
    world.get("trap").meters["hazard"] = 0.0
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return ["__rescued__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="emergency", tag="social", apply=_r_emergency),
    Rule(name="soothe", tag="social", apply=_r_soothe),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
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


ANIMALS = {
    "kitten": Animal(
        id="kitten",
        label="kitten",
        cry="mewed",
        motion="tiny paws",
        comfort="warm and tucked in tight",
        tags={"kitten", "animal"},
    ),
    "duckling": Animal(
        id="duckling",
        label="duckling",
        cry="peeped",
        motion="little yellow feet",
        comfort="soft and safe beside the reeds",
        tags={"duckling", "animal"},
    ),
    "puppy": Animal(
        id="puppy",
        label="puppy",
        cry="yipped",
        motion="muddy paws",
        comfort="snuggled with a happy sigh",
        tags={"puppy", "animal"},
    ),
}

TRAPS = {
    "drain_grate": Trap(
        id="drain_grate",
        label="drain grate",
        the="the drain grate",
        danger="fast rainwater rushing underneath",
        place_line="beside the curb where rain ran thin",
        rescue_need="reach",
        risk_level=3,
        tags={"drain", "rain", "emergency"},
    ),
    "thorn_bush": Trap(
        id="thorn_bush",
        label="thorn bush",
        the="the thorn bush",
        danger="sharp twigs that tugged and scratched",
        place_line="by the gate where brambles grew",
        rescue_need="lift",
        risk_level=2,
        tags={"thorn", "garden", "emergency"},
    ),
    "muddy_ditch": Trap(
        id="muddy_ditch",
        label="muddy ditch",
        the="the muddy ditch",
        danger="slippery mud at the edge",
        place_line="near the path where puddles spread",
        rescue_need="bridge",
        risk_level=2,
        tags={"ditch", "mud", "emergency"},
    ),
}

TOOLS = {
    "umbrella_hook": Tool(
        id="umbrella_hook",
        label="umbrella",
        phrase="a long umbrella with a hooked handle",
        action="looped the curved handle gently where it could guide and reach",
        kind="reach",
        sense=3,
        tags={"umbrella", "reach"},
    ),
    "towel": Tool(
        id="towel",
        label="towel",
        phrase="a soft dry towel",
        action="wrapped the little body softly once it was free",
        kind="lift",
        sense=2,
        tags={"towel", "soft"},
    ),
    "board": Tool(
        id="board",
        label="board",
        phrase="a flat wooden board",
        action="laid the board down like a tiny bridge over the wobbling side",
        kind="bridge",
        sense=3,
        tags={"board", "bridge"},
    ),
}

HELPERS = {
    "parent": Helper(
        id="parent",
        label="parent",
        type="mother",
        phrase="her mom",
        skill="came close, looked twice, and planned before acting",
        kind="home",
        sense=3,
        tags={"parent", "adult"},
    ),
    "gardener": Helper(
        id="gardener",
        label="gardener",
        type="man",
        phrase="the gardener from the gate",
        skill="knew the bushes well and wore thick gloves",
        kind="garden",
        sense=3,
        tags={"gardener", "adult"},
    ),
    "park_ranger": Helper(
        id="park_ranger",
        label="park ranger",
        type="woman",
        phrase="the park ranger with calm boots",
        skill="noticed slippery places and knew how to guide small animals",
        kind="path",
        sense=3,
        tags={"ranger", "adult"},
    ),
    "big_brother": Helper(
        id="big_brother",
        label="big brother",
        type="boy",
        phrase="her big brother",
        skill="wanted to help fast but was still learning",
        kind="home",
        sense=1,
        tags={"sibling", "adult_help"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ruby", "Ivy", "Zoe", "Tessa"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Leo", "Owen", "Jude", "Sam"]
TRAITS = ["careful", "bright", "gentle", "steady", "curious", "kind"]


def trap_allows_helper(trap: Trap, helper: Helper) -> bool:
    if helper.sense < SENSE_MIN:
        return False
    allowed = {
        "drain_grate": {"parent", "park_ranger"},
        "thorn_bush": {"parent", "gardener"},
        "muddy_ditch": {"parent", "park_ranger"},
    }
    return helper.id in allowed[trap.id]


def rescue_possible(trap: Trap, tool: Tool, helper: Helper) -> bool:
    return tool.kind == trap.rescue_need and trap_allows_helper(trap, helper)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for trap_id, trap in TRAPS.items():
        for tool_id, tool in TOOLS.items():
            for helper_id, helper in HELPERS.items():
                if rescue_possible(trap, tool, helper):
                    combos.append((trap_id, tool_id, helper_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    trap: str
    tool: str
    helper: str
    child_name: str
    child_gender: str
    coat_color: str
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


def setup_walk(world: World, child: Entity, coat_color: str) -> None:
    child.memes["wonder"] += 1
    child.attrs["hood_on"] = True
    world.say(
        f"{child.id} skipped through silver weather in a {coat_color} coat with a bright little hood. "
        f"The drops went pit-pat, tip-tat, and the lane felt soft and good."
    )
    world.say(
        f"{child.pronoun().capitalize()} hummed a rainy rhyme and watched the shining street. "
        f"Each puddle made a mirror-glow beneath {child.pronoun('possessive')} splashing feet."
    )


def spot_problem(world: World, child: Entity, animal: Entity, trap: Trap) -> None:
    animal.meters["stuck"] += 1
    world.get("trap").meters["hazard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then from {trap.place_line}, a tiny sound came through the gray: "
        f"a little {animal.label} {animal.attrs['cry']} as if to say, 'Please help today.'"
    )
    world.say(
        f"{trap.The} held the poor small thing in a rainy, wiggly tangle. "
        f"It was not a game at all now. It was a small emergency to handle."
    )


def rush_idea(world: World, child: Entity, trap: Trap) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"{child.id} bent low and reached one hand toward {trap.the} in a hurry-fast way. "
        f"But the rushing water, thorns, or mud made a risky, slippery stay."
    )


def pause_and_plan(world: World, child: Entity, helper: Entity, trap: Trap, tool: Tool) -> None:
    child.memes["calm_plan"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Wait," said {helper.attrs["call_name"]}, "let\'s use our heads before our hands." '
        f'{helper.pronoun().capitalize()} looked at {trap.the} and where the trouble stands.'
    )
    world.say(
        f'"First we stop. Next we think. Then we choose the safest progression. '
        f'This little emergency needs calm problem solving, not a splashy guessing session."'
    )
    world.say(
        f"{child.id} pulled back {child.pronoun('possessive')} hand, tucked snugly in the hood, and nodded slow. "
        f"The plan began to feel like a lantern with a step-by-step kind of glow."
    )
    world.facts["progression_line"] = "First we stop. Next we think. Then we choose the safest progression."


def bring_helper(world: World, helper: Entity) -> None:
    helper.meters["arrived"] += 1
    world.say(
        f"Soon {helper.attrs['call_name']} was right there too, calm-eyed and steady on the ground. "
        f"{helper.pronoun().capitalize()} {helper.attrs['skill_line']}, and safe ideas gathered round."
    )


def use_tool(world: World, helper: Entity, animal: Entity, trap: Trap, tool: Tool) -> None:
    world.get("tool").meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Out came {tool.phrase}. {helper.attrs['call_name'].capitalize()} {tool.action}. "
        f"No jerks, no yanks, no frightened fuss, just patient care in rainy fashion."
    )
    if trap.id == "drain_grate":
        world.say(
            f"The handle slid beside the bars and gave the {animal.label} space to climb. "
            f"One careful nudge, one brave small hop, and out it came in nick of time."
        )
    elif trap.id == "thorn_bush":
        world.say(
            f"The branches lifted, slow and wide, while soft cloth kept the scratches slight. "
            f"The {animal.label} wriggled free and blinked into the silver light."
        )
    else:
        world.say(
            f"The board lay firm above the ooze, a tiny bridge the paws could trust. "
            f"The {animal.label} tiptoed up and reached the path with one small gust."
        )
    propagate(world, narrate=False)


def comfort_and_end(world: World, child: Entity, helper: Entity, animal: Entity, tool: Tool) -> None:
    animal.memes["calm"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} crouched low and whispered soft while rain sang on the neighborhood. "
        f"The little {animal.label} soon looked {animal.attrs['comfort_line']}, warm and understood."
    )
    if tool.id == "towel":
        world.say(
            f"The towel made a gentle nest; the worried shakes grew small and slow. "
            f"Then off the little creature went where safer feet could go."
        )
    else:
        world.say(
            f"A shake, a blink, a grateful look, and then the tiny creature stood. "
            f"It scampered off to safer grass beyond the dripping neighborhood."
        )
    world.say(
        f'On the walk back home, {child.id} said, "I know what brave can be. '
        f'Not rush and grab, but stop and think, then solve the problem carefully."'
    )
    world.say(
        f"The rain still tapped upon the hood, but now the tune sounded good: "
        f"a thoughtful child, a solved-up scare, and kindness where {helper.attrs['call_name']} stood."
    )


def tell(
    animal_cfg: Animal,
    trap_cfg: Trap,
    tool_cfg: Tool,
    helper_cfg: Helper,
    child_name: str = "Lina",
    child_gender: str = "girl",
    coat_color: str = "yellow",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"call_name": child_name},
    ))
    helper_type = "mother" if helper_cfg.id == "parent" else helper_cfg.type
    helper_name = "Mom" if helper_cfg.id == "parent" else helper_cfg.label
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_cfg.label,
        role="helper",
        attrs={"call_name": helper_name, "skill_line": helper_cfg.skill},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="animal",
        type=animal_cfg.id,
        label=animal_cfg.label,
        role="animal",
        attrs={"cry": animal_cfg.cry, "comfort_line": animal_cfg.comfort},
    ))
    trap = world.add(Entity(
        id="trap",
        kind="thing",
        type="trap",
        label=trap_cfg.label,
        role="trap",
        attrs={"danger": trap_cfg.danger},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        role="tool",
        attrs={},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        trap_cfg=trap_cfg,
        tool_cfg=tool_cfg,
        helper_cfg=helper_cfg,
        coat_color=coat_color,
        emergency=False,
    )

    setup_walk(world, child, coat_color)
    world.para()
    spot_problem(world, child, animal, trap_cfg)
    rush_idea(world, child, trap_cfg)
    world.para()
    pause_and_plan(world, child, helper, trap_cfg, tool_cfg)
    bring_helper(world, helper)
    use_tool(world, helper, animal, trap_cfg, tool_cfg)
    world.para()
    comfort_and_end(world, child, helper, animal, tool_cfg)

    world.facts.update(
        rescued=animal.meters["safe"] >= THRESHOLD,
        tool_used=tool_cfg.id,
        helper_used=helper_cfg.id,
        problem_kind=trap_cfg.id,
        child_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "emergency": [
        (
            "What is an emergency?",
            "An emergency is a problem that needs help right away because someone could get hurt or stay in danger. In a small emergency, the best first step is to get a calm grown-up and make a safe plan."
        )
    ],
    "hood": [
        (
            "What does a hood do on a raincoat?",
            "A hood covers your head and helps keep rain off your hair and face. That can help you stay warmer and see better while you walk."
        )
    ],
    "problem_solving": [
        (
            "What does it mean to solve a problem step by step?",
            "It means you do not rush. You stop, think, choose a good plan, and then try the safest step first."
        )
    ],
    "drain": [
        (
            "Why is a drain grate dangerous in the rain?",
            "Rainwater can rush under a drain grate and make the ground slippery. Small paws or feet can get stuck near the bars."
        )
    ],
    "thorn": [
        (
            "Why are thorn bushes hard to get out of?",
            "Thorns can poke and catch on fur or clothes. That is why people move carefully and use protection instead of pulling hard."
        )
    ],
    "ditch": [
        (
            "Why is a muddy ditch slippery?",
            "Wet mud slides under your feet and can make you slip. A flat board can make a safer path across the soft edge."
        )
    ],
    "umbrella": [
        (
            "How can an umbrella help in a rescue?",
            "A long umbrella can help someone reach from a safer distance. Its curved handle can guide without needing a child to climb into danger."
        )
    ],
    "towel": [
        (
            "Why can a towel help a scared animal?",
            "A soft towel can keep an animal warm and still after it gets free. It feels gentle and can stop shivering."
        )
    ],
    "board": [
        (
            "What can a board do in a muddy place?",
            "A flat board can spread weight and make a tiny bridge over mud. That gives paws or feet a steadier path."
        )
    ],
    "adult": [
        (
            "Why should children call a grown-up for a rescue problem?",
            "Grown-ups are bigger, steadier, and can choose tools more safely. Calling for help is smart and brave."
        )
    ],
}
KNOWLEDGE_ORDER = ["emergency", "hood", "problem_solving", "drain", "thorn", "ditch", "umbrella", "towel", "board", "adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trap = f["trap_cfg"]
    animal = f["animal"]
    tool = f["tool_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "progression", "emergency", and "hood".',
        f"Tell a gentle rainy-day story where {child.attrs['call_name']} sees a {animal.label} stuck at {trap.the} and solves the problem step by step with help.",
        f"Write a rhyming problem-solving story where a child in a raincoat hood faces a small emergency, uses {tool.label}, and ends by learning to think before rushing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    animal = f["animal"]
    trap = f["trap_cfg"]
    tool = f["tool_cfg"]
    helper_name = helper.attrs["call_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['call_name']}, a child in a raincoat hood, and a little {animal.label} in trouble. A calm helper named {helper_name} also helps solve the problem."
        ),
        (
            "What was the emergency?",
            f"The little {animal.label} was stuck at {trap.the} while the rainy place was unsafe. It was an emergency because the child could see real danger and knew the animal needed help soon."
        ),
        (
            "Why did the child stop reaching in right away?",
            f"{child.attrs['call_name']} first wanted to help fast, but {trap.the} was risky. The story shows that rushing toward danger can make a rescue harder instead of better."
        ),
        (
            "What does the word progression mean in this story?",
            f"It means the rescue happened in a careful order: stop, think, choose help, and use the right tool. That progression turned worry into a safe plan."
        ),
        (
            f"How did {helper_name} help solve the problem?",
            f"{helper_name} stayed calm and looked closely before acting. Then {helper.pronoun()} used {tool.phrase} in the right way for {trap.the}, which let the {animal.label} get free."
        ),
    ]
    if f.get("rescued"):
        qa.append(
            (
                f"How did the story end?",
                f"The little {animal.label} got out safely and calmed down. On the walk home, {child.attrs['call_name']} understood that brave can mean thinking first and helping carefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"emergency", "hood", "problem_solving", "adult"}
    trap_id = f["trap_cfg"].id
    tool_id = f["tool_cfg"].id
    if trap_id == "drain_grate":
        tags.add("drain")
    elif trap_id == "thorn_bush":
        tags.add("thorn")
    else:
        tags.add("ditch")
    if tool_id == "umbrella_hook":
        tags.add("umbrella")
    elif tool_id == "towel":
        tags.add("towel")
    else:
        tags.add("board")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="kitten",
        trap="drain_grate",
        tool="umbrella_hook",
        helper="parent",
        child_name="Lina",
        child_gender="girl",
        coat_color="yellow",
        trait="careful",
    ),
    StoryParams(
        animal="duckling",
        trap="thorn_bush",
        tool="towel",
        helper="gardener",
        child_name="Maya",
        child_gender="girl",
        coat_color="red",
        trait="gentle",
    ),
    StoryParams(
        animal="puppy",
        trap="muddy_ditch",
        tool="board",
        helper="park_ranger",
        child_name="Theo",
        child_gender="boy",
        coat_color="blue",
        trait="bright",
    ),
    StoryParams(
        animal="kitten",
        trap="muddy_ditch",
        tool="board",
        helper="parent",
        child_name="Ruby",
        child_gender="girl",
        coat_color="green",
        trait="kind",
    ),
]


def explain_rejection(trap: Trap, tool: Tool, helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(Refusing helper '{helper.id}': this world treats that choice as too weak for a rescue. "
            f"A small emergency needs a calmer, more capable grown-up helper.)"
        )
    if tool.kind != trap.rescue_need:
        return (
            f"(No story: {tool.phrase} does not fit {trap.the}. "
            f"That place needs a tool for {trap.rescue_need}, so the rescue would not make sense.)"
        )
    if not trap_allows_helper(trap, helper):
        return (
            f"(No story: {helper.label} is not a reasonable helper for {trap.the}. "
            f"Pick a helper who fits that place and risk.)"
        )
    return "(No story: this rescue setup is not reasonable.)"


ASP_RULES = r"""
tool_fits(Tp, Tl) :- trap(Tp), tool(Tl), need(Tp, K), tool_kind(Tl, K).
helper_ok(Tp, Hp) :- allowed_helper(Tp, Hp), helper(Hp), sense(Hp, S), sense_min(M), S >= M.
valid(Tp, Tl, Hp) :- tool_fits(Tp, Tl), helper_ok(Tp, Hp).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for trap_id, trap in TRAPS.items():
        lines.append(asp.fact("trap", trap_id))
        lines.append(asp.fact("need", trap_id, trap.rescue_need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_kind", tool_id, tool.kind))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    allowed = {
        "drain_grate": ["parent", "park_ranger"],
        "thorn_bush": ["parent", "gardener"],
        "muddy_ditch": ["parent", "park_ranger"],
    }
    for trap_id, helpers in allowed.items():
        for helper_id in helpers:
            lines.append(asp.fact("allowed_helper", trap_id, helper_id))
    return "\n".join(lines)


def asp_program(show_extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show_extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if "hood" not in sample.story or "emergency" not in sample.story or "progression" not in sample.story:
            raise StoryError("Required seed words missing from default generation.")
        print("OK: default resolve/generate includes required seed words.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a child in a hood notices a small emergency and solves it step by step."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--coat-color", choices=["yellow", "red", "blue", "green", "purple"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid rescue combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trap and args.tool and args.helper:
        trap = TRAPS[args.trap]
        tool = TOOLS[args.tool]
        helper = HELPERS[args.helper]
        if not rescue_possible(trap, tool, helper):
            raise StoryError(explain_rejection(trap, tool, helper))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        trap = TRAPS[args.trap] if args.trap else next(iter(TRAPS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(trap, tool, helper))

    combos = [
        c for c in valid_combos()
        if (args.trap is None or c[0] == args.trap)
        and (args.tool is None or c[1] == args.tool)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trap_id, tool_id, helper_id = rng.choice(sorted(combos))
    animal_id = args.animal or rng.choice(sorted(ANIMALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    coat_color = args.coat_color or rng.choice(["yellow", "red", "blue", "green", "purple"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        animal=animal_id,
        trap=trap_id,
        tool=tool_id,
        helper=helper_id,
        child_name=name,
        child_gender=gender,
        coat_color=coat_color,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.trap not in TRAPS:
        raise StoryError(f"(Unknown trap: {params.trap})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    trap = TRAPS[params.trap]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if not rescue_possible(trap, tool, helper):
        raise StoryError(explain_rejection(trap, tool, helper))

    world = tell(
        animal_cfg=ANIMALS[params.animal],
        trap_cfg=trap,
        tool_cfg=tool,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        coat_color=params.coat_color,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (trap, tool, helper) combos:\n")
        for trap_id, tool_id, helper_id in combos:
            print(f"  {trap_id:12} {tool_id:14} {helper_id}")
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
            header = f"### {p.child_name}: {p.animal} at {p.trap} with {p.tool} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
