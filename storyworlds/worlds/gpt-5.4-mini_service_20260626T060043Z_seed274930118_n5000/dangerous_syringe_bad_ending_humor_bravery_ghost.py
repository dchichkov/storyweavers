#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Ghost-Story-style domain about a
dangerous syringe, with bravery, humor, and a bad-ending flavor.

The world is small on purpose:
- a child explores a haunted place
- a dangerous syringe creates real risk
- a ghost adds spooky humor
- bravery means choosing the safe action even when scared
- the ending is a "bad ending" in the sense that the fun is cut short and the
  spooky place stays spooky, but the child stays safe
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
    touched_by: Optional[str] = None
    plural: bool = False
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
    label: str
    spooky: bool = True
    indoors: bool = False
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
class Hazard:
    id: str
    label: str
    phrase: str
    risk: str
    can_poke: bool = True
    can_touch: bool = False
    can_clean: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool = True
    helps_with: set[str] = field(default_factory=set)
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
class Ghost:
    id: str
    label: str
    phrase: str
    jokes: list[str] = field(default_factory=list)
    helps: bool = True
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_gender: str
    ghost_name: str
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


PLACES = {
    "old_house": Place(label="the old house", spooky=True, indoors=True),
    "graveyard_gate": Place(label="the graveyard gate", spooky=True, indoors=False),
    "foggy_shed": Place(label="the foggy shed", spooky=True, indoors=True),
}

GHOSTS = {
    "mop_ghost": Ghost(
        id="mop_ghost",
        label="Mop Ghost",
        phrase="a pale ghost with a broom-handle grin",
        jokes=[
            "I clean up the creep before breakfast!",
            "I was once a stain, but now I'm a complaint.",
            "No poking! I am fragile and dramatic.",
        ],
        helps=True,
    )
}

HAZARDS = {
    "syringe": Hazard(
        id="syringe",
        label="syringe",
        phrase="a dangerous syringe with a tiny sharp needle",
        risk="the needle can poke skin and hurt someone",
        can_poke=True,
        can_touch=False,
        can_clean=False,
    )
}

TOOLS = {
    "tongs": Tool(
        id="tongs",
        label="kitchen tongs",
        phrase="a pair of long kitchen tongs",
        safe=True,
        helps_with={"syringe"},
    ),
    "box": Tool(
        id="box",
        label="a lidded box",
        phrase="a lidded box for keeping the dangerous thing away",
        safe=True,
        helps_with={"syringe"},
    ),
}

BOY_NAMES = ["Leo", "Finn", "Milo", "Noah", "Ben", "Theo"]
GIRL_NAMES = ["Mina", "Tia", "June", "Lila", "Zoe", "Nora"]
TRAITS = ["curious", "brave", "silly", "careful", "stubborn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a dangerous syringe.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--ghost", choices=GHOSTS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("old_house", "syringe"), ("graveyard_gate", "syringe"), ("foggy_shed", "syringe")]


def explain_rejection(place: str) -> str:
    return f"(No story: {place} does not fit the haunted syringe premise.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    ghost = getattr(args, "ghost", None) or "mop_ghost"
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_gender=parent, ghost_name=ghost)


def danger_level(world: World) -> float:
    haz = world.facts.get("hazard")
    if not haz:
        return 0.0
    return 1.0 if haz.id == "syringe" else 0.0


def safe_choice(tool: Tool, hazard: Hazard) -> bool:
    return hazard.id in tool.helps_with and tool.safe


ASP_RULES = r"""
hazard(syringe).
place(old_house).
place(graveyard_gate).
place(foggy_shed).

unsafe(H) :- hazard(H).
helpful(T,H) :- tool(T), hazard(H), helps(T,H).
safe_choice(T,H) :- helpful(T,H).

#show hazard/1.
#show place/1.
#show unsafe/1.
#show safe_choice/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_choice/2."))
    asp_pairs = set(asp.atoms(model, "safe_choice"))
    py_pairs = {(tid, hid) for tid, t in TOOLS.items() for hid in HAZARDS if safe_choice(t, _safe_lookup(HAZARDS, hid))}
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python gate ({len(py_pairs)} safe choices).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(asp_pairs - py_pairs))
    print("only in Python:", sorted(py_pairs - asp_pairs))
    return 1


def narrate_setup(world: World, child: Entity, parent: Entity, ghost: Ghost, hazard: Hazard) -> None:
    world.say(f"{child.id} lived near {world.place.label}, where the air always felt a little spooky.")
    world.say(f"One night, {child.id} met {ghost.label}, {ghost.phrase}, and heard a wobbly laugh in the dark.")
    world.say(f"Then {child.id} saw {hazard.phrase} tucked near the boards.")
    world.say(f"{child.id} knew right away that the {hazard.label} was dangerous, because {hazard.risk}.")


def narrate_conflict(world: World, child: Entity, parent: Entity, ghost: Ghost, hazard: Hazard) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(f"{child.id} wanted to peek closer, but the little sharp needle made {child.pronoun('object')} freeze.")
    world.say(f'"No poking," {ghost.label} whispered. "I tried poking a pinecone once and it got even pointier."')
    world.say(f"{child.id} called for {child.pronoun('possessive')} {parent.pronoun('possessive') if False else world.facts["parent_label"]} and took a brave step back.")


def narrate_bravery(world: World, child: Entity, parent: Entity, ghost: Ghost, tool: Tool, hazard: Hazard) -> None:
    child.memes["bravery"] += 1
    world.say(f"{child.id} did not touch the syringe.")
    world.say(f"Instead, {child.id} used {tool.phrase} to point at it from far away.")
    world.say(f"{world.facts['parent_label'].capitalize()} came quickly, nodded, and used the {tool.label} to move it into {TOOLS['box'].label if tool.id == 'tongs' else 'the safe box'}.")
    world.say(f'{ghost.label} gave a tiny spooky clap. "A brave choice, and not a poke-y choice," {ghost.label} said.')


def narrate_ending(world: World, child: Entity, parent: Entity, ghost: Ghost, hazard: Hazard) -> None:
    world.say(f"The scary corner stayed scary, and nobody wanted to play there anymore.")
    world.say(f"That was the bad part of the night: the fun stopped, and the old place had to be left alone.")
    world.say(f"But {child.id} went home safe, and the dangerous {hazard.label} was locked away where no child could find it.")
    world.say(f"Even {ghost.label} drifted off with a grin, because the bravest thing had already been done.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    parent_type = params.parent_gender
    parent = world.add(Entity(id=parent_type.capitalize(), kind="character", type=parent_type))
    ghost = _safe_lookup(GHOSTS, params.ghost_name)
    hazard = HAZARDS["syringe"]
    tool = TOOLS["tongs"]

    world.facts.update(
        child=child,
        parent=parent,
        parent_label=parent_type,
        ghost=ghost,
        hazard=hazard,
        tool=tool,
    )

    narrate_setup(world, child, parent, ghost, hazard)
    world.para()
    narrate_conflict(world, child, parent, ghost, hazard)
    world.para()
    narrate_bravery(world, child, parent, ghost, tool, hazard)
    world.para()
    narrate_ending(world, child, parent, ghost, hazard)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost story for a young child that includes the words "dangerous" and "syringe".',
        f"Tell a spooky but gentle story where {f['child'].id} finds a dangerous syringe near {world.place.label} and chooses a brave, safe response.",
        "Write a child-friendly haunted story with a funny ghost, a real danger, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent_label = _safe_fact(world, f, "parent_label")
    ghost: Ghost = _safe_fact(world, f, "ghost")
    hazard: Hazard = _safe_fact(world, f, "hazard")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {child.id} find near {world.place.label}?",
            answer=f"{child.id} found {hazard.phrase}. It was dangerous because {hazard.risk}.",
        ),
        QAItem(
            question=f"Who made the story spooky and funny?",
            answer=f"{ghost.label} did. {ghost.label} was a ghost who told a silly line while the danger was being handled.",
        ),
        QAItem(
            question=f"How did {child.id} show bravery?",
            answer=f"{child.id} showed bravery by stepping back, not touching the syringe, and helping grown-ups deal with it safely using {tool.phrase}.",
        ),
        QAItem(
            question=f"Why is the ending a bad ending?",
            answer=f"It is a bad ending for fun because the spooky place had to be left alone and the playtime stopped, even though {child.id} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a syringe?",
            answer="A syringe is a tool that can hold or move liquid, and its sharp needle can poke skin, so it must be handled by careful grown-ups.",
        ),
        QAItem(
            question="Why should children stay away from a dangerous syringe?",
            answer="Children should stay away because the needle can hurt them and can spread germs if it is not handled safely.",
        ),
        QAItem(
            question="What does bravery mean in a scary moment?",
            answer="Bravery means doing the safe thing even when you feel scared, like stepping back and getting help.",
        ),
        QAItem(
            question="Why can ghosts be funny in stories?",
            answer="Ghosts can be funny when they say silly things or act harmlessly, which makes a spooky story less scary for children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", child_name="Mina", child_gender="girl", parent_gender="mother", ghost_name="mop_ghost"),
    StoryParams(place="graveyard_gate", child_name="Leo", child_gender="boy", parent_gender="father", ghost_name="mop_ghost"),
    StoryParams(place="foggy_shed", child_name="Nora", child_gender="girl", parent_gender="father", ghost_name="mop_ghost"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_choice/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_choice/2."))
        print(sorted(set(asp.atoms(model, "safe_choice"))))
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
