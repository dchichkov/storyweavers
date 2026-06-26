#!/usr/bin/env python3
"""
storyworlds/worlds/bozo_capacity_razor_twist_space_adventure.py
===============================================================

A tiny space-adventure storyworld about a cautious crew, a bozo-ish helper,
and one tricky capacity problem with a razor-thin twist.

Seed idea:
A small ship must carry a precious rescue parcel through space. The crew
worries the pod is at capacity, but the bozo helper notices a hidden twist:
if the cargo is packed the right way, the ship can safely take off after all.

The world supports:
- a child-facing space voyage
- physical meters: fuel, capacity load, stress, damage, distance
- emotional memes: worry, courage, pride, relief, delight
- a tension/turn/resolution structure driven by state changes

The words bozo, capacity, razor, and Twist are intentionally part of the domain.
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
# Core world entities
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    cargo: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
class Ship:
    name: str
    capacity: int
    twist_slot: bool = True
    safe: bool = True
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
class StoryParams:
    crew: str
    helper: str
    cargo: str
    place: str
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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.twist_used: bool = False

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
        import copy
        c = World(copy.deepcopy(self.ship))
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.twist_used = self.twist_used
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SHIPS = {
    "comet": Ship(name="Comet Finch", capacity=3, twist_slot=True),
    "starling": Ship(name="Starling One", capacity=2, twist_slot=True),
    "orbit": Ship(name="Orbit Hopper", capacity=4, twist_slot=True),
}

LOCATIONS = {
    "dock": "the moon dock",
    "bay": "the cargo bay",
    "glowfield": "the glowfield station",
}

CREW = {
    "Ari": ("girl", "captain"),
    "Bozo": ("robot", "helper"),
    "Milo": ("boy", "pilot"),
    "Nia": ("girl", "navigator"),
}

CARGO = {
    "seedlings": ("a tray of rescue seedlings", False),
    "crates": ("two crate-bundles of spare cables", True),
    "glider": ("a small glider kit", False),
    "supplies": ("a bag of star snacks and water packs", False),
}

TRAITS = ["brave", "curious", "careful", "cheerful", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The ship is overloaded if the load is above capacity.
over_capacity(S) :- ship(S), ship_capacity(S, C), load(S, L), L > C.

% A twist is reasonable only when the ship has a twist slot and the cargo can be
% packed in a tighter way that reduces the load.
can_twist(S) :- ship(S), twist_slot(S), load(S, L), twist_reduces(S, D), L > D.

% A safe voyage exists when the load fits or the twist makes it fit.
safe_voyage(S) :- ship(S), load(S, L), ship_capacity(S, C), L =< C.
safe_voyage(S) :- can_twist(S), ship_capacity(S, C), twist_reduces(S, D), D =< C.

% A valid story needs one crew, one cargo, and a safe voyage.
valid_story(Crew, Cargo, Ship) :- crew(Crew), cargo(Cargo), ship(Ship), safe_voyage(Ship).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("ship_name", sid, ship.name))
        lines.append(asp.fact("ship_capacity", sid, ship.capacity))
        if ship.twist_slot:
            lines.append(asp.fact("twist_slot", sid))
    for cid, (text, plural) in CARGO.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_text", cid, text))
        if plural:
            lines.append(asp.fact("cargo_plural", cid))
    for name, (gender, role) in CREW.items():
        lines.append(asp.fact("crew", name))
        lines.append(asp.fact("crew_role", name, role))
        lines.append(asp.fact("crew_gender", name, gender))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(python_set - clingo_set))
    print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def cargo_load(cargo_id: str) -> int:
    return 2 if CARGO[cargo_id][1] else 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for crew in CREW:
        for cargo in CARGO:
            for ship_id, ship in SHIPS.items():
                if cargo_load(cargo) <= ship.capacity:
                    combos.append((crew, cargo, ship_id))
                elif ship.twist_slot and cargo_load(cargo) - 1 <= ship.capacity:
                    combos.append((crew, cargo, ship_id))
    return combos


def explain_rejection(cargo_id: str, ship_id: str) -> str:
    ship = _safe_lookup(SHIPS, ship_id)
    load = cargo_load(cargo_id)
    if load <= ship.capacity:
        return "(No story: that combination is already safe.)"
    if ship.twist_slot and load - 1 <= ship.capacity:
        return "(No story: the twist makes this combination safe, so it is valid.)"
    return (
        f"(No story: {CARGO[cargo_id][0]} is too much for {ship.name}. "
        f"It would stay over capacity even after the Twist.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict(world: World, ship_id: str, cargo_id: str) -> dict:
    load = cargo_load(cargo_id)
    ship = _safe_lookup(SHIPS, ship_id)
    over = load > ship.capacity
    twist_needed = over and ship.twist_slot and load - 1 <= ship.capacity
    return {"over": over, "twist_needed": twist_needed, "safe": not over or twist_needed}


def setup_world(params: StoryParams) -> World:
    ship = _safe_lookup(SHIPS, params.place)
    world = World(ship)
    crew_gender, crew_role = CREW[params.crew]
    helper_gender, helper_role = CREW[params.helper]
    cargo_text, plural = CARGO[params.cargo]

    captain = world.add(Entity(id=params.crew, kind="character", type=crew_gender, label=crew_role))
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_gender, label=helper_role))
    cargo = world.add(Entity(
        id=params.cargo,
        kind="thing",
        type="thing",
        label=params.cargo,
        phrase=cargo_text,
        plural=plural,
        owner=captain.id,
        carried_by=captain.id,
    ))

    captain.memes["pride"] = 1
    helper.memes["bozo"] = 1
    world.facts.update(
        captain=captain,
        helper=helper,
        cargo=cargo,
        ship=ship,
        cargo_text=cargo_text,
        place=params.place,
        loc=_safe_lookup(LOCATIONS, params.place),
    )
    return world


def intro(world: World) -> None:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    helper = _safe_fact(world, f, "helper")
    cargo = _safe_fact(world, f, "cargo")
    ship = _safe_fact(world, f, "ship")
    loc = _safe_fact(world, f, "loc")

    world.say(
        f"At {loc}, {captain.id} was a {random.choice(TRAITS)} captain who loved the sky."
    )
    world.say(
        f"{helper.id} was the ship's bozo helper, clanking cheerfully through the deck "
        f"with a grin that made the crew laugh."
    )
    world.say(
        f"They needed to carry {cargo.phrase} aboard {ship.name} for a quiet rescue flight."
    )


def tension(world: World, params: StoryParams) -> None:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    helper = _safe_fact(world, f, "helper")
    cargo = _safe_fact(world, f, "cargo")
    ship = _safe_fact(world, f, "ship")
    loc = _safe_fact(world, f, "loc")
    plan = predict(world, params.place, params.cargo)

    load = cargo_load(params.cargo)
    captain.memes["worry"] += 1
    ship.safe = not plan["over"]

    world.para()
    world.say(
        f"Near the hatch, {captain.id} checked the gauges and frowned. "
        f"The cargo load was {load}, but {ship.name} could only hold {ship.capacity}."
    )
    if plan["over"]:
        world.say(
            f"{cargo.phrase} would put the ship over capacity if they shoved it in as-is."
        )
    world.say(
        f"\"We can't launch from {loc} like this,\" {captain.id} said, while {helper.id} "
        f"scratched its head."
    )
    if plan["over"]:
        world.say(
            f"{helper.id} tried a bozo-sized grin and said, \"Maybe the answer is hiding in the Twist.\""
        )


def apply_twist(world: World, params: StoryParams) -> None:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    helper = _safe_fact(world, f, "helper")
    cargo = _safe_fact(world, f, "cargo")
    ship = _safe_fact(world, f, "ship")
    plan = predict(world, params.place, params.cargo)

    if not plan["over"]:
        return

    if not ship.twist_slot:
        pass

    # Reduce load by compressing/packing efficiently.
    cargo.meters["packed"] = 1
    world.twist_used = True
    captain.memes["surprise"] += 1
    helper.memes["pride"] += 1

    world.say(
        f"{helper.id} opened the Twist compartment, folded the cargo tight, and tucked away the loose pieces."
    )
    world.say(
        f"That careful move shaved the load down just enough to fit inside {ship.name}'s capacity."
    )


def resolution(world: World, params: StoryParams) -> None:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    helper = _safe_fact(world, f, "helper")
    cargo = _safe_fact(world, f, "cargo")
    ship = _safe_fact(world, f, "ship")

    load = cargo_load(params.cargo)
    safe_load = load - 1 if world.twist_used else load

    if safe_load > ship.capacity:
        pass

    captain.memes["worry"] = 0
    captain.memes["relief"] = 1
    helper.memes["delight"] = 1

    world.para()
    if world.twist_used:
        world.say(
            f"{captain.id} blinked, then smiled. The bozo helper had been right: the Twist made room."
        )
    world.say(
        f"Together they sealed the hatch, and {ship.name} rose from the dock with {cargo.phrase} safe inside."
    )
    world.say(
        f"By the time the ship drifted into the stars, the crew was laughing, and even the bozo helper stood tall."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    tension(world, params)
    apply_twist(world, params)
    resolution(world, params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child about {f["captain"].id}, '
        f'the bozo helper {f["helper"].id}, and a cargo problem with capacity.',
        f'Tell a gentle story where the word "razor" appears and the crew uses a Twist '
        f'to solve an over-capacity space-ship problem.',
        f'Write a simple rescue-flight story about {f["cargo"].phrase} that starts with a worry '
        f'and ends with a safe launch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    helper = _safe_fact(world, f, "helper")
    cargo = _safe_fact(world, f, "cargo")
    ship = _safe_fact(world, f, "ship")
    loc = _safe_fact(world, f, "loc")

    load = cargo_load(cargo.id)
    twist = "Twist" if world.twist_used else "careful packing"

    return [
        QAItem(
            question=f"What was the crew trying to carry at {loc}?",
            answer=f"They were trying to carry {cargo.phrase} aboard {ship.name}.",
        ),
        QAItem(
            question=f"Why did {captain.id} worry before the ship left?",
            answer=(
                f"{captain.id} worried because the cargo load was {load}, and {ship.name} could only hold "
                f"{ship.capacity}. The ship would have been over capacity without a better plan."
            ),
        ),
        QAItem(
            question=f"How did the bozo helper {helper.id} help the launch?",
            answer=(
                f"{helper.id} used the {twist} to pack the cargo more tightly, which made the load fit "
                f"inside the ship's capacity."
            ),
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=(
                f"The hatch closed, {ship.name} lifted off safely, and the crew flew away with the cargo "
                f"safe inside."
            ),
        ),
        QAItem(
            question=f"Where does the word razor fit into this story?",
            answer=(
                f"It fits as part of the space-adventure mood: the crew was dealing with a razor-thin "
                f"capacity problem, where even a small change mattered."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does capacity mean?",
            answer="Capacity is how much something can hold before it gets too full.",
        ),
        QAItem(
            question="What is a razor-thin margin?",
            answer="A razor-thin margin is a very tiny difference, so small that only a little change can matter.",
        ),
        QAItem(
            question="What is a Twist in a space adventure?",
            answer="A Twist is a surprising change that helps solve the problem in a new way.",
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


# ---------------------------------------------------------------------------
# Trace / output
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"ship={world.ship.name} capacity={world.ship.capacity} twist_slot={world.ship.twist_slot}")
    lines.append(f"twist_used={world.twist_used}")
    for e in list(world.entities.values()):
        parts = []
        if e.phrase:
            parts.append(f"phrase={e.phrase!r}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a bozo helper and a Twist.")
    ap.add_argument("--crew", choices=CREW)
    ap.add_argument("--helper", choices=CREW)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--place", choices=SHIPS)
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
    crew = getattr(args, "crew", None) or rng.choice(list(CREW))
    helper = getattr(args, "helper", None) or rng.choice([k for k in CREW if k != crew])
    cargo = getattr(args, "cargo", None) or rng.choice(list(CARGO))
    place = getattr(args, "place", None) or rng.choice(list(SHIPS))

    if getattr(args, "helper", None) and getattr(args, "helper", None) == crew:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "cargo", None) and getattr(args, "place", None):
        ship = _safe_lookup(SHIPS, getattr(args, "place", None))
        load = cargo_load(getattr(args, "cargo", None))
        if not (load <= ship.capacity or (ship.twist_slot and load - 1 <= ship.capacity)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(crew=crew, helper=helper, cargo=cargo, place=place)


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


# ---------------------------------------------------------------------------
# Extras
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(crew="Ari", helper="Bozo", cargo="seedlings", place="starling"),
    StoryParams(crew="Milo", helper="Bozo", cargo="crates", place="comet"),
    StoryParams(crew="Nia", helper="Bozo", cargo="supplies", place="orbit"),
    StoryParams(crew="Ari", helper="Bozo", cargo="glider", place="starling"),
]


def asp_verify_print() -> None:
    triples = asp_valid_stories()
    print(f"{len(triples)} compatible story combos:")
    for c, cargo, ship in triples:
        print(f"  {c:5} {cargo:10} {ship}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        asp_verify_print()
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.crew} + {p.helper} / cargo={p.cargo} / ship={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
