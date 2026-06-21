#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py
=================================================================================

A standalone story world about two children playing pirates who want to go on a
special "treasure day" too early. They face a small problem: the prize day is
not today. A calm grown-up helps them use a calendar and a countdown plan, and
the story ends when they finally reach the marked square.

The world model tracks:
- physical meters: readiness, waiting, weather risk, supplies, checked days
- emotional memes: joy, impatience, worry, relief, pride, trust

The main tension is not random template swapping. The children's choices alter
state: they misread or ignore the date, face a practical obstacle, and then
solve it by checking the calendar, making a countdown chain, and preparing the
needed gear. The ending image proves what changed: they no longer rush blindly,
and the marked day truly arrives.

Run it
------
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --theme pirates --goal beach
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --goal museum --plan wait_only
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/calendar_problem_solving_sound_effects_pirate_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    visible: bool = True
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
    crew_word: str
    voyage_word: str
    sendoff: str
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
    article: str
    day_name: str
    place_line: str
    fun_line: str
    gear_needed: str
    prep_line: str
    weather_sensitive: bool
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
class Marker:
    id: str
    label: str
    sound: str
    make_line: str
    check_line: str
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
class Plan:
    id: str
    label: str
    sense: int
    checks_calendar: bool
    makes_countdown: bool
    prepares_gear: bool
    weather_backup: bool
    solve_text: str
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
        return [e for e in self.entities.values() if e.role in ("captain", "mate")]

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


def _r_false_start(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("attempted_early"):
        return out
    if world.facts.get("today_is_goal_day"):
        return out
    sig = ("false_start",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["disappointment"] += 1
        kid.memes["impatience"] += 1
    world.get("calendar").meters["confusion"] += 1
    out.append("__false_start__")
    return out


def _r_weather_block(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("attempted_early"):
        return out
    if not world.facts.get("goal_weather_sensitive"):
        return out
    if world.facts.get("weather_today") != "stormy":
        return out
    sig = ("weather_block",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__weather__")
    return out


def _r_checked_calendar(world: World) -> list[str]:
    out: list[str] = []
    cal = world.get("calendar")
    if cal.meters["looked_at"] < THRESHOLD:
        return out
    sig = ("checked_calendar",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    remaining = max(0, int(world.facts["goal_day"] - world.facts["today_day"]))
    cal.meters["days_remaining"] = float(remaining)
    world.facts["days_remaining"] = remaining
    for kid in world.kids():
        kid.memes["understanding"] += 1
    out.append("__checked__")
    return out


def _r_countdown(world: World) -> list[str]:
    out: list[str] = []
    chain = world.get("countdown")
    if chain.meters["made"] < THRESHOLD:
        return out
    sig = ("countdown",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("calendar").meters["plan"] += 1
    for kid in world.kids():
        kid.memes["patience"] += 1
        kid.memes["hope"] += 1
    out.append("__countdown__")
    return out


def _r_prep(world: World) -> list[str]:
    out: list[str] = []
    chest = world.get("gear")
    if chest.meters["packed"] < THRESHOLD:
        return out
    sig = ("prep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chest.meters["readiness"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
    out.append("__prep__")
    return out


def _r_ready(world: World) -> list[str]:
    out: list[str] = []
    cal = world.get("calendar")
    chain = world.get("countdown")
    gear = world.get("gear")
    if cal.meters["looked_at"] < THRESHOLD:
        return out
    if chain.meters["made"] < THRESHOLD:
        return out
    if gear.meters["packed"] < THRESHOLD:
        return out
    sig = ("ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["readiness"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [
    Rule(name="false_start", tag="social", apply=_r_false_start),
    Rule(name="weather_block", tag="physical", apply=_r_weather_block),
    Rule(name="checked_calendar", tag="cognitive", apply=_r_checked_calendar),
    Rule(name="countdown", tag="cognitive", apply=_r_countdown),
    Rule(name="prep", tag="physical", apply=_r_prep),
    Rule(name="ready", tag="resolution", apply=_r_ready),
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


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.sense)


def goal_reachable(goal: Goal, plan: Plan, weather_today: str) -> bool:
    if not plan.checks_calendar:
        return False
    if not plan.makes_countdown:
        return False
    if not plan.prepares_gear:
        return False
    if goal.weather_sensitive and weather_today == "stormy" and not plan.weather_backup:
        return False
    return True


def explain_goal_rejection(goal: Goal, plan: Plan, weather_today: str) -> str:
    if not plan.checks_calendar:
        return (f"(No story: {plan.label} never checks the calendar, so the children "
                f"would not really solve when {goal.article} {goal.label} happens.)")
    if not plan.makes_countdown:
        return (f"(No story: {plan.label} leaves the waiting problem loose. This world "
                f"needs a concrete countdown so the children can handle the days in between.)")
    if not plan.prepares_gear:
        return (f"(No story: {plan.label} never gets ready for {goal.article} {goal.label}, "
                f"so the ending would not show a solved plan.)")
    if goal.weather_sensitive and weather_today == "stormy" and not plan.weather_backup:
        return (f"(No story: today's weather is stormy, and {goal.article} {goal.label} "
                f"needs a backup plan or the children would just rush into trouble.)")
    return "(No story: that combination does not produce a solved problem.)"


def predict_problem(world: World) -> dict:
    sim = world.copy()
    sim.facts["attempted_early"] = True
    propagate(sim, narrate=False)
    return {
        "false_start": sim.get("calendar").meters["confusion"] >= THRESHOLD,
        "weather_risk": sim.get("room").meters["risk"] >= THRESHOLD,
        "days_remaining": max(0, int(sim.facts["goal_day"] - sim.facts["today_day"])),
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" {a.id} cried. "Today we sail for {theme.voyage_word}!"'
    )


def show_special_day(world: World, a: Entity, b: Entity, goal: Goal, marker: Marker) -> None:
    world.say(
        f"On the wall hung a big calendar. One square had {marker.make_line} around "
        f"{goal.day_name}, because that was the day for {goal.article} {goal.label}."
    )
    world.say(goal.place_line)
    world.say(goal.fun_line)
    a.memes["desire"] += 1
    b.memes["desire"] += 1


def rush_too_soon(world: World, a: Entity, b: Entity, goal: Goal) -> None:
    world.facts["attempted_early"] = True
    a.memes["impatience"] += 1
    world.say(
        f'"Clomp! Clomp!" {a.id} stomped toward the door. "Come on! Let\'s go to {goal.article} {goal.label} now!"'
    )
    world.say(
        f'{b.id} grabbed the paper map and hurried after {a.pronoun("object")}, because the game felt very real.'
    )
    propagate(world, narrate=False)


def warning(world: World, parent: Entity, a: Entity, b: Entity, goal: Goal) -> None:
    pred = predict_problem(world)
    world.facts["predicted_false_start"] = pred["false_start"]
    world.facts["predicted_weather_risk"] = pred["weather_risk"]
    world.facts["predicted_days_remaining"] = pred["days_remaining"]
    extra = ""
    if pred["weather_risk"]:
        extra = " And outside, the wind was already saying whoooosh at the windows."
    world.say(
        f'{parent.label_word.capitalize()} pointed to the calendar. "Not yet," {parent.pronoun()} said. '
        f'"{goal.day_name} is still {pred["days_remaining"]} day'
        f'{"s" if pred["days_remaining"] != 1 else ""} away.{extra}"'
    )
    world.say(
        f'{b.id} blinked at the wall. The treasure day had looked close, but not close enough.'
    )


def worry_beat(world: World, a: Entity, b: Entity, goal: Goal) -> None:
    if world.get("calendar").meters["confusion"] >= THRESHOLD:
        world.say(
            f'"Oh," {a.id} said softly. "{goal.day_name} was the marked square, not today\'s square."'
        )
    if world.get("room").meters["risk"] >= THRESHOLD:
        world.say(
            f'The curtains gave a little "fwap-fwap" in the draft, and both {world.facts["theme"].crew_word} looked back from the door.'
        )


def inspect_calendar(world: World, parent: Entity, marker: Marker) -> None:
    cal = world.get("calendar")
    cal.meters["looked_at"] += 1
    propagate(world, narrate=False)
    remaining = world.facts["days_remaining"]
    world.say(
        f'{parent.label_word.capitalize()} tapped today\'s square and then the marked one. '
        f'"Tap, tap. We can count," {parent.pronoun()} said.'
    )
    world.say(
        f'{marker.check_line.capitalize()} There were {remaining} little squares in between.'
    )


def build_plan(world: World, parent: Entity, plan: Plan, goal: Goal, marker: Marker) -> None:
    if plan.makes_countdown:
        world.get("countdown").meters["made"] += 1
    if plan.prepares_gear:
        world.get("gear").meters["packed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} smiled. "{plan.solve_text}"'
    )
    if plan.makes_countdown:
        world.say(
            f'{marker.sound.capitalize()} {marker.label.capitalize()} went onto each waiting square, one after another.'
        )
    if plan.prepares_gear:
        world.say(goal.prep_line)


def bridge_waiting_days(world: World, a: Entity, b: Entity, marker: Marker) -> None:
    remaining = world.facts.get("days_remaining", 0)
    if remaining <= 0:
        return
    world.say(
        f"Each morning they pulled off one piece of the countdown with a cheerful {marker.sound}."
    )
    if remaining == 1:
        world.say(
            f"After one sleep, only one square was left. Waiting still felt wiggly, but now it felt possible."
        )
    else:
        world.say(
            f"After each sleep, the chain grew shorter. Waiting still felt wiggly, but the days were becoming something they could hold in their hands."
        )


def arrival(world: World, a: Entity, b: Entity, goal: Goal, marker: Marker) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"At last the real square arrived. {marker.sound.capitalize()} went the final marker as {a.id} touched the calendar and laughed."
    )
    world.say(
        f"Now it truly was {goal.day_name}, and the two {world.facts['theme'].crew_word} were ready."
    )
    world.say(
        f"They took their packed things, headed out for {goal.article} {goal.label}, and {world.facts['theme'].sendoff}."
    )


def tell(
    theme: Theme,
    goal: Goal,
    marker: Marker,
    plan: Plan,
    captain: str = "Tom",
    captain_gender: str = "boy",
    mate: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
    weather_today: str = "breezy",
) -> World:
    world = World()
    a = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="calendar", type="calendar", label="calendar", portable=False))
    world.add(Entity(id="countdown", type="countdown", label="countdown chain", portable=True))
    world.add(Entity(id="gear", type="gear", label="supplies", portable=True))
    world.add(Entity(id="room", type="room", label="living room"))

    world.facts["theme"] = theme
    world.facts["goal_cfg"] = goal
    world.facts["marker_cfg"] = marker
    world.facts["plan_cfg"] = plan
    world.facts["weather_today"] = weather_today
    world.facts["goal_weather_sensitive"] = goal.weather_sensitive
    world.facts["today_day"] = 2
    world.facts["goal_day"] = 2 if weather_today == "clear" else (3 if weather_today == "breezy" else 4)
    world.facts["today_is_goal_day"] = world.facts["today_day"] == world.facts["goal_day"]
    world.facts["attempted_early"] = False
    world.facts["days_remaining"] = max(0, world.facts["goal_day"] - world.facts["today_day"])

    a.memes["trust"] = 1.0
    b.memes["trust"] = 1.0

    play_setup(world, a, b, theme)
    show_special_day(world, a, b, goal, marker)

    world.para()
    rush_too_soon(world, a, b, goal)
    warning(world, parent, a, b, goal)
    worry_beat(world, a, b, goal)

    world.para()
    inspect_calendar(world, parent, marker)
    build_plan(world, parent, plan, goal, marker)
    bridge_waiting_days(world, a, b, marker)

    world.para()
    arrival(world, a, b, goal, marker)

    world.facts.update(
        captain=a,
        mate=b,
        parent=parent,
        outcome="solved",
        checked_calendar=world.get("calendar").meters["looked_at"] >= THRESHOLD,
        countdown_made=world.get("countdown").meters["made"] >= THRESHOLD,
        gear_packed=world.get("gear").meters["packed"] >= THRESHOLD,
        room_ready=world.get("room").meters["readiness"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a jolly pirate ship",
        rig="The sofa was their ship, a laundry basket became the treasure chest, and a crayon map curled across the rug like an old sea chart.",
        titles=("Captain", "Mate"),
        crew_word="pirates",
        voyage_word="treasure day",
        sendoff="hurried off like a brave little crew at last sailing on the right tide",
    ),
    "islanders": Theme(
        id="islanders",
        scene="a tiny island harbor",
        rig="The sofa was their dock, a striped blanket became the sea, and two wooden spoons clacked together like mast poles.",
        titles=("Captain", "Scout"),
        crew_word="sailors",
        voyage_word="the marked adventure day",
        sendoff="set out with happy feet and careful plans",
    ),
}

GOALS = {
    "beach": Goal(
        id="beach",
        label="shell hunt at the beach",
        article="a",
        day_name="Saturday",
        place_line="There would be wet sand, shiny shells, and a picnic under the blue sky.",
        fun_line="To the children, it sounded exactly like a pirate treasure shore.",
        gear_needed="bucket",
        prep_line="They packed the little bucket and the striped towel beside the door.",
        weather_sensitive=True,
        tags={"beach", "calendar", "waiting"},
    ),
    "museum": Goal(
        id="museum",
        label="map room at the museum",
        article="the",
        day_name="Saturday",
        place_line="There would be old maps, model ships, and a quiet room full of places to point at.",
        fun_line="To the children, it sounded like a captain's secret chart room.",
        gear_needed="snack",
        prep_line="They set aside their snack bag and the grown-up tickets where nobody could lose them.",
        weather_sensitive=False,
        tags={"museum", "calendar", "maps"},
    ),
    "harbor": Goal(
        id="harbor",
        label="boat parade by the harbor",
        article="the",
        day_name="Saturday",
        place_line="There would be little flags, bobbing boats, and horns calling across the water.",
        fun_line="To the children, it sounded like a whole fleet of friendly pirate ships.",
        gear_needed="binoculars",
        prep_line="They put the toy binoculars and warm sweaters in one neat pile.",
        weather_sensitive=True,
        tags={"harbor", "calendar", "boats"},
    ),
}

MARKERS = {
    "star": Marker(
        id="star",
        label="gold star",
        sound="plip",
        make_line="a gold star drawn",
        check_line="Plip, plip, their fingers hopped from square to square",
        tags={"star", "countdown"},
    ),
    "sticker": Marker(
        id="sticker",
        label="anchor sticker",
        sound="stick",
        make_line="an anchor sticker pressed",
        check_line="Stick, stick, they followed the line of dates with careful fingers",
        tags={"sticker", "countdown"},
    ),
    "circle": Marker(
        id="circle",
        label="red circle",
        sound="swish",
        make_line="a red circle looped",
        check_line="Swish, swish, they traced the ring and then counted the smaller boxes",
        tags={"circle", "countdown"},
    ),
}

PLANS = {
    "full_plan": Plan(
        id="full_plan",
        label="the full plan",
        sense=3,
        checks_calendar=True,
        makes_countdown=True,
        prepares_gear=True,
        weather_backup=True,
        solve_text="We will count the sleeping nights, make a little chain for the waiting squares, and pack what we need now. If the weather fusses, we will still wait for the right day and go safely.",
        qa_text="They checked the calendar, made a countdown, and packed their things ahead of time.",
        tags={"calendar", "countdown", "problem_solving"},
    ),
    "simple_plan": Plan(
        id="simple_plan",
        label="the simple plan",
        sense=2,
        checks_calendar=True,
        makes_countdown=True,
        prepares_gear=True,
        weather_backup=False,
        solve_text="We will count the waiting squares, make a paper chain, and set our things by the door so the right day feels easy when it comes.",
        qa_text="They checked the calendar, made a paper chain, and got ready for the special day.",
        tags={"calendar", "countdown", "problem_solving"},
    ),
    "wait_only": Plan(
        id="wait_only",
        label="just waiting",
        sense=1,
        checks_calendar=True,
        makes_countdown=False,
        prepares_gear=False,
        weather_backup=False,
        solve_text="We can just try to remember and wait somehow.",
        qa_text="They only tried to wait.",
        tags={"calendar"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for goal_id, goal in GOALS.items():
            for marker_id in MARKERS:
                for plan_id, plan in PLANS.items():
                    for weather in ("breezy", "stormy", "clear"):
                        if plan.sense >= SENSE_MIN and goal_reachable(goal, plan, weather):
                            combos.append((theme_id, goal_id, marker_id, plan_id))
    return sorted(set(combos))


@dataclass
class StoryParams:
    theme: str
    goal: str
    marker: str
    plan: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    weather_today: str
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
    "calendar": [
        (
            "What is a calendar?",
            "A calendar is a chart that shows the days and dates. It helps people know when something will happen and how long they need to wait."
        )
    ],
    "countdown": [
        (
            "What is a countdown?",
            "A countdown is a way to count the days until something special happens. It makes waiting easier because you can see the days getting smaller."
        )
    ],
    "problem_solving": [
        (
            "How can a plan help with waiting?",
            "A plan breaks a big problem into small steps. When you know what to do next, waiting feels less confusing."
        )
    ],
    "beach": [
        (
            "Why might weather matter for a beach trip?",
            "Wind and storms can make the beach unsafe or unpleasant. Families often wait for calmer weather so the trip can be fun and safe."
        )
    ],
    "museum": [
        (
            "What can you see in a museum map room?",
            "You might see old maps, models, and interesting objects from long ago. People go there to look carefully and learn new things."
        )
    ],
    "boats": [
        (
            "What is a harbor?",
            "A harbor is a place by the water where boats come and go. It often has docks, ropes, and boats bobbing up and down."
        )
    ],
    "star": [
        (
            "Why do people use stars or stickers on calendars?",
            "They use them to mark important days so those days stand out. A bright mark helps your eyes find the special square quickly."
        )
    ],
    "sticker": [
        (
            "What does a sticker do on a calendar?",
            "A sticker can mark a day you want to remember. It turns one little square into an easy sign."
        )
    ],
    "circle": [
        (
            "Why would someone circle a date?",
            "Circling a date makes it easy to spot. It shows that the day matters for a reason."
        )
    ],
}
KNOWLEDGE_ORDER = ["calendar", "countdown", "problem_solving", "beach", "museum", "boats", "star", "sticker", "circle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["captain"]
    b = f["mate"]
    goal = f["goal_cfg"]
    marker = f["marker_cfg"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "calendar" and uses sound effects while two children solve a waiting problem.',
        f"Tell a gentle pirate tale where {a.id} and {b.id} want to rush to {goal.article} {goal.label}, but a grown-up helps them use a {marker.label} on the calendar and make a plan.",
        f"Write a child-facing story about waiting for a special day, counting squares on a calendar, and ending with the children happily ready at last.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["captain"]
    b = f["mate"]
    parent = f["parent"]
    goal = f["goal_cfg"]
    marker = f["marker_cfg"]
    plan = f["plan_cfg"]
    pair = pair_noun(a, b)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be pirates. It also includes their {parent.label_word}, who helped them solve the problem."
        ),
        (
            "What problem did the children have?",
            f"They wanted to go to {goal.article} {goal.label} right away, but the special day was not today. The calendar showed there were still waiting squares between today and the marked day."
        ),
        (
            "Why did the grown-up point to the calendar?",
            f"{parent.label_word.capitalize()} pointed to the calendar to show the children which square was today and which square was the special day. That helped turn a big, excited feeling into something they could count and understand."
        ),
        (
            "How did the children solve the problem?",
            f"{plan.qa_text} The plan gave them something helpful to do instead of rushing too soon."
        ),
        (
            "What did the sound effect mean when they used the calendar?",
            f"The little {marker.sound} sound went with touching or adding the {marker.label}. It made the counting feel real and playful while they worked through the problem."
        ),
        (
            "How did the story end?",
            f"It ended when the true special day finally arrived and the children were ready. The ending proves they had changed, because they stopped rushing and followed the plan they made."
        ),
    ]
    if f.get("predicted_weather_risk"):
        qa.append(
            (
                "Why was going right away a bad idea?",
                f"Going right away was a bad idea because it was not the right day yet, and the weather was rough besides. The grown-up noticed both the date problem and the outside risk before the children ran out."
            )
        )
    else:
        qa.append(
            (
                "Why was going right away a bad idea?",
                f"Going right away was a bad idea because the marked day had not arrived yet. If they rushed before checking the calendar, they would have been disappointed instead of prepared."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"calendar", "countdown", "problem_solving"}
    goal = world.facts["goal_cfg"]
    marker = world.facts["marker_cfg"]
    if "beach" in goal.tags:
        tags.add("beach")
    if "museum" in goal.tags:
        tags.add("museum")
    if "boats" in goal.tags:
        tags.add("boats")
    tags |= marker.tags
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: {{'days_remaining': {world.facts.get('days_remaining')}, 'weather_today': {world.facts.get('weather_today')}}}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        goal="beach",
        marker="star",
        plan="full_plan",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        weather_today="stormy",
    ),
    StoryParams(
        theme="pirates",
        goal="museum",
        marker="sticker",
        plan="simple_plan",
        captain="Max",
        captain_gender="boy",
        mate="Mia",
        mate_gender="girl",
        parent="father",
        weather_today="breezy",
    ),
    StoryParams(
        theme="islanders",
        goal="harbor",
        marker="circle",
        plan="full_plan",
        captain="Ava",
        captain_gender="girl",
        mate="Noah",
        mate_gender="boy",
        parent="mother",
        weather_today="clear",
    ),
]


ASP_RULES = r"""
% valid plan requirements
reachable(G,P,clear)  :- goal(G), plan(P), checks_calendar(P), makes_countdown(P), prepares_gear(P).
reachable(G,P,breezy) :- goal(G), plan(P), checks_calendar(P), makes_countdown(P), prepares_gear(P).
reachable(G,P,stormy) :- goal(G), not weather_sensitive(G), plan(P), checks_calendar(P), makes_countdown(P), prepares_gear(P).
reachable(G,P,stormy) :- goal(G), weather_sensitive(G), plan(P), checks_calendar(P), makes_countdown(P), prepares_gear(P), weather_backup(P).

valid(T,G,M,P) :- theme(T), goal(G), marker(M), plan(P), sense(P,S), sense_min(Min), S >= Min.

good_combo(T,G,M,P,W) :- valid(T,G,M,P), weather(W), reachable(G,P,W).

today_day(2).
goal_day(clear,2).
goal_day(breezy,3).
goal_day(stormy,4).

days_remaining(W,D) :- goal_day(W,G), today_day(T), D = G - T.

outcome(solved) :- chosen_weather(W), chosen_goal(G), chosen_plan(P),
                   reachable(G,P,W), chosen_theme(T), theme(T),
                   chosen_marker(M), marker(M), valid(T,G,M,P).

#show good_combo/5.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        if goal.weather_sensitive:
            lines.append(asp.fact("weather_sensitive", goal_id))
    for marker_id in MARKERS:
        lines.append(asp.fact("marker", marker_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        if plan.checks_calendar:
            lines.append(asp.fact("checks_calendar", plan_id))
        if plan.makes_countdown:
            lines.append(asp.fact("makes_countdown", plan_id))
        if plan.prepares_gear:
            lines.append(asp.fact("prepares_gear", plan_id))
        if plan.weather_backup:
            lines.append(asp.fact("weather_backup", plan_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for weather in ("clear", "breezy", "stormy"):
        lines.append(asp.fact("weather", weather))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show good_combo/5."))
    atoms = asp.atoms(model, "good_combo")
    collapsed = sorted(set((t, g, m, p) for (t, g, m, p, _w) in atoms))
    return collapsed


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_theme", params.theme),
        asp.fact("chosen_goal", params.goal),
        asp.fact("chosen_marker", params.marker),
        asp.fact("chosen_plan", params.plan),
        asp.fact("chosen_weather", params.weather_today),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.goal not in GOALS or params.plan not in PLANS:
        return "?"
    goal = GOALS[params.goal]
    plan = PLANS[params.plan]
    return "solved" if (plan.sense >= SENSE_MIN and goal_reachable(goal, plan, params.weather_today)) else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

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
        smoke = generate(cases[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate-style children solve a waiting problem with a calendar."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--weather-today", dest="weather_today", choices=["clear", "breezy", "stormy"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan is not None:
        plan = PLANS[args.plan]
        if plan.sense < SENSE_MIN:
            raise StoryError(
                f"(Refusing plan '{args.plan}': it scores too low on common sense "
                f"(sense={plan.sense} < {SENSE_MIN}). Try: {', '.join(sorted(p.id for p in sensible_plans()))}.)"
            )

    weather_choice = args.weather_today
    if args.goal and args.plan and weather_choice:
        goal = GOALS[args.goal]
        plan = PLANS[args.plan]
        if not goal_reachable(goal, plan, weather_choice):
            raise StoryError(explain_goal_rejection(goal, plan, weather_choice))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.goal is None or combo[1] == args.goal)
        and (args.marker is None or combo[2] == args.marker)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, goal_id, marker_id, plan_id = rng.choice(combos)
    weather_pool = ["clear", "breezy", "stormy"]
    if weather_choice is None:
        valid_weathers = [w for w in weather_pool if goal_reachable(GOALS[goal_id], PLANS[plan_id], w)]
        weather_choice = rng.choice(valid_weathers)
    captain, captain_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        goal=goal_id,
        marker=marker_id,
        plan=plan_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        weather_today=weather_choice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.marker not in MARKERS:
        raise StoryError(f"(Unknown marker: {params.marker})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.weather_today not in {"clear", "breezy", "stormy"}:
        raise StoryError(f"(Unknown weather: {params.weather_today})")

    goal = GOALS[params.goal]
    plan = PLANS[params.plan]
    if plan.sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing plan '{params.plan}': it scores too low on common sense "
            f"(sense={plan.sense} < {SENSE_MIN}).)"
        )
    if not goal_reachable(goal, plan, params.weather_today):
        raise StoryError(explain_goal_rejection(goal, plan, params.weather_today))

    world = tell(
        theme=THEMES[params.theme],
        goal=goal,
        marker=MARKERS[params.marker],
        plan=plan,
        captain=params.captain,
        captain_gender=params.captain_gender,
        mate=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        weather_today=params.weather_today,
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
        print(asp_program("", "#show good_combo/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, goal, marker, plan) combos:\n")
        for theme, goal, marker, plan in combos:
            print(f"  {theme:10} {goal:8} {marker:8} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.captain} & {p.mate}: {p.goal} ({p.theme}, {p.marker}, {p.plan}, {p.weather_today})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
