#!/usr/bin/env python3
"""
storyworlds/worlds/simple_luck_dim_cautionary_twist_bad_ending.py
==================================================================

A small space-adventure storyworld with a cautionary setup, a twist, and a bad ending.

Premise:
- A tiny crew is preparing a simple space job: cross a calm drift lane, deliver a tool,
  and come home.
- Luck is deliberately dim in this world. Small good chances exist, but they are scarce.
- The cautionary beat warns that a shortcut may save time, but the ship is not ready.

Twist:
- What looks like a harmless navigation trick turns out to be a baited beacon.
- The crew's confidence is not the problem; the ship's weak sensor is.

Bad ending:
- The ship makes the wrong choice, loses its supply pack, and limps into a cold dark dock.
- The ending proves the loss with changed world state, not a frozen summary.

This script is self-contained and follows the Storyworld contract:
- typed entities with meters and memes
- a simulated world model driving prose
- inline ASP rules plus a Python reasonableness gate
- generate/emit/main plus parser support for standard flags
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    cargo: object | None = None
    crew: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "pilot"}
        male = {"man", "boy", "father", "pilot"}
        if self.type in female and self.type not in {"pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type not in {"pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    vibe: str
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
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    twist: str
    consequence: str
    bad_end: str
    keyword: str
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
class Cargo:
    label: str
    phrase: str
    type: str
    fragile: bool = True
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
class Shield:
    id: str
    label: str
    protects: set[str]
    blocks: set[str]
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.twist_flag = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.twist_flag = self.twist_flag
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def cargo(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "cargo"]


@dataclass
class StoryParams:
    place: str
    mission: str
    cargo: str
    shield: str
    captain: str
    crewmate: str
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
    "drift_lane": Setting(place="the drift lane", vibe="quiet", affords={"scan", "dock", "shortcut"}),
    "relay_ring": Setting(place="the relay ring", vibe="busy", affords={"scan", "dock", "shortcut"}),
    "moon_port": Setting(place="the moon port", vibe="cold", affords={"dock", "scan"}),
}

MISSIONS = {
    "scan": Mission(
        id="scan",
        verb="scan the quiet lane",
        gerund="scanning the quiet lane",
        risk="the scanner could miss a hidden beacon",
        twist="a bright signal blinked like a friendly guide",
        consequence="the ship drifted closer to the wrong path",
        bad_end="the ship lost its map and had to dock in the dark",
        keyword="scan",
        tags={"space", "signal", "beacon"},
    ),
    "dock": Mission(
        id="dock",
        verb="dock at the tiny station",
        gerund="docking at the tiny station",
        risk="the dock light could wink out",
        twist="the station light was not a station light at all",
        consequence="the ship bumped the wrong side of the ring",
        bad_end="the cargo box fell and cracked open on the floor",
        keyword="dock",
        tags={"space", "dock", "light"},
    ),
    "shortcut": Mission(
        id="shortcut",
        verb="take the short path",
        gerund="taking the short path",
        risk="the short path could hide a trap",
        twist="the short path was a baited loop",
        consequence="the engine burned extra fuel to escape",
        bad_end="the ship came home late, empty, and shivering",
        keyword="shortcut",
        tags={"space", "path", "trap"},
    ),
}

CARGOES = {
    "seedbox": Cargo(label="seed box", phrase="a small seed box", type="seedbox"),
    "toolkit": Cargo(label="tool kit", phrase="a bright tool kit", type="toolkit"),
    "watercan": Cargo(label="water can", phrase="a heavy water can", type="watercan"),
}

SHIELDS = [
    Shield(
        id="sensor_shield",
        label="a sensor hood",
        protects={"scan"},
        blocks={"flare"},
        prep="put on a sensor hood first",
        tail="slipped on the sensor hood",
    ),
    Shield(
        id="dock_clamps",
        label="dock clamps",
        protects={"dock"},
        blocks={"impact"},
        prep="attach dock clamps before the approach",
        tail="locked on the dock clamps",
    ),
    Shield(
        id="fuel_wrap",
        label="fuel wrap",
        protects={"shortcut"},
        blocks={"burn"},
        prep="wrap the fuel line before they left",
        tail="wrapped the fuel line",
    ),
]

CAPTAIN_NAMES = ["Nova", "Mira", "Iris", "Sol", "Lina", "Orion", "Echo"]
CREW_NAMES = ["Pip", "Rae", "Tess", "Nell", "Bo", "Kai", "Zed"]
TRAITS = ["simple", "careful", "brave", "small", "steady"]


def mission_is_risky(mission: Mission, cargo: Cargo) -> bool:
    if mission.id == "scan":
        return cargo.label in {"seed box", "tool kit"}
    if mission.id == "dock":
        return cargo.fragile
    if mission.id == "shortcut":
        return True
    return False


def select_shield(mission: Mission, cargo: Cargo) -> Optional[Shield]:
    for shield in SHIELDS:
        if mission.id in shield.protects:
            return shield
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = _safe_lookup(MISSIONS, mid)
            for cid, cargo in CARGOES.items():
                if mission_is_risky(mission, cargo) and select_shield(mission, cargo):
                    combos.append((place, mid, cid))
    return combos


def _do_mission(world: World, crew: Entity, mission: Mission, narrate: bool = True) -> None:
    crew.memes["hope"] += 1
    if mission.id == "shortcut":
        crew.meters["fuel"] = crew.meters.get("fuel", 0) - 1
        crew.meters["risk"] = crew.meters.get("risk", 0) + 1
    if narrate:
        world.say(f"{crew.id} tried to {mission.verb}.")
        world.say(f"But {mission.risk}.")
    if mission.id == "scan":
        crew.meters["signal"] = crew.meters.get("signal", 0) + 1
    elif mission.id == "dock":
        crew.meters["impact"] = crew.meters.get("impact", 0) + 1
    elif mission.id == "shortcut":
        crew.meters["loop"] = crew.meters.get("loop", 0) + 1


def predict(world: World, crew: Entity, mission: Mission, cargo_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(crew.id), mission, narrate=False)
    cargo = sim.get(cargo_id)
    lost = mission.id == "shortcut"
    return {"lost": lost, "broken": cargo.meters.get("broken", 0) > 0}


def setup_line(world: World, captain: Entity, crew: Entity, cargo: Entity, mission: Mission) -> None:
    world.say(f"{captain.id} led a simple space job with {crew.id} beside {captain.pronoun('object')}.")
    world.say(f"They carried {cargo.phrase} for {mission.gerund}, and the lane looked calm.")
    captain.memes["duty"] += 1
    crew.memes["duty"] += 1
    cargo.meters["packed"] = 1


def caution(world: World, captain: Entity, crew: Entity, mission: Mission, cargo: Entity) -> bool:
    pred = predict(world, crew, mission, cargo.id)
    if not mission_is_risky(mission, cargo):
        return False
    world.facts["predicted_loss"] = pred["lost"]
    world.say(f'"Wait," {captain.pronoun("subject")} said. "This feels too lucky for a {mission.keyword}."')
    world.say(f"{captain.id} warned that {mission.twist.lower() if mission.id else 'something was off'}.")
    return True


def twist(world: World, captain: Entity, crew: Entity, mission: Mission) -> None:
    crew.memes["curiosity"] += 1
    world.twist_flag = True
    world.say(f"Then the little beacon blinked again, but it was not a guide.")
    world.say(f"It was {mission.twist}, and the glow pulled the ship off course.")


def bad_ending(world: World, captain: Entity, crew: Entity, cargo: Entity, mission: Mission) -> None:
    captain.memes["regret"] += 1
    crew.memes["fear"] += 1
    cargo.meters["broken"] = cargo.meters.get("broken", 0) + 1
    captain.meters["lost"] = captain.meters.get("lost", 0) + 1
    world.say(f"{mission.consequence.capitalize()}, and {cargo.label} slipped loose.")
    world.say(f"In the end, {mission.bad_end}. {captain.id} could only stare at the cold dock lights.")


def tell(setting: Setting, mission: Mission, cargo_cfg: Cargo,
         captain_name: str = "Nova", crew_name: str = "Pip") -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type="pilot"))
    crew = world.add(Entity(id=crew_name, kind="character", type="pilot"))
    cargo = world.add(Entity(
        id="cargo",
        kind="cargo",
        type=cargo_cfg.type,
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        owner=captain.id,
    ))

    setup_line(world, captain, crew, cargo, mission)
    world.para()
    caution(world, captain, crew, mission, cargo)
    world.say(f"{crew.id} still thought the next shine looked safe.")
    world.say(f"{crew.id} reached for the short path anyway.")
    twist(world, captain, crew, mission)
    world.para()
    _do_mission(world, crew, mission)
    cargo.meters["broken"] = cargo.meters.get("broken", 0) + 1
    bad_ending(world, captain, crew, cargo, mission)

    world.facts.update(
        captain=captain,
        crew=crew,
        cargo=cargo,
        mission=mission,
        setting=setting,
        twist=world.twist_flag,
        failed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission: Mission = _safe_fact(world, f, "mission")
    cargo: Cargo = _safe_fact(world, f, "cargo")
    return [
        f'Write a short, simple space-adventure story with a cautionary warning, a twist, and a bad ending that uses the word "{mission.keyword}".',
        f"Tell a child-friendly story where a tiny crew is tempted by a {mission.keyword} but loses {cargo.label} because the sign was false.",
        f"Write a brief space story about a risky shortcut, a surprise beacon, and a sad ending with damaged cargo.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    crew: Entity = _safe_fact(world, f, "crew")
    cargo: Entity = _safe_fact(world, f, "cargo")
    mission: Mission = _safe_fact(world, f, "mission")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who tried to keep the space job safe in {setting.place}?",
            answer=f"{captain.id} tried to keep the job safe because {captain.pronoun('subject')} noticed the risk first.",
        ),
        QAItem(
            question=f"What did the crew want to do before the warning turned serious?",
            answer=f"They wanted to {mission.verb}, even though the lane looked too lucky.",
        ),
        QAItem(
            question=f"What cargo were they trying to protect during the trip?",
            answer=f"They were carrying {cargo.phrase}, and it was the thing the crew most wanted to bring home.",
        ),
        QAItem(
            question="Why was the warning important?",
            answer=f"The warning mattered because the shortcut could hide trouble, and the ship's weak choice would cost them the cargo.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The beacon was a trap, the cargo broke loose, and the crew ended at a cold dock with a bad result.",
        ),
    ]


KNOWLEDGE = {
    "space": [("What is outer space?", "Outer space is the wide, dark place beyond Earth where stars, planets, and ships can travel.")],
    "signal": [("What is a signal?", "A signal is a sign or message that tells someone something is happening or where to go.")],
    "beacon": [("What is a beacon?", "A beacon is a light or signal used to help guide travelers, especially in the dark.")],
    "dock": [("What is a dock?", "A dock is a place where ships stop so people can get on, off, or load things.")],
    "light": [("Why are lights useful in space?", "Lights help people see ships, doors, and paths when everything around them is dark.")],
    "path": [("What is a shortcut?", "A shortcut is a shorter way to go somewhere, but it is not always the safest way.")],
    "trap": [("What is a trap?", "A trap is something that seems okay at first but is meant to cause trouble.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags)
    out = []
    for tag, qas in KNOWLEDGE.items():
        if tag in tags:
            for q, a in qas:
                out.append(QAItem(question=q, answer=a))
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="drift_lane", mission="shortcut", cargo="seedbox", shield="fuel_wrap", captain="Nova", crewmate="Pip"),
    StoryParams(place="relay_ring", mission="scan", cargo="toolkit", shield="sensor_shield", captain="Mira", crewmate="Rae"),
    StoryParams(place="moon_port", mission="dock", cargo="watercan", shield="dock_clamps", captain="Sol", crewmate="Tess"),
]

GENDERED_NAMES = ["Nova", "Mira", "Iris", "Sol", "Lina", "Orion", "Echo", "Pip", "Rae", "Tess"]


def explain_rejection(mission: Mission, cargo: Cargo) -> str:
    return (
        f"(No story: {mission.gerund} with {cargo.label} does not lead to a believable cautionary twist and bad ending here.)"
    )


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
risky(M,C) :- mission(M), cargo(C), needs_caution(M,C).
compatible(M,C) :- risky(M,C), shield_for(M,S), covers(S,M).
story(Place,M,C) :- affords(Place,M), compatible(M,C).
#show story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("needs_caution", mid, "cargo"))
    for cid, c in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
    for sh in SHIELDS:
        lines.append(asp.fact("shield_for", list(sh.protects)[0], sh.id))
        for m in sorted(sh.protects):
            lines.append(asp.fact("covers", sh.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A simple luck-dim space-adventure storyworld with a cautionary twist and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--captain")
    ap.add_argument("--crewmate")
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
    combos = [c for c in valid_story_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "cargo", None) is None or c[2] == getattr(args, "cargo", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, cargo = rng.choice(list(combos))
    captain = getattr(args, "captain", None) or rng.choice(GENDERED_NAMES)
    crewmate = getattr(args, "crewmate", None) or rng.choice([n for n in GENDERED_NAMES if n != captain])
    shield = next(s.id for s in SHIELDS if mission in s.protects)
    return StoryParams(place=place, mission=mission, cargo=cargo, shield=shield, captain=captain, crewmate=crewmate)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(CARGOES, params.cargo), params.captain, params.crewmate)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story/3."))
        print(f"{len(set(asp.atoms(model, 'story')))} compatible stories")
        for tpl in sorted(set(asp.atoms(model, "story"))):
            print(" ", tpl)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
