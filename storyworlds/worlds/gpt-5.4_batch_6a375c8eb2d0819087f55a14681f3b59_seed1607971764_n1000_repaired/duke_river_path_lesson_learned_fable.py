#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py
==================================================================

A standalone story world for a small fable set on a river path.

Premise
-------
A little duke walks beside the river carrying something precious. A wiser friend
warns that the river path is tricky. Sometimes the duke listens and reaches the
end safely. Sometimes pride sends the duke hurrying ahead, a stumble follows,
and a helper must recover what was nearly lost. In every branch, the ending
shows the lesson learned: pride and hurry make small dangers grow.

Run it
------
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py --cargo berry_basket --hazard steep_edge
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py --response paws_only
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py --all
python storyworlds/worlds/gpt-5.4/duke_river_path_lesson_learned_fable.py --verify
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
SENSE_MIN = 2
PRIDE_INIT = 5.0
WISE_TRAITS = {"steady", "careful", "patient", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    precious: bool = False
    carryable: bool = False
    recover_tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "duck_f", "otter_f", "mouse_f", "frog_f"}
        male = {"boy", "man", "duck_m", "otter_m", "mouse_m", "frog_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Cargo:
    id: str
    label: str
    phrase: str
    fragile: int
    precious: bool = True
    recover_tags: set[str] = field(default_factory=set)
    loss_line: str = ""
    saved_line: str = ""
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
class Hazard:
    id: str
    label: str
    phrase: str
    severity: int
    risky: bool = True
    stumble_text: str = ""
    warning_text: str = ""
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
class Response:
    id: str
    sense: int
    power: int
    recovers: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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
    kind: str
    type: str
    stride: str
    home: str
    title: str = ""
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


def _r_drop_cargo(world: World) -> list[str]:
    duke = world.get("duke")
    cargo = world.get("cargo")
    if duke.meters["off_balance"] < THRESHOLD or cargo.meters["carried"] < THRESHOLD:
        return []
    sig = ("drop", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    cargo.meters["in_water"] += 1
    cargo.meters["carried"] = 0.0
    duke.memes["fear"] += 1
    duke.memes["regret"] += 1
    friend = world.get("friend")
    friend.memes["alarm"] += 1
    return ["__drop__"]


def _r_wet_and_loss(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["in_water"] < THRESHOLD:
        return []
    sig = ("wet", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["wet"] += 1
    cargo.meters["at_risk"] += 1
    return ["__wet__"]


CAUSAL_RULES = [
    Rule(name="drop_cargo", tag="physical", apply=_r_drop_cargo),
    Rule(name="wet_and_loss", tag="physical", apply=_r_wet_and_loss),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def cargo_at_risk(cargo: Cargo, hazard: Hazard) -> bool:
    return cargo.precious and hazard.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def loss_difficulty(cargo: Cargo, hazard: Hazard, delay: int) -> int:
    return cargo.fragile + hazard.severity + delay


def can_recover(response: Response, cargo: Cargo, hazard: Hazard, delay: int) -> bool:
    if not (response.recovers & cargo.recover_tags):
        return False
    return response.power >= loss_difficulty(cargo, hazard, delay)


def initial_wisdom(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_heed(duke_age: int, friend_age: int, friend_trait: str) -> bool:
    elder_bonus = 3.0 if friend_age > duke_age else 0.0
    authority = initial_wisdom(friend_trait) + 1.0 + elder_bonus
    return authority > PRIDE_INIT


def predict_drop(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    duke = sim.get("duke")
    hazard_cfg = HAZARDS[hazard_id]
    duke.meters["off_balance"] += 1
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "drops": cargo.meters["dropped"] >= THRESHOLD,
        "wet": cargo.meters["wet"] >= THRESHOLD,
        "severity": hazard_cfg.severity,
    }


def introduce(world: World, duke: Entity, friend: Entity, cargo: Cargo, creature: Creature) -> None:
    world.say(
        f"Once, on a river path where reeds whispered and minnows flashed like bits of silver, "
        f"there walked {creature.title} {duke.id}. {duke.id} was small, but {duke.pronoun()} liked to step "
        f"as if trumpets should sound for every footfall."
    )
    world.say(
        f"That morning {duke.pronoun()} carried {cargo.phrase} toward {creature.home}, meaning to arrive looking grand. "
        f"Beside {duke.pronoun('object')} walked {friend.id}, a friend with quieter eyes and a steadier pace."
    )


def admire_reflection(world: World, duke: Entity, creature: Creature) -> None:
    duke.memes["pride"] += 1
    world.say(
        f"Every now and then {duke.id} glanced into the bright river to admire {duke.pronoun('possessive')} reflection. "
        f"The little duke loved to see {duke.pronoun('object')}self looking neat and important."
    )


def spot_hazard(world: World, hazard: Hazard) -> None:
    world.say(
        f"After a bend in the river path, they came to {hazard.phrase}. "
        f"{hazard.warning_text}"
    )


def warn(world: World, duke: Entity, friend: Entity, cargo: Cargo, hazard: Hazard) -> None:
    pred = predict_drop(world, hazard.id)
    world.facts["predicted_drop"] = pred["drops"]
    world.facts["predicted_wet"] = pred["wet"]
    friend.memes["care"] += 1
    extra = ""
    if friend.memes["wisdom"] >= 6:
        extra = f" {friend.pronoun().capitalize()} had seen many hurried feet make the same mistake."
    world.say(
        f'"Slow your steps, Duke {duke.id}," said {friend.id}. "The river path is no place for showing off. '
        f'If you rush here, {cargo.label} could slip from your grasp."{extra}'
    )


def defy(world: World, duke: Entity) -> None:
    duke.memes["defiance"] += 1
    world.say(
        f'But the little duke lifted {duke.pronoun("possessive")} chin. "I know this path," '
        f'{duke.pronoun()} said. "I can hurry and still look splendid."'
    )


def heed(world: World, duke: Entity, friend: Entity, cargo: Cargo) -> None:
    duke.memes["pride"] = 0.0
    duke.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{duke.id} took one more vain glance at the water, then looked at {cargo.label} in "
        f"{duke.pronoun('possessive')} arms and thought better of it."
    )
    world.say(
        f'"You are right," {duke.pronoun()} said. "A careful step is finer than a foolish leap." '
        f"So the little duke tucked {cargo.label} close and walked slowly with {friend.id}."
    )


def stumble(world: World, duke: Entity, cargo: Cargo, hazard: Hazard) -> None:
    duke.meters["off_balance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hazard.stumble_text} {duke.id}'s feet flew out, and {cargo.label} slipped from "
        f"{duke.pronoun('possessive')} grasp toward the river."
    )
    if cargo.saved_line:
        world.say(cargo.loss_line)


def cry_out(world: World, friend: Entity, duke: Entity) -> None:
    world.say(f'"{duke.id}!" cried {friend.id}.')
    world.say(
        f"The river gave a quick greedy splash, and for one frightened heartbeat the little duke could only stare."
    )


def recover(world: World, friend: Entity, response: Response, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.meters["in_water"] = 0.0
    cargo_ent.meters["at_risk"] = 0.0
    cargo_ent.meters["saved"] += 1
    duke = world.get("duke")
    duke.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(f"{friend.id} {response.text.replace('{cargo}', cargo.label)}.")
    world.say(cargo.saved_line)


def recover_fail(world: World, friend: Entity, response: Response, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.meters["lost"] += 1
    world.say(f"{friend.id} {response.fail.replace('{cargo}', cargo.label)}.")
    world.say(
        f"The river path stayed the same, but the little duke did not. {duke_phrase(world)} watched the water "
        f"carry away {cargo.label}, and pride suddenly felt very small."
    )


def duke_phrase(world: World) -> str:
    duke = world.get("duke")
    return f"Duke {duke.id}"


def lesson_safe(world: World, duke: Entity, friend: Entity, cargo: Cargo, creature: Creature) -> None:
    duke.memes["lesson"] += 1
    duke.memes["gratitude"] += 1
    world.say(
        f"When they reached {creature.home}, {cargo.label} was still neat and safe. "
        f"{duke.id} bowed to {friend.id} more politely than before."
    )
    world.say(
        f'"Today I learned that a title does not keep one steady," {duke.pronoun()} said. '
        f'"Good advice does."'
    )
    world.say(
        f"From then on, whenever the river path narrowed, the little duke chose slow feet over proud feet."
    )


def lesson_after_rescue(world: World, duke: Entity, friend: Entity, cargo: Cargo, creature: Creature) -> None:
    duke.memes["lesson"] += 1
    duke.memes["gratitude"] += 1
    world.say(
        f"Together they carried {cargo.label} the rest of the way, no longer to look grand, but simply to arrive well."
    )
    world.say(
        f'At {creature.home}, Duke {duke.id} lowered {duke.pronoun("possessive")} head and said, '
        f'"I thought speed would make me splendid. Instead, it nearly made me lose what mattered."'
    )
    world.say(
        f"After that day, the little duke listened before hurrying, and the river path seemed kinder to {duke.pronoun('object')}."
    )


def lesson_after_loss(world: World, duke: Entity, friend: Entity) -> None:
    duke.memes["lesson"] += 1
    duke.memes["sadness"] += 1
    world.say(
        f'{friend.id} put a gentle paw on {duke.id}\'s shoulder. "The river keeps what pride tosses to it," '
        f'{friend.pronoun()} said.'
    )
    world.say(
        f"Duke {duke.id} nodded and answered softly, \"Then I must learn to carry my pride more lightly.\""
    )
    world.say(
        f"Ever after, when the river path gleamed and tempted {duke.pronoun('object')} to hurry, the little duke remembered the splash and chose patience."
    )


def tell(
    creature: Creature,
    cargo: Cargo,
    hazard: Hazard,
    response: Response,
    duke_name: str = "Pip",
    friend_name: str = "Mara",
    friend_trait: str = "careful",
    duke_age: int = 5,
    friend_age: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    duke = world.add(
        Entity(
            id=duke_name,
            kind="character",
            type=creature.type,
            label="duke",
            role="duke",
            traits=["proud"],
            age=duke_age,
            attrs={"title": creature.title, "stride": creature.stride},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type="otter_f" if creature.type.endswith("_m") else "otter_m",
            label="friend",
            role="friend",
            traits=[friend_trait],
            age=friend_age,
            attrs={"wise": True},
        )
    )
    cargo_ent = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="gift",
            label=cargo.label,
            role="cargo",
            precious=cargo.precious,
            carryable=True,
            recover_tags=set(cargo.recover_tags),
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="thing",
            type="river_path",
            label="river path",
            role="setting",
        )
    )
    water = world.add(
        Entity(
            id="river",
            kind="thing",
            type="river",
            label="river",
            role="setting",
        )
    )

    cargo_ent.meters["carried"] = 1.0
    cargo_ent.meters["dropped"] = 0.0
    cargo_ent.meters["wet"] = 0.0
    cargo_ent.meters["saved"] = 0.0
    cargo_ent.meters["lost"] = 0.0
    cargo_ent.meters["in_water"] = 0.0
    cargo_ent.meters["at_risk"] = 0.0

    duke.meters["off_balance"] = 0.0
    duke.memes["pride"] = PRIDE_INIT
    duke.memes["fear"] = 0.0
    duke.memes["regret"] = 0.0
    duke.memes["relief"] = 0.0
    duke.memes["lesson"] = 0.0
    duke.memes["gratitude"] = 0.0
    duke.memes["sadness"] = 0.0

    friend.memes["wisdom"] = initial_wisdom(friend_trait)
    friend.memes["care"] = 0.0
    friend.memes["alarm"] = 0.0
    friend.memes["relief"] = 0.0

    path.meters["risk"] = float(hazard.severity if hazard.risky else 0)
    water.meters["pull"] = float(hazard.severity)

    world.facts.update(
        creature=creature,
        cargo_cfg=cargo,
        hazard_cfg=hazard,
        response=response,
        delay=delay,
        duke=duke,
        friend=friend,
        cargo=cargo_ent,
        safe=False,
        recovered=False,
        lost=False,
    )

    introduce(world, duke, friend, cargo, creature)
    admire_reflection(world, duke, creature)

    world.para()
    spot_hazard(world, hazard)
    warn(world, duke, friend, cargo, hazard)

    if would_heed(duke_age, friend_age, friend_trait):
        heed(world, duke, friend, cargo)
        world.para()
        lesson_safe(world, duke, friend, cargo, creature)
        outcome = "heeded"
    else:
        defy(world, duke)
        world.para()
        stumble(world, duke, cargo, hazard)
        cry_out(world, friend, duke)
        world.para()
        if can_recover(response, cargo, hazard, delay):
            recover(world, friend, response, cargo)
            lesson_after_rescue(world, duke, friend, cargo, creature)
            outcome = "recovered"
        else:
            recover_fail(world, friend, response, cargo)
            lesson_after_loss(world, duke, friend)
            outcome = "lost"

    world.facts.update(
        outcome=outcome,
        safe=(outcome == "heeded"),
        recovered=(outcome == "recovered"),
        lost=(outcome == "lost"),
    )
    return world


CARGO = {
    "berry_basket": Cargo(
        id="berry_basket",
        label="the berry basket",
        phrase="a little basket of wild berries",
        fragile=2,
        recover_tags={"scattered", "basket"},
        loss_line="The basket tipped, and red berries skipped over the stones like startled beads.",
        saved_line="In a moment the berries were back in the basket, glistening but saved for supper.",
        tags={"berries", "basket"},
    ),
    "honey_jar": Cargo(
        id="honey_jar",
        label="the honey jar",
        phrase="a sealed jar of golden honey",
        fragile=1,
        recover_tags={"hookable", "sealed"},
        loss_line="The jar spun once in the air, caught the light, and splashed near the reeds.",
        saved_line="The jar came up dripping, still stoppered tight, with its honey safe inside.",
        tags={"honey", "jar"},
    ),
    "reed_crown": Cargo(
        id="reed_crown",
        label="the reed crown",
        phrase="a woven reed crown for the evening feast",
        fragile=1,
        recover_tags={"light", "hookable"},
        loss_line="The crown floated in a little circle, as if the river itself wished to wear it.",
        saved_line="The crown was bent, but not broken, and a few deft tugs set it right again.",
        tags={"crown", "reeds"},
    ),
    "plain_pebble": Cargo(
        id="plain_pebble",
        label="the plain pebble",
        phrase="a plain gray pebble",
        fragile=0,
        precious=False,
        recover_tags={"hookable"},
        loss_line="The pebble plopped once and vanished beneath hardly a ripple.",
        saved_line="Even if it had come back, it would have been only a pebble.",
        tags={"pebble"},
    ),
}

HAZARDS = {
    "slick_stones": Hazard(
        id="slick_stones",
        label="slick stones",
        phrase="a strip of dark slick stones",
        severity=2,
        risky=True,
        stumble_text="One stone rolled under the duke's foot and the next shone with moss.",
        warning_text="The stones were polished by water and as slippery as soap.",
        tags={"slippery"},
    ),
    "muddy_bend": Hazard(
        id="muddy_bend",
        label="muddy bend",
        phrase="a muddy bend where the bank sagged toward the water",
        severity=1,
        risky=True,
        stumble_text="The earth gave a soft squish and slid away under the duke's haste.",
        warning_text="The mud looked smooth, but smooth mud often hides a trick.",
        tags={"mud"},
    ),
    "steep_edge": Hazard(
        id="steep_edge",
        label="steep edge",
        phrase="a narrow stretch where the path leaned sharply over the river",
        severity=3,
        risky=True,
        stumble_text="The path pinched thin, and one proud quick step left too little room for balance.",
        warning_text="Below it, the water licked at roots and waited for anything careless.",
        tags={"edge", "water"},
    ),
    "sunny_patch": Hazard(
        id="sunny_patch",
        label="sunny patch",
        phrase="a broad sunny patch of flat dry ground",
        severity=0,
        risky=False,
        stumble_text="Nothing there would make a careful traveler fall.",
        warning_text="It was cheerful and harmless, with no trick in it at all.",
        tags={"safe_ground"},
    ),
}

RESPONSES = {
    "willow_branch": Response(
        id="willow_branch",
        sense=3,
        power=2,
        recovers={"hookable", "light", "basket"},
        text="snatched a long willow branch from the bank and drew {cargo} back through the shallows",
        fail="reached with a willow branch, but the current pulled {cargo} just beyond it",
        qa_text="used a willow branch to draw it back from the shallows",
        tags={"branch", "rescue"},
    ),
    "beaver_net": Response(
        id="beaver_net",
        sense=4,
        power=4,
        recovers={"hookable", "light", "basket", "scattered", "sealed"},
        text="called to a nearby beaver, borrowed a woven net, and scooped {cargo} safely from the water",
        fail="borrowed a woven net, but the water had already carried {cargo} too far downstream",
        qa_text="borrowed a woven net and scooped it from the water",
        tags={"net", "beaver", "rescue"},
    ),
    "wade_in": Response(
        id="wade_in",
        sense=2,
        power=1,
        recovers={"sealed", "light"},
        text="splashed in at once and grabbed {cargo} before it drifted far",
        fail="splashed in, but the river slipped {cargo} out of reach",
        qa_text="waded in and grabbed it before it drifted away",
        tags={"water", "rescue"},
    ),
    "paws_only": Response(
        id="paws_only",
        sense=1,
        power=0,
        recovers={"light"},
        text="scrabbled at the edge with bare paws until {cargo} bumped back",
        fail="scrabbled at the edge with bare paws, which only stirred the water and sent {cargo} farther away",
        qa_text="tried to grab it with bare paws",
        tags={"poor_idea"},
    ),
}

CREATURES = {
    "mouse_duke": Creature(
        id="mouse_duke",
        kind="mouse",
        type="mouse_m",
        stride="quick tiny steps",
        home="the willow hall",
        title="Duke",
        tags={"mouse", "duke"},
    ),
    "duck_duke": Creature(
        id="duck_duke",
        kind="duck",
        type="duck_m",
        stride="a smooth proud waddle",
        home="the reed pavilion",
        title="Duke",
        tags={"duck", "duke"},
    ),
    "otter_duke": Creature(
        id="otter_duke",
        kind="otter",
        type="otter_m",
        stride="a neat springy trot",
        home="the riverside gate",
        title="Duke",
        tags={"otter", "duke"},
    ),
}

DUKE_NAMES = ["Pip", "Rowan", "Alder", "Milo", "Bram", "Nettle"]
FRIEND_NAMES = ["Mara", "Tansy", "Willow", "Fern", "Brindle", "Clover"]
FRIEND_TRAITS = ["careful", "patient", "steady", "wise", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cargo_id, cargo in CARGO.items():
        for hazard_id, hazard in HAZARDS.items():
            if cargo_at_risk(cargo, hazard):
                combos.append((cargo_id, hazard_id))
    return combos


@dataclass
class StoryParams:
    creature: str
    cargo: str
    hazard: str
    response: str
    duke_name: str
    friend_name: str
    friend_trait: str
    duke_age: int = 5
    friend_age: int = 7
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
    "river_path": [
        (
            "Why should you walk carefully on a river path?",
            "A river path can be wet, narrow, or slippery. Careful steps help you keep your balance and stay away from the water.",
        )
    ],
    "slippery": [
        (
            "Why are wet stones slippery?",
            "A thin layer of water or moss makes your feet slide instead of grip. That is why wet stones can make a fast walker fall.",
        )
    ],
    "mud": [
        (
            "Why can mud make walking hard?",
            "Mud looks soft, but it can slide under your feet. When the ground moves, it is easier to lose your balance.",
        )
    ],
    "edge": [
        (
            "Why is a steep river edge dangerous?",
            "A steep edge gives you less room to stand safely. One wrong step can send you toward the water.",
        )
    ],
    "berries": [
        (
            "Why do berries spill so easily?",
            "Berries are small and round, so they roll and scatter quickly. A tipped basket can send them in many directions at once.",
        )
    ],
    "honey": [
        (
            "Why is a sealed jar safer than an open bowl near water?",
            "A sealed jar keeps what is inside from spilling right away. Even if it gets wet outside, the lid can protect the honey.",
        )
    ],
    "crown": [
        (
            "What is a reed crown?",
            "A reed crown is a circle woven from long plant stems. It is light and pretty, but it can bend if it is dropped.",
        )
    ],
    "branch": [
        (
            "How can a long branch help reach something in water?",
            "A long branch lets you stay on the bank while reaching farther out. It can hook or pull a floating thing back to shore.",
        )
    ],
    "net": [
        (
            "What does a net help with?",
            "A net catches things that are hard to grab one by one. It is useful when many small things scatter in shallow water.",
        )
    ],
    "beaver": [
        (
            "Why might a beaver be good at helping by a river?",
            "Beavers live near water and know how to work with branches and woven things. In stories, they often make clever helpers by the bank.",
        )
    ],
    "lesson": [
        (
            "What does it mean to learn a lesson from a mistake?",
            "It means you remember what went wrong and choose better next time. A lesson turns one bad moment into wiser steps later.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "river_path",
    "slippery",
    "mud",
    "edge",
    "berries",
    "honey",
    "crown",
    "branch",
    "net",
    "beaver",
    "lesson",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    duke = f["duke"]
    cargo = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old set on a river path about a little duke carrying {cargo.label}. '
        f'Include the word "duke".'
    )
    if outcome == "heeded":
        return [
            base,
            f"Tell a gentle fable where Duke {duke.id} listens when a wiser friend warns about {hazard.label}, and the safe ending proves the lesson.",
            f"Write a lesson-learned story in which pride almost speaks first, but careful advice wins before anything is lost.",
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell a fable where Duke {duke.id} hurries along {hazard.phrase}, drops {cargo.label}, and is saved by a quick-thinking friend.",
            f"Write a story with a clear moral: a proud little duke ignores wise advice on a river path, then learns from the scare and changes.",
        ]
    return [
        base,
        f"Tell a cautionary fable where Duke {duke.id} ignores a warning on {hazard.phrase}, loses {cargo.label}, and learns humility.",
        f"Write a simple lesson-learned fable showing that a proud hurry on a river path can cost something precious.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    duke = f["duke"]
    friend = f["friend"]
    cargo_cfg = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Duke {duke.id}, a small proud traveler on a river path, and {friend.id}, the friend who walked beside him.",
        ),
        (
            f"What was Duke {duke.id} carrying?",
            f"He was carrying {cargo_cfg.phrase}. It mattered because he wanted to arrive looking grand and careful with it.",
        ),
        (
            f"Why did {friend.id} warn Duke {duke.id}?",
            f"{friend.id} warned him because {hazard.phrase} could make a hurried traveler slip. The danger was not just falling, but losing {cargo_cfg.label} to the river.",
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"What did Duke {duke.id} do after the warning?",
                f"He slowed down and listened. Because he chose careful steps instead of proud quick ones, {cargo_cfg.label} stayed safe all the way to the end.",
            )
        )
        qa.append(
            (
                "What lesson did the duke learn?",
                f"He learned that being important does not make a path less slippery. Good advice and patient steps kept him safe.",
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when Duke {duke.id} hurried?",
                f"He stumbled and {cargo_cfg.label} went toward the river. The scare showed him that pride had made him careless.",
            )
        )
        qa.append(
            (
                f"How was {cargo_cfg.label} saved?",
                f"{friend.id} {response.qa_text}. That quick help stopped one bad step from turning into a full loss.",
            )
        )
        qa.append(
            (
                "What lesson did the duke learn?",
                f"He learned that speed and showing off are poor guides on a river path. After the rescue, he listened before hurrying.",
            )
        )
    else:
        qa.append(
            (
                f"Could they get {cargo_cfg.label} back?",
                f"No. {friend.id} tried to help, but the river carried it away before they could save it. The loss made the lesson much heavier for the little duke.",
            )
        )
        qa.append(
            (
                "What lesson did the duke learn?",
                f"He learned that pride can make a small danger into a real loss. After that, he chose patience whenever the river path tempted him to rush.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cargo = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    tags = {"river_path", "lesson"} | set(cargo.tags) | set(hazard.tags)
    if f["outcome"] != "heeded":
        tags |= set(response.tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.precious:
            bits.append("precious=True")
        if ent.recover_tags:
            bits.append(f"recover_tags={sorted(ent.recover_tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        creature="mouse_duke",
        cargo="berry_basket",
        hazard="slick_stones",
        response="beaver_net",
        duke_name="Pip",
        friend_name="Mara",
        friend_trait="careful",
        duke_age=5,
        friend_age=8,
        delay=0,
    ),
    StoryParams(
        creature="duck_duke",
        cargo="honey_jar",
        hazard="muddy_bend",
        response="willow_branch",
        duke_name="Rowan",
        friend_name="Fern",
        friend_trait="gentle",
        duke_age=6,
        friend_age=5,
        delay=0,
    ),
    StoryParams(
        creature="otter_duke",
        cargo="reed_crown",
        hazard="steep_edge",
        response="willow_branch",
        duke_name="Alder",
        friend_name="Tansy",
        friend_trait="thoughtful",
        duke_age=6,
        friend_age=4,
        delay=1,
    ),
    StoryParams(
        creature="mouse_duke",
        cargo="berry_basket",
        hazard="steep_edge",
        response="beaver_net",
        duke_name="Milo",
        friend_name="Clover",
        friend_trait="wise",
        duke_age=5,
        friend_age=6,
        delay=1,
    ),
    StoryParams(
        creature="duck_duke",
        cargo="honey_jar",
        hazard="slick_stones",
        response="wade_in",
        duke_name="Bram",
        friend_name="Willow",
        friend_trait="steady",
        duke_age=7,
        friend_age=5,
        delay=2,
    ),
]


def explain_rejection(cargo: Cargo, hazard: Hazard) -> str:
    if not hazard.risky:
        return (
            f"(No story: {hazard.phrase} is not truly dangerous on a river path, so there is no honest stumble and no lesson to prove.)"
        )
    if not cargo.precious:
        return (
            f"(No story: {cargo.label} is not precious enough to raise the stakes. A fable here needs something that could really matter if the river takes it.)"
        )
    return "(No story: this combination does not create a meaningful risk.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too poor a rescue idea for this world (sense={response.sense} < {SENSE_MIN}). "
        f"Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.duke_age, params.friend_age, params.friend_trait):
        return "heeded"
    cargo = CARGO[params.cargo]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "recovered" if can_recover(response, cargo, hazard, params.delay) else "lost"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
at_risk(C, H) :- precious(C), risky(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(C, H) :- cargo(C), hazard(H), at_risk(C, H).

% --- heed / stumble / outcome ----------------------------------------------
wise_now(T) :- trait(T), wise_trait(T).
init_wisdom(5) :- trait(T), wise_now(T).
init_wisdom(3) :- trait(T), not wise_now(T).
elder_bonus(3) :- friend_age(FA), duke_age(DA), FA > DA.
elder_bonus(0) :- friend_age(FA), duke_age(DA), FA <= DA.
authority(W + 1 + B) :- init_wisdom(W), elder_bonus(B).
heeded :- authority(A), pride_init(P), A > P.

difficulty(F + S + D) :- chosen_cargo(C), fragility(C, F), chosen_hazard(H), severity(H, S), delay(D).
compatible :- chosen_response(R), chosen_cargo(C), recovers(R, T), cargo_tag(C, T).
recovered :- compatible, chosen_response(R), power(R, P), difficulty(X), P >= X.

outcome(heeded) :- heeded.
outcome(recovered) :- not heeded, recovered.
outcome(lost) :- not heeded, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CARGO:
        lines.append(asp.fact("cargo", cid))
        if CARGO[cid].precious:
            lines.append(asp.fact("precious", cid))
        lines.append(asp.fact("fragility", cid, CARGO[cid].fragile))
        for tag in sorted(CARGO[cid].recover_tags):
            lines.append(asp.fact("cargo_tag", cid, tag))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hid, HAZARDS[hid].severity))
        if HAZARDS[hid].risky:
            lines.append(asp.fact("risky", hid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for tag in sorted(response.recovers):
            lines.append(asp.fact("recovers", rid, tag))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("duke_age", params.duke_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.friend_trait),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sense = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sense)} clingo={sorted(asp_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} scenario outcomes differ.")

    try:
        smoke_params = CURATED[0]
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        out = buf.getvalue()
        if "duke" not in sample.story.lower():
            raise StoryError("Smoke test story did not include the required word 'duke'.")
        if "### smoke" not in out:
            raise StoryError("Smoke test emit() did not render expected output.")
        print("OK: smoke generation and emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a proud little duke on a river path learns to value careful steps."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--duke-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS)
    ap.add_argument("--duke-age", type=int, choices=[4, 5, 6, 7], help="younger duke is more likely to heed an older friend")
    ap.add_argument("--friend-age", type=int, choices=[4, 5, 6, 7, 8], help="older friend carries more authority")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the cargo bobs in danger before help acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible cargo/hazard pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and not HAZARDS[args.hazard].risky:
        cargo = CARGO[args.cargo] if args.cargo else next(iter(CARGO.values()))
        raise StoryError(explain_rejection(cargo, HAZARDS[args.hazard]))
    if args.cargo and not CARGO[args.cargo].precious:
        hazard = HAZARDS[args.hazard] if args.hazard else next(iter(HAZARDS.values()))
        raise StoryError(explain_rejection(CARGO[args.cargo], hazard))
    if args.cargo and args.hazard:
        cargo = CARGO[args.cargo]
        hazard = HAZARDS[args.hazard]
        if not cargo_at_risk(cargo, hazard):
            raise StoryError(explain_rejection(cargo, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.hazard is None or combo[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, hazard_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    creature_id = args.creature or rng.choice(sorted(CREATURES))
    duke_name = args.duke_name or rng.choice(DUKE_NAMES)
    friend_name_pool = [n for n in FRIEND_NAMES if n != duke_name]
    friend_name = args.friend_name or rng.choice(friend_name_pool)
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)
    duke_age = args.duke_age if args.duke_age is not None else rng.choice([4, 5, 6, 7])
    friend_age = args.friend_age if args.friend_age is not None else rng.choice([4, 5, 6, 7, 8])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        creature=creature_id,
        cargo=cargo_id,
        hazard=hazard_id,
        response=response_id,
        duke_name=duke_name,
        friend_name=friend_name,
        friend_trait=friend_trait,
        duke_age=duke_age,
        friend_age=friend_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        creature = CREATURES[params.creature]
        cargo = CARGO[params.cargo]
        hazard = HAZARDS[params.hazard]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if not cargo_at_risk(cargo, hazard):
        raise StoryError(explain_rejection(cargo, hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        creature=creature,
        cargo=cargo,
        hazard=hazard,
        response=response,
        duke_name=params.duke_name,
        friend_name=params.friend_name,
        friend_trait=params.friend_trait,
        duke_age=params.duke_age,
        friend_age=params.friend_age,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, hazard) combos:\n")
        for cargo_id, hazard_id in combos:
            print(f"  {cargo_id:13} {hazard_id}")
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
            header = f"### Duke {p.duke_name}: {p.cargo} on {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
