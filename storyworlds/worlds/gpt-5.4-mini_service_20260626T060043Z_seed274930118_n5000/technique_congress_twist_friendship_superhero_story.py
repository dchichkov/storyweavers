#!/usr/bin/env python3
"""
storyworlds/worlds/technique_congress_twist_friendship_superhero_story.py
========================================================================

A small superhero story world about a hero, a public congress of helpers,
a useful technique, and a friendship twist that changes the ending.

The seed idea:
- A young hero is excited to show a technique at a congress.
- The plan goes wrong or feels shaky in front of a crowd.
- A friend steps in with support, turning embarrassment into teamwork.
- The ending proves the friendship and the technique both matter.

This world keeps the simulation tiny but state-driven:
- characters have meters and memes,
- objects can be owned, carried, used, or broken,
- a technique may require a tool or a partner,
- the congress can be calm, crowded, or impressed,
- the friendship twist resolves the tension.

The story text is authored from the simulated state, not from a frozen template.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
class Place:
    id: str
    label: str
    crowd: str = "quiet"
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
class Technique:
    id: str
    label: str
    verb: str
    needs: set[str] = field(default_factory=set)
    uses: str = ""
    risk: str = ""
    success: str = ""
    keyword: str = ""
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
    phrase: str
    helps: set[str] = field(default_factory=set)
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
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
class StoryParams:
    place: str
    hero_type: str
    hero_name: str
    friend_name: str
    friend_type: str
    technique: str
    tool: str
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


PLACES = {
    "city_hall": Place(id="city_hall", label="the city hall", crowd="crowded", affords={"gathering", "demo"}),
    "museum_hall": Place(id="museum_hall", label="the museum hall", crowd="quiet", affords={"gathering", "demo"}),
    "school_stage": Place(id="school_stage", label="the school stage", crowd="crowded", affords={"demo", "speech"}),
}

TECHNIQUES = {
    "loud_lift": Technique(
        id="loud_lift",
        label="the Loud Lift",
        verb="lift the fallen gate",
        needs={"tool"},
        uses="a bright lever",
        risk="it might slip",
        success="the gate rose smoothly",
        keyword="technique",
        tags={"technique", "lift"},
    ),
    "shield_spin": Technique(
        id="shield_spin",
        label="the Shield Spin",
        verb="spin the shield to block the wind",
        needs=set(),
        uses="a round shield",
        risk="the shield could wobble",
        success="the spin made a safe wall",
        keyword="technique",
        tags={"technique", "shield"},
    ),
    "signal_snap": Technique(
        id="signal_snap",
        label="the Signal Snap",
        verb="snap a rescue signal into the sky",
        needs={"friend"},
        uses="a clear hand sign",
        risk="the crowd might not notice",
        success="the signal reached every helper",
        keyword="technique",
        tags={"technique", "signal"},
    ),
}

TOOLS = {
    "lever": Tool(id="lever", label="lever", phrase="a bright lever", helps={"loud_lift"}),
    "shield": Tool(id="shield", label="shield", phrase="a round shield", helps={"shield_spin"}),
    "whistle": Tool(id="whistle", label="whistle", phrase="a silver whistle", helps={"signal_snap"}),
}

HERO_NAMES = ["Nova", "Skye", "Milo", "Zara", "Tess", "Juno"]
FRIEND_NAMES = ["Pip", "Rae", "Bea", "Kai", "Luca", "Nia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, tech in TECHNIQUES.items():
            for tool_id, tool in TOOLS.items():
                if tid in tool.helps and pid in PLACES:
                    combos.append((pid, tid, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: technique, congress, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--technique", choices=TECHNIQUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "technique", None) is None or c[1] == getattr(args, "technique", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, technique, tool = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    if friend_name == hero_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_type=hero_type,
        hero_name=hero_name,
        friend_name=friend_name,
        friend_type=friend_type,
        technique=technique,
        tool=tool,
    )


def _do_demo(world: World, hero: Entity, friend: Entity, tech: Technique, tool: Entity, narrate: bool = True) -> None:
    hero.memes["nervous"] += 1
    if tech.id == "signal_snap":
        hero.memes["alone"] += 1
    if narrate:
        world.say(f"{hero.id} tried {tech.label} with {tool.label}, but the {world.place.label} was full of watching faces.")
    if tech.id == "loud_lift":
        hero.meters["strain"] += 1
        if tool.used_by != hero.id:
            hero.memes["embarrassed"] += 1
    elif tech.id == "shield_spin":
        hero.meters["balance"] += 1
    elif tech.id == "signal_snap":
        hero.memes["hopeless"] += 1
    friend.memes["care"] += 1


def predict(world: World, hero: Entity, friend: Entity, tech: Technique, tool: Entity) -> dict:
    sim = world.copy()
    _do_demo(sim, sim.get(hero.id), sim.get(friend.id), tech, sim.get(tool.id), narrate=False)
    return {
        "stumble": sim.get(hero.id).memes.get("embarrassed", 0) >= THRESHOLD or sim.get(hero.id).memes.get("hopeless", 0) >= THRESHOLD,
        "friend_help": sim.get(friend.id).memes.get("care", 0) >= THRESHOLD,
    }


def tell(place: Place, tech: Technique, tool_cfg: Tool, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    tool = world.add(Entity(id=tool_cfg.id, kind="thing", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id))
    hero.meters["hope"] = 1
    hero.memes["pride"] = 1
    friend.memes["loyal"] = 1

    world.say(f"{hero.id} was a little {hero.type} hero who loved {tech.keyword} days and big saved-the-day plans.")
    world.say(f"{hero.id} had trained {tech.verb} using {tool.phrase}.")
    world.say(f"{hero.id}'s friend {friend.id} always came to the {place.label} to cheer for brave ideas.")

    world.para()
    world.say(f"On the day of the congress, {place.label} was {place.crowd} and bright with flags.")
    world.say(f"{hero.id} stepped up to show {tech.label}, because {tech.success} sounded wonderful.")

    pred = predict(world, hero, friend, tech, tool)
    world.facts.update(hero=hero, friend=friend, tool=tool, tech=tech, place=place, predicted=pred)

    if tech.id == "signal_snap":
        tool.used_by = None
    else:
        tool.used_by = hero.id

    world.para()
    _do_demo(world, hero, friend, tech, tool, narrate=True)
    if pred["stumble"]:
        world.say(f"Then something went wrong: {tech.risk}.")

    if tech.id == "loud_lift":
        world.say(f"{hero.id} could not finish the lift alone, and the crowd got very quiet.")
    elif tech.id == "shield_spin":
        world.say(f"The shield wobbled, and {hero.id} felt the mistake in every eye at the congress.")
    else:
        world.say(f"The signal snapped up, but no one answered right away, so {hero.id}'s face fell.")

    world.para()
    friend.memes["support"] += 1
    hero.memes["friendship"] += 1
    hero.memes["embarrassed"] = 0
    hero.memes["hopeless"] = 0

    if tech.id == "loud_lift":
        friend.meters["steady"] = 1
        world.say(f"Then {friend.id} rushed over with a grin and held the lever steady.")
        world.say(f"Together they tried again, and {tech.success}.")
    elif tech.id == "shield_spin":
        world.say(f"{friend.id} stepped beside {hero.id} and matched the spin, shoulder to shoulder.")
        world.say(f"That friendship twist made the shield turn smoothly, and {tech.success}.")
    else:
        tool.used_by = friend.id
        world.say(f"{friend.id} heard the silence and answered with a clear whistle from the edge of the crowd.")
        world.say(f"At once, helpers turned, and {tech.success}.")

    world.say(f"{hero.id} smiled at {friend.id}, because the best superhero trick was trusting a friend at the right moment.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    tech = _safe_fact(world, f, "tech")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a short superhero story for a young child about {hero.id} showing a {tech.keyword} at {place.label}.",
        f"Tell a story about a congress of helpers where {friend.id} saves the day by supporting {hero.id}'s technique.",
        f"Write a gentle story with a twist of friendship, a brave technique, and a happy ending at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    tech = _safe_fact(world, f, "tech")
    place = _safe_fact(world, f, "place")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was the superhero story about at {place.label}?",
            answer=f"It was about {hero.id}, a little {hero.type} hero, and {friend.id}, who stayed close as a friend.",
        ),
        QAItem(
            question=f"What technique did {hero.id} want to show at the congress?",
            answer=f"{hero.id} wanted to show {tech.label}, a brave {tech.keyword} technique that used {tool.label}.",
        ),
        QAItem(
            question=f"Why did the story turn into a friendship twist?",
            answer=f"It turned that way because {hero.id} started to struggle, and {friend.id} helped so the technique could work.",
        ),
        QAItem(
            question=f"How did the ending prove that the technique and friendship both mattered?",
            answer=f"They used the technique together, and {hero.id} smiled at {friend.id} because the friend made the rescue succeed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a congress?",
            answer="A congress is a big meeting where people gather to talk, plan, or show ideas.",
        ),
        QAItem(
            question="What is a technique?",
            answer="A technique is a special way of doing something, often with practice and skill.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even when things go wrong.",
        ),
        QAItem(
            question="Why do heroes often work together?",
            answer="Heroes often work together because teamwork can solve problems that are too hard for one person alone.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("city_hall", "girl", "Nova", "Pip", "boy", "loud_lift", "lever"),
    StoryParams("museum_hall", "boy", "Milo", "Rae", "girl", "shield_spin", "shield"),
    StoryParams("school_stage", "girl", "Zara", "Kai", "boy", "signal_snap", "whistle"),
]


ASP_RULES = r"""
place(city_hall). place(museum_hall). place(school_stage).
technique(loud_lift). technique(shield_spin). technique(signal_snap).
tool(lever). tool(shield). tool(whistle).

matches(loud_lift, lever).
matches(shield_spin, shield).
matches(signal_snap, whistle).

valid(P, T, U) :- place(P), technique(T), tool(U), matches(T, U).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TECHNIQUES:
        lines.append(asp.fact("technique", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(TECHNIQUES, params.technique),
        _safe_lookup(TOOLS, params.tool),
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, technique, tool) combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.hero_name}: {p.technique} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
