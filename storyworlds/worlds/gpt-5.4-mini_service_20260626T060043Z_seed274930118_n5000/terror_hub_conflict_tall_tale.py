#!/usr/bin/env python3
"""
storyworlds/worlds/terror_hub_conflict_tall_tale.py
====================================================

A small, child-facing tall-tale story world about a busy hub, a big scare,
and a conflict that gets turned into a safer, brighter ending.

The seed image for this world is a noisy hub where people pass through, hear
a frightening story, and argue about what to do next. The tale stays grounded
by modeling the hub, the fear, the rumor, and the calm-down as state changes
rather than as a frozen paragraph.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify compares ASP and Python parity and exercises generated stories
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    teller: object | None = None
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
class Hub:
    place: str
    bustle: str
    afford_conflict: bool = True
    afford_terror: bool = True
    world: object | None = None
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
class Trigger:
    id: str
    label: str
    verb: str
    noun: str
    fear: str
    rumor: str
    cause: str
    effect: str
    location: str
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
class Remedy:
    id: str
    label: str
    action: str
    result: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.phase: str = "setup"

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

        clone = World(self.hub)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.phase = self.phase
        return clone


@dataclass
class Rule:
    name: str
    apply: object
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


def _r_spread_fear(world: World) -> list[str]:
    out = []
    rumor = world.facts.get("rumor")
    if not rumor:
        return out
    teller = world.get(world.facts["teller"])
    audience = world.get(world.facts["hero"])
    sig = ("fear", teller.id, audience.id)
    if sig in world.fired:
        return out
    if audience.memes.get("fear", 0.0) >= THRESHOLD:
        return out
    world.fired.add(sig)
    audience.memes["fear"] = audience.memes.get("fear", 0.0) + 1
    audience.memes["conflict"] = audience.memes.get("conflict", 0.0) + 1
    out.append(f"{audience.label or audience.id} felt a cold shiver from the rumor.")
    return out


def _r_noise_stirs_conflict(world: World) -> list[str]:
    out = []
    if world.facts.get("noise", 0.0) < THRESHOLD:
        return out
    hero = world.get(world.facts["hero"])
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    out.append("The hub grew louder, and that made the argument sharper.")
    return out


def _r_lantern_calm(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"])
    if hero.memes.get("calm", 0.0) < THRESHOLD:
        return out
    sig = ("settle", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    hero.memes["conflict"] = 0.0
    out.append("The lantern light made the shadows smaller and the fear easier to carry.")
    return out


CAUSAL_RULES = [
    Rule("spread_fear", _r_spread_fear),
    Rule("noise_stirs_conflict", _r_noise_stirs_conflict),
    Rule("lantern_calm", _r_lantern_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_conflict(world: World, hero: Entity, trigger: Trigger) -> dict:
    sim = world.copy()
    sim.facts["rumor"] = trigger.id
    sim.facts["hero"] = hero.id
    sim.facts["teller"] = world.facts["teller"]
    propagate(sim, narrate=False)
    return {
        "fear": sim.get(hero.id).memes.get("fear", 0.0),
        "conflict": sim.get(hero.id).memes.get("conflict", 0.0),
    }


def opening_line(hero: Entity, place: str) -> str:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    return f"Once upon a time, there was a little {trait} {hero.type} named {hero.id} who knew the way to {place} by heart."


def hub_detail(hub: Hub, trigger: Trigger) -> str:
    return f"The {hub.place} bustled like a tin kettle, with wheels, boots, and voices all clattering at once."


def tell_tale(world: World, hero: Entity, teller: Entity, trigger: Trigger, remedy: Remedy) -> None:
    world.say(opening_line(hero, world.hub.place))
    world.say(f"{hero.pronoun().capitalize()} loved the {world.hub.bustle}, and {hero.pronoun('possessive')} eyes were always open for surprises.")
    world.say(f"At the {world.hub.place}, {teller.id} told a tall tale about {trigger.rumor}.")
    world.facts.update(hero=hero.id, teller=teller.id, trigger=trigger.id, remedy=remedy.id, rumor=trigger.id)

    world.para()
    world.say(hub_detail(world.hub, trigger))
    world.say(f"{hero.id} heard that {trigger.noun} would {trigger.verb} and make {trigger.effect}.")
    world.say(f"{hero.id} wanted to stay calm, but {hero.pronoun('possessive')} chest felt as tight as a knotted rope.")
    world.facts["rumor"] = trigger.id
    propagate(world, narrate=True)

    world.para()
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} argued back that the tale was too spooky for the busy hub.")
        world.say(f"{teller.id} frowned, and for a moment the whole place felt as crackly as dry leaves.")
    world.facts["noise"] = 1.0
    propagate(world, narrate=True)

    world.para()
    if remedy.id == "lanterns":
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
        world.say(f"Then someone held up the lanterns and said, '{remedy.action.capitalize()}.'")
        world.say(f"That {remedy.result}, and the shadows under the wagons stopped looking so long.")
        propagate(world, narrate=True)
        world.say(
            f"{hero.id} smiled again, and the hub sounded bright instead of frightful. "
            f"In the end, the big fear turned out to be only a tall tale, and {hero.id} carried the light home."
        )
    else:
        pass


def build_story(hero_name: str, hero_type: str, teller_name: str, trigger_id: str) -> World:
    world = World(Hub(place="hub", bustle="wagon-loud"))
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious", "stubborn"]))
    teller = world.add(Entity(id=teller_name, kind="character", type="man", traits=["tall", "boastful"]))
    trigger = _safe_lookup(TRIGGERS, trigger_id)
    remedy = REMEDIES["lanterns"]
    world.facts["hero_obj"] = hero
    world.facts["teller_obj"] = teller
    tell_tale(world, hero, teller, trigger, remedy)
    world.facts.update(trigger=trigger, remedy=remedy)
    return world


TRIGGERS = {
    "black-horse": Trigger(
        id="black-horse",
        label="black horse",
        verb="stamp the boards",
        noun="a black horse",
        fear="a thundering fright",
        rumor="a black horse the size of a barn",
        cause="the rumor spread",
        effect="the rafters tremble",
        location="the hub",
        tags={"terror", "conflict"},
    ),
    "iron-wind": Trigger(
        id="iron-wind",
        label="iron wind",
        verb="whistle through the cracks",
        noun="iron wind",
        fear="a shivery howl",
        rumor="a wind made of iron",
        cause="the tale grows",
        effect="everybody jumps",
        location="the hub",
        tags={"terror"},
    ),
    "night-bell": Trigger(
        id="night-bell",
        label="night bell",
        verb="ring out like thunder",
        noun="a night bell",
        fear="a sudden boom",
        rumor="a bell that wakes the whole valley",
        cause="the story runs ahead",
        effect="people clutch their hats",
        location="the hub",
        tags={"conflict", "terror"},
    ),
}

REMEDIES = {
    "lanterns": Remedy(
        id="lanterns",
        label="lanterns",
        action="lift the lanterns high",
        result="the dark corners looked friendly again",
        helps={"terror", "conflict"},
    )
}

HUBS = {
    "hub": Hub(place="the crossroads hub", bustle="wagon-loud"),
}

NAMES = ["Nell", "Milo", "Tess", "Benny", "Jo", "Wren", "Pip", "Clara"]
TELLERS = ["Old Jed", "Aunt Bess", "Sailor Sam", "Uncle Amos"]
TRAITS = ["curious", "brave", "lively", "stubborn", "bright"]


@dataclass
class StoryParams:
    hub: str
    trigger: str
    name: str
    gender: str
    teller: str
    trait: str
    seed: Optional[int] = None
    sample: object | None = None
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for hub in HUBS:
        for trigger in TRIGGERS:
            combos.append((hub, trigger))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: terror at the hub, then a calmer turn.")
    ap.add_argument("--hub", choices=HUBS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teller", choices=TELLERS)
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
    if getattr(args, "hub", None):
        combos = [c for c in combos if c[0] == getattr(args, "hub", None)]
    if getattr(args, "trigger", None):
        combos = [c for c in combos if c[1] == getattr(args, "trigger", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hub, trigger = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    teller = getattr(args, "teller", None) or rng.choice(TELLERS)
    trait = rng.choice(TRAITS)
    return StoryParams(hub=hub, trigger=trigger, name=name, gender=gender, teller=teller, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero_obj")
    trigger = _safe_fact(world, f, "trigger")
    return [
        f'Write a short tall tale for a small child about a terror at the hub, using the word "terror".',
        f"Tell a story where {hero.id} hears a scary rumor about {trigger.rumor} at the hub and the conflict ends with lantern light.",
        f"Write a kid-friendly tall tale about a busy hub, a big fright, and a calmer ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero_obj")
    teller = _safe_fact(world, world.facts, "teller_obj")
    trigger = _safe_fact(world, world.facts, "trigger")
    qa = [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a little {hero.traits[1]} {hero.type} who comes through the hub.",
        ),
        QAItem(
            question=f"What did {teller.id} tell at the hub?",
            answer=f"{teller.id} told a tall tale about {trigger.rumor}, which sounded frightening to {hero.id}.",
        ),
        QAItem(
            question=f"Why did the argument start?",
            answer=f"The argument started because the scary rumor made {hero.id} feel fear, and the busy hub noise made the conflict sharper.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with lantern light, a calmer hub, and {hero.id} smiling again after the fear turned out to be only a tall tale.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hub?",
            answer="A hub is a busy place where people and wagons meet, turn, or pass through on their way to somewhere else.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story that is told in a huge, exaggerated way, often so big it sounds funny or hard to believe.",
        ),
        QAItem(
            question="What does terror mean?",
            answer="Terror means a very strong fear that can make someone feel shaky or wide-eyed.",
        ),
    ]


def asp_facts() -> str:
    import asp

    lines = []
    for hid in HUBS:
        lines.append(asp.fact("hub", hid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("fear", tid, t.fear))
        lines.append(asp.fact("rumor", tid, t.rumor))
        lines.append(asp.fact("effect", tid, t.effect))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for h in sorted(r.helps):
            lines.append(asp.fact("helps", rid, h))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T) :- trigger(T), tag(T, terror).
conflict(T) :- trigger(T), tag(T, conflict).
fix(T, R) :- at_risk(T), remedy(R), helps(R, terror).
fix(T, R) :- conflict(T), remedy(R), helps(R, conflict).
valid_story(H, T) :- hub(H), trigger(T), at_risk(T), conflict(T), fix(T, _).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = {(h, t) for (h, t) in valid_combos()}
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        sample = generate(StoryParams(hub="hub", trigger="black-horse", name="Nell", gender="girl", teller="Old Jed", trait="curious"))
        if not sample.story.strip():
            print("Parity OK, but sample story was empty.")
            return 1
        print(f"OK: ASP matches Python ({len(py)} combos), and story generation works.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def explain_rejection(trigger: Trigger) -> str:
    return f"(No story: the trigger {trigger.id} does not produce both terror and conflict in a way this hub can resolve.)"


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(HUBS, params.hub))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "stubborn"]))
    teller = world.add(Entity(id=params.teller, kind="character", type="man", traits=["tall", "boastful"]))
    trigger = _safe_lookup(TRIGGERS, params.trigger)
    remedy = REMEDIES["lanterns"]
    world.facts.update(hero_obj=hero, teller_obj=teller, trigger=trigger, remedy=remedy)
    tell_tale(world, hero, teller, trigger, remedy)
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
        for section, items in [("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)]:
            print(f"== {section} ==")
            if isinstance(items, list) and items and isinstance(items[0], str):
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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
        for h, t in stories:
            print(f"  {h:10} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(hub="hub", trigger="black-horse", name="Nell", gender="girl", teller="Old Jed", trait="curious"),
            StoryParams(hub="hub", trigger="iron-wind", name="Milo", gender="boy", teller="Aunt Bess", trait="brave"),
            StoryParams(hub="hub", trigger="night-bell", name="Tess", gender="girl", teller="Uncle Amos", trait="lively"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
