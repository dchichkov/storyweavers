#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py
=================================================================================

A small ghost-story-flavored storyworld about a child lyric-ist in a misty dale
who mistakes a pale hanging shape for a ghost. A remembered song opens a
flashback, moonlight reveals the truth, and the "ghost" transforms into a moth.

The world is classical and state-driven:
- the child hears a ghostly sign and grows afraid
- a relic is sounded, causing a flashback of the elder's old lesson
- moonlight reaches the cocoon and a moth emerges
- fear changes into wonder, and the child finds a new song ending

Run it
------
    python storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py
    python storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py --all
    python storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/lyric_ist_dale_wink_transformation_flashback_ghost.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "woman", "grandmother", "aunt"}
        male = {"boy", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Spot:
    id: str
    label: str
    approach: str
    haunt: str
    ghost_shape: str
    relics: set[str] = field(default_factory=set)
    moths: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    sound: str
    flashback_text: str
    spots: set[str] = field(default_factory=set)
    memory_tag: str = ""
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
class MothKind:
    id: str
    cocoon: str
    adult: str
    wings: str
    emerge: str
    spots: set[str] = field(default_factory=set)
    memory_tag: str = ""
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
    def __init__(self, spot: Spot) -> None:
        self.spot = spot
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
        clone = World(self.spot)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_shiver(world: World) -> list[str]:
    hero = world.get("hero")
    cocoon = world.get("cocoon")
    if cocoon.meters["rustled"] < THRESHOLD:
        return []
    sig = ("shiver", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["attention"] += 1
    return []


def _r_flashback(world: World) -> list[str]:
    relic = world.get("relic")
    memory = world.get("memory")
    hero = world.get("hero")
    elder = world.get("elder")
    if relic.meters["sounded"] < THRESHOLD:
        return []
    sig = ("flashback", relic.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    memory.meters["shown"] += 1
    hero.memes["courage"] += 1
    hero.memes["wonder"] += 1
    elder.memes["remembering"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    cocoon = world.get("cocoon")
    moth = world.get("moth")
    hero = world.get("hero")
    if cocoon.meters["moonlit"] < THRESHOLD or cocoon.meters["ready"] < THRESHOLD:
        return []
    sig = ("transform", cocoon.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cocoon.meters["opened"] += 1
    moth.meters["visible"] += 1
    hero.memes["wonder"] += 1
    if hero.memes["fear"] > 0:
        hero.memes["fear"] -= 1
    return []


def _r_understand(world: World) -> list[str]:
    memory = world.get("memory")
    moth = world.get("moth")
    hero = world.get("hero")
    elder = world.get("elder")
    if memory.meters["shown"] < THRESHOLD or moth.meters["visible"] < THRESHOLD:
        return []
    sig = ("understand", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = 0.0
    hero.memes["understanding"] += 1
    elder.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="shiver", tag="emotional", apply=_r_shiver),
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="understand", tag="emotional", apply=_r_understand),
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
        if any(rule_sig[0] in {"shiver", "flashback", "transform", "understand"} for rule_sig in world.fired):
            changed = any(
                rule.apply(world)
                for rule in []
            )
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def combo_valid(spot: Spot, relic: Relic, moth: MothKind) -> bool:
    return (
        relic.id in spot.relics
        and moth.id in spot.moths
        and spot.id in relic.spots
        and spot.id in moth.spots
        and relic.memory_tag == moth.memory_tag
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, spot in SPOTS.items():
        for rid, relic in RELICS.items():
            for mid, moth in MOTHS.items():
                if combo_valid(spot, relic, moth):
                    combos.append((sid, rid, mid))
    return combos


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("relic").meters["sounded"] += 1
    sim.get("cocoon").meters["moonlit"] += 1
    propagate(sim, narrate=False)
    return {
        "flashback": sim.get("memory").meters["shown"] >= THRESHOLD,
        "transformed": sim.get("moth").meters["visible"] >= THRESHOLD,
        "fear_left": sim.get("hero").memes["fear"],
    }


def introduce(world: World, hero: Entity, elder: Entity, spot: Spot) -> None:
    world.say(
        f"{hero.id} was the youngest lyric-ist in the family, always listening for a line of song "
        f"where other people only heard wind. One violet evening, {hero.pronoun('subject')} walked with "
        f"{elder.label_word} into {spot.label}, where {spot.approach}."
    )


def set_goal(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} had come to find the last line of a bedtime tune {hero.pronoun('subject')} could never finish."
    )


def ghost_sign(world: World, hero: Entity, elder: Entity, spot: Spot) -> None:
    cocoon = world.get("cocoon")
    cocoon.meters["rustled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Halfway down the path, a pale shape swayed in the dark. It looked like {spot.ghost_shape}, "
        f"and a tiny glow seemed to wink between the leaves."
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f'{hero.id} stopped so fast the gravel whispered under {hero.pronoun("possessive")} shoes. '
            f'"Did you see that?" {hero.pronoun("subject")} breathed.'
        )
    world.say(
        f"{elder.label_word.capitalize()} listened instead of hurrying away. {spot.haunt}"
    )


def examine_relic(world: World, hero: Entity, elder: Entity, relic: Relic) -> None:
    pred = predict_reveal(world)
    world.facts["predicted_flashback"] = pred["flashback"]
    world.facts["predicted_transform"] = pred["transformed"]
    world.say(
        f"Near the roots lay {relic.phrase}. {elder.label_word.capitalize()} picked it up, and "
        f"{hero.id} could tell from {elder.pronoun('possessive')} face that it belonged to an old story."
    )
    if pred["flashback"]:
        world.say(
            f'"Listen," {elder.label_word} whispered. "Sometimes the dale remembers before it explains."'
        )


def sound_relic(world: World, hero: Entity, elder: Entity, relic: Relic) -> None:
    world.get("relic").meters["sounded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.label_word.capitalize()} let the {relic.label} sound once -- {relic.sound}."
    )
    if world.get("memory").meters["shown"] >= THRESHOLD:
        world.say(
            f"At once a flashback rose in {elder.label_word}'s eyes. {relic.flashback_text}"
        )
    world.say(
        f"{hero.id} felt the fear loosen a little. The pale shape no longer seemed to drift toward {hero.pronoun('object')}; "
        f"it only trembled in the branches."
    )


def invite_closer(world: World, hero: Entity, elder: Entity, moth: MothKind) -> None:
    hero.memes["courage"] += 1
    world.say(
        f'"Stay by me," said {elder.label_word}. "Ghosts do not hang by silk. Let us look with quiet eyes."'
    )
    world.say(
        f"They stepped close enough to see a white case no bigger than {hero.pronoun('possessive')} thumb: "
        f"{moth.cocoon}."
    )


def moon_reveal(world: World, hero: Entity, moth: MothKind) -> None:
    cocoon = world.get("cocoon")
    cocoon.meters["moonlit"] += 1
    propagate(world, narrate=False)
    if world.get("moth").meters["visible"] >= THRESHOLD:
        world.say(
            f"A gap opened in the clouds. Moonlight poured through, silvering the little shell, and then "
            f"{moth.emerge}."
        )
        world.say(
            f"The thing that had looked like a ghost became {moth.adult} with {moth.wings}."
        )
    if hero.memes["understanding"] >= THRESHOLD:
        world.say(
            f"{hero.id} did not hide this time. {hero.pronoun('subject').capitalize()} watched the transformation with round, shining eyes."
        )


def ending_song(world: World, hero: Entity, elder: Entity, moth: MothKind, spot: Spot) -> None:
    hero.memes["joy"] += 1
    hero.memes["song"] += 1
    elder.memes["joy"] += 1
    world.say(
        f'Then the last line of the bedtime tune came to {hero.id} at last. Softly, {hero.pronoun("subject")} sang it, '
        f"and {moth.adult} circled once above {hero.pronoun('possessive')} head as if listening."
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled and squeezed {hero.pronoun('possessive')} hand. "
        f"By the time they walked home from {spot.label}, the dale still looked deep and shadowy, "
        f"but it no longer felt haunted. It felt full of hidden lives and songs waiting to wake."
    )


def tell(
    spot: Spot,
    relic: Relic,
    moth_cfg: MothKind,
    *,
    hero_name: str = "Nell",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "listening",
) -> World:
    world = World(spot)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[trait]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    world.add(Entity(id="relic", type="relic", label=relic.label))
    world.add(Entity(id="memory", type="memory", label="old memory"))
    cocoon = world.add(Entity(id="cocoon", type="cocoon", label=moth_cfg.cocoon))
    moth = world.add(Entity(id="moth", type="moth", label=moth_cfg.adult))
    hero.attrs["display_name"] = hero_name
    elder.attrs["display_name"] = elder.label_word
    cocoon.meters["ready"] = 1.0

    world.facts.update(
        hero=hero,
        elder=elder,
        spot=spot,
        relic_cfg=relic,
        moth_cfg=moth_cfg,
        ghost_guess=spot.ghost_shape,
    )

    introduce(world, hero, elder, spot)
    set_goal(world, hero)

    world.para()
    ghost_sign(world, hero, elder, spot)
    examine_relic(world, hero, elder, relic)

    world.para()
    sound_relic(world, hero, elder, relic)
    invite_closer(world, hero, elder, moth_cfg)
    moon_reveal(world, hero, moth_cfg)

    world.para()
    ending_song(world, hero, elder, moth_cfg, spot)

    world.facts.update(
        flashback=world.get("memory").meters["shown"] >= THRESHOLD,
        transformed=world.get("moth").meters["visible"] >= THRESHOLD,
        fear_cleared=world.get("hero").memes["fear"] < THRESHOLD,
        song_found=world.get("hero").memes["song"] >= THRESHOLD,
    )
    return world


SPOTS = {
    "willow_dale": Spot(
        id="willow_dale",
        label="the willow dale",
        approach="mist lay low under the willow boughs",
        haunt="The branches kept brushing together with a sound like someone humming behind a door.",
        ghost_shape="a tiny hanging ghost in a white hood",
        relics={"locket", "reed_pipe"},
        moths={"moon_moth", "reed_moth"},
        tags={"dale", "willow"},
    ),
    "bridge_dale": Spot(
        id="bridge_dale",
        label="the old bridge above the dale",
        approach="water slipped under the stones and the rail shone with dew",
        haunt="From under the bridge came a hollow singing note that seemed to float with no singer at all.",
        ghost_shape="a little white face peering from the dark",
        relics={"bell"},
        moths={"lantern_moth"},
        tags={"dale", "bridge"},
    ),
    "reed_dale": Spot(
        id="reed_dale",
        label="the reedy edge of the dale pond",
        approach="thin mist wandered between the reeds like folded scarves",
        haunt="The reeds kept tapping one another, soft and secret, as if something there knew a tune.",
        ghost_shape="a drifting handkerchief ghost over the water",
        relics={"locket", "reed_pipe"},
        moths={"reed_moth"},
        tags={"dale", "pond"},
    ),
}

RELICS = {
    "locket": Relic(
        id="locket",
        label="silver locket",
        phrase="a small silver locket on a frayed ribbon",
        sound="ting",
        flashback_text="For one heartbeat, the night folded back. "
        "Years ago, when the elder was little, the same locket had chimed here while a grown-up said, "
        '"Do not fear every white thing in moonlight. Some of them are only waiting to become themselves."',
        spots={"willow_dale", "reed_dale"},
        memory_tag="moon_song",
        tags={"memory", "song"},
    ),
    "bell": Relic(
        id="bell",
        label="tin bell",
        phrase="a tiny tin bell green with age",
        sound="tin-tin",
        flashback_text="For one heartbeat, the old bridge looked new again. "
        "The elder remembered standing there as a child, hearing the bell ring while moths came to the lamplight like bits of paper turned alive.",
        spots={"bridge_dale"},
        memory_tag="lamplight",
        tags={"memory", "bell"},
    ),
    "reed_pipe": Relic(
        id="reed_pipe",
        label="reed pipe",
        phrase="a short reed pipe, pale and smooth from many fingers",
        sound="pee-oo",
        flashback_text="For one heartbeat, the pond was full of summer from long ago. "
        "The elder remembered blowing the same pipe and watching white cocoons tremble before small wings opened over the reeds.",
        spots={"willow_dale", "reed_dale"},
        memory_tag="reed_tune",
        tags={"memory", "music"},
    ),
}

MOTHS = {
    "moon_moth": MothKind(
        id="moon_moth",
        cocoon="a moon-moth cocoon tucked in the willow thread",
        adult="a moon moth",
        wings="round pale wings dusted like milk glass",
        emerge="the cocoon split with a paper-soft crack and a moon moth worked free",
        spots={"willow_dale"},
        memory_tag="moon_song",
        tags={"moth", "moon"},
    ),
    "lantern_moth": MothKind(
        id="lantern_moth",
        cocoon="a lantern-moth cocoon fastened under the bridge rail",
        adult="a lantern moth",
        wings="cream wings with two gold dots that shone like tiny lamps",
        emerge="the little case quivered, opened, and a lantern moth unfolded into the cold air",
        spots={"bridge_dale"},
        memory_tag="lamplight",
        tags={"moth", "light"},
    ),
    "reed_moth": MothKind(
        id="reed_moth",
        cocoon="a reed-moth cocoon tied to a stalk with shining silk",
        adult="a reed moth",
        wings="soft white wings lined with silver like moonlit water",
        emerge="the silk case stirred, peeled apart, and a reed moth climbed into the moonlight",
        spots={"willow_dale", "reed_dale"},
        memory_tag="reed_tune",
        tags={"moth", "reeds"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Tessa", "Lina", "Ivy", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Rowan", "Tobin", "Jules"]
TRAITS = ["listening", "gentle", "curious", "brave", "quiet"]
ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    spot: str
    relic: str
    moth: str
    hero_name: str
    hero_type: str
    elder_type: str
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
    "moth": [
        (
            "What is a moth?",
            "A moth is an insect with soft wings covered in tiny scales. Many moths come out in the evening and fly toward light."
        )
    ],
    "moon": [
        (
            "Why can a white moth look spooky at night?",
            "At night, moonlight can make pale wings shine very brightly. That can fool your eyes and make a small creature look ghostly for a moment."
        )
    ],
    "light": [
        (
            "Why do some insects fly toward light?",
            "Many night insects use light to help them find their way. A lamp or bright glow can confuse them and pull them closer."
        )
    ],
    "memory": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story shows a memory from earlier time. It helps you understand something happening now."
        )
    ],
    "song": [
        (
            "What does a lyric-ist do?",
            "A lyric-ist listens for words that can be sung and arranges them into lines. In a story, that can mean a child who loves making up songs."
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants with thin stems. Wind can make them tap and whisper together."
        )
    ],
    "bridge": [
        (
            "Why can a bridge sound spooky at night?",
            "Water and wind can echo under a bridge and change ordinary sounds. That makes small noises seem larger and stranger."
        )
    ],
    "willow": [
        (
            "What is special about a willow tree?",
            "A willow has long hanging branches that sway and brush together. In dim light, those branches can make a place feel secret and shadowy."
        )
    ],
}
KNOWLEDGE_ORDER = ["song", "memory", "moth", "moon", "light", "reeds", "bridge", "willow"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    spot = world.facts["spot"]
    relic = world.facts["relic_cfg"]
    moth = world.facts["moth_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that uses the words "lyric-ist", "dale", and "wink".',
        f"Tell a story about a child lyric-ist named {hero.attrs['display_name']} who walks with {elder.label_word} into {spot.label}, mistakes something pale for a ghost, and then learns the truth through a flashback and a transformation.",
        f"Write a child-facing ghost story where {relic.label} helps reveal that the scary shape is really connected to {moth.adult}, ending with a song instead of a scare.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    spot = world.facts["spot"]
    relic = world.facts["relic_cfg"]
    moth = world.facts["moth_cfg"]
    hero_name = hero.attrs["display_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a young lyric-ist, and {elder.label_word}, who walk together into {spot.label}. They begin the night looking for a song line and end it understanding a mystery."
        ),
        (
            f"Why did {hero_name} think there was a ghost?",
            f"{hero_name} saw a pale shape swaying in the dark and heard strange sounds around it, so it looked ghostly at first. The tiny glow that seemed to wink in the leaves made the scare feel even more real."
        ),
    ]
    if world.facts.get("flashback"):
        qa.append(
            (
                f"How did the flashback help {hero_name}?",
                f"When the {relic.label} sounded, it brought back an old memory for {elder.label_word}. That memory explained that the white shape was something living and waiting, so {hero_name} had a reason to look again instead of only being afraid."
            )
        )
    if world.facts.get("transformed"):
        qa.append(
            (
                "What transformed in the story?",
                f"The pale case opened and became {moth.adult}. That transformation turned the ghostly shape into a real creature, which is why the fear changed into wonder."
            )
        )
    if world.facts.get("song_found"):
        qa.append(
            (
                f"How did the story end?",
                f"It ended with {hero_name} finding the missing last line of the tune and singing softly. The walk home proved what had changed, because the dale still looked dark but no longer felt haunted."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"song", "memory", "moth"}
    spot = world.facts["spot"]
    moth = world.facts["moth_cfg"]
    relic = world.facts["relic_cfg"]
    tags |= set(spot.tags)
    tags |= set(moth.tags)
    tags |= set(relic.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spot="willow_dale",
        relic="locket",
        moth="moon_moth",
        hero_name="Nell",
        hero_type="girl",
        elder_type="grandmother",
        trait="listening",
    ),
    StoryParams(
        spot="bridge_dale",
        relic="bell",
        moth="lantern_moth",
        hero_name="Owen",
        hero_type="boy",
        elder_type="grandfather",
        trait="curious",
    ),
    StoryParams(
        spot="reed_dale",
        relic="reed_pipe",
        moth="reed_moth",
        hero_name="Mira",
        hero_type="girl",
        elder_type="grandmother",
        trait="quiet",
    ),
    StoryParams(
        spot="willow_dale",
        relic="reed_pipe",
        moth="reed_moth",
        hero_name="Rowan",
        hero_type="boy",
        elder_type="grandfather",
        trait="brave",
    ),
]


def explain_rejection(spot: Spot, relic: Relic, moth: MothKind) -> str:
    reasons: list[str] = []
    if relic.id not in spot.relics or spot.id not in relic.spots:
        reasons.append(f"{relic.label} does not belong naturally at {spot.label}")
    if moth.id not in spot.moths or spot.id not in moth.spots:
        reasons.append(f"{moth.adult} does not belong naturally at {spot.label}")
    if relic.memory_tag != moth.memory_tag:
        reasons.append("the relic's remembered song does not match the creature it is meant to explain")
    if not reasons:
        reasons.append("that combination does not make a coherent haunted misunderstanding here")
    return "(No story: " + "; ".join(reasons) + ".)"


ASP_RULES = r"""
compatible_place(S,R,M) :- spot(S), relic(R), moth(M), spot_has_relic(S,R), spot_has_moth(S,M),
                           relic_at(R,S), moth_at(M,S), memory_tag(R,T), memory_tag(M,T).
valid(S,R,M) :- compatible_place(S,R,M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for rid in sorted(spot.relics):
            lines.append(asp.fact("spot_has_relic", sid, rid))
        for mid in sorted(spot.moths):
            lines.append(asp.fact("spot_has_moth", sid, mid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("memory_tag", rid, relic.memory_tag))
        for sid in sorted(relic.spots):
            lines.append(asp.fact("relic_at", rid, sid))
    for mid, moth in MOTHS.items():
        lines.append(asp.fact("moth", mid))
        lines.append(asp.fact("memory_tag", mid, moth.memory_tag))
        for sid in sorted(moth.spots):
            lines.append(asp.fact("moth_at", mid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded on a curated story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story from default-resolve smoke test")
        print("OK: default resolve/generate smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lyric-ist in a haunted-looking dale learns that a ghostly shape is really a waiting moth."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--moth", choices=MOTHS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.relic and args.moth:
        if not combo_valid(SPOTS[args.spot], RELICS[args.relic], MOTHS[args.moth]):
            raise StoryError(explain_rejection(SPOTS[args.spot], RELICS[args.relic], MOTHS[args.moth]))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.relic is None or combo[1] == args.relic)
        and (args.moth is None or combo[2] == args.moth)
    ]
    if not combos:
        if args.spot and args.relic and not args.moth:
            spot = SPOTS[args.spot]
            relic = RELICS[args.relic]
            moth = next(iter(MOTHS.values()))
            raise StoryError(explain_rejection(spot, relic, moth))
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, relic_id, moth_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        spot=spot_id,
        relic=relic_id,
        moth=moth_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
    )


def _get_or_fail(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    spot = _get_or_fail(SPOTS, params.spot, "spot")
    relic = _get_or_fail(RELICS, params.relic, "relic")
    moth = _get_or_fail(MOTHS, params.moth, "moth")
    if not combo_valid(spot, relic, moth):
        raise StoryError(explain_rejection(spot, relic, moth))
    world = tell(
        spot,
        relic,
        moth,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        trait=params.trait,
    )
    world.facts["params"] = params
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, relic, moth) combos:\n")
        for spot, relic, moth in combos:
            print(f"  {spot:12} {relic:10} {moth}")
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
            header = f"### {p.hero_name}: {p.spot} / {p.relic} / {p.moth}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
