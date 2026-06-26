#!/usr/bin/env python3
"""
Burp Reconciliation Nursery Rhyme
=================================

A small storyworld where a fizzy burp creates a tiny wobble in a nursery-rhyme
playtime, and a warm reconciliation brings the scene back to calm.

The world model tracks:
- physical state: who has a fizzy drink, who burped, what got spilled, where
- emotional state: delight, embarrassment, hurt, forgiveness, togetherness

The story stays child-facing and rhymed in spirit, with a clear beginning,
middle turn, and ending image proving the change.
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
# Core entities
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
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
class Place:
    name: str
    indoors: bool = True
    cozy: str = "a cozy little room"
    supports: set[str] = field(default_factory=set)
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
class Treat:
    label: str
    phrase: str
    fizzy: bool = False
    can_spill: bool = False
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
class Comfort:
    label: str
    phrase: str
    restores: str
    fits: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nursery": Place(
        name="the nursery",
        indoors=True,
        cozy="the nursery with its soft rug and low little table",
        supports={"tea", "songs", "snacks"},
    ),
    "playroom": Place(
        name="the playroom",
        indoors=True,
        cozy="the playroom with its bright blocks and painted chair",
        supports={"tea", "songs", "snacks"},
    ),
}

TASTES = {
    "juice": Treat(
        label="sparkling juice",
        phrase="a glass of sparkling juice",
        fizzy=True,
        can_spill=True,
    ),
    "soda": Treat(
        label="bubble soda",
        phrase="a tiny cup of bubble soda",
        fizzy=True,
        can_spill=True,
    ),
    "milk": Treat(
        label="warm milk",
        phrase="a cup of warm milk",
        fizzy=False,
        can_spill=True,
    ),
    "water": Treat(
        label="water",
        phrase="a little cup of water",
        fizzy=False,
        can_spill=True,
    ),
}

COMFORTS = {
    "hug": Comfort(
        label="a hug",
        phrase="a gentle hug",
        restores="together",
        fits={"hurt", "embarrassed"},
    ),
    "apology": Comfort(
        label="an apology",
        phrase="a soft apology",
        restores="forgiven",
        fits={"hurt", "embarrassed"},
    ),
    "napkin": Comfort(
        label="a napkin",
        phrase="a clean napkin and a wipe",
        restores="tidy",
        fits={"spill"},
    ),
    "song": Comfort(
        label="a song",
        phrase="a cheerful little song",
        restores="bright",
        fits={"hurt", "embarrassed", "together"},
    ),
}

NAMES = ["Mia", "Leo", "Nina", "Ollie", "Ada", "Ben", "Ruby", "Tom"]
PARENT_NAMES = ["Mum", "Dad", "Mama", "Papa"]
TRAITS = ["little", "bright", "cheery", "sleepy", "playful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_name: str
    parent_name: str
    child_type: str
    parent_type: str
    trait: str
    treat: str
    comfort: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def _mood(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def predict_burp(world: World, child: Entity, treat: Treat) -> dict:
    sim = world.copy()
    _eat_and_burp(sim, sim.get(child.id), treat, narrate=False)
    child2 = sim.get(child.id)
    parent2 = sim.get(world.facts["parent"].id)
    return {
        "spill": child2.meters.get("spill", 0.0) > 0,
        "hurt": child2.memes.get("embarrassed", 0.0) > 0 and parent2.memes.get("worry", 0.0) > 0,
    }


def _eat_and_burp(world: World, child: Entity, treat: Treat, narrate: bool = True) -> None:
    _meter(child, "full", 1)
    if treat.fizzy:
        _meter(child, "burp", 1)
        _mood(child, "embarrassed", 1)
        if narrate:
            world.say(f"{child.id} took a sip, and out popped a burp so round and loud.")
    else:
        if narrate:
            world.say(f"{child.id} sipped the drink and smiled, as neat as a cloud.")


def _spill(world: World, child: Entity, treat: Treat, narrate: bool = True) -> None:
    if not treat.can_spill:
        return
    if child.meters.get("burp", 0.0) >= 1:
        _meter(child, "spill", 1)
        if narrate:
            world.say(f"The cup tipped and dripped a stripe on the table beside.")


def _reconcile(world: World, child: Entity, parent: Entity, comfort: Comfort, narrate: bool = True) -> None:
    if comfort.label == "a napkin":
        child.meters["spill"] = 0
    if comfort.label == "a hug":
        _mood(child, "hurt", -1)
        _mood(parent, "worry", -1)
        _mood(child, "together", 1)
        _mood(parent, "together", 1)
    if comfort.label == "an apology":
        _mood(child, "embarrassed", -1)
        _mood(parent, "forgiveness", 1)
    if comfort.label == "a song":
        _mood(child, "bright", 1)
        _mood(parent, "bright", 1)

    child.memes["hurt"] = max(0.0, child.memes.get("hurt", 0.0))
    parent.memes["worry"] = max(0.0, parent.memes.get("worry", 0.0))
    child.memes["embarrassed"] = max(0.0, child.memes.get("embarrassed", 0.0))

    if narrate:
        world.say(f"{parent.id} smiled, and {comfort.phrase} made the wobble go away.")
        world.say(f"Then the two of them were merry again, side by side, in the light of the day.")


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    treat = _safe_lookup(TASTES, params.treat)
    comfort = _safe_lookup(COMFORTS, params.comfort)
    world = World(place)

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_type))

    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["treat"] = treat
    world.facts["comfort"] = comfort
    world.facts["place"] = place

    # Act 1
    world.say(f"In {place.name}, where the lanterns glowed and the floorboards shone,")
    world.say(f"lived {child.id}, a {params.trait} {params.child_type}, with a smile like morning song.")
    world.say(f"{parent.id} brought {treat.phrase}, bright and small, for a snack by the side of the wall.")

    # Act 2
    world.para()
    world.say(f"{child.id} took a sip in a happy hush; the bubbles began to prance and rush.")
    _eat_and_burp(world, child, treat)
    _spill(world, child, treat)
    if child.meters.get("burp", 0.0) >= 1:
        _mood(parent, "worry", 1)
        _mood(child, "embarrassed", 1)
        world.say(f"{parent.id} said, \"Oh dear, oh my, let us mend this little lullaby.\"")
        world.say(f"{child.id} looked down at the table, red as a berry in a pie.")

    # Act 3
    world.para()
    if child.meters.get("spill", 0.0) > 0:
        world.say(f"{parent.id} handed over {comfort.phrase}, light and kind.")
    _reconcile(world, child, parent, comfort)
    world.say(f"{child.id} laughed again, and the room felt snug and sweet.")
    world.say(f"On the little chair, the clean cup sat, and both were glad to meet.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for treat in TASTES:
            for comfort in COMFORTS:
                if _safe_lookup(TASTES, treat).fizzy and _safe_lookup(COMFORTS, comfort).label in {"a hug", "an apology", "a song", "a napkin"}:
                    combos.append((place, treat, comfort, "any"))
    return combos


ASP_RULES = r"""
% Facts from registries
place(P) :- setting(P).
fizzy(T) :- treat(T), fizzy_treat(T).
spillable(T) :- treat(T), can_spill(T).
comfort(C) :- comfort_item(C).

% A burp is a likely turn when the treat is fizzy.
burp_turn(T) :- fizzy_treat(T).

% A reconciliation is reasonable when some comforting act can answer the turn.
reconciles(C) :- comfort_item(C).

valid_story(P, T, C) :- place(P), treat(T), comfort(C), burp_turn(T), reconciles(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for s in sorted(place.supports):
            lines.append(asp.fact("supports", pid, s))
    for tid, treat in TASTES.items():
        lines.append(asp.fact("treat", tid))
        if treat.fizzy:
            lines.append(asp.fact("fizzy_treat", tid))
        if treat.can_spill:
            lines.append(asp.fact("can_spill", tid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort_item", cid))
        for f in sorted(c.fits):
            lines.append(asp.fact("fits", cid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo = set(asp.atoms(model, "valid_story"))
    mapped = {(p, t, c, "any") for (p, t, c) in clingo}
    if mapped == py:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - mapped:
        print("  only in python:", sorted(py - mapped))
    if mapped - py:
        print("  only in ASP:", sorted(mapped - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    treat = _safe_fact(world, f, "treat")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short nursery-rhyme style story about {child.id}, a burp, and a kind reconciliation.',
        f"Tell a gentle story set in {place.name} where {child.id} drinks {treat.phrase} and then makes up with {f['parent'].id}.",
        f'Write a child-friendly rhyme that includes the word "burp" and ends with everyone feeling friendly again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    t = _safe_fact(world, world.facts, "treat")
    com = _safe_fact(world, world.facts, "comfort")
    return [
        QAItem(
            question=f"What happened after {c.id} drank the fizzy treat?",
            answer=f"{c.id} let out a burp, felt embarrassed, and a little spill followed on the table.",
        ),
        QAItem(
            question=f"Why did {p.id} worry?",
            answer=f"{p.id} worried because the burp made the moment messy and awkward, and {c.id} felt shy about it.",
        ),
        QAItem(
            question=f"How did they reconcile?",
            answer=f"They used {com.phrase}, and that gentle act helped them feel close and calm again.",
        ),
        QAItem(
            question=f"What was the drink called?",
            answer=f"The drink was {t.phrase}, a fizzy little treat that could bubble up into a burp.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burp?",
            answer="A burp is a little bubble of air that comes back up from the tummy and out of the mouth.",
        ),
        QAItem(
            question="Why can fizzy drinks make burps happen?",
            answer="Fizzy drinks hold tiny bubbles of gas, and those bubbles can pop up and make a burp when you drink them.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a small hurt or quarrel so people feel friendly again.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="nursery", child_name="Mia", parent_name="Mum", child_type="girl", parent_type="mother", trait="cheery", treat="juice", comfort="hug"),
    StoryParams(place="playroom", child_name="Leo", parent_name="Dad", child_type="boy", parent_type="father", trait="playful", treat="soda", comfort="apology"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Burp reconciliation nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    treat = getattr(args, "treat", None) or rng.choice(list(TASTES))
    if not _safe_lookup(TASTES, treat).fizzy:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    parent_type = getattr(args, "parent_type", None) or ("mother" if child_type == "girl" else "father")
    child_name = getattr(args, "child_name", None) or rng.choice(NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        child_name=child_name,
        parent_name=parent_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
        treat=treat,
        comfort=comfort,
    )


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = asp.atoms(model, "valid_story")
        print(f"{len(stories)} compatible story shapes:")
        for p, t, c in sorted(set(stories)):
            print(f"  {p:8} {t:8} {c}")
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
