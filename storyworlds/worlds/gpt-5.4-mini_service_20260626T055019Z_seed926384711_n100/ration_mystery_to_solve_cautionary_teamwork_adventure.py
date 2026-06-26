#!/usr/bin/env python3
"""
A standalone storyworld about a careful adventure to solve the mystery of a
missing ration with teamwork.

Premise:
- A small team is traveling with a packed ration for the day.
- The ration goes missing in a cautionary moment.
- The team must work together, search carefully, and solve the mystery.
- The ending should show the ration safely shared and the group wiser.

This script follows the Storyweavers storyworld contract and is self-contained.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    ration: object | None = None
    scout: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the forest trail"
    afford: set[str] = field(default_factory=set)
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
class Supply:
    label: str
    phrase: str
    type: str
    tag: str = "ration"
    risky: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    action: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "trail": Setting(place="the forest trail", afford={"walk", "search"}),
    "canyon": Setting(place="the windy canyon path", afford={"walk", "search"}),
    "camp": Setting(place="the old campsite", afford={"search", "share"}),
}

SUPPLIES = {
    "ration_box": Supply(
        label="ration box",
        phrase="a small ration box wrapped in blue paper",
        type="box",
    ),
    "trail_ration": Supply(
        label="ration pack",
        phrase="a careful ration pack with crackers and fruit",
        type="pack",
    ),
}

TOOLS = [
    Tool(
        id="map",
        label="map",
        phrase="a folded map",
        helps={"search"},
        action="follow the trail markers",
    ),
    Tool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        helps={"search", "caution"},
        action="shine on the shadows",
    ),
    Tool(
        id="rope",
        label="rope",
        phrase="a short rope",
        helps={"caution"},
        action="keep everyone close together",
    ),
]

NAMES = ["Maya", "Leo", "Nina", "Owen", "Ari", "Zoe", "Finn", "Ivy"]
TRAITS = ["careful", "brave", "curious", "kind", "steady", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    supply: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


def ragged_has_mystery(world: World) -> bool:
    hero = world.get("hero")
    ration = world.get("ration")
    return hero.memes.get("worry", 0) > 0 and ration.carried_by is None


def choose_tool_for_mystery() -> Tool:
    return _safe_lookup(TOOLS, 0)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in SETTINGS for s in SUPPLIES]


def explain_rejection(_: object, __: object) -> str:
    return "(No story: the supplied options do not make a clear ration mystery.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _intro(world: World) -> None:
    hero = world.get("hero")
    scout = world.get("scout")
    ration = world.get("ration")
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'careful')} scout who loved adventure and tidy plans."
    )
    world.say(
        f"On the morning trip, {scout.pronoun('possessive')} team carried {ration.phrase} for the long walk."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    scout.memes["trust"] = scout.memes.get("trust", 0) + 1


def _setout(world: World) -> None:
    hero = world.get("hero")
    scout = world.get("scout")
    world.say(
        f"They went to {world.setting.place}, where the path curled ahead like a ribbon."
    )
    world.say(
        f"{hero.id} wanted to lead, and {scout.id} promised to watch the ration box carefully."
    )


def _mystery(world: World) -> None:
    hero = world.get("hero")
    scout = world.get("scout")
    ration = world.get("ration")
    ration.carried_by = None
    ration.location = "hidden under a leaf"
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    scout.memes["caution"] = scout.memes.get("caution", 0) + 1
    world.say(
        f"Then the ration box was not in the pack anymore."
    )
    world.say(
        f"{hero.id} stopped at once. {hero.pronoun().capitalize()} did not rush ahead; {hero.pronoun()} looked around carefully."
    )
    world.say(
        f'"Where did the ration go?" {hero.id} asked. "We should solve this before anyone gets too hungry."'
    )


def _search(world: World) -> None:
    hero = world.get("hero")
    scout = world.get("scout")
    ration = world.get("ration")
    tool = choose_tool_for_mystery()
    world.say(
        f"{scout.id} held up {tool.phrase}, and the team used it to {tool.action}."
    )
    world.say(
        f"{hero.id} checked the ground, while {scout.id} checked the bag straps and the shady spots by the stones."
    )
    if ration.location == "hidden under a leaf":
        world.say(
            f"At last, they found the ration box under a leaf near a small root."
        )
        ration.carried_by = hero.id
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        scout.memes["relief"] = scout.memes.get("relief", 0) + 1


def _resolution(world: World) -> None:
    hero = world.get("hero")
    scout = world.get("scout")
    ration = world.get("ration")
    world.say(
        f"{hero.id} opened the ration box only after everyone stood together in a safe circle."
    )
    world.say(
        f"They shared the crackers and fruit one careful piece at a time, and nobody grabbed more than their share."
    )
    world.say(
        f"{scout.id} smiled and said the mystery was solved best by staying calm, looking closely, and working together."
    )
    ration.location = "shared at camp"
    ration.carried_by = None
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    scout.memes["joy"] = scout.memes.get("joy", 0) + 2


def tell(setting: Setting, supply: Supply, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        memes={"trait": trait},
    ))
    scout = world.add(Entity(
        id="scout",
        kind="character",
        type="mother",
        label="the scout leader",
        memes={"trust": 1},
    ))
    ration = world.add(Entity(
        id="ration",
        kind="thing",
        type=supply.type,
        label=supply.label,
        phrase=supply.phrase,
        owner=hero.id,
        caretaker=scout.id,
        carried_by=scout.id,
        location="in the pack",
    ))
    world.facts.update(hero=hero, scout=scout, ration=ration, supply=supply)

    _intro(world)
    world.para()
    _setout(world)
    _mystery(world)
    world.para()
    _search(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    supply = _safe_fact(world, f, "supply")
    return [
        f'Write a child-friendly adventure story about a team and a "{supply.tag}" mystery.',
        f"Tell a cautionary teamwork tale where {hero.id} loses a ration and solves the problem carefully.",
        f"Write a short story with a brave search, a missing ration, and a gentle ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    scout = world.get("scout")
    ration = world.get("ration")
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was where the ration box went after it disappeared from the pack.",
        ),
        QAItem(
            question=f"How did {hero.id} and {scout.id} solve the problem?",
            answer="They stayed calm, looked closely, used a tool to search, and found the ration under a leaf.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer="The ration was found, everyone shared it safely, and the team felt proud of working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ration?",
            answer="A ration is a planned amount of food or supplies saved for a trip or a hard day.",
        ),
        QAItem(
            question="Why should explorers be cautious?",
            answer="Explorers should be cautious so they can avoid getting lost, hurt, or careless with important supplies.",
        ),
        QAItem(
            question="Why does teamwork help on an adventure?",
            answer="Teamwork helps because different helpers can look in different places, share ideas, and solve problems faster.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A ration story is valid when a place exists, the supply exists, and the story
% includes a safe, solvable mystery that ends in teamwork.
valid_place(P) :- place(P).
valid_supply(S) :- supply(S).
valid_story(P, S) :- valid_place(P), valid_supply(S).

% A mystery is solvable when the ration can be found, and the group can share it.
solvable(P, S) :- valid_story(P, S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in SUPPLIES:
        lines.append(asp.fact("supply", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asps - py:
        print("  only in clingo:", sorted(asps - py))
    if py - asps:
        print("  only in python:", sorted(py - asps))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary teamwork mystery about a ration on an adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [
        (p, s)
        for p, s in combos
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "supply", None) is None or s == getattr(args, "supply", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, supply = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, supply=supply, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SUPPLIES, params.supply), params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="trail", supply="ration_box", name="Maya", gender="girl", trait="careful"),
    StoryParams(place="canyon", supply="trail_ration", name="Leo", gender="boy", trait="curious"),
    StoryParams(place="camp", supply="ration_box", name="Ivy", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible ration story combos:\n")
        for p, s in combos:
            print(f"  {p:8} {s}")
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
            header = f"### {p.name}: {p.place} ({p.supply})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
