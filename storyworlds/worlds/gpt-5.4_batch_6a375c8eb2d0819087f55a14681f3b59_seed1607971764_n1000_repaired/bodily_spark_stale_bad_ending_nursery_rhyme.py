#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py
============================================================================

A standalone storyworld for a cautionary nursery-rhyme-flavored tale:

A pair of children in a nursery feel a bodily chill in stale air, want a spark
for light and warmth, and one child reaches for a forbidden fire-making thing.
Dry nursery stuff catches. A grown-up may stop the blaze before the whole room
goes, or arrive too late -- but every valid story keeps its promised bad ending:
something precious is lost, and the last image proves the game is over.

The domain is intentionally small and constraint-checked:
- only some settings contain some risky targets
- only dry, stale targets can honestly catch from a spark
- low-sense responses are known but refused
- the ASP twin matches the Python gate and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/bodily_spark_stale_bad_ending_nursery_rhyme.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_spark: bool = False
    nearby: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "nurse", "woman"}
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
class Setting:
    id: str
    place: str
    opening: str
    play: str
    dark_spot: str
    rhyme_close: str
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
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    cry: str
    sound: str
    lesson: str
    makes_spark: bool = True
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
class Target:
    id: str
    label: str
    the: str
    near: str
    spread: int
    flammable: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    forbidden: str
    target: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    caregiver: str
    trait: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        if "keepsake" in world.entities and world.get("keepsake").nearby:
            world.get("keepsake").meters["ruined"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic nursery",
        opening="In the attic nursery, under a moon thin and milky, the rafters hummed a tiny tune.",
        play="They played at queens and kittens among the boxes and the cradle.",
        dark_spot="the eaves behind the cradle",
        rhyme_close="No one sang in the attic nursery after that night.",
        affords={"straw_pallet", "rush_mat", "muslin_drape"},
        tags={"nursery"},
    ),
    "cottage": Setting(
        id="cottage",
        place="the cottage nursery",
        opening="In the cottage nursery, where the window latch clicked, the shadows lay long and slick.",
        play="They played at lambs and lullabies beside the rocker and the stool.",
        dark_spot="the dim corner by the rocker",
        rhyme_close="The cottage nursery stood dark and shut for many days.",
        affords={"rush_mat", "muslin_drape"},
        tags={"nursery"},
    ),
    "loft": Setting(
        id="loft",
        place="the loft nursery",
        opening="In the loft nursery, above the hens and hay, the nursery clock went tick-a-day.",
        play="They played at mice and moonboats near a little painted chest.",
        dark_spot="the far nook under the sloped roof",
        rhyme_close="The loft nursery lost its bedtime sweetness there.",
        affords={"straw_pallet", "muslin_drape"},
        tags={"nursery"},
    ),
}

FORBIDDEN = {
    "flint": Forbidden(
        id="flint",
        label="the flint striker",
        phrase="the flint striker",
        where="on the mantel ledge",
        cry="A spark!",
        sound="tik-tik",
        lesson="flint sparks are not for children",
        plural=False,
        tags={"spark", "fire"},
    ),
    "matches": Forbidden(
        id="matches",
        label="the matchbox",
        phrase="the matchbox",
        where="in the sewing drawer",
        cry="A spark!",
        sound="scritch",
        lesson="matches are not for children",
        plural=False,
        tags={"spark", "matches", "fire"},
    ),
    "ember_poker": Forbidden(
        id="ember_poker",
        label="the hearth poker",
        phrase="the hearth poker with a live ember on its tip",
        where="by the fender",
        cry="A spark!",
        sound="tink",
        lesson="hot pokers are not for children",
        plural=False,
        tags={"spark", "fire"},
    ),
}

TARGETS = {
    "straw_pallet": Target(
        id="straw_pallet",
        label="stale straw pallet",
        the="the stale straw pallet",
        near="the stale straw at the pallet's edge",
        spread=3,
        flammable=True,
        tags={"stale", "straw", "flammable"},
    ),
    "rush_mat": Target(
        id="rush_mat",
        label="stale rush mat",
        the="the stale rush mat",
        near="the stale rushes woven through the mat",
        spread=2,
        flammable=True,
        tags={"stale", "mat", "flammable"},
    ),
    "muslin_drape": Target(
        id="muslin_drape",
        label="stale muslin drape",
        the="the stale muslin drape",
        near="the dry fold of the stale muslin",
        spread=2,
        flammable=True,
        tags={"stale", "cloth", "flammable"},
    ),
    "stone_tiles": Target(
        id="stone_tiles",
        label="stone tiles",
        the="the stone tiles",
        near="the cold stone",
        spread=0,
        flammable=False,
        tags={"stone"},
    ),
}

RESPONSES = {
    "blanket": Response(
        id="blanket",
        sense=3,
        power=3,
        text="snatched up a wool blanket and pressed the flames flat until only smoke was left",
        fail="threw a wool blanket over the flames, but the fire had already licked past its edges",
        qa_text="smothered the flames under a wool blanket",
        tags={"blanket", "fire"},
    ),
    "water_pitcher": Response(
        id="water_pitcher",
        sense=2,
        power=2,
        text="seized the wash pitcher and poured the water hard and fast over the fire",
        fail="splashed the wash pitcher over the fire, but the blaze only spat and climbed",
        qa_text="poured a wash pitcher over the fire",
        tags={"water", "fire"},
    ),
    "stomp": Response(
        id="stomp",
        sense=2,
        power=1,
        text="beat the flames down with quick, stamping feet and a heavy cloth",
        fail="stamped and beat at the fire, but sparks skipped away too quickly",
        qa_text="stamped the small flames down with a heavy cloth",
        tags={"stomp", "fire"},
    ),
    "fan": Response(
        id="fan",
        sense=1,
        power=0,
        text="fanned at the smoke with an apron",
        fail="fanned at the smoke with an apron, only feeding the fire fresh air",
        qa_text="fanned at the smoke with an apron",
        tags={"fire"},
    ),
}

GIRL_NAMES = ["May", "Nell", "Rose", "Mina", "Lucy", "Ada", "Bess"]
BOY_NAMES = ["Tom", "Ned", "Finn", "Kit", "Robin", "Sam", "Hugh"]
TRAITS = ["careful", "soft-voiced", "thoughtful", "cautious", "timid", "sensible"]

KNOWLEDGE = {
    "spark": [
        (
            "What is a spark?",
            "A spark is a tiny hot bit of fire or light. Even a very small spark can start a much bigger fire if it lands on dry things."
        )
    ],
    "stale": [
        (
            "What does stale mean?",
            "Stale means old, dry, or no longer fresh. Stale cloth or straw can feel lifeless and may burn more easily than fresh damp things."
        )
    ],
    "straw": [
        (
            "Why can straw catch fire quickly?",
            "Straw is thin and dry, so heat moves through it fast. That lets a little flame grow quickly into a bigger one."
        )
    ],
    "matches": [
        (
            "Why should children not play with matches?",
            "Matches make real fire. A child can lose control of that fire before there is time to stop it."
        )
    ],
    "blanket": [
        (
            "How can a blanket stop a small fire?",
            "A thick blanket can press out a small fire by cutting off the air it needs. A grown-up has to do it quickly and carefully."
        )
    ],
    "water": [
        (
            "Why does water sometimes put a fire out?",
            "Water cools many ordinary fires and can stop the heat from spreading. But a grown-up still has to act fast, because some fires grow too quickly."
        )
    ],
    "fire": [
        (
            "What should you do if something catches fire?",
            "Move away and call for a grown-up right away. Getting help fast is safer than trying to be brave with fire."
        )
    ],
}
KNOWLEDGE_ORDER = ["spark", "stale", "straw", "matches", "blanket", "water", "fire"]


def hazard_at_risk(setting: Setting, forbidden: Forbidden, target: Target) -> bool:
    return (
        forbidden.makes_spark
        and target.flammable
        and target.id in setting.affords
    )


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for fid, forbidden in FORBIDDEN.items():
            for tid, target in TARGETS.items():
                if hazard_at_risk(setting, forbidden, target):
                    combos.append((sid, fid, tid))
    return combos


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    target_ent = sim.get(target_id)
    target_ent.meters["burning"] += 1
    propagate(sim, narrate=False)
    return {
        "ignites": target_ent.meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "ruined": sim.get("keepsake").meters["ruined"],
    }


def introduce(world: World, setting: Setting, a: Entity, b: Entity, target: Target) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(setting.opening)
    world.say(
        f"The nursery air was stale and still, and a bodily shiver ran through {a.id} and {b.id}."
    )
    world.say(
        f"{setting.play} Yet {setting.dark_spot} looked dark as a pocket, and {target.the} lay there dry and old."
    )


def need_light(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f'"If only that nook had a star," said {a.id}. "{setting.dark_spot.capitalize()} is too dark for our game."'
    )
    world.say(
        f'{b.id} rubbed {b.pronoun("possessive")} hands and nodded. "It is cold and dim," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'{a.id} tipped up a grin. "{forbidden.cry} I saw {forbidden.phrase} {forbidden.where}."'
    )
    world.say("For one foolish beat, the idea seemed bright as a rhyme.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, target: Target, caregiver: Entity) -> None:
    pred = predict_fire(world, "target")
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_ruined"] = pred["ruined"]
    b.memes["caution"] += 1
    extra = ""
    if "careful" in b.traits or "cautious" in b.traits or "sensible" in b.traits:
        extra = f" {b.pronoun().capitalize()} sounded certain, not small."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. {forbidden.lesson.capitalize()}, and {target.the} would catch at once."{extra}'
    )
    world.say(
        f'"Call {caregiver.label_word} for a lamp instead," {b.pronoun()} said.'
    )


def defy(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'But {a.id} was already on tiptoe for {forbidden.label}, with mischief quicker than sense.'
    )


def ignite(world: World, forbidden: Forbidden, target: Target) -> None:
    tgt = world.get("target")
    tgt.meters["burning"] += 1
    tgt.meters["scorched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{forbidden.sound}! Out jumped a spark, no bigger than a bead. Then it kissed {target.near}, and the dark began to feed."
    )
    world.say(
        f"{target.The} glimmered, then crackled, then burned in a hungry line."
    )


def alarm(world: World, a: Entity, b: Entity, target: Target, caregiver: Entity) -> None:
    world.say(f'"{a.id}! {target.The} is on fire!" cried {b.id}.')
    world.say(f'"{caregiver.label_word.capitalize()}! Come quick!"')


def rescue_success(world: World, caregiver: Entity, response: Response, target: Target) -> None:
    world.get("target").meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{caregiver.label_word.capitalize()} came with a thud of feet and {response.text}."
    )
    world.say(
        "The flames died down, but smoke curled blackly along the nursery wall."
    )


def bitter_result(world: World, caregiver: Entity, a: Entity, b: Entity, setting: Setting, forbidden: Forbidden, target: Target) -> None:
    for kid in (a, b):
        kid.memes["sorrow"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"On the sill lay their little rhyme book, its pages curled and brown. The game was saved from becoming a greater fire, but the song book was gone."
    )
    world.say(
        f'{caregiver.label_word.capitalize()} held them close and said, "{forbidden.lesson.capitalize()}. A spark is tiny only at the start."'
    )
    world.say(
        f"By bedtime the room smelled wet and bitter, {target.the} was only a blackened heap, and {setting.rhyme_close}"
    )


def rescue_fail(world: World, caregiver: Entity, response: Response, target: Target) -> None:
    world.get("room").meters["burning"] += 1
    world.get("room").meters["danger"] += 1
    world.get("target").meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{caregiver.label_word.capitalize()} rushed in and {response.fail}."
    )
    world.say(
        f"The fire skipped from {target.the} to the curtains and the painted chest."
    )


def escape_and_loss(world: World, caregiver: Entity, a: Entity, b: Entity, setting: Setting, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["sorrow"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] += 1
    world.say(
        f"There was no more play to be played. {caregiver.label_word.capitalize()} gathered {a.id} and {b.id} and hurried them down the stairs into the night air."
    )
    world.say(
        "Behind them the nursery windows flashed orange, and the little rhyme book, the cradle quilt, and the painted chest were lost to smoke."
    )
    world.say(
        f'On the cold step {a.id} wept, and {b.id} hid {b.pronoun("possessive")} face. "{forbidden.lesson.capitalize()}," said {caregiver.label_word}, with a voice as tired as ash.'
    )
    world.say(
        f"By morning the nursery was charred and hollow, and {setting.rhyme_close}"
    )


def tell(
    setting: Setting,
    forbidden: Forbidden,
    target: Target,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "May",
    cautioner_gender: str = "girl",
    caregiver_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the caregiver",
        )
    )
    world.add(Entity(id="room", type="room", label=setting.place))
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=forbidden.label,
            makes_spark=forbidden.makes_spark,
        )
    )
    tgt = world.add(
        Entity(
            id="target",
            type="target",
            label=target.label,
            flammable=target.flammable,
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            type="book",
            label="rhyme book",
            nearby=True,
        )
    )

    world.facts.update(
        predicted_danger=0,
        predicted_ruined=0,
        instigator=a,
        cautioner=b,
        caregiver=caregiver,
        setting=setting,
        forbidden=forbidden,
        target_cfg=target,
        response=response,
        tool=tool,
        target=tgt,
        keepsake=keepsake,
        delay=delay,
    )

    introduce(world, setting, a, b, target)
    need_light(world, a, b, setting)

    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target, caregiver)
    defy(world, a, forbidden)

    world.para()
    ignite(world, forbidden, target)
    alarm(world, a, b, target, caregiver)

    world.para()
    severity = fire_severity(target, delay)
    tgt.meters["severity"] = float(severity)
    contained = is_contained(response, target, delay)
    if contained:
        rescue_success(world, caregiver, response, target)
        bitter_result(world, caregiver, a, b, setting, forbidden, target)
        outcome = "charred"
    else:
        rescue_fail(world, caregiver, response, target)
        escape_and_loss(world, caregiver, a, b, setting, forbidden)
        outcome = "burned"

    world.facts.update(
        ignited=tgt.meters["scorched"] >= THRESHOLD,
        outcome=outcome,
        severity=severity,
        rescued=contained,
        lost_book=keepsake.meters["ruined"] >= THRESHOLD or outcome == "burned",
    )
    return world


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two children"
    if a.type == "girl" and b.type == "girl":
        return "two children"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    end_phrase = "with a bad ending" if outcome in {"charred", "burned"} else ""
    return [
        f'Write a nursery-rhyme-style cautionary story for a 3-to-5-year-old that includes the words "bodily", "spark", and "stale", set in {setting.place}, {end_phrase}.',
        f"Tell a rhyming story where {a.id} reaches for {forbidden.label} to make a spark near {target.the}, while {b.id} warns that it is dangerous.",
        f"Write a gentle-but-sad nursery tale in which stale nursery things catch from one foolish spark, and the ending shows the playroom changed for the worse.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    caregiver = f["caregiver"]
    setting = f["setting"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, playing in {setting.place}. Their {caregiver.label_word} has to come when the fire starts."
        ),
        (
            "Why did the children want a spark?",
            f"They wanted light and a little warmth for {setting.dark_spot}. The nursery felt stale and cold, and that bodily chill made the dangerous idea seem clever."
        ),
        (
            f"What did {b.id} warn about?",
            f"{b.id} warned that {forbidden.lesson} and that {target.the} would catch at once. {b.pronoun().capitalize()} wanted a lamp and a grown-up, not a secret spark."
        ),
        (
            f"What happened when {a.id} made the spark?",
            f"The spark landed on {target.near}, and {target.the} began to burn. That quick fire also ruined the rhyme book lying close by."
        ),
    ]
    if outcome == "charred":
        qa.extend(
            [
                (
                    f"How did {caregiver.label_word} stop the fire?",
                    f"{caregiver.label_word.capitalize()} {response.qa_text}. That was quick enough to save the whole nursery, but not quick enough to save everything in it."
                ),
                (
                    "Why is the ending still a bad ending?",
                    "The room is not happy or safe the way it was before. The rhyme book is ruined, the nursery smells of smoke, and the children lose the place and things that made their game special."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Could {caregiver.label_word} save the nursery?",
                    f"No. {caregiver.label_word.capitalize()} tried, but the fire spread beyond the first burning thing. The children got out safely, yet the nursery and its treasures were lost."
                ),
                (
                    "How did the story end?",
                    "It ended sadly, with the nursery charred and hollow by morning. That ending proves one little spark can stop a whole world of play."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["forbidden"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags) | {"fire"}
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.flammable:
            flags.append("flammable")
        if e.makes_spark:
            flags.append("makes_spark")
        if e.nearby:
            flags.append("nearby")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, forbidden: Forbidden, target: Target) -> str:
    if target.id not in setting.affords:
        return (
            f"(No story: {target.the} does not belong in {setting.place}, so the nursery scene has no honest place for it.)"
        )
    if not target.flammable:
        return (
            f"(No story: {target.the} will not catch from a spark, so there is no real fire and no cautionary turn.)"
        )
    if not forbidden.makes_spark:
        return (
            f"(No story: {forbidden.label} makes no spark, so nothing can ignite.)"
        )
    return "(No story: this combination has no believable nursery fire hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "charred" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, F, T) :- setting(S), forbidden(F), target(T),
                   affords(S, T), makes_spark(F), flammable(T).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
valid(S, F, T) :- hazard(S, F, T).

% --- outcome model ---------------------------------------------------------
severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
contained :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(charred) :- contained.
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, tid))
    for fid, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if forbidden.makes_spark:
            lines.append(asp.fact("makes_spark", fid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("spread", tid, target.spread))
        if target.flammable:
            lines.append(asp.fact("flammable", tid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a stale nursery, a bodily chill, and one dangerous spark."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--caregiver", choices=["mother", "father", "nurse"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.target and args.target not in SETTINGS[args.setting].affords:
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(SETTINGS[args.setting], forbidden, TARGETS[args.target]))
    if args.setting and args.forbidden and args.target:
        if not hazard_at_risk(SETTINGS[args.setting], FORBIDDEN[args.forbidden], TARGETS[args.target]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], FORBIDDEN[args.forbidden], TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    caregiver = args.caregiver or rng.choice(["mother", "father", "nurse"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        forbidden=forbidden,
        target=target,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        caregiver=caregiver,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.forbidden not in FORBIDDEN:
        raise StoryError(f"(Unknown forbidden object: {params.forbidden})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(SETTINGS[params.setting], FORBIDDEN[params.forbidden], TARGETS[params.target]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], FORBIDDEN[params.forbidden], TARGETS[params.target]))

    world = tell(
        setting=SETTINGS[params.setting],
        forbidden=FORBIDDEN[params.forbidden],
        target=TARGETS[params.target],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        caregiver_type=params.caregiver,
        trait=params.trait,
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


CURATED = [
    StoryParams(
        setting="attic",
        forbidden="matches",
        target="straw_pallet",
        response="blanket",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="May",
        cautioner_gender="girl",
        caregiver="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="cottage",
        forbidden="flint",
        target="rush_mat",
        response="water_pitcher",
        instigator="Nell",
        instigator_gender="girl",
        cautioner="Kit",
        cautioner_gender="boy",
        caregiver="nurse",
        trait="sensible",
        delay=1,
    ),
    StoryParams(
        setting="loft",
        forbidden="ember_poker",
        target="straw_pallet",
        response="stomp",
        instigator="Finn",
        instigator_gender="boy",
        cautioner="Rose",
        cautioner_gender="girl",
        caregiver="father",
        trait="cautious",
        delay=2,
    ),
    StoryParams(
        setting="attic",
        forbidden="flint",
        target="muslin_drape",
        response="water_pitcher",
        instigator="Ada",
        instigator_gender="girl",
        cautioner="Robin",
        cautioner_gender="boy",
        caregiver="mother",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="cottage",
        forbidden="matches",
        target="muslin_drape",
        response="blanket",
        instigator="Lucy",
        instigator_gender="girl",
        cautioner="Ned",
        cautioner_gender="boy",
        caregiver="nurse",
        trait="soft-voiced",
        delay=2,
    ),
]


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {r.id for r in sensible_responses()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(cl_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, forbidden, target) combos:\n")
        for setting, forbidden, target in combos:
            print(f"  {setting:8} {forbidden:12} {target}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near {p.target} ({p.setting}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
