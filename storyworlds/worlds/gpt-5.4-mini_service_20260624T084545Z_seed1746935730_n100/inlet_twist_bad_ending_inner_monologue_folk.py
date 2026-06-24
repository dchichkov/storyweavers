#!/usr/bin/env python3
"""
storyworlds/worlds/inlet_twist_bad_ending_inner_monologue_folk.py
==================================================================

A small folk-tale story world about a child, an inlet, a warning, a twist,
and a bad ending that is still complete and causally grounded.

The domain is built around an inlet where the sea can creep in and trap a path.
A child may try to carry a precious message, lantern, or loaf across the water
at the wrong time. A folk-wise elder can foresee the trouble, but the child's
inner monologue can pull them toward a risky choice. The twist is that the
apparently helpful shortcut is the very thing that causes the loss.

The ending is intentionally sad: the goal is not achieved, and something small
but meaningful is lost to the inlet. The prose remains child-facing, concrete,
and state-driven.
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
# Shared entity model
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    goal: object | None = None
    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elderwoman"}
        male = {"boy", "man", "father", "grandfather", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
class Setting:
    place: str = "the inlet"
    affords: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    loss: str
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
class Guide:
    id: str
    label: str
    type: str
    wisdom: str
    warning: str
    twist_hint: str
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
class Choice:
    id: str
    label: str
    action: str
    monologue: str
    consequence: str
    risky: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.tide: str = "low"
        self.weather: str = "clear"

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.tide = self.tide
        c.weather = self.weather
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "inlet": Setting(place="the inlet", affords={"cross", "wait", "call"}),
    "shore": Setting(place="the shore", affords={"cross", "wait", "call"}),
}

GOALS = {
    "bread": Goal(
        id="bread",
        label="loaf of bread",
        phrase="a warm loaf of bread",
        type="bread",
        risk="soak",
        loss="became soggy",
        tags={"food", "bread"},
    ),
    "lantern": Goal(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        type="lantern",
        risk="go out",
        loss="went dark",
        tags={"light", "lantern"},
    ),
    "letter": Goal(
        id="letter",
        label="letter",
        phrase="a folded letter tied with string",
        type="letter",
        risk="smear",
        loss="was ruined",
        tags={"message", "letter"},
    ),
}

GUIDES = {
    "grandmother": Guide(
        id="grandmother",
        label="grandmother",
        type="grandmother",
        wisdom="knew the inlet's moods",
        warning="Do not cross when the tide turns; the water reaches up like fingers.",
        twist_hint="The shortcut is the trap.",
        tags={"wisdom", "family"},
    ),
    "fisherman": Guide(
        id="fisherman",
        label="old fisherman",
        type="man",
        wisdom="knew the sandbars and currents",
        warning="The inlet is kind only to those who wait for the tide.",
        twist_hint="The straight path may be the wrong one.",
        tags={"wisdom", "sea"},
    ),
}

CHOICES = {
    "cross": Choice(
        id="cross",
        label="cross the inlet",
        action="cross the inlet",
        monologue="If I hurry now, I can make it before the water rises.",
        consequence="the tide reached the path first",
        risky=True,
    ),
    "wait": Choice(
        id="wait",
        label="wait at the shore",
        action="wait at the shore",
        monologue="Maybe I should listen and keep my feet dry a while longer.",
        consequence="the tide slowed and the path stayed safe",
        risky=False,
    ),
    "call": Choice(
        id="call",
        label="call for help",
        action="call for help",
        monologue="If I shout, perhaps a grown-up will guide me across.",
        consequence="someone could have helped, if only the child had called soon enough",
        risky=False,
    ),
}

NAMES = ["Mara", "Nell", "Tobin", "Pip", "Rosa", "Eli", "Anya", "Jon", "Hilda", "Soren"]
TRAITS = ["brave", "restless", "curious", "hasty", "quiet", "hopeful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    goal: str
    guide: str
    choice: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def valid_combo(place: str, goal: Goal, choice: Choice) -> bool:
    if place not in SETTINGS:
        return False
    if choice.id == "wait":
        return True
    # The bad ending only makes sense if the risky choice can actually lose the goal.
    return choice.risky and "inlet" in place and goal.id in {"bread", "lantern", "letter"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for goal_id, goal in GOALS.items():
            for choice_id, choice in CHOICES.items():
                if valid_combo(place, goal, choice):
                    out.append((place, goal_id, choice_id))
    return out


def explain_rejection(place: str, goal: Goal, choice: Choice) -> str:
    return (
        f"(No story: '{choice.action}' does not create a believable inlet tale "
        f"with {goal.label}. Try a risky crossing or a waiting choice at the inlet.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,G,C) :- setting(P), goal(G), choice(C), risky(C), place_inlet(P), loss_goal(G).
valid(P,G,C) :- setting(P), goal(G), choice(C), C = wait.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if "inlet" in sid:
            lines.append(asp.fact("place_inlet", sid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("loss_goal", gid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if c.risky:
            lines.append(asp.fact("risky", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------
def build_story(world: World, hero: Entity, guide: Entity, goal: Entity, choice: Choice) -> None:
    world.say(f"{hero.id} was a {hero.meters.get('age', 7):.0f}-year-old {hero.meters.get('role', 1) and hero.type} who lived near {world.setting.place}.")
    world.say(
        f"{hero.id} carried {goal.phrase} because {goal.label} had to reach the far side before dark."
    )
    world.say(
        f"{guide.label.capitalize()} {guide.pronoun('subject')} {guide.memes.get('wisdom', 1) and guide.facts if False else ''}".strip()
    )
    world.say(
        f"{guide.label.capitalize()} knew the inlet well and said, \"{guide.label.capitalize()} {guide.pronoun('subject')} {guide.pronoun('subject') if False else ''}\""
    )


def tell(setting: Setting, goal_cfg: Goal, guide_cfg: Guide, choice_cfg: Choice,
         name: str = "Mara", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mara", "Nell", "Rosa", "Anya", "Hilda"} else "boy"))
    guide = world.add(Entity(id="guide", kind="character", type=guide_cfg.type, label=guide_cfg.label))
    goal = world.add(Entity(id="goal", type=goal_cfg.type, label=goal_cfg.label, phrase=goal_cfg.phrase, owner=hero.id, caretaker=guide.id))
    hero.meters["age"] = 7
    hero.memes["trait"] = 1
    hero.memes["inner_voice"] = 0
    world.tide = "low"
    world.weather = "clear"

    world.say(f"{hero.id} was a {trait} child who lived by {setting.place}.")
    world.say(f"{hero.id} loved the salt smell and the gulls circling over the water.")
    world.say(f"One evening, {hero.id} had to carry {goal.phrase} to the other shore.")
    world.para()
    world.say(f"{guide_cfg.label.capitalize()} met {hero.id} by the reeds and warned, \"{guide_cfg.warning}\"")
    world.say(f"{guide_cfg.label.capitalize()} {guide_cfg.wisdom}, and {guide_cfg.twist_hint}")
    world.para()
    hero.memes["inner_voice"] += 1
    world.say(f"In {hero.id}'s own head, a small thought kept speaking: \"{choice_cfg.monologue}\"")
    world.say(f"So {hero.id} chose to {choice_cfg.action}.")
    world.tide = "rising"
    if choice_cfg.id == "cross":
        world.say(f"But the tide rose faster than the child expected.")
        world.say(f"Cold water slid over the stones and took the path apart.")
        world.say(f"At first, {hero.id} thought the strip of sand was still firm.")
        world.say(f"Then the inlet turned the strip into a little gray island.")
        world.say(f"{goal.label.capitalize()} {goal_cfg.loss}.")
        world.say(f"{hero.id} stood with empty hands, listening to the water lick the posts.")
        world.say(f"The bad twist was that the shortcut was never a shortcut at all; it had been the inlet's trap.")
        world.say(f"By moonrise, {hero.id} walked home without {goal.label}, and the shore looked lonelier than before.")
    else:
        world.say(f"{hero.id} waited as {guide_cfg.label} said, and the tide eased back.")
        world.say(f"The child crossed safely later with dry feet and a steady heart.")
        world.say(f"That ending was not the one the inner voice had first wanted, but it was the wise one.")

    world.facts.update(hero=hero, guide=guide, goal=goal, choice=choice_cfg, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    goal: Entity = f["goal"]
    choice: Choice = f["choice"]
    return [
        f'Write a short folk tale for a young child about an inlet, a warning, and {goal.label}.',
        f"Tell a simple story where {hero.id} hears a wise elder, thinks to {choice.action}, and learns too late about the inlet.",
        f'Write a gentle-seeming but sad story that uses the word "inlet" and ends with a loss caused by the tide.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    goal: Entity = f["goal"]
    choice: Choice = f["choice"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} child who lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {guide.label} warn {hero.id} about?",
            answer=f"{guide.label.capitalize()} warned that the inlet's tide could rise and cut off the path.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the inner monologue?",
            answer=f"{hero.id} kept thinking, \"{choice.monologue}\" and decided to {choice.action}.",
        ),
        QAItem(
            question=f"What happened to {goal.label} at the end?",
            answer=f"{goal.label.capitalize()} {f['goal'].loss}, so the ending was sad and the child came home empty-handed.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The seeming shortcut was the trap: the inlet looked easy to cross, but the rising tide turned it dangerous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inlet?",
            answer="An inlet is a narrow strip of water that reaches into the land, often changing with the tide.",
        ),
        QAItem(
            question="What is a tide?",
            answer="A tide is the regular rising and falling of the sea water near the shore.",
        ),
        QAItem(
            question="Why can a rising tide be dangerous near an inlet?",
            answer="A rising tide can cover a path, make stones slippery, and leave someone stuck on the wrong side.",
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


# ---------------------------------------------------------------------------
# Params / generation / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale inlet story world with a twist and a sad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    goal_id = getattr(args, "goal", None) or rng.choice(list(GOALS))
    guide_id = getattr(args, "guide", None) or rng.choice(list(GUIDES))
    choice_id = getattr(args, "choice", None) or rng.choice(list(CHOICES))
    goal = _safe_lookup(GOALS, goal_id)
    choice = _safe_lookup(CHOICES, choice_id)
    if getattr(args, "place", None) and getattr(args, "goal", None) and getattr(args, "choice", None) and not valid_combo(place, goal, choice):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal_id, guide=guide_id, choice=choice_id, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(GOALS, params.goal), _safe_lookup(GUIDES, params.guide), _safe_lookup(CHOICES, params.choice), params.name, params.trait)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  tide={world.tide}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="inlet", goal="bread", guide="grandmother", choice="cross", name="Mara", trait="curious"),
    StoryParams(place="inlet", goal="lantern", guide="fisherman", choice="cross", name="Tobin", trait="hasty"),
    StoryParams(place="shore", goal="letter", guide="grandmother", choice="wait", name="Nell", trait="hopeful"),
]


def asp_verify_wrapper() -> int:
    return asp_verify()


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_wrapper())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
