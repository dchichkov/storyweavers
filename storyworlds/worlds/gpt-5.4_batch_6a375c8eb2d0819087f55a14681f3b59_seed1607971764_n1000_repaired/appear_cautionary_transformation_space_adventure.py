#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py
==============================================================================

A standalone story world about a child who wants to appear transformed for a
space adventure and reaches for the wrong kind of makeover tool. The world is
small and classical: children build a pretend mission, one child tries to use a
grown-up appearance-changing item, a real mess or stain follows unless an older
sibling stops it, and a calm grown-up redirects the adventure toward safe
costume play.

The domain emphasizes:
- cautionary structure
- transformation as visible state change
- space-adventure style
- constraint-checked combinations
- a Python reasonableness gate plus an inline ASP twin

Run it
------
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py --theme mars --forbidden marker --target face
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py --target beam
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py --json
    python storyworlds/worlds/gpt-5.4/appear_cautionary_transformation_space_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "sensible"}


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
    on_child: bool = False
    # physical / emotional axes
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
    rig: str
    mission: str
    call: str
    dark_spot: str
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
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    action: str
    result_word: str
    lesson: str
    strength: int
    mess: int
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
    appear_as: str
    line: str
    cleanup_line: str
    absorbent: bool
    on_child: bool
    severity: int = 1
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
class SafeDisguise:
    id: str
    phrase: str
    use: str
    effect: str
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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_stain_distress(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("instigator")
    target = world.get("target")
    if target.meters["stained"] < THRESHOLD:
        return out
    sig = ("stain_distress", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.memes["fear"] += 1
    actor.memes["embarrassment"] += 1
    if "room" in world.entities:
        world.get("room").meters["mess"] += 1
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    parent = world.get("parent")
    if target.meters["stained"] < THRESHOLD:
        return out
    sig = ("workload", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.meters["workload"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="stain_distress", tag="social", apply=_r_stain_distress),
    Rule(name="workload", tag="physical", apply=_r_workload),
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
        for sent in produced:
            world.say(sent)
    return produced


def target_is_transformable(forbidden: Forbidden, target: Target) -> bool:
    return target.absorbent


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stain_severity(forbidden: Forbidden, target: Target, delay: int) -> int:
    return forbidden.strength + target.severity + delay


def stain_comes_off(response: Response, forbidden: Forbidden, target: Target, delay: int) -> bool:
    return response.power >= stain_severity(forbidden, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_stain(world: World, target_id: str, forbidden: Forbidden) -> dict:
    sim = world.copy()
    _use_forbidden(sim, sim.get(target_id), forbidden, narrate=False)
    return {
        "stained": sim.get(target_id).meters["stained"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def _use_forbidden(world: World, target: Entity, forbidden: Forbidden, narrate: bool = True) -> None:
    target.meters["stained"] += float(forbidden.strength)
    target.meters["appearance_change"] += 1.0
    target.meters["mess"] += float(forbidden.mess)
    world.get("room").meters["mess"] += float(forbidden.mess)
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.call}!" {a.id} cried. "Tonight we fly {theme.mission}."'
    )
    world.say(
        f"They crouched beside {theme.dark_spot}, waiting for the pretend stars to appear."
    )


def need_disguise(world: World, a: Entity, b: Entity, target: Target) -> None:
    world.say(
        f"Then {a.id} had a new idea. If {a.pronoun()} could change {target.the}, "
        f"{a.pronoun()} thought {a.pronoun()} might appear as {target.appear_as}."
    )
    world.say(
        f'{b.id} looked up at {a.pronoun("object")}. "A real space hero does not need a messy surprise," '
        f'{b.pronoun()} said, but {a.id} was already dreaming.'
    )


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed toward {forbidden.where}. "I know what can do it," '
        f'{a.pronoun()} whispered. "{forbidden.phrase}!"'
    )
    world.say(
        f"For one shining second, the plan felt clever. {a.id} imagined how fast {forbidden.result_word} could make the costume change."
    )


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, target: Target, parent: Entity) -> None:
    pred = predict_stain(world, "target", forbidden)
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{b.id} caught {a.pronoun("possessive")} sleeve. "{a.id}, no. {parent.label_word.capitalize()} said '
        f'we do not touch {forbidden.label}. {target.line}. If you use it there, it may not wash off fast."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    instigator_older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"It will be fine," {a.id} said. Because {a.id} was {b.pronoun("possessive")} {rel}, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"It will be fine," {a.id} said, and reached for it anyway.'
        )


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked at {b.id}. '
        f'{b.id} was {a.pronoun("possessive")} older {rel}, and the warning landed at last.'
    )
    world.say(
        f'Together they left {forbidden.phrase} right where it belonged and went to ask {parent.label_word} for a safer way to make the mission feel real.'
    )


def transform(world: World, a: Entity, forbidden: Forbidden, target: Target) -> None:
    _use_forbidden(world, world.get("target"), forbidden, narrate=False)
    world.say(
        f"{a.id} {forbidden.action} {target.cleanup_line}. At first it looked amazing. "
        f"{target.The} changed at once, and {a.id} gasped as the new color seemed to belong to another creature from the stars."
    )
    world.say(
        f"Then the color kept spreading. It did not stop where {a.id} wanted, and the game no longer felt like a game."
    )


def alarm(world: World, a: Entity, b: Entity, target: Target, parent: Entity) -> None:
    world.say(
        f'"{target.The} will not come clean!" {a.id} cried.'
    )
    world.say(
        f'"{parent.label_word.upper()}!" {b.id} shouted as fast as a launch siren.'
    )


def rescue(world: World, parent: Entity, response: Response, target: Target) -> None:
    target_ent = world.get("target")
    target_ent.meters["stained"] = 0.0
    target_ent.meters["mess"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text.format(target=target.label)}."
    )
    world.say(
        f"Soon the wild color was gone, and the room felt like a living room again instead of a panicked spaceship."
    )


def rescue_fail(world: World, parent: Entity, response: Response, target: Target) -> None:
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {response.fail.format(target=target.label)}."
    )
    world.say(
        f"But the stain stayed behind, bright and stubborn. The space adventure sagged into a quiet, sticky mess."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and wrapped both children in a careful hug. '
        f'"I am glad you called me," {parent.pronoun()} said. "But {forbidden.lesson}. Things that change how something looks can change it for much longer than a game lasts."'
    )


def stubborn_lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden, target: Target) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} held {a.id} close until {a.pronoun()} stopped trembling. '
        f'"You are safe," {parent.pronoun()} whispered. "But look how long {target.the} stayed changed. {forbidden.lesson}."'
    )
    world.say(
        "After that, the children remembered that a fast costume trick could leave a slow problem behind."
    )


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, d1: SafeDisguise, d2: SafeDisguise) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["safety"] += 1
    b.memes["safety"] += 1
    next_day = "The next day" if world.facts.get("outcome") != "averted" else "A little later"
    world.say(
        f'{next_day}, {parent.label_word} brought out {d1.phrase} and {d2.phrase}. '
        f'"If you want to look ready for a mission," {parent.pronoun()} said, "use things made for play."'
    )
    world.say(
        f"{a.id} used {d1.use}, and {b.id} used {d2.use}. Soon they {d1.effect}, and together they {theme.ending}."
    )


def quiet_ending(world: World, a: Entity, b: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"That evening, {a.id} still joined the game, but now and then {a.pronoun()} touched {target.the} and remembered the trouble."
    )
    world.say(
        f"Even so, {a.id} and {b.id} finished their mission softly, steering their cardboard ship through pretend stars and promising to ask first next time."
    )


def tell(
    theme: Theme,
    forbidden: Forbidden,
    target_cfg: Target,
    disguises: tuple[SafeDisguise, SafeDisguise],
    response: Response,
    *,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    cautioner: str = "Leo",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    a.id = instigator
    world.entities[instigator] = world.entities.pop("instigator")
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "trust": trust},
        traits=[trait],
    ))
    b.id = cautioner
    world.entities[cautioner] = world.entities.pop("cautioner")
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    parent.id = "Parent"
    world.entities["Parent"] = world.entities.pop("parent")
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(
        id="target",
        type="target",
        label=target_cfg.label,
        absorbent=target_cfg.absorbent,
        on_child=target_cfg.on_child,
    ))

    # initialize read-before-write values
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.get("room").meters["mess"] = 0.0
    world.get("target").meters["stained"] = 0.0
    world.get("target").meters["mess"] = 0.0
    world.get("target").meters["appearance_change"] = 0.0
    Parent = world.get("Parent")

    play_setup(world, a, b, theme)
    need_disguise(world, a, b, target_cfg)

    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target_cfg, Parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, forbidden, Parent)
        outcome = "averted"
        world.para()
        safe_gift(world, Parent, a, b, theme, disguises[0], disguises[1])
        contained = True
    else:
        defy(world, a, b, forbidden)
        world.para()
        transform(world, a, forbidden, target_cfg)
        alarm(world, a, b, target_cfg, Parent)

        contained = stain_comes_off(response, forbidden, target_cfg, delay)
        outcome = "contained" if contained else "lasting"

        world.para()
        if contained:
            rescue(world, Parent, response, target_cfg)
            lesson(world, Parent, a, b, forbidden)
            world.para()
            safe_gift(world, Parent, a, b, theme, disguises[0], disguises[1])
        else:
            rescue_fail(world, Parent, response, target_cfg)
            stubborn_lesson(world, Parent, a, b, forbidden, target_cfg)
            world.para()
            quiet_ending(world, a, b, theme, target_cfg)

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=Parent,
        theme=theme,
        forbidden=forbidden,
        target_cfg=target_cfg,
        target=world.get("target"),
        disguises=disguises,
        response=response,
        outcome=outcome,
        relation=relation,
        delay=delay,
        transformed=world.get("target").meters["appearance_change"] >= THRESHOLD or outcome == "lasting",
        cleaned=contained,
        severity=stain_severity(forbidden, target_cfg, delay) if not averted else 0,
        averted=averted,
        promised=(a.memes["lesson"] >= THRESHOLD),
    )
    return world


THEMES = {
    "moon": Theme(
        id="moon",
        scene="a silver moon base",
        rig="The sofa was the command ship, two laundry baskets became rocky craters, and a line of pillows made a path through space dust.",
        mission="to the sleeping moon caves",
        call="Captain to Scout",
        dark_spot="the shadow under the coffee table",
        ending="launched their brave little ship past the moon again",
    ),
    "mars": Theme(
        id="mars",
        scene="a red Mars station",
        rig="The rug was the dusty planet floor, a cardboard box became their rover, and a blanket tunnel led to the repair dock.",
        mission="across the windy red plains",
        call="Commander to Engineer",
        dark_spot="the dark repair tunnel by the couch",
        ending="rolled their rover over the red plains once more",
    ),
    "comet": Theme(
        id="comet",
        scene="a comet outpost",
        rig="The chairs were docking towers, a blanket made an icy tail, and their toy box became the supply bay.",
        mission="through the glittering ice trail",
        call="Pilot to Navigator",
        dark_spot="the narrow tunnel between the chairs",
        ending="sailed their comet ship through sparkling dark again",
    ),
}

FORBIDDEN = {
    "marker": Forbidden(
        id="marker",
        label="the permanent marker",
        phrase="The permanent marker",
        where="the desk drawer",
        action="dragged the dark tip across",
        result_word="one quick swipe",
        lesson="permanent markers are not for skin or costumes during play",
        strength=2,
        mess=1,
        tags={"marker", "stain", "ask_first"},
    ),
    "dye_spray": Forbidden(
        id="dye_spray",
        label="the silver hair-dye spray",
        phrase="The silver hair-dye spray",
        where="the bathroom cabinet",
        action="pressed the little nozzle at",
        result_word="a silver puff",
        lesson="grown-up dye sprays are not for children to use by themselves",
        strength=3,
        mess=2,
        tags={"dye", "stain", "ask_first"},
    ),
    "shoe_polish": Forbidden(
        id="shoe_polish",
        label="the black shoe polish",
        phrase="The black shoe polish",
        where="the hall closet",
        action="rubbed a shiny smear onto",
        result_word="one bold shine",
        lesson="shoe polish belongs on shoes, not on children or costumes",
        strength=3,
        mess=2,
        tags={"polish", "stain", "ask_first"},
    ),
}

TARGETS = {
    "face": Target(
        id="face",
        label="face",
        the="the face",
        appear_as="a green moon alien",
        line="Faces are easy to stain and hard to scrub gently",
        cleanup_line="onto her face" if False else "onto the face",
        absorbent=True,
        on_child=True,
        severity=2,
        tags={"face", "skin"},
    ),
    "hands": Target(
        id="hands",
        label="hands",
        the="the hands",
        appear_as="a crater beast with strange claws",
        line="Hands pick color up fast and carry it everywhere",
        cleanup_line="across the hands",
        absorbent=True,
        on_child=True,
        severity=1,
        tags={"hands", "skin"},
    ),
    "hair": Target(
        id="hair",
        label="hair",
        the="the hair",
        appear_as="a silver comet captain",
        line="Hair can hold color for a long time",
        cleanup_line="into the hair",
        absorbent=True,
        on_child=True,
        severity=2,
        tags={"hair", "dye"},
    ),
    "pajamas": Target(
        id="pajamas",
        label="pajamas",
        the="the pajamas",
        appear_as="a star-speckled space explorer",
        line="Pajamas can soak up dark color and keep it",
        cleanup_line="onto the pajamas",
        absorbent=True,
        on_child=True,
        severity=2,
        tags={"clothes", "stain"},
    ),
    "beam": Target(
        id="beam",
        label="flashlight beam",
        the="the flashlight beam",
        appear_as="a glowing alien signal",
        line="A beam is only light, and color rubbed on it will not stay there",
        cleanup_line="into the flashlight beam",
        absorbent=False,
        on_child=False,
        severity=0,
        tags={"light"},
    ),
}

SAFE_DISGUISES = {
    "antennae": SafeDisguise(
        id="antennae",
        phrase="paper antennae on a soft headband",
        use="the paper antennae to bob over the helmet",
        effect="looked wonderfully spacey without changing anything that had to stay clean",
        tags={"costume", "headband"},
    ),
    "stickers": SafeDisguise(
        id="stickers",
        phrase="glow-star stickers",
        use="the glow-star stickers on a shirt and helmet",
        effect="looked ready for launch under the lamp light",
        tags={"stickers", "costume"},
    ),
    "cape": SafeDisguise(
        id="cape",
        phrase="a silver clip-on cape",
        use="the silver cape over the shoulders",
        effect="appeared like brave explorers from another world",
        tags={"cape", "costume"},
    ),
    "visor": SafeDisguise(
        id="visor",
        phrase="a cardboard star visor",
        use="the cardboard visor with a grin",
        effect="looked as if they had just stepped out of a tiny rocket",
        tags={"visor", "costume"},
    ),
}

RESPONSES = {
    "soap": Response(
        id="soap",
        sense=3,
        power=3,
        text="washed the {target} with warm water, soap, and a soft cloth until the color finally lifted",
        fail="washed and washed at the {target}, but the stain still clung there",
        qa_text="washed it off with warm water, soap, and a soft cloth",
        tags={"soap", "cleaning"},
    ),
    "bath": Response(
        id="bath",
        sense=3,
        power=4,
        text="set up a warm bath and gently cleaned the {target} until the strange color faded away",
        fail="even gave the {target} a long warm bath, but the color would not fully fade",
        qa_text="used a warm bath and gentle washing to clean it",
        tags={"bath", "cleaning"},
    ),
    "oil": Response(
        id="oil",
        sense=2,
        power=2,
        text="used a little oil and a washcloth to loosen the color from the {target}",
        fail="rubbed at the {target} with oil and a washcloth, but too much color had already sunk in",
        qa_text="used oil and a washcloth to loosen the color",
        tags={"oil", "cleaning"},
    ),
    "scrub_hard": Response(
        id="scrub_hard",
        sense=1,
        power=1,
        text="scrubbed at the {target} much too hard",
        fail="scrubbed at the {target}, but it only made everyone miserable and did not fix much",
        qa_text="scrubbed at it",
        tags={"cleaning"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mia", "Ava", "Zoe", "Iris", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Noah", "Sam", "Jack"]
TRAITS = ["careful", "cautious", "thoughtful", "sensible", "curious", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for forbidden_id, forbidden in FORBIDDEN.items():
            for target_id, target in TARGETS.items():
                if target_is_transformable(forbidden, target):
                    combos.append((theme_id, forbidden_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    target: str
    disguise1: str
    disguise2: str
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
    "marker": [(
        "What is a permanent marker?",
        "A permanent marker is a strong pen whose ink is made to stay. That is why children should only use it with a grown-up when it is meant for the job."
    )],
    "dye": [(
        "What does hair-dye spray do?",
        "Hair-dye spray changes how hair looks by covering it with color. It is not a toy, and children should not spray it on themselves during play."
    )],
    "polish": [(
        "What is shoe polish for?",
        "Shoe polish is made to shine and darken shoes. It is messy on skin and clothes, so it should stay on shoes."
    )],
    "stain": [(
        "What is a stain?",
        "A stain is color or dirt that sinks into something and stays there. Some stains come out quickly, but some need a lot of careful cleaning."
    )],
    "ask_first": [(
        "Why should children ask before using grown-up products?",
        "Grown-up products can be strong, messy, or hard to clean. Asking first helps a grown-up choose something safe for play."
    )],
    "soap": [(
        "How does soap help clean things?",
        "Soap helps lift dirt, oil, and some color away so water can carry them off. That is why washing gently with soap often helps a mess come clean."
    )],
    "bath": [(
        "Why can a warm bath help with a messy accident?",
        "Warm water softens sticky messes and gives time for gentle cleaning. It can help a child calm down while the mess is washed away."
    )],
    "oil": [(
        "Why might oil help remove sticky color?",
        "Some sticky colors cling to skin or hair, and oil can help loosen them. A grown-up decides when that is a good idea."
    )],
    "costume": [(
        "What makes a costume safer than using dye or polish?",
        "A costume changes how you look without soaking into skin or clothes. You can take it off when playtime ends."
    )],
    "stickers": [(
        "Why are stickers good for pretend play?",
        "Stickers can decorate a costume without changing your real skin or hair. They make things look different, but they are meant to come off."
    )],
    "cape": [(
        "What does a cape do in pretend play?",
        "A cape makes a child look ready for an adventure right away. It changes the look of the costume without making a hard-to-clean mess."
    )],
    "visor": [(
        "What is a visor?",
        "A visor is a piece that sits in front of your forehead and eyes like part of a helmet. A cardboard visor can make pretend space gear look exciting."
    )],
    "headband": [(
        "What is a headband costume piece?",
        "A headband sits on top of your head and can hold safe decorations like paper antennae. It helps something new appear without changing your real hair."
    )],
}
KNOWLEDGE_ORDER = [
    "marker", "dye", "polish", "stain", "ask_first",
    "soap", "bath", "oil",
    "costume", "stickers", "cape", "visor", "headband",
]


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
    theme = f["theme"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    d1, d2 = f["disguises"]
    base = (
        f'Write a short space-adventure story for a 3-to-5-year-old where a child wants to appear as {target.appear_as} and reaches for {forbidden.label}. Include the word "appear".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary transformation story where {a.id} wants to use {forbidden.label}, but {b.id} stops the mistake before it happens and they ask a grown-up for safe costume help.",
            f'Write a gentle story set in {theme.scene} where a child almost uses a grown-up item to change how {target.the} looks, then chooses {d1.phrase} and {d2.phrase} instead.',
        ]
    if outcome == "lasting":
        return [
            base,
            f"Tell a cautionary space story where {a.id} changes {target.the} with {forbidden.label}, but the color will not come off right away and the child learns why asking first matters.",
            f'Write a story with a transformation that goes wrong: a pretend mission starts brightly, a stain lasts longer than the game, and the ending teaches that costumes are safer than grown-up products.',
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {a.id} uses {forbidden.label} to look spacey, a grown-up helps clean the mess, and the children finish the mission with safe costume pieces.",
        f'Write a transformation story in a space-adventure style that ends with {d1.phrase} and {d2.phrase} instead of a risky makeover.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    response = f["response"]
    d1, d2 = f["disguises"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {a.id} and {b.id}, who were playing a space mission together. It also includes their {parent.label_word}, who helped when the pretend costume idea became a real problem."
        ),
        (
            "What were the children pretending?",
            f"They had turned the living room into {theme.scene} and were getting ready for a mission. The space game made them want the costume to look more exciting."
        ),
        (
            f"Why did {a.id} want to use {forbidden.label}?",
            f"{a.id} wanted to change {target.the} and appear as {target.appear_as}. The makeover seemed fast and magical, so it felt like a shortcut to the mission."
        ),
        (
            f"What warning did {b.id} give?",
            f"{b.id} said they were not allowed to use {forbidden.label} and warned that {target.the} might stain and stay changed too long. The warning came before the accident because {b.id} could see the danger in using a grown-up product for play."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{a.id} listened and backed down, so no stain ever started. Then the children asked their {parent.label_word} for a safer way to make the mission feel real."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily with {d1.phrase} and {d2.phrase} instead of a risky makeover. The children still looked ready for space, but nothing had to be scrubbed away."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {a.id} used {forbidden.label}?",
            f"{target.The} changed right away, but the color kept spreading farther than {a.id} wanted. The transformation stopped feeling fun because it became a real stain instead of a pretend costume."
        ))
        qa.append((
            f"How did the grown-up fix it?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That worked because the grown-up acted quickly and used a careful cleaning method meant to remove the mess."
        ))
        qa.append((
            "What changed by the end?",
            f"The stain was gone, the children had learned not to use grown-up products for pretend play, and they finished with safe costume pieces instead. The ending proves the adventure could continue once the unsafe shortcut was replaced."
        ))
    else:
        qa.append((
            f"Did the color come off quickly?",
            f"No. Their {parent.label_word} tried to help, but the stain stayed bright and stubborn for a while. That is what made the lesson feel serious instead of silly."
        ))
        qa.append((
            "Why is the ending cautionary?",
            f"The children were safe, but the unwanted change lasted longer than the game. Because the stain stayed, the ending shows how one quick risky choice can keep causing trouble afterward."
        ))
        qa.append((
            "How did the children act at the very end?",
            f"They finished the mission quietly and promised to ask first next time. The space game was still there, but now it carried a careful memory with it."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["forbidden"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
    for disguise in f["disguises"]:
        tags |= set(disguise.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.absorbent:
            bits.append("absorbent=True")
        if e.on_child:
            bits.append("on_child=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not target.absorbent:
        return (
            f"(No story: {target.the} cannot really be changed by {forbidden.label}. "
            f"The child wants a transformation that will appear on something physical, so pick a target like face, hands, hair, or pajamas.)"
        )
    return "(No story: this combination does not make a reasonable transformation problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    forbidden = FORBIDDEN[params.forbidden]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]
    return "contained" if stain_comes_off(response, forbidden, target, params.delay) else "lasting"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
transformable(F, T) :- forbidden(F), target(T), absorbent(T).
valid(Th, F, T) :- theme(Th), transformable(F, T).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ----------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(Sf + St + D) :- chosen_forbidden(F), strength(F, Sf), chosen_target(T), target_severity(T, St), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lasting) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for forbidden_id, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        lines.append(asp.fact("strength", forbidden_id, forbidden.strength))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.absorbent:
            lines.append(asp.fact("absorbent", target_id))
        lines.append(asp.fact("target_severity", target_id, target.severity))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
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
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_forbidden", params.forbidden),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(250):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} scenarios differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child wants to appear transformed for a space mission and learns to choose safe costume play."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target:
        target = TARGETS[args.target]
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        if not target_is_transformable(forbidden, target):
            raise StoryError(explain_rejection(forbidden, target))
    if args.forbidden and args.target:
        forbidden = FORBIDDEN[args.forbidden]
        target = TARGETS[args.target]
        if not target_is_transformable(forbidden, target):
            raise StoryError(explain_rejection(forbidden, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, forbidden_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    disguise1, disguise2 = rng.sample(sorted(SAFE_DISGUISES), 2)
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme_id,
        forbidden=forbidden_id,
        target=target_id,
        disguise1=disguise1,
        disguise2=disguise2,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent_type,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.forbidden not in FORBIDDEN:
        raise StoryError(f"(Unknown forbidden item: {params.forbidden})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.disguise1 not in SAFE_DISGUISES or params.disguise2 not in SAFE_DISGUISES:
        raise StoryError("(Unknown safe disguise choice.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not target_is_transformable(FORBIDDEN[params.forbidden], TARGETS[params.target]):
        raise StoryError(explain_rejection(FORBIDDEN[params.forbidden], TARGETS[params.target]))

    world = tell(
        THEMES[params.theme],
        FORBIDDEN[params.forbidden],
        TARGETS[params.target],
        (SAFE_DISGUISES[params.disguise1], SAFE_DISGUISES[params.disguise2]),
        RESPONSES[params.response],
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
        theme="moon",
        forbidden="marker",
        target="face",
        disguise1="antennae",
        disguise2="stickers",
        response="soap",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="mars",
        forbidden="dye_spray",
        target="hair",
        disguise1="cape",
        disguise2="visor",
        response="bath",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Iris",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="comet",
        forbidden="shoe_polish",
        target="pajamas",
        disguise1="stickers",
        disguise2="cape",
        response="oil",
        instigator="Luna",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="cautious",
        delay=2,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        theme="mars",
        forbidden="marker",
        target="hands",
        disguise1="visor",
        disguise2="antennae",
        response="soap",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Noah",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=2,
    ),
    StoryParams(
        theme="moon",
        forbidden="dye_spray",
        target="pajamas",
        disguise1="stickers",
        disguise2="visor",
        response="bath",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=6,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sens = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (theme, forbidden, target) combos:\n")
        for theme_id, forbidden_id, target_id in combos:
            print(f"  {theme_id:8} {forbidden_id:11} {target_id}")
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
                f"### {p.instigator} & {p.cautioner}: {p.forbidden} -> {p.target} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
