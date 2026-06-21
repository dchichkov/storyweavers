#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py
================================================================================================

A standalone storyworld for a small cautionary adventure domain: a child wants
to reach something high during an expedition game, invents a shaky climbing
apparatus, ignores a warning, and then either backs down, gets help in time, or
takes a tumble and learns a lesson.

This world is built around:
- the required word: "apparatus"
- inner monologue
- a cautionary turn
- a learned lesson
- an adventure-flavored style

Run it
------
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py --quest attic --apparatus crates --goal map_case
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py --goal trunk
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py --response scold
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py --all
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/apparatus_inner_monologue_lesson_learned_cautionary_adventure.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


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
    stable: bool = True
    reachable: bool = False
    supportive: bool = False
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
class Quest:
    id: str
    place: str
    opening: str
    rig: str
    destination: str
    high_spot: str
    trail_word: str
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
class Goal:
    id: str
    label: str
    phrase: str
    perch: str
    take_line: str
    ending_line: str
    height: int
    reachable: bool = False
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
class ApparatusCfg:
    id: str
    label: str
    phrase: str
    build_line: str
    wobble_line: str
    stable: bool
    power: int
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    goal = world.get("goal")
    app = world.get("apparatus")
    room = world.get("room")
    if goal.meters["climbed"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    if not app.stable:
        world.fired.add(sig)
        app.meters["tilt"] += 1
        room.meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__wobble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    app = world.get("apparatus")
    hero = world.get(world.facts["instigator_id"])
    room = world.get("room")
    if app.meters["tilt"] < THRESHOLD:
        return out
    if world.facts.get("adult_arrived", False):
        return out
    sig = ("fall",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["bump"] += 1
    hero.meters["on_floor"] += 1
    room.meters["danger"] += 1
    hero.memes["shock"] += 1
    hero.memes["fear"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


def goal_needs_height(goal: Goal) -> bool:
    return goal.height >= 2


def hazard_at_risk(apparatus: ApparatusCfg, goal: Goal) -> bool:
    return goal_needs_height(goal) and not apparatus.stable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_level(apparatus: ApparatusCfg, goal: Goal, delay: int) -> int:
    return max(0, goal.height - apparatus.power) + delay + (1 if not apparatus.stable else 0)


def is_contained(response: Response, apparatus: ApparatusCfg, goal: Goal, delay: int) -> bool:
    return response.power >= risk_level(apparatus, goal, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_tumble(world: World) -> dict:
    sim = world.copy()
    sim.get("goal").meters["climbed"] += 1
    propagate(sim, narrate=False)
    hero = sim.get(sim.facts["instigator_id"])
    return {
        "wobbles": sim.get("apparatus").meters["tilt"] >= THRESHOLD,
        "falls": hero.meters["bump"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, quest: Quest) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One bright afternoon, {a.id} and {b.id} turned {quest.place} into {quest.opening}. "
        f"{quest.rig}"
    )
    world.say(
        f'"{quest.role_solo.capitalize()} {a.id} and Scout {b.id}!" {a.id} whispered. '
        f'"The trail goes to {quest.destination}!"'
    )


def glimpse_goal(world: World, b: Entity, quest: Quest, goal: Goal) -> None:
    world.say(
        f"At the end of the trail, {goal.phrase} rested {goal.perch}, just beyond easy reach."
    )
    world.say(
        f'{b.id} stared up at {goal.label}. "It is right there," {b.pronoun()} said, '
        f"looking toward {quest.high_spot}."
    )


def tempt(world: World, a: Entity, app: ApparatusCfg) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted {app.phrase} nearby and grinned. "{app.label.capitalize()}! '
        f'That can be our apparatus."'
    )
    world.say(
        f"{a.id} thought, *If I climb fast and light, I can reach it before anyone worries.*"
    )


def warn(world: World, b: Entity, a: Entity, app: ApparatusCfg, goal: Goal, parent: Entity) -> None:
    pred = predict_tumble(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fall"] = pred["falls"]
    extra = ""
    if pred["falls"]:
        extra = " It looked like the whole thing could tip and send someone down in a thump."
    world.say(
        f'{b.id} lowered {b.pronoun("possessive")} voice. "{a.id}, {parent.label_word.capitalize()} '
        f'said not to build climbing contraptions from whatever we find. {app.label.capitalize()} '
        f'is shaky, and {goal.label} is too high."{extra}'
    )
    world.say(
        f"{b.id} thought, *An adventure is only good if everyone comes back down smiling.*"
    )


def defy(world: World, a: Entity, b: Entity, app: ApparatusCfg) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I know what I\'m doing," {a.id} said. Because {a.id} was the older one, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"I know what I\'m doing," {a.id} said, and started building anyway.')
    world.say(app.build_line)
    world.say(f"{a.id} thought, *Just one quick climb. Then everyone will see I was right.*")


def back_down(world: World, a: Entity, b: Entity, app: ApparatusCfg, parent: Entity, quest: Quest) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sib = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} put one hand on {app.label}, then looked at {b.id}. Because {b.id} was '
        f'{a.pronoun("possessive")} big {sib}, the warning landed hard this time.'
    )
    world.say(
        f'{a.id} stepped back. "No shaky apparatus today," {a.pronoun()} said. '
        f'Together they went to find {parent.label_word} instead.'
    )
    world.say(
        f"The quest did not end. It only changed course, like a good {quest.trail_word} taking a safer bend."
    )


def climb(world: World, a: Entity, goal_ent: Entity, app: ApparatusCfg, goal: Goal) -> None:
    goal_ent.meters["climbed"] += 1
    propagate(world, narrate=False)
    if world.get("apparatus").meters["tilt"] >= THRESHOLD:
        world.say(
            f"{a.id} climbed onto {app.phrase}, reaching for {goal.label}. "
            f"{app.wobble_line}"
        )
    else:
        world.say(
            f"{a.id} climbed onto {app.phrase} and stretched toward {goal.label}."
        )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    if world.get(a.id).meters["bump"] >= THRESHOLD:
        world.say(f'"{a.id}!" {b.id} cried. "{parent.label_word.capitalize()}!"')
    else:
        world.say(
            f'"Stop! It\'s wobbling!" {b.id} shouted, already calling for {parent.label_word}.'
        )


def rescue(world: World, parent: Entity, response: Response, a: Entity, goal: Goal) -> None:
    world.facts["adult_arrived"] = True
    world.get("room").meters["danger"] = 0.0
    world.get("apparatus").meters["tilt"] = 0.0
    body = response.text.replace("{goal}", goal.label)
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {body}."
    )
    if world.get(a.id).meters["bump"] >= THRESHOLD:
        world.say(
            f"{a.id} was safe, though {a.pronoun()} held still for a moment with a sore knee and a fast heart."
        )
    else:
        world.say(
            f"The scary moment passed before anyone hit the floor."
        )


def rescue_fail(world: World, parent: Entity, response: Response, a: Entity, goal: Goal) -> None:
    world.facts["adult_arrived"] = True
    body = response.fail.replace("{goal}", goal.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    if world.get(a.id).meters["bump"] < THRESHOLD:
        world.get(a.id).meters["bump"] += 1
        world.get(a.id).memes["shock"] += 1
    world.say(
        f"{a.id} landed in a heap on the dusty floor, more frightened than hurt."
    )


def comfort_and_lesson(world: World, parent: Entity, a: Entity, b: Entity, app: ApparatusCfg) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For one small moment, nobody pretended to be explorers at all.")
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "I am glad you called me," '
        f'{parent.pronoun()} said softly. "A shaky apparatus can turn an adventure into an accident in one blink."'
    )
    world.say(
        f'{a.id} looked at the floor and thought, *I wanted to be brave, but brave should not mean careless.*'
    )
    world.say(
        f'"Next time," {parent.pronoun()} said, "you ask for help before you climb." '
        f'"We will," whispered {b.id} and {a.id} together.'
    )


def sore_ending(world: World, a: Entity, b: Entity, parent: Entity, app: ApparatusCfg) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} held {a.id} close until {a.pronoun()} stopped shaking."
    )
    world.say(
        f'{a.id} thought, *I do not want another adventure to end with a bump and a scare.*'
    )
    world.say(
        f"That was the lesson both children kept: {app.label.capitalize()} was never a good ladder, "
        f"no matter how exciting the quest felt."
    )


def safe_help(world: World, parent: Entity, a: Entity, b: Entity, goal_ent: Entity, goal: Goal, quest: Quest, response: Response) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    goal_ent.meters["reached"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} showed them the right way to finish the mission: "
        f"{response.qa_text.replace('{goal}', goal.label)}."
    )
    world.say(
        goal.take_line
    )
    world.say(
        f"By the end, the {quest.role_plural} {quest.send_off}, and the new rule of the trail was clear: "
        f"real explorers use safe tools, not shaky guesses."
    )
    world.say(goal.ending_line)


def tell(
    quest: Quest,
    apparatus: ApparatusCfg,
    goal: Goal,
    response: Response,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    cautioner: str = "Lena",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label=quest.place, stable=True))
    goal_ent = world.add(Entity(
        id="goal",
        type="goal",
        label=goal.label,
        reachable=goal.reachable,
        stable=True,
    ))
    app_ent = world.add(Entity(
        id="apparatus",
        type="apparatus",
        label=apparatus.label,
        stable=apparatus.stable,
        supportive=True,
    ))
    world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator")) if False else None

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    a.meters["bump"] = 0.0
    a.meters["on_floor"] = 0.0
    goal_ent.meters["climbed"] = 0.0
    goal_ent.meters["reached"] = 0.0
    app_ent.meters["tilt"] = 0.0
    world.get("room").meters["danger"] = 0.0

    world.facts["instigator_id"] = a.id
    world.facts["adult_arrived"] = False
    world.facts["pet"] = pet
    world.facts["relation"] = relation

    play_setup(world, a, b, quest)
    glimpse_goal(world, b, quest, goal)

    world.para()
    tempt(world, a, apparatus)
    warn(world, b, a, apparatus, goal, parent)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, apparatus, parent, quest)
        world.para()
        safe_help(world, parent, a, b, goal_ent, goal, quest, response)
        contained = True
        severity = 0
    else:
        defy(world, a, b, apparatus)
        world.para()
        climb(world, a, goal_ent, apparatus, goal)
        propagate(world, narrate=False)
        alarm(world, b, a, parent)
        severity = risk_level(apparatus, goal, delay)
        goal_ent.meters["severity"] = float(severity)
        contained = is_contained(response, apparatus, goal, delay)

        world.para()
        if contained:
            rescue(world, parent, response, a, goal)
            comfort_and_lesson(world, parent, a, b, apparatus)
            world.para()
            safe_help(world, parent, a, b, goal_ent, goal, quest, response)
        else:
            rescue_fail(world, parent, response, a, goal)
            sore_ending(world, a, b, parent, apparatus)
            world.para()
            world.say(
                f"Later, {goal.take_line[0].lower() + goal.take_line[1:]}"
            )
            world.say(
                f"When the children looked up again, the high place no longer seemed daring. It simply looked too high for guessing."
            )

    outcome = "averted" if averted else ("contained" if contained else "bumped")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        quest=quest,
        goal_cfg=goal,
        goal=goal_ent,
        apparatus_cfg=apparatus,
        apparatus=app_ent,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        reached=goal_ent.meters["reached"] >= THRESHOLD,
        bumped=a.meters["bump"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "attic": Quest(
        id="attic",
        place="the attic",
        opening="a forgotten watchtower above the house",
        rig="An old blanket became a cliff, a cardboard tube became a spyglass, and a dusty trunk marked the edge of the map.",
        destination="the secret beam above the rafters",
        high_spot="the high beam",
        trail_word="trail",
        role_solo="explorer",
        role_plural="explorers",
        send_off="finished their expedition with steadier feet",
    ),
    "barn": Quest(
        id="barn",
        place="the barn loft",
        opening="a mountain fort full of secret paths",
        rig="A hay bale became a ridge, a length of string became a trail line, and a wooden crate marked the hidden pass.",
        destination="the loft ledge near the rafters",
        high_spot="the loft edge",
        trail_word="trail",
        role_solo="explorer",
        role_plural="explorers",
        send_off="completed their barn expedition the safe way",
    ),
    "shed": Quest(
        id="shed",
        place="the garden shed",
        opening="a tiny jungle outpost packed with mysteries",
        rig="A broom became a flagpole, a seed box became treasure, and a coil of rope marked the path to camp.",
        destination="the top shelf in the dim corner",
        high_spot="the top shelf",
        trail_word="path",
        role_solo="explorer",
        role_plural="explorers",
        send_off="carried their prize home like careful adventurers",
    ),
}

GOALS = {
    "map_case": Goal(
        id="map_case",
        label="the map case",
        phrase="a red map case",
        perch="on a high beam",
        take_line="At last, the map case came down safely into waiting hands.",
        ending_line="Its paper map crackled open like a tiny promise of future trails.",
        height=3,
        tags={"map", "high_place"},
    ),
    "compass_box": Goal(
        id="compass_box",
        label="the compass box",
        phrase="a brass compass box",
        perch="on the highest shelf",
        take_line="Soon the compass box was safely lowered instead of snatched.",
        ending_line="When they opened it, the little needle trembled and then pointed north, calm and sure.",
        height=2,
        tags={"compass", "high_place"},
    ),
    "lantern": Goal(
        id="lantern",
        label="the little lantern",
        phrase="a little lantern",
        perch="from a peg above their heads",
        take_line="A moment later, the little lantern was lifted down the safe way.",
        ending_line="Its glass winked in the light, as if even it liked careful hands better.",
        height=2,
        tags={"lantern", "high_place"},
    ),
    "trunk": Goal(
        id="trunk",
        label="the old trunk",
        phrase="an old trunk",
        perch="on the floor under the window",
        take_line="The old trunk had never needed climbing at all; it only needed patient hands and a clear look.",
        ending_line="Inside, they found only scarves and postcards, but the real treasure was the better choice they had made.",
        height=0,
        tags={"trunk"},
    ),
}

APPARATUS = {
    "crates": ApparatusCfg(
        id="crates",
        label="stacked crates",
        phrase="two stacked crates",
        build_line="In a minute, the crates were one on top of the other beside the wall.",
        wobble_line="The stack gave a sharp little wobble under his foot.",
        stable=False,
        power=1,
        tags={"crates", "climb"},
    ),
    "stool": ApparatusCfg(
        id="stool",
        label="a wobbly stool",
        phrase="a wobbly stool",
        build_line="The stool scraped across the boards and waited under the beam.",
        wobble_line="One leg skidded sideways with a nasty scrape.",
        stable=False,
        power=1,
        tags={"stool", "climb"},
    ),
    "bucket": ApparatusCfg(
        id="bucket",
        label="an upside-down bucket",
        phrase="an upside-down bucket",
        build_line="The bucket was flipped over and pushed into place like a tiny stage.",
        wobble_line="The bucket rolled just enough to make the whole plan feel wrong.",
        stable=False,
        power=1,
        tags={"bucket", "climb"},
    ),
    "step_ladder": ApparatusCfg(
        id="step_ladder",
        label="a small step ladder",
        phrase="a small step ladder",
        build_line="The step ladder opened with a neat click under the shelf.",
        wobble_line="It hardly moved at all.",
        stable=True,
        power=3,
        tags={"ladder", "climb"},
    ),
}

RESPONSES = {
    "steady_ladder": Response(
        id="steady_ladder",
        sense=3,
        power=4,
        text="moved the shaky apparatus away, opened a real step ladder, and kept one hand steady while the prize was reached",
        fail="tried to steady the mess, but the climb had already gone wrong before there was room to help",
        qa_text="used a real step ladder and steady hands to reach {goal}",
        tags={"ladder", "help"},
    ),
    "lift_child": Response(
        id="lift_child",
        sense=2,
        power=3,
        text="lifted the child down first and then fetched a proper reaching tool for the job",
        fail="reached for the child, but the tumble had already happened",
        qa_text="lifted the child down and then used the right tool to get {goal}",
        tags={"help", "adult"},
    ),
    "scold": Response(
        id="scold",
        sense=1,
        power=0,
        text="only shouted from across the room",
        fail="only shouted from across the room, which did not stop the wobble at all",
        qa_text="shouted instead of helping",
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "curious", "thoughtful", "sensible", "clever"]
PETS = ["the cat", "the puppy", "their little dog", "the kitten"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for app_id, app in APPARATUS.items():
            for goal_id, goal in GOALS.items():
                if hazard_at_risk(app, goal):
                    combos.append((theme_id, app_id, goal_id))
    return combos


@dataclass
class StoryParams:
    quest: str
    apparatus: str
    goal: str
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
    pet: str = ""
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
    "ladder": [(
        "Why is a real ladder safer than a shaky pile of things?",
        "A real ladder is made for climbing and standing still under your feet. A shaky pile can slide or tip when you put your weight on it."
    )],
    "help": [(
        "Why should children ask a grown-up for help with something high up?",
        "A grown-up can bring the right tool and keep the job steady. Asking early can stop a scary accident before it starts."
    )],
    "high_place": [(
        "Why are high places risky to climb without the right tool?",
        "If you reach too far or stand on something unstable, you can lose your balance. Even a short fall can hurt and make you very frightened."
    )],
    "map": [(
        "What is a map for?",
        "A map helps you find where to go and shows the path from one place to another. Explorers use maps to make a trip feel less confusing."
    )],
    "compass": [(
        "What does a compass do?",
        "A compass points north, which helps travelers know which way they are facing. It is a small tool for finding direction."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light you can carry with you. It helps you see in dim places."
    )],
    "crates": [(
        "Why are stacked crates not a good climbing tool?",
        "Crates can wobble, slide, or tip when someone climbs on them. They are for holding things, not for being a ladder."
    )],
    "stool": [(
        "Why can a wobbly stool be dangerous?",
        "If one leg moves or the stool rocks, your body can tilt too. Then it is easy to slip and fall."
    )],
    "bucket": [(
        "Why is an upside-down bucket a poor step to stand on?",
        "A bucket is round and light, so it can roll or flip. That makes it a bad thing to climb on."
    )],
}
KNOWLEDGE_ORDER = ["high_place", "help", "ladder", "map", "compass", "lantern", "crates", "stool", "bucket"]


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
    quest = f["quest"]
    app = f["apparatus_cfg"]
    goal = f["goal_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "apparatus", '
        f'an inner monologue, and a cautionary lesson. Two children are exploring {quest.place} '
        f'and one child tries to reach {goal.label} using {app.label}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle adventure where {a.id} wants to use {app.label} as an apparatus, but {b.id} warns {a.pronoun('object')} in time and they ask a grown-up for help instead.",
            f"Write a child-facing cautionary story with inner thoughts where the adventure stays exciting, but the children learn that safe tools matter more than bold guesses.",
        ]
    if outcome == "bumped":
        return [
            base,
            f"Tell a cautionary adventure where {a.id} ignores the warning, the shaky apparatus tips, and the child gets a bump and a scare before learning a lesson.",
            f"Write a story with inner monologue where bravery is confused with risk at first, then corrected by the ending image and a clear learned lesson.",
        ]
    return [
        base,
        f"Tell a gentle cautionary adventure where {a.id} ignores the warning, the apparatus wobbles, and a grown-up arrives quickly with the right tool.",
        f"Write a short story with inner monologue and a lesson learned: a child wants to be brave, but discovers real explorers ask for help and use safe equipment.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    quest = f["quest"]
    goal = f["goal_cfg"]
    app = f["apparatus_cfg"]
    response = f["response"]
    pair = pair_noun(a, b, f.get("relation", "friends"))
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who turned {quest.place} into an adventure. {a.id}'s {pw} also helped when the climb became risky."
        ),
        (
            "What were they trying to do?",
            f"They wanted to reach {goal.label} in a high place as part of their expedition game. The object looked like treasure at the end of the trail, which made the climb feel exciting."
        ),
        (
            f"What apparatus did {a.id} want to use, and why was it a bad idea?",
            f"{a.id} wanted to use {app.label} as a climbing apparatus. It was a bad idea because it was shaky, and the goal was too high to reach safely that way."
        ),
        (
            f"What did {b.id} warn {a.id} about?",
            f"{b.id} warned that the apparatus could wobble and make someone fall. {b.id} could already imagine the danger, so the warning came before the real scare."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append((
            f"What changed {a.id}'s mind?",
            f"{a.id} listened to {b.id}'s warning and stepped back before climbing. Asking for help let the adventure continue without turning into an accident."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a grown-up helping them reach {goal.label} safely. The ending shows that careful explorers can still finish the mission."
        ))
    elif outcome == "contained":
        qa.append((
            f"What happened when {a.id} climbed?",
            f"The apparatus wobbled and the moment turned scary, but {pw} came quickly to help. The right response stopped the danger before the fall became worse."
        ))
        qa.append((
            f"What lesson did {a.id} learn?",
            f"{a.id} learned that being brave does not mean climbing whatever is nearby. Real bravery meant calling for help and using a proper tool."
        ))
        qa.append((
            "How did the ending prove that something changed?",
            f"They still finished the adventure, but this time they used a safe method to reach {goal.label}. The final image of the prize coming down carefully shows the lesson had stuck."
        ))
    else:
        qa.append((
            f"What happened when the apparatus tipped?",
            f"{a.id} fell and got a bump and a scare. The fall happened because the shaky apparatus could not hold steady under the climb."
        ))
        qa.append((
            f"Was {a.id} badly hurt?",
            f"No, {a.id} was more frightened than badly hurt. Even so, the bump was enough to teach that unsafe climbing is not a game."
        ))
        qa.append((
            "What lesson did the children keep afterward?",
            f"They learned that exciting quests do not make bad tools safe. Next time, they would ask a grown-up before trying to reach something high."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["goal_cfg"].tags) | set(f["apparatus_cfg"].tags)
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
        if not e.stable:
            bits.append("stable=False")
        if e.reachable:
            bits.append("reachable=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="attic",
        apparatus="crates",
        goal="map_case",
        response="steady_ladder",
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
        pet="the kitten",
    ),
    StoryParams(
        quest="barn",
        apparatus="bucket",
        goal="compass_box",
        response="lift_child",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
        pet="",
    ),
    StoryParams(
        quest="shed",
        apparatus="stool",
        goal="lantern",
        response="lift_child",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=3,
        pet="the cat",
    ),
    StoryParams(
        quest="attic",
        apparatus="crates",
        goal="map_case",
        response="lift_child",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="clever",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
        pet="their little dog",
    ),
]


def explain_rejection(apparatus: ApparatusCfg, goal: Goal) -> str:
    if goal.height < 2:
        return (
            f"(No story: {goal.label} is not high enough to need a risky climb, so there is no honest cautionary turn. "
            f"Pick a goal on a shelf or beam.)"
        )
    if apparatus.stable:
        return (
            f"(No story: {apparatus.label} is already stable enough that this world has no shaky-apparatus accident to warn about. "
            f"Pick crates, a stool, or a bucket.)"
        )
    return "(No story: this combination has no unsafe height problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a more helpful grown-up action such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], APPARATUS[params.apparatus], GOALS[params.goal], params.delay)
    return "contained" if contained else "bumped"


ASP_RULES = r"""
hazard(A, G) :- unstable(A), high_goal(G).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Q, A, G) :- quest(Q), apparatus(A), goal(G), hazard(A, G).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

risk_level((H - P) + D + 1) :- chosen_goal(G), height(G, H), chosen_apparatus(A), app_power(A, P), H > P, delay(D), unstable(A).
risk_level(D + 1) :- chosen_goal(G), height(G, H), chosen_apparatus(A), app_power(A, P), H <= P, delay(D), unstable(A).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), risk_level(RL), P >= RL.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bumped) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in THEMES:
        lines.append(asp.fact("quest", qid))
    for aid, a in APPARATUS.items():
        lines.append(asp.fact("apparatus", aid))
        lines.append(asp.fact("app_power", aid, a.power))
        if not a.stable:
            lines.append(asp.fact("unstable", aid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("height", gid, g.height))
        if goal_needs_height(g):
            lines.append(asp.fact("high_goal", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
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

    scenario = "\n".join([
        asp.fact("chosen_goal", params.goal),
        asp.fact("chosen_apparatus", params.apparatus),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - python_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child builds a shaky apparatus during an adventure and learns a safer way."
    )
    ap.add_argument("--quest", choices=THEMES)
    ap.add_argument("--apparatus", choices=APPARATUS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to arrive")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and GOALS[args.goal].height < 2:
        app = APPARATUS[args.apparatus] if args.apparatus else next(iter(APPARATUS.values()))
        raise StoryError(explain_rejection(app, GOALS[args.goal]))
    if args.apparatus and APPARATUS[args.apparatus].stable:
        goal = GOALS[args.goal] if args.goal else next(g for g in GOALS.values() if g.height >= 2)
        raise StoryError(explain_rejection(APPARATUS[args.apparatus], goal))
    if args.apparatus and args.goal:
        app = APPARATUS[args.apparatus]
        goal = GOALS[args.goal]
        if not hazard_at_risk(app, goal):
            raise StoryError(explain_rejection(app, goal))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.apparatus is None or c[1] == args.apparatus)
        and (args.goal is None or c[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, apparatus, goal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        quest=quest,
        apparatus=apparatus,
        goal=goal,
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
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in THEMES:
        raise StoryError(f"Unknown quest: {params.quest}")
    if params.apparatus not in APPARATUS:
        raise StoryError(f"Unknown apparatus: {params.apparatus}")
    if params.goal not in GOALS:
        raise StoryError(f"Unknown goal: {params.goal}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if not hazard_at_risk(APPARATUS[params.apparatus], GOALS[params.goal]):
        raise StoryError(explain_rejection(APPARATUS[params.apparatus], GOALS[params.goal]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        quest=THEMES[params.quest],
        apparatus=APPARATUS[params.apparatus],
        goal=GOALS[params.goal],
        response=RESPONSES[params.response],
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
        pet=params.pet,
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
        print(f"{len(combos)} compatible (quest, apparatus, goal) combos:\n")
        for quest, apparatus, goal in combos:
            print(f"  {quest:8} {apparatus:12} {goal}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.apparatus} for {p.goal} ({p.quest}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
