#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py
==============================================================

A standalone storyworld for a tiny nursery-rhyme-like domain:

    Nick wants to make a grand little band.
    A loud clatter startles a nearby animal.
    Something small spills or topples.
    A grown-up helps Nick clean up and choose a softer sound.

The world is deliberately small and constraint-checked. It only tells stories
where a chosen loud tool would really startle the listener in that scene, and
where the chosen gentle tool is actually soft enough to solve the same problem:
Nick still gets music, but without the upset.

Run it
------
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py --scene kitchen
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py --loud-tool pot_lid
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/nick_sound_effects_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
HEEDFUL_TRAITS = {"careful", "gentle", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "hen"}
        male = {"boy", "father", "grandfather"}
        neutral_they = {"child"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_they:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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


@dataclass
class Scene:
    id: str
    place: str
    intro_line: str
    listener_type: str
    listener_label: str
    listener_sound: str
    cargo_label: str
    cargo_phrase: str
    cargo_kind: str
    cargo_event: str
    cargo_result: str
    cleanup_line: str
    ending_image: str
    threshold: int
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
class LoudTool:
    id: str
    label: str
    phrase: str
    sound: str
    strike_verb: str
    loudness: int
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
class SoftTool:
    id: str
    label: str
    phrase: str
    sound: str
    verb: str
    loudness: int
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "scene_threshold": 0,
            "loudness": 0,
            "cargo_meter": "",
        }

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


def _r_startle(world: World) -> list[str]:
    loud = world.facts["loudness"]
    threshold = world.facts["scene_threshold"]
    listener = world.get("listener")
    if loud <= threshold:
        return []
    if listener.meters["startled"] >= THRESHOLD:
        return []
    sig = ("startle", listener.id, loud, threshold)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.meters["startled"] += 1
    listener.memes["fear"] += 1
    nick = world.get("nick")
    nick.memes["worry"] += 1
    return ["__startled__"]


def _r_cargo(world: World) -> list[str]:
    listener = world.get("listener")
    cargo = world.get("cargo")
    meter = world.facts["cargo_meter"]
    if listener.meters["startled"] < THRESHOLD:
        return []
    if cargo.meters[meter] >= THRESHOLD:
        return []
    sig = ("cargo", cargo.id, meter)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters[meter] += 1
    cargo.meters["messy"] += 1
    world.get("room").meters["mess"] += 1
    world.get("helper").meters["workload"] += 1
    return ["__cargo__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="startle", tag="emotional", apply=_r_startle),
    Rule(name="cargo", tag="physical", apply=_r_cargo),
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
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SCENES = {
    "kitchen": Scene(
        id="kitchen",
        place="the sunny kitchen",
        intro_line="In the sunny kitchen, Nick found a patch of floor bright as butter.",
        listener_type="kitten",
        listener_label="the kitten",
        listener_sound="mew-mew",
        cargo_label="milk bowl",
        cargo_phrase="a round blue bowl of milk",
        cargo_kind="milk",
        cargo_event="spilled",
        cargo_result="the milk ran in a white little river across the floor",
        cleanup_line="They wiped the milk with a cloth until the tiles shone again.",
        ending_image="the kitten lapped calmly while Nick kept a softer beat beside the door",
        threshold=1,
        tags={"milk", "sound"},
    ),
    "hallway": Scene(
        id="hallway",
        place="the long hallway",
        intro_line="In the long hallway, Nick marched where the floorboards liked to hum.",
        listener_type="puppy",
        listener_label="the puppy",
        listener_sound="yip-yip",
        cargo_label="block tower",
        cargo_phrase="a tall block tower",
        cargo_kind="blocks",
        cargo_event="toppled",
        cargo_result="the blocks went tum-tum down in a bright wooden tumble",
        cleanup_line="They stacked the blocks back into a neat tower, one by one.",
        ending_image="the puppy wagged by the rebuilt tower while Nick tapped a kinder tune on the step",
        threshold=1,
        tags={"blocks", "sound"},
    ),
    "yard": Scene(
        id="yard",
        place="the little yard",
        intro_line="In the little yard, Nick twirled where the breeze could carry a tune.",
        listener_type="hen",
        listener_label="the hen",
        listener_sound="cluck-cluck",
        cargo_label="seed basket",
        cargo_phrase="a wicker basket of seeds",
        cargo_kind="seeds",
        cargo_event="scattered",
        cargo_result="the seeds skipped and pattered over the path like tiny pebbles",
        cleanup_line="They scooped the seeds back into the basket with slow careful hands.",
        ending_image="the hen pecked in peace while Nick made a soft song under the pear tree",
        threshold=1,
        tags={"seeds", "sound"},
    ),
}

LOUD_TOOLS = {
    "pot_lid": LoudTool(
        id="pot_lid",
        label="pot lid",
        phrase="a bright pot lid and spoon",
        sound="clang-clang! bang-bang!",
        strike_verb="clattered",
        loudness=3,
        tags={"loud", "kitchen_sound"},
    ),
    "pan": LoudTool(
        id="pan",
        label="pan",
        phrase="a shiny pan and wooden spoon",
        sound="bam-bam! tang-tang!",
        strike_verb="banged",
        loudness=3,
        tags={"loud", "kitchen_sound"},
    ),
    "horn": LoudTool(
        id="horn",
        label="toy horn",
        phrase="a little toy horn",
        sound="toot-toot! parp-parp!",
        strike_verb="tooted",
        loudness=2,
        tags={"loud", "horn"},
    ),
}

SOFT_TOOLS = {
    "shaker": SoftTool(
        id="shaker",
        label="paper shaker",
        phrase="a paper shaker full of rice",
        sound="shush-shush",
        verb="shook",
        loudness=1,
        tags={"shaker", "sound"},
    ),
    "drum": SoftTool(
        id="drum",
        label="lap drum",
        phrase="a small lap drum",
        sound="tum-tee tum",
        verb="tapped",
        loudness=1,
        tags={"drum", "sound"},
    ),
    "hum": SoftTool(
        id="hum",
        label="humming voice",
        phrase="his own humming voice",
        sound="la-la-loo",
        verb="hummed",
        loudness=0,
        tags={"hum", "sound"},
    ),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandmother": "grandmother",
}

TRAITS = ["careful", "gentle", "thoughtful", "bouncy", "proud", "hasty"]
BOYS = ["Nick"]
CURATED_NAMES = ["Nick"]


def hazard(scene: Scene, loud_tool: LoudTool) -> bool:
    return loud_tool.loudness > scene.threshold


def safe_alternative(scene: Scene, soft_tool: SoftTool) -> bool:
    return soft_tool.loudness <= scene.threshold


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for loud_id, loud_tool in LOUD_TOOLS.items():
            for soft_id, soft_tool in SOFT_TOOLS.items():
                if hazard(scene, loud_tool) and safe_alternative(scene, soft_tool):
                    combos.append((scene_id, loud_id, soft_id))
    return combos


def would_avert(trait: str) -> bool:
    return trait in HEEDFUL_TRAITS


def predict_mishap(world: World, scene: Scene, loud_tool: LoudTool) -> dict:
    sim = world.copy()
    sim.facts["scene_threshold"] = scene.threshold
    sim.facts["loudness"] = loud_tool.loudness
    _do_loud_sound(sim, narrate=False)
    cargo = sim.get("cargo")
    meter = scene.cargo_event
    return {
        "startled": sim.get("listener").meters["startled"] >= THRESHOLD,
        "mishap": cargo.meters[meter] >= THRESHOLD,
    }


def _do_loud_sound(world: World, narrate: bool = True) -> None:
    nick = world.get("nick")
    nick.memes["joy"] += 1
    nick.memes["pride"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, scene: Scene) -> None:
    nick = world.get("nick")
    world.say(
        f"{scene.intro_line} Nick, quick as a chick and bright as a wick, wanted a rhyme with a ring."
    )
    nick.memes["joy"] += 1


def choose_noise(world: World, loud_tool: LoudTool) -> None:
    world.say(
        f"He found {loud_tool.phrase} and grinned. \"I will make a marching song,\" said Nick."
    )


def warn(world: World, scene: Scene, loud_tool: LoudTool) -> None:
    helper = world.get("helper")
    pred = predict_mishap(world, scene, loud_tool)
    world.facts["predicted_mishap"] = pred["mishap"]
    cargo = scene.cargo_label
    world.say(
        f"But {helper.label_word} saw {scene.listener_label} beside {scene.cargo_phrase} and said, "
        f"\"Softly, Nick, softly. A hard loud {loud_tool.label} may startle {scene.listener_label}.\""
    )
    if pred["mishap"]:
        world.say(
            f"\"If {scene.listener_label} jumps, the {cargo} could be {scene.cargo_event}, and then we must stop to tidy.\""
        )


def heed(world: World, soft_tool: SoftTool) -> None:
    nick = world.get("nick")
    nick.memes["restraint"] += 1
    nick.memes["relief"] += 1
    world.say(
        f"Nick paused with the spoon in the air. He listened, lowered his hands, and chose {soft_tool.phrase} instead."
    )


def defy(world: World, loud_tool: LoudTool) -> None:
    nick = world.get("nick")
    nick.memes["defiance"] += 1
    world.say(
        f"But the beat felt bold in his toes, and Nick gave the {loud_tool.label} a try."
    )


def accident(world: World, scene: Scene, loud_tool: LoudTool) -> None:
    listener = world.get("listener")
    _do_loud_sound(world, narrate=False)
    listener.memes["fear"] += 0.0
    world.say(
        f"{loud_tool.sound} Nick {loud_tool.strike_verb} the {loud_tool.label}, and {scene.listener_label} jumped with a startled {scene.listener_sound}."
    )
    if world.get("cargo").meters[scene.cargo_event] >= THRESHOLD:
        world.say(
            f"Then the {scene.cargo_label} was {scene.cargo_event}, and {scene.cargo_result}."
        )


def comfort_and_clean(world: World, scene: Scene) -> None:
    helper = world.get("helper")
    nick = world.get("nick")
    listener = world.get("listener")
    cargo = world.get("cargo")
    nick.memes["guilt"] += 1
    nick.memes["care"] += 1
    nick.memes["relief"] += 1
    listener.memes["fear"] = 0.0
    cargo.meters["clean"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came close, calm and kind. \"No scolding song,\" {helper.pronoun()} said. \"First we help, then we sing.\""
    )
    world.say(scene.cleanup_line)
    world.say(
        f"Nick knelt small and still, and when the tidying was done, {scene.listener_label} was calm again."
    )


def gentle_fix(world: World, scene: Scene, soft_tool: SoftTool) -> None:
    nick = world.get("nick")
    helper = world.get("helper")
    nick.memes["joy"] += 1
    nick.memes["pride"] = 0.0
    nick.memes["safety"] += 1
    world.say(
        f"Then {helper.label_word} led Nick to a better spot and handed him {soft_tool.phrase}."
    )
    world.say(
        f"\"Try this beat,\" said {helper.label_word}. Nick {soft_tool.verb} a little tune: {soft_tool.sound}, {soft_tool.sound}."
    )
    world.say(
        f"So Nick learned a kinder trick: soft for the small, and sweet for the quick. At the end, {scene.ending_image}."
    )


def tell(
    scene: Scene,
    loud_tool: LoudTool,
    soft_tool: SoftTool,
    helper_type: str = "mother",
    trait: str = "careful",
    seed: Optional[int] = None,
) -> World:
    world = World()
    nick = world.add(
        Entity(
            id="nick",
            kind="character",
            type="boy",
            label="Nick",
            traits=[trait],
            role="hero",
            attrs={"seed": seed, "trait": trait},
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
            attrs={},
            tags={"grownup"},
        )
    )
    listener = world.add(
        Entity(
            id="listener",
            kind="thing",
            type=scene.listener_type,
            label=scene.listener_label,
            role="listener",
            attrs={},
            tags=set(scene.tags),
        )
    )
    cargo = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type=scene.cargo_kind,
            label=scene.cargo_label,
            role="cargo",
            attrs={},
            tags=set(scene.tags),
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="place",
            label=scene.place,
            role="place",
            attrs={},
            tags=set(scene.tags),
        )
    )

    nick.memes["joy"] = 0.0
    nick.memes["defiance"] = 0.0
    nick.memes["relief"] = 0.0
    helper.meters["workload"] = 0.0
    listener.meters["startled"] = 0.0
    cargo.meters[scene.cargo_event] = 0.0
    cargo.meters["messy"] = 0.0
    room.meters["mess"] = 0.0
    world.facts["scene_threshold"] = scene.threshold
    world.facts["loudness"] = loud_tool.loudness
    world.facts["cargo_meter"] = scene.cargo_event

    introduce(world, scene)
    choose_noise(world, loud_tool)

    world.para()
    warn(world, scene, loud_tool)

    if would_avert(trait):
        heed(world, soft_tool)
        outcome = "averted"
        world.para()
        gentle_fix(world, scene, soft_tool)
    else:
        defy(world, loud_tool)
        world.para()
        accident(world, scene, loud_tool)
        world.para()
        comfort_and_clean(world, scene)
        gentle_fix(world, scene, soft_tool)
        outcome = "mishap"

    world.facts.update(
        scene=scene,
        loud_tool=loud_tool,
        soft_tool=soft_tool,
        helper=helper,
        nick=nick,
        listener=listener,
        cargo=cargo,
        outcome=outcome,
        trait=trait,
        hazard=hazard(scene, loud_tool),
        predicted_mishap=world.facts.get("predicted_mishap", False),
    )
    return world


KNOWLEDGE = {
    "sound": [
        (
            "Why can a loud sound upset a small animal?",
            "Small animals can startle fast when a big noise bursts near them. Their ears notice sharp sounds quickly, so they may jump before they understand what happened.",
        )
    ],
    "milk": [
        (
            "What happens when milk spills on the floor?",
            "Milk spreads into a slippery puddle. A grown-up needs to wipe it up so nobody slips.",
        )
    ],
    "blocks": [
        (
            "Why do blocks fall when a tower wobbles?",
            "A tall block tower needs balance. If it shakes too much, the blocks can tumble down.",
        )
    ],
    "seeds": [
        (
            "Why do tiny seeds scatter easily?",
            "Seeds are light and small, so one bump can send them skittering in many directions. That is why careful hands help keep them in a basket.",
        )
    ],
    "shaker": [
        (
            "What is a shaker?",
            "A shaker is a little music maker you move back and forth. It can make a soft rhythm without a big bang.",
        )
    ],
    "drum": [
        (
            "What is a lap drum?",
            "A lap drum is a small drum you tap gently while it rests close to you. It can sound warm and soft instead of sharp and noisy.",
        )
    ],
    "hum": [
        (
            "What is humming?",
            "Humming is making music with your mouth closed. It can be quiet and gentle, so it is a good way to sing near others.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sound", "milk", "blocks", "seeds", "shaker", "drum", "hum"]


@dataclass
class StoryParams:
    scene: str
    loud_tool: str
    soft_tool: str
    helper: str
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


CURATED = [
    StoryParams(
        scene="kitchen",
        loud_tool="pot_lid",
        soft_tool="hum",
        helper="mother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        scene="hallway",
        loud_tool="horn",
        soft_tool="drum",
        helper="father",
        trait="bouncy",
        seed=2,
    ),
    StoryParams(
        scene="yard",
        loud_tool="pan",
        soft_tool="shaker",
        helper="grandmother",
        trait="thoughtful",
        seed=3,
    ),
    StoryParams(
        scene="kitchen",
        loud_tool="horn",
        soft_tool="shaker",
        helper="mother",
        trait="hasty",
        seed=4,
    ),
]


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    loud_tool = world.facts["loud_tool"]
    soft_tool = world.facts["soft_tool"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            'Write a short nursery-rhyme-style story for a 3-to-5-year-old about Nick wanting to make loud music but choosing a gentle sound instead.',
            f'Write a rhyming story with sound effects where Nick almost uses a {loud_tool.label}, then listens to a grown-up and switches to {soft_tool.phrase}.',
            f'Tell a tiny musical story set in {scene.place} with Nick, a nearby animal, and a soft ending image.',
        ]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old about Nick making too much noise, causing a small mess, and learning a gentler way.',
        f'Write a rhyming story with sound effects where Nick uses a {loud_tool.label}, startles {scene.listener_label}, and then helps clean up before making softer music.',
        f'Tell a tiny story set in {scene.place} where Nick learns that a sweet beat can be better than a big bang.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    scene = world.facts["scene"]
    loud_tool = world.facts["loud_tool"]
    soft_tool = world.facts["soft_tool"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    trait = world.facts["trait"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Nick, who wanted to make a lively little song in {scene.place}. A {helper.label_word} was nearby, and so was {scene.listener_label}.",
        ),
        (
            "What did Nick want to do?",
            f"Nick wanted to make music with {loud_tool.phrase}. The noisy idea felt exciting because he wanted a marching beat, not a quiet one.",
        ),
        (
            f"Why did {helper.label_word} warn Nick?",
            f"{helper.label_word.capitalize()} warned Nick because {scene.listener_label} was beside {scene.cargo_phrase}. A loud {loud_tool.label} could startle {scene.listener_label} and make the {scene.cargo_label} get {scene.cargo_event}.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                "What happened after the warning?",
                f"Nick listened and stopped before making the big noise. Because he was {trait}, he chose {soft_tool.phrase} instead, so nothing spilled or toppled.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with Nick making a softer tune instead of a crash. The ending shows he learned that music can still be fun when it is gentle.",
            )
        )
    else:
        qa.append(
            (
                "What went wrong when Nick made the loud sound?",
                f"{scene.listener_label.capitalize()} jumped, and the {scene.cargo_label} was {scene.cargo_event}. The big sound caused the mishap because the nearby animal startled first.",
            )
        )
        qa.append(
            (
                "What did Nick do after the mishap?",
                f"Nick helped clean up with {helper.label_word}. After the mess was fixed, he used {soft_tool.phrase}, which let him keep making music in a kinder way.",
            )
        )
        qa.append(
            (
                "What lesson did Nick learn?",
                f"Nick learned that loud fun is not always the best fun. A soft beat can protect small animals and their things while still making a happy song.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    scene = world.facts["scene"]
    soft_tool = world.facts["soft_tool"]
    tags = set(scene.tags) | set(soft_tool.tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in (None, "", 0)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(scene: Scene, loud_tool: LoudTool, soft_tool: SoftTool) -> str:
    if not hazard(scene, loud_tool):
        return (
            f"(No story: the {loud_tool.label} is not loud enough to trouble {scene.listener_label} in this world, "
            f"so there is no honest mishap or warning to tell.)"
        )
    if not safe_alternative(scene, soft_tool):
        return (
            f"(No story: {soft_tool.phrase} is still too noisy to be the gentle fix here. "
            f"Pick a softer tool like humming, a shaker, or a small drum.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
hazard(S, L) :- scene(S), loud_tool(L), threshold(S, T), loudness(L, V), V > T.
safe(S, Q)   :- scene(S), soft_tool(Q), threshold(S, T), soft_loudness(Q, V), V <= T.
valid(S, L, Q) :- hazard(S, L), safe(S, Q).

heedful(T) :- trait(T), heedful_trait(T).
outcome(averted) :- chosen_trait(T), heedful(T).
outcome(mishap)  :- chosen_trait(T), not heedful(T).

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("threshold", sid, scene.threshold))
    for lid, tool in LOUD_TOOLS.items():
        lines.append(asp.fact("loud_tool", lid))
        lines.append(asp.fact("loudness", lid, tool.loudness))
    for qid, tool in SOFT_TOOLS.items():
        lines.append(asp.fact("soft_tool", qid))
        lines.append(asp.fact("soft_loudness", qid, tool.loudness))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(HEEDFUL_TRAITS):
        lines.append(asp.fact("heedful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    program = asp_program(asp.fact("chosen_trait", params.trait))
    model = asp.one_model(program)
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.trait) else "mishap"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: Nick, sound effects, and a nursery-rhyme-style lesson about gentle music."
    )
    ap.add_argument("--scene", choices=sorted(SCENES))
    ap.add_argument("--loud-tool", choices=sorted(LOUD_TOOLS))
    ap.add_argument("--soft-tool", choices=sorted(SOFT_TOOLS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.loud_tool and args.soft_tool:
        scene = SCENES[args.scene]
        loud_tool = LOUD_TOOLS[args.loud_tool]
        soft_tool = SOFT_TOOLS[args.soft_tool]
        if not (hazard(scene, loud_tool) and safe_alternative(scene, soft_tool)):
            raise StoryError(explain_combo(scene, loud_tool, soft_tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.loud_tool is None or combo[1] == args.loud_tool)
        and (args.soft_tool is None or combo[2] == args.soft_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, loud_id, soft_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        scene=scene_id,
        loud_tool=loud_id,
        soft_tool=soft_id,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene '{params.scene}'.)")
    if params.loud_tool not in LOUD_TOOLS:
        raise StoryError(f"(Unknown loud tool '{params.loud_tool}'.)")
    if params.soft_tool not in SOFT_TOOLS:
        raise StoryError(f"(Unknown soft tool '{params.soft_tool}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait '{params.trait}'.)")

    scene = SCENES[params.scene]
    loud_tool = LOUD_TOOLS[params.loud_tool]
    soft_tool = SOFT_TOOLS[params.soft_tool]
    if not (hazard(scene, loud_tool) and safe_alternative(scene, soft_tool)):
        raise StoryError(explain_combo(scene, loud_tool, soft_tool))

    world = tell(
        scene=scene,
        loud_tool=loud_tool,
        soft_tool=soft_tool,
        helper_type=params.helper,
        trait=params.trait,
        seed=params.seed,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

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
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        sample.to_json()
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated, serialized, and emitted a normal story.")
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
        print(f"{len(combos)} compatible (scene, loud_tool, soft_tool) triples:\n")
        for scene, loud_tool, soft_tool in combos:
            print(f"  {scene:8} {loud_tool:8} {soft_tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### Nick in {p.scene}: {p.loud_tool} -> {p.soft_tool} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
