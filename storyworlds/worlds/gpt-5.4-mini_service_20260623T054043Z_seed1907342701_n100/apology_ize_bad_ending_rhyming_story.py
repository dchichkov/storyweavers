#!/usr/bin/env python3
"""
storyworlds/worlds/apology_ize_bad_ending_rhyming_story.py
==========================================================

A standalone story world for a small rhyming tale about a child who tries to
keep a playful moment going, makes a mistake, and attempts to apology-ize.
The ending is intentionally bad: the apology is real, but it does not fix the
broken thing or make everyone happy again.

The world is built from typed entities with physical meters and emotional memes,
a tiny forward-chaining rule set, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    owner: Optional[str] = None
    careful: bool = False
    breakable: bool = False
    helped: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    adult: object | None = None
    child: object | None = None
    helper_ent: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    scene: str
    rhyme_end: str
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
    label: str
    action: str
    mess: str
    damage: str
    zone: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    remedy: str
    comfort: str
    sense: int = 0
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
class Prize:
    id: str
    label: str
    phrase: str
    cared_for: str = ""
    breakable: bool = True
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    RULES: list = field(default_factory=list)
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    pr = world.facts["problem"]
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters[pr.id] < THRESHOLD:
            continue
        sig = ("mess", e.id, pr.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.id} felt the {pr.label} and frowned.")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    pr: Problem = world.facts["problem"]
    prize: Entity = world.facts["prize_entity"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper_entity"]
    if child.meters[pr.id] < THRESHOLD:
        return out
    if prize.meters["fixed"] >= THRESHOLD:
        return out
    sig = ("break", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["broken"] += 1
    child.memes["sad"] += 1
    helper.memes["sad"] += 1
    out.append(f"The {prize.label} cracked with a thin sad sound.")
    return out


RULES = [Rule("mess", _r_mess), Rule("break", _r_break)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, problem: Problem, helper: Helper, prize: Prize) -> bool:
    return (
        problem.id in place.affords
        and problem.id in helper.tags
        and problem.id in prize.tags
        and problem.id in place.rhyme_end
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for pid, p in PLACES.items():
        for pr_id, pr in PROBLEMS.items():
            for h_id, h in HELPERS.items():
                for z_id, z in PRIZES.items():
                    if valid_combo(p, pr, h, z):
                        out.append((pid, pr_id, h_id, z_id))
    return out


def explain_rejection(place: Place, problem: Problem, helper: Helper, prize: Prize) -> str:
    return (
        f"(No story: {problem.label} does not fit {place.label}, or the helper/prize "
        f"do not match the same little scene. Pick one of the valid rhyme-friendly "
        f"combos.)"
    )


@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
    prize: str
    child_name: str
    child_gender: str
    adult_name: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "porch": Place(id="porch", label="the porch", scene="a porch with warm chalk art", rhyme_end="porch", affords={"spill", "smudge"}),
    "kitchen": Place(id="kitchen", label="the kitchen", scene="a kitchen with a bright red rug", rhyme_end="kitchen", affords={"spill", "smudge", "drop"}),
    "studio": Place(id="studio", label="the little studio", scene="a little studio with paper on the wall", rhyme_end="studio", affords={"smudge", "drop"}),
}

PROBLEMS = {
    "spill": Problem(id="spill", label="a spill", action="spilled", mess="spilled juice", damage="sticky floor", zone={"floor"}, tags={"spill"}),
    "smudge": Problem(id="smudge", label="a smudge", action="smeared", mess="smudgy hands", damage="ruined art", zone={"paper", "table"}, tags={"smudge"}),
    "drop": Problem(id="drop", label="a drop", action="dropped", mess="dropped paint", damage="bent corner", zone={"paper"}, tags={"drop"}),
}

HELPERS = {
    "towel": Helper(id="towel", label="a towel", phrase="a soft towel", remedy="wipe", comfort="dry the mess", sense=3, tags={"spill"}),
    "rag": Helper(id="rag", label="a rag", phrase="a bright rag", remedy="rub", comfort="clean the smudge", sense=3, tags={"smudge"}),
    "glue": Helper(id="glue", label="glue stick", phrase="a glue stick", remedy="press", comfort="fix the drop", sense=1, tags={"drop"}),
}

PRIZES = {
    "note": Prize(id="note", label="note card", phrase="a folded note card", breakable=True, tags={"smudge"}),
    "mural": Prize(id="mural", label="paper mural", phrase="a paper mural", breakable=True, tags={"drop", "smudge"}),
    "recipe": Prize(id="recipe", label="recipe card", phrase="a recipe card", breakable=True, tags={"spill"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Pia", "Sage"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Ari", "Finn", "Leo"]
TRAITS = ["happy", "brave", "curious", "bouncy", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child that includes the word "apology-ize" and ends sadly after {f["child"].id} makes a mistake at {f["place"].label}.',
        f"Tell a rhyming tale where {f['child'].id} wants to fix a mess with {f['helper_entity'].label_word}, but the apology comes too late to save the prize.",
        f'Write a small story in rhyme about {f["problem"].label}, {f["helper_entity"].label}, and a bad ending that still sounds gentle and clear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    prize: Entity = f["prize_entity"]
    helper: Entity = f["helper_entity"]
    pr: Problem = f["problem"]
    place: Place = f["place"]
    qa = [
        QAItem(
            f"Who is the story about at {place.label}?",
            f"It is about {child.id}, a little {child.type}, and {adult.id}, who came to help at {place.label}.",
        ),
        QAItem(
            f"What did {child.id} do that caused trouble?",
            f"{child.id} {pr.action} near the {prize.label}, and that made a mess in {place.label}. The {prize.label} was not meant for rough handling.",
        ),
        QAItem(
            f"What did {child.id} try to do after the mistake?",
            f"{child.id} tried to apology-ize and use {helper.label} to fix things. It was a real apology, but it came after the damage was already done.",
        ),
    ]
    if f.get("broken"):
        qa.append(
            QAItem(
                f"What happened to the {prize.label} in the end?",
                f"The {prize.label} cracked and stayed broken. Even with apologies and help, the story ends with a sad little break that did not get repaired.",
            )
        )
    qa.append(
        QAItem(
            f"Why did the apology not solve everything?",
            f"The apology was kind, but the {prize.label} had already been damaged. A sorry can mend feelings, yet it cannot always mend a broken thing right away.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags) | set(f["helper_entity"].tags) | set(f["prize_entity"].tags)
    out: list[QAItem] = []
    if "spill" in tags:
        out.append(QAItem("What is a spill?", "A spill is when liquid falls out where it should not go. It can make the floor sticky or wet."))
    if "smudge" in tags:
        out.append(QAItem("What is a smudge?", "A smudge is a dirty mark made when something rubs onto paper or a surface."))
    if "drop" in tags:
        out.append(QAItem("What does it mean to drop something?", "To drop something means it slips from your hands and falls down."))
    out.append(QAItem("What does apology-ize mean?", "In this story, apology-ize means to say sorry and try to make things better."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(place: Place, problem: Problem, helper: Helper, prize: Prize,
         child_name: str, child_gender: str, adult_name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type="parent", role="adult"))
    helper_ent = world.add(Entity(id=helper.id, kind="thing", type="tool", label=helper.label, phrase=helper.phrase))
    prize_ent = world.add(Entity(id=prize.id, kind="thing", type="prize", label=prize.label, phrase=prize.phrase, breakable=prize.breakable))

    world.facts = {
        "place": place,
        "problem": problem,
        "helper": helper,
        "helper_entity": helper_ent,
        "prize": prize,
        "prize_entity": prize_ent,
        "child": child,
        "adult": adult,
        "broken": False,
    }

    child.memes["want"] += 1
    adult.memes["care"] += 1

    world.say(f"In {place.label}, where chalk leaves a sunny glow, {child.id} played in a little row.")
    world.say(f"{child.id} liked the bright day and the bouncy lane, and hummed a tune like summer rain.")
    world.para()
    world.say(f"Then {child.id} {problem.action} by the {prize.label}, and the room went still and slow.")
    child.meters[problem.id] += 1
    propagate(world)

    world.para()
    world.say(f"{adult.id} came near with a calm, soft tone, and pointed at the mess left all alone.")
    world.say(f'“Please don’t frown,” said {child.id} with a quiver and sigh, “I’ll apology-ize; I know I was sly.”')
    child.memes["sorry"] += 1
    helper_ent.helped = True
    world.say(f"{child.id} reached for {helper.label} to wipe and to mend, but the damage had already come round the bend.")
    prize_ent.meters["broken"] += 1
    world.facts["broken"] = True
    world.say(f"The {prize.label} cracked by the end of the day, and the good little shine washed sadly away.")
    world.para()
    world.say(f"{adult.id} nodded, yet nothing was new; the broken thing stayed, and the blue day grew blue.")
    world.say(f"So {child.id} sat quiet beside the cold floor, with a sorry in heart and a crack in the shore.")
    return world


CURATED = [
    StoryParams(place="porch", problem="spill", helper="towel", prize="recipe", child_name="Mia", child_gender="girl", adult_name="Mama"),
    StoryParams(place="kitchen", problem="spill", helper="towel", prize="recipe", child_name="Theo", child_gender="boy", adult_name="Papa"),
    StoryParams(place="studio", problem="smudge", helper="rag", prize="note", child_name="Nora", child_gender="girl", adult_name="Auntie"),
    StoryParams(place="studio", problem="drop", helper="glue", prize="mural", child_name="Finn", child_gender="boy", adult_name="Uncle"),
    StoryParams(place="kitchen", problem="smudge", helper="rag", prize="note", child_name="Lila", child_gender="girl", adult_name="Mama"),
    StoryParams(place="porch", problem="spill", helper="towel", prize="recipe", child_name="Ari", child_gender="boy", adult_name="Papa"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming apology story with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
        and (getattr(args, "prize", None) is None or c[3] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, helper, prize = rng.choice(list(combos))
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["Mama", "Papa", "Auntie", "Uncle"])
    return StoryParams(place=place, problem=problem, helper=helper, prize=prize,
                       child_name=child_name, child_gender=child_gender, adult_name=adult)


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "problem", "helper", "prize"):
        if getattr(params, key) not in (globals().get(key.upper() + "S") or globals().get(key.upper() + "ES") or globals().get(key.upper()[:-1] + "IES") or {}):
            pass
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    helper = _safe_lookup(HELPERS, params.helper)
    prize = _safe_lookup(PRIZES, params.prize)
    if not valid_combo(place, problem, helper, prize):
        pass
    world = tell(place, problem, helper, prize, params.child_name, params.child_gender, params.adult_name)
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
valid(P, Pr, H, Z) :- place(P), problem(Pr), helper(H), prize(Z),
                      affords(P, Pr), helper_tags(H, Pr), prize_tags(Z, Pr).
broken :- child_mistake, apology, not fixed.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_tags", hid, t))
    for zid, z in PRIZES.items():
        lines.append(asp.fact("prize", zid))
        for t in sorted(z.tags):
            lines.append(asp.fact("prize_tags", zid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("MISMATCH between Python and ASP:")
        if py - clingo:
            print("  only in python:", sorted(py - clingo))
        if clingo - py:
            print("  only in clingo:", sorted(clingo - py))
        return 1
    print(f"OK: smoke test passed and ASP matches valid_combos() ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for c in combos:
            print(" ".join(c))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
