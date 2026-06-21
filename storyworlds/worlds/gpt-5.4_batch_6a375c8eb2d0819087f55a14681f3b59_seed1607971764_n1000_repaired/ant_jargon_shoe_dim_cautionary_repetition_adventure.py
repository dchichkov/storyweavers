#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ant_jargon_shoe_dim_cautionary_repetition_adventure.py
==================================================================================

A standalone story world about a tiny backyard expedition: two children follow an
ant trail like brave explorers, one child is tempted to disturb the ants at a
shoe-dim hiding place, a warning is given, and the family learns a repeated
rule for safe watching: "Watch, don't poke."

The seed asked for:
- the words "ant", "jargon", and "shoe-dim"
- cautionary repetition
- an adventure style

This world turns that into a small simulation with:
- typed entities carrying physical meters and emotional memes
- a reasonableness gate for valid settings/hideouts and sensible responses
- a Python model plus an inline ASP twin
- state-driven prose with a clear beginning, turn, and ending image
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "steady", "sensible"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    has_ants: bool = False
    safe_tool: bool = False
    soothing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Param registries
# ---------------------------------------------------------------------------
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
    afford_hides: set[str] = field(default_factory=set)
    detail: str = ""
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


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    opening: str
    defend: int
    has_ants: bool = True
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
class RiskAction:
    id: str
    phrase: str
    rush: str
    disturb: int
    touch_word: str
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
class SafeTool:
    id: str
    phrase: str
    use_text: str
    glow_text: str
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


@dataclass
class StoryParams:
    setting: str
    hideout: str
    risk: str
    tool1: str
    tool2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    notebook: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_swarm(world: World) -> list[str]:
    out: list[str] = []
    ants = world.get("ants")
    if ants.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("swarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ants.meters["swarming"] += 1
    world.get("place").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__swarm__")
    return out


def _r_bites(world: World) -> list[str]:
    out: list[str] = []
    ants = world.get("ants")
    instigator = world.get("instigator")
    if ants.meters["swarming"] < THRESHOLD:
        return out
    if instigator.meters["too_close"] < THRESHOLD:
        return out
    sig = ("bites",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    instigator.meters["bites"] += 1
    instigator.memes["fear"] += 1
    out.append("__bites__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="swarm", tag="physical", apply=_r_swarm),
    Rule(name="bites", tag="physical", apply=_r_bites),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def hideout_has_ants(setting: Setting, hideout: Hideout) -> bool:
    return hideout.id in setting.afford_hides and hideout.has_ants


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: (r.sense, r.power))


def disturbance_severity(hideout: Hideout, risk: RiskAction, delay: int) -> int:
    return hideout.defend + risk.disturb + delay


def is_soothed(response: Response, hideout: Hideout, risk: RiskAction, delay: int) -> bool:
    return response.power >= disturbance_severity(hideout, risk, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def explain_rejection(setting: Setting, hideout: Hideout) -> str:
    if hideout.id not in setting.afford_hides:
        return (
            f"(No story: {hideout.phrase} is not a plausible ant hiding place at "
            f"{setting.place}. Pick a hiding place that fits the setting.)"
        )
    return (
        f"(No story: {hideout.phrase} does not hold an ant trail here, so there is "
        f"no honest adventure to follow and no cautionary turn.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer, more helpful response: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for hid, hideout in HIDEOUTS.items():
            if not hideout_has_ants(setting, hideout):
                continue
            for rid in RISKS:
                combos.append((sid, hid, rid))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def _do_risk(world: World, risk: RiskAction, narrate: bool = True) -> None:
    ants = world.get("ants")
    instigator = world.get("instigator")
    ants.meters["disturbed"] += 1
    ants.meters["severity"] = float(world.facts["severity"])
    instigator.meters["too_close"] += 1
    propagate(world, narrate=narrate)


def predict_trouble(world: World, risk: RiskAction, hideout: Hideout) -> dict:
    sim = world.copy()
    sim.facts["severity"] = disturbance_severity(hideout, risk, sim.facts.get("delay", 0))
    _do_risk(sim, risk, narrate=False)
    return {
        "swarm": sim.get("ants").meters["swarming"] >= THRESHOLD,
        "bites": sim.get("instigator").meters["bites"] >= THRESHOLD,
        "danger": sim.get("place").meters["danger"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"On a bright afternoon at {setting.place}, {a.id} and {b.id} set off on a tiny adventure. "
        f"{setting.detail}"
    )
    world.say(
        f"They had even made up explorer jargon for the game, so a crumb was called a gold dot "
        f"and a bug trail was called a marching road."
    )


def find_trail(world: World, a: Entity, b: Entity, hideout: Hideout) -> None:
    ants = world.get("ants")
    ants.meters["marching"] += 1
    world.say(
        f"Soon they found an ant line carrying pale crumbs through the grass. "
        f"The little march led straight to {hideout.phrase}."
    )
    world.say(
        f'"Marching road! Marching road!" {a.id} whispered. '
        f'{b.id} knelt beside {a.pronoun("object")} and watched the tiny feet hurry in and out of {hideout.opening}.'
    )


def wonder_need(world: World, a: Entity, b: Entity, hideout: Hideout) -> None:
    world.say(
        f"But the ants kept disappearing into {hideout.opening}, and that place looked dark and secret, "
        f"almost like a cave made for creatures smaller than pebbles."
    )
    world.say(
        f'{a.id} leaned closer. "I want to know what is inside that shoe-dim place," {a.pronoun()} said.'
    )


def tempt(world: World, a: Entity, risk: RiskAction) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} puffed up with brave feelings. "I know," {a.pronoun()} said. '
        f'"I can {risk.phrase}, and the ant guards will come out."'
    )
    world.say('"Watch, don\'t poke," murmured the breeze through the grass, but the exciting idea still sounded clever.')


def warn(world: World, b: Entity, a: Entity, risk: RiskAction, hideout: Hideout, parent: Entity) -> None:
    pred = predict_trouble(world, risk, hideout)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_bites"] = pred["bites"]
    extra = ""
    if pred["bites"]:
        extra = " If you bother them, they may race out and bite to protect their home."
    world.say(
        f'{b.id} touched {a.pronoun("possessive")} sleeve. "No," {b.pronoun()} said. '
        f'"We can be explorers without touching. {parent.label_word.capitalize()} says small creatures need calm eyes, not poking hands.{extra}"'
    )
    world.say(f'"Watch, don\'t poke," {b.id} said again, slower this time.')


def defy(world: World, a: Entity, b: Entity, risk: RiskAction) -> None:
    a.memes["defiance"] += 1
    older_instigator = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_instigator:
        world.say(
            f'"Just one quick try," {a.id} said. Because {a.pronoun()} was the older sibling, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Just one quick try," {a.id} said, and reached forward anyway.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    rel = "big brother" if b.type == "boy" else "big sister"
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} hand, then looked at {b.id}. '
        f'Because {b.id} was {a.pronoun("possessive")} {rel}, the warning landed hard.'
    )
    world.say(
        f'"Watch, don\'t poke," {a.id} repeated back at last. {a.pronoun().capitalize()} stepped away from the hole '
        f'and went to tell {parent.label_word} about the secret ant road instead.'
    )


def disturb(world: World, a: Entity, risk: RiskAction, hideout: Hideout) -> None:
    _do_risk(world, risk, narrate=False)
    ants = world.get("ants")
    instigator = world.get("instigator")
    world.say(
        f"{a.id} {risk.rush}. At once the neat ant line broke apart, and black specks rushed from {hideout.opening} "
        f"like a tiny army defending a fort."
    )
    if ants.meters["swarming"] >= THRESHOLD:
        world.say('"Watch, don\'t poke! Watch, don\'t poke!" cried the children together, but now the lesson had arrived too late.')
    if instigator.meters["bites"] >= THRESHOLD:
        world.say(
            f"One brave ant climbed onto {a.id}'s {risk.touch_word}, and then another did too. "
            f"{a.id} yelped and jumped back."
        )


def alarm(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} shouted. "{a.id} bothered the ant home!"')


def soothe_success(world: World, parent: Entity, response: Response, a: Entity) -> None:
    ants = world.get("ants")
    ants.meters["swarming"] = 0.0
    world.get("place").meters["danger"] = 0.0
    a.meters["bites"] = 0.0
    a.memes["fear"] = 0.0
    body = response.text
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {body}. Soon the ants were back on the ground and "
        f"{a.id} was safe beside {parent.pronoun('object')}."
    )


def soothe_fail(world: World, parent: Entity, response: Response, a: Entity) -> None:
    body = response.fail
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {body}. The ants scattered off at last, "
        f"but {a.id}'s hand still stung and the little expedition was over for the day."
    )
    a.memes["sadness"] += 1
    a.memes["fear"] += 1


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt in the grass and held both children close. "
        f'"Ant homes may be tiny, but they still need kindness," {parent.pronoun()} said.'
    )
    world.say(
        '"Watch, don\'t poke. Watch, don\'t poke," the children repeated with '
        "small, serious voices."
    )


def safe_return(world: World, parent: Entity, a: Entity, b: Entity, tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
        kid.memes["safety"] += 1
    note = world.facts.get("notebook")
    world.say(
        f"The next day, {parent.label_word} brought {tool1.phrase} and {tool2.phrase}. "
        f'"If you want an adventure," {parent.pronoun()} smiled, "let your eyes do the exploring."'
    )
    world.say(
        f"{a.id} used {tool1.use_text}, and {b.id} used {tool2.use_text}. "
        f"From a safe little distance, the ant road looked busy and brave again."
    )
    if note:
        world.say(f"They wrote their best explorer notes in {note}.")
    world.say(
        f'Soon the children were whispering their old trail jargon again, but now the strongest words were, '
        f'"Watch, don\'t poke." The tiny adventure ended with both children smiling at the marching ants instead of bothering them.'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    hideout: Hideout,
    risk: RiskAction,
    tools: tuple[SafeTool, SafeTool],
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    notebook: str = "",
) -> World:
    world = World(setting)
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="place", type="place", label=setting.place))
    world.add(
        Entity(
            id="ants",
            type="ants",
            label="the ants",
            has_ants=True,
            attrs={"hideout": hideout.id},
        )
    )
    world.add(Entity(id="hideout", type="hideout", label=hideout.label, has_ants=hideout.has_ants))
    t1, t2 = tools
    world.add(Entity(id="tool1", type="tool", label=t1.phrase, safe_tool=True))
    world.add(Entity(id="tool2", type="tool", label=t2.phrase, safe_tool=True))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.facts["delay"] = delay
    world.facts["severity"] = disturbance_severity(hideout, risk, delay)
    world.facts["notebook"] = notebook

    play_setup(world, a, b, setting)
    find_trail(world, a, b, hideout)
    wonder_need(world, a, b, hideout)

    world.para()
    tempt(world, a, risk)
    warn(world, b, a, risk, hideout, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        safe_return(world, parent, a, b, t1, t2)
        outcome = "averted"
        soothed = True
    else:
        defy(world, a, b, risk)
        world.para()
        disturb(world, a, risk, hideout)
        alarm(world, a, b, parent)
        soothed = is_soothed(response, hideout, risk, delay)

        world.para()
        if soothed:
            soothe_success(world, parent, response, a)
            lesson(world, parent, a, b)
        else:
            soothe_fail(world, parent, response, a)
            lesson(world, parent, a, b)

        world.para()
        safe_return(world, parent, a, b, t1, t2)
        outcome = "soothed" if soothed else "tears"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        setting=setting,
        hideout_cfg=hideout,
        risk_cfg=risk,
        tools=(t1, t2),
        response=response,
        outcome=outcome,
        disturbed=world.get("ants").meters["disturbed"] >= THRESHOLD,
        bites=world.get("instigator").meters["bites"] >= THRESHOLD or outcome == "tears",
        severity=world.facts["severity"],
        soothed=soothed,
        relation=relation,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        afford_hides={"step_crack", "flower_pot", "log_hollow"},
        detail="A flat stone path crossed the dirt, and the tall grass around the fence looked like jungle walls.",
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        afford_hides={"flower_pot", "step_crack"},
        detail="Mint leaves nodded in the wind, and every path between the flowers felt like a secret road.",
    ),
    "park": Setting(
        id="park",
        place="the park",
        afford_hides={"log_hollow", "flower_pot"},
        detail="The bench legs were like towers and the roots near the path curled up like dragon backs.",
    ),
}

HIDEOUTS = {
    "step_crack": Hideout(
        id="step_crack",
        label="step crack",
        phrase="a shoe-dim crack under the back step",
        opening="the shoe-dim crack under the step",
        defend=2,
        has_ants=True,
        tags={"ant", "home"},
    ),
    "flower_pot": Hideout(
        id="flower_pot",
        label="flower pot gap",
        phrase="a shoe-dim gap under a tipped flower pot",
        opening="the shoe-dim gap under the pot",
        defend=1,
        has_ants=True,
        tags={"ant", "garden"},
    ),
    "log_hollow": Hideout(
        id="log_hollow",
        label="log hollow",
        phrase="a shoe-dim hollow in a soft old log",
        opening="the shoe-dim hollow in the log",
        defend=2,
        has_ants=True,
        tags={"ant", "log"},
    ),
    "birdbath": Hideout(
        id="birdbath",
        label="birdbath rim",
        phrase="the rim of a birdbath",
        opening="the shiny birdbath rim",
        defend=0,
        has_ants=False,
        tags={"water"},
    ),
}

RISKS = {
    "finger": RiskAction(
        id="finger",
        phrase="poke one finger into the opening",
        rush="poked one finger toward the hole",
        disturb=2,
        touch_word="finger",
        tags={"touch", "bite"},
    ),
    "stick": RiskAction(
        id="stick",
        phrase="jab a twig inside",
        rush="jabbed a twig inside",
        disturb=1,
        touch_word="wrist",
        tags={"touch", "twig"},
    ),
    "splash": RiskAction(
        id="splash",
        phrase="pour a splash of water at the entrance",
        rush="splashed water at the entrance",
        disturb=3,
        touch_word="hand",
        tags={"water", "bite"},
    ),
}

SAFE_TOOLS = {
    "magnifier": SafeTool(
        id="magnifier",
        phrase="a magnifying glass",
        use_text="the magnifying glass to see the ants' shiny backs",
        glow_text="made the tiny trail look big and clear",
        tags={"magnifier"},
    ),
    "picture_card": SafeTool(
        id="picture_card",
        phrase="a little picture card for drawing bug maps",
        use_text="the picture card to mark where the ant road turned",
        glow_text="gave the expedition a tidy map",
        tags={"map"},
    ),
    "kneeling_pad": SafeTool(
        id="kneeling_pad",
        phrase="a soft kneeling pad",
        use_text="the kneeling pad to stay still and low in the grass",
        glow_text="helped the watching feel calm and patient",
        tags={"kneeling"},
    ),
    "tiny_binoculars": SafeTool(
        id="tiny_binoculars",
        phrase="tiny toy binoculars",
        use_text="the tiny binoculars to pretend the ant road was a faraway canyon",
        glow_text="made the game feel brave without any touching",
        tags={"viewing"},
    ),
}

RESPONSES = {
    "brush_and_cool": Response(
        id="brush_and_cool",
        sense=3,
        power=4,
        text="brushed the ants away with a leaf, washed the sting with cool water, and moved everyone back from the hole",
        fail="tried to brush the ants away with a leaf, but too many had already scattered up the sleeve",
        qa_text="brushed the ants away, used cool water, and moved the children back",
        tags={"cool_water", "ants"},
    ),
    "shake_and_step": Response(
        id="shake_and_step",
        sense=2,
        power=3,
        text="helped the children shake the ants off, then led them three big steps away from the nest",
        fail="helped the children shake the ants off, but the stinging lasted longer than anyone liked",
        qa_text="helped shake the ants off and moved everyone away",
        tags={"distance", "ants"},
    ),
    "blow": Response(
        id="blow",
        sense=1,
        power=1,
        text="blew at the ants until they dropped away",
        fail="blew at the ants, which only made the children more upset",
        qa_text="blew at the ants",
        tags={"blowing"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "patient", "steady", "curious", "sensible", "thoughtful"]
NOTEBOOKS = ["a bug notebook", "a green explorer notebook", "a tiny field notebook"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ant": [
        (
            "What does an ant do in a trail?",
            "An ant trail is a little path ants follow to food and back home. Each ant helps the group by carrying or sharing where to go.",
        )
    ],
    "home": [
        (
            "Why should you not poke an ant home?",
            "Ants use their home to protect their eggs, food, and each other. If something pokes in, they may rush out because they think they are in danger.",
        )
    ],
    "bite": [
        (
            "Why might ants bite when they are bothered?",
            "Ants can bite or pinch to defend themselves and their home. They are tiny, but they still try to protect what belongs to them.",
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes small things look bigger, so you can study them without touching them. It helps careful watching.",
        )
    ],
    "map": [
        (
            "Why is drawing a bug map a safe way to explore?",
            "Drawing lets you remember what you saw without grabbing or poking anything. Your eyes do the exploring instead of your hands.",
        )
    ],
    "viewing": [
        (
            "Why is it good to watch tiny animals from a little distance?",
            "A little distance keeps both you and the animal calmer. You can still see a lot, but you do not scare them.",
        )
    ],
    "cool_water": [
        (
            "What can cool water do after a small sting or bite?",
            "Cool water can help the spot feel less hot and sharp. A grown-up can use it while checking that you are all right.",
        )
    ],
    "distance": [
        (
            "Why does stepping back help when insects are upset?",
            "Stepping back gives the insects room to settle down. It also keeps more bugs from climbing on you.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ant", "home", "bite", "magnifier", "map", "viewing", "cool_water", "distance"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    setting = f["setting"]
    hideout = f["hideout_cfg"]
    risk = f["risk_cfg"]
    t1, t2 = f["tools"]
    if f["outcome"] == "averted":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the words "ant", "jargon", and "shoe-dim", where children find {hideout.phrase} and choose to watch instead of touch.',
            f"Tell a gentle cautionary story set in {setting.place} where {a.label} wants to {risk.phrase}, but {b.label} repeats a safer rule and stops the mistake before it happens.",
            f'Write a repeating-rule story where the line "Watch, don\'t poke" helps children stay kind to an ant trail, and the ending uses {t1.phrase} and {t2.phrase} for safe exploring.',
        ]
    if f["outcome"] == "tears":
        return [
            f'Write a cautionary adventure for young children that includes the exact words "ant", "jargon", and "shoe-dim". A child disturbs an ant home, gets scared, learns a repeated safety rule, and returns safely another day.',
            f"Tell a story where {a.label} ignores a warning and tries to {risk.phrase} near {hideout.phrase}, so the adventure goes wrong before a grown-up helps.",
            f'Write a story with repetition, a clear lesson, and a safe ending image: "Watch, don\'t poke."',
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "ant", "jargon", and "shoe-dim". Two children follow an ant trail, one makes a risky choice, and a grown-up teaches a safer way to explore.',
        f"Tell a gentle cautionary story set in {setting.place} where {a.label} wants to {risk.phrase}, but {b.label} warns that tiny creatures should be watched, not bothered.",
        f'Write a repeating-rule story that ends happily with {t1.phrase} and {t2.phrase}, and uses the line "Watch, don\'t poke."',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    setting = f["setting"]
    hideout = f["hideout_cfg"]
    risk = f["risk_cfg"]
    response = f["response"]
    t1, t2 = f["tools"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, on a tiny adventure in {setting.place}. Their {pw} helps them learn how to watch ants kindly.",
        ),
        (
            "What did the children find?",
            f"They found an ant trail carrying crumbs to {hideout.phrase}. That tiny hiding place made the trail feel like a secret adventure.",
        ),
        (
            "What was the explorer jargon in their game?",
            "They used made-up explorer jargon and called a crumb a gold dot and the bug trail a marching road. The pretend words made their bug hunt feel like a real expedition.",
        ),
        (
            f"Why did {b.label} warn {a.label}?",
            f"{b.label} warned {a.label} because bothering the ant home could make the ants rush out to defend it. The safe rule was to watch instead of touch.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.label} do after the warning?",
                f"{a.label} backed away and repeated, 'Watch, don't poke.' That choice stopped the trouble before the ants were disturbed.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.label} tried to {risk.phrase}?",
                f"The neat ant line broke apart and the ants rushed out to defend their home. The trouble started because {a.label} touched the hiding place instead of only watching it.",
            )
        )
        if f["outcome"] == "soothed":
            qa.append(
                (
                    f"How did {a.label}'s {pw} help?",
                    f"{pw.capitalize()} {response.qa_text}. That quick, calm help stopped the scare and showed the children what to do when a tiny adventure turns into a real problem.",
                )
            )
        else:
            qa.append(
                (
                    "Did the adventure stay fun that day?",
                    f"No. The stinging and tears ended the adventure early, even though everyone became safe again. The hard part is what made the repeated rule matter.",
                )
            )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {t1.phrase} and {t2.phrase}, and the children watched from a safe little distance. The ending proves they changed because they still had an adventure, but they did it gently.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["hideout_cfg"].tags)
    tags |= set(f["risk_cfg"].tags)
    tags |= set(f["response"].tags)
    for tool in f["tools"]:
        tags |= set(tool.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("has_ants", e.has_ants), ("safe_tool", e.safe_tool), ("soothing", e.soothing)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="backyard",
        hideout="step_crack",
        risk="finger",
        tool1="magnifier",
        tool2="picture_card",
        response="brush_and_cool",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
        notebook="a bug notebook",
    ),
    StoryParams(
        setting="garden",
        hideout="flower_pot",
        risk="stick",
        tool1="tiny_binoculars",
        tool2="kneeling_pad",
        response="shake_and_step",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        notebook="a green explorer notebook",
    ),
    StoryParams(
        setting="park",
        hideout="log_hollow",
        risk="splash",
        tool1="magnifier",
        tool2="tiny_binoculars",
        response="shake_and_step",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
        notebook="a tiny field notebook",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, H, R) :- setting(S), hideout(H), risk(R), affords(S, H), has_ants(H).
sensible_resp(Rp) :- response(Rp), sense(Rp, Sc), sense_min(M), Sc >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sib :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sib.
bonus(0) :- not older_sib.
authority(C + 1 + B) :- init_caution(C), bonus(B).

averted :- older_sib, authority(A), bravery_init(BR), A > BR.

severity(Hd + Rd + D) :-
    chosen_hideout(H), defend(H, Hd),
    chosen_risk(R), disturb(R, Rd),
    delay(D).

contained :- chosen_response(Rp), power(Rp, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(soothed) :- not averted, contained.
outcome(tears) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.afford_hides):
            lines.append(asp.fact("affords", sid, hid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("defend", hid, hideout.defend))
        if hideout.has_ants:
            lines.append(asp.fact("has_ants", hid))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("disturb", rid, risk.disturb))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_resp/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_resp"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_risk", params.risk),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_soothed(RESPONSES[params.response], HIDEOUTS[params.hideout], RISKS[params.risk], params.delay)
    return "soothed" if contained else "tears"


def _smoke_test() -> None:
    parser = build_parser()
    default_args = parser.parse_args([])
    params = resolve_params(default_args, random.Random(0))
    params.seed = 0
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("smoke test failed: generated empty story")
    if sample.world is None:
        raise StoryError("smoke test failed: missing world model")
    _ = format_qa(sample)
    curated = generate(CURATED[0])
    if "ant" not in curated.story.lower():
        raise StoryError("smoke test failed: curated story did not render correctly")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sense = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sense)} python={sorted(py_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

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
        _smoke_test()
        print("OK: smoke test generation passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny ant adventure with a cautionary repeated rule."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hideout:
        setting = SETTINGS[args.setting]
        hideout = HIDEOUTS[args.hideout]
        if not hideout_has_ants(setting, hideout):
            raise StoryError(explain_rejection(setting, hideout))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.risk is None or combo[2] == args.risk)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hideout_id, risk_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    tool1, tool2 = rng.sample(sorted(SAFE_TOOLS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    notebook = rng.choice(NOTEBOOKS + ["", ""])
    return StoryParams(
        setting=setting_id,
        hideout=hideout_id,
        risk=risk_id,
        tool1=tool1,
        tool2=tool2,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        notebook=notebook,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("hideout", HIDEOUTS),
        ("risk", RISKS),
        ("tool1", SAFE_TOOLS),
        ("tool2", SAFE_TOOLS),
        ("response", RESPONSES),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")

    setting = SETTINGS[params.setting]
    hideout = HIDEOUTS[params.hideout]
    risk = RISKS[params.risk]
    response = RESPONSES[params.response]
    if not hideout_has_ants(setting, hideout):
        raise StoryError(explain_rejection(setting, hideout))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.tool1 == params.tool2:
        raise StoryError("(Pick two different safe tools for the ending.)")

    world = tell(
        setting=setting,
        hideout=hideout,
        risk=risk,
        tools=(SAFE_TOOLS[params.tool1], SAFE_TOOLS[params.tool2]),
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        notebook=params.notebook,
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
        print(asp_program("", "#show valid/3.\n#show sensible_resp/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, hideout, risk) combos:\n")
        for setting, hideout, risk in combos:
            print(f"  {setting:8} {hideout:12} {risk}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.hideout} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
