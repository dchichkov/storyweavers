#!/usr/bin/env python3
"""
A standalone Storyweavers world: a tall-tale dialogue about a magnet and a forum.

This world simulates a small, child-facing domain where a town's bulletin forum
gets shaken up by a mysterious magnet. The story is driven by a tiny world model
with physical meters and emotional memes, plus a declarative ASP twin for the
reasonableness gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "uncle", "brother", "cowboy"}
        female = {"girl", "woman", "mother", "mom", "aunt", "sister"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
class Actor:
    name: str
    type: str
    trait: str
    town_role: str
    seed_voice: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gadget:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    actor: str
    prize: str
    gadget: str
    name: str
    gender: str
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


PLACES = {
    "forum_square": Setting(place="the town forum square", afford={"magnet"}),
    "school_hall": Setting(place="the school hall bulletin forum", afford={"magnet"}),
    "library_nook": Setting(place="the library forum corner", afford={"magnet"}),
}

ACTORS = {
    "boy": Actor(name="", type="boy", trait="whopper-bright", town_role="storyteller", seed_voice="he"),
    "girl": Actor(name="", type="girl", trait="bright-eyed", town_role="clerk", seed_voice="she"),
}

PRIZES = {
    "pinboard": Prize(label="pinboard", phrase="a shiny notice pinboard", type="pinboard", region="wall"),
    "papers": Prize(label="papers", phrase="a stack of important papers", type="papers", region="table", plural=True),
    "clock": Prize(label="clock", phrase="an old brass clock", type="clock", region="wall"),
}

GADGETS = {
    "wooden_box": Gadget(
        id="wooden_box",
        label="a wooden box lined with straw",
        covers={"wall", "table"},
        guards={"jostle"},
        prep="set the magnet inside a wooden box lined with straw",
        tail="patted the box shut and kept the magnet from tugging at the room",
    ),
    "lead_wrap": Gadget(
        id="lead_wrap",
        label="a heavy lead wrap",
        covers={"wall"},
        guards={"pull"},
        prep="wrap the magnet in a heavy lead wrap",
        tail="wrapped the magnet so tight even its whisper could not wander",
    ),
}

NAMES_BY_GENDER = {
    "girl": ["Mina", "Dot", "Ivy", "June", "Nell"],
    "boy": ["Otis", "Bram", "Toby", "Wes", "Finn"],
}

TRAITS = ["spry", "curious", "lively", "pluckier-than-a-goose", "determined"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A forum story is reasonable when the chosen prize could be tugged or jostled by a magnet,
% and some gadget actually protects the at-risk object.
forum_risk(P) :- prize(P), risk_region(P, R), magnet_tugs(R).
has_fix(P) :- forum_risk(P), gadget(G), covers(G, R), risk_region(P, R), guards(G, tug).
valid_story(Place, Prize, Gadget) :- setting(Place), affords(Place, magnet), prize(Prize), gadget(Gadget), has_fix(Prize).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("affords", pid, a))
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("risk_region", pr_id, pr.region))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    lines.append(asp.fact("magnet_tugs", "wall"))
    lines.append(asp.fact("magnet_tugs", "table"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def prize_at_risk(prize: Prize) -> bool:
    return prize.region in {"wall", "table"}


def select_gadget(prize: Prize) -> Optional[Gadget]:
    for gadget in GADGETS.values():
        if prize.region in gadget.covers:
            return gadget
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in PLACES.items():
        if "magnet" not in setting.afford:
            continue
        for prize_id, prize in PRIZES.items():
            if not prize_at_risk(prize):
                continue
            if select_gadget(prize) is None:
                continue
            for gadget_id in GADGETS:
                out.append((place, prize_id, gadget_id))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    actor_template = _safe_lookup(ACTORS, params.gender)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"{params.name}, the {actor_template.trait} {actor_template.town_role}",
        meters={"curiosity": 0.0, "power": 0.0},
        memes={"wonder": 0.0, "worry": 0.0, "delight": 0.0, "pride": 0.0},
    ))
    prize = world.add(Entity(
        id=params.prize,
        type=_safe_lookup(PRIZES, params.prize).type,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        caretaker=params.name,
    ))
    gadget = _safe_lookup(GADGETS, params.gadget)
    world.facts.update(hero=hero, prize=prize, gadget=gadget, setting=world.setting, params=params)
    return world


def _narrate_setup(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    world.say(
        f"In the little town forum, {hero.name} was known as a {hero.phrase}. "
        f"{hero.pronoun().capitalize()} liked collecting stories that rang like tin spoons."
    )
    world.say(
        f"One day, {hero.name} found {prize.phrase} waiting near the forum bench, "
        f"and {hero.pronoun('possessive')} eyes grew wide as lanterns."
    )


def _narrate_dialogue(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    gadget: Gadget = _safe_fact(world, world.facts, "gadget")

    world.say(
        f'"Look at that magnet," said {hero.name}, "it could pull a fishhook from the moon!"'
    )
    world.say(
        f'"It could also tug this {prize.label}," said the forum keeper, "and then I would have a tumble of trouble."'
    )
    hero.meters["power"] += 1.0
    hero.memes["wonder"] += 1.0
    hero.memes["worry"] += 1.0
    prize.meters["risk"] = 1.0
    world.trace.append("hero notices the magnet could disturb the forum prize")

    world.say(
        f'"Then let us be smarter than the wind," said {hero.name}. '
        f'"We can {gadget.prep}."'
    )
    world.say(
        f'"Now that," said the keeper, "sounds like the sort of fix a clever crow would applaud."'
    )


def _narrate_turn(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    gadget: Gadget = _safe_fact(world, world.facts, "gadget")
    prize.meters["risk"] = 0.0
    prize.meters["safe"] = 1.0
    hero.memes["delight"] += 1.0
    hero.memes["pride"] += 1.0

    world.say(
        f"So {hero.name} {gadget.tail}, and the magnet became quiet as a kitten in mittens."
    )
    world.say(
        f"The {prize.label} stayed steady on the forum wall, and not one paper fluttered away."
    )
    world.say(
        f'"That magnet is still a mighty thing," said {hero.name}, "but now it is minding its manners."'
    )


def _narrate_resolution(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    world.say(
        f"Before long, the whole forum was laughing, and {hero.name} stood tall as a barn beam."
    )
    world.say(
        f"In that bright little town, the magnet stayed safe, the {prize.label} stayed put, "
        f"and the story ended with the forum shining tidy and proud."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _narrate_setup(world)
    world.say(
        f'At the forum square, the magnet drew a crowd, and every child leaned in to hear the tale.'
    )
    _narrate_dialogue(world)
    _narrate_turn(world)
    _narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a tall tale for a child where a magnet causes trouble in a forum and the characters solve it by talking.",
        f"Tell a dialogue-heavy story about {f['hero'].name} protecting {f['prize'].label} from a magnet at the forum.",
        "Make the setting a town forum and end with a clever, safe fix for the magnet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    gadget: Gadget = _safe_fact(world, world.facts, "gadget")
    return [
        QAItem(
            question=f"What did {hero.name} find near the forum bench?",
            answer=f"{hero.name} found {prize.phrase} near the forum bench.",
        ),
        QAItem(
            question="Why did the forum keeper worry about the magnet?",
            answer=f"The keeper worried because the magnet could tug at the {prize.label} and make trouble in the forum.",
        ),
        QAItem(
            question=f"How did {hero.name} keep the magnet from causing a mess?",
            answer=f"{hero.name} used {gadget.label} and {gadget.tail} so the magnet stayed quiet and the {prize.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a magnet?",
            answer="A magnet is an object that can pull on some metals without touching them.",
        ),
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to talk, share news, or post notices.",
        ),
        QAItem(
            question="Why can a magnet be tricky near papers and pins?",
            answer="A strong magnet can tug metal bits like pins or clips, which can make neat things spill or shift.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------

def valid_names(gender: str) -> list[str]:
    return NAMES_BY_GENDER[gender]


def explain_invalid(place: str, prize: str, gadget: str) -> str:
    return f"(No story: {place}, {prize}, and {gadget} do not make a safe forum-mag​net tall tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(valid_names(gender))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    gadget = getattr(args, "gadget", None) or rng.choice(list(GADGETS))

    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    if (place, prize, gadget) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, actor=gender, prize=prize, gadget=gadget, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print("--- trace ---")
        for item in sample.world.trace:
            print(item)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="forum_square", actor="girl", prize="pinboard", gadget="wooden_box", name="Mina", gender="girl"),
    StoryParams(place="school_hall", actor="boy", prize="papers", gadget="wooden_box", name="Otis", gender="boy"),
    StoryParams(place="library_nook", actor="girl", prize="clock", gadget="lead_wrap", name="June", gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale dialogue storyworld: magnet + forum.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl3 = {(p, pr, g) for (p, pr, g) in cl}
    if py == cl3:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(py - cl3))
    print(" only in asp:", sorted(cl3 - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        for item in stories:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### story {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
