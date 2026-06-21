#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py
=========================================================

A standalone story world about a small seaside adventure where children meet a
real problem, choose bravery over panic, and use semaphore to ask for help.

Premise
-------
Two children set off on an adventure to fetch a small prize from a dramatic
shore place. A natural hazard cuts them off or threatens to cut them off. One
possible move is rash and dangerous. The brave move is calmer: admit the danger,
use semaphore from a signal point, and let the right grown-up helper come or
answer.

Coverage is intentionally narrow and reasoned:
- A setting must actually have a signal point and be visible to a helper.
- A helper must actually know how to answer the chosen hazard.
- Some stories become a near-miss: the cautious child notices the danger early,
  and the children signal before crossing.
- Other stories become a rescue: the children are already stranded and must wait
  bravely for help.

Run it
------
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py --setting signal_hill --hazard rising_tide
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py --helper cave_guide
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py --all
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py --qa --json
python storyworlds/worlds/gpt-5.4/semaphore_bravery_adventure.py --verify
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
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful"}


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
        female = {"girl", "mother", "woman", "keeper_woman", "ranger_woman", "guide_woman"}
        male = {"boy", "father", "man", "keeper_man", "ranger_man", "guide_man", "captain_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "keeper_woman": "keeper",
            "keeper_man": "keeper",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
            "guide_woman": "guide",
            "guide_man": "guide",
            "captain_man": "captain",
        }
        return mapping.get(self.type, self.type)
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
    scene: str
    trail: str
    signal_spot: str
    far_place: str
    safe_place: str
    helpers_visible: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    reason: str
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
class Hazard:
    id: str
    cue: str
    problem: str
    rash_move: str
    warning: str
    signal_need: str
    rescue_need: str
    danger_kind: str
    severity: int
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
    title: str
    station: str
    methods: dict[str, str] = field(default_factory=dict)
    arrivals: dict[str, str] = field(default_factory=dict)
    lesson: str = ""
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    if place.meters["blocked"] < THRESHOLD and place.meters["stranded"] < THRESHOLD:
        return out
    sig = ("danger", "place")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["danger"] += 1
    for role in ("hero", "friend"):
        kid = world.get(role)
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_signal(world: World) -> list[str]:
    out: list[str] = []
    if world.get("flags").meters["raised"] < THRESHOLD:
        return out
    helper = world.get("helper")
    sig = ("helper_alerted", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["alerted"] += 1
    world.facts["signal_seen"] = True
    out.append("__signal__")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    place = world.get("place")
    if helper.meters["alerted"] < THRESHOLD:
        return out
    if place.meters["danger"] < THRESHOLD and place.meters["blocked"] < THRESHOLD:
        return out
    sig = ("rescued", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["safe"] += 1
    place.meters["danger"] = 0.0
    place.meters["blocked"] = 0.0
    place.meters["stranded"] = 0.0
    for role in ("hero", "friend"):
        kid = world.get(role)
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    out.append("__rescued__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="signal", tag="social", apply=_r_signal),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
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


def has_line_of_sight(setting: Setting, helper_id: str) -> bool:
    return helper_id in setting.helpers_visible


def helper_can_answer(helper: Helper, hazard_id: str) -> bool:
    return hazard_id in helper.methods and hazard_id in helper.arrivals


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hazard_id in sorted(setting.hazards):
            for helper_id, helper in HELPERS.items():
                if has_line_of_sight(setting, helper_id) and helper_can_answer(helper, hazard_id):
                    combos.append((setting_id, hazard_id, helper_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def outcome_of(params: "StoryParams") -> str:
    if params.lead == "early" and params.friend_trait in CAUTIOUS_TRAITS:
        return "averted"
    return "rescued"


def predict_rash(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    place = sim.get("place")
    place.meters["danger"] += 1
    if world.facts.get("already_crossed"):
        place.meters["stranded"] += 1
    else:
        place.meters["blocked"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": place.meters["danger"],
        "fear": sim.get("hero").memes["fear"] + sim.get("friend").memes["fear"],
        "risk_text": hazard.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting, goal: Goal) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"On a bright morning, {hero.id} and {friend.id} set off for {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f"They were on an adventure to find {goal.phrase}, because {goal.reason}"
    )
    world.say(
        f"The path wound along {setting.trail}, and beyond it waited {setting.far_place}."
    )


def reach_edge(world: World, hero: Entity, friend: Entity, setting: Setting, goal: Goal, already_crossed: bool) -> None:
    if already_crossed:
        world.say(
            f"Together they reached {setting.far_place}, where {goal.phrase} glimmered in a crack of stone."
        )
    else:
        world.say(
            f"They stopped just short of {setting.far_place}, where they could already see {goal.phrase} from the path."
        )
    world.facts["already_crossed"] = already_crossed


def hazard_arrives(world: World, hazard: Hazard) -> None:
    place = world.get("place")
    if world.facts.get("already_crossed"):
        place.meters["stranded"] += 1
    else:
        place.meters["blocked"] += 1
    world.facts["hazard_seen"] = True
    propagate(world, narrate=False)
    world.say(hazard.cue)
    world.say(hazard.problem)


def warn(world: World, friend: Entity, hero: Entity, hazard: Hazard) -> None:
    pred = predict_rash(world, hazard)
    friend.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{friend.id} grabbed {hero.id}\'s sleeve. "{hazard.warning}" {friend.pronoun()} said.'
    )
    if friend.memes["caution"] >= 6:
        world.say(
            f"{friend.id} was not trying to spoil the adventure. {friend.pronoun().capitalize()} could already picture how quickly a brave game could turn into a real emergency."
        )


def brave_choice(world: World, hero: Entity, friend: Entity, hazard: Hazard, setting: Setting) -> None:
    hero.memes["bravery"] += 1
    hero.memes["panic"] = 0.0
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} looked at {setting.signal_spot}, then at the trouble in front of them. "
        f'"I still want to be brave," {hero.pronoun()} said, "but not by doing the dangerous thing."'
    )
    world.say(
        f"So instead of trying to {hazard.rash_move}, the children ran to {setting.signal_spot}."
    )


def signal_for_help(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    flags = world.get("flags")
    flags.meters["raised"] += 1
    hero.meters["signaling"] += 1
    friend.meters["signaling"] += 1
    world.facts["used_semaphore"] = True
    world.say(
        f"There, they lifted the bright semaphore flags and worked through the careful positions they had been taught."
    )
    world.say(
        f"{hero.id} held one flag high while {friend.id} matched the next sign, spelling out {hazard.signal_need}."
    )
    propagate(world, narrate=False)


def averted_resolution(world: World, helper: Entity, helper_cfg: Helper, setting: Setting, goal: Goal, hazard: Hazard, hero: Entity, friend: Entity) -> None:
    helper.meters["advised"] += 1
    world.say(
        f"From {helper_cfg.station}, the {helper_cfg.title} spotted the semaphore at once and answered with broad, clear signals."
    )
    world.say(
        f"{helper.pronoun().capitalize()} told them to stay on the safe side and wait while the danger passed. "
        f"That answer felt slower than rushing ahead, but it was the truest kind of bravery."
    )
    world.para()
    world.say(
        f"After a while, the path to {setting.far_place} was safe again. Then the children crossed carefully, found {goal.phrase}, and tucked it away with grins."
    )
    world.say(
        f"On the walk home, they kept glancing back at {setting.signal_spot}. They had not won the adventure by being reckless. They had won it by being wise enough to ask for help."
    )


def rescue_resolution(world: World, helper: Entity, helper_cfg: Helper, setting: Setting, goal: Goal, hazard: Hazard) -> None:
    place = world.get("place")
    place.meters["safe"] += 1
    arrival = helper_cfg.arrivals[hazard.id]
    method = helper_cfg.methods[hazard.id]
    world.say(
        f"Far off at {helper_cfg.station}, the {helper_cfg.title} saw the semaphore message and answered right away."
    )
    world.say(
        f"Soon {arrival} {method}"
    )
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"When the children reached {setting.safe_place} again, their knees felt wobbly, but their hearts felt strong. The adventure had turned frightening, and they had still chosen the right thing."
    )
    world.say(
        f"They kept {goal.phrase} as a memento, but the bigger treasure was the lesson they would remember: {helper_cfg.lesson}"
    )


def ending_image(world: World, hero: Entity, friend: Entity, setting: Setting, goal: Goal) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"The next afternoon they stood on {setting.signal_spot} again, only this time for practice. "
        f"They clicked the semaphore flags into neat shapes against the sky and laughed when the wind tugged at the cloth."
    )
    world.say(
        f"{goal.ending}"
    )


SETTINGS = {
    "signal_hill": Setting(
        id="signal_hill",
        place="Signal Hill",
        scene="Below them the sea flashed blue, and an old stone post for ship signals stood on the ridge like a watchful giant.",
        trail="a steep path above the cove",
        signal_spot="the signal post on the ridge",
        far_place="the shell ledge",
        safe_place="the hill path",
        helpers_visible={"lighthouse_keeper", "harbor_ranger"},
        hazards={"rising_tide", "rockfall"},
        tags={"hill", "sea"},
    ),
    "storm_beach": Setting(
        id="storm_beach",
        place="Storm Beach",
        scene="The shore was wide and silver, and a striped mast for emergency signals leaned beside the dunes.",
        trail="the firm sand between dune grass and surf",
        signal_spot="the striped signal mast",
        far_place="the driftwood point",
        safe_place="the upper dunes",
        helpers_visible={"harbor_ranger", "cave_guide"},
        hazards={"fog_bank", "rising_tide"},
        tags={"beach", "sea"},
    ),
    "echo_cliffs": Setting(
        id="echo_cliffs",
        place="Echo Cliffs",
        scene="White birds wheeled above the rocks, and a little signaling platform looked out over the water.",
        trail="the narrow cliff walk",
        signal_spot="the little signaling platform",
        far_place="the cave mouth",
        safe_place="the cliff gate",
        helpers_visible={"lighthouse_keeper", "cave_guide"},
        hazards={"rockfall", "fog_bank"},
        tags={"cliff", "sea"},
    ),
}

GOALS = {
    "map_tube": Goal(
        id="map_tube",
        label="map tube",
        phrase="a brass map tube",
        reason="they were pretending to be explorers hunting for the captain's lost route",
        ending="At sunset the brass tube shone on the windowsill, and beside it lay the folded semaphore chart they had used so bravely.",
        tags={"map"},
    ),
    "star_shell": Goal(
        id="star_shell",
        label="star shell",
        phrase="a star-shaped shell",
        reason="they wanted a treasure fit for the end of a sea quest",
        ending="That evening the star shell sat in a bowl by the lamp, while the semaphore flags dried nearby like quiet little sails.",
        tags={"shell"},
    ),
    "spyglass_key": Goal(
        id="spyglass_key",
        label="spyglass key",
        phrase="a tiny brass key from an old spyglass case",
        reason="they had promised to finish their pretend rescue mission before supper",
        ending="Before bed, the little brass key hung from a string by the door, and the semaphore flags rested underneath it like badges of good sense.",
        tags={"key"},
    ),
}

HAZARDS = {
    "rising_tide": Hazard(
        id="rising_tide",
        cue="But while they played at explorers, the sea crept in with cold, shining fingers.",
        problem="Water spread over the low stones and cut the easy way back.",
        rash_move="dash through the swirling water",
        warning="The tide is rising too fast. If we rush through, one of us could slip.",
        signal_need="HELP TIDE BLOCKED",
        rescue_need="children cut off by the rising tide",
        danger_kind="water",
        severity=2,
        tags={"tide", "water"},
    ),
    "fog_bank": Hazard(
        id="fog_bank",
        cue="Then a thick white fog came rolling over the shore and swallowed the markers one by one.",
        problem="The path ahead and the path behind both turned into a blank, confusing blur.",
        rash_move="wander into the fog",
        warning="We could walk the wrong way and end up near the edge or the surf.",
        signal_need="HELP FOG LOST PATH",
        rescue_need="children unable to find the safe path in fog",
        danger_kind="fog",
        severity=2,
        tags={"fog", "lost"},
    ),
    "rockfall": Hazard(
        id="rockfall",
        cue="Suddenly a clatter burst from above, and a scatter of stones bounced across the path.",
        problem="The narrow track was blocked by fresh rocks, and more pebbles still rattled down from the cliff.",
        rash_move="climb over the loose rocks",
        warning="Those stones are still sliding. If we climb there, the cliff might throw more down.",
        signal_need="HELP ROCKS ON PATH",
        rescue_need="children stopped by a small rockfall",
        danger_kind="rocks",
        severity=3,
        tags={"rocks", "cliff"},
    ),
}

HELPERS = {
    "lighthouse_keeper": Helper(
        id="lighthouse_keeper",
        type="keeper_woman",
        title="lighthouse keeper",
        station="the lighthouse balcony",
        methods={
            "rising_tide": "and sent down a rope-guided basket car from the cliff track to fetch them safely over the wet stones.",
            "fog_bank": "and answered with bell rings and semaphore directions until they could follow the safe route by sound and signal.",
            "rockfall": "and came along the upper path with a safety rope, leading them around the blocked place one at a time.",
        },
        arrivals={
            "rising_tide": "A small basket car hummed down the cliff line, swaying above the spray,",
            "fog_bank": "A clear bell began to ring from the lighthouse,",
            "rockfall": "A lantern winked from above, and the keeper appeared on the upper steps,",
        },
        lesson="real bravery is not pretending danger is small; it is seeing danger clearly and making the wise call.",
        tags={"lighthouse", "rescue"},
    ),
    "harbor_ranger": Helper(
        id="harbor_ranger",
        type="ranger_man",
        title="harbor ranger",
        station="the harbor watch hut",
        methods={
            "rising_tide": "and steered a little rescue boat around the rocks to pick them up.",
            "fog_bank": "and walked out along the beach line with a bright horn and a guide rope for them to follow.",
            "rockfall": "and brought helmets and a handcart by the safer inland track, then guided them around the blocked path.",
        },
        arrivals={
            "rising_tide": "A red rescue boat bobbed through the chop,",
            "fog_bank": "A horn called from the gray mist,",
            "rockfall": "Boots thumped on the upper path, and the ranger arrived,",
        },
        lesson="bravery can sound quiet. Sometimes it is a steady voice saying, We need help now.",
        tags={"harbor", "rescue"},
    ),
    "cave_guide": Helper(
        id="cave_guide",
        type="guide_woman",
        title="cave guide",
        station="the cave guide's lookout",
        methods={
            "rising_tide": "and waved them toward a high rescue ladder that led back above the wash.",
            "fog_bank": "and answered with semaphore from the lookout, turning the confusing white air into a step-by-step path home.",
        },
        arrivals={
            "rising_tide": "A yellow jacket flashed from the lookout,",
            "fog_bank": "A pair of bright flags moved in the mist,",
        },
        lesson="being adventurous does not mean charging ahead. It means keeping your head and using what you know.",
        tags={"guide", "rescue"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Tessa", "Nora", "Ada", "Mina", "Ruth", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Jude", "Eli", "Theo", "Miles", "Sam", "Ben"]
TRAITS = ["careful", "steady", "thoughtful", "bold", "eager", "curious"]


@dataclass
class StoryParams:
    setting: str
    hazard: str
    helper: str
    goal: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    friend_trait: str
    lead: str = "late"
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
    friend = f["friend"]
    setting = f["setting"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the word "semaphore" and shows bravery as asking for help before danger becomes worse.',
            f"Tell a seaside adventure where {hero.id} and {friend.id} notice {hazard.id.replace('_', ' ')} in time, use semaphore from {setting.signal_spot}, and wait bravely instead of rushing ahead.",
            f"Write a gentle adventure about children on a treasure hunt who prove that bravery can mean stopping, thinking, and signaling for help.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "semaphore" and shows bravery during a seaside emergency.',
        f"Tell an adventure where {hero.id} and {friend.id} become trapped by {hazard.id.replace('_', ' ')}, then use semaphore to call a helper and stay brave while waiting.",
        f"Write a child-facing rescue story where the exciting turn comes when the children choose the wise kind of bravery instead of a reckless escape.",
    ]


KNOWLEDGE = {
    "semaphore": [
        (
            "What is semaphore?",
            "Semaphore is a way to send messages with two flags held in different positions. Each position stands for a letter, so people far away can read the signal."
        )
    ],
    "tide": [
        (
            "What is a tide?",
            "A tide is the sea moving higher or lower along the shore. When the tide rises, water can cover rocks and paths that were dry before."
        )
    ],
    "fog": [
        (
            "Why can fog be dangerous near the shore?",
            "Fog makes it hard to see paths, edges, and other people. If you cannot see clearly, it is easier to get lost or walk somewhere unsafe."
        )
    ],
    "rocks": [
        (
            "Why are loose rocks dangerous on a cliff path?",
            "Loose rocks can slide under your feet or fall from above. That can make you slip or get hurt."
        )
    ],
    "lighthouse": [
        (
            "What does a lighthouse keeper do?",
            "A lighthouse keeper watches the shore and helps keep boats and people safe. A keeper may use lights, bells, or signals to warn others."
        )
    ],
    "harbor": [
        (
            "What does a harbor ranger do?",
            "A harbor ranger watches the beach and water for trouble. Rangers help people find safe paths and come quickly when someone needs rescue."
        )
    ],
    "guide": [
        (
            "What does a guide do?",
            "A guide knows the safe way through a place. Guides help people avoid danger because they understand the land and the weather."
        )
    ],
    "bravery": [
        (
            "Does being brave always mean doing something scary by yourself?",
            "No. Real bravery can mean stopping, thinking, and asking for help when a problem is too dangerous to handle alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["semaphore", "tide", "fog", "rocks", "lighthouse", "harbor", "guide", "bravery"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    hazard = f["hazard"]
    helper = f["helper"]
    goal = f["goal"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children on an adventure at {setting.place}. They went looking for {goal.phrase}."
        ),
        (
            "What problem did the children face?",
            f"They faced {hazard.id.replace('_', ' ')}, and it made the route unsafe. The danger changed their game into a real problem that needed a careful choice."
        ),
        (
            "What dangerous thing did they decide not to do?",
            f"They decided not to {hazard.rash_move}. That choice mattered because {hazard.warning.split('.')[0].lower()}."
        ),
        (
            "How did the children ask for help?",
            f"They used semaphore flags from {setting.signal_spot}. They sent a clear message so a faraway helper could understand exactly what kind of trouble they were in."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                "Why was their choice brave if they had not crossed into the danger yet?",
                f"It was brave because they stopped before the problem trapped them. They cared more about getting home safely than about looking daring for one more minute."
            )
        )
        qa.append(
            (
                "What did the helper do?",
                f"The {helper.title} answered their semaphore and told them to wait on the safe side. Because they listened, they could finish the adventure later without anyone getting hurt."
            )
        )
    else:
        qa.append(
            (
                "What did the helper do after seeing the semaphore?",
                f"The {helper.title} saw the signal and came with the right kind of rescue. The children were saved because their message was clear and because they stayed put instead of taking a bigger risk."
            )
        )
        qa.append(
            (
                "What did the children learn about bravery?",
                f"They learned that bravery is not the same as rushing into danger. In this adventure, bravery meant keeping calm, using semaphore, and trusting help to come."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"semaphore", "bravery"}
    hazard = world.facts["hazard"]
    helper = world.facts["helper"]
    if hazard.id == "rising_tide":
        tags.add("tide")
    if hazard.id == "fog_bank":
        tags.add("fog")
    if hazard.id == "rockfall":
        tags.add("rocks")
    if helper.id == "lighthouse_keeper":
        tags.add("lighthouse")
    if helper.id == "harbor_ranger":
        tags.add("harbor")
    if helper.id == "cave_guide":
        tags.add("guide")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def tell(
    setting: Setting,
    hazard: Hazard,
    helper_cfg: Helper,
    goal: Goal,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    friend_trait: str = "careful",
    lead: str = "late",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=[friend_trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.title, role="helper"))
    place = world.add(Entity(id="place", type="place", label=setting.place))
    flags = world.add(Entity(id="flags", type="thing", label="semaphore flags"))
    treasure = world.add(Entity(id="goal", type="thing", label=goal.label))

    hero.attrs["name"] = hero_name
    friend.attrs["name"] = friend_name
    helper.attrs["title"] = helper_cfg.title
    friend.memes["caution"] = initial_caution(friend_trait)
    hero.memes["bravery"] = 4.0
    hero.memes["panic"] = 0.0
    friend.memes["trust"] = 4.0
    place.meters["blocked"] = 0.0
    place.meters["stranded"] = 0.0
    place.meters["danger"] = 0.0
    place.meters["safe"] = 0.0
    flags.meters["raised"] = 0.0
    helper.meters["alerted"] = 0.0
    helper.meters["advised"] = 0.0

    world.facts.update(
        setting=setting,
        hazard=hazard,
        helper=helper_cfg,
        goal=goal,
        hero=hero,
        friend=friend,
        lead=lead,
        used_semaphore=False,
        signal_seen=False,
        already_crossed=False,
        hazard_seen=False,
    )

    introduce(world, hero, friend, setting, goal)
    world.para()
    already_crossed = lead == "late"
    reach_edge(world, hero, friend, setting, goal, already_crossed)
    hazard_arrives(world, hazard)
    warn(world, friend, hero, hazard)
    world.para()
    brave_choice(world, hero, friend, hazard, setting)
    signal_for_help(world, hero, friend, hazard)

    outcome = "averted" if lead == "early" and friend_trait in CAUTIOUS_TRAITS else "rescued"
    world.facts["outcome"] = outcome

    if outcome == "averted":
        averted_resolution(world, helper, helper_cfg, setting, goal, hazard, hero, friend)
    else:
        rescue_resolution(world, helper, helper_cfg, setting, goal, hazard)
    world.para()
    ending_image(world, hero, friend, setting, goal)
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def render_story(world: World) -> str:
    text = world.render()
    hero = world.get("hero")
    friend = world.get("friend")
    helper = world.get("helper")
    return (
        text.replace("hero", display_name(hero))
        .replace("friend", display_name(friend))
        .replace("helper", helper.label)
    )


CURATED = [
    StoryParams(
        setting="signal_hill",
        hazard="rising_tide",
        helper="lighthouse_keeper",
        goal="star_shell",
        hero="Lina",
        hero_gender="girl",
        friend="Owen",
        friend_gender="boy",
        friend_trait="careful",
        lead="late",
    ),
    StoryParams(
        setting="storm_beach",
        hazard="fog_bank",
        helper="harbor_ranger",
        goal="map_tube",
        hero="Finn",
        hero_gender="boy",
        friend="Mara",
        friend_gender="girl",
        friend_trait="steady",
        lead="early",
    ),
    StoryParams(
        setting="echo_cliffs",
        hazard="rockfall",
        helper="lighthouse_keeper",
        goal="spyglass_key",
        hero="Ada",
        hero_gender="girl",
        friend="Jude",
        friend_gender="boy",
        friend_trait="thoughtful",
        lead="late",
    ),
    StoryParams(
        setting="storm_beach",
        hazard="rising_tide",
        helper="cave_guide",
        goal="star_shell",
        hero="Theo",
        hero_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        friend_trait="curious",
        lead="late",
    ),
    StoryParams(
        setting="echo_cliffs",
        hazard="fog_bank",
        helper="cave_guide",
        goal="map_tube",
        hero="Nora",
        hero_gender="girl",
        friend="Miles",
        friend_gender="boy",
        friend_trait="careful",
        lead="early",
    ),
]


def explain_invalid_combo(setting_id: str, hazard_id: str, helper_id: str) -> str:
    setting = SETTINGS[setting_id]
    helper = HELPERS[helper_id]
    if hazard_id not in setting.hazards:
        return (
            f"(No story: {HAZARDS[hazard_id].id.replace('_', ' ')} does not fit {setting.place}. "
            f"Choose a hazard the setting really supports.)"
        )
    if not has_line_of_sight(setting, helper_id):
        return (
            f"(No story: the {helper.title} at {helper.station} cannot see signals from {setting.place}, "
            f"so semaphore would not honestly work there.)"
        )
    if not helper_can_answer(helper, hazard_id):
        return (
            f"(No story: the {helper.title} is not equipped in this world to answer {hazard_id.replace('_', ' ')}, "
            f"so pick a helper whose station and methods fit the problem.)"
        )
    return "(No story: that combination is unreasonable in this world.)"


ASP_RULES = r"""
valid(S,H,Hp) :- setting(S), hazard(H), helper(Hp),
                 setting_has_hazard(S,H),
                 visible(S,Hp),
                 helper_handles(Hp,H).

cautious(T) :- trait(T), cautious_trait(T).
outcome(averted) :- lead(early), cautious(T), trait(T).
outcome(rescued) :- not outcome(averted).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for hazard_id in sorted(setting.hazards):
            lines.append(asp.fact("setting_has_hazard", setting_id, hazard_id))
        for helper_id in sorted(setting.helpers_visible):
            lines.append(asp.fact("visible", setting_id, helper_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for hazard_id in sorted(helper.methods):
            if hazard_id in helper.arrivals:
                lines.append(asp.fact("helper_handles", helper_id, hazard_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
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
        asp.fact("lead", params.lead),
        asp.fact("trait", params.friend_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        shown_meters = {k: v for k, v in ent.meters.items() if v}
        shown_memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if shown_meters:
            bits.append(f"meters={dict(shown_meters)}")
        if shown_memes:
            bits.append(f"memes={dict(shown_memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:7} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "semaphore" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing required content.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Seaside adventure storyworld: children use semaphore and bravery to solve a real problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--lead", choices=["early", "late"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.helper:
        if (args.setting, args.hazard, args.helper) not in set(valid_combos()):
            raise StoryError(explain_invalid_combo(args.setting, args.hazard, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, helper_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    hero_name, hero_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=hero_name)
    friend_trait = rng.choice(TRAITS)
    lead = args.lead or rng.choice(["early", "late"])

    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        helper=helper_id,
        goal=goal_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        lead=lead,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if (params.setting, params.hazard, params.helper) not in set(valid_combos()):
        raise StoryError(explain_invalid_combo(params.setting, params.hazard, params.helper))
    if params.lead not in {"early", "late"}:
        raise StoryError("(Lead must be 'early' or 'late'.)")

    world = tell(
        setting=SETTINGS[params.setting],
        hazard=HAZARDS[params.hazard],
        helper_cfg=HELPERS[params.helper],
        goal=GOALS[params.goal],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        lead=params.lead,
    )
    story_text = render_story(world)
    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (setting, hazard, helper) combos:\n")
        for setting_id, hazard_id, helper_id in combos:
            print(f"  {setting_id:12} {hazard_id:12} {helper_id}")
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
            header = f"### {p.hero} & {p.friend}: {p.hazard} at {p.setting} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
