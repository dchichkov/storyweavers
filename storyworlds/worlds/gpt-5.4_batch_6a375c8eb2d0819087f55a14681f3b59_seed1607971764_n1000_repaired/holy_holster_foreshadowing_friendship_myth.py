#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py
=========================================================================

A standalone story world for a small child-facing myth about two friends carrying
a holy relic in a holster to greet the dawn.

This domain is built around a simple constraint: a relic, its holster, and the
path must belong together. A good holster is not just decorative; it must suit
the relic's element and steady it for the kind of road ahead. The story then
adds a second layer of tension: one friend is tempted to draw the relic too
early, a foreshadowing omen warns them, and friendship decides whether they
avoid trouble or mend it together.

Run it
------
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py --path reed_marsh --relic moon_arrow --holster reed
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py --path sun_stairs --relic moon_arrow --holster cedar
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py --all
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/holy_holster_foreshadowing_friendship_myth.py --verify
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
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"patient", "careful", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
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
class Path:
    id: str
    label: str
    phrase: str
    omen: str
    hush: str
    creature: str
    condition: str
    severity: int
    altar: str
    ending: str
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
class Relic:
    id: str
    label: str
    phrase: str
    element: str
    glow: str
    taboo: str
    dawn_work: str
    spirit_name: str
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
class Holster:
    id: str
    label: str
    phrase: str
    material: str
    guards: set[str] = field(default_factory=set)
    steadies: set[str] = field(default_factory=set)
    repair_text: str = ""
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


def _r_awaken(world: World) -> list[str]:
    relic = world.get("relic")
    guardian = world.get("guardian")
    if relic.meters["exposed"] < THRESHOLD:
        return []
    sig = ("awaken", relic.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guardian.meters["awake"] += 1
    world.get("path").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__guardian__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="awaken", tag="physical", apply=_r_awaken),
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


def holster_fits(relic: Relic, holster: Holster, path: Path) -> bool:
    return relic.element in holster.guards and path.condition in holster.steadies


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def danger_strength(path: Path, delay: int) -> int:
    return path.severity + delay


def can_calm(response: Response, path: Path, delay: int) -> bool:
    return response.power >= danger_strength(path, delay)


def would_avert(friendship: int, trait: str) -> bool:
    care = 2 if trait in CAUTIOUS_TRAITS else 0
    return friendship + care > BOLDNESS_INIT + 2


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    relic = sim.get("relic")
    relic.meters["in_holster"] = 0.0
    relic.meters["exposed"] += 1
    propagate(sim, narrate=False)
    return {
        "guardian_awake": sim.get("guardian").meters["awake"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def begin_errand(world: World, keeper: Entity, a: Entity, b: Entity,
                 relic: Relic, holster: Holster, path: Path) -> None:
    for kid in (a, b):
        kid.memes["awe"] += 1
        kid.memes["friendship"] = float(world.facts["friendship"])
    world.say(
        f"In the first blue hush before sunrise, {keeper.id} called {a.id} and {b.id} "
        f"to the little hill shrine."
    )
    world.say(
        f'From a basket of laurel leaves, {keeper.pronoun()} lifted {relic.phrase}, '
        f"sleeping in {holster.phrase}. It was a holy charge, meant for {path.altar}."
    )
    world.say(
        f'"Carry it gently," {keeper.id} said. "{relic.taboo}"'
    )


def set_out(world: World, a: Entity, b: Entity, path: Path, holster: Holster) -> None:
    world.say(
        f"So the two friends set out along {path.phrase}. {holster.phrase.capitalize()} "
        f"swung softly at {a.id}'s belt while {b.id} walked beside {a.pronoun('object')}."
    )
    world.say(
        f"They knew that when the true rim of morning rose, the relic would {world.facts['relic_cfg'].dawn_work}."
    )


def foreshadow(world: World, b: Entity, path: Path) -> None:
    b.memes["caution"] += 1
    world.facts["omen_seen"] = True
    world.say(path.omen)
    world.say(
        f"{b.id} noticed it first. {path.hush} was the sort of quiet old songs used before trouble."
    )


def temptation(world: World, a: Entity, b: Entity, relic: Relic) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'The road turned dim under leaning branches, and {a.id} touched the holster. '
        f'"If I draw the {relic.label} for just one breath," {a.pronoun()} said, '
        f'"it will {relic.glow} and show us the stones."'
    )
    world.say(
        f"{b.id} looked at the sleeping hills and did not answer at once."
    )


def warning(world: World, b: Entity, a: Entity, relic: Relic, path: Path) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    extra = " and wake what the old path hides" if pred["guardian_awake"] else ""
    world.say(
        f'"No," said {b.id}. "The signs are speaking. If you pull it free before sunrise, '
        f'you may spill dawn too soon{extra}."'
    )


def back_down(world: World, a: Entity, b: Entity, holster: Holster, path: Path) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["boldness"] = 0.0
    world.say(
        f"{a.id} looked at {b.id}, and because their friendship had been tested by rain, "
        f"games, and long small promises, {a.pronoun()} listened."
    )
    world.say(
        f"Together they tightened the strap of the holster and carried it between them, "
        f"one hand each, all the way toward {path.altar}."
    )


def draw_relic(world: World, a: Entity, relic_cfg: Relic) -> None:
    relic = world.get("relic")
    relic.meters["in_holster"] = 0.0
    relic.meters["exposed"] += 1
    relic.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But eagerness ran ahead of wisdom. {a.id} slipped {relic_cfg.the_label if hasattr(relic_cfg, 'the_label') else 'the relic'} free, "
        f"and at once it {relic_cfg.glow}."
    )


def guardian_rises(world: World, path: Path, relic: Relic, a: Entity, b: Entity) -> None:
    world.say(
        f"Then the omen proved true. Out of the path's shadow rose {path.creature}, "
        f"drawn by the open light of the {relic.label}."
    )
    world.say(
        f"{a.id} stumbled back, and {b.id} caught {a.pronoun('possessive')} wrist before the holy arrow could fall."
    )


def friendship_response(world: World, a: Entity, b: Entity, response: Response,
                        holster: Holster) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    a.memes["shared_courage"] += 1
    b.memes["shared_courage"] += 1
    world.say(
        f"They did not run from each other. {response.text.format(a=a.id, b=b.id, holster=holster.label)}."
    )


def calm_success(world: World, a: Entity, b: Entity, keeper: Entity, path: Path,
                 relic: Relic, holster: Holster, response: Response) -> None:
    rel = world.get("relic")
    rel.meters["exposed"] = 0.0
    rel.meters["in_holster"] = 1.0
    world.get("guardian").meters["awake"] = 0.0
    world.get("path").meters["danger"] = 0.0
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"As soon as the relic slid back into the {holster.label}, {path.creature} thinned like breath on glass and was gone."
    )
    world.say(
        f"When the friends reached {path.altar}, the first gold edge of morning touched the stone, and the {relic.label} {relic.dawn_work} just as {keeper.id} had promised."
    )
    world.say(
        f"From then on, people said the path remembered not only a holy relic, but also two friends who held fast to each other."
    )
    world.facts["repair_used"] = response.id == "braid_strap"


def calm_fail(world: World, a: Entity, b: Entity, path: Path,
              relic: Relic, holster: Holster, response: Response) -> None:
    rel = world.get("relic")
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"But {response.fail.format(a=a.id, b=b.id, holster=holster.label)}. The shadow did not bite or strike; it only circled the light until the sky turned pale and slow."
    )
    world.say(
        f"That morning the dawn came late to {path.label}, and the friends had to sit quietly together until the true sun was strong enough to call the relic home."
    )
    world.say(
        f"When at last they tucked it back into the {holster.label}, they promised never again to let pride pull ahead of friendship."
    )


def ending_after_avert(world: World, a: Entity, b: Entity, keeper: Entity,
                       path: Path, relic: Relic) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"At {path.altar}, they waited side by side. When the sun rose at last, the {relic.label} {relic.dawn_work}, and even the stones looked pleased."
    )
    world.say(
        f"{keeper.id} smiled when they returned and said that the surest hands are not always the quickest ones."
    )
    world.say(
        f"After that, if one of them hurried, the other only had to whisper about the old omen, and both friends would laugh and slow their steps."
    )


def tell(path: Path, relic_cfg: Relic, holster: Holster, response: Response,
         instigator: str = "Tarin", instigator_gender: str = "boy",
         cautioner: str = "Mira", cautioner_gender: str = "girl",
         keeper_type: str = "priestess", trait: str = "patient",
         friendship: int = 7, delay: int = 0) -> World:
    world = World()
    world.facts["friendship"] = friendship
    world.facts["omen_seen"] = False
    world.facts["predicted_danger"] = 0
    world.facts["repair_used"] = False

    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["eager"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
    ))
    keeper_name = "Ione" if keeper_type == "priestess" else "Theron"
    keeper = world.add(Entity(
        id=keeper_name,
        kind="character",
        type=keeper_type,
        role="keeper",
        label="the shrine-keeper",
    ))
    world.add(Entity(id="path", type="path", label=path.label))
    world.add(Entity(id="guardian", type="spirit", label=path.creature))
    relic = world.add(Entity(
        id="relic",
        type="relic",
        label=relic_cfg.label,
        attrs={"element": relic_cfg.element},
    ))
    relic.meters["in_holster"] = 1.0
    relic.meters["exposed"] = 0.0
    relic.meters["glow"] = 0.0
    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = 3.0 if trait not in CAUTIOUS_TRAITS else 5.0
    a.memes["friendship"] = float(friendship)
    b.memes["friendship"] = float(friendship)

    world.facts["path_cfg"] = path
    world.facts["relic_cfg"] = relic_cfg
    world.facts["holster_cfg"] = holster
    world.facts["response"] = response

    begin_errand(world, keeper, a, b, relic_cfg, holster, path)
    set_out(world, a, b, path, holster)

    world.para()
    foreshadow(world, b, path)
    temptation(world, a, b, relic_cfg)
    warning(world, b, a, relic_cfg, path)

    averted = would_avert(friendship, trait)
    if averted:
        back_down(world, a, b, holster, path)
        world.para()
        ending_after_avert(world, a, b, keeper, path, relic_cfg)
        outcome = "averted"
    else:
        world.say(
            f'{a.id} wanted to be brave alone, and that was the mistake. "{relic_cfg.spirit_name} will not mind," {a.pronoun()} whispered.'
        )
        world.para()
        draw_relic(world, a, relic_cfg)
        guardian_rises(world, path, relic_cfg, a, b)

        world.para()
        friendship_response(world, a, b, response, holster)
        if can_calm(response, path, delay):
            calm_success(world, a, b, keeper, path, relic_cfg, holster, response)
            outcome = "calmed"
        else:
            calm_fail(world, a, b, path, relic_cfg, holster, response)
            outcome = "dimmed"

    world.facts.update(
        instigator=a,
        cautioner=b,
        keeper=keeper,
        path_cfg=path,
        relic_cfg=relic_cfg,
        holster_cfg=holster,
        friendship=friendship,
        trait=trait,
        response=response,
        delay=delay,
        outcome=outcome,
        guardian_awake=world.get("guardian").meters["awake"] >= THRESHOLD,
        exposed=world.get("relic").meters["exposed"] >= THRESHOLD,
    )
    return world


PATHS = {
    "sun_stairs": Path(
        id="sun_stairs",
        label="the Sun Stairs",
        phrase="the Sun Stairs that climbed above the olive trees",
        omen="A ring of gold cloud stood around the hidden sun, as if the morning were wearing a crown before any king had risen.",
        hush="Even the cicadas tucked their music away",
        creature="a bronze-maned wind lion",
        condition="windy",
        severity=2,
        altar="the high stair-altar",
        ending="the steps shone like warm bread",
        tags={"mountain", "wind", "myth"},
    ),
    "reed_marsh": Path(
        id="reed_marsh",
        label="the Reed Marsh",
        phrase="the silver path through the Reed Marsh",
        omen="The reeds bent all one way, though no breeze touched the water, and three white herons lifted without making a sound.",
        hush="The marsh went still beneath their sandals",
        creature="a moon-eel made of mist",
        condition="misty",
        severity=3,
        altar="the shell altar by the spring",
        ending="the water held a bright road across it",
        tags={"marsh", "water", "myth"},
    ),
    "echo_pass": Path(
        id="echo_pass",
        label="Echo Pass",
        phrase="Echo Pass between two old red cliffs",
        omen="A pebble rolled uphill by itself and knocked softly against a stone carved with forgotten names.",
        hush="No bird answered the sound",
        creature="a star-ram of blue dust",
        condition="stony",
        severity=2,
        altar="the echo altar in the pass",
        ending="the cliff faces glimmered with tiny points of light",
        tags={"cliff", "echo", "myth"},
    ),
}

RELICS = {
    "sun_arrow": Relic(
        id="sun_arrow",
        label="sun-arrow",
        phrase="a slim sun-arrow of hammered gold",
        element="sun",
        glow="burned with a warm honey-colored light",
        taboo="Do not draw it before the sun sees its own face",
        dawn_work="sent a bright beam dancing over the valley",
        spirit_name="The dawn is only a little late",
        tags={"holy", "sun", "arrow"},
    ),
    "moon_arrow": Relic(
        id="moon_arrow",
        label="moon-arrow",
        phrase="a pale moon-arrow of shell and silver",
        element="moon",
        glow="spilled cool pearl light over the path",
        taboo="Do not draw it before the morning birds begin",
        dawn_work="laid a silver path over the spring before fading into day",
        spirit_name="The marsh spirits are sleeping",
        tags={"holy", "moon", "arrow"},
    ),
    "star_arrow": Relic(
        id="star_arrow",
        label="star-arrow",
        phrase="a star-arrow cut from black glass and bright tin",
        element="star",
        glow="flashed with pinpricks of blue-white fire",
        taboo="Do not draw it before the east has opened",
        dawn_work="shook little sparks across the stone like waking stars",
        spirit_name="Only one little glance",
        tags={"holy", "star", "arrow"},
    ),
}

HOLSTERS = {
    "cedar": Holster(
        id="cedar",
        label="cedar holster",
        phrase="a cedar holster bound with sun-thread",
        material="cedar",
        guards={"sun"},
        steadies={"windy"},
        repair_text="tightened the cedar strap with a laurel knot",
        tags={"holster", "wood"},
    ),
    "reed": Holster(
        id="reed",
        label="reed holster",
        phrase="a reed holster plaited for marsh-light",
        material="reed",
        guards={"moon"},
        steadies={"misty"},
        repair_text="braided new reeds around the slipping clasp",
        tags={"holster", "reed"},
    ),
    "wool": Holster(
        id="wool",
        label="wool holster",
        phrase="a dark wool holster sewn with tiny white knots",
        material="wool",
        guards={"star"},
        steadies={"stony"},
        repair_text="pulled the wool cord snug and even",
        tags={"holster", "cloth"},
    ),
}

RESPONSES = {
    "vow_together": Response(
        id="vow_together",
        sense=3,
        power=3,
        text='They pressed their foreheads together, spoke the dawn vow as one, and guided the relic back toward the {holster}',
        fail='they tried to speak the vow together and push the relic toward the {holster}',
        qa_text="They joined their voices in the dawn vow and returned the relic to its holster",
        tags={"vow", "friendship"},
    ),
    "braid_strap": Response(
        id="braid_strap",
        sense=3,
        power=2,
        text='They knelt shoulder to shoulder, made a quick braid from cord and grass, and looped it around the relic so both could hold it steady beside the {holster}',
        fail='they hurried to braid a new strap beside the {holster}',
        qa_text="They worked together to braid a new strap and steady the relic",
        tags={"repair", "friendship"},
    ),
    "lark_song": Response(
        id="lark_song",
        sense=2,
        power=1,
        text='They sang the little lark-song their elders used at daybreak, hoping the creature would follow the tune while they reached for the {holster}',
        fail='they sang the lark-song and reached for the {holster}',
        qa_text="They sang a dawn song to distract the spirit while they reached for the holster",
        tags={"song", "friendship"},
    ),
    "run_faster": Response(
        id="run_faster",
        sense=1,
        power=0,
        text='They ran with the relic swinging wild between them',
        fail='they only ran faster',
        qa_text="They tried to outrun the trouble",
        tags={"poor_choice"},
    ),
}

GIRL_NAMES = ["Mira", "Nysa", "Dara", "Lina", "Tala", "Rhea", "Eira", "Iris"]
BOY_NAMES = ["Tarin", "Leto", "Aren", "Nico", "Pelas", "Soren", "Ivo", "Milos"]
TRAITS = ["patient", "careful", "wise", "gentle", "thoughtful", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for path_id, path in PATHS.items():
        for relic_id, relic in RELICS.items():
            for holster_id, holster in HOLSTERS.items():
                if holster_fits(relic, holster, path):
                    combos.append((path_id, relic_id, holster_id))
    return combos


@dataclass
class StoryParams:
    path: str
    relic: str
    holster: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    keeper_type: str
    trait: str
    friendship: int = 7
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
    "holy": [
        (
            "What does holy mean in a story like this?",
            "Holy means something is set apart for a special, sacred purpose. In myths, holy objects are treated gently and with respect."
        )
    ],
    "holster": [
        (
            "What is a holster?",
            "A holster is a holder that keeps an object safe and close by. In this story world, the holster protects the sacred relic while it is carried."
        )
    ],
    "vow": [
        (
            "What is a vow?",
            "A vow is a very serious promise. In myths, people sometimes speak a vow together to show truth, respect, or courage."
        )
    ],
    "friendship": [
        (
            "Why can friendship help in a hard moment?",
            "A good friend can warn you when you are rushing and stand beside you when you are scared. Two careful friends are often wiser than one proud person alone."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is when a story gives a small sign before something important happens later. A strange hush, a cloud, or a pebble rolling the wrong way can hint that trouble is near."
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is a wet place with shallow water and tall reeds. Birds, frogs, and mist often gather there."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after you make it. In a mountain pass or cave, your voice can seem to answer you."
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the time when night ends and morning begins. The sky slowly grows brighter as the sun rises."
        )
    ],
}
KNOWLEDGE_ORDER = ["holy", "holster", "friendship", "foreshadowing", "vow", "dawn", "marsh", "echo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    relic = f["relic_cfg"]
    holster = f["holster_cfg"]
    path = f["path_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short child-facing myth that includes the words "holy" and "holster". '
        f"The story should be about two friends carrying a sacred object along {path.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a mythic friendship story where {a.id} wants to draw a {relic.label} early, "
            f"but {b.id} notices an omen first and the friends choose patience together.",
            f"Write a gentle myth with foreshadowing, a holy errand, and a safe ending where the relic stays in its {holster.label}.",
        ]
    if outcome == "dimmed":
        return [
            base,
            f"Tell a myth where a warning sign comes true after {a.id} draws the {relic.label} too soon, "
            f"and the friends must sit with the consequence until dawn is ready again.",
            f"Write a mythic cautionary tale about friendship, impatience, and learning to return a sacred thing to its holster.",
        ]
    return [
        base,
        f"Tell a myth where {a.id} draws the {relic.label} too early, a spirit rises, and friendship helps {a.pronoun('object')} and {b.id} mend the mistake together.",
        f"Write a myth with foreshadowing and friendship where two children calm danger by working together and returning a holy relic to its holster.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    keeper = f["keeper"]
    path = f["path_cfg"]
    relic = f["relic_cfg"]
    holster = f["holster_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, carrying a holy {relic.label} for {keeper.id}. "
            f"They are walking a sacred errand along {path.label}."
        ),
        (
            "What was the holy object kept in?",
            f"The {relic.label} was resting in a {holster.label}. "
            f"The holster was important because it kept the sacred light quiet until the right moment."
        ),
        (
            "What sign warned them that trouble was near?",
            f"The warning sign was this: {path.omen} "
            f"That strange sign was foreshadowing, because it hinted that the path was ready to answer any mistake."
        ),
        (
            f"Why did {b.id} tell {a.id} not to draw the relic early?",
            f"{b.id} saw the omen and understood that the old path was listening. "
            f"{b.pronoun().capitalize()} knew the light might wake {path.creature} before sunrise."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed when {a.id} listened?",
                f"{a.id} stopped trying to be brave alone and let friendship guide the errand instead. "
                f"Because the relic stayed in its holster, no spirit rose and the dawn work happened safely at the altar."
            )
        )
    elif f["outcome"] == "calmed":
        qa.append(
            (
                "How did the friends fix the problem?",
                f"{response.qa_text}. "
                f"They solved it by staying together instead of blaming each other, and that is what calmed the danger."
            )
        )
        qa.append(
            (
                "What happened to the spirit in the end?",
                f"When the relic went back into the {holster.label}, {path.creature} faded away. "
                f"The ending shows that the right time and the right care mattered more than showing off."
            )
        )
    else:
        qa.append(
            (
                "Did the friends get hurt?",
                f"No, they stayed safe together, but the morning grew slow and dim for a while. "
                f"The cost was a late dawn and a serious lesson about patience."
            )
        )
        qa.append(
            (
                "What did they learn by the end?",
                f"They learned that pride can pull faster than wisdom, especially around holy things. "
                f"They also learned that friendship means staying beside each other even after a mistake."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"holy", "holster", "friendship", "foreshadowing", "dawn"}
    if f["path_cfg"].id == "reed_marsh":
        tags.add("marsh")
    if f["path_cfg"].id == "echo_pass":
        tags.add("echo")
    tags |= set(f["response"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        path="sun_stairs",
        relic="sun_arrow",
        holster="cedar",
        response="vow_together",
        instigator="Tarin",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        keeper_type="priestess",
        trait="patient",
        friendship=9,
        delay=0,
    ),
    StoryParams(
        path="echo_pass",
        relic="star_arrow",
        holster="wool",
        response="braid_strap",
        instigator="Aren",
        instigator_gender="boy",
        cautioner="Eira",
        cautioner_gender="girl",
        keeper_type="priest",
        trait="wise",
        friendship=5,
        delay=0,
    ),
    StoryParams(
        path="reed_marsh",
        relic="moon_arrow",
        holster="reed",
        response="lark_song",
        instigator="Nico",
        instigator_gender="boy",
        cautioner="Tala",
        cautioner_gender="girl",
        keeper_type="priestess",
        trait="gentle",
        friendship=4,
        delay=2,
    ),
]


def explain_rejection(path: Path, relic: Relic, holster: Holster) -> str:
    return (
        f"(No story: a {holster.label} is not a reasonable carrier for the {relic.label} on {path.label}. "
        f"The holster must suit the relic's sacred element and steady it for that kind of road.)"
    )


def explain_response(response_id: str) -> str:
    resp = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak or foolish for this mythic world "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.friendship, params.trait):
        return "averted"
    if can_calm(RESPONSES[params.response], PATHS[params.path], params.delay):
        return "calmed"
    return "dimmed"


ASP_RULES = r"""
fits_holster(R, H, P) :- relic(R), holster(H), path(P),
                         element(R, E), guards(H, E),
                         condition(P, C), steadies(H, C).

sensible(Resp) :- response(Resp), sense(Resp, S), sense_min(M), S >= M.
valid(P, R, H) :- path(P), relic(R), holster(H), fits_holster(R, H, P).

care_bonus(2) :- chosen_trait(T), cautious_trait(T).
care_bonus(0) :- chosen_trait(T), not cautious_trait(T).

averted :- friendship(F), care_bonus(B), boldness_init(BI), F + B > BI + 2.

danger(V) :- chosen_path(P), severity(P, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), danger(V), P >= V.

outcome(averted) :- averted.
outcome(calmed) :- not averted, contained.
outcome(dimmed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("condition", path_id, path.condition))
        lines.append(asp.fact("severity", path_id, path.severity))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("element", relic_id, relic.element))
    for holster_id, holster in HOLSTERS.items():
        lines.append(asp.fact("holster", holster_id))
        for guard in sorted(holster.guards):
            lines.append(asp.fact("guards", holster_id, guard))
        for steady in sorted(holster.steadies):
            lines.append(asp.fact("steadies", holster_id, steady))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
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
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_trait", params.trait),
            asp.fact("friendship", params.friendship),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid combos match ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a holy relic, a holster, an omen, and friendship in a small myth."
    )
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--holster", choices=HOLSTERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--keeper-type", choices=["priestess", "priest"])
    ap.add_argument("--friendship", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and args.relic and args.holster:
        path = PATHS[args.path]
        relic = RELICS[args.relic]
        holster = HOLSTERS[args.holster]
        if not holster_fits(relic, holster, path):
            raise StoryError(explain_rejection(path, relic, holster))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.path is None or combo[0] == args.path)
        and (args.relic is None or combo[1] == args.relic)
        and (args.holster is None or combo[2] == args.holster)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    path_id, relic_id, holster_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    keeper_type = args.keeper_type or rng.choice(["priestess", "priest"])
    trait = rng.choice(TRAITS)
    friendship = args.friendship if args.friendship is not None else rng.randint(3, 10)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        path=path_id,
        relic=relic_id,
        holster=holster_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        keeper_type=keeper_type,
        trait=trait,
        friendship=friendship,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.holster not in HOLSTERS:
        raise StoryError(f"(Unknown holster: {params.holster})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not holster_fits(RELICS[params.relic], HOLSTERS[params.holster], PATHS[params.path]):
        raise StoryError(explain_rejection(PATHS[params.path], RELICS[params.relic], HOLSTERS[params.holster]))

    world = tell(
        path=PATHS[params.path],
        relic_cfg=RELICS[params.relic],
        holster=HOLSTERS[params.holster],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        keeper_type=params.keeper_type,
        trait=params.trait,
        friendship=params.friendship,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (path, relic, holster) combos:\n")
        for path_id, relic_id, holster_id in combos:
            print(f"  {path_id:11} {relic_id:11} {holster_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.relic} on {p.path} "
                f"with {p.holster} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
