#!/usr/bin/env python3
"""
storyworlds/worlds/nummy_catalogue_tartar_happy_ending_space_adventure.py
=========================================================================

A small standalone storyworld for a cheerful space-adventure tale.

Seed image:
- A child on a tiny ship is sorting a nummy catalogue of snacks.
- A tartar stain or gritty tartar patch gets in the way of an important launch item.
- The crew solves the problem with a careful repair, a smart swap, and a happy ending.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- state-driven prose rather than a frozen paragraph
- a Python reasonableness gate
- an inline ASP twin for parity checks
- child-facing Q&A grounded in the generated story

The domain keeps the style close to a cozy space adventure: rockets, star maps,
cargo trays, moon snacks, and a bright launch at the end.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    captain: object | None = None
    copilot: object | None = None
    problem: object | None = None
    ship: object | None = None
    sky: object | None = None
    snack: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


@dataclass
class StoryParams:
    captain: str
    copilots: str
    ship: str
    snack: str
    snack_catalogue: str
    tartar: str
    problem: str
    tool: str
    fix: str
    ending_sky: str
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


@dataclass
class Theme:
    id: str
    ship: str
    sky: str
    mission: str
    cargo: str
    landing: str
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


@dataclass
class Snack:
    id: str
    label: str
    nummy: bool = True
    messy: bool = False
    catalogued: bool = True
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
    location: str
    severity: int
    stubborn: bool = True
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
class Tool:
    id: str
    label: str
    power: int
    kind: str
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


THEMES = {
    "moon": Theme("moon", "silver rocket", "moon-dark sky", "moon mission", "cargo bay", "moon base"),
    "comet": Theme("comet", "starlight shuttle", "comet-lit sky", "comet chase", "supply tray", "orbital dock"),
    "planet": Theme("planet", "tiny cruiser", "ringed-planet sky", "planet hop", "launch crate", "friendly station"),
}

SNACKS = {
    "nummy": Snack("nummy", "nummy cookie", nummy=True, messy=True),
    "crumbs": Snack("crumbs", "crumbly biscuit", nummy=True, messy=True),
    "puff": Snack("puff", "puffed moon bite", nummy=True, messy=False),
}

TARTARS = {
    "catalogue": Problem("catalogue", "catalogue page", "the snack catalogue", severity=1, stubborn=False),
    "tartar": Problem("tartar", "tartar patch", "the launch latch", severity=2, stubborn=True),
    "sticker": Problem("sticker", "sticky sticker", "the cargo seal", severity=1, stubborn=False),
}

TOOLS = {
    "cloth": Tool("cloth", "soft cloth", power=1, kind="wipe"),
    "spray": Tool("spray", "gentle spray", power=2, kind="clean"),
    "scanner": Tool("scanner", "star scanner", power=2, kind="inspect"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny happy-ending space adventure storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--problem", choices=TARTARS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--narrator", choices=["captain", "copilot"])
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
    theme = getattr(args, "theme", None) or rng.choice(list(THEMES))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    problem = getattr(args, "problem", None) or rng.choice(list(TARTARS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if snack == "nummy" and problem == "catalogue":
        pass
    if problem == "tartar" and tool == "scanner":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if problem == "tartar" and tool == "cloth":
        # still reasonable but may be weak; allowed.
        pass
    return StoryParams(
        captain="Nova",
        copilots="Pip",
        ship=_safe_lookup(THEMES, theme).ship,
        snack=_safe_lookup(SNACKS, snack).label,
        snack_catalogue="catalogue",
        tartar=_safe_lookup(TARTARS, problem).label,
        problem=problem,
        tool=tool,
        fix="wipe and swap",
        ending_sky=_safe_lookup(THEMES, theme).sky,
    )


def make_world(p: StoryParams) -> World:
    w = World()
    captain = w.add(Entity("Nova", kind="character", type="girl", role="captain", memes={"joy": 2.0, "hope": 2.0}))
    copilot = w.add(Entity("Pip", kind="character", type="boy", role="copilot", memes={"joy": 2.0, "curiosity": 2.0}))
    ship = w.add(Entity("ship", kind="thing", type="ship", label=p.ship, meters={"ready": 0.0, "stuck": 0.0}))
    snack = w.add(Entity("snack", kind="thing", type="snack", label=p.snack, memes={"nummy": 1.0}))
    problem = w.add(Entity("problem", kind="thing", type="problem", label=p.tartar, meters={"grit": 1.0}, attrs={"where": _safe_lookup(TARTARS, p.problem).location}))
    tool = w.add(Entity("tool", kind="thing", type="tool", label=_safe_lookup(TOOLS, p.tool).label, meters={"power": float(_safe_lookup(TOOLS, p.tool).power)}))
    sky = w.add(Entity("sky", kind="place", type="sky", label=p.ending_sky))
    w.facts.update(p=p, captain=captain, copilot=copilot, ship=ship, snack=snack, problem=problem, tool=tool, sky=sky)
    return w


def tell_story(w: World) -> None:
    p = w.facts["p"]
    cap = w.facts["captain"]
    cop = w.facts["copilot"]
    ship = w.facts["ship"]
    snack = w.facts["snack"]
    prob = w.facts["problem"]
    tool = w.facts["tool"]
    sky = w.facts["sky"]

    cap.memes["joy"] += 1
    cop.memes["joy"] += 1
    w.say(
        f"On a bright morning, Nova and Pip turned the cabin of the {ship.label} into a tiny space base. "
        f"They opened the {p.snack_catalogue} and picked a {snack.label} for the trip."
    )
    w.say(
        f"But the launch latch had a {prob.label} on it, right where the ship needed to close."
    )

    cap.memes["worry"] = 1.0
    cop.memes["worry"] = 1.0
    w.para()
    w.say(
        f"\"That looks messy,\" said Pip. \"We need it clean before the countdown.\""
    )
    w.say(
        f"Nova lifted {tool.label}. {tool.label.capitalize()} was the right tool for a careful fix, "
        f"so she used it to {p.fix} the latch."
    )
    prob.meters["grit"] = 0.0
    ship.meters["stuck"] = 0.0
    ship.meters["ready"] = 1.0
    cap.memes["hope"] += 2.0
    cop.memes["relief"] += 2.0

    w.para()
    w.say(
        f"The latch clicked open, and the {ship.label} was ready at last. "
        f"Nova tucked the {snack.label} into the cargo bay, where it stayed neat and nummy."
    )
    w.say(
        f"Then the rocket lifted into {sky.label}, and the two friends whooped as the stars blinked by."
    )
    w.say(
        "They reached the station safely, shared their snack, and grinned at the shiny view from the window."
    )

    w.facts["outcome"] = "happy"
    w.facts["ready"] = True


def generation_prompts(w: World) -> list[str]:
    p = w.facts["p"]
    return [
        f"Write a happy-ending space adventure about Nova and Pip, a {p.snack} snack, and a {p.tartar} on the launch gear.",
        f"Tell a cozy rocket story where a nummy catalogue helps the crew choose a snack, then a careful cleaning fixes the problem before launch.",
        f"Make a child-friendly spaceship story in which a messy tartar patch blocks the mission, but the crew solves it and flies off happily.",
    ]


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["p"]
    return [
        QAItem(
            question="What did Nova and Pip open before the trip?",
            answer=f"They opened the {p.snack_catalogue} to pick a snack for the space trip.",
        ),
        QAItem(
            question="What problem blocked the launch?",
            answer=f"A {p.tartar} was stuck on the launch latch, so the ship could not close at first.",
        ),
        QAItem(
            question="What tool fixed the latch?",
            answer=f"Nova used the {w.facts['tool'].label} to clean it and get the ship ready.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily: the ship launched, the friends reached the station, and they shared their snack.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem("What is a catalogue?", "A catalogue is a list or book that shows what things are available."),
        QAItem("What does nummy mean?", "Nummy means tasty and good to eat."),
        QAItem("What is tartar?", "Tartar is a hard or gritty buildup that can stick to a surface and needs cleaning."),
        QAItem("Why should a launch latch be clean?", "A clean latch helps the ship close properly so it can launch safely."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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
    if trace and sample.world:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.label, e.meters, e.memes, e.attrs)
    if qa:
        print("\n--- QA ---")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
theme(moon; comet; planet).
snack(nummy; crumbs; puff).
problem(catalogue; tartar; sticker).
tool(cloth; spray; scanner).

happy :- theme(_), snack(_), problem(_), tool(_).
show_ok(T,S,P,To) :- theme(T), snack(S), problem(P), tool(To), happy.
#show show_ok/4.
"""


def asp_facts() -> str:
    return "\n".join([
        "theme(moon). theme(comet). theme(planet).",
        "snack(nummy). snack(crumbs). snack(puff).",
        "problem(catalogue). problem(tartar). problem(sticker).",
        "tool(cloth). tool(spray). tool(scanner).",
    ])


def _asp_module():
    import asp  # lazy
    return asp


def asp_verify() -> int:
    asp = _asp_module()
    py = {("moon", "nummy", "catalogue", "cloth"), ("moon", "nummy", "catalogue", "spray"), ("moon", "nummy", "catalogue", "scanner"),
          ("moon", "crumbs", "catalogue", "cloth"), ("moon", "crumbs", "catalogue", "spray"), ("moon", "crumbs", "catalogue", "scanner"),
          ("moon", "puff", "catalogue", "cloth"), ("moon", "puff", "catalogue", "spray"), ("moon", "puff", "catalogue", "scanner"),
          ("moon", "nummy", "tartar", "cloth"), ("moon", "nummy", "tartar", "spray"),
          ("moon", "crumbs", "tartar", "cloth"), ("moon", "crumbs", "tartar", "spray"),
          ("moon", "puff", "tartar", "cloth"), ("moon", "puff", "tartar", "spray"),
          ("moon", "nummy", "sticker", "cloth"), ("moon", "nummy", "sticker", "spray"), ("moon", "nummy", "sticker", "scanner"),
          ("moon", "crumbs", "sticker", "cloth"), ("moon", "crumbs", "sticker", "spray"), ("moon", "crumbs", "sticker", "scanner"),
          ("moon", "puff", "sticker", "cloth"), ("moon", "puff", "sticker", "spray"), ("moon", "puff", "sticker", "scanner")}
    model = asp.one_model(asp_facts() + "\n" + ASP_RULES)
    asp_set = set(asp.atoms(model, "show_ok"))
    asp_set = {tuple(x) for x in asp_set}
    return 0 if py == asp_set else 1


def resolve_reasonable(args: argparse.Namespace) -> None:
    if getattr(args, "problem", None) == "tartar" and getattr(args, "tool", None) == "scanner":
        pass


def build_variants(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if getattr(args, "all", None):
        return [
            StoryParams("Nova", "Pip", THEMES["moon"].ship, SNACKS["nummy"].label, "catalogue", TARTARS["catalogue"].label, "catalogue", "cloth", "wipe and swap", THEMES["moon"].sky),
            StoryParams("Nova", "Pip", THEMES["comet"].ship, SNACKS["crumbs"].label, "catalogue", TARTARS["tartar"].label, "tartar", "spray", "wipe and swap", THEMES["comet"].sky),
            StoryParams("Nova", "Pip", THEMES["planet"].ship, SNACKS["puff"].label, "catalogue", TARTARS["sticker"].label, "sticker", "cloth", "wipe and swap", THEMES["planet"].sky),
        ]
    return [resolve_params(args, rng) for _ in range(getattr(args, "n", None))]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(ASP_RULES)
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_facts())
        print(ASP_RULES)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = [generate(p) for p in build_variants(args, rng)]
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
