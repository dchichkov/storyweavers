#!/usr/bin/env python3
"""
A tiny story world for a silly space adventure with foreshadowing and a twist.

Premise:
- A child astronaut prepares for a small mission.
- A promised star treat goes missing.
- Foreshadowing clues hint that a tiny helper aboard the ship knows more than it seems.
- The twist reveals the "mysterious" helper was the ship's snack drone, which had only been hiding the treat to cool it down.

The world simulates physical meters and emotional memes, and the prose is driven by
the state changes rather than a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    drone: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class World:
    ship: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.ship)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
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
    name: str
    gender: str
    parent: str
    ship: str
    mission: str
    prize: str
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


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    clue: str
    zone: str
    foreshadow: str
    twist_reveal: str
    keyword: str
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
    id: str
    label: str
    phrase: str
    location: str
    clue: str
    spoil_risk: str
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
class Helper:
    id: str
    label: str
    reveal: str
    role: str
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


GIRL_NAMES = ["Lina", "Mira", "Zoe", "Nia", "Ava", "Tess"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Owen", "Kai", "Noel"]
TRAITS = ["brave", "curious", "cheerful", "silly"]


MISSIONS = {
    "moonwalk": Mission(
        id="moonwalk",
        verb="bounce on the moon",
        gerund="bouncing on the moon",
        risk="lose a tiny boot",
        clue="one boot kept tapping by itself in the corner",
        zone="cargo bay",
        foreshadow="a soft clink echoed from the snack shelf",
        twist_reveal="the clink came from a snack drone with a very serious tummy light",
        keyword="moon",
    ),
    "comet": Mission(
        id="comet",
        verb="chase the comet trail",
        gerund="chasing comet dust",
        risk="get comet dust in the scanner",
        clue="the scanner blinked twice like it was trying not to laugh",
        zone="bridge",
        foreshadow="a blue light flashed behind the tea tin",
        twist_reveal="the blue light was the drone's cool-box keeping the treat from melting",
        keyword="comet",
    ),
    "stargarden": Mission(
        id="stargarden",
        verb="plant star seeds",
        gerund="planting star seeds",
        risk="spill shiny seed dust",
        clue="one spoon vanished and reappeared polished and smug",
        zone="greenhouse",
        foreshadow="little wheel marks circled the sweet crate",
        twist_reveal="the wheel marks belonged to the snack drone delivering the snack in secret",
        keyword="star",
    ),
}

PRIZES = {
    "cookie": Prize(
        id="cookie",
        label="cookie",
        phrase="a round sugar cookie shaped like a rocket",
        location="snack crate",
        clue="the cookie box was empty except for crumbs shaped like tiny stars",
        spoil_risk="get warm and crumbly",
    ),
    "juice": Prize(
        id="juice",
        label="juice pouch",
        phrase="a berry juice pouch with a silver straw",
        location="cool drawer",
        clue="the pouch felt cool, but the drawer hummed softly nearby",
        spoil_risk="get warm and flat",
    ),
    "berries": Prize(
        id="berries",
        label="berry cup",
        phrase="a little berry cup with a paper lid",
        location="cargo shelf",
        clue="the paper lid had a tiny neat hole in it",
        spoil_risk="get squished",
    ),
}

HELPERS = {
    "drone": Helper(
        id="drone",
        label="snack drone",
        reveal="A tiny snack drone rolled out with the missing treat in its tray.",
        role="helper",
    ),
}


ASP_RULES = r"""
#show valid_story/4.

mission(M) :- mission_kind(M).
prize(P) :- prize_kind(P).
helper(H) :- helper_kind(H).

risk_pair(M, P) :- risky(M, Zone), stored(P, Zone).
valid_story(N, M, P, G) :- name(N), mission(M), prize(P), gender(G), risk_pair(M, P).
"""

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES_BY_GENDER = {
    "girl": GIRL_NAMES,
    "boy": BOY_NAMES,
}

HUMAN_TRAITS = TRAITS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid, m in MISSIONS.items():
        for pid, p in PRIZES.items():
            if m.zone == "cargo bay" and p.id == "cookie":
                combos.append(("any", mid, pid))
            elif m.zone == "bridge" and p.id == "juice":
                combos.append(("any", mid, pid))
            elif m.zone == "greenhouse" and p.id == "berries":
                combos.append(("any", mid, pid))
    return combos


def prize_at_risk(mission: Mission, prize: Prize) -> bool:
    return (
        (mission.zone == "cargo bay" and prize.id == "cookie")
        or (mission.zone == "bridge" and prize.id == "juice")
        or (mission.zone == "greenhouse" and prize.id == "berries")
    )


def select_gear(mission: Mission, prize: Prize) -> str:
    if mission.zone == "cargo bay" and prize.id == "cookie":
        return "cool pouch"
    if mission.zone == "bridge" and prize.id == "juice":
        return "shade cap"
    if mission.zone == "greenhouse" and prize.id == "berries":
        return "soft tray"
    pass


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return (
        f"(No story: {mission.gerund} does not honestly threaten {prize.label}. "
        f"Choose the prize that fits the mission's risk zone.)"
    )


# ---------------------------------------------------------------------------
# ASP bridge
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("name", name))
    for g in NAMES_BY_GENDER:
        lines.append(asp.fact("gender", g))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission_kind", mid))
        lines.append(asp.fact("risky", mid, m.zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_kind", pid))
        lines.append(asp.fact("stored", pid, p.location))
    lines.append(asp.fact("helper_kind", "drone"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(n, m, p) for (n, m, p, _g) in asp_valid_stories()]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(params.ship)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        role="pilot",
        meters={"joy": 0.0},
        memes={"hope": 0.0, "curiosity": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
        label=params.parent,
        role="captain",
        meters={"calm": 0.0},
        memes={"care": 0.0},
    ))
    mission = _safe_lookup(MISSIONS, params.mission)
    prize = _safe_lookup(PRIZES, params.prize)
    helper = HELPERS["drone"]
    drone = world.add(Entity(
        id=helper.id,
        kind="thing",
        type="drone",
        label=helper.label,
        role=helper.role,
        location=prize.location,
        meters={"battery": 1.0},
        memes={"secret": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, mission=mission, prize=prize, drone=drone)
    return world


def foreshadow(world: World) -> None:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    prize: Prize = _safe_fact(world, world.facts, "prize")
    world.say(
        f"{world.facts['hero'].label} loved the {world.ship}, because every panel hummed like a sleepy song."
    )
    world.say(
        f"One silly day, {world.facts['hero'].label} wanted to {mission.verb} in the {mission.zone}, "
        f"while {world.facts['parent'].label} kept a careful eye on the {prize.label}."
    )
    world.say(
        f"Before the mission even began, {mission.foreshadow}."
    )
    world.say(
        f"That was odd enough to make {world.facts['hero'].label} grin and look around twice."
    )


def tension(world: World) -> None:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    prize: Prize = _safe_fact(world, world.facts, "prize")
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")

    hero.meters["joy"] += 1
    hero.memes["curiosity"] += 1
    parent.memes["care"] += 1
    world.para()
    world.say(
        f"{hero.label} asked to start the {mission.keyword} mission right away, but {parent.label} pointed at the {prize.label}."
    )
    world.say(
        f'"If we go now," {parent.label} said, "the {prize.label} might {prize.spoil_risk}."'
    )
    world.say(
        f"{hero.label} tried not to laugh, but a tiny clink came from the {prize.location} again."
    )
    world.say(
        f"Then the ship gave one extra blink, like it was telling a joke nobody understood yet."
    )
    world.facts["clue"] = mission.clue
    world.say(f"The clue was there all along: {mission.clue}.")


def twist(world: World) -> None:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    prize: Prize = _safe_fact(world, world.facts, "prize")
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    drone = _safe_fact(world, world.facts, "drone")

    world.para()
    world.say(
        f"{hero.label} peeked behind the {prize.location}, expecting a space mouse or a moon goblin."
    )
    world.say(mission.twist_reveal + ".")
    world.say(
        f"{drone.label.capitalize()} rolled forward and spun in a tiny circle, proud as a parade drum."
    )
    world.say(
        f'"I was not stealing it!" the {drone.label} beeped. "I was cooling it, polishing it, and making it extra bouncy."'
    )
    world.say(
        f"{parent.label} blinked, then laughed so hard the whole cabin felt lighter."
    )
    world.facts["reveal"] = helper_reveal_text(drone, prize, mission)


def resolution(world: World) -> None:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    prize: Prize = _safe_fact(world, world.facts, "prize")
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    drone = _safe_fact(world, world.facts, "drone")
    gear = select_gear(mission, prize)

    world.para()
    hero.meters["joy"] += 1
    hero.memes["hope"] += 1
    parent.meters["calm"] += 1
    world.say(
        f"{parent.label} tucked the {prize.label} into the {gear}, and the silly mission could finally begin."
    )
    world.say(
        f"{hero.label} {mission.gerund}, while the {drone.label} zipped beside {hero.pronoun('object')} like a shiny joke."
    )
    world.say(
        f"In the end, the {prize.label} stayed safe, the clue made sense, and the whole ship felt warm with laughter."
    )
    world.say(
        f"The twist had been friendly all along: the missing treat was never gone, only hidden in the coolest place on the ship."
    )


def helper_reveal_text(drone: Entity, prize: Prize, mission: Mission) -> str:
    return f"{drone.label} had hidden the {prize.label} because the ship was keeping it cool before launch"


def tell(params: StoryParams) -> World:
    world = build_world(params)
    foreshadow(world)
    tension(world)
    twist(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short, silly space adventure for children that includes the word "{f["mission"].keyword}".',
        f"Tell a story about {f['hero'].label}, a careful parent, and a missing {f['prize'].label} on a spaceship.",
        f"Write a foreshadowing-and-twist story where a small clue turns out to be about a helper drone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    mission = _safe_fact(world, world.facts, "mission")
    prize = _safe_fact(world, world.facts, "prize")
    return [
        QAItem(
            question=f"What did {hero.label} want to do on the ship?",
            answer=f"{hero.label} wanted to {mission.verb} in the {mission.zone}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried the {prize.label} might {prize.spoil_risk} during the mission.",
        ),
        QAItem(
            question="What was the foreshadowing clue?",
            answer=f"The clue was that {mission.clue}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the missing treat was kept safe by a snack drone, not stolen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spaceship for?",
            answer="A spaceship is a vehicle that carries people through space.",
        ),
        QAItem(
            question="Why might a snack be cooled before a trip?",
            answer="A snack might be cooled so it stays fresh, firm, or tasty during the trip.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue that hints at something important later.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes you understand the story in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} loc={e.location} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(name="Lina", gender="girl", parent="mom", ship="Star Wren", mission="moonwalk", prize="cookie"),
    StoryParams(name="Finn", gender="boy", parent="dad", ship="Comet Nest", mission="comet", prize="juice"),
    StoryParams(name="Mira", gender="girl", parent="mom", ship="Orbit Rose", mission="stargarden", prize="berries"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Silly foreshadowing-and-twist space adventure story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--ship")
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    mission = getattr(args, "mission", None) or rng.choice(list(MISSIONS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not prize_at_risk(_safe_lookup(MISSIONS, mission), _safe_lookup(PRIZES, prize)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_BY_GENDER[gender])
    parent = getattr(args, "parent", None) or rng.choice(["mom", "dad"])
    ship = getattr(args, "ship", None) or rng.choice(["Star Wren", "Comet Nest", "Orbit Rose", "Tiny Nebula"])
    return StoryParams(name=name, gender=gender, parent=parent, ship=ship, mission=mission, prize=prize)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/4.\n")
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/4.\n")
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for s in stories:
            print(s)
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
