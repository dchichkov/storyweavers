#!/usr/bin/env python3
"""
A small comedy-leaning storyworld about a delivery fleet, a careful promise,
and the funny trouble that follows when the same caution is repeated too many
times.

Seed-tale premise:
- A child or small captain is responsible for a little fleet.
- Someone makes a promise to be careful.
- Repeated warnings become a running joke.
- A harmless cautionary mistake threatens a delivery.
- The story resolves with a smarter plan and a cheerful ending.

The world model tracks:
- physical meters: speed, load, wobble, wear, tidiness, distance, fuel
- emotional memes: worry, confidence, pride, relief, annoyance, trust, laughter

This world supports:
- a default randomized run
- --all curated runs
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
# Core domain vocabulary
# ---------------------------------------------------------------------------

MODES = {"pedal", "sail", "skate", "roll"}
SHIP_TYPES = {"fleet": "fleet"}
HAZARDS = {"puddle", "hill", "wind", "mud", "corner"}

# ---------------------------------------------------------------------------
# Typed entities
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "girl", "mother", "woman"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class FleetConfig:
    name: str
    mode: str
    hazard: str
    caution: str
    repetition_count: int
    ending: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class DeliveryItem:
    label: str
    phrase: str
    region: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    fleet: str = ""
    mode: str = ""
    hazard: str = ""
    package: str = ""
    captain_name: str = ""
    captain_type: str = ""
    helper_name: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
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


class World:
    def __init__(self, config: FleetConfig) -> None:
        self.config = config
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.config)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

CATCHPHRASES = [
    "Sure thing!",
    "I promise!",
    "Absolutely sure.",
    "No problem at all.",
]

CAPTAIN_NAMES = ["Mina", "Toby", "Lena", "Arlo", "June", "Pip"]
HELPER_NAMES = ["Dot", "Milo", "Bean", "Nina", "Bram", "Poppy"]
TRAITS = ["cheerful", "careful", "silly", "brave", "bouncy"]

FLEETS = {
    "tiny_trucks": FleetConfig(
        name="the tiny delivery fleet",
        mode="roll",
        hazard="hill",
        caution="keep the wheels straight",
        repetition_count=3,
        ending="rolled in a neat line",
    ),
    "harbor_boats": FleetConfig(
        name="the little harbor fleet",
        mode="sail",
        hazard="wind",
        caution="keep the sails low",
        repetition_count=3,
        ending="bobbed back to the dock",
    ),
    "park_bikes": FleetConfig(
        name="the park bike fleet",
        mode="pedal",
        hazard="puddle",
        caution="slow down near the puddle",
        repetition_count=2,
        ending="pedaled home together",
    ),
}

PACKAGES = {
    "cake": DeliveryItem("cake box", "a box with a cherry cake", "top", fragile=True),
    "flowers": DeliveryItem("flowers", "a bundle of bright flowers", "basket", fragile=True),
    "books": DeliveryItem("books", "a stack of library books", "rack", fragile=False),
    "cookies": DeliveryItem("cookies", "a tin of sugar cookies", "bin", fragile=True),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def valid_combo(fleet_key: str, package_key: str, hazard: str) -> bool:
    config = _safe_lookup(FLEETS, fleet_key)
    package = _safe_lookup(PACKAGES, package_key)
    if hazard not in HAZARDS:
        return False
    # Cautionary comedy works best when there is a real, but not disastrous, risk.
    if config.mode == "pedal" and hazard == "wind":
        return False
    if config.mode == "sail" and hazard == "puddle":
        return False
    if package.label == "books" and hazard == "puddle":
        return False
    return True


def reason_for_rejection(fleet_key: str, package_key: str, hazard: str) -> str:
    config = _safe_lookup(FLEETS, fleet_key)
    package = _safe_lookup(PACKAGES, package_key)
    return (
        f"(No story: {config.name} with {package.label} and a {hazard} does not "
        f"make a good cautionary comedy. The danger is either too silly or too weak "
        f"for the repeated warning-and-promise beat.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(F,P,H) :- fleet(F), package(P), hazard(H), allowed(F,H), risky(F,P,H).

risky(F,P,H) :- mode(F,"roll"), H="hill", fragile(P).
risky(F,P,H) :- mode(F,"sail"), H="wind", fragile(P).
risky(F,P,H) :- mode(F,"pedal"), H="puddle", fragile(P).

allowed(F,H) :- hazard(H), fleet(F).

% Reject combinations that obviously break the comedy premise.
:- mode(F,"pedal"), hazard("wind").
:- mode(F,"sail"), hazard("puddle").
:- package("books"), hazard("puddle").
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fk, cfg in FLEETS.items():
        lines.append(asp.fact("fleet", fk))
        lines.append(asp.fact("mode", fk, cfg.mode))
        lines.append(asp.fact("caution", fk, cfg.caution))
    for pk, pkg in PACKAGES.items():
        lines.append(asp.fact("package", pk))
        if pkg.fragile:
            lines.append(asp.fact("fragile", pk))
    for hz in sorted(HAZARDS):
        lines.append(asp.fact("hazard", hz))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {
        (fk, pk, hz)
        for fk in FLEETS
        for pk in PACKAGES
        for hz in HAZARDS
        if valid_combo(fk, pk, hz)
    }
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between python and clingo:")
    print("only python:", sorted(py - asp_set))
    print("only clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def make_world(params: StoryParams) -> World:
    config = _safe_lookup(FLEETS, params.fleet)
    world = World(config)

    captain = world.add(
        Entity(
            id=params.captain_name,
            kind="character",
            type=params.captain_type,
            label=params.captain_name,
            meters={"confidence": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0},
            memes={"trust": 1.0, "laughter": 0.0, "annoyance": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type="helper",
            label=params.helper_name,
            meters={"confidence": 0.0, "worry": 0.0, "focus": 0.0},
            memes={"trust": 1.0, "laughter": 0.0},
        )
    )
    package = world.add(
        Entity(
            id="package",
            type="package",
            label=_safe_lookup(PACKAGES, params.package).label,
            phrase=_safe_lookup(PACKAGES, params.package).phrase,
            plural=params.package == "books",
            owner=captain.id,
            meters={"tidiness": 1.0, "wear": 0.0, "distance": 0.0},
        )
    )
    fleet = world.add(
        Entity(
            id="fleet",
            kind="thing",
            type="fleet",
            label=config.name,
            meters={"speed": 0.0, "load": 1.0, "wobble": 0.0, "distance": 0.0},
            memes={"busy": 1.0, "confidence": 0.0},
        )
    )

    world.facts.update(
        captain=captain,
        helper=helper,
        package=package,
        fleet=fleet,
        params=params,
        config=config,
    )
    return world


def apply_departure(world: World) -> None:
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    fleet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fleet")
    package = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "package")
    config = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "config")

    captain.memes["trust"] += 0.5
    captain.meters["confidence"] += 1.0
    helper.meters["focus"] += 1.0
    fleet.meters["speed"] += 1.0
    fleet.meters["load"] += 1.0
    package.meters["distance"] += 1.0

    world.say(
        f"{captain.id} looked at {config.name} and said, \"{random.choice(CATCHPHRASES)}\" "
        f"because {captain.id} had made a promise to be careful."
    )
    world.say(
        f"{helper.id} nodded, sure as a spoon in a soup bowl, and checked the package once, then twice."
    )


def apply_repetition(world: World) -> None:
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    config = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "config")

    for i in range(config.repetition_count):
        captain.memes["trust"] += 0.1
        helper.memes["laughter"] += 0.2
        captain.memes["worry"] += 0.1
        world.say(
            f"\"Remember the caution,\" said {helper.id}. "
            f"\"{config.caution.capitalize()}!\""
        )
        world.say(
            f"\"Sure,\" said {captain.id}, promise in a tiny voice, and then said it again: "
            f"\"I promise.\""
        )
        if i == 0:
            world.say("That sounded safe enough.")
        elif i == 1:
            world.say("It sounded safe enough the second time too.")
        else:
            world.say("By the third time, even the pigeons seemed to be listening.")


def trigger_comedy_mishap(world: World) -> None:
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    package = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "package")
    fleet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fleet")
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")

    if params.hazard == "hill":
        fleet.meters["wobble"] += 1.0
        package.meters["distance"] += 1.0
        package.meters["wear"] += 1.0
        captain.memes["worry"] += 1.0
        world.say(
            f"Then the fleet reached the hill, and the front wheel gave a dramatic wobble."
        )
        world.say(
            f"{captain.id} tried to stay sure, but the box tipped, then bobbed, then tipped again."
        )
    elif params.hazard == "wind":
        fleet.meters["wobble"] += 1.0
        package.meters["wear"] += 1.0
        helper.memes["laughter"] += 1.0
        world.say("Then a windy gust puffed the sails so hard they looked like startled pillows.")
        world.say(f"{helper.id} said, \"I did say low sails,\" and {captain.id} laughed too late.")
    elif params.hazard == "puddle":
        fleet.meters["wobble"] += 1.0
        package.meters["wear"] += 1.0
        captain.memes["worry"] += 1.0
        world.say("Then a puddle flashed across the path like a shiny trap for wheels.")
        world.say(f"{captain.id} said, \"I promise I saw it,\" which was not the same as stopping.")
    else:
        world.say("Then the day tried a small trick, just to keep everyone awake.")

    if package.meters["wear"] >= THRESHOLD:
        helper.memes["annoyance"] += 0.5
        world.say(
            f"The package stayed mostly safe, but {helper.id} made a face that meant more caution was needed."
        )


def resolve(world: World) -> None:
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    package = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "package")
    fleet = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fleet")
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")

    captain.memes["worry"] = max(0.0, captain.memes["worry"] - 0.5)
    captain.memes["relief"] += 1.0
    captain.memes["pride"] += 1.0
    helper.memes["laughter"] += 0.5
    fleet.meters["wobble"] = max(0.0, fleet.meters["wobble"] - 0.5)

    world.say(
        f"{helper.id} finally pointed to a smarter plan: slow down first, then go around the trouble."
    )
    world.say(
        f"{captain.id} agreed at once, and this time the promise was not just repeated; it was kept."
    )
    world.say(
        f"So {params.fleet.replace('_', ' ')} {world.config.ending}, {package.label} stayed tidy, "
        f"and everyone laughed because the best joke was how careful they had become."
    )


def simulate(params: StoryParams) -> World:
    world = make_world(params)
    apply_departure(world)
    world.para()
    apply_repetition(world)
    trigger_comedy_mishap(world)
    world.para()
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "config")
    pkg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "package")
    return [
        f'Write a short comedy for a child about {cfg.name}, a promise, and a careful mistake.',
        f"Tell a story where {p.captain_name} keeps saying sure and promise while leading {cfg.name} past a {p.hazard}.",
        f"Write a gentle, funny story that includes the words sure, promise, and fleet, and ends with {pkg.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "config")
    cap = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    package = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "package")

    return [
        QAItem(
            question=f"Who made the promise to be careful in the story?",
            answer=f"{cap.id} made the promise to be careful while helping lead {cfg.name}.",
        ),
        QAItem(
            question=f"What repeated warning kept getting said in the story?",
            answer=f"The warning was \"{cfg.caution.capitalize()}!\" and it was repeated more than once.",
        ),
        QAItem(
            question=f"What was the little fleet carrying?",
            answer=f"It was carrying {package.phrase}, and that made the trip feel extra important.",
        ),
        QAItem(
            question=f"Why was the story funny instead of scary?",
            answer=(
                f"It was funny because the same caution kept getting repeated, "
                f"the promise kept sounding bigger than the problem, and then the "
                f"helpers found a calmer plan before anything was ruined."
            ),
        ),
        QAItem(
            question=f"Who helped fix the problem at the end?",
            answer=f"{helper.id} helped by suggesting a slower, safer plan, and {cap.id} followed it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a promise?",
            answer="A promise is a serious thing you say when you mean you will try to do something and keep your word.",
        ),
        QAItem(
            question="What is a fleet?",
            answer="A fleet is a group of vehicles, boats, or other moving things that travel together.",
        ),
        QAItem(
            question="Why can repeated warnings be funny in a story?",
            answer="Repeated warnings can be funny when someone keeps hearing the same advice again and again, especially if they say they are sure but still need help.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you do not rush into trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("tiny_trucks", "roll", "hill", "cake", "Mina", "girl", "Dot"),
    StoryParams("harbor_boats", "sail", "wind", "flowers", "Toby", "boy", "Poppy"),
    StoryParams("park_bikes", "pedal", "puddle", "cookies", "Lena", "girl", "Milo"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comic cautionary fleet storyworld.")
    ap.add_argument("--fleet", choices=sorted(FLEETS))
    ap.add_argument("--mode", choices=sorted(MODES))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--package", choices=sorted(PACKAGES))
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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
    if getattr(args, "fleet", None) and getattr(args, "package", None) and getattr(args, "hazard", None):
        if not valid_combo(getattr(args, "fleet", None), getattr(args, "package", None), getattr(args, "hazard", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (fk, pk, hz)
        for fk in FLEETS
        for pk in PACKAGES
        for hz in HAZARDS
        if valid_combo(fk, pk, hz)
        and (getattr(args, "fleet", None) is None or fk == getattr(args, "fleet", None))
        and (getattr(args, "mode", None) is None or _safe_lookup(FLEETS, fk).mode == getattr(args, "mode", None))
        and (getattr(args, "hazard", None) is None or hz == getattr(args, "hazard", None))
        and (getattr(args, "package", None) is None or pk == getattr(args, "package", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    fleet, package, hazard = rng.choice(list(combos))
    mode = _safe_lookup(FLEETS, fleet).mode
    captain_type = getattr(args, "captain_type", None) or rng.choice(["girl", "boy"])
    captain_name = getattr(args, "captain_name", None) or rng.choice(CAPTAIN_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        fleet=fleet,
        mode=mode,
        hazard=hazard,
        package=package,
        captain_name=captain_name,
        captain_type=captain_type,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid fleet/package/hazard combinations:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.captain_name}: {p.fleet} / {p.hazard} / {p.package}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
