#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/army_bravery_curiosity_misunderstanding_pirate_tale.py
=================================================================================

A standalone story world about two children turning a yard into an army camp and
getting into trouble because one child bravely, curiously, and wrongly
misunderstands a warning marker as part of the game.

The world is built around a small common-sense constraint:

    a warning marker must plausibly warn about the chosen hazard,
    and an adult response must be sensible enough to tell.

From there, the story can branch into:
- an averted near-miss, when a wiser older sibling talks the child out of it
- a contained rescue, when the adult reaches the child in time
- an oopsie ending, when the adult still helps but only after the child gets wet,
  scratched, or muddy first

Run it
------
    python storyworlds/worlds/gpt-5.4/army_bravery_curiosity_misunderstanding_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/army_bravery_curiosity_misunderstanding_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/army_bravery_curiosity_misunderstanding_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4/army_bravery_curiosity_misunderstanding_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

BRAVERY_INIT = 4.0
CURIOSITY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    titles: tuple[str, str]
    goal: str
    far_spot: str
    hideout_word: str
    role_solo: str
    role_plural: str
    send_off: str
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
class Marker:
    id: str
    label: str
    phrase: str
    where: str
    meaning: str
    misread: str
    warns: set[str] = field(default_factory=set)
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
    the: str
    place: str
    kind: str
    risk: int
    step_text: str
    fail_text: str
    aftermath: str
    safe_route: str
    ending_image: str
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
class SafeAid:
    id: str
    label: str
    phrase: str
    use_text: str
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


def _r_alarm(world: World) -> list[str]:
    hz = world.get("hazard")
    if hz.meters["breach"] < THRESHOLD:
        return []
    sig = ("alarm", hz.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("yard").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__alarm__"]


def _r_hazard_effect(world: World) -> list[str]:
    hz = world.get("hazard")
    child = world.get("instigator")
    if hz.meters["breach"] < THRESHOLD:
        return []
    kind = hz.attrs.get("hazard_kind", "")
    sig = ("effect", kind)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if kind == "water":
        child.meters["wet"] += 1
    elif kind == "thorn":
        child.meters["scratch"] += 1
    elif kind == "mud":
        child.meters["muddy"] += 1
    child.meters["oops"] += 1
    return ["__effect__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="hazard_effect", tag="physical", apply=_r_hazard_effect),
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


def marker_warns(marker: Marker, hazard: Hazard) -> bool:
    return hazard.kind in marker.warns


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(hazard: Hazard, delay: int) -> int:
    return hazard.risk + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= severity_of(hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT + 0.5 * CURIOSITY_INIT


def predict_misstep(world: World) -> dict:
    sim = world.copy()
    hazard = sim.get("hazard")
    child = sim.get("instigator")
    _do_misstep(sim, child, hazard, narrate=False, full=False)
    return {
        "danger": sim.get("yard").meters["danger"],
        "wet": child.meters["wet"],
        "scratch": child.meters["scratch"],
        "muddy": child.meters["muddy"],
    }


def _do_misstep(world: World, child: Entity, hazard: Entity, narrate: bool = True, full: bool = False) -> None:
    child.meters["near_hazard"] += 1
    hazard.meters["breach"] += 1
    if full:
        hazard.meters["breach"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the backyard into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" {a.id} said. "Today we march to {theme.goal}."'
    )


def need_path(world: World, b: Entity, theme: Theme, hazard: Hazard) -> None:
    world.say(
        f"But {theme.goal} lay past {theme.far_spot}, close to {hazard.the}. "
        f"It looked secret and exciting from far away."
    )
    world.say(
        f'{b.id} shaded {b.pronoun("possessive")} eyes. "We need the safe path first," '
        f'{b.pronoun()} said.'
    )


def spot_marker(world: World, a: Entity, marker: Marker) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"Then {a.id} spotted {marker.phrase} {marker.where}. "
        f'"Look!" {a.pronoun().capitalize()} whispered. "Maybe that is {marker.misread}."'
    )


def warn(world: World, b: Entity, a: Entity, marker: Marker, hazard: Hazard, parent: Entity) -> None:
    pred = predict_misstep(world)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = ""
    if pred["wet"] >= THRESHOLD:
        extra = " If anyone crossed there, someone could slip and get wet."
    elif pred["scratch"] >= THRESHOLD:
        extra = " If anyone crossed there, the thorns would scratch."
    elif pred["muddy"] >= THRESHOLD:
        extra = " If anyone crossed there, shoes would sink and get muddy."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{marker.label} does not mean {marker.misread}. '
        f'It means {marker.meaning}, and {parent.label_word} said to stay away from {hazard.the}."{extra}'
    )


def defy(world: World, a: Entity, marker: Marker) -> None:
    a.memes["bravado"] += 1
    a.memes["defiance"] += 1
    world.say(
        f'"I am brave enough to check," {a.id} said. Because {a.pronoun()} was curious '
        f'and sure of the misunderstanding, {a.pronoun()} marched toward {marker.label}.'
    )


def back_down(world: World, a: Entity, b: Entity, marker: Marker, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, who was older and very steady, and the brave feeling changed into a wiser one. '
        f'"Maybe it is not a secret army mark after all," {a.pronoun()} said.'
    )
    world.say(
        f'They left {marker.label} alone and ran to tell {parent.label_word} about the far-off {theme.hideout_word}.'
    )


def misstep(world: World, a: Entity, hazard_ent: Entity, hazard: Hazard) -> None:
    _do_misstep(world, a, hazard_ent, narrate=False, full=True)
    world.say(
        f"{a.id} took one more marching step, and then {hazard.step_text}."
    )


def alarm(world: World, b: Entity, a: Entity, hazard: Hazard, parent: Entity) -> None:
    cry = {
        "water": f'"{a.id}! The bank!"',
        "thorn": f'"{a.id}! The thorns!"',
        "mud": f'"{a.id}! The mud!"',
    }.get(hazard.kind, f'"{a.id}! Stop!"')
    world.say(f"{cry} {b.id} cried.")
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, a: Entity, hazard: Hazard) -> None:
    world.get("hazard").meters["breach"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    a.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text.replace('{hazard}', hazard.label)}."
    )
    world.say(
        f"Soon {a.id} was back on the grass, breathing fast but safe, while the scary feeling blew past."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, marker: Marker) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, nobody said anything.")
    world.say(
        f'Then {parent.label_word} knelt beside them and gave them both a hug. '
        f'"Being brave is good," {parent.pronoun()} said softly, "but brave does not mean guessing. '
        f'When you do not understand a warning, you stop and ask. {marker.label.capitalize()} means {marker.meaning}."'
    )
    world.say(f'"We will ask next time," {b.id} and {a.id} said together.')


def rescue_fail(world: World, parent: Entity, response: Response, a: Entity, hazard: Hazard) -> None:
    body = response.fail.replace("{hazard}", hazard.label)
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {body}."
    )
    if a.meters["wet"] >= THRESHOLD:
        world.say(f"When {a.id} was finally back on the grass, {a.pronoun('possessive')} socks dripped and {a.pronoun()} shivered.")
    elif a.meters["scratch"] >= THRESHOLD:
        world.say(f"When {a.id} was finally back on the grass, a prickly scratch smarted on {a.pronoun('possessive')} leg.")
    elif a.meters["muddy"] >= THRESHOLD:
        world.say(f"When {a.id} was finally back on the grass, mud clung to {a.pronoun('possessive')} shoes and knees.")


def oopsie_lesson(world: World, parent: Entity, a: Entity, b: Entity, marker: Marker) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} wrapped an arm around both children. '
        f'"You are safe, and that is what matters most," {parent.pronoun()} said. '
        f'"But a misunderstanding can still make a big mess. A warning marker is for listening, not guessing."'
    )
    world.say(
        f"{a.id} nodded hard. This time bravery felt different from charging ahead. It felt like stopping and asking."
    )


def safe_route(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, aid1: SafeAid, aid2: SafeAid, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if world.facts.get("outcome") == "averted":
        intro = "The next day, after everyone had talked it through"
    else:
        intro = "The next day, after the scare had been talked through"
    world.say(
        f"{intro}, {parent.label_word} had a better plan. {parent.pronoun().capitalize()} brought {aid1.phrase} and {aid2.phrase}."
    )
    world.say(
        f"{parent.pronoun().capitalize()} {aid1.use_text} and {aid2.use_text}, so the way to {theme.goal} no longer had to go near {hazard.the}."
    )
    world.say(
        f'This time {a.id} checked the markers, {b.id} led the line, and the little {theme.role_plural} {theme.send_off}. {hazard.ending_image}'
    )


def tell(
    theme: Theme,
    marker: Marker,
    hazard: Hazard,
    aids: tuple[SafeAid, SafeAid],
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        traits=["brave", "curious"],
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    yard = world.add(Entity(id="yard", type="place", label="the yard"))
    world.add(Entity(
        id="marker",
        type="marker",
        label=marker.label,
        attrs={"meaning": marker.meaning, "misread": marker.misread},
    ))
    hazard_ent = world.add(Entity(
        id="hazard",
        type="hazard",
        label=hazard.label,
        attrs={"hazard_kind": hazard.kind, "place": hazard.place},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["caution"] = initial_caution(trait)
    yard.meters["danger"] = 0.0
    hazard_ent.meters["breach"] = 0.0
    a.meters["wet"] = 0.0
    a.meters["scratch"] = 0.0
    a.meters["muddy"] = 0.0
    a.meters["oops"] = 0.0

    play_setup(world, a, b, theme)
    need_path(world, b, theme, hazard)

    world.para()
    spot_marker(world, a, marker)
    warn(world, b, a, marker, hazard, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    world.facts["child_names"] = (instigator, cautioner)

    if averted:
        back_down(world, a, b, marker, parent, theme)
        world.para()
        safe_route(world, parent, a, b, theme, aids[0], aids[1], hazard)
        severity = 0
        contained = True
        outcome = "averted"
    else:
        defy(world, a, marker)
        world.para()
        misstep(world, a, hazard_ent, hazard)
        alarm(world, b, a, hazard, parent)
        severity = severity_of(hazard, delay)
        contained = is_contained(response, hazard, delay)
        world.para()
        if contained:
            rescue(world, parent, response, a, hazard)
            lesson(world, parent, a, b, marker)
            outcome = "contained"
            world.para()
            safe_route(world, parent, a, b, theme, aids[0], aids[1], hazard)
        else:
            rescue_fail(world, parent, response, a, hazard)
            oopsie_lesson(world, parent, a, b, marker)
            outcome = "oopsie"
            world.para()
            safe_route(world, parent, a, b, theme, aids[0], aids[1], hazard)

    world.facts.update(
        theme=theme,
        marker_cfg=marker,
        hazard_cfg=hazard,
        response=response,
        aids=aids,
        instigator=a,
        cautioner=b,
        parent=parent,
        yard=yard,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        misunderstanding=marker.misread,
        predicted_danger=world.facts.get("predicted_danger", 0.0),
        name_instigator=instigator,
        name_cautioner=cautioner,
        wet=a.meters["wet"] >= THRESHOLD,
        scratch=a.meters["scratch"] >= THRESHOLD,
        muddy=a.meters["muddy"] >= THRESHOLD,
        oops=a.meters["oops"] >= THRESHOLD,
    )
    return world


THEMES = {
    "army_camp": Theme(
        id="army_camp",
        scene="a tiny army camp",
        rig="The lawn chair became the watchtower, a broom stood up like a flagpole, and a cardboard box held their paper rations and map.",
        titles=("Captain", "Scout"),
        goal="the hidden lookout",
        far_spot="the far corner by the fence",
        hideout_word="lookout",
        role_solo="army scout",
        role_plural="army scouts",
        send_off="marched along the new trail to the hidden lookout",
    ),
    "rescue_army": Theme(
        id="rescue_army",
        scene="a rescue army camp",
        rig="A blanket over two chairs became the command tent, a stick became a marching flag, and a drawn map promised a secret place to save.",
        titles=("Commander", "Scout"),
        goal="the rescue post",
        far_spot="the weedy edge of the yard",
        hideout_word="post",
        role_solo="rescue scout",
        role_plural="rescue scouts",
        send_off="marched in neat little steps to the rescue post",
    ),
    "garden_guard": Theme(
        id="garden_guard",
        scene="a garden guard camp",
        rig="The upside-down bucket became a drum, a broom became the parade pole, and a chalk map showed where the garden needed guarding.",
        titles=("Captain", "Lieutenant"),
        goal="the garden fort",
        far_spot="the narrow strip by the bushes",
        hideout_word="fort",
        role_solo="garden guard",
        role_plural="garden guards",
        send_off="marched safely to the garden fort",
    ),
}

MARKERS = {
    "red_x": Marker(
        id="red_x",
        label="the red X",
        phrase="a board with a great big red X",
        where="near the fence",
        meaning="stay away",
        misread="the secret army mark",
        warns={"water", "thorn", "mud"},
        tags={"warning_marker", "sign"},
    ),
    "striped_tape": Marker(
        id="striped_tape",
        label="the striped tape",
        phrase="yellow striped tape tied between two sticks",
        where="beside the path",
        meaning="do not cross here",
        misread="the finish line for the march",
        warns={"water", "mud"},
        tags={"warning_marker", "tape"},
    ),
    "keep_out": Marker(
        id="keep_out",
        label="the KEEP OUT sign",
        phrase='a sign that said "KEEP OUT"',
        where="at the side gate",
        meaning="children should not go in",
        misread="the name of the fort",
        warns={"thorn", "water"},
        tags={"warning_marker", "sign"},
    ),
}

HAZARDS = {
    "pond_bank": Hazard(
        id="pond_bank",
        label="pond bank",
        the="the slippery pond bank",
        place="by the pond",
        kind="water",
        risk=3,
        step_text="the grass gave a slick little slide under his shoe, and he skidded toward the water",
        fail_text="reached for him, but by then his shoes had already splashed into the cold edge of the pond",
        aftermath="his shoes and socks were wet",
        safe_route="a line of flat stepping stones well away from the bank",
        ending_image="The pond stayed off to the side, shiny and quiet, while their safe boots thumped onward.",
        tags={"water", "pond"},
    ),
    "thorn_patch": Hazard(
        id="thorn_patch",
        label="thorn patch",
        the="the thorn patch",
        place="by the roses",
        kind="thorn",
        risk=2,
        step_text="his foot sank into the weeds, and the thorny stems grabbed at his socks",
        fail_text="caught hold of him, but not before the thorns scratched at his leg",
        aftermath="a little scratch stung on his leg",
        safe_route="a ribbon path circling around the roses",
        ending_image="The thorn patch stayed far from their boots, and the ribbons fluttered like tiny flags.",
        tags={"thorn", "plants"},
    ),
    "compost_edge": Hazard(
        id="compost_edge",
        label="compost edge",
        the="the soft compost edge",
        place="near the compost heap",
        kind="mud",
        risk=2,
        step_text="the ground squished down like cake, and one foot sank deep into the soft brown muck",
        fail_text="pulled him back, but his shoes had already gone squelchy and muddy",
        aftermath="his shoes were muddy",
        safe_route="a neat row of wooden stepping blocks on dry ground",
        ending_image="Their steps landed on clean wooden blocks, and the muddy heap stayed only a smelly mountain nearby.",
        tags={"mud", "compost"},
    ),
}

SAFE_AIDS = {
    "blue_flags": SafeAid(
        id="blue_flags",
        label="blue flags",
        phrase="little blue flags",
        use_text="stuck the blue flags along the safe side of the yard",
        tags={"flags", "safe_path"},
    ),
    "rope_line": SafeAid(
        id="rope_line",
        label="rope line",
        phrase="a soft rope line",
        use_text="laid the rope line where small marching feet could follow it",
        tags={"rope", "safe_path"},
    ),
    "stepping_stones": SafeAid(
        id="stepping_stones",
        label="stepping stones",
        phrase="round stepping stones",
        use_text="set the stepping stones in a neat path",
        tags={"stones", "safe_path"},
    ),
    "toy_compass": SafeAid(
        id="toy_compass",
        label="toy compass",
        phrase="a toy compass",
        use_text="showed them how to stop, check the compass, and look for the safe markers before marching",
        tags={"compass", "safe_path"},
    ),
}

RESPONSES = {
    "grab_hand": Response(
        id="grab_hand",
        sense=3,
        power=2,
        text="caught his wrist and tugged him back from the {hazard}",
        fail="caught his wrist, but only after the first messy trouble had already happened at the {hazard}",
        qa_text="caught him by the wrist and pulled him away from the danger",
        tags={"adult_help"},
    ),
    "reach_rake": Response(
        id="reach_rake",
        sense=3,
        power=4,
        text="reached out with a long garden rake and guided him back from the {hazard}",
        fail="used the long rake, but he had already slipped into trouble beside the {hazard}",
        qa_text="used a long garden rake to guide him back to safe ground",
        tags={"adult_help", "tool_help"},
    ),
    "carry_back": Response(
        id="carry_back",
        sense=2,
        power=3,
        text="stepped in quickly, lifted him up, and carried him away from the {hazard}",
        fail="lifted him out, but not before the trouble at the {hazard} had already left its mark",
        qa_text="lifted him away from the danger and carried him back to the grass",
        tags={"adult_help"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=1,
        text="only shouted from far away",
        fail="only shouted from far away, which was not enough to stop the trouble at the {hazard}",
        qa_text="only shouted from far away",
        tags={"bad_response"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "steady", "cautious", "thoughtful", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for marker_id, marker in MARKERS.items():
            for hazard_id, hazard in HAZARDS.items():
                if marker_warns(marker, hazard):
                    combos.append((theme_id, marker_id, hazard_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    marker: str
    hazard: str
    aid1: str
    aid2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
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
    "warning_marker": [
        (
            "What should you do if you see a warning marker and do not know what it means?",
            "Stop and ask a grown-up right away. A warning marker is there to keep people safe, so guessing is not a brave choice."
        )
    ],
    "sign": [
        (
            "What can a warning sign tell you?",
            "A warning sign can tell you to stay away from something unsafe or to be careful. Signs use words or colors to share important safety messages."
        )
    ],
    "tape": [
        (
            "Why do people put striped tape across a place?",
            "Striped tape shows that you should not go through that spot. It is a simple way to mark danger or work that is not safe to cross."
        )
    ],
    "pond": [
        (
            "Why can a pond bank be slippery?",
            "A pond bank can be slippery because the grass and mud near the water stay wet. Wet ground lets shoes slide more easily."
        )
    ],
    "thorn": [
        (
            "Why do thorny plants hurt?",
            "Thorny plants have sharp points that can poke skin and clothes. That is why it is better to walk around them than through them."
        )
    ],
    "mud": [
        (
            "Why does mud make walking hard?",
            "Mud is soft and sticky, so feet can slide or sink in it. That makes it harder to keep your balance."
        )
    ],
    "flags": [
        (
            "What can little flags be used for?",
            "Little flags can mark a safe path or show where to go. They help people follow a route without guessing."
        )
    ],
    "rope": [
        (
            "How can a rope line help someone walk safely?",
            "A rope line gives your eyes a clear path to follow. It helps you stay on the safe side instead of wandering somewhere risky."
        )
    ],
    "stones": [
        (
            "What are stepping stones for?",
            "Stepping stones make a dry path across grass or dirt. They give your feet firm places to land."
        )
    ],
    "compass": [
        (
            "What does a compass help you do?",
            "A compass helps you check direction instead of just guessing. It is a tool for finding your way."
        )
    ],
    "adult_help": [
        (
            "What should you do if a friend gets too close to danger?",
            "Call a grown-up right away and do not rush into danger yourself. Fast help from an adult is the safest plan."
        )
    ],
    "tool_help": [
        (
            "Why might a grown-up use a long tool to help someone?",
            "A long tool can reach someone without the grown-up stepping into the same danger. It gives help while keeping more distance from the risky spot."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "warning_marker",
    "sign",
    "tape",
    "pond",
    "thorn",
    "mud",
    "flags",
    "rope",
    "stones",
    "compass",
    "adult_help",
    "tool_help",
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
    theme = f["theme"]
    marker = f["marker_cfg"]
    hazard = f["hazard_cfg"]
    instigator = f["name_instigator"]
    cautioner = f["name_cautioner"]
    outcome = f["outcome"]
    base = (
        f'Write a short story for a 3-to-5-year-old where two children play {theme.role_plural}, '
        f'and one child bravely but wrongly misunderstands {marker.label} near {hazard.the}. Include the word "army".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {instigator} thinks {marker.label} is {marker.misread}, but {cautioner} explains the misunderstanding and stops the trouble before it begins.",
            f"Write a story about bravery and curiosity that ends safely because the children ask a grown-up what the marker means instead of guessing.",
        ]
    if outcome == "oopsie":
        return [
            base,
            f"Tell a cautionary story where {instigator} mistakes {marker.label} for {marker.misread}, reaches {hazard.the}, and gets into a small messy scrape before a grown-up helps.",
            f"Write a simple story where misunderstanding a warning causes a little accident, and the ending shows a safer path marked out for the children.",
        ]
    return [
        base,
        f"Tell a gentle rescue story where {instigator} misunderstands {marker.label}, heads toward {hazard.the}, and a calm grown-up helps in time.",
        f"Write a story that teaches that bravery should include stopping to ask what a warning means, and end with a new safe marching path.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    marker = f["marker_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    aid1, aid2 = f["aids"]
    pair = pair_noun(a, b, f["relation"])
    name_a = f["name_instigator"]
    name_b = f["name_cautioner"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {name_a} and {name_b}, who were pretending to be {theme.role_plural}. Their game led them toward a place they did not understand properly."
        ),
        (
            "What were the children pretending to be?",
            f"They turned the backyard into {theme.scene} and pretended to be {theme.role_plural} marching to {theme.goal}. The game made the far corner feel exciting and important."
        ),
        (
            f"What misunderstanding caused the trouble?",
            f"{name_a} thought {marker.label} meant {marker.misread}, but it really meant {marker.meaning}. That misunderstanding made danger look like part of the game."
        ),
        (
            f"Why did {name_b} warn {name_a}?",
            f"{name_b} knew the marker was a real warning and that it pointed to danger near {hazard.the}. {name_b} was trying to stop curiosity from turning into a mistake."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem solved before anything bad happened?",
                f"{name_a} listened when {name_b} spoke firmly and realized the brave choice was to stop. Then they told {pw} and waited for a safe way to reach the hideout."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did {name_a}'s {pw} help?",
                f"{pw.capitalize()} {response.qa_text.replace('{hazard}', hazard.label)}. The help came quickly enough that the scary moment ended before it turned into a real oopsie."
            )
        )
    else:
        detail = hazard.aftermath
        qa.append(
            (
                f"What happened before the grown-up could fully fix it?",
                f"{name_a} got into trouble at {hazard.the}, and {detail}. The help still came, but only after the misunderstanding had already caused a small accident."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {aid1.label} and {aid2.label} helping mark a safer route to the hideout. The final march shows that the children changed by checking and following safe signs instead of guessing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["marker_cfg"].tags) | set(f["hazard_cfg"].tags) | set(f["response"].tags)
    for aid in f["aids"]:
        tags |= set(aid.tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        name = ent.attrs.get("name", ent.id)
        lines.append(f"  {ent.id:10} ({ent.type:8}) {name}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="army_camp",
        marker="red_x",
        hazard="pond_bank",
        aid1="blue_flags",
        aid2="stepping_stones",
        response="reach_rake",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="rescue_army",
        marker="keep_out",
        hazard="thorn_patch",
        aid1="rope_line",
        aid2="toy_compass",
        response="carry_back",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=6,
        cautioner_age=8,
        relation="siblings",
    ),
    StoryParams(
        theme="garden_guard",
        marker="striped_tape",
        hazard="compost_edge",
        aid1="blue_flags",
        aid2="rope_line",
        response="grab_hand",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=1,
        instigator_age=7,
        cautioner_age=6,
        relation="friends",
    ),
    StoryParams(
        theme="army_camp",
        marker="keep_out",
        hazard="pond_bank",
        aid1="stepping_stones",
        aid2="toy_compass",
        response="carry_back",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        theme="rescue_army",
        marker="red_x",
        hazard="thorn_patch",
        aid1="rope_line",
        aid2="blue_flags",
        response="grab_hand",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="mother",
        trait="sensible",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
]


def explain_rejection(marker: Marker, hazard: Hazard) -> str:
    return (
        f"(No story: {marker.label} is not the kind of marker this world uses for {hazard.the}. "
        f"Pick a marker that plausibly warns about that danger.)"
    )


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
    return "contained" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "oopsie"


ASP_RULES = r"""
hazard(M, H) :- marker_warns(M, K), hazard_kind(H, K).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(T, M, H) :- theme(T), marker(M), hazard_obj(H), hazard(M, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), curiosity_init(CU), A > BR + CU / 2.

severity(R + D) :- chosen_hazard(H), risk(H, R), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(oopsie) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for marker_id, marker in MARKERS.items():
        lines.append(asp.fact("marker", marker_id))
        for kind in sorted(marker.warns):
            lines.append(asp.fact("marker_warns", marker_id, kind))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard_obj", hazard_id))
        lines.append(asp.fact("hazard_kind", hazard_id, hazard.kind))
        lines.append(asp.fact("risk", hazard_id, hazard.risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
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

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_resp = set(asp_sensible())
    python_resp = {r.id for r in sensible_responses()}
    if clingo_resp == python_resp:
        print(f"OK: sensible responses match ({sorted(clingo_resp)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(clingo_resp))
        print("  python:", sorted(python_resp))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
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
        if not sample.story.strip():
            raise StoryError("generated empty story during verify smoke test")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="verify smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"VERIFY smoke test failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pretend army game, bravery, curiosity, and a misunderstanding about a warning marker."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the trouble gets before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.marker and args.hazard:
        marker = MARKERS[args.marker]
        hazard = HAZARDS[args.hazard]
        if not marker_warns(marker, hazard):
            raise StoryError(explain_rejection(marker, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.marker is None or combo[1] == args.marker)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, marker, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    aid1, aid2 = rng.sample(sorted(SAFE_AIDS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        theme=theme,
        marker=marker,
        hazard=hazard,
        aid1=aid1,
        aid2=aid2,
        response=response,
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
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.marker not in MARKERS:
        raise StoryError(f"(Unknown marker: {params.marker})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.aid1 not in SAFE_AIDS or params.aid2 not in SAFE_AIDS:
        raise StoryError("(Unknown safe aid.)")
    if params.aid1 == params.aid2:
        raise StoryError("(aid1 and aid2 must be different.)")
    marker = MARKERS[params.marker]
    hazard = HAZARDS[params.hazard]
    if not marker_warns(marker, hazard):
        raise StoryError(explain_rejection(marker, hazard))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        marker=marker,
        hazard=hazard,
        aids=(SAFE_AIDS[params.aid1], SAFE_AIDS[params.aid2]),
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
    )

    story_text = world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner)
    story_text = story_text.replace(" his ", " his ").replace(" her ", " her ")

    for internal, display in [
        ("instigator", params.instigator),
        ("cautioner", params.cautioner),
        ("parent", world.facts["parent"].label_word),
    ]:
        if internal in story_text:
            raise StoryError(f"(Internal id leaked into story text: {internal})")

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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, marker, hazard) combos:\n")
        for theme, marker, hazard in combos:
            print(f"  {theme:12} {marker:12} {hazard}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.marker} near {p.hazard} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
