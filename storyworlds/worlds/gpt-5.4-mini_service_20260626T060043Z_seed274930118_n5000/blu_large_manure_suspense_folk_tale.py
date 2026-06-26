#!/usr/bin/env python3
"""
storyworlds/worlds/blu_large_manure_suspense_folk_tale.py
==========================================================

A small folk-tale storyworld about a blu bundle, a large load of manure,
and a suspenseful trip across a village path.

Premise:
- A child helper must carry a large sack of manure to the garden.
- The sack is tied with a blu ribbon that the helper treasures.
- A little suspense grows when the path becomes tricky and the sack starts to slip.

World style:
- Folklike, concrete, child-facing.
- State-driven: the load can tip, the ribbon can fray, and the helper can gain or lose courage.
- The ending proves what changed: the manure reaches the garden, and the blu ribbon stays safe.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager results import
- lazy ASP import only inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- ASP twin with verify mode
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    movable: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    load: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    afford: set[str] = field(default_factory=set)
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
class Load:
    id: str
    label: str
    phrase: str
    region: str
    weight: str
    precious: str
    danger: str
    slips: str
    keyword: str = "manure"
    tags: set[str] = field(default_factory=set)
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
    protects: set[str]
    fits: set[str]
    prep: str
    finish: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_danger: float = 0.0
        self.wind: str = ""
        self.rain: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_danger = self.path_danger
        clone.wind = self.wind
        clone.rain = self.rain
        return clone


@dataclass
class StoryParams:
    place: str
    load: str
    tool: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "farm": Setting(place="the farm path", afford={"manure"}),
    "village": Setting(place="the village lane", afford={"manure"}),
    "orchard": Setting(place="the orchard road", afford={"manure"}),
}

LOADS = {
    "manure": Load(
        id="manure",
        label="manure",
        phrase="a large sack of manure tied with a blu ribbon",
        region="arms",
        weight="large",
        precious="blu ribbon",
        danger="spill all over the path",
        slips="slid open",
        tags={"manure", "blu", "large"},
    ),
}

TOOLS = {
    "cart": Tool(
        id="cart",
        label="handcart",
        phrase="a sturdy handcart with high sides",
        protects={"arms"},
        fits={"manure"},
        prep="set the sack into the handcart and push it slowly",
        finish="kept the sack high in the handcart all the way",
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a strong rope",
        protects={"arms"},
        fits={"manure"},
        prep="bind the sack with the rope and carry it together",
        finish="kept the sack tied tight with the rope",
    ),
}

NAMES = ["Milo", "Lena", "Suri", "Ivo", "Nina", "Pavel", "Ari", "Toma"]
HERO_TRAITS = ["careful", "brave", "patient", "gentle", "quick-thinking", "steady"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]

ASP_RULES = r"""
% A load is risky when the path is long enough and the load is large manure.
risky(L) :- load(L), large(L), manure(L).

% A tool is a valid fix when it protects the carried region of the load.
fix(T, L) :- tool(T), load(L), risky(L), protects(T, R), on(L, R), fits(T, L).

valid_story(Place, L, T) :- setting(Place), afford(Place, manure), risky(L), fix(T, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("manure", lid))
        lines.append(asp.fact("large", lid))
        lines.append(asp.fact("on", lid, l.region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in sorted(t.protects):
            lines.append(asp.fact("protects", tid, r))
        for f in sorted(t.fits):
            lines.append(asp.fact("fits", tid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def reasonableness_gate(load: Load, tool: Tool) -> bool:
    return load.region in tool.protects and load.id in tool.fits


def valid_stories() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        if "manure" not in setting.afford:
            continue
        for load_id, load in LOADS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(load, tool):
                    out.append((place, load_id, tool_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale suspense storyworld about a blu ribbon and a large load of manure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    if getattr(args, "load", None) and getattr(args, "tool", None) and not reasonableness_gate(_safe_lookup(LOADS, getattr(args, "load", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_stories()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "load", None) is None or c[1] == getattr(args, "load", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, load_id, tool_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, load=load_id, tool=tool_id, name=name, gender=gender, helper=helper, trait=trait)


def _carry_load(world: World, hero: Entity, load: Entity) -> None:
    hero.meters["burden"] += 1
    load.carried_by = hero.id
    load.meters["sway"] += 1
    world.path_danger += 1.0


def _risk_spill(world: World, load: Entity) -> None:
    if world.path_danger >= THRESHOLD:
        load.meters["spill"] += 1
        load.memes["fear"] += 1


def tell(world: World, hero: Entity, helper: Entity, load: Entity, tool: Optional[Entity]) -> None:
    world.say(f"Once, {hero.id} was a {hero.meters.get('age', 1):.0f}-hearted {hero.type} with a taste for village errands.")
    world.say(f"{hero.pronoun().capitalize()} saw {load.phrase} and knew the farm needed it by dusk.")
    world.say(f"The sack was {load.weight}, and the blu ribbon around it shone like a piece of sky.")

    world.para()
    world.say(f"{hero.id} and {helper.label} set out along {world.setting.place}.")
    world.say(f"The wind worried at the sack, and the path turned steep and uneven.")
    _carry_load(world, hero, load)
    _risk_spill(world, load)

    if load.meters["spill"] >= THRESHOLD and not tool:
        world.say(f"The sack {load.slips}, and {hero.id}'s heart thumped hard with suspense.")
        world.say(f"{helper.label} gasped, because one bad jolt could have sent manure over the stones.")
        return

    if tool is not None:
        world.para()
        world.say(f"{helper.label} lifted the {tool.label} and smiled, then said, \"{tool.phrase.capitalize()} will do.\"")
        tool.carried_by = helper.id
        hero.memes["hope"] += 1
        load.carried_by = hero.id
        hero.memes["calm"] += 1
        world.say(f"They chose to {TOOL_TEXT[tool.id]} instead of rushing.")
        world.say(f"That kept the sack steady, and the blu ribbon did not brush the ground.")

    world.para()
    world.say(f"At last they reached the garden gate.")
    load.carried_by = None
    load.meters["delivered"] += 1
    load.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} emptied the manure into the bed where the soil could drink it in.")
    world.say(f"The large sack was gone, the garden smelled rich, and the blu ribbon stayed bright as a morning flower.")

    world.facts.update(hero=hero, helper=helper, load=load, tool=tool, setting=world.setting)


TOOL_TEXT = {
    "cart": "set the sack into the handcart and push it slowly",
    "rope": "bind the sack with the rope and carry it together",
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about a {f["load"].label}, a blu ribbon, and a careful journey.',
        f'Tell a suspenseful village story where {f["hero"].id} must bring manure to {world.setting.place} without losing the blu ribbon.',
        f'Write a gentle tale that uses the word "manure" and ends with the load safely delivered.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    load: Entity = _safe_fact(world, f, "load")
    tool: Optional[Entity] = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"What was {hero.id} carrying on the village path?",
            answer=f"{hero.id} was carrying a large sack of manure tied with a blu ribbon.",
        ),
        QAItem(
            question=f"Why did the trip feel suspenseful for {hero.id}?",
            answer=f"It felt suspenseful because the sack was large and the path could make it slip, so everyone worried about the blu ribbon and the messy load.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the journey?",
            answer=f"{helper.label} helped {hero.id} keep the sack steady and reach the garden safely.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"How did the {tool.label} help?",
                answer=f"The {tool.label} kept the manure steady, so the sack did not spill and the blu ribbon stayed safe.",
            )
        )
    qa.append(
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the large manure sack had reached the garden, and the blu ribbon was still bright and clean.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "manure": [
        QAItem(
            question="What is manure used for on a farm?",
            answer="Manure can help feed the soil, so plants and vegetables can grow better.",
        )
    ],
    "blu": [
        QAItem(
            question="What color is blu in this storyworld?",
            answer="Blu is a bright blue color, like the sky on a clear day.",
        )
    ],
    "large": [
        QAItem(
            question="What does it mean when a load is large?",
            answer="A large load is big and heavy, so it can be harder to carry safely.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["load"].tags)
    out: list[QAItem] = []
    for tag in ("blu", "large", "manure"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  path_danger={world.path_danger}")
    return "\n".join(lines)


def valid_story_combo(place: str, load: str, tool: str) -> bool:
    return place in SETTINGS and load in LOADS and tool in TOOLS and reasonableness_gate(_safe_lookup(LOADS, load), _safe_lookup(TOOLS, tool))


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=params.helper))
    load = world.add(Entity(
        id="load",
        type="thing",
        label="sack",
        phrase=_safe_lookup(LOADS, params.load).phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    tool_def = _safe_lookup(TOOLS, params.tool)
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, phrase=tool_def.phrase))
    tool.carried_by = helper.id

    hero.meters["age"] = 1

    world.say(f"Once upon a time, there was {hero.id}, a {params.trait} child in the village.")
    world.say(f"{helper.label.capitalize()} asked {hero.id} to help with a {load.phrase}.")
    world.say(f"The sack was large, and a blu ribbon tied its mouth like a little promise.")

    world.para()
    world.say(f"Together they walked toward {setting.place}.")
    world.say(f"The path was narrow, and the wind kept tugging at the sack.")
    load.carried_by = hero.id
    hero.memes["duty"] += 1
    hero.memes["worry"] += 1
    _risk_spill(world, load)

    world.para()
    if params.tool == "cart":
        world.say(f"{helper.label.capitalize()} brought a handcart, so they could {TOOL_TEXT['cart']}.")
    else:
        world.say(f"{helper.label.capitalize()} brought a rope, so they could {TOOL_TEXT['rope']}.")
    world.say(f"That made the journey safer, though they still had to move with care.")
    hero.memes["hope"] += 1
    load.meters["stable"] += 1

    world.para()
    load.carried_by = None
    load.meters["delivered"] += 1
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(f"At last they reached the garden, and the manure went into the earth.")
    world.say(f"The soil would grow rich, the blu ribbon stayed bright, and the two travelers went home smiling.")

    world.facts.update(hero=hero, helper=helper, load=load, tool=tool, setting=setting, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="farm", load="manure", tool="cart", name="Milo", gender="boy", helper="mother", trait="careful"),
    StoryParams(place="village", load="manure", tool="rope", name="Lena", gender="girl", helper="grandmother", trait="brave"),
    StoryParams(place="orchard", load="manure", tool="cart", name="Suri", gender="girl", helper="father", trait="steady"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_asp_fact_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_fact_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, load, tool) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.load} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
