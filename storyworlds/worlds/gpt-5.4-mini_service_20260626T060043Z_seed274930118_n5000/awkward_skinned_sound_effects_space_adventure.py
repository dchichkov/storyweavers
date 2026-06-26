#!/usr/bin/env python3
"""
storyworlds/worlds/awkward_skinned_sound_effects_space_adventure.py
====================================================================

A tiny space-adventure storyworld about an awkward bump on a moonwalk, a
scuffed suit patch, and a careful fix that lets the crew continue.

Seed sketch:
---
A small ship drifts near a moon station. A young cadet named Nova is excited to
help with a spacewalk, but the airlock railing is awkward and a little snaggy.
When Nova slips, the glove gets skinned and the suit makes a loud zzzzt sound.
The captain notices, calms Nova down, and helps tape a soft patch over the spot
before the next step outside.

World model:
---
- The hero has two meters that matter here: suit_damage and scrapes.
- The ship has a few useful areas: airlock, corridor, and docking bay.
- Sound effects are not decoration; they are triggered by specific actions and
  state changes so they can be narrated as part of the cause-and-effect.
- The resolution is a practical repair: patching the suit, switching to a safer
  route, and continuing the mission with the hero feeling braver.
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
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

HERO_NAMES = ["Nova", "Pip", "Kite", "Milo", "Aria", "Juno", "Sol", "Rae"]
CAPTAIN_NAMES = ["Captain Vega", "Captain Orion", "Captain Lyra", "Captain Comet"]
SHIP_NAMES = ["the Bright Comet", "the Moon Finch", "the Star Hopper", "the Sky Lantern"]
TRAITS = ["curious", "eager", "brave", "awkward", "spry", "careful"]

# ---------------------------------------------------------------------------
# Entities and world model
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    patch: object | None = None
    ship: object | None = None
    suit: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("suit_damage", 0.0)
        self.meters.setdefault("scrapes", 0.0)
        self.meters.setdefault("worry", 0.0)
        self.meters.setdefault("calm", 0.0)
        self.meters.setdefault("confidence", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father"}
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
class ShipSetting:
    name: str
    areas: list[str]
    allowed_actions: set[str]
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
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    risk: str
    fix_hint: str
    area: str
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
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.current_action: Optional[Action] = None
        self.current_gear: Optional[Gear] = None

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_ouch(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["scrapes"] < THRESHOLD:
            continue
        sig = ("ouch", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        actor.memes["confidence"] -= 0.25
        out.append(f"Nova made a tiny wince, and the whole airlock felt quieter.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    action = world.current_action
    if action is None:
        return out
    for actor in world.characters():
        if actor.meters["scrapes"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id == "suit":
                sig = ("damage", item.id, actor.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["suit_damage"] += 1
                out.append(f"Zzzzt! Nova's suit patch got skinned in the scrape.")
    return out


CAUSAL_RULES = [Rule("ouch", _r_ouch), Rule("damage", _r_damage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def risk_action(action: Action) -> bool:
    return action.id in ACTIONS


def choose_gear(action: Action) -> Optional[Gear]:
    for gear in GEAR:
        if action.risk in gear.guards and action.area in gear.covers:
            return gear
    return None


def explain_rejection(action: Action) -> str:
    return (
        f"(No story: the action '{action.id}' does not have a plausible gear fix "
        f"in this tiny ship world.)"
    )


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(setting: ShipSetting, action: Action, hero_name: str, trait: str, captain_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", label=captain_name))
    ship = world.add(Entity(id="ship", type="ship", label=setting.name))
    suit = world.add(Entity(
        id="suit",
        type="suit",
        label="space suit",
        phrase="a bright space suit",
        owner=hero.id,
        worn_by=hero.id,
    ))
    patch = world.add(Entity(
        id="patch",
        type="patch",
        label="soft patch",
        phrase="a soft adhesive patch",
        owner=captain.id,
        protective=True,
        covers={"suit"},
    ))

    hero.memes["awkward"] = 1.0 if trait == "awkward" else 0.0
    hero.memes["confidence"] = 0.5
    captain.memes["calm"] = 1.0

    world.say(f"{hero.id} was a {trait} little cadet aboard {ship.label}.")
    world.say(f"{hero.id} loved every beep, blink, and hum of the ship.")
    world.say(f"On the deck, {action.gerund} felt exciting, because the station lights went ping-ping.")

    world.para()
    world.say(f"One day, {hero.id} and {captain.id} headed to the {action.area}.")
    world.say(f"{hero.id} wanted to {action.verb}, but the railing was wobbly and odd-shaped.")
    world.say(f"'{action.fix_hint},' {captain.id} said, keeping a steady hand on the wall.")
    world.say(f"{action.sound} went the hatch as it opened with a careful hiss.")

    hero.meters["scrapes"] += 1
    world.current_action = action
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.id} looked startled, then breathed out slowly.")
    world.say(f"'{action.risk.capitalize()} hurts,' {hero.id} said, holding up the skinned glove.")
    world.say(f"{captain.id} nodded and offered the soft patch.")
    world.current_gear = GEAR[0]
    suit.meters["suit_damage"] = max(suit.meters["suit_damage"], 1.0)
    world.say(f"{captain.id} said, '{world.current_gear.prep}.'")
    world.say(f"{action.sound.upper()}-zip! The patch sealed the spot with a tiny glow.")
    suit.meters["suit_damage"] = 0.0
    hero.meters["scrapes"] = 0.0
    hero.memes["confidence"] += 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"After that, {hero.id} {action.gerund} more carefully, "
        f"and {hero.id} even smiled at the funny squeak of the boots."
    )
    world.say(f"The little ship sailed on, with the skinned patch safely covered and the stars shining ahead.")

    world.facts.update(
        hero=hero,
        captain=captain,
        ship=ship,
        suit=suit,
        patch=patch,
        action=action,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "station": ShipSetting(
        name="a moon station",
        areas=["airlock", "corridor", "dock"],
        allowed_actions={"spacewalk", "crawl_panel", "carry_crate"},
    ),
    "ship": ShipSetting(
        name="the Bright Comet",
        areas=["airlock", "corridor", "bay"],
        allowed_actions={"spacewalk", "float_tools"},
    ),
}

ACTIONS = {
    "spacewalk": Action(
        id="spacewalk",
        verb="step outside for the spacewalk",
        gerund="stepping through the airlock",
        sound="whirr",
        risk="scrape",
        fix_hint="Hold the rail with both hands",
        area="airlock",
        tags={"space", "airlock", "repair"},
    ),
    "carry_crate": Action(
        id="carry_crate",
        verb="carry a crate to the dock",
        gerund="carrying crates down the corridor",
        sound="thunk",
        risk="bump",
        fix_hint="Walk slowly around the corner",
        area="dock",
        tags={"ship", "cargo"},
    ),
    "crawl_panel": Action(
        id="crawl_panel",
        verb="crawl under the control panel",
        gerund="crawling beside the blinking panel",
        sound="beep",
        risk="skinned",
        fix_hint="Keep your sleeves tucked in",
        area="corridor",
        tags={"panel", "repair"},
    ),
    "float_tools": Action(
        id="float_tools",
        verb="float the tools to the repair bay",
        gerund="floating tools in a tidy line",
        sound="ping",
        risk="tap",
        fix_hint="Use the tether loop",
        area="bay",
        tags={"tools", "repair"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="padded gloves",
        phrase="a pair of padded gloves",
        covers={"airlock", "corridor", "dock", "bay"},
        guards={"scrape", "bump", "skinned", "tap"},
        prep="Slip on the padded gloves first",
        tail="slid onward with safer hands",
        plural=True,
    ),
    Gear(
        id="patch",
        label="soft patch",
        phrase="a soft adhesive patch",
        covers={"suit"},
        guards={"scrape", "skinned"},
        prep="put on a soft patch first",
        tail="moved on with the patch holding tight",
    ),
]

CURATED = [
    {
        "place": "station",
        "action": "spacewalk",
        "name": "Nova",
        "trait": "awkward",
        "captain": "Captain Vega",
    },
    {
        "place": "ship",
        "action": "crawl_panel",
        "name": "Pip",
        "trait": "curious",
        "captain": "Captain Orion",
    },
    {
        "place": "station",
        "action": "carry_crate",
        "name": "Kite",
        "trait": "careful",
        "captain": "Captain Lyra",
    },
]


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    trait: str
    captain: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
    params: object | None = None
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    action: Action = _safe_fact(world, f, "action")
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    return [
        f'Write a short space-adventure story for a child about "{action.id}" and a skinned glove.',
        f"Tell a gentle story where {hero.id} feels awkward in the {f['setting'].name} and {captain.id} helps after a zzzzt sound.",
        f'Write a simple story that includes a sound effect like "{action.sound}" and ends with a safer way to keep going.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    action: Action = _safe_fact(world, f, "action")
    return [
        QAItem(
            question=f"Who was the story about on the {action.area}?",
            answer=f"It was about {hero.id}, a {f['trait']} little cadet, and {captain.id}, who kept things calm.",
        ),
        QAItem(
            question=f"What made {hero.id} feel awkward at first?",
            answer=f"The wobbly railing and the loud {action.sound} sound made the moment feel awkward and a little scary.",
        ),
        QAItem(
            question=f"What got skinned during the action?",
            answer=f"{hero.id}'s glove and suit patch got skinned a little during the scrape.",
        ),
        QAItem(
            question=f"How did the captain help {hero.id}?",
            answer=f"{captain.id} offered a soft patch, helped {hero.id} fix the suit, and showed a safer way to continue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling braver, the patch holding tight, and the ship continuing through the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spacewalk?",
            answer="A spacewalk is when astronauts leave the ship or station in special suits to work or explore in space.",
        ),
        QAItem(
            question="Why do spacesuits need patches sometimes?",
            answer="Spacesuits need patches if they get scraped or damaged, because the patch helps cover the spot and keep the suit safe.",
        ),
        QAItem(
            question="What does the sound effect 'whirr' suggest?",
            answer="Whirr usually suggests a machine spinning or moving smoothly, like a hatch or motor in a ship.",
        ),
        QAItem(
            question="Why do captains give careful instructions?",
            answer="Captains give careful instructions so the crew stays safe and can finish the mission without extra trouble.",
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An action is reasonable when there is a matching gear fix for the risk and area.
can_fix(A, G) :- action(A), gear(G), risk_of(A, R), guards(G, R), area_of(A, X), covers(G, X).
valid(A) :- action(A), can_fix(A, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in setting.allowed_actions:
            lines.append(asp.fact("allows", sid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk_of", aid, action.risk))
        lines.append(asp.fact("area_of", aid, action.area))
    for gid, gear in ((g.id, g) for g in GEAR):
        lines.append(asp.fact("gear", gid))
        for r in sorted(gear.guards):
            lines.append(asp.fact("guards", gid, r))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_actions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {k for k, v in ACTIONS.items() if choose_gear(v) is not None and risk_action(v)}
    cl = {a[0] for a in asp_valid_actions()}
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} actions).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "action", None) and getattr(args, "place", None):
        action = _safe_lookup(ACTIONS, getattr(args, "action", None))
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        if action.id not in setting.allowed_actions:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    places = [getattr(args, "place", None)] if getattr(args, "place", None) else list(SETTINGS)
    actions = [getattr(args, "action", None)] if getattr(args, "action", None) else list(ACTIONS)

    combos = []
    for place in places:
        setting = _safe_lookup(SETTINGS, place)
        for action_id in actions:
            action = _safe_lookup(ACTIONS, action_id)
            if action.id not in setting.allowed_actions:
                continue
            if choose_gear(action) is None:
                continue
            combos.append((place, action_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(place=place, action=action, name=name, trait=trait, captain=captain)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    action = _safe_lookup(ACTIONS, params.action)
    world = tell(setting, action, params.name, params.trait, params.captain)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with sound effects and a careful repair.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
    ap.add_argument("--captain")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for cur in CURATED:
            params = StoryParams(**cur)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
