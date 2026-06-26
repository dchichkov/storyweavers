#!/usr/bin/env python3
"""
A standalone storyworld for a small mythic tale of alls, jag, and harm.

Premise:
A young seeker and a trusted friend travel to a shrine with an old promise.
A jagged relic in the path foreshadows danger. Suspense rises as a hidden harm
threatens the little caravan, and friendship turns the ending toward safety.

The world is built as a tiny state machine:
- characters have meters and memes
- the relic can be jagged and harmful
- a friend can notice foreshadowing and help
- the resolution changes the physical and emotional state of the world
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

FORESHADOW_THRESHOLD = 1.0
HARM_THRESHOLD = 1.0
JAG_THRESHOLD = 1.0



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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    is_jagged: bool = False
    is_harmful: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    charm: object | None = None
    friend: object | None = None
    hero: object | None = None
    relic: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    mood: str
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
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    danger: str
    guards: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def worn(self, hero: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == hero.id and e.carried_by == hero.id]

    def protected(self, hero: Entity, region: str) -> bool:
        return any(e.protective and region in getattr(e, "covers", set()) for e in self.worn(hero))

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seeker_type: str
    friend_type: str
    relic: str
    charm: str
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
    "ruin": Place(name="the hill ruin", mood="old", supports={"walk", "seek"}),
    "grove": Place(name="the moon grove", mood="quiet", supports={"walk", "seek"}),
    "cave": Place(name="the echo cave", mood="shadowy", supports={"walk", "seek"}),
}

RELICS = {
    "jag": Relic(
        id="jag",
        label="a jagged shard",
        phrase="a jagged shard of black stone",
        region="path",
        danger="harm",
        guards={"feet", "hands"},
    ),
    "blade": Relic(
        id="blade",
        label="a jagged blade",
        phrase="a jagged blade left by old giants",
        region="path",
        danger="harm",
        guards={"feet"},
    ),
    "thorn": Relic(
        id="thorn",
        label="a jagged thorn",
        phrase="a jagged thorn from a thorny vine",
        region="path",
        danger="harm",
        guards={"hands"},
    ),
}

CHARMS = {
    "wrap": Charm(
        id="wrap",
        label="a soft wrap",
        phrase="a soft wrap for safe steps",
        guards={"harm"},
        covers={"feet"},
    ),
    "gloves": Charm(
        id="gloves",
        label="woven gloves",
        phrase="woven gloves for careful hands",
        guards={"harm"},
        covers={"hands"},
    ),
    "sandals": Charm(
        id="sandals",
        label="wooden sandals",
        phrase="wooden sandals for the path",
        guards={"harm"},
        covers={"feet"},
    ),
}

TRAITS = ["brave", "gentle", "curious", "wise", "patient", "swift"]
BOY_NAMES = ["Ari", "Niko", "Taro", "Eli", "Milo", "Jon", "Soren", "Kian"]
GIRL_NAMES = ["Lina", "Mira", "Aya", "Nera", "Ola", "Tiva", "Sela", "Rina"]


class InvalidStory(StoryError):
    pass


def reasonableness_gate(place: Place, relic: Relic, charm: Charm) -> bool:
    return relic.danger in charm.guards and (
        (relic.region == "path" and any(region in charm.covers for region in {"feet", "hands"}))
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("danger_of", rid, r.danger))
        lines.append(asp.fact("region_of", rid, r.region))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
        for cov in sorted(c.covers):
            lines.append(asp.fact("covers", cid, cov))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(R) :- relic(R), danger_of(R, harm).
compatible(C, R) :- charm(C), at_risk(R), guards(C, harm), region_of(R, path), covers(C, feet).
compatible(C, R) :- charm(C), at_risk(R), guards(C, harm), region_of(R, path), covers(C, hands).
valid_story(P, R, C) :- place(P), relic(R), charm(C), compatible(C, R), supports(P, seek).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for rid, relic in RELICS.items():
            for cid, charm in CHARMS.items():
                if place.supports and reasonableness_gate(place, relic, charm):
                    out.append((pid, rid, cid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: foreshadowing, friendship, suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "relic", None):
        combos = [c for c in combos if c[1] == getattr(args, "relic", None)]
    if getattr(args, "charm", None):
        combos = [c for c in combos if c[2] == getattr(args, "charm", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if gender == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    return StoryParams(
        place=place,
        hero=name,
        friend=friend_name,
        seeker_type=gender,
        friend_type=friend_gender,
        relic=relic,
        charm=charm,
    )


def _meet(world: World, hero: Entity, friend: Entity, relic: Entity, charm: Entity) -> None:
    world.say(f"Long ago, {hero.id} and {friend.id} came to {world.place.name} together.")
    world.say(f"They had heard of {relic.phrase}, and the old tale said it could bring harm to careless feet.")
    world.say(f"Still, {hero.id} carried {charm.phrase}, because wise travelers liked to be ready.")


def _foreshadow(world: World, hero: Entity, friend: Entity, relic: Entity) -> None:
    hero.memes["foreshadowing"] += 1
    friend.memes["foreshadowing"] += 1
    world.say(f"At the gate, {friend.id} noticed a broken sign and a whisper of dust on the stones.")
    world.say(f'"That path looks jagged," {friend.id} said softly, as if the place itself was warning them.')


def _suspense(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(f"{hero.id} stepped closer, and the silence grew deep enough to hear a leaf turn.")
    world.say(f"The jagged shard waited where the path bent, and no one could yet see whether it hid harm.'")


def _harm_check(world: World, hero: Entity, relic: Entity) -> None:
    if world.protected(hero, "feet") and "feet" in world.get(hero.id).meters:
        return
    sig = ("harm", hero.id, relic.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["harm"] = hero.meters.get("harm", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"The shard could have cut {hero.id}'s feet, and the thought made the air feel sharp.")


def _friendship_turn(world: World, hero: Entity, friend: Entity, charm: Entity, relic: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    charm.carried_by = hero.id
    charm.owner = hero.id
    world.say(f"Then {friend.id} knelt and tied the {charm.label} on {hero.id}'s feet with steady hands.")
    world.say(f'"We walk together," {friend.id} said. "That is how travelers beat harm."')


def _resolution(world: World, hero: Entity, friend: Entity, relic: Entity) -> None:
    hero.memes["suspense"] = 0.0
    hero.memes["fear"] = 0.0
    hero.meters["safe"] = 1.0
    world.say(f"So {hero.id} crossed the jagged place safely, and {friend.id} walked beside them all the way.")
    world.say(f"At the end, the shard stayed behind, but their friendship kept the road bright.")


def tell(place: Place, relic_cfg: Relic, charm_cfg: Charm, hero_name: str, friend_name: str,
         hero_type: str, friend_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "seeking"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["loyal", "watchful"]))
    relic = world.add(Entity(id=relic_cfg.id, type="relic", label=relic_cfg.label, phrase=relic_cfg.phrase,
                             is_jagged=True, is_harmful=True))
    charm = world.add(Entity(id=charm_cfg.id, type="charm", label=charm_cfg.label, phrase=charm_cfg.phrase,
                             protective=True))
    charm.owner = hero.id
    charm.carried_by = hero.id

    _meet(world, hero, friend, relic, charm)
    world.para()
    _foreshadow(world, hero, friend, relic)
    _suspense(world, hero, relic)
    _harm_check(world, hero, relic)
    world.para()
    _friendship_turn(world, hero, friend, charm, relic)
    _resolution(world, hero, friend, relic)

    world.facts.update(hero=hero, friend=friend, relic=relic, charm=charm, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about {f["hero"].id} and {f["friend"].id} at {f["place"].name}, '
        f'where a jagged relic foreshadows harm and friendship solves the suspense.',
        f"Tell a mythic story in which {f['hero'].id} must cross a jagged place without harm, and a loyal friend helps.",
        f'Write a gentle legend using the words "alls", "jag", and "harm", with a hopeful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    relic: Entity = _safe_fact(world, f, "relic")
    charm: Entity = _safe_fact(world, f, "charm")
    return [
        QAItem(
            question=f"Who went to {world.place.name} in the story?",
            answer=f"{hero.id} went there with {friend.id} to face the old danger together.",
        ),
        QAItem(
            question=f"What sign foreshadowed the harm in the story?",
            answer=f"The broken sign, the dust on the stones, and the jagged shard all foreshadowed harm ahead.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id} stay safe?",
            answer=f"{friend.id} tied on {charm.label} and reminded {hero.id} to walk together, which kept harm away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does jagged mean?",
            answer="Jagged means having sharp, uneven points or edges.",
        ),
        QAItem(
            question="What is harm?",
            answer="Harm is damage or injury that hurts a person or thing.",
        ),
        QAItem(
            question="Why does a friend matter in a scary journey?",
            answer="A friend can watch for danger, help solve problems, and make a hard journey feel safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.is_jagged:
            bits.append("jagged=True")
        if e.is_harmful:
            bits.append("harmful=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(RELICS, params.relic),
        _safe_lookup(CHARMS, params.charm),
        params.hero,
        params.friend,
        params.seeker_type,
        params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="ruin", hero="Ari", friend="Mira", seeker_type="boy", friend_type="girl", relic="jag", charm="wrap"),
    StoryParams(place="grove", hero="Lina", friend="Jon", seeker_type="girl", friend_type="boy", relic="blade", charm="gloves"),
    StoryParams(place="cave", hero="Taro", friend="Ola", seeker_type="boy", friend_type="girl", relic="thorn", charm="sandals"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_asp_show() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
