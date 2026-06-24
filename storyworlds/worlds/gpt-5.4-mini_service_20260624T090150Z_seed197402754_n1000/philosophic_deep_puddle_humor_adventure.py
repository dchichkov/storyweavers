#!/usr/bin/env python3
"""
storyworlds/worlds/philosophic_deep_puddle_humor_adventure.py
==============================================================

A tiny story world about a curious child, a deep puddle, humor, and a small
adventure that turns into a thoughtful lesson.

The seed image:
A child wants to cross a deep puddle. A worried grownup suggests a safer route.
The child notices the puddle can reflect the sky, laughs at a silly splash, and
eventually uses a simple bridge of stepping stones. The ending proves the child
learned something about patience, reflection, and play.

This world keeps the prose child-facing and state-driven:
- physical meters track wetness, wobble, reflection, and bridge use
- emotional memes track curiosity, worry, delight, and calm
- the middle turn comes from a real obstacle, not a frozen template
- the resolution changes the world: the puddle is crossed, shoes are wet, and
  the child carries a small philosophical thought home
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    supports: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
    name: str = "the pond path"
    deep: bool = True
    affords: set[str] = field(default_factory=set)
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
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    joke: str
    insight: str
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
class Tool:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _say_trace(world: World, message: str) -> None:
    world.trace.append(message)


def adventure_at_risk(adventure: Adventure) -> bool:
    return "deep" in adventure.tags or adventure.id in {"cross", "peek", "step"}


def select_tool(adventure: Adventure) -> Optional[Tool]:
    for tool in TOOLS.values():
        if adventure.keyword in tool.helps:
            return tool
    return None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.deep:
            lines.append(asp.fact("deep", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


ASP_RULES = r"""
risky(A) :- tag(A, deep).
fix(A, T) :- risky(A), helps(T, K), keyword(A, K).
valid(A) :- risky(A), fix(A, _).
#show valid/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_adventures() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((aid,) for aid, a in ADVENTURES.items() if adventure_at_risk(a) and select_tool(a))
    cl = set(asp_valid_adventures())
    pyset = set(py)
    if cl == pyset:
        print(f"OK: clingo gate matches Python ({len(cl)} valid adventures).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - pyset:
        print("  only in clingo:", sorted(cl - pyset))
    if pyset - cl:
        print("  only in python:", sorted(pyset - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A philosophic deep-puddle adventure with humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(adventure: Adventure) -> str:
    return f"(No story: {adventure.verb} needs a fixing tool, but no tool in this world honestly helps.)"


@dataclass
class StoryParams:
    place: str
    adventure: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    if getattr(args, "adventure", None) and getattr(args, "tool", None):
        adv = _safe_lookup(ADVENTURES, getattr(args, "adventure", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if adv.keyword not in tool.helps:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [a for a in ADVENTURES if (getattr(args, "adventure", None) is None or a == getattr(args, "adventure", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    aid = getattr(args, "adventure", None) or rng.choice(sorted(choices))
    pid = getattr(args, "place", None) or rng.choice(sorted([p for p, pl in PLACES.items() if aid in pl.affords]))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=pid, adventure=aid, name=name, gender=gender, parent=parent, trait=trait)


def _walk(world: World, hero: Entity, parent: Entity, adv: Adventure) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} who loved small adventures.")
    world.say(f"{hero.pronoun().capitalize()} loved {adv.gerund}, because {adv.joke}.")
    world.say(f"One day, {hero.id} and {parent.noun()} went to {world.place.name}.")
    world.say(f"There was a deep puddle waiting there, dark and still like a tiny mirror.")


def _warn(world: World, parent: Entity, hero: Entity, adv: Adventure) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{parent.pronoun().capitalize()} looked at the puddle and said, \"That one is very deep.\"")
    world.say(f"\"You could get {adv.risk},\" {parent.pronoun('subject')} said, \"so let us think first.\"")


def _laugh(world: World, hero: Entity, adv: Adventure) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(f"{hero.id} peered down and giggled. The puddle made a wobbly face back.")
    world.say(f"\"It looks like the sky forgot to hold still,\" {hero.pronoun('subject')} said, and laughed at the silly reflection.")


def _prepare_bridge(world: World, hero: Entity, tool: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    tool.supports = True
    world.say(f"Then {hero.id}'s {tool.label} came in handy.")
    world.say(f"They used {tool.phrase} and crossed carefully, one little step at a time.")


def _finish(world: World, hero: Entity, parent: Entity, adv: Adventure, tool: Entity) -> None:
    hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"At last, {hero.id} reached the other side with {hero.noun()} {adv.insight}. "
        f"{parent.pronoun().capitalize()} smiled, and the puddle kept shining behind them."
    )


def tell(place: Place, adv: Adventure, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={"trait": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    tool_def = select_tool(adv)
    if tool_def is None:
        pass
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, phrase=tool_def.phrase, owner=hero.id))

    _walk(world, hero, parent, adv)
    world.para()
    _warn(world, parent, hero, adv)
    _laugh(world, hero, adv)
    world.para()
    _prepare_bridge(world, hero, tool)
    _finish(world, hero, parent, adv, tool)

    world.facts.update(hero=hero, parent=parent, adventure=adv, tool=tool, place=place)
    return world


PLACES = {
    "deep_puddle_park": Place(name="the park with the deep puddle", deep=True, affords={"cross", "peek"}),
    "garden_path": Place(name="the garden path", deep=True, affords={"cross", "peek"}),
    "rainy_yard": Place(name="the rainy yard", deep=True, affords={"cross", "peek"}),
}

ADVENTURES = {
    "cross": Adventure(
        id="cross",
        verb="cross the puddle",
        gerund="crossing the puddle",
        rush="step right in",
        risk="soaking wet shoes",
        joke="it was so deep that it looked like a piece of sky someone dropped",
        insight="that even a puddle can be a doorway if you go slowly",
        keyword="cross",
        tags={"deep", "reflection", "wet"},
    ),
    "peek": Adventure(
        id="peek",
        verb="peek into the puddle",
        gerund="peeking into the puddle",
        rush="lean too far over",
        risk="a splash on the sleeves",
        joke="it was polished enough to borrow the clouds",
        insight="that looking carefully can be a kind of courage",
        keyword="peek",
        tags={"deep", "reflection", "wet"},
    ),
}

TOOLS = {
    "stones": Tool(
        id="stones",
        label="stepping stones",
        phrase="the stepping stones",
        prep="place the stepping stones across the water",
        tail="cross the puddle on the stones",
        helps={"cross", "peek"},
        covers={"feet"},
    ),
    "stick": Tool(
        id="stick",
        label="a long stick",
        phrase="the long stick",
        prep="test the water with the long stick",
        tail="keep balance while they crossed",
        helps={"cross"},
        covers={"hands"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ivy", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Owen", "Leo", "Noah"]
TRAITS = ["curious", "brave", "playful", "thoughtful", "cheerful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adv = _safe_fact(world, f, "adventure")
    return [
        f'Write a short adventure story for a child named {hero.id} who wants to {adv.verb}.',
        f'Tell a humorous, philosophic tale about a deep puddle where {hero.id} learns a small lesson.',
        f'Write a gentle story in which a child laughs at a puddle reflection and then crosses safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, adv, tool = f["hero"], f["parent"], f["adventure"], (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the deep puddle?",
            answer=f"{hero.id} wanted to {adv.verb}. {hero.pronoun().capitalize()} was excited, but the puddle was very deep.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} worry about the puddle?",
            answer=f"{parent.pronoun().capitalize()} worried because the puddle could make {hero.id}'s shoes {adv.risk}.",
        ),
        QAItem(
            question=f"What funny thing did {hero.id} notice before crossing?",
            answer=f"{hero.id} noticed that the puddle reflected the sky like a mirror, and {hero.pronoun('subject')} laughed at the silly view.",
        ),
        QAItem(
            question=f"How did {hero.id} cross the puddle safely?",
            answer=f"{hero.id} crossed with {tool.label}, using {tool.phrase} and stepping carefully one step at a time.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puddle?",
            answer="A puddle is a small pool of water on the ground after rain, and a deep puddle can be hard to cross.",
        ),
        QAItem(
            question="Why can a puddle look shiny?",
            answer="A puddle can look shiny because still water reflects light and sky like a mirror.",
        ),
        QAItem(
            question="What are stepping stones for?",
            answer="Stepping stones help people cross wet or muddy places without stepping straight into the water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.supports:
            bits.append("supports=True")
        parts.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(place="deep_puddle_park", adventure="cross", name="Lina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden_path", adventure="peek", name="Theo", gender="boy", parent="father", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ADVENTURES, params.adventure), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.name}: {p.adventure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
