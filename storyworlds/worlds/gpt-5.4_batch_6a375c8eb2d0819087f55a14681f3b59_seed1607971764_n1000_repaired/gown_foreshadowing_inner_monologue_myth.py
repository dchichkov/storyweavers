#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py
=====================================================================

A standalone story world for a small myth-shaped tale about a ceremonial gown,
an omen, a dangerous path, and a wise preparation.

This world is built around three ideas from the seed:
- the word "gown" is central to the plot
- the prose uses clear foreshadowing
- the hero's inner monologue helps drive the turn

The simulation models a child chosen for a dawn errand in a ceremonial gown.
A visible hazard threatens the gown on the way to the shrine. An elder predicts
the trouble and chooses a fitting remedy. If the remedy is strong enough for the
hazard and delay, the journey succeeds in time; if not, the gown is damaged and
the blessing comes late, though the child still learns and changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py --quest rain --hazard briars
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py --hazard marble
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py --response run_faster
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py --all
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gown_foreshadowing_inner_monologue_myth.py --verify
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
        female = {"girl", "woman", "mother", "grandmother", "priestess"}
        male = {"boy", "man", "father", "grandfather", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "priestess": "priestess",
            "priest": "priest",
            "mother": "mother",
            "father": "father",
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
class Quest:
    id: str
    season_line: str
    shrine: str
    vessel: str
    charge: str
    boon: str
    closing: str
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
class Hazard:
    id: str
    label: str
    the: str
    kind: str
    severity: int
    omen: str
    path_line: str
    wound_line: str
    trace_word: str
    risky: bool = True
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
    guards: set[str]
    prepare_text: str
    success_text: str
    fail_text: str
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


def _r_damage_feelings(world: World) -> list[str]:
    gown = world.entities.get("gown")
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    if gown is None or hero is None or elder is None:
        return []
    damaged = gown.meters["torn"] + gown.meters["soaked"] + gown.meters["singed"]
    if damaged < THRESHOLD:
        return []
    sig = ("damage_feelings", int(damaged))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    elder.memes["care"] += 1
    return []


def _r_blessing_hope(world: World) -> list[str]:
    village = world.entities.get("village")
    if village is None:
        return []
    if village.meters["blessed"] < THRESHOLD:
        return []
    sig = ("blessing_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.memes["hope"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_feelings", tag="emotional", apply=_r_damage_feelings),
    Rule(name="blessing_hope", tag="emotional", apply=_r_blessing_hope),
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


def hazard_at_risk(hazard: Hazard) -> bool:
    return hazard.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(hazard: Hazard, response: Response) -> bool:
    return hazard.kind in response.guards and response.sense >= SENSE_MIN


def journey_severity(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_timely(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= journey_severity(hazard, delay)


QUESTS = {
    "rain": Quest(
        id="rain",
        season_line="For three weeks the cisterns had shown their stony bottoms, and the barley leaves had begun to curl.",
        shrine="the Hill of Jars",
        vessel="a blue bowl of first water",
        charge="ask the cloud mothers to open their hands",
        boon="rain came drumming over the roofs and fields",
        closing="By evening, children were laughing under fresh rain while the once-careful gown hung safe beside the fire.",
        tags={"rain", "shrine"},
    ),
    "dawn": Quest(
        id="dawn",
        season_line="On the year's longest night, the elders said the sun liked to be invited back with courtesy.",
        shrine="the East Gate of Light",
        vessel="a polished dish that held the temple flame",
        charge="wake the slow sun before the valley lost heart",
        boon="the sun climbed clear and gold above the hills",
        closing="The rooftops shone like honey, and the gown gleamed in that new light as if it had remembered the morning forever.",
        tags={"sun", "shrine"},
    ),
    "spring": Quest(
        id="spring",
        season_line="After a hard winter, the fig trees still stood quiet, waiting for the hidden water under the hill to stir.",
        shrine="the Stone Spring Door",
        vessel="a small basket of white seeds",
        charge="wake the sleeping spring beneath the rocks",
        boon="water rose singing from the stone mouth and ran through the channels",
        closing="Soon the gardens were whispering green, and the gown, mended and cared for, swayed above the bright new water.",
        tags={"spring", "shrine"},
    ),
}

HAZARDS = {
    "briars": Hazard(
        id="briars",
        label="briars",
        the="the briars",
        kind="snag",
        severity=2,
        omen="That morning a crow flew low over the path and left one black feather on the temple step, and the old people said cloth would be tested before the blessing came.",
        path_line="A shortcut curled through a hedge of red briars, where every thorn seemed to have a small, hungry hook.",
        wound_line="a thorn caught the trailing hem and tore a long whisper through the cloth",
        trace_word="torn",
        risky=True,
        tags={"briars", "thorn"},
    ),
    "mud": Hazard(
        id="mud",
        label="mud",
        the="the mud",
        kind="soak",
        severity=1,
        omen="Before sunrise, frogs sang from the ditches though no one had seen water there the night before, and the old women murmured that the ground meant to keep what brushed against it.",
        path_line="The nearest way dipped through a brown mud hollow where each step made a soft sucking sound.",
        wound_line="the hem drank the mud, darkening and dragging heavier with every step",
        trace_word="soaked",
        risky=True,
        tags={"mud", "ground"},
    ),
    "embers": Hazard(
        id="embers",
        label="embers",
        the="the embers",
        kind="scorch",
        severity=3,
        omen="At dawn the baker's chimney let out a twist of sparks that drifted uphill instead of down, and the elders said fire was looking for silk to kiss.",
        path_line="The quickest lane passed the kiln yard, where sleepy red embers still winked under gray ash.",
        wound_line="a wandering spark kissed the skirt and left a curling singe",
        trace_word="singed",
        risky=True,
        tags={"embers", "fire"},
    ),
    "marble": Hazard(
        id="marble",
        label="marble steps",
        the="the marble steps",
        kind="none",
        severity=0,
        omen="The dawn on the marble steps was bright and still.",
        path_line="The wide marble steps were smooth and clean.",
        wound_line="nothing happened at all",
        trace_word="safe",
        risky=False,
        tags={"stone"},
    ),
}

RESPONSES = {
    "gold_belt": Response(
        id="gold_belt",
        sense=3,
        power=2,
        guards={"snag", "soak"},
        prepare_text="looped a gold belt around the gown and lifted the long hem clear of the ground",
        success_text="With the hem held high, the child crossed lightly, and the danger passed under the gown instead of through it.",
        fail_text="Even with the hem lifted, the path fought back, and the gown could not stay wholly safe.",
        qa_text="lifted the gown with a gold belt so the hem would not drag into danger",
        tags={"belt", "gown"},
    ),
    "reed_clogs": Response(
        id="reed_clogs",
        sense=3,
        power=2,
        guards={"soak"},
        prepare_text="slipped reed clogs onto the child's feet and tied the gown up with a willow cord",
        success_text="The clogs kept the child's steps above the wet ground, and the tied hem swayed cleanly through the hollow.",
        fail_text="The mud was deeper than it looked, and even the tied hem could not keep every dark splash away.",
        qa_text="used reed clogs and a willow cord to keep the gown above the mud",
        tags={"clogs", "gown"},
    ),
    "dew_cloak": Response(
        id="dew_cloak",
        sense=3,
        power=3,
        guards={"scorch"},
        prepare_text="draped a dew-cool cloak over the gown so sparks would meet wet cloth first",
        success_text="The wandering sparks died with tiny sighs against the damp cloak, and the gown beneath stayed unharmed.",
        fail_text="The embers leapt hotter than expected, and the cloak saved much but not all of the silk beneath it.",
        qa_text="covered the gown with a dew-cool cloak so sparks would die before reaching the silk",
        tags={"cloak", "fire", "gown"},
    ),
    "run_faster": Response(
        id="run_faster",
        sense=1,
        power=1,
        guards={"snag", "soak", "scorch"},
        prepare_text="told the child simply to run faster",
        success_text="By luck alone, the danger was missed.",
        fail_text="Luck was not strong enough to guard a ceremonial gown.",
        qa_text="only told the child to run faster",
        tags={"luck"},
    ),
}

GIRL_NAMES = ["Iris", "Lyra", "Nia", "Tala", "Mira", "Dara", "Eira", "Leda"]
BOY_NAMES = ["Orin", "Tarin", "Elio", "Nico", "Soren", "Pavel", "Ivo", "Milo"]
TRAITS = ["careful", "patient", "swift", "hopeful", "earnest", "proud"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for qid in QUESTS:
        for hid, hazard in HAZARDS.items():
            if not hazard_at_risk(hazard):
                continue
            for rid, response in RESPONSES.items():
                if response_fits(hazard, response):
                    combos.append((qid, hid, rid))
    return combos


@dataclass
class StoryParams:
    quest: str
    hazard: str
    response: str
    name: str
    gender: str
    elder: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None
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


def _do_cross(world: World, hazard: Hazard, response: Response, delay: int, narrate: bool = True) -> None:
    gown = world.get("gown")
    village = world.get("village")
    severity = journey_severity(hazard, delay)
    timely = response.power >= severity
    world.facts["timely"] = timely
    world.facts["severity"] = severity
    world.facts["delay"] = delay
    if timely:
        gown.meters["protected"] += 1
        village.meters["blessed"] += 1
        world.facts["gown_harmed"] = False
    else:
        if hazard.kind == "snag":
            gown.meters["torn"] += 1
        elif hazard.kind == "soak":
            gown.meters["soaked"] += 1
        elif hazard.kind == "scorch":
            gown.meters["singed"] += 1
        gown.meters["marred"] += 1
        village.meters["blessed"] += 1
        village.meters["late"] += 1
        world.facts["gown_harmed"] = True
    propagate(world, narrate=narrate)


def predict_cross(world: World, hazard: Hazard, response: Response, delay: int) -> dict:
    sim = world.copy()
    _do_cross(sim, hazard, response, delay, narrate=False)
    gown = sim.get("gown")
    village = sim.get("village")
    return {
        "timely": sim.facts["timely"],
        "harmed": sim.facts["gown_harmed"],
        "late": village.meters["late"] >= THRESHOLD,
        "torn": gown.meters["torn"] >= THRESHOLD,
        "soaked": gown.meters["soaked"] >= THRESHOLD,
        "singed": gown.meters["singed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, quest: Quest, hazard: Hazard) -> None:
    hero.memes["duty"] += 1
    hero.memes["pride"] += 1
    world.say(quest.season_line)
    world.say(hazard.omen)
    world.say(
        f"So the temple chose {hero.id}, a {hero.traits[0]} {hero.type}, to carry "
        f"{quest.vessel} to {quest.shrine} and {quest.charge}."
    )
    world.say(
        f"{hero.id} wore a pale ceremonial gown, long in the skirt and bright at the sleeves, "
        f"because the people said blessings liked to see beauty arrive with clean hands."
    )
    world.say(
        f"{elder.label_word.capitalize()} walked beside {hero.pronoun('object')}, not to take the task away, "
        f"but to help the task reach its end."
    )


def path_and_thought(world: World, hero: Entity, quest: Quest, hazard: Hazard) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Below {quest.shrine}, {hazard.path_line}"
    )
    world.say(
        f'{hero.id} looked at the sky, where morning was already lifting. '
        f'"If I am slow, the blessing may miss its hour," {hero.pronoun()} thought. '
        f'"But if I hurry carelessly, what will become of this gown, and of the gift I carry?"'
    )


def warn(world: World, hero: Entity, elder: Entity, quest: Quest, hazard: Hazard,
         response: Response, delay: int) -> None:
    pred = predict_cross(world, hazard, response, delay)
    world.facts["predicted_harmed"] = pred["harmed"]
    world.facts["predicted_late"] = pred["late"]
    if pred["harmed"]:
        line = (
            f'"Child," said {elder.label_word}, "the path is asking a price. '
            f'If we go as the morning pushes us, {hazard.the} will touch the gown, '
            f'and even a holy errand may arrive marked and late."'
        )
    else:
        line = (
            f'"Child," said {elder.label_word}, "the path is sharp, but not sharper than good preparation. '
            f'If we are wise now, the blessing can still arrive in its proper hour."'
        )
    world.say(line)


def prepare(world: World, hero: Entity, elder: Entity, response: Response) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"Then {elder.label_word} {response.prepare_text}."
    )
    world.say(
        f'{hero.id} drew one long breath and thought, "A gown is not only for being admired. '
        f'Today it must travel wisely with me."'
    )


def crossing(world: World, hero: Entity, elder: Entity, quest: Quest, hazard: Hazard,
             response: Response, delay: int) -> None:
    _do_cross(world, hazard, response, delay, narrate=True)
    if world.facts["timely"]:
        hero.memes["relief"] += 1
        hero.memes["awe"] += 1
        world.say(response.success_text)
        world.say(
            f"{hero.id} climbed the last stones to {quest.shrine} before the edge of morning tipped fully over the hill."
        )
    else:
        hero.memes["fear"] += 1
        hero.memes["humility"] += 1
        world.say(response.fail_text)
        world.say(
            f"Still, {hazard.wound_line}, and {hero.id} felt the errand grow heavier in {hero.pronoun('possessive')} hands."
        )
        world.say(
            f'"I thought only of being fast," {hero.pronoun()} thought, "and forgot that sacred things ask for care first."'
        )
        world.say(
            f"{elder.label_word.capitalize()} did not scold. {elder.pronoun().capitalize()} smoothed the harmed cloth as best {elder.pronoun()} could and led the child onward."
        )


def blessing(world: World, hero: Entity, elder: Entity, quest: Quest) -> None:
    village = world.get("village")
    if world.facts["timely"]:
        world.say(
            f"At the shrine, {hero.id} set down {quest.vessel}. The stones seemed to listen, the air grew still, and then {quest.boon}."
        )
        world.say(
            f"The people said the gods had seen not only the gift, but the care that carried it."
        )
    else:
        world.say(
            f"At the shrine, {hero.id} set down {quest.vessel} and told the whole truth about the journey and the marred gown."
        )
        world.say(
            f"The stones did not close their ears. A slower mercy answered, and {quest.boon}."
        )
        world.say(
            f"The people said the gods love honesty almost as much as beauty, and sometimes more."
        )
    village.meters["blessed"] += 0  # explicit no-op; blessing state already set in crossing


def ending(world: World, hero: Entity, elder: Entity, quest: Quest) -> None:
    gown = world.get("gown")
    if world.facts["timely"]:
        hero.memes["joy"] += 1
        world.say(
            f"Afterward, {hero.id} folded the gown carefully instead of tossing it over a chair, for {hero.pronoun()} had learned that holy things are guarded by small wise acts."
        )
        world.say(quest.closing)
    else:
        hero.memes["resolve"] += 1
        elder.memes["love"] += 1
        world.say(
            f"That evening, {hero.id} sat with {elder.label_word} and mended the gown stitch by stitch. "
            f"After that day, whenever a task was sacred, {hero.pronoun()} checked the path before taking the first step."
        )
        world.say(quest.closing)


def tell(quest: Quest, hazard: Hazard, response: Response,
         name: str = "Iris", gender: str = "girl", elder_type: str = "grandmother",
         trait: str = "careful", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=name,
        role="hero",
        traits=[trait],
        attrs={"name": name},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
        traits=["wise"],
        attrs={},
    ))
    gown = world.add(Entity(
        id="gown",
        kind="thing",
        type="gown",
        label="gown",
        role="garment",
        attrs={"owner": name},
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="village",
        role="community",
        attrs={},
    ))

    world.facts["hero_name"] = name
    world.facts["quest"] = quest
    world.facts["hazard"] = hazard
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["timely"] = False
    world.facts["gown_harmed"] = False
    world.facts["predicted_harmed"] = False
    world.facts["predicted_late"] = False
    world.facts["severity"] = 0

    introduce(world, hero, elder, quest, hazard)
    world.para()
    path_and_thought(world, hero, quest, hazard)
    warn(world, hero, elder, quest, hazard, response, delay)
    prepare(world, hero, elder, response)
    world.para()
    crossing(world, hero, elder, quest, hazard, response, delay)
    blessing(world, hero, elder, quest)
    world.para()
    ending(world, hero, elder, quest)

    world.facts.update(
        hero=hero,
        elder=elder,
        gown=gown,
        village=village,
        outcome="timely" if world.facts["timely"] else "late",
    )
    return world


KNOWLEDGE = {
    "gown": [
        (
            "What is a gown?",
            "A gown is a long dress or robe. In stories, a special gown can show that a job or ceremony matters."
        )
    ],
    "briars": [
        (
            "What are briars?",
            "Briars are thorny plants with sharp hooks. They can snag cloth and scratch skin if you brush past them."
        )
    ],
    "mud": [
        (
            "Why does mud make clothes heavy?",
            "Mud is wet dirt, and it sticks to cloth. When cloth soaks it up, the cloth gets darker, dirtier, and heavier."
        )
    ],
    "embers": [
        (
            "What is an ember?",
            "An ember is a small hot piece left from a fire. It can still burn or scorch things even when there is no big flame."
        )
    ],
    "belt": [
        (
            "Why would lifting a gown help on a rough path?",
            "If the hem is lifted, it does not drag over thorns or wet ground. Keeping cloth off the danger helps keep it clean and whole."
        )
    ],
    "clogs": [
        (
            "What are clogs?",
            "Clogs are sturdy shoes with thick soles. They can help keep feet above wet or muddy ground."
        )
    ],
    "cloak": [
        (
            "What does a cloak do?",
            "A cloak is an outer covering worn over clothes. It can keep what is underneath safer from cold, rain, or even small sparks."
        )
    ],
    "shrine": [
        (
            "What is a shrine?",
            "A shrine is a special place where people pray, leave gifts, or ask for help. In myths, it is often where the world listens back."
        )
    ],
    "rain": [
        (
            "Why did old stories connect rain with blessings?",
            "Rain helps crops and trees grow, so people long ago often spoke of rain as a gift from the sky. That made rain feel holy and precious."
        )
    ],
    "sun": [
        (
            "Why is dawn important in many myths?",
            "Dawn is when darkness ends and light begins again. Because of that, many myths treat dawn like a promise being kept."
        )
    ],
    "spring": [
        (
            "Why is a spring important?",
            "A spring is a place where water comes out of the ground. Fresh water keeps plants, animals, and people alive."
        )
    ],
}
KNOWLEDGE_ORDER = ["gown", "briars", "mud", "embers", "belt", "clogs", "cloak", "shrine", "rain", "sun", "spring"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    hazard = f["hazard"]
    response = f["response"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth for a young child that includes the word "gown", uses foreshadowing and inner monologue, '
        f"and centers on a child carrying {quest.vessel} to {quest.shrine}."
    )
    if outcome == "timely":
        return [
            base,
            f"Tell a mythic story where a wise elder sees that {hazard.the} could harm a ceremonial gown, prepares {response.id.replace('_', ' ')}, and the child reaches the shrine in time.",
            f"Write a gentle myth in which an omen warns of danger to a gown, the hero listens inwardly, accepts help, and a blessing comes because care was stronger than haste.",
        ]
    return [
        base,
        f"Tell a mythic story where a child in a ceremonial gown crosses near {hazard.the}, and even a wise preparation is not quite enough, so the blessing comes late but the child learns reverence.",
        f"Write a myth with foreshadowing and inner thoughts where a sacred errand marks a gown, honesty matters at the shrine, and the ending shows the child behaving more wisely afterward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    hazard = f["hazard"]
    response = f["response"]
    outcome = f["outcome"]
    name = hero.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child chosen for a sacred errand, and a wise {elder.label_word} walking beside {hero.pronoun('object')}. The story also centers on the ceremonial gown {hero.pronoun()} must protect."
        ),
        (
            f"Why was {name} wearing a gown?",
            f"{name} wore a ceremonial gown because the journey to {quest.shrine} was holy, not ordinary. In this myth, the gown shows that the task should be carried with beauty and care."
        ),
        (
            f"What was the foreshadowing in the story?",
            f"The omen came early, before the trouble began, when the morning gave a warning sign tied to cloth and danger. That hint prepared the reader for the moment when {hazard.the} would test the gown."
        ),
        (
            f"What was {name} thinking on the path?",
            f"{name} worried inside about being too slow and missing the hour of blessing. At the same time, {hero.pronoun()} wondered what would happen to the gown if haste won over care."
        ),
        (
            f"How did the elder try to help?",
            f"The elder {response.qa_text}. The help was chosen because it matched the kind of danger waiting on the path."
        ),
    ]
    if outcome == "timely":
        qa.append(
            (
                f"Why did the journey succeed in time?",
                f"It succeeded because the warning was understood early and the remedy fit the danger. The child reached {quest.shrine} in time, so the blessing could arrive in its proper hour."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the blessing answering the village and with the gown still safe. The final image shows that {name} had learned to treat sacred things carefully even after the danger was past."
            )
        )
    else:
        damage_word = hazard.trace_word
        qa.append(
            (
                f"What happened to the gown?",
                f"The gown was {damage_word} on the journey, even though the elder tried to help first. That harm mattered because the gown was part of the sacred errand, not just ordinary clothing."
            )
        )
        qa.append(
            (
                "Why did the blessing still come?",
                f"The blessing still came because {name} told the truth at the shrine instead of hiding the mistake. In the story's myth logic, honesty and humility opened the way when perfect beauty was gone."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, {name} had stopped thinking only about speed and had begun thinking about reverence and preparation. The later mending scene proves the lesson stayed with the child after the journey was over."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gown", "shrine"} | set(f["hazard"].tags) | set(f["quest"].tags) | set(f["response"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} timely={world.facts.get('timely')} severity={world.facts.get('severity')} delay={world.facts.get('delay')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="rain",
        hazard="briars",
        response="gold_belt",
        name="Iris",
        gender="girl",
        elder="grandmother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        quest="dawn",
        hazard="mud",
        response="reed_clogs",
        name="Elio",
        gender="boy",
        elder="grandfather",
        trait="earnest",
        delay=0,
    ),
    StoryParams(
        quest="spring",
        hazard="embers",
        response="dew_cloak",
        name="Mira",
        gender="girl",
        elder="priestess",
        trait="hopeful",
        delay=0,
    ),
    StoryParams(
        quest="rain",
        hazard="embers",
        response="dew_cloak",
        name="Orin",
        gender="boy",
        elder="priest",
        trait="swift",
        delay=1,
    ),
    StoryParams(
        quest="spring",
        hazard="briars",
        response="gold_belt",
        name="Tala",
        gender="girl",
        elder="grandmother",
        trait="proud",
        delay=1,
    ),
]


def explain_rejection(hazard: Hazard) -> str:
    if not hazard.risky:
        return (
            f"(No story: {hazard.the} would not truly threaten a ceremonial gown, so there is no honest tension. "
            f"Pick a hazard like briars, mud, or embers.)"
        )
    return "(No story: this hazard does not create a gown-risk in this world.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a wiser preparation such as {better}.)"
    )


def explain_combo(hazard: Hazard, response: Response) -> str:
    if not response_fits(hazard, response):
        guards = ", ".join(sorted(response.guards))
        return (
            f"(No story: {response.id} guards [{guards}], but {hazard.the} causes {hazard.kind}. "
            f"The remedy must match the danger to the gown.)"
        )
    return "(No story: the chosen remedy does not fit the hazard.)"


def outcome_of(params: StoryParams) -> str:
    return "timely" if is_timely(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "late"


ASP_RULES = r"""
hazard(H)      :- hazard_risky(H).
sensible(R)    :- response(R), sense(R,S), sense_min(M), S >= M.
fits(H,R)      :- hazard_kind(H,K), guards(R,K), sensible(R).
valid(Q,H,R)   :- quest(Q), hazard(H), response(R), fits(H,R).

severity(H,V)  :- chosen_hazard(H), hazard_severity(H,S), delay(D), V = S + D.
timely         :- chosen_hazard(H), chosen_response(R), response_power(R,P), severity(H,V), P >= V.
outcome(timely):- timely.
outcome(late)  :- not timely.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid, hazard in HAZARDS.items():
        if hazard.risky:
            lines.append(asp.fact("hazard_risky", hid))
        lines.append(asp.fact("hazard_kind", hid, hazard.kind))
        lines.append(asp.fact("hazard_severity", hid, hazard.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("response_power", rid, response.power))
        for guard in sorted(response.guards):
            lines.append(asp.fact("guards", rid, guard))
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

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a ceremonial gown, a dangerous path, and a wise preparation."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "priestess", "priest"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much the morning presses the journey")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard:
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(hazard):
            raise StoryError(explain_rejection(hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.hazard and args.response:
        hazard = HAZARDS[args.hazard]
        response = RESPONSES[args.response]
        if not response_fits(hazard, response):
            raise StoryError(explain_combo(hazard, response))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, hazard, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "priestess", "priest"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        quest=quest,
        hazard=hazard,
        response=response,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.elder not in {"grandmother", "grandfather", "priestess", "priest"}:
        raise StoryError(f"(Unknown elder type: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    quest = QUESTS[params.quest]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]

    if not hazard_at_risk(hazard):
        raise StoryError(explain_rejection(hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_fits(hazard, response):
        raise StoryError(explain_combo(hazard, response))

    world = tell(
        quest=quest,
        hazard=hazard,
        response=response,
        name=params.name,
        gender=params.gender,
        elder_type=params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, hazard, response) combos:\n")
        for quest, hazard, response in combos:
            print(f"  {quest:8} {hazard:8} {response}")
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
            header = f"### {p.name}: {p.quest} / {p.hazard} / {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
