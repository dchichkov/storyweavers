#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a hospitable host, a careful monitor,
and a dung-smudged problem that turns into a kind fix.

The seed idea:
- A small host welcomes a visitor.
- A monitor watches the situation and notices dung in the wrong place.
- There is Conflict because the mess threatens the tea, the rug, or the bed.
- A gentle cleanup or relocation resolves things in a rhyming, child-friendly way.

The world is intentionally small:
- One host character
- One guest character
- One monitor character
- One mess-causing animal or object
- One safe, reasonable fix

The prose should feel like a nursery rhyme: short, concrete, rhythmic, and warm.
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


# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guest: object | None = None
    hero: object | None = None
    monitor: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    place: str
    indoor: bool
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
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
    protective: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"dung", "mud"}),
    "cottage": Setting(place="the cottage", indoor=True, affords={"dung"}),
    "yard": Setting(place="the yard", indoor=False, affords={"dung", "mud"}),
}

PROBLEMS = {
    "dung": Problem(
        id="dung",
        verb="tiptoe near the dung",
        gerund="tiptoeing near the dung",
        rush="rush toward the dung",
        mess="dirty",
        soil="smudged and stinky",
        zone={"floor"},
        keyword="dung",
        tags={"dung", "dirty"},
    ),
    "mud": Problem(
        id="mud",
        verb="splash in the mud",
        gerund="splashing in the mud",
        rush="dash into the mud",
        mess="dirty",
        soil="muddy",
        zone={"floor"},
        keyword="mud",
        tags={"mud", "dirty"},
    ),
}

PRIZES = {
    "rug": Prize(label="rug", phrase="a bright little rug", type="rug", region="floor"),
    "bed": Prize(label="bed", phrase="a tidy little bed", type="bed", region="floor"),
    "tea": Prize(label="tea", phrase="a warm cup of tea", type="tea", region="table"),
}

FIXES = [
    Fix(
        id="broom",
        label="a broom",
        prep="fetch a broom and sweep it clean",
        tail="brought out the broom and swept the floor",
        guards={"dirty"},
        covers={"floor"},
    ),
    Fix(
        id="mat",
        label="a clean mat",
        prep="lay down a clean mat first",
        tail="set down the clean mat before the next step",
        guards={"dirty"},
        covers={"floor"},
    ),
]

HERO_NAMES = ["Mia", "Ned", "Rose", "Tom", "Lily", "Ben"]
GUEST_NAMES = ["Pip", "Dot", "Jem", "Wren", "Kit", "Bea"]
MONITOR_NAMES = ["Nurse", "Moss", "Tally", "Mina", "Cora", "Della"]
TRAITS = ["gentle", "cheery", "quiet", "busy", "kind"]


# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    prize: str
    hero_name: str
    guest_name: str
    monitor_name: str
    trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
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


ASP_RULES = r"""
% A prize is at risk when the problem splashes the same region the prize sits on.
at_risk(P, X) :- prize(P), problem(X), zone(X, R), region(P, R).

% A fix is compatible when it guards the mess and covers the at-risk region.
fixes(F, X, P) :- fix(F), problem(X), prize(P),
                  guards(F, M), mess_of(X, M),
                  covers(F, R), region(P, R).

has_fix(X, P) :- fixes(_, X, P).

valid_story(S, X, P) :- setting(S), problem(X), prize(P), afforded(S, X), at_risk(P, X), has_fix(X, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afforded", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess_of", pid, p.mess))
        for r in sorted(p.zone):
            lines.append(asp.fact("zone", pid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            for prid, pr in PRIZES.items():
                if pid in s.affords and pr.region in p.zone:
                    if any(fx for fx in FIXES if p.mess in fx.guards and pr.region in fx.covers):
                        out.append((sid, pid, prid))
    return out


def asp_verify() -> int:
    import asp
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# -----------------------------------------------------------------------------
# Story simulation
# -----------------------------------------------------------------------------
def prize_at_risk(problem: Problem, prize: Prize) -> bool:
    return prize.region in problem.zone


def select_fix(problem: Problem, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if problem.mess in fx.guards and prize.region in fx.covers:
            return fx
    return None


def predict_mess(world: World, problem: Problem, prize_id: str) -> dict:
    sim = world.copy()
    sim.zone = set(problem.zone)
    prize = sim.get(prize_id)
    prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1
    return {"soiled": True, "dirty": prize.meters["dirty"]}


def propagate(world: World) -> None:
    for prize in list(world.entities.values()):
        if prize.meters.get("dirty", 0) >= 1 and ("clean", prize.id) not in world.fired:
            world.fired.add(("clean", prize.id))


def tell(setting: Setting, problem: Problem, prize_cfg: Prize, hero_name: str,
         guest_name: str, monitor_name: str, trait: str) -> World:
    world = World(setting)
    world.weather = "wet" if not setting.indoor else ""

    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mia", "Rose", "Lily"} else "boy"))
    guest = world.add(Entity(id=guest_name, kind="character", type="girl" if guest_name in {"Bea", "Dot"} else "boy"))
    monitor = world.add(Entity(id=monitor_name, kind="character", type="woman"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    prize.worn_by = None

    hero.memes["hospitable"] = 1
    guest.memes["welcome"] = 1
    monitor.memes["watchful"] = 1

    world.say(f"{hero_name} was a {trait} little host in {setting.place}.")
    world.say(f"{hero_name} was hospitable, and {guest_name} came in with a smile.")
    world.say(f"They set out {prize_cfg.phrase}, nice and neat, and sang a tiny do-si-do.")

    world.para()
    world.say(f"Then {monitor_name} kept watch from the corner chair.")
    world.say(f"{monitor_name} saw the {problem.keyword} and frowned with care.")
    world.say(f'“Oh dear,” {monitor_name} said, “that spot is no place to spare.”')

    world.para()
    world.zone = set(problem.zone)
    world.say(f"{hero_name} wanted to {problem.verb}, but the little floor would not stay clean.")
    if prize_at_risk(problem, prize):
        world.say(f"The {prize.label} could get {problem.soil}, and that would be a sad little scene.")
        hero.memes["conflict"] = 1
        world.say(f"There was Conflict in the room, like a hum and a broom.")
        fix = select_fix(problem, prize)
        if fix:
            world.say(f"“Let us {fix.prep},” said {monitor_name}, bright as a moon.")
            world.say(f"{guest_name} helped at once, and {hero_name} nodded soon.")
            world.say(f"They {fix.tail}, and the messy spot was gone.")
            hero.memes["joy"] = 1
            guest.memes["joy"] = 1
            monitor.memes["relief"] = 1
            propagate(world)
            world.para()
            world.say(f"So the room stayed snug, and the tea stayed true.")
            world.say(f"{hero_name} was still hospitable, and {guest_name} was happy too.")
            world.say(f"With the {problem.keyword} put away, they sang bye-bye-blue.")
            world.facts.update(
                hero=hero, guest=guest, monitor=monitor,
                problem=problem, prize=prize, fix=fix, setting=setting
            )
            return world
    world.say(f"But no good fix came, and the rhyme could not glide.")
    world.facts.update(hero=hero, guest=guest, monitor=monitor, problem=problem, prize=prize, fix=None, setting=setting)
    return world


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a nursery-rhyme story about a hospitable child who notices "{problem.keyword}" and keeps a guest safe.',
        f"Tell a gentle rhyme where {hero.id} welcomes a friend, a monitor spots {problem.keyword}, and a little mess is fixed.",
        f"Write a short child-facing story with Conflict, a kind helper, and {prize.label} staying clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guest = _safe_fact(world, f, "guest")
    monitor = _safe_fact(world, f, "monitor")
    problem = _safe_fact(world, f, "problem")
    prize = _safe_fact(world, f, "prize")
    fix = _safe_fact(world, f, "fix")
    qas = [
        QAItem(
            question=f"Who was hospitable in the story?",
            answer=f"{hero.id} was hospitable. {hero.id} welcomed {guest.id} kindly and tried to keep the room nice for everyone.",
        ),
        QAItem(
            question=f"What did {monitor.id} notice that caused Conflict?",
            answer=f"{monitor.id} noticed the {problem.keyword}. That made Conflict because the {prize.label} could get {problem.soil}.",
        ),
        QAItem(
            question=f"What did they do to keep the {prize.label} safe?",
            answer=f"They used {fix.label} so the messy bit would not spoil the {prize.label}. Then the room stayed neat.",
        ),
    ]
    return qas


WORLD_QA = {
    "dung": [
        QAItem(
            question="What is dung?",
            answer="Dung is animal droppings. It is messy, so people usually keep it away from places where children play.",
        )
    ],
    "monitor": [
        QAItem(
            question="What does a monitor do?",
            answer="A monitor watches carefully and notices when something needs attention.",
        )
    ],
    "hospitable": [
        QAItem(
            question="What does hospitable mean?",
            answer="Hospitable means being warm and welcoming to guests.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is Conflict in a story?",
            answer="Conflict is the part where a problem or disagreement makes things tense before it is solved.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tags.add("monitor")
    tags.add("hospitable")
    tags.add("conflict")
    out: list[QAItem] = []
    for tag in ["hospitable", "monitor", "dung", "conflict"]:
        if tag in tags and tag in WORLD_QA:
            out.extend(WORLD_QA[tag])
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


# -----------------------------------------------------------------------------
# CLI helpers
# -----------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, problem: Problem, prize: Prize) -> str:
    if not prize_at_risk(problem, prize):
        return f"(No story: the {problem.keyword} would not reach the {prize.label}, so there is no honest Conflict.)"
    if not select_fix(problem, prize):
        return f"(No story: no fix in the catalog can protect the {prize.label} from the {problem.keyword}.)"
    return "(No story: that combination is not reasonable.)"


# -----------------------------------------------------------------------------
# Parameters and generation
# -----------------------------------------------------------------------------
@dataclass
class RunConfig:
    setting: str
    problem: str
    prize: str
    name: str
    guest: str
    monitor: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about hospitality, a monitor, and dung.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--guest")
    ap.add_argument("--monitor")
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))

    s = _safe_lookup(SETTINGS, setting)
    p = _safe_lookup(PROBLEMS, problem)
    pr = _safe_lookup(PRIZES, prize)

    if problem not in s.affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not prize_at_risk(p, pr):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not select_fix(p, pr):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    guest = getattr(args, "guest", None) or rng.choice(GUEST_NAMES)
    monitor = getattr(args, "monitor", None) or rng.choice(MONITOR_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, prize=prize, hero_name=name, guest_name=guest, monitor_name=monitor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(PRIZES, params.prize),
        params.hero_name,
        params.guest_name,
        params.monitor_name,
        params.trait,
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


# -----------------------------------------------------------------------------
# ASP verification
# -----------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_show_program() -> str:
    return asp_program("#show valid_story/3.")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="nursery", problem="dung", prize="rug", hero_name="Mia", guest_name="Pip", monitor_name="Nurse", trait="gentle"),
    StoryParams(setting="cottage", problem="dung", prize="tea", hero_name="Rose", guest_name="Dot", monitor_name="Moss", trait="cheery"),
    StoryParams(setting="yard", problem="mud", prize="bed", hero_name="Ben", guest_name="Jem", monitor_name="Tally", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        items = asp_valid_stories()
        print(f"{len(items)} compatible story combinations:\n")
        for sid, pid, prid in items:
            print(f"  {sid:8} {pid:6} {prid}")
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
            header = f"### {p.hero_name}: {p.problem} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
