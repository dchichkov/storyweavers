#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py
=========================================================================

A standalone story world for a small rhyming quest tale: a child joins a
leprechaun, reads a clue carved in granite, and uses berry pulp to reveal the
path to a lost treasure.

The world models a simple common-sense gate: different kinds of covering on the
granite marker need different kinds of preparation before berry pulp can settle
into the carved grooves. A wrong preparation is rejected up front with a clear
reason, so the story only tells plausible versions of the quest.

Run it
------
    python storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py --goal bell --cover moss --prep brush
    python storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py --cover dew --prep feather
    python storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/leprechaun_granite_pulp_quest_rhyming_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Goal:
    id: str
    lost_item: str
    place: str
    found_text: str
    ending_image: str
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
class Cover:
    id: str
    label: str
    mantle: str
    trouble: str
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
class Prep:
    id: str
    label: str
    action_text: str
    tool_text: str
    qa_text: str
    works_on: set[str] = field(default_factory=set)
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


def _r_reveal_clue(world: World) -> list[str]:
    marker = world.get("marker")
    clue = world.get("clue")
    child = world.get("child")
    lep = world.get("leprechaun")
    if marker.meters["cleaned"] < THRESHOLD or marker.meters["pulp_in_grooves"] < THRESHOLD:
        return []
    sig = ("reveal_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["revealed"] += 1
    child.memes["hope"] += 1
    lep.memes["hope"] += 1
    return []


def _r_find_prize(world: World) -> list[str]:
    clue = world.get("clue")
    prize = world.get("prize")
    child = world.get("child")
    lep = world.get("leprechaun")
    if clue.meters["revealed"] < THRESHOLD or world.facts.get("followed_path", 0.0) < THRESHOLD:
        return []
    sig = ("find_prize",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["found"] += 1
    child.memes["joy"] += 1
    lep.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="reveal_clue", tag="physical", apply=_r_reveal_clue),
    Rule(name="find_prize", tag="quest", apply=_r_find_prize),
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
        if any(rule_id[0] == "reveal_clue" for rule_id in world.fired) and "__reveal_seen__" not in world.facts:
            changed = True
            world.facts["__reveal_seen__"] = True
        if any(rule_id[0] == "find_prize" for rule_id in world.fired) and "__find_seen__" not in world.facts:
            changed = True
            world.facts["__find_seen__"] = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def prep_works(prep: Prep, cover: Cover) -> bool:
    return cover.id in prep.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for goal_id in GOALS:
        for cover_id, cover in COVERS.items():
            for prep_id, prep in PREPS.items():
                if prep_works(prep, cover):
                    combos.append((goal_id, cover_id, prep_id))
    return combos


def explain_rejection(cover: Cover, prep: Prep) -> str:
    if cover.id == "moss":
        return (
            f"(No story: {cover.label} clings in a soft green blanket, so {prep.label} "
            f"would not clear the granite grooves well enough. Try {', '.join(sorted(p.id for p in PREPS.values() if cover.id in p.works_on))}.)"
        )
    if cover.id == "dew":
        return (
            f"(No story: {cover.label} makes the stone slick, so {prep.label} would not dry the granite enough for berry pulp to settle in the carving. "
            f"Try {', '.join(sorted(p.id for p in PREPS.values() if cover.id in p.works_on))}.)"
        )
    return (
        f"(No story: {prep.label} is not a good way to clear {cover.label} from a carved granite marker. "
        f"Try {', '.join(sorted(p.id for p in PREPS.values() if cover.id in p.works_on))}.)"
    )


def predict_reveal(world: World, prep: Prep) -> dict:
    sim = world.copy()
    do_prepare(sim, prep, narrate=False)
    do_pulp(sim, narrate=False)
    propagate(sim, narrate=False)
    return {
        "revealed": sim.get("clue").meters["revealed"] >= THRESHOLD,
        "cleaned": sim.get("marker").meters["cleaned"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, lep: Entity, goal: Goal) -> None:
    child.memes["wonder"] += 1
    lep.memes["worry"] += 1
    world.say(
        f"At the edge of Clover Glen in the gold-green light, {child.id} heard a tiny call ring clear and bright. "
        f"Upon a granite stone stood {lep.id} the leprechaun, who sighed, \"My {goal.lost_item} is lost, and my brave quest can't go on.\""
    )
    world.say(
        f"{child.id} knelt softly near the stone with sparkling eyes at dawn-bright noon, "
        f"and said, \"I'll help you search and sing; we'll find it very soon.\""
    )


def walk_to_marker(world: World, child: Entity, lep: Entity, cover: Cover) -> None:
    child.memes["trust"] += 1
    lep.memes["trust"] += 1
    world.say(
        f"Through clover curls and ferny swirls they hurried down the track, "
        f"to an old granite marker where a hidden clue slept black. "
        f"But {cover.mantle} lay over the carving, quiet, cold, and deep, "
        f"so the path they needed for the quest stayed tucked away asleep."
    )


def worry_and_plan(world: World, child: Entity, lep: Entity, prep: Prep, cover: Cover) -> None:
    pred = predict_reveal(world, prep)
    world.facts["predicted_reveal"] = pred["revealed"]
    child.memes["worry"] += 1
    lep.memes["worry"] += 1
    world.say(
        f'"If we dab on berry pulp right now, the sign may smear instead of show," '
        f"said {lep.id}. {child.id} touched the granite and whispered, \"Then first we'll clear it slow.\""
    )
    if pred["revealed"]:
        world.say(
            f"{child.id} looked at the {cover.label} and at {prep.tool_text} in hand, "
            f"and guessed the careful little fix that the clue would understand."
        )


def do_prepare(world: World, prep: Prep, narrate: bool = True) -> None:
    marker = world.get("marker")
    marker.meters["cleaned"] = 0.0
    if prep.id == "brush" and world.facts["cover"].id == "moss":
        marker.meters["cleaned"] += 1
    elif prep.id == "cloth" and world.facts["cover"].id in {"dust", "dew"}:
        marker.meters["cleaned"] += 1
    elif prep.id == "feather" and world.facts["cover"].id == "dust":
        marker.meters["cleaned"] += 1
    if narrate:
        world.say(prep.action_text)


def do_pulp(world: World, narrate: bool = True) -> None:
    marker = world.get("marker")
    child = world.get("child")
    lep = world.get("leprechaun")
    marker.meters["pulp_used"] += 1
    if marker.meters["cleaned"] >= THRESHOLD:
        marker.meters["pulp_in_grooves"] += 1
    else:
        marker.meters["smeared"] += 1
        child.memes["worry"] += 1
        lep.memes["worry"] += 1
    if narrate:
        if marker.meters["cleaned"] >= THRESHOLD:
            world.say(
                f"Then {child.id} pressed berry pulp across the granite face, rich as jam and red as a rosy trace. "
                f"The color slipped into the carved lines one by one, like little sunset rivers waking in the sun."
            )
        else:
            world.say(
                f"{child.id} pressed berry pulp on the stone, but it slid in a blur instead of a guide. "
                f"The mark looked thick and muddled there, with no neat path inside."
            )


def reveal(world: World) -> None:
    clue = world.get("clue")
    goal = world.facts["goal"]
    if clue.meters["revealed"] >= THRESHOLD:
        world.say(
            f"An arrow, a turn, and a tiny ring were etched where none had seemed to be, "
            f"and {lep.id} gave such a happy gasp that even the wrens agreed with glee. "
            f"\"The clue points straight to {goal.place}!\" {lep.id} cried with dancing feet. "
            f"Now the quest had shape and shining hope instead of puzzled defeat."
        )


def follow_path(world: World, child: Entity, lep: Entity, goal: Goal) -> None:
    world.facts["followed_path"] = 1.0
    propagate(world, narrate=False)
    if world.get("prize").meters["found"] >= THRESHOLD:
        world.say(
            f"Over roots and under fern-fringed bows they followed the granite sign, "
            f"until they reached {goal.place}, tucked cool in shade and shine."
        )
        world.say(goal.found_text)
        world.say(
            f"{lep.id} bowed low to {child.id} and laughed a silver tune, "
            f"and the whole green glen seemed glad to clap along that afternoon."
        )
        world.say(goal.ending_image)


def tell(
    goal: Goal,
    cover: Cover,
    prep: Prep,
    child_name: str = "Nora",
    child_gender: str = "girl",
    leprechaun_name: str = "Pip",
    parent_type: str = "mother",
    trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        traits=[trait],
        role="child",
    ))
    lep = world.add(Entity(
        id=leprechaun_name,
        kind="character",
        type="leprechaun",
        label="the leprechaun",
        traits=["nimble"],
        role="guide",
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="home",
    ))
    marker = world.add(Entity(
        id="marker",
        kind="thing",
        type="granite_marker",
        label="granite marker",
        attrs={"cover": cover.id},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="carving",
        label="hidden clue",
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type="lost_item",
        label=goal.lost_item,
    ))

    world.facts.update(
        goal=goal,
        cover=cover,
        prep=prep,
        child=child,
        leprechaun=lep,
        parent=parent,
        followed_path=0.0,
        predicted_reveal=False,
    )

    opening(world, child, lep, goal)
    world.para()
    walk_to_marker(world, child, lep, cover)
    worry_and_plan(world, child, lep, prep, cover)
    world.para()
    do_prepare(world, prep, narrate=True)
    do_pulp(world, narrate=True)
    propagate(world, narrate=False)
    reveal(world)
    world.para()
    follow_path(world, child, lep, goal)

    world.facts.update(
        revealed=clue.meters["revealed"] >= THRESHOLD,
        found=prize.meters["found"] >= THRESHOLD,
        cleaned=marker.meters["cleaned"] >= THRESHOLD,
    )
    return world


GOALS = {
    "bell": Goal(
        id="bell",
        lost_item="silver bell",
        place="the hollow under a fern arch",
        found_text="There, under a fern arch, lay the silver bell in a nest of clover thread, and when Pip shook it once, bright chimes skipped overhead.",
        ending_image="Home they went at sunset glow, the bell chiming light and well, and berry-stained fingers waved goodbye beside the happy bell.",
        tags={"bell", "quest"},
    ),
    "key": Goal(
        id="key",
        lost_item="clover key",
        place="a root nook behind the old ash tree",
        found_text="There, in a root nook behind the old ash tree, gleamed the clover key, green-gold and wee. Pip held it high, and the leaves all shivered as if they, too, could see.",
        ending_image="At dusk the key flashed leaf-green sparks, and the lane felt brave and new, while child and leprechaun grinned to see a hard quest tumble through.",
        tags={"key", "quest"},
    ),
    "drum": Goal(
        id="drum",
        lost_item="thimble drum",
        place="the crook of a blackberry bower",
        found_text="There, in the crook of a blackberry bower, sat the thimble drum, round and neat, and when Pip tapped its little rim, the glen woke up its feet.",
        ending_image="Back through the clover they skipped in rhyme, with a tap-tap beat and a bloom-soft hum, and the brave small quest was finished by the steady thimble drum.",
        tags={"drum", "quest"},
    ),
}

COVERS = {
    "moss": Cover(
        id="moss",
        label="moss",
        mantle="a velvet coat of moss",
        trouble="soft moss had filled the cut lines",
        tags={"moss", "granite"},
    ),
    "dust": Cover(
        id="dust",
        label="dust",
        mantle="a powdery film of dust",
        trouble="dust had drifted over the carving",
        tags={"dust", "granite"},
    ),
    "dew": Cover(
        id="dew",
        label="dew",
        mantle="a cold skin of dew",
        trouble="dew made the granite slick and shiny",
        tags={"dew", "granite"},
    ),
}

PREPS = {
    "brush": Prep(
        id="brush",
        label="a soft brush",
        action_text="So {child} drew out a soft brush of thistle fiber and swept the moss aside, slow and light, till the granite grooves could breathe in the open air and light.".replace("{child}", "{child}"),
        tool_text="a soft brush of thistle fiber",
        qa_text="brushed the moss gently away",
        works_on={"moss"},
        tags={"brush"},
    ),
    "cloth": Prep(
        id="cloth",
        label="a dry cloth",
        action_text="So {child} folded a dry cloth square and wiped the stone with care, gentle as a bedtime tuck and neat as folded air.".replace("{child}", "{child}"),
        tool_text="a dry cloth",
        qa_text="wiped the stone dry and clean",
        works_on={"dust", "dew"},
        tags={"cloth"},
    ),
    "feather": Prep(
        id="feather",
        label="a feather whisk",
        action_text="So {child} took a feather whisk and flicked the dusty gray, until the granite cuts peeked out and the loose powder danced away.".replace("{child}", "{child}"),
        tool_text="a feather whisk",
        qa_text="flicked the dust out of the grooves",
        works_on={"dust"},
        tags={"feather"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Ella", "Zoe", "Ruby", "Mae"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Owen", "Max", "Theo", "Ben", "Jack"]
LEPRECHAUN_NAMES = ["Pip", "Tansy", "Mosscap", "Brindle", "Cloverkip"]
TRAITS = ["gentle", "patient", "bright", "careful", "kind"]


@dataclass
class StoryParams:
    goal: str
    cover: str
    prep: str
    child_name: str
    child_gender: str
    leprechaun_name: str
    parent: str
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


KNOWLEDGE = {
    "leprechaun": [
        (
            "What is a leprechaun?",
            "A leprechaun is a tiny magical person from old Irish stories. In many tales, a leprechaun is clever, quick, and connected with hidden things.",
        )
    ],
    "granite": [
        (
            "What is granite?",
            "Granite is a very hard kind of rock. People use it for stones, walls, and markers because it stays strong for a long time.",
        )
    ],
    "pulp": [
        (
            "What is pulp?",
            "Pulp is the soft squishy part of fruit after it is crushed. Berry pulp can be thick and colorful, so it can leave a bright stain.",
        )
    ],
    "moss": [
        (
            "What is moss?",
            "Moss is a soft green plant that grows like a tiny carpet on damp ground, logs, and stones. It can hide cracks and carvings because it spreads over the surface.",
        )
    ],
    "dust": [
        (
            "What is dust?",
            "Dust is made of very tiny dry bits that gather on surfaces. It can blur letters or lines until you wipe or brush it away.",
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is little drops of water that rest on grass, leaves, and stones in cool air. It can make a surface slippery and shiny.",
        )
    ],
    "brush": [
        (
            "What does a brush do?",
            "A brush sweeps light things away. A soft brush can clear moss or crumbs without scratching what is underneath.",
        )
    ],
    "cloth": [
        (
            "What can a dry cloth help with?",
            "A dry cloth can wipe away water or dust. It helps make a surface clean enough to see clearly again.",
        )
    ],
    "feather": [
        (
            "Why would someone use a feather whisk?",
            "A feather whisk is very light, so it is good for flicking away loose dust. It works best when the dirt is dry and not sticky.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey to find or do something important. Stories with quests often have a goal, a problem, and a brave finish.",
        )
    ],
}
KNOWLEDGE_ORDER = ["leprechaun", "granite", "pulp", "moss", "dust", "dew", "brush", "cloth", "feather", "quest"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    lep = world.facts["leprechaun"]
    goal = world.facts["goal"]
    cover = world.facts["cover"]
    return [
        f'Write a short rhyming quest story for a 3-to-5-year-old that includes the words "leprechaun," "granite," and "pulp."',
        f"Tell a gentle story in rhyme where {child.id} helps a leprechaun named {lep.id} reveal a hidden clue on granite and recover a lost {goal.lost_item}.",
        f"Write a child-facing quest tale where berry pulp helps uncover a carving hidden under {cover.label}, and end with a joyful picture that proves the quest is done.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    lep = world.facts["leprechaun"]
    goal = world.facts["goal"]
    cover = world.facts["cover"]
    prep = world.facts["prep"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and a leprechaun named {lep.id}. They go on a quest together to find a lost {goal.lost_item}.",
        ),
        (
            f"Why couldn't {child.id} and {lep.id} read the clue at first?",
            f"They found the clue on a granite marker, but {cover.trouble}. Because the carving was covered, the path for the quest stayed hidden.",
        ),
        (
            f"How did {child.id} help reveal the clue?",
            f"{child.id} first {prep.qa_text}. Then {child.pronoun().capitalize()} pressed berry pulp over the granite so the color could settle into the carved lines and make the clue show.",
        ),
    ]
    if world.facts.get("revealed"):
        qa.append(
            (
                "Why did the berry pulp work after the stone was prepared?",
                f"It worked because the covering had been cleared away first, so the pulp could sink into the grooves instead of smearing on top. That made the hidden arrow and marks easy to see.",
            )
        )
    if world.facts.get("found"):
        qa.append(
            (
                f"How did the quest end?",
                f"They followed the clue to {goal.place} and found the lost {goal.lost_item}. The ending image shows they had really changed the day from worried and stuck to happy and complete.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"leprechaun", "granite", "pulp", "quest"}
    tags |= set(world.facts["cover"].tags)
    tags |= set(world.facts["prep"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        goal="bell",
        cover="moss",
        prep="brush",
        child_name="Nora",
        child_gender="girl",
        leprechaun_name="Pip",
        parent="mother",
        trait="gentle",
    ),
    StoryParams(
        goal="key",
        cover="dust",
        prep="feather",
        child_name="Finn",
        child_gender="boy",
        leprechaun_name="Tansy",
        parent="father",
        trait="bright",
    ),
    StoryParams(
        goal="drum",
        cover="dew",
        prep="cloth",
        child_name="Ella",
        child_gender="girl",
        leprechaun_name="Mosscap",
        parent="mother",
        trait="patient",
    ),
]


ASP_RULES = r"""
valid(G,C,P) :- goal(G), cover(C), prep(P), works(P,C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for cover_id in COVERS:
        lines.append(asp.fact("cover", cover_id))
    for prep_id, prep in PREPS.items():
        lines.append(asp.fact("prep", prep_id))
        for cover_id in sorted(prep.works_on):
            lines.append(asp.fact("works", prep_id, cover_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"Generated empty story for seed {seed}.")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED for seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a rhyming quest with a leprechaun, granite, and berry pulp."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--prep", choices=PREPS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--leprechaun-name", choices=LEPRECHAUN_NAMES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cover and args.prep:
        cover = COVERS[args.cover]
        prep = PREPS[args.prep]
        if not prep_works(prep, cover):
            raise StoryError(explain_rejection(cover, prep))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.cover is None or combo[1] == args.cover)
        and (args.prep is None or combo[2] == args.prep)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, cover_id, prep_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    leprechaun_name = args.leprechaun_name or rng.choice(LEPRECHAUN_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        goal=goal_id,
        cover=cover_id,
        prep=prep_id,
        child_name=child_name,
        child_gender=child_gender,
        leprechaun_name=leprechaun_name,
        parent=parent,
        trait=trait,
    )


def _render_prep_text(text: str, child_name: str) -> str:
    return text.replace("{child}", child_name)


def generate(params: StoryParams) -> StorySample:
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover: {params.cover})")
    if params.prep not in PREPS:
        raise StoryError(f"(Unknown prep: {params.prep})")

    goal = GOALS[params.goal]
    cover = COVERS[params.cover]
    prep = PREPS[params.prep]
    if not prep_works(prep, cover):
        raise StoryError(explain_rejection(cover, prep))

    prep_cfg = Prep(
        id=prep.id,
        label=prep.label,
        action_text=_render_prep_text(prep.action_text, params.child_name),
        tool_text=prep.tool_text,
        qa_text=prep.qa_text,
        works_on=set(prep.works_on),
        tags=set(prep.tags),
    )

    world = tell(
        goal=goal,
        cover=cover,
        prep=prep_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        leprechaun_name=params.leprechaun_name,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (goal, cover, prep) combos:\n")
        for goal, cover, prep in combos:
            print(f"  {goal:6} {cover:5} {prep}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} & {p.leprechaun_name}: {p.goal} / {p.cover} / {p.prep}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
