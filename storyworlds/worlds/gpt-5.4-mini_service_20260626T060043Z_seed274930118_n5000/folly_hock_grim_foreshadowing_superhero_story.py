#!/usr/bin/env python3
"""
Storyworld: a tiny superhero tale with foreshadowing, a risky folly, and a hock.

This world is inspired by a small child-friendly superhero story shape:
- a hero wants to help
- a grim problem appears
- a warning or foreshadowed sign hints that a rash choice could go wrong
- the hero makes a folly, hocks something valuable for a quick fix, then learns a better way
- the ending proves what changed

The world is modeled as a state machine with physical meters and emotional memes.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    hocked: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
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
    indoor: bool
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
class Threat:
    id: str
    label: str
    grim_word: str
    spreads: set[str]
    risk_tag: str
    foreshadow: str
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
class Prize:
    label: str
    phrase: str
    type: str
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
    prep: str
    tail: str
    protects_from: set[str]
    covers: set[str]
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
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "city": Setting(place="the city", indoor=False, affords={"dash", "hover", "lift"}),
    "roof": Setting(place="the rooftop", indoor=False, affords={"dash", "hover"}),
    "laboratory": Setting(place="the laboratory", indoor=True, affords={"lift", "scan"}),
}

THREATS = {
    "smoke": Threat(
        id="smoke",
        label="smoke",
        grim_word="grim",
        spreads={"hands", "torso"},
        risk_tag="dark",
        foreshadow="a thin gray ribbon curled from a broken pipe",
    ),
    "sludge": Threat(
        id="sludge",
        label="sludge",
        grim_word="grim",
        spreads={"feet", "legs"},
        risk_tag="messy",
        foreshadow="a glossy black drip winked under the floor vent",
    ),
    "sparks": Threat(
        id="sparks",
        label="sparks",
        grim_word="grim",
        spreads={"torso"},
        risk_tag="hot",
        foreshadow="tiny orange sparks snapped in the air like impatient crickets",
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "gloves": Prize(label="gloves", phrase="strong blue gloves", type="gloves", region="hands", plural=True),
    "boots": Prize(label="boots", phrase="shiny rescue boots", type="boots", region="feet", plural=True),
}

GEAR = {
    "mask": Gear(
        id="mask",
        label="a mask",
        prep="put on a mask first",
        tail="pulled on the mask before going back out",
        protects_from={"smoke"},
        covers={"face"},
    ),
    "boots": Gear(
        id="boots",
        label="storm boots",
        prep="switch to storm boots",
        tail="changed into storm boots",
        protects_from={"sludge"},
        covers={"feet"},
        plural=True,
    ),
    "shield": Gear(
        id="shield",
        label="a light shield",
        prep="carry a light shield",
        tail="grabbed the light shield",
        protects_from={"sparks"},
        covers={"torso"},
    ),
}

HERO_NAMES = ["Nova", "Milo", "Zara", "Finn", "Ivy", "Jett", "Luna", "Arlo"]
SIDEKICKS = ["Aunt Spark", "Captain Maple", "Coach Comet", "Mira"]
TRAITS = ["brave", "curious", "quick", "kind", "bold"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A threat is at risk for a prize when its spread reaches the same body region.
at_risk(T, P) :- threat(T), prize(P), spreads(T, R), worn_on(P, R).

% Gear is a valid fix when it blocks the threat and covers the at-risk region.
fix(G, T, P) :- gear(G), at_risk(T, P), blocks(G, T), covers(G, R), worn_on(P, R).
valid_story(S, T, P, G) :- setting(S), threat(T), prize(P), fix(G, T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, th in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("risk_tag", tid, th.risk_tag))
        for r in sorted(th.spreads):
            lines.append(asp.fact("spreads", tid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for t in sorted(g.protects_from):
            lines.append(asp.fact("blocks", gid, t))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def threatens(prize: Prize, threat: Threat) -> bool:
    return prize.region in threat.spreads


def selects_gear(threat: Threat, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if threat.id in gear.protects_from and prize.region in gear.covers:
            return gear
    return None


def valid_stories() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for tid, threat in THREATS.items():
            for pid, prize in PRIZES.items():
                if threatens(prize, threat) and selects_gear(threat, prize):
                    for gid, gear in GEAR.items():
                        if threat.id in gear.protects_from and prize.region in gear.covers:
                            out.append((sid, tid, pid, gid))
    return out


def predict(world: World, hero: Entity, threat: Threat, prize: Prize) -> dict[str, bool]:
    sim = world.copy()
    simulate_misstep(sim, hero, threat, prize, narrate=False)
    return {
        "ruined": bool(sim.facts.get("prize_ruined")),
        "grim": bool(sim.facts.get("grim_seen")),
    }


def foreshadow_line(threat: Threat) -> str:
    return threat.foreshadow


def simulate_misstep(world: World, hero: Entity, threat: Threat, prize: Prize, narrate: bool = True) -> None:
    if threaten_state := threatens(prize, threat):
        world.facts["grim_seen"] = True
        if narrate:
            world.say(f"Outside, {foreshadow_line(threat)}.")
        hero.memes["worry"] += 1
        hero.memes["curiosity"] += 1
        hero.meters["exposure"] = hero.meters.get("exposure", 0) + 1
        if prize.region in threat.spreads:
            world.facts["prize_ruined"] = True
            world.facts["threat"] = threat
            world.facts["prize"] = prize
            if narrate:
                world.say(f"{hero.id}'s {prize.label} got {threat.label} on it, and the day turned {threat.grim_word}.")
    return None


def tell_story(setting: Setting, threat: Threat, prize: Prize, hero_name: str,
               hero_type: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"hope": 1}))
    helper = world.add(Entity(id=helper_name, kind="character", type="hero", label=helper_name))
    prize_ent = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=prize.plural,
    ))
    hero.meters["style"] = 1
    prize_ent.worn_by = hero.id

    # Act 1: setup and foreshadowing
    world.say(f"{hero.id} was a {trait} little hero who loved helping in {setting.place}.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a promise to do good.")
    world.say(f"{helper_name} watched the sky and said, \"Something {threat.grim_word} may be coming.\"")
    world.say(f"Still, {hero.id} smiled, because {hero.id} wanted to be useful.")

    # Act 2: problem and folly
    world.para()
    world.say(f"Then the city shook as {threat.label} leaked into the street.")
    simulate_misstep(world, hero, threat, prize)
    hero.memes["folly"] = hero.memes.get("folly", 0) + 1
    world.say(f"{hero.id} made one quick folly and rushed in without thinking.")
    world.say(f"{hero.id} tried to help with {hero.pronoun('possessive')} {prize.label}, but the threat clung on.")

    # A hock: hero pawns something to get an emergency fix
    world.para()
    gear = selects_gear(threat, prize)
    if gear is None:
        pass
    hocked = world.add(Entity(
        id="hock_item",
        type="thing",
        label="a silver badge",
        phrase="a silver badge with a star on it",
        owner=hero.id,
        caretaker=helper.id,
    ))
    world.facts["hocked"] = hocked
    world.say(f"In a hurry, {hero.id} chose to hock {hocked.phrase} for the right gear.")
    world.say(f"{helper_name} did not scold {hero.id}; instead, {helper_name} handed over {gear.label}.")

    # Resolution
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1)
    hero.memes["hope"] += 2
    world.say(f'"Good," said {helper_name}. "{gear.prep}, and then go back to help the safe way."')
    world.say(f"{hero.id} {gear.tail}, and this time the {prize.label} stayed safe.")
    world.say(f"At the end, {hero.id} was still a hero, but a wiser one.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize_ent,
        threat=threat,
        gear=gear,
        setting=setting,
        trait=trait,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story/QA
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    threat: str
    prize: str
    name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    threat: Threat = _safe_fact(world, f, "threat")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    gear: Gear = _safe_fact(world, f, "gear")  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child that includes the words "folly", "hock", and "grim".',
        f"Tell a gentle superhero tale where {hero.id} faces {threat.label}, makes a folly, and hocks something for {gear.label}.",
        f"Write a story in which a foreshadowed warning helps {hero.id} save {prize.label} after a bad choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    threat: Threat = _safe_fact(world, f, "threat")  # type: ignore[assignment]
    gear: Gear = _safe_fact(world, f, "gear")  # type: ignore[assignment]
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {trait} little hero who wanted to help in {world.setting.place}.",
        ),
        QAItem(
            question=f"What foreshadowed the trouble before {hero.id} rushed in?",
            answer=f"The warning sign was that {threat.foreshadow}, which hinted that something {threat.grim_word} was near.",
        ),
        QAItem(
            question=f"What did {hero.id} hock to get the right fix?",
            answer=f"{hero.id} hocked a silver badge so {helper.id} could get {gear.label}.",
        ),
        QAItem(
            question=f"How did the story end for {prize.label}?",
            answer=f"{prize.label.capitalize()} stayed safe at the end because {hero.id} used {gear.label} and learned from the folly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a little hint about what may happen later, so readers can guess that trouble or a surprise is coming.",
        ),
        QAItem(
            question="What does it mean to hock something?",
            answer="To hock something means to pawn it or trade it quickly for money or help, often because someone needs a fast fix.",
        ),
        QAItem(
            question="What does grim mean?",
            answer="Grim means serious, dark, or worrying, like a problem that feels heavy and not cheerful.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="city", threat="smoke", prize="cape", name="Nova", helper="Captain Maple", trait="brave"),
    StoryParams(place="roof", threat="sparks", prize="gloves", name="Milo", helper="Coach Comet", trait="quick"),
    StoryParams(place="laboratory", threat="sludge", prize="boots", name="Ivy", helper="Aunt Spark", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a superhero tale with foreshadowing and a folly.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=SIDEKICKS)
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
    combos = []
    for sid, setting in SETTINGS.items():
        if getattr(args, "place", None) and sid != getattr(args, "place", None):
            continue
        for tid, threat in THREATS.items():
            if getattr(args, "threat", None) and tid != getattr(args, "threat", None):
                continue
            for pid, prize in PRIZES.items():
                if getattr(args, "prize", None) and pid != getattr(args, "prize", None):
                    continue
                if not threatens(prize, threat):
                    continue
                if selects_gear(threat, prize) is None:
                    continue
                combos.append((sid, tid, pid))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, threat, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        threat=threat,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(SIDEKICKS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(THREATS, params.threat),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        "hero",
        params.helper,
        params.trait,
    )
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


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story_set() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_full("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_full("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_story_set()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.name}: {p.threat} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
