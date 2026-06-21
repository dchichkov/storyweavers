#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py
=================================================================================

A standalone story world about two friends, one oversized town event, and the
kind of trouble that curiosity can start before friendship helps mend it.

This world rebuilds a tiny Tall-Tale-style premise:

- a town is getting ready for a giant balloon event
- one friend grows too curious and tests the balloon early
- the balloon snags high above the crowd
- the friends quarrel for a moment
- they reconcile and help a grown-up save the day, or else the event must wait

The simulation tracks physical meters (loose, snagged, torn, paused, saved) and
emotional memes (curiosity, fear, blame, strain, apology, cooperation,
friendship). The prose is rendered from changing state, not from a frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --festival hill_event --balloon whale --target windmill --qa
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --target well
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --response beanpole
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --asp
    python storyworlds/worlds/gpt-5.4/event_reconciliation_curiosity_friendship_tall_tale.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "mechanic", "ferryman"}
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
class Festival:
    id: str
    event_name: str
    place: str
    opener: str
    crowd: str
    wind_line: str
    available_targets: set[str] = field(default_factory=set)
    wind_bonus: int = 0
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
class Balloon:
    id: str
    label: str
    phrase: str
    animal: str
    boast: str
    lift: int
    fragility: int
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
    place_phrase: str
    height: int
    snag_line: str
    snaggy: bool = True
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
    reach: int
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
class HelperCfg:
    id: str
    type: str
    label: str
    intro: str
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
    def __init__(self, festival: Festival) -> None:
        self.festival = festival
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"reconciled": False}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"curious", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.festival)
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


def _r_snag_trouble(world: World) -> list[str]:
    balloon = world.entities.get("balloon")
    event = world.entities.get("event")
    if balloon is None or event is None:
        return []
    if balloon.meters["snagged"] < THRESHOLD:
        return []
    sig = ("snag_trouble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    balloon.meters["torn"] += 1
    event.meters["paused"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__snag__"]


def _r_blame_strain(world: World) -> list[str]:
    if not any(k.memes["blame"] >= THRESHOLD for k in world.kids()):
        return []
    sig = ("blame_strain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["strain"] += 1
    return ["__strain__"]


def _r_reconcile(world: World) -> list[str]:
    curious = world.entities.get("curious")
    friend = world.entities.get("friend")
    if curious is None or friend is None:
        return []
    if curious.memes["apology"] < THRESHOLD:
        return []
    if curious.memes["cooperation"] < THRESHOLD or friend.memes["cooperation"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    curious.memes["strain"] = 0.0
    friend.memes["strain"] = 0.0
    curious.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    curious.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.facts["reconciled"] = True
    return ["__reconciled__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="snag_trouble", tag="physical", apply=_r_snag_trouble),
    Rule(name="blame_strain", tag="social", apply=_r_blame_strain),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def snag_possible(festival: Festival, balloon: Balloon, target: Target) -> bool:
    return (
        target.snaggy
        and target.id in festival.available_targets
        and balloon.lift + festival.wind_bonus >= target.height
    )


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def trouble_severity(target: Target, gust: int) -> int:
    return target.height + gust


def event_saved(response: Response, target: Target, gust: int) -> bool:
    return response.reach >= trouble_severity(target, gust)


def predict_snag(world: World, target_id: str) -> dict:
    sim = world.copy()
    balloon = sim.get("balloon")
    target = sim.get(target_id)
    balloon.meters["loose"] += 1
    if target.attrs.get("snaggy"):
        balloon.meters["snagged"] += 1
        target.meters["holding"] += 1
    propagate(sim, narrate=False)
    return {
        "snagged": balloon.meters["snagged"] >= THRESHOLD,
        "paused": sim.get("event").meters["paused"],
        "torn": balloon.meters["torn"],
    }


def introduce_event(world: World, curious: Entity, friend: Entity, helper: Entity,
                    festival: Festival, balloon: Balloon) -> None:
    for kid in (curious, friend):
        kid.memes["friendship"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"In {festival.place}, folks said the annual {festival.event_name} was so big "
        f"it could make a scarecrow grin and a fence post stand up straighter. "
        f"{festival.opener}"
    )
    world.say(
        f"{curious.id} and {friend.id} were best friends, the sort who could share "
        f"one idea back and forth until it grew feathers. They had been trusted to "
        f"help with {balloon.phrase}, {balloon.boast}."
    )
    world.say(
        f"{helper.label} was in charge of the event rope and kept saying, "
        f'"Easy now. The town can wait one more minute if it has to."'
    )


def show_balloon(world: World, balloon: Balloon, festival: Festival) -> None:
    world.say(
        f"The {balloon.label} lay across the grass like a sleepy hill with ears, "
        f"tail, and a grin. {festival.wind_line}"
    )


def tempt_curiosity(world: World, curious: Entity, friend: Entity, target: Target) -> None:
    curious.memes["curiosity"] += 1
    world.say(
        f'{curious.id} squinted up at {target.the} and whispered, '
        f'"I just want to know what would happen if the rope were let out one tiny bit."'
    )
    world.say(
        f"{friend.id} knew that look. It was the same look {curious.id} wore before "
        f"opening mystery boxes, peeking under wagon tarps, or asking where thunder slept."
    )


def warn(world: World, friend: Entity, curious: Entity, target: Target, helper: Entity) -> None:
    pred = predict_snag(world, "target")
    world.facts["predicted_paused"] = pred["paused"]
    world.facts["predicted_torn"] = pred["torn"]
    extra = ""
    if pred["snagged"]:
        extra = f" It could snag on {target.the} before {helper.label_word} even turns around."
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "Wait for {helper.label_word}," '
        f"{friend.pronoun()} said. \"This event belongs to the whole town, not just our curiosity.\""
        f"{extra}"
    )


def test_rope(world: World, curious: Entity, balloon_ent: Entity, target_ent: Entity,
              balloon: Balloon, target: Target) -> None:
    curious.memes["defiance"] += 1
    balloon_ent.meters["loose"] += 1
    balloon_ent.meters["snagged"] += 1
    target_ent.meters["holding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity in {festival_style_phrase(curious)} was taller than a haystack that morning. "
        f"{curious.id} gave the rope one curious tug."
    )
    world.say(
        f"Up whooshed the {balloon.label}, faster than laundry on a storm line, "
        f"until {target.snag_line}. A groan ran through the cloth, and the whole "
        f"event seemed to hold its breath."
    )


def festival_style_phrase(curious: Entity) -> str:
    if curious.type == "girl":
        return "her chest"
    if curious.type == "boy":
        return "his chest"
    return "their chest"


def quarrel(world: World, curious: Entity, friend: Entity) -> None:
    curious.memes["blame"] += 1
    friend.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh, feathers and fence nails," {curious.id} gasped. '
        f'"I only meant to peek at the wind."'
    )
    world.say(
        f'{friend.id} stamped one foot. "I told you to wait!" {friend.pronoun().capitalize()} said. '
        f"For one hot little moment, the two friends felt farther apart than opposite hills."
    )


def apology(world: World, curious: Entity, friend: Entity) -> None:
    curious.memes["apology"] += 1
    world.say(
        f"Then {curious.id} looked at {friend.id} instead of at the sky. "
        f'"You were right," {curious.pronoun()} said softly. '
        f'"I let my curiosity get bigger than my good sense, and I am sorry."'
    )
    if friend.memes["strain"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s face stayed stiff for one breath, then softened. "
            f"The anger was real, but so was the friendship."
        )


def team_up(world: World, curious: Entity, friend: Entity, helper: Entity) -> None:
    curious.memes["cooperation"] += 1
    friend.memes["cooperation"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Then let\'s fix it together," {friend.id} said. {friend.pronoun().capitalize()} grabbed the spare line, '
        f"and {helper.label_word} came striding over with sleeves rolled high."
    )


def rescue(world: World, helper: Entity, response: Response, target: Target, balloon: Balloon) -> None:
    balloon_ent = world.get("balloon")
    event_ent = world.get("event")
    balloon_ent.meters["snagged"] = 0.0
    balloon_ent.meters["saved"] += 1
    event_ent.meters["paused"] = 0.0
    event_ent.meters["saved"] += 1
    body = response.text.replace("{target}", target.label).replace("{balloon}", balloon.label)
    world.say(
        f"{helper.label} {body}."
    )


def rescue_fail(world: World, helper: Entity, response: Response, target: Target, balloon: Balloon) -> None:
    balloon_ent = world.get("balloon")
    event_ent = world.get("event")
    balloon_ent.meters["snagged"] += 1
    balloon_ent.meters["torn"] += 1
    event_ent.meters["paused"] += 1
    body = response.fail.replace("{target}", target.label).replace("{balloon}", balloon.label)
    world.say(
        f"{helper.label} {body}."
    )


def saved_ending(world: World, curious: Entity, friend: Entity, festival: Festival,
                 balloon: Balloon, helper: Entity) -> None:
    for kid in (curious, friend):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"Soon the patched {balloon.label} was floating proper again, bobbing above "
        f"{festival.crowd} as if nothing in the world had ever dared to bother it."
    )
    world.say(
        f"{helper.label} gave both children a look that was stern around the edges and warm in the middle. "
        f'"Curiosity is a fine horse," {helper.pronoun()} said, '
        f'"but friendship has to hold the reins."'
    )
    world.say(
        f"When the music struck up, {curious.id} and {friend.id} marched side by side under the balloon. "
        f"By the end of the event, they were grinning so wide it looked as though the whole town had lent them extra cheeks."
    )


def postponed_ending(world: World, curious: Entity, friend: Entity, festival: Festival,
                     balloon: Balloon, helper: Entity) -> None:
    for kid in (curious, friend):
        kid.memes["sadness"] += 1
        kid.memes["hope"] += 1
    world.say(
        f"The grown-ups lowered what they could, but the poor {balloon.label} was too torn and too high for a quick rescue. "
        f"So the town rang the bell for a delayed event instead of a grand start."
    )
    world.say(
        f"Nobody shouted. {helper.label} just laid a steady hand on the rope and said, "
        f'"We can mend cloth by sunset. What matters most is mending hearts before then."'
    )
    world.say(
        f"So {curious.id} and {friend.id} sat together on an overturned crate, knotting patch line and making up properly. "
        f"When evening painted the sky peach and gold, they promised the next event would begin with both curiosity and patience walking together."
    )


def tell(festival: Festival, balloon: Balloon, target: Target, response: Response,
         helper_cfg: HelperCfg, curious_name: str = "Mara", curious_gender: str = "girl",
         friend_name: str = "Beau", friend_gender: str = "boy", trait: str = "loyal",
         gust: int = 0) -> World:
    world = World(festival)
    curious = world.add(Entity(
        id=curious_name,
        kind="character",
        type=curious_gender,
        role="curious",
        traits=["bold", "curious"],
        attrs={"trait": "curious"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[trait],
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        attrs={"kind": helper_cfg.id},
    ))
    event_ent = world.add(Entity(
        id="event",
        type="event",
        label=festival.event_name,
    ))
    balloon_ent = world.add(Entity(
        id="balloon",
        type="balloon",
        label=balloon.label,
        attrs={"fragility": balloon.fragility},
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        attrs={"height": target.height, "snaggy": target.snaggy},
    ))

    world.facts.update(
        festival=festival,
        balloon_cfg=balloon,
        target_cfg=target,
        response=response,
        helper_cfg=helper_cfg,
        curious=curious,
        friend=friend,
        helper=helper,
        gust=gust,
    )

    introduce_event(world, curious, friend, helper, festival, balloon)
    show_balloon(world, balloon, festival)

    world.para()
    tempt_curiosity(world, curious, friend, target)
    warn(world, friend, curious, target, helper)
    test_rope(world, curious, balloon_ent, target_ent, balloon, target)
    quarrel(world, curious, friend)

    world.para()
    apology(world, curious, friend)
    team_up(world, curious, friend, helper)

    saved = event_saved(response, target, gust)
    severity = trouble_severity(target, gust)
    world.facts["severity"] = severity
    world.facts["outcome"] = "saved" if saved else "postponed"

    if saved:
        rescue(world, helper, response, target, balloon)
        world.para()
        saved_ending(world, curious, friend, festival, balloon, helper)
    else:
        rescue_fail(world, helper, response, target, balloon)
        world.para()
        postponed_ending(world, curious, friend, festival, balloon, helper)

    world.facts.update(
        event_ent=event_ent,
        balloon_ent=balloon_ent,
        target_ent=target_ent,
        friendship_restored=world.facts.get("reconciled", False),
        balloon_saved=balloon_ent.meters["saved"] >= THRESHOLD,
        event_paused=event_ent.meters["paused"] >= THRESHOLD,
    )
    return world


FESTIVALS = {
    "river_event": Festival(
        id="river_event",
        event_name="River Sky Event",
        place="a river town with docks longer than bedtime stories",
        opener="By noon the pies were cooling on windowsills and the fiddles were tuning themselves, or so people claimed.",
        crowd="a crowd packed from dock rail to bakery door",
        wind_line="The breeze came off the water in long silver breaths.",
        available_targets={"bridge", "water_tower", "well"},
        wind_bonus=1,
        tags={"event", "river", "balloon"},
    ),
    "hill_event": Festival(
        id="hill_event",
        event_name="High Hill Event",
        place="a hill town where even the chickens seemed to walk uphill on purpose",
        opener="Folks had polished their boots, brushed their hats, and set out benches as if expecting the moon itself to stop by.",
        crowd="the whole town shoulder to shoulder along the hill road",
        wind_line="The hill wind was lively enough to turn a whisper into a kite.",
        available_targets={"windmill", "steeple", "well"},
        wind_bonus=1,
        tags={"event", "hill", "balloon"},
    ),
    "prairie_event": Festival(
        id="prairie_event",
        event_name="Prairie Wind Event",
        place="a prairie town flat as a pancake except for the brave things sticking up out of it",
        opener="The bandstand was bunting-bright, and every porch had somebody leaning on the rail to watch.",
        crowd="neighbors lined up clear to the grain store",
        wind_line="Across the open grass, the wind came running with both shoelaces untied.",
        available_targets={"clock_tower", "water_tower", "well"},
        wind_bonus=0,
        tags={"event", "prairie", "balloon"},
    ),
}

BALLOONS = {
    "cat": Balloon(
        id="cat",
        label="cat balloon",
        phrase="a cat balloon with whiskers as long as fishing poles",
        animal="cat",
        boast="it was big enough to cast shade over a watermelon patch",
        lift=2,
        fragility=1,
        tags={"balloon", "cat"},
    ),
    "rooster": Balloon(
        id="rooster",
        label="rooster balloon",
        phrase="a rooster balloon with a tail like five bright flags",
        animal="rooster",
        boast="it looked ready to crow the sun right out of bed",
        lift=3,
        fragility=1,
        tags={"balloon", "rooster"},
    ),
    "whale": Balloon(
        id="whale",
        label="whale balloon",
        phrase="a whale balloon with a smile broad as a ferry dock",
        animal="whale",
        boast="it was so large that three children could have played tag in its shadow and still had room to spare",
        lift=5,
        fragility=2,
        tags={"balloon", "whale"},
    ),
}

TARGETS = {
    "bridge": Target(
        id="bridge",
        label="bridge arch",
        the="the bridge arch",
        place_phrase="over the old bridge",
        height=2,
        snag_line="its ribbon-tail hooked over the bridge arch",
        snaggy=True,
        tags={"bridge", "high_place"},
    ),
    "windmill": Target(
        id="windmill",
        label="windmill arm",
        the="the windmill arm",
        place_phrase="by the windmill",
        height=3,
        snag_line="one flapping fin caught on the windmill arm",
        snaggy=True,
        tags={"windmill", "high_place"},
    ),
    "clock_tower": Target(
        id="clock_tower",
        label="clock tower weathercock",
        the="the clock tower weathercock",
        place_phrase="by the clock tower",
        height=4,
        snag_line="its side snagged beneath the clock tower weathercock",
        snaggy=True,
        tags={"clocktower", "high_place"},
    ),
    "water_tower": Target(
        id="water_tower",
        label="water-tower ladder",
        the="the water-tower ladder",
        place_phrase="near the water tower",
        height=5,
        snag_line="a seam kissed the water-tower ladder and stuck there fast",
        snaggy=True,
        tags={"water_tower", "high_place"},
    ),
    "well": Target(
        id="well",
        label="stone well",
        the="the stone well",
        place_phrase="beside the old well",
        height=1,
        snag_line="nothing at all happened",
        snaggy=False,
        tags={"well"},
    ),
}

RESPONSES = {
    "ladder": Response(
        id="ladder",
        sense=2,
        reach=3,
        text="planted the longest ladder in town, climbed up steady as a cat on a fence, and eased the {balloon} free from the {target}",
        fail="raised the longest ladder in town, but the {balloon} was still too high and too wild above the {target}",
        qa_text="used the town's long ladder to climb up and ease the balloon free",
        tags={"ladder", "repair"},
    ),
    "hay_wagon": Response(
        id="hay_wagon",
        sense=2,
        reach=4,
        text="backed the hay wagon under the trouble, climbed its stacked bales, and with the children's spare line tugged the {balloon} down from the {target}",
        fail="backed the hay wagon under the trouble, but even standing on the bales was not high enough to reach the {balloon}",
        qa_text="used the hay wagon and spare line to pull the balloon down",
        tags={"wagon", "repair"},
    ),
    "crane": Response(
        id="crane",
        sense=3,
        reach=6,
        text="rolled out the grain-yard crane, hooked the safety loop just right, and brought the {balloon} down from the {target} as gently as lowering a sleeping baby",
        fail="rolled out the grain-yard crane, but the gusts kept swinging the {balloon} too hard to free quickly",
        qa_text="used the grain-yard crane to bring the balloon down gently",
        tags={"crane", "repair"},
    ),
    "beanpole": Response(
        id="beanpole",
        sense=1,
        reach=1,
        text="waved an extra-long beanpole at the {balloon} until by pure luck it slipped free",
        fail="poked upward with an extra-long beanpole, but it never came close to the {balloon}",
        qa_text="tried to use a beanpole",
        tags={"beanpole"},
    ),
}

HELPERS = {
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        label="Aunt Tilly",
        intro="Aunt Tilly could tie a knot in wind itself, people said.",
        tags={"adult", "helper"},
    ),
    "mechanic": HelperCfg(
        id="mechanic",
        type="mechanic",
        label="Mr. Vale the mechanic",
        intro="Mr. Vale knew ropes, pulleys, gears, and every squeak a machine could make.",
        tags={"adult", "helper"},
    ),
    "ferryman": HelperCfg(
        id="ferryman",
        type="ferryman",
        label="Old Ferryman Jo",
        intro="Old Ferryman Jo had hands like oak roots and eyes that missed nothing on land or water.",
        tags={"adult", "helper"},
    ),
}

GIRL_NAMES = ["Mara", "June", "Tess", "Nell", "Ruby", "Ada", "Fern", "Clara"]
BOY_NAMES = ["Beau", "Eli", "Wade", "Finn", "Otis", "Jude", "Theo", "Cal"]
TRAITS = ["loyal", "steady", "patient", "kind", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for festival_id, festival in FESTIVALS.items():
        for balloon_id, balloon in BALLOONS.items():
            for target_id, target in TARGETS.items():
                if snag_possible(festival, balloon, target):
                    combos.append((festival_id, balloon_id, target_id))
    return combos


@dataclass
class StoryParams:
    festival: str
    balloon: str
    target: str
    response: str
    helper: str
    curious_name: str
    curious_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    gust: int = 0
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
    "event": [(
        "What is an event?",
        "An event is something special that people plan and gather for, like a fair, parade, or concert. It usually happens at a certain time and place."
    )],
    "balloon": [(
        "How does a big parade balloon stay up?",
        "A big parade balloon stays up because it is filled with a lifting gas and held by ropes. The ropes help people guide it so the wind does not carry it away."
    )],
    "windmill": [(
        "What is a windmill?",
        "A windmill is a tall machine with arms or sails that turn in the wind. Because it sticks up high, things can get caught on it."
    )],
    "clocktower": [(
        "Why is a clock tower hard to reach?",
        "A clock tower is built high above the street so people can see the clock from far away. That height makes it hard to reach without special equipment."
    )],
    "water_tower": [(
        "What is a water tower?",
        "A water tower is a tall structure that holds water high above a town. Its height helps water move through pipes, but it also makes the tower hard to reach."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps people climb up to places that are above their heads. Grown-ups use ladders carefully to reach high spots."
    )],
    "wagon": [(
        "What is a hay wagon?",
        "A hay wagon is a wagon used for carrying hay or stacked bales. In a pinch, it can also help people stand a little higher."
    )],
    "crane": [(
        "What does a crane do?",
        "A crane is a machine for lifting heavy things up and down. People use it when something is too big or too high to move by hand."
    )],
    "repair": [(
        "Why do torn things need patching?",
        "Torn things need patching because the weak spot can rip wider if nobody fixes it. A patch helps make the material strong again."
    )],
    "friendship": [(
        "What does friendship mean?",
        "Friendship means caring about someone, helping them, and staying honest with them. Good friends can be upset and still choose to make things right."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the feeling that makes you want to know or learn something. It can help you discover new things, but it also needs patience and care."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace after a disagreement. It usually begins when someone tells the truth, apologizes, and both people work to mend the hurt."
    )],
}
KNOWLEDGE_ORDER = [
    "event", "balloon", "windmill", "clocktower", "water_tower",
    "ladder", "wagon", "crane", "repair", "curiosity", "friendship",
    "reconciliation",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    festival = f["festival"]
    curious = f["curious"]
    friend = f["friend"]
    balloon = f["balloon_cfg"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a Tall Tale story for a 3-to-5-year-old that includes the word "event" and shows curiosity causing trouble before friendship helps fix it.',
            f"Tell a tall, child-friendly story where best friends {curious.id} and {friend.id} help with a giant {balloon.animal} balloon for the {festival.event_name}, quarrel after a curious mistake, and reconcile in time to save the event.",
            f"Write a story with oversized town details, a moment of apology, and a happy ending where the event can still go on."
        ]
    return [
        f'Write a Tall Tale story for a 3-to-5-year-old that includes the word "event" and shows curiosity causing trouble before friendship is mended.',
        f"Tell a tall, child-friendly story where best friends {curious.id} and {friend.id} help with a giant {balloon.animal} balloon for the {festival.event_name}, quarrel after a curious mistake, and reconcile even though the event must be delayed.",
        f"Write a story with oversized town details, a true apology, and an ending image that shows friendship repaired even after a sad turn."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    curious = f["curious"]
    friend = f["friend"]
    helper = f["helper"]
    festival = f["festival"]
    balloon = f["balloon_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two best friends, {curious.id} and {friend.id}, helping with the {festival.event_name}. It is also about {helper.label_word}, the grown-up guiding the giant balloon."
        ),
        (
            f"What were they getting ready for?",
            f"They were getting ready for the {festival.event_name}, a big town event with a giant {balloon.animal} balloon. The whole town was waiting to see it rise."
        ),
        (
            f"Why did the trouble start?",
            f"The trouble started because {curious.id} got too curious and tugged the rope before it was time. That let the balloon fly up and snag on {target.the}."
        ),
        (
            f"Why were {curious.id} and {friend.id} upset with each other?",
            f"They were upset because {friend.id} had warned {curious.id} to wait, but the warning was ignored. When the balloon got stuck, both children felt scared and the friendship suddenly felt strained."
        ),
        (
            f"How did they reconcile?",
            f"{curious.id} stopped blaming the wind and told the truth, then apologized. {friend.id} chose to help fix the mess, so their friendship became more important than the quarrel."
        ),
    ]
    if outcome == "saved":
        body = response.qa_text.replace("{target}", target.label).replace("{balloon}", balloon.label)
        qa.append((
            f"How was the balloon saved?",
            f"{helper.label_word} {body}. Because the two friends worked together instead of arguing, the rescue happened in time for the event to continue."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the balloon back in the sky and the friends marching side by side under it. That ending proves both the event and the friendship were saved."
        ))
    else:
        qa.append((
            f"Why was the event delayed?",
            f"The balloon was too high or too torn for that rescue method to free quickly. Even so, the children had already reconciled, so the ending was sad about the event but hopeful about the friendship."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two friends sitting together and helping mend the balloon for later. The event had to wait, but their friendship did not stay broken."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"event", "balloon", "curiosity", "friendship", "reconciliation"}
    tags |= set(f["target_cfg"].tags)
    tags |= set(f["response"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="hill_event",
        balloon="rooster",
        target="windmill",
        response="ladder",
        helper="aunt",
        curious_name="June",
        curious_gender="girl",
        friend_name="Beau",
        friend_gender="boy",
        trait="loyal",
        gust=0,
    ),
    StoryParams(
        festival="river_event",
        balloon="whale",
        target="water_tower",
        response="crane",
        helper="mechanic",
        curious_name="Mara",
        curious_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        trait="steady",
        gust=1,
    ),
    StoryParams(
        festival="prairie_event",
        balloon="rooster",
        target="clock_tower",
        response="hay_wagon",
        helper="ferryman",
        curious_name="Eli",
        curious_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        trait="patient",
        gust=1,
    ),
    StoryParams(
        festival="hill_event",
        balloon="whale",
        target="steeple",
        response="ladder",
        helper="aunt",
        curious_name="Fern",
        curious_gender="girl",
        friend_name="Otis",
        friend_gender="boy",
        trait="kind",
        gust=2,
    ),
]

# Insert steeple after CURATED references are defined? No: registry must exist before use.
# This target is appended here to keep the curated examples readable while preserving one file.
TARGETS["steeple"] = Target(
    id="steeple",
    label="church steeple rooster",
    the="the church steeple rooster",
    place_phrase="beside the church",
    height=4,
    snag_line="one bright panel wrapped around the church steeple rooster",
    snaggy=True,
    tags={"steeple", "high_place"},
)
FESTIVALS["hill_event"].available_targets.add("steeple")


def explain_rejection(festival: Festival, balloon: Balloon, target: Target) -> str:
    if not target.snaggy:
        return (
            f"(No story: {target.the} is not a snagging place for a balloon, so the "
            f"curious mistake would not create real trouble for the event. Pick a "
            f"higher catching place like a windmill or tower.)"
        )
    if target.id not in festival.available_targets:
        return (
            f"(No story: {target.the} does not belong in {festival.event_name}. "
            f"Choose a target that fits that town's skyline.)"
        )
    if balloon.lift + festival.wind_bonus < target.height:
        return (
            f"(No story: the {balloon.label} would not rise high enough at the "
            f"{festival.event_name} to snag on {target.the}. Pick a lower target "
            f"or a bigger balloon.)"
        )
    return "(No story: this combination does not make a reasonable balloon mishap.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a more believable rescue "
        f"method such as: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.response not in RESPONSES or params.target not in TARGETS:
        return "?"
    return "saved" if event_saved(RESPONSES[params.response], TARGETS[params.target], params.gust) else "postponed"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(F, B, T) :- festival(F), balloon(B), target(T),
                   available(F, T), snaggy(T),
                   lift(B, L), wind_bonus(F, W), height(T, H), L + W >= H.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(F, B, T) :- hazard(F, B, T).

% --- outcome model ---------------------------------------------------------
severity(H + G) :- chosen_target(T), height(T, H), gust(G).
saved :- chosen_response(R), reach(R, P), severity(S), P >= S.
outcome(saved) :- saved.
outcome(postponed) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for festival_id, festival in FESTIVALS.items():
        lines.append(asp.fact("festival", festival_id))
        lines.append(asp.fact("wind_bonus", festival_id, festival.wind_bonus))
        for target_id in sorted(festival.available_targets):
            lines.append(asp.fact("available", festival_id, target_id))
    for balloon_id, balloon in BALLOONS.items():
        lines.append(asp.fact("balloon", balloon_id))
        lines.append(asp.fact("lift", balloon_id, balloon.lift))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("height", target_id, target.height))
        if target.snaggy:
            lines.append(asp.fact("snaggy", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("reach", response_id, response.reach))
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
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("gust", params.gust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant balloon event, curiosity, reconciliation, and friendship."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--balloon", choices=BALLOONS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gust", type=int, choices=[0, 1, 2], help="extra wind trouble; higher makes rescue harder")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.festival and args.balloon and args.target:
        festival = FESTIVALS[args.festival]
        balloon = BALLOONS[args.balloon]
        target = TARGETS[args.target]
        if not snag_possible(festival, balloon, target):
            raise StoryError(explain_rejection(festival, balloon, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.balloon is None or combo[1] == args.balloon)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, balloon_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    curious_name, curious_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=curious_name)
    trait = rng.choice(TRAITS)
    gust = args.gust if args.gust is not None else rng.randint(0, 2)

    return StoryParams(
        festival=festival_id,
        balloon=balloon_id,
        target=target_id,
        response=response_id,
        helper=helper_id,
        curious_name=curious_name,
        curious_gender=curious_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
        gust=gust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival '{params.festival}')")
    if params.balloon not in BALLOONS:
        raise StoryError(f"(Unknown balloon '{params.balloon}')")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target '{params.target}')")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}')")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}')")

    festival = FESTIVALS[params.festival]
    balloon = BALLOONS[params.balloon]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]
    helper_cfg = HELPERS[params.helper]

    if not snag_possible(festival, balloon, target):
        raise StoryError(explain_rejection(festival, balloon, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        festival=festival,
        balloon=balloon,
        target=target,
        response=response,
        helper_cfg=helper_cfg,
        curious_name=params.curious_name,
        curious_gender=params.curious_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
        gust=params.gust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, balloon, target) combos:\n")
        for festival_id, balloon_id, target_id in combos:
            print(f"  {festival_id:13} {balloon_id:8} {target_id}")
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
            header = (
                f"### {p.curious_name} & {p.friend_name}: {p.balloon} at {p.festival} "
                f"near {p.target} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
