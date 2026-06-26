#!/usr/bin/env python3
"""
Storyworld: bandana friendship myth.

A small myth-style domain about a child, a treasured bandana, and a friendship
that is tested and strengthened by a hard choice.
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
# Model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    charm_item: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "trust": 0.0, "hurt": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "nymph"}
        male = {"boy", "father", "man", "brother", "smith", "king"}
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
    vows: set[str] = field(default_factory=set)
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
class Rite:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    dust_kind: str
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
class Charm:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def protected(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shore": Setting(place="the moonlit shore", vows={"sea", "shells", "wind"}),
    "grove": Setting(place="the elder grove", vows={"trees", "wind", "song"}),
    "hill": Setting(place="the high hill", vows={"wind", "stones", "stars"}),
}

RITES = {
    "sea": Rite(
        id="sea",
        verb="sing to the sea",
        gerund="singing to the sea",
        rush="run to the waterline",
        risk="choke on salt spray",
        dust_kind="salt",
        zone={"torso", "face", "hands"},
        keyword="sea",
        tags={"sea", "salt", "water"},
    ),
    "wind": Rite(
        id="wind",
        verb="dance with the wind",
        gerund="dancing with the wind",
        rush="spin toward the cliff",
        risk="lose what they hold dear",
        dust_kind="dust",
        zone={"torso", "head"},
        keyword="wind",
        tags={"wind", "air"},
    ),
    "embers": Rite(
        id="embers",
        verb="walk through the ember path",
        gerund="walking through the ember path",
        rush="step toward the red stones",
        risk="sting their skin",
        dust_kind="ash",
        zone={"feet", "hands"},
        keyword="embers",
        tags={"ash", "fire"},
    ),
    "rain": Rite(
        id="rain",
        verb="shelter under the rain tree",
        gerund="standing under the rain tree",
        rush="run beneath the branches",
        risk="soak their cloak",
        dust_kind="wet",
        zone={"torso", "head"},
        keyword="rain",
        tags={"rain", "water"},
    ),
}

PRIZES = {
    "bandana": Prize(
        label="bandana",
        phrase="a red bandana with a bright knot",
        type="bandana",
        region="head",
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a blue cloak with a silver clasp",
        type="cloak",
        region="torso",
    ),
    "sandals": Prize(
        label="sandals",
        phrase="golden sandals",
        type="sandals",
        region="feet",
        plural=True,
    ),
    "bracelet": Prize(
        label="bracelet",
        phrase="a woven bracelet",
        type="bracelet",
        region="hands",
    ),
}

CHARMS = [
    Charm(
        id="hood",
        label="a hooded shawl",
        covers={"head", "torso"},
        wards={"wet", "salt"},
        prep="draw a hooded shawl over the bandana",
        tail="returned with the hooded shawl",
    ),
    Charm(
        id="wrap",
        label="a long wind-wrap",
        covers={"head", "torso"},
        wards={"dust", "ash"},
        prep="bind on a long wind-wrap",
        tail="came back with the wind-wrap",
    ),
    Charm(
        id="sandals_cover",
        label="soft travel wraps",
        covers={"feet"},
        wards={"ash", "wet"},
        prep="put on soft travel wraps",
        tail="came back with the travel wraps",
        plural=True,
    ),
]

GIRL_NAMES = ["Ari", "Mira", "Nia", "Lena", "Tala", "Sera"]
BOY_NAMES = ["Ivo", "Kian", "Ravi", "Niko", "Milo", "Orin"]
TRAITS = ["gentle", "brave", "curious", "steadfast", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A rite is risky for a prize when the rite reaches the prize's region.
at_risk(R, P) :- reaches(R, G), worn_on(P, G).

% A charm is a valid protection when it covers the at-risk region and wards the
% relevant hazard kind.
protects(C, R, P) :- charm(C), at_risk(R, P),
                     risk_of(R, K), wards(C, K),
                     covers(C, G), worn_on(P, G).

valid_story(Place, Rite, Prize) :- setting(Place), vows(Place, Rite),
                                  at_risk(Rite, Prize), protects(_, Rite, Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for v in sorted(s.vows):
            lines.append(asp.fact("vows", sid, v))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("risk_of", rid, r.dust_kind))
        for g in sorted(r.zone):
            lines.append(asp.fact("reaches", rid, g))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for g in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, g))
        for k in sorted(c.wards):
            lines.append(asp.fact("wards", c.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(rite: Rite, prize: Prize) -> bool:
    return prize.region in rite.zone


def select_charm(rite: Rite, prize: Prize) -> Optional[Charm]:
    for charm in CHARMS:
        if prize.region in charm.covers and rite.dust_kind in charm.wards:
            return charm
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for rite_id in setting.vows:
            rite = _safe_lookup(RITES, rite_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(rite, prize) and select_charm(rite, prize):
                    out.append((place, rite_id, prize_id))
    return out


def explain_rejection(rite: Rite, prize: Prize) -> str:
    if not prize_at_risk(rite, prize):
        return (
            f"(No story: {rite.gerund} does not reach the {prize.label} on the {prize.region}, "
            f"so there is no honest danger and no mythic warning to make.)"
        )
    return (
        f"(No story: nothing in the charm list both covers the {prize.label} and wards "
        f"{rite.dust_kind}. The friendship needs a real fix, not a pretend one.)"
    )


# ---------------------------------------------------------------------------
# World motion
# ---------------------------------------------------------------------------

def _travel_dust(world: World, actor: Entity, rite: Rite, narrate: bool = True) -> None:
    world.zone = set(rite.zone)
    actor.meters[rite.dust_kind] = actor.meters.get(rite.dust_kind, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} moved into the old way and the air answered with {rite.dust_kind}.")


def _soil_prize(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id == "friendship":
                continue
            if item.kind == "thing" and item.worn_by == actor.id and item.region in world.zone:
                if world.protected(actor, item.region):
                    continue
                if actor.meters.get("dust", 0.0) >= THRESHOLD:
                    sig = ("soil", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dust"] = item.meters.get("dust", 0.0) + 1.0
                    out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} was dulled by the dust.")
    return out


def predict_risk(world: World, actor: Entity, rite: Rite, prize_id: str) -> dict[str, object]:
    sim = world.copy()
    _travel_dust(sim, sim.get(actor.id), rite, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dust", 0.0) >= THRESHOLD}


def apply_rite(world: World, actor: Entity, rite: Rite, narrate: bool = True) -> None:
    _travel_dust(world, actor, rite, narrate=narrate)
    if narrate:
        for line in _soil_prize(world):
            world.say(line)


def tell(setting: Setting, rite: Rite, prize_cfg: Prize, hero_name: str, friend_name: str,
         hero_type: str = "girl", friend_type: str = "boy", trait: str = "gentle") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"dust": 0.0}, memes={"joy": 0.0, "fear": 0.0, "trust": 1.0, "hurt": 0.0, "resolve": 0.0}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, meters={"dust": 0.0}, memes={"joy": 0.0, "fear": 0.0, "trust": 1.0, "hurt": 0.0, "resolve": 0.0}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0

    world.say(f"In the old tale, {hero.id} was a {trait} {hero.type} and {friend.id} was {hero.pronoun('possessive')} truest friend.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}, and the two of them walked as if they shared one shadow.")
    world.para()

    world.say(f"At {setting.place}, {hero.id} longed to {rite.verb}, because {rite.keyword} called like a drum behind the hills.")
    pred = predict_risk(world, hero, rite, "prize")
    if pred["soiled"]:
        hero.memes["fear"] += 1.0
        world.say(f"{friend.id} saw the danger first and said, \"If you rush there now, your {prize.label} will be ruined.\"")
        world.say(f"{hero.id} still stepped forward, and the old place filled with {rite.risk}.")
        hero.memes["resolve"] += 1.0
        friend.memes["hurt"] += 1.0
        world.say(f"{friend.id} reached out, not to stop {hero.id}, but to keep the promise between them from breaking.")
        charm = select_charm(rite, prize)
        if charm is None:
            pass
        charm_item = world.add(Entity(
            id=charm.id, type="charm", label=charm.label, owner=friend.id, protective=True,
            covers=set(charm.covers), plural=charm.plural, worn_by=friend.id
        ))
        _ = charm_item
        world.para()
        world.say(f"{friend.id} offered {charm.prep}, and {hero.id} accepted because friendship was wiser than pride.")
        hero.memes["joy"] += 1.0
        friend.memes["joy"] += 1.0
        hero.memes["hurt"] = 0.0
        friend.memes["hurt"] = 0.0
        world.say(f"Together they went on, and {hero.id} was {rite.gerund}, while {prize.label} stayed bright.")
        world.say(f"That was how the old myth taught the village that true friends make room for one another and still keep each other safe.")
        resolved = True
    else:
        world.say(f"The path was safe after all, but the two friends still chose caution, and their bond only grew.")
        resolved = False

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        rite=rite,
        setting=setting,
        trait=trait,
        resolved=resolved,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    rite = _safe_fact(world, f, "rite")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short myth for a small child about friendship and a "{rite.keyword}" ritual, and include a bandana.',
        f"Tell a simple myth where {hero.id} wants to {rite.verb} but {friend.id} worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a gentle, old-sounding story in which two friends choose a safer way to protect a {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    prize = _safe_fact(world, f, "prize")
    rite = _safe_fact(world, f, "rite")
    trait = _safe_fact(world, f, "trait")
    place = _safe_fact(world, f, "setting").place
    out = [
        QAItem(
            question=f"Who are the story's two friends at {place}?",
            answer=f"The story is about {hero.id}, a {trait} {hero.type}, and {friend.id}, who cares deeply for {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {rite.verb}. That was the old, exciting thing calling from the place.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the {prize.label}?",
            answer=f"{friend.id} worried because {rite.gerund} would have ruined the {prize.label}, and friendship meant protecting what {hero.id} loved.",
        ),
    ]
    if f.get("resolved"):
        charm = select_charm(rite, prize)
        out.append(
            QAItem(
                question=f"How did the friends keep the {prize.label} safe?",
                answer=f"They used {charm.label}, which covered the right place on the body and kept the dangerous dust away from the {prize.label}.",
            )
        )
        out.append(
            QAItem(
                question=f"What changed by the end of the myth?",
                answer=f"By the end, the friends trusted each other more, and {hero.id} could still {rite.verb} without losing the bright {prize.label}.",
            )
        )
    return out


KNOWLEDGE = {
    "bandana": [
        (
            "What is a bandana?",
            "A bandana is a small cloth you can wear around your head or neck, or tie onto a bundle to keep it together.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people care about each other, help each other, and try to stay kind even when they disagree.",
        )
    ],
    "sea": [
        (
            "What is the sea?",
            "The sea is a very large body of salt water that moves in waves and reaches far beyond the shore.",
        )
    ],
    "wind": [
        (
            "What does wind do?",
            "Wind is moving air. It can push leaves, cool your face, and make cloth flutter.",
        )
    ],
    "ash": [
        (
            "What is ash?",
            "Ash is the soft gray powder left after something burns. It can cling to shoes and clothes.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rite"].tags)
    tags.add("friendship")
    tags.add("bandana")
    out: list[QAItem] = []
    for key in ["bandana", "friendship", "sea", "wind", "ash"]:
        if key in tags or key in {"bandana", "friendship"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story params and interface
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    rite: str
    prize: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
    trait: str
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


CURATED = [
    StoryParams("shore", "sea", "bandana", "Ari", "Ivo", "girl", "boy", "gentle"),
    StoryParams("grove", "wind", "bandana", "Mira", "Niko", "girl", "boy", "steadfast"),
    StoryParams("hill", "wind", "cloak", "Lena", "Orin", "girl", "boy", "brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic friendship storyworld with a bandana.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = []
    for place, rite_id, prize_id in valid_combos():
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        if getattr(args, "rite", None) and rite_id != getattr(args, "rite", None):
            continue
        if getattr(args, "prize", None) and prize_id != getattr(args, "prize", None):
            continue
        combos.append((place, rite_id, prize_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, rite_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, rite_id, prize_id, hero, friend, hero_type, friend_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(RITES, params.rite),
        _safe_lookup(PRIZES, params.prize),
        params.hero,
        params.friend,
        params.hero_type,
        params.friend_type,
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


# ---------------------------------------------------------------------------
# ASP / verify
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.rite} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
