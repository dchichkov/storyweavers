#!/usr/bin/env python3
"""
storyworlds/worlds/rib_thunk_reconciliation_superhero_story.py
==============================================================

A tiny superhero storyworld about a hero, a thunk, a hurt rib, and a
reconciliation. The world is physical and emotional: bodies have meters and
memes, the city has places, a small mishap causes tension, and a repaired
relationship ends the story with a change that can be seen and felt.

Seed premise:
- A young superhero hears a thunk during a rescue.
- A rib gets hurt, making the hero slow and grumpy.
- A teammate helps with the repair and the two reconcile.
- The ending proves the team is stronger, calmer, and back on the street.

This world keeps the prose concrete, child-facing, and state-driven.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    ally: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    id: str
    label: str
    detail: str
    outdoors: bool = True
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
class Mission:
    id: str
    label: str
    verb: str
    reason: str
    risk: str
    noise: str
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
class Injury:
    id: str
    label: str
    body_part: str
    complaint: str
    makes_slow: bool = True
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
class Repair:
    id: str
    label: str
    action: str
    tool: str
    promise: str
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
class StoryParams:
    city: str
    mission: str
    injury: str
    repair: str
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        c = World()
        c.entities = _copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


CITIES = {
    "downtown": Location("downtown", "downtown", "the tall buildings and bright street lamps"),
    "harbor": Location("harbor", "the harbor", "the docks, ropes, and gulls"),
    "subway": Location("subway", "the subway station", "the echoing stairs and rushing trains", outdoors=False),
}

MISSIONS = {
    "thunk": Mission(
        id="thunk",
        label="the thunk",
        verb="leap over a falling sign",
        reason="a little runaway robot had rolled into the crosswalk",
        risk="a bump against a metal rail",
        noise="thunk",
        tags={"thunk", "robot", "rescue"},
    ),
    "thud": Mission(
        id="thud",
        label="the thud",
        verb="catch a slipping kite string",
        reason="a windy day had tangled a kite on the rooftop edge",
        risk="a hard knock against a window ledge",
        noise="thud",
        tags={"thud", "kite", "rescue"},
    ),
}

INJURIES = {
    "rib": Injury(
        id="rib",
        label="a sore rib",
        body_part="rib",
        complaint="her rib hurt when she breathed too deep",
        tags={"rib", "hurt"},
    ),
    "side": Injury(
        id="side",
        label="a bruised side",
        body_part="side",
        complaint="his side ached whenever he twisted",
        tags={"side", "hurt"},
    ),
}

REPAIRS = {
    "reconciliation": Repair(
        id="reconciliation",
        label="reconciliation",
        action="talk it out",
        tool="a cool wrap and a soft chair",
        promise="they could keep helping without being sharp with each other",
        tags={"reconciliation", "talk", "heal"},
    ),
    "apology": Repair(
        id="apology",
        label="apology",
        action="say sorry and share the job",
        tool="a calm breath and a water bottle",
        promise="they could work as a team again",
        tags={"apology", "talk", "heal"},
    ),
}


@dataclass
class StoryParamsResolved:
    city: Location
    mission: Mission
    injury: Injury
    repair: Repair
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: a thunk, a sore rib, and reconciliation.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero-name")
    ap.add_argument("--ally-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally-type", choices=["girl", "boy"])
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
    city = _safe_lookup(CITIES, getattr(args, "city", None)) if getattr(args, "city", None) else rng.choice(list(CITIES.values()))
    mission = _safe_lookup(MISSIONS, getattr(args, "mission", None)) if getattr(args, "mission", None) else rng.choice(list(MISSIONS.values()))
    injury = _safe_lookup(INJURIES, getattr(args, "injury", None)) if getattr(args, "injury", None) else rng.choice(list(INJURIES.values()))
    repair = _safe_lookup(REPAIRS, getattr(args, "repair", None)) if getattr(args, "repair", None) else rng.choice(list(REPAIRS.values()))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    ally_type = getattr(args, "ally_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Nova", "Sky", "Maya", "Jett", "Piper"])
    ally_name = getattr(args, "ally_name", None) or rng.choice([n for n in ["Bolt", "Rio", "Nico", "Ivy", "Zane"] if n != hero_name])
    if injury.id == "rib" and mission.id not in {"thunk", "thud"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(city.id, mission.id, injury.id, repair.id, hero_name, hero_type, ally_name, ally_type)


def tell(city: Location, mission: Mission, injury: Injury, repair: Repair, hero_name: str, hero_type: str, ally_name: str, ally_type: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, label=hero_name))
    ally = world.add(Entity(ally_name, kind="character", type=ally_type, label=ally_name))
    hero.meters["hurt"] = 0.0
    hero.meters["slow"] = 0.0
    hero.memes["pride"] = 1.0
    ally.memes["worry"] = 1.0
    world.facts.update(city=city, mission=mission, injury=injury, repair=repair, hero=hero, ally=ally)

    world.say(f"{hero_name} was a little superhero who loved helping people in {city.label}.")
    world.say(f"{hero_name} and {ally_name} were on patrol when {mission.noise} went thunk near {city.detail}.")
    world.say(f"{mission.reason}. {hero_name} sprang forward to {mission.verb}, just as the rail jolted hard against {hero_name}'s side.")

    hero.meters["hurt"] += 1
    hero.meters["slow"] += 1
    hero.memes["grit"] += 1
    world.para()
    world.say(f"{hero_name} winced. {injury.complaint.capitalize()}.")
    world.say(f"{ally_name} saw the stumble and frowned, because the rush had turned into a hurt feeling too.")

    hero.memes["cross"] = 1.0
    ally.memes["guilt"] = 1.0
    world.para()
    world.say(f"{hero_name} snapped, and {ally_name} snapped back.")
    world.say(f"For a moment the team felt split apart, like two capes tugging in different winds.")

    world.para()
    hero.memes["cross"] = 0.0
    ally.memes["guilt"] = 0.0
    hero.memes["trust"] = 1.0
    ally.memes["trust"] = 1.0
    hero.meters["slow"] = 0.0
    world.say(f"Then they both stopped. {ally_name} brought {repair.tool} and said, '{repair.action.capitalize()}.'")
    world.say(f"{hero_name} took a breath, listened, and nodded. That was reconciliation: the sharp words went soft, and they chose to help each other again.")
    world.say(f"With {repair.tool}, {hero_name} could stand straighter. {repair.promise.capitalize()}.")
    world.say(f"At sunset, the two heroes flew home together, side by side, with the thunk behind them and the rib no longer in charge.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the word "{f["mission"].noise}" and ends with reconciliation.',
        f"Tell a gentle story where {f['hero'].id} gets a sore rib during a rescue, argues with {f['ally'].id}, and then makes up.",
        f"Write a child-friendly superhero tale about a thunk, a hurt rib, and two heroes learning to work together again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    mission = f["mission"]
    injury = f["injury"]
    repair = f["repair"]
    city = f["city"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little superhero, and {ally.id}, who help each other in {city.label}.",
        ),
        QAItem(
            question=f"What made the rescue go thunk?",
            answer=f"{mission.reason.capitalize()}. When {hero.id} rushed in, the move bumped hard enough to cause the thunk.",
        ),
        QAItem(
            question=f"What hurt {hero.id}?",
            answer=f"{injury.complaint.capitalize()} because {hero.id} took a hard bump during the rescue.",
        ),
        QAItem(
            question=f"How did {hero.id} and {ally.id} fix their argument?",
            answer=f"They chose {repair.label}: they slowed down, talked it out, and helped each other again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rib?",
            answer="A rib is one of the bones that helps make a body strong and protects the chest.",
        ),
        QAItem(
            question="What does thunk sound like?",
            answer="Thunk sounds like a hard bump or knock, like something heavy tapping against metal or wood.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, make up, and start being kind to each other again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for cid in CITIES:
        lines.append(asp.fact("city", cid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("noise", mid, m.noise))
    for iid, i in INJURIES.items():
        lines.append(asp.fact("injury", iid))
        lines.append(asp.fact("body_part", iid, i.body_part))
    for rid in REPAIRS:
        lines.append(asp.fact("repair", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(C, M, I, R) :- city(C), mission(M), injury(I), repair(R), noise(M, thunk), body_part(I, rib).
#show valid_story/4.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(CITIES, params.city), _safe_lookup(MISSIONS, params.mission), _safe_lookup(INJURIES, params.injury), _safe_lookup(REPAIRS, params.repair), params.hero_name, params.hero_type, params.ally_name, params.ally_type)
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


def resolve_all() -> list[StoryParams]:
    out = []
    for c in CITIES:
        for m in MISSIONS:
            for i in INJURIES:
                for r in REPAIRS:
                    out.append(StoryParams(c, m, i, r, "Nova", "girl", "Bolt", "boy"))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(f"OK: ASP loaded ({len(model)} shown atoms).")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in resolve_all():
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 40:
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
