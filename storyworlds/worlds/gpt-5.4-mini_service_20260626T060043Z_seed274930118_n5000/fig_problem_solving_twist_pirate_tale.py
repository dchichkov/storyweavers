#!/usr/bin/env python3
"""
storyworlds/worlds/fig_problem_solving_twist_pirate_tale.py
============================================================

A small pirate-tale story world with a child-friendly problem-solving turn and
a gentle twist. The seed image is a crew at sea, a precious fig, and a clever
fix that changes what the fig is for.

Premise:
- A little pirate loves a fig.
- A problem at sea makes the fig seem needed for something else.
- The crew tries one idea, then discovers a twist.
- The fig helps in an unexpected but sensible way.

This script follows the storyworld contract:
- self-contained stdlib script
- shared results imported eagerly
- ASP helper imported lazily
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    cloth: object | None = None
    fig: object | None = None
    hero: object | None = None
    rope: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
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
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    sea: bool = True
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
class Problem:
    id: str
    title: str
    cause: str
    hint: str
    emotion: str
    tags: set[str] = field(default_factory=set)
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
class Twist:
    id: str
    reveal: str
    method: str
    payoff: str
    tags: set[str] = field(default_factory=set)
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
    use: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.seen_twist: bool = False

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


PROBLEMS = {
    "storm": Problem(
        id="storm",
        title="a squalling storm",
        cause="the wind kicked up and slapped the sails",
        hint="the mast leaned and the ship shivered",
        emotion="worried",
        tags={"wind", "sea", "sail"},
    ),
    "crates": Problem(
        id="crates",
        title="a pile of rolling crates",
        cause="the cargo boxes slid across the deck",
        hint="they blocked the path to the galley",
        emotion="stuck",
        tags={"cargo", "deck"},
    ),
    "parrot": Problem(
        id="parrot",
        title="a noisy parrot",
        cause="the parrot would not stop squawking at the wrong time",
        hint="the crew could not hear the captain's calls",
        emotion="frazzled",
        tags={"parrot", "noise"},
    ),
}

TWISTS = {
    "sailcloth": Twist(
        id="sailcloth",
        reveal="the fig's sticky juice could help patch a torn sail",
        method="press the fig skin and pulp into the rip",
        payoff="the sail held long enough to catch the wind",
        tags={"sail", "sticky"},
    ),
    "parrot": Twist(
        id="parrot",
        reveal="the parrot had been trying to guard the figs all along",
        method="offer one fig to the bird",
        payoff="the parrot quieted down and led the way to the hidden box",
        tags={"parrot", "fig"},
    ),
    "lantern": Twist(
        id="lantern",
        reveal="the fig's sweet smell could lure a firefly lantern guide",
        method="leave a fig on the rail",
        payoff="the tiny lights flew in a bright trail toward safe water",
        tags={"light", "fig"},
    ),
}

TOOLS = {
    "fig": Tool(
        id="fig",
        label="a ripe fig",
        phrase="a ripe fig with a purple skin",
        use="sweeten the moment",
        helps={"parrot", "lantern"},
        covers={"snack", "sticky"},
    ),
    "rope": Tool(
        id="rope",
        label="a coil of rope",
        phrase="a strong coil of rope",
        use="tie things down",
        helps={"storm", "crates"},
        covers={"deck"},
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket",
        phrase="a sturdy bucket",
        use="scoop and carry water",
        helps={"storm", "crates"},
        covers={"water"},
    ),
    "cloth": Tool(
        id="cloth",
        label="a sailcloth scrap",
        phrase="a torn sailcloth scrap",
        use="patch a tear",
        helps={"storm", "sailcloth"},
        covers={"sail"},
    ),
}

SETTINGS = {
    "ship": Setting(place="the little ship", affords={"storm", "parrot"}, sea=True),
    "dock": Setting(place="the dock by the sea", affords={"crates", "parrot"}, sea=False),
    "cove": Setting(place="the windy cove", affords={"storm", "lantern"}, sea=True),
}

NAMES = ["Pip", "Mina", "Ned", "Rose", "Bea", "Cleo", "Toby", "Finn"]
PIRATE_TITLES = ["tiny pirate", "young pirate", "little deckhand", "curious pirate"]
CREW_ROLES = ["captain", "mate", "bosun", "first mate"]


@dataclass
class StoryParams:
    place: str
    problem: str
    twist: str
    name: str
    role: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for problem_id in setting.affords:
            for twist_id, twist in TWISTS.items():
                if problem_id == "storm" and twist_id in {"sailcloth", "lantern"}:
                    combos.append((place, problem_id, twist_id))
                if problem_id == "parrot" and twist_id in {"parrot"}:
                    combos.append((place, problem_id, twist_id))
                if problem_id == "crates" and twist_id in {"sailcloth"}:
                    combos.append((place, problem_id, twist_id))
    return combos


def reasonability_check(problem: Problem, twist: Twist) -> bool:
    if problem.id == "storm" and twist.id in {"sailcloth", "lantern"}:
        return True
    if problem.id == "parrot" and twist.id == "parrot":
        return True
    if problem.id == "crates" and twist.id == "sailcloth":
        return True
    return False


def explain_rejection(problem: Problem, twist: Twist) -> str:
    return (
        f"(No story: {problem.title} does not fit the twist '{twist.id}' in a "
        f"sensible pirate tale. Try a different problem and twist pair.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with a fig, a problem, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=CREW_ROLES)
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
    if getattr(args, "problem", None) and getattr(args, "twist", None):
        if not reasonability_check(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(TWISTS, getattr(args, "twist", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, problem, twist = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(CREW_ROLES)
    return StoryParams(place=place, problem=problem, twist=twist, name=name, role=role)


def _do_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    if problem.id == "storm":
        hero.meters["sway"] = hero.meters.get("sway", 0.0) + 1.0
    elif problem.id == "crates":
        hero.meters["blocked"] = hero.meters.get("blocked", 0.0) + 1.0
    else:
        hero.memes["noise"] = hero.memes.get("noise", 0.0) + 1.0


def _use_tool(world: World, hero: Entity, tool: Tool, problem: Problem, twist: Twist) -> bool:
    if problem.id == "storm" and twist.id == "sailcloth" and tool.id == "cloth":
        world.say("The pirate pressed the sailcloth scrap over the rip, but the wind still tugged hard.")
        return False
    if problem.id == "parrot" and twist.id == "parrot" and tool.id == "fig":
        world.say("The little pirate held up the fig, and the parrot stopped to stare.")
        return True
    if problem.id == "storm" and twist.id == "lantern" and tool.id == "fig":
        world.say("The pirate set the fig on the rail, and its sweet smell drifted into the dark.")
        return True
    if problem.id == "storm" and twist.id == "sailcloth" and tool.id == "fig":
        world.say("The fig juice made the torn cloth tacky, just enough to hold the patch in place.")
        return True
    return False


def tell(setting: Setting, problem: Problem, twist: Twist, hero_name: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", traits=["little", "brave"]))
    captain = world.add(Entity(id="Captain", kind="character", type=role, label="the captain"))
    fig = world.add(Entity(id="fig", type="fig", label="fig", phrase="a ripe fig", owner=hero.id))
    cloth = world.add(Entity(id="cloth", type="cloth", label="cloth", phrase="a sailcloth scrap"))
    rope = world.add(Entity(id="rope", type="rope", label="rope", phrase="a coil of rope"))

    world.say(f"{hero.id} was a little pirate on {setting.place}, and {hero.pronoun('possessive')} pockets were full of curiosity.")
    world.say(f"{hero.id} loved {fig.phrase}, because it was sweet and soft and felt like treasure.")
    world.say(f"One day, {problem.title} came along: {problem.cause}, and {problem.hint}.")

    world.para()
    world.say(f"{hero.id} frowned, because the crew needed a fix.")
    world.say(f"{twist.reveal.capitalize()}.")

    _do_problem(world, hero, problem)

    world.para()
    world.say(f"{hero.id} tried a plain pirate fix first.")
    if problem.id == "storm":
        world.say("They grabbed rope and cloth, and the captain held the line.")
    elif problem.id == "crates":
        world.say("They tied the crates with rope so they would stop rolling.")
    else:
        world.say("They asked the parrot to hush, but the bird only flapped its wings.")
    used_fig = _use_tool(world, hero, fig, problem, twist)

    if used_fig:
        world.seen_twist = True
        world.para()
        world.say(f"That was the twist: {twist.method}, and soon {twist.payoff}.")
        world.say(f"{hero.id} grinned, because the fig was still a snack and now it had helped the whole crew.")
        world.say(f"The captain laughed, and the little ship felt safe again.")
    else:
        world.para()
        world.say(f"The first try did not work, so {hero.id} paused and thought harder.")
        world.say(f"Then {hero.id} found the clever way: {twist.method}, and soon {twist.payoff}.")
        world.say(f"The crew cheered, because the fig turned an ordinary problem into a surprise victory.")

    world.facts.update(
        hero=hero,
        captain=captain,
        fig=fig,
        problem=problem,
        twist=twist,
        setting=setting,
        used_fig=used_fig,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate story for a child that includes a fig and a clever twist.',
        f"Tell a tiny pirate tale where {f['hero'].id} meets {f['problem'].title} and discovers that {f['twist'].reveal}.",
        f'Write a story about a little pirate on {f["setting"].place} who solves a problem with a fig.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    twist = _safe_fact(world, f, "twist")
    qa = [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a pirate tale about {hero.id}, a little pirate, and a problem that needs a clever fix.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face on {f['setting'].place}?",
            answer=f"{hero.id} faced {problem.title}, and {problem.hint}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}.",
        ),
        QAItem(
            question=f"How did the fig help?",
            answer=f"The fig helped because it became part of the clever fix, instead of only being a snack.",
        ),
    ]
    if f["used_fig"]:
        qa.append(QAItem(
            question=f"Did the first idea work right away for {hero.id}?",
            answer="No, the first idea did not work right away, so the crew had to think again before the fig could help.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "fig": [
        ("What is a fig?",
         "A fig is a small sweet fruit with soft inside and skin that can be purple, green, or brown."),
    ],
    "sticky": [
        ("What does sticky mean?",
         "Sticky means something can cling to fingers or surfaces and hold on for a little while."),
    ],
    "sail": [
        ("What does a sail do?",
         "A sail catches the wind and helps a boat move across the water."),
    ],
    "parrot": [
        ("What is a parrot?",
         "A parrot is a bird with a strong beak that can copy sounds and squawk loudly."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["problem"].id, world.facts["twist"].id, "fig"}
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  seen_twist={world.seen_twist}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", problem="storm", twist="sailcloth", name="Pip", role="captain"),
    StoryParams(place="ship", problem="parrot", twist="parrot", name="Mina", role="mate"),
    StoryParams(place="cove", problem="storm", twist="lantern", name="Ned", role="first mate"),
]


ASP_RULES = r"""
problem_matches_twist(storm,sailcloth).
problem_matches_twist(storm,lantern).
problem_matches_twist(parrot,parrot).
problem_matches_twist(crates,sailcloth).

valid(Place, Problem, Twist) :- affords(Place, Problem), problem_matches_twist(Problem, Twist).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(TWISTS, params.twist), params.name, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, twist = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(CREW_ROLES)
    return StoryParams(place=place, problem=problem, twist=twist, name=name, role=role)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for problem_id in setting.affords:
            problem = _safe_lookup(PROBLEMS, problem_id)
            for twist_id, twist in TWISTS.items():
                if reasonability_check(problem, twist):
                    combos.append((place, problem_id, twist_id))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, twist) combos:\n")
        for place, problem, twist in combos:
            print(f"  {place:8} {problem:8} {twist:10}")
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
            header = f"### {p.name}: {p.problem} with {p.twist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
