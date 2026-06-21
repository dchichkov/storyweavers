#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py

A standalone story world for a tiny rhyming tale about a child hearing a
mysterious repeated sound -- "sic-sic, sic-sic" -- and learning that a shy
little creature comes closer with gentle sounds, not booming ones.

The world model tracks a shy hidden creature, the noise a child makes while
searching, and the softer plan that finally works. The ending always includes a
surprise reveal explaining the mystery sound.

Run it
------
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py --place garden --creature snail --lure lettuce
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py --place pond --creature hedgehog
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py --asp
python storyworlds/worlds/gpt-5.4/sic_repetition_sound_effects_surprise_rhyming_story.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Place:
    id: str
    label: str
    path: str
    hiding_spot: str
    echo_line: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Creature:
    id: str
    label: str
    article: str
    bravery: int
    likes: set[str]
    shuffle: str
    surprise_item: str
    reveal_line: str
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
class Lure:
    id: str
    label: str
    phrase: str
    smell: str
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
class Tool:
    id: str
    label: str
    sound: str
    repeat_line: str
    loudness: int
    gentle: bool
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    room = world.get("place")
    if creature.attrs.get("hidden", True) and room.meters["noise"] >= creature.attrs["bravery"]:
        sig = ("scare", int(room.meters["noise"]))
        if sig not in world.fired:
            world.fired.add(sig)
            creature.memes["fear"] += 1
            creature.memes["trust"] = 0.0
            out.append("__scared__")
    return out


def _r_invite(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    room = world.get("place")
    if not creature.attrs.get("hidden", True):
        return out
    if world.facts.get("lure_id") not in creature.attrs.get("likes", set()):
        return out
    if not world.facts.get("soft_plan", False):
        return out
    if room.meters["noise"] > creature.attrs["bravery"]:
        return out
    sig = ("invite", world.facts.get("lure_id"), int(room.meters["noise"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["curiosity"] += 1
    creature.memes["trust"] += 1
    creature.attrs["hidden"] = False
    out.append("__emerge__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    helper = world.get("helper")
    if creature.attrs.get("hidden", True):
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    helper.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scare", tag="emotional", apply=_r_scare),
    Rule(name="invite", tag="social", apply=_r_invite),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden path",
        path="the stone garden path",
        hiding_spot="under the mint leaves by the path",
        echo_line="The stones made every tiny scrape skip and slip in the air.",
        affords={"snail", "hedgehog"},
    ),
    "porch": Place(
        id="porch",
        label="the sunny porch",
        path="the wooden porch boards",
        hiding_spot="behind a striped flowerpot",
        echo_line="The boards held little sounds and sent them back again.",
        affords={"snail", "duckling"},
    ),
    "pond": Place(
        id="pond",
        label="the pond edge",
        path="the flat stones by the pond",
        hiding_spot="behind the reeds near the water",
        echo_line="The water answered little noises with a silver shimmer.",
        affords={"duckling", "snail"},
    ),
}

CREATURES = {
    "snail": Creature(
        id="snail",
        label="snail",
        article="a",
        bravery=2,
        likes={"lettuce", "apple"},
        shuffle="slid",
        surprise_item="a tiny silver thimble tied behind its shell",
        reveal_line="The little thimble bumped the stones and made the soft sic-sic sound.",
        tags={"snail", "gentle", "surprise"},
    ),
    "duckling": Creature(
        id="duckling",
        label="duckling",
        article="a",
        bravery=3,
        likes={"oats", "apple"},
        shuffle="paddled",
        surprise_item="a shiny bottle cap looped on a ribbon at its foot",
        reveal_line="The bottle cap kissed the stones and made the bright sic-sic sound.",
        tags={"duckling", "pond", "surprise"},
    ),
    "hedgehog": Creature(
        id="hedgehog",
        label="hedgehog",
        article="a",
        bravery=2,
        likes={"apple"},
        shuffle="tiptoed",
        surprise_item="a smooth bead rolling on a bit of string beside its paw",
        reveal_line="The bead skimmed the path and made the neat sic-sic sound.",
        tags={"hedgehog", "garden", "surprise"},
    ),
}

LURES = {
    "lettuce": Lure(
        id="lettuce",
        label="lettuce leaf",
        phrase="a curly lettuce leaf",
        smell="green and cool",
        tags={"lettuce", "food"},
    ),
    "apple": Lure(
        id="apple",
        label="apple slice",
        phrase="a sweet apple slice",
        smell="sweet as sun-warm jam",
        tags={"apple", "food"},
    ),
    "oats": Lure(
        id="oats",
        label="oat crumbs",
        phrase="a little sprinkle of oat crumbs",
        smell="soft and toasty",
        tags={"oats", "food"},
    ),
}

TOOLS = {
    "drum": Tool(
        id="drum",
        label="tin drum",
        sound="boom-boom",
        repeat_line="Boom-boom, boom-boom!",
        loudness=4,
        gentle=False,
        tags={"drum", "loud"},
    ),
    "pan": Tool(
        id="pan",
        label="pan and spoon",
        sound="clang-clang",
        repeat_line="Clang-clang, clang-clang!",
        loudness=5,
        gentle=False,
        tags={"pan", "loud"},
    ),
    "bell": Tool(
        id="bell",
        label="little bell",
        sound="ting-ting",
        repeat_line="Ting-ting, ting-ting!",
        loudness=2,
        gentle=True,
        tags={"bell", "gentle"},
    ),
    "shaker": Tool(
        id="shaker",
        label="seed shaker",
        sound="shh-shh",
        repeat_line="Shh-shh, shh-shh!",
        loudness=1,
        gentle=True,
        tags={"shaker", "gentle"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ella", "Ivy", "Ruby", "Tess"]
BOY_NAMES = ["Ben", "Leo", "Owen", "Max", "Finn", "Theo", "Sam", "Eli"]
TRAITS = ["curious", "careful", "bouncy", "kind", "eager", "thoughtful"]


def place_supports(place: Place, creature: Creature) -> bool:
    return creature.id in place.affords


def lure_matches(creature: Creature, lure: Lure) -> bool:
    return lure.id in creature.likes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            if not place_supports(place, creature):
                continue
            for lure_id, lure in LURES.items():
                if lure_matches(creature, lure):
                    combos.append((place_id, creature_id, lure_id))
    return combos


def explain_rejection(place: Place, creature: Creature, lure: Lure) -> str:
    if not place_supports(place, creature):
        return (
            f"(No story: {creature.article} {creature.label} does not belong at {place.label} "
            f"in this tiny world, so the hiding-and-reveal plot would not make sense there.)"
        )
    return (
        f"(No story: {creature.article} {creature.label} would not come for {lure.phrase}. "
        f"Pick a lure it actually likes so the gentle plan can honestly work.)"
    )


def predict_with_tool(world: World, tool: Tool) -> dict:
    sim = world.copy()
    place = sim.get("place")
    place.meters["noise"] += tool.loudness
    markers = propagate(sim, narrate=False)
    creature = sim.get("creature")
    return {
        "scared": "__scared__" in markers or creature.memes["fear"] >= THRESHOLD,
        "hidden": creature.attrs.get("hidden", True),
        "noise": int(place.meters["noise"]),
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    trait = child.attrs.get("trait", "curious")
    world.say(
        f"One bright day, {child.id} skipped to {place.label}, a {trait} little {child.type} with a listening ear."
    )
    world.say(
        f"From {place.hiding_spot} came a whispery scrape: 'sic-sic, sic-sic,' soft and near."
    )
    world.say(place.echo_line)


def wonder(world: World, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'"Sic-sic, sic-sic! What can it be? A shy small singer? A wheel no one can see?" {child.id} said.'
    )


def try_loud_call(world: World, child: Entity, tool: Tool) -> None:
    place = world.get("place")
    place.meters["noise"] += tool.loudness
    child.memes["effort"] += 1
    world.facts["first_tool"] = tool.id
    world.say(
        f"So {child.id} lifted a {tool.label} and called in a rhyme, "
        f'"{tool.repeat_line} Come out, little friend, this is playtime!"'
    )
    markers = propagate(world, narrate=False)
    creature = world.get("creature")
    if "__scared__" in markers or creature.memes["fear"] >= THRESHOLD:
        world.say(
            f"But the hiding place tucked in tighter. The mysterious 'sic-sic' stopped, and even the leaves kept still."
        )
    else:
        world.say(
            f"The sound answered once, then hushed again, as if the hidden friend was thinking hard."
        )


def helper_warn(world: World, helper: Entity, child: Entity, loud_tool: Tool, soft_tool: Tool, lure: Lure) -> None:
    pred = predict_with_tool(world, loud_tool)
    world.facts["predicted_noise"] = pred["noise"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id}. "{loud_tool.label.capitalize()} sounds are brave and grand," '
        f'{helper.pronoun()} said, "but for a shy little heart they can feel too big."'
    )
    world.say(
        f'"Let us try {soft_tool.repeat_line.lower()} with {lure.phrase}. Soft steps, soft sounds, and maybe soft surprise."'
    )


def gentle_plan(world: World, child: Entity, helper: Entity, soft_tool: Tool, lure: Lure) -> None:
    place = world.get("place")
    creature = world.get("creature")
    place.meters["noise"] = float(soft_tool.loudness)
    world.facts["lure_id"] = lure.id
    world.facts["soft_plan"] = True
    child.memes["patience"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"They set down {lure.phrase}, {lure.smell} in the air, and {child.id} tried again with a {soft_tool.label}: "
        f'"{soft_tool.repeat_line} If you are kind and small, you may come after all."'
    )
    markers = propagate(world, narrate=False)
    if "__emerge__" in markers or not creature.attrs.get("hidden", True):
        world.say(
            f"A leaf gave a twitch. A shadow gave a wiggle. Something tiny began to move from the hiding place."
        )
    else:
        world.say(
            "The place stayed quiet, and the gentle plan did not bloom into a meeting."
        )


def reveal(world: World, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    child = world.get("child")
    if creature.attrs.get("hidden", True):
        raise StoryError("The gentle plan failed to reveal the hidden creature.")
    world.say(
        f"Out {creature_cfg.shuffle} {creature_cfg.article} {creature_cfg.label}, carrying {creature_cfg.surprise_item}."
    )
    world.say(creature_cfg.reveal_line)
    world.say(
        f'{child.id} laughed. "So that was the secret beat -- not scary at all, just small and sweet!"'
    )


def closing(world: World, child: Entity, helper: Entity, soft_tool: Tool, lure: Lure, creature_cfg: Creature) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled, and {child.id} rang the {soft_tool.label} once more -- gentle, not sore."
    )
    world.say(
        f"Now the little {creature_cfg.label} stayed nearby for a crumb and a peep, while the last 'sic-sic' skipped light on the path."
    )
    world.say(
        f"And {child.id} learned a rhyme to keep: big bangs make shy feet hide, but soft songs bring soft friends outside."
    )


def tell(
    place: Place,
    creature_cfg: Creature,
    lure: Lure,
    loud_tool: Tool,
    soft_tool: Tool,
    child_name: str = "Mia",
    child_type: str = "girl",
    helper_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place.label,
            role="place",
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="character",
            type="creature",
            label=creature_cfg.label,
            role="creature",
            attrs={
                "hidden": True,
                "bravery": creature_cfg.bravery,
                "likes": set(creature_cfg.likes),
            },
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        place_cfg=place,
        creature_cfg=creature_cfg,
        lure_cfg=lure,
        loud_tool_cfg=loud_tool,
        soft_tool_cfg=soft_tool,
        lure_id="",
        soft_plan=False,
    )

    introduce(world, child, place)
    wonder(world, child)

    world.para()
    try_loud_call(world, child, loud_tool)
    helper_warn(world, helper, child, loud_tool, soft_tool, lure)

    world.para()
    gentle_plan(world, child, helper, soft_tool, lure)
    reveal(world, creature_cfg)
    closing(world, child, helper, soft_tool, lure, creature_cfg)

    world.facts.update(
        revealed=not creature.attrs.get("hidden", True),
        scared=creature.memes["fear"] >= THRESHOLD,
        trust=creature.memes["trust"],
        outcome="revealed" if not creature.attrs.get("hidden", True) else "hidden",
    )
    return world


@dataclass
class StoryParams:
    place: str
    creature: str
    lure: str
    loud_tool: str
    soft_tool: str
    child_name: str
    child_type: str
    helper_type: str
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
    "snail": [
        (
            "Why do snails move slowly?",
            "Snails move with a soft, stretchy foot under their bodies. That gentle sliding motion is safe and steady, but it is not fast.",
        )
    ],
    "duckling": [
        (
            "What is a duckling?",
            "A duckling is a baby duck. Ducklings are fluffy, small, and often stay close to water and to grown-up ducks.",
        )
    ],
    "hedgehog": [
        (
            "What is a hedgehog?",
            "A hedgehog is a small animal with many prickly spines on its back. It can curl up when it feels scared.",
        )
    ],
    "gentle": [
        (
            "Why do gentle sounds help with shy animals?",
            "Shy animals often feel safer when the world is quiet. Loud crashes can sound like danger, but soft sounds give them time to look and listen.",
        )
    ],
    "drum": [
        (
            "What does a drum sound like?",
            "A drum can sound like boom-boom when you tap it. Big drum sounds travel far and can feel exciting and loud.",
        )
    ],
    "pan": [
        (
            "Why can banging a pan be too loud?",
            "Metal pans can make sharp clang-clang noises. Those noises can surprise little ears and make shy creatures want to hide.",
        )
    ],
    "bell": [
        (
            "What does a little bell do?",
            "A little bell makes a lighter ting-ting sound. It can be easier for a shy listener to hear without feeling startled.",
        )
    ],
    "shaker": [
        (
            "What is a seed shaker?",
            "A shaker is a small object that makes a soft shh-shh sound when you move it. Soft sounds are often calmer than bangs.",
        )
    ],
    "apple": [
        (
            "Why do some animals like apple pieces?",
            "Apple pieces can smell sweet and fresh. In small safe amounts, that sweet smell can help some little creatures come closer.",
        )
    ],
    "lettuce": [
        (
            "Why might a snail like lettuce?",
            "Lettuce is soft and full of water. That makes it easy for a snail to nibble.",
        )
    ],
    "oats": [
        (
            "What are oat crumbs?",
            "Oats are small grains people often eat as porridge or cereal. A few tiny crumbs can smell warm and toasty.",
        )
    ],
    "surprise": [
        (
            "What is a surprise in a story?",
            "A surprise is something you did not expect at first. It makes the ending feel fresh when the story suddenly explains a mystery.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "snail",
    "duckling",
    "hedgehog",
    "gentle",
    "drum",
    "pan",
    "bell",
    "shaker",
    "apple",
    "lettuce",
    "oats",
    "surprise",
]


CURATED = [
    StoryParams(
        place="garden",
        creature="snail",
        lure="lettuce",
        loud_tool="drum",
        soft_tool="bell",
        child_name="Mia",
        child_type="girl",
        helper_type="mother",
        trait="curious",
    ),
    StoryParams(
        place="porch",
        creature="duckling",
        lure="oats",
        loud_tool="pan",
        soft_tool="shaker",
        child_name="Leo",
        child_type="boy",
        helper_type="father",
        trait="eager",
    ),
    StoryParams(
        place="garden",
        creature="hedgehog",
        lure="apple",
        loud_tool="drum",
        soft_tool="bell",
        child_name="Ruby",
        child_type="girl",
        helper_type="mother",
        trait="kind",
    ),
    StoryParams(
        place="pond",
        creature="snail",
        lure="apple",
        loud_tool="pan",
        soft_tool="shaker",
        child_name="Theo",
        child_type="boy",
        helper_type="father",
        trait="thoughtful",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature = f["creature_cfg"]
    place = f["place_cfg"]
    loud_tool = f["loud_tool_cfg"]
    soft_tool = f["soft_tool_cfg"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "sic" and uses repetition, sound effects, and a surprise reveal.',
        f"Tell a rhyming story where {child.id} hears 'sic-sic, sic-sic' at {place.label}, first tries a {loud_tool.label}, and then uses a gentler {soft_tool.label} to meet a shy {creature.label}.",
        "Write a child-facing story with repeated sounds like boom-boom or ting-ting, where the ending explains a mystery in a sweet surprising way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    creature = f["creature_cfg"]
    lure = f["lure_cfg"]
    loud_tool = f["loud_tool_cfg"]
    soft_tool = f["soft_tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What sound did the child hear at the beginning?",
            "The child heard a repeated 'sic-sic, sic-sic' coming from the hiding place. That strange little sound is what started the whole search.",
        ),
        (
            f"Why did the first plan with the {loud_tool.label} not work?",
            f"It was too loud for the shy {creature.label}, so the hidden creature stayed tucked away. In this story, big banging sounds felt scary instead of friendly.",
        ),
        (
            f"How did {helper.label_word} help?",
            f"{helper.label_word.capitalize()} suggested a softer plan instead of more banging. {helper.pronoun().capitalize()} paired {soft_tool.label} sounds with {lure.phrase}, because gentle sounds and a matching treat gave the creature a reason to trust.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that the mystery sound came from a real little {creature.label} carrying {creature.surprise_item}. When it moved, that tiny object made the soft sic-sic sound.",
        ),
        (
            "How did the story end?",
            f"It ended with the shy creature staying nearby while the child used a gentler sound. The ending proves the child changed from making big noise to making kind noise.",
        ),
    ]
    if f.get("revealed"):
        qa.append(
            (
                f"Where was the creature hiding?",
                f"It was hiding at {place.hiding_spot}. That quiet spot let the little creature listen first before it decided to come out.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["creature_cfg"].tags)
    tags |= set(f["loud_tool_cfg"].tags)
    tags |= set(f["soft_tool_cfg"].tags)
    tags |= set(f["lure_cfg"].tags)
    tags.add("surprise")
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
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supported(P, C) :- place(P), creature(C), affords(P, C).
liked(C, L) :- creature(C), lure(L), likes(C, L).
valid(P, C, L) :- supported(P, C), liked(C, L).

too_loud(C, T) :- creature(C), tool(T), bravery(C, B), loudness(T, N), N > B.
calm_enough(C, T) :- creature(C), tool(T), bravery(C, B), loudness(T, N), N <= B.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for creature_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, creature_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("bravery", creature_id, creature.bravery))
        for lure_id in sorted(creature.likes):
            lines.append(asp.fact("likes", creature_id, lure_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("loudness", tool_id, tool.loudness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_tool_relations() -> tuple[set[tuple], set[tuple]]:
    import asp

    model = asp.one_model(asp_program("", "#show too_loud/2.\n#show calm_enough/2."))
    return set(asp.atoms(model, "too_loud")), set(asp.atoms(model, "calm_enough"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_too_loud: set[tuple[str, str]] = set()
    py_calm: set[tuple[str, str]] = set()
    for creature_id, creature in CREATURES.items():
        for tool_id, tool in TOOLS.items():
            if tool.loudness > creature.bravery:
                py_too_loud.add((creature_id, tool_id))
            else:
                py_calm.add((creature_id, tool_id))
    asp_too_loud, asp_calm = asp_tool_relations()
    if py_too_loud == asp_too_loud and py_calm == asp_calm:
        print("OK: tool loudness relations match.")
    else:
        rc = 1
        print("MISMATCH in tool loudness relations.")
        if asp_too_loud - py_too_loud:
            print("  too_loud only in clingo:", sorted(asp_too_loud - py_too_loud))
        if py_too_loud - asp_too_loud:
            print("  too_loud only in python:", sorted(py_too_loud - asp_too_loud))
        if asp_calm - py_calm:
            print("  calm_enough only in clingo:", sorted(asp_calm - py_calm))
        if py_calm - asp_calm:
            print("  calm_enough only in python:", sorted(py_calm - asp_calm))

    try:
        smoke = generate(CURATED[0])
        if "sic" not in smoke.story.lower():
            raise StoryError("Smoke test story did not include the required word 'sic'.")
        if not smoke.story or smoke.world is None:
            raise StoryError("Smoke test generation produced an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a child hears 'sic-sic' and learns that soft sounds invite shy friends."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--loud-tool", choices=[k for k, v in TOOLS.items() if not v.gentle], dest="loud_tool")
    ap.add_argument("--soft-tool", choices=[k for k, v in TOOLS.items() if v.gentle], dest="soft_tool")
    ap.add_argument("--helper", choices=["mother", "father"], dest="helper_type")
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", choices=["girl", "boy"], dest="child_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, creature, lure) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and inline rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and not place_supports(PLACES[args.place], CREATURES[args.creature]):
        lure_id = args.lure or next(iter(CREATURES[args.creature].likes))
        raise StoryError(explain_rejection(PLACES[args.place], CREATURES[args.creature], LURES[lure_id]))
    if args.creature and args.lure and not lure_matches(CREATURES[args.creature], LURES[args.lure]):
        place_id = args.place or next(pid for pid, pl in PLACES.items() if args.creature in pl.affords)
        raise StoryError(explain_rejection(PLACES[place_id], CREATURES[args.creature], LURES[args.lure]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.lure is None or combo[2] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, lure_id = rng.choice(sorted(combos))
    loud_choices = sorted(k for k, tool in TOOLS.items() if not tool.gentle)
    soft_choices = sorted(k for k, tool in TOOLS.items() if tool.gentle)

    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    loud_tool = args.loud_tool or rng.choice(loud_choices)
    soft_tool = args.soft_tool or rng.choice(soft_choices)

    return StoryParams(
        place=place_id,
        creature=creature_id,
        lure=lure_id,
        loud_tool=loud_tool,
        soft_tool=soft_tool,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        creature = CREATURES[params.creature]
        lure = LURES[params.lure]
        loud_tool = TOOLS[params.loud_tool]
        soft_tool = TOOLS[params.soft_tool]
    except KeyError as err:
        raise StoryError(f"Unknown parameter value: {err}") from None

    if loud_tool.gentle:
        raise StoryError("(No story: the first tool must be a louder try, not a gentle one.)")
    if not soft_tool.gentle:
        raise StoryError("(No story: the second tool must be gentle enough for the shy reveal.)")
    if not place_supports(place, creature) or not lure_matches(creature, lure):
        raise StoryError(explain_rejection(place, creature, lure))

    world = tell(
        place=place,
        creature_cfg=creature,
        lure=lure,
        loud_tool=loud_tool,
        soft_tool=soft_tool,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show too_loud/2.\n#show calm_enough/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, lure) combos:\n")
        for place_id, creature_id, lure_id in combos:
            print(f"  {place_id:8} {creature_id:10} {lure_id}")
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
            header = f"### {p.child_name}: {p.creature} at {p.place} with {p.lure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
