#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py
============================================================================

A standalone story world for a suspenseful pirate-tale domain: two children at a
little dockside pirate class want one last lesson card from the wall curriculum.
The card hangs too high. One child mistakes *pluck* for grabbing an old pirate
pistol from a display rack and using it to poke the card down. The other child
warns that real pluck means choosing the safe way and asking for help.

The world model tracks height, wobble, falling danger, fear, relief, and the
lesson learned. The prose is driven by the simulated state: when the child
defies the warning, the stool wobbles, the pistol slips, and a grown-up uses a
sensible reaching tool. In some variants, an older sibling's warning averts the
incident entirely.

Run it
------
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py --goal map_card
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py --response crate_stack
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pluck_pistol_curriculum_suspense_pirate_tale.py --verify
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}


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
    heavy: bool = False
    hanging: bool = False
    breakable: bool = False
    long_reach: bool = False
    stabilizes: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    mood: str
    water_sound: str
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
class LessonGoal:
    id: str
    label: str
    the: str
    phrase: str
    use_text: str
    hang_text: str
    fragile: bool
    height: int
    suspense: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Pistol:
    id: str
    label: str
    phrase: str
    place_text: str
    warning: str
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
class SafeResponse:
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    climber = world.entities.get("stool")
    tool = world.entities.get("tool")
    goal = world.entities.get("goal")
    if climber is None or tool is None or goal is None:
        return out
    if climber.meters["climbed"] < THRESHOLD:
        return out
    if not tool.heavy:
        return out
    sig = ("wobble", climber.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    climber.meters["wobble"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    stool = world.entities.get("stool")
    tool = world.entities.get("tool")
    if stool is None or tool is None:
        return out
    if stool.meters["wobble"] < THRESHOLD or tool.meters["used"] < THRESHOLD:
        return out
    sig = ("drop", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["falling"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__drop__")
    return out


def _r_goal_fall(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    goal = world.entities.get("goal")
    if tool is None or goal is None:
        return out
    if tool.meters["falling"] < THRESHOLD or goal.meters["reached_for"] < THRESHOLD:
        return out
    sig = ("goal_fall", goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["falling"] += 1
    world.get("room").meters["danger"] += 1
    if goal.breakable:
        goal.meters["cracked"] += 1
    out.append("__goal_fall__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
    Rule(name="goal_fall", tag="physical", apply=_r_goal_fall),
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


def goal_at_risk(goal: LessonGoal) -> bool:
    return goal.height >= 2


def sensible_responses() -> list[SafeResponse]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def instability(goal: LessonGoal, delay: int) -> int:
    return goal.height + delay + (1 if goal.fragile else 0)


def is_recovered(response: SafeResponse, goal: LessonGoal, delay: int) -> bool:
    return response.power >= instability(goal, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > BOLDNESS_INIT


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    use_pistol(sim, narrate=False)
    return {
        "wobble": sim.get("stool").meters["wobble"] >= THRESHOLD,
        "goal_falls": sim.get("goal").meters["falling"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, setting: Setting, goal: LessonGoal) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch at {setting.place}, {a.id} and {b.id} hurried into a little pirate lesson room. "
        f"The day's curriculum hung on a rope board by the wall: first knots, then maps, then songs, "
        f"and at the bottom a space for {goal.the}."
    )
    world.say(
        f"Outside, {setting.water_sound}, and inside the room felt {setting.mood}. "
        f'"If we fetch {goal.the}, we can finish the whole pirate day," {a.id} whispered.'
    )


def reveal_problem(world: World, b: Entity, goal: LessonGoal) -> None:
    world.say(
        f"But {goal.the} was {goal.hang_text}. It looked easy to see and hard to reach."
    )
    world.say(
        f'{b.id} stood on tiptoe. "We need it for {goal.use_text}," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, pistol: Pistol) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'Then {a.id} spotted {pistol.phrase} {pistol.place_text}. "{pistol.label.capitalize()}!" '
        f'{a.pronoun().capitalize()} breathed. "I can use it to poke the lesson down."'
    )
    world.say("For one tight little moment, the idea sounded daring enough to work.")


def warn(world: World, b: Entity, a: Entity, pistol: Pistol, goal: LessonGoal, parent: Entity) -> None:
    pred = predict_mishap(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["goal_falls"] and goal.fragile:
        extra = f" If it falls, {goal.the} could crack."
    world.say(
        f'{b.id} caught {a.id} by the sleeve. "{a.id}, no. {pistol.warning}. '
        f'The stool could wobble, and {goal.the} could come crashing down.{extra}"'
    )
    world.say(
        f'"Real pluck is not grabbing the pistol," {b.id} added. '
        f'"Real pluck is calling {parent.label_word} and choosing the safe way."'
    )


def defy(world: World, a: Entity, b: Entity, pistol: Pistol) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"We will be quick," {a.id} said. Because {a.pronoun()} was the older sibling, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Just one reach," {a.id} said, and moved before {b.id} could answer.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, goal: LessonGoal) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked up at {goal.the}, then at the old pistol, and swallowed. '
        f'"You are right," {a.pronoun()} said at last. "That is not pluck."'
    )
    world.say(
        f"They stepped away from the stool and went to find {parent.label_word}. "
        f"The suspense in the room untied itself like a loosened knot."
    )


def use_pistol(world: World, narrate: bool = True) -> None:
    stool = world.get("stool")
    tool = world.get("tool")
    goal = world.get("goal")
    stool.meters["climbed"] += 1
    tool.meters["used"] += 1
    goal.meters["reached_for"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{world.facts['instigator'].id} dragged over the stool, climbed up, and lifted the pistol toward "
            f"{world.facts['goal_cfg'].the}. The room seemed to hold its breath."
        )
        if stool.meters["wobble"] >= THRESHOLD:
            world.say(
                "The stool gave a soft, ugly squeak. One leg skidded. The pistol slipped sideways with a hard little clack."
            )
        if goal.meters["falling"] >= THRESHOLD:
            if goal.breakable:
                world.say(
                    f"{goal.The} jerked loose and tipped through the air. For a heartbeat it looked as if it might smash on the floor."
                )
            else:
                world.say(
                    f"{goal.The} jerked loose and swung down too fast, making both children gasp."
                )


def alarm(world: World, b: Entity, parent: Entity, goal: LessonGoal) -> None:
    if world.get("goal").meters["falling"] >= THRESHOLD:
        world.say(f'"{parent.label_word.upper()}! {goal.The} is falling!" {b.id} cried.')
    else:
        world.say(f'"{parent.label_word.upper()}! The stool is slipping!" {b.id} cried.')


def rescue(world: World, parent: Entity, response: SafeResponse, goal: LessonGoal) -> None:
    world.get("room").meters["danger"] = 0.0
    world.get("stool").meters["wobble"] = 0.0
    world.get("goal").meters["falling"] = 0.0
    world.get("tool").meters["falling"] = 0.0
    body = response.text.replace("{goal}", goal.label)
    world.say(
        f"{parent.label_word.capitalize()} came at once and {body}."
    )
    if goal.fragile:
        world.say(
            f"{goal.The} landed safely in {parent.pronoun('possessive')} hand instead of breaking, and the whole room let out its breath."
        )
    else:
        world.say(
            f"{goal.The} was safe, and the frightened hush in the room melted away."
        )


def rescue_fail(world: World, parent: Entity, response: SafeResponse, goal: LessonGoal) -> None:
    world.get("room").meters["danger"] += 1
    world.get("goal").meters["falling"] += 1
    if goal.fragile:
        world.get("goal").meters["cracked"] += 1
    body = response.fail.replace("{goal}", goal.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    if goal.fragile:
        world.say(
            f"{goal.The} hit the floor with a sad crack, and the pirate room went still."
        )
    else:
        world.say(
            f"{goal.The} thumped down hard enough to make both children jump."
        )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, pistol: Pistol, goal: LessonGoal) -> None:
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say("For a few seconds, nobody said anything at all.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt beside the stool. '
        f'"I am glad you called me," {parent.pronoun()} said softly. '
        f'"That old pirate pistol is for display, not for hands, and pluck does not mean taking a foolish risk. '
        f'Pluck means stopping, thinking, and asking for help before someone gets hurt or {goal.the} gets broken."'
    )
    world.say(f'"We understand," {a.id} and {b.id} said together.')


def sad_lesson(world: World, parent: Entity, a: Entity, b: Entity, pistol: Pistol, goal: LessonGoal) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} put an arm around both children. '
        f'"I am thankful you are safe," {parent.pronoun()} said. '
        f'"But remember this: that old pirate pistol is not for play, and hurry is not the same as pluck."'
    )
    if goal.fragile:
        world.say(
            f"They looked at the cracked {goal.label} and knew the lesson would have to be copied again before the class could finish."
        )
    else:
        world.say(
            f"They looked at {goal.the} on the floor and knew the lesson had turned rough because they had chosen the wrong tool."
        )


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, goal: LessonGoal, response: SafeResponse) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f'When the room felt steady again, {parent.label_word} lowered {goal.the} properly and smoothed the curling edge. '
        f'"Now," {parent.pronoun()} smiled, "let us finish the curriculum the calm way."'
    )
    world.say(
        f"{a.id} held one corner and {b.id} held the other while {parent.label_word} read the last pirate task aloud."
    )
    world.say(
        f"Soon they were using {goal.the} for {goal.use_text}, and the brave part of the day felt bright again. "
        f"The old pistol stayed on its hook, untouched."
    )


def quiet_end(world: World, parent: Entity, goal: LessonGoal) -> None:
    world.say(
        f"Later, while the tide tapped outside, {parent.label_word} pinned up a fresh copy of {goal.the}."
    )
    world.say(
        "The children watched in silence, then helped straighten the rope board. After that, whenever a pirate lesson looked hard to reach, they asked first."
    )


def tell(
    setting: Setting,
    pistol: Pistol,
    goal: LessonGoal,
    response: SafeResponse,
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
) -> World:
    world = World(setting)
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
        label="the teacher",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    room.meters["danger"] = 0.0
    tool = world.add(Entity(id="tool", type="tool", label=pistol.label, heavy=True))
    tool.meters["used"] = 0.0
    tool.meters["falling"] = 0.0
    goal_ent = world.add(Entity(
        id="goal",
        type="goal",
        label=goal.label,
        hanging=True,
        breakable=goal.fragile,
    ))
    goal_ent.meters["reached_for"] = 0.0
    goal_ent.meters["falling"] = 0.0
    goal_ent.meters["cracked"] = 0.0
    stool = world.add(Entity(id="stool", type="stool", label="the stool"))
    stool.meters["climbed"] = 0.0
    stool.meters["wobble"] = 0.0

    a.memes["boldness"] = BOLDNESS_INIT
    a.memes["defiance"] = 0.0
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] = 0.0
        kid.memes["lesson"] = 0.0

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        setting=setting,
        pistol=pistol,
        goal_cfg=goal,
        response=response,
        relation=relation,
    )

    play_setup(world, a, b, setting, goal)
    reveal_problem(world, b, goal)

    world.para()
    tempt(world, a, pistol)
    warn(world, b, a, pistol, goal, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent, goal)
        world.para()
        rescue(world, parent, response, goal)
        lesson(world, parent, a, b, pistol, goal)
        world.para()
        safe_finish(world, parent, a, b, goal, response)
        severity, recovered = 0, True
    else:
        defy(world, a, b, pistol)
        world.para()
        use_pistol(world, narrate=True)
        alarm(world, b, parent, goal)
        severity = instability(goal, delay)
        recovered = is_recovered(response, goal, delay)

        world.para()
        if recovered:
            rescue(world, parent, response, goal)
            lesson(world, parent, a, b, pistol, goal)
            world.para()
            safe_finish(world, parent, a, b, goal, response)
        else:
            rescue_fail(world, parent, response, goal)
            sad_lesson(world, parent, a, b, pistol, goal)
            world.para()
            quiet_end(world, parent, goal)

    outcome = "averted" if averted else ("recovered" if recovered else "broken")
    world.facts.update(
        outcome=outcome,
        severity=severity,
        delay=delay,
        reached=goal_ent.meters["reached_for"] >= THRESHOLD,
        goal_fell=goal_ent.meters["falling"] >= THRESHOLD or goal_ent.meters["cracked"] >= THRESHOLD,
        cracked=goal_ent.meters["cracked"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "harbor_room": Setting(
        id="harbor_room",
        place="the little harbor room",
        mood="hushed and briny",
        water_sound="the tide tapped the pilings",
        tags={"harbor", "pirate"},
    ),
    "captain_loft": Setting(
        id="captain_loft",
        place="the captain's loft above the dock",
        mood="shadowy and exciting",
        water_sound="ropes knocked softly against the mast outside",
        tags={"loft", "pirate"},
    ),
    "chart_cabin": Setting(
        id="chart_cabin",
        place="the chart cabin by the pier",
        mood="close and mysterious",
        water_sound="the waves whispered under the boards",
        tags={"cabin", "pirate"},
    ),
}

GOALS = {
    "map_card": LessonGoal(
        id="map_card",
        label="map card",
        the="the map card",
        phrase="a rolled map card",
        use_text="the treasure-reading lesson",
        hang_text="tied high on the rope board",
        fragile=False,
        height=2,
        suspense="it swung just beyond small fingers",
        tags={"map", "curriculum"},
    ),
    "star_chart": LessonGoal(
        id="star_chart",
        label="star chart",
        the="the star chart",
        phrase="the shiny star chart",
        use_text="the night-sky lesson",
        hang_text="pinned above the tallest hook",
        fragile=True,
        height=3,
        suspense="its thin frame looked ready to slip",
        tags={"stars", "curriculum"},
    ),
    "compass_slate": LessonGoal(
        id="compass_slate",
        label="compass slate",
        the="the compass slate",
        phrase="the chalk compass slate",
        use_text="the steering lesson",
        hang_text="balanced on the upper shelf behind a coil of rope",
        fragile=True,
        height=3,
        suspense="one wrong bump might send it down",
        tags={"compass", "curriculum"},
    ),
    "song_shell": LessonGoal(
        id="song_shell",
        label="song shell",
        the="the song shell",
        phrase="the shell used for singing turns",
        use_text="the sea-song lesson",
        hang_text="looped over a peg near the ceiling",
        fragile=False,
        height=2,
        suspense="it trembled a little whenever the room shook",
        tags={"song", "curriculum"},
    ),
}

PISTOLS = {
    "flintlock": Pistol(
        id="flintlock",
        label="flintlock pistol",
        phrase="an old flintlock pistol",
        place_text="on a wooden wall hook",
        warning="That old flintlock pistol is not for children",
        tags={"pistol", "display"},
    ),
    "brass_pistol": Pistol(
        id="brass_pistol",
        label="brass-handled pistol",
        phrase="a brass-handled pistol",
        place_text="above the costume chest",
        warning="That brass-handled pistol is only for looking",
        tags={"pistol", "display"},
    ),
    "captain_pistol": Pistol(
        id="captain_pistol",
        label="captain's pistol",
        phrase="the captain's pistol",
        place_text="beside the captain's hat",
        warning="The captain's pistol stays on its peg",
        tags={"pistol", "display"},
    ),
}

RESPONSES = {
    "boat_hook": SafeResponse(
        id="boat_hook",
        sense=3,
        power=4,
        text="took down the long boat hook, steadied the stool with one hand, and lowered the {goal} safely",
        fail="caught at the {goal} with the boat hook, but it had already tipped too far",
        qa_text="used the long boat hook to lower the lesson safely",
        tags={"boat_hook", "help"},
    ),
    "step_ladder": SafeResponse(
        id="step_ladder",
        sense=3,
        power=4,
        text="opened the step ladder, climbed carefully, and brought down the {goal} the right way",
        fail="got the step ladder under the shelf, but the {goal} fell before it could be reached",
        qa_text="used a step ladder to bring the lesson down carefully",
        tags={"ladder", "help"},
    ),
    "reach_claw": SafeResponse(
        id="reach_claw",
        sense=2,
        power=3,
        text="fetched the reaching claw from the cupboard and gripped the {goal} before it could drop",
        fail="snapped the reaching claw at the {goal}, but only brushed it as it fell",
        qa_text="used a reaching claw to catch the lesson",
        tags={"reacher", "help"},
    ),
    "crate_stack": SafeResponse(
        id="crate_stack",
        sense=1,
        power=2,
        text="stacked two fish crates and tried to lean over for the {goal}",
        fail="stacked two fish crates, but they shifted and the {goal} slipped past",
        qa_text="stacked fish crates to reach the lesson",
        tags={"crates"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Rose", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn", "Sam", "Eli", "Theo"]
TRAITS = ["careful", "steady", "sensible", "watchful", "curious", "eager"]

KNOWLEDGE = {
    "pistol": [(
        "What is a pistol?",
        "A pistol is a kind of gun. Real pistols are dangerous, so children should never touch one and should tell a grown-up right away."
    )],
    "display": [(
        "What does it mean when something is only for display?",
        "It means the object is there to be looked at, not handled. Display things can be old, fragile, or unsafe."
    )],
    "curriculum": [(
        "What is a curriculum?",
        "A curriculum is a plan of what you are going to learn. It can be a list of lessons or activities in order."
    )],
    "boat_hook": [(
        "What is a boat hook?",
        "A boat hook is a long pole with a hook on the end. Grown-ups can use it to reach or pull things safely from far away."
    )],
    "ladder": [(
        "Why is a step ladder safer than standing on a wobbly stool?",
        "A step ladder is made for climbing and standing. It is steadier than a stool, so it is less likely to tip."
    )],
    "reacher": [(
        "What is a reaching claw?",
        "A reaching claw is a long tool with a grippy end. It helps someone pick up or pull down something without stretching too far."
    )],
    "help": [(
        "When is asking for help brave?",
        "Asking for help is brave when something is too high, too heavy, or unsafe to handle alone. Real pluck means choosing safety over showing off."
    )],
    "map": [(
        "What is a map used for?",
        "A map helps you see where places are and which way to go. In a pirate game, it can help the crew pretend to find treasure."
    )],
    "stars": [(
        "Why do sailors look at star charts?",
        "Star charts help sailors notice patterns in the night sky. Those patterns can help them know direction."
    )],
    "compass": [(
        "What does a compass tell you?",
        "A compass helps show direction, like north and south. It helps travelers know which way they are going."
    )],
    "song": [(
        "Why do crews sing work songs?",
        "Singing together can help a crew keep the same rhythm. It also makes hard work feel less lonely."
    )],
}
KNOWLEDGE_ORDER = ["pistol", "display", "curriculum", "boat_hook", "ladder", "reacher", "help", "map", "stars", "compass", "song"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for pid in PISTOLS:
            for gid, goal in GOALS.items():
                if goal_at_risk(goal):
                    combos.append((sid, pid, gid))
    return combos


@dataclass
class StoryParams:
    setting: str
    pistol: str
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
    goal = f["goal_cfg"]
    pistol = f["pistol"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a suspenseful pirate tale for a 3-to-5-year-old that includes the words "pluck", '
        f'"pistol", and "curriculum". Set it in {setting.place} and center the danger around {goal.the}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a pirate-school story where {a.id} is tempted to grab {pistol.phrase}, but {b.id} explains that real pluck means asking for help.",
            f"Write a gentle near-miss story with suspense in which the children step away from danger and still finish the curriculum safely.",
        ]
    if outcome == "broken":
        return [
            base,
            f"Tell a cautionary pirate tale where {a.id} uses {pistol.phrase} to reach {goal.the}, but the wrong choice leads to a sad break and a strong lesson.",
            "Write a suspenseful but child-safe story where a scary moment proves that hurry is not the same as pluck.",
        ]
    return [
        base,
        f"Tell a suspenseful pirate classroom story where {a.id} ignores {b.id}'s warning, a dangerous wobble begins, and a calm grown-up uses the right tool.",
        "Write a story that turns fear into a lesson: pluck means choosing the safe way, not showing off with the wrong object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    goal = f["goal_cfg"]
    pistol = f["pistol"]
    response = f["response"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, in a little pirate class with their {parent.label_word}. "
            f"They were trying to finish the day's curriculum."
        ),
        (
            "What problem did the children have?",
            f"{goal.The} was too high to reach, but they needed it for {goal.use_text}. "
            f"That is what made the dangerous shortcut feel tempting."
        ),
        (
            f"Why did {b.id} tell {a.id} not to touch the pistol?",
            f"{b.id} knew the old pistol was not for children and that using it from the stool could make the room unsafe. "
            f"{b.pronoun().capitalize()} also understood that {goal.the} might fall if the reach went wrong."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What did {a.id} do after the warning?",
            f"{a.id} listened and stepped away from the stool instead of grabbing the pistol. "
            f"That choice ended the suspense before anything could fall."
        ))
        qa.append((
            "How did they finish the lesson?",
            f"Their {parent.label_word} used the safe tool to lower {goal.the} properly. "
            f"Then the children could finish the curriculum without breaking anything."
        ))
    elif outcome == "recovered":
        qa.append((
            f"What happened when {a.id} tried to use the pistol?",
            f"The stool wobbled and the room suddenly felt dangerous. "
            f"The scary part came from using a heavy display object as a reaching tool."
        ))
        qa.append((
            f"How did the {parent.label_word} fix the problem?",
            f"{parent.label_word.capitalize()} {response.qa_text}. "
            f"The quick, calm response stopped the near accident before {goal.the} could be lost."
        ))
        qa.append((
            "What did they learn about pluck?",
            "They learned that pluck is not showing off with the wrong object. It means stopping, thinking, and asking for help when something feels unsafe."
        ))
    else:
        qa.append((
            f"Did the grown-up save {goal.the} in time?",
            f"No. The rescue came too late, and {goal.the} hit the floor. "
            f"Because the children chose the wrong tool first, the moment turned from suspense into damage."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly, with the children safe but sorry, while their {parent.label_word} put up a fresh lesson card. "
            f"The new ending shows that broken things take extra work to mend."
        ))
        qa.append((
            "What lesson stayed with the children?",
            "They remembered that hurry is not the same as pluck. The brave choice would have been to ask for help before reaching with the pistol."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["pistol"].tags) | set(f["goal_cfg"].tags) | {"curriculum"}
    outcome = f["outcome"]
    if outcome in {"averted", "recovered"}:
        tags |= set(f["response"].tags) | {"help"}
    elif outcome == "broken":
        tags |= {"help"}
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
        flags = [name for name, on in (
            ("heavy", e.heavy),
            ("hanging", e.hanging),
            ("breakable", e.breakable),
            ("long_reach", e.long_reach),
            ("stabilizes", e.stabilizes),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="harbor_room",
        pistol="flintlock",
        goal="star_chart",
        response="boat_hook",
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
    ),
    StoryParams(
        setting="captain_loft",
        pistol="captain_pistol",
        goal="map_card",
        response="step_ladder",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        setting="chart_cabin",
        pistol="brass_pistol",
        goal="compass_slate",
        response="reach_claw",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="watchful",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        setting="harbor_room",
        pistol="captain_pistol",
        goal="song_shell",
        response="step_ladder",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Rose",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        setting="captain_loft",
        pistol="flintlock",
        goal="compass_slate",
        response="boat_hook",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Ava",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
    ),
]


def explain_rejection(goal: LessonGoal) -> str:
    if not goal_at_risk(goal):
        return (
            f"(No story: {goal.the} is low enough that the children do not need a risky shortcut. "
            f"A good suspense story here needs a lesson item that is honestly too high to reach.)"
        )
    return "(No story: this goal does not create a believable reaching problem.)"


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "recovered" if is_recovered(RESPONSES[params.response], GOALS[params.goal], params.delay) else "broken"


ASP_RULES = r"""
high_risk(G) :- goal(G), height(G, H), H >= 2.
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P, G) :- setting(S), pistol(P), goal(G), high_risk(G).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(BD), A > BD.

instability(H + D + F) :- chosen_goal(G), height(G, H), delay(D), fragile_num(G, F).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- not averted, resp_power(P), instability(I), P >= I.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(broken) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PISTOLS:
        lines.append(asp.fact("pistol", pid))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("height", gid, goal.height))
        lines.append(asp.fact("fragile_num", gid, 1 if goal.fragile else 0))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
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
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a suspenseful pirate lesson about pluck, a pistol, and a curriculum."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pistol", choices=PISTOLS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal:
        goal = GOALS[args.goal]
        if not goal_at_risk(goal):
            raise StoryError(explain_rejection(goal))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.pistol is None or combo[1] == args.pistol)
        and (args.goal is None or combo[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, pistol_id, goal_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([3, 4, 5, 6, 7], 2)
    instigator_age, cautioner_age = ages[0], ages[1]
    trust = rng.randint(0, 10)
    return StoryParams(
        setting=setting_id,
        pistol=pistol_id,
        goal=goal_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.pistol not in PISTOLS:
        raise StoryError(f"(Unknown pistol: {params.pistol})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not goal_at_risk(GOALS[params.goal]):
        raise StoryError(explain_rejection(GOALS[params.goal]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        pistol=PISTOLS[params.pistol],
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
        print(f"{len(combos)} compatible (setting, pistol, goal) combos:\n")
        for setting_id, pistol_id, goal_id in combos:
            print(f"  {setting_id:12} {pistol_id:14} {goal_id}")
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
                f"### {p.instigator} & {p.cautioner}: {p.pistol} / {p.goal} "
                f"({p.setting}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
