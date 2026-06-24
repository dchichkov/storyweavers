#!/usr/bin/env python3
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
    station: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "captain", "pilot"}
        female = {"girl", "woman", "mother", "captainess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def was(self) -> str:
        return "were" if self.type == "crew" else "was"
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
class Station:
    name: str
    kind: str
    hazard: str
    view: str
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    consequence: str
    zone: set[str]
    keyword: str
    flashback: str
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
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    gives: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    station: str
    mission: str
    artifact: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy
        c = World(self.station)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        return c


STATIONS = {
    "orbit_lab": Station("the orbit lab", "lab", "glow", "a bright window", {"scan", "repair", "float"}),
    "moon_hangar": Station("the moon hangar", "hangar", "dust", "silver doors", {"drive", "repair", "float"}),
    "asteroid_garden": Station("the asteroid garden", "garden", "dust", "tiny rock paths", {"plant", "repair", "float"}),
    "deep_ship": Station("the deep ship", "ship", "chill", "a long tunnel", {"scan", "drive", "float"}),
}

MISSIONS = {
    "starlight": Mission(
        "starlight",
        verb="chase the bright satellite",
        gerund="chasing bright satellites",
        rush="dash toward the airlock",
        hazard="glow",
        consequence="sparkly and blinded",
        zone={"face", "hands"},
        keyword="starlight",
        flashback="when the child had once watched a tiny light blink out behind a cloud",
        tags={"space", "light"},
    ),
    "moon_dust": Mission(
        "moon_dust",
        verb="collect moon dust",
        gerund="collecting moon dust",
        rush="run to the storage hatch",
        hazard="dust",
        consequence="gray and gritty",
        zone={"hands", "boots"},
        keyword="moon dust",
        flashback="when the child had once seen dust float like snow in a beam of light",
        tags={"space", "dust"},
    ),
    "comet": Mission(
        "comet",
        verb="follow the comet trail",
        gerund="following comet trails",
        rush="sprint to the scanner",
        hazard="chill",
        consequence="cold and shivery",
        zone={"face", "torso"},
        keyword="comet",
        flashback="when the child had once looked up at a streaking light and made a wish",
        tags={"space", "comet"},
    ),
    "repair_beep": Mission(
        "repair_beep",
        verb="fix the beeping rover",
        gerund="repairing the rover",
        rush="hurry to the tool shelf",
        hazard="glow",
        consequence="stuck in a flashing glare",
        zone={"hands", "torso"},
        keyword="beeping rover",
        flashback="when the child had once heard a broken beep in the dark and wanted to help",
        tags={"space", "repair"},
    ),
}

ARTIFACTS = {
    "helmet": Artifact("helmet", "helmet", "a shiny helmet with a clear visor", "face"),
    "gloves": Artifact("gloves", "gloves", "small blue gloves", "hands", plural=True),
    "jacket": Artifact("jacket", "jacket", "a soft space jacket", "torso"),
    "boots": Artifact("boots", "boots", "sturdy moon boots", "boots", plural=True),
}

GEAR = [
    Gear("visor", "a visor cover", {"face"}, {"glow"}, "clip on a visor cover first", "slid on the visor cover"),
    Gear("mitts", "thick mitts", {"hands"}, {"dust", "glow"}, "put on thick mitts first", "pulled on the thick mitts"),
    Gear("shell", "a thermal shell", {"torso"}, {"chill"}, "zip on a thermal shell first", "zipped on the thermal shell"),
    Gear("allgear", "full flight gear", {"face", "hands", "torso", "boots"}, {"glow", "dust", "chill"}, "get into full flight gear", "suited up in full flight gear"),
]

GIRL_NAMES = ["Mira", "Nova", "Luna", "Aria", "Zara", "Tess"]
BOY_NAMES = ["Kai", "Oren", "Ivo", "Max", "Leo", "Nico"]
TRAITS = ["brave", "curious", "lively", "steady", "clever", "bold"]


def prize_at_risk(mission: Mission, artifact: Artifact) -> bool:
    return artifact.region in mission.zone


def select_gear(mission: Mission, artifact: Artifact) -> Optional[Gear]:
    for g in GEAR:
        if mission.hazard in g.guards and artifact.region in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, st in STATIONS.items():
        for mid in st.affords:
            m = _safe_lookup(MISSIONS, mid)
            for aid, a in ARTIFACTS.items():
                if prize_at_risk(m, a) and select_gear(m, a):
                    out.append((sid, mid, aid))
    return out


def explain_rejection(m: Mission, a: Artifact) -> str:
    return f"(No story: {m.gerund} would not actually threaten {a.label} in a believable way.)"


def explain_gender(aid: str, gender: str) -> str:
    return f"(No story: a {_safe_lookup(ARTIFACTS, aid).label} is not a typical {gender}'s item in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a flashback and a twist.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "captain", "robot"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mission", None) and getattr(args, "artifact", None):
        m, a = _safe_lookup(MISSIONS, getattr(args, "mission", None)), _safe_lookup(ARTIFACTS, getattr(args, "artifact", None))
        if not (prize_at_risk(m, a) and select_gear(m, a)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "artifact", None):
        if getattr(args, "gender", None) == "girl" and getattr(args, "artifact", None) == "boots":
            pass
    combos = [c for c in valid_combos()
              if (getattr(args, "station", None) is None or c[0] == getattr(args, "station", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "artifact", None) is None or c[2] == getattr(args, "artifact", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    sid, mid, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "captain", "robot"])
    trait = rng.choice(TRAITS)
    return StoryParams(sid, mid, aid, name, gender, helper, trait)


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    actor.meters[mission.hazard] = actor.meters.get(mission.hazard, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    if narrate:
        world.say(f"{actor.id} did the mission, and the ship felt alive.")


def predict(world: World, actor: Entity, mission: Mission, artifact: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    item = sim.entities[artifact]
    return {"soiled": item.meters.get(mission.hazard, 0) > 0}


def tell(station: Station, mission: Mission, artifact: Artifact, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(station)
    hero = world.add(Entity(name, kind="character", type=gender, meters={}, memes={}))
    guide = world.add(Entity("Guide", kind="character", type=helper, label=f"the {helper}", meters={}, memes={}))
    item = world.add(Entity("Prize", type=artifact.id, label=artifact.label, phrase=artifact.phrase, owner=hero.id, caretaker=guide.id, station=artifact.region))
    gear: Optional[Gear] = None

    world.say(f"{hero.id} was a {trait} {gender} who loved space adventures.")
    world.say(f"{hero.pronoun().capitalize()} had {item.phrase}, and it shone like it belonged in a storybook ship.")
    world.say(f"One day at {station.name}, {hero.id} wanted to {mission.verb}.")
    world.say(f"{hero.id} remembered {mission.flashback}, and that memory made {hero.pronoun('object')} {mission.gerund} even more.")
    world.say(f"But {guide.label} worried the mission could leave {item.label} {mission.consequence}.")
    if predict(world, hero, mission, item.id)["soiled"]:
        world.say(f"{hero.id} rushed toward the start of the mission, but {guide.label} held up a calm hand.")
        world.say(f'"If you go now, {item.label} may get {mission.consequence}," said {guide.label}.')
        world.say(f"{hero.id} frowned, then looked back at the gleaming room.")
        gear = select_gear(mission, item)
        if gear is None:
            gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
        world.say(f"{guide.label.capitalize()} smiled and said, \"How about we {gear.prep} and try together?\"")
        world.say(f"{hero.id} grinned. {hero.pronoun().capitalize()} agreed at once.")
        world.say(f"They {gear.tail}, and then {hero.id} went to {mission.gerund}.")
        _do_mission(world, hero, mission, narrate=False)
        world.say(f"The twist was that the rover beeped only because it had been asking for help, so the mission was kinder than anyone feared.")
        world.say(f"At the end, {hero.id} felt exalted, like a tiny hero among the stars, and {item.label} stayed clean.")
    else:
        _do_mission(world, hero, mission, narrate=False)
        world.say(f"Nothing got in the way, and {hero.id} finished the mission with a proud smile.")
        world.say(f"The stars looked close enough to touch.")
    world.facts = {"hero": hero, "guide": guide, "item": item, "mission": mission, "station": station, "gear": gear}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h, g, m, i = f["hero"], f["guide"], f["mission"], f["item"]
    return [
        f'Write a short space adventure for a young child that includes the word "{m.keyword}" and the idea of feeling exalted.',
        f"Tell a gentle story where {h.id} wants to {m.verb} at {world.station.name} but {g.label} worries about {i.label}.",
        f"Write a story with a flashback and a twist about a child, a ship, and {m.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, g, m, i, st = f["hero"], f["guide"], f["mission"], f["item"], f["station"]
    return [
        QAItem(question=f"What did {h.id} want to do at {st.name}?", answer=f"{h.id} wanted to {m.verb}."),
        QAItem(question=f"Why did {g.label} worry?", answer=f"{g.label.capitalize()} worried that {i.label} could get {m.consequence}."),
        QAItem(question=f"What was the flashback about?", answer=f"It was about {m.flashback}."),
        QAItem(question=f"What was the twist?", answer="The twist was that the problem was really a request for help, so the mission turned kind and useful."),
        QAItem(question=f"How did the story end?", answer=f"It ended with {h.id} feeling exalted and {i.label} staying clean."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a visor for?", answer="A visor helps protect your face from bright light while you look out into space."),
        QAItem(question="What is a rover?", answer="A rover is a small machine that drives over a planet or moon to help explore."),
        QAItem(question="Why do astronauts wear gear?", answer="Astronaut gear helps them stay safe from cold, dust, and bright glare."),
        QAItem(question="What does exalted mean?", answer="Exalted means very proud, lifted up, and full of joyful importance."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbit_lab", "starlight", "helmet", "Mira", "girl", "robot", "brave"),
    StoryParams("moon_hangar", "moon_dust", "gloves", "Kai", "boy", "father", "curious"),
    StoryParams("deep_ship", "comet", "jacket", "Luna", "girl", "mother", "steady"),
    StoryParams("asteroid_garden", "repair_beep", "boots", "Nico", "boy", "captain", "bold"),
]


ASP_RULES = r"""
station(S) :- setting(S).
mission(M) :- activity(M).
artifact(A) :- prize(A).
at_risk(M,A) :- splashes(M,R), worn_on(A,R).
gear_ok(G,M,A) :- gear(G), at_risk(M,A), guards(G,H), hazard_of(M,H), covers(G,R), worn_on(A,R).
valid(S,M,A) :- affords(S,M), at_risk(M,A), gear_ok(_,M,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in STATIONS.items():
        lines.append(asp.fact("setting", sid))
        for m in s.affords:
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("activity", mid))
        lines.append(asp.fact("hazard_of", mid, m.hazard))
        for r in m.zone:
            lines.append(asp.fact("splashes", mid, r))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("prize", aid))
        lines.append(asp.fact("worn_on", aid, a.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in g.guards:
            lines.append(asp.fact("guards", g.id, h))
        for r in g.covers:
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(STATIONS, params.station), _safe_lookup(MISSIONS, params.mission), _safe_lookup(ARTIFACTS, params.artifact), params.name, params.gender, params.helper, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos")
        for row in vals:
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
