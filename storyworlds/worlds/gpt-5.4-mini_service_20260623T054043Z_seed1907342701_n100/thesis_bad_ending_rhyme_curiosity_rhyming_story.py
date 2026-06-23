#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260623T054043Z_seed1907342701_n100/thesis_bad_ending_rhyme_curiosity_rhyming_story.py
===============================================================================================================================

A tiny rhyming storyworld about a curious child, a thesis, and a bad ending.
The child can choose a careful path or a careless one, and the world state
drives the ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    owner: str = ""
    location: str = ""
    carried_by: str = ""
    fragile: bool = False
    protective: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    adult: object | None = None
    child: object | None = None
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
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    id: str
    label: str
    breeze: bool = False
    wet: bool = False
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    verb: str
    risk: str
    consequence: str
    ending: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Helper:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    setting: str
    problem: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str = "curious"
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "attic": Setting(id="attic", label="the dusty attic", breeze=True, wet=False, affords={"paper"}),
    "porch": Setting(id="porch", label="the front porch", breeze=True, wet=True, affords={"paper", "rain"}),
    "kitchen": Setting(id="kitchen", label="the sunny kitchen", breeze=False, wet=False, affords={"paper"}),
    "garden": Setting(id="garden", label="the little garden", breeze=True, wet=True, affords={"paper", "rain"}),
}

PROBLEMS = {
    "paper": Problem(
        id="paper",
        verb="write a thesis",
        risk="the pages would fly",
        consequence="the pages would scatter",
        ending="the thesis went skittering away",
        tags={"paper", "wind", "thesis"},
    ),
    "rain": Problem(
        id="rain",
        verb="finish the thesis outside",
        risk="the paper would soak",
        consequence="the pages would blur",
        ending="the thesis turned soggy and sad",
        tags={"rain", "wet", "thesis"},
    ),
}

HELPERS = {
    "paperweight": Helper(
        id="paperweight",
        label="a paperweight",
        phrase="a heavy paperweight",
        protects={"paper"},
        tags={"paperweight", "thesis"},
    ),
    "folder": Helper(
        id="folder",
        label="a folder",
        phrase="a sturdy folder",
        protects={"paper", "rain"},
        tags={"folder", "thesis"},
    ),
    "umbrella": Helper(
        id="umbrella",
        label="an umbrella",
        phrase="an umbrella",
        protects={"rain"},
        tags={"umbrella", "rain"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Theo", "Sam"]
TRAITS = ["curious", "bright-eyed", "restless", "dreamy", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            if pid not in s.affords:
                continue
            for hid, h in HELPERS.items():
                if p.id in h.protects or "thesis" in h.tags:
                    out.append((sid, pid, hid))
    return out


def helper_works(problem: Problem, helper: Helper) -> bool:
    return problem.id in helper.protects or (problem.id == "paper" and "thesis" in helper.tags)


def problem_at_risk(setting: Setting, problem: Problem) -> bool:
    return problem.id in setting.affords


def advise(world: World, child: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    if problem.id == "paper":
        world.say(
            f"{child.id} leaned over the pages and wanted to {problem.verb}, "
            f"but {child.pronoun('possessive')} {parent.label.lower()} frowned."
        )
    else:
        world.say(
            f"{child.id} wanted to {problem.verb}, but {child.pronoun('possessive')} "
            f"{parent.label.lower()} pointed at the damp air."
        )


def warn(world: World, parent: Entity, child: Entity, problem: Problem) -> None:
    world.say(
        f'"Careful," {parent.label} said. "If you keep going, {problem.consequence}."'
    )


def ignore(world: World, child: Entity) -> None:
    child.memes["stubborn"] += 1
    world.say(f"{child.id} smiled, shrugged, and kept going anyway.")


def forward(world: World, child: Entity, problem: Problem) -> list[str]:
    out = []
    if problem.id == "paper" and child.meters.get("wind", 0.0) >= THRESHOLD:
        sig = ("scatter", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["lost_pages"] = child.meters.get("lost_pages", 0.0) + 1
            out.append("pages scatter")
    if problem.id == "rain" and child.meters.get("wet", 0.0) >= THRESHOLD:
        sig = ("soak", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["blurred_pages"] = child.meters.get("blurred_pages", 0.0) + 1
            out.append("pages soak")
    return out


def apply_problem(world: World, child: Entity, problem: Problem) -> None:
    if problem.id == "paper":
        child.meters["wind"] = child.meters.get("wind", 0.0) + 1
    else:
        child.meters["wet"] = child.meters.get("wet", 0.0) + 1
    forward(world, child, problem)


def offer_helper(world: World, parent: Entity, child: Entity, problem: Problem, helper: Helper) -> bool:
    if not helper_works(problem, helper):
        return False
    world.add(Entity(
        id=helper.id,
        kind="thing",
        type="thing",
        label=helper.label,
        phrase=helper.phrase,
        protective=True,
        tags=set(helper.tags),
        meters={},
        memes={},
    ))
    world.get(helper.id).carried_by = child.id
    world.say(
        f'{parent.label} held up {helper.phrase} and said, "Let us use this for the thesis."'
    )
    return True


def finish_bad(world: World, child: Entity, parent: Entity, problem: Problem) -> None:
    if problem.id == "paper":
        world.say(
            f"A sudden gust tugged the top sheet free, and the thesis went skittering away."
        )
        world.say(
            f"{child.id} ran after the pages, but they danced under a bench and out of sight."
        )
    else:
        world.say(
            f"The rain came harder, and the thesis turned soggy and sad in {child.pronoun('possessive')} hands."
        )
        world.say(
            f"{parent.label.capitalize()} wrapped an arm around {child.id}, and they watched the ink melt into gray."
        )


def finish_good(world: World, child: Entity, parent: Entity, problem: Problem, helper: Helper) -> None:
    world.say(
        f"With {helper.phrase}, {child.id} kept going and the thesis stayed safe."
    )
    world.say(
        f"At the end, {child.id} set the neat pages on the table, bright and still."
    )


def tell(setting: Setting, problem: Problem, helper: Helper,
         name: str = "Mia", gender: str = "girl", parent: str = "mother",
         trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, traits=[trait]))
    adult = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}", meters={}, memes={}))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["parent"] = adult

    world.say(
        f"In {setting.label}, {child.id} was {trait} and full of cheer, "
        f"with a thesis to finish before night grew near."
    )
    world.say(
        f"{child.id} tapped {child.pronoun('possessive')} pen and started to write, "
        f"but the air could turn tricky before the end of the light."
    )
    world.para()
    advise(world, child, adult, problem)
    warn(world, adult, child, problem)
    ignore(world, child)

    world.para()
    if offer_helper(world, adult, child, problem, helper):
        if problem.id == "paper":
            child.meters["wind"] = child.meters.get("wind", 0.0) + 1
        else:
            child.meters["wet"] = child.meters.get("wet", 0.0) + 1
        if helper_works(problem, helper):
            if problem.id == "paper":
                # Still a bad ending: helper is not enough for the breeze if the child ignores care.
                world.say(
                    f"But the paper still lifted, for curiosity hurried the child right on."
                )
                finish_bad(world, child, adult, problem)
                outcome = "bad"
            else:
                world.say(
                    f"But the rain found a crack in the plan, and the ink began to run."
                )
                finish_bad(world, child, adult, problem)
                outcome = "bad"
        else:
            finish_bad(world, child, adult, problem)
            outcome = "bad"
    else:
        finish_bad(world, child, adult, problem)
        outcome = "bad"

    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        f'Write a rhyming story for a child named {child.id} who wants to {problem.verb} in {setting.label}, and include the word "thesis".',
        f"Tell a curious little story where {child.id} keeps working on a thesis, but the weather or breeze causes a bad ending.",
        f'Write a short rhyming tale about curiosity, a thesis, and a sad twist at {setting.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    problem = f["problem"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"What was {child.id} trying to do in {setting.label}?",
            answer=f"{child.id} was trying to {problem.verb}. It was a thesis the child wanted to finish, but the place was not steady enough.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {child.id}?",
            answer=f"{parent.label.capitalize()} warned {child.id} because the air could make trouble for the thesis. The child was curious, but the pages could be lost or ruined.",
        ),
        QAItem(
            question=f"What helper did {parent.label} offer?",
            answer=f"{parent.label.capitalize()} offered {helper.phrase}. It was meant to help, but the story still ends badly because the problem wins.",
        ),
        QAItem(
            question=f"How did the story end for the thesis?",
            answer=f"The thesis ended in a bad way: the pages were scattered or soggy, and {child.id} had to look at the mess. The last image proves the work did not stay safe.",
        ),
    ]
    if f["problem"].id == "paper":
        qa.append(QAItem(
            question=f"What did the wind do to the thesis pages?",
            answer=f"The wind tugged the thesis pages free and sent them skittering away. Curiosity kept {child.id} moving, but it did not keep the paper still.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did the rain do to the thesis pages?",
            answer=f"The rain soaked the thesis pages and blurred the ink. That made the ending sad, because the writing could no longer stay neat.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thesis?",
            answer="A thesis is a piece of writing where someone explains an idea or tries to prove something with words and careful thought.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and asking questions. A curious person keeps looking and learning.",
        ),
        QAItem(
            question="What can wind do to paper?",
            answer="Wind can blow paper around and make it fly away. That is why loose pages need care.",
        ),
        QAItem(
            question="What can rain do to paper?",
            answer="Rain can soak paper and make the ink run. Wet paper is hard to read and hard to save.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", problem="paper", helper="paperweight", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="porch", problem="rain", helper="folder", name="Leo", gender="boy", parent="father", trait="eager"),
    StoryParams(setting="garden", problem="paper", helper="folder", name="Nora", gender="girl", parent="mother", trait="dreamy"),
    StoryParams(setting="kitchen", problem="paper", helper="paperweight", name="Ben", gender="boy", parent="father", trait="restless"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or "curious"
    return StoryParams(setting=setting, problem=problem, helper=helper, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.helper not in HELPERS:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(HELPERS, params.helper), params.name, params.gender, params.parent, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
valid(S,P,H) :- setting(S), problem(P), helper(H), afford(S,P), works(H,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in s.affords:
            lines.append(asp.fact("afford", sid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for p in h.protects:
            lines.append(asp.fact("works", hid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generate(CURATED[0]))
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
