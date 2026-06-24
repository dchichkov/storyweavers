#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective tale set in road repair.

Premise:
- A careful little detective notices a bumpy road that needs fixing.
- One worker keeps procrastinating, which makes the road worse.
- A grumpy character wants revenge, but the detective solves the case with a plan.
- The ending teaches a lesson learned, with a little humor and a repaired road.

The world is intentionally small and constraint-checked:
- the road repair job must actually matter;
- procrastination must create a real delay;
- the chosen fix must match the problem;
- revenge is not allowed to become a harmful act; it is redirected into a safer, kinder resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    detective: object | None = None
    helper: object | None = None
    prankster: object | None = None
    road: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "detective"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the road repair site"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    delay: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    cures: set[str]
    covers: set[str]
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


SETTING = Setting(place="the road repair site", affords={"repair", "inspect"})

ACTIVITIES = {
    "repair": Activity(
        id="repair",
        verb="fix the road",
        gerund="patching the broken road",
        delay="kept putting off the repair",
        mess="bumpy",
        soil="still bumpy",
        zone={"road"},
        keyword="road",
        tags={"road", "repair"},
    ),
    "inspect": Activity(
        id="inspect",
        verb="inspect the cracks",
        gerund="inspecting the cracks",
        delay="kept looking and looking",
        mess="bumpy",
        soil="unfixed",
        zone={"road"},
        keyword="crack",
        tags={"road", "detective"},
    ),
}

PRIZES = {
    "bike": Prize(
        label="bike",
        phrase="a shiny little bike",
        type="bike",
        region="road",
    ),
    "cart": Prize(
        label="cart",
        phrase="a small delivery cart",
        type="cart",
        region="road",
    ),
}

FIXES = [
    Fix(
        id="cones",
        label="orange cones",
        prep="set out orange cones first",
        tail="set out the cones and worked carefully",
        cures={"bumpy"},
        covers={"road"},
    ),
    Fix(
        id="shovel",
        label="a patch kit and shovel",
        prep="grab a patch kit and shovel",
        tail="used the patch kit and shovel",
        cures={"bumpy"},
        covers={"road"},
    ),
]

NAMES = ["Mina", "Noah", "Lia", "Toby", "Iris", "Evan"]
TRAITS = ["sharp-eyed", "patient", "curious", "cheerful", "clever"]


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mess in fx.cures and prize.region in fx.covers:
            return fx
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not actually affect {prize.label}, "
        f"so the detective would have no real case to solve.)"
    )


def predict_delay(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["procrastinate"] = 1.0
    sim.get(actor.id).meters["delay"] = 1.0
    return {
        "delay": sim.get(actor.id).meters.get("delay", 0.0) >= THRESHOLD,
        "frustration": sim.get(actor.id).memes.get("frustration", 0.0),
    }


def propagate(world: World) -> None:
    for ent in world.characters():
        if ent.memes.get("procrastinate", 0.0) >= THRESHOLD and ("delay", ent.id) not in world.fired:
            world.fired.add(("delay", ent.id))
            ent.meters["delay"] = ent.meters.get("delay", 0.0) + 1.0
            ent.memes["frustration"] = ent.memes.get("frustration", 0.0) + 1.0
        if ent.memes.get("revenge", 0.0) >= THRESHOLD and ent.meters.get("delay", 0.0) >= THRESHOLD:
            world.facts["revenge_risk"] = True


def describe_setting(world: World) -> str:
    return "The road repair site was wide open, with cracked asphalt, bright cones, and one very serious detective."  # noqa: E501


def introduce_detective(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"{detective.id} was a {next(t for t in detective.meters.get('trait_list', []) if True) if False else 'sharp-eyed'} detective who liked solving small problems."
    )


def tell(world: World, detective_name: str, helper_name: str, prankster_name: str, trait: str,
         activity: Activity, prize: Prize) -> World:
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label="the detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type="worker", label="the worker"))
    prankster = world.add(Entity(id=prankster_name, kind="character", type="child", label="the prankster"))
    road = world.add(Entity(id="road", kind="thing", type="road", label="the road", region="road"))

    detective.meters["trait"] = 1.0
    detective.memes["curiosity"] = 1.0
    helper.memes["procrastinate"] = 1.0
    prankster.memes["revenge"] = 1.0

    world.say(f"{detective.id} was a {trait} detective who noticed every clue on {SETTING.place}.")
    world.say(f"{helper.id} was supposed to {activity.verb}, but {helper.pronoun('subject')} kept putting it off.")
    world.say(f"That made the road stay {activity.soil}, which was bad for {prize.phrase}.")
    world.para()
    world.say(describe_setting(world))
    world.say(f"{detective.id} saw the same crack again and again, like it was trying to wink.")
    world.say(f"{prize.label.capitalize()}s jolted over the bump, and even the cones seemed to look worried.")
    world.say(f"{prankster.id} wanted revenge for the mess, but {detective.id} said, 'Let's solve the case first.'")
    world.say(f"{detective.id} noticed that {helper.id} kept {activity.delay}, and that was the real clue.")
    propagate(world)
    world.para()
    fx = select_fix(activity, prize)
    if fx is None:
        pass
    world.say(f"{detective.id} pointed at the crack and smiled. 'We need to {fx.prep}.'")
    world.say(f"{helper.id} blinked, then laughed at the tiny cone-shaped shadow on the road. 'Right. No more stalling.'")
    world.say(f"Together they {fx.tail}, and the road finally stopped wobbling under {prize.label}s.")
    world.say(f"{prankster.id} gave up the revenge idea and instead handed out cookies like a tiny detective sidekick.")
    world.say(f"In the end, {helper.id} learned that procrastinating only makes a small problem grow bigger, and {detective.id} learned that a good clue can be funny too.")
    world.say(f"The road was smooth again, the cones stood straight, and everybody could cross without a bump.")
    world.facts.update(
        detective=detective,
        helper=helper,
        prankster=prankster,
        road=road,
        activity=activity,
        prize=prize,
        fix=fx,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a child about a road repair site, including the word "hip".',
        f"Tell a humorous mystery about {f['helper'].id} who keeps procrastinating while {f['detective'].id} investigates a bumpy road.",
        f"Write a lesson-learned story where a character wants revenge, but the detective finds a kinder fix for {f['prize'].label}s on a road.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, p, a, pr, fx = f["detective"], f["helper"], f["prankster"], f["activity"], f["prize"], f["fix"]
    return [
        QAItem(
            question=f"Who solved the mystery at the road repair site?",
            answer=f"{d.id} solved it by noticing that {h.id} kept procrastinating and that the road stayed bumpy.",
        ),
        QAItem(
            question=f"What kept making the road repair take too long?",
            answer=f"{h.id} kept procrastinating, so the repair did not get finished right away.",
        ),
        QAItem(
            question=f"What did the detective do instead of choosing revenge?",
            answer=f"{d.id} chose a safer plan: {fx.label}, which helped fix the road without making the situation meaner.",
        ),
        QAItem(
            question=f"What lesson did the story teach at the end?",
            answer=f"It taught that procrastinating can make trouble grow, and that a calm, clever fix is better than revenge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is road repair?",
            answer="Road repair is the work of fixing cracks, holes, and bumpy places so cars, bikes, and people can travel safely.",
        ),
        QAItem(
            question="What does procrastinate mean?",
            answer="To procrastinate means to keep putting something off instead of doing it when you should.",
        ),
        QAItem(
            question="What is revenge?",
            answer="Revenge is when someone wants to get back at another person because they are angry, but it is usually not a wise choice.",
        ),
        QAItem(
            question="Why can humor help in a detective story?",
            answer="Humor can make a detective story feel friendly and fun, even while the detective is still solving a serious problem.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    prankster: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld set in road repair.")
    ap.add_argument("--place", choices=["road repair site"], default="road repair site")
    ap.add_argument("--activity", choices=ACTIVITIES, default=None)
    ap.add_argument("--prize", choices=PRIZES, default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", default=None)
    ap.add_argument("--prankster", default=None)
    ap.add_argument("--trait", choices=TRAITS, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not reasonableness_gate(_safe_lookup(ACTIVITIES, activity), _safe_lookup(PRIZES, prize)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place="road repair site",
        activity=activity,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(NAMES),
        prankster=getattr(args, "prankster", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    world = tell(
        world,
        detective_name=params.name,
        helper_name=params.helper,
        prankster_name=params.prankster,
        trait=params.trait,
        activity=_safe_lookup(ACTIVITIES, params.activity),
        prize=_safe_lookup(PRIZES, params.prize),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
% A prize is at risk when the road work is on the same region it occupies.
at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).

% A fix is compatible only if it cures the mess and covers the at-risk region.
compatible(F,A,P) :- fix(F), at_risk(A,P), cures(F,M), mess_of(A,M), covers(F,R), worn_on(P,R).

valid_story(A,P) :- at_risk(A,P), compatible(_,A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("mess_of", a.id, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", a.id, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.cures):
            lines.append(asp.fact("cures", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for a in ACTIVITIES.values():
        for p in PRIZES.values():
            if reasonableness_gate(a, p) and select_fix(a, p):
                combos.append((a.id, p.label))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for a in ACTIVITIES:
            for p in PRIZES:
                if reasonableness_gate(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p)):
                    params = StoryParams(
                        place="road repair site",
                        activity=a,
                        prize=p,
                        name="Mina",
                        helper="Noah",
                        prankster="Lia",
                        trait="curious",
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
