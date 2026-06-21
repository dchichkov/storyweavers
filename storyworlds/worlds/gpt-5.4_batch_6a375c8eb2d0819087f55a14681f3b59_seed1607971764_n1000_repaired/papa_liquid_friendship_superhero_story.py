#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py
====================================================================

A standalone story world about two children playing superheroes, a tempting
grown-up liquid that does not belong in the game, a loyal friend who tries to
protect a teammate, and papa helping them choose a safe heroic way instead.

The core shape is:

    heroic play -> need for a dramatic "power effect"
    tempting unsafe liquid -> friend warns
    friendship may avert the spill
    otherwise spill happens -> papa contains it or the mission set collapses
    safe substitute restores the game and proves what changed

The world models both physical meters (spill, soggy, danger, collapse) and
emotional memes (joy, loyalty, fear, relief, trust). Prose is rendered from the
simulated state, not from a single frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py --liquid cleaner --target cardboard_city
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py --target metal_tray
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/papa_liquid_friendship_superhero_story.py --verify
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
STEADY_TRAITS = {"steady", "careful", "loyal"}


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
    absorbent: bool = False
    harmful: bool = False
    playful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "papa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Theme:
    id: str
    scene: str
    setup: str
    titles: tuple[str, str]
    mission: str
    problem: str
    ending: str
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
class UnsafeLiquid:
    id: str
    label: str
    phrase: str
    where: str
    splash: str
    warning: str
    tags: set[str] = field(default_factory=set)
    harmful: bool = True
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
    absorbent: bool
    damage: str
    collapse_text: str
    spread: int
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
class SafeEffect:
    id: str
    label: str
    phrase: str
    action: str
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
    success: str
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
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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
        if ent.meters["spilled_on"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["soggy"] += 1
        if ent.absorbent:
            ent.meters["ruined"] += 1
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__spill__")
    return out


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["ruined"] < THRESHOLD:
            continue
        sig = ("collapse", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["collapsed"] += 1
        for kid in world.kids():
            kid.memes["sadness"] += 1
        out.append("__collapse__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
    Rule(name="collapse", tag="physical", apply=_r_collapse),
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


def hazard_at_risk(liquid: UnsafeLiquid, target: Target) -> bool:
    return liquid.harmful and target.absorbent


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= spill_severity(target, delay)


def would_avert(trait: str, trust: int) -> bool:
    return trait in STEADY_TRAITS and trust >= 6


def predict_spill(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get(target_id), narrate=False)
    return {
        "ruined": sim.get(target_id).meters["ruined"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "collapsed": sim.get(target_id).meters["collapsed"] >= THRESHOLD,
    }


def _do_spill(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["spilled_on"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After lunch, {hero.id} and {friend.id} turned the family room into {theme.scene}. "
        f"{theme.setup}"
    )
    world.say(
        f'"{theme.titles[0]} {hero.id} and {theme.titles[1]} {friend.id}!" '
        f"{hero.id} cheered. \"{theme.mission}\""
    )


def need_effect(world: World, friend: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But {theme.problem}, and {target.the} did not look heroic enough yet."
    )
    world.say(
        f'{friend.id} knelt beside {target.the}. "{theme.problem} We need something flashy," '
        f"{friend.pronoun()} said."
    )


def temptation(world: World, hero: Entity, liquid: UnsafeLiquid) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} pointed toward {liquid.where}. "I know! {liquid.phrase}!"'
    )
    world.say(
        f"For one bright second, the bottle of liquid looked like secret superhero fuel."
    )


def warning(world: World, friend: Entity, hero: Entity, liquid: UnsafeLiquid, target: Target) -> None:
    pred = predict_spill(world, "target")
    world.facts["predicted_danger"] = pred["danger"]
    friend.memes["loyalty"] += 1
    world.say(
        f'{friend.id} caught {hero.id}\'s sleeve. "No, {hero.id}. Papa said {liquid.warning}. '
        f'If it splashes on {target.the}, {target.damage}."'
    )


def defy(world: World, hero: Entity, friend: Entity, liquid: UnsafeLiquid) -> None:
    hero.memes["defiance"] += 1
    if friend.memes["trust"] >= 7:
        middle = (
            f" {friend.id} did not want to fight with a teammate, and for one shaky moment "
            f"{friend.pronoun()} hoped {hero.id} knew what {hero.pronoun()} was doing."
        )
    else:
        middle = f" {friend.id} reached out again, but {hero.id} was already hurrying away."
    world.say(
        f'"It will make our powers stronger," {hero.id} said.{middle}'
    )


def back_down(world: World, hero: Entity, friend: Entity, papa: Entity, liquid: UnsafeLiquid) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{hero.id} looked at the bottle, then at {friend.id}\'s worried face, and slowly nodded. '
        f'"Okay," {hero.pronoun()} said. "A real hero does not use mystery liquid."'
    )
    world.say(
        f"Together they carried the bottle to papa and told him what almost happened."
    )
    world.say(
        f'Papa smiled and ruffled both heads. "That was true teamwork," he said. '
        f'"Friends keep each other safe."'
    )


def spill(world: World, hero: Entity, friend: Entity, liquid: UnsafeLiquid, target_ent: Entity, target: Target) -> None:
    _do_spill(world, target_ent, narrate=True)
    world.say(
        f"{hero.id} tipped the bottle too fast. {liquid.splash} splashed across {target.near}, "
        f"and at once {target.damage}."
    )
    world.say(
        f'"{hero.id}!" {friend.id} cried. "Call papa!"'
    )


def rescue(world: World, papa: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["spilled_on"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"Papa came in at superhero speed and {response.success.replace('{target}', target.label)}."
    )
    world.say(
        f"The sharp smell faded, and the room felt safe again, though everyone was still shaky."
    )


def rescue_fail(world: World, papa: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "room" in world.entities:
        world.get("room").meters["danger"] += 1
    target_ent.meters["collapsed"] += 1
    world.say(
        f"Papa hurried in and {response.fail.replace('{target}', target.label)}."
    )
    world.say(
        f"{target.collapse_text} The mission set was lost for the day."
    )


def lesson(world: World, papa: Entity, hero: Entity, friend: Entity, liquid: UnsafeLiquid) -> None:
    for kid in (hero, friend):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'Papa knelt beside them. "I am glad you called me," he said softly. '
        f'"{liquid.warning.capitalize()}. If you do not know what a liquid is for, '
        f'you stop and ask a grown-up."'
    )
    world.say(
        f'{hero.id} nodded first, and {friend.id} squeezed {hero.pronoun("possessive")} hand. '
        f'"We will," they said.'
    )


def safe_gift(world: World, papa: Entity, hero: Entity, friend: Entity, theme: Theme, s1: SafeEffect, s2: SafeEffect) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then papa opened a cupboard and brought out {s1.phrase} and {s2.phrase}."
    )
    world.say(
        f'"If your mission needs drama," he said, "use tools meant for play."'
    )
    world.say(
        f"{friend.id} {s1.action}, and {hero.id} {s2.action}. Soon the room flashed with safe pretend power."
    )
    world.say(
        f"They finished {theme.ending}, bumping fists like real partners."
    )


def rebuild_after_loss(world: World, papa: Entity, hero: Entity, friend: Entity, theme: Theme, s1: SafeEffect, s2: SafeEffect, target: Target) -> None:
    for kid in (hero, friend):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'Papa hugged them close. "The cardboard can be replaced," he said. '
        f'"What matters is that people stay safe, and that teammates tell the truth."'
    )
    world.say(
        f"{hero.id} whispered sorry to {friend.id}, and {friend.id} answered by hugging back."
    )
    world.say(
        f"Later, papa brought out {s1.phrase} and {s2.phrase}, and the friends built a smaller new {target.label} together."
    )
    world.say(
        f"This time they used safe pretend power, and the new heroes ended the afternoon shoulder to shoulder."
    )


def tell(
    theme: Theme,
    liquid: UnsafeLiquid,
    target: Target,
    safe_effects: tuple[SafeEffect, SafeEffect],
    response: Response,
    hero_name: str = "Max",
    hero_gender: str = "boy",
    friend_name: str = "Lia",
    friend_gender: str = "girl",
    trait: str = "steady",
    trust: int = 7,
    delay: int = 0,
    hero_age: int = 6,
    friend_age: int = 6,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["bold"],
            age=hero_age,
            attrs={},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[trait],
            age=friend_age,
            attrs={},
        )
    )
    papa = world.add(
        Entity(
            id="Papa",
            kind="character",
            type="papa",
            role="papa",
            label="papa",
            traits=["calm"],
            attrs={},
        )
    )
    room = world.add(Entity(id="room", type="room", label="room", attrs={}))
    target_ent = world.add(
        Entity(
            id="target",
            type="prop",
            label=target.label,
            absorbent=target.absorbent,
            attrs={},
        )
    )
    tool = world.add(
        Entity(
            id="liquid",
            type="liquid",
            label=liquid.label,
            harmful=liquid.harmful,
            attrs={},
        )
    )

    hero.memes["bravery"] = 6.0
    friend.memes["trust"] = float(trust)
    friend.memes["caution"] = 5.0 if trait in STEADY_TRAITS else 3.0
    room.meters["danger"] = 0.0
    target_ent.meters["spilled_on"] = 0.0
    target_ent.meters["ruined"] = 0.0
    target_ent.meters["collapsed"] = 0.0
    tool.meters["amount"] = 1.0

    opening(world, hero, friend, theme)
    need_effect(world, friend, theme, target)

    world.para()
    temptation(world, hero, liquid)
    warning(world, friend, hero, liquid, target)

    averted = would_avert(trait, trust)
    if averted:
        back_down(world, hero, friend, papa, liquid)
        world.para()
        safe_gift(world, papa, hero, friend, theme, safe_effects[0], safe_effects[1])
        severity = 0
        contained = True
    else:
        defy(world, hero, friend, liquid)
        world.para()
        spill(world, hero, friend, liquid, target_ent, target)
        severity = spill_severity(target, delay)
        target_ent.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)

        world.para()
        if contained:
            rescue(world, papa, response, target_ent, target)
            lesson(world, papa, hero, friend, liquid)
            world.para()
            safe_gift(world, papa, hero, friend, theme, safe_effects[0], safe_effects[1])
        else:
            rescue_fail(world, papa, response, target_ent, target)
            rebuild_after_loss(world, papa, hero, friend, theme, safe_effects[0], safe_effects[1], target)

    outcome = "averted" if averted else ("contained" if contained else "collapsed")
    world.facts.update(
        hero=hero,
        friend=friend,
        papa=papa,
        room=room,
        theme=theme,
        liquid_cfg=liquid,
        target_cfg=target,
        target=target_ent,
        response=response,
        safe_effects=safe_effects,
        outcome=outcome,
        spilled=target_ent.meters["ruined"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        trust=trust,
        trait=trait,
    )
    return world


THEMES = {
    "city_rescue": Theme(
        id="city_rescue",
        scene="a secret city of blocks and couch cushions",
        setup="A blanket became the night sky, the sofa became headquarters, and a line of toy animals waited to be rescued from danger.",
        titles=("Captain", "Shield-Friend"),
        mission="Let's save every tiny citizen before sunset!",
        problem="the villains were supposed to crash through a glowing river",
        ending="their rescue through the shining city",
    ),
    "sky_patrol": Theme(
        id="sky_patrol",
        scene="a stormy sky made from chairs and blue sheets",
        setup="A laundry basket became a flying car, paper stars hung from string, and stuffed animals waited on rooftops for help.",
        titles=("Jet", "Wing-Friend"),
        mission="Sky Patrol is ready to swoop in!",
        problem="the cloud tunnel needed a streak of power",
        ending="their patrol above the toy rooftops",
    ),
    "moon_guard": Theme(
        id="moon_guard",
        scene="a silver moon base built from boxes and pillows",
        setup="Tin-foil stars blinked on the rug, a basket became the moon rover, and little robot toys lined up for inspection.",
        titles=("Comet", "Beacon-Friend"),
        mission="Moon Guard will protect the base tonight!",
        problem="the meteor shield needed a brave glow",
        ending="their watch over the moon base",
    ),
}

LIQUIDS = {
    "cleaner": UnsafeLiquid(
        id="cleaner",
        label="spray cleaner",
        phrase="the blue bottle of cleaning liquid",
        where="under the sink",
        splash="Cold blue liquid",
        warning="that cleaning liquid is for chores, not for play",
        tags={"liquid", "cleaner", "ask_grownup"},
    ),
    "polish": UnsafeLiquid(
        id="polish",
        label="furniture polish",
        phrase="the shiny can of polish liquid",
        where="in the hall closet",
        splash="A slick silver liquid",
        warning="that polish liquid is slippery and not for children to use",
        tags={"liquid", "slippery", "ask_grownup"},
    ),
    "soap_refill": UnsafeLiquid(
        id="soap_refill",
        label="soap refill",
        phrase="the giant soap refill liquid",
        where="beside the laundry shelf",
        splash="A thick blob of soap liquid",
        warning="that soap refill liquid is for grown-ups and can make a big messy spill",
        tags={"liquid", "soap", "ask_grownup"},
    ),
}

TARGETS = {
    "cardboard_city": Target(
        id="cardboard_city",
        label="cardboard city",
        the="the cardboard city",
        near="the cardboard towers",
        absorbent=True,
        damage="the cardboard softened and sagged",
        collapse_text="The cardboard towers folded like sleepy knees",
        spread=2,
        tags={"cardboard", "absorbent"},
    ),
    "paper_map": Target(
        id="paper_map",
        label="paper map",
        the="the paper map",
        near="the paper streets",
        absorbent=True,
        damage="the paper wrinkled into a soggy lump",
        collapse_text="The map curled up and the paper streets tore apart",
        spread=1,
        tags={"paper", "absorbent"},
    ),
    "felt_cape": Target(
        id="felt_cape",
        label="felt cape",
        the="the felt cape",
        near="the edge of the felt cape",
        absorbent=True,
        damage="the cape turned heavy and blotchy",
        collapse_text="The cape slumped in a wet heap and could not fly at all",
        spread=2,
        tags={"cape", "absorbent"},
    ),
    "metal_tray": Target(
        id="metal_tray",
        label="metal tray",
        the="the metal tray",
        near="the bright metal tray",
        absorbent=False,
        damage="the liquid only puddled and slid around",
        collapse_text="Nothing soaked in, so no real damage followed",
        spread=0,
        tags={"metal"},
    ),
}

SAFE_EFFECTS = {
    "bubble_wand": SafeEffect(
        id="bubble_wand",
        label="bubble wand",
        phrase="a bubble wand",
        action="blew a stream of silver bubbles",
        tags={"bubbles"},
    ),
    "water_mister": SafeEffect(
        id="water_mister",
        label="water mister",
        phrase="a little water mister",
        action="made a cool mist rainbow in the window light",
        tags={"water_play"},
    ),
    "flashlight": SafeEffect(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        action="clicked on a bright beam",
        tags={"flashlight"},
    ),
    "ribbon_spinner": SafeEffect(
        id="ribbon_spinner",
        label="ribbon spinner",
        phrase="a ribbon spinner",
        action="whirled bright ribbons in a circle",
        tags={"ribbon"},
    ),
}

RESPONSES = {
    "towels_and_box": Response(
        id="towels_and_box",
        sense=3,
        power=3,
        success="laid down towels, lifted the {target} away from the puddle, and wiped every last drop before it spread farther",
        fail="grabbed towels and tried to save the {target}, but too much had already soaked in",
        qa_text="used towels and moved the {target} away from the spill",
        tags={"cleanup", "towels"},
    ),
    "rinse_and_wipe": Response(
        id="rinse_and_wipe",
        sense=3,
        power=2,
        success="wiped up the spill, set the {target} aside, and cleaned the floor until it was safe",
        fail="wiped and wiped, but the {target} was already too soggy to save",
        qa_text="wiped up the spill and set the {target} aside to keep everyone safe",
        tags={"cleanup", "wipe"},
    ),
    "tiny_tissue": Response(
        id="tiny_tissue",
        sense=1,
        power=1,
        success="dabbed at the mess with one tiny tissue",
        fail="dabbed at the spill with one tiny tissue, but it was nowhere near enough",
        qa_text="dabbed at the spill with a tiny tissue",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Lia", "Maya", "Nora", "Zoe", "Ava", "Ella", "Lucy", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Theo", "Sam", "Noah", "Ben"]
TRAITS = ["steady", "careful", "loyal", "thoughtful", "curious", "boldish"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for liquid_id, liquid in LIQUIDS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(liquid, target):
                    combos.append((theme_id, liquid_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    liquid: str
    target: str
    response: str
    safe1: str
    safe2: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    trust: int = 7
    delay: int = 0
    hero_age: int = 6
    friend_age: int = 6
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
    "liquid": [
        (
            "What is a liquid?",
            "A liquid is something that can pour and splash, like water or soap. It does not keep its own shape, so it spreads into the shape of the cup or floor it is in.",
        )
    ],
    "ask_grownup": [
        (
            "What should a child do with a mystery bottle of liquid?",
            "A child should leave it alone and ask a grown-up what it is for. That keeps everyone safe because some liquids are only for cleaning or other chores.",
        )
    ],
    "cleanup": [
        (
            "Why do grown-ups clean spills quickly?",
            "They clean spills quickly so nobody slips, touches something unsafe, or lets the mess spread farther. Fast cleanup can stop a small problem from becoming a bigger one.",
        )
    ],
    "cardboard": [
        (
            "Why does cardboard get weak when liquid spills on it?",
            "Cardboard is made from pressed paper, and paper soaks liquid in. When that happens, it turns soft and bends instead of staying strong.",
        )
    ],
    "paper": [
        (
            "Why does paper wrinkle when it gets wet?",
            "Paper absorbs water into its fibers, so the fibers swell and twist. That makes the paper wrinkle and lose its smooth shape.",
        )
    ],
    "cape": [
        (
            "Why can a costume cape get ruined by a spill?",
            "A cape can soak up the liquid and become heavy, stained, or sticky. Then it does not feel good to wear or swirl anymore.",
        )
    ],
    "bubbles": [
        (
            "Why do bubbles feel magical in pretend play?",
            "Bubbles catch the light and float through the air, so they look sparkly and dramatic. They make a game feel special without using anything dangerous.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight a good pretend superhero tool?",
            "A flashlight makes a bright beam you can aim where you want. It feels powerful in a game, but it is meant for safe use.",
        )
    ],
    "water_play": [
        (
            "What does a water mister do?",
            "A water mister sprays a little mist instead of a heavy splash. It can make a cool effect in play when a grown-up says it is okay to use.",
        )
    ],
    "ribbon": [
        (
            "Why do ribbons look exciting in a superhero game?",
            "Ribbons spin and stream through the air, so they show motion even when nothing unsafe is happening. They make pretend powers easy to see.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "liquid",
    "ask_grownup",
    "cleanup",
    "cardboard",
    "paper",
    "cape",
    "bubbles",
    "flashlight",
    "water_play",
    "ribbon",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    theme = f["theme"]
    liquid = f["liquid_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a superhero story for a young child where two friends are tempted to use a mystery liquid in a game, but friendship helps them stop in time. Include the word "papa".',
            f"Tell a friendship-centered superhero story where {friend.id} protects {hero.id} from using {liquid.label}, and papa praises them for being a good team.",
            f"Write a simple story where a bold child listens to a loyal friend, tells papa the truth, and finishes the mission with safe pretend tools.",
        ]
    if outcome == "collapsed":
        return [
            f'Write a superhero story where a child ignores a friend\'s warning about a liquid, the mission set is ruined, but friendship and papa help the children recover safely.',
            f"Tell a story where {hero.id} uses {liquid.label} in play, the prop collapses, and the friends learn that heroes tell the truth and ask papa before touching mystery liquids.",
            f"Write a gentle cautionary superhero story with a sad middle and a hopeful ending built on friendship.",
        ]
    return [
        f'Write a superhero story for a young child where a tempting liquid causes a spill, papa helps, and friendship stays strong.',
        f"Tell a story where {friend.id} warns {hero.id} about {liquid.label}, papa cleans up the danger, and the children finish their mission with safe pretend power.",
        f"Write a simple friendship superhero story with a clear lesson: if you do not know what a liquid is for, stop and ask papa.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    papa = f["papa"]
    theme = f["theme"]
    liquid = f["liquid_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    safe1, safe2 = f["safe_effects"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}, and their papa who helps them when the superhero game turns risky.",
        ),
        (
            "What were the children pretending to be?",
            f"They were pretending to be superheroes in {theme.scene}. The mission gave them a brave problem to solve together.",
        ),
        (
            f"Why did {hero.id} want the liquid?",
            f"{hero.id} thought the liquid would make the mission look more powerful and dramatic. In the game, it seemed like secret superhero fuel.",
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} warned {hero.id} because papa had already said the liquid was not for play. {friend.pronoun().capitalize()} was trying to protect both {hero.id} and {target.the}, which shows the friendship part of the story.",
        ),
    ]

    if outcome == "averted":
        qa.append(
            (
                f"What happened after {friend.id} warned {hero.id}?",
                f"{hero.id} stopped, admitted the bottle was a bad idea, and took it to papa instead of using it. The danger ended before any spill happened because {hero.id} chose to trust a friend.",
            )
        )
        qa.append(
            (
                "How did papa help in the end?",
                f"Papa praised their teamwork and gave them {safe1.phrase} and {safe2.phrase}. Those tools gave the game a heroic feeling without using a risky liquid.",
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                f"What happened when the liquid hit {target.the}?",
                f"The spill made {target.the} start to fail right away, and everyone got scared. That happened because {target.the} could soak the liquid in instead of shedding it.",
            )
        )
        qa.append(
            (
                "How did papa fix the problem?",
                f"Papa {response.qa_text.replace('{target}', target.label)}. He moved fast enough to stop the danger from spreading farther through the room.",
            )
        )
        qa.append(
            (
                "How did friendship matter after the spill?",
                f"{friend.id} still stayed beside {hero.id} instead of running away angry. That helped the lesson feel like teamwork and care, not just trouble.",
            )
        )
    else:
        qa.append(
            (
                f"Could papa save {target.the}?",
                f"No. Papa came quickly, but too much liquid had already soaked in, so {target.the} collapsed. The spill had a head start, and the prop was too absorbent to recover.",
            )
        )
        qa.append(
            (
                "How did the story end after the loss?",
                f"The original mission set was gone, but papa reminded them that safety mattered more than cardboard. Then the friends built a smaller new set together, which showed the friendship had stayed strong.",
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that pretending to be brave is not the same as making a safe choice. A real hero stops and asks papa before touching a mystery liquid.",
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["liquid_cfg"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags)
    for eff in f["safe_effects"]:
        tags |= set(eff.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.absorbent:
            flags.append("absorbent")
        if e.harmful:
            flags.append("harmful")
        if e.playful:
            flags.append("playful")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="city_rescue",
        liquid="cleaner",
        target="cardboard_city",
        response="towels_and_box",
        safe1="bubble_wand",
        safe2="flashlight",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Lia",
        friend_gender="girl",
        trait="steady",
        trust=8,
        delay=0,
        hero_age=6,
        friend_age=6,
    ),
    StoryParams(
        theme="sky_patrol",
        liquid="polish",
        target="felt_cape",
        response="rinse_and_wipe",
        safe1="water_mister",
        safe2="ribbon_spinner",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        trait="thoughtful",
        trust=5,
        delay=0,
        hero_age=7,
        friend_age=6,
    ),
    StoryParams(
        theme="moon_guard",
        liquid="soap_refill",
        target="cardboard_city",
        response="rinse_and_wipe",
        safe1="bubble_wand",
        safe2="flashlight",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        trait="curious",
        trust=4,
        delay=1,
        hero_age=6,
        friend_age=6,
    ),
    StoryParams(
        theme="city_rescue",
        liquid="cleaner",
        target="paper_map",
        response="towels_and_box",
        safe1="water_mister",
        safe2="ribbon_spinner",
        hero_name="Ella",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        trait="loyal",
        trust=7,
        delay=0,
        hero_age=5,
        friend_age=6,
    ),
]


def explain_rejection(liquid: UnsafeLiquid, target: Target) -> str:
    if not target.absorbent:
        return (
            f"(No story: {liquid.label} is a risky liquid, but {target.the} would not soak it in. "
            f"There is no strong turn, so pick cardboard, paper, or felt instead.)"
        )
    return "(No story: this liquid and target do not make a plausible spill problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.trait, params.trust):
        return "averted"
    contained = is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "contained" if contained else "collapsed"


ASP_RULES = r"""
hazard(L, T) :- harmful(L), absorbent(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Theme, L, T) :- theme(Theme), liquid(L), target(T), hazard(L, T).

steady_trait(T) :- trait(T), is_steady(T).
averted :- steady_trait(T), trust(V), avert_trust(M), V >= M.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(collapsed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for liquid_id, liquid in LIQUIDS.items():
        lines.append(asp.fact("liquid", liquid_id))
        if liquid.harmful:
            lines.append(asp.fact("harmful", liquid_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.absorbent:
            lines.append(asp.fact("absorbent", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("avert_trust", 6))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
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
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_gate = set(asp_valid_combos())
    p_gate = set(valid_combos())
    if c_gate == p_gate:
        print(f"OK: gate matches valid_combos() ({len(c_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_gate - p_gate:
            print("  only in clingo:", sorted(c_gate - p_gate))
        if p_gate - c_gate:
            print("  only in python:", sorted(p_gate - c_gate))

    c_sensible = set(asp_sensible())
    p_sensible = {r.id for r in sensible_responses()}
    if c_sensible == p_sensible:
        print(f"OK: sensible responses match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        _ = smoke.to_json()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superheroes, friendship, papa, and a risky liquid."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].absorbent:
        liquid = LIQUIDS[args.liquid] if args.liquid else next(iter(LIQUIDS.values()))
        raise StoryError(explain_rejection(liquid, TARGETS[args.target]))
    if args.liquid and args.target:
        liquid = LIQUIDS[args.liquid]
        target = TARGETS[args.target]
        if not hazard_at_risk(liquid, target):
            raise StoryError(explain_rejection(liquid, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.liquid is None or c[1] == args.liquid)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, liquid, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe1, safe2 = rng.sample(sorted(SAFE_EFFECTS), 2)
    hero_name, hero_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=hero_name)
    trait = rng.choice(TRAITS)
    trust = rng.randint(3, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_age = rng.randint(5, 7)
    friend_age = rng.randint(5, 7)

    return StoryParams(
        theme=theme,
        liquid=liquid,
        target=target,
        response=response,
        safe1=safe1,
        safe2=safe2,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
        trust=trust,
        delay=delay,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def _checked_lookup(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(Unknown {field_name}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    theme = _checked_lookup(THEMES, params.theme, "theme")
    liquid = _checked_lookup(LIQUIDS, params.liquid, "liquid")
    target = _checked_lookup(TARGETS, params.target, "target")
    response = _checked_lookup(RESPONSES, params.response, "response")
    safe1 = _checked_lookup(SAFE_EFFECTS, params.safe1, "safe effect")
    safe2 = _checked_lookup(SAFE_EFFECTS, params.safe2, "safe effect")

    if not hazard_at_risk(liquid, target):
        raise StoryError(explain_rejection(liquid, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.safe1 == params.safe2:
        raise StoryError("(Choose two different safe effects.)")

    world = tell(
        theme=theme,
        liquid=liquid,
        target=target,
        safe_effects=(safe1, safe2),
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
        trust=params.trust,
        delay=params.delay,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
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
        print(f"{len(combos)} compatible (theme, liquid, target) combos:\n")
        for theme, liquid, target in combos:
            print(f"  {theme:11} {liquid:11} {target}")
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
                f"### {p.hero_name} & {p.friend_name}: {p.liquid} near {p.target} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
