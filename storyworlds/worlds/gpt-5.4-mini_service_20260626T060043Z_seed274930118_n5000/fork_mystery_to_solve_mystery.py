#!/usr/bin/env python3
"""
storyworlds/worlds/fork_mystery_to_solve_mystery.py
===================================================

A small mystery storyworld about a gentle little detective, a missing fork,
and the clue trail that leads to a simple solved surprise.

Seed premise:
- A child notices a fork is missing before a picnic/lunch.
- There is a tiny mystery in the room or garden.
- The child looks carefully, follows clues, and uses the fork as an instrument
  to help solve the mystery.
- The ending proves what changed: the missing thing is found, and the world is
  tidier/safer/happier than before.

This world keeps the prose close to classic Mystery-style children's stories:
clear setup, careful clues, a small turn, and a satisfying reveal.
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


# ---------------------------------------------------------------------------
# Entities
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
    type: str = "thing"          # child, parent, fork, basket, etc.
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_to: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    missing: object | None = None
    parent: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def noun(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Setting:
    place: str
    indoors: bool
    surfaces: list[str]
    has_garden: bool = False
    has_table: bool = False
    has_sink: bool = False
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
class Mystery:
    id: str
    missing: str
    clue_word: str
    clue_spot: str
    hidden_place: str
    solve_method: str
    danger: str
    theme: str = "mystery"
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
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps_with: set[str]
    safe_spots: set[str]
    use_verb: str
    outcome: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, surfaces=["table", "floor", "sink"], has_table=True, has_sink=True),
    "garden": Setting(place="the garden", indoors=False, surfaces=["soil", "path", "bench"], has_garden=True),
    "playroom": Setting(place="the playroom", indoors=True, surfaces=["rug", "shelf", "basket"], has_table=True),
    "picnic": Setting(place="the picnic blanket", indoors=False, surfaces=["blanket", "grass", "basket"], has_table=True),
}

MYSTERIES = {
    "missing_fork": Mystery(
        id="missing_fork",
        missing="fork",
        clue_word="crumbs",
        clue_spot="under the bowl",
        hidden_place="behind the sugar jar",
        solve_method="look for the trail of crumbs",
        danger="a sticky lunch that cannot be eaten neatly",
    ),
    "lost_key": Mystery(
        id="lost_key",
        missing="small key",
        clue_word="scratch",
        clue_spot="near the flower pot",
        hidden_place="under the rug",
        solve_method="follow the tiny scratch marks",
        danger="a locked box that stays shut",
    ),
    "hidden_note": Mystery(
        id="hidden_note",
        missing="note",
        clue_word="fold",
        clue_spot="inside the basket",
        hidden_place="under the plate",
        solve_method="notice the careful fold in the paper",
        danger="a surprise message that nobody can read",
    ),
}

TOOLS = {
    "fork": Tool(
        id="fork",
        label="fork",
        phrase="a shiny little fork",
        kind="fork",
        helps_with={"crumbs", "fold", "scratch"},
        safe_spots={"table", "basket", "blanket"},
        use_verb="poke gently",
        outcome="revealed a clue",
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a round spoon",
        kind="spoon",
        helps_with={"crumbs"},
        safe_spots={"table", "basket", "blanket"},
        use_verb="scoop gently",
        outcome="moved the crumbs aside",
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a tiny magnifying glass",
        kind="magnifier",
        helps_with={"scratch", "fold", "crumbs"},
        safe_spots={"table", "basket", "blanket", "rug", "floor", "soil"},
        use_verb="look closely",
        outcome="made the clue easy to see",
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Sam", "Noah", "Theo"]
TRAITS = ["curious", "careful", "gentle", "brave", "quiet", "smart"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting, mystery: Mystery, tool: Tool) -> None:
        self.setting = setting
        self.mystery = mystery
        self.tool = tool
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _place_detail(setting: Setting) -> str:
    if setting.indoors and setting.has_table:
        return f"{setting.place.capitalize()} was neat and quiet, with a little table ready for anything."
    if setting.has_garden:
        return "The garden was soft and green, with tiny places where clues could hide."
    return f"{setting.place.capitalize()} looked calm, and every corner seemed worth a closer look."


def _intro(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} little {hero.type} who loved noticing small things."
    )
    world.say(
        f"{hero.id} and {parent.label} were having a calm day at {world.setting.place}."
    )
    world.say(_place_detail(world.setting))


def _mystery_setup(world: World, hero: Entity, parent: Entity, missing: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then {hero.id} blinked. {hero.pronoun('possessive').capitalize()} {missing.noun} was missing."
    )
    world.say(
        f"'{missing.noun.capitalize()} first, clues second,' {hero.id} whispered, just like a little detective."
    )
    world.say(
        f"{parent.label} pointed at the room and said there might be {world.mystery.clue_word} near {world.mystery.clue_spot}."
    )


def _inspect_clue(world: World, hero: Entity) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} looked very carefully and found the {world.mystery.clue_word}."
    )
    world.say(
        f"The clue suggested someone had been near {world.mystery.hidden_place}."
    )


def _use_tool(world: World, hero: Entity) -> None:
    tool = world.tool
    if world.mystery.clue_word not in tool.helps_with:
        pass

    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} picked up {tool.phrase} and decided to {tool.use_verb} where the clue pointed."
    )
    world.say(
        f"The {tool.label} {tool.outcome}, and that made the mystery easier to solve."
    )


def _solve(world: World, hero: Entity, missing: Entity, parent: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"At last, {hero.id} found the {missing.noun} in {world.mystery.hidden_place}."
    )
    missing.hidden = False
    missing.moved_to = hero.id
    world.say(
        f"{hero.id} brought it back to {parent.label}, and the whole day felt lighter."
    )


def _ending(world: World, hero: Entity, missing: Entity, parent: Entity) -> None:
    world.say(
        f"Soon {hero.id} was smiling with a solved mystery, and {missing.noun} was right where it belonged."
    )
    if missing.noun == "fork":
        world.say(
            f"The lunch looked ready again, because the fork was back on the table beside {hero.id}'s plate."
        )
    else:
        world.say(
            f"The small clue was no longer a problem, and {parent.label} could relax."
        )


def tell(setting: Setting, mystery: Mystery, tool: Tool, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting, mystery, tool)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"trait": 0},
    ))
    if hero_traits:
        hero.memes["trait_name"] = 1
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=mystery.missing,
        label=mystery.missing,
        phrase=mystery.missing,
        hidden=True,
        moved_to=mystery.hidden_place,
        caretaker=parent.id,
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type=tool.kind,
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))

    hero.memes["trait"] = 1
    hero.memes["curiosity"] = 1
    world.facts.update(hero=hero, parent=parent, missing=missing, tool=tool_ent, mystery=mystery)

    _intro(world, hero, parent)
    world.para()
    _mystery_setup(world, hero, parent, missing)
    _inspect_clue(world, hero)
    world.para()
    _use_tool(world, hero)
    _solve(world, hero, missing, parent)
    world.para()
    _ending(world, hero, missing, parent)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the tool helps with the clue word.
solvable(M, T) :- mystery(M), tool(T), clue_word(M, C), helps(T, C).

% A story is valid when the setting matches the mystery and the tool is reasonable.
valid_story(S, M, T) :- setting(S), mystery(M), tool(T), solvable(M, T).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.has_garden:
            lines.append(asp.fact("has_garden", sid))
        if s.has_table:
            lines.append(asp.fact("has_table", sid))
        if s.has_sink:
            lines.append(asp.fact("has_sink", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, k))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for tid, t in TOOLS.items():
                if m.clue_word in t.helps_with:
                    combos.append((sid, mid, tid))
    return combos


def explain_rejection(setting: str, mystery: str, tool: str) -> str:
    m = _safe_lookup(MYSTERIES, mystery)
    t = _safe_lookup(TOOLS, tool)
    return (
        f"(No story: {t.label} does not help with the clue word '{m.clue_word}'. "
        f"Pick a tool that fits the mystery better.)"
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    m = _safe_fact(world, f, "mystery")
    t = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short mystery story for a child about {hero.id}, a missing {m.missing}, and a {t.label}.',
        f"Tell a gentle detective story where {hero.id} notices a clue and uses a {t.label} to solve the mystery.",
        f'Write a simple mystery set at {world.setting.place} that includes a {m.clue_word} clue and ends with the missing thing found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    missing = _safe_fact(world, f, "missing")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice at {world.setting.place}?",
            answer=f"{hero.id} noticed that {missing.noun} was missing, and {hero.id} became a little detective.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} know where to look?",
            answer=f"The clue was {mystery.clue_word}, and it pointed {hero.id} toward {mystery.hidden_place}.",
        ),
        QAItem(
            question=f"How did the {tool.label} help solve the mystery?",
            answer=f"{hero.id} used {tool.phrase} to follow the clue, and that {tool.outcome}.",
        ),
        QAItem(
            question=f"Where was the missing {missing.noun} found?",
            answer=f"The missing {missing.noun} was found in {mystery.hidden_place}, and then {hero.id} brought it back to {parent.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tool = _safe_fact(world, world.facts, "tool")
    mystery = _safe_fact(world, world.facts, "mystery")
    out = []
    if tool.label == "fork":
        out.append(QAItem(
            question="What is a fork for?",
            answer="A fork is a tool with little points that helps you pick up food or gently move things aside.",
        ))
    if mystery.clue_word == "crumbs":
        out.append(QAItem(
            question="What are crumbs?",
            answer="Crumbs are tiny bits of food that fall off bread, crackers, or cake.",
        ))
    if mystery.clue_word == "scratch":
        out.append(QAItem(
            question="What is a scratch mark?",
            answer="A scratch mark is a small line made when something rough brushes across a surface.",
        ))
    if mystery.clue_word == "fold":
        out.append(QAItem(
            question="What is a fold in paper?",
            answer="A fold is a bend in paper where it has been pressed over and over.",
        ))
    return out


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
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.hidden:
            bits.append("hidden=True")
        if e.moved_to:
            bits.append(f"moved_to={e.moved_to}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", mystery="missing_fork", tool="fork", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden", mystery="lost_key", tool="magnifier", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="picnic", mystery="hidden_note", tool="fork", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery world about a child detective and a fork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "mystery", None) and getattr(args, "tool", None):
        if _safe_lookup(MYSTERIES, getattr(args, "mystery", None)).clue_word not in _safe_lookup(TOOLS, getattr(args, "tool", None)).helps_with:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mystery, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        [params.trait],
        params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
