#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py
======================================================================

A standalone story world for a tiny "pirate swim school" tale. Children at swim
school pretend the pool is a pirate bay. One child wants to wear shiny hair gel
to make a pirate crest, but slick hair can make swim goggles slide. A friend or
helper warns about the risk, a grown-up instructor responds, and the ending
shows what changed: either the child chooses the safe way before class, or the
class pauses and fixes the problem.

The world is deliberately small and constraint-checked:

- Some lesson activities truly need clear goggles in the water.
- Hair gel has a slickness level.
- A fix must actually beat the slickness risk.
- Weak fixes are known to the world but refused by the common-sense gate.
- The inline ASP twin mirrors the Python gate and outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py --gel glitter_gel --lesson treasure_dive
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py --lesson rhyme_bench
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/behave_gel_swim_school_rhyme_pirate_tale.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


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
        female = {"girl", "mother", "woman", "coach_f"}
        male = {"boy", "father", "man", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"coach_f": "coach", "coach_m": "coach"}.get(self.type, self.type)
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
class SchoolTheme:
    id: str
    school_name: str
    room_name: str
    pool_name: str
    opening: str
    sendoff: str
    rhyme_a: str
    rhyme_b: str
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
class Lesson:
    id: str
    label: str
    call: str
    water_task: str
    need_goggles: bool
    splashes: bool
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
class GelStyle:
    id: str
    label: str
    phrase: str
    color: str
    boast: str
    slickness: int
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    next_time: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "buddy"}]

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    goggles = world.get("goggles")
    hair = world.get("hair")
    lesson = world.facts["lesson_cfg"]
    if not lesson.need_goggles:
        return out
    if child.meters["in_water"] < THRESHOLD:
        return out
    if goggles.meters["on_face"] < THRESHOLD:
        return out
    if hair.meters["slick"] < THRESHOLD:
        return out
    sig = ("slip", hair.id, lesson.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goggles.meters["slipping"] += 1
    child.meters["blurred_vision"] += 1
    child.memes["fear"] += 1
    world.get("pool").meters["risk"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
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


def hazard_at_risk(gel: GelStyle, lesson: Lesson) -> bool:
    return gel.slickness > 0 and lesson.need_goggles and lesson.splashes


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.sense, f.power))


def hazard_severity(gel: GelStyle, delay: int) -> int:
    return gel.slickness + delay


def is_contained(fix: Fix, gel: GelStyle, delay: int) -> bool:
    return fix.power >= hazard_severity(gel, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, buddy_age: int, trait: str) -> bool:
    buddy_older = relation == "siblings" and buddy_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if buddy_older else 0.0)
    return buddy_older and authority > BRAVERY_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["in_water"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": sim.get("goggles").meters["slipping"] >= THRESHOLD,
        "risk": sim.get("pool").meters["risk"],
    }


def open_school(world: World, child: Entity, buddy: Entity, theme: SchoolTheme, lesson: Lesson) -> None:
    for kid in (child, buddy):
        kid.memes["joy"] += 1
    world.say(
        f"At {theme.school_name}, the warm room around {theme.pool_name} smelled like soap and splashes. "
        f"{theme.opening}"
    )
    world.say(
        f'"{lesson.call}!" sang the coach. "{theme.rhyme_a}, {theme.rhyme_b}!"'
    )
    world.say(
        f"{child.id} and {buddy.id} grinned. To them, the blue water looked like a pirate bay, "
        f"and the float rings looked like bright treasure."
    )


def show_gel(world: World, child: Entity, gel: GelStyle) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Before class, {child.id} had smoothed {gel.phrase} into {child.pronoun('possessive')} hair. "
        f"The {gel.color} shine stood up in a brave little crest."
    )
    world.say(f'"{gel.boast}" {child.id} said.')


def praise_rhyme(world: World, buddy: Entity, theme: SchoolTheme) -> None:
    world.say(
        f'{buddy.id} laughed and answered in a rhyme of {buddy.pronoun("possessive")} own: '
        f'"If we kick and dip and lightly behave, we can be the bravest crew on the wave."'
    )


def warn(world: World, buddy: Entity, child: Entity, coach: Entity, gel: GelStyle, lesson: Lesson) -> None:
    pred = predict_slip(world)
    buddy.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    extra = ""
    if buddy.memes["caution"] >= 6:
        extra = f" {buddy.pronoun().capitalize()} looked hard at the goggles and did not smile anymore."
    world.say(
        f'{buddy.id} touched the strap of {child.id}\'s goggles. "{child.id}, please behave," '
        f'{buddy.pronoun()} said softly. "That {gel.label} is slick, and in {lesson.label} the water splashes hard. '
        f'If your goggles slide, you will not see the rings clearly."{extra}'
    )
    world.say(
        f'The coach heard and nodded. "Clear eyes first, pirate hearts next," {coach.pronoun()} said.'
    )


def defy(world: World, child: Entity, buddy: Entity) -> None:
    child.memes["defiance"] += 1
    older_sib = child.attrs.get("relation") == "siblings" and child.age > buddy.age
    if older_sib:
        world.say(
            f'"It will be fine," {child.id} said, and because {child.pronoun()} was the older sibling, '
            f"{buddy.id} could not stop {child.pronoun('object')} in time."
        )
    else:
        world.say(f'"It will be fine," {child.id} said, and hurried to the pool steps before anyone could answer.')


def back_down(world: World, child: Entity, buddy: Entity, coach: Entity, fix: Fix, lesson: Lesson) -> None:
    child.memes["relief"] += 1
    buddy.memes["relief"] += 1
    child.memes["bravery"] = 0.0
    world.say(
        f'{child.id} looked at the shiny crest again, then at the deep blue lane. '
        f'"Maybe pirate hair is not worth blurry eyes," {child.pronoun()} admitted.'
    )
    world.say(
        f'{coach.label_word.capitalize()} smiled. "{fix.next_time}, and then we can {lesson.water_task}," '
        f'{coach.pronoun()} said.'
    )
    world.say(
        f"So {child.id} chose the safe way before class even began, and the worry floated right out of the room."
    )


def enter_water(world: World, child: Entity, lesson: Lesson) -> None:
    child.meters["in_water"] += 1
    world.get("goggles").meters["on_face"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} splashed into the lane to {lesson.water_task}. For one bright moment, the pool felt like open sea."
    )


def slip_beat(world: World, child: Entity) -> None:
    world.say(
        f"Then the slick hair pushed under the strap. One side of the goggles wriggled loose, "
        f"and the water turned wavy and wrong in front of {child.id}."
    )
    world.say(
        f'"Coach!" {child.id} gasped. {child.pronoun().capitalize()} stopped kicking and grabbed the pool edge at once.'
    )


def assist(world: World, coach: Entity, child: Entity, buddy: Entity, fix: Fix, lesson: Lesson) -> None:
    world.get("pool").meters["risk"] = 0.0
    world.get("goggles").meters["slipping"] = 0.0
    child.meters["blurred_vision"] = 0.0
    child.meters["in_water"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    buddy.memes["relief"] += 1
    world.say(
        f"{coach.label_word.capitalize()} moved quickly and {fix.text}."
    )
    world.say(
        f'Soon the goggles sat snug again. "{theme_line(lesson)}," the coach said in a calm little rhyme.'
    )


def miss_turn(world: World, coach: Entity, child: Entity, buddy: Entity, fix: Fix, lesson: Lesson) -> None:
    child.meters["in_water"] = 0.0
    child.memes["fear"] += 1
    buddy.memes["sadness"] += 1
    world.say(
        f"{coach.label_word.capitalize()} {fix.fail}."
    )
    world.say(
        f"The class had to pause, and the treasure rings were gathered back into the basket while the lane went still."
    )
    world.say(
        f"{child.id} was safe at the wall, but {child.pronoun()} missed the best part of {lesson.label} that day."
    )


def lesson_talk(world: World, coach: Entity, child: Entity, buddy: Entity, gel: GelStyle) -> None:
    for kid in (child, buddy):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{coach.label_word.capitalize()} knelt by the tiles. "I am glad you stopped and called me," '
        f'{coach.pronoun()} said. "At swim school, pirate games are fun, but safety comes first. '
        f'If I say behave, it is because water needs clear eyes and calm bodies."'
    )
    world.say(
        f'{child.id} nodded and touched the {gel.label} in {child.pronoun("possessive")} hair. '
        f'"I wanted a pirate crest," {child.pronoun()} whispered.'
    )
    world.say(
        f'"You can still be brave," {buddy.id} said, "just brave in the careful way."'
    )


def bright_ending(world: World, coach: Entity, child: Entity, buddy: Entity, lesson: Lesson, fix: Fix) -> None:
    child.memes["joy"] += 1
    buddy.memes["joy"] += 1
    child.memes["safety"] += 1
    buddy.memes["safety"] += 1
    world.say(
        f"After that, {child.id} went back to the water and {lesson.water_task} with steady kicks and clear eyes."
    )
    world.say(
        f"{buddy.id} splashed beside {child.pronoun('object')}, and together they sang, "
        f'"Dip, don\'t slip; blink, don\'t sink!"'
    )
    world.say(
        f"When class ended, the two young pirates marched out grinning, and {child.id} promised that next time "
        f"{fix.next_time}."
    )


def quiet_ending(world: World, coach: Entity, child: Entity, buddy: Entity, fix: Fix) -> None:
    child.memes["lesson"] += 1
    buddy.memes["lesson"] += 1
    world.say(
        f"On the bench, wrapped in warm towels, {child.id} watched the ripples settle and wished {child.pronoun()} had listened sooner."
    )
    world.say(
        f'{coach.label_word.capitalize()} tapped the swim cap basket and said, "{fix.next_time}."'
    )
    world.say(
        f"Next week, when the pirate game began again, {child.id} came in neat and ready, and the goggles stayed where they belonged."
    )


def theme_line(lesson: Lesson) -> str:
    if lesson.id == "treasure_dive":
        return "Rinse or cap, then treasure map"
    if lesson.id == "kick_race":
        return "Snug on the face wins the race"
    return "Clear little eyes make strong little tries"


def tell(
    theme: SchoolTheme,
    lesson: Lesson,
    gel: GelStyle,
    fix: Fix,
    *,
    child_name: str = "Milo",
    child_gender: str = "boy",
    buddy_name: str = "Nora",
    buddy_gender: str = "girl",
    coach_type: str = "coach_f",
    trait: str = "careful",
    delay: int = 0,
    child_age: int = 6,
    buddy_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="instigator",
        age=child_age,
        attrs={"relation": relation},
    ))
    buddy = world.add(Entity(
        id=buddy_name,
        kind="character",
        type=buddy_gender,
        role="buddy",
        age=buddy_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_type,
        role="coach",
        label="the coach",
    ))
    pool = world.add(Entity(id="pool", type="pool", label=theme.pool_name))
    hair = world.add(Entity(id="hair", type="hair", label="hair"))
    goggles = world.add(Entity(id="goggles", type="goggles", label="goggles"))

    child.memes["bravery"] = BRAVERY_INIT
    buddy.memes["caution"] = initial_caution(trait)
    pool.meters["risk"] = 0.0
    hair.meters["slick"] = float(gel.slickness)
    goggles.meters["on_face"] = 0.0
    goggles.meters["slipping"] = 0.0
    child.meters["in_water"] = 0.0
    child.meters["blurred_vision"] = 0.0

    world.facts["theme"] = theme
    world.facts["lesson_cfg"] = lesson
    world.facts["gel_cfg"] = gel
    world.facts["fix_cfg"] = fix
    world.facts["delay"] = delay

    open_school(world, child, buddy, theme, lesson)
    show_gel(world, child, gel)
    praise_rhyme(world, buddy, theme)

    world.para()
    warn(world, buddy, child, coach, gel, lesson)

    averted = would_avert(relation, child.age, buddy.age, trait)
    if averted:
        back_down(world, child, buddy, coach, fix, lesson)
        contained = True
        outcome = "averted"
    else:
        defy(world, child, buddy)
        world.para()
        enter_water(world, child, lesson)
        slip_beat(world, child)

        severity = hazard_severity(gel, delay)
        contained = is_contained(fix, gel, delay)

        world.para()
        if contained:
            assist(world, coach, child, buddy, fix, lesson)
            lesson_talk(world, coach, child, buddy, gel)
            world.para()
            bright_ending(world, coach, child, buddy, lesson, fix)
            outcome = "contained"
        else:
            miss_turn(world, coach, child, buddy, fix, lesson)
            lesson_talk(world, coach, child, buddy, gel)
            world.para()
            quiet_ending(world, coach, child, buddy, fix)
            outcome = "missed"

    if averted:
        severity = 0

    world.facts.update(
        child=child,
        buddy=buddy,
        coach=coach,
        pool=pool,
        hair=hair,
        goggles=goggles,
        lesson=lesson,
        gel=gel,
        fix=fix,
        relation=relation,
        predicted_slip=world.facts.get("predicted_risk", 0) > 0,
        outcome=outcome,
        severity=severity,
        contained=contained,
        averted=averted,
        slipped=(outcome != "averted"),
    )
    return world


THEMES = {
    "pirate_swim": SchoolTheme(
        id="pirate_swim",
        school_name="Captain Coral's Swim School",
        room_name="the warm pool room",
        pool_name="the lesson pool",
        opening="Foam noodles rested in a bright barrel, kickboards leaned like little shields, and the lane ropes gleamed like ropes on a tidy ship.",
        sendoff="strode out like a happy crew",
        rhyme_a="Kick and grin",
        rhyme_b="safely in",
    ),
}

LESSONS = {
    "treasure_dive": Lesson(
        id="treasure_dive",
        label="Treasure Dive",
        call="Treasure Dive time",
        water_task="dive for the treasure rings",
        need_goggles=True,
        splashes=True,
        tags={"goggles", "swim_school", "dive"},
    ),
    "kick_race": Lesson(
        id="kick_race",
        label="Kick Race",
        call="Kick Race time",
        water_task="kick to the floating flag",
        need_goggles=True,
        splashes=True,
        tags={"goggles", "swim_school", "kicking"},
    ),
    "rhyme_bench": Lesson(
        id="rhyme_bench",
        label="Rhyme Bench",
        call="Rhyme Bench time",
        water_task="clap the safety song on the bench",
        need_goggles=False,
        splashes=False,
        tags={"rhyme", "swim_school"},
    ),
}

GELS = {
    "glitter_gel": GelStyle(
        id="glitter_gel",
        label="glitter gel",
        phrase="a stripe of glitter gel",
        color="silver-blue",
        boast="Now I look like a captain from the shining sea",
        slickness=2,
        tags={"gel", "goggles"},
    ),
    "spike_gel": GelStyle(
        id="spike_gel",
        label="spike gel",
        phrase="a dab of spike gel",
        color="dark blue",
        boast="My pirate crest points straight at treasure",
        slickness=3,
        tags={"gel", "goggles"},
    ),
    "shell_gel": GelStyle(
        id="shell_gel",
        label="shell gel",
        phrase="a tiny curl of shell gel",
        color="green",
        boast="Even the sea would salute this hair",
        slickness=1,
        tags={"gel"},
    ),
}

FIXES = {
    "rinse_and_reset": Fix(
        id="rinse_and_reset",
        sense=3,
        power=2,
        text="guided the child to the shower, rinsed the gel away, and settled the goggles back into place",
        fail="tried a quick rinse, but there was still too much slick gel under the strap to keep the goggles steady",
        qa_text="rinsed the gel away and reset the goggles",
        next_time="the gel will wait until after swim school",
        tags={"rinse", "goggles"},
    ),
    "swim_cap": Fix(
        id="swim_cap",
        sense=3,
        power=4,
        text="slipped a snug swim cap over the shiny crest and tightened the goggles gently over it",
        fail="reached for a swim cap, but the pause had already used up the turn and class moved on",
        qa_text="put on a swim cap and tightened the goggles",
        next_time="a swim cap will go on before any pirate style",
        tags={"swim_cap", "goggles"},
    ),
    "towel_wipe": Fix(
        id="towel_wipe",
        sense=1,
        power=1,
        text="rubbed the hair with a towel and tried to press the strap down again",
        fail="wiped the hair with a towel, but the strap still slid over the slick patch",
        qa_text="wiped the hair with a towel and pressed the strap down",
        next_time="the towel trick is not enough for slick gel",
        tags={"towel", "goggles"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora", "Rose", "Poppy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Milo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_fixes():
        return combos
    for lesson_id, lesson in LESSONS.items():
        for gel_id, gel in GELS.items():
            if hazard_at_risk(gel, lesson):
                combos.append((lesson_id, gel_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    lesson: str
    gel: str
    fix: str
    child_name: str
    child_gender: str
    buddy_name: str
    buddy_gender: str
    coach: str
    trait: str
    delay: int = 0
    child_age: int = 6
    buddy_age: int = 4
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
    "gel": [(
        "What is gel for hair?",
        "Hair gel is a sticky, slippery stuff people smooth into hair to help it hold a shape. Too much of it can make things slide."
    )],
    "goggles": [(
        "Why do swimmers wear goggles?",
        "Swimmers wear goggles to keep water out of their eyes and help them see clearly under the water. Clear eyes make it easier to notice where to kick and where to stop."
    )],
    "swim_school": [(
        "What happens at swim school?",
        "At swim school, children practice floating, kicking, breathing, and listening to a coach in the pool. The coach helps everyone stay safe while they learn."
    )],
    "dive": [(
        "Why is it important to see clearly when you dive for rings?",
        "Seeing clearly helps you know where the rings are and where the pool edge is. If your goggles slip, you can feel confused and should stop right away."
    )],
    "kicking": [(
        "Why should swimmers listen during a kick race?",
        "Listening helps swimmers wait for the right time to start and keep their bodies safe in the lane. Calm, careful swimming is faster than wild splashing."
    )],
    "rinse": [(
        "Why can rinsing hair help with goggles?",
        "Rinsing can wash slippery gel away so the strap grips better. When the strap stays put, the swimmer can see more clearly."
    )],
    "swim_cap": [(
        "What does a swim cap do?",
        "A swim cap holds hair close to the head so it stays neat in the water. It can also give goggles a steadier place to sit."
    )],
}
KNOWLEDGE_ORDER = ["gel", "goggles", "swim_school", "dive", "kicking", "rinse", "swim_cap"]


def pair_noun(child: Entity, buddy: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and buddy.type == "boy":
            return "two brothers"
        if child.type == "girl" and buddy.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    gel = f["gel"]
    lesson = f["lesson"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-flavored swim-school story for a 3-to-5-year-old that includes the words "behave" and "gel".',
            f"Tell a rhyming story where {child.id} comes to swim school wearing {gel.label}, but {buddy.id} warns that the goggles may slide, and the child chooses the safe way before getting in the pool.",
            f"Write a gentle story set at swim school where a child wants pirate hair, hears the coach say behave, and learns to trade style for safety."
        ]
    if outcome == "missed":
        return [
            f'Write a pirate-flavored swim-school story for a 3-to-5-year-old that includes the words "behave" and "gel".',
            f"Tell a cautionary story where {child.id} ignores a warning about {gel.label}, the goggles slip during {lesson.label}, and the child misses the game but learns the lesson safely.",
            f"Write a rhyming swim-school story with a worried friend, a quick coach, and an ending where the child comes better prepared next time."
        ]
    return [
        f'Write a pirate-flavored swim-school story for a 3-to-5-year-old that includes the words "behave" and "gel".',
        f"Tell a rhyming story where {child.id} wears {gel.label} to {lesson.label}, the goggles slip, and a calm coach fixes the problem so the game can continue.",
        f"Write a simple story in pirate-tale style where swim-school safety matters more than showing off."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    coach = f["coach"]
    lesson = f["lesson"]
    gel = f["gel"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(child, buddy, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {buddy.id}, at swim school with their coach. They were pretending the pool was a pirate bay."
        ),
        (
            f"Why did {child.id} put gel in {child.pronoun('possessive')} hair?",
            f"{child.id} wanted a shiny pirate crest before class. The gel made the hair look bold, but it also made it slippery."
        ),
        (
            f"Why did {buddy.id} ask {child.id} to behave?",
            f"{buddy.id} worried the slick gel would make the goggles slide during {lesson.label}. If the goggles slipped in splashing water, {child.id} might not see clearly."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed before class began?",
            f"{child.id} listened before getting into the pool and chose the safe plan instead. That stopped the problem before the goggles ever had a chance to slip."
        ))
        qa.append((
            "How did the story end?",
            f"It ended calmly and brightly, with the worry gone and the crew ready to learn safely. The ending shows that being brave can also mean being careful."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {child.id} got in the water?",
            f"The goggles wriggled loose because the slick hair pushed under the strap. {child.id} stopped at the wall and called for help right away."
        ))
        qa.append((
            f"How did the coach solve the problem?",
            f"The coach {fix.qa_text}. That worked because it gave the goggles a steadier, less slippery place to sit."
        ))
        qa.append((
            "How did the story end?",
            f"{child.id} went back to class with clear eyes and a calmer heart. The two children finished as a happy little pirate crew, but now they understood the safe way."
        ))
    else:
        qa.append((
            f"Did the first fix work well enough for {lesson.label}?",
            f"No. The coach helped quickly, but the trouble had already used up the turn, so {child.id} missed the best part of the game that day."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.id} learned that pirate style comes after swim-school safety. Next time, the child came ready so the goggles could stay put from the start."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["gel"].tags) | set(f["lesson"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["fix"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirate_swim",
        lesson="treasure_dive",
        gel="glitter_gel",
        fix="swim_cap",
        child_name="Milo",
        child_gender="boy",
        buddy_name="Nora",
        buddy_gender="girl",
        coach="coach_f",
        trait="careful",
        delay=0,
        child_age=6,
        buddy_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="pirate_swim",
        lesson="kick_race",
        gel="shell_gel",
        fix="rinse_and_reset",
        child_name="Lucy",
        child_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        coach="coach_m",
        trait="steady",
        delay=0,
        child_age=5,
        buddy_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="pirate_swim",
        lesson="treasure_dive",
        gel="spike_gel",
        fix="rinse_and_reset",
        child_name="Sam",
        child_gender="boy",
        buddy_name="Mia",
        buddy_gender="girl",
        coach="coach_f",
        trait="cautious",
        delay=1,
        child_age=7,
        buddy_age=5,
        relation="siblings",
    ),
    StoryParams(
        theme="pirate_swim",
        lesson="kick_race",
        gel="spike_gel",
        fix="swim_cap",
        child_name="Ava",
        child_gender="girl",
        buddy_name="Leo",
        buddy_gender="boy",
        coach="coach_m",
        trait="gentle",
        delay=0,
        child_age=6,
        buddy_age=6,
        relation="friends",
    ),
]


def explain_rejection(lesson: Lesson, gel: GelStyle) -> str:
    if not lesson.need_goggles or not lesson.splashes:
        return (
            f"(No story: {lesson.label} does not put a slick-haired child into splashing water with working goggles, "
            f"so there is no honest gel problem to solve. Pick a pool lesson like treasure_dive or kick_race.)"
        )
    if gel.slickness <= 0:
        return f"(No story: {gel.label} is not slick enough to matter here.)"
    return "(No story: this combination has no goggles-slip hazard.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = " / ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.buddy_age, params.trait):
        return "averted"
    return "contained" if is_contained(FIXES[params.fix], GELS[params.gel], params.delay) else "missed"


ASP_RULES = r"""
hazard(L, G) :- lesson(L), gel(G), need_goggles(L), splashes(L), slickness(G, S), S > 0.
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, L, G) :- theme(T), lesson(L), gel(G), hazard(L, G).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
buddy_older :- relation(siblings), child_age(CA), buddy_age(BA), BA > CA.
bonus(4) :- buddy_older.
bonus(0) :- not buddy_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- buddy_older, authority(A), bravery_init(BR), A > BR.

severity(S + D) :- chosen_gel(G), slickness(G, S), delay(D).
fix_power(P) :- chosen_fix(F), power(F, P).
contained :- fix_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(missed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for lid, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        if lesson.need_goggles:
            lines.append(asp.fact("need_goggles", lid))
        if lesson.splashes:
            lines.append(asp.fact("splashes", lid))
    for gid, gel in GELS.items():
        lines.append(asp.fact("gel", gid))
        lines.append(asp.fact("slickness", gid, gel.slickness))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_gel", params.gel),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("buddy_age", params.buddy_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set((theme, lesson, gel) for theme in THEMES for lesson, gel in valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

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
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story during smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate swim school, rhymes, hair gel, and safe goggles."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--gel", choices=GELS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--coach", choices=["coach_f", "coach_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much time the trouble costs before the fix can work")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lesson and args.gel:
        lesson = LESSONS[args.lesson]
        gel = GELS[args.gel]
        if not hazard_at_risk(gel, lesson):
            raise StoryError(explain_rejection(lesson, gel))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.lesson is None or combo[0] == args.lesson)
        and (args.gel is None or combo[1] == args.gel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lesson_id, gel_id = rng.choice(sorted(combos))
    theme = args.theme or "pirate_swim"
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    child_name, child_gender = _pick_kid(rng)
    buddy_name, buddy_gender = _pick_kid(rng, avoid=child_name)
    coach = args.coach or rng.choice(["coach_f", "coach_m"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    child_age, buddy_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        lesson=lesson_id,
        gel=gel_id,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        coach=coach,
        trait=trait,
        delay=delay,
        child_age=child_age,
        buddy_age=buddy_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        lesson = LESSONS[params.lesson]
        gel = GELS[params.gel]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not hazard_at_risk(gel, lesson):
        raise StoryError(explain_rejection(lesson, gel))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        theme=theme,
        lesson=lesson,
        gel=gel,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        coach_type=params.coach,
        trait=params.trait,
        delay=params.delay,
        child_age=params.child_age,
        buddy_age=params.buddy_age,
        relation=params.relation,
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
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, lesson, gel) combos:\n")
        for theme, lesson, gel in combos:
            print(f"  {theme:12} {lesson:14} {gel}")
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
            header = f"### {p.child_name} & {p.buddy_name}: {p.gel} in {p.lesson} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
