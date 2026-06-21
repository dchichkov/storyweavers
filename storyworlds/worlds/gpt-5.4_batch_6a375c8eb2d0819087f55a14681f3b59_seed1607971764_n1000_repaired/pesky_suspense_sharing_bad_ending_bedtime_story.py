#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py
==============================================================================

A standalone story world about a bedtime mystery: a child hears a pesky sound in
the dark, must decide whether to share the one helpful bedtime tool, and learns
what changes when fear is faced together versus alone.

The world is tuned for:
- the word "pesky"
- suspense
- sharing
- a possible bad ending
- a soft bedtime-story voice

Run it
------
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py --noise crinkle --item lantern --choice share
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py --item pillow   # rejected: not enough help for the mystery
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pesky_suspense_sharing_bad_ending_bedtime_story.py --verify
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
    gives_light: bool = False
    gives_comfort: bool = False
    tiny: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
class Noise:
    id: str
    sound: str
    source: str
    spot: str
    reveal: str
    danger: int
    tiny_kind: str
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
class SharedItem:
    id: str
    label: str
    phrase: str
    beam: str
    comfort_line: str
    help: int
    light: bool = False
    comfort: bool = False
    plural: bool = False
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
class Choice:
    id: str
    shares: bool
    together: bool
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "waiter"}]

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


def _r_lonely_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["darkness"] < THRESHOLD:
        return out
    for kid in world.kids():
        alone = kid.attrs.get("alone", False)
        if not alone:
            continue
        sig = ("lonely_fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_shared_bravery(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    waiter = world.get("waiter")
    item = world.get("item")
    if holder.attrs.get("shared", False) and item.meters["active"] >= THRESHOLD:
        sig = ("shared_bravery",)
        if sig not in world.fired:
            world.fired.add(sig)
            holder.memes["care"] += 1
            waiter.memes["relief"] += 1
            holder.memes["bravery"] += 1
            waiter.memes["bravery"] += 1
            out.append("__share__")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.get("mystery")
    item = world.get("item")
    holder = world.get("holder")
    waiter = world.get("waiter")
    together = holder.attrs.get("with_friend", False) and waiter.attrs.get("with_friend", False)
    if item.meters["help_power"] >= mystery.meters["need"] and together:
        sig = ("solved",)
        if sig not in world.fired:
            world.fired.add(sig)
            mystery.meters["solved"] += 1
            holder.memes["fear"] = 0.0
            waiter.memes["fear"] = 0.0
            holder.memes["relief"] += 1
            waiter.memes["relief"] += 1
            out.append("__solved__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="lonely_fear", tag="emotion", apply=_r_lonely_fear),
    Rule(name="shared_bravery", tag="social", apply=_r_shared_bravery),
    Rule(name="solved", tag="resolution", apply=_r_solved),
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


def item_works(item: SharedItem, noise: Noise) -> bool:
    return item.help >= max(HELP_MIN, noise.danger)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for noise_id, noise in NOISES.items():
        for item_id, item in ITEMS.items():
            for choice_id in CHOICES:
                if item_works(item, noise):
                    combos.append((noise_id, item_id, choice_id))
    return combos


@dataclass
class StoryParams:
    noise: str
    item: str
    choice: str
    holder_name: str
    holder_gender: str
    waiter_name: str
    waiter_gender: str
    parent: str
    holder_trait: str
    waiter_trait: str
    relationship: str = "siblings"
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


def predict_outcome(noise: Noise, item: SharedItem, choice: Choice) -> str:
    if not item_works(item, noise):
        return "bad"
    return "good" if (choice.shares and choice.together) else "bad"


def introduce(world: World, holder: Entity, waiter: Entity, item: SharedItem) -> None:
    room = world.get("room")
    room.meters["darkness"] = 1.0
    holder.memes["sleepy"] += 1
    waiter.memes["sleepy"] += 1
    item_ent = world.get("item")
    item_ent.meters["help_power"] = float(item.help)
    item_ent.meters["active"] = 1.0
    world.say(
        f"In a quiet room at bedtime, {holder.id} and {waiter.id} lay under their blankets "
        f"while the moon painted a pale square on the floor."
    )
    world.say(
        f"Between them rested {item.phrase}, ready to {item.beam} if anyone needed courage."
    )


def stir_suspense(world: World, holder: Entity, waiter: Entity, noise: Noise) -> None:
    mystery = world.get("mystery")
    mystery.meters["need"] = float(max(HELP_MIN, noise.danger))
    waiter.memes["fear"] += 1
    holder.memes["wonder"] += 1
    world.say(
        f"Then a pesky {noise.sound} came from {noise.spot}. It happened once, then stopped, "
        f"and for a moment the whole room seemed to listen."
    )
    world.say(
        f'"Did you hear that?" whispered {waiter.id}. {holder.id} listened too, and the soft dark '
        f"felt suddenly full of secrets."
    )


def ask_to_share(world: World, holder: Entity, waiter: Entity, item: SharedItem) -> None:
    world.say(
        f'"Can we use {item.phrase} together?" {waiter.id} asked. "{item.comfort_line}"'
    )


def choose_share(world: World, holder: Entity, waiter: Entity, item: SharedItem, choice: Choice) -> None:
    holder.attrs["shared"] = choice.shares
    holder.attrs["with_friend"] = choice.together
    waiter.attrs["with_friend"] = choice.together
    holder.attrs["alone"] = not choice.together
    waiter.attrs["alone"] = not choice.together
    if choice.shares:
        holder.memes["generosity"] += 1
        world.say(
            f'{holder.id} nodded and moved over. "{item.label.capitalize()} is better when we share it," '
            f"{holder.pronoun()} said."
        )
        world.say(
            f"Together they held {item.phrase}, and its gentle glow reached both pillows."
        )
    else:
        holder.memes["selfishness"] += 1
        waiter.memes["hurt"] += 1
        world.say(
            f'{holder.id} hugged {item.phrase} close. "No. It is mine tonight," {holder.pronoun()} said.'
        )
        world.say(
            f"{waiter.id} stayed in the dim side of the room while {holder.id} kept the only helpful thing."
        )
    propagate(world, narrate=False)


def investigate(world: World, holder: Entity, waiter: Entity, noise: Noise, item: SharedItem, choice: Choice) -> None:
    if choice.together:
        world.say(
            f"Step by step, they padded across the rug toward {noise.spot}, listening to the pesky sound."
        )
    else:
        world.say(
            f"{holder.id} crept alone toward {noise.spot} while {waiter.id} stayed in bed, listening and worrying."
        )
    if choice.shares and choice.together:
        world.say(
            f"The beam did not chase the dark away all at once, but it made a small brave path in front of them."
        )
    else:
        propagate(world, narrate=False)
        world.say(
            f"Without warm company beside {holder.pronoun('object')}, every tiny rustle sounded bigger than before."
        )


def reveal_good(world: World, holder: Entity, waiter: Entity, noise: Noise) -> None:
    mystery = world.get("mystery")
    tiny = world.get("tiny")
    mystery.meters["solved"] = 1.0
    tiny.meters["found"] = 1.0
    holder.memes["care"] += 1
    waiter.memes["care"] += 1
    world.say(
        f"At last the light found the trouble: {noise.reveal}. {noise.source.capitalize()} looked more bothered than scary."
    )
    world.say(
        f"{holder.id} and {waiter.id} worked together to help {tiny.label}, and soon the room was quiet again."
    )


def settle_good(world: World, holder: Entity, waiter: Entity, parent: Entity, item: SharedItem) -> None:
    holder.memes["sleepy"] += 1
    waiter.memes["sleepy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came to the doorway, smiled at the peaceful room, and tucked the blankets back around them.'
    )
    world.say(
        f'"You were brave because you stayed kind," {parent.pronoun()} said softly. '
        f"With {item.phrase} between them, both children drifted toward sleep."
    )


def reveal_bad(world: World, holder: Entity, waiter: Entity, noise: Noise, item: SharedItem) -> None:
    room = world.get("room")
    holder.memes["fear"] += 1
    waiter.memes["fear"] += 1
    room.meters["darkness"] += 1
    world.say(
        f"Then the pesky {noise.sound} came again, sharper this time, and {holder.id} jumped so hard that {item.phrase} slipped."
    )
    world.say(
        f"It thumped under the bed, and the room turned darker than before. Nobody could see what had been making the sound."
    )


def settle_bad(world: World, holder: Entity, waiter: Entity, parent: Entity) -> None:
    holder.memes["regret"] += 1
    waiter.memes["sadness"] += 1
    world.say(
        f"{waiter.id} began to cry, and soon {holder.id} did too. {parent.label_word.capitalize()} hurried in, "
        f"but the little mystery was still hidden and the room no longer felt cozy."
    )
    world.say(
        f"That night they fell asleep late, sniffling in the dark, wishing they had stayed together and shared."
    )


def tell(
    noise: Noise,
    item: SharedItem,
    choice: Choice,
    holder_name: str,
    holder_gender: str,
    waiter_name: str,
    waiter_gender: str,
    parent_type: str,
    holder_trait: str,
    waiter_trait: str,
    relationship: str,
) -> World:
    world = World()
    holder = world.add(Entity(
        id=holder_name,
        kind="character",
        type=holder_gender,
        role="holder",
        traits=[holder_trait],
        attrs={"shared": False, "with_friend": False, "alone": False, "relationship": relationship},
    ))
    waiter = world.add(Entity(
        id=waiter_name,
        kind="character",
        type=waiter_gender,
        role="waiter",
        traits=[waiter_trait],
        attrs={"with_friend": False, "alone": False, "relationship": relationship},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="bedroom"))
    world.add(Entity(
        id="item",
        type="tool",
        label=item.label,
        gives_light=item.light,
        gives_comfort=item.comfort,
    ))
    world.add(Entity(id="mystery", type="mystery", label="the mystery"))
    world.add(Entity(id="tiny", type=noise.tiny_kind, label=noise.source, tiny=True))

    introduce(world, holder, waiter, item)
    stir_suspense(world, holder, waiter, noise)
    world.para()
    ask_to_share(world, holder, waiter, item)
    choose_share(world, holder, waiter, item, choice)
    world.para()
    investigate(world, holder, waiter, noise, item, choice)

    outcome = predict_outcome(noise, item, choice)
    if outcome == "good":
        propagate(world, narrate=False)
        reveal_good(world, holder, waiter, noise)
        world.para()
        settle_good(world, holder, waiter, parent, item)
    else:
        reveal_bad(world, holder, waiter, noise, item)
        world.para()
        settle_bad(world, holder, waiter, parent)

    world.facts.update(
        holder=holder,
        waiter=waiter,
        parent=parent,
        noise=noise,
        item_cfg=item,
        choice=choice,
        relationship=relationship,
        outcome=outcome,
        mystery_solved=world.get("mystery").meters["solved"] >= THRESHOLD,
        shared=choice.shares,
        together=choice.together,
    )
    return world


NOISES = {
    "scratch": Noise(
        id="scratch",
        sound="scratch-scratch",
        source="a tiny mouse tangled in a paper crown",
        spot="the toy chest",
        reveal="a tiny mouse was caught in a paper crown from yesterday's game",
        danger=2,
        tiny_kind="mouse",
        tags={"mouse", "bedtime", "mystery"},
    ),
    "crinkle": Noise(
        id="crinkle",
        sound="crinkle-crinkle",
        source="a kitten trapped inside a crinkly gift bag",
        spot="the curtain by the rocking chair",
        reveal="a kitten had backed into a crinkly gift bag and could not turn around",
        danger=2,
        tiny_kind="kitten",
        tags={"kitten", "bedtime", "mystery"},
    ),
    "tap": Noise(
        id="tap",
        sound="tap... tap... tap",
        source="a pet turtle nudging a wooden block",
        spot="the shelf near the books",
        reveal="a pet turtle was nudging a wooden block against the shelf",
        danger=2,
        tiny_kind="turtle",
        tags={"turtle", "bedtime", "mystery"},
    ),
}

ITEMS = {
    "lantern": SharedItem(
        id="lantern",
        label="lantern",
        phrase="the little star lantern",
        beam="spill honey-colored light across the sheets",
        comfort_line="I do not want the dark to be so big",
        help=3,
        light=True,
        comfort=True,
        tags={"lantern", "sharing", "light"},
    ),
    "flashlight": SharedItem(
        id="flashlight",
        label="flashlight",
        phrase="the moon flashlight",
        beam="paint a silver path through the room",
        comfort_line="The sound feels less scary if we look together",
        help=3,
        light=True,
        comfort=False,
        tags={"flashlight", "sharing", "light"},
    ),
    "pillow": SharedItem(
        id="pillow",
        label="pillow",
        phrase="the extra moon pillow",
        beam="rest softly by the blankets",
        comfort_line="I want something kind beside me",
        help=1,
        light=False,
        comfort=True,
        tags={"pillow", "sharing", "comfort"},
    ),
}

CHOICES = {
    "share": Choice(id="share", shares=True, together=True, tags={"sharing", "good"}),
    "keep": Choice(id="keep", shares=False, together=False, tags={"selfish", "bad"}),
}

GIRL_NAMES = ["Lila", "Nora", "Mina", "Eva", "Lucy", "Maya", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Sam", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["sleepy", "gentle", "careful", "curious", "soft-voiced", "tender"]


KNOWLEDGE = {
    "lantern": [
        ("What is a lantern?",
         "A lantern is a light with a cover around it, so it can glow softly and safely. A small lantern can make a dark room feel friendlier.")
    ],
    "flashlight": [
        ("What does a flashlight do?",
         "A flashlight shines a beam of light when you turn it on. It helps people see in dark places without using fire.")
    ],
    "sharing": [
        ("Why does sharing help when something feels scary?",
         "Sharing means nobody has to face the hard part alone. When children stay together, they can lend each other courage and make kinder choices.")
    ],
    "bedtime": [
        ("Why do little sounds seem bigger at bedtime?",
         "At bedtime the house is quieter, so tiny noises stand out more. When the room is dark and still, a small sound can feel like a big mystery.")
    ],
    "mouse": [
        ("Are mice always scary?",
         "No. Many mice are tiny and mostly just looking for crumbs or a place to hide. They can still surprise people because they move so quickly.")
    ],
    "kitten": [
        ("Why might a kitten make a crinkly noise?",
         "A kitten can rustle paper or bags when it climbs somewhere small. The sound can seem mysterious before you know what it is.")
    ],
    "turtle": [
        ("How can a turtle make tapping sounds?",
         "A turtle can bump a shell or nose against a toy or wooden thing. Slow animals can still make surprising noises.")
    ],
}
KNOWLEDGE_ORDER = ["bedtime", "sharing", "lantern", "flashlight", "mouse", "kitten", "turtle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    noise = f["noise"]
    item = f["item_cfg"]
    if f["outcome"] == "good":
        return [
            'Write a bedtime story for a 3-to-5-year-old that includes the word "pesky", a mysterious noise, and a lesson about sharing.',
            f"Tell a soft suspense story where {holder.id} and {waiter.id} hear {noise.sound} at bedtime and choose to share {item.phrase}.",
            "Write a gentle bedtime tale where children stay together in the dark, solve a little mystery, and end the night feeling safe.",
        ]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the word "pesky", suspense, sharing, and a sad ending.',
        f"Tell a suspenseful bedtime tale where {holder.id} refuses to share {item.phrase} after hearing {noise.sound}, and the night ends badly.",
        "Write a story where a child keeps the only helpful bedtime object instead of sharing, and the ending shows why that choice hurt everyone.",
    ]


def pair_noun(holder: Entity, waiter: Entity, relationship: str) -> str:
    if relationship == "siblings":
        if holder.type == "boy" and waiter.type == "boy":
            return "two brothers"
        if holder.type == "girl" and waiter.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    parent = f["parent"]
    noise = f["noise"]
    item = f["item_cfg"]
    relationship = f["relationship"]
    pair = pair_noun(holder, waiter, relationship)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {holder.id} and {waiter.id}, at bedtime with their {parent.label_word}. "
            f"They are trying to understand a strange noise in the dark."
        ),
        (
            "What made the room feel suspenseful?",
            f"A pesky {noise.sound} kept coming from {noise.spot}, then stopping again. "
            f"That made the quiet bedroom feel full of secrets because nobody knew what was making the sound."
        ),
        (
            f"What did {waiter.id} ask {holder.id} to do?",
            f"{waiter.id} asked to use {item.phrase} together. "
            f"The request mattered because it was the one helpful thing that could make the mystery less frightening."
        ),
    ]
    if f["outcome"] == "good":
        qa.extend([
            (
                "How did sharing change the story?",
                f"Sharing let both children walk together and use the light at the same time. "
                f"Because they stayed together, they were brave enough to find the real cause and help it."
            ),
            (
                "What was making the noise?",
                f"It turned out that {noise.reveal}. "
                f"The sound seemed scary before they looked closely, but it was really a small problem that needed kindness."
            ),
            (
                "How did the story end?",
                f"It ended calmly and safely, with the mystery solved and the room feeling cozy again. "
                f"The ending shows that sharing made bedtime gentler for everyone."
            ),
        ])
    else:
        qa.extend([
            (
                "Why did the ending turn sad?",
                f"The ending turned sad because {holder.id} would not share the only helpful thing and went alone. "
                f"When fear grew bigger, the light was lost under the bed, so the mystery stayed unsolved and both children ended the night upset."
            ),
            (
                "Did anyone learn something from the bad ending?",
                f"Yes. The children learned that keeping help to yourself can make a scary moment worse instead of better. "
                f"If they had stayed together and shared, the room would likely have felt safer."
            ),
            (
                "How did the story end?",
                f"They fell asleep late and unhappy, still wishing they had shared and stayed together. "
                f"The final image is dark and sniffly, which proves the choice changed the whole night for the worse."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bedtime", "sharing"}
    noise = world.facts["noise"]
    item = world.facts["item_cfg"]
    tags |= set(noise.tags)
    tags |= set(item.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("gives_light", e.gives_light), ("gives_comfort", e.gives_comfort), ("tiny", e.tiny)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        noise="scratch",
        item="lantern",
        choice="share",
        holder_name="Lila",
        holder_gender="girl",
        waiter_name="Owen",
        waiter_gender="boy",
        parent="mother",
        holder_trait="gentle",
        waiter_trait="careful",
        relationship="siblings",
    ),
    StoryParams(
        noise="crinkle",
        item="flashlight",
        choice="share",
        holder_name="Finn",
        holder_gender="boy",
        waiter_name="Maya",
        waiter_gender="girl",
        parent="father",
        holder_trait="curious",
        waiter_trait="soft-voiced",
        relationship="friends",
    ),
    StoryParams(
        noise="tap",
        item="lantern",
        choice="keep",
        holder_name="Nora",
        holder_gender="girl",
        waiter_name="Lucy",
        waiter_gender="girl",
        parent="mother",
        holder_trait="sleepy",
        waiter_trait="tender",
        relationship="siblings",
    ),
]


def explain_rejection(item: SharedItem, noise: Noise) -> str:
    return (
        f"(No story: {item.phrase} does not give enough help for a bedtime mystery like {noise.sound}. "
        f"This world needs an item that can genuinely make the dark feel manageable, such as a lantern or flashlight.)"
    )


ASP_RULES = r"""
usable_item(I,N) :- item(I), noise(N), help(I,H), danger(N,D), help_min(M), H >= D, H >= M.
valid(N,I,C) :- noise(N), choice(C), usable_item(I,N).

good_outcome :- chosen_choice(C), shares(C), together(C), chosen_item(I), chosen_noise(N), usable_item(I,N).
bad_outcome :- not good_outcome.

outcome(good) :- good_outcome.
outcome(bad) :- bad_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nid, noise in NOISES.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("danger", nid, noise.danger))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("help", iid, item.help))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if choice.shares:
            lines.append(asp.fact("shares", cid))
        if choice.together:
            lines.append(asp.fact("together", cid))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_noise", params.noise),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    lines = [sample.story]
    if sample.prompts:
        lines.append(sample.prompts[0])
    _ = "\n".join(lines)


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != predict_outcome(NOISES[p.noise], ITEMS[p.item], CHOICES[p.choice])]
    if mismatches:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime mystery about sharing, suspense, and what happens when kindness fails."
    )
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.noise:
        if not item_works(ITEMS[args.item], NOISES[args.noise]):
            raise StoryError(explain_rejection(ITEMS[args.item], NOISES[args.noise]))

    combos = [
        c for c in valid_combos()
        if (args.noise is None or c[0] == args.noise)
        and (args.item is None or c[1] == args.item)
        and (args.choice is None or c[2] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    noise_id, item_id, choice_id = rng.choice(sorted(combos))
    holder_name, holder_gender = _pick_child(rng)
    waiter_name, waiter_gender = _pick_child(rng, avoid=holder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    holder_trait = rng.choice(TRAITS)
    waiter_trait = rng.choice(TRAITS)
    relationship = rng.choice(["siblings", "friends"])

    return StoryParams(
        noise=noise_id,
        item=item_id,
        choice=choice_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        waiter_name=waiter_name,
        waiter_gender=waiter_gender,
        parent=parent,
        holder_trait=holder_trait,
        waiter_trait=waiter_trait,
        relationship=relationship,
    )


def generate(params: StoryParams) -> StorySample:
    if params.noise not in NOISES:
        raise StoryError(f"(Unknown noise: {params.noise})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    noise = NOISES[params.noise]
    item = ITEMS[params.item]
    choice = CHOICES[params.choice]
    if not item_works(item, noise):
        raise StoryError(explain_rejection(item, noise))

    world = tell(
        noise=noise,
        item=item,
        choice=choice,
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        waiter_name=params.waiter_name,
        waiter_gender=params.waiter_gender,
        parent_type=params.parent,
        holder_trait=params.holder_trait,
        waiter_trait=params.waiter_trait,
        relationship=params.relationship,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (noise, item, choice) combos:\n")
        for noise_id, item_id, choice_id in combos:
            outcome = predict_outcome(NOISES[noise_id], ITEMS[item_id], CHOICES[choice_id])
            print(f"  {noise_id:8} {item_id:10} {choice_id:6} -> {outcome}")
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
            outcome = predict_outcome(NOISES[p.noise], ITEMS[p.item], CHOICES[p.choice])
            header = f"### {p.holder_name} & {p.waiter_name}: {p.noise} with {p.item} ({p.choice}, {outcome})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
