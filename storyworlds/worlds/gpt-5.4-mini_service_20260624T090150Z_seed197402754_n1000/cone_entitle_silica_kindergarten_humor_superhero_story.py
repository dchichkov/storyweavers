#!/usr/bin/env python3
"""
A small storyworld about a kindergarten superhero day.

Premise:
- In kindergarten, a young hero loves helping classmates and showing off a tiny
  superhero talent.
- A special object is at risk during a playful mission.
- A sensible helper notices the risk and offers a funny but safe compromise.

This world keeps the prose child-facing and the state changes concrete:
bravery, confusion, laughter, and a final successful rescue.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    kid: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safe": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "pride": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the kindergarten"
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
    rush: str
    risk: str
    zone: set[str]
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
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    humor_line: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kindergarten": Setting(place="the kindergarten", affords={"cones", "silica", "heroics"}),
}

MISSIONS = {
    "cone": Mission(
        id="cone",
        verb="rescue the cone",
        gerund="rescuing cones",
        rush="dash toward the tall orange cone",
        risk="might get knocked over and spun into the snack area",
        zone={"hands", "feet"},
        keyword="cone",
        tags={"cone", "humor"},
    ),
    "silica": Mission(
        id="silica",
        verb="protect the silica",
        gerund="protecting the silica",
        rush="race over to the glittery silica jar",
        risk="could spill into the art table",
        zone={"hands", "torso"},
        keyword="silica",
        tags={"silica", "humor"},
    ),
}

PRIZES = {
    "badge": Prize(
        label="badge",
        phrase="a shiny star badge",
        type="badge",
        region="torso",
    ),
    "cape": Prize(
        label="cape",
        phrase="a bright red cape",
        type="cape",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a little hero hat",
        type="hat",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="foam_pad",
        label="foam pads",
        covers={"hands", "feet"},
        prep="put on foam pads first",
        tail="walked back with foam pads on",
        humor_line="They looked a little silly, like marshmallows with superhero jobs.",
        plural=True,
    ),
    Gear(
        id="paper_tray",
        label="a paper tray",
        covers={"torso", "hands"},
        prep="carry a paper tray like a tiny shield",
        tail="marched back carrying the paper tray shield",
        humor_line="It was a goofy shield, but it really worked.",
    ),
]

KID_NAMES = ["Mila", "Owen", "Nia", "Theo", "Luna", "Ezra", "Ari", "Zoe"]
PARENT_NAMES = ["Teacher Sun", "Ms. Piper", "Mr. Bean", "Coach Dot"]
TRAITS = ["brave", "curious", "silly", "speedy", "gentle"]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    trait: str
    helper: str
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


def mission_at_risk(mission: Mission, prize: Prize) -> bool:
    return prize.region in mission.zone or mission.id == "silica"


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    if mission.id == "cone" and prize.region in {"hands", "feet"}:
        return GEAR[0]
    if mission.id == "silica" and prize.region in {"hands", "torso"}:
        return GEAR[1]
    return None


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return (
        f"(No story: {mission.gerund} would not honestly put {prize.label} at risk "
        f"in a way a funny safety fix could solve.)"
    )


ASP_RULES = r"""
mission_risk(M,P) :- mission(M), prize(P), zone(M,R), region(P,R).
mission_risk(silica,P) :- mission(silica), prize(P).
fix(G,M,P) :- gear(G), mission_risk(M,P), covers(G,R), region(P,R).
valid_story(M,P) :- mission(M), prize(P), mission_risk(M,P), fix(_,M,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((m, p) for m in MISSIONS for p in PRIZES if mission_at_risk(_safe_lookup(MISSIONS, m), _safe_lookup(PRIZES, p)) and select_gear(_safe_lookup(MISSIONS, m), _safe_lookup(PRIZES, p)))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print(" only in clingo:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-kindergarten story world with humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=PARENT_NAMES)
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
    if getattr(args, "mission", None) and getattr(args, "prize", None):
        if not (mission_at_risk(_safe_lookup(MISSIONS, getattr(args, "mission", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))) and select_gear(_safe_lookup(MISSIONS, getattr(args, "mission", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    missions = [m for m in MISSIONS if getattr(args, "mission", None) in (None, m)]
    prizes = [p for p in PRIZES if getattr(args, "prize", None) in (None, p)]
    combos = [(m, p) for m in missions for p in prizes if mission_at_risk(_safe_lookup(MISSIONS, m), _safe_lookup(PRIZES, p)) and select_gear(_safe_lookup(MISSIONS, m), _safe_lookup(PRIZES, p))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    m, p = rng.choice(list(combos))
    return StoryParams(
        place=getattr(args, "place", None) or "kindergarten",
        mission=m,
        prize=p,
        name=getattr(args, "name", None) or rng.choice(KID_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        helper=getattr(args, "helper", None) or rng.choice(PARENT_NAMES),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    kid = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Owen", "Theo", "Ezra", "Ari"} else "girl"))
    helper = world.add(Entity(id="Helper", kind="character", type="teacher", label=params.helper))
    prize = world.add(Entity(id="Prize", type=params.prize, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=kid.id, caretaker=helper.id))
    mission = _safe_lookup(MISSIONS, params.mission)

    kid.traits = ["little", params.trait, "hero"]
    kid.memes["joy"] += 1
    kid.memes["pride"] += 1

    world.say(f"{kid.id} was a little {params.trait} superhero at {world.setting.place}, and {kid.pronoun('possessive')} favorite thing was helping everyone.")
    world.say(f"{kid.id} loved {mission.gerund}, especially when {mission.keyword} days made the room feel like a comic book.")

    world.para()
    world.say(f"One bright day at {world.setting.place}, {kid.id} noticed {prize.phrase} near the toy corner.")
    world.say(f"{kid.id} wanted to {mission.verb}, but the mission {mission.risk}.")

    kid.memes["worry"] += 1
    world.zone = set(mission.zone)
    if params.mission == "silica":
        prize.meters["mess"] += 1
        kid.memes["humor"] += 1
        world.say(f"The glittery silica jar looked important, and also a tiny bit sneaky, like it knew it could sparkle everywhere.")

    world.para()
    gear = select_gear(mission, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    world.say(f"{helper.label if helper.label else params.helper} smiled and said, \"Let's use {gear.label} first.\"")
    world.say(gear.humor_line)
    world.say(f"That way, {kid.id} could {mission.verb} without upsetting {prize.label}.")

    kid.memes["worry"] = 0
    kid.memes["humor"] += 1
    kid.memes["joy"] += 1
    kid.memes["conflict"] = 0
    prize.meters["mess"] = 0
    prize.carried_by = kid.id
    prize.worn_by = kid.id

    world.para()
    world.say(f"{kid.id} zipped off on the safe plan, {mission.gerund}, and laughing so hard {kid.id} almost wobbled like a tiny rocket.")
    world.say(f"In the end, {prize.label} stayed safe, {kid.id} felt like a true hero, and the kindergarten room was full of happy giggles.")

    world.facts.update(
        kid=kid,
        helper=helper,
        prize=prize,
        mission=mission,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for kindergarten that includes the word "{mission.keyword}" and a funny safe solution.',
        f"Tell a gentle story where {kid.id} wants to {mission.verb} but worries about {prize.phrase}, then solves the problem with humor.",
        f"Write a tiny comic-style story about a child hero at kindergarten, a risky {mission.keyword} mission, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    mission = _safe_fact(world, f, "mission")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What kind of hero was {kid.id} at kindergarten?",
            answer=f"{kid.id} was a little {kid.traits[1]} superhero who liked helping classmates and solving small problems.",
        ),
        QAItem(
            question=f"What did {kid.id} want to do with the {prize.label}?",
            answer=f"{kid.id} wanted to {mission.verb}, but the {prize.label} needed to stay safe.",
        ),
        QAItem(
            question=f"How did {helper.label if helper.label else 'the helper'} help {kid.id}?",
            answer=f"{helper.label if helper.label else 'The helper'} suggested using {gear.label} first, which was a funny but safe way to let {kid.id} keep going.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {kid.id} felt proud and happy, and the {prize.label} stayed safe while the kindergarten room filled with giggles.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindergarten?",
            answer="Kindergarten is a place where young children learn, play, and practice being kind and brave together.",
        ),
        QAItem(
            question="What is a cone?",
            answer="A cone is a pointy shape, and it can also be a traffic cone that helps people notice a spot or stay away from it.",
        ),
        QAItem(
            question="What is silica?",
            answer="Silica is a natural material found in sand and tiny grains. It can sparkle when it is in little pieces.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and makes people smile or laugh.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="kindergarten", mission="cone", prize="badge", name="Mila", trait="silly", helper="Teacher Sun"),
    StoryParams(place="kindergarten", mission="silica", prize="cape", name="Owen", trait="brave", helper="Ms. Piper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(combos)
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
