#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/signal_serpentine_comedian_rhyme_ghost_story.py
==========================================================================

A small storyworld about a child who follows a spooky signal and meets a
friendly comedian ghost with a serpentine scarf caught in the wrong place.

The world model keeps track of:
- physical state: cold air, a caught scarf, whether the ghost is freed
- emotional state: fear, wonder, relief, hope, joy

Every story moves through:
1. a spooky beginning with a signal in a creaky place
2. a middle turn where the child discovers the ghost is stuck, not mean
3. a resolution where the child tries a fitting tool
4. an ending image that proves the place feels different

The "Rhyme" feature is built into the ghost's clues and the child's reply.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Place:
    id: str
    label: str
    intro: str
    path: str
    ending: str
    affords: set[str] = field(default_factory=set)
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
class SignalCfg:
    id: str
    label: str
    sound: str
    line: str
    clue: str
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
class SnagCfg:
    id: str
    label: str
    phrase: str
    site: str
    need: str
    height: int
    severity: int
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
class AidCfg:
    id: str
    label: str
    phrase: str
    action: str
    reach: int
    power: int
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


def _r_signal_chill(world: World) -> list[str]:
    room = world.get("room")
    hero = world.get("hero")
    ghost = world.get("ghost")
    if room.meters["signal_on"] < THRESHOLD:
        return []
    sig = ("signal_chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    hero.memes["fear"] += 1
    hero.memes["wonder"] += 1
    ghost.memes["hope"] += 1
    return []


def _r_freed_relief(world: World) -> list[str]:
    ghost = world.get("ghost")
    hero = world.get("hero")
    room = world.get("room")
    if ghost.meters["freed"] < THRESHOLD:
        return []
    sig = ("freed_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    ghost.memes["joy"] += 1
    room.meters["cold"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="signal_chill", tag="spooky", apply=_r_signal_chill),
    Rule(name="freed_relief", tag="resolution", apply=_r_freed_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def aid_fits(aid: AidCfg, snag: SnagCfg) -> bool:
    return aid.action == snag.need and aid.reach >= snag.height


def valid_combo(place: Place, signal: SignalCfg, snag: SnagCfg, aid: AidCfg) -> bool:
    return signal.id in place.affords and snag.id in place.affords and aid_fits(aid, snag)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for signal_id, signal in SIGNALS.items():
            for snag_id, snag in SNAGS.items():
                for aid_id, aid in AIDS.items():
                    if valid_combo(place, signal, snag, aid):
                        out.append((place_id, signal_id, snag_id, aid_id))
    return out


def ghost_severity(snag: SnagCfg, delay: int) -> int:
    return snag.severity + delay


def is_success(aid: AidCfg, snag: SnagCfg, delay: int) -> bool:
    return aid.power >= ghost_severity(snag, delay)


def predict_outcome(world: World, aid: AidCfg, snag: SnagCfg, delay: int) -> dict:
    sim = world.copy()
    ghost = sim.get("ghost")
    if is_success(aid, snag, delay):
        ghost.meters["freed"] += 1
        propagate(sim, narrate=False)
    else:
        ghost.meters["freed"] += 0
        ghost.meters["fading"] += 1
        sim.get("room").meters["cold"] += 1
    return {
        "success": ghost.meters["freed"] >= THRESHOLD,
        "cold": sim.get("room").meters["cold"],
    }


def introduce(world: World, hero: Entity, grownup: Entity, place: Place) -> None:
    world.say(
        f"One misty evening, {hero.id} was with {hero.pronoun('possessive')} "
        f"{grownup.label_word} near {place.label}. {place.intro}"
    )


def open_signal(world: World, hero: Entity, place: Place, signal: SignalCfg) -> None:
    room = world.get("room")
    room.meters["signal_on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a strange signal rose out of the dimness: {signal.sound}. "
        f"{signal.line}"
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id} felt a small shiver, but wonder tugged just as hard."
        )
    world.say(f"{hero.id} followed {place.path} toward the sound.")


def discover_ghost(world: World, hero: Entity, ghost: Entity, snag: SnagCfg) -> None:
    ghost.meters["caught"] += 1
    ghost.memes["embarrassed"] += 1
    world.say(
        f"Behind the gloom, {hero.id} found not a monster but a pale little ghost "
        f"with a comedian's smile. A long serpentine scarf of moon-white cloth "
        f"was caught on {snag.phrase} at {snag.site}."
    )
    world.say(
        f'The ghost bowed as well as {ghost.pronoun()} could and whispered, '
        f'"I meant to make a joke, not croak. I sent a signal because I am stuck."'
    )


def rhyme_clue(
    world: World,
    hero: Entity,
    grownup: Entity,
    ghost: Entity,
    signal: SignalCfg,
    aid: AidCfg,
    snag: SnagCfg,
    delay: int,
) -> None:
    pred = predict_outcome(world, aid, snag, delay)
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_success"] = pred["success"]
    hero.memes["care"] += 1
    ghost.memes["hope"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} came close enough to see the trouble and '
        f'held the {aid.label} out to {hero.id}.'
    )
    world.say(
        f'"If we are gentle, we can help," {grownup.pronoun()} said.'
    )
    world.say(
        f'The ghost tried another rhyme: "{signal.clue} '
        f'Lift with care, if you dare."'
    )


def try_help(world: World, hero: Entity, aid: AidCfg, snag: SnagCfg) -> None:
    hero.meters["reaching"] += 1
    world.say(
        f"{hero.id} took {aid.phrase} and reached toward {snag.phrase}. "
        f"{aid.action.capitalize()} was exactly what the moment called for."
    )


def free_ghost(
    world: World,
    hero: Entity,
    ghost: Entity,
    snag: SnagCfg,
    aid: AidCfg,
    place: Place,
) -> None:
    ghost.meters["caught"] = 0.0
    ghost.meters["freed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With one careful try, {hero.id} used the {aid.label} to ease the "
        f"serpentine scarf free from {snag.phrase}. The cold in the air softened "
        f"at once."
    )
    world.say(
        f'The comedian ghost spun in a tiny happy loop and laughed, '
        f'"Snag to free, gloom to glee! Thank you for helping me."'
    )
    world.say(
        f"Soon {place.ending} The ghost's smile made the old shadows feel smaller."
    )


def ghost_show(world: World, hero: Entity, grownup: Entity, ghost: Entity, signal: SignalCfg) -> None:
    hero.memes["joy"] += 1
    ghost.memes["performing"] += 1
    world.say(
        f'Then the ghost gave a soft, silly show. {signal.sound.capitalize()} '
        f'became part of the act instead of a warning, and even '
        f'{grownup.label_word} laughed.'
    )
    world.say(
        f"{hero.id} laughed too, because the scary signal had turned into a funny song "
        f"with a friendly ghost keeping rhyme."
    )


def fail_help(
    world: World,
    hero: Entity,
    ghost: Entity,
    grownup: Entity,
    snag: SnagCfg,
    aid: AidCfg,
) -> None:
    ghost.meters["fading"] += 1
    world.get("room").meters["cold"] += 1
    hero.memes["sadness"] += 1
    ghost.memes["hope"] -= 1
    world.say(
        f"{hero.id} tried with the {aid.label}, but {snag.phrase} was too awkward "
        f"and too tight. The serpentine scarf tugged back, and the ghost gave a small sigh."
    )
    world.say(
        f'{grownup.label_word.capitalize()} squeezed {hero.id}\'s shoulder. '
        f'"You were kind to try," {grownup.pronoun()} said.'
    )
    world.say(
        f'The comedian ghost managed one last rhyme: "Kind heart, bright part. '
        f'You helped, though we must part."'
    )


def wistful_end(world: World, hero: Entity, place: Place, signal: SignalCfg) -> None:
    world.say(
        f"The little ghost floated away into the gray, leaving only a faint "
        f"{signal.label} and a silver thread on the floor."
    )
    world.say(
        f"After that, {hero.id} still remembered {place.label} as spooky, but not cruel. "
        f"The place felt full of lonely stories, and one of them had smiled back."
    )


def tell(
    place: Place,
    signal: SignalCfg,
    snag: SnagCfg,
    aid: AidCfg,
    child_name: str = "Nora",
    child_gender: str = "girl",
    grownup_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    grownup = world.add(
        Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up")
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
            traits=["friendly", "comedian"],
            attrs={"comedian": True},
        )
    )
    room = world.add(Entity(id="room", type="place", label=place.label))

    room.meters["signal_on"] = 0.0
    room.meters["cold"] = 0.0
    ghost.meters["caught"] = 0.0
    ghost.meters["freed"] = 0.0
    ghost.meters["fading"] = 0.0
    hero.meters["reaching"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["sadness"] = 0.0
    ghost.memes["hope"] = 0.0
    ghost.memes["joy"] = 0.0
    ghost.memes["embarrassed"] = 0.0
    ghost.memes["performing"] = 0.0

    introduce(world, hero, grownup, place)
    open_signal(world, hero, place, signal)

    world.para()
    discover_ghost(world, hero, ghost, snag)
    rhyme_clue(world, hero, grownup, ghost, signal, aid, snag, delay)

    world.para()
    try_help(world, hero, aid, snag)
    success = is_success(aid, snag, delay)
    if success:
        free_ghost(world, hero, ghost, snag, aid, place)
        world.para()
        ghost_show(world, hero, grownup, ghost, signal)
        outcome = "glee"
    else:
        fail_help(world, hero, ghost, grownup, snag, aid)
        world.para()
        wistful_end(world, hero, place, signal)
        outcome = "wistful"

    world.facts.update(
        hero=hero,
        grownup=grownup,
        ghost=ghost,
        room=room,
        place=place,
        signal=signal,
        snag=snag,
        aid=aid,
        delay=delay,
        outcome=outcome,
        success=success,
        comedian=bool(ghost.attrs.get("comedian")),
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic stairs",
        intro="The boards creaked, and the dusty air smelled like old trunks and rain.",
        path="the crooked attic stairs",
        ending="the attic stairs looked less like a mouth in the dark and more like a place that had been waiting for laughter",
        affords={"bell", "trunk_latch", "stool"},
        tags={"attic", "dark"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        intro="The porch roof dripped softly, and the wind pushed shadows under the rails.",
        path="the dripping porch boards",
        ending="the porch no longer seemed haunted by trouble, only hushed by night",
        affords={"window_tap", "railing", "umbrella"},
        tags={"porch", "night"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the old greenhouse",
        intro="Glass panes shone like dim eyes, and ivy pressed wet leaves against them.",
        path="the narrow stone path to the greenhouse",
        ending="the greenhouse glimmered softly, as if the moon had learned a joke",
        affords={"lantern_blink", "ivy_hook", "shears"},
        tags={"greenhouse", "ivy"},
    ),
}

SIGNALS = {
    "bell": SignalCfg(
        id="bell",
        label="bell signal",
        sound="a tiny bell rang three times",
        line="It was not loud, but it sounded very sure, as if someone wanted to be found.",
        clue="Ring, ring, near the string.",
        tags={"signal", "bell"},
    ),
    "window_tap": SignalCfg(
        id="window_tap",
        label="tapping signal",
        sound="tap-tap on the window glass",
        line="The taps came in a neat little pattern, almost like knuckles telling a secret.",
        clue="Tap in the night, set the knot right.",
        tags={"signal", "tap"},
    ),
    "lantern_blink": SignalCfg(
        id="lantern_blink",
        label="blinking signal",
        sound="a lantern blinked on and off in the mist",
        line="The light winked patiently, like an eye that hoped not to frighten anyone.",
        clue="Blink and see where I cannot be free.",
        tags={"signal", "lantern"},
    ),
}

SNAGS = {
    "trunk_latch": SnagCfg(
        id="trunk_latch",
        label="trunk latch",
        phrase="the brass latch of an old trunk",
        site="the top landing",
        need="lift",
        height=1,
        severity=1,
        tags={"trunk", "snag"},
    ),
    "railing": SnagCfg(
        id="railing",
        label="porch railing",
        phrase="the splintery porch railing",
        site="the far corner of the porch",
        need="hook",
        height=2,
        severity=2,
        tags={"railing", "snag"},
    ),
    "ivy_hook": SnagCfg(
        id="ivy_hook",
        label="ivy hook",
        phrase="an iron hook buried under thick ivy",
        site="the back wall of the greenhouse",
        need="snip",
        height=2,
        severity=2,
        tags={"ivy", "snag"},
    ),
}

AIDS = {
    "stool": AidCfg(
        id="stool",
        label="stool",
        phrase="a small wooden stool",
        action="lift",
        reach=1,
        power=2,
        tags={"stool", "help"},
    ),
    "umbrella": AidCfg(
        id="umbrella",
        label="umbrella",
        phrase="a closed umbrella with a curved handle",
        action="hook",
        reach=2,
        power=2,
        tags={"umbrella", "help"},
    ),
    "shears": AidCfg(
        id="shears",
        label="garden shears",
        phrase="a pair of garden shears",
        action="snip",
        reach=2,
        power=3,
        tags={"shears", "help"},
    ),
    "teaspoon": AidCfg(
        id="teaspoon",
        label="teaspoon",
        phrase="a shiny teaspoon",
        action="lift",
        reach=0,
        power=0,
        tags={"teaspoon"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ava", "Zoe", "Clara", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Leo", "Max", "Sam", "Ben", "Eli", "Noah", "Finn"]


KNOWLEDGE = {
    "signal": [
        (
            "What is a signal?",
            "A signal is a sign that means something or asks someone to notice. It can be a sound, a light, or a little pattern."
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale with spooky feelings, dark places, and something mysterious. It does not have to be cruel to be a ghost story."
        )
    ],
    "comedian": [
        (
            "What is a comedian?",
            "A comedian is someone who tries to make people laugh. They use jokes, funny faces, or silly surprises."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like light and night. Rhymes can make a clue or a song easier to remember."
        )
    ],
    "ivy": [
        (
            "What is ivy?",
            "Ivy is a climbing plant with many leaves. It can spread over walls and hooks and tangle around things."
        )
    ],
    "bell": [
        (
            "Why does a bell make a good signal?",
            "A bell can be heard from far away, even in dim light. That makes it useful when someone wants to be found."
        )
    ],
    "lantern": [
        (
            "Why can a lantern be used as a signal?",
            "A lantern makes a small light that people can see in the dark. Blinking it on and off can send a message."
        )
    ],
    "shears": [
        (
            "What are garden shears for?",
            "Garden shears are used to cut stems and leaves. Grown-ups use them carefully to trim plants."
        )
    ],
    "umbrella": [
        (
            "How can an umbrella help reach something?",
            "A closed umbrella with a curved handle can catch or hook something gently. Its long shape lets you reach farther."
        )
    ],
    "stool": [
        (
            "Why does a stool help with high places?",
            "A stool lifts you up a little so your hands can reach better. It is useful when something is just out of reach."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "signal",
    "ghost",
    "comedian",
    "rhyme",
    "bell",
    "lantern",
    "ivy",
    "shears",
    "umbrella",
    "stool",
]


@dataclass
class StoryParams:
    place: str
    signal: str
    snag: str
    aid: str
    child_name: str
    child_gender: str
    grownup: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    signal = f["signal"]
    snag = f["snag"]
    outcome = f["outcome"]
    base = (
        f'Write a ghost story for a 3-to-5-year-old that includes the words '
        f'"signal", "serpentine", and "comedian", and uses rhyme.'
    )
    if outcome == "glee":
        return [
            base,
            f"Tell a gentle ghost story where {hero.id} follows a spooky {signal.label} at {place.label} and finds a friendly comedian ghost with a serpentine scarf caught on {snag.label}.",
            "Write a spooky-but-kind story where a child solves a ghost's problem, and the scary feeling turns into laughter at the end.",
        ]
    return [
        base,
        f"Tell a wistful ghost story where {hero.id} follows a spooky {signal.label} at {place.label} and tries to help a friendly comedian ghost with a serpentine scarf.",
        "Write a child-friendly ghost story with rhyme where a child is brave and kind even though the ending stays a little sad and mysterious.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    place = f["place"]
    signal = f["signal"]
    snag = f["snag"]
    aid = f["aid"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} {grownup.label_word}, and a friendly ghost who acts like a comedian. The story begins when they notice a strange signal in the dark."
        ),
        (
            "What made the place feel spooky at first?",
            f"The place felt spooky because {signal.sound} came out of the dimness, and the air turned cold. That signal made {hero.id} feel both fear and wonder at the same time."
        ),
        (
            "What was wrong with the ghost?",
            f"The ghost was not trying to scare anyone on purpose. {hero.pronoun('capitalize') if False else ''}"
        ),
    ]
    qa[-1] = (
        "What was wrong with the ghost?",
        f"The ghost's long serpentine scarf was caught on {snag.phrase}. That is why the ghost sent a signal instead of simply floating away."
    )
    qa.append(
        (
            f"Why did {hero.id} use the {aid.label}?",
            f"{hero.id} used the {aid.label} because it matched the problem at {snag.site}. It was the best tool to try for that kind of snag."
        )
    )
    if outcome == "glee":
        qa.append(
            (
                "How did the story change from scary to happy?",
                f"The story changed when {hero.id} freed the ghost and the cold feeling went away. After that, the comedian ghost turned the spooky signal into a funny little show with rhyme."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with laughter in a place that had seemed haunted before. The ending image shows that the shadows felt smaller because the ghost was safe and smiling."
            )
        )
    else:
        qa.append(
            (
                "Did the child help even though the ending was sadder?",
                f"Yes. {hero.id} was still brave and kind, and the ghost thanked {hero.pronoun('object')} in rhyme. Even though the scarf stayed caught, the ghost left knowing someone had cared."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the ghost drifting away and the signal growing faint. The place still felt spooky, but it no longer felt cruel, because {hero.id} had answered the call kindly."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"signal", "ghost", "comedian", "rhyme"}
    tags |= set(world.facts["signal"].tags)
    tags |= set(world.facts["snag"].tags)
    tags |= set(world.facts["aid"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        signal="bell",
        snag="trunk_latch",
        aid="stool",
        child_name="Nora",
        child_gender="girl",
        grownup="grandmother",
        delay=0,
    ),
    StoryParams(
        place="porch",
        signal="window_tap",
        snag="railing",
        aid="umbrella",
        child_name="Theo",
        child_gender="boy",
        grownup="father",
        delay=0,
    ),
    StoryParams(
        place="greenhouse",
        signal="lantern_blink",
        snag="ivy_hook",
        aid="shears",
        child_name="Mina",
        child_gender="girl",
        grownup="grandfather",
        delay=1,
    ),
    StoryParams(
        place="attic",
        signal="bell",
        snag="trunk_latch",
        aid="stool",
        child_name="Ben",
        child_gender="boy",
        grownup="mother",
        delay=2,
    ),
]


def explain_rejection(place: Optional[Place], signal: Optional[SignalCfg], snag: Optional[SnagCfg], aid: Optional[AidCfg]) -> str:
    if place and signal and signal.id not in place.affords:
        return f"(No story: {place.label} is not where this kind of signal belongs in this world.)"
    if place and snag and snag.id not in place.affords:
        return f"(No story: {snag.label} does not belong in {place.label} here.)"
    if aid and snag and not aid_fits(aid, snag):
        return (
            f"(No story: the {aid.label} cannot reasonably solve {snag.label}. "
            f"It needs {snag.need} and enough reach.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    return "glee" if is_success(AIDS[params.aid], SNAGS[params.snag], params.delay) else "wistful"


ASP_RULES = r"""
fits(Aid, Snag) :- aid(Aid), snag(Snag), action(Aid, Need), need(Snag, Need),
                   reach(Aid, R), height(Snag, H), R >= H.
valid(Place, Sig, Snag, Aid) :- place(Place), signal(Sig), snag(Snag), aid(Aid),
                                affords(Place, Sig), affords(Place, Snag), fits(Aid, Snag).

severity_value(S + D) :- chosen_snag(Sn), snag_severity(Sn, S), delay(D).
success :- chosen_aid(A), aid_power(A, P), severity_value(V), P >= V.
outcome(glee) :- success.
outcome(wistful) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for item in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, item))
    for signal_id in SIGNALS:
        lines.append(asp.fact("signal", signal_id))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("need", snag_id, snag.need))
        lines.append(asp.fact("height", snag_id, snag.height))
        lines.append(asp.fact("snag_severity", snag_id, snag.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("action", aid_id, aid.action))
        lines.append(asp.fact("reach", aid_id, aid.reach))
        lines.append(asp.fact("aid_power", aid_id, aid.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_snag", params.snag),
            asp.fact("chosen_aid", params.aid),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = cases[0]
        smoke = generate(smoke_params)
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="smoke")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a spooky signal, a serpentine snag, and a comedian ghost."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the ghost stays caught before help arrives")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    signal = SIGNALS.get(args.signal) if args.signal else None
    snag = SNAGS.get(args.snag) if args.snag else None
    aid = AIDS.get(args.aid) if args.aid else None

    if any(x is not None for x in (place, signal, snag, aid)):
        if place and signal and signal.id not in place.affords:
            raise StoryError(explain_rejection(place, signal, snag, aid))
        if place and snag and snag.id not in place.affords:
            raise StoryError(explain_rejection(place, signal, snag, aid))
        if aid and snag and not aid_fits(aid, snag):
            raise StoryError(explain_rejection(place, signal, snag, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.signal is None or combo[1] == args.signal)
        and (args.snag is None or combo[2] == args.snag)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, signal_id, snag_id, aid_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        signal=signal_id,
        snag=snag_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=child_gender,
        grownup=grownup,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        signal = SIGNALS[params.signal]
        snag = SNAGS[params.snag]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(place, signal, snag, aid):
        raise StoryError(explain_rejection(place, signal, snag, aid))

    world = tell(
        place=place,
        signal=signal,
        snag=snag,
        aid=aid,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, signal, snag, aid) combos:\n")
        for place, signal, snag, aid in combos:
            print(f"  {place:10} {signal:14} {snag:12} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.child_name}: {p.place} / {p.signal} / {p.snag} / "
                f"{p.aid} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
