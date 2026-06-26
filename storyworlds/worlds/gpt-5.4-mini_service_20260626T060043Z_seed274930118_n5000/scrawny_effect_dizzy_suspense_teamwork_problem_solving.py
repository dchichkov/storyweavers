#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scrawny_effect_dizzy_suspense_teamwork_problem_solving.py
===============================================================================================================

A small standalone story world in a rhyming-story style:
a scrawny little helper faces a dizzying effect, a suspenseful problem,
and a teamwork-based fix that the world model can actually justify.

Seed-inspired anchor words:
- scrawny
- effect
- dizzy

Narrative instruments:
- Suspense
- Teamwork
- Problem Solving
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    noun: str
    verb: str
    danger: str
    suspense: str
    zone: str
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
class SolutionGear:
    id: str
    label: str
    prep: str
    tail: str
    solves: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = self.zone
        return clone


def rhyming_tagline(problem: Problem, setting: Setting) -> str:
    return {
        "attic": "High in the attic, the shadows could mock it.",
        "garden": "In the garden breeze, the leaves did tease.",
        "shed": "In the little shed, soft beams turned red.",
        "pier": "By the pier so wide, the waves did glide.",
    }.get(setting.place, "The little place was bright, and ready for light.")


def problem_at_risk(problem: Problem, gear: SolutionGear) -> bool:
    return problem.id in gear.solves


def select_gear(problem: Problem) -> Optional[SolutionGear]:
    for gear in GEAR:
        if problem.id in gear.solves:
            return gear
    return None


def predict_resolution(world: World, hero: Entity, problem: Problem, gear: SolutionGear) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem, narrate=False)
    _use_gear(sim, sim.get(hero.id), problem, gear, narrate=False)
    helper = sim.entities.get("Helper")
    return {
        "solved": bool(sim.facts.get("solved")),
        "dizzy": hero.memes.get("dizzy", 0.0),
        "teamwork": helper.memes.get("teamwork", 0.0) if helper else 0.0,
    }


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    world.zone = problem.zone
    hero.memes["suspense"] += 1
    hero.meters[problem.keyword] += 1
    hero.meters["trouble"] += 1
    if narrate:
        world.say(problem.suspense)


def _dizzy_effect(world: World, hero: Entity, problem: Problem) -> None:
    if hero.meters[problem.keyword] < THRESHOLD:
        return
    hero.memes["dizzy"] += 1
    world.say(
        f"The strange effect made {hero.id} feel dizzy, and {hero.pronoun('possessive')} paws went wobbly."
    )


def _teamwork(world: World, hero: Entity, helper: Entity, gear: SolutionGear) -> None:
    helper.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1
    world.say(
        f"Then {helper.id} hurried in with a grin, and they worked as a team to try {gear.prep}."
    )


def _use_gear(world: World, hero: Entity, problem: Problem, gear: SolutionGear, narrate: bool = True) -> None:
    if problem.id not in gear.solves:
        return
    if hero.meters[problem.keyword] < THRESHOLD:
        return
    if world.facts.get("solved"):
        return
    world.facts["solved"] = True
    hero.memes["suspense"] = 0.0
    hero.memes["dizzy"] = 0.0
    if narrate:
        world.say(
            f"Together they {gear.tail}, and the trouble was tidy as could be."
        )


def tell(setting: Setting, problem: Problem, hero_name: str, helper_name: str, hero_type: str,
         helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["scrawny", "brave"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_name, traits=["kind"]))
    item = world.add(Entity(id="Item", type="thing", label=problem.noun, phrase=problem.noun, caretaker=helper.id))

    world.say(f"{hero.id} was a scrawny little {hero.type}, with a heart full of cheer.")
    world.say(f"{setting.mood} {rhyming_tagline(problem, setting)}")
    world.say(f"{hero.id} loved to help and to solve, to hop and to cheer.")

    world.para()
    world.say(
        f"One day at {setting.place}, {hero.id} found {item.phrase}, and the scene got near."
    )
    _do_problem(world, hero, problem, narrate=True)
    _dizzy_effect(world, hero, problem)
    world.say(
        f"{hero.id} peeked and leaned, but the path looked grim; the fix was not clear."
    )

    world.para()
    world.say(
        f"At last came {helper.id}, with calm eyes bright; they would not let the worry grow."
    )
    gear = select_gear(problem)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    _teamwork(world, hero, helper, gear)
    _use_gear(world, hero, problem, gear, narrate=True)
    world.say(
        f"So {hero.id} and {helper.id} solved it together, and home they did glow."
    )

    world.facts.update(hero=hero, helper=helper, item=item, problem=problem, setting=setting, gear=gear)
    return world


SETTINGS = {
    "attic": Setting(place="the attic", mood="Up high in"),
    "garden": Setting(place="the garden", mood="Out in"),
    "shed": Setting(place="the shed", mood="Inside"),
    "pier": Setting(place="the pier", mood="By"),
}

PROBLEMS = {
    "kite_string": Problem(
        id="kite_string",
        noun="a kite string tied on a high nail",
        verb="reach the kite string",
        danger="the kite could drift away",
        suspense="The string fluttered and twirled, and the little nail looked too tall to touch.",
        zone="high",
        keyword="reach",
        tags={"kite", "string", "wind", "suspense"},
    ),
    "jar_lid": Problem(
        id="jar_lid",
        noun="a jam jar with a stuck lid",
        verb="open the jar",
        danger="the jam could stay locked away",
        suspense="The lid would not budge, though every twist and turn was tried.",
        zone="table",
        keyword="twist",
        tags={"jar", "lid", "problem_solving"},
    ),
    "lantern_hook": Problem(
        id="lantern_hook",
        noun="a lantern hanging on a bent hook",
        verb="free the lantern",
        danger="the dark would stay sleepy and gray",
        suspense="The hook was bent just so, and the lantern swung with a hush-hush sway.",
        zone="hook",
        keyword="lift",
        tags={"lantern", "hook", "twilight", "suspense"},
    ),
}

GEAR = [
    SolutionGear(
        id="stool",
        label="a small stool",
        prep="stacking a small stool beside the shelf",
        tail="stacked the stool, reached the string, and saved the day",
        solves={"kite_string"},
    ),
    SolutionGear(
        id="cloth",
        label="a warm cloth",
        prep="wrapping a warm cloth round the jar",
        tail="wrapped the cloth, loosened the lid, and won the way",
        solves={"jar_lid"},
    ),
    SolutionGear(
        id="hookpole",
        label="a hook pole",
        prep="sliding a hook pole under the lantern",
        tail="lifted the lantern free, and moonlight led the play",
        solves={"lantern_hook"},
    ),
]

HERO_NAMES = ["Pip", "Mina", "Otto", "Lia", "Jory", "Nell"]
HELPER_NAMES = ["Bea", "Toby", "Rin", "Moss", "Jun", "Suri"]
HERO_TYPES = ["mouse", "rabbit", "fox", "chipmunk", "bird"]
HELPER_TYPES = ["fox", "bear", "cat", "dog", "goat"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    helper: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if pid in [g for gear in GEAR for g in gear.solves] and problem.id in setting.affords.union(problem.tags):
                combos.append((place, pid))
    # affordance-based filter is intentionally looser in Python, then tightened below.
    out = []
    for place, pid in combos:
        if select_gear(_safe_lookup(PROBLEMS, pid)) is not None:
            out.append((place, pid))
    return sorted(set(out))


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, setting, gear = f["hero"], f["helper"], f["problem"], f["setting"], f["gear"]
    return [
        QAItem(
            question=f"Who was the scrawny hero in the story at {setting.place}?",
            answer=f"The scrawny hero was {hero.id}, and {hero.id} was the one facing the tricky problem.",
        ),
        QAItem(
            question=f"What problem made {hero.id} feel dizzy?",
            answer=f"{problem.noun.capitalize()} made {hero.id} feel dizzy because the effect of the trouble was wobbly and strange.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They used {gear.label} together, so {hero.id} and {helper.label} could fix the trouble as a team.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and each one helps, so a job can get done more easily.",
        ),
        QAItem(
            question="What does dizzy mean?",
            answer="Dizzy means feeling wobbly or spinning inside, like your head is not steady for a moment.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving is looking at a hard thing, trying a smart idea, and finding a way to fix it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child about a scrawny little helper at {f["setting"].place}.',
        f"Tell a suspenseful, gentle story where {f['hero'].id} feels dizzy but teamwork helps fix {f['problem'].noun}.",
        f'Create a problem-solving rhyme that ends with {f["hero"].id} and {f["helper"].label} smiling together.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: scrawny, dizzy, suspense, teamwork, problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def explain_rejection() -> str:
    return "(No story: that combination would not have a clear problem-and-fix path.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    filtered = [
        (place, pid) for place, pid in combos
        if (getattr(args, "place", None) is None or place == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or pid == getattr(args, "problem", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, pid = rng.choice(filtered)
    return StoryParams(
        place=place,
        problem=pid,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(HERO_TYPES),
        helper_type=getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        params.name,
        params.helper,
        params.hero_type,
        params.helper_type,
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
place(attic;garden;shed;pier).
problem(kite_string;jar_lid;lantern_hook).
gear(stool;cloth;hookpole).

solves(stool,kite_string).
solves(cloth,jar_lid).
solves(hookpole,lantern_hook).

valid(Place,Problem) :- place(Place), problem(Problem), solves(_,Problem).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for pid in g.solves:
            lines.append(asp.fact("solves", g.id, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in [
            StoryParams("attic", "kite_string", "Pip", "Bea", "mouse", "cat"),
            StoryParams("garden", "jar_lid", "Mina", "Toby", "rabbit", "dog"),
            StoryParams("shed", "lantern_hook", "Otto", "Rin", "fox", "goat"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
