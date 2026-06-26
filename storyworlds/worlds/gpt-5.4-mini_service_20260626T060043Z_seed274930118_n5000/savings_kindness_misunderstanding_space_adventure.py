#!/usr/bin/env python3
"""
Storyworld: savings_kindness_misunderstanding_space_adventure
=============================================================

A small, self-contained story world about a child in a space-adventure setting
who is saving for something important, stumbles through a misunderstanding, and
finds a kind solution.

Premise seed:
- A child is saving credits for a space adventure prize.
- A misunderstanding makes them think the prize is out of reach.
- Kindness from a helper reveals the true plan.
- The ending proves the savings mattered and the misunderstanding cleared.

The world model tracks physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
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



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    indoor: bool
    affordances: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    cost: int
    theme: str
    tags: set[str] = field(default_factory=set)
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
class HelpItem:
    id: str
    label: str
    phrase: str
    effect: str
    kind: str
    tags: set[str] = field(default_factory=set)
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    goal: str
    help_item: str
    name: str
    gender: str
    helper: str
    trait: str
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


SETTINGS = {
    "orbital_station": Setting("the orbital station", False, {"market", "dock", "bay"}),
    "moon_outpost": Setting("the moon outpost", False, {"market", "dock"}),
    "spaceport": Setting("the spaceport", False, {"market", "dock", "bay"}),
    "ship_cabin": Setting("the ship cabin", True, {"repair"}),
}

GOALS = {
    "star_map": Goal("star_map", "star map", "a bright star map with silver edges", 5, "exploration", {"map", "stars"}),
    "telescope": Goal("telescope", "small telescope", "a small telescope with a clear blue lens", 7, "exploration", {"stars", "view"}),
    "robot_kit": Goal("robot_kit", "robot kit", "a robot kit with tiny bolts", 6, "making", {"robot", "build"}),
    "moon_jar": Goal("moon_jar", "moon jar", "a moon-jar for storing shiny stones", 4, "collecting", {"jar", "moon"}),
}

HELP_ITEMS = {
    "repair_coupon": HelpItem("repair_coupon", "repair coupon", "a repair coupon from the station shop", "save money for the broken door", "coupon", {"help", "repair"}),
    "kindness_note": HelpItem("kindness_note", "kindness note", "a kind note with a picture of a rocket", "show that someone cared", "note", {"kindness", "care"}),
    "extra_chips": HelpItem("extra_chips", "extra chips", "a tin of extra chips from the lunch cart", "give a small boost to the savings jar", "food", {"savings", "coins"}),
    "share_ticket": HelpItem("share_ticket", "share ticket", "a share ticket for one more seat on the shuttle", "let two friends travel together", "ticket", {"travel", "friend"}),
}

NAMES = {
    "girl": ["Mia", "Luna", "Ivy", "Nora", "Zia", "Aria"],
    "boy": ["Finn", "Eli", "Rex", "Kai", "Noah", "Tobin"],
}

TRAITS = ["curious", "brave", "gentle", "busy", "dreamy", "patient"]
HELPERS = ["mother", "father", "pilot", "mechanic", "captain"]


def goal_at_risk(goal: Goal) -> bool:
    return goal.cost >= 4


def select_help(goal: Goal, helper_item: HelpItem) -> bool:
    return ("savings" in goal.tags and "savings" in helper_item.tags) or (
        "kindness" in helper_item.tags or "help" in helper_item.tags
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for goal_id, goal in GOALS.items():
            if place not in SETTINGS:
                continue
            if not goal_at_risk(goal):
                continue
            for help_id, help_item in HELP_ITEMS.items():
                if select_help(goal, help_item):
                    out.append((place, goal_id, help_id))
    return out


def sample_name(gender: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(NAMES, gender))


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['curious']))} {hero.type} who loved looking up at the stars.")


def setup_story(world: World, hero: Entity, helper: Entity, goal: Entity, help_item: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.meters["savings"] = hero.meters.get("savings", 0) + 1
    world.say(
        f"{hero.id} kept a jar of savings near {hero.pronoun('possessive')} bunk. "
        f"{hero.pronoun().capitalize()} wanted to buy {hero.pronoun('possessive')} {goal.label} one day."
    )
    world.say(
        f"{hero.id} also liked {helper.label_word} because {helper.pronoun('subject').capitalize()} often had a kind smile."
    )
    world.say(
        f"The prize was {goal.phrase}, and {hero.id} counted every coin, chip, and tiny credit twice."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, goal: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["misunderstanding"] = helper.memes.get("misunderstanding", 0) + 1
    world.say(
        f"One bright day at {world.setting.place}, {hero.id} heard {helper.label_word} say the shop was almost out of {goal.label}."
    )
    world.say(
        f"{hero.id} thought that meant {goal.label} was gone for good, and {hero.pronoun('possessive')} heart sank like a small stone."
    )
    world.say(
        f"{hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} savings jar and whispered, "
        f'"Maybe I will never get there."'
    )


def kindness_turn(world: World, hero: Entity, helper: Entity, goal: Entity, help_item: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"Then {helper.id} gently showed {hero.id} the real message: the shop was keeping one {goal.label} aside."
    )
    world.say(
        f"{helper.id} had meant the shelves looked empty because some things were moved for cleaning, not because the {goal.label} was lost."
    )
    world.say(
        f"{helper.id} also gave {hero.id} {help_item.phrase}, which helped {hero.id} save more of {hero.pronoun('possessive')} credits."
    )


def resolution(world: World, hero: Entity, helper: Entity, goal: Entity, help_item: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["misunderstanding"] = 0
    hero.meters["savings"] += 2
    world.say(
        f"{hero.id} smiled so big it looked like a new moon. {hero.pronoun().capitalize()} had enough savings after all."
    )
    world.say(
        f"By sunset, {hero.id} bought {hero.pronoun('possessive')} {goal.label} and tucked it beside {help_item.label_word} in the cabin."
    )
    world.say(
        f"The little {hero.type} stood at the window, holding the {goal.label}, while {helper.id} watched the stars with a kind grin."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    goal = _safe_lookup(GOALS, params.goal)
    help_item = _safe_lookup(HELP_ITEMS, params.help_item)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"savings": 2},
        memes={"traits": [params.trait], "hope": 1},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        memes={"kindness": 1},
    ))
    target = world.add(Entity(
        id=goal.id,
        type="thing",
        label=goal.label,
        phrase=goal.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    item = world.add(Entity(
        id=help_item.id,
        type="thing",
        label=help_item.label,
        phrase=help_item.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    introduce(world, hero)
    world.para()
    setup_story(world, hero, helper, target, item)
    world.para()
    misunderstanding(world, hero, helper, target)
    world.para()
    kindness_turn(world, hero, helper, target, item)
    world.para()
    resolution(world, hero, helper, target, item)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "goal": target,
        "help_item": item,
        "setting": setting,
    }
    return world


KNOWLEDGE = {
    "savings": [
        ("What are savings?", "Savings are money or credits you keep instead of spending right away, so you can buy something later."),
    ],
    "kindness": [
        ("What is kindness?", "Kindness is being gentle, helpful, and caring to someone else."),
    ],
    "misunderstanding": [
        ("What is a misunderstanding?", "A misunderstanding happens when someone thinks something is true, but they got the message wrong."),
    ],
    "stars": [
        ("What are stars?", "Stars are giant balls of hot light far away in space. They look tiny because they are so distant."),
    ],
    "map": [
        ("What does a map do?", "A map shows where things are and helps people find their way."),
    ],
    "robot": [
        ("What is a robot?", "A robot is a machine that can move or do jobs, sometimes with buttons or code helping it work."),
    ],
    "coin": [
        ("Why do people count coins?", "People count coins so they know how much money they have saved."),
    ],
}


ASP_RULES = r"""
goal_at_risk(G) :- goal(G), cost(G,N), N >= 4.
helpful(H,G) :- goal_at_risk(G), help_item(H), kindness_help(H).
compatible(Place,G,H) :- afford(Place,adventure), goal_at_risk(G), helpful(H,G).
valid_story(Place,G,H) :- setting(Place), goal(G), help_item(H), compatible(Place,G,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for aff in sorted(setting.affordances):
            lines.append(asp.fact("afford", pid, aff))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("cost", gid, goal.cost))
        for tag in sorted(goal.tags):
            lines.append(asp.fact("goal_tag", gid, tag))
    for hid, help_item in HELP_ITEMS.items():
        lines.append(asp.fact("help_item", hid))
        if "kindness" in help_item.tags:
            lines.append(asp.fact("kindness_help", hid))
        for tag in sorted(help_item.tags):
            lines.append(asp.fact("help_tag", hid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, goal = f["hero"], f["helper"], f["goal"]
    return [
        f'Write a short space adventure story for a young child about {hero.id} saving up for a {goal.label}.',
        f"Tell a gentle story where {hero.id} has savings, hears something wrong, and later learns a kind truth from {helper.label_word}.",
        f'Write a child-friendly story that includes the words "savings", "kindness", and "misunderstanding".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, goal, item = f["hero"], f["helper"], f["goal"], f["help_item"]
    return [
        QAItem(
            question=f"What was {hero.id} saving for?",
            answer=f"{hero.id} was saving credits for {hero.pronoun('possessive')} {goal.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried before {helper.id} explained things?",
            answer=(
                f"{hero.id} had a misunderstanding and thought the {goal.label} was gone for good. "
                f"That made {hero.pronoun('possessive')} heart sink for a while."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} in the end?",
            answer=(
                f"{helper.id} was kind, explained the truth, and gave {hero.id} {item.phrase} "
                f"so the savings could grow again."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"The misunderstanding was cleared up, the savings were enough, and {hero.id} "
                f"got {hero.pronoun('possessive')} {goal.label}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    goal = _safe_fact(world, world.facts, "goal")
    item = _safe_fact(world, world.facts, "help_item")
    tags.update(goal.tags)
    tags.update(item.tags)
    tags.add("savings")
    tags.add("kindness")
    tags.add("misunderstanding")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about savings, kindness, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--help-item", choices=HELP_ITEMS, dest="help_item")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "goal", None):
        combos = [c for c in combos if c[1] == getattr(args, "goal", None)]
    if getattr(args, "help_item", None):
        combos = [c for c in combos if c[2] == getattr(args, "help_item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal, help_item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or sample_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, help_item=help_item, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="orbital_station", goal="star_map", help_item="kindness_note", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="moon_outpost", goal="telescope", help_item="repair_coupon", name="Finn", gender="boy", helper="mechanic", trait="gentle"),
    StoryParams(place="spaceport", goal="robot_kit", help_item="extra_chips", name="Luna", gender="girl", helper="captain", trait="patient"),
    StoryParams(place="ship_cabin", goal="moon_jar", help_item="share_ticket", name="Kai", gender="boy", helper="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.goal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
