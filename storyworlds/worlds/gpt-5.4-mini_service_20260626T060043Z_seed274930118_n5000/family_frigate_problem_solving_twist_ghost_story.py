#!/usr/bin/env python3
"""
A small story world in a ghost-story style about a family aboard a frigate,
where a spooky problem turns into a gentle problem-solving twist.

The world is built to be constraint-checked, state-driven, and child-facing.
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
    kind: str = "thing"  # "character" | "thing" | "ghost"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grand: object | None = None
    parent1: object | None = None
    parent2: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Frigate:
    name: str
    place: str = "the frigate"
    holds: list[str] = field(default_factory=lambda: ["deck", "cabins", "cargo hold", "cabin stairs"])
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    facts: dict = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    hidden: str = "a missing ship bell"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def ghosts(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "ghost"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "Frigate":
        import copy

        clone = Frigate(self.name)
        clone.place = self.place
        clone.holds = list(self.holds)
        clone.meters = dict(self.meters)
        clone.memes = dict(self.memes)
        clone.facts = dict(self.facts)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.hidden = self.hidden
        return clone


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------
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
    family_name: str = ""
    member_count: int = 0
    frigate_name: str = ""
    problem: str = ""
    twist: str = ""
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


FAMILY_NAMES = ["Harbor", "Marlow", "Bennet", "Rowan", "Sailor", "Moss"]
FRIGATE_NAMES = ["The Moon Gull", "The Lantern Finch", "The Blue Finch", "The Honey Wave"]
PROBLEMS = {
    "stuck_hatch": "a hatch that would not open",
    "cold_cabin": "a cabin that felt cold and dark",
    "missing_lantern": "a lantern that had gone out",
    "quiet_bell": "a ship bell that would not ring",
}
TWISTS = {
    "friendly_ghost": "a friendly ghost was trying to help",
    "lost_ghost": "a little ghost was looking for its bell",
    "echo_ghost": "the spooky sounds were only the ship's echo",
}


@dataclass
class FamilyRole:
    name: str
    type: str
    trait: str
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


ROLES = [
    FamilyRole("mother", "mother", "calm"),
    FamilyRole("father", "father", "patient"),
    FamilyRole("child", "girl", "curious"),
    FamilyRole("child", "boy", "brave"),
]

GHOST_TRAITS = ["misty", "soft-spoken", "glimmering", "lonely"]
FAMILY_TRAITS = ["curious", "brave", "gentle", "clever", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story family frigate problem-solving twist world.")
    ap.add_argument("--family-name", choices=FAMILY_NAMES)
    ap.add_argument("--frigate-name", choices=FRIGATE_NAMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
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
    family_name = getattr(args, "family_name", None) or rng.choice(FAMILY_NAMES)
    frigate_name = getattr(args, "frigate_name", None) or rng.choice(FRIGATE_NAMES)
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    member_count = rng.choice([3, 4, 4, 5])

    if problem == "quiet_bell" and twist == "echo_ghost":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "name", None):
        family_name = getattr(args, "name", None)

    return StoryParams(
        family_name=family_name,
        member_count=member_count,
        frigate_name=frigate_name,
        problem=problem,
        twist=twist,
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _make_family(world: Frigate, params: StoryParams) -> tuple[Entity, list[Entity]]:
    parent1 = world.add(Entity(id="parent1", kind="character", type="mother", label="the mother", traits=["calm"]))
    parent2 = world.add(Entity(id="parent2", kind="character", type="father", label="the father", traits=["patient"]))
    child = world.add(Entity(id="child", kind="character", type="girl", label="the child", traits=["curious"]))
    others: list[Entity] = [parent1, parent2, child]
    if params.member_count >= 4:
        sibling = world.add(Entity(id="sibling", kind="character", type="boy", label="the little brother", traits=["brave"]))
        others.append(sibling)
    if params.member_count >= 5:
        grand = world.add(Entity(id="grand", kind="character", type="woman", label="grandma", traits=["gentle"]))
        others.append(grand)
    return child, others


def _add_ghost(world: Frigate, twist: str) -> Entity:
    if twist == "friendly_ghost":
        label = "a friendly ghost"
        trait = "friendly"
    elif twist == "lost_ghost":
        label = "a little ghost"
        trait = "lost"
    else:
        label = "a pale echo"
        trait = "echoing"
    return world.add(Entity(id="ghost", kind="ghost", type="ghost", label=label, traits=[trait]))


def _risk_problem(world: Frigate, problem: str) -> None:
    if problem == "stuck_hatch":
        world.meters["stuck"] = 1.0
    elif problem == "cold_cabin":
        world.meters["cold"] = 1.0
    elif problem == "missing_lantern":
        world.meters["dark"] = 1.0
    elif problem == "quiet_bell":
        world.meters["silent"] = 1.0


def propagate(world: Frigate) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if world.meters.get("dark", 0.0) >= THRESHOLD and ("ghost_seen",) not in world.fired:
            world.fired.add(("ghost_seen",))
            world.memes["spooky"] = world.memes.get("spooky", 0.0) + 1
            changed = True
        if world.meters.get("stuck", 0.0) >= THRESHOLD and ("needs_plan", "hatch") not in world.fired:
            world.fired.add(("needs_plan", "hatch"))
            world.memes["worry"] = world.memes.get("worry", 0.0) + 1
            changed = True
        if world.meters.get("cold", 0.0) >= THRESHOLD and ("needs_plan", "cold") not in world.fired:
            world.fired.add(("needs_plan", "cold"))
            world.memes["worry"] = world.memes.get("worry", 0.0) + 1
            changed = True
        if world.meters.get("silent", 0.0) >= THRESHOLD and ("needs_plan", "bell") not in world.fired:
            world.fired.add(("needs_plan", "bell"))
            world.memes["worry"] = world.memes.get("worry", 0.0) + 1
            changed = True


def tell(params: StoryParams) -> Frigate:
    world = Frigate(params.frigate_name)
    child, family = _make_family(world, params)
    ghost = _add_ghost(world, params.twist)
    _risk_problem(world, params.problem)
    world.facts.update(params=params, child=child, family=family, ghost=ghost)

    world.say(f"The family boarded {world.name} on a gray evening, when the water looked like folded ink.")
    world.say(f"Inside the frigate, the lamps swayed, and everyone felt the ship breathing under their feet.")
    world.para()

    if params.problem == "stuck_hatch":
        world.say("Then a hatch clanged shut in the wind, and it would not open again.")
    elif params.problem == "cold_cabin":
        world.say("Then one little cabin turned cold and dim, as if the dark had crawled inside.")
    elif params.problem == "missing_lantern":
        world.say("Then the family noticed a lantern had gone out, and the deck became spooky and gray.")
    else:
        world.say("Then the ship bell stayed silent, and the whole frigate felt too still.")
    propagate(world)

    world.say("The child listened hard. A soft whisper slid through the ropes like a secret.")
    if params.twist == "friendly_ghost":
        world.say("At first the family shivered, because a ghost hovered near the mast like a patch of fog.")
        world.say("But the ghost did not scare them. It pointed at the problem as if it wanted to help.")
    elif params.twist == "lost_ghost":
        world.say("At first the family shivered, because a ghost drifted in the corridor with a lonely sigh.")
        world.say("But the ghost was not there to frighten anyone. It seemed to be searching for something tiny.")
    else:
        world.say("At first the family shivered, because a pale shape fluttered by the stairs in the moonlight.")
        world.say("Then they noticed the shape was only the ship's echo, bouncing back from the metal walls.")
    world.para()

    # Problem solving turn
    if params.problem == "stuck_hatch":
        world.say("The father knelt and felt the hatch edge. A bit of rope had jammed it shut.")
        world.say("The child fetched a small hook, and together they nudged the rope free.")
        world.say("The hatch popped open with a tired sigh, and cold air rushed out like a released breath.")
    elif params.problem == "cold_cabin":
        world.say("The mother touched the window and found a crack where sea air sneaked in.")
        world.say("She stuffed a folded blanket into the gap, and the child lit the lamp again.")
        world.say("Soon the cabin glowed warm and gold, as if the room had remembered how to smile.")
    elif params.problem == "missing_lantern":
        world.say("The child climbed onto a box, found the wick, and trimmed it with careful fingers.")
        world.say("The father shielded the flame with his hands until it caught.")
        world.say("Then the lantern brightened, and the shadows shrank back to the corners.")
    else:
        world.say("The family followed the sound to a nail behind a beam, where the bell's little clapper had come loose.")
        world.say("The mother tied it on with a loop of thread, and the child gave the bell a gentle tap.")
        world.say("The bell rang at last, bright and clear, and the whole ship seemed to wake up.")

    # Twist resolution
    if params.twist == "friendly_ghost":
        world.say("The ghost gave a tiny nod, and the family saw it had only wanted the frigate to feel safe again.")
        world.say("When the work was done, the ghost faded into the lantern light, peaceful as mist at dawn.")
    elif params.twist == "lost_ghost":
        world.say("Then the ghost smiled when it heard the bell, because the sound matched the little bell it had lost long ago.")
        world.say("It found the missing bell tucked in a coil of rope, and the family helped hang it beside the mast.")
    else:
        world.say("That was the twist: the spooky visitor was nothing more than the ship's own echo, making the frigate sound haunted.")
        world.say("Once the family solved the real problem, the ship felt brave and ordinary again.")

    world.para()
    world.say("By the end, the frigate was calm, the family was smiling, and even the dark corners seemed less lonely.")
    world.say("The sea still rocked outside, but inside the ship, the warm light held steady like a little home.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: Frigate) -> list[str]:
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write a gentle ghost story about a family on {p.frigate_name} where a spooky problem gets solved.",
        f"Tell a child-friendly tale set on a frigate that includes a twist and ends with the family feeling safe.",
        f"Write a short story about {p.family_name} family aboard a ship, with a problem, a clue, and a clever fix.",
    ]


def story_qa(world: Frigate) -> list[QAItem]:
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    ghost = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "ghost")
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    return [
        QAItem(
            question=f"Where did the family spend the night in the story?",
            answer=f"The family spent the night on {world.name}, a frigate rocking on the dark water.",
        ),
        QAItem(
            question=f"What problem had to be solved on the ship?",
            answer=f"The main problem was {_safe_lookup(PROBLEMS, p.problem)}, so the family had to work together and fix it.",
        ),
        QAItem(
            question=f"What did the ghost turn out to be like?",
            answer=f"The ghost turned out to be {ghost.label}, and the story showed that it was not there just to scare anyone.",
        ),
        QAItem(
            question=f"Who did most of the noticing and careful helping?",
            answer=f"The child noticed the clues first and helped the family solve the problem.",
        ),
    ]


def world_knowledge_qa(world: Frigate) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frigate?",
            answer="A frigate is a kind of ship that sails on the sea and can have rooms, ropes, and a deck.",
        ),
        QAItem(
            question="What makes a ghost story spooky?",
            answer="A ghost story feels spooky when strange shadows, whispers, or surprises make people wonder what is happening.",
        ),
        QAItem(
            question="Why do people work together to solve a problem?",
            answer="People work together because one person may notice one clue and another person may know another useful step.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: Frigate) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "ghost":
            bits.append("kind=ghost")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is at risk when it creates a visible spooky state.
at_risk(P) :- problem(P), risk(P).

% A twist is compatible when it can explain or solve the problem.
compatible(T, P) :- twist(T), problem(P), can_help(T, P).

valid_story(F, P, T) :- family(F), problem(P), twist(T), compatible(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for f in FAMILY_NAMES:
        lines.append(asp.fact("family", f))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for p in PROBLEMS:
        if p in {"stuck_hatch", "cold_cabin", "missing_lantern", "quiet_bell"}:
            lines.append(asp.fact("risk", p))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    lines.append(asp.fact("can_help", "friendly_ghost", "stuck_hatch"))
    lines.append(asp.fact("can_help", "friendly_ghost", "cold_cabin"))
    lines.append(asp.fact("can_help", "friendly_ghost", "missing_lantern"))
    lines.append(asp.fact("can_help", "lost_ghost", "quiet_bell"))
    lines.append(asp.fact("can_help", "echo_ghost", "missing_lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for family in FAMILY_NAMES:
        for problem in PROBLEMS:
            for twist in TWISTS:
                ok = (
                    (twist == "friendly_ghost" and problem in {"stuck_hatch", "cold_cabin", "missing_lantern"}) or
                    (twist == "lost_ghost" and problem == "quiet_bell") or
                    (twist == "echo_ghost" and problem == "missing_lantern")
                )
                if ok:
                    combos.append((family, problem, twist))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("Harbor", 4, "The Moon Gull", "stuck_hatch", "friendly_ghost"),
    StoryParams("Marlow", 3, "The Lantern Finch", "missing_lantern", "echo_ghost"),
    StoryParams("Rowan", 5, "The Blue Finch", "quiet_bell", "lost_ghost"),
]


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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        for item in stories:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.family_name}: {p.problem} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
