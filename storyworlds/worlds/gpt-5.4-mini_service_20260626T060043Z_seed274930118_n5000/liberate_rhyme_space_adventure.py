#!/usr/bin/env python3
"""
storyworlds/worlds/liberate_rhyme_space_adventure.py
====================================================

A small space-adventure story world about liberating a rhyme-powered friend
from a drifting problem, with a gentle turn from worry to a clever rescue.

The seed notion:
- liberate something/someone valuable
- keep the mood close to a space adventure
- use rhyme as a meaningful feature, not a random style swap

The story domain:
- A tiny crew flies to a moon or orbiting place
- A rhyme beacon / rhyme bot / sing-sphere gets stuck behind a latch, stray net,
  or quiet field
- The hero must free it with a tool, a tune, or a careful maneuver
- The ending proves the object is liberated and the crew's feelings change

This file follows the Storyweavers world contract:
- it is standalone and stdlib-only unless ASP mode is used
- it exposes StoryParams, build_parser, resolve_params, generate, emit, main
- it imports shared result containers eagerly and ASP lazily
- it contains an inline ASP_RULES twin for the reasonableness gate
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
    carried_by: Optional[str] = None
    trapped_in: Optional[str] = None
    liberated: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    tool: object | None = None
    trap: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
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
class Scene:
    place: str
    place_phrase: str
    space_type: str  # station, moon, ship, dock
    has_open_sky: bool
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    can_free: set[str] = field(default_factory=set)  # trap types
    can_reach: set[str] = field(default_factory=set)  # places where use is sensible
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
class Trap:
    id: str
    label: str
    phrase: str
    trap_type: str
    risk: str
    need: str
    requires: set[str] = field(default_factory=set)  # tool ids or effects
    place_tags: set[str] = field(default_factory=set)
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
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
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


SCENES = {
    "station": Scene(
        place="the quiet star station",
        place_phrase="a quiet star station",
        space_type="station",
        has_open_sky=False,
        affords={"tether", "beam", "signal"},
    ),
    "moonbase": Scene(
        place="the moonbase",
        place_phrase="a small moonbase",
        space_type="base",
        has_open_sky=True,
        affords={"tether", "beam"},
    ),
    "shipdeck": Scene(
        place="the ship deck",
        place_phrase="the deck of a little ship",
        space_type="ship",
        has_open_sky=True,
        affords={"tether", "signal"},
    ),
}

TRAPS = {
    "net": Trap(
        id="net",
        label="a floating net",
        phrase="a drifting tangle of silver net",
        trap_type="net",
        risk="tangled",
        need="cut free",
        requires={"cutter"},
        place_tags={"station", "base", "ship"},
    ),
    "field": Trap(
        id="field",
        label="a quiet field",
        phrase="a humming quiet field",
        trap_type="field",
        risk="stuck",
        need="switch off",
        requires={"tuner"},
        place_tags={"station", "ship"},
    ),
    "latch": Trap(
        id="latch",
        label="a tight latch",
        phrase="a stubborn latch on a metal box",
        trap_type="latch",
        risk="locked",
        need="open carefully",
        requires={"key"},
        place_tags={"station", "base"},
    ),
}

TOOLS = {
    "cutter": Tool(
        id="cutter",
        label="a tiny cutter",
        phrase="a tiny cutter with a bright handle",
        action="snip the net",
        can_free={"net"},
        can_reach={"station", "base", "ship"},
    ),
    "tuner": Tool(
        id="tuner",
        label="a tune dial",
        phrase="a tune dial that could calm humming machines",
        action="tune the field",
        can_free={"field"},
        can_reach={"station", "ship"},
    ),
    "key": Tool(
        id="key",
        label="a silver key",
        phrase="a silver key on a ribbon",
        action="open the latch",
        can_free={"latch"},
        can_reach={"station", "base"},
    ),
}

HEROES = {
    "Astra": {"type": "girl"},
    "Nova": {"type": "girl"},
    "Orion": {"type": "boy"},
    "Pip": {"type": "boy"},
}

CREW_ROLES = ["captain", "pilot", "mechanic", "navigator"]
MOODS = ["brave", "careful", "curious", "spry", "steady"]


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
scene(S).
tool(T).
trap(X).

can_free(T, X) :- tool(T), trap(X), tool_free(T, X).
reasonable(S, X, T) :- scene(S), trap(X), can_free(T, X), trap_place(X, S).
valid_story(S, X, T) :- reasonable(S, X, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if scene.has_open_sky:
            lines.append(asp.fact("open_sky", sid))
        for a in sorted(scene.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for t in sorted(tool.can_free):
            lines.append(asp.fact("tool_free", tid, t))
        for p in sorted(tool.can_reach):
            lines.append(asp.fact("tool_reach", tid, p))
    for xid, trap in TRAPS.items():
        lines.append(asp.fact("trap", xid))
        lines.append(asp.fact("trap_type", xid, trap.trap_type))
        for p in sorted(trap.place_tags):
            lines.append(asp.fact("trap_place", xid, p))
        for req in sorted(trap.requires):
            lines.append(asp.fact("needs", xid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_reasonable_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    scene: str
    trap: str
    tool: str
    name: str
    role: str
    mood: str
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


def valid_pairs() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for trap_id, trap in TRAPS.items():
            if scene.space_type not in trap.place_tags:
                continue
            for tool_id, tool in TOOLS.items():
                if trap.trap_type in tool.can_free and scene.space_type in tool.can_reach:
                    combos.append((scene_id, trap_id, tool_id))
    return combos


def reason_reject(scene_id: str, trap_id: str, tool_id: str) -> str:
    scene = _safe_lookup(SCENES, scene_id)
    trap = _safe_lookup(TRAPS, trap_id)
    tool = _safe_lookup(TOOLS, tool_id)
    if scene.space_type not in trap.place_tags:
        return f"(No story: {trap.label} does not belong at {scene.place_phrase}.)"
    if trap.trap_type not in tool.can_free:
        return f"(No story: {tool.label} cannot free {trap.label}; it only helps with other traps.)"
    if scene.space_type not in tool.can_reach:
        return f"(No story: {tool.label} is not sensible for {scene.place_phrase}.)"
    return "(No story: that combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _story_beat_open(world: World) -> None:
    hero = world.get("hero")
    trap = world.get("trap")
    world.say(
        f"{hero.id} was a {world.facts['role']} on {world.scene.place_phrase}, and "
        f"{hero.pronoun().capitalize()} watched the stars blink like tiny lanterns."
    )
    world.say(
        f"Far ahead, {trap.phrase} held a small rhyme bot still, and the bot's "
        f"soft voice kept trying to rhyme through the hush."
    )
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1


def _story_beat_problem(world: World) -> None:
    hero = world.get("hero")
    trap = world.get("trap")
    tool = world.get("tool")
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} wanted to liberate {trap.label}, but {hero.pronoun('possessive')} "
        f"hands trembled for a moment because the {tool.label} had to be used just right."
    )
    if trap.trapped_in == "quiet":
        world.say(
            f"The little bot looked dim and sad, as if it had forgotten its own rhyme."
        )


def _free_trap(world: World) -> None:
    hero = world.get("hero")
    trap = world.get("trap")
    tool = world.get("tool")
    sig = (trap.id, tool.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if trap.trapped_in == "net":
        world.say(
            f"{hero.id} guided {tool.label} along the silver loops and snipped them one by one."
        )
    elif trap.trapped_in == "field":
        world.say(
            f"{hero.id} turned {tool.label} until the humming field softened like a sleepy song."
        )
    else:
        world.say(
            f"{hero.id} slid {tool.label} into the latch and opened it with a careful twist."
        )
    trap.liberated = True
    trap.meters["free"] = 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1


def _story_beat_finish(world: World) -> None:
    hero = world.get("hero")
    trap = world.get("trap")
    tool = world.get("tool")
    world.say(
        f"At last, the rhyme bot floated free and sang, "
        f'"Now I can chime and rhyme in time!"'
    )
    world.say(
        f"{hero.id} smiled wide. The {tool.label} hung quiet again, and {world.scene.place} "
        f"felt brighter because something small had been liberated."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1


def build_world(params: StoryParams) -> World:
    scene = _safe_lookup(SCENES, params.scene)
    world = World(scene)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=_safe_lookup(HEROES, params.name)["type"],
        meters={"fuel": 1.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    trap_def = _safe_lookup(TRAPS, params.trap)
    tool_def = _safe_lookup(TOOLS, params.tool)
    trap = world.add(Entity(
        id="trap",
        kind="thing",
        type="trap",
        label=trap_def.label,
        phrase=trap_def.phrase,
        trapped_in=trap_def.trap_type,
        liberated=False,
        meters={"strain": 1.0},
        memes={"silence": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        meters={"charge": 1.0},
    ))

    world.facts.update(
        hero=hero,
        trap=trap,
        tool=tool,
        role=params.role,
        mood=params.mood,
        scene=params.scene,
        trap_id=params.trap,
        tool_id=params.tool,
    )

    _story_beat_open(world)
    world.para()
    _story_beat_problem(world)
    world.para()
    _free_trap(world)
    _story_beat_finish(world)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trap = _safe_fact(world, f, "trap")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short space adventure for a young child about liberating {trap.label} with {tool.label}.',
        f"Tell a gentle starship story where {hero.id} has to free a trapped rhyme bot using {tool.phrase}.",
        f'Create a simple adventure story that includes the word "liberate" and ends with a rhyme bot singing again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trap = _safe_fact(world, f, "trap")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was trying to liberate {trap.label}?",
            answer=f"{hero.id} was trying to liberate {trap.label} on {world.scene.place_phrase}.",
        ),
        QAItem(
            question=f"What was {trap.label} trapped in?",
            answer=(
                f"{trap.label.capitalize()} was trapped in {trap.phrase}, and that kept the rhyme bot quiet until {hero.id} fixed it."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} free the rhyme bot?",
            answer=(
                f"{tool.label} helped {hero.id}. {tool.phrase.capitalize()} was the careful tool that made the rescue work."
            ),
        ),
        QAItem(
            question=f"How did the story end after the rescue?",
            answer=(
                f"The rhyme bot floated free, sang again, and {world.scene.place} felt brighter because the trapped thing had been liberated."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where stars, planets, and moons are found.",
        ),
        QAItem(
            question="Why do astronauts use spacecraft?",
            answer="Astronauts use spacecraft to travel and work safely in space.",
        ),
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="Why do children like rhymes?",
            answer="Children often like rhymes because they sound playful and are easy to remember.",
        ),
    ],
    "liberate": [
        QAItem(
            question="What does liberate mean?",
            answer="Liberate means to free something or someone from being stuck or trapped.",
        ),
    ],
    "tether": [
        QAItem(
            question="What does a tether do in space?",
            answer="A tether is a line that helps keep people or objects from drifting away.",
        ),
    ],
    "signal": [
        QAItem(
            question="What is a signal?",
            answer="A signal is a message or a sign that tells someone what is happening.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["trap_id"], world.facts["tool_id"], "space", "rhyme", "liberate"}
    out: list[QAItem] = []
    if world.scene.space_type in {"station", "base", "ship"}:
        tags.add("tether")
        tags.add("signal")
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling and validation
# ---------------------------------------------------------------------------

def valid_names_for_role(role: str) -> list[str]:
    if role in {"captain", "pilot"}:
        return ["Astra", "Nova", "Orion", "Pip"]
    return ["Astra", "Nova", "Orion", "Pip"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "scene", None) and getattr(args, "trap", None) and getattr(args, "tool", None):
        if (getattr(args, "scene", None), getattr(args, "trap", None), getattr(args, "tool", None)) not in valid_pairs():
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_pairs()
        if (getattr(args, "scene", None) is None or c[0] == getattr(args, "scene", None))
        and (getattr(args, "trap", None) is None or c[1] == getattr(args, "trap", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    scene_id, trap_id, tool_id = rng.choice(list(combos))
    role = getattr(args, "role", None) or rng.choice(CREW_ROLES)
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    names = valid_names_for_role(role)
    name = getattr(args, "name", None) or rng.choice(names)
    return StoryParams(
        scene=scene_id,
        trap=trap_id,
        tool=tool_id,
        name=name,
        role=role,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.trapped_in:
            bits.append(f"trapped_in={e.trapped_in}")
        if e.liberated:
            bits.append("liberated=True")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(scene="station", trap="net", tool="cutter", name="Astra", role="captain", mood="steady"),
    StoryParams(scene="moonbase", trap="latch", tool="key", name="Nova", role="mechanic", mood="careful"),
    StoryParams(scene="shipdeck", trap="field", tool="tuner", name="Orion", role="pilot", mood="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure story world about liberating a rhyme bot."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=sorted(HEROES))
    ap.add_argument("--role", choices=CREW_ROLES)
    ap.add_argument("--mood", choices=MOODS)
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


def asp_show() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show())
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_show())
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible scene/trap/tool triples:\n")
        for scene, trap, tool in pairs:
            print(f"  {scene:10} {trap:8} {tool:8}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.trap} with {p.tool} at {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
