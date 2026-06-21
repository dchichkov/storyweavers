#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lower_calendar_inspector_rhyme_foreshadowing_conflict_folk.py
=============================================================================================

A tiny folk-tale storyworld about a village clock-room, a careful lowerer,
a calendar, and an inspector who arrives just before a mistake turns into a
mess. The world is built around three required seed words -- lower, calendar,
inspector -- and the narrative instruments Rhyme, Foreshadowing, and Conflict.

Premise
-------
A village keeps its dates, feast days, and market bells on a hanging calendar.
A child helper is asked to lower the calendar for the day. The task sounds
simple, but the frame is high on a wall and the inspector is due to visit.

Tension
-------
The child wants to help quickly, yet the calendar can tear or fall if handled
carelessly. The inspector notices signs of trouble in advance, warns about them,
and the story can turn either into a safe fix or a small folk-tale tangle.

Turn
----
The lowering action changes the room state: if done well, the calendar comes
down neatly and the dates are saved; if done badly, the pages crumple, the room
grows tense, and the inspector must intervene.

Resolution
----------
A wise fix uses a stool, a ribbon, or a careful helper. The ending image proves
what changed by showing the calendar lowered safely, the conflict eased, and the
village ready for the next day.

This file is self-contained and uses only the stdlib plus the shared
storyworlds/results.py containers. clingo support is imported lazily through
storyworlds/asp.py when ASP modes are requested.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Calendar:
    id: str
    label: str
    phrase: str
    pages: int
    ribbon: str
    fragile: bool = True
    lowerable: bool = True
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
class InspectorProfile:
    id: str
    title: str
    label: str
    rhyme: str
    warning: str
    praise: str
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
class Fix:
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
    village: str
    calendar: str
    inspector: str
    helper_name: str
    helper_type: str
    adult_name: str
    adult_type: str
    fix: str
    delay: int = 0
    helper_age: int = 7
    adult_age: int = 35
    helper_care: int = 5
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    cal = world.entities.get("calendar")
    if not cal:
        return out
    if cal.meters["fallen"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cal.meters["torn"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"helper", "inspector", "adult"}:
            ent.memes["alarm"] += 1
    out.append("__damage__")
    return out


def _r_relief(world: World) -> list[str]:
    cal = world.entities.get("calendar")
    if not cal:
        return []
    if cal.meters["lowered"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"helper", "inspector", "adult"}:
            ent.memes["relief"] += 1
    return ["The dates settled down like seeds in a pouch."]


CAUSAL_RULES = [Rule("damage", "physical", _r_damage), Rule("relief", "social", _r_relief)]


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


def lower_risk(calendar: Calendar, delay: int) -> int:
    return 1 + delay


def is_safe_fix(fix: Fix, calendar: Calendar, delay: int) -> bool:
    return fix.power >= lower_risk(calendar, delay)


def has_reason_to_warn(calendar: Calendar) -> bool:
    return calendar.fragile and calendar.lowerable


def valid_calendar(calendar: Calendar) -> bool:
    return calendar.lowerable and calendar.fragile


def sensibly_fixable() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def predict_lower(world: World, calendar_id: str) -> dict:
    sim = world.copy()
    _lower_calendar(sim, sim.get(calendar_id), narrate=False)
    return {
        "lowered": sim.get(calendar_id).meters["lowered"] >= THRESHOLD,
        "torn": sim.get(calendar_id).meters["torn"] >= THRESHOLD,
    }


def _lower_calendar(world: World, calendar: Entity, narrate: bool = True) -> None:
    calendar.meters["lowered"] += 1
    propagate(world, narrate=narrate)


def scene_setup(world: World, helper: Entity, adult: Entity, village: str, cal: Calendar) -> None:
    helper.memes["help"] += 1
    world.say(
        f"In {village}, the cottage had a bright wall where the village calendar hung "
        f"high and neat. Its pages waited for names, market days, and feast bells."
    )
    world.say(
        f"{helper.id} liked to help in the old house, and {adult.id} trusted "
        f"{helper.pronoun('object')} with small chores."
    )


def foreshadow(world: World, inspector: Entity, cal: Calendar) -> None:
    inspector.memes["notice"] += 1
    world.say(
        f"Before long, {inspector.label} came along the lane. "
        f"{inspector.rhyme} {inspector.warning}"
    )
    world.say(
        f"{inspector.id} glanced at the cord and the crooked nail. "
        f"The calendar looked a little too high for a hurried hand."
    )


def conflict(world: World, helper: Entity, inspector: Entity, cal: Calendar) -> None:
    helper.memes["want"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f'{helper.id} said, "I can lower the calendar now, quick as a hare." '
        f'But {inspector.id} frowned and pointed to the loose ribbon there.'
    )
    world.say(
        f'"A rush can crumple the month," {inspector.id} said. '
        f'"Go slow, go low, and let the pages glow."'
    )


def careful_lower(world: World, helper: Entity, adult: Entity, cal: Entity, calendar: Calendar) -> None:
    helper.memes["pride"] += 1
    cal.meters["lowered"] += 1
    world.say(
        f"Together they brought a stool to the wall, and {helper.id} lowered the "
        f"calendar with both hands, one corner at a time."
    )
    world.say(
        f"The ribbon held, the pages stayed flat, and the dates came down without a wrinkle."
    )


def mishap(world: World, helper: Entity, adult: Entity, cal: Entity, calendar: Calendar) -> None:
    cal.meters["fallen"] += 1
    cal.meters["lowered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} tugged too hard, and the calendar slipped. It fluttered down like "
        f"a startled bird and banged against the table."
    )
    world.say(
        f"A corner bent, and the week names shook loose. {adult.id} reached out at once."
    )


def rescue(world: World, adult: Entity, fix: Fix, cal: Entity, calendar: Calendar) -> None:
    cal.meters["torn"] = 0.0
    cal.meters["fallen"] = 0.0
    body = fix.text.replace("{calendar}", calendar.label)
    world.say(
        f"{adult.id} smiled and {body}."
    )
    world.say(
        f"Then the pages were straight again, and the wall looked calm as a pond."
    )


def lesson(world: World, adult: Entity, helper: Entity, inspector: Entity, calendar: Calendar) -> None:
    helper.memes["relief"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"{adult.id} knelt beside {helper.id}. \"You're not in trouble for asking,\" "
        f"{adult.pronoun()} said. \"But the careful way saves the day.\""
    )
    world.say(
        f"{inspector.id} nodded too. \"A thing hung high must be treated like a song "
        f"with soft feet,\" {inspector.id} said."
    )


def ending(world: World, helper: Entity, inspector: Entity, cal: Entity, calendar: Calendar) -> None:
    world.say(
        f"At dusk, the calendar hung lower and safer than before. Its newest page was flat, "
        f"and the next day's square had been marked in red ink."
    )
    world.say(
        f"{helper.id} and {inspector.id} stood shoulder to shoulder, and the room felt "
        f"ready for tomorrow's bell."
    )


def tell(village: str, cal_cfg: Calendar, inspector_cfg: InspectorProfile, fix: Fix,
         helper_name: str = "Mira", helper_type: str = "girl",
         adult_name: str = "Grandma", adult_type: str = "woman",
         delay: int = 0, helper_age: int = 7, adult_age: int = 35, helper_care: int = 5) -> World:
    world = World()
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="adult"))
    inspector = world.add(Entity(id="Inspector", kind="character", type="person", role="inspector"))
    cal = world.add(Entity(id="calendar", kind="thing", type="calendar", label=cal_cfg.label))
    helper.attrs.update(age=helper_age, care=helper_care)
    adult.attrs.update(age=adult_age)
    world.facts["village"] = village
    world.facts["calendar_cfg"] = cal_cfg
    world.facts["inspector_cfg"] = inspector_cfg
    world.facts["fix"] = fix
    world.facts["delay"] = delay
    scene_setup(world, helper, adult, village, cal_cfg)
    world.para()
    foreshadow(world, inspector, cal_cfg)
    conflict(world, helper, inspector, cal_cfg)
    if delay == 0:
        careful_lower(world, helper, adult, cal, cal_cfg)
        world.para()
        rescue(world, adult, fix, cal, cal_cfg)
        lesson(world, adult, helper, inspector, cal_cfg)
        world.para()
        ending(world, helper, inspector, cal, cal_cfg)
        outcome = "safe"
    else:
        mishap(world, helper, adult, cal, cal_cfg)
        world.para()
        rescue(world, adult, fix, cal, cal_cfg)
        lesson(world, adult, helper, inspector, cal_cfg)
        world.para()
        ending(world, helper, inspector, cal, cal_cfg)
        outcome = "mended"
    world.facts["outcome"] = outcome
    world.facts["helper"] = helper
    world.facts["adult"] = adult
    world.facts["inspector"] = inspector
    world.facts["calendar"] = cal
    return world


VILLAGES = {
    "hill": "the hill village",
    "river": "the river hamlet",
    "orchard": "the orchard lane",
}

CALENDARS = {
    "market": Calendar(
        id="market",
        label="village calendar",
        phrase="a village calendar with bright squares",
        pages=12,
        ribbon="a blue ribbon",
        tags={"calendar", "dates"},
    ),
    "feast": Calendar(
        id="feast",
        label="feast calendar",
        phrase="a feast calendar with painted birds",
        pages=8,
        ribbon="a red ribbon",
        tags={"calendar", "feast"},
    ),
    "school": Calendar(
        id="school",
        label="school calendar",
        phrase="a school calendar with gold stars",
        pages=10,
        ribbon="a green ribbon",
        tags={"calendar", "school"},
    ),
}

INSPECTORS = {
    "moss": InspectorProfile(
        id="moss",
        title="the moss inspector",
        label="Inspector Moss",
        rhyme="Moss in the lane, see the cord by the chain.",
        warning="If you pull too fast, the month may slip and the day may last.",
        praise="You kept it steady and true.",
        tags={"inspector", "rhyme", "foreshadowing"},
    ),
    "reed": InspectorProfile(
        id="reed",
        title="the reed inspector",
        label="Inspector Reed",
        rhyme="Reed by the gate, better to wait.",
        warning="A calm hand first, and a hurried tug worst.",
        praise="You chose the safe way.",
        tags={"inspector", "rhyme", "foreshadowing"},
    ),
}

FIXES = {
    "stool": Fix(
        id="stool",
        sense=3,
        power=2,
        text="lifted the {calendar} back to the wall and tied it with a steady knot",
        fail="lifted the {calendar} back, but the torn page still hung crooked",
        qa_text="lifted the calendar back and tied it with a steady knot",
        tags={"fix", "stool"},
    ),
    "tape": Fix(
        id="tape",
        sense=2,
        power=1,
        text="smoothed the {calendar} with wide hands and pressed the loose corner flat",
        fail="smoothed the {calendar}, but the bend was too deep to hide",
        qa_text="smoothed the calendar and pressed the loose corner flat",
        tags={"fix", "tape"},
    ),
    "pins": Fix(
        id="pins",
        sense=3,
        power=2,
        text="found two small pins and hung the {calendar} straight again",
        fail="used the pins, but the paper had already wrinkled too much",
        qa_text="found two small pins and hung the calendar straight again",
        tags={"fix", "pins"},
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Lena", "Tessa", "Ivy"]
BOY_NAMES = ["Oren", "Bram", "Joss", "Perrin", "Leif"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for v in VILLAGES:
        for c in CALENDARS:
            for i in INSPECTORS:
                combos.append((v, c, i))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about lowering a calendar.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--calendar", choices=CALENDARS)
    ap.add_argument("--inspector", choices=INSPECTORS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.village is None or c[0] == args.village)
              and (args.calendar is None or c[1] == args.calendar)
              and (args.inspector is None or c[2] == args.inspector)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, calendar, inspector = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = gender
    adult_name = args.adult or "Grandma"
    adult_type = "woman"
    return StoryParams(
        village=village,
        calendar=calendar,
        inspector=inspector,
        helper_name=helper_name,
        helper_type=helper_type,
        adult_name=adult_name,
        adult_type=adult_type,
        fix=fix,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the words "lower", '
        f'"calendar", and "inspector".',
        f"Tell a small village story where {f['helper'].id} must lower the "
        f"{f['calendar_cfg'].label} before {f['inspector_cfg'].label} arrives.",
        f"Write a rhyme-filled tale with foreshadowing and conflict, ending with "
        f"a safe way to lower a hanging calendar.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper, adult, inspector = f["helper"], f["adult"], f["inspector"]
    cal = f["calendar_cfg"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {helper.id}, {adult.id}, and {inspector.id}, all in a village with a hanging calendar."),
        ("Why was the inspector's warning important?",
         f"The warning mattered because the calendar was high and fragile. A quick tug could make it fall and wrinkle the pages."),
        ("What did the helper need to do?",
         f"{helper.id} needed to lower the calendar carefully so the dates stayed neat."),
    ]
    if f["outcome"] == "safe":
        qa.append((
            "How did they avoid trouble?",
            f"They used a careful method and the calendar came down without tearing. The stool and steady hands kept the month in order."
        ))
    else:
        qa.append((
            "What went wrong?",
            f"The calendar slipped down too fast and a page bent. The adult fixed it, but the story shows why slow hands mattered."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the calendar lowered and the room calm again. The inspector could see the dates straight and ready for the next day."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["calendar_cfg"].tags) | set(f["inspector_cfg"].tags) | set(f["fix"].tags)
    out: list[tuple[str, str]] = []
    if "calendar" in tags:
        out.append(("What is a calendar?",
                    "A calendar is a chart of days and dates. People use it to remember what comes next."))
    if "inspector" in tags:
        out.append(("What does an inspector do?",
                    "An inspector looks closely to check whether something is safe, neat, or done the right way."))
    if "rhyme" in tags:
        out.append(("What is rhyme?",
                    "Rhyme is when words sound alike at the end, like day and way. It makes stories sing."))
    if "foreshadowing" in tags:
        out.append(("What is foreshadowing?",
                    "Foreshadowing is a small clue that hints something may happen later. It helps the reader pay attention."))
    if "fix" in tags:
        out.append(("Why use a stool for a high job?",
                    "A stool helps someone reach a high place safely. It is better than stretching and tugging."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,C,I) :- village(V), calendar(C), inspector(I).

safe(C) :- fragile(C), lowerable(C).
warns(I) :- inspector(I).
outcome(safe) :- safe(calendar), not fallen(calendar).
outcome(mended) :- fallen(calendar).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for c in CALENDARS:
        lines.append(asp.fact("calendar", c))
        if CALENDARS[c].fragile:
            lines.append(asp.fact("fragile", c))
        if CALENDARS[c].lowerable:
            lines.append(asp.fact("lowerable", c))
    for i in INSPECTORS:
        lines.append(asp.fact("inspector", i))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("fallen", "calendar") if params.delay else ""
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(
            StoryParams(
                village="hill",
                calendar="market",
                inspector="moss",
                helper_name="Mira",
                helper_type="girl",
                adult_name="Grandma",
                adult_type="woman",
                fix="stool",
            )
        )
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(
        village="hill",
        calendar="market",
        inspector="moss",
        helper_name="Mira",
        helper_type="girl",
        adult_name="Grandma",
        adult_type="woman",
        fix="stool",
        delay=0,
    ),
    StoryParams(
        village="river",
        calendar="feast",
        inspector="reed",
        helper_name="Oren",
        helper_type="boy",
        adult_name="Grandma",
        adult_type="woman",
        fix="pins",
        delay=1,
    ),
]


def generate(params: StoryParams) -> StorySample:
    for key in ("village", "calendar", "inspector", "fix"):
        if not hasattr(params, key):
            raise StoryError(f"Missing required story parameter: {key}")
    if params.calendar not in CALENDARS or params.inspector not in INSPECTORS or params.fix not in FIXES:
        raise StoryError("(Invalid parameter choice.)")
    world = tell(
        village=VILLAGES[params.village],
        cal_cfg=CALENDARS[params.calendar],
        inspector_cfg=INSPECTORS[params.inspector],
        fix=FIXES[params.fix],
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        adult_name=params.adult_name,
        adult_type=params.adult_type,
        delay=params.delay,
        helper_age=params.helper_age,
        adult_age=params.adult_age,
        helper_care=params.helper_care,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (village, calendar, inspector) combos:\n")
        for v, c, i in combos:
            print(f"  {v:8} {c:8} {i}")
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
            header = f"### {p.helper_name}: {p.calendar} in {p.village}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
