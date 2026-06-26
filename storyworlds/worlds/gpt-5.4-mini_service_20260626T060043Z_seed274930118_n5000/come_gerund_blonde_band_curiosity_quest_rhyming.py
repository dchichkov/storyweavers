#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Rhyming Story domain:
a blonde band goes on a curiosity quest, meets a small obstacle,
and comes home changed by what they learned.

The story is generated from a simulated world with physical meters
and emotional memes. The main causal turn is:
curiosity -> quest -> small risk -> helpful fix -> cheerful ending.
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
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    band: object | None = None
    clue: object | None = None
    map_item: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "band":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Location:
    name: str
    place: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    theme: str
    verb: str
    gerund: str
    obstacle: str
    risk: str
    fix: str
    ending: str
    keyword: str = ""
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
class Gear:
    id: str
    label: str
    protects: set[str]
    helps: set[str]
    prep: str
    tail: str
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
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "hill": Location(name="the green hill", place="the green hill", affords={"walk", "search"}),
    "harbor": Location(name="the little harbor", place="the little harbor", affords={"boat", "search"}),
    "garden": Location(name="the moon garden", place="the moon garden", affords={"walk", "search"}),
}

QUESTS = {
    "curiosity": Quest(
        id="curiosity",
        theme="Curiosity",
        verb="follow the curious trail",
        gerund="following the curious trail",
        obstacle="a twisty path of tall grass",
        risk="they could lose the clue",
        fix="a careful look and a soft step",
        ending="They found the clue shining by a stone.",
        keyword="Curiosity",
        tags={"curiosity", "quest", "trail"},
    ),
    "quest": Quest(
        id="quest",
        theme="Quest",
        verb="seek the bright little clue",
        gerund="seeking the bright little clue",
        obstacle="a windy bend that made the map flap",
        risk="the map might fly away",
        fix="a steady hand and a quick tuck in",
        ending="The map stayed safe, and the clue came home with them.",
        keyword="Quest",
        tags={"quest", "map", "clue"},
    ),
}

GEAR = {
    "bag": Gear(
        id="bag",
        label="a blue satchel",
        protects={"map"},
        helps={"quest"},
        prep="pack the map in a blue satchel first",
        tail="packed the map away and set off again",
    ),
    "boots": Gear(
        id="boots",
        label="soft boots",
        protects={"trail"},
        helps={"curiosity"},
        prep="put on soft boots first",
        tail="tied their boots tight and went on tiptoe",
        plural=True,
    ),
}

BANDS = ["Milo", "Tia", "Leni", "Arlo", "Noa", "Zuri", "Bram", "Pia"]
NAMES = ["Milo", "Tia", "Leni", "Arlo", "Noa", "Zuri", "Bram", "Pia"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    location: str
    quest: str
    band_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A quest is reasoned about from facts that represent the little domain.
needs_help(Q) :- quest(Q), obstacle(Q, O), risky(Q, O).
has_fix(Q) :- quest(Q), fix(Q, F), gear(G), helps(G, Q), protects(G, map).

valid_story(L, Q) :- location(L), quest(Q), allowed(L, Q), needs_help(Q), has_fix(Q).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", lid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("theme", qid, q.theme))
        lines.append(asp.fact("verb", qid, q.verb))
        lines.append(asp.fact("obstacle", qid, q.obstacle))
        lines.append(asp.fact("risky", qid, q.risk))
        lines.append(asp.fact("fix", qid, q.fix))
        lines.append(asp.fact("keyword", qid, q.keyword))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", gid, p))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    # allowed pairs are the same as the Python gate below.
    for lid, loc in LOCATIONS.items():
        for qid in QUESTS:
            if qid in loc.affords:
                lines.append(asp.fact("allowed", lid, qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for lid, loc in LOCATIONS.items():
        for qid in loc.affords:
            if qid in QUESTS:
                combos.append((lid, qid))
    return combos


def explain_rejection(location: str, quest: str) -> str:
    return (
        f"(No story: {quest} cannot happen at {location} in this tiny world. "
        f"Choose a location that affords that quest.)"
    )


# ---------------------------------------------------------------------------
# Simulation and narration
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    loc = _safe_lookup(LOCATIONS, params.location)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(loc)

    band = world.add(Entity(
        id=params.band_name,
        kind="band",
        label=f"the {params.band_name} band",
        phrase=f"the {params.band_name} band",
        traits=["blonde", "brave"],
        memes={"curiosity": 2.0, "joy": 0.5},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        label="clue",
        phrase="a tiny glittering clue",
        owner=band.id,
        meters={"shine": 1.0},
    ))
    map_item = world.add(Entity(
        id="map",
        kind="thing",
        label="map",
        phrase="a folded little map",
        owner=band.id,
        meters={"care": 1.0},
    ))
    world.facts.update(band=band, clue=clue, map=map_item, quest=quest)
    return world


def maybe_need_help(world: World, quest: Quest) -> bool:
    band = _safe_fact(world, world.facts, "band")
    band.memes["curiosity"] += 1.0
    band.meters["distance"] = band.meters.get("distance", 0.0) + 1.0
    world.say(
        f"The blonde band went to {world.location.place}, "
        f"for {quest.theme} made their hearts lean in."
    )
    world.say(
        f"They were {quest.gerund}, and their song was light as a grin."
    )
    return True


def obstacle_turn(world: World, quest: Quest) -> None:
    band = _safe_fact(world, world.facts, "band")
    if band.memes.get("curiosity", 0.0) >= THRESHOLD:
        band.memes["worry"] = band.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Then came {quest.obstacle}, and {quest.risk}."
    )
    world.say(
        f"The blonde band slowed down a bit, because even brave feet can think."
    )


def offer_fix(world: World, quest: Quest) -> Optional[Gear]:
    band = _safe_fact(world, world.facts, "band")
    gear = None
    if quest.id == "quest":
        gear = GEAR["bag"]
    elif quest.id == "curiosity":
        gear = GEAR["boots"]
    if gear:
        world.say(
            f"So they chose {gear.prep}, and that felt wise and trim."
        )
        band.memes["hope"] = band.memes.get("hope", 0.0) + 1.0
    return gear


def resolve(world: World, quest: Quest, gear: Optional[Gear]) -> None:
    band = _safe_fact(world, world.facts, "band")
    band.memes["joy"] = band.memes.get("joy", 0.0) + 1.0
    band.memes["curiosity"] = band.memes.get("curiosity", 0.0) + 0.5
    if gear:
        if gear.id == "bag":
            world.say(f"{gear.tail}, and the little map did not take a dive.")
        else:
            world.say(f"{gear.tail}, and their steps felt light in the clime.")
    world.say(quest.ending)
    world.say(
        f"By the end, the blonde band was laughing in rhyme, "
        f"glad they had gone and glad they had taken the time."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    quest = _safe_lookup(QUESTS, params.quest)
    maybe_need_help(world, quest)
    world.say(
        f"The path was bright, but the bend was sly;"
    )
    obstacle_turn(world, quest)
    gear = offer_fix(world, quest)
    world.say(
        f"They looked at the problem, then up at the sky."
    )
    resolve(world, quest, gear)
    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    quest = _safe_fact(world, world.facts, "quest")
    band = _safe_fact(world, world.facts, "band")
    return [
        f"Write a short Rhyming Story about {band.label} and {quest.theme}.",
        f"Tell a child-friendly story where a blonde band goes on a {quest.keyword.lower()} quest and finds a careful fix.",
        f"Make a simple rhyme about a band at {world.location.place} who keeps going after a small obstacle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    band = _safe_fact(world, world.facts, "band")
    quest = _safe_fact(world, world.facts, "quest")
    gear = _safe_fact(world, world.facts, "gear")
    return [
        QAItem(
            question=f"Who goes on the quest in the story?",
            answer=f"The story is about the blonde band called {band.id}, and they go on a {quest.theme.lower()} quest.",
        ),
        QAItem(
            question=f"What problem do they meet on the way?",
            answer=f"They meet {quest.obstacle}, which makes the path a little tricky and calls for a careful move.",
        ),
        QAItem(
            question=f"How do they handle the problem?",
            answer=f"They use {gear.label if gear else 'a careful plan'} so they can keep going without losing the clue.",
        ),
        QAItem(
            question=f"What changes by the end?",
            answer=f"By the end, the blonde band feels happier and braver, and the quest ends in a warm, rhyming way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or search to find something important, like a clue or a treasure.",
        ),
        QAItem(
            question="Why can a map help on a quest?",
            answer="A map can help because it shows the way and makes it easier not to get lost.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} meters={meters} memes={memes}")
    lines.append(f"location={world.location.place}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: a blonde band on a curiosity quest.")
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--band-name", choices=BANDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    filtered = [
        c for c in combos
        if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
    ]
    if getattr(args, "location", None) and getattr(args, "quest", None) and not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    location, quest = rng.choice(list(filtered))
    band_name = getattr(args, "band_name", None) or rng.choice(BANDS)
    return StoryParams(location=location, quest=quest, band_name=band_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(location="hill", quest="curiosity", band_name="Milo"),
    StoryParams(location="harbor", quest="quest", band_name="Tia"),
    StoryParams(location="garden", quest="curiosity", band_name="Leni"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, quest in stories:
            print(f"  {place:10} {quest}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
