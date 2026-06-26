#!/usr/bin/env python3
"""
Standalone storyworld: a small superhero-story domain built around a pamphlet,
an inner monologue, and a twist.

Premise:
- A child superhero or sidekick finds a pamphlet advertising a "good deed" route
  through the city.
- The hero wants to act fast, but the pamphlet is a little wrong.
- Inner monologue reveals the hero's doubt and reasoning.
- A twist changes what the pamphlet actually means.
- The ending proves the change in state with a concrete image.

This world models:
- typed entities with physical meters and emotional memes
- causal state updates driven by simulated events
- a reasonableness gate plus an inline ASP twin
"""

from __future__ import annotations

import argparse
import dataclasses
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear_ent: object | None = None
    guide: object | None = None
    hero: object | None = None
    pamphlet: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    indoors: bool = False
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
class Action:
    id: str
    name: str
    rush: str
    tension: str
    turn: str
    consequence: str
    mess: str
    risk_zone: set[str]
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    covers: set[str]
    helps_with: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_action: str = ""

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in g.meters.get("covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.active_action = self.active_action
        return clone


SETTINGS = {
    "alley": Setting(place="the bright alley", indoors=False, affordances={"fly", "sprint"}),
    "rooftop": Setting(place="the rooftop", indoors=False, affordances={"fly", "sprint"}),
    "museum": Setting(place="the museum hall", indoors=True, affordances={"sneak", "sprint"}),
    "bridge": Setting(place="the city bridge", indoors=False, affordances={"fly", "sprint", "sneak"}),
}

ACTIONS = {
    "fly": Action(
        id="fly",
        name="fly over the city",
        rush="dash into the sky",
        tension="the wind tugged at the cape",
        turn="the pamphlet was not an ad at all",
        consequence="the route pointed to a rescue, not a race",
        mess="scuffed",
        risk_zone={"torso"},
        keyword="fly",
        tags={"sky", "cape", "hero"},
    ),
    "sprint": Action(
        id="sprint",
        name="sprint across the city",
        rush="race down the street",
        tension="the boots scraped hard on the stones",
        turn="the pamphlet had folded notes inside",
        consequence="the notes marked where people needed help",
        mess="dusty",
        risk_zone={"feet", "legs"},
        keyword="run",
        tags={"city", "boots", "hero"},
    ),
    "sneak": Action(
        id="sneak",
        name="sneak through the hall",
        rush="slip past the tall pillars",
        tension="the mask felt too quiet for a loud day",
        turn="the pamphlet was a puzzle booklet",
        consequence="the puzzle hid a clue to the missing badge",
        mess="smudged",
        risk_zone={"hands"},
        keyword="secret",
        tags={"museum", "mask", "clue"},
    ),
}

PRIZES = {
    "cape": Prize(id="cape", label="cape", phrase="a red superhero cape", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="shiny blue boots", region="feet", plural=True),
    "mask": Prize(id="mask", label="mask", phrase="a silver mask", region="face"),
    "gloves": Prize(id="gloves", label="gloves", phrase="clean white gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="gloves_wrap", label="thin gloves", covers={"hands"}, helps_with={"smudged"}, prep="pull on thin gloves first", tail="slipped on the thin gloves"),
    Gear(id="cape_clip", label="a cape clip", covers={"torso"}, helps_with={"scuffed"}, prep="snap on a cape clip first", tail="clicked the cape clip in place"),
    Gear(id="boot_straps", label="boot straps", covers={"feet", "legs"}, helps_with={"dusty"}, prep="tighten the boot straps first", tail="fastened the boot straps"),
]

HERO_NAMES = ["Nova", "Mira", "Jett", "Kai", "Zara", "Theo"]
ROLES = ["hero", "sidekick", "rookie hero"]
TRAITS = ["brave", "curious", "careful", "bold", "quick-thinking"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    role: str
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


def action_risks_prize(action: Action, prize: Prize) -> bool:
    return prize.region in action.risk_zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if action.mess in g.helps_with and prize.region in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for a in setting.affordances:
            act = _safe_lookup(ACTIONS, a)
            for pid, prize in PRIZES.items():
                if action_risks_prize(act, prize) and select_gear(act, prize):
                    out.append((place, a, pid))
    return out


def inner_monologue(hero: Entity, action: Action, prize: Entity, twist: str) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} thought, "
        f'"If I rush now, my {prize.label} will get ruined. '
        f'But that pamphlet looks too neat to be simple."'
    )


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        act = ACTIONS.get(world.active_action)
        if not act:
            continue
        if actor.memes.get("risk", 0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id:
                continue
            if item.region not in act.risk_zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{item.label.capitalize()} picked up dust and trouble.")
    return out


def _r_reveal(world: World) -> list[str]:
    if world.facts.get("twist_revealed"):
        return []
    if world.facts.get("pamphlet_kind") == "hidden_help":
        world.facts["twist_revealed"] = True
        return ["__twist__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_soil, _r_reveal):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend([p for p in produced if p != "__twist__"])
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name, role=role))
    guide = world.add(Entity(id="Guide", kind="character", type="woman", label="the guide"))
    prize = world.add(Entity(
        id="prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=guide.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    pamphlet = world.add(Entity(id="pamphlet", type="thing", label="pamphlet", phrase="a folded city pamphlet"))
    pamphlet.worn_by = None

    world.facts["pamphlet_kind"] = "hidden_help"
    world.facts["action"] = action
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["prize"] = prize
    world.facts["setting"] = setting
    world.facts["pamphlet"] = pamphlet

    hero.memes["hope"] = 1
    hero.memes["risk"] = 1

    world.say(f"{hero_name} was a {trait} {role} who loved looking for trouble before trouble could find the city.")
    world.say(f"One afternoon, {hero_name} found a pamphlet tucked under a bench near {setting.place}.")
    world.say(f"It promised a quick way to {action.name}, and {hero_name} held {prize.it()} close while reading it.")

    world.para()
    world.say(f"{hero_name} wanted to go at once, but {action.tension}.")
    world.say(inner_monologue(hero, action, prize, action.turn))
    world.say(f'"Maybe the pamphlet knows something," {hero_name} whispered to {hero.pronoun("object")}self.')
    world.say(f"Still, the route looked strange, and {hero_name} kept reading instead of charging ahead.")

    world.para()
    world.say(f"Then came the twist: {action.turn}.")
    world.say(f"The last line explained {action.consequence}.")
    world.say(f"So the pamphlet was not a trick after all; it was a guide for helping people safely.")

    gear = select_gear(action, prize)
    if gear:
        gear_ent = world.add(Entity(
            id=gear.id, kind="thing", type="gear", label=gear.label, phrase=gear.label,
            owner=hero.id, caretaker=guide.id, plural=gear.plural
        ))
        gear_ent.meters["covers"] = gear.covers  # type: ignore[assignment]
        gear_ent.worn_by = hero.id
        world.say(f"{hero_name} and {guide.label} used the plan to {action.name} without hurting {prize.label}.")
        world.say(f"They {gear.tail}, and the city felt calmer under their feet.")
        hero.memes["relief"] = 1
        hero.memes["joy"] = 1
    propagate(world, narrate=True)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    return [
        'Write a superhero story for a young child that includes a pamphlet and a surprising twist.',
        f"Tell a short story about {hero.id}, a {hero.role}, who wants to {action.name} but worries about {prize.label}.",
        f"Write a child-friendly superhero story where a pamphlet changes what the hero thinks the mission is.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What did {hero.id} find near {setting.place}?",
            answer=f"{hero.id} found a pamphlet tucked under a bench near {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do after reading the pamphlet?",
            answer=f"{hero.id} wanted to {action.name}, but stayed to read more because the pamphlet looked important.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the pamphlet was not advertising a stunt at all; it was a guide that explained the real rescue route.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about {prize.label}?",
            answer=f"{hero.id} worried that {prize.label} might get ruined while rushing into the mission, so careful thinking mattered.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pamphlet?", answer="A pamphlet is a small folded paper with information or a message on it."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprising change that makes the story mean something new."),
        QAItem(question="What does a superhero do?", answer="A superhero helps people, protects a city, and uses courage to solve problems."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for r in sorted(a.risk_zone):
            lines.append(asp.fact("risks", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.helps_with):
            lines.append(asp.fact("helps_with", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- risks(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), helps_with(G,M), mess(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_story_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a pamphlet, inner monologue, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        role=getattr(args, "role", None) or rng.choice(ROLES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.role, params.trait)
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
    StoryParams(place="bridge", action="fly", prize="cape", name="Nova", role="hero", trait="brave"),
    StoryParams(place="rooftop", action="sprint", prize="boots", name="Jett", role="sidekick", trait="quick-thinking"),
    StoryParams(place="museum", action="sneak", prize="gloves", name="Mira", role="rookie hero", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos")
        for row in sorted(set(asp.atoms(model, "valid"))):
            print(row)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
