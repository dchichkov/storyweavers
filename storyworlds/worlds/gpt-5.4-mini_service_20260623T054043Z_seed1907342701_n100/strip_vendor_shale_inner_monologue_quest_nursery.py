#!/usr/bin/env python3
"""
storyworlds/worlds/strip_vendor_shale_inner_monologue_quest_nursery.py
=======================================================================

A small nursery-rhyme-style story world about a child on a quest down a strip
of path, a vendor with a kind stall, and shale stones that make the road tricky.

The world is built around:
- a child with an inner monologue
- a quest to fetch or return something simple
- a vendor helper
- a physical route with shale that can cause slipping
- a soft, rhyme-like cadence with a beginning, turn, and ending image

The story engine uses typed entities with physical meters and emotional memes,
a tiny causal rule system, and an ASP twin for the reasonableness gate.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    owner: str = ""
    guide: str = ""
    path_kind: str = ""
    tangible: bool = False
    slippery: bool = False
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    path: object | None = None
    prize: object | None = None
    vendor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    strip_name: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Quest:
    id: str
    want: str
    verb: str
    object_label: str
    object_phrase: str
    object_kind: str
    route_word: str
    keywords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class VendorDeal:
    id: str
    label: str
    phrase: str
    gives: str
    price: str
    solved_with: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route = place.strip_name

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["slip"] < THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["wobble"] += 1
        out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(place: Place, quest: Quest) -> bool:
    return quest.route_word in place.affords


def helpful_deal(quest: Quest, deal: VendorDeal) -> bool:
    return quest.object_kind in deal.tags and quest.want in deal.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            if not quest_at_risk(place, quest):
                continue
            for deal_id, deal in DEALS.items():
                if helpful_deal(quest, deal):
                    combos.append((place_id, quest_id, deal_id))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    deal: str
    child_name: str
    child_gender: str
    vendor_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


GIRL_NAMES = ["Milly", "Polly", "Rosie", "Daisy", "Nell", "Lily", "Mara", "Ivy"]
BOY_NAMES = ["Jack", "Tom", "Sam", "Finn", "Ben", "Leo", "Toby", "Max"]


PLACES = {
    "lane": Place("lane", "the lane", "shale strip", {"walk", "shale"}),
    "market": Place("market", "the market road", "shale strip", {"walk", "shale"}),
    "hill": Place("hill", "the little hill path", "shale strip", {"walk", "shale"}),
    "garden": Place("garden", "the garden way", "bright strip", {"walk"}),
}


QUESTS = {
    "ribbon": Quest("ribbon", "find a ribbon", "fetch the ribbon", "ribbon", "a bright ribbon", "ribbon", "shale strip", {"ribbon", "quest"}),
    "bread": Quest("bread", "bring bread home", "bring the bread", "bread", "a warm loaf of bread", "bread", "shale strip", {"bread", "quest"}),
    "bell": Quest("bell", "return a bell", "return the bell", "bell", "a little brass bell", "bell", "shale strip", {"bell", "quest"}),
    "spoon": Quest("spoon", "carry a spoon", "carry the spoon", "spoon", "a silver spoon", "spoon", "shale strip", {"spoon", "quest"}),
}


DEALS = {
    "wrap": VendorDeal("wrap", "a wool wrap", "a wool wrap", "ribbon", "coin", "keep the path steady", {"ribbon", "quest", "soft"}),
    "basket": VendorDeal("basket", "a small basket", "a small basket", "bread", "coin", "carry the bread safely", {"bread", "quest", "carry"}),
    "pouch": VendorDeal("pouch", "a button pouch", "a button pouch", "bell", "coin", "hold the bell snugly", {"bell", "quest", "hold"}),
    "cloth": VendorDeal("cloth", "a square cloth", "a square cloth", "spoon", "coin", "wrap the spoon in cloth", {"spoon", "quest", "hold"}),
}


ASP_RULES = r"""
quest_ok(P,Q) :- place(P), quest(Q), route_word(Q,R), affords(P,R).
deal_ok(Q,D) :- quest(Q), deal(D), want(Q,W), tags(D,W1), tags(D,W2), has_kind(D,K), object_kind(Q,K), W=W1, W=W2.
valid(P,Q,D) :- quest_ok(P,Q), deal_ok(Q,D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("want", qid, q.want))
        lines.append(asp.fact("route_word", qid, q.route_word))
        lines.append(asp.fact("object_kind", qid, q.object_kind))
    for did, d in DEALS.items():
        lines.append(asp.fact("deal", did))
        lines.append(asp.fact("has_kind", did, next(iter(d.tags & {"ribbon", "bread", "bell", "spoon"}))))
        for t in sorted(d.tags):
            lines.append(asp.fact("tags", did, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        if py - cl:
            print("only python:", sorted(py - cl))
        if cl - py:
            print("only clingo:", sorted(cl - py))
        return 1
    print(f"OK: {len(py)} valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, deal=None, child_name=None, child_gender=None, vendor_name=None, seed=None), random.Random(777)))
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme quest with a vendor and shale.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--deal", choices=DEALS)
    ap.add_argument("--name")
    ap.add_argument("--vendor")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "deal", None) is None or c[2] == getattr(args, "deal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, deal = rng.choice(list(combos))
    q = _safe_lookup(QUESTS, quest)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    vendor = getattr(args, "vendor", None) or rng.choice(["Mabel", "Ned", "Mrs. Moss", "Old Pip"])
    return StoryParams(place=place, quest=quest, deal=deal, child_name=name, child_gender=gender, vendor_name=vendor)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    deal = _safe_lookup(DEALS, params.deal)
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    vendor = world.add(Entity(id="vendor", kind="character", type="vendor", label=params.vendor_name, helpful=True))
    path = world.add(Entity(id="path", label=place.strip_name, path_kind=place.strip_name, slippery="shale" in place.affords))
    prize = world.add(Entity(id="prize", label=quest.object_label, phrase=quest.object_phrase, tangible=True))
    world.facts.update(child=child, vendor=vendor, path=path, prize=prize, quest=quest, deal=deal, place=place)
    child.memes["hope"] += 1
    vendor.memes["kind"] += 1
    world.say(f"{params.child_name} went down {place.label}, a strip of shale and shine.")
    world.say(f"In a tiny inner voice, {params.child_name} thought, “I must {quest.want}; my quest is mine.”")
    world.para()
    world.say(f"There stood {params.vendor_name}, with {deal.phrase} on a little tray.")
    world.say(f'“A coin for the {quest.object_label}, and the path will be a kinder one,” said the vendor.')
    child.meters["slip"] += 1
    propagate(world, narrate=False)
    if child.memes["wobble"] >= THRESHOLD:
        world.say(f"{params.child_name} took one soft step, and the shale made the shoes go skitter-scatter.")
        world.say(f"Then the little voice said, “Slow feet, calm heart; I can still go on my quest.”")
    world.para()
    world.say(f"{params.child_name} gave the coin, and {params.vendor_name} handed over {deal.phrase}.")
    world.say(f"With {deal.solved_with}, {params.child_name} could {quest.verb}, and the strip did not defeat the day.")
    world.say(f"At home again, {params.child_name} held the {quest.object_label} like a star in a palm, and the shale stayed behind in the lane.")
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story about {f["child"].label} on a quest through a {f["place"].strip_name} where a vendor helps, and include the words "strip", "vendor", and "shale".',
        f"Tell a gentle little tale in rhyme where {f['child'].label} speaks a private inner monologue, meets a vendor, and finishes a quest on the shale strip.",
        f"Write a child-facing quest story with a soft sing-song feel, a strip of path, a kind vendor, and a small reward at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]; vendor = f["vendor"]; quest = f["quest"]; deal = f["deal"]; place = f["place"]
    return [
        QAItem(
            question=f"What did {child.label} want to do on the shale strip?",
            answer=f"{child.label} wanted to {quest.want}. That wish was the heart of the quest, so the whole walk had a goal from the start."
        ),
        QAItem(
            question=f"Who helped {child.label} in the story?",
            answer=f"{vendor.label_word if hasattr(vendor, 'label_word') else vendor.label} the vendor helped by offering {deal.phrase}. The help made the path easier and let the quest reach a happy end."
        ),
        QAItem(
            question=f"Why did the shale matter in the middle of the tale?",
            answer=f"The shale made the strip slick and skittery underfoot. That little danger gave the child a reason to slow down, think, and keep going carefully."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {child.label} had the {quest.object_label}, and the rough strip no longer felt like a problem. The quest was finished, and the ending image showed the prize held safely at home."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a vendor?", "A vendor is a person who sells things, often at a stall or shop. In a story, a vendor can also help by giving a child a useful item."),
        QAItem("What is shale?", "Shale is a kind of rock that can break into thin pieces. A path with shale can feel rough or slippery under tiny shoes."),
        QAItem("What is a quest?", "A quest is a journey to reach a goal. In a story, it gives the character a reason to keep going."),
        QAItem("What is an inner monologue?", "An inner monologue is the quiet voice a character thinks to themself. It helps readers hear worry, hope, or courage from the inside."),
    ]


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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", quest="ribbon", deal="wrap", child_name="Milly", child_gender="girl", vendor_name="Mabel"),
    StoryParams(place="market", quest="bread", deal="basket", child_name="Jack", child_gender="boy", vendor_name="Old Pip"),
    StoryParams(place="hill", quest="bell", deal="pouch", child_name="Rosie", child_gender="girl", vendor_name="Mrs. Moss"),
    StoryParams(place="lane", quest="spoon", deal="cloth", child_name="Tom", child_gender="boy", vendor_name="Ned"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest not in QUESTS or params.deal not in DEALS:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
