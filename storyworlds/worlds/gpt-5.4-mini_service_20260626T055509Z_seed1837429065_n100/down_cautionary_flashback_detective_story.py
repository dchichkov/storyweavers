#!/usr/bin/env python3
"""
storyworlds/worlds/down_cautionary_flashback_detective_story.py
===============================================================

A small detective-style storyworld with a cautionary beat and a flashback
turn. The seed word is "down", and the story always follows a careful child
detective who learns to solve a case without rushing into danger.

The world is built from a short source-tale premise:
- a child detective notices a clue leading down somewhere hidden,
- a warning or remembered mishap makes the child cautious,
- a helpful tool or companion lets the detective continue safely,
- the case is solved, and the ending image proves the change.

This script keeps the prose child-facing and state-driven while remaining a
small classical simulation.
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
    carried_by: Optional[str] = None
    location: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    clue: str
    location: str
    weather: str = ""
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used = False

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.flashback_used = self.flashback_used
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
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


SETTINGS = {
    "hallway": Setting(place="the hallway", affords={"follow", "search"}),
    "attic": Setting(place="the attic", affords={"follow", "search"}),
    "cellar": Setting(place="the cellar", affords={"follow", "search"}),
    "library": Setting(place="the library", affords={"follow", "search"}),
}

ACTIVITIES = {
    "follow_down": Activity(
        id="follow_down",
        verb="follow the clue down the stairs",
        gerund="following the clue down the stairs",
        risk="darkness",
        clue="down",
        location="down the stairs",
        tags={"down", "detective", "cautionary", "flashback"},
    ),
    "search_down": Activity(
        id="search_down",
        verb="search down in the shadows",
        gerund="searching down in the shadows",
        risk="getting lost",
        clue="down",
        location="down below",
        tags={"down", "detective", "cautionary", "flashback"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a little lantern",
        prep="take a little lantern first",
        tail="walked down with the lantern held high",
        protects_from={"darkness"},
    ),
    "rope": Tool(
        id="rope",
        label="a short rope",
        prep="tie a short rope to the banister",
        tail="went down with the rope safely looped nearby",
        protects_from={"getting lost"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "June", "Luna", "Ada", "Nora"]
BOY_NAMES = ["Pip", "Finn", "Eli", "Theo", "Max", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for clue in ("down",):
                out.append((place, act_id, clue))
    return out


def select_tool(activity: Activity) -> Optional[Tool]:
    for tool in TOOLS.values():
        if activity.risk in tool.protects_from:
            return tool
    return None


def story_setup(world: World, hero: Entity, helper: Entity, activity: Activity, clue: str) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} detective who liked quiet puzzles and neat clues."
    )
    world.say(
        f"{hero.id} kept noticing the word {clue!r} because it was scratched onto a tiny paper tag."
    )
    world.say(
        f"{helper.id} stayed nearby and promised to help {hero.pronoun('object')} think before rushing."
    )
    hero.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0


def flashback(world: World, hero: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} remembered a time when {hero.pronoun('object')} had rushed down the dark stairs "
        f"and bumped a knee."
    )
    world.say(
        f"That old memory made {hero.id} slow down and look harder at the clue."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity) -> None:
    world.say(
        f'"Let\'s not hurry down there," {helper.id} said. '
        f'"A careful detective solves more cases than a fast one."'
    )
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1.0


def choose_tool(world: World, helper: Entity, hero: Entity, activity: Activity) -> Optional[Tool]:
    tool = select_tool(activity)
    if tool is None:
        return None
    world.say(
        f"{helper.id} picked up {tool.label} and said they should {tool.prep}."
    )
    ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        owner=hero.id,
        carried_by=hero.id,
        protective=True,
        plural=tool.plural,
    ))
    ent.meters["ready"] = 1.0
    return tool


def do_activity(world: World, hero: Entity, activity: Activity, tool: Optional[Tool]) -> None:
    if activity.id not in world.setting.affords:
        pass
    if tool is None:
        pass
    world.say(
        f"At last, {hero.id} could {activity.verb} without guessing in the dark."
    )
    world.say(
        f"{hero.id} {tool.tail}, spotted the missing note, and found that the clue led to a hidden tin box."
    )
    hero.meters["progress"] = hero.meters.get("progress", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0


def resolve(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(
        f"Inside the tin box was the missing badge, still shiny and safe."
    )
    world.say(
        f"{hero.id} smiled, because being careful had solved the case and kept the night calm."
    )
    world.say(
        f"{helper.id} laughed softly, and together they walked back up with the answer in hand."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0


def tell(setting: Setting, activity: Activity, clue: str, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    hero.meters["progress"] = 0.0
    helper.meters["care"] = 0.0

    story_setup(world, hero, helper, activity, clue)
    world.para()
    warn(world, helper, hero, activity)
    flashback(world, hero)
    tool = choose_tool(world, helper, hero, activity)
    world.para()
    if tool is None:
        pass
    do_activity(world, hero, activity, tool)
    resolve(world, hero, helper, activity)

    world.facts.update(
        hero=hero,
        helper=helper,
        activity=activity,
        clue=clue,
        tool=tool,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    activity = _safe_fact(world, f, "activity")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short detective story for a child that uses the word "{clue}" and includes a careful warning.',
        f"Tell a cautionary mystery where {hero.id} wants to {activity.verb}, remembers an old mistake, and solves the case with {helper.id}.",
        f"Write a gentle story with a flashback in which a young detective learns to be safe before going down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    activity = _safe_fact(world, f, "activity")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero.id}, a little {hero.type} who paid close attention to clues.",
        ),
        QAItem(
            question=f"What did {helper.id} tell {hero.id} to do before going down?",
            answer=f"{helper.id} told {hero.id} to stay careful and use {tool.label} before {activity.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered a time when rushing down the dark stairs led to a bumped knee.",
        ),
        QAItem(
            question=f"What was found at the end of the mystery in {setting.place}?",
            answer=f"The missing badge was found in a hidden tin box, and the case was solved safely.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "down": [
        QAItem(
            question="What does it mean to go down the stairs?",
            answer="Going down the stairs means moving from a higher place to a lower place, one step at a time.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story gives a careful warning so someone can avoid a mistake or danger.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something from before.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ("down", "detective", "cautionary", "flashback"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(
            f"  {e.id:10} type={e.type:8} "
            f"{'meters=' + str(meters) if meters else ''} "
            f"{'memes=' + str(memes) if memes else ''} "
            f"{'tool=' + e.label if e.protective else ''}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
activity(activity(follow_down)).
activity(activity(search_down)).

place(place(hallway)).
place(place(attic)).
place(place(cellar)).
place(place(library)).

clue_word(down).

affords(hallway,follow_down).
affords(hallway,search_down).
affords(attic,follow_down).
affords(attic,search_down).
affords(cellar,follow_down).
affords(cellar,search_down).
affords(library,follow_down).
affords(library,search_down).

risk(follow_down,darkness).
risk(search_down,getting_lost).

tool(lantern).
tool(rope).

protects(lantern,darkness).
protects(rope,getting_lost).

valid(Place,Act,down) :- place(Place), activity(Act), affords(Place,Act), risk(Act,R),
                          clue_word(down), tool(T), protects(T,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for act_id in ACTIVITIES:
        lines.append(asp.fact("activity", act_id))
    for clue in ("down",):
        lines.append(asp.fact("clue_word", clue))
    for place, setting in SETTINGS.items():
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act_id, act in ACTIVITIES.items():
        lines.append(asp.fact("risk", act_id, act.risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for danger in sorted(tool.protects_from):
            lines.append(asp.fact("protects", tool_id, danger))
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
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary flashback detective storyworld with the seed word 'down'."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--clue", choices=["down"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--helper-type", choices=["woman", "man"], dest="helper_type")
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
    if getattr(args, "clue", None) and getattr(args, "clue", None) != "down":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity_id, clue = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["woman", "man"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(["Mara", "Jun", "Iris", "Otto", "Nell", "Bram"])
    return StoryParams(
        place=place,
        activity=activity_id,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        params.clue,
        params.hero_name,
        params.hero_type,
        params.helper_name,
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


CURATED = [
    StoryParams(place="hallway", activity="follow_down", clue="down", hero_name="Mina", hero_type="girl",
                helper_name="Mara", helper_type="woman"),
    StoryParams(place="library", activity="search_down", clue="down", hero_name="Pip", hero_type="boy",
                helper_name="Jun", helper_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            seed = base_seed + i
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
