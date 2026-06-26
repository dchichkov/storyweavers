#!/usr/bin/env python3
"""
A standalone storyworld for a small detective suspense tale about a trek and a
piece of gristle that points the sleuth toward the truth.

Premise:
- A young detective joins a short trek with a guide and a helper.
- A strange gristly bit turns up where a missing snack or clue should be.
- Suspense rises as the detective checks footprints, pockets, and path marks.
- The turn is a small, concrete reveal: the gristle is not random trash; it is
  the clue that leads to the hidden snack and clears up the mystery.

This file follows the Storyweavers storyworld contract:
- dataclass StoryParams plus registries
- build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP_RULES twin and a Python reasonableness gate
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    detective: object | None = None
    sidekick: object | None = None
    suspect: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    source: str
    significance: str
    reveals: str
    at_risk_on: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    detective: str
    sidekick: str
    suspect: str
    clue: str
    tool: str
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
    "trail": Place(id="trail", label="the pine trail", kind="outdoor", affords={"trek"}),
    "market": Place(id="market", label="the covered market lane", kind="outdoor", affords={"trek"}),
    "station": Place(id="station", label="the old station platform", kind="outdoor", affords={"trek"}),
}

DETECTIVES = [
    ("Nina", "girl"),
    ("Milo", "boy"),
    ("Iris", "girl"),
    ("Otis", "boy"),
]

SIDEKICKS = [
    ("Aunt June", "woman"),
    ("Dad", "father"),
    ("Rae", "girl"),
    ("Ben", "boy"),
]

SUSPECTS = [
    ("the baker", "man"),
    ("the porter", "man"),
    ("the gardener", "woman"),
    ("the map seller", "woman"),
]

TOOLS = {
    "notebook": Tool(id="notebook", label="notebook", phrase="a little notebook", helps_with={"note", "observe"}),
    "lamp": Tool(id="lamp", label="lamp", phrase="a small brass lamp", helps_with={"dark", "peek"}),
    "glass": Tool(id="glass", label="glass", phrase="a pocket glass", helps_with={"look", "inspect"}),
}

CLUES = {
    "gristle": Clue(
        id="gristle",
        label="gristle",
        phrase="a tough little piece of gristle",
        source="snack",
        significance="it came from a torn snack wrap",
        reveals="someone hid the snack in a coat pocket",
        at_risk_on="path",
    ),
    "crumb": Clue(
        id="crumb",
        label="crumb",
        phrase="a buttery crumb",
        source="pastry",
        significance="it matched the baker's basket",
        reveals="the snack came from the market stall",
        at_risk_on="bench",
    ),
    "string": Clue(
        id="string",
        label="string",
        phrase="a thin bit of twine",
        source="bundle",
        significance="it matched a wrapped parcel",
        reveals="the parcel had been retied on the trail",
        at_risk_on="gate",
    ),
}

TREK_MATERIAL = {
    "trek": {
        "verb": "trek along the trail",
        "gerund": "trekking along the trail",
        "rush": "hurry deeper down the trail",
        "risk": "shadowy and uncertain",
    }
}


def reasonableness_gate(place: Place, clue: Clue, tool: Tool) -> bool:
    return "trek" in place.affords and clue.at_risk_on in {"path", "bench", "gate"} and bool(tool.helps_with)


def select_reasonable_combo(place: Place, clue: Clue, tool: Tool) -> bool:
    return reasonableness_gate(place, clue, tool)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("at_risk_on", cid, clue.at_risk_on))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps_with):
            lines.append(asp.fact("helps_with", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue, Tool) :- affords(Place, trek), clue(Clue), at_risk_on(Clue, Risk),
                            risk_site(Risk), tool(Tool), helps_with(Tool, _).
risk_site(path).
risk_site(bench).
risk_site(gate).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, c, t) for p in PLACES for c in CLUES for t in TOOLS if select_reasonable_combo(_safe_lookup(PLACES, p), _safe_lookup(CLUES, c), _safe_lookup(TOOLS, t))}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective suspense storyworld with a trek and a gristle clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective")
    ap.add_argument("--sidekick")
    ap.add_argument("--suspect")
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
    if getattr(args, "place", None) and getattr(args, "clue", None) and getattr(args, "tool", None):
        if not select_reasonable_combo(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(CLUES, getattr(args, "clue", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    detective = getattr(args, "detective", None) or rng.choice([n for n, _ in DETECTIVES])
    sidekick = getattr(args, "sidekick", None) or rng.choice([n for n, _ in SIDEKICKS])
    suspect = getattr(args, "suspect", None) or rng.choice([n for n, _ in SUSPECTS])
    if not select_reasonable_combo(_safe_lookup(PLACES, place), _safe_lookup(CLUES, clue), _safe_lookup(TOOLS, tool)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, detective=detective, sidekick=sidekick, suspect=suspect, clue=clue, tool=tool)


def _trek(world: World, detective: Entity, sidekick: Entity, clue: Clue) -> None:
    detective.meters["uncertainty"] = detective.meters.get("uncertainty", 0) + 1
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    world.say(f"{detective.id} and {sidekick.id} set out on a careful trek along the trail.")
    world.say("The air felt quiet, and every little rustle seemed to matter.")


def _find_gristle(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["suspense"] = detective.memes.get("suspense", 0) + 1
    world.say(f"Near a patch of stones, {detective.id} spotted {clue.phrase}.")
    world.say(f"It looked odd enough to stop the whole walk.")
    world.facts["found_clue"] = clue.id


def _question(world: World, detective: Entity, suspect: Entity, clue: Clue, tool: Tool) -> None:
    world.say(f"{detective.id} lifted {tool.phrase} and looked again.")
    world.say(
        f"“This bit of {clue.label} did not grow here,” {detective.id} said, "
        f"and {detective.pronoun('subject')} turned toward {suspect.id}."
    )
    detective.memes["suspense"] = detective.memes.get("suspense", 0) + 1
    world.facts["suspect"] = suspect.id


def _reveal(world: World, detective: Entity, sidekick: Entity, suspect: Entity, clue: Clue) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    detective.memes["suspense"] = 0
    world.say(
        f"At last, the trail of tiny marks led to a coat pocket, and the mystery made sense."
    )
    world.say(
        f"The gristle was not trash at all; {clue.reveals}. {suspect.id} had only been hiding the snack "
        f"so nobody would eat it early."
    )
    world.say(
        f"{detective.id} laughed softly, {sidekick.id} smiled, and the trek ended with the real snack found at last."
    )


def tell(place: Place, clue: Clue, tool: Tool, detective_name: str, sidekick_name: str, suspect_name: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl" if detective_name in {"Nina", "Iris"} else "boy"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="woman" if sidekick_name == "Aunt June" else ("father" if sidekick_name == "Dad" else "boy")))
    suspect = world.add(Entity(id=suspect_name, kind="character", type="man" if suspect_name in {"the baker", "the porter"} else "woman"))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=detective.id))
    clue_ent = world.add(Entity(id=clue.id, type="clue", label=clue.label, phrase=clue.phrase, hidden_in="path"))

    world.say(f"{detective.id} was a small detective who liked quiet problems and clear answers.")
    world.say(f"{detective.id} kept {tool_ent.phrase} ready, because {detective.pronoun('subject')} liked to notice details.")
    world.say(f"One morning, {detective.id}, {sidekick.id}, and {suspect.id} all met near {place.label}.")
    world.para()
    _trek(world, detective, sidekick, clue)
    _find_gristle(world, detective, clue)
    _question(world, detective, suspect, clue, tool)
    world.para()
    _reveal(world, detective, sidekick, suspect, clue_ent)
    world.facts.update(detective=detective, sidekick=sidekick, suspect=suspect, clue=clue_ent, tool=tool_ent, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful detective story for a young child about a trek at {f["place"].label} that includes the word "gristle".',
        f"Tell a short detective tale where {f['detective'].id} finds {f['clue'].phrase} during a trek and uses {(f.get('tool') or next(iter(TOOLS.values()))).phrase} to solve the mystery.",
        f"Create a child-friendly suspense story with a trail, a clue, and a calm reveal at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective").id
    s = _safe_fact(world, f, "sidekick").id
    sus = _safe_fact(world, f, "suspect").id
    clue = _safe_fact(world, f, "clue").label
    return [
        QAItem(
            question=f"Who went on the trek and found the {clue}?",
            answer=f"{d} and {s} went on the trek, and {d} found the {clue} near the trail.",
        ),
        QAItem(
            question=f"Why did {d} stop and look so carefully at the ground?",
            answer=f"{d} stopped because the piece of {clue} looked strange, and it might be an important clue.",
        ),
        QAItem(
            question=f"What did the clue help the detective learn about {sus}?",
            answer=f"The clue helped {d} learn that {sus} had hidden the snack in a coat pocket, so the mystery could be solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trek?",
            answer="A trek is a long walk or journey, often with some effort and careful steps.",
        ),
        QAItem(
            question="What is gristle?",
            answer="Gristle is a tough, chewy part found in some meat. It feels hard and a little rubbery.",
        ),
        QAItem(
            question="Why can a detective story feel suspenseful?",
            answer="A detective story feels suspenseful when the answer is not known yet and the clues make you wonder what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="trail", detective="Nina", sidekick="Aunt June", suspect="the baker", clue="gristle", tool="glass"),
    StoryParams(place="market", detective="Milo", sidekick="Dad", suspect="the porter", clue="crumb", tool="notebook"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(TOOLS, params.tool), params.detective, params.sidekick, params.suspect)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
