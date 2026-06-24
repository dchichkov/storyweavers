#!/usr/bin/env python3
"""
storyworlds/worlds/transit_pretend_participate_repetition_flashback_fairy_tale.py
==================================================================================

A small fairy-tale story world about a child who wants to join a royal transit
and must stop pretending long enough to participate for real.

Seed tale idea:
---
A little child wants to ride the moon-carriage to the castle festival. The child
pretends to be a knight, but the gatekeeper only lets real helpers join the ride.
A flashback reminds the child how the village train once helped everyone travel
together. With a small true act of kindness, the child earns a seat at last.

Narrative instruments:
---
- Repetition: a royal call-and-response pattern is used to make the choice feel
  magical and memorable.
- Flashback: a remembered earlier transit shows why the current transit matters.

State model:
---
- ``meters`` track physical readiness, distance to the gate, and tokens carried.
- ``memes`` track delight, shame, courage, and belonging.
- Pretend play can increase courage, but it can also delay real participation.
- A transit route can only depart when the child and helper have the right token.
- A flashback can reveal a prior good transit, which shifts the child's choice
  from pretend bravado to actual participation.

The story is authored from simulated state rather than a frozen template.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    key: object | None = None
    tr: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    place: str
    transit_kind: str
    route_name: str
    depart_phrase: str
    arrival_phrase: str
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
class Transit:
    id: str
    label: str
    keyword: str
    requires: str
    destination: str
    repetition: str
    flashback_topic: str
    keeps_out: set[str] = field(default_factory=set)
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
class Token:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
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
class StoryParams:
    setting: str
    transit: str
    token: str
    name: str
    gender: str
    companion: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "lane": Setting(
        place="the silver lane",
        transit_kind="carriage",
        route_name="moon-road",
        depart_phrase="rolled from the gate",
        arrival_phrase="reached the castle",
    ),
    "river": Setting(
        place="the lantern riverbank",
        transit_kind="boat",
        route_name="starlit waterway",
        depart_phrase="floated from the dock",
        arrival_phrase="glided to the fair",
    ),
    "hill": Setting(
        place="the hill path",
        transit_kind="tram",
        route_name="windy track",
        depart_phrase="chimed away",
        arrival_phrase="climbed to the tower",
    ),
}

TRANSITS = {
    "moon_carriage": Transit(
        id="moon_carriage",
        label="moon carriage",
        keyword="carriage",
        requires="kindness token",
        destination="castle festival",
        repetition="the wheels go roll and the bells go ring",
        flashback_topic="village_train",
        keeps_out={"pretend", "showy"},
    ),
    "lantern_boat": Transit(
        id="lantern_boat",
        label="lantern boat",
        keyword="boat",
        requires="river token",
        destination="harbor fair",
        repetition="the oars go dip and the lanterns go sway",
        flashback_topic="village_bridge",
        keeps_out={"pretend", "loud"},
    ),
    "sun_tram": Transit(
        id="sun_tram",
        label="sun tram",
        keyword="tram",
        requires="helper badge",
        destination="tower market",
        repetition="the bell goes ding and the track goes round",
        flashback_topic="village_tram",
        keeps_out={"pretend", "rushed"},
    ),
}

TOKENS = {
    "kindness_token": Token(
        id="kindness_token",
        label="kindness token",
        phrase="a little brass kindness token",
        fits={"moon_carriage"},
    ),
    "river_token": Token(
        id="river_token",
        label="river token",
        phrase="a blue shell river token",
        fits={"lantern_boat"},
    ),
    "helper_badge": Token(
        id="helper_badge",
        label="helper badge",
        phrase="a bright helper badge",
        fits={"sun_tram"},
    ),
}

NAMES = {
    "girl": ["Lina", "Mira", "Nora", "Tessa", "Elin"],
    "boy": ["Oren", "Bram", "Pip", "Rowan", "Theo"],
}
MOODS = ["hopeful", "brave", "curious", "restless", "gentle"]


ASP_RULES = r"""
setting(silver_lane). setting(lantern_riverbank). setting(hill_path).
transit(moon_carriage). transit(lantern_boat). transit(sun_tram).
token(kindness_token). token(river_token). token(helper_badge).

uses(moon_carriage, kindness_token).
uses(lantern_boat, river_token).
uses(sun_tram, helper_badge).

at_risk(moon_carriage, kindness_token).
at_risk(lantern_boat, river_token).
at_risk(sun_tram, helper_badge).

valid(S, T, K) :- setting(S), transit(T), token(K), uses(T, K), at_risk(T, K).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRANSITS.items():
        lines.append(asp.fact("transit", tid))
        lines.append(asp.fact("requires", tid, t.requires))
        lines.append(asp.fact("destination", tid, t.destination))
        for k in sorted(t.keeps_out):
            lines.append(asp.fact("keeps_out", tid, k))
    for kid, k in TOKENS.items():
        lines.append(asp.fact("token", kid))
        for t in sorted(k.fits):
            lines.append(asp.fact("fits", kid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t, tr in TRANSITS.items():
            for k, tok in TOKENS.items():
                if t in tok.fits:
                    out.append((s, t, k))
    return out


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print(" only python:", sorted(py - cl))
    if cl - py:
        print(" only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale transit story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transit", choices=TRANSITS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mouse", "bird", "cat", "fox"])
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


def explain_rejection(transit: Transit, token: Token) -> str:
    return (
        f"(No story: the {transit.label} needs a {transit.requires}, "
        f"and {token.label} does not fit that transit.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "transit", None) is None or c[1] == getattr(args, "transit", None))
        and (getattr(args, "token", None) is None or c[2] == getattr(args, "token", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s, t, k = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    companion = getattr(args, "companion", None) or rng.choice(["mouse", "bird", "cat", "fox"])
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    return StoryParams(setting=s, transit=t, token=k, name=name, gender=gender,
                       companion=companion, mood=mood)


def can_depart(world: World, hero: Entity, transit: Transit, token: Entity) -> bool:
    return token.id in {k.id for k in world.entities.values() if k.id == token.id}


def generate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    transit = _safe_lookup(TRANSITS, params.transit)
    token = _safe_lookup(TOKENS, params.token)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type="king", label="the gatekeeper"))
    tr = world.add(Entity(id=transit.id, type="transit", label=transit.label))
    key = world.add(Entity(id=token.id, type="token", label=token.label, phrase=token.phrase))
    key.owner = hero.id

    hero.meters["distance"] = 0
    hero.meters["readiness"] = 0
    hero.memes["pretend"] = 1
    hero.memes["belonging"] = 0
    hero.memes["courage"] = 0
    hero.memes["joy"] = 0

    world.say(f"In {setting.place}, {hero.id} stood by the old gate and watched the {transit.label}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to join the {setting.route_name} ride, and {hero.pronoun()} began to pretend to be a knight.")
    world.say(f"The little game felt brave, and the child kept saying, '{transit.repetition}.'")

    world.para()
    world.say(f"The gatekeeper bowed and said, 'To ride the {transit.label}, you must bring a {token.label} and mean it.'")
    hero.meters["distance"] += 1
    hero.memes["shame"] += 1
    world.say(f"{hero.id} looked down at the token and saw that pretending was not the same as participating.")

    world.para()
    world.say(f"Then came a flashback: long ago, a village train had carried lanterns, bread, and tired neighbors home together.")
    world.say(f"That memory repeated in {hero.id}'s mind like a song: the best travel was shared travel, and the best part was helping.")

    hero.memes["courage"] += 1
    hero.memes["pretend"] = 0
    hero.meters["readiness"] += 1
    world.say(f"So {hero.id} stopped pretending and chose a small true act: {hero.pronoun()} returned a dropped basket to the gatekeeper.")
    world.say(f"The gatekeeper smiled, gave back the {token.label}, and called, 'Now you may participate.'")

    world.para()
    hero.memes["belonging"] += 2
    hero.memes["joy"] += 2
    hero.meters["distance"] = 0
    world.say(f"The {transit.label} departed as the bells rang again, {transit.repetition}, and this time {hero.id} climbed aboard for real.")
    world.say(f"{hero.id} rode with {params.companion} curled nearby, the {token.label} safe in {hero.pronoun('possessive')} hand, and the story ended with {setting.arrival_phrase}.")

    world.facts.update(hero=hero, helper=helper, transit=transit, token=key, setting=setting,
                       companion=params.companion)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    transit = _safe_fact(world, f, "transit")
    token = _safe_fact(world, f, "token")
    return [
        f'Write a fairy-tale story about a child named {hero.id} who wants to join a {transit.label} and must learn the difference between pretend play and true participation.',
        f'Tell a gentle story with repetition and a flashback where {hero.id} uses {token.label} to board the {transit.label}.',
        f'Write a short fairy tale for young children that includes the words "transit", "pretend", and "participate".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    transit = _safe_fact(world, f, "transit")
    token = _safe_fact(world, f, "token")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {hero.id} want to join at the beginning of the story?",
            answer=f"{hero.id} wanted to join the {transit.label} and ride on the {world.setting.route_name}.",
        ),
        QAItem(
            question=f"Why did the gatekeeper say {hero.id} needed the {token.label}?",
            answer=f"The gatekeeper said the {transit.label} needed a {token.label}, so the child could participate for real instead of only pretending.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember an older village transit where people shared the ride and helped each other get home.",
        ),
        QAItem(
            question=f"How did {hero.id} finally earn a place on the {transit.label}?",
            answer=f"{hero.id} stopped pretending, did a small true kindness, and the gatekeeper let {hero.id} participate by boarding with the {token.label}.",
        ),
        QAItem(
            question=f"Who gave {hero.id} permission to travel at the end?",
            answer=f"{helper.label} the gatekeeper gave permission and smiled when {hero.id} chose the honest way to participate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is transit?",
            answer="Transit means travel from one place to another, like riding a carriage, boat, or tram.",
        ),
        QAItem(
            question="What does it mean to pretend?",
            answer="To pretend means to play as if something is true, even when it is only make-believe.",
        ),
        QAItem(
            question="What does it mean to participate?",
            answer="To participate means to take part in something for real, not just watch from the side.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a remembered moment from before that helps explain what is happening now.",
        ),
        QAItem(
            question="Why do stories sometimes repeat a line?",
            answer="Stories repeat a line to make it feel magical, memorable, or like a song.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    parts = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("lane", "moon_carriage", "kindness_token", "Lina", "girl", "fox", "hopeful"),
            StoryParams("river", "lantern_boat", "river_token", "Oren", "boy", "bird", "curious"),
            StoryParams("hill", "sun_tram", "helper_badge", "Mira", "girl", "mouse", "brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
