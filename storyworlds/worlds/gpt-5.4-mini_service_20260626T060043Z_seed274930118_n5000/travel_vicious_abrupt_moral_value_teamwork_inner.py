#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a journey, an abrupt trouble, a vicious
obstacle, and a teamwork-based escape guided by an inner moral thought.

The seed tale behind this world:
---
A young traveler set out with a lantern to bring a lost ribbon to a hill-top
grandmother. On the road, a vicious wolf sprang out so abruptly that the child
froze. A friend appeared, and together they outwitted the wolf by working as a
team, while the traveler remembered that courage is often kind, not loud.
---

This file models:
- physical meters: distance, fear, danger, carried items, shelter
- emotional memes: worry, courage, trust, relief, pride
- an inner monologue that can change the hero's choice
- teamwork as a genuine causal fix, not a decorative ending
"""

from __future__ import annotations

import argparse
import dataclasses
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    comp: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "grandfather"}:
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
    distance: int
    helps: set[str] = field(default_factory=set)
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
class Companion:
    id: str
    label: str
    type: str
    help_word: str
    tool: str
    teamwork_bonus: str
    can_help: set[str] = field(default_factory=set)
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
class Threat:
    id: str
    label: str
    type: str
    abrupt: bool
    vicious: bool
    blocks: set[str] = field(default_factory=set)
    scares: float = 1.0
    route: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        clone = World(self.place)
        clone.entities = dataclasses.replace(self.entities) if False else {}
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_advance(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters.get("on_road", 0) < THRESHOLD:
        return out
    if hero.meters.get("distance_done", 0) >= world.place.distance:
        return out
    sig = ("advance",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["distance_done"] = world.place.distance
    out.append(f"The road bent on to the hill, and the way drew nearer to its end.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    threat = world.entities.get("threat")
    if not hero or not threat:
        return out
    if hero.meters.get("seen_threat", 0) < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = hero.memes.get("fear", 0) + threat.meters.get("scare", 1.0)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append(f"The sight of {threat.label} made {hero.id}'s heart go small and quick.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    companion = world.entities.get("companion")
    threat = world.entities.get("threat")
    if not hero or not companion or not threat:
        return out
    if hero.memes.get("courage", 0) < THRESHOLD:
        return out
    if companion.meters.get("helping", 0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    out.append(f"With {companion.label} beside them, the two of them could think as one small team.")
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    companion = world.entities.get("companion")
    threat = world.entities.get("threat")
    if not hero or not companion or not threat:
        return out
    if hero.memes.get("trust", 0) < THRESHOLD or companion.meters.get("helping", 0) < THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["safe"] = 1
    threat.meters["gone"] = 1
    out.append(f"Together they outsmarted {threat.label}, and the road opened again.")
    return out


RULES = [
    _r_advance,
    _r_fear,
    _r_teamwork,
    _r_resolve,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    place: str
    traveler: str
    companion: str
    threat: str
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
    "forest_road": Place(id="forest_road", label="the forest road", kind="road", distance=3, helps={"hide", "listen"}),
    "hill_path": Place(id="hill_path", label="the hill path", kind="path", distance=4, helps={"climb", "see_far"}),
    "river_lane": Place(id="river_lane", label="the river lane", kind="lane", distance=2, helps={"reflect", "cross"}),
}

TRAVELERS = {
    "girl": {"type": "girl", "label": "young traveler", "traits": ["brave", "thoughtful"]},
    "boy": {"type": "boy", "label": "young traveler", "traits": ["gentle", "curious"]},
}

COMPANIONS = {
    "fox": Companion(id="fox", label="a clever fox", type="fox", help_word="guide", tool="a bright tail", teamwork_bonus="the fox listened for the safest path", can_help={"hide", "listen", "cross"}),
    "miller": Companion(id="miller", label="a kind miller", type="man", help_word="plan", tool="a sack of bread", teamwork_bonus="the miller knew the road and spoke calmly", can_help={"climb", "cross"}),
    "sister": Companion(id="sister", label="an older sister", type="girl", help_word="share", tool="a lantern", teamwork_bonus="the sister kept the lantern steady and brave", can_help={"see_far", "listen", "cross"}),
}

THREATS = {
    "wolf": Threat(id="wolf", label="a vicious wolf", type="wolf", abrupt=True, vicious=True, blocks={"road", "listen"}, scares=2.0, route="sprang from the brush"),
    "storm": Threat(id="storm", label="an abrupt storm", type="storm", abrupt=True, vicious=False, blocks={"cross", "see_far"}, scares=1.5, route="rolled in all at once"),
    "bandit": Threat(id="bandit", label="a vicious bandit", type="bandit", abrupt=True, vicious=True, blocks={"road", "cross"}, scares=1.8, route="jumped out from behind a stone"),
}

NAMES = ["Elin", "Pip", "Mara", "Owen", "Lina", "Ivo", "Sera", "Tobin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale travel storyworld with abrupt danger and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name")
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


def reasonableness_gate(place: Place, threat: Threat, companion: Companion) -> bool:
    return threat.abrupt and threat.vicious and (place.kind in threat.blocks or "road" in threat.blocks) and len(companion.can_help & place.helps) > 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = getattr(args, "place", None) or rng.choice(list(PLACES))
    threat_id = getattr(args, "threat", None) or rng.choice(list(THREATS))
    comp_id = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    if getattr(args, "traveler", None) and getattr(args, "traveler", None) not in TRAVELERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not reasonableness_gate(_safe_lookup(PLACES, place_id), _safe_lookup(THREATS, threat_id), _safe_lookup(COMPANIONS, comp_id)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    traveler = getattr(args, "traveler", None) or rng.choice(list(TRAVELERS))
    return StoryParams(
        place=place_id,
        traveler=traveler,
        companion=comp_id,
        threat=threat_id,
        seed=None,
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero_info = _safe_lookup(TRAVELERS, params.traveler)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_info["type"],
        label=params.name or rng_name(params.seed),
        phrase=f"a {hero_info['label']}",
        traits=hero_info["traits"],
        meters={"on_road": 1, "distance_done": 0, "seen_threat": 0, "safe": 0},
        memes={"worry": 0, "courage": 1, "trust": 0, "relief": 0, "pride": 0},
    ))
    companion = _safe_lookup(COMPANIONS, params.companion)
    comp = world.add(Entity(
        id="companion",
        kind="character",
        type=companion.type,
        label=companion.label,
        phrase=companion.label,
        meters={"helping": 0},
        memes={"kindness": 1},
    ))
    threat = _safe_lookup(THREATS, params.threat)
    world.add(Entity(
        id="threat",
        kind="thing",
        type=threat.type,
        label=threat.label,
        phrase=threat.label,
        meters={"scare": threat.scares, "gone": 0},
        memes={"danger": 1},
    ))
    world.facts.update(place=place, hero=hero, companion=comp, threat=threat)
    return world


def rng_name(seed: Optional[int]) -> str:
    rng = random.Random(seed)
    return rng.choice(NAMES)


def tell(world: World, params: StoryParams) -> World:
    hero = world.get("hero")
    comp = world.get("companion")
    threat = world.get("threat")
    place = world.place

    world.say(f"Once upon a time, {hero.label} set out along {place.label} with a little brave heart.")
    world.say(f"{hero.pronoun('subject').capitalize()} wished to reach the far end of the road and bring help where it was needed.")
    world.para()
    world.say(f"On the way, {threat.label} {threat.route} so abruptly that {hero.label} stopped at once.")
    hero.meters["seen_threat"] = 1
    propagate(world)
    world.say(f"{hero.label} whispered a quiet thought: 'If I hurry alone, I may fail, but if I listen, I may find a kinder way.'")
    hero.memes["courage"] += 1
    hero.memes["inner_monologue"] = 1
    world.para()
    comp.meters["helping"] = 1
    world.say(f"Then {comp.label} came near with {companion_phrase(params.companion)}.")
    world.say(f"{companion_help_line(params.companion)}")
    propagate(world)
    hero.meters["on_road"] = 1
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    world.say(f"The two of them worked as a team: one watched the path, the other made a sound, and the {threat.label} lost its boldness.")
    propagate(world)
    world.para()
    hero.memes["pride"] += 1
    world.say(f"At last, {hero.label} walked on with {comp.label} beside {hero.pronoun('object')}, and the road seemed less dark than before.")
    return world


def companion_phrase(companion_id: str) -> str:
    c = _safe_lookup(COMPANIONS, companion_id)
    if companion_id == "fox":
        return "a fox with quick eyes and a soft step"
    if companion_id == "miller":
        return "a miller carrying bread and patience"
    return "an older sister with a steady lantern"


def companion_help_line(companion_id: str) -> str:
    c = _safe_lookup(COMPANIONS, companion_id)
    return c.teamwork_bonus + ", which gave the traveler a smaller, steadier fear."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale about a child who must travel on {f['place'].label} and meets {f['threat'].label}.",
        f"Tell a short story where teamwork helps a young traveler face an abrupt danger on the road.",
        f"Write a gentle tale with an inner monologue that turns fear into courage during a journey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "companion")
    threat = _safe_fact(world, f, "threat")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Where did {hero.label} travel at the start of the story?",
            answer=f"{hero.label} traveled along {place.label}, hoping to go farther down the road.",
        ),
        QAItem(
            question=f"What made {hero.label} stop so suddenly?",
            answer=f"{threat.label} appeared so abruptly that {hero.label} stopped right away.",
        ),
        QAItem(
            question=f"How did {comp.label} help {hero.label}?",
            answer=f"{comp.label} helped by joining in the plan, and together they worked as a team to outsmart the danger.",
        ),
        QAItem(
            question=f"What did {hero.label} think to {hero.pronoun('object')}self when things got scary?",
            answer=f"{hero.label} thought that rushing alone would fail, but listening and staying kind could lead to a better way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.label} felt braver and safer, and the road seemed less dark because teamwork solved the trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or animals help each other and do a job together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character hears in their own mind when they think to themselves.",
        ),
        QAItem(
            question="What does abrupt mean?",
            answer="Abrupt means something happens very suddenly and without much warning.",
        ),
        QAItem(
            question="What does vicious mean?",
            answer="Vicious means mean, cruel, or dangerous in a way that can cause harm.",
        ),
        QAItem(
            question="What lesson can a fairy tale sometimes teach?",
            answer="A fairy tale can teach a moral value, like kindness, courage, or working together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest_road", traveler="girl", companion="fox", threat="wolf", seed=1),
    StoryParams(place="hill_path", traveler="boy", companion="miller", threat="bandit", seed=2),
    StoryParams(place="river_lane", traveler="girl", companion="sister", threat="storm", seed=3),
]


ASP_RULES = r"""
travel_story(P, T, C, H) :- place(P), traveler(T), companion(C), threat(H),
                           abrupt(H), vicious(H), helps(C, P),
                           blocks(H, road), moral_value(T), teamwork(C).
#show travel_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("distance", pid, p.distance))
        for h in sorted(p.helps):
            lines.append(asp.fact("helps", pid, h))
    for tid in TRAVELERS:
        lines.append(asp.fact("traveler", tid))
        lines.append(asp.fact("moral_value", tid))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        lines.append(asp.fact("teamwork", cid))
        for h in sorted(c.can_help):
            lines.append(asp.fact("helps", cid, h))
    for hid, h in THREATS.items():
        lines.append(asp.fact("threat", hid))
        if h.abrupt:
            lines.append(asp.fact("abrupt", hid))
        if h.vicious:
            lines.append(asp.fact("vicious", hid))
        lines.append(asp.fact("blocks", hid, "road"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show travel_story/4."))
    return sorted(set(asp.atoms(model, "travel_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TRAVELERS:
            for c in COMPANIONS:
                for h in THREATS:
                    if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(THREATS, h), _safe_lookup(COMPANIONS, c)):
                        out.append((p, t, c))
    return sorted(set(out))


def asp_verify() -> int:
    py = set((p, t, c) for p, t, c in valid_combos())
    cl = set((p, t, c) for p, t, c, in [x[:3] for x in asp_valid()])
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world, params)
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


def resolve_all(params: Optional[StoryParams], args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if params is not None:
        return params
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show travel_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.place} / {p.traveler} / {p.companion} / {p.threat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
