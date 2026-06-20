#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spam_composition_rhyme_sound_effects_bedtime_story.py
=====================================================================================

A standalone storyworld for a tiny bedtime domain: a child tries to write a
gentle bedtime composition, but a flood of spam keeps interrupting the page.
A calm grown-up helps clean up the mailbox, and the child turns the leftover
words into a sleepy little rhyme with sound effects.

Seed words:
- spam
- composition

Features:
- Rhyme
- Sound Effects

Style:
- Bedtime Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class PromptItem:
    id: str
    title: str
    sound: str
    rhythm: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SpamBurst:
    id: str
    label: str
    effect: str
    sound: str
    messy: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class QuietFix:
    id: str
    label: str
    action: str
    sound: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spam(world: World) -> list[str]:
    out: list[str] = []
    inbox = world.get("inbox")
    for burst in list(world.entities.values()):
        if burst.attrs.get("kind") != "spam" or burst.meters["seen"] < THRESHOLD:
            continue
        sig = ("spam", burst.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        inbox.meters["clutter"] += 1
        world.get("child").memes["frustration"] += 1
        out.append("__spam__")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    page = world.get("page")
    child = world.get("child")
    if child.memes["calm"] < THRESHOLD:
        return out
    if page.meters["sleepy"] < THRESHOLD:
        return out
    sig = ("rhyme", page.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    page.meters["finished"] += 1
    out.append("__rhyme__")
    return out


CAUSAL_RULES = [
    Rule("spam", "mess", _r_spam),
    Rule("rhyme", "art", _r_rhyme),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def calm_choice(fix: QuietFix, burst: SpamBurst) -> bool:
    return fix.power >= 2 and burst.messy


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for burst in SPAM_BURSTS:
            for fix in QUIET_FIXES:
                if calm_choice(fix, burst):
                    combos.append((setting, burst, fix))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    spam: str
    fix: str
    child_name: str
    child_gender: str
    grownup: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: spam, composition, rhyme, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spam", choices=SPAM_BURSTS)
    ap.add_argument("--fix", choices=QUIET_FIXES)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, burst in SPAM_BURSTS.items():
        lines.append(asp.fact("spam", bid))
        if burst.messy:
            lines.append(asp.fact("messy", bid))
    for fid, fix in QUIET_FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, F) :- setting(S), spam(B), fix(F), messy(B), power(F, P), P >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH in gate:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "soft and cozy"),
    "nursery": Setting("nursery", "the nursery", "warm and sleepy"),
    "reading_nook": Setting("reading_nook", "the reading nook", "small and quiet"),
}

SPAM_BURSTS = {
    "spam_mail": SpamBurst("spam_mail", "spam mail", "kept arriving in little piles", "ding-ding!", tags={"spam"}),
    "spam_messages": SpamBurst("spam_messages", "spam messages", "kept popping onto the screen", "ping-ping!", tags={"spam"}),
    "junk_flyers": SpamBurst("junk_flyers", "junk flyers", "slid under the door", "whish-whish!", tags={"spam"}),
}

QUIET_FIXES = {
    "sort_and_delete": QuietFix("sort_and_delete", "sort and delete", "cleared the inbox", "shhh-click", 3, tags={"quiet"}),
    "filter_and_sleep": QuietFix("filter_and_sleep", "set a quiet filter", "made the inbox hush", "tap-tap", 2, tags={"quiet"}),
    "basket_and_breath": QuietFix("basket_and_breath", "use a paper basket", "set the pages aside", "rustle", 2, tags={"quiet"}),
}

CHILD_NAMES = ["Luna", "Milo", "Ivy", "Noah", "Maya", "Leo", "Nora", "Eli"]
GROWNUP_NAMES = {"mother": "Mom", "father": "Dad"}


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = [n for n in CHILD_NAMES if (gender == "girl") == (n in {"Luna", "Ivy", "Maya", "Nora"})]
    return rng.choice(pool or CHILD_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spam and args.fix and not calm_choice(QUIET_FIXES[args.fix], SPAM_BURSTS[args.spam]):
        raise StoryError("That fix is too weak for the spammy interruption.")
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.spam is None or c[1] == args.spam
              if args.fix is None or c[2] == args.fix]
    # the above list comp is intentionally invalid syntax if kept; replace with loop
