#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py
=================================================================================

A standalone story world about a child with an unfinished cloth costume that is
mended and transformed with one careful stitch after another.

Seed requirements covered
-------------------------
- uses the words: "variable", "absent", "stitch"
- feature: Transformation
- style: Rhyming Story

World premise
-------------
A child is getting ready for a small costume walk. The costume begins in one
state -- cocoon, seed, or cloud -- but one key piece is absent, so the magic
change cannot happen yet. A grown-up helper chooses a matching patch and thread,
adds the missing stitch-work, and the costume transforms into butterfly, flower,
or rainbow. If they finish in time, the child joins the walk; if they finish
late, the child still ends with a joyful transformed twirl at home.

Run it
------
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py --base cocoon_cape --patch wings
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py --base cloud_smock --patch petals
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/variable_absent_stitch_transformation_rhyming_story.py --verify
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
SKILL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class BaseCostume:
    id: str
    start_label: str
    start_phrase: str
    transformed_label: str
    transformed_phrase: str
    missing_piece: str
    bare_line: str
    after_line: str
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
class Patch:
    id: str
    label: str
    phrase: str
    compatible_bases: set[str] = field(default_factory=set)
    transform_word: str = ""
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
class ThreadColor:
    id: str
    label: str
    shimmer: str
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
class Helper:
    id: str
    type: str
    label: str
    skill: int
    comfort_line: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_absent_sad(world: World) -> list[str]:
    costume = world.get("costume")
    child = world.get("child")
    if costume.meters["missing"] < THRESHOLD:
        return []
    sig = ("absent_sad",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["disappointment"] += 1
    return []


def _r_stitch_complete(world: World) -> list[str]:
    costume = world.get("costume")
    if costume.meters["stitched"] < THRESHOLD or costume.meters["missing"] < THRESHOLD:
        return []
    sig = ("stitch_complete",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    costume.meters["missing"] = 0.0
    costume.meters["complete"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    costume = world.get("costume")
    child = world.get("child")
    if costume.meters["complete"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    costume.meters["transformed"] += 1
    child.memes["wonder"] += 1
    child.memes["confidence"] += 1
    child.memes["disappointment"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="absent_sad", tag="emotion", apply=_r_absent_sad),
    Rule(name="stitch_complete", tag="physical", apply=_r_stitch_complete),
    Rule(name="transform", tag="physical", apply=_r_transform),
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


def patch_fits(base_id: str, patch_id: str) -> bool:
    return base_id in PATCHES[patch_id].compatible_bases


def skilled_enough(helper_id: str) -> bool:
    return HELPERS[helper_id].skill >= SKILL_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for base_id in BASES:
        for patch_id in PATCHES:
            if not patch_fits(base_id, patch_id):
                continue
            for helper_id in HELPERS:
                if skilled_enough(helper_id):
                    combos.append((base_id, patch_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.delay >= 1:
        return "home"
    return "walk"


def predict_transform(world: World) -> dict:
    sim = world.copy()
    costume = sim.get("costume")
    costume.meters["stitched"] += 1
    propagate(sim, narrate=False)
    return {
        "complete": costume.meters["complete"] >= THRESHOLD,
        "transformed": costume.meters["transformed"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, base: BaseCostume) -> None:
    child.memes["hope"] += 1
    costume = world.get("costume")
    costume.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In a snug little room at the close of the day, {child.id} got ready for the costume walk away."
    )
    world.say(
        f"On the chair lay {base.start_phrase}, soft in a heap, while a basket of cloth scraps in variable shades sat deep."
    )


def admire(world: World, child: Entity, base: BaseCostume) -> None:
    world.say(
        f"{child.id} loved how {base.bare_line}, yet {child.pronoun('possessive')} smile slipped low with a tiny sigh."
    )
    world.say(
        f"One important piece was absent still, and without it the change could not bend to {child.pronoun('possessive')} will."
    )


def worry(world: World, child: Entity, helper: Entity, base: BaseCostume) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Oh dear," said {child.id}, "it cannot be right. It wants to transform, but it waits for the night."'
    )
    world.say(
        f'{helper.label_word.capitalize()} came near with a calm little nod. "{helper.comfort_line}"'
    )


def choose_patch(world: World, child: Entity, helper: Entity, base: BaseCostume, patch: Patch, thread: ThreadColor) -> None:
    pred = predict_transform(world)
    world.facts["predicted_transform"] = pred["transformed"]
    world.say(
        f"Together they searched through the scraps in the bin for {patch.phrase}, a match for the shape tucked in."
    )
    world.say(
        f"They found {thread.shimmer} thread for each careful stitch, and {helper.label_word} said, "
        f'"This little piece is not too much, not too rich."'
    )


def sew(world: World, child: Entity, helper: Entity, base: BaseCostume, patch: Patch, thread: ThreadColor) -> None:
    costume = world.get("costume")
    helper.memes["care"] += 1
    child.memes["attention"] += 1
    costume.meters["stitched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Loop went the thread and dip went the hand; stitch after stitch made the small shape stand."
    )
    world.say(
        f"{child.id} held the cloth while {helper.label_word} drew {thread.label} arcs neat and slow, "
        f"and the once-quiet costume began to glow."
    )


def reveal(world: World, child: Entity, helper: Entity, base: BaseCostume, patch: Patch) -> None:
    costume = world.get("costume")
    if costume.meters["transformed"] < THRESHOLD:
        raise StoryError("(Internal story error: costume failed to transform after a matching stitch.)")
    world.say(
        f"When the final knot gave one soft tug, {base.after_line} -- not plain and snug,"
    )
    world.say(
        f"but {base.transformed_phrase} bright to behold, with {patch.label} turning the simple cloth bold."
    )


def finish_walk(world: World, child: Entity, helper: Entity, base: BaseCostume) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"They hurried outside where the paper stars flicked, and {child.id} skipped along light as a wick."
    )
    world.say(
        f"At the walk, children clapped for the marvelous sight: {child.id} in {base.transformed_phrase}, swaying bright."
    )
    world.say(
        f"So what had been worried and quiet before went dancing transformed past the lantern-lit door."
    )


def finish_home(world: World, child: Entity, helper: Entity, base: BaseCostume) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    child.memes["wistful"] += 1
    world.say(
        "By the time it was finished, the walk-bell was done, and the last little parade had already begun."
    )
    world.say(
        f"{child.id} looked sad for a blink, then spun round in delight, for {base.transformed_phrase} still shimmered in light."
    )
    world.say(
        f"So there in the room, with {helper.label_word} smiling near, the changed little costume made its own kind of cheer."
    )


def tell(
    base: BaseCostume,
    patch: Patch,
    thread: ThreadColor,
    helper_cfg: Helper,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Grandma",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            label=child_name,
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label="the helper",
            attrs={"helper_id": helper_cfg.id},
        )
    )
    costume = world.add(
        Entity(
            id="costume",
            kind="thing",
            type="costume",
            label=base.start_label,
            owner=child.id,
            attrs={
                "base_id": base.id,
                "patch_id": patch.id,
                "transformed_label": base.transformed_label,
            },
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        base=base,
        patch=patch,
        thread=thread,
        helper_cfg=helper_cfg,
        delay=delay,
    )

    introduce(world, child, helper, base)
    admire(world, child, base)

    world.para()
    worry(world, child, helper, base)
    choose_patch(world, child, helper, base, patch, thread)
    sew(world, child, helper, base, patch, thread)
    reveal(world, child, helper, base, patch)

    world.para()
    if delay == 0:
        finish_walk(world, child, helper, base)
        outcome = "walk"
    else:
        finish_home(world, child, helper, base)
        outcome = "home"

    world.facts.update(
        outcome=outcome,
        transformed=world.get("costume").meters["transformed"] >= THRESHOLD,
        complete=world.get("costume").meters["complete"] >= THRESHOLD,
        absent_before=True,
    )
    return world


BASES = {
    "cocoon_cape": BaseCostume(
        id="cocoon_cape",
        start_label="cocoon cape",
        start_phrase="a soft brown cocoon cape",
        transformed_label="butterfly cape",
        transformed_phrase="a butterfly cape",
        missing_piece="wings",
        bare_line="it wrapped around her like a sleepy shell",
        after_line="the brown cape lifted and opened as well",
        tags={"cocoon", "butterfly", "transformation"},
    ),
    "seed_pocket": BaseCostume(
        id="seed_pocket",
        start_label="seed pocket",
        start_phrase="a round seed pocket costume",
        transformed_label="flower costume",
        transformed_phrase="a flower costume",
        missing_piece="petals",
        bare_line="it bobbed like a seed in a soft little bed",
        after_line="the round seed pocket seemed suddenly spread",
        tags={"seed", "flower", "transformation"},
    ),
    "cloud_smock": BaseCostume(
        id="cloud_smock",
        start_label="cloud smock",
        start_phrase="a puffy cloud smock",
        transformed_label="rainbow smock",
        transformed_phrase="a rainbow smock",
        missing_piece="rainbow ribbons",
        bare_line="it drifted like mist with a pale silver sweep",
        after_line="the pale cloud smock arched in a luminous leap",
        tags={"cloud", "rainbow", "transformation"},
    ),
}

PATCHES = {
    "wings": Patch(
        id="wings",
        label="wings",
        phrase="two bright wings",
        compatible_bases={"cocoon_cape"},
        transform_word="flutter",
        tags={"butterfly", "wings"},
    ),
    "petals": Patch(
        id="petals",
        label="petals",
        phrase="five velvet petals",
        compatible_bases={"seed_pocket"},
        transform_word="bloom",
        tags={"flower", "petals"},
    ),
    "ribbons": Patch(
        id="ribbons",
        label="rainbow ribbons",
        phrase="curved rainbow ribbons",
        compatible_bases={"cloud_smock"},
        transform_word="arc",
        tags={"rainbow", "ribbons"},
    ),
    "tail": Patch(
        id="tail",
        label="a swishy tail",
        phrase="a swishy tail",
        compatible_bases=set(),
        transform_word="swish",
        tags={"tail"},
    ),
}

THREADS = {
    "gold": ThreadColor(
        id="gold",
        label="gold thread",
        shimmer="golden thread",
        tags={"gold"},
    ),
    "silver": ThreadColor(
        id="silver",
        label="silver thread",
        shimmer="silver thread",
        tags={"silver"},
    ),
    "rose": ThreadColor(
        id="rose",
        label="rose thread",
        shimmer="rose-red thread",
        tags={"rose"},
    ),
    "sky": ThreadColor(
        id="sky",
        label="sky-blue thread",
        shimmer="sky-blue thread",
        tags={"blue"},
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        type="grandmother",
        label="Grandma",
        skill=3,
        comfort_line="We can mend what is absent, and we can do it with song.",
        tags={"grandma"},
    ),
    "dad": Helper(
        id="dad",
        type="father",
        label="Dad",
        skill=2,
        comfort_line="A patient little stitch can help a big change come along.",
        tags={"dad"},
    ),
    "aunt": Helper(
        id="aunt",
        type="aunt",
        label="Auntie",
        skill=3,
        comfort_line="Let us match the missing piece, and the cloth will know its way.",
        tags={"aunt"},
    ),
    "brother": Helper(
        id="brother",
        type="boy",
        label="Brother",
        skill=1,
        comfort_line="I can try, but my stitches still hop and slide today.",
        tags={"brother"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Pia", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Ben", "Eli"]


@dataclass
class StoryParams:
    base: str
    patch: str
    thread: str
    helper: str
    child_name: str
    child_type: str
    helper_name: str
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
    "stitch": [
        (
            "What is a stitch?",
            "A stitch is one small loop of thread that holds cloth together. Many little stitches can mend a rip or attach a new piece.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new form. Sometimes the change is physical, and sometimes it also changes how a character feels.",
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar changes inside a chrysalis and later comes out as a butterfly. That is a real kind of transformation in nature.",
        )
    ],
    "flower": [
        (
            "How does a seed become a flower?",
            "A seed can grow roots, a stem, and later a flower when it has water, soil, and sunlight. The tiny beginning changes into something bright and open.",
        )
    ],
    "rainbow": [
        (
            "What makes a rainbow appear?",
            "A rainbow appears when sunlight shines through drops of water. The light bends and spreads into many colors.",
        )
    ],
    "thread": [
        (
            "Why do people use thread with cloth?",
            "Thread helps fasten cloth pieces together. It can repair something old or help make something new.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stitch", "transformation", "thread", "butterfly", "flower", "rainbow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    base = f["base"]
    patch = f["patch"]
    helper = f["helper_cfg"]
    if f["outcome"] == "walk":
        ending = "finish in time for the costume walk"
    else:
        ending = "finish too late for the walk but still end joyfully at home"
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "variable", "absent", and "stitch".',
        f"Tell a gentle transformation story where {child.id} has {base.start_phrase}, but {patch.label} are absent until {helper.label} helps mend it.",
        f"Write a child-facing rhyming tale about a missing costume piece, careful sewing, and a magical change that lets the child {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    base = f["base"]
    patch = f["patch"]
    thread = f["thread"]
    outcome = f["outcome"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper_word}, who work together on a costume. The story follows how an unfinished outfit becomes something new.",
        ),
        (
            f"What problem did {child.id} have at the start?",
            f"{child.id} had {base.start_phrase}, but one important part was absent. Without that missing piece, the costume could not transform the way {child.pronoun('subject')} hoped.",
        ),
        (
            f"How did {helper_word} help?",
            f"{helper_word.capitalize()} searched for {patch.phrase} and used {thread.label} to sew it on. The careful stitch-work fixed what was missing and let the costume become complete.",
        ),
        (
            "What changed after the sewing?",
            f"The unfinished {base.start_label} turned into {base.transformed_phrase}. The change was not only in the cloth, because {child.id} also changed from worried to proud.",
        ),
    ]
    if outcome == "walk":
        qa.append(
            (
                f"How did the story end for {child.id}?",
                f"{child.id} finished in time for the costume walk and skipped outside wearing {base.transformed_phrase}. The ending proves the transformation worked because other children could see and clap for it.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} get to the walk?",
                f"No, the costume was finished after the walk-bell. But the ending is still happy because {child.id} twirled at home in {base.transformed_phrase} and felt the change anyway.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    base = f["base"]
    tags = {"stitch", "transformation", "thread"}
    if "butterfly" in base.tags:
        tags.add("butterfly")
    if "flower" in base.tags:
        tags.add("flower")
    if "rainbow" in base.tags:
        tags.add("rainbow")
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
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        base="cocoon_cape",
        patch="wings",
        thread="gold",
        helper="grandma",
        child_name="Mina",
        child_type="girl",
        helper_name="Grandma",
        delay=0,
    ),
    StoryParams(
        base="seed_pocket",
        patch="petals",
        thread="rose",
        helper="dad",
        child_name="Theo",
        child_type="boy",
        helper_name="Dad",
        delay=0,
    ),
    StoryParams(
        base="cloud_smock",
        patch="ribbons",
        thread="sky",
        helper="aunt",
        child_name="Lila",
        child_type="girl",
        helper_name="Auntie",
        delay=1,
    ),
]


def explain_rejection(base_id: str, patch_id: str, helper_id: Optional[str] = None) -> str:
    if patch_id in PATCHES and base_id in BASES and not patch_fits(base_id, patch_id):
        base = BASES[base_id]
        patch = PATCHES[patch_id]
        return (
            f"(No story: {patch.label} do not fit {base.start_phrase}. "
            f"This world only allows a transformation when the missing piece matches the costume.)"
        )
    if helper_id and helper_id in HELPERS and not skilled_enough(helper_id):
        helper = HELPERS[helper_id]
        return (
            f"(No story: {helper.label} is known here, but the stitching skill is too low "
            f"for a neat repair. Pick a steadier helper like grandma, dad, or aunt.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


ASP_RULES = r"""
fits(B,P) :- base(B), patch(P), compatible(P,B).
skilled(H) :- helper(H), skill(H,S), skill_min(M), S >= M.
valid(B,P,H) :- fits(B,P), skilled(H).

outcome(home) :- delay(D), D >= 1.
outcome(walk) :- delay(D), D < 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for base_id in BASES:
        lines.append(asp.fact("base", base_id))
    for patch_id, patch in PATCHES.items():
        lines.append(asp.fact("patch", patch_id))
        for base_id in sorted(patch.compatible_bases):
            lines.append(asp.fact("compatible", patch_id, base_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill", helper_id, helper.skill))
    lines.append(asp.fact("skill_min", SKILL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome results differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: an absent costume piece, a careful stitch, and a transformation."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--thread", choices=THREADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = in time for the walk, 1 = finished too late")
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and args.patch and not patch_fits(args.base, args.patch):
        raise StoryError(explain_rejection(args.base, args.patch))
    if args.helper and not skilled_enough(args.helper):
        raise StoryError(explain_rejection(args.base or next(iter(BASES)), args.patch or next(iter(PATCHES)), args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.patch is None or combo[1] == args.patch)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    base_id, patch_id, helper_id = rng.choice(sorted(combos))
    thread_id = args.thread or rng.choice(sorted(THREADS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_name = HELPERS[helper_id].label
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        base=base_id,
        patch=patch_id,
        thread=thread_id,
        helper=helper_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.base not in BASES:
        raise StoryError(f"(Invalid base: {params.base})")
    if params.patch not in PATCHES:
        raise StoryError(f"(Invalid patch: {params.patch})")
    if params.thread not in THREADS:
        raise StoryError(f"(Invalid thread: {params.thread})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if not patch_fits(params.base, params.patch):
        raise StoryError(explain_rejection(params.base, params.patch))
    if not skilled_enough(params.helper):
        raise StoryError(explain_rejection(params.base, params.patch, params.helper))
    if params.delay not in (0, 1):
        raise StoryError("(Invalid delay: choose 0 or 1.)")

    world = tell(
        base=BASES[params.base],
        patch=PATCHES[params.patch],
        thread=THREADS[params.thread],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (base, patch, helper) combos:\n")
        for base_id, patch_id, helper_id in combos:
            print(f"  {base_id:12} {patch_id:8} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.base} + {p.patch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
